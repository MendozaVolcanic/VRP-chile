# Verificador de CM162-01, CM162-02 y CM162-03 (cúmulo por vecindad de matriz)

- Hora del servidor GitHub al empezar: Sat, 24 Oct 2026 14:31:13 GMT.
- Commit medido: `origin/main` = `80b819828f16e19ceacbd21dc7c4e474d46122b4` (2026-10-24 14:21:51 UTC, posterior a e850152b). Código, datos de los 11 Tier A, `frontend/index.html`, `docs/MIROVA_DIVERGENCES.md`, `docs/AUDIT_S155.md` y la referencia `data/mirova_reference/mirova_v1_snapshot/` extraídos con `git archive` a `CARPETA\src\`. Árbol de trabajo (rama loop/activo) no leído.
- Modelo y esfuerzo: Claude Opus 5.5, esfuerzo bajo por configuración de la sesión, compensado con controles en cada medición.
- Caminos escritos antes de releer: `CARPETA\caminos.md`, sha256 `f923e82f5b528b0e54b925204bec5c06d40f567d2114da0e5678ca808811d786`.
- Qué NO miré: MODIS (process_modis.py y sus cúmulos), el cuerpo de `process_viirs.py` (el número publicado de VIIRS 375 lo verifiqué contra el campo persistido `f5_core_vrp_mw`, no contra el código del procesador), los artefactos del A/B de D25 (el brazo K de las ventanas), los gránulos L1B (prohibido bajarlos), y el razonamiento del auditor original (a propósito).
- Toda la medición usa los records de producción, que en las 11 series están escritos con código K (campo `regimen.codigo_sha`, histórico reprocesado). "Ventanas K" = V1 (2026-08-29 a 2026-10-18) más V2 (2026-04-01 a 2026-06-12), del PREREGISTRO de D25.

CARPETA = `C:\Users\nmend\AppData\Local\Temp\claude\C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile\a3efc9fd-8a35-470a-aad1-531abaec64d8\scratchpad\vuelta2\verificador_matriz`

## En una pantalla

1. CM162-01 CONFIRMADO EN PARTE: el mecanismo (cúmulo = componente 8-conexa de la matriz) y los casos Láscar 05-05 06:06 (0,932 a 1,001) y Chillán 10-14 06:18 (1,173 a 1,890) se reproducen; en K cambian 7 a 13 de 290 publicaciones V750 según el umbral (8 con 0,7 km), todas hacia arriba (por construcción), sólo Láscar 05-05 es protegida que cruza 1 MW. Los denominadores 338, 82 y 2.070 y el «61» no se reproducen (yo: 290, 86, 1.769 y 41 a 55). Control a nadir: 0 cambios bajo 20° con cualquier umbral.
2. CM162-02 CONFIRMADO: f5_core no cambia en 0 de 153 pasadas fragmentadas de K (control positivo 147 de 153 sí cambia); la fracción con ajeno a menos de un paso sube de 4/78 bajo 10° a 44/91 entre 50 y 60°. El centroide torcido se mueve 0,1 km de mediana: gravedad 1, no 2.
3. CM162-03 CONFIRMADO EN PARTE: la geometría de los dos casos sí; pero en Láscar 2025-07-07 lo publicado es el máximo (1,553), no la suma, y en Chillán 10-01 los dos píxeles tienen BT distinta (298,64 y 292,28 K): 4,2 MW es una cota, y la MIROVA de 10,0 es sólo OCR y queda más lejos si se resta.
4. Afirmación 4 CONFIRMADA EN PARTE: la causa de CM162-01 (matriz contra terreno) no está nombrada, pero su síntoma es AUDIT_S155 F5-01 y su cura es D17 (remuestreo) con D32; CM162-03 SÍ está catalogada: `docs/DISENO_D17_REMUESTREO_UTM.md` §4.3 («solape residual entre barridos que hoy cuenta doble»), F5-09 (VIIRS 375) y V5-02 (VIIRS 750). Lo nuevo es la instancia VIIRS 750 a cenit bajo (11° y 22-24°).
5. Hallazgo propio principal (VM162-01): pegar no es neutro; en K sube un negativo limpio de 0,447 a 3,03 MW (PCC 2026-06-11 06:18, MIROVA RUTINA), y 25 de 70 píxeles pegados en la historia solapan más de media huella con otro del grupo: los valores pegados en modo suma son cota superior. Un A/B tiene que contar negativos y deduplicar.

## Veredictos

### CM162-01: CONFIRMADO EN PARTE. Gravedad propia 3

**Lo que se sostiene, con evidencia de esta sesión:**

- Código (leído en `CARPETA\src\pipeline\`):
  - `clustering.py:91-96`: con `connectivity=8` (valor por defecto, l. 38) la estructura es `np.ones((3,3))` y `ndi_label(hot_mask_2d, structure=structure)` etiqueta sobre índices de la matriz. No hay dilatación previa. VIIRS 750 llama sin `connectivity` (`process_viirs_mod.py:1098-1102`), o sea 8.
  - `clustering.py:143-158`: `vent_anchored` rankea primero los cúmulos con `vrp_mw > 0` (l. 143-147) y entre ellos por (dentro del radio interno, distancia del centroide, -vrp). La afirmación omite el filtro de vrp > 0, que no cambia el punto.
  - `single_pixel_mode.py:161-183`: publica `max(per_pixel_vrp)` del cúmulo elegido sólo si `vrp_mw < 5` y `n_pixels <= 3` (flags leídos con `VRP_PROFILE=mirova_equivalent` de `pipeline.profile`: `ENABLE_SINGLE_PIXEL_SUB_MW_MODE True`, umbral 5,0, máximo 3; `ENABLE_VENT_ANCHORED_CLUSTERING True`; `ENABLE_TEST1_PATH False`; `ENABLE_UTM_REGRID False`). Fuera de ese régimen publica la suma del fragmento: la fragmentación también recorta energía en modo suma, no sólo el pico.
  - Tablero: `frontend/index.html:1162-1173` (`mirovaEqVrp`) publica `pc.vrp_mw` en VIIRS 750 si `distance_class == "summit"` y el centroide está dentro de `inner_radius_km` del volcán (l. 2204 y 2428); `mirovaEqVrpCore` (l. 1295-1306) sólo sustituye por el núcleo en banda I.
- Instrumento de membresía (`m1_membresia.py`, salida `m1_salida.txt`): el cúmulo publicado se infiere como el subconjunto de `anomaly_pixels` de tamaño `n_pixels` cuya media reproduce el centroide persistido (tolerancia 2,5e-5°). VIIRS 750, toda la historia: 2.654 resueltos, 0 ambiguos, y la magnitud recalculada con la regla del modo de un píxel reproduce `pc.vrp_mw` en 2.654 de 2.654. SIN DATO aparte: 66 sin píxeles, 19 con top-100 truncado. Control negativo (`m11_control_membresia.py`): con el píxel ajeno más cercano en lugar del miembro, la magnitud «se reproduce» en 92 de 2.262 (4 %, casi todos píxeles de 0,0 MW), así que la comprobación discrimina.
- Paso de grilla, calibrado con los propios datos (`m2_paso.py`, `m2_salida.txt`): en cúmulos de 2 píxeles (8-vecinos por definición) la distancia mediana va de 0,77 km bajo 10° a 0,97 a 1,10 km sobre 40°. El píxel alertado ajeno más cercano al cúmulo publicado está a 1,558 km o más (p01) bajo 10° y 1,528 km entre 10 y 20°, o sea a dos pasos, que es lo que manda una grilla regular para dos píxeles no vecinos. Sobre 30° la ley se rompe: p05 de 0,35 km (30-40°), 0,28 (40-50°), 0,105 (50-60°). Eso sólo pasa si las huellas se solapan o si la matriz tiene filas intermedias que el terreno no tiene: la vecindad de matriz deja de ser vecindad de terreno justo en las pasadas oblicuas.
- Simulación del pegado (`m3_pegar.py`, `m5_sensibilidad.py`; salidas `m3_salida.txt`, `m5_salida.txt`, `m5_salida.json`). Denominador: publicaciones V750 del tablero en K = 290 (todas nocturnas), historia = 1.769.

  | umbral | K: cambian / sube / cruzan 1 MW / protegidas que cambian | historia: cambian / cruzan 1 MW | historia, cambios bajo 20° |
  |---|---|---|---|
  | 0,5 km | 6 / 6 / 2 / 3 | 27 / 7 | 0 |
  | 0,7 km | 8 / 8 / 2 / 5 | 41 / 9 | 0 |
  | 1,0 km | 14 / 14 / 2 / 8 | 55 / 11 | 0 |
  | p05 intra por cenit | 7 / 7 / 2 / 4 | 43 / 10 | 0 |
  | mediana intra por cenit («un paso») | 13 / 13 / 2 / 7 | 53 / 10 | 0 |

  El cambio más bajo de toda la historia está a 27,9° de cenit, el siguiente a 32,4°. De los 2 cruces de 1 MW en K, uno es Láscar 2026-05-05 06:06 (protegida, 0,932 a 1,001; MIROVA tabla 1,62, OCR 1,0) y el otro es Puyehue Cordón Caulle 2026-06-11 06:18, negativo (ver VM162-01). Láscar 05-05 es la única protegida que cruza 1 MW con cualquier umbral entre 0,4 y 1,0 km.
- Casos citados, píxel a píxel (`m4_casos.py`, `m4_salida.txt`):
  - Láscar 2026-05-05 06:06 VIIRS_NOAA20_750, cenit 41,75°: cúmulo publicado de 1 píxel (0,9323 MW); el ajeno de 1,0014 MW está a 0,396 km, 0,41 de un paso. Pegado y en modo máximo: 1,001.
  - Chillán 2026-10-14 06:18 VIIRS_NOAA21_750, cenit 51,48°: los dos miembros (1,1729 y 0,9462 MW) están a 1,293 km entre sí y son 8-conexos; el ajeno más caliente (1,8896 MW) queda en el terreno ENTRE ellos, a 0,672 km. Pegado: 3 píxeles, suma 4,01 < 5, modo máximo, 1,890. MIROVA tabla 2,0. Es el ejemplo más limpio de que la matriz separa lo que el terreno junta.
- Protegidas en K: 86 publicaciones V750 pareadas a una alerta de MIROVA de 1 MW o más (`m9_protegidas.py`), contra 82 de la afirmación; la diferencia es del pareo (yo uso tabla más OCR del snapshot de origin/main, ±8 min).

**Lo que no se sostiene tal como está escrito:**

- Los denominadores. Con el predicado del tablero hay 290 publicaciones V750 en K y 1.769 en la historia, no 338 y 2.070; ninguna variante que probé los da (sin filtro de `distance_class`, con radio 10, 20 o 25 km, hasta hoy, sólo 2026). Los numeradores del mismo orden sí se reproducen (8 en K con 0,7 km; 10 a 11 cruces históricos), pero «61 de 2.070» no: yo obtengo 41 a 55 de 1.769. SIN DATO sobre qué población usó el auditor.
- «Todas hacia arriba» no es evidencia: es una propiedad del cálculo. Pegar agrega píxeles; el máximo de un superconjunto es mayor o igual, la suma también, y pasar de máximo a suma también sube. No dice que el valor nuevo sea mejor.
- No toca qué se publica, sólo cuánto: pegando, ningún centroide cruza el radio interno (`m7_frontera.py`: 0 cruces en 162 pasadas V750 y 902 V375 pegadas, toda la historia, con el ancla reconstruida que reproduce `centroid_dist_km` a menos de 5 m en todas).

**Por qué gravedad 3 y no más:** no cambia ninguna publicación, sólo la magnitud y el nivel mostrado, y lo hace en pasadas oblicuas. Pesa en erupción: Chillán 2026-10-10 06:30 pasaría de 4,33 a 25,89 MW (MIROVA 32,0, OCR sin geometría), 10-18 05:06 de 8,10 a 15,06 (MIROVA 19,63), 10-18 06:48 de 2,84 a 5,50 (MIROVA 22,85). Es el mismo síntoma que AUDIT_S155 F2-02 (Chillán se ve un nivel más abajo) y F5-01.

### CM162-02: CONFIRMADO. Gravedad propia 1

- `f5_core.py:61-104` ancla el núcleo con distancias en el terreno: candidatos a `inner_km` o menos del centroide, pico por VRP, suma a 0,75 km del pico o BT de 295 K o más. No usa la membresía del cúmulo; sólo su centroide.
- `m6_v375.py` (`m6_salida.txt`), port propio. El port reproduce el campo persistido `f5_core_vrp_mw` en 1.331 de 1.331 publicaciones de K que lo traen (6.698 de 6.698 en la historia). Pegando ajenos a menos de un paso (mediana intra por cenit, 0,377 km bajo 10° a 0,673 sobre 60°): f5 cambia en **0 de 153** pasadas pegadas de K (0 de 837 en la historia). Control positivo: corriendo el centroide `inner` km al norte, f5 cambia en 147 de 153, así que el recálculo no está muerto. SIN DATO: 97 publicaciones de K con top-100 truncado.
- Fracción de pasadas multi-cúmulo publicadas con un ajeno a menos de un paso, K: 4/78 (0-10°), 4/84, 14/85, 22/87, 37/103, **44/91** (50-60°), 28/45 (60-70°). Los numeradores 4 y 44 coinciden con la afirmación; mis denominadores son 78 y 91, no 98 (truncados fuera). Que la subida no sea azar por haber más píxeles a gran cenit lo garantiza la geometría: en una grilla regular dos píxeles no vecinos nunca están a menos de dos pasos, cualquiera sea su número.
- Lo torcido es chico: el centroide (que el ancla `ctx_cluster` publica como posición del marcador en 153 de 153) se mueve 0,105 km de mediana, 0,181 p90 y 0,327 máximo (`m10_centroide.py`). `n_pixels` sí aparece en la ventana del mapa (`index.html:3147`, «cluster N pix»). Para el operador es invisible en posición y casi invisible en el conteo: gravedad 1.

### CM162-03: CONFIRMADO EN PARTE. Gravedad propia 2 (VIIRS 750)

- Láscar 2025-07-07 05:24 VIIRS_NOAA20_750, cenit 22,76° (`m4_salida.txt`): dos píxeles a 0,180 km, BT idéntica 274,98 K, 1,5531 MW cada uno, 8-conexos (cúmulo de 2). CONFIRMADO. Pero lo publicado es **1,553**, el máximo, porque el cúmulo está en modo de un píxel: la magnitud no se cuenta doble, sólo `n_pixels` (2) y el centroide. La «cuenta doble» de la afirmación no llega al número publicado en este caso.
- Los otros casos Láscar a 23,5-23,9° (2025-03-13 05:48, 03-29 05:48, 04-10 05:24, NOAA-21) sí están en modo suma, pero publican 5,0, el tope D9: el duplicado queda escondido detrás del tope (`m8_salida.txt`).
- Chillán 2026-10-01 06:00 VIIRS_SNPP_750, cenit 11,12°: 3 píxeles 8-conexos, suma publicada 11,084 (6,059 + 4,1747 + 0,8503). Los dos primeros están a 0,371 km, 0,47 de un paso a ese cenit, o sea huellas solapadas cerca de la mitad. CONFIRMADO que la geometría es de solape. Pero sus BT difieren 6,4 K (298,64 contra 292,28), así que no son el mismo terreno entero: «4,2 de 11,1 serían duplicado» es una cota superior, no una medida. Además la MIROVA de 10,0 viene sólo del OCR (no está en la tabla `latest.php`, ni en el snapshot ni en el congelado V1), y restar 4,2 deja 6,9, más lejos de esa referencia.
- Cuánto pesa hoy en lo publicado de VIIRS 750 (`m8_duplicado.py`, pares del cúmulo publicado a menos de medio paso, sólo cúmulos en modo suma): K, 1 de 290 publicaciones (Chillán 10-01); historia, 4 de 1.769, 3 de ellas topadas a 5,0. Raro.
- En VIIRS 375 el mismo fenómeno sí pesa, porque f5 suma vecinos en el terreno: K, 24 de 118 publicaciones sobre 60° y 26 de 238 entre 50 y 60° tienen un par solapado en el núcleo, con cota de exceso de 24,1 % y 15,2 % de los MW publicados. Reproduce AUDIT_S155 F5-09: Chillán 2026-10-10 06:30 VIIRS 375 publica 11,822 con cota de duplicado 5,122 (11,82 a 6,70, igual al número de F5-09). No es nuevo.

### Afirmación 4 (no está en el catálogo): CONFIRMADA EN PARTE. Gravedad propia 2

- CM162-01: ni D17 (`MIROVA_DIVERGENCES.md:2298`), ni D28 (l. 2984, sólo MODIS; sus «8 vecinos» son los del detector, no los del cúmulo), ni D32 (l. 3234, que sí habla de «primero el cúmulo de 8 conexos») nombran que la vecindad del cúmulo es de matriz y no de terreno. AUDIT_S155 F5-01 (`AUDIT_S155.md:50-54`) describe el **síntoma** sólo en Chillán y lo reparte entre modo de un píxel (36 %) y selección (64 %): CM162-01 es la causa común de las dos partes. Lo nuevo es la causa, no el defecto. Y la cura ya está escrita en otro lado: `docs/DISENO_D17_REMUESTREO_UTM.md` §4.3 dice que remuestrear «lo resuelve de por sí, porque cada celda recibe un solo valor», y D32 (sumar todo) también lo haría desaparecer.
- CM162-03: **sí está catalogada**, por fuera de `MIROVA_DIVERGENCES.md`: `docs/DISENO_D17_REMUESTREO_UTM.md` §4.3 («Queda un solape residual entre barridos que hoy cuenta doble en el borde»), AUDIT_S155 F5-09 (VIIRS 375, CONFIRMADO, «todas sobre 50°») y V5-02 (VIIRS 750, SOSPECHA, para el caso de sumar fragmentos). Lo que agrega CM162-03 es la instancia VIIRS 750 dentro de un cúmulo 8-conexo y a cenit bajo (11° y 22-24°), que contradice el «en el borde / sobre 50°» de esas fuentes. Eso es un matiz, no una divergencia nueva.

## Hallazgos propios

### VM162-01. Pegar fragmentos no es gratis: sube un negativo y arrastra huellas solapadas
- SCRIPT:SALIDA: `m5_sensibilidad.py` (`m5_salida.txt`), `m12_pegado_y_duplicado.py` (`m12_salida.txt`), y la lista de d/paso al final de la sesión (70 píxeles pegados en la historia).
- QUÉ PASA: cuando la pasada oblicua ve dos veces parte del mismo terreno, pegar por cercanía junta también esa repetición. En K, con «un paso», 1 de las 13 publicaciones que cambian es un negativo limpio: Puyehue Cordón Caulle 2026-06-11 06:18 VIIRS_NOAA20_750, cenit 44,8°, MIROVA RUTINA, pasa de 0,447 a 3,029 MW (de 3 a 8 píxeles, sale del modo máximo y entra en suma). En la historia, 25 de los 70 píxeles que el pegado agrega están a menos de medio paso de otro píxel del grupo, o sea con huellas solapadas más de la mitad; cuando el grupo pegado queda en modo suma, ese solape se suma dos veces. En los 13 cambios de K la cota de duplicado con medio paso da 0,0, así que la salvedad pesa en la historia, no en esas 13.
- CÓMO SE VE EN EL DASHBOARD: hoy invisible; si se adopta un arreglo sólo por pegado, PCC mostraría 3,03 MW donde MIROVA no vio nada, y algunas magnitudes de erupción quedarían infladas por duplicado.
- CÓMO REPRODUCIRLO: `python m5_sensibilidad.py` y `python m12_pegado_y_duplicado.py` en CARPETA; caso PCC 2026-06-11 06:18 UTC.
- CONFIANZA: CONFIRMADO el conteo; SOSPECHA que cada par solapado sea duplicado entero (sin L1B no sé qué fila de qué barrido es cada píxel).
- GRAVEDAD: 2. Lo que puede torcer es la decisión de adopción: un A/B que mida sólo protegidas vería «todo sube hacia MIROVA».

### VM162-02. Los denominadores de CM162-01 no salen del predicado del tablero
- SCRIPT:SALIDA: conteos en sesión con `lib_vm.published` (réplica de `index.html:1162-1173`): K 290 y historia 1.769 publicaciones V750; `isValidDetection` sin filtro de distancia: 369 y 2.138; con radio fijo de 25 km: 344 y 1.733. Ninguno da 338 ni 2.070. Protegidas: 86 contra 82 (`m9_salida.txt`).
- QUÉ PASA: los numeradores del orden correcto se reproducen, pero las tasas «8 de 338» y «61 de 2.070» no se pueden repetir sin saber qué población se usó.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python m3_pegar.py` (línea «publicadas»).
- CONFIANZA: CONFIRMADO que no se reproducen; SIN DATO del porqué.
- GRAVEDAD: 1.

