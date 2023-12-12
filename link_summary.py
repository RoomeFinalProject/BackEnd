from fastapi import FastAPI, HTTPException, Form, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from youtube_transcript_api import YouTubeTranscriptApi
from langchain.text_splitter import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
import openai 
import os
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI


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

# Specify the path to your .env file
env_path = 'openai_api.env'   # Change the Path
# env_path = '/Users/user/Desktop/FinalProject/youtube_summarizer_fastapi/openai_api.env'


# Load the OpenAI API key from the .env file
load_dotenv(env_path)
openai.api_key = os.getenv('OPENAI_API_KEY')

# Setup Jinja2 templates
templates = Jinja2Templates(directory="templates")

def get_transcript(youtube_url):
    video_id = youtube_url.split("v=")[-1]
    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

    # Try fetching the manual transcript
    try:
        transcript = transcript_list.find_manually_created_transcript()
        language_code = transcript.language_code  # Save the detected language
    except:
        # If no manual transcript is found, try fetching an auto-generated transcript in a supported language
        try:
            generated_transcripts = [trans for trans in transcript_list if trans.is_generated]
            transcript = generated_transcripts[0]
            language_code = transcript.language_code  # Save the detected language
        except:
            # If no auto-generated transcript is found, raise an exception
            raise Exception("적합한 트랜스크립트가 없습니다.")

    full_transcript = " ".join([part['text'] for part in transcript.fetch()])
    return full_transcript, language_code  # Return both the transcript and detected language

async def summarize_with_langchain_and_openai(transcript, language_code, model_name='gpt-3.5-turbo'):
    # Split the document if it's too long
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=0)
    texts = text_splitter.split_text(transcript)
    text_to_summarize = " ".join(texts[:4]) # Adjust this as needed
    
    # Prepare the prompt for summarization
    system_prompt = '요약을 생성해주세요!'
    prompt = f'''다음 텍스트를 {language_code}로 요약해주세요.
    텍스트: {text_to_summarize}
    
    텍스트의 내용을 Summarize the following in 10 bullet points.'''


    # Start summarizing using OpenAI
    client = OpenAI()
    
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': prompt}
        ],
        temperature=1
    )
    return response.choices[0].message.content

# @app.get("/linkedVideo", response_class=JSONResponse)
# def read_root(request: Request):
#     return templates.TemplateResponse("index.html", {"request": request})

# @app.post("/linkedVideo")
# async def linkedVideo(request: Request, link: str = Form(...)):
#     try:
#         progress = 0
#         status_text = ''

#         status_text = '트랜스크립트 불러오는 중...'
#         progress = 25

#         # Getting both the transcript and language_code
#         transcript, language_code = get_transcript(link)

#         status_text = '요약본 생성 중...'
#         progress = 75

#         model_name = 'gpt-3.5-turbo'
#         summary = await summarize_with_langchain_and_openai(transcript, language_code, model_name)

#         status_text = '요약:'
#         progress = 100
#         print(summary)
        
#         return JSONResponse(content={"summary": summary})
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# 9.FastAPI 라우트 (경로정의)
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

        status_text = '요약:'
        progress = 100
        print(summary)
        
        return JSONResponse(content={"summary": summary})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))