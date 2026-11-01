# -*- coding: utf-8 -*-
"""S157 issue #865: probe de SOLO LECTURA, atribución por etapa (A75) de la pasada PCC VIIRS 750 NOAA-21
del 2026-10-10 05:54 UTC, la alerta protegida de MIROVA (1,19 MW) que K no publica y C0 sí.

POR QUÉ. El record persistido dice que en K el primer pase y el segundo quedaron vacíos (0 y 0) y en C0 dieron 2 y 6,
con mu y sigma del dNTI y del dETI idénticos en los dos. Con esos diagnósticos, el umbral de la cumbre es
max(C1, mu + 5 sigma) = 0,01415 en dNTI y 0,00416 en dETI con K, y 0,003 en los dos con C0. Lo que el record NO
guarda es cuánto valen el dNTI, el dETI y la BT de los píxeles del cúmulo, que es lo que dice por cuánto les faltó.

QUÉ HACE. Baja el L1B y el GEO del MISMO granule del record (VJ202MOD.A2026283.0554.021...) y corre
`process_viirs_mod.calculate_vrp` cuatro veces en el mismo proceso, cambiando sólo dos globales del módulo
(los dos flags de K que llegan a VIIRS 750; la banda 22 es sólo MODIS):
  K         conectiva max, sin Test 1   (producción)
  C0        conectiva min, con Test 1   (sombra)
  min_sinT1 conectiva min, sin Test 1   (aísla la conectiva)
  max_conT1 conectiva max, con Test 1   (aísla el Test 1)
Envuelve `first_pass_tests_2_and_3` y `second_pass_adjacent` (el del ensamblado, el que recibe active_mask por
nombre) y guarda, por píxel, dNTI, dETI, BT y los umbrales de cada conectiva. No escribe en data/ (store._save anulado).

CONTROL (fijado antes de correr): el brazo K reproduce el record de producción (0 píxeles, Test 1 no corre,
diag_sd_dnti = 0,0028313 a 1e-6) y el brazo C0 el de la sombra (pc.vrp_mw 1,886 a 1 %, 4 píxeles, 8 anómalos).
Si alguno falla, el resultado es INDECIDIBLE y no se interpreta.
Salida: out/probe_pcc865.json. Sale 2 si no puede bajar el granule (S141).
"""
import io
import json
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")   # ANTES de importar el pipeline
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
for p in (ROOT, ROOT / "scripts"):
    sys.path.insert(0, str(p))

import numpy as np  # noqa: E402
import pipeline.detection_context as dc  # noqa: E402
import pipeline.process_viirs_mod as pvm  # noqa: E402
import pipeline.store as store  # noqa: E402
from pipeline.fetch import auth, download_granules, search_granules  # noqa: E402
from pipeline.geo_utils import get_detection_anchor  # noqa: E402
from run_pipeline import VOLCANIC_FEATURES, load_volcanoes, vrp_profile  # noqa: E402

store._save = lambda *a, **kw: None   # sólo lectura

VOL = "PuyehueCordonCaulle"
L1B = "VJ202MOD.A2026283.0554.021.2026283113526.nc"
STAMP = "A2026283.0554"
PASADA = datetime(2026, 10, 10, 5, 54)
PRODUCTOS = ("VIIRS_NOAA21_MOD_L1B", "VIIRS_NOAA21_MOD_GEO")
BRAZOS = {"K": (True, False), "C0": (False, True), "min_sinT1": (False, False), "max_conT1": (True, True)}
DEST, OUT = HERE / "granules", HERE / "out"
CAMPOS = ("vrp_mw", "n_anomalous_pixels", "diag_n_first_pass_pixels", "diag_n_second_pass_recapture",
          "diag_mu_dnti", "diag_sd_dnti", "diag_mu_deti", "diag_sd_deti", "triggered_test1", "test1_k_observed",
          "n_test1_pixels", "final_hotspot_source", "final_hotspot_dist_km", "distance_class", "primary_cluster",
          "anomaly_pixels", "t_bg_k", "nti_max", "discarded_reason", "f5_core_vrp_mw", "vrp_mir_mw", "t_max_k",
          "sensor", "vrp_vent_mw")

E = {"geo": None, "fp": None, "sp": None}
_fp_real, _sp_real, _geo_real = pvm.first_pass_tests_2_and_3, pvm.second_pass_adjacent, pvm.read_viirs_mod_geo


def _geo(path, *a, **kw):
    g = _geo_real(path, *a, **kw)
    E["geo"] = g
    return g


