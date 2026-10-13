import numpy as np

import make_samples
import multiqr


def test_decode_multi_reads_all_codes_left_to_right(sample_image):
    codes = multiqr.decode_multi(sample_image)

    assert [c.text for c in codes] == list(make_samples.SAMPLE_TEXTS)
    assert all(c.points.shape == (4, 2) for c in codes)


def test_decode_multi_accepts_grayscale(sample_image):
    gray = make_samples.cv2.cvtColor(sample_image, make_samples.cv2.COLOR_BGR2GRAY)

    assert [c.text for c in multiqr.decode_multi(gray)] == list(make_samples.SAMPLE_TEXTS)


def test_decode_multi_returns_empty_list_without_qr():
    blank = np.full((200, 200, 3), 255, np.uint8)

    assert multiqr.decode_multi(blank) == []


def test_draw_results_returns_annotated_copy(sample_image):
    original = sample_image.copy()
    codes = multiqr.decode_multi(sample_image)

    drawn = multiqr.draw_results(sample_image, codes)

    assert drawn.shape == sample_image.shape
    assert not np.array_equal(drawn, sample_image)
    assert np.array_equal(sample_image, original)
    x, y = codes[0].points[0].astype(int)
    assert tuple(drawn[y, x]) == multiqr.DECODED_COLOR


def test_draw_results_converts_grayscale_to_color(sample_image):
    gray = make_samples.cv2.cvtColor(sample_image, make_samples.cv2.COLOR_BGR2GRAY)

    drawn = multiqr.draw_results(gray, multiqr.decode_multi(gray))

    assert drawn.ndim == 3


def test_parse_source_treats_digits_as_camera_index():
    assert multiqr.parse_source("0") == 0
    assert multiqr.parse_source("2") == 2
    assert multiqr.parse_source("/tmp/sample.avi") == "/tmp/sample.avi"


def test_format_texts():
    codes = [multiqr.QRCode("a", np.zeros((4, 2))), multiqr.QRCode("", np.zeros((4, 2)))]

    assert multiqr.format_texts(codes) == "a, (decode failed)"
