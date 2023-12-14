
# 파이썬 기반 웹서비스

    - flask, Django, fastapi
    - fastapi
        - flask 와 유사하게 자유도가 높고, 빠르게 구축가능
        - 처리속도는 가장 빠르고, 비동기 처리도 유연하다
        - 모델 서빙등에 많이 사용된다.

# 설치

    - pip install fastapi
        - conda install fastapi -y
    - pip install "uvicorn[standard]"
        - conda install "uvicorn[standard]" -y
    - uvicorn run_JJ:app --reload --port 8001 (8001번 포트로 실행)

# 코드 실행전 주의사항

    Redis
        - 코드 사용시 반드시 redis.exe를 실행시킨 상태일것
        - del UCr7XsrSrvAn_WcU4kF99bbQ     : 이 명령어를 redis.cli 창에서 실행하면 레디스에 저장된 데이터가 삭제된다(ex: del 채널아이디)

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
    - uvicorn summary:app --reload

# 확인용

# git에서 다음과 같은 오류일떄

- error: failed to push some refs to 'https://github.com/userId/userProject.git'
  -> git pull origin 브런치명 --allow-unrelated-histories 하고 다시 add - commit - push 하면 행복 git
