import csv, sys, io
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

path = r'C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\data\mirova_reference\VRP_GLOBAL_ARCHIVE_2025.csv'

# Tier A Chile volcanoes with nominal GVP coords (approx, from volcanoes.yaml region)
tier_a = {
    'Lascar': (-23.37, -67.73),
    'Isluga': (-19.15, -68.83),
    'Lastarria': (-25.17, -68.51),
    'Nevados de Chillan': (-36.86, -71.38),
    'Llaima': (-38.69, -71.73),
    'Villarrica': (-39.42, -71.93),
    'Chaiten': (-42.83, -72.65),
    'PlanchonPeteroa': (-35.24, -70.57),
    'Tupungatito': (-33.40, -69.85),
    'PuyehueCordonCaulle': (-40.59, -72.12),
    'Copahue': (-37.85, -71.17),
}

rows_by_name = defaultdict(list)
all_names = set()
with open(path, encoding='utf-8', errors='replace') as f:
    reader = csv.DictReader(f)
    for r in reader:
        try:
            lat = float(r['Volc_LAT'])
            lon = float(r['Volc_LON'])
        except (ValueError, TypeError):
            continue
        name = r['Volc_Name']
        all_names.add(name)
        for tname, (tlat, tlon) in tier_a.items():
            if abs(lat - tlat) < 0.15 and abs(lon - tlon) < 0.15:
                rows_by_name[tname].append(r)

print("=== Nombres encontrados por cercania de coordenadas ===")
for tname in tier_a:
    print(tname, len(rows_by_name[tname]))

print()
print("=== Nombres Volc_Name reales usados en OSF para estos matches ===")
for tname in tier_a:
    names_seen = set(r['Volc_Name'] for r in rows_by_name[tname])
    print(tname, '->', names_seen)

# Also search by name substring in Volc_Name for sanity
print()
print("=== Grep de nombres parecidos en Volc_Name completo ===")
keywords = ['Lascar','Isluga','Lastarria','Chillan','Llaima','Villarrica','Chaiten','Planchon','Peteroa','Tupungatito','Puyehue','Caulle','Copahue']
name_hits = defaultdict(int)
with open(path, encoding='utf-8', errors='replace') as f:
    reader = csv.DictReader(f)
    for r in reader:
        vn = r['Volc_Name']
        for kw in keywords:
            if kw.lower() in vn.lower():
                name_hits[vn] += 1
for k,v in sorted(name_hits.items()):
    print(k, v)
