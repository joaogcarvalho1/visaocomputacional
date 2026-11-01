"""Protocolo serial com confirmação e política temporal de acionamento."""

import math
import time
from dataclasses import dataclass

import serial


@dataclass
class LampPolicy:
    on_delay: float = 5.0
    off_delay: float = 5.0
    state: bool = False
    pending_since: float | None = None

    def __post_init__(self):
        if any(not math.isfinite(delay) or delay < 0 for delay in (self.on_delay, self.off_delay)):
            raise ValueError("Os atrasos devem ser números finitos maiores ou iguais a zero.")

    def update(self, face_present: bool, now: float) -> bool:
        if face_present == self.state:
            self.pending_since = None
            return self.state
        if self.pending_since is None:
            self.pending_since = now
        delay = self.on_delay if face_present else self.off_delay
        if now - self.pending_since >= delay:
            self.state = face_present
            self.pending_since = None
        return self.state


class ArduinoRelay:
    def __init__(self, port: str, *, reset_delay: float = 2.0):
        self.connection = serial.Serial(port, 9600, timeout=0.5, write_timeout=1)
        try:
            time.sleep(reset_delay)  # O Uno reinicia quando a porta USB é aberta.
            self.connection.reset_input_buffer()
            self.set_state(False)
        except Exception:
            self.connection.close()
            raise

    def set_state(self, enabled: bool) -> None:
        command = b"ON" if enabled else b"OFF"
        self.connection.write(command + b"\n")
        expected = b"ACK " + command
        response = self.connection.readline().strip()
        if response != expected:
            raise ConnectionError(
                "O Arduino não confirmou o comando. Verifique a porta e o firmware."
            )

    def close(self) -> None:
        try:
            self.set_state(False)
        finally:
            self.connection.close()


class SimulatedRelay:
    def __init__(self):
        self.state = False

    def set_state(self, enabled: bool) -> None:
        if self.state != enabled:
            print(f"[SIMULAÇÃO] Lâmpada {'LIGADA' if enabled else 'DESLIGADA'}", flush=True)
        self.state = enabled

    def close(self) -> None:
        self.set_state(False)
