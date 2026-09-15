# Verificador con contexto limpio: probe del vecino del foco (Fase 1, S141)

Informe verificado: `experiments\_s141_fase1_probe\RESULTADOS.md`.
Fecha: 2026-09-15. Scripts propios (sólo lectura de artefactos): `...\scratchpad\verif_probe\estratificar.py`, salida en `estratificar_out.txt` de la misma carpeta.

## 0. Resumen en una línea

Los números del informe se reproducen exactos, pero **tres de sus lecturas no se sostienen**: el patrón "nevado" es Nevados de Chillán solo, y en Nevados de Chillán el punto de MIROVA está a 13 a 17 km del cráter (no es el mismo foco); M6 es tautológico; y el etiquetado por etapa trata como secuencia rutas que en el pipeline corren en paralelo, así que "perdido_en_cluster" y "perdido_en_test1" no significan lo que el informe dice.

## 1. Re-corrida (encargo §1)

`python experiments/_s141_fase1_probe/juntar.py` y `analisis_posthoc.py`: ambos rc=0. El código de la corrida es el de hoy: `git diff d640e82bd` sobre `probe_vecinos.py`, `analisis_vecinos.py`, `probe_etapas.py`, `pipeline/process_viirs.py` y `pipeline/clustering.py` sale vacío.

Toda cifra de §2 y §4 de RESULTADOS.md coincide con la salida cruda, sin excepción: tabla §2 (29/11, 20/9, 9/2; 0,644/0,607/0,722; 0,411/0,544/0,347; P3 20 y 9), M1 17/23 = 0,7391, tabla M2 a M6 completa (focal y nevado, `hoy_1px`), bloque `todos` (0,333/0,595; −2,32/5,35 K), 16 de 320 vecinos sin BT, y las fracciones de Chaitén 1,17 y 2,09 (1,1727 y 2,0861). No hay diferencias numéricas.

## 2. Veredicto por afirmación

