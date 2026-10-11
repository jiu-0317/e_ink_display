/**
 * e-Paper 달력용 구글 캘린더 → JSON 다리 (Google Apps Script 웹 앱)
 *
 * Pico 가 이 웹 앱 주소를 부르면, 내 구글 캘린더 일정을 app/model.py 가 읽는 형식으로 돌려준다.
 *   시간 일정: {"title": "회의", "start": "2026-10-10T09:00", "end": "2026-10-10T10:00"}
 *   종일 일정: {"title": "휴가", "start": "2026-10-21", "end": "2026-10-24"}   (end 는 포함 안 함)
 *
 * 설치 방법은 tools/apps_script/README.md 참고.
 */

// ---------------------------------------------------------------- 설정
// Pico 의 credentials.py 에 있는 주소 끝의 token 과 같아야 함. 아무도 모르는 긴 문자열로.
const TOKEN = 'QQtIT-iI-Mk8oTDp4ruk8ORY';

// 가져올 캘린더. 'primary' = 내 기본 캘린더.
// 다른 캘린더는 구글 캘린더 → 설정 → 해당 캘린더 → "캘린더 통합" → 캘린더 ID 를 넣으면 됨.
// 예) 대한민국 공휴일: 'ko.south_korea#holiday@group.v.calendar.google.com'
const CALENDAR_IDS = [
  'primary',
  // 'ko.south_korea#holiday@group.v.calendar.google.com',
];

const MONTHS_BACK = 1;    // 지난달 1일부터
const MONTHS_AHEAD = 3;   // 3달 뒤 말일까지 (월간 화면에서 앞으로 넘겨 볼 수 있는 범위)
const TZ = 'Asia/Seoul';
const SKIP_DECLINED = true;   // 내가 "거절"한 초대 일정은 빼기


// ---------------------------------------------------------------- 웹 앱 입구
function doGet(e) {
  if (!e || !e.parameter || e.parameter.token !== TOKEN) {
    return json_({ error: 'forbidden' });
  }
  try {
    return json_(collect_());
  } catch (err) {
    return json_({ error: String(err) });
  }
}

// 편집기에서 ▶ 실행해서 권한 허용 + 결과 확인용
function test() {
  const r = collect_();
  Logger.log('일정 %s개', r.events.length);
  Logger.log(JSON.stringify(r.events.slice(0, 10), null, 1));
}


// ---------------------------------------------------------------- 본체
function collect_() {
  const now = new Date();
  const ym = Utilities.formatDate(now, TZ, 'yyyy-MM').split('-').map(Number);
  const start = new Date(ym[0], ym[1] - 1 - MONTHS_BACK, 1);
  const end = new Date(ym[0], ym[1] + MONTHS_AHEAD, 1);
  const scriptTz = Session.getScriptTimeZone();

  const events = [];
  for (const id of CALENDAR_IDS) {
    const cal = id === 'primary' ? CalendarApp.getDefaultCalendar() : CalendarApp.getCalendarById(id);
    if (!cal) continue;
    for (const ev of cal.getEvents(start, end)) {
      if (SKIP_DECLINED) {
        try {
          if (ev.getMyStatus() === CalendarApp.GuestStatus.NO) continue;
        } catch (err) { /* 공휴일처럼 상태가 없는 캘린더 */ }
      }
      if (ev.isAllDayEvent()) {
        events.push({
          title: ev.getTitle(),
          start: Utilities.formatDate(ev.getAllDayStartDate(), scriptTz, 'yyyy-MM-dd'),
          end: Utilities.formatDate(ev.getAllDayEndDate(), scriptTz, 'yyyy-MM-dd'),
        });
      } else {
        events.push({
          title: ev.getTitle(),
          start: Utilities.formatDate(ev.getStartTime(), TZ, "yyyy-MM-dd'T'HH:mm"),
          end: Utilities.formatDate(ev.getEndTime(), TZ, "yyyy-MM-dd'T'HH:mm"),
        });
      }
    }
  }
  events.sort((a, b) => (a.start < b.start ? -1 : a.start > b.start ? 1 : 0));
  return { now: Math.floor(now.getTime() / 1000), tz: TZ, events: events };
}

function json_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
      .setMimeType(ContentService.MimeType.JSON);
}
