# S159, frente M: MODIS con MxD03 contra `_interp_geo`, efecto sobre lo publicado

**Veredicto pre-registrado (`PREREGISTRO_M.md`, commit 10ffdd3d6, sellado antes del primer despacho): CONFIRMA.**
Instrumento válido: control S151 reproducido exacto, nulo de geometría 0 en 85 de 85, A idéntico a A2 en 85 de 85.
Métrica 1 (desplazamiento del píxel caliente del cúmulo): mediana **2,85 km** en S1 (n = 38) y **1,58 km** en S2
(n = 25). Métrica 2 (cambios de clase en S1 + S2 + S4): **9 de 75**.

- Run válido: **39681481914** (4 partes verdes, 85 de 85 records, 0 faltantes; 6 ReadTimeout de CMR recuperados por el
  reintento). Run previo **39679594869**: cayó por un ReadTimeout de CMR sin reintento (31 records parciales, no se
  usan para nada salvo depurar el analizador).
- Población: `objetivos.json`, 85 records MODIS de los 11 Tier A, ventana de datos **2025-02-15 a 2026-10-17**.
  S1 es el **censo completo** de los records `summit` del lado del frame 0 sobre 40° de todo el corpus (38 de 38);
  S2 son 25 de 41 del lado contrario. El corpus MODIS tiene 619 records con clase (de 14.565), 452 `summit`.
- Salidas: `resultado/` (jsonl crudos del run), `analizar_m_salida.txt`, `analizar_m_tabla.json`, `extra_m_salida.txt`,
  `osf_2025_salida.txt`, `cmr_chillan_salida.txt`.

## Las dos preguntas del instrumento (para todo el informe)

1. *Si la geolocalización estuviera completamente rota, ¿se vería?* Sí. El brazo B sólo cambia la lat/lon que devuelve
   `read_modis_l1b`; la prueba sintética (`probar_m.py`, corrida en el runner: `resultado/prueba_sintetica_parte0.txt`)
   mide 3,0 km donde el defecto del zoom lo pone y < 0,01 km con una grilla sin defecto.
2. *Si el instrumento estuviera muerto, ¿se vería distinto?* Sí. Control positivo: en `MYD021KM.A2026073.0705`
   (Láscar) la componente hacia el sensor en el píxel del cráter da **2,581 km y la traza −0,431 km**, idénticos a
   S151 (run 38733452917). Nulos: `_interp_geo` contra sí misma da **0 en 85 de 85**; la misma corrida dos veces (A y
   A2) da el mismo record publicado en **85 de 85**. Y A reproduce el record publicado hoy en `data/` en **84 de 85**
   (la excepción, Chillán 2026-10-17 08:50, da 0,535 contra 0,538 MW; ese record se escribió con otro `codigo_sha`).
   «Publicado» es `mirovaEqVrp` de `frontend/index.html` ejecutada con node (A97), con control: el arnés da 2, 0, 0, 0
   para un cúmulo dentro del inner, fuera del inner, `far` y vacío.

## Hallazgos, de mayor a menor gravedad

### H1. La geolocalización decide qué píxel recibe el umbral de cumbre: con MxD03, 10 de 57 publicaciones de cumbre sobre 40° se apagan y 2 se encienden
- **ARCHIVO:LÍNEA**: `pipeline/process_modis.py:838` (`is_summit = roi1_summit_mask(vent_dist_per_pixel,
  inner_radius_km, ...)`), `pipeline/detection_context.py:299`; posiciones de `_interp_geo` en `process_modis.py:292-293`
  y `:385-396`. SCRIPT:SALIDA `extra_m_salida.txt` (bloque «Records con cambio de clase o de publicación») y
  `analizar_m_salida.txt` (resumen por estrato).
