# F3 · El mecanismo que corre el cúmulo al flanco — código vs física (S134)

Auditoría read-only. Worktree `s134-f3`, JSON leídos por ruta absoluta desde
`C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/data/mirova_equivalent/`.
Ventana de todos los números: **records VIIRS 375 m, `distance_class=summit`, desde 2026-06-01**
(convención A48: `VIIRS_*` sin sufijo `_750`). Ancla siempre `vent_lat/vent_lon` de
`volcanoes.yaml` (A13). Scripts y salidas en esta carpeta:

| archivo | qué produce |
|---|---|
| `atribucion_pixeles.py` → `resultados.json` | instrumento, distancias por fuente, cruce por camino, histograma de píxeles (Villarrica + Láscar) |
| `anillo_por_source.py` → `anillo_por_source.json` | el anillo de `docs/s133/ANILLO_TIER_A.md` desglosado por `final_hotspot_source`, 11 Tier A |
| `tabla_6_pasadas.py` → `tabla_6_pasadas.json` | tabla etapa × pasada, 3 Villarrica + 3 Láscar |
| `cruce_mirova_por_clase.py` → `cruce_mirova_por_clase.json` | ¿MIROVA (CONS ∪ OCR) publicó esa pasada?, por clase de record |
| `probe_etapas_ci.md` | diseño del probe A75 para GitHub Actions (S135) |

---

## 0. La afirmación central

**El cúmulo publicado deja de estar en el cráter en la etapa de FILTRADO DEL TEST 1, antes de
agrupar, por el mecanismo `keep_peak`: `test1_hot_filtered = (Test1 ∩ dNTI_ctx) ∪ {argmax BT}`.**
Cuando la máscara contextual está vacía —lo normal en un nevado con señal débil— el Test 1 queda
reducido a **un solo píxel: el de mayor BT MIR dentro del disco de 3 km**. En un cono nevado ese
píxel es la cota más baja del disco, o sea su borde (2,5-3,0 km), en cualquier dirección. Ese píxel
único es el `primary_cluster`, su `ΔL` sobre la mediana del anillo 1-3 km es la magnitud publicada
(`f5_core_vrp_mw`), y su BT es en el 70 % de los casos **menor que el fondo global** `t_bg_k`.
No es calor.

**CONFIANZA: CONFIRMADO** por traza estática (archivo:línea abajo) y por tres mediciones
independientes sobre los píxeles persistidos que dan la firma exacta que la traza predice:
un píxel, en el borde del ROI, más frío que el fondo, sin primer pase. El control positivo
(Láscar, camino contextual) responde: 0,18 km. No hace falta el probe en CI para la afirmación
central; sí para cuantificar cuántos píxeles del Test 1 cubren el cráter antes del recorte (§7).

Las cuatro causas candidatas del brief, evaluadas:

| candidata | veredicto | evidencia |
|---|---|---|
| (a) la detección marca el cráter pero la selección elige otro cúmulo | **NO es la causa principal.** Cuando llega a `cluster_hotspots` ya sólo hay un píxel | `pc.n_pixels==1` en 244/245 records `test1_roi` de Villarrica; `len(anomaly_pixels)==1` en 243/245 |
| (b) un cúmulo grande con cola de nieve que arrastra el centroide | **NO.** El cúmulo publicado es un píxel | ídem; `frac_E_075` mediana 1,0 |
| (c) recaptura del second pass agrega flanco | **SÍ, pero es el mecanismo SECUNDARIO** (Hallazgo 2): 28/289 Villarrica, 89/323 Chaitén; posición 3,5 km | §3.2 |
| (d) centroide sin ponderar por energía | **Cierto en el código** (`clustering.py:102-103`) **pero irrelevante** para VIIRS375: 99 % single-pixel; en Láscar multi-píxel geo vs ponderado difieren ≤0,1 km | tabla §5 |

---

## 1. Traza estática (etapa → función → archivo:línea → ancla → qué devuelve)

Todos los valores de flag son **efectivos** (`VRP_PROFILE=mirova_equivalent python -c "import
pipeline.profile as p; ..."`), no leídos del YAML (A89).

