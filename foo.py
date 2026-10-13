"""画像を読み込んで detectAndDecodeMulti をかけるスクリプトです。

nuxt-multiQR-study で opencv.js に detectAndDecodeMulti が無いことに失望して
Python へやってきました。最初は「detectAndDecodeMulti の検出精度がとても低い」と
感じていましたが、baz.py で二値化するとちゃんと読めることが分かりました。
"""

import argparse
from pathlib import Path

import cv2

from multiqr import decode_multi, draw_results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="画像から複数の QR コードを読み取ります。")
    parser.add_argument("image", type=Path, help="読み取る画像")
    parser.add_argument("--output", type=Path, help="枠を描いた画像の保存先")
    args = parser.parse_args(argv)

    img = cv2.imread(str(args.image))
    if img is None:
        parser.error(f"画像を読み込めません: {args.image}")

    codes = decode_multi(img)
    if not codes:
        print("QR コードが見つかりませんでした。")
        return 1
    for code in codes:
        print(code.text or "(decode failed)")

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        if not cv2.imwrite(str(args.output), draw_results(img, codes)):
            parser.error(f"画像を保存できません: {args.output}")
        print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
