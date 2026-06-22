# BLOQUE ARRANQUE S115

**Sesión S114 (2026-06-19/21)** cerró el frente **far→summit MODIS / D11** como **físicamente
irreducible a 1 km** (A82) tras exploración exhaustiva ("probar todo y descartar", pedido Nicolás).
Re-auditoría por sensor: VIIRS sano (375m 99% / 750m 86%), MODIS 16% = bug etiquetado A46, no falta
de detección. **Sin cambios de pipeline** (todo diagnóstico/diseño). Registro: `project_s114_estado`
(memoria) + `docs/AUDIT_S114_PARITY_BY_SENSOR.md`.

## §0 — Primer comando
```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
git fetch origin --prune && git pull --ff-only
```
Leer en memoria: `project_s114_estado` + `MEMORY.md` index. Doc del frente cerrado:
`docs/AUDIT_S114_PARITY_BY_SENSOR.md`. Divergencia: `docs/MIROVA_DIVERGENCES.md` §D11 (cara MODIS CERRADA).

## 🚫 NO reabrir (cerrado con evidencia exhaustiva S114 — anti-A8)
- **far→summit MODIS / sobre-detección difusa A69 (D11 cara-MODIS)**: irreducible a 1 km (A82). NO
  buscar otro gate/discriminante/cap/umbral post-hoc — agotados los 8 discriminantes per-record, N·σ
  Tabla 1, y los 3 ejes ortogonales (ancla, cross-sensor, cap, temporal). La detección MODIS es FIEL a
  Coppola (verificado file:line). El difuso pasa genuinamente; KILLER cat-b (Villarrica/Chaitén ≡ difuso
  a 1 km). Recall cubierto por VIIRS375 (A77). Solo queda abierta la cara POSICIÓN del ancla en nevados
  (~1-1.5 km N, A70, costo residual no de recall/magnitud).

## ⭐ PRIORIDAD S115 — obligaciones + hygiene + decisión GAP #A (frentes con fix limpio)
El frente algorítmico grande (D11-MODIS) está cerrado; lo que queda son frentes acotados:

1. **FICHA SDA update (obligación de transparencia CPLT N°372)** — `docs/FICHA_SDA_VRP_CHILE.md` +
   cabeceras: acumular los cambios metodológicos S112-S114 (anillo intermedio Muy Bajo VIIRS375 S112;
   guard A46 coherencia S113; confirmación de fidelidad detección MODIS S114). Es deuda legal, no
   técnica — vale cerrarla.
2. **#6 `diario.html:432` datetime sin `Z`** — bug display real (parseUtcMs, S89/PR #250 ya lo arregló
   en otras vistas). Verificar las 3 vistas con preview real navegador (S92 L5). Rápido.
3. **Decidir GAP #A** (hallazgo S114, fidelidad literal Coppola §298-300): activar
   `enable_test1_k1_retire_from_hot_mask` retira los píxeles Test 1 K1 del pool μ/σ. **OJO**: afloja el
   gate (saca outliers positivos → σ baja → umbral más permisivo), NO ataca el difuso. Es fidelidad por
   fidelidad. Brainstorming: ¿vale el A/B (riesgo más FP) o queda documentado como divergencia menor
   aceptada? Si A/B → A45 (tag + OK Nicolás) + reproc.
4. **#5 inner_radius PCC 20→10 km** (display/clasificación; conserva lacolito real ≤8.5 km; validar A18).

## Backlog (de AUDIT_S112/S113, menor prioridad)
- Backfill histórico completo VIIRS375+V750 (NRT llena forward).
- Parte C Test1-lowmag (NdC 22-mar 0.49 FN; sub-píxel → verificar canal alta-res OLI/MSI, A77 — es
  Landsat-v1/NHI-v1, otro repo, instrumento correcto).
- #2 cirrus D9/A23: RESUELTO/caracterizado S113 (0 fuga dashboard + cap C). NO reabrir A/B (redo S71).

## Estado operacional (sano)
NRT cada 2h. Guard A46 LIVE. Detección MODIS fiel a Coppola (S114). Suite 776. Reglas vinculantes:
A45 (tag + OK Nicolás antes de tocar pipeline/), MISSION 3-preguntas, A62 adversarial (cruzar vs
MIROVA con pc.vrp_mw — A10), A82 (no reabrir D11-MODIS). Explicar como geólogo.

## Pendiente de commit (S114, solo docs/experiments — SIN pipeline)
`docs/AUDIT_S114_PARITY_BY_SENSOR.md`, `experiments/_s114_audit/`, `CLAUDE.md` (regla NTI + A82),
`docs/MISSION.md`, `docs/MIROVA_DIVERGENCES.md`. (Memoria en `~/.claude/` está fuera del repo.)
