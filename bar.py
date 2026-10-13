"""foo.py と同じく detectAndDecodeMulti をかけるスクリプトですが、こちらはカメラ映像を読みます。

--video に動画ファイルを渡すとカメラの代わりに使えます。
"""

import argparse
import sys

import cv2

from multiqr import (
    WindowUnavailableError,
    decode_multi,
    draw_results,
    format_texts,
    open_capture,
    show,
)

WINDOW_NAME = "OpenCV QR Code"


def run(capture, show_window: bool = True, delay_ms: int = 1) -> int:
    """フレームが読めなくなるか q キーが押されるまで読み取り、処理したフレーム数を返します。"""
    detector = cv2.QRCodeDetector()
    count = 0
    while True:
        ok, frame = capture.read()
        if not ok:
            break
        count += 1
        codes = decode_multi(frame, detector)
        if codes:
            print(f"frame {count:04}: {format_texts(codes)}")
        if show_window and show(WINDOW_NAME, draw_results(frame, codes), delay_ms) == ord("q"):
            break
    if show_window and count:
        cv2.destroyWindow(WINDOW_NAME)
    return count


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="カメラ映像から複数の QR コードを読み取ります。")
    parser.add_argument("--video", default="0", help="カメラ番号か動画ファイル [default: 0]")
    parser.add_argument("--no-window", action="store_true", help="ウィンドウを出さずに読み取ります")
    args = parser.parse_args(argv)

    capture = open_capture(args.video)
    if capture is None:
        print(f"カメラまたは動画を開けません: {args.video}", file=sys.stderr)
        return 1
    try:
        run(capture, show_window=not args.no_window)
    except WindowUnavailableError as e:
        print(e, file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        pass
    finally:
        capture.release()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
