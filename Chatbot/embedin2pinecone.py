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
from Docs2nodes import data_loader, docs2nodes

# 1. Key값 설정
os.environ["OPENAI_API_KEY"] = get_openai_key()
os.environ["PINECONE_ENV"] = get_pinecone_env()
environment = get_pinecone_env()
os.environ["PINECONE_API_KEY"] = get_pinecone_key()

# 2. Nodes 만들기
current_directory = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(current_directory, '..', 'data', 'Research_daily','20231206')
#path = os.path.join(current_directory, '..', 'data', 'Research_daily','20231207')
#path = os.path.join(current_directory, '..', 'data', 'Research_daily','20231213')
llm = OpenAI(temperature=0, model="gpt-3.5-turbo")
documents = data_loader(path)
documents_nodes = docs2nodes (documents, llm)


# 3. 라마가 가져올 storage Index 설정: 여기서는 pinceone의 index 'openai'로 설정.
index_name = "openai" # pinecone에 저장될 인덱스 저장소 이름
vector_store = PineconeVectorStore(
                                   index_name=index_name,
                                   environment=environment,
                                   #metadata_filters=metadata_filters,
                                   )
storage_context = StorageContext.from_defaults(vector_store=vector_store)


# 4. Service contenxt 조건 설정: 어떤 embedding 모델을 사용할 것인지 결정
service_context=ServiceContext.from_defaults(llm=llm)


# 5. Embedding
index = VectorStoreIndex( # <-# document에서 직접 불러올 시 VectorStoreIndex.from_documents // nodes를 만들어 불러올시 VectorStoreIndex
                         documents_nodes,
                         storage_context=storage_context,
                         service_context=service_context,
                         )