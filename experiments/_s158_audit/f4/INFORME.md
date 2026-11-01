# F4 (S158): qué se traslada del código de VIIRS 750 a MODIS y VIIRS 375, y con qué evidencia

> Auditoría S158, frente F4. 2026-10-21. Worktree `D:\vrp-trabajo\temporales\s158_d17`, rama `s158-d17-diseno`.
> Sólo lectura fuera de esta carpeta. Scripts y salidas crudas en `experiments/_s158_audit/f4/`.
> Vara: para VIIRS 750 manda el código (`experiments/_s158_d17_diseno/osf_codigo_mirova/*.m`, leído entero); para
> MODIS y VIIRS 375 manda el paper, leído renderizando la página a imagen (A95; las páginas están en `paginas/`).
> Toda afirmación trasladada desde VIIRS 750 se marca TRASLADADA, no CONFIRMADA.

## 0. En una pantalla

1. **Lo que decide la publicación fuera de la cumbre es el mínimo fijo de dNTI, y para VIIRS 375 no existe ningún
   dato sobre él.** Medido sobre 5.226 pasadas nocturnas de VIIRS 375 (marzo a octubre de 2026): en el 92,8 % la
   rama estadística `μ + 10σ` queda por debajo de 0,02, así que el umbral de escena lo fija el mínimo. En VIIRS 750
   pasa en el 75,4 % y en MODIS en el 51,6 %. El número que más pesa es el que menos evidencia tiene (hallazgo 1).
2. **K1 casi no decide nada en Chile**: ningún negativo limpio de ningún sensor tiene `nti_max` sobre -0,86
   (n = 5.168 MODIS, 3.834 VIIRS 375, 5.994 VIIRS 750), y entre los positivos de VIIRS 375 sólo 25 de 1.392 (1,8 %)
   superan -0,7 y 44 (3,2 %) superan -0,8. La cota inferior que se puede inferir de la referencia es K1 ≥ -0,87, que no
   distingue -0,8 de -0,7. Trasladar K1 mal cuesta poco; trasladar el mínimo de escena mal cuesta mucho (hallazgo 2).
3. **El mínimo de cumbre 0,003 es inerte en los tres sensores** (`μ + 5σ < 0,003` en 0,0 a 0,8 % de las pasadas): lo que
   decide en la cumbre es el 5σ y el tamaño de la caja, no el mínimo (hallazgo 3).
4. **El OSF v2.5 no sirve para inferir ningún umbral de detección en ningún sensor**: sus pisos por sensor coinciden al
   watt con los filtros de la Tabla 1 de Coppola 2026 (VIIRS 375 noche 10.004 W contra 1,0 × 10⁴; VIIRS 750 noche
   5.000.049 W contra 5,0 × 10⁶; MODIS 100.013 W contra 1,0 × 10⁵). En VIIRS 750 el filtro de 5 MW deja Npix = 1 en el
   0,2 % de las filas (hallazgo 5).
5. **Incluso en VIIRS 750 el código no es toda la cadena de producción**: 8.239 de 100.641 filas de VIIRS 750 del OSF
   (8,2 %) tienen un VRP que no es `1,97 × 10⁷ × 0,5625 × ΔL` (la razón al valor de la fórmula tiene mediana 0,51).
   En VIIRS 375 y MODIS la identidad se cumple en el 100 %. Fuera de mi alcance (F6), pero cambia qué significa
   «el código manda» (hallazgo 4).
6. **La frase «la estructura se traslada con apoyo citable» (`docs/S158_CODIGO_MIROVA_VS_VRP_CHILE.md` §5) tiene la
   misma clase de evidencia que tenía el traslado de los números que resultó falso**: las dos citas (Campus 2022 p. 7
   y Coppola 2026 p. 5) dicen «mismo algoritmo» y no distinguen estructura de números, y para tres elementos
   estructurales el paper de los otros sensores dice otra cosa que el código de VIIRS 750 (hallazgo 6).
7. **El K1 diurno del código es -0,5; nuestra rama diurna (apagada) trae -0,6 de la Tabla 1 de MODIS.** El informe
   S158 compara sólo la noche y no lo registra. Latente hasta que `enable_daytime_viirs` pase a `true` (hallazgo 7).

## 1. Tabla maestra: evidencia por elemento y por sensor

