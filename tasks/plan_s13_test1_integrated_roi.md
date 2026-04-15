# Plan S13 — Test 1 Integrado-ROI (Coppola 2015 Eq.1)

**Objetivo:** resolver el gap arquitectural donde nuestro método per-pixel
pierde detecciones que MIROVA sí captura, específicamente:

- **Villarrica 0% recall** (6 refs MIROVA, todas NTI-only visuales).
- **Sub-umbral real** en Chaitén/Tupungatito/Lastarria/PCC (el domo/lava
  lake emite continuo pero nuestro pixel-max no siempre dispara).

## Referencia metodológica

Coppola, D. et al. (2015). **MIROVA: a new hotspot detection system based on
MODIS Level 1B data.** *Bulletin of Volcanology* 77:55. DOI 10.1007/s00445-015-0953-8.

### Test 1 — integrated-ROI MIR (fórmula 1 del paper, §2.2)

Para una noche-overpass dada, sobre una ROI cuadrada de `2·R×2·R` pixels
centrada en el cráter (típicamente 6×6 km para MODIS, 6×6 km para
VIIRS 375m ≈ 16×16 pixels):

```
1. L_MIR(i,j) = radiancia MIR [W/m²/sr/μm] del pixel (i,j) en la ROI.
2. L_bg_MIR  = mediana L_MIR(ROI \ ventana_central)
              — anillo que excluye el centro donde está el crater.
3. σ_bg_MIR  = MAD·1.4826 de L_MIR en el mismo anillo.
4. ΔL_ROI = Σ_{i,j ∈ ROI} max(0, L_MIR(i,j) − L_bg_MIR)
           — exceso integrado sobre toda la ROI (solo pixeles por
             encima del background).
5. σ_ΔL_ROI = σ_bg_MIR · sqrt(N_ROI_pixels)
             — propagación de error, integrar N pixeles reduce ruido
               por sqrt(N).
6. criterio:   ΔL_ROI > K_Test1 · σ_ΔL_ROI          (K_Test1 = 3 en MIROVA)
               AND
               ΔL_ROI / L_bg_MIR > MIR_relative     (MIR_rel = 0.02 en MIROVA)
```

**Por qué detecta lo que per-pixel no:** un pixel caliente sub-pixel produce
ΔL individual pequeño (apenas 1% de L_bg). Per-pixel exige ese pixel supere
3σ local (σ de 1 pixel). Integrado junta el exceso de TODOS los pixeles de
la ROI y compara contra σ integrado (que baja por sqrt(N)). Un pico de
0.5σ en 10 pixeles contiguos suma 5σ integrado. Captura señales
espacialmente extendidas de baja amplitud que MIROVA clasifica NTI-only.

### VRP desde Test 1

Si Test 1 dispara, VRP se computa con la misma fórmula Wooster:

```
VRP_ROI = 18.9 · Σ A_pix(i,j) · ΔL_MIR(i,j)    [W]
         para (i,j) con L_MIR > L_bg_MIR en la ROI.
```

**Nota importante:** el VRP no es per-pixel max sino suma del exceso
sobre la ROI. Para Villarrica donde el hotspot es 1 pixel sub-pixel,
VRP_ROI ≈ VRP_pixel. Para emisiones extendidas (plumas, flujos de lava)
VRP_ROI >> VRP_pixel y es el número correcto.

## Plan de implementación

### Fase 1: prototipo offline (1-2 h)

Script `experiments/15_test1_integrated_prototype.py`:

1. Cargar un granule Villarrica para una de las 6 noches MIROVA.
2. Construir la ROI 16×16 pixels centrada en vent_lat/lon.
3. Computar L_MIR usando Planck inversa desde BT I04 (para VIIRS 375m).
4. Calcular L_bg_MIR + σ_bg_MIR sobre el anillo externo.
5. Aplicar el criterio integrado.
6. Verificar: ¿dispara en las 6 noches Villarrica donde MIROVA detectó?
7. Verificar: ¿no dispara en 10-20 noches aleatorias sin actividad?

**Criterio de éxito de la fase:** ≥4 de 6 refs Villarrica disparan, ≤10%
FPR en muestra aleatoria.

