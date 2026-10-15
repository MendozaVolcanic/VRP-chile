# Probe S151 (tarea 1.15): geolocalizacion MODIS de `_interp_geo` contra MxD03, pixel a pixel, en Lascar.
# Solo lectura: no escribe en data/, no commitea, borra cada HDF al terminar de usarlo.
#
# POR QUE. El estudio del PR #826 encontro que el pixel MODIS del crater sale corrido hacia el sensor y lo
# atribuyo a `_interp_geo` (pipeline/process_modis.py:342), que estira la grilla de 5 km de MxD021KM con un
# zoom de extremos alineados cuando el primer punto grueso es el frame 2 (MODIS L1B Data Dictionary C7,
# p. 66). Esa atribucion descansa en un brazo de A/B y casi un solo volcan. MxD03 trae la posicion de cada
# pixel de 1 km, corregida por terreno: comparar las dos geolocalizaciones en el mismo granulo decide sin
# depender de ningun foco termico. El criterio esta en README.md y se fijo antes de correr.
#
# Uso (en Linux, con pyhdf): EARTHDATA_TOKEN=... VRP_PROFILE=mirova_equivalent python probe_mod03.py --out out
# Sale con codigo 2 si falta algun granulo.
import argparse
import json
import math
import os
import sys
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(RAIZ))

VENT = (-23.36293, -67.731416)        # vent_lat/vent_lon de Lascar en volcanoes.yaml
GRANULOS = [  # (L1B, GEO, AAAADDD.HHMM, rotulo) elegidos del brazo K y de produccion, ver README
    ("MYD021KM", "MYD03", "A2026073.0705", "Aqua, lado frame 0, cenit 44,6 (pasada del veto)"),
    ("MYD021KM", "MYD03", "A2026086.0710", "Aqua, lado frame 0, cenit 39,9 (pasada del veto)"),
    ("MYD021KM", "MYD03", "A2026074.0745", "Aqua, otro lado, cenit 30,5"),
    ("MYD021KM", "MYD03", "A2026113.0800", "Aqua, otro lado, cenit 43,2"),
    ("MOD021KM", "MOD03", "A2026078.0155", "Terra, lado frame 0, cenit 31,2"),
    ("MOD021KM", "MOD03", "A2026075.0135", "Terra, otro lado, cenit 10,4"),
    ("MOD021KM", "MOD03", "A2026077.0115", "Terra, otro lado, cenit 46,8"),
]
TOL_KM = 0.3          # criterio: coincidencia con la regla, y umbral de "no corre nada"
MIN_KM = 1.0          # criterio: corrimiento minimo hacia el sensor, lado del frame 0 con cenit >= 30
VENTANA_KM = 15.0


def ne_km(lat0, lon0, lat, lon):
    return ((lat - lat0) * 111.32, (lon - lon0) * 111.32 * math.cos(math.radians((lat + lat0) / 2)))


def _unit(v):
    n = math.hypot(*v)
    return (v[0] / n, v[1] / n) if n > 0 else (0.0, 0.0)


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1]


def _interp_fila(arr, i, t):
    j0 = int(math.floor(t))
    j1 = min(j0 + 1, arr.shape[1] - 1)
    f = t - j0
    return arr[i, j0] * (1 - f) + arr[i, j1] * f


def _interp_col(arr, t, j):
    i0 = int(math.floor(t))
    i1 = min(i0 + 1, arr.shape[0] - 1)
    f = t - i0
    return arr[i0, j] * (1 - f) + arr[i1, j] * f


def offsets_de_la_grilla(glat, glon, latc, lonc):
    """Distancia mediana (km) entre los puntos gruesos de L1B y MxD03 en (o_linea + 5a, o_frame + 5b), para
    o de 0 a 4 en cada eje con el otro fijo en 2. El offset verdadero da ~0."""
    out = {"frame": {}, "linea": {}}
    for eje in ("frame", "linea"):
        for o in range(5):
            orow, ocol = (2, o) if eje == "frame" else (o, 2)
            g1 = glat[orow::5, ocol::5]
            g2 = glon[orow::5, ocol::5]
            n0 = min(g1.shape[0], latc.shape[0])
            n1 = min(g1.shape[1], latc.shape[1])
            dn = (latc[:n0, :n1] - g1[:n0, :n1]) * 111.32
            de = (lonc[:n0, :n1] - g2[:n0, :n1]) * 111.32 * np.cos(np.radians(latc[:n0, :n1]))
            out[eje][o] = round(float(np.nanmedian(np.hypot(dn, de))), 4)
    return out


