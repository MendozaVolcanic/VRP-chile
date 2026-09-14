# S139 eje 2: banco de prueba con todos los datos y línea base de hoy

Auditoría de sólo lectura. No se tocó `pipeline/`, `frontend/` ni `data/`. Scripts en
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s139_audit\eje2\`:

| script | qué hace | tiempo |
|---|---|---|
| `banco_noches.py` | arma la tabla noche de volcán x sensor, evalúa 26 configuraciones, controles; salida `banco_noches_out.json` y `banco_tabla.json` | 31 s |
| `analisis_banco.py` | línea base por volcán, cobertura, poder, AUC por volcán con control barajado, reproducción de los números preliminares, contaminación de RUTINA; salida `auc_por_volcan.json` | 35 s |
| `magnitud_y_poder.py` | magnitud publicada en positivos y negativos, intervalos de Wilson, diferencia mínima detectable | 35 s |

Corrida sobre `main` en `b16bb8fab` (2026-09-13, después del PR #642).

## 0. Cómo está construido el banco (supuestos declarados)

**Unidad.** La noche de volcán por sensor (MODIS, VIIRS 375, VIIRS 750) y la noche de volcán con
cualquier sensor. Noche = fecha UTC de la pasada, la misma clave que `scripts/auto_audit_weekly.py`
y el eje 4 de S138.

**Referencia.** Todas las filas de `registro_vrp_consolidado.csv` (CONS: ALERTA_TERMICA,
FALSO_POSITIVO, RUTINA) y de `registro_vrp_ocr.csv` (OCR: sólo ALERTA_TERMICA_OCR y
FALSO_POSITIVO_OCR), normalizadas con `normalize_volcano_name` y `normalize_sensor` del loader
oficial. Ventana de la referencia: **2026-01-10 a 2026-09-07** (CONS; OCR desde 2026-01-20). Toda
cifra de este informe está restringida a esa ventana salvo que se diga otra cosa.

**Nuestro lado.** 59.310 records de los 11 Tier A (2025-02-15 a 2026-09-13). Se publica una noche
si al menos un record cumple el predicado del operador **ejecutado con node desde
`frontend/index.html`**: `isSummitDetection && isValidDetection && !isThermalArtifact &&
mirovaEqVrpDisplay(r, inner_radius_km) > 0` (el de `latestDetection`, index.html:1509-1513, sin
`isSensorVisible`, que por defecto deja los tres sensores visibles, index.html:868). Supuesto:
`_mirova_confirmed = false` siempre, porque si la etiqueta entra al predicado el banco se vuelve
circular. `inner_radius_km` se lee de la lista de volcanes del HTML.

**Negativo parametrizado** (el orquestador tiene otro auditor mirando si RUTINA vale):
- `rutina_estricta`: fila CONS, todas RUTINA, sin FP ni ALERTA en ese sensor (por defecto).
- `sin_alerta`: sin ALERTA en ese sensor (RUTINA o FP).
- `volcan_quieto`: rutina_estricta y sin ALERTA de ningún sensor del volcán en más o menos 3 días.
- `solo_fp`: noches con FALSO_POSITIVO y sin ALERTA.

Además: fuentes `cons` o `cons_ocr`; filtro diurno `pipeline` (elevación solar, mismo
`_reject_daytime` que `store.py`, vía `es_pasada_diurna_descartada`), `utc12` o `ninguno`;
radio de referencia opcional. Una noche con referencia y sin record nuestro (o al revés) es
**SIN DATO** y no entra ni como acierto ni como error.

**Configuración por defecto de la línea base:** `cons_ocr | pipeline | rutina_estricta | sin radio`.

## 1. Controles del instrumento

Dos preguntas, aplicadas al banco entero.
1. Si el predicado estuviera completamente roto, ¿se vería? Sí: los controles C_TODO (todo publica)
   y C_NADA (nada publica) dan recall 1,000 / 0,000 y tasa en negativos 1,000 / 0,000 en los tres
   sensores con los mismos denominadores (`banco_noches_out.json`, clave de la config por defecto).
2. Si el instrumento estuviera muerto, ¿se vería distinto? Sí: SIN DATO se cuenta aparte en cada
   celda (MODIS 2 positivos y 156 negativos sin record nuestro, VIIRS 375 42 y 104, VIIRS 750 13 y 142).

| control | resultado | esperado |
|---|---|---|
| identidad `isValidDetection` sobre los 5 casos del guard S139 | `[0,1,1,1,0]` | `[F,T,T,T,F]` |
| publicación: summit con cúmulo 0,4 MW a 1 km / far con el mismo cúmulo | `[1,0]` | `[1,0]` |
| alertas del banco contra `load_mirova_alertas` (claves fecha, volcán, sensor) | 1.952 = 1.952, 0 y 0 de diferencia | iguales |
| AUC con un campo oráculo igual a la etiqueta | 1,0 en los tres sensores | 1,0 |
| AUC con etiquetas barajadas dentro de cada volcán, media por volcán | 0,44 a 0,57 | cerca de 0,5 |
| records diurnos según el filtro del pipeline | 0 de 59.310 | 0 |

## 2. Línea base de hoy

### 2.1 Por sensor, todos los volcanes (config por defecto, ventana 2026-01-10 a 2026-09-07)

| sensor | recall en alertas (IC 95 %) | detección en negativos (IC 95 %) |
|---|---|---|
| MODIS | 10/75 = 0,133 (0,074 a 0,228) | 428/2.347 = 0,182 (0,167 a 0,198) |
| VIIRS 375 | 840/854 = 0,984 (0,973 a 0,990) | 1.145/1.393 = 0,822 (0,801 a 0,841) |
| VIIRS 750 | 200/233 = 0,858 (0,808 a 0,897) | 1.205/2.188 = 0,551 (0,530 a 0,571) |
| cualquier sensor, noche de volcán | 874/877 = 0,997 (0,990 a 0,999) | 1.252/1.384 = 0,905 (0,888 a 0,919) |

### 2.2 Por volcán (det/total; `sd` = SIN DATO positivos/negativos)

| volcán | MODIS pos | MODIS neg | V375 pos | V375 neg | V750 pos | V750 neg | cualquiera pos | cualquiera neg |
|---|---|---|---|---|---|---|---|---|
| Láscar | 9/74 | 5/144 | 166/167 | 19/37 | 123/131 | 46/90 | 177/177 | 24/36 |
| Lastarria | 0/0 | 18/220 | 142/146 | 29/47 | 0/0 | 120/218 | 146/146 | 37/46 |
| Isluga | 0/0 | 15/215 | 159/159 | 32/33 | 29/40 | 116/181 | 165/165 | 32/32 |
| Tupungatito | 0/0 | 21/206 | 105/107 | 55/74 | 6/14 | 100/187 | 107/108 | 67/72 |
| Planchón-Peteroa | 0/0 | 27/221 | 88/88 | 87/109 | 5/9 | 109/211 | 91/91 | 101/107 |
| Nevados de Chillán | 0/0 | 22/221 | 6/10 | 82/186 | 0/0 | 57/218 | 8/10 | 105/186 |
| Llaima | 0/0 | 22/220 | 2/2 | 193/206 | 0/0 | 93/221 | 2/2 | 204/206 |
| Villarrica | 1/1 | 30/238 | 29/29 | 188/202 | 5/6 | 136/232 | 31/31 | 197/201 |
| Copahue | 0/0 | 10/220 | 4/4 | 199/205 | 1/1 | 94/220 | 5/5 | 200/204 |
| Puyehue-Cordón Caulle | 0/0 | 202/222 | 104/107 | 97/113 | 30/31 | 181/190 | 107/107 | 112/113 |
| Chaitén | 0/0 | 56/220 | 35/35 | 164/181 | 1/1 | 153/220 | 35/35 | 173/181 |

### 2.3 Sensibilidad a las elecciones (todas en `banco_noches_out.json`)

| elección | MODIS neg | V375 neg | V750 neg | cualquiera neg | recall |
|---|---|---|---|---|---|
| rutina_estricta (defecto) | 0,182 | 0,822 | 0,551 | 0,905 | sin cambio |
| sin_alerta | 428/2.355 = 0,182 | 1.289/1.585 = 0,813 | 1.211/2.203 = 0,550 | 1.409/1.568 = 0,899 | sin cambio |
| volcan_quieto | 86/808 = 0,106 | 609/749 = 0,813 | 369/806 = 0,458 | 663/750 = 0,884 | sin cambio |
| solo_fp | 0/8 | 144/192 = 0,750 | 6/15 | 1/1 | sin cambio |
| sólo CONS (rutina_estricta) | 428/2.348 | 1.229/1.479 | 1.217/2.200 | 1.329/1.461 | V375 745/757, V750 186/219, MODIS 10/74 |
| filtro diurno `utc12` en vez de `pipeline` | 426/2.347 | igual | igual | igual | igual |
| sin filtro diurno | 426/2.326 | 1.077/1.312 | 1.191/2.154 | 1.151/1.270 | MODIS 11/81, V375 854/872 |
| radio de referencia 5 km | igual | igual | igual | igual | V375 751/763, V750 173/202 |

La conclusión de VIIRS 375 no depende de la definición de negativo: entre 75 % y 82 % en las
cuatro. La de MODIS sí (18 % contra 11 % en volcán quieto). El filtro diurno no mueve nada
(dos noches como máximo).

## 3. Hallazgos, lo peor primero

### H201. En VIIRS 375 el dashboard publica en 4 de cada 5 noches que MIROVA dejó en rutina, y el recall de 98 % es casi el de publicar todo
- **SCRIPT:SALIDA** `banco_noches.py`, config `cons_ocr|pipeline|rutina_estricta`: V375 negativos 1.145/1.393
  (0,822); control C_TODO recall 854/854. `analisis_banco.py` (g): el dashboard publica en 2.149 de
  2.461 noches-sensor V375 con record en la ventana, sin mirar etiqueta.
- **QUÉ PASA.** Sobre el cráter de volcanes tranquilos, a 375 m casi siempre hay uno o dos píxeles
  apenas más tibios que su entorno (ΔT mediano de 12 a 17 K en los ejemplos de Llaima), y el
  pipeline los convierte en un cúmulo summit con energía de décimas de megawatt. La magnitud
  mediana publicada en noches negativas es 0,069 MW (n = 1.145) y 72 % de esas publicaciones está
  bajo 0,1 MW; en positivas es 0,185 MW (n = 840) (`magnitud_y_poder.py` (1)). El predicado del
  operador no tiene piso de magnitud, así que cualquier energía positiva es "detección".
  Consecuencia para el banco: el recall V375 no mide nada útil por sí solo; un cambio que empeore
  la detección real puede quedar invisible porque el predicado ya está saturado.
- **CÓMO SE VE EN EL DASHBOARD.** Llaima con detección V375 en 193 de 206 noches rutinarias,
  Copahue 199/205, Villarrica 188/202, Chaitén 164/181. En noche de volcán con cualquier sensor,
  1.252 de 1.384 noches tranquilas (90,5 %) tienen algo publicado. El operador que mira "¿cambió
  el volcán?" ve señal casi todas las noches en volcanes donde MIROVA no alertó.
- **CÓMO REPRODUCIRLO.** `PYTHONIOENCODING=utf-8 python experiments/_s139_audit/eje2/banco_noches.py`;
  ejemplo Llaima VIIRS_NOAA21 2026-03-01 05:36 UTC, cúmulo summit 0,137 MW a 2,9 km, 1 píxel,
  `diag_nti_max` -0,930; noche 2026-03-01 con CONS RUTINA.
- **CONFIANZA.** CONFIRMADO como medición. Que eso sea sobre-detección depende de que RUTINA sea un
  negativo válido (lo mira otro auditor); con `volcan_quieto` sigue en 81,3 % (609/749).
- **GRAVEDAD 4.** Tuerce la lectura de "hubo cambio" en los volcanes de actividad baja y deja al
  banco V375 sin poder de detectar regresiones de recall.

### H202. MODIS: se pierden 64 de 75 noches de alerta de Láscar con el cúmulo en el cráter, porque la etiqueta sigue a un píxel a 24 a 33 km; y en Puyehue-Cordón Caulle se publica en 91 % de las noches rutinarias
- **SCRIPT:SALIDA** `analisis_banco.py` (e): "Lascar MODIS noches ALERTA no publicadas con cúmulo en
  inner y far: 64 de 75; mediana final_hotspot_dist_km 24,2 km (n=122 records), mediana pc_dist
  1,76 km". Línea base: MODIS recall 10/75; Puyehue-Cordón Caulle negativos 202/222.
- **QUÉ PASA.** En Láscar, el foco del cráter queda en el cúmulo primario (a 1 a 3 km), pero el
  píxel "más caliente" de la escena de 1 km cae en el salar o en otro terreno lejano; el record
  toma `distance_class = far` desde `final_hotspot` (fuente `eruption`, `discarded_reason =
  partial_eruption_hotspot_too_far`) y `mirovaEqVrp` (index.html:1057) devuelve 0. Es la cara
  far→summit de A46/A81/A82 ya conocida, medida ahora en noches. En Puyehue-Cordón Caulle pasa lo
  inverso: con `inner_radius_km = 20` el campo difuso del lacolito cae dentro y publica con
  mediana 2,8 MW (n = 202) noches en que MIROVA MODIS no alertó nunca.
  Ninguno de los dos predicados discrimina en MODIS: el del dashboard da 10/75 y 18 % en
  negativos; el del cúmulo (`pc.vrp_mw > 0` y centroide dentro del inner, sin mirar
  `distance_class`) da 75/75 y 2.302/2.347 = 98 %. `distance_class` es lo único que mantiene bajos
  los negativos MODIS, y lo hace a costa del recall.
- **CÓMO SE VE EN EL DASHBOARD.** Láscar MODIS aparece sin detección en noches con alerta de
  MIROVA (el cúmulo sólo se ve con "incluir lejanas"). Puyehue-Cordón Caulle MODIS aparece con
  detección casi todas las noches.
- **CÓMO REPRODUCIRLO.** Láscar MODIS_TERRA 2026-02-12 02:00 UTC: far, `pc.vrp_mw` 1,786 a 2,946 km,
  `final_hotspot_dist_km` 27,79; MODIS_AQUA 2026-02-09 07:20: far, 1,179 MW a 2,0 km, final a 26,61.
  CONS tiene 2 ALERTA_TERMICA ambas noches.
- **CONFIANZA.** CONFIRMADO.
- **GRAVEDAD 4.** Para Láscar el sensor MODIS no da alerta cuando MIROVA sí; queda cubierto a nivel
  noche por VIIRS (Láscar cualquier sensor 177/177), por eso no es 5.

### H203. La referencia CONS no lista todas las pasadas de MIROVA: RUTINA está contaminada en VIIRS 375 y "sin fila" no es negativo
- **SCRIPT:SALIDA** `analisis_banco.py` (f): de 734 alertas OCR V375, 492 no tienen ninguna pasada CONS
  a más o menos 10 minutos (V750 44 de 76, MODIS 3 de 36); ninguna cae sobre una pasada CONS RUTINA.
  83 de 1.587 noches V375 RUTINA estricta en CONS (5,2 %) tienen una ALERTA OCR esa misma noche y
  sensor, repartidas en 10 volcanes (V750 12 de 2.342, MODIS 1 de 2.504).
- **QUÉ PASA.** El canal CONS (latest.php) omite pasadas que sí aparecen en las imágenes por volcán.
  Una noche marcada RUTINA en CONS puede tener otra pasada, no listada, con alerta. Sólo CONS
  pierde 97 noches positivas V375 (757 contra 854) y 14 V750.
- **CÓMO SE VE EN EL DASHBOARD.** Invisible para el operador; afecta a toda métrica de precisión.
- **CÓMO REPRODUCIRLO.** `analisis_banco.py`, bloque (f).
- **CONFIANZA.** CONFIRMADO para el hueco de pasadas. Que las OCR sean alertas genuinas y no
  artefactos del OCR es SOSPECHA (A11, A76).
- **GRAVEDAD 3.** Cualquier banco que use sólo CONS subestima positivos V375 en 11 % y mete ~5 %
  de positivos dentro del negativo RUTINA.

### H204. Hueco de cobertura en enero de 2026 en 9 volcanes; contarlo como "no detectamos" infla los denominadores
- **SCRIPT:SALIDA** `analisis_banco.py` (b): noches-sensor con referencia y sin record nuestro:
  MODIS 160, V375 161 (42 con alerta), V750 156 (13 con alerta); concentradas en enero de 2026, 52 a
  54 por volcán en Chaitén, Copahue, Isluga, Láscar, Lastarria, Llaima, Nevados de Chillán,
  Planchón-Peteroa y Puyehue-Cordón Caulle. Tupungatito y Villarrica no tienen hueco. Records de
  Láscar por mes: 2025-11 136, 2025-12 ninguno, 2026-01 26.
- **QUÉ PASA.** No hay granules procesados para esas fechas en esos volcanes; no es falta de
  detección. Sin exigir cobertura, MODIS en negativos pasa de 426/2.356 a 426/2.514 y
  Puyehue-Cordón Caulle de 0,91 a 0,84.
- **CÓMO SE VE EN EL DASHBOARD.** Serie vacía en diciembre de 2025 y casi todo enero de 2026 en esos
  9 volcanes.
- **CÓMO REPRODUCIRLO.** `analisis_banco.py`, bloque (b).
- **CONFIANZA.** CONFIRMADO.
- **GRAVEDAD 2.** Histórico, no NRT; sí tuerce una métrica si no se exige cobertura.

### H205. El banco sólo puede decidir algo para VIIRS 375 en 7 volcanes, para VIIRS 750 en Láscar, Isluga y Puyehue-Cordón Caulle, y para MODIS sólo en Láscar
- **SCRIPT:SALIDA** `analisis_banco.py` (c) y `magnitud_y_poder.py` (3). Positivos con cobertura:
  MODIS Láscar 74, Villarrica 1, resto 0. V750 Láscar 131, Isluga 40, Puyehue-Cordón Caulle 31,
  Tupungatito 14, Planchón-Peteroa 9, Villarrica 6, Copahue y Chaitén 1, Lastarria, Nevados de
  Chillán y Llaima 0. V375 Láscar 167, Isluga 159, Lastarria 146, Tupungatito 107,
  Puyehue-Cordón Caulle 107, Planchón-Peteroa 88, Chaitén 35, Villarrica 29, Nevados de Chillán 10,
  Copahue 4, Llaima 2.
- **QUÉ PASA.** Diferencia mínima detectable (80 % de poder, cota no pareada): recall MODIS 0,155
  (12 noches de 75), V750 0,090 (21 de 233), V375 0,017 (15 de 854). Negativos: 0,03 a 0,04 en todos.
  Un cambio del pipeline que afecte sólo a Nevados de Chillán, Llaima o Copahue no se puede juzgar
  por recall con este banco; sólo por tasa en negativos.
- **CÓMO SE VE EN EL DASHBOARD.** Invisible.
- **CONFIANZA.** CONFIRMADO.
- **GRAVEDAD 3.** Limita qué decisiones del pipeline puede avalar el banco.

### H206. El AUC agrupado sobre volcanes miente: con etiquetas barajadas dentro de cada volcán todavía da 0,66 a 0,70 en VIIRS 375
- **SCRIPT:SALIDA** `banco_noches.py`, `control_barajado_auc` en `banco_noches_out.json`: V375 pooled
  `pc_dist` 0,698, `f5` 0,683, `pc_vrp` 0,672, mientras la media por volcán queda en 0,51 a 0,57.
- **QUÉ PASA.** Los volcanes con muchas alertas (Láscar, Isluga) tienen también campos más altos;
  mezclarlos crea separación aunque dentro de cada volcán no haya ninguna (Simpson; regla S126).
- **CÓMO SE VE EN EL DASHBOARD.** Invisible; es una trampa del instrumento.
- **CONFIANZA.** CONFIRMADO.
- **GRAVEDAD 3.** Un AUC agrupado reportado como "hay señal" puede justificar un umbral que no separa nada.

### H207. Sí hay señal persistida en VIIRS 375 (magnitud y distancia del cúmulo); en MODIS de Láscar no la hay en la magnitud del cúmulo, sí en la energía del Test 1 y el NTI
- **SCRIPT:SALIDA** `analisis_banco.py` (d), `auc_por_volcan.json`. Máximo por noche, AUC por volcán
  con al menos 5 positivos, control barajado por volcán entre 0,44 y 0,57:

| campo | MODIS Láscar | V375 media por volcán (rango) | V750 media por volcán (rango) |
|---|---|---|---|
| `primary_cluster.vrp_mw` sólo si summit | 0,544 | 0,829 (0,669 Nevados de Chillán a 0,922 Puyehue-Cordón Caulle) | 0,730 (0,483 Tupungatito a 0,849 Láscar) |
| `primary_cluster.centroid_dist_km` (menor = positivo) | 0,584 | 0,831 (0,625 Lastarria a 0,944 Villarrica) | 0,746 (0,438 Planchón-Peteroa a 0,953 Villarrica) |
| `f5_core_vrp_mw` | no persistido | 0,767 (0,565 Lastarria a 0,899 Villarrica) | no persistido |
| `diag_nti_max` | 0,720 | 0,661 (0,437 a 0,804) | 0,651 (0,428 a 0,733) |
| `test1_k_observed` | 0,736 | 0,621 (0,365 a 0,727) | 0,646 (0,446 a 0,689) |
| `vrp_mw` del record | 0,705 | 0,769 | 0,692 |
| `t_max_k - t_bg_k` | 0,384 | 0,588, con Chaitén 0,191 (invertido) | 0,412 |
| `diag_n_first_pass_summit` | 0,558 | no persistido en VIIRS | no persistido en VIIRS |

- **QUÉ PASA.** En VIIRS 375 las noches de alerta tienen cúmulos más energéticos y más cerca del
  cráter que las rutinarias, en todos los volcanes con positivos. En MODIS la magnitud del cúmulo
  no separa en Láscar (el cúmulo del cráter existe igual en noches rutinarias, H202); lo que separa
  algo es la energía del Test 1 y el NTI. El contraste térmico `ΔT` va al revés en Chaitén V375 y
  en V750: las noches rutinarias tienen fondos más fríos que inflan el ΔT, que es lo esperable del
  gradiente topográfico (A69). No se propone umbral.
- **CÓMO SE VE EN EL DASHBOARD.** Invisible.
- **CONFIANZA.** CONFIRMADO para los AUC. Láscar MODIS descansa en 73 a 74 positivos.
- **GRAVEDAD 2.** Informativo.

### H208. La magnitud "núcleo" que se publica en VIIRS 375 supera a la del cúmulo en 23 % de los records, pese a que el código y la documentación dicen que sólo reduce
- **ARCHIVO:LÍNEA** `pipeline/f5_core.py:83-103` (el núcleo suma `anomaly_pixels` de cualquier
  camino dentro de `inner_km` del centroide, no sólo los píxeles del cúmulo); `frontend/index.html`
  en `mirovaEqVrpCore` ("F5' solo REDUCE el halo glaciar"); `docs/F5_DISPLAY_S96.md:41` ("0 inflación").
- **SCRIPT:SALIDA** consulta en esta sesión: de 17.667 records V375 con cúmulo con energía y
  `f5_core_vrp_mw`, en 4.145 el núcleo supera `pc.vrp_mw` en más de 1 %, en 964 lo duplica; máximo
  Isluga VIIRS_NOAA20 2026-03-09 05:30 UTC, cúmulo 0,001 MW y núcleo 0,130 MW (130 veces). Llaima
  VIIRS_NOAA20 2026-03-01 04:48: cúmulo 0,022 MW, núcleo 0,159 MW.
- **QUÉ PASA.** Cuando el cúmulo primario es un píxel débil y hay otros píxeles anómalos cerca que no
  forman parte de él, el núcleo los suma y publica más energía que la del cúmulo.
- **CÓMO SE VE EN EL DASHBOARD.** El valor en MW de la tarjeta y el gráfico V375 (modo Núcleo, por
  defecto) es mayor que el del cúmulo en esas pasadas. No cambia si una noche publica o no
  (`mirovaEqVrpCore` sólo actúa con base mayor que 0).
- **CÓMO REPRODUCIRLO.** Leer el record de Isluga citado y comparar `primary_cluster.vrp_mw` con
  `f5_core_vrp_mw`.
- **CONFIANZA.** CONFIRMADO el conteo y el mecanismo del código. Si esto es inflación indebida o el
  diseño recupera energía que el cúmulo dejó fuera (A46), es SOSPECHA; A10 (S132) ya decía que la
  mediana del núcleo contra MIROVA es mayor que la del cúmulo.
- **GRAVEDAD 2.** Magnitud, no decisión de publicar.

## 4. Reproducción de los números preliminares del orquestador

MODIS, hora UTC menor que 12, sólo CONS, predicado del dashboard. Los números del orquestador
corresponden a **no exigir cobertura** (cuenta las noches del hueco H204 como no detectadas).

| afirmación | orquestador | esta sesión, sin exigir cobertura | exigiendo cobertura | veredicto |
|---|---|---|---|---|
| Láscar noches ALERTA, detectadas | 75, 9 | 75, 9 | 73, 9 (2 SIN DATO) | reproducido |
| con cúmulo a menos de 5 km y far | 64 | 64 de 75 | igual | reproducido |
| `final_hotspot` a ~27 km | ~27 | mediana 24,2 km sobre 122 records (ejemplos entre 26,6 y 33,3) | igual | aproximado |
| RUTINA sin alerta con detección, 11 volcanes | 432/2.513 (17 %) | 426/2.514 | 426/2.356 | reproducido en orden, no exacto |
| Puyehue-Cordón Caulle | 84 % | 202/240 = 0,84 | 202/222 = 0,91 | reproducido |
| Chaitén | 23 % | 54/239 = 0,23 | 54/221 = 0,24 | reproducido |
| etiquetando por cúmulo: alertas | 74/76 | 74/76 | 74/74 | reproducido |
| etiquetando por cúmulo: RUTINA con detección | 2.309/2.513 | 2.310/2.514 | 2.310/2.356 | reproducido |
| AUC Láscar VRP del cúmulo | 0,57 | 0,536 (0,546 sólo summit) | igual | cerca, algo menor |
| AUC Láscar `diag_nti_max` | 0,72 | 0,711 | igual | reproducido |

Las diferencias de 6 noches y 1 alerta vienen de la definición de negativo (aquí `sin_alerta`
por sensor) y de cómo se agrupan las filas; no cambian ninguna conclusión.

## 5. Sobre si el banco discrimina

- **VIIRS 375**: el banco sí mide la tasa en negativos (IC de 4 puntos) y las AUC de magnitud y
  distancia; el recall con el predicado de hoy está saturado (H201) y no avala cambios por sí solo.
- **VIIRS 750**: discrimina en Láscar, Isluga y Puyehue-Cordón Caulle; en el resto no hay positivos.
- **MODIS**: sólo Láscar tiene positivos; ningún predicado probado separa (H202).
- **Cualquier sensor por noche de volcán**: 99,7 % de recall y 90,5 % en negativos; hoy casi no
  distingue una noche de alerta de una tranquila.
- La definición de negativo cambia MODIS y V750 unos 7 a 9 puntos; no cambia V375.
- Un juicio de cambio del pipeline con este banco debe reportar las dos columnas, estratificado
  por volcán, exigiendo cobertura y con OCR incluido; nunca AUC agrupado (H206).

## 6. VERIFICADO LIMPIO

| qué | comando o evidencia |
|---|---|
| el predicado ejecutado desde el HTML reproduce los controles del guard S139 | `banco_noches.py` imprime `[0,1,1,1,0]` y `[1,0]` |
| el loader oficial y la carga cruda del banco dan las mismas 1.952 alertas | `banco_noches.py`, línea "CONTROL loader oficial" |
| nuestros records no traen pasadas diurnas según el filtro del pipeline | `banco_noches.py`: "diurnos segun pipeline 0" sobre 59.310 |
| filtro diurno por elevación solar y por hora UTC dan lo mismo (2 noches MODIS de diferencia) | tabla 2.3 |
| en VIIRS (375 y 750) `distance_class` nunca es la causa de una noche no publicada: el predicado del dashboard y el del cúmulo dan conteos idénticos | `por_sensor` y `por_sensor_pred_cumulo` en `banco_noches_out.json` |
| `isSensorVisible` deja los tres sensores visibles por defecto | `frontend/index.html:868` |
| `inner_radius_km` del frontend coincide con la tabla del CLAUDE.md del proyecto (Lastarria 3, Planchón-Peteroa 3, Copahue 4, Tupungatito 7, Puyehue-Cordón Caulle 20, resto 5) | `banco_noches.py` imprime el diccionario |
| la etiqueta de sensor del CSV (`VIIRS` a secas = 750 m) se normaliza con la función oficial, sin regex propia | `pipeline/mirova_csv_loader.py:65-84` |
| ninguna alerta OCR cae sobre una pasada CONS RUTINA a más o menos 10 minutos (no hay conflicto de etiqueta en la misma pasada, sólo pasadas faltantes) | `analisis_banco.py` (f) |
| los controles C_TODO y C_NADA dan 1 y 0 con los mismos denominadores | `banco_noches_out.json` |

No se hicieron commits, ramas ni pushes. No se escribió en `data/`.
