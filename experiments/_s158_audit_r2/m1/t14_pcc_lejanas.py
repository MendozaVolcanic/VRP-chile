# M1 T14. V1 (F1-H3) afirma que a 9.9-19 km del crater de Cordon Caulle "MIROVA nunca publico una alerta V750
# (maximo 8,55 km)". Esa frase usa solo filas ALERTA_TERMICA (lectura A). Pero el scraper rotula FALSO_POSITIVO a lo
# que cae fuera de su limite_km: si MIROVA SI alerto lejos, estaria en FALSO_POSITIVO. Pregunta 1: si el instrumento
# (lectura A) oculta alertas lejanas de MIROVA, aqui aparecen filas FALSO_POSITIVO de PCC con Distancia_km > 8,55.
# Pregunta 2: control = el mismo conteo en otro volcan donde se sabe que hay FALSO_POSITIVO.
import pandas as pd
t=pd.read_csv('latest_consolidado.csv'); t['t']=pd.to_datetime(t.Fecha_Satelite_UTC)
w=t[(t.Sensor=='VIIRS')&(t.t>='2026-03-01')]
for vol in ['Puyehue-Cordon Caulle','Lascar','Nevados de Chillan','Isluga']:
    g=w[w.Volcan==vol]
    print('==',vol,'| filas V750 desde 2026-03-01:',len(g),g.Tipo_Registro.value_counts().to_dict())
    for tr in ['ALERTA_TERMICA','FALSO_POSITIVO']:
        s=g[g.Tipo_Registro==tr].Distancia_km
        if len(s): print(f'   {tr}: n={len(s)} dist min {s.min():.2f} mediana {s.median():.2f} max {s.max():.2f} | >8.55 km: {(s>8.55).sum()}')
pc=w[(w.Volcan=='Puyehue-Cordon Caulle')&(w.Tipo_Registro=='FALSO_POSITIVO')]
print(pc[['Fecha_Satelite_UTC','VRP_MW','Distancia_km','Clasificacion Mirova']].tail(12).to_string())
# fechas de las 8 pasadas de 9.9-19 km citadas por V1
for f in ['2026-09-21','2026-09-22','2026-09-26','2026-09-29','2026-10-04','2026-10-07','2026-10-10','2026-10-21']:
    x=pc[pc.Fecha_Satelite_UTC.str.startswith(f)]
    y=w[(w.Volcan=='Puyehue-Cordon Caulle')&w.Fecha_Satelite_UTC.str.startswith(f)&(w.Tipo_Registro!='RUTINA')]
    print(f,'PCC V750 filas no-RUTINA ese dia:',len(y),y[['Fecha_Satelite_UTC','Tipo_Registro','Distancia_km','VRP_MW']].values.tolist()[:4])
