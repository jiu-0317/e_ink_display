"""PC에서 실행: 원본 글꼴(BDF/TTF/OTF) → Pico용 비트맵 글꼴 파일(.epf)

    pip install pillow
    python tools/fontgen/build_fonts.py          (프로젝트 폴더에서)

결과: app/fonts/xs.epf, s.epf, m.epf, xl.epf

.epf 형식 (리틀엔디언) — Pico가 글자 하나씩 seek 해서 읽도록 설계
    헤더 16B : b"EPF1", 버전 u8, 줄높이 u8, 기준선 u8, 예비 u8, 구간 수 u16, 예비 u16, 글자 수 u32
    구간     : (시작 코드포인트 u32, 개수 u16) x 구간 수        ← RAM에 올림 (작음)
    폭       : 글자마다 advance u8                              ← RAM에 올림 (약 11KB)
    위치     : 글자마다 레코드 시작 위치 u32                    ← 파일에서 읽음
    레코드   : xo i8, yo u8, w u8, h u8, 비트맵 (MONO_HLSB, 한 줄 (w+7)//8 바이트) x h
               xo = 글자 시작점에서 잉크 왼쪽까지, yo = 줄 상자 위에서 잉크 위까지
"""
import os
import struct
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from bdf import BdfFont  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(HERE, "src")
OUT = os.path.join(ROOT, "app", "fonts")

# 넣을 문자 (원본에 있는 것만 들어감)
TEXT_RANGES = [
    (0x20, 0x7E),        # ASCII
    (0xA0, 0xFF),        # Latin-1 (· ° × 등)
    (0x2010, 0x2027),    # – — ‘ ’ “ ” • …
    (0x2030, 0x203B),
    (0x2190, 0x2199),    # 화살표
    (0x2460, 0x2473),    # ① ~ ⑳
    (0x25A0, 0x25CF),    # ■ □ ▲ ▶ ○ ●
    (0x2605, 0x2606),    # ★ ☆
    (0x3000, 0x3011),    # CJK 기호 「 」 『 』
    (0x3131, 0x318E),    # 한글 자모 ㄱ ㅏ
    (0xAC00, 0xD7A3),    # 한글 음절 11,172자
    (0xFF01, 0xFF5E),    # 전각 기호
]
DIGIT_RANGES = [(0x30, 0x39), (0x2D, 0x2F), (0x3A, 0x3A)]   # 0-9 - . / :

# 줄 상자(위/아래 잘라낼 높이)를 정할 때 기준이 되는 문자
CORE = [c for c in range(0x20, 0x7F)] + list(range(0xAC00, 0xD7A4, 7))

FONTS = [
    # 이름, 원본, 크기(px, TTF만), 문자 범위
    ("xs", "Galmuri11.bdf", None, TEXT_RANGES),
    ("s", "neodgm.ttf", 16, TEXT_RANGES),
    ("m", "Pretendard-SemiBold.ttf", 24, TEXT_RANGES),
    ("xl", "Pretendard-Bold.ttf", 96, DIGIT_RANGES),
]


# ------------------------------------------------------------ 원본에서 글자 꺼내기
# 결과: dx, 잉크 비트맵 [(x, y)...] — 좌표는 "글자 시작점 = 0, 기준선 = 0, 위쪽이 -"
class BdfSource:
    def __init__(self, path):
        self.f = BdfFont(path)

    def has(self, cp):
        return cp in self.f.glyphs

    def glyph(self, cp):
        g = self.f.glyphs[cp]
        pts = []
        for j in range(g.h):
            row = g.rows[j]
            for i in range(g.w):
                if (row >> (g.w - 1 - i)) & 1:
                    pts.append((g.xo + i, -(g.yo + g.h) + j))
        return g.dx, pts


