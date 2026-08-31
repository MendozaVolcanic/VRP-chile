# S129 · V1 — Coherencia entre las vistas

**Pregunta**: un operador mira el mismo volcán en `index.html`, `diario.html` y `mosaico.html`
el mismo día. ¿Ve el mismo número? Y si no, ¿el dashboard le avisa?

**Respuesta corta**: no, y no avisa.

---

## Resumen (334 palabras)

**La divergencia de mayor impacto operacional es el nivel de alerta entre `index` y `mosaico`.**
No es un desacuerdo de fórmula: las dos vistas calculan la magnitud con el **mismo código**
(`mirovaEqVrp` es byte-idéntico entre ambas, verificado con `diff`) y con los **mismos cortes de
nivel** (0/1/10/100/1000 MW). Divergen en **qué record de las 48 horas eligen**: `index` toma la
**última** detección (`latestDetection`, `index.html:1387`), `mosaico` toma el **máximo**
(`latestVRP`, `mosaico.html:370`).

Barriendo ventanas de 48 h cada 6 h sobre los últimos 60 días (240 instantes × 11 volcanes = 2.640
ventanas), las dos vistas muestran **número distinto en el 73 %** de las ventanas y **nivel de
alerta distinto en el 19 %**. Por volcán, el nivel discrepa el **50 % del tiempo en
Puyehue-Cordón Caulle**, 34 % en Villarrica, 29 % en Chaitén. La razón mosaico/index llega a
**263×** en el percentil 95 de PCC. En el instante de esta auditoría (2026-08-31 12:11 UTC), PCC
se lee *0,43 MW · Muy Bajo* en `index` y *4,58 MW · Bajo* en `mosaico`; Llaima, *0,05 MW · Muy
Bajo* contra *1,12 MW · Bajo*.

Nada en la interfaz distingue las dos cantidades. `mosaico` rotula su número `MW (48h)` y pone
abajo **«Últ. detección»** junto a un timestamp que en realidad es el del **máximo**
(`mosaico.html:600`, `643-646`) — una etiqueta falsa dentro de la propia vista. Y la tarjeta de
`mosaico` es un enlace a `index.html?volcano=<nombre>`: el operador hace clic sobre «Bajo» y
aterriza en «Muy Bajo» del mismo volcán, en el mismo minuto, sin ninguna explicación.

Fuera de eso, la copia triplicada de los helpers está **más sana de lo esperado**: `parseUtcMs`,
`_havKm`, `f5CoreMagnitude` y los tres filtros de artefacto son idénticos entre las tres vistas
(`diff` limpio), los `inner_radius_km` coinciden con `volcanoes.yaml` en los 11 Tier A, y las dos
diferencias reales de `mirovaEqVrp` en `diario` no cambian **ningún** valor sobre los 10.458
records de los últimos 90 días. Son divergencias **latentes**, no activas.

---

## Tabla de divergencias

| # | Panel | `index.html` | `diario.html` | `mosaico.html` | ¿Lo nota el operador? |
|---|---|---|---|---|---|
| **D1** | Número VRP y **nivel de alerta** de la tarjeta | **Última** detección de 48 h (`:1387`, `:1435`) | *(no muestra nivel)* | **Máximo** de 48 h (`:370`) | **No.** 73 % de ventanas con número distinto, **19 % con nivel distinto** |
| **D2** | Pie de la tarjeta de `mosaico` | «Última detección» = la mostrada | — | «Últ. detección» = timestamp del **máximo** (`:600`,`:643`) | **No.** La etiqueta es falsa |
| **D3** | Guardas de detección | `isSummitDetection` + `isValidDetection` + `isSensorVisible` (`:1390-1393`) | ninguna | ninguna | **No.** 124 records/90 d con VRP>0 que `index` descarta y las otras muestran |
| **D4** | Firma de `mirovaEqVrp` | fallback legacy **antes** del gate, con tope 50.000 MW (`:975-981`) | gate **antes** del fallback; fallback **sin tope** y sin `vrp_mir_mw` (`:241-245`) | = `index` (idéntico) | **Latente**: 0 diferencias en 10.458 records |
| **D5** | Filtro de artefacto térmico | entrada `includeFar=false` fija + cinturón `_mirova_confirmed` (`:1112`,`:1131`) | entrada = toggle vivo; **sin** cinturón (`:337`,`:348`) | `false` fijo; **sin** cinturón (`:328`,`:339`) | **Latente**: 0 artefactos disparan en 90 d |
| **D6** | Toggles de display | `vrp_f5_core`, `vrp_include_far`, `vrp_sensors_v3` | `diario_f5_core`, `diario_include_far` | `mosaico_f5_core`; **sin** «incluir lejanas» ni filtro de sensor | **No.** Cambiar un toggle no propaga a las otras vistas |
| **D7** | Referencia MIROVA | `data/mirova/<vol>.json` (`:904`) | `latest_consolidado.csv`, sólo `ALERTA_TERMICA` (`:193-206`) | `data/mirova/<vol>.json` (`:399`) | **Coinciden hoy** (mismo conteo en los 11); dos rutas independientes |
| **D8** | Barras del gráfico | por **plataforma** (Terra/Aqua, SNPP/N20/N21) | por **banda** (3 series) | sparkline 30 d, máximo diario | Sí, es visible; la barra alta de `diario` = la más alta de `index` |
| **D9** | Ventana temporal | 30 d por defecto (`:806`), toggle a 90/180 | **90 d fijo** (`:155`) | 48 h + sparkline 30 d | Sí, está rotulado |

