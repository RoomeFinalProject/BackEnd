import os
import sys
current_directory = os.path.dirname(os.path.abspath(__file__))
full_path = os.path.join(current_directory, '..')
sys.path.append(full_path)
from access import get_openai_key, get_pinecone_env, get_pinecone_key
import pinecone
from llama_index.vector_stores import PineconeVectorStore
from llama_index import VectorStoreIndex, get_response_synthesizer
from llama_index.retrievers import VectorIndexRetriever
from llama_index.query_engine import RetrieverQueryEngine
from llama_index.postprocessor import SimilarityPostprocessor
from llama_index.prompts import PromptTemplate
from llama_index.llms import ChatMessage, MessageRole
from llama_index.prompts import ChatPromptTemplate
import time
from llama_index.memory import ChatMemoryBuffer
from llama_index.prompts import PromptTemplate
from llama_index.llms import ChatMessage, MessageRole
from llama_index.chat_engine.condense_question import CondenseQuestionChatEngine


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
## 3.1 configure retriever\
retriever = VectorIndexRetriever(index=index, similarity_top_k=3,) # 여기에 필터기능 있는 것 같음

## 3.2 Configuring node postprocessors
'''
    postprocessors의 종류는 다양한 것이 있지만 내가 활용하지 못함. 특히 장문의 node를 반환하였을때 재배열하여 문장을 추출하는 기능이 있는데 
    retriever에서 받은 node를 중간에 어떻게 LongContextRecoder 함수로 반환하는지 확인 할 수 없어 도입을 포기함.
    https://docs.llamaindex.ai/en/stable/module_guides/querying/node_postprocessors/node_postprocessors.html
'''
node_postprocessors = [SimilarityPostprocessor(similarity_cutoff=0.1)]

## 3.3 configure response synthesizer: Prompt Engineering, configuration
### 3.3.1 Prompt Engineering
### Text QA Prompt
chat_text_qa_msgs = [
    ChatMessage(
        role=MessageRole.SYSTEM,
        content=(
            "Always answer the question, even if the context isn't helpful.\n"
            "answer the query in the style of a kind friend.\n"
            "You are Korean you always say Korean"
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

### Refine Prompt
chat_refine_msgs = [
    ChatMessage(
        role=MessageRole.SYSTEM,
        content=(
            "Always answer the question, even if the context isn't helpful.\n"
            "answer the query in the style of a kind friend.\n"
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


### 3.3.2 configure response synthesizer
'''
    Response mode: refine, compact, tree_summarize, accumulate 등이 있는데 결과상 그 차이를 잘 모르겠음
    Response mode를 설정하면 오히려 성능이 떨어지는 경우가 있는데, default mode가 무엇인지 확인이 필요하다.
'''
response_synthesizer = get_response_synthesizer(text_qa_template = text_qa_template, refine_template = refine_template)

 
## 3.4 assemble query engine
'''
    query engine의 경우 custom query engine을 상속받아 나만의 query engine을 만드는 것이 가능하다. 
'''
query_engine = RetrieverQueryEngine(
    retriever=retriever,
    response_synthesizer=response_synthesizer,
    node_postprocessors=node_postprocessors,
)


# 4. Chat engine Stage 조작: ChatMemoryBuffer, custom_prompt, custom_chat_history,assemble chat engine
## 4.1 Chat memory buffer

memory = ChatMemoryBuffer.from_defaults(token_limit=4000)

## 4.2 Prompt Template
custom_prompt = PromptTemplate(
    """\
Given a conversation (between Human and Assistant) and a follow up message from Human, \
rewrite the message to be a standalone question that captures all relevant context \
from the conversation.
You must translate English to Korean for your answer.\

<Chat History>
{chat_history}

<Follow Up Message>
{question}

<Standalone question>
"""
)

# list of `ChatMessage` objects
custom_chat_history = [
    ChatMessage(
        role=MessageRole.USER,
        content=
            "You must translate English to Korean for your answer.\n",
    ),
    ChatMessage(role=MessageRole.ASSISTANT, content="Okay, sounds good."),
]

chat_engine = CondenseQuestionChatEngine.from_defaults(
    query_engine=query_engine,
    condense_question_prompt=custom_prompt,
    chat_history=custom_chat_history,
    verbose=True,
)


if __name__ == "__main__":
    
    while True:
        text_input = input("User: ")
        if text_input.lower() == "exit":
            break
        
        print("=====================CHAT RESPONSE============================")
        start_time = time.time()
        chat_engine = index.as_chat_engine(chat_mode="condense_plus_context", memory = memory) # react mode에서는 한글이 절대 나오지않음
        chat_response = chat_engine.chat(text_input)
        response_time = time.time() - start_time
        print("Response:", chat_response.response)
        print("Response Time: {:.2f} seconds".format(response_time))
        print("===============================================================")
        
        
        print("=====================QUERY RESPONSE============================")
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
        
    '''
        chat_engine에서도 retriever 값들을 반환하고 싶은데 잘 되지 않는다.
    '''
    
    
    
'''
    text_input = "천보 회사의 목표주가를 알려줄 수 있니?"

    start_time = time.time()
    response = query_engine.query(text_input)
    response_time = time.time() - start_time
    
    print("Response:", response.response)    
    print("Response Time: {:.2f} seconds".format(response_time))
    print("===============================================================")
    
    if response.metadata:
        for source_node in response.source_nodes:
            file_name, page_label = source_node.metadata['file_name'], source_node.metadata['page_label']
            selected_node, similarity_score = source_node.get_content(), source_node.get_score()
            print(f'file_name : {file_name}, page_label : {page_label}, similarity_score : {similarity_score}')
            print('selected_node :', selected_node)
            print("===============================================================")
    # 참고링크: https://docs.llamaindex.ai/en/stable/examples/query_engine/custom_query_engine.html
        
 
'''   
 