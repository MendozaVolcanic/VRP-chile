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
- **Estado**: **ACTIVE** — no implementada. Diferible a S19.

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
- **Estado**: **CONFIRMADA PARCIAL** (granules existen, falta integrar al pipeline).
- **Resolución**: implementación S18. NOAA-21 no tiene paper MIROVA que lo respalde, pero sí ATBD NASA (JPSS Rev C) — respaldo operacional suficiente.

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
- **Estado**: **CONFIRMADA** (drift documental sin resolver).
- **Resolución**: corregir en S18 con TDD.

---

## H13 — N·σ uniforme 3.0 es inferior al ~4× vs papers MIROVA (drift D2)

- **Formulada**: S17 (2026-04-23).
- **Evidencia**:
  - Coppola 2016a Tabla 1: MODIS 5/10/15 dual-ROI + día.
  - Di Bella 2024 §3.3 p.6: VIIRS 12 noche / 8 día, MODIS 5/10.
  - Nuestro código: 3.0 uniforme.
- **Hipótesis**: nuestro 3σ es demasiado permisivo, explica FPs sistemáticos.
- **Criterio testable**: test A/B de 3 configuraciones (actual, Coppola 5/10/15, Di Bella 12/8) en los 11 Tier A, sobre OSF v2.5. Adoptar el que maximice F1 sin recall < 0.60.
- **Estado**: **CONFIRMADA con ambigüedad** (ningún paper soporta 3σ uniforme, pero Coppola y Di Bella discrepan entre sí).
- **Resolución**: S18.

---

## H14 — VRP TIR: Stefan-Boltzmann vs Aveni Eq.9 (drift D3)

- **Formulada**: S17 (2026-04-23).
- **Evidencia**:
  - Aveni 2025 GRL: Eq.9 con k_TIR=60.17 μm·sr; Stefan-Boltzmann subestima 90% bajo 600 K.
  - Coppola 2024 cap Springer: Eq.16 Stefan-Boltzmann (usado canonicamente para low-T).
  - Nuestro código: Stefan-Boltzmann ([process_viirs.py:481](../pipeline/process_viirs.py#L481)).
- **Hipótesis alt A**: migrar a Aveni Eq.9 es correcto (paper más reciente autoritativo).
- **Hipótesis alt B**: mantener Stefan-Boltzmann (Coppola 2024 revisa post-Aveni y usa igual).
- **Criterio testable**: auditar Aveni 2024 TIRVolcH RSE (paper algorítmico previo a GRL 2025). Ver si MIROVA oficial adoptó Eq.9.
- **Estado**: **ACTIVE — AMBIGÜEDAD DOCTRINAL**.
- **Resolución pendiente**: S19.

---

## H15 — NOAA-21 VJ202 producto estable en CMR desde ene 2023

- **Formulada**: S17 (2026-04-23) sub-hipótesis de H10.
- **Evidencia**: earthaccess retorna VJ202IMG + VJ202MOD v2.1 Standard + NRT para fechas 2026-04-10 y 2026-04-22.
- **Respaldo documental**: JPSS VIIRS Radiometric ATBD Rev C (descargado S17).
- **Estado**: **CONFIRMADA**.

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
