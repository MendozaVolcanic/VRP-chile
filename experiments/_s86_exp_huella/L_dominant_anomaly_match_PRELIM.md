# Validación 1:1 anomalía dominante: ¿nuestra mayor = la mayor de MIROVA? (PRELIMINAR S86)

**Fecha**: 2026-05-28
**Objetivo (definido por Nicolás S86)**: para cada pasada satelital (timestamp × volcán × sensor) donde MIROVA reporta su mayor anomalía, ¿nuestra mayor anomalía es la misma? Si no coincide, descubrir cómo arreglarlo.
**Estado**: PRELIMINAR — solo OCR (que trae distancia parseable), comparación radial (no 2D), datos pre-fix-loader. El experimento completo es S87 post-Bloque 2.

## Resultado preliminar (3 vols control)

| Volcán | Match (gap ≤2 km) | Diagnóstico |
|---|---|---|
| Tupungatito | 92% (24/26) | Sano — mismo punto que MIROVA salvo 2 casos a ~7km |
| Chaitén | 62% (5/8) | Divergencia moderada (MIROVA ~2.8-3.1 km, nuestro ~0.2 km) |
| **PCC** | **0% (0/34)** | **Reportamos punto totalmente distinto** |

## Hallazgo central — PCC reporta el centro volcánico equivocado

**Fenómeno físico**: el sistema Puyehue–Cordón Caulle tiene dos centros separados ~12 km. El vent nominal cargado es el volcán Puyehue. La actividad térmica real está en el Cordón Caulle (fisura erupción 2011, lacolito).

**MIROVA** reporta consistentemente la anomalía del Cordón Caulle a ~12-14 km del Puyehue (la mayor anomalía real). **Nosotros** reportamos a ~0.4-1 km (pegados al vent Puyehue). 34/34 pasadas divergen.

**Mecanismo del pipeline (causa raíz)**: el fix D8 `vent_anchored` elige el cluster más cercano al vent. Con el vent en el Puyehue, ancla ahí. La mayor anomalía (lacolito Cordón Caulle) está dentro del `inner_radius=20km` pero lejos del vent → vent_anchored la ignora porque prioriza proximidad sobre magnitud. MIROVA hace lo opuesto: reporta la mayor de la escena.

**Dos causas, ambas arreglables**:
1. Vent nominal de PCC está en el Puyehue, no en el Cordón Caulle.
2. `vent_anchored` prioriza cercanía sobre magnitud (opuesto a MIROVA).

## Chaitén (divergencia moderada)

3 de 8 pasadas: MIROVA reporta a ~2.8-3.1 km, nosotros a ~0.2 km (domo/cráter). Gap menor que PCC. Requiere investigación 2D: ¿qué hay a ~3 km del domo Chaitén que MIROVA reporta? ¿actividad dispersa real o punto distinto?

## Tupungatito (sano)

92% match. Los 2 diverge: MIROVA a ~7km vs nuestro ~0.4-1km (cráter). Podrían ser los casos donde MIROVA reportó el ring glaciar lejano (A19) y nosotros bien el cráter — verificar dirección de la divergencia (¿quién tiene razón?).

## Limitaciones (declaradas)

- Solo OCR (CONS no parseada — distancia=0, Bloque 2 fix F-B2 pendiente).
- Comparación radial (distancia al vent), no 2D. PCC 0.4 vs 12km es inequívoco; gaps chicos requieren 2D.
- `by_key` toma nuestro max-vrp por pasada, pero el primary ya viene elegido con vent_anchored — NO es necesariamente nuestro máximo de escena. Para responder "¿detectamos algo a 12km que descartamos?" se requiere reproceso que guarde TODOS los clusters por escena (flag diagnóstico S87).

## Implicación para S87

Este es **EL experimento central de S87** (validación 1:1 anomalía dominante). Plan:

1. **Bloque 2** (fix loader): parsear distancia MIROVA CONS+OCR → comparación completa todos los vols.
2. **Reproceso con flag diagnóstico** que persista todos los clusters por escena → responder "¿detectamos la mayor pero la descartamos en la selección?".
3. **A/B criterio de selección**: `vent_anchored` (actual) vs `vrp_max_inner` (la mayor dentro del inner) vs mover ancla PCC al Cordón Caulle. Métrica: % de pasadas donde nuestra mayor = la mayor de MIROVA. Controles: Tupungatito (hoy 92%, no romper), Lascar (compacto), PCC (hoy 0%, arreglar).
4. **Cuidado** (experimento K): `vrp_max` puede empeorar el sobre-reporte de MAGNITUD per-vol. La selección de UBICACIÓN y el cálculo de MAGNITUD son problemas separados — el A/B debe medir ambos.

## Script

Inline en sesión S86 (no persistido como script standalone — re-derivable del bloque de arranque S87). El experimento formal S87 tendrá `script_L.py`.
