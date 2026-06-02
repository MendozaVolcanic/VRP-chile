# BLOQUE ARRANQUE S98

**Sesión previa S97 (2026-06-01/02 UTC).** Sesión muy larga. ~13 PRs mergeados (#304-#316).
main al día. Detalle: `docs/S97_*` + [[reference_s97_refresh_y_frontend]] + memoria S97.

## §0 — Primer comando
```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
git fetch origin --prune && git pull --ff-only
cat tasks/BLOQUE_ARRANQUE_S98.md
cat docs/superpowers/specs/2026-06-02-detection-anchor-crater-design.md   # EL diseño a ejecutar
cat docs/S97_TUPUNGATITO_ROOTCAUSE.md                                     # diagnóstico raíz
```

## §0.5 — Integridad + proceso (REFORZADO S97, lecciones duras)
- Entorno entrelaza stdout: número/conclusión NUNCA antes del dato; salida a archivo + `cat`;
  un tool call por mensaje. PYTHONIOENCODING=utf-8 para Unicode (°, →, σ). pytest con `-s`.
- **AUDIT-SPATIAL (nuevo A61)**: auditar detección SIEMPRE incluye eje espacial — comparar
  lat/lon de nuestras detecciones contra el cráter físico Y la radiancia local del TIF MIROVA,
  NO solo números de distancia (comparten ancla, pueden coincidir estando ambos mal).
- **AUDIT-ADVERSARIAL (nuevo A62)**: al concluir "estamos bien", y MÁS si Nicolás (dominio)
  disiente, asumir error y refutarlo con datos antes de reafirmar. Su insistencia = señal.
- **TIF ≠ anomalía (A24 reforzado)**: el TIF/KMZ es el campo de radiancia de FONDO (topografía);
  la anomalía es un realce LOCAL de NTI, NO el píxel más brillante. NO ubicar la anomalía por
  centroide/sumas del TIF completo.
- **Tengo Chrome MCP + TIF en ../mirova-tif-archive** — usarlos antes de decir "no puedo".

## §1 — PRIORIDAD S98: implementar el fix del ANCLA (diseño B aprobado, A45)
**Contexto (S97, ya diagnosticado — NO re-investigar):** `get_effective_vent()` usa el
`mirova_center` (centro del recuadro KMZ) como ancla de detección dual-ROI + clustering +
distance_class. Para Tupun/PCC/PP el centro del grid está 2-7.6 km del cráter → detecciones
corridas (Tupungatito ~5.9 km al sur, sobre el glaciar). MIROVA reporta el cráter (dist ~5.2
≈ offset 4.86). **Ya lo arreglamos en S65 (PR #93) y S80 (#220) lo revirtió al regenerar los
11 mirova_center desde el KMZ.** Diseño aprobado: enfoque **B (separar roles)**, alcance solo
el ancla.

**Plan (writing-plans → TDD → A45):**
1. `tests/test_detection_anchor.py` (TDD, rojo): Tupun/PCC/PP → `get_detection_anchor` devuelve
   vent_lat (cráter), NO mirova_center. Guard anti-regresión (lo que faltó en S80).
2. `pipeline/geo_utils.py`: dividir `get_effective_vent` → `get_grid_center` (mirova_center) +
   `get_detection_anchor` (vent_lat prioritario). Migrar callers (run_pipeline.py:202/245/291,
   process_*.py). Detección/clustering/distance_class usan el cráter; grid extent usa grid center.
3. A45: `git tag pre-s98-detection-anchor` + push ANTES del primer edit. OK Nicolás.
4. Reproc validación (nube/local, ventana mayo con TIF): Tupun/PCC/PP + controles Lascar/Villarrica
   a data_subdir aislado. Criterio: Tupungatito det→cráter de ~5.9 a <2 km; ratio hacia 0.5-2.0
   (S66 dio 0.67×); **0 cambio en los 8 de offset chico**; recall no cae. Audit independiente.
5. Promover a operacional solo tras OK Nicolás. Display: distancia desde el cráter (no grid center).

## §2 — Después del fix (medir antes de seguir)
- El 44% que S65 no curó = selección de cluster por VRP sumado (elige glaciar grande sobre
  cráter chico). Medir cuánto cura B; si queda gap → brainstorm propio (¿pico NTI como MIROVA?).
- Opción C (sacar vent_anchored, replicar dual-ROI fiel) — objetivo de fondo.
- Gates intra-radio redundantes (A55, identificados S86) — revisar/remover.

## Estado operacional al cierre S97 (no romper)
- Refresh operacional promovido (#306): magnitud corregida + anomaly_pixels poblado. Cluster
  global/MIROVA 1.18×, F5' fallback 0%, 0 regresiones.
- Núcleo F5' = magnitud DEFAULT (#313). Tarjetas estilo MIROVA + símbolos de volcán + toggle
  footprint + auto-refresh detector de cambios + carga rápida (sin cache-bust).
- Tags defensivos: pre-s97-refresh-promote, pre-s97-staging-cleanup.
