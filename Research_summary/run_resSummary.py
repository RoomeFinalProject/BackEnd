# 기본설정, 모듈가져오기, openai API KEY 세팅, 코드에 세팅 (리소스로 뺴도 되고)
# Git에 올리는 것은 주의 (KEY 때문에)

# AWS의 lambda로 가면 환경변수로 세팅
from fastapi import FastAPI, Request
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
from Loading import file_names
from resSummary import summary_list
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware



###02. 객체, 답변 생성 ------------------------------------------------------------------------------------------------------
'''
구동 절차: GPT 답변 -> 채팅메시지 구성, 카카오톡 서버 전달
1. 응답 결과를 담고있는 큐 객체 생성.
2. 응답 스타일 설정
2.1 text_response_json_format
2.2 image_response_json_format
2.3 timeover_response_json_format
2.4 empty_response 
'''

# 큐 객체 생성
response_queue = q.Queue() # 응답결과를 담고 있는 큐

# 정상 답변 2개, 시간 지연 답변 1개

# GPT 답변 -> 채팅메시지 구성, 카카오톡 서버 전달 -----------------------------------------
# SimpleText, SimpleImage 채팅 메세지 구성
# GPT 답변 -> 카카오톡 스타일로 질의응답 텍스트
text_response_json_format = lambda msg: {
    "version": "2.0",
    "template": {
        "outputs": [
            {
                "simpleText": {
                    "text": msg
                }
            }
        ]
    }
}

# GPT 답변 -> 질의응답 url
image_response_json_format = lambda url, msg:{
    "version": "2.0",
    "template": {
        "outputs": [
            {
                "simpleImage": {
                    "imageUrl": url,
                    "altText": msg  # + ' 관련 내용 이미지 입니다.'
                }
            }
        ]
    }
}
# print( image_response_json_format('https://도메인/a.png' , '춤추는 고양이'))

# 답변이 지연(5초 이내 불가), 지연 메시지를 보내고, 답변을 다시 요청받기 위한 버튼 생성
# 버튼 생성의 내용 => "quickReplies"
# 응답 시간 초과시 답변 내용
timeover_response_json_format = {
    "version": "2.0",
    "template": {
        "outputs": [
            {
                "simpleText": {
                    "text": "답변 준비중입니다... \n 잠시후\
                    에 다시말풍선을 눌러서 요청해주세요"
                }
            }
        ], 
        "quickReplies": [
            {
                "messageText": '다시 물어보아도 될까요?',
                "action": "message",
                "label": "다시 물어보아도 될까요?"
            }
        ]
    }
}

# 대응 안하면 답변 ->  상대방 메세지를 읽지 않은 것으로 처리됨, 타임아웃 해당없음.
empty_response = {
    "version": "2.0",
    "template": {
        "outputs": [],
        "quickReplies" : []
    }
}


# 텍스트(로그) 파일 초기화
def init_res_log( filename, init_value=None ) :
    with open(filename, 'w') as f:
        if not init_value:
            f.write('')
        else:
            f.write('init_value')


# GPT 텍스트 질문과 답변
    '''
    GPT가 질문을 받고 답변을 하는 부분이므로 이 부분이 핵심
    '''
def get_qa_by_GPT(prompt):
    
    print('prompt:', prompt)
    print('GPT 요쳥')
    #message = my_chatbot(prompt)
    #print('GPT 응답', message)
    #return message


#4. 요청 / 응답 처리 메인 ---------------------------------------------------
# 1. 앱생성
app = FastAPI()
app.mount("/imgs", StaticFiles(directory="imgs"), name='images')
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

# /chat
@app.post('/chat')
async def chat(request:Request):
    # post로 전송한 데이터 획득 : http 관점(기반 TCP/IP)=> 헤더전송 이후 바디가 전송
    # 클라이언트(카카오톡에서 json 형태로 전송)의 메세지
    # request로 받아오고 다시 클라이언트에게 전송
    kakao_message = await request.json()
    print('chat:', kakao_message)
    return main_chat_proc( kakao_message, request)

print("hi")
# 라우팅
@app.get('/')
async def get_last_research():
    summary_text = summary_list(file_names)
    print("summary_text", summary_text )
    return JSONResponse(content=summary_text)