| # | Afirmación | Veredicto | Evidencia | Grav. |
|---|---|---|---|---|
| 1 | Los números salen de dos scripts sobre los artefactos | CONFIRMADA | §1 de este informe | 1 |
| 2 | Tabla §2 y veredicto INDETERMINADO | CONFIRMADA | `criterio_total.json` regenerado | 1 |
| 3 | Descartes 0 de 40, grilla consistente | CONFIRMADA CON MATIZ | `descartes: {}`. `grilla_ok` sólo compara la forma (`analisis_vecinos.py:72-73`); ver §4, V1 para por qué igual es la misma grilla | 1 |
| 4 | P3: "20 siguen publicando 1 píxel hoy" | REFUTADA como está escrita | `pub_n` del backfill es el conteo del núcleo F5 (`scripts/descomponer_magnitud_osf.py:139-143`); `hoy.pc_n` es `primary_cluster.n_pixels` (`probe_vecinos.py:98-100`), otra magnitud. Además 36 de 40 pasadas salen hoy con `single_pixel_mode=True` (`process_viirs.py:1522`, `SINGLE_PIXEL_MAX_CLUSTER_PIXELS=3`), incluidos controles. El probe no captura `f5_core_vrp_mw` de hoy, así que "publica 1 píxel hoy" no se midió | 4 |
| 5 | D1 (control imposible con `pc_n ≤ 4`) es real | CONFIRMADA CON MATIZ | Aritmética correcta, pero supone que el centro está en el cúmulo. Puyehue 2025-03-14: `pc_n=1` y 1 vecino `incluido`, o sea el píxel publicado es un vecino y no el centro | 2 |
| 6 | D2 (aporte con ruido) es real | CONFIRMADA | Chaitén 1,17 y 2,09 con vecinos nunca candidatos; Puyehue 2025-10-02 da 5,51 | 2 |
| 7 | D1 y D2 son los defectos del instrumento | REFUTADA (no son los únicos) | Ver §4: V2 a V8, dos de gravedad 5 | 5 |
| 8 | Focal: los vecinos calientes "sí pasan algún test" y el ensamblado los deja fuera del cúmulo | REFUTADA en su mitad "pasan algún test" | `perdido_en_cluster` en pasadas donde el filtro contextual no corrió = píxel dentro de `mask_contributing` del Test 1, que es **todo píxel del ROI con exceso > 0 sobre la mediana del anillo** (`pipeline/test1_integrated.py:421-444`), no un test por píxel. Lastarria 2025-09-05: los 8 vecinos `perdido_en_cluster` con cúmulo de 1 píxel a 1,34 km del punto OSF; imposible si el filtro contextual hubiera corrido (el cúmulo 8-conexo los habría incluido) | 4 |
| 9 | Focal: "los recorta keep_peak" | CONFIRMADA CON MATIZ | Lo que los saca es la intersección con dNTI_ctx (`process_viirs.py:1798-1799`); `keep_peak` sólo conserva el pico. Es D19 tal como lo nombra el proyecto, pero la palanca es la intersección | 2 |
| 10 | Focal: los vecinos son más fríos que el anillo (M5 −2,27 K) | CONFIRMADA CON MATIZ | Heterogéneo por volcán: Planchón −4,89, Isluga −3,99, Láscar −1,39, Lastarria +0,65, Puyehue +5,26. Sin Planchón el estrato da +0,14 K | 3 |
| 11 | Focal: contra la media de sus vecinos sí tienen exceso (M5 local +2,84 K) | CONFIRMADA CON MATIZ | Sesgo de selección: los `Npix−1` más calientes dan +2,84 K, los 8 vecinos +0,60 K, los restantes +0,42 K. Parte del exceso es haber elegido los más calientes | 3 |
| 12 | Nevado: los vecinos están "por sobre el anillo" (M5 +4,31 K) | **REFUTADA por estratificación** | Es Nevados de Chillán (+8,60 K, 27 de los 35 vecinos del estrato). Sin NdC el estrato da **−9,66 K** (Villarrica −10,98, Chaitén −2,08): el signo se invierte | 5 |
| 13 | Nevado: ningún test los marca "o se pierden en el Test 1" | REFUTADA en su segunda mitad | Los 13 `perdido_en_test1` son todos de NdC, y la etiqueta es artefacto: un píxel de Tests 2/3 que no está en la máscara del Test 1 sale `perdido_en_test1` (`analisis_vecinos.py:61-66`, comprobado con entrada sintética). Villarrica y Chaitén: 8 de 8 `nunca_candidato`, n = 4 pasadas | 5 |
| 14 | Nevado: "el problema es de detección, no de fondo" | NO VERIFICABLE hoy | Con NdC fuera quedan 4 pasadas; M3 = 0 es consecuencia mecánica de que ninguno fue marcado, no una medición del fondo | 4 |
| 15 | M1: "el instrumento ve la inclusión cuando existe; el control falló sólo por D1" | CONFIRMADA CON MATIZ | 17/23 exacto, pero 3 de 11 controles hoy tienen `pc_n=1` (Lastarria ×2, Puyehue 2025-10-02) y aportan 0 alcanzables; Láscar 2025-10-27 da 0 de 1. M1 sólo prueba el lado "incluido", no que las etapas de pérdida estén bien rotuladas | 3 |
| 16 | Tabla M2 a M6 | CONFIRMADA (números) | `posthoc.json` regenerado | 1 |
| 17 | Con los 29 candidatos "el patrón se repite" | CONFIRMADA CON MATIZ | NdC está en ambos conjuntos; la repetición no es independiente | 3 |
| 18 | M6: el centro está a < 1 píxel del píxel caliente OSF, "la comparación mira el mismo foco" | **REFUTADA** | Tautológico: el centro se elige como el píxel más cercano al punto OSF (`analisis_vecinos.py:77-79`), así que la distancia queda bajo media diagonal por construcción. Lo que importa es dónde está nuestro cúmulo: centroide publicado a **13,0 a 15,2 km** del punto OSF en las 4 de NdC, 1,1 a 3,4 km en Chaitén 03-16 y 07-04 y Lastarria 02-16 y 09-05. En NdC el punto OSF está a 13,3 a 17,3 km del `vent` del probe con 2,3 a 12,2 MW y 4 a 16 píxeles: no es el cráter. Además el centro no es el pico local en 3 pasadas (NdC 02-16, 03-05, Isluga 08-06) y es NaN en 2 (Láscar 07-01, Isluga 05-27) | 5 |
| 19 | 16 de 320 vecinos sin BT no entran a M5 | CONFIRMADA | conteo propio 16/320 | 1 |
| 20 | Nada de esto es veredicto; propuesta §5 | CONFIRMADA en la forma | El informe sí lo declara post hoc. Pero §5.2 propone un brazo apoyado en afirmaciones 8, 12 y 13, que no se sostienen | 3 |
| 21 | Hallazgo previo de D1/D2 en Chaitén antes de ver el total; corrida 34928488409 | NO VERIFICABLE | No hay registro leído en esta sesión; no se consultaron los runs | 1 |

## 3. Tabla por volcán (candidatos que hoy tienen `pc_n = 1`, definiciones de `analisis_posthoc.bloque`)

