import cv2
import pytest

import baz


def test_reader_binarizes_and_decodes(sample_image):
    reader = baz.QRCodeReader()

    codes = reader(sample_image, thresh=80)

    assert [c.text for c in codes] == ["hello-1", "hello-2", "テスト3"]
    assert reader.img.shape == sample_image.shape


def test_run_saves_side_by_side_frames(sample_image, fake_capture_factory, tmp_path, capsys):
    capture = fake_capture_factory([sample_image])

    assert baz.run(capture, thresh=80, show_window=False, save_dir=tmp_path) == 1

    saved = cv2.imread(str(tmp_path / "frame_0001.png"))
    assert saved.shape == (sample_image.shape[0], sample_image.shape[1] * 2, 3)
    assert capsys.readouterr().out.splitlines() == [
        "frame 0001 (thresh 80): hello-1, hello-2, テスト3",
    ]


def test_main_with_out_dir_string_saves_frames(sample_files, tmp_path, capsys):
    _, video_path = sample_files
    out_dir = tmp_path / "frames"

    argv = ["--video", str(video_path), "--no-window", "--save-frame", "--out-dir", str(out_dir)]
    assert baz.main(argv) == 0

    assert len(list(out_dir.glob("frame_*.png"))) == 12
    assert capsys.readouterr().out.splitlines()[0] == (
        "frame 0001 (thresh 80): hello-1, hello-2, テスト3"
    )


def test_main_opens_camera_index_as_int(monkeypatch, sample_image, fake_capture_factory):
    opened = []
    capture = fake_capture_factory([sample_image])

    def fake_video_capture(source):
        opened.append(source)
        return capture

    monkeypatch.setattr(baz.cv2, "VideoCapture", fake_video_capture)

    assert baz.main(["--video", "0", "--no-window"]) == 0
    assert opened == [0]
    assert capture.released


def test_main_does_not_create_out_dir_without_save_frame(sample_files, tmp_path):
    _, video_path = sample_files
    out_dir = tmp_path / "frames"

    assert baz.main(["--video", str(video_path), "--no-window", "--out-dir", str(out_dir)]) == 0
    assert not out_dir.exists()


def test_main_explains_no_window_on_headless_opencv(monkeypatch, sample_files, capsys):
    _, video_path = sample_files

    def headless_imshow(*_args):
        raise baz.cv2.error("OpenCV(5.0.0) window.cpp: The function is not implemented.")

    monkeypatch.setattr(baz.cv2, "imshow", headless_imshow)

    assert baz.main(["--video", str(video_path)]) == 1
    assert "--no-window" in capsys.readouterr().err


@pytest.mark.parametrize("thresh", ["-1", "256", "999"])
def test_main_rejects_threshold_out_of_range(thresh, capsys):
    with pytest.raises(SystemExit) as exc:
        baz.main(["--video", "missing.avi", "--no-window", "--thresh", thresh])

    assert exc.value.code == 2
    assert "0 から 255" in capsys.readouterr().err


def test_main_prints_threshold_in_use(sample_files, capsys):
    _, video_path = sample_files

    assert baz.main(["--video", str(video_path), "--no-window", "--thresh", "100"]) == 0
    assert capsys.readouterr().out.splitlines()[0] == (
        "frame 0001 (thresh 100): hello-1, hello-2, テスト3"
    )


def test_main_reports_failed_frame_save(monkeypatch, sample_files, tmp_path, capsys):
    _, video_path = sample_files
    monkeypatch.setattr(cv2, "imwrite", lambda *_args: False)

    argv = ["--video", str(video_path), "--no-window", "--save-frame", "--out-dir", str(tmp_path)]
    assert baz.main(argv) == 1

    captured = capsys.readouterr()
    assert "保存できません" in captured.err
    assert "--out-dir" in captured.err
    assert len(captured.out.splitlines()) == 1


def test_main_reports_unwritable_out_dir(sample_files, tmp_path, capsys):
    _, video_path = sample_files
    not_a_dir = tmp_path / "file.txt"
    not_a_dir.write_text("x")

    argv = ["--video", str(video_path), "--no-window", "--save-frame", "--out-dir", str(not_a_dir)]
    assert baz.main(argv) == 1
    assert "--out-dir" in capsys.readouterr().err
