"""S106 — Probe del diseño "ancla espacial honesta" (sobre data en disco, A2).

Hipótesis del diseño: los píxeles de los paths contextuales (dNTI/ETI, los
MIROVA-reales, inmunes a topografía per A69) están bien anclados al cráter en
nevados y al campo fumarólico real en Lastarria. Si es así, anclar la POSICIÓN
del record en ellos (y no en el centroide del Test1-MIR) cura D11 sin tocar
sensibilidad.

Mide, por volcán (baseline_mir, VIIRS375):
  1. composición: records con píxeles contextuales (anomaly_pixels>0) vs
     Test1-only vs nada.
  2. offN/dist mediana del píxel contextual de mayor VRP por record (el ancla
     candidata) vs el ancla actual (final_hotspot).
  3. en noches ALERTA VIIRS375: ¿cuántas tienen >=1 record con píxel contextual?
     (si la noche real es Test1-only, el ancla caería al fallback vent/NTI-peak).

Uso: python probe_anchor_design.py
"""
import csv
import statistics
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from audit_local_sweep import load, v375, hav, VENT

ROOT = Path(__file__).resolve().parents[2]
BASE = Path(__file__).parent
VOLS = ["Tupungatito", "Villarrica", "Llaima", "Lascar", "Lastarria"]


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


def med(xs):
    return statistics.median(xs) if xs else None


def fmt(x, spec=".0f"):
    return format(x, spec) if x is not None else "—"


def main():
    for vol in VOLS:
        vlat, vlon = VENT[vol]
        recs = v375(load(BASE / "baseline_mir", vol))
        with_ctx, t1_only, neither = [], [], []
        for r in recs:
            if r.get("anomaly_pixels"):
                with_ctx.append(r)
            elif r.get("triggered_test1"):
                t1_only.append(r)
            else:
                neither.append(r)

        # ancla candidata: pixel contextual de mayor VRP del record
        offN_ctx, dist_ctx = [], []
        for r in with_ctx:
            px = max(r["anomaly_pixels"], key=lambda p: p.get("vrp_mw") or 0)
            offN_ctx.append((px["lat"] - vlat) * 111320)
            dist_ctx.append(hav(vlat, vlon, px["lat"], px["lon"]))

        # ancla actual de los MISMOS records (para comparar como-con-como)
        offN_cur = [(r["final_hotspot_lat"] - vlat) * 111320
                    for r in with_ctx if r.get("final_hotspot_lat") is not None]
        # ancla actual de los Test1-only (la fuente del sesgo)
        offN_t1 = [(r["final_hotspot_lat"] - vlat) * 111320
                   for r in t1_only if r.get("final_hotspot_lat") is not None]
        dist_t1 = [hav(vlat, vlon, r["final_hotspot_lat"], r["final_hotspot_lon"])
                   for r in t1_only if r.get("final_hotspot_lat") is not None]

        nights = alert_nights_v375(vol)
        n_ctx_night = sum(1 for nd in nights if any(
            (r.get("datetime_utc") or "")[:10] == nd for r in with_ctx))
        n_t1only_night = sum(1 for nd in nights
                             if not any((r.get("datetime_utc") or "")[:10] == nd
                                        for r in with_ctx)
                             and any((r.get("datetime_utc") or "")[:10] == nd
                                     for r in t1_only))

        print(f"\n=== {vol} ===")
        print(f"  composicion: ctx={len(with_ctx)}  test1-only={len(t1_only)}"
              f"  ninguno={len(neither)}  (de {len(recs)})")
        print(f"  ancla CANDIDATA (pixel ctx max-vrp): offN={fmt(med(offN_ctx))} m"
              f"  dist={fmt(med(dist_ctx), '.2f')} km  (n={len(offN_ctx)})")
        print(f"  ancla ACTUAL en esos records:        offN={fmt(med(offN_cur))} m")
        print(f"  ancla ACTUAL en Test1-only:          offN={fmt(med(offN_t1))} m"
              f"  dist={fmt(med(dist_t1), '.2f')} km  (n={len(offN_t1)})")
        print(f"  noches ALERTA V375: {len(nights)} | con pixel ctx: {n_ctx_night}"
              f" | solo-Test1: {n_t1only_night}")


if __name__ == "__main__":
    main()
