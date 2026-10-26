# Verificador S160, auditoría espacial (Tupungatito, Cordón Caulle, Isluga)

## 1. Encabezado

- Hora del servidor (GitHub, header `Date`): inicio Thu, 22 Oct 2026 16:56:56 GMT; cierre del informe Thu, 22 Oct 2026 17:12:35 GMT.
- Commit medido: datos de producción de `origin/main` db0dfe847 (comprobado contra el remoto con `gh api .../commits/main` a las 16:58 UTC: db0dfe847, y md5 de las tres copias de `data\` del auditor idéntico a `git show db0dfe847:data/mirova_equivalent/<v>.json`). Checkout local en 16ef350ed (rama loop/activo); `volcanoes.yaml` local igual al de origin/main salvo fin de línea.
- Modelo y esfuerzo: Claude Opus 5.5, esfuerzo por defecto de la sesión del verificador.
- CARPETA: C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s160_espacial\verificador\
- Caminos escritos antes de abrir nada: C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s160_espacial\verificador\caminos.md (sha256 2f6ea22f0a049f37f778b105b42101138f2e0dd9643b44929a891ffd904b1a5e, 16:57:37 GMT).
- Lo que NO miré: el INFORME.md y el hallazgos.csv del auditor (a propósito); el código del pipeline (`pipeline/`) ni el del frontend más allá de lo que ejecuta `banco_paridad`; la fidelidad del port del código de MIROVA (oráculo S159) contra el MATLAB original; MODIS en los TIF; los otros ocho volcanes salvo Lascar e Isluga como controles; la naturaleza física de las fuentes lejanas (no hay mapa ni DEM en mi sesión); los TIF posteriores al 2026-09-20 (no hay en disco: el índice remoto termina el 2026-09-20 y ningún directorio tiene TIF del 28-29 de septiembre ni del 21 de octubre).
- Re-corrida del auditor: copié 01, 02a, 02b, 02c, 02d, 03, 03b, 03d, 03e y 04 a `verificador\rerun\` con sólo las rutas cambiadas. Todas las salidas son idénticas byte a byte a las del auditor, salvo una línea de encabezado («caja del oraculo: ...») que falta en el `02a_oraculo_v750_posicion_salida.txt` guardado por el auditor (lo generó una versión anterior del script; el contenido es el mismo).

## 2. En una pantalla

1. La geometría base se sostiene: el cráter está a 4,79 km al NW (Tupungatito) y 7,61 km al N (Cordón Caulle) del centro del TIF, el calor que MIROVA alerta cae casi siempre en el cráter, y nuestro cúmulo está en el mismo lugar. Lo que nos separa de MIROVA en estos tres volcanes no es la posición del cráter.
2. La incoherencia del mapa de Cordón Caulle es superposición. 51 de los 64 píxeles caen en dos celdas del cráter, tapadas por la estrella. Los cuadrados del sur son 10 píxeles de una sola pasada (2026-10-21 05:48, NOAA-21), donde MIROVA alertó a 6,45 km del centro y nosotros publicamos 1,42 MW a 10,1 km al SW del cráter: esa alerta no está en el cráter.
3. Varios números no salen como se enuncian. 8 de los 62 TIF de Tupungatito y 10 de los 78 de Cordón Caulle están pareados con la alerta de otra pasada. El anillo de MIROVA se usa simétrico (±7,875 km) cuando en realidad es +8,625 al N y −7,125 al S, así que el contrafactual pierde 2 alertas y no 3, y una de las tres era un cúmulo en el cráter. MODIS da 26 negativos a más de 2 km, no 28. 9 de las 59 no publicadas no son «1 píxel en el cráter con 0 MW».
4. E-01 (0 de 10 y 0 de 48 con la caja por defecto) se reproduce desde el JSON crudo. Es un hecho del port, y no prueba qué caja usa MIROVA en producción.
5. Lo nuevo y más grave es SOSPECHA: la protegida de Tupungatito del 2026-09-29 04:54 (Suomi NPP, 1,86 MW). En esa pasada nuestro único píxel es de 1,11 MW, con 302 K, a 9,42 km al ENE del cráter, fuera del inner de 7 km y nada en el cráter. Puede ser la misma fuente que alertó MIROVA, y entonces sería una protegida perdida por radio.

Informe: C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s160_espacial\verificador\INFORME.md

## 3. Veredictos por afirmación

Las dos preguntas del instrumento van en el encabezado de cada script mío (`v01` a `v10`). Denominador y ventana van en cada cifra.

### Afirmación 1: el calor de MIROVA está en el cráter y no en el centro del TIF. CONFIRMADO EN PARTE, gravedad propia 2

- **Desfase entre el cráter y el centro del TIF: CONFIRMADO.** Medido con geodésica WGS84, que no es la haversine del auditor. El centro del TIF lo leí con rasterio (bounds iguales en hasta 40 TIF 4326 por volcán): Tupungatito 4,790 km, rumbo 327 (NW); Cordón Caulle 7,612 km, rumbo 341 (N); Isluga 0,061 km. Contra el centro de la grilla de MIROVA (objetivos.json del censo) da 4,851 y 7,618 km. Salida: `v01_oraculo_posicion_salida.txt`.
- **Distancia_km p50 5,21 (n = 154) y 8,10 (n = 197): CONFIRMADO.** Son las filas de la tabla, VIIRS 375 nocturno, del 2026-01-10 al 2026-10-18. La re-corrida es idéntica (`rerun\01_distancia_mirova_salida.txt`).
- **Foco del TIF a 0,36 km y 60 % (n = 62) en Tupungatito; 0,68 km y 74 % (n = 78) en Cordón Caulle: CONFIRMADO EN PARTE.** El script los reproduce, pero el pareo de 02b mezcla pasadas: ver VE-05. Con mi re-pareo a 120 s, sin prioridad de tipo, quedan Tupungatito p50 0,36 km con 65 % a 1 km o menos (n = 55) y Cordón Caulle 0,68 km con 81 % (n = 68). Los TIF mal pareados (|dt| > 10 min) dan foco a 6,9 y 6,1 km del cráter. La conclusión sale reforzada y los números cambian. Los 62 y 78 TIF con ALERTA son todos nocturnos (`v09_dia_noche_tif_salida.txt`). El control RUTINA nocturno queda en 5 % (Tupungatito) y 13 % (Cordón Caulle) a 1 km o menos, así que el instrumento distingue. El control A109 está en la afirmación 2.
- **Píxel del código de MIROVA a 0,54 km (n = 7) y 0,48 km (n = 64): CONFIRMADO en el número, con dos precisiones.** (a) Son píxeles del oráculo con anillo sensible (O-sens), una versión modificada del código. Con la caja por defecto el código marca 0 píxeles en los dos volcanes, como muestra la afirmación 3, y la afirmación 1 no lo dice. (b) n son píxeles, no pasadas: en Cordón Caulle son 64 píxeles en 41 pasadas. Calculé lat/lon desde el JSON crudo del censo con mi propia conversión. La diferencia con el CSV 02a es de 0,6 m o menos, y mi distancia en metros UTM difiere 4,9 m o menos de la distancia en celdas que guarda el propio oráculo.
- **La incoherencia del mapa se resuelve como superposición, no como error del número.** De los 64 píxeles, 28 están en la celda (23,30), a 0,27 km al W del cráter, y 23 en la (23,31), a 0,48 km al E. Esas dos celdas quedan bajo la estrella dorada y los cuadrados magenta. Los cuadrados visibles cerca de -40,62 / -72,18 son 10 píxeles de **una sola pasada** (2026-10-21 05:48, VIIRS_NOAA21_750), más uno a 2,85 km de la misma pasada. La otra pasada con un píxel lejano (2026-04-07 05:42) tiene también uno en el cráter y otro a 17,1 km al SE. La figura está bien dibujada y el número también: induce a error porque un marcador por píxel hace que una sola pasada pese 11 marcadores contra 2 visibles para 40 pasadas. Ver VE-02 para lo que pasa en esa pasada.
- **Isluga en el centro y 0,8 a 1,0 km al SW del yaml: CONFIRMADO por tres instrumentos.** Foco del TIF p50 0,85 km, con 3 % a 0,6 km o menos (subconjunto de 66 TIF de `v03`, parte b) y octante SW o S (02b, re-corrido). Píxeles del oráculo en las celdas (34,33) y vecinas, a 1,03 km al S/SW (`v01`). Nuestro cúmulo p50 0,82 a 0,91 km, SW (`03`). No verifiqué cuál de los dos está bien, el yaml (-19,15 / -68,83, números redondos) o el cráter físico.
- **Excepciones a «el calor está en el cráter».** Una, CONFIRMADA: Cordón Caulle 2026-10-21 05:48 (VE-02). Otra, SOSPECHA: Tupungatito 2026-09-29 04:54 (VE-01).

### Afirmación 2: nuestro cúmulo a 0,19 a 0,48 km del foco; 0 de 876 perdidas por geometría; las 58 son de 1 píxel en el cráter con 0 MW. CONFIRMADO EN PARTE, gravedad propia 2

- **Distancia entre el cúmulo y el foco: CONFIRMADA, con matiz A109 (VE-11).** En la misma pasada da 0,23 (Tupungatito), 0,49 (Cordón Caulle) y 0,21 km (Isluga). Contra el cúmulo de otra pasada de la misma noche (45 a 120 min) da 0,47, 0,52 y 0,59 km. Contra una noche al azar da 0,39, 0,74 y 0,61 km. Los n son 44, 67 y 66 TIF (`v03_pareo_y_a109_salida.txt`). Parte de lo ajustado de la cifra de la misma pasada viene del gránulo compartido. La conclusión de posición se sostiene en todos los controles, siempre bajo 1 km.
- **876 alertas pareadas a 120 s: CONFIRMADO, y el pareo es robusto.** De 1.010 filas ALERTA nocturnas (CONS y OCR por separado), 1.004 se parean a 10 s o menos. La cuenta no cambia entre 30 y 900 s, y las 6 restantes no tienen record a menos de 15 min (`v10_tolerancia_pareo_records_salida.txt`).
- **«0 de 876 por etiqueta, radio o elección de cúmulo»: CONFIRMADO en el efecto, con el instrumento vivo.** El clasificador de 03 sí produce `perdida_geometria:far` (5 filas en negativos limpios de Cordón Caulle MODIS), así que su cero en las alertas no es un cero ciego. Pero su propia salida muestra **1** fila `perdida_geometria:cumulo_elegido_lejos_o_0MW` (Isluga 2026-07-28 06:12). Al mirarla, el cúmulo elegido es el píxel del cráter, con pc.vrp 0,0 y el píxel en 0,0001 MW: es de la misma clase que las 58, no una elección de cúmulo. La cobertura del radio en Tupungatito queda abierta por VE-01, que no entra en las 876 como pérdida de geometría porque 03 la clasifica `perdida_deteccion:foco_lejano`.
- **«Las 58 son cúmulos de 1 píxel en el cráter con 0,0 MW»: CONFIRMADO EN PARTE, 50 de 59 (VE-07).** Fuente: `v06_no_publicadas_y_odef_salida.txt` y `v06_perdidas_geometria.csv`.

### Afirmación 3 (E-01): caja por defecto 0 de 10 y 0 de 48 (0 de 8 protegidas); anillo sensible 7 y 41. CONFIRMADO, gravedad propia 2

- Contado por mi cuenta en el JSON crudo del censo (`v06`, parte B). Con la caja por defecto, Tupungatito da 10 pasadas pos vacías y Cordón Caulle 48 vacías, las 58 con (n_abs, n_p1, n_p2) = (0, 0, 0): ni un píxel pasa el primer test. Con el anillo sensible marcan 7 y 41. Las protegidas de Cordón Caulle son 8. Controles positivos con la caja por defecto: Lascar 125 de 125 e Isluga 33 de 35.
- Precisión de interpretación (SOSPECHA): MIROVA sí alertó esas 58 pasadas. Lo que esto prueba es que el código tal como se portó, con la caja por defecto centrada en la grilla, no reproduce a MIROVA en esos dos volcanes. No prueba que MIROVA use el anillo sensible: también puede ser otra caja, otro centro o una diferencia del port, que la memoria del proyecto da como «sin verificar».

### Afirmación 4 (E-02): negativos limpios publicados en Cordón Caulle y el contrafactual del anillo. CONFIRMADO EN PARTE, gravedad propia 2

- VIIRS 375, 30 de 38 a más de 2 km y 26 fuera del anillo: CONFIRMADO, por precisión completa y por la forma real.
- VIIRS 750, 13 de 30 y 12: CONFIRMADO.
- **MODIS, 28 de 38 a más de 2 km: REFUTADO.** La salida del propio auditor (`03d_negativos_pcc_salida.txt`, contando sus líneas) da 26, y mi cuenta a precisión completa también da 26. «21 fuera del anillo»: sale 21 sólo con el anillo simétrico a precisión completa. La salida 03d del auditor da 19 porque usa lat/lon redondeadas a 0,01° (VE-04), y la forma real del anillo da 20 (VE-03).
- **«Perdería 3 alertas de 266 (0 protegidas)»: CONFIRMADO EN PARTE.** Con el anillo real (filas 22 a 42 de la grilla) se pierden **2**. La tercera (2026-03-28 04:42, MIROVA 0,15 MW) es un cúmulo a 0,79 km del cráter, en la fila 22, que el anillo simétrico deja fuera por 37 m (dN 7,912 km contra el borde de 7,875, medido sobre el centroide del JSON). Protegidas: 0 en las dos cuentas. Fuente: `v05_negativos_anillo_salida.txt`.

### Afirmación 5 (E-04, E-08): fuente persistente a 10,7 km al E de Cordón Caulle; focos débiles al N. CONFIRMADO EN PARTE, gravedad propia 1

- Las cifras salen: 15 de 161 TIF RUTINA, prominencia p50 10,0, posición mediana -40,5297 / -72,0192, a 10,77 km del cráter, con dispersión de 0,54 km.
- **Pero la palabra «persistente» no se sostiene así (VE-08).** 13 de esas 15 RUTINA son TIF **diurnos** (17:36 a 19:54 UTC), y 19 de las 23 apariciones en esa celda caen entre el 2026-05-09 y el 2026-05-18, aunque hay TIF diurnos de Cordón Caulle también en junio (7), julio (10) y septiembre (24). Los 10 sigma son prominencia diurna. En las 4 noches con ALERTA en que el máximo del TIF cayó ahí, la Distancia_km de MIROVA (7,65 a 8,02) apunta al cráter, no a la fuente (10,6 km del centro). Nuestro pipeline no tiene píxel anómalo a 1 km o menos de ese foco en ninguno de los 23 TIF, y tiene en 63 de 108 en la celda del cráter, que es el control (`v08_fuente_persistente_salida.txt`, `v09_dia_noche_tif_salida.txt`).
- Focos al N, CONFIRMADO como débiles (~4 sigma). En Isluga son 22 TIF, 18 nocturnos; en Tupungatito, 21 TIF, 12 diurnos. En las pasadas con ALERTA, la Distancia_km de MIROVA apunta al cráter, no a esos focos (`v08b_focos_norte_salida.txt`).

### Afirmación 6 (E-06): las dos protegidas de Tupungatito no publicadas son filas sólo OCR de Suomi NPP con geometría de otra pasada. CONFIRMADO EN PARTE, gravedad propia 3

- Sólo OCR y Suomi NPP: CONFIRMADO. A esa hora no hay ninguna fila de la tabla, y nuestros records de esas horas son `VIIRS_SNPP`.
- Geometría de otra pasada, 2026-09-28 05:18 (2,51 MW, 5,27 km): CONFIRMADO como compatible. 5,27 es exactamente la Distancia del OCR de la pasada NOAA-20 de las 05:36 (ALERTA 0,09 MW). En nuestro record de 05:18 el único píxel está a 21,56 km al NE.
- Geometría de otra pasada, 2026-09-29 04:54 (1,86 MW, 5,68 km): **SIN DATO.** Ninguna otra fila de esa noche tiene 5,68 (la tabla de las 05:18 da 5,41). Y aparece VE-01.

## 4. Hallazgos propios (orden por gravedad)

**VE-01**
- TÍTULO: La protegida de Tupungatito del 2026-09-29 04:54 (Suomi NPP, 1,86 MW) puede estar en una fuente a 9,4 km al ENE del cráter que nuestro radio de 7 km descarta
- ARCHIVO:LÍNEA: `data\Tupungatito.json` (db0dfe847), record `2026-09-29 04:54` VIIRS_SNPP; referencia `registro_vrp_ocr` fila ALERTA_TERMICA_OCR 2026-09-29 04:54:00 (1,86 MW, 5,68 km). Salida: comando de abajo.
- QUÉ PASA: Esa noche hubo una fuente caliente intensa a 9,42 km al ENE del cráter: un píxel de 302 K y 1,11 MW, a 9,03 km del centro del TIF, y nada en el cráter. MIROVA publicó 1,86 MW en esa misma pasada, sólo por OCR. Según el hito A119 de Suomi NPP, el VRP del OCR es de su pasada y la distancia puede ser de otra. Si las dos son la misma fuente, MIROVA la alertó dentro de su recuadro y nosotros la etiquetamos `far` por estar fuera del inner de 7 km medido desde el cráter: sería una protegida perdida por radio.
- CÓMO SE VE EN EL DASHBOARD: invisible. El record es `far` y el tablero no lo publica.
- CÓMO REPRODUCIRLO: `python -c` sobre `data\Tupungatito.json`, record `2026-09-29 04:54` (sensor VIIRS_SNPP, `primary_cluster` 1,112 MW en -33,36927 / -69,72791); la fila OCR sale de `referencia_mirova_unificada.cargar_referencia_unificada()`. Volcán Tupungatito, pasada 2026-09-29 04:54 UTC. Para ubicar la celda en la grilla de MIROVA, la transformación de `v05_negativos_anillo.py` (función `celda`) sobre esas coordenadas.
- CONFIANZA: SOSPECHA. No hay TIF de esa fecha en disco y la distancia del OCR no la ubica (5,68 no corresponde a 9,03).
- GRAVEDAD: 3. Una protegida de 1,86 MW es una alerta que el criterio de victoria no deja perder.

**VE-02**
- TÍTULO: Cordón Caulle 2026-10-21 05:48 (NOAA-21, VIIRS 750): MIROVA alertó una fuente a 10-12 km al S/SW del cráter, no el cráter; explica los cuadrados del sur del mapa
- ARCHIVO:LÍNEA: `v01_oraculo_posicion_salida.txt` (bloque PuyehueCordonCaulle, pasadas con píxel a más de 1,5 km); `_censo_s159\objetivos.json` (hora 2026-10-21 05:48: ALERTA_TERMICA CONS 0,36 MW a 6,45 km; pc_vrp 1,418; pc_dist 10,135; pub_prod 1); `03_pareo_geometria_pasadas.csv` (fila PuyehueCordonCaulle,VIIRS750,2026-10-21 05:48: lab sin_info).
- QUÉ PASA: Esa pasada tiene calor real lejos del cráter. El oráculo O-sens marca 10 píxeles a 8,9-12,1 km al S/SW del cráter, a 5,4-7,8 km del centro de la grilla, y ninguno en el cráter. MIROVA da Distancia 6,45 km, que cuadra con esos píxeles y no con el cráter (7,5-7,7 km de la celda). Nuestro pipeline publicó un cúmulo de 3 píxeles con 1,42 MW a 10,1 km al SW. Como la referencia local del auditor llega al 2026-10-18, en 01, 02b y 03 esa pasada aparece `sin_info`; sólo el censo la etiqueta `pos`. La afirmación 1 («el calor está en el cráter») tiene ahí una excepción reciente.
- CÓMO SE VE EN EL DASHBOARD: visible. Una detección de 1,42 MW en Cordón Caulle el 21-oct marcada `summit`, porque el inner de 20 km la cubre, aunque está a 10 km del cráter.
- CÓMO REPRODUCIRLO: `python verificador\v01_oraculo_posicion.py`, desde la carpeta del verificador. Volcán Cordón Caulle, 2026-10-21 05:48 UTC.
- CONFIANZA: CONFIRMADO (el oráculo, MIROVA y nuestra detección coinciden en que es lejos del cráter). La naturaleza de la fuente es SOSPECHA: no hay TIF y no miré otras pasadas posteriores.
- GRAVEDAD: 2.

**VE-03**
- TÍTULO: El anillo de MIROVA se modela simétrico (±7,875 km N-S) cuando la forma real es +8,625 km al N y −7,125 km al S
- ARCHIVO:LÍNEA: `comun.py:43` (`ANILLO_KM = 10.5 * 0.75`), usado en `04_contrafactuales.py:87-88`, `03d_negativos_pcc.py:22` y `05_mapas.py:69`. La forma real está en `git show origin/main:experiments/_s158_audit_r2/a113/m08_box_forma.txt`, TEXTO: «BOX==1 es rectangulo filas 22-42 x cols 24-42 menos la caja: True 350». Con la celda central 33, eso son 11 filas al N y 9 al S.
- QUÉ PASA: En Cordón Caulle el cráter está a 7,6 km al N del centro, justo junto al borde norte del anillo simétrico. El borde real está 0,75 km más al norte. El contrafactual R3 apaga un cúmulo del cráter (2026-03-28 04:42, a 0,79 km del cráter, fila 22) que el anillo real conserva: se pierden 2 alertas, no 3. En MODIS, los negativos fuera del anillo dan 20 y no 21. El mapa dibuja el anillo con el borde norte rozando el cráter, y eso puede llevar a concluir que el recuadro de MIROVA corta el cráter.
- CÓMO SE VE EN EL DASHBOARD: invisible. Afecta el análisis que decide la geometría, no producción.
- CÓMO REPRODUCIRLO: `python verificador\v05_negativos_anillo.py`, Cordón Caulle, VIIRS 375, pasada 2026-03-28 04:42 UTC.
- CONFIANZA: CONFIRMADO, suponiendo que la fila 0 de la caja es el norte, que es como la usa `probe_n.py` (ys = ul_y − 750·(fila+0,5)). Que el MATLAB de MIROVA oriente igual no lo verifiqué.
- GRAVEDAD: 2.

**VE-04**
- TÍTULO: El CSV de 03 redondea pc_lat/pc_lon a 0,01° y 03d y el mapa usan esas coordenadas
- ARCHIVO:LÍNEA: `03_pareo_geometria.py:154` (`f"{r[c]:.2f}" if isinstance(r[c], float)`), consumido en `03d_negativos_pcc.py:20-22` y en `05_mapas.py:94` y siguientes.
- QUÉ PASA: La posición del cúmulo queda en una grilla de ~1,1 km N-S por ~0,85 km E-O. Los marcadores de nuestros cúmulos en los tres mapas están corridos hasta ~0,5 km, que es la escala de la pregunta. El conteo de «fuera del anillo» de 03d en MODIS da 19 en vez de 21 (simétrico, precisión completa). Las distancias pc_dvent y pc_dtif de 03 se calcularon antes de redondear y están bien. 04 lee el JSON y no está afectado.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python verificador\v05_negativos_anillo.py` (columna «simetrico con lat/lon del CSV» contra «simetrico a precisión completa», Cordón Caulle MODIS, pasadas 2026-04-04 07:25, 2026-06-08 07:45 y 2026-07-27 01:25 UTC).
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2.

**VE-05**
- TÍTULO: 02b parea cada TIF con la fila de MIROVA a ±30 min con prioridad ALERTA: hay TIF etiquetados ALERTA por la alerta de otra pasada
- ARCHIVO:LÍNEA: `02b_tif_v375_posicion.py:153-154`.
- QUÉ PASA: Los satélites VIIRS pasan con 18 a 50 min de diferencia. Un TIF de una pasada sin alerta hereda la alerta de la vecina: 8 de 62 (Tupungatito), 10 de 78 (Cordón Caulle) y 21 de 97 (Isluga) tienen |dt| > 10 min. Re-pareados a 120 s, entre los TIF que 02b llama ALERTA quedan 6, 10 y 13 RUTINA de su propia pasada, más 1, 0 y 3 sin fila u otra. Esos TIF tienen el foco lejos del cráter (p50 6,9 / 6,1 / 3,5 km) y bajan las cifras de «foco en el cráter».
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python verificador\v03_pareo_y_a109.py` (parte a).
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2. La dirección de la conclusión no cambia; sí sus números.

**VE-06**
- TÍTULO: «MODIS 28 de 38 a más de 2 km» no sale de ningún instrumento
- ARCHIVO:LÍNEA: `03d_negativos_pcc_salida.txt` (sección PCC MODIS, 38 líneas).
- QUÉ PASA: Contando las líneas de la salida del propio auditor dan 26 a más de 2 km y 19 fuera del anillo. Mi cuenta a precisión completa da 26 y 21 (simétrico) o 20 (forma real). Ninguna cuenta da 28.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python verificador\v05_negativos_anillo.py`, Cordón Caulle MODIS.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 1.

**VE-07**
- TÍTULO: De las 59 alertas no publicadas que 03 clasifica como geometría, 9 no son «1 píxel en el cráter con 0 MW», y 2 son pérdidas de detección
- ARCHIVO:LÍNEA: `03_pareo_geometria.py:121` y `:125` (`cerca` = dentro del inner, 20 km en Cordón Caulle). Salida: `v06_no_publicadas_y_odef_salida.txt`.
- QUÉ PASA: Hay 3 casos con cúmulos de 2 píxeles en el cráter (Tupungatito 2026-03-04 05:12; Isluga 2026-02-24 05:54 y 2026-04-11 05:12). En 2 de Cordón Caulle VIIRS 750 (2026-02-01 05:12 y 2026-04-30 06:06) el único píxel está a 3,25 y 17,62 km del cráter mientras MIROVA alertó a 7,83 km del centro, o sea en el cráter: no detectamos el cráter, y el clasificador lo llama geometría sólo porque el píxel cae dentro de 20 km. En 4 de Isluga VIIRS 375 (2026-02-02 06:06, 2026-06-30 05:18, 2026-09-19 05:42 y 2026-09-22 04:48) el cúmulo elegido está lejos (`far`, 7,9 a 22,8 km, 0,03 a 0,41 MW) y el píxel del cráter está en 0 MW. Elegir el del cráter tampoco publicaría, así que no son pérdidas por elección. Además está la fila `cumulo_elegido` de Isluga del 2026-07-28 (afirmación 2).
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python verificador\v06_no_publicadas_y_odef.py`, en las pasadas listadas.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 1. No cambia el «0 por geometría» en efecto.

**VE-08**
- TÍTULO: La «fuente persistente» a 10,7 km al E de Cordón Caulle es casi toda diurna y de mayo
- ARCHIVO:LÍNEA: `v08_fuente_persistente_salida.txt` y `v09_dia_noche_tif_salida.txt`.
- QUÉ PASA: 13 de las 15 RUTINA y 19 de las 23 apariciones son entre el 9 y el 18 de mayo, la mayoría entre 17:36 y 19:54 UTC (tarde local). Los 10 sigma son de día. En las noches con ALERTA en que el máximo cae ahí, MIROVA apunta al cráter. Ningún píxel nuestro cae a 1 km de ese foco.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python verificador\v08_fuente_persistente.py` y `python verificador\v09_dia_noche_tif.py`.
- CONFIANZA: CONFIRMADO en la composición. La naturaleza física queda SIN DATO.
- GRAVEDAD: 1.

**VE-09**
- TÍTULO: «píxel del código de MIROVA» en la afirmación 1 es el oráculo con anillo sensible, no el código por defecto
- ARCHIVO:LÍNEA: `02a_oraculo_v750_posicion.py`, que por defecto toma `CAJA = "geo_linear_anillo_sensible"`; `_censo_s159\probe_n.py:61-65` (`if sensible_anillo: b[b == 1] = 2`).
- QUÉ PASA: Las posiciones de 0,54 y 0,48 km son de una versión que trata todo el anillo como cumbre. El código con la caja por defecto marca 0 píxeles en Tupungatito y Cordón Caulle. Es correcto como «dónde marcaría si el anillo fuera sensible», no como «dónde marca MIROVA». La Distancia_km de MIROVA en esas pasadas sí cuadra con esas celdas (|dif| de 0,8 km o menos en el 80 % de los 64 píxeles).
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python verificador\v01_oraculo_posicion.py` (bloque «caja geo_linear»: SIN DATO, 0 píxeles).
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2. Puede leerse como evidencia de producción de MIROVA, y no lo es.

**VE-10**
- TÍTULO: Control A109: la coincidencia de 0,19 a 0,49 km en la misma pasada se abre a 0,47 a 0,59 km con otra pasada de la misma noche
- ARCHIVO:LÍNEA: `v03_pareo_y_a109_salida.txt` (parte b).
- QUÉ PASA: El TIF de MIROVA y nuestro record comparten gránulo, y con eso la grilla de píxeles. Parte de lo ajustado viene de ahí. La posición en el cráter se sostiene igual.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python verificador\v03_pareo_y_a109.py`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 1.

**VE-11**
- TÍTULO: 03 imprime «alertas sin record: 3» cuando son 6
- ARCHIVO:LÍNEA: `03_pareo_geometria.py:218` (`len(sin_record)` de un diccionario: cuenta claves volcán-sensor, no alertas).
- QUÉ PASA: El total real es 6 (3 de Cordón Caulle, 2 de Isluga y 1 de Tupungatito, todas VIIRS 375), como da 03e. Mi v10 lo confirma: 1.004 de 1.010 filas pareadas.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python verificador\v10_tolerancia_pareo_records.py`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 1.

**VE-12**
- TÍTULO: El mapa rotula el fondo como «BT MIR, K» y el TIF trae valores de 0,07 a 0,46
- ARCHIVO:LÍNEA: `05_mapas.py:108`; columna `bt_max` de `02b_tif_v375_focos.csv` (0,2 a 0,7).
- QUÉ PASA: Los GeoTIFF VIIRS 375 de MIROVA son float64 escritos por MATLAB con valores de radiancia, no K. Lo leí con rasterio en 3 TIF de Cordón Caulle. Es sólo una etiqueta: no afecta posiciones.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: leer cualquier `mirova-tif-archive\data\tif\PuyehueCordonCaulle\*VIIRS375*.tif` con rasterio.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 1.

## 5. SEGUIMIENTOS (fuera del eje, no perseguidos)

- Cordón Caulle MODIS: 5 negativos limpios con `distance_class = far` y el cúmulo primario dentro del inner de 20 km (15,7 a 18,0 km del cráter, 0,58 a 1,70 MW), no publicados. Es la asimetría A46 entre final_hotspot y primary_cluster. Filas de `03_pareo_geometria_pasadas.csv`: PCC MODIS 2026-03-01 07:05, 2026-03-14 01:50, 2026-05-03 07:50, 2026-06-22 08:25 y 2026-10-12 02:20. Confianza CONFIRMADO en el dato, SOSPECHA en la causa.
- Cordón Caulle VIIRS 750, 2026-10-10 05:54: protegida de 1,19 MW (CONS) perdida por detección. Producción no tiene cúmulo y el oráculo O-sens marca píxeles en el cráter (0,27 W y 0,48 E). Fuente: `03b_protegidas_salida.txt` y `02a_oraculo_v750_posicion_salida.txt`. CONFIRMADO.
- Señales recurrentes al S de la cumbre del Puyehue (-40,61 a -40,63 / -72,14 a -72,21). Aparecen el 2026-10-21 05:48 (VE-02), en un píxel del oráculo en un negativo limpio el 2026-10-09 06:54 (-40,6335 / -72,1447) y en focos del TIF con ALERTA en el mapa. Vale revisar las pasadas posteriores al 21-oct. SOSPECHA.
- Las dos referencias no tienen el mismo corte: el censo S159 etiqueta hasta el 2026-10-21 y la referencia local que usan 01, 02b y 03 llega al 2026-10-18. La «ventana 2026-01-10 a 2026-10-21» de 03 tiene 3 días sin etiqueta (A90).
- `comun.py`: el docstring dice esquina del anillo «~11,1 km» y `ANILLO_ESQUINA_KM` vale 10,62; 01 imprime «esq 11,1» en las filas pero usa 10,62. Con la forma real, las esquinas son 11,19 al N y 10,08 al S.

## 6. VERIFICADO LIMPIO

- Copias de datos del auditor = origin/main db0dfe847 = remoto a las 16:58 UTC. Vara: `gh api repos/MendozaVolcanic/VRP-chile/commits/main` y md5 contra `git show db0dfe847:...`.
- Reproducibilidad: los 10 scripts del auditor re-corridos en `verificador\rerun\` dan salidas idénticas, y el CSV 03 re-corrido coincide en lab y pub en 8.828 de 8.828 filas (`v05`, línea de control). Vara: diff de texto sin CR.
- Conversión fila/col a lat/lon del oráculo: 0,6 m o menos contra el CSV 02a y 4,9 m o menos contra la distancia en celdas del propio oráculo. La celda (33,33) queda a 265 m del centro de la grilla (`v01`). Vara: transformación propia más geodésica WGS84.
- Georreferencia de los TIF: todos los TIF 4326 de cada volcán tienen bounds y resolución idénticos. En escenas despejadas (r 0,70 a 0,99), el desplazamiento contra la mediana nocturna es 0 o ±1 píxel; las escenas con r < 0,35 son nubes y no informan. El control positivo (mediana corrida 2 filas) recupera (2, 0). Rasgo fijo absoluto, el cráter de Lascar: desplazamiento mediano del máximo −0,06 km E y +0,11 km N, con n = 49 TIF nocturnos de 8 sigma o más dentro de 5 km; menos de un tercio de píxel (`v02_georef_tif_salida.txt`, `v02b_sesgo_lascar_salida.txt`). Vara: vent de Lascar en volcanoes.yaml.
- Pareo record-MIROVA a 120 s: 1.004 de 1.010 filas a 10 s o menos, sin cambios entre 30 y 900 s (`v10`).
- Los TIF con ALERTA de Tupungatito y Cordón Caulle son todos nocturnos, y el control RUTINA nocturno sigue lejos del cráter (`v09`).

## 7. SIN DATO

- Dirección de la fuente de VE-01 y de VE-02 en la imagen de MIROVA: no hay TIF en disco después del 2026-09-20 (índice `experiments\_s147_tif\index_remoto.csv`: máximo 2026-09-20 para los 11 volcanes; glob vacío en los 5 directorios de TIF para el 28-29 de septiembre y el 20-21 de octubre).
- Si el yaml de Isluga o el cráter físico es el que está corrido: sin mapa ni DEM en la sesión.
- Orientación norte-sur de la caja en el MATLAB original de MIROVA (VE-03 supone la del port).

## 8. FUERA DE ALCANCE

- Fidelidad del port del código de MIROVA (oráculo S159).
- Por qué la caja por defecto no marca nada (umbrales de escena en el anillo): es pregunta de detección.
- Naturaleza física de las fuentes lejanas (E de Cordón Caulle, S del Puyehue, ENE de Tupungatito, N de Isluga).
