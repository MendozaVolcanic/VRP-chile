# -*- coding: utf-8 -*-
"""S162, A/B de MxD03 sobre K (tarea 1.30, D-19). Pre-registro sellado: experiments/_s159/mxd03_prereg/PREREGISTRO_MXD03.md
(v2 mas el sello D-48 y su adenda). Solo lectura: no escribe en data/, no commitea, no hace push; borra cada HDF salvo los
que el control 4 necesita re-correr en otro codigo_sha (se borran en el paso siguiente del job).

POR QUE. El pipeline ubica cada pixel MODIS interpolando la grilla de 5 km del L1B (`_interp_geo`) y no usa el MxD03 que
baja; el frente M midio que asi el pixel del crater queda corrido 1 a 5 km hacia el sensor. La pregunta sellada es si
ubicarlo con MxD03 DANA la replica (pierde una protegida o publica mas donde MIROVA callo). Este arnes corre, sobre el
MISMO L1B leido una sola vez, la funcion de produccion (calculate_vrp + store.append_record + predicado del tablero con
node, A97) en los brazos del §3:
  K          produccion del tag (lat/lon de `_interp_geo`);
  K2         K otra vez en el mismo proceso: control de identidad (tiene que dar K exacto, §8 control 3);
  X          lat/lon por pixel de MxD03 (lo unico que cambia; angulos, bandas y perfil iguales);
  R00 a R19  solo en records con cenit <= 35 grados (record de K en data/, §3): la grilla de `_interp_geo` trasladada en
             bloque el mismo modulo en km que el corrimiento de X en el pixel del crater, en 20 rumbos cada 18 grados con
             fase al azar fija por granulo (sal "s159-mxd03-r", la del pre-registro);
  X_fondo    solo donde la publicacion de K y X difiere: posiciones de K salvo la distancia al centro del volcan, que arma
             el anillo de fondo de 5 a 25 km (`dist`, process_modis.py:560 y :582), con MxD03;
  X_det      el complemento: MxD03 en todo salvo esa distancia, con `_interp_geo`.
  XF_id/XD_id controles de identidad de la atribucion: X_fondo con la misma grilla de K tiene que dar K, y X_det con la
             misma grilla de X tiene que dar X (§3, «controles de identidad que tienen que dar exactos»).
Como X_fondo/X_det cambian SOLO el arreglo `dist` (no hay otro punto de corte sin tocar pipeline/, A45), tambien cambia
con el el `dist_km` informativo de cada pixel anomalo (:1143) y su diagnostico (:1273): queda declarado en el README.

Las dos preguntas del instrumento:
1. Si X no moviera nada (parche muerto), ¿se veria? Si: se guarda el hash de la grilla de cada brazo (control 8) y el
   corrimiento en el crater; X con la misma grilla que K daria hash igual y corrimiento 0. Si R no moviera la grilla, el
   modulo aplicado (medido en el mismo pixel) daria 0 contra el pedido (control 2).
2. Si un brazo se cayera, ¿se veria distinto de «no publica»? Si: un record None se guarda como None con su motivo, una
   excepcion como estado "error" (el job sale 2), y un granulo no bajado como "no_bajado" con sus records.

Uso (Linux con pyhdf): EARTHDATA_TOKEN=... VRP_PROFILE=mirova_equivalent \
    python experiments/_s162_mxd03/probe_mxd03_ab.py --parte 0 --out out [--poblacion poblacion.json]
"""
import argparse
import copy
import hashlib
import importlib.util
import json
import math
import os
import sys
import time
import traceback
from pathlib import Path
from unittest.mock import patch

import numpy as np

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")


def _cargar(nombre, ruta):
    """Importa un modulo de experimento por ruta (los de 1.17, 1.21 y 1.23, sin copiarlos)."""
    spec = importlib.util.spec_from_file_location(nombre, RAIZ / ruta)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[nombre] = mod
    spec.loader.exec_module(mod)
    return mod


