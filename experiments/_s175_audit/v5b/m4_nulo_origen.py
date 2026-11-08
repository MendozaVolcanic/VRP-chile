# -*- coding: utf-8 -*-
"""m4 (V5B): nulo de la clase i/iii, origen de la Distancia_km de MIROVA y empates del pixel mas claro.

Fenomeno: (1) si nuestro punto y la mancha de MIROVA estan ambos cerca del crater, casi cualquier punto cae cerca; el
nulo pone en lugar de nuestro punto uno de OTRA pasada del mismo volcan y sensor, o uno uniforme en el inner. (2) La
tabla da distancias cuantizadas por celda: si su origen es la celda central, las celdas de la mancha reproducen el
valor exacto (sqrt(i^2+j^2)*celda nominal a 0,03 km); se barre el origen y se evalua en mitad de ajuste y mitad de
prueba. (3) Cuando hay dos componentes saturadas, np.argmax toma la primera en orden de barrido, no la mas caliente.

Pregunta 1: si la lamina no diera informacion, el observado seria igual al nulo. Pregunta 2: si el barrido de origen
estuviera muerto, todas las celdas darian la misma tasa. Control positivo del origen: Lascar V375 y Puyehue tienen
TIF-era validada; se reporta el mejor origen tambien alli.
Denominador: pasadas con panel de p8_clases.json (aciertos 2026-09-22 a 2026-11-06). Lee m1_mancha.json y p8_clases.json.
"""
import json, os, sys, collections, math, random
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(HERE, "..", "f5b"))
import f5b_lib as L
import yaml
sys.stdout.reconfigure(encoding="utf-8")
m1 = json.load(open(os.path.join(HERE, "m1_mancha.json"), encoding="utf-8"))
p8 = {(x["vol"], x["b"], x["dt"]): x for x in json.load(open(os.path.join(HERE, "..", "f5b", "p8_clases.json"), encoding="utf-8")) if x.get("vol") != "_CONTROL_"}
V = {v["name"]: v for v in yaml.safe_load(open(r"C:\Users\nmend\vrp-temporales\s175_audit\main\volcanoes.yaml", encoding="utf-8"))["volcanoes"]}
d = json.load(open(r"C:\Users\nmend\vrp-temporales\s175_audit\v5b\chillan_base.json", encoding="utf-8"))
RES = {"VIIRS375": 0.375, "VIIRS750": 0.75, "MODIS": 1.0}
rng = random.Random(175)
print("== (1) NULO de la clase i (control A ok): fraccion d <= tol; observado vs nuestro punto de otra pasada vs uniforme en inner ==")
TMP = r"C:\Users\nmend\vrp-temporales\s175_audit\f5b"
ARCH = {"NevadosDeChillan": "ChillanNevadosde"}
refs = json.load(open(os.path.join(HERE, "..", "f5b", "p6_tif_referencia_out.json"), encoding="utf-8"))
gr = {}


def grilla(vol, b):
    if (vol, b) not in gr:
        ref = refs[f"{ARCH.get(vol, vol)}|{b}"]["ref_sep"]
        g = L.grilla(os.path.join(TMP, "tif_ref", ARCH.get(vol, vol) + "_" + os.path.basename(ref["path"])))
        g["mc"] = (V[vol]["mirova_center_lat"], V[vol]["mirova_center_lon"])
        g["inner"] = L.mascara_inner(g, g["mc"], V[vol]["inner_radius_km"])
        gr[(vol, b)] = g
    return gr[(vol, b)]


