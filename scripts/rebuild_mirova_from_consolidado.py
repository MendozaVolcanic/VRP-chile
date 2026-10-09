"""
rebuild_mirova_from_consolidado.py — Regenerate any data/mirova/<Volcano>.json
from the authoritative text-scraped CSV (registro_vrp_consolidado.csv).

Generalisation of rebuild_mirova_lascar.py (kept for history). Use this for
any new volcano before trusting it as a validation reference.

Usage:
    python scripts/rebuild_mirova_from_consolidado.py <JsonName> <CsvName> [--source PATH]
    python scripts/rebuild_mirova_from_consolidado.py PuyehueCordonCaulle "Puyehue-Cordon Caulle"
    python scripts/rebuild_mirova_from_consolidado.py Tupungatito Tupungatito
    python scripts/rebuild_mirova_from_consolidado.py Llaima Llaima --source data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv

S77 (2026-05-24): hardcoded 14042026 CSV no longer exists. Default source is now
the canonical 'latest_consolidado.csv' at repo root (refreshed by Mirova-v1
scraper). For historical rescue use --source pointing at
mirova_v1_snapshot/registro_vrp_consolidado.csv (longer history, 17,966 rows).

The first arg is the JSON stem used by data/mirova/<stem>.json (matching
volcanoes.yaml 'name' field). The second is the 'Volcan' value as it appears
in the CSV (which may differ: hyphens, spaces, accents).

If the destination JSON exists it is backed up to
  data/mirova/<stem>_OLD_pre_consolidado.json
before overwriting.
"""
import argparse
import csv
import json
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).parent.parent
# Session 12 2026-04-14: swap from '10.04.2026' (11668 rows) to '14042026'
# (12437 rows, +769 rows, +4 days of coverage through Apr 14 including 37
# new refs in the Apr 10-14 window previously missing from our NRT gap).
# Older CSVs preserved on disk for historical reproducibility.
DEFAULT_SOURCE = REPO / "latest_consolidado.csv"


# S150 (auditoria S150, B-H4/B-H5; decision de Nicolas 2026-10-09, opcion a): la linea de MIROVA del tablero
# leia solo la tabla y solo "Muy Bajo"/"Bajo", y en la erupcion de Nevados de Chillan perdia las dos pasadas
# mas fuertes del 2026-10-01 (9,0 MW y 10,0 MW "Moderado", llegadas solo por OCR). La escala de MIROVA
# tiene cinco niveles de actividad; "Moderado" ya aparecio en el OCR, que era la condicion que la regla de
# abajo exigia para ampliar el conjunto. NULO y FALSO POSITIVO siguen fuera. "Medio" es la etiqueta que usaba
# la version 21 del OCR (hasta el 2026-06-10, 196 alertas, mediana 1,9 MW) para el nivel que despues se llama
# "Moderado".
CLASES_ALERTA = {"Muy Bajo", "Bajo", "Medio", "Moderado", "Alto", "Muy Alto"}
RAIZ_REAL = Path(__file__).resolve().parent.parent   # REPO puede apuntar a otro lado en los tests


def _coords(json_stem):
    import yaml
    with open(RAIZ_REAL / "volcanoes.yaml", encoding="utf-8") as fh:
        return {v["name"]: (v["lat"], v["lon"]) for v in yaml.safe_load(fh)["volcanoes"] if "lat" in v}.get(json_stem)


