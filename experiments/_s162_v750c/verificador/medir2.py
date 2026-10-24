# -*- coding: utf-8 -*-
"""Verificador V750-C, segunda tanda: la zona de la caja donde cae el pixel de K en el censo, y el margen que ese
pixel tendria con los umbrales sensibles (zona 2) aunque caiga en la zona conservadora (zona 1).

Pregunta 1: si la zona no importara, los recuperados por vecino mas cercano se repartirian entre zona 1 y 2 como el
censo (20 en zona 1, 38 en zona 2). Pregunta 2: el margen con umbrales de zona 2 es mayor o igual que con los de
zona 1 por construccion; si no lo fuera, el instrumento esta roto.
Uso: python medir2.py --insumos <carpeta> --grillas <dir> --csv <ablacion_por_pasada.csv>
"""
from __future__ import annotations

import argparse
import collections
import csv
import statistics
import sys
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
import ablacion as A  # noqa: E402
import oraculo_ablacion as OA  # noqa: E402
import banco_paridad as B  # noqa: E402


def margen_zona(d, rc, zona):
    """Como ablacion.margen_en_k pero con los umbrales de una zona fija (1 o 2) para todo el entorno 3x3."""
    p = d.get("pasada1") or {}
    if "c_eti" not in p:
        return np.nan
    un, ue = (p["u_nti2"], p["u_eti2"]) if zona == 2 else (p["u_nti1"], p["u_eti1"])
    mejor = -np.inf
    for a in range(rc[0] - 1, rc[0] + 2):
        for b in range(rc[1] - 1, rc[1] + 2):
            if not (0 <= a < OA.N and 0 <= b < OA.N):
                continue
            cn, ce = p["c_nti"][a, b], p["c_eti"][a, b]
            if np.isfinite(cn) and np.isfinite(ce):
                mejor = max(mejor, min(cn / un, ce / ue))
    return mejor if np.isfinite(mejor) else np.nan


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--insumos", required=True, type=Path)
    ap.add_argument("--grillas", required=True, type=Path)
    ap.add_argument("--csv", required=True, type=Path)
    a = ap.parse_args()
    res, obj = A.cargar(a.insumos)
    inner = B.inner_desde_html()
    rows = {int(x["id"]): x for x in csv.DictReader(open(a.csv, encoding="utf-8"))}
    f = lambda s: s == "True"
    censo = [i for i, x in rows.items() if x["clase"] == "cumbre_0mw"]
    print("censo:", len(censo))
    # zona de la celda de K (de la caja por defecto) contra recuperacion por brazo
    print("\n== censo 60: recuperados ('enK') por zona de la caja por defecto donde cae la celda de K")
    zona = {}
    for i in censo:
        o, r = obj[i], res[i]
        k = r["brazos"]["K"]["record"]
        rc = A.celda_k(o, k)
        bx = OA.caja("def")
        zona[i] = int(bx[rc]) if np.isfinite(bx[rc]) else None
    print("  zona de la celda de K:", dict(collections.Counter(zona.values())), "| por volcan:",
          {v: dict(collections.Counter(zona[i] for i in censo if obj[i]["volcan"] == v)) for v in sorted({obj[i]["volcan"] for i in censo})})
    for b in ("O", "O_8vec", "O_sens", "O_circ", "O_todoK_sincomp", "geo_nearest", "geo_cubic", "r2_linear", "r2_nearest"):
        c = collections.Counter(zona[i] for i in censo if f(rows[i][f"{b}_enK"]))
        print(f"  {b:16s} enK por zona: {dict(c)}")
    # distancia de la celda de K al centro de la grilla por volcan
    print("\n== distancia de la celda de K al centro de la grilla de MIROVA (km), por volcan (censo):")
    dk = collections.defaultdict(list)
    for i in censo:
        o, r = obj[i], res[i]
        rc = A.celda_k(o, r["brazos"]["K"]["record"])
        dk[o["volcan"]].append(float(np.hypot(rc[0] - OA.N // 2, rc[1] - OA.N // 2) * 0.75))
    for v, d in sorted(dk.items()):
        print(f"  {v:22s} mediana {statistics.median(d):.2f} min {min(d):.2f} max {max(d):.2f} n={len(d)} | inner_radius_km {inner[v]} | mitad de la caja sensible 7x7: 2.625")
    # margen con umbrales de zona 2 para todos (brazo O, grilla lineal)
    print("\n== censo 60: margen del pase 1 del .m en el entorno de K con los umbrales de SU zona vs con los de zona 2 (sensible)")
    por_z = collections.defaultdict(lambda: {"propia": [], "z2": [], "z2_pasa": 0})
    tup = {"propia": [], "z2": []}
    for i in censo:
        o, r = obj[i], res[i]
        z = np.load(A.buscar_grilla(a.grillas, i))
        inn = inner[o["volcan"]]
        rc = A.celda_k(o, r["brazos"]["K"]["record"])
        _m, d = OA.detectar(z["m13"], z["m15"], r["dayflag"], r["sunglint"], OA.PIEZAS_MIROVA, inner_km=inn, devolver_diag=True)
        mp = margen_zona(d, rc, zona[i] if zona[i] in (1, 2) else 1)
        m2 = margen_zona(d, rc, 2)
        por_z[zona[i]]["propia"].append(mp)
        por_z[zona[i]]["z2"].append(m2)
        por_z[zona[i]]["z2_pasa"] += int(m2 >= 1)
        if o["volcan"] == "Tupungatito":
            tup["propia"].append(mp)
            tup["z2"].append(m2)
        assert m2 >= mp - 1e-12, (i, mp, m2)
    q = lambda v: f"mediana {statistics.median(v):.3f} [q1 {np.percentile(v, 25):.3f}, q3 {np.percentile(v, 75):.3f}] n={len(v)}" if v else "sin datos"
    for zz, d in sorted(por_z.items(), key=lambda x: str(x[0])):
        print(f"  zona {zz}: margen propio {q(d['propia'])} | con umbrales de zona 2 {q(d['z2'])} | pasarian con zona 2: {d['z2_pasa']}")
    print(f"  Tupungatito (17): margen propio {q(tup['propia'])} | con umbrales de zona 2 {q(tup['z2'])}")
    print("  (control: el margen con zona 2 nunca es menor que el propio; aserto en el bucle)")
    # Tupungatito: que hace O_sens y O_circ
    print("\n== Tupungatito en el censo con las cajas sensibles (brazo recalculado):")
    for b in ("O_sens", "O_circ", "O_8vec", "O_todoK_sincomp"):
        n = 0
        for i in censo:
            if obj[i]["volcan"] != "Tupungatito":
                continue
            n += f(rows[i][f"{b}_enK"])
        print(f"  {b:16s} enK {n}/17")


if __name__ == "__main__":
    main()
