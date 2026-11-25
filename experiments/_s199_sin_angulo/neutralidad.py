# -*- coding: utf-8 -*-
"""S199, neutralidad de la marca «angulo_ausente»: con los cuatro ángulos válidos, el record es byte a byte el mismo.

POR QUÉ. La marca sólo debe actuar cuando falta un ángulo. Con los cuatro presentes y válidos (todos los records de la
vía en producción, censos F8-107 i2 y R3F3-102 i1), el record que se guarda tiene que ser idéntico antes y después
del cambio en los tres sensores, incluidos dayflag, sunglint, los *_deg y la miniatura.

Cómo. Este script corre UN árbol (--raiz): importa pipeline.mirova_v750_codigo de ese árbol y pasa por
calcular_vrp_granulo real un juego de escenas con ángulos válidos, y escribe una línea JSON por escena (sort_keys, la
miniatura como lista). Se corre dos veces, sobre origin/main (git archive a un temporal) y sobre la rama, y
--comparar compara los dos archivos byte a byte. Escenas, en MODIS, VIIRS 750 y VIIRS 375:
  * gránulos sintéticos de tests/test_via_dato_faltante_crater_s190.py (foco de 1 píxel) y
    tests/test_via_sin_radiancia_s192.py (sin foco), y un foco de 2 x 2 a 600 K; con 9 geometrías válidas (noche,
    satélite en el nadir, satélite oblicuo, día, reflejo real bajo 12°, sol justo en 90°, sol en 0° y 180°, azimut en
    los bordes del rango);
  * escena sin radiancia, escena con media grilla sin dato (escena_invalida) y foco con miniatura encendida;
  * VIIRS: el mismo gránulo escrito como L1B y GEO HDF5 (ángulos int16 con factor 0,01) y leído por
    leer_radiancia_l1b y leer_geo_l1b;
  * MODIS: los recortes reales de tests/datos_s192_sin_radiancia (Mentolat, Melimoyu; MOD021KM.A2026213.0300).
Uso (desde cualquier carpeta):
  python neutralidad.py --raiz <árbol> --salida <archivo.jsonl> --tmp <carpeta>
  python neutralidad.py --comparar <a.jsonl> <b.jsonl>
Control del instrumento (--control): quita el cenit solar en la escena foco2x2 de noche de cada sensor; corrido así en
los dos árboles, la comparación TIENE que dar 3 escenas distintas (si diera 0, el comparador no ve diferencias).
Salidas guardadas: neutralidad_salida.txt (comparación) y neutralidad_control_salida.txt (control).
"""
import argparse
import hashlib
import importlib
import io
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

GEOMETRIAS = {   # (cenit satélite, azimut satélite, cenit sol, azimut sol), todas válidas
    "noche": (20.0, -100.0, 120.0, 50.0),
    "noche_nadir": (5.0, -100.0, 120.0, 50.0),
    "noche_oblicua": (60.0, 80.0, 100.0, -170.0),
    "dia": (30.0, -100.0, 40.0, 10.0),
    "reflejo_real": (5.0, -100.0, 5.0, 80.0),
    "sol_90": (0.0, 0.0, 90.0, 0.0),
    "sol_0": (10.0, 0.0, 0.0, 0.0),
    "sol_180": (10.0, 0.0, 180.0, 0.0),
    "azimut_bordes": (20.0, -180.0, 120.0, 360.0),
}


def _serial(o):
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    raise TypeError(type(o))


def _foco_2x2(MV, familia, T):
    gr = T._granulo(familia)
    c = gr["c"]
    cfg = MV.FAMILIAS[familia]
    gr["rad"][gr["b_mir"]][c:c + 2, c:c + 2] = MV.temperatura_a_radiancia(600.0, cfg["lam_mir"])
    return gr


def _con_geometria(gr, g):
    sz, sa, uz, ua = g
    n = gr["lat"].shape
    gr = dict(gr)
    gr["ang"] = {"sensor_zenith": np.full(n, sz), "sensor_azimuth": np.full(n, sa),
                 "solar_zenith": np.full(n, uz), "solar_azimuth": np.full(n, ua)}
    return gr


def _escribir_l1b_geo(tmp, nombre, gr):
    import h5py
    sf_rad = 0.0002
    l1b, geo = tmp / f"{nombre}_l1b.nc", tmp / f"{nombre}_geo.nc"
    with h5py.File(l1b, "w") as f:
        obs = f.create_group("observation_data")
        for b in (gr["b_mir"], gr["b_tir"]):
            dn = np.clip(np.round(gr["rad"][b] / sf_rad), 0, 65527).astype(np.uint16)
            ds = obs.create_dataset(b, data=dn)
            ds.attrs["scale_factor"] = np.array([sf_rad], np.float32)
            ds.attrs["add_offset"] = np.array([0.0], np.float32)
            ds.attrs["valid_max"] = np.array([65527], np.uint16)
    with h5py.File(geo, "w") as f:
        g = f.create_group("geolocation_data")
        g.create_dataset("latitude", data=gr["lat"].astype(np.float32))
        g.create_dataset("longitude", data=gr["lon"].astype(np.float32))
        for k, a in gr["ang"].items():
            ds = g.create_dataset(k, data=np.round(a / 0.01).astype(np.int16))
            ds.attrs["scale_factor"] = np.array([0.01], np.float32)
    return l1b, geo


