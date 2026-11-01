"""Detecção de qualquer rosto frontal; não cadastra nem identifica pessoas."""

from pathlib import Path

import cv2
import numpy as np


class FaceDetector:
    def __init__(self):
        cascade = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
        # Ler o XML em memória também suporta caminhos com acentos no Windows.
        storage = cv2.FileStorage(
            cascade.read_text(encoding="utf-8"), cv2.FILE_STORAGE_READ | cv2.FILE_STORAGE_MEMORY
        )
        self.detector = cv2.CascadeClassifier()
        try:
            loaded = self.detector.read(storage.getFirstTopLevelNode())
        finally:
            storage.release()
        if not loaded or self.detector.empty():
            raise RuntimeError("Detector facial OpenCV indisponível.")

    def detect(self, frame: np.ndarray) -> list[tuple[int, int, int, int]]:
        if (
            frame is None
            or frame.dtype != np.uint8
            or frame.ndim != 3
            or frame.shape[2] != 3
            or frame.size == 0
        ):
            raise ValueError("Esperada uma imagem BGR não vazia.")
        gray = cv2.equalizeHist(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))
        boxes = self.detector.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80)
        )
        return [tuple(int(value) for value in box) for box in boxes]
