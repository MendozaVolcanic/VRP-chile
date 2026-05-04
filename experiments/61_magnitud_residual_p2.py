"""S32 P2 Fase 1 — magnitud residual: candidatos pareados MIROVA vs nuestro.

Síntoma a investigar: ratio nuestro/MIROVA mediano 3.72×, peor en
Lastarria (14.5×), Villarrica (41.5×), Planchón (18.5×).

Output: top peores ratios con MIROVA<0.5 MW (señal real baja, nuestro infla),
desglosando primary_cluster, n_pixels, sensor, paths que dispararon.

NO toca pipeline. Solo lectura.
"""
from __future__ import annotations
import json, sys, io
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


def parse_csv_dt(s):
    return datetime.strptime(s.strip(), "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)

def parse_rec_dt(s):
    s = s.strip().replace("Z","+00:00")
    for fmt in ("%Y-%m-%d %H:%M:%S","%Y-%m-%d %H:%M","%Y-%m-%dT%H:%M:%S","%Y-%m-%dT%H:%M"):
        try:
            return datetime.strptime(s.split("+")[0], fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
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

# Load CSV → solo ALERTA_TERMICA (MIROVA detectó algo)
df = pd.read_csv(CSV)
df['dt'] = df['Fecha_Satelite_UTC'].apply(parse_csv_dt)
df = df[(df['dt'] >= START_DT) & (df['dt'] <= END_DT)]
df = df[df['Volcan'].isin(VOLC_MAP.keys())]
df = df[df['Tipo_Registro'] == 'ALERTA_TERMICA'].copy()
df = df[df['VRP_MW'] > 0].copy()  # Excluir VRP=0 (no hay ratio definible)

print(f"# P2 magnitud residual — pareo MIROVA vs nuestro (90d)\n")
print(f"Refs MIROVA ALERTA_TERMICA con VRP>0: {len(df)}\n")

# Load records
all_records = {}
for csv_v, our_v in VOLC_MAP.items():
    f = DATA / f"{our_v}.json"
    if not f.exists():
        all_records[our_v] = []; continue
    d = json.loads(f.read_text(encoding='utf-8'))
    recs = d.get('records', [])
    out = []
    for r in recs:
        try: dt = parse_rec_dt(r['datetime_utc'])
        except (ValueError, KeyError): continue
        if START_DT <= dt <= END_DT:
            r['_dt'] = dt
            out.append(r)
    all_records[our_v] = out

def find_match(ref_dt, ref_sensor, recs, tol_min=TOL_MIN):
    tol = timedelta(minutes=tol_min)
    best, bd = None, tol + timedelta(seconds=1)
    for r in recs:
        if not sensor_match(ref_sensor, r.get('sensor','')): continue
        delta = abs(r['_dt'] - ref_dt)
        if delta <= tol and delta < bd:
            best, bd = r, delta
    return best

# Pareo
matches = []
for _, row in df.iterrows():
    csv_v = row['Volcan']; our_v = VOLC_MAP[csv_v]
    ref_dt = row['dt']; ref_sensor = row['Sensor']
    mirova_vrp = float(row['VRP_MW'])
    rec = find_match(ref_dt, ref_sensor, all_records[our_v])
    if rec is None: continue
    our_vrp = float(rec.get('vrp_mw') or 0)
    if our_vrp <= 0: continue
    ratio = our_vrp / mirova_vrp
    pc = rec.get('primary_cluster') or {}
    matches.append({
        'volcan': our_v,
        'sensor': sensor_bucket(rec.get('sensor','')),
        'dt': ref_dt.strftime('%Y-%m-%d %H:%M'),
        'mirova_vrp': mirova_vrp,
        'our_vrp': our_vrp,
        'ratio': ratio,
        'pc_n': pc.get('n_pixels', 0),
        'pc_vrp': pc.get('vrp_mw', 0),
        'pc_dist': pc.get('centroid_dist_km', None),
        'n_anom_pix': rec.get('n_anomalous_pixels', 0),
        'n_clusters': rec.get('n_hotspots_clustered', 0),
        'test1': bool(rec.get('triggered_test1')),
        'n_test1_pix': rec.get('n_test1_pixels', 0),
        'n_vent_pix': rec.get('n_vent_pixels', 0),
        'dist_class': rec.get('distance_class', '?'),
    })

mdf = pd.DataFrame(matches)
print(f"Pares MIROVA-nuestro encontrados: {len(mdf)}\n")

# Ratios por volcán
print("## Ratio mediano por volcán (todos los TPs con VRP>0 ambos)\n")
print("| Volcán | n | mediana ratio | mean ratio | mediana MIROVA MW | mediana nuestro MW |")
print("|---|---:|---:|---:|---:|---:|")
for v, g in mdf.groupby('volcan'):
    print(f"| {v} | {len(g)} | {g['ratio'].median():.2f} | {g['ratio'].mean():.2f} | "
          f"{g['mirova_vrp'].median():.2f} | {g['our_vrp'].median():.2f} |")
print(f"| **GLOBAL** | {len(mdf)} | **{mdf['ratio'].median():.2f}** | {mdf['ratio'].mean():.2f} | "
      f"{mdf['mirova_vrp'].median():.2f} | {mdf['our_vrp'].median():.2f} |\n")

# Top peores con MIROVA<0.5 MW
print("## Top 15 peores ratios con MIROVA_VRP < 0.5 MW\n")
sub = mdf[mdf['mirova_vrp'] < 0.5].sort_values('ratio', ascending=False).head(15)
print("| Volcán | Sensor | Fecha UTC | MIROVA MW | Nuestro MW | Ratio | pc_n | pc_VRP | pc_dist | n_anom | n_clu | T1 | T1_pix | vent_pix | clase |")
print("|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|:--:|---:|---:|---|")
for _, r in sub.iterrows():
    print(f"| {r['volcan']} | {r['sensor']} | {r['dt']} | {r['mirova_vrp']:.3f} | {r['our_vrp']:.2f} | "
          f"{r['ratio']:.1f}x | {r['pc_n']} | {r['pc_vrp']:.2f} | "
          f"{r['pc_dist'] if r['pc_dist'] is None else f'{r['pc_dist']:.2f}'} | "
          f"{r['n_anom_pix']} | {r['n_clusters']} | {'Y' if r['test1'] else 'N'} | "
          f"{r['n_test1_pix']} | {r['n_vent_pix']} | {r['dist_class']} |")

# Distribución n_pixels y test1 en peores
print("\n## Composición de los 30 peores ratios (cualquier MIROVA)\n")
sub30 = mdf.sort_values('ratio', ascending=False).head(30)
print(f"- Test 1 ON: {sub30['test1'].sum()}/30")
print(f"- pc_n mediana: {sub30['pc_n'].median()}, max: {sub30['pc_n'].max()}")
print(f"- n_anom_pix mediana: {sub30['n_anom_pix'].median()}, max: {sub30['n_anom_pix'].max()}")
print(f"- Sensores: {sub30['sensor'].value_counts().to_dict()}")
print(f"- Volcanes: {sub30['volcan'].value_counts().to_dict()}")

# Comparar 3 métricas de magnitud
print("\n## Comparación 3 métricas: vrp_mw global vs pc_vrp cluster vs pc_vrp summit-only\n")
mdf['ratio_pc'] = mdf['pc_vrp'] / mdf['mirova_vrp']
# pc_vrp solo si summit; si far, magnitud = 0 (MIROVA tampoco reportaría)
mdf['mirova_eq_vrp'] = mdf.apply(
    lambda r: r['pc_vrp'] if r['dist_class'] == 'summit' else 0.0, axis=1
)
mdf['ratio_eq'] = mdf['mirova_eq_vrp'] / mdf['mirova_vrp']

print(f"- vrp_mw GLOBAL              : mediana {mdf['ratio'].median():.2f}x  (n={len(mdf)})")
sub_pc = mdf[mdf['pc_vrp']>0]
print(f"- pc_vrp CLUSTER (any class) : mediana {sub_pc['ratio_pc'].median():.2f}x  (n={len(sub_pc)})")
sub_eq = mdf[mdf['mirova_eq_vrp']>0]
print(f"- pc_vrp SUMMIT-ONLY         : mediana {sub_eq['ratio_eq'].median():.2f}x  (n={len(sub_eq)})")
print(f"  (records donde pareo MIROVA pero nuestro dist_class=far → magnitud=0: "
      f"{(mdf['dist_class']=='far').sum()}/{len(mdf)} = {(mdf['dist_class']=='far').sum()/len(mdf)*100:.1f}%)")

print("\n### Ratio summit-only por volcán\n")
print("| Volcán | n_summit | mediana ratio | mediana MIROVA MW | mediana nuestro pc_vrp summit MW |")
print("|---|---:|---:|---:|---:|")
for v, g in sub_eq.groupby('volcan'):
    print(f"| {v} | {len(g)} | {g['ratio_eq'].median():.2f} | "
          f"{g['mirova_vrp'].median():.2f} | {g['mirova_eq_vrp'].median():.2f} |")
g_all = sub_eq
print(f"| **GLOBAL summit** | {len(g_all)} | **{g_all['ratio_eq'].median():.2f}** | "
      f"{g_all['mirova_vrp'].median():.2f} | {g_all['mirova_eq_vrp'].median():.2f} |")
