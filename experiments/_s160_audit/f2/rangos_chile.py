#!/usr/bin/env python
"""Rangos reales en Chile y conteos de recortes, medidos sobre la instantánea de datos de origin/main.

Pregunta 1 del instrumento: si un recorte se comiera el rango, ¿se ve? Sí, porque se cuentan
los records que caen exactamente en el valor del recorte (5,0 MW, 0,0 MW con cúmulo, 70° de
cenit) y se comparan con los que lo superan. Pregunta 2: si el instrumento estuviera muerto,
cada tabla saldría con n = 0; el n se imprime siempre, y el control positivo es que el tope D9
tiene que aparecer con cientos de records en 5,0 exacto (A23, S151: 1.565 en el corpus de
octubre).

Denominador: todos los records de data/mirova_equivalent/*.json de la instantánea (45
volcanes), y aparte la ventana K (observaciones desde 2026-09-18 00:00 UTC, que es desde cuando
los datos de producción llevan el detector K, S155). Salida: rangos_chile.json y rangos_chile.txt.
"""
from __future__ import annotations

import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
RAIZ = Path(r"D:\vrp-trabajo\temporales\s160_audit\main")
DATA = RAIZ / "data" / "mirova_equivalent"
SALIDA = Path(__file__).resolve().parent
K_DESDE = "2026-09-18 00:00"


def bucket(s):
    s = s or ""
    if s.startswith("MODIS"):
        return "MODIS"
    if s.endswith("_750"):
        return "VIIRS750"
    if s.startswith("VIIRS"):
        return "VIIRS375"
    return "?"


def pct(xs, qs=(0, 5, 25, 50, 75, 95, 100)):
    xs = np.asarray([x for x in xs if x is not None and np.isfinite(x)], dtype=float)
    if xs.size == 0:
        return {"n": 0}
    out = {"n": int(xs.size)}
    for q in qs:
        out[f"p{q}"] = round(float(np.percentile(xs, q)), 4)
    return out


def hav(lat1, lon1, lat2, lon2):
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def cargar_volcanes():
    import yaml
    y = yaml.safe_load((RAIZ / "volcanoes.yaml").read_text(encoding="utf-8"))
    vols = y["volcanoes"] if isinstance(y, dict) and "volcanoes" in y else y
    out = {}
    for v in vols:
        out[v["name"]] = v
    return out