- **QUÉ PASA**: el píxel caliente de un volcán visto de lado (cenit sobre 40°) queda ubicado 2 a 5 km fuera de su lugar.
  El detector le da el umbral laxo de cumbre (N·σ y C1 menores) según la distancia de ese píxel al cráter. Cuando el
  píxel cae cerca del borde del círculo `inner_radius_km`, la geolocalización decide si se detecta: en 6 de los 10
  apagados el cúmulo de A estaba a 4,4 a 4,9 km de un inner de 5 (Llaima, Chillán, Chaitén) o a 17,6 a 19,2 km de un
  inner de 20 (Cordón Caulle), con `diag_n_first_pass_summit` = 1, y con MxD03 sale del círculo, pasa al umbral de
  escena y no se detecta (`diag_n_first_pass_summit` = 0). Sobre S1 + S2 (63 records, 57 publicados en A): 12 cambios
  de publicación (S1: 8, S2: 4). Clase: 9 de 75 en S1 + S2 + S4 (7 `summit` a nada, 1 `summit` a `far`, 1 `far` a
  nada), **0 de `far` a `summit`** en S4 (n = 12). En S3, cerca del nadir (n = 8), ningún cambio.
- **Contra MIROVA** (CSV del scraper para 2026; OSF v2.5 para 2025, con `osf_2025.py`, que tiene control positivo: 235
  filas de Láscar MODIS en 2025):
  | cambio | MIROVA dice | records |
  |---|---|---|
  | se apaga | RUTINA (miró y no vio nada) | 5: Cordón Caulle 2026-06-19 01:15 y 2026-06-30 07:00, Lastarria 2026-02-24 07:05, Chillán 2026-06-01 08:15, Chaitén 2026-03-13 06:35 |
  | se apaga | alerta (OSF 0,44 MW a 1,41 km) | 1: Láscar 2025-05-23 07:25 (A publicaba 0,029 MW) |
  | se apaga | sin fila (SIN DATO: el OSF es filtrado, A105; enero, A119) | 4: Llaima 2025-02-15 03:15 (1,243 MW), Láscar 2025-06-02 07:20, Cordón Caulle 2025-08-03 06:35, Chillán 2026-01-19 02:40 |
  | se enciende | ALERTA 0,48 MW a 1,41 km | 1: Láscar 2026-02-11 07:00 (B publica 0,033) |
  | se enciende | RUTINA | 1: Láscar 2026-04-01 07:05 (B publica 0,060) |
  En las 8 con referencia, B acerca a MIROVA en 6 y aleja en 2. **No es una muestra para estimar la tasa** (n chico,
  población de cenit alto), pero la dirección es la de A98: la brecha es sobre-publicación, y parte de ella es un
  píxel mal ubicado que cae dentro del círculo de cumbre.
- **CÓMO SE VE EN EL DASHBOARD**: barras de magnitud MODIS de cumbre (0,4 a 1,2 MW) en noches donde MIROVA miró y no vio
  nada, en volcanes vistos de lado; y lo contrario en algún caso (Láscar 2026-02-11).
- **CÓMO REPRODUCIRLO**: `python experiments/_s159/m/analizar_m.py experiments/_s159/m/resultado` y
  `python experiments/_s159/m/extra_m.py experiments/_s159/m/resultado`; caso de manual Llaima, Terra, 2025-02-15
  03:15 UTC (`MOD021KM.A2025046.0315`), cenit 51°, frame 130.
- **CONFIANZA**: CONFIRMADO (medido con la función de producción y el predicado del tablero).
- **GRAVEDAD**: 4. Cambia qué se publica en 1 de cada 5 records de cumbre sobre 40°, sin que nada en el record lo avise.
  Sobre los records bajo 40° no hay medición de cambios de clase salvo S3 (n = 8, ninguno): SIN DATO.