def tasa_nulos(sub, etiqueta):
    obs_a, obs_b, per_a, per_b, uni_a = [], [], [], [], []
    for o in sub:
        x = p8[(o["vol"], o["b"], o["dt"])]
        if x.get("png_lat") is None:
            continue
        la, lo = float(x["our_lat"]), float(x["our_lon"])
        obs_a.append(x["d_png_nuestro_km"] <= o["tol"])
        obs_b.append(o["d_B_ours_cent"] <= o["tol"])
        otros = [y for y in sub if y["vol"] == o["vol"] and y["b"] == o["b"] and y["dt"] != o["dt"]]
        g = grilla(o["vol"], o["b"])
        idx = np.argwhere(g["inner"])
        for _ in range(30):
            if otros:
                y = rng.choice(otros)
                yy = p8[(y["vol"], y["b"], y["dt"])]
                d_ = L.hav(x["png_lat"], x["png_lon"], float(yy["our_lat"]), float(yy["our_lon"]))
                per_a.append(d_ <= o["tol"])
                per_b.append(L.hav(g["lats"][o["celdas"][0][0], o["celdas"][0][1]], g["lons"][o["celdas"][0][0], o["celdas"][0][1]], float(yy["our_lat"]), float(yy["our_lon"])) <= o["tol"])
            r_, c_ = idx[rng.randrange(len(idx))]
            uni_a.append(L.hav(x["png_lat"], x["png_lon"], float(g["lats"][r_, c_]), float(g["lons"][r_, c_])) <= o["tol"])
    print(f"  {etiqueta}: n={len(obs_a)} observado A {np.mean(obs_a):.3f} | observado B(centroide) {np.mean(obs_b):.3f} | nulo permutacion {np.mean(per_a) if per_a else float('nan'):.3f} (A) | nulo uniforme {np.mean(uni_a):.3f}")


con_ctrl = [o for o in m1 if o["controlA"] is True]
for b in ("VIIRS375", "VIIRS750", "MODIS"):
    tasa_nulos([o for o in con_ctrl if o["b"] == b], f"{b} todos los volcanes")
    tasa_nulos([o for o in con_ctrl if o["b"] == b and o["vol"] == "NevadosDeChillan"], f"{b} Chillan")
    tasa_nulos([o for o in con_ctrl if o["b"] == b and o["vol"] != "NevadosDeChillan"], f"{b} sin Chillan")

print("\n== (2) ORIGEN de la Distancia_km ==")


def tasa_origen(sub, r0, c0, b):
    res = RES[b]
    ok = 0
    for o in sub:
        if any(abs(math.hypot(r - r0, c - c0) * res - o["dist_tabla"]) <= 0.03 for r, c in o["celdas"]):
            ok += 1
    return ok / len(sub) if sub else float("nan")


for vol, b in (("NevadosDeChillan", "VIIRS375"), ("NevadosDeChillan", "VIIRS750"), ("Lascar", "VIIRS375"), ("Isluga", "VIIRS375"), ("PuyehueCordonCaulle", "VIIRS750")):
    sub = sorted([o for o in m1 if o["vol"] == vol and o["b"] == b and o["dist_tabla"] not in (None, "") and o["fuente"] == "CONS"], key=lambda o: o["dt"])
    if len(sub) < 6:
        print(vol, b, "pocos", len(sub))
        continue
    g = grilla(vol, b)
    mc = g["mc"]
    dd = (g["lats"] - mc[0]) ** 2 + ((g["lons"] - mc[1]) * math.cos(math.radians(mc[0]))) ** 2
    rc0 = np.unravel_index(np.argmin(dd), dd.shape)
    ajus, prue = sub[::2], sub[1::2]
    ran = range(-8, 9)
    gridfit = sorted(((tasa_origen(ajus, rc0[0] + a, rc0[1] + c, b), a, c) for a in ran for c in ran), reverse=True)
    best = gridfit[0]
    print(f"{vol} {b}: n={len(sub)} (mitades {len(ajus)}/{len(prue)}); celda de mirova_center {tuple(int(x) for x in rc0)}")
    print(f"   origen centro: ajuste {tasa_origen(ajus, rc0[0], rc0[1], b):.2f}, prueba {tasa_origen(prue, rc0[0], rc0[1], b):.2f}")
    print(f"   mejor del barrido en ajuste: offset fila,col ({best[1]},{best[2]}) tasa ajuste {best[0]:.2f}, tasa prueba {tasa_origen(prue, rc0[0] + best[1], rc0[1] + best[2], b):.2f}")
    print("   top 5 ajuste:", [(round(x[0], 2), x[1], x[2]) for x in gridfit[:5]])
    print("   mediana de tasa de todo el barrido (si no hubiera origen):", round(float(np.median([x[0] for x in gridfit])), 2))

