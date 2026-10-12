# e-Paper 구글 캘린더

[English](README.md) | **한국어**

Raspberry Pi Pico 2 W 와 7.5인치 e-Paper 로 만든 탁상용 달력입니다.
구글 캘린더 일정을 30분마다 받아와서 **월간 / 주간 / 오늘(시간표)** 화면으로 보여 줍니다.
e-Paper 라서 전원을 꺼도 화면이 남아 있고, 눈이 편하며, 백라이트가 없습니다.

| 월간 | 주간 | 오늘 |
|:---:|:---:|:---:|
| ![월간 화면](pictures/monthly.jpg) | ![주간 화면](pictures/weekly.jpg) | ![오늘 화면](pictures/daily.jpg) |

## 주요 기능

- 구글 캘린더 자동 동기화 (30분마다, 버튼으로 즉시 동기화도 가능)
- 세 가지 화면: 월간 달력, 주간 일정, 오늘 시간표 (07시~24시, 지금 시각 선 표시)
- 한글 글꼴 (Pretendard, Galmuri11, Neo둥근모) 을 Pico 용 비트맵으로 변환해서 사용
- 10분마다 깜빡임 없는 부분 갱신, 일정이 바뀌거나 자정이 되면 전체 갱신으로 잔상 제거
- Wi-Fi 여러 개 등록 가능 (집 / 학교 / 회사 등 보이는 것에 자동 연결)
- 설정 전에도 예시 일정으로 바로 동작 → 하드웨어만 있으면 화면부터 확인 가능
- 하드웨어 없이 PC 에서 화면을 PNG 로 미리보기 하는 도구 포함

## 동작 방식

```
 ┌────────────┐   HTTPS GET (30분마다)    ┌───────────────────┐      ┌──────────────┐
 │ Pico 2 W   │ ───────────────────────▶ │ Google Apps Script│ ───▶ │ 구글 캘린더    │
 │ + e-Paper  │ ◀─────────────────────── │ (내 계정, 웹 앱)   │      └──────────────┘
 └────────────┘      일정 JSON            └───────────────────┘
```

Pico 가 구글 로그인을 직접 하지 않아도 되도록, 내 구글 계정에서 도는 작은 스크립트(Apps Script)가
일정을 JSON 으로 바꿔서 주소 하나로 내보냅니다. 주소 끝의 비밀 `token` 이 맞을 때만 일정을 돌려줍니다.

---

## 1. 준비물

### 하드웨어

| 부품 | 비고 |
|---|---|
| Raspberry Pi Pico 2 W | Wi-Fi 가 있는 **W** 모델. 헤더 핀이 납땜된 것(Pico 2 WH)이면 편함 |
| Waveshare Pico-ePaper-7.5 | 7.5인치 흑백 800×480, Pico 를 바로 꽂는 드라이버 보드 + KEY0/KEY1 버튼 포함 |
| USB 케이블 | 데이터 전송이 되는 케이블 (충전 전용 케이블은 PC 에서 인식 안 됨) |
| 케이스 (선택) | `3d_models/` 의 STL 파일을 3D 프린터로 출력 |

드라이버 보드에 Pico 를 꽂기만 하면 되므로 따로 배선할 필요가 없습니다.
이 프로젝트가 쓰는 핀은 다음과 같습니다 (보드에 이미 연결되어 있음).

| 기능 | Pico 핀 |
|---|---|
| e-Paper DC / CS / RST / BUSY | GP8 / GP9 / GP12 / GP13 |
| e-Paper SPI (CLK / DIN) | GP10 / GP11 |
| KEY0 / KEY1 버튼 | GP2 / GP3 |

> 보드 버전에 따라 버튼 핀이 다르면 `01_bringup/key_finder.py` 를 실행해서 찾은 뒤
> `app/config.py` 의 `KEY0_PIN`, `KEY1_PIN` 을 바꾸세요.

### 소프트웨어

