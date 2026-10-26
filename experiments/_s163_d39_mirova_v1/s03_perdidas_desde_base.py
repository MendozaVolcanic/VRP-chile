"""S163 D-39: llaves del consolidado perdidas desde la base del PR #26 (c48d24cad) y en el commit candidato 53b1e6d3c0."""
import subprocess, sys, csv, io, collections
sys.path.insert(0, r'D:\vrp-trabajo\s163-d39\scripts'); import gl
R = r'D:\vrp-trabajo\s163-d39\mirova-v1'; F = 'monitoreo_satelital/registro_vrp_consolidado.csv'
def txt(rev): return subprocess.run(['git','-C',R,'show',f'{rev}:{F}'],capture_output=True,check=True).stdout.decode('utf-8')
def filas(rev):
    return list(csv.DictReader(io.StringIO(txt(rev))))
def resumen(a, b, etiqueta):
    fa, fb = filas(a), filas(b)
    ka = collections.Counter(gl._llave(f) for f in fa); kb = collections.Counter(gl._llave(f) for f in fb)
    perd = set(ka) - set(kb)
    dup = sum(v-1 for v in kb.values() if v > 1)
    print(f'{etiqueta}: {a[:10]} {len(fa)} filas -> {b[:10]} {len(fb)} filas; llaves perdidas {len(perd)}; repetidas en destino {dup}')
    porfila = {gl._llave(f): f for f in fa}
    tipos = collections.Counter(porfila[k]['Tipo_Registro'] for k in perd)
    print('   tipos de las perdidas', dict(tipos))
    prot = [porfila[k] for k in perd if porfila[k]['Tipo_Registro']=='ALERTA_TERMICA' and float(porfila[k]['VRP_MW'] or 0) >= 1]
    for p in sorted(prot, key=lambda x: x['timestamp']): print('   protegida perdida:', p['Fecha_Satelite_UTC'], p['Volcan'], p['Sensor'], p['VRP_MW'], p['Distancia_km'])
    return perd
base = subprocess.run(['git','-C',R,'merge-base','main','pr26'],capture_output=True,text=True).stdout.strip()
resumen(base, 'main', 'base->main')
resumen('53b1e6d3c0^', '53b1e6d3c0', 'candidato')
resumen('53b1e6d3c0', '53b1e6d3c0~0', 'nulo')
