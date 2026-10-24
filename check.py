import os, zipfile
from pathlib import Path

B = Path(r"D:\Breed\backend")
print("== backend folder ==")
for p in sorted(B.iterdir()):
    kind = "DIR " if p.is_dir() else "FILE"
    size = "" if p.is_dir() else f"{p.stat().st_size:,} bytes"
    print(kind, p.name, size)

k = B / "breed_model_final.keras"
print("\n== breed_model_final.keras ==")
if k.is_file():
    print("size:", k.stat().st_size)
    print("zip contents:", zipfile.ZipFile(k).namelist() if zipfile.is_zipfile(k) else "NOT A ZIP")
else:
    print("not a file (missing or a folder)")

print("\n== searching for model parts ==")
for root in [r"D:\\", r"C:\Users\user"]:
    for dp, dn, fn in os.walk(root):
        for f in fn:
            if f == "model.weights.h5" or f.endswith(".keras"):
                fp = Path(dp) / f
                print(f"{fp}  {fp.stat().st_size:,} bytes")