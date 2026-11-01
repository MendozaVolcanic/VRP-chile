# Verificador con contexto limpio: pre-registro S157 1.29 (D25 sobre K)

**Veredicto global: PARCIAL.** Las cifras del §4 salen exactas de `sustrato_k.py`, los perfiles y su prueba hacen lo que
declaran y el probe reproduce el primer pase real; pero el criterio de magnitud tiene tres puntos que pueden hacerlo
medir otra cosa sin dar error (kernel local en 5 volcanes, el estrato oblicuo excluido por un argumento que sólo vale
para Chillán, un nulo y un ruido que no pueden fallar), y el evaluador heredado de F/K da INDECIDIBLE por construcción
con MODIS apagado si nadie lo ajusta.

Revisado en `D:\vrp-trabajo\s157-prereg-d25` (rama `s157-prereg-d25`, commit `b84a5c394`, base `8c94c847b`). `origin/main`
avanzó a `f101d7304` (#868), que sólo cambia comentarios de una línea en `pipeline/process_modis.py`,
`pipeline/process_viirs.py` y `frontend/index.html`: las líneas citadas en el §3 no se mueven (`git diff 8c94c847b
origin/main -- pipeline/ frontend/index.html`, reemplazos de una línea por una línea).

Escala: 1 = más grave, 5 = menor. Scripts y salidas de este informe, en `verificador/`:
`v1_poblaciones_ocultas.py` (`v1_salida.txt`), `v2_mutaciones_perfiles.sh` (`v2_salida.txt`),
`v3_rescate_por_noche.py` (`v3_salida.txt`), `v4_probe_reproduce_first_pass.py` (`v4_salida.txt`). La copia unida K que
usan v1 y v3 la arma `sustrato_k.py --tmp D:\vrp-trabajo\temporales\verif_s157` (la re-corrida de abajo).

---

## Gravedad 2

### H1. En VIIRS 375 el control no resta la mediana del anillo en 5 de los 11 volcanes: tienen el kernel local 3x3, y ahí D25 casi no hace nada

- **Dónde**: `PREREGISTRO.md:13` («Nuestro pipeline resta como fondo la mediana de ese anillo»), `:139` (predicción 1),
  `:145` (predicción 5, Lastarria); `pipeline/process_viirs.py:1471` (`if ENABLE_LOCAL_KERNEL_BG and
  local_kernel_bg_compatible`), `volcanoes.yaml` (`local_kernel_bg: true` en Puyehue-Cordón Caulle, Villarrica, Chaitén,
  Planchón-Peteroa y Lastarria).
- **Qué pasa**: con K (`ENABLE_LOCAL_KERNEL_BG True`, resuelto desde `pipeline.profile` en los cuatro brazos) esos 5
  volcanes ya restan en VIIRS 375 la media de temperatura de los 8 vecinos no alertados. D25 cambia eso por la media de
  radiancia con ventana hasta 7x7: casi lo mismo. La tarea 1.14 lo midió: «0,99 a 1,00 en los volcanes con kernel
  local» (`experiments/_s151_presupuesto_magnitud/README.md:124`) y lo pidió mirar aparte (`:175`). El documento no lo
  nombra, describe a todo el control como «anillo», y la predicción 5 explica a Lastarria con «vecinos más tibios que el
  anillo» cuando en K Lastarria no usa el anillo en VIIRS 375. VIIRS 750 no tiene kernel (`process_viirs_mod.py`
  recibe `local_kernel_bg_compatible` pero no lo usa), así que ahí sí es anillo contra vecinos.
- **Cómo se ve**: de los pares que deciden M en VIIRS 375 con cenit ≤ 40°, son de volcanes con kernel **63 de 166 en V1
  y 103 de 211 en V2** (`v1_salida.txt`, líneas `pares VIIRS375 cenit<=40 {'total': 166, 'otro': 103, 'Chillan': 16,
  'kernel': 63}` y `{'total': 211, 'otro': 108, 'Chillan': 0, 'kernel': 103}`). Con casi la mitad de los pares en d ≈ 0,
  la mediana de d se arrastra a cero: M puede salir NEUTRO por dilución aunque D25 mejore en los otros seis volcanes.
- **Reproducir**: `python experiments/_s157_prereg_d25/verificador/v1_poblaciones_ocultas.py --kunido
  D:\vrp-trabajo\temporales\verif_s157\k_unido`.
- **Confianza**: alta en el hecho (código, YAML y conteo); media en el tamaño del efecto (el 0,99 a 1,00 es de 1.14 en
  `literal`, no sobre K).
- **Cambio propuesto**: decir en §1 y §3 que en VIIRS 375 el control es kernel en esos 5; estratificar M en VIIRS 375
  por «con kernel / sin kernel» y decidir con el estrato sin kernel (o con los dos y declarar cuál manda); corregir la
  predicción 5.

### H2. Excluir de la decisión a VIIRS 375 con cenit > 40° se justifica con Chillán, pero el estrato es casi todo de otros volcanes, y ahí D25 puede pasarse

- **Dónde**: `PREREGISTRO.md:27` (techo), `:127` y `:128` (M375 oblicuo informa), `:136`, §8 a.
- **Qué pasa**: el argumento es físico y de Chillán: un foco de 330 K frente a un fondo de 272 K, donde el fondo pesa
  poco y ni con fondo cero se llega a MIROVA (#869, «en Chillán», `experiments/_s157_magnitud_chillan/README.md` §5.1).
  Pero los pares excluidos son **131 en V1, de los que 28 son de Chillán, y 189 en V2, de los que 0 son de Chillán**
  (`v1_salida.txt`). El resto son focos débiles (Láscar, Isluga, Tupungatito, Puyehue), donde el fondo pesa mucho: 1.14
  midió ahí D25 ×1,72 en Isluga y ×2,37 en Tupungatito, y el efecto **más grande** en el borde (×1,41,
  `_s151_presupuesto_magnitud/README.md:124` y `:128`). Que D25 «no pueda cerrar» en Chillán no dice que no pueda
  mejorar ni, sobre todo, que no pueda **pasarse** en los demás. Con el estrato en «informa», un EMPEORA por
  sobre-corrección en VIIRS 375 oblicuo no impide CUMPLE.
- **Cómo se ve**: la decisión «M no decide en VIIRS 375 > 40°» aparece como consecuencia técnica de #869, y es una
  elección de alcance.
- **Reproducir**: ídem H1 (líneas `pares VIIRS375 cenit>40`).
- **Confianza**: alta en los conteos; la dirección del efecto en los volcanes débiles oblicuos es SOSPECHA (no medida
  sobre K).
- **Cambio propuesto**: que VIIRS 375 > 40° **decida en la dirección EMPEORA** (un EMPEORA ahí bloquea CUMPLE) aunque
  su MEJORA no cuente; o excluir sólo a Chillán de ese estrato. Y llevarlo al §8 a como lo que es: una decisión de
  Nicolás, con los conteos por volcán a la vista.

### H3. El nulo del §7.5 y el ruido de M no pueden fallar

- **Dónde**: `PREREGISTRO.md:127` (ruido de M = «mediana de abs(d) entre K' y K»), `:126` (ruido de P2), `:195` (nulo).
- **Qué pasa**: (a) el ruido de M sale de K' contra K. Con el desempate explícito de S151 1.22 (`process_viirs.py`,
  `orden_vrp_descendente`), el gemelo da lo mismo que el control: 1.14 midió el gemelo en «**1,00 exacto**» en 88 pasadas
  (`_s151_presupuesto_magnitud/README.md`, fila «nulo: gemelo del control»). La mediana de abs(d) es 0 y la condición
  «la mediana pasa el ruido» se cumple con cualquier mediana distinta de cero. En V2 no hay gemelo y el documento no dice
  de dónde sale el ruido de M (sí lo dice para P2). (b) El nulo «evaluador con K' en el lugar de D» compara al gemelo
  contra el control **con el ruido medido entre esos mismos dos**: toda diferencia de P1 es «ruidosa» (INDECIDIBLE, nunca
  VETADO), P2 queda en EMPATE por definición del ruido, y M da d = 0. Es el caso que A116 (2) describe: el nulo sólo
  «funciona» donde la pregunta no aplica. La prueba sintética «cuatro brazos idénticos» del candado tiene el mismo
  problema.
- **Cómo se ve**: dos controles declarados «medidos, no razonados (A110, A116)» que no tienen camino para dar rojo.
- **Reproducir**: leer `PREREGISTRO.md:127` y `:195` junto a la fila del gemelo de 1.14; no hace falta correr nada.
- **Confianza**: alta en (b) por construcción; alta en que el ruido de M será 0 o casi (SOSPECHA hasta ver K' contra K).
- **Cambio propuesto**: declarar que el ruido de M es 0 y que M decide sólo con el intervalo bootstrap; reemplazar el
  nulo por uno que pueda fallar (por ejemplo, correr el evaluador con D contra K pero con el VRP de MIROVA barajado
  dentro de cada volcán, sensor y tramo, y exigir NEUTRO; o una prueba sintética donde D = K salvo un cambio chico de
  signo aleatorio, que tiene que dar NEUTRO y no MEJORA); decir qué ruido usa M en V2.

### H4. Con MODIS apagado, el evaluador de F/K reusado «con los brazos parametrizados» da INDECIDIBLE por construcción

- **Dónde**: `PREREGISTRO.md:184` a `:195` (§7.1 y §7.4), `:203` («el evaluador de F/K ... con los brazos
  parametrizados ... sin tocar el archivo de F/K»); `experiments/_s151_prereg_fk_11/evaluar_fk.py:149` a `:160`
  (`claves_produccion` junta los tres sensores de producción), `:464` a `:472` (cobertura contra producción), `:451` a
  `:458` (paridad entre brazos y protegidas sin record en algún brazo), `:511` a `:518` (determinismo por `SENS`, con
  `ok = bool(amb) and ...`).
- **Qué pasa**: producción tiene MODIS; los brazos no. Copiando la lógica de F/K, a cada volcán le «faltan» el 100 % de
  sus pasadas MODIS (cobertura corta), las protegidas MODIS quedan «sin record en algún brazo» y el determinismo de MODIS
  da `amb` vacío, o sea `ok = False`. Las tres cosas llevan a CONTROLES GENERALES FALLAN y nada decide. No es silencioso
  (sale rojo), pero el documento no lo anticipa y el candado podría pasar sus pruebas sintéticas si éstas no traen
  MODIS en producción.
- **Cómo se ve**: `PREREGISTRO.md` dice «el control contra lo que hay en disco con K ... en algún volcán y sensor» sin
  excluir MODIS.
- **Reproducir**: leer las líneas citadas de `evaluar_fk.py`; `scripts/run_pipeline.py:213` confirma que
  `SENSOR_MODIS False` sólo salta el procesamiento.
- **Confianza**: alta.
- **Cambio propuesto**: escribir en §7.1, §7.4 y en el candado que los sensores del A/B son sólo VIIRS 375 y 750 en
  cobertura, determinismo, protegidas sin record, P1 y P2; y agregar a `probar_evaluar_d25.py` una prueba con MODIS en
  producción y ausente en los brazos que tiene que dar cobertura OK.

---

## Gravedad 3

### H5. La tabla de consumidores describe mal cómo D25 mueve la selección del cúmulo

- **Dónde**: `PREREGISTRO.md:65`; `pipeline/clustering.py:144`, `:145`, `:149` a `:153`; `pipeline/anchor.py:82` a
  `:84`; `pipeline/process_viirs.py:2121` a `:2135`.
- **Qué pasa**: con `vent_anchored` (K), dentro del inner gana el cúmulo **más cercano**; el VRP sólo desempata
  (`_vent_key = (0 si adentro, distancia, -vrp)`). Lo que D25 mueve es otra cosa: el ranking se arma sólo con los
  cúmulos de VRP mayor que cero (`with_vrp`). Un cúmulo del cráter en 0,0 MW pierde contra un cúmulo **lejano** con VRP,
  el ancla honesta toma ese centroide y `distance_class` pasa a `far`. Con D25 el del cráter puede pasar a VRP > 0, volver
  a ganar y la pasada pasa de `far` a `summit` (y al revés si D25 lo deja en cero). El cambio es summit/far, no «cuál de
  los del inner».
- **Cómo se ve**: el sustrato no cuenta esta población (ver H13), y P4 lo ve como «el cúmulo se mueve» sin decir que
  cambia la etiqueta.
- **Reproducir**: leer las líneas citadas.
- **Confianza**: alta.
- **Cambio propuesto**: reescribir la fila: «qué cúmulo es primario: el filtro de VRP > 0 del ranking puede cambiar
  summit por far o al revés», y contar en P4 aparte las pasadas cuyo `distance_class` cambia.

### H6. El veto del §4 cuenta protegidas que el mismo documento dice que no deciden

- **Dónde**: `PREREGISTRO.md:99` y la fila siguiente; `:82` a `:84` (V1: las filas sólo OCR de Suomi NPP antes del
  2026-10-09 «no deciden con la lectura A, se listan»).
- **Qué pasa**: `sustrato_k.py` no separa esas filas (la versión de F/K sí lo hacía, columna `snpp`,
  `experiments/_s151_prereg_fk_11/sustrato.py:71` a `:78`). De las protegidas que K publica en V1, **7 de 38 en VIIRS 375
  y 2 de 31 en VIIRS 750** descansan sólo en OCR de Suomi NPP (`v1_salida.txt`: `'pA_pub': 38, 'pA_pub_solo_ocr_snpp':
  7` y `'pA_pub': 31, 'pA_pub_solo_ocr_snpp': 2`). Las que deciden son 31 y 29, y la fracción detectable al 80 % pasa de
  4,1 y 5,1 % a 5,1 y 5,4 % (misma fórmula de `fk.poder`).
- **Reproducir**: `v1_poblaciones_ocultas.py` (arriba).
- **Confianza**: alta.
- **Cambio propuesto**: agregar la columna `snpp` a `sustrato_k.py` y usar en el §4 los denominadores que deciden.

### H7. El corte de 40° no es «dónde #869 mostró que D25 puede actuar»

- **Dónde**: `PREREGISTRO.md:27` («techo 0,64 a 0,68 sobre 40°»), `:136`.
- **Qué pasa**: #869 midió el techo por **bandas de 30 a 50° y de 50° o más** (G con fondo 0 de 0,64 y 0,68,
  `_s157_magnitud_chillan/README.md` §2.2 y §3), no sobre y bajo 40°. El 40° es el corte de D17 (nota S141). Con la
  banda de #869, entre 30 y 40° D25 tampoco cierra en Chillán, y esos pares quedan **dentro** del estrato que decide:
  42 de 166 en V1 y 57 de 211 en V2 (`v1_salida.txt`, `pares VIIRS375 30-40`). El techo de #869 además es sólo de
  Chillán.
- **Confianza**: alta.
- **Cambio propuesto**: decir que el 40° es el de D17, elegido, y que no coincide con las bandas de #869; o decidir con
  < 30° si se quiere ser fiel a #869. Y bajar «sobre 40°» a «en las bandas de 30 a 50° y de 50° o más».

### H8. P2 y el sustrato cuentan pasadas; en noches (A94) el balance cambia

- **Dónde**: `PREREGISTRO.md:107` a `:113`, `:126`, predicción 4 (`:143`).
- **Qué pasa**: en VIIRS 750 las 11 y 23 alertas «recuperables» caen todas en noches que K ya publica por otra pasada,
  y los 17 y 21 negativos «encendibles» caen en noches en que K ya publica algo (0 noches nuevas en ambas ventanas). En
  VIIRS 375 de V2, los 2 encendibles serían 2 noches nuevas (`v3_salida.txt`). O sea que, en la unidad del operador,
  D25 en VIIRS 750 no cambia nada de lo que se ve por noche en esos conteos, y un GANA o PIERDE de P2 por pasadas puede
  no tener contraparte en noches. D25 ya lo había anotado así en S145 («en noches el premio es cero»,
  `docs/MIROVA_DIVERGENCES.md`, sección D25).
- **Reproducir**: `python v3_rescate_por_noche.py --kunido D:\vrp-trabajo\temporales\verif_s157\k_unido`.
- **Confianza**: alta en el conteo (cuenta publicación de K en cualquier sensor de esa noche y volcán).
- **Cambio propuesto**: informar P2 también en noches-volcán y decir cuál manda si discrepan.

### H9. CUMPLE se gana con un MEJORA en cualquiera de seis estratos, y sin pedir que mejore el caso que motivó el A/B

- **Dónde**: `PREREGISTRO.md:232` y `:233`.
- **Qué pasa**: deciden 2 ventanas por 3 estratos (VIIRS 750 ≤ 40 y > 40, VIIRS 375 ≤ 40). Con intervalos al 95 %, la
  probabilidad de que al menos uno quede entero bajo 0 por azar es del orden de 6 × 2,5 % ≈ 14 % (SOSPECHA: los estratos
  no son independientes). Y un MEJORA en V2 VIIRS 750 ≤ 40° (0 pares de Chillán) basta para CUMPLE aunque en V1 Chillán
  quede NEUTRO. Además el bootstrap remuestrea pasadas como independientes, y las pasadas de una misma noche y volcán no
  lo son (Chillán aporta 19 de los 23 pares de VIIRS 750 > 40° en V1, `v1_salida.txt`).
- **Confianza**: media.
- **Cambio propuesto**: exigir MEJORA en al menos un estrato **de cada ventana**, o en el estrato combinado; bootstrap
  por bloques de noche-volcán; informar M por volcán (A83, S126).

### H10. La decisión §8 b depende de un probe que hoy no puede correr, y no tiene salida si no corre

- **Dónde**: `PREREGISTRO.md:219` a `:222`; `probe_l1b/README.md` (sin resultado; CMR caído según el encargo).
- **Qué pasa**: «se toma con el resultado del probe a la vista, antes de despachar». Si CMR sigue caído, el despacho
  queda bloqueado sin regla. Además «la mitad de los píxeles» y «5 %» son umbrales elegidos (A115 pide decirlo).
- **Confianza**: alta.
- **Cambio propuesto**: una regla por defecto («sin probe al momento del candado: sólo D») y declarar los dos umbrales
  como elegidos.

---

## Gravedad 4

### H11. El probe atribuye el rechazo de los vecinos al primer pase; con K la etapa que decide es el segundo pase

- **Dónde**: `probe_l1b/probe_chillan.py`, `vecinos_no_alertados` (columnas `pasa_t2`, `pasa_t3`, `pasa_bt`);
  `pipeline/process_viirs.py:1336` a `:1390` (segundo pase sin condicionar, `ENABLE_SECOND_PASS_ADJACENT True`,
  `ENABLE_SECOND_PASS_CONDITIONED False`, y `hot_mask_2d = final_active_mask`); `pipeline/detection_context.py:822`
  (`second_pass_adjacent`: recalcula dNTI y dETI **sin** los activos en la media, sin compuerta de temperatura).
- **Qué pasa**: el diagnóstico reproduce **exacto** el primer pase real bajo `max` (abajo, VERIFICADO LIMPIO), pero un
  vecino no alertado en la máscara final fue rechazado también por el segundo pase, con otro dNTI (más alto, porque ya
  no lo contaminan los activos) y otro μ y σ. Reportar el dNTI del primer pase y «BT» como motivo puede exagerar la
  distancia al umbral y nombrar una compuerta que la etapa decisiva no aplica. En la escena sintética no apareció ningún
  vecino atribuido sólo a BT (`v4_salida.txt`: 0), así que el riesgo de atribución equivocada es SOSPECHA.
- **Cambio propuesto**: agregar al diagnóstico el dNTI, dETI y umbrales del segundo pase (capturando
  `second_pass_adjacent`), y rotular las columnas actuales como «primer pase».

### H12. El consumidor «píxel de más energía» y el filtro de distancia de `store.py` no están en la tabla A118

- **Dónde**: `pipeline/process_viirs.py:1536` y `process_viirs_mod.py:1081` (`hotspot_lat = anomaly_pixels[0]`, el de
  más VRP, que D25 reordena); `pipeline/store.py:381` a `:435` (si ese píxel cae fuera del radio y `cluster_rescues` es
  falso, que depende de `pc.vrp_mw > 0`, el record queda con `vrp_mw = 0`, `discarded_reason` y `anomaly_pixels = []`);
  `frontend/index.html:1609` (`isSummitDetection` descarta `vrp_mw === 0` con `discarded_reason`).
- **Qué pasa**: D25 puede cambiar qué píxel es el «más caliente» y si el cúmulo rescata. En la práctica casi todo esto
  se mueve junto con `pc.vrp_mw` (que P1 y P2 ya cuentan), pero el top-100 y el vaciado de `anomaly_pixels` también
  alimentan el núcleo F5'.
- **Cambio propuesto**: una fila más en el §3; en P5 contar los `discarded_reason` que cambian entre K y D.

### H13. El «rescatable» no ve los cúmulos del cráter mudos detrás de un primario lejano; el resto de lo que D25 podría encender sí está acotado

- **Dónde**: `sustrato_k.py`, `rescatable` (exige `dc == "summit"`); `PREREGISTRO.md:111` («como mucho»).
- **Qué pasa**: por H5, una pasada con un cúmulo del cráter en 0,0 MW y un primario lejano con VRP queda `far` y fuera
  del conteo. Medido como cota inferior (píxeles guardados en 0,0 MW dentro del inner con el primario fuera): **VIIRS
  375: 1 negativo y 2 alertas en V1, 1 negativo en V2; VIIRS 750: 0** (`v1_salida.txt`, `a_neg_limpio`, `a_pos`).
  También busqué publicaciones escondidas hoy por `isCirrusArtifact` o `isDiffuseFieldArtifact` que D25 podría
  destapar al bajar la magnitud bajo su umbral (el §3 sólo mira la dirección contraria): **0** en las dos ventanas.
  El control de mi script reproduce exacto los rescN y rescP del sustrato (V1: 0/4 y 17/11; V2: 2/6 y 21/23).
- **Confianza**: alta en los conteos; la cota de (a) es inferior porque `anomaly_pixels` guarda sólo 100 píxeles y la
  distancia del píxel se mide desde `volcano_lat/lon`, no desde el ancla.
- **Cambio propuesto**: cambiar «como mucho» por «del orden de», nombrar esa población chica y la dirección inversa de
  los filtros.

### H14. M no dice qué hace con las alertas mínimas (SN), con las «sin geometría» ni con los pares que D25 saca del conjunto

- **Dónde**: `PREREGISTRO.md:82` a `:86`, `:120` a `:127`.
- **Qué pasa**: (a) la regla SN pasa a «no vio nada» las alertas de VIIRS 375 de 0,05 MW o menos (37 en V1, 36 en V2,
  `sustrato_k_salida.txt`); no se dice si entran a M, donde un VRP de MIROVA tan chico pesa mucho en escala log.
  (b) Las `ALERTA_SIN_GEOMETRIA_OCR` «sí sirven para magnitud»: no se dice si deciden M o sólo informan. (c) M sólo
  mira pares que **los dos** publican: una pasada que D25 lleva a 0,0 (el peor alejamiento posible) sale de M; queda
  contada en P1 o P2, pero el estimador de M queda sesgado hacia MEJORA.
- **Cambio propuesto**: fijar las tres cosas por escrito; informar cuántos pares salen de M en cada dirección.

### H15. El C1 nuevo de `sustrato_k.py` es una prueba de regresión del cargador, no un control positivo de V1

- **Dónde**: `sustrato_k.py`, docstring C1 y `main()`.
- **Qué pasa**: el C1 vuelve a contar 158 con la misma referencia congelada de V2, la misma función y la misma ventana
  que dieron 158 en F/K (`experiments/_s151_prereg_fk_11/sustrato_salida.txt:86`). Sirve para ver que el cargador no
  derivó, y el cambio está bien motivado (la unión viva da hoy `{'A': 478, 'B': 1053}`, comprobado en esta sesión). Pero
  no toca `_congelado_v1`: V1 queda sin control positivo propio (C2 comparte el indexado de la referencia en sus dos
  caminos; C3 es negativo).
- **Cambio propuesto**: decirlo así en el §4, y si se quiere un positivo de V1, contar las protegidas A de V1 leyendo el
  CSV crudo con un camino independiente de `banco_paridad`.

### H16. La evidencia previa en contra de la predicción 1 no está citada

- **Dónde**: `PREREGISTRO.md:139`; `docs/MIROVA_DIVERGENCES.md`, sección D25 (S145): «en VIIRS 375 el fondo del
  cúmulo ya se midió con criterio pre-registrado y no cerró la brecha en ningún volcán» (`docs/HYPOTHESIS_LOG.md:1509`,
  H_S141_VECINO_FOCO_V2).
- **Cambio propuesto**: citarla junto a la predicción 1 y decir en qué se diferencia de D25 sobre K.

---

## Gravedad 5

- **H17. Costo**: «sin MODIS debería ser menos» (`PREREGISTRO.md:176`). `SENSOR_MODIS` sólo salta el procesamiento
  (`scripts/run_pipeline.py:213`); `fetch.fetch_for_volcano` no lee el perfil (`grep SENSOR_ pipeline/fetch.py`: 0), así
  que el L1B de MODIS se sigue bajando. El ahorro es sólo de proceso.
- **H18. Despacho**: «el siguiente recién cuando el anterior empezó» (`PREREGISTRO.md:161` y `:162`) contradice el
  comando que sigue, que exige 0 corridas no completadas (o sea, que el anterior **terminó**). Elegir una.
- **H19. §4, fila «alertas bajo 1 MW»**: los conteos son con la regla original; el §5 decide con SN. Rotularlo.
- **H20. `RESUMEN_SELLO.md`**: remite a «la sección de resultado en `probe_l1b/README.md`», que no existe todavía; y
  «entre la mitad y un octavo» no es la mediana de #869 (0,45 y 0,16 en el tramo de 50° o más).

---

## Qué le falta al documento para sellarlo sin preguntar, y qué decisión está escondida

1. **Escondidas como técnicas**: que VIIRS 375 oblicuo no decida (H2), el corte de 40° (H7), que CUMPLE baste con un
   estrato de cualquier ventana (H9), y los umbrales «mitad» y «5 %» del §8 b (H10).
2. **Faltan**: los sensores del evaluador (H4), qué ruido usa M en V2 y un nulo que pueda fallar (H3), el tratamiento de
   los volcanes con kernel (H1), la unidad de P2 (H8), SN y sin geometría en M (H14), y la salida si el probe no corre
   (H10).
3. **Ya está bien para sellar**: el §2, el §6 (con H18 resuelto), el §7.2, §7.3, §7.6 y §7.7, y la tabla d) del §8
   salvo el caso «M SIN SUSTRATO en todos los estratos que deciden», que no tiene fila.

---

## VERIFICADO LIMPIO

- **`sustrato_k.py` se reproduce idéntico.** Re-corrido con `TMP` y `TEMP` en `D:\vrp-trabajo\temporales`, `--tmp
  D:\vrp-trabajo\temporales\verif_s157`: 1 min 14 s, rc 0, y `diff` contra `sustrato_k_salida.txt` sin diferencias
  («IDENTICO»). Controles en la salida: `C1 ... 158 | esperado 158 | OK`, `CK ... 0 | OK`, C2 OK y C3 OK en las dos
  ventanas (V1: 407 contra 16; V2: 578 contra 119).
- **Tabla del §4 contra la salida, celda por celda**: protegidas que K publica 38 / 31 / 38 / 42; fracción detectable
  4,1 / 5,1 / 4,1 / 3,8 %; alertas bajo 1 MW 279/259, 38/21, 385/362, 75/49; negativos limpios 945/23, 1.497/14,
  871/36, 1.635/20; rescN 0 / 17 / 2 / 21; rescP 4 / 11 / 6 / 23; pares 166/131, 29/23, 211/189, 64/27; razones
  0,719/0,524, 0,659/0,353, 0,733/0,557, 0,540/0,511. Todo coincide. MODIS 14 y 16 protegidas (§8 c) también.
- **Cifras de #869** (`git show origin/s157-magnitud-chillan:experiments/_s157_magnitud_chillan/README.md`, §2.2):
  VIIRS 375 0,73 / 0,58 / 0,45, VIIRS 750 0,84 / 0,41 / 0,16, techo VIIRS 750 y MODIS 0,96 a 1,48, hallazgo lateral
  ×1,052 a 1,059. Coinciden (con la salvedad de H7 sobre «sobre 40°»). Los techos PL-0 del probe coinciden con G fondo
  0 sobre G de #869 en las pasadas que comprobé (06:48 VIIRS 375 0,47/0,36 = 1,31; VIIRS 750 0,96/0,30 = 3,2; 05:42
  0,92/0,67 = 1,37; 06:00 0,98/0,72 = 1,36; VIIRS 375 06:00 0,89/0,72 = 1,24).
