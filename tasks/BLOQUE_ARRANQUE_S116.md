# BLOQUE ARRANQUE S116

**Sesión S115 (2026-06-22)** cerró las 4 prioridades acotadas que quedaban tras S114
(que había cerrado el frente algorítmico grande D11-MODIS como irreducible, A82). Todo S115
fue **docs + 1 fix de frontend, sin pipeline** (PR #451 merged, squash `e7bde3d6`). Registro:
`project_s115_estado` (memoria) + `tasks/backlog_s115.md`.

## §0 — Primer comando
```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
git fetch origin --prune && git pull --ff-only
```
Leer en memoria: `project_s115_estado` + `MEMORY.md` index.

## ✅ Cerrado en S115 (no reabrir)
- **#6 datetime diario.html** — `parseUtcMs` sobre la referencia MIROVA (LIVE, verificado preview).
- **#1 FICHA SDA** → v1.0 — 2026-06-22 (`docs/FICHA_SDA_VRP_CHILE.md`, publicable al día).
- **#3 GAP #A** — RESUELTO como **MISLABEL** (no era gap): el flag `ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK`
  controla el REPORTE (OFF=fiel, paper §298-300 + Eq.6), no el pool μ/σ. **No reabrir, no A/B.**
- **#5 inner_radius PCC 20→10** — RECHAZADO (MISSION anti-patrón + A18/A45 + A72). Decisión Nicolás
  "no tocar". Ver `tasks/backlog_s115.md`.

## 🚫 NO reabrir (cerrado S114, anti-A8)
- **far→summit MODIS / sobre-detección difusa A69 (D11 cara-MODIS)**: irreducible a 1 km (A82).
  Detección MODIS fiel a Coppola (file:line). Recall cubierto por VIIRS375 (A77). VIIRS sano (99%/86%).

## Backlog S116 (sin frente urgente — el sistema está sano)
1. **Cabeceras FICHA SDA en código núcleo** (deuda CPLT N°372, decisión Nicolás S115 = sesión dedicada):
   `process_modis.py`, `process_viirs.py`, `process_viirs_mod.py`, `store.py` NO tienen cabecera FICHA
   (solo `anchor.py` + `vrp_regimes.py`). Solo comentarios, pero toca pipeline → **A45** (tag + OK).
   Detalle: `tasks/backlog_s115.md`.
2. **#5 alternativa display PCC** (solo si Nicolás lo pide; eligió "no tocar" en S115): render
   `geo_class="extension"` (naranja, frontend, hoy NO aplicado a PCC) para la cola del lacolito en vez
   de summit-rojo. Frontend puro (MISSION pregunta 3). No es prioridad.
3. **Backfill histórico VIIRS375+V750** (NRT llena forward; de AUDIT_S112).
4. **Parte C Test1-lowmag** (NdC 22-mar 0.49 FN): sub-píxel → canal correcto es alta-res OLI/MSI
   (Landsat-v1 / NHI-v1, OTRO repo, A77). No es VRP Chile (instrumento equivocado por resolución).
5. **NEW-8 gaps 2-4** (pool estadístico m,σ §267-273) — divergencia menor abierta, no prioridad.

## Reglas vinculantes (siempre)
A45 (tag + OK Nicolás antes de tocar `pipeline/`), MISSION 3-preguntas, A62 adversarial (cruzar vs
MIROVA con `pc.vrp_mw` — A10), A82 (no reabrir D11-MODIS), A72 (fix de algoritmo > display si es
artefacto). Explicar como geólogo (fenómeno → mecanismo → recién números).

## Estado operacional (sano)
NRT cada 2h. Guard A46 LIVE. Detección MODIS fiel a Coppola (S114). FICHA SDA v1.0. Suite 776.
