# S131 — Eje exógeno "otro sensor" (NHI, Landsat, MIROVA OLI/MSI)

**Pregunta**: ¿existe hoy, publicado y gratis, un tercer juez de alta resolución que permita
distinguir un FN real de un FN físicamente invisible para VIIRS/MODIS (A77/A78)? Eje marcado
"nunca usado" en `docs/PROTOCOLO_AUDITORIA_PROFUNDA.md:295` — los otros tres ejes exógenos
(TIF/KMZ, papers verbatim) tienen 4/4 hallazgos en 127 sesiones.

## Resultado primero

**Sí existe y sirve, con matices serios.** `MendozaVolcanic/NHI-v1` (repo hermano del mismo
autor, GitHub Pages, cron diario) publica una serie temporal cuantitativa de hot pixels SWIR
(Sentinel-2 20 m + Landsat 30 m, algoritmo Marchese et al. 2019) para 10 de los 11 volcanes
Tier A (**falta Lastarria** — no está en su lista de 43 volcanes activos, verificado contra
`config_nhi.py`). El piloto sobre 2026-02-06→09-02 (5 volcanes, régimen focal/lava-lake/
explosivo) confirma el caso de manual A77 (NdC 22-mar) y da una señal real pero **débil como
adjudicador binario**: la tasa de "alerta" NHI en nuestras detecciones-sin-respaldo-MIROVA
es, en 4 de 5 volcanes, **estadísticamente indistinguible de la tasa de fondo** de NHI en ese
mismo volcán (20-49 %, altísima porque son focos crónicos reales — fumarolas, lava lake,
dominio activo). Solo en Nevados de Chillán la tasa sube claramente sobre el fondo (25 % vs
12 % basal), coincidiendo con el período eruptivo de 2026. **Recomendación**: no cablear NHI
como gate automático pass/fail; sí incorporarlo como **panel de contexto manual** (enlace +
`alerta`/`pixeles_calientes` del día más cercano) en la auditoría S131+ para los casos FN que
el protocolo actual marca como "irreducibles" (D11/A82/A83), y como insumo del próximo caso
tipo A77/A78 cuando Nicolás reporte "erupciona y no lo vemos".

---

## 1. Inventario de fuentes candidatas

Regla de trabajo: primero lo local (`documentacion/`, `data/mirova_reference/`), después el
remote de cada repo hermano (`gh api`, nunca el checkout local — A90/regla del workspace),
nunca credenciales nuevas.

