# Auditoría Integral S81 — VRP Chile

**Fecha**: 2026-05-26
**Método**: 12 subagentes paralelos (read-only) sobre los 12 frentes del proyecto.
**Output**: este doc + 8 tareas trackeables + propuesta de siguiente paso.

---

## TL;DR — 1 párrafo

El pipeline está **operacionalmente sano** (NRT recuperado hace 24h, dashboard parity 100%, tests 507 verde, 11/11 mirova_center documentados). Pero hay **3 deudas concretas no triviales**: (1) un **bug VRP_TIR** activo que produce magnitudes >1000× la realidad en 726 records (Stefan-Boltzmann sobre máscara sin restar background — plan F46 escrito S76, sin implementar), (2) **PCC con 15 duplicados** por overlap reproc S62 (workflow store.upsert_record no deduplica), (3) **>2000 FPs MODIS catastróficos** (cluster 200-970 pixels, 100-1362 MW) en PCC/PP/Chaiten/Tupungatito que probablemente sean **incendios forestales** que MIROVA filtra arquitecturalmente. F66 (la prioridad declarada al inicio de la sesión) sigue siendo válida como P1, pero **F46 puede ser más urgente** porque desbloquea F31 + sanea el TIR del dashboard.

---

## Glosario de hallazgos por frente

### 1. NRT health (últimos 14 días)

**Estado**: ⚠️ crítico → ✅ recuperado.

- 14 días con tasa de fallo 84.5% (98/116 runs failed) por single root cause: **timeout NASA Earthdata Auth para IPs Azure GH-hosted** (DoS-mitigation greylist).
- Commit `9d9e13f0` "F55/S77 fix earthaccess Store /profile bypass" mergeado **2026-05-25 12:32 UTC** cerró el último camino al endpoint bloqueado.
- **7 runs consecutivos success post-fix** (45/45 jobs verde cada uno).
- **Lascar lag 76.7h** (único Tier A fuera de "≤55h"). No urgente — posible ausencia satelital ese día, monitorear 48h.
- **EARTHDATA_TOKEN expira ~2026-07-20** (60d post-deploy 2026-05-21). Setear recordatorio.

**Acción S81**: vigilar 24-48h, tag `nrt-recovered-s81` si sostiene.

### 2. Dashboard parity local vs Pages

**Estado**: ✅ perfecta.

- 11/11 Tier A: n_records y last_dt idénticos worktree ↔ origin/main ↔ GitHub Pages.
- Frontend chart gotcha VIIRS 375m (`vrp_mw` no `vrp_mir_mw`): correcto en código actual.
- Deploy workflow 14/15 success últimos 7 días (1 cancelled por concurrency, esperable).
- Solo sirve perfil `mirova_equivalent` (sin contaminación experimental).

**Acción S81**: ninguna — el dashboard refleja honestamente el pipeline.

### 3. Anomalías numéricas data/mirova_equivalent/

13,207 records auditados sobre los 11 Tier A. **Top 5 anomalías por gravedad**:

| # | Anomalía | Gravedad | Conteo |
|---|---|---|---|
| 1 | **PCC duplicados 2026-05-18/19** (7 con datos divergentes) | CRÍTICA | 15 |
| 2 | **VRP_TIR / VRP_MIR >1000×** (Stefan-Boltzmann sobre máscara contaminada) | ALTA — drift científico | 726 |
| 3 | **vrp_mw=0 con n_anomalous_pixels>0** (sin flag de razón) | ALTA — schema | 2117 |
| 4 | **n_hotspots_clustered > n_anomalous_pixels** (físicamente imposible) | MEDIA — schema/lógica | 228 |
| 5 | **Lastarria 2026-04-23 σ_bg=149.18K** (imposible físicamente) | MEDIA — outlier patológico | 1 |

**Top 10 VRP MIR** todos <2000 MW (rango Wooster aceptable, F2.8 saturation guard funcionando — sin survivors >5000 MW).

