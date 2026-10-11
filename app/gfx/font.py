# 글꼴 역할 표 — 화면 코드는 F.XS / F.S / F.M / F.XL / F.TINY 만 쓴다.
#
#   XS   Galmuri11            (줄 13px)  월간/주간 칸 안 일정
#   S    Neo둥근모 16px        (줄 15px)  날짜 숫자, 시간, 요일 머리
#   M    Pretendard SemiBold 24px (줄 25px)  오늘 화면 일정 제목, 헤더 제목
#   XL   Pretendard Bold 96px  (숫자만)    오늘 화면 큰 날짜
#   TINY 내장 8x8               다른 달 날짜 숫자
#
# 글꼴 파일(fonts/*.epf)은 PC에서 tools/fontgen/build_fonts.py 로 만든다.
# 파일이 없으면 8x8 글꼴을 확대한 Font8 로 대신 그린다 (화면은 나오지만 한글은 안 보임).
from gfx.font8 import Font8, PAL  # noqa: F401
from gfx.bitmapfont import BitmapFont


def _load(path, fallback_px):
    try:
        return BitmapFont(path)
    except OSError as e:
        print("글꼴 파일 없음:", path, e, "→ 8x8 글꼴로 대신")
        return Font8(fallback_px)


TINY = Font8(8)
XS = _load("fonts/xs.epf", 12)
S = _load("fonts/s.epf", 16)
M = _load("fonts/m.epf", 24)
XL = _load("fonts/xl.epf", 96)
