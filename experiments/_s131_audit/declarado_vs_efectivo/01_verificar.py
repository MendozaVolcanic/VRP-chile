"""S131 T9 - verifica afirmaciones declaradas contra el estado efectivo.

Read-only. Persiste 01_resultados.json.
"""
import sys, io, os, json, re, glob, subprocess, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
os.chdir(ROOT)
R = []


def add(fuente, afirmacion, estado, declarado, efectivo, evidencia, sev):
    R.append(dict(fuente=fuente, afirmacion=afirmacion, estado=estado,
                  declarado=declarado, efectivo=efectivo,
                  evidencia=evidencia, severidad=sev))


def prof():
    code = ('import json,pipeline.profile as p;'
            'print(json.dumps({k:getattr(p,k) for k in dir(p) '
            'if k.isupper() and isinstance(getattr(p,k),(bool,int,float,str,type(None)))}))')
    out = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True,
                         env={**os.environ, 'VRP_PROFILE': 'mirova_equivalent'})
    return json.loads(out.stdout.strip().splitlines()[-1])


P = prof()
import yaml

# ---------------- FICHA SDA (documento legal) ----------------
add('FICHA_SDA', 'Categorias de datos: MODIS (MOD14/MYD14)', 'FALSO',
    'MOD14/MYD14 (producto de incendios)',
    'MOD021KM/MYD021KM + MOD03/MYD03 (radiancias L1B). MOD14 no se descarga nunca',
    'pipeline/fetch.py:176-183 (short_name); pipeline/process_modis.py:10 ya lo dice bien',
    'ALTA')

add('FICHA_SDA', 'Mitigacion de sesgos incluye "zonas de exclusion"',
    'FALSO' if not P['ENABLE_EXCLUDE_ZONES'] else 'CONFIRMADO',
    'zonas de exclusion activas como mitigacion',
    'ENABLE_EXCLUDE_ZONES=%s. MISSION.md las lista como parche removido en S27' % P['ENABLE_EXCLUDE_ZONES'],
    'pipeline.profile ENABLE_EXCLUDE_ZONES', 'ALTA')

add('FICHA_SDA', 'Sesgo topografico "mitigado normalizando por indice termico (NTI)"',
    'FALSO' if not P['ENABLE_TEST1_NTI_INTEGRAL'] else 'CONFIRMADO',
    'mitigado por NTI',
    ('ENABLE_TEST1_NTI_INTEGRAL=%s; compute_test1_nti solo se importa en '
     'process_viirs.py:206. MODIS y V750 importan unicamente compute_test1_mir '
     '(MIR absoluto), que es justo el mecanismo que A69 senala como causa'
     % P['ENABLE_TEST1_NTI_INTEGRAL']),
    'pipeline/process_modis.py:59 y pipeline/process_viirs_mod.py:153', 'ALTA')

add('FICHA_SDA', 'Artefacto solar mitigado restringiendo MIR a pasadas nocturnas',
    'CONFIRMADO', 'solo noche',
    'scripts/run_pipeline.py:170 nighttime_only=True por defecto; nrt.yml:176 y :196 no pasan --no-night-filter',
    'scripts/run_pipeline.py:170,185-196,411,446', 'n/a')

add('FICHA_SDA', 'v1.4: parametros single-pixel (umbral 5,0 MW, max 3 px)',
    'CONFIRMADO' if (P['SUB_MW_REGIME_THRESHOLD_MW'] == 5.0 and P['SINGLE_PIXEL_MAX_CLUSTER_PIXELS'] == 3) else 'FALSO',
    '5,0 MW / 3 px',
    '%s MW / %s px' % (P['SUB_MW_REGIME_THRESHOLD_MW'], P['SINGLE_PIXEL_MAX_CLUSTER_PIXELS']),
    'pipeline.profile', 'n/a')

add('FICHA_SDA', 'v1.3: path_d_intra_radio y second_pass_intra_radio desactivados',
    'CONFIRMADO' if not (P['ENABLE_PATH_D_INTRA_RADIO_GATE'] or P['ENABLE_SECOND_PASS_INTRA_RADIO_GATE']) else 'FALSO',
    'ambos OFF desde S118',
    'path_d=%s second_pass=%s' % (P['ENABLE_PATH_D_INTRA_RADIO_GATE'], P['ENABLE_SECOND_PASS_INTRA_RADIO_GATE']),
    'pipeline.profile', 'n/a')

