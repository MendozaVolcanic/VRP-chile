# -*- coding: utf-8 -*-
"""S157 (tarea 1.29): probe de sólo lectura del L1B de Nevados de Chillán, 2026-10-18. ESCRITO ANTES DE CORRER.

POR QUÉ. La sesión de magnitud de Chillán (PR #869) acotó sin L1B cuánto de nuestro déficit contra MIROVA es fondo
y cuánto es selección (píxeles tibios que MIROVA suma y nosotros no alertamos): los records no guardan a los
vecinos del píxel caliente, así que el fondo real de los vecinos y el motivo por el que un vecino tibio no se alertó
sólo los conoce el gránulo. Este probe los lee en 10 gránulos del 18-oct (la mañana con nadir y borde del barrido
en la misma hora) y deja medido, no acotado, lo que hace D25 sobre K en cada uno.

QUÉ CORRE, por gránulo, en el mismo proceso y sobre el mismo archivo (sólo cambia un global del módulo):
  VIIRS 375 y 750:
    control   K tal cual (flag D25 apagado). Tiene que reproducir el record persistido (C-P1).
    nulo      flag D25 encendido pero el envoltorio devuelve el fondo de hoy: tiene que dar EXACTAMENTE el control.
              Mide que encender el camino de D25 no cambie nada por sí solo (A110, A116).
    d25_h3    flag D25 encendido, ventana hasta 7x7 (VRP_BG_NEIGHBOR_MAX_HALF_PX = 3, el valor del perfil).
    d25_h1    flag D25 encendido, sólo los 8 vecinos (la otra mitad de la decisión abierta de S142).
  MODIS (no hay flag D25 en MODIS; ver PREREGISTRO.md §2): se usa el camino opt-in del kernel local,
  `local_kernel_bg_compatible=True`, que ya existe en process_modis y que Chillán no tiene en volcanoes.yaml:
    control   K tal cual (mediana del anillo).
    nulo      kernel encendido con un envoltorio que devuelve el fondo del anillo: tiene que dar el control.
    kernel3   kernel encendido tal cual: media de la TEMPERATURA de los vecinos no alertados en 3x3.
    d25_rad   kernel encendido con envoltorio: media de la RADIANCIA de los vecinos no alertados con ventana hasta
              7x7 (la misma función que D25 usa en VIIRS), devuelta como temperatura a la longitud de onda con que
              process_modis vuelve a radiancia. Es el análogo de D25 en MODIS SIN tocar pipeline/.
DIAGNÓSTICO DE SELECCIÓN (en d25_h3 y d25_rad): para cada vecino 8-conexo NO alertado del cúmulo publicado, su BT,
su dNTI y su dETI del primer pase, los umbrales que tenía (conectiva `max` de K, summit o escena según la
distancia), qué prueba lo dejó afuera y cuánta potencia agregaría si se sumara restando el anillo. Eso acota la
selección: «si MIROVA sumara todos los vecinos del cúmulo, a lo más esto».

CONTROLES (fijados antes de correr):
  C-P1  el control reproduce el record persistido de data/mirova_equivalent/NevadosDeChillan.json (mismo gránulo):
        pc.vrp_mw y, en VIIRS 375, f5_core_vrp_mw a <= max(1e-3 MW, 1 %); mismo pc.n_pixels; centroide a <= 0,01 km.
        Si falla, la pasada se informa pero su factor D25 no se interpreta (el código de hoy no es el que la
        escribió).
  C-N   el brazo nulo da pc.vrp_mw, f5_core_vrp_mw y anomaly_pixels idénticos al control (igualdad exacta).
  C-A   el envoltorio de D25 se llamó al menos una vez en d25_h3/d25_h1/d25_rad y nunca en control (A118).
  C-K   el área por píxel por k reproduce el VRP del píxel más caliente del control con el fondo del anillo a
        <= 1 % (el instrumento de la potencia de los vecinos usa esa misma cuenta).

Uso (Actions; autentica sólo con EARTHDATA_TOKEN, A71):
  python probe_chillan.py --familia VIIRS --out out
  python probe_chillan.py --familia MODIS --out out
Sale 2 si falta alguna pasada o si una corrida se cae (S141: un job verde sin datos no sirve).
"""
from __future__ import annotations

