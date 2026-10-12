# 화면들이 같이 쓰는 것
import cal
import model

N_SCREENS = 3


class Ctx:
    """화면 하나를 그리는 데 필요한 모든 것."""

    def __init__(self, now, valid, events, offset=0, status=""):
        self.now = now                    # (y, m, d, h, mi, s, wd)
        self.valid = valid                # RTC 가 맞는지
        self.events = events              # [model.Event] (정렬됨)
        self.offset = offset              # 다음 달/다음 주/다음 페이지 이동량
        self.status = status              # 헤더 오른쪽에 붙일 상태 ("동기화 실패" 등)
        self.today = now[:3]
        self.today_ord = cal.to_ord(*self.today)
        self.now_min = model.minute_of(now)
        self.now_min10 = self.now_min - self.now_min % 10   # 화면에 보이는 시각은 10분 단위

    def clock(self):
        """헤더 오른쪽 글자: 화면을 그린 시각 (+ 상태)."""
        t = "%02d:%02d" % (self.now[3], self.now[4] - self.now[4] % 10) if self.valid else "시간 미설정"
        return (self.status + " · " + t) if self.status else t

