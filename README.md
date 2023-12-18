
# [1] 유튜브 자막요약(summary.py)

# 설치

    - pip install fastapi
        - conda install fastapi -y
    - pip install "uvicorn[standard]"
        - conda install "uvicorn[standard]" -y

# redis 설정

    Redis   ※ 유튜브 api 호출을 최소화 하기 위해 씀
        - 코드 사용시 반드시 redis.exe를 실행시킨 상태일것
        - del UCr7XsrSrvAn_WcU4kF99bbQ     : 이 명령어를 redis.cli 창에서 실행하면 레디스에 저장된 데이터가 삭제된다(ex: del 채널아이디)

# mongodb 설정

    버전: 5.023
    사용자: localhost
    포트: 27017 (기본값)

    사용법
    - 윈도우 검색에 시스템 환경변수 편집을 입력 => 고급 탭에서 환경변수 설정으로 들어간다
    - 환경변수 path 에 mongodb 의 bin 파일을 지정하면 cmd 창에서
        mongod
        mongo    
    - 입력해서 실행시킨뒤 MongoDBCompass 실행
        ※ mongod, mongo 가 실행중인 창을 닫으면 안됨!

        - 첫 화면 중앙에 보이는 uri 창에 mongodb://localhost:27017 가 떠있는지 확인하고 connect를 누른다
        - 좌측상단 localhost:27017 이라는 초록색 버튼을 누르고 하위 항목인 database에 들어가서 db 문서를 확인한다

    - vscode에서 아래의 코드로 db와 연결 가능함
        
        # 사용 예시
        
        mongo_client = MongoClient('mongodb://localhost:27017/')    => 로컬호스트, 포트번호 지정
        db = mongo_client['youtube_summary_db']                     => db 문서명
        collection = db['summary']                                  => db 콜렉션명

# 구동

    - 가상환경을 생성하고 commend prompt 창에서

        uvicorn summary:app --reload

# 코드 작동 원리(중요)

    [0] 작동전 세팅
        - openai_api_key 와 youtube_api 키, service_account_key를 py파일이 있는 폴더의 상위 폴더에 넣고 상대경로를 지정한다
        - 채널id와 유튜버명을 매핑시킨다(가독성을 향상시키고, 코드 유지보수가 용이해짐)

    [1] redis 에서 데이터 확인: 유튜버 채널id로 데이터 인덱스 저장 및 검색(=키 역할)
        [1-1] redis에 임시로 저장된 캐시 데이터가 있을 경우
            - redis에서 데이터를 가져오고 [2]번 항목으로 넘어간다
            
        [1-2] redis에 캐시 데이터가 없을 경우
            - youtube_api_key를 통해 유튜브로 부터 데이터를 제공받아 채널id를 이용하여 redis 에 영상타이틀과 자막원본을 저장하고 [2]번 항목으로 넘어간다
                - 제공 받는 데이터: 유튜버명, 영상타이틀, 자막원본
                    - 영상타이틀에 데이터 전처리 수행(이모지 제거, 특수문자로 인한 글자깨짐 개선)
    
    [2] 모델 색인화 - 요약수행 모델: XLM-RoBERTa (다국어로 훈련된 언어 모델)
                    - 벡터디비: GPT3.5 turbo

    [3] 자막 요약전 db에 요약본이 있는지 확인: 유튜버 채널 id와 영상 타이틀로 인덱스 저장 및 검색(=2가지 키)

        - [3-1] 있으면 불러와서 유튜버명, 영상타이틀, 자막요약 3개를 묶어서 서버에 라우트한다
        - [3-2] 없으면 자막원본을 불러와 모델로 요약을 실행한뒤 요약본을 db에 저장한다. 그 후 [3]번 항목 처음으로 돌아감
    
    [4] 목표: 서버에 아래의 항목을 전송한다
        --------------------------------------------
        | 유튜버명  :                               |
        | 영상게시일:                               |
        | 영상썸네일:                               |
        | 영상타이틀:                               |
        | 요약내용  :                               |
        --------------------------------------------

# 한계점

    1. api_key 할당량 때문에 제한적인 부분이 많았고(실시간 자동 업데이트 기능이나 한번에 대용량의 데이터 호출에 제약이 있음)
    2. 자막을 가져올때 불용어가 많이 섞여있거나, 유튜버가 콩글리시 같은 은어나 한글로 외래어 표현을 많이 할 경우 요약에 영향이 있음
    3. 자막을 지원하지 않는 영상은 데이터 접근 자체가 불가능함
    4. 쿼리 호출 함수에 제약이 많고 예외 사항이 많음
        - 영상길이 제한 videoDuration 함수는 short(4분이내), medium(4~20분), long(20분이상) 3가지만 쓸수있고 short 만 빼고 가져온다 같은 예외처리를 하려면 2번 호출해야함
        - 일반영상, 실시간스트리밍영상, 예약방송 등 영상타입도 나눠져있고, 일반영상중에는 올라오자마자 자막이 올라오지 않는 경우도 있음
        - 자막이 없거나, 자막 지원을 안하거나, 비공개 영상이 검색되는 경우도 발생함

# [2] 리서치요약, 챗봇

설정 순서
1.1 가상환경 만들기
    - python -m venv venv_chatbot

1.2 gitignore 설정
    - .gitignore 파일 생성

1.3 requirements.txt
    - 필요한 pip을 install 해준다. - pip freeze > requirements.txt

1.4 git 연결
    - git remote에 branch 생성: 여기서는 'chatbot'
    - git remote add origin https://github.com/RoomeFinalProject/Model.git
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