Claves: **CÓDIGO** = `MIROVA_VIIRS750_*.m` (línea); **PAPER** = página renderizada; **TEXTO** = capa de texto o `.txt`
extraído (no renderizado, vale menos); **TRASLADADA** = sólo se sabe en VIIRS 750 y se supone en el otro sensor;
**SIN DATO** = ningún paper, código ni dato lo fija; **CONTRADICE** = el paper de ese sensor dice otra cosa que el
código de VIIRS 750. La columna «sustrato» es lo que medí en Chile (§3): cuánto decide ese elemento.

| elemento | MODIS | VIIRS 750 | VIIRS 375 | sustrato medido en Chile |
|---|---|---|---|---|
| **K1 noche** | -0,8 PAPER (Coppola 2016a Tabla 1, p. 7; Coppola 2025 cap. 11 Tabla 2, p. impresa 336, sólo MODIS y atribuido a Wright 2002) | -0,7 CÓDIGO (H:178) | SIN DATO | ningún negativo sobre -0,86 en ningún sensor; positivos sobre -0,7: 1,5 a 1,8 %; sobre -0,8: 1,0 a 3,4 % |
| **K1 día** | -0,6 PAPER (Tabla 1) | -0,5 CÓDIGO (H:189) | SIN DATO | no corre (`ENABLE_DAYTIME_VIIRS = False`) |
| **mínimo dNTI cumbre** (0,003) | PAPER (Tabla 1, C1 ROI1) | CÓDIGO (H:184, ROI2 = caja de 7 × 7) | SIN DATO | inerte: `μ+5σ < 0,003` en 0,8 / 0,2 / 0,0 % |
| **mínimo dNTI fuera** | 0,01 PAPER (Tabla 1, C1 ROI2, el mismo para dNTI y dETI) | **0,02** CÓDIGO (H:183) | SIN DATO | **decide**: `μ+10σ < 0,02` en 51,6 / 75,4 / **92,8 %** |
| **mínimo dETI fuera** | 0,01 PAPER (el mismo C1) | 0,01 CÓDIGO (H:186) | SIN DATO | `μ+10σ_dETI < 0,01` en 53,1 / 75,8 / 54,4 % |
| **N·σ** (5 cumbre / 10 fuera noche; 15 día) | PAPER (Tabla 1, C2) | CÓDIGO (H:180-181, 191-192) | SIN DATO | ver filas anteriores |
| **conectiva** `max(μ+Nσ, mínimo)` | CONTRADICE: el paper escribe `dNTI > C1 or dNTI > μ+C2σ` (p. 7, Tests 2 y 3) | CÓDIGO (H:306-312) | SIN DATO (ni paper ni código) | K ya adoptó `max` en los tres (S153); no es objeto de este frente |
| **Test 1 como alerta directa que sale del fondo** | PAPER (p. 6, «flagged as active and subsequently discarded») | CÓDIGO (H:245, 276, 328) | TRASLADADA (Campus 2024 no lo describe) | casi inerte: ver K1 |
| **media local 3 × 3 con el central** | CONTRADICE: «eight neighbouring pixels» (`sp426_5.txt` l. 242-245, texto; renderizado en S158 por otro frente) | CÓDIGO (H:281-287) | SIN DATO | escala 9/8 en los mínimos fijos (§3.2) |
| **μ y σ de toda la escena** | PAPER (p. 7, «all the suitable pixels within the image») | CÓDIGO (H:303-304) | TRASLADADA | nuestra σ es de la caja nativa (D17) |
| **piso -0,1** | CONTRADICE: el paper lo pone en dNTI y en dETI (p. 5, renderizado en S158) | sólo en dNTI, CÓDIGO (H:298) | SIN DATO | no medido |
| **segundo pase que recalcula μ, σ y la regresión** | PAPER parcial («second run», p. 7, no dice si recalcula la regresión) | CÓDIGO (H:228-235) | TRASLADADA | no medido |
| **regresión cuadrática única** | PAPER (p. 6, Fig. 2a `y = ax² + bx + c`) | CÓDIGO (H:338-345) | TRASLADADA | no medido |
| **filtro píxel frío ≤ 200 K y escena con ≥ 50 % NaN** | SIN DATO (no está en ningún paper leído) | CÓDIGO (H:151, 163-165) | SIN DATO | no medido (el record no persiste la BT mínima del TIR) |
| **sun-glint < 12°** | SIN DATO | CÓDIGO (H:87) | SIN DATO | sólo de día; no corre |
| **unión de todas las alertas de la pasada** (D32) | PAPER: Coppola 2026 p. 5 («All resampled pixels exhibiting anomalous thermal behavior within this area were retained for VRP calculation»), para los tres sensores; Campus 2024 ec. 1 (TEXTO) para 375 | CÓDIGO (H:241-248) | PAPER (mismas citas) | n/a |
| **fondo del VRP: hueco dilatado 3/5/7 e interpolación lineal, sin recorte** | CONTRADICE: «arithmetic mean of all the pixels surrounding» (p. 8 del paper, S158 §4.3) | CÓDIGO (V:64-85) | **CONTRADICE**: Campus 2024 (TEXTO, l. 118-123): «arithmetic mean of the radiance of the pixels surrounding the alerted one(s)» | no medido (F3) |
| **caja de cumbre** | 5 × 5 km PAPER (p. 3) | 7 × 7 celdas = 5,25 km, en la matriz de ejemplo (dato, no comentario) | SIN DATO (¿13 o 14 celdas de 375 m?) | no medido (D18) |
| **dilatación 3/5/7 según Npix ≤ 4 / ≤ 30 / > 30** | SIN DATO | CÓDIGO (V:68-73) | SIN DATO; en celdas de 375 m el mismo número cubre la mitad de terreno | Npix mediana OSF 375 noche = 4 (en el borde del primer tramo) |
| **coeficiente y área nominal** | 18,9 × 10⁶ m² PAPER + OSF (coef = 18.900.000 en p1 a p99 de 243.401 filas noche) | 1,97 × 10⁷ × 0,5625 CÓDIGO (V:88-91) + OSF (mediana 11.081.250, **pero p1 = 3.678.250**, hallazgo 4) | 18,0 × 140.625 = 2.531.250 PAPER (Campus 2024 TEXTO) + OSF (p1 a p99 exactos, 250.990 filas) + jepv6 (354 de 354) | identidad cumplida salvo VIIRS 750 |
| **constantes de Planck y 3,14** | SIN DATO | CÓDIGO (H:403-440) | SIN DATO | efecto sólo cerca del umbral |

