# -*- coding: utf-8 -*-
"""S159 frente GEO, parte R: baja la lamina "Dist" (distancia de la anomalia en el tiempo) de MIROVA para cada
Tier A, en VIIRS 375, VIIRS 750 y MODIS, de la carpeta de fecha mas reciente que tenga las tres.

POR QUE: la lamina Dist de Cordon Caulle 2026-10-10 05:54 trae una leyenda que separa las anomalias en
">20km" y "<20km", o sea un umbral de distancia propio del volcan dibujado por MIROVA. Si ese umbral cambia entre
volcanes es el radio de la ROI de cumbre de MIROVA por volcan, comparable con `inner_radius_km` del yaml.

Instrumento: la leyenda se LEE A OJO en cada PNG (no hay OCR aqui). Pregunta 1: si el umbral fuera igual en todos,
se veria el mismo numero en las 11 laminas. Pregunta 2: si la descarga fallara, el PNG no abre (se imprime ERROR).
Uso: python -I r2_laminas_dist.py <carpeta salida>
"""
import os
import subprocess
import sys
import json

REPO = "MendozaVolcanic/Mirova-v1"
BASE = "monitoreo_satelital/imagenes_satelitales"
VOLS = ["Chaiten", "Copahue", "Isluga", "Lascar", "Lastarria", "Llaima", "Nevados_de_Chillan", "PlanchonPeteroa",
        "Puyehue_Cordon_Caulle", "Tupungatito", "Villarrica"]


def api(path, raw=False):
    cmd = ["gh", "api"] + (["-H", "Accept: application/vnd.github.raw"] if raw else []) + [f"repos/{REPO}/contents/{path}"]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode:
        raise RuntimeError(r.stderr.decode("utf-8", "replace")[:200])
    return r.stdout


def main(out):
    os.makedirs(out, exist_ok=True)
    for v in VOLS:
        fechas = sorted(e["name"] for e in json.loads(api(f"{BASE}/{v}")) if e["type"] == "dir")
        for f in reversed(fechas):
            nombres = [e["name"] for e in json.loads(api(f"{BASE}/{v}/{f}"))]
            dist = sorted(n for n in nombres if n.endswith("_Dist.png"))
            if dist:
                for n in dist:
                    sen = n.split("_")[-2]
                    dest = os.path.join(out, f"{v}_{f}_{n}")
                    if not os.path.exists(dest):
                        open(dest, "wb").write(api(f"{BASE}/{v}/{f}/{n}", raw=True))
                    print(v, f, n, os.path.getsize(dest))
                break


if __name__ == "__main__":
    main(sys.argv[1])
