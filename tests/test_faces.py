import numpy as np
import pytest

from vision.faces import FaceDetector


def test_blank_image_has_no_faces_without_any_enrollment(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    detector = FaceDetector()
    assert detector.detect(np.zeros((480, 640, 3), np.uint8)) == []
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    "frame",
    [
        None,
        np.zeros((0, 0, 3), np.uint8),
        np.zeros((10, 10), np.uint8),
        np.zeros((10, 10, 3), np.float32),
    ],
)
def test_invalid_frames_are_rejected(frame):
    with pytest.raises(ValueError, match="imagem BGR"):
        FaceDetector().detect(frame)


def test_multiple_faces_are_all_returned():
    class Cascade:
        def detectMultiScale(self, *args, **kwargs):
            return np.array([[1, 2, 80, 90], [100, 20, 100, 100]])

    detector = FaceDetector()
    detector.detector = Cascade()
    assert detector.detect(np.zeros((300, 300, 3), np.uint8)) == [
        (1, 2, 80, 90),
        (100, 20, 100, 100),
    ]
