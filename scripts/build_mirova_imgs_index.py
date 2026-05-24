"""
build_mirova_imgs_index.py
==========================

S77 F30 P3 — Genera `frontend/mirova_imgs_index.json` con el catálogo de
imágenes MIROVA disponibles para el dashboard:

  - tifs : geoTIFFs georeferenciados en `mirova-tif-archive/data/tif/<Volcano>/`
           con filename `<YYYYMMDD>_<HHMMSS>_<Sensor>.tif`.
  - kmz  : KMZ paralelos en `mirova-tif-archive/data/kmz/<Volcano>/` con
           filename `<YYYYMMDD>_<HHMMSS>_<Sensor>(_lm)?.kmz`.
  - pngs : capturas mirovaweb scrapeadas en `imagenes/<YYYY_MM_DD>/` con
           filename `<Volcano>_<Sensor>_<plotType>.png`.

`mirova-tif-archive/` vive UN NIVEL ARRIBA del repo (en
`Volcanologia/mirova-tif-archive/`), NO commiteado al repo VRP Chile —
sólo se sirve desde la máquina local de Nicolás. El frontend tolera
fetch fallido (cuando se publica a GH Pages se ve sólo PNGs y un
mensaje "TIFs disponibles sólo en máquina local").

Ejecución
---------
    python scripts/build_mirova_imgs_index.py

Salida
------
    frontend/mirova_imgs_index.json   (~1-2 MB)

Estructura
----------
{
  "generated_utc": "2026-05-24T..",
  "tifs": { "Lascar": [ {"path": "...", "datetime": "...", "sensor": "..."} ] },
  "kmz":  { "Lascar": [ {"path": "...", "datetime": "...", "sensor": "..."} ] },
  "pngs": { "Lascar": [ {"path": "...", "date": "2026-04-25",
                          "sensor": "MODIS", "type": "VRP"} ] }
}

Las listas se ordenan por (volcán, datetime desc) — la última imagen
primero. Es lo que el dashboard espera para mostrar "más reciente" arriba.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# --- Paths -------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
# mirova-tif-archive vive UN NIVEL ARRIBA del repo (Volcanologia/mirova-tif-archive)
TIF_ARCHIVE = REPO_ROOT.parent / "mirova-tif-archive" / "data" / "tif"
KMZ_ARCHIVE = REPO_ROOT.parent / "mirova-tif-archive" / "data" / "kmz"
PNG_ARCHIVE = REPO_ROOT / "imagenes"
OUTPUT = REPO_ROOT / "frontend" / "mirova_imgs_index.json"

# Path relativo desde frontend/index.html cuando se sirve la página:
#   * GH Pages: index.html se publica en root del repo → mirova-tif-archive
#     NO existe (queda fuera del repo). Estos URLs van a 404 y el frontend
#     muestra fallback. PNGs (en `imagenes/`) sí funcionan en ambos casos.
#   * Local file:// o http local: index.html sirve desde frontend/ pero
#     hay tooling (vrp-chile/scripts/serve.py) que monta root. Por eso
#     usamos paths relativos AL REPO ROOT y el frontend prefija BASE_PATH
#     según corresponda (igual que data/*.json).
#
# Convención de paths:
#   - PNGs (en repo): relativos a repo root → "imagenes/..." . Frontend les
#     prefijea BASE_PATH (mismo patrón que data/*.json). Funciona en GH Pages
#     y en local http.server desde repo root.
#   - TIFs/KMZs (FUERA del repo, en Volcanologia/mirova-tif-archive): relativos
#     a `frontend/index.html` → "../../mirova-tif-archive/...". Frontend los
#     usa DIRECTO (sin BASE_PATH). Funciona en file:// y http.server desde
#     Volcanologia/ (parent del repo). En GH Pages devuelve 404 esperado
#     y el frontend muestra fallback "disponible sólo en máquina local".
TIF_REL_PREFIX = "../../mirova-tif-archive/data/tif"
KMZ_REL_PREFIX = "../../mirova-tif-archive/data/kmz"
PNG_REL_PREFIX_REPO = "imagenes"

# --- Regex parsing -----------------------------------------------------
# TIF/KMZ filename: 20260509_034733_VIIRS750.tif   o  ..._lm.kmz
RE_TIFKMZ = re.compile(
    r"^(?P<date>\d{8})_(?P<time>\d{6})_(?P<sensor>[A-Za-z0-9]+)(?:_lm)?\.(?:tif|kmz)$"
)
# PNG filename: Lascar_VIIRS375_logVRP.png
RE_PNG = re.compile(
    r"^(?P<volcano>[A-Za-z]+)_(?P<sensor>[A-Za-z0-9]+)_(?P<type>[A-Za-z0-9]+)\.png$"
)
# Subcarpeta PNG por fecha: 2026_04_25
RE_PNG_DATE_DIR = re.compile(r"^(\d{4})_(\d{2})_(\d{2})$")


def parse_tif_or_kmz_filename(name: str) -> tuple[str, str] | None:
    """
    Extract ISO datetime + sensor of an entry like '20260509_034733_VIIRS750.tif'.
    Returns (iso_datetime, sensor) or None when filename doesn't match.
    """
    m = RE_TIFKMZ.match(name)
    if not m:
        return None
    date_s = m.group("date")  # 20260509
    time_s = m.group("time")  # 034733
    sensor = m.group("sensor")
    try:
        dt = datetime.strptime(date_s + time_s, "%Y%m%d%H%M%S")
        iso = dt.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None
    return iso, sensor


def scan_tif_or_kmz(root: Path, rel_prefix: str, ext: str) -> dict[str, list[dict]]:
    """
    Walk `<root>/<Volcano>/*.<ext>`. Return dict volcano -> list[item].
    Each item: {"path": "...", "datetime": "YYYY-MM-DD HH:MM:SS", "sensor": "..."}.
    """
    out: dict[str, list[dict]] = {}
    if not root.exists():
        print(f"[warn] {root} no existe — saltando .{ext}", file=sys.stderr)
        return out
    for vol_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        volcano = vol_dir.name
        items: list[dict] = []
        for f in vol_dir.iterdir():
            if not f.is_file() or f.suffix.lower() != f".{ext}":
                continue
            parsed = parse_tif_or_kmz_filename(f.name)
            if not parsed:
                continue
            iso, sensor = parsed
            items.append({
                "path": f"{rel_prefix}/{volcano}/{f.name}",
                "datetime": iso,
                "sensor": sensor,
            })
        if items:
            items.sort(key=lambda x: x["datetime"], reverse=True)
            out[volcano] = items
    return out


def scan_pngs(root: Path, rel_prefix: str) -> dict[str, list[dict]]:
    """
    Walk `<root>/<YYYY_MM_DD>/<Volcano>_<Sensor>_<type>.png`.
    Group by volcano. Each item: path/date/sensor/type.
    """
    out: dict[str, list[dict]] = {}
    if not root.exists():
        print(f"[warn] {root} no existe — saltando PNGs", file=sys.stderr)
        return out
    for date_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        m = RE_PNG_DATE_DIR.match(date_dir.name)
        if not m:
            continue
        date_iso = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
        for f in date_dir.iterdir():
            if not f.is_file() or f.suffix.lower() != ".png":
                continue
            mp = RE_PNG.match(f.name)
            if not mp:
                # Imágenes "misc" que no respetan la convención — saltarlas
                # silenciosamente (frontend no las puede ubicar por volcán).
                continue
            volcano = mp.group("volcano")
            sensor = mp.group("sensor")
            ptype = mp.group("type")
            out.setdefault(volcano, []).append({
                "path": f"{rel_prefix}/{date_dir.name}/{f.name}",
                "date": date_iso,
                "sensor": sensor,
                "type": ptype,
            })
    # Order: date desc, then sensor, then type.
    for vol in out:
        out[vol].sort(key=lambda x: (x["date"], x["sensor"], x["type"]), reverse=True)
    return out


def main() -> int:
    tifs = scan_tif_or_kmz(TIF_ARCHIVE, TIF_REL_PREFIX, "tif")
    kmz = scan_tif_or_kmz(KMZ_ARCHIVE, KMZ_REL_PREFIX, "kmz")
    pngs = scan_pngs(PNG_ARCHIVE, PNG_REL_PREFIX_REPO)

    payload = {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "note": (
            "Index de imágenes MIROVA para el dashboard. TIFs/KMZs viven en "
            "mirova-tif-archive/ (fuera del repo); sólo accesibles en máquina "
            "local de Nicolás. PNGs viven en imagenes/ (committed)."
        ),
        "tifs": tifs,
        "kmz": kmz,
        "pngs": pngs,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)

    n_tif = sum(len(v) for v in tifs.values())
    n_kmz = sum(len(v) for v in kmz.values())
    n_png = sum(len(v) for v in pngs.values())
    print(f"[ok] {OUTPUT}")
    print(f"     TIFs : {n_tif:>5} archivos en {len(tifs)} volcanes")
    print(f"     KMZs : {n_kmz:>5} archivos en {len(kmz)} volcanes")
    print(f"     PNGs : {n_png:>5} archivos en {len(pngs)} volcanes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
