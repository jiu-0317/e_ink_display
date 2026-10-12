# 갱신 정책 — 화면을 실제로 띄우는 곳은 여기 한 군데뿐
#
#   - 버튼으로 화면을 바꿀 때: fast (약 1.6초)
#   - fast 를 FULL_EVERY 번 하면, 또는 request_full() 이 불리면 다음 갱신은 full (약 4초, 잔상 제거)
#   - 오늘 화면의 10분 갱신: partial (약 0.4초, 깜빡임 없음)
#     partial 을 partial_limit 번 하면 그다음은 full (잔상 제거, 약 1시간에 한 번)
#   - 처음 한 번은 항상 full
#   - 어떤 경우에도 갱신이 끝나면 sleep (고전압 상태로 두지 않기)
import utime


class Refresher:
    def __init__(self, epd, full_every=10, partial_limit=6):
        self.epd = epd
        self.full_every = full_every
        self.partial_limit = partial_limit
        self.fast_count = 0
        self.partial_count = 0
        self._force_full = True
        self.total = 0

    def request_full(self):
        self._force_full = True

    def next_mode(self, partial=False):
        if self._force_full or self.fast_count >= self.full_every:
            return "full"
        if partial:
            return "full" if self.partial_count >= self.partial_limit else "partial"
        return "fast"

    def show(self, partial=False):
        """epd.buffer_1Gray 를 화면에 띄움. partial=True 면 가능할 때 부분 갱신.
        (사용한 모드, 걸린 ms) 반환."""
        mode = self.next_mode(partial)
        epd = self.epd
        t0 = utime.ticks_ms()
        try:
            if mode == "partial":
                epd.init_part()
                epd.display_partial_full(epd.buffer_1Gray)
            else:
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
            self.partial_count = 0
            self._force_full = False
        elif mode == "partial":
            self.partial_count += 1
        else:
            self.fast_count += 1
        self.total += 1
        return mode, ms
