# Design — Supresión display del artefacto "campo difuso (fondo frío)"

**Sesión**: S93 (2026-05-30). **Tipo**: display-only, NO toca pipeline (A55).
**Precedente**: extiende el filtro cirrus S90 (`2026-05-30-display-cirrus-artifact-suppression-design.md`).

## 1. Problema (fenómeno físico)

El dashboard de PuyehueCordonCaulle muestra picos de magnitud como **337.7 MW**
(record 2026-05-05 07:30 MODIS_AQUA) cuando MIROVA reporta el mismo evento a
**0.3 MW** (foco VIIRS375). Nicolás (operador) lo señaló como engañoso: 337 MW es
energía de erupción efusiva, no de un lacolito difuso de señal baja.

**Diagnóstico (record 05-05):** `t_bg_k=242.9` (−30 °C), `t_max_k=274.98` (+1.8 °C),
`diag_n_dnti_ctx_path=362` (todos los píxeles por path D, 0 por BT/NTI/ETI),
`primary_cluster: 670 px, 337.7 MW`. Sobre un fondo gélido, terreno normal apenas
sobre cero aparece como anomalía de +32 K y el path D contextual lo marca píxel a
píxel; 670 píxeles × ~0.5 MW = 337 MW de pura suma. **No es el lacolito** (que es
sub-píxel para MODIS 1 km — solo VIIRS 375 m de MIROVA lo resuelve). Es el
**artefacto A23/D9** (path D sobre fondo frío), la misma familia que el cirrus,
separado solo por estar el píxel a +1.8 °C en vez de bajo 0 °C.

**Reclasificación**: estos records pasan de "cat. b sobre-estimada" (S91/S92) a
**cat. d artefacto** — consistente con A54 (que ya lista "cirrus path D PCC" como
el 4.6 % de artefactos reales).

## 2. Discriminante físico (validado)

El primer criterio candidato (solo `t_max` bajo) fue **refutado con datos**: la
franja `t_max ∈ [0,5) °C ∧ VRP≥10` tiene 157 records en los 11 Tier A, muchos
**focos reales débiles** (p.ej. Copahue 81 MW con 3 px, VRP/px=27) — el píxel está
apenas sobre cero en absoluto pero concentra radiancia sobre fondo frío. Filtrar por
`t_max` solo destruiría señal real (rompe A54).

El discriminante correcto separa **cómo se reparte la radiancia**:
- **Foco real**: pocos píxeles, mucha radiancia c/u (VRP/px alto 8–56). Concentrado.
- **Campo difuso artefacto**: cientos de píxeles, casi nada c/u (VRP/px ~0.5). Disperso.

**Criterio** (usa `t_max` + geometría del cluster, NUNCA `t_bg` → respeta escudo §3.2):
```
isDiffuseFieldArtifact(r) :=
    NO _mirova_confirmed
  ∧ primary_cluster existe
  ∧ t_max_k < 278.15            (5 °C: píxel apenas sobre el fondo)
  ∧ n_pixels ≥ 100             (campo amplio)
  ∧ mirovaEqVrp(r) ≥ 50        (solo los PICOS engañosos, no señales menores)
  ∧ mirovaEqVrp(r) / n_pixels < 1.0   (radiancia dispersa, NO foco)
```

**Validación (45 volcanes)**: atrapa 14 records; **12 ya los cubre el filtro cirrus**
(t_max<0 °C); solo **2 nuevos** (PCC 05-05 337 MW, PCC 05-01 146 MW). **0 señales
reales atrapadas** (el evento eruptivo Lascar 02-17 bajo nube fría tiene t_max
+15/+45 °C y 2–9 px → NO cae en el criterio). Script:
`experiments/_s93_warmscene/validate_criterion.py`.

## 3. Diseño (3 vistas standalone — helpers duplicados, S92 L5)

Mismo tratamiento que el cirrus, vía wrapper unificado:
- Agregar `isDiffuseFieldArtifact(r, ...)` junto a `isCirrusArtifact` en cada vista.
- Agregar `isThermalArtifact(r, ...) = isCirrusArtifact(r) || isDiffuseFieldArtifact(r)`.
- Reemplazar los usos de supresión `isCirrusArtifact` → `isThermalArtifact` en:
  chart, métricas (`eqVrp`/`eqVrpDisplay`), cards/no-titular, sparkline, latestVRP.
- **Badge (solo index, tiene tabla)**: distinguir — `isCirrusArtifact` → "artefacto
  cirrus"; `isDiffuseFieldArtifact` → **"campo difuso (fondo frío)"** (texto elegido
  por Nicolás). Tooltip: magnitud = suma de muchos píxeles apenas tibios sobre fondo
  gélido (path D), no un foco volcánico real.
- CSS: reutilizar `row-cirrus-artifact` (atenúa fila, opacity 0.5) para ambos tipos.

Firmas por vista (sin cambio): index `(r, innerKm)`, diario `(r, volcanoName)`,
mosaico `(r, innerKm)`.

## 4. Alcance / no-objetivos
- **NO toca pipeline.** El record conserva `pc.vrp_mw=337` en los datos (provenance
  / paper); solo se atenúa+etiqueta y no infla el gráfico/tarjeta.
- **NO usa `t_bg`** (gate refutado S86 que mata Lascar bajo nube fría).
- **Item pipeline futuro** (abierto, NO en este PR): gate de coherencia en
  detección/selección con proceso completo (tag A45 + TDD + reproc local + R2 vs
  TIF). Documentado aparte. El display es defensa-en-profundidad útil aun si se hace.

## 5. Verificación
- `validate_criterion.py` → 0 reales atrapadas, 2 nuevos (PCC), reproducible.
- Preview navegador real (no `node --check`) en las 3 vistas: PCC ya no titula 337
  MW; fila atenuada + badge "campo difuso (fondo frío)"; chart sin el pico.
- Las 3 vistas sirven desde `/frontend/`, BASE_PATH=`/`, data en `/data/...`.

## 6. Pre-mortem
- *Riesgo*: umbrales (100 px, VRP/px 1.0, 5 °C, 50 MW) ajustados a 2 records →
  "huele a hardcode". *Mitigación*: el criterio es físicamente general (campo
  disperso vs foco); validado en 45 vols, 0 reales. Documentar que es estrecho a
  propósito (solo los picos engañosos).
- *Riesgo*: futura colada de lava extendida real (muchos px) marcada como artefacto.
  *Mitigación*: una colada real tiene `t_max` ALTO (lava) → el gate `t_max<5 °C` la
  excluye. La incoherencia (VRP alto + píxel frío) es la firma del artefacto.
