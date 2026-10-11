# PC용 MicroPython framebuf 대체 모듈 (미리보기 전용, Pico에 올리지 마세요)
# 실제 bytearray 를 MicroPython과 같은 비트 배치로 읽고 씀 → 버퍼를 그대로 화면 에뮬레이터에 보낼 수 있음.
# 지원 형식: MONO_HLSB (전부), GS2_HMSB (pixel/fill/fill_rect 수준)
from font8x8 import FONT

MONO_VLSB = 0
MONO_HLSB = 3
MONO_HMSB = 4
GS2_HMSB = 5
GS4_HMSB = 2
GS8 = 6
RGB565 = 1


class FrameBuffer:
    def __init__(self, buf, width, height, fmt, stride=None):
        if fmt not in (MONO_HLSB, GS2_HMSB):
            raise NotImplementedError("pc_sim framebuf: format %d not supported" % fmt)
        self.buf = buf
        self.width = width
        self.height = height
        self.format = fmt
        stride = width if stride is None else stride
        if fmt == MONO_HLSB:
            self.stride = (stride + 7) & ~7
            need = self.stride * height // 8
        else:
            self.stride = (stride + 3) & ~3
            need = self.stride * height // 4
        if len(buf) < need:
            raise ValueError("buffer too small (%d < %d)" % (len(buf), need))

    # ---------------------------------------------------- pixel 단위
    def _set(self, x, y, c):
        if self.format == MONO_HLSB:
            i = (y * self.stride + x) >> 3
            b = 7 - (x & 7)
            if c & 1:
                self.buf[i] |= (1 << b)
            else:
                self.buf[i] &= ~(1 << b) & 0xFF
        else:
            i = (y * self.stride + x) >> 2
            s = (x & 3) << 1
            self.buf[i] = (self.buf[i] & ~(3 << s) & 0xFF) | ((c & 3) << s)

    def _get(self, x, y):
        if self.format == MONO_HLSB:
            return (self.buf[(y * self.stride + x) >> 3] >> (7 - (x & 7))) & 1
        return (self.buf[(y * self.stride + x) >> 2] >> ((x & 3) << 1)) & 3

    def pixel(self, x, y, c=None):
        if not (0 <= x < self.width and 0 <= y < self.height):
            return None if c is not None else 0
        if c is None:
            return self._get(x, y)
        self._set(x, y, c)

    # ---------------------------------------------------- 채우기
    def fill(self, c):
        if self.format == MONO_HLSB:
            v = 0xFF if c & 1 else 0x00
        else:
            v = (c & 3) * 0x55
        n = self.stride * self.height // (8 if self.format == MONO_HLSB else 4)
        self.buf[0:n] = bytes([v]) * n

    def fill_rect(self, x, y, w, h, c):
        x0, y0 = max(x, 0), max(y, 0)
        x1, y1 = min(x + w, self.width), min(y + h, self.height)
        for yy in range(y0, y1):
            for xx in range(x0, x1):
                self._set(xx, yy, c)

    def hline(self, x, y, w, c):
        self.fill_rect(x, y, w, 1, c)

    def vline(self, x, y, h, c):
        self.fill_rect(x, y, 1, h, c)

    def rect(self, x, y, w, h, c, f=False):
        if f:
            self.fill_rect(x, y, w, h, c)
            return
        self.fill_rect(x, y, w, 1, c)
        self.fill_rect(x, y + h - 1, w, 1, c)
        self.fill_rect(x, y, 1, h, c)
        self.fill_rect(x + w - 1, y, 1, h, c)

    def line(self, x1, y1, x2, y2, c):
        dx, dy = abs(x2 - x1), -abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx + dy
        while True:
            self.pixel(x1, y1, c)
            if x1 == x2 and y1 == y2:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x1 += sx
            if e2 <= dx:
                err += dx
                y1 += sy

    # ---------------------------------------------------- 글자 (MicroPython과 같은 방식)
    def text(self, s, x0, y0, c=1):
        for ch in s.encode("utf-8"):           # MicroPython도 바이트 단위로 처리
            if ch < 32 or ch > 127:
                ch = 127
            data = FONT[(ch - 32) * 8:(ch - 32) * 8 + 8]
            for col in data:
                if 0 <= x0 < self.width:
                    y = y0
                    while col:
                        if col & 1 and 0 <= y < self.height:
                            self._set(x0, y, c)
                        col >>= 1
                        y += 1
                x0 += 1

    # ---------------------------------------------------- blit
    def blit(self, src, x, y, key=-1, palette=None):
        for j in range(src.height):
            for i in range(src.width):
                c = src._get(i, j)
                if palette is not None:          # MicroPython: 팔레트 먼저, 그다음 key 비교
                    c = palette._get(c, 0)
                if c == key:
                    continue
                self.pixel(x + i, y + j, c)

    def scroll(self, xstep, ystep):
        raise NotImplementedError("pc_sim framebuf: scroll")

    def ellipse(self, *a):
        raise NotImplementedError("pc_sim framebuf: ellipse")

    def poly(self, *a):
        raise NotImplementedError("pc_sim framebuf: poly")
