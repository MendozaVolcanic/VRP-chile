# S136 — auditoría del probe, dos caminos descartados, y el frente que queda

> Sesión de continuación. El probe (run 34274884640) terminó verde y su veredicto impreso dice
> **A — el filtro quedó sin función**. **Ese veredicto no se sostiene**, por dos defectos del
> instrumento que se documentan acá; aplicado como está escrito, el criterio pre-registrado da
> **C — indeterminado**. Además se descartaron dos caminos con medición, y la investigación
> documental reencuadró el problema: el frente no está en el Test 1 sino en los tests
> contextuales.

## 1. El control de validez del probe estaba mal construido (falso negativo)

El probe reportó **0 de 15 pasadas reproducen** la producción, y su propio texto concluyó que por
eso «ningún otro número del run es interpretable». Pero comparaba contra
`data/mirova_equivalent/`, que para pasadas de junio y julio fue escrito por el **código de
entonces** — régimen previo a `#535`, con la máscara de nube encendida y el fondo global 6-8 K más
alto en nevados. El probe corre con el código de hoy: **no podía reproducir por construcción**.

El término de comparación correcto existía: el brazo control del A/B de S135 reprocesó **esos
mismos granules con código post-`#535`**. Rehecho contra esa referencia:

| control de validez, pareo por volcán + minuto + **sensor** | resultado |
|---|---|
| probe contra **reproceso con el mismo código** (brazo control del A/B de S135) | **16 / 16, exacto** |
| probe contra producción (código de cuando se escribió el record) | 10 / 20 |
| **producción contra reproceso, MISMO granule, código distinto** | **IGUAL 7 · DIFIEREN 9** |

La tercera fila cierra el caso: **producción y reproceso difieren entre sí en 9 de 16 pasadas
sobre el mismo granule**, y esas 9 son las que hacen fallar el control. El probe no se aparta de
la producción por un defecto propio, sino porque **la producción de junio-julio la escribió otro
código**. Las 4 pasadas sin referencia son de Villarrica, que no está entre los 6 volcanes del
A/B. Script: `scratchpad/auditar_probe.py` §2.

