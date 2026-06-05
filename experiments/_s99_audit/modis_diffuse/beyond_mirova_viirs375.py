"""S101 — Candidatos beyond-MIROVA (cat-b) en VIIRS375, cruce limpio (datos paper).

Cruce robusto (descarta falta de cobertura): días con MIROVA RUTINA VIIRS375 (MIROVA
PROCESÓ ese día-volcán y NO emitió alerta) donde NOSOTROS detectamos VIIRS375 al cráter
(distance_class summit o centroid<=inner, pc.vrp>0). Esos son FP nominales sólidos =
candidatos cat-b (feature real no publicada) o cat-d (artefacto). Reportar magnitud y
proximidad para distinguir.

MIROVA 'VIIRS375' en el CSV. Nuestro VIIRS375 = VIIRS_{SNPP,NOAA20,NOAA21} (no _750).
Fuente S91: este script. Output stdout + JSON.
"""
import json, csv, statistics
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
INNER = {'Lascar': 5, 'PuyehueCordonCaulle': 20, 'Tupungatito': 7, 'Chaiten': 5,
         'Villarrica': 5, 'Llaima': 5, 'PlanchonPeteroa': 3, 'Copahue': 4,
         'Isluga': 5, 'Lastarria': 3, 'NevadosDeChillan': 5}
namemap = {'PuyehueCordonCaulle': 'Puyehue-Cordon Caulle', 'NevadosDeChillan': 'Nevados de Chillan'}
rev = {v: k for k, v in namemap.items()}


def is_v375(s):
    s = (s or '').upper()
    return s.startswith('VIIRS') and not s.endswith('_750')


# MIROVA VIIRS375: días con RUTINA (procesó) y con ALERTA, por vol
mir_rutina = defaultdict(set)
mir_alerta = defaultdict(set)
for r in csv.DictReader(open(REPO / 'latest_consolidado.csv', encoding='utf-8')):
    if r['Sensor'] != 'VIIRS375':
        continue
    vol = rev.get(r['Volcan'], r['Volcan'])
    if vol not in INNER:
        continue
    day = r['Fecha_Satelite_UTC'][:10]
    if r['Tipo_Registro'] == 'RUTINA':
        mir_rutina[vol].add(day)
    elif r['Tipo_Registro'] == 'ALERTA_TERMICA':
        mir_alerta[vol].add(day)

print("=== Candidatos beyond-MIROVA VIIRS375 (nuestra det summit en día MIROVA-RUTINA) ===\n")
print(f"{'Volcan':<20}{'cand':>5}{'al cráter':>10}  magnitud cand (med/max MW)")
out = {}
tot = 0
for vol in INNER:
    p = REPO / 'data/mirova_equivalent' / f'{vol}.json'
    if not p.exists():
        continue
    o = json.load(open(p, encoding='utf-8'))
    inner = INNER[vol]
    cand, near_mags = [], []
    seen = set()
    for r in (o['records'] if isinstance(o, dict) else o):
        if not is_v375(r.get('sensor', '')):
            continue
        pc = r.get('primary_cluster') or {}
        v = pc.get('vrp_mw', 0) or 0
        if v <= 0:
            continue
        day = str(r.get('datetime_utc', ''))[:10]
        # MIROVA procesó (RUTINA) y NO alertó ese día
        if day in mir_rutina[vol] and day not in mir_alerta[vol]:
            cd = pc.get('centroid_dist_km')
            summit = (r.get('distance_class') == 'summit') or (cd is not None and cd <= inner)
            if summit and (vol, day) not in seen:
                seen.add((vol, day))
                cand.append((day, round(v, 2), round(cd, 1) if cd is not None else None))
                near_mags.append(v)
    tot += len(cand)
    mm = f"{statistics.median(near_mags):.2f}/{max(near_mags):.2f}" if near_mags else "-"
    print(f"{vol:<20}{len(cand):>5}{len(cand):>10}  {mm}")
    out[vol] = {'n_cand': len(cand), 'mag_med': round(statistics.median(near_mags), 2) if near_mags else None,
                'mag_max': round(max(near_mags), 2) if near_mags else None,
                'sample': sorted(cand, key=lambda x: -x[1])[:5]}

print(f"\nTOTAL candidatos beyond-MIROVA VIIRS375 (summit, día MIROVA-RUTINA): {tot}")
print("Nota: estos son FP nominales SÓLIDOS (MIROVA procesó sin alertar). Mezcla cat-b")
print("(feature real: lacolito/flanco/lava lake sub-MIROVA-threshold) + cat-d (artefacto).")
print("Distinguir requiere eje espacial (cráter/flanco vs disperso) + magnitud (A86).")
json.dump(out, open(Path(__file__).parent / 'beyond_mirova_viirs375_result.json', 'w', encoding='utf-8'),
          indent=2, ensure_ascii=False)
print("-> beyond_mirova_viirs375_result.json")
