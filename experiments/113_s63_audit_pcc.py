"""S63 Audit — PCC A/B kernel-bg.

Pre-condicion: workflow 26115708153 completado.
  git pull --rebase origin main
  python experiments/113_s63_audit_pcc.py

Verdict criterio:
- Recall NEW >= LEGACY (sin regresion)
- Ratio mediano NEW < LEGACY 3.51x
- Si NEW <3x: ADOPTAR local_kernel_bg=true PCC
"""
import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import csv
import json
import statistics
from datetime import datetime
from pathlib import Path

WINDOW_START = datetime(2026, 3, 1)
WINDOW_END = datetime(2026, 5, 19, 23, 59, 59)

CSV_CONS = 'data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv'
CSV_OCR = 'C:/Users/nmend/AppData/Local/Temp/csv_ocr.csv'


def sensor_family(s):
    if 'MODIS' in s:
        return 'MODIS'
    if '750' in s:
        return 'VIIRS750'
    if 'VIIRS' in s:
        return 'VIIRS375'
    return s


def load_refs(path, vol_csv, types):
    refs = []
    if not Path(path).exists():
        return refs
    with open(path, encoding='utf-8') as f:
        for row in csv.DictReader(f):
            if row.get('Volcan') != vol_csv:
                continue
            if row.get('Tipo_Registro') not in types:
                continue
            try:
                dt = datetime.strptime(row['Fecha_Satelite_UTC'], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                continue
            if not (WINDOW_START <= dt <= WINDOW_END):
                continue
            try:
                vrp = float(row['VRP_MW'])
            except ValueError:
                continue
            refs.append({'dt': dt, 'sensor': row['Sensor'], 'vrp': vrp, 'tipo': row['Tipo_Registro']})
    return refs


def audit(json_path, vol_csv, label):
    if not Path(json_path).exists():
        print(f'\n{label}: {json_path} NO EXISTE')
        return None
    cons = load_refs(CSV_CONS, vol_csv, ['ALERTA_TERMICA'])
    ocr = load_refs(CSV_OCR, vol_csv, ['ALERTA_TERMICA_OCR'])
    refs = cons + ocr
    if not refs:
        print(f'\n{label}: 0 ALERTAS')
        return None
    with open(json_path, encoding='utf-8') as f:
        recs = json.load(f).get('records', [])
    ratios = []
    detected = 0
    for r in refs:
        cands = []
        for rec in recs:
            try:
                rdt = datetime.fromisoformat(rec['datetime_utc'].replace('Z', ''))
            except (ValueError, KeyError):
                continue
            if abs((rdt - r['dt']).total_seconds()) > 900:
                continue
            if sensor_family(rec.get('sensor', '')) != sensor_family(r['sensor']):
                continue
            cands.append(rec)
        if not cands:
            continue
        best = min(cands, key=lambda x: (x.get('primary_cluster') or {}).get('centroid_dist_km', 99))
        pc = best.get('primary_cluster') or {}
        pc_vrp = pc.get('vrp_mw', 0)
        if pc_vrp <= 0:
            continue
        detected += 1
        if r['vrp'] > 0:
            ratios.append(pc_vrp / r['vrp'])
    print(f'\n=== {label} ===')
    print(f'  ALERTAS: {len(refs)} ({len(cons)} CONS + {len(ocr)} OCR)')
    print(f'  Detected pc.vrp>0: {detected}/{len(refs)} = {100*detected/len(refs):.0f}%')
    if not ratios:
        return None
    med = statistics.median(ratios)
    in_range = sum(1 for x in ratios if 0.5 <= x <= 2.0)
    le3 = sum(1 for x in ratios if x <= 3.0)
    print(f'  Ratio pc.vrp / MIROVA: median={med:.2f}x  min={min(ratios):.2f}  max={max(ratios):.2f}')
    print(f'  En rango [0.5, 2.0]: {in_range}/{len(ratios)} ({100*in_range/len(ratios):.0f}%)')
    print(f'  Aceptable <=3.0x: {le3}/{len(ratios)} ({100*le3/len(ratios):.0f}%)')
    return {'n_refs': len(refs), 'detected': detected, 'median_ratio': med,
            'in_range': in_range, 'total_ratios': len(ratios)}


def verdict(legacy, new):
    print(f'\n--- VERDICT PCC ---')
    if not legacy or not new:
        print('  Sin data suficiente')
        return
    recall_ok = new['detected'] >= legacy['detected']
    ratio_ok = new['median_ratio'] < legacy['median_ratio']
    print(f'  Recall: {legacy["detected"]} -> {new["detected"]} ({"OK" if recall_ok else "REGRESION"})')
    print(f'  Ratio mediano: {legacy["median_ratio"]:.2f}x -> {new["median_ratio"]:.2f}x ({"OK" if ratio_ok else "EMPEORA"})')
    print(f'  En rango: {legacy["in_range"]}/{legacy["total_ratios"]} -> {new["in_range"]}/{new["total_ratios"]}')
    if recall_ok and ratio_ok and new['median_ratio'] < 3.0:
        print('  ==> ADOPTAR local_kernel_bg=true PCC')
    elif recall_ok and ratio_ok:
        print('  ==> MEJORA pero ratio > 3.0x. Considerar adopcion + investigar residual.')
    else:
        print('  ==> NO ADOPTAR (verifica si patron Tupungatito-like)')


def main():
    legacy = audit('data/mirova_equivalent/PuyehueCordonCaulle.json', 'Puyehue-Cordon Caulle',
                   'PCC OPERACIONAL (LEGACY, inner=20 sin kernel-bg)')
    new = audit('data/_local_kernel_bg_enabled/PuyehueCordonCaulle.json', 'Puyehue-Cordon Caulle',
                'PCC NEW (con kernel-bg fix)')
    verdict(legacy, new)


if __name__ == '__main__':
    main()
