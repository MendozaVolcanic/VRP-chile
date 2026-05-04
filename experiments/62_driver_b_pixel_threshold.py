"""S32 P2 Driver B — pixel-level threshold simulation.

Hipótesis (b) BLOQUE_ARRANQUE_S32: MIROVA aplica min_pixel_vrp pixel-por-pixel
sobre el cluster (no solo umbral de detección/Test1). Default ~0.05 MW por pixel.

Test: para cada record summit pareado con MIROVA, simular qué pasaría con
distintos pisos pixel-level. Calcular ratio resultante.

Pixels del primary_cluster se identifican por proximidad al centroid del
cluster (haversine < threshold). Aproximación; lo correcto sería re-clustering.
"""
from __future__ import annotations
import json, sys, io, math
from datetime import datetime, timedelta, timezone
from pathlib import Path
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

# Threshold para asociar anomaly_pixel a primary_cluster (radio km del centroid)
CLUSTER_RADIUS_KM = {
    'MODIS': 3.0,    # 1km × 3 vecinos
    'VIIRS750': 2.0,  # 750m × 2.5 vecinos
    'VIIRS375': 1.0,  # 375m × 2.5 vecinos
}

PIXEL_THRESHOLDS_MW = [0.01, 0.05, 0.10, 0.20, 0.50]


def parse_csv_dt(s):
    return datetime.strptime(s.strip(), "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)

def parse_rec_dt(s):
    s = s.strip().replace("Z","+00:00")
    for fmt in ("%Y-%m-%d %H:%M:%S","%Y-%m-%d %H:%M","%Y-%m-%dT%H:%M:%S","%Y-%m-%dT%H:%M"):
        try:
            return datetime.strptime(s.split("+")[0], fmt).replace(tzinfo=timezone.utc)
        except ValueError: continue
    return datetime.fromisoformat(s)

def sensor_match(ref_s, rec_s):
    if ref_s == "MODIS": return rec_s.startswith("MODIS")
    if ref_s == "VIIRS": return rec_s.startswith("VIIRS_") and rec_s.endswith("_750")
    if ref_s == "VIIRS375": return rec_s.startswith("VIIRS_") and not rec_s.endswith("_750")
    return False

def sensor_bucket(rec_s):
    if rec_s.startswith("MODIS"): return "MODIS"
    if rec_s.endswith("_750"): return "VIIRS750"
    if rec_s.startswith("VIIRS_"): return "VIIRS375"
    return "?"

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2-lat1); dlon = math.radians(lon2-lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlon/2)**2
    return 2*R*math.asin(math.sqrt(a))


# Load CSV — solo ALERTA_TERMICA
df = pd.read_csv(CSV)
df['dt'] = df['Fecha_Satelite_UTC'].apply(parse_csv_dt)
df = df[(df['dt'] >= START_DT) & (df['dt'] <= END_DT)]
df = df[df['Volcan'].isin(VOLC_MAP.keys())]
df = df[df['Tipo_Registro'] == 'ALERTA_TERMICA']
df = df[df['VRP_MW'] > 0]

# Load records
all_records = {}
for csv_v, our_v in VOLC_MAP.items():
    f = DATA / f"{our_v}.json"
    if not f.exists(): all_records[our_v] = []; continue
    d = json.loads(f.read_text(encoding='utf-8'))
    out = []
    for r in d.get('records', []):
        try: dt = parse_rec_dt(r['datetime_utc'])
        except (ValueError, KeyError): continue
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


# Pareo summit-only con cluster válido y anomaly_pixels disponibles
samples = []
for _, row in df.iterrows():
    csv_v = row['Volcan']; our_v = VOLC_MAP[csv_v]
    rec = find_match(row['dt'], row['Sensor'], all_records[our_v])
    if rec is None: continue
    if rec.get('distance_class') != 'summit': continue
    pc = rec.get('primary_cluster') or {}
    pc_vrp = pc.get('vrp_mw', 0)
    if pc_vrp <= 0: continue
    aps = rec.get('anomaly_pixels') or []
    if not aps: continue
    sb = sensor_bucket(rec.get('sensor',''))
    cluster_radius = CLUSTER_RADIUS_KM.get(sb, 1.5)
    cent_lat = pc.get('centroid_lat'); cent_lon = pc.get('centroid_lon')
    if cent_lat is None or cent_lon is None: continue
    # Pixels del cluster: cercanos al centroid
    cluster_pixels = []
    for p in aps:
        d_km = haversine_km(cent_lat, cent_lon, p['lat'], p['lon'])
        if d_km <= cluster_radius:
            cluster_pixels.append(p)
    if not cluster_pixels: continue
    # Recompute pc_vrp via pixels (sanity check vs reported)
    pc_vrp_recomp = sum(p.get('vrp_mw', 0) for p in cluster_pixels)
    samples.append({
        'volcan': our_v,
        'sensor': sb,
        'dt': row['dt'],
        'mirova_vrp': float(row['VRP_MW']),
        'pc_vrp_reported': pc_vrp,
        'pc_vrp_recomp': pc_vrp_recomp,
        'pc_n': pc.get('n_pixels'),
        'cluster_pixels': cluster_pixels,
    })

