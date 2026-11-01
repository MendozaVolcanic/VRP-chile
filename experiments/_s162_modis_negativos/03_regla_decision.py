# -*- coding: utf-8 -*-
"""S162 MODIS negativos, paso 3: la regla de decision del lote, escrita y probada ANTES de correrlo
(PREREGISTRO.md §5). Sin red y sin resultados del lote nuevo.

POR QUE ASI. El veredicto MISSION de S159 era DeltaE = (alertas bajo 1 MW perdidas - ganadas) + (negativos
encendidos - apagados), ponderado. En MODIS el estrato neg_resto (5.093 pasadas, K no publica en ninguna) solo puede
SUMAR: cada pasada donde el port publique es una publicacion de mas. El bootstrap de S159 re-sorteaba los 37 ceros y
no veia nada (V-1). Aqui las dos partes se tratan por separado y se suman replica a replica:

  DeltaE* = DeltaE_otros*  +  0 (las sorteadas de S159 en neg_resto, conocidas: 0 encendidas)  +  N_marco * p*

  DeltaE_otros*  bootstrap estratificado por clase (pos_bajo, neg_pub) de las filas de S159
                 (filas_lote_s159_modis_fisica.json, congeladas por 02_filas_lote_s159.py), 20.000 replicas.
  p*             tasa de publicacion del port en neg_resto, Beta(x + 1/2, n - x + 1/2) (Jeffreys: con 0 eventos
                 tiene varianza, a diferencia del bootstrap; su intervalo tiene cobertura cercana al 95 % nominal en
                 binomiales con p chico, Brown, Cai y DasGupta 2001, Statistical Science 16:101).
  N_marco        5.055 (el estrato sin las 38 ya sorteadas). Conservador: las pasadas que en el lote resulten no
                 evaluables (volcan fuera del granulo, escena invalida) salen de n, y la tasa de las evaluables se
                 aplica igual a todo el marco.

Veredicto (IC 95 % percentil de DeltaE*): CONFIRMA el GANA si el IC queda entero bajo 0; REFUTA (el port enciende de
mas) si queda entero sobre 0; INDECIDIBLE si contiene 0. Controles de la regla, que tienen que pasar antes de
usarla: (a) con los datos de S159 (0 de 36 evaluables) tiene que dar INDECIDIBLE, como dijo el verificador; (b) con
muchos eventos tiene que poder dar REFUTA; (c) con 0 de 400 tiene que poder dar CONFIRMA (si no, el lote no puede
resolver nada y no vale la pena correrlo).

Uso: python -I 03_regla_decision.py                 (controles y tabla de planificacion)
     python -I 03_regla_decision.py --x 3 --n 392   (veredicto con el resultado del lote)
"""
from __future__ import annotations

import argparse
import collections
import io
import json
import math
import sys
from pathlib import Path

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

AQUI = Path(__file__).resolve().parent
N_MARCO = 5055
N_ESTRATO = 5093
K_NEG = (39, 5132)          # K publica en 39 de 5.132 negativos limpios MODIS (PREREGISTRO de S159, §5 R3)
REPLICAS = 20000
SEMILLA = 162


def filas():
    return json.loads((AQUI / "filas_lote_s159_modis_fisica.json").read_text(encoding="utf-8"))["filas"]


def de_otros(s):
    bp = sum(x["w"] for x in s if x["c"] == "pos_bajo" and x["K"] and not x["X"])
    bg = sum(x["w"] for x in s if x["c"] == "pos_bajo" and not x["K"] and x["X"])
    ne = sum(x["w"] for x in s if x["c"] == "neg_pub" and x["X"] and not x["K"])
    na = sum(x["w"] for x in s if x["c"] == "neg_pub" and x["K"] and not x["X"])
    return (bp - bg) + (ne - na)


def pub_neg_pub(s):
    return sum(x["w"] for x in s if x["c"] == "neg_pub" and x["X"])


def replicas_otros(F, rng):
    por = collections.defaultdict(list)
    for x in F:
        if x["c"] in ("pos_bajo", "neg_pub"):
            por[x["c"]].append(x)
    de = np.empty(REPLICAS)
    pp = np.empty(REPLICAS)
    for j in range(REPLICAS):
        s = []
        for c in sorted(por):
            lst = por[c]
            s += [lst[k] for k in rng.integers(0, len(lst), len(lst))]
        de[j] = de_otros(s)
        pp[j] = pub_neg_pub(s)
    return de, pp


