"""
API tests. Run from the backend/ folder:   pytest -q

If breed_model_final.keras is absent, a small random stand-in model with the same
input/output shape (224x224x3 -> N classes) is generated so the API logic can be
tested. NOTE: with the stand-in, only API behaviour is tested, not accuracy.
"""
import io
import json
import os
import tempfile
from pathlib import Path

import pytest
from PIL import Image

BACKEND = Path(__file__).resolve().parent.parent
CLASSES = json.loads((BACKEND / "breed_info.json").read_text(encoding="utf-8")).keys()

if not (BACKEND / "breed_model_final.keras").exists():
    import tensorflow as tf
    tmp = Path(tempfile.mkdtemp())
    inp = tf.keras.Input((224, 224, 3))
    x = tf.keras.layers.GlobalAveragePooling2D()(inp)
    out = tf.keras.layers.Dense(len(CLASSES), activation="softmax")(x)
    tf.keras.Model(inp, out).save(tmp / "model.keras")
    (tmp / "class_names.json").write_text(json.dumps(sorted(CLASSES)))
    os.environ["MODEL_PATH"] = str(tmp / "model.keras")
    os.environ["LABELS_PATH"] = str(tmp / "class_names.json")

from fastapi.testclient import TestClient  # noqa: E402
import backend.main as main  # noqa: E402


@pytest.fixture(scope="module")
def client():
    with TestClient(main.app) as c:   # `with` triggers lifespan -> model load
        yield c


def img_bytes(fmt="JPEG", size=(300, 200)):
    buf = io.BytesIO()
    Image.new("RGB", size, (120, 90, 60)).save(buf, fmt)
    return buf.getvalue()


def test_health(client):
    r = client.get("/health").json()
    assert r["status"] == "ok" and r["model_loaded"] and r["num_breeds"] == 73


def test_breeds_list_is_bilingual_and_complete(client):
    r = client.get("/breeds").json()
    assert r["count"] == 73
    for b in r["breeds"]:
        assert b["description_en"] and b["description_mr"]


def test_breed_detail_and_404(client):
    assert client.get("/breeds/Gir").json()["type"] == "cattle"
    assert client.get("/breeds/Murrah").json()["type"] == "buffalo"
    assert client.get("/breeds/NotABreed").status_code == 404


def test_predict_returns_top3_sorted(client):
    r = client.post("/predict", files={"file": ("a.jpg", img_bytes(), "image/jpeg")})
    assert r.status_code == 200
    d = r.json()
    confs = [p["confidence"] for p in d["predictions"]]
    assert len(confs) == 3 and confs == sorted(confs, reverse=True)
    assert d["top_prediction"] == d["predictions"][0]["breed"]
    assert isinstance(d["needs_review"], bool)


def test_predict_png_and_top_k(client):
    r = client.post("/predict?top_k=5", files={"file": ("a.png", img_bytes("PNG"), "image/png")})
    assert r.status_code == 200 and len(r.json()["predictions"]) == 5


def test_rejects_non_image(client):
    r = client.post("/predict", files={"file": ("a.txt", b"hello", "text/plain")})
    assert r.status_code == 400


def test_rejects_corrupt_image(client):
    r = client.post("/predict", files={"file": ("a.jpg", b"not really a jpeg", "image/jpeg")})
    assert r.status_code == 400


def test_rejects_oversized(client):
    big = b"\xff" * (main.MAX_UPLOAD_BYTES + 1)
    r = client.post("/predict", files={"file": ("a.jpg", big, "image/jpeg")})
    assert r.status_code == 413