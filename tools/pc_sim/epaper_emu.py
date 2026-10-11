# 7.5인치 V2 e-Paper 컨트롤러(UC8179) 간이 에뮬레이터 (미리보기 전용)
# 드라이버가 SPI로 보내는 명령/데이터를 그대로 해석해서 화면 RAM을 재구성하고,
# 갱신 명령(0x12)이 오면 그 순간의 화면을 PNG로 저장한다.
#   - 0x13 데이터 비트 1 = 검정 (드라이버가 버퍼를 반전해서 보내므로)
#   - 0x91/0x90 부분 모드 창, 0x07+0xA5 deep sleep, RST 핀으로 깨우기
import os

W, H = 800, 480
NB = W * H // 8


class EPaperEmu:
    def __init__(self, out_dir, scale=1):
        self.out_dir = out_dir
        self.scale = scale
        os.makedirs(out_dir, exist_ok=True)
        self.ram_new = bytearray(NB)          # 0x13 (화면 기준). 0 = 흰색
        self.ram_old = bytearray(NB)          # 0x10
        self.dc = 1
        self.cs = 1
        self.cmd = None
        self.args = []
        self.ptr = 0
        self.partial = False
        self.win = (0, 0, W, H)               # x0, y0, x1, y1 (끝은 제외)
        self.asleep = False
        self.mode = "full"                    # 마지막 init 종류
        self.refresh_no = 0
        self.bytes_since_refresh = 0
        self.frames = []                      # (파일 경로, 라벨)
        self.warnings = []

    # ------------------------------------------------ 핀 이벤트
    def on_reset(self):
        self.asleep = False
        self.partial = False

    def on_spi(self, data):
        if self.cs != 0:
            return
        if self.asleep:
            self.warn("deep sleep 중에 SPI 전송 — init(리셋) 없이 보낸 데이터는 무시됨")
            return
        self.bytes_since_refresh += len(data)
        if self.dc == 0:
            for b in data:
                self._command(b)
        else:
            self._data(data)

    # ------------------------------------------------ 해석
    def _command(self, c):
        self.cmd = c
        self.args = []
        self.ptr = 0
        if c == 0x01:
            self.mode = "full"
        elif c == 0x91:
            self.partial = True
        elif c == 0x92:
            self.partial = False
        elif c == 0x12:
            self._refresh()

    def _data(self, data):
        c = self.cmd
        if c in (0x10, 0x13):
            ram = self.ram_new if c == 0x13 else self.ram_old
            if self.partial:
                x0, y0, x1, y1 = self.win
                wb = (x1 - x0) // 8
                for b in data:
                    r, col = divmod(self.ptr, wb)
                    if r < (y1 - y0):
                        ram[(y0 + r) * (W // 8) + x0 // 8 + col] = b
                    self.ptr += 1
            else:
                n = min(len(data), NB - self.ptr)
                ram[self.ptr:self.ptr + n] = bytes(data[:n])
                self.ptr += len(data)
        else:
            self.args.extend(data)
            if c == 0x90 and len(self.args) >= 8:
                a = self.args
                x0 = a[0] * 256 + a[1]
                x1 = a[2] * 256 + a[3] + 1
                y0 = a[4] * 256 + a[5]
                y1 = a[6] * 256 + a[7] + 1
                self.win = (x0, y0, x1, y1)
            elif c == 0xE5 and len(self.args) == 1:
                self.mode = {0x5A: "fast", 0x6E: "partial", 0x5F: "gray4"}.get(self.args[0], self.mode)
            elif c == 0x07 and self.args[:1] == [0xA5]:
                self.asleep = True

    def _refresh(self):
        from PIL import Image
        self.refresh_no += 1
        label = "partial" if self.partial else self.mode
        img = Image.new("1", (W, H), 1)
        px = img.load()
        for y in range(H):
            row = y * (W // 8)
            for xb in range(W // 8):
                b = self.ram_new[row + xb]
                if b:
                    for k in range(8):
                        if b & (0x80 >> k):
                            px[xb * 8 + k, y] = 0
        if self.scale != 1:
            img = img.resize((W * self.scale, H * self.scale), Image.NEAREST)
        path = os.path.join(self.out_dir, "%02d_%s.png" % (self.refresh_no, label))
        img.save(path)
        self.frames.append((path, "#%d %s" % (self.refresh_no, label)))
        print("[PREVIEW] 갱신 #%d (%s) → %s   SPI %d bytes" %
              (self.refresh_no, label, path, self.bytes_since_refresh))
        self.bytes_since_refresh = 0

    def warn(self, msg):
        if msg not in self.warnings:
            self.warnings.append(msg)
            print("[PREVIEW 경고]", msg)


EMU = None      # preview.py 가 생성해서 넣음
