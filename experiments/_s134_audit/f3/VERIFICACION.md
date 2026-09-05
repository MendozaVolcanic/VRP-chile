# VERIFICACIÓN F3 — verificador con contexto limpio (S134)

Sólo lectura. Scripts propios: `verif_h1.py`, `verif_h1b.py`, `verif_h1c.py`, `verif_h2.py`,
`verif_mirova2.py` en este mismo directorio. Flags leídos SIEMPRE por `pipeline.profile`
(A89), nunca del YAML. Ventana: V375, `distance_class == "summit"`, desde 2026-06-01.

---

## El fenómeno, antes del código

Un cono nevado de noche no es térmicamente plano: la cumbre está a 272 K y el pie del cono, mil
metros más abajo y sin nieve, a 280 K. Dentro de un disco de 3 km alrededor del cráter, el píxel
más caliente en el MIR **no es el cráter: es el borde del disco**, y lo es por la cota, no por
actividad. Eso es A69 escrito de nuevo. Lo que verifiqué es si el pipeline publica ese píxel del
flanco como si fuera el cráter.

---

## H1 — CONFIRMADO · gravedad **5** (la subo desde 4)

**(a) Flags efectivos** — `VRP_PROFILE=mirova_equivalent python -c "import pipeline.profile as p; ..."`:
`ENABLE_TEST1_CONTEXTUAL_FILTER = True`, `ENABLE_TEST1_CONTEXTUAL_KEEP_PEAK = True`,
`ENABLE_TEST1_PRIORITY_WEAK_CLUSTER = True`, `ENABLE_HONEST_ANCHOR = True`,
`HONEST_ANCHOR_TEST1_MODE = vent`. Los cinco encendidos: la rama existe y corre.

**(b) La rama** — `process_viirs.py:1777-1786`: `_ctx_peak_rc` = `argmax(bt)` sobre
`test1_hot_filtered`; `test1_contextual_filter.py:58-66` devuelve `(mask ∩ ctx) ∪ {peak}`.
`test1_hot` viene de `mask_contributing` (`process_viirs.py:1107`), que es
`excess_roi > 0` dentro del ROI (`test1_integrated.py:291-295`). Todo píxel del disco más caliente
que la mediana del anillo está ahí, luego **el argmax sobre la máscara ES el argmax del disco**.

**(c) Radio** — `TEST1_ROI_KM = 3.0` efectivo, pasado en `process_viirs.py:1098`. Los 3 km son reales.

**(d) «Más frío que el fondo»: válido, y con el par de campos correcto.** No es `t_max_i04_k`
(ése es el máximo del ROI de 25 km y está **+9,76 K sobre el fondo**, mediana). Es el `bt_k` del
píxel del cúmulo contra `t_bg_k` (anillo global 5-25 km): **172/245 = 70 %**, mediana **−2,95 K**
(`verif_h1c.py`). Reproduce el 172/245 del auditor exactamente. Que ambas cosas convivan es
coherente: el píxel supera el anillo **local** [1,3] km (nevado, frío) y no supera el global
(valles tibios). El fondo del Test 1 en Villarrica es el local, porque
`ENABLE_TEST1_INTERMEDIATE_BG` está gateado per-vol a Lascar/NdC/Lastarria
(`test1_integrated.py`, docstring SCOPE S112).

**(e) Conteos reproducidos** (`verif_h1.py`): Villarrica **245/289** `test1_roi`, **100 %** con
1 píxel, mediana **2,80 km**, **198/245** en [2,5-3,0], `final_hotspot_dist_km = 0,0` en **245/245**
(`anchor.py:89` → `return (vent_lat, vent_lon, 0.0, "test1_roi")`).

**(f) Lecturas alternativas — las enumeré y ninguna lo salva:**

| lectura alternativa | resultado |
|---|---|
| «el argmax cae en cualquier píxel tibio, no en el borde» | **Refutada.** Si cayera al azar en el disco, el área daría ~30 % en [2,5-3,0]. Da **81 %**. Está apilado contra la frontera del ROI: gradiente radial monótono. |
| «`dnti_ctx_hot` no está vacía sino con píxeles fuera del cráter» | **Refutada por medición.** Si sobrevivieran píxeles contextuales, el cúmulo tendría >1 píxel. Tiene **1 en el 100 %** de los 245. La intersección es vacía y sólo queda `keep_peak`. |
| «el anillo es del volcán, no del path» | **Refutada.** Mismo volcán, mismo mes: `test1_roi` 198/245 (81 %) en [2,5-3,0]; `ctx_cluster` **12/44 (27 %)**, rango 0,01-4,91 km. El anillo sigue al path, no al cerro. |
| **«poner la posición en el cráter es semántica deliberada de integral-de-ROI, no un bug»** | **VÁLIDA y hay que decirla.** `frontend/index.html:2779-2784` lo declara: los `anomaly_pixels` son «el FOOTPRINT de la integral … arrastre topográfico A69, no detecciones puntuales reclamadas». **Pero no cubre la magnitud** (abajo). |
| «MIROVA no lo publica ⇒ es artefacto» | **No es válida sola** (A54): MIROVA publicó sólo **15** ALERTAS VIIRS375 de Villarrica en 3 meses contra 289 records nuestros. Ver P3. |

