# 시각 맞추기: NTP 로 RTC 를 UTC 로 맞추고, 화면에는 +9시간(한국) 해서 보여 준다.
# NTP 가 실패하면 Apps Script 응답의 "now" (UTC 초) 로 대신 맞춘다.
import utime
import machine

synced = False          # 이번 부팅에서 시각을 맞춘 적이 있는지 (hw/clock.py 가 확인)

# MicroPython 기기의 epoch 가 2000년인 경우를 대비
_EPOCH_DIFF = 0 if utime.gmtime(0)[0] == 1970 else 946684800


def ntp(host="kr.pool.ntp.org"):
    global synced
    import ntptime
    ntptime.host = host
    ntptime.settime()            # RTC = UTC
    synced = True


def set_from_unix(unix_sec):
    """UTC 유닉스 초로 RTC 맞추기."""
    global synced
    t = utime.gmtime(unix_sec - _EPOCH_DIFF)
    # RTC.datetime: (년, 월, 일, 요일, 시, 분, 초, 서브초)
    machine.RTC().datetime((t[0], t[1], t[2], t[6], t[3], t[4], t[5], 0))
    synced = True
