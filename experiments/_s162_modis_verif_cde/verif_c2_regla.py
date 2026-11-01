# -*- coding: utf-8 -*-
"""Verificador CDE, C2: la regla de decisión del lote de negativos (03_regla_decision.py) por OTRO camino.

Las dos preguntas del instrumento:
1. Si la tabla «CONFIRMA sólo con x = 0; INDECIDIBLE 1 a 7; REFUTA desde 8» dependiera de la semilla o del denominador
   elegido, ¿se vería? Sí: se repite el veredicto con 10 semillas distintas y con N_MARCO = 5.093 (el estrato entero) en
   vez de 5.055, y se mira si alguna frontera de x se mueve.
2. Si la regla estuviera rota (no monótona, dos veredictos para el mismo x), ¿se vería? Sí: se recorre x de 0 a 60 para
   n de 300 a 400 y se exige CONFIRMA -> INDECIDIBLE -> REFUTA sin retrocesos.
Control positivo: la cota analítica de Jeffreys (cuantil 97,5 % de Beta(0,5; n + 0,5)) multiplicada por 5.055 tiene que
reproducir el orden de magnitud del tramo positivo del IC (hi - hi_otros).
Denominador: filas congeladas de S159 (149 filas, variante fisica), 20.000 réplicas como el script del auditor.
Uso: python -I verif_c2_regla.py --regla <carpeta de 03_regla_decision.py>
"""
import argparse
import importlib.util
import sys
from pathlib import Path

import numpy as np
from scipy import stats

sys.stdout.reconfigure(encoding="utf-8")
ap = argparse.ArgumentParser()
ap.add_argument("--regla", required=True)
a = ap.parse_args()
spec = importlib.util.spec_from_file_location("regla", Path(a.regla) / "03_regla_decision.py")
R = importlib.util.module_from_spec(spec)
spec.loader.exec_module(R)

F = R.filas()
print("filas:", len(F), "| DeltaE_otros punto:", R.de_otros(F))
de_rep, pp_rep = R.replicas_otros(F, np.random.default_rng(R.SEMILLA))
print(f"IC DeltaE_otros [{np.percentile(de_rep, 2.5):+.2f}, {np.percentile(de_rep, 97.5):+.2f}]")

print("\n== analítico: cuantiles de Jeffreys Beta(x+0,5; n-x+0,5) por 5.055, n = 400")
for x in (0, 1, 2, 7, 8):
    lo, hi = stats.beta.ppf([0.025, 0.975], x + 0.5, 400 - x + 0.5)
    print(f"  x {x}: p en [{lo:.5f}; {hi:.5f}] -> +[{5055 * lo:.1f}; {5055 * hi:.1f}] pasadas; punto -44 + {5055 * x / 400:.1f}")

print("\n== fronteras de x por semilla (n = 400, N_MARCO 5.055)")
fron = {}
for sem in range(163, 173):
    v = []
    for x in range(0, 40):
        r = R.veredicto(x, 400, de_rep, pp_rep, np.random.default_rng(sem))
        v.append(r["veredicto"])
    # primera x INDECIDIBLE y primera x REFUTA
    xi = next((i for i, s in enumerate(v) if s == "INDECIDIBLE"), None)
    xr = next((i for i, s in enumerate(v) if s == "REFUTA"), None)
    mono = all(v[i] != "CONFIRMA" or i < xi for i in range(len(v))) and all(v[i] != "INDECIDIBLE" or (xi <= i < xr) for i in range(len(v)))
    fron[sem] = (xi, xr, mono)
    print(f"  semilla {sem}: CONFIRMA hasta x {xi - 1}, INDECIDIBLE {xi} a {xr - 1}, REFUTA desde {xr}; monótona {mono}")
print("  fronteras distintas entre semillas:", sorted(set((xi, xr) for xi, xr, _ in fron.values())))

print("\n== sensibilidad al denominador: N_MARCO 5.093 en vez de 5.055 (semilla del auditor)")
R.N_MARCO = 5093
v = [R.veredicto(x, 400, de_rep, pp_rep, np.random.default_rng(R.SEMILLA + 1))["veredicto"] for x in range(0, 40)]
xi = next((i for i, s in enumerate(v) if s == "INDECIDIBLE"), None)
xr = next((i for i, s in enumerate(v) if s == "REFUTA"), None)
print(f"  CONFIRMA hasta x {xi - 1}, INDECIDIBLE {xi} a {xr - 1}, REFUTA desde {xr}")
R.N_MARCO = 5055

print("\n== monotonía y n mínimo que confirma con x = 0 (semilla del auditor)")
for n in range(300, 401, 10):
    v = [R.veredicto(x, n, de_rep, pp_rep, np.random.default_rng(R.SEMILLA + 1))["veredicto"] for x in range(0, 60)]
    orden = {"CONFIRMA": 0, "INDECIDIBLE": 1, "REFUTA": 2}
    mono = all(orden[v[i]] <= orden[v[i + 1]] for i in range(len(v) - 1))
    xi = next((i for i, s in enumerate(v) if s == "INDECIDIBLE"), None)
    xr = next((i for i, s in enumerate(v) if s == "REFUTA"), None)
    r0 = R.veredicto(0, n, de_rep, pp_rep, np.random.default_rng(R.SEMILLA + 1))
    print(f"  n {n}: x0 -> {v[0]} (hi {r0['ic'][1]:+.1f}); INDECIDIBLE desde {xi}; REFUTA desde {xr}; monótona {mono}")

print("\n== lo que el IC de x = 0 NO incluye: la cota de Wilson (la 'cota conservadora' del auditor) y qué pasa si el"
      " estrato pos_bajo (censo, 42 de 42) se trata como fijo")
r0 = R.veredicto(0, 400, de_rep, pp_rep, np.random.default_rng(R.SEMILLA + 1))
print(f"  cota conservadora x0 n400: {r0['cota_conservadora']:+.1f} (nunca confirma, declarado por el auditor)")
# pos_bajo fijo: réplicas sólo de neg_pub
import collections
por = collections.defaultdict(list)
for x in F:
    if x["c"] in ("pos_bajo", "neg_pub"):
        por[x["c"]].append(x)
rng = np.random.default_rng(R.SEMILLA)
de2 = np.empty(R.REPLICAS)
for j in range(R.REPLICAS):
    s = list(por["pos_bajo"]) + [por["neg_pub"][k] for k in rng.integers(0, len(por["neg_pub"]), len(por["neg_pub"]))]
    de2[j] = R.de_otros(s)
p = np.random.default_rng(R.SEMILLA + 1).beta(0.5, 400.5, size=R.REPLICAS)
tot = de2 + 5055 * p
print(f"  pos_bajo fijo: IC DeltaE_otros [{np.percentile(de2, 2.5):+.1f}; {np.percentile(de2, 97.5):+.1f}]; con x0 n400 "
      f"IC total [{np.percentile(tot, 2.5):+.1f}; {np.percentile(tot, 97.5):+.1f}] (más angosto: el auditor lo declara y no lo usa)")
