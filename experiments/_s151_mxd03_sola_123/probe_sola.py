# Probe S151, tarea 1.23: MxD03 sola (posicion), contra un nulo con distribucion y una vara externa.
# Solo lectura: no escribe en data/, no commitea, borra cada HDF al terminar de usarlo.
#
# POR QUE. La 1.21 dejo a MxD03 sola (brazo M) ni refutada ni probada: pierde 2 protegidas de Lascar por
# la ETIQUETA (el Test 1 deja de disparar y el hotspot salta al Salar, A46), gana 9, y su nulo (un solo
# rumbo al azar por granulo) pierde 4. Con un solo sorteo no hay distribucion contra que comparar. Este
# probe corre sobre el MISMO L1B, con el pipeline de produccion (calculate_vrp + store.append_record +
# predicado del tablero con node, A97, reutilizando probe_etiquetas.py de la 1.17 y probe_cumulo.py de la
# 1.21):
#   C       : produccion (lat/lon de `_interp_geo`);
#   M       : lat/lon de MxD03 (lo unico que cambia es la posicion);
#   R00-R19 : la grilla de `_interp_geo` trasladada en bloque, 20 rumbos por granulo. El tamano NO es el
#             del corrimiento real en km (eso hacia la 1.21) sino en PIXELES: el pixel MODIS se ensancha a
#             lo ancho del barrido, y sobre 50 grados de cenit el rumbo al azar en km movia la grilla 24 %
#             mas pixeles que MxD03 (verificador de la 1.21). Aca el corrimiento real se pasa a pixeles con
#             el jacobiano local de la grilla en el crater (km por linea y por frame, de las mismas lat/lon
#             del granulo, sin angulos), se sortea un rumbo en el espacio de pixeles con ese modulo, y se
#             vuelve a km con el mismo jacobiano. Los 20 rumbos son equiespaciados (18 grados) con una
#             fase al azar por granulo, determinista (sha1 de la clave).
#   C'      : (2 primeros granulos de cada job) la lat/lon de `_interp_geo` pasada por el parche de M:
#             tiene que dar un record identico al de C. Prueba el parche.
# La etiqueta es la de produccion en todos: ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER no se toca (la
# 1.21 ya midio que encenderla publica ~3.500 de mas) y el job guarda el valor que vio.
#
# Por granulo y brazo se guarda ademas:
#   - lo que vio el Test 1 (un espia sobre compute_test1_mir): n_roi, n_bg, L_bg, sigma_bg, delta_L, k,
#     y donde cae el pixel mas caliente del disco (si cae en el anillo de fondo de 1 a 3 km); es lo que
#     falta para decir POR QUE k salta con unos cientos de metros (punto 3 de la tarea);
#   - la posicion del pixel MIR mas caliente cerca del crater, elegido POR INDICE (el mismo pixel fisico
#     del L1B en todos los brazos) con su centroide de 3 x 3 pesado por el exceso: es la posicion pura de
#     la geolocalizacion, sin seleccion de cumulo en el medio. Es lo que se compara contra la vara VIIRS
#     (vara_viirs.json).
#
# Uso (Linux con pyhdf): EARTHDATA_TOKEN=... VRP_PROFILE=mirova_equivalent \
#     python probe_sola.py --job Lascar-1a --out out [--presupuesto-min 50]
import argparse
import hashlib
import json
import math
import os
import sys
import time
from pathlib import Path
from unittest.mock import patch

import numpy as np

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
DIR_117 = AQUI.parent / "_s151_mxd03_etiquetas"
DIR_121 = AQUI.parent / "_s151_mxd03_cumulo_121"
for p in (DIR_117, DIR_121, AQUI, RAIZ, RAIZ / "scripts"):
    sys.path.insert(0, str(p))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")

import jobs_123 as J  # noqa: E402
import probe_cumulo as Q  # noqa: E402  (1.21: trasladar, resumir, procedencia)
import probe_etiquetas as P  # noqa: E402  (1.17: procesar_brazo, publica, desplazamiento, E/S)
from pipeline import process_modis as pm  # noqa: E402
from pipeline.geo_utils import get_detection_anchor  # noqa: E402
from pipeline.test1_integrated import bt_to_radiance_um, haversine_km  # noqa: E402

