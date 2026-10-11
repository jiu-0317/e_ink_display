# .epf 비트맵 글꼴 읽기 (형식은 tools/fontgen/build_fonts.py 설명 참고)
#
# RAM 에는 구간 표와 글자 폭(약 11KB)만 올리고, 글자 모양은 처음 쓸 때 파일에서 읽어
# 작은 캐시에 둔다. 화면 코드가 쓰는 메서드는 Font8 과 같다: h, width(), draw(), has()
import struct
import framebuf
from gfx.font8 import PAL, BLACK

CACHE_MAX = 200          # 글꼴마다 기억해 둘 글자 모양 수 (넘치면 비움, 3개 글꼴 합쳐 약 60KB)


class BitmapFont:
    def __init__(self, path):
        self.path = path
        f = open(path, "rb")
        self.f = f
        head = f.read(16)
        magic, ver, self.h, self.ascent, _, n_ranges, _, n = struct.unpack("<4sBBBBHHI", head)
        if magic != b"EPF1":
            raise ValueError("not an EPF1 font: " + path)
        self.n = n
        self.ranges = []                     # (시작, 개수, 첫 글자 번호)
        first = 0
        raw = f.read(6 * n_ranges)
        for k in range(n_ranges):
            start, cnt = struct.unpack_from("<IH", raw, 6 * k)
            self.ranges.append((start, cnt, first))
            first += cnt
        self.adv = f.read(n)                 # 글자 폭
        self.off_pos = 16 + 6 * n_ranges + n
        self._cache = {}
        self._buf4 = bytearray(4)
        self.missing = self._index(0x25A1)   # □
        if self.missing < 0:
            self.missing = self._index(0x3F)  # ?

    def _index(self, cp):
        for start, cnt, first in self.ranges:
            if start <= cp < start + cnt:
                return first + cp - start
        return -1

    def has(self, ch):
        return self._index(ord(ch)) >= 0

    def _idx(self, ch):
        i = self._index(ord(ch))
        return i if i >= 0 else self.missing

    def width(self, s):
        adv = self.adv
        w = 0
        for ch in s:
            i = self._idx(ch)
            if i >= 0:
                w += adv[i]
        return w

    def _glyph(self, i):
        g = self._cache.get(i)
        if g is None:
            f = self.f
            b4 = self._buf4
            f.seek(self.off_pos + 4 * i)
            f.readinto(b4)
            f.seek(struct.unpack("<I", b4)[0])
            f.readinto(b4)
            xo, yo, w, h = struct.unpack("<bBBB", b4)
            if w == 0:
                g = (None, 0, 0)
            else:
                bm = bytearray(((w + 7) // 8) * h)
                f.readinto(bm)
                g = (framebuf.FrameBuffer(bm, w, h, framebuf.MONO_HLSB), xo, yo)
            if len(self._cache) >= CACHE_MAX:
                self._cache.clear()
            self._cache[i] = g
        return g

    def draw(self, fb, s, x, y, color=BLACK):
        """글자를 그리고 끝난 x 를 돌려줌. y = 줄 상자 위쪽. 배경은 투명."""
        pal = PAL[color]
        key = 1 - color
        adv = self.adv
        for ch in s:
            i = self._idx(ch)
            if i < 0:
                continue
            g, xo, yo = self._glyph(i)
            if g is not None:
                fb.blit(g, x + xo, y + yo, key, pal)
            x += adv[i]
        return x
