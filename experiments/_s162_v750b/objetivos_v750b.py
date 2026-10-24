# -*- coding: utf-8 -*-
"""S162 V750-B, paso 1: lista de objetivos del run (población de N extendida) con la celda del cráter, el radio interior
y la marca del subconjunto S_C (brazo nativo de V750-C).

POR QUÉ. El run corre el código de MIROVA con cuatro cajas en todas las pasadas de VIIRS 750 nocturnas de la ventana, y
con la geometría nativa en S_C. La caja B2 necesita saber en qué celda de la grilla de MIROVA cae el cráter de
volcanoes.yaml; B3 necesita el radio interior del tablero.

Población: experiments/_s159/n/01_poblacion.py sin cambiar su lógica (banco_paridad, regla SN, lectura A, ±120 s), con
la ventana y los días excluidos del pre-registro (§3). Lo corre la coordinadora al despachar, contra los records y la
referencia remota de ese momento; el resultado y su sha256 se commitean antes del despacho.

S_C (semilla 162): las cumbres de K en 0,0 MW (negativas y con alerta), todas las alertas que deciden, y 300 negativos
limpios sin cúmulo de K sorteados.
Uso: python objetivos_v750b.py --data <data/mirova_equivalent de origin/main> --ref-dest <carpeta> --hasta 2026-11-02
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import random
import sys
from pathlib import Path

import yaml

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
N_DIR = RAIZ / "experiments/_s159/n"
EXCLUIDOS = ("2026-10-13", "2026-10-17", "2026-10-18", "2026-10-19", "2026-10-20")
CORTE_SNPP = "2026-11-02 13:00"   # cese de Suomi NPP: toda pasada desde esta hora es otro régimen
SEMILLA_SC = 162
N_NEG_SC = 300
CELDA, NG = 750.0, 67


def _modulo(nombre, ruta):
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def celda_crater(g, vent_lat, vent_lon):
    """(fila, columna) de la grilla GEO de MIROVA donde cae el cráter (fila 0 = norte, como probe_n.grillar)."""
    from pyproj import Transformer
    t = Transformer.from_crs("EPSG:4326", f"EPSG:{g['epsg']}", always_xy=True)
    x, y = t.transform(vent_lon, vent_lat)
    return [int((g["ul_y"] - y) // CELDA), int((x - g["ul_x"]) // CELDA)]


def completar(objs, vy, inner):
    """Agrega celda_crater e inner_km a cada objetivo (vy: volcanoes.yaml por nombre; inner: del tablero)."""
    for o in objs:
        v = vy[o["volcan"]]
        o["celda_crater"] = celda_crater(o["grilla"], v.get("vent_lat", v["lat"]), v.get("vent_lon", v["lon"]))
        o["inner_km"] = float(inner[o["volcan"]])
    return objs


def marcar_sc(objs):
    cumbre0 = [o for o in objs if o.get("dc") == "summit" and o.get("pc_vrp") == 0]
    alertas = [o for o in objs if o["lab"] == "pos" and o.get("decide")]
    sin_k = [o for o in objs if o["lab"] == "neg_limpio" and not o.get("pc_n")]
    rng = random.Random(SEMILLA_SC)
    neg = rng.sample(sorted(sin_k, key=lambda o: (o["volcan"], o["hora_utc"])), min(N_NEG_SC, len(sin_k)))
    sc = {id(o) for o in cumbre0 + alertas + neg}
    for o in objs:
        o["en_sc"] = id(o) in sc
    return len(cumbre0), len(alertas), len(neg)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--ref-dest", required=True)
    ap.add_argument("--hasta", required=True, help="último día de la ventana (YYYY-MM-DD)")
    a = ap.parse_args()
    P = _modulo("pob", N_DIR / "01_poblacion.py")
    P.VENTANA = ("2026-04-01", a.hasta)
    P.AQUI = AQUI                       # escribe poblacion_completa.json acá, no en la carpeta de N
    sys.argv = ["01_poblacion.py", "--data", a.data, "--ref-dest", a.ref_dest]
    P.main()
    pob = json.loads((AQUI / "poblacion_completa.json").read_text(encoding="utf-8"))["pasadas"]
    pob = [p for p in pob if p["hora_utc"][:10] not in EXCLUIDOS and p["hora_utc"] < CORTE_SNPP]
    SEL = _modulo("sel", N_DIR / "02_seleccion.py")
    G = SEL.grillas()
    for p in pob:
        p["grilla"] = G[SEL.TIF.get(p["volcan"], p["volcan"])]
    vy = {v["name"]: v for v in yaml.safe_load((RAIZ / "volcanoes.yaml").read_text(encoding="utf-8"))["volcanoes"]}
    sys.path.insert(0, str(RAIZ / "scripts"))
    import banco_paridad as B
    completar(pob, vy, B.inner_desde_html())
    nc, na, nn = marcar_sc(pob)
    pob.sort(key=lambda e: (e["granule"] or "", e["volcan"]))
    for n, e in enumerate(pob):
        e["id"] = n
    texto = json.dumps(pob, ensure_ascii=False, default=str)
    (AQUI / "objetivos_v750b.json").write_text(texto, encoding="utf-8")
    print(f"objetivos: {len(pob)} | S_C: cumbres en 0 MW {nc}, alertas que deciden {na}, negativos sin K {nn} | "
          f"sin granulo {sum(1 for e in pob if not e['granule'])} | sha256 "
          f"{hashlib.sha256(texto.encode('utf-8')).hexdigest()}")


if __name__ == "__main__":
    main()