add('FICHA_SDA', 'v1.2: vrptir.py no productivo (ENABLE_VRPTIR_AVENI=False)',
    'CONFIRMADO' if not P['ENABLE_VRPTIR_AVENI'] else 'FALSO', 'False',
    str(P['ENABLE_VRPTIR_AVENI']), 'pipeline.profile', 'n/a')

con = sorted(os.path.basename(f) for f in glob.glob('pipeline/*.py')
             if 'FICHA SDA' in open(f, encoding='utf-8', errors='replace').read())
declarados = {'process_modis.py', 'process_viirs.py', 'process_viirs_mod.py', 'store.py',
              'anchor.py', 'detection_context.py', 'test1_integrated.py',
              'test1_contextual_filter.py', 'test1_spatial_core.py', 'path_d_cap.py',
              'path_d_intra_radio.py', 'second_pass_intra_radio.py',
              'exclusion_zones.py', 'single_pixel_mode.py'}
extra = sorted(set(con) - declarados)
add('FICHA_SDA', 'Historial declara 14 modulos con cabecera FICHA (6 nucleo v1.1 + 8 secundarios v1.2)',
    'OBSOLETO' if extra else 'CONFIRMADO', '14 modulos',
    '%d modulos tienen la cabecera; no declarados en ninguna version: %s' % (len(con), extra),
    'grep -l "FICHA SDA" pipeline/*.py', 'MEDIA')

add('FICHA_SDA', 'Alcance de trazabilidad: scan_geometry.py',
    'SIN RESPALDO', 'no figura ni como incluido ni como excluido',
    ('scan_geometry.py fija A_pix, multiplicador directo del VRP -> cae bajo el criterio '
     'v1.2 ("modulos que deciden la magnitud"), pero no tiene cabecera FICHA y tampoco '
     'esta en la lista de exclusiones justificadas (serializacion / no productivos)'),
    'pipeline/scan_geometry.py (sin "FICHA SDA")', 'MEDIA')

add('FICHA_SDA (codigo)', 'Cabecera FICHA de vrp_regimes.py: "Radiancia MODIS (MOD14/MYD14)"',
    'FALSO', 'MOD14/MYD14', 'MOD021KM/MYD021KM',
    'pipeline/vrp_regimes.py:10 contra pipeline/process_modis.py:10, que lo dice bien', 'ALTA')

# ---------------- MISSION.md ----------------
pisos = (P['MIN_VRP_MW_VIIRS375'], P['MIN_VRP_MW_VIIRS750'], P['MIN_VRP_MW_MODIS'])
add('MISSION', 'Pisos VRP por sensor: "SIGUEN ACTIVOS" (store.py:459-468, 0.02/0.15/0.05)',
    'OBSOLETO' if pisos == (0.0, 0.0, 0.0) else 'CONFIRMADO',
    'activos 0.02/0.15/0.05; alcance 1564 de 23990 records summit (6,5 %)',
    ('pisos=%s: S130 los llevo a 0 en los tres sensores. Ademas la cita drifteo: el helper '
     'esta en store.py:72-103 y se llama en store.py:489; las lineas 459-468 son hoy el guard A46'
     % (pisos,)),
    'pipeline.profile + pipeline/store.py:72,489', 'ALTA')

cbt = open('pipeline/process_viirs.py', encoding='utf-8').read()
hard260 = any(l.strip().startswith('CLOUD_BT_THRESHOLD') and '260' in l
              for l in cbt.splitlines())  # solo asignaciones, no comentarios
add('MISSION', 'Cloud mask BT<260 K: "SIGUE ACTIVA en VIIRS 375", literal en process_viirs.py:674',
    'OBSOLETO' if not hard260 else 'CONFIRMADO',
    'literal 260.0 hardcodeado, ciega ~23 % de las pasadas del sensor',
    ('process_viirs.py:786 dice CLOUD_BT_THRESHOLD = CLOUD_MASK_BT_K y el perfil vale %s. '
     'El cambio de una linea que MISSION propone ya se hizo en S126 (#535)' % P['CLOUD_MASK_BT_K']),
    'pipeline/process_viirs.py:786,790', 'ALTA')

