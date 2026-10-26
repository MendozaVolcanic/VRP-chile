"""Prueba con gránulos chilenos (segunda ronda S158): el segundo oráculo de MIROVA sobre L1B reales de VIIRS 750.

Qué mide. Para cada pasada de objetivos.json baja el par L1B (VNP02MOD / VJ102MOD / VJ202MOD) y geolocalización
(VNP03MOD / VJ103MOD / VJ203MOD) del MISMO gránulo que usó nuestro record, remuestrea M13 y M15 a la grilla UTM de
MIROVA (67 x 67 celdas de 750 m con la esquina de la grilla de 375 m medida en sus TIF; HIPÓTESIS del §4.1 de
docs/DISENO_D17_REMUESTREO_UTM.md) y corre el oráculo. En el mismo gránulo corre también la función de producción
(pipeline.process_viirs_mod.calculate_vrp, sin store: no escribe nada) para tener tres números de una misma pasada:
MIROVA NRT, oráculo y producción.

Pregunta 1 del instrumento: si la cadena oráculo + grilla no fuera la de MIROVA, ¿se vería? Sí, en las alertas: el
oráculo daría otros Npix y otro VRP que la referencia NRT. Pregunta 2: si el instrumento estuviera muerto (gránulo
vacío, banda mal leída, grilla fuera del volcán), el oráculo daría escena inválida o 0 píxeles en las 12 alertas; el
informe distingue «no bajó», «escena inválida» y «0 píxeles». Control positivo: las alertas de Chillán (13 a 23 MW)
tienen que aparecer. Control negativo: dos pasadas RUTINA (Villarrica y Llaima).

Sólo lectura: no escribe en data/, no commitea. Autentica sólo por EARTHDATA_TOKEN (A71).
Uso: python probe_granulos.py --objetivos objetivos.json --out out [--sin-red]  (--sin-red corre la prueba sintética)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import traceback
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, str(AQUI.parent / "oraculo"))
import mirova_v750_r2 as ORA  # noqa: E402

N = 67
CELDA = 750.0
FLAG_MIN = 65528  # DN >= 65528 son banderas en el L1B de VIIRS (UserGuide Aug 2021, Tabla C.1)


def caja_mirova(n=N, lado_roi1=21, lado_roi2=7):
    """BOX por defecto: 0 fuera, ROI2 = cuadro central de 7 x 7 (cumbre, umbrales sensibles de noche), ROI1 = anillo
    de 21 x 21. Medido en la matriz de ejemplo: BOX==2 es el 7 x 7 central (filas y columnas 30 a 36) y BOX==1 es
    un bloque de 21 x 19 (filas 22 a 42, columnas 24 a 42). Aquí se usa 21 x 21 centrado: SUPUESTO declarado."""
    b = np.zeros((n, n))
    c = n // 2
    h1, h2 = lado_roi1 // 2, lado_roi2 // 2
    b[c - h1:c + h1 + 1, c - h1:c + h1 + 1] = 1
    b[c - h2:c + h2 + 1, c - h2:c + h2 + 1] = 2
    return b


def centros_celda(g):
    xs = g["ul_x"] + CELDA * (np.arange(N) + 0.5)
    ys = g["ul_y"] - CELDA * (np.arange(N) + 0.5)
    return np.meshgrid(xs, ys)  # fila 0 = norte


def remuestrear(x, y, v, X, Y, metodo):
    from scipy.interpolate import griddata
    ok = np.isfinite(v) & np.isfinite(x) & np.isfinite(y)
    return griddata(np.column_stack([x[ok], y[ok]]), v[ok], (X, Y), method=metodo)


def correr_oraculo(m13g, m15g, dayflag, sunglint):
    box = caja_mirova()
    salida = {}
    mask, lista, d = ORA.detectar(m13g, m15g, box, dayflag, sunglint, devolver_diag=True)
    r = ORA.vrp(m13g, mask)
    rr, cc = np.nonzero(mask)
    c = N // 2
    salida.update({
        "motivo_vacio": d.get("motivo"), "n_abs": d.get("n_abs"), "n_p1": d.get("n_p1"), "n_p2": d.get("n_p2"),
        "npix": r["npix"], "vrp_mw": None if r["npix"] == 0 else r["VRP_MW"],
        "L_hot": r["L_hot"], "L_bk": r["L_bk"],
        "pixeles": [[int(a), int(b), int(box[a, b]), round(float(np.hypot(a - c, b - c) * 0.75), 2)]
                    for a, b in zip(rr, cc)],
        "nan_m13": int(np.isnan(m13g).sum()), "nan_m15": int(np.isnan(m15g).sum()),
        "umbrales_p1": {k: d.get("pasada1", {}).get(k) for k in ("u_nti1", "u_nti2", "u_eti1", "u_eti2")},
    })
    # Sensibilidad a la triangulación del fondo (fillmissing2): 20 triangulaciones
    if r["npix"]:
        v = [ORA.vrp(m13g, mask, jitter=1e-6, semilla=s)["VRP_MW"] for s in range(20)]
        salida["vrp_rango_triangulacion"] = [float(min(v)), float(max(v))]
    return salida


def leer_l1b(ruta):
    import h5py
    out, attrs = {}, {}
    with h5py.File(ruta, "r") as f:
        obs = f["observation_data"]
        for b in ("M13", "M15"):
            ds = obs[b]
            dn = ds[:].astype(np.float64)
            sf = np.asarray(ds.attrs.get("scale_factor", 1.0)).ravel()[0]
            ao = np.asarray(ds.attrs.get("add_offset", 0.0)).ravel()[0]
            un = ds.attrs.get("units", b"")
            attrs[b] = {"scale_factor": float(sf), "add_offset": float(ao),
                        "units": un.decode() if isinstance(un, bytes) else str(un)}
            rad = dn * sf + ao
            rad[dn >= FLAG_MIN] = np.nan
            qf = obs[f"{b}_quality_flags"][:] if f"{b}_quality_flags" in obs else None
            attrs[b]["n_flag_dn"] = int((dn >= FLAG_MIN).sum())
            attrs[b]["n_saturado_qf"] = int(((qf & 0b100) != 0).sum()) if qf is not None else None
            out[b] = rad
    return out, attrs


def leer_geo(ruta):
    import h5py
    with h5py.File(ruta, "r") as f:
        g = f["geolocation_data"]
        lat = g["latitude"][:].astype(np.float64)
        lon = g["longitude"][:].astype(np.float64)
        lat[lat < -90] = np.nan
        lon[lon < -180] = np.nan
        ang = {}
        for k in ("sensor_zenith", "sensor_azimuth", "solar_zenith", "solar_azimuth"):
            if k in g:
                ds = g[k]
                sf = np.asarray(ds.attrs.get("scale_factor", 1.0)).ravel()[0]
                a = ds[:].astype(np.float64) * sf
                a[np.isnan(lat)] = np.nan
                ang[k] = a
    return lat, lon, ang


def recortar_y_grillar(lat, lon, m13, m15, ang, g, radio_km=45.0):
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
    X, Y = centros_celda(g)
    i0 = np.unravel_index(np.nanargmin(np.where(sel, dist, np.inf)), dist.shape)
    geom = {k: float(v[i0]) for k, v in ang.items()}
    crop = {"lat": lat[sel], "lon": lon[sel], "x": x, "y": y, "m13": m13[sel], "m15": m15[sel],
            "dist_km": dist[sel]}
    grillas = {m: (remuestrear(x, y, m13[sel], X, Y, m), remuestrear(x, y, m15[sel], X, Y, m))
               for m in ("linear", "nearest")}
    return crop, grillas, geom


def produccion(volcan_nombre, l1b, geo):
    from run_pipeline import load_volcanoes
    from pipeline.geo_utils import get_detection_anchor
    from pipeline import process_viirs_mod
    v = load_volcanoes(volcan_nombre)
    if not v:
        return {"error": f"volcan {volcan_nombre} no esta en volcanoes.yaml activo"}
    v = v[0]
    vl, vo = get_detection_anchor(v)
    r = process_viirs_mod.calculate_vrp(
        l1b, geo, v["lat"], v["lon"], v["radius_km"], vent_lat=vl, vent_lon=vo,
        vent_radius_km=v.get("vent_radius_km", 4.0), inner_radius_km=v.get("inner_radius_km"),
        exclude_zones=v.get("exclude_zones"), active_water_bodies=v.get("active_water_bodies"),
        lbg_global_compatible=v.get("lbg_global_compatible", False),
        local_kernel_bg_compatible=v.get("local_kernel_bg", False))
    if not r:
        return {"resultado": None}
    pc = r.get("primary_cluster") or {}
    return {"vrp_mw": r.get("vrp_mw"), "pc_vrp_mw": pc.get("vrp_mw"), "n_px": r.get("n_anomalous_pixels"),
            "pc_n": pc.get("n_pixels"), "clase": r.get("distance_class"), "t_bg_k": r.get("t_bg_k"),
            "L_bg": r.get("diag_L_bg_w_m2_sr_um"), "sensor_zenith_deg": r.get("sensor_zenith_deg"),
            "final_hotspot_dist_km": r.get("final_hotspot_dist_km")}


LATLON = [0.0, 0.0]  # centro del volcán de la pasada en curso (lo fija procesar)


def bajar(nombre_granulo, destino):
    """Busca en CMR por nombre exacto del gránulo (L1B y GEO) y baja los dos archivos."""
    import earthaccess
    m = re.match(r"(V\w\w0)2MOD(_NRT)?\.(A\d{7}\.\d{4})\.(\d{3})", nombre_granulo)
    pref, nrt, tag, col = m.group(1), m.group(2) or "", m.group(3), m.group(4)
    ver = {"021": "2.1", "002": "2", "001": "1"}.get(col, "2")
    res = {}
    for tipo in ("2", "3"):
        sn = f"{pref}{tipo}MOD"
        hallados = []
        for s in (sn + nrt, sn, sn + "_NRT"):
            try:
                hallados = earthaccess.search_data(short_name=s, version=ver, granule_name=f"{s}.{tag}.{col}*", count=5)
            except Exception as e:  # noqa: BLE001
                print(f"   busqueda {s} fallo: {type(e).__name__}: {str(e)[:120]}", flush=True)
                hallados = []
            if hallados:
                break
        if not hallados:
            # Respaldo (run 2): búsqueda por día y caja con la función de producción, filtrada por la hora del gránulo.
            from datetime import datetime
            from pipeline import fetch as F
            plat = {"VNP0": "SNPP", "VJ10": "NOAA20", "VJ20": "NOAA21"}[pref]
            clave = f"VIIRS_{plat}_MOD_{'L1B' if tipo == '2' else 'GEO'}"
            dia = datetime.strptime(tag[1:8], "%Y%j")
            try:
                cand = F.search_granules(clave, LATLON[0], LATLON[1], 30, dia)
            except Exception as e:  # noqa: BLE001
                print(f"   respaldo {clave} fallo: {type(e).__name__}: {str(e)[:120]}", flush=True)
                cand = []
            hallados = [g for g in cand if tag in str(g["umm"].get("GranuleUR", ""))]
            print(f"   respaldo {clave} {dia:%Y-%m-%d}: {len(cand)} candidatos, {len(hallados)} con {tag}", flush=True)
        if not hallados:
            return None, f"sin_granulo_{sn}"
        from pipeline.fetch import download_granules
        p = download_granules(hallados[:1], destino)
        res[tipo] = [q for q in p if q.suffix in (".nc", ".h5")][0]
    return (res["2"], res["3"]), None


def procesar(obj, destino, outdir):
    r = {"volcan": obj["volcan"], "hora_utc": obj["hora_utc"], "motivo": obj["motivo"], "mirova": obj["mirova"],
         "nuestro_record": obj["nuestros"]}
    if not obj["nuestros"]:
        r["estado"] = "sin_record_nuestro"
        return r
    gran = obj["nuestros"][0]["granule"]
    LATLON[0], LATLON[1] = obj["grilla"]["centro_lat"], obj["grilla"]["centro_lon"]
    r["granulo"] = gran
    t0 = time.time()
    par, err = bajar(gran, destino)
    if err:
        r["estado"] = err
        return r
    l1b, geo = par
    r["archivos"] = [l1b.name, geo.name]
    rad, attrs = leer_l1b(l1b)
    lat, lon, ang = leer_geo(geo)
    r["atributos_l1b"] = attrs
    rec = recortar_y_grillar(lat, lon, rad["M13"], rad["M15"], ang, obj["grilla"])
    if rec is None:
        r["estado"] = "volcan_fuera_del_granulo"
        return r
    crop, grillas, geom = rec
    r["geometria_centro"] = geom
    dayflag = 0 if geom.get("solar_zenith", 180) > 90 else 1
    sg = ORA.sunglint_deg(geom.get("sensor_zenith", 0), geom.get("solar_zenith", 0),
                          geom.get("sensor_azimuth", 0), geom.get("solar_azimuth", 0))
    r["dayflag"], r["sunglint"] = dayflag, sg
    r["oraculo"] = {m: correr_oraculo(g13, g15, dayflag, sg) for m, (g13, g15) in grillas.items()}
    try:
        r["produccion"] = produccion(obj["volcan"], l1b, geo)
    except Exception as e:  # noqa: BLE001
        r["produccion"] = {"error": f"{type(e).__name__}: {e}", "traza": traceback.format_exc()[-800:]}
    clave = f"{obj['volcan']}_{obj['hora_utc'].replace(' ', '_').replace(':', '')}"
    np.savez_compressed(outdir / f"recorte_{clave}.npz", **crop,
                        **{f"grilla_{m}_M13": g[0] for m, g in grillas.items()},
                        **{f"grilla_{m}_M15": g[1] for m, g in grillas.items()})
    for q in (l1b, geo):
        try:
            q.unlink()
        except OSError:
            pass
    r["estado"] = "ok"
    r["segundos"] = round(time.time() - t0, 1)
    return r


def prueba_sintetica():
    """Sin red: una escena sintética con un foco en el centro de la grilla de Láscar tiene que dar alertas en la
    celda central y un VRP positivo; sin foco, 0 píxeles. Comprueba proyección, orientación de la grilla y oráculo."""
    g = {"epsg": 32719, "ul_x": 604613.9, "ul_y": 7440011.2, "centro_lat": -23.37058, "centro_lon": -67.73061}
    rng = np.random.default_rng(1)
    lat = g["centro_lat"] + rng.uniform(-0.45, 0.45, (400, 400))
    lon = g["centro_lon"] + rng.uniform(-0.5, 0.5, (400, 400))
    T = 265 + rng.normal(0, 0.4, lat.shape)
    m15 = ORA.temperatura_a_radiancia(T, ORA.LAMBDA_M15)
    m13 = ORA.temperatura_a_radiancia(T - 3, ORA.LAMBDA_M13)
    ang = {"sensor_zenith": np.full(lat.shape, 20.0), "solar_zenith": np.full(lat.shape, 120.0),
           "sensor_azimuth": np.zeros(lat.shape), "solar_azimuth": np.zeros(lat.shape)}
    res = {}
    for con_foco in (False, True):
        a = m13.copy()
        if con_foco:
            d = np.hypot((lat - g["centro_lat"]) * 111, (lon - g["centro_lon"]) * 102)
            a[d < 0.4] *= 3.0
        crop, grillas, geom = recortar_y_grillar(lat, lon, a, m15, ang, g)
        res[con_foco] = correr_oraculo(*grillas["linear"], 0, 100.0)
        print("foco" if con_foco else "sin foco", "npix", res[con_foco]["npix"], "pixeles", res[con_foco]["pixeles"][:5],
              "vrp", res[con_foco]["vrp_mw"], flush=True)
    assert res[False]["npix"] == 0, "control negativo sintético con alertas"
    assert res[True]["npix"] >= 1 and all(p[3] <= 1.5 for p in res[True]["pixeles"]), "el foco no cae en el centro"
    print("PRUEBA SINTETICA OK", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--objetivos", default=str(AQUI / "objetivos.json"))
    ap.add_argument("--out", default="out")
    ap.add_argument("--sin-red", action="store_true")
    ap.add_argument("--solo", default="", help="lista de volcan|hora separadas por coma")
    a = ap.parse_args()
    prueba_sintetica()
    if a.sin_red:
        return 0
    if not os.environ.get("EARTHDATA_TOKEN", "").strip():
        print("EARTHDATA_TOKEN vacio: no se corre (A71)")
        return 1
    from pipeline.fetch import auth
    auth()
    outdir = Path(a.out); outdir.mkdir(parents=True, exist_ok=True)
    destino = Path(os.environ.get("VRP_TMP_DIR", "/tmp/vrp_tmp")) / "granulos"
    objs = json.loads(Path(a.objetivos).read_text(encoding="utf-8"))
    if a.solo:
        quiero = set(a.solo.split(","))
        objs = [o for o in objs if f"{o['volcan']}|{o['hora_utc']}" in quiero]
    resultados, faltan = [], 0
    for o in objs:
        print(f"== {o['volcan']} {o['hora_utc']} ({o['motivo']})", flush=True)
        try:
            r = procesar(o, destino, outdir)
        except Exception as e:  # noqa: BLE001
            r = {"volcan": o["volcan"], "hora_utc": o["hora_utc"], "estado": f"error: {type(e).__name__}: {e}",
                 "traza": traceback.format_exc()[-1500:]}
        if r.get("estado") != "ok":
            faltan += 1
        ol = (r.get("oraculo") or {}).get("linear", {})
        print(f"   estado={r.get('estado')} oraculo npix={ol.get('npix')} vrp={ol.get('vrp_mw')} "
              f"produccion={r.get('produccion')} mirova={[m.get('VRP_MW') for m in o['mirova']]}", flush=True)
        resultados.append(r)
        (outdir / "resultados.json").write_text(json.dumps(resultados, indent=1, default=float), encoding="utf-8")
    print(f"pasadas sin procesar: {faltan} de {len(objs)}", flush=True)
    return 2 if faltan else 0


if __name__ == "__main__":
    sys.exit(main())
