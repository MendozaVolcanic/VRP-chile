"""S32 Driver B Fase 1b — ¿qué función de agregación usa MIROVA NRT?

Hipótesis revisada: MIROVA NRT no reporta sum(per_pixel_vrp) del cluster
sino algo más restrictivo. Tests:
- max(pixel_vrp): VRP del pixel más caliente
- top1, top3 sum, top5 sum
- sum solo pixels >0.05 / >0.1 / >0.2 MW

Para cada función, calcular ratio mediano global vs MIROVA. La que más se
acerque a 1.0× es candidata fuerte para mecanismo MIROVA.
"""
from __future__ import annotations
import json, sys, io, math
from datetime import datetime, timedelta, timezone
from pathlib import Path
from collections import defaultdict
import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT = Path("C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile")
CSV = ROOT / "01_05_2026_registro_vrp_consolidado.csv"
DATA = ROOT / "data" / "mirova_equivalent"

VOLC_MAP = {
    'Lascar':'Lascar','Lastarria':'Lastarria','Tupungatito':'Tupungatito',
    'Villarrica':'Villarrica','Puyehue-Cordon Caulle':'PuyehueCordonCaulle',
    'Copahue':'Copahue','Nevados de Chillan':'NevadosDeChillan',
    'Llaima':'Llaima','Chaiten':'Chaiten','PlanchonPeteroa':'PlanchonPeteroa',
    'Isluga':'Isluga'
}
END_DT = datetime(2026,5,1,23,59,tzinfo=timezone.utc)
START_DT = END_DT - timedelta(days=90)
TOL_MIN = 60
CLUSTER_RADIUS_KM = {'MODIS': 5.0, 'VIIRS750': 4.0, 'VIIRS375': 3.0}


