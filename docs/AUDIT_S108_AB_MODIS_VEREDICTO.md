# AUDIT_S108 — Veredicto (DEFINITIVO) del A/B fondo-local de magnitud MODIS

**Run**: 27480234385 (S107 §2). **Estado**: COMPLETO — 36/36 jobs success, 0 fallos
(6 vols × 3 brazos × 2 chunks). **Veredicto DEFINITIVO** (confirma el preliminar de 2 vols).

## Curación por volcán (inflados pc.vrp>5 → ≤5; det-diffs en granules COMUNES = C1)
| Vol | footprint (V-B) curados | ring (V-A) curados | det-diffs (C1) |
|---|---|---|---|
| Lascar (control) | 0/1 | 1/1 | 0 |
| Chaiten | 0/37 | 6/37 | 0 |
| Villarrica | 3/19 | 8/19 | 0 |
| PuyehueCordonCaulle | 1/27 | 7/27 | 0 |
| Tupungatito | 0/18 | 0/18 | 0 |
| Llaima | 1/9 | 1/9 | 0 |
| **TOTAL** | **5/111 (4%)** | **23/111 (20%)** | **0** |

Más records SUBEN que se curan (footprint 56 suben, ring 49). Tupungatito **0/18 en ambos**
(A19, ring glaciar). El brazo recomendado por el design (footprint V-B) es el PEOR (4%).

## Criterios A66 (pre-registrados)
| Criterio | Resultado | Detalle |
|---|---|---|
| **C1** detección 0-diffs | **PASS** (real) | 0 det-diffs en granules COMUNES (Chaiten/Lascar). El "FAIL" del audit script era 100% cobertura NASA distinta por corrida (only_base/only_on = 1-2 granules; cada brazo es un reproc separado). El fix es POST-selección, no toca detección. |
| **C3** Lascar control | **PASS** | mediana ON/base = 1.000 (n=252). El foco MODIS real (único con MIROVA-MODIS) se preserva. |
| **C2** inflados curados ≥85% | **REFUTADO** | footprint **5/111 (4%)**, ring **23/111 (20%)** — ambos << 85% (tabla por vol arriba). Más records suben que se curan. |

## Mecanismo de la refutación (por qué no cura — y a veces empeora)
El fix V-B/V-A recalcula `pc.vrp = coef × area × (L_cluster − L_bg_corona)`. El design
asumió que la corona del cluster (campo difuso MODIS 1km alrededor del cráter) sería MÁS
CALIENTE que el fondo regional → restaría más → bajaría la magnitud inflada. **El A/B
muestra lo OPUESTO en Chaiten/Villarrica**: la corona es MÁS FRÍA (o similar) que el fondo
regional → `L_bg_corona < L_bg_regional` → `ΔL` SUBE → `pc.vrp` SUBE (ej. Chaiten
18.59→21.59, 7.97→9.26 MW). `ratio_med ON/base = 1.000` (neutral para la mayoría;
inconsistente para los inflados). corona_degraded=0 (no es fallback).

Es el **mismo patrón A19** (Tupungatito refutó el kernel-bg per-pixel por el ring glaciar)
y el **patrón A66** (el fondo-local NO generaliza entre volcanes). El fix §2 (corona) es
otra variante de fondo-local que NO funciona para los inflados MODIS.

## Implicaciones
1. **§2 (magnitud fondo-local) REFUTADO** → NO adoptar V-B ni V-A. El flag queda OFF
   (no afectó producción; A45 cumplido). Descarte con datos (A26).
2. **§1 (flip ancla MODIS) BLOQUEADO**: estaba gateado por §2 para no destapar los ~84
   inflados como summit con magnitud inflada. Sin cura de magnitud, el flip los mostraría
   inflados (o empeorados) → NO activar.
3. **El frente MODIS** (curar el gap summit-gated recall 10.8% = D12 + la magnitud inflada)
   necesita **OTRO enfoque de magnitud** — el fondo-local de corona NO sirve. Candidatos a
   explorar (papers-first): cap de magnitud por umbral físico, co-validación cross-sensor
   (VIIRS confirma magnitud), o el método de selección de pixels del cluster (¿incluye
   campo difuso que no debería?).

## Notas (A62)
- DEFINITIVO: los 6 vols confirman la refutación (footprint 4%, ring 20% << 85%). PCC y
  Tupungatito —los que podrían haber diferido— también fallan (Tupun 0/18 en ambos brazos, A19).
- C1 del audit script cuenta la cobertura NASA como diff; el check de granules COMUNES da
  **0 det-diffs en los 6 vols** → C1 real PASS (el fix es POST-selección, no toca detección).
- C3 (Lascar) PASS en ambos brazos (foco MODIS-MIROVA real preservado).
