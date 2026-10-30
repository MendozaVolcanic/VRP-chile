# -*- coding: utf-8 -*-
"""S168 MOD-D fase 4, arnés del A/B de la vía «código MIROVA» de MODIS contra K, con los tres brazos de posición.
Pre-registro SELLADO: experiments/_s166_modd_f4/PREREGISTRO_MODD_F4.md (tag s168-modd-f4-sellado), §2, §6, §8 y §11.
Sólo lectura: no escribe en data/, no commitea, no hace push; cada HDF se borra al terminar su gránulo.

POR QUÉ. La fase 3 metió en pipeline/ el código de MIROVA llevado a MODIS y probó que da lo mismo que el port del censo
sobre las grillas que el censo armó, pero no el camino de punta a punta (pyhdf no corre en Windows y el censo no guardó
los gránulos). Este arnés corre, sobre el MISMO L1B y el MISMO MxD03 que usó el censo (pedidos por nombre), lo que
correría en producción:
  K          process_modis.calculate_vrp con el perfil mirova_equivalent intacto (flag de la vía apagado), seguido de
             store.append_record en un directorio temporal (probe_etiquetas.procesar_brazo, el brazo de MOD-B y MOD-D,
             sin copiarlo; el L1B se lee una vez y K recibe una copia).
  V          la misma llamada con process_modis.ENABLE_MODIS_CODIGO_MIROVA = True EN MEMORIA y nada más (los tres flags
             del MxD03 de #920 siguen apagados: la vía lee su propio MxD03). V lee el HDF y el MxD03 por su cuenta, con
             las funciones de producción: es justo el camino que la fase 3 no pudo medir.
  V-cercano  el record de V con la distancia del alertado más cercano al cráter;
  V-pico     el record de V con la distancia del alertado de mayor radiancia MIR.
             Las dos variantes salen de evaluar_f4.variante_posicion (sin copiarla) y cada una pasa por
             store.append_record en su propio directorio temporal, como en producción.
Para las tres distancias se envuelven, SÓLO PARA LEER (A75: llaman a la original y copian entradas y salidas), tres
funciones de pipeline/mirova_v750_codigo.py: calcular_vrp_granulo (si corrió, si devolvió None, y el cenit del sensor
en el píxel MxD03 más cercano al cráter), procesar_grilla (grilla MIR y TIR, caja, posición fraccionaria del cráter,
inner y el record que devolvió) y detectar_mirova (la máscara de alertadas). Con eso, evaluar_f4.distancias (sin
copiarla) mide las tres distancias desde el cráter con _cumulo_del_mas_radiante de la vía.

Por pasada, además: la grilla en npz (formato abajo, para identidad_f4.py), k_difiere_de_guardado contra el record de
data/mirova_equivalent/ del commit (publicación con el predicado del tablero y pc.vrp_mw a 0,001 MW, la regla de MOD-B,
probe_mxd03_ab.difiere_de_guardado) y, si difiere, la re-corrida de K en el codigo_sha del record guardado con
experiments/_s162_mxd03/k_en_sha.py (el mismo de MOD-B; el árbol de ese commit se extrae con git archive CON RUTA:
pipeline, scripts y volcanoes.yaml), y pub_runner con la publicación del predicado de frontend/index.html corrido con
node en el runner (A97) sobre los records COMPLETOS (el evaluador lo corre sobre el slim: si el slim perdiera algo que
el predicado lee, el control §8.1 lo vería).

FORMATO DE LA GRILLA (grillas/grilla_<vol>_<AAAAMMDDHHMM>.npz, np.savez_compressed): las entradas de procesar_grilla
tal como las recibió, para que identidad_f4.py pueda re-correr la vía sobre la grilla del runner bit a bit y comparar
con la del censo: mir y tir (float64, 51 x 51, fila 0 = norte), box (float64), pos_crater (2,), mascara (bool, las
alertadas que devolvió detectar_mirova), vrp_mw (el vrp_mw del record de V antes del almacén), dayflag, sunglint,
inner_km, epsg, ul_x, ul_y, paso, n. Si la vía no llegó a procesar_grilla (volcán fuera del gránulo o no corrió), no
hay npz y la fila trae grilla_npz = None.

MOTIVO Y MARCA (contrato del §11, evaluar_f4.evaluable): v_marca es via_codigo_mirova del record de V (True, o
sin_mxd03 / geo_distinta / sin_grilla si siguió K). motivo = "volcan_fuera_del_granulo" si calcular_vrp_granulo corrió
y devolvió None (con la grilla presente es el único camino: menos de 100 píxeles a 45 km o el más cercano al centro a
más de 5 km); "escena_invalida" si el record de la vía trae diag_codigo_mirova.motivo_vacio == "escena_invalida" (el
mismo criterio que el evaluador sellado de MOD-D); None en todo otro caso. Si V no dejó record y la vía nunca se llamó,
v_marca = "sin_record_ni_via": es falla, no «no publica».

Las dos preguntas del instrumento:
1. Si V no corriera la vía (flag mal parcheado), ¿se vería? Sí: v_marca no sería True y la captura vendría vacía; la
   pasada sale como falla y la cobertura queda en rojo. Si la captura no correspondiera al record (otra llamada, otra
   máscara), estado = "captura_incoherente" (falla), no una distancia inventada.
2. Si un brazo se cayera, ¿se vería distinto de «no publica»? Sí: una excepción es estado "error" con su traza, un
   gránulo no bajado es "no_bajado", y un record que el almacén descartó queda marcado en store_descarto.
Uso (Linux con pyhdf): EARTHDATA_TOKEN=... VRP_PROFILE=mirova_equivalent \
    python experiments/_s166_modd_f4/probe_f4.py --parte 0 --de 24 --out out [--humo] [--poblacion RUTA]
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import inspect
import io
import json
import os
import platform
import subprocess
import sys
import tarfile
import tempfile
import time
import traceback
from pathlib import Path
from unittest.mock import patch

import numpy as np

AQUI = Path(__file__).resolve().parent
# F4_RAIZ sólo la usa probar_probe_f4.py, que corre copias mutadas del arnés fuera del repositorio
RAIZ = Path(os.environ.get("F4_RAIZ") or AQUI.parents[1])
CARPETA = RAIZ / "experiments/_s166_modd_f4"
for _p in (RAIZ, RAIZ / "scripts", RAIZ / "experiments/_s162_mxd03", RAIZ / "experiments/_s151_mxd03_etiquetas", CARPETA):
    sys.path.insert(0, str(_p))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")

import probe_etiquetas as P  # noqa: E402  (procesar_brazo, argumentos de producción, publica, _copia)
import probe_mxd03_ab as PB  # noqa: E402  (difiere_de_guardado, resumen: la regla del control K = producción de MOD-B)
import evaluar_f4 as E  # noqa: E402  (distancias, variante_posicion, CAMPOS_MAG: el contrato sellado, sin copiar)
from pipeline import mirova_v750_codigo as MV  # noqa: E402
from pipeline import process_modis as pm  # noqa: E402
from pipeline import store  # noqa: E402
from pipeline.geo_utils import get_detection_anchor  # noqa: E402

POBLACION = CARPETA / "poblacion_f4.json"
HUMO = CARPETA / "humo_f4.txt"
K_EN_SHA = RAIZ / "experiments/_s162_mxd03/k_en_sha.py"
CAMPOS_PIXEL = ("lat", "lon", "vrp_mw", "bt_k")          # los mismos que probe_etiquetas.publica manda a node
EXTRAS_SLIM = ("final_hotspot_dist_km", "final_hotspot_source", "via_codigo_mirova", "datetime_utc", "granule",
               "n_anomalous_pixels", "sensor_zenith_deg", "product_version")
TOL_POS = 1e-9
FLAGS_APAGADOS = ("ENABLE_MODIS_CODIGO_MIROVA", "ENABLE_MODIS_GEO_MXD03", "ENABLE_MODIS_CRATER_SIN_DATO",
                  "ENABLE_MODIS_DIST_DESDE_CRATER")


def sha256_lf(ruta):
    """sha256 con fin de línea LF (el checkout de Windows puede traer CRLF; el del runner, LF)."""
    return hashlib.sha256(Path(ruta).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


# ------------------------------------------------------------------ captura de sólo lectura (A75)
class Captura:
    """Envuelve calcular_vrp_granulo, procesar_grilla y detectar_mirova de la vía. Cada envoltorio llama a la función
    original con los mismos argumentos y devuelve su salida SIN TOCARLA (el mismo objeto); sólo guarda copias."""

    def __init__(self):
        self.granulo, self.grilla, self.deteccion = [], [], []

    def __enter__(self):
        self._orig = {n: getattr(MV, n) for n in ("calcular_vrp_granulo", "procesar_grilla", "detectar_mirova")}
        self._parches = [patch.object(MV, "calcular_vrp_granulo", self._granulo),
                         patch.object(MV, "procesar_grilla", self._procesar),
                         patch.object(MV, "detectar_mirova", self._detectar)]
        for p in self._parches:
            p.start()
        return self

    def __exit__(self, *_a):
        for p in reversed(self._parches):
            p.stop()
        return False

    def _args(self, nombre, a, k):
        b = inspect.signature(self._orig[nombre]).bind(*a, **k)
        b.apply_defaults()
        return b.arguments

    def _granulo(self, *a, **k):
        x = self._args("calcular_vrp_granulo", a, k)
        info = {"nombre": x["nombre_volcan"], "vent": [float(x["vent_lat"]), float(x["vent_lon"])],
                "inner_km": x["inner_km"], "sensor": x["sensor"], "familia": x["familia"]}
        try:   # cenit del sensor en el píxel MxD03 más cercano al cráter (§11, campo z); informa, no decide
            d = MV._haversine(np.asarray(x["lat"], float), np.asarray(x["lon"], float), x["vent_lat"], x["vent_lon"])
            i = np.unravel_index(np.nanargmin(np.where(np.isfinite(d), d, np.inf)), d.shape)
            ang = x["angulos"] or {}
            info["crater_px"] = [int(i[0]), int(i[1])]
            info["crater_dist_km"] = float(d[i])
            info["z_crater"] = None if ang.get("sensor_zenith") is None else float(np.asarray(ang["sensor_zenith"])[i])
        except Exception as e:  # noqa: BLE001
            info["z_error"] = f"{type(e).__name__}: {e}"[:200]
        r = self._orig["calcular_vrp_granulo"](*a, **k)
        info["devolvio_none"] = r is None
        self.granulo.append(info)
        return r

    def _procesar(self, *a, **k):
        x = self._args("procesar_grilla", a, k)
        g = dict(x["grilla"])
        ent = {"mir": np.array(x["m13g"], dtype=float, copy=True), "tir": np.array(x["m15g"], dtype=float, copy=True),
               "box": np.array(x["box"], dtype=float, copy=True),
               "pos_crater": (float(x["pos_crater"][0]), float(x["pos_crater"][1])),
               "inner_km": x["inner_km"], "dayflag": x["dayflag"], "sunglint": float(x["sunglint"]),
               "familia": x["familia"], "sensor": x["sensor"], "grilla": g}
        r = self._orig["procesar_grilla"](*a, **k)
        self.grilla.append({"entrada": ent, "salida": copy.deepcopy(r)})
        return r

    def _detectar(self, *a, **k):
        r = self._orig["detectar_mirova"](*a, **k)
        mask = r[0] if isinstance(r, tuple) else r
        self.deteccion.append(np.array(mask, dtype=bool, copy=True))
        return r


def celdas_de(mascara):
    return sorted((int(f), int(c)) for f, c in zip(*np.nonzero(mascara)))


def leer_captura(cap):
    """Lo que la captura dice de la corrida de V: (diagnóstico, entrada de procesar_grilla o None, celdas, error).
    error no es None si la captura es incoherente (más de una llamada, o la máscara no es la del record)."""
    diag = {"n_granulo": len(cap.granulo), "n_grilla": len(cap.grilla), "n_deteccion": len(cap.deteccion)}
    if cap.granulo:
        diag.update({k: cap.granulo[-1].get(k) for k in ("crater_px", "crater_dist_km", "z_crater", "devolvio_none",
                                                         "z_error")})
    if len(cap.granulo) > 1 or len(cap.grilla) > 1 or len(cap.deteccion) > 1:
        return diag, None, None, "más de una llamada a la vía en una pasada"
    if not cap.grilla:
        return diag, None, None, None
    if len(cap.deteccion) != 1:
        return diag, None, None, "procesar_grilla corrió sin detectar_mirova"
    ent, sal = cap.grilla[0]["entrada"], cap.grilla[0]["salida"]
    celdas = celdas_de(cap.deteccion[0])
    del_record = sorted((int(p["fila"]), int(p["col"])) for p in (sal.get("anomaly_pixels") or []))
    if celdas != del_record:
        return diag, ent, celdas, "la máscara capturada no es la de los anomaly_pixels del record"
    return diag, ent, celdas, None


def tres_distancias(ent, celdas):
    """§2: las tres distancias desde el cráter, en km sin redondear, con evaluar_f4.distancias y el
    _cumulo_del_mas_radiante de la vía (sin copiarlos). None si no hay alertadas."""
    if not celdas:
        return None
    rad = [float(ent["mir"][f, c]) for f, c in celdas]
    paso_km = float(ent["grilla"].get("paso", MV.PASO_MODIS_M)) / 1000.0
    return E.distancias(celdas, rad, ent["pos_crater"], paso_km, MV._cumulo_del_mas_radiante)


def guardar_npz(ent, celdas, vrp_mw, ruta):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    g = ent["grilla"]
    mascara = np.zeros(ent["mir"].shape, bool)
    for f, c in celdas or []:
        mascara[f, c] = True
    np.savez_compressed(ruta, mir=ent["mir"], tir=ent["tir"], box=ent["box"], pos_crater=np.array(ent["pos_crater"]),
                        mascara=mascara, vrp_mw=np.float64(vrp_mw if vrp_mw is not None else np.nan),
                        dayflag=np.int64(ent["dayflag"]), sunglint=np.float64(ent["sunglint"]),
                        inner_km=np.float64(ent["inner_km"] if ent["inner_km"] is not None else np.nan),
                        epsg=np.int64(g["epsg"]), ul_x=np.float64(g["ul_x"]), ul_y=np.float64(g["ul_y"]),
                        paso=np.float64(g.get("paso", MV.PASO_MODIS_M)), n=np.int64(g.get("n", ent["mir"].shape[0])))
    return ruta


def nombre_npz(vol, dt):
    return f"grilla_{vol}_{dt.replace('-', '').replace(' ', '').replace(':', '')}.npz"


# ------------------------------------------------------------------ brazos
def correr_v(l1b, geo, volcan):
    """V: calculate_vrp con el flag de la vía encendido en memoria (y nada más), con la captura de sólo lectura. El
    HDF y el MxD03 los lee la vía con las funciones de producción (sin caché). Devuelve (record crudo, captura)."""
    cap = Captura()
    with patch.object(pm, "ENABLE_MODIS_CODIGO_MIROVA", True), cap:
        r = pm.calculate_vrp(Path(l1b), Path(geo), volcan["lat"], volcan["lon"], volcan["radius_km"],
                             **P.argumentos_calculate_vrp(volcan))
    return (copy.deepcopy(r) if r else None), cap


def correr_k(l1b, geo, volcan, feats, datos):
    """K: el brazo de producción de MOD-B y MOD-D (calculate_vrp + store.append_record), con el L1B ya leído."""
    return P.procesar_brazo(Path(l1b), Path(geo), volcan, None, feats, lambda _p: P._copia(datos))


def guardar(volcan, rec, feats):
    """store.append_record en un directorio temporal, con los argumentos de run_pipeline (probe_etiquetas). Devuelve
    el record guardado, o None si el almacén no escribió nada."""
    if rec is None:
        return None
    with tempfile.TemporaryDirectory() as tmp, patch.object(store, "DATA_DIR", Path(tmp)):
        store.append_record(volcan["name"], copy.deepcopy(rec), **P.argumentos_append_record(volcan, True, feats))
        recs = store.get_records(volcan["name"])
    return recs[-1] if recs else None


def slim(rec):
    """Los campos de banco_paridad.CAMPOS_JS (lo que el evaluador manda a node), con anomaly_pixels reducido a los
    campos que probe_etiquetas.publica manda a node, más campos de lectura que el predicado no ve."""
    import banco_paridad as bp
    if rec is None:
        return None
    s = {k: rec.get(k) for k in bp.CAMPOS_JS if k != "anomaly_pixels"}
    s["anomaly_pixels"] = [{k: p.get(k) for k in CAMPOS_PIXEL} for p in (rec.get("anomaly_pixels") or [])]
    s.update({k: rec.get(k) for k in EXTRAS_SLIM if k in rec})
    return s


def motivo_y_marca(rv_raw, diag):
    if rv_raw is None:
        if diag.get("n_granulo") and diag.get("devolvio_none"):
            return "volcan_fuera_del_granulo", True
        return None, "sin_record_ni_via"
    marca = rv_raw.get("via_codigo_mirova")
    if marca is True and (rv_raw.get("diag_codigo_mirova") or {}).get("motivo_vacio") == "escena_invalida":
        return "escena_invalida", True
    return None, marca if marca is not None else "sin_marca"


# ------------------------------------------------------------------ control K = producción (§8.1)
_DATA = {}


def registro_guardado(vol, dt, sensor, raiz=RAIZ):
    """El record de data/mirova_equivalent/ del commit para (dt, sensor), o None."""
    if vol not in _DATA:
        p = Path(raiz) / "data" / "mirova_equivalent" / f"{vol}.json"
        recs = json.load(open(p, encoding="utf-8"))["records"] if p.exists() else []
        _DATA[vol] = {(r.get("datetime_utc"), r.get("sensor")): r for r in recs}
    return _DATA[vol].get((dt, sensor))


def difiere(guardado, pub_guardado, rec, pub_rec):
    """La regla de MOD-B (probe_mxd03_ab.difiere_de_guardado, sin copiarla): publicación y pc.vrp_mw a 0,001 MW."""
    pcg = None if guardado is None else (guardado.get("primary_cluster") or {}).get("vrp_mw")
    return bool(PB.difiere_de_guardado({"pub_guardada": pub_guardado, "pc_vrp_guardada": pcg}, PB.resumen(rec),
                                       pub_rec))


def extraer_arbol(sha, destino, raiz=RAIZ):
    """pipeline, scripts y volcanoes.yaml del commit `sha`, con git archive CON RUTA (sin ruta extrae el repo entero,
    memoria S147). El checkout del job es superficial: se trae sólo ese commit."""
    d = Path(destino) / sha[:12]
    if d.exists():
        return d
    if subprocess.run(["git", "-C", str(raiz), "cat-file", "-e", f"{sha}^{{commit}}"], capture_output=True).returncode:
        subprocess.run(["git", "-C", str(raiz), "fetch", "--depth", "1", "origin", sha], check=True,
                       capture_output=True, text=True)
    t = subprocess.run(["git", "-C", str(raiz), "archive", "--format=tar", sha, "--", "pipeline", "scripts",
                        "volcanoes.yaml"], check=True, capture_output=True)
    d.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(t.stdout)) as tf:
        tf.extractall(d)
    return d


def recorrer_en_sha(sha, l1b, geo, vol, guardado, pub_de, inner, arboles):
    """K re-corrido con el código del commit que escribió el record guardado (k_en_sha.py de MOD-B, proceso aparte con
    ese árbol primero en sys.path). True si reproduce el record guardado con la regla de MOD-B."""
    if not sha:
        return {"estado": "sin_codigo_sha", "reproduce": False}
    try:
        d = extraer_arbol(sha, arboles)
        p = subprocess.run([sys.executable, str(K_EN_SHA), "--arbol", str(d), "--l1b", str(l1b), "--geo", str(geo),
                            "--vol", vol], capture_output=True, text=True, cwd=str(d))
        if p.returncode != 0:
            raise RuntimeError(p.stderr[-1500:])
        sal = json.loads(p.stdout.strip().splitlines()[-1])
        rec = sal["rec"]
        pub_g, pub_s = pub_de([guardado, rec], inner)
        rep = not difiere(guardado, pub_g, rec, pub_s)
        return {"estado": "reproduce" if rep else "no_reproduce", "reproduce": rep, "codigo_sha": sha,
                "firma_omitidos": sal.get("firma_omitidos"), "pub_sha": pub_s,
                "pc_vrp_sha": ((rec or {}).get("primary_cluster") or {}).get("vrp_mw")}
    except Exception as e:  # noqa: BLE001
        return {"estado": "error", "reproduce": False, "codigo_sha": sha, "error": f"{type(e).__name__}: {e}"[:1500]}


# ------------------------------------------------------------------ una pasada
def medir_pasada(pas, volcan, feats, l1b, geo, datos, outdir, arboles, otro_granulo=False, publica=None,
                 recorrer=None):
    """Una pasada (un volcán en un gránulo ya bajado y leído). Devuelve la fila del contrato del §11."""
    publica = publica or P.publica
    recorrer = recorrer or recorrer_en_sha
    t0 = time.time()
    inner = volcan.get("inner_radius_km")
    if pas.get("inner") is not None and inner != pas["inner"]:
        raise ValueError(f"inner de volcanoes.yaml {inner} distinto del de la población {pas['inner']}")
    sensor = pm._sensor_modis(Path(l1b).name)
    fila = {"tipo": "record", "vol": pas["vol"], "dt": pas["dt"], "sensor": sensor, "inner": inner,
            "clave": pas.get("clave"), "l1b_pedido": pas.get("l1b"), "geo_pedido": pas.get("geo"),
            "l1b_usado": Path(l1b).name, "geo_usado": Path(geo).name, "otro_granulo": bool(otro_granulo)}
    if pas.get("noche") is not None:
        fila["noche"] = pas["noche"]
    rk = correr_k(l1b, geo, volcan, feats, datos)
    rv, cap = correr_v(l1b, geo, volcan)
    diag, ent, celdas, err = leer_captura(cap)
    fila["captura"] = diag
    if err:
        fila.update({"estado": "captura_incoherente", "error": err})
        return fila
    motivo, marca = motivo_y_marca(rv, diag)
    vent = get_detection_anchor(volcan)
    dist = None
    if ent is not None:
        pos_ancla = MV.posicion_de(ent["grilla"], vent[0], vent[1])
        diag["pos_crater"] = list(ent["pos_crater"])
        diag["pos_crater_es_el_ancla"] = bool(abs(pos_ancla[0] - ent["pos_crater"][0]) <= TOL_POS and
                                               abs(pos_ancla[1] - ent["pos_crater"][1]) <= TOL_POS)
        dist = tres_distancias(ent, celdas)
        npz = guardar_npz(ent, celdas, None if rv is None else rv.get("vrp_mw"),
                          Path(outdir) / "grillas" / nombre_npz(pas["vol"], pas["dt"]))
        fila["grilla_npz"] = npz.relative_to(outdir).as_posix()
        fila["n_alertadas"] = len(celdas)
    else:
        fila["grilla_npz"] = None
    variantes = {"V": rv}
    for b in ("V-cercano", "V-pico"):
        variantes[b] = E.variante_posicion(rv, E.REGLA_DE[b], dist, inner) if (rv and dist) else copy.deepcopy(rv)
    guardados = {b: guardar(volcan, r, feats) for b, r in variantes.items()}
    guardado = registro_guardado(pas["vol"], pas["dt"], sensor)
    pubs = publica([rk, guardados["V"], guardados["V-cercano"], guardados["V-pico"], guardado], inner)
    pub_k = pubs[0]
    k_dif = difiere(guardado, pubs[4], rk, pub_k)
    fila.update({
        "estado": "ok", "motivo": motivo, "v_marca": marca, "dist": dist,
        "k_slim": slim(rk), "v_slim": slim(guardados["V"]), "vcerc_slim": slim(guardados["V-cercano"]),
        "vpico_slim": slim(guardados["V-pico"]),
        "store_descarto": {b: variantes[b] is not None and guardados[b] is None for b in variantes},
        "pub_runner": {"K": int(pub_k), "V": int(pubs[1]), "V-cercano": int(pubs[2]), "V-pico": int(pubs[3])},
        "k_difiere_de_guardado": k_dif,
        "k_guardado": None if guardado is None else {
            "pub": int(pubs[4]), "pc_vrp": (guardado.get("primary_cluster") or {}).get("vrp_mw"),
            "codigo_sha": (guardado.get("regimen") or {}).get("codigo_sha"), "granule": guardado.get("granule"),
            "product_version": guardado.get("product_version")},
    })
    z = diag.get("z_crater")
    if z is not None:
        fila.update({"z": z, "z_fuente": "mxd03_crater"})
    elif (rk or {}).get("sensor_zenith_deg") is not None:
        fila.update({"z": rk["sensor_zenith_deg"], "z_fuente": "record_k"})
    fila["z_k"] = (rk or {}).get("sensor_zenith_deg")
    if k_dif:
        sha = (fila["k_guardado"] or {}).get("codigo_sha")
        r = recorrer(sha, l1b, geo, pas["vol"], guardado, publica, inner, arboles)
        fila["k_sha"] = r
        fila["k_reproducida_en_su_sha"] = bool(r.get("reproduce"))
    else:
        fila["k_reproducida_en_su_sha"] = None
    fila["segundos"] = round(time.time() - t0, 2)
    return fila


# ------------------------------------------------------------------ descarga por nombre
# S168, P2-01 (experiments/_s169/audit_patrones/f2/INFORME.md y su verificador, m01b): el circuit-breaker de descarga de
# pipeline/fetch.py guarda los hosts caídos en el PROCESO, pensado para una corrida NRT de un día. En el arnés el proceso
# es la parte entera (53 o 54 gránulos): un solo ConnectTimeout dejaba el host marcado para siempre, cada gránulo
# siguiente chocaba con el breaker y gastaba 400 s de espera sin bajar nada, aunque el host ya hubiera vuelto. Por eso
# se resetea el breaker (pipeline.fetch.reset_transient_breakers, pública) antes de CADA intento de descarga, y la parte
# tiene un tope: TOPE_CAIDAS gránulos seguidos sin bajar por caída de host la terminan con filas no_bajado explícitas y
# código de salida SALIDA_TOPE (el job queda rojo y esa parte se repite). pipeline/fetch.py no se toca.
TOPE_CAIDAS = 3
SALIDA_TOPE = 3
MENSAJE_BREAKER = "download host(s) down this run"     # el RuntimeError de pipeline/fetch.download_granules


def es_error_del_breaker(e):
    """El salto inmediato del breaker de fetch.py (no gastó red): no se duerme por él."""
    return isinstance(e, RuntimeError) and str(e).startswith(MENSAJE_BREAKER)


def es_caida_de_host(e):
    """ConnectTimeout o ConnectionError de requests (el host no acepta la conexión, como fetch._CONNECT_ERRORS) o el
    salto del breaker. Un ReadTimeout u otro error no cuenta: se reintenta pero no acerca la parte al tope."""
    if es_error_del_breaker(e):
        return True
    try:
        from requests.exceptions import ConnectionError as RCE, ConnectTimeout as RCT
    except Exception:  # noqa: BLE001
        return False
    return isinstance(e, (RCT, RCE))


def bajar_por_nombre(nombre, dest, buscar=None, descargar=None, intentos=4, espera=20, reset=None, info=None):
    """El gránulo pedido por nombre (versión 6.1, o 6.1NRT si el nombre lo es). Si CMR ya no lo sirve, el vigente de
    la misma hora (6.1) y la pasada queda marcada otro_granulo. Devuelve (ruta, otro_granulo) o (None, None).
    reset: se llama antes de cada descarga (por omisión pipeline.fetch.reset_transient_breakers, P2-01). info: si se da,
    queda info["caida_host"] = True cuando el último intento fallido fue una caída de host (ver es_caida_de_host)."""
    if buscar is None or descargar is None:
        import earthaccess
        from pipeline.fetch import download_granules
        buscar = buscar or earthaccess.search_data
        descargar = descargar or download_granules
    if reset is None:
        from pipeline.fetch import reset_transient_breakers as reset
    info = {} if info is None else info
    info["caida_host"] = False
    short = nombre.split(".")[0]
    version = "6.1NRT" if ".NRT." in nombre else "6.1"
    patron = ".".join(nombre.split(".")[1:3])
    for intento in range(intentos):
        try:
            res = buscar(short_name=short, version=version, granule_name=nombre)
            if res:
                reset()
                ps = descargar(res[:1], Path(dest))
                if ps and Path(ps[0]).name == nombre:
                    info["caida_host"] = False
                    return Path(ps[0]), False
                for q in ps or []:
                    Path(q).unlink(missing_ok=True)
            res = buscar(short_name=short, version="6.1", granule_name=f"{short}.{patron}*")
            if not res:
                info["caida_host"] = False
                return None, None
            reset()
            ps = descargar(res[:1], Path(dest))
            if not ps:
                raise RuntimeError("descarga vacía del vigente")
            info["caida_host"] = False
            return Path(ps[0]), Path(ps[0]).name != nombre
        except Exception as e:  # noqa: BLE001
            info["caida_host"] = es_caida_de_host(e)
            print(f"  CMR/descarga fallo intento {intento} {nombre}: {e!r}"[:300], flush=True)
            if not es_error_del_breaker(e):
                time.sleep(espera * (intento + 1))
    return None, None


def fila_no_bajado(p, clave, falta, n_l1b, n_geo, motivo_arnes=None):
    """Contrato de evaluar_f4.cargar y evaluable: tipo record, vol, dt, clave y estado no_bajado (la cobertura la cuenta
    como falla del arnés, falla_arnes_no_bajado, no como pasada ausente)."""
    f = {"tipo": "record", "vol": p["vol"], "dt": p["dt"], "clave": clave, "estado": "no_bajado", "falta": falta,
         "l1b_pedido": n_l1b, "geo_pedido": n_geo}
    if motivo_arnes:
        f["motivo_arnes"] = motivo_arnes
    return f


def recorrer_granulos(grupos, salida, bajar, medir_archivo, tope=TOPE_CAIDAS):
    """Recorre los gránulos de la parte (cada par L1B + MxD03 una vez). bajar(nombre, info) -> (ruta, otro);
    medir_archivo(clave, ps, l1b, geo, otro_granulo, escribir) -> errores. Cada fila se escribe con flush. Con `tope`
    gránulos seguidos sin bajar por caída de host, las pasadas que quedan se escriben como no_bajado (falta
    "no_intentado", motivo_arnes "tope_caidas_host") y se corta. Devuelve (errores, terminada_por o None)."""
    def escribir(f):
        salida.write(json.dumps(f, ensure_ascii=False, default=float) + "\n")
        salida.flush()

    trabajos = []
    for clave, lista in grupos.items():
        por_archivo = {}
        for p in lista:
            por_archivo.setdefault((p.get("l1b"), p.get("geo")), []).append(p)
        trabajos += [(clave, n_l1b, n_geo, ps) for (n_l1b, n_geo), ps in por_archivo.items()]
    errores, seguidas, terminada = 0, 0, None
    for i, (clave, n_l1b, n_geo, ps) in enumerate(trabajos):
        l1b = geo = None
        try:
            if not n_l1b or not n_geo:
                for p in ps:
                    escribir({"tipo": "record", "vol": p["vol"], "dt": p["dt"], "clave": clave,
                              "estado": "sin_nombre_en_poblacion"})
                    errores += 1
                continue
            info = {}
            l1b, otro_l = bajar(n_l1b, info)
            otro_g = None
            if l1b is not None:          # sin L1B no se pide el MxD03 (P2-01: no gastar otra espera)
                info = {}
                geo, otro_g = bajar(n_geo, info)
            if l1b is None or geo is None:
                for p in ps:
                    escribir(fila_no_bajado(p, clave, "L1B" if l1b is None else "MxD03", n_l1b, n_geo))
                    errores += 1
                seguidas = seguidas + 1 if info.get("caida_host") else 0
                if seguidas >= tope:
                    terminada = "tope_caidas_host"
                    print(f"  TOPE: {seguidas} gránulos seguidos sin bajar por caída de host; la parte se corta",
                          flush=True)
                    for clave2, a, b, ps2 in trabajos[i + 1:]:
                        for p in ps2:
                            escribir(fila_no_bajado(p, clave2, "no_intentado", a, b, motivo_arnes=terminada))
                            errores += 1
                    break
                continue
            seguidas = 0
            errores += medir_archivo(clave, ps, l1b, geo, bool(otro_l or otro_g), escribir)
        except Exception as e:  # noqa: BLE001
            for p in ps:
                escribir({"tipo": "record", "vol": p["vol"], "dt": p["dt"], "clave": clave,
                          "estado": "error", "error": f"{type(e).__name__}: {e}"})
                errores += 1
        finally:
            for q in (l1b, geo):
                if q is not None:
                    Path(q).unlink(missing_ok=True)
    return errores, terminada


def codigo_salida(errores, terminada):
    """SALIDA_TOPE si la parte se cortó por el tope; 2 si hubo errores; 0 si no."""
    return SALIDA_TOPE if terminada else (2 if errores else 0)


# ------------------------------------------------------------------ población y partes
def clave_de(p):
    return p.get("clave") or ".".join(str(p.get("l1b") or "").split(".")[:3])


def pasadas_de_la_parte(pob, parte, de, humo=None):
    """Las pasadas de la parte, agrupadas por gránulo. Con `partes` en la población (24 listas de claves, armadas por
    poblacion_f4.py con la regla de MOD-B), se usan tal cual; si no, reparto determinista por índice. humo: lista de
    (vol, dt); todas tienen que estar en la población (si no, ValueError antes de bajar nada)."""
    pas = pob["pasadas"]
    if humo is not None:
        idx = {(p["vol"], p["dt"]): p for p in pas}
        faltan = [k for k in humo if k not in idx]
        if faltan:
            raise ValueError(f"pasadas del humo que no están en la población: {faltan}")
        sel = [idx[k] for k in humo]
    else:
        if pob.get("partes") is not None:
            if len(pob["partes"]) != de:
                raise ValueError(f"la población trae {len(pob['partes'])} partes y se pidió --de {de}")
            claves = set(pob["partes"][parte])
        else:
            todas = sorted({clave_de(p) for p in pas})
            claves = {c for i, c in enumerate(todas) if i % de == parte}
        sel = [p for p in pas if clave_de(p) in claves]
    grupos = {}
    for p in sorted(sel, key=lambda p: (clave_de(p), p["vol"], p["dt"])):
        grupos.setdefault(clave_de(p), []).append(p)
    return grupos


def leer_humo(ruta=HUMO):
    out = []
    for x in Path(ruta).read_text(encoding="utf-8").splitlines():
        x = x.split("#", 1)[0].strip()
        if x:
            vol, dt = (s.strip() for s in x.split("|"))
            out.append((vol, dt))
    return out


def cabecera(parte, de, modo, n_pasadas, n_granulos, pob_ruta):
    import scipy
    return {"tipo": "cabecera", "parte": parte, "de": de, "modo": modo, "n_pasadas": n_pasadas,
            "n_granulos": n_granulos, **PB.Q.procedencia(), "tag": os.environ.get("F4_TAG") or None,
            "poblacion": Path(pob_ruta).name, "sha256_poblacion": sha256_lf(pob_ruta),
            "sha256_frontend_index": sha256_lf(RAIZ / "frontend/index.html"),
            "sha256_evaluar_f4": sha256_lf(CARPETA / "evaluar_f4.py"), "sha256_probe_f4": sha256_lf(__file__),
            "blob_evaluar_d25": E.blob(E.D25_RUTA),
            "flags": {f: bool(getattr(pm, f)) for f in FLAGS_APAGADOS + ("ENABLE_MODIS_B22_PRIMARY",)},
            "versiones": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__},
            "formato_npz": "grillas/grilla_<vol>_<AAAAMMDDHHMM>.npz: mir, tir, box, pos_crater, mascara, vrp_mw, "
                           "dayflag, sunglint, inner_km, epsg, ul_x, ul_y, paso, n"}


def comprobar_entorno():
    """Antes de bajar nada: los flags de producción apagados (K es producción) y el blob de evaluar_d25."""
    malos = [f for f in FLAGS_APAGADOS if getattr(pm, f)]
    if malos:
        sys.exit(f"flags que tienen que estar apagados en el perfil y no lo están: {malos}")
    if E.blob(E.D25_RUTA) != E.D25_BLOB:
        sys.exit("evaluar_d25.py no es el blob sellado 1dbabf65")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parte", type=int, required=True)
    ap.add_argument("--de", type=int, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--poblacion", default=str(POBLACION))
    ap.add_argument("--humo", action="store_true", help=f"sólo las pasadas de {HUMO.name}")
    args = ap.parse_args()
    if not os.environ.get("EARTHDATA_TOKEN", "").strip():
        sys.exit("EARTHDATA_TOKEN vacío: el arnés no usa usuario y clave (A71).")
    comprobar_entorno()
    pob = json.load(open(args.poblacion, encoding="utf-8"))
    grupos = pasadas_de_la_parte(pob, args.parte, args.de, leer_humo() if args.humo else None)
    import run_pipeline as rp
    from pipeline.fetch import auth
    auth()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    hdf = out / "hdf"
    arboles = Path(os.environ.get("VRP_TMP_DIR", tempfile.gettempdir())) / "arboles_f4"
    nombre = "f4_parte_humo.jsonl" if args.humo else f"f4_parte{args.parte:02d}.jsonl"
    salida = open(out / nombre, "w", encoding="utf-8")
    n_pas = sum(len(v) for v in grupos.values())
    salida.write(json.dumps(cabecera(args.parte, args.de, "humo" if args.humo else "completo", n_pas, len(grupos),
                                     args.poblacion), ensure_ascii=False) + "\n")
    t0, vol_cache = time.time(), {}

    def medir_archivo(clave, ps, l1b, geo, otro_granulo, escribir):
        err = 0
        datos = pm.read_modis_l1b(l1b)
        for p in ps:
            try:
                if p["vol"] not in vol_cache:
                    vol_cache[p["vol"]] = rp.load_volcanoes(p["vol"])[0]
                v = vol_cache[p["vol"]]
                fila = medir_pasada(p, v, rp.VOLCANIC_FEATURES.get(v["name"]), l1b, geo, datos, out,
                                    arboles, otro_granulo=otro_granulo)
                if fila["estado"] != "ok":
                    err += 1
            except Exception as e:  # noqa: BLE001
                fila = {"tipo": "record", "vol": p["vol"], "dt": p["dt"], "clave": clave, "estado": "error",
                        "error": f"{type(e).__name__}: {e}", "traza": traceback.format_exc()[-1500:]}
                err += 1
            escribir(fila)
            print(json.dumps({"vol": fila["vol"], "dt": fila["dt"], "estado": fila["estado"],
                              "marca": fila.get("v_marca"), "motivo": fila.get("motivo"),
                              "pub": fila.get("pub_runner"), "dist": fila.get("dist"),
                              "k_vs_data": fila.get("k_difiere_de_guardado"),
                              "k_sha": fila.get("k_reproducida_en_su_sha"), "s": fila.get("segundos")},
                             ensure_ascii=False, default=float), flush=True)
        return err

    errores, terminada = recorrer_granulos(grupos, salida, lambda n, info: bajar_por_nombre(n, hdf, info=info),
                                           medir_archivo)
    minutos = (time.time() - t0) / 60
    salida.write(json.dumps({"tipo": "pie", "errores": errores, "minutos": round(minutos, 1), "terminada_por": terminada,
                             "s_por_pasada": round(60 * minutos / n_pas, 2) if n_pas else None}) + "\n")
    salida.close()
    print(f"parte {args.parte}: {len(grupos)} gránulos, {n_pas} pasadas, {errores} con error, {minutos:.1f} min"
          + (f", cortada por {terminada}" if terminada else ""))
    sys.exit(codigo_salida(errores, terminada))


if __name__ == "__main__":
    main()
