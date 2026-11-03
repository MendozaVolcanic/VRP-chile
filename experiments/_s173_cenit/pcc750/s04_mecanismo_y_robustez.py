# -*- coding: utf-8 -*-
"""s04 (S173, cenit PCC V750): de qué está hecho el déficit de K (detección, recorte a cero por el fondo, nivel), cómo
se compara el fondo de anillo de K con el fondo local del código de MIROVA en PCC, y robustez de los brazos clave.

POR QUÉ. La razón «con ceros» mezcla tres cosas que físicamente son distintas: (a) el detector nativo de K no
encuentra el lacolito en esa pasada; (b) lo encuentra pero el fondo de anillo (mediana de 5 a 25 km) es tan radiante
como el píxel caliente y el exceso se recorta a 0,0 MW; (c) publica, pero con menos potencia que MIROVA. Cada una pide
una palanca distinta. Y si el fondo de anillo es la palanca, tiene que verse que es más radiante que el fondo local
del código, y en cuánto (en K de temperatura de brillo, para leerlo como geólogo).

P1: (i) Planck(t_bg del record K del runner) contra la mediana de radiancia M13 del anillo 5-25 km en la grilla: si el
    brazo de grilla no representa al fondo de K, la comparación lo muestra; (ii) un control que debe dar 0: K2 contra K
    en la clasificación (a/b/c).
P2: barajado 200 semilla 173; dejar una noche fuera (26 réplicas); sólo CONS.
Ventana y denominador: los positivos de s03 (29 pasadas con alerta de MIROVA, 2026-04-07 a 2026-10-16, 26 noches).
Uso: python -B s04_mecanismo_y_robustez.py
"""
from __future__ import annotations

import collections
import csv
import io
import math
import os
import sys
from pathlib import Path

import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
REPO = AQUI / "repo"
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(AQUI))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
from _est import fl, linea, med, q, spearman, barajado  # noqa: E402
from pipeline.process_viirs_mod import bt_to_spectral_radiance, M13_LAMBDA  # noqa: E402

L = []


def pr(*x):
    s = " ".join(str(y) for y in x)
    print(s, flush=True)
    L.append(s)


def planck_inv(Lr, lam_um=M13_LAMBDA):
    """BT (K) de una radiancia espectral W m-2 sr-1 um-1, invirtiendo bt_to_spectral_radiance por bisección (así se
    usa exactamente la función de producción, sin reescribir sus constantes)."""
    lo, hi = 150.0, 400.0
    for _ in range(60):
        m = (lo + hi) / 2
        if float(bt_to_spectral_radiance(np.float64(m), lam_um)) < Lr:
            lo = m
        else:
            hi = m
    return (lo + hi) / 2


