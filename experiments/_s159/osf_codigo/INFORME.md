# S159, frente «el código OSF de MIROVA, entero»: los dos `.m` paso a paso contra `pipeline/` de hoy

Fecha 2026-10-21. Sólo lectura: no se tocó nada fuera de `experiments/_s159/osf_codigo/`, sin git, sin workflows.
Vara: `experiments/_s158_d17_diseno/osf_codigo_mirova/MIROVA_VIIRS750_hotspot_detection.m` (**H**, 444 líneas) y
`MIROVA_VIIRS750_VRP.m` (**V**, 92 líneas), leídos enteros en esta sesión con `cat -n`; README.txt, CITATION.txt y
`Example/run_example.m` también. Nuestro lado: worktree `C:\vrp-trabajo\s159-pruebas` en `b4adf13cf`,
`pipeline/process_viirs_mod.py` (**pvm**), `pipeline/detection_context.py` (**dc**), `pipeline/store.py`,
`scripts/run_pipeline.py`, `pipeline/fetch.py`, `pipeline/diurno.py`, `frontend/index.html`; valores efectivos leídos
de `pipeline.profile` con `VRP_PROFILE=mirova_equivalent` (volcado completo en la sesión, no del YAML). Lo que es
inferencia propia lleva **SOSPECHA**.

Copias locales contra OSF: los cuatro archivos de texto son byte a byte los del OSF salvo el fin de línea (local CRLF,
OSF LF): `md5` tras `tr -d '\r'` = 5ef30868… (H), 2e95d1d3… (V), 154c6a22… (README), 7484c4c3… (CITATION), los
mismos que publica la API de OSF, todos `current_version 1`, `date_modified 2026-07-24`.

Instrumento propio: `pasos_del_m.py` → `pasos_del_m_salida.txt` (encabezado con las dos preguntas; control positivo
Etna 5 alertas y Tot_Lmir_hot 1,965342180 reproducido; control negativo token inventado = 0 archivos).

## 0. En una pantalla

1. **El código no elige ni recorta gránulos.** Recibe una matriz `ZI_M13` de 67 × 67 ya remuestreada («resampled»,
   H:19-23) y una `BOX` del mismo tamaño; la única decisión de escena que trae es rechazarla entera si la mitad o más
   del NTI es NaN (H:163-167). Todo lo anterior (qué gránulo, cómo se remuestrea, dónde se centra) está fuera: «The code
   intentionally excludes operational components [...] including file-system logic, volcano databases, cloud outputs,
   quality-flag outputs, geolocation diagnostics» (README.txt:9). La regla «gránulo sur» del frente pareo_modis pasa
   antes de este código, y el código no la contradice ni la confirma.
2. De **42 pasos** contados en los dos `.m` (tabla §2), nuestro lado hace **IGUAL 12**, **DISTINTO 22**, **NO EXISTE
   en el nuestro 7**, **NO EXISTE en el suyo 1**. De los 29 no iguales, **24 ya tienen D en el catálogo o un frente de
   S158/S159**. Quedan **5 sin frente ni A/B** (§4): el rechazo por sun-glint, el marco de la ventana como no
   detectable, el filtro de píxel frío de M15 más el rechazo de escena incompleta, el piso de dETI que sacamos del
   pool de μ y σ (MIROVA no lo saca), y la desviación con N en vez de N − 1. Ninguno mueve hoy una publicación
   protegida de noche; el primero sí puede moverlas el día que se encienda la rama diurna (D-10).
3. **Día, saturación y nube** (§3): el código trae la rama diurna completa (K1 −0,5, 15σ, mínimos 0,02) y el rechazo
   por sun-glint < 12°; no trae nada de saturación ni de nube salvo el filtro de M15 ≤ 200 K, y el README lo dice
   explícito: «Quality screening, cloud assessment, input preparation [...] remain the responsibility of the user»
   (README.txt:92).
4. **El segundo pase del código corre siempre y sobre toda la escena**, sin la condición «sólo si hubo detección» ni la
   restricción «adyacentes» del paper (H:228-235 llama a la misma función con la misma máscara). Con el conjunto
   previo vacío es idéntico al primero y no puede agregar nada. El nuestro sí agrega con el primero vacío (F1 H5: 19 de
   67 publicados en K) porque difiere del primero en tres cosas que el código no tiene (sin compuerta de 3 K, sin
   filtros de no aptos, reusa la regresión: D22, D26). Para la decisión D19 D1/D2: la condición (b) «adyacentes» del
   flag `enable_second_pass_conditioned` **no está en el código de MIROVA**.
