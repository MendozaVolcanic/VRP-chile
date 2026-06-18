# BLOQUE ARRANQUE S114

**Sesión S113 (2026-06-18)** cerró el frente #3 (coherencia A46) + formalizó A77-A81 + caracterizó #2
(cirrus). PRs #444 + #445. Registro: `project_s113_estado` (memoria) + `docs/S113_A46_COHERENCE_GUARD.md`.

## §0 — Primer comando
```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
git fetch origin --prune && git pull --ff-only
```
Leer en memoria: `project_s113_estado` + `reference_s113_cirrus_d9_scope` (reframe #2) +
`reference_s113_a46_bidirectional`.

## ✅ Cerrado en S113 (LIVE)
1. **#3 coherencia A46** (#444, A45, tag `pre-s113-a46-coherence-guard`): guard unidireccional en
   `store.py` (summit + pc.vrp>0 + pc.centroid>inner → far). Suite 776. El flagship ya se había
   auto-curado por el ancla honesta (A8); bug genuino = 2 records Villarrica. Evité el trap A48 de
   re-derivar 2527 far→summit.
2. **A77-A81** en CLAUDE.md proyecto (#445).

## §1 — #2 cirrus D9/A23 — EL GATE DE DETECCIÓN YA ESTÁ RESUELTO (S71). NO re-abrir A/B.
**Hallazgo S113 (papers-first cruzado con D9 + verificación en vivo, `reference_s113_cirrus_d9_scope`
+ `docs/MIROVA_DIVERGENCES.md` §S113):**
- **La cara FP de detección está RESUELTA y verificada en vivo**: cirrus FAR genuino (path-D + t_bg<262
  + far) = 199 records, **0 fugan** al dashboard (gate `far`) y **0 con pc.vrp>5MW** (cap C de S71 activo).
- **Los 3 candidatos que el bloque viejo listaba para #2 = exactamente las 3 opciones A/B-testeadas en
  S71**: atm-gate t_bg y co-validación BT/NTI fueron **RECHAZADAS** (A = cloud-mask anti-MIROVA removido
  S27, Coppola 2016a §247 / 2023 §554; B rompe recall NdC 1.00→0.33); el **cap 5MW (C) fue ADOPTADO y
  está LIVE**, respaldado verbatim (Coppola 2016a §687 "FPs typically radiate <5 MW"). **NO abrir un A/B
  de cirrus nuevo — sería redo de S71 (anti-A8).**
- **TRAP confirmado (A68/A80)**: el candidato "gate si t_bg<262/270K" mataría 207/214 detecciones
  MIROVA-confirmadas reales de fondo-frío-por-altitud (Láscar 5592m). El discriminante NO puede ser t_bg.

**Lo único genuinamente abierto de D9** = la **amplificación de MAGNITUD** (ratios 6-12× cuando MIROVA
también detecta en cirrus) → hipótesis HT1.5-NEW-1/2/3 (cluster selection / kernel bg / Method-2 temporal
weekly-minima). **Es un frente de MAGNITUD, no de detección de cirrus** → fusionar con #4 (MODIS difuso
A69) + reevaluar si persiste tras las adopciones nadir/focal S102-S109. Si se aborda: papers-first ya
hecho (S71/S72, `docs/PAPERS_MIROVA_SYNTHESIS_S71.md`) + MISSION + A45.

## §2 — Frentes menores (backlog, de AUDIT_S112)
- #4 MODIS difuso A69 (sobre-detección RUTINA; focal MODIS + co-val; frente abierto).
- #5 inner_radius PCC 20→10km (display/clasificación; conserva lacolito real ≤8.5km; validar A18).
- #6 20 records MODIS PCC clavados pc.vrp=5.0 (¿cap?); `diario.html:432` datetime sin Z (parseUtcMs, S89).
- Backfill histórico completo VIIRS375+V750 (NRT llena forward).
- Parte C Test1-lowmag (NdC 22-mar 0.49 FN; probablemente sub-píxel, verificar OLI/MSI — A77).
- FICHA SDA update (cambios metodológicos S112-S113).

## Estado operacional (sano)
NRT cada 2h. Guard A46 LIVE (NRT lo aplica forward). Suite 776. A45 + MISSION + A62 adversarial
(cruzar vs MIROVA con pc.vrp_mw — A10). Explicar como geólogo.
