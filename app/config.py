# 앱 전체 설정 — 값만 바꿔서 동작을 조정하는 곳

# ---- e-Paper
EPD_BAUD = 10_000_000       # Phase 1 실측: 10MHz에서 정상 (전송 126ms)
FULL_EVERY = 10             # fast 갱신을 이만큼 하면 다음 갱신은 full (잔상 제거)

# ---- 버튼 (Phase 1 key_finder 결과)
KEY0_PIN = 2
KEY1_PIN = 3
LONG_MS = 1000              # 이 시간 이상 누르면 길게 누름
DEBOUNCE_MS = 40

# ---- 시간
# RTC가 맞춰져 있지 않을 때(연도 < 2025) 대신 쓸 시각. 테스트용으로 날짜를 고정하고 싶으면
# FAKE_NOW 에 (년, 월, 일, 시, 분, 초) 를 넣으면 항상 그 시각을 사용.
FALLBACK_NOW = (2026, 10, 10, 12, 0, 0)
FAKE_NOW = None

TZ_OFFSET = 9 * 3600        # 한국 시간 = UTC + 9

# ---- 일정 데이터
CACHE_PATH = "data/events.json"         # 구글 캘린더에서 받아 저장해 둔 일정
MOCK_PATH = "data/mock_events.json"     # credentials.py 를 아직 안 채웠을 때 쓰는 예시 일정

# ---- 동기화 (credentials.py 를 채우면 동작)
SYNC_MIN = 30               # 구글 캘린더를 다시 받아오는 간격 (분)
SYNC_RETRY_MIN = 5          # 실패했을 때 다시 시도할 때까지 (분)

# ---- 화면 갱신 주기 (시계 기준 10분 단위: :00 :10 :20 ... 에 맞춰 갱신)
TODAY_TICK_MIN = 10         # 오늘 화면: 10분마다 (지금 선 이동)
OTHER_TICK_MIN = 30         # 월간/주간: 30분마다 (:00, :30)
TODAY_TICK_PARTIAL = True   # 오늘 화면 10분 갱신을 부분 갱신(깜빡임 없음)으로. 이상하면 False → fast
PARTIALS_BEFORE_FULL = 5    # 부분 갱신 5번(50분)마다 한 번은 full 로 잔상 제거 (Waveshare FAQ 기준)

# ---- 오늘 화면
TODAY_STYLE = "timeline"    # "timeline" = 시간표 (KEY1 = 다음 날), "list" = 예전 목록 (KEY1 = 다음 페이지)
TL_START_H = 7              # 시간표 시작 시각
TL_END_H = 24               # 시간표 끝 시각

# ---- 메인 루프
LOOP_MS = 20                # 버튼 확인 주기
