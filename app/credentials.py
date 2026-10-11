# 비밀 정보 — 이 파일은 다른 사람과 공유하지 마세요.
#
# 1) Wi-Fi: Pico 2 W 는 2.4GHz 만 지원 (5GHz 전용 이름에는 연결 안 됨)
# 2) CALENDAR_URL: Apps Script 를 "웹 앱"으로 배포하고 받은 주소 + ?token=...
#    token 은 tools/apps_script/Code.gs 의 TOKEN 과 똑같아야 함.
#
# 아래 값이 비어 있거나 "여기에" 가 남아 있으면, 예시 일정(data/mock_events.json)으로 동작합니다.

WIFI_SSID = "reptitude"
WIFI_PASSWORD = "rootroot"

CALENDAR_URL = "https://script.google.com/macros/s/AKfycbxoGL3QwOER-yPo9I6YJZdcImrPmr4gUo4iMhdADZNgTdX_zHpX_DTLkNbLotB5y31VYQ/exec?token=QQtIT-iI-Mk8oTDp4ruk8ORY"