sys.path.insert(0, str(RAIZ / "experiments/_s151_mxd03_etiquetas"))
sys.path.insert(0, str(RAIZ / "experiments/_s151_mxd03_cumulo_121"))
P = _cargar("probe_etiquetas", "experiments/_s151_mxd03_etiquetas/probe_etiquetas.py")   # brazo, publica, E/S
Q = _cargar("probe_cumulo", "experiments/_s151_mxd03_cumulo_121/probe_cumulo.py")        # trasladar, resumir
S = _cargar("probe_sola", "experiments/_s151_mxd03_sola_123/probe_sola.py")              # nulo en km, pico
P151 = _cargar("probe151", "experiments/_s151_probe_mod03/probe_mod03.py")              # control 1 (geometria)

from pipeline import process_modis as pm  # noqa: E402
from pipeline.geo_utils import get_detection_anchor  # noqa: E402

_HAV_REAL = pm.haversine_km   # fijada al importar: FondoCruzado se crea DENTRO del parche y no puede leerla de pm

K_NULOS = 20
SAL = "s159-mxd03-r"                          # §3 del pre-registro
NULOS = tuple("R%02d" % k for k in range(K_NULOS))
CAMPOS_DIAG = ("t_bg_k", "t_max_k", "diag_n_first_pass_pixels", "diag_n_first_pass_summit",
               "diag_n_second_pass_recapture", "diag_sigma_bg_k", "diag_n_bg_anillo", "sensor_zenith_deg",
               "sensor_azimuth_deg", "geo_class")
CONTROL_S151 = "MYD021KM.A2026073.0705"       # §8 control 1: Lascar, hacia el sensor 2,581 km (S151 y M)
TOL_VRP = 0.001
CENIT_R = 35.0                                # §3: los nulos solo con cenit <= 35 grados (lo fija poblacion.json)
BRAZOS_BASE = (("K", "interp"), ("K2", "interp"), ("X", "mxd03"))                               # §8 control 4: primary_cluster.vrp_mw a 0,001 MW


# ------------------------------------------------------------------ piezas puras (probadas sin HDF)
def rumbos(clave, k=K_NULOS):
    """k rumbos equiespaciados con fase al azar determinista por granulo (S.rumbos de la 1.23 con la sal de este
    pre-registro: la funcion de 1.23 fija su propia sal como constante de modulo)."""
    h = hashlib.sha1((SAL + clave).encode()).hexdigest()
    u = int(h[:12], 16) / float(16 ** 12)
    return [round(360.0 * ((u + n / k) % 1.0), 6) for n in range(k)]


def hash_grilla(lat, lon):
    a = np.ascontiguousarray(np.asarray(lat, dtype=np.float32))
    b = np.ascontiguousarray(np.asarray(lon, dtype=np.float32))
    return hashlib.sha1(a.tobytes() + b.tobytes()).hexdigest()[:16]


def resumen(rec):
    s = Q.resumir(rec)
    if s is None:
        return None
    s.update({k: rec.get(k) for k in CAMPOS_DIAG})
    return s


def difiere_de_guardado(fila_pob, res_k, pub_k):
    """Control 4: el K del arnes contra el record de data/ (publicacion y pc.vrp_mw a 0,001 MW)."""
    if pub_k != fila_pob["pub_guardada"]:
        return True
    a = None if res_k is None else res_k.get("pc_vrp")
    b = fila_pob["pc_vrp_guardada"]
    if (a is None) != (b is None):
        return True
    return a is not None and abs(a - b) > TOL_VRP


def decide(fila_pob):
    """Records donde el control 4 no admite tolerancia (§8 punto 4): alertas, negativos que K publica, expuestas."""
    return (fila_pob["lab"] in ("protegida", "bajo1") or fila_pob["expuesta"]
            or (fila_pob["lab"] == "neg_limpio" and fila_pob["pub_guardada"]))


class FondoCruzado:
    """Reemplaza SOLO la primera llamada a haversine_km de calculate_vrp (la distancia al centro del volcan, `dist`,
    process_modis.py:560, que arma el anillo de fondo en :582) por la misma distancia calculada sobre otra grilla.
    Reconoce la llamada por identidad del arreglo lat que entrego el lector; cuenta cuantas reemplazo (tiene que ser 1)."""

    def __init__(self, lat_obj, lat_alt, lon_alt):
        self.lat_obj, self.lat_alt, self.lon_alt = lat_obj, lat_alt, lon_alt
        self.reemplazos = 0
        self.llamadas = 0
        self.real = _HAV_REAL

    def __call__(self, lat1, lon1, lat2, lon2):
        self.llamadas += 1
        if self.llamadas == 1 and lat2 is self.lat_obj:
            self.reemplazos += 1
            return self.real(lat1, lon1, self.lat_alt, self.lon_alt)
        return self.real(lat1, lon1, lat2, lon2)


