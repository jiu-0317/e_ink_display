# 예시 파일 — 이 파일을 복사해서 credentials.py 로 만든 뒤 실제 값을 채우세요.
#   copy app\credentials.example.py app\credentials.py
# credentials.py 는 .gitignore 에 들어 있어서 GitHub 에 올라가지 않습니다. 실제 값은 여기에 적지 마세요.
#
# 1) Wi-Fi: Pico 2 W 는 2.4GHz 만 지원 (5GHz 전용 이름에는 연결 안 됨)
# 2) CALENDAR_URL: Apps Script 를 "웹 앱"으로 배포하고 받은 주소 + ?token=...
#    token 은 Apps Script 편집기에 있는 Code.gs 의 TOKEN 과 똑같아야 함.
#
# 아래 값이 비어 있거나 "여기에" 가 남아 있으면, 예시 일정(data/mock_events.json)으로 동작합니다.

# 여러 곳에서 쓸 때: 위에서부터 차례로 시도 (주변에 보이는 것만). 순서 = 우선순위.
WIFI_NETWORKS = [
    ("여기에_Wi-Fi_이름", "여기에_Wi-Fi_비밀번호"),
    # ("두번째_Wi-Fi_이름", "두번째_Wi-Fi_비밀번호"),
]

CALENDAR_URL = "https://script.google.com/macros/s/여기에_배포_ID/exec?token=여기에_토큰"
