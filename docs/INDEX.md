# ÍNDICE MAESTRO DE DOCS — VRP Chile
> Creado S105 (AUDIT_S105 acción P1). Clasifica SIN mover (limpieza física pospuesta).
> Regla: al crear un doc nuevo, agregarlo acá. Al cerrar un frente, mover su entrada a HISTÓRICO.
>
> **Puesto al día S123 (2026-08-09)** tras 18 sesiones sin mantención: este índice declaraba
> AUDIT_S105 como "última auditoría vigente" mientras existían 6 auditorías integrales
> posteriores, y ~25 docs S106-S123 no figuraban. Si vas a agregar un doc, agregá también
> su fila acá **en la misma sesión** — la regla de arriba es vieja, lo que falló es cumplirla.
>
> **S133**: volvió a fallar. Los seis docs de `s133/` y los dos de `s132/` se agregaron sólo
> cuando Nicolás preguntó si se había cruzado contra los propios documentos del proyecto.
> Escribir el doc y no indexarlo es la forma habitual del olvido: el doc existe, pero para
> una sesión fría no existe.

## CANÓNICOS (fuente de verdad — leer estos primero)

| Doc | Qué es | Desde |
|---|---|---|
| MISSION.md | Misión vinculante: clon literal MIROVA, 3 preguntas | S22 |
| MIROVA_DIVERGENCES.md | Catálogo vivo de divergencias vs MIROVA | S71+ |
| AUDIT_S131.md | Resultados + dashboard + utilidad OVDAS; 6 ejes (magnitud/ATBD, dashboard, T9, pendientes, TIF por pasada, otro sensor) | S131 |
| AUDIT_S128.md | Evidencia exógena: ángulo de vista, grilla desde KMZ, D2 medida, GAP #A reabierto | S128 |
| AUDIT_S127.md | Eje «declarado ≠ efectivo» (T9): 4 afirmaciones falsas, 3 guards | S127 |
| AUDIT_S125_PROFUNDA.md | Sub-reporte aislado en VIIRS375; rebaja de A82 | S125 |
| AUDIT_S124.md | Banda de paridad, filtro solar, D15/D16/D17 | S124 |
| PROTOCOLO_AUDITORIA_PROFUNDA.md | Las 9 técnicas validadas (T9 = declarado vs efectivo) | S124+ |
| AUDIT_S123.md | Auditoría integral 6 ejes | S123 |
| AUDIT_S122.md · AUDIT_S121_MEJORA_INTEGRAL.md | Anteriores (deuda docs; multi-modelo) | S121-S122 |

> ⚠️ **No hardcodear cuál es «la vigente» acá.** Este índice marcó S123 como VIGENTE
> durante cuatro sesiones mientras existían S124, S125 y S127, y ni S124 ni S125 estaban
> listadas. Es el mismo defecto que la propia AUDIT_S127 audita. Para saber cuál es la
> última: `ls docs/AUDIT_S*.md | sort -V | tail -1` (ojo, `sort -V`: el orden alfabético
> pone S99 después de S122).

