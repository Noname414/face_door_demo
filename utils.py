# ============================================================
# utils.py — Shared helper functions
# ============================================================

import pickle
import warnings
from pathlib import Path

import numpy as np

import config


# ------------------------------------------------------------------
# InsightFace app loader
# ------------------------------------------------------------------

def load_face_app():
    """Initialise and return an InsightFace FaceAnalysis application.

    Uses the model and providers defined in config.py.
    """
    import insightface
    from insightface.app import FaceAnalysis

    app = FaceAnalysis(
        name=config.MODEL_NAME,
        providers=config.PROVIDERS,
    )
    app.prepare(ctx_id=0, det_size=config.DET_SIZE)
    return app


# ------------------------------------------------------------------
# Embedding math
# ------------------------------------------------------------------

def l2_normalize(embedding: np.ndarray) -> np.ndarray:
    """Return the L2-normalised version of *embedding*."""
    norm = np.linalg.norm(embedding)
    if norm == 0:
        return embedding
    return embedding / norm


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two *already normalised* vectors.

    InsightFace's ``normed_embedding`` is already unit-length, so a
    plain dot product gives the cosine similarity directly.
    """
    return float(np.dot(a, b))


# ------------------------------------------------------------------
# Face selection helper
# ------------------------------------------------------------------

def get_largest_face(faces):
    """Return the face with the largest bounding-box area from *faces*.

    Parameters
    ----------
    faces : list
        List of InsightFace Face objects (each has a ``.bbox`` attribute).

    Returns
    -------
    Face or None
    """
    if not faces:
        return None
    return max(
        faces,
        key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]),
    )


# ------------------------------------------------------------------
# Database I/O
# ------------------------------------------------------------------

def save_face_db(face_db: dict, path: str = config.DB_PATH) -> None:
    """Persist *face_db* to a pickle file at *path*."""
    with open(path, "wb") as fh:
        pickle.dump(face_db, fh)


def load_face_db(path: str = config.DB_PATH) -> dict:
    """Load and return the face database from *path*.

    Returns an empty dict if the file does not exist.
    """
    db_path = Path(path)
    if not db_path.exists():
        warnings.warn(f"[WARN] face_db not found at '{path}'. Run register_faces.py first.")
        return {}
    with open(db_path, "rb") as fh:
        return pickle.load(fh)


# ------------------------------------------------------------------
# Recognition
# ------------------------------------------------------------------

def recognize_face(
    face_embedding: np.ndarray,
    face_db: dict,
    threshold: float = config.THRESHOLD,
) -> tuple[str, float]:
    """Match *face_embedding* against every entry in *face_db*.

    Parameters
    ----------
    face_embedding : np.ndarray
        L2-normalised embedding of the current face.
    face_db : dict
        ``{name: normalised_embedding}`` mapping loaded from pickle.
    threshold : float
        Cosine-similarity threshold; matches below this are "unknown".

    Returns
    -------
    (name, best_similarity) : tuple[str, float]
        ``name`` is the matched person name or ``"unknown"``.
    """
    if not face_db:
        return "unknown", 0.0

    best_name = "unknown"
    best_sim = -1.0

    for name, registered_emb in face_db.items():
        sim = cosine_similarity(registered_emb, face_embedding)
        if sim > best_sim:
            best_sim = sim
            best_name = name

    if best_sim < threshold:
        best_name = "unknown"

    return best_name, best_sim
