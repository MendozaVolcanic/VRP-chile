# -*- coding: utf-8 -*-
"""S149. Reemplazo de C8. El C8 de S147 pide que el contraste quede FUERA del nulo barajado, a dos
colas, y un apagador al azar lo cumple en 200 de 200 semillas (verificador S148, H2): su nulo no esta
centrado donde cae un apagado al azar.

Estadistico nuevo, sobre las pasadas que el CONTROL publica: supervivencia de las positivas menos
supervivencia de los negativos limpios. Nulo: barajar las etiquetas pos/neg SOLO entre las pasadas
publicadas por el control, dentro de cada volcan y sensor. Bajo un apagado al azar dentro del estrato
las etiquetas son intercambiables, asi que el nulo queda CALIBRADO por construccion (A110), y aca
ademas se MIDE. Ojo: calibrado no es centrado en cero. La media del nulo sale positiva (+0,27 en V375)
porque los estratos con muchos negativos son tambien los que mas apaga el brazo; el barajado dentro
del estrato lo absorbe, y por eso el apagador al azar cumple solo 3 de 200. Criterio a UNA cola: observado > p97,5 del nulo.

Se valida con tres casos: (1) apagador al azar, 200 semillas: debe cumplir cerca del 2,5 %;
(2) el brazo F real; (3) corte parejo por magnitud por sensor (apaga lo mas debil primero)."""
import json, random, collections, sys, io
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
T = json.loads((AQUI.parent / "_s148_verificador_resultado" / "tabla.json").read_text(encoding="utf-8"))
B, F = "_s146_ab_sin_test1", "_s147_ab_sin_test1_max"


def selectividad(pares, campo, n_iter=1000, semilla=149):
    """pares: dicts con vol, b, lab, pB (=1 siempre) y el campo de publicacion del brazo."""
    def est(labs):
        pos = [p[campo] for p, l in zip(pares, labs) if l == "pos"]; neg = [p[campo] for p, l in zip(pares, labs) if l == "neg_limpio"]
        return sum(pos) / len(pos) - sum(neg) / len(neg)
    obs = est([p["lab"] for p in pares]); rnd = random.Random(semilla)
    g = collections.defaultdict(list)
    for i, p in enumerate(pares): g[(p["vol"], p["b"])].append(i)
    nul = []
    for _ in range(n_iter):
        labs = [None] * len(pares)
        for idx in g.values():
            ls = [pares[i]["lab"] for i in idx]; rnd.shuffle(ls)
            for i, l in zip(idx, ls): labs[i] = l
        nul.append(est(labs))
    nul.sort()
    return obs, nul[int(.025 * (len(nul) - 1))], nul[int(.975 * (len(nul) - 1))], sum(nul) / len(nul)


for sensor in ("VIIRS375", "VIIRS750"):
    pares = []
    for k, v in T.items():
        vol, b, dt = k.split("|")
        if b == sensor and v[B]["lab"] in ("pos", "neg_limpio") and v[B]["pub"]:
            pares.append(dict(vol=vol, b=b, lab=v[B]["lab"], pF=v[F]["pub"], dB=v[B]["disp"] or 0))
    npos = sum(p["lab"] == "pos" for p in pares); nneg = len(pares) - npos
    k_ap = sum(1 - p["pF"] for p in pares)
    print("\n== %s | publicadas por el control: %d positivas, %d negativos limpios | F apaga %d" % (sensor, npos, nneg, k_ap))
    o, lo, hi, me = selectividad(pares, "pF")
    print("  (2) brazo F real:        observado %+.4f | nulo [%+.4f, %+.4f] media %+.4f | CUMPLE a una cola: %s" % (o, lo, hi, me, o > hi))
    # (1) apagador al azar dentro del estrato, misma cantidad que F por estrato
    g = collections.defaultdict(list)
    for p in pares: g[(p["vol"], p["b"])].append(p)
    cumple = 0; dos_colas = 0; obs_az = []
    for s in range(200):
        rnd = random.Random(1000 + s)
        for p in pares: p["pR"] = 1
        for est_ in g.values():
            k = sum(1 - p["pF"] for p in est_)
            for p in rnd.sample(est_, k): p["pR"] = 0
        o2, lo2, hi2, _ = selectividad(pares, "pR", n_iter=300, semilla=s)
        cumple += o2 > hi2; dos_colas += (o2 > hi2 or o2 < lo2); obs_az.append(o2)
    print("  (1) apagador al azar, 200 semillas: cumple a una cola %d de 200 | a dos colas %d de 200 | observado medio %+.4f" % (cumple, dos_colas, sum(obs_az) / 200))
    # (3) corte parejo por magnitud: apaga las k mas debiles del sensor
    orden = sorted(pares, key=lambda p: p["dB"])
    for i, p in enumerate(orden): p["pU"] = int(i >= k_ap)
    o3, lo3, hi3, me3 = selectividad(pares, "pU")
    print("  (3) corte parejo por magnitud: observado %+.4f | nulo [%+.4f, %+.4f] | cumple: %s | positivas perdidas %d (F pierde %d)" % (
        o3, lo3, hi3, o3 > hi3, sum(1 for p in pares if p["lab"] == "pos" and not p["pU"]), sum(1 for p in pares if p["lab"] == "pos" and not p["pF"])))
