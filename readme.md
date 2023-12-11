# 설치

    - pip install fastapi
        - conda install fastapi -y
    - pip install "uvicorn[standard]"
        - conda install "uvicorn[standard]" -y

# 코드 실행전 주의사항

    Redis   ※ 유튜브 api 호출을 최소화 하기 위해 씀
        - 코드 사용시 반드시 redis.exe를 실행시킨 상태일것
        - del UCr7XsrSrvAn_WcU4kF99bbQ     : 이 명령어를 redis.cli 창에서 실행하면 레디스에 저장된 데이터가 삭제된다(ex: del 채널아이디)

# 구동

    - uvicorn summary:app --reload

# 코드 작동 원리(중요)

    [1] redis 에서 데이터가 있을경우
        - redis 에서 데이터를 가져오고 [2] 번 항목으로 넘어간다
            
            [1-1] redis 에서 데이터가 없을경우
                - youtube_api_key를 통해 유튜브로 부터 데이터를 제공받아 redis 와 db 에 저장하고 [1] 번 항목으로 돌아간다
                    - 데이터: 유튜버명, 영상타이틀, 자막원본, 영상게시일
    
    [2] 모델 색인화 - 요약 모델명: XLM-RoBERTa (다국어로 훈련된 언어 모델)

    [3] 자막 요약전 db에 요약본이 있는지 확인

        - [3-1] 있으면 불러와서 유튜버명, 영상타이틀, 자막요약, 영상게시일, 자막원본 5개를 묶어서 서버에 라우트한다
        - [3-2] 없으면 자막원본을 불러와 모델로 요약을 실행한뒤 요약본을 db에 저장한다. 그 후 [3] 번 처음으로 돌아감
    
    [4] 목표: 서버에 아래와 같이 띄운다
        --------------------------------------------
        | 유튜버명  :                               |
        | 영상타이틀:                               |
        | 요약내용  :                               |
        | 자막원본  :                               |
        --------------------------------------------

# MariaDB 사용전 점검사항

1. bash 에서            mysql -u root -p -h 127.0.0.1 -P 3307   # 로그인
2. mariadb 쿼리문에서   SELECT User, Host FROM mysql.user;      # 실행
    - 권한이 없을경우   GRANT ALL PRIVILEGES ON *.* TO 'root'@'localhost' IDENTIFIED BY 'your_password' WITH GRANT OPTION;
    - 변경된 권한 적용  FLUSH PRIVILEGES;

3. 포트 3307 지정(원래 3306은 mysql mariadb 공통이지만 mysql이 3306을 쓰고 있어서 3307 지정)

    - 제어판 열기: 시작 메뉴에서 "제어판"을 검색하고 엽니다.
    - Windows 방화벽 및 고급 보안 선택: "System and Security" 카테고리에서 "Windows Defender Firewall"을 선택합니다.
    - 포트 확인: "고급 설정" 옵션을 선택하고 "인바운드 규칙"을 클릭합니다.
    - 포트 3307 추가: 오른쪽 창에서 "새 규칙 추가..."를 클릭하고 "포트"를 선택합니다. 그리고 3307을 지정하고 다음 단계를 계속 진행합니다.
    - 규칙 구성 마치기: 규칙을 추가할 때 해당 규칙이 활성화되도록 설정한 다음 마칩니다.