"""
https://tech-blog.optim.co.jp/entry/2020/12/15/100000
……より。
このスクリプトは カメラ + 二値化の程度をコントロール可能 ……とすごいぞ。
foo.py と bar.py で、 opencv の detectAndDecodeMulti が精度悪いとノートしてしまったが、
それは違うということが分かった。

- 二値化すると読みやすくなる
- 連結 QR コードはそもそも detectAndDecodeMulti では読めない
    - 単一の QR コードならちゃんと読める
"""

import argparse
from pathlib import Path

import cv2
import numpy as np


def command():
    parser = argparse.ArgumentParser(description='QRコードの複数同時検出デモ')
    parser.add_argument(
        '--video', default=0,
        help='Video入力 [default: 0]'
    )
    parser.add_argument(
        '--wait_time', type=int, default=2,
        help='cv2.waitKey() [default: 2]'
    )
    parser.add_argument(
        '--out_dir', default=Path().cwd() / 'out' / 'video',
        help='frame保存場所 [default: ./out/video]'
    )
    parser.add_argument(
        '--save_frame', action='store_true',
        help='frame保存モード'
    )
    args = parser.parse_args()
    return args


class QRCodeReader(object):

    def __init__(self):
        self.qr = cv2.QRCodeDetector()
        self._img = None

    def __call__(self, img, thresh=80, max_val=255):
        # 二値化して、QRコードの検出
        binary = self._cvt_bgr2binary(img, thresh)
        ret, *data = self.qr.detectAndDecodeMulti(binary)
        # 見やすくするためにnormalizeして、描画用の画像を準備する
        cv2.normalize(binary, binary, 100, max_val, cv2.NORM_MINMAX)
        self._img = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
        self._write_txt(f'thresh: {thresh:3}', (10, 30))

        # QRコードの未検出
        if not ret:
            return self

        # QRコードの描画
        diff = max_val // len(data[0])
        for i, (txt, pts, straight_qrcode) in enumerate(zip(*data)):
            print(f'Original TXT: {txt}')
            color = self._apply_color_map(diff * i)
            rslt = self._draw_qr(txt, pts, straight_qrcode.shape[0], color)
            print(i, rslt)

        return self

    @property
    def img(self):
        return self._img

    def _cvt_bgr2binary(self, img, thresh, max_val=255, flg=cv2.THRESH_BINARY):
        if thresh < 0:
            thresh = 0
        elif thresh > max_val:
            thresh = max_val

        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        img = cv2.threshold(img, thresh, max_val, flg)[1]
        return img

    def _apply_color_map(self, val):
        bk = np.zeros((1, 1), dtype=np.uint8)
        bk.fill(val)
        return tuple([
            int(c) for c in cv2.split(cv2.applyColorMap(bk, cv2.COLORMAP_JET))
        ])

    def _write_txt(
        self, txt, pts, color=(0, 0, 0),
        font_face=cv2.FONT_HERSHEY_PLAIN,
        font_scale=2, font_thick=2, line_type=cv2.LINE_8
    ):
        cv2.putText(
            self._img, txt, pts,
            font_face, font_scale, color, font_thick, line_type
        )

    def _draw_qr(
        self, txt, pts, option='', color=(0, 0, 255),
        line_thick=5, line_type=cv2.LINE_8, line_shift=0
    ):
        pts = pts.astype(np.int32)
        cv2.polylines(
            self._img, [pts], True, color,
            thickness=line_thick, lineType=line_type, shift=line_shift
        )

        txt = txt.replace('https://', '')
        out_txt = 'txt not found' if txt == '' else f'{txt[:20]}({option})'
        self._write_txt(out_txt, (pts[0][0], pts[0][1] - 10), color)
        return f'{out_txt},{color}'


def main(args):
    print(args)
    # カメラ設定
    cap = cv2.VideoCapture(args.video)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) * 0.5)
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) * 0.5)
    print(
        f'Display size ({w}, {h})\n',
        'Key\n',
        '  [q]: Exit\n',
        '  [a]: Thresh += 5\n',
        '  [z]: Thresh -= 5'
    )

    # 保存ディレクトリの作成
    if not args.out_dir.exists():
        args.out_dir.mkdir(parents=True)

    # カメラ読込み開始
    qr = QRCodeReader()
    cnt = 0
    thresh = 80
    while True:
        # ビデオキャプチャ
        ret, frame = cap.read()
        if not ret:
            print('[Error] camera frame not found')
            break

        # QRコードを検出して、検出結果を描画する
        dst = qr(frame, thresh).img
        # frameに検出結果を連結する
        frame = cv2.resize(np.hstack([frame, dst]), (w * 2, h))
        # 可視化
        cv2.imshow('Camera frame', frame)
        # キーボード入力受付
        key = cv2.waitKey(100 if ret else args.wait_time)
        if key == ord('q'):
            break
        elif key == ord('a'):
            thresh += 5
            print(f'Thresh: {thresh}')
        elif key == ord('z'):
            thresh -= 5
            print(f'Thresh: {thresh}')

        # 保存
        if args.save_frame:
            cnt += 1
            save_path = args.out_dir / f'frame_{cnt:04}.png'
            cv2.imwrite(save_path.as_posix(), frame)

    cap.release()
    return 0


if __name__ == '__main__':
    exit(main(command()))
