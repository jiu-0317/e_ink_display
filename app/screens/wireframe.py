# Phase 2 와이어프레임 — 세 화면의 뼈대를 실제 좌표·글자 크기로 그려 보는 단계
# 일정은 아래 MOCK 의 가짜 데이터. Phase 3에서 진짜 모델/레이아웃으로 교체.
#
# now = (년, 월, 일, 시, 분, 초, 요일[월=0])
import cal
from gfx.layout import (BLACK, WHITE, W, H, MARGIN, HEADER_H, BODY_X, BODY_W,
                        COL_W, col_x, M_WDAY_Y, M_WDAY_H, M_GRID_Y, M_ROWS,
                        M_ROW_H, M_EVENT_LINES, WK_HEAD_Y, WK_HEAD_H, WK_BODY_Y,
                        WK_BODY_H, TD_LEFT_W, TD_RIGHT_X, TD_RIGHT_W, TD_ROW_H,
                        TD_LIST_Y, TD_FOOT_H, TD_ROWS)
from gfx import font as F
from gfx import draw as D

N_SCREENS = 3

# ---- 가짜 일정: 오늘 기준 며칠 뒤(offset) → [(시작 "HH:MM" 또는 None=종일, 제목)]
MOCK = {
    -3: [("10:00", "Lab meeting")],
    0: [(None, "Reptitude delivery"), ("09:00", "Mplab weekly meeting"),
        ("11:00", "FP8 MAC paper review with professor"), ("13:00", "Lunch"),
        ("15:30", "Oint Reptile call"), ("19:00", "Gym"), ("21:00", "E-ink display")],
    1: [("10:00", "Thesis draft"), ("14:00", "Shop")],
    2: [("09:30", "Class"), ("13:00", "Class"), ("16:00", "Study"), ("18:00", "Dinner")],
    5: [(None, "Holiday")],
    9: [("11:00", "Interview")],
}


def _events_for(today, ymd):
    n = cal.to_ord(*ymd) - cal.to_ord(*today)
    return MOCK.get(n, [])


def _clock(now, valid):
    return "%02d:%02d" % (now[3], now[4]) if valid else "NO RTC"


