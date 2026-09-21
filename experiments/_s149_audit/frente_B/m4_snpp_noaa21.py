# -*- coding: utf-8 -*-
"""Frente B. M4: por que la tabla casi no lista Suomi NPP y desde cuando lista NOAA-21.
(a) Es un artefacto del pareo a +-120 s? Distribucion del desfase a la fila de tabla MAS CERCANA
    (mismo volcan y bucket) para pasadas SNPP sin fila: si fuera desfase de granulo habria un pico
    en +-6 min. Control: lo mismo para NOAA20 (debe estar en ~0).
(b) Fecha de la primera fila de tabla que parea con un record NOAA-21; tasa semanal NOAA21 y SNPP.
(c) La tasa SNPP depende del cenit del sensor, del volcan, o de si hubo otra pasada VIIRS cerca?
(d) Las ALERTA solo-OCR (sin fila de tabla): de que satelite nuestro son.
Instrumento: (1) un pareo roto daria 0 en todos los satelites, y NOAA20 da 81-91 %, asi que no esta roto;
(2) n por celda impreso.
"""
import bisect, collections, csv, io, json, os, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
from auto_audit_weekly import _coords_por_volcan, es_pasada_diurna_descartada  # noqa
from pipeline.mirova_csv_loader import normalize_sensor, normalize_volcano_name  # noqa
VOLS = ["Lascar", "Lastarria", "Isluga", "Tupungatito", "PlanchonPeteroa", "NevadosDeChillan",
        "Llaima", "Villarrica", "Copahue", "PuyehueCordonCaulle", "Chaiten"]
coords = _coords_por_volcan()
SNAP = ROOT / "data/mirova_reference/mirova_v1_snapshot"
UTC = timezone.utc


def sat(s):
    for k in ("SNPP", "NOAA20", "NOAA21"):
        if k in s: return k


recs = []
for v in VOLS:
    for r in json.load(open(ROOT / "data/mirova_equivalent" / (v + ".json"), encoding="utf-8"))["records"]:
        s = r.get("sensor") or ""
        if not s.startswith("VIIRS") or s.endswith("_750"): continue
        dt = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=UTC)
        if dt < datetime(2026, 1, 29, tzinfo=UTC): continue
        lat, lon = coords[v]
        if es_pasada_diurna_descartada("VIIRS375", lat, lon, dt): continue
        recs.append((v, sat(s), dt, r.get("sensor_zenith_deg")))
