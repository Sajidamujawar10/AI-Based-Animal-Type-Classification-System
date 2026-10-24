"""
Phase 2 - Model Training
"""

import argparse
import json
from pathlib import Path

import numpy as np
import tensorflow as tf
from sklearn.utils.class_weight import compute_class_weight


def build_datasets(data_dir: Path, img_size: int, batch_size: int):
    train_ds = tf.keras.utils.image_dataset_from_directory(
        data_dir / "train", image_size=(img_size, img_size),
        batch_size=batch_size, label_mode="int", shuffle=True, seed=42,
    )
    val_ds = tf.keras.utils.image_dataset_from_directory(
        data_dir / "val", image_size=(img_size, img_size),
        batch_size=batch_size, label_mode="int", shuffle=False,
    )
    class_names = train_ds.class_names

    augment = tf.keras.Sequential([
        tf.keras.layers.RandomFlip("horizontal"),
        tf.keras.layers.RandomRotation(0.08),
        tf.keras.layers.RandomZoom(0.15),
        tf.keras.layers.RandomContrast(0.15),
        tf.keras.layers.RandomBrightness(0.15),
    ], name="augmentation")

    preprocess = tf.keras.applications.mobilenet_v3.preprocess_input

    def prep_train(x, y):
        x = augment(x, training=True)
        x = preprocess(x)
        return x, y

    def prep_eval(x, y):
        x = preprocess(x)
        return x, y

    train_ds_prepped = train_ds.map(prep_train, num_parallel_calls=tf.data.AUTOTUNE)
    val_ds_prepped = val_ds.map(prep_eval, num_parallel_calls=tf.data.AUTOTUNE)

    train_ds_prepped = train_ds_prepped.prefetch(tf.data.AUTOTUNE)
    val_ds_prepped = val_ds_prepped.prefetch(tf.data.AUTOTUNE)

    return train_ds, train_ds_prepped, val_ds_prepped, class_names


def compute_weights(train_ds, num_classes):
    labels = np.concatenate([y.numpy() for _, y in train_ds], axis=0)
    classes = np.arange(num_classes)
    weights = compute_class_weight(class_weight="balanced", classes=classes, y=labels)
    return {int(c): float(w) for c, w in zip(classes, weights)}


def build_model(num_classes: int, img_size: int):
    base = tf.keras.applications.MobileNetV3Large(
        input_shape=(img_size, img_size, 3), include_top=False, weights="imagenet",
        pooling="avg",
    )
    base.trainable = False

    inputs = tf.keras.Input(shape=(img_size, img_size, 3))
    x = base(inputs, training=False)
    x = tf.keras.layers.Dropout(0.3)(x)
    x = tf.keras.layers.Dense(256, activation="relu")(x)
    x = tf.keras.layers.Dropout(0.3)(x)
    outputs = tf.keras.layers.Dense(num_classes, activation="softmax")(x)

    model = tf.keras.Model(inputs, outputs)
    return model, base


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data_dir", required=True)
    ap.add_argument("--out_dir", required=True)
    ap.add_argument("--img_size", type=int, default=224)
    ap.add_argument("--batch_size", type=int, default=32)
    ap.add_argument("--epochs_head", type=int, default=15)
    ap.add_argument("--epochs_finetune", type=int, default=20)
    ap.add_argument("--unfreeze_layers", type=int, default=40)
    ap.add_argument("--lr_head", type=float, default=1e-3)
    ap.add_argument("--lr_finetune", type=float, default=5e-5)
    args = ap.parse_args()

    data_dir = Path(args.data_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    train_ds_raw, train_ds, val_ds, class_names = build_datasets(
        data_dir, args.img_size, args.batch_size)
    num_classes = len(class_names)
    print(f"Classes ({num_classes}): {class_names}")

    with open(out_dir / "class_names.json", "w") as f:
        json.dump(class_names, f, indent=2)

    class_weights = compute_weights(train_ds_raw, num_classes)
    print("Class weights:", class_weights)

    model, base = build_model(num_classes, args.img_size)

    callbacks = [
        tf.keras.callbacks.ModelCheckpoint(
            str(out_dir / "best_head.keras"), save_best_only=True, monitor="val_accuracy"),
        tf.keras.callbacks.EarlyStopping(
            monitor="val_accuracy", patience=5, restore_best_weights=True),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss", factor=0.5, patience=3, min_lr=1e-7),
    ]

    print("\n=== Phase A: training classification head (backbone frozen) ===")
    model.compile(
        optimizer=tf.keras.optimizers.Adam(args.lr_head),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    history_a = model.fit(
        train_ds, validation_data=val_ds,
        epochs=args.epochs_head, class_weight=class_weights, callbacks=callbacks,
    )

    print(f"\n=== Phase B: fine-tuning top {args.unfreeze_layers} backbone layers ===")
    base.trainable = True
    for layer in base.layers[:-args.unfreeze_layers]:
        layer.trainable = False

    model.compile(
        optimizer=tf.keras.optimizers.Adam(args.lr_finetune),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    callbacks_ft = [
        tf.keras.callbacks.ModelCheckpoint(
            str(out_dir / "best_finetuned.keras"), save_best_only=True, monitor="val_accuracy"),
        tf.keras.callbacks.EarlyStopping(
            monitor="val_accuracy", patience=6, restore_best_weights=True),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss", factor=0.5, patience=3, min_lr=1e-8),
    ]
    history_b = model.fit(
        train_ds, validation_data=val_ds,
        epochs=args.epochs_finetune, class_weight=class_weights, callbacks=callbacks_ft,
    )

    final_path = out_dir / "breed_model_final.keras"
    model.save(final_path)
    print(f"\nSaved final model to {final_path}")

    hist = {
        "phase_a": {k: [float(v) for v in vals] for k, vals in history_a.history.items()},
        "phase_b": {k: [float(v) for v in vals] for k, vals in history_b.history.items()},
    }
    with open(out_dir / "training_history.json", "w") as f:
        json.dump(hist, f, indent=2)


if __name__ == "__main__":
    main()