from llama_index import ServiceContext, get_response_synthesizer
from llama_index.indices.document_summary import DocumentSummaryIndex
from llama_index.llms import OpenAI
import nest_asyncio
import os
import sys
current_directory = os.path.dirname(os.path.abspath(__file__))
full_path = os.path.join(current_directory, '..')
sys.path.append(full_path)

from access import get_openai_key, get_pinecone_env, get_pinecone_key
from JSONFormat import convert_to_jsonfile
from llama_index.prompts import PromptTemplate
from llama_index import SimpleDirectoryReader


# 1. Key값 설정
os.environ["OPENAI_API_KEY"] = get_openai_key()
os.environ["PINECONE_ENV"] = get_pinecone_env()
environment = get_pinecone_env()
os.environ["PINECONE_API_KEY"] = get_pinecone_key()
nest_asyncio.apply()


def create_finance_docs(file_names, directory_path):
    '''
        디렉토리 경로에 있는 파일들을 불러와 finance_docs을 만든다.
        pdf파일을 읽어 chunk size로 쪼갠 후 metadata를 입력한 객체가 만들어 진다.
    '''
    filename_fn = lambda filename: {'file_name': filename}
    finance_docs = []

    for file_name in file_names:
        file_path = os.path.join(directory_path, file_name)
        documents = SimpleDirectoryReader(input_files=[file_path], file_metadata=filename_fn).load_data()
        documents[0].doc_id = file_name
        finance_docs.extend(documents)

    return finance_docs


def document_summary(finance_docs):
    '''
        finance_docs을 불러와 파일이름에 따라 구분하여 요약본을 만들어 낸다.
        
    '''
    # LLM (gpt-3.5-turbo)
    chatgpt = OpenAI(temperature=0, model="gpt-3.5-turbo")
    #service_context = ServiceContext.from_defaults(llm=chatgpt, chunk_size=1024)
    service_context = ServiceContext.from_defaults(llm=chatgpt, chunk_size=512)

    # Prompt foramt
    qa_prompt_tmpl = (
        "Context information is below.\n"
        "---------------------\n"
        "{context_str}\n"
        "---------------------\n"
        "Given the context information and not prior knowledge, "
        "Summarize only Korean"
        "Summarize over 500 characters."
        "Answer with Korean"
        "Query: {query_str}\n"
        "Answer: "
    )
    qa_prompt = PromptTemplate(qa_prompt_tmpl)


    # default mode of building the index
    response_synthesizer = get_response_synthesizer(response_mode="tree_summarize", summary_template=qa_prompt, use_async=True)
        # 여기에 tree summarize가 있다. 멘토님이 말씀해 주신것 생각해보기. 


    doc_summary_index = DocumentSummaryIndex.from_documents(
        finance_docs,
        service_context=service_context,
        response_synthesizer=response_synthesizer,
        show_progress=True,
        )
    return doc_summary_index


if __name__ == "__main__":
    '''
        directory_path와 target_path는 실수하지 않도록 일부로 날짜 형식을 다르게 적었다.
        저장 전 반드시 Research_daily, Research_toprank를 잘 구분하여 directory_path, target_path를 지정해야한다.
    '''
    current_directory = os.path.dirname(os.path.abspath(__file__))
    directory_path = os.path.join(current_directory, '..', 'data', 'Research_daily', '20231218')
    #directory_path = os.path.join(current_directory, '..', 'data', 'Research_toprank', '20231217')
    file_names = os.listdir(directory_path)
    
    finance_docs = create_finance_docs(file_names, directory_path)
    doc_summary_index = document_summary(finance_docs)
    print(doc_summary_index)
    
    target_path = os.path.join(current_directory, '..', 'data', 'Results_Summary', 'daily_231218')
    #target_path = os.path.join(current_directory, '..', 'data', 'Results_Summary', 'toprank_231217')
    for file_name in file_names:
        content = doc_summary_index.get_document_summary(f"{file_name}")
        json_result = convert_to_jsonfile(file_name, content, target_path)

  