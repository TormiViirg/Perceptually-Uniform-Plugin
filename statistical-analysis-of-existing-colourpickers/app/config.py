from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class AppConfig:
    upload_dir: str = "uploads"
    output_dir: str = "outputs"

    max_upload_mb: int = 25
    allowed_exts: Tuple[str, ...] = ("png", "jpg", "jpeg", "bmp", "gif", "tiff", "webp")

    # Output defaults
    default_top_n_display: int = 50      # how many colors to show on the results page
    max_top_n_display: int = 500         # safety cap for UI rendering
    include_alpha_default: bool = False  # default checkbox state

    # CSV settings
    csv_dialect: str = "excel"
    csv_newline: str = ""


CONFIG = AppConfig()
