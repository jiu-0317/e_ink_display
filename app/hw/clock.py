# 현재 시각 (한국 시간)
#  1) Wi-Fi 로 시각을 맞춘 뒤(net.timesync): RTC 는 UTC → +9시간 해서 사용
#  2) 이번 부팅에선 아직 못 맞췄지만 RTC 가 그럴듯하면: 그것도 UTC 로 보고 +9시간
#     (소프트 리셋 뒤에도 RTC 는 지난번 NTP 로 맞춘 UTC 값을 그대로 갖고 있음)
#  3) 둘 다 아니면 config.FALLBACK_NOW, 화면에 "시간 미설정" 표시
import utime
import config
import cal
from net import timesync


def now():
    """((년, 월, 일, 시, 분, 초, 요일), 시각이 유효한지) — 요일은 월=0..일=6."""
    if config.FAKE_NOW:
        y, mo, d, h, mi, s = config.FAKE_NOW
        return (y, mo, d, h, mi, s, cal.weekday(y, mo, d)), True
    if timesync.synced:
        return tuple(utime.localtime(utime.time() + config.TZ_OFFSET)[:7]), True
    t = utime.localtime()
    if t[0] >= 2025:
        if config.RTC_IS_UTC:
            t = utime.localtime(utime.time() + config.TZ_OFFSET)
        return tuple(t[:7]), True
    y, mo, d, h, mi, s = config.FALLBACK_NOW
    return (y, mo, d, h, mi, s, cal.weekday(y, mo, d)), False
