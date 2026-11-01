# M1 T12c. Prueba OFFLINE de la logica de reparto por dia de la busqueda por ventana (pipeline/fetch.py, S157 #866),
# extraida por AST (no se importa pipeline.fetch: carga .env y earthaccess). Pregunta: si un granule Standard del
# 2026-10-18 05:06 UTC (como el que tiene produccion) llega en la lista de CMR, el reparto lo asigna al dia 18?
# Pregunta 1: si el reparto tuviera un defecto de borde, el caso 'ultimo dia de la ventana' lo veria.
# Pregunta 2: control positivo = granule del 17-oct debe caer en el 17; granule de medianoche debe dar None.
import ast,sys,datetime as dt
src=open('pipeline/fetch.py',encoding='utf-8').read()
tree=ast.parse(src)
want={'_repartir_por_dia','_parse_cmr'}
consts={'_MARGEN_MEDIANOCHE_S','_COUNT_POR_DIA'}
body=[]
for n in tree.body:
    if isinstance(n,ast.FunctionDef) and n.name in want: body.append(n)
    if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in consts for t in n.targets): body.append(n)
ns={'datetime':dt.datetime,'timedelta':dt.timedelta}
exec(compile(ast.Module(body=body,type_ignores=[]),'fetch_extract','exec'),ns)
print('constantes:',{k:ns[k] for k in consts})
def gran(b,e): return {'umm':{'TemporalExtent':{'RangeDateTime':{'BeginningDateTime':b,'EndingDateTime':e}}}}
dias=['2026-10-16','2026-10-17','2026-10-18']
G=[gran('2026-10-16T05:00:00Z','2026-10-16T05:06:00Z'),
   gran('2026-10-17T05:42:00Z','2026-10-17T05:48:00Z'),
   gran('2026-10-18T05:06:00Z','2026-10-18T05:12:00Z'),   # como VJ202IMG.A2026291.0506
   gran('2026-10-18T05:42:00Z','2026-10-18T05:48:00Z')]  # como VNP02IMG.A2026291.0542
r=ns['_repartir_por_dia'](G,dias)
print({d:(None if v is None else len(v)) for d,v in r.items()})
# medianoche: granule 23:57-00:03 del 17 al 18
r2=ns['_repartir_por_dia'](G+[gran('2026-10-17T23:57:00Z','2026-10-18T00:03:00Z')],dias)
print('con granule de medianoche:',{d:(None if v is None else len(v)) for d,v in r2.items()})
