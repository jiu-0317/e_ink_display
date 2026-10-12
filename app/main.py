# 메인 루프 — 상태: 현재 화면, 화면 안 이동량(offset), 동기화 일정
#
#   KEY0 짧게: 화면 순환 (월 → 주 → 오늘)
#   KEY0 길게: 오늘로 복귀 (offset 0)
#   KEY1 짧게: 다음 달 / 다음 주 / 다음 날 (KEY0 길게 누르면 오늘로)
#   KEY1 길게: 지금 바로 구글 캘린더 동기화 + full 갱신
#
# 부팅: 저장해 둔 일정으로 먼저 그림 → 동기화 → 바뀌었으면 다시 그림
# 이후: SYNC_MIN 마다 동기화, 시계 기준 10분(오늘)/30분(월·주) 경계마다 다시 그림, 자정에 full 갱신
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
from screens import month, week, today, timeline


def today_screen(fb, ctx):
    """오늘 화면: 시간표(기본, offset = 며칠 뒤) 또는 목록(offset = 페이지)."""
    (timeline.render if config.TODAY_STYLE == "timeline" else today.render)(fb, ctx)


SCREENS = (month.render, week.render, today_screen)
SCREEN_NAMES = ("month", "week", "today")
TODAY = 2
MIN = 60000


def load_credentials():
    try:
        import credentials as c
    except ImportError:
        return None
    url = getattr(c, "CALENDAR_URL", "")
    has_wifi = getattr(c, "WIFI_NETWORKS", None) or getattr(c, "WIFI_SSID", "")
    if not has_wifi or not url or "여기에" in url:
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
    ref = Refresher(epd, config.FULL_EVERY, config.PARTIALS_BEFORE_FULL)
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
    dirty = True                                 # 다시 그려야 함
    changed = True                               # 시간 경과가 아닌 이유(버튼·데이터)로 다시 그림
    drawn_slot = None                            # 마지막으로 그린 시각 칸 (10분/30분 단위)
    force_sync = False
    t = utime.ticks_ms()
    next_sync = t                                # 첫 화면을 그린 직후 바로 동기화
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
            dirty = changed = True

        # ---- 동기화 (첫 화면을 그린 뒤부터)
        t = utime.ticks_ms()
        if cred and ref.total > 0 and (force_sync or utime.ticks_diff(t, next_sync) >= 0):
            force_sync = False
            was_valid = valid
            print("동기화 시작")
            led(True)
            try:
                import sync
                changed_data, count = sync.run(cred)
                print("동기화 완료: 일정 %d개, %s" % (count, "바뀜" if changed_data else "그대로"))
                if changed_data:
                    events = load_events(config.CACHE_PATH)
                    ref.request_full()
                    dirty = changed = True
                if status:
                    status = ""
                    dirty = changed = True
                next_sync = utime.ticks_add(t, config.SYNC_MIN * MIN)
            except Exception as e:
                print("동기화 실패:", e)
                if status != "동기화 실패":
                    status = "동기화 실패"
                    dirty = changed = True
                next_sync = utime.ticks_add(t, config.SYNC_RETRY_MIN * MIN)
            led(False)
            gc.collect()
            now, valid = clock.now()
            if valid and not was_valid:          # 처음으로 시각을 맞춤 → 날짜가 바뀌었을 수 있음
                last_day = now[:3]
                dirty = changed = True

        # ---- 시간 흐름
        now, valid = clock.now()
        if now[:3] != last_day:                  # 자정: 날짜가 바뀌면 full 로 다시 그림
            last_day = now[:3]
            offset = 0
            ref.request_full()
            dirty = changed = True
        tick = config.TODAY_TICK_MIN if (screen == TODAY and offset == 0) else config.OTHER_TICK_MIN
        slot = model.minute_of(now) // tick
        if valid and slot != drawn_slot:         # 시계가 10분(또는 30분) 경계를 넘음
            dirty = True

        # ---- 그리기
        if dirty:
            partial = (not changed and screen == TODAY and config.TODAY_TICK_PARTIAL
                       and drawn_slot is not None)
            dirty = changed = False
            drawn_slot = slot
            t0 = utime.ticks_ms()
            SCREENS[screen](fb, Ctx(now, valid, events, offset, status))
            draw_ms = utime.ticks_diff(utime.ticks_ms(), t0)
            mode, ms = ref.show(partial)
            gc.collect()
            print("[%02d:%02d %s +%d] draw %d ms, %s refresh %d ms (fast %d, partial %d), RAM free %d KB" %
                  (now[3], now[4], SCREEN_NAMES[screen], offset, draw_ms, mode, ms,
                   ref.fast_count, ref.partial_count, gc.mem_free() // 1024))

        utime.sleep_ms(config.LOOP_MS)


def run():
    """전원을 켜면 자동 실행되는 입구. 오류가 나면 error.log 에 남기고 30초 뒤 다시 시작."""
    utime.sleep_ms(500)                          # 전원 안정 + Ctrl+C 로 끼어들 틈
    try:
        main()
    except KeyboardInterrupt:                    # VS Code(MicroPico)가 멈춘 경우
        print("중단됨")
    except Exception as e:
        import sys
        try:
            import io
            buf = io.StringIO()
            sys.print_exception(e, buf)
            msg = buf.getvalue()
        except Exception:
            msg = repr(e)
        print(msg)
        try:
            t = utime.localtime()
            with open("error.log", "a") as f:
                f.write("---- %04d-%02d-%02d %02d:%02d:%02d\n%s\n" % (t[:6] + (msg,)))
        except Exception:
            pass
        utime.sleep(30)
        import machine
        machine.reset()


run()
