# S158 Tupungatito: informe del verificador con contexto limpio

> Verificador de `experiments/_s158_tupungatito/README.md`, escrito el 2026-10-21. Sólo lectura: no toqué
> `pipeline/`, `data/` ni los scripts o salidas del experimento. Mis comprobaciones viven en esta carpeta
> (`v1_` a `v8_`, cada una con su `_salida.txt`); tres sondas sueltas, movidas por el autor a esta carpeta (`v3b_sonda.py`, `v3c_sonda.py`,
> `v3d_sonda.py`). Los CSV del scraper los leí de `_tmp/ref4/` (bajados por la sesión autora; no volví a bajar el
> remoto, así que no sé su commit; los conteos de Tupungatito coinciden con las salidas del informe).
> Todo número de aquí sale de una salida mía de esta sesión o de una línea que leí.

## Veredicto por afirmación central

| # | Afirmación del README | Veredicto |
|---|---|---|
| 1 | Las dos protegidas «perdidas» (y las otras dos de la serie) son anomalías lejanas, no del cráter; no se pierde ninguna protegida de cráter | **CONFIRMADO** por una vía independiente (dirección en la miniatura de MIROVA), con una precisión: vale para las nocturnas |
| 2 | El 0,266 está inflado por esas dos; déficit real ~0,5 por noche, ~0,36 por pasada | **CONFIRMADO** (reproducido con la función real del auto-audit) |
| 3 | El déficit es casi entero el fondo; parte angular compatible con el área (D17); la selección pesa poco | **PARCIAL**: el fondo como pieza principal se sostiene; la «planitud con área» depende del modelo de área elegido, y la prueba de coherencia con que se apoya el fondo local es casi vacía |
| 4 | C0 tenía un fondo local por su Test 1 integrado, y por eso daba 0,83 | **PARCIAL**: el mecanismo se confirma por código y sale reforzado al reclasificar por fondo efectivo; pero «por eso #864 ve 0,27 donde C0 veía 0,83» compara noches distintas: en las mismas noches el cambio de detector lleva de 0,825 a 0,553 |
| 5 | Lado del barrido: dirección de #879, dentro del azar | **CONFIRMADO** en los números; nulo con pasadas tratadas como independientes (ver H11) |

## Hallazgos, de mayor a menor peso sobre las conclusiones

### H1. «Por eso #864 ve 0,27 donde C0 veía 0,83» compara noches distintas
- **Archivo:línea**: `README.md:25-26` (En corto, punto 4).
- **Qué pasa**: el 0,825 de C0 (`data/audit_continuous/latest.json`, `por_detector/C0`) es de las noches del
  2026-08-20 al 2026-09-17; el 0,266 de K es de las noches del 2026-09-18 al 2026-10-19. Medido con
  `auto_audit_weekly.evaluar_detector` sobre las MISMAS 14 noches de la ventana C0: C0 0,825, K 0,553; sólo
  noches con la alerta máxima de la tabla, C0 0,844 y K 0,571 (n = 11). La ventana C0 tiene además su propia
  protegida lejana (2026-09-14, R 0,049 en C0).
- **Cómo se ve**: de la caída 0,83 a 0,27, el cambio de detector explica 0,83 a ~0,55 en las mismas noches;
  las dos alertas lejanas explican 0,27 a 0,45 en la ventana K; el resto (~0,55 contra ~0,45) es cambio de
  noches. La atribución «por eso» es demasiado fuerte; la conclusión física (el fondo de C0) no cae, la
  aritmética del 0,27 contra 0,83 sí.
- **Reproducir**: `python -I verificador/v7_c0_ventana_auto_audit.py _tmp/Tupungatito_pre883.json` (reproduce
  0,825 n 14 y 0,266 n 8) y `python -I verificador/v8_k_en_noches_c0.py _tmp/Tupungatito_pre883.json`.
- **Confianza**: CONFIRMADO.

### H2. La «coherencia 1.130 de 1.130» del fondo local es casi vacía
- **Archivo:línea**: `README.md:132-133`; `e_fondo_local.py` (bloque «1. fondo local despejado», criterio
  `coherente = (max(ts) - min(ts)) < 0.3`).
