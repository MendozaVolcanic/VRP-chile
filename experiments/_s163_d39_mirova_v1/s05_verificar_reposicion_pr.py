"""S163 D-39 (punto 2): cada fila de filas_perdidas_por_mezcla_2026.csv del PR #26 debe estar,
identica campo a campo, en el padre de un commit de mezcla, faltar en ese commit, y faltar hoy en main.
Ademas: se cruzan las 241 llaves que perdio 53b1e6d3c0 (2026-10-24) con el archivo del PR."""
import subprocess, sys, csv, io, collections
sys.path.insert(0, r'D:\vrp-trabajo\s163-d39\scripts'); import gl
R = r'D:\vrp-trabajo\s163-d39\mirova-v1'; F = 'monitoreo_satelital/registro_vrp_consolidado.csv'
EPIS = ["79b9033e90", "74af2c3899", "b1dc9640c0", "e555d63337", "c05dc4d778", "85089b8a60",
        "9d70bc2d53", "8825bb4057", "fb2a3123f8", "f843a1ead6", "8e04975286", "dc5e5c0121", "81c06c52ab",
        "f1eaeaf74f", "c292d6b267", "ecdc09e4d6"]
def show(rev, path=F):
    return subprocess.run(['git','-C',R,'show',f'{rev}:{path}'],capture_output=True,check=True).stdout.decode('utf-8')
def tabla(rev, path=F):
    return list(csv.DictReader(io.StringIO(show(rev, path))))
pr = tabla('pr26', 'monitoreo_satelital/filas_perdidas_por_mezcla_2026.csv')
print('archivo del PR:', len(pr), 'filas; llaves distintas', len({gl._llave(f) for f in pr}))
hoy = {gl._llave(f) for f in tabla('main')}
padres = {e: {gl._llave(f): f for f in tabla(e + '^')} for e in EPIS}
hijos = {e: {gl._llave(f) for f in tabla(e)} for e in EPIS}
res = collections.Counter(); malas = []
for f in pr:
    k = gl._llave(f)
    if k in hoy: res['presente hoy en main'] += 1; malas.append(('hoy', f)); continue
    hit = [e for e in EPIS if k in padres[e] and k not in hijos[e]]
    ident = [e for e in hit if all((padres[e][k].get(c) or '') == (f.get(c) or '') for c in f)]
    if ident: res['identica en padre y perdida en el episodio'] += 1
    elif hit: res['en padre pero con algun campo distinto'] += 1; malas.append(('campo', f, hit))
    else: res['no aparece en ningun padre'] += 1; malas.append(('nada', f))
print(dict(res)); print('cabecera PR == cabecera main:', list(pr[0].keys()) == list(tabla('main')[0].keys()))
for m in malas[:10]: print('  ', m[0], {c: m[1][c] for c in ('Fecha_Satelite_UTC','Volcan','Sensor','VRP_MW','Tipo_Registro')}, m[2:] )
nuevas = [l for l in csv.DictReader(open(r'D:\vrp-trabajo\s163-d39\scripts\s04_ausentes_hoy.csv', encoding='utf-8'))]
kpr = {gl._llave(f) for f in pr}
print('perdidas del 2026-10-24 (s04):', len(nuevas), '; ya en el archivo del PR:', sum(gl._llave(f) in kpr for f in nuevas))
