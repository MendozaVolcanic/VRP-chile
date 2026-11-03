# -*- coding: utf-8 -*-
"""v05 (verificador S173 ver_tupun375): ¿los 23 pares de la via (afirmacion 2) representan a los 168 de K (afirmacion 1)?
POR QUE: la via se mide en 23 pasadas elegidas por los lotes retrospectivos; si esas 23 son distintas en cenit, plataforma,
magnitud de MIROVA, fuente (CONS/OCR) o en la razon de K, el 1,01 / 1,02 no se puede extrapolar a los 168.
Mide: razon K/M en B contra el resto (toda la ventana y la ventana de los lotes), cenit, plataforma, VRP de MIROVA, src;
prueba de rangos (Mann-Whitney U con aproximacion normal, sin scipy) de K/M y de z entre B y resto.
P1: si B fuera una copia de A, todas las diferencias serian 0; control: comparar un subconjunto aleatorio de 23 de A
contra el resto (200 sorteos, semilla 173) y ver donde cae la diferencia de medianas real.
Uso: python -B v05_representatividad.py r01_k_pasadas.csv r03_v375e_pasadas.csv v05
"""
import csv, json, math, random, statistics, sys
from collections import Counter
KCSV, VCSV, PRE = sys.argv[1:4]
L = []
def pr(*x):
    s = " ".join(str(y) for y in x); print(s); L.append(s)
def f(x):
    try:
        y = float(x); return None if math.isnan(y) else y
    except (TypeError, ValueError):
        return None
def med(xs):
    xs = [x for x in xs if x is not None]; return round(statistics.median(xs), 3) if xs else None
def mwu(a, b):
    """U de Mann-Whitney, z normal con empates ignorados; devuelve (U, z, p bilateral aprox)."""
    allv = sorted([(x, 0) for x in a] + [(x, 1) for x in b])
    rk, i = {}, 0
    ranks = [0.0] * len(allv)
    while i < len(allv):
        j = i
        while j + 1 < len(allv) and allv[j + 1][0] == allv[i][0]: j += 1
        for k in range(i, j + 1): ranks[k] = (i + j) / 2 + 1
        i = j + 1
    R1 = sum(r for r, (x, g) in zip(ranks, allv) if g == 0)
    n1, n2 = len(a), len(b)
    U = R1 - n1 * (n1 + 1) / 2
    mu, sd = n1 * n2 / 2, math.sqrt(n1 * n2 * (n1 + n2 + 1) / 12)
    z = (U - mu) / sd
    p = math.erfc(abs(z) / math.sqrt(2))
    return round(U, 1), round(z, 2), round(p, 3)

