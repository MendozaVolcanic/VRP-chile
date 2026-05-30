#!/usr/bin/env python3
"""S91 — auditoría reproducible de los warm-scene highs de PCC.

Fuente de verdad de las tablas de FINDINGS.md. Regenera, de primera mano sobre
`data/mirova_equivalent/PuyehueCordonCaulle.json`:
  - warm-scene (t_max≥273K, meq>10): NO los toca el filtro display #259.
  - cirrus-cold (t_max<273K, meq>10): caen en la categoría que atenúa #259.
  - cruce MIROVA OCR (CONS no los tiene; A11) para las fechas warm-scene.

Lección S91: NO transcribir números a mano (hubo 2 transcripciones erróneas
en la sesión). Correr este script y copiar su salida verbatim.

Uso:
  python experiments/_s91_warmscene/audit_warmscene.py
  python experiments/_s91_warmscene/audit_warmscene.py --no-ocr   # offline
"""
import argparse
import csv
import io
import json
import sys
import urllib.request
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from pipeline.audit_metrics import mirova_eq_vrp  # noqa: E402

VOL = "PuyehueCordonCaulle"
OCR_URL = ("https://raw.githubusercontent.com/MendozaVolcanic/Mirova-v1/main/"
           "monitoreo_satelital/registro_vrp_ocr.csv")


def fmt(meq, r):
    return ("  %s | meq=%7.1f MW | t_max=%5.1f K | t_bg=%5.1f K | "
            "dnti_ctx=%4s | bt=%s nti=%s eti=%s | %s | %s" % (
                r.get("datetime_utc"), meq, r.get("t_max_k") or 0,
                r.get("t_bg_k") or 0, r.get("diag_n_dnti_ctx_path"),
                r.get("diag_n_bt_path"), r.get("diag_n_nti_path"),
                r.get("diag_n_eti_path"), r.get("distance_class"),
                r.get("sensor")))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-ocr", action="store_true")
    ap.add_argument("--top", type=int, default=6)
    args = ap.parse_args()

    d = json.load(open(ROOT / "data" / "mirova_equivalent" / f"{VOL}.json",
                       encoding="utf-8"))
    recs = d.get("records", d) if isinstance(d, dict) else d
    warm, cold = [], []
    for r in recs:
        meq = mirova_eq_vrp(r, VOL)
        if meq <= 10:
            continue
        (warm if (r.get("t_max_k") or 0) >= 273 else cold).append((meq, r))
    warm.sort(key=lambda x: -x[0])
    cold.sort(key=lambda x: -x[0])

    print(f"\nPCC warm-scene audit — n_records={len(recs)} "
          f"warm(≥273K,meq>10)={len(warm)} cold(<273K,meq>10)={len(cold)}")
    print(f"\n=== WARM-SCENE t_max≥273K (categoría #2, no atenuado por #259), "
          f"top {args.top} ===")
    for meq, r in warm[:args.top]:
        print(fmt(meq, r))
    print(f"\n=== CIRRUS-COLD t_max<273K (atenuado display #259), "
          f"top {args.top} ===")
    for meq, r in cold[:args.top]:
        print(fmt(meq, r))

    if args.no_ocr:
        return
    print("\n=== Cruce MIROVA OCR (A11: PCC no está en CONS) ===")
    dates = {r.get("datetime_utc", "")[:10] for _, r in warm[:args.top]}
    dates |= {r.get("datetime_utc", "")[:10] for _, r in cold[:2]}
    try:
        raw = urllib.request.urlopen(OCR_URL, timeout=30).read().decode(
            "utf-8", errors="replace")
    except Exception as e:  # noqa: BLE001
        print(f"  (OCR no disponible: {e})")
        return
    rows = list(csv.DictReader(io.StringIO(raw)))
    hit = 0
    for r in rows:
        v = (r.get("Volcan", "") or "").lower()
        if "uyehue" not in v and "aulle" not in v:
            continue
        ts = (r.get("Fecha_Satelite_UTC", "") or "").strip()
        if ts[:10] in dates and (r.get("Tipo_Registro", "") or "").startswith("ALERTA"):
            hit += 1
            print(f"  MIROVA {ts[:16]} | VRP={r.get('VRP_MW')} MW | "
                  f"dist={r.get('Distancia_km')} | {r.get('Sensor')}")
    if not hit:
        print("  (sin filas OCR PCC en esas fechas)")


if __name__ == "__main__":
    main()
