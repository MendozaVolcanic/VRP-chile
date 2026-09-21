# -*- coding: utf-8 -*-
"""Verificador S148 del resultado: (a) el nulo barajado, con dos contrafactuales; (b) costos que el
evaluador no cuenta (sin_info en noches con alerta, far_ref); (c) z entre brazos; (d) magnitud:
el brazo se acerca o se aleja de MIROVA par a par; (e) Fisher de la selectividad por zona."""
import json, random, collections, math, statistics as st
from pathlib import Path
AQUI = Path(__file__).resolve().parent
T = json.loads((AQUI / "tabla.json").read_text(encoding="utf-8"))
B, F = "_s146_ab_sin_test1", "_s147_ab_sin_test1_max"
rows = []
for k, v in T.items():
    vol, b, dt = k.split("|")
    rows.append({"vol": vol, "b": b, "dt": dt, "lab": v[B]["lab"], "pB": v[B]["pub"], "pF": v[F]["pub"],
                 "dB": v[B]["disp"] or 0, "dF": v[F]["disp"] or 0, "ref": v[B]["vrp_ref"],
                 "zB": v[B]["z"], "zF": v[F]["z"], "tbg": v[B]["t_bg"]})


def zona(z):
    return "nadir" if z < 36 else ("medio" if z < 52 else "borde")


def contraste(pares, labs, campo):
    neg = [p for p, l in zip(pares, labs) if l == "neg_limpio"]
    pos = [p for p, l in zip(pares, labs) if l == "pos"]
    dn = sum(p[campo] - p["pB"] for p in neg) / len(neg)
    dp = sum(p[campo] - p["pB"] for p in pos) / len(pos)
    return dn - dp


def nulo(pares, campo, n_iter=1000, semilla=146):
    obs = contraste(pares, [p["lab"] for p in pares], campo)
    rnd = random.Random(semilla)
    g = collections.defaultdict(list)
    for i, p in enumerate(pares):
        g[(p["vol"], p["b"])].append(i)
    out = []
    for _ in range(n_iter):
        labs = [None] * len(pares)
        for idx in g.values():
            ls = [pares[i]["lab"] for i in idx]
            rnd.shuffle(ls)
            for i, l in zip(idx, ls):
                labs[i] = l
        out.append(contraste(pares, labs, campo))
    out.sort()
    return round(obs, 4), round(out[int(0.025 * (len(out) - 1))], 4), round(out[int(0.975 * (len(out) - 1))], 4), round(sum(out) / len(out), 4)


pares = [r for r in rows if r["lab"] in ("pos", "neg_limpio")]
print("== a. nulo barajado, reimplementado (obs, p2.5, p97.5, media)")
print("  brazo F real:", nulo(pares, "pF"))
# contrafactual 1: endurecimiento PAREJO por magnitud. Se apagan las publicaciones del control con
# disp bajo un corte unico, elegido para apagar la misma cantidad que F en pos+neg.
n_apaga = sum(p["pB"] - p["pF"] for p in pares)
pubs = sorted(p["dB"] for p in pares if p["pB"])
corte = pubs[n_apaga - 1]
for p in pares:
    p["pU"] = int(p["pB"] and p["dB"] > corte)
print("  F apaga", n_apaga, "de", len(pubs), "| corte parejo de magnitud = %.4f MW, apaga" % corte, sum(p["pB"] - p["pU"] for p in pares))
print("  contrafactual endurecimiento parejo por magnitud (un solo corte en MW):", nulo(pares, "pU"))
print("     ese contrafactual pierde positivas:", sum(1 for p in pares if p["lab"] == "pos" and p["pB"] and not p["pU"]),
      "| deja negativos:", sum(1 for p in pares if p["lab"] == "neg_limpio" and p["pU"]))
# contrafactual 1b: corte parejo por sensor
for p in pares:
    p["pU2"] = p["pB"]
for b in ("VIIRS375", "VIIRS750", "MODIS"):
    s = [p for p in pares if p["b"] == b]
    k = sum(p["pB"] - p["pF"] for p in s)
    pb = sorted(p["dB"] for p in s if p["pB"])
    if k:
        c = pb[k - 1]
        for p in s:
            p["pU2"] = int(p["pB"] and p["dB"] > c)
        print("     corte por sensor", b, "%.4f MW" % c)
print("  contrafactual corte parejo POR SENSOR:", nulo(pares, "pU2"),
      "| pierde positivas:", sum(1 for p in pares if p["lab"] == "pos" and p["pB"] and not p["pU2"]),
      "| deja negativos V375:", sum(1 for p in pares if p["lab"] == "neg_limpio" and p["pU2"] and p["b"] == "VIIRS375"))
# contrafactual 2: apagado AL AZAR dentro de cada volcan y sensor, misma cantidad que F
rnd = random.Random(7)
g = collections.defaultdict(list)
for p in pares:
    g[(p["vol"], p["b"])].append(p)
for p in pares:
    p["pR"] = p["pB"]