**Top 10 VRP_TIR/VRP_MIR**: Villarrica 2026-02-11 mir=0.98 MW vs tir=5680 MW (ratio 5802×). Patrón sistemático que confirma bug F46.

**Acción S81**: dedup PCC (script + tag), gate dashboard VRP_TIR hasta F46, agregar test sintético "compute_bg_stats σ>50K".

### 4. Gap MIROVA CSV consolidado (ventana 45d)

| Recall global Tier A | **97.8%** (262/268 detecciones MIROVA cubiertas) |
|---|---|
| Precision global | baja (0-33% según volcán) |
| FN críticos | 10 total: 9 VIIRS-I 375m sub-pixel + 1 VIIRS-M |
| FP catastróficos | **>2000** MODIS con cluster 200-970 px, VRP 100-1362 MW |
| Volcán recall 0% | **NevadosDeChillan** (4 FN, todos sub-pixel) |
| Ratio sistemático crítico | **Tupungatito 19.68×** (26 records VIIRS-I) |

**⚠️ Diagnóstico re-leído S81 con aclaración Nicolás**: el subagente comparó nuestras detecciones SOLO contra `ALERTA_TERMICA` del CSV. Pero `FALSO_POSITIVO` y `RUTINA NULO` **no son filtros de MIROVA** — son tags del scraper Mirova-v1 nuestro. `FALSO_POSITIVO` = MIROVA SÍ vio el hotspot pero quedaba fuera del radio per-volcán; el scraper lo descartó como atribución al volcán. Por lo tanto, parte de los >2000 "FPs MODIS" pueden ser **detecciones MIROVA reales en clase `far`** — concordancia, no discrepancia. **Acción correcta**: re-correr gap analysis con ground truth `ALERTA_TERMICA ∪ FALSO_POSITIVO` antes de hipotetizar gate MOD14 active fire o cualquier otro fix. Ver `memory/reference_mirova_csv_scraper_tags.md`.

**Acción S81**: investigar gate fire-detection (F-S81-A), reproducir 4 FN NdC (F-S81-B), refrescar CSV ground truth (es del 2026-05-15, 11 días atrás).

### 5. Cobertura mirova-tif-archive

- Repo `MendozaVolcanic/mirova-tif-archive` **vivo** (last push 2026-05-26 10:19 UTC).
- **Histórico solo desde 2026-05-08** (12 días disponibles localmente). NO existe pre-mayo 2026 y nunca existirá (MIROVA sobreescribe TIFs).
- 2684 TIFs en 12 días, ~21/día/volcán × 3 sensores.
- **F66 Tasks 9-11 R2 pixel-level viable** con ventana 12d (≥250 candidatos por volcán Copahue/Llaima/Villarrica, >50× el mínimo F66 Task 13 que pide 15).
- Bloat PNG: 1.9 GB de 4.4 GB (intermedios committeados, candidato a pruning).
- Local 6 días atrás del remoto — hacer `git pull` antes de cualquier R2.

**Acción S81**: pull local, planificar F66 con ventana 12d en vez de 30d.

### 6. Backlog hipótesis abiertas

**27 items abiertos** en backlog/HYPOTHESIS_LOG/MIROVA_DIVERGENCES catalogados con impacto, esfuerzo, prioridad. Top 5 candidatos a próximo paso S81:

| # | Item | Esfuerzo | Por qué |
|---|---|---|---|
| 🥇 | **F66 Tasks 7-15** | 8-12h | Tasks 0-6 done. Solo profile yaml + reproc serial + R2 manual + PR |
| 🥈 | **F2.1 unsuitable filters** Coppola 2016a §267-273 | 6-10h | 4 gaps bibliografía ⭐⭐⭐. Causa probable drift Muy Bajo. Verificar si quedó branch en limbo S72 |
| 🥉 | **F31 VRPTIR Aveni A2** | 8-12h | **Bloqueado** — F46 va primero, además evento baja-T no se materializó Q1 2026 |
| 4 | **D7 local p95 VIIRS-I 375m** | 6-8h | Drift histórico documentado S17, A/B vs OSF v2.5 barato. Neutralizado hoy por bt_path off |
| 5 | **Frontend bugs 6+7+11a** | 45 min | Quick win UX |

