import csv, sys, io
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

path = r'C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\data\mirova_reference\VRP_GLOBAL_ARCHIVE_2025.csv'

target_names = {'Láscar','Isluga','Lastarria','Chillán, Nevados de','Llaima','Villarrica',
                 'Chaitén','Planchón-Peteroa','Puyehue-Cordón Caulle','Copahue','Tupungatito'}

rows_by_name = defaultdict(list)
date_min_max = [None, None]
with open(path, encoding='utf-8', errors='replace') as f:
    reader = csv.DictReader(f)
    for r in reader:
        vn = r['Volc_Name']
        t = r['timeUTC']
        if date_min_max[0] is None or t < date_min_max[0]:
            date_min_max[0] = t
        if date_min_max[1] is None or t > date_min_max[1]:
            date_min_max[1] = t
        if vn in target_names:
            rows_by_name[vn].append(r)

print("Rango completo de timeUTC en archivo:", date_min_max)
print()

for vn, rows in rows_by_name.items():
    n = len(rows)
    # year distribution
    years = defaultdict(int)
    vrps_pos_by_year = defaultdict(list)
    class_by_year = defaultdict(lambda: defaultdict(int))
    for r in rows:
        t = r['timeUTC']
        # format dd/mm/yyyy hh:mm
        try:
            datepart = t.split(' ')[0]
            d,m,y = datepart.split('/')
        except Exception:
            y = '????'
        years[y] += 1
        try:
            vrp = float(r['VRP'])
        except (ValueError, TypeError):
            vrp = None
        if vrp is not None and vrp > 0:
            vrps_pos_by_year[y].append(vrp)
        cls = r['class']
        class_by_year[y][cls] += 1
    print(f"=== {vn} (n={n}) ===")
    for y in sorted(years):
        pos = vrps_pos_by_year[y]
        minv = min(pos) if pos else None
        maxv = max(pos) if pos else None
        med = sorted(pos)[len(pos)//2] if pos else None
        print(f"  {y}: n={years[y]:5d}  VRP>0 n={len(pos):5d}  min={minv}  median~={med}  max={maxv}  class_counts={dict(class_by_year[y])}")
    print()