K_NULOS = 20
SAL = "s151-tarea-1.23-rumbos"
NULOS = tuple("R%02d" % k for k in range(K_NULOS))
BRAZOS = ("C", "M") + NULOS
FLAG = "ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER"
PASO_JAC = 2                     # diferencia centrada de +-2 pixeles para el jacobiano
CAMPOS_TEST1 = ("triggered", "abs_criterion", "rel_criterion", "n_roi", "n_bg", "n_contributing", "L_bg",
                "sigma_bg", "delta_L_integrated", "sigma_delta_L_integrated", "k_sigma_observed",
                "rel_observed", "reason")


# ------------------------------------------------------------------ el nulo en pixeles
def jacobiano(lat, lon, i, j, h=PASO_JAC):
    """km por pixel en el pixel (i, j): [[dN/dlinea, dN/dframe], [dE/dlinea, dE/dframe]]. Diferencia
    centrada de +-h pixeles sobre la misma grilla (recortada en los bordes). None si cae en NaN."""
    lat = np.asarray(lat, dtype=np.float64)
    lon = np.asarray(lon, dtype=np.float64)
    ny, nx = lat.shape
    i0, i1 = max(i - h, 0), min(i + h, ny - 1)
    j0, j1 = max(j - h, 0), min(j + h, nx - 1)
    if i1 == i0 or j1 == j0:
        return None
    c = math.cos(math.radians(float(lat[i, j])))
    dn_di = (lat[i1, j] - lat[i0, j]) / (i1 - i0) * 111.32
    de_di = (lon[i1, j] - lon[i0, j]) / (i1 - i0) * 111.32 * c
    dn_dj = (lat[i, j1] - lat[i, j0]) / (j1 - j0) * 111.32
    de_dj = (lon[i, j1] - lon[i, j0]) / (j1 - j0) * 111.32 * c
    m = np.array([[dn_di, dn_dj], [de_di, de_dj]], dtype=np.float64)
    if not np.all(np.isfinite(m)) or abs(np.linalg.det(m)) < 1e-9:
        return None
    return m


def a_pixeles(jac, dn, de):
    """Vector (linea, frame) en pixeles que produce el corrimiento (dn, de) km con ese jacobiano."""
    p = np.linalg.solve(jac, np.array([dn, de], dtype=np.float64))
    return float(p[0]), float(p[1])


def rumbos(clave, k=K_NULOS):
    """k rumbos equiespaciados en el espacio de pixeles (grados desde el eje de lineas, hacia el eje de
    frames), con una fase al azar determinista por granulo. Cada rumbo es uniforme por si solo."""
    h = hashlib.sha1((SAL + clave).encode()).hexdigest()
    u = int(h[:12], 16) / float(16 ** 12)
    return [round(360.0 * ((u + n / k) % 1.0), 6) for n in range(k)]


def vector_nulo(jac, modulo_px, angulo):
    """(dn, de) km de un corrimiento de `modulo_px` pixeles en el rumbo `angulo` del espacio de pixeles."""
    a = math.radians(angulo)
    q = np.array([modulo_px * math.cos(a), modulo_px * math.sin(a)])
    v = jac @ q
    return float(v[0]), float(v[1])


def medido_en(lat_r, lon_r, lat, lon, i, j):
    """Corrimiento aplicado (km) medido en el MISMO pixel donde se calculo el jacobiano. Medirlo en otro
    pixel (el mas cercano al crater en la grilla trasladada, como la 1.21) mezclaria con el error del nulo
    el cambio de tamano del pixel de un frame a otro, que crece hacia el borde del barrido."""
    la, lo = float(lat[i, j]), float(lon[i, j])
    dn = (float(lat_r[i, j]) - la) * 111.32
    de = (float(lon_r[i, j]) - lo) * 111.32 * math.cos(math.radians(la))
    return {"dn_km": round(dn, 4), "de_km": round(de, 4), "km": round(math.hypot(dn, de), 4)}


def trasladar_ne(lat, lon, dn, de):
    """Traslacion rigida de toda la grilla por (dn, de) km (la de la 1.21, con el vector en vez del rumbo)."""
    return Q.trasladar(lat, lon, math.hypot(dn, de), math.degrees(math.atan2(de, dn)) % 360.0)


