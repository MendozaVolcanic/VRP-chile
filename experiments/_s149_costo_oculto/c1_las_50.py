# -*- coding: utf-8 -*-
"""S149. Las publicaciones V375 que el brazo F (max) apaga en pasadas sin_info de noches en que MIROVA
alerto por otra pasada. Pregunta: el cumulo apagado, esta en el mismo lugar que el cumulo de la pasada
positiva de esa noche (granulo distinto, A109)? Solo lee tabla.json del verificador S148."""
import json, math, collections, statistics as st, random, sys, io
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
T = json.loads((AQUI.parent / "_s148_verificador_resultado" / "tabla.json").read_text(encoding="utf-8"))
B, F = "_s146_ab_sin_test1", "_s147_ab_sin_test1_max"
def hav(a, b, c, d):
    R = 6371.0; p = math.radians
    x = math.sin(p(c - a) / 2) ** 2 + math.cos(p(a)) * math.cos(p(c)) * math.sin(p(d - b) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(x))
rows = []
for k, v in T.items():
    vol, b, dt = k.split("|")
    if b != "VIIRS375": continue
    rows.append(dict(vol=vol, dt=dt, noche=dt[:10], lab=v[B]["lab"], pB=v[B]["pub"], pF=v[F]["pub"], dB=v[B]["disp"] or 0,
                     lat=v[B]["pc_lat"], lon=v[B]["pc_lon"], dist=v[B]["pc_dist"], z=v[B]["z"], tbg=v[B]["t_bg"],
                     npx=v[B]["pc_npx"], ref=v[B]["vrp_ref"], nfp=v[B]["n_fp"], nsp=v[B]["n_sp"]))
pos = collections.defaultdict(list)
for r in rows:
    if r["lab"] == "pos" and r["pB"] and r["lat"] is not None: pos[(r["vol"], r["noche"])].append(r)
pos_vol = collections.defaultdict(list)
for (v, n), l in pos.items(): pos_vol[v] += l
def sep(r, cands):
    return min(hav(r["lat"], r["lon"], c["lat"], c["lon"]) for c in cands)
def grupo(nombre, sel):
    ds = []
    for r in sel:
        c = pos.get((r["vol"], r["noche"]))
        if c and r["lat"] is not None: ds.append(sep(r, c))
    if not ds: print(nombre, "n 0"); return ds
    print("%-46s n %3d | mediana %.2f km | <=0.4 km: %d | <=1 km: %d | >2 km: %d" % (nombre, len(ds), st.median(ds), sum(d <= .4 for d in ds), sum(d <= 1 for d in ds), sum(d > 2 for d in ds)))
    return ds
noches_pos = {(r["vol"], r["noche"]) for r in rows if r["lab"] == "pos"}
si = [r for r in rows if r["lab"] == "sin_info" and (r["vol"], r["noche"]) in noches_pos and r["pB"]]
ap = [r for r in si if not r["pF"]]; sv = [r for r in si if r["pF"]]
print("sin_info en noche con alerta, publicadas por el control:", len(si), "| apagadas por F:", len(ap), "| sobreviven:", len(sv))
print("noches con alerta que tienen pasada positiva PUBLICADA por el control (hay contra que comparar):",
      sum(1 for r in ap if (r["vol"], r["noche"]) in pos), "de", len(ap))
print("\n== separacion al cumulo de la pasada positiva de la MISMA noche")
d_ap = grupo("apagadas por F", ap); d_sv = grupo("sobreviven a F", sv)
# nulo: misma pasada apagada contra el cumulo positivo de OTRA noche del mismo volcan
rnd = random.Random(149); nul = []
for r in ap:
    otros = [c for c in pos_vol[r["vol"]] if c["noche"] != r["noche"]]
    if otros and r["lat"] is not None: nul.append(st.median(hav(r["lat"], r["lon"], c["lat"], c["lon"]) for c in otros))
if nul: print("%-46s n %3d | mediana %.2f km | <=0.4: %d | <=1: %d" % ("NULO: apagadas contra positivas de OTRAS noches", len(nul), st.median(nul), sum(d <= .4 for d in nul), sum(d <= 1 for d in nul)))
# control negativo: publicaciones en neg_limpio apagadas por F, contra la posicion positiva tipica del volcan
neg = [r for r in rows if r["lab"] == "neg_limpio" and r["pB"] and not r["pF"] and r["lat"] is not None]
dn = [st.median(hav(r["lat"], r["lon"], c["lat"], c["lon"]) for c in pos_vol[r["vol"]]) for r in neg if pos_vol[r["vol"]]]
if dn: print("%-46s n %3d | mediana %.2f km | <=0.4: %d | <=1: %d" % ("NEG LIMPIOS apagados contra positivas del volcan", len(dn), st.median(dn), sum(d <= .4 for d in dn), sum(d <= 1 for d in dn)))
print("\n== por volcan (apagadas): n, separacion mediana, dist al ancla mediana, zenit mediano, t_bg mediano, MW mediano")
for v in sorted({r["vol"] for r in ap}):
    s = [r for r in ap if r["vol"] == v]; d = [sep(r, pos[(r["vol"], r["noche"])]) for r in s if (r["vol"], r["noche"]) in pos and r["lat"] is not None]
    print("  %-22s n %2d | sep %s | dist %.2f | z %.0f | t_bg %.1f | %.3f MW | fp=0: %d" % (v, len(s), ("%.2f" % st.median(d)) if d else "  - ",
          st.median(r["dist"] for r in s if r["dist"] is not None), st.median(r["z"] for r in s), st.median(r["tbg"] for r in s if r["tbg"]), st.median(r["dB"] for r in s), sum(1 for r in s if not r["nfp"])))
print("\n== zona del barrido y fondo: apagadas contra sobrevivientes contra positivas")
for nom, s in (("apagadas", ap), ("sobreviven", sv), ("positivas pub. control", [r for r in rows if r["lab"] == "pos" and r["pB"]]), ("neg limpios apagados", neg)):
    z = [r["z"] for r in s if r["z"] is not None]; t = [r["tbg"] for r in s if r["tbg"]]
    print("  %-24s n %3d | borde(z>=52) %4.0f %% | t_bg mediano %.1f K | MW mediano %.3f" % (nom, len(s), 100 * sum(x >= 52 for x in z) / len(z), st.median(t), st.median(r["dB"] for r in s)))
json.dump([dict(r, sep=(sep(r, pos[(r["vol"], r["noche"])]) if (r["vol"], r["noche"]) in pos and r["lat"] is not None else None)) for r in ap],
          open(AQUI / "las_50.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
