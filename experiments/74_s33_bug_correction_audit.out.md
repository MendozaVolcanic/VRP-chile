# S33 Bug Fix — Driver B Phase 1 reaudit con métrica corregida

## Contexto del bug

`mirovaEqVrp(r)` tenía un bug: chequeaba `distance_class === "summit"` pero
NO validaba `primary_cluster.centroid_dist_km <= inner_radius_km`.

Caso patológico (Lascar 2026-02-14 MODIS_TERRA):
- `distance_class = "summit"` (calculado con final_hotspot_dist_km — Test 1
  centroide cerca del vent).
- `primary_cluster.centroid_dist_km = 24.17 km` (cluster Salar Atacama).
- `primary_cluster.vrp_mw = 19389.8 MW` (sumando pixels Salar caliente).

Resultado pre-fix: `mirovaEqVrp` devolvía 19389 MW como si fuera VRP del
cráter. Idéntico bug en `experiments/65_audit_ab_test1pix_filter.py`.

## Implicación: Driver B Phase 1 audit estaba contaminado

Audit pre-fix (commit `0d8f0b5` adopción operacional):
- Driver A solo: ratio 6.25× (suma vrp_mw global)
- Driver A summit-only: ratio 2.29× (cluster contiguo summit)
- Driver A + Phase 1: ratio 1.66×, recall 73.6%

Audit post-fix S33 (con validación pc_dist):

| Métrica | Driver A solo (filter OFF) | Driver A + Phase 1 (filter ON) | Δ |
|---|---:|---:|---:|
| Recall global | 74.2% | **55.6%** | **−18.6pp** |
| Ratio mediano | 2.53× | 1.39× | −45% |

| Volcán | OFF recall | ON recall | Δ |
|---|---:|---:|---:|
| Lastarria | 100% | 42.9% | **−57pp** |
| Villarrica | 100% | 33.3% | **−67pp** |
| Planchón | 96.8% | 12.9% | **−84pp** |
| Lascar | 65.2% | 56.2% | −9pp |
| Tupungatito | 48.5% | 36.8% | −12pp |
| Isluga | 77.9% | 69.1% | −9pp |

## Diagnóstico físico

Driver B Phase 1 aplica filtro 5σ summit a la mask Test 1 antes del cluster.
Ese filtro elimina pixels marginales. Pero esos pixels marginales SÍ formaban
el cluster contiguo del cráter (8-conn pixel-vecindad) en Lastarria, Villarrica,
Planchón. Sin ellos:
- El cluster contiguo Test1 se rompe.
- El "primary_cluster" reportado cae al siguiente cluster mayor, que es del
  Salar/lago lejano.
- Con bug S33 dist_class='summit' (final_hotspot Test1 sigue cerca), el
  cluster del Salar contaba como TP con magnitud falsa.
- Sin bug S33: cluster del Salar correctamente clasifica far-vrp=0 → FN.

## Conclusión

**Driver B Phase 1 destruye recall real cuando se mide correctamente**.
El "audit aprobado" del adopción S32 estaba contaminado por bug S33.

## Acciones pendientes

1. **Revertir adopción Driver B Phase 1** en `pipeline/profiles/mirova_equivalent.yaml`:
   `enable_test1_pixel_filter: true` → `false`.
2. **Reproc operacional** con flag OFF para sustituir data actual (que tiene
   Phase 1 ON por adopción S32).
3. **Mantener Driver A frontend con fix S33** — esa parte sigue siendo
   correcta y necesaria.
4. **Esperar audit D4** (corriendo). D4 es más permisivo (L_bg global), tiene
   chance de recuperar Tupungatito sin destruir Lastarria/Villarrica/Planchón.
5. **Documentar lección**: el bug del frontend `mirovaEqVrp` ocultó el verdadero
   costo de Driver B Phase 1 durante todo S32. Validación A/B sin verificación
   pixel-level adicional fue insuficiente.

## Commits relevantes

- Bug S33 introducido: commit `c30e2de` (S32 P2 Driver A frontend).
- Bug en audit Python: `experiments/65_audit_ab_test1pix_filter.py`.
- Fix S33: este commit (mirovaEqVrp recibe innerKm + valida pc_dist).
