# -*- coding: utf-8 -*-
"""Cajas de análisis de NHI-v1 para los 11 Tier A, a un commit fijo de NHI-v1 (S195, pre-registro del control diurno).

POR QUÉ. El evaluador del control diurno usa NHI (SWIR de Sentinel 2 y Landsat, repo MendozaVolcanic/NHI-v1) para
rescatar como «real con respaldo SWIR» una publicación diurna que MIROVA no lista. NHI no guarda la posición de sus
píxeles calientes, sólo si la caja de análisis del volcán tiene alguno; la caja es un cuadrado de medio lado
`buffer_km` alrededor de (lat, lon) del `config_nhi.py` (`nhi_analyzer.get_bbox`). Este script copia esos números a
`nhi_cajas.json` (nunca a mano, S91) y mide la distancia entre el centro de NHI y el de `volcanoes.yaml`: si NHI mira
otro lugar, su serie no sirve de respaldo para ese volcán.

Uso: python experiments/_s195_viirs_dia_control/extraer_nhi_cajas.py
"""
import ast
import base64
import json
import math
import subprocess
import sys
from pathlib import Path

import yaml

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[1]
COMMIT_NHI = "4d24515abe1e9fcb0a014d13eeb1963483b98993"   # main de NHI-v1 el 2026-11-23T05:15:25Z (re-sello S196: Chillán corregido en NHI-v1 #1; antes 09c45707e9a6, 2026-11-21T22:16:12Z)
NOMBRE_NHI = {"Chaiten": "Chaiten", "Copahue": "Copahue", "Isluga": "Isluga", "Lascar": "Lascar",
              "Lastarria": "Lastarria", "Llaima": "Llaima", "NevadosDeChillan": "Nevados de Chillan",
              "PlanchonPeteroa": "Planchon-Peteroa", "PuyehueCordonCaulle": "Puyehue - Cordon Caulle",
              "Tupungatito": "Tupungatito", "Villarrica": "Villarrica"}


def bajar(ruta):
    o = subprocess.run(["gh", "api", "repos/MendozaVolcanic/NHI-v1/contents/%s?ref=%s" % (ruta, COMMIT_NHI),
                        "--jq", ".content"], capture_output=True, text=True, check=True)
    return base64.b64decode(o.stdout).decode("utf-8")


def volcanes_nhi(fuente):
    for nodo in ast.parse(fuente).body:
        if isinstance(nodo, ast.Assign) and any(getattr(t, "id", None) == "VOLCANES" for t in nodo.targets):
            return ast.literal_eval(nodo.value)
    raise SystemExit("config_nhi.py sin VOLCANES")


def hav_km(a, b, c, d):
    p1, p2, dl, dn = math.radians(a), math.radians(c), math.radians(c - a), math.radians(d - b)
    h = math.sin(dl / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dn / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(h))


def main():
    vn = volcanes_nhi(bajar("config_nhi.py"))
    vy = {v["name"]: v for v in yaml.safe_load((ROOT / "volcanoes.yaml").read_text(encoding="utf-8"))
          if isinstance(v, dict) and "name" in v} if isinstance(
        yaml.safe_load((ROOT / "volcanoes.yaml").read_text(encoding="utf-8")), list) else {
        v["name"]: v for v in yaml.safe_load((ROOT / "volcanoes.yaml").read_text(encoding="utf-8"))["volcanoes"]}
    out = {"commit_nhi": COMMIT_NHI, "fuente": "config_nhi.py VOLCANES (lat, lon, buffer_km)", "volcanes": {}}
    for vol, nombre in NOMBRE_NHI.items():
        y = vy[vol]
        if nombre not in vn:
            out["volcanes"][vol] = {"nombre_nhi": nombre, "en_nhi": False}
            print("%-20s sin entrada en config_nhi.py" % vol)
            continue
        c = vn[nombre]
        d = hav_km(y["lat"], y["lon"], c["lat"], c["lon"])
        out["volcanes"][vol] = {"nombre_nhi": nombre, "en_nhi": True, "lat": c["lat"], "lon": c["lon"],
                                "buffer_km": c["buffer_km"], "dist_centro_yaml_km": round(d, 2)}
        print("%-20s buffer %4.1f km  centro NHI a %6.2f km del de volcanoes.yaml" % (vol, c["buffer_km"], d))
    (AQUI / "nhi_cajas.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8",
                                         newline="\n")


if __name__ == "__main__":
    main()
