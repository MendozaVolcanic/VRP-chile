# Verificador: el control de identidad (relleno del port sobre el hueco del script == VRP del port del lote) puede fallar?
import sys, json, numpy as np
from scipy.io import loadmat
from scipy.ndimage import binary_dilation
sys.path.insert(0,'/c/vrp-trabajo/s162-modd/experiments/_s158_audit_r2/oraculo'); sys.path.insert(0,'C:/vrp-trabajo/s162-modd/experiments/_s158_audit_r2/oraculo')
import mirova_v750_r2 as ORA
sys.stdout.reconfigure(encoding='utf-8')
E=loadmat('../entradas_o2_modis.mat'); et=json.load(open('../entradas_o2_modis_etiquetas.json',encoding='utf-8'))
def hueco(m13,mask,k=None,incluir_nan=True,halo=True):
    enm=m13.copy(); enm[mask]=np.nan
    if k is None: k=3 if mask.sum()<=4 else (5 if mask.sum()<=30 else 7)
    ref=np.isnan(enm) if incluir_nan else mask
    if halo: enm[binary_dilation(ref,structure=np.ones((k,k),bool))]=np.nan
    else: enm[ref]=np.nan
    return enm
def correr(nombre, fmask=lambda m,a,sh:m, **kw):
    malos=0; mx=0
    for i,e in enumerate(et):
        M=E['M13'][:,:,i].astype(float); a=np.asarray(E['ALERTAS'][i,0]).ravel().astype(int)
        mask=np.zeros(M.shape,bool); mask[np.unravel_index(a-1,M.shape,order='F')]=True
        mask=fmask(mask,a,M.shape)
        enm=hueco(M,mask,**kw)
        lhot=float(np.nansum(M[mask])); c=e['coef_area']/1e6
        v=(lhot-float(np.nansum(ORA._fillmissing2_lineal(enm)[mask])))*c
        r=abs(v/e['vrp_port_recalculado_mw']-1); mx=max(mx,r); malos+= r>1e-9
    print('%-42s identidad rota en %3d de %d (max dif rel %.3g)'%(nombre,malos,len(et),mx))
correr('original (sin mutar)')
correr('halo k=5 en todas',k=5)
correr('sin halo',halo=False)
correr('mascara traspuesta',fmask=lambda m,a,sh:m.T.copy())
correr('mascara con orden C (base 1 por fila)',fmask=lambda m,a,sh:(lambda z:(z.__setitem__(np.unravel_index(a-1,sh,order='C'),True),z)[1])(np.zeros(sh,bool)))
correr('mascara corrida una columna',fmask=lambda m,a,sh:np.roll(m,1,axis=1))
correr('hueco sin tapar NaN originales',incluir_nan=False)
