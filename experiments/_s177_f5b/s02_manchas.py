# -*- coding: utf-8 -*-
"""s02: recalcular para los 303 aciertos con lámina (a) el selector A de F5b con su propio código, (b) C1 y (c) C2.

Por qué: antes de medir nada hay que probar que el instrumento corregido (1) conserva la mancha donde F5b la borraba, (2) no
cambia las láminas donde no había mancha y (3) reproduce el selector de F5b cuando se le pide ser F5b.
Pre-registro (escrito antes de correr):
  - Control positivo: Chillán VIIRS_NOAA20_750 2026-10-10 06:54 UTC. F5b/V5B dan lum 196,7 con A; C1 y C2 deben dar lum 255 y una
    mancha de 48 px (V5B m1) en 11 celdas.
  - Control de no-cambio: en los records donde el panel NO tiene componente blanca de 20 a 399 px dentro del inner (A no borra nada
    de calor), C1 debe dar la misma celda que A en el 100 %. Si C1 difiere ahí, el selector corregido cambia algo que no debía.
  - Control de reproducción: A recalculado con el código de F5b debe dar las mismas lat/lon que p8_clases.json en 303 de 303.
  - Pregunta 2 (¿puede el instrumento dar un resultado distinto?): si el selector estuviera muerto, C1 = A en los 35 records donde
    A borraba una componente; se cuentan los que cambian.
Salida: salidas/s02_manchas.json (una fila por acierto con lámina) y salidas/s02_manchas.out.txt.
"""
import json, os, sys, collections
import numpy as np
import yaml
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lib177 as M
L = M.L
sys.stdout.reconfigure(encoding="utf-8")
TMP = r"C:\Users\nmend\vrp-temporales\s175_audit\f5b"
V = {v["name"]: v for v in yaml.safe_load(open(r"C:\Users\nmend\vrp-temporales\s175_audit\main\volcanoes.yaml", encoding="utf-8"))["volcanoes"]}
ARCH = {"NevadosDeChillan": "ChillanNevadosde"}
refs = json.load(open(os.path.join(HERE, "orig", "p6_tif_referencia_out.json"), encoding="utf-8"))
recs = [x for x in json.load(open(os.path.join(HERE, "orig", "p8_clases.json"), encoding="utf-8")) if x.get("vol") != "_CONTROL_"]
gr = {}


def grilla(vol, b):
    if (vol, b) not in gr:
        ref = refs[f"{ARCH.get(vol, vol)}|{b}"]["ref_sep"]
        g = L.grilla(os.path.join(TMP, "tif_ref", ARCH.get(vol, vol) + "_" + os.path.basename(ref["path"])))
        g["mc"] = (V[vol]["mirova_center_lat"], V[vol]["mirova_center_lon"])
        g["inner"] = L.mascara_inner(g, g["mc"], V[vol]["inner_radius_km"])
        g["celda_km"] = abs(g["transform"].e) * 111.0
        gr[(vol, b)] = g
    return gr[(vol, b)]