### VM162-03. El mismo hecho geométrico da CM162-03 a cenit bajo y CM162-01 a cenit alto
- SCRIPT:SALIDA: `m2_salida.txt` y `m8_salida.txt`.
- QUÉ PASA: en VIIRS 750 los pares 8-conexos más cercanos que un paso aparecen entre 10 y 30° (cúmulos de 2 con p05 de 0,347 y 0,191 km), y los pares solapados dentro del cúmulo publicado sólo en los bins 10 y 20 (4 en la historia, 0 de 30° para arriba). Sobre 30° los píxeles que ven el mismo terreno ya no son filas contiguas de la matriz y caen en cúmulos distintos (ajenos a 0,1-0,4 km). O sea: cuando el solape entre barridos es menor que una fila, las dos copias quedan pegadas en la matriz y se suman (CM162-03); cuando es mayor, o cuando hay filas borradas a bordo en medio, quedan separadas y se fragmenta (CM162-01). El cambio de VIIRS 750 más bajo de toda la historia está a 27,9°. Las dos afirmaciones son una sola divergencia: la falta de de-solape y remuestreo de D17.
- CÓMO SE VE EN EL DASHBOARD: lo de CM162-01 y CM162-03.
- CÓMO REPRODUCIRLO: `python m2_paso.py`, `python m8_duplicado.py`.
- CONFIANZA: CONFIRMADO el patrón por cenit; SOSPECHA el mecanismo fila por fila (filas borradas por bow tie marcadas NaN, `FLAG_DNS` en `process_viirs_mod.py:68`, contra solape residual), que exige L1B.
- GRAVEDAD: 1 (es de diagnóstico: dice que un arreglo aparte de CM162-01 no hace falta si D17 se implementa con de-solape).

