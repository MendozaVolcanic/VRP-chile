# F2 · Dónde pone MIROVA su cúmulo, en la misma pasada

**Veredicto en una línea: MIROVA no integra la celda del cráter mejor que nosotros. En las
pasadas donde los dos sistemas ven el volcán, los dos cúmulos caen en el mismo lugar —
separación mediana 0,21 km, menos que la celda de 0,375 km en que MIROVA informa. El anillo
de 2,3-2,8 km de S133 vive entero en las pasadas que MIROVA *no* confirma.**

Ventana de todo el documento: ALERTAS MIROVA VIIRS375 desde **2026-06-01** hasta **2026-09-05**,
emparejadas a la misma pasada con tolerancia **≤120 s**. **n = 223 pasadas** en 10 de los 11
Tier A (Llaima: cero ALERTAS V375 en la ventana). Ancla: `vent_lat/vent_lon` de `volcanoes.yaml`
salvo donde se dice lo contrario (A13). Fuente: 222 CONS + 1 OCR; las 223 con `dist_km`.
El GeoTIFF se usó **sólo para posición, nunca para magnitud** (A24).

Scripts (todos read-only, en `experiments/_s134_audit/f2/`): `00_verificar_indice.py`,
`01_desacuerdo_ts.py`, `02_emparejar.py`, `03_control_instrumento.py`,
`f2_tif_misma_pasada.py`, `05_analisis.py`, `06_control_condicionamiento.py`,
`07_pareado_y_negativo.py`, `08_reanclar.py`, `09_cierre.py`. Datos: `resultados.json`
(223 filas), `control_instrumento.json`, `control_condicionamiento.json`, `cola_validacion.json`.

---

## 1. Control del instrumento — PASA, y sólo donde se lo controló

**El fenómeno.** El TIF que publica MIROVA trae una sola banda, el infrarrojo medio crudo. En
un volcán nevado de altura ese campo lo manda el gradiente de temperatura con la altitud, no el
foco volcánico (A69). Por eso S131 lo refutó como árbitro de posición: buscando el máximo en
**todo** el radio de 25 km, el error mediano contra `Distancia_km` fue 4,80 km. La pregunta de
acá es más modesta y por eso tiene respuesta: restringido al `inner_radius`, donde ya no hay
salar que compita, ¿el máximo cae en el cráter?

Láscar, 5 pasadas más recientes con ALERTA (`03_control_instrumento.py`), inner = 5 km:

| pasada UTC | d(máx TIF dentro del inner → cráter) | control neg.: d(máx en 25 km) | MIROVA `Distancia_km` |
|---|---|---|---|
| 2026-08-20 06:00:01 | **0,128 km** | 23,00 km | 1,13 |
| 2026-08-09 06:06:01 | **0,273 km** | 23,00 km | 1,13 |
| 2026-08-09 05:48:00 | **0,128 km** | 23,31 km | 1,13 |
| 2026-08-07 06:30:00 | **0,128 km** | 23,31 km | 1,13 |
| 2026-08-07 05:54:02 | **0,128 km** | 23,38 km | 1,13 |

**5 de 5 a < 1 km** (criterio: ≥ 4 de 5) → **PASA**. El control negativo del radio completo da
**0 de 5**, reproduciendo a S131 en su propio terreno: el máximo sin restringir se va a 23 km,
al salar. Las dos mediciones son la misma sobre el mismo archivo; lo único que cambia es el
espacio de búsqueda. Por azar puro el criterio daría ~4 % (π·1²/π·5²).

**Control de georreferencia** (independiente del veredicto): CRS `EPSG:4326`, 134×134 celdas,
celda **0,375 × 0,374 km**, extensión **50,3 × 50,1 km**, semidiagonal 36,08 km contra los
36,06 km que exige una grilla de 51×51 km. Confirma `half_km = 25,5` de S131.

**Control negativo de clase** (`07_pareado_y_negativo.py`) — el que decide si el acierto es
vacuo. Si dentro del inner el cráter fuera *siempre* la roca más tibia, «el máximo cae en el
cráter» no diría nada sobre la anomalía. Medido sobre pasadas con TIF y **sin** ALERTA:

| volcán | ALERTA: d mediana / <1 km | RUTINA: d mediana / <1 km |
|---|---|---|
| Láscar (inner 5 km) | 0,27 km · **82 %** (n=45) | 4,78 km · **9 %** (n=23) |
| Planchón-Peteroa (inner 3 km) | 0,60 km · **80 %** (n=20) | 2,85 km · **8 %** (n=25) |