def wilson_sup(k, n, z=1.96):
    p = k / n
    d = 1 + z * z / n
    return (p + z * z / (2 * n) + z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / d


def veredicto(x, n, de_rep, pp_rep, rng, de_punto=-44.0):
    p = rng.beta(x + 0.5, n - x + 0.5, size=len(de_rep))
    tot = de_rep + N_MARCO * p
    lo, hi = np.percentile(tot, [2.5, 97.5])
    if hi < 0:
        v = "CONFIRMA"
    elif lo > 0:
        v = "REFUTA"
    else:
        v = "INDECIDIBLE"
    # R3 (silencio): publicacion ponderada del port en los 5.132 negativos limpios, contra K
    r3 = (pp_rep + N_MARCO * p) / K_NEG[1]
    r3lo, r3hi = np.percentile(r3, [2.5, 97.5])
    r3v = "NO REPRODUCE" if r3lo > K_NEG[0] / K_NEG[1] else "REPRODUCE"
    return {"x": x, "n": n, "dE_punto": de_punto + N_MARCO * x / n, "ic": (float(lo), float(hi)),
            "veredicto": v, "r3_ic": (float(r3lo), float(r3hi)), "r3": r3v,
            "cota_conservadora": float(np.percentile(de_rep, 97.5)) + N_MARCO * wilson_sup(x, n)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--x", type=int, default=None, help="pasadas evaluables del lote donde el port publica")
    ap.add_argument("--n", type=int, default=None, help="pasadas evaluables del lote")
    a = ap.parse_args()
    F = filas()
    assert abs(de_otros(F) - (-44.0)) < 1e-9, "las filas no dan el DeltaE de S159 (-44,0)"
    rng = np.random.default_rng(SEMILLA)
    de_rep, pp_rep = replicas_otros(F, rng)
    print(f"DeltaE_otros (pos_bajo + neg_pub de S159): punto {de_otros(F):+.2f}; bootstrap {REPLICAS} replicas, "
          f"semilla {SEMILLA}: mediana {np.median(de_rep):+.2f}, IC 95 % [{np.percentile(de_rep, 2.5):+.2f}, "
          f"{np.percentile(de_rep, 97.5):+.2f}] (S159 imprimio [-58,8; -29,5] con otro orden del generador)")
    print(f"publicacion ponderada del port en neg_pub: punto {pub_neg_pub(F):.2f}; K en negativos {K_NEG[0]} de "
          f"{K_NEG[1]} = {K_NEG[0] / K_NEG[1]:.4f}")
    if a.x is not None:
        r = veredicto(a.x, a.n, de_rep, pp_rep, np.random.default_rng(SEMILLA + 1))
        print(f"\nVEREDICTO con x = {a.x} de n = {a.n}: DeltaE punto {r['dE_punto']:+.1f}, IC 95 % "
              f"[{r['ic'][0]:+.1f}; {r['ic'][1]:+.1f}] -> {r['veredicto']}; R3 IC [{r['r3_ic'][0]:.4f}; "
              f"{r['r3_ic'][1]:.4f}] -> {r['r3']}; cota conservadora (suma de cotas) {r['cota_conservadora']:+.1f}")
        return 0

    print("\n== controles de la regla")
    c_a = veredicto(0, 36, de_rep, pp_rep, np.random.default_rng(SEMILLA + 1))
    print(f"  (a) datos de S159, 0 de 36 evaluables: IC [{c_a['ic'][0]:+.1f}; {c_a['ic'][1]:+.1f}] -> "
          f"{c_a['veredicto']} (tiene que dar INDECIDIBLE)")
    c_b = veredicto(40, 400, de_rep, pp_rep, np.random.default_rng(SEMILLA + 1))
    print(f"  (b) 40 de 400: IC [{c_b['ic'][0]:+.1f}; {c_b['ic'][1]:+.1f}] -> {c_b['veredicto']} (tiene que dar "
          f"REFUTA)")
    c_c = veredicto(0, 400, de_rep, pp_rep, np.random.default_rng(SEMILLA + 1))
    print(f"  (c) 0 de 400: IC [{c_c['ic'][0]:+.1f}; {c_c['ic'][1]:+.1f}] -> {c_c['veredicto']} (tiene que poder "
          f"dar CONFIRMA)")
    assert c_a["veredicto"] == "INDECIDIBLE" and c_b["veredicto"] == "REFUTA" and c_c["veredicto"] == "CONFIRMA", \
        "la regla no pasa sus controles"
    print("  controles OK")

    print("\n== tabla de planificacion: veredicto segun x (eventos) para cada n evaluable")
    for n in (300, 350, 380, 400):
        filas_t = []
        prev = None
        for x in range(0, 60):
            r = veredicto(x, n, de_rep, pp_rep, np.random.default_rng(SEMILLA + 1))
            if r["veredicto"] != prev:
                filas_t.append((x, r["veredicto"], r["ic"], r["r3"]))
                prev = r["veredicto"]
            if r["veredicto"] == "REFUTA":
                break
        tramos = []
        for k, (x, v, ic, r3) in enumerate(filas_t):
            hasta = filas_t[k + 1][0] - 1 if k + 1 < len(filas_t) else None
            tramos.append(f"x {x}{'' if hasta == x else (' a ' + str(hasta) if hasta is not None else ' o mas')}: {v}")
        print(f"  n {n}: " + " | ".join(tramos))
        for x in (0, 1, 2, 3, 5):
            r = veredicto(x, n, de_rep, pp_rep, np.random.default_rng(SEMILLA + 1))
            print(f"      x {x}: DeltaE punto {r['dE_punto']:+.1f}, IC [{r['ic'][0]:+.1f}; {r['ic'][1]:+.1f}] "
                  f"{r['veredicto']}; R3 IC [{r['r3_ic'][0]:.4f}; {r['r3_ic'][1]:.4f}] {r['r3']}; cota "
                  f"conservadora {r['cota_conservadora']:+.1f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
