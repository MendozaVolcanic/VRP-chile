# VM m04: escenas distintas y forma de las alertas, con mis propias definiciones
import sys, hashlib, numpy as np, collections, json
from pathlib import Path
from scipy.io import loadmat
from scipy.ndimage import label
sys.stdout.reconfigure(encoding='utf-8')
P = Path('..').resolve()
R = loadmat(P/'resultado_o2_modis.mat'); E = loadmat(P/'entradas_o2_modis.mat')
et = json.loads((P/'entradas_o2_modis_etiquetas.json').read_text(encoding='utf-8'))
K = E['M13'].shape[2]
def forma(a):
    rc = sorted(((int(i)-1)%51, (int(i)-1)//51) for i in a)
    n = len(rc)
    if n==1: return '1'
    r = [x[0] for x in rc]; c=[x[1] for x in rc]
    if n==4 and max(r)-min(r)==1 and max(c)-min(c)==1: return '2x2'
    # conexa (8)?
    m = np.zeros((51,51),int)
    for x in rc: m[x]=1
    nl = label(m, structure=np.ones((3,3)))[1]
    # 4-conexa
    nl4 = label(m)[1]
    if n==2: return '2_' + ('adj4' if nl4==1 else ('diag' if nl==1 else 'separados'))
    return '%d_%s' % (n, 'conexa4' if nl4==1 else ('conexa8' if nl==1 else 'sueltos'))
keyA = {}; keyB = {}; keyC={}
formas = []
for k in range(K):
    m = E['M13'][:,:,k]; a = np.asarray(E['ALERTAS'][k,0]).ravel().astype(int)
    hA = hashlib.md5(m.tobytes()+a.tobytes()).hexdigest()
    hB = hashlib.md5(m.tobytes()).hexdigest()
    hC = hashlib.md5(R['BK'][k,0].tobytes()).hexdigest()
    keyA.setdefault(hA, []).append(k); keyB.setdefault(hB, []).append(k); keyC.setdefault(hC,[]).append(k)
    formas.append(forma(a))
print('escenas', K)
print('distintas por (grilla+alertas):', len(keyA), '| solo grilla:', len(keyB), '| por matriz de fondo BK de MATLAB:', len(keyC))
# pasadas
print('etiquetas: pasadas', len({(e['volcan'],e['hora_utc'],e['lote']) for e in et}), 'variantes', collections.Counter(e['variante'] for e in et))
print('formas:', collections.Counter(formas))
# distintas por forma
fd = collections.defaultdict(set)
for h, ks in keyA.items(): fd[formas[ks[0]]].add(h)
print('distintas por forma:', {f:len(s) for f,s in fd.items()}, 'total', sum(len(s) for s in fd.values()))
# npix del etiquetado vs forma
print('npix etiqueta vs forma:', collections.Counter((e['npix'], formas[i]) for i,e in enumerate(et)))
# duplicados: grilla igual con alertas distintas
dup = [ks for ks in keyB.values() if len({keyA_k for keyA_k,v in keyA.items() if v[0] in ks})>1]
print('grillas repetidas con alertas distintas:', len(dup))
json.dump({'formas':formas}, open('m04_formas.json','w'))