def _en_pixel(glat, glon, ilat, ilon, saz, i, j, n_geo_f, n_geo_l):
    nl, ns = glat.shape
    p0 = (float(glat[i, j]), float(glon[i, j]))
    d = ne_km(p0[0], p0[1], float(ilat[i, j]), float(ilon[i, j]))          # interp menos MxD03
    jm, jp = max(j - 1, 0), min(j + 1, ns - 1)
    im, ip = max(i - 1, 0), min(i + 1, nl - 1)
    e_scan = _unit(ne_km(glat[i, jm], glon[i, jm], glat[i, jp], glon[i, jp]))
    e_track = _unit(ne_km(glat[im, j], glon[im, j], glat[ip, j], glon[ip, j]))
    t = 2.0 + 5.0 * j * (n_geo_f - 1) / (ns - 1)                             # regla del zoom, eje del barrido
    pv = ne_km(p0[0], p0[1], float(_interp_fila(glat, i, t)), float(_interp_fila(glon, i, t)))
    tl = 2.0 + 5.0 * i * (n_geo_l - 1) / (nl - 1)                            # idem a lo largo de la traza
    pt = ne_km(p0[0], p0[1], float(_interp_col(glat, tl, j)), float(_interp_col(glon, tl, j)))
    az = math.radians(float(saz[i, j]))
    hacia = (math.cos(az), math.sin(az))
    signo = 1.0 if _dot(e_scan, hacia) >= 0 else -1.0                        # +s apunta hacia el sensor?
    return {
        "obs_barrido_km": _dot(d, e_scan), "pred_barrido_km": _dot(pv, e_scan),
        "obs_traza_km": _dot(d, e_track), "pred_traza_km": _dot(pt, e_track),
        "obs_hacia_sensor_km": _dot(d, e_scan) * signo, "pred_hacia_sensor_km": _dot(pv, e_scan) * signo,
        "e_scan": e_scan, "e_track": e_track,
    }


def comparar(glat, glon, latc, lonc, saz, szen, interp, rad=None, vent=VENT):
    """Nucleo sin E/S, para poder probarlo con datos sinteticos (probar_probe.py)."""
    nl, ns = glat.shape
    ilat = interp(latc, nl, ns).astype(np.float64)
    ilon = interp(lonc, nl, ns).astype(np.float64)
    dist = np.hypot((glat - vent[0]) * 111.32, (glon - vent[1]) * 111.32 * math.cos(math.radians(vent[0])))
    i, j = np.unravel_index(np.nanargmin(dist), dist.shape)
    px = _en_pixel(glat, glon, ilat, ilon, saz, i, j, latc.shape[1], latc.shape[0])
    # lado: las lineas crecen en el sentido de vuelo; la derecha es el rumbo girado 90 grados horario
    h = px["e_track"]
    derecha = (-h[1], h[0])
    frame0_a_la_derecha = _dot((-px["e_scan"][0], -px["e_scan"][1]), derecha) > 0
    lado_frame0 = j < (ns - 1) / 2.0
    # ventana: residuo observado menos predicho a lo largo del barrido
    res = []
    ii, jj = np.where(dist <= VENTANA_KM)
    for a, b in zip(ii[::3], jj[::3]):
        if 1 <= b < ns - 1 and 1 <= a < nl - 1:
            q = _en_pixel(glat, glon, ilat, ilon, saz, a, b, latc.shape[1], latc.shape[0])
            res.append(q["obs_barrido_km"] - q["pred_barrido_km"])
    out = {
        "linea": int(i), "frame": int(j), "cenit": float(szen[i, j]), "acimut_sensor": float(saz[i, j]),
        "volcan_del_lado_del_frame0": bool(lado_frame0), "frame0_a_la_derecha_de_la_traza": bool(frame0_a_la_derecha),
        "obs_barrido_km": round(px["obs_barrido_km"], 3), "pred_barrido_km": round(px["pred_barrido_km"], 3),
        "obs_hacia_sensor_km": round(px["obs_hacia_sensor_km"], 3), "pred_hacia_sensor_km": round(px["pred_hacia_sensor_km"], 3),
        "obs_traza_km": round(px["obs_traza_km"], 3), "pred_traza_km_offset2": round(px["pred_traza_km"], 3),
        "ventana_residuo_barrido_mediana_abs_km": round(float(np.median(np.abs(res))), 3) if res else None,
        "ventana_n": len(res),
        "offsets_grilla_km": offsets_de_la_grilla(glat, glon, latc, lonc),
    }
    if rad is not None:
        m = np.where(dist <= 8.0, rad, np.nan)
        if np.any(np.isfinite(m)):
            k = np.unravel_index(np.nanargmax(m), m.shape)
            out["pixel_brillante_b22_mxd03_dn_de_km"] = [round(x, 3) for x in ne_km(vent[0], vent[1], float(glat[k]), float(glon[k]))]
            out["pixel_brillante_b22_interp_dn_de_km"] = [round(x, 3) for x in ne_km(vent[0], vent[1], float(ilat[k]), float(ilon[k]))]
    return out


