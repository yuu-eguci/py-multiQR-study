"""画像を読み込んで detectAndDecodeMulti をかけるスクリプトです。"""

import argparse
import sys
from pathlib import Path

from multiqr import (
    ImageWriteError,
    decode_multi,
    draw_results,
    format_text,
    read_image,
    write_image,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="画像から複数の QR コードを読み取ります。")
    parser.add_argument("image", type=Path, help="読み取る画像")
    parser.add_argument("--output", type=Path, help="枠を描いた画像の保存先")
    args = parser.parse_args(argv)

    img = read_image(args.image)
    if img is None:
        parser.error(f"画像を読み込めません: {args.image}")
    if args.output and args.output.exists() and args.output.samefile(args.image):
        parser.error(f"--output に入力画像と同じファイルは指定できません: {args.output}")

    codes = decode_multi(img)
    if not codes:
        print("QR コードが見つかりませんでした。")
        return 1
    for code in codes:
        print(format_text(code))

    if args.output:
        try:
            write_image(args.output, draw_results(img, codes))
        except ImageWriteError as e:
            print(e, file=sys.stderr)
            return 1
        print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