El instrumento **separa clases**: no está midiendo topografía, está viendo la anomalía.

**El límite, dicho sin adornos.** El control se corrió en Láscar y se corroboró en PP: dos
volcanes de foco fuerte con inner chico (5 y 3 km). Donde el inner es grande o el terreno es
nevado, el máximo del TIF vuelve a ser el artefacto A69 — PCC 16,5 km (inner 20), Tupungatito
6,7 (inner 7), Isluga 4,65, Villarrica 4,71. **El TIF no es árbitro general de posición**, y la
conclusión de §3 no se apoya en él sino en el auto-reporte de MIROVA.

---

## 2. HALLAZGO 1 — El anillo de S133 es un efecto del denominador, no de la detección

**SCRIPT:SALIDA** — `experiments/_s134_audit/f2/06_control_condicionamiento.py`
→ `control_condicionamiento.json`; contra `docs/s133/ANILLO_TIER_A.md`.

**QUÉ PASA.** S133 midió la distancia de nuestro cúmulo al cráter sobre **todos** los records
publicados (magnitud > 0, clase *summit*) y encontró 2,3-2,8 km en 9 de 11. Yo mido lo mismo
sobre el subconjunto en que **MIROVA además declaró ALERTA**. No son la misma población: las
pasadas con ALERTA son aquellas donde había señal suficiente para que dos sistemas
independientes la vieran. El anillo se desarma al condicionar.

Mi réplica de la columna S133 reproduce la tabla publicada con **error mediano 0,00 km sobre los
11 volcanes** — o sea el instrumento está verificado contra el número que quiere comparar:

| volcán | S133, todos los records | sólo con ALERTA MIROVA | desplazamiento |
|---|---|---|---|
| Villarrica | 2,79 (n=289) | **0,19** (n=3) | −2,60 |
| Chaitén | 2,49 (n=323) | **0,18** (n=9) | −2,31 |
| Nevados de Chillán | 2,61 (n=189) | **0,33** (n=1) | −2,28 |
| Planchón-Peteroa | 2,45 (n=251) | **0,36** (n=20) | −2,09 |
| Tupungatito | 2,27 (n=223) | **0,25** (n=22) | −2,02 |
| Copahue | 2,80 (n=305) | **1,56** (n=1) | −1,24 |
| Puyehue-C. Caulle | 1,04 (n=314) | **0,23** (n=32) | −0,81 |
| Isluga | 0,96 (n=314) | 0,85 (n=51) | −0,11 |
| Lastarria | 2,28 (n=147) | 2,20 (n=36) | −0,08 |
| Láscar | 0,23 (n=209) | 0,16 (n=45) | −0,07 |
| Llaima | 2,84 (n=277) | SIN DATO (n=0) | — |

Mediana del desplazamiento: **−1,63 km** (n=10 volcanes).

**El control interno que lo vuelve creíble**: los tres volcanes donde S133 dijo que la posición
es *genuina* — Láscar y Isluga (foco fuerte y aislado) y Lastarria (campo fumarólico Lazufre,
dato de campo, A84) — **no se mueven** (−0,07, −0,11, −0,08). La medición no fabrica separación
donde no la hay. Se mueven exactamente los nevados de señal débil, que es donde A69 predice el
artefacto topográfico.

**Lectura física.** El anillo no es «el pipeline integra el flanco». Es que en las pasadas
**sin** confirmación de MIROVA lo que publicamos es señal sub-umbral (cat-b, A54) o el
gradiente cráter-nieve (A69), y *eso* es lo que se sienta a 2,5 km. En las pasadas donde hay
lava resoluble, el cúmulo va al cráter.

**CÓMO SE VE EN EL DASHBOARD.** Visible, y engañoso en el sentido opuesto al que se creía: el
mapa acumula todas las pasadas juntas, así que el operador ve una nube de puntos a ~2,5 km del
cráter dominada por las pasadas débiles, y no puede distinguir las que MIROVA confirmó (que sí
están en el cráter) de las que no.

**CÓMO REPRODUCIRLO** — `cd experiments/_s134_audit/f2 && python 06_control_condicionamiento.py`

**CONFIANZA: CONFIRMADO** (medido; réplica verificada contra la tabla publicada a 0,00 km).
**GRAVEDAD: 4** — no tuerce una alerta por sí solo, pero invalida la hipótesis que S134 iba a
usar para explicar el déficit de magnitud, y ese sí es el eje de una decisión.

---

## 3. HALLAZGO 2 — MIROVA y nosotros ponemos el cúmulo en el mismo lugar (y el «se corre» era el ancla)

