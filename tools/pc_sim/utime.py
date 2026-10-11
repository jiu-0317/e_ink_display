# PC용 utime 대체 모듈 (미리보기 전용)
# 가상 시계: sleep 은 기다리지 않고 시계만 앞으로 돌림 → 미리보기가 즉시 끝남.
# 그래서 미리보기에서 찍히는 측정 시간(ms)은 의미가 없습니다.
import time as _time

_now_ms = [0]


def ticks_ms():
    return _now_ms[0]


def ticks_us():
    return _now_ms[0] * 1000


def ticks_diff(a, b):
    return a - b


def ticks_add(a, b):
    return a + b


def sleep_ms(n):
    _now_ms[0] += int(n)


def sleep_us(n):
    _now_ms[0] += int(n) // 1000


def sleep(s):
    _now_ms[0] += int(s * 1000)


def time():
    return int(_time.time())


def localtime(secs=None):
    return _time.localtime(secs)[:8]


def gmtime(secs=None):
    return _time.gmtime(secs)[:8]
