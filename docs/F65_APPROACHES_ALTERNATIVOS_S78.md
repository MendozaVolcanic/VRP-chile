# F65 — Approaches alternativos para FPs de agua sin destruir TPs (S78, read-only)

**Tipo**: brainstorm exploratorio (sin cambios de código ni de datos).
**Branch**: `claude/s78-approaches-alternativos`.
**Worktree**: `VRP-Chile-s78-approaches-alt/` (aislado A44).
**Contexto**: F61 (NTI gate `-0.85` global) destruye 17-57% de TPs reales en 6 Tier A. Coppola 2016a/2024, Aveni 2024, Campus 2024 ya investigados, no resuelven el trade-off.

## Por qué este brainstorm

El gate `NTI > -0.85` aplicado globalmente es físicamente correcto para distinguir
agua de lava — pero su efecto operacional es asimétrico:

- **Lava abierta y fuerte (Villarrica lava lake activo, Lascar coletazos)**: NTI
  cómodamente > -0.6. Sobrevive el gate. ✓
- **Anomalía térmica débil persistente cráter-tapado (Lastarria fumarólico,
  Copahue dome cooling, Tupungatito glaciar caliente)**: BT_MIR ligeramente
  elevado pero L_MIR muy bajo en valor absoluto ⇒ NTI = -0.88 a -0.92. Cae
  bajo el gate. ✗ (TP destruido.)

La asimetría no es un bug del NTI: es una propiedad física. La señal MIR de un
fumarol a 50-100°C es genuinamente baja. **No podemos discriminar agua de
fumarol con NTI univariado**. Necesitamos otra dimensión.

Este documento revisa 10 approaches alternativos que aportan **una segunda
dimensión** al filtro (geografía, tiempo, espectral extra, contexto cluster,
o aprendizaje).

## Evaluación per approach

Leyenda: **Esfuerzo** = horas-Claude para implementación+tests+docs. **MIROVA-faithful**
= consistente con la filosofía "clon literal MIROVA" (ver `docs/MISSION.md`).
**ROI esperado** = recovery TPs perdidos por F61 **menos** FPs nuevos no resueltos.