cons = collections.defaultdict(list); alert_ocr = []
cons_tipo = {}
for r in csv.DictReader(open(SNAP / "registro_vrp_consolidado.csv", encoding="utf-8")):
    v = normalize_volcano_name(r["Volcan"]); b = normalize_sensor(r["Sensor"])
    if v and b == "VIIRS375":
        t = datetime.strptime(r["Fecha_Satelite_UTC"][:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)
        cons[v].append(t); cons_tipo[(v, t)] = r["Tipo_Registro"]
for v in cons: cons[v].sort()


def cerca(lista, t):
    i = bisect.bisect_left(lista, t)
    c = [abs((lista[j] - t).total_seconds()) for j in (i - 1, i) if 0 <= j < len(lista)]
    return min(c) if c else None


print("(a) desfase a la fila de tabla VIIRS375 mas cercana, pasadas nocturnas nuestras desde 2026-01-29")
for st in ("NOAA20", "SNPP", "NOAA21"):
    h = collections.Counter()
    for v, s, dt, z in recs:
        if s != st: continue
        if st == "NOAA21" and dt < datetime(2026, 8, 1, tzinfo=UTC): continue
        d = cerca(cons[v], dt)
        k = "<=2min" if d <= 120 else "2-8min" if d <= 480 else "8-20min" if d <= 1200 else "20-40min" if d <= 2400 else "40-70min" if d <= 4200 else ">70min"
        h[k] += 1
    n = sum(h.values())
    print("   %-7s n=%5d | %s" % (st, n, "  ".join("%s %.0f%%" % (k, 100.0 * h[k] / n) for k in ("<=2min", "2-8min", "8-20min", "20-40min", "40-70min", ">70min"))))

print("\n(b) primera fila de tabla que parea (+-120 s) con un record nuestro NOAA-21:")
prim = sorted(dt for v, s, dt, z in recs if s == "NOAA21" and cerca(cons[v], dt) <= 120)
print("   ", prim[:3], "| n total", len(prim))
print("   tasa por quincena (% con fila en tabla, n): quincena | NOAA20 | NOAA21 | SNPP")
q = collections.defaultdict(lambda: [0, 0])
for v, s, dt, z in recs:
    k = (dt.strftime("%Y-%m") + ("a" if dt.day <= 15 else "b"), s)
    q[k][0] += 1; q[k][1] += cerca(cons[v], dt) <= 120
for qq in sorted(set(k[0] for k in q)):
    print("    %s | %s" % (qq, " | ".join("%3.0f%% (%3d)" % (100.0 * q[(qq, s)][1] / q[(qq, s)][0], q[(qq, s)][0]) if q[(qq, s)][0] else "SIN DATO" for s in ("NOAA20", "NOAA21", "SNPP"))))

print("\n(c) SNPP desde 2026-02: % con fila en tabla segun cenit del sensor, y segun volcan")
zc = collections.defaultdict(lambda: [0, 0]); vc = collections.defaultdict(lambda: [0, 0])
for v, s, dt, z in recs:
    if s != "SNPP": continue
    ok = cerca(cons[v], dt) <= 120
    zb = "z?" if z is None else "z<20" if z < 20 else "z20-40" if z < 40 else "z40-55" if z < 55 else "z>=55"
    zc[zb][0] += 1; zc[zb][1] += ok; vc[v][0] += 1; vc[v][1] += ok
print("    cenit:", {k: "%.0f%% (%d)" % (100.0 * a / n, n) for k, (n, a) in sorted(zc.items())})
print("    volcan:", {k: "%.0f%% (%d)" % (100.0 * a / n, n) for k, (n, a) in sorted(vc.items())})
# mismo corte para NOAA20 (control: si el cenit explicara todo, NOAA20 tendria el mismo perfil)
zc2 = collections.defaultdict(lambda: [0, 0])
for v, s, dt, z in recs:
    if s != "NOAA20": continue
    zb = "z?" if z is None else "z<20" if z < 20 else "z20-40" if z < 40 else "z40-55" if z < 55 else "z>=55"
    zc2[zb][0] += 1; zc2[zb][1] += cerca(cons[v], dt) <= 120
print("    control NOAA20 por cenit:", {k: "%.0f%% (%d)" % (100.0 * a / n, n) for k, (n, a) in sorted(zc2.items())})
# cuando la tabla SI lista SNPP, que tipo de fila es
tt = collections.Counter()
for v, s, dt, z in recs:
    if s != "SNPP": continue
    i = bisect.bisect_left(cons[v], dt - timedelta(seconds=120))
    if i < len(cons[v]) and cons[v][i] <= dt + timedelta(seconds=120):
        tt[cons_tipo[(v, cons[v][i])]] += 1
print("    tipo de la fila de tabla cuando SI lista SNPP:", dict(tt))
tt2 = collections.Counter()
for v, s, dt, z in recs:
    if s != "NOAA20": continue
    i = bisect.bisect_left(cons[v], dt - timedelta(seconds=120))
    if i < len(cons[v]) and cons[v][i] <= dt + timedelta(seconds=120):
        tt2[cons_tipo[(v, cons[v][i])]] += 1
print("    idem NOAA20 (control):", dict(tt2))

print("\n(d) ALERTA_TERMICA_OCR VIIRS375 nocturnas SIN fila de tabla a +-120 s: satelite de nuestro record a +-120 s, por tramo")
nuestros = collections.defaultdict(list)
for v, s, dt, z in recs: nuestros[v].append((dt, s))
for v in nuestros: nuestros[v].sort()
out = collections.defaultdict(collections.Counter)
for r in csv.DictReader(open(SNAP / "registro_vrp_ocr.csv", encoding="utf-8")):
    v = normalize_volcano_name(r["Volcan"])
    if not v or normalize_sensor(r["Sensor"]) != "VIIRS375" or r["Tipo_Registro"] != "ALERTA_TERMICA_OCR": continue
    t = datetime.strptime(r["Fecha_Satelite_UTC"][:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)
    if t < datetime(2026, 1, 29, tzinfo=UTC): continue
    lat, lon = coords[v]
    if es_pasada_diurna_descartada("VIIRS375", lat, lon, t): continue
    d = cerca(cons[v], t)
    if d is not None and d <= 120: continue
    lst = nuestros[v]; tl = [x[0] for x in lst]
    i = bisect.bisect_left(tl, t - timedelta(seconds=120))
    quien = lst[i][1] if i < len(lst) and lst[i][0] <= t + timedelta(seconds=120) else "sin_record_nuestro"
    tramo = "antes 06-13" if t < datetime(2026, 6, 13, tzinfo=UTC) else "desde 06-13"
    out[tramo][quien] += 1
for k in out: print("   ", k, dict(out[k]), "n =", sum(out[k].values()))
