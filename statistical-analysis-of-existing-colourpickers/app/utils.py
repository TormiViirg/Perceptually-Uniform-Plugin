import os
import json
import secrets
from typing import Any, Dict

from werkzeug.utils import secure_filename
from PIL import Image

from .config import CONFIG


def ensure_dirs() -> None:
    os.makedirs(CONFIG.upload_dir, exist_ok=True)
    os.makedirs(CONFIG.output_dir, exist_ok=True)


def allowed_file(filename: str) -> bool:
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in CONFIG.allowed_exts


def unique_basename(original_filename: str) -> str:
    """
    Generate a safe, unique base name:
      "my photo.png" -> "my_photo__a1b2c3d4e5f6g7h8"
    """
    name = os.path.splitext(secure_filename(original_filename))[0] or "image"
    token = secrets.token_hex(8)
    return f"{name}__{token}"


def normalize_image(img: Image.Image, include_alpha: bool) -> Image.Image:
    """
    Convert any image mode into consistent RGB or RGBA.
    - If include_alpha=False: RGB (drops alpha)
    - If include_alpha=True : RGBA (keeps alpha)
    """
    target_mode = "RGBA" if include_alpha else "RGB"
    if img.mode != target_mode:
        img = img.convert(target_mode)
    return img


def safe_cleanup(path: str) -> None:
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


def clamp_int(value: Any, default: int, min_v: int, max_v: int) -> int:
    try:
        n = int(value)
    except Exception:
        return default
    return max(min_v, min(max_v, n))


def metadata_path(base: str) -> str:
    return os.path.join(CONFIG.output_dir, f"{base}.json")


def write_metadata(base: str, meta: Dict[str, Any]) -> None:
    with open(metadata_path(base), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)


def read_metadata(base: str) -> Dict[str, Any]:
    path = metadata_path(base)
    if not os.path.exists(path):
        raise FileNotFoundError("Metadata not found (maybe server restarted or files deleted).")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def output_paths(base: str) -> Dict[str, str]:
    """
    Standard output file naming.
    """
    return {
        "pixels_csv": os.path.join(CONFIG.output_dir, f"{base}_pixels.csv"),
        "summary_csv": os.path.join(CONFIG.output_dir, f"{base}_color_summary.csv"),
    }