import argparse
import io
import json
import os
import shutil
import sys
import traceback
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")   # ANTES de importar el pipeline: producción = K
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
for p in (ROOT, ROOT / "scripts"):
    sys.path.insert(0, str(p))

import numpy as np  # noqa: E402
import pipeline.detection_context as dc  # noqa: E402
import pipeline.store as store  # noqa: E402
import pipeline.vrp_regimes as vr  # noqa: E402
from pipeline import profile as vrp_profile  # noqa: E402
from pipeline.geo_utils import get_detection_anchor  # noqa: E402

store._save = lambda *a, **kw: None   # sólo lectura: nada se escribe en data/

VOLCAN = "NevadosDeChillan"
# Los 10 gránulos del 2026-10-18 que leyó el PR #869 (a_pasadas_salida.txt) y razon_por_cenit_salida_20261018.txt:
# nombre EXACTO del record persistido (fuente: data/mirova_equivalent/NevadosDeChillan.json en origin/main 8c94c847b).
PASADAS = {
    "VIIRS": [
        ("VIIRS_NOAA21", "VJ202IMG.A2026291.0506.021.2026291103813.nc"),
        ("VIIRS_NOAA21_750", "VJ202MOD.A2026291.0506.021.2026291103813.nc"),
        ("VIIRS_SNPP", "VNP02IMG.A2026291.0542.002.2026291121847.nc"),
        ("VIIRS_SNPP_750", "VNP02MOD.A2026291.0542.002.2026291121847.nc"),
        ("VIIRS_NOAA20", "VJ102IMG.A2026291.0600.021.2026291123439.nc"),
        ("VIIRS_NOAA20_750", "VJ102MOD.A2026291.0600.021.2026291123439.nc"),
        ("VIIRS_NOAA21", "VJ202IMG.A2026291.0648.021.2026291130237.nc"),
        ("VIIRS_NOAA21_750", "VJ202MOD.A2026291.0648.021.2026291130237.nc"),
    ],
    "MODIS": [
        ("MODIS_TERRA", "MOD021KM.A2026291.0120.061.2026291131348.hdf"),
        ("MODIS_AQUA", "MYD021KM.A2026291.0750.061.2026292011058.hdf"),
    ],
}
PRODUCTO = {"VIIRS_NOAA21": ("VIIRS_NOAA21_L1B", "VIIRS_NOAA21_GEO"),
            "VIIRS_NOAA21_750": ("VIIRS_NOAA21_MOD_L1B", "VIIRS_NOAA21_MOD_GEO"),
            "VIIRS_SNPP": ("VIIRS_SNPP_L1B", "VIIRS_SNPP_GEO"),
            "VIIRS_SNPP_750": ("VIIRS_SNPP_MOD_L1B", "VIIRS_SNPP_MOD_GEO"),
            "VIIRS_NOAA20": ("VIIRS_NOAA20_L1B", "VIIRS_NOAA20_GEO"),
            "VIIRS_NOAA20_750": ("VIIRS_NOAA20_MOD_L1B", "VIIRS_NOAA20_MOD_GEO"),
            "MODIS_TERRA": ("MODIS_TERRA_L1B", None),     # process_modis no usa el geo (docstring de calculate_vrp)
            "MODIS_AQUA": ("MODIS_AQUA_L1B", None)}
CAMPOS = ("sensor", "datetime_utc", "granule", "product_version", "sensor_zenith_deg", "vrp_mw", "vrp_mir_mw",
          "t_bg_k", "t_max_k", "n_anomalous_pixels", "final_hotspot_source", "final_hotspot_dist_km",
          "distance_class", "discarded_reason", "primary_cluster", "f5_core_vrp_mw", "triggered_test1",
          "diag_n_first_pass_pixels", "diag_n_second_pass_recapture", "diag_bg_vecinos_n_sin_vecinos",
          "diag_L_bg_vecinos_w_m2_sr_um", "diag_L_bg_local_w_m2_sr_um", "anomaly_pixels")