- **Qué pasa**: de los 1.130 records C0 `test1_roi`, **1.126 tienen un solo píxel** dentro de 7 km; sólo 4
  tienen dos o más (en esos 4 el rango es 0,011 K como máximo). Con un píxel siempre existe un único T que
  reproduce su VRP, así que «todos los píxeles de cada pasada dan el mismo fondo» no puede fallar en 1.126 de
  1.130 casos.
- **Cómo se ve**: la lectura «fondo = mediana del anillo de 1 a 3 km» no queda probada por los datos sino
  por el código. La tracé y se sostiene: en `pipeline/process_viirs.py:1920-1926` el fondo del recompute
  Test 1 es `select_test1_effective_lbg(...)`, que (en `pipeline/test1_integrated.py:170-176`) sólo usa el
  anillo intermedio o el global si `lbg_global_compatible` es verdadero; en `volcanoes.yaml` ese campo existe
  sólo en Láscar (l. 129), Nevados de Chillán (l. 270) y Lastarria (l. 653), nunca en Tupungatito, así que
  cae a `test1_L_bg_local` (`process_viirs.py:1175-1177`), que es `np.median` de la radiancia en
  `dist > inner_ring_km` y `<= roi_km` (`test1_integrated.py:412-447`), con `TEST1_ROI_KM` 3,0 y
  `TEST1_INNER_RING_KM` 1,0 (`pipeline/profile.py:178-179`; `git log -S"test1_roi_km"` muestra un único
  commit, S25). `anomaly_pixels` de esos records se arma con ese fondo (`process_viirs.py:1983-2008`). Queda
  supuesto, sin poder comprobarlo desde el record, que el área fue la nadir y el coeficiente 18,0 cuando se
  escribió cada record; la falta de tendencia con el cenit (H7) es consistente con área nadir.
- **Reproducir**: `python -I verificador/v3_fondo_local_c0.py _tmp/Tupungatito_pre883.json`.
- **Confianza**: CONFIRMADO (lo vacío de la prueba); el mecanismo por código, CONFIRMADO para el código de hoy,
  SOSPECHA para records escritos por código de otras fechas.