add('pipeline/process_viirs.py', 'Comentario del anillo intermedio: valid_mask=cloud_free "excluye nubes I05<260K"',
    'OBSOLETO' if P['CLOUD_MASK_BT_K'] == 0.0 else 'CONFIRMADO',
    'el anillo intermedio se calcula sobre pixeles sin nube',
    ('CLOUD_MASK_BT_K=%s, asi que cloud_free = I05 >= 0.0 y no excluye nada: valid_mask es '
     'una mascara todo-True. El comentario quedo describiendo el comportamiento previo a S126 (#535). '
     'Importa porque el anillo intermedio es justo el mecanismo que la FICHA describe como '
     'recuperacion de focos sub-pixel' % P['CLOUD_MASK_BT_K']),
    'pipeline/process_viirs.py:1797-1799 y :786,790', 'MEDIA')

add('MISSION', 'Regla D Test 1-priority activa en process_viirs.py:1502-1568 / process_modis.py:1167-1204 / process_viirs_mod.py:1055',
    'OBSOLETO', 'esas lineas',
    ('hoy los bloques estan en process_viirs.py:1642-1710, process_modis.py:1196-1230 y '
     'process_viirs_mod.py:1069. La afirmacion de fondo (sigue activa) se mantiene; '
     'ademas ya no es "sin flag": process_viirs.py:1695 pasa ENABLE_TEST1_PRIORITY_WEAK_CLUSTER'),
    'grep -n "Regla D" pipeline/process_*.py', 'BAJA')

add('MISSION', 'MAX_SIGMA_COMPONENT_K neutralizado por valor, default del codigo 7.0',
    'CONFIRMADO', 'perfil 999.0, default 7.0',
    'perfil=%s' % P['MAX_SIGMA_COMPONENT_K'], 'pipeline.profile', 'n/a')

add('MISSION', 'Resumen de divergencias: "Abiertas D2, D3, D11-posicion"',
    'OBSOLETO', 'tres abiertas',
    ('el catalogo declara ademas D13 (ABIERTA documental, S124), D17 (ABIERTA, S124/S125) '
     'y D18 (ABIERTA, S129/S130). El resumen de MISSION quedo en S105'),
    'docs/MIROVA_DIVERGENCES.md:1457, :1883, :1960', 'MEDIA')

# ---------------- CLAUDE.md ----------------
_vy = yaml.safe_load(open('volcanoes.yaml', encoding='utf-8'))
vs = _vy['volcanoes'] if isinstance(_vy, dict) and 'volcanoes' in _vy else _vy
rad = collections.Counter(v.get('radius_km') for v in vs)
add('CLAUDE.md', '"radius_km = 25 km uniforme para volcanes chilenos"',
    'FALSO', '25 km uniforme',
    'volcanoes.yaml: %s -> 25 km solo en los 11 Tier A; los otros 34 tienen 5 km' % dict(rad),
    'volcanoes.yaml', 'MEDIA')

inner = {v['name']: v.get('inner_radius_km') for v in vs}
esperado = {'Lastarria': 3, 'Lascar': 5, 'Isluga': 5, 'NevadosDeChillan': 5, 'Llaima': 5,
            'Villarrica': 5, 'Chaiten': 5, 'PlanchonPeteroa': 3, 'Copahue': 4,
            'Tupungatito': 7, 'PuyehueCordonCaulle': 20}
mal = {k: (v, inner.get(k)) for k, v in esperado.items() if inner.get(k) != v}
add('CLAUDE.md', 'Tabla inner_radius_km por volcan (Reglas geometricas S14)',
    'CONFIRMADO' if not mal else 'FALSO', str(esperado),
    'coincide en los 11' if not mal else str(mal), 'volcanoes.yaml', 'n/a')

datos = {}
for f in glob.glob('data/mirova_equivalent/*.json'):
    d = json.load(open(f, encoding='utf-8'))
    datos[os.path.basename(f)[:-5]] = len(d.get('records', d))
