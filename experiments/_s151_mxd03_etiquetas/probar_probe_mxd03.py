# Prueba sintetica del probe de la tarea 1.17 (A116: el instrumento tiene que poder dar cada resultado).
# Sin red ni HDF. Arma una escena MODIS de 81 x 81 pixeles de 1 km con un foco de 335 K a 6 km al
# norte del crater (inner = 5 km) y la pasa por el pipeline REAL (`calculate_vrp` + `store.append_record`
# + predicado del tablero con node) en los dos brazos del probe:
#   PRESENTE: la geolocalizacion "interpolada" esta corrida 2 km al sur de la verdadera (MxD03). El
#             brazo C ve el foco a 4 km (summit, publica) y el brazo M a 6 km (far, no publica).
#             El probe tiene que medir el corrimiento (2 km) y el cambio summit->far, 1->0.
#   AUSENTE:  las dos geolocalizaciones coinciden. El probe tiene que dar "igual" en todo.
#   RELLENO:  como AUSENTE, pero MxD03 trae relleno (-999) en una esquina lejos del crater: "igual".
# En los tres casos corre tambien el brazo C' (la lat/lon interpolada por el mismo parche que M), que
# tiene que dar un record identico al del brazo C.
# Uso: python probar_probe_mxd03.py   (sale con codigo 1 si algo falla; necesita node)
import os
import sys
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(AQUI.parents[1]))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")

import probe_etiquetas as P  # noqa: E402
from pipeline import process_modis as pm  # noqa: E402

CORRIMIENTO_KM = 2.0
VENT = (-23.36293, -67.731416)
VOLCAN = {"name": "Sintetico_s151", "lat": -23.369, "lon": -67.732, "radius_km": 25,
          "vent_lat": VENT[0], "vent_lon": VENT[1], "vent_radius_km": 3, "inner_radius_km": 5,
          "lbg_global_compatible": True}
L1B = Path("MYD021KM.A2026073.0705.061.2026074000000.hdf")   # 07:05 UTC en Lascar: de noche
N = 81


def escena(foco_km_norte=6.0, seed=1):
    """Radiancias de una escena a 262 K con ruido de 0,4 K y un pixel a 335 K (TIR 268 K)."""
    rng = np.random.default_rng(seed)
    bt_mir = rng.normal(262.0, 0.4, (N, N))
    bt_tir = bt_mir.copy()
    k = N // 2
    r = k - int(round(foco_km_norte))
    bt_mir[r, k], bt_tir[r, k] = 335.0, 268.0
    lats = VENT[0] + (k - np.arange(N)) / 111.32
    lons = VENT[1] + (np.arange(N) - k) / (111.32 * np.cos(np.radians(VENT[0])))
    lat, lon = np.meshgrid(lats, lons, indexing="ij")
    return {"band21": pm.bt_to_radiance(bt_mir, pm.BAND21_LAMBDA).astype(np.float32),
            "band22": pm.bt_to_radiance(bt_mir, pm.BAND22_LAMBDA).astype(np.float32),
            "band31": pm.bt_to_radiance(bt_tir, pm.BAND31_LAMBDA).astype(np.float32),
            "lat": lat.astype(np.float32), "lon": lon.astype(np.float32), "angles": {}}


def _caso(corrimiento_km, relleno=False):
    verdad = escena()
    interp = dict(verdad)
    interp["lat"] = (verdad["lat"] - corrimiento_km / 111.32).astype(np.float32)  # corrida hacia el sur
    lat_m, lon_m = verdad["lat"].copy(), verdad["lon"].copy()
    if relleno:   # MxD03 trae -999 (NaN tras limpiar) en una esquina a 50 km del crater, fuera del ROI
        lat_m[:6, :6] = np.nan
        lon_m[:6, :6] = np.nan
    rc, rm, rcp = P.medir_granulo(L1B, Path("geo.hdf"), VOLCAN, (lat_m, lon_m), datos=interp, con_cprima=True)
    pub_c, pub_m = P.publica([rc, rm], VOLCAN["inner_radius_km"])
    return {"c": P.resumir(rc), "m": P.resumir(rm), "pub": (pub_c, pub_m),
            "comparacion": P.comparar(P.resumir(rc), P.resumir(rm), pub_c, pub_m),
            "cprima_igual": P.registros_iguales(rc, rcp),
            "desplazamiento": P.desplazamiento_crater(interp["lat"], interp["lon"], lat_m, lon_m, VENT)}


def correr():
    return {"presente": _caso(CORRIMIENTO_KM), "ausente": _caso(0.0), "relleno": _caso(0.0, relleno=True)}


def main():
    r = correr()
    fallas = []
    for nombre, caso in r.items():
        print("%-8s desplazamiento %s | C %s | M %s | %s | C' igual a C: %s" % (
            nombre.upper(), caso["desplazamiento"], {k: caso["c"][k] for k in ("dc", "final_dist", "pc_dist")},
            {k: caso["m"][k] for k in ("dc", "final_dist", "pc_dist")}, caso["comparacion"], caso["cprima_igual"]))
    presente, ausente, relleno = r["presente"], r["ausente"], r["relleno"]
    if presente["comparacion"] != {"etiqueta": "summit->far", "pub": "1->0", "deteccion_cambia": False}:
        fallas.append("PRESENTE: el probe no vio el cambio summit->far / 1->0")
    if abs(presente["desplazamiento"]["km"] - CORRIMIENTO_KM) > 0.05:
        fallas.append("PRESENTE: midio %.3f km en vez de %.1f" % (presente["desplazamiento"]["km"], CORRIMIENTO_KM))
    if ausente["comparacion"] != {"etiqueta": "igual", "pub": "igual", "deteccion_cambia": False}:
        fallas.append("AUSENTE: el probe invento un cambio")
    if ausente["desplazamiento"]["km"] > 1e-6:
        fallas.append("AUSENTE: midio un corrimiento que no existe")
    if relleno["comparacion"]["etiqueta"] != "igual" or relleno["comparacion"]["pub"] != "igual":
        fallas.append("RELLENO: el NaN de MxD03 lejos del crater cambio la etiqueta o la publicacion")
    if not all(c["cprima_igual"] for c in r.values()):
        fallas.append("C': la lat/lon interpolada por el parche no da el mismo record que el brazo C")
    if fallas:
        print("FALLAS:", *fallas, sep="\n  ")
        sys.exit(1)
    print("OK: corrimiento presente (summit->far, 1->0, 2 km), ausente (igual), relleno lejano (igual) y C' == C")


if __name__ == "__main__":
    main()
