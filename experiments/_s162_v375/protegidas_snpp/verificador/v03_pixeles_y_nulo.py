# -*- coding: utf-8 -*-
"""VP162 verificador, v03: posiciones de los pixeles del port recalculadas desde la grilla UTM (sin usar la distancia
que escribe el runner), su distancia al crater de volcanoes.yaml, su distancia al centroide del cumulo de K (otro
codigo, el de produccion), y un nulo del pareo VRP de MIROVA contra la suma del port.

Pregunta 1: si los pixeles del port estuvieran en el crater, la distancia recalculada daria < inner (5 o 7 km); si el
pareo VRP fuera azar, el nulo barajado daria errores tan chicos como el pareo real.
Pregunta 2: control de instrumento: la convencion fila/columna se elige UNA vez y se exige que reproduzca la distancia
del runner en todos los pixeles del lote (si el instrumento estuviera roto, el maximo |delta| seria grande).
Ventana: lote de S159 run 39712862945 (150 pasadas VIIRS 375, 6 de ellas las protegidas en cuestion).
"""
import io, json, glob, math, random, sys
from pathlib import Path
import numpy as np, yaml
from pyproj import Transformer
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
R = Path(__file__).resolve().parents[4]
ART = r"D:\vrp-trabajo\temporales\s159_portes\run_39712862945"
rs = {r["id"]: r for f in sorted(glob.glob(ART + r"\s159-portes-VIIRS375-*\resultados_VIIRS375_*.json"))
      for r in json.load(open(f, encoding="utf-8"))}
OBJ = {o["id"]: o for o in json.load(open(R/"experiments/_s159/portes/objetivos_portes.json", encoding="utf-8"))}
V = {v["name"]: v for v in yaml.safe_load(open(R/"volcanoes.yaml", encoding="utf-8"))["volcanoes"]}
def hav(a, b, c, d):
    r = 6371.0088; p1, p2 = math.radians(a), math.radians(c)
    dp, dl = p2-p1, math.radians(d-b)
    return 2*r*math.asin(math.sqrt(math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2))
TR = {}
def latlon(g, i, j, conv):
    t = TR.setdefault(g["epsg"], Transformer.from_crs(g["epsg"], 4326, always_xy=True))
    r_, c_ = (i, j) if conv == "rc" else (j, i)
    x = g["ul_x"] + (c_+0.5)*g["celda"]; y = g["ul_y"] - (r_+0.5)*g["celda"]
    lon, lat = t.transform(x, y); return lat, lon
# CONTROL DE INSTRUMENTO (corregido): el campo 3 de cada pixel del runner es la distancia a (X0, Y0), el punto de
# referencia de MIROVA (mirova_port.py:111), NO al crater. La convencion fila/columna se elige exigiendo que la
# distancia planar a (X0, Y0) reproduzca ese campo; la distancia al crater se calcula aparte.
err = {"rc": [], "cr": []}
for i, r in rs.items():
    if r.get("estado") != "ok" or i not in OBJ: continue
    g = OBJ[i]["grilla"]
    for px in r["port"]["fisica"]["pixeles"] or []:
        for conv in err:
            rr, cc = (px[0], px[1]) if conv == "rc" else (px[1], px[0])
            x = g["ul_x"] + (cc+0.5)*g["celda"]; y = g["ul_y"] - (rr+0.5)*g["celda"]
            err[conv].append(abs(math.hypot(x-g["X0"], y-g["Y0"])/1000 - px[3]))
for k, e in err.items():
    print(f"convencion {k}: n={len(e)} max|delta dist a X0Y0| = {max(e):.4f} km, mediana {np.median(e):.4f}")
conv = min(err, key=lambda k: max(err[k]))
print("convencion elegida:", conv)
SEIS = [279, 285, 288, 289, 294, 295]
for i in SEIS:
    r = rs[i]; o = OBJ[i]; g = o["grilla"]; v = V[o["volcan"]]
    vl, vo = v.get("vent_lat", v["lat"]), v.get("vent_lon", v["lon"])
    fis = r["port"]["fisica"]; kc = r["K"]["record"]["primary_cluster"] if r["K"]["record"] else None
    print(f"\n{i} {o['volcan']} {o['hora_utc']} granulo {r['granule'][:24]} zen {r['geometria_centro']['sensor_zenith']:.1f} inner {v['inner_radius_km']} | MIROVA {o['mirova_vrp']} MW")
    print(f"  port fisica: {fis['npix']} px, VRP {fis['vrp_mw']:.3f} MW; banda {fis.get('vrp_banda')} (campo 4 de cada pixel es la radiancia MIR, no MW)")
    for px in fis["pixeles"]:
        la, lo = latlon(g, px[0], px[1], conv)
        dk = hav(la, lo, kc["centroid_lat"], kc["centroid_lon"]) if kc else float("nan")
        print(f"    px({px[0]},{px[1]}) {la:.4f},{lo:.4f} d_crater {hav(la, lo, vl, vo):.2f} km (runner, a X0Y0: {px[3]}) L_mir {px[4]:.3f} BT {px[5]} | d a centroide K {dk:.2f} km")
    if kc:
        print(f"  K cumulo primario: {kc['n_pixels']} px {kc['vrp_mw']} MW centroide a {hav(kc['centroid_lat'], kc['centroid_lon'], vl, vo):.2f} km del crater ({kc.get('geo_class')}); escena vrp {r['K']['record']['vrp_mw']} n_anom {r['K']['record']['n_anomalous_pixels']} dc {r['K']['record']['distance_class']} discarded {r['K']['record'].get('discarded_reason')}")
