import os
import json
import re

from flask import (
    Blueprint,
    send_file,
    render_template,
    flash,
    redirect,
    url_for,
    abort,
)
from PIL import Image, UnidentifiedImageError

from .config import CONFIG
from .utils import (
    ensure_dirs,
    allowed_file,
    unique_basename,
    safe_cleanup,
    clamp_int,
    write_metadata,
    read_metadata,
    output_paths,
)
from .processing import process_image_and_write_csvs, read_top_colors_from_summary_csv

from pathlib import Path
from flask import current_app, jsonify, request

bp = Blueprint("main", __name__)

HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")

def _themes_path() -> Path:
    p = Path(current_app.instance_path) / "themes.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _default_store():
    return {
        "current_id": "default",
        "themes": [{"id": "default", "bg": "#ffffff", "text": "#111111"}],
    }


def _atomic_write_json(path: Path, data: dict):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(path)


def load_theme_store() -> dict:
    path = _themes_path()
    if not path.exists():
        store = _default_store()
        _atomic_write_json(path, store)
        return store
    try:
        store = json.loads(path.read_text(encoding="utf-8"))
        if "themes" not in store or not isinstance(store["themes"], list) or not store["themes"]:
            raise ValueError("Invalid store")
        return store
    except Exception:
        store = _default_store()
        _atomic_write_json(path, store)
        return store


def save_theme_store(store: dict):
    _atomic_write_json(_themes_path(), store)


def _validate_hex(value: str, fallback: str) -> str:
    if not isinstance(value, str):
        return fallback
    s = value.strip()
    if not s.startswith("#"):
        s = "#" + s
    return s.lower() if HEX_RE.match(s) else fallback


def _theme_id(bg: str, text: str) -> str:
    return f"{bg.lower()}_{text.lower()}"


def get_current_theme() -> dict:
    store = load_theme_store()
    cur_id = store.get("current_id")
    themes = store.get("themes", [])
    cur = next((t for t in themes if t.get("id") == cur_id), None)
    return cur or themes[0] if themes else _default_store()["themes"][0]


@bp.app_context_processor
def inject_theme():
    return {"theme": get_current_theme()}


@bp.get("/api/themes")
def themes_api():
    return jsonify(load_theme_store())


@bp.post("/api/themes")
def themes_add_api():
    data = request.get_json(silent=True) or {}
    bg = _validate_hex(data.get("bg"), "#ffffff")
    text = _validate_hex(data.get("text"), "#111111")

    store = load_theme_store()
    tid = _theme_id(bg, text)

    if not any(t.get("id") == tid for t in store["themes"]):
        store["themes"].append({"id": tid, "bg": bg, "text": text})

    store["current_id"] = tid
    save_theme_store(store)
    return jsonify(store)


@bp.post("/api/themes/current")
def themes_set_current_api():
    data = request.get_json(silent=True) or {}
    tid = data.get("id")

    store = load_theme_store()
    if tid and any(t.get("id") == tid for t in store["themes"]):
        store["current_id"] = tid
        save_theme_store(store)

    return jsonify(store)


@bp.route("/", methods=["GET"])
def index():
    import app.config as cfg
    print("CONFIG FILE:", cfg.__file__, flush=True)
    print("RUNTIME max_top_n:", CONFIG.max_top_n_display, flush=True)

    ensure_dirs()
    return render_template(
        "upload.html",
        max_mb=CONFIG.max_upload_mb,
        exts=", ".join(CONFIG.allowed_exts),
        default_top_n=CONFIG.default_top_n_display,
        max_top_n=CONFIG.max_top_n_display,
        include_alpha_default=CONFIG.include_alpha_default,
    )



@bp.route("/upload", methods=["POST"])
def upload():
    ensure_dirs()

    if "image" not in request.files:
        flash("No file part in the request.", "error")
        return redirect(url_for("main.index"))

    file = request.files["image"]
    if file.filename == "":
        flash("No file selected.", "error")
        return redirect(url_for("main.index"))

    if not allowed_file(file.filename):
        flash("File type not allowed. Please upload a standard image format.", "error")
        return redirect(url_for("main.index"))

    include_alpha = bool(request.form.get("include_alpha"))
    top_n = clamp_int(
        request.form.get("top_n"),
        default=CONFIG.default_top_n_display,
        min_v=1,
        max_v=CONFIG.max_top_n_display,
    )

    base = unique_basename(file.filename)
    ext = file.filename.rsplit(".", 1)[1].lower()

    image_path = os.path.join(CONFIG.upload_dir, f"{base}.{ext}")
    paths = output_paths(base)
    pixels_csv_path = paths["pixels_csv"]
    summary_csv_path = paths["summary_csv"]

    file.save(image_path)

    try:
        with Image.open(image_path) as img:
            img.verify()

        meta = process_image_and_write_csvs(
            image_path=image_path,
            pixels_csv_path=pixels_csv_path,
            summary_csv_path=summary_csv_path,
            include_alpha=include_alpha,
        )

        meta["base"] = base
        meta["original_filename"] = file.filename
        meta["top_n"] = top_n

        write_metadata(base, meta)

    except UnidentifiedImageError:
        safe_cleanup(image_path)
        safe_cleanup(pixels_csv_path)
        safe_cleanup(summary_csv_path)
        flash("That file doesn't appear to be a valid image.", "error")
        return redirect(url_for("main.index"))

    except Exception as e:
        safe_cleanup(image_path)
        safe_cleanup(pixels_csv_path)
        safe_cleanup(summary_csv_path)
        flash(f"Processing failed: {type(e).__name__}: {e}", "error")
        return redirect(url_for("main.index"))

    return redirect(url_for("main.results", base=base))


@bp.route("/results/<base>", methods=["GET"])
def results(base: str):
    ensure_dirs()

    if "__" not in base:
        abort(404)

    meta = read_metadata(base)
    paths = output_paths(base)

    if not os.path.exists(paths["summary_csv"]):
        abort(404)

    top_n = clamp_int(
        request.args.get("top_n", meta.get("top_n", CONFIG.default_top_n_display)),
        default=CONFIG.default_top_n_display,
        min_v=1,
        max_v=CONFIG.max_top_n_display,
    )

    rows = read_top_colors_from_summary_csv(
        summary_csv_path=paths["summary_csv"],
        include_alpha=bool(meta["include_alpha"]),
        top_n=top_n,
    )

    return render_template(
        "results.html",
        base=base,
        meta=meta,
        rows=rows,
        top_n=top_n,
    )


@bp.route("/download/<base>/<kind>", methods=["GET"])
def download_file(base: str, kind: str):
    ensure_dirs()
    if "__" not in base:
        abort(404)

    paths = output_paths(base)

    if kind == "pixels":
        path = paths["pixels_csv"]
        download_name = os.path.basename(path)
    elif kind == "summary":
        path = paths["summary_csv"]
        download_name = os.path.basename(path)
    else:
        abort(404)

    if not os.path.exists(path):
        abort(404)

    return send_file(
        path,
        as_attachment=True,
        download_name=download_name,
        mimetype="text/csv",
        max_age=0,
    )


@bp.app_errorhandler(413)
def file_too_large(_err):
    flash(f"Upload too large. Max is {CONFIG.max_upload_mb} MB.", "error")
    return redirect(url_for("main.index"))