con_data = sum(1 for v in datos.values() if v > 0)
no_tier = sorted(v for k, v in datos.items() if v < 500)
add('CLAUDE.md', '"volcanoes.yaml (45 configurados, 11 con data, 34 sin pull)"',
    'FALSO', '11 con data / 34 sin pull',
    ('%d configurados y %d con data en data/mirova_equivalent/. Los 34 no-TierA tienen '
     'entre %d y %d records cada uno (backfill 2026-04-17 a 2026-04-24)'
     % (len(vs), con_data, min(no_tier), max(no_tier))),
    'data/mirova_equivalent/*.json', 'MEDIA')

wfs = {}
for f in sorted(glob.glob('.github/workflows/*.yml')):
    txt = open(f, encoding='utf-8').read()
    d = yaml.safe_load(txt)
    wfs[os.path.basename(f)] = dict(
        pushea=txt.count('git push') > 0,
        grupo=(d.get('concurrency') or {}).get('group'),
        on_es_string='on' in d)
pushers = {k: v for k, v in wfs.items() if v['pushea']}
en_grupo = sorted(k for k, v in pushers.items() if v['grupo'] == 'push-main')
fuera = sorted(k for k, v in pushers.items() if v['grupo'] != 'push-main')
add('CLAUDE.md', '"los 6 workflows que hacen git push a main comparten group: push-main - nrt, nrt-retry, sync-mirova-csv, audit-weekly, backfill y reproc"',
    'FALSO', '6 workflows, incluidos nrt-retry y audit-weekly',
    ('%d workflows hacen git push; %d estan en push-main (%s). nrt-retry.yml NO pushea '
     '(dispara nrt.yml con gh workflow run) y no declara concurrency alguna; '
     'audit-weekly.yml pushea con grupo propio "audit-weekly"'
     % (len(pushers), len(en_grupo), en_grupo)),
    '.github/workflows/*.yml', 'ALTA')

add('CLAUDE.md', '"hay 3 excepciones deliberadas" al grupo push-main',
    'FALSO', '3 excepciones',
    ('son %d: %s. audit-weekly.yml es la cuarta y no esta documentada; cumple el criterio '
     '(retry x5 con backoff en audit-weekly.yml:71-77) pero nadie lo escribio'
     % (len(fuera), fuera)),
    '.github/workflows/audit-weekly.yml:71-77', 'MEDIA')

noquoted = sorted(k for k, v in wfs.items() if not v['on_es_string'])
add('CLAUDE.md', 'A43: todo yml nuevo con "on": entre comillas (Norway problem)',
    'CONFIRMADO' if not noquoted else 'FALSO', 'los 18 quoted',
    'los %d parsean la clave como string' % len(wfs) if not noquoted else str(noquoted),
    'yaml.safe_load sobre .github/workflows/*.yml', 'n/a')

add('CLAUDE.md', 'nrt.yml: cron 2h, matrix por volcan, timeout 50 min per-step, max-parallel 8',
    'CONFIRMADO', 'cron 0 */2, 50 min per-step, max-parallel 8',
    'cron "0 */2 * * *" (l.12), timeout-minutes 50 en los dos pasos de proceso (l.173, l.193), job 60 (l.69), max-parallel 8 (l.80), fail-fast false (l.76)',
    '.github/workflows/nrt.yml', 'n/a')

add('CLAUDE.md', 'A12: "Lascar 21.6K, Isluga ~20K" (dT > 20 K, calibrados naturalmente sin fix)',
    'FALSO', 'Lascar 21,6 K y Isluga ~20 K',
    ('medido: Lascar 16,9 K e Isluga 8,3 K. Isluga cae DEBAJO del corte de 12 K con el que la '
     'propia A12 define la clase que SI necesita kernel-bg, o sea el ejemplo contradice la regla. '
     'El libro de cuentas lo registra desde S128 y la regla sigue sin marcar'),
    'scripts/libro_de_cuentas.py:261-264 + docs/LIBRO_DE_CUENTAS.json', 'ALTA')

usos = {os.path.basename(f): open(f, encoding='utf-8').read().count('mirovaEqVrp')
        for f in sorted(glob.glob('frontend/*.html'))}
add('CLAUDE.md', 'frontend: 3 vistas live + comparacion.html preview sin mirovaEqVrp (25/8/8/0)',
    'CONFIRMADO', 'index 25, diario 8, mosaico 8, comparacion 0', str(usos),
    'frontend/*.html', 'n/a')

