# -*- coding: utf-8 -*-
"""S134 F3 - Atribucion del corrimiento del cumulo sobre los pixeles PERSISTIDOS.

FICHA SDA - medicion read-only sobre data/mirova_equivalent/<Vol>.json; no toca la deteccion.

POR QUE. En 9 de 11 Tier A el centroide del cumulo VIIRS375 publicado cae a 2,3-2,8 km del
crater (docs/s133/ANILLO_TIER_A.md). Este script mide, sin granules, en que ETAPA del
ensamblado se corre el cumulo, usando lo que cada record guarda: anomaly_pixels
({lat, lon, bt_k, vrp_mw, dist_km}), primary_cluster, final_hotspot_* y los conteos por
camino (diag_n_*).

LAS DOS PREGUNTAS DEL INSTRUMENTO
 1. Si el cumulo estuviera roto (siempre al flanco), la medicion lo veria: d_crater del
    centroide y del pico saldrian grandes en Villarrica y chicos en Lascar (control positivo).
 2. Si el instrumento estuviera muerto (anomaly_pixels vacio o truncado), se ve distinto:
    se reporta aparte cuantos records NO tienen pixeles (SIN DATO) y cuantos tienen la lista
    al tope de 100 (TRUNCADO). Un record sin pixeles no entra a ninguna mediana.

Ancla: vent_lat/vent_lon de volcanoes.yaml (A13). Ventana: records VIIRS375 (sensor VIIRS_*
sin sufijo _750, convencion A48) con distance_class=summit desde DESDE (default 2026-06-01).
"""
import io, json, math, os, sys, statistics as st
from collections import Counter, defaultdict
import yaml

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
WT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))            # worktree s134-f3
DATA = "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/data/mirova_equivalent"
DESDE = sys.argv[1] if len(sys.argv) > 1 else "2026-06-01"
VOLS = ["Villarrica", "Lascar"]
CONN_KM = 0.56   # 8-vecinos a 375 m: diagonal = 0.53 km; margen por geolocalizacion


def hav(a, b, c, d):
    p = math.pi / 180
    x = math.sin((c - a) * p / 2) ** 2 + math.cos(a * p) * math.cos(c * p) * math.sin((d - b) * p / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(x))


def med(x):
    return round(st.median(x), 3) if x else None


cfg = yaml.safe_load(io.open(os.path.join(WT, "volcanoes.yaml"), encoding="utf-8"))
vols = cfg["volcanoes"] if isinstance(cfg, dict) and "volcanoes" in cfg else cfg
VCFG = {v["name"]: v for v in vols}


def es_v375(s):
    s = str(s or "").upper()
    return s.startswith("VIIRS") and not s.endswith("_750")


def clusters_8vec(px):
    """Union-find por distancia <= CONN_KM (aprox. 8-conectividad en grilla 375 m)."""
    n = len(px)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i in range(n):
        for j in range(i + 1, n):
            if hav(px[i]["lat"], px[i]["lon"], px[j]["lat"], px[j]["lon"]) <= CONN_KM:
                ri, rj = find(i), find(j)
                if ri != rj:
                    parent[ri] = rj
    g = defaultdict(list)
    for i in range(n):
        g[find(i)].append(i)
    return list(g.values())


