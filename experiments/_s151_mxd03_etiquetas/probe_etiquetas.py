# Probe S151, tarea 1.17: re-etiqueta detecciones MODIS con la geolocalizacion oficial MxD03.
# Solo lectura: no escribe en data/, no commitea, borra cada HDF al terminar de usarlo.
#
# POR QUE. El probe de #828 (experiments/_s151_probe_mod03/) midio en 7 granulos, casi todos de
# Lascar, que `_interp_geo` (pipeline/process_modis.py:342) deja el pixel corrido de 1 a 3 km respecto
# de MxD03. De esa posicion cuelgan la etiqueta summit/far y la publicacion en el tablero. Este probe
# corre, para cada granulo de la muestra (poblacion.json), el pipeline de produccion DOS veces sobre
# el mismo L1B:
#   brazo C: tal cual (lat/lon de `_interp_geo`), que es lo que produccion hace hoy;
#   brazo M: identico, salvo que lat/lon salen de MxD03 (lo unico que cambia es la posicion).
# Las dos salidas pasan por `store.append_record` (en un directorio temporal) y por el predicado del
# tablero ejecutado con node desde frontend/index.html (A97), igual que en scripts/banco_paridad.py.
# Lo que cambie entre C y M es el efecto del arreglo MxD03 sobre lo que el operador ve.
#
# Los angulos (cenit, acimut) siguen saliendo de `_interp_geo` en los dos brazos: el cenit solo se
# persiste para estudio (A_pix es nadir fijo, A66) y asi el brazo M aisla la posicion.
#
# Uso (Linux con pyhdf): EARTHDATA_TOKEN=... VRP_PROFILE=mirova_equivalent \
#     python probe_etiquetas.py --volcan Lascar --out out [--presupuesto-min 70]
import argparse
import json
import math
import os
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import numpy as np

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")

from pipeline import process_modis as pm  # noqa: E402
from pipeline import store  # noqa: E402
from pipeline.geo_utils import get_detection_anchor  # noqa: E402

RELLENO_MXD03 = -999.0


# ------------------------------------------------------------------ argumentos de produccion
def argumentos_calculate_vrp(volcan):
    """Los keyword de `process_modis.calculate_vrp` tal como los arma scripts/run_pipeline.py
    (process_date, rama MODIS). El test compara los nombres contra el AST de run_pipeline."""
    vlat, vlon = get_detection_anchor(volcan)
    return {
        "vent_lat": vlat,
        "vent_lon": vlon,
        "vent_radius_km": volcan.get("vent_radius_km", 4.0),
        "inner_radius_km": volcan.get("inner_radius_km"),
        "exclude_zones": volcan.get("exclude_zones"),
        "active_water_bodies": volcan.get("active_water_bodies"),
        "lbg_global_compatible": volcan.get("lbg_global_compatible", False),
        "local_kernel_bg_compatible": volcan.get("local_kernel_bg", False),
    }


def argumentos_append_record(volcan, overwrite, volcanic_features=None):
    from pipeline import profile as vrp_profile
    return {
        "volcano_lat": volcan["lat"], "volcano_lon": volcan["lon"],
        "overwrite": overwrite,
        "max_hotspot_dist_km": volcan.get("radius_km"),
        "enable_pixel_level_distance_filter": vrp_profile.ENABLE_PIXEL_LEVEL_DISTANCE_FILTER,
        "max_cluster_pixels": volcan.get("max_cluster_pixels"),
        "inner_radius_km": volcan.get("inner_radius_km"),
        "volcanic_features": volcanic_features,
    }


# ------------------------------------------------------------------ un brazo
def procesar_brazo(l1b, geo, volcan, latlon=None, volcanic_features=None, lector=None):
    """Corre calculate_vrp + store.append_record como produccion y devuelve el record guardado.

    `latlon=(lat, lon)` reemplaza la geolocalizacion que entrega read_modis_l1b (brazo M); None
    deja la de `_interp_geo` (brazo C). El store escribe en un directorio temporal, nunca en data/.
    `lector` permite leer el HDF una sola vez por granulo (por defecto, read_modis_l1b de produccion).
    """
    lector = lector or pm.read_modis_l1b

    def leer(path):
        d = lector(path)
        if latlon is not None:
            lat, lon = latlon
            if lat.shape != d["lat"].shape:
                raise ValueError("MxD03 %s y L1B %s no calzan" % (lat.shape, d["lat"].shape))
            d = dict(d)
            d["lat"], d["lon"] = lat.astype(np.float32), lon.astype(np.float32)
        return d

    with patch.object(pm, "read_modis_l1b", leer):
        res = pm.calculate_vrp(l1b, geo, volcan["lat"], volcan["lon"], volcan["radius_km"],
                               **argumentos_calculate_vrp(volcan))
    if not res:
        return None
    with tempfile.TemporaryDirectory() as tmp, patch.object(store, "DATA_DIR", Path(tmp)):
        store.append_record(volcan["name"], res,
                            **argumentos_append_record(volcan, True, volcanic_features))
        recs = store.get_records(volcan["name"])
    return recs[-1] if recs else None


