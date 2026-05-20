import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import json
import pandas as pd
from datetime import timedelta

with open('lastarria_high_summit.json') as f:
    records = json.load(f)

df_c = pd.read_csv('data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv')
las_c = df_c[df_c['Volcan'].str.contains('Lastarr', case=False, na=False)].copy()
las_c['ts'] = pd.to_datetime(las_c['Fecha_Satelite_UTC'], errors='coerce')

df_o = pd.read_csv('data/mirova_reference/registro_vrp_ocr.csv')
las_o = df_o[df_o['Volcan'].str.contains('Lastarr', case=False, na=False)].copy()
las_o['ts'] = pd.to_datetime(las_o['Fecha_Satelite_UTC'], errors='coerce')

TOLERANCE = timedelta(minutes=10)

matches = []
for r in records:
    rec_ts = pd.to_datetime(r['datetime_utc'])

    cons_m = las_c[(las_c['ts'] >= rec_ts - TOLERANCE) & (las_c['ts'] <= rec_ts + TOLERANCE)]
    ocr_m = las_o[(las_o['ts'] >= rec_ts - TOLERANCE) & (las_o['ts'] <= rec_ts + TOLERANCE)]

    cons_alerta = cons_m[cons_m['Tipo_Registro'] == 'ALERTA_TERMICA']
    cons_rutina = cons_m[cons_m['Tipo_Registro'] == 'RUTINA']
    cons_fp = cons_m[cons_m['Tipo_Registro'] == 'FALSO_POSITIVO']
    ocr_alerta = ocr_m[ocr_m['Tipo_Registro'] == 'ALERTA_TERMICA_OCR']
    ocr_fp = ocr_m[ocr_m['Tipo_Registro'] == 'FALSO_POSITIVO_OCR']

    mirova_alerta = (len(cons_alerta) + len(ocr_alerta)) > 0

    matches.append({
        'datetime_utc': r['datetime_utc'],
        'sensor': r['sensor'],
        'pc_vrp_mw': r['pc_vrp_mw'],
        'path': f"BT{r['diag_n_bt_path']}/NTI{r['diag_n_nti_path']}/dNTI{r['diag_n_dnti_ctx_path']}",
        't_bg_k': r['t_bg_k'],
        't_max_k': r['t_max_k'],
        'cons_alerta_n': len(cons_alerta),
        'cons_alerta_vrp_max': float(cons_alerta['VRP_MW'].max()) if not cons_alerta.empty else None,
        'cons_rutina_n': len(cons_rutina),
        'cons_fp_n': len(cons_fp),
        'cons_fp_sensors': list(cons_fp['Sensor'].unique()) if not cons_fp.empty else [],
        'ocr_alerta_n': len(ocr_alerta),
        'ocr_alerta_vrp_max': float(ocr_alerta['VRP_MW'].max()) if not ocr_alerta.empty else None,
        'ocr_fp_n': len(ocr_fp),
        'mirova_alerta': mirova_alerta,
        'any_mirova_record': len(cons_m) + len(ocr_m) > 0,
    })

total = len(matches)
mirova_si = sum(1 for m in matches if m['mirova_alerta'])
mirova_no = total - mirova_si

# Cuantos tienen ALGUN registro MIROVA (aunque sea RUTINA o FP)
no_mirova_any = sum(1 for m in matches if not m['any_mirova_record'])
mirova_fp = sum(1 for m in matches if m['cons_fp_n'] > 0 or m['ocr_fp_n'] > 0)
mirova_rutina_only = sum(1 for m in matches if (m['cons_rutina_n'] > 0 and not m['mirova_alerta'] and m['cons_fp_n'] == 0 and m['ocr_fp_n'] == 0))

