# -*- coding: utf-8 -*-
"""S159 frente N: brazos K, K2, C, F y FC de la función de producción y el oráculo de MIROVA sobre el MISMO gránulo
de VIIRS 750, para las pasadas de objetivos_n.json. Sólo lectura: no escribe en data/, no commitea, no hace push.

QUÉ ES CADA BRAZO (ninguno edita pipeline/; todo es reemplazo en memoria del módulo, patrón A75):
  K   pipeline.process_viirs_mod.calculate_vrp tal cual (detector K de producción), y el record pasado por
      pipeline.store.append_record en una carpeta temporal (store.DATA_DIR reemplazado): es lo que se publicaría.
  K2  K otra vez en el mismo proceso (nulo: tiene que dar idéntico, A110/A116).
  C   K sin la compuerta `bt > t_bg + 3 K` del primer pase (D22): first_pass_tests_2_and_3 con bt_sanity_k = -inf.
  F   K con el fondo y la suma del código de MIROVA (MIROVA_VIIRS750_VRP.m l. 61-91): los alertados se apartan, el
      hueco se ensancha con un halo de k x k (k = 3, 5 o 7 según cuántos alertados hay en la escena), el fondo se
      interpola por debajo con fillmissing2 lineal (port de la segunda ronda, Delaunay) y el exceso NO se recorta a
      cero; el cúmulo suma todos sus píxeles (single_pixel_mode apagado). Se hace en la geometría del gránulo (no hay
      remuestreo en producción, ENABLE_UTM_REGRID = False), con la misma radiancia, área y coeficiente que K.
      Piezas: flag ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750 encendido con vrp_bg_neighbor_mean_v750 reemplazado por el
      fondo del código; `np` del módulo reemplazado por un proxy cuyo maximum(x, 0.0) devuelve x (sólo hay tres
      llamadas así en el módulo, las tres son el recorte del VRP; se cuentan); ENABLE_SINGLE_PIXEL_SUB_MW_MODE = False.
  FC  F y C juntos.
  O   el oráculo de la segunda ronda (código de MIROVA completo, detección y VRP) en la grilla UTM de 67 x 67 celdas de
      750 m con la esquina de GEO (375 m menos 187,5 m en x e y), interpolador lineal; variantes: vecino más cercano,
      cúbico, grilla vieja de R2 (esquina de 375 m) lineal y vecino, y anillo con umbrales de cumbre.

Pregunta 1 del instrumento: si un brazo no aplicara su cambio, ¿se vería? Cada reemplazo lleva contador (llamadas
del fondo, del proxy, de la compuerta) y el informe exige contador > 0 en las pasadas donde el brazo puede actuar.
Pregunta 2: si el instrumento estuviera muerto (gránulo vacío, función que no corre), cada pasada queda con estado
distinto de "ok" y el job sale 2 (S141); K2 contra K mide el nulo; K contra el record publicado en data/ mide que el
envoltorio reproduce producción.
Uso: python probe_n.py --objetivos objetivos_n.json --out out --chunk 0 --nchunks 8  [--sin-red] [--solo id,id]
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import sys
import tempfile
import time
import traceback
from pathlib import Path

import numpy as np
from scipy.ndimage import binary_dilation

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, str(RAIZ / "experiments/_s158_audit_r2/oraculo"))
sys.path.insert(0, str(RAIZ / "experiments/_s158_audit_r2/granulos"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import mirova_v750_r2 as ORA  # noqa: E402
import probe_granulos as PG  # noqa: E402

N = 67
CELDA = 750.0
SEMILLAS = 20


# ---------------------------------------------------------------- oráculo en la grilla de MIROVA
def caja(sensible_anillo=False):
    b = PG.caja_mirova()
    if sensible_anillo:
        b[b == 1] = 2
    return b


def grillar(lat, lon, m13, m15, g, ul_x, ul_y, metodos, radio_km=45.0):
    from pyproj import Transformer
    dlat = np.radians(lat - g["centro_lat"])
    dlon = np.radians(lon - g["centro_lon"])
    a = np.sin(dlat / 2) ** 2 + np.cos(np.radians(lat)) * np.cos(np.radians(g["centro_lat"])) * np.sin(dlon / 2) ** 2
    dist = 6371.0 * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))
    sel = np.isfinite(dist) & (dist < radio_km)
    if sel.sum() < 100:
        return None
    t = Transformer.from_crs("EPSG:4326", f"EPSG:{g['epsg']}", always_xy=True)
    x, y = t.transform(lon[sel], lat[sel])
    xs = ul_x + CELDA * (np.arange(N) + 0.5)
    ys = ul_y - CELDA * (np.arange(N) + 0.5)
    X, Y = np.meshgrid(xs, ys)
    return {m: (PG.remuestrear(x, y, m13[sel], X, Y, m), PG.remuestrear(x, y, m15[sel], X, Y, m)) for m in metodos}


def oraculo(m13g, m15g, dayflag, sg, sensible=False):
    box = caja(sensible)
    mask, _lista, d = ORA.detectar(m13g, m15g, box, dayflag, sg, devolver_diag=True)
    r = ORA.vrp(m13g, mask)
    rr, cc = np.nonzero(mask)
    c = N // 2
    out = {"motivo_vacio": d.get("motivo"), "n_abs": d.get("n_abs"), "n_p1": d.get("n_p1"), "n_p2": d.get("n_p2"),
           "npix": r["npix"], "vrp_mw": None if r["npix"] == 0 else float(r["VRP_MW"]),
           "pixeles": [[int(a), int(b), int(box[a, b]), round(float(np.hypot(a - c, b - c) * 0.75), 2),
                        round(float(m13g[a, b]), 5)] for a, b in zip(rr, cc)],
           "nan_m13": int(np.isnan(m13g).sum())}
    if r["npix"]:
        v = [ORA.vrp(m13g, mask, jitter=1e-6, semilla=s)["VRP_MW"] for s in range(SEMILLAS)]
        out["vrp_banda"] = [float(min(v)), float(max(v))]
    return out


# ---------------------------------------------------------------- brazos de producción (reemplazos en memoria)
class _NPSinRecorte:
    """`np` del módulo con maximum(x, 0.0) -> x. Todo lo demás es numpy."""

    def __init__(self):
        self.n = 0

    def __getattr__(self, k):
        return getattr(np, k)

    def maximum(self, a, b, *args, **kw):
        if not args and not kw and isinstance(b, float) and b == 0.0:
            self.n += 1
            return np.array(a, dtype=float, copy=True)
        return np.maximum(a, b, *args, **kw)


def fondo_codigo_en_granulo(bt, alerta, hot_rows, hot_cols, lam_um, jitter=0.0, semilla=0, margen=15):
    """Fondo de MIROVA_VIIRS750_VRP.m l. 61-81 aplicado en la geometría del gránulo. Devuelve el fondo en los
    píxeles (hot_rows, hot_cols). La radiancia es la de producción (bt_to_spectral_radiance)."""
    from pipeline.process_viirs_mod import bt_to_spectral_radiance
    npix = int(alerta.sum())
    k = 3 if npix <= 4 else (5 if npix <= 30 else 7)               # l. 68-74
    r0 = max(int(hot_rows.min()) - margen, 0)
    r1 = min(int(hot_rows.max()) + margen + 1, bt.shape[0])
    c0 = max(int(hot_cols.min()) - margen, 0)
    c1 = min(int(hot_cols.max()) + margen + 1, bt.shape[1])
    L = np.asarray(bt_to_spectral_radiance(bt[r0:r1, c0:c1].astype(np.float64), lam_um), dtype=np.float64)
    enm = L.copy()
    enm[alerta[r0:r1, c0:c1]] = np.nan                              # l. 64-65 (todos los alertados de la escena)
    excl = binary_dilation(np.isnan(enm), structure=np.ones((k, k), bool))   # l. 76-77
    enm[excl] = np.nan                                              # l. 78
    fondo = ORA._fillmissing2_lineal(enm, jitter=jitter, semilla=semilla)   # l. 81
    return fondo[hot_rows - r0, hot_cols - c0], k


def correr_brazo(nombre, PVM, volcan, l1b, geo, captura):
    """Corre calculate_vrp con los reemplazos del brazo y devuelve el resultado crudo (o None)."""
    import pipeline.process_viirs_mod as M
    from run_pipeline import load_volcanoes
    from pipeline.geo_utils import get_detection_anchor
    orig = {k: getattr(M, k) for k in ("first_pass_tests_2_and_3", "cluster_hotspots", "vrp_bg_neighbor_mean_v750",
                                       "np", "ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750",
                                       "ENABLE_SINGLE_PIXEL_SUB_MW_MODE")}
    cont = {"compuerta": 0, "fondo": 0, "proxy": None, "cluster": 0}

    def fp(*a, **kw):
        if nombre in ("C", "FC"):
            kw["bt_sanity_k"] = -np.inf
            cont["compuerta"] += 1
        hot, diag = orig["first_pass_tests_2_and_3"](*a, **kw)
        captura["fp_mask"] = np.array(hot, dtype=bool)
        return hot, diag

    def ch(hot_mask_2d, *a, **kw):
        res = orig["cluster_hotspots"](hot_mask_2d, *a, **kw)
        cont["cluster"] += 1
        captura["hot_mask"] = np.array(hot_mask_2d, dtype=bool)
        captura["clusters"] = [{"pixel_indices": c["pixel_indices"], "vrp_mw": c.get("vrp_mw"),
                                "centroid_dist_km": c.get("centroid_dist_km")} for c in res[:5]]
        return res

    def fondo(bt, alerta, hot_rows, hot_cols, legacy, *, max_half_px):
        cont["fondo"] += 1
        l_bk, k = fondo_codigo_en_granulo(bt, alerta, hot_rows, hot_cols, M.M13_LAMBDA)
        banda = [fondo_codigo_en_granulo(bt, alerta, hot_rows, hot_cols, M.M13_LAMBDA, jitter=1e-6, semilla=s)[0]
                 for s in range(SEMILLAS)]
        L_hot = np.asarray(M.bt_to_spectral_radiance(bt[hot_rows, hot_cols].astype(np.float64), M.M13_LAMBDA))
        captura["F_pix"] = {"rows": hot_rows.tolist(), "cols": hot_cols.tolist(), "L_hot": L_hot.tolist(),
                            "L_bk": l_bk.tolist(), "L_bk_banda": [b.tolist() for b in banda], "k": k,
                            "L_bg_anillo": float(np.asarray(legacy).ravel()[0])}
        sin = ~np.isfinite(l_bk)
        return np.where(sin, legacy, l_bk), int(sin.sum())

    try:
        M.first_pass_tests_2_and_3 = fp
        M.cluster_hotspots = ch
        if nombre in ("F", "FC"):
            prox = _NPSinRecorte()
            cont["proxy"] = prox
            M.np = prox
            M.vrp_bg_neighbor_mean_v750 = fondo
            M.ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750 = True
            M.ENABLE_SINGLE_PIXEL_SUB_MW_MODE = False
        v = load_volcanoes(volcan)[0]
        vl, vo = get_detection_anchor(v)
        r = M.calculate_vrp(
            l1b, geo, v["lat"], v["lon"], v["radius_km"], vent_lat=vl, vent_lon=vo,
            vent_radius_km=v.get("vent_radius_km", 4.0), inner_radius_km=v.get("inner_radius_km"),
            exclude_zones=v.get("exclude_zones"), active_water_bodies=v.get("active_water_bodies"),
            lbg_global_compatible=v.get("lbg_global_compatible", False),
            local_kernel_bg_compatible=v.get("local_kernel_bg", False))
    finally:
        for k, val in orig.items():
            setattr(M, k, val)
    captura["contadores"] = {"compuerta": cont["compuerta"], "fondo": cont["fondo"], "cluster": cont["cluster"],
                             "proxy_recortes": None if cont["proxy"] is None else cont["proxy"].n}
    return r, v


def guardar_como_store(volcan, v, r):
    """El record que store.append_record escribiría, en una carpeta temporal (store.DATA_DIR reemplazado)."""
    import pipeline.store as S
    from run_pipeline import VOLCANIC_FEATURES
    import pipeline.profile as P
    tmp = Path(tempfile.mkdtemp(prefix="s159n_"))
    orig = S.DATA_DIR
    try:
        S.DATA_DIR = tmp
        S.append_record(volcan, copy.deepcopy(r), volcano_lat=v["lat"], volcano_lon=v["lon"], overwrite=True,
                        max_hotspot_dist_km=v.get("radius_km"),
                        enable_pixel_level_distance_filter=P.ENABLE_PIXEL_LEVEL_DISTANCE_FILTER,
                        max_cluster_pixels=v.get("max_cluster_pixels"), inner_radius_km=v.get("inner_radius_km"),
                        volcanic_features=VOLCANIC_FEATURES.get(volcan))
        f = tmp / f"{volcan}.json"
        if not f.exists():
            return None
        recs = json.loads(f.read_text(encoding="utf-8"))["records"]
        return recs[-1] if recs else None
    finally:
        S.DATA_DIR = orig
        for q in tmp.glob("*"):
            q.unlink()
        tmp.rmdir()


CAMPOS = ["primary_cluster", "distance_class", "vrp_mw", "vrp_mir_mw", "discarded_reason", "triggered_test1",
          "vrp_vent_mw", "t_max_k", "sensor", "f5_core_vrp_mw", "n_anomalous_pixels", "t_bg_k", "datetime_utc",
          "final_hotspot_dist_km", "final_hotspot_source", "sensor_zenith_deg", "granule", "diag_n_first_pass_pixels",
          "diag_n_second_pass_recapture"]


def resumen_brazo(nombre, PVM, volcan, l1b, geo):
    cap = {}
    t0 = time.time()
    r, v = correr_brazo(nombre, PVM, volcan, l1b, geo, cap)
    out = {"segundos": round(time.time() - t0, 1), "contadores": cap.get("contadores")}
    if not r:
        out["record"] = None
        return out
    st = guardar_como_store(volcan, v, r)
    out["record"] = None if st is None else {k: st.get(k) for k in CAMPOS}
    out["crudo_pc"] = r.get("primary_cluster")
    out["n_hot"] = int(cap["hot_mask"].sum()) if "hot_mask" in cap else None
    if cap.get("clusters"):
        pi = cap["clusters"][0]["pixel_indices"]
        fp = cap.get("fp_mask")
        out["pc_pix"] = [list(p) for p in pi]
        out["pc_pix_primer_pase"] = None if fp is None else int(sum(bool(fp[i, j]) for i, j in pi))
        if "F_pix" in cap:  # banda del cúmulo por la triangulación del fondo
            F = cap["F_pix"]
            pos = {(a, b): n for n, (a, b) in enumerate(zip(F["rows"], F["cols"]))}
            idx = [pos[tuple(p)] for p in pi if tuple(p) in pos]
            import pipeline.process_viirs_mod as M
            kf = M.NADIR_PIXEL_AREA_M2 * M.WOOSTER_COEFF / 1e6
            Lh = np.array(F["L_hot"])[idx]
            out["F_pc_central"] = float(np.sum(Lh - np.array(F["L_bk"])[idx]) * kf)
            vs = [float(np.sum(Lh - np.array(b)[idx]) * kf) for b in F["L_bk_banda"]]
            out["F_pc_banda"] = [min(vs), max(vs)]
            out["F_k"] = F["k"]
            out["F_L_bg_anillo"] = F["L_bg_anillo"]
            out["F_L_bk_pc"] = [float(x) for x in np.array(F["L_bk"])[idx]]
            out["F_L_hot_pc"] = [float(x) for x in Lh]
            out["F_escena_central"] = float(np.sum(np.array(F["L_hot"]) - np.array(F["L_bk"])) * kf)
    return out


# ---------------------------------------------------------------- bajada
def bajar_por_tag(tag, lat, lon, destino):
    """Estrato diurno: no hay record nuestro. Se busca en CMR por nombre de gránulo con la hora de MIROVA, en los
    tres satélites (la búsqueda de producción por día y caja filtra lo diurno, por eso no sirve aquí)."""
    import earthaccess
    from pipeline.fetch import download_granules
    for pref, vers in (("VNP", ("2",)), ("VJ1", ("2.1", "2")), ("VJ2", ("2.1",))):
        par = {}
        for tipo in ("02", "03"):
            for sn in (f"{pref}{tipo}MOD", f"{pref}{tipo}MOD_NRT"):
                h = []
                for ver in vers:
                    try:
                        h = earthaccess.search_data(short_name=sn, version=ver, granule_name=f"{sn}.{tag}.*", count=5)
                    except Exception as e:  # noqa: BLE001
                        print(f"   busqueda {sn} {ver} fallo: {type(e).__name__}: {str(e)[:100]}", flush=True)
                        h = []
                    if h:
                        break
                if h:
                    par[tipo] = h[:1]
                    break
        if len(par) == 2:
            p1 = download_granules(par["02"], destino)
            p2 = download_granules(par["03"], destino)
            return ([q for q in p1 if q.suffix in (".nc", ".h5")][0],
                    [q for q in p2 if q.suffix in (".nc", ".h5")][0]), None
    return None, "sin_granulo_diurno"


def bajar_con_reintentos(nombre, destino, intentos=3):
    """CMR da ReadTimeout transitorios (humo, run 39680724047: Chaitén 2026-10-06). Reintenta la búsqueda."""
    err = None
    for n in range(intentos):
        par, err = PG.bajar(nombre, destino)
        if not err:
            return par, None
        print(f"   intento {n + 1} de {intentos}: {err}", flush=True)
        time.sleep(30)
    return None, err


def procesar_granulo(objs, destino, outdir, sin_k=False):
    """Todas las pasadas de un mismo gránulo con una sola bajada."""
    o0 = objs[0]
    PG.LATLON[0], PG.LATLON[1] = o0["grilla"]["centro_lat"], o0["grilla"]["centro_lon"]
    if o0.get("granule"):
        par, err = bajar_con_reintentos(o0["granule"], destino)
    else:
        h = o0["hora_utc"]
        from datetime import datetime
        dt = datetime.strptime(h, "%Y-%m-%d %H:%M")
        par, err = bajar_por_tag(f"A{dt:%Y%j}.{dt:%H%M}", o0["grilla"]["centro_lat"], o0["grilla"]["centro_lon"], destino)
    if err:
        return [{"id": o["id"], "volcan": o["volcan"], "hora_utc": o["hora_utc"], "estado": err} for o in objs]
    l1b, geo = par
    rad, attrs = PG.leer_l1b(l1b)
    lat, lon, ang = PG.leer_geo(geo)
    res = []
    for o in objs:
        t0 = time.time()
        r = {"id": o["id"], "volcan": o["volcan"], "hora_utc": o["hora_utc"], "archivos": [l1b.name, geo.name]}
        try:
            g = o["grilla"]
            dlat = np.radians(lat - g["centro_lat"])
            dlon = np.radians(lon - g["centro_lon"])
            a = (np.sin(dlat / 2) ** 2 + np.cos(np.radians(lat)) * np.cos(np.radians(g["centro_lat"]))
                 * np.sin(dlon / 2) ** 2)
            dist = 6371.0 * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))
            if not np.isfinite(dist).any() or np.nanmin(dist) > 5:
                r["estado"] = "volcan_fuera_del_granulo"
                res.append(r)
                continue
            i0 = np.unravel_index(np.nanargmin(np.where(np.isfinite(dist), dist, np.inf)), dist.shape)
            geom = {k: float(v[i0]) for k, v in ang.items()}
            r["geometria_centro"] = geom
            dayflag = 0 if geom.get("solar_zenith", 180) > 90 else 1
            sg = ORA.sunglint_deg(geom.get("sensor_zenith", 0), geom.get("solar_zenith", 0),
                                  geom.get("sensor_azimuth", 0), geom.get("solar_azimuth", 0))
            r["dayflag"], r["sunglint"] = dayflag, sg
            orc = {}
            gg = grillar(lat, lon, rad["M13"], rad["M15"], g, g["ul_x"], g["ul_y"], ("linear", "nearest", "cubic"))
            gr2 = grillar(lat, lon, rad["M13"], rad["M15"], g, g["ul_x_r2"], g["ul_y_r2"], ("linear", "nearest"))
            if gg is None:
                r["estado"] = "volcan_fuera_del_granulo"
                res.append(r)
                continue
            for m, (a13, a15) in gg.items():
                orc[f"geo_{m}"] = oraculo(a13, a15, dayflag, sg)
            orc["geo_linear_anillo_sensible"] = oraculo(*gg["linear"], dayflag, sg, sensible=True)
            for m, (a13, a15) in gr2.items():
                orc[f"r2_{m}"] = oraculo(a13, a15, dayflag, sg)
            r["oraculo"] = orc
            np.savez_compressed(outdir / f"grilla_{o['id']:03d}.npz", m13=gg["linear"][0], m15=gg["linear"][1])
            if not sin_k and dayflag == 0:
                r["brazos"] = {}
                for b in ("K", "K2", "C", "F", "FC"):
                    try:
                        r["brazos"][b] = resumen_brazo(b, None, o["volcan"], l1b, geo)
                    except Exception as e:  # noqa: BLE001
                        r["brazos"][b] = {"error": f"{type(e).__name__}: {e}", "traza": traceback.format_exc()[-1200:]}
            r["estado"] = "ok"
        except Exception as e:  # noqa: BLE001
            r["estado"] = f"error: {type(e).__name__}: {e}"
            r["traza"] = traceback.format_exc()[-1500:]
        r["segundos"] = round(time.time() - t0, 1)
        res.append(r)
    for q in (l1b, geo):
        try:
            q.unlink()
        except OSError:
            pass
    return res


def prueba_sin_red():
    """(1) El fondo del código en la geometría del gránulo, aplicado a una matriz de 67 x 67 como si fuera un
    gránulo, da exactamente el L_bk del oráculo (misma función de relleno). (2) El proxy sólo intercepta
    maximum(x, 0.0). (3) Los reemplazos se restauran."""
    from pipeline.process_viirs_mod import bt_to_spectral_radiance, M13_LAMBDA
    rng = np.random.default_rng(3)
    bt = 265 + rng.normal(0, 0.5, (67, 67))
    bt[33, 33] = 300.0
    bt[33, 34] = 285.0
    alerta = np.zeros_like(bt, bool)
    alerta[33, 33] = alerta[33, 34] = True
    hr, hc = np.nonzero(alerta)
    fondo, k = fondo_codigo_en_granulo(bt, alerta, hr, hc, M13_LAMBDA, margen=100)
    L = np.asarray(bt_to_spectral_radiance(bt, M13_LAMBDA))
    ref = ORA.vrp(L, alerta)
    lbk_ref = float(np.nansum(ref["fondo"][alerta]))
    print("fondo granulo", float(fondo.sum()), "fondo oraculo", lbk_ref, "k", k)
    assert abs(float(fondo.sum()) - lbk_ref) < 1e-9 and k == 3
    p = _NPSinRecorte()
    x = np.array([-1.0, 2.0])
    assert np.array_equal(p.maximum(x, 0.0), x) and p.n == 1
    assert np.array_equal(p.maximum(x, 1.0), np.array([1.0, 2.0])) and p.n == 1
    assert p.pi == np.pi
    import pipeline.process_viirs_mod as M
    assert M.np is np and M.ENABLE_SINGLE_PIXEL_SUB_MW_MODE is True
    print("PRUEBA SIN RED OK", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--objetivos", default=str(AQUI / "objetivos_n.json"))
    ap.add_argument("--out", default="out")
    ap.add_argument("--chunk", type=int, default=0)
    ap.add_argument("--nchunks", type=int, default=1)
    ap.add_argument("--solo", default="")
    ap.add_argument("--sin-red", action="store_true")
    a = ap.parse_args()
    prueba_sin_red()
    PG.prueba_sintetica()
    if a.sin_red:
        return 0
    if not os.environ.get("EARTHDATA_TOKEN", "").strip():
        print("EARTHDATA_TOKEN vacio: no se corre (A71)")
        return 1
    from pipeline.fetch import auth
    auth()
    outdir = Path(a.out)
    outdir.mkdir(parents=True, exist_ok=True)
    destino = Path(os.environ.get("VRP_TMP_DIR", "/tmp/vrp_tmp")) / "granulos"
    objs = json.loads(Path(a.objetivos).read_text(encoding="utf-8"))
    if a.solo:
        quiero = {int(x) for x in a.solo.split(",")}
        objs = [o for o in objs if o["id"] in quiero]
    grupos = {}
    for o in objs:
        grupos.setdefault(o.get("granule") or f"diurna|{o['volcan']}|{o['hora_utc']}", []).append(o)
    claves = sorted(grupos)
    mias = [k for n, k in enumerate(claves) if n % a.nchunks == a.chunk]
    n_obj = sum(len(grupos[k]) for k in mias)
    print(f"chunk {a.chunk}/{a.nchunks}: {len(mias)} granulos, {n_obj} pasadas", flush=True)
    resultados, faltan = [], 0
    for k in mias:
        print(f"== {k} ({len(grupos[k])} pasadas)", flush=True)
        try:
            rs = procesar_granulo(grupos[k], destino, outdir)
        except Exception as e:  # noqa: BLE001
            rs = [{"id": o["id"], "volcan": o["volcan"], "hora_utc": o["hora_utc"],
                   "estado": f"error: {type(e).__name__}: {e}", "traza": traceback.format_exc()[-1500:]}
                  for o in grupos[k]]
        for r in rs:
            if r.get("estado") != "ok":
                faltan += 1
            b = r.get("brazos") or {}
            pcs = {n: ((x.get("record") or {}).get("primary_cluster") or {}).get("vrp_mw") for n, x in b.items()}
            ol = (r.get("oraculo") or {}).get("geo_linear", {})
            print(f"   {r['id']} {r['volcan']} {r['hora_utc']} estado={r.get('estado')} O={ol.get('npix')}px "
                  f"{ol.get('vrp_mw')} | pc {pcs}", flush=True)
            resultados.append(r)
        (outdir / f"resultados_{a.chunk:02d}.json").write_text(json.dumps(resultados, default=float), encoding="utf-8")
    print(f"pasadas sin procesar: {faltan} de {n_obj}", flush=True)
    return 2 if faltan else 0


if __name__ == "__main__":
    sys.exit(main())
