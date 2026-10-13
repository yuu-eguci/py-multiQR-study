import cv2
import numpy as np
import pytest

import make_samples
import multiqr


def damaged_sample(image):
    """真ん中の QR コードの中央を白く塗り、検出はできてもデコードできない画像にします。"""
    damaged = image.copy()
    damaged[220:260, 580:620] = 255
    return damaged


def test_decode_multi_reads_all_codes_left_to_right(sample_image):
    codes = multiqr.decode_multi(sample_image)

    assert [c.text for c in codes] == list(make_samples.SAMPLE_TEXTS)
    assert all(c.points.shape == (4, 2) for c in codes)


def test_decode_multi_accepts_grayscale(sample_image):
    gray = cv2.cvtColor(sample_image, cv2.COLOR_BGR2GRAY)

    assert [c.text for c in multiqr.decode_multi(gray)] == list(make_samples.SAMPLE_TEXTS)


def test_decode_multi_returns_empty_list_without_qr():
    blank = np.full((200, 200, 3), 255, np.uint8)

    assert multiqr.decode_multi(blank) == []


def test_decode_multi_keeps_detected_but_undecoded_code(sample_image):
    codes = multiqr.decode_multi(damaged_sample(sample_image))

    assert [c.text for c in codes] == ["hello-1", "", "テスト3"]
    assert multiqr.format_texts(codes) == "hello-1, (decode failed), テスト3"


def test_draw_results_returns_annotated_copy(sample_image):
    original = sample_image.copy()
    codes = multiqr.decode_multi(sample_image)

    drawn = multiqr.draw_results(sample_image, codes)

    assert drawn.shape == sample_image.shape
    assert not np.array_equal(drawn, sample_image)
    assert np.array_equal(sample_image, original)
    x, y = codes[0].points[0].astype(int)
    assert tuple(drawn[y, x]) == multiqr.DECODED_COLOR


def test_draw_results_marks_undecoded_code_red(sample_image):
    damaged = damaged_sample(sample_image)
    codes = multiqr.decode_multi(damaged)

    drawn = multiqr.draw_results(damaged, codes)

    x, y = codes[1].points[0].astype(int)
    assert tuple(drawn[y, x]) == multiqr.FAILED_COLOR


def test_draw_results_converts_grayscale_to_color(sample_image):
    gray = cv2.cvtColor(sample_image, cv2.COLOR_BGR2GRAY)

    drawn = multiqr.draw_results(gray, multiqr.decode_multi(gray))

    assert drawn.ndim == 3


def test_parse_source_treats_digits_as_camera_index():
    assert multiqr.parse_source("0") == 0
    assert multiqr.parse_source("2") == 2
    assert multiqr.parse_source("/tmp/sample.avi") == "/tmp/sample.avi"


def test_parse_source_treats_non_ascii_digits_as_path():
    assert multiqr.parse_source("²") == "²"
    assert multiqr.parse_source("\u0661") == "\u0661"


def test_format_texts():
    codes = [multiqr.QRCode("a", np.zeros((4, 2))), multiqr.QRCode("", np.zeros((4, 2)))]

    assert multiqr.format_texts(codes) == "a, (decode failed)"


def test_format_texts_escapes_control_characters():
    codes = [multiqr.QRCode("A\x1b[31mRED\x1b[0m\nB", np.zeros((4, 2)))]

    assert multiqr.format_texts(codes) == r"A\x1b[31mRED\x1b[0m\nB"


def test_format_text_keeps_printable_unicode():
    assert multiqr.format_text(multiqr.QRCode("テスト3 ok", np.zeros((4, 2)))) == "テスト3 ok"


def write_transparent_qr(path, text):
    """透明な背景に黒いモジュールだけを描いた PNG を作ります。"""
    qr = make_samples.make_qr(text)[:, :, 0]
    rgba = np.zeros((480, 480, 4), np.uint8)
    rgba[120:360, 120:360, 3] = np.where(qr == 0, 255, 0)
    cv2.imwrite(str(path), rgba)


def test_read_image_puts_transparent_png_on_white(tmp_path):
    path = tmp_path / "alpha.png"
    write_transparent_qr(path, "alpha-1")

    img = multiqr.read_image(path)

    assert img.shape == (480, 480, 3)
    assert tuple(img[0, 0]) == (255, 255, 255)
    assert [c.text for c in multiqr.decode_multi(img)] == ["alpha-1"]


def test_read_image_reads_opaque_image_as_bgr(tmp_path, sample_image):
    path = tmp_path / "sample.png"
    cv2.imwrite(str(path), sample_image)

    assert np.array_equal(multiqr.read_image(path), sample_image)


def test_read_image_returns_none_for_unreadable_file(tmp_path):
    path = tmp_path / "broken.png"
    path.write_bytes(b"not an image")

    assert multiqr.read_image(path) is None
    assert multiqr.read_image(tmp_path / "missing.png") is None


def test_write_image_rejects_unsupported_extension(tmp_path, sample_image):
    with pytest.raises(multiqr.ImageWriteError, match="保存できません"):
        multiqr.write_image(tmp_path / "result.unknown", sample_image)


def test_write_image_reports_failed_write(monkeypatch, tmp_path, sample_image):
    monkeypatch.setattr(cv2, "imwrite", lambda *_args: False)

    with pytest.raises(multiqr.ImageWriteError, match="保存できません"):
        multiqr.write_image(tmp_path / "result.png", sample_image)