5. **OSF sin novedades de código** (§5): desde el 2026-07-24 sólo hubo dos renombres de carpetas (2026-08-16) y dos
   ediciones de la cita (2026-08-19). `scripts/vigilar_osf_mirova.py` en modo lectura: «sin novedades en 7 proyectos
   OSF del grupo MIROVA».

## 1. Advertencias de lectura (las de S158 siguen vigentes)

- El `.m` llama «ROI 1» a la región conservadora y «ROI 2» a la sensible (H:107-118), al revés de la nomenclatura
  del paper; en la matriz de ejemplo la clase 2 es el cuadro central de 7 × 7 (O1 §VERIFICADO LIMPIO). Abajo uso
  **cumbre** (= `BOX == 2`, umbrales sensibles) y **fuera** (= `BOX == 1` y `BOX == 0`, umbrales conservadores).
- `contextualDetectionPass` resta y mide sobre `ZI_NTI_backgroundPopulation`, que ya tiene NaN en las alertas absolutas
  y en las del pase previo (H:275-277): esos píxeles no pueden ser detectados de nuevo ni entran a ninguna media.
- Con el perfil de producción el primer pase de Tests 2 y 3 **reemplaza** la máscara de los caminos antiguos
  (pvm:904 `hot_mask_2d = fp_hot`); el camino D «dnti_ctx», el de BT y el NTI absoluto se calculan sólo como
  diagnóstico (pvm:663-664 apaga BT; pvm:836-844 se sobrescribe). El Test 1 integrado está apagado
  (`ENABLE_TEST1_PATH = False`), así que el bloque pvm:1296-1375 (magnitud focal, keep_peak en V750) **no corre**.

## 2. Tabla completa, paso a paso

Columnas: paso del código → qué hace → nuestro lado hoy → veredicto → frente. «Frente» = D del catálogo
`docs/MIROVA_DIVERGENCES.md`, o informe de `experiments/_s158*` / `_s159/*`; «ninguno» = ninguno encontrado (busqué por
palabra clave en el catálogo y en los títulos de hallazgo de F1 a F6, V1 a V3, N, O1, GEO, P1 a P3, pareo_modis).

### 2.1 `MIROVA_VIIRS750_hotspot_detection.m`

