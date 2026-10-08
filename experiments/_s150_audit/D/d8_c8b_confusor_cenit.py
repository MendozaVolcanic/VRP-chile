# -*- coding: utf-8 -*-
"""S150 auditor D, sonda 8: C8b (selectividad a una cola) baraja las etiquetas pos/neg dentro de cada VOLCAN.
Pero la etiqueta esta correlacionada con el cenit (MIROVA alerta mas en el nadir; los negativos limpios se
concentran en el borde), asi que un brazo que solo corta el borde, sin saber nada de etiquetas, sale
"selectivo". Esta sonda recalcula C8b con el nulo de medir_predicciones (por volcan) y con un nulo
estratificado por volcan Y zona de cenit (nadir < 36, medio 36-52, borde >= 52), para el brazo F real y para
el brazo sintetico "borde_solo".

PREGUNTAS DEL INSTRUMENTO
 1. Si C8b midiera geometria en vez de etiqueta, esta sonda lo veria? Si: el brazo borde_solo (cero
    informacion de etiqueta) cumple con el nulo por volcan y debe dejar de cumplir con el nulo por zona.
 2. Si la sonda estuviera muerta, se veria distinto? Control: el oraculo (publica solo pos) debe cumplir con
    los dos nulos; la identidad debe fallar con los dos.

Uso: python d8_c8b_confusor_cenit.py tabla1.json [tabla2.json ...]
"""
import collections, io, json, random, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


def zona(z):
    return "z?" if z is None else ("nadir" if z < 36 else ("medio" if z < 52 else "borde"))


def c8b(rows, pF, estrato, n=1000, semilla=149):
    base = [r for r in rows if r["lab"] in ("pos", "neg_limpio") and r["pB"]]
    f = [pF(r) for r in base]

    def est(labs):
        p = [x for x, l in zip(f, labs) if l == "pos"]; q = [x for x, l in zip(f, labs) if l == "neg_limpio"]
        return sum(p) / len(p) - sum(q) / len(q)
    obs = est([r["lab"] for r in base]); rnd = random.Random(semilla); g = collections.defaultdict(list)
    for i, r in enumerate(base):
        g[estrato(r)].append(i)
    nul = []
    for _ in range(n):
        labs = [None] * len(base)
        for idx in g.values():
            ls = [base[i]["lab"] for i in idx]; rnd.shuffle(ls)
            for i, l in zip(idx, ls):
                labs[i] = l
        nul.append(est(labs))
    nul.sort(); hi = nul[int(.975 * (n - 1))]
    return obs, hi, obs > hi


for ruta in sys.argv[1:]:
    T = json.load(open(ruta, encoding="utf-8"))
    rows = []
    for k, v in T["pasadas"].items():
        vol, b, dt = k.split("|")
        if b == "VIIRS375" and len(v) == 2:
            c, f = v["control"], v["brazo"]
            rows.append(dict(vol=vol, lab=c["lab"], pB=c["pub"], pFr=f["pub"], z=c["z"], plat=c.get("plataforma")))
    base = [r for r in rows if r["lab"] in ("pos", "neg_limpio") and r["pB"]]
    print("== ventana", T["ventana"], "| base (publicadas por el control, pos o neg limpio):", len(base),
          "| pos por zona", dict(collections.Counter(zona(r["z"]) for r in base if r["lab"] == "pos")),
          "| neg por zona", dict(collections.Counter(zona(r["z"]) for r in base if r["lab"] == "neg_limpio")))
    brazos = {"F real (max)": lambda r: r["pFr"], "borde_solo (sintetico)": lambda r: int(r["z"] is None or r["z"] < 52),
              "oraculo": lambda r: int(r["lab"] == "pos"), "identidad": lambda r: 1}
    for nom, fn in brazos.items():
        o1, h1, ok1 = c8b(rows, fn, lambda r: r["vol"])
        o2, h2, ok2 = c8b(rows, fn, lambda r: (r["vol"], zona(r["z"])))
        print("   %-24s observado %+.3f | nulo por volcan p97,5 %+.3f %-7s | nulo por volcan y zona p97,5 %+.3f %s" % (
            nom, o1, h1, "CUMPLE" if ok1 else "FALLA", h2, "CUMPLE" if ok2 else "FALLA"))