def brazo(l1b, geo, volcan, feats, datos, latlon=None, fondo=None):
    """Un brazo de produccion. `latlon` reemplaza la lat/lon del lector; `fondo=(lat, lon)` reemplaza la grilla de la
    distancia al centro (X_fondo / X_det). Devuelve (record, reemplazos_de_fondo)."""
    estado = {}

    def lector(_p):
        d = P._copia(datos)
        if latlon is not None:
            d["lat"], d["lon"] = np.asarray(latlon[0], np.float32), np.asarray(latlon[1], np.float32)
        estado["lat_obj"] = d["lat"]
        return d

    if fondo is None:
        return P.procesar_brazo(l1b, geo, volcan, None, feats, lector), None

    class _Envoltorio:
        def __init__(self):
            self.fc = None

        def __call__(self, *a):
            if self.fc is None:
                # mismo dtype que la lat/lon que ve calculate_vrp: si no, XF_id no reproduciria K bit a bit
                t = estado["lat_obj"].dtype
                self.fc = FondoCruzado(estado["lat_obj"], np.asarray(fondo[0], t), np.asarray(fondo[1], t))
            return self.fc(*a)

    env = _Envoltorio()
    with patch.object(pm, "haversine_km", env):
        rec = P.procesar_brazo(l1b, geo, volcan, None, feats, lector)
    return rec, (None if env.fc is None else env.fc.reemplazos)


def medir_record(l1b, geo, volcan, feats, datos, latlon_m, fila_pob, clave):
    """Todos los brazos de un record (volcan) sobre un granulo ya leido."""
    lat, lon = datos["lat"], datos["lon"]
    vent = get_detection_anchor(volcan)
    inner = volcan.get("inner_radius_km")
    out = {"vol": fila_pob["vol"], "dt": fila_pob["dt"], "sensor": fila_pob["sensor"], "clave": clave,
           "lab": fila_pob["lab"], "z": fila_pob["z"], "tramo": fila_pob["tramo"], "lado": fila_pob["lado"],
           "r_nulos": fila_pob["r_nulos"], "inner": inner, "vent": [vent[0], vent[1]]}
    desp = P.desplazamiento_crater(lat, lon, latlon_m[0], latlon_m[1], vent)
    out["desplazamiento"] = desp
    recs = {b: brazo(l1b, geo, volcan, feats, datos, latlon=(latlon_m if g == "mxd03" else None))[0]
            for b, g in BRAZOS_BASE}
    posiciones = {"C": (lat, lon), "M": latlon_m}
    hashes = {"K": hash_grilla(lat, lon), "X": hash_grilla(*latlon_m)}
    nulos = []
    if fila_pob["r_nulos"]:
        for n, ang in zip(range(K_NULOS), rumbos(clave)):
            dn, de = S.vector_nulo(desp["km"], ang)
            lat_r, lon_r = S.trasladar_ne(lat, lon, dn, de)
            ap = S.medido_en(lat_r, lon_r, lat, lon, desp["linea"], desp["frame"])
            b = NULOS[n]
            recs[b] = brazo(l1b, geo, volcan, feats, datos, latlon=(lat_r, lon_r))[0]
            posiciones[b] = (lat_r, lon_r)
            hashes[b] = hash_grilla(lat_r, lon_r)
            nulos.append({"k": n, "angulo_grados": ang, "km_pedido": round(desp["km"], 4), "km_aplicado": ap["km"]})
    orden = list(recs)
    pubs = dict(zip(orden, P.publica([recs[b] for b in orden], inner)))
    out["nulos"] = nulos
    out["hash_grilla"] = hashes
    out["brazos"] = {b: resumen(recs[b]) for b in orden}
    out["pub"] = pubs
    out["k2_igual"] = P.registros_iguales(recs["K"], recs["K2"])
    out["pico"] = S.pico_por_indice(datos, posiciones, latlon_m[0], latlon_m[1], vent, float(inner or 5.0))
    out["k_difiere_de_guardado"] = difiere_de_guardado(fila_pob, out["brazos"]["K"], pubs["K"])
    out["decide"] = decide(fila_pob)
    if pubs["K"] != pubs["X"]:
        extra = {}
        for nombre, latlon, fondo in (("X_fondo", None, latlon_m), ("X_det", latlon_m, (lat, lon)),
                                      ("XF_id", None, (lat, lon)), ("XD_id", latlon_m, latlon_m)):
            r, n_reemp = brazo(l1b, geo, volcan, feats, datos, latlon=latlon, fondo=fondo)
            extra[nombre] = (r, n_reemp)
        o2 = list(extra)
        p2 = P.publica([extra[b][0] for b in o2], inner)
        out["atribucion"] = {b: {"rec": resumen(extra[b][0]), "pub": p, "reemplazos_fondo": extra[b][1]}
                             for b, p in zip(o2, p2)}
        out["atribucion"]["XF_id_igual_K"] = P.registros_iguales(extra["XF_id"][0], recs["K"])
        out["atribucion"]["XD_id_igual_X"] = P.registros_iguales(extra["XD_id"][0], recs["X"])
    return out


