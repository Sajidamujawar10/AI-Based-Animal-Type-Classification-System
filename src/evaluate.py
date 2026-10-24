"""
Phase 3 - Evaluation
"""

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import tensorflow as tf
from sklearn.metrics import classification_report, confusion_matrix


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data_dir", required=True)
    ap.add_argument("--model_path", required=True)
    ap.add_argument("--img_size", type=int, default=224)
    ap.add_argument("--batch_size", type=int, default=32)
    ap.add_argument("--out_dir", default=None)
    args = ap.parse_args()

    data_dir = Path(args.data_dir)
    model_path = Path(args.model_path)
    out_dir = Path(args.out_dir) if args.out_dir else model_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    test_ds = tf.keras.utils.image_dataset_from_directory(
        data_dir / "test", image_size=(args.img_size, args.img_size),
        batch_size=args.batch_size, label_mode="int", shuffle=False,
    )
    class_names = test_ds.class_names

    preprocess = tf.keras.applications.mobilenet_v3.preprocess_input
    test_ds_prepped = test_ds.map(lambda x, y: (preprocess(x), y)).prefetch(tf.data.AUTOTUNE)

    print(f"Loading model from {model_path} ...")
    model = tf.keras.models.load_model(model_path)

    y_true, y_pred_probs = [], []
    for x_batch, y_batch in test_ds_prepped:
        preds = model.predict(x_batch, verbose=0)
        y_pred_probs.append(preds)
        y_true.append(y_batch.numpy())

    y_true = np.concatenate(y_true)
    y_pred_probs = np.concatenate(y_pred_probs)
    y_pred = np.argmax(y_pred_probs, axis=1)

    report = classification_report(
        y_true, y_pred, target_names=class_names, digits=3, zero_division=0)
    print("\n" + report)
    with open(out_dir / "classification_report.txt", "w") as f:
        f.write(report)

    report_dict = classification_report(
        y_true, y_pred, target_names=class_names, digits=3,
        zero_division=0, output_dict=True)
    with open(out_dir / "classification_report.json", "w") as f:
        json.dump(report_dict, f, indent=2)

    top3_correct = 0
    for i, probs in enumerate(y_pred_probs):
        top3 = np.argsort(probs)[-3:]
        if y_true[i] in top3:
            top3_correct += 1
    top3_acc = top3_correct / len(y_true)
    print(f"\nTop-3 Accuracy: {top3_acc:.4f}")
    with open(out_dir / "top3_accuracy.txt", "w") as f:
        f.write(f"Top-3 Accuracy: {top3_acc:.4f}\n")

    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(max(8, len(class_names) * 0.5), max(6, len(class_names) * 0.5)))
    sns.heatmap(cm, annot=False, cmap="Blues",
                xticklabels=class_names, yticklabels=class_names)
    plt.xlabel("Predicted breed")
    plt.ylabel("True breed")
    plt.title("Confusion Matrix - Breed Classification")
    plt.xticks(rotation=90)
    plt.yticks(rotation=0)
    plt.tight_layout()
    cm_path = out_dir / "confusion_matrix.png"
    plt.savefig(cm_path, dpi=150)
    print(f"Confusion matrix saved to {cm_path}")

    print(f"\nAll evaluation artifacts saved in: {out_dir}")


if __name__ == "__main__":
    main()