### Fase 2: integración al pipeline (2-3 h)

1. **Nuevo módulo** `pipeline/test1_integrated.py`:
   - Función pura: `compute_test1(bt_2d, lat_2d, lon_2d, vent_lat, vent_lon,
     roi_km, lambda_mir, k_sigma, mir_rel_threshold) → dict`.
   - Retorna: `{ triggered: bool, vrp_roi_mw, delta_l, sigma_delta_l,
     n_pixels_contributing, centroid_lat, centroid_lon }`.
   - Sin side-effects. Testeable con fixtures.

2. **Integrar en process_viirs.py** como cuarto path (ENABLE_TEST1_PATH):
   - Se ejecuta **después** del BT-path, NTI-path y vent-path.
   - Si dispara, agrega `vrp_test1_mw` y campo diagnóstico `n_test1_pixels`.
   - Store.py incluye test1 en el `max(eruption, vent, test1)` → `vrp_mw`.

3. **Agregar parámetros al profile**:
   - `test1_k_sigma: 3.0` (MIROVA default)
   - `test1_mir_relative: 0.02` (MIROVA default)
   - `test1_roi_km: 3.0` (radio ROI)
   - `enable_test1_path: true` en `mirova_equivalent`

4. **Mismo patrón para MODIS** (process_modis.py) y **VIIRS 750m**
   (process_viirs_mod.py) usando las bandas MIR correspondientes.

### Fase 3: validación (1 h)

1. Reproceso completo Villarrica con Test 1 activado.
2. Auditoría: recall debe subir de 0% a ≥67% (4/6 refs).
3. Auditoría lateral Lascar/PCC/Chaitén: recall no debe caer,
   precision no debe deteriorarse >10%.
4. Si ambas se cumplen → activamos en `mirova_equivalent`.
5. Si recall Villarrica ≥4/6 pero Lascar precision cae: movemos a
   `experimental` solamente.

### Fase 4: rollout (30 min)

1. Activar `enable_test1_path: true` en ambos perfiles.
2. Reproceso batch de los 11 volcanes Tier A/B/C.
3. Publicar en dashboard con leyenda nueva (Test 1 como 4ª ruta).
4. Documentar en `tasks/lessons.md` L13.1.

## Riesgos conocidos y mitigaciones

### R1: duplicación con eruption-path
Si el eruption-path dispara para un pixel hot fuerte (dT=8 K) Y el Test 1
también, el VRP unificado toma el max. Ambos detectan el mismo fenómeno
— no es duplicación, es corroboración. **Mitigación:** trackear qué path
disparó con flags (`n_test1_pixels`, `n_bt_path`, etc.) para auditoría.

### R2: FPs por bg inhomogéneo
Si el anillo de fondo incluye features calientes no-volcánicos
(laguna al sol residual, asentamiento), σ_bg se infla y el umbral sube
→ menos detecciones. Pero si el feature cae DENTRO de la ROI, aparece
como "excess" ficticio. **Mitigación:** validar contra lista de features
no-volcánicos por volcán (Chaitén: pueblo; PCC: lago Puyehue).

### R3: tamaño ROI incorrecto
ROI muy grande promedia diluye señal (σ_integrado cede por sqrt(N)
pero ΔL_ROI también se diluye si la anomalía está concentrada).
ROI muy pequeño pierde el beneficio integrado.
**Mitigación:** probar 3, 4, 5 km en prototipo para cada volcán.
MIROVA usa 3 km para volcanes puntuales.

### R4: VIIRS 375 vs MODIS 1km geometría distinta
VIIRS 375m: 16×16 pixels para ROI de 3 km. MODIS 1km: 6×6 pixels.
**Mitigación:** mismo algoritmo, sólo cambia el conteo de pixels.
La fórmula de σ_integrado es idéntica.

### R5: Record schema breaking change
Agregar vrp_test1_mw al schema de records cambia todos los JSONs.
**Mitigación:** default None, retrocompatible. Dashboard y audit no
fallan si el campo no existe (records viejos).

## Criterios de aceptación antes de merge a main

