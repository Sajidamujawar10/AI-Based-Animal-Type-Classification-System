import zipfile
from pathlib import Path

SRC = Path(r"D:\Breed\backend")
OUT = Path(r"D:\Breed\backend\breed_model_final.keras")
FILES = ["config.json", "metadata.json", "model.weights.h5"]

for f in FILES:
    if not (SRC / f).exists():
        raise SystemExit(f"Missing: {SRC / f}")

if OUT.exists():
    OUT.unlink()          # remove the bad zip first

with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    for f in FILES:
        z.write(SRC / f, arcname=f)     # arcname puts them at the zip root

print("contents:", zipfile.ZipFile(OUT).namelist())
print("size:", round(OUT.stat().st_size / 1e6, 1), "MB")