# ---------------------------------------------------------------------------------------------------------------
# Capturas (envoltorios en el espacio de nombres de cada procesador; se instalan una vez y leen ESTADO)
# ---------------------------------------------------------------------------------------------------------------
ESTADO: dict = {}


def _reiniciar(brazo):
    ESTADO.clear()
    ESTADO.update({"brazo": brazo, "fondo": [], "first_pass": None, "cumulos": None, "areas": None})


def _capturar_first_pass(real):
    def env(nti, nti_app, bt, roi_mask, dist_km, t_bg, bt_sanity_k, **kw):
        hot, diag = real(nti, nti_app, bt, roi_mask, dist_km, t_bg, bt_sanity_k, **kw)
        if ESTADO.get("first_pass") is None:      # el primer llamado es el primer pase del bloque contextual
            ESTADO["first_pass"] = {"nti": np.array(nti, dtype=np.float64), "bt": np.array(bt, dtype=np.float64),
                                    "dist": np.array(dist_km, dtype=np.float64), "t_bg": float(t_bg),
                                    "bt_sanity_k": float(bt_sanity_k), "kw": {k: v for k, v in kw.items()
                                                                              if not isinstance(v, np.ndarray)},
                                    "roi1_mask": kw.get("roi1_mask"), "hot": np.array(hot, dtype=bool),
                                    "diag": {k: v for k, v in diag.items() if k != "eti"},
                                    "eti": None if diag.get("eti") is None else np.array(diag["eti"], dtype=np.float64)}
        return hot, diag
    return env


def _capturar_cumulos(real):
    def env(hot_mask_2d, lat, lon, vlat, vlon, **kw):
        out = real(hot_mask_2d, lat, lon, vlat, vlon, **kw)
        if ESTADO.get("cumulos") is None:
            ESTADO["cumulos"] = {"hot": np.array(hot_mask_2d, dtype=bool), "lat": np.array(lat), "lon": np.array(lon),
                                 "c0": [tuple(map(int, ij)) for ij in (out[0]["pixel_indices"] if out else [])]}
        return out
    return env


def _capturar_areas(real):
    def env(*a, **kw):
        areas = real(*a, **kw)
        ESTADO["areas"] = np.array(areas, dtype=np.float64)
        return areas
    return env


def _fondo_viirs(real, lam):
    """Envoltorio del fondo D25 de VIIRS. En `nulo` devuelve el fondo de hoy (legacy_l_bg) sin tocarlo."""
    def env(bt_grid, alert_mask, hot_rows, hot_cols, legacy_l_bg, *, max_half_px):
        if ESTADO["brazo"] == "nulo":
            l_bg = np.broadcast_to(np.asarray(legacy_l_bg, dtype=np.float64), (len(hot_rows),)).copy()
            n_sin = 0
        else:
            l_bg, n_sin = real(bt_grid, alert_mask, hot_rows, hot_cols, legacy_l_bg, max_half_px=max_half_px)
        _, half = vr.neighbor_mean_radiance_background(bt_grid, alert_mask, hot_rows, hot_cols, lam,
                                                       max_half_px=max_half_px)
        ESTADO["fondo"].append(_diag_fondo(bt_grid, alert_mask, hot_rows, hot_cols, legacy_l_bg, l_bg, half, lam))
        return l_bg, n_sin
    return env


def _diag_fondo(bt_grid, alert_mask, hot_rows, hot_cols, legacy, l_bg, half, lam):
    bt_hot = np.asarray(bt_grid, dtype=np.float64)[hot_rows, hot_cols]
    return {"bt_grid": np.asarray(bt_grid, dtype=np.float64), "alert": np.asarray(alert_mask, dtype=bool),
            "rows": np.asarray(hot_rows, dtype=int), "cols": np.asarray(hot_cols, dtype=int),
            "bt_hot": bt_hot, "L_hot": vr_planck(bt_hot, lam),
            "L_bg_hoy": np.broadcast_to(np.asarray(legacy, dtype=np.float64), np.shape(bt_hot)).copy(),
            "L_bg_brazo": np.asarray(l_bg, dtype=np.float64).copy(), "half": np.asarray(half).copy()}


