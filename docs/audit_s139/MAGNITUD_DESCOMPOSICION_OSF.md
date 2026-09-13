# S139: por qué nuestra magnitud VRP queda en ~0,7 de la de MIROVA

Auditoría de fase 1 (causa raíz con datos, sin arreglos). Scripts y salidas en
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s139_audit\magnitud\`
(`01_formula_osf.py` a `08_dispersion_miroVA.py`, cada uno con su `*_salida.txt`; pares en `02_pares.csv`).
Ningún archivo del repositorio fuera de esa carpeta y de este informe fue modificado.

## 0. Respuesta corta

**Contamos menos píxeles que MIROVA, no medimos peor cada píxel.** Cuando nosotros y MIROVA sumamos el
mismo número de píxeles, la razón es **0,99** y no depende del ángulo cenital. La razón global de
375 m (media geométrica 0,66; mediana 0,70 con F5') se parte en:

| factor | valor (media geométrica) | qué es físicamente |
|---|---|---|
| F_n = n publicado / Npix MIROVA | **0,55** | MIROVA integra 3 píxeles (mediana) donde publicamos 1 |
| F_hot, nivel caliente | 1,40 | los píxeles que guardamos son los más calientes del foco (se queda el pico) |
| F_bg, fondo | **0,875** | restamos un fondo ~1,2 K más tibio (anillo 5 a 25 km: +3,5 K) |
| selección = F_n · F_hot | 0,785 | 64 % del déficit en escala logarítmica |
| fondo | 0,875 | 36 % del déficit |

Denominador: 1.499 pasadas nocturnas VIIRS 375 m, clase 1 en el OSF v2.5, con record nuestro en el
mismo minuto que detecta al cráter, 2025-02-15 a 2025-12-01, 9 volcanes (Tupungatito y Llaima no
tienen filas clase 1 pareadas). La separación caliente/fondo usa 1.483 de esas pasadas.

## 1. El fenómeno, antes que los números

Un foco volcánico chico (fumarola, lago de lava, domo) es más pequeño que un píxel de 375 m. Su
calor se reparte en el píxel que lo contiene y "se derrama" a los vecinos por la respuesta óptica del
sensor y por dónde cae el foco respecto de la grilla. MIROVA suma el exceso de radiancia de todos esos
píxeles tibios que pasan su alerta (mediana 3). Nuestro pipeline, en la mayoría de las pasadas, se
queda con el píxel pico y deja fuera a los vecinos tibios: lo que integramos es sólo una parte de la
energía del foco. Cuando la mirada es oblicua el píxel real crece, MIROVA lo remuestrea a varias
celdas de área fija y cuenta más celdas; nosotros seguimos contando un píxel.

Además, lo que se resta como "suelo" difiere: MIROVA resta un fondo por píxel que queda en ~263 K
(mediana, noche, 375 m); nuestro anillo de 5 a 25 km, en volcanes sin kernel local, da un suelo más
tibio (Láscar, Isluga), y cada kelvin de suelo de más se come parte de un exceso que es de apenas
unos pocos kelvin.

## 2. La fórmula de MIROVA en el OSF (paso 1)

Preguntas del instrumento: si MIROVA usara área variable, el cociente VRP / (k·A·(hot − bk)) crecería
con SatZen; control negativo, aplicar el k·A de 375 m a filas de 1 km debe dar ~7,5 (dio 7,467).

- **375 m y 1 km: 100 % de las filas** (252.374 y 262.455) cumplen VRP = k·A_fija·(Tot_Lmir_hot −
  Tot_Lmir_bk) con |error| < 0,1 %, con k·A = 18,0·140.625 y 18,9·10⁶. Plano en los 5 bins de SatZen.
- **750 m: 91,8 %** (100.641 filas) cumplen con 19,7·562.500. El 8,2 % restante (8.239 filas) da
  cociente mediano 0,51, más frecuente de día (20 % contra 5,6 % de noche) y en eventos grandes
  (Npix 13 a 38 en la muestra). Lado MIROVA; no toca a Chile nocturno.
- **Tot_* es suma sobre Npix**: el fondo por píxel equivale a 279,7 K de noche (plausible); el total
  sin dividir daría 327,6 K (imposible como suelo nocturno).
- **Npix crece con SatZen** (firma del remuestreo), global 375 m: mediana 3 → 5, media 4,35 → 7,68 de
  0-15° a 50+°; 750 m mediana 6 → 11; 1 km 4 → 7.

Conclusión: MIROVA usa área fija en la fórmula y absorbe la geometría oblicua en el número de celdas.
Nuestro k y A son los mismos (`pipeline/process_viirs.py:65,75`, `pipeline/process_viirs_mod.py:53,64`,
`pipeline/process_modis.py:79,82`), así que la razón nuestra/MIROVA se separa **exactamente** en
R = F_n · F_ex.

## 3. Hallazgos (lo peor primero)

### H1. El déficit de magnitud es de conteo de píxeles, y nace en la detección, no en el recorte F5'
- SCRIPT:SALIDA `02_descomposicion_pares.py` / `02_salida.txt`, `03_salida.txt`
- QUÉ PASA: integramos 1 píxel donde MIROVA integra 3 (medianas). F_n = 0,553; F_ex = 1,192. Cuando el
  conteo coincide (343 pasadas, casi todas de 1 píxel), R = 0,992 y por SatZen 0,96 / 1,06 / 1,07 /
  1,02 / 0,93. No es el recorte del núcleo: F5' **sube** la razón (0,551 con `pc.vrp_mw` a 0,703), y
  aun sumando todos nuestros píxeles detectados dentro del `inner_radius_km` la razón es 0,755 con
  n/Npix = 0,667 (n_anomalous_pixels/Npix = 0,75). La razón sigue al conteo: por Npix de MIROVA 1 / 2 /
  3-5 / 6+ da 1,20 / 0,68 / 0,59 / 0,42; por n publicado 1 / 2 / 3-5 / 6+ da 0,56 / 0,72 / 0,86 / 1,25.
- CÓMO SE VE EN EL DASHBOARD: el operador ve magnitudes ~30 % más bajas que MIROVA en actividad
  débil persistente; un umbral o nivel en MW heredado de MIROVA quedaría corrido hacia abajo.
- CÓMO REPRODUCIRLO: `PYTHONIOENCODING=utf-8 python experiments/_s139_audit/magnitud/02_descomposicion_pares.py`.
  Pasada ejemplo: Láscar VIIRS_NOAA20 2025-03-03 04:48 UTC, SatZen 63,8°, MIROVA Npix 5 y 0,601 MW,
  nosotros 2 píxeles y 0,148 MW (R 0,25).
- CONFIANZA: CONFIRMADO (medido). El mecanismo que deja fuera a los vecinos (umbral de los Tests,
  `keep_peak`, second pass) es SOSPECHA: no se abrió ningún granule en esta sesión.
- GRAVEDAD: 3.

### H2. Dentro de un mismo volcán el déficit crece con el ángulo cenital porque MIROVA cuenta más celdas
- SCRIPT:SALIDA `03_estratos_finos.py` / `03_salida.txt`
- QUÉ PASA: una mirada oblicua agranda el píxel; MIROVA lo reparte en más celdas y nosotros no.
  Isluga, de 0-15° a 50+°: R 0,76 → 0,40, F_n 0,64 → 0,35, Npix MIROVA 3 → 5, nuestro n fijo en 1-2.
  Láscar: R 0,80 → 0,48 hasta 50°, F_n 0,49 → 0,32, Npix 5 → 6. Agrupado, R 0,825 → 0,562, pero la
  mezcla de volcanes cambia entre bins (Npix Chile agrupado es plano, Spearman 0,08): la tendencia se
  lee por volcán. Lastarria (0,59 a 0,72) y Cordón Caulle (0,95 a 1,01) no la muestran.
  **A nadir el déficit no desaparece**: F_n = 0,63 en 0-15° agrupado, así que el remuestreo explica
  la pendiente, no el nivel.
- CÓMO SE VE EN EL DASHBOARD: la serie de un volcán oscila con la geometría de la pasada (una misma
  actividad aparece hasta 2× más baja en pasadas oblicuas).
- CÓMO REPRODUCIRLO: `python experiments/_s139_audit/magnitud/03_estratos_finos.py`, bloque "tendencia SatZen dentro de volcan".
- CONFIANZA: CONFIRMADO la tendencia; SOSPECHA que el mecanismo sea sólo el remuestreo (en el
  subconjunto de igual conteo no hay pendiente, pero ese subconjunto es de 1 píxel y está condicionado).
- GRAVEDAD: 3.

### H3. El fondo del anillo 5 a 25 km resta de más en los volcanes sin kernel local
- SCRIPT:SALIDA `02_salida.txt`, `04_fondo_y_test1.py` / `04_salida.txt`; código `pipeline/process_viirs.py:1398-1419`
- QUÉ PASA: el suelo que restamos es más tibio que el de MIROVA. `t_bg_k` del anillo queda +3,5 K sobre
  el fondo por píxel de MIROVA (mediana); el fondo efectivamente usado (implícito en el VRP de cada
  píxel guardado) +1,2 K. En volcanes sin kernel, F_bg = 0,84 (Láscar, 390 pasadas) y 0,79 (Isluga, 333);
  con kernel 3×3 (`local_kernel_bg: true` en `volcanoes.yaml` para Cordón Caulle, Villarrica, Chaitén,
  Planchón-Peteroa, Lastarria) F_bg = 1,07 / 0,99 / 1,21 / 1,06, y Lastarria 0,755 (usa fondo global
  en su Test 1, `lbg_global_compatible`). En Láscar el fondo implícito coincide con el anillo en 95 %
  de las pasadas (difiere >1 % sólo en 4,9 %), es decir, ahí manda el anillo.
- CÓMO SE VE EN EL DASHBOARD: magnitudes de Láscar e Isluga 15 a 20 % más bajas sólo por el suelo.
- CÓMO REPRODUCIRLO: `python experiments/_s139_audit/magnitud/04_fondo_y_test1.py`, tabla "por volcan".
- CONFIANZA: CONFIRMADO la diferencia medida. SOSPECHA cuál es exactamente el fondo de MIROVA
  (vecinos, anillo propio): el OSF sólo da su suma.
- GRAVEDAD: 3.

### H4. Las pasadas cuya magnitud sale del Test 1 quedan en 0,45
- SCRIPT:SALIDA `04_salida.txt`; código `pipeline/process_viirs.py:1828-1869`
- QUÉ PASA: cuando el punto final viene del Test 1 (`final_hotspot_source = test1_roi`, 185 de 1.483
  pasadas, 13 %), R = 0,454 contra 0,729 del resto, y el fondo pesa mucho más (F_bg 0,61 contra 0,92;
  anillo +5,5 K sobre MIROVA). Sin las 15 pasadas de Nevados de Chillán (H5) la muestra de Test 1 se
  reduce pero la diferencia de F_bg persiste en Lastarria (Test 1 en 30 % de sus pasadas, F_bg 0,755).
- CÓMO SE VE EN EL DASHBOARD: pasadas de actividad real mostradas con magnitudes de ruido.
- CÓMO REPRODUCIRLO: `04_fondo_y_test1.py`, tabla "test1_roi vs resto".
- CONFIANZA: CONFIRMADO medido; SOSPECHA el reparto entre fondo efectivo del Test 1 y contaminación por NdC.
- GRAVEDAD: 3.

### H5. Nevados de Chillán feb-mar 2025: MIROVA suma una fuente a 15-19 km y la marca clase 1
- SCRIPT:SALIDA `05_ejemplos.py`, `06_ndc_record.txt`, `07_ndc_maxdist.py` / `07_salida.txt`
- QUÉ PASA: 15 pasadas con R = 0,007: MIROVA 9 a 13 MW con Npix 10 a 19, nosotros 1 píxel de ~0,05 MW.
  El centroide de MIROVA está a 15,3-19,6 km del volcán (Max_Dist 15,8-20,4 km); nuestro record pone
  el píxel más caliente a 17 km (`diag_t_max_dist_km` 16,97, 315,7 K) y publica sólo el píxel de cumbre.
  Nuestro comportamiento es el correcto; el problema es de la referencia. Excluyendo las 16 pasadas
  con centroide MIROVA fuera del inner: R = 0,688 (media geométrica), F_n 0,561.
- CÓMO SE VE EN EL DASHBOARD: invisible (la fuente lejana va a `far`).
- CÓMO REPRODUCIRLO: NdC VIIRS_NOAA20 2025-02-16 06:12 UTC, `VJ102IMG.A2025047.0612.021.2025047122017.nc`.
- CONFIANZA: CONFIRMADO la distancia; SOSPECHA la naturaleza de la fuente (probable incendio estival, no verificado).
- GRAVEDAD: 2 (sesga cualquier audit que tome clase 1 del OSF como verdad sin distancia; el cruce
  del eje 6 cuenta estas 15 pasadas como "DETECTA").

### H6. MODIS en Láscar: nuestro cúmulo tiene 3× más píxeles y 1/7 del exceso por píxel
- SCRIPT:SALIDA `02_salida.txt`, `05_salida.txt`
- QUÉ PASA: 35 pasadas, `pc.n_pixels` mediana 9 contra Npix 3; F_n 3,25, F_ex 0,14, R mediana 0,63.
  Agregamos muchos píxeles casi fríos y el exceso por píxel se diluye. Ejemplo MODIS_TERRA 2025-03-10
  02:10 UTC: MIROVA 3 píxeles 1,60 MW, nosotros 9 píxeles 0,12 MW.
- CÓMO SE VE EN EL DASHBOARD: magnitudes MODIS erráticas (0,07 a 1,02 en la muestra).
- CONFIANZA: CONFIRMADO medido; n chico y un solo volcán. Relación con D21 (banda 21) SOSPECHA.
- GRAVEDAD: 2.

### H7. VIIRS 750 m sigue el patrón de 375 m con muestra mínima
- `02_salida.txt`: 17 pasadas (sólo Láscar), F_n 0,40, F_ex 1,45, R 0,586. CONFIRMADO, n insuficiente para estratificar. GRAVEDAD 1.

### H8. El 8,2 % de las filas 750 m del OSF no cumple la fórmula de área fija
- `01b_salida_750.txt`. Lado MIROVA (cociente mediano 0,51, concentrado de día y en eventos grandes).
  Si alguna calibración de k para 750 m usó esas filas, el k quedaría sesgado: SOSPECHA, no verificado. GRAVEDAD 1.

## 4. Controles

| control | esperado | obtenido |
|---|---|---|
| reproducir el punto de partida | 0,551 / 0,586 / 0,665 | 0,551 / 0,586 / 0,665 (`pc.vrp_mw`, 375/750/1000) |
| negativo: pareo desplazado +6 h | ~0 pares | **0** pares (contra 1.552) |
| positivo del factor conteo: igual n | R ~1 si k, A y banda están bien | 0,992 (n = 343) |
| positivo SatZen en MIROVA | Npix crece | global 375 m mediana 3 → 5; Isluga 3 → 5 |
| k·A equivocado aplicado a 1 km | ~7,5 | 7,467 |
| réplica del núcleo F5' | 0 diferencias | 0 de 1.499 |
| instrumento de distancia MIROVA | NdC en el bin lejano | NdC centroide 15-19 km, R 0,011 |

Preguntas del instrumento. (1) Si la magnitud por píxel estuviera rota (k, A, banda), el subconjunto de
igual conteo lo mostraría lejos de 1: no lo está. Si la selección estuviera rota, F_n lo mostraría: lo
muestra. (2) Un instrumento muerto daría pares aleatorios o ninguno: el control de 6 h da 0 y la razón
responde de forma monótona a Npix, así que el instrumento distingue.

## 5. Supuestos y límites

- Pareo: misma resolución, ±10 min (todos los pares resultaron en el mismo minuto), predicado de
  cráter del eje 6 (`experiments/_s139_audit/eje6/02_cruce_osf_2025.py`).
- Publicado: V375 = `f5_core_vrp_mw` (presente en 1.499 de 1.499 pares); 750 m y MODIS = `pc.vrp_mw`.
- El fondo implícito por píxel es L(bt) − vrp_px/(k·A), mediana sobre los píxeles del núcleo con vrp > 0.
  La separación F_hot · F_bg usa el fondo de MIROVA como contrafactual; es una partición, no una prueba
  de cuál de los dos fondos es "el correcto".
- `anomaly_pixels` guarda el top 100 por VRP: sólo 1 par V375 llegó al tope.
- Banda MODIS usada para Planck: 3,929 µm (banda 21, `pipeline/process_modis.py:70`).
- No se abrieron granules: todo lo que diga "por qué el pipeline deja fuera a los vecinos" es SOSPECHA.
- Records 2025 sin `sensor_zenith_deg` persistido: se usó el SatZen del OSF de la misma pasada.

## 6. VERIFICADO LIMPIO

- **k y A de nuestro código = los de MIROVA** en los tres sensores: `process_viirs.py:65,75`,
  `process_viirs_mod.py:53,64`, `process_modis.py:79,82`, más perfil `ENABLE_NADIR_FIXED_PIXEL_AREA_{MODIS,VIIRS}=True`,
  `ENABLE_UTM_REGRID=False` (`VRP_PROFILE=mirova_equivalent python -c "import pipeline.profile as p; ..."`).
- **La fórmula de MIROVA es área fija sin corrección cenital**, exacta en 375 m y 1 km (`01_salida.txt`).
- **La magnitud por píxel coincide con MIROVA** cuando el conteo coincide (R 0,99, sin pendiente cenital): no
  hay que volver a buscar el déficit en k, en A, en la banda I04 ni en Planck (`03_salida.txt`).
- **`f5_core_vrp_mw` persistido = réplica independiente** del algoritmo en 1.499 de 1.499 pares (`02_salida.txt`).
- **El déficit no viene de que MIROVA sume píxeles lejanos** (salvo NdC): con Max_Dist ≤ 1 km, Isluga
  sigue en R 0,63 y F_n 0,51 (`08_salida.txt`).
- **El recorte a cero de ΔL** (`process_viirs.py:1416`) no es el motor: sólo aplica a píxeles con vrp 0,
  y los factores se midieron sobre píxeles con vrp > 0.
