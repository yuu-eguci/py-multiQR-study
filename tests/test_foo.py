import cv2
import numpy as np
import pytest

import foo


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
