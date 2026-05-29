"""S88 — Re-selección offline `vent_anchored` sobre pixeles persistidos.

Contexto (cierre S87): la validación 1:1 anomalía dominante dio vent_anchored
74.7% global, pero esa columna leyó el `primary_cluster` PERSISTIDO, que mezcla
épocas de estrategia (pre-S38 `vrp_max` vs post-S38 `vent_anchored`). El "67% de
Lascar" quedó como piso contaminado por records eruptivos de febrero generados
con la estrategia vieja.

Este script responde dos preguntas SIN reproceso, 100% offline:

  (1) FRENTE A-LITE — ¿cuánto sube el match si re-aplico la lógica `vent_anchored`
      ACTUAL a los `anomaly_pixels` persistidos (en vez de leer el primary stale)?
      Es un PISO ESTRICTO del pipeline actual (A18: la re-selección offline no
      reproduce 1:1 el cluster real porque opera sobre el top-N ya guardado, no
      sobre el hot_mask completo del grid; pero como el pipeline de hoy produce
      una nube MÁS limpia — gates intra-radio S84/S85, bt_path off — solo puede
      matchear igual o mejor que re-clusterizar los pixeles viejos más sucios).

  (2) DECOMPOSICIÓN LASCAR FEB — para cada no-match eruptivo, ¿el cráter está
      PRESENTE en la escena persistida (→ selection-stale, recuperable en disco)
      o AUSENTE (→ detection-loss, requiere reproceso real desde L1B)? Esto decide
      si el reproceso local MODIS caro (Frente A) vale la pena y cuántos records
      flipearía.

NO toca pipeline NRT. Importa `cluster_pixels_geographic` + `load_mirova_alertas`
ya existentes. Espeja la lógica de ranking `vent_anchored` de
pipeline/clustering.py:cluster_hotspots (S38 D8 fix + S43 filtro vrp>0).
"""
from __future__ import annotations

import io
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd
import yaml

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from pipeline.mirova_csv_loader import load_mirova_alertas  # noqa: E402
from pipeline.clustering import cluster_pixels_geographic  # noqa: E402