Scripts: `02_osf_v25_por_sensor.py` (OSF), `03_jepv6_y_coef750.out` (jepv6 y VIIRS 750), `04_cota_k1_y_sustrato_minimos.py`
(K1 y sustrato), `05_coef750_mecanismo.out`. Ventanas y denominadores en cada salida.

## 2. Hallazgos (ordenados por gravedad)

### H1. El parámetro con menos evidencia es el que más decide: el mínimo de dNTI fuera de la cumbre en VIIRS 375

- **DÓNDE**: `pipeline/profiles/mirova_equivalent.yaml:124` (`dnti_contextual_c1_scene: 0.010`, comentario «Coppola
  2016a Table 2», que es la Tabla 1 de MODIS); el valor efectivo `DNTI_CONTEXTUAL_C1_SCENE = 0.01` se aplica igual en
  los tres procesadores (`pipeline/process_viirs.py:116`, `process_viirs_mod.py`, `process_modis.py:122` lo importan
  de `pipeline.profile`; no hay sobreescritura por sensor: `grep '375' pipeline/profile.py` sólo da flags de magnitud).
  Medición: `04_cota_k1_y_sustrato_minimos.py`, salida `.out`, sección M2.
- **QUÉ PASA**: la física primero. Fuera de la cumbre la escena de VIIRS 375 es muy homogénea de noche (σ del
  contraste de dNTI chica), así que `μ + 10σ` cae bajo el mínimo fijo y el mínimo pasa a ser el umbral real. En Chile,
  marzo a octubre de 2026, `μ + 10σ < 0,02` en el **92,8 % de 5.226 pasadas nocturnas de VIIRS 375**, en el 75,4 % de
  6.318 de VIIRS 750 y en el 51,6 % de 5.259 de MODIS (fracciones impresas por el script; denominador = pasadas
  `pos` más `neg_limpio` con `diag_mu_dnti` y `diag_sd_dnti`). Con el mínimo de 0,010 que usamos, la rama
  estadística sólo queda abajo en 11,3 / 5,9 / 7,4 %. O sea: el número que fija cuántos píxeles de escena se alertan
  en VIIRS 375 es el mínimo, y para VIIRS 375 **no hay ningún dato** (ni paper, ni código, ni OSF: §1). En VIIRS 750 el
  código dice 0,02 y usamos 0,010: en cerca del 70 % de las pasadas (75,4 menos 5,9) nuestro umbral de escena es la
  mitad del de MIROVA, y en unidades nuestras (dNTI de 8 vecinos, 9/8 del de 3 × 3) el 0,02 de MIROVA vale 0,0225.
