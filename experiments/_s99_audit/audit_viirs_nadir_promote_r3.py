"""S103 — Audit R3 independiente post-promoción nadir-fijo VIIRS.

Espejo de audit_nadir_promote_r3.py (S102 MODIS). Lee data/mirova_equivalent/
(DESPUÉS de merge_promote_viirs_nadir.py) y compara los records VIIRS contra el
ground truth MIROVA-VIIRS (latest_consolidado.csv).

BUCKETING DE SENSOR (verificado S103, A48 — el subagente S77 lo erró):
  - MIROVA CSV: Sensor 'VIIRS375' = I-band 375m | Sensor 'VIIRS' = M-band 750m.
  - Nuestros records: VIIRS_SNPP/NOAA20/NOAA21 = 375m (sin sufijo);
    VIIRS_*_750 = 750m.

Por volcán (11 Tier A) y POR SENSOR (375 / 750), sobre 2026-01-29..2026-06-07:
  - RATIO mediana: nuestro pc.vrp_mw / MIROVA VRP_MW en días confirmados (A10).
  - FN: días con MIROVA-VIIRS ALERTA de ese sensor y SIN detección nuestra.
  - Residuo: días con detección nuestra (pc>0) SIN MIROVA ese día (over-detección).

Criterio de aceptación (design doc 2026-06-06 §5bis):
  - VIIRS375 global ~0.78× (no 1.95×), 0 FN nuevos VIIRS375.
  - VIIRS750 ~0.80×; residuo glaciar path D (Tupun/PP/Isluga) PERSISTE = §2 path D.
  - MODIS NO debe cambiar (byte-idéntico; lo verifica el merge).

Uso: python experiments/_s99_audit/audit_viirs_nadir_promote_r3.py
"""
import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
VOLS = ["Lascar", "PuyehueCordonCaulle", "Tupungatito", "Chaiten", "Villarrica",
        "Llaima", "PlanchonPeteroa", "Copahue", "Isluga", "Lastarria",
        "NevadosDeChillan"]
NAMEMAP = {"PuyehueCordonCaulle": "Puyehue-Cordon Caulle",
           "NevadosDeChillan": "Nevados de Chillan",
           "PlanchonPeteroa": "PlanchonPeteroa"}
W0, W1 = "2026-01-29", "2026-06-07"

# Mapeo Sensor MIROVA CSV -> bucket
CSV_BUCKET = {"VIIRS375": "375", "VIIRS": "750"}


def _recs(o):
    return o["records"] if isinstance(o, dict) else o


def _pc(r):
    return (r.get("primary_cluster") or {}).get("vrp_mw", 0) or 0


def _our_bucket(sensor):
    s = str(sensor)
    if not s.startswith("VIIRS"):
        return None
    return "750" if s.endswith("_750") else "375"


def load_mirova_viirs():
    """{vol_csvname: {bucket: {dia: [VRP_MW,...]}}} para VIIRS ALERTA_TERMICA."""
    m = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for r in csv.DictReader(open(REPO / "latest_consolidado.csv", encoding="utf-8")):
        b = CSV_BUCKET.get(r.get("Sensor", ""))
        if b and r.get("Tipo_Registro") == "ALERTA_TERMICA":
            day = r["Fecha_Satelite_UTC"][:10]
            if W0 <= day <= W1:
                try:
                    m[r["Volcan"]][b][day].append(float(r["VRP_MW"]))
                except (ValueError, KeyError):
                    pass
    return m


def main():
    mir = load_mirova_viirs()
    print(f"=== Audit R3 nadir-fijo VIIRS (ventana {W0}..{W1}) ===")
    print(f"{'Volcan':<20} {'sens':>4} {'ratio_med':>9} {'n':>4} {'FN':>4} {'resid':>6} {'max_res':>8}")
    glob = defaultdict(list)  # bucket -> [ratios] (global)
    glob_fn = defaultdict(int)
    for vol in VOLS:
        f = REPO / "data/mirova_equivalent" / f"{vol}.json"
        if not f.exists():
            print(f"{vol:<20} FALTA json")
            continue
        all_recs = _recs(json.load(open(f, encoding="utf-8")))
        mir_vol = mir.get(NAMEMAP.get(vol, vol), {})
        for b in ("375", "750"):
            recs = [r for r in all_recs
                    if _our_bucket(r.get("sensor")) == b
                    and W0 <= str(r.get("datetime_utc", ""))[:10] <= W1]
            ours_day = defaultdict(float)
            for r in recs:
                d = str(r.get("datetime_utc", ""))[:10]
                ours_day[d] = max(ours_day[d], _pc(r))
            mir_b = mir_vol.get(b, {})
            ratios, fn = [], 0
            for day, vrps in mir_b.items():
                mir_vrp = max(vrps)
                ours = ours_day.get(day, 0)
                if ours > 0 and mir_vrp > 0:
                    ratios.append(ours / mir_vrp)
                elif ours == 0:
                    fn += 1
            resid = [(d, v) for d, v in ours_day.items() if v > 0 and d not in mir_b]
            rmax = max((v for _, v in resid), default=0)
            rmed = statistics.median(ratios) if ratios else float("nan")
            glob[b].extend(ratios)
            glob_fn[b] += fn
            print(f"{vol:<20} {b:>4} {rmed:>9.2f} {len(ratios):>4} {fn:>4} {len(resid):>6} {rmax:>8.1f}")
    print("-" * 60)
    for b in ("375", "750"):
        gm = statistics.median(glob[b]) if glob[b] else float("nan")
        print(f"{'GLOBAL':<20} {b:>4} {gm:>9.2f} {len(glob[b]):>4} {glob_fn[b]:>4}")
    print("\nAceptación: VIIRS375 global ~0.78 (no 1.95), 0 FN nuevos; VIIRS750 ~0.80")
    print("(residuo glaciar Tupun/PP/Isluga en 750 PERSISTE = §2 path D, frente aparte).")


if __name__ == "__main__":
    main()
