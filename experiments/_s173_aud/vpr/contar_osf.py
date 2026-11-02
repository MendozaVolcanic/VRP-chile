# -*- coding: utf-8 -*-
"""Reproduce con un script propio las cifras del §4.2 y §7 del pre-registro sobre el OSF v2.5 de MIROVA (R25):
filas chilenas 2025-02-15 a 12-31, pisos de VRP por resolucion, protegidas OSF (noche por elevacion solar del
proyecto, class 1, VRP >= 1e6 W, pixel mas caliente a <= inner_radius_km del crater de volcanoes.yaml), lejanas
(class 1 >= 1 MW fuera del radio), ambiguas (class 0 >= 1 MW dentro), Dayflag contra la noche del proyecto, y si K
de disco (origin/main exportado) publica cada protegida (pareo +-120 s, predicado del tablero con node).

Las dos preguntas: (1) si K perdiera protegidas del OSF, el pareo + node lo ve (control: las protegidas sin record a
+-120 s se listan aparte, no se cuentan como publicadas); (2) instrumento muerto: imprime filas leidas, filas chilenas
y records de K cargados; ceros delatan. Control positivo del pareo: la mediana de |dt| tiene que ser 0 s (timeUTC al
minuto, como dice el pre-registro) y se imprime la distribucion.
Uso: python contar_osf.py <export_root> <osf_csv> <crater: vent|centro>
"""
import collections
import csv
import math
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

EXPORT = Path(sys.argv[1]); OSF = Path(sys.argv[2]); CRATER = sys.argv[3] if len(sys.argv) > 3 else "vent"
os.environ["VRP_PROFILE"] = "mirova_equivalent"
sys.path.insert(0, str(EXPORT)); sys.path.insert(0, str(EXPORT / "scripts"))
import yaml  # noqa: E402
import banco_paridad as BP  # noqa: E402
from auto_audit_weekly import es_pasada_diurna_descartada  # noqa: E402

NOMBRES = {"Chaitén": "Chaiten", "Chillán, Nevados de": "NevadosDeChillan", "Láscar": "Lascar",
           "Planchón-Peteroa": "PlanchonPeteroa", "Puyehue-Cordón Caulle": "PuyehueCordonCaulle",
           "Copahue": "Copahue", "Isluga": "Isluga", "Lastarria": "Lastarria", "Llaima": "Llaima",
           "Villarrica": "Villarrica", "Tupungatito": "Tupungatito"}
RES_BUCKET = {"375": "VIIRS375", "750": "VIIRS750", "1000": "MODIS"}
# Volc_LAT/Volc_LON del OSF (listado en esta sesion con errors='replace'), redondeados a 2 decimales
POR_COORD = {(-42.83, -72.65): "Chaiten", (-36.86, -71.38): "NevadosDeChillan", (-37.86, -71.18): "Copahue",
             (-19.15, -68.83): "Isluga", (-25.17, -68.51): "Lastarria", (-38.69, -71.73): "Llaima",
             (-23.37, -67.73): "Lascar", (-35.22, -70.57): "PlanchonPeteroa", (-40.59, -72.12): "PuyehueCordonCaulle",
             (-39.42, -71.93): "Villarrica"}
INICIO, FIN = "2025-02-15", "2025-12-31"

vol = {v["name"]: v for v in yaml.safe_load(open(EXPORT / "volcanoes.yaml", encoding="utf-8"))["volcanoes"]}
def crater(n):
    v = vol[n]
    if CRATER == "vent" and v.get("vent_lat") is not None:
        return v["vent_lat"], v["vent_lon"]
    return v["lat"], v["lon"]
def hav(a, b, c, d):
    R = 6371.0088
    p1, p2 = math.radians(a), math.radians(c); dp = p2 - p1; dl = math.radians(d - b)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))

filas = []; n_total = 0
with open(OSF, encoding="latin-1") as fh:
    for r in csv.DictReader(fh):
        n_total += 1
        # el nombre viene con acentos en una codificacion que no es UTF-8: se identifica por Volc_LAT/Volc_LON
        n = NOMBRES.get(r["Volc_Name"]) or POR_COORD.get((round(float(r["Volc_LAT"]), 2), round(float(r["Volc_LON"]), 2)))
        if n is None:
            continue
        dt = datetime.strptime(r["timeUTC"], "%d/%m/%Y %H:%M").replace(tzinfo=timezone.utc)
        d = dt.strftime("%Y-%m-%d")
        if not (INICIO <= d <= FIN):
            continue
        b = RES_BUCKET[r["Resolution"]]
        lat, lon = vol[n]["lat"], vol[n]["lon"]
        noche = not es_pasada_diurna_descartada(b, lat, lon, dt)
        cl, cn = crater(n)
        filas.append({"vol": n, "b": b, "dt": dt, "vrp_w": float(r["VRP"]), "class": int(float(r["class"])),
                      "dayflag": int(float(r["Dayflag"])), "noche": noche, "sat": r["Satellite"],
                      "dist_crater_km": hav(float(r["LAT"]), float(r["LON"]), cl, cn),
                      "max_dist_m": float(r["Max_Dist"]), "satzen": float(r["SatZen"]), "npix": r["Npix"]})