def _fp(*a, **kw):
    hot, diag = _fp_real(*a, **kw)
    nti, bt, dist = kw["nti"], kw["bt"], kw["dist_km"]
    eti = diag.get("eti")
    dnti = nti - dc._nanmean_8neighbors_fast(nti)
    deti = eti - dc._nanmean_8neighbors_fast(eti) if eti is not None else None
    E["fp"] = {"hot": hot, "diag": diag, "dnti": dnti, "deti": deti, "bt": bt, "dist": dist, "roi": kw["roi_mask"],
               "t_bg": kw["t_bg"], "gate": kw["t_bg"] + kw["bt_sanity_k"], "kw": {k: kw[k] for k in (
                   "c1_dnti_summit", "c2_dnti_summit", "c1_dnti_scene", "c2_dnti_scene", "inner_km",
                   "use_prose_branch")}}
    return hot, diag


def _sp(*a, **kw):
    out = _sp_real(*a, **kw)
    if "active_mask" in kw:   # el del ensamblado (process_viirs_mod.py, segundo pase tras el primero)
        act = kw["active_mask"]
        nti_m = np.where(act, np.nan, kw["nti"])
        eti_m = np.where(act, np.nan, kw["eti"])
        dnti = kw["nti"] - dc._nanmean_8neighbors_fast(nti_m)
        deti = kw["eti"] - dc._nanmean_8neighbors_fast(eti_m)
        bg = (~act) & np.isfinite(dnti) & np.isfinite(deti)
        E["sp"] = {"out": out, "act": act, "dnti": dnti, "deti": deti,
                   "mu_dnti": float(np.mean(dnti[bg])), "sd_dnti": float(np.std(dnti[bg])),
                   "mu_deti": float(np.mean(deti[bg])), "sd_deti": float(np.std(deti[bg])),
                   "use_prose_branch": kw.get("use_prose_branch")}
    return out


pvm.first_pass_tests_2_and_3, pvm.second_pass_adjacent, pvm.read_viirs_mod_geo = _fp, _sp, _geo


def gname(g):
    try:
        return g["umm"]["DataGranule"]["Identifiers"][0]["Identifier"]
    except Exception:
        return str(g.get("umm", {}).get("GranuleUR", g))[:120]


def bajar(vol):
    out = []
    for key in PRODUCTOS:
        grs = [g for g in search_granules(key, vol["lat"], vol["lon"], vol["radius_km"], PASADA) if STAMP in gname(g)]
        if key.endswith("_L1B"):
            grs = [g for g in grs if gname(g) == L1B] or grs
        if not grs:
            return None, f"sin granule {key} {STAMP}"
        got = [Path(p) for p in download_granules(grs[:1], DEST) if STAMP in Path(p).name]
        if not got:
            return None, f"descarga fallida {key} {STAMP}"
        out.append(got[0])
    return tuple(out), (None if out[0].name == L1B else f"L1B reprocesado: {out[0].name}")


def umbrales(mu_n, sd_n, mu_e, sd_e, c1, c2):
    cn, ce = mu_n + c2 * sd_n, mu_e + c2 * sd_e
    return {"dnti_max": max(c1, cn), "dnti_min": min(c1, cn), "deti_max": max(c1, ce), "deti_min": min(c1, ce),
            "contraste_dnti": cn, "contraste_deti": ce}


def px(r, c, fp, sp, lat, lon):
    def f(x):
        return None if x is None or not np.isfinite(x) else round(float(x), 6)
    return {"fila": int(r), "col": int(c), "lat": round(float(lat[r, c]), 5), "lon": round(float(lon[r, c]), 5),
            "dist_ancla_km": f(fp["dist"][r, c]), "bt_k": f(fp["bt"][r, c]), "dnti_1": f(fp["dnti"][r, c]),
            "deti_1": f(fp["deti"][r, c]) if fp["deti"] is not None else None,
            "dnti_2": f(sp["dnti"][r, c]) if sp else None, "deti_2": f(sp["deti"][r, c]) if sp else None,
            "pasa_gate_bt": bool(fp["bt"][r, c] > fp["gate"]), "en_roi": bool(fp["roi"][r, c])}


