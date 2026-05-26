# P3.1 — Dual-ROI thresholds Implementation Plan (skeleton)

> **Ejecutar DESPUES de validar P3.2**. Si delta report P3.2 muestra Lastarria
> ratio mediano <3 y recall global >=0.23, arrancar este plan.

**Goal:** Implementar dual-ROI per-pixel threshold (Coppola 2016a SP 426.5): summit
vs scene con umbrales distintos. En ROI1 summit (5 km del vent) umbrales sensibles
C1=0.003 / C2=5σ (MIROVA para dNTI); en ROI2 scene (resto 25 km) estrictos
C1=0.010 / C2=10σ. Objetivo: cortar los FPs lejanos que infla el perfil actual
con umbrales uniformes.

**Baseline esperado al arrancar** (depende de P3.2): Chaitén precision ~0.0
(60 FP, 0 TP) debe subir mucho. Chaitén tiene 14 AT en summit (dist <=5 km) y
~60 detecciones pre-P3 eran todas lejanas -> scene con umbral estricto las mata.

**Architecture:** 
- Nueva variante del helper `contextual_dnti_hot_mask` que acepta un mapa
  de C1 per-pixel (o dos mascaras summit/scene separadas).
- En cada procesador: computar `dist_per_pixel` (ya existe como parte del cálculo
  del `vent_dist_for_p95` en process_modis/viirs_mod), crear summit_mask
  (dist <= 5 km) y scene_mask (5 < dist <= 25 km), aplicar helper 2 veces con
  C1 distintos y OR.

**Tech Stack:** numpy + existente. No dependencias nuevas.

---

## Task 1: Extender helper o agregar wrapper

**Files:**
- Modify: `pipeline/detection_context.py`
- Test: `tests/test_detection_context.py` (agregar casos)

Decision: agregar una funcion wrapper `dual_roi_contextual_dnti_hot_mask` que
delega en `contextual_dnti_hot_mask` dos veces (summit y scene) con C1 distintos
y OR. Deja el helper original como primitiva reusable.

```python
def dual_roi_contextual_dnti_hot_mask(
    nti, bt, roi_mask, dist_km, t_bg,
    c1_summit, c1_scene, inner_km, bt_sanity_k,
) -> np.ndarray:
    summit_mask = roi_mask & (dist_km <= inner_km)
    scene_mask = roi_mask & (dist_km > inner_km)
    hot_summit = contextual_dnti_hot_mask(
        nti, bt, summit_mask, t_bg, c1_summit, bt_sanity_k)
    hot_scene = contextual_dnti_hot_mask(
        nti, bt, scene_mask, t_bg, c1_scene, bt_sanity_k)
    return hot_summit | hot_scene
```

Test nuevo: verificar que pixel a 10 km del vent con dNTI=0.005 pasa summit
(si inner=15) pero falla scene (con c1_scene=0.010).

## Task 2: Profile keys

- `dnti_contextual_c1_summit: 0.003` (ya existe como `dnti_contextual_c1`,
  renombrar con fallback).
- `dnti_contextual_c1_scene: 0.010` (nuevo).
- `enable_dnti_dual_roi: true` en mirova_equivalent (inicia false en experimental).

## Task 3-5: Integrar en los 3 procesadores

Patron: donde hoy esta `contextual_dnti_hot_mask(...)`, sustituir por:

```python
if ENABLE_DNTI_DUAL_ROI:
    dnti_ctx_hot = dual_roi_contextual_dnti_hot_mask(
        nti=nti, bt=bt, roi_mask=roi_mask,
        dist_km=dist_from_center_per_pixel,
        t_bg=t_bg,
        c1_summit=DNTI_CONTEXTUAL_C1_SUMMIT,
        c1_scene=DNTI_CONTEXTUAL_C1_SCENE,
        inner_km=inner_radius_km,   # ya pasado como arg a calculate_vrp
        bt_sanity_k=NTI_BT_SANITY_K,
    )
```

Detalles por procesador:
- **process_viirs.py**: `dist_from_center_per_pixel` se puede derivar de
  `haversine_km(vent_lat, vent_lon, lat, lon)` aplicado al array per-pixel.
  Ya existe implicitamente para vent-path; exponer a nivel funcion.
- **process_viirs_mod.py**: idem, ya existe `vent_dist_for_p95` como array
  (line ~264).
- **process_modis.py**: idem, ya existe `vent_dist_for_p95` (line ~259).

## Task 4a (checkpoint): reproceso + crossmatch delta

Script `experiments/31_p31_delta_report.py` clon de `30_p32_delta_report.py`
pero comparando post-P3.2 vs post-P3.1.

Criterio aceptacion P3.1:
- Chaiten precision >= 0.40 (desde 0.0 pre-P3.2, con P3.2 indeterminado).
- FP totales globales bajan >=30% sin perder mas de 5pp de recall.
- Lascar ratio mediano permanece en [1.10, 1.30] (canary no regresa).

## Task 5 (opcional): BT path tambien dual-ROI

P3.1 puede extenderse al Path A (BT-sigma): N_SIGMA=3 en summit, N_SIGMA=5-10
en scene. Evaluar tras P3.1 basico. Si los FPs lejanos no caen suficiente
con solo dNTI dual-ROI, agregar este.

---

## Notas metodologicas

1. **P3.1 es multiplicativo con P3.2**. Sin P3.2, dual-ROI solo no arregla
   Lastarria (sobreestim por terreno heterogeneo, independiente de distancia).
   Con P3.2 + P3.1: summit sensible + scene estricto = cura completa.

2. **inner_radius_km ya es por-volcan**. Cada volcan tiene su KML oficial
   (Lascar=5, Lastarria=3, PCC=20). Dual-ROI usa ese mismo valor — no hace falta
   parametros nuevos de geometria.

3. **Riesgo**: para PCC `inner_radius=20`, casi toda la escena 25 km es summit.
   Scene ROI es solo anillo 20-25 km. Pocos pixels, poco impacto. OK — PCC ya
   tiene buena precision, no necesita scene estricto.

4. **Tupungatito/PP**: con mirova_center ya fijado (Fase 0.7), la distancia
   per-pixel queda alineada con MIROVA. Dual-ROI va a funcionar ahi.

---

## Referencias

- Coppola et al. 2016 SP 426.5 "An enhanced automated thermal anomaly
  detection algorithm" — seccion Dual-ROI thresholds, Table 2.
- Nuestro commit P3.2: `b0ba72b` (process_modis), `f24f683` (viirs_mod),
  `885ac02` (viirs).
- Baseline pre-P3: `memory/project_baseline_pre_p3_s15.md`.
