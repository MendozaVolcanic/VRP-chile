"""S32 P4 — Llaima sobre-detección 347 vs 0 alertas reales MIROVA.

Plan S31+ dice: Llaima 0 detecciones MIROVA NRT en 90d, pero nosotros
347 detecciones. ¿Qué mecanismo MIROVA usa que nosotros no?

Memoria proyecto (`project_llaima_thermal.md`): "139 FPs son ruido térmico
lago Conguillío ~9km NE; historia fisural = sin filtro geométrico". Pero
los números cambiaron a 347 — más drástico aún.

Análisis sin bajar granules:
1. Distribución espacial: ¿pc_dist agrupado en ~9km NE (Conguillío) o en
   el cráter?
2. Distribución temporal: ¿uniforme o concentrada en períodos específicos?
3. distance_class: ¿summit o far en mayoría?
4. Si summit: ¿son detecciones reales del cráter Llaima o cluster del lago
   se mete en summit por inner_radius=5km generoso?
5. CSV MIROVA: ¿qué dice realmente para Llaima 90d?
"""
from __future__ import annotations
import json, sys, io
from datetime import datetime, timedelta, timezone
from pathlib import Path
from collections import defaultdict
import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT = Path("C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile")
CSV = ROOT / "01_05_2026_registro_vrp_consolidado.csv"
DATA = ROOT / "data" / "mirova_equivalent"
END_DT = datetime(2026,4,29,23,59,tzinfo=timezone.utc)
START_DT = END_DT - timedelta(days=90)


