"""S65 Audit — Tupungatito post-fix mirova_center.

Pre-condicion: workflow 26143572382 completado.
  git pull --rebase origin main
  python experiments/115_s65_audit_tupungatito_post_fix.py

Verifica:
- vent_anchored ancla ahora en vent_lat (cráter activo) en vez de mirova_center (bbox SE)
- Ratio mediano LEGACY 10.37× cura a ~1-3× post-fix
- Bin centroides shifts de (-33.43, -69.79) FP a (-33.39, -69.83) cráter real

Verdict criterio:
- Recall >= LEGACY 70/92
- Ratio mediano < 3×
- Si valida: mantener fix mergeado, S65 cierra
- Si NO valida: revertir mirova_center back, investigar S66+
"""
import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import csv
import json
import statistics
from collections import defaultdict
from datetime import datetime
from pathlib import Path

WINDOW_START = datetime(2026, 3, 1)
WINDOW_END = datetime(2026, 5, 20, 23, 59, 59)

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
            refs.append({'dt': dt, 'sensor': row['Sensor'], 'vrp': vrp})
    return refs


def audit():
    cons = load_refs(CSV_CONS, 'Tupungatito', ['ALERTA_TERMICA'])
    ocr = load_refs(CSV_OCR, 'Tupungatito', ['ALERTA_TERMICA_OCR'])
    refs = cons + ocr
    print(f'Tupungatito CONS+OCR ALERTAS window {WINDOW_START.date()} a {WINDOW_END.date()}: {len(refs)}')

    json_path = 'data/mirova_equivalent/Tupungatito.json'
    with open(json_path, encoding='utf-8') as f:
        recs = json.load(f).get('records', [])

    ratios = []
    detected = 0
    centroid_bins = defaultdict(int)
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
        clat, clon = pc.get('centroid_lat'), pc.get('centroid_lon')
        if clat and clon:
            centroid_bins[(round(clat, 2), round(clon, 2))] += 1

    print(f'\nDetected pc.vrp>0: {detected}/{len(refs)} = {100*detected/len(refs):.0f}%')
    if ratios:
        med = statistics.median(ratios)
        in_range = sum(1 for x in ratios if 0.5 <= x <= 2.0)
        le3 = sum(1 for x in ratios if x <= 3.0)
        print(f'Ratio pc.vrp/MIROVA: median={med:.2f}x  min={min(ratios):.2f}  max={max(ratios):.2f}')
        print(f'En rango [0.5, 2.0]: {in_range}/{len(ratios)} ({100*in_range/len(ratios):.0f}%)')
        print(f'Aceptable <=3.0x: {le3}/{len(ratios)} ({100*le3/len(ratios):.0f}%)')

    print(f'\nTop 5 centroides bins (esperado bin cráter (-33.39, -69.83) dominar post-fix):')
    for (la, lo), n in sorted(centroid_bins.items(), key=lambda x: -x[1])[:5]:
        print(f'  ({la:.2f}, {lo:.2f}): {n} records')

    print('\n--- VERDICT Tupungatito S65 ---')
    print('  LEGACY baseline (S64 audit): recall 70/92, ratio 10.37x')
    if ratios:
        ok_recall = detected >= 70
        ok_ratio = statistics.median(ratios) < 3.0
        if ok_recall and ok_ratio:
            print('  ==> FIX VALIDA. Mantener mirova_center removido.')
        elif ok_ratio:
            print('  ==> Ratio mejora pero recall baja. Investigar.')
        else:
            print('  ==> NO VALIDA. Revertir agregando mirova_center back.')


if __name__ == '__main__':
    audit()
