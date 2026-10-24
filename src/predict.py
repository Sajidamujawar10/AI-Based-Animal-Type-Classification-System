"""
Phase 4 - Inference
=====================
Runs breed prediction on a single image and prints top-3 candidates with
confidence scores. This is the same logic your FastAPI `/predict` endpoint
will call.

Usage:
    python predict.py --model_path <model.keras> --labels_path <class_names.json> \
        --image_path <image.jpg> [--img_size 224] [--top_k 3]
"""

import argparse
import json

import numpy as np
import tensorflow as tf


def load_and_prep_image(image_path: str, img_size: int):
    img = tf.keras.utils.load_img(image_path, target_size=(img_size, img_size))
    arr = tf.keras.utils.img_to_array(img)
    arr = tf.keras.applications.mobilenet_v3.preprocess_input(arr)
    return np.expand_dims(arr, axis=0)


def predict_breed(model, class_names, image_path: str, img_size: int = 224, top_k: int = 3):
    x = load_and_prep_image(image_path, img_size)
    probs = model.predict(x, verbose=0)[0]
    top_indices = np.argsort(probs)[::-1][:top_k]
    return [
        {"breed": class_names[i], "confidence": round(float(probs[i]) * 100, 2)}
        for i in top_indices
    ]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model_path", required=True)
    ap.add_argument("--labels_path", required=True)
    ap.add_argument("--image_path", required=True)
    ap.add_argument("--img_size", type=int, default=224)
    ap.add_argument("--top_k", type=int, default=3)
    args = ap.parse_args()

    with open(args.labels_path) as f:
        class_names = json.load(f)

    model = tf.keras.models.load_model(args.model_path)
    results = predict_breed(model, class_names, args.image_path, args.img_size, args.top_k)

    print(f"\nPredictions for {args.image_path}:")
    for r in results:
        print(f"  {r['breed']:<25} {r['confidence']:>6.2f}%")


if __name__ == "__main__":
    main()