Esto **descarta las tres sospechas** que quedaron anotadas en `RESULTADO_PROBE.md` (#611), sin
necesidad de investigarlas: (1) el A/B fue un reproceso real por `run_pipeline`, así que **pasó
por `store.py`**, y el probe le coincide exacto — si `store.py` alterara la magnitud, no podría;
(2) dieciséis coincidencias al cuarto decimal no ocurren con granules distintos; (3) Lastarria
07-24 coincide exacto, así que no es el comparador cayendo a otra cantidad.

> **Error propio, corregido antes de reportar.** La primera versión de esta tabla hacía *fallback*
> silencioso a producción cuando un volcán no estaba en el A/B. Villarrica no está entre los 6, así
> que sus 4 pasadas se comparaban contra sí mismas y daban «IGUAL» trivial: habría reportado 20/20
> en lugar de 16/16. Quinto error de instrumento de la sesión, misma familia A93, y lo delató que
> Villarrica no podía tener referencia.

Lección, de la familia A87/A90: **un control de reproducibilidad debe comparar contra datos del
mismo régimen de código**, no contra lo persistido. La fecha del granule no fija el régimen; lo
fija el código que lo procesó. El propio pre-registro lo dice para elegir las pasadas, y el
control cayó en lo contrario.

## 2. El desenlace se calculó sin verificar que hubiera sustrato (falso «A»)

El filtro contextual sólo corre si el hotspot final **viene del camino Test 1**
(`process_viirs.py:1779`, `final_hotspot_source == "test1"` en su valor *legacy*). Las 20 pasadas
se eligieron por `triggered_test1 == True`, que es otra cosa: **disparar el Test 1 no es ganar la
selección**. Si el camino contextual gana, el filtro no tiene sobre qué actuar.

Medido, comparando ACTUAL contra SIN_FILTRO pasada por pasada:

| | pasadas |
|---|---|
| el filtro cambia el `vrp_mir` interno del Test 1 | 9 / 20 |
| **el filtro cambia la magnitud PUBLICADA** (lo que mide el criterio) | **7 / 20** |
| de esas 7, **en nevados** | **3** |
| de esas 7, en el control no nevado | 4 |

El criterio pre-registrado dice **«C — indeterminado: menos de 4 pasadas útiles en los nevados»**.
Hay **3**. El desenlace correcto es **C**, no A. El `×1,07` que el script leyó como «el filtro no
mueve nada» resulta de promediar 13 pasadas de las que **10 no tienen sustrato**: la mediana no se
mueve porque en la mayoría el filtro nunca actuó.

Tercera aparición del mismo problema en el proyecto
(`feedback_s130_medir_el_sustrato_antes_del_ab`): la pregunta previa a «¿mejora algo?» es «¿llega
a ejecutarse?».

### Donde sí hay sustrato, el efecto es grande y va hacia MIROVA

En las 7 pasadas con sustrato la magnitud **sube siempre** al retirar la intersección, entre ×1,2
y ×4,3 (Lastarria 24-jul 0,042 → 0,183; Tupungatito 07-jul 0,070 → 0,153). Como el sistema
**sub-reporta** (paridad 0,708 en la ventana completa), la dirección es la correcta. Con n = 3 en
nevados no se concluye: es lo que el desenlace C ordena, ampliar la muestra.

## 3. Camino descartado — restaurar la unión de caminos de detección

El código construye la unión de todos los caminos (`combine_hot_paths`, que incluye el Test 1) y
**la descarta** una línea después: `hot_mask_2d = fp_hot` (`process_viirs.py:1255`,
`process_modis.py:884`, `process_viirs_mod.py:847`), sustituyéndola por sólo el primer pase de
Tests 2∧3. El comentario del propio código lo declara: «Paths legacy se calcularon arriba (diag)
pero no contribuyen cuando ON». El paper dice lo contrario, verificado verbatim: *"The total
active pixels (first and second runs) are shown in the alert mask"*
(`documentacion/sp426_5.txt:379-380`), y los píxeles del Test 1 quedan marcados como activos
(`:298-300`).

**Es una divergencia literal real, en los tres sensores.** Pero **no resuelve las 12 noches** que
perdía el brazo fiel de S135: medido sobre los 45 registros de esas noches, el término que
importaría de esa unión —el Test 1 del paper— vale **cero en todas**. Queda como divergencia a
documentar, no como solución.

## 4. Camino descartado — recalibrar K1 para VIIRS (por dos vías independientes)

**Vía empírica.** El Test 1 del paper dispara en **13 de 2.142 registros de VIIRS 375 m (0,61 %)**
en junio-agosto, con `nti_max` mediano de **−0,956** contra el umbral de −0,80. Medido por noche
sobre 279 noches con alerta de MIROVA y 273 sin alerta (`scratchpad/sustrato_k1.py`):

| K1 candidato | noches de MIROVA capturadas | noches sin alerta que entran |
|---|---|---|
| −0,80 (actual) | 4 / 279 — 1 % | 9 / 273 — 3 % |
| −0,95 | 224 / 279 — 80 % | 155 / 273 — **57 %** |
| −0,96 | 265 / 279 — 95 % | 205 / 273 — **75 %** |

**AUC del `nti_max` como discriminante: 0,614** (0,5 sería azar). No existe umbral con separación
útil, y la medición es **optimista**: `nti_max` se calcula sobre el mismo ROI donde el Test 1
evalúa (`process_viirs.py:846`), y el test real exige además `bt > t_bg + sanity`, así que dispara
en un subconjunto. Si el óptimo no separa, el real menos. Consistente con A80/A83.

**Vía documental, y es la que cierra el caso.** No existe umbral fijo de NTI para VIIRS en la
literatura MIROVA:

- **Campus et al. 2022** (*Sensors* 22:1713 — Torino, MIROVA legítimo) es el paper de la
  adaptación a VIIRS, y en detección **no adapta nada**: *"The hot-spot detection algorithm is the
  same used for MODIS"*, remitiendo a Coppola 2016a (`campus2022_extracted.txt:418-421`). Sus
  únicas modificaciones explícitas son geométricas y radiométricas.
- **Coppola 2024 Tabla 2**, la tabla de umbrales fijos por sensor del grupo, asigna el −0,8/−0,6
  **exclusivamente a Terra/Aqua (MODIS), citando Wright 2002**. No hay fila VIIRS
  (`coppola2024_chapter.txt:1034`).
- `K1` no aparece ni una vez en Campus 2022, Campus 2024, Massimetti 2024 ni la tesis.
- En el mismo capítulo, MIROVA **no** está clasificado como algoritmo de umbral fijo sino como
  **híbrido**, que *"uses some spectral indices in combination with a contextual analysis"*
  (`coppola2024_chapter.txt:1082-1084`).

**Recalibrar K1 sería inventar un mecanismo que MIROVA no tiene.** Camino cerrado.

## 5. El reencuadre — el 0,61 % es el diseño, no la avería

El dato que reordena el problema está en los apéndices del propio paper: las anomalías **reales**
de Villarrica (NTI ≈ −0,93) y Ubinas (−0,91) están **muy por debajo** de K1 = −0,80, y el paper
dice que se detectan *"after performing the spatial filtering (dNTI and dETI)"*
(`sp426_5.txt:809`, `:817`, `:829`).

O sea: **en MIROVA la señal débil la capturan los tests contextuales, no el Test 1.** El Test 1 es
un atajo para anomalías fuertes, heredado de MODVOLC (`sp426_5.txt:296-299`). Que el nuestro
dispare en 0,61 % es **consistente con el diseño**.

Y entonces la pregunta correcta cambia de lugar. En las 12 noches que perdía el brazo fiel, el
primer pase de nuestros Tests 2∧3 entrega **0 a 2 píxeles**. Con Villarrica a NTI −0,93 el paper
detecta por filtrado espacial; nosotros, a −0,95, no lo vemos por el contextual y lo cubrimos con
el Test 1 integrado.

**Hipótesis de causa raíz, no verificada:** el Test 1 integrado (S25/S27) no fue un aporte al
algoritmo sino **una compensación de la debilidad de nuestros tests contextuales**. Si es así,
explica por qué los cinco brazos del A/B de S135 fracasaron: tocaban los parches, no la causa. El
frente a auditar es el contextual — C1/C2 por dual-ROI, el σ global por imagen, el retiro de los
activos del pool, y el second run.

## 6. Estado de los caminos

| camino | estado |
|---|---|
| **Los tests contextuales: por qué el primer pase da 0-2 px donde MIROVA detecta** | **abierto, candidato principal** |
| Intersección contextual del Test 1 | abierto — desenlace C; ampliar a pasadas con sustrato |
| Restaurar la unión de caminos (`:1255`) | descartado como solución; divergencia literal a documentar |
| Recalibrar K1 para VIIRS | **cerrado** — empírico (AUC 0,614) y documental (no existe en MIROVA) |
| Máximo diario de Laiolo 2026 | sin explorar |
| `k_sigma` = 3 contra 5/10 de la Tabla 1 | sin explorar |

## 7. Hallazgo aparte, que afecta el artículo en redacción

El mecanismo que sostiene **toda** la señal débil del sensor principal —`compute_test1_mir`, el
«Test 1 integrado»— **no es el Test 1 del paper**, y sus parámetros tampoco salen de ahí:

- No hay en `sp426.5` ninguna versión del Test 1 que integre radiancia sobre una región: el del
  paper es per-píxel (`:294-302`), en una sección titulada *Fixed NTI threshold*.
- `mir_relative = 0,02` coincide con el **C1 diurno** de la Tabla 1, un piso adimensional sobre el
  índice contextual, no una fracción de radiancia del infrarrojo medio.
- `k_sigma = 3,0` no está en la Tabla 1, que fija 5 (cumbre) y 10 (escena) de noche. El paper
  menciona un valor cercano a 3 para describir su costo: pierde sólo 7 % de las alertas chicas
  *"at the expense of more than 7% false detections"* (`:408-413`).
- La cita que lo respalda en el código y en tres documentos, «Coppola 2015 §2.2 Eq.1», remite a una
  sección que no existe: el paper no tiene secciones numeradas.

Nació de un experimento honesto sobre Villarrica (S25, activado en S27) y cerró D4 subiendo el
recall unos 30 puntos. El problema es que quedó **rotulado como fidelidad al paper**. Decisión de
Nicolás pendiente: declararlo como divergencia en el artículo, o corregir el mecanismo antes de
redactar.

## 8. Hueco declarado

**Coppola et al. 2022, Vulcano, *Front. Earth Sci.* 10:964372** —el paper primario de las bandas I
de VIIRS— **no está en `documentacion/`**; sólo aparece citado por la tesis, Campus 2024 y Aveni
2024. Es el único documento del canon que podría contener un umbral para I04/I05 y no se pudo
verificar. Conseguirlo es barato y cerraría el punto 4 sin residuo.
