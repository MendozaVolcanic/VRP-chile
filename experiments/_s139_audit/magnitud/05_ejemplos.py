"""S139 magnitud, paso 5: pasadas concretas para reproducir (NdC colapso, Lascar tipico, MODIS Lascar).
Reusa build() de 02 sin reescribirlo: importa el modulo como texto hasta la definicion."""
import pathlib, sys, runpy, io, contextlib
R = pathlib.Path(__file__).resolve().parents[3]
src = open(R / 'experiments/_s139_audit/magnitud/02_descomposicion_pares.py', encoding='utf-8').read()
src = src.split('d = build(0)')[0].replace("d['pub_mw'], d['pub_n'] = pub, npub", "d['pub_mw'], d['pub_n'] = pub, npub; d['t'] = str(x.t); d['rec_t'] = r['datetime_utc']")
g = {'__file__': str(R / 'experiments/_s139_audit/magnitud/02_descomposicion_pares.py')}
exec(compile(src, '02', 'exec'), g)
d = g['build'](0)
d['R'] = d.pub_mw / d.osf_mw
cols = ['t', 'sensor', 'satzen', 'Npix', 'osf_mw', 'pub_n', 'pub_mw', 'pc_n', 'pc_mw', 'R', 't_bg', 'test1']
import pandas as pd; pd.set_option('display.width', 250); pd.set_option('display.max_columns', None)
print('NdC V375:'); print(d[(d.vol == 'NevadosDeChillan')][cols].round(3).to_string())
print('\nLascar V375 muestra (Npix>=5, R<0.5):'); print(d[(d.vol == 'Lascar') & (d.res == 375) & (d.Npix >= 5) & (d.R < .5)][cols].head(5).round(3).to_string())
print('\nLascar MODIS muestra:'); print(d[(d.res == 1000)][cols].head(6).round(3).to_string())
print('\ntest1 V375 muestra:'); print(d[(d.res == 375) & d.test1 & (d.R < .3)][cols + ['vol']].head(5).round(3).to_string())