---

## Lo que sí está sano (negativos establecidos)

`diff` sobre las funciones extraídas de las tres vistas, ignorando comentarios:

- `parseUtcMs` — **idéntico** en las tres (`index:1175`, `diario:364`, `mosaico:355`). Y los tres
  cortes de ventana lo usan (`index:925`, `diario:416`/`501`, `mosaico:376`/`517`), igual que el
  parseo del CSV/JSON MIROVA. **No hay bug de UTC vivo**: todo se corta en UTC.
- `_havKm` y `f5CoreMagnitude` — **idénticos** en las tres (`R_CORE=0.75 km`, `BT_EXT=295 K`).
- `isCirrusArtifact` / `isDiffuseFieldArtifact` / `isThermalArtifact` — **idénticos** entre `index`
  y `mosaico`; en `diario` la única diferencia es la firma (D5).
- `LEVELS` — cortes idénticos entre `index:707` y `mosaico:229`. (Detalle cosmético: `index` le da
  a «Muy Alto» la misma clase de badge que «Alto», `:714`.)
- `mirovaEqVrp` — `index` y `mosaico` byte-idénticos.
- `inner_radius_km` — los 11 valores coinciden entre `index:643-684`, `diario:227-231`,
  `mosaico:207-217` y `volcanoes.yaml`. Sólo difieren los *defaults* para volcanes sin data
  (`index` 10, `diario` 5), que hoy no se ejercitan.
- El default de F5' (`USE_F5_CORE = true`) coincide en las tres.
- Las tres consumen el mismo `<vol>_recent.json` (100 d) que genera `build_recent_json.py`.

**Por qué D4 y D5 no muerden hoy** (fenómeno, no suerte): D4 sólo se activaría con un record
legacy sin `primary_cluster` que además esté clasificado `far` o supere los 50.000 MW; de los 3.903
records sin `primary_cluster` en 90 días, **cero** cumplen alguna de las dos condiciones (son
pasadas sin detección). D5 sólo se activaría con un artefacto de nube fría, y desde que se adoptó
el área nadir-fija (S102/S103) **ningún** record de los 11 pasa de 10 MW salvo uno (máximo global
13,60 MW, y no es frío): los dos filtros de artefacto están **dormidos**, 0/10.458.

---

## Riesgo de mantención: los punteros de sincronía están todos obsoletos

Lo único que mantiene alineadas las tres copias son comentarios del tipo «sync con index.html
L###». **Los siete de `mosaico.html` apuntan a otra cosa**: L585 → un botón, L665 → la ficha de
Copahue, L732 → una banda de color, L822 → línea en blanco, **L998 → un comentario de F5' (la
función citada, `latestVRP`, está en `index.html:1435`)**, L2675 y L2853 → código sin relación.
`index.html:978` cita «paridad con diario.html:237», y esa línea es `let includeFarDistance = false`.

Dos casos más de «declarado ≠ efectivo», en la línea del que ya trae el contexto:

- `mosaico.html:369` rotula la función «Latest 48h max (sync con index.html L998)» — pero desde S90
  `index` **ya no calcula un máximo de 48 h**. El comentario describe el código de `mosaico` y
  afirma que es el de `index`; es exactamente la divergencia D1, escrita al revés.
- `index.html:811-812` dice que las lejanas «no inflan el valor *48h max* ni el nivel de alerta».
  Ese «48h max» dejó de existir en `index` en S90.

`comparacion.html` queda fuera de alcance por diseño (PREVIEW S115). Sólo se deja constancia de que
carga el JSON **completo** por volcán (`:195`, 19-34 MB), no el `_recent` que usan las tres vistas
live.

---

## Verificación

- **`diff` propio** de cada helper extraído con `sed` de las tres vistas, filtrando comentarios.
- **Reimplementación 1:1 en Python** de `mirovaEqVrp` (dos variantes), `f5CoreMagnitude`,
  los filtros de artefacto, `isValidDetection`/`isSummitDetection` y `getLevel`, corrida sobre los
  11 JSON operacionales (`data/mirova_equivalent/`), 10.458 records de 90 días.
- **Barrido rodante** de 240 ventanas de 48 h × 11 volcanes, con descomposición de la causa
  (máximo-vs-última contra guardas): la causa dominante es máximo-vs-última en los 11
  (1.844 de 1.917 ventanas divergentes).
- El instante de referencia es **2026-08-31 12:11 UTC** (A86); los porcentajes del barrido rodante
  no dependen de él, los valores puntuales de PCC/Llaima sí.

*Auditoría read-only. No se modificó código.*
