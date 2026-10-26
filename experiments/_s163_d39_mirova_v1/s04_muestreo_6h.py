"""S163 D-39: llaves del consolidado presentes en algun punto desde la base del PR #26 y ausentes hoy.
Muestras: la base, cada ~6 h de commits del consolidado, y el padre de cada commit con firma de mezcla
(s02_firma_sin_bitacora.txt). Una fila agregada y perdida entre dos muestras no se ve (limite declarado)."""
import subprocess, sys, csv, io, collections, datetime as dt
sys.path.insert(0, r'D:\vrp-trabajo\s163-d39\scripts'); import gl
R = r'D:\vrp-trabajo\s163-d39\mirova-v1'; F = 'monitoreo_satelital/registro_vrp_consolidado.csv'
def filas(rev):
    t = subprocess.run(['git','-C',R,'show',f'{rev}:{F}'],capture_output=True,check=True).stdout.decode('utf-8')
    return {gl._llave(f): f for f in csv.DictReader(io.StringIO(t))}
commits = [l.split() for l in open(r'D:\vrp-trabajo\s163-d39\scripts\commits_cons_desde_base.txt')][::-1]  # viejo a nuevo
base = subprocess.run(['git','-C',R,'merge-base','main','pr26'],capture_output=True,text=True).stdout.strip()
muestras = [base]; ult = None
for h, a, ad, cd in commits:
    t = dt.datetime.fromisoformat(cd.replace('Z','+00:00'))
    if ult is None or (t-ult).total_seconds() >= 6*3600: muestras.append(h); ult = t
for l in open(r'D:\vrp-trabajo\s163-d39\scripts\s02_firma_sin_bitacora.txt'):
    muestras.append(l.split()[1] + '^')
hoy = filas('main'); print('main', len(hoy), 'filas;', len(muestras), 'muestras')
faltan = {}
for m in muestras:
    fm = filas(m); nuevas = {k: v for k, v in fm.items() if k not in hoy and k not in faltan}
    faltan.update({k: (m, v) for k, v in nuevas.items()})
    print(f'  {m[:11]:12s} {len(fm):6d} filas, ausentes hoy {sum(1 for k in fm if k not in hoy):4d}, nuevas en la union {len(nuevas)}')
print('UNION ausentes hoy:', len(faltan), dict(collections.Counter(v['Tipo_Registro'] for _, v in faltan.values())))
with open(r'D:\vrp-trabajo\s163-d39\scripts\s04_ausentes_hoy.csv','w',newline='',encoding='utf-8') as f:
    cab = list(next(iter(faltan.values()))[1].keys())
    w = csv.DictWriter(f, fieldnames=['muestra']+cab); w.writeheader()
    for k,(m,v) in sorted(faltan.items()): w.writerow({'muestra': m, **v})
