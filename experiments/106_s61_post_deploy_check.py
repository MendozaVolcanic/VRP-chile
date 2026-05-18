"""S61 Post-deploy verification — Villarrica + PlanchonPeteroa.

Compara los ultimos 10 records de cada vol contra magnitudes esperadas
post-adopcion (Task 7 plan S61).

Pre-condicion: cron NRT post-merge Task 5 ya corrio al menos 1 vez.

Uso:
  # IMPORTANTE: pull main es REQUIRED -- el worktree no recibe commits NRT
  git pull --rebase origin main
  python experiments/106_s61_post_deploy_check.py

Notas:
  - El cron NRT corre cada 2h. Latest record max 2-4h ago si todo OK.
  - El cron NRT tiene 93% success rate (3/45 vols fallan por NASA timeout
    intermitente en cada run, fix H7/H7b PR #2+#44). Si Villarrica/PP
    fallan en un run especifico, el siguiente en 2h los recupera.
"""
import io
import json
import statistics
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Force utf-8 stdout for Windows cp1252 (CLAUDE.md regla Windows encoding)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


VOLS = ['Villarrica', 'PlanchonPeteroa']
LOOKBACK_RECORDS = 10
EXPECTED_MAX_VRP_SUMMIT = {
    # Vol -> max VRP MW summit razonable post-fix (sanity check)
    'Villarrica': 10.0,  # 5 ALERTAS audit C: max ratio 3.17x sobre MIROVA 0.31 → ~1 MW
    'PlanchonPeteroa': 5.0,  # max esperado fix sub-1 MW MIROVA, fix curado a ~2-3 MW
}


def sensor_family(s):
    if 'MODIS' in s:
        return 'MODIS'
    if '750' in s:
        return 'VIIRS750'
    if 'VIIRS' in s:
        return 'VIIRS375'
    return s


def check_vol(vol):
    path = Path(f'data/mirova_equivalent/{vol}.json')
    if not path.exists():
        print(f'  ❌ {vol}: JSON no existe en data/mirova_equivalent/')
        return False

    with open(path, encoding='utf-8') as f:
        recs = json.load(f).get('records', [])

    # Últimos 10 records anómalos
    anom = [r for r in recs if (r.get('vrp_mw') or 0) > 0]
    if not anom:
        print(f'  ⚠️  {vol}: 0 records anómalos en todo el histórico')
        return False

    anom_sorted = sorted(anom, key=lambda r: r.get('datetime_utc', ''), reverse=True)
    recent = anom_sorted[:LOOKBACK_RECORDS]

    # Fecha del más reciente vs hoy
    latest_dt = datetime.fromisoformat(recent[0]['datetime_utc'].replace('Z', ''))
    age_hours = (datetime.utcnow() - latest_dt).total_seconds() / 3600

    print(f'\n  === {vol} ===')
    print(f'  Latest record: {recent[0]["datetime_utc"][:19]} ({age_hours:.1f}h ago)')

    # Last 10 records summary
    summit = [r for r in recent if (r.get('final_hotspot_dist_km') or 99) <= 5]
    vrps_summit = [r['vrp_mw'] for r in summit]
    print(f'  Últimos {len(recent)} anom records: summit={len(summit)}, far={len(recent)-len(summit)}')
    if vrps_summit:
        print(f'  Summit VRPs: min={min(vrps_summit):.2f}  median={statistics.median(vrps_summit):.2f}  max={max(vrps_summit):.2f}')

    # Sanity checks
    issues = []
    if age_hours > 8:
        issues.append(f'⚠️  Latest record es de hace {age_hours:.1f}h. Cron NRT puede estar fallando.')
    max_expected = EXPECTED_MAX_VRP_SUMMIT[vol]
    outliers = [r for r in summit if r['vrp_mw'] > max_expected]
    if outliers:
        issues.append(f'⚠️  {len(outliers)} summit records sobre {max_expected} MW (esperado max).')
        for o in outliers[:3]:
            print(f'    {o["datetime_utc"][:19]} {o["sensor"]:15} vrp={o["vrp_mw"]:.2f} dist={o.get("final_hotspot_dist_km", 99):.2f}')
    zero_vrp_count = sum(1 for r in recent if r['vrp_mw'] == 0)
    if zero_vrp_count > 7:
        issues.append(f'⚠️  {zero_vrp_count}/{LOOKBACK_RECORDS} últimos records con vrp=0. Posible regresión por fix demasiado agresivo.')

    if issues:
        for i in issues:
            print(f'  {i}')
        return False
    print(f'  ✅ {vol} verificación OK')
    return True


def main():
    print(f'S61 Post-deploy verification — {datetime.utcnow().isoformat(timespec="seconds")}Z UTC')
    print('=' * 60)
    results = {}
    for vol in VOLS:
        results[vol] = check_vol(vol)

    print('\n=== Verdict ===')
    if all(results.values()):
        print('✅ Adopción estable. Cron NRT procesa OK con fix kernel-bg.')
    else:
        failures = [v for v, ok in results.items() if not ok]
        print(f'⚠️  Issues detectados en: {", ".join(failures)}. Revisar manualmente.')


if __name__ == '__main__':
    main()