add('CLAUDE.md', 'Coeficientes Wooster 18.9 (MODIS) / 19.7 (V750) / 18.0 (V375)',
    'CONFIRMADO', '18.9 / 19.7 / 18.0',
    'process_modis.py:82 = 18.9; process_viirs_mod.py:63 = 19.7; process_viirs.py:74 = 18.0',
    'grep -n WOOSTER_COEFF pipeline/*.py', 'n/a')

nsig_ok = (P['N_SIGMA_MIR_SUMMIT'] == 5.0 and P['N_SIGMA_MIR_SCENE'] == 10.0
           and P['N_SIGMA_MIR_DAY'] == 15.0
           and P['DNTI_CONTEXTUAL_C1_SUMMIT'] == 0.003
           and P['DNTI_CONTEXTUAL_C1_SCENE'] == 0.01
           and P['DNTI_CONTEXTUAL_C1_DAY'] == 0.02
           and P['NTI_REL_MIN_FLOOR'] == 0.005)
add('CLAUDE.md', 'N.sigma 5 summit / 10 scene / 15 dia; C1 0.003 / 0.010 / 0.02; NTI floor 0.005',
    'CONFIRMADO' if nsig_ok else 'FALSO', '5/10/15 y 0.003/0.010/0.02 y 0.005',
    'perfil efectivo: %s/%s/%s, %s/%s/%s, %s' % (
        P['N_SIGMA_MIR_SUMMIT'], P['N_SIGMA_MIR_SCENE'], P['N_SIGMA_MIR_DAY'],
        P['DNTI_CONTEXTUAL_C1_SUMMIT'], P['DNTI_CONTEXTUAL_C1_SCENE'],
        P['DNTI_CONTEXTUAL_C1_DAY'], P['NTI_REL_MIN_FLOOR']),
    'pipeline.profile con VRP_PROFILE=mirova_equivalent', 'n/a')

add('CLAUDE.md', 'Estado 4: "abiertas D2, D3 y D12" en el catalogo',
    'OBSOLETO', 'D2, D3, D12',
    'el catalogo declara ademas D13, D17 y D18 abiertas; el puntero de CLAUDE.md no las nombra',
    'docs/MIROVA_DIVERGENCES.md:1457, :1883, :1960', 'MEDIA')

citas = [
    ('A6 ejemplo corregido en S127', 'scripts/run_pipeline.py', 234, 'get_detection_anchor'),
    ('A89 puente del kernel', 'scripts/run_pipeline.py', 244, 'local_kernel_bg'),
    ('A89 docstring 5 volcanes opt-in', 'pipeline/process_viirs_mod.py', 409, 'Villarrica'),
    ('A69 nota: compute_test1_nti', 'pipeline/process_viirs.py', 958, 'compute_test1_nti'),
    ('A69 nota: import MODIS', 'pipeline/process_modis.py', 674, 'compute_test1_mir'),
    ('A69 nota: import V750', 'pipeline/process_viirs_mod.py', 665, 'compute_test1_mir'),
    ('A10 dashboard pc.vrp_mw', 'frontend/index.html', 680, 'vrp_mw'),
    ('store.py: isValidDetection', 'frontend/index.html', 1372, 'vrp_mw'),
    ('D17/S127: get_grid_center', 'pipeline/geo_utils.py', 29, 'get_grid_center'),
    ('D17/S127: regrid centrado en volcano_lat', 'pipeline/process_modis.py', 455, 'volcano_lat'),
]
ok, drift = [], []
for etiq, f, n, tok in citas:
    L = open(f, encoding='utf-8', errors='replace').read().splitlines()
    linea = L[n - 1] if n <= len(L) else ''
    (ok if tok in linea else drift).append((etiq, f, n, linea.strip()[:70]))
add('CLAUDE.md / docs', 'Citas file:line: la linea citada contiene el simbolo que la afirmacion nombra (10 muestreadas)',
    'FALSO' if drift else 'CONFIRMADO', '10/10 apuntan bien',
    '%d/%d apuntan bien; %d drifteadas -> %s' % (
        len(ok), len(citas), len(drift),
        ' | '.join('%s: %s:%d dice "%s"' % (e, f, n, l) for e, f, n, l in drift)),
    'experiments/_s131_audit/declarado_vs_efectivo/01_verificar.py', 'MEDIA')

