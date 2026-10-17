# Prueba sintetica del probe de la tarea 1.23 (A116: el instrumento tiene que poder dar cada resultado).
# Sin red ni HDF. Escenas MODIS de 81 x 81 pixeles que pasan por el pipeline REAL (`calculate_vrp` +
# `store.append_record` + predicado del tablero con node) en C, M, los 20 nulos y C':
#   POSICION: la de la 1.17 (foco de 335 K a 6 km al norte, inner 5 km, `_interp_geo` corrida 2 km al
#             sur). C publica, M no. Los nulos tienen modulo 2 px (= 2 km en esta grilla de 1 km) y, segun
#             el rumbo, el foco queda dentro o fuera del inner: al menos uno tiene que publicar y al menos
#             uno no (el nulo PUEDE cambiar la publicacion en los dos sentidos). El pixel por indice tiene
#             que ser el foco, en la posicion de MxD03 en M y 2 km al sur en C.
#   ANISO:    grilla con pixeles de 1 km a lo largo de la traza y 2 km a lo ancho (el borde del barrido),
#             corrimiento real de 2 km a lo ancho (1 px). Los nulos tienen que tener 2 km, el mismo tamano
#             EN KM que el real (version 2: el invariante del pipeline es el km, invariante_km.py), y su
#             modulo en pixeles tiene que ir de 1 a 2 (la anotacion).
#   SIERRA:   la grilla de `_interp_geo` con bow tie (verificador del pre-registro, jac_bowtie.py): filas de
#             amarre en las lineas 2 + 5t de barridos de 10 lineas con huella f = 1,95 km, estiradas con
#             la misma funcion del pipeline. El espaciado a lo largo de la traza alterna 0,05 y 1,95 km por
#             linea. Corrimiento real de 1 km a lo largo: el jacobiano sobre un barrido entero tiene que
#             dar 1 px; el de +-2 lineas de la version 1 daba 0,5 o 20 px segun la fase.
#   TEST1:    disco de 5 pixeles a +1 K sobre el crater (dispara el Test 1, escena de la 1.21) y
#             `_interp_geo` corrida 1,2 km al sur: en C el pixel mas caliente del disco cae a mas de 1 km
#             del crater, dentro del anillo de fondo; en M cae en el centro. El espia tiene que verlo.
#   AUSENTE:  geolocalizaciones iguales: modulo 0, todos los brazos iguales, C' igual a C.
# Uso: python probar_probe_sola.py   (sale con codigo 1 si algo falla; necesita node)
import math
import os
import sys
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
for p in (AQUI, AQUI.parent / "_s151_mxd03_cumulo_121", AQUI.parent / "_s151_mxd03_etiquetas", AQUI.parents[1]):
    sys.path.insert(0, str(p))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")

import probar_probe_cumulo as T21  # noqa: E402  (escena del Test 1 de la 1.21)
import probar_probe_mxd03 as T  # noqa: E402  (escena de la 1.17)
import probe_sola as S  # noqa: E402
from pipeline import process_modis as pm  # noqa: E402

CLAVE = "MYD021KM.A2026073.0705"


def _ne(lat0, lon0, lat, lon):
    return (lat - lat0) * 111.32, (lon - lon0) * 111.32 * math.cos(math.radians(lat0))


def escena_aniso(seed=1):
    """Como la escena de la 1.17 (foco a 6 km al norte), con pixeles de 2 km a lo ancho (este-oeste)."""
    d = T.escena(seed=seed)
    k = T.N // 2
    lats = T.VENT[0] + (k - np.arange(T.N)) / 111.32
    lons = T.VENT[1] + 2.0 * (np.arange(T.N) - k) / (111.32 * np.cos(np.radians(T.VENT[0])))
    lat, lon = np.meshgrid(lats, lons, indexing="ij")
    d["lat"], d["lon"] = lat.astype(np.float32), lon.astype(np.float32)
    return d