| AUDIT_S119.md · AUDIT_S116.md · AUDIT_S105.md | Auditorías integrales anteriores (históricas) | S105-S119 |
| AUDIT_S86.md | Marco FPs: 95% son realidad física (A54) — matizado por A69/A82 | S86 |
| META_RULES_S80.md | Reglas meta M1-M9 + A56-A60 | S80 |
| SESSION_INDEX_CONSOLIDATED_S80.md | Ancla consolidada sesiones S1-S80 | S80 |
| SESSION_CLOSE_CHECKLIST.md | Checklist obligatorio de cierre de sesión | S20 |
| HYPOTHESIS_LOG.md | Log vivo de hipótesis confirmadas/refutadas | S17 |
| DATA_SOURCES.md | Inventario vivo de fuentes de datos | S17 |
| PAPER_VRP_CHILE_DRAFT_S72.md | Draft del paper VRP Chile | S72 |
| R2_GATES_BY_REGIME.md | Gates R2 por régimen térmico (operacional) | S70 |
| PROCESS_RULES_S33.md | Reglas de proceso R1-R8 (adopciones) | S33 |
| RESEARCH_WORKFLOW.md | Workflow bibliográfico del proyecto | S36+ |
| PAPERS_AUDIT.md | Audit vivo papers autoritativos vs código | S17 |
| MIROVA_DETAILED_CITATIONS.md | Citas detalladas MIROVA (referencia biblio) | S26+ |
| MIROVA_IMG_READING_GUIDE.md | Cómo leer imágenes/TIF de mirovaweb | S70+ |
| BEYOND_MIROVA_EXTENSIONS.md | Catálogo vivo extensiones beyond-MIROVA (EXT-*) | S99 |
| AUDIT_S103_OVERDETECTION_PCC_VILLARRICA.md | Diagnóstico vivo sobre-detección sistémica (A68) | S103 |
| AUDIT_S103_PRE_VIIRS.md | Auditoría profunda pre-flip nadir VIIRS | S103 |
| AUDIT_S104_SYSTEMIC_DIVERGENCE.md | Diagnóstico vivo divergencia sistémica | S104 |
| AUDIT_S104_VIIRS_POSITION_OFFSET.md | Diagnóstico vivo sesgo topográfico MIR (A69) | S104 |
| S103_S2_VIIRS750_PATHD_PREP.md | Prep frente path D (§2, abierto) | S103 |
| AUDIT_S108_AB_MODIS_VEREDICTO.md | Veredicto vivo: fix §2 magnitud MODIS (fondo-local) REFUTADO | S108 |
| AUDIT_S108_ESTADO.md | Estado global vivo vs MIROVA por sensor (gap MODIS 10.8%, ratio VIIRS 0.5×) | S108 |
| AUDIT_S108_DASHBOARD.md | Auditoría dashboard/frontend (0 bugs, display dist=cráter) | S108 |
| LOCAL_NRT_SETUP.md | Guía setup NRT local (operacional) | — |
| EARTHDATA_TOKEN_SETUP.md | Guía setup credenciales Earthdata | — |
| superpowers/specs/2026-06-10-test1-local-bg-nti-design.md | Design frente ABIERTO fondo-local NTI | S105 |
| superpowers/specs/2026-06-09-test1-nti-covalidation-design.md | Design frente ABIERTO Test1-NTI co-validación | S104 |
| superpowers/specs/2026-06-05-frente-modis-campo-difuso-design.md | Design frente ABIERTO MODIS campo difuso | S101 |

### Agregados S123 — docs S106-S123 que faltaban en el índice

**Veredictos y cierres (leer antes de reabrir cualquier frente — anti-A8):**

| Doc | Qué cierra / concluye | Sesión |
|---|---|---|
| AUDIT_S114_PARITY_BY_SENSOR.md | far→summit MODIS **irreducible** (A82); detección MODIS fiel a Coppola file:line | S114 |
| AUDIT_S116_FOLLOWUP.md | No existe discriminante físico universal cat-b vs artefacto (A83); refina A80 | S116 |
| AUDIT_S116_C2_GATES.md · AUDIT_S118_C2_GATES_AB.md | Gates intra-radio: investigación → A/B real → **flip OFF** (A85) | S116-S118 |
| AUDIT_S121_D12_AB.md | D12 ancla honesta MODIS: **NO ADOPTAR** (cura Láscar, destapa path-D) | S121 |
| AUDIT_S122_C2_PASO0.md | C2 peak-of-kernel **no viable** (pico solapa nevados); D12 cerrable | S122 |
| AUDIT_S109_MODIS_FOCAL_VEREDICTO.md · AUDIT_S108_AB_MODIS_VEREDICTO.md | Magnitud focal MODIS adoptada / fondo-local refutado | S108-S109 |
| S103_VIIRS_NADIR_PROMOTE_RESULTS.md · S102_NADIR_PROMOTE_RESULTS.md | nadir-fijo adoptado y promovido (A66/A67) | S102-S103 |
| S113_A46_COHERENCE_GUARD.md | Guard de coherencia A46 (summit→far) live | S113 |
| S112_TEST1_LOWMAG_AB_RESULTS.md | Magnitud "Muy Bajo" VIIRS375, anillo [1.5,3] (A79) | S112 |

