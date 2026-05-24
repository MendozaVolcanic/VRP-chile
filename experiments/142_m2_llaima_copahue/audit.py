"""
F48 / S77 M2 — audit refs MIROVA Llaima/Copahue.

Cuenta filas por volcán en los CSV consolidados y muestra muestras.
"""
import sys, io, csv, json
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT = Path(__file__).resolve().parents[2]

CSVS = {
    'latest_consolidado.csv': ROOT / 'latest_consolidado.csv',
    'mirova_v1_snapshot/registro_vrp_consolidado.csv': ROOT / 'data' / 'mirova_reference' / 'mirova_v1_snapshot' / 'registro_vrp_consolidado.csv',
    '01_05_2026_registro_vrp_consolidado.csv': ROOT / '01_05_2026_registro_vrp_consolidado.csv',
}

TARGETS = {'Llaima', 'Copahue', 'Lascar', 'PuyehueCordonCaulle', 'Lastarria', 'Villarrica', 'Chaiten', 'NevadosDeChillan', 'Tupungatito', 'PlanchonPeteroa', 'Isluga'}

for name, path in CSVS.items():
    print(f'\n=== {name} ===')
    if not path.exists():
        print('  NOT FOUND')
        continue
    print(f'  size: {path.stat().st_size:,} bytes')
    counter = Counter()
    samples = defaultdict(list)
    headers = None
    with path.open('r', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        for row in reader:
            vol = row.get('Volcan') or row.get('volcano') or row.get('volcan') or row.get('Volcano') or ''
            vol = vol.strip()
            counter[vol] += 1
            if vol in TARGETS and len(samples[vol]) < 3:
                samples[vol].append(row)
    print(f'  headers: {headers}')
    print(f'  unique volcanoes: {len(counter)}')
    print(f'  total rows: {sum(counter.values()):,}')
    print('  rows per target volcano:')
    for v in sorted(TARGETS):
        print(f'    {v}: {counter.get(v, 0)}')
    print('  other top volcano names (top 10):')
    others = [(k,v) for k,v in counter.most_common(20) if k not in TARGETS][:10]
    for k,v in others:
        print(f'    {k!r}: {v}')
    for v in ('Llaima', 'Copahue'):
        if samples[v]:
            print(f'  sample {v}:')
            for s in samples[v]:
                print(f'    {dict(s)}')
