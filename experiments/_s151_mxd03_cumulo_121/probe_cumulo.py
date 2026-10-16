# Probe S151, tarea 1.21: MxD03 junto con la etiqueta desde el cumulo, con un brazo de ruido de control.
# Solo lectura: no escribe en data/, no commitea, borra cada HDF al terminar de usarlo.
#
# POR QUE. La 1.17 (run 38894508138) dio PIERDE PROTEGIDA por la letra, pero su verificador mostro que
# las 2 perdidas (Lascar Terra 2026-04-20 y 2026-04-30 01:30) no son de posicion: con MxD03 el cumulo
# queda igual y mas cerca del crater, el Test 1 deja de disparar, gana un hotspot `eruption` en el borde
# del Salar a 19 a 21 km, y la etiqueta sale de ese hotspot porque
# `ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER = False` (A46/A81). Este probe separa los dos efectos sobre
# el mismo L1B y mide cuanto cambio produce mover las posiciones al azar (A110: el nulo se mide).
#
# Brazos (todos con el pipeline de produccion, `calculate_vrp` + `store.append_record` + predicado del
# tablero con node, A97; reutiliza probe_etiquetas.py de la 1.17):
#   C  : produccion (lat/lon de `_interp_geo`, etiqueta desde el hotspot final);
#   CC : produccion con la etiqueta desde el cumulo (flag en memoria);
#   M  : lat/lon de MxD03, etiqueta de produccion (repite el brazo M de la 1.17);
#   MC : lat/lon de MxD03 y etiqueta desde el cumulo (el arreglo que se evalua);
#   R  : lat/lon de `_interp_geo` trasladada en bloque una distancia igual al corrimiento medido en el
#        crater de ESE granulo, en una direccion al azar (determinista por granulo), etiqueta de produccion;
#   RC : la misma traslacion que R, etiqueta desde el cumulo;
#   C' : (2 primeros granulos de cada job) la lat/lon de `_interp_geo` pasada por el mismo parche que M:
#        tiene que dar un record identico al de C. Prueba el parche, no es un control del efecto.
#
# EL FLAG (A89, A118). `pipeline/process_modis.py:173` importa ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER
# por valor desde pipeline.profile, asi que parchear pipeline.profile no llega a nada: el brazo lo
# cambia en el modulo process_modis, que es el nombre que leen sus dos consumidores (las dos llamadas a
# `derivar_distance_class`, process_modis.py:1328 y :1495). store.py y el tablero no lo leen. Cada brazo
# registra el `desde_cluster` que vio `derivar_distance_class` en cada llamada (un espia), y el
# evaluador da INVALIDO si un brazo con etiqueta del cumulo vio False o uno de produccion vio True.
#
# Uso (Linux con pyhdf): EARTHDATA_TOKEN=... VRP_PROFILE=mirova_equivalent \
#     python probe_cumulo.py --job Lascar-1 --out out [--presupuesto-min 70]
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
sys.path.insert(0, str(DIR_117))
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")

import probe_etiquetas as P  # noqa: E402  (1.17: procesar_brazo, publica, desplazamiento, guardar, ...)
from pipeline import process_modis as pm  # noqa: E402
from pipeline.geo_utils import get_detection_anchor  # noqa: E402

FLAG = "ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER"
BRAZOS = ("C", "CC", "M", "MC", "R", "RC")
CUMULO = {"C": False, "CC": True, "M": False, "MC": True, "R": False, "RC": True}
POSICION = {"C": "interp", "CC": "interp", "M": "mxd03", "MC": "mxd03", "R": "ruido", "RC": "ruido"}
SAL_RUIDO = "s151-tarea-1.21-ruido"
N_CPRIMA = P.N_CPRIMA
EXTRA = ("triggered_test1", "test1_k_observed", "hotspot_dist_km", "discarded_reason", "vrp_vent_mw",
         "diag_a46_relabel", "final_hotspot_source")


# ------------------------------------------------------------------ un brazo, con el flag en memoria
def procesar(l1b, geo, volcan, latlon, feats, lector, cumulo):
    """Un brazo: probe_etiquetas.procesar_brazo con el flag del modulo process_modis fijado a `cumulo`.
    Devuelve (record, lista ordenada de los `desde_cluster` que vio derivar_distance_class, llamadas).
    `llamadas` guarda los cuatro argumentos y el resultado de cada llamada (verificador del
    pre-registro, bloqueante 1): en la rama del Test 1 (process_modis.py:1381) el cumulo que entra a
    `derivar_distance_class` (:1328) es el del camino de erupcion, y despues se reemplaza por el del
    Test 1 (:1425/:1440), que es el que se guarda y se publica. Sin los argumentos no se sabe con que
    cumulo se etiqueto."""
    llamadas = []
    real = pm.derivar_distance_class

    def espia(*a, **k):
        args = list(a) + [k[n] for n in ("final_dist_km", "pc_dist_km", "inner_km", "desde_cluster")[len(a):]]
        r = real(*a, **k)
        llamadas.append([None if x is None else float(x) for x in args[:3]] + [bool(args[3]), r])
        return r

    with patch.object(pm, FLAG, bool(cumulo)), patch.object(pm, "derivar_distance_class", espia):
        rec = P.procesar_brazo(l1b, geo, volcan, latlon, feats, lector)
    return rec, sorted({c[3] for c in llamadas}), llamadas


def cumulo_de_la_etiqueta(rec, llamadas):
    """Distancia del cumulo con que se etiqueto (ultima llamada a derivar) contra la del cumulo guardado
    y publicado. `distinto` es True si difieren en mas de 1 m: el caso de la rama del Test 1."""
    if rec is None or not llamadas:
        return None
    vio = llamadas[-1][1]
    guardado = (rec.get("primary_cluster") or {}).get("centroid_dist_km")
    distinto = (vio is None) != (guardado is None) or (vio is not None and abs(vio - guardado) > 1e-3)
    return {"vio_km": vio, "guardado_km": guardado, "distinto": bool(distinto)}


