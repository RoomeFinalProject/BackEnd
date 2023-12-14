'''
한번에 embedding 할수 있는 토큰수 : 4097
'''

import os
import sys
current_directory = os.path.dirname(os.path.abspath(__file__))
full_path = os.path.join(current_directory, '..')
sys.path.append(full_path)
from access import get_openai_key

from llama_index import SimpleDirectoryReader
from llama_index.llms import OpenAI
from llama_index.text_splitter import TokenTextSplitter
from llama_index.extractors import SummaryExtractor, QuestionsAnsweredExtractor, TitleExtractor, KeywordExtractor, EntityExtractor, BaseExtractor
from llama_index.ingestion import IngestionPipeline
import nest_asyncio
nest_asyncio.apply()

# key값 불러오기
os.environ["OPENAI_API_KEY"] = get_openai_key()

llm = OpenAI(temperature=0, model="gpt-3.5-turbo")

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



if __name__ == "__main__":
    current_directory = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(current_directory, '..', 'data', 'testdata')
    documents = data_loader(full_path)
    documents_nodes = docs2nodes (documents, llm)
    #print(documents_nodes)
    print(len(documents_nodes))
    print('===========================================================')
    print(documents_nodes[20])
    print('===========================================================')
    print('text node. text:', documents_nodes[20].text)
    print('===========================================================')
    print('text node. metadata:', documents_nodes[20].metadata)

