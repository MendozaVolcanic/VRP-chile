"""S163 D-39: el archivo de reposicion regenerado conserva byte a byte las 2.110 lineas del PR, no repite llaves,
y cada fila agregada es identica a su copia en 53b1e6d3c0^, falta en 53b1e6d3c0 y falta hoy en main."""
import csv, io, subprocess, sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'D:\vrp-trabajo\s163-d39\scripts'); import gl
S = r'D:\vrp-trabajo\s163-d39'; R = S + r'\mirova-v1'; F = 'monitoreo_satelital/registro_vrp_consolidado.csv'
viejo = open(S + r'\scripts\filas_perdidas_pr26.csv', encoding='utf-8', newline='').read()
nuevo = open(S + r'\scripts\filas_perdidas_s163.csv', encoding='utf-8', newline='').read()
print('el archivo nuevo empieza con el del PR byte a byte:', nuevo.startswith(viejo))
def tab(t): return list(csv.DictReader(io.StringIO(t)))
def git(rev): return subprocess.run(['git', '-C', R, 'show', f'{rev}:{F}'], capture_output=True, check=True).stdout.decode('utf-8')
fn = tab(nuevo); kn = [gl._llave(f) for f in fn]
print('filas', len(fn), 'llaves distintas', len(set(kn)))
agregadas = fn[len(tab(viejo)):]
padre = {gl._llave(f): f for f in tab(git('53b1e6d3c0^'))}; hijo = {gl._llave(f) for f in tab(git('53b1e6d3c0'))}; hoy = {gl._llave(f) for f in tab(git('main'))}
ok = sum(1 for f in agregadas if padre.get(gl._llave(f)) == f and gl._llave(f) not in hijo and gl._llave(f) not in hoy)
print('agregadas', len(agregadas), '; identicas a 53b1e6d3c0^, ausentes en 53b1e6d3c0 y ausentes hoy:', ok)
print('ninguna fila del archivo esta hoy en main:', not any(k in hoy for k in kn))
prot = [f for f in fn if f['Tipo_Registro'] == 'ALERTA_TERMICA' and float(f['VRP_MW']) >= 1]
print('protegidas en el archivo:', len(prot))
