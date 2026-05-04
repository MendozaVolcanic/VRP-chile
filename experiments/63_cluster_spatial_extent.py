"""S32 Driver B Fase 1a — extensión espacial intra-cluster.

Sin bajar granules: medir cuán geográficamente extenso es el cluster nuestro
para records summit con MIROVA paired. Si el cluster nuestro tiene radio
efectivo >2-3 km y MIROVA reporta hotspot compacto, confirma hipótesis
"8-conn sin acotar".

Métricas:
- max_pixel_dist_km: distancia max pixel-pixel dentro del cluster
- centroid_radius_km: max distancia pixel→centroid del cluster
- pc_n vs len(cluster_pixels_in_array): cobertura del array exportado

Caveat: anomaly_pixels JSON tiene cap top-100 (gap 60% mediano vs pc_vrp
reportado). Mide solo lo exportado.
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

# Pixel size en km por sensor
PIXEL_KM = {'MODIS': 1.0, 'VIIRS750': 0.75, 'VIIRS375': 0.375}

# Cluster radius para asociar anomaly_pixels al primary_cluster
CLUSTER_RADIUS_KM = {'MODIS': 5.0, 'VIIRS750': 4.0, 'VIIRS375': 3.0}


def parse_csv_dt(s):
    return datetime.strptime(s.strip(), "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)

def parse_rec_dt(s):
    s = s.strip().replace("Z","+00:00")
    for fmt in ("%Y-%m-%d %H:%M:%S","%Y-%m-%d %H:%M"):
        try: return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
        except: continue
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

def hav_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2-lat1); dlon = math.radians(lon2-lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlon/2)**2
    return 2*R*math.asin(math.sqrt(a))


# Cargar refs MIROVA
df = pd.read_csv(CSV)
df['dt'] = df['Fecha_Satelite_UTC'].apply(parse_csv_dt)
df = df[(df['dt'] >= START_DT) & (df['dt'] <= END_DT)]
df = df[df['Volcan'].isin(VOLC_MAP.keys())]
df = df[df['Tipo_Registro'] == 'ALERTA_TERMICA']
df = df[df['VRP_MW'] > 0]

# Cargar records
all_records = {}
for csv_v, our_v in VOLC_MAP.items():
    f = DATA / f"{our_v}.json"
    if not f.exists(): all_records[our_v] = []; continue
    d = json.loads(f.read_text(encoding='utf-8'))
    out = []
    for r in d.get('records', []):
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


# Acumular extensión por sample
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
    # Pixels asociados al cluster (anomaly_pixels dentro del radio)
    cluster_aps = [p for p in aps if hav_km(cent_lat, cent_lon, p['lat'], p['lon']) <= cluster_r]
    if len(cluster_aps) < 2: continue
    # Métricas extensión
    max_pix_pix = 0
    radii = []
    for i, p in enumerate(cluster_aps):
        radii.append(hav_km(cent_lat, cent_lon, p['lat'], p['lon']))
        for q in cluster_aps[i+1:]:
            d = hav_km(p['lat'], p['lon'], q['lat'], q['lon'])
            if d > max_pix_pix: max_pix_pix = d
    samples.append({
        'volcan': our_v, 'sensor': sb,
        'mirova_vrp': float(row['VRP_MW']),
        'pc_vrp_reported': pc_vrp,
        'pc_n_reported': pc.get('n_pixels'),
        'n_pixels_in_array': len(cluster_aps),
        'max_pixel_pixel_km': max_pix_pix,
        'centroid_radius_km': max(radii),
        'pixel_size_km': PIXEL_KM.get(sb, 1.0),
    })

print(f"# Driver B Fase 1a — extensión espacial intra-cluster\n")
print(f"Samples summit pareados: {len(samples)}\n")

# Resumen por volcán + sensor
print("## Extensión geográfica del cluster (mediana por volcán × sensor)\n")
print("| Volcán | Sensor | n | pix_km | pc_n_pipe | n_in_array | max_pix-pix km | centroid_radius km | extension/pix_size |")
print("|---|---|---:|---:|---:|---:|---:|---:|---:|")
buckets = defaultdict(list)
for s in samples:
    buckets[(s['volcan'], s['sensor'])].append(s)
for (v, sb), items in sorted(buckets.items()):
    n = len(items)
    if n == 0: continue
    items_sorted = sorted(items, key=lambda x: x['max_pixel_pixel_km'])
    med = items_sorted[n//2]
    pc_n_med = sorted(s['pc_n_reported'] for s in items)[n//2]
    n_arr_med = sorted(s['n_pixels_in_array'] for s in items)[n//2]
    pix_pix_med = sorted(s['max_pixel_pixel_km'] for s in items)[n//2]
    cent_med = sorted(s['centroid_radius_km'] for s in items)[n//2]
    pix_size = med['pixel_size_km']
    ext_pix = pix_pix_med / pix_size
    print(f"| {v} | {sb} | {n} | {pix_size:.2f} | {pc_n_med} | {n_arr_med} | "
          f"{pix_pix_med:.2f} | {cent_med:.2f} | {ext_pix:.1f} |")

# Análisis del residual: ¿correlaciona ratio con extensión?
print("\n## Correlación ratio nuestro/MIROVA vs extensión cluster\n")
for s in samples: s['ratio'] = s['pc_vrp_reported'] / s['mirova_vrp']
# Bins por extensión
print("| Extensión cluster (km) | n | mediana ratio | mediana MIROVA MW | mediana pc_vrp MW |")
print("|---|---:|---:|---:|---:|")
bins = [(0, 1), (1, 2), (2, 3), (3, 5), (5, 99)]
for lo, hi in bins:
    sub = [s for s in samples if lo <= s['max_pixel_pixel_km'] < hi]
    if not sub: continue
    n = len(sub)
    rs = sorted(s['ratio'] for s in sub); med_r = rs[n//2]
    ms = sorted(s['mirova_vrp'] for s in sub); med_m = ms[n//2]
    ps = sorted(s['pc_vrp_reported'] for s in sub); med_p = ps[n//2]
    print(f"| {lo}–{hi} | {n} | {med_r:.2f}x | {med_m:.3f} | {med_p:.3f} |")

# Cobertura del array (pc_n_reported vs n_in_array): ¿qué % capturamos?
print("\n## Cobertura del array anomaly_pixels (top-100 cap)\n")
covs = []
for s in samples:
    if s['pc_n_reported'] and s['pc_n_reported'] > 0:
        covs.append(s['n_pixels_in_array'] / s['pc_n_reported'])
covs.sort()
if covs:
    print(f"- mediana cobertura n_in_array / pc_n_reported: {covs[len(covs)//2]*100:.0f}%")
    print(f"- min / max: {covs[0]*100:.0f}% / {covs[-1]*100:.0f}%")
    print(f"- samples con cobertura <50%: {sum(1 for c in covs if c<0.5)}/{len(covs)}")