## VERIFICADO LIMPIO

- Membresía del cúmulo inferida desde los records: 2.654/2.654 VIIRS 750 y 8.611/8.611 VIIRS 375 reproducen `pc.vrp_mw`, 0 ambiguos; control negativo 92/2.262. Vara: `python m1_membresia.py`, `python m11_control_membresia.py`. No hace falta volver a dudar de que el cúmulo se puede reconstruir desde `anomaly_pixels` cuando el top-100 está completo.
- Port propio de f5 igual al campo persistido `f5_core_vrp_mw`: 1.331/1.331 en K, 6.698/6.698 en la historia. Vara: `python m6_v375.py` (claves `f5_persistido_igual`, sin `f5_persistido_DISTINTO`).
- Pegar no cambia qué pasadas se publican por el radio interno: 0 cruces. Vara: `python m7_frontera.py`.
- Control negativo a nadir: 0 cambios de VIIRS 750 bajo 20° con umbrales de 0,3 a 1,0 km, y el ajeno más cercano bajo 20° está a dos pasos o más (p01 1,528 a 1,558 km). Vara: `python m5_sensibilidad.py`, `python m2_paso.py`.
- Las 290 publicaciones V750 de K y las 1.769 de la historia son nocturnas (cenit solar > 90°): la cuenta no mezcla pasadas diurnas ni MODIS (sensor `_750`, convención A48). Vara: conteo en sesión con `lib_vm.is750` y `solar_zenith_deg`.
- Citas de código de la afirmación 1: `clustering.py:96`, `149-153` y `single_pixel_mode.py:181-182` dicen lo que se les atribuye (con los matices de arriba). Flags leídos de `pipeline.profile`, no del YAML.

## SIN DATO

- A qué barrido y fila pertenece cada píxel de un par solapado (duplicado entero o parcial): exige L1B, prohibido en esta tarea.
- Población exacta con que el auditor obtuvo 338, 82, 2.070 y 61.
- MODIS: no medido. `process_modis.py` llama al mismo `cluster_hotspots` (`process_modis.py:1167` y `1461` en origin/main, leído con `git grep`) y el bow tie de MODIS no tiene borrado a bordo, así que el fenómeno debería ser mayor allí; SOSPECHA sin medir.
- Si la MIROVA de Chillán 2026-10-01 06:00 (10,0, sólo OCR) es de esa pasada (la regla S150 sobre imágenes de otra pasada aplica).
