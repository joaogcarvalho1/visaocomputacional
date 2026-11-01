import pytest

from vision.relay import ArduinoRelay, LampPolicy


def test_lamp_needs_consecutive_matches_and_expires():
    policy = LampPolicy(confirmations=3, hold_seconds=5)
    assert not policy.update(False, 0)
    assert not policy.update(True, 1)
    assert not policy.update(False, 2)
    assert not policy.update(True, 3)
    assert not policy.update(True, 4)
    assert policy.update(True, 5)
    assert policy.update(False, 9.9)
    assert not policy.update(False, 10.1)
    assert not policy.update(True, 11)


def test_multiple_faces_cancels_existing_authorization():
    policy = LampPolicy(confirmations=1)
    assert policy.update(True, 1)
    assert not policy.update(False, 2, force_off=True)
    assert not policy.update(False, 3)


class FakeSerial:
    def __init__(self, *args, **kwargs):
        self.commands = []
        self.closed = False
        self.bad_ack = False

    def reset_input_buffer(self):
        pass

    def write(self, value):
        self.commands.append(value)

    def readline(self):
        return b"ERR\n" if self.bad_ack else b"ACK " + self.commands[-1]

    def close(self):
        self.closed = True


def test_serial_protocol_starts_and_ends_off(monkeypatch):
    device = FakeSerial()
    monkeypatch.setattr("vision.relay.serial.Serial", lambda *args, **kwargs: device)
    relay = ArduinoRelay("COM3", reset_delay=0)
    relay.set_state(True)
    relay.close()
    assert device.commands == [b"OFF\n", b"ON\n", b"OFF\n"]
    assert device.closed


def test_bad_ack_is_not_treated_as_success(monkeypatch):
    device = FakeSerial()
    monkeypatch.setattr("vision.relay.serial.Serial", lambda *args, **kwargs: device)
    relay = ArduinoRelay("COM3", reset_delay=0)
    device.bad_ack = True
    with pytest.raises(ConnectionError):
        relay.set_state(True)
    with pytest.raises(ConnectionError):
        relay.close()
    assert device.closed


def test_initial_connection_failure_closes_port(monkeypatch):
    device = FakeSerial()
    device.bad_ack = True
    monkeypatch.setattr("vision.relay.serial.Serial", lambda *args, **kwargs: device)
    with pytest.raises(ConnectionError):
        ArduinoRelay("COM3", reset_delay=0)
    assert device.closed