- **Cifras de 1.14** (`experiments/_s151_presupuesto_magnitud/README.md:116`, `:124`, `:128`): ×1,28 [1,21; 1,35] en
  468 pasadas, ×1,18 a nadir y ×1,41 en el borde, Lastarria 0,91. Coinciden.
- **Líneas del §3**: `process_viirs.py:1492` y `process_viirs_mod.py:1047` son el `if` del flag en el bloque
  contextual; `:1958`, `:1989`, `:1278`, `:1302` son los recomputes del Test 1. Correctas en `b84a5c394` y sin cambio en
  `origin/main`. El corona S126 que podría pisar el VRP de D25 en el cúmulo está apagado en los cuatro brazos
  (`ENABLE_LOCAL_CLUSTER_MAGNITUDE_VIIRS375 False`, resuelto desde `pipeline.profile`).
- **Ningún flag de D25 llega a MODIS**: `grep -c "NEIGHBOR\|neighbor_mean" pipeline/process_modis.py` = 0.
- **Perfiles y prueba**: `python -m pytest -q tests/test_perfiles_d25_k_s157.py` → `3 passed`. Mutaciones sobre una
  copia en un temporal (`v2_salida.txt`): sacar el flag de VIIRS 750 de D, ventana 5x5 en D, D25 en el gemelo, MODIS en
  el control, `vent_anchored` apagado en `paths:` de D, `SENSOR_MODIS` fuera de `FLAGS_BRAZO` y producción de vuelta al
  Test 1: las siete hacen fallar la prueba **por aserción** («1 failed», 3 líneas de aserción). La misma clave escrita en
  la raíz del YAML (donde `pipeline.profile` no la lee) no cambia ninguna constante y la prueba pasa, que es lo correcto
  (A89). Ninguna constante del perfil se consume fuera de `pipeline/profile.py` por `_cfg` (`grep "profile\._\|_cfg\["`
  fuera de ese archivo: 0).
