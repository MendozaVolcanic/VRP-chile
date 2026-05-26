# SESSION_INDEX_CONSOLIDATED_S80 — Mapa canónico VRP Chile

> Documento ancla. **Leer primero al entrar al proyecto en cualquier sesión nueva.**
> Reemplaza a `docs/SESSION_INDEX.md` previo. Recopila S1–S80 con
> respaldo cruzado de git log, PRs mergeados, drifts cerrados, hipótesis,
> flags activos y papers verificados.
>
> **Última actualización**: 2026-05-26 (S80, auditoría post-pérdida-contexto).
> **Misión proyecto**: clon literal MIROVA con leves diferencias permitidas.

---

## 0. Lectura de orientación rápida (5 minutos)

Si entrás a una sesión nueva y querés saber dónde estamos parados:

1. **Estado operacional NRT**: pipeline corre cron cada 2h sobre 11 volcanes Tier
   A. Última corrida exitosa: ver `gh run list --workflow=nrt.yml --limit 5`.
2. **Misión**: clon MIROVA. Lo que no esté respaldado por paper Coppola/Laiolo/
   Massimetti/Campus/Aveni/Cigolini NO entra al perfil `mirova_equivalent`.
3. **Última feature en curso (S80)**: **F66 dual-bg consistency gate** —
   implementación Tasks 0–6 (helper + 9 tests + integración en los 3 sensores
   I4/M13/B21-22) en branch `claude/s79-f66-hybrid-bg-gate`. **Pending Tasks
   7–15** (profile yaml + reproc serial + R2 manual + PR).
4. **Reglas vinculantes activas**: A45 (tag defensivo antes de tocar pipeline
   NRT), A47 (NO paralelo sobre `data/mirova_equivalent/`), A44 (worktrees
   dedicados per subagente paralelo). Detalles en `docs/META_RULES_S80.md`.

---

## 1. Cronología por fases (S1–S80)

### Fase A — Bootstrap pipeline + drifts doctrinales (S1–S20)

| Sesión | Hito |
|---|---|
| S1–S8 | Pipeline VIIRS+MODIS inicial, 11 Tier A, NTI/vent paths básicos |
| S9–S14 | Calibración Wooster coeff empírica (error ≤0.17% vs OSF v2.5), geometría MIROVA-equivalent (`radius_km=25` + `inner_radius_km` per-vol oficial KML) |
| S15–S16 | P3.1 dual-ROI thresholds, P3.2 dNTI contextual 8-vecinos, Tema E ROI bbox cuadrado, Tema F sigma-cap eruption-path VIIRS |
| **S17** | **MILESTONE hallazgo H10**: NOAA-21 (VJ202IMG/MOD) faltaba en `fetch.py`. MIROVA sí lo procesa. Cuello de botella real de recall Tupungatito/Chaitén NO era sigma-gating (H1 refutada). Drifts D1–D7 identificados. |
| S18 | Integración NOAA-21 operacional. +14/+1/+3 TPs (Lascar/Chaitén/Tupungatito). |
| S19–S20 | M1-M4 seguridad, Regla D vent-priority. Recall 0.25→0.69, Chaitén 100%. |

**Salida fase A**: pipeline reproducible Wooster + NTI + Test 1, geometría
oficial MIROVA, drifts cerrados D1 ✅ y D3 ✅, D2 con CAP empírico.

### Fase B — Calibración fina volcán-a-volcán (S21–S65)

| Sesión | Hito |
|---|---|
| S21 | D6 REFUTADO (std_bg local/global=0.81, glaciar Tupungatito afecta toda el área). Schema diag_* OBLIGATORIO. A6/A7 sobre lectura completa de callers. |
| S22–S26 | Test 1 integrated-ROI implementación. Villarrica 0→6/6 detecciones. 21 PRs mergeados. |
| **S27** | **MILESTONE Test 1 ON cierra D4**. Recall 50%→80%. Clon literal cercano. |
| S31 | FRONTIER 83.5% recall, ratio 3.72× — balance mejor histórico |
| S32–S44 | D8 vent-anchored, Driver A+B, R2 píxel-level. F1 89.2%→89.9%. 260/16/0 tests |
| S45–S47 | D9 summit-priority, F2.8 infraestructura. R2 scaffold. 305 tests. |
| S60–S62 | **Adopción operacional `enable_local_kernel_bg`**: Villarrica 31×→2.16×, Lastarria 6.78×→1.07×, PlanchónPeteroa adoptado. |
| S63–S65 | Chaitén/PCC adoptados, Tupungatito `mirova_center` (offset 2.99 km SE del vent), R2 retroactivo. 7/9 calibrados ratio ~78%. |

