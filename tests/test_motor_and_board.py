import pytest

from bci_motor import motor as motor_mod
from bci_motor.board import channel_command, rail_uv
from bci_motor.motor import Motor


class FakeSerial:
    def __init__(self, *args, **kwargs):
        self.sent = []
        self.in_waiting = 0
        self.closed = False

    def write(self, data):
        self.sent.append(data.decode().strip())

    def reset_input_buffer(self):
        pass

    def close(self):
        self.closed = True


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr(motor_mod.time, "sleep", lambda s: None)


def test_motorinador_protocol():
    m = Motor("COM7", "motorinador", rpm=30, serial_factory=FakeSerial)
    ser = m.ser
    m.set_running(True)
    m.set_running(True)          # repetido: no debe reenviar
    m.toggle_direction()
    m.set_running(False)
    m.close()
    assert ser.sent == ["0", "f", "v30", "1", "b", "0", "0"]
    assert ser.closed and not m.connected


def test_simple_protocol():
    m = Motor("COM7", "simple", serial_factory=FakeSerial)
    m.set_running(True)
    m.toggle_direction()
    assert m.ser.sent == ["R0", "R1", "D"]


def test_without_port_does_nothing():
    m = Motor(None)
    m.set_running(True)
    m.toggle_direction()
    m.close()
    assert not m.connected


def test_unknown_protocol():
    with pytest.raises(ValueError):
        Motor(None, "otro")


def test_channel_command():
    assert channel_command(0, gain=8, bias=False) == "x1040010X"   # el de la guía de ThinkPulse
    assert channel_command(7, gain=8, bias=True) == "x8040110X"
    assert channel_command(8, gain=24) == "xQ060010X"              # canal 9 = Daisy


def test_rail():
    assert rail_uv("cyton", 8) == pytest.approx(534_375)
    assert rail_uv("synthetic", 8) == float("inf")
