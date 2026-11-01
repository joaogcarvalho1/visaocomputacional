from argparse import Namespace

import numpy as np
import pytest

from vision.faces import Recognition
from vision.monitor import run


def test_camera_failure_stops_relay_and_releases_camera(monkeypatch):
    class Engine:
        def __init__(self, *args):
            pass

        def train(self):
            pass

        def recognize(self, frame):
            return Recognition("recognized", 20)

    class Camera:
        reads = 0
        released = False

        def isOpened(self):
            return True

        def set(self, *args):
            pass

        def read(self):
            self.reads += 1
            return (True, np.zeros((10, 10, 3), np.uint8)) if self.reads <= 3 else (False, None)

        def release(self):
            self.released = True

    class Relay:
        commands = []
        closed = False

        def set_state(self, enabled):
            self.commands.append(enabled)

        def close(self):
            self.set_state(False)
            self.closed = True

    camera, relay = Camera(), Relay()
    monkeypatch.setattr("vision.monitor.FaceEngine", Engine)
    monkeypatch.setattr("vision.monitor.cv2.VideoCapture", lambda *args: camera)
    monkeypatch.setattr("vision.monitor.SimulatedRelay", lambda: relay)
    monkeypatch.setattr("vision.monitor.time.sleep", lambda _: None)
    args = Namespace(
        data_dir="unused", threshold=65, confirmations=3, hold=5, simulate=True, camera=0
    )
    with pytest.raises(RuntimeError, match="parou de fornecer"):
        run(args)
    assert True in relay.commands
    assert relay.commands[-1] is False
    assert camera.released and relay.closed
