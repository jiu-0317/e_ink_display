# 오늘 화면 — 시간표(타임라인) 방식
#  ctx.offset = 며칠 뒤를 볼지 (KEY1 짧게 = 다음 날, KEY0 길게 = 오늘로)
#
#  ┌───────────┬────────────────────────────────────────────┐
#  │           │ 종일 ▓렙티튜드 납품▓ ▓한글날▓   ↑ 7시 전 1개│  종일 줄 (20px)
#  │    12     ├────────────────────────────────────────────┤
#  │  월요일   │  7시 · · · · · · · · · · · · · · · · · · · │  정시마다 점선, 1시간 = 23px
#  │  2026.10  │  8시 · · · · · · · · · · · · · · · · · · · │
#  │           │  9시 ▓디지털회로설계 수업▓▓▓▓▓ 09:30~09:50▓ │  모든 일정: 검정 + 흰 글씨
#  │ 남은 일정 │ 10시 · · · · · · · · · · · · · · · · · · · │  겹치면 나란히 (열 나눔)
#  │   2 / 6   │ ...                                         │
#  │- - - - - -│18:50 ●━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━│  지금 선 (10분 단위, 색 반전)
#  │ 내일      │ ...                                         │
#  └───────────┴────────────────────────────────────────────┘
import cal
import config
import model
from gfx.layout import (BLACK, WHITE, W, H, MARGIN, HEADER_H, TD_LEFT_W, TD_RIGHT_X)
from gfx import font as F
from gfx import draw as D
from screens.common import N_SCREENS

DAY = model.DAY
START_H = config.TL_START_H
END_H = config.TL_END_H

LABEL_W = 46                        # 왼쪽 "13시" 칸
GRID_X = TD_RIGHT_X + LABEL_W       # 시간표 시작 x
RIGHT = W - MARGIN                  # 시간표 끝 x
AD_Y = HEADER_H + 4                 # 종일 줄
AD_H = 20
SEP_Y = AD_Y + AD_H + 4             # 종일 줄 아래 구분선
Y0 = SEP_Y + 8                      # START_H 시각의 y
HOUR_PX = (H - 5 - Y0) // (END_H - START_H)
Y1 = Y0 + HOUR_PX * (END_H - START_H)
MIN_H = F.XS.h + 4                  # 블록 최소 높이 (짧은 일정도 글자가 보이게)
MIN_MINUTES = (MIN_H * 60 + HOUR_PX - 1) // HOUR_PX


def y_of(m):
    """하루 시작부터의 분 → y."""
    return Y0 + (m - START_H * 60) * HOUR_PX // 60


def render(fb, ctx):
    o = ctx.today_ord + ctx.offset              # 보여 줄 날
    t = cal.from_ord(o)
    wd = cal.weekday(*t)
    is_today = ctx.offset == 0
    day0 = o * DAY
    idx = model.by_day(ctx.events, o, o + 2)
    events = idx.get(o, [])
    tomorrow = idx.get(o + 1, [])

    fb.fill(WHITE)
    title = "%d년 %d월 %d일 %s" % (t[0], t[1], t[2], cal.WD_KO_LONG[wd])
    if ctx.offset == 1:
        title += " · 내일"
    elif ctx.offset > 1:
        title += " · %d일 뒤" % ctx.offset
    D.header(fb, title, ctx.clock(), 2, N_SCREENS)
    _left(fb, ctx, t, wd, is_today, events, tomorrow)
    fb.vline(TD_RIGHT_X, HEADER_H, H - HEADER_H, BLACK)

    all_day = [e for e in events if e.all_day]
    timed = [e for e in events if not e.all_day]
    lo = day0 + START_H * 60
    hi = day0 + END_H * 60
    early = [e for e in timed if e.end <= lo]            # 시간표 시작 전에 끝난 일정

    _all_day_row(fb, all_day, len(early))
    _grid(fb)

    items = []
    for e in timed:
        s = max(e.start, lo)
        en = min(e.end, hi)
        if en <= s:
            continue
        s -= day0
        en -= day0
        items.append((s, max(en, s + MIN_MINUTES), e))
    for s, e_vis, ev, col, n in model.layout_columns(items):
        _block(fb, ev, s, e_vis, col, n, day0)

    if ctx.valid and is_today:
        _now_line(fb, ctx.now_min10 - day0)


# ---------------------------------------------------------------- 왼쪽 패널
def _left(fb, ctx, t, wd, is_today, events, tomorrow):
    lx, lw = MARGIN, TD_LEFT_W
    y = HEADER_H + 28
    D.text_center(fb, "%d" % t[2], lx, y, lw, F.XL)
    y += F.XL.h + 18
    D.text_center(fb, cal.WD_KO_LONG[wd], lx, y, lw, F.M)
    y += F.M.h + 8
    D.text_center(fb, "%d.%02d" % (t[0], t[1]), lx, y, lw, F.S)

    y = 316
    if not events:
        msg = "오늘 일정 없음" if is_today else "일정 없음"
    elif is_today:
        left = 0
        for e in events:
            if e.end > ctx.now_min:
                left += 1
        msg = "남은 일정 %d / %d" % (left, len(events))
    else:
        msg = "일정 %d개" % len(events)
    D.text_center(fb, msg, lx, y, lw, F.S)

    y = 356
    D.dashed_hline(fb, lx + 20, y, lw - 40)
    y += 14
    D.text_center(fb, "내일" if is_today else "다음 날", lx, y, lw, F.S)
    y += F.S.h + 6
    if tomorrow:
        first = "종일"
        for e in tomorrow:
            if not e.all_day:
                first = e.start_hm() if e.start >= (cal.to_ord(*t) + 1) * DAY else "~" + e.end_hm()
                break
        D.text_center(fb, "일정 %d개 · 첫 %s" % (len(tomorrow), first), lx, y, lw, F.S)
    else:
        D.text_center(fb, "일정 없음", lx, y, lw, F.S)


