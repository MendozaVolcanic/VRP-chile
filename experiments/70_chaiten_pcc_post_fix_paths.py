"""S32 P2 Driver B post-A/B — Chaiten 14.5× y PCC 11.9× post-fix.

Driver B redujo Lastarria 18.5→6.5×, Villarrica 64.9→2.2×, Planchón 16→2.5×.
Pero Chaiten solo bajó 18.3→14.5× (-21%) y PCC 12.1→11.9× (-2%).

Hipótesis: Test 1 NO es el path dominante en Chaiten/PCC. Otro path
(BT clásico, dNTI, etc.) está aportando los pixels marginales que inflan
el cluster.

Análisis: para records con ratio alto post-fix, identificar:
- triggered_test1?
- final_hotspot_source (qué path ganó la cascada)?
- Si NO es test1 → confirmamos Test 1 no es el problema.
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
ON  = ROOT / "data" / "mirova_equivalent_test1pix_filter"

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
df = df[df['Tipo_Registro']=='ALERTA_TERMICA']

print(f"# Chaiten + PCC post-fix Driver B — qué path domina los altos ratios\n")

for VOLC, csv_name in [('Chaiten','Chaiten'), ('PuyehueCordonCaulle','Puyehue-Cordon Caulle')]:
    print(f"\n## {VOLC}\n")
    subdf = df[df['Volcan']==csv_name]
    out = []
    for r in json.loads((ON/f'{VOLC}.json').read_text(encoding='utf-8')).get('records', []):
        try: dt = parse_rec_dt(r['datetime_utc'])
        except: continue
        if START_DT <= dt <= END_DT:
            r['_dt'] = dt; out.append(r)

    def find_match(ref_dt, ref_sensor, recs):
        tol = timedelta(minutes=TOL_MIN)
        best, bd = None, tol + timedelta(seconds=1)
        for r in recs:
            if not sensor_match(ref_sensor, r.get('sensor','')): continue
            d = abs(r['_dt']-ref_dt)
            if d <= tol and d < bd: best, bd = r, d
        return best

    rows = []
    path_count_test1 = defaultdict(int)
    for _, row in subdf.iterrows():
        rec = find_match(row['dt'], row['Sensor'], out)
        if rec is None: continue
        v = vrp_summit(rec)
        if v <= 0: continue
        ratio = v / row['VRP_MW']
        rows.append({
            'dt': row['dt'], 'sensor': row['Sensor'], 'mirova_mw': row['VRP_MW'],
            'our_mw': v, 'ratio': ratio,
            'triggered_test1': bool(rec.get('triggered_test1')),
            'final_source': rec.get('final_hotspot_source'),
            'pc_n': (rec.get('primary_cluster') or {}).get('n_pixels'),
            'n_t1_pix': rec.get('n_test1_pixels', 0),
            'n_bt_path': rec.get('n_bt_path', 0),
            'n_dnti_ctx': rec.get('n_dnti_ctx_path', 0),
            'n_anomalous': rec.get('n_anomalous_pixels', 0),
        })
    if not rows:
        print("(sin TPs summit-only)"); continue

    rows.sort(key=lambda x: -x['ratio'])
    print(f"### Top 10 peores ratios post-fix ({len(rows)} TPs total)\n")
    print("| Fecha | Sensor | MIROVA MW | Nuestro MW | Ratio | T1? | path_source | pc_n | n_t1pix | n_bt | n_dnti | n_anom |")
    print("|---|---|---:|---:|---:|:--:|---|---:|---:|---:|---:|---:|")
    for r in rows[:10]:
        print(f"| {r['dt'].strftime('%Y-%m-%d %H:%M')} | {r['sensor']} | {r['mirova_mw']:.3f} | "
              f"{r['our_mw']:.2f} | {r['ratio']:.1f} | {'Y' if r['triggered_test1'] else 'N'} | "
              f"{r['final_source']} | {r['pc_n']} | {r['n_t1_pix']} | {r['n_bt_path']} | "
              f"{r['n_dnti_ctx']} | {r['n_anomalous']} |")

    # Distribución path source
    sources = defaultdict(int)
    test1_in_top10 = 0
    test1_in_all = 0
    for r in rows:
        sources[r['final_source'] or 'None'] += 1
        if r['triggered_test1']: test1_in_all += 1
    for r in rows[:10]:
        if r['triggered_test1']: test1_in_top10 += 1
    print(f"\n**Distribución path_source en TPs ({len(rows)} total):**")
    for k, n in sorted(sources.items(), key=lambda x:-x[1]):
        print(f"  - {k}: {n} ({n/len(rows)*100:.0f}%)")
    print(f"\n**triggered_test1 en TOP 10 peor ratio**: {test1_in_top10}/10")
    print(f"**triggered_test1 en TODOS los TPs**: {test1_in_all}/{len(rows)} ({test1_in_all/len(rows)*100:.0f}%)")

    # Mediana n_bt_path en records con ratio alto
    high_ratio = [r for r in rows if r['ratio'] >= 5]
    low_ratio  = [r for r in rows if r['ratio'] < 5]
    if high_ratio:
        nbt_high = sorted(r['n_bt_path'] for r in high_ratio)[len(high_ratio)//2]
        ndnti_high = sorted(r['n_dnti_ctx'] for r in high_ratio)[len(high_ratio)//2]
        nt1_high = sorted(r['n_t1_pix'] for r in high_ratio)[len(high_ratio)//2]
        print(f"\n**Records ratio>=5x ({len(high_ratio)})**: mediana n_bt={nbt_high}, n_dnti={ndnti_high}, n_t1={nt1_high}")
    if low_ratio:
        nbt_low = sorted(r['n_bt_path'] for r in low_ratio)[len(low_ratio)//2]
        ndnti_low = sorted(r['n_dnti_ctx'] for r in low_ratio)[len(low_ratio)//2]
        nt1_low = sorted(r['n_t1_pix'] for r in low_ratio)[len(low_ratio)//2]
        print(f"**Records ratio<5x ({len(low_ratio)})**: mediana n_bt={nbt_low}, n_dnti={ndnti_low}, n_t1={nt1_low}")

print("\n\n## Veredicto\n")
print("Si triggered_test1 alto (>80%) + ratio sigue alto → Test 1 SÍ es path pero filtro 5σ insuficiente.")
print("Si triggered_test1 bajo (<50%) + ratio alto → otro path domina, extender filter a path BT/dNTI.")
print("Si n_bt_path o n_dnti_ctx altos en records ratio>5 → ese es el path no-filtrado dominante.")
