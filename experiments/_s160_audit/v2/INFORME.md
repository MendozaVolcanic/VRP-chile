# Verificación V2 de los hallazgos de F2 (unidades y magnitudes)

- Hora del servidor (header `Date` de api.github.com): inicio Thu, 22 Oct 2026 03:45:24 GMT; última lectura 03:56:47 GMT. Los tiempos de modificación de los archivos de CARPETA (00:45 a 00:56, hora de Chile) cuadran con eso.
- Commit medido: d516b9d8c. Instantánea en `D:\vrp-trabajo\temporales\s160_audit\main\`, y los datos se leyeron sólo de ahí.
- Modelo: Opus 5.5, esfuerzo bajo, sin subagentes.
- CARPETA: `C:\vrp-trabajo\s159-pruebas\experiments\_s160_audit\v2\`
- caminos.md se escribió antes de abrir los archivos citados. Su sha256 (787d157dbe4c7104a5fa9024977e8c67deac2a42db5a4a27a73fe52c56dde10b) y la hora están en `caminos.md.sha256`, un archivo aparte para no alterar el hash.
- Plan: `git diff 06e0fad3b -- docs/PLAN_AUDITORIA_S160.md` sólo muestra el §11.2b (R7). F2 no cambió.
- Referencia: tabla sola = `latest_consolidado.csv`, sha256 bc1522c24c924cb5...; combinado = tabla más `registro_vrp_ocr.csv`, sha256 94679246acbd0db5.... Pareo con `banco_paridad` (TOL_S 120 s) y sus capas por defecto (histórico y respaldo encendidos).
- Qué NO miré:
  - No reprocesé L1B, así que los efectos que piden píxeles quedan SIN DATO.
  - No hay código de MIROVA para MODIS ni para V375.
  - No abrí el informe de F2.
  - No verifiqué el «32» total de 203; sí el 30 summit y el 118.
  - No comprobé si el BOX de MIROVA cambia por volcán.
  - No crucé las 7 pasadas con alerta de 203 contra otras pasadas de la misma noche.
- Forma general: la «ventana K» de F2 (2026-09-18 a 2026-10-21) es un subconjunto. En d516b9d8c todo el corpus es K: `frontend/cambio_detector.js:32`, `DATOS_K_DESDE_UTC = "2025-02-15T00:00:00Z"`. Por eso informo dos ventanas, «desde 2026-09-18» y el corpus o marzo a octubre.

## En una pantalla

1. 203 CONFIRMADO, gravedad 5. Entre el 18-sep y el 21-oct, 30 de 97 cúmulos summit de V750 quedan en 0,0 MW: todos sus píxeles están a la temperatura del anillo o más fríos. El tablero no los publica. De esas 30 pasadas, 7 tenían alerta de MIROVA y 11 eran negativos limpios; ninguna era protegida.
2. 201 CONFIRMADO EN PARTE, gravedad 3 y no 5. La conversión 9/8 y los porcentajes son exactos, pero el C1 de escena casi no toca lo publicado: sólo 4 de 2.452 publicaciones V375, 8 de 485 V750 y 1 de 129 MODIS tienen algún píxel fuera del inner.
3. 211 REFUTADO. El auditor contó todos los records, y la VRE sólo suma las detecciones válidas: 6,2 h por día y volcán, no 62,5. Lo que queda es que 15 de 147 días-volcán integran más de 24 h.
4. 213, 202, 205, 206, 207 y 208 CONFIRMADOS; en 202, 205 y 206 el efecto queda SIN DATO. 209 CONFIRMADO EN PARTE: los cúmulos expuestos son 8, 80 y 18, no 12, 102 y 27, y en V375 no toca lo publicado. 204 CONFIRMADO EN PARTE: el respaldo de clase del tablero no corre nunca.
5. Hallazgo propio (SOSPECHA): los umbrales de cumbre rigen hasta inner_radius_km, y en el código de MIROVA sólo dentro de una caja de 7 × 7 píxeles. Entre 8 y 29 % de lo publicado cae fuera de esa caja, casi todo en PCC.

## Instrumentos (en CARPETA, cada uno con su salida al lado)

| script | salida | control |
|---|---|---|
| v_201_202_umbral.py | v_201_202_umbral_salida.txt | factor medido con la función real del pipeline; negativo 0/71.731; positivo 71.731/71.731 |
| v_201_efecto_v375.py | v_201_efecto_v375_salida.txt | positivo con inner/4: 507 |
| v_203_cero.py | v_203_cero_salida.txt | identidad del predicado ([0,1,1,1,0],[1,0]); 3.066 publicados |
| v_211_204.py | v_211_204_salida.txt | con todos los records reproduce las 62,5 h/día del auditor |
| v_204_respaldo.py | v_204_respaldo_salida.txt | las combinaciones suman 71.968 records |
| v_206_distancias.py | v_206_distancias_salida.txt | Copahue da 0,00 |
| v_208_d9.py | v_208_d9_salida.txt | t_bg<0: 0; t_bg<400: 100 % |
| v_209_spm.py | v_209_spm_salida.txt | spm_total como denominador |
| v_nuevo_caja_cumbre.py | v_nuevo_caja_cumbre_salida.txt | umbral de 0 km: 100 % |
| autoaudit_latest_d516b9d8c.json | copia de `data/audit_continuous/latest.json` del commit | (no aplica) |

## Hallazgos, ordenados por mi gravedad

### V2-01 (= F2-203): CONFIRMADO, gravedad 5
- TÍTULO: Los cúmulos summit con todos sus píxeles a la temperatura del anillo de 5 a 25 km, o más fríos, salen con 0,0 MW y el tablero no los publica; el código de MIROVA no recorta y usa fondo local.
- ARCHIVO:LÍNEA:
  - pipeline/process_viirs_mod.py:1039 (`L_bg_rad` sale de `t_bg`) y :1054 (`delta_L = np.maximum(L_hot - L_bg_rad, 0.0)`).
  - El fondo por vecinos está apagado: `ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750 False`, leído de `pipeline.profile`.
  - frontend/index.html:1603: `if (r?.primary_cluster) return (r.primary_cluster.vrp_mw ?? 0) > 0;`
  - MIROVA_VIIRS750_VRP.m l. 64-91, leído en TEXTO (es código fuente): el fondo sale de `fillmissing2` bajo un halo dilatado, `deltaL_MIR = L_MIRhot - L_MIRbk`, sin `max(0, ...)`.
  - SCRIPT:SALIDA v_203_cero.py : v_203_cero_salida.txt
- QUÉ PASA: en una cumbre nevada el cráter débil queda más frío que la mediana del anillo regional, que es valle tibio. El exceso de cada píxel se recorta a cero y el cúmulo vale 0,0 MW. Entre el 18-sep y el 21-oct hay 118 records V750 con cúmulo, 97 de ellos summit y 30 en 0 MW. En los 30, todos los píxeles tienen BT ≤ t_bg, así que la causa está confirmada. De marzo a octubre son 235 de 720 summit en V750, 16 de 145 en MODIS y 84 de 2.536 en V375.
- CÓMO SE VE EN EL DASHBOARD: la pasada no cuenta como detección, porque isValidDetection da falso. Contra MIROVA, la tabla sola y el combinado dan lo mismo para esos 30 cúmulos:

  | etiqueta | 18-sep a 21-oct | marzo a octubre (V750) |
  |---|---|---|
  | con alerta de MIROVA (perdida) | 7 | 55 |
  | negativo limpio (callar es lo correcto) | 11 | 68 |
  | sin información | 12 | 112 |
  | protegida (1 MW o más) | 0 | sin medir |
- CÓMO REPRODUCIRLO: `PYTHONIOENCODING=utf-8 python C:\vrp-trabajo\s159-pruebas\experiments\_s160_audit\v2\v_203_cero.py`. Un ejemplo es el primer record V750 de Láscar desde el 2026-10-01: `primary_cluster.vrp_mw = 0.0`, `geo_class summit`, BT del píxel 263,04 K.
- CONFIANZA: CONFIRMADO
- GRAVEDAD: 5. Mueve lo que se publica hoy, en las dos direcciones: arreglarlo destaparía alertas perdidas y también negativos limpios. Ninguna alerta protegida queda afectada en la ventana K.

### V2-02 (= F2-201): CONFIRMADO EN PARTE, gravedad 3
- TÍTULO: El C1 de escena (0,010 en dNTI y en dETI) queda bajo los mínimos del código de MIROVA llevados a 8 vecinos (0,0225 y 0,01125). La cuenta del auditor es exacta, pero ese umbral casi no actúa sobre lo publicado.
- ARCHIVO:LÍNEA:
  - pipeline/profile.py:105 (`DNTI_CONTEXTUAL_C1_SCENE`, valor efectivo 0.01).
  - pipeline/process_viirs_mod.py:808-809 y 891-893: el mismo C1 de escena se pasa al dNTI y al dETI.
  - pipeline/detection_context.py:483-486: media de 8 vecinos, sin el central.
  - MIROVA_VIIRS750_hotspot_detection.m l. 183 y 186 (mínimos 0,02 y 0,01 de ROI1); l. 281-287 y 362-363 (`colfilt` 3x3 con `mean(...,'omitnan')`, central incluido); l. 389-395 (BOX0 y ROI1 usan los umbrales de ROI1).
  - SCRIPT:SALIDA v_201_202_umbral.py, v_201_efecto_v375.py, v_203_cero.py
- QUÉ PASA:
  - La conversión es correcta. La medí con la función real del pipeline (`_nanmean_8neighbors_fast`) contra un port de `colfilt`: en todo el interior, el contraste de MIROVA es 0,888889 veces el nuestro (8/9). Con un vecino NaN el factor es 0,875 (7/8), así que cerca de píxeles retirados la conversión cambia un poco.
  - Los porcentajes del auditor se reproducen exactos. Entre el 18-sep y el 21-oct, el umbral de dNTI de escena queda más laxo en 93,2 % de las pasadas V375, 75,6 % V750 y 58,5 % MODIS. Los dos tests de escena quedan laxos a la vez en 58,2, 67,8 y 48,7 %. Por volcán va de 38 % (Planchón-Peteroa, MODIS) a 99 % (Lastarria, V375).
  - Lo que no se sostiene es la gravedad 5. El C1 de escena sólo rige fuera de inner_radius_km, y para publicar hay que ser summit. De marzo a octubre, sólo 4 de 2.452 publicaciones V375 tienen en su núcleo F5 algún píxel fuera del inner (el control positivo, con inner/4, da 507). En V750 son 8 de 485 y en MODIS 1 de 129, contando cualquier píxel de anomaly_pixels.
- CÓMO SE VE EN EL DASHBOARD: casi no se ve. Cambia cuántos píxeles «far» (grises) aparecen, no lo que se publica como alerta.
- CÓMO REPRODUCIRLO: `python ...\v2\v_201_202_umbral.py` y `python ...\v2\v_201_efecto_v375.py`
- CONFIANZA: CONFIRMADO en código, conversión y porcentajes. El efecto en lo publicado está medido y es casi nulo. Para V375 y MODIS no hay código de MIROVA, así que sus mínimos siguen como SOSPECHA, igual que dice el auditor.
- GRAVEDAD: 3. Es una divergencia de fidelidad que entra en el A/B de paridad con el código de MIROVA; hoy no mueve lo publicado.

### V2-03 (= F2-213): CONFIRMADO, gravedad 3
- TÍTULO: RECALL_MIN del auto-audit se calibró con el detector C0 (S119) y se aplica al detector K. Con K, V750 queda bajo la banda en la última corrida guardada en el commit.
- ARCHIVO:LÍNEA:
  - scripts/auto_audit_weekly.py:19-21 (las bandas son «referencia S119 - margen 5pp»), :120 (`RECALL_MIN`) y :742-747 (el flag).
  - frontend/index.html:544: el aviso dice que con K, V750 publicó 28 de 42 y 91 de 117.
  - SCRIPT:SALIDA autoaudit_latest_d516b9d8c.json, sacado con `git show d516b9d8c:data/audit_continuous/latest.json`.
- QUÉ PASA:
  - Medí por otro camino: la salida del propio auto-audit en el commit, generada el 2026-10-19T16:29:28Z sobre la ventana 2026-08-20 a 2026-10-19. Trae el flag `recall VIIRS750 73.3% < banda 79.5% (n=30, detector K)`. En la misma ventana, C0 da 88,0 %.
  - MODIS con K da 66,7 %, también bajo su banda de 95, pero no dispara. Supongo que es por `MIN_N_RECALL`; no lo leí.
  - Los 66,7 y 77,8 % del título del auditor son tasas por pasada de la prueba de adopción (index.html:544). El flag mide recall por noche. Son métricas distintas, aunque las dos apuntan al mismo lado.
- CÓMO SE VE EN EL DASHBOARD: el operador no lo ve. El auto-audit semanal queda con un flag permanente que no se apaga sin recalibrar la banda.
- CÓMO REPRODUCIRLO: `git -C C:\vrp-trabajo\s159-pruebas show d516b9d8c:data/audit_continuous/latest.json` y buscar `flags` y `por_detector`.
- CONFIANZA: CONFIRMADO
- GRAVEDAD: 3

### V2-04 (= F2-202): CONFIRMADO, efecto SIN DATO, gravedad 3
- TÍTULO: El C1 de cumbre (0,003) queda contra 0,003375 de MIROVA en 8 vecinos, y el piso de descarte (-0,1) contra -0,1125. Además, nosotros sacamos del pool los dETI < -0,1 y MIROVA no.
- ARCHIVO:LÍNEA:
  - pipeline/detection_context.py:60-61 (pisos de -0,1), :127-129 (descarte por dNTI y por dETI) y :483-486.
  - MIROVA_VIIRS750_hotspot_detection.m l. 184 y 187 (0,003); l. 298 (descarta sólo por el contraste de NTI); l. 368-374 (el contraste de ETI no tiene descarte).
  - SCRIPT:SALIDA v_201_202_umbral.py
- QUÉ PASA: se reproduce. Entre el 18-sep y el 21-oct, el umbral de dETI de cumbre queda más laxo que el de MIROVA en 8,2 % de las pasadas V375, 21,7 % V750 y 18,2 % MODIS; el de dNTI de cumbre, entre 0,2 y 2,8 %. Los dos descartes de más (el piso de dNTI y el de dETI, que MIROVA no tiene) recortan la cola negativa del pool. Eso achica sigma y también empuja hacia lo laxo. Saber cuántos píxeles cambian pide el dETI de cada píxel, que no se guarda.
- CÓMO SE VE EN EL DASHBOARD: SIN DATO (son píxeles de cumbre en el borde del umbral).
- CÓMO REPRODUCIRLO: `python ...\v2\v_201_202_umbral.py`, filas dnti_sum y deti_sum.
- CONFIANZA: CONFIRMADO en código y fracciones.
- GRAVEDAD: 3

### V2-05 (= F2-205): CONFIRMADO en código, efecto SIN DATO, gravedad 3
- TÍTULO: El pool de mu y sigma del segundo pase no excluye el borde ni los descartes negativos. MIROVA usa la misma función, con los mismos descartes, en los dos pases.
- ARCHIVO:LÍNEA:
  - pipeline/detection_context.py:923: `bg_mask = (~active_mask) & np.isfinite(dnti) & np.isfinite(deti)`. El primer pase, en :492-500, usa `build_unsuitable_mask`.
  - MIROVA_VIIRS750_hotspot_detection.m l. 211-235: los dos pases llaman a `contextualDetectionPass`. l. 288, 298 y 369: esa función excluye el borde y descarta los contrastes < -0,1.
- QUÉ PASA: es tal como dice el auditor. Además, el pool del segundo pase no lleva `roi_mask` y el del primero sí. Sospecho que eso amplía el pool a toda la matriz que recibe, pero no tracé qué recorte le pasa el procesador.
- CÓMO SE VE EN EL DASHBOARD: SIN DATO. El segundo pase no guarda su mu ni su sigma, sólo `diag_n_second_pass_recapture`.
- CÓMO REPRODUCIRLO: `sed -n 900,935p D:\vrp-trabajo\temporales\s160_audit\main\pipeline\detection_context.py`
- CONFIANZA: CONFIRMADO en código. Lo del `roi_mask` queda como SOSPECHA.
- GRAVEDAD: 3

### V2-06 (= F2-206): CONFIRMADO en código y coordenadas, efecto SIN DATO, gravedad 3
- TÍTULO: El anillo de fondo de 5 a 25 km se mide desde el lat/lon del volcán, no desde el ancla de detección (el cráter). En PCC el cráter cae dentro del anillo.
- ARCHIVO:LÍNEA:
  - pipeline/process_viirs_mod.py:517 (`dist = haversine_km(volcano_lat, ...)`) y :539 (`bg_mask` se arma con `dist`). El mismo patrón está en process_viirs.py:780 y process_modis.py:560.
  - scripts/run_pipeline.py pasa `volcano["lat"], volcano["lon"]` como centro, y pasa `get_detection_anchor` (vent primero, pipeline/geo_utils.py:53-78) sólo como `vent_lat`.
  - SCRIPT:SALIDA v_206_distancias.py
- QUÉ PASA:
  - Distancia del centro al cráter: PCC 7,58 km, con el cráter dentro del anillo; Tupungatito 2,73 km, con margen de 2,27 km; Villarrica 0,85; Láscar 0,68; Chaitén 0,59; Planchón-Peteroa 0,50; el resto 0.
  - Aquí la vara es la coherencia interna del pipeline. El `.m` de MIROVA para V750 no tiene anillo: su fondo del VRP es local. Su grilla se centra en `mirova_center`, que en PCC está a 0,15 km del lat/lon del volcán, no en el cráter.
  - El anillo alimenta `t_bg`, la compuerta de 3 K (`ENABLE_TESTS_23_NO_BT_GATE_VIIRS375 False`) y el fondo del VRP de V2-01. Cuánto cambia la mediana pide los píxeles.
- CÓMO SE VE EN EL DASHBOARD: SIN DATO.
- CÓMO REPRODUCIRLO: `python ...\v2\v_206_distancias.py`; `sed -n 515,540p .../process_viirs_mod.py`
- CONFIANZA: CONFIRMADO en código y coordenadas.
- GRAVEDAD: 3

### V2-07 (= F2-209): CONFIRMADO EN PARTE, gravedad 3
- TÍTULO: El modo de un píxel publica el máximo en vez de la suma en cúmulos de 2 o 3 píxeles bajo 5 MW, y el código de MIROVA suma todos los alertados. La exposición real es menor que la que dio el auditor, y en V375 no toca lo publicado.
- ARCHIVO:LÍNEA:
  - pipeline/single_pixel_mode.py:93 y siguientes; pipeline/process_viirs_mod.py:1122-1130.
  - MIROVA_VIIRS750_VRP.m l. 83-84: `L_MIRhot = sum(ZI_M13(alert), 'omitnan')`.
  - SCRIPT:SALIDA v_209_spm.py
- QUÉ PASA:
  - El máximo sólo difiere de la suma cuando el cúmulo tiene 2 o 3 píxeles. Desde el 2026-09-18 hay 8 cúmulos así en MODIS, 80 en V375 y 18 en V750. El auditor contó todos los cúmulos de más de un píxel (12, 102 y 27), que es sólo una cota.
  - En V375 los 80 traen `f5_core_vrp_mw`, y el tablero publica el núcleo F5 (frontend/index.html:1320-1321), que suma sus píxeles sin pasar por este modo.
  - La decisión de publicar no cambia, porque el máximo es mayor que 0 si y sólo si la suma lo es. Lo que cambia es la magnitud de 7 cúmulos summit con energía en MODIS y 18 en V750.
- CÓMO SE VE EN EL DASHBOARD: esos cúmulos de MODIS y V750 muestran una magnitud más baja. Ninguna alerta aparece ni desaparece.
- CÓMO REPRODUCIRLO: `python ...\v2\v_209_spm.py`
- CONFIANZA: CONFIRMADO EN PARTE.
- GRAVEDAD: 3

### V2-08 (= F2-208): números CONFIRMADOS, atribución SOSPECHA, gravedad 3
- TÍTULO: El predicado del tope D9 (sin camino de BT, sin NTI absoluto y con t_bg < 270 K) está activo en la mayoría de las pasadas. Topó 1 cúmulo desde el 2026-09-18 y 9 en el corpus.
- ARCHIVO:LÍNEA: pipeline/process_viirs_mod.py:1009-1016. Valores efectivos del perfil: `PATH_D_ONLY_CAP_MW 5.0`, `PATH_D_ONLY_CAP_TBG_MAX_K 270.0`, `ENABLE_BT_PATH_HOT False`. SCRIPT:SALIDA v_208_d9.py
- QUÉ PASA:
  - Desde el 2026-09-18, el predicado es verdadero en 80,6 % de las pasadas MODIS, 82,1 % V375 y 88,3 % V750. En todo el corpus K baja a 60,6, 63,2 y 71,8 %.
  - La diferencia entre las dos ventanas sugiere que además de la altitud pesa la estación. No medí la altitud, así que «por altitud» queda como SOSPECHA.
  - El cúmulo topado en la ventana es de PCC, MODIS_TERRA, 2026-10-03 01:25: summit, centroide a 15,28 km, 5,0 MW. En el corpus hay 1 en MODIS y 8 en V750.
- CÓMO SE VE EN EL DASHBOARD: esa pasada de PCC se publica con 5,0 MW exactos.
- CÓMO REPRODUCIRLO: `python ...\v2\v_208_d9.py`
- CONFIANZA: CONFIRMADO en números; la causa por altitud es SOSPECHA.
- GRAVEDAD: 3

### V2-09 (propio): SOSPECHA, gravedad 3
- TÍTULO: Los umbrales de cumbre (5 sigma y 0,003) rigen hasta inner_radius_km, que va de 3 a 20 km. En el código de MIROVA rigen sólo en la caja BOX==2 de 7 × 7 píxeles; fuera de ella aplica los mínimos de ROI1 (0,0225 y 0,01125 en 8 vecinos, con 10 sigma).
- ARCHIVO:LÍNEA:
  - MIROVA_VIIRS750_hotspot_detection.m l. 180-187 y 389-399.
  - Ejemplo de OSF, `Example/VIIRS750_example.mat`: BOX==2 son 49 píxeles en las filas y columnas 30 a 36 de 67, o sea una media anchura de 2,625 km a 750 m. BOX==1 son 350 píxeles en las filas 22 a 42 y las columnas 24 a 42.
  - pipeline/detection_context.py `roi1_summit_mask`: es un círculo de inner_km mientras `ENABLE_ROI1_BOX_PAPER` siga apagado.
  - SCRIPT:SALIDA v_nuevo_caja_cumbre.py
- QUÉ PASA:
  - Esto es lo que sí mueve lo publicado, a diferencia del C1 de escena de V2-02. Entre 2,625 km y el inner_radius aplicamos la vara sensible donde MIROVA aplica la estricta.
  - Publicaciones con el centroide a más de 2,625 km del cráter:

    | sensor | marzo a octubre | desde 2026-09-18 |
    |---|---|---|
    | MODIS | 27 de 129 | 6 de 21 |
    | V375 | 110 de 2.452 | 24 de 298 |
    | V750 | 38 de 485 | 9 de 67 |

  - Casi todas son de PCC, cuyo inner es de 20 km.
  - Queda como SOSPECHA porque el `.m` dice que MIROVA puede mover y redimensionar las ROI por volcán (l. 120-125), y no sé qué BOX usa en PCC.
  - En las diagonales la caja llega a 3,7 km. Con 3,712 km los números bajan poco: 22, 90 y 35.
  - Está emparentado con D18.
- CÓMO SE VE EN EL DASHBOARD: pasadas publicadas en PCC, y unas pocas en Tupungatito y Chillán, con cúmulos fuera de la caja de cumbre de MIROVA.
- CÓMO REPRODUCIRLO: `python ...\v2\v_nuevo_caja_cumbre.py`
- CONFIANZA: SOSPECHA
- GRAVEDAD: 3

### V2-10 (= F2-204): CONFIRMADO EN PARTE, gravedad 2
- TÍTULO: anomaly_pixels[].dist_km se mide desde el centro del volcán y el popup lo rotula «Distancia al cráter». El respaldo de clase por dist_km del tablero no se ejecuta nunca, y el cambio de clase de 8 de 73 es contrafactual.
- ARCHIVO:LÍNEA:
  - pipeline/process_viirs_mod.py:517 y 1075: `"dist_km": round(float(dist[r, c]), 2)`, con `dist` medida desde volcano_lat.
  - pipeline/clustering.py:104: el centroide se mide desde el vent.
  - frontend/index.html:3159 (el rótulo) y :3034-3036 (el respaldo de clase).
  - pipeline/f5_core.py:80-82: el comentario ya dice que dist_km tiene el ancla en el centro.
  - SCRIPT:SALIDA v_204_respaldo.py
- QUÉ PASA: confirmo el origen distinto y el rótulo. El respaldo de clase sólo corre si falta `distance_class` y hay píxeles, y eso pasa en 0 de 71.968 records: los 58.926 sin `distance_class` tampoco tienen píxeles ni hotspot final. El «8 de 73 cambian de clase» es lo que pasaría si el inner se midiera desde el centro, no algo que el tablero haga.
- CÓMO SE VE EN EL DASHBOARD: en PCC, con el toggle «Todos los pixels», el popup de los píxeles secundarios dice «al cráter» y en realidad mide al centro, que está a 7,58 km del cráter.
- CÓMO REPRODUCIRLO: `python ...\v2\v_204_respaldo.py`
- CONFIANZA: CONFIRMADO EN PARTE
- GRAVEDAD: 2

### V2-11 (= F2-211): REFUTADO tal como está escrito; lo que queda es de gravedad 2
- TÍTULO: La VRE del tablero no integra 62,5 h por día. Suma 6 h sólo por cada detección válida, que da 6,2 h por día y volcán de promedio entre el 18-sep y el 21-oct. Aun así, 15 de 147 días-volcán pasan de 24 h.
- ARCHIVO:LÍNEA: frontend/index.html:2486-2500: `if (!isValidDetection(r)) continue; ... if (v_mw > 0) vre_gj += v_mw * DT_HOURS * 3.6`. SCRIPT:SALIDA v_211_204.py
- QUÉ PASA:
  - El auditor dividió todos los records (10,4 por volcán y día) por los días. Su número se reproduce exacto si se cuentan todos los records: ese es el control, 62,5 h/día.
  - Pero la VRE se salta los records no válidos y los de magnitud 0. Aproximándola con el predicado de publicación (que además exige summit) da 6,2 h/día, y 7,1 de marzo a octubre. Por volcán va de 0 (Copahue, Llaima) a 19,1 h/día (Chillán).
  - La convención de 6 h por detección sigue sin base física. Con más de 4 publicaciones en un día integra más de 24 h: 15 días-volcán en la ventana y 148 de marzo a octubre. Con pocas publicaciones integra de menos.
- CÓMO SE VE EN EL DASHBOARD: en la caja VRE y en su curva. El factor 2,6 no existe.
- CÓMO REPRODUCIRLO: `python ...\v2\v_211_204.py`
- CONFIANZA: REFUTADO en el número; CONFIRMADO en que la convención de 6 h no tiene base física.
- GRAVEDAD: 2

### V2-12 (= F2-207): CONFIRMADO, latente, gravedad 2
- TÍTULO: El tope de cordura de 50 GW juzga la BT con t_max_k antes de copiar t_max_i04_k. En V375 la BT llega vacía, así que cualquier magnitud sobre el tope se anularía como imposible.
- ARCHIVO:LÍNEA:
  - pipeline/store.py:165-166: `t_max = record.get("t_max_k")` y `bt_imposible = t_max is None or ...`.
  - :556 (`_apply_sanity_cap`) corre antes de :561-562 (la normalización).
  - pipeline/process_viirs.py:2210: sólo devuelve `t_max_i04_k`.
- QUÉ PASA: lo confirma el orden de ejecución. En los datos, los 29.985 records V375 tienen las dos claves porque la normalización corre después. Hoy ningún record pasa de 5 GW: 0 casos.
- CÓMO SE VE EN EL DASHBOARD: hoy no se ve. Una pasada V375 real sobre 50 GW se publicaría en 0.
- CÓMO REPRODUCIRLO: `sed -n 159,175p` y `sed -n 548,562p` de pipeline/store.py.
- CONFIANZA: CONFIRMADO
- GRAVEDAD: 2

### V2-13 (forma): CONFIRMADO, gravedad 1
- TÍTULO: En hallazgos.csv de F2, las filas 203 y 207 tienen 9 campos en vez de 8, por comas sin comillas en «confianza». La gravedad de 207 que quedó corrida es 3.
- ARCHIVO:LÍNEA: C:\vrp-trabajo\s159-pruebas\experiments\_s160_audit\f2\hallazgos.csv, filas 4 y 8.
- CÓMO REPRODUCIRLO: leer el archivo con el módulo csv y contar los campos de cada fila.
- CONFIANZA: CONFIRMADO. GRAVEDAD: 1

## SEGUIMIENTOS (fuera de eje)

1. El primer pase promedia los 8 vecinos sobre el NTI crudo, con los píxeles calientes adentro (pipeline/detection_context.py:483-486). MIROVA saca antes de la población de vecinos los píxeles con NTI absoluto > -0,7 (.m l. 275-287). Un vecino caliente sube la media y baja el contraste de los píxeles de al lado, así que es un mecanismo candidato para la pérdida de vecinos tibios (A103). Desde el 2026-09-18, el 2,5 % de los records V375 y el 1,0 % de los V750 tienen píxeles de NTI absoluto (v_208_d9_salida.txt, columna con_nti_path). SOSPECHA, gravedad 3.
2. f5_core elige el pico entre los anomaly_pixels a menos de inner_km del centroide, no entre los píxeles del cúmulo (pipeline/f5_core.py:83-91). Hay 4 publicaciones V375 cuyo núcleo es un solo píxel fuera del inner del cráter: Lastarria 2026-05-12 05:36, 2026-07-17 06:18 y 2026-07-29 05:18, e Isluga 2026-06-14 05:18 (v_201_efecto_v375_salida.txt). Sospecho que ese píxel no es del cúmulo. SOSPECHA, gravedad 2.
3. La salida del auto-audit guardada en el commit todavía separa C0 de K con la frontera vieja (hay `por_detector.C0` en la ventana 2026-08-20 a 2026-10-19). O sea, se generó antes del cambio de frontera de `cambio_detector.js`. Gravedad 1.

## VERIFICADO LIMPIO

- Conversión 9/8, contra la vara correcta (el `colfilt` del .m con 'omitnan'): factor 0,888889 exacto en el interior, medido con la función de producción (v_201_202_umbral_salida.txt, parte A).
- Valores efectivos del perfil, leídos de `pipeline.profile` con VRP_PROFILE=mirova_equivalent:
  - C1: cumbre 0,003, escena 0,01, día 0,02.
  - C2: 5, 10 y 15.
  - Conectiva max (ENABLE_TESTS_23_PROSE_BRANCH True).
  - Fondo por vecinos apagado en V750 y V375.
  - Modo de un píxel encendido, con 3 píxeles.
  - Tope D9: 5 MW y 270 K.
- MIROVA_VIIRS750_VRP.m no recorta el exceso (l. 83-91; leído en TEXTO, es código fuente).
- Predicado del tablero: el control de identidad de banco_paridad da ([0,1,1,1,0],[1,0]).

## SIN DATO

- El efecto en píxeles de 202, 205 y 206: pide el dNTI y el dETI de cada píxel, o reprocesar L1B, que queda fuera de esta tarea.
- Si las 7 pasadas con alerta perdidas de V2-01 se publicaron en otra pasada de la misma noche.
- El BOX que usa MIROVA en cada volcán (V2-09).
- El «32» total de cúmulos en 0 MW de 203: verifiqué los 30 summit y los 118 con cúmulo, no los 2 far.

## FUERA DE ALCANCE

- Arreglos y tests del repositorio. MODIS y V375 contra código de MIROVA, que no existe.