# ------------------------------------------------------------------ un brazo, con el espia del Test 1
def procesar(l1b, geo, volcan, latlon, feats, lector):
    """Un brazo con la etiqueta de produccion. Devuelve (record, lista de lo que vio el Test 1)."""
    vistos = []
    real = pm.compute_test1_mir

    def espia(*a, **k):
        r = real(*a, **k)
        d = {c: (r.get(c) if not isinstance(r.get(c), (np.floating, np.integer, np.bool_)) else r.get(c).item())
             for c in CAMPOS_TEST1}
        bt, lat, lon = k.get("bt"), k.get("lat"), k.get("lon")
        try:
            dist = haversine_km(k["vent_lat"], k["vent_lon"], np.asarray(lat, dtype=np.float64),
                                np.asarray(lon, dtype=np.float64))
            roi = (dist <= k.get("roi_km", 3.0)) & np.isfinite(bt)
            if roi.any():
                idx = np.flatnonzero(roi.ravel())[int(np.nanargmax(np.asarray(bt, dtype=np.float64).ravel()[roi.ravel()]))]
                i, j = np.unravel_index(idx, bt.shape)
                d["caliente_dist_km"] = round(float(dist[i, j]), 3)
                d["caliente_bt_k"] = round(float(bt[i, j]), 3)
                d["caliente_en_anillo"] = bool(dist[i, j] > k.get("inner_ring_km", 1.0))
                d["caliente_indice"] = [int(i), int(j)]
                lb, dl = d.get("L_bg"), d.get("delta_L_integrated") or 0.0
                if lb is not None and np.isfinite(lb) and dl > 0:
                    lh = float(bt_to_radiance_um(np.array([bt[i, j]], dtype=np.float64), k["lambda_um"])[0])
                    d["fraccion_del_caliente"] = round(max(lh - lb, 0.0) / dl, 4)
        except Exception as e:  # el diagnostico no puede tumbar el brazo
            d["error_diagnostico"] = "%s: %s" % (type(e).__name__, e)
        vistos.append({x: (round(y, 6) if isinstance(y, float) and np.isfinite(y) else
                           (None if isinstance(y, float) else y)) for x, y in d.items()})
        return r

    with patch.object(pm, "compute_test1_mir", espia):
        rec = P.procesar_brazo(l1b, geo, volcan, latlon, feats, lector)
    return rec, vistos


# ------------------------------------------------------------------ la posicion pura (pixel por indice)
def pico_por_indice(datos, posiciones, lat_m, lon_m, vent, r_sel_km):
    """El pixel MIR mas caliente (banda 22, con la 21 donde la 22 no es finita) entre los que caen a menos
    de r_sel_km del crater con `_interp_geo` O con MxD03 (seleccion simetrica entre las dos), y su
    centroide de 3 x 3 pesado por el exceso sobre la mediana de la seleccion. Los pesos e indices son los
    mismos en todos los brazos; solo cambia la lat/lon. `posiciones`: {brazo: (lat, lon)}. Devuelve None si
    la seleccion queda vacia."""
    b22 = np.asarray(datos["band22"], dtype=np.float64)
    b21 = np.asarray(datos["band21"], dtype=np.float64)
    L = np.where(np.isfinite(b22), b22, b21)
    lat_c, lon_c = posiciones["C"]
    d_c = haversine_km(vent[0], vent[1], np.asarray(lat_c, dtype=np.float64), np.asarray(lon_c, dtype=np.float64))
    with np.errstate(invalid="ignore"):
        d_m = haversine_km(vent[0], vent[1], np.asarray(lat_m, dtype=np.float64), np.asarray(lon_m, dtype=np.float64))
        sel = ((d_c <= r_sel_km) | (np.nan_to_num(d_m, nan=1e9) <= r_sel_km)) & np.isfinite(L)
    if not sel.any():
        return None
    med = float(np.median(L[sel]))
    flat = np.flatnonzero(sel.ravel())
    i, j = np.unravel_index(flat[int(np.argmax(L.ravel()[flat]))], L.shape)
    i0, i1, j0, j1 = max(i - 1, 0), min(i + 2, L.shape[0]), max(j - 1, 0), min(j + 2, L.shape[1])
    w = np.maximum(np.nan_to_num(L[i0:i1, j0:j1] - med, nan=0.0), 0.0)
    if w.sum() <= 0:
        w = np.zeros_like(w)
        w[i - i0, j - j0] = 1.0
    out = {"linea": int(i), "frame": int(j), "exceso": round(float(L[i, j] - med), 6), "pos": {}}
    for b, (la, lo) in posiciones.items():
        la = np.asarray(la[i0:i1, j0:j1], dtype=np.float64)
        lo = np.asarray(lo[i0:i1, j0:j1], dtype=np.float64)
        ok = np.isfinite(la) & np.isfinite(lo)
        ww = w * ok
        if ww.sum() <= 0:
            out["pos"][b] = None
            continue
        out["pos"][b] = [round(float((ww * np.where(ok, la, 0)).sum() / ww.sum()), 6),
                         round(float((ww * np.where(ok, lo, 0)).sum() / ww.sum()), 6)]
    return out