class TtfSource:
    def __init__(self, path, size):
        from fontTools.ttLib import TTFont
        self.cmap = TTFont(path).getBestCmap()
        self.font = ImageFont.truetype(path, size)
        self.size = size

    def has(self, cp):
        return cp in self.cmap

    def glyph(self, cp):
        ch = chr(cp)
        dx = int(round(self.font.getlength(ch)))
        S = self.size * 3
        img = Image.new("1", (S, S), 0)
        d = ImageDraw.Draw(img)
        d.fontmode = "1"                             # 흑백, 안티앨리어싱 없음
        ox, oy = self.size, self.size * 2            # 글자 시작점/기준선 위치
        d.text((ox, oy), ch, font=self.font, fill=1, anchor="ls")
        px = img.load()
        bb = img.getbbox()
        pts = []
        if bb:
            for y in range(bb[1], bb[3]):
                for x in range(bb[0], bb[2]):
                    if px[x, y]:
                        pts.append((x - ox, y - oy))
        return dx, pts


def build(name, src_file, size, ranges):
    path = os.path.join(SRC, src_file)
    src = BdfSource(path) if src_file.endswith(".bdf") else TtfSource(path, size)

    cps = [c for a, b in ranges for c in range(a, b + 1) if src.has(c)]
    glyphs = {c: src.glyph(c) for c in cps}

    # 줄 상자: 기준 문자들의 잉크 위/아래 범위
    core = [c for c in CORE if c in glyphs] or cps
    top = min((min(y for _, y in glyphs[c][1]) for c in core if glyphs[c][1]), default=0)
    bot = max((max(y for _, y in glyphs[c][1]) for c in core if glyphs[c][1]), default=0) + 1
    line_h = bot - top
    ascent = -top

    # 연속 구간
    ranges_out = []
    for c in cps:
        if ranges_out and ranges_out[-1][0] + ranges_out[-1][1] == c:
            ranges_out[-1][1] += 1
        else:
            ranges_out.append([c, 1])

    adv = bytearray()
    records = []
    clipped = 0
    for c in cps:
        dx, pts = glyphs[c]
        adv.append(max(0, min(255, dx)))
        pts2 = [(x, y - top) for x, y in pts if top <= y < bot]
        clipped += len(pts) - len(pts2)
        if not pts2:
            records.append(struct.pack("<bBBB", 0, 0, 0, 0))
            continue
        x0 = min(x for x, _ in pts2)
        x1 = max(x for x, _ in pts2) + 1
        y0 = min(y for _, y in pts2)
        y1 = max(y for _, y in pts2) + 1
        w, h = x1 - x0, y1 - y0
        stride = (w + 7) // 8
        bm = bytearray(stride * h)
        for x, y in pts2:
            i = (y - y0) * stride + (x - x0) // 8
            bm[i] |= 0x80 >> ((x - x0) & 7)
        records.append(struct.pack("<bBBB", x0, y0, w, h) + bytes(bm))

    n = len(cps)
    head = struct.pack("<4sBBBBHHI", b"EPF1", 1, line_h, ascent, 0, len(ranges_out), 0, n)
    rng = b"".join(struct.pack("<IH", a, k) for a, k in ranges_out)
    base = len(head) + len(rng) + n + 4 * n
    offs = []
    pos = base
    for r in records:
        offs.append(pos)
        pos += len(r)
    data = head + rng + bytes(adv) + b"".join(struct.pack("<I", o) for o in offs) + b"".join(records)

    os.makedirs(OUT, exist_ok=True)
    out = os.path.join(OUT, name + ".epf")
    with open(out, "wb") as f:
        f.write(data)
    hangul = sum(1 for c in cps if 0xAC00 <= c <= 0xD7A3)
    print("%-3s %-26s 줄높이 %3d  기준선 %3d  글자 %5d (한글 %5d)  %7.1f KB%s" %
          (name, src_file, line_h, ascent, n, hangul, len(data) / 1024,
           "  (상자 밖 잘린 픽셀 %d)" % clipped if clipped else ""))
    return out


if __name__ == "__main__":
    for spec in FONTS:
        build(*spec)
