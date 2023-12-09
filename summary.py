from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import requests
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
from pathlib import Path
import redis
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware


# 레디스 클라이언트 생성: 연결 설정
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)

# 현재 스크립트 디렉토리 경로
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
service_account_file = os.path.join(script_directory, '..', 'youtube_api_key.json').replace('\\', '/')

# YouTube API 빌드
youtube = build("youtube", "v3", credentials=service_account.Credentials.from_service_account_file(service_account_file))

# 4. 채널 ID와 이름을 매핑
channel_mapping = {
    "UCr7XsrSrvAn_WcU4kF99bbQ": "박곰희TV",
    "UCv-spDeZBGYVUI9eGXGaLSg": "시윤주식",
    "UCWeYU4snOLj4Jj52Q9VCcOg": "주식하는강이사",
    # "UCFznPlqnBtRKQhtkm6GGoRQ": "달팽이주식",
    # "UCVAbB2v_MCpAWNVTGxVLRxw": "안정모의 주식투자",

}


    # "UCO8tX-tvkJmN70sALNmXhCg": "친절한 재승씨",
#     "UCWeYU4snOLj4Jj52Q9VCcOg": "주식하는강이사",
#     "UCw8pcmyPWGSik7bjJpeINlA": "기릿의 주식노트 Let's Get It",
#     "UCM_HKYb6M9ZIAjosJfWS3Lw": "미주부",
#     "UCpqD9_OJNtF6suPpi6mOQCQ": "월가아재의 과학적 투자",
#     "UCHWFdDG50K-k8btmLG_2Lcg": "어니스트와 주식 빌드업",
#     "UCWBb2cJKOIRUSI_rgndkgWw": "주주톡",
#     "UCcIkTkPN8QP3PzJuwACgxMg": "공모주린이의 투자백서",
#     "UCVAbB2v_MCpAWNVTGxVLRxw": "안정모의 주식투자",

# 5. FastAPI 애플리케이션 초기화 및 경로 정의
app = FastAPI()

# Set up CORS
origins = [
    "http://localhost:3000",  # Adjust the frontend URL as needed
    # Add other frontend origins as needed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 6. 문서 불러오기
def load_video_data(channel_id):
    redis_key = f"{channel_id}"
    loaded_data = redis_client.get(redis_key)

    if loaded_data is not None:
        loaded_data = loaded_data.decode('utf-8')
        video_title, korean_transcript = loaded_data.split("\n", 1)
        print("데이터를 Redis에서 로드했습니다.")
        
    else:
        response_items = []

        try:
            response = youtube.search().list(part="id, snippet", channelId=channel_id, order="date", maxResults=1).execute()
            # YouTube API 호출에 대한 응답 확인
            if "items" not in response:
                raise Exception("No video items in the YouTube API response")
            response_items = response.get("items", [])
        except Exception as e:
            print(f"Error during YouTube API request: {e}")
            # 발생한 예외에 대한 추가 디버깅을 위해 예외를 출력합니다.
            raise

        if response_items:
            first_item = response_items[0]
            video_id = first_item.get("id", {}).get("videoId")
            video_title = first_item.get("snippet", {}).get("title", "")
            try:
                transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=["ko"])
                if not transcript:
                    raise YouTubeTranscriptApi.CouldNotRetrieveTranscript("자막이 없습니다.")
                korean_transcript = " ".join(entry["text"] for entry in transcript)
                video_title = first_item.get("snippet", {}).get("title", "")
                redis_client.set(redis_key, f"{video_title}\n{korean_transcript}") # 레디스에 저장
            except Exception as e:
                print(f"자막을 검색하는 동안 오류가 발생했습니다: {e}")
                raise HTTPException(status_code=500, detail=f"자막 검색 중 오류 발생: {e}")
        else:
            print("API 응답에 비디오 아이템이 없습니다. API 응답을 확인하세요.")
    return video_title, korean_transcript

# 7. 문서 요약 함수
def summarize_documents(documents, embed_model):
    summaries = []
    for j, doc in enumerate(documents, start=1):
        selected_index = GPTVectorStoreIndex.from_documents([doc], service_context=ServiceContext.from_defaults(embed_model=embed_model))
        result = selected_index.as_query_engine().query(f'{j}번 텍스트의 내용을 Summarize the following in 10 bullet points.')
        print(f"문서 요약:\n{result}\n")
        summaries.append(str(result))
    return summaries

# 8. 모델 색인화 과정( 모델명: 다국어로 훈련된 언어 모델 XLM-RoBERTa )
def get_video_info(channel_id, channel_name, num_videos=1):
    all_video_data = []  # 특정 채널의 동영상 정보 저장
    try:
        for _ in range(num_videos):
            
            video_title, korean_transcript = load_video_data(channel_id) # 함수를 호출하여 Redis 캐시 또는 YouTube API에서 동영상의 제목과 한국어 대본을 가져옵니다.
            
            if video_title is not None and korean_transcript is not None:

                documents = load_documents_from_text(korean_transcript)
                # 임베딩 모델 초기화
                embed_model = LangchainEmbedding(HuggingFaceEmbeddings(
                    model_name='sentence-transformers/xlm-r-100langs-bert-base-nli-stsb-mean-tokens'
                ))
                #  문서 요약 생성
                summaries = summarize_documents(documents, embed_model)

                # 딕셔너리 생성
                video_info = {
                    "channel_name": channel_name,
                    "video_title": video_title,
                    "summary": summaries,
                }
                all_video_data.append(video_info)
    except Exception as e:
        print(f"오류가 발생했습니다: {e}")
        raise HTTPException(status_code=500, detail="오류가 발생했습니다.")
    return all_video_data

# 9.FastAPI 라우트 (경로정의)
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