def resumir(rec, vistos):
    s = Q.resumir(rec)
    if s is None:
        return None
    s["test1"] = vistos[-1] if vistos else None
    s["test1_llamadas"] = len(vistos)
    return s


# ------------------------------------------------------------------ un granulo
def medir_granulo(l1b, geo, volcan, latlon_m, datos, vent, clave, feats=None, con_cprima=False, k=K_NULOS):
    """C, M y los k nulos (y C' si se pide) sobre el mismo L1B. Devuelve el dict del granulo."""
    nulos_n = NULOS[:k]
    lector = lambda _p: P._copia(datos)  # noqa: E731
    lat, lon = datos["lat"], datos["lon"]
    desp = P.desplazamiento_crater(lat, lon, latlon_m[0], latlon_m[1], vent)
    jac = jacobiano(lat, lon, desp["linea"], desp["frame"])
    if jac is None:
        raise ValueError("jacobiano degenerado en el crater")
    pl, pf = a_pixeles(jac, desp["dn_km"], desp["de_km"])
    modulo = math.hypot(pl, pf)
    pos = {"C": None, "M": latlon_m}
    nulos = []
    for n, ang in zip(range(k), rumbos(clave, k)):
        dn, de = vector_nulo(jac, modulo, ang)
        lat_r, lon_r = trasladar_ne(lat, lon, dn, de)
        ap = medido_en(lat_r, lon_r, lat, lon, desp["linea"], desp["frame"])
        apl, apf = a_pixeles(jac, ap["dn_km"], ap["de_km"])
        pos[nulos_n[n]] = (lat_r, lon_r)
        nulos.append({"k": n, "angulo_grados": ang, "dn_km": round(dn, 4), "de_km": round(de, 4),
                      "km": round(math.hypot(dn, de), 4), "km_aplicado": ap["km"],
                      "px_aplicado": round(math.hypot(apl, apf), 4)})
    recs, vistos = {}, {}
    for b in ("C", "M") + nulos_n:
        recs[b], vistos[b] = procesar(l1b, geo, volcan, pos[b], feats, lector)
    inner = volcan.get("inner_radius_km")
    brazos = ("C", "M") + nulos_n
    pubs = P.publica([recs[b] for b in brazos], inner)
    posiciones = {"C": (lat, lon), "M": latlon_m}
    posiciones.update({b: pos[b] for b in nulos_n})
    fila = {"desplazamiento": desp,
            "jacobiano_km_por_px": [[round(float(x), 5) for x in fila_j] for fila_j in jac],
            "corrimiento_px": {"linea": round(pl, 4), "frame": round(pf, 4), "modulo": round(modulo, 4)},
            "nulos": nulos, "brazos": {b: resumir(recs[b], vistos[b]) for b in brazos},
            "pub": dict(zip(brazos, pubs)),
            "pico": pico_por_indice(datos, posiciones, latlon_m[0], latlon_m[1], vent, float(inner or 5.0)),
            "cprima_igual": None}
    if con_cprima:
        rcp, _ = procesar(l1b, geo, volcan, (lat.copy(), lon.copy()), feats, lector)
        fila["cprima_igual"] = P.registros_iguales(recs["C"], rcp)
    return fila


