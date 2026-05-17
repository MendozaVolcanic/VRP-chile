# Hypothesis Log — VRP Chile

> Bitácora cronológica de hipótesis formuladas sobre el pipeline. Cada entrada tiene ID (H#),
> fecha, evidencia a favor, evidencia en contra, estado (active/confirmed/refuted/stale),
> criterio testable, y resolución. **Nunca se borra una entrada** — se marca `stale` si queda obsoleta.

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