# nulo del pareo: todas las pasadas del lote con MIROVA > 0 y port fisica > 0
pares = [(OBJ[i]["mirova_vrp"], rs[i]["port"]["fisica"]["vrp_mw"], i) for i in rs if i in OBJ and rs[i].get("estado") == "ok"
         and (OBJ[i].get("mirova_vrp") or 0) > 0 and (rs[i]["port"]["fisica"]["vrp_mw"] or 0) > 0]
lr = lambda a, b: abs(math.log(b/a))
real = [lr(a, b) for a, b, _ in pares]
print(f"\npares MIROVA>0 y port>0 en el lote: {len(pares)}; |log ratio| mediana real {np.median(real):.3f}")
seis = [lr(a, b) for a, b, i in pares if i in SEIS]
print(f"  las 6: {[round(x, 3) for x in seis]} mediana {np.median(seis):.3f}")
random.seed(0)
mir = [a for a, _, _ in pares]; meds = []; meds6 = []
for _ in range(2000):
    sh = mir[:]; random.shuffle(sh)
    b = [lr(s, p[1]) for s, p in zip(sh, pares)]; meds.append(np.median(b))
    # nulo restringido a las 6: emparejar cada port de las 6 con un MIROVA al azar del lote con VRP >= 1
    prot = [a for a in mir if a >= 1.0]
    meds6.append(np.median([lr(random.choice(prot), p[1]) for p in pares if p[2] in SEIS]))
print(f"  nulo barajado (todo el lote): mediana |log ratio| p5 {np.percentile(meds, 5):.3f} p50 {np.median(meds):.3f}")
print(f"  nulo 6 vs MIROVA>=1 al azar: p1 {np.percentile(meds6, 1):.3f} p50 {np.median(meds6):.3f}; fraccion <= real6 {np.mean(np.array(meds6) <= np.median(seis)):.4f}")
prot_pairs = [(a, b, i) for a, b, i in pares if a >= 1.0]
print(f"  protegidas (MIROVA>=1) del lote con port>0: {len(prot_pairs)}; |log ratio| mediana {np.median([lr(a,b) for a,b,_ in prot_pairs]):.3f}")

print("\n== (X0, Y0) de MIROVA contra el crater de volcanoes.yaml, y rango de distancia AL CRATER de los pixeles del port")
for i in SEIS:
    o = OBJ[i]; g = o["grilla"]; v = V[o["volcan"]]
    vl, vo = v.get("vent_lat", v["lat"]), v.get("vent_lon", v["lon"])
    t = TR.setdefault(g["epsg"], Transformer.from_crs(g["epsg"], 4326, always_xy=True))
    x0lon, x0lat = t.transform(g["X0"], g["Y0"])
    dc = [hav(*latlon(g, p[0], p[1], conv), vl, vo) for p in rs[i]["port"]["fisica"]["pixeles"]]
    dx = [p[3] for p in rs[i]["port"]["fisica"]["pixeles"]]
    print(f"  {i} {o['volcan']}: X0Y0 a {hav(x0lat, x0lon, vl, vo):.2f} km del crater | pixeles: al crater {min(dc):.2f} a {max(dc):.2f} km; a X0Y0 (runner) {min(dx):.2f} a {max(dx):.2f} km")

print("\n== evaluar.dist_regla('cercano') mide desde (X0,Y0) de MIROVA; ¿cambia la clase summit/far si se mide desde el crater?")
flips = []; n = 0
for i, r in rs.items():
    if r.get("estado") != "ok" or i not in OBJ: continue
    px = r["port"]["fisica"]["pixeles"]
    if not px: continue
    o = OBJ[i]; g = o["grilla"]; v = V[o["volcan"]]; inner = v["inner_radius_km"]
    vl, vo = v.get("vent_lat", v["lat"]), v.get("vent_lon", v["lon"])
    dx = min(p[3] for p in px); dc = min(hav(*latlon(g, p[0], p[1], conv), vl, vo) for p in px)
    n += 1
    if (dx <= inner) != (dc <= inner):
        flips.append((i, o["volcan"], o["hora_utc"], o.get("clase"), round(dx, 2), round(dc, 2), inner))
print(f"  pasadas del lote con pixeles del port: {n}; cambian de clase: {len(flips)}")
for f in flips: print("   ", f)
