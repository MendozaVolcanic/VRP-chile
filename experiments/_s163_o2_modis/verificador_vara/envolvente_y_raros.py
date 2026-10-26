import sys, json, numpy as np
from scipy.io import loadmat
from scipy.spatial import ConvexHull
sys.stdout.reconfigure(encoding='utf-8')
E=loadmat('../entradas_o2_modis.mat'); et=json.load(open('../entradas_o2_modis_etiquetas.json',encoding='utf-8'))
J=json.load(open('../vara_preliminar_fillmissing2.json',encoding='utf-8'))
for i in (361,386):
    M=E['M13'][:,:,i]; a=np.asarray(E['ALERTAS'][i,0]).ravel().astype(int)-1
    print(i,et[i]['volcan'],et[i]['variante'],'npix',et[i]['npix'],'ratio',J[i]['vrp_port_recalculado_mw']/J[i]['vrp_regla_matlab_mw'],'nNaN',int(np.isnan(M).sum()))
# la 'otra' de 1 pixel
for i,e in enumerate(et):
    if e['npix']!=1: continue
    a=np.asarray(E['ALERTAS'][i,0]).ravel().astype(int)-1; f=a[0]%51; c=a[0]//51; M=E['M13'][:,:,i]; cc=e['coef_area']/1e6
    vf=(M[f,c]-(M[f-2,c]+M[f+2,c])/2)*cc; vc=(M[f,c]-(M[f,c-2]+M[f,c+2])/2)*cc; p=J[i]['vrp_port_recalculado_mw']
    if abs(p-vf)>1e-9*abs(vf) and abs(p-vc)>1e-9*abs(vc):
        print('OTRO',i,e['volcan'],e['variante'],'port',p,'fila',vf,'col',vc,'f,c',f,c,'NaNs vecinos',int(np.isnan(M[f-3:f+4,c-3:c+4]).sum()))
# Envolvente por otro metodo: ConvexHull con ecuaciones, alertas dentro?
fuera=0
for i in range(len(et)):
    M=E['M13'][:,:,i].astype(float); a=np.asarray(E['ALERTAS'][i,0]).ravel().astype(int)-1
    ok=np.isfinite(M).copy(); mk=np.zeros(M.size,bool); mk[a]=True; mk=mk.reshape(M.shape,order='F'); ok[mk]=False
    r=3 if len(a)<=4 else 5; 
    # dilatar el hueco: quitar tambien el halo
    from scipy.ndimage import binary_dilation
    ok &= ~binary_dilation(mk|np.isnan(M),structure=np.ones((r,r),bool))
    P=np.column_stack(np.nonzero(ok)).astype(float); h=ConvexHull(P)
    Q=np.column_stack(np.nonzero(mk)).astype(float)
    d=(Q@h.equations[:,:2].T+h.equations[:,2]).max(1)
    fuera+=int((d>1e-9).sum())
print('alertas fuera de la envolvente (ConvexHull propio):',fuera)
