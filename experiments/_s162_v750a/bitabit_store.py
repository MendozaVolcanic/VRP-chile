# -*- coding: utf-8 -*-
"""S162 V750-A: el almacén con el cableado de la vía queda BIT A BIT igual al de origin/main cuando nadie marca la vía.

POR QUÉ (pedido de la coordinadora S163 antes de mergear el cableado, A45). El cableado toca store.py: un record con
`via_codigo_mirova: True` ya no pasa por la geocerca, el filtro de píxeles por distancia ni el tope de píxeles por
cúmulo. Con el flag apagado ningún record trae esa marca, así que el almacén tiene que dar exactamente lo mismo que
antes. Aquí se pasan los MISMOS records reales (los publicados en data/mirova_equivalent, todos los sensores) por el
store.py de origin/main y por el de esta rama, con los mismos argumentos que usa run_pipeline.py para cada volcán, y se
compara el JSON escrito, record por record. Control (pregunta 1 del instrumento): los mismos records con la marca
puesta tienen que dar DISTINTO en al menos uno, o la comparación no puede ver el cambio.
Uso: python bitabit_store.py --ref origin/main [--por-volcan 300] [--semilla 162]
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import random
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
# el almacén marca cada record con el commit del código (regimen.codigo_sha, S151): fuera de Actions lo lee con
# `git rev-parse` desde la carpeta del archivo, y la copia de main vive en una carpeta temporal fuera del repo, así que
# sin esto TODOS los records difieren por el instrumento y no por el código (primera corrida: 0 de 6.143 iguales).
# Con GITHUB_SHA fijo los dos almacenes escriben la misma marca, como en Actions.
import os  # noqa: E402
os.environ["GITHUB_SHA"] = "bitabit-s162"
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))


def cargar_store(ruta, nombre):
    spec = importlib.util.spec_from_file_location(f"pipeline.{nombre}", ruta)
    m = importlib.util.module_from_spec(spec)
    m.__package__ = "pipeline"
    spec.loader.exec_module(m)
    return m


def pasar(store, recs, vol, dest):
    store.DATA_DIR = dest
    dest.mkdir(parents=True, exist_ok=True)
    for r in recs:
        store.append_record(vol["name"], r, volcano_lat=vol["lat"], volcano_lon=vol["lon"],
                            max_hotspot_dist_km=vol.get("radius_km"),
                            enable_pixel_level_distance_filter=PR.ENABLE_PIXEL_LEVEL_DISTANCE_FILTER,
                            max_cluster_pixels=vol.get("max_cluster_pixels"),
                            inner_radius_km=vol.get("inner_radius_km"),
                            volcanic_features=RP.VOLCANIC_FEATURES.get(vol["name"]))
    f = dest / f"{vol['name']}.json"
    d = json.loads(f.read_text(encoding="utf-8")) if f.exists() else []
    recs_out = d if isinstance(d, list) else d.get("records", d)
    for x in recs_out:                     # la hora de proceso cambia entre corridas por construcción
        for k in ("processed_utc", "first_processed_utc"):
            x.pop(k, None)
    return recs_out


def main():
    global PR, RP
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", default="origin/main")
    ap.add_argument("--por-volcan", type=int, default=300)
    ap.add_argument("--semilla", type=int, default=162)
    a = ap.parse_args()
    import pipeline.profile as PR
    import run_pipeline as RP
    tmp = Path(tempfile.mkdtemp(prefix="bitabit_store_"))
    viejo = tmp / "store_main.py"
    viejo.write_text(subprocess.run(["git", "show", f"{a.ref}:pipeline/store.py"], cwd=RAIZ, capture_output=True,
                                    text=True, encoding="utf-8", check=True).stdout, encoding="utf-8")
    SM = cargar_store(viejo, "store_main")
    SN = cargar_store(RAIZ / "pipeline/store.py", "store_nuevo")
    rng = random.Random(a.semilla)
    vols = [v for v in RP.load_volcanoes() if (RAIZ / "data/mirova_equivalent" / f"{v['name']}.json").exists()]
    n_tot = n_igual = n_ctrl_distinto = 0
    sensores = {}
    for v in vols:
        d = json.loads((RAIZ / "data/mirova_equivalent" / f"{v['name']}.json").read_text(encoding="utf-8"))
        todos = d if isinstance(d, list) else d.get("records", d)
        if not todos:
            continue
        recs = rng.sample(todos, min(a.por_volcan, len(todos)))
        for r in recs:
            sensores[r.get("sensor")] = sensores.get(r.get("sensor"), 0) + 1
        sal_m = pasar(SM, copy.deepcopy(recs), v, tmp / "main" / v["name"])
        sal_n = pasar(SN, copy.deepcopy(recs), v, tmp / "nuevo" / v["name"])
        n_tot += len(sal_m)
        igual = json.dumps(sal_m, sort_keys=True) == json.dumps(sal_n, sort_keys=True)
        n_igual += len(sal_m) if igual else 0
        print(f"{v['name']:22s} records {len(recs):4d} -> escritos {len(sal_m):4d} | iguales: {'SÍ' if igual else 'NO'}",
              flush=True)
        # control: con la marca de la vía el almacén nuevo tiene que poder dar distinto
        marcados = copy.deepcopy(recs)
        for r in marcados:
            r["via_codigo_mirova"] = True
        sal_c = pasar(SN, marcados, v, tmp / "control" / v["name"])
        for x in sal_c:
            x.pop("via_codigo_mirova", None)
        n_ctrl_distinto += json.dumps(sal_c, sort_keys=True) != json.dumps(sal_m, sort_keys=True)
    print(f"sensores en la muestra: {dict(sorted(sensores.items()))}")
    print(f"records escritos {n_tot}; iguales bit a bit entre {a.ref} y esta rama: {n_igual}")
    print(f"control (con la marca de la vía): volcanes donde el almacén nuevo da distinto: {n_ctrl_distinto} de {len(vols)} "
          "(tiene que ser más de 0)")
    bien = n_tot > 0 and n_igual == n_tot and n_ctrl_distinto > 0
    print("== bit a bit del almacén:", "VERDE" if bien else "ROJO")
    return 0 if bien else 1


if __name__ == "__main__":
    sys.exit(main())