# ------------------------------------------------------------------ el ruido
def angulo_ruido(clave):
    """Direccion (grados desde el norte, sentido horario) uniforme y determinista por granulo."""
    h = hashlib.sha1((SAL_RUIDO + clave).encode()).hexdigest()
    return 360.0 * int(h[:12], 16) / float(16 ** 12)


def trasladar(lat, lon, km, angulo):
    """Traslacion rigida de toda la grilla: `km` hacia el rumbo `angulo`. Copia, no toca la entrada."""
    dn = km * math.cos(math.radians(angulo))
    de = km * math.sin(math.radians(angulo))
    lat = np.asarray(lat, dtype=np.float64)
    lat2 = lat + dn / 111.32
    lon2 = np.asarray(lon, dtype=np.float64) + de / (111.32 * np.cos(np.radians(lat)))
    return lat2.astype(np.float32), lon2.astype(np.float32)


def resumir(rec):
    s = P.resumir(rec)
    if s is None:
        return None
    pc = rec.get("primary_cluster") or {}
    s.update({k: rec.get(k) for k in EXTRA})
    s["pc_n_pixels"] = pc.get("n_pixels")
    return s


# ------------------------------------------------------------------ un granulo
def medir_granulo(l1b, geo, volcan, latlon_m, datos, vent, clave, feats=None, con_cprima=False):
    """Los seis brazos (y C' si se pide) sobre el mismo L1B. `datos`: lo que devolvio read_modis_l1b;
    cada brazo recibe una copia. Devuelve un dict listo para el JSON del job."""
    lector = lambda _p: P._copia(datos)  # noqa: E731
    desp = P.desplazamiento_crater(datos["lat"], datos["lon"], latlon_m[0], latlon_m[1], vent)
    ang = angulo_ruido(clave)
    lat_r, lon_r = trasladar(datos["lat"], datos["lon"], desp["km"], ang)
    aplicado = P.desplazamiento_crater(lat_r, lon_r, datos["lat"], datos["lon"], vent)
    pos = {"interp": None, "mxd03": latlon_m, "ruido": (lat_r, lon_r)}
    recs, vistos, llamadas = {}, {}, {}
    for b in BRAZOS:
        recs[b], vistos[b], llamadas[b] = procesar(l1b, geo, volcan, pos[POSICION[b]], feats, lector, CUMULO[b])
    inner = volcan.get("inner_radius_km")
    pubs = P.publica([recs[b] for b in BRAZOS], inner)
    fila = {"desplazamiento": desp, "ruido": {"km_objetivo": desp["km"], "angulo_grados": round(ang, 3),
                                              "km_aplicado": aplicado["km"]},
            "brazos": {b: resumir(recs[b]) for b in BRAZOS}, "pub": dict(zip(BRAZOS, pubs)),
            "flag_visto": vistos, "derivar": llamadas,
            "cumulo_etiqueta": {b: cumulo_de_la_etiqueta(recs[b], llamadas[b]) for b in BRAZOS},
            "cprima_igual": None}
    if con_cprima:
        rcp, _, _ = procesar(l1b, geo, volcan, (datos["lat"].copy(), datos["lon"].copy()), feats, lector, False)
        fila["cprima_igual"] = P.registros_iguales(recs["C"], rcp)
    return fila


# ------------------------------------------------------------------ E/S (solo en el runner)
def procedencia():
    """Commit y ref con que corrio el job (verificador v2, A108): el despacho partido en dos puede caer
    sobre dos pipelines, y el evaluador tiene que poder verlo. En Actions, GITHUB_SHA y GITHUB_REF; fuera,
    el HEAD del repo."""
    commit = os.environ.get("GITHUB_SHA", "").strip()
    ref = os.environ.get("GITHUB_REF", "").strip()
    if not commit:
        import subprocess
        commit = subprocess.run(["git", "-C", str(RAIZ), "rev-parse", "HEAD"], capture_output=True,
                                text=True).stdout.strip()
        ref = ref or "local"
    return {"commit": commit or None, "ref": ref or None}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--job", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--poblacion", default=str(DIR_117 / "poblacion.json"))
    ap.add_argument("--presupuesto-min", type=float, default=70.0)
    args = ap.parse_args()
    if not os.environ.get("EARTHDATA_TOKEN", "").strip():
        sys.exit("EARTHDATA_TOKEN vacio: el probe no usa usuario y clave (A71).")
    import run_pipeline as rp     # el mismo dict de volcan que produccion (overrides del perfil incluidos)
    from pipeline.fetch import auth
    auth()
    t0 = time.time()
    pob = json.load(open(args.poblacion, encoding="utf-8"))
    job = pob["jobs"][args.job]
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
    estado = {"job": args.job, "volcan": vol, "inner_radius_km": inner, "completo": False, **procedencia(),
              "brazos": list(BRAZOS), "granulos": []}
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
                con_cp = n_cprima < N_CPRIMA
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
        print(json.dumps({"clave": clave, "estado": fila.get("estado"), "pub": fila.get("pub"),
                          "cprima_igual": fila.get("cprima_igual")}, ensure_ascii=False), flush=True)
    estado["completo"] = True
    P.guardar(destino, estado)
    n_ok = sum(1 for f in estado["granulos"] if f.get("estado") == "ok")
    print("%s: %d de %d granulos medidos en %.1f min" % (args.job, n_ok, len(job["granulos"]),
                                                         (time.time() - t0) / 60.0))


if __name__ == "__main__":
    main()