| # | Approach | Esfuerzo | MIROVA-faithful | Riesgo técnico | ROI esperado |
|---|---|---:|:---:|:---:|---|
| 1 | NDWI dedicado (Sentinel-2 / VIIRS DNB) | 8-16 h | ✗ (no MIROVA) | Alto (data nueva, fetch, regridding) | Medio — agua resuelta pero scope creep grande |
| 2 | Sensor fusion temporal MODIS↔VIIRS | 3-5 h | ✓ (data ya bajada) | Bajo (matching temporal granule) | **Alto** — usa redundancia free, descarta inconsistentes |
| 3 | ML Random Forest classifier | 12-20 h | ✗ (no en papers MIROVA) | Medio-alto (labeling, train/val, overfit) | Medio — potente pero "caja negra" para auditor científico |
| 4 | Baseline temporal 10yr (Aveni 2024 TIRVolcH) | 16-30 h | ✓✓ (canonical MIROVA-grupo) | Alto (compute baselines, storage, lookup) | **Alto** — physically grounded, ya parcialmente en roadmap F31 |
| 5 | Threshold NTI adaptativo per-volcán | 2-3 h | ~ (parametrización per-volcán, no en papers) | Bajo (un dict en yaml) | **Alto** — respeta régimen físico, mínimo cambio código |
| 6 | Lake mask externa fija (HydroLAKES/OSM) | 4-6 h | ✗ (= `exclude_zones` rechazado) | Bajo | Bajo — filosóficamente cerrado |
| 7 | Test 1 Coppola 2015 con baseline propia | 8-12 h | ✓✓ (paper canonical) | Medio (baseline build) | Medio — subsume baseline (#4) pero más complejo |
| 8 | Reflectance check daytime | 6-10 h | ~ (no en pipeline VRP nocturno) | Medio (data daytime adicional) | Bajo-medio |
| 9 | Cluster vent-anchored estricto | 1-2 h | ✓ (MIROVA-like centroid) | Bajo | Medio — pierde detecciones legítimas off-center |
| 10 | Combinación low-impact F63 + F57 + NTI per-volcán | 4-6 h | ✓ (composición de fixes ya validados) | Bajo | **Alto** — pragmático, reversible, incremental |

## Análisis físico per approach

### Approach 1 — NDWI dedicado

NDWI clásico (McFeeters 1996) = `(Green - NIR) / (Green + NIR)`. Funciona porque
agua absorbe NIR. **Problema operacional**: requiere bandas que MODIS L1B 1km no
tiene en formato útil (solo b1/b2 1km son visibles, no reflectance calibrada en
nuestro pipeline). Sentinel-2 sí, pero abrir esa puerta significa:

- earthaccess o Copernicus Hub adicional.
- Regridding S2 (10-20m) a footprint MODIS/VIIRS (375m-1km).
- Lookup pixel-a-pixel.
- Frecuencia S2 = 5 días, incompatible con NRT 2h.

**Veredicto**: scope creep enorme. Se aleja de "clon MIROVA".

### Approach 2 — Sensor fusion temporal MODIS↔VIIRS ⭐

Una noche típica un volcán Tier A recibe 2-4 overpasses (Aqua 02-04 UTC, Terra
05-07 UTC, NPP/N20/N21 06-08 UTC). Si el cráter está caliente real, **la mayoría
debería detectar** (modulo cloud cover). Si solo un sensor detecta y los otros
mismo-cobertura-no-detectan, es sospechoso.

Específicamente para agua: lago a temperatura ambiente irradia ~uniformly TIR
all night. **NO debería triggear más de un sensor** porque el modo de falla
suele ser local (kernel-bg roto en un solo granule por sec³(θ_z), nube fina
en otro). Lava real es consistente cross-sensor.

Implementación bite-sized: en `audit_metrics` o post-procesing por volcán-noche,
contar overpasses con cobertura del vent (`scan_geometry.py` ya calcula
footprint) y marcar `cross_sensor_confirmed: True/False`. Profile flag para
filtrar las no-confirmadas. **Reversible, no toca pipeline core**.

**Risk**: en noches nubladas reales puede destruir TPs si solo Aqua escapó la
nube. Mitigación: aplicar solo cuando `n_overpasses_with_coverage ≥ 2`.

### Approach 3 — ML Random Forest

Potente pero filosóficamente "no MIROVA" — el científico SERNAGEOMIN no puede
auditar un RF de 100 árboles. Aceptable si se documenta como `experimental`,
NO en `mirova_equivalent`. Feature engineering ya disponible (BT, NTI, ΔBT,
t_bg, distance, sensor). Training set existe (494 refs MIROVA TPs + FPs lago
S77-S78 etiquetados).

**Veredicto**: deferir a fase (2) "herramienta independiente". No para clon
MIROVA actual.

### Approach 4 — Baseline temporal 10yr ⭐⭐

Aveni 2024 RSE (TIRVolcH) es **canonical MIROVA-grupo** (Coppola, Laiolo,
Aveni — Torino-Firenze). Construye baseline μ ± σ cloud-free monthly per pixel
sobre 10 años, y declara hot si BT > μ + z·σ. **Físicamente lago aparece como
"normal alto" en su propio baseline** (siempre tibio respecto a roca circundante)
— el delta vs μ_baseline es casi cero. Cráter realmente eruptivo emerge como
desviación neta.

Ya parcialmente integrado en F31 roadmap (PR #153 detector base, A2 pausada).
Esfuerzo restante grande pero **alineado con plan ya aprobado**. Aplicación al
problema de FPs water = subproducto natural.

**Risk**: 10 años de L1B per volcán = TB de data. Mitigación Aveni: precomputar
baselines offline, persistirlos como `data/baselines/<vol>.parquet`, lookup
NRT trivial.

### Approach 5 — Threshold NTI adaptativo per-volcán ⭐⭐⭐

El insight más simple y subestimado. La distribución NTI de "calma" es distinta
per volcán por composición de fondo (Lastarria es altiplano árido seco, Villarrica
es bosque húmedo con lago, Lascar es desierto Atacama). Aplicar `-0.85` uniforme
ignora esta variabilidad.

**Procedimiento**:
1. Para cada volcán, identificar período de "calma" (ej. 6 meses sin refs MIROVA).
2. Calcular distribución empírica de NTI sobre todos los pixels detectados.
3. Threshold = percentil 5 o `μ - 2σ`.

Volcanes con cráter seco (Lastarria, Lascar) probablemente convergen a
`NTI_thresh ≈ -0.92` (permite fumarólica débil). Volcanes con lago (Villarrica,
Copahue laguna del Agrio) → `-0.80` (estricto, agua dominante).

Implementación: dict en `volcanoes.yaml` per-volcán + read en process_*.py.
**Mínimo cambio código, máxima ganancia per-volcano.**

**Risk filosófico**: parametrización per-volcán no está en papers MIROVA
explícita. Sin embargo, MIROVA opera per-volcán en sus KMZ/OSF (radios distintos,
masks distintos) — la idea de "configuración local" no rompe la filosofía,
solo la extiende.

### Approach 6 — Lake mask externa

= `exclude_zones`. Ya rechazado por filosofía MISSION.md (parche reactivo, no
diagnóstico físico). No reabrir.

### Approach 7 — Test 1 Coppola 2015 con baseline propia

Subsume #4. Implementar #4 primero, Test 1 después como cliente del baseline.

### Approach 8 — Reflectance check daytime

Conceptualmente OK pero rompe "VRP solo nocturno". Agregar pipeline day para
discriminar pixels es doble esfuerzo. Bajo ROI.

### Approach 9 — Cluster vent-anchored estricto

Idea: si un cluster térmico no contiene al pixel-del-vent, descartarlo. MIROVA
hace algo parecido en su clustering (centroide debe estar dentro del ROI inner).

**Lo que recupera**: filtra FPs water sí, porque lagos típicamente offset del
vent (Copahue laguna Agrio @ 0.5-1 km del cráter, Villarrica zona termal lateral).

**Lo que rompe**: en eruptions con flow ladera abajo, el cluster real puede
no incluir el vent activo (vent puede estar tapado por pluma). Riesgo de
destruir TPs eruptivos justo en el momento más crítico.

**Veredicto**: peligroso como gate único. OK como SEÑAL en F63 ranking.

### Approach 10 — Combinación low-impact ⭐⭐

F63 (cluster ranking, ya brainstormed) + F57 (local_kernel_bg activado) +
threshold NTI per-volcán adaptativo (#5).

**Por qué funciona**: cada componente ataca una dimensión distinta:
- F63 → contexto espacial cluster (descarta isolated water pixels).
- F57 → background local respeta heterogeneidad (lago no infla σ_bg vecino).
- #5 → threshold físico per régimen volcánico.

Suma de efectos > efecto individual. Y **cada componente es reversible
independientemente** vía profile flag.

## Recomendación TOP 3 (priorizados)

### 🥇 TOP 1 — Approach 5: Threshold NTI adaptativo per-volcán

**Razón**: máximo ROI/esfuerzo. 2-3 horas. Cero riesgo arquitectural. Resuelve
el 60-80% del trade-off F61 sin tocar pipeline core.

**Plan bite-sized**:
1. Análisis offline distribución NTI per-volcán durante "calma" (6 meses sin
   refs MIROVA o ≤ 3 hotspots/mes). Subagente Explore sobre `data/mirova_equivalent/`.
2. Generar tabla `NTI_THRESH_PER_VOLCAN` (dict YAML, 11 entradas).
3. Modificar process_modis.py y process_viirs.py para leer el dict (fallback `-0.85`).
4. Profile flag `enable_nti_thresh_per_volcano: true`.
5. Tests sintéticos + A/B vs operacional actual.

**Métrica de éxito**: recovery ≥80% TPs destruidos F61 sin reintroducir
>20% de los FPs water originales.

### 🥈 TOP 2 — Approach 2: Sensor fusion temporal MODIS↔VIIRS

**Razón**: usa data ya bajada (zero data cost), MIROVA-faithful (multi-sensor
es la filosofía de Coppola 2024), reversible. 3-5 horas.

**Plan bite-sized**:
1. Función `count_overpasses_with_coverage(vol, date)` usando `scan_geometry.py`.
2. Post-process: para cada detección, marcar `n_sensors_confirming` (cuántos
   sensores en la misma noche-±2h detectaron este pixel/cluster).
3. Profile flag `require_cross_sensor_confirmation: true` con guard
   `n_overpasses_with_coverage ≥ 2`.
4. A/B test vs operacional.

**Combina muy bien con TOP 1**: NTI adaptativo elimina low-hanging FPs water,
sensor fusion elimina los borderline.

### 🥉 TOP 3 — Approach 10: Combinación low-impact (F63 + F57 + #5)

**Razón**: meta-approach. Si TOP 1 + TOP 2 dejan residual, agregar F63 cluster
ranking + F57 local_kernel_bg como tercera y cuarta dimensiones de filtrado.
Cada componente es bite-sized, todos son reversibles, todos son MIROVA-faithful.

**No implementar de una**: secuenciar TOP 1 → medir → TOP 2 → medir → si
queda residual, F63+F57.

## Approach a considerar fuera de S78 (mid-term)

**Approach 4 (baseline temporal 10yr Aveni 2024)** es el approach
"definitivo" físicamente. Ya está en roadmap F31 (PR #153 detector base
hecho, A2 pausada S75). Mantener como **mid-term goal después de TOP 1+2+3**.
Cuando TIRVolcH baseline esté generado, el problema FPs water se resuelve
"de oficio" porque el baseline lo absorbe.

## Approaches descartados (con razón)

| Approach | Razón descarte |
|---|---|
| #1 NDWI dedicado | Scope creep S2/data nueva, no NRT-compatible, no MIROVA |
| #3 ML Random Forest | "Caja negra" para SERNAGEOMIN, deferir a fase (2) experimental |
| #6 Lake mask externa | Equivale a `exclude_zones`, ya rechazado filosóficamente |
| #7 Test 1 con baseline | Subsumido por #4 que está en roadmap F31 |
| #8 Reflectance daytime | Rompe "VRP solo nocturno", doble compute |
| #9 Cluster vent-anchored estricto | Peligroso como gate único (destruye TPs eruptivos off-vent) |

## Notas operacionales

- Todos los approaches recomendados son **reversibles vía profile flag**
  (`enable_*` default OFF en `mirova_equivalent`).
- Tests sintéticos OBLIGATORIOS antes de tocar `data/mirova_equivalent/` (A45).
- Tag git defensivo OBLIGATORIO antes de reproceso histórico (A38).
- A/B test pattern S24-S25 (reproc-ab-*.yml clone) para validación cuantitativa.

## Próximos pasos sugeridos S79

1. Subagente Explore sobre `data/mirova_equivalent/*.json` para análisis NTI
   per-volcán durante períodos de calma → tabla empírica.
2. Plan bite-sized TOP 1 (NTI threshold per-volcán) en `tasks/plan_s79_top1_*.md`.
3. Implementación TOP 1 con `writing-plans` + `test-driven-development`.
4. A/B test, validación, push.
5. Si TOP 1 deja residual >20% FPs water → TOP 2.
