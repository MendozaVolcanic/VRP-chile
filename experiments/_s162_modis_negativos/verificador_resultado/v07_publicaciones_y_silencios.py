# -*- coding: utf-8 -*-
"""Verificador, R4 y hueco de R1: (1) geometria de las dos publicaciones del port en neg_resto (fila/columna del
pixel, distancia al centro de la grilla y al crater de volcanoes.yaml, inner_radius, noche); (2) TODOS los neg_resto
evaluables donde el port detecto algo (npix > 0) y que el tablero NO publico, con su distancia y clase: si alguno
estuviera al borde del inner, x dependeria del ancla; (3) el mismo predicado con el frontend/index.html de origin/main
de hoy (otro camino: el tablero que ve el operador hoy, no el del commit base).
Pregunta 1: si el lector del autor hubiera clasificado mal una publicacion, mi recomputo de dcen y la corrida con otro
HTML lo verian. Pregunta 2: control positivo: los 11 controles pos_prot deben publicar con los dos HTML."""
import json, sys, math, collections, importlib.util
from pathlib import Path
import numpy as np, yaml
D, ARB, RUN, OUT = (Path(a) for a in sys.argv[1:5])
def modulo(n, r):
    s = importlib.util.spec_from_file_location(n, r); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
A = modulo("an", ARB / "experiments/_s159/portes/04_analizar.py"); B = A.B
obj = {o["id"]: o for o in json.loads((D / "objetivos_neg_resto_modis.json").read_text(encoding="utf-8"))}
res = {}
for f in sorted(RUN.rglob("resultados_MODIS_*.json")):
    for r in json.loads(f.read_text(encoding="utf-8")): res[r["id"]] = r
inner = B.inner_desde_html()
vol = yaml.safe_load((ARB / "volcanoes.yaml").read_text(encoding="utf-8"))
vols = {v["name"]: v for v in (vol["volcanoes"] if isinstance(vol, dict) else vol)}
def hav(a, b, c, d):
    a, b, c, d = map(math.radians, (a, b, c, d)); h = math.sin((c-a)/2)**2 + math.cos(a)*math.cos(c)*math.sin((d-b)/2)**2
    return 2*6371.0*math.asin(math.sqrt(h))
def pix_latlon(g, fr, fc):
    x = g["ul_x"] + g["celda"]*(fc+.5); y = g["ul_y"] - g["celda"]*(fr+.5)
    dx, dy = x - g["X0"], y - g["Y0"]
    lat = g["centro_lat"] + dy/111320.0; lon = g["centro_lon"] + dx/(111320.0*math.cos(math.radians(g["centro_lat"])))
    return lat, lon, math.hypot(dx, dy)/1000
print("inner_radius_km (HTML del arbol):", inner)
print("\n== 1. las dos publicaciones ==")
for i in (1120, 1251):
    o, r = obj[i], res[i]; p = r["port"]["fisica"]; g = o["grilla"]; v = vols[o["volcan"]]
    campos = {k: v.get(k) for k in ("lat", "lon", "vent_lat", "vent_lon", "mirova_center", "inner_radius_km", "radius_km")}
    print(f"\n-- {i} {o['volcan']} {o['hora_utc']} {o['sensor']} z={o['z']} estrato_z={o['estrato_z']} partida={o.get('partida')} peso={o['peso']:.2f}")
    print("   volcanoes.yaml:", campos)
    print("   grilla centro:", (g["centro_lat"], g["centro_lon"]), "epsg", g["epsg"], "| dist centro grilla -> lat/lon yaml:", round(hav(g["centro_lat"], g["centro_lon"], v["lat"], v["lon"]), 3), "km; -> vent:", round(hav(g["centro_lat"], g["centro_lon"], v.get("vent_lat") or v["lat"], v.get("vent_lon") or v["lon"]), 3), "km")
    for q in p["pixeles"]:
        lat, lon, dkm = pix_latlon(g, q[0], q[1])
        print(f"   pixel fila {q[0]} col {q[1]} (centro 25,25) campos={q[2:]} -> lat {lat:.4f} lon {lon:.4f}; dist al centro de grilla {dkm:.3f} km; al crater (vent) {hav(lat, lon, v.get('vent_lat') or v['lat'], v.get('vent_lon') or v['lon']):.3f} km; al lat/lon yaml {hav(lat, lon, v['lat'], v['lon']):.3f} km; inner {inner[o['volcan']]}")
    print("   dist_centroide (04_analizar):", round(A.dist_centroide(p, g), 3), "| npix", p["npix"], "vrp", p["vrp_mw"], "n_p1", p["n_p1"], "n_p2", p["n_p2"], "n_abs", p["n_abs"])
    print("   noche: solar_zenith", r["geometria_centro"]["solar_zenith"], "dayflag", r["dayflag"], "| sensor_zenith", r["geometria_centro"]["sensor_zenith"])
    print("   otras variantes del port:", {k: (r["port"][k] or {}).get("npix") for k in r["port"]})
    print("   K record (pc, dc, vrp):", ((r["K"]["record"] or {}).get("primary_cluster"), (r["K"]["record"] or {}).get("distance_class"), (r["K"]["record"] or {}).get("vrp_mw")))
    print("   MIROVA en la poblacion:", o["mirova"])
