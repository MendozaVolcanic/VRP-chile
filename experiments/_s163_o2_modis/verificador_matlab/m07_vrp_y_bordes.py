import sys, json, numpy as np
from pathlib import Path
from scipy.io import loadmat
sys.stdout.reconfigure(encoding='utf-8')
P = Path('..').resolve()
R = loadmat(P/'resultado_o2_modis.mat'); E = loadmat(P/'entradas_o2_modis.mat')
et = json.loads((P/'entradas_o2_modis_etiquetas.json').read_text(encoding='utf-8'))
V = np.array([float(R['VRP'][k,0]) for k in range(404)]); DL=np.array([float(R['DL'][k,0]) for k in range(404)])
print('VRP del .m == DL*1.97e7*0.5625/1e6 :', float(np.max(np.abs(V/(DL*1.97e7*0.5625/1e6)-1))))
print('coef_area etiquetas:', sorted({e['coef_area'] for e in et}), ' variantes por coef:', {c: sorted({e['variante'] for e in et if e['coef_area']==c}) for c in sorted({e['coef_area'] for e in et})})
# alertas cerca del borde (dentro de 3 celdas)
cerca=0; fuera_hull=0
from scipy.spatial import Delaunay
from scipy.ndimage import binary_dilation
for k in range(404):
    a=np.asarray(E['ALERTAS'][k,0]).ravel().astype(int)-1
    f=a%51; c=a//51
    if min(f.min(),c.min(),50-f.max(),50-c.max())<=2: cerca+=1
print('escenas con alerta a <=2 celdas del borde:', cerca)
J=json.load(open(P/'vara_preliminar_fillmissing2.json',encoding='utf-8'))
print('alertas_fuera_envolvente>0 segun vara_preliminar (no mio):', sum(j['alertas_fuera_envolvente']>0 for j in J))