**Items para archivar**: D1/D3/D4/D6/D8 background ring, H1-H10 cerradas, 9/11 mirova_center cerrado S80, backlog handoffs históricos.

### 7. Git/GitHub estado

- **0 PRs abiertos** (saludable).
- **24 branches mergeadas safe-delete** (catalogadas en BRANCHES_CLEANUP_S80.md).
- **`claude/nostalgic-aryabhata-e05d1e`**: investigado en A1, **0 contenido único vs main**, ambos archivos novedosos ya en main. Recomendación: tag defensivo + delete.
- `claude/sweet-austin-b5413b`: 16 commits S46 tests R2 pixel-level — verificar.
- Worktree raíz `VRP Chile/` (s15-dev): **1185 commits ahead / 2 behind** main. Merge debt masivo. Decidir sincronizar o eliminar.
- Repo size sano (~27 MB working tree, 545 MB packs, 27 packs = 2-3 repack ciclos).
- Minor garbage flag → `git gc --aggressive` recomendado.
- `Mirova-v1` scraper NO encontrado localmente — verificar.

**Acción S81**: cerrar A1 nostalgic-aryabhata, decidir worktree s15-dev, gc aggressive.

### 8. Re-audit drifts D1-D7 + nuevos

**Estado drifts originales S17**:
- D1 (kernel median→mean): ✅ RESUELTO S17.
- D2 (3σ uniforme): ✅ RESUELTO S27+ (dual-ROI 5σ summit / 10σ scene).
- D3 (TIR Stefan-Boltzmann vs Aveni Eq.9): ✅ RESUELTO S17.
- D4 (dashboard scale): ⏳ pendiente sin urgencia.
- D5 (no supervisión humana): ✅ documentado design choice.
- D6 (std_bg global): ❌ REFUTADO S21.
- D7 (local p95 VIIRS-I): ⚠️ neutralizado por bt_path off, no resuelto.

**Drifts nuevos detectados S33-S77** (todos mitigados o documentados):
- D8 (bug mirovaEqVrp S33), D10 (single-pixel sub-MW S77), D11 (vrp_tir consistency gate S77), D12 (BT saturation guard S73), D13 (test1_lbg_global S39), D14 (vent-anchored clustering S38), D9 (cap path D cirrus S71) — todos con tests + flags + adopción controlada.

**Coherencia código vs papers MIROVA canonical** (Torino+Firenze+Sapienza Roma): ✅ Wooster coeffs, A_pix nadir, Planck constants, lambdas, K1 thresholds, C1 contextual, Tests 2∧3 first-pass + second-pass adjacent, ETI scene-wide cuadrática, unsuitable mask — todos verbatim citados.

**Sin hardcodes sin justificación**.

**Acción S81**: ninguna acción urgente (todos los drifts críticos cerrados o mitigados). Considerar guard test para D7 (test que falle si alguien re-activa bt_path_hot sin agregar local_threshold).

### 9. Tests health

- **507 passed, 24 skipped, 0 failed, 0 errors** en 8s.
- 16 skips: `test_golden_records.py` (obsoletos pre-S27 — pendientes regenerar 50+ sesiones).
- 8 skips: `test_r2_pixel_level.py` (opt-in con tifffile).

**Gap crítico de cobertura**:
- `process_viirs.py`: **14%** cobertura
- `process_viirs_mod.py`: **7%** cobertura
- Estos son el corazón del clon MIROVA. El bug `compute_bg_stats` que S79 introdujo y S80 detectó habría caído con un test unitario de 5 líneas.

**R1 audit_metrics: 100% cobertura** (17 tests, bug S33 reproducer explícito). OK.

**Acción S81**: agregar 10-15 tests sintéticos sobre VIIRS processors core helpers. Regenerar o borrar golden records. CI gate `--cov-fail-under=50` gradual.

### 10. Validación mirova_center 11 Tier A

