# -*- coding: utf-8 -*-
"""Frente C, auditoria S179. Instrumento c10: en R25, (1) las alertas del OSF bajo 1 MW que el §4.2 del pre-registro
manda informar y el lector no informa, y (2) las pasadas que publica solo la via o solo K, cruzadas con el OSF.

POR QUE IMPORTA. En R25 no hay negativos limpios (el OSF esta filtrado), asi que el pre-registro no mide publicaciones
de mas ahi. Pero la historia de 2025 que se va a reemplazar es la de la via: conviene saber cuantas pasadas publica
solo la via y cuantas de ellas tienen una fila del OSF (MIROVA tambien vio algo).

VARAS: publicacion de la tabla de c02; noche del proyecto; volcan del OSF por coordenadas.
LAS DOS PREGUNTAS. (1) Si la via perdiera lo debil de 2025, lo veria en el recall bajo 1 MW OSF. (2) Muerto: 0 filas
OSF aborta; control positivo: el recall de un brazo mudo es 0 (se imprime).
Limite: el OSF tiene piso (0,011 MW en 375 m, 0,176 MW en 1 km, 5,05 MW en 750 m): en VIIRS 750 no hay bajo 1 MW.
Uso: python c10_r25_bajo1_y_solo_via.py
"""
import collections, csv, json, math, statistics, sys
from datetime import datetime, timezone
import yaml
sys.stdout.reconfigure(encoding="utf-8")
MAIN = "D:/vrp-trabajo/temporales/s179-audit/main"
T = "D:/vrp-trabajo/temporales/s179-audit/c"
OSF = "D:/vrp-trabajo/worktrees/s178-lectura/data/mirova_reference/VRP_GLOBAL_ARCHIVE_2025.csv"
sys.path.insert(0, MAIN + "/scripts"); sys.path.insert(0, MAIN)
import banco_paridad as bp
RES = {"375": "VIIRS375", "750": "VIIRS750", "1000": "MODIS"}
def hav(a, b, c, d):
    p1, p2 = math.radians(a), math.radians(c)
    h = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(d - b) / 2) ** 2
    return 2 * 6371.0088 * math.asin(math.sqrt(h))
vy = {v["name"]: v for v in yaml.safe_load(open(MAIN + "/volcanoes.yaml", encoding="utf-8"))["volcanoes"]}
TIER = ["Lascar", "PuyehueCordonCaulle", "Lastarria", "Isluga", "PlanchonPeteroa", "Chaiten", "Copahue", "Llaima", "Villarrica", "NevadosDeChillan"]
tabla = [f for f in json.load(open(T + "/tabla_tag.json", encoding="utf-8")) if f["tramo"] == "R25"]
osf = collections.defaultdict(list)
n = 0
with open(OSF, encoding="latin-1") as fh:
    for r in csv.DictReader(fh):
        la, lo = float(r["Volc_LAT"]), float(r["Volc_LON"])
        if not (-56 < la < -17 and -76 < lo < -66):
            continue
        d, nom = min((hav(la, lo, vy[x]["lat"], vy[x]["lon"]), x) for x in TIER)
        if d > 10:
            continue
        dt = datetime.strptime(r["timeUTC"], "%d/%m/%Y %H:%M").replace(tzinfo=timezone.utc)
        if not ("2025-02-15" <= dt.strftime("%Y-%m-%d") <= "2025-12-31"):
            continue
        v = vy[nom]; b = RES[r["Resolution"]]
        cl, cn = (v["vent_lat"], v["vent_lon"]) if v.get("vent_lat") is not None else (v["lat"], v["lon"])
        n += 1
        osf[(nom, b)].append({"dt": dt, "mw": float(r["VRP"]) / 1e6, "cl": int(float(r["class"])),
                              "noche": not bp.es_pasada_diurna_descartada(b, v["lat"], v["lon"], dt),
                              "dentro": hav(float(r["LAT"]), float(r["LON"]), cl, cn) <= float(v["inner_radius_km"])})
print("filas OSF de los 10 volcanes en R25:", n)
if not n:
    sys.exit("ABORTA: 0 filas OSF")
idx = collections.defaultdict(list)
for f in tabla:
    if f["estado"] == "ok":
        f["_dt"] = datetime.strptime(f["dt"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        idx[(f["vol"], f["b"])].append(f)
print("\n(1) ALERTAS OSF BAJO 1 MW (noche, class 1, dentro del radio interno), pareadas a +-120 s con pasada evaluable:")
for b in ("MODIS", "VIIRS375", "VIIRS750"):
    tot = par = pk = pv = 0
    porv = collections.defaultdict(lambda: [0, 0, 0])
    for (vol, bb), filas in osf.items():
        if bb != b:
            continue
        for o in filas:
            if not (o["noche"] and o["cl"] == 1 and o["mw"] < 1.0 and o["dentro"]):
                continue
            tot += 1
            c = [f for f in idx.get((vol, b), []) if abs((f["_dt"] - o["dt"]).total_seconds()) <= 120]
            if not c:
                continue
            par += 1; pk += c[0]["pub_K"]; pv += c[0]["pub_V"]
            porv[vol][0] += 1; porv[vol][1] += c[0]["pub_K"]; porv[vol][2] += c[0]["pub_V"]
    print(f"  {b}: bajo 1 MW OSF {tot}; pareadas {par}; K publica {pk}; la via (radiante) publica {pv}; brazo mudo publicaria 0")
    print("     por volcan (pareadas, K, via):", {k: v for k, v in sorted(porv.items())})
print("\n(2) PASADAS EVALUABLES DE R25 QUE PUBLICA SOLO UN BRAZO, cruzadas con el OSF (cualquier fila nocturna del mismo sensor a +-120 s):")
for b in ("MODIS", "VIIRS375", "VIIRS750"):
    for nom, cond in (("solo la via", lambda f: f["pub_V"] and not f["pub_K"]), ("solo K", lambda f: f["pub_K"] and not f["pub_V"])):
        sel = [f for (vol, bb), fs in idx.items() if bb == b for f in fs if cond(f)]
        con = [f for f in sel if any(abs((f["_dt"] - o["dt"]).total_seconds()) <= 120 for o in osf.get((f["vol"], b), []))]
        mags = [f["mag_V"] if nom == "solo la via" else f["mag_K"] for f in sel]
        print(f"  {b}, {nom}: {len(sel)} pasadas; con fila del OSF {len(con)}; magnitud mostrada mediana "
              f"{statistics.median(mags) if mags else None}; por volcan {dict(collections.Counter(f['vol'] for f in sel))}")