def vr_planck(bt, lam):
    from pipeline.process_viirs import bt_to_spectral_radiance
    return np.asarray(bt_to_spectral_radiance(np.asarray(bt, dtype=np.float64), lam), dtype=np.float64)


def _fondo_modis(real, pm):
    """Envoltorio de compute_local_background en process_modis (sólo se llama con local_kernel_bg_compatible).

    kernel3 llama al real (media de BT 3x3). nulo devuelve NaN (el procesador cae al t_bg del anillo: es el control).
    d25_rad promedia RADIANCIA de vecinos no alertados con ventana hasta 7x7 y la devuelve como BT a BAND21_LAMBDA,
    que es la longitud de onda con que process_modis vuelve a radiancia (process_modis.py, bloque Wooster)."""
    lam = pm.BAND21_LAMBDA

    def env(bt_grid, hot_rows, hot_cols, kernel_size=3):
        grid = np.asarray(bt_grid, dtype=np.float64)
        alert = np.zeros(grid.shape, dtype=bool)
        alert[np.asarray(hot_rows, dtype=int), np.asarray(hot_cols, dtype=int)] = True
        b = ESTADO["brazo"]
        if b == "nulo":
            out = [float("nan")] * len(hot_rows)
        elif b == "kernel3":
            out = real(bt_grid, hot_rows, hot_cols, kernel_size=kernel_size)
        elif b == "d25_rad":
            l_bk, _ = vr.neighbor_mean_radiance_background(grid, alert, hot_rows, hot_cols, lam,
                                                           max_half_px=int(vrp_profile.VRP_BG_NEIGHBOR_MAX_HALF_PX))
            out = [float("nan") if not np.isfinite(L) else float(pm.C2 / (lam * np.log(1.0 + pm.C1 / (lam ** 5 * L))))
                   for L in l_bk]
        else:
            raise RuntimeError("compute_local_background llamado en el brazo %r" % b)
        _, half = vr.neighbor_mean_radiance_background(grid, alert, hot_rows, hot_cols, lam,
                                                       max_half_px=int(vrp_profile.VRP_BG_NEIGHBOR_MAX_HALF_PX))
        t = np.asarray(out, dtype=np.float64)
        bt_hot = grid[np.asarray(hot_rows, dtype=int), np.asarray(hot_cols, dtype=int)]
        planck = lambda x: pm.C1 / (lam ** 5 * (np.exp(pm.C2 / (lam * x)) - 1))  # noqa: E731
        ESTADO["fondo"].append({"bt_grid": grid, "alert": alert, "rows": np.asarray(hot_rows, dtype=int),
                                "cols": np.asarray(hot_cols, dtype=int), "bt_hot": bt_hot, "L_hot": planck(bt_hot),
                                "L_bg_hoy": np.full(bt_hot.shape, np.nan), "L_bg_brazo": planck(t), "half": half,
                                "t_bk_brazo": t})
        return out
    return env


def instalar(familia):
    if familia == "VIIRS":
        import pipeline.process_viirs as pv
        import pipeline.process_viirs_mod as pvm
        mods = {"375": pv, "750": pvm}
        pv.vrp_bg_neighbor_mean_v375 = _fondo_viirs(pv.vrp_bg_neighbor_mean_v375, pv.I04_LAMBDA)
        pvm.vrp_bg_neighbor_mean_v750 = _fondo_viirs(pvm.vrp_bg_neighbor_mean_v750, pvm.M13_LAMBDA)
        for m in mods.values():
            m.first_pass_tests_2_and_3 = _capturar_first_pass(m.first_pass_tests_2_and_3)
            m.cluster_hotspots = _capturar_cumulos(m.cluster_hotspots)
            m.resolve_viirs_pixel_areas = _capturar_areas(m.resolve_viirs_pixel_areas)
        return mods
    import pipeline.process_modis as pm
    pm.compute_local_background = _fondo_modis(pm.compute_local_background, pm)
    pm.first_pass_tests_2_and_3 = _capturar_first_pass(pm.first_pass_tests_2_and_3)
    pm.cluster_hotspots = _capturar_cumulos(pm.cluster_hotspots)
    pm.modis_pixel_areas = _capturar_areas(pm.modis_pixel_areas)
    return {"modis": pm}


