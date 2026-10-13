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


def test_main_reports_failed_image_write(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(cv2, "imwrite", lambda *_args: False)

    assert make_samples.main(["--out-dir", str(tmp_path)]) == 1

    captured = capsys.readouterr()
    assert "保存できません" in captured.err
    assert "wrote" not in captured.out


def test_main_reports_unopenable_video_writer(monkeypatch, tmp_path, capsys):
    class ClosedWriter:
        def __init__(self, *_args):
            pass

        def isOpened(self):
            return False

        def release(self):
            pass

    monkeypatch.setattr(cv2, "VideoWriter", ClosedWriter)

    assert make_samples.main(["--out-dir", str(tmp_path)]) == 1

    captured = capsys.readouterr()
    assert captured.out.splitlines() == [f"wrote {tmp_path / 'sample.png'}"]
    assert "動画を保存できません" in captured.err


def test_main_reports_unwritable_out_dir(tmp_path, capsys):
    not_a_dir = tmp_path / "file.txt"
    not_a_dir.write_text("x")

    assert make_samples.main(["--out-dir", str(not_a_dir / "out")]) == 1
    assert "保存できません" in capsys.readouterr().err
