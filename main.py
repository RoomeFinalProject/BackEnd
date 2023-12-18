from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
# from Backend 폴더내의 쓰여지는 주요 함수모음
from youtube_summary.summary import get_latest_video # Import the summary function
from youtube_summary.summary import get_video_info, channel_mapping
from Research_summary.run_resSummary import summary_list
from Research_summary.Loading import file_names
from Chatbot.run_Chatbot import main_chat_proc
from youtube_summary.link_summary import get_transcript, summarize_with_langchain_and_openai

# 라우터 모음
from Chatbot.run_Chatbot import router as home_router
from youtube_summary.summary import router as youtube_summary_router
from Research_summary.run_resSummary import router as research_summary_router
from youtube_summary.link_summary import router as linked_summary_router
from Chatbot.run_Chatbot import router as chatbot_router
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse


app = FastAPI()
app.mount("/imgs", StaticFiles(directory="imgs"), name='images')


# home ----------------------------------------------------------------------
@app.get("/")
def home():
    return {'message':'home page'}

# youtube_summary -----------------------------------------------------------
@app.get("/youtube")
async def get_latest_video():
    all_video_data = []
    for channel_id, channel_name in channel_mapping.items():
        video_info = get_video_info(channel_id, channel_name)
        all_video_data.append(video_info)
        print( '종료' )
        #break
    print(all_video_data)

    return JSONResponse(content=all_video_data)

@app.get("/linkedVideo")
async def linked_video(request: Request, link: str):
    try:
        progress = 0
        status_text = ''

        status_text = '트랜스크립트 불러오는 중...'
        progress = 25

        # Getting both the transcript and language_code
        
        transcript, language_code = get_transcript(link)
        status_text = '요약본 생성 중...'
        progress = 75

        model_name = 'gpt-3.5-turbo'
        summary = await summarize_with_langchain_and_openai(transcript, language_code, model_name)
        print(summary)
        status_text = '요약:'
        progress = 100
        
        return JSONResponse(content={"summary": summary})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ----------------------------------------------------------------------------
# research_summary -----------------------------------------------------------
@app.get('/research')
async def get_last_research():
    summary_text = summary_list(file_names)
    print("summary_text", summary_text )
    return JSONResponse(content=summary_text)



# ----------------------------------------------------------------------------
# chatbot --------------------------------------------------------------------
@app.post("/chat")
async def chat(request:Request):
    # post로 전송한 데이터 획득 : http 관점 (기반 TCP/IP) => 헤더 전송 이후 바디 전송
    kakao_message = await request.json() # 클라이언트 (카카오톡에서 json 형태로 전송)의 메시지
    print('chat', kakao_message)
    return main_chat_proc(kakao_message, request)

# ----------------------------------------------------------------------------


# Include routers from each functionality file
# app.include_router(home_router, prefix="/home", )
app.include_router(youtube_summary_router, prefix="/youtube", tags=["youtube"])
app.include_router(research_summary_router, prefix="/research", tags=["research"])
app.include_router(chatbot_router, prefix="/chat", tags=["chat"])
app.include_router(linked_summary_router, prefix="/linkedVideo", tags=["linkedVideo"])

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

