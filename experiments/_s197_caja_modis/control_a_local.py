# -*- coding: utf-8 -*-
# S197: dónde difiere el brazo A local (recortes float32) del A guardado por Actions (float64). Sólo lectura.
# Uso: python control_a_local.py <carpeta_artefactos_d36> <salida_ab_caja>
import sys, json, glob, collections
from pathlib import Path
act = {}
for f in glob.glob(str(Path(sys.argv[1]) / "*" / "p1_resultados_*.json")):
    for p in json.load(open(f, encoding="utf-8"))["pasadas"]:
        if p.get("estado") == "ok":
            act[(p["volcan"], p["dt"])] = p["brazos"]["A"]
loc = {(p["volcan"], p["dt"]): p["brazos"]["A"] for p in json.load(open(Path(sys.argv[2]) / "x" / "p1_resultados_0.json",
                                                                       encoding="utf-8"))["pasadas"] if p.get("estado") == "ok"}
PUB = ("vrp_mw", "n", "dc", "pc_vrp", "pc_dist", "pc_n", "final_dist", "celdas", "motivo", "n_abs", "n_p1", "n_p2")
campos = collections.Counter()
pub_dif = []
for k, a in act.items():
    l = loc[k]
    if a is None or l is None:
        if (a is None) != (l is None):
            pub_dif.append({"pasada": k, "campos": ["record None en uno solo"], "actions": a is None, "local": l is None})
        campos.update(["ambos_None"] if a is None and l is None else [])
        continue
    dif = [c for c in a if json.dumps(a[c], sort_keys=True) != json.dumps(l.get(c), sort_keys=True)]
    campos.update(dif)
    if any(c in PUB for c in dif):
        pub_dif.append({"pasada": k, "campos": [c for c in dif if c in PUB],
                        **{c: [a.get(c), l.get(c)] for c in dif if c in PUB and c != "celdas"}})
print("pasadas:", len(act), "| campos que difieren (n pasadas):", dict(campos))
print("pasadas con algún campo de detección o publicación distinto:", len(pub_dif))
for x in pub_dif:
    print("  ", x)