**Diagnósticos y planes vivos:**

| Doc | Qué es | Sesión |
|---|---|---|
| PLAN_EXPERIMENTAL_BEYOND_MIROVA_S122.md | Plan del modo experimental (M1 zonas, M2 AVTOD, backfill P4) | S122 |
| M2_AVTOD_INTEGRATION_S122.md | AVTOD: premisa refutada (no publica VRP en watts) | S122 |
| S121_GIT_FILTER_REPO_DESIGN.md | Diseño poda de historia git (autorizado, **sin ejecutar**) | S121 |
| S122_ANGLE_BIAS_FINDING.md | Geometría de observación per-record | S122 |
| BACKFILL_PLAN_S120.md | Plan de backfill (usado en la recuperación del 04-ago) | S120 |
| AUDIT_S110_NDC_PATH_DIAGNOSTIC.md · AUDIT_S111_TEST1_LOWMAG_FN.md | Diagnósticos NdC / FN régimen bajo | S110-S111 |
| AUDIT_S112_DASHBOARD_MIROVA.md · S101_DASHBOARD_AUDIT.md · S100_DASHBOARD_AUDIT.md | Auditorías de dashboard | S100-S112 |
| AUDIT_S106.md · AUDIT_S109_VIIRS_FRENTES.md · S101_SENSOR_PERFORMANCE.md | Estado por sensor / frentes VIIRS | S106-S109 |
| EARTHDATA_TOKEN_SETUP.md | Setup de credenciales NASA — **relevante tras el incidente 20-jul** | — |
| s133/AB_B22_VEREDICTO.md | A/B de B22: NO ADOPTAR (C1 y C3 fallan); el fondo cae 1,2 K, no 0,004 | S133 |
| **s133/AUDITORIA_DEL_INCIDENTE.md** | **La alerta de 4,75 MW que no vimos y los 5 defectos que la escondieron** | **S133** |
| s133/AUDITORIA_NRT_MODIS.md | El NRT de MODIS pedía una colección inexistente (`MYD021KM_NRT` v61) | S133 |
| s133/CADENCIA_DEL_CRON.md | La entrega de eventos programados cayó 51 %; sin pérdida de datos | S133 |
| s133/SUSTRATO_AREA_GEOLOCALIZADA.md | El A/B del área no tenía sustrato de código | S133 |
| s133/B22_EVIDENCIA.md | B22 banda primaria: evidencia + criterios C1-C4 pre-registrados | S133 |
| s133/C2_NORMALIZADO_INNER_RADIUS.md | C2 de `distance_class` era tautológico; C2' propuesto | S133 |
| s132/AB_AREA_GEOLOCALIZADA.md | Criterio pre-registrado del A/B del área (**no se toca**) | S132 |
| s132/AB_DISTANCE_CLASS_MODIS.md | A/B corrido: NO ADOPTAR (falló C2, mal calibrado — A91) | S132 |
| s131/REMUESTREO_LEY_DE_AREA.md | El área explica el gradiente cenital entero; ATBD 4,38× | S131 |

## HISTÓRICO-CERRADO (referencia, NO fuente de verdad actual)

