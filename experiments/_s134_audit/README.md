# experiments/_s134_audit — auditoría S134 (anillo → magnitud → paridad)

Plan: `docs/superpowers/plans/2026-09-05-auditoria-s134-anillo-y-paridad.md`.
Un subdirectorio por frente: `f1/` posición→magnitud→paridad · `f2/` TIF MIROVA misma pasada ·
`f3/` probe de atribución por etapa · `f4/` solape del barrido · `f5/` regla C (pendientes).
`tif/` y `granules/` son descargas puntuales (NO se commitean; ver `.gitignore` local).

## Decisión de infraestructura tomada al arrancar (2026-09-05 14:40 UTC)

El disco C: estaba al 100 % (4,3 GB libres) y un worktree completo pesa 3,2 GB (data 1,05 GB,
experiments 1,28 GB, documentacion 0,55 GB). Cinco worktrees completos eran imposibles, así que
se aplicó la salida que la propia regla A44 prevé: **worktrees con sparse-checkout** (29 MB cada
uno) en `../VRP-Chile-s134-f{1..5}/`, branches `s134-f{1..5}`, con `pipeline/ scripts/ tests/
docs/ frontend/ .github/ tasks/ experiments/_s133* experiments/_s134_audit`. Los auditores leen
`data/mirova_equivalent/*.json` y `documentacion/` desde la raíz canónica por ruta absoluta,
sólo lectura. Los A/B ya estaban bajados en `~/ab_area` (24/24) y `~/ab_b22` (4/4); no se
volvieron a bajar.
