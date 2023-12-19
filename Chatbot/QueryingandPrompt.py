import os
import sys
current_directory = os.path.dirname(os.path.abspath(__file__))
full_path = os.path.join(current_directory, '..')
sys.path.append(full_path)
from access import get_openai_key, get_pinecone_env, get_pinecone_key
import pinecone
from llama_index import VectorStoreIndex, ServiceContext
from llama_index.vector_stores import PineconeVectorStore
from llama_index import VectorStoreIndex, get_response_synthesizer
from llama_index.retrievers import VectorIndexRetriever
from llama_index.query_engine import RetrieverQueryEngine
from llama_index.postprocessor import SimilarityPostprocessor,KeywordNodePostprocessor
from llama_index.prompts import PromptTemplate
from llama_index.llms import ChatMessage, MessageRole
from llama_index.prompts import ChatPromptTemplate
import time


# 1. Key값 설정
os.environ["OPENAI_API_KEY"] = get_openai_key()
os.environ["PINECONE_ENV"] = get_pinecone_env()
environment = get_pinecone_env()
os.environ["PINECONE_API_KEY"] = get_pinecone_key()
pinecone.init(api_key = get_pinecone_key(), environment = get_pinecone_env())


# 2. LlammaIndex - Pinecone 연동
pinecone_index = pinecone.Index("openai")
vector_store = PineconeVectorStore(pinecone_index=pinecone_index)
index = VectorStoreIndex.from_vector_store(vector_store)


# 3. Querying Stage 조작: configure retriever, Configuring node postprocessors, configure response synthesizer
## 3.1 configure retriever
retriever = VectorIndexRetriever(index=index, similarity_top_k=3,) # 여기에 필터기능 있는 것 같음

## 3.2 Configuring node postprocessors
node_postprocessors = [SimilarityPostprocessor(similarity_cutoff=0.1)]


# Text QA Prompt
chat_text_qa_msgs = [
    ChatMessage(
        role=MessageRole.SYSTEM,
        content=(
            "Always answer the question, even if the context isn't helpful.\n"
            "answer the query in the style of a kind friend.\n"
            "You always say Korean"
        ),
    ),
    ChatMessage(
        role=MessageRole.USER,
        content=(
            "Context information is below.\n"
            "---------------------\n"
            "{context_str}\n"
            "---------------------\n"
            "Given the context information and not prior knowledge, "
            "You must translate English to Korean for your answer.\n"
            
            "answer the question: {query_str}\n"
        ),
    ),
]
text_qa_template = ChatPromptTemplate(chat_text_qa_msgs)

# Refine Prompt
chat_refine_msgs = [
    ChatMessage(
        role=MessageRole.SYSTEM,
        content=(
            "Always answer the question, even if the context isn't helpful.\n"
            "answer the query in the style of kind friend.\n"
            "You are Korean you always say Korean"
            
        ),
    ),
    ChatMessage(
        role=MessageRole.USER,
        content=(
            "We have the opportunity to refine the original answer "
            "(only if needed) with some more context below.\n"
            "------------\n"
            "{context_msg}\n"
            "------------\n"
            "Given the new context, refine the original answer to better "
            "answer the question: {query_str}. "
            "If the context isn't useful, output the original answer again.\n"
            "You must translate English to Korean for your answer.\n"
            "Original Answer: {existing_answer}"
        ),
    ),
]
refine_template = ChatPromptTemplate(chat_refine_msgs)


## 3.3 configure response synthesizer
response_synthesizer = get_response_synthesizer(text_qa_template = text_qa_template, refine_template = refine_template)

  
## 3.4 assemble query engine
query_engine = RetrieverQueryEngine(
    retriever=retriever,
    response_synthesizer=response_synthesizer,
    node_postprocessors=node_postprocessors,
)


if __name__ == "__main__":
    
    text_input = "나 오늘 너무 힘들어 ㅠㅠㅜㅜㅠㅠ"

    start_time = time.time()
    response = query_engine.query(text_input)
    response_time = time.time() - start_time
    
    print("Response:", response.response)    
    print("Response Time: {:.2f} seconds".format(response_time))
    print("===============================================================")
    
    if response.metadata:
        for source_node in response.source_nodes:
            file_name = source_node.metadata.get('file_name', 'N/A')
            page_label = source_node.metadata.get('page_label', 'N/A')
            selected_node, similarity_score = source_node.get_content(), source_node.get_score()

            print(f'file_name: {file_name}, page_label: {page_label}, similarity_score: {similarity_score}')
            print('selected_node:', selected_node)
        print("===============================================================")
    # 참고링크: https://docs.llamaindex.ai/en/stable/examples/query_engine/custom_query_engine.html
        