def main():
    P = [x for x in csv.DictReader(open(AQUI / "s03_por_pasada.csv", encoding="utf-8"))
         if fl(x["vM"]) and fl(x["vM"]) > 0]
    for x in P:
        x["z"] = fl(x["z"])
        x["vM"] = fl(x["vM"])
    pr("== denominador:", len(P), "pasadas con alerta MIROVA; ventana", min(x["hora_utc"] for x in P), "a",
       max(x["hora_utc"] for x in P), "| noches", len({x["hora_utc"][:10] for x in P}))

    # ---------------- clasificación del resultado de K por alerta
    def clase(x, pref="NK"):
        pc = fl(x[f"{pref}_pc"])
        nan = fl(x[f"{pref}_nanom"])
        if pc is None and not nan:
            return "a_no_detecta"
        if not pc or pc <= 0:
            return "b_detecta_0MW"
        return "c_con_VRP"
    pr("\n== (1) QUÉ LE PASA A K EN CADA ALERTA DE MIROVA (runner N, gránulo nativo)")
    for tramo, sel in (("z<30", lambda z: z < 30), ("z>=30", lambda z: z >= 30)):
        S = [x for x in P if sel(x["z"])]
        pr(f"{tramo} n={len(S)}:", dict(sorted(collections.Counter(clase(x) for x in S).items())),
           "| K2:", dict(sorted(collections.Counter(clase(x, 'NK2') for x in S).items())))
    pr("control: K2 con clase distinta de K:", sum(1 for x in P if clase(x) != clase(x, "NK2")))
    pr("Spearman cenit contra (clase a o b = 1):",
       f"{spearman([x['z'] for x in P], [1.0 if clase(x) != 'c_con_VRP' else 0.0 for x in P]):+.3f}",
       "barajado", tuple(round(v, 3) for v in barajado([x["z"] for x in P],
                                                         [1.0 if clase(x) != "c_con_VRP" else 0.0 for x in P])))
    pr("Spearman cenit contra (clase a = 1):",
       f"{spearman([x['z'] for x in P], [1.0 if clase(x) == 'a_no_detecta' else 0.0 for x in P]):+.3f}",
       "barajado", tuple(round(v, 3) for v in barajado([x["z"] for x in P],
                                                         [1.0 if clase(x) == "a_no_detecta" else 0.0 for x in P])))
    pr("\n-- en las 'a' (K no detecta): ¿qué hace la grilla de MIROVA (C) y la grilla con el fondo de K?")
    for x in sorted(P, key=lambda y: y["z"]):
        if clase(x) == "a_no_detecta":
            pr(f"  {x['hora_utc']} z {x['z']:5.1f} vM {x['vM']:.2f} C {fl(x['C_vrp']) or 0:.3f} "
               f"C_fan525_rec {fl(x['C_fan525_rec_vrp']) or 0:.3f} todoK525 {fl(x['todoK525_vrp']) or 0:.3f} "
               f"distM {x['distM']}")
    pr("\n-- en las 'b' (K detecta con 0,0 MW): F (fondo del código, nativo) y C")
    for x in sorted(P, key=lambda y: y["z"]):
        if clase(x) == "b_detecta_0MW":
            pr(f"  {x['hora_utc']} z {x['z']:5.1f} vM {x['vM']:.2f} NF_pc {fl(x['NF_pc']) or 0:.3f} "
               f"C {fl(x['C_vrp']) or 0:.3f} t_bg {x['k_t_bg']} k_dcen {fl(x['k_dcen_km'])}")

    # ---------------- fondo
    pr("\n== (2) FONDO: anillo de K contra fondo local del código (radiancia M13 y BT equivalente)")
    filas = []
    for x in P:
        tbg = fl(x["k_t_bg"])
        a525 = fl(x["anillo525_L_med"])
        cl, cn = fl(x["C_Lbk"]), fl(x["C_npix"])
        ch = fl(x["C_Lhot"])
        r = {"z": x["z"], "L_tbgK": float(bt_to_spectral_radiance(np.float64(tbg), M13_LAMBDA)) if tbg else None,
             "L_a525": a525, "Lbk_cod_px": cl / cn if cl and cn else None, "Lhot_px": ch / cn if ch and cn else None}
        r["BT_a525"] = planck_inv(a525) if a525 else None
        r["BT_cod"] = planck_inv(r["Lbk_cod_px"]) if r["Lbk_cod_px"] else None
        r["BT_hot"] = planck_inv(r["Lhot_px"]) if r["Lhot_px"] else None
        filas.append(r)
    pares = [(r["L_tbgK"], r["L_a525"]) for r in filas if r["L_tbgK"] and r["L_a525"]]
    pr("P1 (i) Planck(t_bg de K) / mediana del anillo 5-25 en la grilla:", q([a / b for a, b in pares]))
    pr("BT anillo 5-25 (grilla) - BT fondo del código bajo los alertados de C, K:")
    linea(pr, "  dBT anillo-código", [(r["z"], r["BT_a525"] - r["BT_cod"]) for r in filas
                                     if r["BT_a525"] and r["BT_cod"]])
    linea(pr, "  dBT caliente-código", [(r["z"], r["BT_hot"] - r["BT_cod"]) for r in filas
                                       if r["BT_hot"] and r["BT_cod"]])
    linea(pr, "  dBT caliente-anillo", [(r["z"], r["BT_hot"] - r["BT_a525"]) for r in filas
                                       if r["BT_hot"] and r["BT_a525"]])
    linea(pr, "  t_bg K (record)", [(r["z"], planck_inv(r["L_tbgK"])) for r in filas if r["L_tbgK"]])

    # ---------------- sin ceros
    pr("\n== (3) RAZÓN SIN CEROS (sólo pasadas donde el brazo da VRP > 0)")
    for nombre, col in (("N K pc", "NK_pc"), ("N F pc", "NF_pc"), ("S", "S_vrp"), ("C", "C_vrp"),
                        ("C_fan525_rec", "C_fan525_rec_vrp"), ("todoK525", "todoK525_vrp"),
                        ("todoK525_fcodigo", "todoK525_fcodigo_vrp"), ("C_sinhalo", "C_sinhalo_vrp")):
        linea(pr, nombre, [(x["z"], fl(x[col]) / x["vM"]) for x in P if (fl(x[col]) or 0) > 0])
    pr("\n-- y en el subconjunto común (K publica y C da VRP > 0)")
    com = [x for x in P if (fl(x["NK_pc"]) or 0) > 0 and (fl(x["C_vrp"]) or 0) > 0]
    for nombre, col in (("N K pc", "NK_pc"), ("N F pc", "NF_pc"), ("C", "C_vrp"), ("todoK525", "todoK525_vrp"),
                        ("todoK525_fcodigo", "todoK525_fcodigo_vrp")):
        linea(pr, nombre, [(x["z"], max(fl(x[col]) or 0, 0) / x["vM"]) for x in com])

    # ---------------- robustez
    def r0(x, col):
        v = fl(x[col])
        return max(v, 0.0) / x["vM"] if v else 0.0
    BR = {"N K pc": "NK_pc", "N F pc": "NF_pc", "S": "S_vrp", "C": "C_vrp", "C_fan525_rec": "C_fan525_rec_vrp",
          "todoK525": "todoK525_vrp", "todoK525_fcodigo": "todoK525_fcodigo_vrp"}
    pr("\n== (4a) sólo filas CONS (A119), con ceros")
    S = [x for x in P if x["srcM"] == "CONS"]
    for b, col in BR.items():
        linea(pr, b, [(x["z"], r0(x, col)) for x in S])
    pr("\n== (4b) dejar una noche fuera: Spearman [mín, máx], réplicas FUERA del barajado, mediana z<30 [mín, máx]")
    noches = sorted({x["hora_utc"][:10] for x in P})
    for b, col in BR.items():
        sps, fuera, mlo = [], 0, []
        for n in noches:
            T = [x for x in P if x["hora_utc"][:10] != n]
            z = [x["z"] for x in T]
            r = [r0(x, col) for x in T]
            sp = spearman(z, r)
            bj = barajado(z, r)
            sps.append(sp)
            fuera += sp < bj[0] or sp > bj[1]
            mlo.append(med([v for a, v in zip(z, r) if a < 30]))
        pr(f"{b:18s} Spearman [{min(sps):+.3f}, {max(sps):+.3f}] FUERA {fuera}/{len(noches)} | med z<30 "
           f"[{min(mlo):.3f}, {max(mlo):.3f}]")
    pr("\n== (4c) corte alternativo del cenit (40°), con ceros")
    for b, col in BR.items():
        linea(pr, b + " (corte 40)", [(x["z"], r0(x, col)) for x in P], corte=40.0)
    (AQUI / "s04_salida.txt").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