| # | código (H:línea) | qué hace | nuestro lado (archivo:línea) | veredicto | frente |
|---|---|---|---|---|---|
| 1 | H:1-2, 67-78 | firma `(ZI_M13, ZI_M15, BOX, dayflag, sunglint)`; valida tipos, 2D, mismo tamaño, escalares | `calculate_vrp(l1b_path, geo_path, lat, lon, radius_km, vent…)` (pvm:438-448): recibe archivos, no matrices; sin `sunglint` | DISTINTO (entrada) | D17 (remuestreo), GEO |
| 2 | H:19-23 | entradas son **radiancias** `[W m^-2 sr^-1 um^-1]` remuestreadas | leemos BT del LUT de la L1B (pvm:244-253, 278-286) y volvemos a radiancia con Planck CODATA (pvm:352-355; `constants.py:20-21`) | DISTINTO | F1 H8 (sesgo −0,55 % a 240 K, SOSPECHA) |
| 3 | H:81, 87-89 | **sun-glint**: si `sunglint < 12` o no finito, `return` con alerta vacía | **no existe**: `grep -ri glint pipeline/ scripts/` = 0 (`pasos_del_m_salida.txt` A); la geometría solar y de sensor sí se lee (pvm:338-348, «solo para estudio») | NO EXISTE EN EL NUESTRO | ninguno (D-10 pendiente no lo menciona) |
| 4 | H:95-97 | todo a `double` | BT `float32` del LUT (pvm:247); NTI se calcula en float32 y se castea después (dc:683) | DISTINTO (precisión) | ninguno (sin efecto medible: O1 §2.4 margen mínimo 2,8e-5, float32 resuelve ~5e-8) |
| 5 | H:102-103 | el **marco** de la ventana de 67 × 67 pasa a NaN: no se detecta ni entra a estadísticos | `_edge_unsuitable_mask` (dc:64-78, 123) sólo lo saca del pool de μ y σ; el borde del **gránulo** sigue detectable (dc:547-552 no lo excluye); el borde de nuestra caja de 50 km tampoco | DISTINTO | ninguno |
| 6 | H:105-138 | tres dominios: `BOX==2` cumbre (sensible), `BOX==1` y `BOX==0` fuera (conservador); cajas en celdas, ajustables por volcán | cumbre = círculo `inner_radius_km` (3 a 20 km, `volcanoes.yaml`; dc:299-325); fuera = resto de la caja de 50 km (pvm:538) | DISTINTO | D18, GEO, F1 H3 |
| 7 | H:140 | `excludedPixels = isnan(BOX)`: fuera del dominio no hay detección | `roi_mask` de 50 km (pvm:538) y `hot = roi_mask & …` (dc:547-548) | IGUAL (concepto) | |
| 8 | H:144-145 | λ M13 4,05 µm, M15 10,763 µm | pvm:169-170 | IGUAL | |
| 9 | H:150-154 | BT de M15 ≤ 200 K → NaN en BT y en M15 («invalid or strongly contaminated») | no existe; sólo el techo de 343 K (pvm:182, 286) y el bit de saturación | NO EXISTE EN EL NUESTRO | F1 H8 (SIN DATO), F4 §3.3 (diseño); medido acá: 0 de 190 escenas chilenas, 66 de 600 sintéticas |
| 10 | H:159 | NTI = (M13 − M15)/(M13 + M15) | pvm:554-558 | IGUAL | |
| 11 | H:163-167 | **rechazo de escena**: `sum(isnan(NTI)) >= floor(numel/2)` → sin alertas | no existe; exigimos ≥ 10 píxeles en el anillo (pvm:566) y ≥ 10 en el pool (dc:432, 501) | NO EXISTE EN EL NUESTRO | F1 H8 (proxy: 0 de 64 publicadas), F4 §3.3; acá 0 de 190 chilenas, 25 de 600 sintéticas |
| 12 | H:170-171 | NTI restringido al dominio | ídem 7 | IGUAL | |
| 13 | H:177-187 | **noche**: K1 −0,7; σ cumbre 5, fuera 10; mín dNTI cumbre 0,003, fuera **0,02**; mín dETI cumbre 0,003, fuera 0,01 | K1 **−0,8** (`NTI_K1_NIGHT`, YAML:47); C2 5/10; C1 dNTI y dETI 0,003 cumbre, **0,010** fuera (`DNTI_CONTEXTUAL_C1_SCENE`, YAML:124; pvm:891-894 pasa el mismo C1 a dNTI y dETI) | DISTINTO en K1 y en mín dNTI fuera; IGUAL en lo demás | D34; F1 H4 (0,02 decide 3 de 4 pasadas); F4 H2 (K1 casi no decide); medido acá: el umbral dNTI fuera es el piso en 171 de 190 chilenas |
| 14 | H:188-199 | **día**: K1 −0,5; 15σ en las dos; mínimos 0,02 en las dos | rama apagada (`ENABLE_DAYTIME_VIIRS = False`; `store.py:203-224` rechaza el diurno); `diurno.py:121-148` trae K1 **−0,6**, 15σ, 0,02 | DISTINTO (K1) y apagada | D27, D-10, F1 H2 (3 protegidas diurnas de Chillán perdidas), F4 H7 |
| 15 | H:206 | **Test 1 absoluto** `NTI > K1` dentro del dominio | se calcula (pvm:668-675, con compuerta `bt > t_bg + 3 K`) pero no entra a la máscara final (pvm:904) | DISTINTO | D23; medido acá: 7 de 190 chilenas con algún píxel > −0,7 |
| 16 | H:275-277, 328-329 | los absolutos (y el pase previo) **salen** de la población de fondo del NTI, del NTI esperado y de la regresión | no salen: `ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK = False` → `test1_mask=None` (pvm:876-878, dc:496); la regresión se ajusta con todos (dc:760-765) y luego refit 3σ | DISTINTO | GAP #A (reabierto S128), D29 |
| 17 | H:281-287 | fondo local = media de la ventana **3 × 3 con el central**, sin NaN (`colfilt`) | media de los **8 vecinos sin el central** (dc:147-189) | DISTINTO | D34 (sin A/B aislado; incluido en el brazo post hoc «paquete entero» de N) |
| 18 | H:288, 293-294 | contraste dNTI = población − fondo local; NaN fuera del dominio | dc:485 | IGUAL | |
| 19 | H:298 | **piso −0,1 sólo en dNTI**: `< -0.1 → NaN` (sale de μ, σ y de la detección) | dNTI < −0,1 **y** dETI < −0,1 salen del pool (dc:98-99, 127-129; `ENABLE_UNSUITABLE_FILTERS_267_273 = True`) | DISTINTO (dETI) | D34 (registrado, sin A/B) |
| 20 | H:303-304 | μ y σ del contraste sobre **toda la ventana** (67 × 67 menos marco y NaN), `std(...,0)` = N − 1 | μ y σ sobre el pool dentro de la caja de 50 km del barrido nativo (dc:507-510), `np.std` = N | DISTINTO (dominio: D17; N vs N − 1: despreciable) | D17, GEO; el N − 1: ninguno |
| 21 | H:306-312 | umbral = `max(μ + Nσ, mínimo)`, por región | `combinar = max` con `ENABLE_TESTS_23_PROSE_BRANCH = True` (dc:525, 530-535) | IGUAL | K (#850) |
| 22 | H:319-326 | M13 esperado desde BT de M15 (Planck con **3,14**, h 6,6256e-34, c 2,9979e8, k 1,38e-23), NTI esperado | `compute_nti_and_nti_app` (dc:672-683) con CODATA y π implícito | DISTINTO (constantes) | D34 (efecto chico, sin medir) |
| 23 | H:335-341 | regresión sólo si ≥ 3 puntos válidos; si no, el pase devuelve vacío | `min_pixels = 10` → ETI NaN → sin detección (dc:707, 757-758) | IGUAL (espíritu) | |
| 24 | H:343-350 | **un** `polyfit` de grado 2 sin absolutos ni pase previo | `np.polyfit(x, y, 2)` más refit iterativo a 3σ, hasta 3 vueltas (dc:765-788) | DISTINTO | D29 |
| 25 | H:357-358 | ETI = población − referencia espectral | dc:792 | IGUAL | |
| 26 | H:362-369 | fondo local de ETI 3 × 3 con central; contraste; NaN fuera | 8 vecinos (dc:484, 486) | DISTINTO | ídem 17 |
| 27 | H:373-382 | μ, σ del dETI sobre toda la ventana; `max(μ + Nσ, mínimo)` | dc:509-510, 531-533 | IGUAL (conectiva), DISTINTO (dominio, 20) | |
| 28 | H:389-399 | alerta = dNTI > umbral **∧** dETI > umbral, por región; sin condición de temperatura | `pass_2 & pass_3 & gate_bt` con `gate_bt = bt > t_bg + 3 K` (dc:546-552; pvm:885 pasa `NTI_BT_SANITY_K = 3`) | DISTINTO (compuerta) | D22; N brazo C (0 de 391 publicaciones cambian) |
| 29 | H:211-218 | primer pase: excluye sólo los absolutos | ídem 16 | DISTINTO | GAP #A |
| 30 | H:228-235 | **segundo pase**: misma función, excluye absolutos + pase 1, **recalcula μ, σ y la regresión**; corre siempre, sobre toda la escena, sin restricción de adyacencia | `second_pass_adjacent` (dc:822-967): reusa el ETI del primero (pvm:916), recalcula μ, σ sin los filtros de no aptos (dc:923), **sin compuerta de BT**; `conditioned = False` (YAML:440) | DISTINTO en regresión, filtros y compuerta; IGUAL en «corre siempre y sobre toda la escena» | D26, D19 (D1/D2 pendiente: la condición (b) adyacentes no está en el código), F1 H5 |
| 31 | H:241-248 | salida = **concatenación** de pase 1 (fuera, cumbre), absolutos, pase 2; sin `unique` | máscara booleana (pvm:965, 1018) | IGUAL en efecto: 0 de 791 escenas con índices repetidos (O1; acá reproducido) | |
| 32 | H:403-421 | Planck inverso con las constantes operacionales | LUT de la L1B (pvm:244-253) | DISTINTO (entrada) | F1 H8 |
| 33 | H:424-444 | Planck directo con 3,14 | ídem 22 | DISTINTO | D34 |

### 2.2 `MIROVA_VIIRS750_VRP.m`

| # | código (V:línea) | qué hace | nuestro lado | veredicto | frente |
|---|---|---|---|---|---|
| 34 | V:45-52 | sin alertas: `VRP_MW = NaN`, `npix = 0`; «must not be interpreted as a measurement of zero» | `vrp_mw = 0.0` (pvm:1027); el tablero toma el 0 como valor | DISTINTO | F1 H9 |
| 35 | V:54-57 | error si un índice excede la matriz | no aplica (máscaras) | NO EXISTE EN EL SUYO lado nuestro / n. a. | |
| 36 | V:60-61 | `npix = numel(alert)` (contaría duplicados; no los hay) | `n_anomalous` (pvm:1019) | IGUAL | |
| 37 | V:64-65 | los alertados pasan a NaN en M13 | `hot_mask_2d` (pvm:1018) | IGUAL | |
| 38 | V:67-78 | **dilatación** del hueco con cuadrado de 3, 5 o 7 celdas (npix ≤ 4, ≤ 30, > 30) | no existe en producción; el flag D25 `ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750 = False` toma justo esos vecinos (pvm:1047-1052) | NO EXISTE EN EL NUESTRO | D25 (adenda S158 §4.3), N brazo F |
| 39 | V:80-81 | fondo 2D por **`fillmissing2` lineal** | escalar: Planck de la **mediana** de BT de M13 en el anillo 5 a 25 km (pvm:539, 560-567, 1041) | DISTINTO | D25, F1 H1, N; O1 H1 (la vara de 1 píxel varía hasta 1,82×, O2 pendiente) |
| 40 | V:83-85 | ΔL = Σ L_hot − Σ L_bk, **sin recorte** | `np.maximum(L_hot − L_bg, 0)` por píxel (pvm:1056) | DISTINTO | D25, F1 H1 |
| 41 | V:88-91 | 1,97e7 × 0,5625 km² | 19,7 × 562.500 m² (pvm:55, 66) = 11.081.250 | IGUAL | |
| 42 | README:41-43, V:1-2 | lo que se devuelve es el VRP de **todas** las alertas de la pasada | cúmulo `vent_anchored` 8-conexo (pvm:1092-1119; `clustering.py:38, 92`), modo de un píxel (pvm:1125-1130), tope D9 (pvm:1110-1112), cero si el píxel más caliente cae lejos (`store.py:393-436`), tope por volcán (`store.py:447-454`, Villarrica 12), tablero exige `pc.vrp_mw > 0` y `summit` (`index.html:1162-1183, 1595-1607`) | DISTINTO | D32, D8', D9, D13, F1 H6 |

Lo que el `.m` **no tiene** y nosotros sí (NO EXISTE EN EL SUYO): el **Test 1 integrado en el ROI** (apagado), el
camino de BT (apagado), el tope D9 de 5 MW, el modo de un píxel, el tope por volcán, la cerca `far`, el filtro por
distancia de píxel (`store.py:354`), la máscara de nube (`CLOUD_MASK_BT_K = 0`, hoy inerte), el bit de saturación y
los techos de LUT (pvm:252, 182), el rechazo diurno de `store.py`. Son nueve cosas; cuento una sola fila (42) porque
todas actúan sobre el mismo paso: qué se publica.

## 3. Lo que el código dice y no dice: gránulo, día, saturación, nube

| tema | lo que dice el código (cita) | lo que hacemos | consecuencia |
|---|---|---|---|
| **gránulo** | nada. Entra «ZI_M13: resampled VIIRS M13 spectral radiance» (README.txt:39) de 67 × 67 con un `BOX` del mismo tamaño; «The code intentionally excludes [...] file-system logic, volcano databases [...] geolocation diagnostics» (README.txt:9). La única decisión de escena es H:163-167 (≥ mitad NaN → vacío) | procesamos **todos** los gránulos que cubren la caja (`run_pipeline.py:316-335` itera cada L1B; `store.py:650` desdobla por `(datetime_utc, sensor)`, así que los dos miembros de una pasada partida se guardan) | la elección «sur» de MIROVA (526 de 537, verificador pareo_modis §2) ocurre **antes** del código publicado. **SOSPECHA** derivada: si la ventana de MIROVA se llena con NaN donde el gránulo no cubre, una pasada con menos de la mitad del ROI en el gránulo cae por H:163-167 y da alerta vacía y VRP NaN; como MIROVA igual lista una fila RUTINA en 24 de 129 casos de MODIS con menos del 20 % de nuestro anillo (`granulo_que_elige_mirova_salida.txt`), la fila se escribe aunque el detector no haya corrido hasta el final. Lo cierra un TIF de una pasada partida |
| **día** | rama completa: `dayflag ~= 0` → K1 −0,5, 15σ, mínimos 0,02 (H:188-199); sun-glint < 12° rechaza la escena (H:87-89); el ángulo se arma en `run_example.m:15-20` con cenit y azimut solar y de sensor | rechazamos el diurno (`store.py:203-224`); la rama D-10 lleva K1 −0,6 y **no** calcula sun-glint; los ángulos ya se leen (pvm:338-348) | el día que D-10 se encienda, faltan dos piezas del código: K1 −0,5 y el rechazo por glint. Sin la segunda, un reflejo especular sobre nube entra al detector con K1 relajado |
| **saturación** | nada. «Quality screening [...] remain the responsibility of the user» (README.txt:92) | bit 2 de `quality_flags` y techos 634 K (M13) y 343 K (M15) → NaN (pvm:182-194, 252, 285); MODIS: todo DN > 32767 → NaN (`process_modis.py:252-258`) | en el código un píxel saturado entra con su radiancia tope (si la L1B lo entrega así); en el nuestro es un hueco. Sin sustrato en Chile hoy (F1 H8); D24 en MODIS |
| **nube** | sólo el filtro de M15 ≤ 200 K (H:147-154); «cloud assessment [...] responsibility of the user» (README.txt:92) | ninguna máscara activa (`CLOUD_MASK_BT_K = 0.0`, YAML:53); tampoco el filtro de 200 K | IGUAL en que ninguno de los dos enmascara nube; DISTINTO en el filtro de 200 K (sustrato 0 en las 190 escenas chilenas de O1) |

## 4. Pasos DISTINTOS sin A/B ni frente, por cuánto podrían mover publicaciones (protegidas primero)

| orden | paso | por qué puede mover publicaciones | sustrato medido | gravedad |
|---|---|---|---|---|
| 1 | **sun-glint** (fila 3) | sólo de día. F1 H2 contó 3 alertas **protegidas** diurnas de Chillán en K que MIROVA publicó y nosotros rechazamos; cuando D-10 abra el día, el código de MIROVA rechaza la escena entera bajo 12° y nosotros no tendríamos ese freno | 0 de 190 escenas chilenas (todas nocturnas: `dayflag≠0` = 0); 27 de 600 sintéticas lo disparan (control positivo) | 2 hoy (latente), 3 si se enciende D-10 sin él |
| 2 | **segundo pase condicionado**, cara (b) adyacencia (fila 30) | no es divergencia nueva: es una **decisión pendiente (D19 D1/D2)** que el código contesta. El `.m` no restringe a adyacentes y corre siempre; con el primero vacío no agrega. Adoptar (b) alejaría de MIROVA; lo que acerca es quitar lo que hace distinto al segundo pase (D22, D26) | F1 H5: 19 de 67 publicados en K vienen sólo del segundo pase | informa D19; no es acción propia |
| 3 | **píxel frío ≤ 200 K + escena ≥ mitad NaN** (filas 9 y 11) | sólo puede **quitar** publicaciones nuestras en escenas muy incompletas; ninguna protegida | 0 de 190 chilenas en los dos; F1 H8 proxy 0 de 64 publicadas en K | 1 |
| 4 | **dETI < −0,1 fuera del pool** (fila 19) | cambia σ del dETI; con `max` el umbral fuera es el piso 0,01 en 167 de 190 chilenas, así que σ decide en ≤ 23 de 190 | medido acá (pase 1 del oráculo, que ya no saca el dETI) | 1 |
| 5 | **marco de la ventana** (fila 5) | un píxel en el borde de los 51 km es detectable aquí y no allá; sólo `far` | no medido (el borde de nuestra caja no se persiste como tal) | 1 |
| 6 | **N contra N − 1** en σ (fila 20) | con ~4.400 píxeles cambia σ en 0,01 % | no hace falta | 0 |

No hay ningún paso DISTINTO sin frente que pueda mover una publicación protegida **de noche**: los que pueden (fondo
del VRP, suma de todas las alertas, K1, mínimo de dNTI fuera, caja de cumbre, regresión y segundo pase) ya están en
D25, D32, D34, D18, D29, D26 y en los frentes N, F1, F4, GEO.

## 5. OSF: novedades desde julio

Consultado el 2026-10-21 por la API pública, sin sesión (`https://api.osf.io/v2/nodes/zm62w/logs/`, 340 entradas;
`.../files/osfstorage/` y la carpeta `6a6329390399ee013b6b824a`):

| fecha (UTC) | acción | qué |
|---|---|---|
| 2026-07-24 08:58-08:59 | `osf_storage_file_added` ×6 | los cinco archivos del código y el ejemplo |
| 2026-07-24 09:19-09:20 | `addon_file_renamed` ×2 | «MIROVA Dataset v1» → «MIROVA Dataset v1.0»; «MIROVA Database v2.5» → «MIROVA Dataset v2.5» |
| 2026-08-16 10:09-10:10 | `addon_file_renamed` ×2 | → «MIROVA Dataset v1.0 [MODIS 2000-2020]» y «MIROVA Dataset v2.5 [MODIS+VIIRS 2000-2025]» |
| 2026-08-19 08:05 | `custom_citation_edited` ×2 | cita del proyecto |

Los `.m`, README, LICENSE y CITATION siguen en `current_version 1` (2026-07-24). **No hay código nuevo, ni otro sensor,
ni otra versión.** `scripts/vigilar_osf_mirova.py` (lectura, contra `scripts/osf_mirova_linea_base.json`): «sin
novedades en 7 proyectos OSF del grupo MIROVA». Enlace: https://osf.io/zm62w/ (DOI 10.17605/OSF.IO/ZM62W).

## 6. Hallazgos con formato, de mayor a menor gravedad

### H1. La rama diurna D-10 no tiene el rechazo por sun-glint que el código de MIROVA aplica antes de todo
- ARCHIVO:LÍNEA: H:35-36 («All detections are rejected when this angle is smaller than 12 degrees»), H:87-89;
  `run_example.m:15-20` (fórmula). Nuestro: `pipeline/diurno.py:121-148` (umbrales diurnos, sin glint);
  `grep -ri glint pipeline/ scripts/` = 0 (`pasos_del_m_salida.txt` A).
- QUÉ PASA: de día el sol puede reflejarse de forma especular en una nube o un lago hacia el sensor; el MIR se
  enciende sin que nada esté caliente. MIROVA tira la escena entera si la geometría sol-sensor queda a menos de 12°
  del reflejo. Nuestra rama diurna (apagada) sólo cambia umbrales.
- CÓMO SE VE EN EL DASHBOARD: invisible hoy (día rechazado). Con D-10 encendido: una alerta diurna de VRP alto sobre
  nube, de la clase que A76 ya vio en Láscar (760 MW).
- CÓMO REPRODUCIRLO: encender `enable_daytime_viirs` en un perfil A/B y buscar pasadas diurnas con cenit solar bajo
  sobre nube; la geometría necesaria ya está en el record (`angles`, pvm:338-348).
- CONFIANZA: CONFIRMADO que falta; SOSPECHA el efecto (sin pasada diurna medida).
- GRAVEDAD: 2 (3 si se enciende D-10 sin él).

### H2. El segundo pase del código no está condicionado ni restringido a adyacentes; la decisión D19 D1/D2 debe saberlo
- ARCHIVO:LÍNEA: H:228-235 (misma función, mismas máscaras, sin condición); dc:906-907 y dc:964-965
  (`conditioned`, caras (a) y (b)); YAML:440 `enable_second_pass_conditioned: false`.
- QUÉ PASA: en el código, con pase 1 vacío y sin absolutos el pase 2 es el mismo cálculo y no agrega; lo que lo hace
  distinto en el nuestro es que el segundo pase no lleva la compuerta de 3 K (dc:958 no la aplica), no saca los no
  aptos (dc:923) y reusa la regresión (pvm:916). La cara (b) «adyacentes» del flag no existe en MIROVA.
- CÓMO SE VE EN EL DASHBOARD: F1 H5: 19 de 67 publicados en K vienen sólo del segundo pase.
- CÓMO REPRODUCIRLO: leer H:228-235 contra dc:822-967; `experiments/_s158_audit/f1/primer_pase_vacio.py`.
- CONFIANZA: CONFIRMADO (leído).
- GRAVEDAD: 2 (es información para una decisión pendiente, no un defecto nuevo).

### H3. El regex de «VRP NaN sin alerta» de mi script A dio 2 falsos positivos (`np.nansum`); el dato correcto es `vrp_mw = 0.0`
- SCRIPT:SALIDA: `pasos_del_m_salida.txt` A, fila «V VRP NaN sin alerta» (pvm:1058, `process_modis.py:1120` son
  `np.nansum`). Lo real: pvm:1027 `vrp_mw = 0.0` por defecto; V:45-52 NaN.
- CONFIANZA: CONFIRMADO (lo leí). GRAVEDAD: 0 (del instrumento, se anota para que nadie lo herede).

### H4. Píxel frío y escena incompleta: el código los filtra, nosotros no, y en Chile no hay sustrato en esta batería
- ARCHIVO:LÍNEA: H:150-154, H:163-167; nuestro: pvm:566 (≥ 10 píxeles en el anillo), dc:432 (≥ 10 en el pool).
- SCRIPT:SALIDA: `pasos_del_m_salida.txt` B: 0 de 190 escenas chilenas con M15 ≤ 200 K, 0 rechazadas por ≥ mitad
  NaN; sintéticas 66 y 25 de 600 (el instrumento las ve). Denominador: las 791 escenas de O1 (Etna 2023-05-19;
  chilenas 2026-03-01 a 2026-10-16, 10 pasadas × 19 variantes; 600 sintéticas).
- CÓMO SE VE EN EL DASHBOARD: invisible hoy.
- CONFIANZA: CONFIRMADO en esta batería; SOSPECHA fuera de ella (190 escenas de 10 pasadas no son el corpus).
- GRAVEDAD: 1.

### H5. El umbral de dNTI fuera de la cumbre es el piso de MIROVA (0,02) en 171 de 190 escenas chilenas; el de la cumbre nunca es el piso
- SCRIPT:SALIDA: `pasos_del_m_salida.txt` B, filas «pase1: umbral …». Positivo de instrumento: Etna reproduce el OSF.
- QUÉ PASA: fuera de la cumbre decide el mínimo fijo (0,02 contra nuestro 0,010 con las mismas unidades salvo el 8/9
  del kernel); en la cumbre decide siempre 5σ, el 0,003 es inerte. Reproduce F1 H4 y F4 H3 con otro instrumento (el
  oráculo con diagnóstico, no el corpus).
- CONFIANZA: CONFIRMADO. GRAVEDAD: informativo (el frente ya existe: D34, F1 H4).

## 7. VERIFICADO LIMPIO

| qué | cómo se confirmó |
|---|---|
| Copias locales de los `.m`, README y CITATION = OSF, byte a byte salvo CRLF | `tr -d '\r' \| md5sum` = md5 de la API (5ef30868…, 2e95d1d3…, 154c6a22…, 7484c4c3…); `current_version 1` |
| OSF zm62w sin archivos nuevos ni versiones nuevas desde 2026-07-24 | log de 340 entradas (las 15 últimas listadas en §5) y listado de la carpeta de código; `vigilar_osf_mirova.py` en lectura |
| Coeficiente y área (fila 41), longitudes de onda (8), NTI (10), conectiva `max` (21), conjunción ∧ (28), «corre siempre y sobre toda la escena» del segundo pase (30), sin duplicados en la salida (31) | lectura H y pvm/dc en las líneas citadas; duplicados: 0 de 791 en `pasos_del_m_salida.txt` B |
| El instrumento B ve: Etna 5 alertas y Tot_Lmir_hot 1,965342180; sun-glint y escena incompleta disparan en sintéticas (27 y 25 de 600) | `pasos_del_m_salida.txt` cabecera y tabla |
| El instrumento A ve: `polyfit` 1 archivo (dc:719), token inventado 0 | ídem, bloque A |
| Con el perfil de producción el Test 1 integrado y la magnitud focal de V750 no corren | `ENABLE_TEST1_PATH = False` de `pipeline.profile`; el bloque pvm:1296-1375 cuelga de él |
| No hay ninguna selección de gránulo en `run_pipeline.py` ni en `fetch.py` más allá del bbox y del filtro nocturno | `run_pipeline.py:316-335` (itera todos), `fetch.py:751-753` (bbox), `fetch.py:997-1024` (noche) |

## 8. Candidatas para `docs/BEYOND_MIROVA_EXTENSIONS.md` §12

Van al perfil `experimental`, se miden contra OVDAS y SWIR, no contra MIROVA (A115, feedback S159):

1. **Procesar los dos gránulos de una pasada partida y quedarse con el que tiene el cráter** (hoy ya lo hacemos: fila
   «gránulo» §3): MIROVA lista casi siempre el sur y no ve el cráter si cae en el norte (0 alertas observadas contra
   28,7 esperadas, verificador pareo_modis §2). Es una ceguera de MIROVA que no tenemos; anotarla como extensión y
   medir cuántas noches de volcán salva por año.
2. **Rechazo por sun-glint también de noche con luna** (SOSPECHA, no está en ningún paper leído): el código sólo lo
   usa por la geometría solar; con la geometría lunar sería la misma fórmula. Primero medir si existe el fenómeno.
3. **VRP NaN distinto de 0 MW** (F1 H9): distinguir «nublado o sin cobertura» de «miró y no vio» en el record y en el
   tablero; MIROVA lo declara en el código (V:19-22) y nosotros no.
4. **Guardar el resultado de las compuertas de escena** (fracción de NaN, píxeles fríos, glint) como diagnóstico por
   pasada, aunque no se apliquen: hoy «no hay sustrato» se mide con proxies (F1 H8) porque no se persisten.

## 9. Reproducir

```
PYTHONIOENCODING=utf-8 python C:\vrp-trabajo\s159-pruebas\experiments\_s159\osf_codigo\pasos_del_m.py
PYTHONIOENCODING=utf-8 python C:\vrp-trabajo\s159-pruebas\scripts\vigilar_osf_mirova.py
curl -s "https://api.osf.io/v2/nodes/zm62w/logs/?page%5Bsize%5D=15"
cd C:\vrp-trabajo\s159-pruebas\experiments\_s158_d17_diseno\osf_codigo_mirova && cat -n MIROVA_VIIRS750_hotspot_detection.m
```

## 10. Lo que no pude medir

- El efecto de cada paso sobre publicaciones de Chile: esta carpeta no corre el corpus; los números de efecto citados
  son de F1, F4 y N. Lo mío es cobertura (tabla) y sustrato de compuertas sobre las 791 escenas de O1.
- Si MIROVA rellena con NaN la parte de la ventana que el gránulo no cubre (clave para la SOSPECHA del §3): pide un
  TIF o una imagen de MIROVA de una pasada partida.
- `fillmissing2` real (O2 pendiente en MATLAB Online).
