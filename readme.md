# 파이썬 기반 웹서비스
    - flask, Django, fastapi
    - fastapi 
        - flask 와 유사하게 자유도가 높고, 빠르게 구축가능
        - 처리속도는 가장 빠르고, 비동기 처리도 유연하다
        - 모델 서빙등에 많이 사용된다.

# 설치
    - pip install fastapi
    - pip install "uvicorn[standard]"

# 구동
    - uvicorn run:app --reload

# 접속
    - http://127.0.0.1:8000
    - ngrok.com 진입, 다운로드
    - ngrok config add-authtoken <개인토큰>

# 카카오톡 메시지 규격
        {
        "intent": {
            "id": "je987ax8ygx9yaupfjntvx7q",
            "name": "블록 이름"
        },
        "userRequest": {
            "timezone": "Asia/Seoul",
            "params": {
            "ignoreMe": "true"
            },
            "block": {
            "id": "je987ax8ygx9yaupfjntvx7q",
            "name": "블록 이름"
            },
            "utterance": "발화 내용", # 유저 메시지
            "lang": null,
            "user": {
            "id": "212001",
            "type": "accountId",
            "properties": {}
            }
        },
        "bot": {
            "id": "655d559d2e80044ceaed0671",
            "name": "봇 이름"
        },
        "action": {
            "name": "69bpgbfkef",
            "clientExtra": null,
            "params": {},
            "id": "exf7lvbsaqmx2bxweutcql4r",
            "detailParams": {}
        }
        }