### H3. La etiqueta `ctx_cluster` no garantiza el fondo del anillo; reclasificar por fondo efectivo refuerza la conclusión
- **Archivo:línea**: `README.md:140-146` (tabla K contra C0 por fuente y «desde #535, K = C0 (14 de 14)»).
- **Qué pasa**: despejando el fondo efectivo del VRP guardado de cada record C0 (mismo método que
  `e_fondo_local.py`), de los 53 pares rotulados `ctx_cluster` **15 usaban un fondo más frío que el anillo**.
  En todo el JSON C0, 247 de 472 records `ctx_cluster` despejables tienen fondo más frío, y **los 247 tienen
  `triggered_test1` verdadero** (los 225 con fondo del anillo se reparten 218 con Test 1 y 7 sin él).
  Reclasificado por fondo efectivo: anillo n 38, R_C0 0,351, R_K 0,395, K/C0 1,040; más frío n 89, R_C0 0,740,
  R_K 0,356, K/C0 0,507.
  Aparte: «desde #535, K = C0 (14 de 14)» vale para el **fondo del anillo** (t_bg igual en 14 de 14), no para la
  magnitud: la publicada es igual en 9 de 14 y en las otras 5 K/C0 va de 0,59 a 0,88.
- **Cómo se ve**: la conclusión 4 sale **más fuerte**, no más débil: todo C0 que restaba un fondo más frío que el
  anillo da el doble que K en el mismo gránulo, y todo C0 con el fondo del anillo da lo mismo que K. Lo que
  hay que corregir es el rótulo de la tabla («cúmulo contextual = fondo del anillo») y la frase del 14 de 14.
  No tracé por qué esos records `ctx_cluster` llevan el fondo del Test 1 (SOSPECHA: píxeles del Test 1 que
  entran al cúmulo antes del rotulado final).
- **Reproducir**: `python -I verificador/v4_k_c0_por_fondo_real.py _tmp/Tupungatito_pre883.json`;
  `python -I experiments/_s158_tupungatito/verificador/v3d_sonda.py`; la lista del 14 de 14 sale de `d_pasadas_salida.json` (pasadas con
  `pasada >= "2026-08-28 23"`).
- **Confianza**: CONFIRMADO.

### H4. La planitud del «fondo que cierra con área» es propia del modelo B; con el modelo C no es plana
- **Archivo:línea**: `README.md:27-29` y `150-153`; columna «ídem, con área real» de la tabla de `README.md:107-112`.
- **Qué pasa**: con los mismos píxeles y la misma bisección, cambiando sólo la ley de área de S131
  (`experiments/_s131_audit/magnitud/02_correccion_area_por_angulo.py:72-89`):
  sin área 7,0 / 10,6 / 16,7 K (contando como infinito las pasadas sin solución); modelo B (`f_modelo`) 5,0 /
  4,2 / 5,5; modelo C (`f_lineal`, el otro brazo de S131) 4,5 / 2,3 / 0,8; raíz de B 5,8 / 6,4 / 9,3. El
  modelo no está ajustado a estos datos (es geométrico, anclado a los extremos del ATBD), así que la planitud
  con B no es circular; pero llamarlo «área real» es más de lo que es: el propio S131 lo declara «modelo», y
  con el otro brazo la corrección se pasa.
- Segundo matiz: «sólo 10 de 141 pasadas no se cierran con ningún fondo» (`README.md:124-127`) vale **sin**
  área. Con `f_modelo` las 141 cierran (0 sin solución), pero las 10 piden 7,6 a 23,8 K bajo el anillo, y 8 de
  las 10 piden un fondo más frío que el entorno de 1 a 3 km medido para su pasada o su banda. Las 10 son del
  este y de un solo píxel (verificado), y 9 tienen cenit sobre 34° (verificado).
- **Cómo se ve**: «compatible con D17» sigue en pie; «queda plano» debe decir «queda plano con el modelo B de
  S131; con el modelo C se invierte». El orden de la tabla de la sección 4 no cambia.
- **Reproducir**: `python -I verificador/v5_fondo_que_cierra_modelos.py`.
- **Confianza**: CONFIRMADO.

### H5. Las temperaturas de la sección 1 mezclan poblaciones
- **Archivo:línea**: `README.md:37-40`.
- **Qué pasa**: «píxel más caliente 266 K (258, 273)» y «anillo 261 K (252, 269)» son de las 141 pasadas con
  alerta (reproduzco 265,8 / 258,4 / 273,4 y 260,5 / 251,9 / 268,8). Pero «entorno de 1 a 3 km 251 K (242,
  257)» es la T despejada de los **1.130 records C0** de 2025 y 2026 (reproduzco 250,8 / 241,5 / 256,6), no de
  esas 141. Sobre las 141 el entorno queda en 248,5 K (237,3 a 255,2) con la mezcla de misma pasada y mediana
  de banda, y 246,1 K sólo con la misma pasada (n 74). Esos cuantiles no están impresos en ninguna salida
  (están en el JSON; regla S91).
- **Cómo se ve**: nada cambia de fondo (el entorno sale incluso más frío en las 141), pero la frase pone en
  la misma oración tres números de dos poblaciones.
- **Reproducir**: lectura de `d_pasadas_salida.json` y `e_fondo_local_salida.json` (sonda en esta sesión,
  comando en la sección de reproducción abajo).
- **Confianza**: CONFIRMADO.

### H6. «A 12,5 km del cráter» no se mide desde el cráter
- **Archivo:línea**: `README.md:67-68`; `g_protegidas.py` (`p_["dist_km"]`).
- **Qué pasa**: `anomaly_pixels[].dist_km` se mide desde `volcano_lat/lon` de `volcanoes.yaml` (-33,4,
  -69,8), no desde el cráter (`pipeline/process_viirs.py:780`: `dist = haversine_km(volcano_lat, volcano_lon,
  ...)`). Desde el cráter, el píxel del 2026-08-01 está a 13,37 km y el del 2026-09-14 a 14,98 km; el del
  2026-09-29 a 9,40 km (el campo dice 7,52). Los filtros «dentro de 7 km» de `d_pasadas.py` y
  `e_fondo_local.py` usan el mismo campo, o sea 7 km del punto nominal, a ~2,7 km del cráter.
- **Cómo se ve**: no cambia ninguna conclusión (todos siguen lejos, y F_rec da 1,00 en mediana), pero el rótulo
  «del cráter» es falso y hay tres orígenes de distancia en juego (punto nominal, cráter, centro de MIROVA).
- **Reproducir**: sonda de esta sesión con haversine desde `vent_lat/lon` sobre los records K de esas pasadas.
- **Confianza**: CONFIRMADO.

### H7. «Sin dependencia del cenit (14,7 / 14,0 / 14,6 K)» se midió sobre 434 de 1.130
- **Archivo:línea**: `README.md:134`; `e_fondo_local_salida.txt:3-5`.
- **Qué pasa**: los 696 records C0 de 2025 no traen `sensor_zenith_deg`, así que la tabla por cenit es sólo
  2026. Tomando el cenit del record K de la misma pasada para esos 696: 12,25 / 11,97 / 12,92 K; las 1.130
  juntas, 12,72 / 12,68 / 13,54 K.
- **Cómo se ve**: la afirmación se **confirma** con la muestra completa (sigue plano). Ojo con un desfase de
  régimen: 2025 da 12,5 K de mediana y 2026 14,5 K; desde el 2026-06-07 sube a 15,4 a 17,5 K por banda.
- **Reproducir**: `python -I verificador/v3_fondo_local_c0.py _tmp/Tupungatito_pre883.json`;
  `python -I experiments/_s158_tupungatito/verificador/v3b_sonda.py`.
- **Confianza**: CONFIRMADO.

### H8. «Ninguna protegida de cráter en toda la serie» vale para las nocturnas
- **Archivo:línea**: `README.md:13-14`; `g_protegidas.py` (pasa por `bp.indexar_referencia`, que descarta
  diurnas, `scripts/banco_paridad.py:239-240`, y `bp.es_alerta`, que excluye `ALERTA_SIN_GEOMETRIA_OCR`,
  `banco_paridad.py:196-203`).
- **Qué pasa**: leyendo los CSV crudos sin filtro: la **tabla no tiene ninguna `ALERTA_TERMICA` de 1 MW o más**
  para Tupungatito VIIRS 375 (sus 17 filas de 1 MW o más son `FALSO_POSITIVO`, todas a 10,7 km o más). El OCR
  tiene 5 alertas de 1 MW o más: las 4 nocturnas lejanas del informe y una **diurna**, 2026-04-13 18:24 UTC,
  1,62 MW, clase «Medio», a 0,0 km en el CSV remoto y a 2,24 km en el snapshot del repo. Las 3
  `ALERTA_SIN_GEOMETRIA_OCR` están bajo 1 MW. El histórico de filas perdidas no agrega ninguna de 1 MW o más.
- **Cómo se ve**: la conclusión se sostiene para lo que el pipeline mira (noche). La frase debe decir
  «nocturna»; la diurna queda fuera por diseño (el pipeline no mira de día), no porque no exista.
- **Reproducir**: `python -I verificador/v1_protegidas_crudo.py _tmp/ref4`; la consulta al cargador del
  auto-audit (`aw.alertas_mirova()`) en esta sesión.
- **Confianza**: CONFIRMADO.

### H9. Dos láminas con la misma cabecera y distinto contenido (2026-08-01)
- **Archivo:línea**: `README.md:67` («lámina del 06-ago»); `b_series_mirova_salida.txt:2-11`.
- **Qué pasa**: `2026-08-01_05-00-00_..._Dist.png` y `2026-08-01_06-06-02_..._Dist.png` dicen las dos «Last
  Update 01-Aug-2026 06:06:02», pero sólo la primera trae el marcador gris a 15,29 km en el 1-ago (lo vi en
  las dos imágenes). La lámina del 06-ago sí lo trae.
- **Cómo se ve**: no cambia la asignación (2 de 3 láminas lo traen, y la miniatura lo ubica, ver «Verificado
  limpio»), pero el panel de MIROVA no es estable entre descargas con la misma cabecera.
- **Confianza**: CONFIRMADO (la inconsistencia); su causa, no la investigué.

### H10. La distancia ~5 km «de la otra pasada» no está comprobada para el 2026-09-29
- **Archivo:línea**: `README.md:11-12` y `58-59`.
- **Qué pasa**: para el 28-sep la lámina de las 05:18 (cabecera 05:36:01) muestra la estrella verde de la
  pasada de 05:36 a ~5 km: confirmado. Para el 29-sep la lámina (cabecera 06:36:00) no tiene estrella
  (anomalía NONE) y el OCR leyó 5,68 km, que no coincide con la otra pasada (tabla 5,41; serie 5,43).
- **Cómo se ve**: no cambia nada (la distancia correcta de las 04:54 sale de la serie y de la miniatura), pero
  el origen exacto del 5,68 queda sin explicar.
- **Confianza**: SOSPECHA.

### H11. Detalles menores
- **El nulo del lado** (`d_pasadas.py`, función `nulo`) sortea el lado pasada por pasada dentro de cada banda
  de cenit; las pasadas de una misma noche no son independientes, así que el IC95 del nulo es optimista. Para
  R y M no importa (ya están «dentro del azar» o al borde); el p 0,0015 de G con fondo cero (`README.md:166`)
  es el que más podría estar inflado. CONFIRMADO como diseño; el tamaño del sesgo, no medido.
- **Regla D-9**: `d_pasadas.py` indexa con la regla «original» (`indexar_referencia` sin `regla_minimas`); 12 de
  las 141 pasadas tienen M de 0,05 MW o menos. Sin ellas la mediana por pasada es 0,338 (n 129) contra 0,359.
  No cambia la conclusión. CONFIRMADO.
- **«El tablero no recorta nada (F_rec 1,00)»**: es la mediana; 3 pasadas tienen F_rec bajo 0,99 (mínimo
  0,12). CONFIRMADO.
- **«Desviación máxima 0,4 px»** (`README.md:54`): la salida dice 0,30 y 0,29 px. Número no transcrito de la
  salida (regla S91), inocuo. CONFIRMADO.
- **Rótulos de fecha del eje x de las series**: los marcadores quedan ~9 px (~0,6 día) a la izquierda de donde
  los pondrían los rótulos de semana leídos como 00 UTC (espaciado de rejilla 106,5 px por semana, ~15,2 px por
  día). Asignar días por los rótulos pondría la pasada del 29-sep 04:54 en el 28. El informe asigna por
  posición relativa y pareo, que es lo correcto. CONFIRMADO (offset medido en una lámina; su causa, no).

## Verificado limpio

- **El 0,266 n 8 sale de la función real del auto-audit**, no de una copia: `aw.evaluar_detector` sobre la
  ventana de #864 con frontera 2026-09-18 da `{'n_noches': 8, 'ratio_mediano': 0.266}`, igual que
  `data/audit_continuous/latest.json` (commit 2e1bc0e3, 2026-10-19). Con toda la data en K: 0,489 n 22, como el
  README. `c_noche_audit.py` replica la línea `por_vs` de `scripts/auto_audit_weekly.py:583-589`. Las variantes
  B, C y D (0,448 n 7) las recalculé a mano desde el JSON: la noche del 28-sep queda con M de la tabla 0,09
  (R 0,448) y la del 29-sep sale por D-9 (0,04 MW).
- **Las cuatro protegidas son lejanas, por una vía independiente de la serie**: en la miniatura Latest10NTI de
  cada pasada, suponiendo 51 km de lado centrada en `mirova_center` y norte arriba, hay un punto brillante
  aislado que coincide en rumbo y distancia con nuestro píxel lejano de la misma pasada: 08-01 05:00, MIROVA
  15,6 km a 32° contra nuestro 15,0 km a 32°; 09-14 06:18, 13,8 km a 75° contra 13,1 km a 74°; 09-28 05:18,
  25,0 km a 26° contra 23,9 km a 26°; 09-29 04:54, 9,8 km a 48° contra 9,3 km a 46°. Control: la pasada 09-28
  05:36 también calza (26,4 km a 297° contra 25,8 km a 297°). El detector de puntos da además candidatos
  espurios en los bordes y, el 28-sep, un segundo punto a 23,0 km a 204° que nuestro record no tiene (la
  magnitud de MIROVA de esa pasada puede incluirlo). El supuesto de escala es mío y no está leído de la lámina;
  lo respaldan las cinco coincidencias. `verificador/v6_miniaturas_direccion.py`.
- **Asignación de cada marcador a su pasada**: el panel Latest10NTI lista, para el 28-sep, sólo dos pasadas con
  VRP (05:18 2,51 MW y 05:36 0,09 MW; 04:42 NaN) y para el 29-sep sólo dos (04:54 1,86 y 05:18 0,04; 06:00 y
  06:36 NaN); para el 1-ago, 05:00 1,25 y 06:06 0,04; para el 14-sep, 05:00 0,10, 05:42 0,13 y 06:18 2,22 (lo vi
  en las imágenes). Con dos alertas por día y una de ellas en la tabla a ~5 km, el marcador gris de ~2 MW sólo
  puede ser la otra. Las cabeceras «Last Update» 05:36:01 y 06:36:00 de los archivos de 05:18 y 04:54, vistas.
- **Cenit y azimut de MIROVA contra nuestros records** en 8 pasadas de esas noches: coinciden a 1° (p. ej. 09-28
  05:18: MIROVA 48° y 105°, record 48,77° y 105,37°). El pareo record a pasada es correcto.
- **Filas de la tabla y del OCR** de esas noches (`_tmp/ref4`): 05:36 0,09 MW a 5,21 km; 29-sep 05:18 0,04 a
  5,41; 1-ago 06:06 0,04 a 5,21; 27-sep 05:54 `FALSO_POSITIVO` 0,37 a 21,8; las cuatro protegidas son sólo OCR y
  su `Distancia_aprox` es 15,27 «único», 13,11 «único», 5,27 a 22,57 «ambiguo» y 5,41 a 9,59 «ambiguo».
- **Conteos del pareo** (`d_pasadas_salida.txt:2-3`): 198, 158, 141, 40; los 17 no publicados se reparten 10
  sin cúmulo, 1 lejos y 6 en el cráter con 0,0 MW, y en los 6 el píxel del cráter está bajo t_bg (los seis pares
  leídos). Control de reproducción del VRP por píxel 229 de 229.
- **Números de las tablas de las secciones 3, 4 y 5** contra las salidas: todos los que revisé coinciden
  (0,49 n 101; 0,36 n 141; 0,347 n 27 contra 0,48 n 89; fila por banda de cenit R, G, G-10K, G_f0, f_area,
  G_area; zonas 0,41 / 0,29 / 0,25; antes y después del 2026-06-13, 0,29 contra 0,44; G_local 1,30;
  dT_local 13,00 (8,91 a 22,35), verano 11,07, invierno 14,19; K contra C0 por fuente 0,76 / 0,35 / 0,46 y
  0,39 / 0,38 / 1,02; anillo 2,66 K más frío antes de #535; factores este/oeste e IC95 del nulo).
- **El fondo del anillo de K es t_bg_k**: en los records C0 `ctx_cluster` de 2026 con cenit bajo 50° el fondo
  despejado coincide con t_bg_k (mediana 0,00 a 0,01 K); el control 229 de 229 del informe lo confirma para K.
- **La selección pesa poco**: en las pasadas donde C0 y K restan el mismo fondo (reclasificación de H3), K/C0
  es 1,040 (n 38).
- **Lado**: los 10 casos sin solución sin área son todos del este, todos de un píxel, 9 con cenit sobre 34°.

## Reproducir lo de este informe

```bash
python -I experiments/_s158_tupungatito/verificador/v1_protegidas_crudo.py _tmp/ref4
python -I experiments/_s158_tupungatito/verificador/v2_auto_audit_directo.py
python -I experiments/_s158_tupungatito/verificador/v3_fondo_local_c0.py _tmp/Tupungatito_pre883.json
python -I experiments/_s158_tupungatito/verificador/v4_k_c0_por_fondo_real.py _tmp/Tupungatito_pre883.json
python -I experiments/_s158_tupungatito/verificador/v5_fondo_que_cierra_modelos.py
python -I experiments/_s158_tupungatito/verificador/v6_miniaturas_direccion.py _tmp/img
python -I experiments/_s158_tupungatito/verificador/v7_c0_ventana_auto_audit.py _tmp/Tupungatito_pre883.json
python -I experiments/_s158_tupungatito/verificador/v8_k_en_noches_c0.py _tmp/Tupungatito_pre883.json
```

No verifiqué: el contenido de `a_bajar_imagenes.py` contra el remoto de Mirova-v1 (usé las láminas ya en
`_tmp/img/`); la causa del rotulado `ctx_cluster` con fondo del Test 1 (H3); la causa del desfase de los rótulos
del eje x (H11); ni volví a bajar los CSV remotos.