def analiza_record(r, vlat, vlon, inner):
    px = r.get("anomaly_pixels") or []
    pc = r.get("primary_cluster") or {}
    out = {
        "datetime_utc": r.get("datetime_utc"), "sensor": r.get("sensor"),
        "source": r.get("final_hotspot_source"),
        "n_ap": len(px), "n_anomalous_pixels": r.get("n_anomalous_pixels"),
        "n_test1_pixels": r.get("n_test1_pixels"),
        "pc_n": pc.get("n_pixels"), "pc_vrp": pc.get("vrp_mw"),
        "f5_core_vrp_mw": r.get("f5_core_vrp_mw"), "vrp_mw": r.get("vrp_mw"),
        "single_pixel_mode": pc.get("single_pixel_mode"),
        "discarded_reason": r.get("discarded_reason"),
        "d_pc": None, "d_final": None, "d_peak": None, "d_geo": None, "d_w": None,
        "match": None, "frac_E_075": None, "bt_far_med": None, "bt_near_med": None,
        "t_bg_k": r.get("t_bg_k"), "t_max_k": r.get("t_max_k"),
        "n_fp": r.get("diag_n_first_pass_pixels"), "n_sp": r.get("diag_n_second_pass_recapture"),
        "n_bt": r.get("diag_n_bt_path"), "n_dnti": r.get("diag_n_dnti_ctx_path"),
        "d_pxmin": None, "d_pxmax": None,
    }
    if pc.get("centroid_lat") is not None:
        out["d_pc"] = round(hav(pc["centroid_lat"], pc["centroid_lon"], vlat, vlon), 3)
    if r.get("final_hotspot_lat") is not None:
        out["d_final"] = round(hav(r["final_hotspot_lat"], r["final_hotspot_lon"], vlat, vlon), 3)
    if not px or pc.get("centroid_lat") is None:
        return out
    dv = [hav(p["lat"], p["lon"], vlat, vlon) for p in px]
    out["d_pxmin"], out["d_pxmax"] = round(min(dv), 3), round(max(dv), 3)
    # reconstruir el cumulo publicado: el grupo 8-vec cuyo centroide geometrico cae mas cerca
    # de pc.centroid (cluster_hotspots.py:102-103 usa la media aritmetica de lat/lon)
    grupos = clusters_8vec(px)
    best, bestd = None, 1e9
    for g in grupos:
        gl = sum(px[i]["lat"] for i in g) / len(g)
        go = sum(px[i]["lon"] for i in g) / len(g)
        d = hav(gl, go, pc["centroid_lat"], pc["centroid_lon"])
        if d < bestd:
            best, bestd = g, d
    out["match_geo_km"] = round(bestd, 3)          # 0 si el centroide geometrico reproduce pc
    out["n_grupos"] = len(grupos)
    out["n_grupo_pc"] = len(best)
    g = [px[i] for i in best]
    gl = sum(p["lat"] for p in g) / len(g); go = sum(p["lon"] for p in g) / len(g)
    W = sum(p["vrp_mw"] or 0 for p in g)
    if W > 0:
        wl = sum(p["lat"] * (p["vrp_mw"] or 0) for p in g) / W
        wo = sum(p["lon"] * (p["vrp_mw"] or 0) for p in g) / W
        out["d_w"] = round(hav(wl, wo, vlat, vlon), 3)
        out["match_w_km"] = round(hav(wl, wo, pc["centroid_lat"], pc["centroid_lon"]), 3)
    pk = max(g, key=lambda p: p["vrp_mw"] or 0)
    out["d_geo"] = round(hav(gl, go, vlat, vlon), 3)
    out["d_peak"] = round(hav(pk["lat"], pk["lon"], vlat, vlon), 3)
    out["bt_peak"] = pk.get("bt_k")
    near = [p for p in g if hav(p["lat"], p["lon"], pk["lat"], pk["lon"]) <= 0.75]
    far = [p for p in g if p not in near]
    if W > 0:
        out["frac_E_075"] = round(sum(p["vrp_mw"] or 0 for p in near) / W, 3)
    out["bt_near_med"] = med([p["bt_k"] for p in near])
    out["bt_far_med"] = med([p["bt_k"] for p in far])
    return out


def bucket(d):
    if d is None:
        return "sin_dato"
    return "<1" if d < 1 else ("1-2" if d < 2 else ("2-3" if d < 3 else ">=3"))


