# 테스트 스크립트들이 같이 쓰는 그리기·버튼·시간 측정 도우미
import framebuf
import utime
from machine import Pin

BLACK = 0          # MONO_HLSB 버퍼에서 비트 0 = 검정
WHITE = 1          # 비트 1 = 흰색
W, H = 800, 480

KEY0_PIN = 2
KEY1_PIN = 3
LONG_MS = 1000
DEBOUNCE_MS = 50


# ---------------------------------------------------------------- 결과 기록
results = []       # (이름, 값 문자열)


def log(name, value):
    results.append((name, value))
    print("[RESULT] %-22s %s" % (name, value))


class Timer:
    def __init__(self):
        self.t = utime.ticks_ms()

    def ms(self):
        return utime.ticks_diff(utime.ticks_ms(), self.t)


# ---------------------------------------------------------------- 버튼
key0 = Pin(KEY0_PIN, Pin.IN, Pin.PULL_UP)
key1 = Pin(KEY1_PIN, Pin.IN, Pin.PULL_UP)


def wait_key():
    """아무 키나 눌렀다 뗄 때까지 대기. ('KEY0'|'KEY1', 누른 시간 ms) 반환."""
    while True:
        for name, pin in (("KEY0", key0), ("KEY1", key1)):
            if pin.value() == 0:
                utime.sleep_ms(DEBOUNCE_MS)
                if pin.value() != 0:
                    continue            # 떨림이었음
                t0 = utime.ticks_ms()
                while pin.value() == 0:
                    utime.sleep_ms(10)
                dur = utime.ticks_diff(utime.ticks_ms(), t0) + DEBOUNCE_MS
                utime.sleep_ms(DEBOUNCE_MS)
                return name, dur
        utime.sleep_ms(10)


def wait_next(step_name):
    print("\n>>> %s 화면을 확인한 뒤 KEY0을 눌러 다음 단계로" % step_name)
    while True:
        name, dur = wait_key()
        print("    %s 눌림 (%d ms)" % (name, dur))
        if name == "KEY0":
            return


# ---------------------------------------------------------------- 그리기
def text_width(s, scale=1):
    return len(s) * 8 * scale


def big_text(fb, s, x, y, scale=2, color=BLACK, max_w=W):
    """framebuf 기본 8x8 글꼴을 scale 배로 확대해서 그림."""
    n = len(s)
    if n == 0:
        return
    if x + n * 8 * scale > max_w:
        print("[WARN] 글자가 잘림: %r (끝 x=%d > %d)" % (s, x + n * 8 * scale, max_w))
    tw = n * 8
    tbuf = bytearray(tw)                      # (tw/8 바이트) x 8줄
    tmp = framebuf.FrameBuffer(tbuf, tw, 8, framebuf.MONO_HLSB)
    tmp.fill(WHITE)
    tmp.text(s, 0, 0, BLACK)
    for j in range(8):
        for i in range(tw):
            if tmp.pixel(i, j) == BLACK:
                fb.fill_rect(x + i * scale, y + j * scale, scale, scale, color)


def dither(fb, x, y, w, h, period=2):
    """period=2 → 체커보드(50% 회색), 4 → 4x4마다 점 하나(1/16)."""
    for j in range(h):
        for i in range(w):
            if period == 2:
                if (i + j) % 2 == 0:
                    fb.pixel(x + i, y + j, BLACK)
            elif i % period == 0 and j % period == 0:
                fb.pixel(x + i, y + j, BLACK)


def draw_frame(fb):
    """테두리, 눈금, 모서리 좌표 — 위치 밀림/잘림 확인용."""
    fb.rect(0, 0, W, H, BLACK)            # 가장 바깥 1px
    fb.rect(3, 3, W - 6, H - 6, BLACK)    # 안쪽 한 줄 더
    for x in range(0, W, 50):             # 위쪽 눈금 (x)
        L = 14 if x % 100 == 0 else 7
        fb.vline(x, 0, L, BLACK)
        if x % 100 == 0 and x > 0:
            fb.text(str(x), x + 2, 16, BLACK)
    for y in range(0, H, 50):             # 왼쪽 눈금 (y)
        L = 14 if y % 100 == 0 else 7
        fb.hline(0, y, L, BLACK)
        if y % 100 == 0 and y > 0:
            fb.text(str(y), 16, y + 2, BLACK)
    fb.text("(0,0)", 8, 30, BLACK)
    fb.text("(799,0)", W - 8 - 7 * 8, 30, BLACK)
    fb.text("(0,479)", 8, H - 16, BLACK)
    fb.text("(799,479)", W - 8 - 9 * 8, H - 16, BLACK)
    for cx, cy in ((0, 0), (W - 3, 0), (0, H - 3), (W - 3, H - 3)):
        fb.fill_rect(cx, cy, 3, 3, BLACK)  # 꼭짓점 3x3 점
    fb.hline(W // 2 - 20, H // 2, 41, BLACK)
    fb.vline(W // 2, H // 2 - 20, 41, BLACK)


def draw_results(fb, x, y, scale=2, items=None):
    line_h = 8 * scale + 4
    for name, value in (results if items is None else items):
        big_text(fb, "%-22s %s" % (name, value), x, y, scale)
        y += line_h
    return y