| # | etapa | función | archivo:línea | ancla que recibe | devuelve / hace |
|---|---|---|---|---|---|
| 0 | ancla | `get_detection_anchor(volcano)` | `pipeline/geo_utils.py:53-78` | `vent_lat/lon` (prioridad 1) | `(vent_lat, vent_lon)`; el caller `scripts/run_pipeline.py:277-281` lo pasa como `vent_lat/vent_lon` a `process_viirs.calculate_vrp` |
| 0b | distancias | `dist` vs `vent_dist_per_pixel` | `pipeline/process_viirs.py:723` y `:728-731` | `dist` = desde `volcano_lat/lon` (**catálogo**); `vent_dist_per_pixel` = desde el vent | dos grillas de distancia con anclas distintas (ver censo §2) |
| 1 | Test 1 (MIR absoluto) | `compute_test1_mir` | `pipeline/test1_integrated.py:317`; ROI `:376` (`dist<=3 km`), fondo `:377,412` (**mediana** del anillo 1-3 km), `excess_roi=max(0,L−L_bg)` `:420`, `contributing = excess>0` `:432` | `vent_lat/lon` (`process_viirs.py:1094-1096`) | `mask_contributing` (≈ la mitad del disco de 3 km por construcción de la mediana; n_test1 mediana **67**), `L_bg`, centroide **ponderado por exceso** (`:440-447`) |
| 1' | Test 1 (NTI) | `compute_test1_nti` | `test1_integrated.py:185` | — | **NO corre**: `ENABLE_TEST1_NTI_INTEGRAL = False` (efectivo). Sólo `process_viirs.py:1077` la importa; MODIS/V750 ni eso |
| 2 | first pass Tests 2∧3 | `first_pass_tests_2_and_3` | `pipeline/detection_context.py:399`; pool μ/σ con pisos «unsuitable» `:476`; compuerta final `:517-522` = `roi & pass_2 & pass_3 & (bt > t_bg + 3 K)` | `dist_km=vent_dist_per_pixel`, `inner_km=inner_radius_km` (`process_viirs.py:1231-1250`) | `hot_mask_2d` (dual-ROI 5σ/10σ), `n_first_pass_pixels` |
| 3 | second pass | `second_pass_adjacent` | `detection_context.py:767`; pool `:845` (todo no-activo, **sin pisos**), `newly_active = pass_2 & pass_3` `:876` (**sin `roi`, sin compuerta BT**) | `is_summit = vent_dist_per_pixel <= inner` | `hot_mask_2d ∪ newly_active` |
| 3b | gate intra-radio S85 | `apply_second_pass_intra_radio_gate` | `pipeline/second_pass_intra_radio.py:135` | — | **NO corre**: `ENABLE_SECOND_PASS_INTRA_RADIO_GATE = False` (efectivo, flip OFF S118) |
| 4 | píxeles y cúmulo contextual | `cluster_hotspots(hot_mask_2d, …, _vlat, _vlon, strategy=vent_anchored, inner)` | `process_viirs.py:1454-1459`; `anomaly_pixels` top-100 `:1416-1431` | `_vlat/_vlon = vent` (fallback catálogo) | `primary_cluster` → snapshot `ctx_cluster_anchor` `:1520-1521` |
| 4' | `cluster_hotspots` | conectividad **8**, centroide **media aritmética** de lat/lon, `vent_anchored`: sólo cúmulos con `vrp_mw>0` son elegibles (S43), entre ellos gana el **más cercano al ancla** dentro del inner | `pipeline/clustering.py:96-104, 143-158` | `vent_lat/lon` | lista ordenada; `[0]` es el primario |
| 5 | ¿gana el Test 1? | `resolve_test1_source_priority` | `process_viirs.py:1697-1703`; helper `test1_integrated.py:156`; **`ENABLE_TEST1_PRIORITY_WEAK_CLUSTER = True`** (cúmulo rival < 0,01 MW ⇒ gana el Test 1) | — | `_test1_wins` → `final_hotspot_source` interno `"test1"` |
| 6 | **filtrado del Test 1** | `apply_contextual_test1_filter(test1_hot_filtered, dnti_ctx_hot, keep_peak_rc)` | `process_viirs.py:1775-1786`; pico = `argmax(bt)` sobre los píxeles Test 1 `:1782-1784`; helper `pipeline/test1_contextual_filter.py:57-62` | — | `(Test1 ∩ dNTI_ctx) ∪ {pico}`. **`ENABLE_TEST1_CONTEXTUAL_FILTER = True`, `ENABLE_TEST1_CONTEXTUAL_KEEP_PEAK = True`** (adoptados S100, #340 «ctxpeak») |
| 6b | fondo del recompute | `select_test1_effective_lbg` | `test1_integrated.py:147-153` | — | intermedio [1,5-3] km y global **sólo si `lbg_global_compatible`** (Láscar/NdC/Lastarria); Villarrica usa el **local** (mediana 1-3 km, la misma del paso 1) |
| 7 | píxeles y cúmulo del Test 1 | `build_anomaly_pixels(t1_vrp_2d…)` sólo `vrp>0` (`pipeline/anomaly_pixels.py:31`); `cluster_hotspots(test1_hot_filtered, …, vent_lat, vent_lon, vent_anchored)` | `process_viirs.py:1889`, `:1897-1901` | `vent_lat/lon` | **pisa `primary_cluster`** `:1926-1932` (el snapshot contextual del paso 4 sobrevive aparte) |
| 8 | single-pixel | `apply_single_pixel_mode` | `pipeline/single_pixel_mode.py:94`; `<5 MW` y `≤3 px` ⇒ `vrp = max(per_pixel)` | — | no toca posición |
| 9 | posición honesta | `resolve_honest_anchor` | `pipeline/anchor.py:67-96`; caller `process_viirs.py:2002-2011`; `ENABLE_HONEST_ANCHOR = True`, modo `vent` | `ctx_cluster` si existe y no está far; si no y `test1_triggered` ⇒ **`(vent_lat, vent_lon, 0.0, "test1_roi")`** | `final_hotspot_*`, `distance_class` |
| 10 | store | `append_record` | `pipeline/store.py:272`; filtro de píxeles por `dist_km` **del catálogo** `:215-270`; rescate F47 `:335-380` (no pisa posición si la fuente es honesta); guard A46 `:470-478`; `max_cluster_pixels` `:405-412`; F5' `f5_core_vrp_mw` (`pipeline/f5_core.py:234-277`, ancla en `pc.centroid`, pico = máx `vrp_mw`) | — | record persistido |
| 11 | dashboard | `frontend/index.html:1513-1518` (distancia mostrada = `final_hotspot_dist_km` si fuente honesta), `:2781-2790` (marker primario en `final_hotspot` para `test1_roi`), `:1160-1185` (`mirovaEqVrpCore` → `f5CoreMagnitude` para V375) | — | **punto rojo en el cráter, «0,0 km», magnitud del píxel del borde** |

**Patrón «un arreglo que cubre un camino de dos»**: el `ctx_cluster` y el cúmulo del Test 1 usan la
misma ancla (`vent`), pero son **dos objetos distintos** que conviven en un record: el snapshot
contextual (paso 4) da la posición y el cúmulo del Test 1 (paso 7) da la magnitud cuando `_test1_wins`
(Hallazgo 3).

---

## 2. Censo de campos de distancia del record (A3: desde qué punto mide cada uno)

| campo | ancla | dónde se calcula | nota |
|---|---|---|---|
| `anomaly_pixels[].dist_km` | **catálogo `lat/lon`** | `process_viirs.py:723` (`dist`), `:1429`; `anomaly_pixels.py:42` | en Villarrica el catálogo (-39,42/-71,93) está a **0,85 km** del cráter; medido en la tabla §5: 2,18 vs 2,97 km para el mismo píxel |
| `hotspot_dist_km` | catálogo | `:1437` = `anomaly_pixels[0].dist_km`; `store.py:258` lo recalcula desde el mismo campo | |
| `diag_t_max_dist_km` | catálogo | `:945` `dist[r_max, c_max]` | y sobre el ROI de 25 km, no del cráter |
| `vent_hotspot_dist_km` | vent | `:1611-1612` | `ENABLE_VENT_PATH=False` ⇒ hoy `None` |
| `primary_cluster.centroid_dist_km` | vent (`_vlat/_vlon`, fallback catálogo) | `clustering.py:104`; `process_viirs.py:1444-1445`, `:1898` | centroide **geométrico** |
| `final_hotspot_dist_km` | vent | `anchor.py:82-89` | `0.0` por definición en `test1_roi` |
| `nti_peak_dist_km` | vent | `:1991` | sólo modo `nti_peak` (no operativo) |
| `store._filter_pixels_by_distance` (25 km) | catálogo (`dist_km` del píxel) | `store.py:243-244` | inocuo a 25 km; el mapa no lo usa para posicionar |

El mapa y `mirovaEqVrp` miden desde el vent; `anomaly_pixels[].dist_km` y `hotspot_dist_km` desde el
catálogo. En Láscar coinciden (vent ≈ catálogo); en Villarrica difieren 0,85 km. El fallback del
frontend `index.html:2485-2489` puede mostrar `hotspot_dist_km` (catálogo) cuando la fuente no es honesta.

---

## 3. Hallazgos (peor primero)

### H1 · `keep_peak` publica como «summit a 0,0 km» un píxel del borde del ROI más frío que el fondo
- **ARCHIVO:LÍNEA**: `pipeline/process_viirs.py:1775-1786` (filtro contextual + pico), `:1782-1784`
  (`argmax(bt)`), `pipeline/test1_contextual_filter.py:57-62`; `pipeline/anchor.py:89`
  (`test1_roi → (vent, 0.0)`); `pipeline/test1_integrated.py:376,412,420` (ROI 3 km, mediana, exceso).
  Flags efectivos `ENABLE_TEST1_CONTEXTUAL_FILTER=True`, `ENABLE_TEST1_CONTEXTUAL_KEEP_PEAK=True`
  (adopción S100, commit `5da0afdef`, «fix magnitud 19× Tupungatito»; `docs/MIROVA_DIVERGENCES.md:1201-1214`
  D10 justifica el pico como «= cráter»).
- **QUÉ PASA**. Física: en un cono nevado la temperatura MIR nocturna sigue la altitud; el píxel más
  caliente de un disco de 3 km centrado en la cumbre es el borde del disco, no el cráter (A69). Código:
  el Test 1 integra el exceso sobre la **mediana** del anillo 1-3 km, así que por construcción marca
  ~la mitad del disco (mediana 67 píxeles); el filtro contextual lo intersecta con `dNTI_ctx`, que en
  estas noches está vacío (`n_dnti=0` en 174/245 Villarrica), y `keep_peak` conserva **sólo `argmax(BT)`**.
  Ese único píxel es el cúmulo, su `ΔL` la magnitud, y el ancla honesta lo rotula `test1_roi` en el
  **vent a 0,0 km**. La suposición del docstring D10 «pico = cráter» es falsa en los nevados de señal
  débil: el pico está a 2,5-3,0 km y **su BT es menor que `t_bg_k`** en 172/245 (Villarrica),
  169/202 (Tupungatito), 163/223 (Llaima), 171/266 (Copahue), 152/191 (PP).
- **NÚMEROS** (publicados = `f5_core_vrp_mw`>0, summit, V375, desde 2026-06-01; `anillo_por_source.json`):

  | volcán | records `test1_roi` | d_pc mediana | `len(ap)==1` | MIROVA publicó esa pasada (CONS∪OCR, ±20 min) |
  |---|---|---|---|---|
  | Villarrica | **245 / 289** (85 %) | 2,80 km | 243 | **4,9 %** |
  | Llaima | 223 / 282 | 2,84 | 220 | 1,8 % |
  | Copahue | 266 / 307 | 2,80 | 264 | 2,3 % |
  | Chaitén | 185 / 323 | 2,60 | 160 | 2,7 % |
  | NdC | 128 / 279 | 2,70 | 124 | 7,8 % |
  | PCC | 58 / 314 | 2,45 | 55 | 3,4 % |
  | PP | 191 / 251 | 2,59 | 188 | 16,2 % |
  | Tupungatito | 202 / 224 | 2,26 | 201 | 34,2 % |
  | Isluga | 96 / 318 | 2,76 | 94 | 30,2 % |
  | Lastarria | 78 / 287 | 2,28 | 77 | 60,3 % |
  | **Láscar (control)** | 60 / 290 | **2,48** | 59 | 41,7 % |

  Los 247 píxeles persistidos de los `test1_roi` de Villarrica caen 200 en la corona 2,5-3,0 km y 4
  a <0,5 km (`resultados.json → hist_px_test1_roi_km`). Rumbo desde el cráter repartido (W 58, SE 40,
  NW 38, N 30, E 22, NE 22, SW 20, S 15): es el borde del disco, no un valle.
  **El anillo de ANILLO_TIER_A.md es esta población, y está en los 11, incluido Láscar** (2,48 km): la
  diferencia «Láscar 0,22 vs Villarrica 2,79» es la **mezcla** de fuentes (Láscar 149 `ctx_cluster` en
  el cráter contra 60 `test1_roi`; Villarrica 44 contra 245), no que el mecanismo respete a Láscar.
- **CÓMO SE VE EN EL DASHBOARD**: punto rojo *summit* sobre el cráter, distancia «0,0 km», 0,03-0,17 MW
  «Muy Bajo», casi todas las noches. La ficha muestra `t_max_k` de la escena de 25 km (273-281 K), no
  del píxel publicado (263-268 K). Con «Todos los pixels» aparece el píxel real a 2,8 km. El operador
  ve una anomalía crateriana persistente de bajo nivel que MIROVA no publica en el 95 % de las noches
  (Villarrica); un inicio real de 0,1 MW en el cráter sería indistinguible de este fondo.
- **CÓMO REPRODUCIRLO**: `python experiments/_s134_audit/f3/tabla_6_pasadas.py` — Villarrica
  `2026-07-01 05:00 VIIRS_NOAA20`: `n_test1=49`, `n_ap=1`, píxel a 2,678 km del vent, BT 263,86 K con
  `t_bg=270,10 K`, `f5=0,130 MW`, `final_hotspot_dist_km=0.0`, `source=test1_roi`. Ídem 2026-08-14 04:42
  NOAA20 (2,857 km, 266,28 K vs 262,78) y 2026-08-31 05:06 NOAA21 (2 px a 2,58/2,97 km).
- **CONFIANZA**: CONFIRMADO (traza + 3 firmas medidas + control positivo).
- **GRAVEDAD**: **4**. No tuerce una alerta alta; fabrica un nivel base falso «Muy Bajo» en el cráter
  de 6 volcanes nevados, 12 veces al día, y desplaza la magnitud comparada contra MIROVA a otro objeto.
- **TENSIÓN con A84/A83, no fix**: el mismo mecanismo devuelve pasadas que MIROVA sí publica en
  Lastarria (60 %), Tupungatito (34 %), Isluga (30 %) — ahí el «pico» puede ser Lazufre o el cráter
  fumarólico real. Cualquier cambio a `keep_peak` es régimen-dependiente (A83) y debe medirse con FN
  sobre cat-b real, no sólo FP. No se propone acá.

### H2 · El second pass «recaptura» sin primer pase: es una segunda detección más permisiva, no una recaptura
- **ARCHIVO:LÍNEA**: `pipeline/detection_context.py:876-877` (`newly_active = pass_2 & pass_3 & finite`)
  contra `:517-522` (first pass exige además `roi_mask` y **`bt > t_bg + bt_sanity_k`**, con
  `NTI_BT_SANITY_K = 3.0` efectivo); pool μ/σ `:845` sin los pisos «unsuitable» de `:476`. Caller
  `process_viirs.py:1277-1291` lo corre siempre que `fp_diag` exista, **aunque `hot_mask_2d` esté vacía**.
- **QUÉ PASA**. Física: Coppola 2016a §347-356 repite el paso 2 para rescatar vecinos cuya media de
  8 fue contaminada por un píxel activo; sin activos no hay nada que rescatar. Código: con máscara activa
  vacía el second pass recalcula el mismo dNTI/dETI y aplica Tests 2∧3 **sin la compuerta térmica del
  first pass**, así que flaggea píxeles que el first pass rechazó por no estar 3 K sobre el fondo.
  **404 de 424** píxeles publicados así (11 Tier A) tienen `bt ≤ t_bg + 3 K`; 175 son más fríos que el fondo.
- **NÚMEROS**: records summit V375 con `n_first_pass=0` y `n_second_pass_recapture>0`, fuente
  `ctx_cluster`: Chaitén **89/323**, NdC 63, Isluga 55, PCC 50, Llaima 36, PP 34, Villarrica 28, Láscar 24,
  Copahue 24, Lastarria 15, Tupungatito 9. Posición (`final_hotspot`): Villarrica 3,55 km, Llaima 3,74,
  Tupungatito 3,93, PCC 3,16 — contra 0,18 km de los `ctx_cluster` **con** primer pase en Villarrica.
  MIROVA publicó esas pasadas: Villarrica 0 %, Llaima 0 %, Copahue 0 %, Chaitén 11 %, Láscar 33 %.
- **CÓMO SE VE EN EL DASHBOARD**: punto rojo *summit* a 3-4 km del cráter (dentro del inner de 5 km),
  posición y magnitud del mismo píxel, `n_pixels=1`.
- **CÓMO REPRODUCIRLO**: `python experiments/_s134_audit/f3/anillo_por_source.py` (columna
  `rec n_fp=0&n_sp>0`) y el one-liner del §6 para la compuerta BT.
- **CONFIANZA**: CONFIRMADO (código + medición). SOSPECHA sólo en el reparto exacto entre las tres
  asimetrías (compuerta BT / pool σ / `roi`) — el 95 % que falla la compuerta BT dice cuál domina.
- **GRAVEDAD**: **3**. Es 10-28 % de lo publicado por volcán, siempre off-crater, MIROVA-silente en los
  nevados. Es drift respecto del paper (el second pass presupone activos) y ninguna regla lo protege hoy:
  la ficha de `second_pass_intra_radio.py:97` documenta otro drift, no este.

### H3 · Un record, dos objetos: la posición viene del cúmulo contextual y la magnitud del píxel-pico del Test 1
- **ARCHIVO:LÍNEA**: `process_viirs.py:1520-1521` (snapshot `ctx_cluster_anchor`), `:1699-1703`
  (`_test1_wins` con `ENABLE_TEST1_PRIORITY_WEAK_CLUSTER=True`, ε=0,01 MW), `:1926-1932` (el cúmulo Test 1
  **pisa** `primary_cluster`), `anchor.py:82-84` (posición = snapshot contextual).
- **QUÉ PASA**. Cuando Tests 2∧3 dan un cúmulo débil (<0,01 MW) y el Test 1 dispara, el record queda
  `source=ctx_cluster` (posición del contextual) pero `primary_cluster`/`f5_core_vrp_mw` son el píxel-pico
  del Test 1 (H1), a otra distancia. `pc.centroid ≠ final_hotspot` en **19/44** Villarrica, **23/52**
  Llaima, **14/22** Tupungatito, 18/152 Láscar (>50 m). Mediana Villarrica: `d_pc` 2,48 vs `d_final` 3,23 km.
  Misma familia que A46/A81 (asimetría de schema hotspot↔cluster).
- **CÓMO SE VE EN EL DASHBOARD**: el punto y la distancia son de un lugar; la magnitud, de otro.
  `docs/s133/ANILLO_TIER_A.md` midió `pc.centroid`: para estos records midió el objeto que NO se dibuja.
- **CÓMO REPRODUCIRLO**: one-liner de rumbos del §6 (columna `ctx_cluster con pc!=final`).
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: **3** (una auditoría de posición sobre `pc` y una sobre
  `final_hotspot` llegan a conclusiones distintas sobre el mismo record).

### H4 · `anomaly_pixels[].dist_km`, `hotspot_dist_km` y `diag_t_max_dist_km` miden desde el catálogo, no desde el cráter
- **ARCHIVO:LÍNEA**: `process_viirs.py:723` (`dist = haversine_km(volcano_lat, volcano_lon, …)`), `:1429`,
  `:1437`, `:945`; `anomaly_pixels.py:20-23` lo declara.
- **QUÉ PASA**: 0,85 km de sesgo en Villarrica (tabla §5: mismo píxel 2,18 km «campo» vs 2,97 km al vent);
  `f5_core.py:253-255` y el frontend ya lo saben y recomputan desde lat/lon, pero el fallback
  `index.html:2485-2489` y cualquier audit que lea `dist_km` heredan el sesgo.
- **DASHBOARD**: invisible en fuentes honestas; visible en la tabla de píxeles («dist») y en records legacy.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: **2**.

### H5 · El centroide de `cluster_hotspots` es geométrico, no ponderado — cierto pero no es la causa del anillo
- **ARCHIVO:LÍNEA**: `pipeline/clustering.py:102-103` (`np.mean(lat)`, `np.mean(lon)`); el Test 1 sí pondera
  (`test1_integrated.py:440-447`) pero su centroide sólo alimenta `test1_hotspot_dist_km`, no `pc`.
- **MEDIDO**: en los 3 Láscar multi-píxel de §5, geo vs ponderado difieren 0,04-0,08 km; en V375
  `pc.n_pixels==1` en el 93-100 % de lo publicado. Refuta la candidata (d) como origen del anillo.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: **1** (cosmético a esta resolución; relevante si algún día el
  cúmulo vuelve a ser multi-píxel).

### H6 · Comentario del perfil desactualizado: dice anillo intermedio «[2,4] km», el efectivo es (1.5, 3.0)
- **ARCHIVO:LÍNEA**: `pipeline/profiles/mirova_equivalent.yaml:375` vs `TEST1_INTERMEDIATE_BG_RING_KM = (1.5, 3.0)`
  efectivo (y la l. 27 del mismo YAML dice [1.5,3]; A79 adoptó [1.5,3]).
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: **1** (documental; y ese fondo sólo aplica a los 3 con
  `lbg_global_compatible`).

---

## 4. Verificación del instrumento (Ruta 2)

Pregunta 2 del instrumento: ¿`anomaly_pixels` está completo o truncado?

| medición | Villarrica (n=289) | Láscar (n=290) | lectura |
|---|---|---|---|
| records sin `anomaly_pixels` | 0 | **79** | SIN DATO, excluidos de toda mediana; son `test1_roi` con `ΔL≤0` en todos los píxeles (magnitud 0, no publicados) |
| records con lista al tope de 100 | 0 | 0 | no hay truncamiento en la ventana |
| `len(ap) == n_anomalous_pixels` | 48 | 186 | el resto son `test1_roi`: `n_anomalous_pixels` cuenta `hot_mask_2d` (contextual) y `anomaly_pixels` viene de `t1_vrp_2d` — **dos máscaras distintas, no truncamiento** |
| `len(ap) < n_test1_pixels` en `test1_roi` | 245/245 | 138/138 | `build_anomaly_pixels` sólo guarda `vrp>0` (`anomaly_pixels.py:31`) y el filtro del paso 6 ya redujo la máscara: **el footprint del Test 1 (67 px) NO se persiste**; sólo el pico |
| centroide geométrico de mi grupo 8-vec reproduce `pc.centroid` (≤10 m) | 288/289 | 197/211 | confirma `clustering.py:102-103`; los fallos son mi reconstrucción por distancia (0,56 km) en píxeles off-nadir, no el pipeline |
| centroide **ponderado** reproduce `pc` (multi-píxel) | 0/3 | 1/59 | `pc` NO es ponderado |

Control positivo: Láscar `ctx_cluster` con primer pase → 0,17 km (128 records), 82,8 % MIROVA. El
instrumento distingue.

---

## 5. Tabla etapa × pasada (6 pasadas; `tabla_6_pasadas.json`)

d en km al vent. «pico» = píxel de mayor `vrp_mw` del grupo; «geo» = media lat/lon; «pond» = ponderado
por `vrp_mw`; «pc» = `primary_cluster.centroid`; «final» = `final_hotspot`.

| volcán · pasada UTC · sensor | source | n_test1 | n_ap | n_fp | n_sp | pico | geo | pond | pc | final | BT pico / t_bg | f5 MW |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Villarrica 2026-08-31 05:06 NOAA21 | test1_roi | 49 | 2 | 0 | 0 | 2,58 | 2,58 | 2,58 | 2,76 | **0,00** | 267,5 / 262,3 | 0,165 |
| Villarrica 2026-08-14 04:42 NOAA20 | test1_roi | 36 | 1 | 0 | 0 | 2,86 | 2,86 | 2,86 | 2,86 | **0,00** | 266,3 / 262,8 | 0,142 |
| Villarrica 2026-07-01 05:00 NOAA20 | test1_roi | 49 | 1 | 0 | 0 | 2,68 | 2,68 | 2,68 | 2,68 | **0,00** | **263,9 / 270,1** | 0,130 |
| Láscar 2026-06-17 05:42 SNPP | ctx_cluster | 96 | 4 | 2 | 2 | 0,10 | 0,09 | 0,05 | 0,09 | 0,09 | 288,9 / 265,7 | 0,550 |
| Láscar 2026-07-09 05:48 NOAA20 | ctx_cluster | 93 | 4 | 3 | 1 | 0,13 | 0,06 | 0,07 | 0,06 | 0,06 | 279,8 / 264,1 | 0,359 |
| Láscar 2026-07-10 05:30 NOAA20 | ctx_cluster | 83 | 3 | 2 | 1 | 0,26 | 0,14 | 0,06 | 0,14 | 0,14 | 273,5 / 264,0 | 0,249 |

En Láscar el pico está 8-23 K sobre el fondo y todo cae en <0,3 km. En Villarrica el «pico» está
1-5 K sobre el fondo o **debajo** de él, a 2,6-2,9 km, y el record se publica a 0,0 km. Nota: en la
pasada 08-31 los 2 píxeles distan 0,6 km entre sí y el pipeline los agrupó (`pc_n=2`): la grilla
regrillada de 375 m (`_regrid_viirs_granule`, `process_viirs.py:706`) es regular, así que mi umbral de
0,56 km es conservador — no afecta las conclusiones.

## 6. Cruce por camino sobre TODOS los records (denominador y ventana en cada tabla)

- Villarrica, buckets de `d_pc` (n=289): `<1 km` n=16 → 75 % con primer pase; `2-3 km` n=247 → **4 %**
  con primer pase, 92 % `test1_roi`; `≥3 km` n=9 → 67 % con second pass. La distancia al cráter y la
  ausencia de primer pase son la misma variable.
- Láscar (n=290): `<1 km` n=182 → 74 % con primer pase; `2-3 km` n=101 → 17 %, 93 % `test1_roi`.
- Rumbos y `pc≠final` (one-liner en la sesión, reproducible con `anillo_por_source.py` + este comando):
  ```
  cd "…/VRP Chile" && python -c "<bloque 'Rumbo de los picos test1_roi' — ver F3_HALLAZGOS.md §3 H1/H3>"
  ```
  (los dos one-liners están transcritos en `resultados.json → comandos_auxiliares`).

## 7. Qué NO se puede decidir sin el probe en CI (y por qué importa)

Los píxeles del Test 1 **anteriores** al filtro (los 67) no se persisten. Sin ellos no se puede medir
(i) si el cráter está dentro de `mask_contributing` (y con qué exceso) antes de que `keep_peak` lo
descarte, (ii) cuánto habría dado `(Test1 ∩ dNTI_ctx)` sin el pico, ni (iii) el perfil BT-vs-distancia
que separa «borde del disco = cota baja» de «valle tibio de un lado». Eso es lo que el probe A75 debe
capturar (`probe_etapas_ci.md`). Nada de eso cambia la afirmación central; la cuantifica.

---

## VERIFICADO LIMPIO

| qué | cómo se confirmó |
|---|---|
| El ancla de detección es el cráter en los 3 sensores | `scripts/run_pipeline.py:234,277,324` → `get_detection_anchor` (`geo_utils.py:68-71` prioriza `vent_lat/lon`); `process_viirs_mod.py:1014,1226` y `process_modis.py:1092,1382` reciben la misma ancla |
| `ctx_cluster` y cúmulo Test 1 usan la misma ancla (`vent`) | `process_viirs.py:1444-1445` (fallback catálogo sólo si `vent_lat is None`) y `:1898` |
| Gate intra-radio S85 apagado en producción | `ENABLE_SECOND_PASS_INTRA_RADIO_GATE = False` (efectivo); `ENABLE_PATH_D_INTRA_RADIO_GATE = False` |
| Test 1 NTI no corre; el MIR absoluto es el operativo | `ENABLE_TEST1_NTI_INTEGRAL = False`; `process_viirs.py:1094` llama `compute_test1_mir` |
| `anomaly_pixels` sin truncamiento en la ventana | 0 records al tope de 100 en Villarrica y Láscar (§4) |
| El centroide persistido es el que `clustering.py:102-103` dice | reproducido a ≤10 m en 288/289 y 197/211 |
| El dashboard posiciona por `final_hotspot` en fuentes honestas y usa F5' para V375 | `frontend/index.html:1513-1518, 2781-2790, 1160-1185` |
| Control positivo del instrumento | Láscar `ctx_cluster`+first pass: 0,17 km, 82,8 % MIROVA (n=128) |
| `single_pixel_mode` no toca posición | `single_pixel_mode.py:145-184` sólo reescribe `vrp_mw` |
| El rescate F47 no pisa la posición honesta | `store.py:349-358` (guard `_honest_anchor_sources`) |
| Nombres del CSV MIROVA (A14) | `Counter` en `cruce_mirova_por_clase.py`: `PlanchonPeteroa`, `Puyehue-Cordon Caulle`, `Nevados de Chillan`; sensores `MODIS/VIIRS/VIIRS375` |

No mirado (fuera de F3): paridad de magnitud contra MIROVA por pasada, MODIS/VIIRS750 (las tablas de
sources acá son sólo V375), y el `ctx_cluster` de Lastarria (A84: no reabrir).
