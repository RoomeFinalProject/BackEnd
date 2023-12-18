from fastapi import FastAPI
import json
from youtube_transcript_api import YouTubeTranscriptApi
import os
import openai
from llama_index import Document, GPTVectorStoreIndex, ServiceContext
from googleapiclient.discovery import build
from google.oauth2 import service_account
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import HuggingFaceEmbeddings
from llama_index.embeddings.langchain import LangchainEmbedding
import redis
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
import re
import html
from datetime import datetime, timedelta
# nosql db와 연결(redis, mongodb)
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)                             # 레디스 클라이언트 생성: 연결 설정

mongo_client = MongoClient('mongodb://localhost:27017/')                                        # MongoDB 연결 정보
db = mongo_client['youtube_summary_db']
collection = db['summary']
script_directory = os.path.dirname(os.path.abspath(__file__))                                   # 현재 작업중인 디렉토리 상대경로 설정
# 문서처리 함수
def load_documents_from_text(transcript_text):
    sentences = transcript_text.split(".")                                                      # 주어진 텍스트 문장단위로 나눔
    documents = [Document(text=sentence.strip()) for sentence in sentences if sentence.strip()] # 
    return documents
    
# 1. load_api_key 함수 정의, OpenAI API 키 로드, 객체 생성, API 키와 서비스 계정 파일 등의 설정
def load_api_keys(api_key_file_path: str) -> tuple:
    try:
        with open(api_key_file_path, 'r') as file:
            api_key_data = json.load(file)
            youtube_api_key = api_key_data.get("youtube_api_key", "")
            return youtube_api_key
    except Exception as e:
        print(f"API 키를 로드하는 중 오류 발생: {e}")
        return "", ""
openai_api_key_path = os.path.join(script_directory, '..', 'api_key.json').replace('\\', '/')
try:
    with open(openai_api_key_path, 'r') as file:
        openai_api_key_data = json.load(file)
        openai_api_key = openai_api_key_data.get("OPENAI_API_KEY", "")
        if openai_api_key:                                                                              # 빈 문자열이 아닌 경우에만 설정
            openai.api_key = str(openai_api_key)                                                        # 문자열로 변환하여 OpenAI API 키 설정
except Exception as e:
    print(f"OpenAI API 키를 로드하는 중 오류 발생: {e}")
youtube_api_key = os.path.join(script_directory, '..', 'api_key.json').replace('\\', '/')               # fastapi_summary 상위 폴더의 키를 참조
service_account_file = os.path.join(script_directory, '..', 'api_key.json').replace('\\', '/')
youtube = build("youtube", "v3", credentials=service_account.Credentials.from_service_account_file(service_account_file))

# 2. FastAPI 애플리케이션 초기화 및 경로 정의
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

# 3. 채널 ID와 이름을 매핑: 코드의 가독성을 높이고 유지보수가 용이하게 하기위해 설정
channel_mapping = {   
    "UCr7XsrSrvAn_WcU4kF99bbQ": "박곰희TV",
    "UCO8tX-tvkJmN70sALNmXhCg": "친절한 재승씨",
    "UCWBb2cJKOIRUSI_rgndkgWw": "주주톡",
    "UCM_HKYb6M9ZIAjosJfWS3Lw": "미주부",
    "UCv-spDeZBGYVUI9eGXGaLSg": "시윤주식",
    "UCFznPlqnBtRKQhtkm6GGoRQ": "달팽이주식",
    "UC5Mjj4LKlMtP_PXlIVYGxIQ": "와조스키",
    "UCHWFdDG50K-k8btmLG_2Lcg": "어니스트와 주식 빌드업",
    "UCWeYU4snOLj4Jj52Q9VCcOg": "주식하는강이사",
    "UCw8pcmyPWGSik7bjJpeINlA": "기릿의 주식노트 Let's Get It",
}