**Lo que la defensa deliberada NO cubre.** La posición puede ser convención; el **número en MW no**.
`pc.vrp_mw` sale del cúmulo Test 1 (`process_viirs.py:1896-1930`) = ese píxel del flanco, medido
contra el anillo [1,3] km que **solapa el ROI de 3 km que mide** (fondo autorreferente, S126). El
arreglo del paper —Eq. 6, «arithmetic mean of all the pixels surrounding the active one»
(`documentacion/sp426_5.txt:355-358`)— es la corona, y está
**`ENABLE_LOCAL_CLUSTER_MAGNITUDE_VIIRS375 = False`**. Publicamos 0,011-0,618 MW (mediana 0,046)
como exceso del píxel de roca desnuda del flanco sobre su propio anillo de nieve.

**Número del auditor que NO reproduce**: «MIROVA publicó esas pasadas en el 4,9 %». Con
`load_mirova_alertas`, ventana común 2026-06-01→2026-08-31, ±90 min, bucket VIIRS375, me da
**11,5 %** (27/235). La dirección aguanta; la cifra no.

---

## Corrección al brief — CONFIRMADA

El anillo está en los **11**, Láscar incluido. Mediana de `test1_roi` al vent (`verif_h1.py` B):
Villarrica 2,80 · Copahue 2,80 · Llaima 2,84 · Isluga 2,76 · NdC 2,69 · **Láscar 2,63** ·
Chaitén 2,60 · PP 2,59 · Lastarria 2,46 · PCC 2,45 · Tupungatito 2,26. La diferencia es la mezcla
de fuentes: Láscar 138 `test1_roi` / 152 `ctx_cluster`; Villarrica 245 / 44. Y el control positivo
aguanta: `ctx_cluster` de Láscar a **0,18 km** (n=152).

---

## H2 — CONFIRMADO · gravedad **3**, y con **más** divergencias que las que reporta el auditor

**Código.** Primer pass `detection_context.py:518-523`: `hot = roi_mask & … & pass_2 & pass_3 &
(bt > t_bg + bt_sanity_k)`. Segundo pass `:877-879`: `newly_active = pass_2 & pass_3 &
isfinite(dnti) & isfinite(deti)` — **sin** el término de BT.

**Verifiqué si algo aguas abajo lo tapa (y no):**
- El call site del path ETI **sí** lo reaplica (`process_viirs.py:1171-1172`). Ése está cubierto.
- El call site principal (`:1277`, sobre `hot_mask_2d`) **no**.
- El filtro que lo habría atrapado, `ENABLE_FINAL_PIXEL_FILTER`, está **False** efectivo; el
  `ENABLE_SECOND_PASS_INTRA_RADIO_GATE` también. **La brecha es efectiva, no nominal.**

**¿Es el diseño de Coppola?** No: es lo contrario. `documentacion/sp426_5.txt:329-341` — *«The last
step is applied only if one or more pixels have been detected by the previous tests, and focuses on
refining the hotspot detection for the pixels adjacent to those already flagged.»* Nuestro
`second_pass_adjacent` incumple las dos condiciones: (1) corre con `active_mask` **vacía** —
**2295/3164** records summit V375 tienen `diag_n_first_pass_pixels == 0`; (2) `newly_active` **no**
se restringe a la vecindad de `active_mask`, es de imagen entera. Con conjunto activo vacío no hay
«adyacentes» y el segundo run del paper no debería correr. Eso es más grave que la compuerta de BT.

**Datos**: 438 records con `first_pass==0 & recapture>0` (auditor: 424), **Chaitén 89** exacto.
No reproduce «175 más fríos»: con `t_max_i04_k` vs `t_bg_k` da **0** (mismo malentendido de campo
que en H1(d); con el píxel del cúmulo probablemente sí).

---

## H3 — CONFIRMADO · gravedad **3**

Reproducido exacto (`verif_h1.py` D): `pc.centroid ≠ final_hotspot` en **19/44** Villarrica,
**23/52** Llaima, **14/22** Tupungatito.

