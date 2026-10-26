"""S163 D-39: alguna version horaria del consolidado del 15 al 17-oct tuvo filas de Chillan a la hora de las alertas del OCR sin fila de tabla?"""
import subprocess, sys, csv, io, datetime as dt
R = r'D:\vrp-trabajo\s163-d39\mirova-v1'; F = 'monitoreo_satelital/registro_vrp_consolidado.csv'
log = subprocess.run(['git','-C',R,'log','--format=%H %cI','--since=2026-10-15T04:00:00Z','--until=2026-10-17T02:00:00Z','main','--',F],capture_output=True,text=True).stdout.split('\n')
log = [l.split() for l in log if l][::-1]
muestras, ult = [], None
for h, c in log:
    t = dt.datetime.fromisoformat(c.replace('Z','+00:00'))
    if ult is None or (t-ult).total_seconds() >= 3600: muestras.append((h, c)); ult = t
objetivo = {'2026-10-15 05:00', '2026-10-15 19:00', '2026-10-16 06:18', '2026-10-16 18:42'}
vistas = {}
for h, c in muestras:
    t = subprocess.run(['git','-C',R,'show',f'{h}:{F}'],capture_output=True,check=True).stdout.decode('utf-8')
    for f in csv.DictReader(io.StringIO(t)):
        if f['Volcan'].startswith('Nevados') and f['Fecha_Satelite_UTC'][:16] in objetivo:
            vistas.setdefault((f['Fecha_Satelite_UTC'], f['Sensor']), c)
print(len(muestras), 'muestras horarias; filas de Chillan a esas horas vistas en alguna:', vistas)