# ------------------------------------------------------------------ medidas
def limpiar_relleno(a):
    a = np.asarray(a, dtype=np.float32).copy()
    a[a <= RELLENO_MXD03 + 0.5] = np.nan
    return a


def _ne_km(lat0, lon0, lat, lon):
    return (lat - lat0) * 111.32, (lon - lon0) * 111.32 * math.cos(math.radians((lat + lat0) / 2))


def desplazamiento_crater(lat_i, lon_i, lat_m, lon_m, vent):
    """`_interp_geo` menos MxD03 en el pixel cuya posicion MxD03 cae mas cerca del crater."""
    d = np.hypot((lat_m - vent[0]) * 111.32, (lon_m - vent[1]) * 111.32 * math.cos(math.radians(vent[0])))
    i, j = np.unravel_index(np.nanargmin(d), d.shape)
    dn, de = _ne_km(float(lat_m[i, j]), float(lon_m[i, j]), float(lat_i[i, j]), float(lon_i[i, j]))
    return {"linea": int(i), "frame": int(j), "dn_km": round(dn, 3), "de_km": round(de, 3),
            "km": round(math.hypot(dn, de), 3)}


def resumir(rec):
    if rec is None:
        return None
    pc = rec.get("primary_cluster") or {}
    return {"dc": rec.get("distance_class"), "fuente": rec.get("final_hotspot_source"),
            "final_lat": rec.get("final_hotspot_lat"), "final_lon": rec.get("final_hotspot_lon"),
            "final_dist": rec.get("final_hotspot_dist_km"),
            "pc_lat": pc.get("centroid_lat"), "pc_lon": pc.get("centroid_lon"),
            "pc_dist": pc.get("centroid_dist_km"), "pc_vrp": pc.get("vrp_mw"),
            "n_anom": rec.get("n_anomalous_pixels"), "vrp_mw": rec.get("vrp_mw"),
            "sensor": rec.get("sensor"), "cenit": rec.get("sensor_zenith_deg"),
            "datetime_utc": rec.get("datetime_utc")}


def comparar(c, m, pub_c, pub_m):
    """Que cambio del brazo C al M: etiqueta, publicacion y si la deteccion misma cambio."""
    dc_c = None if c is None else c.get("dc")
    dc_m = None if m is None else m.get("dc")
    det = (c is None) != (m is None) or (c is not None and (
        c.get("n_anom") != m.get("n_anom") or abs((c.get("pc_vrp") or 0) - (m.get("pc_vrp") or 0)) > 1e-9))
    return {"etiqueta": "igual" if dc_c == dc_m else "%s->%s" % (dc_c, dc_m),
            "pub": "igual" if pub_c == pub_m else "%d->%d" % (pub_c, pub_m),
            "deteccion_cambia": bool(det)}