def veredicto(filas):
    """Criterio fijado en README.md antes de correr."""
    if any("error" in f for f in filas):
        return "INCOMPLETO"
    coincide = all(abs(f["obs_barrido_km"] - f["pred_barrido_km"]) <= TOL_KM for f in filas)
    grandes = [f for f in filas if f["volcan_del_lado_del_frame0"] and f["cenit"] >= 30]
    hacia = bool(grandes) and all(f["obs_hacia_sensor_km"] >= MIN_KM for f in grandes)
    nada = all(math.hypot(f["obs_barrido_km"], f["obs_traza_km"]) < TOL_KM for f in filas)
    contra = any(abs(f["pred_barrido_km"]) > 1.0 and f["obs_barrido_km"] * f["pred_barrido_km"] < 0 for f in filas)
    if nada or contra:
        return "REFUTA"
    if coincide and hacia:
        return "CONFIRMA"
    return "PARCIAL"


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


def _leer_geo(path):
    from pyhdf.SD import SD, SDC
    sd = SD(str(path), SDC.READ)
    try:
        lat = sd.select("Latitude").get().astype(np.float64)
        lon = sd.select("Longitude").get().astype(np.float64)
        out = [lat, lon]
        for nombre in ("SensorAzimuth", "SensorZenith"):
            s = sd.select(nombre)
            out.append(s.get().astype(np.float64) * float(s.attributes().get("scale_factor", 0.01)))
        return out
    finally:
        sd.end()


def _leer_l1b(path):
    from pyhdf.SD import SD, SDC
    sd = SD(str(path), SDC.READ)
    try:
        latc = sd.select("Latitude").get().astype(np.float32)
        lonc = sd.select("Longitude").get().astype(np.float32)
        ev = sd.select("EV_1KM_Emissive")
        data = ev.get()
        at = ev.attributes()
        i22 = 2                     # EV_1KM_Emissive: bandas 20, 21, 22, ... (BAND22_IDX = 2 en process_modis)
        rad = (data[i22].astype(np.float64) - at["radiance_offsets"][i22]) * at["radiance_scales"][i22]
        rad[data[i22] > 32767] = np.nan
        return latc, lonc, rad
    finally:
        sd.end()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    if not os.environ.get("EARTHDATA_TOKEN", "").strip():
        sys.exit("EARTHDATA_TOKEN vacio: el probe no usa usuario y clave (A71).")
    from pipeline.fetch import auth
    from pipeline.process_modis import _interp_geo
    auth()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    filas = []
    for l1b_sn, geo_sn, pat, rotulo in GRANULOS:
        l1b = _bajar(l1b_sn, pat, out / "hdf")
        geo = _bajar(geo_sn, pat, out / "hdf")
        if l1b is None or geo is None:
            filas.append({"granulo": pat, "rotulo": rotulo, "error": "no encontrado o no bajado"})
            continue
        glat, glon, saz, szen = _leer_geo(geo)
        latc, lonc, rad = _leer_l1b(l1b)
        if glat.shape != rad.shape:
            filas.append({"granulo": pat, "rotulo": rotulo, "error": "forma distinta %s %s" % (glat.shape, rad.shape)})
        else:
            f = comparar(glat, glon, latc, lonc, saz, szen, _interp_geo, rad)
            f.update({"granulo": f"{l1b_sn}.{pat}", "rotulo": rotulo})
            filas.append(f)
        for p in (l1b, geo):
            Path(p).unlink(missing_ok=True)
        print(json.dumps(filas[-1], ensure_ascii=False), flush=True)
    v = veredicto(filas)
    json.dump({"veredicto": v, "granulos": filas}, open(out / "probe_mod03.json", "w", encoding="utf-8"),
              indent=1, ensure_ascii=False)
    print("VEREDICTO:", v)
    sys.exit(2 if v == "INCOMPLETO" else 0)


if __name__ == "__main__":
    main()