def correr(vol, par, nombre):
    prose, t1 = BRAZOS[nombre]
    pvm.ENABLE_TESTS_23_PROSE_BRANCH, pvm.ENABLE_TEST1_PATH = prose, t1
    E.update({"fp": None, "sp": None})
    a_lat, a_lon = get_detection_anchor(vol)
    rec = pvm.calculate_vrp(par[0], par[1], vol["lat"], vol["lon"], vol["radius_km"],
                            vent_lat=a_lat, vent_lon=a_lon, vent_radius_km=vol.get("vent_radius_km", 4.0),
                            inner_radius_km=vol.get("inner_radius_km"), exclude_zones=vol.get("exclude_zones"),
                            active_water_bodies=vol.get("active_water_bodies"),
                            lbg_global_compatible=vol.get("lbg_global_compatible", False),
                            local_kernel_bg_compatible=vol.get("local_kernel_bg", False))
    store.append_record(vol["name"], rec, volcano_lat=vol["lat"], volcano_lon=vol["lon"], overwrite=True,
                        max_hotspot_dist_km=vol.get("radius_km"),
                        enable_pixel_level_distance_filter=vrp_profile.ENABLE_PIXEL_LEVEL_DISTANCE_FILTER,
                        max_cluster_pixels=vol.get("max_cluster_pixels"),
                        inner_radius_km=vol.get("inner_radius_km"),
                        volcanic_features=VOLCANIC_FEATURES.get(vol["name"]))
    fp, sp = E["fp"], E["sp"]
    lat, lon = E["geo"]["lat"], E["geo"]["lon"]
    d = fp["diag"]
    kw = fp["kw"]
    res = {"flags": {"use_prose_branch": prose, "test1": t1, "leido_fp": kw["use_prose_branch"],
                     "leido_sp": sp and sp["use_prose_branch"], "pvm_prose": pvm.ENABLE_TESTS_23_PROSE_BRANCH,
                     "pvm_test1": pvm.ENABLE_TEST1_PATH},
           "record": {k: rec.get(k) for k in CAMPOS if k in rec}, "gate_bt_k": round(float(fp["gate"]), 3),
           "umbrales_1_cumbre": umbrales(d["mu_dnti"], d["sd_dnti"], d["mu_deti"], d["sd_deti"],
                                         kw["c1_dnti_summit"], kw["c2_dnti_summit"]),
           "umbrales_2_cumbre": (umbrales(sp["mu_dnti"], sp["sd_dnti"], sp["mu_deti"], sp["sd_deti"],
                                          kw["c1_dnti_summit"], kw["c2_dnti_summit"]) if sp else None),
           "params": kw, "n_fp": int(np.sum(fp["hot"])), "n_sp_out": int(np.sum(sp["out"])) if sp else None}
    # píxeles: los del primer pase, los del segundo, y los 15 de mayor dNTI en la cumbre dentro del ROI
    summit = fp["roi"] & (fp["dist"] <= kw["inner_km"]) & np.isfinite(fp["dnti"])
    orden = np.argsort(np.where(summit, fp["dnti"], -np.inf), axis=None)[::-1][:15]
    sel = {("fp", int(r), int(c)) for r, c in zip(*np.where(fp["hot"]))}
    if sp:
        sel |= {("sp", int(r), int(c)) for r, c in zip(*np.where(sp["out"] & ~fp["hot"]))}
    sel |= {("top_dnti", *map(int, np.unravel_index(i, fp["dnti"].shape))) for i in orden}
    res["pixeles"] = sorted(({"origen": o, **px(r, c, fp, sp, lat, lon)} for o, r, c in sel),
                            key=lambda x: -(x["dnti_1"] or -9))
    return res


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"perfil {os.environ['VRP_PROFILE']} | granule {L1B}", flush=True)
    auth()
    vol = {v["name"]: v for v in load_volcanoes()}[VOL]
    par, nota = bajar(vol)
    if par is None:
        print("NO SE PUDO BAJAR:", nota, flush=True)
        sys.exit(2)
    out = {"granule": [p.name for p in par], "nota": nota, "brazos": {}}
    for nombre in BRAZOS:
        try:
            out["brazos"][nombre] = correr(vol, par, nombre)
            r = out["brazos"][nombre]
            pc = r["record"].get("primary_cluster") or {}
            print(f"{nombre:10s} 1er {r['n_fp']} 2do-out {r['n_sp_out']} anom {r['record'].get('n_anomalous_pixels')} "
                  f"pc {pc.get('vrp_mw')} MW {pc.get('n_pixels')} px | T1 {r['record'].get('triggered_test1')} "
                  f"| umbral1 {r['umbrales_1_cumbre']} | gate {r['gate_bt_k']}", flush=True)
        except Exception:
            out["brazos"][nombre] = {"error": traceback.format_exc()}
            print(nombre, "ERROR", traceback.format_exc(), flush=True)
    k, c0 = out["brazos"].get("K", {}), out["brazos"].get("C0", {})
    rk, rc = k.get("record", {}), c0.get("record", {})
    pcc = rc.get("primary_cluster") or {}
    out["control"] = {
        "K_reproduce": (rk.get("n_anomalous_pixels") == 0 and not rk.get("triggered_test1")
                        and abs((rk.get("diag_sd_dnti") or 0) - 0.0028313448879440607) < 1e-6),
        "C0_reproduce": (pcc.get("n_pixels") == 4 and abs((pcc.get("vrp_mw") or 0) - 1.886) <= 0.01 * 1.886
                         and rc.get("n_anomalous_pixels") == 8)}
    print("CONTROL", out["control"], flush=True)
    (OUT / "probe_pcc865.json").write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
    if not all(out["control"].values()):
        print("INDECIDIBLE: el control no reproduce los records persistidos", flush=True)


if __name__ == "__main__":
    main()
