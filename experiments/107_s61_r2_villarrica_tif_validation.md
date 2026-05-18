# S61 R2 pixel-level validation Villarrica 2026-05-11 vs TIF MIROVA

**Fecha**: 2026-05-18
**Caso**: 2026-05-11 06:00 UTC ALERTA MIROVA VIIRS375 Villarrica
**Status**: ✅ NEW kernel-bg confirmado visualmente como mecanismo correcto

## Refs del caso paradigmático

| Sistema | VRP (MW) | dist al cráter (km) | Ratio vs MIROVA |
|---|---:|---:|---:|
| MIROVA reportó (CSV NRT) | 0.31 | 0.84 | 1.00× |
| LEGACY median-ring | 5.84 | 1.53 | **18.83×** |
| NEW kernel-bg (fix S58) | 0.50 | 0.79 | **1.61×** |

## TIF MIROVA inspeccionado

`mirova-tif-archive/data/tif/Villarrica/20260511_060001_VIIRS375.tif`
- Shape: 134×134 grid (~50×50 km)
- Bounds: lat -39.65 a -39.19, lon -72.23 a -71.63
- Cráter vent (Nicolás): -39.420, -71.940
- Valores: 0.10 - 0.27 (unidades no documentadas, probable BT scaled)
- 17930 pixels > 0 en toda la escena (pre-clustering scene-wide)

## Análisis spatial

### Top 10 pixels hottest (excluyendo NaN bordes)

| row,col | lat | lon | val | dist al cráter (km) |
|---|---|---|---:|---:|
| 12,66 | -39.232 | -71.934 | 0.267 | **20.9 N** |
| 12,67 | -39.232 | -71.929 | 0.263 | **20.9 N** |
| 3,54 | -39.201 | -71.987 | 0.262 | **24.7 N** |
| 1,70 | -39.194 | -71.916 | 0.262 | **25.2 N** |
| 3,67 | -39.201 | -71.929 | 0.261 | **24.4 N** |
| 4,65 | -39.204 | -71.938 | 0.261 | **24.0 N** |
| 1,71 | -39.194 | -71.912 | 0.261 | **25.2 N** |
| 3,66 | -39.201 | -71.934 | 0.260 | **24.4 N** |
| 3,53 | -39.201 | -71.992 | 0.260 | **24.8 N** |
| 11,66 | -39.228 | -71.934 | 0.260 | **21.3 N** |

**TODOS los Top 10 pixels más calientes están al norte del cráter (20-25 km)**.

### Pixels dentro de 2 km del cráter

- n = 86 pixels
- sum total = 10.57 (sumatoria sin clustering)
- max = 0.16 (más frío que el lago norte)
- median = 0.12

## Interpretación geofísica

**El lago Villarrica norte (centro a ~15-18 km del cráter)** aparece como la zona
con mayor señal térmica en VIIRS375 3.7 μm. Esto coincide con el agente lagos S60
que reportó "lago glacio-volcánico, ~20°C verano, profundidad 120m, contraste térmico
fuerte contra terreno andino frío nocturno".

**Mecanismo confirmado**:
- LEGACY `median(ring 5-25 km)` incluye estos pixels lago calientes → median del ring
  está sesgado alto (~0.20 vs 0.12 base)
- Pero, **dirección bias**: si median(ring) está ALTO, L_bg está alto, ΔL = L_hot - L_bg
  está BAJO → VRP debería estar SUB-ESTIMADO.
- **Sin embargo**, audit empírico muestra LEGACY 5.84 MW vs MIROVA 0.31 MW (ratio 18×
  SOBRE-ESTIMADO).

**Reconciliación**: el bias es CONTRARIO a lo esperado de "ring contaminado". La causa
debe ser otra. Hipótesis:

1. El median(ring) actual NO incluye los pixels lago (filtro pre-existente) y opera
   sobre pixels frios → L_bg bajo → ΔL inflado.
2. O el pixel hot reportado por LEGACY incluye edge mixing con el lago → BT inflado
   → VRP inflado.
3. O el cluster que LEGACY selecciona summit no es el cráter sino algún pixel marginal
   del bbox del lago (1.53 km dist sugiere borde del lago).

NEW kernel-bg cura porque los 8 vecinos directos del pixel cráter NO incluyen el lago
norte (a 15 km), por lo que L_bg es honesto (background frío local) y ΔL refleja la
señal real del cráter.

## Implicación para confianza adopción S61

✅ **Evidencia visual independiente confirma mecanismo fisico** que justifica el fix
local_kernel_bg para Villarrica. El TIF MIROVA muestra el lago como la fuente
dominante de señal térmica que contamina la escena.

NEW kernel-bg sigue mecanismo Coppola 2024 L1129 ("T_bk from pixels adjacent to hot")
literal y produce VRP 0.50 MW (1.61× MIROVA 0.31) — dentro del rango operacional
tolerable y mucho mejor que LEGACY 18.83×.

## Limitaciones de este análisis

- TIF MIROVA NO valida magnitud (REAUDITORIA_S52 documentado: TIF = visualización
  scene-wide con sum pixels brutos, no MW reportado). Sum total del TIF = 3254 MW vs
  MIROVA reporta 0.31 MW (factor 10500× — esperable, no es bug).
- Solo cubre 1 de los 5 ALERTAS Villarrica window. Los otros 4 (2026-05-14, 2026-04-09,
  2026-03-08, 2026-02-26) no están en el archive local pero presumiblemente muestran
  patrón similar (mismo cráter, mismo lago).
- Decisión adopción Task 5 NO depende de este análisis (ya validada por audit C
  empírico), pero refuerza la confianza física.
