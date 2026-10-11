# 날짜 계산 (라이브러리 없이 순수 계산 — Pico와 PC에서 똑같이 동작)
# 요일은 월요일 = 0 ... 일요일 = 6  (MicroPython utime.localtime 과 같은 규칙)

_DIM = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)

WD_SHORT = ("MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN")
WD_LONG = ("MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY")
WD_KO = ("월", "화", "수", "목", "금", "토", "일")
WD_KO_LONG = ("월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일")


def is_leap(y):
    return y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)


def days_in_month(y, m):
    return 29 if (m == 2 and is_leap(y)) else _DIM[m - 1]


def to_ord(y, m, d):
    """1970-01-01 = 0 인 일련번호 (Howard Hinnant days_from_civil)."""
    y -= m <= 2
    era = (y if y >= 0 else y - 399) // 400
    yoe = y - era * 400
    doy = (153 * (m + (-3 if m > 2 else 9)) + 2) // 5 + d - 1
    doe = yoe * 365 + yoe // 4 - yoe // 100 + doy
    return era * 146097 + doe - 719468


def from_ord(n):
    n += 719468
    era = (n if n >= 0 else n - 146096) // 146097
    doe = n - era * 146097
    yoe = (doe - doe // 1460 + doe // 36524 - doe // 146096) // 365
    y = yoe + era * 400
    doy = doe - (365 * yoe + yoe // 4 - yoe // 100)
    mp = (5 * doy + 2) // 153
    d = doy - (153 * mp + 2) // 5 + 1
    m = mp + (3 if mp < 10 else -9)
    return (y + (m <= 2), m, d)


def weekday(y, m, d):
    """월=0 ... 일=6. (1970-01-01 은 목요일=3)"""
    return (to_ord(y, m, d) + 3) % 7


def add_days(y, m, d, n):
    return from_ord(to_ord(y, m, d) + n)


def add_months(y, m, n):
    k = y * 12 + (m - 1) + n
    return (k // 12, k % 12 + 1)


def month_grid(y, m):
    """월간 달력 6주 x 7일 = 42칸. 일요일 시작. (y, m, d) 리스트."""
    wd1 = weekday(y, m, 1)                 # 월=0..일=6
    back = (wd1 + 1) % 7                   # 그 주 일요일까지 거슬러 올라갈 일수
    start = to_ord(y, m, 1) - back
    return [from_ord(start + i) for i in range(42)]


def week_days(y, m, d):
    """(y, m, d)가 속한 주의 월~일 7일."""
    start = to_ord(y, m, d) - weekday(y, m, d)
    return [from_ord(start + i) for i in range(7)]
