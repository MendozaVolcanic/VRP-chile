# S16 — Background annulus parity con bbox (pendiente)

> **No ejecutar en S15.** Requiere reproceso completo y puede introducir
> nuevos FPs. Dejar para S16 cuando haya ventana para validar empíricamente.

## Problema

Ampliamos el ROI de `dist <= radius_km` (círculo 25 km) a bbox 50×50 km
(±25 km) en S15 Tema E. Pero el background annulus siguió con
`BG_INNER_KM=5, BG_OUTER_KM=25` (anillo circular).

Consecuencia: pixels scene a 28-35 km (esquinas del bbox, ej. Llaima
Conguillío lake a 28 km NE) caen **dentro del ROI** pero **fuera del
annulus** que calcula `t_bg`. El threshold efectivo se distorsiona
porque el pixel lejano se compara contra un background de zona distinta.

Evidencia S15 2026-04-22: Llaima abril recall 0/17 pese a bbox. Agent
forense confirmó hipótesis annulus mismatch.

## Fix propuesto

Opción A (simple): ampliar `BG_OUTER_KM: 25 → 35` en profiles.

Opción B (preciso): annulus bbox también (`5 ≤ |lat|, |lon| ≤ 35` en km).

## Riesgos conocidos

1. **Contaminación por volcanes vecinos**: Lonquimay a 30 km del Llaima
   entraría al annulus Llaima. σ_bg podría inflarse si Lonquimay tiene
   actividad térmica simultánea.
2. **Cambio de t_bg baseline**: todos los volcanes recalcularían t_bg
   con datos distintos → FPs/FNs podrían desplazarse.
3. **Reproceso completo requerido**: ~8 horas para los 11 volcanes Tier A.

## Validación necesaria antes de aprobar

1. TDD: tests sintéticos de annulus ampliado.
2. Reproceso comparativo S15 bbox-only vs S15 bbox+annulus.
3. Crossmatch delta: si Llaima recall sube a >0.40 sin regresar otros
   volcanes, aprobar.
4. Sanity check volcanes cercanos geograficamente (Lonquimay vs Llaima,
   Michinmahuida vs Chaitén).

## Referencia

- Agent diagnosis: `a6e879336d840c91b` Llaima forense 2026-04-22 S15.
- Commit bbox S15: `9df6bd7`.
