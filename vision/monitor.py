"""Reconhecimento contínuo na webcam do computador conectado ao Arduino."""

import argparse
import logging
import time
from pathlib import Path

import cv2
import serial
from serial.tools import list_ports

from vision.faces import FaceEngine
from vision.relay import ArduinoRelay, LampPolicy, SimulatedRelay

LOG = logging.getLogger(__name__)


def run(args: argparse.Namespace) -> None:
    engine = FaceEngine(Path(args.data_dir), args.threshold)
    engine.train()
    policy = LampPolicy(args.confirmations, args.hold)
    relay = SimulatedRelay() if args.simulate else ArduinoRelay(args.port)
    camera = None
    try:
        camera = cv2.VideoCapture(args.camera)
        if not camera.isOpened():
            raise RuntimeError(
                "Não foi possível abrir a câmera. Feche outros aplicativos de vídeo."
            )
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        last_send = float("-inf")
        previous_state = None
        previous_status = None
        LOG.info("Monitor ativo. Pressione Ctrl+C para encerrar e apagar a lâmpada.")
        while True:
            ok, frame = camera.read()
            if not ok:
                raise RuntimeError("A câmera parou de fornecer imagens.")
            result = engine.recognize(frame)
            now = time.monotonic()
            state = policy.update(result.matched, now, force_off=result.status == "multiple_faces")
            if state != previous_state or now - last_send >= 0.5:
                relay.set_state(state)
                last_send = now
                previous_state = state
            if result.status != previous_status:
                LOG.info(
                    "Rosto: %s | lâmpada: %s | distância LBPH: %s",
                    result.status,
                    "ligada" if state else "desligada",
                    result.distance,
                )
                previous_status = result.status
            time.sleep(0.05)
    finally:
        if camera is not None:
            camera.release()
        try:
            relay.close()
        except (serial.SerialException, ConnectionError, OSError):
            LOG.warning(
                "Sem confirmação de desligamento; o watchdog do Uno atua em até 3 segundos."
            )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list-ports", action="store_true", help="Lista portas USB/seriais e sai.")
    parser.add_argument("--port", help="Porta do Arduino, por exemplo COM3 no Windows.")
    parser.add_argument("--simulate", action="store_true", help="Usa webcam e simula o relé.")
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--data-dir", default="data")
    parser.add_argument(
        "--threshold",
        type=float,
        default=65.0,
        help="Distância LBPH máxima; menor é mais rigoroso. Não é porcentagem.",
    )
    parser.add_argument("--confirmations", type=int, default=3)
    parser.add_argument(
        "--hold", type=float, default=5.0, help="Segundos até apagar após perder o rosto."
    )
    args = parser.parse_args()
    if args.list_ports:
        ports = list(list_ports.comports())
        for port in ports:
            print(f"{port.device}: {port.description}")
        if not ports:
            print("Nenhuma porta serial encontrada. Conecte o Arduino via USB.")
        return 0
    if args.port and args.simulate:
        parser.error("Use --port ou --simulate, apenas um por vez.")
    if not args.port and not args.simulate:
        parser.error("Informe --port COM3 ou use --simulate para testar sem Arduino.")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        run(args)
    except KeyboardInterrupt:
        LOG.info("Monitor encerrado.")
    except (ValueError, RuntimeError, OSError, ConnectionError, cv2.error) as error:
        LOG.error("%s", error)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
