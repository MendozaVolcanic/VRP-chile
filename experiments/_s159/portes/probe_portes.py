# -*- coding: utf-8 -*-
"""S159 frente PORTES: el código de VIIRS 750 de MIROVA portado a VIIRS 375 y a MODIS, y la producción (K), sobre el
MISMO gránulo, para las pasadas de objetivos_portes.json. Sólo lectura: no escribe en data/, no commitea, no hace push.

QUÉ CORRE EN CADA PASADA
  K      la función de producción del sensor (pipeline.process_viirs.calculate_vrp en VIIRS 375,
         pipeline.process_modis.calculate_vrp en MODIS), con los argumentos de scripts/run_pipeline.py, y el record
         pasado por pipeline.store.append_record en una carpeta temporal (store.DATA_DIR reemplazado). Control: tiene
         que reproducir el record publicado en data/.
  PORT   mirova_port.correr (detección + fondo + suma del .m, con las longitudes de onda y el coeficiente del sensor)
         sobre la grilla UTM de MIROVA del sensor (GEO H1/H2), remuestreo lineal (el que reprodujo a MIROVA en N-2).
         Variantes: caja física (principal), caja de 7 x 7 y 21 x 21 celdas, caja física con ROI1 sensible; en MODIS
         además banda 21 primaria y geolocalización interpolada de la grilla de 5 km (la de producción).
  CTL750 en las 10 pasadas de control de VIIRS 750: el port con la configuración de 750 tiene que reproducir el
         oráculo del frente N (npix y VRP).

Pregunta 1 del instrumento: si el port o K no corrieran, ¿se vería? Cada pasada guarda estado distinto de "ok" si
falla la bajada, la lectura o el volcán no está en el gránulo, y el job sale 2 (S141). K contra el record publicado
y CTL750 contra N miden el envoltorio. Pregunta 2: una grilla vacía (volcán fuera, lectura muerta) da
«grilla_incompleta» o «escena_invalida», nunca 0 píxeles silencioso.
Uso: python probe_portes.py --objetivos objetivos_portes.json --out out --sensor VIIRS375 --chunk 0 --nchunks 8
     [--sin-red] [--solo id,id]
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import re
import sys
import tempfile
import time
import traceback
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, str(AQUI))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import mirova_port as MP  # noqa: E402

ORA = MP.ORA
FLAG_MIN = 65528   # DN >= 65528: banderas del L1B de VIIRS (UserGuide Aug 2021, Tabla C.1), como el probe de R2
RADIO_KM = 45.0
SEMILLAS = 20


# ---------------------------------------------------------------- bajada
def _buscar(sn, ver, patron, intentos=3):
    import earthaccess
    for n in range(intentos):
        try:
            return earthaccess.search_data(short_name=sn, version=ver, granule_name=patron, count=5)
        except Exception as e:  # noqa: BLE001  (ReadTimeout de CMR)
            print(f"   busqueda {sn} v{ver} intento {n + 1}: {type(e).__name__}: {str(e)[:100]}", flush=True)
            time.sleep(20)
    return []


def _buscar_ventana(sn, ver, tag, lat, lon, minutos=6):
    import earthaccess
    from datetime import datetime, timedelta
    t = datetime.strptime(tag[1:], "%Y%j.%H%M")
    for n in range(3):
        try:
            h = earthaccess.search_data(short_name=sn, version=ver,
                                        temporal=((t - timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                                                  (t + timedelta(minutes=minutos)).strftime("%Y-%m-%dT%H:%M:%SZ")),
                                        bounding_box=(lon - 0.5, lat - 0.5, lon + 0.5, lat + 0.5), count=10)
            return [g for g in h if tag in str(g["umm"].get("GranuleUR", ""))]
        except Exception as e:  # noqa: BLE001
            print(f"   ventana {sn} v{ver} intento {n + 1}: {type(e).__name__}: {str(e)[:100]}", flush=True)
            time.sleep(20)
    return []


def productos(granule):
    """(lista de (short_name, version) para L1B, idem GEO, tag, col) desde el nombre del gránulo del record."""
    m = re.match(r"(MOD|MYD)021KM\.(A\d{7}\.\d{4})\.(\d{3})", granule)
    if m:
        p, tag, col = m.groups()
        vs = ("6.1", "6.1NRT")
        return [(f"{p}021KM", v) for v in vs], [(f"{p}03", v) for v in vs], tag, col
    m = re.match(r"(VNP|VJ1|VJ2)02(IMG|MOD)(?:_NRT)?\.(A\d{7}\.\d{4})\.(\d{3})", granule)
    p, typ, tag, col = m.groups()
    vers = {"002": ("2",), "021": ("2.1", "2"), "001": ("1",)}.get(col, ("2",))
    l1b = [(f"{p}02{typ}{s}", v) for s in ("", "_NRT") for v in vers]
    geo = [(f"{p}03{typ}{s}", v) for s in ("", "_NRT") for v in vers]
    return l1b, geo, tag, col


def bajar_par(granule, lat, lon, destino):
    from pipeline.fetch import download_granules
    l1b_c, geo_c, tag, col = productos(granule)
    par = []
    for cands in (l1b_c, geo_c):
        h = []
        for sn, ver in cands:
            h = _buscar(sn, ver, f"{sn}.{tag}.{col}*")
            if h:
                break
        if not h:
            for sn, ver in cands:
                h = _buscar_ventana(sn, ver, tag, lat, lon)
                if h:
                    break
        if not h:
            return None, f"sin_granulo_{cands[0][0]}"
        p = download_granules(h[:1], destino)
        arch = [q for q in p if q.suffix in (".nc", ".h5", ".hdf")]
        if not arch:
            return None, f"descarga_vacia_{cands[0][0]}"
        par.append(arch[0])
    return tuple(par), None


# ---------------------------------------------------------------- lectura (recortada a la zona del volcán)
def _haversine(lat, lon, lat0, lon0):
    dlat = np.radians(lat - lat0)
    dlon = np.radians(lon - lon0)
    a = np.sin(dlat / 2) ** 2 + np.cos(np.radians(lat)) * np.cos(np.radians(lat0)) * np.sin(dlon / 2) ** 2
    return 6371.0 * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def _ventana(lat, lon, lat0, lon0, radio):
    """Caja de filas y columnas que contiene todos los píxeles a < radio km (sobre una submuestra de 1 de cada 8)."""
    s = 8
    d = _haversine(lat[::s, ::s].astype(np.float64), lon[::s, ::s].astype(np.float64), lat0, lon0)
    ok = np.isfinite(d) & (d < radio + 15)
    if not ok.any():
        return None, float(np.nanmin(d)) if np.isfinite(d).any() else None
    rr, cc = np.nonzero(ok)
    r0, r1 = max(rr.min() * s - s, 0), min(rr.max() * s + 2 * s, lat.shape[0])
    c0, c1 = max(cc.min() * s - s, 0), min(cc.max() * s + 2 * s, lat.shape[1])
    return (slice(r0, r1), slice(c0, c1)), None


def leer_viirs(l1b, geo, bandas, lat0, lon0):
    import h5py
    with h5py.File(geo, "r") as f:
        gd = f["geolocation_data"]
        lat = gd["latitude"][:]
        lon = gd["longitude"][:]
        lat = np.where(lat < -90, np.nan, lat)
        lon = np.where(lon < -180, np.nan, lon)
        w, dmin = _ventana(lat, lon, lat0, lon0, RADIO_KM)
        if w is None:
            return None, dmin
        out = {"lat": lat[w].astype(np.float64), "lon": lon[w].astype(np.float64)}
        for k in ("sensor_zenith", "sensor_azimuth", "solar_zenith", "solar_azimuth"):
            if k in gd:
                ds = gd[k]
                sf = float(np.asarray(ds.attrs.get("scale_factor", 1.0)).ravel()[0])
                out[k] = ds[w[0], w[1]].astype(np.float64) * sf
    with h5py.File(l1b, "r") as f:
        obs = f["observation_data"]
        out["sat"] = {}
        for nombre, b in zip(("mir", "tir"), bandas):
            ds = obs[b]
            dn = ds[w[0], w[1]].astype(np.float64)
            sf = float(np.asarray(ds.attrs.get("scale_factor", 1.0)).ravel()[0])
            ao = float(np.asarray(ds.attrs.get("add_offset", 0.0)).ravel()[0])
            rad = dn * sf + ao
            rad[dn >= FLAG_MIN] = np.nan
            out[nombre] = rad
            q = f"{b}_quality_flags"
            out["sat"][b] = int(((obs[q][w[0], w[1]] & 0b100) != 0).sum()) if q in obs else None
    return out, None


def leer_modis(l1b, geo, lat0, lon0):
    """Radiancias por la función de producción (B21, B22, B31; DN > 32767 -> NaN) y dos geolocalizaciones: la del
    MxD03 (1 km, la del producto de geolocalización) y la interpolada de la grilla de 5 km (la que usa producción)."""
    from pipeline.process_modis import read_modis_l1b, merge_mir_bands
    from pyhdf.SD import SD, SDC
    d = read_modis_l1b(l1b)
    sd = SD(str(geo), SDC.READ)
    lat3 = sd.select("Latitude").get().astype(np.float64)
    lon3 = sd.select("Longitude").get().astype(np.float64)
    ang = {}
    for k, nm in (("sensor_zenith", "SensorZenith"), ("sensor_azimuth", "SensorAzimuth"),
                  ("solar_zenith", "SolarZenith"), ("solar_azimuth", "SolarAzimuth")):
        s = sd.select(nm)
        ang[k] = s.get().astype(np.float64) * float(s.attributes().get("scale_factor", 1.0))
    sd.end()
    lat3[(lat3 < -90) | (lat3 > 90)] = np.nan
    lon3[(lon3 < -180) | (lon3 > 180)] = np.nan
    if lat3.shape != d["band21"].shape:
        return None, f"forma_geo_{lat3.shape}_vs_{d['band21'].shape}"
    w, dmin = _ventana(lat3, lon3, lat0, lon0, RADIO_KM)
    if w is None:
        return None, dmin
    b21, b22, b31 = (np.asarray(d[k], np.float64)[w] for k in ("band21", "band22", "band31"))
    out = {"lat": lat3[w], "lon": lon3[w], "lat5": np.asarray(d["lat"], np.float64)[w],
           "lon5": np.asarray(d["lon"], np.float64)[w], "mir": merge_mir_bands(b21, b22, True),
           "mir_b21": merge_mir_bands(b21, b22, False), "tir": b31,
           "sat": {"b22_nan_con_b21": int((np.isnan(b22) & np.isfinite(b21)).sum())}}
    for k, v in ang.items():
        out[k] = v[w]
    return out, None


# ---------------------------------------------------------------- grilla
def grillar(crop, g, epsg, mir_k="mir", tir_k="tir", lat_k="lat", lon_k="lon"):
    from pyproj import Transformer
    from scipy.interpolate import griddata
    lat, lon = crop[lat_k], crop[lon_k]
    t = Transformer.from_crs("EPSG:4326", f"EPSG:{epsg}", always_xy=True)
    # como el probe de N (grillar): sólo los píxeles a < 45 km del centro, para que la triangulación sea la misma
    ok = np.isfinite(lat) & np.isfinite(lon)
    if "centro_lat" in g:
        with np.errstate(invalid="ignore"):
            ok &= _haversine(lat, lon, g["centro_lat"], g["centro_lon"]) < RADIO_KM
    x, y = t.transform(lon[ok], lat[ok])
    X, Y = MP.centros(g)
    res = []
    for k in (mir_k, tir_k):
        v = crop[k][ok]
        f = np.isfinite(v)
        res.append(griddata(np.column_stack([x[f], y[f]]), v[f], (X, Y), method="linear"))
    return res


# ---------------------------------------------------------------- producción K
def correr_k(b, volcan, l1b, geo):
    from run_pipeline import load_volcanoes
    from pipeline.geo_utils import get_detection_anchor
    v = load_volcanoes(volcan)[0]
    vl, vo = get_detection_anchor(v)
    kw = dict(vent_lat=vl, vent_lon=vo, vent_radius_km=v.get("vent_radius_km", 4.0),
              inner_radius_km=v.get("inner_radius_km"), exclude_zones=v.get("exclude_zones"),
              active_water_bodies=v.get("active_water_bodies"),
              lbg_global_compatible=v.get("lbg_global_compatible", False),
              local_kernel_bg_compatible=v.get("local_kernel_bg", False))
    if b == "VIIRS375":
        from pipeline import process_viirs as M
        kw["lava_lake_magmatic"] = v.get("lava_lake_magmatic", False)
    else:
        from pipeline import process_modis as M
    r = M.calculate_vrp(l1b, geo, v["lat"], v["lon"], v["radius_km"], **kw)
    return r, v


def guardar_como_store(volcan, v, r):
    import pipeline.store as S
    from run_pipeline import VOLCANIC_FEATURES
    import pipeline.profile as P
    tmp = Path(tempfile.mkdtemp(prefix="s159p_"))
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
          "final_hotspot_dist_km", "final_hotspot_source", "sensor_zenith_deg", "granule"]


def resumen_k(b, volcan, l1b, geo):
    t0 = time.time()
    r, v = correr_k(b, volcan, l1b, geo)
    out = {"segundos": round(time.time() - t0, 1)}
    if not r:
        out["record"] = None
        return out
    st = guardar_como_store(volcan, v, r)
    if st is None:
        out["record"] = None
        return out
    rec = {k: st.get(k) for k in CAMPOS}
    if rec.get("f5_core_vrp_mw") is None:
        rec["anomaly_pixels"] = [{k: p.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")}
                                 for p in (st.get("anomaly_pixels") or [])]
    out["record"] = rec
    return out


# ---------------------------------------------------------------- una pasada
def procesar(o, destino, outdir, sin_k=False):
    g = o["grilla"]
    b = o["b"]
    t0 = time.time()
    r = {"id": o["id"], "volcan": o["volcan"], "hora_utc": o["hora_utc"], "b": b, "granule": o["granule"]}
    par, err = bajar_par(o["granule"], g["centro_lat"], g["centro_lon"], destino)
    if err:
        r["estado"] = err
        return r
    l1b, geo = par
    r["archivos"] = [l1b.name, geo.name]
    try:
        if b == "MODIS":
            crop, dmin = leer_modis(l1b, geo, g["centro_lat"], g["centro_lon"])
        else:
            crop, dmin = leer_viirs(l1b, geo, ("I04", "I05") if b == "VIIRS375" else ("M13", "M15"),
                                    g["centro_lat"], g["centro_lon"])
        if crop is None:
            r["estado"] = "volcan_fuera_del_granulo"
            r["dist_min_km"] = dmin
            return r
        d = _haversine(crop["lat"], crop["lon"], g["centro_lat"], g["centro_lon"])
        if not np.isfinite(d).any() or np.nanmin(d) > 5:
            r["estado"] = "volcan_fuera_del_granulo"
            r["dist_min_km"] = None if not np.isfinite(d).any() else float(np.nanmin(d))
            return r
        i0 = np.unravel_index(np.nanargmin(np.where(np.isfinite(d), d, np.inf)), d.shape)
        geom = {k: float(crop[k][i0]) for k in ("sensor_zenith", "sensor_azimuth", "solar_zenith", "solar_azimuth")
                if k in crop}
        r["geometria_centro"] = geom
        r["saturados"] = crop.get("sat")
        dayflag = 0 if geom.get("solar_zenith", 180) > 90 else 1
        sg = ORA.sunglint_deg(geom.get("sensor_zenith", 0), geom.get("solar_zenith", 0),
                              geom.get("sensor_azimuth", 0), geom.get("solar_azimuth", 0))
        r["dayflag"], r["sunglint"] = dayflag, sg
        cfg = MP.SENSORES[b]
        port = {}
        mir, tir = grillar(crop, g, g["epsg"])
        guardar = {"mir": mir.astype(np.float32), "tir": tir.astype(np.float32)}
        if np.isnan(mir).sum() > mir.size // 2:
            r["port_estado"] = "grilla_incompleta"
        modos = ("fisica",) if b == "VIIRS750" else ("fisica", "pixel", "sensible")
        for m in modos:
            port[m] = MP.correr(mir, tir, g, g["X0"], g["Y0"], dayflag, sg, cfg, modo=m, semillas=SEMILLAS)
        if b == "MODIS":
            m21, t21 = grillar(crop, g, g["epsg"], mir_k="mir_b21")
            port["fisica_b21"] = MP.correr(m21, t21, g, g["X0"], g["Y0"], dayflag, sg, MP.SENSORES["MODIS_B21"],
                                           semillas=SEMILLAS)
            m5, t5 = grillar(crop, g, g["epsg"], lat_k="lat5", lon_k="lon5")
            port["fisica_geo5km"] = MP.correr(m5, t5, g, g["X0"], g["Y0"], dayflag, sg, cfg, semillas=SEMILLAS)
            guardar.update({"mir_b21": m21.astype(np.float32), "mir_geo5": m5.astype(np.float32),
                            "tir_geo5": t5.astype(np.float32)})
        r["port"] = port
        np.savez_compressed(outdir / f"grilla_{o['id']:03d}.npz", **guardar)
        if not sin_k and b != "VIIRS750":
            try:
                r["K"] = resumen_k(b, o["volcan"], l1b, geo)
            except Exception as e:  # noqa: BLE001
                r["K"] = {"error": f"{type(e).__name__}: {e}", "traza": traceback.format_exc()[-1200:]}
        r["estado"] = "ok"
    except Exception as e:  # noqa: BLE001
        r["estado"] = f"error: {type(e).__name__}: {e}"
        r["traza"] = traceback.format_exc()[-1500:]
    finally:
        for q in (l1b, geo):
            try:
                q.unlink()
            except OSError:
                pass
    r["segundos"] = round(time.time() - t0, 1)
    return r


def prueba_sin_red():
    """(1) mirova_port.control_sin_red. (2) Grilla sintética de VIIRS 375 y de MODIS: un foco puesto en (X0, Y0)
    tiene que caer en la caja de cumbre y dar VRP > 0; sin foco, 0 píxeles. Comprueba proyección, orientación y
    centros de la grilla nueva."""
    MP.control_sin_red()
    from pyproj import Transformer
    X0, Y0, epsg = 604426.4 + 187.5 + 25000, 7439824.0 + 187.5 - 25000, 32719   # ~Láscar
    t = Transformer.from_crs(f"EPSG:{epsg}", "EPSG:4326", always_xy=True)
    lon0, lat0 = t.transform(X0, Y0)
    rng = np.random.default_rng(2)
    for b, paso, n, ul_dx, ul_dy in (("VIIRS375", 375.0, 134, 0.0, 0.0), ("MODIS", 1000.0, 51, -312.5, 437.5)):
        ux375, uy375 = X0 - 25187.5, Y0 + 25062.5
        g = {"ul_x": ux375 + ul_dx, "ul_y": uy375 + ul_dy, "n": n, "celda": paso, "X0": X0, "Y0": Y0}
        npts = int((90000 / (paso * 0.9)) ** 2)
        xs = X0 + rng.uniform(-45000, 45000, npts)
        ys = Y0 + rng.uniform(-45000, 45000, npts)
        lo, la = t.transform(xs, ys)
        cfg = MP.SENSORES[b]
        T = 265 + rng.normal(0, 0.4, npts)
        tir = ORA.temperatura_a_radiancia(T, cfg["lam_tir"])
        res = {}
        for foco in (False, True):
            mir = ORA.temperatura_a_radiancia(T - 3, cfg["lam_mir"])
            if foco:
                mir[np.hypot(xs - X0, ys - Y0) < 0.7 * paso] *= 3.0
            crop = {"lat": np.asarray(la), "lon": np.asarray(lo), "mir": mir, "tir": tir}
            gm, gt = grillar(crop, g, epsg)
            res[foco] = MP.correr(gm, gt, g, X0, Y0, 0, 100.0, cfg, semillas=0)
        print(b, "sin foco npix", res[False]["npix"], "| con foco npix", res[True]["npix"], "vrp", res[True]["vrp_mw"],
              "pixeles", res[True]["pixeles"][:3], flush=True)
        assert res[False]["npix"] == 0, f"{b}: control negativo sintético con alertas"
        assert res[True]["npix"] >= 1 and all(p[2] == 2 and p[3] <= 1.5 * paso / 1000 for p in res[True]["pixeles"]), \
            f"{b}: el foco no cae en la caja de cumbre"
    print("PRUEBA SIN RED OK", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--objetivos", default=str(AQUI / "objetivos_portes.json"))
    ap.add_argument("--out", default="out")
    ap.add_argument("--sensor", default="")
    ap.add_argument("--chunk", type=int, default=0)
    ap.add_argument("--nchunks", type=int, default=1)
    ap.add_argument("--solo", default="")
    ap.add_argument("--sin-red", action="store_true")
    a = ap.parse_args()
    prueba_sin_red()
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
    if a.sensor:
        objs = [o for o in objs if o["b"] == a.sensor]
    if a.solo:
        quiero = {int(x) for x in a.solo.split(",")}
        objs = [o for o in objs if o["id"] in quiero]
    mias = [o for n, o in enumerate(objs) if n % a.nchunks == a.chunk]
    print(f"{a.sensor or 'todos'} chunk {a.chunk}/{a.nchunks}: {len(mias)} pasadas", flush=True)
    resultados, faltan = [], 0
    for o in mias:
        print(f"== {o['id']} {o['volcan']} {o['hora_utc']} {o['granule']}", flush=True)
        try:
            r = procesar(o, destino, outdir)
        except Exception as e:  # noqa: BLE001
            r = {"id": o["id"], "volcan": o["volcan"], "hora_utc": o["hora_utc"], "b": o["b"],
                 "estado": f"error: {type(e).__name__}: {e}", "traza": traceback.format_exc()[-1500:]}
        if r.get("estado") != "ok":
            faltan += 1
        pf = (r.get("port") or {}).get("fisica") or {}
        kr = ((r.get("K") or {}).get("record") or {})
        print(f"   estado={r.get('estado')} {r.get('segundos')} s | port {pf.get('npix')} px {pf.get('vrp_mw')} | "
              f"K pc {(kr.get('primary_cluster') or {}).get('vrp_mw')} dc {kr.get('distance_class')}", flush=True)
        resultados.append(r)
        (outdir / f"resultados_{a.sensor or 'todos'}_{a.chunk:02d}.json").write_text(
            json.dumps(resultados, default=float), encoding="utf-8")
    print(f"pasadas sin procesar: {faltan} de {len(mias)}", flush=True)
    return 2 if faltan else 0


if __name__ == "__main__":
    sys.exit(main())