| volcán | estrato | n | vecinos calientes por etapa | frac. nunca | M3 | M5 local K | M5 anillo K |
|---|---|---|---|---|---|---|---|
| Isluga | focal | 2 | nunca 5 · cluster 1 | 0,833 | 0,056 | 0,49 | −3,99 |
| Láscar | focal | 1 | ctx_filter_out 4 | 0,000 | 0,362 | 5,60 | −1,39 |
| Lastarria | focal | 3 | cluster 5 · ctx_filter_out 2 | 0,000 | 1,232 | 2,44 | +0,65 |
| Planchón-Peteroa | focal | 4 | ctx_filter_out 5 · cluster 3 · nunca 1 | 0,111 | 0,517 | 2,92 | −4,89 |
| Puyehue-CC | focal | 2 | cluster 3 · incluido 1 | 0,000 | 0,796 | 6,24 | +5,26 |
| Chaitén | nevado | 1 | nunca 2 | 1,000 | 0,000 | 1,26 | −2,08 |
| Nevados de Chillán | nevado | 4 | nunca 14 · test1 13 | 0,519 | 0,343 | 3,15 | +8,60 |
| Villarrica | nevado | 3 | nunca 6 | 1,000 | 0,000 | 0,03 | −10,98 |

Peso en M2: focal Isluga 6, Láscar 4, Lastarria 7, Planchón 9, Puyehue 4 (30); nevado Chaitén 2, **NdC 27**, Villarrica 6 (35).

Dejando un volcán fuera: focal sin Isluga, frac. nunca 0,042; sin Planchón, M5 anillo +0,14 K. **Nevado sin NdC: frac. nunca 1,0, M3 0, M5 anillo −9,66 K.** NdC sostiene solo el patrón nevado de M5 y todo el `perdido_en_test1`; Isluga sostiene casi solo el `nunca_candidato` focal; ningún volcán focal comparte el signo y la etapa dominante con los demás en más de dos de las tres cifras.

## 4. Instrumento: hallazgos propios

**V1. Misma grilla y mismo momento: VERIFICADO LIMPIO para el perfil actual.** `compute_test1_mir` recibe `bt=bt, lat=lat, lon=lon` (`process_viirs.py:1099-1101`) y `first_pass_tests_2_and_3` recibe `bt=bt` (`:1240-1241`) en el mismo alcance; `bt` no se reasigna hasta `:1609`, después del ensamblado. Es la escena completa, no un recorte. Entre el segundo pase y el cúmulo de `:1467` no hay filtros activos: `ENABLE_FINAL_PIXEL_FILTER`, `PATH_D_REQUIRES_COVALIDATION` y `ENABLE_EXCLUDE_ZONES` dan False (leídos de `pipeline.process_viirs` con `VRP_PROFILE=mirova_equivalent`). `second_pass_adjacent` devuelve `active_mask | newly_active` (`detection_context.py:949`), así que la unión incluye el primer pase, como supone el análisis. Las llamadas de `:1149` y `:1164` (ETI de escena) no corren: `ENABLE_ETI_QUADRATIC_SCENE=False`.

**V2. Etapas paralelas leídas como secuencia (gravedad 5).** `ORDEN` pone `first_pass, second_pass, test1, ctx_filter_out, cluster` en fila (`analisis_vecinos.py:24`), pero el pipeline tiene dos rutas: Tests 2/3 más segundo pase alimentan el cúmulo contextual (`process_viirs.py:1467`), y Test 1 más filtro contextual alimentan el cúmulo del Test 1 (`:1910`), que sólo reemplaza al primero si la fuente interna es `test1` (`:1861`, `:1881`). Comprobado con entradas sintéticas: un píxel de Tests 2/3 que no está en el Test 1 sale `perdido_en_test1`; un píxel sólo del Test 1 con el filtro sin correr sale `perdido_en_cluster`. Ninguna de las dos etiquetas describe una pérdida en esa etapa.

**V3. La máscara del Test 1 no es un test por píxel (gravedad 5).** `mask_contributing` = exceso MIR > 0 sobre la mediana del anillo, dentro del ROI de 3 km (`test1_integrated.py:421-444`). Es D2 otra vez: medio ROI puede quedar "marcado". M3 cuenta esos píxeles como "marcados y perdidos", así que M3 no corrige D2 como dice su definición.

**V4. `alertado` incluye el halo del Test 1 (gravedad 3).** `resumir_vecindario` une todas las máscaras en `alertado` (`analisis_vecinos.py:80-83`), así que el fondo local excluye píxeles que MIROVA sí usaría como fondo. 7 de 30 vecinos calientes focales quedan con `fondo_local_k = None` y aporte 0.

**V5. Muestra: el punto OSF no es nuestro foco (gravedad 5).** El pareo sólo exige que **nuestro** cúmulo esté dentro del radio interno (`descomponer_magnitud_osf.py:86-89`); no mira dónde está el píxel de MIROVA. En NdC las 4 pasadas comparan un foco de MIROVA a 13 a 17 km del cráter (2 a 12 MW) contra nuestro cúmulo del cráter (0,04 a 0,06 MW). Esa brecha no es de vecinos no sumados.

