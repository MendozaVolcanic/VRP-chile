# -*- coding: utf-8 -*-
"""S159 oblicuo, paso 2: ¿el remuestreo reparte el píxel oblicuo en más celdas? Conteo del oráculo contra el nativo.

POR QUÉ. Si MIROVA cierra el déficit oblicuo porque interpola el gránulo a una grilla fija de 750 m, un píxel nativo
oblicuo (más grande en el terreno) cae en varias celdas, cada una sumada con el área nominal: el remuestreo devuelve el
área que el área nadir fija le quita. La firma es que el número de celdas alertadas del oráculo POR píxel nativo
alertado crezca con el cenit. La tarea 1.14 (S151) buscó esa firma en VIIRS 375 con el Npix del OSF 2025 y no la
encontró; acá se mira en VIIRS 750 con el oráculo, cuya magnitud reproduce a MIROVA (frente N).

Pregunta 1: si el conteo no dependiera del cenit, el cociente O_n/F_n daría lo mismo en los cuatro tramos; se imprime
por tramo y con Chillán separada (Chillán en erupción tiene focos grandes en cualquier ángulo, por eso se separa).
Pregunta 2: sólo entran pares con F publicando y el oráculo detectando (n declarado); el resto es SIN DATO.
Además: VRP medio por celda del oráculo contra VRP por píxel nativo de F (si el remuestreo sólo reparte, el VRP por
celda baja con el cenit y el total se conserva).
Uso: python 02_conteo_por_cenit.py
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
N = AQUI.parent / "n"
sys.path.insert(0, str(AQUI))
import importlib  # noqa: E402

M = importlib.import_module("01_razon_por_cenit")
L = []


def pr(*x):
    s = " ".join(str(y) for y in x)
    print(s)
    L.append(s)


def main():
    obj = {o["id"]: o for o in json.loads((N / "objetivos_n.json").read_text(encoding="utf-8"))}
    tab = {int(r["id"]): r for r in csv.DictReader(open(N / "tabla_por_pasada.csv", encoding="utf-8"))}
    res = {}
    for d in M.ARTS:
        for f in sorted(d.rglob("resultados_*.json")):
            for r in json.loads(f.read_text(encoding="utf-8")):
                if r.get("estado") == "ok" or r["id"] not in res:
                    res[r["id"]] = r
    inner = M.B.inner_desde_html()
    pos = [i for i, o in obj.items() if o["lab"] == "pos" and o["decide"] and (res.get(i) or {}).get("estado") == "ok"
           and o["clase"] != "diurna"]
    filas = []
    for i in pos:
        t = tab[i]
        o = res[i]["oraculo"]["geo_linear"]
        z = res[i]["geometria_centro"]["sensor_zenith"]
        if t["F_pub"] != "True" or not M.alerta_o(o, inner[obj[i]["volcan"]]):
            continue
        fn, fpc = float(t["F_n"]), float(t["F_pc"])
        if fn <= 0 or fpc <= 0:
            continue
        filas.append((M.tramo(z), obj[i]["volcan"] == "NevadosDeChillan", o["npix"] / fn,
                      (o["vrp_mw"] / o["npix"]) / (fpc / fn), o["npix"], fn))
    pr(f"pares F publica y oraculo detecta, con F_n>0 y F_pc>0: {len(filas)}")
    for etq, sel in (("todas", lambda c: True), ("sin Chillan", lambda c: not c), ("Chillan", lambda c: c)):
        pr(f"\n== {etq}: tramo | n | O_n/F_n mediana [q1,q3] | O_n mediana | F_n mediana | "
           f"(VRP por celda O)/(VRP por pixel F) mediana [q1,q3]")
        for nm, _, _ in M.TRAMOS:
            ss = [f for f in filas if f[0] == nm and sel(f[1])]
            if not ss:
                pr(f"   {nm:6s} | 0 | SIN DATO")
                continue
            a = np.array([f[2] for f in ss])
            b = np.array([f[3] for f in ss])
            pr(f"   {nm:6s} | {len(ss):3d} | {np.median(a):.2f} [{np.quantile(a, .25):.2f}, {np.quantile(a, .75):.2f}]"
               f" | {np.median([f[4] for f in ss]):.0f} | {np.median([f[5] for f in ss]):.0f} | "
               f"{np.median(b):.2f} [{np.quantile(b, .25):.2f}, {np.quantile(b, .75):.2f}]")
    (AQUI / "02_conteo_por_cenit_salida.txt").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
