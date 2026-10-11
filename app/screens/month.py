# 월간 화면
#
#  헤더 48 │ 요일 행 24 (일요일 시작, 일요일 반전) │ 6주 x 68px 고정
#  칸 (112 x 68):
#    ┌────────────────┐
#    │ 12          +3 │  날짜 S(Neo둥근모), 넘친 일정 수 XS 오른쪽
#    │ 연구실 미팅    │  일정 1  ┐ XS(Galmuri11), 줄 간격 19
#    │▓반도체 학회▓▓▓▓│  일정 2  ┘ 종일 일정은 반전 띠
#    └────────────────┘
#  오늘 칸은 전체 반전, 다른 달 날짜는 옅은 디더 + 작은 숫자
import cal
import model
from gfx.layout import (BLACK, WHITE, H, BODY_X, BODY_W, COL_W, col_x,
                        M_WDAY_Y, M_WDAY_H, M_GRID_Y, M_ROWS, M_ROW_H)
from gfx import font as F
from gfx import draw as D
from screens.common import N_SCREENS

LINES = 2           # 칸 하나에 보여 줄 일정 줄 수
DATE_Y = 3
LINE0_Y = 25        # 첫 일정 줄 (칸 위 기준)
LINE_H = 19         # 일정 줄 간격 (띠 높이 16 + 3)
BAR_H = 16
PAD = 4
WD_NAMES = ("일", "월", "화", "수", "목", "금", "토")


def render(fb, ctx):
    y, m = cal.add_months(ctx.today[0], ctx.today[1], ctx.offset)
    fb.fill(WHITE)
    D.header(fb, "%d년 %d월" % (y, m), ctx.clock(), 0, N_SCREENS)

    for c in range(7):
        x = col_x(c)
        color = BLACK
        if c == 0:
            D.invert_box(fb, x, M_WDAY_Y, COL_W, M_WDAY_H)
            color = WHITE
        D.text_center(fb, WD_NAMES[c], x, M_WDAY_Y + (M_WDAY_H - F.S.h) // 2, COL_W, F.S, color)

    grid = cal.month_grid(y, m)
    o0 = cal.to_ord(*grid[0])
    idx = model.by_day(ctx.events, o0, o0 + 42)
    for i in range(42):
        ymd = grid[i]
        o = o0 + i
        _cell(fb, col_x(i % 7), M_GRID_Y + (i // 7) * M_ROW_H, ymd,
              ymd[1] == m, o == ctx.today_ord, idx.get(o, []))

    fb.hline(BODY_X, M_GRID_Y - 1, BODY_W, BLACK)
    for c in range(8):
        fb.vline(col_x(c), M_GRID_Y, H - M_GRID_Y, BLACK)
    for r in range(1, M_ROWS):
        fb.hline(BODY_X, M_GRID_Y + r * M_ROW_H, BODY_W, BLACK)
    fb.hline(BODY_X, H - 1, BODY_W, BLACK)


def _cell(fb, x, y, ymd, in_month, is_today, events):
    w, h = COL_W, M_ROW_H
    if not in_month:
        D.dither(fb, x + 1, y + 1, w - 1, h - 1, D.LIGHT)
        fb.fill_rect(x + 3, y + 3, F.TINY.width("00") + 4, F.TINY.h + 4, WHITE)
        F.TINY.draw(fb, "%2d" % ymd[2], x + 5, y + 5)
        return

    fg, bg = BLACK, WHITE
    if is_today:
        D.invert_box(fb, x, y, w, h)
        fg, bg = WHITE, BLACK
    F.S.draw(fb, "%d" % ymd[2], x + PAD, y + DATE_Y, fg)

    n = len(events)
    if n > LINES:
        D.text_right(fb, "+%d" % (n - LINES), x + w - PAD, y + DATE_Y + (F.S.h - F.XS.h), F.XS, fg)

    ly = y + LINE0_Y
    tw = w - 2 * PAD - 2
    for e in events[:LINES]:
        if e.all_day:
            fb.fill_rect(x + 2, ly, w - 3, BAR_H, fg)
            D.text_fit(fb, e.title, x + PAD + 1, ly + (BAR_H - F.XS.h) // 2, tw, F.XS, bg)
        else:
            D.text_fit(fb, e.title, x + PAD + 1, ly + (BAR_H - F.XS.h) // 2, tw, F.XS, fg)
        ly += LINE_H
