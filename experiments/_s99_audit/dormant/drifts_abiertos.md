# Drifts / hipótesis / divergencias ABIERTAS o abandonadas — auditoría S99

**Fecha**: 2026-06-03
**Misión**: barrer ~99 sesiones de docs de drift/divergencia/hipótesis buscando items marcados
ABIERTO / PENDIENTE / no resuelto / sin validar / DIFERIDO / investigación-no-adoptada que se
hayan abandonado, y verificar contra el código actual si siguen abiertos hoy.

**Docs barridos**: `DRIFTS_S17.md`, `MIROVA_DIVERGENCES.md`, `MIROVA_DIVERGENCES_CATALOG_S71.md`,
`HYPOTHESIS_LOG.md`, `AUDIT_S86.md`, `AUDIT_INTEGRAL_S81.md`, `AUDIT_S95_gaps_sistemicos.md`,
`MIROVA_INTRA_RADIO_GATE_S81.md`, `F28_HYPOTHESIS_LOG.md`, `PAPERS_MIROVA_SYNTHESIS_S71.md`,
`R2_GATES_BY_REGIME.md`, specs en `docs/superpowers/specs/`.

**Verificación de código** (flags leídos en `pipeline/profile.py` + `pipeline/profiles/mirova_equivalent.yaml`):
- `enable_unsuitable_filters_267_273` → **default True** (adoptado de facto, NEW-8).
- `enable_test1_k1_retire_from_hot_mask` → **default False, NO en yaml operacional** (NEW-7 SIGUE ABIERTO).
- `enable_first_pass_tests_2_and_3: true` en yaml → R6 drift #2+3 (Test 3 dETI conjunción) ADOPTADO.
  Caveat: el `contextual_dnti_hot_mask` viejo (sólo Test 2, dnti>c1) sigue siendo llamado en paralelo
  (process_modis.py:506/517) — coexistencia, no drift limpio.
- `enable_second_pass_adjacent: true` → R6 drift #4 cerrado.
- `path_d_only_cap_mw: 5.0` / `path_d_only_cap_tbg_max_k: 270.0` → D9 mitigación adoptada (parcial).
- `enable_daytime_modis: false` (default) → detección diurna NO adoptada (A/B inconcluso, cerrado).
- `enable_bt_path_hot: false` → D7 (local p95 VIIRS-I) neutralizado por bt_path OFF.

---

## RANKING de items abiertos por impacto (FN > FP > magnitud > cosmético)

### 🔴🔴 ALTO — siguen abiertos hoy y afectan magnitud/cluster (mismo tipo que D8/D9 ya resueltos)

| ID | Descripción | ¿Abierto hoy? | Impacto | Doc fuente |
|---|---|---|---|---|
| **D9 causa raíz** | Path D dNTI ctx sobre cirrus/fondo frío: **el cap 5 MW tapó la magnitud absurda, pero la causa raíz arquitectural sigue ABIERTA** — ratios post-cap 24-83× cuando MIROVA presente, 6-12× independiente del cap, en Villarrica/Chaiten/PP/Tupungatito/NdC. | **SÍ — ABIERTA explícita** | MAGNITUD alta (sistémico Muy Bajo) | MIROVA_DIVERGENCES.md §D9 (línea 270); MIROVA_DIVERGENCES_CATALOG_S71 fila D9 "PARCIALMENTE RESUELTO" |
| **NEW-7 (F1.2 gap)** | `enable_test1_k1_retire_from_hot_mask` debe retirar pixels Test1-K1 de la máscara de firing (SP426.5 §298-300 "discarded for further steps"). **Flag default False, ausente del yaml operacional**. Era 1 de los "4 gaps F1.2" señalados como causa más probable del drift remanente Muy Bajo. | **SÍ — NO adoptado** | MAGNITUD/FP (infla σ → threshold alto → entran pixels que MIROVA descarta) | MIROVA_DIVERGENCES.md §F1.2; CATALOG_S71 NEW-7; verificado profile.py:335 |
| **Gate intra-radio MODIS (S81 P0)** | 10/11 Tier A: 0 ALERTA MODIS de MIROVA pero nosotros gritamos ~70-100/volcán en el mismo granule intra-radio. "Mayor payoff del proyecto en MODIS". Mecanismo a determinar (N·σ path, NDVI, cluster≥2px, MOD14). **MARCO PARCIALMENTE REINTERPRETADO por S86** (46% de esos "FPs" son features volcánicas reales cat. b), pero el subconjunto artefacto + la metodología de gate quedó SIN cerrar. | **SÍ — "ABIERTO P0 reformulado"** | FP masivo MODIS (precision) | MIROVA_INTRA_RADIO_GATE_S81.md (línea 165) |
| **MODIS recall-al-cráter ~9-12% (deuda Salar)** | MODIS casi ciego al cráter en vols débiles; primary_cluster se va al Salar de Atacama (Lascar) o campo glaciar. Recurrente S88/S94/S97. Es el contrapeso FN del gate intra-radio. | **SÍ — deuda activa** | **FN** (lo más grave) + magnitud | AUDIT_S94_per_sensor; reference_s94/_s97 (MEMORY) |

