'''
한번에 embedding 할수 있는 토큰수 : 4097
'''
import os
import sys
current_directory = os.path.dirname(os.path.abspath(__file__))
full_path = os.path.join(current_directory, '..')
sys.path.append(full_path)
from access import get_openai_key, get_pinecone_env, get_pinecone_key

from pathlib import Path
from llama_index import Document
from llama_index import SimpleDirectoryReader
from llama_index.llms import OpenAI
from llama_index.node_parser import SimpleNodeParser
#from llama_index.node_parser import SentenceSplitter
from langchain.document_loaders import TextLoader
from llama_index.schema import IndexNode
from llama_index.extractors import SummaryExtractor, QuestionsAnsweredExtractor, TitleExtractor, KeywordExtractor, EntityExtractor, BaseExtractor
from llama_index.ingestion import IngestionPipeline
# from llama_index.text_splitter import TokenTextSplitter
import nest_asyncio
from llama_index import download_loader



nest_asyncio.apply()

# key값 불러오기
# 1. Key값 설정
os.environ["OPENAI_API_KEY"] = get_openai_key()
os.environ["PINECONE_ENV"] = get_pinecone_env()
environment = get_pinecone_env()
os.environ["PINECONE_API_KEY"] = get_pinecone_key()

llm = OpenAI(temperature=0, model="gpt-3.5-turbo")

#test_data_path = os.path.join(BackEnd_directory, 'data', 'Chatbot_db_pdf')
#test_data_path = os.path.join(BackEnd_directory, 'data', 'Chatbot_db_text')

def pdf_loader(test_data_path, file_name):
    '''
        PDF를 읽어주는 로더
    '''
    PDFReader = download_loader("PDFReader")
    loader = PDFReader()
    document_path = os.path.join(test_data_path, file_name)
    documents = loader.load_data(file=Path(document_path))
    return documents

def text_loader(test_data_path, file_name):
    '''
        .txt 파일을 읽기 위해 만든 로더
    '''
    document_path = os.path.join(test_data_path, file_name)
    loader = TextLoader(document_path, encoding = 'utf-8')
    documents = loader.load()
    return documents

def data_loader(path):
    '''
        폴더 전체 (PDF, .txt 파일 동시가능)를 읽기 위한 로더
        한계점: 한번에 gpt embedding system에 많이올리다 보면 중간에 멈추는데, 어디 까지 올라왔는지 조절할 수 없어서 pdf와 text로더를 각각 만들었다.
        pdf, text로더를 사용하면 한파일씩 쪼개어 embedding까지 완성 시킬 수 있기 때문에 gpt가 reject한 시점부터 다시 시작 가능하다.
    '''
    filename_fn = lambda filename: {"file_name": filename}
    documents = SimpleDirectoryReader(path, file_metadata=filename_fn).load_data()
    return documents

def sentence_nodes(documents):
    '''
        text 파일을 로딩한경우와 pdf 파일을 로딩한 경우 output 형식이 다르다.
        - text 파일 로딩: d.page_content
        - pdf 파일 로딩 : d.get_content 
        사용 해야 파일을 읽을 수 있다.
    '''
    try:
        doc_text = "\n\n".join([d.get_content() for d in documents]) # try read pdf file
    except Exception as pdf_error:
        try:
            doc_text = "\n\n".join([d.page_content for d in documents]) # try read .txt file
        except Exception as txt_error:
            print("다른 pdf, .txt 외 다른 파일이 로딩되었습니다.")
            
    docs = [Document(text=doc_text)]
    node_parser = SimpleNodeParser.from_defaults(chunk_size=300, chunk_overlap = 100) # node_parser = SentenceSplitter(chunk_size=300, chunk_overlap = 100) 두 개가 동일한 것
    base_nodes = node_parser.get_nodes_from_documents(docs)

    extractors = [
                    TitleExtractor(nodes=5, llm=llm),
                    SummaryExtractor(summaries=["prev", "self"], llm=llm),
                    #QuestionsAnsweredExtractor(questions=3, llm=llm),
                    #EntityExtractor(prediction_threshold=0.5),
                    # KeywordExtractor(keywords=10, llm=llm),
                    # CustomExtractor()
                ]

    # 3. 변환 조건들 리스트
    transformations = [node_parser] + extractors # Extractor는 원하는 함수를 만들어 넣을 수도 있다.
    
    # 4. node로 변환
    pipeline = IngestionPipeline(transformations = transformations)
    documents_nodes = pipeline.run(documents = docs)
    
    return base_nodes, documents_nodes


if __name__ == "__main__":
    
    BackEnd_directory = os.path.dirname(os.path.abspath(os.path.dirname(os.path.abspath(__file__))))
    test_data_path = os.path.join(BackEnd_directory, 'data', 'Chatbot_db_text')
    file_names = os.listdir(test_data_path)
    
    for i, file_name in enumerate(file_names):
        print(file_name)
        documents = text_loader(test_data_path, file_name)
        base_nodes = sentence_nodes(documents)
        print(base_nodes)
    
    pass

