from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class AppConfig:
    upload_dir: str = "uploads"
    output_dir: str = "outputs"

    max_upload_mb: int = 25
    allowed_exts: Tuple[str, ...] = ("png", "jpg", "jpeg", "bmp", "gif", "tiff", "webp")

    default_top_n_display: int = 5000      
    max_top_n_display: int = 5000         
    include_alpha_default: bool = False  

    csv_dialect: str = "excel"
    csv_newline: str = ""


CONFIG = AppConfig()
