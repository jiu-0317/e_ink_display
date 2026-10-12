# 위젯: 글자 맞춤/줄바꿈, 디더(회색), 반전 박스, 점선, 공통 헤더
import framebuf
from gfx.layout import BLACK, WHITE, W, MARGIN, HEADER_H
from gfx.font import PAL
from gfx import font as F

def _ell(font):
    return "\u2026" if font.has("\u2026") else ".."


# ---------------------------------------------------------------- 글자
def text(fb, s, x, y, font, color=BLACK):
    return font.draw(fb, s, x, y, color)


def fit(s, font, w):
    """폭 w 에 들어가도록 자르고, 넘치면 끝에 '…'."""
    if font.width(s) <= w:
        return s
    ell = _ell(font)
    room = w - font.width(ell)
    if room <= 0:
        return ""
    n = 0
    acc = 0
    for ch in s:                       # 앞에서부터 폭을 더해 가며 들어가는 만큼
        cw = font.width(ch)
        if acc + cw > room:
            break
        acc += cw
        n += 1
    return s[:n].rstrip() + ell


def text_fit(fb, s, x, y, w, font, color=BLACK):
    return font.draw(fb, fit(s, font, w), x, y, color)


def text_center(fb, s, x, y, w, font, color=BLACK):
    s = fit(s, font, w)
    return font.draw(fb, s, x + (w - font.width(s)) // 2, y, color)


def text_right(fb, s, x_right, y, font, color=BLACK):
    return font.draw(fb, s, x_right - font.width(s), y, color)


def wrap(s, font, w, max_lines=None):
    """폭 w 로 줄바꿈. 한글은 글자 단위로 끊되, 그 줄에 공백이 있으면 공백에서 끊는다.
    max_lines 를 넘으면 마지막 줄 끝을 '…' 로 처리."""
    lines = []
    cur = ""
    cur_w = 0
    for ch in s:
        cw = font.width(ch)
        if cur_w + cw <= w or not cur:
            cur += ch
            cur_w += cw
            continue
        k = cur.rfind(" ")
        if ch != " " and k > 0:
            lines.append(cur[:k])
            cur = cur[k + 1:] + ch
        else:
            lines.append(cur.rstrip())
            cur = "" if ch == " " else ch
        cur_w = font.width(cur)
    if cur:
        lines.append(cur)
    if max_lines is not None and len(lines) > max_lines:
        rest = " ".join(lines[max_lines - 1:])
        lines = lines[:max_lines - 1] + [fit(rest, font, w)]
    return lines


def text_wrap(fb, s, x, y, w, font, max_lines=None, line_gap=2, color=BLACK):
    """여러 줄로 그리고 다음 y 를 돌려줌."""
    for line in wrap(s, font, w, max_lines):
        font.draw(fb, line, x, y, color)
        y += font.h + line_gap
    return y


# ---------------------------------------------------------------- 회색(디더)
LIGHT = 1       # 1/8
MID = 2         # 1/2 체커보드
DARK = 3        # 3/4


def _ink(level, x, y):
    if level == LIGHT:
        return (x % 4 == 0 and y % 4 == 0) or (x % 4 == 2 and y % 4 == 2)
    if level == MID:
        return (x + y) % 2 == 0
    return not (x % 2 == 0 and y % 2 == 0)


def dither(fb, x, y, w, h, level=MID, color=BLACK):
    """(x,y,w,h) 에 디더 무늬. 무늬는 화면 절대좌표 기준이라 붙여 그려도 이음새가 없음."""
    if w <= 0 or h <= 0:
        return
    period = 4 if level == LIGHT else 2
    rows = []
    for k in range(period):              # 절대 y % period 마다 한 줄 무늬
        r = framebuf.FrameBuffer(bytearray((w + 7) // 8), w, 1, framebuf.MONO_HLSB)
        r.fill(0)
        for i in range(w):
            if _ink(level, x + i, k):
                r.pixel(i, 0, 1)
        rows.append(r)
    pal = PAL[color]
    key = 1 - color
    for yy in range(y, y + h):
        fb.blit(rows[yy % period], x, yy, key, pal)


# ---------------------------------------------------------------- 상자/선
def invert_box(fb, x, y, w, h):
    """검은 상자 (그 위에 WHITE 로 글자를 쓰면 반전 표시)."""
    fb.fill_rect(x, y, w, h, BLACK)


def invert_rect(fb, x, y, w, h):
    """영역의 흑백을 뒤집음 — 흰 바탕에서는 검게, 검은 블록 위에서는 희게 보이는 선."""
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            fb.pixel(xx, yy, 1 - fb.pixel(xx, yy))


def dashed_hline(fb, x, y, w, on=4, off=4, color=BLACK):
    i = 0
    while i < w:
        fb.hline(x + i, y, min(on, w - i), color)
        i += on + off


# ---------------------------------------------------------------- 공통 헤더
def header(fb, title, right="", page=0, n_pages=0):
    """y 0~47: 왼쪽 제목(M), 오른쪽 상태 글자(S), 그 왼쪽에 화면 위치 점."""
    fb.fill_rect(0, 0, W, HEADER_H, WHITE)
    F.M.draw(fb, title, MARGIN, (HEADER_H - F.M.h) // 2 - 1)
    x_right = W - MARGIN
    if right:
        x_right -= F.S.width(right)
        F.S.draw(fb, right, x_right, (HEADER_H - F.S.h) // 2)
    if n_pages:
        size, gap = 10, 8
        x = x_right - 24 - n_pages * (size + gap) + gap
        y = (HEADER_H - size) // 2
        for i in range(n_pages):
            if i == page:
                fb.fill_rect(x, y, size, size, BLACK)
            else:
                fb.rect(x, y, size, size, BLACK)
            x += size + gap
    fb.fill_rect(0, HEADER_H - 2, W, 2, BLACK)
