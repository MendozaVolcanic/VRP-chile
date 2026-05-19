# S62 Investigación Tupungatito Test 1 path mecanismo (gap residual 7×)

**Fecha**: 2026-05-18 (S61 paralelo, dejado para S62)
**Status**: investigación parcial, conclusiones inconclusas

## Pregunta original

¿Por qué Tupungatito gap LEGACY/MIROVA NRT con `pc.vrp_mw` es 7.0×? El fix kernel-bg
está OFF para Tupungatito (S59 decisión "ring frío glaciar empeoraría"). Mecanismo
físico real no claro.

## Inspección records top Tupungatito

Window 04-16/05-15, top 5 por `pc.vrp_mw`:

| DT | pc.vrp_mw | n_anom_pix | pc.n_pixels | dist | source |
|---|---:|---:|---:|---:|---|
| 2026-05-15 05:30 | 6.22 | 99 | 98 | 1.57 | test1 |
| 2026-05-13 05:18 | 5.50 | 89 | 89 | 1.66 | test1 |
| 2026-05-14 05:00 | 5.33 | 90 | 85 | 1.78 | test1 |
| 2026-04-27 05:18 | 5.08 | 88 | 88 | 1.64 | test1 |
| 2026-04-25 05:36 | 5.00 | 94 | 92 | 1.78 | test1 |

**Observaciones**:
- Source 87% `test1` (integrated-ROI Coppola 2015 §2.2)
- n_anom_pix ≈ pc.n_pixels (casi todos pixels Test 1 forman 1 cluster contiguo)
- dist 1.57-1.78 km (en summit dentro de inner_radius=7km Tupungatito)

## Anomaly pixels top record 2026-05-15 05:30 (top 10 por VRP):

```
lat=-33.4006 lon=-69.7934 dist=0.62 bt_k=254.3 vrp=0.0000
lat=-33.4040 lon=-69.7940 dist=0.71 bt_k=254.4 vrp=0.0000
lat=-33.4048 lon=-69.7898 dist=1.08 bt_k=254.8 vrp=0.0000
lat=-33.4055 lon=-69.7858 dist=1.46 bt_k=256.5 vrp=0.0000
lat=-33.4062 lon=-69.7819 dist=1.82 bt_k=257.9 vrp=0.0000
```

**Hallazgo inesperado**:
- bt_k = **254-260 K** (−19°C a −13°C) — **fríos**, no calientes
- per_pixel_vrp = **0.0000** (cada pixel individualmente NO contribuye)
- pc.vrp_mw = 6.22 (¡a pesar de pixels fríos!)

**Mecanismo**: Test 1 integrated-ROI suma `max(0, L - L_bg)` sobre toda la ROI 3 km.
Si L_bg es AÚN más frío que 254 K (e.g. 245 K glaciar en bg ring), entonces ΔL > 0
para cada pixel a 254K, y la integral sobre 98 pixels acumula 6.22 MW total.

## Análisis código Test 1 path (`pipeline/test1_integrated.py`)

Función `compute_test1_mir` (líneas 51-189) sigue Coppola 2015 §2.2 Eq.1 literalmente:
- `roi_km = 3.0`, `inner_ring_km = 1.0` (ring background entre 1-3km)
- `L_bg = median(L)` sobre bg_mask
- `sigma_bg = 1.4826 * MAD` (MAD-based robust statistic)
- `delta_L_integrated = sum(max(0, L_roi - L_bg))` sobre toda la ROI ≤ 3km
- `k_sigma = 3.0`, `mir_relative = 0.02` (paper defaults Coppola 2015)
- Trigger si `abs (>3σ) AND rel (>2% L_bg×N)`

**El cálculo es paper-literal**. No hay over-detection arquitectural visible.

## Hipótesis posibles para gap 7×

**H1: L_bg glaciar muy frío sesga ΔL**: en escena con ring 1-3km mayoritariamente
glaciar (245K), L_bg es bajo, ΔL = L_pixel - L_bg es grande aún si L_pixel es solo
moderadamente bajo (254K). Test 1 dispara correctamente, pero la magnitud integrada
resulta mucho mayor que la señal "real" del cráter.

**H1 implicación**: kernel-bg podría ayudar — si los 8 vecinos directos del pixel
hot son menos fríos que el ring 1-3km amplio (porque están en el cráter mismo, no
en el glaciar circundante), el L_bg local sería mayor → ΔL menor → VRP menor.
**Esto contradice S59 decisión "ring frío glaciar empeoraría"**.

**Revisar S62**: A/B Tupungatito kernel-bg=true con 22 ALERTAS y comparar contra
MIROVA NRT. Si NEW pc.vrp_mw mediano < LEGACY 1.33 MW, adoptar.

**H2: MIROVA usa ROI distinta**: si MIROVA usa roi_km < 3 (e.g. 1.5km), n_roi
es mucho menor, ΔL_integrated es menor, VRP final menor. Verificar si paper
documenta ROI variable per-volcán.

**H3: MIROVA aplica filtro post-trigger por cluster connectivity**: solo cuenta
pixels conectivamente al pico más caliente. Nuestro pipeline ya hace eso (línea
1143 `cluster_hotspots` con 8-connectivity), por lo que H3 menos probable.

## Recomendación S62

1. **Re-evaluar Tupungatito en kernel-bg**. La razón S59 "ring frío empeoraría"
   asumía glaciar uniforme. Si el cráter mismo está rodeado de roca caliente (no
   glaciar) en los 8 vecinos directos, kernel-bg local podría dar L_bg más alto
   y curar el gap.
   - Costo: 1 A/B Tupungatito kernel-bg = 3h GH Actions
   - Si valida: agregar Tupungatito a per-vol true
   - Si refuta: confirmar S59 y explorar H2/H3

2. **NO** revertir decisión S59 sin A/B empírico. El razonamiento físico va en
   sentido contrario — necesita validación.

3. **Si A/B Tupungatito NO valida**: investigar params Test 1 (ROI, k_sigma,
   mir_relative) per-vol vs paper. Posible que MIROVA usa params calibrados
   per-volcán que nosotros no tenemos.

## Limitaciones investigación S61

- No tengo BT MIROVA pixel-by-pixel para cross-validar (TIF archive no tiene
  Tupungatito en window window investigado)
- No tengo acceso a fuente código MIROVA NRT (cerrado)
- Hipótesis sin A/B real es teoría
