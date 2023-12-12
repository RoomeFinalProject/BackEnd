from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import requests
import json
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled
import os
import sys
import llama_index
import openai
from llama_index import SimpleDirectoryReader, Document, GPTVectorStoreIndex, LLMPredictor, ServiceContext, PromptHelper
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from google.oauth2 import service_account
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import HuggingFaceEmbeddings
from llama_index.embeddings.langchain import LangchainEmbedding
from pathlib import Path
import time

# load_api_key 함수 정의 추가
def load_api_key(api_key_file_path: str) -> str:
    try:
        with open(api_key_file_path, 'r') as file:
            api_key_data = json.load(file)
            return api_key_data.get("youtube_api_key", "")
    except Exception as e:
        print(f"API 키를 로드하는 중 오류 발생: {e}")
        return ""

# 현재 스크립트 디렉토리 경로
script_directory = os.path.dirname(os.path.abspath(__file__))

# Jinja2 템플릿 설정
templates = Jinja2Templates(directory=os.path.join(script_directory, "templates"))

# 채널 ID와 이름을 매핑
channel_mapping = {
    "UCr7XsrSrvAn_WcU4kF99bbQ": "박곰희TV",
    "UCFznPlqnBtRKQhtkm6GGoRQ": "달팽이주식",
    "UCWeYU4snOLj4Jj52Q9VCcOg": "주식하는강이사",
    "UCw8pcmyPWGSik7bjJpeINlA": "기릿의 주식노트 Let's Get It",
    "UCM_HKYb6M9ZIAjosJfWS3Lw": "미주부",
    "UCv-spDeZBGYVUI9eGXGaLSg": "시윤주식",
    "UCO8tX-tvkJmN70sALNmXhCg": "친절한 재승씨",
    "UCpqD9_OJNtF6suPpi6mOQCQ": "월가아재의 과학적 투자",
    "UCHWFdDG50K-k8btmLG_2Lcg": "어니스트와 주식 빌드업",
    "UCWBb2cJKOIRUSI_rgndkgWw": "주주톡",
    "UCcIkTkPN8QP3PzJuwACgxMg": "공모주린이의 투자백서",
    "UCVAbB2v_MCpAWNVTGxVLRxw": "안정모의 주식투자",
}

app = FastAPI()

# API 키와 서비스 계정 파일 등의 설정
youtube_api_key = os.path.join(script_directory, '..', 'real_youtube_api_key.json').replace('\\', '/')
service_account_file = os.path.join(script_directory, '..', 'youtube_api_key.json').replace('\\', '/')

def get_latest_video(channel_id: str):
    # youtube_api_key 경로 수정: os.path.abspath 사용
    api_key = load_api_key(youtube_api_key)  # 파일에서 API 키 로드
    if not api_key:
        print("YouTube API 키를 확인하십시오.")
        return None, None

    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={channel_id}&maxResults=1&order=date&type=video&key={api_key}"

    # API 요청 간격을 설정하기 위한 변수
    time.sleep(1)  # 1초 간격으로 설정
    
    data = None  # data를 None으로 초기화
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if "items" in data and data["items"]:
            latest_video_id = data["items"][0]["id"]["videoId"]
            latest_video_title = data["items"][0]["snippet"]["title"]
            return latest_video_id, latest_video_title
    except requests.exceptions.RequestException as e:
        print(f"YouTube API 요청 오류: {e}")
        print(f"Response Content: {response.content}")

    print(data)
    return None, None