### Auditorías y sesiones superseded
| Doc | Qué fue | Cerrado en |
|---|---|---|
| SESSION_INDEX.md | Índice sesiones viejo | Superseded S80 |
| SESSION_CLOSE_S77.md | Cierre puntual S77 | S77 |
| SESSION_CLOSE_S78.md | Cierre puntual S78 | S78 |
| AUDITORIA_PRE_REPROC_S77.md | Auditoría pre-reproc | S77 |
| AUDITORIA_PRE_REPROC_S77_ADDENDUM_V2.md | Addendum v2 (corrige regex subagente A48) | S77 |
| AUDITORIA_PASADA_POR_PASADA_S78.md | Auditoría pasada-por-pasada | S78 |
| AUDIT_INTEGRAL_S81.md | Auditoría integral S81 | S81 |
| AUDIT_S93_artefactos_sobreestimacion.md | Audit artefactos sobre-estimación | S93 |
| AUDIT_S94_per_sensor_metrics.md | Métricas per-sensor, loader corregido | S94 |
| AUDIT_S95_gaps_sistemicos.md | Auditoría 5 ejes gaps sistémicos | S95 |
| REAUDITORIA_S52.md | Re-auditoría S52 | S52 |
| DRIFTS_S17.md | Drifts D1-D3 código vs papers (resueltos) | S17 |
| MIROVA_DIVERGENCES_CATALOG_S71.md | Catálogo divergencias (superseded por MIROVA_DIVERGENCES.md) | S71 |
| F_PRECISION_GAP_INVESTIGATION_S86.md | Investigación gap precisión (insumo AUDIT_S86) | S86 |

### Resultados de sesiones cerradas (S97-S103)
| Doc | Qué fue | Cerrado en |
|---|---|---|
| S97_DEEP_AUDIT.md | Deep audit S97 | S97 |
| S97_TUPUNGATITO_ROOTCAUSE.md | Root cause ancla Tupungatito (resuelto S98) | S98 |
| S97_A46_A07_DIAGNOSIS.md | Diagnóstico A46/A07 anomaly_pixels | S97 |
| S97_STAGING_CLEANUP_INVENTORY.md | Inventario cleanup staging | S97 |
| S98_ANCHOR_FIX_RESULTS.md | Resultados fix ancla (promovido) | S98 |
| S98_PROMOTION_PROCEDURE.md | Procedimiento promoción S98 | S98 |
| S99_TEST1_AB_RESULTS.md | A/B 4 candidatos magnitud Test1 | S99 |
| S99_DORMANT_FINDINGS_AUDIT.md | Auditoría hallazgos dormidos | S99 |
| S99_AUDIT_SYNTHESIS.md | Síntesis auditoría S99 | S99 |
| S100_TEST1_FULL_AB.md | A/B paired ctxpeak (adoptado) | S100 |
| S100_DASHBOARD_AUDIT.md | Auditoría coherencia dashboard | S100 |
| S101_DASHBOARD_AUDIT.md | Auditoría dashboard S101 | S101 |
| S101_SENSOR_PERFORMANCE.md | Performance por sensor | S101 |
| S102_NADIR_PROMOTE_RESULTS.md | Promoción nadir-fijo MODIS | S102 |
| S103_VIIRS_NADIR_PROMOTE_RESULTS.md | Promoción nadir-fijo VIIRS | S103 |
| S103_WORKFLOWS_CLEANUP_INVENTORY.md | Inventario cleanup workflows | S103 |

