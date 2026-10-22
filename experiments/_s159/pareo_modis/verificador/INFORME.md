# Verificador S159, frente «pareo MODIS en el borde del gránulo»

Fecha 2026-10-21. Verificador con contexto limpio: no encontré esto, intenté romperlo. Datos de hoy desde
`origin/main` en `5b922c363` (el informe usó `533398f8f`; los conteos centrales salen idénticos), extraídos con
`git archive` a `D:\vrp-trabajo\temporales\s159_pareo_verif\`; para #864, `2e1bc0e31` en
`D:\vrp-trabajo\temporales\s159_pareo_verif_864\`. Ambos espejos se borran al terminar. No toqué git ni
workflows. Scripts propios y salidas en
`C:\vrp-trabajo\s159-pruebas\experiments\_s159\pareo_modis\verificador\`:

| script | qué mide | salida |
|---|---|---|
| `verif_pareo.py` | censo MODIS, las 148/130/18, lado que lista MIROVA por plataforma, validación del indicador de anillo contra la posición del cúmulo | `verif_pareo_salida.txt`, `.json` |
| `verif_negativos.py` | negativos limpios con el gránulo de MIROVA bajo la mitad del anillo; partidas contra enteras con el predicado del tablero (node), por cadena y por miembro | `verif_negativos_salida.txt` |
| `verif_modelo_alternativo.py` | ¿MIROVA ve el cráter aunque esté en el otro gránulo? alertas esperadas contra observadas | `verif_modelo_alternativo_salida.txt` |
| `verif_ancha.py` | ¿alguna alerta gana par sólo con ±390 s? | `verif_ancha_salida.txt` |
| (re-corrida) `../audit_864_variantes.py` hoy y orbita sobre `2e1bc0e31` + `../comparar_latest.py` | reproducción de #864 | consola (ver §4) |

Las dos preguntas del instrumento, comunes a todo: (1) si MIROVA eligiera el gránulo por orden de llegada,
Terra y Aqua darían lados opuestos (Terra sube de noche, Aqua baja), así que separar por plataforma lo vería;
(2) cada conteo trae un control positivo (abajo) y el indicador de anillo se validó contra una medición
independiente antes de usarlo.

## Veredicto por afirmación

### 1. 6.646 / 6.349 / 148 (130 + 18), ninguna protegida, ensanchar empeora: CONFIRMADA

- `verif_pareo.py`: 6.349 records MODIS parean a ±120 s, **148** sólo con el vecino (±5 min), de ellos **130**
  con record nuestro también en el gránulo de MIROVA y **18** sin él. Tipos de las 148: 147 RUTINA y 1
  ALERTA_TERMICA de 0,9 MW (máximo VRP de MIROVA en el grupo): ninguna protegida.
- El total 6.646 depende de cómo se fija el inicio de la ventana: con «desde la medianoche del día de la primera
  fila del volcán» me da 6.692 (sin fila a ±10 min 195 en vez de 149). Los conteos que importan no cambian.
- Las 18 tienen anillo 0,931 a 1,019 de la mediana de pasadas enteras del mismo volcán, plataforma y cenit ±3°
  (lista completa al final de `verif_pareo_salida.txt`): reproduce el 0,93 a 1,02.
- Ensanchar: `verif_ancha.py`, alertas nocturnas (00 a 11 UTC) 2026-01-10 a 2026-10-21: **0** alertas sin record
  a ±120 s que ganen record en 121 a 390 s (MODIS 0 de 112, V375 0 de 1.734, V750 0 de 366). Las 24 que tienen
  vecino (1 MODIS, 22 V375, 1 V750) ya tenían par a ±120 s: el pareo ancho sólo duplica. Control: el mismo
  script sí encuentra 15 alertas V375 y 1 V750 sin record a ±120 s, o sea que puede dar distinto de cero.

### 2. MIROVA lista el gránulo sur en 526 de 537 y sólo alerta con el cráter en él: CONFIRMADA en lo medible; dos matices

Cómo se sabe qué gránulo «listó» MIROVA: la fila del CSV con la hora exacta del inicio del gránulo (MIROVA
guarda MODIS en múltiplos de 5 min con segundos 00, 12.822 de 12.822 filas; si usara la hora de fin, las 6.349
pasadas enteras parearían a +5 min, no exacto). Cómo se sabe la fracción del ROI: no se sabe; se aproxima con
`diag_n_bg_anillo` de cada miembro (`pipeline/process_modis.py:621-630` lo cuenta en el anillo tras la máscara
de nube y la exclusión K1; se persiste en `:1581`). Como el anillo es simétrico respecto del cráter, el miembro
con la mitad o más del anillo es el que tiene el cráter. **Lo validé contra una medición independiente**: en los
miembros de pasadas partidas que traen un cúmulo con VRP a menos de 3 km del cráter, la fracción es ≥ 0,5 en
**221 de 234** (MODIS 6 de 6, V375 183 de 193, V750 32 de 35). El indicador acierta ~94 %; cerca de 0,5 es
ruido (el p10 de las pasadas enteras ya está en 0,92 de la mediana por nubes).

- Lado por plataforma (`verif_pareo.py`): Aqua 70 sur de 70; **Terra 57 sur, 3 norte**; V375 218 de 223; V750
  181 de 184. Total 526 de 537. Esto **descarta toda explicación por orden temporal** (el scraper que guarda la
  primera o la última fila, MIROVA que procesa en orden de llegada, hora de inicio contra hora de fin): Terra y
  Aqua están invertidos en el tiempo y coinciden en la latitud. En VIIRS (todos bajan de noche) sur y posterior
  son lo mismo, así que **el peso de la prueba lo lleva Terra** (57 contra 3).
- Lo nuevo y más fuerte (`verif_modelo_alternativo.py`): si MIROVA viera el cráter aunque cayera en el otro
  gránulo (mosaico, o procesar los dos y listar el caliente), en las partidas con el cráter en el norte
  aparecerían alertas a la tasa de pasadas de ese volcán, sensor y mes. **Esperadas 28,7, observadas 0** (n 272).
  Control positivo: con el cráter en el sur, **esperadas 25,4, observadas 24** (n 254). Y ninguna de las 12
  filas que listan el norte es alerta. Esto sube la lectura «MIROVA no ve el cráter fuera de su gránulo» de
  SOSPECHA alta a muy probable.
- Matiz a: «24 de 24» es casi todo VIIRS 375 (22). En MODIS hay **1** alerta (fracción 0,51, en el borde del
  indicador; esperadas 0,6 con el cráter en el sur y 1,6 en el norte). La regla en MODIS sola no está probada:
  descansa en Terra para el lado y en VIIRS para la ceguera.
- Matiz b: el «~45 %» de RUTINA con menos de la mitad del ROI sólo vale en MODIS (55 de 129, 43 %); en V375 es
  114 de 201 (57 %) y en V750 103 de 184 (56 %); juntos 272 de 514 (53 %).
- «1 a 3 % de los negativos limpios» (`verif_negativos.py`, ventana 2026-01-10 a 2026-10-21, regla D-9
  original): MODIS 54 de 6.156 (0,9 %), V375 84 de 4.260 (2,0 %), V750 97 de 6.819 (1,4 %). Confirmado, con
  MODIS apenas bajo 1 %.
- Observación propia: en 11 de las 12 veces que MIROVA lista el norte, su gránulo trae 0,8 a 1,0 de nuestro
  anillo (el sur casi no tiene ROI). La regla real parece «el sur, salvo que el sur casi no toque el ROI»,
  con el ROI de MIROVA (grilla 51 × 51 km), no el nuestro. No cambia nada del informe.
- SOSPECHA residual de mecanismo: no puedo separar «MIROVA procesa un solo gránulo» de «MIROVA procesa los dos
  y el canal que scrapeamos sólo expone el del sur». Para las métricas da igual (la fila no informa sobre el
  cráter); para la extensión BEYOND_MIROVA sí importa. Lo cierra un GeoTIFF o una imagen de MIROVA de una
  pasada partida.

### 3. Publicaciones del gránulo norte fuera de métrica: 8,8 % (13 de 147) contra 2,6 %, p = 0,0002: PARCIAL

- Los números se reproducen (`verif_negativos.py`): V375 partidas 13 de 147 (8,84 %), enteras 108 de 4.113
  (2,63 %; el informe dice 4.114), Fisher p = 0,00023. MODIS 2/128 contra 48/6.022 (p 0,28), V750 4/169 contra
  60/6.650 (p 0,07).
- Defecto de comparación: una partida tiene **dos** records y publica si publica cualquiera; una entera, uno.
  Con dos chances a la tasa de las enteras se esperan **7,6 de 147**, no 3,9; contra eso, 13 da p binomial
  **0,043**. Por miembro: el del norte (sin fila) publica 8 de 147 (Fisher p 0,062) y el de MIROVA 6 de 147
  (p 0,29). Queda un exceso, pero del orden de p 0,04, no 0,0002.
- Rótulo: las 13 no son todas «del gránulo norte». En 6 publica el miembro de MIROVA (sur), que ya entra a la
  métrica; en 8 publica el del norte (en una, PCC 03-14, publican los dos). Las que de verdad quedan fuera de
  toda métrica son 7 en V375 (sólo el norte publica y el gránulo de MIROVA tiene menos de la mitad del anillo),
  2 en MODIS y 4 en V750: **13 en total**, lo que el informe sí dice en su hallazgo 4.
- Detalle: «publica siempre el miembro con el anillo mayor» tiene una excepción parcial (PCC V375 2026-03-14
  05:42/05:48, fracciones 0,51/0,49, publican los dos). La refutación de «el pedazo chico da fondo ruidoso» se
  sostiene.

### 4. #864 no cambia salvo las falsas de K por 1 o 2: CONFIRMADA con un matiz

- Re-corrí `audit_864_variantes.py` hoy y orbita sobre un espejo de `2e1bc0e31` con fecha congelada: salidas de
  texto **idénticas** a `audit_864_hoy.txt` y `audit_864_orbita.txt`; `comparar_latest.py` del `latest.json`
  commiteado (`generated_utc` 2026-10-19T16:29:28Z) contra mi «hoy»: **0 distintas de 1.203**; hoy contra orbita:
  37 distintas, **todas bajo `falsas_publicaciones`**. Leí el código: recall y magnitud agrupan por noche
  (`scripts/auto_audit_weekly.py:497`, `nuestros_por_noche`) y las protegidas usan `TOL_PASADA_S` (`:795`),
  que el parche sí cambia (variable de módulo leída en cada llamada).
- Las 5 protegidas sin publicar tienen, en los datos de hoy, **un solo record** a ±15 min cada una (Tupungatito
  V375 09-28 05:18 y 09-29 04:54, PCC V750 10-10 05:54, Chillán MODIS 10-12 07:20 y 10-15 01:05), con anillo
  0,99 de la mediana de enteras en las dos de Chillán: no son borde.
- Matiz: no sólo cambian las falsas de K. También las de C0 (MODIS 43 a 44, V750 118 a 119, **V375 295 a 299**
  con orbita; 86,8 a 87,9 %) y los estratos por cenit y régimen. Ningún flag ni veredicto se mueve.

### 5. Chillán 2026-01-19 02:40 es uno de los 18 y su RUTINA de las 02:35 no habla del cráter: CONFIRMADA

- Está en mi lista de las 18 (Terra, fila de MIROVA a −5 min, RUTINA, CONS; nuestro record `summit` 0,849 MW).
- Anillo 981 contra mediana 1.039 de 63 pasadas enteras Terra de cenit 41 a 47°: **0,944**, reproducido. Matiz:
  el p10 de esas enteras es 953 (0,917), así que el «~6 % del ROI en el gránulo de MIROVA» está dentro del ruido
  de nubes; lo que sí queda probado es que nuestro gránulo trae casi todo el ROI y por lo tanto el cráter.
- Terra sube de noche: 02:35 es el gránulo del sur. Con la prueba de la afirmación 2 (0 alertas observadas
  contra 28,7 esperadas con el cráter fuera del gránulo listado), esa RUTINA no informa sobre el cráter.
  La «línea 23» del verificador de M no la verifiqué (no abrí el HDF).

## Hallazgos propios

1. **El exceso de publicación en partidas está inflado por contar dos records contra uno.** Ver afirmación 3.
   Gravedad 1 (cambia la fuerza de una evidencia, no una decisión de alerta). CONFIRMADO.
2. **El indicador de anillo se equivoca ~6 % de las veces** contra la posición del cúmulo (13 de 234). Una regla
   operativa basada en «fracción ≥ 0,5» clasificaría mal ~1 de cada 17 pasadas partidas; la línea del cráter
   persistida (hallazgo 5 del informe) lo resolvería. Gravedad 1. CONFIRMADO.
3. **La afirmación «sólo alerta con el cráter en su gránulo» no está probada en MODIS** (n = 1). Gravedad 1.
   CONFIRMADO.

## VERIFICADO LIMPIO

- Todos los records de los 11 Tier A son nocturnos salvo 5 MODIS con cenit solar < 90 o sin dato, de 14.565
  (`verif_pareo.py`, bloque 0): la dirección de órbita «Terra sube, el resto baja» aplica al corpus.
- La convención horaria: MIROVA MODIS en múltiplos de 5 min con segundos 00 (12.822 filas), y el pareo exacto de
  6.349 enteras descarta que MIROVA use la hora de fin del gránulo.
- El orden del scraper o de procesamiento no explica el sesgo al sur: Terra 57 a 3 contra Aqua 70 a 0.
- El pareo ancho no rescata ninguna alerta (0 en los tres sensores, `verif_ancha.py`).
- #864 se reproduce hoja por hoja y las variantes no tocan recall, magnitud, protegidas, flags ni veredicto.
- Las 5 protegidas sin publicar de #864 no son pasadas partidas.
- Comando base: `python -I verif_pareo.py <espejo>`, `python -I verif_negativos.py <espejo>`,
  `python -I verif_modelo_alternativo.py <espejo>`, `python -I verif_ancha.py <espejo>`.
