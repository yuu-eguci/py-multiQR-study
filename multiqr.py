"""foo.py / bar.py / baz.py が共通で使う、QR コードの読み取りと描画の処理です。"""

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


def format_texts(codes: list[QRCode]) -> str:
    return ", ".join(code.text or "(decode failed)" for code in codes)


def parse_source(value: str) -> int | str:
    """数字だけならカメラ番号、それ以外は動画ファイルのパスとして扱います。"""
    return int(value) if value.isdigit() else value


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
