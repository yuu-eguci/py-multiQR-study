"""cv2.QRCodeEncoder で、QR コードが3つ並んだサンプル画像と短い動画を作ります。"""

import argparse
from pathlib import Path

import cv2
import numpy as np

SAMPLE_TEXTS = ("hello-1", "hello-2", "テスト3")
WIDTH, HEIGHT = 1200, 480
QR_SIZE = 240
VIDEO_FRAMES = 12
VIDEO_FPS = 6


def make_qr(text: str, size: int = QR_SIZE) -> np.ndarray:
    qr = cv2.QRCodeEncoder.create().encode(text)
    qr = cv2.resize(qr, (size, size), interpolation=cv2.INTER_NEAREST)
    return cv2.cvtColor(qr, cv2.COLOR_GRAY2BGR)


def make_sample_image(offset: int = 0, texts: tuple[str, ...] = SAMPLE_TEXTS) -> np.ndarray:
    """白い画像に QR コードを横に並べます。offset を変えると少しずつ位置がずれます。"""
    canvas = np.full((HEIGHT, WIDTH, 3), 255, np.uint8)
    step = WIDTH // len(texts)
    for i, text in enumerate(texts):
        x = i * step + (step - QR_SIZE) // 2 + offset
        y = (HEIGHT - QR_SIZE) // 2 + (offset if i % 2 else -offset)
        canvas[y : y + QR_SIZE, x : x + QR_SIZE] = make_qr(text)
    return canvas


def write_sample_video(path: Path) -> None:
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"MJPG"), VIDEO_FPS, (WIDTH, HEIGHT))
    try:
        for i in range(VIDEO_FRAMES):
            writer.write(make_sample_image(offset=i * 3))
    finally:
        writer.release()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="サンプルの QR 画像と動画を作ります。")
    parser.add_argument("--out-dir", type=Path, default=Path("out"), help="保存先 [default: out]")
    args = parser.parse_args(argv)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    image_path = args.out_dir / "sample.png"
    video_path = args.out_dir / "sample.avi"
    cv2.imwrite(str(image_path), make_sample_image())
    print(f"wrote {image_path}")
    write_sample_video(video_path)
    print(f"wrote {video_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