- **Workflow**: el único cambio contra `origin/main` es agregar los dos flags de D25, `VRP_BG_NEIGHBOR_MAX_HALF_PX` y
  `SENSOR_MODIS` a la línea `FLAGS_BRAZO`; `runs-on: ubuntu-24.04`, `"on":` entre comillas, autenticación sólo por
  token, paso que exige `DATA_SUBDIR == PROFILE_NAME`. Costo: 51 días × 2,20 = 112 min y ×1,42 = 159; 37 y 36 días ≈ 80
  min; peor job bajo el tope de 300 con el margen de A15.
- **Referencia congelada de V1**: sha256 en LF de los cuatro archivos igual a `MANIFIESTO.json` (5ae612a6...,
  904b331a..., bfd42726..., 8e4f9492...).
- **A119 y A104**: V1 empieza el 2026-08-29, después de la frontera de #535; V2 decide con la tabla sola y VIIRS desde
  el 2026-04-01; los hitos que el cargador imprime para V1 son sólo los del 2026-10-09 y 2026-10-10, ya tratados en el
  §4.
- **Probe, reproducción del primer pase**: en 20 escenas sintéticas con focos, el diagnóstico de vecinos del probe da
  T2, T3 y BT en verdadero exactamente en los vecinos que el `first_pass_tests_2_and_3` real marcó, y alguno en falso en
  los demás: **384 vecinos, 0 discrepancias** (`v4_salida.txt`), con conectiva `max` y umbrales duales.
  `prueba_probe.py` y `prueba_probe.py --modis` dan «prueba del instrumento: OK», rc 0.
