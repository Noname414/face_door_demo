# ============================================================
# register_faces.py — Build face_db.pkl from known_faces/
# ============================================================
# Usage:
#   python register_faces.py
# ============================================================

# ---- GPU: 必須在 import onnxruntime / insightface 之前先設 DLL 路徑 ----
import os, sys as _sys
_dll_dirs = []
for _sp in list(_sys.path):
    for _sub in ("nvidia\\cudnn\\bin", "nvidia\\cublas\\bin", "nvidia\\cuda_nvrtc\\bin"):
        _d = os.path.join(_sp, _sub)
        if os.path.isdir(_d):
            _dll_dirs.append(_d)
if _dll_dirs:
    os.environ["PATH"] = os.pathsep.join(_dll_dirs) + os.pathsep + os.environ.get("PATH", "")
# -----------------------------------------------------------------------

import sys
from pathlib import Path

import cv2
import numpy as np

import config
from utils import (
    get_largest_face,
    l2_normalize,
    load_face_app,
    save_face_db,
)

SUPPORTED_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def register_all_faces() -> dict:
    """Scan known_faces/, extract embeddings and build face database."""

    known_dir = Path(config.KNOWN_FACES_DIR)
    if not known_dir.exists() or not known_dir.is_dir():
        print(f"[ERROR] Folder '{known_dir}' does not exist. Aborting.")
        sys.exit(1)

    person_dirs = sorted([d for d in known_dir.iterdir() if d.is_dir()])
    if not person_dirs:
        print(f"[ERROR] No sub-folders found in '{known_dir}'. Aborting.")
        sys.exit(1)

    print("Loading InsightFace model …")
    app = load_face_app()
    print("Model ready.\n")

    face_db: dict = {}

    for person_dir in person_dirs:
        name = person_dir.name
        image_paths = sorted(
            [p for p in person_dir.iterdir() if p.suffix.lower() in SUPPORTED_EXT]
        )

        if not image_paths:
            print(f"[WARN] {name}: no valid image files found, skipping.")
            continue

        embeddings = []

        for img_path in image_paths:
            img = cv2.imread(str(img_path))
            if img is None:
                print(f"[WARN] {name}: cannot read '{img_path.name}', skipping.")
                continue

            faces = app.get(img)

            if not faces:
                print(f"[WARN] {name}: no face detected in '{img_path.name}', skipping.")
                continue

            if len(faces) > 1:
                print(
                    f"[WARN] {name}: {len(faces)} faces found in '{img_path.name}', "
                    "using the largest one."
                )

            face = get_largest_face(faces)
            emb = l2_normalize(face.normed_embedding)
            embeddings.append(emb)
            print(f"[OK] {name}: {img_path.name}")

        if not embeddings:
            print(f"[WARN] {name}: no valid embeddings extracted, skipping.")
            continue

        # Average all embeddings and re-normalise
        avg_emb = l2_normalize(np.mean(embeddings, axis=0))
        face_db[name] = avg_emb

    return face_db


def main() -> None:
    face_db = register_all_faces()

    if not face_db:
        print("\n[ERROR] No people registered. face_db.pkl was NOT saved.")
        sys.exit(1)

    save_face_db(face_db, config.DB_PATH)
    print(f"\nFace database saved to {config.DB_PATH}")
    print(f"Total registered people: {len(face_db)}")
    for name in face_db:
        print(f"  - {name}")


if __name__ == "__main__":
    main()
