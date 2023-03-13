"""
pipenv install --python 3.11
pipenv install opencv-python

foo.py と同様に画像に detectAndDecodeMulti をかけるスクリプトだけど、
こっちは VideoCapture でカメラを起動する。
でもやっぱり foo.py と同じように検出精度がめっちゃくちゃ低い。
"""

import cv2

camera_id = 0
delay = 1
window_name = 'OpenCV QR Code'

detector = cv2.QRCodeDetector()
video_capture = cv2.VideoCapture(camera_id)

while True:
    ret, frame = video_capture.read()

    if ret:
        ret_qr, decoded_info, points, _ = detector.detectAndDecodeMulti(frame)
        if ret_qr:
            for s, p in zip(decoded_info, points):
                if s:
                    print(s)
                    color = (0, 255, 0)
                else:
                    color = (0, 0, 255)
                frame = cv2.polylines(frame, [p.astype(int)], True, color, 8)
        cv2.imshow(window_name, frame)

    if cv2.waitKey(delay) & 0xFF == ord('q'):
        break

cv2.destroyWindow(window_name)