CHILE_TZ = "America/Santiago"
CONS = ROOT / "data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv"
OCR = ROOT / "data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv"
TOL_MAIN = 2.0


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    p = math.radians
    dlat = p(lat2 - lat1)
    dlon = p(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(p(lat1)) * math.cos(p(lat2)) * math.sin(dlon / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(a))


# --- volcanoes.yaml: mirova_center + inner_radius por Tier A ---
VY = yaml.safe_load((ROOT / "volcanoes.yaml").read_text(encoding="utf-8"))
TIERA = {}
for v in VY["volcanoes"]:
    if v.get("mirova_monitored"):
        TIERA[v["name"]] = {
            "mc_lat": float(v["mirova_center_lat"]),
            "mc_lon": float(v["mirova_center_lon"]),
            "inner": float(v.get("inner_radius_km", 5.0)),
        }
TIERA_NAMES = sorted(TIERA)


def json_sensor_bucket(s: str):
    s = (s or "").upper()
    if s.startswith("MODIS"):
        return "MODIS"
    if s.startswith("VIIRS") and s.endswith("_750"):
        return "VIIRS750"
    if s.startswith("VIIRS"):
        return "VIIRS375"
    return None


def reselect_vent_anchored(clusters, mc_lat, mc_lon, inner):
    """Espeja pipeline/clustering.py:cluster_hotspots ranking vent_anchored.

    clusters: salida de cluster_pixels_geographic (tiene vrp_mw, centroid_lat/lon).
    Calcula dist de cada cluster desde mirova_center (= effective vent para Tier A,
    get_effective_vent prioriza mirova_center). Aplica S43 filtro vrp>0 + ranking
    (inside inner ? 0:1, dist asc, -vrp). Devuelve el cluster primary (o None).
    """
    if not clusters:
        return None
    enriched = []
    for c in clusters:
        d = haversine_km(mc_lat, mc_lon, c["centroid_lat"], c["centroid_lon"])
        enriched.append({**c, "dist_mc": d})
    # S43: si hay clusters con vrp>0, ignorar los vrp==0 al rankear.
    with_vrp = [c for c in enriched if c.get("vrp_mw", 0.0) > 0]
    ranking_set = with_vrp if with_vrp else enriched

    def key(c):
        inside = c["dist_mc"] <= inner
        return (0 if inside else 1, c["dist_mc"], -c.get("vrp_mw", 0.0))

    ranking_set.sort(key=key)
    return ranking_set[0]


# ---------------------------------------------------------------------------
# 1. MIROVA dominante por (vol, sensor, noche)
# ---------------------------------------------------------------------------
mirova_all = load_mirova_alertas(str(CONS), str(OCR))
mirova_df = pd.DataFrame(mirova_all)
mirova_df["dt"] = pd.to_datetime(mirova_df["fecha_utc"], utc=True, errors="coerce")
mirova_df = mirova_df[mirova_df["dt"].notna()].copy()
mirova_df["night"] = mirova_df["dt"].dt.tz_convert(CHILE_TZ).dt.date

mirova_dominant = {}
for (vol, sb, night), g in mirova_df.groupby(["volcano", "sensor_bucket", "night"]):
    best = g.loc[g["vrp_mw"].idxmax()]
    mirova_dominant[(vol, sb, night)] = {
        "dist_km": float(best["dist_km"]) if pd.notna(best["dist_km"]) else None,
        "vrp_mw": float(best["vrp_mw"]),
        "source": best["source"],
    }


# ---------------------------------------------------------------------------
# 2. Nuestros records: stale primary vs re-selected vent_anchored
# ---------------------------------------------------------------------------
def build():
    out = {}
    for vol in TIERA_NAMES:
        fp = ROOT / "data/mirova_equivalent" / f"{vol}.json"
        if not fp.exists():
            continue
        mc_lat, mc_lon = TIERA[vol]["mc_lat"], TIERA[vol]["mc_lon"]
        inner = TIERA[vol]["inner"]
        data = json.loads(fp.read_text(encoding="utf-8"))
        per_key = defaultdict(list)
        for r in data.get("records", []):
            ap = r.get("anomaly_pixels")
            if not ap:
                continue
            sb = json_sensor_bucket(r.get("sensor", ""))
            if sb is None:
                continue
            dt = pd.to_datetime(r.get("datetime_utc"), utc=True, errors="coerce")
            if pd.isna(dt):
                continue
            night = dt.tz_convert(CHILE_TZ).date()

            clusters = cluster_pixels_geographic(ap, max_dist_km=1.5)
            scene_vrp = clusters[0]["vrp_mw"] if clusters else 0.0

            # stale primary (lo que S87 midió)
            pc = r.get("primary_cluster") or {}
            if pc.get("centroid_lat") is not None:
                stale_dist = haversine_km(mc_lat, mc_lon,
                                          float(pc["centroid_lat"]),
                                          float(pc["centroid_lon"]))
            else:
                stale_dist = None

            # re-selected vent_anchored sobre los pixeles persistidos
            sel = reselect_vent_anchored(clusters, mc_lat, mc_lon, inner)
            resel_dist = sel["dist_mc"] if sel else None
            resel_vrp = sel["vrp_mw"] if sel else None

            # ¿hay algún cluster del cráter (dentro inner) en la escena?
            crater_present = any(
                haversine_km(mc_lat, mc_lon, c["centroid_lat"], c["centroid_lon"]) <= inner
                for c in clusters
            )
            # distancia del cluster MÁS cercano al cráter (para diagnóstico)
            nearest = min(
                (haversine_km(mc_lat, mc_lon, c["centroid_lat"], c["centroid_lon"])
                 for c in clusters), default=None)

            per_key[(vol, sb, night)].append({
                "scene_vrp": scene_vrp,
                "stale_dist": stale_dist,
                "resel_dist": resel_dist,
                "resel_vrp": resel_vrp,
                "crater_present": crater_present,
                "nearest_cluster_km": nearest,
                "datetime": str(dt),
                "n_clusters": len(clusters),
            })
        # por key, el record de mayor VRP de escena (igual que S87)
        for key, lst in per_key.items():
            out[key] = max(lst, key=lambda x: x["scene_vrp"])
    return out


ours = build()


# ---------------------------------------------------------------------------
# 3. Match stale vs re-selected; decomposición Lascar feb
# ---------------------------------------------------------------------------
def match(our_dist, mir_dist, tol=TOL_MAIN):
    if our_dist is None or mir_dist is None:
        return False
    return abs(our_dist - mir_dist) <= tol


per_vol = defaultdict(lambda: {"n": 0, "stale": 0, "resel": 0})
lascar_feb_rows = []

for key, mir in mirova_dominant.items():
    vol, sb, night = key
    o = ours.get(key)
    if o is None or mir["dist_km"] is None:
        continue
    pv = per_vol[vol]
    pv["n"] += 1
    stale_ok = match(o["stale_dist"], mir["dist_km"])
    resel_ok = match(o["resel_dist"], mir["dist_km"])
    if stale_ok:
        pv["stale"] += 1
    if resel_ok:
        pv["resel"] += 1

    # decomposición Lascar febrero (eventos eruptivos MODIS)
    if vol == "Lascar" and str(night)[:7] == "2026-02":
        lascar_feb_rows.append({
            "night": str(night), "sensor": sb,
            "mir_dist": round(mir["dist_km"], 2),
            "stale_dist": round(o["stale_dist"], 2) if o["stale_dist"] is not None else None,
            "resel_dist": round(o["resel_dist"], 2) if o["resel_dist"] is not None else None,
            "stale_ok": stale_ok, "resel_ok": resel_ok,
            "crater_present": o["crater_present"],
            "nearest_km": round(o["nearest_cluster_km"], 2) if o["nearest_cluster_km"] is not None else None,
            "n_clusters": o["n_clusters"],
        })


def pct(a, b):
    return round(100 * a / b, 1) if b else None


print("=== FRENTE A-LITE: re-seleccion vent_anchored offline (tol=2km) ===")
print(f"{'Volcan':<22} {'n':>5} {'stale%':>8} {'resel%':>8} {'dpp':>7}")
summary = {}
for vol in TIERA_NAMES:
    pv = per_vol.get(vol)
    if not pv or pv["n"] == 0:
        continue
    s, r2 = pct(pv["stale"], pv["n"]), pct(pv["resel"], pv["n"])
    delta = round(r2 - s, 1) if (s is not None and r2 is not None) else None
    summary[vol] = {"n": pv["n"], "stale_pct": s, "resel_pct": r2, "delta_pp": delta}
    print(f"{vol:<22} {pv['n']:>5} {str(s):>8} {str(r2):>8} {str(delta):>7}")

tot_n = sum(pv["n"] for pv in per_vol.values())
tot_stale = sum(pv["stale"] for pv in per_vol.values())
tot_resel = sum(pv["resel"] for pv in per_vol.values())
print(f"\n{'GLOBAL':<22} {tot_n:>5} {str(pct(tot_stale,tot_n)):>8} "
      f"{str(pct(tot_resel,tot_n)):>8}")

print("\n=== DECOMPOSICION LASCAR FEBRERO (no-match) ===")
nm = [r for r in lascar_feb_rows if not r["stale_ok"]]
recoverable = [r for r in nm if r["resel_ok"]]
crater_present_still_nm = [r for r in nm if not r["resel_ok"] and r["crater_present"]]
detection_loss = [r for r in nm if not r["resel_ok"] and not r["crater_present"]]
print(f"Lascar feb total comparados: {len(lascar_feb_rows)}")
print(f"  no-match con stale primary:         {len(nm)}")
print(f"  -> recuperables por re-seleccion:   {len(recoverable)} (crater presente, vent_anchored lo elige)")
print(f"  -> crater presente pero aun no-match:{len(crater_present_still_nm)} (gap fisico chico / halo)")
print(f"  -> detection-loss (crater AUSENTE): {len(detection_loss)} (REQUIERE reproceso L1B)")

(OUT / "reselect_results.json").write_text(json.dumps({
    "tol_km": TOL_MAIN,
    "per_vol": summary,
    "global": {"n": tot_n, "stale_pct": pct(tot_stale, tot_n),
               "resel_pct": pct(tot_resel, tot_n)},
    "lascar_feb": {
        "total": len(lascar_feb_rows),
        "no_match_stale": len(nm),
        "recoverable_by_reselect": len(recoverable),
        "crater_present_still_nomatch": len(crater_present_still_nm),
        "detection_loss_needs_reproc": len(detection_loss),
        "rows": lascar_feb_rows,
    },
}, indent=2, default=str), encoding="utf-8")
print("\n[OK] reselect_results.json escrito")
