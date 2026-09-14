import csv, sys, io
from collections import defaultdict
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

path = r'C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\data\mirova_reference\VRP_GLOBAL_ARCHIVE_2025.csv'

target_names = {'Láscar','Isluga','Lastarria','Chillán, Nevados de','Llaima','Villarrica',
                 'Chaitén','Planchón-Peteroa','Puyehue-Cordón Caulle','Copahue'}

rows_by_name = defaultdict(list)
sat_by_year = defaultdict(lambda: defaultdict(int))
with open(path, encoding='utf-8', errors='replace') as f:
    reader = csv.DictReader(f)
    for r in reader:
        vn = r['Volc_Name']
        if vn not in target_names:
            continue
        t = r['timeUTC']
        try:
            dt = datetime.strptime(t, '%d/%m/%Y %H:%M')
        except Exception:
            continue
        rows_by_name[vn].append((dt, r))
        sat_by_year[dt.year][r.get('Satellite','?')] += 1

print("=== Ultima fecha por volcan en 2025, y conteo por mes 2025 ===")
for vn, rows in rows_by_name.items():
    rows2025 = [dt for dt, r in rows if dt.year == 2025]
    if not rows2025:
        print(vn, "sin datos 2025")
        continue
    rows2025.sort()
    by_month = defaultdict(int)
    for dt in rows2025:
        by_month[dt.month] += 1
    print(f"{vn}: n2025={len(rows2025)}  primera={rows2025[0]}  ultima={rows2025[-1]}  por_mes={dict(sorted(by_month.items()))}")

print()
print("=== Distribucion de Satellite code por año (todo el conjunto Chile Tier A combinado) ===")
for y in sorted(sat_by_year):
    print(y, dict(sat_by_year[y]))