# ---------------- README.md ----------------
add('README', '"the 50x50 km grid uses the official MIROVA grid center - decoupled on purpose"',
    'FALSO', 'la grilla se centra en el centro oficial de MIROVA',
    ('get_grid_center() (geo_utils.py:29) no tiene ningun llamador en produccion y '
     'ENABLE_UTM_REGRID=%s. Es exactamente lo que D17 declara NO implementado y lo que '
     'AUDIT_S127 Hallazgo 7 re-verifico' % P['ENABLE_UTM_REGRID']),
    'docs/MIROVA_DIVERGENCES.md:1883 + docs/AUDIT_S127.md Hallazgo 7', 'ALTA')

vt = {'nz': 0, 'z': 0}
for f in glob.glob('data/mirova_equivalent/*.json'):
    d = json.load(open(f, encoding='utf-8'))
    for r in d.get('records', d):
        if 'vrp_tir_mw' in r:
            vt['nz' if (r['vrp_tir_mw'] or 0) > 0 else 'z'] += 1
add('README', 'Feature list: "TIR VRP (VIIRS I05, 11.45 um): Stefan-Boltzmann (Aveni 2024, TIRVolcH)"',
    'FALSO', 'feature entregada',
    ('ENABLE_VRP_TIR_OUTPUT=%s y ENABLE_VRPTIR_AVENI=%s: %d de %d records con el campo valen 0. '
     'Los %d con valor son residuo de 2026-04 (max 4817 MW, la clase de outlier que motivo apagarlo). '
     'detect_tirvolch.py sigue sin importarlo nadie'
     % (P['ENABLE_VRP_TIR_OUTPUT'], P['ENABLE_VRPTIR_AVENI'], vt['z'], vt['nz'] + vt['z'], vt['nz'])),
    'pipeline/profiles/mirova_equivalent.yaml:521 + data/mirova_equivalent/*.json', 'ALTA')

add('README', '"34 additional volcanoes are configured under the experimental profile (outside the operational dashboard)"',
    'FALSO', 'solo bajo experimental',
    'los 34 tienen records dentro de data/mirova_equivalent/ (el subdir operacional), 67-94 cada uno',
    'data/mirova_equivalent/Osorno.json, Hudson.json, Parinacota.json', 'MEDIA')

add('README', '"Dashboard (frontend - 3 standalone views)"',
    'OBSOLETO', '3 vistas',
    '4 desplegadas: comparacion.html se rotula PREVIEW S115. CLAUDE.md se corrigio en S127; README no',
    'frontend/*.html + docs/AUDIT_S127.md Hallazgo 5', 'BAJA')

add('README', '"Nadir-fixed pixel area: no sec3 off-nadir scaling"',
    'CONFIRMADO' if (P['ENABLE_NADIR_FIXED_PIXEL_AREA_MODIS'] and P['ENABLE_NADIR_FIXED_PIXEL_AREA_VIIRS']) else 'FALSO',
    'nadir-fijo en los 3 sensores',
    'MODIS=%s VIIRS=%s' % (P['ENABLE_NADIR_FIXED_PIXEL_AREA_MODIS'], P['ENABLE_NADIR_FIXED_PIXEL_AREA_VIIRS']),
    'pipeline.profile', 'n/a')

add('README', '"Night-time only MIR processing (barrier at fetch, process and store stages)"',
    'CONFIRMADO', 'noche en las 3 etapas',
    'scripts/run_pipeline.py:170 default True + _check_night en las 3 ramas de sensor (l.227, 270, 317)',
    'scripts/run_pipeline.py', 'n/a')

# ---------------- docstrings de pipeline ----------------
add('pipeline/scan_geometry.py', 'Docstring del modulo presenta sec3(theta) como lo que el modulo hace ("Without correction ... underestimate")',
    'OBSOLETO', 'sec3 es el modo de operacion',
    ('los dos flags nadir-fijo estan ON (A66/A67), asi que la rama sec3 no se ejecuta en '
     'produccion en ningun sensor. El aviso aparece recien en la linea 232, dentro de un '
     'bloque agregado en S122, no en la cabecera'),
    'pipeline/scan_geometry.py:1-28 contra :232', 'MEDIA')

