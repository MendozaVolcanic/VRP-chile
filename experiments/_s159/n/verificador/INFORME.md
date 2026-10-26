# Verificador con contexto limpio del frente N (S159)

2026-10-21. Worktree `C:\vrp-trabajo\s159-n`, rama `s159-n`, commit `3faa5a4f6` (pre-registro `0b20eb1f3`). Sin git, sin
workflows, sin API de GitHub. Leí el pre-registro, pensé cómo romper cada afirmación y recién después leí el INFORME.
Scripts y salidas en esta carpeta (`v1` a `v6`). Insumos: resultados crudos `..\run_39682867040\*resultados_*.json`
(md5 idéntico a los artefactos de `D:\vrp-trabajo\temporales\s159_n\`, comprobado), `objetivos_n.json`,
`poblacion_completa.json`. Ventana de todo número: pasadas VIIRS 750 nocturnas del 2026-04-01 al 2026-10-21 sin el 18 y
el 19 de octubre.

**Recalculé la publicación de los cinco brazos desde los records crudos, con el predicado del tablero ejecutado con
node** (`v1_recalcular.py`): coincide con la tabla del agente en 391 × 5 de 391 × 5. Control positivo de la
comparación: el record de F difiere del de K en 238 pasadas, así que el instrumento sí ve diferencias.

## Qué estaba pre-registrado

Pre-registrados antes del disparo (y sin cambios en `objetivos_n.json` ni en la geometría del probe después de
`0b20eb1f3`, comprobado con `git diff`): los brazos K, K2, C, F y FC, la regla de veredicto, el estimador ponderado y el
bootstrap; el oráculo en la grilla de GEO con interpolador lineal como versión principal, y las variantes. Lo que cambió
después del pre-registro en `probe_n.py` es sólo la bajada (reintentos y búsqueda por ventana). **No pre-registrado:** el
oráculo contado como brazo (afirmación 3, declarado post hoc por el agente).

## Veredicto por afirmación

### 1. «F y FC encienden de más: 206 de 5.385 negativos (3,8 %), ΔE +104, IC 14,5 a 212». PARCIAL: el mecanismo y las alertas ganadas se confirman; el número de negativos y el ΔE se REFUTAN

- **Lo que se confirma** (`v2_estimador_F_salida.txt`, `v3`): los 6 negativos que F enciende son cúmulos de 1 píxel de
  cumbre que K deja en 0,0 MW, con 0 píxeles del primer pase, oráculo con 0 píxeles (n_abs 0) también con el anillo
  sensible, MIROVA RUTINA 0,0, magnitud de F de 0,23 a 0,45 MW y banda entera positiva. Alertas bajo 1 MW ganadas: 48
  (censo), sin publicar de 65 a 17 de 175. Protegidas perdidas: 0 de **78 medidas**; la protegida que decide número 79
  (Chillán 2026-10-12 05:18, 3,46 MW en producción) es SIN DATO (`v6`).
- **Lo que cae.** F no toca la detección: mismo `n_hot` y mismo número de píxeles del cúmulo que K en 391 de 391
  (`v3`). Entonces F sólo puede encender un negativo donde K ya tiene cúmulo que no publica, y eso se puede contar en la
  **población entera**, sin muestreo: de 5.476 negativos limpios, 5.303 no tienen ni un píxel alertado, **60 tienen un
  cúmulo de cumbre en 0,0 MW** y 59 tienen un cúmulo `far` (`v3`, `v5`). El techo físico de lo que F puede encender es
  119, y el estimador del agente da **152,3**: excede el máximo posible. El techo de negativos publicados por F es
  54 + 119 = 173 (3,2 %), no 206 (3,8 %), y el techo de ΔE es 119 − 48 = **+71**, no +104. El IC hasta 212 cae casi
  entero en una zona imposible.
- **Por qué pasó.** Sorteo con suerte, no un defecto del código: la muestra sacó 6 elegibles de 140 (4,3 %) cuando en la
  población son 60 de 5.476 (1,1 %). En Isluga con cenit hasta 40°, 3 de 6 sorteados eran elegibles (peso 20,8 cada uno,
  62,5 estimados) cuando el estrato entero tiene 20; en Planchón-Peteroa, 2 de 6 (61,7 estimados) contra 6 reales. El
  bootstrap estratificado no sabe que el estrato tiene un techo.
- **Estimación corregida.** Entre los elegibles muestreados F enciende 6 de 6 (Clopper-Pearson 95 %: 0,54 a 1); en toda
  la muestra F publica los 55 de 55 cúmulos que K dejaba en 0,0 MW (48 alertas, 6 negativos, 1 de R2). Si F publica todo
  cúmulo de cumbre en 0,0 MW, como sugiere el 55 de 55: ganaría 49 alertas (48 medidas más la SIN DATO de Isluga
  2026-10-12, que también está en 0,0 de cumbre) y encendería 60 negativos, **ΔE ≈ +11**; con la cota baja de la tasa
  (32 encendidos), ΔE ≈ −16. Los 59 `far` no tienen ningún representante en la muestra: lo que F haga con ellos es SIN
  DATO (podría cambiar el píxel de mayor VRP y con eso la clase de distancia), y sumaría de 0 a +59.
- **Veredicto pre-registrado con el número corregido:** el signo probablemente sigue positivo, pero el efecto es del
  orden de **una decena, no de cien**, y con este lote **no está resuelto**. La lectura física del agente (el fondo del
  código destapa una divergencia de detección que el recorte a cero tapaba) se sostiene; la de «del orden de 150 puntos
  de cumbre más en seis meses» (N-1, dashboard) no: son a lo más 60, más lo que salga de los 59 `far`.
- **Cómo cerrarlo barato:** correr F sobre los **60 elegibles y los 59 `far`** (119 pasadas, censo, sin pesos) y sobre la
  alerta de Isluga 10-12. Con eso ΔE queda contado, no estimado.
- CONFIANZA: CONFIRMADO (medido). GRAVEDAD 4: cambia el tamaño del argumento contra adoptar el fondo solo.

### 2. «El oráculo en la grilla de GEO reproduce la magnitud: 0,999 [0,978; 1,007] en 145». CONFIRMADA, con dos precisiones

- **Las 145 no son las mismas en cada variante** (145, 133, 136, 113, 129). Sobre la **intersección de las cinco
  variantes (107 alertas)** el resultado se sostiene igual (`v4_oraculo_y_resto_salida.txt`): GEO lineal 1,000
  [0,985; 1,008], 94 de 107 entre 0,8 y 1,25; R2 lineal 1,000 [0,868; 1,108], 80; vecino 1,227; cúbico 1,210. Control
  positivo: las variantes dan razones distintas sobre las mismas pasadas.
- **Sobreajuste: no.** La esquina de GEO sale de los encabezados de los TIF (`experiments/_s159/geo/INFORME.md` H1), no de
  ajustar magnitudes; la grilla y el interpolador lineal estaban fijos en `objetivos_n.json` y en `probe_n.py` del
  commit de pre-registro, y no cambiaron. El `.m` recibe la grilla ya hecha (sólo `fillmissing2(..., 'linear')` en la
  l. 81 es suyo), así que «remuestreo lineal» es un supuesto, pero declarado antes y que podía fallar: falló para vecino
  y cúbico.
- Precisiones: (a) la cifra es **condicional a que el oráculo detecte** (145 de 181; las 36 que no, 28 de Cordón Caulle
  y 8 de Tupungatito, son el tema de la afirmación 3); (b) 4 de las 145 cifras de MIROVA vienen del OCR, 141 de la tabla.
  Los corchetes son cuartiles, no intervalo de confianza.

### 3. «El oráculo como brazo gana en las dos caras (post hoc): 0 protegidas perdidas, 59 ganadas, negativos 54 a 8, ΔE −105; con la caja por defecto pierde 6 protegidas de Cordón Caulle a 7,8 a 10,5 km». PARCIAL

- La aritmética se reproduce (`v4`): anillo sensible 0 protegidas perdidas de 78, 59 alertas ganadas, 6 sin publicar,
  8 negativos (los 8 en `neg_pub`), ΔE −105,0; caja por defecto 6 protegidas perdidas, ΔE −72,6.
- **Cae la distancia:** una de las 6 (Cordón Caulle 2026-07-03 05:48, MIROVA 1,0 MW) está a **4,59 km** según MIROVA; el
  rango es 4,6 a 10,5 km, como dice el propio INFORME en N-3, no 7,8 a 10,5.
- **«Gana» no está resuelto:** el oráculo publicó 0 de 140 negativos muestreados, pero, a diferencia de F, cambia la
  detección, así que no hay techo por censo. La cota superior de Clopper-Pearson para 0 de 140 es 2,6 %, unos 139 de
  5.331 (`v6`): ΔE podría llegar a +34. No se calculó intervalo.
- **Predicados distintos:** el oráculo «publica» con un supuesto del agente (píxel de mayor M13 a no más de
  `inner_radius_km`), sin `store` ni el predicado del tablero; K y los brazos usan el del tablero. La comparación mezcla
  dos reglas. Además, la variante que gana no es el código de MIROVA, que trae la caja por defecto.

### 4. «La compuerta de 3 K no cambia ninguna publicación (0 de 391); el cero de los 55 lo pone el fondo». CONFIRMADA

`v4`: C publica distinto de K en 0 de 391; los 55 cúmulos en 0,0 MW son los **mismos ids** en K y en C; C agrega un
píxel al cúmulo en 8 pasadas y cambia la magnitud sólo en Villarrica 2026-04-11 06:42 (0,208 a 0,226). F deja los 55 en
positivo (`v3`). Alcance: es de la muestra; C cambia la detección y 0 de 140 negativos no excluye efecto en la
población (misma cota de 2,6 %).

### 5. «El tope D9 recorta con F a la protegida de Chillán 2026-10-01 05:24». CONFIRMADA

`v4`: MIROVA 9,0 MW, oráculo 7 px 9,157, K 2,655 sin tope, F 6,214 a 5,0 con `d9_capped` (banda 6,2137 a 6,2137); es el
único `d9_capped` del lote en K, F y FC. Sigue publicada (no se pierde), es magnitud. Ojo: la cifra de MIROVA es **sólo
OCR** (`ALERTA_TERMICA_OCR`, después del 13 de junio, decide).

### 6. «Controles: K2 = K, K = producción 391 de 391, 7 SIN DATO». CONFIRMADA

`v1`: K2 idéntico a K en 391 (nulo débil: mismo proceso determinista, no vería un envoltorio roto); K publica igual que
producción en 391 de 391 y `pc.vrp_mw` a 0,001 en 391 (éste es el control fuerte). Los 7 SIN DATO se confirman en las
bitácoras: los tres del 2026-10-12 fallan tres veces por nombre y después por ventana en el redisparo (que CMR no los
devuelva es lo que muestra la bitácora; no lo verifiqué contra CMR para no gastar la API); los dos de Chaitén tienen el
píxel más cercano a 10,4 y 23,5 km; las dos diurnas, sin gránulo por ventana. Dentro de los 7 hay **una protegida que
decide** (Chillán 10-12 05:18) y una alerta en 0,0 de cumbre (Isluga 10-12 05:48): el «0 protegidas perdidas» es sobre
78 de 79.

## VERIFICADO LIMPIO

- Resultados del repo = artefactos bajados (md5 de los 9 JSON).
- Publicación por brazo recalculada con node desde los records crudos = tabla del agente (`v1`, 0 diferencias en 1.955).
- Protegida recalculada con `clase_mirova.alerta_protegida` sobre las filas de MIROVA de cada pasada: 0 diferencias.
- F y FC publican igual en 391 (`v1`); F no cambia la detección ni la clase de distancia en ninguna pasada (`v3`, `v5`).
- Grilla e interpolador del oráculo fijados en el commit de pre-registro (`git diff 0b20eb1f3 3faa5a4f6`).
- El proxy de `np` en F sólo puede interceptar las tres llamadas `np.maximum(..., 0.0)` del módulo
  (`pipeline/process_viirs_mod.py:1056`, `:1286`, `:1312`); las dos últimas son del Test 1 integrado, apagado en
  producción.
