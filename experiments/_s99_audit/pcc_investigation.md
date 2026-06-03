# S99 — Investigación PCC: ¿qué son los >1000 MW y el ancla del lacolito es correcta?

Generado por `pcc_analyze.py` + `pcc_analyze2.py`. Datos: `pcc_result.json`, `pcc_result2.json`.
Ningún número transcrito a mano. A61 aplicada (comparación espacial lat/lon, no solo distancias).

## 0. Coordenadas de referencia (volcanoes.yaml + frontend)
- **vent (lacolito)** = (-40.525499, -72.146137) — cráter morfológico verificado en campo.
- **mirova_center** = (-40.5903, -72.1187) — centro del recuadro KMZ.
- Distancia vent↔mirova_center = **7.569 km** (offset grande, como Tupungatito).
- `inner_radius_km` = 20 (PCC). `radius_km` = 25.

## 1. ¿Qué son los ">1000 MW" / cientos de MW del mapa?

**No existe ningún record con `pc.vrp_mw` > 1000.** El máximo `pc.vrp_mw` (la magnitud
MIROVA-equivalente que la TARJETA usa) es **342.2 MW**; solo 2 records superan 100 MW con ese campo.

Lo que el usuario ve en el MAPA es otro número. El popup del marcador
(`frontend/index.html:2455`) imprime `VRP total record (suma): {recordTotalVrp} MW`, donde
`recordTotalVrp = r.vrp_mw ?? r.vrp_mir_mw`. Esos campos son la **suma scene-wide** de todos
los píxeles, no el cluster summit:
- `max vrp_mw` (suma del record) = **981.1 MW**
- `max vrp_mir_mw` (fallback de suma) = **1092.9 MW** ← el ">1000 MW" del mapa
- `max pc.vrp_mw` (cluster, lo que muestra la tarjeta) = 342.2 MW

Hay **188 records con suma-de-record > 100 MW** (todos los gigantes son **MODIS**).

### Tabla de records gigantes (top 14 por suma de record; mecanismo)
| Fecha UTC | Sensor | total(suma) | vrp_mir | pc.vrp | n_px | t_bg K | t_max K | n_dNTI_ctx | cent→vent km | dist_class |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026-01-31 08:15 | MODIS_AQUA | 981 | 824 | 231.9 | 144 | 272 | 288 | 82 | 4.93 | far |
| 2026-04-05 01:30 | MODIS_TERRA | 907 | 773 | 3.1 | 136 | 274 | 290 | 83 | 2.86 | summit |
| 2026-01-29 07:00 | MODIS_AQUA | 834 | 372 | 1.1 | 290 | 288 | 297 | 87 | 0.78 | summit |
| 2026-05-17 08:30 | MODIS_AQUA | 755 | 711 | 8.8 | 105 | 276 | 284 | 52 | 3.82 | far |
| 2026-02-14 01:35 | MODIS_TERRA | 681 | 493 | 8.3 | 172 | 272 | 285 | 76 | 1.41 | summit |
| 2026-03-08 06:40 | MODIS_AQUA | 647 | 623 | 11.9 | 78 | 284 | 291 | 14 | 4.15 | summit |
| 2026-02-21 06:55 | MODIS_AQUA | 634 | 476 | 0.8 | 167 | 288 | 293 | 31 | 3.10 | summit |
| 2026-05-29 21:35 | MODIS_AQUA | 633 | 0 | 35.8 | 100 | 279 | 285 | 18 | 4.76 | summit |
| 2026-04-26 08:20 | MODIS_AQUA | 631 | 478 | 342.2 | 165 | 270 | 286 | 68 | 5.01 | summit |
| 2026-02-13 08:20 | MODIS_AQUA | 629 | 580 | 17.6 | 84 | 279 | 289 | 26 | 5.27 | summit |
| 2026-05-22 06:50 | MODIS_AQUA | 629 | 585 | 23.5 | 90 | 280 | 286 | 28 | 4.13 | summit |
| 2026-05-09 06:45 | MODIS_AQUA | 627 | 582 | 66.8 | 95 | 275 | 287 | 19 | 4.72 | far |
| 2026-02-08 06:50 | MODIS_AQUA | 614 | 494 | 11.5 | 141 | 285 | 294 | 39 | 3.19 | summit |
| 2026-03-06 07:00 | MODIS_AQUA | 588 | 344 | 2.0 | 233 | 278 | 288 | 114 | 2.22 | summit |

**Mecanismo (clasificación A23/A18 / campo difuso warm-scene):**
- **100% MODIS** (1 km, no resuelve foco). VIIRS375 (sensor real) jamás supera ~80 MW.
- 78–290 píxeles anómalos por record, **dominados por el path D (dNTI contextual)** (14–114 px).
- Background tibio-a-frío (t_bg 270–288 K) con t_max apenas +6 a +16 K encima → contraste
  nieve/terreno/vegetación leído como anomalía por el kernel 8-vecinos.
