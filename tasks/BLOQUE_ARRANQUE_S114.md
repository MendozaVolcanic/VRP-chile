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

## §1 — PRIORIDAD S114: #2 cirrus D9/A23 — EMPEZAR POR EL GATE DE BRAINSTORMING
**Reframe de S113 (read-only, `reference_s113_cirrus_d9_scope`) — leer ANTES de diseñar:**
- **El impacto operacional-visible YA está mitigado**: cirrus FAR genuino (path-D + t_bg<262 + far) =
  199 records, **0 fugan** al dashboard (gate `far` de mirovaEqVrp) y **0 con pc.vrp>5MW** (cap D9 5MW
  activo). Por eso el "problema" es de pureza clon-literal / data-hygiene, NO daño operacional.
- **El candidato del bloque viejo "gate path-D si t_bg<262/270K" es un TRAP** (A68/A80 verificado en
  vivo): 207/214 records cold+path-D VISIBLES son MIROVA-CONFIRMADOS reales = fondo frío por ALTITUD
  (Láscar 5592m, Lastarria, Tupun), NO cirrus. Un gate por t_bg los MATARÍA (mismo trap que el V1
  NTI-per-píxel refutado S104). **El discriminante NO puede ser t_bg.**

**Decisión de diseño (gate brainstorming, Nicolás):** ¿vale un cambio de detección delicado dado que
la mitigación (cap 5MW + far-hide) ya neutraliza el impacto visible? Trade-off recall/pureza explícito.
- Si **NO** → documentar D9 como "mitigado, causa raíz aceptada" y mover a #4/#5/#6.
- Si **SÍ** → ciclo completo: **papers-first** (Coppola 2016a §SP426.5 dNTI 8-vec + Campus 2024: cómo
  manejan el contextual dNTI en fondos fríos) + **MISSION 3 preguntas** + **superpowers-brainstorming**
  (definir discriminante NO-t_bg: co-validación BT/NTI absoluto, textura espacial del dNTI, estructura
  del campo) + **A/B 3 brazos** + **A45**. NO meter código sin pasar el gate de diseño.

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
