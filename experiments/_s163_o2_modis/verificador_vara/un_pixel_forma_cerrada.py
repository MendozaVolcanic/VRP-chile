import sys, json, collections, numpy as np
from scipy.io import loadmat
sys.stdout.reconfigure(encoding='utf-8')
# 1) en VIIRS: que par promedia MATLAB en el centro de una alerta de 1 pixel
R=loadmat('viirs_matlab/resultado_o2.mat'); V=loadmat('viirs_matlab/entradas_o2.mat')
c=collections.Counter()
for i in range(311):
    a=np.asarray(R['ALERTAS'][i,0]).ravel()
    if len(a)==1 and R['BK'][i,0].shape==(67,67):
        idx=int(a[0])-1; f=idx%67; col=idx//67; M=V['M13'][:,:,i]; BK=R['BK'][i,0]
        pf=(M[f-2,col]+M[f+2,col])/2; pc=(M[f,col-2]+M[f,col+2])/2
        c[('fila' if abs(BK[f,col]-pf)<1e-12*abs(pf) else '')+('col' if abs(BK[f,col]-pc)<1e-12*abs(pc) else '')+('' if (abs(BK[f,col]-pf)<1e-12*abs(pf) or abs(BK[f,col]-pc)<1e-12*abs(pc)) else 'NINGUNO')]+=1
print('VIIRS 1 pixel: MATLAB centro = media de ...',dict(c))
# 2) MODIS 1 pixel: forma cerrada propia vs JSON
E=loadmat('../entradas_o2_modis.mat'); et=json.load(open('../entradas_o2_modis_etiquetas.json',encoding='utf-8'))
J=json.load(open('../vara_preliminar_fillmissing2.json',encoding='utf-8'))
assert len(J)==len(et)
mal=0; n1=0; qh=collections.Counter(); sin_alt=0
for i,e in enumerate(et):
    if e['npix']!=1: continue
    n1+=1
    a=np.asarray(E['ALERTAS'][i,0]).ravel().astype(int)-1; f=a[0]%51; col=a[0]//51; M=E['M13'][:,:,i]
    cc=e['coef_area']/1e6
    lhot=M[f,col]; fondo_f=(M[f-2,col]+M[f+2,col])/2; fondo_c=(M[f,col-2]+M[f,col+2])/2
    v_f=(lhot-fondo_f)*cc; v_c=(lhot-fondo_c)*cc
    j=J[i]; assert j['k']==e['k']
    # regla = media de la pareja de fila (x = fila)
    if not np.isfinite(v_c): sin_alt+=1
    elif abs(v_c-j['vrp_regla_matlab_mw'])>1e-12*max(1,abs(v_c)): mal+=1
    p=j['vrp_port_recalculado_mw']
    qh['port=fila' if abs(p-v_f)<1e-9*max(1,abs(v_f)) and abs(v_f-v_c)>1e-12 else ('port=col' if abs(p-v_c)<1e-9*max(1,abs(v_c)) and abs(v_f-v_c)>1e-12 else ('empate (ambos iguales)' if abs(v_f-v_c)<=1e-12 else 'otro'))]+=1
print('MODIS 1 pixel: n',n1,'| regla del script != media de la pareja de COLUMNA (col-2,col+2), que es lo que hizo MATLAB en VIIRS: ',mal)
print('escenas donde la forma cerrada no aplica (NaN original en la pareja):',sin_alt)
print('port de Qhull elige:',dict(qh))