**SCRIPT:SALIDA** — `08_reanclar.py`.

**QUÉ PASA.** MIROVA no mide su `Distancia_km` desde nuestro `vent_lat/lon`: la mide desde el
centro de **su** grilla, que en algunos volcanes está lejísimos del cráter — PCC **7,57 km**,
Tupungatito **4,86 km**, PP 2,02 km. Comparar su número contra el nuestro sin re-anclar es
comparar dos reglas con cero distinto (S115, A13, D15).

**Yo mismo caí en la trampa a mitad de camino**: `07_pareado_y_negativo.py` daba «MIROVA declara
su punto más lejos del cráter que el nuestro en el 77 % de 220 pasadas», con PCC +7,68 km y
Tupungatito +4,80 km. **Ese resultado es artefacto del ancla y queda retractado.** Re-anclando
nuestro centroide al centro de la grilla de MIROVA:

| volcán | n | nuestro cúmulo @ centro MIROVA | MIROVA declara | delta |
|---|---|---|---|---|
| Puyehue-C. Caulle | 32 | 7,65 | 7,96 | +0,29 |
| Tupungatito | 22 | 4,98 | 5,21 | +0,12 |
| Lastarria | 36 | 2,15 | 2,40 | +0,19 |
| Planchón-Peteroa | 20 | 2,14 | 2,02 | −0,16 |
| Copahue | 1 | 1,68 | 2,12 | +0,44 |
| Láscar | 45 | 0,92 | 1,50 | +0,52 |
| Isluga | 51 | 0,49 | 0,53 | +0,18 |
| Villarrica | 3 | 0,48 | 0,84 | +0,36 |
| Chaitén | 9 | 0,25 | 0,38 | +0,20 |
| Nevados de Chillán | 1 | 0,16 | 0,00 | −0,16 |
| **GLOBAL** | **220** | **1,19** | **1,55** | **+0,21** |

**La separación mediana es 0,21 km — menor que la celda de 0,375 km en la que MIROVA informa.**
Las dos posiciones son indistinguibles a la resolución del propio ground truth. Los «8 km» de
PCC y los «5 km» de Tupungatito eran el offset del ancla, no un desacuerdo.

**Respuesta a la pregunta del frente**: en las pasadas que ambos ven, **MIROVA integra el cráter
tanto como nosotros, ni más ni menos**. La premisa de que ella integra la celda del cráter y
nosotros el flanco **queda refutada**, y con ella la explicación candidata de S133 para el
déficit de magnitud — porque la paridad se mide justamente sobre estas pasadas comunes. El
déficit habrá que buscarlo en otra parte: no viene de estar mirando dos objetos distintos.

**CÓMO SE VE EN EL DASHBOARD.** Invisible. Es una comparación de auditoría.

**CÓMO REPRODUCIRLO** — `cd experiments/_s134_audit/f2 && python 08_reanclar.py`

**CONFIANZA: CONFIRMADO.** **GRAVEDAD: 4** — cierra un eje de S134 (`anillo`) por refutación.

---

## 4. HALLAZGO 3 — El índice del archivo tiene dos relojes que discrepan 1-2 h en el 14 %

**SCRIPT:SALIDA** — `00_verificar_indice.py`, `01_desacuerdo_ts.py`.

**QUÉ PASA.** En `index.csv` (18.885 filas) el timestamp de la pasada está en dos lugares: el
nombre del archivo y `acquisition_utc`. `acquisition_utc` está **vacío en 3.324 filas (17,6 %)**,
y de las 15.561 que tienen ambos, **el 14,2 % discrepa más de 60 s**, típicamente 1-2 h (máximo
20,7 h) — o sea otra órbita, otro gránulo. Ejemplo: `20260509_054202_VIIRS375.tif` declara
`acquisition_utc = 2026-05-09T06:36:01`, y el mismo nombre aparece para Tupungatito y Chaitén.

**Por qué importa**: un emparejamiento a ±20 min sobre el reloj equivocado toma el TIF de otra
pasada, y toda comparación posterior es ruido. Peor: SNPP y NOAA-20/21 se separan ~18-50 min, o
sea dentro de la tolerancia — medido, el 27 % de los emparejamientos a ±20 min tienen desfase de
540-1081 s y son casi seguro **el otro satélite**. Mitigación aplicada en F2: usar sólo filas
donde los dos relojes coinciden (13.351 de 18.885) y exigir ≤120 s. Con eso el desfase mediano
TIF↔ALERTA es **0 s** y el de record↔ALERTA **1 s** (n=223).

