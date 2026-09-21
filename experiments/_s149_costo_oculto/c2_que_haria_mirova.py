# -*- coding: utf-8 -*-
"""S149. Que haria MIROVA en las pasadas sin_info de noches con alerta? No lo sabemos pasada a pasada
(el scraper no las tiene), pero si se puede medir en las pasadas ETIQUETADAS de la misma clase:
pasadas V375 con OTRA pasada positiva esa noche en el volcan (dejando fuera la propia). Ahi MIROVA
si dijo alerta o rutina. Se compara la tasa de alerta de MIROVA con la tasa de publicacion de B y F,
por zona del barrido. Solo lee tabla.json."""
import json, collections, sys, io
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
T = json.loads((AQUI.parent / "_s148_verificador_resultado" / "tabla.json").read_text(encoding="utf-8"))
B, F = "_s146_ab_sin_test1", "_s147_ab_sin_test1_max"
rows = []
for k, v in T.items():
    vol, b, dt = k.split("|")
    if b == "VIIRS375" and v[B]["z"] is not None:
        rows.append(dict(vol=vol, dt=dt, n=dt[:10], lab=v[B]["lab"], pB=v[B]["pub"], pF=v[F]["pub"], z=v[B]["z"]))
npos = collections.Counter((r["vol"], r["n"]) for r in rows if r["lab"] == "pos")
def otra_pos(r): return npos[(r["vol"], r["n"])] - (1 if r["lab"] == "pos" else 0) >= 1
def zona(z): return "nadir" if z < 36 else ("medio" if z < 52 else "borde")
print("Pasadas V375 con OTRA pasada positiva de MIROVA esa noche en el volcan")
print("%-7s | %-44s | %-30s" % ("zona", "ETIQUETADAS: n, MIROVA alerta, B pub, F pub", "SIN_INFO: n, B pub, F pub"))
tot = collections.Counter()
for zn in ("nadir", "medio", "borde", "todas"):
    e = [r for r in rows if otra_pos(r) and r["lab"] in ("pos", "neg_limpio") and (zn == "todas" or zona(r["z"]) == zn)]
    s = [r for r in rows if otra_pos(r) and r["lab"] == "sin_info" and (zn == "todas" or zona(r["z"]) == zn)]
    f = lambda x, n: "%3d (%4.1f %%)" % (x, 100 * x / n if n else 0)
    print("%-7s | n %3d  MIROVA %s  B %s  F %s | n %3d  B %s  F %s" % (zn, len(e), f(sum(r["lab"] == "pos" for r in e), len(e)),
          f(sum(r["pB"] for r in e), len(e)), f(sum(r["pF"] for r in e), len(e)), len(s), f(sum(r["pB"] for r in s), len(s)), f(sum(r["pF"] for r in s), len(s))))
print("\nEn las etiquetadas: acuerdo pasada a pasada con MIROVA (alerta<->publica)")
e = [r for r in rows if otra_pos(r) and r["lab"] in ("pos", "neg_limpio")]
for nom, c in (("B", "pB"), ("F", "pF")):
    tp = sum(1 for r in e if r["lab"] == "pos" and r[c]); fn = sum(1 for r in e if r["lab"] == "pos" and not r[c])
    fp = sum(1 for r in e if r["lab"] != "pos" and r[c]); tn = sum(1 for r in e if r["lab"] != "pos" and not r[c])
    print("  %s: TP %d FN %d FP %d TN %d | acuerdo %.1f %%" % (nom, tp, fn, fp, tn, 100 * (tp + tn) / len(e)))
print("\nNulo de la clase: mismas tasas en pasadas SIN otra positiva esa noche (etiquetadas)")
e0 = [r for r in rows if not otra_pos(r) and r["lab"] in ("pos", "neg_limpio")]
print("  n %d | MIROVA alerta %.1f %% | B %.1f %% | F %.1f %%" % (len(e0), 100 * sum(r["lab"] == "pos" for r in e0) / len(e0), 100 * sum(r["pB"] for r in e0) / len(e0), 100 * sum(r["pF"] for r in e0) / len(e0)))