| Fuente | Publica series por volcán | Sensor / método | Cobertura Tier A | Cadencia / última data | Veredicto |
|---|---|---|---|---|---|
| **NHI-v1** (`docs/nhi_data/<Vol>/nhi_timeseries.json`) | **Sí** — lista de pasadas con `pixeles_calientes`, `alerta` bool, `fecha`, `sensor`, `cloud_cover` | SWIR Sentinel-2/Landsat 8-9, algoritmo Marchese 2019 (NHISWIR/NHISWNIR, ver detalle §2) | 10/11 (falta Lastarria) | cron diario (commits `nhi:` 2026-09-02 15:49 UTC, `toa:` 19:14 UTC, verificado `gh api .../commits`) | **Mejor candidato — usado en el piloto** |
| **NHI-v1** (`docs/nhi_data_toa/`) | Sí, variante TOA (radiancia sin corregir atmósfera, más fiel al paper original) | ídem, banda TOA | 10/11 | mismo cron, ventana rodante `dias=14` (no acumula histórico largo, verificado en el mensaje de commit) | Complemento, no reemplazo — sirve solo para los últimos 14 días |
| **Landsat-v1** (`docs/niveles_landsat.json`) | Parcial — `{fecha: "L1"/"L2"...}` categórico, no cuantitativo | `change_detection.html`, no queda claro si es térmico o multiespectral genérico (no verificado a fondo, fuera de presupuesto de esta sesión) | 43 volcanes (dict con nombre exacto) | activo (Pages verde, `MAPA_WORKSPACE.md`) | Señal secundaria/categórica, no ideal para cruce cuantitativo |
| **Mirova-v1** (scraper OCR de mirovaweb.it) | **No** — `gh api search/code?q=NPixHot+repo:MendozaVolcanic/Mirova-v1` → **0 resultados** (verificado, no supuesto — A89) | Solo CONS+OCR de las tablas VIIRS/MODIS de MIROVA, nunca las tablas OLI/MSI | — | — | Descartado para este eje; ya es la fuente MIROVA "de siempre" |
| **mirova-tif-archive** (ground truth pixel-level) | Sí, pero **mismo instrumento** — `index.csv` (4,5 MB, leído por rango de bytes) solo tiene `sensor` ∈ {MODIS, VIIRS750, VIIRS375} | MIR (igual que nosotros) | 11/11 | vivo (18 snapshots/día, según `MAPA_WORKSPACE.md`) | No es exógeno — es la misma física, otro archivo |
| **MIROVA OLI/MSI (NPixHot)** — la fuente que A77 usó vía Chrome en `mirovaweb.it` | Existe en la web de MIROVA (`volcanoDetails_OLI.php` / `_MSI.php`) pero **no está scrapeada por ningún repo del ecosistema** | Landsat OLI 30 m / Sentinel-2 MSI 20 m — el producto que MIROVA mismo usa para lo sub-píxel | ilimitada (es la fuente de A77) | manual (visita Chrome MCP) | **Gap real**: sería el juez más autorizado (mismo grupo MIROVA) pero no hay pipeline que lo persista — candidato a scraper nuevo, no a esta sesión |
| **AVTOD (Reath et al. 2019)** — `data/mirova_reference/avtod_reath2019_chile.csv` | Sí, un valor agregado por volcán | ASTER 90 m, análisis manual, °C sobre fondo | 40 volcanes chilenos, 1 fila c/u | **estático, 2000-2017** (verificado `head`, `wc -l`=18 filas) | Descartado para 2026 — es histórico, no serie temporal actual |
| **Schroeder 2014 (VIIRS 375m Active Fire)** — `documentacion/schroeder2014_...pdf` | Es el paper detrás de NASA FIRMS | **Mismo sensor VIIRS 375 m** que usamos, algoritmo distinto (no exógeno en resolución, sí en implementación) | — | — | No resuelve el problema de resolución sub-píxel; útil solo como segunda opinión algorítmica sobre el mismo granule |
| **NASA FIRMS** (VIIRS/MODIS Active Fire CSV por área) | Sí, pero requiere `MAP_KEY` (registro gratis) | Mismo sensor VIIRS/MODIS | — | — | **No descargado** — requiere credencial nueva (prohibido crear cuentas). Reportado, no ejecutado |
| **goes-volcanic-monitoring**, **Lightning-v1** | Publican FRP/rayos, no hotspots SWIR de alta resolución | GOES-19 (2 km), GLM | 11/11 | vivos | Resolución peor que VIIRS, no sirven como juez de mayor detalle |

## 2. Metodología NHI-v1 (verificada, no asumida)

`README.md` del repo (leído vía `gh api repos/MendozaVolcanic/NHI-v1/contents/README.md`):

- `NHISWIR = (SWIR2−SWIR1)/(SWIR2+SWIR1)`, `NHISWNIR = (SWIR1−NIR)/(SWIR1+NIR)` — Marchese et
  al. 2019, adaptado a reflectancia L2A (el paper original usa radiancia TOA — de ahí la
  variante `nhi_data_toa`).
- Un píxel se marca caliente si: reflectancia SWIR1/SWIR2 > 0.05 (filtra inválidos) **y**
  `NHISWIR` supera mediana+max(0.02, 3σ) **y** `NHISWIR>0` **y** `NHISWNIR>0` **y** la fracción
  de píxeles calientes de la escena es <0.5 % (antirruido nieve/sol). El propio README dice
  que el filtro estadístico está "inspirado en la metodología VRP Chile (triple-threshold
  sobre anillo de fondo)" — comparten familia de diseño, no son cajas negras independientes al
  100 %, pero sí son implementaciones separadas sobre un instrumento de resolución 15-50×
  mejor.
- Semáforo: rojo = anomalía en 7 días, amarillo = en 30 días, verde = sin anomalía en 30 días.

## 3. Piloto: cruce 2026-02-06 → 2026-09-02, 5 volcanes de régimen distinto

**Denominador y ventana explícitos (A90)**: ventana acotada al rango real que cubre el
archivo NHI descargado (`gh api .../nhi_timeseries.json`, min-max de `fecha` por volcán,
todos arrancan 2026-02-06). Match NHI↔fecha con tolerancia ±2 días (revisión combinada S2+
Landsat, más densa que el revisit puro de un solo sensor). "Detección nuestra" = noche con
`primary_cluster.vrp_mw>0` y `distance_class=="summit"` en `data/mirova_equivalent/<Vol>.json`
(pc.vrp_mw, no record.vrp_mw — A10), solo pasadas nocturnas 03-09 UTC (A76). Ground truth
MIROVA = `experiments/_s126_lib.py::cargar_mirova` (CONS∪OCR vivo, alias completos, night-only).
Script: `experiments/_s131_audit/otro_sensor/pilot_cross_check.py` → `resumen_piloto.json`.

