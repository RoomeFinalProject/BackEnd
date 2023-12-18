# 기본설정, 모듈가져오기, openai API KEY 세팅, 코드에 세팅 (리소스로 뺴도 되고)
# Git에 올리는 것은 주의 (KEY 때문에)

# AWS의 lambda로 가면 환경변수로 세팅
from fastapi import FastAPI, Request, APIRouter

from fastapi.staticfiles import StaticFiles  # 정적 디렉토리(js, css, 리소스(이미지등등)) 지정
import json
from openai import OpenAI
import os
import threading # 동시에 여러작업을 가능케 하는 페키지
import time      # 답변 시간 계산용, 제한 시간 체크해서 대응
import queue as q # 자료구조 큐, 요청을 차곡차곡 쌓아서 하나씩 꺼내서 처리
import urllib.request as req
import numpy as np
import uvicorn
from fastapi.responses import JSONResponse
from .LoadfromMongoDB import research_summary_from_DB


router = APIRouter()


# 라우팅
@router.get('/')
async def get_last_research():
    json_responses =  research_summary_from_DB(5)
    print(json_responses)
    return json_responses

