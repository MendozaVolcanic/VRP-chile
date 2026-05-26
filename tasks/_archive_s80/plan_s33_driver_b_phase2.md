# Plan S33 — Driver B Phase 2 (filtro dual-ROI sobre Path D dNTI)

> Continuación natural de Driver B Phase 1 validado en S32 P2. No bloquea
> adopción Phase 1 operacional.

## Contexto

Driver B Phase 1 (S32 commit `0d8f0b5`) aplica filtro dual-ROI 5σ summit /
10σ scene pixel-level sobre `test1_hot` antes de sumar VRP. Validado A/B:
recall paridad (74.4 → 73.6%), ratio mediano 2.52 → 1.66×.

Pero Chaiten (14.5×) y PCC (11.9×) siguen altos post-fix. Análisis
`experiments/70_chaiten_pcc_post_fix_paths.py`: el path dominante NO es
Test 1 filtrado, sino **Path D dNTI contextual** que aporta hasta 667
pixels marginales por record sin filtro N·σ pixel-level.

## Hipótesis

Path D usa C1 absoluto (0.003 summit / 0.010 scene, Coppola 2016a SP 426.5).
Pixels que pasan dNTI > median_8_vecinos + C1 entran al cluster sin
verificar BT individual contra 5σ summit. Inflan magnitud cuando hay
heterogeneidad NTI background sin señal térmica fuerte (background
noise en NTI con BT casi-bg).

## Plan Phase 2

### Opción A — Filtro 5σ aplicado a hot_mask final combinado

Más limpio metodológicamente. Después del OR de todas las paths
(eruption_hotspot + test1_hot + dnti_ctx + nti_path...), aplicar el filtro
dual-ROI 5σ summit / 10σ scene como gate final. Cualquier pixel del cluster
reportado debe superar ese threshold de magnitud absoluta.

Pros: simple, una sola pasada de filtro, garantiza coherencia.
Contras: puede afectar Test 1 (que ya filtra Phase 1) doblemente.

### Opción B — Filtro específico al dnti_ctx_hot mask

Análogo a Phase 1: cuando se calcula `dnti_ctx_hot` o `dual_roi_dnti_hot`,
intersectar con `dual_roi_bt_threshold` antes de OR-earlo al hot_mask.

Pros: consistencia con Phase 1 (cada path se filtra por separado).
Contras: más código duplicado, mantenimiento.

### Recomendación

**Opción A** — Filtro final al hot_mask combinado. Refactoriza Phase 1
(test1_hot ya no necesita filtro propio porque caería en el final). Más
limpio.

## Caveats

1. **PCC inner_radius=20km lacolito**: el "summit" es muy generoso,
   filtro 5σ summit aplicable a clusters a 7-9km del centro. Coppola
   2016a Tabla 1 dice 5σ noche para summit, 10σ noche para scene.
   PCC podría requerir su propio inner_radius_km efectivo más estricto
   (5km) para el filtro pixel-level, distinto del visual classification
   (20km). Decidir si introducir parámetro `inner_radius_pixel_filter_km`
   separado.

2. **Riesgo regresión Lastarria/Villarrica**: Phase 1 dio Lastarria 6.5×
   y Villarrica 2.2× con flag ON. Phase 2 debería mantener o mejorar
   esos números. A/B test obligatorio antes de adoptar.

3. **Pisos VRP por sensor** (`min_vrp_mw_*`): el filtro Phase 2 puede
   reducir VRP a sub-piso → record marcado como no-detección. Verificar
   que recall no caiga por interacción Phase 2 + pisos.

## Pasos S33

1. Implementar Opción A: nuevo flag `enable_final_pixel_filter` en
   profile.py + profile yaml. Aplicar `dual_roi_bt_threshold` a
   `hot_mask` antes de calcular VRP.
2. Tests unitarios sintéticos similares a Phase 1.
3. Profile A/B `mirova_equivalent_test1pix_phase2.yaml` con Phase 1 + 2.
4. Workflow A/B reproc 11 Tier A 90d.
5. Audit comparativo Phase 1 vs Phase 2.
6. Si Phase 2 mejora Chaiten/PCC sin destruir otros volcanes, adoptar.

## Criterios de éxito

- Recall global ≥73% (baseline Phase 1).
- Ratio Chaiten ≤5× (vs 14.5× Phase 1).
- Ratio PCC ≤8× (vs 11.9× Phase 1).
- Lastarria/Villarrica/Planchón mantienen ratios Phase 1.

## Anti-patrones a evitar

- **No subir N·σ summit ad-hoc** para PCC. Si necesita 7σ en lugar de 5σ,
  documentarlo como caso especial paramétrico, no parche silencioso.
- **No sumar filtros geográficos** (radio físico hard-cap, exclude_zones)
  que MISSION.md prohíbe. Si filtro pixel-level no alcanza, es señal de
  método MIROVA no replicado, no de necesidad de parche.
