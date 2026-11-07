# -*- coding: utf-8 -*-
"""V5-H: 309 por otro camino. (a) elevacion solar con la formula NOAA propia (no store._solar_elevation) para las 194 protegidas;
(b) ¿tenemos record nuestro en esas pasadas diurnas? (si el pipeline las descarta, no debe haber); (c) sensibilidad de 'protegida nocturna vecina'
a la ventana (6, 12, 18 h) y distancia en horas a la mas cercana.
Preg 1: si la clasificacion diurna del auditor estuviera rota, mi elevacion propia daria otro reparto (>0 para las 42, <=0 para las 152 restantes).
Preg 2: control positivo: pasadas nocturnas reales de la misma lista (04-07 UTC) deben dar elevacion <0; si mi formula estuviera muerta daria todo igual.
Universo: protegidas (lectura A, >=1 MW, clave_pasada) de la referencia unificada de la base, aw.VOLS x aw.SENSORS, 2026-09-01..2026-11-07."""
import collections, json, math, os, pickle, sys
from datetime import datetime, timezone, timedelta
sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"C:\Users\nmend\vrp-temporales\s175_audit\f5\root"
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "scripts"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import auto_audit_weekly as aw, clase_mirova as cm
B = pickle.load(open(r"C:\Users\nmend\vrp-temporales\s175_audit\f5\f5_base.pkl", "rb"))
def elev(lat, lon, d):
    # algoritmo NOAA (Meeus simplificado), d aware UTC
    jd = d.timestamp() / 86400.0 + 2440587.5
    n = jd - 2451545.0
    L = (280.460 + 0.9856474 * n) % 360
    g = math.radians((357.528 + 0.9856003 * n) % 360)
    lam = math.radians(L + 1.915 * math.sin(g) + 0.020 * math.sin(2 * g))
    eps = math.radians(23.439 - 0.0000004 * n)
    dec = math.asin(math.sin(eps) * math.sin(lam))
    ra = math.atan2(math.cos(eps) * math.sin(lam), math.cos(lam))
    gmst = (280.46061837 + 360.98564736629 * n) % 360
    ha = math.radians((gmst + lon) - math.degrees(ra))
    la = math.radians(lat)
    return math.degrees(math.asin(math.sin(la) * math.sin(dec) + math.cos(la) * math.cos(dec) * math.cos(ha)))
coords = B["coords"]
prot = {}
for f in B["filas"]:
    if f["volcano"] not in aw.VOLS or f["sensor_bucket"] not in aw.SENSORS or not ("2026-09-01" <= f["fecha_utc"][:10] <= "2026-11-07"):
        continue
    if cm.alerta_protegida(f):
        k = cm.clave_pasada(f)
        prot[k] = f
rows = []
for k, f in prot.items():
    d = datetime.strptime(f["fecha_utc"][:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    lat, lon = coords[f["volcano"]]
    rows.append({"k": k, "vol": f["volcano"], "b": f["sensor_bucket"], "d": d, "e_mia": elev(lat, lon, d), "e_aud": aw._solar_elevation(lat, lon, d),
                 "diurna_aud": aw.es_pasada_diurna_descartada(f["sensor_bucket"], lat, lon, d)})
print("protegidas:", len(rows))
print("max |elev mia - elev store|:", round(max(abs(r["e_mia"] - r["e_aud"]) for r in rows), 3), "grados")
dis = [r for r in rows if (r["e_mia"] > 0) != r["diurna_aud"]]
print("discrepancias de clasificacion (mia vs auditor):", len(dis), [(r["k"], round(r["e_mia"], 2)) for r in dis])
dia = [r for r in rows if r["diurna_aud"]]; noc = [r for r in rows if not r["diurna_aud"]]
print("diurnas:", len(dia), "por volcan", dict(collections.Counter(r["vol"] for r in dia)), "| elevacion min/max diurnas", round(min(r["e_mia"] for r in dia), 1), round(max(r["e_mia"] for r in dia), 1))
print("CONTROL nocturnas: n", len(noc), "elev max", round(max(r["e_mia"] for r in noc), 1), "(debe ser <=0)")
# (b) records nuestros en pasadas diurnas
tenemos = 0; sin = 0
cache = {}
for r in dia:
    if r["vol"] not in cache:
        cache[r["vol"]] = json.load(open(os.path.join(ROOT, "data", "mirova_equivalent", r["vol"] + ".json"), encoding="utf-8"))["records"]
    t = r["d"]
    hit = [x for x in cache[r["vol"]] if abs((datetime.strptime(x["datetime_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc) - t).total_seconds()) <= 120 and aw.our_bucket(x["sensor"]) == r["b"]]
    tenemos += bool(hit); sin += not hit
print("pasadas diurnas protegidas CON record nuestro (+-120 s, mismo bucket):", tenemos, "SIN:", sin)
# (c) sensibilidad de la ventana
todas_al = collections.defaultdict(list)
for k, f in prot.items():
    pass
for W in (6, 12, 18):
    con = collections.Counter()
    for r in dia:
        vec = [x for x in noc if x["vol"] == r["vol"] and abs((x["d"] - r["d"]).total_seconds()) < W * 3600]
        con[(r["vol"])] += bool(vec)
    print(f"ventana {W} h: diurnas con protegida nocturna vecina (mismo volcan, cualquier sensor):", sum(con.values()), "de", len(dia), dict(con))
hh = sorted(round(min(abs((x["d"] - r["d"]).total_seconds()) for x in noc if x["vol"] == r["vol"]) / 3600, 1) for r in dia if any(x["vol"] == r["vol"] for x in noc))
print("horas a la protegida nocturna mas cercana (mismo volcan):", hh)