### 🟡 MEDIO — abiertos, candidatos arquitecturales no probados o diferidos

| ID | Descripción | ¿Abierto hoy? | Impacto | Doc fuente |
|---|---|---|---|---|
| **HT1.5-NEW-1** | MIROVA agrega Σ scene-wide de pixels alerted dentro del radio vs nuestro `primary_cluster`. **Re-interpretada S72** (F1.8/F1.9: state-of-art = primary_cluster, probable que estemos bien) pero NUNCA se corrió el A/B F2.1 scene-wide para cerrarla. Queda "bajada de prioridad, no refutada". | Abierto (bajada prioridad, sin A/B) | MAGNITUD/cluster | CATALOG_S71 NEW-1; §"Re-interpretación HT1.5-NEW-1" |
| **HT1.5-NEW-3 (Method-2)** | MIROVA descarta mínimos locales semanales en post-processing (Coppola 2023 §530-540) para reducir contaminación de nube. **NO implementado** (explícito en PAPERS_MIROVA_SYNTHESIS_S71:122). Es presentation-layer, no NRT core. | **SÍ — NO implementado** | MAGNITUD/FP (suaviza cola) | MIROVA_DIVERGENCES.md §HT1.5-NEW-3; SYNTHESIS_S71 |
| **D7 (local p95 VIIRS-I 375m)** | MODIS y VIIRS-750 aplican filtro local p95; VIIRS-I 375m NO. "Neutralizado hoy por bt_path off, **no resuelto**". A/B vs OSF barato pero nunca corrido. Si se reactiva bt_path sin agregar p95 → regresión latente. | **SÍ — "no resuelto"** | FP VIIRS-I (sensor caballo de batalla) | DRIFTS_S17.md §D7; AUDIT_INTEGRAL_S81:119 |
| **R6 drift #7 (sec³ θz MODIS)** | scan-angle elongation: el paper usa A_pix=1 km² fijo; nosotros aplicamos sec³ (correcto físicamente, A36). Listado como "probable causa ratio 1.21×" sin A/B aislado que lo confirme/refute. | Documentado, sin A/B aislado | MAGNITUD baja (~1.2×) | HYPOTHESIS_LOG S45+R6 drift #7 |
| **Mecanismo 1 S45 (cluster selection Lascar MODIS)** | 4 FN Lascar: el pixel cráter SÍ está en anomaly_pixels pero el clustering lo entierra bajo el Salar; `enable_summit_priority_eruption` propuesto S46 nunca implementado. Solapa con deuda Salar. | Abierto (flag propuesto, no impl.) | **FN** | HYPOTHESIS_LOG S45 Mecanismo 1 |

### 🟢 BAJO / cosmético — abiertos pero sin urgencia o ya documentados como diseño

| ID | Descripción | ¿Abierto hoy? | Impacto | Doc fuente |
|---|---|---|---|---|
| D4 (escala alerta dashboard Low/Medium/.../Extreme) | Feature parity de presentación, nunca agregado. | SÍ (sin urgencia) | Cosmético | DRIFTS_S17.md §D4 |
| D2 ground truth CSV ~70% VIIRS | Re-scrape para cerrar gaps; mitigado por universo CONS+OCR (S86 loader fix). | Parcial (mitigado) | Métricas | MIROVA_DIVERGENCES.md §D2 |
| NEW-6 (reproducir Villarrica 2009 Fig A6) | Benchmark de fidelidad; aplazado por pyhdf roto Windows + falta dump rasters. | SÍ (aplazado) | Validación | CATALOG_S71 NEW-6 / F1.5 |
| F28 BT-saturation guard opciones | Varias sub-hipótesis "ABIERTA dependent de adopción" (hard-block frontend, etc.). | Parcial | FP raro | F28_HYPOTHESIS_LOG.md |
| Mecanismo 2 S45 (Test1 con vrp_mw=0) | Edge case: Test1 dispara pero VRP=0 en cluster sutil; backlog filtrar anomaly_pixels por vrp>0. | Abierto (backlog) | Cosmético/FN raro | HYPOTHESIS_LOG S45 Mecanismo 2 |

