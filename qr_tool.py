# -*- coding: utf-8 -*-
"""
qr_tool.py —— 把网址写进屏的二维码缓冲区，并导出一张可扫描的二维码图
====================================================================

屏上 P05 那个二维码控件，内容来自变量 0x1200 开始的缓冲区：
    22_Config.bin 里对应字节偏移 = 0x1200 × 2 = 0x2400
缓冲区目前开了 64 字节，所以 **网址 + 结束符 必须 ≤ 64 字节**，
也就是网址最多 62 个 ASCII 字符。

用法
----
    python qr_tool.py --url "https://example.com/gutu/01"            # 写入 22 并出图
    python qr_tool.py --url "..." --dry-run                          # 只看长度/出图，不改文件
    python qr_tool.py --url "..." --qr qr.png --dry-run              # 指定输出图名
    python qr_tool.py --url "..." --root "D:\\MyProject\\..."        # 指定工程根目录

写完要烧 **22_Config.bin**，二维码内容才会变（不用动控件）。
"""

import argparse
import os
import shutil
import sys

BUF_VP = 0x1200
BUF_BYTES = 64                      # 0x1200–0x121F
DEFAULT_ROOT = r"D:\MyProject\基于北斗精准时空信息的情感记忆传承系统"


def build_qr(url, out_png):
    try:
        import qrcode
    except ImportError:
        print("（没装 qrcode，跳过出图：pip install \"qrcode[pil]\"）")
        return None
    qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M,
                       box_size=10, border=3)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(out_png)
    return qr.modules_count


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True, help="二维码内容（一般是网址）")
    ap.add_argument("--root", default=DEFAULT_ROOT, help="项目根目录")
    ap.add_argument("--qr", default=None, help="二维码预览图输出路径")
    ap.add_argument("--dry-run", action="store_true", help="只检查长度、出图，不写文件")
    args = ap.parse_args()

    data = args.url.encode("utf-8")
    need = len(data) + 2                    # + 结束符 00 00
    print("内容      : %s" % args.url)
    print("UTF-8 字节 : %d + 2（结束符）= %d / 缓冲区 %d" % (len(data), need, BUF_BYTES))
    if need > BUF_BYTES:
        sys.exit("!! 超了 %d 字节。要么缩短网址，要么把缓冲区扩到 0x1280（需改隐藏文本控件长度）"
                 % (need - BUF_BYTES))

    qr_png = args.qr or os.path.join(os.path.dirname(os.path.abspath(__file__)), "qr_preview.png")
    n = build_qr(args.url, qr_png)
    if n:
        # 屏上单元像素 4 → 成品边长
        print("二维码     : %d×%d 单元，屏上按 4px/单元 = %d×%d 像素" % (n, n, n * 4, n * 4))
        print("预览图     : %s" % qr_png)
        if n > 45:
            print("             ⚠ 超过 45×45，屏上会自动切到 73×73 模式（292×292），"
                  "P05 那 180×180 的框会装不下，建议缩短")

    if args.dry_run:
        print("（--dry-run，未修改 22_Config.bin）")
        return

    cfg = os.path.join(args.root, "DGUS工程文件", "DWIN_SET", "22_Config.bin")
    if not os.path.exists(cfg):
        sys.exit("找不到 %s" % cfg)

    bak = cfg + ".bak"
    if not os.path.exists(bak):
        shutil.copy2(cfg, bak)
        print("已备份原 22 → %s" % os.path.basename(bak))

    with open(cfg, "r+b") as f:
        f.seek(BUF_VP * 2)
        buf = data + b"\x00\x00"
        buf += b"\x00" * (BUF_BYTES - len(buf))
        f.write(buf)

    print("已写入 %s 的 0x%04X（文件偏移 0x%04X），%d 字节" % (
        os.path.basename(cfg), BUF_VP, BUF_VP * 2, BUF_BYTES))
    print("→ 烧 22_Config.bin 后，P05 的二维码内容就变了（控件不用动）")


if __name__ == "__main__":
    main()