print("\n== 2. neg_resto evaluables con npix > 0 (cualquier variante) ==")
neg_ev = [i for i, o in obj.items() if o["clase"] == "neg_resto" and res.get(i, {}).get("estado") == "ok"
          and (res[i]["port"]["fisica"] or {}).get("motivo_vacio") != "escena_invalida" and res[i].get("port_estado") != "grilla_incompleta"]
print("neg_resto evaluables:", len(neg_ev))
cnt = collections.Counter()
for i in neg_ev:
    for k, p in res[i]["port"].items():
        if p and p.get("npix"): cnt[k] += 1
print("con npix>0 por variante:", dict(cnt))
casos, idx = [], []
for i in neg_ev:
    p = res[i]["port"]["fisica"]
    if p and p.get("npix"):
        p = dict(p); p["_dcen"] = A.dist_centroide(p, obj[i]["grilla"])
        rp = A.record_port(p, inner[obj[i]["volcan"]], obj[i]["sensor"])
        print(f"  fisica npix>0: {i} {obj[i]['volcan']} {obj[i]['hora_utc']} npix {p['npix']} vrp {p['vrp_mw']:.3f} dcen {p['_dcen']:.3f} inner {inner[obj[i]['volcan']]} clase {rp['distance_class']}")
# 3. predicado con el HTML de origin/main (hoy) vs el del arbol, sobre TODOS los evaluables (port y K) y controles
ids_ev = [i for i in sorted(obj) if res.get(i, {}).get("estado") == "ok" and (res[i]["port"]["fisica"] or {}).get("motivo_vacio") != "escena_invalida" and res[i].get("port_estado") != "grilla_incompleta"]
casos, idx = [], []
for i in ids_ev:
    o = obj[i]; p = dict(res[i]["port"]["fisica"])
    if p.get("npix"): p["_dcen"] = A.dist_centroide(p, o["grilla"])
    rp = A.record_port(p, inner[o["volcan"]], o["sensor"])
    casos.append([A.slim({k: x for k, x in rp.items() if not k.startswith("_")}), inner[o["volcan"]]]); idx.append((i, "port"))
    krec = (res[i].get("K") or {}).get("record")
    if krec is not None:
        casos.append([A.slim(krec), inner[o["volcan"]]]); idx.append((i, "K"))
P_arbol = dict(zip(idx, B.correr_node(casos)))
B.HTML = OUT / "index_origin_main.html"
P_main = dict(zip(idx, B.correr_node(casos)))
print("\n== 3. predicado: HTML del arbol (0e18e1053) vs HTML de origin/main de hoy, sobre", len(casos), "casos ==")
dif = [(k, P_arbol[k], P_main[k]) for k in idx if P_arbol[k][4] != P_main[k][4]]
print("casos con publicacion distinta entre los dos HTML:", len(dif), dif[:20])
for nombre, P in (("arbol", P_arbol), ("main", P_main)):
    neg = [i for i in ids_ev if obj[i]["clase"] == "neg_resto"]
    x = sum(P[(i, "port")][4] for i in neg)
    prot = [i for i in ids_ev if obj[i]["clase"] == "control_s159" and obj[i]["clase_s159"] == "pos_prot"]
    print(f"  HTML {nombre}: x port en neg_resto = {x} de {len(neg)}; port publica en protegidas {sum(P[(i,'port')][4] for i in prot)} de {len(prot)}; K publica en protegidas {sum(P[(i,'K')][4] for i in prot)} de {len(prot)} (pub_prod declarado {sum(obj[i]['pub_prod'] for i in prot)}); K publica en neg_resto {sum(P[(i,'K')][4] for i in neg)}")
print("detalle de las dos publicaciones (summit, valid, art, disp, publica):", {i: (P_arbol[(i, 'port')], P_main[(i, 'port')]) for i in (1120, 1251)})