### Verificados como CERRADOS / RESUELTOS (no perseguir)

- **D1** kernel median→mean (RESUELTO S17, np.mean confirmado en código).
- **D2 N·σ** (RESUELTO: dual-ROI 5σ summit/10σ scene + cap 7K, en yaml).
- **D3** TIR Stefan-Boltzmann (RESUELTO S17, Aveni 2024 RSE confirma SB puro).
- **D6** std_bg global (REFUTADO S21 empíricamente, ratio 0.81).
- **D8 (cluster selection PCC/Puyehue)** (RESUELTO S38 `enable_vent_anchored_clustering: true`, cierre formal S86).
- **D8 (background ring contaminado)** (RESUELTO S60-62 kernel-bg per-vol).
- **NEW-8 unsuitable filters edge/dNTI<-0.1/dETI<-0.1** (ADOPTADO, default True profile.py:385).
- **R6 #2+3 Tests 2∧3 / Test 3 dETI** (ADOPTADO `enable_first_pass_tests_2_and_3: true`; caveat: path viejo Test2-solo coexiste).
- **R6 #4 second_pass_adjacent** (ON).
- **NEW-5 geofencing 5km** (REFUTADO F1.4: 21.79% OSF >5km).
- **HT1.5-NEW-2 (L_bk excluye todos hot pixels)** (PASS F1.3).
- **HT1.5-NEW-4 (coord vent vs fumarole rim)** (REFUTADA 4/5; Tupungatito sí → resuelto S98 ancla=cráter).
- **NEW-10 two-component Eq.14-16** (descartado, MIROVA NRT no usa).
- **Daytime MODIS** (A/B inconcluso por ventana sin fenómeno, flag OFF, cerrado S92/S93).
- **H1-H7, H10** (refutadas/implementadas S17-S22).

---

## Observaciones meta

1. **El patrón de los items abiertos de ALTO impacto es el mismo que D8/D9 ya resueltos**: divergencia
   de magnitud / selección de cluster en volcanes Tier A "Muy Bajo" (Villarrica, Chaiten, PP, Tupungatito,
   PCC, NdC) bajo cirrus / fondo frío / glaciar. D9 causa-raíz + NEW-7 + intra-radio MODIS son tres caras
   del mismo fenómeno físico (path D / Test1 suma pixels marginales que MIROVA filtra).

2. **NEW-7 (Test1 K1 retire) es el item barato-y-abierto más prometedor**: tiene cita bibliográfica
   directa ⭐⭐⭐ (SP426.5 §298-300), flag YA implementado en código pero **default OFF y ausente del yaml
   operacional**, y fue señalado en S72 como "causa más probable del drift remanente". El A/B F2.1 se
   corrió para los OTROS filtros (NEW-8 unsuitable, adoptados) pero el K1-retire quedó deliberadamente
   aislado "para A/B S72 F2.3" (profile.py:383-384) que aparentemente nunca se cerró.

3. **El marco S86 reencuadra (no cierra) el gate intra-radio MODIS**: 46% de los "FPs" son features
   volcánicas reales (cat. b). Pero eso NO cierra el item — separa el trabajo en (a) etiquetar
   honestamente vs (b) el subconjunto artefacto real (cat. d, 4.6%, cirrus PCC + glaciar Tupungatito)
   que sigue sin gate. La deuda MODIS recall-al-cráter (FN) es el reverso y es lo MÁS grave por ser FN.

4. **Riesgo latente D7**: si alguien reactiva `enable_bt_path_hot` sin agregar el filtro p95 a VIIRS-I,
   reaparece la divergencia. Conviene un guard test (sugerido ya en AUDIT_INTEGRAL_S81:128).
