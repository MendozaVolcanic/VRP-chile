"""S163 D-39: las protegidas de Chillan del 15 y 16-oct (OCR) y si alguna version del consolidado tuvo su fila de tabla.
Ademas, identidad de las 29 filas de abril sin episodio propio contra 9d70bc2d53^."""
import subprocess, sys, csv, io
sys.path.insert(0, r'D:\vrp-trabajo\s163-d39\scripts'); import gl
R = r'D:\vrp-trabajo\s163-d39\mirova-v1'
def tabla(rev, path='monitoreo_satelital/registro_vrp_consolidado.csv'):
    t = subprocess.run(['git','-C',R,'show',f'{rev}:{path}'],capture_output=True,check=True).stdout.decode('utf-8')
    return list(csv.DictReader(io.StringIO(t)))
ocr = tabla('main', 'monitoreo_satelital/registro_vrp_ocr.csv')
ch = [f for f in ocr if f['Volcan'].startswith('Nevados') and f['Fecha_Satelite_UTC'][:10] in ('2026-10-15','2026-10-16')]
for f in ch: print('OCR', f['Fecha_Satelite_UTC'], f['Sensor'], f['VRP_MW'], f['Tipo_Registro'], f.get('Distancia_km'))
cons_hoy = {gl._llave(f): f for f in tabla('main')}
chc = [f for f in cons_hoy.values() if f['Volcan'].startswith('Nevados') and f['Fecha_Satelite_UTC'][:10] in ('2026-10-15','2026-10-16')]
print('consolidado hoy, Chillan 15-16 oct:', len(chc)); [print('  CONS', f['Fecha_Satelite_UTC'], f['Sensor'], f['VRP_MW'], f['Tipo_Registro'], f['Distancia_km']) for f in sorted(chc, key=lambda x: x['timestamp'])]
pr = {gl._llave(f): f for f in tabla('pr26','monitoreo_satelital/filas_perdidas_por_mezcla_2026.csv')}
print('en el archivo del PR, Chillan 15-16 oct:', [ (f['Fecha_Satelite_UTC'], f['Sensor'], f['VRP_MW']) for f in pr.values() if f['Volcan'].startswith('Nevados') and f['Fecha_Satelite_UTC'][:10] in ('2026-10-15','2026-10-16')])
p = {gl._llave(f): f for f in tabla('9d70bc2d53^')}
sin = [f for f in pr.values() if f['Fecha_Satelite_UTC'][:7]=='2026-04']
ok = sum(1 for f in sin if gl._llave(f) in p and all((p[gl._llave(f)].get(c) or '')==(f[c] or '') for c in f if c not in ('Fecha_Proceso_UTC','Ultima_Actualizacion_UTC')))
print('filas de abril del PR identicas (sin columnas UTC) a 9d70bc2d53^:', ok, 'de', len(sin))
