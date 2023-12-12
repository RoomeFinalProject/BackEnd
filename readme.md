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

    - uvicorn summary:app --reload

# 확인용

# git에서 다음과 같은 오류일떄

- error: failed to push some refs to 'https://github.com/userId/userProject.git'
  -> git pull origin 브런치명 --allow-unrelated-histories 하고 다시 add - commit - push 하면 행복 git
