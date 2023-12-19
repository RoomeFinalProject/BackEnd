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

설정 순서
1.1 가상환경 만들기 - python -m venv venv_chatbot

1.2 gitignore 설정 - .gitignore 파일 생성

1.3 requirements.txt - 필요한 pip을 install 해준다. - pip freeze > requirements.txt

1.4 git 연결 - git remote에 branch 생성: 여기서는 'chatbot' - git remote add origin https://github.com/RoomeFinalProject/Model.git

    - git branch --set-upstream-to=origin/chatbot main
        - 작동하지 않으면 - git ls-remote --heads origin (remote에 branch가 잘 생겼는지 확인 후)

    - git fetch

    - branch 간 잘 연결되어 있는지 확인 - git branch -vv

    - git pull 취소
        - git reset --hard HEAD@{1}

    - git push origin main:chatbot

    - git remote -v : 현재 연결된 remote repo
    - git ls-remote --heads origin : remote repo branch의 종류
    - git push origin main:chatbot
    - git push origin -d chatbot : 원격 브랜치 삭제
    - git push origin chatbot : 원격 브랜치 추가

1.5 pip 인스톨후 여전히 실행 불가 일때 -> 어쩔수 없다 가상환경 삭제후 재설치 필요