print('=' * 90)
print('CROSS-CHECK RESULTS')
print('=' * 90)
print(f'Total records nuestros summit eqVrp>5: {total}')
print(f'MIROVA reporta ALERTA (cons o OCR): {mirova_si} ({100*mirova_si/total:.1f}%)')
print(f'MIROVA NO reporta ALERTA: {mirova_no} ({100*mirova_no/total:.1f}%)')
print(f'  --> Desglose MIROVA-NO:')
print(f'      MIROVA marca FALSO_POSITIVO: {mirova_fp}')
print(f'      MIROVA marca RUTINA solo (sin alerta, sin FP): {mirova_rutina_only}')
print(f'      MIROVA NO tiene registro alguno (sin granule MIROVA): {no_mirova_any}')
print()
print('Detalle por record (orden vrp desc):')
print('-' * 90)
for m in matches:
    flag = 'OK MIROVA-ALERTA' if m['mirova_alerta'] else ('FP-MIROVA' if (m['cons_fp_n']>0 or m['ocr_fp_n']>0) else ('RUTINA-only' if m['cons_rutina_n']>0 else 'NO-MIROVA'))
    cons_a_vrp = f"{m['cons_alerta_vrp_max']:.2f}" if m['cons_alerta_vrp_max'] is not None else '-'
    ocr_a_vrp = f"{m['ocr_alerta_vrp_max']:.2f}" if m['ocr_alerta_vrp_max'] is not None else '-'
    tbg = m['t_bg_k'] if m['t_bg_k'] is not None else 0
    print(f"  [{flag:18s}] {m['datetime_utc']} {m['sensor']:20s} vrp_ours={m['pc_vrp_mw']:5.2f}MW path={m['path']:18s} t_bg={tbg:5.1f}K  CONS(A={m['cons_alerta_n']} vrp={cons_a_vrp}, R={m['cons_rutina_n']}, FP={m['cons_fp_n']}) OCR(A={m['ocr_alerta_n']} vrp={ocr_a_vrp}, FP={m['ocr_fp_n']})")

# Sub-analysis FPs
fps = [m for m in matches if not m['mirova_alerta']]
print()
print('=' * 90)
print(f'SUB-ANALISIS DE FPs candidatos ({len(fps)})')
print('=' * 90)
dnti_only = [m for m in fps if m['path'].startswith('BT0/NTI0/dNTI')]
print(f'FPs path D solo (BT0/NTI0/dNTI>0): {len(dnti_only)} de {len(fps)}')
bt_or_nti = [m for m in fps if not m['path'].startswith('BT0/NTI0/')]
print(f'FPs co-validados BT o NTI: {len(bt_or_nti)} de {len(fps)}')

import statistics
fp_tbg = [m['t_bg_k'] for m in fps if m['t_bg_k'] is not None]
if fp_tbg:
    print(f't_bg distribucion FPs: median={statistics.median(fp_tbg):.1f}K min={min(fp_tbg):.1f}K max={max(fp_tbg):.1f}K')
cold_fps = [m for m in fps if m['t_bg_k'] is not None and m['t_bg_k'] < 260]
print(f'FPs con t_bg < 260K (cirrus muy frio): {len(cold_fps)}/{len(fps)} ({100*len(cold_fps)/len(fps):.1f}%)')
cold_fps_270 = [m for m in fps if m['t_bg_k'] is not None and m['t_bg_k'] < 270]
print(f'FPs con t_bg < 270K (cirrus/frio): {len(cold_fps_270)}/{len(fps)} ({100*len(cold_fps_270)/len(fps):.1f}%)')

# All-32 path distribution (sanity)
print()
print('=' * 90)
print('SANIDAD: distribucion path en los 32')
print('=' * 90)
dnti_only_all = [m for m in matches if m['path'].startswith('BT0/NTI0/dNTI')]
print(f'Todos los 32 son path D solo? {len(dnti_only_all) == 32} (count={len(dnti_only_all)})')

with open('cross_check_results.json', 'w') as f:
    json.dump({
        'total': total,
        'mirova_alerta_si': mirova_si,
        'mirova_alerta_no': mirova_no,
        'mirova_fp_marca': mirova_fp,
        'mirova_rutina_only': mirova_rutina_only,
        'no_mirova_record': no_mirova_any,
        'matches': matches,
    }, f, indent=2, default=str)
print('\ncross_check_results.json guardado')