- [ ] Recall Villarrica ≥ 67% (4/6 refs detectadas).
- [ ] Recall Lascar Tier A no cae más de 5 pp vs pre-Test1.
- [ ] Precision sistema global no cae más de 10%.
- [ ] Tests unitarios para `compute_test1` con fixtures: crater solo,
      background ruidoso, crater + FP lejano.
- [ ] Audit completo con snapshots antes/después en `experiments/audit_s13/`.
- [ ] Lesson documentado en `tasks/lessons.md`.
- [ ] Dashboard renderiza las detecciones Test 1 con color distintivo.

## Estimación total

| Fase | Esfuerzo |
|---|---|
| 1. Prototipo offline | 1-2 h |
| 2. Integración pipeline | 2-3 h |
| 3. Validación | 1 h |
| 4. Rollout | 0.5 h |
| **Total** | **~5-7 h de sesión S13** |

## Código base para empezar (pseudocódigo)

```python
def compute_test1(bt_2d, lat_2d, lon_2d, vent_lat, vent_lon,
                  lambda_mir_um, roi_km=3.0, inner_km=1.0,
                  k_sigma=3.0, mir_relative=0.02, scan_angle=0.0):
    """
    Coppola 2015 Eq. 1 implementation.
    
    Returns: {
        'triggered': bool,
        'vrp_roi_mw': float,
        'delta_l_integrated': float,  # W/m²/sr/µm
        'sigma_delta_l': float,
        'l_bg_mir': float,
        'n_contributing_pixels': int,
        'centroid_lat': float | None,
        'centroid_lon': float | None,
    }
    """
    # 1. masks
    dist = haversine_km(vent_lat, vent_lon, lat_2d, lon_2d)
    roi_mask = dist <= roi_km
    bg_ring_mask = (dist > inner_km) & (dist <= roi_km)
    
    # 2. convertir BT a radiancia MIR vía Planck
    L_mir = bt_to_spectral_radiance(bt_2d, lambda_mir_um)
    
    # 3. background stats (MAD-based para robustez ante outliers)
    L_bg_values = L_mir[bg_ring_mask & ~np.isnan(L_mir)]
    if len(L_bg_values) < 20:
        return no_trigger()
    L_bg = np.median(L_bg_values)
    mad = np.median(np.abs(L_bg_values - L_bg))
    sigma_bg = 1.4826 * mad
    
    # 4. exceso integrado (solo pixeles > bg)
    roi_vals = L_mir[roi_mask]
    excess = np.maximum(0, roi_vals - L_bg)
    delta_l_roi = np.sum(excess)
    n_contributing = np.sum(excess > 0)
    
    # 5. σ integrado
    n_roi = np.sum(roi_mask)
    sigma_delta_l = sigma_bg * np.sqrt(n_roi)
    
    # 6. criterio dual
    abs_criterion = delta_l_roi > k_sigma * sigma_delta_l
    rel_criterion = delta_l_roi > mir_relative * L_bg * n_roi
    
    if not (abs_criterion and rel_criterion):
        return no_trigger()
    
    # 7. VRP con Wooster sobre pixeles contributivos
    # (en la implementación real pasamos pixel_areas)
    vrp_roi_mw = 18.9 * np.sum(pixel_areas[roi_mask] * excess) / 1e6
    
    # 8. centroide ponderado por excess (para display)
    weights = excess
    centroid_lat = np.sum(lat_2d[roi_mask] * weights) / np.sum(weights)
    centroid_lon = np.sum(lon_2d[roi_mask] * weights) / np.sum(weights)
    
    return {
        'triggered': True,
        'vrp_roi_mw': vrp_roi_mw,
        'delta_l_integrated': delta_l_roi,
        'sigma_delta_l': sigma_delta_l,
        'l_bg_mir': L_bg,
        'n_contributing_pixels': int(n_contributing),
        'centroid_lat': float(centroid_lat),
        'centroid_lon': float(centroid_lon),
    }
```

## Próxima sesión (S13)

Arrancamos con Fase 1 sobre Villarrica (caso más claro del gap). Si
funciona ahí, el resto es mecánico.