- **Matices del instrumento**: `diag_mu_dnti` y `diag_sd_dnti` son del primer pase, con el dNTI de 8 vecinos y la σ
  sobre la caja nativa (D17), no sobre la grilla de 67 × 67 de MIROVA. La fracción puede moverse con el remuestreo,
  pero no cambia la conclusión de que el mínimo gobierna en la mayoría de las pasadas de VIIRS 375.
- **CÓMO SE VE EN EL DASHBOARD**: los píxeles de escena alertados de más caen fuera del `inner_radius_km` y el tablero
  los oculta (`far`), así que el operador no los ve directamente; sí entran al segundo pase y a la recaptura y pueden
  sumar magnitud a un cúmulo de cumbre que los toque (SOSPECHA en esta última parte: no lo medí).
- **REPRODUCIR**: `python -B experiments/_s158_audit/f4/04_cota_k1_y_sustrato_minimos.py` (ventana 2026-03-01 a
  2026-10-21, referencia snapshot, regla SN).
- **CONFIANZA**: CONFIRMADO en la medición del sustrato; SIN DATO en el valor de VIIRS 375.
- **GRAVEDAD**: 4. Es el número que gobierna la sobre-publicación fuera de cumbre en el sensor que más alertas trae
  (A98), y se eligió por traslado desde MODIS.

### H2. K1 casi no decide en Chile: la cota inferible desde la referencia es K1 ≥ -0,87 y no separa -0,8 de -0,7

- **DÓNDE**: `04_cota_k1_y_sustrato_minimos.out`, sección M1. Campo `diag_nti_max` (máximo del NTI en el ROI de
  detección nativo: `pipeline/process_viirs.py:902`, `process_viirs_mod.py:601`, `process_modis.py:1264`).
- **QUÉ PASA**: el Test 1 de MIROVA es incondicional (NTI > K1 es alerta, H:245), así que si MIROVA miró y no vio nada,
  ningún píxel suyo superó K1. Sobre los negativos limpios, el máximo de `nti_max` es -0,864 (MODIS, n = 5.168),
  -0,868 (VIIRS 375, n = 3.834, 12 sin dato) y -0,877 (VIIRS 750, n = 5.994). Cero negativos sobre -0,8 en los tres.
  Entre los positivos: VIIRS 375 sobre -0,7 son 25 de 1.392 (1,8 %), sobre -0,8 son 44 (3,2 %); VIIRS 750 sobre -0,7
  son 5 de 324 (1,5 %); MODIS sobre -0,8 es 1 de 96. El traslado de K1 -0,8 a VIIRS 375 toca a lo sumo 19 pasadas
  positivas (las que están entre -0,8 y -0,7) en ocho meses, todas ya positivas.
- **Las dos preguntas**: (1) si K1 de VIIRS 375 fuera -0,8 y hubiera negativos entre -0,8 y -0,7, M1 los contaría; no
  los hay. (2) Control positivo en VIIRS 750, donde K1 = -0,7 es dato: 0 de 5.994 negativos sobre -0,7, como exige el
  código, así que nuestro `nti_max` no contradice al de MIROVA. Pero 0 también sobre -0,8: **el instrumento no tiene
  poder para distinguir -0,7 de -0,8** con negativos. Con positivos tampoco, porque un positivo puede venir del test
  contextual. Lo que sí prueba es el tamaño del efecto: pequeño. Matiz: el remuestreo de MIROVA suaviza el pico, así
  que su máximo es menor o igual que el nuestro y la cota es conservadora hacia arriba.
- **CÓMO SE VE EN EL DASHBOARD**: invisible (las pasadas afectadas ya se publican por el camino contextual).
- **REPRODUCIR**: el mismo script.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD**: 1 para el valor de K1 en sí; el hallazgo importa porque ordena el trabajo: medir el mínimo de escena
  (H1) antes que K1.

### H3. El mínimo de cumbre 0,003 es inerte en los tres sensores; lo que decide en la cumbre es 5σ y la caja

- **DÓNDE**: misma salida, M2: `μ + 5σ < 0,003` en 0,8 % (MODIS), 0,0 % (VIIRS 375), 0,2 % (VIIRS 750); mediana de
  `μ + 5σ` 0,0098 / 0,0067 / 0,0081.