print("\n== (3) Afirmacion 352: Chillan, control A fallido, protegidas ==")
fall = [o for o in m1 if o["vol"] == "NevadosDeChillan" and o["controlA"] is False and o["prot"] == "True"]
print("n:", collections.Counter(o["b"] for o in fall))
for b in ("VIIRS375", "VIIRS750", "MODIS"):
    g = [o for o in fall if o["b"] == b]
    if not g:
        continue
    d_c = [p8[(o["vol"], o["b"], o["dt"])]["d_png_mirova_center_km"] for o in g]
    print(f"  {b}: d(mancha A, mirova_center) en celda central (<=0,05 km): {sum(x <= 0.05 for x in d_c)} de {len(g)}; max {max(d_c):.2f}; valores tabla {sorted(collections.Counter(o['dist_tabla'] for o in g).items())}; lum_A min {min(o['lum_A'] for o in g)}")
    print(f"     control B pasa (cualquier celda de la mancha) {sum(1 for o in g if o['ctrl_B'])} de {len(g)}; nuestro punto a la celda mas cercana p50 {np.median([o['d_B_ours_min'] for o in g]):.2f}; d_A_ours p50 {np.median([o['d_A_ours'] for o in g]):.2f}")
    print(f"     mirando origen: comps blancas borradas por A en {sum(1 for o in g if o['comps_borradas_por_A'] > 0)}; n_celdas mancha p50 {np.median([o['n_celdas'] for o in g])}")
print("  ¿Dist tabla == 0 en Chillan VIIRS375 alguna vez en p8?", sorted(collections.Counter(x["dist_tabla_km"] for k, x in p8.items() if k[0] == "NevadosDeChillan" and k[1] == "VIIRS375" and x.get("dist_tabla_km") is not None).items())[:12])

print("\n== (4) Empates: pasadas con mas de una componente blanca en inner (Chillan) y zenit ==")
ch = [o for o in m1 if o["vol"] == "NevadosDeChillan"]
print("  con >=2 componentes blancas no-borde en inner:", collections.Counter((o["b"], len(o["areas_blanco_inner"]) >= 2) for o in ch))
recs = {(r["sensor"], str(r["datetime_utc"])[:16]): r for r in d["records"]}
filas = []
for o in ch:
    if o["b"] == "MODIS":
        continue
    r = recs.get((o["sensor"], o["dt"]))
    if r is None or o["d_A_ours"] is None:
        continue
    filas.append((abs(r.get("sensor_zenith_deg") or 0), o["d_A_ours"] / o["celda_km"], o["d_B_ours_cent"] / o["celda_km"], o["n_celdas"], o["b"]))
a = np.array([f[:4] for f in filas], float)
print("  n con zenit:", len(a))
for lo, hi in ((0, 30), (30, 50), (50, 60), (60, 90)):
    m = (a[:, 0] >= lo) & (a[:, 0] < hi)
    if m.sum():
        print(f"  zenit {lo}-{hi}: n={m.sum()} d_A_ours/celda p50 {np.median(a[m,1]):.2f}; d_B_cent/celda p50 {np.median(a[m,2]):.2f}; n_celdas p50 {np.median(a[m,3]):.1f}")
print("  Spearman zenit vs n_celdas:", round(float(np.corrcoef(np.argsort(np.argsort(a[:, 0])), np.argsort(np.argsort(a[:, 3])))[0, 1]), 3))
