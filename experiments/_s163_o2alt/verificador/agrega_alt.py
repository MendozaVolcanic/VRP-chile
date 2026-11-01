import json, math, numpy as np
from collections import defaultdict
from math import comb
D = json.load(open("rerun_pareo.json")); esc = D["escenas"]; mir = {p: v[0] for p, v in D["mirova"].items()}
VAR = ("matlab", "shim", "r2", "o1")
pares = [s for s in esc if s["pasada"] in mir and all(s[v] > 0 for v in VAR)]
uno = [s for s in pares if s["npix"] == 1]
print("escenas 1 px pareadas", len(uno), "pasadas", sorted({s['pasada'] for s in uno}))
def agreg(lista, err, nombre, agg=np.median, por="pasada"):
    g = defaultdict(list)
    for s in lista: g[s["pasada"] if por == "pasada" else s["pasada"].split("_")[0]].append(s)
    fila = {}
    for v in VAR:
        e = [agg([err(s[v], mir[s["pasada"]]) for s in ss]) for ss in g.values()]
        fila[v] = float(np.median(e)); fila[v + "_pp"] = e
    print(f"{nombre:55s} n={len(g):2d} | " + " ".join(f"{v}={fila[v]:.4f}" for v in VAR))
    return fila, g
e_log = lambda x, m: abs(math.log(x/m)); e_rel = lambda x, m: abs(x/m - 1); e_sq = lambda x, m: math.log(x/m)**2
for nom, err in (("|log|", e_log), ("|razon-1| (sin log)", e_rel), ("log^2", e_sq)):
    for aggn, agg in (("mediana", np.median), ("media", np.mean)):
        agreg(uno, err, f"1px por pasada, {nom}, {aggn} sobre variantes", agg)
agreg(uno, e_log, "1px por VOLCAN (|log|, mediana)", por="volcan")
# solo escena guardada lineal caja_def (la del pipeline por defecto) de cualquier npix
d = [s for s in pares if s["familia"] == "chile_guardada" and s["metodo"] == "linear" and s["caja"] == "caja_def"]
agreg(d, e_log, "escena por defecto (3 pasadas), |log|")
# por ESCENA (sin resumir; no independiente) en 1 px
print("\nPor escena de 1 px (no independientes):")
for v in VAR:
    print(v, "mediana |log|", round(float(np.median([e_log(s[v], mir[s['pasada']]) for s in uno])), 4), " media", round(float(np.mean([e_log(s[v], mir[s['pasada']]) for s in uno])), 4))
# pasadas informativas: MATLAB difiere de alguna otra variante (en alguna escena de 1 px)
info = sorted({s["pasada"] for s in uno if any(abs(s[v]/s["matlab"]-1) > 1e-9 for v in VAR[1:])})
print("\npasadas de 1 px donde las variantes difieren:", info)
g = defaultdict(list)
for s in uno: g[s["pasada"]].append(s)
for p in info:
    # entre escenas de la pasada donde difieren, quien queda mas cerca de MIROVA (por escena)
    for v in VAR[1:]:
        sc = [(e_log(s["matlab"], mir[p]), e_log(s[v], mir[p])) for s in g[p] if abs(s[v]/s["matlab"]-1) > 1e-9]
        if sc:
            print(f"  {p:38s} {v:5s}: escenas donde difiere {len(sc)}; MATLAB mas cerca en {sum(a<b for a,b in sc)}, mas lejos en {sum(a>b for a,b in sc)}")
# prueba de signos exacta sobre pasadas informativas: MATLAB vs mejor otro, por pasada (mediana de |log| de las escenas donde difiere)
w = l = 0
for p in info:
    am = np.median([e_log(s["matlab"], mir[p]) for s in g[p]])
    ao = min(np.median([e_log(s[v], mir[p]) for s in g[p]]) for v in VAR[1:])
    if am < ao - 1e-9: w += 1
    elif am > ao + 1e-9: l += 1
print(f"MATLAB vs MEJOR de los otros tres, por pasada informativa: gana {w}, pierde {l}, de {len(info)}")
# prueba de signos exacta bilateral con n informativas contra shim
def sign_p(k, n): return min(1.0, 2*sum(comb(n, i) for i in range(0, min(k, n-k)+1))/2**n)
for v in VAR[1:]:
    w = l = 0
    for p in info:
        am = np.median([e_log(s["matlab"], mir[p]) for s in g[p]]); av = np.median([e_log(s[v], mir[p]) for s in g[p]])
        if am < av - 1e-9: w += 1
        elif am > av + 1e-9: l += 1
    n = w + l
    print(f"signos vs {v}: MATLAB mejor {w}, peor {l}; p bilateral exacto = {sign_p(w, n) if n else float('nan'):.3f} (n={n})")
# Potencia minima: con n informativas = k, la prueba de signos exacta nunca llega a p<0.05 si k<6
print("n minimo de pasadas informativas para p<0.05 bilateral en la prueba de signos (todas a favor):", next(n for n in range(1, 20) if 2/2**n < 0.05))
