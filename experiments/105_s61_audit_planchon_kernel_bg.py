"""S61 Audit — PlanchonPeteroa LEGACY vs NEW kernel-bg.

Compara recall + ratio MIROVA/nuestro sobre window 02-20/05-15 ALERTAS reales.

Pre-condición: workflow run 26035918192 completo y JSON
  data/_local_kernel_bg_enabled/PlanchonPeteroa.json existe en main.

Uso:
  python experiments/105_s61_audit_planchon_kernel_bg.py
"""
import json
import csv
import statistics
from datetime import datetime
from pathlib import Path

VOL = 'PlanchonPeteroa'
WINDOW_START = datetime(2026, 2, 20)
WINDOW_END = datetime(2026, 5, 15, 23, 59, 59)

CSV_PATH = Path('data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv')
NEW_PATH = Path(f'data/_local_kernel_bg_enabled/{VOL}.json')
LEGACY_PATH = Path(f'data/mirova_equivalent/{VOL}.json')


def load_mirova_refs():
    """Filtrar CSV a PlanchonPeteroa ALERTA+FP en window."""
    refs = []
    with open(CSV_PATH, encoding='utf-8') as f:
        for row in csv.DictReader(f):
            if row['Volcan'] != VOL:
                continue
            if row['Tipo_Registro'] not in ('ALERTA_TERMICA', 'FALSO_POSITIVO'):
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
            refs.append({
                'dt': dt,
                'sensor': row['Sensor'],
                'vrp': vrp,
                'dist': float(row['Distancia_km']),
                'tipo': row['Tipo_Registro'],
            })
    return refs


def sensor_family(s):
    if 'MODIS' in s:
        return 'MODIS'
    if '750' in s:
        return 'VIIRS750'
    if 'VIIRS' in s:
        return 'VIIRS375'
    return s


def match_records(refs, recs_path, label):
    """Para cada ref MIROVA, encontrar el record nuestro más cercano en tiempo + sensor."""
    if not Path(recs_path).exists():
        print(f'\n!!! {recs_path} NO EXISTE — workflow PP no completó aún?')
        return []
    with open(recs_path, encoding='utf-8') as f:
        recs = json.load(f).get('records', [])
    results = []
    for r in refs:
        candidates = []
        for rec in recs:
            try:
                rec_dt = datetime.fromisoformat(rec['datetime_utc'].replace('Z', ''))
            except (ValueError, KeyError):
                continue
            if abs((rec_dt - r['dt']).total_seconds()) > 900:
                continue
            if sensor_family(rec.get('sensor', '')) != sensor_family(r['sensor']):
                continue
            candidates.append(rec)
        if candidates:
            best = max(candidates, key=lambda x: x.get('vrp_mw') or 0)
            # CRITICO S61: usar primary_cluster.vrp_mw (alineado con MIROVA NRT)
            # y NO record.vrp_mw (scene-wide sum con clusters lejanos). El dashboard
            # frontend/index.html usa pc.vrp_mw (linea 680). REAUDITORIA_S52 documentado.
            pc = best.get('primary_cluster') or {}
            vrp_ours = pc.get('vrp_mw', best.get('vrp_mw') or 0)
            dist_ours = best.get('final_hotspot_dist_km') or best.get('hotspot_dist_km') or -1
            ratio = vrp_ours / r['vrp'] if r['vrp'] > 0 else 0
            results.append({
                **r,
                'matched': True,
                'our_vrp': vrp_ours,
                'our_dist': dist_ours,
                'ratio': ratio,
            })
        else:
            results.append({**r, 'matched': False, 'our_vrp': 0, 'our_dist': -1, 'ratio': 0})
    return results


def summarize(results, label):
    alerta = [r for r in results if r['tipo'] == 'ALERTA_TERMICA']
    alerta_matched = [r for r in alerta if r['matched'] and r['our_vrp'] > 0]
    ratios = [r['ratio'] for r in alerta_matched]
    print(f'\n=== {label} ===')
    print(f'ALERTA recall: {len(alerta_matched)}/{len(alerta)} = {100 * len(alerta_matched) / max(1, len(alerta)):.1f}%')
    if ratios:
        print(f'Ratio ALERTAS: median={statistics.median(ratios):.2f}x  min={min(ratios):.2f}x  max={max(ratios):.2f}x')
        in_range = sum(1 for r in ratios if 0.5 <= r <= 2.0)
        print(f'Ratios en rango tolerable [0.5, 2.0]: {in_range}/{len(ratios)}')
        ge3 = sum(1 for r in ratios if r >= 3.0)
        print(f'Ratios sobre 3.0x (potencialmente inflados): {ge3}/{len(ratios)}')


