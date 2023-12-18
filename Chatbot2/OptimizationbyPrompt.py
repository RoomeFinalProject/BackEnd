import os
import sys
import pinecone
import nest_asyncio
from pathlib import Path
from llama_hub.file.pdf.base import PDFReader
from llama_index import Document, ServiceContext, VectorStoreIndex
from llama_index.llms import OpenAI
from llama_index.evaluation import DatasetGenerator
from llama_index.node_parser import SimpleNodeParser
import asyncio

current_directory = os.path.dirname(os.path.abspath(__file__))
full_path = os.path.join(current_directory, '..')
sys.path.append(full_path)

from access import get_openai_key, get_pinecone_env, get_pinecone_key

# 1. Set Key values
os.environ["OPENAI_API_KEY"] = get_openai_key()
os.environ["PINECONE_ENV"] = get_pinecone_env()
environment = get_pinecone_env()
os.environ["PINECONE_API_KEY"] = get_pinecone_key()
pinecone.init(api_key=os.environ["PINECONE_API_KEY"], environment=os.environ["PINECONE_ENV"])

full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'Chatbot_db_Temp')

loader = PDFReader()
docs0 = loader.load_data(file=Path(full_path) / "2024년_자동차_이차전지_투자전략_2023-11-28_유안타증권.pdf")

doc_text = "\n\n".join([d.get_content() for d in docs0])
docs = [Document(text=doc_text)]

node_parser = SimpleNodeParser.from_defaults(chunk_size=1024)
base_nodes = node_parser.get_nodes_from_documents(docs)

print(base_nodes)

rag_service_context = ServiceContext.from_defaults(
    llm=OpenAI(model="gpt-3.5-turbo")
)

index = VectorStoreIndex(base_nodes, service_context=rag_service_context)

query_engine = index.as_query_engine(similarity_top_k=2)

eval_service_context = ServiceContext.from_defaults(llm=OpenAI(model="gpt-4"))

dataset_generator = DatasetGenerator(
    base_nodes[:20],
    service_context=eval_service_context,
    show_progress=True,
    num_questions_per_chunk=3,
)

async def main():
    eval_dataset = await dataset_generator.generate_dataset_from_nodes(num=60)
    # ... the rest of your code ...

# Run the asynchronous main function
asyncio.run(main())