for s in g.values():
    k = sum(p["pB"] - p["pF"] for p in s)
    for p in rnd.sample([p for p in s if p["pB"]], k):
        p["pR"] = 0
print("  contrafactual apagado al azar dentro del estrato (debe caer DENTRO del nulo):", nulo(pares, "pR"))

print("\n== b. costos que el evaluador no cuenta")
noches_pos = {(r["vol"], r["dt"][:10]) for r in rows if r["lab"] == "pos"}
for b in ("VIIRS375", "VIIRS750", "MODIS"):
    si = [r for r in rows if r["b"] == b and r["lab"] == "sin_info"]
    act = [r for r in si if (r["vol"], r["dt"][:10]) in noches_pos]
    print("  %s sin_info %d (B %d, F %d) | de ellas en noche con alerta de MIROVA en el volcan: %d (B %d, F %d)" % (
        b, len(si), sum(r["pB"] for r in si), sum(r["pF"] for r in si), len(act), sum(r["pB"] for r in act), sum(r["pF"] for r in act)))
    fr = [r for r in rows if r["b"] == b and r["lab"] == "far_ref"]
    print("  %s far_ref %d (B %d, F %d)" % (b, len(fr), sum(r["pB"] for r in fr), sum(r["pF"] for r in fr)))
print("  far_ref V375 que F apaga:")
for r in rows:
    if r["lab"] == "far_ref" and r["pB"] and not r["pF"]:
        print("    ", r["vol"], r["b"], r["dt"], "dispB %.4f" % r["dB"])
act = [r for r in rows if r["b"] == "VIIRS375" and r["lab"] == "sin_info" and (r["vol"], r["dt"][:10]) in noches_pos and r["pB"] and not r["pF"]]
print("  V375 sin_info en noche con alerta, apagadas por F: %d, por volcan %s" % (len(act), dict(collections.Counter(r["vol"] for r in act))))
print("     mediana dispB de esas: %.4f MW; con dispB>=0.1: %d" % (st.median(r["dB"] for r in act), sum(r["dB"] >= 0.1 for r in act)))

print("\n== c. sensor_zenith_deg entre brazos (mismo granulo)")
dz = [abs(r["zB"] - r["zF"]) for r in rows if r["zB"] is not None and r["zF"] is not None]
print("  n %d | distintos >0.01: %d | max %.3f | >1 grado: %d | cambian de zona: %d" % (
    len(dz), sum(x > 0.01 for x in dz), max(dz), sum(x > 1 for x in dz),
    sum(1 for r in rows if r["zB"] is not None and zona(r["zB"]) != zona(r["zF"]))))

print("\n== d. magnitud par a par contra MIROVA, V375 positivas publicadas por ambos")
pp = [r for r in rows if r["b"] == "VIIRS375" and r["lab"] == "pos" and r["pB"] and r["pF"] and r["ref"]]
cam = [r for r in pp if abs(r["dB"] - r["dF"]) > 1e-9]
ac = sum(1 for r in cam if abs(math.log(r["dF"] / r["ref"])) < abs(math.log(r["dB"] / r["ref"])))
print("  pares %d | cambian %d | de los que cambian, F queda MAS CERCA de MIROVA en %d y mas lejos en %d" % (len(pp), len(cam), ac, len(cam) - ac))
for v in sorted({r["vol"] for r in cam}):
    s = [r for r in cam if r["vol"] == v]
    a = sum(1 for r in s if abs(math.log(r["dF"] / r["ref"])) < abs(math.log(r["dB"] / r["ref"])))
    print("    %-22s cambian %2d | mas cerca %2d | mas lejos %2d" % (v, len(s), a, len(s) - a))
for nom, c in (("B", "dB"), ("F", "dF")):
    e = [abs(math.log(r[c] / r["ref"])) for r in pp]
    print("  %s error log absoluto mediano %.4f | medio %.4f" % (nom, st.median(e), sum(e) / len(e)))

print("\n== e. selectividad por zona en negativos V375: supervivencia de las publicaciones del control")
neg = [r for r in rows if r["b"] == "VIIRS375" and r["lab"] == "neg_limpio" and r["pB"]]
tab = {}
for zn in ("nadir", "medio", "borde"):
    s = [r for r in neg if zona(r["zB"]) == zn]
    tab[zn] = (sum(r["pF"] for r in s), len(s))
    print("   %s: sobreviven %d de %d" % (zn, tab[zn][0], tab[zn][1]))
try:
    from scipy.stats import fisher_exact
    a, n1 = tab["nadir"]; c, n2 = tab["borde"]
    print("   Fisher nadir contra borde:", fisher_exact([[a, n1 - a], [c, n2 - c]]))
except Exception as e:
    print("   scipy no disponible:", e)
# la selectividad, ¿la explica la magnitud? magnitud de las publicaciones del control por zona
for zn in ("nadir", "medio", "borde"):
    s = [r["dB"] for r in neg if zona(r["zB"]) == zn]
    print("   %s mediana dispB de negativos publicados por el control: %.4f MW (n %d)" % (zn, st.median(s), len(s)))