def parse_csv_dt(s):
    return datetime.strptime(s.strip(), "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
def parse_rec_dt(s):
    s = s.strip().replace("Z","+00:00")
    for fmt in ("%Y-%m-%d %H:%M:%S","%Y-%m-%d %H:%M"):
        try: return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
        except: continue
    return datetime.fromisoformat(s)
def sensor_match(ref, rec):
    if ref == "MODIS": return rec.startswith("MODIS")
    if ref == "VIIRS": return rec.startswith("VIIRS_") and rec.endswith("_750")
    if ref == "VIIRS375": return rec.startswith("VIIRS_") and not rec.endswith("_750")
    return False
def sensor_bucket(rec):
    if rec.startswith("MODIS"): return "MODIS"
    if rec.endswith("_750"): return "VIIRS750"
    if rec.startswith("VIIRS_"): return "VIIRS375"
    return "?"
def hav_km(la1,lo1,la2,lo2):
    R=6371.0
    dla=math.radians(la2-la1); dlo=math.radians(lo2-lo1)
    a=math.sin(dla/2)**2+math.cos(math.radians(la1))*math.cos(math.radians(la2))*math.sin(dlo/2)**2
    return 2*R*math.asin(math.sqrt(a))


df = pd.read_csv(CSV)
df['dt'] = df['Fecha_Satelite_UTC'].apply(parse_csv_dt)
df = df[(df['dt'] >= START_DT) & (df['dt'] <= END_DT)]
df = df[df['Volcan'].isin(VOLC_MAP.keys())]
df = df[df['Tipo_Registro'] == 'ALERTA_TERMICA']
df = df[df['VRP_MW'] > 0]

all_records = {}
for csv_v, our_v in VOLC_MAP.items():
    f = DATA / f"{our_v}.json"
    if not f.exists(): all_records[our_v] = []; continue
    out = []
    for r in json.loads(f.read_text(encoding='utf-8')).get('records', []):
        try: dt = parse_rec_dt(r['datetime_utc'])
        except: continue
        if START_DT <= dt <= END_DT:
            r['_dt'] = dt; out.append(r)
    all_records[our_v] = out

def find_match(ref_dt, ref_sensor, recs):
    tol = timedelta(minutes=TOL_MIN)
    best, bd = None, tol + timedelta(seconds=1)
    for r in recs:
        if not sensor_match(ref_sensor, r.get('sensor','')): continue
        delta = abs(r['_dt'] - ref_dt)
        if delta <= tol and delta < bd: best, bd = r, delta
    return best

samples = []
for _, row in df.iterrows():
    csv_v = row['Volcan']; our_v = VOLC_MAP[csv_v]
    rec = find_match(row['dt'], row['Sensor'], all_records[our_v])
    if rec is None or rec.get('distance_class') != 'summit': continue
    pc = rec.get('primary_cluster') or {}
    pc_vrp = pc.get('vrp_mw', 0)
    if pc_vrp <= 0: continue
    aps = rec.get('anomaly_pixels') or []
    if not aps: continue
    sb = sensor_bucket(rec.get('sensor',''))
    cluster_r = CLUSTER_RADIUS_KM.get(sb, 3.0)
    cent_lat, cent_lon = pc.get('centroid_lat'), pc.get('centroid_lon')
    if cent_lat is None or cent_lon is None: continue
    cluster_aps = sorted(
        [p for p in aps if hav_km(cent_lat, cent_lon, p['lat'], p['lon']) <= cluster_r and p.get('vrp_mw',0)>0],
        key=lambda p: p.get('vrp_mw', 0), reverse=True
    )
    if not cluster_aps: continue
    samples.append({
        'volcan': our_v, 'sensor': sb,
        'mirova_vrp': float(row['VRP_MW']),
        'pc_vrp_reported': pc_vrp,
        'pixels_vrp_sorted': [p.get('vrp_mw',0) for p in cluster_aps],
    })

print(f"# Driver B Fase 1b — agregación VRP\n")
print(f"Samples: {len(samples)}\n")

# Definir las funciones candidatas
def f_sum(vrps): return sum(vrps)
def f_max(vrps): return vrps[0] if vrps else 0
def f_top3(vrps): return sum(vrps[:3])
def f_top5(vrps): return sum(vrps[:5])
def f_top1plushalftop2(vrps):
    if len(vrps)==0: return 0
    if len(vrps)==1: return vrps[0]
    return vrps[0] + 0.5*vrps[1]
def f_thresh(vrps, thr): return sum(v for v in vrps if v >= thr)
def f_max_with_floor(vrps, thr): return max((v for v in vrps if v>=thr), default=0)

candidates = [
    ('pipeline_reported', None, lambda s: s['pc_vrp_reported']),
    ('sum_all', None, lambda s: f_sum(s['pixels_vrp_sorted'])),
    ('max_only', None, lambda s: f_max(s['pixels_vrp_sorted'])),
    ('top3_sum', None, lambda s: f_top3(s['pixels_vrp_sorted'])),
    ('top5_sum', None, lambda s: f_top5(s['pixels_vrp_sorted'])),
    ('sum_>=0.05', None, lambda s: f_thresh(s['pixels_vrp_sorted'], 0.05)),
    ('sum_>=0.10', None, lambda s: f_thresh(s['pixels_vrp_sorted'], 0.10)),
    ('sum_>=0.20', None, lambda s: f_thresh(s['pixels_vrp_sorted'], 0.20)),
    ('sum_>=0.50', None, lambda s: f_thresh(s['pixels_vrp_sorted'], 0.50)),
    ('top1_plus_half_top2', None, lambda s: f_top1plushalftop2(s['pixels_vrp_sorted'])),
]

print("## Ratio mediano global por función de agregación\n")
print("| Función | n_validos | mediana ratio | percentil 25 | percentil 75 | mediana nuestro MW | mediana MIROVA MW |")
print("|---|---:|---:|---:|---:|---:|---:|")
for name, _, fn in candidates:
    rows = []
    for s in samples:
        v = fn(s)
        if v <= 0: continue
        rows.append((v, s['mirova_vrp'], v/s['mirova_vrp']))
    rows.sort(key=lambda x: x[2])
    if not rows: print(f"| {name} | 0 | - | - | - | - | - |"); continue
    n = len(rows)
    p25 = rows[n//4][2]; p50 = rows[n//2][2]; p75 = rows[(3*n)//4][2]
    med_o = sorted(r[0] for r in rows)[n//2]
    med_m = sorted(r[1] for r in rows)[n//2]
    print(f"| {name} | {n} | {p50:.2f} | {p25:.2f} | {p75:.2f} | {med_o:.3f} | {med_m:.3f} |")

# Mejor ajuste por volcán para max_only
print("\n## Función max(pixel) por volcán (la más restrictiva)\n")
print("| Volcán | n | mediana ratio | mediana max_pixel MW | mediana MIROVA MW |")
print("|---|---:|---:|---:|---:|")
buckets = defaultdict(list)
for s in samples:
    v = f_max(s['pixels_vrp_sorted'])
    if v > 0: buckets[s['volcan']].append((v, s['mirova_vrp'], v/s['mirova_vrp']))
for v, items in sorted(buckets.items()):
    items.sort(key=lambda x: x[2])
    n = len(items)
    med_r = items[n//2][2]
    med_o = sorted(x[0] for x in items)[n//2]
    med_m = sorted(x[1] for x in items)[n//2]
    print(f"| {v} | {n} | {med_r:.2f} | {med_o:.3f} | {med_m:.3f} |")