- **QUÉ PASA**: en la cumbre la rama estadística siempre está arriba del mínimo. «Cumbre (5σ, 0,003), probablemente
  igual» en `docs/S158_CODIGO_MIROVA_VS_VRP_CHILE.md` §5 es verdad en lo que no importa: el 0,003 de VIIRS 375 puede ser
  cualquier cosa bajo 0,006 sin cambiar nada; lo que falta medir para 375 es el tamaño de la caja de cumbre (D18) y la
  σ sobre la grilla (D17), que sí entran en 5σ.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CONFIANZA**: CONFIRMADO (con el matiz de instrumento de H1).
- **GRAVEDAD**: 2 (ordena prioridades; no tuerce una alerta).

### H4. (Fuera de alcance, F6) El 8,2 % de las filas de VIIRS 750 del OSF no cumplen la fórmula del código

- **DÓNDE**: `03_jepv6_y_coef750.out`, `05_coef750_mecanismo.out`; OSF v2.5, 100.641 filas de `Resolution = 750`,
  2012 a 2025.
- **QUÉ PASA**: 8.239 filas tienen `VRP / (Tot_Lmir_hot − Tot_Lmir_bk)` distinto de 11.081.250 (razón al valor de la
  fórmula: p10 0,25, mediana 0,51, p90 0,75). Son anomalías grandes (VRP mediana 244 MW contra 30 MW; Npix mediana 19
  contra 8; L_hot por píxel mediana 2,9 contra 0,74 W m⁻² sr⁻¹ µm⁻¹; el 48 % tiene L_hot por píxel sobre 3, contra
  13 % en las normales). Están en todos los años (247 en 2012 a 596 en 2025). En VIIRS 375 y MODIS el coeficiente es
  exacto en p1 a p99. **La cadena de producción de VIIRS 750 tiene una rama que la versión publicada no trae**
  (SOSPECHA sobre el mecanismo: saturación de M13 o sustitución por otra banda; no lo medí).
- **Por qué le importa a F4**: «para VIIRS 750 manda el código» vale para la detección y para el VRP de anomalías
  chicas; para las grandes el código no reproduce lo publicado. Trasladar «el VRP es la fórmula sin recorte» a 375 y
  MODIS tiene mejor respaldo (la identidad se cumple ahí al 100 %) que en el propio VIIRS 750.
- **CÓMO SE VE EN EL DASHBOARD**: invisible hoy (nuestros cúmulos de VIIRS 750 rara vez llegan a esos niveles).
- **CONFIANZA**: CONFIRMADO el número; SOSPECHA el mecanismo.
- **GRAVEDAD**: 3 (para F6 y para la regla «el código manda»).

### H5. El OSF v2.5 no puede dar umbrales de detección para ningún sensor: sus pisos son los filtros de Coppola 2026

- **DÓNDE**: `02_osf_v25_por_sensor.out`; Coppola 2026 Tabla 1 (p. 7-8 del PDF, renderizadas: `paginas/Coppola_2026_SciData_p7.png`, `_p8.png`).
- **QUÉ PASA**: VRP mínimo por sensor y dayflag en el OSF: VIIRS 375 noche 10.004 W (Tabla 1: 1,0 × 10⁴); VIIRS 750
  noche 5.000.049 W (Tabla 1: **5,0 × 10⁶**); MODIS noche 100.013 W (Tabla 1: 1,0 × 10⁵); día 5,0 × 10⁷ en los tres.
  El ΔL por píxel mínimo con Npix = 1 de noche es exactamente el filtro dividido por el coeficiente (375: 0,00395;
  MODIS: 0,00529). Consecuencias: (a) ningún umbral de detección (K1, mínimos, N·σ) se puede inferir del OSF en ningún
  sensor; (b) el producto de VIIRS 750 del OSF es sólo de anomalías de 5 MW o más (Npix = 1 en 151 de 82.782 filas
  nocturnas, 0,2 %), así que toda comparación de VIIRS 750 contra el OSF (F3, D25) mide anomalías fuertes; (c) el
  dato de Vulcano (jepv6, 354 alertas de VIIRS 375, 2021 a 2023) sí es NRT sin filtro declarado: VRP mínimo 20.512 W,
  ΔL por píxel mínimo 0,0081, Npix = 1 en 191 de 354.
- **CONFIANZA**: CONFIRMADO. Refuerza A105 con números por sensor.
- **GRAVEDAD**: 2 (evita diseñar una inferencia que no puede funcionar).

### H6. «Lo estructural se traslada con apoyo citable» descansa en la misma evidencia que falló para los números

