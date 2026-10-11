# 오늘 화면 (할 일 = 오늘의 캘린더 일정)
#
#  ┌─────────────┬───────────────────────────────────────┐
#  │             │ 종일   렙티튜드 납품                  │  행 40px: 시간 S + 제목 M
#  │     10      │ 09:00  M̶p̶l̶a̶b̶ ̶주̶간̶ ̶미̶팅̶               │  끝난 일정은 취소선
#  │   토요일    │ 20:30  전자잉크 달력 Phase 4    지금  │  진행 중 표시
#  │   2026.10   │ ...                             1/2   │  KEY1 = 다음 페이지
#  │ 남은 일정 3/8├ - - - - - - - - - - - - - - - - - - - ┤
#  │             │ 내일: 일정 3개 · 첫 일정 ~01:00       │
#  └─────────────┴───────────────────────────────────────┘
import cal
import model
from gfx.layout import (BLACK, WHITE, W, H, MARGIN, HEADER_H, TD_LEFT_W,
                        TD_RIGHT_X, TD_ROW_H, TD_LIST_Y, TD_FOOT_H, TD_ROWS)
from gfx import font as F
from gfx import draw as D
from screens.common import N_SCREENS

ALL_DAY = "종일"
NOW = "지금"


def render(fb, ctx):
    t = ctx.today
    wd = ctx.now[6]
    o = ctx.today_ord
    idx = model.by_day(ctx.events, o, o + 2)
    events = idx.get(o, [])
    tomorrow = idx.get(o + 1, [])
    now = ctx.now_min

    fb.fill(WHITE)
    D.header(fb, "%d년 %d월 %d일 %s" % (t[0], t[1], t[2], cal.WD_KO_LONG[wd]),
             ctx.clock(), 2, N_SCREENS)

    # ---- 왼쪽: 큰 날짜 + 남은 일정 수
    lx, lw = MARGIN, TD_LEFT_W
    y = HEADER_H + 40
    D.text_center(fb, "%d" % t[2], lx, y, lw, F.XL)
    y += F.XL.h + 22
    D.text_center(fb, cal.WD_KO_LONG[wd], lx, y, lw, F.M)
    y += F.M.h + 10
    D.text_center(fb, "%d.%02d" % (t[0], t[1]), lx, y, lw, F.S)
    left = 0
    for e in events:
        if e.end > now:
            left += 1
    msg = "남은 일정 %d / %d" % (left, len(events)) if events else "일정 없음"
    D.text_center(fb, msg, lx, H - TD_FOOT_H + (TD_FOOT_H - F.S.h) // 2, lw, F.S)
    fb.vline(TD_RIGHT_X, HEADER_H, H - HEADER_H, BLACK)

    # ---- 오른쪽: 목록
    rows = TD_ROWS
    n_pages = max(1, (len(events) + rows - 1) // rows)
    page = ctx.offset % n_pages
    rx = TD_RIGHT_X + 12
    right = W - MARGIN
    tx = rx + max(F.S.width("~00:00"), F.S.width(ALL_DAY) + 8) + 16
    y = TD_LIST_Y
    if not events:
        F.M.draw(fb, "오늘 일정 없음", rx, y + (TD_ROW_H - F.M.h) // 2)
    for e in events[page * rows:(page + 1) * rows]:
        _row(fb, e, rx, tx, right, y, o, now)
        y += TD_ROW_H
    if n_pages > 1:
        D.text_right(fb, "%d/%d" % (page + 1, n_pages), right,
                     H - TD_FOOT_H - F.S.h - 4, F.S)

    # ---- 아래: 내일
    fy = H - TD_FOOT_H
    D.dashed_hline(fb, TD_RIGHT_X + 8, fy, right - TD_RIGHT_X - 8)
    if tomorrow:
        first = ALL_DAY
        for e in tomorrow:
            if not e.all_day:
                first = e.start_hm() if e.start >= (o + 1) * model.DAY else "~" + e.end_hm()
                break
        msg = "내일: 일정 %d개 · 첫 일정 %s" % (len(tomorrow), first)
    else:
        msg = "내일: 일정 없음"
    D.text_fit(fb, msg, rx, fy + (TD_FOOT_H - F.S.h) // 2, right - rx, F.S)


def _row(fb, e, rx, tx, right, y, day_ord, now):
    mid = y + TD_ROW_H // 2
    if e.all_day:
        bw = F.S.width(ALL_DAY) + 12
        D.invert_box(fb, rx - 4, y + 9, bw, TD_ROW_H - 18)
        F.S.draw(fb, ALL_DAY, rx + 2, mid - F.S.h // 2, WHITE)
    elif e.start < day_ord * model.DAY:
        F.S.draw(fb, "~" + e.end_hm(), rx, mid - F.S.h // 2)
    else:
        F.S.draw(fb, e.start_hm(), rx, mid - F.S.h // 2)

    ongoing = (not e.all_day) and e.start <= now < e.end
    tag_w = F.S.width(NOW) + 16 if ongoing else 0
    ty = mid - F.M.h // 2
    end_x = D.text_fit(fb, e.title, tx, ty, right - tx - tag_w - 4, F.M)
    if ongoing:
        D.invert_box(fb, right - tag_w, y + 9, tag_w, TD_ROW_H - 18)
        F.S.draw(fb, NOW, right - tag_w + 8, mid - F.S.h // 2, WHITE)
    elif not e.all_day and e.end <= now:              # 끝난 일정: 취소선
        fb.fill_rect(tx, mid - 1, end_x - tx, 2, BLACK)
