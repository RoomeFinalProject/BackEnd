'''
한번에 embedding 할수 있는 토큰수 : 4097
이 파일을 사용하면 한번에 pdf loading 부터 node 분할, pinecone upload까지 수행 가능.

'''
import os
import sys
current_directory = os.path.dirname(os.path.abspath(__file__))
full_path = os.path.join(current_directory, '..')
sys.path.append(full_path)
from access import get_openai_key, get_pinecone_env, get_pinecone_key

from llama_index import SimpleDirectoryReader
from llama_index.llms import OpenAI
from llama_index.text_splitter import TokenTextSplitter
from llama_index.extractors import SummaryExtractor, QuestionsAnsweredExtractor, TitleExtractor, KeywordExtractor, EntityExtractor, BaseExtractor
from llama_index.ingestion import IngestionPipeline
import nest_asyncio

from pathlib import Path
from llama_index import download_loader
import pinecone

from llama_index.vector_stores import PineconeVectorStore
from llama_index.storage.storage_context import StorageContext
from llama_index import VectorStoreIndex, ServiceContext

nest_asyncio.apply()

# key값 불러오기
# 1. Key값 설정
os.environ["OPENAI_API_KEY"] = get_openai_key()
os.environ["PINECONE_ENV"] = get_pinecone_env()
environment = get_pinecone_env()
os.environ["PINECONE_API_KEY"] = get_pinecone_key()
pinecone.init(api_key=os.environ["PINECONE_API_KEY"],environment=os.environ["PINECONE_ENV"])

llm = OpenAI(temperature=0, model="gpt-3.5-turbo")

BackEnd_directory = os.path.dirname(os.path.abspath(os.path.dirname(os.path.abspath(__file__))))
test_data_path = os.path.join(BackEnd_directory, 'data', 'Chatbot_db_pdf')

def pdf_loader(test_data_path, file_name):
    '''
        pdf를 loading하는 함수 documents로 읽어온다.
        txt 파일이 없을 시 simpledirectoryreader보다 효율적임
        simpledirectoryreader의 경우 파일 로딩이 실패하면 어느 시점인지 모르기 때문에 처음부터 다시 해야함.
        pdf 파일을 각각 loading하면 실패한 시점부터 다시 가능
    '''
    PDFReader = download_loader("PDFReader")
    loader = PDFReader()
    document_path = os.path.join(test_data_path, file_name)
    documents = loader.load_data(file=Path(document_path))
    return documents


# Data Loading
def data_loader(path):
    filename_fn = lambda filename: {"file_name": filename}
    documents = SimpleDirectoryReader(path, file_metadata=filename_fn).load_data()
    return documents


# Nodes 및 Metadata 생성
def docs2nodes(documents, llm, chunk_size = 512, chunk_overlap = 128):
    '''
        default 값
        chunk_size = 512
        chunk_overlap = 128
    '''
    # 1. text_splitting 방법 설정
    text_splitter = TokenTextSplitter(separator = " ", chunk_size = chunk_size, chunk_overlap = chunk_overlap)
    # sentenssesplitter와 차이는? SentenceSplitter(chunk_size=512, # include_extra_info=False, <-- 이게 있으면 에러난다. include_prev_next_rel=False)

    # 2. metadata로 추출할 조건 설정
    #llm = OpenAI(temperature=0, model="gpt-3.5-turbo")
    extractors = [
        TitleExtractor(nodes=5, llm=llm),
        #QuestionsAnsweredExtractor(questions=3, llm=llm),
        # EntityExtractor(prediction_threshold=0.5),
        SummaryExtractor(summaries=["prev", "self"], llm=llm),
        # KeywordExtractor(keywords=10, llm=llm),
        # CustomExtractor()
    ]

    # 3. 변환 조건들 리스트
    transformations = [text_splitter] + extractors

    ''' Extractor는 원하는 함수를 만들어 넣을 수도 있다.
    class CustomExtractor(BaseExtractor):
    def extract(self, nodes):
        metadata_list = [
            {
                "custom":(node.metadata["document_title"] + "\n" + node.metadata["excerpt_keywords"])
            }
            for node in nodes
        ]
        return metadata_list
    '''
    # 4. node로 변환
    pipeline = IngestionPipeline(transformations = transformations)
    documents_nodes = pipeline.run(documents = documents)
    
    return documents_nodes


def emb_pinecone(documents_nodes, index_name = 'openai'):
    llm = OpenAI(temperature=0, model="gpt-3.5-turbo")
    # 3. 라마가 가져올 storage Index 설정: 여기서는 pinceone의 index 'openai'로 설정.
    index_name = "openai" # pinecone에 저장될 인덱스 저장소 이름
    vector_store = PineconeVectorStore(
                                    index_name=index_name,
                                    environment=environment,
                                    #metadata_filters=metadata_filters,
                                    )
    storage_context = StorageContext.from_defaults(vector_store=vector_store)


    # 4. Service contenxt 조건 설정: 어떤 embedding 모델을 사용할 것인지 결정, llm은 생성형, embedding은 ada default로 설정되어 있음.
    service_context=ServiceContext.from_defaults(llm=llm)

    # 5. Embedding
    index = VectorStoreIndex( # <-# document에서 직접 불러올 시 VectorStoreIndex.from_documents // nodes를 만들어 불러올시 VectorStoreIndex
                            documents_nodes,
                            storage_context=storage_context,
                            service_context=service_context,
                            )
    
    print('Embedding and uploding have beend completed')
    return index

file_names = os.listdir(test_data_path)
for i, file_name in enumerate(file_names):
    documents = pdf_loader(test_data_path, file_name)
    print(f'[{i}] {file_name} PDF loading has been completed.')
    documents_nodes = docs2nodes(documents, llm, chunk_size = 341, chunk_overlap = 86)
    
if __name__ == "__main__":
    file_names = os.listdir(test_data_path)
    for i, file_name in enumerate(file_names):
        documents = pdf_loader(test_data_path, file_name)
        print(f'[{i}] {file_name} PDF loading has been completed.')
        documents_nodes = docs2nodes(documents, llm, chunk_size = 341, chunk_overlap = 86)
        print(f'[{i}] {file_name} PDF Nodes have been created.')
        emb_pinecone(documents_nodes)
        print(f'[{i}] {file_name} The PDF has been converted to vectors and uploaded to Pinecone.')
        #print(len(documents_nodes))
        print('===========================================================')
        #print('text node. text:', documents_nodes[10].text)
        print('===========================================================')
        #print('text node. metadata:', documents_nodes[10].metadata)
    pass

