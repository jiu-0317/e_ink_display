# MicroPython 내장 8x8 글꼴을 확대해서 쓰는 임시/예비 글꼴 (글꼴 파일이 없을 때 대신 사용)
import framebuf
from gfx.layout import BLACK, WHITE  # noqa: F401  (BLACK 은 다른 모듈이 여기서 가져감)


def _palette(color):
    """blit 용 팔레트: 글리프 비트 1(잉크) → color, 0(배경) → 반대색(=key 로 투명 처리)."""
    p = framebuf.FrameBuffer(bytearray(1), 2, 1, framebuf.MONO_HLSB)
    p.pixel(0, 0, 1 - color)
    p.pixel(1, 0, color)
    return p


PAL = {BLACK: _palette(BLACK), WHITE: _palette(WHITE)}


class Font8:
    """MicroPython 내장 8x8 글꼴을 px 픽셀 크기로 확대 (정수배가 아니면 최근접 확대).
    글자별로 확대 결과를 캐시해서 blit."""

    def __init__(self, px=8):
        self.px = px
        self.cw = px                 # 글자 폭 (고정폭, 정사각)
        self.h = px
        self._cache = {}

    def width(self, s):
        return len(s) * self.cw

    def has(self, ch):
        return 32 <= ord(ch) < 127

    def _glyph(self, ch):
        g = self._cache.get(ch)
        if g is None:
            small = framebuf.FrameBuffer(bytearray(8), 8, 8, framebuf.MONO_HLSB)
            small.fill(0)
            small.text(ch, 0, 0, 1)
            px = self.px
            if px == 8:
                g = small
            elif px % 8 == 0:                       # 정수배: 블록으로 확대
                s = px // 8
                g = framebuf.FrameBuffer(bytearray(px * px // 8), px, px, framebuf.MONO_HLSB)
                g.fill(0)
                for j in range(8):
                    for i in range(8):
                        if small.pixel(i, j):
                            g.fill_rect(i * s, j * s, s, s, 1)
            else:                                   # 예: 12px = 1.5배, 최근접
                stride = (px + 7) // 8
                g = framebuf.FrameBuffer(bytearray(stride * px), px, px, framebuf.MONO_HLSB)
                g.fill(0)
                for j in range(px):
                    sj = j * 8 // px
                    for i in range(px):
                        if small.pixel(i * 8 // px, sj):
                            g.pixel(i, j, 1)
            self._cache[ch] = g
        return g

    def draw(self, fb, s, x, y, color=BLACK):
        """글자를 그리고 끝난 x 좌표를 돌려줌. 배경은 건드리지 않음(투명)."""
        pal = PAL[color]
        key = 1 - color
        cw = self.cw
        for ch in s:
            fb.blit(self._glyph(ch), x, y, key, pal)
            x += cw
        return x


