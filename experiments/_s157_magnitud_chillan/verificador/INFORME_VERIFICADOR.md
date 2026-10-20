# Verificador con contexto limpio: tarea 1.33 (a), magnitud de Chillán con K

Estudio verificado: `D:\vrp-trabajo\worktrees\s157-magnitud-chillan\experiments\_s157_magnitud_chillan\`
(commit 9ea507585). Fecha: 2026-10-20. Sólo lectura: no se editó nada bajo `worktrees\` ni en OneDrive, no
hubo commits, ramas, workflows ni Earthdata.

Scripts y salidas del verificador (todo en `D:\vrp-trabajo\temporales\s157_magnitud\verificador\`):
`v1_comprobar.py` / `v1_salida.txt`, `v2_laminas.py` / `v2_salida.txt`, `v3_extra.py` / `v3_salida.txt`,
`v4_control_pixel.py` / `v4_salida.txt`, `rerun_a.log`, `rerun_b.log`, `diff_reejecucion.patch`.

## Veredicto global: PARCIAL

Los números del README salen de las salidas y se reproducen (re-corrida idéntica salvo el commit del
consolidado). La aritmética es correcta y los controles de píxel y de predicado están vivos. Lo que no se
sostiene entero es la **atribución**: la frase de cabecera («el déficit que crece con el ángulo es
geométrico») y la recomendación «D17 primero» descansan en un argumento por eliminación que no descarta la
selección, en una estratificación por cenital que no puede separar el área de cualquier otro efecto
colineal con el ángulo, y en un indicio (las miniaturas) que no discrimina. Además el propio dato muestra que
el área sobre-corrige respecto del nadir, el mismo patrón que S133.

| # | afirmación | veredicto |
|---|---|---|
| 1 | tabla por pasada reproduce lo publicado y el VRP de MIROVA | CONFIRMADO (con 2 matices menores) |
| 2 | VRP por píxel con la fórmula del procesador; MODIS vuelve a radiancia con λ de B21 | CONFIRMADO |
| 3 | en VIIRS 375 el fondo no puede cerrar el déficit oblicuo (techo con fondo cero) | CONFIRMADO como cota para D25 tal como está implementado; NO dice nada de la selección |
| 4 | el área «aplana la curva» | PARCIAL: reduce la caída, pero sobre-corrige respecto del nadir y no se distingue de otros efectos del ángulo |
| 5 | sensibilidad al fondo en 750 crece con el ángulo por dilución | PARCIAL: la sensibilidad es función del exceso ΔT (mecánico); que ΔT caiga por dilución de área no está aislado |
| 6 | testigo de saturación (corr 0,79) | PARCIAL: la correlación está inflada por la dependencia común con el cenital y por leer las mismas radiancias; la conclusión se apoya mejor en 5 pasadas puntuales |
| 7 | indicio de las miniaturas | Mapeo CONFIRMADO; la lectura como firma del remuestreo del VRP, REFUTADA como discriminante |
| 8 | recomendación D17 antes que D25 | PARCIAL: «D25 no cierra Chillán oblicuo» se sostiene; «D17 es la única palanca con la dependencia angular correcta» y el brazo elegido no se siguen de lo medido |

## Hallazgos, ordenados por gravedad

### H1. La recomendación descansa en una eliminación que no excluye la selección (gravedad 4, confianza alta)
- **Dónde**: `README.md` §0 («el fondo no es lo que falta: el déficit ... es geométrico»), §3 primer punto,
  §5.2; `a_pasadas.py:19-28` (G = selección + fondo + área).
- **Qué pasa**: G mezcla selección, fondo y área. El techo con fondo cero acota sólo el fondo **sobre
  nuestros píxeles**. Que el fondo no alcance no implica que lo que falta sea área: también puede ser que
  MIROVA sume más píxeles (vecinos tibios, A99 y A103) en las pasadas oblicuas. El README lo reconoce en §2
  y §6 («sin el Npix de MIROVA no se reparte») pero la cabecera y §5 concluyen «geométrico».
- **Cómo se ve**: nuestro conteo no crece con el ángulo (n_dentro mediana 2,5 a nadir y 2,5 oblicuo en
  VIIRS 375; `v1_salida.txt` sección 4 y 8), y el de MIROVA es desconocido en 2026. La tarea 1.14 midió
  en el OSF de 2025 Npix 3, 5, 5, 4 por banda (`experiments\_s151_presupuesto_magnitud\README.md` §3.2):
  ni constante ni proporcional al área.
- **Reproducir**: `python -I v1_comprobar.py` (secciones 4 y 8).

### H2. El área sobre-corrige respecto del nadir: «aplana la curva» es demasiado fuerte (gravedad 3, confianza media)
- **Dónde**: `README.md` §3 («Con el área real, G queda en 0,80 / 0,94 / 0,95: la curva se aplana»).
- **Qué pasa**: el mismo párrafo dice que lo que sobra a nadir (0,73 a 0,80) «es otra cosa ... y es
  parejo». Si fuera parejo y el área fuera el mecanismo, G_area debería quedar en ~0,80 en las tres
  bandas. Queda en 0,80 / 0,94 / 0,95: la caída de 38 % se reemplaza por una subida de ~19 %, que es la
  firma de sobre-corrección que S133 midió con n = 111 y 210 (0,958 nadir, 1,360 borde;
  `docs\s133\AB_AREA_VEREDICTO_CHUNK1.md`). En Chillán cae cerca de 1 por coincidencia con un déficit
  independiente a nadir.
- **Cómo se ve** (`v1_salida.txt` sección 7): VIIRS 375 G_area mediana <30° 0,80 [0,68; 0,91], 30 a 50°
  0,94 [0,84; 1,02], ≥50° 0,95 [0,78; 1,21], cuartiles ≥50° 0,76 a 1,36, 9 de 19 con G_area ≥ 1. Con el
  corte de D17 (S141, cenit ≤ 40 contra > 40; `v3_salida.txt` (c)): VIIRS 375 G_area 0,85 contra 0,95
  (sobre-corrige), VIIRS 750 0,97 contra 0,66 (sub-corrige). Los intervalos se solapan: con estos n no es
  significativo, pero tampoco «aplana».
- **Reproducir**: `python -I v1_comprobar.py` sección 7; `python -I v3_extra.py` sección (c).

### H3. La estratificación por cenital no separa área de cualquier efecto colineal con el ángulo (gravedad 3, confianza media)
- **Dónde**: `README.md` §2.2 y §3; `a_pasadas.py:145-146` (bandas <30, 30-50, ≥50).
- **Qué pasa**: log f_area y sec(cenital) tienen correlación 0,91 en estas pasadas. La única variación que
  separa área de ángulo es el diente de sierra de la agregación de VIIRS (f_modelo cae de ~2,0 a ~1,3 al
  pasar de 2:1 a 1:1 cerca de 52,6° de cenital), y el README no la usa: sus bandas mezclan las dos zonas.
- **Cómo se ve** (`v1_salida.txt` sección 5; diente de sierra con M ≥ 1 en `v5_diente_sierra_M1_salida.txt`):
  - VIIRS 375: pendiente log G ~ log f = -0,71 [-1,10; -0,32] (-0,95 con M ≥ 1); en regresión múltiple
    con sec(z), log f -0,51 y sec -0,16: el área gana, pero colineal.
  - VIIRS 750: pendiente -1,33; en múltiple, log f -0,10 y sec -0,98: **gana el ángulo, no el área**.
  - Diente de sierra, M ≥ 1: VIIRS 375 zona 2:1 (f mediana ~1,75) G 0,55 contra zona 1:1 baja
    (f 1,33 a 1,51, n = 3) G 0,60: el área predice ~0,7. VIIRS 750: 0,45 contra 0,38, **dirección
    contraria** a la del área. Con n = 3 y 4 no decide nada, pero es el único test que podía.
- **Reproducir**: `python -I v1_comprobar.py` secciones 5 y 6.

### H4. Las miniaturas de MIROVA no pueden discriminar si el VRP se suma sobre celdas remuestreadas (gravedad 3, confianza alta)
- **Dónde**: `b_mancha_mirova.py:4-9` («si suma píxeles nativos, no [crece]»), `README.md` §4 y §5.2.
- **Qué pasa**: la lámina es un mapa grillado (A24, A106: producto de visualización). Cualquier mapa
  dibujado en coordenadas de terreno agranda la mancha de un píxel oblicuo, **sume MIROVA el VRP sobre
  celdas o sobre píxeles nativos con área nominal**. La alternativa que el script dice descartar predice
  lo mismo que la hipótesis: el instrumento no puede fallar. Además el conteo de blancos sigue más a la
  potencia que al área.
- **Cómo se ve** (`v2_salida.txt`, al final): en las 5 pasadas de VIIRS 375 con MIROVA ≥ 9 MW,
  corr(log px, log M) 0,94 contra corr(log px, log f) 0,89, y corr(log M, log f) 0,91; en 750, 0,85
  contra 0,81. Una pendiente de 2,00 (más que el 1 que predice el remuestreo puro) es lo esperable si la
  intensidad también empuja. Y la pasada de 68° del 17-oct en 750 da 1 px blanco.
- **Mapeo a ojo**: verificado abriendo las cuatro láminas (md5 coincidentes con la salida). Los rótulos de
  cada miniatura coinciden con `PANELES` en las 4 láminas (incluidos los `None` de día, nubladas y la
  17:42 diurna de 5,64 MW). Las 8 pasadas repetidas son la misma imagen byte a byte (diferencia media 0,0
  en `v2_salida.txt`), así que el control 1 sólo prueba el mapeo, no el instrumento.
- **Reproducir**: `python -I v2_laminas.py`.

### H5. «D17 es la única palanca con la dependencia angular correcta» contradice una medición ya publicada (gravedad 3, confianza alta)
- **Dónde**: `README.md` §5.2.
- **Qué pasa**: la tarea 1.14 midió D25 por banda de ángulo: 1,18 [1,12; 1,24] a nadir a 1,41 [1,27;
  1,60] en el borde, y con efecto fijo por volcán 1,00 / 1,08 / 1,17 / 1,20
  (`experiments\_s151_presupuesto_magnitud\README.md` §3.4). D25 también tiene dependencia angular, y es
  la única palanca de las dos que ya está **medida** como brazo de reproceso (1,28 en `literal`). En
  Chillán mismo, el alza de los vecinos 10 K más fríos es ×1,09 / ×1,06 / ×1,28 en 375 y ×1,19 / ×1,35 /
  ×2,00 en 750 (`a_pasadas_salida.txt`, estratos).
- **Lo que sí se sostiene**: en VIIRS 375 oblicuo ningún fondo cierra con nuestros píxeles (25 de 32
  pasadas con G_fondo0 < 1; `v1_salida.txt` sección 8).

### H6. El brazo recomendado (remuestreo literal) choca con la evidencia que el README deja «abierta» (gravedad 3, confianza media)
- **Dónde**: `README.md` §5.3 y §4 último párrafo.
- **Qué pasa**: si MIROVA remuestreara el VRP a celdas, su Npix crecería con el área; 1.14 no lo vio
  (3, 5, 5, 4). El catálogo (`docs\MIROVA_DIVERGENCES.md`, D17, nota S141) cita que el grupo escribe que
  el remuestreo corrige el cenit sólo «partially» y que su VRP cae con el ángulo (Aveni 2023), y pide
  reportar la magnitud **restringida a cenit ≤ 40°** antes de atribuir el gap a un mecanismo; el estudio no
  lo hace para sí mismo (lo dejo hecho en `v3_salida.txt` (c)). El §1 del README afirma además que el
  remuestreo «conserva la energía»: eso es inferencia, no cita (SOSPECHA: no revisé los PDF). Una hipótesis
  que reconcilia Npix constante con magnitud plana sería «área por píxel sin remuestreo», que es justo el
  brazo que S133 probó y se pasó (1,36). Ninguno de los dos brazos está respaldado; el pre-registro debería
  llevar ambos o ninguno como «el» brazo.

### H7. El testigo de saturación mide sobre todo la dependencia común con el cenital y que ambos leemos las mismas radiancias (gravedad 2, confianza alta)
- **Dónde**: `a_pasadas.py:245-284`, `README.md` §3 último punto.
- **Qué pasa**: las dos razones log(750/375) caen con el cenital (corr -0,72 nuestra, -0,65 MIROVA): sólo
  por eso se esperaría una correlación ~0,47. Controlando el cenital, la parcial es 0,60 (nulo barajado
  p99 0,43): hay algo común más allá del ángulo, pero es lo esperable de dos sistemas que leen el mismo
  gránulo. La pendiente es 0,52 (sd 0,74 contra 0,49): nuestra razón oscila 1,5 veces más que la de
  MIROVA, y log(G750/G375) correlaciona -0,47 con el cenital, o sea que el testigo **sí** separa a MIROVA
  de nosotros, pero por el ángulo (fondo y recorte en 750), no por saturación. Lo que sí apoya «la falta
  es común» son las 5 pasadas cercanas al nadir con razón alta: 3,09/2,93, 2,18/1,81, 2,16/2,05,
  1,89/1,91, 1,88/1,74. Ningún píxel 375 está a 5 K del techo de I4 (`cerca_del_techo` 0 de 44), lo
  que es lo esperado si el saturado se descarta: ese flag no puede ver la saturación.
- **Reproducir**: `python -I v1_comprobar.py` sección 9.

### H8. «Lo último es consecuencia de lo primero» apunta al recorte, no al área (gravedad 2, confianza alta)
- **Dónde**: `README.md` §3, punto VIIRS 750.
- **Qué pasa**: en la lista, «lo primero» es el recorte del tablero; el argumento que sigue es la dilución
  de área. Además el mecanismo está a medio aislar: el alza por fondo es función casi pura del exceso
  ΔT (corr log alza contra log ΔT -0,95; con ΔT en el modelo el cenital no aporta: 0,0028), y ΔT cae con
  el cenital en 750 (-0,51) pero **no en 375** (-0,18), aunque el área crece igual en los dos. Que ΔT de
  750 caiga por dilución geométrica y no por otro efecto del ángulo (camino atmosférico, oclusión del
  cráter, Aveni 2024 §7.3 según el catálogo) no está medido.
- **Reproducir**: `python -I v1_comprobar.py` sección 11.

### H9. «El fondo no es lo que falta» generaliza a VIIRS 750 y MODIS, donde el techo con fondo cero sí pasa de 1 (gravedad 2, confianza alta)
- **Dónde**: `README.md` §0.
- **Cómo se ve**: G_fondo0 mediana 1,22 / 0,96 / 1,18 en VIIRS 750 y 1,48 / 1,27 / 1,12 en MODIS
  (`a_pasadas_salida.txt`, estratos). La frase vale para VIIRS 375; el propio §3 lo matiza, la cabecera no.

### H10. El universo excluye 12 alertas de MIROVA «sin geometría» que sirven para magnitud (gravedad 2, confianza alta)
- **Dónde**: `a_pasadas.py:179` (sólo `lab == "pos"`), etiqueta `sin_geometria` de `scripts\banco_paridad.py`.
- **Qué pasa**: para la detección se excluyen con razón (no se sabe la distancia), pero el VRP es de la
  propia pasada y para la magnitud son tan válidas como las otras. Dos son casi a nadir (17-oct 06:00,
  10,5°: G 0,88 en 375 y 0,84 en 750) y una es un contraejemplo fuerte del área: 10-oct 06:30, 50,5°,
  f 2,23, G 0,97 (375) y 0,81 (750), o sea G_area 2,16 y 1,81 (`v3_salida.txt` (b), `v4_salida.txt`).
- **Reproducir**: `python -I v3_extra.py`, `python -I v4_control_pixel.py`.

### H11. Menores (gravedad 1)
- 10 pasadas usan el VRP del OCR; 3 de VIIRS 750 traen enteros (9, 10, 7 MW): error hasta ±7 %.
- 2026-09-28 05:18 VIIRS 375 con M = 0,05 MW entra como positiva (G 1,43); bajo la regla SN de D-9 es
  «MIROVA no vio nada». `indexar_referencia` se llama con la regla `original` por defecto.
- El control de píxel acepta hasta 12,9 % de error relativo en los 92 píxeles donde manda la tolerancia
  absoluta de 0,002 MW (`v4_salida.txt`); no cambia ninguna conclusión.
- `f_lambda_modis` (`a_pasadas.py:95`) mezcla la λ de B21 en el píxel con la de B22 en el fondo cuando el
  píxel pasa de 331 K; en estas 11 pasadas ningún píxel MODIS pasa de 300 K, así que no actúa (mi
  cálculo limpio da los mismos 1,052 a 1,059).
- 1 de 87 records tiene `n_anomalous_pixels` 2 y un solo píxel guardado (2026-09-28 06:18 VIIRS 375).
- `a_pasadas.py` no corre `control_identidad_predicado`; lo compensa que D coincide con `f5_core_vrp_mw`
  (44 de 44 en 375) y con `primary_cluster.vrp_mw` (43 de 43 en 750 y MODIS).

## Hallazgos propios que no estaban en la lista

- **H10** (alertas sin geometría excluidas, con un contraejemplo de área a 50,5°).
- **En la pasada estrella (06:48) quien se mueve es MIROVA, no nosotros**: nuestro S_in de 375 sube de 7,20
  (06:00) a 9,37 (06:48) mientras MIROVA sube de 9,94 a 25,79 (×2,6); en 750 MIROVA sube ×1,2 y nosotros
  bajamos a la mitad (`a_pasadas_salida.txt`). Bajo la hipótesis del área, la potencia física habría
  subido ×3,9 según nuestro 375 y ×1,5 según nuestro 750: las dos lecturas no son coherentes entre sí. Con
  todo el conjunto, log M no correlaciona con el cenital (0,05 en 375) y para M ≥ 5 sube con él (0,43),
  mientras S_in baja (-0,22) (`v3_salida.txt` (a)). Una pasada no basta para anclar un pre-registro.
- **El diente de sierra de f_modelo es la herramienta que falta** (H3): cualquier A/B de D17 debería
  pre-registrar el contraste 2:1 contra 1:1 a cenital parecido, porque es lo único que separa área de
  ángulo sin L1B.

## VERIFICADO LIMPIO

- Re-corrida de `a_pasadas.py` con referencia nueva: **mismas 95 / 95 / 87 pasadas, mismas 8 no
  publicadas, 223 de 223, misma tabla y correlación 0,788**. El único cambio es `commit_cons`
  (25114fe7 a 81941e2c) y la hora de generación (`diff_reejecucion.patch`). `b_mancha_mirova.py`
  re-corrido: sin diferencias. Salidas restauradas con `git checkout`.
- Todos los números de §1, §2.1, §2.2, §3 (25 de 32; 25 de 87, 1,00 a 1,73, 2 sin definir; 3,09 y 2,93)
  y §4 (2,00, 0,85, -0,72, 8 duplicados) salen de las salidas (`v1_salida.txt` secciones 1 a 3 y 9).
- El píxel de 268,9 K bajo el anillo de 272,0 K en la 06:48 de 750, y los 6 alertados que suman 6,84 MW
  con un cúmulo de un píxel de 2,84 MW (`v1_salida.txt` sección 2).
- Afirmación lateral de MODIS: `pipeline\process_modis.py:1036` y `:1040` usan `BAND21_LAMBDA`;
  `merge_mir_bands` (l. 323-339) da B22 primaria; `pipeline.profile.ENABLE_MODIS_B22_PRIMARY = True`
  (leído del módulo, no del YAML). El control discrimina: con λ de B22 sólo 3 de 23 píxeles MODIS pasan, con
  B21 23 de 23; con k·A de 375 en 750, 0 pasan (`v4_salida.txt`). Factor 1,052 a 1,059 reproducido.
- Flags leídos de `pipeline.profile`: `ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS375/750 = False` (D25 sólo toca el
  fondo, no la selección, así que el techo con fondo cero es una cota honesta **para ese flag**),
  `ENABLE_UTM_REGRID = False`, `ENABLE_GEOLOCATED_PIXEL_AREA = False`, nadir fijo True. El regrid F70 existe
  (`pipeline\regrid.py`, vecino más cercano).
- Todos nuestros alertados están dentro del inner (S_todos / S_in = 1,00 en todos los estratos).
- `f_modelo` se aplica al cenital del record (el mismo en 375 y 750 de una pasada) y convierte a ángulo de
  barrido; está bien usado. El de MODIS es un modelo propio declarado como tal, sin descontar el bow-tie.
- Pareo ±2 min y prioridad CONS sobre OCR: 77 CONS, 10 OCR; los VRP de la 06:48 coinciden con el CSV.

## Las dos preguntas, por instrumento

| instrumento | si lo medido estuviera roto, ¿falla? | si el instrumento estuviera muerto, ¿se vería distinto? |
|---|---|---|
| control de píxel | sí (λ de B22: 20 de 23 fallan; área de 375: todos) | sí |
| D por node | sí (coincide 87 de 87 con f5 o pc) | sí |
| techo fondo cero | es aritmética; vale sólo para nuestros píxeles | no aplica |
| G·f_area por estratos | no: un efecto colineal con el ángulo daría lo mismo (corr 0,91) | parcialmente |
| testigo 0,79 | no del todo: el cenital común solo ya daría ~0,47 | parcialmente |
| mancha en miniaturas | no: un mapa de píxeles nativos también agranda la mancha | no |
