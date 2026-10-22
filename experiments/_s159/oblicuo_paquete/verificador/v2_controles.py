# -*- coding: utf-8 -*-
"""S159 verificador, paso 2: controles de lo que salió en v1.

(a) Las 4 alertas >50 con CONS+OCR: ¿mirova_vrp es el de la tabla (CONS) o el del OCR?
(b) Pasadas donde la banda de triangulación del oráculo (O1) es ancha (max/min > 1,82): ¿pesan en la tabla?
(c) MIROVA misma noche, oblicua contra menos oblicua (v1 §5 dio 0,52). Nulo: los MISMOS pares ordenados por HORA en
    vez de por cenit (si la caída fuera deriva temporal del volcán dentro de la noche, el orden por hora también la
    mostraría), y pares con diferencia de cenit < 10° ordenados por cenit (sin palanca angular: tiene que dar ~1).
    Además, una sola razón por noche (la mediana de sus pares) para no contar la misma noche varias veces.
Pregunta 1: si MIROVA no dependiera del cenit, el orden por cenit daría ~1 igual que el nulo; se ve.
Pregunta 2: n por celda; n 0 = SIN DATO.
Denominador: el de v1 (181 alertas que deciden, VIIRS 750 nocturno, 2026-04-01 a 2026-10-21 sin 18-19 oct).
"""
from __future__ import annotations

import collections
import csv
import glob
import io
import json
import sys
from pathlib import Path

import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
N = AQUI.parents[1] / "n"
ROOT = AQUI.parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
import banco_paridad as B  # noqa: E402

ART = r"D:\vrp-trabajo\temporales\s159_n\run_39682867040"
L = []


def pr(*x):
    s = " ".join(str(y) for y in x)
    print(s)
    L.append(s)


def q(xs):
    if len(xs) == 0:
        return "SIN DATO (n=0)"
    a = np.asarray(xs, float)
    return f"med {np.median(a):.3f} [{np.quantile(a, .25):.3f}, {np.quantile(a, .75):.3f}] n={len(a)}"


def alerta_o(o, inner):
    if not o or not o.get("npix") or (o.get("vrp_mw") or 0) <= 0:
        return False
    return max(o["pixeles"], key=lambda p: p[4])[3] <= inner


def main():
    obj = {o["id"]: o for o in json.loads((N / "objetivos_n.json").read_text(encoding="utf-8"))}
    tab = {int(r["id"]): r for r in csv.DictReader(open(N / "tabla_por_pasada.csv", encoding="utf-8"))}
    res = {}
    for f in sorted(glob.glob(ART + r"\*\resultados_*.json")):
        for r in json.loads(Path(f).read_text(encoding="utf-8")):
            if r.get("estado") == "ok" or r["id"] not in res:
                res[r["id"]] = r
    inner = B.inner_desde_html()
    pos = [i for i, o in obj.items() if o["lab"] == "pos" and o["decide"] and (res.get(i) or {}).get("estado") == "ok"
           and o["clase"] != "diurna"]
    Z = {i: res[i]["geometria_centro"]["sensor_zenith"] for i in pos}
    M = {i: obj[i]["mirova_vrp"] for i in pos}
    O = {i: (res[i]["oraculo"]["geo_linear"]["vrp_mw"] if alerta_o(res[i]["oraculo"]["geo_linear"],
                                                                      inner[obj[i]["volcan"]]) else None) for i in pos}

    pr("== (a) alertas con dos filas del scraper: valor elegido contra cada fila")
    for i in pos:
        if len(obj[i]["mirova"]) > 1:
            fil = "; ".join(f"{m['source']} {m['tipo']} {m['vrp_mw']} {m['fecha_utc'][11:]}" for m in obj[i]["mirova"])
            pr(f"   {i:3d} {obj[i]['volcan'][:12]:12s} {obj[i]['hora_utc']} z{Z[i]:.0f} elegido {M[i]} | {fil} | O {O[i]}")
    pr("   alertas solo OCR: " + ", ".join(f"{i} {obj[i]['volcan'][:10]} z{Z[i]:.0f} M{M[i]} O{O[i]}"
                                       for i in pos if {m['source'] for m in obj[i]['mirova']} == {'OCR'}))

    pr("\n== (b) banda de triangulación del oráculo ancha (max/min > 1,82)")
    for i in pos:
        b = res[i]["oraculo"]["geo_linear"].get("vrp_banda")
        if O[i] and b and b[0] > 0 and b[1] / b[0] > 1.82:
            pr(f"   {i:3d} {obj[i]['volcan'][:12]:12s} {obj[i]['hora_utc']} z{Z[i]:.1f} M{M[i]} O {O[i]:.3f} banda"
               f" [{b[0]:.3f}, {b[1]:.3f}] npix {res[i]['oraculo']['geo_linear']['npix']}")

    pr("\n== (c) MIROVA y O, misma noche y volcán")
    noche = lambda i: (obj[i]["volcan"], obj[i]["hora_utc"][:10])
    g = collections.defaultdict(list)
    for i in pos:
        g[noche(i)].append(i)

    def pares(cond):
        return [(a, b) for ss in g.values() for a in ss for b in ss if a != b and cond(a, b)]
    hora = lambda i: obj[i]["hora_utc"]
    casos = (
        ("cenit: oblicua/menos (dz >= 15)", pares(lambda a, b: Z[a] - Z[b] >= 15)),
        ("NULO hora: tardía/temprana, mismos pares", [(a, b) if hora(a) > hora(b) else (b, a)
                                                     for a, b in pares(lambda a, b: Z[a] - Z[b] >= 15)]),
        ("NULO sin palanca: cenit mayor/menor con 0 < dz < 10", pares(lambda a, b: 0 < Z[a] - Z[b] < 10)),
        ("cenit: >50 contra <=30", pares(lambda a, b: Z[a] > 50 and Z[b] <= 30)),
    )
    for etq, ps in casos:
        rM = [M[a] / M[b] for a, b in ps]
        rO = [O[a] / O[b] for a, b in ps if O[a] and O[b]]
        rK = [float(tab[a]["K_pc"]) / float(tab[b]["K_pc"]) for a, b in ps
              if tab[a]["K_pub"] == "True" and tab[b]["K_pub"] == "True" and float(tab[b]["K_pc"]) > 0]
        por_noche = collections.defaultdict(list)
        for a, b in ps:
            por_noche[noche(a)].append(M[a] / M[b])
        pn = [float(np.median(v)) for v in por_noche.values()]
        pr(f"   {etq}")
        pr(f"      MIROVA {q(rM)} | una por noche {q(pn)} (bajo 1: {sum(x < 1 for x in pn)} de {len(pn)})")
        pr(f"      O      {q(rO)}")
        pr(f"      K      {q(rK)}")
        pr(f"      volcanes {dict(collections.Counter(obj[a]['volcan'] for a, _ in ps))}")
    (AQUI / "v2_controles_salida.txt").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
