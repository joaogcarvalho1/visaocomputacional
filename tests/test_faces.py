from io import BytesIO

import cv2
import numpy as np
import pytest
from PIL import Image

from vision.faces import FaceEngine, decode_image


def test_decode_converts_rgb_to_bgr_and_rejects_invalid_data():
    output = BytesIO()
    Image.new("RGB", (100, 100), (255, 0, 0)).save(output, format="PNG")
    frame = decode_image(output.getvalue())
    assert frame[0, 0].tolist() == [0, 0, 255]
    with pytest.raises(ValueError, match="ler a imagem"):
        decode_image(b"not an image")
    with pytest.raises(ValueError, match="10 MB"):
        decode_image(b"x" * (10 * 1024 * 1024 + 1))


def test_transparent_image_gets_white_background():
    output = BytesIO()
    Image.new("RGBA", (100, 100), (0, 0, 0, 0)).save(output, format="PNG")
    assert np.all(decode_image(output.getvalue()) == 255)


def test_no_face_cannot_be_enrolled(tmp_path):
    engine = FaceEngine(tmp_path)
    with pytest.raises(ValueError, match="exatamente um rosto"):
        engine.enroll(np.zeros((480, 640, 3), dtype=np.uint8))
    assert engine.samples == []


def test_enrollment_rejects_duplicates_and_trains_real_lbph(tmp_path, monkeypatch):
    engine = FaceEngine(tmp_path / "cadastro-João")
    rng = np.random.default_rng(1)
    known = rng.integers(0, 256, (160, 160), dtype=np.uint8)
    frame = np.zeros((200, 200, 3), dtype=np.uint8)
    box = (0, 0, 160, 160)
    monkeypatch.setattr(engine, "_extract", lambda _: [(known, box)])
    assert engine.enroll(frame) == 1
    with pytest.raises(ValueError, match="já está cadastrada"):
        engine.enroll(frame)
    with pytest.raises(ValueError, match="pelo menos 5"):
        engine.train()
    for index in range(1, 5):
        sample = np.roll(known, index, axis=0)
        monkeypatch.setattr(engine, "_extract", lambda _, sample=sample: [(sample, box)])
        engine.enroll(frame)
    assert engine.train() == 5
    monkeypatch.setattr(engine, "_extract", lambda _: [(known, box)])
    match = engine.recognize(frame)
    assert match.matched
    assert match.distance == pytest.approx(0)
    # Uma textura uniforme difere das amostras: exercita a rejeição do LBPH real.
    monkeypatch.setattr(engine, "_extract", lambda _: [(np.zeros_like(known), box)])
    assert engine.recognize(frame).status == "unknown"
    monkeypatch.setattr(engine, "_extract", lambda _: [])
    assert engine.recognize(frame).status == "no_face"
    monkeypatch.setattr(engine, "_extract", lambda _: [(known, box), (known, box)])
    assert engine.recognize(frame).status == "multiple_faces"
    engine.clear()
    assert engine.samples == []
    assert engine.model is None


def test_corrupt_training_sample_is_reported(tmp_path):
    folder = tmp_path / "samples"
    folder.mkdir()
    for index in range(5):
        cv2.imwrite(str(folder / f"{index}.png"), np.zeros((20, 20), np.uint8))
    with pytest.raises(ValueError, match="amostras inválidas"):
        FaceEngine(tmp_path).train()