**CÓMO SE VE EN EL DASHBOARD.** Invisible — afecta a auditorías, no a producción.

**CÓMO REPRODUCIRLO** — `python 00_verificar_indice.py && python 01_desacuerdo_ts.py`

**CONFIANZA: CONFIRMADO.** **GRAVEDAD: 2** — no toca la alerta; sí puede torcer cualquier
auditoría futura que use el archivo sin este cuidado. Vale como nota de método para S135+.

---

## 5. HALLAZGO 4 — `anomaly_pixels` persistido no es el conjunto de píxeles anómalos

**SCRIPT:SALIDA** — `05_analisis.py`, bloque final.

**QUÉ PASA.** En las 223 pasadas, la mediana de `anomaly_pixels` persistidos es **1** mientras
`n_anomalous_pixels` tiene mediana **2**. El array guardado está recortado respecto del contador.
No lo investigué más allá de constatarlo; puede ser deliberado (recorte al núcleo) o una pérdida.
Afecta a cualquier auditoría que reconstruya la geometría del cúmulo desde `anomaly_pixels`: acá
`d_pico_nuestro` se calculó sobre lo persistido y por eso puede no ser el píxel de máximo real.

**CÓMO SE VE EN EL DASHBOARD.** SOSPECHA de invisible; no verifiqué qué consume el frontend.

**CÓMO REPRODUCIRLO** — `python 05_analisis.py` (última línea del bloque de controles).

**CONFIANZA: CONFIRMADO** el desajuste de conteos; **SOSPECHA** su causa e impacto.
**GRAVEDAD: 2**.

---

## 6. HALLAZGO 5 — Llaima: cero ALERTAS VIIRS375 de MIROVA en tres meses, y 277 records nuestros

**SCRIPT:SALIDA** — `02_emparejar.py`, `06_control_condicionamiento.py`.

**QUÉ PASA.** Entre 2026-06-01 y 2026-09-05 MIROVA no publicó **ninguna** ALERTA VIIRS375 de
Llaima, mientras nosotros publicamos **277 records** *summit* con magnitud > 0, cuyo cúmulo se
sienta a 2,84 km del cráter — el peor anillo de los 11. Por el hallazgo 1, ese es exactamente el
perfil de la población no confirmada: nevado de señal débil, sin contraparte. Villarrica (3
ALERTAS contra 289 records), Copahue (1 contra 305) y NdC (1 contra 189) están en el mismo caso.

Esto **no prueba** que sean falsos positivos — A54 dice que ~95 % de ese excedente es actividad
térmica físicamente real que MIROVA no publica, y A77 recuerda que a 375 m el instrumento puede
ser el equivocado. Pero sí dice que para esos cuatro volcanes **no hay ground truth espacial
contemporáneo**, y que cualquier verdicto de posición sobre ellos se apoya en n = 0-3.

**CÓMO SE VE EN EL DASHBOARD.** Visible: el operador ve serie térmica continua en Llaima sin
ninguna forma de saber que MIROVA lleva tres meses sin confirmar una sola pasada.

**CÓMO REPRODUCIRLO** — `python 02_emparejar.py`

**CONFIANZA: CONFIRMADO** el conteo. **GRAVEDAD: 3** — es información que cambia cómo se lee la
serie de cuatro volcanes, y hoy no está en ninguna parte de la vista.

---

## 7. Cola de validación en campo (para Nicolás)

Dashboard: `https://mendozavolcanic.github.io/VRP-chile/?volcano=<Volcan>` — parámetro `volcano`
verificado en `frontend/index.html:869` y `:3915`, URL base en `README.md:13`.
mirovaweb: `https://www.mirovaweb.it/NRT/volcanoMap.php?volcano=<Volcan>&sensor=VIIRS375` —
patrón verificado en `scripts/generate_villarrica_pruebas.py`. **Advertencia**: ese patrón sirve
la vista *actual* del volcán, **no** una pasada histórica; no encontré en `docs/` ni en `scripts/`
ningún patrón de URL que permita pedir una pasada por fecha. Para la pasada concreta, el
sustituto verificable es el TIF ya descargado en `experiments/_s134_audit/tif/`.

