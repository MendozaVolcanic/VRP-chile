# -*- coding: utf-8 -*-
"""S159 frente Chillan MODIS: por que el primer pase no marca el crater en las pasadas oblicuas (PREREGISTRO.md).

Corre la funcion de produccion process_modis.calculate_vrp (argumentos de scripts/run_pipeline.py:235-245) con tres
envoltorios en memoria, sin tocar pipeline/ (A75):
  - read_modis_l1b: guarda radiancias y lat/lon tal como las ve el detector;
  - first_pass_tests_2_and_3: llama a la original, replica sus cuentas (replica.py) y exige mascara identica; ademas
    corre la original con la compuerta apagada (F1), con la conectiva min (F2) y con las dos (F3);
  - second_pass_adjacent: idem, con su propio pool de fondo.
Brazos: P (produccion) y B21 (ENABLE_MODIS_B22_PRIMARY=False en el modulo, solo en memoria).
Por pixel a 6 km o menos del ancla guarda DN crudo 21/22/31, BT, NTI, ETI, dNTI, dETI, umbrales y pases.
El record que arma store.append_record (a un temporal) se compara con el publicado en data/.

Solo lectura: store.DATA_DIR va a un temporal, no commitea, borra cada HDF. Sale 2 si falta un granulo o falla algo.
Uso (Linux con pyhdf): EARTHDATA_TOKEN=... VRP_PROFILE=mirova_equivalent python probe_chillan.py --out out
"""
import argparse
import copy
import importlib.util
import inspect
import json
import math
import os
import sys
import tempfile
import time
import traceback
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(AQUI))

from replica import replicar_first_pass, replicar_second_pass  # noqa: E402

OBJETIVOS = [
    ("T1", "MYD021KM", "A2026285.0720"), ("T2", "MOD021KM", "A2026288.0105"),
    ("E1", "MYD021KM", "A2026272.0720"), ("E2", "MYD021KM", "A2026290.0850"),
    ("C1", "MYD021KM", "A2026274.0835"), ("C2", "MOD021KM", "A2026290.0220"),
    ("C3", "MOD021KM", "A2026289.0140"),
]
VOL = "NevadosDeChillan"
R_GUARDA_KM = 6.0
CAMPOS_REC = ("granule", "datetime_utc", "t_bg_k", "t_max_k", "diag_sigma_bg_k", "diag_n_bg_anillo",
              "diag_n_first_pass_pixels", "diag_n_first_pass_summit", "diag_n_second_pass_recapture",
              "diag_mu_dnti", "diag_sd_dnti", "diag_mu_deti", "diag_sd_deti", "diag_n_bg_used_first_pass",
              "diag_nti_bg", "diag_nti_max", "diag_t_max_dist_km", "distance_class", "n_anomalous_pixels",
              "sensor_zenith_deg", "vrp_mw")

_spec = importlib.util.spec_from_file_location("probe151", RAIZ / "experiments/_s151_probe_mod03/probe_mod03.py")
P151 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(P151)


