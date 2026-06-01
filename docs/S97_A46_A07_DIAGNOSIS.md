# S97 — Diagnóstico raíz A46/A07: ya estaba reparado por #294

**Sesión S97 (2026-05-31).** `superpowers-systematic-debugging`. Conclusión central:
**la "raíz A46/A07" que el arranque S97 mandaba reparar YA está reparada en el código
por el PR #294 (S94).** Lo que vimos en S96 era **data stale** (lección A50), no un bug
del código actual. No hace falta un fix nuevo de pipeline para el gap A07.

## Cómo se llegó (evidencia, no opinión)

### 1. Lectura del código (`pipeline/process_viirs.py:1465-1525`, `anomaly_pixels.py`)
El path Test1, desde #294, reasigna `anomaly_pixels = build_anomaly_pixels(t1_vrp_2d, ...)`
(línea 1486) **dentro del mismo bloque** que construye el cluster
(`cluster_hotspots(test1_hot_filtered, vrp_per_pixel=t1_vrp_2d, ...)`). `build_anomaly_pixels`
devuelve **todos** los píxeles con `t1_vrp_2d > 0` (top-100). El cluster es subconjunto
espacial de esos píxeles → `anomaly_pixels ⊇ cluster`. No son grids distintos.

### 2. Prueba controlada (mismo granule, distinto código)
Comparando el **mismo** record entre data live (pre-#294) y `data/_s94_reproc_viirs` (post-#294):

| Granule PP 2026-05-29 | LIVE (pre-#294) | REPRO (post-#294) |
|---|---|---|
| 05:00 SNPP | pc 5px/0.103 MW · **n_ap=0** | pc 5px/0.103 MW · **n_ap=47, Σ=1.333** (1.9–4.1 km del cráter) |
| 06:42 SNPP | pc 1px/0.01 · n_ap=1 | pc 1px/0.01 · **n_ap=51, Σ=2.0** |

Mismo input, misma detección (`pc.vrp_mw` idéntico — #294 es aditivo), pero `anomaly_pixels`
0→47 y 1→51. **#294 repara el gap A07.**

### 3. Datación
- #294 (`6c93b3c6`) mergeó a `main` el **2026-05-31 12:20 -04**.
- Todos los records Test1 V375 de la data live llegan hasta **2026-05-30** → anteriores a #294.
- Por eso tienen `anomaly_pixels` ralo: vienen del path normal viejo (scene-wide, incluye
  fuentes lejanas/incendios), no del grid Test1.

## El "anomaly sin resolver" del arranque, explicado
PP 2026-05-30 06:24 live: `pc.vrp_mw=0.819` (19px @1.9km, cráter) pero `anomaly_pixels`=3
(los 2 de mayor VRP a 19 km = incendios). En el **código viejo** `primary_cluster` (cluster
Test1) y `anomaly_pixels` (path normal eruption/vent) SÍ salían de paths distintos → de ahí
la incoherencia. #294 los unificó. La observación de S96 era correcta sobre el record stale;
la conclusión "hace falta fix nuevo" no, porque #294 (mergeado DESPUÉS de ese record) ya lo
resolvió.

## Alcance de la data stale (live, 2026-05-31)
983/4603 (21.4%) records Test1 V375 en los 11 Tier A live tienen `anomaly_pixels` vacío.
Peores: Tupungatito 190, Villarrica 180, Chaitén 126, PP 104, Copahue 98. Son los sub-píxel
que F5' busca curar. **Se curan reprocesando la data live con el código actual** (no con
código nuevo).

## Edge-case residual en reproc (NO es bug A07)
118/1112 (10.6%) records Test1 V375 en la data reproc tienen `anomaly_pixels` vacío, todos
con **`pc_vrp = 0.0`** (NdC 86, Lastarria 20, Lascar 12). Firma: cluster de N píxeles
contiguos (test1_hot_filtered marcó por NTI/BT) pero su exceso de radiancia MIR sobre el
fondo da cero (campo frío) → `t1_vrp_2d` todo en 0 → `build_anomaly_pixels` devuelve []
**correctamente** y `pc.vrp_mw=0.0`. Son detecciones de energía cero; para F5' display
muestran 0 en cualquier modo (Cluster o Núcleo). No requieren acción. (Si acaso, se vinculan
a la discusión campo-frío/cirrus A23 de NdC, fuera del scope F5'.)

## Verificación A2 (staging vs live, ventana mayo, antes de reproc completo)

`experiments/_s97_audit/verify_staging_vs_live.py` corre la métrica F5' (Núcleo vs
Cluster vs MIROVA, VIIRS375 ±60min) parametrizando el dir de data, misma ventana
(2026-05-01→05-29):

| | LIVE (código viejo) | STAGING (#294/#297) |
|---|---|---|
| Fallback F5' (Núcleo>0 cae al cluster) | 30% (129/435) | **0%** (0/425) |
| Tupungatito fallback | 92% | 0% |
| Villarrica fallback | 73% | 0% |
| Planchón fallback | 48% | 0% |
| Regresiones (detección borrada) | 0 | **0** |
| Villarrica Núcleo/MIROVA | 10.60× (no curaba) | **2.07×** |
| Tupungatito Núcleo/MIROVA | 14.27× | **2.52×** |
| Cluster global/MIROVA (vista default) | 1.32× | **1.14×** |

**Conclusión**: reprocesar con el código actual (a) elimina el fallback F5' (el Núcleo
recompone la magnitud del lava lake/halo glaciar), (b) **0 detecciones perdidas**, (c)
limpia la deuda de magnitud A18 también en la vista Cluster por defecto. Luz verde para
escalar al rango completo. Outputs: `experiments/_s97_audit/out_{live,staging}_may.txt`.

## Implicación para el plan S97
- **§1 (reparar raíz con fix de pipeline nuevo)**: NO necesario. El código ya está bien.
- **Acción real**: reprocesar la data LIVE operacional con el código actual para que el fix
  #294 llegue al dashboard, y re-correr `experiments/_s96_audit/f5_display_vs_mirova.py`
  sobre data fresca → el % de fallback debe caer de 21% a ~10% (solo quedan los pc_vrp=0).
- Reproc de historia = **local** (regla S15, GH Actions timeout). A47: secuencial por volcán.
