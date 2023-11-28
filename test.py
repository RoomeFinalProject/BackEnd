# 기본설정, 모듈가져오기, openai API KEY 세팅, 코드에 세팅 (리소스로 뺴도 되고)
# Git에 올리는 것은 주의 (KEY 때문에)

#0. 모듈 세팅
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles   # 정적 디렉토리를 지정함.
import json
from openai import OpenAI
import os
import threading # 동시에 여러작업을 가능케 하는 페키지
import time      # 답변 시간 계산용, 제한 시간 체크해서 대응
import queue as q # 자료구조 큐, 요청을 차곡차곡 쌓아서 하나씩 꺼내서 처리
import urllib.request as req
import numpy as np

### 각종 객체 생성 ###============================================================

# openAI객체 생성
def get_openai_key():
    try:
        key_path = 'openai_key.json'
        with open (key_path) as f:
            data = json.load(f)
        key = data['OPENAI_API_KEY']
    except Exception:
        # AWS Lambda의 환경변수
        key = os.environ['OPENAI_API_KEY']
    return key

client = OpenAI(
    api_key =  get_openai_key()
)
response_queue = q.Queue()

### 포맷 ###



# 객체생성 end ============================================================


# end ========================================================================

# 답변 포맷

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

timeover_response_json_format = {
    "version": "2.0",
    "template": {
        "outputs": [
            {
                "simpleText": {
                    "text": "아직 저의 고민이 끝나지않았습니다. 다시말풍선을 눌러서 요청해주세요"
                }
            }
        ], 
        "quickReplies": [
            {
                "messageText": '고민 다 하셨나요?',
                "action": "message",
                "label": "고민 다 하셨나요?"
            }
        ]
    }
}

empty_response = {
    "version": "2.0",
    "template": {
        "outputs": [],
        "quickReplies" : []
    }
}


# end ========================================================================

# 텍스트 질문초기화
def init_res_log( filename, init_value=None ) :
    with open(filename, 'w') as f:
        if not init_value:
            f.write('')
        else:
            f.write('init_value')


# GPT ========================================================================
def get_qa_by_GPT(prompt):
    # 채팅형, 페르소나 부여(), gpt-3.5-turbo, 응답메시지 리턴
    # 실습 (저수준 openai api 사용)

    prompt_template = [
            {
                # 페르소나 부여
                'role':'system',
                # 영어로 부여
                'content':'You are a thoughtful assistant. Respond to all input in 25 words and answer in korean'
            },
            {
                'role':'user',
                'content':prompt
            }
        ]
    global client
    print('GPT 요쳥')
    # 지연시간 발생

    response = client.chat.completions.create(
        model = 'gpt-3.5-turbo',
        messages = prompt_template
    )
    message = response.choices[0].message.content
    print('GPT 응답', message)
    return message






# 1.앱생성
app = FastAPI()
app.mount("/imgs", StaticFiles(directory="imgs"), name='images')

    # 카톡의 모든 메세지는 이 url을 타고 전송된다. -> 이안에서 분기
    # Queue : 먼저 들어온 데이터(작업(쓰레드))가 먼저 나간다- 사용
    # 쓰레드 사용(GPT가 처리하는 속도가 제각각) -> 병렬처리 진행

    # 03. 카카오톡의 응답메세지는 5초 제한룰이 있음. -> 처리(필요시 더미응답처리
    #  -> 사용자에게 메세지, 다시 확인할수 있는 버튼 제공 -> 클릭 -> 결과를 요청
    # (GPTX, 결과가 덤프되었으면 전송, 아니면 다시대기))

    # /chat
@app.post('/chat/')
async def chat(request:Request):
    # post로 전송한 데이터 획득 : http 관점(기반 TCP/IP)=> 헤더전송 이후 바디가 전송
    # 클라이언트(카카오톡에서 json 형태로 전송)의 메세지
    kakao_message = await request.json()
    print('chat:', kakao_message)
    return main_chat_proc( kakao_message, request)


@app.get('/')
def home():
    return {'message': 'homepage'}

# /echo
@app.get('/echo') # 라우팅, get방식
def echo():
    return { 'message' : 'echo page'}





# end ========================================================================

# 라우팅
# 요청 받아 분리처리 하는 메인함수 ============================================================
def main_chat_proc( kakao_message, request):
    # 파라미터(지연시간 계산)
    over_res_limit     =  False       # 3.7초 이내에 답변이 완성되어서 처리되면 True
    response           = None         # 응답 JSON
    s_time             = time.time()  # 요청이 시작되는 시간
    filename = os.getcwd() + '/user_log.txt' # 사용자별 1개
    with open(filename, 'w') as f:
        f.write('')

    # 큐에 응답결과 담고, 쓰레드에 넣어서 가동
    global response_queue
    thread = threading.Thread( 
        target = responseai_per_request,  
        args   = (parameter, response_queue, filename, str(request.base_url))  # 함수에 전달할 파라미터
    )
    thread.start()

    # 5초 지연시간
    while (time.time() - s_time < 3.7):
        # 큐를 체크 => 답변여부 검사
        if not response_queue.empty():  # 무언가 들어있다
            response = response_queue.get()  # 첫번째 답변 두번쨰 답변 식으로 답변 추출
            print( ' 답변 출력: ', response)
            over_res_limit = True
            break
        time.sleep(0.01)     # 잠시 쉬었다가 다시체크
        if not over_res_limit:
            response = timeover_response_json_format
        return response


# 요청별 답변 처리
def responseai_per_request(parameter, response_queue, filename, domain):
    print( 'responseai_per_request call')
    print( response_queue, filename)

    user_question = parameter["userRequest"]["utterance"]

    if '고민 다 하셨나요' in user_question: 
        pass
    elif '@qa' in user_question:
        init_res_log( filename )
        # 질문에서 @qa 제외 => 프럼프트 구성
        prompt = user_question.replace('@qa', '').strip()
        # GPT에게 질의 -> 질의결과로 블락(응답 지연후 발생) -> 응답
        gpt_answer = get_qa_by_GPT( prompt )
        # Queue 에 응답을 넣는다.
        response_queue.put( text_response_json_format(gpt_answer) )
        # 로그기록
        init_res_log( filename, init_value=f'@qa {str(gpt_answer)} ' )
    elif '@img' in user_question:
        pass
    else:
        response_queue.put( empty_response )





