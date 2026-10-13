"""foo.py / bar.py / baz.py が共通で使う、QR コードの読み取りと描画の処理です。"""

from pathlib import Path
from typing import NamedTuple

import cv2
import numpy as np

DECODED_COLOR = (0, 255, 0)
FAILED_COLOR = (0, 0, 255)


class QRCode(NamedTuple):
    """読み取った QR コード1つ分です。デコードできなかったときの text は空文字です。"""

    text: str
    points: np.ndarray


class WindowUnavailableError(RuntimeError):
    """GUI なしの OpenCV でウィンドウを出そうとしたときのエラーです。"""


class ImageWriteError(RuntimeError):
    """画像や動画を保存できなかったときのエラーです。"""


def decode_multi(img: np.ndarray, detector: cv2.QRCodeDetector | None = None) -> list[QRCode]:
    """画像中の QR コードをすべて読み取り、左にあるものから順に返します。"""
    detector = detector or cv2.QRCodeDetector()
    found, texts, points, _ = detector.detectAndDecodeMulti(img)
    if not found:
        return []
    codes = [QRCode(text, pts) for text, pts in zip(texts, points, strict=True)]
    return sorted(codes, key=lambda code: (code.points[:, 0].min(), code.points[:, 1].min()))


def draw_results(img: np.ndarray, codes: list[QRCode], thickness: int = 8) -> np.ndarray:
    """読めた QR を緑、読めなかった QR を赤で囲んだカラー画像を返します。元の画像は変更しません。"""
    canvas = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR) if img.ndim == 2 else img.copy()
    for code in codes:
        pts = code.points.astype(np.int32)
        color = DECODED_COLOR if code.text else FAILED_COLOR
        cv2.polylines(canvas, [pts], True, color, thickness)
        if code.text:
            x, y = pts[0]
            org = (int(x), int(y) - 10)
            cv2.putText(canvas, code.text, org, cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2, cv2.LINE_AA)
    return canvas


def format_text(code: QRCode) -> str:
    """端末に表示する文字列を返します。

    制御文字などの表示できない文字は \\x1b や \\n のようにエスケープするので、
    QR コードの中身で端末の表示が乱れたり、1行1コードの出力が崩れたりしません。
    """
    if not code.text:
        return "(decode failed)"
    return "".join(
        c if c.isprintable() else c.encode("unicode_escape").decode("ascii") for c in code.text
    )


def format_texts(codes: list[QRCode]) -> str:
    return ", ".join(format_text(code) for code in codes)


def read_image(path: Path) -> np.ndarray | None:
    """画像を BGR で読み込みます。読み込めないときは None を返します。

    透過のある 8bit 画像は、白い背景に重ねてから返します。
    透明な部分が黒として扱われて QR コードが見えなくなるのを防ぐためです。
    """
    try:
        img = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
        if img is None or img.ndim != 3 or img.shape[2] != 4 or img.dtype != np.uint8:
            return None if img is None else cv2.imread(str(path))
    except cv2.error:
        # OPENCV_IO_MAX_IMAGE_PIXELS を超える大きな画像などです。
        return None
    alpha = img[:, :, 3:].astype(np.uint16)
    return ((img[:, :, :3] * alpha + 255 * (255 - alpha)) // 255).astype(np.uint8)


def write_image(path: Path, img: np.ndarray) -> None:
    """画像を保存します。保存先のフォルダが無ければ作ります。

    保存できなかったときは ImageWriteError を送出します。
    """
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        ok = cv2.imwrite(str(path), img)
    except OSError as e:
        raise ImageWriteError(f"画像を保存できません: {path} ({e.strerror})") from e
    except cv2.error as e:
        raise ImageWriteError(f"画像を保存できません(対応していない拡張子です): {path}") from e
    if not ok:
        raise ImageWriteError(f"画像を保存できません: {path}")


def parse_source(value: str) -> int | str:
    """半角数字だけならカメラ番号、それ以外は動画ファイルのパスとして扱います。"""
    return int(value) if value.isascii() and value.isdigit() else value


def open_capture(value: str) -> cv2.VideoCapture | None:
    capture = cv2.VideoCapture(parse_source(value))
    if not capture.isOpened():
        capture.release()
        return None
    return capture


def show(window_name: str, img: np.ndarray, delay_ms: int) -> int:
    """画像をウィンドウに出し、押されたキーのコードを返します。"""
    try:
        cv2.imshow(window_name, img)
    except cv2.error as e:
        if "not implemented" not in str(e):
            raise
        raise WindowUnavailableError(
            "この OpenCV ではウィンドウを表示できません。--no-window を付けて実行してください。"
        ) from e
    return cv2.waitKey(delay_ms) & 0xFF
