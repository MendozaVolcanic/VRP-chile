# Catálogo sistemático de divergencias VRP Chile vs MIROVA — S71 (2026-05-21)

> Trigger: Nicolás señaló que la revisión exhaustiva debe iluminar **TODOS los posibles problemas del pipeline**, no solo cloud handling. Este doc consolida en una matriz: drifts conocidos D1-D9, hipótesis HT1.5-NEW, hipótesis históricas H_S*, y candidatos nuevos derivados de la revisión bibliográfica S71. Cada uno con status + autoridad bibliográfica + costo de verificación + prioridad.
>
> **Metodología**: probar cada candidato con A/B aislado o audit barato → descartar los que no impactan → adoptar los que sí + documentar el "por qué" con cita literal del paper.

## 1. Drifts resueltos / adoptados (cerrados)

| ID | Tema | Adopción | Fecha | Source |
|---|---|---|---|---|
| D3 | TIR Stefan-Boltzmann puro (no Eq.9 Aveni) | Adoptado | S17 | Aveni 2024 RSE + Coppola 2024 Eq.16 |
| D4 | Cobertura events recall stratified — `local_kernel_bg` per-vol opt-in | Adoptado per-vol S61 (Villarrica, PP, Lastarria, Chaiten, PCC) | S60-S62 | Campus 2024, Coppola 2024 §1129 |
| D6 | TIF MIROVA no es VRP per-pixel sumable | Documentado, no actionable | S70-0 T3 | TIF audit empírico |
| D7 | R2 retroactivo régimen-dependiente | Documentado, no universal | S70-1 | Audit 5/5 Tier A |
| D8 | Background ring contaminado | RESUELTO con kernel local 3×3 | S60-S62 | Coppola 2024 §1051+1129 |
| D9 | Path D cirrus FPs amplifica magnitud | PARCIALMENTE RESUELTO — cap 5MW @ t_bg<270K | S71 (PR #112) | SP 426.5 §675-696 (cita literal "<5 MW") |

## 2. Drifts abiertos / candidatos no probados — MATRIZ PRIORIZADA

### Codificación

- **Impacto** (drift size esperado): 🔴 alto (>3× ratio improvement), 🟡 medio (1.5-3×), 🟢 bajo (<1.5×)
- **Costo verificación**: ⚡ rápido (<1h audit), ⏱ medio (1-4h), 🔥 caro (workflow A/B reproc 11 vols 90d)
- **Confianza bibliográfica**: ⭐⭐⭐ cita directa con número de línea, ⭐⭐ derivable, ⭐ hipotético

### Tabla principal

| ID | Hipótesis | Source | Impacto | Costo | Confianza | Status |
|---|---|---|---|---|---|---|
| **HT1.5-NEW-4** | Coord `vent_lat/lon` apunta a lago/dome geométrico, señal MIROVA viene de fumaroles rim adyacente. **Drift geométrico, no algorítmico** | Laiolo 2017 §336-338 (Santa Ana lake silent, fumaroles emit) | 🔴 (Villarrica/PCC/Chaiten potencial fix similar a S62 Tupungatito mirova_center) | ⚡ ~30min audit | ⭐⭐⭐ | **Abierto — top P1** |
| **HT1.5-NEW-1** | MIROVA agrega Σ scene-wide dentro de 5km radius. Nosotros `primary_cluster`. | SP 426.5 Eq.8 + Coppola 2024 Eq.13 + Massimetti 2024 §561-562 (cita literal "5 km") | 🔴 (validada en lit, drift arquitectural) | 🔥 workflow A/B + refactor | ⭐⭐⭐ | **Abierto — P2 (post HT1.5-NEW-4)** |
| **HT1.5-NEW-2** | L_bk debe excluir **TODOS** los hot pixels del cluster (no solo central) | SP 426.5 §357-359 ("around the active cluster"), Campus 2024 §119 | 🟡 | ⚡ verificación code | ⭐⭐ | **Abierto — P3** |
| **HT1.5-NEW-3** | Method-2 MIROVA: descartar weekly local minima en post-processing | Coppola 2023 §530-540 ("local VRP minima are removed") | 🟡 (presentation layer, no NRT core) | ⏱ implementación dashboard | ⭐⭐⭐ | **Abierto — P4 (post-core fixes)** |
| **NEW-5** | 5 km geofencing MIR vs nuestro 25 km uniforme | Massimetti 2024 §561-562 (Stromboli 5 km) | 🟡 (para Andes box 50×50 km podría ser distinto) | ⚡ audit empírico OSF | ⭐⭐ (Stromboli context puede no aplicar Andes) | Abierto — P5 |
| **NEW-6** | Reproducción benchmark Villarrica 24-Jun-2009 Fig. A6 SP 426.5 | SP 426.5 Fig. A6 (caso paper) | 🟢 (validación) | ⚡ correr 1 noche | ⭐⭐⭐ | Abierto — útil P6 |
| **NEW-7** | Pixels Test 1 (NTI>K1) descartados de Tests 2/3 | SP 426.5 §298-300 ("subsequently discarded for further steps") | 🟢 | ⚡ verificar code | ⭐⭐⭐ | Abierto — P7 |
| **NEW-8** | Pixels unsuitable: edge + dNTI<-0.1 + dETI<-0.1 filtrados | SP 426.5 §267-273 | 🟢 | ⚡ verificar code | ⭐⭐⭐ | Abierto — P7 |
| **NEW-9** | C2 trade-off explorado (5 vs 10 vs 15) — sub-camino refutado para Muy Bajo | SP 426.5 §403-414 + Laiolo 2017 (refuta para Muy Bajo) | 🟢 | 🔥 workflow A/B | ⭐⭐ | **Refutado para Muy Bajo, mantener Tabla 1 default** |
| **NEW-10** | Two-component model Eq.14-16 Coppola 2024 | Coppola 2024 §1132-1141 | 🟢 (no usado por MIROVA NRT) | — | ⭐⭐⭐ | **Descartado — MIROVA NRT no usa, requiere T_hot assumption** |
| H_S54 | Cluster sum NN pixels vs MIROVA single-cluster (factor 42) | Empírico Lastarria | 🔴 (relacionado HT1.5-NEW-1) | 🔥 | ⭐⭐ | Cubierto por HT1.5-NEW-1 |
| H_S55 | 4 estrategias agregación offline negativo | Audit S55 | — | — | Refutado |
| H_S56 | Background percentil bajo (p01-p05) ring resuelve gap MW | Empírico S56 | 🟡 | ⏱ | ⭐ (no en papers) | **Refutado por kernel-bg S58 (papers > percentil empírico)** |
| H_S49 | Test 1 integrated-ROI VRP missing | SP 426.5 §test1 + Wooster pixel-level | 🟡 | ⏱ | ⭐⭐ | Cosmético, no afecta recall |
| H_S24 | Aveni 2025 Eq.9 NO resuelve Villarrica | Empirical S24 | — | — | Refutado |
| H_S23 | MIROVA reporta clusters, nosotros pixels (factor 42) | Empirical S23 | 🔴 | 🔥 | ⭐⭐ | Cubierto HT1.5-NEW-1 |

## 3. Plan ejecutivo "probar todo, descartar, registrar"

### Fase 1 — Audits baratos (sin reproc, ⚡ <1h cada uno)

| Orden | Tarea | Decisión derivada |
|---|---|---|
| F1.1 | **HT1.5-NEW-4 — audit coords vent vs centroides MIROVA NRT** sobre 5 vols Tier A Muy Bajo (Villarrica, PCC, Chaiten, PP, Tupungatito). Cruce: para cada record MIROVA NRT en CONS+OCR, ¿está el centroide a >0.5 km del vent_lat/lon que tenemos? Si sí + sistemático → drift geométrico confirmado | Si confirmado → actualizar coords (S62 Tupungatito pattern) → reproc → AUDIT post-fix |
| F1.2 | **NEW-7+NEW-8 — verificar code**: ¿`first_pass_tests_2_and_3` descarta Test 1 pixels + pixels unsuitable? Code review | Si gap → fix bajo cost |
| F1.3 | **HT1.5-NEW-2 — verificar code**: ¿`local_kernel_bg` excluye TODOS hot pixels del cluster surrounding? | Si gap → fix bajo cost |
| F1.4 | **NEW-5 — audit empírico**: en OSF v2.5, ¿qué fracción de records están a >5 km del vent? Si <5% → 5 km MIROVA aplica también Andes. Si >20% → MIROVA usa otra geofencing en Andes | Decisión: geofencing 5 km o 25 km |
| F1.5 | **NEW-6 — reproducir Villarrica 24-Jun-2009**: ¿podemos generar la NTI/NTIbk/dNTI/dETI maps que SP 426.5 Fig. A6 muestra? | Benchmark de fidelidad algorítmica |

### Fase 2 — Si Fase 1 no resuelve (workflows A/B 🔥 caros)

| Orden | Tarea | Decisión derivada |
|---|---|---|
| F2.1 | **HT1.5-NEW-1 — implementar scene-wide aggregation** (sum ALL alerted pixels dentro de 5/25 km) en profile aislado `mirova_equivalent_scenewide_v1` + workflow A/B 11 Tier A 90d | Comparar contra `mirova_equivalent` actual (con cap S71). Validar pre-condición: cap S71 sigue activo durante A/B |
| F2.2 | **HT1.5-NEW-3 — Method-2 weekly minima** como post-processing dashboard | Implementable sin tocar pipeline. UX decision |

### Fase 3 — Cleanup y consolidación

- Documentar todos los resultados (pasen o no) en `docs/MIROVA_DIVERGENCES.md`
- Si NEW-5 sale "Andes usa otra geofencing" → contactar Coppola directamente (correo) para confirmar
- Reglas de decisión documentadas

## 4. Criterio de descarte (cuándo abandonar un drift)

Cada drift se descarta si:
1. **No tiene cita bibliográfica directa** (⭐ hipotético) AND audit empírico negativo
2. **Cita bibliográfica refuta** (e.g., Laiolo 2017 refuta C2 distinto para Muy Bajo régimen)
3. **A/B test muestra delta <5% en ratio mediano** sobre Tier A
4. **Implementación rompe recall validado en otro vol** (e.g., Opción B colapsa NdC)

Cada drift se adopta si:
1. Cita bibliográfica directa ⭐⭐⭐
2. Audit empírico positivo (ratio→1.0±0.5)
3. R1 (test sintético) + R2 (pixel-level) + R3 (audit independiente) passing (regla S33)
4. Sin regresión en recall ningún vol Tier A

## 5. Backlog refs a procesar (bibliografía pendiente)

- ⚠️ **Campus 2022 transición VIIRS** — leer detalle del L_bk method si HT1.5-NEW-2 requiere
- ⚠️ **Massimetti THESIS** — complementario, baja prioridad
- ⚠️ **Coppola 2022 Sabancaya + EPSL** (Cigolini últimos papers) — baja prioridad

## 6. Plan de sesión S72 (recomendado)

1. **Fase 1 completa** (F1.1 → F1.5) en una sesión con subagentes paralelos. Output: tabla de "qué pasó / qué se descartó / qué se confirmó".
2. **Decisión informada** de qué Fase 2 worth correr (workflows A/B caros).
3. **Si HT1.5-NEW-4 resuelve drift remanente** sin tocar algoritmo → adopción inmediata bajo regla S33.
4. **Si NO**, escalar a Fase 2.

## 7. Aprendizaje meta A29

**A29** — **catálogo sistemático antes que decisión punctual**. Cuando hay 5+ candidatos arquitecturales, hacer un catálogo priorizado por (impacto × confianza) / costo antes de implementar el primero. Evita el costo de implementar el menos prometedor primero (ej: S71 Opción B colapsó NdC porque saltamos directo a A/B sin priorización fina; ahora sabemos que Fase 1 audits baratos son más informativos).

---

**Próximo paso ejecutable**: arrancar Fase 1.1 (HT1.5-NEW-4 audit coords vent vs MIROVA centroids). Es el más barato + más alto impacto + más alta confianza bibliográfica.

---

## Update Fase 1 — verdicts cerrados (2026-05-21)

5 audits ejecutados en paralelo. Resultados:

| Audit | Hipótesis | Verdict | Status |
|---|---|---|---|
| F1.1 | HT1.5-NEW-4 coord vent vs MIROVA | ❌ Refutada 4/5 vols; Tupungatito sí 5.21 km SE | Cerrado — F1.6 follow-up |
| F1.2 | NEW-7+8 unsuitable filters | 🚨 4 GAPS detectados | **Top P1 — F2.1 en implementación** |
| F1.3 | HT1.5-NEW-2 kernel L_bk | ✅ PASS | Descartado |
| F1.4 | NEW-5 geofencing 5km | ❌ Refutado, mantener 25km | Cerrado |
| F1.5 | NEW-6 benchmark Villarrica 2009 | ⏸️ Gap operativo | Aplazado |

**Hallazgo cabeza**: los 4 gaps F1.2 (Test 1 K1 retire flag OFF + edge + dNTI<-0.1 + dETI<-0.1) son la **causa más probable del drift remanente**. SP 426.5 §267-273 cita literal: *"the second condition eliminates the negative outliers that would alter the contextual thresholds"*. Filtros faltantes inflan σ → threshold m+C2·σ alto → pixels que MIROVA descarta entran a nuestro firing.

**Acciones derivadas en paralelo S72**:
- **F2.1** — implementar 4 filtros + flag (subagente activo, bibliografía ⭐⭐⭐)
- **F1.6** — Tupungatito coord re-eval (subagente activo)

**Refutaciones documentadas** (no perseguir):
- C2 distinto Muy Bajo régimen (Laiolo 2017 refuta)
- Two-component Eq.14-16 en NRT (Coppola 2024 explícito)
- Percentil bajo ring vs kernel local (S58)
- Aveni 2025 Eq.9 Villarrica (S24)
- Geofencing 5km Andes (F1.4 empírico)
- Fumarole rim hypothesis 4/5 vols (F1.1 empírico)
- Kernel L_bk solo central (F1.3 code review)

**Estado catálogo**: 13 hipótesis evaluadas, 2 abiertas activas (F2.1 + F1.6), 7 refutadas con cita, 4 cerradas pendientes activación operacional (F2.1 audit).