# FastAPI 채널 정보를 위한 라우트
@app.get("/channel/{channel_id}")
async def get_channel(request: Request, channel_id: str):
    json_dir = os.path.join(script_directory, "json_files")
    channel_name = channel_mapping.get(channel_id)
    if not channel_name:
        raise HTTPException(status_code=404, detail="채널을 찾을 수 없습니다.")

    # 최신 동영상 정보 가져오기
    latest_video_id, latest_video_title = get_latest_video(channel_id)
    if not latest_video_id:
        raise HTTPException(status_code=404, detail="최신 동영상을 찾을 수 없습니다.")

    # 동영상의 한글 자막 가져오기
    transcript, json_path = get_korean_transcript(latest_video_id, json_dir)
    if transcript is None:
        raise HTTPException(status_code=404, detail="한글 자막을 찾을 수 없습니다.")

    # 자막 요약
    summary = summarize_transcript(transcript, latest_video_id)

    # 채널명, 동영상 제목, 요약 정보 전달
    return templates.TemplateResponse(
        "channel_result.html",
        {"request": request, "channel_name": channel_name, "video_title": latest_video_title, "summary": summary},
    )


# YouTube API를 이용하여 최신 동영상 정보 가져오기
def get_latest_videos(channel_mapping, api_keys):
    videos_info = []

    for channel_id, channel_name in channel_mapping.items():
        latest_video_id, latest_video_title = get_latest_video(channel_id)
        if latest_video_id:
            videos_info.append({
                'channel_id': channel_id,
                'channel_name': channel_name,
                'latest_video_id': latest_video_id,
                'latest_video_title': latest_video_title
            })

    return videos_info

# 최신 동영상 정보 가져오기
def get_latest_video_info(channel_mapping):
    latest_video_info = {}

    for channel_id, _ in channel_mapping.items():
        latest_video_id, latest_video_title = get_latest_video(channel_id)
        if latest_video_id:
            latest_video_info[channel_id] = {
                'title': latest_video_title,
                'subtitle': f"Latest Video ID: {latest_video_id}"
            }
        else:
            latest_video_info[channel_id] = None

    return latest_video_info

# FastAPI 채널 정보를 위한 라우트
@app.get("/")
async def Roomae(request: Request):
    # 채널 정보 및 최신 동영상 정보 가져오기
    api_key = "your_api_key"  # 여기에 본인의 유튜브 API 키를 추가
    channels_with_info = get_latest_videos(channel_mapping, api_key)
    latest_video_info = get_latest_video_info(channel_mapping)

    return templates.TemplateResponse("Roomae.html", {"request": request, "channels": channels_with_info, "latest_video_info": latest_video_info})

# 한글 자막 가져오기 및 요약에 대한 공통 기능 추출
def get_korean_transcript(video_id: str, json_dir: str):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=["ko"])
    except TranscriptsDisabled as e:
        print(f"TranscriptsDisabled 에러: {e}")
        return None, None
    
    # json 파일을 저장할 경로 설정
    json_path = os.path.join(json_dir, f"{video_id}_transcript.json")

    # transcript를 json 파일로 저장
    with open(json_path, 'w', encoding='utf-8') as json_file:
        json.dump(transcript, json_file, ensure_ascii=False, indent=2)

    return transcript, json_path

json_path_list = []
    
# 요약 함수None
def summarize_transcript(transcript: str, video_id: str):
    # 저장할 json 파일 경로
    json_dir = os.path.join(script_directory, "json_files")

    # 동영상의 한글 자막 가져오기
    transcript, json_path = get_korean_transcript(video_id, json_dir)
    
    if json_path:
        json_path_list.append(json_path)

    return transcript

def save_transcript_to_json(video_id, transcript, json_dir):
    json_path = os.path.join(json_dir, f"{video_id}_transcript.json")
    with open(json_path, 'w', encoding='utf-8') as json_file:
        json.dump({"video_id": video_id, "transcript": transcript}, json_file, ensure_ascii=False, indent=4)
    return json_path

    # get_korean_transcript 함수 내의 save_transcript_to_json 호출 부분 수정
def get_korean_transcript(video_id, json_dir):
    try:
        # 동영상 정보 가져오기
        video_info = requests.get(f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}")
        video_info.raise_for_status()
        video_info = video_info.json()

        # 자막이 있는지 확인
        if 'English' in video_info['title']:
            raise Exception("이 동영상은 자막이 비활성화되어 있습니다.")

        # 자막 가져오기
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=["ko"])
        korean_transcript = " ".join(entry["text"] for entry in transcript)

        # 저장한 json 파일의 경로 반환
        json_path = save_transcript_to_json(video_id, korean_transcript, json_dir)

        return korean_transcript, json_path  # 수정된 부분: json_path 반환
    except YouTubeTranscriptApi.TranscriptsDisabled as e:
        print(f"TranscriptsDisabled 에러: {e}")
        return None, None
    except Exception as e:
        print(f"오류: {e}")
        return None, None

