"""83 — Análisis FPs curados OSF v2.5 en Llaima (Bloque F S37).

Pregunta operacional: los 411 records class=0 (FPs curados por MIROVA)
en Llaima Tier A — ¿son geográficos (Lago Conguillío ~10km NE, otros
features) o temporales (estación cálida, contaminación solar diurna)?

Implicación: si la concentración geográfica es alta y consistente con
features hidrológicos, REVALIDA los `exclude_zones` que removimos en
S27 al adoptar "clon literal MIROVA". MIROVA NO tiene exclude_zones —
pero curate post-hoc, marcando estos pixels como class=0. Nuestro
pipeline NRT no puede curar post-hoc; el filtro geográfico apriori es
el sustituto operacional.

Salida:
- stdout: tablas distancia, bearing, mes, sensor, top clusters
- reports/llaima_fp_analysis.md: conclusión accionable
"""
import csv, sys, io, math
from datetime import datetime
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

REPO = Path(__file__).resolve().parent.parent
OSF = REPO / 'reports' / 'osf_v25_tier_a.csv'
OUT_MD = REPO / 'reports' / 'llaima_fp_analysis.md'

# Llaima vent (volcanoes.yaml)
VENT_LAT, VENT_LON = -38.692, -71.729
LLAIMA_IDVOLC = '357110'

# Bearing sectors (degrees CW from N)
SECTORS = [('N', 348.75, 11.25), ('NNE', 11.25, 33.75), ('NE', 33.75, 56.25),
           ('ENE', 56.25, 78.75), ('E', 78.75, 101.25), ('ESE', 101.25, 123.75),
           ('SE', 123.75, 146.25), ('SSE', 146.25, 168.75), ('S', 168.75, 191.25),
           ('SSW', 191.25, 213.75), ('SW', 213.75, 236.25), ('WSW', 236.25, 258.75),
           ('W', 258.75, 281.25), ('WNW', 281.25, 303.75), ('NW', 303.75, 326.25),
           ('NNW', 326.25, 348.75)]


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat/2)**2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2)
    return 2 * R * math.asin(math.sqrt(a))