def _es_noche(latlon, fecha):
    """Elevacion solar <= 0 en el volcan, con la misma funcion que usa el pipeline (store._solar_elevation)."""
    import sys
    if str(RAIZ_REAL) not in sys.path:
        sys.path.insert(0, str(RAIZ_REAL))
    from pipeline.store import _solar_elevation
    dt = datetime.strptime(fecha[:16], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    return _solar_elevation(latlon[0], latlon[1], dt) <= 0


def _filas_ocr(path, names, latlon=None):
    """Alertas del OCR (valores leidos de las imagenes de MIROVA). FALSO_POSITIVO_OCR queda fuera: es la
    etiqueta del scraper para lo que no pudo confirmar. Ojo (docs/S150_IMAGENES_SNPP.md): una fila del OCR
    puede traer la imagen de otra pasada; por eso salen marcadas `source: ocr` y el tablero las dibuja
    distinto. Solo pasadas NOCTURNAS: el pipeline no procesa el dia, y entre las diurnas del OCR estan los
    artefactos solares de MIROVA (A76: Lascar 2026-06-15 17:24, 760 MW "Alto")."""
    with open(path, encoding="utf-8-sig") as f:
        filas = [r for r in csv.DictReader(f)
                 if (r.get("Volcan") or "").strip() in names and (r.get("Tipo_Registro") or "").strip() == "ALERTA_TERMICA_OCR"]
    if latlon is None:
        return filas
    return [r for r in filas if (r.get("Fecha_Satelite_UTC") or "")[:16] and _es_noche(latlon, r["Fecha_Satelite_UTC"])]


def rebuild(json_stem: str, csv_volcano: str, source: Path = None, ocr: Path = None) -> None:
    SOURCE = Path(source) if source else DEFAULT_SOURCE
    if not SOURCE.exists():
        raise FileNotFoundError(f"Source CSV not found: {SOURCE}")
    print(f"Source: {SOURCE}")

    dest = REPO / "data" / "mirova" / f"{json_stem}.json"
    dest.parent.mkdir(parents=True, exist_ok=True)

    with open(SOURCE, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["_fuente"] = "consolidado"

    # S12 2026-04-14: allow multiple CSV names per volcano (comma-separated).
    # MIROVA renamed some volcanoes mid-year (e.g., 'Peteroa' -> 'PlanchonPeteroa'
    # on 2026-01-16). The scraper preserves both names exactly as found, so
    # the rebuild must merge them. Pass as e.g. "Peteroa,PlanchonPeteroa".
    names = [n.strip() for n in csv_volcano.split(",") if n.strip()]
    matched = [r for r in rows if (r.get("Volcan") or "").strip() in names]
    print(f"Total CSV rows: {len(rows)}")
    print(f"Matching {names}: {len(matched)}")
    if ocr:
        filas_ocr = _filas_ocr(Path(ocr), names, _coords(json_stem))
        for r in filas_ocr:
            r["_fuente"] = "ocr"
        print(f"OCR alerts for {names}: {len(filas_ocr)} (from {ocr})")
        matched = matched + filas_ocr

    # CRITICAL — see lessons L7.10 (post-mortem of session 8 contamination):
    # Filter by 'Clasificacion Mirova'. The CSV's universe of values is exactly
    # 4 categories (verified 2026-04-08 on registro_vrp_consolidado.csv):
    #     NULO            9324  — MIROVA-rejected, NOT a thermal detection
    #     Muy Bajo         263  — real detection (low activity)
    #     Bajo             118  — real detection
    #     FALSO POSITIVO    12  — MIROVA-confirmed false positive
    # Only 'Muy Bajo' and 'Bajo' are ground truth. The first version of this
    # script filtered only by VRP_MW>0, which imported all 9324 NULOs and
    # contaminated the entire Session 8 audit. This must never happen again.
    # The set is CLOSED at {'Muy Bajo', 'Bajo'} until a new category actually
    # appears in the CSV — do NOT speculatively add 'Moderado'/'Alto'/etc.,
    # silent additions hide regressions.
    # S150: ampliado a la escala completa de MIROVA (ver CLASES_ALERTA arriba); el texto de arriba se
    # conserva por historia.
    VALID_CLASSES = CLASES_ALERTA
    rejected_clases = Counter()
    kept = []
    for r in matched:
        try:
            vrp = float(r.get("VRP_MW") or 0)
        except ValueError:
            continue
        if vrp <= 0:
            continue
        clas = (r.get("Clasificacion Mirova") or "").strip()
        if clas not in VALID_CLASSES:
            rejected_clases[clas] += 1
            continue
        dt_raw = (r.get("Fecha_Satelite_UTC") or "").strip()
        if not dt_raw:
            continue
        try:
            dt = datetime.strptime(dt_raw[:19], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                dt = datetime.strptime(dt_raw[:16], "%Y-%m-%d %H:%M")
            except ValueError:
                continue
        dt_str = dt.strftime("%Y-%m-%d %H:%M")
        sensor = (r.get("Sensor") or "").strip()
        try:
            dist = float(r.get("Distancia_km") or 0)
        except ValueError:
            dist = 0.0
        kept.append({
            "datetime_utc": dt_str,
            "sensor": sensor,
            "VRP_MW": round(vrp, 3),
            "distancia_km": round(dist, 2),
            "clasificacion": (r.get("Clasificacion Mirova") or "").strip(),
            "source": r.get("_fuente", "consolidado"),
        })

    print(f"  rejected by clasificacion: {dict(rejected_clases)}")
    print(f"  with VRP > 0 AND clasificacion in {sorted(VALID_CLASSES)}: {len(kept)}")

    # Defense in depth: hard-fail if any NULO snuck through. Impossible with
    # the filter above, but if a future edit weakens VALID_CLASSES this check
    # will catch it before it contaminates a ref file. See L7.10.
    leaked = [r for r in kept if (r.get("clasificacion") or "").strip() not in VALID_CLASSES]
    assert not leaked, f"FATAL: {len(leaked)} records leaked past clasificacion filter"

    # Dedupe (datetime, sensor). S150: si la tabla y el OCR traen la misma pasada, manda la tabla (texto con
    # decimales exactos); entre filas de la misma fuente, la de mayor VRP, como antes.
    by_key = {}
    for rec in kept:
        key = (rec["datetime_utc"], rec["sensor"])
        prev = by_key.get(key)
        if prev is None:
            by_key[key] = rec
        elif prev["source"] != rec["source"]:
            if rec["source"] == "consolidado":
                by_key[key] = rec
        elif rec["VRP_MW"] > prev["VRP_MW"]:
            by_key[key] = rec
    deduped = sorted(by_key.values(), key=lambda r: (r["datetime_utc"], r["sensor"]))
    print(f"  after dedupe: {len(deduped)}")

    sensors = Counter(r["sensor"] for r in deduped)
    print(f"  sensors: {dict(sensors)}")
    if deduped:
        print(f"  range: {deduped[0]['datetime_utc']} -> {deduped[-1]['datetime_utc']}")

    # Backup old OCR file if present
    if dest.exists():
        backup = dest.with_name(f"{json_stem}_OLD_pre_consolidado.json")
        shutil.copy(dest, backup)
        print(f"  backed up existing to: {backup.name}")

    output = {
        "volcano": json_stem,
        "source": "registro_vrp_consolidado.csv (text-scraped from mirovaweb.it)" + (" + registro_vrp_ocr.csv (OCR de las imagenes)" if ocr else ""),
        "note": ("S150: incluye alertas del OCR marcadas source='ocr' (valores leidos de la imagen de MIROVA; pueden "
                 "traer la imagen de otra pasada, docs/S150_IMAGENES_SNPP.md). Para calibrar magnitud usar solo "
                 "source='consolidado'.") if ocr else "OCR-derived records intentionally excluded (decimals truncated by OCR). Only text-scraped values used for quantitative calibration.",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "records": deduped,
    }
    dest.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"  wrote: {dest}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("json_stem", help="JSON stem (e.g. PuyehueCordonCaulle)")
    p.add_argument("csv_volcano", help="Volcano name as it appears in the CSV")
    p.add_argument("--source", default=None, help="Path to consolidado CSV (default: repo/latest_consolidado.csv)")
    p.add_argument("--ocr", default=None, help="S150: path to registro_vrp_ocr.csv to add OCR alerts (source='ocr')")
    args = p.parse_args()
    rebuild(args.json_stem, args.csv_volcano, source=args.source, ocr=args.ocr)


if __name__ == "__main__":
    main()