- VRP = **suma** de todos esos píxeles 1 km → cientos de MW de un campo difuso, no de un foco.
- = **campo difuso warm-scene** (cat. b sobre-estimada, marco S86 / A23 / A18 deuda histórica).
  Es el mismo patrón ya documentado en el dashboard (`index.html:1067`, "PCC 1362/892 MW").

## 2. Comparación con MIROVA (lo que MIROVA realmente publica en PCC)
`latest_consolidado.csv`, 2028 filas PCC, 131 con VRP>0:
- VRP MIROVA con señal: **mediana 0.37 MW, media 0.47, máx 5.45 MW** a **mediana 7.83 km** del
  punto nominal GVP (= el lacolito/fisura Cordón Caulle, sub-píxel, real pero pequeño).
- Nuestra suma scene-wide MODIS (hasta 981–1093 MW) sobre-estima el foco por **factor ~180–200×**.
  Es exactamente el "el TIF/suma no es VRP per-pixel sumable" de A24 + el campo difuso A23.

## 3. ¿El ancla del lacolito es correcta vs el centroide del TIF MIROVA?

**SÍ, post-S98 nuestro ancla de detección es el lacolito (cráter), y es lo correcto.** El centroide
de NUESTRO cluster summit cae a ~1 km del vent (lacolito), no a 7.6 km en mirova_center:

| Mes | n | mediana centroide→vent | mediana centroide→mirova_center |
|---|---|---|---|
| 2026-01 | 32 | **1.12 km** | 7.75 km |
| 2026-02 | 295 | **1.14 km** | 7.77 km |
| 2026-03 | 290 | 2.07 km | 7.96 km |
| 2026-04 | 292 | **1.30 km** | 7.73 km |
| 2026-05 | 303 | **0.84 km** | 7.75 km |
| 2026-06 | 13 | 10.53 km (NRT parcial, pocos records) | 9.61 km |

El radio dibujado en el mapa nace del `v.lat/lon` (centro de referencia) y del marcador `vent_lat`
(lacolito) — el cráter, no mirova_center. **Correcto.**

### Caveat A24 sobre el TIF (importante — NO repetir el error S97)
El centroide ponderado del TIF **completo** cae cerca de mirova_center (~0.5–1.6 km), pero eso es
**artefacto del método**: el TIF es el campo de radiancia de FONDO (topografía, nieve, vegetación),
~17.900 píxeles positivos sumando miles de "MW" (A24). Su píxel más caliente está a **8–17 km del
cráter con valores ínfimos (0.2–0.7)** — terreno, no fuente volcánica. **El TIF NO sirve como mapa
de la fuente.** El ground truth correcto de la posición de la fuente es lo que MIROVA REPORTA
(mediana 7.83 km del GVP nominal = el lacolito), que coincide con nuestro vent_lat (el lacolito está
a 7.57 km de mirova_center). Es decir: nuestro vent_lat ES el lacolito que MIROVA reporta. Ancla OK.

## 4. ¿Sigue habiendo >1000 MW DESPUÉS del fix de ancla? ¿Mismo problema que Tupungatito?

- El fix S98 (`get_detection_anchor`=vent_lat) **ya aplicó a PCC** (verificado en `geo_utils.py`
  + reproc 90d ene–jun: centroide ancla al lacolito, ~1 km, en todos los meses).
- **El fix de ancla NO toca los cientos de MW.** Esos vienen de la **suma de campo difuso MODIS**
  (cuántos píxeles y cómo se agregan), no de DÓNDE está el ancla. Por eso siguen presentes
  post-fix (records de abr–may con suma 600–907 MW).
- **Es un problema DISTINTO al de Tupungatito.** Tupungatito S98 era un bug de **ubicación** (las
  detecciones caían 5.9 km al sur sobre el glaciar; el fix de ancla lo corrigió). PCC tiene el ancla
  **correcta** (lacolito) — su problema es de **magnitud**: suma de un campo difuso MODIS sobre fondo
  tibio (A23/A18), no de posición. Son dos fallas independientes que comparten el offset grande
  vent↔mirova_center pero se manifiestan distinto.

**Mitigaciones ya existentes (display-only, no tocan pipeline):** la TARJETA usa `pc.vrp_mw`
(máx 342, no la suma); el toggle "Núcleo F5'" recomputa magnitud desde el núcleo 0.75 km; el filtro
"campo difuso (fondo frío)" oculta el subconjunto cirrus. Pero el **popup del mapa** sigue mostrando
la suma cruda (`vrp_mw`/`vrp_mir_mw`) — ese es el ">1000 MW" que vio Nicolás.