- **DÓNDE**: `docs/S158_CODIGO_MIROVA_VS_VRP_CHILE.md` §5, primer párrafo. Citas: Campus 2022 p. 7 §3.2 (renderizada,
  `paginas/campus2022_sensors_2_p7.png`): «The hot-spot detection algorithm is the same used for MODIS» y «steps 1 to
  4 have been slightly modified from [28] and adapted to VIIRS»; Coppola 2026 p. 5 (renderizada): «the
  hotspot-detection code used by MIROVA», singular.
- **QUÉ PASA**: las dos frases hablan del algoritmo entero. Son exactamente las frases con las que se trasladaron
  K1 y el mínimo de escena, que resultaron distintos. Si no distinguen números, tampoco distinguen estructura. Y hay
  tres elementos estructurales donde el paper del otro sensor **contradice** al código de VIIRS 750: la media local (8
  vecinos en Coppola 2016a contra 3 × 3 con central), el piso de -0,1 (en dNTI y dETI contra sólo dNTI) y el fondo del
  VRP (media de los vecinos en Coppola 2016a y en Campus 2024 para 375 contra interpolación bajo hueco dilatado). Para
  esos tres, el único respaldo de trasladar es que el código de VIIRS 750 es más reciente que los papers; eso es un
  criterio, no evidencia del otro sensor. Lo que sí tiene cita para los tres sensores: la unión de todas las alertas
  (Coppola 2026 p. 5) y el ETI con regresión (Coppola 2016a p. 6, Fig. 2).
- **CÓMO SE VE EN EL DASHBOARD**: no aplica (es un juicio sobre el documento).
- **CONFIANZA**: CONFIRMADO (lecturas renderizadas).
- **GRAVEDAD**: 3. El plan 7 bis, punto 7, propone «trasladar lo estructural a MODIS y VIIRS 375, con su propio A/B»;
  el A/B es la parte que vale, la cita no.

### H7. K1 diurno: el código usa -0,5; la rama diurna (apagada) trae -0,6 de la Tabla 1 de MODIS; el informe S158 no lo registra

- **DÓNDE**: `MIROVA_VIIRS750_hotspot_detection.m:189` (`absoluteNTIthreshold = -0.5`); `pipeline/profile.py`
  (`NTI_K1_DAY = -0.6`); `pipeline/process_viirs.py:733-744` y `process_viirs_mod.py:474-481` (comentario «K1 = -0,6»);
  `pipeline/profiles/mirova_equivalent.yaml:474-479` (`enable_daytime_viirs: false`). El informe
  `docs/S158_CODIGO_MIROVA_VS_VRP_CHILE.md` §3 se titula «VIIRS 750 de noche» y §5 sólo tabula «K1 noche».
- **QUÉ PASA**: de día MIROVA sube K1 porque el sol calienta y refleja en el MIR; el código de VIIRS 750 lo pone en
  -0,5, la Tabla 1 de MODIS en -0,6. Los demás valores diurnos coinciden (15σ en las dos regiones, mínimos 0,02 en dNTI
  y dETI). Es el mismo error de traslado de la noche, un paso antes de que corra.
- **CÓMO SE VE EN EL DASHBOARD**: invisible mientras la rama diurna esté apagada.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD**: 2 (latente; sube a 3 el día que se encienda el A/B diurno de S151 con -0,6).

### H8. Coppola 2025 cap. 11 Tabla 2 no es evidencia para VIIRS: sólo trae el NTI de MODIS, atribuido a Wright 2002

- **DÓNDE**: `978-3-031-86841-2.pdf`, p. 340 del PDF (p. impresa 336), renderizada en `paginas/libro_cap11_p340.png`.
  Nota: `978-3-031-86841-2_9.pdf` de `documentacion/` es el capítulo 9 (gases), no el 11.
- **QUÉ PASA**: la fila NTI de la Tabla 2 dice -0,8 noche y -0,6 día, satélite «Terra (MODIS), Aqua (MODIS)»,
  referencia Wright et al. 2002. No hay fila de VIIRS. Coppola 2016a p. 6 dice lo mismo: los K1 se fijaron «according
  to the global application and validation of the NTI thresholds within the MODVOLC algorithm». O sea, el K1 de MODIS
  es un préstamo de MODVOLC; el de VIIRS 750 lo cambió MIROVA (-0,7) y el de VIIRS 375 nadie lo publicó.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD**: 1 (precisa de dónde sale cada número).

## 3. Diseño de las mediciones que faltan, con su poder (T8)

### 3.1 El mínimo de dNTI fuera de la cumbre en VIIRS 375 (y comprobar el 0,02 en VIIRS 750)

