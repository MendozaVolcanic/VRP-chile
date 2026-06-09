# Design — Co-validación NTI del Test1 integrado (realineamiento con MIROVA)

**Fecha**: 2026-06-09 · **Sesión**: S104 · **Estado**: DISEÑO (no implementado) ·
**Gate**: A45 (pipeline operacional) + brainstorming (este doc) + TDD + A/B + R2/R3/R8.

## 1. Problema (causa raíz confirmada S104)

Las detecciones VIIRS de los volcanes **nevados** (Tupungatito, Villarrica, Llaima)
se sesgan ~1 km al N/NW del cráter, hacia terreno tibio de baja altitud. **NO** es el
ancla de medición (eso lo arregló S98), **NO** es Lastarria (su offset N es el campo
fumarólico Lazufre real, dato de campo de Nicolás).

**Mecanismo físico** (ground truth: reproc instrumentado Actions run 27173150500,
`docs/AUDIT_S104_VIIRS_POSITION_OFFSET.md`, imágenes `experiments/_s104_roi_probe/out/`):
el campo crudo de BT I04 nocturno está dominado por el **gradiente topográfico de
altitud** — la cumbre nevada está fría (272 K) y el valle tibio (281 K), con el
píxel más caliente a 9 km al N. El lava lake sub-pixel frecuentemente **no produce
señal** detectable sobre el glaciar frío.

**Por qué MIROVA NO se sesga** (Coppola 2016a SP426.5 + 2024, `documentacion/`):
MIROVA detecta sobre **NTI = (L_MIR − L_TIR)/(L_MIR + L_TIR)**, que **cancela el
gradiente topográfico** (MIR y TIR suben juntos sobre terreno tibio → la resta se
anula). Verificado: (I04−I05) en el ROI es plano (mediana 0.01–0.14 K) mientras I04
solo tiene gradiente de 15 K.

**El culpable** (auditoría código): `pipeline/test1_integrated.py:compute_test1_mir`.
- Integra exceso de **radiancia MIR absoluta** sobre TODO el ROI (líneas 140-142):
  `excess_roi = max(0, L_MIR − L_bg)`, `delta_L = Σ excess_roi`.
- `L_bg` = **mediana del anillo** 5–25 km (líneas 132-133) → mezcla cumbre fría +
  valle tibio.
- Centroide **ponderado por el exceso MIR** (líneas 161-168) → el valle tibio supera
  la mediana, aporta peso y arrastra la posición al N.
- **Sin ningún gate NTI** → no distingue lava de topografía.

Esto **diverge de MIROVA**: Coppola 2024 (Eq.13) suma ΔL **solo de píxeles ya
detectados por NTI/dNTI** (Tests 1-3), con fondo local al cluster. Nuestro Test1-MIR
es un drift introducido S13/S25 para curar el recall 0% de Villarrica — resuelve un
problema real (sensibilidad sub-pixel) pero con una implementación que importa el
sesgo topográfico.

## 2. Objetivo

Realinear el Test1 con MIROVA: que **solo integre, dispare y posicione sobre píxeles
que también pasan un gate NTI relativo** — preservando la sensibilidad sub-pixel
(las noches reales disparan dNTI) y eliminando los falsos positivos topográficos
(el valle tibio tiene NTI/dNTI plano).

**No-objetivos (YAGNI)**: no tocar el ancla (S98 OK), no tocar Lastarria fumarólico,
no rediseñar kernel-bg, no tocar los paths NTI/dNTI existentes.

## 3. Decisión de diseño clave — ¿qué gate NTI?

El experimento S104 (`nti_max` ~−0.94 en records reales Y topográficos) muestra que
el **NTI absoluto NO sirve** como gate: el lava lake de Villarrica es tan débil que
casi nunca supera K1=−0.8. Si usáramos NTI absoluto, mataríamos el recall (volvería
el problema que el Test1 vino a resolver en S25).

**El gate correcto es RELATIVO** — el mismo criterio que las noches ALERTA reales
disparan (verificado: en las 11 noches ALERTA MIROVA, la mayoría de nuestros records
disparan path NTI/dNTI relativo):
- **dNTI contextual** (Path D, `detection_context.py`): NTI del píxel vs media de 8
  vecinos > c1. Es lo que MIROVA usa (Coppola 2016a Tests 2-3) y lo que cancela la
  topografía (el valle tibio tiene NTI uniforme → dNTI ~0).
- Alternativa/complemento: **NTI relativo** (Path C): NTI > NTI_bg + max(0.005, 3σ).

**Propuesta**: el gate de co-validación = el píxel debe pertenecer al `hot_mask` de
los paths NTI-relativos ya computados (Path C ∪ Path D), que el pipeline YA calcula
antes del Test1 en `process_viirs.py`. Es literalmente Coppola 2024 Eq.13 (integrar
sobre píxeles detectados). **No introduce un umbral nuevo** — reusa los existentes.

## 4. Mecanismo (cambio quirúrgico)

`compute_test1_mir` recibe un nuevo parámetro opcional `nti_hot_mask: np.ndarray | None`
(2-D bool, mismo shape que `bt`, True donde el píxel pasó Path C/D):

- Si `nti_hot_mask is None` → comportamiento ACTUAL (backward-compatible, rama A/B
  "disabled").
- Si se provee → restringir la contribución:
  ```
  contributing_in_roi = (excess_roi > 0) & nti_hot_mask[roi_mask]
  ```
  Esto propaga a `delta_L` (solo suma píxeles co-validados), `n_contributing`,
  `mask_contributing`, y el **centroide** (pesado solo por píxeles co-validados).