**V6. P3 mide otra cosa (gravedad 4).** Ver afirmación 4. Tampoco se registra si hoy aplica el modo de un píxel ni el núcleo F5.

**V7. Brecha con el publicado del backfill, vecinos con el código de hoy (gravedad 3).** `probe_vecinos.py:106` usa `persistido.pub_mw`. Diferencias grandes contra el `pc.vrp_mw` de hoy: Planchón 2025-08-27 brecha 0,080 contra 0,322; Láscar 2025-11-14 0,311 contra 0,185; Láscar 2025-10-27 (control) −0,012 contra 0,285.

**V8. Captura del cúmulo (SOSPECHA, gravedad 3).** `mascaras_de` toma `ci[-1]` (`probe_vecinos.py:65-70`). Con el código de hoy la última llamada coincide con el cúmulo publicado cuando corre `:1910` con cúmulos no vacíos (publica `t1_clusters[0]`) o cuando sólo corre `:1467` (publica `_clusters[0]`); con `vent_anchored` el índice 0 es el primario en ambas. El caso que rompería la correspondencia (llamada en `:1910` con lista vacía, que dejaría `primario=[]` mientras se publica el de `:1467`) no se puede descartar desde los artefactos, porque no guardan índices ni la fuente interna. Indicio a favor de revisarlo: Láscar 2025-10-27 control, `pc_n=2`, centroide a 0,135 km del punto OSF y 0 vecinos incluidos.

**V9. `nunca_candidato` por etapa que no corrió (SOSPECHA, gravedad 2).** Si el primer pase se salta (`_path_d_atm_gate_skip`, `process_viirs.py:1011`, `:1212`), el cúmulo sale de `combine_hot_paths` (`:1191`) con rutas que el probe no captura, y un píxel de esas rutas fuera del cúmulo saldría `nunca_candidato`. `diag_n_first_pass_pixels = 0` en 4 pasadas no distingue "corrió y quedó vacío" de "no corrió".

**V10. Orden con NaN en `_calientes` (gravedad 1).** La clave `-(bt_k or -1)` no maneja NaN; hoy los 16 sin BT vienen como `None` y quedan al final, sin efecto medido.

## 5. VERIFICADO LIMPIO

- Reproducción exacta de todos los números (§1).
- Código de la corrida idéntico al del árbol actual.
- Misma grilla y mismo instante de cálculo para BT, lat, lon y las máscaras de primer pase, segundo pase y Test 1 (V1).
- La unión del segundo pase contiene al primer pase; las llamadas ETI de escena no contaminan la unión con el perfil actual.
- Con `vent_anchored`, el índice 0 de `cluster_hotspots` es el cúmulo que se publica en ambas llamadas.
- El informe declara lo post hoc como tal y no adopta brazo.

## 6. Qué debe cambiar en el instrumento v2

1. **Filtrar la muestra por posición del foco de MIROVA**, no sólo del nuestro: exigir punto OSF a ≤ 0,75 km de nuestro píxel pico o del cráter, y reportar las excluidas. Sin eso NdC 2025-02 no entra.
2. **Rotular por ruta, no por secuencia**: guardar la fuente interna (`final_hotspot_source` antes del ancla honesta) y clasificar cada vecino dentro de la ruta que publicó (contextual: Tests 2/3, segundo pase, cúmulo; Test 1: filtro contextual, cúmulo). La máscara `mask_contributing` del Test 1 no cuenta como "marcado".
3. **Guardar evidencia del cúmulo publicado**: índices del cúmulo que terminó en `primary_cluster`, marcando de qué llamada vino, y si el centro pertenece a él. Registrar qué etapas corrieron (booleano por etapa), no inferirlo de `None`.
4. **Centro = nuestro píxel pico del cúmulo publicado**, con la distancia al punto OSF como variable de pareo; M6 debe medir esa distancia, no la del píxel más cercano.
5. **Medir lo que hoy se publica**: capturar `f5_core_vrp_mw`, su conteo y `single_pixel_mode`; la brecha se calcula contra el publicado de la misma corrida.
6. **Fondo local con la máscara de alertas que se publicaría** (Tests 2/3 más segundo pase de la ruta ganadora), no con la unión de todo.
7. **Contraste contra la selección**: M5 sobre los `Npix−1` calientes y, como referencia, sobre los restantes y sobre vecinos de un píxel de control lejos del foco.
8. **Pre-registrar por volcán además de por estrato**, con mínimo de pasadas por volcán y un leave-one-out en el criterio; hoy un volcán invierte el signo del estrato nevado.
