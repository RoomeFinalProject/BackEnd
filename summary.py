from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
import json
from youtube_transcript_api import YouTubeTranscriptApi
import os
import openai
from llama_index import SimpleDirectoryReader, Document, GPTVectorStoreIndex, LLMPredictor, ServiceContext, PromptHelper
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from google.oauth2 import service_account
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.embeddings import OpenAIEmbeddings
from llama_index.embeddings.langchain import LangchainEmbedding
import redis
from fastapi.responses import JSONResponse
from pymongo import MongoClient
import re
import html

# 레디스 클라이언트 생성: 연결 설정
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)

# MongoDB 연결 정보
mongo_client = MongoClient('mongodb://localhost:27017/')
db = mongo_client['youtube_summary_db']
collection = db['summary']

# 현재 작업중인 디렉토리 상대경로 설정
script_directory = os.path.dirname(os.path.abspath(__file__))

def load_documents_from_text(transcript_text):
    sentences = transcript_text.split(".")  # 문장 단위로 분리
    documents = [Document(text=sentence.strip()) for sentence in sentences if sentence.strip()]
    return documents
    
# 1. load_api_key 함수 정의 추가
def load_api_keys(api_key_file_path: str) -> tuple:
    try:
        with open(api_key_file_path, 'r') as file:
            api_key_data = json.load(file)
            youtube_api_key = api_key_data.get("youtube_api_key", "")
            return youtube_api_key
    except Exception as e:
        print(f"API 키를 로드하는 중 오류 발생: {e}")
        return "", ""

# Jinja2 템플릿 설정
templates = Jinja2Templates(directory=os.path.join(script_directory, "templates"))

# 2. OpenAI API 키 로드, 객체 생성
openai_api_key_path = os.path.join(script_directory, '..', 'openai_key.json').replace('\\', '/')

try:
    with open(openai_api_key_path, 'r') as file:
        openai_api_key_data = json.load(file)
        openai_api_key = openai_api_key_data.get("OPENAI_API_KEY", "")
        if openai_api_key:  # 빈 문자열이 아닌 경우에만 설정
            openai.api_key = str(openai_api_key)  # 문자열로 변환하여 OpenAI API 키 설정
except Exception as e:
    print(f"OpenAI API 키를 로드하는 중 오류 발생: {e}")
        
# 3. API 키와 서비스 계정 파일 등의 설정
youtube_api_key = os.path.join(script_directory, '..', 'real_youtube_api_key.json').replace('\\', '/') # fastapi_summary 상위 폴더의 키를 참조
service_account_file = os.path.join(script_directory, '..', 'service_account_key.json').replace('\\', '/')

youtube = build("youtube", "v3", credentials=service_account.Credentials.from_service_account_file(service_account_file))

# 4. 채널 ID와 이름을 매핑
channel_mapping = {
    "UCr7XsrSrvAn_WcU4kF99bbQ": "박곰희TV",
    "UCO8tX-tvkJmN70sALNmXhCg": "친절한 재승씨",
    "UCWBb2cJKOIRUSI_rgndkgWw": "주주톡",
    "UCM_HKYb6M9ZIAjosJfWS3Lw": "미주부",
    "UCv-spDeZBGYVUI9eGXGaLSg": "시윤주식",
}
#     "UCFznPlqnBtRKQhtkm6GGoRQ": "달팽이주식",
#     "UCWeYU4snOLj4Jj52Q9VCcOg": "주식하는강이사",
#     "UCw8pcmyPWGSik7bjJpeINlA": "기릿의 주식노트 Let's Get It",
#     "UCpqD9_OJNtF6suPpi6mOQCQ": "월가아재의 과학적 투자",
#     "UCHWFdDG50K-k8btmLG_2Lcg": "어니스트와 주식 빌드업",
#     "UCcIkTkPN8QP3PzJuwACgxMg": "공모주린이의 투자백서",
#     "UCVAbB2v_MCpAWNVTGxVLRxw": "안정모의 주식투자",

