# Auditoría de flags dormidos — S99

> **Veta**: flags/parámetros con default OFF (o cap/valor neutro) cuyo comentario
> describe un PROBLEMA REAL del pipeline con un fix ya construido pero desactivado
> y olvidado. Arquetipo: `enable_test1_pixel_filter` (comentario diagnostica
> "suma 14-49 pixels → factor 8-30× MIROVA" pero quedó OFF).
>
> Fuente: `pipeline/profile.py` (defaults) + `pipeline/profiles/mirova_equivalent.yaml`
> (estado operacional). Citas file:line verbatim. Disciplina systematic-debugging.

## Método

1. Listado de TODOS los `ENABLE_*` con default `False` en `profile.py` + cada
   cap/threshold con comentario "default OFF / backward compat / pendiente / A/B".
2. Cruce contra `mirova_equivalent.yaml` (grep `enable_`) para ver cuáles están
   OFF en el perfil operacional → esos son los candidatos dormidos.
3. Veredicto por candidato: ¿problema real aún presente? ¿fix implementado? ¿hay
   A/B asociado y se concluyó? ¿por qué se dejó OFF (puede haber buena razón)?

---

## Estado operacional (grep `enable_` en mirova_equivalent.yaml)

**ON**: eruption_path, dnti_contextual_path, path_d_intra_radio_gate,
second_pass_intra_radio_gate, dnti_dual_roi, test1_path, dual_roi_bt,
vent_anchored_clustering, pixel_level_distance_filter, test1_lbg_global,
first_pass_tests_2_and_3, dual_roi_first_pass, second_pass_adjacent,
dual_roi_second_pass, local_kernel_bg, single_pixel_sub_mw_mode,
vrp_tir_consistency_gate, bt_sat_secondary_guard.

**OFF (candidatos dormidos)**: vent_path, vent_path_modis, nti_relative_path,
**exclude_zones**, **test1_pixel_filter**, **bt_path_hot**, **vrp_tir_output**,
+ defaults-no-presentes: **enable_daytime_modis**, **enable_test1_spatial_core**,
enable_test1_k1_retire_from_hot_mask, enable_test1_k1_bg_exclude,
enable_nadir_fixed_pixel_area_{modis,viirs}, enable_h_d8_5 (eti_quadratic/sum_vrp),
enable_vrptir_aveni, path_d_atm_gate_tbg_min_k (None), path_d_requires_covalidation.

---

## Ranking de candidatos dormidos

### 1. `enable_test1_spatial_core` — ARQUETIPO test1_pixel_filter (EL ACTIVO de S99)

- **profile.py:225-227** (`ENABLE_TEST1_SPATIAL_CORE`, default False) +
  comentario 213-224: *"El Test 1 integrado-ROI es un test de DETECCIÓN: su
  mask_contributing marca todo píxel del ROI sobre la mediana del fondo. Sobre el
  glaciar nevado de Tupungatito en invierno eso es el mosaico nieve/roca entero
  → VRP suma el halo → factor ~8-30× MIROVA"*. `spatial_core_filter` conserva solo
  el foco compacto + guard anti-FN (siempre conserva el pico).
- **Problema real**: SÍ — es exactamente el 19× crónico Tupungatito de S98/S99
  (MEMORY.md: "= TAREA PRINCIPAL S99 §2"). Sigue presente en operacional.
- **Implementado**: SÍ (helper `spatial_core_filter`, params `test1_core_r_km=0.75`,
  `test1_core_bt_ext_k=295`).
- **En operacional**: NO.
- **A/B asociado**: SÍ y EN CURSO — `_s99_test1_core.yaml` (Candidato B) vs
  `_s99_test1_pixfilter.yaml` (Candidato A) vs `_s99_test1_baseline.yaml`. Diseño
  `docs/superpowers/specs/2026-06-03-test1-magnitude-compactness-design.md`.