### Frentes F* ejecutados/cerrados
| Doc | Qué fue | Cerrado en |
|---|---|---|
| A33_FALSA_ALARMA_F25b.md | Falsa alarma F25b | — |
| F26_VERDICT_CONSOLIDATED_S72.md | Veredicto F26 consolidado | S72 |
| F28_SATURATION_INVESTIGATION.md | Investigación saturación MODIS/VIIRS | S73-74 |
| F28_HYPOTHESIS_LOG.md | Hipótesis F28 | S73-74 |
| F28_LIT_SEARCH_S73.md | Búsqueda literatura F28 | S73 |
| F28_DATA_ARCHIVE_INVENTORY.md | Inventario archive F28 | S73 |
| F30_FRONTEND_BUGS_PLAN_S74.md | Plan bugs frontend (ejecutado) | S74 |
| F31_AVENI_VRPTIR_PLAN_S74.md | Plan VRP-TIR Aveni (ejecutado S75) | S75 |
| F31_AVENI_2024_TIRVOLCH_VERIFY.md | Verificación Aveni 2024 TIRVolcH | S74 |
| F31_AVENI_GRL_2025_EXTRACT.md | Extracto Aveni GRL 2025 | S74 |
| F31_AGUILERA_2021_PETEROA.md | Extracto Aguilera 2021 Peteroa | S74 |
| F46_VRP_TIR_BUG_S76.md | Bug VRP-TIR | S76 |
| F46_AB_TEST_PLAN.md | Plan A/B F46 | S76 |
| F46_LASTARRIA_IMPACT_S77.md | Impacto F46 Lastarria | S77 |
| F46_VRP_TIR_GATE_S81.md | Gate VRP-TIR | S81 |
| F47_NDC_RECALL_S76.md | Bug recall NdC (cluster_rescue, A46) | S77 |
| F48_LLAIMA_COPAHUE_REFS_GAP.md | Gap refs Llaima/Copahue | S76+ |
| F49_SCRAPER_MIROVA_DOWN_S77.md | Scraper MIROVA caído | S77 |
| F50_MODIS_07_25_AUDIT_S77.md | Audit MODIS 07/25 | S77 |
| F51_NRT_DOWN_INVESTIGATION_S77.md | Investigación NRT caído | S77 |
| F52_TUPUNGATITO_PCC_AUDIT_S77.md | Audit Tupungatito/PCC | S77 |
| F52_VILLARRICA_OVER_ESTIMATION_S77.md | Sobre-estimación Villarrica | S77 |
| F5_CALIBRATION_S95.md | Calibración F5' núcleo (adoptada) | S95 |
| F5_DISPLAY_S96.md | F5' display toggle (deployado) | S96 |
| F60_VSROI_BRAINSTORM_S78.md | Brainstorm VSROI | S78 |
| F61_NTI_RIGOR_BRAINSTORM_S78.md | Brainstorm rigor NTI | S78 |
| F61_F63_F57_INTEGRATED_PLAN_S78.md | Plan integrado F61/F63/F57 | S78 |
| F62_TEST1_K_SIGMA_BRAINSTORM_S78.md | Brainstorm k-sigma Test1 | S78 |
| F63_CLUSTER_CONNECTIVITY_BRAINSTORM_S78.md | Brainstorm conectividad cluster | S78 |
| F64_NTI_METHOD_BRAINSTORM_S78.md | Brainstorm método NTI | S78 |
| F65_APPROACHES_ALTERNATIVOS_S78.md | Approaches alternativos | S78 |
| F66_BG_KERNEL_LOCAL_DEEP_S78.md | Deep dive kernel-bg local | S78-80 |
| F_S81_A_ADOPTION_S84.md | Adopción F_S81_A | S84 |
| F_S81_A_FASE1B_SANITY_P95.md | Sanity P95 fase 1b | S84 |
| F_S81_B_PRIME_ADOPTION_S85.md | Adopción B-prime | S85 |
| F_S81_B_PRIME_SECOND_PASS_GATE.md | Gate second-pass (redundante per A55) | S85-86 |
| F_S81_B_SANITY_VIIRS.md | Sanity VIIRS | S81+ |
| F_S81_C_1_ZONES_CATALOG.md | Catálogo zonas | S81+ |
| F_S81_C_R3_NATURE_AUDIT.md | Audit naturaleza R3 | S81+ |
| MIROVA_INTRA_RADIO_GATE_S81.md | Gate intra-radio (anti-patrón per A55) | S86 |
| PLAN_S53_VRPTIR_AVENI2025.md | Plan VRP-TIR Aveni (ejecutado) | S53 |

### Hallazgos, inventarios y snapshots
| Doc | Qué fue | Cerrado en |
|---|---|---|
| AVTOD_CROSS_VALIDATION_S72.md | Cross-validación AVTOD | S72 |
| BASELINE_LITERATURA_TIER_A_S77.md | Baseline literatura Tier A | S77 |
| BRANCHES_CLEANUP_S80.md | Cleanup de branches | S80 |
| DATA_SUBDIRS_INVENTORY_S80.md | Inventario data/_*/ subdirs | S80 |
| EXCELS_INVENTORY_S57.md | Inventario excels | S57 |
| MIROVA_IMAGES_INVENTORY.md | Inventario imágenes MIROVA (snapshot) | — |
| MIROVA_V1_PARITY_PROPOSAL_S77.md | Propuesta paridad Mirova-v1 | S77 |
| PAPERS_MIROVA_SYNTHESIS_S71.md | Síntesis papers MIROVA (snapshot S71) | S71 |
| REFS_TIER1_S72.md | Refs tier 1 | S72 |
| TUPUNGATITO_FINDING_S72.md | Hallazgo Tupungatito | S72 |
| papers_mirova_processed_S72_backlog.md | Backlog papers procesados | S72 |