def publica(records, inner):
    """Predicado del tablero (`isSummitDetection && isValidDetection && !isThermalArtifact &&
    mirovaEqVrpDisplay > 0`) ejecutado con node desde frontend/index.html, via banco_paridad."""
    import banco_paridad as bp
    casos, idx = [], []
    for i, r in enumerate(records):
        if r is None:
            continue
        slim = {k: r.get(k) for k in bp.CAMPOS_JS if k != "anomaly_pixels"}
        slim["anomaly_pixels"] = [{k: p.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")}
                                  for p in (r.get("anomaly_pixels") or [])]
        casos.append([slim, inner])
        idx.append(i)
    out = [0] * len(records)
    for i, p in zip(idx, bp.correr_node(casos) if casos else []):
        out[i] = int(p[4])
    return out


def _copia(d):
    return {k: (v.copy() if isinstance(v, np.ndarray) else v) for k, v in d.items()}


def medir_granulo(l1b, geo, volcan, latlon_m, volcanic_features=None, datos=None):
    """Los dos brazos sobre el mismo L1B, sin el predicado (se corre en lote al final).
    `datos`: lo que ya devolvio read_modis_l1b para este granulo; cada brazo recibe una copia."""
    lector = None if datos is None else (lambda _p: _copia(datos))
    rc = procesar_brazo(l1b, geo, volcan, None, volcanic_features, lector)
    rm = procesar_brazo(l1b, geo, volcan, latlon_m, volcanic_features, lector)
    return rc, rm


# ------------------------------------------------------------------ E/S (solo en el runner)
def _bajar(short, patron, dest):
    import earthaccess
    from pipeline.fetch import download_granules
    dest.mkdir(parents=True, exist_ok=True)
    res = earthaccess.search_data(short_name=short, version="6.1", granule_name=f"{short}.{patron}*")
    if not res:
        return None
    paths = download_granules(res[:1], dest)
    return paths[0] if paths else None


def _leer_mxd03(path):
    from pyhdf.SD import SD, SDC
    sd = SD(str(path), SDC.READ)
    try:
        return (limpiar_relleno(sd.select("Latitude").get()), limpiar_relleno(sd.select("Longitude").get()))
    finally:
        sd.end()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--volcan", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--poblacion", default=str(AQUI / "poblacion.json"))
    ap.add_argument("--presupuesto-min", type=float, default=70.0)
    args = ap.parse_args()
    if not os.environ.get("EARTHDATA_TOKEN", "").strip():
        sys.exit("EARTHDATA_TOKEN vacio: el probe no usa usuario y clave (A71).")
    import run_pipeline as rp     # el mismo dict de volcan que produccion (overrides del perfil incluidos)
    from pipeline.fetch import auth
    auth()
    t0 = time.time()
    pob = json.load(open(args.poblacion, encoding="utf-8"))["volcanes"][args.volcan]
    volcan = rp.load_volcanoes(args.volcan)[0]
    vent = get_detection_anchor(volcan)
    feats = rp.VOLCANIC_FEATURES.get(volcan["name"])
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    hdf = out / "hdf"
    filas, records_c, records_m = [], [], []
    for g in pob["muestra"]:
        fila = dict(g)
        filas.append(fila)
        records_c.append(None)
        records_m.append(None)
        if (time.time() - t0) / 60.0 > args.presupuesto_min:
            fila["estado"] = "sin_tiempo"
            continue
        prod, patron = g["clave"].split(".", 1)
        l1b = geo = None
        try:
            l1b = _bajar(prod, patron, hdf)
            geo = _bajar(prod.replace("021KM", "03"), patron, hdf)
            if l1b is None or geo is None:
                fila["estado"] = "error"
                fila["error"] = "no encontrado o no bajado (%s)" % ("L1B" if l1b is None else "MxD03")
                continue
            lat_m, lon_m = _leer_mxd03(geo)
            d = pm.read_modis_l1b(l1b)
            fila["desplazamiento"] = desplazamiento_crater(d["lat"], d["lon"], lat_m, lon_m, vent)
            fila["mxd03_relleno_cerca"] = bool(np.isnan(lat_m[
                max(fila["desplazamiento"]["linea"] - 30, 0):fila["desplazamiento"]["linea"] + 31,
                max(fila["desplazamiento"]["frame"] - 30, 0):fila["desplazamiento"]["frame"] + 31]).any())
            rc, rm = medir_granulo(l1b, geo, volcan, (lat_m, lon_m), feats, datos=d)
            records_c[-1], records_m[-1] = rc, rm
            fila["c"], fila["m"] = resumir(rc), resumir(rm)
            fila["estado"] = "ok"
        except Exception as e:  # un granulo roto no tumba el volcan; queda contado como error
            fila["estado"] = "error"
            fila["error"] = "%s: %s" % (type(e).__name__, e)
        finally:
            for p in (l1b, geo):
                if p is not None:
                    Path(p).unlink(missing_ok=True)
        print(json.dumps({k: fila.get(k) for k in ("clave", "estrato", "estado", "desplazamiento")},
                         ensure_ascii=False), flush=True)
    inner = pob["inner_radius_km"]
    pub_c, pub_m = publica(records_c, inner), publica(records_m, inner)
    for fila, pc_, pm_ in zip(filas, pub_c, pub_m):
        if fila.get("estado") != "ok":
            continue
        fila["pub_c"], fila["pub_m"] = pc_, pm_
        fila["comparacion"] = comparar(fila["c"], fila["m"], pc_, pm_)
        fila["c_igual_a_guardada"] = (fila["c"] or {}).get("dc") == fila.get("dc_guardada") and pc_ == fila.get("pub_guardada")
    res = {"volcan": args.volcan, "inner_radius_km": inner, "N": pob["N"], "n_pub_tramo": pob["n_pub_tramo"],
           "minutos": round((time.time() - t0) / 60.0, 1), "granulos": filas}
    with open(out / f"{args.volcan}.json", "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1, ensure_ascii=False)
    n_ok = sum(1 for f in filas if f.get("estado") == "ok")
    print("%s: %d de %d granulos medidos en %.1f min" % (args.volcan, n_ok, len(filas), res["minutos"]))


if __name__ == "__main__":
    main()