K = [r for r in csv.DictReader(open(KCSV, encoding="utf-8")) if r["b"] == "VIIRS375"]
A = [r for r in K if f(r["vrp_M"]) and f(r["vrp_M"]) > 0 and r["pub"] == "1" and f(r["disp"]) and f(r["disp"]) > 0]
V = {(r["sensor"], r["dt"]): r for r in csv.DictReader(open(VCSV, encoding="utf-8"))}
B = [r for r in A if (r["sensor"], r["dt"]) in V and V[(r["sensor"], r["dt"])]["via_pub"] == "1" and f(V[(r["sensor"], r["dt"])]["via_disp"]) and f(V[(r["sensor"], r["dt"])]["via_disp"]) > 0]
enlote = [r for r in A if (r["sensor"], r["dt"]) in V]
pr(f"A (K pares) n {len(A)} ventana {min(r['dt'] for r in A)}..{max(r['dt'] for r in A)}; en lotes {len(enlote)}; B (K y via publicadas) n {len(B)} ventana {min(r['dt'] for r in B)}..{max(r['dt'] for r in B)}")
pr(f"  pasadas de los lotes: {len(V)}; con K publicada y alerta MIROVA pero via NO publicada: {len(enlote) - len(B)}: {[(r['dt'], r['sensor'], r['vrp_M'], r['src_M'], V[(r['sensor'], r['dt'])]['via_dc'], V[(r['sensor'], r['dt'])]['via_vrp_rec']) for r in enlote if r not in B]}")
resto = [r for r in A if r not in B]
VL = ("2026-04-04", "2026-10-21")
restoL = [r for r in resto if VL[0] <= r["dt"][:10] <= VL[1]]
res = {}
def comp(nom, X, Y):
    rx = [f(r["disp"]) / f(r["vrp_M"]) for r in X]; ry = [f(r["disp"]) / f(r["vrp_M"]) for r in Y]
    zx = [f(r["z"]) for r in X]; zy = [f(r["z"]) for r in Y]
    mx = [f(r["vrp_M"]) for r in X]; my = [f(r["vrp_M"]) for r in Y]
    d = {"n": [len(X), len(Y)], "K/M mediana": [med(rx), med(ry)], "K/M z<30": [med([q for q, z in zip(rx, zx) if z < 30]), med([q for q, z in zip(ry, zy) if z < 30])],
         "K/M z>=30": [med([q for q, z in zip(rx, zx) if z >= 30]), med([q for q, z in zip(ry, zy) if z >= 30])],
         "MWU K/M (U,z,p)": mwu(rx, ry), "z mediana": [med(zx), med(zy)], "frac z>=30": [round(sum(1 for z in zx if z >= 30) / len(zx), 2), round(sum(1 for z in zy if z >= 30) / len(zy), 2)],
         "frac z>=50": [round(sum(1 for z in zx if z >= 50) / len(zx), 2), round(sum(1 for z in zy if z >= 50) / len(zy), 2)], "MWU z (U,z,p)": mwu(zx, zy),
         "VRP MIROVA mediana": [med(mx), med(my)], "MWU VRP_M": mwu(mx, my), "frac M>=1MW": [round(sum(1 for m in mx if m >= 1) / len(mx), 2), round(sum(1 for m in my if m >= 1) / len(my), 2)],
         "plataformas": [dict(Counter(r["sensor"] for r in X)), dict(Counter(r["sensor"] for r in Y))], "src_M": [dict(Counter(r["src_M"] for r in X)), dict(Counter(r["src_M"] for r in Y))]}
    pr(f"== {nom}"); [pr(f"   {k}: {v}") for k, v in d.items()]
    res[nom] = d
comp("B contra resto de A (toda la ventana)", B, resto)
comp("B contra resto de A dentro de la ventana de los lotes 2026-04-04..2026-10-21", B, restoL)
# control P1: sorteos de 23 de A
rnd = random.Random(173)
rA = {(r["sensor"], r["dt"]): f(r["disp"]) / f(r["vrp_M"]) for r in A}
real = med([rA[(r["sensor"], r["dt"])] for r in B]) - med([rA[(r["sensor"], r["dt"])] for r in resto])
sims = []
for _ in range(200):
    s = rnd.sample(A, len(B)); ks = {(r["sensor"], r["dt"]) for r in s}
    sims.append(med([q for k, q in rA.items() if k in ks]) - med([q for k, q in rA.items() if k not in ks]))
sims.sort()
res["control_sorteo"] = {"dif_mediana_real_B_menos_resto": round(real, 3), "sorteos_[2.5,50,97.5]": [round(sims[5], 3), round(statistics.median(sims), 3), round(sims[194], 3)]}
pr(f"== control: diferencia de medianas K/M (B - resto) real {round(real, 3)}; 200 sorteos de {len(B)} de A: [{round(sims[5], 3)}; {round(statistics.median(sims), 3)}; {round(sims[194], 3)}]")
# cociente de medianas vs mediana de cocientes (via/K)
vb = [(f(V[(r['sensor'], r['dt'])]["via_disp"]), f(r["disp"]), f(r["vrp_M"]), f(r["z"])) for r in B]
for nom, cond in (("z<30", lambda z: z < 30), ("z>=30", lambda z: z >= 30)):
    s = [t for t in vb if cond(t[3])]
    pr(f"  {nom}: mediana de via/K {med([a / b for a, b, _, _ in s])}; cociente de medianas (via/M)/(K/M) {round(med([a / m for a, _, m, _ in s]) / med([b / m for _, b, m, _ in s]), 3)}; n {len(s)}")
# A104 en B: codigo que escribio los records K de B
pr(f"  codigo_sha de K en B: {Counter((r['sha'] or '')[:9] for r in B)}; en resto: {Counter((r['sha'] or '')[:9] for r in resto).most_common(3)}")
json.dump(res, open(PRE + "_salida.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
open(PRE + "_salida.txt", "w", encoding="utf-8").write("\n".join(L) + "\n")