print("filas leidas", n_total, "| chilenas %s a %s:" % (INICIO, FIN), len(filas), "| por volcan:",
      dict(collections.Counter(f["vol"] for f in filas)))
print("Tupungatito:", sum(f["vol"] == "Tupungatito" for f in filas), "| codigos Satellite:",
      dict(collections.Counter((f["sat"], f["b"]) for f in filas)))
print("crater usado:", CRATER)
for b in BP.BUCKETS:
    v = [f["vrp_w"] / 1e6 for f in filas if f["b"] == b]
    print("  piso de VRP %-9s min %.3f MW (n %d)" % (b, min(v), len(v)))
# Dayflag contra noche del proyecto
c = collections.Counter((f["dayflag"], f["noche"]) for f in filas)
print("Dayflag x noche_proyecto (dayflag, noche):", dict(c))
for f in filas:
    if f["dayflag"] == 0 and not f["noche"]:
        print("   Dayflag 0 pero dia del proyecto:", f["vol"], f["b"], f["dt"].strftime("%Y-%m-%d %H:%M"), "%.2f MW" % (f["vrp_w"] / 1e6))

# K de disco en 2025: records nocturnos con predicado node
coords = BP._coords_por_volcan(); inner = BP.inner_desde_html()
recs = BP.cargar_nuestros(coords, inner, (INICIO, FIN))
print("records nocturnos de K 2025 cargados:", len(recs), "| por sensor:", dict(collections.Counter(r["b"] for r in recs)))
assert recs, "instrumento muerto: 0 records"
idx = collections.defaultdict(list)
for r in recs:
    idx[(r["vol"], r["b"])].append(r)
for k in idx:
    idx[k].sort(key=lambda x: x["dt"])
def parear(f):
    cand = [r for r in idx.get((f["vol"], f["b"]), []) if abs((r["dt"] - f["dt"]).total_seconds()) <= 120]
    return cand

print("\n== protegidas OSF (noche proyecto, class 1, >= 1 MW, pixel mas caliente <= inner) ==")
dts = []
for b in BP.BUCKETS:
    prot = [f for f in filas if f["b"] == b and f["noche"] and f["class"] == 1 and f["vrp_w"] >= 1e6
            and f["dist_crater_km"] <= vol[f["vol"]]["inner_radius_km"]]
    lej = [f for f in filas if f["b"] == b and f["noche"] and f["class"] == 1 and f["vrp_w"] >= 1e6
           and f["dist_crater_km"] > vol[f["vol"]]["inner_radius_km"]]
    amb_in = [f for f in filas if f["b"] == b and f["noche"] and f["class"] == 0 and f["vrp_w"] >= 1e6
              and f["dist_crater_km"] <= vol[f["vol"]]["inner_radius_km"]]
    amb_out = [f for f in filas if f["b"] == b and f["noche"] and f["class"] == 0 and f["vrp_w"] >= 1e6
               and f["dist_crater_km"] > vol[f["vol"]]["inner_radius_km"]]
    bajo = [f for f in filas if f["b"] == b and f["noche"] and f["class"] == 1 and f["vrp_w"] < 1e6
            and f["dist_crater_km"] <= vol[f["vol"]]["inner_radius_km"]]
    pub = sin_rec = dos = 0; perdidas = []
    for f in prot:
        c = parear(f)
        if not c:
            sin_rec += 1; continue
        if len(c) > 1:
            dos += 1
        dts.append(min(abs((r["dt"] - f["dt"]).total_seconds()) for r in c))
        if any(r["pub"] for r in c):
            pub += 1
        else:
            perdidas.append((f["vol"], f["dt"].strftime("%Y-%m-%d %H:%M"), round(f["vrp_w"] / 1e6, 2)))
    print("%-9s protegidas %3d por volcan %s | K publica %3d | sin record +-120 s %d | pareadas a 2 records %d | bajo 1 MW %d | lejanas class1 %d (%s) | ambiguas class0 dentro %d (%s) fuera %d" % (
        b, len(prot), dict(collections.Counter(f["vol"] for f in prot)), pub, sin_rec, dos, len(bajo),
        len(lej), dict(collections.Counter(f["vol"] for f in lej)), len(amb_in), dict(collections.Counter(f["vol"] for f in amb_in)), len(amb_out)))
    if perdidas:
        print("     K NO publica:", perdidas[:20])
    if lej:
        d = sorted(f["dist_crater_km"] for f in lej); m = sorted(f["vrp_w"] / 1e6 for f in lej)
        print("     lejanas: dist %.1f a %.1f km, mediana VRP %.1f MW, fechas %s a %s" % (
            d[0], d[-1], m[len(m) // 2], min(f["dt"] for f in lej).strftime("%Y-%m-%d"), max(f["dt"] for f in lej).strftime("%Y-%m-%d")))
print("|dt| de pareo (s): distribucion", dict(collections.Counter(dts)))