- **Pregunta**: ¿qué mínimo fijo reproduce lo que MIROVA publica y deja de publicar fuera de la cumbre?
- **Dato que falta**: el dNTI por píxel. `anomaly_pixels` sólo persiste `lat, lon, vrp_mw, bt_k, dist_km` (comprobado en
  `data/mirova_equivalent/Villarrica.json`, records VIIRS_SNPP 2026-10-15 06:42 y VIIRS_SNPP_750 2026-08-19 06:06).
  Hace falta reprocesar gránulos con un diagnóstico extra: el máximo del dNTI (3 × 3 con central, para estar en las
  unidades de MIROVA) fuera de la caja de cumbre, y la σ de escena.
- **Diseño**: sobre la grilla remuestreada (D17) si existe, o sobre la caja nativa si no (declarándolo). Para cada
  pasada nocturna etiquetada por `banco_paridad`: `far_ref` (MIROVA alertó fuera de la cumbre: FALSO_POSITIVO del
  scraper, 356 pasadas de VIIRS 375 en la ventana) contra `neg_limpio` (3.846). Ajustar por máxima verosimilitud un
  umbral `t` sobre `max dNTI fuera` tal que `max(μ+10σ, t)` separe mejor las dos clases; informar el intervalo por
  bootstrap (5.000 remuestreos, como `experiments/_s124_f70/05_poder_estadistico.py`).
- **Poder**: con 356 contra 3.846 y una diferencia de factor 2 en el umbral (0,01 contra 0,02), la separación esperada
  del `max dNTI` entre clases es de varias σ de escena; con n ≥ 300 por clase, un test de dos proporciones detecta un
  cambio de 10 puntos en la tasa de publicación con potencia > 0,9 a α = 0,05. El factor limitante no es n, es el
  instrumento: la etiqueta `far_ref` del OCR es confiable sólo desde el 2026-06-11 (A119), así que la ventana útil es
  junio a octubre (contar n ahí antes de correr).
- **Control positivo**: correrlo en VIIRS 750, donde la respuesta es 0,02: si el ajuste da 0,02 ± 0,005, el instrumento
  sirve; si da 0,010, mide otra cosa (por ejemplo la σ nativa, D17).
- **Costo**: un reproceso de 4 meses de VIIRS 375 y 750 en 11 volcanes con un diagnóstico nuevo (no toca la detección
  si el diagnóstico es aditivo; aun así A45).

### 3.2 La caja de cumbre en VIIRS 375 (D18)

- **Dato**: los TIF UTM de MIROVA de VIIRS 375 sólo existieron del 2026-09-14 al 15 (A106, ocho adquisiciones): no
  alcanzan. Alternativa: las alertas `far_ref` del scraper con `Distancia_km` (desde el 2026-06-13) dan la distancia
  mínima a la que MIROVA llama «lejana»; el borde entre «en cráter» y «lejana» del OCR, si MIROVA lo deriva de la
  caja, aparece como un escalón en la distribución de `Distancia_km` de las alertas. Poder: con 356 lejanas y 1.392
  en cráter se ve un escalón de 1 km; pero `Distancia_km` no trae acimut (A93), así que una caja cuadrada aparece
  como un rango de 2,6 a 3,7 km, no como un valor. Es barato (sólo CSV) y lo dejo diseñado, no corrido: el frente F3
  ya cubre la geometría y no quise duplicar.

### 3.3 Filtro de 200 K y escena con ≥ 50 % NaN

- No se puede medir con los records (no persisten la BT mínima del TIR ni la fracción de NaN). Físicamente 200 K en el
  TIR sólo aparece en topes de nube convectiva profunda o en píxeles inválidos; en Chile de noche la palanca esperada
  es casi nula. Lo dejo como SIN DATO de bajo rendimiento: no gastar en esto antes que en 3.1.

## 4. VERIFICADO LIMPIO (contra qué vara)

