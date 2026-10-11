# Phase 1 측정 스크립트 — Pico 2 W + Pico-ePaper-7.5 (V2)
# (원래 드라이버 전송 방식 그대로 측정하는 기준 버전)
#
# 준비: epd7in5.py, draw_util.py 를 Pico에 업로드 (MicroPico: "Upload project to Pico")
#       그다음 이 파일을 열고 "Run current file" 로 실행.
#
#   STEP 1  full 갱신  — 테두리/눈금/모서리 좌표 확인
#   STEP 2  fast 갱신  — STEP 1 측정값 + 디더 패턴
#   STEP 3  부분 갱신  — 가운데 박스만 5회 부분 갱신
#   STEP 4  sleep 후 init → full 갱신으로 결과 요약
#   STEP 5  버튼 테스트 (콘솔만) — KEY1 길게 누르면 종료

import gc
import os
import framebuf
import machine
import utime

from draw_util import (BLACK, WHITE, W, H, LONG_MS, log, results, Timer,
                       wait_key, wait_next, big_text, dither, draw_frame,
                       draw_results)


def mem():
    gc.collect()
    return gc.mem_free()


def timed_display(epd, buf):
    """display()의 전체 시간과 그중 패널 갱신(TurnOnDisplay) 시간을 분리 측정."""
    holder = {}
    orig = epd.TurnOnDisplay

    def wrapped():
        t = Timer()
        orig()
        holder["refresh"] = t.ms()

    epd.TurnOnDisplay = wrapped
    t = Timer()
    epd.display(buf)
    total = t.ms()
    epd.TurnOnDisplay = orig
    refresh = holder.get("refresh", 0)
    return total, total - refresh, refresh


# ================================================================ 시작
print("=" * 50)
print("Phase 1 측정 시작")
print("CPU 클럭: %d MHz" % (machine.freq() // 1_000_000))
try:
    st = os.statvfs("/")
    log("flash free", "%d KB" % (st[0] * st[3] // 1024))
except Exception as e:
    print("statvfs 실패:", e)

m0 = mem()
log("RAM free (start)", "%d KB" % (m0 // 1024))

import epd7in5                     # noqa: E402
t = Timer()
epd = epd7in5.EPD_7in5()           # 생성자 안에서 버퍼 할당 + init()
log("EPD create+init", "%d ms" % t.ms())
m1 = mem()
log("RAM free (EPD)", "%d KB" % (m1 // 1024))
log("RAM used by EPD", "%d KB" % ((m0 - m1) // 1024))

fb = epd.image1Gray
buf = epd.buffer_1Gray

# ---------------------------------------------------------------- STEP 1
print("\n--- STEP 1: full 갱신")
fb.fill(WHITE)
draw_frame(fb)
big_text(fb, "STEP 1  FULL REFRESH", 120, 70, 3)
big_text(fb, "Check: border, ticks, corner dots all visible?", 40, 120, 2)
big_text(fb, "KEY0 = next", 40, 150, 2)
total, xfer, refresh = timed_display(epd, buf)
log("full total", "%d ms" % total)
log("full transfer", "%d ms" % xfer)
log("full panel", "%d ms" % refresh)
t = Timer()
epd.sleep()
log("sleep cmd", "%d ms" % t.ms())
wait_next("STEP 1")

# ---------------------------------------------------------------- STEP 2
print("\n--- STEP 2: fast 갱신")
t = Timer()
epd.init_fast()
log("init_fast (from sleep)", "%d ms" % t.ms())
fb.fill(WHITE)
draw_frame(fb)
big_text(fb, "STEP 2  FAST REFRESH", 120, 50, 3)
draw_results(fb, 120, 90, 2)
big_text(fb, "dither 50%", 120, 380, 1)
dither(fb, 120, 392, 120, 60, 2)
big_text(fb, "dither 1/16", 260, 380, 1)
dither(fb, 260, 392, 120, 60, 4)
big_text(fb, "inverted box", 400, 380, 1)
fb.fill_rect(400, 392, 120, 60, BLACK)
big_text(fb, "10", 436, 408, 3, WHITE)
total, xfer, refresh = timed_display(epd, buf)
log("fast total", "%d ms" % total)
log("fast panel", "%d ms" % refresh)
epd.sleep()
wait_next("STEP 2")

# ---------------------------------------------------------------- STEP 3
print("\n--- STEP 3: 부분 갱신 (바탕은 full 갱신)")
epd.init()
fb.fill(WHITE)
draw_frame(fb)
big_text(fb, "STEP 3  PARTIAL REFRESH", 120, 70, 3)
big_text(fb, "the box below updates 5 times", 120, 120, 2)
PX, PY, PW, PH = 304, 200, 192, 80          # x, 폭은 8의 배수
fb.rect(PX - 4, PY - 4, PW + 8, PH + 8, BLACK)
timed_display(epd, buf)

pbuf = bytearray(PW * PH // 8)
pfb = framebuf.FrameBuffer(pbuf, PW, PH, framebuf.MONO_HLSB)

t = Timer()
epd.init_part()
log("init_part", "%d ms" % t.ms())
ptimes = []
for i in range(1, 6):
    pfb.fill(WHITE)
    big_text(pfb, "PART %d" % i, 24, 28, 3, max_w=PW)   # 6글자 x 24px = 144px
    t = Timer()
    epd.display_Partial(pbuf, PX, PY, PX + PW, PY + PH)
    ptimes.append(t.ms())
    print("    partial %d: %d ms" % (i, ptimes[-1]))
    utime.sleep_ms(1000)
log("partial avg", "%d ms" % (sum(ptimes) // len(ptimes)))
log("partial min/max", "%d / %d ms" % (min(ptimes), max(ptimes)))
epd.sleep()
wait_next("STEP 3 (잔상이 남았는지도 봐 주세요)")

# ---------------------------------------------------------------- STEP 4
print("\n--- STEP 4: sleep → init → full 요약")
t = Timer()
epd.init()
log("init (from sleep)", "%d ms" % t.ms())
log("RAM free (end)", "%d KB" % (mem() // 1024))
fb.fill(WHITE)
draw_frame(fb)
big_text(fb, "PHASE 1 RESULTS", 120, 40, 3)
draw_results(fb, 64, 80, 2)
timed_display(epd, buf)
epd.sleep()
print("\n화면은 요약을 표시한 채 sleep 상태입니다 (e-Paper는 전원이 없어도 유지).")

# ---------------------------------------------------------------- STEP 5
print("\n--- STEP 5: 버튼 테스트 (화면 갱신 없음)")
print("짧게/길게(%d ms 이상) 눌러 보세요. KEY1을 길게 누르면 종료." % LONG_MS)
while True:
    name, dur = wait_key()
    kind = "LONG" if dur >= LONG_MS else "short"
    print("    %s %s (%d ms)" % (name, kind, dur))
    if name == "KEY1" and kind == "LONG":
        break

print("\n" + "=" * 50)
print("요약 (복사해서 알려 주세요)")
for name, value in results:
    print("  %-22s %s" % (name, value))
print("=" * 50)
