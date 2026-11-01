"""Cadastro local de uma pessoa e reconhecimento facial OpenCV LBPH."""

import warnings
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from uuid import uuid4

import cv2
import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError

MIN_SAMPLES = 5
MAX_SAMPLES = 100
FACE_SIZE = (160, 160)


def read_sample(path: Path) -> np.ndarray | None:
    # Bytes evitam a limitação de caminhos Unicode do imread no Windows.
    content = path.read_bytes()
    if not content:
        return None
    return cv2.imdecode(np.frombuffer(content, np.uint8), cv2.IMREAD_GRAYSCALE)


def decode_image(data: bytes) -> np.ndarray:
    """Decodifica upload para BGR, limitado a 10 MB e 24 megapixels."""
    if not data or len(data) > 10 * 1024 * 1024:
        raise ValueError("Envie uma imagem de até 10 MB.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(data)) as source:
                if source.format not in {"JPEG", "PNG", "WEBP"}:
                    raise ValueError("Use uma imagem JPEG, PNG ou WebP.")
                if source.width * source.height > 24_000_000:
                    raise ValueError("Use uma imagem de até 24 megapixels.")
                image = ImageOps.exif_transpose(source)
                image.thumbnail((1280, 1280))
                rgba = image.convert("RGBA")
                background = Image.new("RGBA", rgba.size, "white")
                rgb = np.array(Image.alpha_composite(background, rgba).convert("RGB"))
                return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    except (Image.DecompressionBombError, Image.DecompressionBombWarning) as error:
        raise ValueError("Imagem grande demais. Use até 24 megapixels.") from error
    except (UnidentifiedImageError, OSError, SyntaxError) as error:
        raise ValueError("Não foi possível ler a imagem. Verifique o arquivo.") from error


@dataclass(frozen=True)
class Recognition:
    status: str
    distance: float | None = None
    box: tuple[int, int, int, int] | None = None

    @property
    def matched(self) -> bool:
        return self.status == "recognized"


class FaceEngine:
    def __init__(self, data_dir: Path, threshold: float = 65.0):
        if not 0 < threshold <= 200:
            raise ValueError("O limite LBPH deve estar entre 0 e 200.")
        self.data_dir = Path(data_dir)
        self.threshold = threshold
        cascade = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
        self.detector = cv2.CascadeClassifier(str(cascade))
        if self.detector.empty():
            raise RuntimeError("Detector facial OpenCV indisponível.")
        self.model = None

    @property
    def samples(self) -> list[Path]:
        return sorted((self.data_dir / "samples").glob("*.png"))

    def _extract(self, frame: np.ndarray) -> list[tuple[np.ndarray, tuple[int, int, int, int]]]:
        if frame is None or frame.dtype != np.uint8 or frame.ndim != 3 or frame.shape[2] != 3:
            raise ValueError("Esperada uma imagem BGR válida.")
        if frame.size == 0:
            raise ValueError("Imagem vazia.")
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        boxes = self.detector.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(80, 80),
        )
        faces = []
        for raw_box in boxes:
            x, y, width, height = (int(value) for value in raw_box)
            face = cv2.resize(gray[y : y + height, x : x + width], FACE_SIZE)
            faces.append((cv2.equalizeHist(face), (x, y, width, height)))
        return faces

    def enroll(self, frame: np.ndarray) -> int:
        faces = self._extract(frame)
        if len(faces) != 1:
            raise ValueError("Cada foto deve conter exatamente um rosto frontal visível.")
        samples = self.samples
        if len(samples) >= MAX_SAMPLES:
            raise ValueError(f"Limite de {MAX_SAMPLES} fotos atingido.")
        face, _ = faces[0]
        for path in samples:
            if np.array_equal(face, read_sample(path)):
                raise ValueError("Esta foto já está cadastrada. Use outra pose ou iluminação.")
        folder = self.data_dir / "samples"
        folder.mkdir(parents=True, exist_ok=True)
        destination = folder / f"{uuid4().hex}.png"
        success, encoded = cv2.imencode(".png", face)
        if not success:
            raise OSError("Não foi possível salvar a amostra facial.")
        destination.write_bytes(encoded.tobytes())
        self.model = None
        return len(samples) + 1

    def train(self) -> int:
        samples = self.samples
        if len(samples) < MIN_SAMPLES:
            raise ValueError(f"Cadastre pelo menos {MIN_SAMPLES} fotos diferentes da mesma pessoa.")
        faces = [read_sample(path) for path in samples]
        if any(face is None or face.shape != FACE_SIZE for face in faces):
            raise ValueError("Há amostras inválidas. Exclua o cadastro e faça um novo.")
        model = cv2.face.LBPHFaceRecognizer_create(radius=1, neighbors=8, grid_x=8, grid_y=8)
        model.train(faces, np.ones(len(faces), dtype=np.int32))
        self.model = model
        return len(faces)

    def recognize(self, frame: np.ndarray) -> Recognition:
        if self.model is None:
            self.train()
        faces = self._extract(frame)
        if not faces:
            return Recognition("no_face")
        if len(faces) > 1:
            return Recognition("multiple_faces")
        face, box = faces[0]
        label, distance = self.model.predict(face)
        matched = label == 1 and distance <= self.threshold
        return Recognition("recognized" if matched else "unknown", float(distance), box)

    def clear(self) -> None:
        for path in self.samples:
            path.unlink()
        self.model = None
