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


def _scan():
    """주변에 보이는 SSID -> 신호세기(dBm). 실패하면 None."""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    try:
        seen = {}
        for ap in wlan.scan():
            try:
                name = ap[0].decode()
            except Exception:
                continue
            if name and (name not in seen or ap[3] > seen[name]):
                seen[name] = ap[3]
        return seen
    except Exception as e:
        print("  Wi-Fi 스캔 실패 (목록 전부 시도):", e)
        return None


def connect_any(networks, timeout_ms=15000):
    """[(ssid, password), ...] 를 앞에서부터 차례로 시도. (wlan, ssid) 반환.

    먼저 주변을 스캔해서 보이는 것만 시도한다 (안 보이는 곳에서 시간 낭비 X).
    순서는 목록에 적은 순서 = 우선순위.
    """
    seen = _scan()
    todo = [n for n in networks if seen is None or n[0] in seen]
    if not todo:
        raise OSError("등록된 Wi-Fi 가 주변에 없음 (보이는 것: %s)"
                      % ", ".join(sorted(seen)) if seen else "등록된 Wi-Fi 가 주변에 없음")
    errors = []
    for ssid, password in todo:
        try:
            if seen:
                print("  Wi-Fi 시도: %s (%d dBm)" % (ssid, seen[ssid]))
            else:
                print("  Wi-Fi 시도: %s" % ssid)
            return connect(ssid, password, timeout_ms), ssid
        except OSError as e:
            print("    실패:", e)
            errors.append("%s: %s" % (ssid, e))
    raise OSError("모든 Wi-Fi 실패 (" + " / ".join(errors) + ")")


def off(wlan):
    try:
        wlan.disconnect()
    except Exception:
        pass
    wlan.active(False)