def main():
    vols = cargar_volcanes()
    series = defaultdict(lambda: defaultdict(list))   # (ventana, bucket) -> campo -> valores
    cnt = Counter()
    por_vol = defaultdict(Counter)
    capped = []
    cero_con_cumulo = []
    origen = defaultdict(Counter)
    n_total = 0
    for fp in sorted(DATA.glob("*.json")):
        vol = fp.stem
        d = json.load(open(fp, encoding="utf-8"))
        recs = d["records"] if isinstance(d, dict) and "records" in d else d
        if isinstance(recs, dict):
            recs = [r for v in recs.values() for r in (v if isinstance(v, list) else [v])]
        vinfo = vols.get(vol, {})
        inner = vinfo.get("inner_radius_km")
        for r in recs:
            n_total += 1
            b = bucket(r.get("sensor"))
            dt = r.get("datetime_utc") or ""
            ventanas = ["todo"] + (["K"] if dt >= K_DESDE else [])
            pc = r.get("primary_cluster") or {}
            pcv = pc.get("vrp_mw")
            tmax = r.get("t_max_k") if r.get("t_max_k") is not None else r.get("t_max_i04_k")
            for w in ventanas:
                s = series[(w, b)]
                s["t_max_k"].append(tmax)
                s["t_bg_k"].append(r.get("t_bg_k"))
                s["sigma_bg_k"].append(r.get("diag_sigma_bg_k"))
                s["sensor_zenith_deg"].append(r.get("sensor_zenith_deg"))
                s["sd_dnti"].append(r.get("diag_sd_dnti"))
                s["mu_dnti"].append(r.get("diag_mu_dnti"))
                s["sd_deti"].append(r.get("diag_sd_deti"))
                s["nti_max"].append(r.get("diag_nti_max"))
                s["n_bg_first_pass"].append(r.get("diag_n_bg_used_first_pass"))
                s["n_bg_anillo"].append(r.get("diag_n_bg_anillo"))
                if r.get("diag_mu_dnti") is not None and r.get("diag_sd_dnti") is not None:
                    s["mu+5sd_dnti"].append(r["diag_mu_dnti"] + 5 * r["diag_sd_dnti"])
                    s["mu+10sd_dnti"].append(r["diag_mu_dnti"] + 10 * r["diag_sd_dnti"])
                if r.get("diag_mu_deti") is not None and r.get("diag_sd_deti") is not None:
                    s["mu+5sd_deti"].append(r["diag_mu_deti"] + 5 * r["diag_sd_deti"])
                    s["mu+10sd_deti"].append(r["diag_mu_deti"] + 10 * r["diag_sd_deti"])
                if pcv is not None and pcv > 0:
                    s["pc_vrp_mw_pos"].append(pcv)
                    s["pc_n_pixels"].append(pc.get("n_pixels"))
                    s["pc_centroid_dist_km"].append(pc.get("centroid_dist_km"))
                if r.get("f5_core_vrp_mw"):
                    s["f5_core_vrp_mw"].append(r["f5_core_vrp_mw"])
                if r.get("vrp_mw"):
                    s["vrp_mw_pos"].append(r["vrp_mw"])
                # contadores
                k = (w, b)
                cnt[(k, "records")] += 1
                if r.get("t_bg_k") is not None and r["t_bg_k"] < 270:
                    cnt[(k, "t_bg<270")] += 1
                    por_vol[(w, vol)]["t_bg<270"] += 1
                por_vol[(w, vol)]["records"] += 1
                if pc.get("d9_capped"):
                    cnt[(k, "d9_capped")] += 1
                    por_vol[(w, vol)]["d9_capped"] += 1
                    if r.get("distance_class") == "summit":
                        cnt[(k, "d9_capped_summit")] += 1
                        por_vol[(w, vol)]["d9_capped_summit"] += 1
                    if w == "K":
                        capped.append((vol, r.get("sensor"), dt, r.get("t_bg_k"), pc.get("centroid_dist_km"),
                                       r.get("distance_class"), pc.get("n_pixels"), r.get("vrp_mw")))
                if pcv is not None and pcv == 5.0:
                    cnt[(k, "pc_vrp==5.0")] += 1
                if pcv is not None and pcv > 5.0:
                    cnt[(k, "pc_vrp>5")] += 1
                    if r.get("t_bg_k") is not None and r["t_bg_k"] < 270:
                        cnt[(k, "pc_vrp>5 y t_bg<270")] += 1
                if pc and (pc.get("n_pixels") or 0) > 0 and (pcv or 0) == 0:
                    cnt[(k, "cumulo_con_px_y_vrp_0")] += 1
                    por_vol[(w, vol)]["cumulo_vrp_0"] += 1
                    if r.get("distance_class") == "summit":
                        cnt[(k, "cumulo_con_px_y_vrp_0_summit")] += 1
                if pc and (pc.get("n_pixels") or 0) > 0:
                    cnt[(k, "cumulo_con_px")] += 1
                if tmax is not None and tmax > 500:
                    cnt[(k, "t_max>500")] += 1
                if tmax is not None and tmax > 367 and b == "VIIRS375":
                    cnt[(k, "t_max_i04>367")] += 1
                if tmax is not None and tmax > 331 and b == "MODIS":
                    cnt[(k, "t_max>331_modis")] += 1
                if r.get("diag_rejected_sanity_cap_mw") is not None or r.get("diag_pc_rejected_sanity_cap_mw") is not None:
                    cnt[(k, "sanity_cap_anulado")] += 1
                if r.get("vrp_exceeds_sanity_cap"):
                    cnt[(k, "vrp_exceeds_sanity_cap")] += 1
                if (r.get("diag_n_bt_path") or 0) > 0:
                    cnt[(k, "n_bt_path>0")] += 1
                if (r.get("diag_n_nti_path") or 0) > 0:
                    cnt[(k, "n_nti_path>0")] += 1
                if r.get("triggered_test1"):
                    cnt[(k, "triggered_test1")] += 1
                if (r.get("diag_n_second_pass_recapture") or 0) > 0:
                    cnt[(k, "second_pass_recapture>0")] += 1
                if r.get("sensor_zenith_deg") is not None and r["sensor_zenith_deg"] >= 70:
                    cnt[(k, "zenith>=70")] += 1
                if r.get("t_max_i04_k") is not None and r.get("t_max_k") is None:
                    cnt[(k, "t_max_i04_sin_t_max_k")] += 1
                if r.get("diurno") or (r.get("solar_zenith_deg") is not None and r["solar_zenith_deg"] < 90):
                    cnt[(k, "solar_zenith<90")] += 1
                # origen de la distancia: centro vs crater
                if inner is not None and pcv and pcv > 0:
                    pcd = pc.get("centroid_dist_km")
                    hd = r.get("hotspot_dist_km")
                    fd = r.get("final_hotspot_dist_km")
                    px = (r.get("anomaly_pixels") or [{}])[0]
                    pxd = px.get("dist_km") if isinstance(px, dict) else None
                    if pcd is not None and pxd is not None:
                        a = pcd <= inner
                        bb = pxd <= inner
                        origen[(w, b)]["pares"] += 1
                        if a != bb:
                            origen[(w, b)]["clase_distinta(pc_vs_px0)"] += 1
                    if pcd is not None and fd is not None:
                        origen[(w, b)]["pares_pc_final"] += 1
                        if (pcd <= inner) != (fd <= inner):
                            origen[(w, b)]["clase_distinta(pc_vs_final)"] += 1
                            if r.get("distance_class") == "summit":
                                origen[(w, b)]["clase_distinta(pc_vs_final)_summit"] += 1
    # distancia centro-crater por volcan
    dcv = {}
    for name, v in vols.items():
        if v.get("vent_lat") is not None and v.get("lat") is not None:
            dcv[name] = round(hav(v["lat"], v["lon"], v["vent_lat"], v["vent_lon"]), 2)
    res = {
        "n_total_records": n_total,
        "ventana_K_desde": K_DESDE,
        "percentiles": {f"{w}|{b}": {c: pct(v) for c, v in s.items()} for (w, b), s in series.items()},
        "contadores": {f"{w}|{b}|{c}": n for ((w, b), c), n in sorted(cnt.items())},
        "por_volcan": {f"{w}|{v}": dict(c) for (w, v), c in sorted(por_vol.items())},
        "origen_distancia": {f"{w}|{b}": dict(c) for (w, b), c in sorted(origen.items())},
        "dist_centro_crater_km": dcv,
        "capped_K": capped,
    }
    json.dump(res, open(SALIDA / "rangos_chile.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=str)
    with open(SALIDA / "rangos_chile.txt", "w", encoding="utf-8") as fh:
        fh.write(f"records totales: {n_total}\n")
        for (w, b), s in sorted(series.items()):
            fh.write(f"\n== {w} | {b}\n")
            for c, v in s.items():
                fh.write(f"  {c:22s} {pct(v)}\n")
        fh.write("\n== contadores\n")
        for ((w, b), c), n in sorted(cnt.items()):
            fh.write(f"  {w:5s} {b:9s} {c:34s} {n}\n")
        fh.write("\n== por volcan (K)\n")
        for (w, v), c in sorted(por_vol.items()):
            if w == "K":
                fh.write(f"  {v:22s} {dict(c)}\n")
        fh.write("\n== por volcan (todo)\n")
        for (w, v), c in sorted(por_vol.items()):
            if w == "todo":
                fh.write(f"  {v:22s} {dict(c)}\n")
        fh.write("\n== origen de la distancia (centro vs crater)\n")
        for k, c in sorted(origen.items()):
            fh.write(f"  {k} {dict(c)}\n")
        fh.write("\n== distancia centro->crater (km) por volcan\n")
        for k, v in sorted(dcv.items(), key=lambda kv: -kv[1]):
            fh.write(f"  {k:22s} {v}\n")
        fh.write(f"\n== records con tope D9 en ventana K: {len(capped)}\n")
        for c in capped:
            fh.write("  " + " | ".join(str(x) for x in c) + "\n")
    print(open(SALIDA / "rangos_chile.txt", encoding="utf-8").read())


if __name__ == "__main__":
    main()
