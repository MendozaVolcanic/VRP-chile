"""88 — R2 validación 5 casos vent_anchored vs disabled (S38 Bloque B).

Para cada caso D8 representativo, compara record vent_anchored vs disabled
con foco en:
- primary_cluster: vrp_mw, dist (cambió de equivocado a correcto?)
- anomaly_pixels: pixels filtrados por H8 (in_range vs out_range)
- diag fields: paths que dispararon (bt/nti/dnti_ctx/test1)
- Si TIF MIROVA disponible en mirova-tif-archive: confirmar pixel-level

5 casos seleccionados para máxima información:
1. Lascar MODIS  — caso D8 más claro (Salar→cráter)
2. PuyehueCordonCaulle VIIRS — caso D8 con inner_radius_km=20 atípico
3. Tupungatito VIIRS — control negativo (combo regresiona, vent solo +0 TP)
4. Isluga VIIRS — +2 TP en A/B, mecanismo no investigado
5. Lastarria VIIRS — geotermal fumarolas, +1 TP A/B
"""
import sys, io, json
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

REPO = Path(__file__).resolve().parent.parent


def find_record(profile, vol, dt_prefix, sensor_substring):
    """Find first record matching prefix + sensor."""
    p = REPO / 'data' / profile / f'{vol}.json'
    if not p.exists():
        return None
    with open(p) as f:
        data = json.load(f)
    recs = data if isinstance(data, list) else data['records']
    for r in recs:
        dt = r.get('datetime_utc', '')
        s = r.get('sensor', '')
        if dt.startswith(dt_prefix) and sensor_substring in s:
            return r
    return None


def diff_record(label, vol, dt_prefix, sensor):
    """Compare disabled vs vent_anchored for one record."""
    rd = find_record('_d8_vent_anchored_disabled', vol, dt_prefix, sensor)
    rv = find_record('_d8_vent_anchored', vol, dt_prefix, sensor)
    print(f'=== {label} ===')
    print(f'    vol={vol}  dt={dt_prefix}  sensor={sensor}')
    if not rd:
        print('    [disabled record NOT FOUND]')
        return
    if not rv:
        print('    [vent_anchored record NOT FOUND]')
        return
    pcd = rd.get('primary_cluster') or {}
    pcv = rv.get('primary_cluster') or {}
    print(f'    disabled:')
    print(f'      vrp_mw={rd.get("vrp_mw")} hotspot_dist={rd.get("hotspot_dist_km")}km '
          f'n_anom={rd.get("n_anomalous_pixels")}')
    print(f'      primary[vrp={pcd.get("vrp_mw")} dist={pcd.get("centroid_dist_km")}km '
          f'n_pix={pcd.get("n_pixels")}]')
    print(f'      n_clusters_total={rd.get("n_hotspots_clustered")}')
    print(f'      discarded_reason={rd.get("discarded_reason")}')
    print(f'    vent_anchored:')
    print(f'      vrp_mw={rv.get("vrp_mw")} hotspot_dist={rv.get("hotspot_dist_km")}km '
          f'n_anom={rv.get("n_anomalous_pixels")}')
    print(f'      primary[vrp={pcv.get("vrp_mw")} dist={pcv.get("centroid_dist_km")}km '
          f'n_pix={pcv.get("n_pixels")}]')
    print(f'      n_clusters_total={rv.get("n_hotspots_clustered")}')
    print(f'      discarded_reason={rv.get("discarded_reason")}')

    # Diff
    vrp_d = rd.get('vrp_mw', 0) or 0
    vrp_v = rv.get('vrp_mw', 0) or 0
    if vrp_d == 0 and vrp_v > 0:
        verdict = '✅ FN→TP (vent_anchored rescató detección)'
    elif vrp_d > 0 and vrp_v == 0:
        verdict = '❌ TP→FN (REGRESIÓN)'
    elif vrp_d > 0 and vrp_v > 0:
        if pcv.get('centroid_dist_km', 99) < pcd.get('centroid_dist_km', 0) - 3:
            verdict = '✅ Primary cluster moved closer to vent'
        else:
            verdict = '○ Same TP, primary similar'
    else:
        verdict = '○ Both FN'
    print(f'    Veredicto: {verdict}')
    print()


def main():
    # 5 casos representativos. Datetime + sensor elegidos de logs S38.
    cases = [
        # Lascar MODIS Salar->crater (FN→TP en vent_anchored, ratio Salar 25km)
        ('CASE 1 - Lascar MODIS Salar→cráter (S38 case)',
         'Lascar', '2026-05-06 02:05', 'MODIS_TERRA'),

        # Puyehue lacolito caso canónico
        ('CASE 2 - Puyehue VIIRS lacolito (inner=20km)',
         'PuyehueCordonCaulle', '2026-05-09 05:42', 'VIIRS_NOAA21_750'),

        # Tupungatito vent_anchored TP (control - el caso que combo regresionaría)
        ('CASE 3 - Tupungatito VIIRS (control vs combo)',
         'Tupungatito', '2026-05-10 05:24', 'VIIRS_NOAA21'),

        # Isluga +2 TP A/B (mecanismo no investigado)
        ('CASE 4 - Isluga VIIRS (+2 TP A/B unexplored)',
         'Isluga', '2026-05-01', 'VIIRS'),  # broad sensor match

        # Lastarria geotermal (+1 TP A/B)
        ('CASE 5 - Lastarria VIIRS geotermal fumaroles',
         'Lastarria', '2026-05-03', 'VIIRS'),
    ]
    for (label, vol, dt, sens) in cases:
        diff_record(label, vol, dt, sens)


if __name__ == '__main__':
    main()
