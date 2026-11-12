# -*- coding: utf-8 -*-
"""S181: qué cambia en la historia publicada al aplicar el reemplazo con la vía (PR #994), por volcán y familia.

Antes: data/mirova_equivalent de origin/main (git show). Después: la misma carpeta en el worktree
D:/vrp-trabajo/worktrees/s181-verif-994 tras correr aplicar_via.py --aplicar (sólo en ese worktree, nunca en main).
VRP con el predicado simple del tablero (mirovaEqVrp sin toggle: pc.vrp_mw si distance_class es summit).
Ventana: 2025-02-15 hasta el corte de cada familia. Salida en cambio.txt. Correr desde la raíz del worktree.
"""
import collections
import json
import subprocess

TIER = ["Lascar", "PuyehueCordonCaulle", "Lastarria", "Isluga", "Tupungatito", "PlanchonPeteroa", "Chaiten",
        "Villarrica", "NevadosDeChillan", "Llaima", "Copahue"]
CORTES = {"MODIS": "2026-11-02 17:18", "VIIRS375": "2026-11-11 13:09", "VIIRS750": "2026-11-11 13:22"}


def fam(s):
    s = (s or "").upper()
    return "MODIS" if s.startswith("MODIS") else ("VIIRS750" if s.endswith("_750") else "VIIRS375")


def vrp(r):
    pc = r.get("primary_cluster")
    if not pc:
        return r.get("vrp_mw") or 0
    if r.get("distance_class") and r["distance_class"] != "summit":
        return 0
    return pc.get("vrp_mw") or 0


def resumen(recs):
    out = collections.defaultdict(lambda: [0, 0, 0, set(), 0.0])
    for r in recs:
        t = (r.get("datetime_utc") or "").replace("T", " ")[:16]
        f = fam(r.get("sensor"))
        if not ("2025-02-15" <= t < CORTES[f]):
            continue
        v = vrp(r)
        o = out[f]
        o[0] += 1
        if v > 0:
            o[1] += 1
        if v >= 1:
            o[2] += 1
            o[3].add(t[:10])
            o[4] += v
    return out


tot = {"antes": collections.defaultdict(lambda: [0, 0, 0, 0, 0.0]),
       "despues": collections.defaultdict(lambda: [0, 0, 0, 0, 0.0])}
print("volcan familia | pasadas antes/despues | VRP>0 antes/despues | >=1MW antes/despues | dias>=1MW antes/despues")
for v in TIER:
    a = json.loads(subprocess.run(["git", "show", f"origin/main:data/mirova_equivalent/{v}.json"],
                                  capture_output=True).stdout)["records"]
    b = json.load(open(f"data/mirova_equivalent/{v}.json", encoding="utf-8"))["records"]
    ra, rb = resumen(a), resumen(b)
    for f in CORTES:
        x, y = ra[f], rb[f]
        print(f"{v} {f} | {x[0]}/{y[0]} | {x[1]}/{y[1]} | {x[2]}/{y[2]} | {len(x[3])}/{len(y[3])}")
        for k, z in (("antes", x), ("despues", y)):
            T = tot[k][f]
            T[0] += z[0]; T[1] += z[1]; T[2] += z[2]; T[3] += len(z[3]); T[4] += z[4]
print("TOTAL")
for f in CORTES:
    a, b = tot["antes"][f], tot["despues"][f]
    print(f"{f}: pasadas {a[0]}->{b[0]}  VRP>0 {a[1]}->{b[1]}  >=1MW {a[2]}->{b[2]}  volcan-dias>=1MW {a[3]}->{b[3]}"
          f"  suma MW(>=1) {a[4]:.0f}->{b[4]:.0f}")
