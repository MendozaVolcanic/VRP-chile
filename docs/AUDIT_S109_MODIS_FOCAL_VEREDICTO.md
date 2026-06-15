# AUDIT_S109 — Veredicto FINAL A/B magnitud núcleo-focal MODIS

**Run**: 27521928757 (36/36 success). **Audit**: `experiments/_s109_modis_mag/audit_focalmag_ab.py`
(criterios A66 pre-registrados, design 2026-06-14 §8). **Fecha**: 2026-06-15.

## Resultado (6 vols: Chaitén, Villarrica, PCC, Tupungatito, Llaima + Láscar control)

| Criterio | ctx (keep-peak) ⭐ | ctxpure (canario) |
|---|---|---|
| **C1** detección 0-diffs (granules comunes) | **PASS** (0 / 1791) | PASS (0 / 1791) |
| **C2** inflados curados (pc.vrp>5 → ≤5) | 71% · mediana ON/base **0.42×** | 72% · 0.34× |
| **C3** Láscar control (ratio ∈[0.85,1.15]) | **PASS 1.000** (n=254) | PASS 1.000 |
| **C4** foco/incendio preservado (≥0.80) | **PASS 1.000** (n=864) | PASS 1.000 |
| focal_degraded (solo-pico, sin foco contextual) | 1055 records | 1055 |

## Veredicto: ctx ADOPTABLE (regla A66 pre-registrada)

Los criterios DUROS (C1 detección, C3 Láscar, C4 foco) **pasan limpio en los 6 vols**, incluidos
los 2 difíciles (**PCC cirrus + Tupungatito glaciar** — los que rompieron el fondo-local A19/A66).
Por la regla pre-registrada (adoptar el brazo que pase C1+C3+C4 y maximice C2), **ctx es adoptable**.
ctx preferido sobre ctxpure (keep-peak = guard anti-FN; C2 prácticamente empatado 71 vs 72%).

**Mecanismo confirmado**: 1055 records colapsaron al solo-pico = eran **campo difuso topográfico
puro** sin foco contextual (A69/D11). Los focos reales (Láscar y demás) quedaron en **1.000**
(intactos). Es el **opuesto exacto del fondo-local refutado** (S108: footprint 4% / ring 20%,
empeoraba; este cura 71% sin tocar lo real).

## Honesto (A66/A62)

- **C2 71% < 85% pre-registrado**: los ~29% que no curan del todo son los **difusos más fuertes de
  Chaitén** (bajan ~40-50% igual: 18.6→10.8, 17.6→13.7, 16.8→8.0, pero no cruzan el piso de 5 MW).
  Quedan acotados (~8-13 MW vs hasta 60 del base). NO es un fallo de los criterios duros.
- El C2 es métrica de "maximizar", no gate duro (así se pre-registró). La cura es sustancial
  (mediana 0.42× = magnitud partida a la mitad) y uniforme entre vols.

## Implicación / próximo paso (A45, decisión Nicolás)

El fix desbloquea el **flip de §1**:
1. Adoptar `enable_focal_cluster_magnitude` (flip flag + reproc histórico → dashboard muestra
   magnitudes curadas).
2. Flip `enable_honest_anchor_modis` (gateado por la magnitud) → cura el **gap recall MODIS
   summit-gated D12 (10.8%→~96%)**, espejo del ancla ya viva en V375/V750.

**Alto impacto dashboard** (~2476 records far→summit, 93% señal real cross-confirmada; **NdC =
caso especial** MIROVA 0, ~128 candidato-ruido a vigilar). Requiere **OK explícito Nicolás (A45)**
+ tag + reproc + R2/R3/R8. Residuo Chaitén (~8-13 MW) a juicio del geólogo (aceptable vs base 60).

## Verificación NdC del destape del ancla (pedido Nicolás antes del flip)

`experiments/_s109_modis_mag/verify_ndc_destape.py`. Destape NdC = records MODIS 'far' con cluster
AL CRÁTER (Nuevo/Arrau, -36.865/-71.379) que el ancla flipearía a summit:
- **199 records**, magnitud baja (mediana pc.vrp 0.52 MW, de-inflada más por el fix focal), **ΔT 9.2 K**.
- **MIROVA 2026 NdC: 5 VIIRS375 + 1 VIIRS750 + 1 MODIS** (NO es "MIROVA 0" como decía el PREVERDICT S108 —
  desactualizado; NdC es térmicamente activo).
- **Split por cobertura VIIRS375 (refinamiento A62)**: **71% (141) = VIIRS pasó y NO vio nada → artefacto
  A69** (MODIS sobre-detecta el campo tibio topográfico que el sensor más fino no ve); 25% (49) = VIIRS
  summit = REAL cat-b; 5% (9) = VIIRS far parcial. Casi 0 gap de cobertura.

**VEREDICTO NdC: el destape NO está limpio** — 71% es artefacto topográfico (cara-DETECCIÓN de D11/A69,
frente abierto). El fix de magnitud de-infla pero NO frena la detección artefacto. Flipear el ancla
agregaría ~141 detecciones de bajo nivel artefacto en NdC.

**Implicación para el flip**: el fix de MAGNITUD (focal) es adoptable de por sí (de-infla los picos
artefacto visibles en las vistas de tendencia). El flip del ANCLA queda bloqueado por la detección A69
en NdC → su root fix es **D11 (detección MODIS NTI-contextual, A69-inmune)**, el frente siguiente. Tras
D11, el ancla va limpio (cura Lascar D12 sin artefacto NdC). Decisión Nicolás (A45).
