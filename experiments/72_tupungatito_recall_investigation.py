"""S33 — Tupungatito 48.5% recall: ¿qué refs MIROVA perdemos y por qué?

Patrón consistente OFF y ON Driver B: Tupungatito recall ~48% (33/68 refs).
35 refs MIROVA NO detectadas summit-only. Causa independiente Driver B.

Hipótesis a evaluar:
H1: Sub-pixel <0.3 MW que ningún path nuestro captura.
H2: Path BT 5σ summit demasiado estricto (std_bg inflado por glaciar 5800m).
H3: dist_class='far' por offset fumarola descentrada (S15 documentado:
    mirova_center 3km SE del vent nominal; inner_radius=7km debería capturar).
H4: Detecciones MIROVA en sensor que NO procesamos (MODIS ya documentado
    poco usado; mayoría VIIRS375).

Análisis sobre data A/B filter_OFF (estable) — Tupungatito.json.
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
DATA = ROOT / "data" / "mirova_equivalent_test1pix_disabled"  # control estable

VOLC = 'Tupungatito'
END_DT = datetime(2026,4,29,23,59,tzinfo=timezone.utc)
START_DT = END_DT - timedelta(days=90)
TOL_MIN = 60


def parse_csv_dt(s): return datetime.strptime(s.strip(),"%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
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
def vrp_summit(rec):
    if not rec: return 0
    pc = rec.get('primary_cluster')
    if not pc: return rec.get('vrp_mw') or 0
    if rec.get('distance_class') and rec.get('distance_class') != 'summit': return 0
    return pc.get('vrp_mw', 0)


df = pd.read_csv(CSV)
df['dt'] = df['Fecha_Satelite_UTC'].apply(parse_csv_dt)
df = df[(df['dt'] >= START_DT) & (df['dt'] <= END_DT)]
df = df[df['Volcan']=='Tupungatito']
df_alerta = df[df['Tipo_Registro']=='ALERTA_TERMICA']

print(f"# Tupungatito recall investigation\n")
print(f"Window: {START_DT.date()} -> {END_DT.date()}")
print(f"Refs MIROVA Tupungatito ALERTA_TERMICA: {len(df_alerta)}")

# Distribución MIROVA: VRP, sensor
print(f"\n## Distribución refs MIROVA Tupungatito\n")
vrps = sorted(df_alerta['VRP_MW'].tolist())
n = len(vrps)
print(f"VRP: min={vrps[0]:.3f}, p25={vrps[n//4]:.3f}, mediana={vrps[n//2]:.3f}, "
      f"p75={vrps[(3*n)//4]:.3f}, max={vrps[-1]:.3f}")
sensores = df_alerta['Sensor'].value_counts().to_dict()
print(f"Sensores: {sensores}")

# Cargar nuestros records
recs = []
for r in json.loads((DATA/f'{VOLC}.json').read_text(encoding='utf-8')).get('records', []):
    try: dt = parse_rec_dt(r['datetime_utc'])
    except: continue
    if START_DT <= dt <= END_DT:
        r['_dt'] = dt; recs.append(r)

def find_match(ref_dt, ref_sensor, recs):
    tol = timedelta(minutes=TOL_MIN)
    best, bd = None, tol + timedelta(seconds=1)
    for r in recs:
        if not sensor_match(ref_sensor, r.get('sensor','')): continue
        d = abs(r['_dt']-ref_dt)
        if d <= tol and d < bd: best, bd = r, d
    return best

# Clasificar refs en TP/FN/FN-no-match
tps, fns_far, fns_zero, fns_no_match = [], [], [], []
for _, row in df_alerta.iterrows():
    rec = find_match(row['dt'], row['Sensor'], recs)
    if rec is None:
        fns_no_match.append(row); continue
    v = vrp_summit(rec)
    if v > 0:
        tps.append((row, rec))
    else:
        # ¿Por qué vrp_summit=0?
        if (rec.get('vrp_mw') or 0) > 0 and rec.get('distance_class') == 'far':
            fns_far.append((row, rec))
        else:
            fns_zero.append((row, rec))

print(f"\n## Categorización refs MIROVA Tupungatito\n")
print(f"- TPs (nosotros detectamos summit): {len(tps)} ({len(tps)/len(df_alerta)*100:.1f}%)")
print(f"- FNs vrp_mw=0 (no detección nuestra): {len(fns_zero)} ({len(fns_zero)/len(df_alerta)*100:.1f}%)")
print(f"- FNs dist_class=far (cluster lejos): {len(fns_far)} ({len(fns_far)/len(df_alerta)*100:.1f}%)")
print(f"- FNs sin match temporal (granule no procesado?): {len(fns_no_match)} ({len(fns_no_match)/len(df_alerta)*100:.1f}%)")

# H1: distribución VRP MIROVA en FNs
print(f"\n### H1: distribución VRP MIROVA en FNs\n")
for label, lst in [('FNs vrp=0', fns_zero), ('FNs far', fns_far)]:
    if not lst: continue
    vs = sorted([row['VRP_MW'] for row, _ in lst])
    print(f"{label} ({len(vs)}): min={vs[0]:.3f}, mediana={vs[len(vs)//2]:.3f}, max={vs[-1]:.3f}")

# H4: distribución sensor en FNs
print(f"\n### H4: distribución sensor en FNs\n")
sensors_fn = defaultdict(int)
for label, lst in [('vrp=0', fns_zero), ('far', fns_far), ('no_match', [(r, None) for r in fns_no_match])]:
    for row, _ in lst:
        sensors_fn[(label, row['Sensor'])] += 1
for k, n in sorted(sensors_fn.items()):
    print(f"  - {k}: {n}")

# H2 + H3: para FNs vrp=0, ver diagnostics del record nuestro
print(f"\n### H2 + H3: diagnostics pipeline en FNs vrp=0 (top 10)\n")
print("| Fecha | Sensor | MIROVA MW | T1? | n_t1pix | t_bg | std_bg | t_max | nti_max | n_anom |")
print("|---|---|---:|:--:|---:|---:|---:|---:|---:|---:|")
for row, rec in fns_zero[:10]:
    sens = rec.get('sensor', '?')
    print(f"| {row['dt'].strftime('%Y-%m-%d %H:%M')} | {sens} | {row['VRP_MW']:.3f} | "
          f"{'Y' if rec.get('triggered_test1') else 'N'} | "
          f"{rec.get('n_test1_pixels','?')} | "
          f"{rec.get('t_bg_k','?')} | "
          f"{rec.get('diag_sigma_bg_k', rec.get('diag_sigma_bg', '?'))} | "
          f"{rec.get('t_max_k','?')} | "
          f"{rec.get('nti_max','?')} | "
          f"{rec.get('n_anomalous_pixels','?')} |")

# H3: FNs far — ¿qué tan lejos cae el cluster?
if fns_far:
    print(f"\n### H3: FNs far — distancia del cluster reportado\n")
    print("| Fecha | Sensor | MIROVA MW | pc_dist_km | pc_n | dist_class |")
    print("|---|---|---:|---:|---:|---|")
    for row, rec in fns_far[:10]:
        pc = rec.get('primary_cluster') or {}
        print(f"| {row['dt'].strftime('%Y-%m-%d %H:%M')} | {rec.get('sensor','?')} | "
              f"{row['VRP_MW']:.3f} | {pc.get('centroid_dist_km','?')} | "
              f"{pc.get('n_pixels','?')} | {rec.get('distance_class','?')} |")

# Veredicto preliminar
print(f"\n## Veredicto preliminar\n")
fn_subpix = sum(1 for row, _ in fns_zero if row['VRP_MW'] < 0.3) if fns_zero else 0
fn_total_zero = len(fns_zero)
if fn_subpix and fn_total_zero:
    print(f"- {fn_subpix}/{fn_total_zero} FNs vrp=0 son MIROVA<0.3 MW (sub-pixel) — H1 probable.")
if fns_far:
    print(f"- {len(fns_far)} FNs far — H3: cluster cae fuera summit pese a inner_radius=7km.")
if fns_no_match:
    print(f"- {len(fns_no_match)} FNs sin match — H4 o granule no descargado/procesado.")
