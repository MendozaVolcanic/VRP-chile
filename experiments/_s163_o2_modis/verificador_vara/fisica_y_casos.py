import sys, json, numpy as np
from scipy.io import loadmat
sys.stdout.reconfigure(encoding='utf-8')
E=loadmat('../entradas_o2_modis.mat'); et=json.load(open('../entradas_o2_modis_etiquetas.json',encoding='utf-8')); J=json.load(open('../vara_preliminar_fillmissing2.json',encoding='utf-8'))
r=np.array([j['vrp_port_recalculado_mw']/j['vrp_regla_matlab_mw'] for j in J])
for n in (1,2,3,4):
    s=[i for i,j in enumerate(J) if j['variante']=='fisica' and j['npix']==n]; x=r[s]
    print('fisica npix',n,'n',len(s),'mediana %.4f min %.4f max %.4f >10%%: %d  mediana|r-1| %.4f'%(np.median(x),x.min(),x.max(),int((abs(x-1)>.1).sum()),np.median(abs(x-1))))
for i,j in enumerate(J):
    if j['volcan'] in('Llaima','Lascar') and ((j['volcan']=='Llaima' and j['hora_utc'].startswith('2026-07-24 01:05')) or (j['volcan']=='Lascar' and j['hora_utc'].startswith('2026-05-11 07:55') and j['variante']=='fisica')):
        a=np.asarray(E['ALERTAS'][i,0]).ravel().astype(int)-1; f=a[0]%51; c=a[0]//51; M=E['M13'][:,:,i]; cc=et[i]['coef_area']/1e6
        vf=(M[f,c]-(M[f-2,c]+M[f+2,c])/2)*cc; vc=(M[f,c]-(M[f,c-2]+M[f,c+2])/2)*cc
        print(j['volcan'],j['hora_utc'],j['variante'],'npix',j['npix'],'port',j['vrp_port_recalculado_mw'],'regla',j['vrp_regla_matlab_mw'],'| cerrada par-columna',vc,'par-fila',vf)
