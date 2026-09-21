# -*- coding: utf-8 -*-
"""Verificador S148 del resultado: (a) C8 frente a un apagador al azar, 200 semillas; (b) poder de P2
bajo apagado parejo; (c) noches perdidas con definicion propia; (d) MODIS primer pase, ventana
completa; (e) cruce contra resultado_F del documento (magnitud pareada, movidos)."""
import json, random, collections
from pathlib import Path
AQUI = Path(__file__).resolve().parent
T = json.loads((AQUI / "tabla.json").read_text(encoding="utf-8"))
B, F = "_s146_ab_sin_test1", "_s147_ab_sin_test1_max"
rows = []
for k, v in T.items():
    vol, b, dt = k.split("|")
    rows.append({"vol": vol, "b": b, "dt": dt, "lab": v[B]["lab"], "pB": v[B]["pub"], "pF": v[F]["pub"],
                 "zB": v[B]["z"], "nfpB": v[B]["n_fp"], "nfpF": v[F]["n_fp"], "nspF": v[F]["n_sp"]})


def zona(z):
    return "nadir" if z < 36 else ("medio" if z < 52 else "borde")


pares = [r for r in rows if r["lab"] in ("pos", "neg_limpio")]


def contraste(labs, campo):
    neg = [p for p, l in zip(pares, labs) if l == "neg_limpio"]
    pos = [p for p, l in zip(pares, labs) if l == "pos"]
    return sum(p[campo] - p["pB"] for p in neg) / len(neg) - sum(p[campo] - p["pB"] for p in pos) / len(pos)


print("== a. C8 frente a un apagador AL AZAR (misma cantidad que F por volcan y sensor), 200 semillas")
LO, HI = 0.0498, 0.146  # intervalo del nulo que imprime el evaluador y que reproduje en r3
g = collections.defaultdict(list)
for p in pares:
    g[(p["vol"], p["b"])].append(p)
fuera = 0
vals = []
for s in range(200):
    rnd = random.Random(s)
    for p in pares:
        p["pR"] = p["pB"]
    for grp in g.values():
        k = sum(p["pB"] - p["pF"] for p in grp)
        for p in rnd.sample([p for p in grp if p["pB"]], k):
            p["pR"] = 0
    v = contraste([p["lab"] for p in pares], "pR")
    vals.append(v)
    fuera += (v < LO or v > HI)
vals.sort()
print("  apagador al azar: contraste mediano %.4f, rango %.4f a %.4f | 'fuera del nulo' (C8 cumplido) en %d de 200" % (vals[100], vals[0], vals[-1], fuera))
print("  brazo F observado: -0.1082 (lado opuesto al apagador al azar)")

print("\n== b. poder de P2: si F apagara PAREJO las publicaciones del control en negativos V375 (sobreviven 10 de 111 al azar)")
neg = [r for r in rows if r["b"] == "VIIRS375" and r["lab"] == "neg_limpio"]
nz = collections.Counter(zona(r["zB"]) for r in neg)
pubs = [r for r in neg if r["pB"]]
ok = 0; N = 5000; rnd = random.Random(1); ok025 = 0; indef = 0
for _ in range(N):
    sv = rnd.sample(pubs, 10)
    c = collections.Counter(zona(r["zB"]) for r in sv)
    tn, tb = c["nadir"] / nz["nadir"], c["borde"] / nz["borde"]
    if tn == 0:
        indef += 1
        continue
    ok += (tb / tn <= 1.3)
    ok025 += (tb / tn <= 0.25)
print("  bajo apagado parejo P2<=1,3 se cumple por azar en %.1f %% de %d sorteos (razon indefinida en %.1f %%); P2<=0,25 en %.2f %%" % (100 * ok / N, N, 100 * indef / N, 100 * ok025 / N))

print("\n== c. noches con alerta: perdidas con definicion propia")
for unidad, f in (("volcan", lambda r: (r["vol"], r["dt"][:10])), ("volcan+sensor", lambda r: (r["vol"], r["b"], r["dt"][:10]))):
    nb, nf = collections.defaultdict(int), collections.defaultdict(int)
    for r in rows:
        if r["lab"] == "pos":
            nb[f(r)] += r["pB"]; nf[f(r)] += r["pF"]
    perd = [k for k in nb if nb[k] > 0 and nf[k] == 0]
    print("  unidad %s (solo pasadas pos): noches con alerta %d | control publica %d | brazo %d | perdidas %s" % (unidad, len(nb), sum(v > 0 for v in nb.values()), sum(v > 0 for v in nf.values()), perd))
    # variante: cualquier pasada de la noche
    ab, af = collections.defaultdict(int), collections.defaultdict(int)
    for r in rows:
        ab[f(r)] += r["pB"]; af[f(r)] += r["pF"]
    perd2 = [k for k in nb if ab[k] > 0 and af[k] == 0]
    print("     variante cualquier pasada de esa noche: perdidas", perd2)

print("\n== d. MODIS y los otros: pasadas con pixeles de primer pase, ventana completa")
for b in ("MODIS", "VIIRS750", "VIIRS375"):
    s = [r for r in rows if r["b"] == b]
    print("  %s n %d | n_fp>0: B %d F %d | F publica %d, de ellas con n_fp==0: %d" % (b, len(s), sum((r["nfpB"] or 0) > 0 for r in s), sum((r["nfpF"] or 0) > 0 for r in s),
          sum(r["pF"] for r in s), sum(1 for r in s if r["pF"] and (r["nfpF"] or 0) == 0)))
s = [r for r in rows if r["b"] == "MODIS" and r["lab"] == "neg_limpio"]
print("  MODIS neg_limpio n %d | n_fp>0: B %d F %d" % (len(s), sum((r["nfpB"] or 0) > 0 for r in s), sum((r["nfpF"] or 0) > 0 for r in s)))

print("\n== e. cruce con resultado_F del documento")
d = json.loads((AQUI / "resultado_F_documento.json").read_text(encoding="utf-8"))["brazos"][0]
for k, v in sorted(d["razon_magnitud_pareada"].items()):
    print("  ", k, v)
print("  C4_peor_estrato:", d["C4_peor_estrato"])
print("  C4 sin muestra:", d["C4_estratos_sin_muestra"])
po = d["posicion"]
print("  posicion: pares %s movidos %s mediana %s p90 %s" % (po["n_pares_publicados_por_ambos"], po["n_movidos_mas_de_500_m"], po["mediana_separacion_km"], po["p90_separacion_km"]))
for m in po["movidos"]:
    print("    ", m)
mio = json.loads((AQUI / "resultado_F_mio.json").read_text(encoding="utf-8"))["brazos"][0]
igual = all(json.dumps(d[k], sort_keys=True) == json.dumps(mio[k], sort_keys=True) for k in d if k not in ("veredicto", "razon"))
print("  mi corrida del evaluador da el mismo bloque del brazo que el JSON del documento:", igual)