- [VS Code](https://code.visualstudio.com/) + [MicroPico](https://marketplace.visualstudio.com/items?itemName=paulober.pico-w-go) 확장 (Pico 에 파일 올리기 / 실행)
  - Thonny 를 써도 됩니다.
- [Python 3](https://www.python.org/) + `pip install pillow` (PC 미리보기, 글꼴 변환을 할 때만 필요)
- 구글 계정 (구글 캘린더)

---

## 2. Pico 에 MicroPython 설치

1. [MicroPython 다운로드 페이지](https://micropython.org/download/RPI_PICO2_W/) 에서 **Pico 2 W** 용 최신 `.uf2` 파일을 받습니다.
2. Pico 의 **BOOTSEL** 버튼을 누른 채로 USB 를 PC 에 꽂습니다.
3. `RP2350` 이라는 USB 드라이브가 나타나면 `.uf2` 파일을 끌어다 놓습니다.
4. Pico 가 자동으로 재시작되면 설치 완료입니다.

---

## 3. 코드 받기

```bash
git clone https://github.com/jiu-0317/e_ink_display.git
cd e_ink_display
```

### 폴더 구조

```
app/                  ← Pico 에 올리는 실제 프로그램 (이 폴더만 Pico 에 올라감)
  main.py             ← 전원을 켜면 자동 실행되는 메인 루프
  config.py           ← 동작 설정 (갱신 주기, 버튼 핀, 시간표 범위 등)
  credentials.example.py  ← Wi-Fi / 캘린더 주소 예시 (복사해서 credentials.py 로)
  screens/            ← 월간·주간·오늘 화면 그리기
  gfx/ hw/ net/       ← 그리기, 하드웨어(e-Paper·버튼·시계), 네트워크
  fonts/              ← Pico 용 한글 비트맵 글꼴 (.epf)
  data/mock_events.json  ← 설정 전에 보여 줄 예시 일정
tools/
  apps_script/        ← 구글 캘린더 → JSON 을 내보내는 Apps Script (Code.gs) 와 설치 안내
  preview.py          ← PC 에서 화면을 PNG 로 미리보기
  fontgen/            ← 글꼴 → .epf 변환 도구
3d_models/            ← 케이스 STL
01_bringup/           ← 처음 하드웨어 점검용 테스트 스크립트
```

---

## 4. 먼저 예시 일정으로 화면 확인하기

설정을 하기 전에 하드웨어가 잘 동작하는지부터 확인해 봅니다.

1. VS Code 에서 **`app` 폴더를 엽니다** (`File → Open Folder → app`).
   MicroPico 는 열린 폴더를 기준으로 Pico 에 올리므로, 저장소 최상위가 아니라 `app` 을 열어야 합니다.
2. Pico 를 USB 로 연결하면 아래 상태줄에 `Pico Connected` 가 보입니다.
3. 명령 팔레트(`Ctrl+Shift+P`) → **MicroPico: Upload project to Pico**
4. 업로드가 끝나면 Pico 를 다시 꽂거나 **MicroPico: Reset** → 자동으로 `main.py` 가 실행됩니다.

`credentials.py` 가 없으므로 화면에 **"예시 데이터"** 라고 표시되고, 예시 일정이 보이면 성공입니다.

> 화면이 안 나오면 `01_bringup/` 의 테스트 스크립트로 e-Paper 연결부터 확인해 보세요.

---

## 5. 구글 캘린더 연결

자세한 내용(스크린샷 수준의 단계별 설명)은 **[tools/apps_script/README.md](tools/apps_script/README.md)** 에 있습니다. 요약하면:

1. [script.google.com](https://script.google.com) → **새 프로젝트** → `tools/apps_script/Code.gs` 내용을 붙여 넣기
2. 맨 위 `TOKEN` 에 **나만 아는 긴 무작위 문자열**을 넣기. 예를 들어 PowerShell 에서
   ```powershell
   -join ((48..57)+(65..90)+(97..122) | Get-Random -Count 40 | % {[char]$_})
   ```
3. ⚙ 프로젝트 설정 → 시간대 `(GMT+09:00) 서울`
4. `test` 함수 실행 → 권한 허용 → 실행 로그에 일정이 보이는지 확인
5. **배포 → 새 배포 → 웹 앱**, 실행 사용자 **나**, 액세스 **모든 사용자** → 웹 앱 URL 복사
6. 브라우저에서 `웹앱URL?token=내토큰` 을 열어 `{"events": [...]}` 가 보이는지 확인

> ⚠️ 실제 `TOKEN` 값은 Apps Script 편집기에만 넣고, 저장소의 `Code.gs` 에는 넣지 마세요.
> 토큰이 포함된 주소를 아는 사람은 누구나 내 일정을 볼 수 있습니다.

---

## 6. Wi-Fi 와 캘린더 주소 설정 (`credentials.py`)

예시 파일을 복사해서 실제 값을 채웁니다.

```powershell
copy app\credentials.example.py app\credentials.py     # Windows
```
```bash
cp app/credentials.example.py app/credentials.py       # macOS / Linux
```

```python
WIFI_NETWORKS = [
    ("집_와이파이", "비밀번호"),          # 위에서부터 차례로 시도
    ("학교_와이파이", "비밀번호"),
]

CALENDAR_URL = "https://script.google.com/macros/s/AKfy.../exec?token=내토큰"
```

- Pico 2 W 는 **2.4GHz Wi-Fi 만** 지원합니다. 5GHz 전용 네트워크에는 연결되지 않습니다.
- `credentials.py` 는 `.gitignore` 에 들어 있어서 GitHub 에 올라가지 않습니다. **절대 커밋하지 마세요.**

다시 **Upload project to Pico** → 리셋하면 Wi-Fi 에 연결해서 시각을 맞추고(NTP) 내 일정을 받아옵니다.
동기화 중에는 Pico 의 LED 가 켜집니다.

---

## 7. 사용법

| 버튼 | 짧게 누르기 | 길게 누르기 (1초) |
|---|---|---|
| **KEY0** | 화면 바꾸기 (월간 → 주간 → 오늘) | 오늘로 돌아가기 |
| **KEY1** | 다음 달 / 다음 주 / 다음 날 | 지금 바로 동기화 + 전체 갱신 |

화면 오른쪽 위의 `■□□` 는 지금 어느 화면인지(월간·주간·오늘), 옆의 숫자는 마지막으로 그린 시각입니다.

| 화면 | 갱신 |
|---|---|
| 오늘 | 10분마다 (지금 시각 선 이동, 깜빡임 없는 부분 갱신) |
| 월간 / 주간 | 30분마다 |
| 공통 | 일정이 바뀌거나 자정이 되면 전체 갱신 |

---

## 8. 설정 바꾸기 (`app/config.py`)

자주 바꾸는 값들입니다. 바꾼 뒤에는 다시 Pico 에 업로드하세요.

| 설정 | 기본값 | 설명 |
|---|---|---|
| `SYNC_MIN` | `30` | 구글 캘린더를 다시 받아오는 간격 (분) |
| `TODAY_STYLE` | `"timeline"` | 오늘 화면 형태. `"list"` 로 바꾸면 목록형 |
| `TL_START_H` / `TL_END_H` | `7` / `24` | 시간표에 보이는 시간 범위 |
| `TZ_OFFSET` | `9 * 3600` | 시간대 (한국 = UTC+9) |
| `TODAY_TICK_PARTIAL` | `True` | 부분 갱신이 이상하게 보이면 `False` |
| `KEY0_PIN` / `KEY1_PIN` | `2` / `3` | 버튼 GPIO |

가져올 캘린더(공휴일 캘린더 추가 등)와 기간은 Apps Script 의 `Code.gs` 맨 위에서 바꿉니다.
`Code.gs` 를 고친 뒤에는 **배포 → 배포 관리 → ✏ 수정 → 새 버전 → 배포** 를 해야 반영됩니다
("새 배포" 를 하면 주소가 바뀌니 주의).

---

## 9. 케이스 3D 프린팅

`3d_models/` 폴더의 STL 파일입니다.

| 파일 | 부품 |
|---|---|
| `frame.stl` | 화면 앞쪽 테두리 |
| `display_holder.stl` | e-Paper 패널 / 드라이버 보드를 잡아 주는 부분 |
| `base.stl` | 아래 받침대 (Pico 와 보드가 들어가는 공간) |
| `bottom_plate.stl` | 받침대 바닥 덮개 |
| `botton.stl` | 받침대 앞의 버튼 캡 (KEY0 / KEY1 을 눌러 줌) |

사진 속 케이스는 흰색 필라멘트로 출력하고 작은 나사로 프레임을 고정했습니다.

---

## 10. PC 에서 미리보기 (하드웨어 없이)

Pico 없이도 PC 에서 화면을 PNG 로 볼 수 있습니다. `machine`, `framebuf` 같은 Pico 전용 모듈을
가짜 모듈로 바꾸고, e-Paper 가 받는 데이터를 그대로 해석해서 이미지로 저장합니다.

```bash
pip install pillow
python tools/preview.py app/main.py --keys 0,0,0
```

- `--keys` : 순서대로 누를 버튼. `0` = KEY0 짧게, `1` = KEY1 짧게, `1L` = KEY1 길게
- 결과: `preview_out/main/01_full.png, 02_fast.png ...` 와 전체를 모은 `all.png`
- `--scale 2` 로 확대해서 저장할 수 있습니다.

화면 디자인을 고칠 때 Pico 에 매번 올리지 않고 빠르게 확인할 수 있습니다.

---

## 11. 글꼴 바꾸기 (선택)

`tools/fontgen/src/` 의 글꼴을 Pico 용 `.epf` 비트맵 글꼴로 변환합니다.

```bash
pip install pillow
python tools/fontgen/build_fonts.py
```

결과는 `app/fonts/` 에 저장됩니다. 글꼴 크기나 넣을 문자는 `build_fonts.py` 에서 바꿀 수 있습니다.

---

## 문제 해결

| 증상 | 확인할 것 |
|---|---|
| 화면에 "예시 데이터" 가 계속 보임 | `credentials.py` 가 Pico 에 올라갔는지, `CALENDAR_URL` 에 `여기에` 가 남아 있지 않은지 |
| 화면에 "동기화 실패" | Wi-Fi 가 2.4GHz 인지, 이름/비밀번호가 맞는지. 브라우저로 `웹앱URL?token=...` 이 열리는지 |
| 브라우저에서 `{"error":"forbidden"}` | URL 의 token 과 `Code.gs` 의 `TOKEN` 이 다름 |
| 종일 일정이 하루 밀림 | Apps Script 프로젝트 설정의 시간대가 서울인지 |
| `Code.gs` 를 고쳤는데 그대로임 | 배포 관리에서 **새 버전** 으로 다시 배포했는지 |
| 화면에 잔상이 남음 | KEY1 길게 눌러서 전체 갱신. 자주 그러면 `config.py` 의 `PARTIALS_BEFORE_FULL` 을 줄이기 |
| 갑자기 멈췄다가 다시 시작됨 | 오류가 나면 30초 뒤 자동 재시작합니다. Pico 의 `error.log` 에 원인이 남습니다 |
| Pico 가 PC 에서 인식 안 됨 | 데이터 전송이 되는 USB 케이블인지 |

---

## 라이선스 / 출처

- e-Paper 드라이버(`epd7in5.py`)는 [Waveshare](https://www.waveshare.com/wiki/Pico-ePaper-7.5) 예제 코드를 수정한 것입니다 (원본 라이선스는 파일 머리말 참고).
- 글꼴: Pretendard (Kil Hyung-jin), Galmuri11 (Lee Minseo), Neo둥근모 (Dalgona) — 모두 SIL Open Font License 1.1.
  자세한 내용은 [app/fonts/FONTS_LICENSE.txt](app/fonts/FONTS_LICENSE.txt).