# ================================================================ 월간
def month(fb, now, valid, offset=0):
    today = now[:3]
    y, m = cal.add_months(today[0], today[1], offset)
    fb.fill(WHITE)
    D.header(fb, "%d.%02d" % (y, m), _clock(now, valid), 0, N_SCREENS)

    # 요일 행 (일요일 시작). 일요일 칸은 반전
    names = ("SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT")
    for c in range(7):
        x = col_x(c)
        color = BLACK
        if c == 0:
            D.invert_box(fb, x, M_WDAY_Y, COL_W, M_WDAY_H)
            color = WHITE
        D.text_center(fb, names[c], x, M_WDAY_Y + (M_WDAY_H - F.S.h) // 2, COL_W, F.S, color)
    fb.hline(BODY_X, M_GRID_Y - 1, BODY_W, BLACK)

    grid = cal.month_grid(y, m)
    for r in range(M_ROWS):
        for c in range(7):
            ymd = grid[r * 7 + c]
            x = col_x(c)
            yy = M_GRID_Y + r * M_ROW_H
            _month_cell(fb, x, yy, ymd, ymd[1] == m, ymd == today, _events_for(today, ymd))

    # 격자선
    for c in range(8):
        fb.vline(col_x(c), M_GRID_Y, H - M_GRID_Y, BLACK)
    for r in range(1, M_ROWS):
        fb.hline(BODY_X, M_GRID_Y + r * M_ROW_H, BODY_W, BLACK)
    fb.hline(BODY_X, H - 1, BODY_W, BLACK)


def _month_cell(fb, x, y, ymd, in_month, is_today, events):
    w, h = COL_W, M_ROW_H
    if not in_month:
        D.dither(fb, x + 1, y + 1, w - 1, h - 1, D.LIGHT)
        fb.fill_rect(x + 3, y + 3, F.TINY.width("00") + 4, F.TINY.h + 4, WHITE)
        F.TINY.draw(fb, "%2d" % ymd[2], x + 5, y + 5)
        return
    color = BLACK
    if is_today:
        D.invert_box(fb, x, y, w, h)
        color = WHITE
    F.S.draw(fb, "%d" % ymd[2], x + 4, y + 2, color)
    # 일정 줄: 날짜(16px) 아래로 16px 간격 3줄
    lines = M_EVENT_LINES
    show = events if len(events) <= lines else events[:lines - 1]
    ly = y + 2 + F.S.h + 1
    for start, title in show:
        D.text_fit(fb, title, x + 4, ly, w - 8, F.S, color)
        ly += F.S.h
    if len(events) > lines:
        F.S.draw(fb, "+%d" % (len(events) - (lines - 1)), x + 4, ly, color)


# ================================================================ 주간
def week(fb, now, valid, offset=0):
    today = now[:3]
    base = cal.add_days(today[0], today[1], today[2], 7 * offset)
    days = cal.week_days(*base)
    fb.fill(WHITE)
    a, b = days[0], days[6]
    D.header(fb, "%d/%d - %d/%d" % (a[1], a[2], b[1], b[2]), _clock(now, valid), 1, N_SCREENS)

    for c, ymd in enumerate(days):
        x = col_x(c)
        color = BLACK
        if ymd == today:
            D.invert_box(fb, x, WK_HEAD_Y, COL_W, WK_HEAD_H)
            color = WHITE
        D.text_center(fb, cal.WD_SHORT[c], x, WK_HEAD_Y + 3, COL_W, F.S, color)
        D.text_center(fb, "%d/%d" % (ymd[1], ymd[2]), x, WK_HEAD_Y + 3 + F.S.h + 2, COL_W, F.S, color)
        _week_column(fb, x, WK_BODY_Y, _events_for(today, ymd))

    fb.hline(BODY_X, WK_BODY_Y - 1, BODY_W, BLACK)
    for c in range(8):
        fb.vline(col_x(c), WK_HEAD_Y, H - WK_HEAD_Y, BLACK)
    fb.hline(BODY_X, H - 1, BODY_W, BLACK)


def _week_column(fb, x, y, events):
    w = COL_W
    pad = 4
    bottom = y + WK_BODY_H - pad
    yy = y + pad
    for i, (start, title) in enumerate(events):
        need = (F.S.h + 2) if start is None else (F.S.h * 3 + 6)
        if yy + need + F.S.h > bottom and i < len(events) - 1:
            F.S.draw(fb, "+%d" % (len(events) - i), x + pad, yy)
            return
        if start is None:                          # 종일: 반전 띠
            D.invert_box(fb, x + 2, yy, w - 3, F.S.h + 2)
            D.text_fit(fb, title, x + pad, yy + 1, w - 2 * pad, F.S, WHITE)
            yy += F.S.h + 6
        else:
            F.S.draw(fb, start, x + pad, yy)
            yy = D.text_wrap(fb, title, x + pad, yy + F.S.h + 2, w - 2 * pad, F.S, max_lines=2)
            D.dashed_hline(fb, x + pad, yy + 1, w - 2 * pad, 2, 3)
            yy += 6


# ================================================================ 오늘
def today(fb, now, valid, page=0):
    t = now[:3]
    wd = now[6]
    fb.fill(WHITE)
    D.header(fb, "%d.%02d.%02d %s" % (t[0], t[1], t[2], cal.WD_SHORT[wd]),
             _clock(now, valid), 2, N_SCREENS)

    # ---- 왼쪽: 큰 날짜
    lx, lw = MARGIN, TD_LEFT_W
    D.text_center(fb, "%d" % t[2], lx, HEADER_H + 40, lw, F.XL)
    D.text_center(fb, cal.WD_LONG[wd], lx, HEADER_H + 40 + F.XL.h + 24, lw, F.M)
    D.text_center(fb, "%d.%02d" % (t[0], t[1]), lx, HEADER_H + 40 + F.XL.h + 24 + F.M.h + 12, lw, F.S)
    fb.vline(TD_RIGHT_X, HEADER_H, H - HEADER_H, BLACK)

    # ---- 오른쪽: 오늘 일정 (= 할 일)
    events = _events_for(t, t)
    rows = TD_ROWS
    n_pages = max(1, (len(events) + rows - 1) // rows)
    page = page % n_pages
    rx = TD_RIGHT_X + 12
    rw = TD_RIGHT_W - 12
    now_hm = "%02d:%02d" % (now[3], now[4])
    y = TD_LIST_Y
    for start, title in events[page * rows:(page + 1) * rows]:
        ty = y + (TD_ROW_H - F.M.h) // 2
        if start is None:
            label = "ALL DAY"
            D.invert_box(fb, rx, y + 8, F.S.width(label) + 8, TD_ROW_H - 16)
            F.S.draw(fb, label, rx + 4, y + (TD_ROW_H - F.S.h) // 2, WHITE)
        else:
            F.S.draw(fb, start, rx, y + (TD_ROW_H - F.S.h) // 2)
        tx = rx + F.S.width("ALL DAY") + 16
        end_x = D.text_fit(fb, title, tx, ty, rx + rw - tx, F.M)
        if start is not None and start < now_hm:        # 지난 일정: 취소선
            fb.fill_rect(tx, ty + F.M.h // 2 - 1, end_x - tx, 2, BLACK)
        y += TD_ROW_H

    if n_pages > 1:
        D.text_right(fb, "%d/%d" % (page + 1, n_pages), W - MARGIN, H - TD_FOOT_H - F.S.h - 2, F.S)

    # ---- 아래: 내일 요약
    fy = H - TD_FOOT_H
    D.dashed_hline(fb, TD_RIGHT_X + 8, fy, W - MARGIN - TD_RIGHT_X - 8)
    tm = cal.add_days(t[0], t[1], t[2], 1)
    ev = _events_for(t, tm)
    if ev:
        first = "ALL DAY"
        for s, _ in ev:                 # (MicroPython은 next(it, 기본값)을 지원 안 할 수 있음)
            if s:
                first = s
                break
        msg = "TOMORROW: %d, first %s" % (len(ev), first)
    else:
        msg = "TOMORROW: nothing"
    F.S.draw(fb, msg, rx, fy + (TD_FOOT_H - F.S.h) // 2)


SCREENS = (month, week, today)
