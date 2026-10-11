# 메인 루프 — 상태: 현재 화면, 화면 안 이동량(offset), 동기화 일정
#
#   KEY0 짧게: 화면 순환 (월 → 주 → 오늘)
#   KEY0 길게: 오늘로 복귀 (offset 0)
#   KEY1 짧게: 다음 달 / 다음 주 / 다음 페이지(오늘 화면)
#   KEY1 길게: 지금 바로 구글 캘린더 동기화 + full 갱신
#
# 부팅: 저장해 둔 일정으로 먼저 그림 → 동기화 → 바뀌었으면 다시 그림
# 이후: SYNC_MIN 마다 동기화, REDRAW_MIN 마다 다시 그림, 자정에 full 갱신
# 갱신 중에 여러 번 눌러도 상태만 바꾸고 화면은 마지막 상태로 한 번만 그림.
import gc
import utime

import config
from hw.epd7in5 import EPD_7in5
from hw.buttons import Buttons, SHORT, LONG
from hw import clock
from gfx.refresh import Refresher
import model
from screens.common import Ctx
from screens import month, week, today

SCREENS = (month.render, week.render, today.render)
SCREEN_NAMES = ("month", "week", "today")
MIN = 60000


def load_credentials():
    try:
        import credentials as c
    except ImportError:
        return None
    url = getattr(c, "CALENDAR_URL", "")
    if not getattr(c, "WIFI_SSID", "") or not url or "여기에" in url:
        return None
    return c


def load_events(path):
    try:
        ev = model.load(path)
        print("일정 %d개 읽음 (%s)" % (len(ev), path))
        return ev
    except Exception as e:
        print("일정 파일을 읽지 못함:", path, e)
        return []


def led(on):
    try:
        from machine import Pin
        Pin("LED", Pin.OUT).value(1 if on else 0)
    except Exception:
        pass


def main():
    epd = EPD_7in5(baudrate=config.EPD_BAUD)
    epd.sleep()                                  # 생성자가 init 한 상태 → 일단 재움
    fb = epd.image1Gray
    ref = Refresher(epd, config.FULL_EVERY)
    btn = Buttons({"KEY0": config.KEY0_PIN, "KEY1": config.KEY1_PIN},
                  config.LONG_MS, config.DEBOUNCE_MS)

    cred = load_credentials()
    if cred:
        events = load_events(config.CACHE_PATH)
        status = ""
    else:
        print("credentials.py 가 비어 있음 → 예시 일정으로 동작 (동기화 안 함)")
        events = load_events(config.MOCK_PATH)
        status = "예시 데이터"

    screen = 0
    offset = 0
    dirty = True
    force_sync = False
    t = utime.ticks_ms()
    next_sync = t                                # 첫 화면을 그린 직후 바로 동기화
    next_redraw = utime.ticks_add(t, config.REDRAW_MIN * MIN)
    now, valid = clock.now()
    last_day = now[:3]

    while True:
        # ---- 버튼
        for name, kind in btn.poll():
            print("button:", name, kind)
            if name == "KEY0" and kind == SHORT:
                screen = (screen + 1) % len(SCREENS)
                offset = 0
            elif name == "KEY0" and kind == LONG:
                offset = 0
            elif name == "KEY1" and kind == SHORT:
                offset += 1
            elif name == "KEY1" and kind == LONG:
                force_sync = True
                ref.request_full()
            dirty = True

        # ---- 동기화 (첫 화면을 그린 뒤부터)
        t = utime.ticks_ms()
        if cred and ref.total > 0 and (force_sync or utime.ticks_diff(t, next_sync) >= 0):
            force_sync = False
            was_valid = valid
            print("동기화 시작")
            led(True)
            try:
                import sync
                changed, count = sync.run(cred)
                print("동기화 완료: 일정 %d개, %s" % (count, "바뀜" if changed else "그대로"))
                if changed:
                    events = load_events(config.CACHE_PATH)
                    ref.request_full()
                    dirty = True
                if status:
                    status = ""
                    dirty = True
                next_sync = utime.ticks_add(t, config.SYNC_MIN * MIN)
            except Exception as e:
                print("동기화 실패:", e)
                if status != "동기화 실패":
                    status = "동기화 실패"
                    dirty = True
                next_sync = utime.ticks_add(t, config.SYNC_RETRY_MIN * MIN)
            led(False)
            gc.collect()
            now, valid = clock.now()
            if valid and not was_valid:          # 처음으로 시각을 맞춤 → 날짜가 바뀌었을 수 있음
                last_day = now[:3]
                dirty = True

        # ---- 시간 흐름
        now, valid = clock.now()
        if now[:3] != last_day:                  # 자정: 날짜가 바뀌면 full 로 다시 그림
            last_day = now[:3]
            offset = 0
            ref.request_full()
            dirty = True
        if utime.ticks_diff(utime.ticks_ms(), next_redraw) >= 0:
            dirty = True

        # ---- 그리기
        if dirty:
            dirty = False
            t0 = utime.ticks_ms()
            SCREENS[screen](fb, Ctx(now, valid, events, offset, status))
            draw_ms = utime.ticks_diff(utime.ticks_ms(), t0)
            mode, ms = ref.show()
            next_redraw = utime.ticks_add(utime.ticks_ms(), config.REDRAW_MIN * MIN)
            gc.collect()
            print("[%s +%d] draw %d ms, %s refresh %d ms (fast since full: %d), RAM free %d KB" %
                  (SCREEN_NAMES[screen], offset, draw_ms, mode, ms, ref.fast_count,
                   gc.mem_free() // 1024))

        utime.sleep_ms(config.LOOP_MS)


main()
