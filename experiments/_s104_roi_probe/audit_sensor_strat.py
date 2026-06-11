"""S106 — Re-audit del A/B fondo-local ESTRATIFICADO por sensor (pedido Nicolás).

El audit original (audit_local_sweep.py) contaba noches ALERTA de CUALQUIER sensor
del CSV MIROVA contra nuestros records VIIRS375 → mezcla de universos. Acá:
- universo de noches ALERTA separado por Sensor del CSV (MODIS / VIIRS / VIIRS375)
- métrica decisiva (Test1 vivo en noche ALERTA) solo contra noches VIIRS375
- recall simple ídem.

Uso: python audit_sensor_strat.py
"""
import csv
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from audit_local_sweep import load, v375

ROOT = Path(__file__).resolve().parents[2]
BASE = Path(__file__).parent
VOLS = ["Tupungatito", "Villarrica", "Llaima", "Lascar", "Lastarria"]
ARMS = [("MIR-anillo", "baseline_mir"), ("local-k2.0", "local_k20"),
        ("local-k2.5", "local_k25"), ("local-k3.0", "local_k30")]


def alert_nights_by_sensor():
    nights = defaultdict(lambda: defaultdict(set))
    rows = csv.DictReader(open(ROOT / "latest_consolidado.csv",
                               encoding="utf-8", errors="replace"))
    for r in rows:
        if r["Volcan"] in VOLS and r["Tipo_Registro"] == "ALERTA_TERMICA":
            day = (r["Fecha_Satelite_UTC"] or "")[:10]
            if day:
                nights[r["Volcan"]][r["Sensor"]].add(day)
    return nights


def table(title, nights, fn):
    print()
    print(title)
    print(f"{'vol':<13}" + "".join(f"{label:>12}" for label, _ in ARMS))
    for vol in VOLS:
        n375 = nights[vol]["VIIRS375"]
        row = f"{vol:<13}"
        for _, arm_dir in ARMS:
            recs = v375(load(BASE / arm_dir, vol))
            hit = sum(1 for nd in n375 if fn(recs, nd))
            row += f"{hit}/{len(n375)}".rjust(12)
        print(row)


def main():
    nights = alert_nights_by_sensor()
    print("Noches ALERTA por sensor (universo del CSV):")
    for vol in VOLS:
        s = nights[vol]
        union = set().union(*s.values()) if s else set()
        print(f"  {vol:<13} MODIS:{len(s['MODIS']):>3}  VIIRS:{len(s['VIIRS']):>3}"
              f"  VIIRS375:{len(s['VIIRS375']):>3}  union:{len(union):>3}")

    table("Test1 disparado en noches ALERTA *VIIRS375* (manzanas con manzanas):",
          nights,
          lambda recs, nd: any((r.get("datetime_utc") or "")[:10] == nd
                               and r.get("triggered_test1") for r in recs))
    table("Recall simple (>=1 record nuestro) en noches ALERTA VIIRS375:",
          nights,
          lambda recs, nd: any((r.get("datetime_utc") or "")[:10] == nd
                               for r in recs))


if __name__ == "__main__":
    main()
