# 구글 캘린더 연결하기 (Apps Script 웹 앱)

Pico 가 구글 로그인을 직접 하지 않도록, 내 구글 계정에서 도는 작은 스크립트(Apps Script)가
캘린더 일정을 JSON 으로 바꿔서 주소 하나로 내보냅니다. Pico 는 30분마다 그 주소를 읽기만 합니다.

```
Pico 2 W ──HTTPS GET──▶ script.google.com/.../exec?token=비밀값 ──▶ 내 구글 캘린더
         ◀── {"events": [{"title": ..., "start": ..., "end": ...}, ...]} ──
```

## 1. 스크립트 만들기 (5분)

1. https://script.google.com 접속 → **새 프로젝트**
2. 왼쪽 위 제목을 `e-paper 달력` 등으로 바꾸기
3. `Code.gs` 안의 내용을 모두 지우고, 이 폴더의 **Code.gs** 내용을 통째로 붙여 넣기 → 저장(Ctrl+S)
4. 필요하면 맨 위 설정 수정
   - `CALENDAR_IDS`: 기본은 내 기본 캘린더(`'primary'`)만. 공휴일을 같이 보려면 아래 줄의 `//` 를 지우기
   - 다른 캘린더 ID: 구글 캘린더 → ⚙ 설정 → 왼쪽에서 캘린더 선택 → "캘린더 통합" → **캘린더 ID**
   - `TOKEN`: 이미 무작위 값이 들어 있음. 바꾸면 Pico 의 `credentials.py` 주소 끝도 똑같이 바꾸기
5. 왼쪽 ⚙ **프로젝트 설정** → **시간대**를 `(GMT+09:00) 서울` 로 (종일 일정 날짜가 하루 밀리지 않도록)

## 2. 권한 허용 + 테스트

1. 편집기 위쪽 함수 선택에서 **test** 고르고 ▶ **실행**
2. "승인 필요" → 내 구글 계정 선택
3. "Google에서 확인하지 않은 앱" 경고가 나오면 → **고급** → **(안전하지 않음)으로 이동** → **허용**
   (내가 만든 스크립트가 내 캘린더를 읽는 것이라 괜찮습니다)
4. 아래 **실행 로그**에 `일정 N개` 와 일정 몇 개가 보이면 성공

## 3. 웹 앱으로 배포

1. 오른쪽 위 **배포** → **새 배포**
2. ⚙(유형 선택) → **웹 앱**
3. 설정
   - 다음 사용자 인증 정보로 실행: **나**
   - 액세스 권한이 있는 사용자: **모든 사용자**  ← Pico 는 로그인 없이 접속하므로 꼭 이것
4. **배포** → 나오는 **웹 앱 URL** (`https://script.google.com/macros/s/AKfy.../exec`) 복사

"모든 사용자" 라도 주소 끝의 `token` 이 맞아야만 일정을 돌려줍니다. 주소와 token 은 남에게 알려주지 마세요.

## 4. 브라우저로 확인

주소창에 `웹앱URL?token=TOKEN값` 을 넣어 보세요.

- `{"now":..., "tz":"Asia/Seoul", "events":[...]}` 가 보이면 성공
- `{"error":"forbidden"}` → token 이 Code.gs 의 값과 다름

## 5. Pico 설정

`app/credentials.py` 를 열어서:

```python
WIFI_SSID = "집 와이파이 이름"        # 2.4GHz
WIFI_PASSWORD = "비밀번호"
CALENDAR_URL = "https://script.google.com/macros/s/AKfy.../exec?token=QQtIT-iI-Mk8oTDp4ruk8ORY"
```

저장 → **Upload project to Pico** → `main.py` 실행.

## 나중에 Code.gs 를 고쳤다면

저장만 해서는 웹 앱에 반영되지 않습니다. **배포 → 배포 관리 → ✏ 수정 → 버전: 새 버전 → 배포**
(이렇게 하면 주소가 그대로 유지됩니다. "새 배포"를 하면 주소가 바뀌니 주의)