res = {"desde": DESDE, "conn_km": CONN_KM, "por_volcan": {}}
for vol in VOLS:
    v = VCFG[vol]
    vlat, vlon, inner = v["vent_lat"], v["vent_lon"], v["inner_radius_km"]
    d = json.load(io.open(os.path.join(DATA, vol + ".json"), encoding="utf-8"))
    recs = d["records"] if isinstance(d, dict) and "records" in d else d
    sel = [r for r in recs if isinstance(r, dict) and str(r.get("datetime_utc") or "")[:10] >= DESDE
           and es_v375(r.get("sensor")) and r.get("distance_class") == "summit"]
    filas = [analiza_record(r, vlat, vlon, inner) for r in sel]
    R = {"ancla": [vlat, vlon], "inner_km": inner, "n_summit_v375": len(sel)}

    # --- instrumento ---
    con_px = [f for f in filas if f["n_ap"] > 0]
    R["instrumento"] = {
        "n_sin_anomaly_pixels": len(filas) - len(con_px),
        "n_con_anomaly_pixels": len(con_px),
        "n_truncados_a_100": sum(1 for f in filas if f["n_ap"] >= 100),
        "n_ap_eq_n_anomalous": sum(1 for f in filas if f["n_ap"] == (f["n_anomalous_pixels"] or 0)),
        "n_ap_lt_n_test1": sum(1 for f in filas if f["source"] == "test1_roi" and f["n_test1_pixels"]
                               and f["n_ap"] < f["n_test1_pixels"]),
        "match_geo_le_10m": sum(1 for f in con_px if f.get("match_geo_km") is not None and f["match_geo_km"] <= 0.01),
        "match_w_le_10m": sum(1 for f in con_px if f.get("match_w_km") is not None and f["match_w_km"] <= 0.01),
        "multi_px_con_match": sum(1 for f in con_px if (f.get("n_grupo_pc") or 0) > 1 and f.get("match_geo_km") is not None),
        "multi_px_match_geo_le_10m": sum(1 for f in con_px if (f.get("n_grupo_pc") or 0) > 1 and f.get("match_geo_km") is not None and f["match_geo_km"] <= 0.01),
        "multi_px_match_w_le_10m": sum(1 for f in con_px if (f.get("n_grupo_pc") or 0) > 1 and f.get("match_w_km") is not None and f["match_w_km"] <= 0.01),
    }
    # --- por fuente ---
    por_src = defaultdict(list)
    for f in filas:
        por_src[f["source"]].append(f)
    R["por_source"] = {}
    for s, fs in por_src.items():
        R["por_source"][s] = {
            "n": len(fs),
            "d_pc_med": med([f["d_pc"] for f in fs if f["d_pc"] is not None]),
            "d_final_med": med([f["d_final"] for f in fs if f["d_final"] is not None]),
            "d_peak_med": med([f["d_peak"] for f in fs if f["d_peak"] is not None]),
            "d_geo_med": med([f["d_geo"] for f in fs if f["d_geo"] is not None]),
            "d_w_med": med([f["d_w"] for f in fs if f["d_w"] is not None]),
            "pc_n_med": med([f["pc_n"] for f in fs if f["pc_n"] is not None]),
            "frac_single_px": round(sum(1 for f in fs if f["pc_n"] == 1) / len(fs), 3),
            "n_fp_med": med([f["n_fp"] for f in fs if f["n_fp"] is not None]),
            "n_sp_med": med([f["n_sp"] for f in fs if f["n_sp"] is not None]),
            "n_test1_med": med([f["n_test1_pixels"] for f in fs if f["n_test1_pixels"] is not None]),
            "n_ap_med": med([f["n_ap"] for f in fs]),
            "d_pxmin_med": med([f["d_pxmin"] for f in fs if f["d_pxmin"] is not None]),
            "d_pxmax_med": med([f["d_pxmax"] for f in fs if f["d_pxmax"] is not None]),
            "frac_E_075_med": med([f["frac_E_075"] for f in fs if f["frac_E_075"] is not None]),
            "bt_peak_med": med([f["bt_peak"] for f in fs if f.get("bt_peak") is not None]),
            "bt_far_med": med([f["bt_far_med"] for f in fs if f["bt_far_med"] is not None]),
            "t_bg_med": med([f["t_bg_k"] for f in fs if f["t_bg_k"] is not None]),
            "discarded": dict(Counter(f["discarded_reason"] for f in fs)),
        }
    # --- cruce d_crater x camino ---
    R["por_bucket_d_pc"] = {}
    for b in ("<1", "1-2", "2-3", ">=3", "sin_dato"):
        fs = [f for f in filas if bucket(f["d_pc"]) == b]
        if not fs:
            continue
        R["por_bucket_d_pc"][b] = {
            "n": len(fs),
            "sources": dict(Counter(f["source"] for f in fs)),
            "n_fp_med": med([f["n_fp"] for f in fs if f["n_fp"] is not None]),
            "frac_fp_gt0": round(sum(1 for f in fs if (f["n_fp"] or 0) > 0) / len(fs), 3),
            "n_sp_med": med([f["n_sp"] for f in fs if f["n_sp"] is not None]),
            "frac_sp_gt0": round(sum(1 for f in fs if (f["n_sp"] or 0) > 0) / len(fs), 3),
            "n_bt_med": med([f["n_bt"] for f in fs if f["n_bt"] is not None]),
            "pc_n_med": med([f["pc_n"] for f in fs if f["pc_n"] is not None]),
            "d_peak_med": med([f["d_peak"] for f in fs if f["d_peak"] is not None]),
            "d_pxmin_med": med([f["d_pxmin"] for f in fs if f["d_pxmin"] is not None]),
            "f5_med": med([f["f5_core_vrp_mw"] for f in fs if f["f5_core_vrp_mw"] is not None]),
        }
    # --- histograma de distancia de TODOS los pixeles persistidos al crater (test1_roi) ---
    hist = Counter()
    for r, f in zip(sel, filas):
        if f["source"] != "test1_roi":
            continue
        for p in (r.get("anomaly_pixels") or []):
            dd = hav(p["lat"], p["lon"], vlat, vlon)
            hist[min(int(dd * 2) / 2, 5.0)] += 1     # bins de 0,5 km, tope 5
    R["hist_px_test1_roi_km"] = {str(k): hist[k] for k in sorted(hist)}
    R["filas"] = filas
    res["por_volcan"][vol] = R

    # --- impresion ---
    print("=" * 100)
    print(f"{vol}  ancla vent=({vlat},{vlon}) inner={inner} km  VIIRS375 summit desde {DESDE}: n={len(sel)}")
    print("instrumento:", json.dumps(R["instrumento"]))
    print("por source:")
    for s, x in R["por_source"].items():
        print(f"  {s!s:14} n={x['n']:3}  d_pc={x['d_pc_med']}  d_final={x['d_final_med']}  d_peak={x['d_peak_med']}  "
              f"d_geo={x['d_geo_med']}  d_w={x['d_w_med']}  pc_n={x['pc_n_med']}  1px={x['frac_single_px']}  "
              f"n_fp={x['n_fp_med']}  n_sp={x['n_sp_med']}  n_t1={x['n_test1_med']}  n_ap={x['n_ap_med']}  "
              f"d_pxmin={x['d_pxmin_med']}  d_pxmax={x['d_pxmax_med']}  bt_peak={x['bt_peak_med']}  t_bg={x['t_bg_med']}  disc={x['discarded']}")
    print("por bucket d_pc:")
    for b, x in R["por_bucket_d_pc"].items():
        print(f"  {b:8} n={x['n']:3} src={x['sources']} fp>0={x['frac_fp_gt0']} sp>0={x['frac_sp_gt0']} "
              f"pc_n={x['pc_n_med']} d_peak={x['d_peak_med']} d_pxmin={x['d_pxmin_med']} f5={x['f5_med']}")
    print("hist px test1_roi (km->n):", R["hist_px_test1_roi_km"])

json.dump(res, io.open(os.path.join(HERE, "resultados.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("\n->", os.path.join(HERE, "resultados.json"))
