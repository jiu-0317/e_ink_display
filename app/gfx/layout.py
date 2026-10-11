# 화면 좌표 체계 (가로 800 x 480, 회전 없음)
#
#   y 0-47     공통 헤더
#   y 48-479   본문 432px
#   좌우 여백 8px → 본문 폭 784 = 7열 x 112px

BLACK = 0           # MONO_HLSB 비트 0 = 검정
WHITE = 1

W, H = 800, 480
MARGIN = 8

HEADER_H = 48
BODY_Y = HEADER_H
BODY_H = H - HEADER_H           # 432
BODY_X = MARGIN
BODY_W = W - 2 * MARGIN         # 784
COLS = 7
COL_W = BODY_W // COLS          # 112

# ---- 월간
M_WDAY_Y = BODY_Y               # 요일 행
M_WDAY_H = 24
M_GRID_Y = M_WDAY_Y + M_WDAY_H  # 72
M_ROWS = 6
M_ROW_H = (H - M_GRID_Y) // M_ROWS   # 68
M_EVENT_LINES = 3

# ---- 주간
WK_HEAD_Y = BODY_Y              # 열 머리 (요일 + 날짜)
WK_HEAD_H = 40
WK_BODY_Y = WK_HEAD_Y + WK_HEAD_H    # 88
WK_BODY_H = H - WK_BODY_Y            # 392

# ---- 오늘
TD_LEFT_W = 260
TD_RIGHT_X = BODY_X + TD_LEFT_W      # 268
TD_RIGHT_W = W - MARGIN - TD_RIGHT_X  # 524
TD_ROW_H = 40
TD_LIST_Y = BODY_Y + 8
TD_FOOT_H = 48                       # 아래쪽 "내일" 영역
TD_ROWS = (H - TD_FOOT_H - TD_LIST_Y) // TD_ROW_H   # 한 페이지 행 수


def col_x(c):
    return BODY_X + c * COL_W
