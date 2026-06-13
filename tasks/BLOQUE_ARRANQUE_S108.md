# BLOQUE ARRANQUE S108

**Sesión S107 (2026-06-13)** — frente MODIS magnitud+posición. Cerró §1 (verificación
del peor FN) + §2 (fix de magnitud implementado y mergeado flag-OFF) + disparó el A/B §2.
Registro completo: `project_s107_lascar_d12_verdict` (memoria) + `docs/AUDIT_S106.md` (marco).

## §0 — Primer comando
```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
git fetch origin --prune && git pull --ff-only
# estado de los 2 A/B que quedaron en vuelo / listos:
gh run view 27480234385 --json status,conclusion   # §2 A/B fondo-local MODIS (36 jobs)
gh run view 27468739388 --json status,conclusion   # §3 A/B V750 (ya COMPLETÓ S107)
```

## ✅ Cerrado en S107
- **§1 FN MODIS Láscar (D12) VERIFICADO**: es FN real (cluster al cráter 1.17 km ≈ MIROVA
  1.41 km; píxel del Salar a ~24 km lo manda a `far`). Blindado con TIF B21 (eje espacial
  A61) + figura. **Veredicto pivote: NO es puro reproc — es CÓDIGO+REPROC encadenado a §2.**
- **§2 fix de magnitud IMPLEMENTADO + MERGEADO flag-OFF** (PR #413, tag `pre-s107-modis-fondo-local`):
  helpers `cluster_corona_background` (V-A/V-B) + `cluster_vrp_mw_with_bg` en vrp_regimes.py;
  integración en process_modis.py (recompute pc.vrp_mw del cluster primario con la corona del
  cluster contiguo, Eq.6, POST-selección → detección intacta). Cierra gap A48. TDD 13 tests +
  pin GR2. Suite 721. Design revisado (gap A48 cerrado).
- **§2 A/B DISPARADO** (PR #414, run **27480234385**): profiles `_modis_localmag_{base,footprint,ring}`
  + workflow + audit pre-escrito. 6 vols (Chaitén/Villarrica/PCC/Tupun/Llaima + Láscar control)
  × 3 brazos × 2 chunks. Criterios A66 pre-registrados.

## §1 — PRIORIDAD S108: aterrizar el A/B §2 (fondo-local magnitud MODIS)
Cuando el run **27480234385** complete:
```bash
gh run download 27480234385 -D experiments/_s107_modis_localmag/_staging
# A64: success != completo. Coverage gate por brazo ANTES del audit:
python experiments/reproc_coverage_gate.py --staging experiments/_s107_modis_localmag/_staging --sensor modis --win 2026-01-29:2026-06-13 --min 0.95
python experiments/_s107_modis_localmag/audit_localmag_ab.py --staging experiments/_s107_modis_localmag/_staging
```
- Criterios (A66): **C1** detección 0-diffs base-vs-ON, **C2** inflados pc.vrp>5 → ≤5 ≥85%,
  **C3** Láscar control ratio ON/base ∈ [0.85,1.15]. Discriminador V-A vs V-B.
- OJO P1.6: el circuit-breaker A64 NO cubre CMR search → algún job puede colgar 50min →
  rerun serial (`gh run rerun --job <id>`) los truncados antes del audit.
- **Si V-B (footprint) pasa los 3 criterios** → flip operacional (A45: tag + **OK explícito
  Nicolás** + es DASHBOARD-VISIBLE, él revisa ahí) → reproc 11 + activar espejo ancla MODIS
  (`enable_honest_anchor_modis`) → **eso cura §1/D12** → frontend 3 vistas.

## §2 — Aterrizar §3 V750 (A/B ya completó: run 27468739388)
Thread independiente, dashboard-visible. Coverage gate (`--sensor v750`, A64) → audit pareado
(`audit_honest_anchor.py`) → flip `enable_honest_anchor_viirs750` + promoción (A45 + OK Nicolás).
Destape pre-verificado limpio (S106, 93 flips far→summit, 0 con pc.vrp>5). Profile + workflow ya existen.

## §3 — §1 D12 (cura definitiva del FN Láscar)
Se cura SOLO al activar el espejo `enable_honest_anchor_modis` (gateado por §2). Por eso §1
depende de que §2 pase el A/B. Después: reproc Láscar MODIS (clonar reproc-s102-nadir-promote.yml,
perfil con ambos flags ON, A47) → `per_sensor_metrics.py` antes/después → frontend.

## 🔑 Reglas vivas para S108
- **A45**: el FLIP operacional (§2 o §3) toca NRT → tag + **OK explícito Nicolás** antes. La
  implementación flag-OFF ya está; falta SOLO el flip, que SÍ cambia el dashboard.
- **Nicolás revisa en el DASHBOARD, no en el código** (feedback S107): yo manejo lo técnico
  (TDD/verificación/merge flag-OFF); él opina cuando hay algo visible. Traerle resultados
  dashboard-relevantes, no diffs.
- **A64**: todo reproc → coverage gate (success≠completo). **A48**: los inflados estaban en
  vols distintos a los del design (verificar con datos, no con el framing). **A61** recall espacial.
- A47 reproc local nunca paralelo sobre mismo data_subdir. A26 calidad > tokens.
- Limpieza: dirty pre-sesión en `experiments/_s9*` (de antes, no tocar). Scratch §1 verificado
  en `experiments/_s107_tif_verify/` (reproducible).

## Prompt copy-paste S108
```
Sesión S108 — VRP Chile. Sincronizá (git fetch origin --prune && git pull --ff-only) y leé
tasks/BLOQUE_ARRANQUE_S108.md + project_s107_lascar_d12_verdict (memoria). S107 verificó el
FN MODIS Láscar (D12, es código+reproc no puro reproc), implementó+mergeó el fix de magnitud
MODIS fondo-local (corona del cluster Eq.6, PR #413, flag-OFF, cierra gap A48, TDD 13 tests) y
disparó el A/B §2 (run 27480234385, 6 vols × 3 brazos). PRIORIDAD §1: aterrizar ese A/B
(gh run download → reproc_coverage_gate.py --sensor modis A64 → audit_localmag_ab.py →
criterios A66 C1/C2/C3 → si V-B pasa, flip operacional + reproc D12, A45 con OK explícito).
§2: aterrizar el A/B V750 (run 27468739388 ya completó: coverage gate → audit pareado → flip
enable_honest_anchor_viirs750 + promoción). RECORDÁ: A45 (el flip toca NRT → tag + OK Nicolás),
Nicolás revisa en el DASHBOARD no en código, A64 coverage gate, A48, A61, explicame como geólogo.
🔐 .netrc local Earthdata inválido (MODIS/reproc solo en Actions).
```