**Cuál dibuja el dashboard: el `final_hotspot`.** `frontend/index.html:2787-2790` y `:2794-2797`
construyen el marcador con `lat: r.final_hotspot_lat, lon: r.final_hotspot_lon,
dist_km: r.final_hotspot_dist_km`. `primary_cluster.centroid` **no** dibuja (sólo se usa en
`:1140-1141` para recortar el núcleo F5'). O sea: se dibuja la posición del snapshot contextual y
se informa la magnitud del pico del Test 1 — dos objetos distintos en un mismo punto.

---

## H4 — CONFIRMADO · gravedad **2**

Medido, no leído (`verif_h1c.py`, Villarrica, error mediano en km):

| campo | vs vent | vs catálogo | origen |
|---|---|---|---|
| `anomaly_pixels[].dist_km` | 0,694 | **0,0027** | catálogo |
| `hotspot_dist_km` | 0,515 | **0,0038** | catálogo |
| `diag_t_max_dist_km` | — | — | catálogo (`process_viirs.py:945`, usa `dist`) |
| `final_hotspot_dist_km` | — | — | cascada del ancla (0,0 en `test1_roi`) |
| `vent_dist_per_pixel` (detección, dual-ROI) | — | — | **vent** (`:729`) |

Separación catálogo↔vent en Villarrica: **0,849 km** medidos. El defecto no es el sesgo sino la
**mezcla**: cuatro orígenes distintos en el mismo record, y la detección usa uno que los campos
publicados no usan (A3).

---

## H6 — REFUTADO como defecto · gravedad **1**

El comentario de `mirova_equivalent.yaml:375` dice «[2,4]km **(default)**», y la línea **379** del
mismo bloque dice, textual, «Ring [1.5,3] en thresholds (ver test1_intermediate_bg_ring_km)».
Efectivo `TEST1_INTERMEDIATE_BG_RING_KM = (1.5, 3.0)`. El comentario documenta su propio override:
no hay discrepancia, a lo sumo redacción.

---

## Punto 7 (dashboard) — CONFIRMADO · gravedad **4**

`frontend/index.html:2785-2792`: si `final_hotspot_source ∈ {test1_roi, test1_nti_peak}`, el
marcador **primario** es el ancla (cráter, 0,0 km) y el footprint real va `.concat()`-eado detrás,
visible sólo bajo «Todos los pixels». VRP mediano 0,046 MW. **No son 6 volcanes: son los 11**,
entre 56 y 266 records `test1_roi` cada uno en 3 meses.

---

## Hallazgos propios

- **P1 · gravedad 3.** `frontend/index.html:2789` pone en el popup `bt_k: r.t_max_k ?? r.t_max_i04_k`
  — el máximo del ROI de **25 km**, un TERCER píxel. En los 245 records de Villarrica el popup
  combina: punto en el cráter (0,0 km), temperatura de un píxel que puede estar a 25 km (+9,76 K
  sobre el fondo) y magnitud de un píxel a 2,8 km que está **−2,95 K bajo** el fondo. Tres objetos,
  un globo.
- **P2 · gravedad 3.** El segundo run corre sin conjunto activo y sin restricción de adyacencia,
  contra `sp426_5.txt:329-341` (detallado en H2). 2295/3164 records.
- **P3 · método.** El control cruzado del auditor (Láscar 82,8 % vs Villarrica 4,9 %) está
  **confundido por cuánto publica MIROVA cada volcán**: 118 ALERTAS VIIRS375 de Láscar contra 15 de
  Villarrica en la ventana. El control válido es **dentro** del volcán, y ése aguanta:
  `ctx_cluster` corrobora más que `test1_roi` en **10 de 11** (Láscar 97,1 % vs 47,8 %; PCC 55,6 vs
  16,1; PP 73,1 vs 32,0; Villarrica 32,4 vs 11,5). Única inversión: Tupungatito (50,8 vs 11,1, n=9).
- **P4.** Dos números del informe no reproducen: Villarrica 4,9 % (→11,5 %) y «175 más fríos» (→0
  con los campos obvios). Ninguno cambia el veredicto.
- **P5 · gravedad 4.** La pata de magnitud de H1 (fondo autorreferente + corona OFF) no está
  enunciada como tal en el informe y es la parte **no** cubierta por la defensa «semántica
  deliberada».

## VERIFICADO LIMPIO

Lecturas de flags (todas por `pipeline.profile`); desglose por `final_hotspot_source` en los 11;
conteos de H3; origen de los campos de distancia de H4; `TEST1_ROI_KM = 3.0`.
