import argparse
import hashlib
import json
import os
import re
import shutil
from collections import defaultdict
from pathlib import Path

from PIL import Image
from tqdm import tqdm

try:
    import imagehash
    HAS_IMAGEHASH = True
except ImportError:
    HAS_IMAGEHASH = False
    print("[WARN] imagehash not installed -> near-duplicate removal will be skipped.")

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
JUNK_FOLDER_NAMES = {"images", "image", "img", "data", "train", "test", "val", "dataset"}

BREED_ALIASES = {
    "alambadi": "Alambadi",
    "amritmahal": "Amritmahal",
    "ayrshire": "Ayrshire_Cross",
    "banni": "Banni",
    "bargur": "Bargur",
    "bhadawari": "Bhadawari", "bhadwari": "Bhadawari",
    "brownswiss": "Brown_Swiss_Cross",
    "chhattisgarhi": "Chhattisgarhi",
    "dangi": "Dangi",
    "deoni": "Deoni",
    "gir": "Gir", "girindia": "Gir", "gircattle": "Gir",
    "guernsey": "Guernsey_Cross",
    "hallikar": "Hallikar",
    "hariana": "Hariana",
    "himachalipahari": "Himachali_Pahari",
    "holsteinfriesian": "HF_Cross", "hf": "HF_Cross", "hfcross": "HF_Cross",
    "jaffarabadi": "Jaffarabadi", "jaffrabadi": "Jaffarabadi",
    "jersey": "Jersey_Cross", "jerseycross": "Jersey_Cross",
    "kalahandi": "Kalahandi",
    "kangayam": "Kangayam",
    "kankrej": "Kankrej",
    "kasargod": "Kasargod",
    "kenkatha": "Kenkatha",
    "khariar": "Khariar",
    "kherigarh": "Kherigarh",
    "khillari": "Khillari",
    "konkankapila": "Konkan_Kapila",
    "kosali": "Kosali",
    "krishnavalley": "Krishna_Valley",
    "ladakhi": "Ladakhi",
    "lakhimi": "Lakhimi",
    "malnadgidda": "Malnad_Gidda",
    "malvi": "Malvi",
    "mehsana": "Mehsana",
    "mewati": "Mewati",
    "murrah": "Murrah",
    "nagori": "Nagori",
    "nagpuri": "Nagpuri",
    "nari": "Nari",
    "nilravi": "Nili_Ravi", "niliravi": "Nili_Ravi",
    "nimari": "Nimari",
    "ongole": "Ongole",
    "pandharpuri": "Pandharpuri",
    "podathirupu": "Poda_Thirupu",
    "pulikulam": "Pulikulam",
    "punganur": "Punganur",
    "purnea": "Purnea",
    "rathi": "Rathi",
    "reddane": "Red_Dane_Cross",
    "redsindhi": "Red_Sindhi", "sindhired": "Red_Sindhi",
    "redkandhari": "Red_Kandhari",
    "sahiwal": "Sahiwal",
    "shwetakapila": "Shweta_Kapila",
    "surti": "Surti",
    "tharparkar": "Tharparkar",
    "toda": "Toda",
    "umblachery": "Umblachery",
    "vechur": "Vechur",
    "bachaur": "Bachaur",
    "badri": "Badri",
    "bhelai": "Bhelai",
    "chilika": "Chilika",
    "dagri": "Dagri",
    "gangatari": "Gangatiri",
    "gaolao": "Gaolao",
    "ghumsari": "Ghumsari",
    "gojri": "Gojri",
    "luit": "Luit",
    "marathwada": "Marathwadi",
    "motu": "Motu",
    "ponwar": "Ponwar",
    "siri": "Siri",
    "thutho": "Thutho",
    "crossbreed": "Crossbred_Cattle", "crossbred": "Crossbred_Cattle",
    "desicow": "Desi_Cattle", "desi": "Desi_Cattle",
    "desibuffalo": "Desi_Buffalo", "desibuffalos": "Desi_Buffalo",
}