### H2. El cúmulo publicado queda corrido del cráter 2 a 3 km, y con MxD03 cae sobre el cráter
- **SCRIPT:SALIDA**: `extra_m_salida.txt`, bloques «Distancia del centroide ... por volcán» y «Control de selección».
- **QUÉ PASA**: Láscar tiene una fuente persistente en el cráter, así que sirve de vara física. Con los **mismos
  píxeles** detectados en los dos brazos (descarta que el efecto sea de selección), la distancia del centroide al vent
  pasa de mediana **2,54 km a 0,59 km**, más cerca en **35 de 38** (S1 + S2 + S3). Por volcán, con cúmulo en los dos
  brazos: Láscar 2,55 a 0,62 (36 de 39), Chillán 1,91 a 0,69 (7 de 8), Planchón-Peteroa 1,27 a 0,46 (2 de 2), Chaitén
  0,92 a 0,40 (1), Isluga 1,17 a 0,71 (1); Cordón Caulle 12,87 a 12,30 (7 de 13: el lacolito no es puntual, A20).
  Pasa también cerca del nadir: S3 1,08 a 0,39 km, 8 de 8. Es la misma conclusión que el control del píxel brillante de
  S151, ahora en 6 volcanes.
- **CÓMO SE VE EN EL DASHBOARD**: el marcador MODIS (`final_hotspot` = centroide del cúmulo, `ctx_cluster`) se dibuja a
  2 a 3 km del cráter y la tabla dice esa distancia. Un operador que mire la posición (A61) lee un foco en el flanco que
  no está ahí. Las auditorías espaciales MODIS hechas hasta hoy heredan el corrimiento.
- **CÓMO REPRODUCIRLO**: igual que H1; ejemplo Láscar Aqua 2025-03-17 06:25 UTC, distancia 3,375 km (A) contra 0,537 km
  (B).
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD**: 3. No cambia una alerta por sí solo (eso es H1), pero tuerce toda lectura espacial de MODIS.

### H3. El corrimiento es mayor que el del plan y no es «casi nulo» del otro lado
- **SCRIPT:SALIDA**: `extra_m_salida.txt`, bloque «Componente hacia el sensor y desplazamiento total».
- **QUÉ PASA**: en el píxel del cráter, desplazamiento total (mediana): lado del frame 0, cenit 40 a 50°, **2,82 km**
  (n = 36, hacia el sensor 2,27); sobre 50°, **5,04 km** (n = 15, máximo 9,42 en Chaitén a 65°); lado contrario, 40 a
  50°, **1,10 km** (n = 15); sobre 50°, **2,48 km** (n = 11); cerca del nadir, 1,10 y 0,79 km (n = 4 y 4). La asimetría
  de R2-2 se confirma, pero el «casi nulo del otro lado» vale sólo para la componente del zoom bajo ~45°: sobre 50°, un
  frame del lado contrario ya son 2 a 4 km, y la traza más el terreno dan 0,8 a 1,1 km aun en el nadir. La hipótesis
  del plan («1 a 1,7 km») subestima el lado del frame 0.
- **Extremos del gránulo** (±400 líneas): en S1, traza mediana +0,81 km (n = 17) contra −0,09 en el centro (n = 21),
  métrica 1 3,24 contra 2,59 km, cambios de clase 4 contra 2. El efecto de P3 existe y se suma, pero no es el dominante.
- **CÓMO SE VE EN EL DASHBOARD**: invisible como número; es la causa de H1 y H2.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD**: 3.

### H4. Las dos alertas protegidas de Chillán del #864 sí tienen gránulo nuestro, y MxD03 no las recupera
- **SCRIPT:SALIDA**: `cmr_chillan_salida.txt` (los 4 archivos, L1B y MxD03, están en CMR en LAADS y LANCE);
  `data/mirova_equivalent/NevadosDeChillan.json` tiene los dos records (`MYD021KM.A2026285.0720`, cenit 58,2°, y
  `MOD021KM.A2026288.0105`, cenit 57,6°), con `primary_cluster` nulo; `resultado/probe_m_parte*.jsonl`, estrato S5.
