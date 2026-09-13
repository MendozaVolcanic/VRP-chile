"""S139 VERIFICADOR v2: por que el eje 6 da 0,551 (VIIRS 375, OSF 2025) y el libro de cuentas 0,689
(ratio_v375, 2026). Descompone la diferencia cambiando UN factor a la vez.

Factores: (1) anio y referencia (OSF 2025 reprocesado vs latest.php 2026 NRT); (2) unidad (pasada vs
maximo por noche a ambos lados); (3) predicado de nuestro lado (crater del auto-audit vs cualquier
pc.vrp_mw > 0); (4) mezcla de volcanes.

Instrumento. P1: si nuestra magnitud estuviera inflada o hundida en bloque, todas las variantes lo
verian igual; lo que se mide aqui es cuanto mueve cada definicion. P2: la variante que replica el
libro debe dar 0,689 y la que replica el eje 6 debe dar 0,551; si no, el instrumento no es el mismo
y la comparacion no vale. Denominadores impresos en cada linea.
"""
import csv, json, sys, io, bisect, pathlib, statistics as st
from datetime import datetime, timedelta
from collections import defaultdict
import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
R = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(R / "experiments"))
sys.path.insert(0, str(R))
from _s126_lib import VENTS, bucket, cargar_mirova  # noqa
from pipeline.mirova_csv_loader import normalize_volcano_name, normalize_sensor  # noqa

INNER = {"Lascar": 5, "Lastarria": 3, "Tupungatito": 7, "PlanchonPeteroa": 3, "NevadosDeChillan": 5,
         "Chaiten": 5, "Villarrica": 5, "Llaima": 5, "Copahue": 4, "Isluga": 5, "PuyehueCordonCaulle": 20}
MAP = {'Láscar': 'Lascar', 'Lastarria': 'Lastarria', 'Isluga': 'Isluga', 'Llaima': 'Llaima', 'Villarrica': 'Villarrica',
       'Chaitén': 'Chaiten', 'Copahue': 'Copahue', 'Planchón-Peteroa': 'PlanchonPeteroa',
       'Puyehue-Cordón Caulle': 'PuyehueCordonCaulle', 'Chillán, Nevados de': 'NevadosDeChillan', 'Tupungatito': 'Tupungatito'}


def crater(r, v):
    pc = r.get('primary_cluster') or {}
    vr = pc.get('vrp_mw') or 0
    d = pc.get('centroid_dist_km')
    return vr > 0 and d is not None and d <= INNER[v] and vr <= 50000 and r.get('distance_class') in ('summit', None)


def med(xs):
    return (round(st.median(xs), 3), len(xs)) if xs else (None, 0)


recs = {v: json.load(open(R / f"data/mirova_equivalent/{v}.json", encoding="utf-8"))["records"] for v in INNER}


def noct(r):
    sz = r.get("solar_zenith_deg")
    h = int(r["datetime_utc"][11:13])
    return not ((sz is not None and sz < 90) or (sz is None and h > 11))


def v375(r):
    return bucket(r.get("sensor")) == "v375"


# ---------- 2026, referencia latest.php (CONS+OCR del _s126_lib, horas 3-9)
mir, _ = cargar_mirova(("2026-01-01", "2026-12-31"))
por_vol = defaultdict(list)


def ratio_noche_2026(pred_crater, por_vol_out=None):
    out = []
    for v in VENTS:
        if v not in recs:
            continue
        mejor = {}
        for r in recs[v]:
            if not noct(r) or not v375(r) or not r["datetime_utc"].startswith("2026"):
                continue
            val = (r.get("primary_cluster") or {}).get("vrp_mw") or 0
            if val <= 0 or (pred_crater and not crater(r, v)):
                continue
            k = (r["datetime_utc"][:10], "v375")
            mejor[k] = max(mejor.get(k, 0), val)
        for k, val in mejor.items():
            m = (mir.get(v) or {}).get(k)
            if m and m > 0:
                out.append(val / m)
                if por_vol_out is not None:
                    por_vol_out[v].append(val / m)
    return out


pv26 = defaultdict(list)
print("A 2026 noche-max, cualquier pc>0 (replica libro, esperado 0,689):", med(ratio_noche_2026(False, pv26)))
print("B 2026 noche-max, predicado crater:", med(ratio_noche_2026(True)))