# ---------------------------------------------------------------------------------------------------------------
# Selección: vecinos no alertados del cúmulo publicado y por qué quedaron afuera
# ---------------------------------------------------------------------------------------------------------------
def vecinos_no_alertados(fp, cum, fondo, k_area, lam_planck, inner_km):
    """Vecinos 8-conexos NO alertados del cúmulo publicado, con dNTI/dETI del primer pase y su umbral bajo `max`."""
    if fp is None or cum is None or not cum["c0"] or fp.get("eti") is None:
        return {"error": "sin captura de primer pase o de cúmulo"}
    nti, eti = fp["nti"], fp["eti"]
    dnti = nti - dc._nanmean_8neighbors_fast(nti)
    deti = eti - dc._nanmean_8neighbors_fast(eti)
    kw, dg = fp["kw"], fp["diag"]
    if dg.get("mu_dnti") is None:
        return {"error": "primer pase sin pool de fondo"}
    comb = max if kw.get("use_prose_branch") else min
    sce = kw.get("c1_dnti_scene") is not None

    def umbrales(summit):
        c1n = kw.get("c1_dnti_summit", 0.003) if (summit or not sce) else kw["c1_dnti_scene"]
        c1e = kw.get("c1_deti_summit", 0.003) if (summit or not sce) else kw["c1_deti_scene"]
        c2n = kw.get("c2_dnti_summit", 5) if (summit or not sce) else kw["c2_dnti_scene"]
        c2e = kw.get("c2_deti_summit", 5) if (summit or not sce) else kw["c2_deti_scene"]
        return comb(c1n, dg["mu_dnti"] + c2n * dg["sd_dnti"]), comb(c1e, dg["mu_deti"] + c2e * dg["sd_deti"])

    hot = cum["hot"]
    bt = fp["bt"]
    roi1 = fp.get("roi1_mask")
    summit_mask = dc.roi1_summit_mask(fp["dist"], kw.get("inner_km", inner_km), roi1)
    t_bg = fp["t_bg"]
    L_ring = float(lam_planck(np.array([t_bg]))[0])
    filas, vistos = [], set()
    for (i, j) in cum["c0"]:
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                a, b = i + di, j + dj
                if (di, dj) == (0, 0) or (a, b) in vistos or not (0 <= a < hot.shape[0] and 0 <= b < hot.shape[1]):
                    continue
                vistos.add((a, b))
                if hot[a, b]:
                    continue
                thn, the = umbrales(bool(summit_mask[a, b]))
                L_n = float(lam_planck(np.array([bt[a, b]]))[0]) if np.isfinite(bt[a, b]) else float("nan")
                filas.append({"ij": [a, b], "bt_k": round(float(bt[a, b]), 3), "dist_km": round(float(fp["dist"][a, b]), 3),
                              "summit": bool(summit_mask[a, b]), "dnti": float(dnti[a, b]), "deti": float(deti[a, b]),
                              "thr_dnti": float(thn), "thr_deti": float(the),
                              "pasa_t2": bool(dnti[a, b] > thn), "pasa_t3": bool(deti[a, b] > the),
                              "pasa_bt": bool(bt[a, b] > t_bg + fp["bt_sanity_k"]),
                              "dL_anillo": L_n - L_ring,
                              "vrp_si_se_sumara_anillo_mw": max(L_n - L_ring, 0.0) * k_area / 1e6})
    return {"t_bg_k": t_bg, "L_anillo": L_ring, "mu_dnti": dg["mu_dnti"], "sd_dnti": dg["sd_dnti"],
            "mu_deti": dg["mu_deti"], "sd_deti": dg["sd_deti"], "n_cumulo": len(cum["c0"]), "vecinos": filas,
            "suma_vecinos_tibios_anillo_mw": sum(f["vrp_si_se_sumara_anillo_mw"] for f in filas)}


