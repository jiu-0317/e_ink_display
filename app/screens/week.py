# 주간 화면 (월요일 시작, 날짜별 목록 방식)
#
#  열 머리 40px: 요일 S + 날짜 S (오늘 열은 반전)
#  열 본문 (112 x 392):
#    ▓종일 일정▓▓▓      종일: 반전 띠 (XS)
#    09:00              시간 XS
#    Mplab 주간         제목 XS, 최대 2줄
#    미팅
#    - - - - - -
#    ...
#    +3                 넘치면 남은 개수
#  끝난 일정은 시간 글자에 취소선, 전날부터 이어지는 일정은 "~끝시각"
import cal
import model
from gfx.layout import (BLACK, WHITE, H, BODY_X, BODY_W, COL_W, col_x,
                        WK_HEAD_Y, WK_HEAD_H, WK_BODY_Y, WK_BODY_H)
from gfx import font as F
from gfx import draw as D
from screens.common import N_SCREENS

PAD = 5
BAR_H = 16
TITLE_LINES = 2
GAP = 3


def render(fb, ctx):
    t = ctx.today
    base = cal.add_days(t[0], t[1], t[2], 7 * ctx.offset)
    days = cal.week_days(*base)
    o0 = cal.to_ord(*days[0])
    idx = model.by_day(ctx.events, o0, o0 + 7)

    fb.fill(WHITE)
    a, b = days[0], days[6]
    D.header(fb, "%d/%d - %d/%d" % (a[1], a[2], b[1], b[2]), ctx.clock(), 1, N_SCREENS)

    for c in range(7):
        ymd = days[c]
        o = o0 + c
        x = col_x(c)
        color = BLACK
        if o == ctx.today_ord:
            D.invert_box(fb, x, WK_HEAD_Y, COL_W, WK_HEAD_H)
            color = WHITE
        D.text_center(fb, cal.WD_KO[c], x, WK_HEAD_Y + 4, COL_W, F.S, color)
        D.text_center(fb, "%d/%d" % (ymd[1], ymd[2]), x, WK_HEAD_Y + 6 + F.S.h, COL_W, F.S, color)
        _column(fb, x, o, idx.get(o, []), ctx.now_min)

    fb.hline(BODY_X, WK_BODY_Y - 1, BODY_W, BLACK)
    for c in range(8):
        fb.vline(col_x(c), WK_HEAD_Y, H - WK_HEAD_Y, BLACK)
    fb.hline(BODY_X, H - 1, BODY_W, BLACK)


def _block_h(e, w):
    if e.all_day:
        return BAR_H + GAP
    n = len(D.wrap(e.title, F.XS, w, TITLE_LINES))
    return F.XS.h + 2 + n * (F.XS.h + 2) + 2 + GAP + 2


def _time_label(e, day_ord):
    if e.start < day_ord * model.DAY:          # 전날부터 이어지는 일정
        return "~" + e.end_hm()
    return e.start_hm()


def _column(fb, x, day_ord, events, now_min):
    w = COL_W - 2 * PAD
    y = WK_BODY_Y + PAD
    bottom = WK_BODY_Y + WK_BODY_H - PAD
    more_h = F.XS.h + 2
    n = len(events)
    for i, e in enumerate(events):
        need = _block_h(e, w)
        last = (i == n - 1)
        if y + need > bottom - (0 if last else more_h):
            F.XS.draw(fb, "+%d개 더" % (n - i), x + PAD, bottom - F.XS.h)
            return
        if e.all_day:
            fb.fill_rect(x + 2, y, COL_W - 3, BAR_H, BLACK)
            D.text_fit(fb, e.title, x + PAD, y + (BAR_H - F.XS.h) // 2, w, F.XS, WHITE)
            y += BAR_H + GAP
            continue
        label = _time_label(e, day_ord)
        end_x = F.XS.draw(fb, label, x + PAD, y)
        if e.end <= now_min:                        # 끝난 일정: 시간에 취소선
            fb.hline(x + PAD, y + F.XS.h // 2, end_x - x - PAD, BLACK)
        y += F.XS.h + 2
        y = D.text_wrap(fb, e.title, x + PAD, y, w, F.XS, TITLE_LINES)
        y += 2
        D.dashed_hline(fb, x + PAD, y, w, 2, 3)
        y += GAP + 2
