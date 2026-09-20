# -*- coding: utf-8 -*-
"""V-12: el 0,995 'a igual conteo' de A99. Camino propio: lee 02_pares.csv con csv (sin pandas, sin el script 04) y recalcula
R = pub_mw/osf_mw, F_hot = (hot1_ours-bk1)/ex1, F_bg = F_ex/F_hot, en el subconjunto pub_n == Npix de 375 m.
Ademas: dispersion de R (una media geometrica de ~1 puede esconder una nube ancha), reparto por n de pixeles y por volcan, y bootstrap.
(1) roto? control: R debe ser = F_n*F_ex par a par (identidad de la descomposicion); se imprime el error maximo.
(2) muerto? se imprime n del subconjunto y del complemento; si el filtro no filtrara darian lo mismo.
Limite: 02_pares.csv es un intermedio de S139 (pareo contra el OSF v2.5, 2025-02-15 a 2025-12-01, regimen previo a #535); no lo regenere."""
import csv, math, io, sys, random
from collections import Counter, defaultdict
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
P = "../../_s139_audit/magnitud/02_pares.csv"
def fl(x):
    try: return float(x)
    except Exception: return float("nan")
rows = [{k: v for k, v in r.items()} for r in csv.DictReader(open(P, encoding="utf-8"))]
gm = lambda xs: math.exp(sum(math.log(x) for x in xs) / len(xs))
base = []
for r in rows:
    if fl(r["res"]) != 375 or math.isnan(fl(r["Lbg_imp"])) or not fl(r["R"]) > 0: continue
    r["Fhot"] = (fl(r["hot1_ours"]) - fl(r["bk1"])) / fl(r["ex1"])
    base.append(r)
print("pares 375 con fondo implicito y R>0:", len(base))
ig = [r for r in base if fl(r["pub_n"]) == fl(r["Npix"])]; di = [r for r in base if fl(r["pub_n"]) != fl(r["Npix"])]
print("igual conteo:", len(ig), "| de ellos con F_hot<=0 (el script 04 los descarta):", sum(1 for r in ig if not r["Fhot"] > 0), "| conteo distinto:", len(di))
ig = [r for r in ig if r["Fhot"] > 0]
err = max(abs(fl(r["R"]) - fl(r["F_n"]) * fl(r["F_ex"])) for r in ig); print("control identidad R=F_n*F_ex, error max:", round(err, 6))
R = [fl(r["R"]) for r in ig]; Fh = [r["Fhot"] for r in ig]; Fb = [fl(r["F_ex"]) / r["Fhot"] for r in ig]
print(f"n={len(ig)}  R gm={gm(R):.3f}  F_hot gm={gm(Fh):.3f}  F_bg gm={gm(Fb):.3f}  producto={gm(Fh)*gm(Fb):.3f}")
Rs = sorted(R); q = lambda p: Rs[int(p * (len(Rs) - 1))]
print(f"dispersion de R: p10={q(.1):.2f} p25={q(.25):.2f} mediana={q(.5):.2f} p75={q(.75):.2f} p90={q(.9):.2f} | dentro de 0.8-1.25: {sum(0.8<=x<=1.25 for x in R)} de {len(R)} | fuera de 0.5-2: {sum(not 0.5<=x<=2 for x in R)}")
print("por n de pixeles:", {k: (v, round(gm([fl(r['R']) for r in ig if int(fl(r['Npix'])) == k]), 3)) for k, v in sorted(Counter(int(fl(r["Npix"])) for r in ig).items())})
print("fraccion de un pixel:", sum(1 for r in ig if int(fl(r["Npix"])) == 1), "de", len(ig))
pv = defaultdict(list)
for r in ig: pv[r["vol"]].append(r)
print("por volcan (n, R gm, F_hot gm, F_bg gm):")
for v, g in sorted(pv.items(), key=lambda x: -len(x[1])):
    print(f"   {v:22s} {len(g):4d}  {gm([fl(r['R']) for r in g]):.3f}  {gm([r['Fhot'] for r in g]):.3f}  {gm([fl(r['F_ex'])/r['Fhot'] for r in g]):.3f}")
random.seed(146); bs = sorted(gm([random.choice(R) for _ in R]) for _ in range(2000)); print("bootstrap R gm IC95:", round(bs[50], 3), round(bs[1949], 3))
# sin el volcan dominante
top = max(pv, key=lambda v: len(pv[v])); resto = [fl(r["R"]) for r in ig if r["vol"] != top]
print(f"sin {top} (n={len(pv[top])}): R gm del resto = {gm(resto):.3f} (n={len(resto)})")
print("todos los pares 375 (no solo igual conteo): R gm =", round(gm([fl(r['R']) for r in base if r['Fhot'] > 0]), 3), "| fraccion con igual conteo:", round(len(ig) / len([r for r in base if r['Fhot'] > 0]), 3))
