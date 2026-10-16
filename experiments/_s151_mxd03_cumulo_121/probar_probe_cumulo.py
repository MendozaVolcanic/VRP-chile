# Prueba sintetica del probe de la tarea 1.21 (A116: el instrumento tiene que poder dar cada resultado).
# Sin red ni HDF. Escenas MODIS de 81 x 81 pixeles de 1 km que pasan por el pipeline REAL
# (`calculate_vrp` + `store.append_record` + predicado del tablero con node) en los seis brazos:
#   ETIQUETA: el mecanismo de las 2 perdidas de la 1.17 (A46). Un pixel tibio a 4 km del crater (forma el
#             cumulo, fuera del ROI de 3 km del Test 1) y uno caliente a 15 km (gana el hotspot final,
#             dentro de la cerca de 25 km, sin rescate F47). Sin corrimiento. Tiene que dar C far / 0,
#             CC summit / 1, M = C, MC = CC, R = C, RC = CC, y el espia del flag False en C, M, R y True
#             en CC, MC, RC.
#   POSICION: el PRESENTE de la 1.17 (foco a 6 km al norte, inner 5 km, `_interp_geo` corrida 2 km al sur):
#             C summit / 1, M far / 0, y lo mismo con la etiqueta del cumulo (CC 1, MC 0). El ruido se
#             aplica con 2,000 km.
#   AUSENTE:  geolocalizaciones iguales: los brazos de una misma etiqueta dan lo mismo y el ruido vale 0.
#   RELLENO:  como AUSENTE, con MxD03 en NaN en una esquina lejos del crater.
# En todos corre C', que tiene que dar identico a C.
# Uso: python probar_probe_cumulo.py   (sale con codigo 1 si algo falla; necesita node)
import os
import sys
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(AQUI.parent / "_s151_mxd03_etiquetas"))
sys.path.insert(0, str(AQUI.parents[1]))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")

import probe_cumulo as Q  # noqa: E402
import probar_probe_mxd03 as T  # noqa: E402  (escena de la 1.17)
from pipeline import process_modis as pm  # noqa: E402

N = T.N
CLAVE = "MYD021KM.A2026073.0705"


def escena_a46(crater_km=4.0, far_km=15.0, seed=1):
    """Fondo a 262 K; pixel de 285 K a `crater_km` al norte del crater y de 330 K a `far_km` al sur."""
    rng = np.random.default_rng(seed)
    bt_mir = rng.normal(262.0, 0.4, (N, N))
    bt_tir = bt_mir.copy()
    k = N // 2
    bt_mir[k - int(round(crater_km)), k], bt_tir[k - int(round(crater_km)), k] = 285.0, 266.0
    bt_mir[k + int(round(far_km)), k], bt_tir[k + int(round(far_km)), k] = 330.0, 268.0
    lats = T.VENT[0] + (k - np.arange(N)) / 111.32
    lons = T.VENT[1] + (np.arange(N) - k) / (111.32 * np.cos(np.radians(T.VENT[0])))
    lat, lon = np.meshgrid(lats, lons, indexing="ij")
    return {"band21": pm.bt_to_radiance(bt_mir, pm.BAND21_LAMBDA).astype(np.float32),
            "band22": pm.bt_to_radiance(bt_mir, pm.BAND22_LAMBDA).astype(np.float32),
            "band31": pm.bt_to_radiance(bt_tir, pm.BAND31_LAMBDA).astype(np.float32),
            "lat": lat.astype(np.float32), "lon": lon.astype(np.float32), "angles": {}}


def _caso(verdad, corrimiento_km=0.0, relleno=False):
    interp = dict(verdad)
    interp["lat"] = (verdad["lat"] - corrimiento_km / 111.32).astype(np.float32)
    lat_m, lon_m = verdad["lat"].copy(), verdad["lon"].copy()
    if relleno:
        lat_m[:6, :6] = np.nan
        lon_m[:6, :6] = np.nan
    return Q.medir_granulo(T.L1B, Path("geo.hdf"), T.VOLCAN, (lat_m, lon_m), interp, T.VENT, CLAVE,
                           con_cprima=True)


