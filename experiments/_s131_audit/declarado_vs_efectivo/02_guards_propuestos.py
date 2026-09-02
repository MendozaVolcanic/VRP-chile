"""S131 T9 - prototipo de los guards propuestos (regla B del protocolo).

NO esta en tests/ a proposito: esta sesion es read-only sobre el repo. Este
archivo es el borrador ejecutable para que la sesion que aplique los fixes lo
mueva a tests/test_guard_declarado_vs_efectivo_s131.py sin reescribirlo.

Cada guard cierra un hallazgo por MEDICION, no por correccion de texto.
Ejecutar: python experiments/_s131_audit/declarado_vs_efectivo/02_guards_propuestos.py
"""
import sys, io, os, json, glob, re, subprocess
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
os.chdir(ROOT)

FALLAS = []


def check(nombre, ok, detalle):
    print(('  OK   ' if ok else '  FALLA') + '  ' + nombre + ('' if ok else ' -> ' + detalle))
    if not ok:
        FALLAS.append((nombre, detalle))


# G1 - ningun documento publicable nombra un producto NASA que el pipeline no descarga.
#      Cierra: FICHA "MOD14/MYD14" y la cabecera de vrp_regimes.py.
fetch = open('pipeline/fetch.py', encoding='utf-8').read()
productos = set(re.findall(r'"short_name":\s*"([A-Z0-9_]+)"', fetch))
vigilados = ['docs/FICHA_SDA_VRP_CHILE.md', 'README.md'] + glob.glob('pipeline/*.py')
malos = []
for f in vigilados:
    txt = open(f, encoding='utf-8', errors='replace').read()
    for cand in set(re.findall(r'\b(M[OY]D\d{2}[A-Z0-9]*)\b', txt)):
        if cand not in productos and not cand.startswith(('MOD021', 'MYD021', 'MOD03', 'MYD03')):
            malos.append((f, cand))
check('G1 productos NASA declarados existen en fetch.py', not malos, str(malos))

# G2 - toda mitigacion que la FICHA declara tiene su flag encendido.
#      Cierra: "zonas de exclusion" y "mitigado normalizando por NTI".
code = ('import json,pipeline.profile as p;'
        'print(json.dumps({k:getattr(p,k) for k in dir(p) if k.startswith("ENABLE_")}))')
P = json.loads(subprocess.run([sys.executable, '-c', code], capture_output=True, text=True,
                              env={**os.environ, 'VRP_PROFILE': 'mirova_equivalent'}
                              ).stdout.strip().splitlines()[-1])
ficha = open('docs/FICHA_SDA_VRP_CHILE.md', encoding='utf-8').read()
# El bloque de mitigaciones vive en "Evaluaciones de impacto / sesgos".
bloque = ficha[ficha.index('Evaluaciones de impacto'):ficha.index('Politica de privacidad')
                if 'Politica de privacidad' in ficha else ficha.index('privacidad')]
MITIGACIONES = {
    'zonas de exclusi': 'ENABLE_EXCLUDE_ZONES',
    'normalizando por indice termico': 'ENABLE_TEST1_NTI_INTEGRAL',
    'normalizando por índice térmico': 'ENABLE_TEST1_NTI_INTEGRAL',
}
mal = [(frase, flag) for frase, flag in MITIGACIONES.items()
       if frase in bloque and not P.get(flag, False)]
check('G2 mitigaciones declaradas en la FICHA estan encendidas', not mal, str(mal))

# G3 - invariante del piso VRP en el dato publicado.
#      Cierra: 1.635 records con el sello pegado y vrp_mw>0.
viol = tot = 0
for f in glob.glob('data/mirova_equivalent/*.json'):
    d = json.load(open(f, encoding='utf-8'))
    for r in d.get('records', d):
        if r.get('diag_vrp_floor_mw') is not None:
            tot += 1
            if (r.get('vrp_mw') or 0) > 0:
                viol += 1
check('G3 diag_vrp_floor_mw => vrp_mw == 0', viol == 0,
      '%d de %d sellados tienen vrp_mw>0' % (viol, tot))

# G4 - todo workflow que hace git push a main tiene grupo push-main O retry propio.
#      Cierra: "6 workflows / 3 excepciones" de CLAUDE.md, sin fijar la lista.
import yaml
mal = []
for f in sorted(glob.glob('.github/workflows/*.yml')):
    txt = open(f, encoding='utf-8').read()
    if 'git push' not in txt:
        continue
    d = yaml.safe_load(txt)
    grupo = (d.get('concurrency') or {}).get('group')
    tiene_retry = bool(re.search(r'for attempt in .*\n(?:.*\n){0,6}.*git push', txt))
    if grupo != 'push-main' and not tiene_retry:
        mal.append(os.path.basename(f))
check('G4 pusher a main: push-main o retry propio', not mal, str(mal))

# G5 - "on" quoted en todos los workflows (A43).
mal = [os.path.basename(f) for f in glob.glob('.github/workflows/*.yml')
       if 'on' not in yaml.safe_load(open(f, encoding='utf-8'))]
check('G5 clave "on" quoted en todos los yml', not mal, str(mal))

# G6 - docs/INDEX.md nombra como ultima auditoria la que realmente es la ultima.
auds = sorted(int(m.group(1)) for m in
              (re.search(r'AUDIT_S(\d+)', os.path.basename(f)) for f in glob.glob('docs/AUDIT_S*.md'))
              if m)
idx = open('docs/INDEX.md', encoding='utf-8').read()
ultima = 'AUDIT_S%d.md' % max(auds)
check('G6 INDEX.md lista la auditoria mas reciente', ultima in idx,
      'la ultima es %s y no figura' % ultima)

# G7 - ningun campo del schema publicado queda escrito con valor > 0 cuando su
#      flag productor esta apagado. Instancia: vrp_tir_mw con ENABLE_VRP_TIR_OUTPUT=False.
nz = 0
for f in glob.glob('data/mirova_equivalent/*.json'):
    d = json.load(open(f, encoding='utf-8'))
    nz += sum(1 for r in d.get('records', d) if (r.get('vrp_tir_mw') or 0) > 0)
check('G7 vrp_tir_mw == 0 mientras ENABLE_VRP_TIR_OUTPUT esta OFF',
      P.get('ENABLE_VRP_TIR_OUTPUT', True) or nz == 0,
      '%d records con vrp_tir_mw>0 y el flag apagado' % nz)

# G8 - las citas file:line de CLAUDE.md apuntan a la linea que dicen.
#      Se mantiene la tabla explicita: es el contrato, no una heuristica.
CITAS = [
    ('scripts/run_pipeline.py', 234, 'get_detection_anchor'),
    ('scripts/run_pipeline.py', 244, 'local_kernel_bg'),
    ('pipeline/geo_utils.py', 29, 'get_grid_center'),
    ('frontend/index.html', 1372, 'vrp_mw'),
]
mal = []
for f, n, tok in CITAS:
    L = open(f, encoding='utf-8', errors='replace').read().splitlines()
    if n > len(L) or tok not in L[n - 1]:
        mal.append('%s:%d no dice %s' % (f, n, tok))
check('G8 citas file:line de CLAUDE.md apuntan bien', not mal, str(mal))

print()
print('guards: %d | fallando hoy: %d' % (8, len(FALLAS)))
for n, d in FALLAS:
    print('  -', n, '::', d)
sys.exit(0)
