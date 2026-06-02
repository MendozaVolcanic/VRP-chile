# S98 — Procedimiento de promoción a operacional (fix del ancla de detección)

**Ejecutar SOLO si el reproc de validación cumple los criterios Y con OK explícito
de Nicolás (A45).** Mientras tanto: pre-escrito (A16) para cierre rápido.

El fix (branch `s98-detection-anchor`) cambia el ancla de detección/clustering/
distancia de `mirova_center` (centro del grid) al cráter (`vent_lat`). Afecta
SOLO a Tupungatito / PuyehueCordonCaulle / PlanchonPeteroa (offset grande); los 8
de offset <0.55 km no cambian (ancla ≈ igual).

---

## GATE 0 — Evaluar el reproc (paso previo, no es promoción todavía)

Cuando termine el run (artifacts): descargar y auditar A/B.
```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
mkdir -p experiments/_s98_anchor/_artifacts
gh run download <RUN_ID> -D experiments/_s98_anchor/_artifacts
# mover cada s98-anchor-<vol>/<vol>.json a data/_s98_anchor/<vol>.json
mkdir -p data/_s98_anchor
for d in experiments/_s98_anchor/_artifacts/s98-anchor-*/; do cp "$d"/*.json data/_s98_anchor/; done
PYTHONIOENCODING=utf-8 python experiments/_s98_anchor/audit_spatial.py
PYTHONIOENCODING=utf-8 python experiments/_s98_anchor/audit_ratio.py
```

**Criterios de aceptación (todos deben cumplirse):**
- [ ] Tupungatito: mediana det→cráter **< 2 km** (baseline 5.91).
- [ ] Tupungatito: ratio mediano **hacia 0.5–2.0** (baseline 20.0×).
- [ ] Recall (ALERTAS detectadas con pc.vrp>0) **NO cae** vs baseline.
- [ ] Lascar + Villarrica (controles, offset chico): **sin cambio** (det→cráter y
      ratio ≈ baseline; cualquier desvío >0.3 km / >0.2× es señal de bug).
- [ ] PCC / PP: mejora o al menos no empeora (difusos A20/A22 → tolerar gap).

Si NO cumple → NO promover. Documentar en `docs/S98_ANCHOR_FIX_RESULTS.md` y
decidir (¿gap por selección de cluster §2? → brainstorm propio).

---

## Promoción (solo tras GATE 0 ✅ + OK Nicolás)

### Paso 1 — Tag defensivo (A45)
```bash
git checkout main && git pull --ff-only
git tag -a pre-s98-promote-operational -m "snapshot pre-promoción fix ancla S98" && git push origin pre-s98-promote-operational
```
(El tag `pre-s98-detection-anchor` ya cubre el estado del código pre-fix.)

### Paso 2 — Mergear el fix de código a main
PR `s98-detection-anchor` → main. Cambia el pipeline operacional: el NRT cron
(cada 2h) usará `get_detection_anchor` (cráter) de ahí en adelante.
```bash
gh pr create --base main --head s98-detection-anchor --title "fix(s98): ancla detección al cráter (enfoque B)" --body "..."
# CI verde + mergeStateStatus CLEAN:
gh api --method PUT repos/MendozaVolcanic/VRP-chile/pulls/<N>/merge -f merge_method=squash
```
⚠️ Desde este merge, los records NRT nuevos llevan el ancla correcto, pero el
**histórico de mirova_equivalent sigue con el ancla viejo** hasta el Paso 3.

### Paso 3 — Reprocesar histórico a mirova_equivalent (vols afectados)
Solo **Tupungatito / PCC / PP** cambian; los 8 chicos no necesitan reproc (ancla
idéntica). Decisión de ventana (consultar a Nicolás): todo el histórico vs solo
lo que muestra el dashboard (~90 días) vs desde la primera ref MIROVA.
- Mecanismo: reproc por **chunks mensuales** (A15: no full-history en un job GH;
  timeout 6h) o **local** (`run_pipeline.py --profile mirova_equivalent --volcano X`).
- **A47: secuencial, NO paralelo** sobre el mismo `data_subdir=mirova_equivalent`.
- ⚠️ Sobrescribe data operacional → el tag del Paso 1 es el respaldo.
- Tras reproc: `git add data/mirova_equivalent/{Tupungatito,PuyehueCordonCaulle,PlanchonPeteroa}.json`.

### Paso 4 — Verificación en las 3 vistas (S92 L5, preview REAL no `node --check`)
Servir desde `/frontend/` (BASE_PATH=/, data en `/data/...`). Verificar en
navegador (mcp Claude_Preview o local server):
- [ ] **index.html**: tarjeta Tupungatito muestra dist al **cráter** (≈0–2 km), NO
      ~4.8 km. Mapa: marcador de detección en el cráter (norte), no en el glaciar (sur).
- [ ] **index.html**: PCC / PP coherentes; los 8 chicos + Lascar/Villarrica SIN cambio.
- [ ] **diario.html**: tendencia 90d de Tupun sin saltos artificiales.
- [ ] **mosaico.html**: overview 48h/30d sin regresión de render.
- [ ] Toggle Cluster⟷Núcleo (F5'), footprint, auto-refresh: siguen funcionando.

### Paso 5 — Push + verificar deploy público (R8)
```bash
git commit -m "data(s98): reproc histórico vols afectados con ancla=cráter"
git push origin main
```
- [ ] GitHub Pages publicó (esperar deploy) y la URL pública muestra Tupungatito
      en el cráter.

### Paso 6 — Cierre
- Actualizar `docs/S98_ANCHOR_FIX_RESULTS.md` (tabla fix llena), `MEMORY.md`,
  `CLAUDE.md` Estado, `tasks/BLOQUE_ARRANQUE_S99.md`.
- A63: el test `tests/test_detection_anchor.py` queda como guard anti-revert.

---

## Rollback (si algo sale mal post-promoción)
```bash
# código:
git checkout pre-s98-promote-operational -- pipeline/geo_utils.py scripts/run_pipeline.py
# data:
git checkout pre-s98-promote-operational -- data/mirova_equivalent/Tupungatito.json \
   data/mirova_equivalent/PuyehueCordonCaulle.json data/mirova_equivalent/PlanchonPeteroa.json
git commit -m "revert(s98): rollback fix ancla" && git push
```
El test de regresión fallará tras el rollback (espera el ancla=cráter) → es
esperado; comentarlo o marcarlo xfail si el rollback es definitivo.
```

## Notas de decisión (para resolver con Nicolás en la promoción)
1. **Ventana del reproc histórico** (Paso 3): ¿todo el histórico, 90 días, o desde
   la 1ª ref MIROVA? Trade-off: completitud del dashboard vs tiempo de reproc.
2. **PCC**: su `vent_lat` es el cono Puyehue, pero la actividad real es el lacolito
   Cordón Caulle ~6 km SE (en `volcanic_features.yaml`). El fix ancla al cono. Si
   el audit muestra que PCC no mejora, evaluar si su `vent_lat` debería apuntar al
   lacolito (cambio de config separado, su propio A45).
3. **Segundo problema (§2)**: el 44% que S65 no curó (selección de cluster por VRP
   sumado). Medir cuánto cura B; si queda gap, brainstorm propio antes de tocar
   `clustering.py`.