# 트랜스크립트를 JSON으로 저장하는 헬퍼 함수
def save_transcript_to_json(video_id, transcript, json_dir):
    json_path = os.path.join(json_dir, f"{video_id}_transcript.json")
    with open(json_path, 'w', encoding='utf-8') as json_file:
        json.dump({"video_id": video_id, "transcript": transcript}, json_file, ensure_ascii=False, indent=4)
    return json_path

# JSON에서 문서를 로드하는 헬퍼 함수
def load_documents_from_json(json_dir):
    documents = []

    # json_dir 디렉토리에 있는 모든 JSON 파일을 읽어옴
    for filename in os.listdir(json_dir):
        if filename.endswith(".json"):
            file_path = os.path.join(json_dir, filename)

            # JSON 파일에서 데이터를 읽어와 문서 객체를 생성
            with open(file_path, 'r', encoding='utf-8') as json_file:
                data = json.load(json_file)
                video_id = data.get("video_id", "")
                transcript = data.get("transcript", "")
                document = Document(text=transcript, metadata={"video_id": video_id})
                documents.append(document)

    return documents

# 한글 자막을 가져오고 텍스트로 변환하고 JSON 형식으로 저장하고 내용을 요약하는 라우트
@app.get("/process_video/{video_id}")
async def process_video(request: Request, video_id: str):
    # 한글 자막 가져오기
    json_dir = os.path.join(script_directory, "json_files")
    transcript, json_path = get_korean_transcript(video_id, json_dir)
    if transcript is None:
        raise HTTPException(status_code=404, detail="한글 자막을 찾을 수 없습니다.")

    # 트랜스크립트를 JSON으로 저장
    json_path = save_transcript_to_json(video_id, transcript, json_dir)

    # JSON에서 문서로드
    documents = load_documents_from_json(json_dir)

    # GPTVectorStoreIndex를 사용하여 색인 생성
    index = GPTVectorStoreIndex.from_documents(documents)

    # 허깅페이스 기반 임베딩 모델 생성
    embed_model = LangchainEmbedding(HuggingFaceEmbeddings(
        model_name='sentence-transformers/xlm-r-100langs-bert-base-nli-stsb-mean-tokens'
    ))

    service_context = ServiceContext.from_defaults(embed_model=embed_model)

    # 임베딩을 사용하여 문서로 색인 생성
    index_embed = GPTVectorStoreIndex.from_documents(
        documents,
        service_context=service_context
    )

# 내용 요약
summary_results = []  # 요약 결과를 저장할 리스트 초기화
json_dir = os.path.join(script_directory, "json_files")
documents = load_documents_from_json(json_dir)
for j, doc in enumerate(documents, start=1):
    selected_index = GPTVectorStoreIndex.from_documents([doc], service_context=ServiceContext.from_defaults(embed_model=embed_model))
    result = selected_index.as_query_engine().query(f'{j}번 텍스트의 내용을 Summarize the following in 10 bullet points.', language="ko")

    # 결과를 리스트에 추가
    summary_results.append({f"{j}번 문서 요약 (Selected Model)": result})
        
# FastAPI 라우트: 요약 버튼을 눌렀을 때의 동작
@app.post("/summarize/{video_id}")
async def summarize_video(request: Request, video_id: str):
    # 동영상의 한글 자막 가져오기
    transcript = get_korean_transcript(video_id)
    if not transcript:
        raise HTTPException(status_code=404, detail="한글 자막을 찾을 수 없습니다.")

    # 자막 요약
    summary = summarize_transcript(transcript)

    # 요약 결과 반환
    return {"summary": summary_results}