out = []
hist = collections.Counter()
for x in recs:
    if not x.get("png"):
        continue
    g = grilla(x["vol"], x["b"])
    im = L.abrir_png(os.path.join(TMP, "png", x["png"].split("/")[-2] + "_" + os.path.basename(x["png"])))
    bb = L.bbox_marco(im, x["panel"])
    P = M.preparar(im, bb, g)
    hA = L.pixel_mas_claro(im, bb, g, g["inner"])      # A con el código ORIGINAL de F5b
    comps = M.componentes_blancas(P)
    for c in comps:
        if not c["toca"]:
            hist[min(c["area"] // 50 * 50, 2000)] += 1
    borra = [c["area"] for c in comps if c["en_inner"] and not c["toca"] and 20 <= c["area"] < M.UMBRAL_SIN_DATO]
    sA = M.seleccionar(P, g, "A", False)
    sC1 = M.seleccionar(P, g, "B", False)
    sC2 = M.seleccionar(P, g, "B", True)
    o = dict(vol=x["vol"], b=x["b"], sensor=x["sensor"], dt=x["dt"], prot=x["protegida"], vrp=x["vrp_mirova"], dist_tabla=x.get("dist_tabla_km"),
             fuente=x.get("fuente_dist"), our_lat=float(x["our_lat"]), our_lon=float(x["our_lon"]), panel=x["panel"], png=x["png"],
             claseF5b=x["clase"], motivo_iv=x.get("motivo_iv"), ctrlF5b=x.get("control_distancia"), F5b_lat=x.get("png_lat"), F5b_lon=x.get("png_lon"),
             F5b_lum=x.get("lum_max"), F5b_mancha_px=x.get("mancha_px"), celda_km=g["celda_km"],
             hA_lat=(round(hA["lat"], 5) if hA else None), hA_lon=(round(hA["lon"], 5) if hA else None), hA_lum=(hA["lum_max"] if hA else None),
             comps_borradas_por_A=len(borra), areas_borradas=borra, A=sA, C1=sC1, C2=sC2)
    out.append(o)
json.dump(out, open(os.path.join(HERE, "salidas", "s02_manchas.json"), "w", encoding="utf-8"), ensure_ascii=False)

print("== Control de reproducción: A con el código original de F5b contra p8_clases.json ==")
n = len(out)
rep = sum(1 for o in out if o["hA_lat"] is not None and o["F5b_lat"] is not None and abs(o["hA_lat"] - o["F5b_lat"]) < 1e-5 and abs(o["hA_lon"] - o["F5b_lon"]) < 1e-5)
print(f"records con panel: {n}; lat/lon de A recalculado igual al de p8_clases.json: {rep} de {n}")
repA = sum(1 for o in out if o["A"] and abs(o["A"]["lat"] - o["F5b_lat"]) < 1e-5 and abs(o["A"]["lon"] - o["F5b_lon"]) < 1e-5)
print(f"mi reimplementación de A (lib177, regla A, sin empates) igual a p8_clases.json: {repA} de {n}")
print("\n== Histograma de componentes blancas que no tocan el borde (area // 50 * 50; 2000 = >= 2000) ==")
print(sorted(hist.items()))
print("\n== Records donde A borraba una componente blanca de calor (20 a 399 px, en el inner, sin tocar el borde) ==")
bor = [o for o in out if o["comps_borradas_por_A"] > 0]
print("n =", len(bor), "de", n, "|", dict(collections.Counter((o["vol"], o["b"]) for o in bor)))
print("\n== Control positivo: Chillán VIIRS_NOAA20_750 2026-10-10 06:54 ==")
for o in out:
    if o["vol"] == "NevadosDeChillan" and o["dt"] == "2026-10-10 06:54" and o["sensor"] == "VIIRS_NOAA20_750":
        for k in ("A", "C1", "C2"):
            s = o[k]
            print(f"  {k}: lum {s['lum_max']:.1f}, saturado {s['saturado']}, principal {s['px_principal']} px, componentes {s['n_comps']}, celdas {sum(len(c['celdas']) for c in s['comps'])}, centro {s['lat']:.5f},{s['lon']:.5f}")
        print(f"  F5b guardó: lum {o['F5b_lum']}, mancha {o['F5b_mancha_px']} px; V5B m1 espera lum 255, 48 px, 11 celdas")
print("\n== Control de no-cambio: records SIN componente borrada por A ==")
sin = [o for o in out if o["comps_borradas_por_A"] == 0]
igual = [o for o in sin if o["C1"]["rc"] == o["A"]["rc"] and abs(o["C1"]["lum_max"] - o["A"]["lum_max"]) < 1e-9]
print(f"n = {len(sin)}; C1 igual a A (misma celda y misma lum): {len(igual)} de {len(sin)}")
dif = [o for o in sin if o not in igual]
for o in dif:
    print("   DIFIERE", o["vol"], o["sensor"], o["dt"], "A rc", o["A"]["rc"], o["A"]["lum_max"], "C1 rc", o["C1"]["rc"], o["C1"]["lum_max"], "sin_dato_toca_inner", o["C1"]["sin_dato_toca_inner"])
print("\n== Pregunta 2: records donde C1 difiere de A (celda o lum) ==")
dd = [o for o in out if o["C1"]["rc"] != o["A"]["rc"] or abs(o["C1"]["lum_max"] - o["A"]["lum_max"]) > 1e-9]
print("n =", len(dd), "| de ellos con componente borrada por A:", sum(1 for o in dd if o["comps_borradas_por_A"] > 0), "| sin ella:", sum(1 for o in dd if o["comps_borradas_por_A"] == 0))
print(dict(collections.Counter((o["vol"], o["b"]) for o in dd)))
print("\n== C2 contra C1 (empates y unión de saturados) ==")
c2 = [o for o in out if o["C2"]["rc"] != o["C1"]["rc"] or o["C2"]["n_comps"] != 1 or o["C2"]["px_principal"] != o["C1"]["px_principal"]]
print("records donde C2 difiere de C1 (principal, nº de componentes o su área):", len(c2), "|", dict(collections.Counter((o["vol"], o["b"]) for o in c2)))
print("   sin saturación y distinto (debería ser 0):", sum(1 for o in c2 if not o["C2"]["saturado"]))
print("   saturados:", sum(1 for o in out if o["C2"]["saturado"]), "de", n, "| con >= 2 componentes tras unir:", sum(1 for o in out if o["C2"]["n_comps"] >= 2))
print("   sin dato que toca el inner (posible mancha pegada al sin dato; no se puede separar):", sum(1 for o in out if o["C2"]["sin_dato_toca_inner"]), "|",
      dict(collections.Counter((o["vol"], o["b"]) for o in out if o["C2"]["sin_dato_toca_inner"])))
print("\n== Mancha saturada en Chillán (celdas de todas las componentes: p50, p90, max) ==")
for b in ("VIIRS375", "VIIRS750", "MODIS"):
    g_ = [o for o in out if o["vol"] == "NevadosDeChillan" and o["b"] == b]
    ce = [sum(len(c["celdas"]) for c in o["C2"]["comps"]) for o in g_]
    sat = sum(1 for o in g_ if o["C2"]["saturado"])
    print(f"  {b}: n={len(g_)} saturadas {sat}; celdas p50 {np.median(ce):.0f} p90 {np.percentile(ce, 90):.0f} max {max(ce)}; con >=2 componentes {sum(1 for o in g_ if o['C2']['n_comps'] >= 2)}")
