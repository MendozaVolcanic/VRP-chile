# VM m06: por forma, filas y escenas distintas; regla y port contra MATLAB; magnitud de la diferencia del port en VRP
import sys, json, hashlib, numpy as np, pandas as pd
from pathlib import Path
from scipy.io import loadmat
sys.stdout.reconfigure(encoding='utf-8')
P = Path('..').resolve()
E = loadmat(P/'entradas_o2_modis.mat'); R = loadmat(P/'resultado_o2_modis.mat')
et = json.loads((P/'entradas_o2_modis_etiquetas.json').read_text(encoding='utf-8'))
df = pd.DataFrame(json.load(open('m03_regla_vs_bk.json')))
df['forma'] = json.load(open('m04_formas.json'))['formas']
df['h'] = [hashlib.md5(E['M13'][:,:,k].tobytes()+np.asarray(E['ALERTAS'][k,0]).tobytes()).hexdigest() for k in range(len(df))]
df['port_ok'] = df.d_port_alert<=1e-12; df['regla_ok']=df.d_regla_alert<=1e-12
# VRP por escena de MATLAB (reescalado MODIS) y VRP del port con su relleno: diferencia relativa
df['dl_mat'] = [float(R['DL'][k,0]) for k in range(len(df))]
df['coef'] = [e['coef_area']/1e6 for e in et]
df['vrp_mat'] = df.dl_mat*df.coef; df['vrp_port'] = [e['vrp_port_recalculado_mw'] for e in et]
df['rel'] = df.vrp_port/df.vrp_mat-1
g = df.groupby('forma')
print('forma | filas | distintas | regla==MATLAB (filas) | port==MATLAB (filas) | distintas con port!=MATLAB | filas con |VRP port/MATLAB-1|>1%')
for f, x in g:
    d = x.drop_duplicates('h')
    print('%-12s %4d %4d  regla %4d  port %4d  dist_port_mal %3d  >1%% %3d' % (f, len(x), len(d), x.regla_ok.sum(), x.port_ok.sum(), (~d.port_ok).sum(), (x.rel.abs()>0.01).sum()))
d = df.drop_duplicates('h')
print('TOTAL filas', len(df), 'distintas', len(d), '| regla==MATLAB filas', df.regla_ok.sum(), 'distintas', d.regla_ok.sum(), '| port==MATLAB filas', df.port_ok.sum(), 'distintas', d.port_ok.sum())
# 'alertas de 1 pixel y 2x2' del enunciado
for nombre, sel in (('1 pixel', df.forma=='1'), ('2x2', df.forma=='2x2')):
    x = df[sel]; dd = x.drop_duplicates('h')
    print(nombre, 'filas', len(x), 'distintas', len(dd), 'port==MATLAB filas', int(x.port_ok.sum()), 'distintas', int(dd.port_ok.sum()), '| mediana |rel VRP| port vs MATLAB filas con dif', float(x.rel[~x.port_ok].abs().median()))
# VRP: la regla da el VRP de MATLAB?
print('VRP MATLAB (DL*coef) vs VRP MATLAB (campo VRP del .m, coef VIIRS750):  max relativo tras reescalar', float(np.nanmax(np.abs(np.array([float(R['VRP'][k,0]) for k in range(len(df))])*1.89e7/(1.97e7*0.5625)/ (df.dl_mat*1.89e7/(1.97e7*0.5625)) -1))))
print('DL <= 0 en MATLAB (VRP negativo):', int((df.dl_mat<=0).sum()), '| en port:', int((df.vrp_port<=0).sum()))
df.to_json('m06_por_forma.json', orient='records')
