"""VE01-V: etiqueta de la pasada 2026-09-29 04:54 VIIRS375 de Tupungatito con el banco de paridad (snapshot del repo,
regla original y SN), y la misma etiqueta si la fila OCR llevara la distancia de la serie (9,59 km, Distancia_aprox_max)
con la regla del scraper (dist > limite_km = 7 -> FALSO_POSITIVO_OCR; Mirova-v1 volcanes.py l. 37-38, scraper.py l. 144-152
segun docs/audit_s139/EJE_1 l. 41-42). Ademas lista las alertas protegidas (>= 1 MW, nocturnas) de Tupungatito en toda la
referencia, con su distancia y canal, para ver si VE-01 es la unica.
P1: si el banco no viera la fila, la pasada saldria sin_info; se imprime la fila pareada.
P2: control: la pasada 05:18 NOAA-20 (fila CONS ALERTA 0,04 MW) debe salir pos."""
import sys, io, copy
sys.path.insert(0, 'scripts'); sys.path.insert(0, '.')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import banco_paridad as bp
coords = bp._coords_por_volcan(); inner = bp.inner_desde_html()
filas = bp.cargar_referencia_unificada(bp.SNAP_CONS, bp.SNAP_OCR)
print('sha cons', bp.sha_git(bp.SNAP_CONS), 'sha ocr', bp.sha_git(bp.SNAP_OCR))
ven = ('2026-09-29', '2026-09-29')
tup = [f for f in filas if f['volcano'] == 'Tupungatito' and f['fecha_utc'][:10] == '2026-09-29']
for f in tup:
    if f['sensor_bucket'] == 'VIIRS375': print('  ref', {k: f.get(k) for k in ('fecha_utc', 'sensor_bucket', 'tipo', 'vrp_mw', 'dist_km', 'source')})
def correr(filas_, regla):
    por_vb, ns, nv, n = bp.indexar_referencia(filas_, coords, ven, regla_minimas=regla)
    recs = [r for r in bp.cargar_nuestros(coords, inner, ven) if r['vol'] == 'Tupungatito']
    bp.etiquetar(recs, por_vb, ns, nv)
    for r in recs:
        if r['b'] == 'VIIRS375':
            print(f"   {regla:8s} {r['dt']} {r['b']} lab={r['lab']} dist_ref={r['dist_ref']} " + ' '.join(f'{k}={r.get(k)}' for k in ('pub', 'publica', 'summit') if k in r))
for regla in ('original', 'SN'):
    print('referencia tal cual, regla', regla); correr(filas, regla)
mod = copy.deepcopy(filas)
for f in mod:
    if f['volcano'] == 'Tupungatito' and f['fecha_utc'].startswith('2026-09-29 04:54') and f['source'] != 'CONS':
        f['tipo'] = 'FALSO_POSITIVO_OCR'; f['dist_km'] = 9.59
print('referencia con la fila 04:54 a 9,59 km (regla del scraper -> FALSO_POSITIVO_OCR)'); correr(mod, 'SN')
print('\nalertas nocturnas >= 1 MW de Tupungatito en toda la referencia del snapshot:')
for f in sorted(filas, key=lambda x: x['fecha_utc']):
    if f['volcano'] == 'Tupungatito' and bp.es_alerta(f['tipo']) and (f['vrp_mw'] or 0) >= 1.0:
        print('  ', {k: f.get(k) for k in ('fecha_utc', 'sensor_bucket', 'tipo', 'vrp_mw', 'dist_km', 'source')})