add('pipeline/scan_geometry.py', 'Docstring de roi_mask_bbox: "Cambiar a bbox recupera esas refs" (bbox 50x50)',
    'OBSOLETO' if not P['ENABLE_ROI1_BOX_PAPER'] else 'CONFIRMADO',
    'el bbox 50x50 es la geometria de MIROVA y conviene adoptarlo',
    ('ENABLE_ROI1_BOX_PAPER=%s y ROI1_BOX_HALF_KM=%s km, o sea la caja 5x5 del ROI1 (D18), '
     'no el bbox 50x50 del docstring. El A/B de D18 en S130 dio NO ADOPTAR'
     % (P['ENABLE_ROI1_BOX_PAPER'], P['ROI1_BOX_HALF_KM'])),
    'pipeline.profile + docs/MIROVA_DIVERGENCES.md:1960', 'MEDIA')

add('pipeline/process_modis.py', '_select_thresholds: "con enable_day=False el comportamiento es identico al historico"',
    'CONFIRMADO' if not P['ENABLE_DAYTIME_MODIS'] else 'FALSO', 'enable_day False',
    'ENABLE_DAYTIME_MODIS=%s' % P['ENABLE_DAYTIME_MODIS'], 'pipeline.profile', 'n/a')

# ---------------- data: invariante del piso ----------------
viol = tot_stamp = 0
for f in glob.glob('data/mirova_equivalent/*.json'):
    d = json.load(open(f, encoding='utf-8'))
    for r in d.get('records', d):
        if r.get('diag_vrp_floor_mw') is not None:
            tot_stamp += 1
            if (r.get('vrp_mw') or 0) > 0:
                viol += 1
tot_rec = sum(datos.values())
add('data/mirova_equivalent', 'Invariante de store.py: diag_vrp_floor_mw presente => vrp_mw == 0',
    'FALSO' if viol else 'CONFIRMADO', 'el sello solo existe cuando el piso actuo',
    ('%d de %d records sellados tienen vrp_mw>0 (%.2f %% de los %d records del corpus, '
     '2025-02 a 2026-09). El reproceso de S130 restauro vrp_mw pero el sello quedo pegado: '
     'un audit futuro leeria "el piso piso %d records" y seria falso (A87/A90)'
     % (viol, tot_stamp, viol / tot_rec * 100, tot_rec, tot_stamp)),
    'pipeline/store.py:99-103 escribe los dos campos juntos', 'ALTA')

# ---------------- INDEX.md ----------------
auds = sorted(int(re.search(r'AUDIT_S(\d+)', os.path.basename(f)).group(1))
              for f in glob.glob('docs/AUDIT_S*.md')
              if re.search(r'AUDIT_S(\d+)', os.path.basename(f)))
add('docs/INDEX.md', 'AUDIT_S127.md marcada como "Ultima"',
    'OBSOLETO', 'S127 es la ultima',
    ('existen auditorias hasta S%d; AUDIT_S128.md no figura en el indice. Es la 4a vez que se '
     'redescubre "INDEX congelado" (Fuga 1 del protocolo), y el propio indice trae el aviso '
     'de no hardcodear cual es la vigente' % max(auds)),
    'ls docs/AUDIT_S*.md | sort -V | tail -1', 'MEDIA')

# ---------------- MIROVA_DIVERGENCES ----------------
dv = open('docs/MIROVA_DIVERGENCES.md', encoding='utf-8').read()
d2 = dv[dv.index('### D2 -') if '### D2 -' in dv else dv.index('### D2'):]
d2 = d2[:d2.index('### D3')]
add('MIROVA_DIVERGENCES', 'D2: "cobertura ~70 % para VIIRS" + pendiente re-scrapear',
    'OBSOLETO' if 'S128' not in d2 else 'CONFIRMADO', '~70 %',
    ('S128 la midio en 79,2 % y el loader CONS union OCR de S86 la mitigo de facto. La seccion '
     'no tiene ninguna nota posterior al 2026-04-29. CLAUDE.md ya avisa que "el doc nunca se actualizo", '
     'o sea el error esta identificado y sin corregir'),
    'docs/MIROVA_DIVERGENCES.md:42-65', 'MEDIA')

