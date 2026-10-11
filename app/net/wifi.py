# Wi-Fi 켜기/끄기 (Pico 2 W, 2.4GHz 만 지원)
import utime
import network

_STATUS = {
    -1: "연결 실패",
    -2: "공유기를 찾지 못함 (SSID 확인, 2.4GHz 인지 확인)",
    -3: "비밀번호 틀림",
}


def connect(ssid, password, timeout_ms=20000):
    try:
        network.country("KR")
    except Exception:
        pass
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    try:
        wlan.config(pm=0xA11140)        # 절전 끄기 (연결 안정성)
    except Exception:
        pass
    if wlan.isconnected():
        return wlan
    wlan.connect(ssid, password)
    t0 = utime.ticks_ms()
    while not wlan.isconnected():
        st = wlan.status()
        if st < 0:
            off(wlan)
            raise OSError("Wi-Fi " + _STATUS.get(st, "오류 %d" % st))
        if utime.ticks_diff(utime.ticks_ms(), t0) > timeout_ms:
            off(wlan)
            raise OSError("Wi-Fi 연결 시간 초과")
        utime.sleep_ms(200)
    return wlan


def off(wlan):
    try:
        wlan.disconnect()
    except Exception:
        pass
    wlan.active(False)
