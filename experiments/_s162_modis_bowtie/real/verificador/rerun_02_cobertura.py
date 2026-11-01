# -*- coding: utf-8 -*-
"""Paso 2, ANTES de leer ningun resultado del port: donde se pisan los barridos en los datos reales y cuanto suelo
queda visto 0, 1 o 2+ veces con cada metodo de quitar duplicados (comun.ORDEN_METODOS).

Medida. Puntos del suelo cada 200 m en dos cajas alrededor del punto de referencia de MIROVA (X0, Y0): la caja de la
ROI1 del port (+/- 7,875 km, donde el codigo detecta) y la grilla entera (+/- 25,5 km). Para cada punto se cuentan las
huellas nominales (paralelogramo centro +/- a/2 +/- b/2, comun.py) de los pixeles conservados que lo contienen.
Controles (A110, nulo medido): (1) en pasadas casi al nadir (cenit < 15) "todos" tiene que dar ~100 % visto una vez:
si no, el modelo de huella esta mal; (2) C_sin_det0 tiene que abrir huecos (~10 %) tambien en el nadir; (3) el vecino
k-esimo del arbol no debe contener el punto (si lo contiene, k es corto y el conteo se queda bajo).
Ademas, por pasada: cuantos detectores por barrido quita cada metodo, el detector del pixel nativo del crater y cuantas
huellas de "todos" cubren el crater. Escribe 02_cobertura.json para el paso 3.
Uso: python -I 02_cobertura.py
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # VERIFICADOR: importa comun.py del auditor; salidas en verificador/
import numpy as np  # noqa: E402
import comun as CM  # noqa: E402

CAJAS = {"roi1": 7875.0, "grilla": 25500.0}


def estrato(z):
    return "z<15" if z < 15 else "15-25" if z < 25 else "25-40" if z < 40 else "40-50" if z < 50 else "z>=50"


def main():
    pr, L = CM.pr_factory()
    obj, res = CM.objetivos(), CM.resultados()
    ids = [i for i in sorted(obj) if CM.evaluable(res.get(i))]
    salida = {}
    k_corto = 0
    for i in ids:
        o, g = obj[i], obj[i]["grilla"]
        n = CM.cargar_nativo(i)
        G = CM.geometria(n, g["epsg"])
        ci, cj, dcr = CM.pixel_crater(G, g)
        fila = {"z": o["z"], "estrato": estrato(o["z"]), "det_crater": int(G["det"][ci, cj]),
                "dist_pixel_crater_m": round(dcr, 1), "metodos": {}}
        # cobertura del crater (punto X0, Y0) con todos
        cnt_cr, _ = CM.conteo_cobertura(G, np.zeros_like(G["u"], bool), np.array([g["X0"]]), np.array([g["Y0"]]))
        fila["huellas_en_crater_todos"] = int(cnt_cr[0])
        for m in CM.ORDEN_METODOS:
            q = CM.mascara_quitar(G, m)
            d = {"frac_quitada": round(float(q.mean()), 4),
                 "quita_det_crater": bool(q[ci, cj]),
                 "quita_por_det": [round(float(q[G["det"] == t].mean()), 3) for t in range(10)]}
            for nombre, medio in CAJAS.items():
                px, py = CM.puntos_caja(g, medio)
                c, ult = CM.conteo_cobertura(G, q, px, py)
                k_corto += int(ult.sum())
                d[nombre] = [round(float((c == 0).mean()), 5), round(float((c == 1).mean()), 5),
                             round(float((c >= 2).mean()), 5)]
            fila["metodos"][m] = d
        salida[i] = fila
    (Path(__file__).with_name("02_cobertura.json")).write_text(json.dumps(salida, indent=0), encoding="utf-8")

    pr(f"pasadas evaluables: {len(ids)}; puntos donde el vecino k-esimo aun contenia el punto (k corto): {k_corto}")
    est = collections.defaultdict(list)
    for i, f in salida.items():
        est[f["estrato"]].append(i)
    orden = ["z<15", "15-25", "25-40", "40-50", "z>=50"]
    pr("pasadas por estrato de cenit:", {e: len(est[e]) for e in orden})
    for caja in CAJAS:
        pr(f"\n== cobertura del suelo, caja {caja} (+/- {CAJAS[caja] / 1000:.3f} km). Media por pasada de la fraccion "
           f"vista [0, 1, 2+] veces; entre corchetes, la peor pasada en huecos (max frac 0) y en duplicados (max 2+)")
        for m in CM.ORDEN_METODOS:
            pr(f"  {m}: {CM.DESCRIPCION[m]}")
            for e in orden:
                if not est[e]:
                    continue
                v = np.array([salida[i]["metodos"][m][caja] for i in est[e]])
                pr(f"     {e:6s} n {len(est[e]):3d}  0: {v[:, 0].mean():.4f}  1: {v[:, 1].mean():.4f}  "
                   f"2+: {v[:, 2].mean():.4f}   [max 0: {v[:, 0].max():.4f}; max 2+: {v[:, 2].max():.4f}]")
    pr("\n== fraccion de pixeles quitados por detector (media por pasada), estrato z>=50 y 40-50")
    for e in ("40-50", "z>=50"):
        for m in CM.ORDEN_METODOS[1:]:
            v = np.array([salida[i]["metodos"][m]["quita_por_det"] for i in est[e]])
            pr(f"  {e:6s} {m:24s}", np.round(v.mean(axis=0), 2).tolist())
    pr("\n== el crater: detector del pixel nativo mas cercano a (X0, Y0) y huellas de 'todos' que lo cubren")
    for e in orden:
        c = collections.Counter(salida[i]["huellas_en_crater_todos"] for i in est[e])
        s = sum(salida[i]["det_crater"] in (0, 9) for i in est[e])
        pr(f"  {e:6s} n {len(est[e]):3d}  crater en detector 0 o 9: {s}; huellas sobre el crater: {dict(sorted(c.items()))}")
    (Path(__file__).with_name("02_cobertura_salida.txt")).write_bytes(("\n".join(L) + "\n").encode("utf-8"))


if __name__ == "__main__":
    main()
