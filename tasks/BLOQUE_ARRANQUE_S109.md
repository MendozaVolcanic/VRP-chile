# BLOQUE ARRANQUE S109

**Sesión S108 (2026-06-13/14)** — aterrizó §3 ancla honesta V750 COMPLETA (11 Tier A, live)
+ auditó el dashboard (0 bugs) + bloque autónomo 6h que **REFUTÓ el fix §2 de magnitud MODIS**.
Registro completo: `project_s108_estado` (memoria) + `docs/AUDIT_S108_AB_MODIS_VEREDICTO.md`.

## §0 — Primer comando
```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
git fetch origin --prune && git pull --ff-only
cat docs/AUDIT_S108_AB_MODIS_VEREDICTO.md     # por qué el fondo-local no cura
cat experiments/_s107_modis_localmag/PREVERDICT_NOTES.md  # clasificación inflados + flip §1
# estado del A/B §2 que quedó corriendo (confirmar refutación con 6 vols):
gh run view 27480234385 --json status,conclusion
```

## ✅ Cerrado en S108
- **§3 ancla honesta V750 COMPLETA (11 Tier A, LIVE)** — PR #416 (flip) + #417 (promoción
  5+6 + display dist=cráter). Dashboard republicado. Tag `pre-s108-honest-anchor-v750`.
- **§4 Auditoría dashboard**: SANO, 0 bugs (`docs/AUDIT_S108_DASHBOARD.md`). Display
  `dist=0.0 → "cráter"` (cierra P2.3/D11-bis).
- **Estado global vs MIROVA** (`docs/AUDIT_S108_ESTADO.md`): gap mayor = MODIS summit-gated
  recall 10.8% (D12). Ratio VIIRS ~0.5× (frente candidato).
- **A/B §2 magnitud MODIS REFUTADO (preliminar)**: el fondo-local de corona NO cura los
  inflados (Chaiten 0/37, los empeora; corona más fría que el fondo regional). Flag OFF, no
  tocó producción. §1 flip ancla MODIS BLOQUEADO sin cura de magnitud.

## §1 — PRIORIDAD S109: replanteo del enfoque de magnitud MODIS (MISSION/brainstorming)
**Decisión Nicolás S108: "partimos con eso en otra sesión".** El fondo-local está refutado
con datos → hace falta OTRO enfoque. **Es decisión metodológica (MISSION) → brainstorming
con Nicolás + papers-first ANTES de implementar.**
- **Diagnóstico raíz** (no re-derivar): los inflados MODIS son **clusters AL CRÁTER**
  (dist 1-3 km) con ΔT bajo (~10K, sub-pixel); la magnitud se infla porque el **cluster
  MODIS incluye el campo difuso de 1km que NO es foco real**. MIROVA casi no publica MODIS
  (solo Lascar, 81) → no hay foco MODIS resoluble en los otros 10. El problema NO es el
  fondo (fondo-local refutado), es la **selección/composición del cluster**.
- **Candidatos a explorar** (papers-first: BIBLIOGRAPHY_SYNTHESIS + Coppola 2016a/2024):
  (a) exigir un foco real (ΔT umbral) al cluster MODIS antes de reportar magnitud;
  (b) co-validación cross-sensor (VIIRS confirma el foco — el 93% del destape §1 ya está
  cross-confirmado por VIIRS); (c) cap físico de magnitud; (d) revisar qué píxeles entran
  al cluster (excluir campo difuso). Cada uno pasar las 3 preguntas de MISSION.md.
- **Por qué importa**: desbloquea §1 (flip ancla MODIS) → cura el gap recall summit-gated
  10.8%→~96% (D12 Láscar). El flip recupera 93% señal real cross-confirmada (NdC = caso
  especial, MIROVA 0, probable ruido — investigar con ground truth/TIF antes).

## §2 — A/B §2 CONFIRMADO DEFINITIVO (run 27480234385, 36/36 success)
Completó al cierre de S108: **footprint 4% / ring 20% inflados curados** (<<85%) en los 6
vols → **fix §2 REFUTADO definitivo**, NO adoptar (Tupun 0/18 en ambos brazos, A19; el
brazo recomendado footprint es el peor). C1 detección intacta (0 det-diffs en granules
COMUNES), C3 Lascar preservado. Ver `AUDIT_S108_AB_MODIS_VEREDICTO.md`. **Ya confirmado —
S109 arranca DIRECTO con §1 (replanteo del enfoque de magnitud).**

## §3 — (Opcional) frente magnitud VIIRS ~0.5×
`ratio_viirs_cons_vs_ocr.py`: sub-estimación real ~0.5× (CONS+OCR), dentro de paridad pero
objetivo →1.0. Causa: área nadir / fondo Test1 / cluster-vs-suma (NO coef Wooster). Resolver
método de agregación (por-pasada vs S103) antes de accionar.

## 🔑 Reglas vivas S109
- **A-rules candidatas a formalizar (revise-claude-md)**: (1) el fondo-local NO generaliza
  para curar magnitud MODIS (corona/vecindad puede ser más fría → infla); (2) A/B con brazos
  en reprocs SEPARADOS = ruido de cobertura NASA → comparar detección en granules COMUNES;
  (3) ratio de magnitud depende del método de agregación; (4) flip ancla MODIS = alto impacto
  (~2476 destape), no solo D12.
- **A45**: cualquier flip operacional (ancla MODIS, nuevo fix magnitud) → tag + OK Nicolás.
- **MISSION 3-preguntas** antes de implementar cualquier enfoque de magnitud MODIS.
- **A26** calidad>tokens. **A62** adversarial. **A47** no reproc paralelo mismo data_subdir.
- Dirty pre-sesión en `experiments/_s9*` (de antes, no commitear). Scratch S108 en
  `experiments/_s107_modis_localmag/` + `_s94_audit/ratio_*` (committed, reproducibles).

## Prompt copy-paste S109
```
Sesión S109 — VRP Chile. Sincronizá (git fetch origin --prune && git pull --ff-only) y leé
tasks/BLOQUE_ARRANQUE_S109.md + project_s108_estado (memoria) + docs/AUDIT_S108_AB_MODIS_VEREDICTO.md.
S108 dejó §3 ancla V750 COMPLETA y live (11 Tier A), auditó el dashboard (0 bugs + display
dist=cráter), y REFUTÓ con datos el fix §2 de magnitud MODIS (fondo-local de corona no cura los
inflados — la corona es más fría que el fondo regional → magnitud sube; Chaiten 0/37). PRIORIDAD
§1: replantear el enfoque de magnitud MODIS — es decisión metodológica (MISSION), así que
BRAINSTORMING + papers-first ANTES de implementar. Diagnóstico raíz: el cluster MODIS incluye el
campo difuso de 1km que no es foco real (MIROVA no ve foco MODIS salvo Lascar). Candidatos: exigir
ΔT al cluster, co-validación cross-sensor VIIRS (93% del destape ya cross-confirmado), cap físico,
o revisar qué píxeles entran al cluster. Curar la magnitud desbloquea el flip ancla MODIS → cura
el gap recall summit-gated 10.8%→~96% (D12 Láscar). RECORDÁ: A45 (flip → tag + OK), MISSION
3-preguntas, A62 adversarial, explicame como geólogo. El A/B §2 (run 27480234385) ya completó
al cierre de S108: REFUTADO definitivo (footprint 4% / ring 20% inflados curados en los 6 vols).
```
