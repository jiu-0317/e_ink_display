# 갱신 정책 — 화면을 실제로 띄우는 곳은 여기 한 군데뿐
#
#   - 버튼으로 화면을 바꿀 때: fast (약 1.6초)
#   - fast 를 FULL_EVERY 번 하면, 또는 request_full() 이 불리면 다음 갱신은 full (약 4초, 잔상 제거)
#   - 처음 한 번은 항상 full
#   - 어떤 경우에도 갱신이 끝나면 sleep (고전압 상태로 두지 않기)
import utime


class Refresher:
    def __init__(self, epd, full_every=10):
        self.epd = epd
        self.full_every = full_every
        self.fast_count = 0
        self._force_full = True
        self.total = 0

    def request_full(self):
        self._force_full = True

    def next_mode(self):
        if self._force_full or self.fast_count >= self.full_every:
            return "full"
        return "fast"

    def show(self, mode=None):
        """epd.buffer_1Gray 를 화면에 띄움. (사용한 모드, 걸린 ms) 반환."""
        mode = mode or self.next_mode()
        epd = self.epd
        t0 = utime.ticks_ms()
        try:
            if mode == "full":
                epd.init()
            else:
                epd.init_fast()
            epd.display_fast(epd.buffer_1Gray)
        finally:
            epd.sleep()
        ms = utime.ticks_diff(utime.ticks_ms(), t0)
        if mode == "full":
            self.fast_count = 0
            self._force_full = False
        else:
            self.fast_count += 1
        self.total += 1
        return mode, ms
