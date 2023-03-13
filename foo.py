"""
pipenv install --python 3.11
pipenv install opencv-python

QR コードの画像を imread して、
それを detectAndDecodeMulti するスクリプト。

nuxt-multiQR-study で detectAndDecodeMulti が使えないことに失望して
Python へやってきたのだが、
なんか detectAndDecodeMulti の検出精度がめっちゃくちゃ低いので使い物にならない感。
"""

from numpy import ndarray
import cv2

mat: ndarray = cv2.imread('/Users/user/Desktop/sample.png', cv2.IMREAD_GRAYSCALE)
assert mat is not None, 'ファイルないよ。'

detector: cv2.QRCodeDetector = cv2.QRCodeDetector()

# https://docs.opencv.org/4.x/de/dc3/classcv_1_1QRCodeDetector.html#a188b63ffa17922b2c65d8a0ab7b70775
# tuple[bool, tuple, ndarray, tuple]
# retval: bool 検出成功
# decoded_info: tuple 検出できてもデコードできないときは ''
# points: ndarray QR の四隅の座標
retval, decoded_info, points, straight_qrcode = \
    detector.detectAndDecodeMulti(mat)
if retval:
    # 検出成功
    print(retval, decoded_info)

    img = cv2.polylines(mat, points.astype(int), True, (0, 255, 0), 3)

    for s, p in zip(decoded_info, points):
        img = cv2.putText(img, s, p[0].astype(int),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)

    cv2.imwrite('/Users/user/Desktop/qr_DST.png', img)
