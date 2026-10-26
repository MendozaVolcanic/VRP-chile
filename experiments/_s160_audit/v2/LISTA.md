# Lista que verificas (de F2: 11 de 20 hallazgos; gravedad 3 o más, más ['203', '207'])

Sólo título, ubicación, gravedad y comando del auditor. No abras C:\vrp-trabajo\s159-pruebas\experiments\_s160_audit\f2\INFORME.md; sí puedes correr sus scripts (están en C:\vrp-trabajo\s159-pruebas\experiments\_s160_audit\f2).

## 201 (gravedad 5, CONFIRMADO (V750; para V375 y MODIS SOSPECHA de que rijan los mismos minimos))
- TÍTULO: C1 de escena 0,010 contra 0,02 (dNTI) y 0,01 (dETI) del codigo de MIROVA, que ademas resta la media 3x3 con el central: en 8 vecinos valen 0,0225 y 0,01125; el umbral efectivo de escena queda bajo el de MIROVA en 93 % V375, 76 % V750, 58 % MODIS (ventana K)
- UBICACIÓN: pipeline/profile.py:105 (yaml:124); detection_context.py:483-486,532-533; MIROVA_VIIRS750_hotspot_detection.m l. 183,186,281-285
- COMANDO DEL AUDITOR: PYTHONIOENCODING=utf-8 python experiments/_s160_audit/f2/umbral_efectivo.py
- SALIDA CRUDA: experiments/_s160_audit/f2/umbral_efectivo_salida.txt

## 202 (gravedad 4, CONFIRMADO)
- TÍTULO: C1 de cumbre 0,003 y piso de descarte -0,1 sufren el mismo cambio de espacio (3x3 con central -> 8 vecinos): 12,5 % mas laxos que el codigo de MIROVA; muerde en dETI de cumbre en 8 a 22 % de las pasadas K
- UBICACIÓN: pipeline/profile.py:104; detection_context.py:60-61,127-129,530-531; .m l. 184,187,298
- COMANDO DEL AUDITOR: python experiments/_s160_audit/f2/umbral_efectivo.py (filas *_sum)
- SALIDA CRUDA: experiments/_s160_audit/f2/umbral_efectivo_salida.txt

## 203 (gravedad  D25), CONFIRMADO (control del plan)
- TÍTULO: Recorte a cero del exceso sobre un fondo regional (mediana del anillo 5-25 km): 32 de 118 cumulos VIIRS 750 de la ventana K (27 %, 30 summit) se publican con 0,0 MW y desaparecen del tablero (isValidDetection exige pc.vrp_mw > 0); MIROVA no recorta y usa fondo local
- UBICACIÓN: pipeline/process_viirs_mod.py:1041,1056; process_viirs.py:1504; process_modis.py:1118; frontend/index.html:1603; MIROVA_VIIRS750_VRP.m l. 69-91
- COMANDO DEL AUDITOR: recorte
- SALIDA CRUDA: python experiments/_s160_audit/f2/rangos_chile.py (contador cumulo_con_px_y_vrp_0)

## 204 (gravedad 3, CONFIRMADO (control V3-1 reproducido y medido))
- TÍTULO: inner_radius_km se aplica desde el crater en el pipeline y desde el centro del volcan en anomaly_pixels[].dist_km, en el respaldo de clase del tablero y bajo el rotulo 'Distancia al crater'; en PCC (7,58 km entre centro y crater) 8 de 73 cumulos K cambian de clase segun el origen
- UBICACIÓN: volcanoes.yaml:18; clustering.py:104; process_viirs.py:1530; process_viirs_mod.py:1075; process_modis.py:1143; frontend/index.html:3036,3159
- COMANDO DEL AUDITOR: python experiments/_s160_audit/f2/origen_distancia.py
- SALIDA CRUDA: experiments/_s160_audit/f2/origen_distancia_salida.txt

## 205 (gravedad 4, CONFIRMADO (codigo); efecto SIN DATO)
- TÍTULO: C2 (5 y 10) multiplica en el segundo pase la sigma de un pool distinto al de MIROVA: sin el descarte < -0,1 ni el borde (MIROVA los aplica en los dos pases, misma funcion); ademas descartamos dETI < -0,1 del pool y MIROVA no
- UBICACIÓN: pipeline/detection_context.py:923 vs 492-510; .m l. 252-256,298-304,373-374
- COMANDO DEL AUDITOR: grep -n 'bg_mask = ' pipeline/detection_context.py; sed -n 295,305p MIROVA_VIIRS750_hotspot_detection.m
- SALIDA CRUDA: experiments/_s160_audit/f2/INFORME.md (seccion 205)