- 9/11 actualizados S80 desde KMZ: Δ <5 m con re-parse fresco. ✅
- PlanchonPeteroa: yaml coincide con KMZ a 5 m (manual previo era correcto). ✅
- **PuyehueCordonCaulle: yaml difiere 1.39 km del KMZ oficial** ⚠️
  - yaml: `-40.582, -72.131`
  - KMZ: `-40.5903, -72.1187`
  - No afecta clasificación summit (inner=20 km absorbe el error), pero sesga ROI ~3 pixels VIIRS para R2 pixel-level.

**Tupungatito offset 4.86 km vent→center confirma S15** ("3 km SE" era subestimación humana, el KMZ es exacto).

**Acción S81**: update yaml PCC (tag pre-s81-pcc-mirova-center), confirmación A45 Nicolás.

### 11. VRP TIR Aveni F31 estado

- **Implementación PARCIAL** — diagnostic-only, default OFF.
- F31 Tasks A2 (Eq.8/9 verbatim) + TIRVolcH detector mergeados S75. Helper + tests done.
- `experimental_lowT.yaml` existe pero **nunca ejecutado** (data/experimental_lowT/ no existe).
- **El "evento baja-T" enero-marzo 2026 no se materializó como evento agudo.** El régimen es permanente fumarólico (Lascar, Lastarria, PCC, Tupungatito, Isluga, PP). MIROVA NRT captura con VIIRS-I 0.05-5 MW; nosotros lo perdemos en algunos casos.
- **F31 bloqueado por F46**: cualquier integración VRPTIR operacional hereda el mismo bug Stefan-Boltzmann sobre máscara contaminada.
- A35 PDF Aveni 2025 GRL paywalled (confidence:medium) — falta verificación verbatim 9/9 como se hizo con Aveni 2024 RSE.

**Acción S81**: NO adoptar F31 operacional. Avanzar F46 primero. Actualizar MEMORY.md eliminando "esperar evento baja-T".

### 12. Race conditions / data integrity

- **Damage residual: ~0.11%** (15 filas extras en PCC, 7 con datos divergentes).
- Causa real: **overlap reproc S62 humano** (2 commits sobre mismo rango sin dedup en store.upsert_record), NO race CI.
- Mitigación S22 (git add solo archivo del job actual) **cerró la clase race S25 efectivamente**.
- nrt.yml `max-parallel: 8` es seguro post-S22 (archivos disjuntos por volcán). A47 aplica a reprocs históricos paralelos del mismo volcán, no NRT.
- 19 tags defensivos disponibles para rollback.

**Acción S81**: hot-fix PCC dedup (15 min) + endurecer store.upsert_record con dedup key (30 min) + agregar M11 a META_RULES (reprocs manuales overlap <24h).

### 13. Tests/Workflows/Tasks borrados S77/S80

- **0 tests críticos borrados injustificadamente**.
- 1 test borrado (`test_sigma_cap_eruption.py` S32) — justificado, feature revertida a spec MIROVA S27.
- 44 workflows archivados (no borrados) en `_archive/`, todos con README contextual.
- 30 tasks archivadas (versionadas en git, recuperables), todas con README explicativo.
- Cleanup S77/S80 fue íntegro, conservador, documentado, reversible.

**Acción S81**: ninguna.

---

## Hallazgos prioritarios (consolidación cross-frente)

### 🔴 P0 — Atención científica/operacional

1. **PCC duplicados (15 filas, 7 divergentes)** — frente 3+12. Hot-fix puntual + endurecer store.upsert_record. Tiempo: 45 min. Requiere A45.

2. **VRP_TIR drift 726 records** — frente 3+11. Plan F46 escrito sin implementar. Bloquea F31. **Mientras tanto el dashboard expone vrp_tir hasta 5680 MW que no son reales.** Hay dos opciones:
   - **Opción mínima (1h)**: gate frontend — esconder columna VRP_TIR del dashboard + nullear vrp_tir_mw en JSON publicado hasta que F46 esté.
   - **Opción completa (14-16h)**: implementar Plan F46 según `docs/F46_VRP_TIR_BUG_S76.md`.