| qué | vara | cómo se comprobó |
|---|---|---|
| Los tres procesadores usan los mismos umbrales de detección (sin sobreescritura por sensor) | código de hoy | `VRP_PROFILE=mirova_equivalent python -B -c "import pipeline.profile as p; ..."`: `NTI_K1_NIGHT -0.8`, `C1_SUMMIT 0.003`, `C1_SCENE 0.01`, `N_SIGMA 5/10`, `ENABLE_ROI1_BOX_PAPER False`, `ENABLE_DAYTIME_VIIRS False`; `grep -n "NTI_K1\|DNTI_CONTEXTUAL_C1" pipeline/process_*.py` sólo importa de `pipeline.profile` |
| Coppola 2016a Tabla 1 (MODIS): K1 -0,8/-0,6, C1 0,003/0,01 noche y 0,02 día, C2 5/10 y 15/15; un solo C1 «for both dNTI and dETI» | PDF renderizado p. 7 | `paginas/sp426.5_p7.png` |
| El código de VIIRS 750 noche: K1 -0,7; 10σ y 0,02/0,01 en BOX0 y ROI1; 5σ y 0,003/0,003 en ROI2; día K1 -0,5, 15σ, 0,02 en todo | `MIROVA_VIIRS750_hotspot_detection.m:178-198` | leído entero; líneas reverificadas con `grep -n` al cierre |
| Coeficientes por sensor en el OSF: 18.900.000 (MODIS), 11.081.250 (VIIRS 750, mediana), 2.531.250 (VIIRS 375), p1 a p99 exactos salvo VIIRS 750 | OSF v2.5, 615.470 filas, 2000-02-24 a 2025-12-31 | `02_osf_v25_por_sensor.out` |
| jepv6 (Vulcano, VIIRS 375, 354 alertas): coeficiente 2.531.250 en las 354, ΔL > 0 en las 354, VRP mínimo 20.512 W | `_tmp_jepv6/S1_MIROVA_Vulcano.csv` | `03_jepv6_y_coef750.out` |
| `diag_nti_max` de VIIRS 750 en negativos limpios nunca supera -0,7 (0 de 5.994): nuestro NTI no contradice el K1 del código | referencia snapshot, ventana 2026-03-01 a 2026-10-21 | `04_cota_k1_y_sustrato_minimos.out` M1 |
| El oráculo `experiments/_s158_oraculo_mirova/mirova_v750.py` reproduce los umbrales del `.m` (K1 -0,7; 10/5; 0,02/0,003; 0,01/0,003; día -0,5/15/0,02) | el `.m` | lectura de `hotspot_detection`, l. 165-167 del port |
| Coppola 2026 p. 5: un solo «hotspot-detection code»; la unión de alertas vale para los tres sensores; p. 7-8 Tabla 1 con los filtros por sensor | PDF renderizado | `paginas/Coppola_2026_SciData_p5.png`, `_p7.png`, `_p8.png` |
| Campus 2022 p. 7 §3.2: «the same used for MODIS», sin números; p. 16 (Tabla 4 es de volcanes, no de umbrales) | PDF renderizado | `paginas/campus2022_sensors_2_p7.png`, `campus2022_p16.png` |
| Aveni 2024 (TIRVolcH) no fija umbrales del MIR de 375 m; describe su propio algoritmo TIR (grilla 134 × 134 UTM, p. 5; tests 11 a 16, p. 11) | PDF renderizado | `paginas/Aveni_2024_TIRVolcH__p5.png`, `_p11.png` |

## 5. Fuera de alcance (anotado, no seguido)

- H4 (VIIRS 750 del OSF fuera de fórmula en 8,2 %): F6.
- La caja de cumbre y la distancia de las alertas lejanas (§3.2): F3 / D18.
- `banco_paridad` imprime 8 avisos de A119 para la ventana; para H1 y H2 usé la tabla y el OCR juntos (etiqueta
  `pos` y `neg_limpio` de `banco_paridad`, regla SN); la cota de K1 sólo usa `neg_limpio`, que es de la tabla (CONS).

## 6. Lo que no pude medir, y por qué

- El mínimo de dNTI fuera de la cumbre en VIIRS 375 (H1): hace falta un diagnóstico por píxel que los records no
  persisten; diseño en §3.1, costo un reproceso.
- Si el remuestreo cambia las fracciones de M2: `diag_sd_dnti` es de la caja nativa (D17 sin implementar).
- El filtro de 200 K y la escena con ≥ 50 % NaN (§3.3): sin campos en los records.
- El mecanismo de H4 (saturación u otra banda): no está en el código publicado ni en los papers leídos.
- Campus 2024 lo leí por la capa de texto (`campus2024_extracted.txt`, no hay PDF en `documentacion/`); lo cito como
  TEXTO. Coppola 2016a l. 242-245 y p. 8 («eight neighbouring», «surrounding») los tomo del informe S158, que los
  renderizó; no los volví a renderizar.
- El poder de §3.1 está estimado, no calculado por simulación: no hay dato por píxel con el que simular.
