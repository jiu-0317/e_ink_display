"""Pico용 MicroPython 스크립트를 PC에서 실행해 e-Paper 화면을 PNG로 저장하는 미리보기 도구.

사용법 (프로젝트 폴더에서):
    pip install pillow
    python tools/preview.py 01_bringup/phase1_test.py
    python tools/preview.py 01_bringup/phase1_xfer_test.py --scale 2

결과: preview_out/<스크립트이름>/01_full.png, 02_fast.png ... 와 전체를 모은 all.png

동작 방식:
  - machine / utime / framebuf / micropython 을 tools/pc_sim 의 가짜 모듈로 바꿔서
    스크립트와 드라이버(epd7in5.py)를 수정 없이 그대로 실행한다.
  - 드라이버가 SPI로 보내는 명령·데이터를 컨트롤러 에뮬레이터가 해석해서,
    갱신 명령이 올 때마다 화면 RAM 내용을 PNG로 저장한다.
    → 실제 패널이 받는 데이터 그대로라서, 반전·전송 순서 실수도 PNG에 드러난다.
  - 버튼은 --keys 순서대로 자동으로 눌린다. 키를 다 쓰면 스크립트를 멈춘다.
  - sleep 은 기다리지 않으므로 미리보기에서 찍히는 ms 측정값은 의미 없다.
"""
import argparse
import builtins
import gc
import os
import runpy
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SIM_DIR = os.path.join(HERE, "pc_sim")


def contact_sheet(frames, path):
    from PIL import Image, ImageDraw
    if not frames:
        return
    ims = [(Image.open(p).convert("L"), label) for p, label in frames]
    w, h = ims[0][0].size
    cols = 2 if len(ims) > 1 else 1
    rows = (len(ims) + cols - 1) // cols
    pad, lab = 12, 20
    sheet = Image.new("L", (cols * (w + pad) + pad, rows * (h + pad + lab) + pad), 150)
    d = ImageDraw.Draw(sheet)
    for k, (im, label) in enumerate(ims):
        x = pad + (k % cols) * (w + pad)
        y = pad + (k // cols) * (h + pad + lab)
        d.text((x, y), label, fill=0)
        sheet.paste(im, (x, y + lab))
    sheet.save(path)


def main():
    ap = argparse.ArgumentParser(description="e-Paper 화면 PNG 미리보기")
    ap.add_argument("script", help="실행할 MicroPython 스크립트 (.py)")
    ap.add_argument("--keys", default="0,0,0,0,0,0,0,0,1L",
                    help="자동으로 누를 버튼 순서. 0=KEY0, 1=KEY1, 뒤에 L=길게 (기본: %(default)s)")
    ap.add_argument("--out", default=None, help="출력 폴더 (기본: preview_out/<스크립트이름>)")
    ap.add_argument("--scale", type=int, default=1, help="PNG 확대 배율 (기본 1 = 800x480)")
    args = ap.parse_args()

    script = os.path.abspath(args.script)
    name = os.path.splitext(os.path.basename(script))[0]
    out_dir = args.out or os.path.join(os.getcwd(), "preview_out", name)

    # 가짜 모듈이 먼저 잡히도록 경로 설정: pc_sim → 스크립트 폴더
    sys.path.insert(0, os.path.dirname(script))
    sys.path.insert(0, SIM_DIR)

    # MicroPython 전용 이름들
    gc.mem_free = lambda: 400 * 1024          # 가짜 값
    gc.mem_alloc = lambda: 0
    os.statvfs = lambda p: (4096, 4096, 0, 0, 0, 0, 0, 0, 0, 255)   # 가짜 값 (flash free = 0)
    for n in ("ptr", "ptr8", "ptr16", "ptr32"):
        setattr(builtins, n, lambda x: x)
    builtins.uint = int

    # MicroPython 의 bytearray([..]) 는 범위를 넘는 정수(예: ~0x12 = -19)를 하위 8비트로 잘라 저장한다.
    # 원래 드라이버가 이 동작에 기대고 있어서 PC에서도 똑같이 맞춰 준다.
    class _MPBytearray(bytearray):
        def __init__(self, src=0, *a):
            if isinstance(src, (list, tuple)):
                src = [v & 0xFF for v in src]
            super().__init__(src, *a)
    builtins.bytearray = _MPBytearray

    import epaper_emu
    import machine
    epaper_emu.EMU = epaper_emu.EPaperEmu(out_dir, args.scale)
    machine.KEYS = machine.KeyScript(args.keys)

    # 이전 결과 PNG 지우기
    if os.path.isdir(out_dir):
        for f in os.listdir(out_dir):
            if f.endswith(".png"):
                os.remove(os.path.join(out_dir, f))

    print("[PREVIEW] 실행:", script)
    print("[PREVIEW] 출력:", out_dir)
    print("-" * 60)
    # Pico 에서는 프로젝트 폴더가 파일시스템의 루트(/)이므로, 스크립트 폴더를 현재 폴더로
    os.chdir(os.path.dirname(script))
    try:
        runpy.run_path(script, run_name="__main__")
    except SystemExit as e:
        if e.code not in (None, 0):
            print(e.code)
    except KeyboardInterrupt:
        print("[PREVIEW] 중단됨")
    print("-" * 60)

    emu = epaper_emu.EMU
    contact_sheet(emu.frames, os.path.join(out_dir, "all.png"))
    print("[PREVIEW] 화면 갱신 %d회 → %s" % (len(emu.frames), out_dir))
    if emu.frames:
        print("[PREVIEW] 한눈에 보기:", os.path.join(out_dir, "all.png"))
    if not emu.asleep:
        print("[PREVIEW 경고] 스크립트가 e-Paper를 sleep 시키지 않고 끝남 (실제 화면이면 고전압 상태 유지)")
    for w in emu.warnings:
        print("[PREVIEW 경고]", w)


if __name__ == "__main__":
    main()
