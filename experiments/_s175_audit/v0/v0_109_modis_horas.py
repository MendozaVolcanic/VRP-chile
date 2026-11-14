"""V0-109: las 49 filas MODIS de MIROVA sin record nuestro, son pasadas que de verdad cubren el volcan?
Camino distinto al del auditor: (1) hora del dia (UTC) de las filas MIROVA sin record vs la de las que SI tienen
record, en la misma ventana; (2) para esas fechas, que records MODIS (cualquier volcan) tenemos ese dia.
P1: si de verdad bajaramos todo, la lista (1) seria vacia; si el instrumento estuviera roto no distinguiria horas.
P2: control = las filas MIROVA con record (match) deben ser mayoria; si fueran 0 el instrumento estaria muerto.
Ventana: 2026-09-14 a 2026-11-06 (ultimo record), 11 Tier A, MODIS, nocturnas (hora UTC < 12), tabla+OCR de la base.
Insumos: base_data del auditor (git show de la base, verificado abajo con hash) y latest_consolidado_base.csv."""
import csv
import hashlib
import io
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378"
B = "752d348bc67190e53b610989877e2405d238a1bc"
INS = r"C:\Users\nmend\vrp-temporales\s175_audit\insumos"
BD = r"C:\Users\nmend\vrp-temporales\s175_audit\f0\base_data"
VOLS = ["Lascar", "Lastarria", "Isluga", "Tupungatito", "PlanchonPeteroa", "NevadosDeChillan", "Llaima", "Villarrica",
        "Copahue", "PuyehueCordonCaulle", "Chaiten"]
D0 = datetime(2026, 9, 14)


def t(s):
    s = s.strip().replace("T", " ").replace("Z", "")
    return datetime.strptime(s[:16], "%Y-%m-%d %H:%M")


# control de procedencia: base_data == git show de la base
malos = 0
recs = []
for v in VOLS:
    g = subprocess.run(["git", "-C", REPO, "show", f"{B}:data/mirova_equivalent/{v}.json"], capture_output=True).stdout
    d = json.loads(g.decode("utf-8"))
    loc = json.load(open(f"{BD}\\{v}.json", encoding="utf-8"))
    if d["records"] != loc["records"]:
        malos += 1
    for r in d["records"]:
        if r["sensor"].startswith("MODIS"):
            recs.append((v, t(r["datetime_utc"]), r["sensor"]))
print("volcanes cuyo base_data difiere de git show de la base:", malos, "de", len(VOLS))
print("records MODIS leidos:", len(recs), "ultimo:", max(x[1] for x in recs))

idx = defaultdict(list)
for v, tt, s in recs:
    idx[v].append(tt)
for k in idx:
    idx[k].sort()

mir = []
with open(INS + r"\latest_consolidado_base.csv", encoding="utf-8") as fh:
    for f in csv.DictReader(fh):
        if f["Sensor"].strip() != "MODIS":
            continue
        n = re.sub(r"[^a-z]", "", f["Volcan"].lower())
        v = {re.sub(r"[^a-z]", "", x.lower()): x for x in VOLS}.get(n)
        if not v:
            continue
        mir.append((v, t(f["Fecha_Satelite_UTC"]), f["Tipo_Registro"], f["VRP_MW"]))
hasta = max(x[1] for x in recs) - timedelta(hours=6)
con, sin = [], []
for v, tt, tipo, vrp in mir:
    if tt < D0 or tt > hasta or tt.hour >= 12:
        continue
    ts = idx[v]
    ok = any(abs((x - tt).total_seconds()) <= 120 for x in ts)
    (con if ok else sin).append((v, tt, tipo, vrp))
print(f"filas MIROVA MODIS nocturnas (<12 UTC) desde {D0:%F}: con record {len(con)}, sin record {len(sin)}")
print("hora UTC (HH) de las que SI tienen record:", sorted(Counter(x[1].hour for x in con).items()))
print("hora UTC (HH) de las que NO tienen record:", sorted(Counter(x[1].hour for x in sin).items()))
print("tipos de las sin record:", Counter((x[2], x[3]) for x in sin))
print("fechas de las sin record (n por fecha-hora):", sorted(Counter(f"{x[1]:%Y-%m-%d %H}" for x in sin).items()))

# horas de nuestros records MODIS en la ventana por volcan Lascar (control: que existen a esa hora otros dias)
print("hora UTC de nuestros records MODIS desde 2026-03-01 (todos los volcanes):",
      sorted(Counter(x[1].hour for x in recs if x[1] >= datetime(2026, 3, 1)).items()))
print("hora UTC de TODAS las filas MIROVA MODIS (todas, desde 2026-03-01) con record a +-120 s:")
c_all, c_sin = Counter(), Counter()
for v, tt, tipo, vrp in mir:
    if tt < datetime(2026, 3, 1) or tt > hasta or tt.hour >= 12:
        continue
    ok = any(abs((x - tt).total_seconds()) <= 120 for x in idx[v])
    c_all[tt.hour] += 1
    if not ok:
        c_sin[tt.hour] += 1
print("hora, filas, sin_record:", [(h, c_all[h], c_sin[h]) for h in sorted(c_all)])
# fechas completas de la ventana: records MODIS por fecha (todos los volcanes), para los dias de las pasadas enteras
for dia in ("2026-09-28", "2026-10-02", "2026-10-10"):
    hs = sorted({f"{x[1]:%H:%M}" for x in recs if f"{x[1]:%Y-%m-%d}" == dia})
    print(dia, "horas de records MODIS nuestros (11 volcanes):", hs)
