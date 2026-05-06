"""S33 R3 — audit independiente del frontend.

Diseñado para auditar D4, Phase 1, Driver A y futuros A/B SIN compartir
código con el frontend ni con experiments/65/71/73.

Re-implementa la lógica de "VRP MIROVA-equivalente" desde primer principio,
documentando cada decisión inline. Si los resultados de este audit difieren
de experiments/65 (que usa pipeline.audit_metrics.mirova_eq_vrp), hay
divergencia entre las dos implementaciones — eso es señal de bug en una
de ellas.

Política R3 (S33+): cualquier resultado A/B importante debe coincidir entre
este script y experiments/65. Si difieren, NO confiar en el resultado hasta
encontrar la causa.
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

# Tabla independiente — NO importada de pipeline.audit_metrics.
# Si esta tabla difiere de la otra, el test_audit_metrics fallará.
INNER_RADIUS_KM = {
    'Lascar': 5, 'Lastarria': 3, 'Tupungatito': 7, 'Villarrica': 5,
    'PuyehueCordonCaulle': 20, 'Copahue': 4, 'NevadosDeChillan': 5,
    'Llaima': 5, 'Chaiten': 5, 'PlanchonPeteroa': 3, 'Isluga': 5,
}

VOLC_MAP = {
    'Lascar':'Lascar','Lastarria':'Lastarria','Tupungatito':'Tupungatito',
    'Villarrica':'Villarrica','Puyehue-Cordon Caulle':'PuyehueCordonCaulle',
    'Copahue':'Copahue','Nevados de Chillan':'NevadosDeChillan',
    'Llaima':'Llaima','Chaiten':'Chaiten','PlanchonPeteroa':'PlanchonPeteroa',
    'Isluga':'Isluga'
}

END_DT = datetime(2026,4,29,23,59,tzinfo=timezone.utc)
START_DT = END_DT - timedelta(days=90)
TOL_MIN = 60


def parse_csv_dt(s):
    return datetime.strptime(s.strip(), "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)


def parse_rec_dt(s):
    s = s.strip().replace("Z", "+00:00")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return datetime.fromisoformat(s)


def sensor_match(csv_sensor, our_sensor):
    if csv_sensor == 'MODIS':
        return our_sensor.startswith('MODIS')
    if csv_sensor == 'VIIRS':
        return our_sensor.startswith('VIIRS_') and our_sensor.endswith('_750')
    if csv_sensor == 'VIIRS375':
        return our_sensor.startswith('VIIRS_') and not our_sensor.endswith('_750')
    return False


def detection_vrp_independent(record, volcano_name):
    """Independiente de pipeline.audit_metrics.mirova_eq_vrp.

    Re-implementación desde primer principio. Si difiere del otro,
    hay bug en alguno de los dos.

    Lógica:
      Step 1: si record None → 0.
      Step 2: distance_class explicit 'far' → 0 (pipeline ya lo descartó).
      Step 3: si no hay primary_cluster, fallback legacy a vrp_mw global.
      Step 4: validar pc.centroid_dist_km <= inner_radius_km del volcán.
              Esto es CRÍTICO: distance_class podría ser 'summit' por
              final_hotspot Test1 cerca, pero pc puede estar lejos
              (Salar/lago). Si pc lejos, NO es VRP del cráter.
      Step 5: return pc.vrp_mw si todo pasa.
    """
    # Step 1
    if record is None or not isinstance(record, dict):
        return 0.0
    # Step 2
    distance_class = record.get('distance_class', None)
    if distance_class == 'far':
        return 0.0
    # Step 3 - legacy fallback
    primary_cluster = record.get('primary_cluster', None)
    if primary_cluster is None:
        global_vrp = record.get('vrp_mw', 0.0)
        return float(global_vrp) if global_vrp else 0.0
    # Step 4 - validación pc dist
    pc_centroid_dist_km = primary_cluster.get('centroid_dist_km', None)
    inner_km_volcano = INNER_RADIUS_KM.get(volcano_name, 10)
    if pc_centroid_dist_km is not None:
        if pc_centroid_dist_km > inner_km_volcano:
            return 0.0
    # Step 5
    pc_vrp = primary_cluster.get('vrp_mw', 0.0)
    return float(pc_vrp) if pc_vrp else 0.0


def load_records_window(profile_dir, volcano_name):
    f = profile_dir / f"{volcano_name}.json"
    if not f.exists():
        return []
    raw = json.loads(f.read_text(encoding='utf-8'))
    out = []
    for r in raw.get('records', []):
        try:
            dt = parse_rec_dt(r.get('datetime_utc', ''))
        except (ValueError, KeyError):
            continue
        if START_DT <= dt <= END_DT:
            r['_dt'] = dt
            out.append(r)
    return out


def find_match(reference_dt, reference_sensor, records):
    tolerance = timedelta(minutes=TOL_MIN)
    best = None
    best_delta = tolerance + timedelta(seconds=1)
    for r in records:
        if not sensor_match(reference_sensor, r.get('sensor', '')):
            continue
        delta = abs(r['_dt'] - reference_dt)
        if delta <= tolerance and delta < best_delta:
            best, best_delta = r, delta
    return best


def audit_profile(profile_dir, label):
    print(f"\n## Profile: {label}\n")
    if not profile_dir.exists():
        print(f"❌ {profile_dir} no existe"); return None

    df = pd.read_csv(CSV)
    df['dt'] = df['Fecha_Satelite_UTC'].apply(parse_csv_dt)
    df = df[(df['dt'] >= START_DT) & (df['dt'] <= END_DT)]
    df = df[df['Volcan'].isin(VOLC_MAP.keys())]
    df = df[df['Tipo_Registro'] == 'ALERTA_TERMICA']

    by_volcano = defaultdict(lambda: {'refs': 0, 'tps': 0, 'ratios': []})
    for _, row in df.iterrows():
        csv_volcano = row['Volcan']
        our_volcano = VOLC_MAP[csv_volcano]
        by_volcano[our_volcano]['refs'] += 1
        records = load_records_window(profile_dir, our_volcano)
        rec = find_match(row['dt'], row['Sensor'], records)
        if rec is None:
            continue
        our_vrp = detection_vrp_independent(rec, our_volcano)
        if our_vrp > 0:
            by_volcano[our_volcano]['tps'] += 1
            mirova_vrp = float(row['VRP_MW']) if row['VRP_MW'] else 0
            if mirova_vrp > 0:
                by_volcano[our_volcano]['ratios'].append(our_vrp / mirova_vrp)

    print("| Volcán | Refs | TPs | Recall % | Ratio mediano |")
    print("|---|---:|---:|---:|---:|")
    global_refs, global_tps, all_ratios = 0, 0, []
    for vol in sorted(by_volcano.keys()):
        d = by_volcano[vol]
        global_refs += d['refs']
        global_tps += d['tps']
        all_ratios.extend(d['ratios'])
        recall_pct = d['tps'] / d['refs'] * 100 if d['refs'] else 0
        sorted_ratios = sorted(d['ratios'])
        median_ratio = sorted_ratios[len(sorted_ratios)//2] if sorted_ratios else float('nan')
        ratio_str = f"{median_ratio:.2f}" if sorted_ratios else "NA"
        print(f"| {vol} | {d['refs']} | {d['tps']} | {recall_pct:.1f} | {ratio_str} |")

    global_recall = global_tps / max(1, global_refs) * 100
    all_ratios.sort()
    global_median = all_ratios[len(all_ratios)//2] if all_ratios else float('nan')
    print(f"\n**GLOBAL — Recall: {global_recall:.1f}% ({global_tps}/{global_refs}). "
          f"Ratio mediano: {global_median:.2f}x.**")
    return {'recall': global_recall, 'ratio': global_median, 'by_vol': dict(by_volcano)}


def main():
    print("# Audit independiente — R3 implementación re-derivada\n")
    print(f"Window: {START_DT.date()} -> {END_DT.date()}")
    print(f"Política R3: este script NO comparte código con frontend ni audits previos.")
    print(f"Si discrepa con experiments/65, hay bug en alguno.\n")

    profiles = {
        'mirova_equivalent (operacional Phase 1 ON)': ROOT / "data" / "mirova_equivalent",
        'filter_OFF (control, Phase 1 OFF)': ROOT / "data" / "mirova_equivalent_test1pix_disabled",
        'filter_ON (Phase 1 explicit ON)': ROOT / "data" / "mirova_equivalent_test1pix_filter",
    }

    # D4 si existe
    d4_dir = ROOT / "data" / "mirova_equivalent_lbg_global"
    if d4_dir.exists():
        profiles['D4 (L_bg global)'] = d4_dir

    results = {}
    for label, prof_dir in profiles.items():
        results[label] = audit_profile(prof_dir, label)

    print("\n" + "="*80)
    print("\n## Comparación cross-profile\n")
    print("| Profile | Recall % | Ratio mediano |")
    print("|---|---:|---:|")
    for label, r in results.items():
        if r is None:
            print(f"| {label} | — | — |"); continue
        print(f"| {label} | {r['recall']:.1f} | {r['ratio']:.2f}x |")


if __name__ == '__main__':
    main()
