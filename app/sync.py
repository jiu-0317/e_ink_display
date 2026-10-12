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


def networks(cred):
    """credentials.py 의 Wi-Fi 목록. WIFI_NETWORKS 가 있으면 그것, 없으면 WIFI_SSID 하나."""
    nets = [(n[0], n[1]) for n in getattr(cred, "WIFI_NETWORKS", ()) if n and n[0]]
    ssid = getattr(cred, "WIFI_SSID", "")
    if ssid and ssid not in [n[0] for n in nets]:
        nets.append((ssid, getattr(cred, "WIFI_PASSWORD", "")))
    return nets


def run(cred):
    """(changed, 일정 수) 반환. 실패하면 예외."""
    from net import wifi, http          # network 모듈은 여기서만 (PC 미리보기에는 없음)
    gc.collect()
    tmp = config.CACHE_PATH + ".tmp"
    t0 = utime.ticks_ms()
    wlan, ssid = wifi.connect_any(networks(cred))
    try:
        print("  Wi-Fi 연결: %s, %d ms, IP %s" % (ssid, utime.ticks_diff(utime.ticks_ms(), t0),
                                                wlan.ifconfig()[0]))
        if not timesync.synced:
            try:
                timesync.ntp()
                print("  NTP 시각 맞춤")
            except Exception as e:
                print("  NTP 실패 (응답의 시각으로 대신):", e)
        t1 = utime.ticks_ms()
        tries = getattr(config, "HTTP_TRIES", 2)
        for k in range(tries):
            try:
                n = http.get_to_file(cred.CALENDAR_URL, tmp, timeout=getattr(config, "HTTP_TIMEOUT_S", 45))
                break
            except OSError as e:
                if k == tries - 1:
                    raise
                print("  일정 받기 실패, 다시 시도:", e)
                gc.collect()
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