| Volcán (régimen) | noches MIROVA | **FN vs MIROVA** (n) | de los FN, NHI dice | noches "detección-sin-MIROVA" (n) | de esas, NHI alerta / con-pasada (tasa) | tasa basal NHI del volcán (todo el archivo) |
|---|---|---|---|---|---|---|
| Láscar (focal, dominio activo) | 168 | **0** | — | 23 | 9/22 = **41 %** | 49 % (30/61) |
| Villarrica (lava lake sub-píxel) | 27 | **0** | — | 177 | 43/142 = **30 %** | 38 % (26/68) |
| Nevados de Chillán (explosivo/sub-píxel, A77) | 9 | **2** | 22-mar: NHI alerta=True a 1 día · 17-abr: NHI alerta=False a 0 días | 113 | 25/101 = **25 %** | 12 % (10/82) |
| Copahue (fumarólico) | 5 | **0** | — | 199 | 40/196 = **20 %** | 21 % (20/94) |
| Llaima (fumarólico, ruido térmico conocido) | 2 | **0** | — | 202 | 59/175 = **34 %** | 38 % (25/65) |

**Lectura del "de los FN, NHI dice"**: el 22-mar es exactamente el caso Parte C que
`project_s112_estado.md` dejó pendiente de investigar ("Parte C (22-mar 0.49): investigar por
qué Test1 no disparó") — el piloto, sin buscarlo a propósito, reprodujo evidencia
independiente de que ESE día había una señal SWIR real 1 día antes/después. Es una
confirmación de A77 con un dato nuevo, no una repetición del mismo hallazgo (el 22-mar no
había sido cruzado antes contra NHI). El 17-abr, en cambio, NHI tampoco ve nada el mismo día
— consistente con "señal bajo el piso incluso para el instrumento de mayor resolución", no
necesariamente un FN nuestro.

**Lectura del lado "detección-sin-MIROVA" (n=23 a 202 según volcán, total 714 noches)**: en
**4 de 5 volcanes** (Láscar, Villarrica, Copahue, Llaima) la tasa de alerta NHI en esas noches
es **estadísticamente igual a la tasa basal** de NHI para ese volcán en todo el período — la
diferencia máxima es 8 puntos porcentuales sobre bases de 20-100 noches, dentro del ruido de
un evento binario con esa n. Esto significa que NHI **no está confirmando ni refutando** esas
detecciones por encima de lo que ya "dice siempre" de ese volcán — es evidencia consistente
con A54 (la mayoría son features térmicas reales y crónicas — fumarola, dominio, lava lake —
tanto para VRP Chile como para NHI, ninguno de los dos las llama "anomalía nueva" con más
frecuencia que su propio ruido de fondo). Solo **Nevados de Chillán** muestra una tasa **2×
por sobre su basal** (25 % vs 12 %) — coincide con la ventana eruptiva de 2026 documentada en
`project_s112_estado.md`, y es la señal más creíble de que ahí SÍ hay algo que NHI está
viendo por encima de su ruido propio.

**Caveat metodológico, no escondido**: la tasa basal de alerta de NHI es alta (12-49 %) para
volcanes que SERNAGEOMIN no reporta en erupción sostenida — se revisó si era contaminación de
nube (`cloud_cover` mediana de las pasadas con `alerta=True` es 0.6-14.9 %, **no** mayor que
las pasadas sin alerta en 4/5 volcanes) — no es un artefacto de nube obvio. Es más consistente
con que estos volcanes SÍ tienen fumarolas/dominios calientes crónicos visibles en SWIR de
alta resolución, que es justamente el fenómeno que A54 ya documentó del lado VRP Chile. No se
alcanzó a verificar visualmente (mirar los PNG `*_hotspot.png` que el repo también publica)
si esas alertas caen exactamente en el cráter o en un área más amplia — pendiente si se
adopta el eje.

## 4. Veredicto de viabilidad

**¿Vale la pena integrar como cross-check permanente (cron/CI, patrón sparse-checkout)?**

- **No como gate automático pass/fail.** La tasa basal de NHI es demasiado alta y su
  "alerta" no discrimina limpiamente detección-real de ruido-propio en 4/5 volcanes del
  piloto — cablearlo como criterio de aceptación/rechazo repetiría el error que A83 ya
  documentó puertas adentro (buscar un discriminante físico único cuando el terreno es
  régimen-dependiente), esta vez importado de otro repo.
- **Sí como panel de contexto en la auditoría manual**, con costo bajo: un script que, dado
  un FN o una racha de detección-sin-MIROVA, busque la pasada NHI más cercana (±2 días) y
  muestre `alerta`, `pixeles_calientes`, `cloud_cover` y el link al PNG (`docs/nhi_data/<Vol>/
  <fecha>_{s2,ls}_hotspot.png` — confirmado que existen, ver Villarrica §listing). Esto es
  exactamente el patrón que ya funcionó ad-hoc en S112 (A77) pero manual vía Chrome; acá
  queda reproducible con `gh api`/curl, sin browser.
- **Costo de mantenerlo vivo**: bajo. NHI-v1 corre solo (cron diario, Pages, sin secrets —
  `MAPA_WORKSPACE.md` lo marca 🟢), y su output ya es JSON estructurado — no hace falta
  scraping de HTML. El patrón `sparse-checkout` de `Copernicus-v1/.github/workflows/
  change_analysis.yml` aplicaría literal: `sparse-checkout: docs/nhi_data` sobre
  `MendozaVolcanic/NHI-v1`.
- **Qué preguntas SÍ responde**: "¿había algo caliente visible en alta resolución cerca de
  esta fecha, sí o no?" — útil para el caso puntual tipo A77/A78 ("erupciona y VRP no lo ve").
  **Qué NO responde**: no da una magnitud comparable a VRP_MW (píxeles calientes ≠ vatios), su
  cadencia es de días (S2 ~5 d, Landsat ~16 d, combinados ~3-5 d) — nunca va a cubrir cada
  pasada VIIRS de 2 h, y su cobertura excluye Lastarria.
- **Gap real detectado, distinto de NHI**: el producto OLI/MSI **del propio MIROVA** (el que
  A77 usó) sería el juez más autorizado — mismo grupo, mismo criterio que ya validan contra su
  propio VRP — pero **no está scrapeado por ningún repo**. Vale la pena como backlog aparte
  (no de esta sesión): un scraper liviano de `volcanoDetails_OLI.php`/`_MSI.php` por volcán,
  con la misma cadencia que Mirova-v1 usa para VIIRS/MODIS.

**Recomendación concreta**: no abrir un PR de integración operacional ahora. Sí:
1. Dejar este script (`experiments/_s131_audit/otro_sensor/pilot_cross_check.py`) como base
   para un helper de auditoría bajo demanda (no cron) que cualquier sesión futura pueda correr
   dado un FN puntual — sin necesidad de reabrir Chrome MCP cada vez.
2. Anotar en `docs/PROTOCOLO_AUDITORIA_PROFUNDA.md` el registro de ejes: "evidencia exógena:
   otro sensor" pasa de "nunca" a **1 uso, rendimiento medio** (confirmó A77/NdC 22-mar con
   evidencia nueva; no discrimina limpio en 4/5 volcanes; expone el gap OLI/MSI no scrapeado).
3. Backlog separado (no bloqueante): evaluar scraper de MIROVA OLI/MSI si el caso A77-style se
   repite — ahí sí habría un juez de la misma autoridad que MIROVA, hoy inexistente como dato
   persistido.

## Archivos de este eje

- `experiments/_s131_audit/otro_sensor/nhi_raw/*.json` — 10 timeseries NHI-v1 descargadas del
  remote (Copahue, Chaiten, Isluga, Lascar, Llaima, Nevados_de_Chillan, Planchon-Peteroa,
  Puyehue_-_Cordon_Caulle, Tupungatito, Villarrica).
- `experiments/_s131_audit/otro_sensor/pilot_cross_check.py` — script del piloto (read-only,
  reusa `experiments/_s126_lib.py`).
- `experiments/_s131_audit/otro_sensor/resumen_piloto.json` — conteos crudos por volcán.
- `experiments/_s131_audit/otro_sensor/pilot_output_feb_sep.txt` — stdout completo del piloto,
  ventana 2026-02-06→09-02 (incluye el detalle fecha-por-fecha de cada FN y cada
  detección-sin-MIROVA para los 5 volcanes).