# ---------- 2026 por pasada contra CONS ALERTA (±120 s)
cons = defaultdict(list)
for row in csv.DictReader(open(R / "latest_consolidado.csv", encoding="utf-8", errors="replace")):
    vol = normalize_volcano_name(row.get("Volcan"))
    if vol is None or normalize_sensor(row.get("Sensor")) != "VIIRS375" or row.get("Tipo_Registro") != "ALERTA_TERMICA":
        continue
    t = datetime.strptime(row["Fecha_Satelite_UTC"][:19], "%Y-%m-%d %H:%M:%S")
    if t.hour > 11:
        continue
    cons[vol].append((t, float(row["VRP_MW"])))
for v in cons:
    cons[v].sort()
C1, C2 = [], []
for v in INNER:
    L = cons.get(v, [])
    ts = [x[0] for x in L]
    for r in recs[v]:
        if not noct(r) or not v375(r):
            continue
        t = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M")
        i = bisect.bisect_left(ts, t - timedelta(seconds=120))
        if i < len(L) and L[i][0] <= t + timedelta(seconds=120) and L[i][1] > 0:
            val = (r.get("primary_cluster") or {}).get("vrp_mw") or 0
            if val > 0:
                C1.append(val / L[i][1])
                if crater(r, v):
                    C2.append(val / L[i][1])
print("C 2026 por pasada vs CONS ALERTA, cualquier pc>0:", med(C1))
print("D 2026 por pasada vs CONS ALERTA, predicado crater:", med(C2))

# ---------- 2025 OSF
osf = pd.read_csv(R / 'data/mirova_reference/VRP_GLOBAL_ARCHIVE_2025.csv')
osf['t'] = pd.to_datetime(osf.timeUTC, format='%d/%m/%Y %H:%M', errors='coerce')
T0, T1 = datetime(2025, 2, 15), datetime(2025, 12, 1)
o = osf[osf.Volc_Name.isin(MAP) & (osf.t >= T0) & (osf.t < T1) & (osf.Dayflag == 0) & (osf.Resolution.astype(int) == 375) & (osf['class'] == 1)].copy()
o['vol'] = o.Volc_Name.map(MAP)
idx = defaultdict(list)
for _, x in o.iterrows():
    idx[x.vol].append((x.t.to_pydatetime(), x.VRP / 1e6))
for v in idx:
    idx[v].sort()
E1, E2 = [], []
pv25 = defaultdict(list)
for v in INNER:
    L = idx.get(v, [])
    ts = [x[0] for x in L]
    for r in recs[v]:
        t = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M")
        if not (T0 <= t < T1) or not v375(r):
            continue
        i = bisect.bisect_left(ts, t - timedelta(minutes=10))
        best = None
        while i < len(L) and L[i][0] <= t + timedelta(minutes=10):
            best = L[i] if best is None or abs((L[i][0] - t).total_seconds()) < abs((best[0] - t).total_seconds()) else best
            i += 1
        if best is None or best[1] <= 0:
            continue
        val = (r.get("primary_cluster") or {}).get("vrp_mw") or 0
        if val > 0:
            E1.append(val / best[1])
            if crater(r, v):
                E2.append(val / best[1])
print("E 2025 OSF por pasada, cualquier pc>0:", med(E1))
print("F 2025 OSF por pasada, predicado crater (eje 6 declara 0,551):", med(E2))
# noche-max 2025 (metodo del libro sobre OSF; horas 3-9 del lado MIROVA como _s126_lib)
mo = defaultdict(float)
for v, L in idx.items():
    for t, val in L:
        if 3 <= t.hour <= 9:
            k = (v, t.strftime("%Y-%m-%d"))
            mo[k] = max(mo[k], val)
G = []
for v in INNER:
    mejor = {}
    for r in recs[v]:
        t = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M")
        if not (T0 <= t < T1) or not v375(r) or not noct(r):
            continue
        val = (r.get("primary_cluster") or {}).get("vrp_mw") or 0
        if val > 0:
            k = (v, t.strftime("%Y-%m-%d"))
            mejor[k] = max(mejor.get(k, 0), val)
    for k, val in mejor.items():
        if mo.get(k, 0) > 0:
            G.append(val / mo[k])
            pv25[v].append(val / mo[k])
print("G 2025 OSF noche-max (metodo del libro), cualquier pc>0:", med(G))

print("\n== por volcan, metodo del libro: 2026 (latest.php) vs 2025 (OSF)")
for v in INNER:
    print(f"  {v:22s} 2026 {med(pv26[v])}  2025 {med(pv25[v])}")
print("mediana de medianas por volcan 2026:", round(st.median([st.median(x) for x in pv26.values() if x]), 3),
      "| 2025:", round(st.median([st.median(x) for x in pv25.values() if x]), 3))