3. **~2300 FPs MODIS Subtipo C — gate intra-radio MIROVA faltante (re-audit S81 v2)** — frente 4. El re-audit con tags correctos (`memory/reference_mirova_csv_scraper_tags.md`) confirmó que el problema es real pero el diagnóstico cambia. Solo 2.1% (64/2986) de los "FPs originales" eran **concordancia far** (MIROVA tagged FALSO_POSITIVO + nuestro `distance_class=far`). El 77% (2295/2986) son **Subtipo C**: MIROVA procesó el granule, miró dentro del radio del volcán, y publicó `RUTINA` (sin alerta) — nosotros sí alertamos. **MIROVA tiene un gate intra-radio que no tenemos**. Candidatos (Coppola 2016a Table 1): N·σ MODIS 5/10/15σ (no 3σ uniforme), NDVI/land-cover, cluster ≥2 px MODIS. **Re-formular F-S81-A**: no es "gate del radio MIROVA externo" (eso solo explica 2%), es **gate intra-radio MIROVA**. Plan: simular cada candidato sobre los ~800 FPs MODIS Tier A para ver cuál corta mejor. Ver `experiments/_s81_v2_out/REPORT_S81_GAP_V2.md`.

   **Hallazgo secundario**: 64 casos Subtipo A son casi todos VIIRS375 (Isluga 18, Lastarria 11, PP 9, Lascar 6) con nuestro `distance_class=summit` pero MIROVA tagged `FALSO_POSITIVO` — divergencia entre nuestro `inner_radius_km` yaml y radio efectivo MIROVA. Calibración VIIRS375 a revisar.

### 🟡 P1 — Mejora operacional

4. **F66 Tasks 7-15** — frente 5+6. Plan listo, branch viva, 12d TIFs disponibles (más que suficiente). 8-12h.

5. **NdC recall 0%** — frente 4. 4 FN específicos VIIRS-I 375m sub-pixel. 4h investigación + posible fix.

6. **F2.1 unsuitable filters** — frente 6+8. Verificar si quedó branch S72 en limbo o requiere implementar fresh. 6-10h.

7. **Update mirova_center PCC** — frente 10. Cambio 2 líneas yaml + tag + commit. 15 min. Requiere A45.

### 🟢 P2 — Higiene técnica

8. **Cerrar A1 nostalgic-aryabhata** — frente 7. Tag + delete + persistir en BRANCHES_CLEANUP_S80.md. 5 min.

9. **Tests sintéticos process_viirs core** — frente 9. Subir cobertura 14%→50%. 4-6h.

10. **Worktree raíz s15-dev** — frente 7. 1185 commits ahead. Decidir merge o eliminar.

11. **Regenerar golden records** — frente 9. 16 skips permanentes. 2-3h.

12. **EARTHDATA_TOKEN expiry recordatorio** — frente 1. Calendario 2026-07-20.

---

## Lo que NO está pasando (vale notar)

- ✅ Pipeline NRT operacional sano (post-2026-05-25 13:28Z).
- ✅ Dashboard refleja honestamente el pipeline (parity perfecta).
- ✅ Drifts D1-D6 originales S17 cerrados.
- ✅ Coherencia código vs papers MIROVA canonical.
- ✅ Bug `mirovaEqVrp` S33 cubierto por 17 tests R1.
- ✅ Cleanup S77/S80 íntegro.
- ✅ No hay corruption de datos por race CI (mitigación S22 efectiva).
- ✅ Branches stale catalogadas, descartables.

---

## Recomendación de siguiente paso

**No es F66.** O al menos no F66 *primero*.

**Propuesta**: bloquear el dashboard VRP_TIR (1h) + dedup PCC (45 min) + cerrar A1 nostalgic-aryabhata (5 min) + update mirova_center PCC (15 min) → cerrar P0 inmediato en 2h. Después decidir entre F66 vs F46 vs F2.1 con contexto limpio.