# 4. 데이터 불러오기(if => redis 에서 데이터를 확인하고 없으면 else => youtube api key로 호출)
def load_video_data(channel_id):
    redis_key = f"{channel_id}"
    loaded_data = redis_client.get(redis_key)

    if loaded_data is not None:
        loaded_data = loaded_data.decode('utf-8')
        video_title, korean_transcript, thumbnail, publish_time = loaded_data.split("\n", 3)
        print("데이터를 Redis에서 로드했습니다.")
        response = youtube.search().list(part="id, snippet", channelId=channel_id, order="date", maxResults=1).execute()
        print(response)
        if "items" in response:
            new_thumbnail = response['items'][0]['snippet']['thumbnails']['high']['url']
            if thumbnail == new_thumbnail:                                                                  # 캐싱된 영상의 썸네일과 채널에 있는 영상 썸네일의 url 비교
                print("캐시된 썸네일과 새로운 썸네일이 동일합니다.")                                            # 같을경우 return 값 반환
            else:
                print("캐시된 썸네일과 새로운 썸네일이 다릅니다.")                                              # 다를경우 재호출해서 기존에 있던 데이터에 덮어쓰기(업데이트)
                response_items = response.get("items", [])
                if response_items:
                    first_item = response_items[0]
                    video_id = first_item.get("id", {}).get("videoId")
                    video_title = first_item.get("snippet", {}).get("title", "")
                    video_title = html.unescape(video_title)                                                # HTML 엔터티로 치환된 특수문자를 원래 문자로 돌림(글자깨짐 개선)
                    video_title = re.sub(r'[\U0001F300-\U0001F6FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF]', '', video_title)    # 이모지 제거
                    channel_name = first_item.get("snippet", {}).get("channelTitle", "")
                    thumbnail = response['items'][0]['snippet']['thumbnails']['high']['url']                # default medium, high 썸네일 크기 설정가능
                    publish_time = response['items'][0]['snippet']['publishTime']
                    try:
                        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=["ko"])
                        if not transcript:
                            raise Exception("자막이 없습니다.")
                        pattern = re.compile(r'\[음악\]|\[박수\]|여러분|환영합니다|안녕하세요|이제|다시|좀|네|자') # 자막에 포함된 [음악]과 [박수] 부분을 삭제하는 정규표현식 패턴
                        korean_transcript = " ".join(entry["text"] for entry in transcript)
                        korean_transcript = pattern.sub('', korean_transcript)                              # pattern으로 지정해둔 부분을 자막에서 삭제
                        
                        if 'T' in publish_time and 'Z' in publish_time:                                     # publish_time을 utc시 => kst시 로 변환작업
                            publish_time = re.sub(r'[TZ]', ' ', publish_time).strip()                       # 시간에 있는 T 와 Z를 공백으로 만들고 양쪽 공백제거
                            publish_time = datetime.strptime(publish_time, '%Y-%m-%d %H:%M:%S')             # 문자열을 datetime 객체로 파싱
                            publish_time += timedelta(hours=9)                                              # utc가 kst 시간보다 9시간 뒤쳐지므로 9을 더함
                            publish_time = publish_time.strftime('%Y-%m-%d %H:%M:%S')
                        else:
                            return publish_time
                    except Exception as e:
                        print(f"자막을 검색하는 동안 오류가 발생했습니다: {e}") 
                    redis_client.set(redis_key, f"{video_title}\n{korean_transcript}\n{thumbnail}\n{publish_time}", ex=259200)   # Redis에 데이터 저장/ 259200 = 3일
                    print("데이터를 Redis에 저장했습니다.")
    else:
        response_items = []
        try:
            response = youtube.search().list(part="id, snippet", channelId=channel_id, order="date", maxResults=1).execute() 
            print(response)                                   # 채널별로 최신영상 1개(maxResults=1)의 데이터를 가져온다
            if "items" not in response:
                raise Exception("No video items in the YouTube API response")
            response_items = response.get("items", [])
        except Exception as e:
            response = youtube.search().list(part="id, snippet", channelId=channel_id, order="date", maxResults=1, type="video", eventType="completed").execute()
            print(f"API 호출 중 오류가 발생했습니다: {e}")      # eventType='completed', type='video' 실시간 스트리밍 방송이나 예약인 영상은 제외
            raise
        if response_items:
            first_item = response_items[0]
            video_id = first_item.get("id", {}).get("videoId")
            video_title = first_item.get("snippet", {}).get("title", "")
            video_title = html.unescape(video_title)                                                # HTML 엔터티로 치환된 특수문자를 원래 문자로 돌림(글자깨짐 개선)
            video_title = re.sub(r'[\U0001F300-\U0001F6FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF]', '', video_title)    # 이모지 제거
            channel_name = first_item.get("snippet", {}).get("channelTitle", "")
            thumbnail = response['items'][0]['snippet']['thumbnails']['high']['url']                # default medium, high 썸네일 크기 설정가능
            publish_time = response['items'][0]['snippet']['publishTime']
            try:
                transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=["ko"])
                if not transcript:
                    raise Exception("자막이 없습니다.")
                pattern = re.compile(r'\[음악\]|\[박수\]|여러분|환영합니다|안녕하세요|이제|다시|좀|네|자') # 자막에 포함된 [음악]과 [박수] 부분을 삭제하는 정규표현식 패턴
                korean_transcript = " ".join(entry["text"] for entry in transcript)
                korean_transcript = pattern.sub('', korean_transcript)                              # pattern으로 지정해둔 부분을 자막에서 삭제
                
                if 'T' in publish_time and 'Z' in publish_time:                                     # publish_time을 utc시 => kst시 로 변환작업
                    publish_time = re.sub(r'[TZ]', ' ', publish_time).strip()                       # 시간에 있는 T 와 Z를 공백으로 만들고 양쪽 공백제거
                    publish_time = datetime.strptime(publish_time, '%Y-%m-%d %H:%M:%S')             # 문자열을 datetime 객체로 파싱
                    publish_time += timedelta(hours=9)                                              # utc가 kst 시간보다 9시간 뒤쳐지므로 9을 더함
                    publish_time = publish_time.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    return publish_time
                # save_path = os.path.join("text_data", f"{channel_name}_{video_id}_transcript.txt")    # 한글자막 필요하면 텍스트로 저장
                # with open(save_path, "w", encoding="utf-8") as file:
                #     file.write(korean_transcript)
                # print(f"데이터를 파일로 저장했습니다. 경로: {save_path}")
            except Exception as e:
                print(f"자막을 검색하는 동안 오류가 발생했습니다: {e}") 
            redis_client.set(redis_key, f"{video_title}\n{korean_transcript}\n{thumbnail}\n{publish_time}", ex=259200)   # Redis에 데이터 저장/ 259200 = 3일
            print("데이터를 Redis에 저장했습니다.")
        else:
            print("API 응답에 비디오 아이템이 없습니다. API 응답을 확인하세요.")
    return video_title, korean_transcript, thumbnail, publish_time

