"""S106 — Detalle de los records VIIRS375 de Villarrica en noches ALERTA (baseline).

¿Por qué el primary_cluster está a ~2.8 km del cráter en noches de lava confirmada,
si MIROVA publica el hotspot a 0.84 km? Dump por pasada: píxeles contextuales
(posición/dist/BT/vrp), cluster, ancla actual y diagnósticos NTI.

Uso: python probe_villarrica_alert_detail.py
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from audit_local_sweep import load, v375, hav, VENT

ROOT = Path(__file__).resolve().parents[2]
BASE = Path(__file__).parent
VOL = "Villarrica"


def alert_nights_v375(vol):
    out = set()
    rows = csv.DictReader(open(ROOT / "latest_consolidado.csv",
                               encoding="utf-8", errors="replace"))
    for r in rows:
        if (r["Volcan"] == vol and r["Tipo_Registro"] == "ALERTA_TERMICA"
                and r["Sensor"] == "VIIRS375"):
            day = (r["Fecha_Satelite_UTC"] or "")[:10]
            if day:
                out.add(day)
    return out


def main():
    vlat, vlon = VENT[VOL]
    nights = alert_nights_v375(VOL)
    recs = [r for r in v375(load(BASE / "baseline_mir", VOL))
            if (r.get("datetime_utc") or "")[:10] in nights]
    print(f"{len(recs)} records en {len(nights)} noches ALERTA V375")
    for r in sorted(recs, key=lambda x: x["datetime_utc"]):
        pc = r.get("primary_cluster") or {}
        fh = r.get("final_hotspot_dist_km")
        print(f"\n{r['datetime_utc']} {r['sensor']}  t1={r.get('triggered_test1')}"
              f" src={r.get('final_hotspot_source')}"
              f" fh_dist={fh:.2f}km" if fh is not None else "fh=None")
        print(f"  n_dnti={r.get('n_dnti_ctx_path')} n_test1px={r.get('n_test1_pixels')}"
              f" nti_max={r.get('nti_max')} diag_tmax_dist={r.get('diag_t_max_dist_km')}"
              f" vrp={r.get('vrp_mw')} pc_vrp={pc.get('vrp_mw')}"
              f" pc_dist={pc.get('centroid_dist_km')} pc_npx={pc.get('n_pixels')}")
        for px in (r.get("anomaly_pixels") or [])[:6]:
            d = hav(vlat, vlon, px["lat"], px["lon"])
            off_n = (px["lat"] - vlat) * 111320
            print(f"    px dist={d:.2f}km offN={off_n:.0f}m bt={px.get('bt_k')}"
                  f" vrp={px.get('vrp_mw')}")


if __name__ == "__main__":
    main()