| ID | pasada UTC | volcán | qué mirar | qué decide |
|---|---|---|---|---|
| F2-1 | 2026-08-21 06:36:02 | Puyehue-C. Caulle | nuestro 0,08 km del cráter; MIROVA declara 8,19 km **desde su centro de grilla, que está a 7,57 km del cráter** | confirma que el «8 km» es el ancla y no un desacuerdo — el caso más extremo del hallazgo 2 |
| F2-2 | 2026-08-21 06:30:02 | Tupungatito | nuestro 2,89 km; MIROVA 5,21 km; offset de ancla 4,86 km | idem, en el segundo volcán con ancla corrida |
| F2-3 | 2026-08-20 06:00:01 | Láscar | máximo del TIF a 0,128 km y nuestro cúmulo a 0,14 km, los dos en el cráter | control positivo: los tres puntos coinciden cuando el foco es fuerte |
| F2-4 | 2026-08-09 05:54:00 | Planchón-Peteroa | nuestro 0,47 km; TIF 0,60 km; MIROVA declara 2,02 km con ancla a 2,02 km | volcán multi-cráter (A22): ver si el cúmulo cae en Peteroa |
| F2-5 | 2026-07-20 05:48:01 | Villarrica | nuestro 0,15 km del cráter, pero el máximo del TIF a 4,71 km | una de sólo 3 pasadas confirmadas en 3 meses; y el caso donde el TIF falla como árbitro |
| F2-6 | 2026-08-20 06:00:01 | Isluga | nuestro 0,86 km; MIROVA 0,53 km — **el único volcán donde MIROVA está sistemáticamente más cerca** (86 % de 51 pasadas) | si hay un offset real nuestro, Isluga es donde buscarlo |

---

## 8. VERIFICADO LIMPIO

Lo que miré y está sano — para que la auditoría 35 no lo vuelva a recorrer:

| qué | cómo lo confirmé | resultado |
|---|---|---|
| Emparejamiento TIF ↔ ALERTA ↔ record nuestro | `02_emparejar.py` | desfase mediano **0 s** y **1 s** (n=223); 100 % de los records a ≤2 s |
| Georreferencia de los GeoTIFF | `03_control_instrumento.py` + `09_cierre.py` | `EPSG:4326`, 134×134, celda 0,375 km, extensión 50,3 km, semidiagonal 36,08 vs 36,06 teórico. Confirma `half_km=25,5` de S131 |
| Alias de nombres del archivo | `00_verificar_indice.py` | exactamente 11 volcanes; único alias `ChillanNevadosde` → `NevadosDeChillan`. Ningún otro |
| Nocturnidad de la muestra | `05_analisis.py` | `solar_zenith_deg` presente en **223/223**, mínimo 143,4° → todas nocturnas. Sin diurnas que activen A76 |
| Descarga y lectura de los 223 TIF | `f2_tif_misma_pasada.py` | **0 errores**; `celdas_en_inner` mediana 555, mínimo 200 (ninguna medición vacua) |
| `pipeline/mirova_csv_loader.py::load_mirova_alertas` | firma leída en `pipeline/mirova_csv_loader.py:123-143` | la firma del brief es correcta; el `dist_km=0` del OCR se trata como «no informado», no como cero — sin matches espurios al vent |
| Réplica de la tabla de S133 | `06_control_condicionamiento.py` | error mediano **0,00 km** sobre los 11 volcanes contra `docs/s133/ANILLO_TIER_A.md` |
| El GeoTIFF **no** es árbitro general de posición (S131) | `05_analisis.py` tabla 1 + control negativo de 25 km | **confirmado, no refutado**: el máximo del TIF falla donde el inner es grande o el terreno nevado (PCC 16,5 km, Tupungatito 6,7, Villarrica 4,71). S131 sigue en pie; lo que agrego es que **restringido a un inner chico y terreno seco sí funciona** (Láscar 5/5, PP 80 %), con control negativo ALERTA-vs-RUTINA que lo separa de la topografía |
| `radius_km=25` e `inner_radius_km` por volcán | `volcanoes.yaml` vía `08_reanclar.py` | coinciden con la tabla de CLAUDE.md: inner 3 (Lastarria, PP), 4 (Copahue), 5 (Láscar, Isluga, NdC, Llaima, Villarrica, Chaitén), 7 (Tupungatito), 20 (PCC) |

**Lo que NO miré** (para que nadie lo dé por cubierto): MODIS y VIIRS750 — todo F2 es VIIRS375.
Magnitud — el TIF no sirve para eso (A24) y no la toqué. La causa del déficit de paridad: F2 sólo
**descarta** una explicación candidata, no propone otra. Y el impacto real del hallazgo 4
(`anomaly_pixels` recortado) sobre el frontend.

**Ningún archivo del repositorio fue modificado.** Todo vive en `experiments/_s134_audit/`.
