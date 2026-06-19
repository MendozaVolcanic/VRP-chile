# BLOQUE ARRANQUE S114

**Sesión S113 (2026-06-18)** cerró el frente #3 (coherencia A46) + formalizó A77-A81 + caracterizó #2
(cirrus). PRs #444 + #445. Registro: `project_s113_estado` (memoria) + `docs/S113_A46_COHERENCE_GUARD.md`.

## §0 — Primer comando
```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
git fetch origin --prune && git pull --ff-only
```
Leer en memoria: `project_s113_estado` + `reference_s113_cirrus_d9_scope` (reframe #2) +
`reference_s113_a46_bidirectional` (incluye el hallazgo MODIS far→summit de abajo).

## ⭐ PRIORIDAD S114 — re-auditoría de paridad por sensor + frente MODIS far→summit (A46 inverso)
El cierre de S113 (re-audit pedido por Nicolás) destapó esto sobre data fresca, gate dashboard
(summit && centroid≤inner = lo que ve el operador): **VIIRS375 recall 99% · VIIRS750 85% · MODIS 17%**.
La caída MODIS es la cara **far→summit** del bug A46 (la S112 reportó 94% con un "detectamos algo", no
el gate del dashboard): para Láscar, de 16 ALERTAS MODIS, **23 records quedan `far` con `geo_class=
"summit"`** (cluster crateriano 1.2-3.1km) porque el `final_hotspot` apunta al **Salar de Atacama 18-24km**
que le roba el hotspot; `cluster_rescue` F47 NO dispara (Salar dentro del geofence, hotspot_dist<MAX 25km).
- **Es recuperación LEGÍTIMA** (MIROVA confirma, cráter real), distinta del NdC A69. Matiz A62:
  cobertura por-noche sana (VIIRS375 cubre), falla la COMPLETITUD por-sensor (serie MODIS Láscar vacía).
- **Plan**: (1) re-auditoría completa por sensor — refrescar CSV ground-truth (A17, los actuales son del
  16-jun) + subagentes paralelos por sensor (A26). (2) Frente far→summit = guard unidireccional ESPEJO
  del de S113: promover SOLO clusters crateriana genuinos (geo=summit + cerca + no-nti-piso), NO los A69
  de NdC (trap A48 de los 2527). El discriminante real-vs-A69 es el mismo problema duro que D11 →
  MISSION 3-preguntas + brainstorming + TDD + A45 (tag, OK Nicolás). Detalle: `reference_s113_a46_bidirectional`.

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

**La otra cara de D9 (amplificación de MAGNITUD) — REEVALUADA Y CURADA S113**: el "6-12× sistemático
en cirrus" de S71 ya NO existe tras las adopciones nadir/focal S102-S109. Ratio nuestro/MIROVA (pc.vrp,
A10) sobre 610 TP path-D visibles = **mediana 0.53×**; solo 2 records >5× (VIIRS750 cirrus a 3-4 MW =
cola documentada del ~30% residual focal V750 S112). **D9 efectivamente RESUELTA en ambas caras — no
quedan acciones abiertas.** Ver `docs/MIROVA_DIVERGENCES.md` §S113.

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