def normalize_key(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


def canonical_breed_name(raw_folder_name: str) -> str:
    key = normalize_key(raw_folder_name)
    if key in BREED_ALIASES:
        return BREED_ALIASES[key]
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", raw_folder_name).strip("_")
    return cleaned if cleaned else "Unknown"


def discover_breed_folders(raw_dir: Path):
    """If the folder containing images has a generic name (images/img/data),
    use its PARENT folder's name as the breed instead - some datasets nest
    images one level deeper as <Breed>/images/*.jpg."""
    found = []
    for root, dirs, files in os.walk(raw_dir):
        has_image = any(Path(f).suffix.lower() in IMAGE_EXTS for f in files)
        if not has_image:
            continue
        root_path = Path(root)
        if root_path.name.lower() in JUNK_FOLDER_NAMES:
            parent = root_path.parent
            if parent == raw_dir or parent.name.lower() in JUNK_FOLDER_NAMES:
                continue
            found.append((root_path, parent.name))
        else:
            found.append((root_path, root_path.name))
    return found


def is_valid_image(path: Path, min_side=64) -> bool:
    try:
        with Image.open(path) as img:
            img.verify()
        with Image.open(path) as img:
            w, h = img.size
            if w < min_side or h < min_side:
                return False
        return True
    except Exception:
        return False


def phash_of(path: Path):
    try:
        with Image.open(path) as img:
            return str(imagehash.phash(img.convert("RGB")))
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw_dirs", nargs="+", required=True)
    ap.add_argument("--out_dir", required=True)
    ap.add_argument("--min_images", type=int, default=15)
    ap.add_argument("--val_split", type=float, default=0.15)
    ap.add_argument("--test_split", type=float, default=0.15)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    breed_to_images = defaultdict(list)
    all_raw_names = set()

    for raw_dir in args.raw_dirs:
        raw_dir = Path(raw_dir)
        if not raw_dir.exists():
            print(f"[WARN] raw dir not found, skipping: {raw_dir}")
            continue
        folders = discover_breed_folders(raw_dir)
        print(f"[{raw_dir.name}] discovered {len(folders)} candidate breed folders")
        for folder_path, raw_name in folders:
            all_raw_names.add(raw_name)
            breed = canonical_breed_name(raw_name)
            imgs = [p for p in folder_path.iterdir()
                    if p.is_file() and p.suffix.lower() in IMAGE_EXTS]
            breed_to_images[breed].extend(imgs)

    print("\n=== All raw folder names discovered ===")
    for n in sorted(all_raw_names):
        print(" -", n)
    print("=" * 70)

    print("\nValidating images...")
    for breed in list(breed_to_images.keys()):
        valid = [p for p in tqdm(breed_to_images[breed], desc=breed, leave=False)
                 if is_valid_image(p)]
        breed_to_images[breed] = valid

    if HAS_IMAGEHASH:
        print("\nRemoving near-duplicate images...")
        seen_hashes = set()
        for breed in list(breed_to_images.keys()):
            deduped = []
            for p in tqdm(breed_to_images[breed], desc=breed, leave=False):
                h = phash_of(p)
                if h is None or h in seen_hashes:
                    continue
                seen_hashes.add(h)
                deduped.append(p)
            breed_to_images[breed] = deduped

    dropped = []
    for breed in list(breed_to_images.keys()):
        if len(breed_to_images[breed]) < args.min_images:
            dropped.append((breed, len(breed_to_images[breed])))
            del breed_to_images[breed]
    if dropped:
        print(f"\nDropped {len(dropped)} classes with < {args.min_images} images:")
        for b, c in dropped:
            print(f"   {b}: {c} images")

    import random
    random.seed(args.seed)

    report_rows = []
    for breed, imgs in sorted(breed_to_images.items()):
        random.shuffle(imgs)
        n = len(imgs)
        n_test = max(1, int(n * args.test_split))
        n_val = max(1, int(n * args.val_split))
        n_train = n - n_val - n_test

        splits = {
            "train": imgs[:n_train],
            "val": imgs[n_train:n_train + n_val],
            "test": imgs[n_train + n_val:],
        }

        for split_name, split_imgs in splits.items():
            split_dir = out_dir / split_name / breed
            split_dir.mkdir(parents=True, exist_ok=True)
            for src in split_imgs:
                h = hashlib.md5(str(src).encode()).hexdigest()[:8]
                dst = split_dir / f"{h}_{src.name}"
                shutil.copy2(src, dst)

        report_rows.append({
            "breed": breed, "total": n,
            "train": len(splits["train"]), "val": len(splits["val"]), "test": len(splits["test"]),
        })

    import csv
    report_path = out_dir / "merge_report.csv"
    with open(report_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["breed", "total", "train", "val", "test"])
        writer.writeheader()
        writer.writerows(report_rows)

    class_names = sorted(breed_to_images.keys())
    with open(out_dir / "class_names.json", "w") as f:
        json.dump(class_names, f, indent=2)

    print(f"\nDone. {len(class_names)} breed classes, "
          f"{sum(r['total'] for r in report_rows)} images total.")
    print(f"Report: {report_path}")


if __name__ == "__main__":
    main()