# /echo
@app.get('/echo') # 라우팅, get방식
def echo():
    return { 'message' : 'echo page'}


# 카톡에서 발송되는 메시지별로 분기 처리(비동기, 쓰레드) ------------------------------

# 요청을 실질적으로 분리해서 처리하는 메인 함수
def main_chat_proc(parameter, request):
    # 지연시간 계산, 시간 초과시 -> 재요청(버튼클릭) ->작업이 완료되었는지 체크/ 
    # 데이터-> 파일사용(rdb, nosql 등등 사용가능)
    over_res_limit     =  False         # 3.7초 이내에 답변이 완성되어서 처리되면 True
    response           = None         # 응답 JSON
    s_time             = time.time()  # 요청이 시작되는 시간

    # 응답 결과를 받은 텍스트 파일 생성(결과를 임시로 저장하는 공간)
    # 1인 사용자 기준에서는 문자 x, n명이 도면 계정별로 관리
    filename = os.getcwd() + '/user_log.txt' # 사용자별 1개
    # 해당파일 존재 여부
    # if not os.path.exists( filename ): # 해당 파일이 없다면
    with open(filename, 'w') as f:
        f.write('')


    # 큐에다 응답 결과를 담는다, 쓰레드(요청 파라미터, 큐, 파일명(결과를 임시저장))넣어서 가동
    # 쓰레드 생성 ( threading.Thread를 사용하여 새로운 쓰레드 생성)
    global response_queue
    thread = threading.Thread( # 쓰레드에서 병렬적으로 직접 일을 하는 함수
        target = responseai_per_request,  
        # request.base_url = 
        args   = (parameter, response_queue, filename, str(request.base_url))  # 함수에 전달할 파라미터
    )
    # 쓰레드 가동 -> 요청별 처리 진행 -> GPT 관련 내용은 장시간 소요된다 -> 이후 종료
    thread.start()
    
    # 5초가 지연시간 최대값 -> 4초이내를 제한적으로 계산해서 반복 체크
    while (time.time() - s_time < 3.7):
        # 큐를 체크 => 답변여부 검사
        if not response_queue.empty():  # 무언가 들어있다

            # 큐에 내용이 있다면 => 답변 추출 => 응답 구성 => over_res_limit = True로 변경 => break
            # 큐에서 답변 추출
            response = response_queue.get()  # 답변 추출
            print( ' 답변 출력: ', response)
            over_res_limit = True
            break

        # 잠시 대기
        time.sleep(0.01)     # 잠시 쉬었다가 다시체크


    # 시간이 초과되면 => 타임오버 메시지 전송   
    if not over_res_limit:
        response = timeover_response_json_format
    return response


# 요청별 답변 처리
def responseai_per_request(parameter, response_queue, filename, domain):
    print( 'responseai_per_request call')
    print( response_queue, filename)
    # 요청의 구분은 현재는 메세지를 기반으로 분류함(규칙기반)
    user_question = parameter["userRequest"]["utterance"]

    # 타임오버에 대한 요청
    if '다시 물어보아도 될까요?' in user_question:
        # 파일을 읽어서 -> 내용이 존재하면 -> 내용을 읽어서 응답 큐에 세팅
        # 중복 응답의 가능성이 있어서 배제
        pass
    
    # 단순 텍스트 질의 요청 -> GPT 질의
    elif '@que' in user_question:
        # 답변을 저장하고 있는 로그파일 초기화
        init_res_log( filename )
        # 질문에서 @qa 제외 => 프럼프트 구성
        prompt = user_question.replace('@que', '').strip()
        # GPT에게 질의 -> 질의결과로 블락(응답 지연후 발생) -> 응답
        gpt_answer = get_qa_by_GPT( prompt )
        # Queue 에 응답을 넣는다.
        response_queue.put( text_response_json_format(gpt_answer) )
        # 로그기록
        init_res_log( filename, init_value=f'@que {str(gpt_answer)} ' )

    # 예상치 못한 케이스 : 이미지도 아니고, 텍스트도 아닌?
    else:
        response_queue.put( empty_response)

    pass