def correr():
    return {"etiqueta": _caso(escena_a46()), "posicion": _caso(T.escena(), T.CORRIMIENTO_KM),
            "ausente": _caso(T.escena()), "relleno": _caso(T.escena(), relleno=True)}


def _dc(f, b):
    return (f["brazos"][b] or {}).get("dc")


def fallas_de(r):
    fallas = []
    for nombre, f in r.items():
        if f["cprima_igual"] is not True:
            fallas.append("%s: C' distinto de C" % nombre)
        for b in Q.BRAZOS:
            if f["flag_visto"][b] not in ([], [Q.CUMULO[b]]):
                fallas.append("%s: el brazo %s vio desde_cluster=%s" % (nombre, b, f["flag_visto"][b]))
        if abs(f["ruido"]["km_aplicado"] - f["ruido"]["km_objetivo"]) > 0.01:
            fallas.append("%s: ruido aplicado %.3f km contra %.3f pedido" % (
                nombre, f["ruido"]["km_aplicado"], f["ruido"]["km_objetivo"]))
    e = r["etiqueta"]
    if [_dc(e, b) for b in Q.BRAZOS] != ["far", "summit", "far", "summit", "far", "summit"]:
        fallas.append("ETIQUETA: etiquetas %s" % [_dc(e, b) for b in Q.BRAZOS])
    if [e["pub"][b] for b in Q.BRAZOS] != [0, 1, 0, 1, 0, 1]:
        fallas.append("ETIQUETA: publicaciones %s" % [e["pub"][b] for b in Q.BRAZOS])
    if any(e["flag_visto"][b] == [] for b in Q.BRAZOS):
        fallas.append("ETIQUETA: algun brazo no llamo a derivar_distance_class")
    p = r["posicion"]
    if (p["pub"]["C"], p["pub"]["M"], p["pub"]["CC"], p["pub"]["MC"]) != (1, 0, 1, 0):
        fallas.append("POSICION: C, M, CC, MC publican %s" % [p["pub"][b] for b in ("C", "M", "CC", "MC")])
    if abs(p["desplazamiento"]["km"] - T.CORRIMIENTO_KM) > 0.05:
        fallas.append("POSICION: midio %.3f km" % p["desplazamiento"]["km"])
    for nombre in ("ausente", "relleno"):
        f = r[nombre]
        if f["ruido"]["km_objetivo"] > 1e-6:
            fallas.append("%s: ruido distinto de 0" % nombre)
        if len({f["pub"][b] for b in ("C", "M", "R")}) != 1 or len({f["pub"][b] for b in ("CC", "MC", "RC")}) != 1:
            fallas.append("%s: brazos de una misma etiqueta publican distinto %s" % (nombre, f["pub"]))
        if len({_dc(f, b) for b in ("C", "M", "R")}) != 1:
            fallas.append("%s: brazos de produccion con etiqueta distinta" % nombre)
    return fallas


def main():
    r = correr()
    for nombre, f in r.items():
        print("%-9s desplazamiento %.3f km | ruido %s | etiquetas %s | pub %s | C' igual: %s" % (
            nombre.upper(), f["desplazamiento"]["km"], f["ruido"], {b: _dc(f, b) for b in Q.BRAZOS},
            f["pub"], f["cprima_igual"]))
    fallas = fallas_de(r)
    if fallas:
        print("FALLAS:", *fallas, sep="\n  ")
        sys.exit(1)
    print("OK: etiqueta A46 (C far, CC summit), posicion (C 1, M 0), ausente y relleno iguales, ruido aplicado, "
          "flag visto en cada brazo y C' == C")


if __name__ == "__main__":
    main()