# ---------------------------------------------------------------- 종일 줄
def _all_day_row(fb, all_day, n_early):
    x = GRID_X + 2
    right = RIGHT
    if n_early:
        note = "↑ %d시 전 %d개" % (START_H, n_early)
        right -= F.XS.width(note) + 8
        F.XS.draw(fb, note, RIGHT - F.XS.width(note), AD_Y + (AD_H - F.XS.h) // 2)
    if all_day:
        D.text_right(fb, "종일", GRID_X - 6, AD_Y + (AD_H - F.S.h) // 2, F.S)
        n = len(all_day)
        show = all_day if n <= 3 else all_day[:2]
        more = n - len(show)
        if more:
            label = "+%d" % more
            right -= F.XS.width(label) + 8
            F.XS.draw(fb, label, right + 4, AD_Y + (AD_H - F.XS.h) // 2)
        gap = 4
        bw = (right - x - gap * (len(show) - 1)) // len(show)
        bw = min(bw, 220)
        for e in show:
            fb.fill_rect(x, AD_Y, bw, AD_H, BLACK)
            D.text_fit(fb, e.title, x + 5, AD_Y + (AD_H - F.XS.h) // 2, bw - 10, F.XS, WHITE)
            x += bw + gap
    fb.hline(TD_RIGHT_X + 1, SEP_Y, RIGHT - TD_RIGHT_X - 1, BLACK)


# ---------------------------------------------------------------- 시간 눈금
def _grid(fb):
    for h in range(START_H, END_H + 1):
        y = y_of(h * 60)
        D.dashed_hline(fb, GRID_X, y, RIGHT - GRID_X, 1, 3)
        if h < END_H:
            D.text_right(fb, "%d시" % h, GRID_X - 6, y - F.S.h // 2, F.S)


# ---------------------------------------------------------------- 일정 블록
def _range(ev, day0):
    a = ev.start_hm() if ev.start >= day0 else ""
    b = ev.end_hm() if ev.end <= day0 + DAY else ""
    return a + "~" + b


def _block(fb, ev, s, e_vis, col, n, day0):
    gx = GRID_X + 2
    gw = RIGHT - gx
    x = gx + col * gw // n
    x2 = gx + (col + 1) * gw // n
    y = y_of(s)
    y2 = min(y_of(e_vis), Y1)
    if y2 - y < MIN_H:
        y = y2 - MIN_H
    # 1px 흰 틈을 두고 검정으로 채움 → 붙어 있는 일정끼리도 구분됨
    fb.fill_rect(x + 1, y + 1, x2 - x - 2, y2 - y - 1, BLACK)
    h = y2 - y - 1
    ix = x + 6
    iw = x2 - x - 12
    title = ev.title
    rng = _range(ev, day0)
    font = F.S if h >= F.S.h + 4 else F.XS

    if h >= font.h + F.XS.h + 8:                         # 두 줄 이상: 제목(여러 줄) + 시간
        lines_room = (h - F.XS.h - 8) // (font.h + 2)
        ty = y + 4
        for line in D.wrap(title, font, iw, max(1, lines_room)):
            font.draw(fb, line, ix, ty, WHITE)
            ty += font.h + 2
        F.XS.draw(fb, D.fit(rng, F.XS, iw), ix, ty + 1, WHITE)
        return

    ty = y + 1 + (h - font.h) // 2                       # 한 줄: 제목 + (자리 있으면) 오른쪽에 시간
    rw = F.XS.width(rng)
    if font.width(title) + 16 + rw <= iw:
        font.draw(fb, title, ix, ty, WHITE)
        F.XS.draw(fb, rng, ix + iw - rw, y + 1 + (h - F.XS.h) // 2, WHITE)
    else:
        D.text_fit(fb, title, ix, ty, iw, font, WHITE)


# ---------------------------------------------------------------- 지금 선
def _now_line(fb, m):
    if not (START_H * 60 <= m <= END_H * 60):
        return
    y = y_of(m)
    D.invert_rect(fb, GRID_X + 1, y - 1, RIGHT - GRID_X - 1, 3)     # 흰 곳은 검게, 블록 위는 희게
    for dy, half in ((-3, 1), (-2, 2), (-1, 3), (0, 3), (1, 3), (2, 2), (3, 1)):
        fb.hline(GRID_X - half, y + dy, 2 * half + 1, BLACK)       # 작은 원
    tag = "%02d:%02d" % (m // 60, m % 60)
    tw = F.XS.width(tag) + 6
    fb.fill_rect(TD_RIGHT_X + 1, y - 9, LABEL_W - 4, 19, WHITE)    # 겹치는 "N시" 글자 가리기
    fb.fill_rect(GRID_X - 6 - tw, y - 8, tw, 17, BLACK)
    F.XS.draw(fb, tag, GRID_X - 3 - tw, y - F.XS.h // 2, WHITE)
