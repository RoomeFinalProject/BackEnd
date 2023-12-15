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

from .Loading import file_names, finance_docs
from .JSONFormat import convert_to_jsonformat
from .JSONFormat import convert_to_jsonfile
from llama_index.prompts import PromptTemplate


# 1. Key값 설정
os.environ["OPENAI_API_KEY"] = get_openai_key()
os.environ["PINECONE_ENV"] = get_pinecone_env()
environment = get_pinecone_env()
os.environ["PINECONE_API_KEY"] = get_pinecone_key()
nest_asyncio.apply()

# LLM (gpt-3.5-turbo)
chatgpt = OpenAI(temperature=0, model="gpt-3.5-turbo")

service_context = ServiceContext.from_defaults(llm=chatgpt, chunk_size=1024)

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

# if __name__ == "__main__":
#     summary_list = []
#     company_name = "Yuanta Securities" 
#     title_value = "AAA" 
#     for file_name in file_names:
#         content = doc_summary_index.get_document_summary(f"{file_name}")
#         json_result = {"company": company_name, "title": title_value, "content": content}
#         summary_list.append(json_result)
#     print(summary_list)

# json_result = convert_to_jsonformat(file_name, content)
# summary_list.append(json_result)

# if __name__ == "__main__":
#     current_directory = os.path.dirname(os.path.abspath(__file__))
#     full_path = os.path.join(current_directory, '..', 'data', 'Results_Summary')
#     for file_name in file_names:
#         content = doc_summary_index.get_document_summary(f"{file_name}")
#         json_result = convert_to_jsonfile(file_name, content, full_path)

  
