# 현재 시각 (한국 시간)
#  1) Wi-Fi 로 시각을 맞춘 뒤(net.timesync): RTC 는 UTC → +9시간 해서 사용
#  2) 아직 못 맞췄지만 RTC 가 그럴듯하면(PC 도구가 맞춰 준 경우): 그대로 사용
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
        return tuple(t[:7]), True
    y, mo, d, h, mi, s = config.FALLBACK_NOW
    return (y, mo, d, h, mi, s, cal.weekday(y, mo, d)), False
