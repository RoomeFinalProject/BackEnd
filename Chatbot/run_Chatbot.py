# 기본 설정, 모듈 가져오기, openai API KEY 세팅 -> 코드에 세팅 (리소스로 빼도 되고) -> GIT에 올리는 것 주의
# AWS의 lambda로 가면 환경변수로 세팅

from fastapi import FastAPI, Request, APIRouter
from fastapi.staticfiles import StaticFiles # 정적 디렉토리 (js, css, 리소스(이미지 등등)) 지정
import json
from openai import OpenAI
import os
import threading                # 동시에 여러 작업을 가능케 하는 패키지
import time                     # 답변 시간 계산용, 제한 시간 체크해서 사용
import queue as q               # 자료구조, 큐, 요청을 차곡차곡 쌓아서 하나씩 꺼내서 처리
import urllib.request as req
from .chatbot import my_chatbot

# def get_openai_key():
#     try:
#         # 개발시 로컬 파일
#         # openai_key.json 파일을 읽어 "OPENAI_API_KEY" 값을 획득
#         key_path = "C:\\Users\\USER\\Desktop\\Sesac\\SESAC_2\\openai.key.json"
        
#         with open(key_path) as f:
#             data = json.load(f)
#             #print(data)
#         key = data["OPENAI_API_KEY"]
#     except Exception:
#         # AWS Lambda의 환경 변수
#         key = os.environ["OPENAI_API_KEY"]
        
#     return key
# # openAI 객체 생성
# client = OpenAI(
#     api_key = get_openai_key()
# )

# 큐 객체 생성
response_queue = q.Queue() # 응답결과를 담고 있는 큐

# 정상 답변 2개, 시간 지연 답변 1개
# GPT 답변 -> 채팅 메시지 구성, 카카오톡 서버 전달 
# SimpleText, SimpleImage 채팅 메시지 구성
# GPT 답변 -> 카카오톡 스타일 질의응 답 텍스트
text_response_json_format = lambda msg:{
    "version" : "2.0",
    "template" : {
        "outputs" : [
            {
                "simpleText":{
                    "text":msg
                }
            }
        ]
    }
}

# GPT 답변 -> 카카오톡 스타일 이미지 생성, 텍스트 설명
image_response_json_format = lambda url, msg:{
    "version" : "2.0",
    "template" : {
        "outputs" : [
            {
                "simpleImage":{
                    "imageUrl": url,
                    "altText" : msg # + '관련내용 이미지 입니다'
                }
            }
        ]
    }
}

# 답변이 지연(5초 이내 불가), 지연 메시지를 보내고, 답변을 다시 요청 받기 위한 버튼 생성
# 버튼 생성의 내용 => 'quickReplies"
# 응답 시간 초과시 답변 내용
timeover_response_json_format = {
    "version": "2.0",
    "template": {
        "outputs": [
            {
                "simpleText": {
                    "text": "아직 저의 고민이 끝나지 않았습니다.🙏🙏\n잠시후에 다시 말풍선을 꼭 눌러서 요청해주세요👆"
                }
            }
        ],
        "quickReplies": [
            {
                "messageText": "고민 다 하셨나요?",
                "action": "message",
                "label": "고민 다 하셨나요?"
            }
        ]
    }
}

# 텍스트(로그) 파일 초기화
def init_res_log(filename, init_value = None):
    with open(filename, 'w') as f:
        if not init_value:
            f.write('')
        else:
            f.write(init_value)
    pass


# GPT 텍스트 질문과 답변
def get_qa_by_GPT(prompt):
    
    print('prompt:', prompt)
    print('GPT 요쳥')
    _, message, _ = my_chatbot(prompt)
    print('GPT 응답', message)
    return message


# GPT 이미지 생성
def get_img_by_dalle(prompt):
    print('DALL-E-3 이미지 생성 요청')
    global client
    response = client.images.generate(
        model = 'dall-e-3',
        prompt = prompt,
        size = '1024x1024',
        quality = 'standard',
        n = 1    
    )
    print('DALL-E-3 이미지 생성 완료')
    return response.data[0].url, response.date[0].revised_prompt
    
# 요청/응답 처리 메인 ----------------------------------------------
# app = FastAPI()
# app.mount("/imgs", StaticFiles(directory="imgs"), name='images')
router = APIRouter()


# 카톡의 모든 메세지는 이 url을 타고 전송된다 -> 이 안에서 분기
# 큐 데이터 구조 사용
# 쓰레드 사용 (GPT가 처리하는 속도가 제각각) -> 병렬 처리 진행
# 카카오톡의 응답 메시지는 5초 제한 룰이 있음 -> 처리(필요시 더 미응답 처리 -> 사용자에게 메시지, 다시 확인 할 수 있는 버튼 제공 -> 클릭
# -> 결과를 요청 (GPT X, 결과가 덤프 되었으면 전송, 아니면 다시 대기))

# /chat
@router.post('/chat')
async def chat(request:Request):
    # post로 전송한 데이터 획득 : http 관점 (기반 TCP/IP) => 헤더 전송 이후 바디 전송
    kakao_message = await request.json() # 클라이언트 (카카오톡에서 json 형태로 전송)의 메시지
    print('chat', kakao_message)
    return main_chat_proc(kakao_message, request)

