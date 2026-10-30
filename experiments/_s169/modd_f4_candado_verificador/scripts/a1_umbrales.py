# P1: si una etiqueta estuviera mal respecto del umbral 1 MW (lectura A) o de la regla SN (<=0,05 MW no es alerta), lo veria: reclasifico por vrp_mirova desde el json crudo.
# P2: control positivo: la regla debe separar al menos una fila en cada clase (si todas dieran igual, el script esta muerto).
import json, collections
p=json.load(open('D:/vrp-trabajo/temporales/s169_ver_candado/arbol/experiments/_s166_modd_f4/poblacion_f4.json',encoding='utf-8'))
P=p['pasadas']
def clase(x):
    v=x['vrp_mirova']
    if x['lab'] in ('protegida','bajo1'): return ('protegida' if v>=1 else 'bajo1') 
    return x['lab']
mal=[(x['vol'],x['dt'],x['lab'],x['vrp_mirova']) for x in P if x['lab'] in ('protegida','bajo1') and clase(x)!=x['lab']]
print('mal etiquetadas por umbral 1 MW:', mal)
b=[x['vrp_mirova'] for x in P if x['lab']=='bajo1']; print('bajo1 n',len(b),'min',min(b),'max',max(b),'<=0.05:',sum(1 for v in b if v<=0.05))
pr=[x['vrp_mirova'] for x in P if x['lab']=='protegida']; print('protegida n',len(pr),'min',min(pr),'max',max(pr))
print('lab con vrp_mirova no nulo fuera de protegida/bajo1:', collections.Counter(x['lab'] for x in P if x['vrp_mirova'] not in (None,0) and x['lab'] not in ('protegida','bajo1')))
print('control positivo: clases distintas', len({clase(x) for x in P}))