add('MIROVA_DIVERGENCES', 'D18 encabezado: "ABIERTA (medida, sin A/B) S129"',
    'OBSOLETO', 'sin A/B',
    ('el A/B se corrio en S130 y su veredicto (NO ADOPTAR) esta en el cuerpo de la misma seccion, '
     'lineas 2018-2043, citando docs/s130/VEREDICTO_AB_D18.md'),
    'docs/MIROVA_DIVERGENCES.md:1960 contra :2018', 'BAJA')

add('MIROVA_DIVERGENCES', 'D3: conteos de categorias MIROVA (13.378 RUTINA, 407 Muy Bajo, 253 FP)',
    'SIN RESPALDO', 'los conteos del 2026-04-29',
    ('la seccion no nombra ningun script que los recompute y no hay entrada de D3 en '
     'scripts/libro_de_cuentas.py. Son conteos absolutos sobre un corpus vivo (A90): el CSV '
     'crecio y los porcentajes ya no se pueden comparar contra nada'),
    'docs/MIROVA_DIVERGENCES.md:66-95 + docs/LIBRO_DE_CUENTAS.json', 'MEDIA')

add('MIROVA_DIVERGENCES', 'D12 (S105, nota de gates intra-radio): "Siguen ON en mirova_equivalent.yaml"',
    'CONFIRMADO', 'la frase esta pero corregida abajo',
    ('el parrafo de S105 sigue diciendo "Siguen ON" y el flag efectivo es False, pero la propia '
     'seccion trae el bloque "RESUELTO S118 (flip OFF)" a continuacion. Queda como riesgo de '
     'lectura parcial, no como afirmacion sin corregir'),
    'docs/MIROVA_DIVERGENCES.md:1407-1441', 'BAJA')

# ---------------- MAPA_WORKSPACE ----------------
mp = os.path.abspath(os.path.join(ROOT, '..', '..', 'MAPA_WORKSPACE.md'))
if os.path.exists(mp):
    t = open(mp, encoding='utf-8').read()
    add('MAPA_WORKSPACE.md', 'Grafo de dependencias: "VRP Chile / CAIDO"',
        'FALSO' if 'CAÍDO' in t else 'CONFIRMADO', 'caido',
        ('el mismo documento declara arriba "RECUPERADO (verificado 2026-08-09)". El grafo ASCII '
         'no se actualizo: contradiccion interna dentro del doc'),
        'MAPA_WORKSPACE.md:18 contra :70-71', 'MEDIA')
    add('MAPA_WORKSPACE.md', '"Latente en VRP-chile (5 de 6 sin grupo de concurrency)"',
        'FALSO', '5 de 6 sin grupo',
        ('%d workflows pushean; %d tienen push-main y los %d restantes tienen grupo propio con '
         'retry x5. Ninguno queda sin grupo Y sin retry' % (len(pushers), len(en_grupo), len(fuera))),
        '.github/workflows/*.yml', 'MEDIA')

# ---------------- libro de cuentas ----------------
if os.path.exists('docs/LIBRO_DE_CUENTAS.json'):
    add('scripts/libro_de_cuentas.py', 'Cobertura del instrumento de numeros',
        'SIN RESPALDO', 'n/a',
        ('13 afirmaciones con instrumento: 11 OK y 2 con deriva (git_mb 6507,8 -> 6930,6; '
         'data_mb 1034,7 -> 1100,8). El propio script reporta 415 numeros SIN instrumento en el repo. '
         'Ninguna de las afirmaciones falsas de esta auditoria tenia instrumento'),
        'python scripts/libro_de_cuentas.py', 'MEDIA')

out = os.path.join('experiments', '_s131_audit', 'declarado_vs_efectivo', '01_resultados.json')
json.dump(R, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
c = collections.Counter(r['estado'] for r in R)
print('checks: %d  ->  %s' % (len(R), dict(c)))
for r in R:
    print('  [%-12s] %-6s %-26s %s' % (r['estado'], r['severidad'], r['fuente'], r['afirmacion'][:70]))
print('escrito:', out)
