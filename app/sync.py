# 구글 캘린더 동기화: Wi-Fi 켜기 → (시각 맞추기) → Apps Script 에서 일정 받기 → Wi-Fi 끄기
#
# 받은 일정은 data/events.json 에 저장해 두고, 다음 부팅이나 동기화 실패 때 그대로 쓴다.
# 내용이 이전과 같으면 changed=False → 화면을 다시 그리지 않아도 됨.
import gc
import json
import os
import utime

import config
from net import timesync


def _read(path):
    try:
        with open(path) as f:
            return f.read()
    except OSError:
        return None


def run(cred):
    """(changed, 일정 수) 반환. 실패하면 예외."""
    from net import wifi, http          # network 모듈은 여기서만 (PC 미리보기에는 없음)
    gc.collect()
    tmp = config.CACHE_PATH + ".tmp"
    t0 = utime.ticks_ms()
    wlan = wifi.connect(cred.WIFI_SSID, cred.WIFI_PASSWORD)
    try:
        print("  Wi-Fi 연결: %d ms, IP %s" % (utime.ticks_diff(utime.ticks_ms(), t0),
                                            wlan.ifconfig()[0]))
        if not timesync.synced:
            try:
                timesync.ntp()
                print("  NTP 시각 맞춤")
            except Exception as e:
                print("  NTP 실패 (응답의 시각으로 대신):", e)
        t1 = utime.ticks_ms()
        n = http.get_to_file(cred.CALENDAR_URL, tmp)
        print("  일정 받음: %d bytes, %d ms" % (n, utime.ticks_diff(utime.ticks_ms(), t1)))
    finally:
        wifi.off(wlan)

    # ---- 검사
    with open(tmp) as f:
        data = json.load(f)
    os.remove(tmp)
    if isinstance(data, dict):
        if data.get("error"):
            raise OSError("Apps Script 오류: %s" % data["error"])
        if not timesync.synced and data.get("now"):
            timesync.set_from_unix(int(data["now"]))
            print("  응답의 시각으로 맞춤")
        events = data.get("events")
    else:
        events = data
    if not isinstance(events, list):
        raise ValueError("응답에 일정 목록이 없음")

    # ---- 저장 (일정 내용이 바뀌었을 때만)
    text = json.dumps(events)
    count = len(events)
    del data, events
    gc.collect()
    changed = text != _read(config.CACHE_PATH)
    if changed:
        with open(config.CACHE_PATH, "w") as f:
            f.write(text)
    return changed, count
