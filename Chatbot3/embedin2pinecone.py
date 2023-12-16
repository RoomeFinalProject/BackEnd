import os
import sys
current_directory = os.path.dirname(os.path.abspath(__file__))
full_path = os.path.join(current_directory, '..')
sys.path.append(full_path)
from access import get_openai_key, get_pinecone_env, get_pinecone_key
import os
from llama_index.vector_stores import PineconeVectorStore
from llama_index.storage.storage_context import StorageContext
from llama_index.storage.storage_context import StorageContext
from llama_index import VectorStoreIndex, ServiceContext
from llama_index.llms import OpenAI
from llama_index.embeddings import OpenAIEmbedding
from Loading2nodes import pdf_loader, sentence_nodes
# 1. Key값 설정
os.environ["OPENAI_API_KEY"] = get_openai_key()
os.environ["PINECONE_ENV"] = get_pinecone_env()
environment = get_pinecone_env()
os.environ["PINECONE_API_KEY"] = get_pinecone_key()

# 2. Nodes 만들기

llm = OpenAI(temperature=0, model="gpt-3.5-turbo")
embed_model = OpenAIEmbedding() # text-embedding-ada-002 default 모델

def embedding_pinecone(documents_nodes, index_name = 'openai'):
    '''
        Index_name: 라마가 가져올 storage Index 설정 (여기서는 pinceone의 index 'openai'로 설정)
        Service contenxt 조건: embedding 모델, 생성형 모델 설정; 여기서 설정한 임베딩 모델은 indexing, querying 모두에 적용
            https://docs.llamaindex.ai/en/stable/module_guides/models/embeddings.html#local-embedding-models
    
        service_context=ServiceContext.from_defaults(llm_predictor=llm, embed_model=embed_model,)
        * Huggingface model 이용
        service_context = ServiceContext.from_defaults(embed_model="local:BAAI/bge-large-en")
        커스텀 임베딩까지 가능하나 너무 어려움.
    '''
    index_name = "openai" # pinecone에 저장될 인덱스 저장소 이름
    vector_store = PineconeVectorStore(
                                    index_name=index_name,
                                    environment=environment,
                                    #metadata_filters=metadata_filters,
                                    )
    storage_context = StorageContext.from_defaults(vector_store=vector_store)    
    service_context=ServiceContext.from_defaults(llm_predictor=llm, embed_model=embed_model,)
    index = VectorStoreIndex( # <-# document에서 직접 불러올 시 VectorStoreIndex.from_documents // nodes를 만들어 불러올시 VectorStoreIndex
                            documents_nodes,
                            storage_context=storage_context,
                            service_context=service_context,
                            )
    return print("Pinecone vector store에 저장 완료")

if __name__ == "__main__":
    BackEnd_directory = os.path.dirname(os.path.abspath(os.path.dirname(os.path.abspath(__file__))))
    test_data_path = os.path.join(BackEnd_directory, 'data', 'Chatbot_db_pdf')
    file_names = os.listdir(test_data_path)
    
    for i, file_name in enumerate(file_names):
        documents = pdf_loader(test_data_path, file_name)
        print(f'[{i}] {file_name} PDF loading has been completed.')
        documents_nodes = sentence_nodes(documents, llm, chunk_size = 125, chunk_overlap = 40)
        print(f'[{i}] {file_name} PDF Nodes have been created.')
        embedding_pinecone(documents_nodes)
        print(f'[{i}] {file_name} The PDF has been converted to vectors and uploaded to Pinecone.')
        print(len(documents_nodes))
        print('===========================================================')
        print('text node. text:', documents_nodes[10].text)
        print('===========================================================')
        print('text node. metadata:', documents_nodes[10].metadata)
    