- `abs_criterion`/`rel_criterion` se evalúan sobre el `delta_L` co-validado.

Punto de inserción exacto: líneas 140-150 (gate sobre `contributing_in_roi`) y el
centroide 161-168 hereda automáticamente.

**Caller** (`process_viirs.py:~818`): pasar el `nti_hot_mask` = unión de los hot_mask
de Path C (`n_nti_rel_path`) y Path D (`n_dnti_ctx_path`) ya computados arriba en la
misma función. Gateado por flag de perfil `enable_test1_nti_covalidation`.

**Scope**: VIIRS375 (`process_viirs.py`) primero — donde el sesgo es visible y donde
viven Tupun/Villarrica/Llaima. Replicar a VIIRS750 (`process_viirs_mod.py`) y MODIS
(`process_modis.py`) **solo tras validar** en VIIRS375 (los tres comparten
`test1_integrated.py`, pero el A/B se valida por sensor — A37, no extrapolar).

## 5. Flag de perfil (A/B aislado)

`pipeline/profiles/_test1_covalidation_{enabled,disabled}.yaml` con `data_subdir`
aislado (patrón S24/S25). Flag operacional: `enable_test1_nti_covalidation: bool`
(default **false** en `mirova_equivalent.yaml` hasta validar+adoptar).

## 6. TDD (tests sintéticos ANTES del fix)

`tests/test_test1_nti_covalidation.py`:
1. **Gradiente topográfico puro, sin lava**: campo BT con rampa lineal (cumbre fría →
   valle tibio), NTI plano. Sin gate → Test1 dispara y centroide cae en el valle.
   Con gate (nti_hot_mask todo False en el valle) → **NO dispara** / centroide None.
2. **Lava lake sub-pixel real**: un píxel cerca del cráter con MIR alto Y NTI elevado
   (nti_hot_mask True ahí). Con gate → dispara, centroide EN el cráter.
3. **Mixto** (gradiente + lava): con gate → centroide anclado al cráter, no arrastrado
   al valle.
4. **Backward-compat**: `nti_hot_mask=None` → resultado idéntico al actual (regresión).
5. **Guard shape**: `nti_hot_mask` con shape distinto → ValueError.

## 7. Criterios de aceptación del A/B (antes de adoptar)

Reproc A/B (perfiles aislados) sobre los 11 Tier A, ventana ≥90 d:
- **(R-recall) 0 FN nuevos** en las 11 noches ALERTA_TERMICA MIROVA Villarrica (+ las
  de Tupun/Llaima). Criterio duro — si cae ≥1 noche real, NO adoptar sin revisar.
- **(R-FP) cuántos Test1-puro elimina**: medir reducción de records y del offset
  direccional (objetivo: offset medio VIIRS375 Villarrica de +685N → ~0).
- **(R-ground-truth)** reproc instrumentado del campo crudo de **una muestra de 3-5
  records Test1-puro eliminados** → confirmar que eran topográficos (sin firma
  MIR−TIR), NO actividad real sub-umbral (cat-b, A54). Si alguno tiene firma NTI
  real, revisar el gate.
- **(R-control)** Lascar/Chaitén/NdC (áridos) y Lastarria (fumarólico) **sin cambio**
  → el fix no debe tocar lo que ya está bien.
- **(R2)** posición vs TIF MIROVA donde haya (archive congelado mayo, limitado).
- **(R3)** ratio magnitud vs MIROVA no empeora.

## 8. Procedimiento A45

1. `git tag pre-s<NN>-test1-nti-covalidation <sha>` + push.
2. **OK explícito de Nicolás** antes del primer edit a `test1_integrated.py` /
   `process_viirs.py`.
3. TDD (§6) → fix → suite verde.
4. A/B (§7) en GitHub Actions (no local — Earthdata local roto + 90d > timeout).
5. Si A/B cumple criterios → promover a `mirova_equivalent` + reproc 11 Tier A +
   R8 (deploy + preview 3 vistas) + doc en MIROVA_DIVERGENCES (nueva divergencia
   resuelta) + actualizar CLAUDE.md (regla nueva).

## 9. Pre-mortem / riesgos

- **R1 — perder cat-b real**: algunos Test1-puro podrían ser señal real sub-umbral
  que ni dNTI capta (S25 decía que el Test1 capta lo que pixel-NTI miss). Mitiga:
  gate RELATIVO (no absoluto) + ground truth de muestra antes de adoptar (§7). Si
  el A/B muestra pérdida de noches reales → el gate es muy estricto, ablandar a
  "co-validar solo el centroide, no el trigger" (degradación a opción 1/posición).
- **R2 — el dNTI también se sesga**: si en el valle tibio el dNTI dispara por ruido
  (NTI plano con σ chico → cualquier fluctuación pasa), el gate no filtraría. Mitiga:
  el experimento mostró que las noches ALERTA tienen dNTI y hay 180 Test1-puro SIN
  dNTI → el gate sí separa la mayoría. Cuantificar en A/B.
- **R3 — extrapolación cross-sensor** (A37): validar VIIRS375 antes de VIIRS750/MODIS.
- **R4 — Earthdata local roto**: el A/B corre en Actions (secrets válidos); el probe
  de ground truth también (run S104 ya validó el patrón).

## 10. Qué NO hace este fix (límites honestos)

- No resuelve el campo difuso MODIS (DF-6, anillo gris lejano) — ese es otro path.
- No cuantifica con certeza qué % de las detecciones de Villarrica son topográficas
  vs reales (eso lo da el A/B + ground truth, no este diseño).
- No toca el ancla, ni la magnitud (ctxpeak S100 ya la cura), ni Lastarria.
