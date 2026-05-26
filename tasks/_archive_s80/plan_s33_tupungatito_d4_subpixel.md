# Plan S33+ — Tupungatito 51% FNs sub-pixel (D4 caso especial)

> Hallazgo independiente de Driver B. Recall Tupungatito ~48% pre y post
> S32. No empeoró con Phase 1.

## Síntoma

35/68 refs MIROVA Tupungatito (51.5%) son FNs nuestros. TODOS tienen
`triggered_test1=Y` con 40-88 pixels Test 1 y t_max 277-285K (5-12K
sobre background ~265K) — pero **`vrp_mw = 0`**.

MIROVA reporta 0.03-0.59 MW para esas mismas noches (sub-pixel típico).

## Causa raíz

`pipeline/process_viirs.py:779`: cuando Test 1 dispara,
```python
t1_delta_L = np.maximum(t1_L - test1_L_bg_local, 0.0)
t1_vrp = t1_area * WOOSTER_COEFF * t1_delta_L / 1e6
vrp_mir_mw = float(np.sum(t1_vrp))
```

`test1_L_bg_local` es la mediana de radiancia del **ring 1-3km** del cráter
(test1_inner_ring_km..test1_roi_km). En Tupungatito ese ring contiene:
- Lago crateriana siempre tibio.
- Fumarolas peri-cráter.
- Roca alterada hidrotermal.

Resultado: `L_bg_local` es alto, similar o mayor que `t1_L` individual.
ΔL clip a 0 en todos los pixels → sum=0 → vrp_mir_mw=0.

**Test 1 integrated sí captura la señal** (ΔL_ROI > k_sigma * σ_ΔL trigger),
pero cuando descomponemos per-pixel para sumar VRP, perdemos esa misma
señal porque cada pixel individualmente NO supera el L_bg_local.

## Verificación pendiente

1. Inspeccionar `test1_L_bg_local` en records Tupungatito FNs — verificar
   numéricamente que es alto vs t1_L pixels.
2. Comparar con `L_bg_global` (anillo 5-25km vent) — cuánto más bajo es
   el background "lejos" del cráter.
3. Verificar que Coppola 2015 §2.2 Eq.1 prescribe "L_bg ROI vent" (1-3km)
   o "L_bg global" (5-25km) para el cálculo VRP per-pixel post-Test1.

## Hipótesis fix

### Opción A — VRP integrated del Test 1 trigger

Cuando Test 1 dispara, en lugar de re-calcular VRP per-pixel, usar el
ΔL_ROI integrated del trigger (que ya está en `test1_res`) directamente.
Coppola 2015 Eq.1: VRP = ΔL_ROI · A_ROI · k.

Pros: usa la señal que el Test 1 detectó.  
Contras: pierde info pixel-level (no podemos clusterizar).

### Opción B — L_bg global cuando per-pixel sum es 0

Detectar el caso (Test 1 trigger=Y, sum t1_vrp=0) y fallback a recálculo
con L_bg global (anillo 5-25km).

Pros: mantiene framework actual, fix focalizado.  
Contras: el L_bg global puede tener su propia heterogeneidad.

### Opción C — clip negativo permitido

`t1_delta_L = t1_L - test1_L_bg_local` sin clip a 0. Si la sumatoria es
positiva, hay señal. Si es negativa, no detección real.

Pros: matemáticamente coherente con el integrated trigger.  
Contras: VRP "negativo" no físico para pixels individuales.

### Recomendación

**Opción B** — defensiva y compatible con el framework. Si Tupungatito y
similares tienen L_bg_local contaminado pero L_bg_global limpio, ese
fallback recupera la señal sin tocar la metodología principal.

Aplicable solo cuando `triggered_test1=True` y `np.sum(t1_vrp)=0`.

## Caveat regla MISSION.md

¿Está documentado en papers MIROVA core?
- Coppola 2015 §2.2 Eq.1: VRP del integrated. NO especifica L_bg local vs global.
- Coppola 2024 cap Springer Eq.16: `VRP_MIR = k · A_pix · (L_obs - L_bg)`.
  No define L_bg local vs global.

Borderline. Defendible como **alineación con Test 1 integrated logic** (si
el trigger ve señal, el reporte debe mostrarla). Pero si MIROVA hace algo
distinto a "L_bg=ring 1-3km y clip", divergimos.

## Pasos S33+

1. Verificar empíricamente con records Tupungatito: `t1_L pixels` vs
   `test1_L_bg_local` vs `L_bg_global`.
2. Si confirma hipótesis: implementar Opción B con flag.
3. A/B test: Tupungatito debería subir recall hacia 80-95%.
4. Verificar que Lascar/Lastarria/Villarrica no regresionen (sus L_bg_local
   no son contaminados como Tupungatito; el fix no los afecta).

## Volcanes potencialmente afectados

Por característica fisiográfica (calor geotérmico crónico ring cráter):
- Tupungatito (este caso, glaciar 5800m + lago + fumarolas).
- Lastarria (fumarolas peri-cráter persistentes).
- Llaima (calor geotérmico crónico documentado en P4).
- Posiblemente Copahue (lago ácido ~50°C en periodos no eruptivos).
