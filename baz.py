"""カメラ映像を二値化してから detectAndDecodeMulti をかけるスクリプトです。

https://tech-blog.optim.co.jp/entry/2020/12/15/100000 のコードを元にしています。
"""

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np

from multiqr import (
    ImageWriteError,
    QRCode,
    WindowUnavailableError,
    decode_multi,
    draw_results,
    format_texts,
    open_capture,
    show,
    write_image,
)

WINDOW_NAME = "Camera frame"
MAX_VAL = 255


class QRCodeReader:
    """二値化した画像から QR コードを読み取り、描画用の画像も作ります。"""

    def __init__(self):
        self.detector = cv2.QRCodeDetector()
        self._img = None

    def __call__(self, img: np.ndarray, thresh: int = 80) -> list[QRCode]:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        binary = cv2.threshold(gray, thresh, MAX_VAL, cv2.THRESH_BINARY)[1]
        codes = decode_multi(binary, self.detector)

        # 枠が見やすいように、白黒を少し薄くしてから描画します。
        display = cv2.normalize(binary, None, 100, MAX_VAL, cv2.NORM_MINMAX)
        self._img = draw_results(display, codes)
        cv2.putText(
            self._img, f"thresh: {thresh:3}", (10, 30), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 0), 2
        )
        return codes

    @property
    def img(self) -> np.ndarray | None:
        return self._img


def run(capture, thresh: int = 80, show_window: bool = True, save_dir: Path | None = None) -> int:
    """フレームが読めなくなるか q キーが押されるまで読み取り、処理したフレーム数を返します。"""
    reader = QRCodeReader()
    count = 0
    while True:
        ok, frame = capture.read()
        if not ok:
            break
        count += 1
        codes = reader(frame, thresh)
        if codes:
            print(f"frame {count:04} (thresh {thresh}): {format_texts(codes)}")

        combined = np.hstack([frame, reader.img])
        if save_dir is not None:
            write_image(save_dir / f"frame_{count:04}.png", combined)
        if not show_window:
            continue

        h, w = combined.shape[:2]
        key = show(WINDOW_NAME, cv2.resize(combined, (w // 2, h // 2)), 100)
        if key == ord("q"):
            break
        if key in (ord("a"), ord("z")):
            thresh = min(max(thresh + (5 if key == ord("a") else -5), 0), MAX_VAL)
            print(f"thresh: {thresh}")
    if show_window and count:
        cv2.destroyWindow(WINDOW_NAME)
    return count


def threshold(value: str) -> int:
    thresh = int(value)
    if not 0 <= thresh <= MAX_VAL:
        raise argparse.ArgumentTypeError(f"0 から {MAX_VAL} の整数を指定してください: {value}")
    return thresh


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="QRコードの複数同時検出デモ")
    parser.add_argument("--video", default="0", help="カメラ番号か動画ファイル [default: 0]")
    parser.add_argument(
        "--thresh", type=threshold, default=80, help="二値化のしきい値 0-255 [default: 80]"
    )
    parser.add_argument(
        "--out-dir",
        "--out_dir",
        type=Path,
        default=Path("out/video"),
        help="フレームの保存先 [default: out/video]",
    )
    parser.add_argument(
        "--save-frame", "--save_frame", action="store_true", help="フレームを保存します"
    )
    parser.add_argument("--no-window", action="store_true", help="ウィンドウを出さずに読み取ります")
    args = parser.parse_args(argv)

    capture = open_capture(args.video)
    if capture is None:
        print(f"カメラまたは動画を開けません: {args.video}", file=sys.stderr)
        return 1
    if not args.no_window:
        print("Key\n  [q]: Exit\n  [a]: Thresh += 5\n  [z]: Thresh -= 5")

    try:
        run(
            capture,
            thresh=args.thresh,
            show_window=not args.no_window,
            save_dir=args.out_dir if args.save_frame else None,
        )
    except WindowUnavailableError as e:
        print(e, file=sys.stderr)
        return 1
    except ImageWriteError as e:
        print(f"{e}\n--out-dir に書き込めるフォルダを指定してください。", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        pass
    finally:
        capture.release()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