- **Probe, controles**: C-P1 puede fallar (compara contra el record persistido con tolerancia de 1 % y 0,01 km); C-N
  puede fallar (encender el flag con el fondo de hoy tiene que dejar idénticos cúmulo, núcleo, píxeles y `vrp_mw`); C-A
  puede fallar (el envoltorio cuenta llamadas y el control debe dar 0); C-K puede fallar (recalcula el píxel de más
  energía con k·A y el anillo). Los argumentos de `calculate_vrp` y `append_record` del probe son los de
  `scripts/run_pipeline.py:234` a `:254`, `:277` a `:299` y `:324` a `:344`; MODIS sin geolocación es válido
  (`process_modis.py:470`, «geo_path is accepted ... but not used»).
- **Probe, brazo MODIS `d25_rad`**: es un análogo honesto de D25. `compute_local_background` se llama con todos los
  alertados (`process_modis.py:1000` y `:1055`), así que la máscara que arma el envoltorio es `hot_mask_2d` entera, como
  en VIIRS; promedia radiancia de vecinos no alertados con ventana hasta 7x7, el respaldo sin vecinos es el anillo (igual
  que D25), y vuelve a radiancia a la longitud de onda de la banda 21 que usa `process_modis` (`:1036`, `:1040`, `:1060`),
  con la misma inconsistencia de banda que #869 anotó. Su nulo devuelve NaN y cae al anillo, idéntico al control.
  Salvedad: a 1 km la ventana de 7x7 abarca 3 km a cada lado, el triple que en VIIRS 375.
