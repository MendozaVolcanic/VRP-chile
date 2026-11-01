import json,glob,re,collections,math,sys
R=r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s162-viirs375-c1b864"
src=open(R+r"\frontend\index.html",encoding="utf-8").read()
inner={}
for m in re.finditer(r'name:\s*"(\w+)".*?inner_radius_km:\s*([\d.]+)',src): inner.setdefault(m.group(1),float(m.group(2)))
def load(d):
    out={}
    for f in sorted(glob.glob(d+r"\*\resultados_VIIRS375_*.json")):
        for r in json.load(open(f,encoding="utf-8")):
            if isinstance(r,dict): out[r['id']]=r
    return out
b2=load(r"C:\vrp-trabajo\temporales\s162_v375\run_40131572769")
s162=load(r"C:\vrp-trabajo\temporales\s162_v375\run_40116289866")
ob=json.load(open(R+r"\experiments\_s162_v375\b2\objetivos_v375_b2.json",encoding="utf-8"))
o162=json.load(open(R+r"\experiments\_s162_v375\objetivos_v375_bc.json",encoding="utf-8"))
OB={o['id']:o for o in ob['pasadas']}
O162={o['id']:o for o in o162['pasadas']}
print("ids B2 en O162?", len(set(OB)&set(O162)))
def pub(r,mode='cercano'):
    p=r['port']['M14']
    if not p.get('npix') or p.get('vrp_mw') is None: return False,0
    d=min(q[3] for q in p['pixeles'])
    return (d<=inner[r['volcan']] and p['vrp_mw']>0), p['vrp_mw']
if __name__=="__main__":
    c=collections.Counter(r['estado'] for r in b2.values()); print(c)
    ok=[i for i,r in b2.items() if r['estado']=='ok' and OB[i]['lote']=='S162b']
    print("ok S162b",len(ok), "fuera",sum(1 for i,r in b2.items() if r['estado']!='ok'))
    pubs=[];anyp=0;
    for i in ok:
        r=b2[i]; p,v=pub(r)
        if r['port']['M14']['npix']: anyp+=1
        if p: pubs.append((i,r['volcan'],r['hora_utc'],round(v,4),r['port']['M14']['npix'],round(min(q[3] for q in r['port']['M14']['pixeles']),2)))
    print("M14 con npix>0:",anyp,"publica (mi predicado):",len(pubs))
    for x in pubs: print(x)
    # K publish in B2: pub_prod
    print("pub_prod en S162b:",sum(OB[i]['pub_prod'] for i in ok))
    fu=[(i,OB[i]['volcan']) for i,r in b2.items() if r['estado']!='ok']
    print("fuera por volcan:",collections.Counter(v for i,v in fu if i<5000), "ids",[i for i,v in fu][:3],"...")
    print("fuera dist_min:",[b2[i].get('dist_min_km') for i,v in fu][:10])
    print("fuera por tramo:",collections.Counter(OB[i]['tramo'] for i,v in fu), "por z:",collections.Counter(OB[i]['estrato_z'] for i,v in fu))
    # distribucion de la muestra total para comparar
    print("muestra tramo:",collections.Counter(o['tramo'] for o in OB.values() if o['lote']=='S162b'))
    print("fuera por volcan%:",{v:(n, sum(1 for o in OB.values() if o['lote']=='S162b' and o['volcan']==v)) for v,n in collections.Counter(v for i,v in fu).items()})
