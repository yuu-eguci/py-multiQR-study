import os
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest

import foo
import make_samples

REPO_ROOT = Path(__file__).resolve().parent.parent


def write_single_qr(path, text):
    canvas = np.full((480, 480, 3), 255, np.uint8)
    canvas[120:360, 120:360] = make_samples.make_qr(text)
    cv2.imwrite(str(path), canvas)


def test_main_prints_texts_and_writes_output(sample_files, tmp_path, capsys):
    image_path, _ = sample_files
    output = tmp_path / "nested" / "result.png"

    assert foo.main([str(image_path), "--output", str(output)]) == 0

    out = capsys.readouterr().out.splitlines()
    assert out == ["hello-1", "hello-2", "テスト3", f"wrote {output}"]
    assert cv2.imread(str(output)) is not None


def test_main_without_output_only_prints(sample_files, capsys):
    image_path, _ = sample_files

    assert foo.main([str(image_path)]) == 0
    assert capsys.readouterr().out.splitlines() == ["hello-1", "hello-2", "テスト3"]


def test_main_reports_missing_file(tmp_path, capsys):
    with pytest.raises(SystemExit) as exc:
        foo.main([str(tmp_path / "missing.png")])

    assert exc.value.code == 2
    assert "画像を読み込めません" in capsys.readouterr().err


def test_main_returns_1_when_no_qr(tmp_path, capsys):
    blank = tmp_path / "blank.png"
    cv2.imwrite(str(blank), np.full((100, 100, 3), 255, np.uint8))

    assert foo.main([str(blank)]) == 1
    assert "見つかりませんでした" in capsys.readouterr().out


def test_main_escapes_control_characters(tmp_path, capsys):
    image_path = tmp_path / "escape.png"
    write_single_qr(image_path, "A\x1b[31mRED\x1b[0m\nB")

    assert foo.main([str(image_path)]) == 0
    assert capsys.readouterr().out.splitlines() == [r"A\x1b[31mRED\x1b[0m\nB"]


def test_main_reads_transparent_png(tmp_path, capsys):
    image_path = tmp_path / "alpha.png"
    qr = make_samples.make_qr("alpha-1")[:, :, 0]
    rgba = np.zeros((480, 480, 4), np.uint8)
    rgba[120:360, 120:360, 3] = np.where(qr == 0, 255, 0)
    cv2.imwrite(str(image_path), rgba)

    assert foo.main([str(image_path)]) == 0
    assert capsys.readouterr().out.splitlines() == ["alpha-1"]


@pytest.mark.parametrize("name", ["result.unknown", "result"])
def test_main_reports_unsupported_output_extension(sample_files, tmp_path, capsys, name):
    image_path, _ = sample_files

    assert foo.main([str(image_path), "--output", str(tmp_path / name)]) == 1

    captured = capsys.readouterr()
    assert "画像を保存できません" in captured.err
    assert "wrote" not in captured.out


def test_main_reports_unwritable_output_dir(sample_files, tmp_path, capsys):
    image_path, _ = sample_files
    not_a_dir = tmp_path / "file.txt"
    not_a_dir.write_text("x")

    assert foo.main([str(image_path), "--output", str(not_a_dir / "result.png")]) == 1
    assert "保存できません" in capsys.readouterr().err


def test_main_refuses_to_overwrite_input(sample_files, capsys):
    image_path, _ = sample_files
    before = image_path.read_bytes()
    same_file = image_path.parent / "." / image_path.name

    with pytest.raises(SystemExit) as exc:
        foo.main([str(image_path), "--output", str(same_file)])

    assert exc.value.code == 2
    assert "入力画像と同じ" in capsys.readouterr().err
    assert image_path.read_bytes() == before


def test_main_rejects_image_over_pixel_limit(sample_files):
    image_path, _ = sample_files
    env = {**os.environ, "OPENCV_IO_MAX_IMAGE_PIXELS": "1000"}

    result = subprocess.run(
        [sys.executable, "foo.py", str(image_path)],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    assert "画像を読み込めません" in result.stderr
    assert "Traceback" not in result.stderr
