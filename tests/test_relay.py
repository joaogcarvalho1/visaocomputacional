import pytest

from vision.relay import ArduinoRelay, LampPolicy


def test_five_second_delays_start_at_first_presence_and_first_absence():
    policy = LampPolicy()
    assert not policy.update(False, 0)
    assert not policy.update(True, 1)
    assert not policy.update(True, 5.99)
    assert policy.update(True, 6)
    assert policy.update(False, 7)
    assert policy.update(False, 11.99)
    assert not policy.update(False, 12)


def test_condition_change_resets_both_pending_timers():
    policy = LampPolicy()
    assert not policy.update(True, 0)
    assert not policy.update(False, 4)
    assert not policy.update(True, 5)
    assert not policy.update(True, 9)
    assert policy.update(True, 10)
    assert policy.update(False, 11)
    assert policy.update(True, 15)
    assert policy.update(False, 16)
    assert policy.update(False, 20)
    assert not policy.update(False, 21)


def test_zero_delay_and_custom_delays():
    policy = LampPolicy(on_delay=0, off_delay=2)
    assert policy.update(True, 0)
    assert policy.update(False, 1)
    assert not policy.update(False, 3)


@pytest.mark.parametrize("delay", [-1, float("nan"), float("inf")])
def test_invalid_delays_fail_before_startup(delay):
    with pytest.raises(ValueError):
        LampPolicy(on_delay=delay)
    with pytest.raises(ValueError):
        LampPolicy(off_delay=delay)


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