- **QUÉ PASA**: la premisa del encargo («no tienen gránulo nuestro») es falsa: el pipeline los bajó, los procesó y no
  detectó nada. Con MxD03 el cráter se mueve 5,7 km (2026-10-12, frame 61, lado del frame 0) y 1,5 km (2026-10-15), y
  **ninguno de los dos brazos detecta**: `diag_n_first_pass_pixels` = 0 en A y en B, píxel más caliente de la escena a
  24 a 33 km del cráter. MIROVA publicó 2,18 y 1,72 MW a 2,24 km. La geolocalización no es la causa; la causa queda SIN
  MEDIR (a 58° el píxel MODIS mide del orden de 2 × 5 km y la señal se diluye; D17, remuestreo, es candidata, no
  probada).
- **CÓMO SE VE EN EL DASHBOARD**: dos noches de Chillán sin barra MODIS cuando MIROVA alertó (la noche sí se publicó en
  otra pasada, según el #864).
- **CÓMO REPRODUCIRLO**: `python experiments/_s159/m/cmr_chillan.py`; el probe con `--solo` no existe, se lee el
  estrato S5 del jsonl.
- **CONFIANZA**: CONFIRMADO para «no es la geolocalización» en estos dos gránulos.
- **GRAVEDAD**: 2 (corrige un diagnóstico; no agrega un defecto nuevo).

### H5. El fondo del anillo y la magnitud casi no cambian con MxD03
- **SCRIPT:SALIDA**: `analizar_m_salida.txt`. Δ`t_bg_k` (B − A), mediana: S1 −0,01 K (n = 38, máximo |2,98|), S2
  +0,18 K (n = 25, máximo 1,89), S3 −0,045 K (n = 8). `pc.vrp_mw` B/A, mediana: S1 1,029 (n = 29), S2 1,00 (n = 21).
- **QUÉ PASA**: el anillo de fondo de 5 a 25 km tiene cientos de píxeles (`diag_n_bg_anillo` entre 484 y 857 en los records que revisé), y correrlo
  2 a 3 km cambia poco su mediana. La hipótesis del plan «cambia el fondo» se refuta en la mediana; en casos sueltos el
  fondo se mueve hasta 3 K. La geolocalización **no explica** el déficit de magnitud MODIS de Chillán (#864): en
  2026-10-17 08:50 MIROVA da 7,09 MW, A 0,535 y B 0,470.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 2.

### H6. Los ángulos de observación persistidos también salen de `_interp_geo`
- **ARCHIVO:LÍNEA**: `pipeline/process_modis.py:294` (los ángulos de la grilla gruesa pasan por `_interp_geo`) y
  `:1624-1628` (`observation_geometry` los muestrea en el `final_hotspot`).
- **QUÉ PASA**: `sensor_zenith_deg` y sus pares llevan el mismo corrimiento de muestreo. Según el comentario de
  `:268-271` no entran a detección ni magnitud. **CÓMO SE VE**: invisible (campo de investigación).
- **CONFIANZA**: CONFIRMADO lo leído; el tamaño del error angular no lo medí (SOSPECHA de que es chico: el ángulo varía
  suave). **GRAVEDAD**: 1.

### H7. Fuera del frente: `vigilar-osf-mirova.yml` deja un run fallido sin jobs en cada push de cualquier rama
- **SCRIPT:SALIDA**: `gh run list --workflow vigilar-osf-mirova.yml` muestra al menos 8 runs `push` con `failure` hoy (s159-m,
  s159-m-disparo, s159-n, s159-n-disparo), 0 jobs (`gh api .../runs/39679593175/jobs` da `total_count` 0); el archivo
  sólo declara `workflow_dispatch` y `schedule` y todavía no está en `main`.
- **QUÉ PASA**: es la firma de GitHub para un archivo de workflow que no valida. SOSPECHA de que el `schedule` tampoco
  corra cuando llegue a `main`. **CÓMO SE VE**: invisible para el operador; ruido en Actions y un vigilante que podría
  no vigilar. **CONFIANZA**: SOSPECHA. **GRAVEDAD**: 1.

## Decisiones que no son mías (para Nicolás)

- Leer MxD03 en `process_modis` (S151 ya lo recomendó) cambia qué se publica (H1) y dónde (H2): es un cambio de
  `pipeline/` con ciclo A45 y A/B sobre todos los ángulos, no sólo los de 40°. La medición de este frente sostiene que
  MxD03 es la posición correcta (H2) y que el cambio acerca a MIROVA en 6 de 8 casos con referencia, con un costo (una
  alerta del OSF de 0,44 MW deja de publicarse).
- El borde del círculo de cumbre es frágil por construcción: cualquier corrimiento de 2 a 5 km decide la detección.
  Eso también toca D18 (la caja de 5 × 5 km de Coppola 2016a).

## VERIFICADO LIMPIO

- `calculate_vrp` no usa el MxD03 que recibe: `grep -n geo_path pipeline/process_modis.py` da sólo la firma (`:500`) y
  el docstring (`:513`, «accepted for API compatibility but not used»).
- `run_pipeline` exige el MxD03 y salta el gránulo si falta (`scripts/run_pipeline.py:223-230`, «No geolocation match»):
  la geolocalización no causa huecos de cobertura, sólo de posición.
- El MxD03 cubre el gránulo entero sin relleno: 0 píxeles fuera de [−90, 90] en 85 de 85 (`n_fill_mxd03`).
- La regla de lado del barrido (Aqua con acimut positivo o Terra con acimut negativo = lado del frame 0) coincide con el
  frame real en **85 de 85** (`analizar_m_salida.txt`, «regla=real»): sirve para estratificar desde el JSON sin bajar
  el gránulo.
- La función de producción es determinista: A = A2 en 85 de 85.
- Las versiones: 84 pares de colección 6.1 y 1 de 6.1NRT; el resultado no depende de eso (A reproduce `data/` en 84
  de 85).
- El instrumento de S151 (`comparar`) se reusó sin cambios y reproduce su propio resultado exacto (2,581 km).

## Candidatas para BEYOND_MIROVA_EXTENSIONS §12

(La geolocalización desde MxD03 en sí es paridad, no mejora: ya está en la lista de «donde MIROVA hace algo mejor».)

| id propuesto | qué | por qué podría ser mejor | evidencia | estado |
|---|---|---|---|---|
| MEJ-7 | **Cumbre por huella del píxel, no por su centro** | A 50 a 65° el píxel MODIS mide del orden de 2 × 5 km; decidir «cumbre» por la distancia de su centro al cráter hace que un corrimiento de 2 a 5 km apague o encienda la detección (H1). Una regla por fracción de la huella dentro del círculo (o de la caja de D18) sería estable ante el error de posición | este informe H1 y H3 | idea; va al `experimental` |
| MEJ-8 | **Incertidumbre de posición en cada record** | Guardar la posición MxD03 del píxel y un radio de error que crezca con el cenit (aquí: 0,8 km en el nadir, 2,8 km a 40 a 50°, 5 km sobre 50°, del lado del frame 0) dejaría al operador ver cuándo una detección «a 4,9 km» es en realidad indistinguible de «a 7 km». MIROVA publica `Distancia_km` sin acimut ni error (A93) | este informe H3 | idea |
| MEJ-9 | **Marca de confianza para MODIS sobre ~55° de cenit** | Ahí el corrimiento llega a 5 a 9 km y el píxel es grande: las dos protegidas de Chillán (58°) no se ven con ninguna geolocalización. Una marca «baja confianza geométrica» en la tabla, sin borrar el dato, separaría lo que el sensor puede resolver de lo que no | este informe H3 y H4 | idea; medir contra OVDAS antes de llamarlo mejora |

## Qué no se midió

- Cambios de clase bajo 40° de cenit, salvo S3 (n = 8). El corrimiento existe ahí (0,8 a 1,1 km en el nadir) y puede
  cruzar el borde de inner en Lastarria y Planchón-Peteroa (inner 3 km): SIN DATO.
- VIIRS no se tocó (R2-2 lo da casi nulo; no lo reverifiqué).
- La magnitud con MxD03 en todo el corpus y su efecto sobre el recall nocturno (unidad noche, A94): falta un reproceso
  A/B, que es decisión de Nicolás.