def hav(lat0, lon0, lat, lon):
    r = 6371.0
    p1, p2 = np.radians(lat0), np.radians(lat)
    dphi, dl = p2 - p1, np.radians(lon - lon0)
    a = np.sin(dphi / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * r * np.arcsin(np.sqrt(a))


def f(x):
    if x is None:
        return None
    x = float(x)
    return None if not math.isfinite(x) else round(x, 6)


def bajar(short, pat, dest):
    import earthaccess
    from pipeline.fetch import download_granules
    for intento in range(4):
        try:
            r = P151._bajar(short, pat, dest)
            if r is not None:
                return r, "6.1"
            res = earthaccess.search_data(short_name=short, version="6.1NRT", granule_name=f"{short}.{pat}*")
            if res:
                p = download_granules(res[:1], dest)
                if p:
                    return p[0], "6.1NRT"
            return None, None
        except Exception as e:  # ReadTimeout de CMR (lo vio el frente M)
            print(f"  CMR/descarga fallo intento {intento} {short}.{pat}: {e!r}"[:300], flush=True)
            time.sleep(20 * (intento + 1))
    return None, None


def leer_dn(path):
    from pyhdf.SD import SD, SDC
    from pipeline import process_modis as PM
    sd = SD(str(path), SDC.READ)
    try:
        e = sd.select("EV_1KM_Emissive")
        a = e.get()
        out = {21: a[PM.BAND21_IDX].copy(), 22: a[PM.BAND22_IDX].copy(), 31: a[PM.BAND31_IDX].copy()}
        e.endaccess()
        return out
    finally:
        sd.end()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    if not os.environ.get("EARTHDATA_TOKEN", "").strip():
        sys.exit("EARTHDATA_TOKEN vacio: el probe no usa usuario y clave (A71).")

    import yaml
    from pipeline import detection_context as DC
    from pipeline import process_modis as PM
    from pipeline import profile as vrp_profile
    from pipeline import store
    from pipeline.fetch import auth
    from pipeline.geo_utils import get_detection_anchor
    from pipeline.scan_geometry import modis_pixel_areas

    vols = {v["name"]: v for v in yaml.safe_load(open(RAIZ / "volcanoes.yaml", encoding="utf-8"))["volcanoes"]}
    v = vols[VOL]
    vf_path = RAIZ / "pipeline" / "volcanic_features.yaml"
    VF = (yaml.safe_load(open(vf_path, encoding="utf-8")) or {}) if vf_path.exists() else {}
    publicados = {r["granule"][:22]: r for r in
                  json.load(open(RAIZ / "data" / "mirova_equivalent" / f"{VOL}.json", encoding="utf-8"))["records"]
                  if (r.get("sensor") or "").startswith("MODIS")}
    alat, alon = get_detection_anchor(v)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    sal = open(out / "probe_chillan.jsonl", "w", encoding="utf-8")
    print(f"ancla {alat} {alon}; volcan {v['lat']} {v['lon']}; inner {v.get('inner_radius_km')}; "
          f"B22 primaria {PM.ENABLE_MODIS_B22_PRIMARY}; prosa {PM.ENABLE_TESTS_23_PROSE_BRANCH}; "
          f"CLOUD_MASK_BT_K {PM.CLOUD_MASK_BT_K}; NTI_BT_SANITY_K {PM.NTI_BT_SANITY_K}", flush=True)
    auth()
    ORIG_READ, ORIG_FP, ORIG_SP = PM.read_modis_l1b, PM.first_pass_tests_2_and_3, PM.second_pass_adjacent
    ORIG_B22 = PM.ENABLE_MODIS_B22_PRIMARY
    ORIG_PROSA = PM.ENABLE_TESTS_23_PROSE_BRANCH
    faltan = 0

    for tag, short, pat in OBJETIVOS:
        fila = {"tag": tag, "granulo": f"{short}.{pat}"}
        l1b, ver = bajar(short, pat, out / "hdf")
        if l1b is None:
            fila["error"] = "no bajado"
            faltan += 1
            sal.write(json.dumps(fila) + "\n")
            sal.flush()
            continue
        fila["version"] = ver
        fila["archivo"] = Path(l1b).name
        try:
            dn = leer_dn(l1b)
            # Brazos (todos en memoria): P produccion; B21 banda 21 primaria; SC primer pase sin compuerta de 3 K;
            # MIN conectiva min en los dos pases; MINSC las dos cosas. SC, MIN y MINSC llegan hasta el record, para
            # saber si el pixel, una vez detectado, sobrevive a la magnitud (clip de dL >= 0 contra el fondo del anillo).
            for brazo in ("P", "B21", "SC", "MIN", "MINSC"):
                cap = {"sin_compuerta": brazo in ("SC", "MINSC")}

                def lector(path):
                    d = ORIG_READ(path)
                    cap["data"] = d
                    return d

                def fp(*a, **k):
                    if cap["sin_compuerta"]:
                        k = dict(k, apply_bt_gate=False)
                    hot, diag = ORIG_FP(*a, **k)
                    cap["fp_args"], cap["fp_kw"], cap["fp_hot"], cap["fp_diag"] = a, k, hot, diag
                    kk = dict(k)
                    cap["F1"] = ORIG_FP(*a, **dict(kk, apply_bt_gate=False))[0]
                    cap["F2"] = ORIG_FP(*a, **dict(kk, use_prose_branch=False))[0]
                    cap["F3"] = ORIG_FP(*a, **dict(kk, apply_bt_gate=False, use_prose_branch=False))[0]
                    return hot, diag

                def sp(*a, **k):
                    res = ORIG_SP(*a, **k)
                    cap.setdefault("sp", []).append((a, k, res))
                    return res

                PM.read_modis_l1b, PM.first_pass_tests_2_and_3, PM.second_pass_adjacent = lector, fp, sp
                PM.ENABLE_MODIS_B22_PRIMARY = (brazo != "B21") and ORIG_B22
                PM.ENABLE_TESTS_23_PROSE_BRANCH = (brazo not in ("MIN", "MINSC")) and ORIG_PROSA
                try:
                    res = PM.calculate_vrp(
                        Path(l1b), Path(l1b), v["lat"], v["lon"], v["radius_km"],
                        vent_lat=alat, vent_lon=alon, vent_radius_km=v.get("vent_radius_km", 4.0),
                        inner_radius_km=v.get("inner_radius_km"), exclude_zones=v.get("exclude_zones"),
                        active_water_bodies=v.get("active_water_bodies"),
                        lbg_global_compatible=v.get("lbg_global_compatible", False),
                        local_kernel_bg_compatible=v.get("local_kernel_bg", False))
                finally:
                    PM.read_modis_l1b, PM.first_pass_tests_2_and_3, PM.second_pass_adjacent = ORIG_READ, ORIG_FP, ORIG_SP
                    PM.ENABLE_MODIS_B22_PRIMARY = ORIG_B22
                    PM.ENABLE_TESTS_23_PROSE_BRANCH = ORIG_PROSA
                b = {"res_none": res is None}
                # record como lo escribe produccion
                if res:
                    with tempfile.TemporaryDirectory() as td:
                        store.DATA_DIR = Path(td)
                        store.append_record(v["name"], copy.deepcopy(res), volcano_lat=v["lat"], volcano_lon=v["lon"],
                                            overwrite=True, max_hotspot_dist_km=v.get("radius_km"),
                                            enable_pixel_level_distance_filter=vrp_profile.ENABLE_PIXEL_LEVEL_DISTANCE_FILTER,
                                            max_cluster_pixels=v.get("max_cluster_pixels"),
                                            inner_radius_km=v.get("inner_radius_km"),
                                            volcanic_features=VF.get(v["name"]))
                        p = Path(td) / f"{v['name']}.json"
                        recs = json.load(open(p))["records"] if p.exists() else []
                        rec = recs[-1] if recs else None
                    if rec:
                        pc = rec.get("primary_cluster") or {}
                        b["rec"] = {k: rec.get(k) for k in CAMPOS_REC}
                        b["rec"]["pc"] = {k: pc.get(k) for k in ("vrp_mw", "n_pixels", "centroid_dist_km")} if pc else None
                        # record reducido para el predicado del tablero (banco_paridad.CAMPOS_JS), corrido despues con node
                        slim = {kk: rec.get(kk) for kk in ("primary_cluster", "distance_class", "vrp_mw", "vrp_mir_mw",
                                                          "discarded_reason", "triggered_test1", "vrp_vent_mw", "t_max_k",
                                                          "sensor", "f5_core_vrp_mw")}
                        slim["anomaly_pixels"] = [{kk: q.get(kk) for kk in ("lat", "lon", "vrp_mw", "bt_k")}
                                                  for q in (rec.get("anomaly_pixels") or [])]
                        b["slim"] = slim
                if "fp_args" not in cap:
                    b["fp_no_corrio"] = True
                    fila[brazo] = b
                    continue
                d = cap["data"]
                lat, lon = d["lat"], d["lon"]
                # calculate_vrp llama con argumentos por nombre: se enlazan a la firma original
                ba = inspect.signature(ORIG_FP).bind(*cap["fp_args"], **cap["fp_kw"])
                ba.apply_defaults()
                k = dict(ba.arguments)
                nti, nti_app, bt = k["nti"], k["nti_app"], k["bt"]
                roi_mask, dist_km, t_bg = k["roi_mask"], k["dist_km"], k["t_bg"]
                rep = replicar_first_pass(**k)
                b["replica_identica"] = bool(np.array_equal(rep["hot"], cap["fp_hot"]))
                inner = k["inner_km"]
                dv = hav(alat, alon, lat, lon)
                dentro = dv <= inner
                b["n_fp"] = int(cap["fp_hot"].sum())
                b["n_fp_inner"] = int((cap["fp_hot"] & dentro).sum())
                for nombre in ("F1", "F2", "F3"):
                    b[f"n_{nombre}"] = int(cap[nombre].sum())
                    b[f"n_{nombre}_inner"] = int((cap[nombre] & dentro).sum())
                b["t_bg"] = f(t_bg)
                for kk in ("mu_dnti", "sd_dnti", "mu_deti", "sd_deti", "n_bg"):
                    b[kk] = f(rep.get(kk))
                b["thr"] = {x: f(y) for x, y in (rep.get("thr") or {}).items()}
                b["stat"] = {x: f(y) for x, y in (rep.get("stat") or {}).items()}
                b["c1"] = {x: f(y) for x, y in (rep.get("c1") or {}).items()}
                # contexto
                bt31 = PM.radiance_to_bt(d["band31"], PM.BAND31_LAMBDA)
                bt21 = PM.radiance_to_bt(d["band21"], PM.BAND21_LAMBDA)
                bt22 = PM.radiance_to_bt(d["band22"], PM.BAND22_LAMBDA)
                dvol = hav(v["lat"], v["lon"], lat, lon)
                anillo = (dvol >= 5) & (dvol <= 25)
                b["bt31_anillo_mediana"] = f(np.nanmedian(bt31[anillo]))
                b["btmir_anillo_mediana"] = f(np.nanmedian(bt[anillo]))
                areas = modis_pixel_areas(lat.shape, nadir_fixed=False)
                # segundo pase
                sp_rep = None
                if cap.get("sp"):
                    sa, sk, sres = cap["sp"][-1]
                    sb = inspect.signature(ORIG_SP).bind(*sa, **sk)
                    sb.apply_defaults()
                    sk = dict(sb.arguments)
                    sp_rep = replicar_second_pass(**sk)
                    b["sp_replica_identica"] = bool(np.array_equal(sp_rep["out"], sres))
                    b["sp_n_nuevos_inner"] = int((sres & ~sk["active_mask"] & dentro).sum())
                    b["sp_n_nuevos"] = int((sres & ~sk["active_mask"]).sum())
                    for kk in ("mu_dnti", "sd_dnti", "mu_deti", "sd_deti", "n_bg"):
                        b["sp_" + kk] = f(sp_rep.get(kk))
                    b["sp_kw"] = {x: (y if isinstance(y, (int, float, bool, type(None))) else str(type(y)))
                                  for x, y in sk.items() if x not in ("nti", "eti", "active_mask", "is_summit")}
                # pixeles cerca
                ii, jj = np.where(dv <= R_GUARDA_KM)
                ic, jc = np.unravel_index(np.nanargmin(np.where(np.isfinite(dv), dv, np.inf)), dv.shape)
                b["pixel_crater"] = [int(ic), int(jc), f(dv[ic, jc])]
                b["area_factor_crater"] = f(areas[ic, jc] / 1e6)
                b["n_lineas"], b["n_cols"] = int(lat.shape[0]), int(lat.shape[1])
                pix = []
                for i, j in zip(ii, jj):
                    p = {"i": int(i), "j": int(j), "d_km": f(dv[i, j]), "lat": f(lat[i, j]), "lon": f(lon[i, j]),
                         "dn21": int(dn[21][i, j]), "dn22": int(dn[22][i, j]), "dn31": int(dn[31][i, j]),
                         "L21": f(d["band21"][i, j]), "L22": f(d["band22"][i, j]), "L31": f(d["band31"][i, j]),
                         "bt21": f(bt21[i, j]), "bt22": f(bt22[i, j]), "btmir": f(bt[i, j]), "bt31": f(bt31[i, j]),
                         "nti": f(nti[i, j]), "nti_app": f(nti_app[i, j]), "eti": f(rep["eti"][i, j]),
                         "mean_nti8": f(rep["mean_nti"][i, j]), "dnti": f(rep["dnti"][i, j]),
                         "deti": f(rep["deti"][i, j]), "en_pool_bg": bool(rep["bg_mask"][i, j]),
                         "en_roi": bool(roi_mask[i, j]), "vecindad_3x3": bool(abs(int(i) - int(ic)) <= 1 and abs(int(j) - int(jc)) <= 1)}
                    if not rep.get("corto"):
                        p.update({"cumbre": bool(rep["is_summit"][i, j]), "thr_dnti": f(rep["thr_dnti"][i, j]),
                                  "thr_deti": f(rep["thr_deti"][i, j]), "pasa2": bool(rep["pass_2"][i, j]),
                                  "pasa3": bool(rep["pass_3"][i, j]), "pasa_compuerta": bool(rep["gate_bt"][i, j]),
                                  "hot": bool(cap["fp_hot"][i, j]), "F1": bool(cap["F1"][i, j]),
                                  "F2": bool(cap["F2"][i, j]), "F3": bool(cap["F3"][i, j])})
                    if sp_rep is not None and not sp_rep.get("corto"):
                        p.update({"sp_dnti": f(sp_rep["dnti"][i, j]), "sp_deti": f(sp_rep["deti"][i, j]),
                                  "sp_thr_dnti": f(sp_rep["thr_dnti"][i, j]), "sp_thr_deti": f(sp_rep["thr_deti"][i, j]),
                                  "sp_out": bool(cap["sp"][-1][2][i, j])})
                    pix.append(p)
                b["pixeles"] = sorted(pix, key=lambda p: p["d_km"])
                fila[brazo] = b
            # comparacion con el publicado
            pub = publicados.get(f"{short}.{pat}")
            fila["publicado"] = ({kk: pub.get(kk) for kk in CAMPOS_REC} if pub else None)
            if pub:
                fila["publicado"]["pc"] = ({kk: (pub.get("primary_cluster") or {}).get(kk)
                                           for kk in ("vrp_mw", "n_pixels", "centroid_dist_km")}
                                          if pub.get("primary_cluster") else None)
        except Exception as e:
            fila["error"] = repr(e)
            fila["traza"] = traceback.format_exc()[-2000:]
            faltan += 1
        sal.write(json.dumps(fila, ensure_ascii=False, default=str) + "\n")
        sal.flush()
        P = fila.get("P") or {}
        print(tag, fila["granulo"], "n_fp", P.get("n_fp"), "inner", P.get("n_fp_inner"), "F1", P.get("n_F1_inner"),
              "F2", P.get("n_F2_inner"), "F3", P.get("n_F3_inner"), "rep", P.get("replica_identica"),
              "B21", (fila.get("B21") or {}).get("n_fp_inner"),
              "pc SC/MIN/MINSC", [((fila.get(x) or {}).get("rec") or {}).get("pc") for x in ("SC", "MIN", "MINSC")],
              fila.get("error", ""), flush=True)
        Path(l1b).unlink(missing_ok=True)
    sal.close()
    print("FALTAN:", faltan)
    sys.exit(2 if faltan else 0)


if __name__ == "__main__":
    main()