**Por qué no F66 primero**:

- F66 está ready (Tasks 0-6 done, branch viva, plan claro).
- Pero F66 ataca el problema de **inflación de magnitudes en cirrus** — beneficio incremental sobre un pipeline que ya tiene cap `path_d_only_cap_mw=5.0` mitigando el síntoma.
- Mientras tanto, el dashboard está mostrando vrp_tir_mw=5680 para Villarrica 2026-02-11. **Eso es magnitud volcánica falsa visible al público.** Es más urgente sanear el output que continuar mejorando la calibración interna.

**Por qué no F46 directo**:

- F46 son 14-16h. Es trabajo profundo.
- Pero el dashboard está exponiendo el bug AHORA. La opción "gate dashboard VRP_TIR" en 1h cierra la exposición sin comprometer el fix definitivo.

**Por qué F2.1 vale como contender**:

- Si la causa de los FPs MODIS catastróficos (>2000 records) es ausencia de algún unsuitable filter de Coppola 2016a, F2.1 podría cerrar simultáneamente el ruido MODIS + el drift Muy Bajo + parte del 43% residual Tupungatito.
- Pero F2.1 no toca VRP_TIR. F46 sí.

**Mi recomendación final**: **Bloque inmediato P0 (2h) → decisión F46 vs F2.1 vs F66 con números limpios**. Si los FPs MODIS resultan ser incendios forestales (verificable rápidamente con MOD14), F-S81-A puede ser un payoff aún mayor que F46.

---

## Archivos consultados clave

- `docs/SESSION_INDEX_CONSOLIDATED_S80.md`
- `docs/META_RULES_S80.md`
- `docs/HYPOTHESIS_LOG.md`
- `docs/DRIFTS_S17.md`
- `docs/MIROVA_DIVERGENCES.md` y `docs/MIROVA_DIVERGENCES_CATALOG_S71.md`
- `docs/F46_VRP_TIR_BUG_S76.md`
- `docs/F31_AVENI_VRPTIR_PLAN_S74.md`
- `docs/superpowers/plans/2026-05-26-f66-hybrid-bg-kernel-consistency-gate.md`
- `pipeline/audit_metrics.py`, `tests/test_audit_metrics.py`
- `pipeline/process_viirs.py`, `pipeline/process_viirs_mod.py`, `pipeline/process_modis.py`
- `pipeline/vrptir.py`, `pipeline/detect_tirvolch.py`, `pipeline/vrp_regimes.py`
- `pipeline/detection_context.py` (kernel + Tests 2∧3)
- `pipeline/profiles/mirova_equivalent.yaml`, `pipeline/profiles/experimental_lowT.yaml`
- `volcanoes.yaml`
- `.github/workflows/nrt.yml`, `pages-deploy.yml`
- 11 × `data/mirova_equivalent/<Vol>.json` (13,207 records)
- `15_05_2026_registro_vrp_consolidado.csv` (CSV ground truth MIROVA NRT)
- `~/.../mirova-tif-archive/` (2684 TIFs ventana 12d)
- `kmz/*.kmz` (15 archivos GroundOverlay MIROVA oficial)
- 19 tags defensivos `pre-s*-*`
- 36 branches `claude/*` (24 mergeadas, 12 con commits únicos)
- 67 tests vivos + 24 skipped justificados

---

## Próximas tareas pendientes (TaskList)

1. ⏳ Escribir AUDIT_INTEGRAL_S81.md (este doc — completado al cerrarlo).
2. ⏳ Cerrar A1 nostalgic-aryabhata (tag + delete + persistir).
3. ⏳ Fix PCC dups + endurecer store.upsert_record.
4. ⏳ Fix VRP_TIR drift F46 o gate dashboard mínimo.
5. ⏳ Update mirova_center PCC.
6. ⏳ Investigar FPs MODIS catastróficos (gate MOD14).
7. ⏳ NdC recall 0% — investigar 4 FN específicos.
8. ⏳ Decidir siguiente paso operacional S81 con Nicolás.
