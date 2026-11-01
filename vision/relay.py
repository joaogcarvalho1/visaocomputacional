"""Protocolo serial com confirmação e política temporal de acionamento."""

import time
from dataclasses import dataclass

import serial


@dataclass
class LampPolicy:
    confirmations: int = 3
    hold_seconds: float = 5.0
    consecutive: int = 0
    authorized_until: float = float("-inf")

    def __post_init__(self):
        if self.confirmations < 1 or self.hold_seconds < 0:
            raise ValueError("Confirmações deve ser positivo e duração não pode ser negativa.")

    def update(self, recognized: bool, now: float, *, force_off: bool = False) -> bool:
        if force_off:
            self.consecutive = 0
            self.authorized_until = float("-inf")
            return False
        self.consecutive = self.consecutive + 1 if recognized else 0
        if self.consecutive >= self.confirmations:
            self.authorized_until = now + self.hold_seconds
        return now <= self.authorized_until


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