def correr(raiz, salida, tmp, control=False):
    raiz = Path(raiz).resolve()
    sys.path.insert(0, str(raiz / "tests"))
    sys.path.insert(0, str(raiz))
    MV = importlib.import_module("pipeline.mirova_v750_codigo")
    assert Path(MV.__file__).resolve().is_relative_to(raiz), MV.__file__
    T190 = importlib.import_module("test_via_dato_faltante_crater_s190")
    T192 = importlib.import_module("test_via_sin_radiancia_s192")
    tmp = Path(tmp)
    tmp.mkdir(parents=True, exist_ok=True)
    lineas = []

    def registrar(nombre, rec):
        lineas.append(nombre + "\t" + json.dumps(rec, sort_keys=True, default=_serial))

    def run(T, gr, fam):
        return MV.calcular_vrp_granulo(gr["rad"], gr["lat"], gr["lon"], gr["ang"], T.VOLC, T.V_LAT, T.V_LON,
                                       T.INNER_KM, T.SENSOR[fam], familia=fam)

    for fam in ("MODIS", "VIIRS750", "VIIRS375"):
        bases = {"s190_foco1": (T190, T190._granulo(fam)), "s192_sinfoco": (T192, T192._granulo(fam)),
                 "foco2x2": (T190, _foco_2x2(MV, fam, T190))}
        for nb, (T, gr0) in bases.items():
            for ng, g in GEOMETRIAS.items():
                gr = _con_geometria(gr0, g)
                if control and nb == "foco2x2" and ng == "noche":
                    del gr["ang"]["solar_zenith"]   # control del instrumento: aquí la rama debe diferir de main
                registrar(f"{fam}|{nb}|{ng}", run(T, gr, fam))
        # escena sin radiancia y media grilla sin dato
        T, gr = T192, _con_geometria(T192._granulo(fam), GEOMETRIAS["noche"])
        for b in gr["rad"]:
            gr["rad"][b][:] = np.nan
        registrar(f"{fam}|sin_radiancia|noche", run(T, gr, fam))
        gr = _con_geometria(T192._granulo(fam), GEOMETRIAS["noche"])
        gr["rad"][gr["b_tir"]][: gr["lat"].shape[0] * 3 // 5] = np.nan
        registrar(f"{fam}|media_grilla|noche", run(T, gr, fam))
        # miniatura encendida
        MV.GENERAR_MINIATURA = True
        try:
            registrar(f"{fam}|foco2x2_miniatura|noche",
                      run(T190, _con_geometria(_foco_2x2(MV, fam, T190), GEOMETRIAS["noche"]), fam))
        finally:
            MV.GENERAR_MINIATURA = False
        # lectores reales de VIIRS
        if fam != "MODIS":
            for ng in ("noche", "dia", "reflejo_real"):
                gr = _con_geometria(_foco_2x2(MV, fam, T190), GEOMETRIAS[ng])
                l1b, geo = _escribir_l1b_geo(tmp, f"{fam}_{ng}", gr)
                rad = MV.leer_radiancia_l1b(l1b, bandas=(gr["b_mir"], gr["b_tir"]))
                lat, lon, ang = MV.leer_geo_l1b(geo)
                rec = MV.calcular_vrp_granulo(rad, lat, lon, ang, T190.VOLC, T190.V_LAT, T190.V_LON, T190.INNER_KM,
                                              T190.SENSOR[fam], familia=fam)
                registrar(f"{fam}|hdf5_l1b_geo|{ng}", rec)
    for nombre in ("Mentolat", "Melimoyu"):
        registrar(f"MODIS|real_{nombre}|noche60", T192._real(nombre))
    texto = "\n".join(lineas) + "\n"
    Path(salida).write_text(texto, encoding="utf-8", newline="\n")
    print(f"{raiz}: {len(lineas)} escenas, sha256 {hashlib.sha256(texto.encode()).hexdigest()}")


def comparar(a, b):
    ba, bb = Path(a).read_bytes(), Path(b).read_bytes()
    la, lb = ba.decode().splitlines(), bb.decode().splitlines()
    print(f"A: {a}\n   {len(la)} escenas, {len(ba)} bytes, sha256 {hashlib.sha256(ba).hexdigest()}")
    print(f"B: {b}\n   {len(lb)} escenas, {len(bb)} bytes, sha256 {hashlib.sha256(bb).hexdigest()}")
    distintas = [x.split("\t")[0] for x, y in zip(la, lb) if x != y]
    nombres = [x.split("\t")[0] for x in la]
    detectadas = sum(1 for x in la if json.loads(x.split("\t")[1]).get("vrp_mw", 0) > 0)
    motivos = sorted({str(json.loads(x.split("\t")[1])["diag_codigo_mirova"].get("motivo_vacio")) for x in la})
    print(f"escenas con vrp_mw > 0: {detectadas} de {len(la)}; motivos presentes: {motivos}")
    print(f"mismos nombres en el mismo orden: {nombres == [y.split(chr(9))[0] for y in lb]}")
    print(f"escenas distintas: {len(distintas)} {distintas[:10]}")
    print("IDENTICOS BYTE A BYTE" if ba == bb else "DISTINTOS")
    return 0 if ba == bb else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--raiz")
    ap.add_argument("--salida")
    ap.add_argument("--tmp")
    ap.add_argument("--comparar", nargs=2)
    ap.add_argument("--control", action="store_true")
    a = ap.parse_args()
    sys.exit(comparar(*a.comparar) if a.comparar else correr(a.raiz, a.salida, a.tmp, a.control))
