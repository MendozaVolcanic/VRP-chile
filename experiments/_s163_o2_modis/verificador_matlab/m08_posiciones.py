import sys, json, hashlib, numpy as np, pandas as pd
from pathlib import Path
from scipy.io import loadmat
sys.stdout.reconfigure(encoding='utf-8')
P = Path('..').resolve()
E = loadmat(P/'entradas_o2_modis.mat'); df = pd.read_json('m06_por_forma.json')
et = json.loads((P/'entradas_o2_modis_etiquetas.json').read_text(encoding='utf-8'))
seen=set(); 
for k in range(404):
    if df.forma[k]!='2x2' or df.h[k] in seen: continue
    seen.add(df.h[k]); a=np.asarray(E['ALERTAS'][k,0]).ravel().astype(int)-1
    print('2x2 distinta k',k,et[k]['volcan'],et[k]['hora_utc'],'filas',sorted(set(a%51)),'cols',sorted(set(a//51)),'NaN originales en M13:',int(np.isnan(E['M13'][:,:,k]).sum()))
# posiciones del centro de la alerta para las 191 distintas
pos=set()
for k in range(404):
    if df.h[k] in pos: continue
    pos.add(df.h[k])
cs=[]
seen=set()
for k in range(404):
    if df.h[k] in seen: continue
    seen.add(df.h[k]); a=np.asarray(E['ALERTAS'][k,0]).ravel().astype(int)-1
    cs.append((float((a%51).mean()), float((a//51).mean())))
cs=np.array(cs); print('centro de alerta en las 191 distintas: fila min %.1f max %.1f | col min %.1f max %.1f | pares (fila,col) distintos %d' % (cs[:,0].min(),cs[:,0].max(),cs[:,1].min(),cs[:,1].max(), len({tuple(np.round(c,1)) for c in cs})))
print('volcanes de las 191 distintas:', pd.Series([et[k]['volcan'] for k in df.drop_duplicates('h').k]).value_counts().to_dict())
# escenas donde MATLAB, regla, port y marco cambiado coinciden TODOS (no discriminan)
print('escenas (filas) donde regla, port y marco cambiado dan lo mismo en alertas (1e-12):', int(((df.regla_vs_port_alert<=1e-12)&(df.regla_vs_col_alert<=1e-12)).sum()))
print('escenas distintas donde la regla NO es trivial (regla != port o regla != marco cambiado):', int(df.drop_duplicates('h').pipe(lambda d: ((d.regla_vs_port_alert>1e-12)|(d.regla_vs_col_alert>1e-12)).sum())))