## 206 (gravedad 4, CONFIRMADO (codigo y coordenadas); efecto SIN DATO (pide pixeles))
- TÍTULO: Anillo de fondo 5-25 km centrado en el centro del volcan y no en el crater: en PCC el crater (7,58 km del centro) queda dentro del anillo que define t_bg, la compuerta de 3 K y el fondo del VRP; en Tupungatito el margen es 2,27 km
- UBICACIÓN: pipeline/profile.py:127-128; process_viirs.py:780,786,807; process_viirs_mod.py:517,521,539; process_modis.py:560,564,582; volcanoes.yaml (PCC lat/lon vs vent)
- COMANDO DEL AUDITOR: python experiments/_s160_audit/f2/origen_distancia.py (dist_centro_crater)
- SALIDA CRUDA: experiments/_s160_audit/f2/origen_distancia_salida.txt

## 207 (gravedad  latente), CONFIRMADO (control R2-7)
- TÍTULO: Tope de cordura 50 GW se decide con t_max_k antes de normalizar t_max_i04_k (VIIRS 375 siempre 'imposible' sobre el tope); 0 casos hoy
- UBICACIÓN: pipeline/store.py:165-166,551,556-557
- COMANDO DEL AUDITOR: orden de aplicacion
- SALIDA CRUDA: sed -n 551,557p pipeline/store.py; python experiments/_s160_audit/f2/rangos_chile.py (sanity_cap_anulado, vrp_exceeds)

## 208 (gravedad 3, CONFIRMADO)
- TÍTULO: Tope D9 de 5 MW: su predicado 'cirrus' (t_bg < 270 K) es verdadero en 81-88 % de las pasadas K por altitud, y 'solo contextual' es casi vacio porque el camino de BT esta apagado; muerde 1 cumulo en K (PCC MODIS 2026-10-03 01:25, 15,3 km) y 9 en todo el corpus
- UBICACIÓN: pipeline/profile.py:824-829 (yaml:506-507); process_viirs_mod.py:1009-1015; process_viirs.py:1440-1446; process_modis.py:1056-1062
- COMANDO DEL AUDITOR: python experiments/_s160_audit/f2/rangos_chile.py (t_bg<270, d9_capped, capped_K)
- SALIDA CRUDA: experiments/_s160_audit/f2/rangos_chile.txt

## 209 (gravedad 4, CONFIRMADO (codigo); conteo exacto de magnitudes cambiadas SIN DATO)
- TÍTULO: Modo de un pixel (suma < 5 MW y <= 3 pixeles publica el maximo) contra el codigo de MIROVA que suma todos los alertados; calibrado con el detector C0; en K puede cambiar la magnitud de hasta 102 cumulos V375, 27 V750 y 12 MODIS
- UBICACIÓN: pipeline/profile.py:857 (yaml:533-534); single_pixel_mode.py:94; process_viirs_mod.py:1125-1130; MIROVA_VIIRS750_VRP.m l. 83-91
- COMANDO DEL AUDITOR: python - (ver single_pixel_salida.txt)
- SALIDA CRUDA: experiments/_s160_audit/f2/single_pixel_salida.txt

## 211 (gravedad 3, CONFIRMADO)
- TÍTULO: VRE del tablero integra 6 h por record y hay 10,4 records por volcan y dia en K: 62,5 h integradas por dia, VRE sobreestimada 2,6 veces
- UBICACIÓN: frontend/index.html:2486-2500,3319
- COMANDO DEL AUDITOR: python experiments/_s160_audit/f2/origen_distancia.py (seccion VRE)
- SALIDA CRUDA: experiments/_s160_audit/f2/origen_distancia_salida.txt

## 213 (gravedad 4, CONFIRMADO)
- TÍTULO: RECALL_MIN del auto-audit (93,4 / 79,5 / 95,0) calibrado sobre el detector C0 y aplicado a records del detector K; con K VIIRS 750 publico 66,7 y 77,8 % de las alertas, bajo 79,5, asi que el flag sale por construccion
- UBICACIÓN: scripts/auto_audit_weekly.py:20-21,120,742-747; frontend/index.html:544
- COMANDO DEL AUDITOR: sed -n 742,747p scripts/auto_audit_weekly.py; sed -n 544p frontend/index.html
- SALIDA CRUDA: experiments/_s160_audit/f2/INFORME.md

Nota del orquestador: en hallazgos.csv del auditor, las filas 203 y 207 traen comas sin comillas y los campos quedaron
corridos. Según el auditor, 203 es de gravedad 5 («32 de 118 cúmulos VIIRS 750 ... se publican con 0,0 MW») y 207 es un
control con efecto latente (0 casos hoy). Sus comandos están entre los scripts de la carpeta de F2. Que el CSV del
auditor esté mal formado es un hallazgo de forma tuyo si lo confirmas.
