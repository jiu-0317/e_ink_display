# 전송 속도 비교 — 원래 방식(1바이트씩) vs 빠른 전송(반전 후 한 번에)
#
# 준비: epd7in5.py, draw_util.py 를 Pico에 업로드 (MicroPico: "Upload project to Pico")
#
#   BENCH   화면 갱신 없이 전송 시간만 비교 (원래 / 빠른 4MHz / 빠른 10MHz)
#   STEP A  fast 갱신, 빠른 전송 @4MHz   — 화면이 정상인지 확인
#   STEP B  fast 갱신, 빠른 전송 @10MHz  — A와 똑같이 보이는지 (노이즈·밀림 없는지)
#   STEP C  full 갱신 + 부분 갱신 5회 (빠른 부분 전송)
#   STEP D  full 갱신으로 결과 요약 후 종료
#
# 단계 사이에서 KEY0을 누르면 다음 단계로 넘어갑니다.

import gc
import framebuf
import utime

import epd7in5
from draw_util import (BLACK, WHITE, W, H, log, results, Timer, wait_next,
                       big_text, draw_frame, draw_results)

FAST_BAUD = 10_000_000      # 컨트롤러(UC8179) 쓰기 SPI 클럭 상한 근처. 더 올리지 않음


def mem_kb():
    gc.collect()
    return gc.mem_free() // 1024


def screen(fb, title, subtitle):
    fb.fill(WHITE)
    draw_frame(fb)
    big_text(fb, title, 64, 44, 3)
    big_text(fb, subtitle, 64, 80, 2)
    # 작은 글씨·가는 선이 깨지는지 보기 위한 패턴
    for i in range(0, 200, 4):
        fb.vline(560 + i, 380, 60, BLACK)       # 1px 선 / 3px 간격
    fb.text("1px lines", 560, 368, BLACK)
    fb.fill_rect(64, 380, 160, 60, BLACK)
    big_text(fb, "INVERT", 96, 400, 2, WHITE)


print("=" * 50)
print("전송 속도 비교 시작")
log("RAM free (start)", "%d KB" % mem_kb())
epd = epd7in5.EPD_7in5()                     # gray4=False, 4MHz
log("RAM free (EPD)", "%d KB" % mem_kb())
print("SPI:", epd.spi)

fb = epd.image1Gray
buf = epd.buffer_1Gray

# ---------------------------------------------------------------- BENCH
print("\n--- BENCH: 전송만 (화면 갱신 없음)")
screen(fb, "BENCH", "")

t = Timer()
epd.send_frame_slow(buf)
log("xfer original 4MHz", "%d ms" % t.ms())

t = Timer()
epd7in5._invert(buf, epd.buffer_inv, len(buf))
log("invert only (viper)", "%d ms" % t.ms())

t = Timer()
epd.send_frame(buf)
log("xfer fast 4MHz", "%d ms" % t.ms())

print("SPI ->", epd.set_baudrate(FAST_BAUD))
t = Timer()
epd.send_frame(buf)
log("xfer fast 10MHz", "%d ms" % t.ms())
epd.set_baudrate(4_000_000)

# ---------------------------------------------------------------- STEP A
print("\n--- STEP A: fast 갱신 @4MHz")
epd.init_fast()
screen(fb, "STEP A  FAST XFER @4MHz", "Compare with STEP B: must look identical")
draw_results(fb, 64, 120, 2)
t = Timer()
epd.display_fast(buf)
log("A fast total @4MHz", "%d ms" % t.ms())
epd.sleep()
wait_next("STEP A")

# ---------------------------------------------------------------- STEP B
print("\n--- STEP B: fast 갱신 @10MHz")
print("SPI ->", epd.set_baudrate(FAST_BAUD))
epd.init_fast()
screen(fb, "STEP B  FAST XFER @10MHz", "Compare with STEP A: must look identical")
draw_results(fb, 64, 120, 2)
t = Timer()
epd.display_fast(buf)
log("B fast total @10MHz", "%d ms" % t.ms())
epd.sleep()
wait_next("STEP B (A와 비교해서 노이즈·밀림이 없는지)")

# ---------------------------------------------------------------- STEP C
print("\n--- STEP C: full 갱신 + 빠른 부분 갱신 @10MHz")
t = Timer()
epd.init()
fb.fill(WHITE)
draw_frame(fb)
big_text(fb, "STEP C  FULL + PARTIAL", 64, 44, 3)
big_text(fb, "the box below updates 5 times", 64, 80, 2)
PX, PY, PW, PH = 304, 200, 192, 80          # x, 폭은 8의 배수
fb.rect(PX - 4, PY - 4, PW + 8, PH + 8, BLACK)
epd.display_fast(buf)
log("C full total @10MHz", "%d ms" % t.ms())     # init 포함

pbuf = bytearray(PW * PH // 8)
pfb = framebuf.FrameBuffer(pbuf, PW, PH, framebuf.MONO_HLSB)
epd.init_part()
ptimes = []
for i in range(1, 6):
    pfb.fill(WHITE)
    big_text(pfb, "PART %d" % i, 24, 28, 3, max_w=PW)
    t = Timer()
    epd.display_Partial_fast(pbuf, PX, PY, PX + PW, PY + PH)
    ptimes.append(t.ms())
    print("    partial %d: %d ms" % (i, ptimes[-1]))
    utime.sleep_ms(1000)
log("C partial avg (fast)", "%d ms" % (sum(ptimes) // len(ptimes)))
epd.sleep()
wait_next("STEP C")

# ---------------------------------------------------------------- STEP D
print("\n--- STEP D: full 갱신으로 결과 요약")
epd.init()
log("RAM free (end)", "%d KB" % mem_kb())
fb.fill(WHITE)
draw_frame(fb)
big_text(fb, "TRANSFER RESULTS", 120, 40, 3)
draw_results(fb, 64, 80, 2)
epd.display_fast(buf)
epd.sleep()

print("\n" + "=" * 50)
print("요약 (복사해서 알려 주세요)")
for name, value in results:
    print("  %-22s %s" % (name, value))
print("=" * 50)
