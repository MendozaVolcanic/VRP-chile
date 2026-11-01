# -*- coding: utf-8 -*-
"""F4-01: ¿donde esta el escalon en la serie que ve el operador (fecha de observacion) y donde lo marca el tablero?
P1: si el predicado no cambiara con K, la fraccion publicada seria igual a ambos lados de cualquier fecha; el
   control positivo es el par C0 (tag pre-s154-reproc-k-datos) contra K (worktree) sobre LAS MISMAS pasadas.
P2: 'pub' sale del node (aborta si cae). Denominador: records V375 nocturnos de los 11 Tier A por dia.
"""
import io, json, sys, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
L = lambda f: [json.loads(x) for x in open(f, encoding="utf-8")]
M = L("main_jul_oct.jsonl"); T = L("tag_c0_ventana.jsonl")
# 1) serie diaria V375, fraccion publicada, y regimen
d = collections.defaultdict(lambda: [0, 0, collections.Counter()])
for r in M:
    if r["b"] != "VIIRS375": continue
    e = d[r["noche"]]; e[0] += r["pub"]; e[1] += 1; e[2][r["reg"]] += 1
print("dia        pub/n  frac  regimen")
for k in sorted(d):
    if "2026-09-10" <= k <= "2026-10-19":
        p, n, c = d[k]; print(k, f"{p:3d}/{n:3d} {p/n:.2f}", dict(c))
# 2) por regimen, toda la tabla
for b in ("VIIRS375", "VIIRS750", "MODIS"):
    for per, lo, hi in (("C0 29ago-17sep", "2026-08-29", "2026-09-17"), ("K 18sep-17oct", "2026-09-18", "2026-10-17"),
                        ("K? 18oct-19oct", "2026-10-18", "2026-10-19")):
        s = [r for r in M if r["b"] == b and lo <= r["noche"] <= hi]
        print(b, per, "n", len(s), "pub", sum(r["pub"] for r in s), f"{sum(r['pub'] for r in s)/max(1,len(s)):.3f}",
              dict(collections.Counter(r["reg"] for r in s)))
# 3) pareado mismas pasadas: tag (C0) vs main (K)
km = {(r["vol"], r["dt"], r["sensor"]): r for r in M}
par = collections.Counter()
for r in T:
    k = (r["vol"], r["dt"], r["sensor"]); m = km.get(k)
    if m is None: par["sin_par"] += 1; continue
    par[(r["b"], "tagC0reg=" + r["reg"], "mainreg=" + m["reg"], r["pub"], m["pub"])] += 1
for k, v in sorted(par.items(), key=str): print("PAR", k, v)
# 4) Chillan, publicaciones V375 por noche
print("Chillan V375 pub por noche (main):")
for k in sorted(d):
    pass
ch = collections.defaultdict(lambda: [0, 0])
for r in M:
    if r["vol"] == "NevadosDeChillan" and r["b"] == "VIIRS375" and "2026-09-08" <= r["noche"] <= "2026-09-28":
        ch[r["noche"]][0] += r["pub"]; ch[r["noche"]][1] += 1
print({k: tuple(v) for k, v in sorted(ch.items())})
chT = collections.defaultdict(lambda: [0, 0])
for r in T:
    if r["vol"] == "NevadosDeChillan" and r["b"] == "VIIRS375" and r["noche"] <= "2026-09-28":
        chT[r["noche"]][0] += r["pub"]; chT[r["noche"]][1] += 1
print("Chillan V375 en el tag C0 (mismas noches):", {k: tuple(v) for k, v in sorted(chT.items())})