print(f"# Driver B — pixel threshold simulation\n")
print(f"Samples summit con cluster + pixels: {len(samples)}\n")

# Sanity: comparación pc_vrp reported vs recomp
diffs = [abs(s['pc_vrp_reported']-s['pc_vrp_recomp'])/max(0.01,s['pc_vrp_reported']) for s in samples]
print(f"Sanity check pc_vrp reportado vs recomputado por pixels:")
print(f"  diff% mediano: {sorted(diffs)[len(diffs)//2]*100:.1f}%")
print(f"  diff% max: {max(diffs)*100:.1f}%")
print()

# Distribución pixels intra-cluster (Lastarria solo, top 5 ratios)
print("## Distribución de pixels intra-cluster (Lastarria, top 5 peores ratios)\n")
last = [s for s in samples if s['volcan']=='Lastarria']
last.sort(key=lambda s: s['pc_vrp_recomp']/max(0.001,s['mirova_vrp']), reverse=True)
for i, s in enumerate(last[:5]):
    vrps = sorted([p.get('vrp_mw',0) for p in s['cluster_pixels']], reverse=True)
    ratio = s['pc_vrp_recomp']/max(0.001,s['mirova_vrp'])
    print(f"### Lastarria {s['sensor']} {s['dt'].strftime('%Y-%m-%d %H:%M')} — MIROVA {s['mirova_vrp']:.3f} MW vs nuestro {s['pc_vrp_recomp']:.2f} MW (ratio {ratio:.0f}x)")
    print(f"  cluster: {len(vrps)} pixels, suma={sum(vrps):.2f} MW")
    print(f"  top 5 vrp pixel: {[f'{v:.3f}' for v in vrps[:5]]}")
    print(f"  bottom 5 vrp pixel: {[f'{v:.4f}' for v in vrps[-5:]]}")
    print(f"  pixels >0.5 MW: {sum(1 for v in vrps if v>0.5)}, "
          f">0.1 MW: {sum(1 for v in vrps if v>0.1)}, "
          f">0.05 MW: {sum(1 for v in vrps if v>0.05)}, "
          f">0.01 MW: {sum(1 for v in vrps if v>0.01)}")

# Simulación pisos pixel-level: nuevo ratio mediano global
print("\n## Ratio mediano global vs piso pixel-level\n")
print("| Piso pixel MW | Mediana ratio nuestro/MIROVA | n_samples utiles | n_pixels promedio en cluster |")
print("|---:|---:|---:|---:|")
for thr in [0.0] + PIXEL_THRESHOLDS_MW:
    ratios = []
    npix = []
    for s in samples:
        filt = [p for p in s['cluster_pixels'] if p.get('vrp_mw',0) >= thr]
        new_pc_vrp = sum(p.get('vrp_mw',0) for p in filt)
        if new_pc_vrp <= 0: continue
        ratios.append(new_pc_vrp / s['mirova_vrp'])
        npix.append(len(filt))
    if not ratios:
        print(f"| ≥{thr:.2f} | (todos filtrados) | 0 | 0 |"); continue
    med = sorted(ratios)[len(ratios)//2]
    avg_npix = sum(npix)/len(npix)
    print(f"| ≥{thr:.2f} | {med:.2f}x | {len(ratios)} | {avg_npix:.1f} |")

# Por volcán con piso 0.05
print("\n## Por volcán con piso pixel ≥ 0.05 MW (hipótesis MIROVA default)\n")
print("| Volcán | n | mediana ratio | mediana MIROVA | mediana nuestro filt |")
print("|---|---:|---:|---:|---:|")
import collections
buckets = collections.defaultdict(list)
for s in samples:
    filt = [p for p in s['cluster_pixels'] if p.get('vrp_mw',0) >= 0.05]
    new_vrp = sum(p.get('vrp_mw',0) for p in filt)
    if new_vrp <= 0: continue
    buckets[s['volcan']].append((s['mirova_vrp'], new_vrp, new_vrp/s['mirova_vrp']))
for v, items in sorted(buckets.items()):
    items.sort()
    n = len(items)
    med_ratio = sorted(r for _,_,r in items)[n//2]
    med_mirova = sorted(m for m,_,_ in items)[n//2]
    med_ours = sorted(o for _,o,_ in items)[n//2]
    print(f"| {v} | {n} | {med_ratio:.2f} | {med_mirova:.3f} | {med_ours:.3f} |")
