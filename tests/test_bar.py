import numpy as np

import bar
import make_samples


def test_run_prints_texts_per_frame(sample_image, fake_capture_factory, capsys):
    capture = fake_capture_factory([sample_image, sample_image])

    assert bar.run(capture, show_window=False) == 2

    assert capsys.readouterr().out.splitlines() == [
        "frame 0001: hello-1, hello-2, テスト3",
        "frame 0002: hello-1, hello-2, テスト3",
    ]


def test_run_skips_frames_without_qr(fake_capture_factory, capsys):
    capture = fake_capture_factory([np.full((100, 100, 3), 255, np.uint8)])

    assert bar.run(capture, show_window=False) == 1
    assert capsys.readouterr().out == ""


def test_run_stops_when_camera_cannot_be_read(fake_capture_factory):
    capture = fake_capture_factory([])

    assert bar.run(capture, show_window=False) == 0
    assert capture.read_count == 1


def test_main_opens_camera_index_as_int(monkeypatch, sample_image, fake_capture_factory, capsys):
    opened = []
    capture = fake_capture_factory([sample_image])

    def fake_video_capture(source):
        opened.append(source)
        return capture

    monkeypatch.setattr(bar.cv2, "VideoCapture", fake_video_capture)

    assert bar.main(["--video", "0", "--no-window"]) == 0
    assert opened == [0]
    assert capture.released
    assert "hello-1" in capsys.readouterr().out


def test_main_reads_video_file(sample_files, capsys):
    _, video_path = sample_files

    assert bar.main(["--video", str(video_path), "--no-window"]) == 0

    lines = capsys.readouterr().out.splitlines()
    assert [line.split(":")[0] for line in lines] == [f"frame {i:04}" for i in range(1, 13)]
    assert lines[0] == "frame 0001: hello-1, hello-2, テスト3"


def test_main_reports_unopenable_source(tmp_path, capsys):
    assert bar.main(["--video", str(tmp_path / "missing.avi"), "--no-window"]) == 1
    assert "開けません" in capsys.readouterr().err


def test_main_explains_no_window_on_headless_opencv(monkeypatch, sample_files, capsys):
    _, video_path = sample_files

    def headless_imshow(*_args):
        raise bar.cv2.error("OpenCV(5.0.0) window.cpp: The function is not implemented.")

    monkeypatch.setattr(bar.cv2, "imshow", headless_imshow)

    assert bar.main(["--video", str(video_path)]) == 1
    assert "--no-window" in capsys.readouterr().err


def test_main_treats_non_ascii_digit_as_path(capsys):
    assert bar.main(["--video", "²", "--no-window"]) == 1
    assert "開けません: ²" in capsys.readouterr().err


def test_run_escapes_control_characters(fake_capture_factory, capsys):
    frame = np.full((480, 480, 3), 255, np.uint8)
    frame[120:360, 120:360] = make_samples.make_qr("A\x1b[31mRED\x1b[0m\nB")

    assert bar.run(fake_capture_factory([frame]), show_window=False) == 1
    assert capsys.readouterr().out.splitlines() == [r"frame 0001: A\x1b[31mRED\x1b[0m\nB"]
