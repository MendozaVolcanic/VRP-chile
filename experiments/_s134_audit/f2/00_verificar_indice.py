# -*- coding: utf-8 -*-
"""F2/00 - Verificacion del indice de TIF antes de usarlo.

LAS DOS PREGUNTAS:
1. Si el indice estuviera completamente roto (nombres que no matchean, timestamps
   corridos), esta medicion lo veria? SI: comparo el timestamp del nombre de archivo
   contra acquisition_utc en las filas donde AMBOS existen; si no coincidieran el
   error saltaria. Y listo los nombres reales contra los 11 canonicos.
2. Si el instrumento estuviera muerto (csv vacio / no baja), el resultado se veria
   distinto? SI: n=0 filas es distinguible de n=18885. Reporto n explicito.
Read-only.
"""
import csv, io, os, re, sys, datetime as dt
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
IDX = os.path.join(AQUI, "index.csv")

RE_FN = re.compile(r"(\d{8})_(\d{6})_([A-Za-z0-9]+)(_lm)?\.tif$")
TIER_A = {"Chaiten","Copahue","Isluga","Lascar","Lastarria","Llaima",
          "NevadosDeChillan","PlanchonPeteroa","PuyehueCordonCaulle",
          "Tupungatito","Villarrica"}

rows = list(csv.DictReader(open(IDX, encoding="utf-8")))
print("filas totales del indice:", len(rows))
print("columnas:", list(rows[0].keys()) if rows else "SIN DATO")

vols = sorted(set(r["volcano"] for r in rows))
print("\nvolcanes distintos en el indice (n=%d):" % len(vols))
print(vols)
print("\ncanonicos NO presentes tal cual:", sorted(TIER_A - set(vols)))
print("presentes que NO son canonicos:", sorted(set(vols) - TIER_A))

vacias = sum(1 for r in rows if not (r["acquisition_utc"] or "").strip())
print("\nacquisition_utc vacio: %d de %d (%.1f%%)" % (vacias, len(rows), 100*vacias/len(rows)))

sensores = {}
for r in rows: sensores[r["sensor"]] = sensores.get(r["sensor"], 0) + 1
print("sensores:", sensores)

# CONTROL: timestamp del nombre vs acquisition_utc donde ambos existen
difs, sin_match = [], 0
for r in rows:
    a = (r["acquisition_utc"] or "").strip()
    m = RE_FN.search(r["tif_path"].replace("\\", "/"))
    if not a or not m:
        if not m: sin_match += 1
        continue
    tfn = dt.datetime.strptime(m.group(1)+m.group(2), "%Y%m%d%H%M%S").replace(tzinfo=dt.timezone.utc)
    ta = dt.datetime.fromisoformat(a.replace("Z", "+00:00"))
    if ta.tzinfo is None: ta = ta.replace(tzinfo=dt.timezone.utc)
    difs.append(abs((tfn - ta).total_seconds()))
print("tif_path que NO matchea el patron de nombre:", sin_match)
if difs:
    difs.sort()
    n = len(difs)
    print("\nCONTROL nombre-vs-acquisition_utc (n=%d filas con ambos):" % n)
    print("  identicos (0 s): %d (%.1f%%)" % (sum(1 for d in difs if d == 0), 100*sum(1 for d in difs if d==0)/n))
    print("  <=60 s: %.1f%%   mediana: %.0f s   max: %.0f s" %
          (100*sum(1 for d in difs if d <= 60)/n, difs[n//2], difs[-1]))
else:
    print("SIN DATO: ninguna fila tiene ambos timestamps")

# Cobertura temporal y por volcan desde 2026-06-01, VIIRS375
D0 = dt.datetime(2026, 6, 1, tzinfo=dt.timezone.utc)
cnt = {}
tmax = None
for r in rows:
    m = RE_FN.search(r["tif_path"].replace("\\", "/"))
    if not m: continue
    t = dt.datetime.strptime(m.group(1)+m.group(2), "%Y%m%d%H%M%S").replace(tzinfo=dt.timezone.utc)
    tmax = t if tmax is None or t > tmax else tmax
    if t >= D0 and r["sensor"] == "VIIRS375":
        cnt[r["volcano"]] = cnt.get(r["volcano"], 0) + 1
print("\npasada mas reciente del indice (por nombre):", tmax)
print("VIIRS375 desde 2026-06-01 por volcan:", dict(sorted(cnt.items(), key=lambda x: -x[1])))
