# 일정 모델 — 화면 코드는 데이터가 어디서 왔는지(가짜 JSON / 구글 캘린더) 모른다.
#
# JSON 형식 (구글 캘린더 API의 date / dateTime 모양을 그대로 따름):
#   시간 일정: {"title": "회의", "start": "2026-10-10T09:00", "end": "2026-10-10T10:00"}
#   종일 일정: {"title": "휴가", "start": "2026-10-21", "end": "2026-10-24"}   ← end 는 포함 안 함
#
# 내부 시각은 "분 단위 일련번호" (1970-01-01 00:00 = 0) 로 다룬다.
import json
import cal

DAY = 1440


def _parse(s):
    """'YYYY-MM-DD' 또는 'YYYY-MM-DDTHH:MM[:SS]' → (분 일련번호, 종일 여부)."""
    y, m, d = int(s[0:4]), int(s[5:7]), int(s[8:10])
    if len(s) > 10:
        return cal.to_ord(y, m, d) * DAY + int(s[11:13]) * 60 + int(s[14:16]), False
    return cal.to_ord(y, m, d) * DAY, True


class Event:
    def __init__(self, title, start, end, all_day):
        self.title = title
        self.start = start          # 분 일련번호
        self.end = end              # 분 일련번호 (포함 안 함)
        self.all_day = all_day

    def hm(self, t):
        t %= DAY
        return "%02d:%02d" % (t // 60, t % 60)

    def start_hm(self):
        return self.hm(self.start)

    def end_hm(self):
        return self.hm(self.end)

    def sort_key(self):
        return (0 if self.all_day else 1, self.start, self.title)


def from_dict(d):
    start, all_day = _parse(d["start"])
    end, _ = _parse(d.get("end") or d["start"])
    if end <= start:
        end = start + (DAY if all_day else 1)
    return Event(d.get("title") or "(no title)", start, end, all_day)


def load(path):
    with open(path) as f:
        items = json.load(f)
    if isinstance(items, dict):          # Apps Script 응답 그대로인 경우 {"events": [...]}
        items = items.get("events", [])
    events = [from_dict(d) for d in items]
    events.sort(key=lambda e: e.sort_key())
    return events


def minute_of(now):
    """now = (y, m, d, h, mi, ...) → 분 일련번호."""
    return cal.to_ord(now[0], now[1], now[2]) * DAY + now[3] * 60 + now[4]


def by_day(events, ord_from, ord_to):
    """{날짜 일련번호: [Event, ...]} — ord_from 이상 ord_to 미만 날짜만. 여러 날 일정은 매일 들어감."""
    idx = {}
    lo = ord_from * DAY
    hi = ord_to * DAY
    for e in events:
        if e.end <= lo or e.start >= hi:
            continue
        a = max(e.start, lo) // DAY
        b = (min(e.end, hi) - 1) // DAY
        for o in range(a, b + 1):
            lst = idx.get(o)
            if lst is None:
                lst = idx[o] = []
            lst.append(e)
    return idx       # load() 에서 정렬해 두었으므로 날짜별 목록도 정렬된 상태


def layout_columns(items):
    """겹치는 일정을 나란히 놓기 (구글 캘린더 방식).
    items: [(시작, 끝, 무엇), ...] 시작 순 정렬. 끝은 화면에 보이는 끝(최소 높이 반영).
    반환: [(시작, 끝, 무엇, 열 번호, 그 묶음의 열 수), ...]"""
    out = []
    group = []
    col_end = []            # 열마다 마지막 일정의 끝
    group_end = -1
    for s, e, x in items:
        if group and s >= group_end:          # 앞 묶음과 안 겹침 → 묶음 마감
            n = len(col_end)
            out.extend(g + (n,) for g in group)
            group, col_end, group_end = [], [], -1
        for c in range(len(col_end)):
            if col_end[c] <= s:
                col_end[c] = e
                break
        else:
            c = len(col_end)
            col_end.append(e)
        group.append((s, e, x, c))
        group_end = max(group_end, e)
    n = len(col_end)
    out.extend(g + (n,) for g in group)
    return out


def on_day(events, o):
    return by_day(events, o, o + 1).get(o, [])