# # 라우팅
# @router.get('/home')
# def home():
#     return {'message':'home page'}

# # /echo
# @app.get('/echo') # 라우팅, get 방식
# def echo():
#     return {'message':'home page'}

# 카톡에서 발송되는 메시지별로 분기 처리 (비동기, 쓰레드) 

# 요청을 실질 적으로 분리해서 처리하는 메인 함수
def main_chat_proc(parameter, request):
    # 지연시간 계산, 시간 초과시 -> 재요청(버튼클릭) -> 작업이 완료 되었는지 체크/데이터 -> 파일 사용 (rdb, nosql 등등 사용가능)
    over_res_limit = False # 3.7초 이내에 답변이 완성되어 처리되면 True
    response = None # 응답 JSON
    s_time = time.time() # 요청이 시작된 시간
    
    # 응답 결과를 받는 텍스트 파일 생성 (결과를 임시로 저장하는 공간)
    # 1인 사용자 기준에서는 문제 X, n 명이 되면 게정별로 관리
    filename = os.getcwd() + '/user_log.txt' # 사용자별 1개
    # 해당 파일 존재 여부로 구성
    #if not os.path.exists(filename): # 해당 파일이 없다면
    init_res_log(filename)
    
    # 큐에다 응답 결과를 담는다, 쓰레드(요청파라미터, 큐, 파일명(결과를 임시저장)) 넣어서 가동
    # 쓰레드 생성
    global response_queue
    thread = threading.Thread(
        target = responseai_per_request, # 쓰레드에서 병렬적으로 직접 일을 하는 함수
        # request.base_url => 
        args = (parameter, response_queue, filename, str(request.base_url)) # 함수에 전달할 파라미터
    )
    # 쓰레드 가동 -> 요청별 처리 진행 -> GPT관련 내용은 장시간 소요된다 -> 이후 종료
    thread.start()
    
    # 5초가 지연시간 최대값 -> 3.5 ~ 4초 이내를 제한적으로 계산해서 반복 체크
    while (time.time() - s_time < 3.7):
        # 큐를 체크 => 답변 여부 검사
        if not response_queue.empty(): # 뭔가 들어 있다.
            # 큐에 내용이 있다면 => 답변 추출 => 응답 구성 => over_res_limit_True로 변경 => break
            # 큐에서 답변 추출
            response = response_queue.get() # 답변 추출
            print('답변 출력:', response)
            over_res_limit = True # 시간내에 답변했다.
            break
        # 잠시 대기
        time.sleep(0.01) # 잠시 쉬었다가 다시 체크
        
    # 시간이 초과 되면 => 타임오버 메시지 전송
    if not over_res_limit:
        response = timeover_response_json_format
        
    return response


# 요청 답변 처리
def responseai_per_request(parameter, response_queue, filename, domain):
    print('responseai_per_request call')
    print( response_queue, filename)
    # 요청의 구분은 현재는 메시지를 기반으로 분류하겠다 (규칙 기반)
    user_question = parameter['userRequest']['utterance']
    # 타임오버에 대한 요청
    if '고민 다 하셨나요?' in user_question:
        pass
    # 단순 텍스트 질의 요청 -> GPT 질의
    elif '@qa' in user_question:
        # 답변을 저장하고 있는 로그파일을 초기화
        init_res_log(filename)
        # 질문에서 @qa 제외 => 프럼프트 구성
        prompt = user_question.replace('@qa','').strip()
        # GPT에게 질의 -> 블락(응답 지연후 발생) -> 응답
        gpt_answer = get_qa_by_GPT(prompt)
        # Queue에 응답을 넣는다.
        response_queue.put(text_response_json_format(gpt_answer))
        # 로그 기록
        init_res_log(filename, init_value = f'q{str(gpt_answer)}')
        pass
    # 이미지 생성 질의 요청 -> GPT 이미지 생성
    elif '@img' in user_question:
        # 답변을 저장하고 있는 로그파일을 초기화
        init_res_log(filename)
        
        # 질문에서 @img 제외 => 프롬프트구성
        prompt = user_question.replace('@img', '').strip()
        
        # GPT에게 질의 -> 블락(응답 지연후 발생) -> 응답
        img_url, img_text = get_img_by_dalle(prompt)
        
        # 이미지 로컬에 저장, 이름은 해시활용 (시간, 계정, 해시 등 활용)
        req.urlretrieve(img_url, f'./imgs/create_gpt.png') # 임시로 단일 파일명 저장
        
        # Queue에 응답을 넣는다.
        # 생성된 이미지는 특정한 스토리지에 다운로드 후 개별 URL로 처리하면
        # 카카오톡에서 처리 될 듯 (이미지 -> 서버 저자 혹은 aws s3에 업로드 -> aws cdn 서비스를 이용하여 URL을 획득 후 세팅 권장)
        dumy_url = domain + 'imgs/create_gpt.png'
        response_queue.put(image_response_json_format(dumy_url, img_text))
        # 로그 기록
        init_res_log(filename, init_value = f'img{str(img_url)}{str(img_text)}')
    # 예상치 못한 케이스
    else:
        pass
    pass