# FastAPI 애플리케이션 초기화
app = FastAPI()
# 5. 데이터 불러오기(if => redis 에서, else => youtube api key로 호출)
def load_video_data(channel_id):
    redis_key = f"{channel_id}"
    loaded_data = redis_client.get(redis_key)

    if loaded_data is not None:
        loaded_data = loaded_data.decode('utf-8')
        video_title, korean_transcript = loaded_data.split("\n", 1)
        print("데이터를 Redis에서 로드했습니다.")
    else:
        response_items = []
        try:    # 채널별로 최신영상 1개(maxResults=1)의 데이터를 가져온다
            response = youtube.search().list(part="id, snippet", channelId=channel_id, order="date", maxResults=1).execute()
            print(response)
            if "items" not in response:
                raise Exception("No video items in the YouTube API response")

            response_items = response.get("items", [])
        except Exception as e:
            raise

        if response_items:
            first_item = response_items[0]
            video_id = first_item.get("id", {}).get("videoId")
            video_title = first_item.get("snippet", {}).get("title", "")
            video_title = html.unescape(video_title)                                # HTML 엔터티 변환
            video_title = re.sub(r'[^\w\s\n]', '', video_title)                     # 특수문자 및 이모지 제거
            channel_name = first_item.get("snippet", {}).get("channelTitle", "")
            try:
                transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=["ko"])
                if not transcript:
                    raise Exception("자막이 없습니다.")
                korean_transcript = " ".join(entry["text"] for entry in transcript)
                
                # 텍스트 데이터를 파일로 저장
                save_path = os.path.join("text_data", f"{channel_name}_{video_id}_transcript.txt")
                with open(save_path, "w", encoding="utf-8") as file:
                    file.write(korean_transcript)
                print(f"데이터를 파일로 저장했습니다. 경로: {save_path}")
                
            except Exception as e:
                print(f"자막을 검색하는 동안 오류가 발생했습니다: {e}")
                raise HTTPException(status_code=500, detail=f"자막 검색 중 오류 발생: {e}")
            # Redis에 데이터 저장
            redis_client.set(redis_key, f"{video_title}\n{korean_transcript}")                  
            print("데이터를 Redis에 저장했습니다.")
        else:
            print("API 응답에 비디오 아이템이 없습니다. API 응답을 확인하세요.")

    return video_title, korean_transcript

# 6. 문서 요약 함수 수정
def summarize_documents(channel_name, video_title, korean_transcript, embed_model):
    summary = ""

    # MongoDB에서 자막 요약 정보 조회
    existing_summary = collection.find_one({"channel_name": channel_name, "video_title": video_title})

    if existing_summary:
        print("기존에 저장된 자막 요약을 사용합니다.")
        summary = existing_summary["summary"]
    else:
        documents = load_documents_from_text(korean_transcript)
        if documents:
            selected_index = GPTVectorStoreIndex.from_documents(documents, service_context=ServiceContext.from_defaults(embed_model=embed_model))
            result = selected_index.as_query_engine().query('텍스트의 내용을 Summarize the following in 10 bullet points.')
            print(f"문서 요약:\n{result}\n")
            summary = str(result)
            
            # MongoDB에 자막 요약 정보 저장
            collection.update_one(
                {"channel_name": channel_name, "video_title": video_title},
                {"$set": {"summary": summary, "transcript": korean_transcript}},
                upsert=True  # upsert 문서가 없는 경우 새로운 문서를 추가
            )
            print("자막 요약을 MongoDB에 저장했습니다.")
        else:
            print("자막이 존재하지 않아 요약을 수행할 수 없습니다.")

    return summary

# 7. 모델 색인화 과정
def get_video_info(channel_id, channel_name):
    all_video_data = []  # 특정 채널의 동영상 정보 저장
    try:
        # load_video_data 함수를 호출하여 Redis 캐시 또는 YouTube API에서 동영상의 제목과 한국어 대본을 가져옵니다.
        video_title, korean_transcript = load_video_data(channel_id)

        # 임베딩 모델 초기화
        embed_model = LangchainEmbedding(HuggingFaceEmbeddings(
            model_name='sentence-transformers/xlm-r-100langs-bert-base-nli-stsb-mean-tokens'
        ))
        documents = load_documents_from_text(korean_transcript)
        # 문서 요약 생성
        summary = summarize_documents(channel_name, video_title, korean_transcript, embed_model)
        
        # 딕셔너리 생성
        video_info = {
            "channel_name": channel_name,
            "video_title": video_title,
            "summary": summary,
        }
        all_video_data.append(video_info)
    except Exception as e:
        print(f"오류가 발생했습니다: {e}")
        raise HTTPException(status_code=500, detail="오류가 발생했습니다.")
    return all_video_data

# 8.FastAPI 라우트 (경로정의)
@app.get("/")
async def get_latest_video():
    all_video_data = []
    for channel_id, channel_name in channel_mapping.items():
        video_info = get_video_info(channel_id, channel_name)
        all_video_data.append(video_info)

    return JSONResponse(content=all_video_data)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)