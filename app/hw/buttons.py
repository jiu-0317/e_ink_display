# 버튼 입력: 짧게/길게 누름 판별
#
# 메인 루프에서 poll()을 자주(20ms 정도) 불러서 이벤트를 받는다.
# e-Paper 갱신 중(약 1.6~4초)에는 poll()이 불리지 않으므로, 그동안 눌린 것은
# IRQ가 "눌렸었다"는 표시만 남겨 두고, 갱신이 끝난 뒤 poll()이 짧게 누름으로 처리한다.
import utime
from machine import Pin

SHORT = "short"
LONG = "long"


class Buttons:
    def __init__(self, pins, long_ms=1000, debounce_ms=40):
        """pins: {"KEY0": 2, "KEY1": 3}"""
        self.names = list(pins.keys())
        self.pins = [Pin(pins[n], Pin.IN, Pin.PULL_UP) for n in self.names]
        self.long_ms = long_ms
        self.debounce_ms = debounce_ms
        k = len(self.names)
        self._pending = [None] * k       # IRQ가 기록한 눌림 시각
        self._down = [None] * k          # 눌림 확정 시각
        self._long_sent = [False] * k
        self._last_up = [0] * k
        for i, p in enumerate(self.pins):
            p.irq(trigger=Pin.IRQ_FALLING, handler=self._make_irq(i))

    def _make_irq(self, i):
        def handler(pin):
            if self._down[i] is None and self._pending[i] is None:
                self._pending[i] = utime.ticks_ms()
        return handler

    def poll(self):
        """[(이름, SHORT|LONG), ...] — 길게 누름은 1초가 되는 순간 바로 나옴."""
        events = []
        now = utime.ticks_ms()
        for i, pin in enumerate(self.pins):
            level = pin.value()
            pend = self._pending[i]
            self._pending[i] = None
            if self._down[i] is None:
                if level == 0:
                    self._down[i] = pend if pend is not None else now
                    self._long_sent[i] = False
                elif pend is not None:
                    # 갱신 중에 눌렀다 뗀 경우. 떼는 순간의 떨림(bounce)은 무시
                    if utime.ticks_diff(pend, self._last_up[i]) > self.debounce_ms * 2:
                        events.append((self.names[i], SHORT))
            else:
                held = utime.ticks_diff(now, self._down[i])
                if level == 0:
                    if not self._long_sent[i] and held >= self.long_ms:
                        events.append((self.names[i], LONG))
                        self._long_sent[i] = True
                else:
                    if not self._long_sent[i] and held >= self.debounce_ms:
                        events.append((self.names[i], SHORT))
                    self._down[i] = None
                    self._last_up[i] = now
        return events
