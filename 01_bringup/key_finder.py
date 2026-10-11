# KEY0 / KEY1 가 어떤 GPIO에 연결돼 있는지 찾는 스크립트
# 사용법: Thonny에서 실행한 뒤 KEY0, KEY1을 하나씩 눌러 보세요. Ctrl+C로 종료.
from machine import Pin
import utime

# e-Paper가 쓰는 핀(GP8~GP13)과 Pico 내부용 핀(GP23,24,25,29)은 제외
CANDIDATES = [0, 1, 2, 3, 4, 5, 6, 7, 14, 15, 16, 17, 18, 19, 20, 21, 22, 26, 27, 28]

pins = {n: Pin(n, Pin.IN, Pin.PULL_UP) for n in CANDIDATES}
last = {n: p.value() for n, p in pins.items()}

print("초기 상태:", last)
print("버튼을 눌러 보세요...")
while True:
    for n, p in pins.items():
        v = p.value()
        if v != last[n]:
            print("GP%d -> %d (%s)" % (n, v, "눌림" if v == 0 else "뗌"))
            last[n] = v
    utime.sleep_ms(20)
