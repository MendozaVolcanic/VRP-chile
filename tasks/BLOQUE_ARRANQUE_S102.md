# BLOQUE ARRANQUE S102

**Sesión previa S101 (2026-06-05).** MUY larga. 1 PR (#345). Cerró §1 magnitud (Llaima
ctxpeak promovido por union) y **diseñó el frente MODIS** (brainstorming + auditoría
6-ejes + 5 pruebas de descarte). Registro: `project_s101_estado` (memoria). Design doc:
`docs/superpowers/specs/2026-06-05-frente-modis-campo-difuso-design.md`.

## §0 — Primer comando
```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
git fetch origin --prune && git pull --ff-only
```

## §1 — PRIORIDAD: revisar el design doc del frente MODIS (gate brainstorming)
Nicolás debe **revisar** `docs/superpowers/specs/2026-06-05-frente-modis-campo-difuso-design.md`
antes de implementar. Lo esencial ya establecido y VERIFICADO en S101:
- **Target MIROVA-MODIS** (`experiments/_s99_audit/modis_diffuse/characterize_target.py`):
  ≤4 MW al cráter, casi solo Láscar (78). PCC/Tupun = 0 en 5 meses. Nuestro pipeline 342/133.
- **TIF de MIROVA**: en MODIS no hay foco al cráter ni en Láscar → señal real en VIIRS375.
- **TODOS los discriminantes post-hoc descartados con datos** (térmico/dispersión/co-validación).
  No hay cura de display (schema no persiste píxeles del cluster, A46/A07).
- **Causa raíz = 2 palancas de pipeline**:
  1. **sec³(θ)** (`ENABLE_NADIR_FIXED_PIXEL_AREA_MODIS` default False = sec³ ON). MIROVA
     usa nadir-fijo. Vols del sur off-nadir → infla 3-5×. Clon literal = nadir-fijo PERO
     exige re-validar WOOSTER_COEFF vs OSF (A63, no toggle inocuo).
  2. **path D detección** del campo difuso (dNTI ctx + second-pass).
- **Acople #1↔magnitud**: 88/110 inflados ocultos hoy por distance_class="far" corrupto;
  arreglar #1 (deriva del hotspot suelto, no del cluster; S98 lo dejó pendiente) los DESTAPARÍA
  → magnitud primero/junto.

### Primer paso de implementación recomendado (cuando Nicolás dé OK — A45):
**Medir la palanca sec³** con un reproc A/B `enable_nadir_fixed_pixel_area_modis` ON/OFF
(GH Actions, MODIS no corre local). Cuantifica cuánto del inflado es sec³ off-nadir ANTES
de tocar calibración. Si es la mayor parte → evaluar nadir-fijo + re-validar WOOSTER_COEFF.
Decisiones abiertas en §9 del design doc.

## §2 — Pasivos
- **R8 Llaima**: verificar en Diario live (post #345 deploy) que abr-may muestra ctxpeak.
- **§3 ramas stale (76 claude/sNN-*)**: decisión S101 = dejar para revisión posterior.
  Cuando se haga: podar solo las mergeadas (cero riesgo), revisar no-mergeadas aparte.

## Tags defensivos S101
Ninguno nuevo (no se tocó pipeline). El frente MODIS los necesitará al implementar
(`pre-s102-modis-*` antes de cualquier edit a process_modis.py — A45).

## Worktree canónico
Raíz `VRP Chile/` en main al día.