# ------------------------------------------------------------------ E/S (solo en el runner)
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--job", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--poblacion", default=str(J.POBLACION))
    ap.add_argument("--presupuesto-min", type=float, default=50.0)
    args = ap.parse_args()
    if not os.environ.get("EARTHDATA_TOKEN", "").strip():
        sys.exit("EARTHDATA_TOKEN vacio: el probe no usa usuario y clave (A71).")
    import run_pipeline as rp     # el mismo dict de volcan que produccion (overrides del perfil incluidos)
    from pipeline.fetch import auth
    auth()
    t0 = time.time()
    pob = J.cargar(args.poblacion)
    job = J.partir(pob)[args.job]
    vol = job["volcan"]
    por_clave = {g["clave"]: g for g in pob["volcanes"][vol]["muestra"]}
    inner = pob["volcanes"][vol]["inner_radius_km"]
    volcan = rp.load_volcanoes(vol)[0]
    if volcan.get("inner_radius_km") != inner:
        sys.exit("inner_radius_km de volcanoes.yaml (%s) distinto del de poblacion.json (%s)"
                 % (volcan.get("inner_radius_km"), inner))
    vent = get_detection_anchor(volcan)
    feats = rp.VOLCANIC_FEATURES.get(volcan["name"])
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    hdf = out / "hdf"
    destino = out / f"{args.job}.json"
    estado = {"job": args.job, "origen": job["origen"], "volcan": vol, "inner_radius_km": inner,
              "completo": False, **Q.procedencia(), "brazos": list(BRAZOS), "k_nulos": K_NULOS,
              "flag_" + FLAG: bool(getattr(pm, FLAG)), "granulos": []}
    n_cprima = 0
    for clave in job["granulos"]:
        fila = {"clave": clave, "estrato": por_clave[clave]["estrato"], "censo": por_clave[clave]["censo"]}
        if (time.time() - t0) / 60.0 > args.presupuesto_min:
            fila["estado"] = "sin_tiempo"
            estado["granulos"].append(fila)
            P.guardar(destino, estado)
            continue
        prod, patron = clave.split(".", 1)
        l1b = geo = None
        try:
            l1b = P._bajar(prod, patron, hdf)
            geo = P._bajar(prod.replace("021KM", "03"), patron, hdf)
            if l1b is None or geo is None:
                fila["estado"] = "error"
                fila["error"] = "no encontrado o no bajado (%s)" % ("L1B" if l1b is None else "MxD03")
            else:
                lat_m, lon_m = P._leer_mxd03(geo)
                d = pm.read_modis_l1b(l1b)
                con_cp = n_cprima < P.N_CPRIMA
                fila.update(medir_granulo(l1b, geo, volcan, (lat_m, lon_m), d, vent, clave, feats, con_cp))
                i, j = fila["desplazamiento"]["linea"], fila["desplazamiento"]["frame"]
                fila["mxd03_relleno_cerca"] = bool(np.isnan(lat_m[max(i - 30, 0):i + 31, max(j - 30, 0):j + 31]).any())
                n_cprima += int(con_cp)
                g = por_clave[clave]
                fila["c_igual_a_guardada"] = (((fila["brazos"]["C"] or {}).get("dc") == g.get("dc_guardada"))
                                              and fila["pub"]["C"] == g.get("pub_guardada"))
                fila["estado"] = "ok"
        except Exception as e:  # un granulo roto no tumba el job; queda contado como error
            fila["estado"] = "error"
            fila["error"] = "%s: %s" % (type(e).__name__, e)
        finally:
            for p in (l1b, geo):
                if p is not None:
                    Path(p).unlink(missing_ok=True)
        estado["granulos"].append(fila)
        estado["minutos"] = round((time.time() - t0) / 60.0, 1)
        P.guardar(destino, estado)
        print(json.dumps({"clave": clave, "estado": fila.get("estado"),
                          "pub": {b: (fila.get("pub") or {}).get(b) for b in ("C", "M")},
                          "nulos_publican": sum((fila.get("pub") or {}).get(b, 0) for b in NULOS),
                          "cprima_igual": fila.get("cprima_igual")}, ensure_ascii=False), flush=True)
    estado["completo"] = True
    P.guardar(destino, estado)
    n_ok = sum(1 for f in estado["granulos"] if f.get("estado") == "ok")
    print("%s: %d de %d granulos medidos en %.1f min" % (args.job, n_ok, len(job["granulos"]),
                                                         (time.time() - t0) / 60.0))


if __name__ == "__main__":
    main()
