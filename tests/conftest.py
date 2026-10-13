import pytest

import make_samples


class FakeCapture:
    """カメラの代わりに、決められたフレームを順に返す偽キャプチャです。"""

    def __init__(self, frames):
        self.frames = list(frames)
        self.read_count = 0
        self.released = False

    def read(self):
        self.read_count += 1
        if not self.frames:
            return False, None
        return True, self.frames.pop(0)

    def isOpened(self):
        return True

    def release(self):
        self.released = True


@pytest.fixture
def sample_image():
    return make_samples.make_sample_image()


@pytest.fixture
def sample_files(tmp_path):
    make_samples.main(["--out-dir", str(tmp_path)])
    return tmp_path / "sample.png", tmp_path / "sample.avi"


@pytest.fixture
def fake_capture_factory():
    return FakeCapture