# 5. 문서 요약 함수 수정
def summarize_documents(channel_name, video_title, korean_transcript, thumbnail, publish_time, embed_model):
    summary = ""
    existing_summary = collection.find_one({"channel_name": channel_name, "video_title": video_title})  # MongoDB에서 자막요약 정보 조회

    if existing_summary:
        print("기존에 저장된 자막 요약을 사용합니다.")
        summary = existing_summary["summary"]
    else:
        documents = load_documents_from_text(korean_transcript)
        if documents:
            selected_index = GPTVectorStoreIndex.from_documents(documents, service_context=ServiceContext.from_defaults(embed_model=embed_model))
            result = selected_index.as_query_engine().query('텍스트의 내용을 10개의 핵심 문단으로 요약해주세요. 중복 내용이면 한번만 요약 해주세요.')
            print(f"문서 요약:\n{result}\n")
            summary = str(result)
            collection.update_one(                                                                      # MongoDB에 자막 요약 정보 저장
                {"channel_name": channel_name, "video_title": video_title},                             # collection.update_one: 문서가 있을 경우 덮어쓰기
                {"$set": {"publish_time": publish_time,"thumbnail": thumbnail,"summary": summary, "transcript": korean_transcript}},                        
                upsert=True                                                                             # upsert 문서가 없는 경우 새로운 문서를 추가
            )
            print("자막 요약을 MongoDB에 저장했습니다.")
        else:
            print("자막이 존재하지 않아 요약을 수행할 수 없습니다.")
    return summary

# 임베딩 모델 초기화
embed_model = LangchainEmbedding(HuggingFaceEmbeddings(model_name='sentence-transformers/xlm-r-100langs-bert-base-nli-stsb-mean-tokens'))

# 6. 서버에 띄울 데이터 딕셔너리 생성
def get_video_info(channel_id, channel_name):
    all_video_data = []  # 특정 채널의 동영상 정보 저장
    global embed_model
    try:
        video_title, korean_transcript, thumbnail, publish_time = load_video_data(channel_id)
        # 문서 요약 생성
        summary = summarize_documents(channel_name, video_title, korean_transcript, thumbnail, publish_time, embed_model)
        # 딕셔너리 생성
        video_info = {
            "channel_name": channel_name,
            "publish_time": publish_time,
            "thumbnail": thumbnail,
            "video_title": video_title,
            "summary": summary,
        }
        all_video_data.append(video_info)
    except Exception as e:
        print(f"오류가 발생했습니다: {e}")
    return all_video_data

# 7.FastAPI 라우트 (경로정의)
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