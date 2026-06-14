"""S108 — ¿El ratio VIIRS 0.52x (per_sensor_metrics, CONS∪OCR) es sub-estimación REAL o
artefacto de incluir OCR? Computa el ratio mediano nuestro/MIROVA para VIIRS375 y VIIRS750
en 3 universos: CONS-only, OCR-only, CONS∪OCR. Match temporal ±60min, summit (pc.vrp>0).

S103 R3 reportó VIIRS375 0.78x / VIIRS750 0.80x post-nadir. Si CONS-only ≈ 0.78x y
CONS∪OCR = 0.52x -> la diferencia es el OCR (universo), no sub-estimación nueva. Si
CONS-only ≈ 0.52x -> sub-estimación real (frente de calibración candidato).

Read-only. S91 fuente de verdad. Uso: python experiments/_s94_audit/ratio_viirs_cons_vs_ocr.py
"""
import csv
import datetime as dt
import json
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TIER_A = ["PuyehueCordonCaulle", "Villarrica", "Lascar", "Copahue", "NevadosDeChillan",
          "Llaima", "Chaiten", "PlanchonPeteroa", "Lastarria", "Isluga", "Tupungatito"]
CONS = ROOT / "latest_consolidado.csv"
OCR = ROOT / "data/mirova_reference/registro_vrp_ocr.csv"
WIN = 3600


def parse(s):
    s = str(s).replace("T", " ")[:19]
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return dt.datetime.strptime(s[:len(fmt) + 2], fmt)
        except Exception:
            pass
    return None


def our_v375(r):
    s = str(r.get("sensor", ""))
    return s.startswith("VIIRS") and not s.endswith("750")


def our_v750(r):
    return str(r.get("sensor", "")).endswith("750")


def load_mir(path, sensor_match):
    """Devuelve {vol: [(dt, vrp)]} de ALERTA con Sensor en sensor_match."""
    out = defaultdict(list)
    if not path.exists():
        return out
    for row in csv.DictReader(open(path, encoding="utf-8", errors="replace")):
        if not str(row.get("Tipo_Registro", "")).startswith("ALERTA"):
            continue
        sen = str(row.get("Sensor", "")).upper()
        if not sensor_match(sen):
            continue
        t = parse(row.get("Fecha_Satelite_UTC") or row.get("Fecha_UTC") or "")
        try:
            v = float(row.get("VRP_MW") or 0)
        except Exception:
            v = 0
        if t and v > 0:
            out[row.get("Volcan")].append((t, v))
    return out


def our_summit(vol, pred):
    obj = json.load(open(ROOT / "data/mirova_equivalent" / f"{vol}.json", encoding="utf-8"))
    recs = obj.get("records", obj)
    out = []
    for r in recs:
        if not pred(r) or r.get("distance_class") != "summit":
            continue
        v = (r.get("primary_cluster") or {}).get("vrp_mw") or 0
        t = parse(r.get("datetime_utc"))
        if t and v > 0:
            out.append((t, v))
    return out


def ratio(our_pred, mir):
    rs = []
    for vol in TIER_A:
        ours = our_summit(vol, our_pred)
        mv = mir.get(vol, [])
        for t, ov in ours:
            cands = [(abs((t - mt).total_seconds()), mvrp) for mt, mvrp in mv
                     if abs((t - mt).total_seconds()) <= WIN]
            if cands:
                rs.append(ov / min(cands)[1])
    return (statistics.median(rs), len(rs)) if rs else (None, 0)


def main():
    # V375: CONS "VIIRS375"; OCR "VIIRS375". V750: CONS/OCR "VIIRS" a secas (A48).
    v375_match = lambda s: "VIIRS375" in s or "375" in s
    v750_match = lambda s: s == "VIIRS" or "750" in s
    cons375, ocr375 = load_mir(CONS, v375_match), load_mir(OCR, v375_match)
    cons750, ocr750 = load_mir(CONS, v750_match), load_mir(OCR, v750_match)

    def merged(a, b):
        m = defaultdict(list)
        for d in (a, b):
            for k, v in d.items():
                m[k].extend(v)
        return m

    print("=== Ratio nuestro/MIROVA por universo (summit, ±60min) ===")
    print(f"{'sensor':<10}{'universo':<14}{'ratio_med':>10}{'n_pairs':>9}")
    for label, pred, c, o in [("VIIRS375", our_v375, cons375, ocr375),
                              ("VIIRS750", our_v750, cons750, ocr750)]:
        for uname, mir in [("CONS-only", c), ("OCR-only", o), ("CONS∪OCR", merged(c, o))]:
            rm, n = ratio(pred, mir)
            rms = f"{rm:.3f}x" if rm is not None else "—"
            print(f"{label:<10}{uname:<14}{rms:>10}{n:>9}")
    print("\nLectura: si CONS-only ~0.78x (V375) / 0.80x (V750) = S103 R3 -> el 0.52x del "
          "per_sensor es por el OCR (universo), no sub-estimación nueva. Si CONS-only ~0.52x "
          "-> sub-estimación real (frente de calibración).")


if __name__ == "__main__":
    main()
