"""S32 P3 — Lascar 32% FNs MODIS: ¿alineados con MIROVA o pérdida real?

Plan S31+ dijo "límite físico — bg ring 1-3km MODIS solo ~25 pixels". Pero
no se verificó si esos FNs son MIROVA-true (MIROVA tampoco detectó esa
noche) o MIROVA-positive (MIROVA detectó, nosotros perdimos).

Test:
1. Cargar Lascar MODIS records nuestros (90d ventana).
2. Para cada record nuestro vrp_mw=0 (no detección), buscar en CSV MIROVA si
   hay ALERTA_TERMICA MODIS misma noche.
   - Si NO hay → MIROVA tampoco detectó → no es FN, es TN alineado.
   - Si SÍ hay → MIROVA detectó, nosotros perdimos → FN real.
3. Cuantificar: % de "FNs reportados" que son TN alineados vs FNs reales.

Si ≥80% son TN alineados, el "límite físico Lascar" se confirma como
alineación con MIROVA, no como nuestra deficiencia.
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
TOL_MIN = 60


def parse_csv_dt(s):
    return datetime.strptime(s.strip(), "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
def parse_rec_dt(s):
    s = s.strip().replace("Z","+00:00")
    for fmt in ("%Y-%m-%d %H:%M:%S","%Y-%m-%d %H:%M"):
        try: return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
        except: continue
    return datetime.fromisoformat(s)


# Cargar CSV MIROVA filtrado a Lascar
df = pd.read_csv(CSV)
df['dt'] = df['Fecha_Satelite_UTC'].apply(parse_csv_dt)
df = df[(df['dt'] >= START_DT) & (df['dt'] <= END_DT)]
df_lascar = df[df['Volcan'] == 'Lascar']
print(f"# P3 Lascar — alineamiento FNs MODIS\n")
print(f"Window: {START_DT.date()} -> {END_DT.date()}")
print(f"Refs MIROVA Lascar (todas): {len(df_lascar)}")

modis_alertas = df_lascar[(df_lascar['Sensor']=='MODIS') & (df_lascar['Tipo_Registro']=='ALERTA_TERMICA')]
modis_rutina  = df_lascar[(df_lascar['Sensor']=='MODIS') & (df_lascar['Tipo_Registro']=='RUTINA')]
modis_fp      = df_lascar[(df_lascar['Sensor']=='MODIS') & (df_lascar['Tipo_Registro']=='FALSO_POSITIVO')]
print(f"\nMIROVA MODIS Lascar 90d:")
print(f"  ALERTA_TERMICA (deteccion): {len(modis_alertas)}")
print(f"  RUTINA (no deteccion): {len(modis_rutina)}")
print(f"  FALSO_POSITIVO: {len(modis_fp)}")
print(f"  Total MODIS records: {len(modis_alertas)+len(modis_rutina)+len(modis_fp)}")

# Cargar nuestros records Lascar MODIS
recs = []
for r in json.loads((DATA/"Lascar.json").read_text(encoding='utf-8')).get('records', []):
    if not r.get('sensor','').startswith('MODIS'): continue
    try: dt = parse_rec_dt(r['datetime_utc'])
    except: continue
    if START_DT <= dt <= END_DT:
        r['_dt'] = dt
        recs.append(r)
print(f"\nNuestros records Lascar MODIS 90d: {len(recs)}")
n_pos = sum(1 for r in recs if (r.get('vrp_mw') or 0)>0)
n_test1 = sum(1 for r in recs if r.get('triggered_test1'))
print(f"  con vrp_mw>0: {n_pos}")
print(f"  triggered_test1: {n_test1}")

# Pareo: para cada nuestro record (vrp_mw=0), buscar en CSV MIROVA misma noche
print(f"\n## Análisis: en records nuestros con vrp_mw=0, ¿qué reportó MIROVA?\n")
cats = defaultdict(int)
fn_real_examples = []
tn_aligned_examples = []
for rec in recs:
    if (rec.get('vrp_mw') or 0) > 0: continue  # nuestra detección, no FN
    # Buscar match temporal en CSV (cualquier Tipo_Registro)
    tol = timedelta(minutes=TOL_MIN)
    candidates = df_lascar[df_lascar['Sensor']=='MODIS']
    matches = candidates[abs(candidates['dt']-rec['_dt']) <= tol]
    if matches.empty:
        cats['no_pareo_csv'] += 1
        continue
    # Tomar el más cercano
    matches = matches.copy()
    matches['delta'] = abs(matches['dt']-rec['_dt'])
    best = matches.sort_values('delta').iloc[0]
    tipo = best['Tipo_Registro']
    cats[tipo] += 1
    if tipo == 'ALERTA_TERMICA':
        fn_real_examples.append((rec['_dt'].strftime('%Y-%m-%d %H:%M'),
                                 best['VRP_MW'], rec.get('sensor','?'),
                                 rec.get('n_anomalous_pixels',0),
                                 rec.get('triggered_test1',False)))
    elif tipo == 'RUTINA':
        tn_aligned_examples.append((rec['_dt'].strftime('%Y-%m-%d %H:%M'),
                                    rec.get('n_anomalous_pixels',0)))

total_zeros = sum(cats.values()) + cats['no_pareo_csv']
total_zeros_with_match = sum(v for k,v in cats.items() if k != 'no_pareo_csv')
print(f"Records nuestros vrp=0 totales: {len(recs)-n_pos}")
print(f"Categoría:")
for k, v in sorted(cats.items(), key=lambda x:-x[1]):
    pct = v/max(1,len(recs)-n_pos)*100
    print(f"  - {k}: {v} ({pct:.1f}%)")

print(f"\n## Veredicto P3 Lascar MODIS\n")
fn_real = cats.get('ALERTA_TERMICA', 0)
tn_aligned = cats.get('RUTINA', 0) + cats.get('FALSO_POSITIVO', 0)
total_meaningful = fn_real + tn_aligned
if total_meaningful > 0:
    pct_aligned = tn_aligned / total_meaningful * 100
    pct_fn_real = fn_real / total_meaningful * 100
    print(f"De los records donde NOSOTROS no detectamos pero MIROVA SÍ tiene observación:")
    print(f"  - FN reales (MIROVA detectó, perdimos): {fn_real} ({pct_fn_real:.1f}%)")
    print(f"  - TN alineados (MIROVA tampoco detectó): {tn_aligned} ({pct_aligned:.1f}%)")
    if pct_aligned >= 80:
        print(f"\n**CONFIRMADO**: ≥80% son TN alineados → 'límite físico Lascar' es alineación con MIROVA, no deficiencia.")
    elif pct_aligned >= 50:
        print(f"\n**PARCIAL**: mayoría TN alineados pero {pct_fn_real:.0f}% son FNs reales — vale la pena investigar.")
    else:
        print(f"\n**NO CONFIRMADO**: la mayoría son FNs reales — Lascar MODIS deficiencia activa.")

# Función mirovaEqVrp (replica frontend Driver A)
def mirova_eq_vrp(r):
    if not r: return 0
    pc = r.get('primary_cluster')
    if not pc: return r.get('vrp_mw') or 0
    if r.get('distance_class') and r.get('distance_class') != 'summit': return 0
    return pc.get('vrp_mw', 0)

# Matriz confusión con summit-only (Driver A frontend metric)
print(f"\n## Matriz confusión Lascar MODIS — métrica SUMMIT-ONLY (Driver A frontend)\n")
tp_fp = defaultdict(int)
for rec in recs:
    has_detection = mirova_eq_vrp(rec) > 0
    candidates = df_lascar[df_lascar['Sensor']=='MODIS']
    matches = candidates[abs(candidates['dt']-rec['_dt']) <= timedelta(minutes=TOL_MIN)]
    if matches.empty:
        tp_fp['nuestro_'+('det' if has_detection else 'no_det')+'_csv_no_pareo'] += 1
        continue
    matches = matches.copy()
    matches['delta'] = abs(matches['dt']-rec['_dt'])
    best = matches.sort_values('delta').iloc[0]
    tipo = best['Tipo_Registro']
    key_us = 'det' if has_detection else 'no_det'
    if tipo == 'ALERTA_TERMICA':
        tp_fp[f'nuestro_{key_us}_mirova_alerta'] += 1
    elif tipo == 'RUTINA':
        tp_fp[f'nuestro_{key_us}_mirova_rutina'] += 1
    elif tipo == 'FALSO_POSITIVO':
        tp_fp[f'nuestro_{key_us}_mirova_fp'] += 1

# Render como matriz 2x3
labels_us = ['det', 'no_det']
labels_csv = ['mirova_alerta', 'mirova_rutina', 'mirova_fp']
print("|        | MIROVA ALERTA | MIROVA RUTINA | MIROVA FALSO_POSITIVO |")
print("|---|---:|---:|---:|")
for u in labels_us:
    row_label = "Nuestro DET" if u=='det' else "Nuestro NO-DET"
    cells = [tp_fp.get(f'nuestro_{u}_{c}', 0) for c in labels_csv]
    print(f"| {row_label} | {cells[0]} | {cells[1]} | {cells[2]} |")

# Métricas derivadas
TP = tp_fp.get('nuestro_det_mirova_alerta', 0)
FP = tp_fp.get('nuestro_det_mirova_rutina', 0)  # MIROVA dice no, nosotros sí
FN = tp_fp.get('nuestro_no_det_mirova_alerta', 0)
TN = tp_fp.get('nuestro_no_det_mirova_rutina', 0)
n_total = TP + FP + FN + TN
if n_total > 0:
    print(f"\n- TP (ambos detectan): {TP}")
    print(f"- FP (nosotros sí, MIROVA no): {FP}")
    print(f"- FN (MIROVA sí, nosotros no): {FN}")
    print(f"- TN (ambos rutina): {TN}")
    if TP+FN > 0:
        print(f"- **Recall MODIS Lascar = TP/(TP+FN) = {TP}/{TP+FN} = {TP/(TP+FN)*100:.1f}%**")
    if TP+FP > 0:
        print(f"- **Precision MODIS Lascar = TP/(TP+FP) = {TP}/{TP+FP} = {TP/(TP+FP)*100:.1f}%**")
    print(f"- **Accuracy = (TP+TN)/total = {(TP+TN)}/{n_total} = {(TP+TN)/n_total*100:.1f}%**")

# Mostrar algunos FNs reales para inspección
if fn_real_examples:
    print(f"\n### Ejemplos FNs reales (MIROVA detectó, nosotros vrp=0):\n")
    print("| Fecha UTC | MIROVA MW | Sensor nuestro | n_anom_pix | T1? |")
    print("|---|---:|---|---:|:--:|")
    for dt, mvrp, sens, nap, t1 in fn_real_examples[:10]:
        print(f"| {dt} | {mvrp:.3f} | {sens} | {nap} | {'Y' if t1 else 'N'} |")
    print(f"\n(Total FNs reales: {len(fn_real_examples)})")