### superpowers/plans/ (todos ejecutados)
| Doc | Qué fue | Cerrado en |
|---|---|---|
| 2026-04-25-s21-d6-foundation.md | Plan fundación D6 | S21 |
| 2026-04-26-s23-audit-followup.md | Follow-up auditoría | S23 |
| 2026-04-27-s26-dual-roi-bt-path.md | Dual-ROI BT path | S26 |
| 2026-04-28-mirova-literal-puro.md | Plan MIROVA literal puro | S27+ |
| 2026-05-15-s46-coppola-literal-implementation.md | Implementación Coppola literal | S46 |
| 2026-05-18-s61-local-kernel-bg-adoption.md | Adopción kernel-bg local | S61 |
| 2026-05-19-s62-pcc-lastarria-tupungatito.md | Plan PCC/Lastarria/Tupungatito | S62 |
| 2026-05-23-f28-saturation-guard.md | Guard saturación F28 | S73-74 |

### superpowers/specs/ (frentes cerrados)
| Doc | Qué fue | Cerrado en |
|---|---|---|
| 2026-05-06-vrp-integrated-eq1.md | VRP integrado Eq1 | S33 |
| 2026-05-10-d8-cluster-selection.md | D8 selección cluster | S35+ |
| 2026-05-10-h8-eruption-filter-pixel-level.md | H8 filtro pixel-level | S35 |
| 2026-05-11-plan-integrado-s36.md | Plan integrado S36 | S36 |
| 2026-05-12-d8-combo-fix.md | D8 combo fix | S36+ |
| 2026-05-12-paths-retirement-analysis.md | Análisis retiro de paths | S36+ |
| 2026-05-13-frontend-audit-s38.md | Audit frontend | S38 |
| 2026-05-15-s46-coppola-literal-design.md | Design Coppola literal | S46 |
| 2026-05-17-vrp-three-regimes-design.md | Design 3 regímenes VRP | S57+ |
| 2026-05-29-s88-pc-classification-design.md | Design clasificación pc | S88 |
| 2026-05-30-clon-mirova-por-sensor-design.md | Design clon por sensor | S90 |
| 2026-05-30-display-cirrus-artifact-suppression-design.md | Supresión display cirrus (adoptada; candidata migrar a algoritmo A72) | S90 |
| 2026-05-30-display-diffuse-field-artifact-design.md | Display campo difuso (superseded por frente MODIS) | S90+ |
| 2026-05-31-f5-coldfield-magnitude-design.md | Design F5' campo frío | S95 |
| 2026-06-02-detection-anchor-crater-design.md | Design ancla al cráter (promovido) | S98 |
| 2026-06-03-test1-magnitude-compactness-design.md | Design magnitud/compacidad Test1 (ctxpeak adoptado) | S100 |
| 2026-06-06-viirs-nadir-ctxpeak-interaction-design.md | Design A/B 3 brazos nadir/ctxpeak | S103 |

## REVISAR (clasificación pendiente)

- F52B_SINGLE_PIXEL_MODE.md — estado del modo single-pixel no confirmado
- F_S81_B_BACKLOG_PATH_ABC_GATES.md — "backlog" sugiere items quizá vivos
- R3_RESIDUAL_BY_PATH.md — análisis residual por path; ¿método vivo o snapshot?
- VILLARRICA_DETECTION_HISTORY.md — historia detecciones; ¿referencia viva?
- VILLARRICA_VIIRS375_OVERDETECTION.md — ¿resuelto o frente latente (A68)?
- superpowers/plans/2026-05-30-daytime-modis-detection.md — daytime MODIS flag-OFF, A/B pendiente
- superpowers/specs/2026-05-30-daytime-modis-detection-design.md — ídem, frente pausado no cerrado