- **VEREDICTO**: este NO está "olvidado" — es el candidato que la sesión S99 está
  evaluando ahora mismo como reemplazo del arquetipo. Es el fix preferido (espacial,
  guard anti-FN) frente a test1_pixel_filter. **No requiere "redescubrirse"**; sí
  requiere cerrar el A/B y adoptar bajo A45.

### 2. `enable_test1_pixel_filter` — EL ARQUETIPO ORIGINAL

- **profile.py:203-211** (`ENABLE_TEST1_PIXEL_FILTER`, default False) +
  **yaml:171-186**: el comentario operacional dice que Phase 1 fue **REFUTADO S33**
  (commit b9a6857 retirado): *"Driver A solo: recall 74.2%; Driver A + Phase 1:
  recall 55.6% (-18.6pp). Phase 1 destruye señal real validada por MIROVA en
  Lastarria/Villarrica/Planchón (eventos Muy Bajo sub-pixel — el filtro 5σ
  pixel-level elimina los pixels marginales del cluster Test 1 contiguo y rompe la
  detección summit)"*.
- **Problema real**: SÍ diagnostica el factor 8-30× (profile.py:206-209).
- **Implementado**: SÍ.
- **En operacional**: NO.
- **A/B**: histórico (S32/S33) CONCLUIDO con resultado NEGATIVO; re-evaluándose en
  S99 (`_s99_test1_pixfilter.yaml`).
