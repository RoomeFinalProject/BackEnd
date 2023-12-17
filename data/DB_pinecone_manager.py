import os
import sys
current_directory = os.path.dirname(os.path.abspath(__file__))
full_path = os.path.join(current_directory, '..')
sys.path.append(full_path)
from access import get_openai_key, get_pinecone_env, get_pinecone_key
import pinecone
import shutil

# 1. Key값 설정
os.environ["OPENAI_API_KEY"] = get_openai_key()
os.environ["PINECONE_ENV"] = get_pinecone_env()
environment = get_pinecone_env()
os.environ["PINECONE_API_KEY"] = get_pinecone_key()
pinecone.init(api_key=os.environ["PINECONE_API_KEY"],environment=os.environ["PINECONE_ENV"])

# Index 생성
# dimensions are for text-embedding-ada-002
def pinecone_clear():
    # Index 삭제
    pinecone.delete_index("openai")
    
    return print('openai index has been deleted')

def pinecone_creator():
    index_name = 'openai'
    if 'openai' not in pinecone.list_indexes():
        pinecone.create_index(index_name, dimension=1536, metric="euclidean", pod_type="p1")
    #index = pinecone.Index('openai')
    
    return print('openai index has been created')


# Define the paths
def copy_files(source_directory = 'Research_daily', destination_directory = 'testdata'):
    for subdirectory in os.listdir(source_directory):
        subdirectory_path = os.path.join(source_directory, subdirectory)
        for file_name in os.listdir(subdirectory_path):
            file_path = os.path.join(subdirectory_path, file_name)
            if os.path.isfile(file_path):
                destination_path = os.path.join(destination_directory, file_name)
                shutil.copy2(file_path, destination_path)
                print(f"Copied {file_path} to {destination_path}")


if __name__ == "__main__":
    #pinecone_clear()
    #pinecone_creator()
    #copy_files('Research_ranktop')
    pass