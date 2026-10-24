"""
FastAPI backend for the cattle/buffalo breed recognition system.

Endpoints:
    POST /predict        - upload an image, get top-k breed predictions
    GET  /breeds         - list all supported breeds (with bilingual info)
    GET  /breeds/{name}  - info about one breed
    GET  /health         - health check

Run:
    pip install -r requirements.txt
    uvicorn main:app --host 0.0.0.0 --port 8000

Place these next to this file (download from Kaggle notebook -> Output):
    breed_model_final.keras
    class_names.json
"""

import io
import json
import os
from contextlib import asynccontextmanager
from pathlib import Path

import numpy as np
import tensorflow as tf
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from PIL import Image, ImageOps
from pydantic import BaseModel

BASE_DIR = Path(__file__).parent
MODEL_PATH = Path(os.getenv("MODEL_PATH", BASE_DIR / "breed_model_final.keras"))
LABELS_PATH = Path(os.getenv("LABELS_PATH", BASE_DIR / "class_names.json"))
BREED_INFO_PATH = BASE_DIR / "breed_info.json"
FRONTEND_PATH = BASE_DIR.parent / "frontend" / "index.html"

IMG_SIZE = 224
MAX_UPLOAD_BYTES = 10 * 1024 * 1024   # 10 MB
LOW_CONFIDENCE_THRESHOLD = 35.0       # % - below this, ask the worker to double-check

state = {"model": None, "class_names": [], "breed_info": {}}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load once at startup - loading per request would add seconds of latency.
    if not MODEL_PATH.exists():
        raise RuntimeError(f"Model not found at {MODEL_PATH}. Download breed_model_final.keras "
                           f"from the Kaggle notebook Output tab.")
    if not LABELS_PATH.exists():
        raise RuntimeError(f"class_names.json not found at {LABELS_PATH}")

    state["model"] = tf.keras.models.load_model(MODEL_PATH)
    state["class_names"] = json.loads(LABELS_PATH.read_text())
    if BREED_INFO_PATH.exists():
        state["breed_info"] = json.loads(BREED_INFO_PATH.read_text(encoding="utf-8"))

    n_out = state["model"].output_shape[-1]
    if n_out != len(state["class_names"]):
        raise RuntimeError(f"Model outputs {n_out} classes but class_names.json has "
                           f"{len(state['class_names'])}. Files are from different runs.")
    print(f"Model loaded: {len(state['class_names'])} breeds")
    yield


app = FastAPI(
    title="Cattle & Buffalo Breed Recognition API",
    description="AI breed identification supporting BPA (Bharat Pashudhan App) registration.",
    version="1.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict to your real frontend domain in production
    allow_methods=["*"],
    allow_headers=["*"],
)


class BreedPrediction(BaseModel):
    breed: str
    confidence: float
    type: str | None = None
    origin_states: list[str] = []
    description_en: str | None = None
    description_mr: str | None = None
    # Farmer-friendly guidance: main purpose, milk level, farm-work level, where to use.
    usage: dict | None = None


class PredictResponse(BaseModel):
    predictions: list[BreedPrediction]
    top_prediction: str
    top_confidence: float
    needs_review: bool   # True when the model is unsure -> UI should warn the worker


def preprocess_image(image_bytes: bytes) -> np.ndarray:
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img = ImageOps.exif_transpose(img)      # phone photos: respect rotation metadata
        img = img.convert("RGB").resize((IMG_SIZE, IMG_SIZE))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or unreadable image file.")
    arr = tf.keras.utils.img_to_array(img)
    arr = tf.keras.applications.mobilenet_v3.preprocess_input(arr)
    return np.expand_dims(arr, axis=0)


@app.get("/", include_in_schema=False)
def home():
    """Serve the web page so http://127.0.0.1:8000/ opens the app."""
    if FRONTEND_PATH.exists():
        return FileResponse(FRONTEND_PATH)
    raise HTTPException(status_code=404, detail="Frontend not found. Use /docs for the API.")


@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": state["model"] is not None,
            "num_breeds": len(state["class_names"])}


@app.get("/breeds")
def list_breeds():
    items = [{"name": n, **state["breed_info"].get(n, {})} for n in state["class_names"]]
    return {"count": len(items), "breeds": items}


@app.get("/breeds/{breed_name}")
def get_breed(breed_name: str):
    if breed_name not in state["class_names"]:
        raise HTTPException(status_code=404, detail=f"Breed '{breed_name}' not found.")
    return {"name": breed_name, **state["breed_info"].get(breed_name, {})}


@app.post("/predict", response_model=PredictResponse)
async def predict(file: UploadFile = File(...), top_k: int = Query(3, ge=1, le=10)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image.")

    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Image too large (max 10 MB).")

    probs = state["model"].predict(preprocess_image(data), verbose=0)[0]
    top = np.argsort(probs)[::-1][:top_k]

    preds = []
    for i in top:
        name = state["class_names"][i]
        info = state["breed_info"].get(name, {})
        preds.append(BreedPrediction(
            breed=name,
            confidence=round(float(probs[i]) * 100, 2),
            type=info.get("type"),
            origin_states=info.get("origin_states", []),
            description_en=info.get("description_en"),
            description_mr=info.get("description_mr"),
            usage=info.get("usage"),
        ))

    return PredictResponse(
        predictions=preds,
        top_prediction=preds[0].breed,
        top_confidence=preds[0].confidence,
        needs_review=preds[0].confidence < LOW_CONFIDENCE_THRESHOLD,
    )