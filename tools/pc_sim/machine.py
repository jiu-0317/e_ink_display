# PC용 machine 대체 모듈 (미리보기 전용, Pico에 올리지 마세요)
# e-Paper 핀(DC=8, CS=9, RST=12, BUSY=13)과 SPI는 에뮬레이터로 연결,
# 버튼(KEY0=2, KEY1=3)은 preview.py 의 --keys 순서대로 자동으로 눌림.
import epaper_emu
import utime

DC_PIN, CS_PIN, RST_PIN, BUSY_PIN = 8, 9, 12, 13
KEY_PINS = {2: "0", 3: "1"}


class KeyScript:
    """'0,0,1L' 같은 순서. 0/1 = KEY0/KEY1 짧게(120ms), 뒤에 L = 길게(1500ms)."""

    def __init__(self, spec):
        self.events = []
        for tok in [t.strip() for t in spec.split(",") if t.strip()]:
            if tok[0] == "w":
                self.events.append(("w", int(tok[1:])))
            else:
                self.events.append((tok[0], 1500 if tok.upper().endswith("L") else 120))
        self.start = None

    def level(self, key):
        if not self.events:
            raise SystemExit("[PREVIEW] 키 순서를 모두 사용해서 종료")
        k, dur = self.events[0]
        if k == "w":                         # 대기: "w60000" = 60초 동안 아무것도 안 누름
            now = utime.ticks_ms()
            if self.start is None:
                self.start = now
            elif now - self.start >= dur:
                self.events.pop(0)
                self.start = None
            return 1
        if k != key:
            return 1
        now = utime.ticks_ms()
        if self.start is None:
            self.start = now
            return 0
        if now - self.start < dur:
            return 0
        self.events.pop(0)
        self.start = None
        return 1


KEYS = KeyScript("")


class Pin:
    IN = 0
    OUT = 1
    OPEN_DRAIN = 2
    PULL_UP = 1
    PULL_DOWN = 2
    IRQ_FALLING = 4
    IRQ_RISING = 8

    def __init__(self, id, mode=-1, pull=-1, value=None):
        self.id = id
        self._v = 1 if value is None else value

    def value(self, v=None):
        if v is None:
            if self.id == BUSY_PIN:
                return 1                       # 항상 idle
            if self.id in KEY_PINS:
                return KEYS.level(KEY_PINS[self.id])
            return self._v
        v = 1 if v else 0
        emu = epaper_emu.EMU
        if self.id == DC_PIN:
            emu.dc = v
        elif self.id == CS_PIN:
            emu.cs = v
        elif self.id == RST_PIN and v == 0 and self._v == 1:
            emu.on_reset()
        self._v = v

    def __call__(self, v=None):
        return self.value(v)

    def on(self):
        self.value(1)

    def off(self):
        self.value(0)

    def toggle(self):
        self.value(0 if self._v else 1)

    def irq(self, handler=None, trigger=None):
        pass


class SPI:
    def __init__(self, id, baudrate=1_000_000, **kw):
        self.id = id
        self.baudrate = baudrate

    def init(self, baudrate=None, **kw):
        if baudrate:
            self.baudrate = baudrate

    def write(self, buf):
        epaper_emu.EMU.on_spi(bytes(buf))

    def __repr__(self):
        return "SPI(%d, baudrate=%d) [pc_sim]" % (self.id, self.baudrate)


def freq(hz=None):
    return 150_000_000


def reset():
    raise SystemExit("[PREVIEW] machine.reset()")


def unique_id():
    return b"\x00" * 8


class RTC:
    def datetime(self, t=None):
        if t is not None:
            print("[pc_sim] RTC.datetime set:", t)
        return (2026, 1, 1, 3, 0, 0, 0, 0)
