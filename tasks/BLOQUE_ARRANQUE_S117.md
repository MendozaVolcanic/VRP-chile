# BLOQUE ARRANQUE S117

**Sesión S116 (2026-06-27)** ejecutó la **auditoría integral A51** (8 ejes paralelos + síntesis
adversarial) → `docs/AUDIT_S116.md`. Veredicto: **motor SANO, deuda de TRACKING**. Se identificaron
**3 contradicciones cross-source firmes + 1 borderline = umbral A51** → la recomendación es
**consolidar antes de abrir features nuevas**. Registro: `project_s116_estado` (memoria) +
`experiments/_s116_audit/eje{1..8}_*.json`. Tag `pre-s116-audit`. 0 pipeline, 0 A45.

## §0 — Primer comando
```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
git fetch origin --prune && git pull --ff-only
```
Leer: `docs/AUDIT_S116.md` (síntesis + plan priorizado) + `project_s116_estado` (memoria).

## ⭐ PRIORIDAD S117 — Sprint de consolidación (gatillo A51)
Cerrar las contradicciones antes de features. Cada fix que toque `pipeline/` lleva A45 (tag + OK Nicolás)
en su propia sesión/PR. Orden recomendado:

### P1 — barato, sin riesgo algorítmico
1. **C3 — Reactivar R2 + decidir goldens.** Corregir el path stale del TIF archive en
   `tests/test_r2_pixel_level.py` (busca `C:\Users\nmend\OneDrive\mirova-tif-archive`, real está en
   `...\Escritorio\claude\Volcanologia\mirova-tif-archive`) → reactiva los 7 tests R2 (protocolo de
   adopción S33). Decidir si regenerar los **16 golden records S27** (skipped "obsoletos pre-S27") contra
   el pipeline actual = suite de regresión metodológica. *(tests/, TDD — no es pipeline).*
2. **C1 — Cabeceras FICHA SDA en los 6 núcleo** (deuda legal CPLT N°372): `process_modis.py`,
   `process_viirs.py`, `process_viirs_mod.py`, `store.py`, **`anchor.py`** (NO la tenía, contra lo
   documentado), `detection_context.py`. Contenido propuesto en `experiments/_s116_audit/eje6_transparencia.json`.
   Solo comentarios, pero toca pipeline → **A45, sesión dedicada**. NO la requieren: fetch/scan_geometry/
   clustering/audit_metrics/loaders.
3. **Corregir doc** que generó C1: CLAUDE.md + `tasks/backlog_s115.md` afirman que anchor.py tiene FICHA
   (falso). Y actualizar `docs/MIROVA_DIVERGENCES.md` con C4 (NEW-8 pool m,σ: premisa D9 curada S102-S113
   → ¿obsoleto el A/B F2.1?).

### P2 — decisión binaria de Nicolás
4. **C2 — Gates intra-radio S84/S85** (`enable_path_d_intra_radio_gate` yaml l.188 +
   `enable_second_pass_intra_radio_gate` l.207, ambos ON). Flagged por S86 + S105 como anti-patrón A55
   redundante con el frontend. Antes de tocar: clasificar la categoría física (E-S86/A54) de los records
   que filtran. Revertir o re-justificar/documentar. *(pipeline → A45 + MISSION).*

### P3 — robustez + housekeeping (sin urgencia)
5. **Blindaje CMR-search** (espejo de A64 para el host de búsqueda; única falla NRT real fue Copahue 26-jun
   por ReadTimeout de `cmr.earthdata.nasa.gov`). *(fetch.py → A45).*
6. **Housekeeping** (A38, tag defensivo, NO borrar): archivar `data/_*/` (757MB) + `_s76_experiments_pending/`
   (115MB, en carpeta padre) bajo tag; agregar scratch dirs a `.gitignore`; podar ~120 branches mergeadas.
   Integrar `IDEAS_*.md` de la carpeta padre a `docs/`/`tasks/backlog`.
7. **`Distancia_km`** del CSV MIROVA en diario.html (validación de posición desperdiciada). *(frontend).*

## 🚫 NO tocar (anti-A8 / decisión Nicolás)
- far→summit MODIS / D11 / A69 (A82, irreducible, cerrado S114).
- inner_radius PCC 20→10 (rechazado S115, MISSION).
- Parte C Test1-lowmag NdC 22-mar (sub-píxel → Landsat-v1/NHI-v1, A77, OTRO repo).

## Reglas vinculantes (siempre)
A45 (tag + OK Nicolás antes de `pipeline/`), MISSION 3-preguntas, A62 adversarial (cruzar vs MIROVA con
`pc.vrp_mw` — A10), A61 (re-anclar al GVP), A48/A50 (verificar file:line + cross-source — la auditoría
S116 reconfirmó que las contradicciones de doc se ven solo verificando el código). Explicar como geólogo.

## Estado operacional (sano)
NRT cada 2h (~92-98% éxito, breaker LANCE OK). Guard A46 LIVE. Detección MODIS fiel a Coppola (S114/S116).
FICHA SDA v1.0 publicable. Suite 775 passed. Recall VIIRS375 98.4% / V750 85% / MODIS cráter 100%.
</content>