def lineas_bowtie(n, f, total=2030):
    """Posicion a lo largo de la traza (km) de n lineas al centro de un granulo de `total` lineas, tal como
    las deja `_interp_geo` con bow tie: barridos de 10 lineas que avanzan 10 km, huella f km, filas de
    amarre en 2 + 5t (offset 2 de #828), estiradas con pipeline.process_modis._interp_geo."""
    L = np.arange(total)
    y = 10.0 * (L // 10) + (L % 10 - 4.5) * f
    tie = np.repeat(y[2::5][:, None], 2, axis=1)
    yi = pm._interp_geo(tie, total, 2)[:, 0]
    c = total // 2
    return yi[c - n // 2:c - n // 2 + n]


def escena_sierra(f=1.95, seed=1):
    """La escena de la 1.17 (foco a 6 km al norte) sobre la grilla con bow tie: lineas en diente de sierra
    de norte a sur, pixeles de 2 km a lo ancho."""
    d = T.escena(seed=seed)
    k = T.N // 2
    y = lineas_bowtie(T.N, f)
    y = y - y[k]
    lats = T.VENT[0] - y / 111.32                      # la linea crece hacia el sur
    lons = T.VENT[1] + 2.0 * (np.arange(T.N) - k) / (111.32 * np.cos(np.radians(T.VENT[0])))
    lat, lon = np.meshgrid(lats, lons, indexing="ij")
    d["lat"], d["lon"] = lat.astype(np.float32), lon.astype(np.float32)
    return d


def _caso(verdad, dn_km=0.0, de_km=0.0):
    """`_interp_geo` = la verdad corrida (dn, de) km; MxD03 = la verdad."""
    interp = dict(verdad)
    lat_v = verdad["lat"].astype(np.float64)
    interp["lat"] = (lat_v + dn_km / 111.32).astype(np.float32)
    interp["lon"] = (verdad["lon"].astype(np.float64)
                     + de_km / (111.32 * np.cos(np.radians(lat_v)))).astype(np.float32)
    lat_m, lon_m = verdad["lat"].copy(), verdad["lon"].copy()
    return S.medir_granulo(T.L1B, Path("geo.hdf"), T.VOLCAN, (lat_m, lon_m), interp, T.VENT, CLAVE,
                           con_cprima=True)


def correr():
    return {"posicion": _caso(T.escena(), dn_km=-T.CORRIMIENTO_KM),
            "aniso": _caso(escena_aniso(), de_km=-2.0),
            "sierra": _caso(escena_sierra(), dn_km=-1.0),
            "test1": _caso(T21.escena_test1(), dn_km=-1.2),
            "ausente": _caso(T.escena())}


def fallas_de(r):
    fallas = []
    for nombre, f in r.items():
        if f["cprima_igual"] is not True:
            fallas.append("%s: C' distinto de C" % nombre)
        real = f["desplazamiento"]["km"]
        for x in f["nulos"]:
            if abs(x["km"] - real) > 0.01:
                fallas.append("%s: nulo %d de %.3f km contra %.3f del real" % (nombre, x["k"], x["km"], real))
            if abs(x["km_aplicado"] - x["km"]) > 0.01:
                fallas.append("%s: nulo %d aplicado %.3f km contra %.3f pedido" % (nombre, x["k"], x["km_aplicado"], x["km"]))
        difs = sorted((x["angulo_grados"] - f["nulos"][0]["angulo_grados"]) % 360 for x in f["nulos"])
        if any(abs(a - b - 18.0) > 1e-3 for a, b in zip(difs[1:], difs[:-1])):
            fallas.append("%s: los rumbos no son equiespaciados" % nombre)
        if len(f["brazos"]) != 22 or len(f["pub"]) != 22:
            fallas.append("%s: %d brazos" % (nombre, len(f["brazos"])))
    p = r["posicion"]
    if (p["pub"]["C"], p["pub"]["M"]) != (1, 0):
        fallas.append("POSICION: C, M publican %s" % [p["pub"]["C"], p["pub"]["M"]])
    n_pub = sum(p["pub"][b] for b in S.NULOS)
    if not 0 < n_pub < len(S.NULOS):
        fallas.append("POSICION: %d de 20 nulos publican (el nulo tiene que poder dar los dos)" % n_pub)
    if abs(p["corrimiento_px"]["modulo"] - 2.0) > 0.02:
        fallas.append("POSICION: modulo %.3f px" % p["corrimiento_px"]["modulo"])
    pk = p["pico"] or {}
    if (pk.get("linea"), pk.get("frame")) != (T.N // 2 - 6, T.N // 2):
        fallas.append("POSICION: el pixel por indice no es el foco: %s" % [pk.get("linea"), pk.get("frame")])
    else:
        nm, em = _ne(T.VENT[0], T.VENT[1], *pk["pos"]["M"])
        nc, ec = _ne(T.VENT[0], T.VENT[1], *pk["pos"]["C"])
        if abs(nm - 6.0) > 0.15 or abs(em) > 0.15 or abs(nc - 4.0) > 0.15 or abs(ec) > 0.15:
            fallas.append("POSICION: pico M (%.2f, %.2f) y C (%.2f, %.2f) km" % (nm, em, nc, ec))
        for x in p["nulos"]:
            nr, er = _ne(T.VENT[0], T.VENT[1], *pk["pos"]["R%02d" % x["k"]])
            if math.hypot(nr - nc - x["dn_km"], er - ec - x["de_km"]) > 0.01:
                fallas.append("POSICION: el pico del nulo %d no es C mas su vector" % x["k"])
    a = r["aniso"]
    if abs(a["corrimiento_px"]["modulo"] - 1.0) > 0.02:
        fallas.append("ANISO: modulo real %.3f px (se esperaba 1)" % a["corrimiento_px"]["modulo"])
    pxs = [x["px_aplicado"] for x in a["nulos"]]
    if min(pxs) < 0.98 or max(pxs) > 2.02 or max(pxs) - min(pxs) < 0.8:
        fallas.append("ANISO: px de los nulos %s (se esperaba de 1 a 2)" % [round(x, 2) for x in pxs])
    if any(abs(x["km"] - 2.0) > 0.01 for x in a["nulos"]):
        fallas.append("ANISO: km de los nulos distintos de 2")
    si = r.get("sierra")
    if si is not None and abs(si["corrimiento_px"]["modulo"] - 1.0) > 0.05:
        fallas.append("SIERRA: modulo real %.3f px (se esperaba 1: el jacobiano tiene que cubrir un barrido)"
                      % si["corrimiento_px"]["modulo"])
    t = r["test1"]
    tc, tm = (t["brazos"]["C"] or {}).get("test1") or {}, (t["brazos"]["M"] or {}).get("test1") or {}
    if tc.get("caliente_en_anillo") is not True or tm.get("caliente_en_anillo") is not False:
        fallas.append("TEST1: el pixel caliente en el anillo: C %s, M %s" % (tc.get("caliente_en_anillo"),
                                                                             tm.get("caliente_en_anillo")))
    for b in ("C", "M"):
        s = t["brazos"][b] or {}
        if s.get("test1_llamadas") != 1 or abs((s["test1"]["k_sigma_observed"] or 0) - (s["test1_k_observed"] or 0)) > 0.006:
            fallas.append("TEST1: el espia de %s no coincide con el record: %s" % (b, s.get("test1")))
    if not tm.get("triggered"):
        fallas.append("TEST1: en M (disco centrado) el Test 1 tiene que disparar")
    au = r["ausente"]
    if au["corrimiento_px"]["modulo"] > 1e-3 or len({au["pub"][b] for b in S.BRAZOS}) != 1:
        fallas.append("AUSENTE: modulo %s, publicaciones %s" % (au["corrimiento_px"]["modulo"], set(au["pub"].values())))
    return fallas


def main():
    r = correr()
    for nombre, f in r.items():
        t = (f["brazos"]["C"] or {}).get("test1") or {}
        print("%-9s modulo real %.3f px | km nulos %.2f a %.2f | pub C %d M %d nulos %d de 20 | test1 C k=%s anillo=%s | C' %s" % (
            nombre.upper(), f["corrimiento_px"]["modulo"], min(x["km"] for x in f["nulos"]),
            max(x["km"] for x in f["nulos"]), f["pub"]["C"], f["pub"]["M"], sum(f["pub"][b] for b in S.NULOS),
            t.get("k_sigma_observed"), t.get("caliente_en_anillo"), f["cprima_igual"]))
    fallas = fallas_de(r)
    if fallas:
        print("FALLAS:", *fallas, sep="\n  ")
        sys.exit(1)
    print("OK: nulo del tamano en km del real (isotropo, anisotropo y con bow tie), aplicado igual al pedido, "
          "rumbos equiespaciados, el nulo cambia la publicacion en los dos sentidos, jacobiano sobre un barrido, "
          "pixel por indice, espia del Test 1 y C' == C")


if __name__ == "__main__":
    main()