def bearing_deg(lat1, lon1, lat2, lon2):
    """Forward bearing from (lat1,lon1) to (lat2,lon2), 0=N CW."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dlon = math.radians(lon2 - lon1)
    y = math.sin(dlon) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dlon)
    brng = math.degrees(math.atan2(y, x))
    return (brng + 360) % 360


def sector(b):
    for name, lo, hi in SECTORS:
        if name == 'N':
            if b >= lo or b < hi: return name
        elif lo <= b < hi:
            return name
    return '?'


def sensor_label(sat, res):
    sat, res = str(sat).strip(), str(res).strip()
    if sat in ('1', '2'): return 'MODIS'
    if res == '375': return 'VIIRS375'
    return 'VIIRS750'


def main():
    if not OSF.exists():
        sys.exit(f'ERROR: {OSF} missing — run experiments/82_osf_v25_audit.py first.')

    fps = []
    real = []
    with open(OSF, encoding='utf-8') as f:
        for r in csv.DictReader(f):
            if r['IDvolc'].strip() != LLAIMA_IDVOLC:
                continue
            cls = r.get('class', '').strip()
            try:
                lat = float(r['LAT'])
                lon = float(r['LON'])
            except (KeyError, ValueError):
                continue
            try:
                ts = datetime.strptime(r['timeUTC'], '%d/%m/%Y %H:%M')
            except ValueError:
                continue
            dist = haversine_km(VENT_LAT, VENT_LON, lat, lon)
            brng = bearing_deg(VENT_LAT, VENT_LON, lat, lon)
            entry = {
                'ts': ts, 'lat': lat, 'lon': lon, 'dist_km': dist,
                'bearing': brng, 'sector': sector(brng),
                'sensor': sensor_label(r['Satellite'], r['Resolution']),
                'vrp': float(r.get('VRP', 0) or 0),
                'dayflag': r.get('Dayflag', '').strip(),
            }
            if cls == '0':
                fps.append(entry)
            elif cls == '1':
                real.append(entry)

    print(f'Llaima OSF Tier A: {len(fps)} class=0 (curated FPs) + {len(real)} class=1 (detections)')
    print(f'Vent reference: ({VENT_LAT}, {VENT_LON})')
    print()

    # 1. Distance histogram (1 km buckets, up to 30 km)
    print('=== Distance from vent — class=0 vs class=1 ===')
    print(f'{"dist_km":<10} {"class=0 (FP)":>14} {"class=1 (real)":>16} {"FP/Real ratio":>14}')
    print('-' * 56)
    bins = list(range(0, 31))
    fp_bins = Counter(min(int(e['dist_km']), 30) for e in fps)
    real_bins = Counter(min(int(e['dist_km']), 30) for e in real)
    for b in bins:
        f = fp_bins.get(b, 0)
        r = real_bins.get(b, 0)
        if f == 0 and r == 0:
            continue
        ratio = f'{f/r:.2f}' if r > 0 else ('∞' if f > 0 else '—')
        print(f'{b}-{b+1:<6} {f:>14} {r:>16} {ratio:>14}')

    # 2. Bearing sector distribution (FPs only)
    print()
    print('=== Bearing sector distribution (class=0 FPs only) ===')
    sec_count = Counter(e['sector'] for e in fps)
    total = sum(sec_count.values())
    for name, _, _ in SECTORS:
        c = sec_count.get(name, 0)
        pct = 100 * c / total if total else 0
        bar = '█' * int(pct / 2)
        print(f'  {name:<4} {c:>4}  {pct:>5.1f}%  {bar}')

    # 3. Top geographic clusters (round lat/lon to 0.05° = ~5km grid)
    print()
    print('=== Top FP geographic clusters (0.05° grid = ~5 km) ===')
    grid = Counter((round(e['lat'] / 0.05) * 0.05, round(e['lon'] / 0.05) * 0.05) for e in fps)
    print(f'{"lat":>9} {"lon":>9} {"n_FPs":>7} {"dist_vent":>10} {"sector":>8} {"sensor_top":>15}')
    print('-' * 75)
    top_clusters = []
    for (glat, glon), n in grid.most_common(15):
        d = haversine_km(VENT_LAT, VENT_LON, glat, glon)
        b = bearing_deg(VENT_LAT, VENT_LON, glat, glon)
        sec_cell = sector(b)
        sens_in_cell = Counter(
            e['sensor'] for e in fps
            if round(e['lat']/0.05)*0.05 == glat and round(e['lon']/0.05)*0.05 == glon
        )
        sens_top = sens_in_cell.most_common(1)[0] if sens_in_cell else ('—', 0)
        print(f'{glat:>9.3f} {glon:>9.3f} {n:>7} {d:>9.1f}km {sec_cell:>8} {sens_top[0]:>10}={sens_top[1]:<3}')
        top_clusters.append({'lat': glat, 'lon': glon, 'n': n, 'dist': d, 'sector': sec_cell})

    # 4. Monthly distribution (seasonality)
    print()
    print('=== Monthly distribution (class=0 FPs) ===')
    months = Counter(e['ts'].month for e in fps)
    real_months = Counter(e['ts'].month for e in real)
    print(f'{"month":<6} {"FP":>5} {"Real":>5} {"FP/(FP+Real)":>13}')
    for m in range(1, 13):
        f = months.get(m, 0)
        r = real_months.get(m, 0)
        tot = f + r
        pct = 100 * f / tot if tot else 0
        print(f'  {m:<4} {f:>5} {r:>5}  {pct:>11.1f}%')

    # 5. Sensor distribution
    print()
    print('=== Sensor distribution (FPs vs Real) ===')
    fp_sens = Counter(e['sensor'] for e in fps)
    real_sens = Counter(e['sensor'] for e in real)
    for s in ['MODIS', 'VIIRS750', 'VIIRS375']:
        f = fp_sens.get(s, 0)
        r = real_sens.get(s, 0)
        tot = f + r
        pct = 100 * f / tot if tot else 0
        print(f'  {s:<10} FP={f:>5} Real={r:>5}  FP/(FP+Real)={pct:>5.1f}%')

    # 6. Day/night
    print()
    print('=== Day/night distribution (FPs) ===')
    df = Counter(e['dayflag'] for e in fps)
    for k, v in df.most_common():
        print(f'  dayflag={k!r}: {v}')

    # Conclusion heuristics
    print()
    print('=== Heurística operacional ===')
    # Top cluster outside inner_radius (5 km)
    far_clusters = [c for c in top_clusters if c['dist'] > 5.0]
    near_clusters = [c for c in top_clusters if c['dist'] <= 5.0]
    n_far = sum(c['n'] for c in far_clusters)
    n_near = sum(c['n'] for c in near_clusters)
    pct_far = 100 * n_far / max(n_far + n_near, 1)
    print(f'  FPs en top-15 clusters: {n_far + n_near} '
          f'(de {len(fps)} totales = {100*(n_far+n_near)/len(fps):.0f}%)')
    print(f'  De top-15 clusters: {n_far} ({pct_far:.0f}%) están fuera de inner_radius=5km')
    if far_clusters:
        print(f'  Top FAR cluster (>5km): ({far_clusters[0]["lat"]:.3f}, {far_clusters[0]["lon"]:.3f}) '
              f'sector={far_clusters[0]["sector"]} dist={far_clusters[0]["dist"]:.1f}km n={far_clusters[0]["n"]}')

    # Estimar NE concentration (Conguillío hypothesis)
    ne_sectors = {'N', 'NNE', 'NE', 'ENE'}
    ne_fps = sum(1 for e in fps if e['sector'] in ne_sectors)
    pct_ne = 100 * ne_fps / len(fps)
    print(f'  FPs en sectores N/NNE/NE/ENE (hipótesis Conguillío): {ne_fps} ({pct_ne:.1f}%)')

    # Write summary markdown
    OUT_MD.parent.mkdir(exist_ok=True)
    with open(OUT_MD, 'w', encoding='utf-8') as f:
        f.write('# Análisis FPs curados OSF v2.5 — Llaima\n\n')
        f.write(f'Generado por `experiments/83_llaima_fp_analysis.py` desde `reports/osf_v25_tier_a.csv`.\n\n')
        f.write(f'## Resumen\n\n')
        f.write(f'- **{len(fps)}** records class=0 (FPs curados por MIROVA)\n')
        f.write(f'- **{len(real)}** records class=1 (detecciones reales)\n')
        f.write(f'- Vent referencia: ({VENT_LAT}, {VENT_LON})\n')
        f.write(f'- FP rate global: {100*len(fps)/(len(fps)+len(real)):.1f}% '
                f'({len(fps)}/{len(fps)+len(real)})\n\n')
        f.write(f'## Concentración geográfica\n\n')
        f.write(f'Top-15 clusters (grid 0.05° = ~5km) acumulan '
                f'{100*(n_far+n_near)/max(len(fps),1):.0f}% de los FPs.\n\n')
        f.write(f'**Hipótesis Conguillío (sectores N/NNE/NE/ENE)**: '
                f'{ne_fps} FPs = {pct_ne:.1f}% del total class=0.\n\n')
        f.write(f'| lat | lon | n_FPs | dist_vent | sector |\n|---|---|---|---|---|\n')
        for c in top_clusters[:10]:
            f.write(f'| {c["lat"]:.3f} | {c["lon"]:.3f} | {c["n"]} | {c["dist"]:.1f}km | {c["sector"]} |\n')
        f.write('\n## Conclusión operacional (preliminar)\n\n')
        if pct_ne >= 40:
            f.write(f'- **Geográfico-dominante** ({pct_ne:.1f}% en sectores NE). Consistente con '
                    f'hipótesis Lago Conguillío. Justifica reintroducir `exclude_zones` '
                    f'para la cuenca lacustre en perfil operacional (revertir parche '
                    f'removido en S27).\n')
        elif pct_ne >= 20:
            f.write(f'- **Mixto**: NE acumula {pct_ne:.1f}% pero hay dispersión adicional. '
                    f'`exclude_zones` ayuda pero no es suficiente — combinar con filtros físicos.\n')
        else:
            f.write(f'- **NO dominante NE** ({pct_ne:.1f}%). Los FPs están distribuidos. '
                    f'`exclude_zones` Conguillío tendría impacto bajo. Revisar otros features '
                    f'o causas temporales.\n')
        f.write('\nVer stdout para tablas completas distancia / bearing / mes / sensor.\n')

    print(f'\nWrote {OUT_MD}')


if __name__ == '__main__':
    main()
