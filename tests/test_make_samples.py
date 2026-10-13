import cv2

import make_samples


def test_main_writes_image_and_video(sample_files, capsys):
    image_path, video_path = sample_files

    image = cv2.imread(str(image_path))
    assert image is not None
    assert image.shape == (make_samples.HEIGHT, make_samples.WIDTH, 3)

    capture = cv2.VideoCapture(str(video_path))
    frames = 0
    while capture.read()[0]:
        frames += 1
    capture.release()
    assert frames == make_samples.VIDEO_FRAMES


def test_sample_image_moves_with_offset():
    assert not (make_samples.make_sample_image(0) == make_samples.make_sample_image(10)).all()
