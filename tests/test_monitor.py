from argparse import Namespace

import numpy as np
import pytest

from vision.monitor import main, run


@pytest.mark.parametrize("face_count", [1, 2])
@pytest.mark.parametrize("frame_limit", [4, 7])
def test_automatic_monitor_delays_on_and_off_without_enrollment(
    monkeypatch, tmp_path, face_count, frame_limit
):
    counts = iter([0, face_count, face_count, face_count, 0, 0, 0])
    timestamps = iter([0, 1, 5.9, 6, 7, 11.9, 12])

    class Detector:
        def detect(self, frame):
            return [(0, 0, 80, 80)] * next(counts)

    class Camera:
        reads = 0
        released = False

        def isOpened(self):
            return True

        def set(self, *args):
            pass

        def read(self):
            self.reads += 1
            if self.reads <= frame_limit:
                return True, np.zeros((100, 100, 3), np.uint8)
            return False, None

        def release(self):
            self.released = True

    class Relay:
        def __init__(self):
            self.commands = []
            self.closed = False

        def set_state(self, enabled):
            self.commands.append(enabled)

        def close(self):
            self.set_state(False)
            self.closed = True

    camera, relay = Camera(), Relay()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("vision.monitor.FaceDetector", Detector)
    monkeypatch.setattr("vision.monitor.cv2.VideoCapture", lambda *args: camera)
    monkeypatch.setattr("vision.monitor.SimulatedRelay", lambda: relay)
    monkeypatch.setattr("vision.monitor.time.sleep", lambda _: None)
    monkeypatch.setattr("vision.monitor.time.monotonic", lambda: next(timestamps))
    args = Namespace(on_delay=5, off_delay=5, simulate=True, camera=0)
    with pytest.raises(RuntimeError, match="parou de fornecer"):
        run(args)
    expected_frames = [False, False, False, True, True, True, False]
    assert relay.commands == expected_frames[:frame_limit] + [False]
    assert camera.released and relay.closed
    assert list(tmp_path.iterdir()) == []


def test_cli_defaults_to_five_seconds_and_needs_no_training_arguments(monkeypatch):
    observed = []
    monkeypatch.setattr("sys.argv", ["monitor", "--simulate"])
    monkeypatch.setattr("vision.monitor.run", observed.append)
    assert main() == 0
    assert observed[0].on_delay == observed[0].off_delay == 5
    assert not hasattr(observed[0], "data_dir")
