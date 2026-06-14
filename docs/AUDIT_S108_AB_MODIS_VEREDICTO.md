# AUDIT_S108 — Veredicto (PARCIAL) del A/B fondo-local de magnitud MODIS

**Run**: 27480234385 (S107 §2, disparado 2026-06-13). **Estado**: parcial — completos
**Chaiten** (37 inflados) + **Lascar** (control); **Villarrica** parcial (footprint chunk1).
Faltan PCC/Tupungatito/Llaima (A/B lento ~12h total; Villarrica/PCC ~150 min c/u).
**Veredicto preliminar con señal decisiva en 2 vols con inflados.**

## Criterios A66 (pre-registrados)
| Criterio | Resultado | Detalle |
|---|---|---|
| **C1** detección 0-diffs | **PASS** (real) | 0 det-diffs en granules COMUNES (Chaiten/Lascar). El "FAIL" del audit script era 100% cobertura NASA distinta por corrida (only_base/only_on = 1-2 granules; cada brazo es un reproc separado). El fix es POST-selección, no toca detección. |
| **C3** Lascar control | **PASS** | mediana ON/base = 1.000 (n=252). El foco MODIS real (único con MIROVA-MODIS) se preserva. |
| **C2** inflados curados ≥85% | **REFUTADO** | Chaiten footprint **0/37 curados** (20 SUBIERON); ring 6/37 (15 subieron). Villarrica footprint 2/11 (4 subieron). Muy por debajo del 85%. |

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

## Caveats (A62)
- Parcial: faltan PCC/Tupungatito/Llaima. PCC (cirrus D9) y Tupun (glaciar) podrían diferir,
  pero el fix ya falló en 2 vols representativos (Chaiten boscoso + Villarrica nevado) y el
  mecanismo (corona vs fondo regional) es general. Confirmar con el A/B completo.
- C1 del audit script cuenta cobertura como diff — usar el check de granules comunes
  (`0 det-diffs`) como C1 real.
