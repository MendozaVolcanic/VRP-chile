# C2 — fix de magnitud path-D MODIS (peak-of-kernel) — design S122

> **Estado: DISEÑO. No ejecutado.** Prerequisito para destrabar D12 (AUDIT_S121_D12_AB.md).
> **CORRECCIÓN S121 (investigación ctxpeak)**: el plan original "portar ctxpeak a MODIS"
> NO sirve — ver §"Por qué". C2 requiere LÓGICA NUEVA, no un flag flip.

## Por qué C2 — y por qué NO es "portar ctxpeak" (premisa corregida)

El A/B del ancla honesta MODIS (S121) **falló por MAGNITUD, no por posición**: se destapan
blobs path-D contextual con VRP inflado (PCC **117 MW**, Tupun 23, NdC 20 — 0% MIROVA, A82).

**Hallazgo que corrige el plan (investigación ctxpeak S121)**: el "ctxpeak"/focal contextual
YA está portado a MODIS y **ya está ON en el operacional** (`enable_focal_cluster_magnitude`,
`mirova_equivalent.yaml:154-155`; `cluster_focal_vrp_mw` en `vrp_regimes.py:214-254`, aplicado
`process_modis.py:984-988,1233-1237`). **Ya estaba activo cuando aparecieron los 117 MW.**

Por qué no basta: `cluster_focal_vrp_mw` suma solo los píxeles que están en `dnti_ctx_hot`
(descarta el campo difuso *no*-contextual). Pero el blob PCC 117 MW es **100% path-D
contextual** — TODOS sus píxeles ya están en `dnti_ctx_hot` → `focal == cluster` → misma
suma. El filtro de máscara contextual no puede bajarlo. Flipear el flag no hace nada (ya ON).

**C2 real = un mecanismo NUEVO que no existe**: reducir el blob path-D contextual a su
**núcleo/pico de radiancia** (peak-of-kernel), no solo filtrar por máscara. Es lógica a
diseñar+codear, no reusar `cluster_focal_vrp_mw`. Ref: los helpers actuales en
`test1_contextual_filter.py:34-63` (VIIRS) y `vrp_regimes.py:214-254` (MODIS/V750) son
filtros de MÁSCARA; ninguno hace peak-of-kernel de radiancia.

## Hipótesis (a validar antes de codear)

Que exista un núcleo de radiancia dentro del blob path-D que, aislado, dé magnitud <5 MW.
⚠️ **Riesgo físico (A82/A83)**: a 1 km el blob difuso y el foco real son el mismo objeto —
el "pico" del blob difuso también puede ser alto. Puede que NO haya núcleo separable. Por
eso el paso 0 es una investigación de datos, NO codear a ciegas.

## Paso 0 (S122, ANTES de diseñar el mecanismo): ¿el blob TIENE núcleo separable?
Sobre los 41 records destapados (artifacts run 29582035729 en scratchpad + reproc): mirar
la distribución de radiancia MIR por-píxel dentro del blob path-D. ¿Hay 1-2 píxeles pico muy
por encima (foco real) + cola difusa (bajar la cola cura)? ¿O es un blob plano (sin núcleo,
C2 no puede funcionar → D12 irreducible a 1 km, confirma A82 y se cierra)? Script read-only
sobre `anomaly_pixels`. **Este análisis decide si C2 es viable ANTES de invertir en código.**

## Secuencia para cerrar D12 (Paso 0 primero — decide viabilidad)

1. **Paso 0 (data, read-only) — ¿el blob tiene núcleo separable?** (§Paso 0 arriba). Barato,
   decide TODO. Si NO hay núcleo → C2 imposible, D12 irreducible a 1 km (confirma A82), se
   cierra el frente sin gastar en código. ← **empezar acá S122**.
2. Si Paso 0 muestra núcleo → **diseñar el mecanismo peak-of-kernel** (design propio + TDD):
   aislar el núcleo de radiancia del blob path-D. Flag nuevo `enable_path_d_peak_magnitude`
   (u similar), OFF por default.
3. **A/B C2 solo** (profile `_c2_peak_modis`, ancla OFF): reproc los 4 vols ×
   2025-02-15..05-15 (comparable directo al A/B ancla). Métrica: los 41 destapes pc.vrp>5
   → ¿caen a <5 MW? Láscar ratio ~0.92× intacto. Script espejo de
   `experiments/_s121_d12_ab/analyze.py`.
4. Si C2 ✅ → **A/B ancla+C2 juntos**: reactivar `_d12_honest_anchor_modis` con C2 ON →
   cura Láscar (76 noches) SIN destape.
5. Si ambos ✅ → adopción: R2 pixel-level Láscar + R3 independiente + **tag A45 + OK Nicolás**.

## Nota de método
- Aislar cada variable (Paso 0 antes de código; C2 solo antes de C2+ancla) — lección A66.
- El Paso 0 es el filtro barato que evita el anti-patrón "codear un fix para un problema
  físicamente irreducible" (A82). Si el blob no tiene núcleo, la respuesta honesta es que
  D12 no se cura a 1 km y el recall MODIS lo cubre VIIRS375 (A77) — cerrar, no forzar.
