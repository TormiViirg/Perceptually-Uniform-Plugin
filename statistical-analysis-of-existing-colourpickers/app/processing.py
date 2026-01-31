import csv
from typing import Any, Dict, List
from collections import Counter

from PIL import Image

from .config import CONFIG
from .utils import normalize_image


def process_image_and_write_csvs(
    image_path: str,
    pixels_csv_path: str,
    summary_csv_path: str,
    include_alpha: bool,
) -> Dict[str, Any]:
    """
    Single-pass processing:
      - iterates pixel-by-pixel
      - writes pixel CSV: x,y,r,g,b,(a)
      - counts unique colors using Counter
      - writes summary CSV: r,g,b,(a),count,percent,hex

    Returns metadata dict.
    """
    with Image.open(image_path) as img:
        img = normalize_image(img, include_alpha=include_alpha)
        width, height = img.size
        total_pixels = width * height

        data_iter = img.getdata()
        color_counts: Counter = Counter()

        with open(pixels_csv_path, "w", newline=CONFIG.csv_newline, encoding="utf-8") as f:
            writer = csv.writer(f, dialect=CONFIG.csv_dialect)

            header = ["x", "y", "r", "g", "b"]
            if include_alpha:
                header.append("a")
            writer.writerow(header)

            for i, px in enumerate(data_iter):
                x = i % width
                y = i // width

                color_counts[px] += 1

                if include_alpha:
                    r, g, b, a = px
                    writer.writerow([x, y, r, g, b, a])
                else:
                    r, g, b = px
                    writer.writerow([x, y, r, g, b])

        write_color_summary_csv(
            color_counts=color_counts,
            total_pixels=total_pixels,
            out_path=summary_csv_path,
            include_alpha=include_alpha,
        )

        return {
            "width": width,
            "height": height,
            "total_pixels": total_pixels,
            "unique_colors": len(color_counts),
            "include_alpha": include_alpha,
        }


def write_color_summary_csv(
    color_counts: Counter,
    total_pixels: int,
    out_path: str,
    include_alpha: bool,
) -> None:
    """
    Writes a CSV listing each unique color and:
      - count
      - percent of all pixels
      - hex representation

    Sorted by count descending.
    """
    with open(out_path, "w", newline=CONFIG.csv_newline, encoding="utf-8") as f:
        writer = csv.writer(f, dialect=CONFIG.csv_dialect)

        if include_alpha:
            writer.writerow(["r", "g", "b", "a", "count", "percent", "hex_rgba"])
        else:
            writer.writerow(["r", "g", "b", "count", "percent", "hex_rgb"])

        for color_tuple, count in color_counts.most_common():
            percent = (count / total_pixels * 100.0) if total_pixels else 0.0

            if include_alpha:
                r, g, b, a = color_tuple
                hex_str = f"#{r:02X}{g:02X}{b:02X} {a:03d}"
                writer.writerow([r, g, b, a, count, f"{percent:.10f}", hex_str])
            else:
                r, g, b = color_tuple
                hex_str = f"#{r:02X}{g:02X}{b:02X}"
                writer.writerow([r, g, b, count, f"{percent:.10f}", hex_str])


def read_top_colors_from_summary_csv(
    summary_csv_path: str,
    include_alpha: bool,
    top_n: int,
) -> List[Dict[str, Any]]:
    """
    Reads the first N data rows from the summary CSV (already sorted by count desc)
    and returns a list of dicts suitable for rendering the HTML table.
    """
    rows: List[Dict[str, Any]] = []
    with open(summary_csv_path, "r", newline=CONFIG.csv_newline, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            if idx >= top_n:
                break

            if include_alpha:
                r = int(row["r"]); g = int(row["g"]); b = int(row["b"]); a = int(row["a"])
                count = int(row["count"])
                percent = float(row["percent"])
                tuple_str = f"({r}, {g}, {b}, {a})"
                hex_str = row.get("hex_rgba", f"#{r:02X}{g:02X}{b:02X} {a:03d}")
                css_color = f"rgba({r}, {g}, {b}, {a/255.0:.6f})"
            else:
                r = int(row["r"]); g = int(row["g"]); b = int(row["b"])
                count = int(row["count"])
                percent = float(row["percent"])
                tuple_str = f"({r}, {g}, {b})"
                hex_str = row.get("hex_rgb", f"#{r:02X}{g:02X}{b:02X}")
                css_color = f"rgb({r}, {g}, {b})"

            rows.append({
                "r": r, "g": g, "b": b,
                "a": a if include_alpha else None,
                "count": count,
                "percent": percent,
                "tuple_str": tuple_str,
                "hex_str": hex_str,
                "css_color": css_color,
            })
    return rows