def parse_csv_dt(s): return datetime.strptime(s.strip(),"%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
def parse_rec_dt(s):
    s = s.strip().replace("Z","+00:00")
    for fmt in ("%Y-%m-%d %H:%M:%S","%Y-%m-%d %H:%M"):
        try: return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
        except: continue
    return datetime.fromisoformat(s)


# CSV MIROVA Llaima
df = pd.read_csv(CSV)
df['dt'] = df['Fecha_Satelite_UTC'].apply(parse_csv_dt)
df = df[(df['dt'] >= START_DT) & (df['dt'] <= END_DT)]
df_llaima = df[df['Volcan']=='Llaima']
print(f"# P4 Llaima sobre-detección — análisis estadístico\n")
print(f"Window: {START_DT.date()} -> {END_DT.date()}")
print(f"\n## CSV MIROVA Llaima 90d")
print(f"Total records MIROVA Llaima (todos sensores, todos tipos): {len(df_llaima)}")
for tipo in ['ALERTA_TERMICA','RUTINA','FALSO_POSITIVO']:
    n = sum(df_llaima['Tipo_Registro']==tipo)
    print(f"  - {tipo}: {n}")
for sensor in ['MODIS','VIIRS','VIIRS375']:
    n = sum(df_llaima['Sensor']==sensor)
    print(f"  Sensor {sensor}: {n} records")

# Nuestros records Llaima
recs = []
for r in json.loads((DATA/"Llaima.json").read_text(encoding='utf-8')).get('records', []):
    try: dt = parse_rec_dt(r['datetime_utc'])
    except: continue
    if START_DT <= dt <= END_DT:
        r['_dt'] = dt; recs.append(r)
n_total = len(recs)
n_pos = sum(1 for r in recs if (r.get('vrp_mw') or 0)>0)
print(f"\n## Nuestros records Llaima 90d")
print(f"Total records: {n_total}")
print(f"  con vrp_mw>0: {n_pos}")

# Distribución pc_dist
print(f"\n## Distribución espacial de nuestras detecciones (vrp_mw>0)")
buckets = defaultdict(int)
no_pc = 0
for r in recs:
    if (r.get('vrp_mw') or 0) <= 0: continue
    pc = r.get('primary_cluster')
    if not pc: no_pc += 1; continue
    d = pc.get('centroid_dist_km', None)
    if d is None: continue
    if d <= 2: buckets['0-2 km'] += 1
    elif d <= 5: buckets['2-5 km'] += 1
    elif d <= 10: buckets['5-10 km'] += 1
    elif d <= 15: buckets['10-15 km'] += 1
    elif d <= 20: buckets['15-20 km'] += 1
    else: buckets['>20 km'] += 1
print("| pc_dist bin | n detecciones |")
print("|---|---:|")
for k in ['0-2 km','2-5 km','5-10 km','10-15 km','15-20 km','>20 km']:
    print(f"| {k} | {buckets.get(k,0)} |")
if no_pc: print(f"\n(Records con vrp>0 sin primary_cluster: {no_pc})")

# Distance class
n_summit = sum(1 for r in recs if (r.get('vrp_mw') or 0)>0 and r.get('distance_class')=='summit')
n_far    = sum(1 for r in recs if (r.get('vrp_mw') or 0)>0 and r.get('distance_class')=='far')
n_none   = sum(1 for r in recs if (r.get('vrp_mw') or 0)>0 and r.get('distance_class') not in ['summit','far'])
print(f"\n## Distance class (Llaima inner_radius_km=5)")
print(f"  summit (≤5km): {n_summit}")
print(f"  far (>5km): {n_far}")
print(f"  None/unset: {n_none}")

# Sensor breakdown
print(f"\n## Sensor breakdown (vrp_mw>0)")
sensor_count = defaultdict(int)
for r in recs:
    if (r.get('vrp_mw') or 0)<=0: continue
    s = r.get('sensor','?')
    if s.startswith('MODIS'): sensor_count['MODIS'] += 1
    elif s.endswith('_750'): sensor_count['VIIRS750'] += 1
    elif s.startswith('VIIRS'): sensor_count['VIIRS375'] += 1
    else: sensor_count[s] += 1
for s, n in sorted(sensor_count.items(), key=lambda x:-x[1]):
    print(f"  {s}: {n}")

# Magnitud distribution
print(f"\n## Magnitud (vrp_mw global) distribution detecciones Llaima")
vrps = sorted([(r.get('vrp_mw') or 0) for r in recs if (r.get('vrp_mw') or 0)>0])
if vrps:
    n = len(vrps)
    print(f"  n: {n}")
    print(f"  min: {vrps[0]:.3f} MW | p25: {vrps[n//4]:.2f} | mediana: {vrps[n//2]:.2f} | p75: {vrps[(3*n)//4]:.2f} | max: {vrps[-1]:.2f}")

# Mostrar 10 detecciones random con todos campos relevantes
print(f"\n## Sample 10 detecciones (top vrp)")
recs_pos = [r for r in recs if (r.get('vrp_mw') or 0)>0]
recs_pos.sort(key=lambda r: r['vrp_mw'], reverse=True)
print("| Fecha | Sensor | vrp_mw | pc_n | pc_vrp | pc_dist | dist_class | T1? | n_anom |")
print("|---|---|---:|---:|---:|---:|---|:--:|---:|")
for r in recs_pos[:10]:
    pc = r.get('primary_cluster') or {}
    sens = r.get('sensor','?')
    print(f"| {r['_dt'].strftime('%Y-%m-%d %H:%M')} | {sens} | {r['vrp_mw']:.2f} | "
          f"{pc.get('n_pixels','?')} | {pc.get('vrp_mw','?')} | "
          f"{pc.get('centroid_dist_km','?')} | {r.get('distance_class','?')} | "
          f"{'Y' if r.get('triggered_test1') else 'N'} | {r.get('n_anomalous_pixels',0)} |")

# Veredicto
print(f"\n## Veredicto P4 Llaima\n")
total_pos = n_pos
ratio_summit = n_summit/max(1,total_pos)*100
ratio_far = n_far/max(1,total_pos)*100
print(f"- {total_pos} detecciones nuestras vs 0 ALERTA_TERMICA MIROVA = sobre-detección consistente.")
print(f"- {ratio_summit:.0f}% summit-class ({n_summit}/{total_pos}). Esto pasa filtro Driver A.")
print(f"- {ratio_far:.0f}% far-class. Driver A las suprime en frontend, pero quedan en JSON.")
if buckets.get('5-10 km',0) > total_pos * 0.3:
    print(f"- {buckets.get('5-10 km')} clusters caen en 5-10km — coherente con lago Conguillío 9km NE.")
print(f"- Driver A NO ayuda si las detecciones son summit-class (aunque sean del lago llegando al borde inner).")
print(f"\nHipótesis MIROVA NRT: filtro de persistencia temporal (no detección si record único en 7 días),")
print(f"o filtro de magnitud absoluta (descarta vrp<X MW), o supervisión humana NRT (parcial).")
