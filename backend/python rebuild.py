import zipfile
from pathlib import Path

SRC = Path(r"D:\path\to\extracted_folder")   # folder with the 3 files
OUT = Path(r"D:\Breed\backend\breed_model_final.keras")

with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    for name in ["config.json", "metadata.json", "model.weights.h5"]:
        z.write(SRC / name, arcname=name)   # must sit at the root of the zip
print("done:", OUT.stat().st_size / 1e6, "MB")