# ---------------------------------------------------------------------------------------------------------------
def gname(g):
    try:
        return g["umm"]["DataGranule"]["Identifiers"][0]["Identifier"]
    except Exception:
        return str(g.get("umm", {}).get("GranuleUR", g))[:160]


def bajar(vol, sensor, nombre, dest):
    from pipeline.fetch import download_granules, search_granules
    stamp = ".".join(nombre.split(".")[1:3])
    dt = datetime.strptime(stamp[1:], "%Y%j.%H%M")
    out = []
    for key in PRODUCTO[sensor]:
        if key is None:
            out.append(None)
            continue
        grs = [g for g in search_granules(key, vol["lat"], vol["lon"], vol["radius_km"], dt) if stamp in gname(g)]
        if key.endswith("_L1B"):
            grs = [g for g in grs if gname(g) == nombre] or grs
        if not grs:
            return None, "sin gránulo %s %s" % (key, stamp)
        got = [Path(p) for p in download_granules(grs[:1], dest) if stamp in Path(p).name]
        if not got:
            return None, "descarga fallida %s %s" % (key, stamp)
        out.append(got[0])
    nota = None if out[0].name == nombre else "L1B reprocesado: %s en lugar de %s" % (out[0].name, nombre)
    return tuple(out), nota


def correr(mod, familia, vol, par, brazo, half=None):
    _reiniciar(brazo)
    if familia == "VIIRS":
        flag = "ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS375" if mod.__name__.endswith("process_viirs") else "ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750"
        setattr(mod, flag, brazo != "control")
        mod.VRP_BG_NEIGHBOR_MAX_HALF_PX = int(half if half else vrp_profile.VRP_BG_NEIGHBOR_MAX_HALF_PX)
        kernel = vol.get("local_kernel_bg", False)
    else:
        kernel = brazo != "control"
    lat, lon = get_detection_anchor(vol)
    kw = dict(vent_lat=lat, vent_lon=lon, vent_radius_km=vol.get("vent_radius_km", 4.0),
              inner_radius_km=vol.get("inner_radius_km"), exclude_zones=vol.get("exclude_zones"),
              active_water_bodies=vol.get("active_water_bodies"),
              lbg_global_compatible=vol.get("lbg_global_compatible", False), local_kernel_bg_compatible=kernel)
    if mod.__name__.endswith("process_viirs"):
        kw["lava_lake_magmatic"] = vol.get("lava_lake_magmatic", False)
    rec = mod.calculate_vrp(par[0], par[1], vol["lat"], vol["lon"], vol["radius_km"], **kw)
    if rec is None:
        return {"error": "calculate_vrp devolvió None"}
    from run_pipeline import VOLCANIC_FEATURES
    store.append_record(vol["name"], rec, volcano_lat=vol["lat"], volcano_lon=vol["lon"], overwrite=True,
                        max_hotspot_dist_km=vol.get("radius_km"),
                        enable_pixel_level_distance_filter=vrp_profile.ENABLE_PIXEL_LEVEL_DISTANCE_FILTER,
                        max_cluster_pixels=vol.get("max_cluster_pixels"), inner_radius_km=vol.get("inner_radius_km"),
                        volcanic_features=VOLCANIC_FEATURES.get(vol["name"]))
    return {"record": {k: rec.get(k) for k in CAMPOS if k in rec}, "n_llamadas_fondo": len(ESTADO["fondo"])}


def fondo_resumen(est):
    """Por píxel alertado del último llamado al fondo: BT, radiancia, fondo de hoy y del brazo, semiancho usado."""
    if not est["fondo"]:
        return None
    f = est["fondo"][-1]
    return [{"ij": [int(r), int(c)], "bt_k": round(float(b), 3), "L_hot": float(lh), "L_bg_hoy": float(lo),
             "L_bg_brazo": float(lb), "half": int(h)}
            for r, c, b, lh, lo, lb, h in zip(f["rows"], f["cols"], f["bt_hot"], f["L_hot"], f["L_bg_hoy"],
                                               f["L_bg_brazo"], f["half"])]


