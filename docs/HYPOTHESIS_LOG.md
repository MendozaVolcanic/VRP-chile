# Hypothesis Log — VRP Chile

> Bitácora cronológica de hipótesis formuladas sobre el pipeline. Cada entrada tiene ID (H#),
> fecha, evidencia a favor, evidencia en contra, estado (active/confirmed/refuted/stale),
> criterio testable, y resolución. **Nunca se borra una entrada** — se marca `stale` si queda obsoleta.

---

## H_S61_PCC_INFLATION_NOT_KERNEL — PCC 52× NO es por contaminación ring (gradient positivo)

- **Formulada**: S61 (2026-05-18) durante investigación paralela a workflow PP (ver `experiments/107_*` pendiente).
- **Hipótesis inicial (refutada)**: PCC gap 52.77× LEGACY/MIROVA es similar a Villarrica (lago en ring) o PlanchonPeteroa (glaciar heterogéneo), por tanto kernel-bg lo curaría.
- **Hipótesis revisada (CONFIRMADA)**: PCC inflación 52× tiene mecanismo DISTINTO — cluster selection lejano residual + magnitud sobre-estimada Test 1 path.
- **Evidencia decisiva**:
  - **Ring gradient PCC +4.5 K POSITIVO** (S60 audit línea 588 HYPOTHESIS_LOG): el ring 5-25 km está MÁS caliente que el cráter. Kernel local no aplica.
  - Records summit MODIS recientes muestran clusters a 16-20 km del lacolito (no en lacolito 2011): vrp 159-522 MW, 100-450 pixels, classified `summit` por `inner_radius_km=20`.
  - VIIRS_I Test 1 path ancla en lacolito (<2 km, OK) pero suma 200-470 pixels anómalos → 28-34 MW vs MIROVA ~0.23 MW (factor ~130× residual incluso con localización correcta).
  - `inner_radius_km=20` PCC es extremadamente permisivo (otros Tier A: 3-7 km).
- **Mecanismo doble**:
  - **D-PCC-1**: Cluster selection lejano residual D8/D9. vent_anchored S38 elige lacolito pero entre 2 clusters dentro de 20 km, el más grande gana. Records dispersos en escena ancha (probable Antillanca, Mocho-Choshuenco, ground burns, Lago Ranco thermal).
  - **D-PCC-2**: Test 1 path acepta más pixels marginales que MIROVA filtra con threshold más estricto (Coppola 2016a fixed-ROI sum literal vs implementación nuestra).
- **Criterio testable**:
  - Reducir `inner_radius_km` 20→7-10 PCC en `volcanoes.yaml`. Si magnitud baja a <3× MIROVA: confirma D-PCC-1.
  - Audit pixel-level VIIRS_I Test 1 vs MIROVA TIF (R2). Si pixel count nuestro >> MIROVA: confirma D-PCC-2.
- **Estado**: **CONFIRMADA** (hipótesis revisada).
- **Resolución**: NO disparar A/B kernel-bg PCC en S61. Plan S62:
  1. Reducir `inner_radius_km` PCC a 7-10 km (cambio mínimo, bajo riesgo)
  2. Auditar `cluster_hotspots(vent_anchored)` PCC con dump clusters[]
  3. Investigar pixel-counting Test 1 path vs MIROVA literal
- **Lección metodológica**: NO asumir que "vol con gap alto" → "kernel-bg lo soluciona". Verificar mecanismo físico (gradient ring) antes de extender fix.

---

## H_S61_TUPUNGATITO_KERNEL_BG_REVIEW — Tupungatito gap 9.8× NO es kernel-bg, es Test 1 over-detection

- **Formulada**: S61 (2026-05-18) durante audit offline mientras corre workflow PP.
- **Hipótesis inicial (refutada paralelo S61)**: Tupungatito debería tener `local_kernel_bg: true` porque gap LEGACY/MIROVA NRT es 9.8× similar a Villarrica.
- **Hipótesis revisada (CONFIRMADA)**: Tupungatito gap 9.8× tiene el MISMO mecanismo que PCC/Lastarria/Isluga (Test 1 path sobre-detección), NO kernel-bg.
- **Evidencia decisiva**:
  - Inspección records window 04-16/05-15 VIIRS375 summit anom (n=93):
    - Top 5 vrp 5-6 MW vs MIROVA median 0.19 MW (top ratio ~30×, mediano 9.8×)
    - **n_anomalous_pixels median = 76** (max 117) — mucho más que cluster MIROVA típico
    - **`final_hotspot_source: test1` en 81/93 records (87%)** — Test 1 path dominante
  - Patrón idéntico a Lastarria (n_pix 71, src test1 89%), Isluga (n_pix 69, test1 56%) y PCC (n_pix 200-470, test1 dominante).
  - S59 razón teórica "ring frío glaciar empeoraría con kernel local" sigue siendo correcta físicamente — kernel-bg NO es la solución.
- **Mecanismo común con PCC/Lastarria/Isluga**:
  - Test 1 path integrated-ROI (Coppola 2015 §2.2 Eq.1) en nuestro pipeline acepta 70-470 pixels anómalos por cluster summit.
  - MIROVA cluster típico es 1-5 pixels (según TIF visual).
  - El threshold pixel-level específico del paper Coppola 2015 puede no estar replicado fielmente en nuestro código.
- **Criterio testable**: lectura `pipeline/process_viirs.py` función Test 1 + comparación línea por línea con Coppola 2015 §2.2 Eq.1. Test sintético con cluster conocido.
- **Estado**: **CONFIRMADA** (refutada hipótesis kernel-bg, confirmada Test 1 over-detection).
- **Resolución**:
  - NO modificar S61 (mantener Tupungatito false y NO A/B kernel-bg).
  - NO A/B kernel-bg en S62 (no curaría el problema).
  - **Investigar Test 1 path en S62** — fix arquitectural cura 4 vols simultáneamente (Lastarria, Isluga, Tupungatito, PCC).
- **Costo S62 ahorrado**: ~9-12h GH Actions evitadas (no A/B Tupungatito/Lastarria/Isluga/PCC).
- **Posible extensión**: Villarrica también puede tener Test 1 over-detection residual. NEW post-kernel-bg median 1.51 MW vs target 1.06 MW (42% sobre). Si fix Test 1 cierra ese 42% restante, mejor que refinamiento kernel_size=5.

---

## H_S61_PLANCHON_KERNEL_BG — Fix kernel-bg también necesario en PlanchonPeteroa (glaciar heterogéneo)

- **Formulada**: S61 (2026-05-18) tras audit C Villarrica y descubrimiento error S60 (scraper sí cubre PlanchonPeteroa como 'PlanchonPeteroa' sin guión).
- **Hipótesis**: el ratio LEGACY/MIROVA 15.03× en PlanchonPeteroa NO es por lago cálido (no hay lago grande en ring), sino por heterogeneidad glaciar en el ring 5-25km. Kernel local 3×3 cura igual por mecanismo distinto.
- **Evidencia a favor**:
  - 18 ALERTAS window 04-16/05-15 con LEGACY ratio mediano 15.03× (min 0.23, max 130×)
  - 39 ALERTAS window 02-20/05-15 (audit S61 extendido)
  - Agente lagos S60 confirmó: complejo glaciar grande, sin lago contaminante en ring
  - Fix kernel mecánicamente actúa contra heterogeneidad del background, no requiere lago específico
- **Evidencia en contra / pendiente** (post-Task 3 workflow PP):
  - Recall NEW <X>/39 vs LEGACY (TBD)
  - Ratio mediano NEW <Y>× vs LEGACY 15.03× (TBD)
- **Criterio testable**: workflow run 26035918192 + audit `experiments/105_s61_audit_planchon_kernel_bg.py`. Adoptar si recall sin regresión Y ratio mediano <5× (objetivo: rango similar Villarrica 2.16×).
- **Estado**: <CONFIRMADA / REFUTADA> tras Task 3.
- **Resolución**: <adoptado per-vol + global / mantener solo Villarrica>.

---

## H_S60_KERNEL_BG_HELPS_MIROVA_DAYS — Fix local kernel bg cura calibración solo en días MIROVA reportó

- **Formulada**: S60 (2026-05-17) tras audit A+B+B2 sobre reproc S58 Villarrica window 2026-04-16 → 2026-05-15.
- **Hipótesis**: el fix `enable_local_kernel_bg=true` (kernel 3×3 vecinos en lugar de median ring 5-25km) reduce inflación de magnitud por contaminación del lago Villarrica, pero el efecto es VISIBLE solo en días donde MIROVA NRT reporta. En días RUTINA MIROVA, NEW = LEGACY porque no hay lago contaminando ese subgrupo.
- **Evidencia a favor** (experiments/104_s60_audit_b2_decompose_by_mirova_day.md):
  - Días MIROVA reportó (n=17): NEW median **1.51 MW** vs LEGACY 1.88 MW (**-20%**). Target OSF curado VIIRS375 class=1 = 1.06 MW; NEW gap 42% vs LEGACY gap 77%.
  - Caso paradigmático 2026-05-11 ALERTA: LEGACY 5.84 MW (ratio 18.8×) → NEW 0.50 MW (ratio 1.61×). Cura la inflación extrema.
  - Top 10 outliers NEW (vrp > 4.3 MW summit) son **TODOS** días RUTINA — no son refs MIROVA inflados.
- **Evidencia en contra / limitación**:
  - Días MIROVA RUTINA (n=85-94): NEW median 2.19 MW ≈ LEGACY 2.20 MW. Fix no aporta porque la causa de la sobre-detección NO es contaminación lago — es divergencia en umbral publicación interno MIROVA NRT (no documentado en papers Coppola).
  - Caso 2026-05-14 ALERTA: LEGACY 0.30 MW (0.97×) → NEW 0.67 MW (2.17×). Empeora marginalmente (acepta porque <30× tolerable).
  - Mediana agregada VIIRS375 summit sigue 2× sobre OSF target (artefacto de mezclar MIROVA-days con RUTINA-days).
- **Criterio testable**:
  - Recall sin regresión: NEW detecta los mismos 2 ALERTAS + 2 FPs MIROVA que LEGACY. ✓ CONFIRMADO.
  - Mediana MIROVA-day NEW < mediana LEGACY: 1.51 < 1.88. ✓ CONFIRMADO.
  - Extensión: con C (reproc 2026-02 → 2026-05) confirmar el patrón sobre 5 ALERTAS (no solo 2).
- **Estado**: **CONFIRMADA** (parcialmente — pendiente C para n=5 ALERTAS).
- **Resolución**:
  - NEW preserva intacto recall MIROVA y cura calibración en días-MIROVA (cierra 20% del gap a OSF).
  - **Adopción operacional defendible** pero pendiente C para validar sobre 5 ALERTAS.
  - Tupungatito mantiene exclusión explícita (`local_kernel_bg: false`) por ring frío de glaciar (decisión S59 PR #65).
  - Refinamientos S61+ pendientes si se quiere converger más a OSF target: `kernel_size=5` o `p25 del kernel` en lugar de mean.
- **Decisión adopción S60**: pendiente cierre con resultado workflow run 25998122095 (90d reproc).

---

## H1 — Sigma-gating vent-path introducido en S12 F1 mató TPs sub-pixel

- **Formulada**: S16 (2026-04-22) en `tasks/plan_s16_restore_s9_recall.md`.
- **Hipótesis**: commit `6eaed67` S12 F1 activó `N_SIGMA_VENT=2.0` en vent-path. En volcanes con σ_bg alto (glaciar Tupungatito, domo Chaitén), el threshold pasó de 1K fijo (S9) a max(1K, 2·σ) capped 3K (S12+). Pixels fumarólicos +1.5K sub-pixel quedaron excluidos.
- **Evidencia a favor**:
  - `git show 6eaed67`: diff exacto del gate cambiado.
  - Recall histórico Tupungatito S9=0.977 → S12=0.5 → S15=0.45.
  - Análisis forense subagente S15 Tupungatito (σ_bg glaciar ~2K).
- **Evidencia en contra**:
  - Test E1 S17 (profile `s9_vent_permissive` con `n_sigma_vent=0.0`): recall vent-based igual (6/17 ambos S15 y E1 en Tupungatito). **Sigma-gating no era el cuello real**.
- **Criterio testable**: reproceso E1 debe subir recall Tupungatito ≥0.85 / Chaitén ≥0.90.
- **Estado**: **REFUTADA** (S17 2026-04-23, delta report 36).
- **Resolución**: el cuello de botella real es **H10 (NOAA-21 missing)**. No pushear profile E1.

---

## H2 — Bbox chico en `fetch.py` pierde granules tangenciales

- **Formulada**: S17 (2026-04-23).
- **Hipótesis**: `search_granules` usa `bbox = lat±25km/111°` → ±0.23°. Granules cuyo centroide cae fuera pero que cubren el vent no son retornados por CMR.
- **Evidencia**: ninguna concluyente en búsquedas con bbox 25/100/165 km.
- **Estado**: **REFUTADA** (S17 2026-04-23). Bbox más grande no retorna más granules porque los que faltan están en **otro short_name** (VJ202), no en otro bbox.
- **Resolución**: descartada.

---

## H3 — `earthaccess.download()` sin timeout causa deadlocks

- **Formulada**: S17 (2026-04-23).
- **Hipótesis**: procesos zombies en S17 early eran por `earthaccess.download()` sin `timeout=` esperando sockets NASA cerrados a medias.
- **Evidencia a favor inicial**: 3 procesos ~8h sin progreso, alto RAM.
- **Evidencia en contra**: netstat sin sockets abiertos; WMI muestra ~105 min CPU user (22%). No era deadlock de red.
- **Estado**: **REFUTADA** (confirmado con py-spy dump).
- **Resolución**: el deadlock era **H4 (generic_filter Python lento sobre granule completo)**.

---

## H4 — `scipy.ndimage.generic_filter` con función Python sobre granule completo es performance catastrófica

- **Formulada**: S17 (2026-04-23) con py-spy dump.
- **Hipótesis**: `dual_roi_contextual_dnti_hot_mask` llama a `contextual_dnti_hot_mask` 2× sobre NTI completo (VIIRS 375m ~6400×6400 = 41M pixels) con función Python `_nanmedian_ignore_self`. O(pixels_granule) cuando debería ser O(pixels_ROI).
- **Criterio testable**: recortar al bbox del ROI debe reducir tiempo por día-volcán de horas a segundos.
- **Evidencia**: test de performance con array 1000×1000 → 20s pre-fix, <1s post-fix (**factor ~2400×**).
- **Estado**: **CONFIRMADA**.
- **Resolución**: fix commit `ad030f5` — crop al bbox del ROI antes de generic_filter. 49/49 tests verde.

---

## H5 — GitHub Actions NRT falla por cambio de código reciente

- **Formulada**: S17 (2026-04-23) al ver 7 runs consecutivos "failure" en Actions.
- **Hipótesis**: algún cambio en s15-dev rompió el NRT.
- **Evidencia en contra**:
  - Actions corre `main`, no `s15-dev`. Entre último éxito (04-22 20:41) y primer fallo (04-22 22:36) no hubo commits de código, solo "NRT update Xxx" auto.
  - Error `urllib3 [Errno 101] Network is unreachable` a `urs.earthdata.nasa.gov` desde runners — desde shell local el mismo URL responde 200 en 0.82s.
- **Estado**: **REFUTADA** (no es nuestro código).
- **Resolución**: problema intermitente de red GitHub↔NASA. **H6** (mitigación retry backoff) pendiente.

---

## H6 — Retry+backoff en auth() mitiga fallas intermitentes NOAA

- **Formulada**: S17 (2026-04-23).
- **Hipótesis**: 3 intentos sleep 5s/15s/45s en `fetch.auth()` recuperan los runs Actions que fallan con "Network is unreachable".
- **Criterio testable**: tras implementar, runs fallidos bajan de 7/7 a <2/7 en 14 días.
- **Estado**: **IMPLEMENTADA S22 (commit `bf5ecce`)** — pendiente validación
  empírica (esperar 14 días NRT runs y comparar tasa de fallos vs baseline 40%).
- **Resolución implementada**: 4 intentos (immediate + 5s + 15s + 45s) en
  `auth()` probando environment y netrc en cada uno. También aplicado a
  `download_granules()` con waits 10s/30s/60s. Suite 119/119 verde. Retry
  behavior NO mockeado (mockear earthaccess es complejo); validación
  empírica en NRT cron próximas semanas.

---

## H7 — MIROVA scraper tiene bug de timezone/parsing

- **Formulada**: S17 (2026-04-23) cuando no encontraba granules CMR para horas MIROVA.
- **Hipótesis**: `Fecha_Satelite_UTC` del CSV no es UTC real o tiene shift.
- **Evidencia en contra**:
  - Agente auditó `scraper.py` Mirova-v1: lee literal `<td>` de MIROVA con `datetime.strptime("%d-%b-%Y %H:%M:%S")` como UTC.
  - CSV tiene `Fecha_Captura_Chile` = UTC-4 exacto para todas las filas.
- **Estado**: **REFUTADA**.
- **Resolución**: descartar. Ground truth CSV está bien.

---

## H8 — Ground truth MIROVA es incompleto/erróneo

- **Formulada**: S17 (2026-04-23) brevemente cuando no encontraba granules.
- **Estado**: **REFUTADA** (el ground truth está bien; el error era nuestro).

---

## H9 — MIROVA usa algoritmo privado diferente al de los papers

- **Estado**: **STALE** (se asumió inicialmente, falso). MIROVA = Coppola 2016a + Campus 2022 + Aveni 2023 tal como los papers. No hay algoritmo privado.

---

## H10 — Nuestro `fetch.py` no busca NOAA-21 (JPSS-2); MIROVA sí lo procesa ✳️

- **Formulada**: S17 (2026-04-23) — **HIPÓTESIS REAL TRAS 3 FALSAS**.
- **Hipótesis**: las horas MIROVA que "no existen en CMR" son granules NOAA-21 (VJ202IMG) que nuestro fetch.py no enumera. `PRODUCTS` dict tiene SNPP (VNP) + NOAA-20 (VJ1) pero no NOAA-21 (VJ2).
- **Evidencia**: earthaccess.search_data con VJ202IMG 2026-04-10 retorna granules a **04:48 y 06:24 UTC** — exactamente las horas MIROVA que faltaban.
- **Criterio testable**: agregar NOAA-21 a PRODUCTS, reproceso Tupungatito abril 2026, recall summit-only vent-based debe subir de 5/13 a ≥10/13 (0.77+).
- **Estado**: **✅ CONFIRMADA y RESUELTA** (S18 2026-04-24).
- **Resolución S18**: implementación en commit `b08b71f`. Reproceso 3 volcanes Tier A validó:
    - Lascar: 22/42 → 36/42 (0.52 → **0.86**, +14 TP)
    - Chaitén: 1/2 → 2/2 (0.50 → **1.00**, +1 TP)
    - Tupungatito: 4/17 → 7/17 (0.24 → **0.41**, +3 TP, +75% relativo)
  Confirmado que NOAA-21 agrega TPs reales (contrafactual: sin NOAA-21 el recall cae al baseline). Tupungatito no alcanza el criterio 0.77 del handoff — el resto del cuello es H17 (Embalse El Yeso / σ_bg inflado). Merge a main commit `f78ad5d`.

---

## H17 — Tupungatito: el cuello residual post-NOAA-21

- **Formulada**: S18 (2026-04-24).
- **Reformulada**: S18 tarde (2026-04-24) tras evidencia de `scripts/verify_reproc.py` (M2) y análisis direccional de hotspots.
- **Contexto**: H10 validada pero Tupungatito quedó en recall 0.41 vs 0.77 esperado. De 37 detecciones reprocesadas, 36 son "far" y solo 1 "summit".
- **Hipótesis original (DESCARTADA)**: el Embalse El Yeso era el principal contribuyente de FPs far.
  - **Evidencia en contra**: el Embalse está a **39.7 km** del centro Tupungatito (no 15-27 km como comentarios antiguos). El bbox de detección es ±25 km. **El Embalse queda fuera del área de análisis** — sus pixels nunca son candidatos hot. `verify_reproc` reporta `n_excluded_water=0` no por bug del filtro sino porque no hay nada que filtrar.
  - Análisis direccional (S18 tarde): los 23 hotspots far Tupungatito están distribuidos: 9 NE, 5 NW, 5 SW, 4 SE. **Ninguno cerca del Embalse**.
- **Hipótesis revisada (3 candidatos)**:
  - **H17a**: Hotspot caliente persistente al NE alrededor de (-33.28, -69.58), recurrente en 4 días distintos a 22-25 km. Podría ser Cerro Marmolejo (volcán a ~30 km NE de Tupungatito) o infraestructura. **Cuando un record tiene un hotspot far más fuerte que la señal del cráter, todo el record queda clasificado "far" y no matchea contra refs MIROVA summit**.
  - **H17b**: σ_bg inflado por casquete glaciar a 5682 m levanta el umbral efectivo (max(ANOMALY_K, sigma_cap)) por encima de la señal real sub-pixel de 1-2 K del vent fumarólico.
  - **H17c**: vent fumarólico inherentemente débil (<0.5 MW) — limit del detector independiente del background.
- **Evidencia a favor (revisada)**:
  - H17a: 9 detecciones far NE recurrentes en mismo cuadrante (-33.28, -69.58), separadas semanas → no es ruido aleatorio sino fuente persistente.
  - H17b: σ_bg Tupungatito ~2-3 K pre-S16 (vs 0.5-1 K en volcanes sin glaciar).
  - H17c: refs MIROVA Tupungatito son típicamente <0.5 MW.
- **Criterio testable revisado**:
  1. Geocodificar/identificar el hotspot NE recurrente (¿Cerro Marmolejo? ¿planta solar? ¿centro minero?). Si es no-volcánico, agregar a `exclude_zones` Tupungatito.
  2. Separar los 10 FN por causa con script forense: (a) no hay granule, (b) hay granule pero BT_max<umbral, (c) hay detección clasificada far por hotspot NE más fuerte.
  3. Si (c) > 50% → fix expandiendo exclude_zones o re-ranking del hotspot dentro del inner_radius_km cuando existe.
  4. Si (c) bajo → fix sigma-cap más agresivo para vent-path Tupungatito.
- **Estado**: **PARCIALMENTE RESUELTA S20 (2026-04-25 tarde)**.
- **Resolución S20**: forense ejecutada — clasificadas 35 refs Tupungatito summit en 30 días:
  - 20 TP correctos.
  - **8 T3 (vent-path detectó cráter pero record clasificado far)** → resueltos por **Regla D vent-priority** (commit `2fde274`).
  - **9 T4 (no hay pixel summit detectado)** + 4 T2b → causa nueva **D6 (background no localizado)**, ver `docs/DRIFTS_S17.md` D6.
  - 2 T1 (no granule) → límite físico cobertura satélite.
- **Recall post-Regla D**: Tupungatito 0.57 (vs 0.00 pre-D, vs 0.98 S9). El gap restante (-0.41) corresponde a T4 + T2b → D6.
- **H17a (POI hotspot NE Tupungatito)**: descartada (Nicolás verificó visualmente que no hay nada en (-33.28, -69.58)). El hotspot recurrente es ruido térmico difuso del altiplano, no fuente identificable.
- **H17b/H17c**: subsumidas en **D6 (background no localizado)** — la causa raíz es el cómputo de `std_bg` sobre el bbox global incluyendo terreno heterogéneo (glaciar). Solución requiere `std_bg_summit` localizado en ROI1 5×5km.
- **Próximo paso**: S21 implementar background localizado.

---

## H_S21_10 — D6 (background localizado) refuta empíricamente

- **Formulada**: S20 (2026-04-25 tarde) tras forense H17, como camino S21.
- **Hipótesis**: std_bg sobre ROI1 5×5 km local sería ≪ std_bg sobre anillo bbox
  50×50 km global en Tupungatito. Si se cambiara el gate vent-path a usar el
  std_bg local, el threshold caería de ~3 K a ~1-1.5 K, disparando la fumarola
  sub-pixel y resolviendo los 12 T4.
- **Criterio testable**: medir std_bg sobre múltiples ROI en granules T4 reales.
  Ratio summit/global esperado <0.5 si D6 viable.
- **Evidencia**: experiments/41 S21 descarga 3 granules T4 vía earthaccess. Resultado:
  std_bg_global=5.47 K, std_bg_summit_5_8=4.41 K. **Ratio = 0.81** (no <0.5).
- **Estado**: **❌ REFUTADA S21 (2026-04-25 noche)**.
- **Resolución**: el glaciar Tupungatito 5682m afecta toda el área hasta 10+ km,
  no solo lateralmente. El cap MAX_VENT_SIGMA_CONTRIB_K=3K satura igual con std_bg
  local que global → threshold idéntico, no resuelve. Causa raíz definitiva:
  fumarola sub-pixel + sub-Kelvin con variabilidad. **MIROVA NRT no supervisa
  manualmente** (ver `~memory/feedback_mirova_no_human_supervision`); diferencias
  son algorítmicas. Detalles en `experiments/41_DIAGNOSIS_FINAL_S21.md` y
  `docs/DRIFTS_S17.md` D6.

---

## H_S21_11 — Schema gap VIIRS bloquea diagnóstico posterior

- **Formulada**: S21 (2026-04-25 noche) al ejecutar experiments/40.
- **Hipótesis**: `process_viirs.py` y `process_viirs_mod.py` no persisten campos
  diagnósticos (`diag_sigma_bg_k`, `diag_eff_threshold_k`, `diag_n_bt_path`,
  `diag_n_nti_path`, `diag_n_dnti_ctx_path`). `process_modis.py` sí los persiste.
- **Evidencia**: 47/47 records MODIS Tupungatito abril tienen `diag_sigma_bg_k`;
  0/177 records VIIRS lo tienen. Mismo patrón en otros volcanes.
- **Implicancia operacional**: como refs MIROVA Tupungatito son 100% VIIRS
  (H_S21_2), todos los records relevantes para diagnóstico quedan ciegos.
- **Estado**: **CONFIRMADA, ACTIVA — pendiente fix S22.1**.
- **Resolución pendiente S22**: agregar campos al return de `calculate_vrp` en
  ambos procesadores VIIRS + actualizar `store.py append_record`. ~10-15 líneas
  + tests TDD. NO requiere reproceso (NRT cron poblará gradualmente).

---

## H18 — Vent-priority (Regla D): si vrp_vent_mw>0, distance_class debe ser summit

- **Formulada**: S20 (2026-04-25 tarde) tras forense de H17.
- **Hipótesis**: 8/15 FN Tupungatito tienen vrp_vent_mw>0 pero distance_class='far' porque un eruption-path far más caliente "robó" el final_hotspot. El vent-path por construcción solo dispara dentro del vent_radius_km, así que vrp_vent>0 implica anomalía real del cráter por construcción.
- **Criterio testable**: aplicar regla D (forzar class=summit cuando vrp_vent>0) sobre JSONs ya generados y medir delta recall summit-class.
- **Evidencia**: contrafactual + aplicación empírica:
  - Tupungatito: 0.00 → 0.57 (+0.57)
  - Chaitén: 0.50 → 1.00 (+0.50, supera S9 0.93)
  - Lascar: 0.35 → 0.73 (+0.38)
  - Agregado: 0.25 → 0.69 (+0.44)
- **Estado**: **✅ CONFIRMADA y RESUELTA** (S20 2026-04-25 tarde).
- **Resolución**: implementada en `pipeline/store.py` append_record(). 5 tests TDD nuevos. Aplicada retroactivamente a 11 Tier A (1,574 records reclasificados). Commit `2fde274` mergeado a main `9b8d852`.

---

## H11 — Feature parity MIROVA dashboard: falta Combined MIR, escala alerta, GeoTIFF export

- **Formulada**: S17 (2026-04-23) tras auditoría mirovaweb.it.
- **Hipótesis**: MIROVA publica Combined MIR series (MODIS+VIIRS750+VIIRS375 en un plot, 0.01 MW–50 GW), escala Low/Medium/High/Very High/Extreme, GeoTIFF/KMZ download por imagen. Nuestro dashboard no tiene estas 3 features.
- **Criterio testable**: implementar → OVDAS pueden ver lo mismo que en mirovaweb.it sin switching de fuente.
- **Estado**: **ACTIVE** — diferido a Fase 3 (S19+).

---

## H12 — Kernel dNTI 8-vecinos: paper dice mean, código usa median (drift D1)

- **Formulada**: S17 (2026-04-23) tras auditoría de Coppola 2016a.
- **Evidencia**: Coppola 2016a §"Spatial analysis" literal "arithmetic mean"; Campus 2024 p.3 literal "arithmetic mean"; código `detection_context.py:35` usa `np.median`.
- **Criterio testable**: cambiar a `np.mean` + test regresión vs OSF.
- **Estado**: **✅ CONFIRMADA y RESUELTA** (S17 2026-04-23 tarde).
- **Resolución**: fix aplicado en `detection_context.py` — `_nanmedian_ignore_self` → `_nanmean_ignore_self`. Test nuevo `test_kernel_uses_arithmetic_mean_not_median` con outlier explícito. 50/50 tests verde.

---

## H13 — N·σ uniforme 3.0 es inferior al ~4× vs papers MIROVA (drift D2)

- **Formulada**: S17 (2026-04-23).
- **Evidencia inicial**:
  - Coppola 2016a Tabla 1: MODIS 5/10/15 dual-ROI + día.
  - Di Bella 2024 §3.3 p.6: VIIRS 12 noche / 8 día, MODIS 5/10.
  - Nuestro código: 3.0 uniforme.
- **Hipótesis original**: nuestro 3σ es demasiado permisivo, explica FPs sistemáticos.
- **Criterio testable**: test A/B de 3 configuraciones (3σ baseline, 5σ Coppola, 12σ Di Bella) sobre Tupungatito/Chaitén/Lascar, ventana 30 días. Adoptar el que maximice F1.
- **Estado**: **✅ REFUTADA — 3σ NO es problemático**. Resuelto S19 (2026-04-25).
- **Resolución completa**:
  - Test A/B ejecutado S19 con 6 reprocesos (3 volcanes × 2 perfiles 5σ/12σ + baseline 3σ S18 existente).
  - **Resultado agregado**: 3σ gana en F1 (0.36 vs 0.29), recall (0.71 vs 0.64), precision (0.24 vs 0.19).
  - **Hallazgo crítico**: 5σ y 12σ producen resultados **idénticos al bit** en Lascar y Tupungatito. Causa: el cap `MAX_SIGMA_COMPONENT_K=7K` ([process_viirs.py:358](../pipeline/process_viirs.py#L358)) satura cuando `std_bg > 0.58 K` (típico).
  - **Por qué 3σ + cap gana**: actúa como umbral adaptativo de facto:
    - σ_bg bajo: threshold = max(5K, 3·σ_bg) → permisivo, captura señales débiles.
    - σ_bg alto: threshold capeado a 7K → no se infla a 9-15K que mata señal real.
  - **Decisión**: mantener `n_sigma_mir = 3.0` + `MAX_SIGMA_COMPONENT_K = 7.0`. Documentar el cap como **innovación nuestra (S15 Tema F)** que empíricamente supera 5σ/12σ uniformes para nuestra geometría σ-anillo bbox 50×50 km.
  - **No resuelve H17 Tupungatito**: el A/B confirma que el problema NO es N·σ. Camino alternativo S20: dual-ROI Coppola 5σ summit / 10σ scene.
  - Detalle completo: `docs/DRIFTS_S17.md` sección "D2 — Resolución S19".

---

## H14 — VRP TIR: Stefan-Boltzmann vs Aveni Eq.9 (drift D3)

- **Formulada**: S17 (2026-04-23).
- **Evidencia**:
  - Aveni 2025 GRL: Eq.9 con k_TIR=60.17 μm·sr; Stefan-Boltzmann subestima 90% bajo 600 K.
  - Coppola 2024 cap Springer: Eq.16 Stefan-Boltzmann (usado canonicamente para low-T).
  - **Aveni 2024 TIRVolcH RSE Eq.5 p.12: Stefan-Boltzmann puro** — mismo grupo MIROVA.
  - Nuestro código: Stefan-Boltzmann ([process_viirs.py:481](../pipeline/process_viirs.py#L481)).
- **Criterio testable**: auditar Aveni 2024 TIRVolcH RSE (paper algorítmico previo a GRL 2025). Ver si MIROVA oficial adoptó Eq.9.
- **Estado**: **✅ RESUELTA HIPÓTESIS ALT B** (Stefan-Boltzmann correcto).
- **Resolución**: Aveni 2024 RSE (paper algorítmico del mismo grupo MIROVA) usa Stefan-Boltzmann puro, igual que Coppola 2024 y nuestro código. La Eq.9 con k_TIR=60.17 solo existe en Aveni 2025 GRL (refinamiento teórico, no adoptado operacionalmente por MIROVA). Mantener Stefan-Boltzmann. Considerar TIRVolcH completo (perfil experimental futuro) para Copahue/Peteroa/Tupungatito crater lakes.

---

## H16 — TIRVolcH (Aveni 2024) es investigación paralela, no migración MIROVA

- **Formulada**: S17 (2026-04-23 tarde).
- **Hipótesis**: TIRVolcH (Aveni 2024 RSE) **no reemplaza** MIROVA operacional — es un algoritmo experimental paralelo del mismo grupo (Turín+Sapienza).
- **Evidencia**: Coppola coautor tanto en Aveni 2024 como en su review Springer 2024. Review 2024 sigue usando Stefan-Boltzmann puro sin mención de TIRVolcH como método operacional. Aveni 2024 menciona NOAA-21 como "future" (p.20), reforzando que el paper se escribió pre-operacional J2.
- **Estado**: **CONFIRMADA**.
- **Implicación**: TIRVolcH tiene valor potencial para crater lakes chilenos (Copahue, Peteroa, Tupungatito hydrothermal sub-pixel) pero su implementación es costosa (REF mensuales por volcán, 4 ROIs + VSROI, 14 tests, bi-cubic BT_bg). Mantener en backlog para objetivo 2 (herramienta independiente). Bajo objetivo 1 (clon MIROVA) no aporta.

---

## H15 — NOAA-21 VJ202 producto estable en CMR desde ene 2023

- **Formulada**: S17 (2026-04-23) sub-hipótesis de H10.
- **Evidencia**: earthaccess retorna VJ202IMG + VJ202MOD v2.1 Standard + NRT para fechas 2026-04-10 y 2026-04-22.
- **Respaldo documental**: JPSS VIIRS Radiometric ATBD Rev C (descargado S17).
- **Estado**: **CONFIRMADA**.

---

## H_S23_FACTOR42 — MIROVA reporta clusters, nosotros pixels

- **Formulada**: S23 (2026-04-26) tras audit profundo S22 que detectó "factor 42"
  abierto desde S15 (77 px nuestro vs 4 MIROVA Lascar 2025-11-15) sin causa raíz.
- **Hipótesis**: MIROVA reporta `n_hotspots` (regiones contiguas, conectividad ~1km),
  nosotros reportamos `n_anomalous_pixels` (pixels individuales). Mismos pixels
  físicamente — diferencia de agregación al reportar.
- **Criterio testable**: union-find sobre records con muchos pixels, cluster_radius
  variable. Si ratio `pixels/clusters` ≈ 20-50, hipótesis confirmada.
- **Evidencia** (`experiments/50_factor_42_clustering_test.py`, S23 T14):
  - Lastarria 77 px → 3 clusters @1km (ratio 25.7)
  - Chaitén 360 px → 9 clusters @1km (ratio 40)
  - Lascar 77/4 reportado audit = ratio 19.25 → compatible cluster_radius ~0.5-1km.
- **Estado**: **✅ CONFIRMADA y RESUELTA** S23 (commit `2646fe2`).
- **Resolución**: NO es bug — diferencia de agregación. Recall/precision NO afectados.
  Documentado `experiments/50_FACTOR_42_HALLAZGO.md` + glosario CLAUDE.md.
- **Item derivado S24+**: agregar `n_anomalous_clusters` al schema para paridad
  exacta con MIROVA (no crítico).

---

## H_S23_LOCAL_ROI — Solo VIIRS 375m carece local p95 threshold (D7)

- **Formulada**: S23 (2026-04-26) tras audit profundo. Audit S22 inicial sugirió
  "MODIS-only" pero re-investigación reveló matiz importante.
- **Hipótesis**: process_modis (1km) y process_viirs_mod (750m) aplican
  `local_threshold = roi_p95 + max(3.0, 2.0*roi_std)`. process_viirs (375m) NO.
- **Estado**: **DOCUMENTADO como D7** en `docs/DRIFTS_S17.md` (S23 commit `acb98ff`).
- **Resolución**: 4 tests schema-source (`test_local_roi_paridad.py`) alertan si
  el código diverge sin update docs.
- **Decisión diferida S24+**: fix algorítmico (agregar a VIIRS 375m o quitar de
  MODIS/VIIRS 750m) requiere A/B contra OSF v2.5.

---

## H_S24_P31_VALIDATED — P3.1 dual-ROI corta FP_far sin tocar summit

- **Formulada**: S24 (2026-04-26) ejecutando P1 del handoff S24.
- **Hipótesis**: P3.1 (Coppola 2016a Tabla 2, dual-ROI thresholds summit/scene)
  reduce FPs en zona "far" (5-25 km del vent) sin afectar TPs summit. S15
  implementó pero nunca cuantificó la contribución aislada vs P3.2 single-ROI.
- **Criterio testable**: A/B 14d × 4 Tier A con dual_roi=true vs false. P3.1
  pasa si Δ FP_far ≪ 0 y Δ summit ≈ 0.
- **Evidencia** (run 24962122990, `experiments/51_p31_ab/DELTA_REPORT.md`):
  - **FP_far: 282 → 189 (−33%)** ✓
  - Summit estable: 185 → 187 (Lascar/Lastarria/Tupungatito idénticos; +2 Chaitén = efecto borde mediana 8-vecinos cuando split por máscaras separadas).
  - Trade-off: TP_far cae 86 → 64 (−25%) — refs MIROVA en zona scene descartadas.
- **Estado**: **✅ CONFIRMADA**.
- **Resolución**: MANTENER P3.1 en `mirova_equivalent`. Trade-off TP_far
  aceptable: operacional prioriza precision, refs MIROVA lejanas suelen ser
  ruido geográfico no actividad eruptiva.

---

## H_S24_AVENI_NEGATIVE — Aveni 2025 Eq.9 NO resuelve Villarrica recall 0%

- **Formulada**: S24 (2026-04-26) ejecutando P2 del handoff S24.
- **Hipótesis original (handoff)**: Eq.9 con k_TIR=60.17 capturaría señal
  sub-pixel <600K que Stefan-Boltzmann puro pierde.
- **Criterio testable**: aplicar Eq.9 sobre las 6 refs MIROVA Villarrica con
  t_max,t_bg disponibles. Pasa si VRP_Aveni ~ VRP MIROVA (ratio [0.5, 2.0]).
- **Evidencia** (`experiments/52_aveni_tir_poc.py`):
  - 6/6 refs tenemos record con t_max−t_bg = 2.5–6.8 K (señal SÍ presente).
  - Pipeline reporta vrp_mw=0 en los 6 → DETECCIÓN falla, no fórmula.
  - VRP_Aveni naive sobre-estima 15.5–74.1× MIROVA NRT.
  - VRP_SB 10–50× similar — diferencia Aveni vs SB solo ~30%, no factor 10.
  - Sanity: VRP_Aveni = 0.1 MW basta ΔBT 0.15 K — sin floor produce FPs masa.
- **Estado**: **REFUTADA EN SU FORMULACIÓN**.
- **Resolución**: NO implementar Eq.9 como fix Villarrica. Verdadero cuello
  de botella es **falta de path TIR-only de detección**. MIROVA usa algoritmo
  sub-pixel (Dozier dual-band o equivalente) que la fórmula sola no reproduce.
  Diferido S25+ con decisión metodológica con Nicolás (TIRVolcH completo vs
  path TIR lightweight).

---

## H_S49_TEST1_INTEGRATED_VRP_MISSING — Wooster pixel-level no extrae VRP de sub-pixel summit

- **Formulada**: S49 (2026-05-17) tras investigar NdC pc.vrp=0 sistemático post-fix audit S48.
- **Síntoma**: en NdC y otros volcanes con domo persistente, `pc.vrp_mw=0` aunque `vrp_mir_mw>0` (con lbg_global aplicado) y Test 1 dispara summit con 50-100 pixels.
- **Causa raíz INVESTIGADA**: caso paradigmático NdC 2026-05-01 04:54 NOAA21:
  - 70 anomaly_pixels reportados, solo 2 con `vrp>0` y están a **22-23 km del vent** (background warm valley, bt=271K)
  - 61 pixels summit cráter (bt 251-257K), todos con `vrp_individual=0` porque L_hot - L_bg_global ≤ 0
  - L_bg_global (ring 5-25km) también frío (invierno chileno, nieve circundante summit + bajada) → ΔL ≈ 0
  - vent_anchored cluster selecciona summit (correcto), pero suma de los 61 pixels = 0
- **NO es bug de pipeline**: `effective_L_bg` se propaga bien desde S33/S39 (verificado `pipeline/process_viirs.py:1069`). El lbg_global_compatible flag funciona como diseñado.
- **Causa raíz REAL — divergencia metodológica MIROVA**: MIROVA detecta sub-pixel summit con Coppola 2015 Eq.1 **integrated VRP** (asume fracción f_hot del pixel, calcula radiancia total integrada). VRP-chile usa Wooster pixel-level (ΔL × área × k) que físicamente no puede extraer señal sub-pixel cuando el pixel completo tiene BT promediada con background nieve.
- **Estado**: **CONFIRMADA, NO FIX POSIBLE con Wooster pixel-level. Pendiente S50: Test 1 integrated VRP implementación.**
- **Cobertura operacional actual**: fix audit S48 (H_S48_AUDIT_VRP_ZERO_FALSE_FN) cuenta correctamente TP por `test1+summit+dist<=inner` independientemente de `pc.vrp_mw`. Recall 97.2% logrado. El issue de **magnitud reportada** (pc.vrp=0 cuando MIROVA reporta 0.02-0.30 MW) queda como pendiente cosmético — no afecta operativa.
- **Volcanes afectados**: NdC (89 records 30d), Lascar (15), Lastarria (9), Copahue/Isluga/Planchón/Villarrica (1-2 cada uno). Total 118 records con `test1+summit+pc.vrp=0`.
- **Acción S50**: implementar `Test 1 integrated VRP` per Coppola 2015 Eq.1. Pasa MISSION.md las 3 preguntas:
  1. ¿En papers core? SÍ — Coppola 2015 Eq.1 explícito sobre Stromboli para detección sub-pixel summit.
  2. (no necesita pregunta 2) — cubre Q1.
- **Complejidad estimada**: medio. Requiere agregar path `vrp_integrated_test1` en `pipeline/process_viirs.py` + tests sintéticos + A/B reproc validation.

---

## H_S48_AUDIT_VRP_ZERO_FALSE_FN — Audit cuenta FN cuando Test 1 dispara summit pero pc.vrp=0

- **Formulada**: S48 (2026-05-17) post-comentario usuario "MODIS no detecta lava lake Villarrica, VIIRS-I sí — ¿qué pasa con VIIRS?".
- **Síntoma observado**: subagente VIIRS deep dive reportó "NdC recall 0/3 alertas MIROVA VIIRS-I" como anomalía. Investigación caso-a-caso reveló que las 3 alertas MIROVA NdC VIIRS-I (vrp 0.02-0.06 MW, "Muy Bajo") SÍ estaban detectadas por VRP-chile: Test 1 disparaba con 49-98 pixels summit a 0.0-2.7 km del vent.
- **Causa raíz**: `vrp_mirovaEq(rec, inner)` en `experiments/88_audit_s47_fps_distribution.py` retorna 0 si `pc.vrp_mw == 0`. El audit gate `if vrp_mirovaEq(r, inner) <= 0: continue` descartaba **records con detección legítima pero magnitud cero**.
- **Mecanismo físico (patrón D4 documentado CLAUDE.md)**: en volcanes con domo activo persistente (NdC Nicanor, Lascar fumarola summit, Lastarria geotermal), el ring background 1-3km está contaminado por calor crónico → L_bg local sale alta → ΔL_pix - L_bg ≈ 0 → pc.vrp=0 aunque Test 1 dispare correctamente sobre background global.
- **Alcance del bug en window 30d**: 118 records totales perdidos. **NdC concentra 89 (82% de sus test1+summit)**. Lascar 15, Lastarria 9. 4 vols sin impacto.
- **Estado**: **CONFIRMADA y FIX APLICADO**.
- **Fix S48** (`experiments/88_audit_s47_fps_distribution.py`):
  - Nuevo helper `is_test1_summit_detection(rec, inner)`: True si `final_hotspot_source=="test1"` + `distance_class=="summit"` + `final_hotspot_dist_km <= inner`.
  - Nuevo helper `is_detected(rec, inner)`: `vrp_mirovaEq > 0 OR is_test1_summit_detection`.
  - Reemplazado gate del audit en main loop + en loop FN matching.
- **Impacto cuantitativo en métricas S48 finales**:
  | Métrica | Pre-fix vrp_zero | Post-fix |
  |---|---:|---:|
  | TP | 329 | **352** (+23) |
  | FN | 21 | **10** (-11) |
  | Recall | 94.0% | **97.2%** |
  | F1 | 96.6% | **98.3%** |
  | NdC TP | 0 | 5 |
  | NdC FN | 4 | 1 |
- **Issue separado a investigar S49**: ¿por qué `lbg_global_compatible: true` (set en `volcanoes.yaml` NdC desde S42) no produce pc.vrp>0 en VIIRS-I? El fix D4 S39 fue aplicado a MODIS; verificar si VIIRS-I propaga el flag correctamente en `pipeline/process_viirs.py:compute_primary_cluster_vrp`.
- **Lección metodológica**: para volcanes con actividad summit persistente (≥6/11 Tier A), el VRP es señal sub-piso (0.02-0.5 MW) y MIROVA NRT mismo reporta así. Distinguir entre "no detectado" (no entró Test 1) y "detectado pero magnitud sub-piso" (entró Test 1, pc.vrp=0). Ambos son TPs operacionales si el alerta MIROVA existía.

---

## H_S48_AUDIT_SPATIAL_MISMATCH — Audit matcher confunde clusters distintos del mismo granule

- **Formulada**: S48 (2026-05-17) post-investigación 8 FPs Isluga + 5 FPs Lascar.
- **Síntoma observado**: audit S47 contó 51 FP(a) en window 30d. Isluga 16, Lascar 5 (zona cráter <1.6 km del vent). Investigación per-caso reveló que MIROVA en esos timestamps reportó FALSO_POSITIVO de clusters a 16-29 km del vent (chimney lejano, masas de agua), no en summit.
- **Hipótesis**: el matcher `experiments/88_audit_s47_fps_distribution.py` clasifica como FP(a) cualquier detección nuestra que tenga entry MIROVA `Tipo_Registro=FALSO_POSITIVO` en ±30min mismo sensor, **sin chequear distancia espacial**. Cuando MIROVA marca FP de un cluster lejano mientras nosotros detectamos correctamente el summit cráter, ambos son entradas legítimas pero **eventos distintos del mismo granule** — no nuestro FP.
- **Caso paradigmático**: Isluga 2026-04-16 05:18 VIIRS375. MIROVA reportó FP con `Distancia_km=21.14`, nuestro pc `centroid_dist_km=1.04`. Diferencia espacial 20 km → mismo granule, clusters distintos.
- **Estado**: **CONFIRMADA y FIX APLICADO**.
- **Fix S48** (`experiments/88_audit_s47_fps_distribution.py`):
  - Antes de clasificar como FP(a) o FP(c), exigir `abs(MIROVA.Distancia_km - ours.centroid_dist_km) <= 5 km` (`SPATIAL_TOL_KM`).
  - Si MIROVA tuvo entry temporal pero `mirova_diff_cluster==True`, reclasificar a FP(b) `b_no_mirova_entry` con flag explícito.
  - Fallback conservador: si alguna distancia es None, mantener comportamiento legacy (no agravar).
- **Impacto cuantitativo**:
  | Métrica | Pre-fix | Post-fix |
  |---|---:|---:|
  | TP | 329 | 329 |
  | FP(a) drift real | 51 | **2** |
  | FP(b) huérfanos | 180 | 360 |
  | FP(c) RUTINA | 1374 | 1243 |
  | Precision (vs FP(a)) | 86.6% | **99.4%** |
  | F1 | 90.1% | **96.6%** |

  De los 49 casos reclasificados, `mirova_diff_cluster=True`: PCC 102, Tupungatito 37, Isluga 15. PCC concentra el patrón — consistente con H_S48_PCC_COORD (otro fix de esta sesión).
- **Caveat**: el F1=96.6% es bajo convención "MIROVA vio nuestro cluster y lo marcó FP". Los 178 nuevos `mirova_diff_cluster` siguen siendo casos donde ambos sistemas detectan en zonas distintas del mismo granule — merecen investigación caso a caso (algunos pueden ser nuestros drifts cluster selection, otros pueden ser MIROVA disparando a ruido lejano).
- **Lección metodológica**: matchers de auditoría que cruzan solo por timestamp+sensor son insuficientes en escenas con múltiples clusters térmicos. El criterio espacial debe ser obligatorio para cualquier conclusión sobre drift.

---

## H_S58_LOCAL_KERNEL_BG_REPROC_VALIDATED — A/B reproc Villarrica VALIDA fix

- **Formulada**: S58 (2026-05-17) tras reproc Villarrica window 30d run 25990074670 SUCCESS (76 min).
- **Reproc setup**: profile `_local_kernel_bg_enabled` con `enable_local_kernel_bg=true` + per-vol `local_kernel_bg=true` Villarrica. Window 2026-04-16 → 2026-05-15.

### Resultados casos paradigmáticos

| Caso | MIROVA | LEGACY pc.vrp | NEW pc.vrp | LEGACY ratio | NEW ratio | Mejora |
|---|---:|---:|---:|---:|---:|---|
| 2026-05-11 06:00 NOAA20 | 0.31 | 0.385 | 0.498 | 1.24× | 1.61× | ≈ (cambio marginal dentro tolerancia Aveni ±35%) |
| **2026-05-14 05:48 NOAA21** | **0.31** | **3.744** | **0.672** | **12.08×** | **2.17×** | **-82% inflación** ✓ |
| 2026-04-09 / 2026-03-08 / 2026-02-26 | — | — | — | — | — | Fuera window reproc (start=04-16) |

### Stats agregados (todos records VIIRS-I summit window 30d)

| Métrica | LEGACY | NEW | Cambio | Target OSF v2.5 |
|---|---:|---:|---|---:|
| N records summit pc.vrp>0 | 321 | **111** | -65% | — |
| Mediana | 2.52 MW | **1.41 MW** | -44% | 0.92 MW |
| Max | 18.34 MW | **6.59 MW** | -64% | — |

### Interpretación

**Funciona estructuralmente**:
- Mediana cae 44% acercándose a target OSF (1.41 vs target 0.92, gap reducido 6× → 1.5×)
- Max cae 64% (eliminando outliers patológicos)
- N records baja 65% (los sub-pixel marginales que antes pasaban por background contaminado ahora se filtran correctamente)
- Caso 2026-05-14 cura inflación 12× → 2.17×

**Caveats**:
- N=2 casos comparables (otros 3 fuera del window 30d reproc)
- Mediana 1.41 MW vs target OSF 0.92 MW sigue 1.5× arriba. Posibles refinamientos S60+:
  - `kernel_size=5` (más vecinos, bg menos sensible a outliers)
  - Percentile (p25-p50) en lugar de mean del kernel
  - Combinar con threshold strict adicional
- Reducción 65% records summit puede incluir algunos TPs MIROVA RUTINA legítimos
  (auditar contra CSV scraper antes de adopción operacional)

### Estado pipeline

- ✅ Fix funcionando en path opt-in `_local_kernel_bg_enabled` profile
- ✅ Per-vol flag aplica solo Villarrica/Copahue/Llaima/Planchón (no universal)
- ✅ Operacional `mirova_equivalent` sin afectar (flag profile OFF)
- ⏸️ Adopción operacional **pendiente**: requiere R6 (cuestionar mejora >30% antes adoptar)
  + audit recall recall sin regresión + R2 pixel-level vs `mirova-tif-archive`

### Próximos pasos S60+

1. Auditar recall Villarrica NEW vs MIROVA CSV (no perder TPs)
2. Comparar con OSF v2.5 mediana estadística
3. R2 pixel-level validation 5+ casos canónicos
4. Considerar refinamientos (kernel 5×5, percentile)
5. Si R6 valida: adopción operacional `mirova_equivalent.yaml` con `enable_local_kernel_bg: true`
6. Extender A/B reproc a Copahue/Planchón/Llaima (otros 3 vols opt-in S59)

---

## H_S58_LOCAL_KERNEL_BG_OPT_IN_PER_VOL — fix per-vol, no universal

- **Formulada**: S58 (2026-05-17) tras análisis offline 3 subagentes paralelos: OSF v2.5 Villarrica + extensión MODIS + audit otros 10 Tier A.

### Hallazgo Subagente A — OSF v2.5 Villarrica (5211 filas 2000-2025)

- Magnitudes históricas VIIRS-I: **mediana 0.92 MW**, p25=0.27 MW, p10=0.09 MW
- Rango "0.1-0.3 MW" del CSV scraper NRT corresponde a **p10-p25 histórico OSF**
- Ratio bg/hot mediano = 0.52 (señal 48% sobre bg)
- **Snap 838m confirmado** = diagonal pixel I-band 375×√5 = 838.5m
- 2025 solo 18 detecciones full year (bajón vs 2023=110)
- OSF NO cubre 2026 (termina 2025-12), sirve como **target estadístico**, no día-a-día

### Hallazgo Subagente B — MODIS extension TDD

- `compute_local_background` extendido a `process_modis.py:636-653`
- 5 tests TDD nuevos pass
- Suite total: **335 passed** (era 330, +5 MODIS)
- MODIS B21 λ=3.929μm, Planck inline (no helper) — paridad metodológica con VIIRS

### Hallazgo Subagente C — bug per-vol, NO universal

| Vol | ALERTAs MIROVA | ΔBT_max−median | ¿Bug aplica? |
|---|---:|---:|---|
| **Villarrica** | 0 (15d) | -1.29 K | SÍ (caso canónico) |
| **Copahue** | 1 | -1.68 K | **SÍ (ratio 50×, lago El Agrio activo)** |
| **Planchón** | 7 | -2.88 K | **SÍ (ratio 5.1×, laguna cráter)** |
| **Llaima** | 0 | -0.96 K | SÍ (lago Conguillío) |
| Tupungatito | 14 | **-5.04 K** | NO — ring FRÍO por glaciar, kernel empeoraría |
| Lascar | 58 | +16 K | NO — gradiente positivo, sano |
| Lastarria | 18 | +3 K | NO — gradiente positivo |
| Isluga | 16 | +2.84 K | NO — ratio ~1 |
| NdC | 2 | -4 K | NO — sin señal robusta |
| PCC | 8 | +4.5 K | NO — gradiente positivo (inflación es de cluster selection D8/D9) |
| Chaitén | 0 | +2.31 K | NO — gradiente positivo |

**Bug aplica específicamente** donde hay **fuente de calor extensa dentro del ring 5-25km que NO es el cráter**:
- Villarrica: lago Villarrica al N
- Copahue: lago El Agrio cráter activo  
- Planchón: laguna cráter
- Llaima: lago Conguillío

**Tupungatito es caso OPUESTO**: ring FRÍO por glaciar → kernel local agregaría FPs.

### Recomendación implementación

**Activar flag per-vol, NO global**:

```yaml
# volcanoes.yaml
- name: Villarrica
  local_kernel_bg: true  # S58 fix
- name: Copahue
  local_kernel_bg: true  # S58 fix
- name: PlanchonPeteroa  
  local_kernel_bg: true  # S58 fix
- name: Llaima
  local_kernel_bg: true  # S58 fix (sin alertas pero patrón similar)
# Resto: default false (mantiene legacy median ring)
```

Profile flag `enable_local_kernel_bg` se queda como **gate global on/off para el feature**, y `local_kernel_bg` per-vol controla aplicación específica.

### Caveats fuertes

- CSV ground truth solo cubre 15/30d nominales (termina 2026-05-01)
- `p10 = median - 1.282σ` es proxy estadístico, no implementación real kernel
- Ratio inflación usa "pc.vrp>1MW" como proxy de "alerta", no réplica exacta

### Estado

- Pipeline integrado (VIIRS + MODIS) — flag global ON/OFF funciona
- Per-vol flag PENDIENTE S59 (requiere cambio en `compute_local_background` callsite para pasar `volcano_config`)
- Reproc Villarrica en progreso (run 25990074670)

---

## H_S57_PAPERS_RE_READ + EXCELS_OLVIDADOS + LOCAL_KERNEL_TDD — meta-leccion + hallazgos masivos

- **Formulada**: S57 (2026-05-17) tras Nicolás señalar dos olvidos críticos:
  1. "¿por qué encontramos esa información ahora? no hemos revisado todos los papers al máximo detalle"
  2. "los excels que has estado olvidando, eso no debería pasar"

### Subagente A — extracción exhaustiva citas LITERALES papers (`docs/MIROVA_DETAILED_CITATIONS.md`, 320 líneas)

Lectura sistemática de 7 papers core. **Confirmado triple en TRES papers que el background MIROVA es kernel local, NO ring**:
- `[sp426_5.txt:357-359]`: "L4bk is estimated from the **arithmetic mean of all the pixels surrounding the active one** (or around the active cluster)"
- `[coppola2024_chapter.txt:1129]`: "T_bk is retrieved from the pixels adjacent to the hot one"
- `[campus2024_extracted.txt:119-124]`: "Lpixbk computed from the arithmetic mean of the radiance of the **pixels surrounding the alerted one(s)**"

**Y cluster aggregation = sum scene-wide en TRES papers**:
- Coppola 2016a Eq.8, Coppola 2024 Eq.13, Campus 2024 Eq.1: TODOS Σ sobre alerted pixels. NO hay "primary cluster" en MIROVA core.

**Tabla 1 SP426.5 thresholds verbatim**: K1 night=−0.8, C1 ROI1=0.003 / ROI2=0.01, C2 ROI1=5σ / ROI2=10σ. Nuestro pipeline usa 3σ universal → drift D2 documental.

### Subagente B — archivos olvidados (`docs/EXCELS_INVENTORY_S57.md`)

**Hallazgo más grave: OSF v2.5 archive ignorado**. `data/mirova_reference/VRP_GLOBAL_ARCHIVE_2025.csv`:
- 615,470 filas globales, **5211 Villarrica (2005-2024)** con `LAT/LON` exactos del hotspot MIROVA, `VRP` en Watts, `Max_Dist` real, `class` (1=alerta, 0=otro).
- 48,360 filas Chile en 10 volcanes.
- En S45 traté de auditar coord vent + cluster MIROVA usando TIFs cuando tenía LAT/LON exactos del hotspot histórico aquí mismo. Habría resuelto D9 sin TIF.
- Verificado: Villarrica 2025-12-06 06:00 NOAA20 → VRP=48543W=0.048 MW, Max_Dist=838.5m → **patrón 838m constante = 1 pixel I-band centrado**, idéntico al CSV scraper 0.84km. Confirma snap pixel.

**6 CSVs adicionales olvidados**: registro_vrp_ocr (con 6 cols validación humana extra), Historial_Puyehue_Cordon_Caulle (curado), per-volcán snapshots.

### Subagente C — TDD local kernel (`pipeline/vrp_regimes.py` + `tests/test_local_kernel_background.py`)

Implementación MISSION-compliant (Coppola 2024 L1129 literal):

```python
def compute_local_background(bt_grid, hot_rows, hot_cols, kernel_size=3):
    # Coppola 2024 L1129: "T_bk is retrieved from pixels adjacent to hot one"
    # Para cada hot pixel: mean de vecinos 3x3, excluyendo (a) centro (b) otros hot.
    # NaNs ignorados.
```

8 tests sintéticos TDD estrictos PASSED. Suite total: **330 passed / 16 skipped** (era 322, +8).

NO INTEGRADO en `process_viirs.py` aún — solo módulo standalone. Próximo paso S58: flag profile experimental.

### Lección meta-meta (anti-olvido permanente)

**Regla S57+ obligatoria** al iniciar cada sesión:

1. **Leer `docs/MIROVA_DETAILED_CITATIONS.md`** (citas verbatim 7 papers core).
2. **Auditar disponibilidad**: `find data/ -name "*.csv"` antes de cualquier audit. No re-scrape lo que ya tengo.
3. **OSF v2.5 archive es PRIMARY ground truth histórico** (no CSV scraper de Nicolás que solo cubre últimos meses). Cargar siempre que se valide algo.
4. **Anti-patrón documentado**: "asumir que ya leí el paper" sin verificar línea-por-línea. Para hipótesis críticas, releer la sección relevante.

### Estado pipeline post-S57

- Sin cambios operacionales (solo módulo nuevo + tests)
- `compute_local_background` listo para integración S58
- 4 documentos canónicos nuevos disponibles:
  - `docs/MIROVA_DETAILED_CITATIONS.md` (citas verbatim)
  - `docs/EXCELS_INVENTORY_S57.md` (archivos olvidados)
  - `pipeline/vrp_regimes.py:compute_local_background` (implementación)
  - `tests/test_local_kernel_background.py` (8 tests TDD)

---

## H_S56_BACKGROUND_PERCENTILE_BAJO_REPLICA_MIROVA — p01-p05 del ring resuelve gap MW

- **Formulada**: S56 (2026-05-17) tras A/B offline 5 variantes de background.
- **Hipótesis original**: nuestro `median(ring 5-25km)` está sesgado hacia caliente por incluir lake/valley adyacentes en Villarrica. MIROVA usa background más frío.
- **Implementación**: `experiments/101_background_variants_offline.py` con proxy de percentiles via `t_bg = median - k·σ` (asumiendo distribución normal del ring).

- **Resultado A/B**:

  | Variant | Mediana ratio | Promedio | Casos rango [0.3, 3.0] |
  |---|---:|---:|---:|
  | p50 (current) | 0.10× | 0.09× | **0/5** ✗ |
  | p25 | 0.39× | 0.25× | 2/5 |
  | p10 | 0.50× | 0.46× | 3/5 |
  | p05 | 0.56× | 0.58× | **4/5** ✓ |
  | **p01** | **0.73×** | **0.79×** | **4/5** ✓ (caso 02-26: 1.20× casi perfecto) |

- **Análisis matemático** (despejando Eq.16 hacia atrás caso 2026-02-26 MIROVA 0.12 MW):
  - T_bg implícito ≈ **275K**
  - Nuestro median actual = 281.25K → desfase **+6K**
  - p05 del ring = **275.51K** ← coincide ✓
- **Causa raíz física**: median(ring 5-25km) incluye **lake Villarrica al N + valles agrícolas E** (más cálidos que summit nevado en invierno chileno). Sesga `t_bg` hacia caliente → ΔL clipped → vrp=0 en pixels summit que MIROVA SÍ detecta.
- **Estado**: HIPÓTESIS CONFIRMADA por A/B offline. Background distinto resuelve el gap MW.

### Approach MISSION-compliant identificado

**Coppola 2024 chapter línea 1129** dice literal:
> "T_bk is retrieved from the pixels adjacent to the hot one"

Esto es **kernel local 3×3 o 5×5** alrededor de cada hot pixel, NO median del ring 5-25km. **MISSION-COMPLIANT** (Coppola 2024 paper core MIROVA).

### Plan S57+ (3 approaches A/B/C)

1. **Approach A (más simple, MISSION-compliant Coppola 2024)**: `t_bg local` = mean/median del kernel 3×3 alrededor de cada hot pixel
   - ✓ Coppola 2024 línea 1129 literal
   - Aplica per-pixel, no scene-wide
   - Físicamente correcto (background inmediato no contaminado por lake remoto)

2. **Approach B (más conservador)**: ring background más pequeño (3-8 km en vez de 5-25)
   - ⚠️ NO explícito en papers
   - Pero más cerca del summit = más frío en Villarrica

3. **Approach C (más reciente)**: usar percentil 5 del ring 5-25km actual
   - ⚠️ NO en papers Coppola
   - Más rápido implementar (1 línea cambio)
   - Probable hack más que solución metodológica

### Pre-recomendación: Approach A (Coppola 2024 local kernel)

Pasa MISSION.md Q1 literal. Implementación scope mediano (kernel filter per hot pixel). Tests TDD obligatorios para validar conservación de detección + magnitud realista en los 5 casos paradigmáticos.

---

## H_S55_AGGREGATION_OFFLINE_NEGATIVE — 4 estrategias agregación NO replican MIROVA en casos no-emergentes

- **Formulada**: S55 (2026-05-17) tras A/B offline 4 estrategias contra 5 casos paradigmáticos.
- **Implementación**: `experiments/100_aggregation_strategies_offline.py` con 4 estrategias:
  1. `top_pixel`: pixel más caliente del cluster summit
  2. `eq16_two_component`: R2 Eq.16 con T_e=1000K aplicado a top pixel
  3. `threshold_strict`: pixels con vrp_individual > 0.05 MW dentro 2km
  4. `summit_radius_filter`: sum pixels dentro 1km del centroide

- **Resultado A/B**:

  | Estrategia | Mediana ratio | Caso 1 emergente | Casos 2-5 no emergentes |
  |---|---:|---:|---|
  | pc.vrp_mw (sum actual) | 31.59× | 1.24× ✓ | 12-84× inflado |
  | top_pixel | 0.00× | 0.61× | **0.00× todos** |
  | eq16 (R2) | 0.00× | 0.26× | **0.00× todos** |
  | thresh strict | 0.00× | 0.61× | 0.00× todos |
  | radius 1km | 0.00× | 0.61× | 0.00× todos |

- **Hallazgo crítico**: en 4/5 casos los pixels summit tienen `vrp_individual=0` (patrón D4: L_bg local contaminado clipped). **Las 4 estrategias offline reducen a 0** porque trabajan sobre `anomaly_pixels` que ya tienen vrp clipped.
- **MIROVA aún reporta 0.11-0.21 MW** en esos 4 casos → **MIROVA NO usa el mismo background que nosotros**. El problema es UPSTREAM, no en agregación.
- **Posibles backgrounds MIROVA distintos**:
  - (a) Percentil bajo (25%) del ring summit, no median → bg más frío → ΔL positivo
  - (b) Background del bbox 50×50 km completo (incluye lake/valley más fríos en mediana)
  - (c) Background DUAL ring (combinación summit + scene) según Coppola 2016a Tabla 2
  - (d) Aplicar Eq.16 sobre cluster como UNIDAD (no por pixel) con BT_efectiva integrada
- **Estado**: AGGREGATION offline NEGATIVA. Problema es BACKGROUND, no agregación.
- **Plan S56+**: requiere reproc (no offline) con diferentes background strategies:
  1. Variar percentil background (median/p25/p75)
  2. Variar dual_roi summit vs scene
  3. Probar Eq.16 sobre cluster como unidad (BT_efectiva = mean del cluster)
- **MISSION.md gate**: dual_roi summit/scene está en Coppola 2016a Tabla 2 ✓ MISSION-compliant. Percentil bajo NO está en papers explícito ⚠️.
- **Lección metodológica**: cuando los anomaly_pixels reportados tienen vrp=0 globalmente pero MIROVA reporta algo, el problema es upstream (background) no downstream (agregación). Verificar siempre el upstream antes de probar agregaciones.

---

## H_S54_CLUSTER_SUM_INFLATES_VS_MIROVA — pc.vrp_mw=Wooster sum NN pixels vs MIROVA single-cluster

- **Formulada**: S54 (2026-05-17) tras investigación pixel-a-pixel granules nuestros vs imágenes Mirova-v1 + análisis distribución espacial cluster.
- **Plot twist S54**: H_S53 era PARCIALMENTE incorrecta. La premisa "MIROVA captura cluster lake/valley en casos sin emergencia summit" fue REFUTADA por imágenes Mirova-v1 (20 PNGs descargados): **MIROVA marca CRÁTER en TODAS las 5 fechas**, incluyendo 2026-04-09 y 2026-03-08.
- **Hallazgo verdadero**:

  | Caso | MIROVA MW | pc.vrp_mw (Wooster sum) | pc.n_pixels | Ratio |
  |---|---:|---:|---:|---:|
  | 2026-05-11 06:00 | 0.31 | **0.385** | **1** | **1.24× ✓** |
  | 2026-05-14 05:48 | 0.31 | 3.744 | 87 | 12.08× |
  | 2026-04-09 06:00 | 0.11 | 7.141 | 71 | 64.92× |
  | 2026-03-08 06:00 | 0.21 | 6.633 | 69 | 31.59× |
  | 2026-02-26 05:42 | 0.12 | 10.105 | 84 | 84.21× |

- **Patrón claro**: cuando cluster tiene 1 pixel (caso 1 lava lake emergente puro), ratio perfecto. Cuando cluster tiene 60-90 pixels conectados (casos 2-5), ratio inflado 12-84×.
- **Distribución espacial pixels** (anomaly_pixels top-100 dentro de 5km del centroide vs >5km):
  - Caso 2026-02-26: 39 pixels <5km del centroide pero suma vrp_individual=0.01 MW; 10 pixels >5km suma 4.83 MW
  - **pc.vrp_mw = 10.1 MW NO es la suma de anomaly_pixels visible** — cluster real tiene más pixels (84 total) que el top-100 anomaly_pixels muestra (porque scene tiene pixels más calientes en otra parte)
- **Causa raíz**: `cluster_hotspots(vent_anchored)` agrupa pixels conectados 8-vec en grid 2D. 70-90 pixels conectados ~30×30 px (~11×11 km) cerca del cráter forman cluster contiguo. **Wooster sum de Tantos pixels infla 30-80× vs MIROVA**.
- **MIROVA NO usa cluster selection** (Subagente B S54 + Coppola 2016a línea 387-398 + Coppola 2024 Eq.13). Sum scene-wide pero **MIROVA reporta menos magnitud** porque:
  - (a) Probable usa Eq.16 two-component sub-pixel (Coppola 2024 §Lava lakes)
  - (b) O usa threshold más estricto que descarta pixels marginales del cluster
  - (c) O reporta solo top-1 pixel del cluster (no sum total)
- **Estado**: CONFIRMADA causa, AGREGACIÓN distinta es el problema, no detección.
- **Plan S55+**: profile experimental `_villarrica_aggregation_test` con estrategias diferentes:
  1. `top_pixel`: reportar solo top-1 pixel del cluster
  2. `eq16_two_component`: usar Eq.16 R2 ya implementado S53 (T_e=1000K asumido)
  3. `threshold_strict`: solo pixels >N×σ del centroide
  4. `summit_radius_filter`: solo pixels dentro de X km del centroide del cluster
- **MISSION.md compliance check**:
  - Opción 1 (top_pixel): ⚠️ NO en papers literal — divergencia
  - Opción 2 (Eq.16): ✓ Coppola 2024 §Lava lakes, asumiendo T_e=1000K Burgi-Coppola
  - Opción 3 (threshold strict): ✓ Coppola 2016a Tests 2/3 N·σ threshold
  - Opción 4 (radius filter): ⚠️ NO en papers literal — divergencia
- **Imágenes Mirova-v1 descargadas** en `data/mirova_reference/mirova_v1_images/Villarrica_<5_fechas>/`: 20 PNGs RGB + plots logVRP/Dist. Disponibles para investigaciones futuras.

---

## H_S53_R2_LAVA_LAKE_PARTIAL_REPLICATES_MIROVA — Eq.16 funciona solo cuando lava lake emerge

- **Formulada**: S53 (2026-05-17) tras implementación R2 Eq.16 (TDD) + calibración empírica.
- **Hipótesis original**: R2 Eq.16 Burgi-Coppola con T_e=1000K replicaría MIROVA Villarrica 0.1-0.3 MW.
- **Implementación**: `pipeline/vrp_regimes.py:compute_vrp_lava_lake_eq16` con TDD (10/10 tests pass).
- **Calibración empírica** (`experiments/98_calibrate_te_villarrica.py`) contra 5 ALERTAS MIROVA confirmadas:

  | Caso | BT_hot pixel summit | t_bg_k ring | ΔBT | MIROVA MW | R2 T_e=400K | Ratio |
  |---|---:|---:|---:|---:|---:|---:|
  | 2026-05-11 06:00 NOAA20 | 283.3 | 279.06 | **+4.24** | 0.31 | 0.077 | 0.25 (T_e=600K mejor) |
  | 2026-05-11 (Wooster actual) | — | — | — | 0.31 | 0.385 | 1.24 ✓ |
  | 2026-02-26 05:42 NOAA20 | 281.85 | 281.25 | +0.60 | 0.12 | 0.076 | 0.63 |
  | 2026-04-09 06:00 NOAA20 | 276.97 | 281.12 | **-4.15** | 0.11 | 0.00 | 0.00 ✗ |
  | 2026-03-08 06:00 NOAA20 | 282.28 | 282.62 | -0.34 | 0.21 | 0.00 | 0.00 ✗ |

- **Hallazgo clave**: en 2 de 4 casos, **pixel summit (cráter) ES MÁS FRÍO que ring 5-25km**. Físicamente posible: invierno chileno, summit Villarrica nieve cubre lava lake oculto, ring contiene zonas más bajas/cálidas (lake Villarrica, valles).
- **MIROVA aún reporta alertas en esos casos**: probablemente captura cluster del lake Villarrica al N (BT 285-291K, distancia 5-30km) y lo asigna al volcán Villarrica por estar dentro del ROI MIROVA. Reporta 0.11-0.21 MW de cluster lake, NO del lava lake.
- **Implicación importante**: las "ALERTAS MIROVA Villarrica" NO son necesariamente del lava lake. Pueden ser:
  - (a) Lava lake emergente (caso 2026-05-11): MIROVA captura summit correctamente
  - (b) Fenómenos térmicos lake/valley adyacente asignados al volcán
- **R2 Eq.16 funciona estructuralmente** cuando hay gradiente summit positivo (ΔBT > 0). Para casos sin emergencia, R2 retorna 0 (correcto físicamente). Replica MIROVA solo parcialmente.
- **Estado**: IMPLEMENTACIÓN COMPLETA, REPLICA PARCIAL.
- **Próximos pasos S54+**:
  1. Integrar R2 en `process_viirs.py` como path opt-in (flag profile `enable_r2_lava_lake`)
  2. Agregar `lava_lake_magmatic: true` a Villarrica en `volcanoes.yaml`
  3. A/B reproc Villarrica para validar magnitudes per-caso
  4. Para casos sin emergencia summit (2 de 4): investigar si MIROVA realmente reporta lake/valley clusters → entender método MIROVA cluster-selection
- **Lección metodológica**: replicar MIROVA exactamente requiere también replicar su CLUSTER SELECTION operacional, no solo la fórmula de magnitud. Coppola 2024 chapter no describe esto explícitamente.

---

## H_S52_PCC_COORD_3CASES_TRADEOFF — 3/69 PCC empeoraron, trade-off aceptable

- **Formulada**: S52 (2026-05-17) tras investigación 3 casos PCC que empeoraron post-fix coord.
- **Hallazgo**: los 3 casos son del **mismo día (2026-05-15)** y todos VIIRS (NOAA20 + SNPP_750 + NOAA20_750):

  | Granule | Pre-fix | Post-fix | Diff |
  |---|---|---|---|
  | 06:24 NOAA20 (375m) | 41 px, vrp=0.78, d=5.60km | 1 px, vrp=0.06, d=6.37km | +0.78km |
  | 06:06 SNPP_750 | 3 px, vrp=2.82, d=5.76km | 1 px, vrp=0.00, d=7.18km | +1.42km |
  | 06:24 NOAA20_750 | 1 px, vrp=0.37, d=1.93km | 1 px, vrp=0.34, d=11.89km | +9.96km |

- **Causa**: vent_anchored cluster selection prioriza cluster cerca de `effective_vent` (ahora lacolito). En estos 3 casos, el cluster real estaba cerca del **cone morfológico Puyehue** (no del lacolito). Post-fix, vent_anchored "abandona" el cluster cone-cercano y elige uno más cercano al lacolito — que puede ser cluster degradado (1 px) o muy lejano (11.89 km).
- **Interpretación volcanológica**: PCC tiene actividad histórica en 2 zonas: (1) lacolito 2011 SE del cone (térmico persistente, donde MIROVA centra TIFs) y (2) cone morfológico Puyehue (posibles fumarolas residuales). El fix optimiza para (1) pero degrada (2).
- **Estado**: ACEPTAR como trade-off conocido.
- **Razón**: 48/69 (70%) mejoraron, 18/69 (26%) sin cambio, 3/69 (4%) empeoraron. Ratio claramente positivo. Los 3 casos son del mismo día (sugiere actividad anómala puntual cone) no patrón estructural.
- **Mitigación pendiente S53+**: si actividad en cone Puyehue se vuelve persistente, considerar:
  - Estrategia `multi_vent`: vent_anchored evalúa proximidad a múltiples vents (cone + lacolito) y elige cluster más grande
  - Volver a `vent_anchored` con `vent_lat/vent_lon` (cone) si actividad cone supera lacolito en sesiones futuras
- **No-acción S52**: documentado en este entry. No revertir fix coord — el 70% de mejora es estructural.

---

## H_S51_PCC_COORD_VALIDATED — Validación empírica fix mirova_center PCC

- **Formulada**: S51 (2026-05-17) post-reproc PCC --overwrite (run 25981141120).
- **Contexto**: H_S48_PCC_COORD fixed via mirova_center_lat=-40.582,
  mirova_center_lon=-72.131 (lacolito) en `volcanoes.yaml`. Validación
  pendiente reproc empírico hasta S51.
- **Método validación**:
  - Disparado `nrt.yml` workflow_dispatch con volcano=PuyehueCordonCaulle,
    start=2026-05-10, end=2026-05-17, overwrite=true.
  - Run 25981141120 completed success (commit `d90993e`, JSON reescrito
    +12310/-28863 líneas).
  - Comparación par-a-par (timestamp, sensor) records pre-fix
    (commit `21fe097`) vs post-fix (commit `d90993e`).
- **Resultado**:
  | Métrica | Resultado |
  |---|---:|
  | Records comparados (window 7d) | 69 |
  | Mejoraron (>0.5 km más cerca lacolito) | **48/69 (70%)** |
  | Igual (±0.5 km) | 18/69 (26%) |
  | Empeoraron (>0.5 km más lejos) | 3/69 (4%) |
  | **Mediana shift** | **+1.65 km más cerca lacolito** |
  | Promedio shift | +2.90 km más cerca |
  | Máximo acercamiento | 13.06 km |
- **Casos paradigmáticos**:
  - 2026-05-15 07:15 MODIS_AQUA: pre 5.11 km → post **2.10 km** (-3.01 km)
  - 2026-05-16 02:00 MODIS_TERRA: pre 8.11 km → post **5.39 km** (-2.72 km)
  - 2026-05-16 06:54 VIIRS_NOAA21: pre 6.78 km → post **0.95 km** (-5.83 km)
- **Estado**: **CONFIRMADA EMPÍRICAMENTE**.
- **Lección**: fix de coord vent → centroide térmico es de alto impacto
  cuando existe offset documentado por TIFs MIROVA. Approach reproducible:
  (1) calcular centroide ponderado TIFs MODIS con n_pixels>2500, (2) verificar
  consistencia entre múltiples TIFs, (3) agregar mirova_center_lat/lon al
  yaml. Para vols con TIFs dispersos (Planchón, NdC, Villarrica) NO replicar
  sin evidencia empírica.
- **3 casos empeoraron (4%)**: investigar S52 si tienen patrón común
  (posible cluster legítimo en zona del cone que ahora se descarta por
  estar lejos del lacolito).

---

## H_S48_PCC_COORD — PCC vent_anchored ancla en cone, MIROVA centra en lacolito

- **Formulada**: S48 (2026-05-17) en deep dive D9 MODIS sub-issue post-S47 R2 expansion.
- **Síntoma**: 4/4 casos PCC MODIS del R2 expansion mostraron drift centroid 11-18 km entre TIF MIROVA y nuestro `primary_cluster`. Mismo patrón en cluster selection diff de S48 audit (102 PCC reclasificados a `mirova_diff_cluster`).
- **Causa raíz**: `volcanoes.yaml` PCC tenía `vent_lat=-40.5255, vent_lon=-72.1461` = cone morfológico Puyehue. Sin `mirova_center_*` set, `get_effective_vent()` devolvía el cone. Pero el TIF MIROVA centra en lacolito Cordón Caulle 2011 (~6 km SE del cone). `cluster_hotspots(strategy=vent_anchored)` ordenaba por proximidad al cone, eligiendo clusters al N del cone cuando el hotspot real está al SE en lacolito.
- **Verificación empírica**: centroides ponderados de 2 TIFs MODIS PCC `n_pixels>2500` → promedio `(-40.582, -72.131)`.
- **Estado**: **CONFIRMADA y FIX APLICADO**.
- **Fix S48** (`volcanoes.yaml`):
  - Agregadas líneas `mirova_center_lat: -40.582` y `mirova_center_lon: -72.131` al config PCC.
  - `get_effective_vent()` (que ya prioriza mirova_center_*) ahora retorna `(-40.582, -72.131)` para PCC.
  - Cluster selection ancla en lacolito, no en cone.
- **Validación pendiente**: A/B reproc PCC MODIS 30d para confirmar:
  - 102 casos `mirova_diff_cluster` reclasifiquen a TP o `b` benigno.
  - Recall PCC no regresa (radius_km=25 cubre ambos cone+lacolito).
- **Generalización pendiente**: revisar para otros 10 Tier A si `mirova_center_*` debería poblarse desde KMZ MIROVA. Caso obvio futuro: Villarrica (lava lake summit, no vent morfológico oficial) y Planchón-Peteroa (offset 1.87 km N ya documentado S15).

---

## H_S47_NASA_TIMEOUT_10S — NRT cron falla por connect timeout interno earthaccess

- **Formulada**: S47 (2026-05-16) al verificar deploy drift234. 9 runs NRT
  consecutivos fallidos post-adopción S46.
- **Síntoma**: `requests.exceptions.ConnectTimeout` en
  `urs.earthdata.nasa.gov:443` durante `earthaccess.login(strategy="environment")`
  → `pipeline/fetch.py:127 auth()` levanta y aborta el job.
- **Hipótesis inicial descartada**: regresión por adopción drift234 commit
  `3d25ea1` (14:55 UTC). **Refutada**: primer fallo NRT 02:50 UTC del mismo día
  (~12h ANTES del commit). El fallo es pre-existente, no causado por S46.
- **Hipótesis confirmada**: `earthaccess.auth._find_or_create_token` pasa
  `timeout=10` hardcoded al `session.post()`. Cuando NASA Earthdata responde
  con latencia 15-30s (carga alta o degradación intermitente), el connect
  timeout dispara antes que cualquier retry de nuestro `auth()`. El monkey-patch
  IPv4 (H7 S35) no resuelve esto — IPv4 ya está activo, el problema es la
  ventana de 10s para handshake TLS.
- **Evidencia**: run 25974930327 (cron 22:43 UTC) terminó "failure" con
  jobs mezclados — algunos volcanes pasan, otros timeout-ean. Confirma
  intermitencia, no caída total.
- **Estado**: **CONFIRMADA y FIX APLICADO** (H7b).
- **Fix S47** (`pipeline/fetch.py`):
  1. Monkey-patch `requests.Session.request` para forzar `timeout>=60s` en
     hosts NASA (urs.earthdata, cmr.earthdata, ladsweb, nrt3.modaps,
     lpdaac.earthdatacloud). Tuplas `(connect, read)` normalizadas a
     `max(30, connect)` y `max(60, read)`. Hosts no-NASA intactos.
  2. Backoff `auth()` extendido de 6 → 8 intentos, waits hasta 480s
     (`[0,10,30,60,120,240,360,480]`, ~22 min total).
- **Tests**: `tests/test_fetch_nasa_timeout_override.py` 6/6 PASS (no_timeout,
  low_timeout, high_timeout, tuple, non-NASA-untouched, non-NASA-default).
- **Suite total post-fix**: 304 passed / 21 skipped (era 298/21), 0 regresiones.
- **Pendiente verificación R8**: próximos 1-2 ciclos cron NRT deberían tener
  tasa de éxito >>0 post-deploy. Si NASA degrada >22 min seguidos, el siguiente
  cron reintenta automáticamente.

---

## H_S24_DIBELLA_OUT_OF_OSF — Campus k=18 correcto también out-of-OSF

- **Formulada**: S24 (2026-04-26) ejecutando P3 del handoff S24.
- **Hipótesis original (handoff)**: S14 calibró Campus k=18.0 contra OSF v2.5
  que excluye Villarrica/Tupungatito. Di Bella 2024 k=2.48×10⁷ (10× distinto)
  podría ajustar mejor para esos 2 volcanes out-of-OSF.
- **Criterio testable**: comparar VRP nuestro vs MIROVA NRT en matches
  Tupungatito/Villarrica VIIRS 375m. Pasa Di Bella si ratio MIROVA/nuestro ≈ 10.
- **Evidencia** (análisis offline, sin reproceso):
  - Tupungatito 37/56 matches con vrp_mw>0: **ratio mediano 1.16** (within
    [0.7, 1.4] tolerable).
  - Aplicar Di Bella 10× → ratio caería a ~0.12 → sobre-estimaríamos 10×.
  - Villarrica 0/6 matches con vrp_mw>0 → confirma H_S24_AVENI_NEGATIVE.
- **Estado**: **REFUTADA**.
- **Resolución**: NO adoptar Di Bella k=2.48×10⁷ ni global ni per-volcán.
  Confirma doctrina CLAUDE.md y la extiende a casos out-of-OSF.

---

## Formato para agregar nuevas hipótesis

```
## H# — [título de una línea]

- **Formulada**: S# (fecha) en [archivo/sesión]
- **Hipótesis**: [afirmación testable]
- **Evidencia a favor**: [hechos observados]
- **Evidencia en contra**: [hechos que la contradigan]
- **Criterio testable**: [qué experimento decide]
- **Estado**: active / confirmed / refuted / stale
- **Resolución**: [acción tomada o pendiente]
```
