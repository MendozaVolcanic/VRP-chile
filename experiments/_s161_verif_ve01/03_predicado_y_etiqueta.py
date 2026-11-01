"""VE01-V: (1) el predicado del tablero (frontend/index.html, ejecutado con node via banco_paridad.correr_node, A97)
sobre los records de Tupungatito del 2026-09-29 entre 04 y 07 UTC; (2) mutaciones del record de las 04:54 para
atribuir la causa (distance_class far->summit; inner 7->10 km); (3) etiqueta que le pone banco_paridad a esa pasada
con la referencia de hoy (snapshot del repo, regla SN y original); (4) la misma etiqueta si la fila OCR llevara la
distancia que el propio scraper le pone a la serie (Distancia_aprox_max 9,59) y su regla limite_km = 7.
P1: control de identidad del predicado (banco_paridad.control_identidad_predicado) debe dar [0,1,1,1,0] y [1,0].
P2: control positivo: la mutacion summit debe cambiar la columna publica; si no cambia, el predicado no ve la clase."""
import sys, copy, json, io
sys.path.insert(0, 'scripts')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import banco_paridad as bp
print('control identidad predicado:', bp.control_identidad_predicado())
print('inner desde html:', {k: v for k, v in bp.inner_desde_html().items() if 'upung' in k})
recs = json.load(open('data/mirova_equivalent/Tupungatito.json', encoding='utf-8'))['records']
sel = [r for r in recs if '2026-09-29 04' <= r['datetime_utc'] <= '2026-09-29 07']
casos = [[r, 7.0] for r in sel]
r0454 = next(r for r in sel if r['datetime_utc'] == '2026-09-29 04:54' and r['sensor'] == 'VIIRS_SNPP')
m1 = copy.deepcopy(r0454); m1['distance_class'] = 'summit'; m1['primary_cluster']['geo_class'] = 'summit'
casos += [[m1, 7.0], [copy.deepcopy(r0454), 10.0], [m1, 10.0]]
res = bp.correr_node(casos)
print('columnas: [summit, valid, artefacto, display_vrp, PUBLICA]')
for (r, inner), o in zip(casos, res):
    tag = ''
    if r is m1: tag = ' <- MUTACION distance_class=summit'
    elif r is not r0454 and r['datetime_utc'] == '2026-09-29 04:54' and r['sensor'] == 'VIIRS_SNPP': tag = ' <- copia sin mutar'
    print(f"  {r['datetime_utc']} {r['sensor']:18s} inner {inner:4.1f} dc={r.get('distance_class')}: {o}{tag}")