def persistido(granulo):
    d = json.loads((ROOT / "data" / "mirova_equivalent" / ("%s.json" % VOLCAN)).read_text(encoding="utf-8"))
    for r in d["records"]:
        if r.get("granule") == granulo:
            return r
    return None


def control_p1(pers, ctrl):
    if pers is None:
        return False, "sin record persistido con ese gránulo"
    pc, pp = (ctrl.get("primary_cluster") or {}), (pers.get("primary_cluster") or {})
    errs = []
    for campo, a, b in (("pc.vrp_mw", pc.get("vrp_mw"), pp.get("vrp_mw")),
                        ("f5_core_vrp_mw", ctrl.get("f5_core_vrp_mw"), pers.get("f5_core_vrp_mw"))):
        if a is None and b is None:
            continue
        if a is None or b is None or abs(a - b) > max(1e-3, 0.01 * abs(b)):
            errs.append("%s %s contra %s" % (campo, a, b))
    if pc.get("n_pixels") != pp.get("n_pixels"):
        errs.append("n_pixels %s contra %s" % (pc.get("n_pixels"), pp.get("n_pixels")))
    da, db = pc.get("centroid_dist_km"), pp.get("centroid_dist_km")
    if da is None or db is None or abs(da - db) > 0.01:
        errs.append("centroide %s contra %s" % (da, db))
    return not errs, "; ".join(errs)


def igual_exacto(a, b):
    ca = {k: a.get(k) for k in ("primary_cluster", "f5_core_vrp_mw", "anomaly_pixels", "vrp_mw")}
    cb = {k: b.get(k) for k in ("primary_cluster", "f5_core_vrp_mw", "anomaly_pixels", "vrp_mw")}
    return json.dumps(ca, sort_keys=True, default=str) == json.dumps(cb, sort_keys=True, default=str)


