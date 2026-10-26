"""S163 D-39 (R4 al dia): agrega al archivo de reposicion del PR #26 las filas que el consolidado perdio
DESPUES de armarse el PR (base c48d24cad8, 2026-10-22). Las busca en la historia: la base, una version cada
~6 h de commits del consolidado, y el padre de cada commit de VolcanoBot que toca el consolidado sin tocar
bitacora_robot.txt (firma de mezcla, H-T1). De cada llave ausente en <hasta> toma la copia mas reciente.
Las 2.110 lineas del PR quedan byte a byte. Solo nombres canonicos y tipos vigentes (mismo filtro que reponer_filas.py).
Limite declarado: una fila agregada y perdida entre dos muestras sin firma no se ve.
Uso: python s16_regenerar_reposicion.py <repo> <archivo_pr> <salida> [--hasta main]"""
import argparse, csv, datetime as dt, io, subprocess, sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'D:\vrp-trabajo\s163-d39\scripts'); import gl
F = 'monitoreo_satelital/registro_vrp_consolidado.csv'; BASE = 'c48d24cad87dcbc7741f0a683af6347501da592e'
TIPOS = {'ALERTA_TERMICA', 'FALSO_POSITIVO', 'RUTINA'}
ap = argparse.ArgumentParser(); ap.add_argument('repo'); ap.add_argument('pr'); ap.add_argument('salida'); ap.add_argument('--hasta', default='main')
a = ap.parse_args()
def git(*x): return subprocess.run(['git', '-C', a.repo, *x], capture_output=True, check=True).stdout.decode('utf-8')
def filas(rev): return {gl._llave(f): f for f in csv.DictReader(io.StringIO(git('show', f'{rev}:{F}')))}
sys.path.insert(0, a.repo); from volcanes import VOLCANES_CONFIG
NOMBRES = {v['nombre'] for v in VOLCANES_CONFIG.values()}
hasta = git('rev-parse', a.hasta).strip()
log = [l.split() for l in git('log', '--format=%H %an %cI', f'{BASE}..{hasta}', '--', F).splitlines()][::-1]
muestras, ult = [BASE], None
for h, autor, c in log:
    t = dt.datetime.fromisoformat(c.replace('Z', '+00:00'))
    if ult is None or (t - ult).total_seconds() >= 6 * 3600: muestras.append(h); ult = t
    if autor == 'VolcanoBot' and 'monitoreo_satelital/bitacora_robot.txt' not in git('diff-tree', '--no-commit-id', '--name-only', '-r', h).split():
        print('firma de mezcla:', h, c); muestras.append(h + '^')
hoy = filas(hasta)
falta = {}
for m in muestras:  # de viejo a nuevo: la copia mas reciente gana
    for k, v in filas(m).items():
        if k not in hoy: falta[k] = (m, v)
texto_pr = open(a.pr, encoding='utf-8', newline='').read()
lector = csv.DictReader(io.StringIO(texto_pr)); cab = lector.fieldnames; previas = {gl._llave(f) for f in lector}
assert cab == list(next(iter(hoy.values())).keys()), 'cabecera distinta a la del consolidado'
nuevas = {k: v for k, (m, v) in falta.items() if k not in previas and v['Volcan'] in NOMBRES and v['Tipo_Registro'] in TIPOS}
descartadas = {k for k in falta if k not in previas} - set(nuevas)
ya_hoy = sum(1 for k in previas if k in hoy)
print(f'hasta {hasta[:10]}: {len(muestras)} muestras; ausentes hoy {len(falta)}; ya en el archivo del PR {len(falta) - len(nuevas) - len(descartadas)};'
      f' nuevas {len(nuevas)}; descartadas por nombre o tipo {len(descartadas)}; filas del PR que hoy SI estan en main {ya_hoy}')
buf = io.StringIO(); w = csv.DictWriter(buf, fieldnames=cab, lineterminator='\n')
for k in sorted(nuevas, key=lambda k: (-int(k[0]), k[1], k[2])): w.writerow(nuevas[k])
with open(a.salida, 'w', encoding='utf-8', newline='') as f:
    f.write(texto_pr if texto_pr.endswith('\n') else texto_pr + '\n'); f.write(buf.getvalue())
prot = [v for v in nuevas.values() if v['Tipo_Registro'] == 'ALERTA_TERMICA' and float(v['VRP_MW'] or 0) >= 1]
for v in sorted(prot, key=lambda v: v['timestamp']): print('   protegida nueva:', v['Fecha_Satelite_UTC'], v['Volcan'], v['Sensor'], v['VRP_MW'], 'MW', v['Distancia_km'], 'km')
print('tipos de las nuevas:', {t: sum(v['Tipo_Registro'] == t for v in nuevas.values()) for t in TIPOS})
