"""S102 — Audit R3 independiente post-promoción nadir-fijo MODIS.

Lee data/mirova_equivalent/ (DESPUÉS del merge_promote_nadir.py) y compara los
records MODIS contra el ground truth MIROVA-MODIS (latest_consolidado.csv).

Por volcán (11 Tier A), sobre la ventana 2026-01-29..2026-06-04:
  - RATIO mediana: nuestro pc.vrp_mw / MIROVA VRP_MW en días con MIROVA-MODIS
    confirmado (A10: pc.vrp_mw, NO record.vrp_mw).
  - FN: días con MIROVA-MODIS ALERTA y SIN detección nuestra (pc.vrp>0).
  - Residuo path D: records MODIS >20 MW SIN MIROVA ese día (artefacto).

Criterio de aceptación (design doc §6 / §10.6): Lascar ratio ~0.9× (no 2.79×),
0 FN nuevos, residuo acotado (PCC ~60, resto <=19). VIIRS no debe cambiar.

Uso: python experiments/_s99_audit/audit_nadir_promote_r3.py
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
# A14: el CSV usa variantes de nombre.
NAMEMAP = {"PuyehueCordonCaulle": "Puyehue-Cordon Caulle",
           "NevadosDeChillan": "Nevados de Chillan",
           "PlanchonPeteroa": "PlanchonPeteroa"}
W0, W1 = "2026-01-29", "2026-06-04"


def _recs(o):
    return o["records"] if isinstance(o, dict) else o


def _pc(r):
    return (r.get("primary_cluster") or {}).get("vrp_mw", 0) or 0


def load_mirova_modis():
    """{vol_csvname: {dia: [VRP_MW,...]}} para Sensor=MODIS ALERTA_TERMICA."""
    m = defaultdict(lambda: defaultdict(list))
    for r in csv.DictReader(open(REPO / "latest_consolidado.csv", encoding="utf-8")):
        if r["Sensor"] == "MODIS" and r["Tipo_Registro"] == "ALERTA_TERMICA":
            day = r["Fecha_Satelite_UTC"][:10]
            if W0 <= day <= W1:
                try:
                    m[r["Volcan"]][day].append(float(r["VRP_MW"]))
                except (ValueError, KeyError):
                    pass
    return m


def main():
    mir = load_mirova_modis()
    print(f"=== Audit R3 nadir-fijo MODIS (ventana {W0}..{W1}) ===")
    print(f"{'Volcan':<20} {'ratio_med':>9} {'n':>4} {'FN':>4} {'resid>20':>8} {'max_resid':>9}")
    for vol in VOLS:
        f = REPO / "data/mirova_equivalent" / f"{vol}.json"
        if not f.exists():
            print(f"{vol:<20} FALTA json")
            continue
        recs = [r for r in _recs(json.load(open(f, encoding="utf-8")))
                if str(r.get("sensor", "")).startswith("MODIS")
                and W0 <= str(r.get("datetime_utc", ""))[:10] <= W1]
        # nuestra detección por día (max pc.vrp del día)
        ours_day = defaultdict(float)
        for r in recs:
            d = str(r.get("datetime_utc", ""))[:10]
            ours_day[d] = max(ours_day[d], _pc(r))
        mir_vol = mir.get(NAMEMAP.get(vol, vol), {})
        # ratio en días confirmados MIROVA-MODIS
        ratios, fn = [], 0
        for day, vrps in mir_vol.items():
            mir_vrp = max(vrps)
            ours = ours_day.get(day, 0)
            if ours > 0 and mir_vrp > 0:
                ratios.append(ours / mir_vrp)
            elif ours == 0:
                fn += 1
        # residuo path D: nuestro >20 MW sin MIROVA ese día
        resid = [(d, v) for d, v in ours_day.items() if v > 20 and d not in mir_vol]
        rmax = max((v for _, v in resid), default=0)
        rmed = statistics.median(ratios) if ratios else float("nan")
        print(f"{vol:<20} {rmed:>9.2f} {len(ratios):>4} {fn:>4} {len(resid):>8} {rmax:>9.1f}")
    print("\nAceptación: Lascar ratio ~0.9 (no 2.79), 0 FN nuevos, residuo PCC ~60 resto <=19.")


if __name__ == "__main__":
    main()