def a_json(x):
    if isinstance(x, (np.floating,)):
        return float(x)
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.bool_,)):
        return bool(x)
    if isinstance(x, np.ndarray):
        return x.tolist()
    raise TypeError(type(x))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--familia", choices=("VIIRS", "MODIS"), required=True)
    ap.add_argument("--out", default="out")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    print("perfil %s | ENABLE_TEST1_PATH %s | PROSE %s | B22 %s | D25_375 %s | D25_750 %s | max_half_px %s" % (
        os.environ["VRP_PROFILE"], vrp_profile.ENABLE_TEST1_PATH, vrp_profile.ENABLE_TESTS_23_PROSE_BRANCH,
        vrp_profile.ENABLE_MODIS_B22_PRIMARY, vrp_profile.ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS375,
        vrp_profile.ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750, vrp_profile.VRP_BG_NEIGHBOR_MAX_HALF_PX))
    if vrp_profile.ENABLE_TEST1_PATH or not vrp_profile.ENABLE_TESTS_23_PROSE_BRANCH or not vrp_profile.ENABLE_MODIS_B22_PRIMARY:
        print("el perfil no es K: no se corre")
        return 2
    mods = instalar(a.familia)
    from pipeline.fetch import auth
    from run_pipeline import load_volcanoes
    auth()
    vol = {v["name"]: v for v in load_volcanoes()}[VOLCAN]
    dest = Path(os.environ.get("VRP_TMP_DIR", str(HERE / "granulos")))
    faltan = 0
    for sensor, nombre in PASADAS[a.familia]:
        res = {"sensor": sensor, "granulo": nombre, "ok": False}
        print("\n== %s %s" % (sensor, nombre), flush=True)
        try:
            par, nota = bajar(vol, sensor, nombre, dest)
            if par is None:
                raise RuntimeError(nota)
            res["nota_granulo"] = nota
            if a.familia == "MODIS":
                mod, brazos = mods["modis"], [("control", None), ("nulo", None), ("kernel3", None), ("d25_rad", None)]
                lam = mod.BAND21_LAMBDA
                planck = lambda x, m=mod, l=lam: m.C1 / (l ** 5 * (np.exp(m.C2 / (l * x)) - 1))  # noqa: E731
                k = mod.WOOSTER_COEFF
            else:
                mod = mods["750"] if sensor.endswith("_750") else mods["375"]
                brazos = [("control", None), ("nulo", None), ("d25_h3", 3), ("d25_h1", 1)]
                lam = mod.M13_LAMBDA if sensor.endswith("_750") else mod.I04_LAMBDA
                planck = lambda x, l=lam: vr_planck(x, l)  # noqa: E731
                k = mod.WOOSTER_COEFF
            for brazo, half in brazos:
                r = correr(mod, a.familia, vol, par, brazo, half)
                r["fondo_por_pixel"] = fondo_resumen(ESTADO)
                if brazo in ("d25_h3", "d25_rad", "control"):
                    # Área nadir-fija (A66/A67): uniforme en producción. Se usa la mediana y se deja anotado cuánto
                    # varía, porque la grilla de áreas puede no tener la forma recortada del primer pase.
                    ar = ESTADO["areas"]
                    k_area = None if ar is None else k * float(np.nanmedian(ar))
                    r["area_m2"] = None if ar is None else {"mediana": float(np.nanmedian(ar)), "min": float(np.nanmin(ar)),
                                                            "max": float(np.nanmax(ar))}
                    r["seleccion"] = (vecinos_no_alertados(ESTADO["first_pass"], ESTADO["cumulos"], ESTADO["fondo"],
                                                           k_area, planck, vol.get("inner_radius_km"))
                                      if k_area is not None else {"error": "sin captura de área"})
                    rec_c = r.get("record") or {}
                    if brazo == "control" and k_area is not None and rec_c.get("anomaly_pixels") and rec_c.get("t_bg_k"):
                        # C-K: el píxel de más energía del control, recalculado con k·A y el fondo del anillo.
                        top = rec_c["anomaly_pixels"][0]
                        L_top = float(planck(np.array([top["bt_k"]], dtype=np.float64))[0])
                        L_rg = float(planck(np.array([rec_c["t_bg_k"]], dtype=np.float64))[0])
                        esperado = k_area * max(L_top - L_rg, 0.0) / 1e6
                        r["C_K"] = {"vrp_pixel_record": top["vrp_mw"], "vrp_recalculado": esperado,
                                    "ok": abs(esperado - top["vrp_mw"]) <= max(0.01 * abs(top["vrp_mw"]), 2e-3)}
                res[brazo] = r
                pc = (r.get("record") or {}).get("primary_cluster") or {}
                print("   %-8s pc %s MW (%s px, %s km) | f5 %s | llamadas al fondo %s" % (
                    brazo, pc.get("vrp_mw"), pc.get("n_pixels"), pc.get("centroid_dist_km"),
                    (r.get("record") or {}).get("f5_core_vrp_mw"), r.get("n_llamadas_fondo")), flush=True)
            ctrl = res["control"].get("record") or {}
            res["C_P1"] = control_p1(persistido(nombre), ctrl)
            res["C_N"] = igual_exacto(ctrl, res["nulo"].get("record") or {})
            llam = {b: res[b].get("n_llamadas_fondo") for b, _ in brazos}
            res["C_A"] = (llam["control"] == 0 and all(v and v > 0 for b, v in llam.items() if b != "control"))
            res["llamadas_fondo"] = llam
            res["ok"] = True
            print("   C-P1 %s | C-N %s | C-A %s %s" % (res["C_P1"], res["C_N"], res["C_A"], llam), flush=True)
        except Exception as e:  # noqa: BLE001
            res["error"] = "%s: %s" % (type(e).__name__, e)
            res["traceback"] = traceback.format_exc()
            print("   ERROR", res["error"], flush=True)
            faltan += 1
        finally:
            shutil.rmtree(dest, ignore_errors=True)
        (out / ("%s_%s.json" % (sensor, nombre.split(".")[2]))).write_text(
            json.dumps(res, default=a_json, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\nfaltan %d de %d" % (faltan, len(PASADAS[a.familia])))
    return 2 if faltan else 0


if __name__ == "__main__":
    sys.exit(main())