**Salida fase B**: 7/9 volcanes Tier A con ratio MIROVA ~78%, kernel-bg local
adoptado en 5/11. F1 89.9% pico histórico.

### Fase C — Quemada de bugs operacionales + brainstorms (S66–S80)

| Sesión | Hito |
|---|---|
| S66–S72 | Validación 21 PRs, D6/D7/D9 análisis. 5/5 R2 pass, NRT local 100%, 507 tests. |
| S73–S75 | **F2.8 saturation guard MODIS+VIIRS** (PR #133, hallazgo PP 695,431 MW fósil). F31 Aveni VRPTIR plan + TIRVolcH detector + Aguilera 2021. 456 tests. 8 PRs. |
| S76–S78 | **65 PRs S76-S78 fixes críticos**: F46 Stefan-Boltzmann I-band, F47 cluster rescate, F50 D9 cap scene-wide, F52 Villarrica/Tupu/PCC caps + single-pixel mode, F53 Test1 unbound, F54-F55 sync + NRT auth. Brainstorms F60-F66 (read-only no-fix). |
| S78 | **Insight clave F65 refutado**: Path B NTI absoluto (>-0.8) **NUNCA dispara en Andes Chile** (0/8142 TPs). F65 TOP 1 era noop. F66 dual-bg consistency gate es el approach correcto. |
| **S79** | F66 design + plan bite-sized 15 tasks + Tasks 0–4 implementación (helper `apply_f66_consistency_gate` + 9 tests + integración VIIRS-I 375m). Tag `pre-s79-f66-hybrid` → `9d4dd082`. Cleanup CI (PR #217 archive 9 reproc-* legacy, fix YAML roto). |
| **S80** | **Esta sesión.** Tasks 5–6 done (M-band + MODIS). Fix regresión `compute_bg_stats` (introducida por Task 1 insert). Auditoría completa post-pérdida-contexto. Este documento + META_RULES_S80. |

**Salida fase C**: pipeline operacional estable (7/10 corridas OK post-PR #190),
516 tests passing, F66 implementación 6/15 tasks. Velocidad de cambio
preocupante (117 PRs en 10 sesiones).

---

## 2. Drifts D1–D7 — estado final consolidado

| ID | Tema | Estado | Resolución | Paper origen |
|---|---|---|---|---|
| **D1** | Kernel 8-vec mean vs median | ✅ Resuelto S17 (commit `f78ad5d`) | Cambio `np.median`→`np.mean` en `detection_context.py:30-35` | Coppola 2016a SP426.5 línea 357, confirmado Campus 2024 BV 86:25 |
| **D2** | N·σ uniforme 3σ vs Coppola 5σ/10σ/15σ (Tabla 1) / Di Bella 12σ noche/8σ día | ⚖️ **Empíricamente CAP anula efecto** | `MAX_SIGMA_COMPONENT_K=7K` hace converger 3σ y 12σ. Mantener 3σ+cap (F1=0.36 supera 5σ y 12σ teóricas) | Coppola 2016a Tabla 1, Di Bella 2024 §3.3 (NO MIROVA — RSDF Catania, ver A9) |
| **D3** | TIR Stefan-Boltzmann vs Aveni 2025 k_TIR=60.17 | ✅ Resuelto S17 | Aveni 2024 RSE Eq.5 confirma Stefan-Boltzmann puro. Aveni 2025 GRL es refinamiento futuro (Eq.9), NO migración operacional | Coppola 2024 Springer cap Eq.16, Aveni 2024 RSE Eq.5 |
| **D4** | Escala dashboard Low/Medium/Extreme | 📋 Feature gap UI | No es bug — falta categorización visual | Coppola 2023 Frontiers p.5 |
| **D5** | Supervisión humana (nosotros automático puro) | ❌ No actuar | Diferencia de diseño aceptada (MIROVA NRT también es automático; OSF v2.5 tiene curación manual post-hoc) | Coppola 2023 §2.5 |
| **D6** | Background localizado 5×5 km vs ring 5–25 km | ❌ Refutado S21 | std_bg local/global = 0.81. Glaciar Tupungatito afecta toda el área. **NO reemplazar ring.** | (refutado por experimento propio S21) |
| **D7** | Local ROI threshold p95 ausente en VIIRS 375m (presente MODIS + VIIRS 750m) | ⏳ Diferido | Pendiente A/B test vs OSF para decidir si agregar o quitar | Coppola 2016a implícito |

**Aclaración crítica**: F66 **NO es D6 redux**. D6 proponía reemplazar el
ring por kernel local. F66 los usa **juntos** como gate de consistencia: el
ring sigue dando `t_bg`, `std_bg`, threshold; el kernel local 3×3 valida
que el calor del pixel candidato es espacialmente compacto, no artefacto
de heterogeneidad regional.

---

## 3. Features Fxx — estado adopción operacional

### Adoptadas en `mirova_equivalent.yaml` (NRT cron 2h)

**Detección térmica core**:
- ✅ `enable_eruption_path` (Path A clásico BT > threshold)
- ✅ `enable_test1_path` (Test 1 integrated-ROI Wooster, MILESTONE S27)
- ✅ `enable_dual_roi_bt` (Coppola 2016a Tabla 2 dual-thresholds summit/scene)
- ✅ `enable_test1_lbg_global` (Wooster L_bg global, S39)

**Filtrado contextual**:
- ✅ `enable_dnti_contextual_path` (Path D dNTI 8-vec kernel, P3.2 S15)
- ✅ `enable_dnti_dual_roi` (dual-ROI summit/scene en dNTI, P3.1 S15)
- ✅ `enable_first_pass_tests_2_and_3` (NTI+ETI primeras pasadas)
- ✅ `enable_dual_roi_first_pass` + `enable_dual_roi_second_pass`
- ✅ `enable_second_pass_adjacent` (recapture adyacente S46)

**Geometría/clustering**:
- ✅ `enable_vent_anchored_clustering` (D8 S32-S44)
- ✅ `enable_pixel_level_distance_filter` (S14 schema final_hotspot_*)
- ✅ `enable_local_kernel_bg` (S60-S65 Villarrica/Lastarria/PP)

**Hardening recientes (S73-S77)**:
- ✅ `enable_single_pixel_sub_mw_mode` (F52-B Villarrica sub-MW)
- ✅ `enable_vrp_tir_consistency_gate` (F46-F47 Stefan-Boltzmann TIR)
- ✅ `enable_bt_sat_secondary_guard` (F2.8 S73 saturation MODIS+VIIRS)

**Defaults profile.py sin override yaml (cuidado, ON sin enunciar)**:
- ⚠️ `enable_unsuitable_filters_267_273` default `True` (S72 F2.3) —
  **operacional pero no aparece en yaml**. Riesgo de pérdida de contexto.

### Disabled en operacional (código vivo por si se reactiva)

- ❌ `enable_vent_path`, `enable_vent_path_modis` (Path C, refutado S20)
- ❌ `enable_nti_relative_path` (Path B NTI absoluto — **nunca dispara en
  Andes Chile**, F65 confirmó, 0/8142 TPs)
- ❌ `enable_exclude_zones` (parche pre-MIROVA, S27 T3 desactivó)
- ❌ `enable_bt_path_hot` (refutado pre-S27)
- ❌ `enable_test1_pixel_filter` (refutado S33)

### Pending implementación (no en mirova_equivalent todavía)

| Feature | Estado | Branch / Profile | Próximo paso |
|---|---|---|---|
| **F66** dual-bg consistency gate | Tasks 0-6 done (S79+S80) | `claude/s79-f66-hybrid-bg-gate` | Task 7 profile yaml `_f66_dt5k.yaml`, Tasks 9-11 reproc serial, Task 13 R2 manual Nicolás |
| **F31 VRPTIR Aveni** | Helper + tests done (S75), pipeline integración A2 **pausada por A45** | `experimental_lowT.yaml` listo | Tag defensivo + confirmación Nicolás + Task A2 cuando hay evento baja-T (enero-marzo) |
| **F60 VSROI polygonal** | Brainstorm S78 read-only | — | Diferido, no urgente |

### Flags huérfanos (en profile.py sin yaml que los pruebe)

Detectados S80 — son drifts S46 que no llegaron a A/B isolation:
- `enable_test1_k1_retire_from_hot_mask` (drift #1a)
- `enable_test1_k1_bg_exclude` (drift #1b)

**Decisión S80**: dejar en código por trazabilidad (refs Coppola 2016a:352-356)
pero documentar como "no operacional, no A/B planeado". Si en algún momento
volvemos a auditar drift #1, ahí se rescatan.

---

## 4. Papers canónicos — estado verificación verbatim

### Grupo MIROVA (Torino + Firenze + Sapienza Roma)

| Paper | DOI | Verificación | Aporte crítico |
|---|---|---|---|
| Coppola 2016a SP426.5 | 10.1016/j.spl.2016.06.025 | ✅ Completo S17 | Kernel mean (D1), Tabla 1 dual-ROI (D2), Eq.16 SB |
| Wooster 2003 RSE | 10.1016/S0034-4257(03)00070-1 | ✅ S17 | k=18.9 MODIS Eq.6b |
| Campus 2022 Sensors | 10.3390/s22041713 | ✅ S17 | k=19.7 VIIRS 750m Eq.1 |
| Campus 2024 BV 86:25 | 10.1007/s00445-024-01721-z | ✅ S17 | k=18.0 VIIRS I4, bbox 50×50 km |
| Coppola 2024 Springer cap | 10.1007/978-3-031-86841-2_11 | ✅ S71 exhaustivo | α MODIS/VIIRS, K1=-0.8/-0.6, Stefan-Boltzmann Eq.16, background "adjacent" |
| Coppola 2019 Frontiers | 10.3389/feart.2019.00028 | ✅ S71 | Cloud no en algoritmo, FP rate 0-3%, supervisión visual mandatory |
| Coppola 2023 Frontiers | 10.3389/feart.2023.1240107 | ✅ S71 | OSF v1.0, post-processing temporal minima |
| Aveni 2024 RSE TIRVolcH | 10.1016/j.rse.2024.114388 | ✅ S17+S75 (9/9 const) | Stefan-Boltzmann puro Eq.5 (cierra D3) |
| Aveni 2025 GRL VRPTIR | 10.1029/2024GL113324 | ⚠️ Vault note verified S75 PR #150, PDF AGU paywalled | Eq.9 k_TIR=60.17 (refinamiento futuro, NO operacional) |
| Aguilera 2021 PP crater | 10.3389/feart.2021.722056 | ✅ S75 | Qvolc 7-59 MW Planchón-Peteroa, ground truth Aveni 2025 |
| Laiolo 2017 Santa Ana | varios | ⚠️ Caso aplicación específico, marginal | NO Turrialba (corregido S77 audit) |
| Massimetti tesis | (sin DOI) | ⚠️ Marginal MIR | 90% SWIR focus, desclasificada a ref informal |

### Grupo NO-MIROVA (separados S26 audit, lista canónica)

**INGV Catania (sistema RSDF/V-STAR/FastVRP/CNN)**: Del Negro, Corradino,
**Di Bella**, Torrisi, Cariello, Amato, Malaguti.
- Di Bella 2024 RS 16:2879: tabla 12σ noche/8σ día válida para RSDF, NO MIROVA.
  Citable como "trabajo relacionado", no como autoridad MIROVA.

**CNR-IMAA Potenza (sistema NHI)**: Marchese, Pergola, Genzano, Filizzola.
- Sin citas problemáticas en código operacional al cierre S80.

### Otros relevantes

- Dhage 2025 arxiv:2510.26816 (PR #137): validación independiente A37.
  VIIRS FIRMS undocumented filtering. Nosotros L1B directo NO afectados.
- Coppola 2026 Lascar SO2 (DOI 10.2139/ssrn.6481652): pending descarga manual,
  Cloudflare bloquea SSRN.

---

## 5. Aprendizajes A1–A52 (CLAUDE.md proyecto)

Lista resumida. Detalle completo en `CLAUDE.md` raíz proyecto.

- **A1-A9**: principios calibración empírica > teórica, diagnósticos paralelos
  antes de reprocesos, schema gaps, MIROVA arquitectura simple, valores
  oficiales como datos, verificar callers, schema "no calculado" vs "no
  persistido", verificar data fresca antes de fix, afiliación de paper.
- **A10-A30**: race conditions, encoding Windows, YAML safe_dump destruye
  comentarios, NRT vs Standard L1B auto-upgrade, frontend gotchas, etc.
- **A35-A41 (S73)**: Vault `ai_generated` necesita verificación verbatim,
  sec³(θ_z) amplificación, VIIRS vs MODIS L1B esquemas distintos, tag
  defensivo obligatorio, Claude responsable de merge cuando CI OK,
  discovery dirigido > orchestrators, Chrome MCP Perplexity Pro.
- **A42-A47 (S74-S77)**: latest_consolidado.csv hard copy, A43 YAML `on:`
  con comillas (Norway problem), worktrees dedicados per subagente, **A45
  tag defensivo + confirmación Nicolás antes pipeline NRT**, A46 schema
  consistency, **A47 NO paralelo sobre `data/mirova_equivalent/`**.
- **A48-A52 (S80)**: ver `docs/META_RULES_S80.md` para detalle.
  - A48: insert nuevo entre funciones no debe comer el `return` final
  - A49: cap PRs/sesión soft 12 (alerta), hard 20 (review pausa)
  - A50: "pre-existing fails" requiere verificación cross-source (origin/main)
  - A51: audit flags trimestral (cross-check `profile.py` ↔ `mirova_equivalent.yaml`)
  - A52: worktrees no-main pueden estar atrasados (`git fetch + git pull` siempre)

---

## 6. Hipótesis cerradas + abiertas (selección recientes)

**Confirmadas S69-S70 (ciclo audit S67-S70)**:
- H_S70_PATH_D_CIRRUS_FP: 22/32 FPs cirrus, t_bg<270K, amplificación 62× mediano
- H_S70_R2_RETROACTIVO_4VOLS: Lastarria 1.05×, Chaitén 1.26×, Villarrica 1.97×, PP 2.08×, PCC 0.575×
- H_S70_TIF_VRP_SUMABILITY: TIF NO sumable globalmente (11.5×); R2 con filtro <3km SÍ válido
- H_S69_R2_RETROACTIVO_LASTARRIA: 2026-05-14 pc.vrp_mw=0.147 vs MIROVA 0.14 (1.05×), drift centroide=0.752 km
- H_S69_MODIS_OUTLIERS_05_17: 3 vols outliers cirrus regional cálida (nube, no actividad)
- H_S68_TIF_ARCHIVE_NOT_STOPPED: scraper OK, directorio local desactualizado 9 días
- H_S68_ANTIPATRONES_AUDIT: exclude_zones off OK, min_vrp_mw_* son floors (0.6% afectados)
- H_S21_11: Tupungatito sub-pixel + sub-Kelvin (caso singular)

**Pending S78-S80**:
- H_F66_GATE_REDUCE_FP_LAKE: F66 con `kernel_size=3, dt_min=5K` reduce FPs lago Villarrica
  >50% sin perder TPs reales. **Tests sintéticos OK; reproc real pending Tasks 9-11.**
- H_F31_VRPTIR_AVENI_LOW_T: TIRVolcH detector + Eq.9 captura señal sub-MW PP crater lake
  donde MIR está vacío. Pending evento estacional + integración pipeline A2.

---

## 7. Estado operacional al cierre S80

- **Volcanes Tier A activos**: 11 (Lascar, Copahue, Chaitén, Isluga, Lastarria,
  Llaima, NdC, PlanchónPeteroa, PCC, Tupungatito, Villarrica).
- **Volcanes con `mirova_center` documentado**: 2/11 (PP offset 1.87 km N,
  Tupungatito offset 2.99 km SE). **Gap pending S80**: extraer los 9
  restantes desde KMZ oficiales.
- **NRT cron**: cada 2h, matrix 11 Tier A + 19 extras. 28-30/30 success típico.
  Últimas 7 corridas: success. Issue #1 (3 fallos consecutivos pre-#190) obsoleto.
- **Sync MIROVA**: cada 1h via `sync-mirova-csv.yml`.
- **Workflows activos main**: 5 (`nrt`, `nrt-monitor`, `nrt-retry`,
  `pages-deploy`, `sync-mirova-csv`).
- **Workflows archivados**: 35+ en `.github/workflows/_archive/` (PR #217).
- **Tests**: 510 passed + 6 pre-existing fail (regresión Task 1 resuelta S80
  → 516 passed en F66 branch).
- **Tamaño `data/`**: ~1.5 GB (35+ subdirs A/B aislados, inventario pending pruning).

---

## 8. Tags defensivos (rollback A45) — orden cronológico

```
pre-s27-baseline                    (MILESTONE S27)
pre-s73-data-cleanup                (S73 F2.8)
pre-s75-vrptir-a2-integration       (S75 F31 A2)
pre-s77-f46-vrp-tir-fix             (S77)
pre-s77-f47-store-cluster-rescue    (S77)
pre-s77-f47-distance-class-fix      (S77)
pre-s77-f50-vrp-mw-cap              (S77)
pre-s77-f51-fetch-probe-bypass      (S77)
pre-s77-f52a-villarrica-cluster-cap (S77)
pre-s77-f52b-single-pixel-sub-mw    (S77)
pre-s77-f55-nrt-auth-deep           (S77)
pre-s77-f55-profile-bypass          (S77)
pre-s78-f53-test1-hot               (S78)
pre-s78-f56-enable-exclude-zones    (S78)
pre-s78-f63-cluster-rank            (S78)
pre-s79-workflows-cleanup           (S79)
pre-s79-f66-hybrid → 9d4dd082       (S79)
pre-s80-consolidation               (S80, este worktree)
```

---

## 9. Documentos clave del proyecto (qué leer cuándo)

### Lecturas obligatorias al iniciar sesión nueva

1. **Este documento** (`docs/SESSION_INDEX_CONSOLIDATED_S80.md`) — primer comando
2. `docs/META_RULES_S80.md` — reglas preventivas pérdida contexto
3. `tasks/BLOQUE_ARRANQUE_S<latest>.md` — estado al cierre sesión anterior
4. `CLAUDE.md` raíz proyecto — aprendizajes A1-A52 vigentes

### Lecturas situacionales

- **Entrando a F66 implementación**: `docs/superpowers/specs/2026-05-26-f66-hybrid-bg-kernel-consistency-gate-design.md` + `docs/superpowers/plans/2026-05-26-f66-hybrid-bg-kernel-consistency-gate.md` + `docs/F66_BG_KERNEL_LOCAL_DEEP_S78.md`
- **Trabajando con drifts**: `docs/DRIFTS_S17.md`, `docs/MIROVA_DIVERGENCES.md`
- **Auditoría reproducibilidad**: `docs/AUDITORIA_PRE_REPROC_S77_ADDENDUM_V2.md`
- **F31 VRPTIR Aveni**: `docs/F31_VRPTIR_AVENI_PLAN.md` (si existe en main)
- **Hipótesis log**: `docs/HYPOTHESIS_LOG.md`

### Investigación bibliográfica

- Guía maestra cross-proyecto: `../GUIA_MAESTRA_INVESTIGACION.md`
- Workflow específico VRP Chile: `docs/RESEARCH_WORKFLOW.md`

---

## 10. Backlog real pendientes (post-cleanup S80)

Deudas verificadas que NO son planes ya implementados:

1. **F66 Tasks 7–15** (continuar implementación)
2. **F31 VRPTIR A2** integración pipeline (esperando evento baja-T enero-marzo)
3. **9/11 `mirova_center`** pending extracción desde KMZ (gap visual sesgo 1-5 km)
4. **`backlog_s32_schema_gap_anomaly_pixels.md`** — schema gap anomaly_pixels vs primary_cluster.vrp_mw
5. **D7** local ROI threshold p95 ausente VIIRS 375m (diferido, A/B vs OSF)
6. **Coppola 2026 Lascar SO2** PDF (DOI 10.2139/ssrn.6481652) — descarga manual
7. **Aveni 2025 GRL** PDF AGU paywalled — buscar ResearchGate/EarthArXiv
8. **F2.8.f reproc histórico** fósil PP 2026-03-18 (NRT corre OK, nice-to-have)
9. **TROPOMI SO2**, **F60 VSROI polygonal**, **paper VRP Chile P5** (backlog largo plazo)

---

**Mantenimiento de este documento**: actualizar al cierre de cada sesión con
hito nuevo + tag defensivo + flags adoptados. Si no cabe en una pantalla
después de S100, particionar por fases en docs separados conservando esta
estructura.
