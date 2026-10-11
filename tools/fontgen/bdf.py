"""BDF 비트맵 글꼴 읽기 (PC 전용).

BDF 는 글자마다 비트맵이 그대로 들어 있는 텍스트 형식이라, 픽셀 글꼴을 손실 없이 가져올 수 있다.
"""


class Glyph:
    __slots__ = ("cp", "dx", "w", "h", "xo", "yo", "rows")

    def __init__(self, cp, dx, w, h, xo, yo, rows):
        self.cp = cp          # 유니코드 코드포인트
        self.dx = dx          # 다음 글자까지 이동 폭 (advance)
        self.w, self.h = w, h  # 비트맵 크기
        self.xo, self.yo = xo, yo  # 기준선 기준 위치 (yo: 기준선에서 비트맵 아래까지, 위가 +)
        self.rows = rows      # 각 줄을 정수로 (MSB = 왼쪽), 폭 w 비트

    def pixel(self, x, y):
        return (self.rows[y] >> (self.w - 1 - x)) & 1


class BdfFont:
    def __init__(self, path):
        self.path = path
        self.glyphs = {}
        self.ascent = self.descent = 0
        self.props = {}
        self._load(path)

    def _load(self, path):
        with open(path, encoding="latin-1") as f:
            lines = f.read().splitlines()
        i = 0
        n = len(lines)
        in_props = False
        while i < n:
            ln = lines[i]
            if ln.startswith("STARTPROPERTIES"):
                in_props = True
            elif ln.startswith("ENDPROPERTIES"):
                in_props = False
            elif in_props:
                k, _, v = ln.partition(" ")
                self.props[k] = v.strip().strip('"')
            elif ln.startswith("STARTCHAR"):
                cp = dx = w = h = xo = yo = None
                i += 1
                while not lines[i].startswith("BITMAP"):
                    p = lines[i].split()
                    if p[0] == "ENCODING":
                        cp = int(p[1])
                    elif p[0] == "DWIDTH":
                        dx = int(p[1])
                    elif p[0] == "BBX":
                        w, h, xo, yo = map(int, p[1:5])
                    i += 1
                i += 1
                rows = []
                while not lines[i].startswith("ENDCHAR"):
                    hx = lines[i].strip()
                    v = int(hx, 16) if hx else 0
                    rows.append(v >> (len(hx) * 4 - w) if w else 0)
                    i += 1
                if cp is not None and cp >= 0:
                    self.glyphs[cp] = Glyph(cp, dx, w, h, xo, yo, rows[:h])
            i += 1
        self.ascent = int(self.props.get("FONT_ASCENT", 0))
        self.descent = int(self.props.get("FONT_DESCENT", 0))

    @property
    def line_h(self):
        return self.ascent + self.descent

    def get(self, ch):
        return self.glyphs.get(ord(ch)) or self.glyphs.get(0xFFFD) or self.glyphs.get(ord("?"))