def main():
    refs = load_mirova_refs()
    print(f'PlanchonPeteroa MIROVA refs en window 02-20/05-15: {len(refs)}')
    alerta_n = sum(1 for r in refs if r['tipo'] == 'ALERTA_TERMICA')
    fp_n = sum(1 for r in refs if r['tipo'] == 'FALSO_POSITIVO')
    print(f'  ALERTA: {alerta_n}, FP: {fp_n}')

    legacy_res = match_records(refs, LEGACY_PATH, 'LEGACY median-ring')
    new_res = match_records(refs, NEW_PATH, 'NEW kernel-bg')

    if not new_res:
        print('\n!!! Audit incompleto — esperar workflow PP terminar.')
        return

    summarize(legacy_res, 'LEGACY median-ring')
    summarize(new_res, 'NEW kernel-bg')

    # Side-by-side per ALERTA
    print('\n=== Side-by-side per ALERTA (MIROVA | LEGACY | NEW) ===')
    print(f'{"DateTime":20} {"MIROVA":>7} {"LEGACY VRP / ratio":>22} {"NEW VRP / ratio":>22}')
    print('-' * 90)
    for l, n in zip(legacy_res, new_res):
        if l['tipo'] != 'ALERTA_TERMICA':
            continue
        l_str = f'{l["our_vrp"]:.2f} / {l["ratio"]:.2f}x' if l['matched'] else 'NO MATCH'
        n_str = f'{n["our_vrp"]:.2f} / {n["ratio"]:.2f}x' if n['matched'] else 'NO MATCH'
        print(f'{l["dt"]!s:20} {l["vrp"]:>7.2f} {l_str:>22} {n_str:>22}')

    # Side-by-side per FP
    print('\n=== Side-by-side per FALSO_POSITIVO ===')
    print(f'{"DateTime":20} {"MIROVA":>7} {"LEGACY VRP / ratio":>22} {"NEW VRP / ratio":>22}')
    print('-' * 90)
    for l, n in zip(legacy_res, new_res):
        if l['tipo'] != 'FALSO_POSITIVO':
            continue
        l_str = f'{l["our_vrp"]:.2f} / {l["ratio"]:.2f}x' if l['matched'] else 'NO MATCH'
        n_str = f'{n["our_vrp"]:.2f} / {n["ratio"]:.2f}x' if n['matched'] else 'NO MATCH'
        print(f'{l["dt"]!s:20} {l["vrp"]:>7.2f} {l_str:>22} {n_str:>22}')

    # Adoption verdict heuristic
    print('\n=== ADOPCIÓN VERDICT HEURÍSTICO ===')
    legacy_alerta = [r for r in legacy_res if r['tipo'] == 'ALERTA_TERMICA' and r['matched'] and r['our_vrp'] > 0]
    new_alerta = [r for r in new_res if r['tipo'] == 'ALERTA_TERMICA' and r['matched'] and r['our_vrp'] > 0]
    legacy_med = statistics.median([r['ratio'] for r in legacy_alerta]) if legacy_alerta else float('inf')
    new_med = statistics.median([r['ratio'] for r in new_alerta]) if new_alerta else float('inf')

    print(f'Recall LEGACY: {len(legacy_alerta)}, Recall NEW: {len(new_alerta)}')
    print(f'Ratio mediano LEGACY: {legacy_med:.2f}x, NEW: {new_med:.2f}x')

    recall_ok = len(new_alerta) >= len(legacy_alerta)
    ratio_ok = new_med < legacy_med
    if recall_ok and ratio_ok:
        print('\n✅ ADOPTAR: recall sin regresión + ratio mediano mejora.')
    elif recall_ok and not ratio_ok:
        print('\n⚠️  MIXTO: recall sin regresión pero ratio mediano no mejora. Decidir manualmente.')
    elif not recall_ok:
        print('\n❌ NO ADOPTAR: regresión de recall.')


if __name__ == '__main__':
    main()