- **VEREDICTO**: **hay una buena razón documentada para dejarlo OFF** — cuesta
  -18.6pp recall (FN en focos sub-píxel: Villarrica lava lake no supera el umbral
  5σ por-píxel). Es el contra-ejemplo del arquetipo: problema real + fix construido
  pero el fix tiene daño colateral conocido. Por eso S99 prefiere spatial_core
  (candidato #1), que tiene guard anti-FN. Reconsiderar SOLO vía A/B contra el
  canario Villarrica.

### 3. `enable_vrp_tir_output` — silenciado provisorio, NO olvidado

- **profile.py:524-531** (default True en profile.py) pero **yaml:360-369 lo pone
  False**: *"Silenciar vrp_tir_mw hasta que el fix completo Coppola 2024 Eq.16 esté
  implementado. Auditoría S81 detectó 726 records con vrp_tir_mw/vrp_mir_mw > 1000×
  POST-S77 gate (top: Villarrica mir=0.98 MW vs tir=5680 MW, ratio 5802×)... emitimos
  vrp_tir_mw=0 — honesto en vez de inflado"*.
- **Problema real**: SÍ (outliers Stefan-Boltzmann sobre máscara contaminada).
- **Implementado**: el OUTPUT sí; el FIX raíz (unmixing A_hot + background subtraction
  T_bk⁴, Coppola 2024 Eq.16) NO — es idea, no construido.
- **En operacional**: OFF deliberado (A45, Nicolás explícito).
- **VEREDICTO**: **NO reconsiderar encender** sin construir primero el fix raíz
  (`docs/F46_VRP_TIR_BUG_S76.md`). El OFF es la decisión correcta (suprime inflado).
  Es lo contrario al arquetipo: el problema es real pero el fix NO está construido.

### 4. `enable_bt_path_hot` — RETIRADO deliberadamente S40

- **profile.py:321-328** (default True) pero **yaml:241-264 lo pone False**: A/B
  run 25804811234 mostró recall 90.5%→92.2% (+1.7pp) al APAGARLO: *"bt_path_hot
  metía pixels lejanos calientes (Salar bordes, terreno cálido) al hot_mask...
  acerca el operacional al clon literal MIROVA"*.
- **Problema real**: SÍ pero **el fix ES apagarlo** (ya apagado).
- **VEREDICTO**: NO dormido — es un OFF que mejora. No tocar.

### 5. `enable_daytime_modis` — A/B CONCLUIDO INCONCLUSO (S92/S93)

- **profile.py:198-201** (default False). Comentario: *"OFF = excluir diurno
  (histórico MIR solo nocturno). ON = procesar MODIS diurno con params día"*.
  Params día listos (K1=-0.6, C1=0.02, 15σ — Coppola 2016a Tabla 1 verbatim).
- **Problema real**: el lever de recall sería detección diurna (NdC/Villarrica
  faint), pero S92/S93 cerraron: de 23 pasadas diurnas, 22→meq=0 (path INOCUO),
  MIROVA OCR=0 alertas diurnas → **A/B inconcluso por ventana sin actividad
  diurna**, R2 inviable (`reference_s91_daytime_ab_pending`).
- **Implementado**: SÍ (flag-OFF, PRs #255-258, tag pre-s90-daytime-modis).
- **VEREDICTO**: fix construido, problema potencial, pero **A/B no demostró
  beneficio** (path inocuo, sin ground truth diurno). Dejarlo OFF es correcto hasta
  que aparezca una ventana con actividad diurna real para validar. Reconsiderar solo
  si se quiere subir recall NdC/Villarrica y hay evento diurno medible.

### 6. `path_d_requires_covalidation` (Opción B D9) — descartada con datos

- **profile.py:464-469** (default False). Opción B del fix D9: el firing contextual
  solo cuenta si BT o NTI también dispararon.
- **Problema real**: SÍ (FPs path D en cirrus, D9). Operacional ya usa la Opción C
  (cap 5 MW, yaml:317).
- **VEREDICTO**: S93 mostró que co-validación GLOBAL mata 93% del recall; SOLO-MODIS
  sería seguro pero quedó como F3 pendiente (`AUDIT_S93`). No es "olvidado": es una
  alternativa explícitamente descartada en su forma global. Reconsiderar solo la
  variante SOLO-MODIS, que NO está implementada como tal en este flag.

### Otros OFF (no-arquetipo, descartados con buena razón o no construidos)

- **enable_exclude_zones** (yaml:170 false): retiro DELIBERADO S27 (MIROVA no usa
  máscaras geográficas). NO reconsiderar (anti-misión).
- **enable_test1_k1_retire_from_hot_mask** (profile.py:335) / **k1_bg_exclude**
  (profile.py:395): drifts Coppola 2016a §298-300/§352-356. Tienen A/B
  (`_drift1a_only`, `_drift1b_only`). Aditivos menores; no diagnostican un problema
  de magnitud grande presente. Baja prioridad.
- **enable_nadir_fixed_pixel_area_{modis,viirs}** (profile.py:405-410): clon literal
  A_pix nadir-fijo, PERO romper la calibración empírica S14 (error ≤0.17% vs OSF) es
  contra-misión sin evidencia. NO reconsiderar.
- **enable_eti_quadratic_scene / enable_sum_vrp_reporting** (H_D8_5, profile.py:276-278):
  A/B S37 REFUTÓ "MIROVA suma todo". Idea cerrada.
- **enable_vrptir_aveni** (profile.py:366): requiere detector TIRVolcH no integrado;
  fix no construido. Experimental_lowT only.
- **enable_vent_path / vent_path_modis / nti_relative_path** (yaml:113-118):
  reemplazados por Test 1 (S27). Anti-misión reactivar.

---

## Conclusión

**Único arquetipo verdadero "problema real + fix construido + OFF + olvidado"** que
NO está siendo ya trabajado: ninguno totalmente olvidado. El más importante
(`spatial_core` / `test1_pixel_filter`, el 19× Tupungatito) **ya es el foco activo
de S99** con A/B en curso. Los demás OFF tienen una de estas razones:
(a) el fix DAÑA recall (test1_pixel_filter −18.6pp),
(b) el fix raíz NO está construido (vrp_tir_output, vrptir_aveni),
(c) apagarlos ES el fix (bt_path_hot, exclude_zones),
(d) A/B concluido sin beneficio (daytime_modis, eti_quadratic, covalidation global).

La hipótesis de Nicolás ("hay más hallazgos dormidos como test1") se confirma
parcialmente: el patrón existe, pero el ejemplar más valioso ya fue redescubierto y
está en evaluación esta misma sesión. No hay un segundo "gigante dormido" con fix
limpio sin daño colateral conocido.
