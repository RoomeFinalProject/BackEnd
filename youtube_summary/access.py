import sys
import json
import os


def get_openai_key():
    current_directory = os.path.dirname(os.path.abspath(__file__))
    key_path_setting = os.path.join(current_directory, 'access_key.json')
    
    try:
        key_path = key_path_setting
                      
        with open(key_path) as f:
            data = json.load(f)
        key = data["OPENAI_API_KEY"]
    except Exception:
        # AWS Lambda의 환경 변수
        key = os.environ["OPENAI_API_KEY"]
        
    return key

def get_pinecone_key():
    current_directory = os.path.dirname(os.path.abspath(__file__))
    key_path_setting = os.path.join(current_directory, 'access_key.json')
    try:
        key_path = key_path_setting
        
        with open(key_path) as f:
            data = json.load(f)

        key = data["PINECONE_KEY"]
    except Exception:
        # AWS Lambda의 환경 변수
        key = os.environ["PINECONE_KEY"]
        
    return key

def get_pinecone_env():
    current_directory = os.path.dirname(os.path.abspath(__file__))
    key_path_setting = os.path.join(current_directory, 'access_key.json')
    try:
        key_path = key_path_setting
        
        with open(key_path) as f:
            data = json.load(f)

        key = data["PINECONE_ENV"]
    except Exception:
        # AWS Lambda의 환경 변수
        key = os.environ["PINECONE_ENV"]
        
    return key