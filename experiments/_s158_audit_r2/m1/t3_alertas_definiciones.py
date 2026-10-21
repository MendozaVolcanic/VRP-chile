# M1 T3. Cuenta de "alertas de MIROVA" de VIIRS 750 en la ventana K (2026-09-18..2026-10-21) bajo las definiciones
# que usaron distintos frentes. Pregunta 1: si los frentes usaran definiciones incompatibles, los totales
# diferirian y aqui se veria. Pregunta 2: el control es que 'Sensor == VIIRS' sea 750: se comprueba con la
# cuantizacion de Distancia_km (celda 0.75 km vs 0.375 km) en alertas; si la columna estuviera muerta
# (constante) se imprimiria.
import pandas as pd, numpy as np
d=pd.read_csv('latest_consolidado.csv')
d['t']=pd.to_datetime(d['Fecha_Satelite_UTC'])
w=d[(d.t>='2026-09-18')&(d.t<'2026-10-22')]
print('filas tabla en ventana:',len(w), w.Sensor.value_counts().to_dict())
for s in ['VIIRS','VIIRS375','MODIS']:
    a=w[(w.Sensor==s)&(w.Tipo_Registro=='ALERTA_TERMICA')]
    print(s,'ALERTA_TERMICA tabla:',len(a),'| FALSO_POSITIVO:',((w.Sensor==s)&(w.Tipo_Registro=='FALSO_POSITIVO')).sum(),'| RUTINA:',((w.Sensor==s)&(w.Tipo_Registro=='RUTINA')).sum())
# control cuantizacion: distancia=0.75*sqrt(i^2+j^2) -> d/0.75 al cuadrado debe ser entero (para 750); para 375 usa 0.375
def frac_ok(dist,cell):
    q=(dist/cell)**2
    return np.mean(np.abs(q-np.round(q))<0.02)
for s,cell in [('VIIRS',0.75),('VIIRS375',0.375)]:
    a=d[(d.Sensor==s)&(d.Tipo_Registro=='ALERTA_TERMICA')&(d.Distancia_km>0)]
    print(s,'n',len(a),'cuantiza a celda',cell,':',round(frac_ok(a.Distancia_km.values,cell),3),'| a celda',0.375 if cell==0.75 else 0.75,':',round(frac_ok(a.Distancia_km.values,0.375 if cell==0.75 else 0.75),3))
# por clase de noche y por volcan
a=w[(w.Sensor=='VIIRS')&(w.Tipo_Registro=='ALERTA_TERMICA')].copy()
a['h']=a.t.dt.hour
print('V750 alertas tabla por hora UTC (diurnas ~17-21):',a.h.value_counts().sort_index().to_dict())
print(a.Volcan.value_counts().to_dict())
# OCR
import os
ocr='data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv'
print('OCR existe en snapshot:',os.path.exists(ocr))