# ------------------------------------------------------------------ E/S (solo en el runner)
def bajar(short, patron, dest):
    """Version 6.1 (la poblacion es 100 % estandar); reintento con espera ante CMR caido (run 39679594869 de M)."""
    for intento in range(4):
        try:
            return P._bajar(short, patron, dest)
        except Exception as e:  # noqa: BLE001
            print(f"  CMR/descarga fallo intento {intento} {short}.{patron}: {e!r}"[:300], flush=True)
            time.sleep(20 * (intento + 1))
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parte", type=int, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--poblacion", default=str(AQUI / "poblacion.json"))
    ap.add_argument("--solo", default="", help="claves de granulo separadas por coma (humo)")
    args = ap.parse_args()
    if not os.environ.get("EARTHDATA_TOKEN", "").strip():
        sys.exit("EARTHDATA_TOKEN vacio: el probe no usa usuario y clave (A71).")
    import run_pipeline as rp   # el mismo dict de volcan que produccion (overrides del perfil incluidos)
    from pipeline.fetch import auth
    auth()
    pob = json.load(open(args.poblacion, encoding="utf-8"))
    por_clave = {g["clave"]: g for g in pob["granulos"]}
    claves = pob["partes"][args.parte]
    if args.solo:   # humo: claves de cualquier parte (la salida se rotula con --parte igual)
        claves = [c for c in sorted(por_clave) if c in set(args.solo.split(","))]
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    hdf, retenidos = out / "hdf", out / "retenidos"
    salida = open(out / f"ab_parte{args.parte:02d}.jsonl", "w", encoding="utf-8")
    cab = {"tipo": "cabecera", "parte": args.parte, "n_granulos": len(claves), **Q.procedencia(),
           "poblacion_checkout": pob["checkout"], "referencia": pob["referencia"], "sal": SAL, "k_nulos": K_NULOS,
           "flag_ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER": bool(pm.ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER),
           "flag_ENABLE_MODIS_B22_PRIMARY": bool(pm.ENABLE_MODIS_B22_PRIMARY)}
    salida.write(json.dumps(cab, ensure_ascii=False) + "\n")
    errores, t0 = 0, time.time()
    vol_cache = {}
    for clave in claves:
        g = por_clave[clave]
        prod, patron = clave.split(".", 1)
        l1b = geo = None
        retener = False
        try:
            l1b = bajar(prod, patron, hdf)
            geo = bajar(prod.replace("021KM", "03"), patron, hdf)
            if l1b is None or geo is None:
                for f in g["records"]:
                    salida.write(json.dumps({"tipo": "record", "clave": clave, "vol": f["vol"], "dt": f["dt"],
                                             "estado": "no_bajado",
                                             "falta": "L1B" if l1b is None else "MxD03"}) + "\n")
                    errores += 1
                continue
            datos = pm.read_modis_l1b(l1b)
            lat_m, lon_m = P._leer_mxd03(geo)
            if lat_m.shape != datos["lat"].shape:
                raise ValueError(f"MxD03 {lat_m.shape} y L1B {datos['lat'].shape} no calzan")
            n_fill = int(np.isnan(lat_m).sum())
            # control 1 (§8): instrumento de geometria de S151, el mismo nucleo `comparar` que uso M
            glat, glon, saz, szen = P151._leer_geo(geo)
            latc, lonc, _rad = P151._leer_l1b(l1b)
            ilat = pm._interp_geo(latc, glat.shape[0], glat.shape[1]).astype(np.float64)
            ilon = pm._interp_geo(lonc, glat.shape[0], glat.shape[1]).astype(np.float64)
            for f in g["records"]:
                fila = {"tipo": "record", "clave": clave, "l1b": Path(l1b).name, "geo": Path(geo).name,
                        "n_fill_mxd03": n_fill}
                try:
                    if f["vol"] not in vol_cache:
                        v = rp.load_volcanoes(f["vol"])[0]
                        if v.get("inner_radius_km") != f["inner"] and f["inner"] is not None:
                            raise ValueError(f"inner de volcanoes.yaml {v.get('inner_radius_km')} distinto del "
                                             f"del frontend {f['inner']}")
                        vol_cache[f["vol"]] = v
                    volcan = vol_cache[f["vol"]]
                    fila.update(medir_record(l1b, geo, volcan, rp.VOLCANIC_FEATURES.get(volcan["name"]), datos,
                                             (lat_m, lon_m), f, clave))
                    vent = get_detection_anchor(volcan)
                    nulo = P151.comparar(ilat, ilon, latc, lonc, saz, szen, pm._interp_geo, None, vent=vent)
                    fila["nulo_geo_crater_km"] = round(math.hypot(nulo["obs_barrido_km"], nulo["obs_traza_km"]), 6)
                    if clave == CONTROL_S151 and f["vol"] == "Lascar":
                        c = P151.comparar(glat, glon, latc, lonc, saz, szen, pm._interp_geo, None, vent=vent)
                        fila["control_s151"] = {k: c.get(k) for k in ("obs_hacia_sensor_km", "obs_traza_km",
                                                                      "obs_barrido_km")}
                    fila["estado"] = "ok"
                    if fila["decide"] and fila["k_difiere_de_guardado"]:
                        fila["retenido_para_sha"] = f["codigo_sha"]
                        retener = True
                except Exception as e:  # noqa: BLE001
                    fila.update({"vol": f["vol"], "dt": f["dt"], "estado": "error",
                                 "error": f"{type(e).__name__}: {e}", "traza": traceback.format_exc()[-1500:]})
                    errores += 1
                salida.write(json.dumps(fila, ensure_ascii=False, default=str) + "\n")
                salida.flush()
                print(json.dumps({"clave": clave, "vol": fila.get("vol"), "estado": fila.get("estado"),
                                  "pub": fila.get("pub", {}) and {b: fila["pub"].get(b) for b in ("K", "X")},
                                  "nulos_publican": sum(fila.get("pub", {}).get(b, 0) for b in NULOS),
                                  "k2": fila.get("k2_igual"), "k_vs_data": fila.get("k_difiere_de_guardado")},
                                 ensure_ascii=False), flush=True)
        except Exception as e:  # noqa: BLE001
            for f in g["records"]:
                salida.write(json.dumps({"tipo": "record", "clave": clave, "vol": f["vol"], "dt": f["dt"],
                                         "estado": "error", "error": f"{type(e).__name__}: {e}"}) + "\n")
                errores += 1
        finally:
            for p in (l1b, geo):
                if p is None:
                    continue
                if retener:
                    retenidos.mkdir(parents=True, exist_ok=True)
                    Path(p).replace(retenidos / Path(p).name)
                else:
                    Path(p).unlink(missing_ok=True)
    salida.write(json.dumps({"tipo": "pie", "errores": errores, "minutos": round((time.time() - t0) / 60, 1)}) + "\n")
    salida.close()
    print(f"parte {args.parte}: {len(claves)} granulos, {errores} records con error, "
          f"{(time.time() - t0) / 60:.1f} min")
    sys.exit(2 if errores else 0)


if __name__ == "__main__":
    main()
