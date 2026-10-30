# P1: si head_e.json estuviera mal (URL faltantes, status distinto), lo vería: recomputo desde poblacion_f4.json.e_candidatas.
# P2: control positivo = el set de URL de e_candidatas contra las claves de head_e.json; control sintético: quitar una URL debe aparecer como faltante.
import json, collections
B='D:/vrp-trabajo/temporales/s169_ver_candado/arbol/experiments/_s166_modd_f4/'
p=json.load(open(B+'poblacion_f4.json',encoding='utf-8')); h=json.load(open(B+'head_e.json',encoding='utf-8'))
cand=p['e_candidatas']; print('e_candidatas', len(cand), 'tramo E en pasadas', sum(1 for x in p['pasadas'] if x['tramo']=='E'))
urls={u for x in cand for u in (x.get('url_l1b'), x.get('url_geo')) if u}
print('urls esperadas', len(urls), 'claves head_e', len(h['urls']), 'iguales', urls==set(h['urls']))
print('modo', h['modo'], h['hora_utc'], 'controles', {k:(v['estado'],v['status']) for k,v in h['controles'].items()})
print('status', collections.Counter(v['status'] for v in h['urls'].values()), 'pide_urs', sum(v['pide_urs'] for v in h['urls'].values()), 'errores', sum(1 for v in h['urls'].values() if v['error']))
print('bytes None', sum(1 for v in h['urls'].values() if v['bytes'] is None), 'bytes min', min(v['bytes'] for v in h['urls'].values() if v['bytes']))
print('dias', {d:(v['pasadas'],v['sirve']) for d,v in h['dias'].items()})
print('dias_e_excluidos en poblacion', p['dias_e_excluidos'], 'detalle', p['head_e'].get('detalle_excluidos'))
# pasadas por dia en E de pasadas vs dias de head
c=collections.Counter(x['dt'][:10] for x in p['pasadas'] if x['tramo']=='E'); print('pasadas E por dia coincide', dict(c)=={d:v['pasadas'] for d,v in h['dias'].items()})
# todas las pasadas E tienen url en head
miss=[x for x in p['pasadas'] if x['tramo']=='E' and (x['url_l1b'] not in h['urls'] or x['url_geo'] not in h['urls'])]
print('pasadas E con url fuera de head', len(miss))
print('url esquemas', collections.Counter(u.split('/')[2] for u in urls))
# control: quitar una url
u0=sorted(urls)[0]; print('control sintetico (quitar una url) detectado:', (urls-{u0})!=set(h['urls']))
# los tamanos son plausibles (L1B ~70MB, MxD03 ~ 30MB?)
import re
for kind in ('021KM','03.'):
    bs=[v['bytes'] for u,v in h['urls'].items() if ('/'+('MOD' if True else '')) and re.search(kind,u.split('/')[-1])]
    print(kind, len(bs), (min(bs), max(bs)) if bs else None)
print('ejemplos url', sorted(urls)[:2], sorted(urls)[-1])
