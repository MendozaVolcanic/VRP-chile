# Workflows archivados — S70-1 T6 (2026-05-20)

Los workflows en este directorio son **experimentales A/B históricos** de sesiones S24-S40 del proyecto VRP Chile.
Todos están **archivados** porque sus features fueron:
- adoptadas en el perfil `mirova_equivalent` operacional, o
- refutadas durante el A/B y el código revertido, o
- one-shot operacional ya consumido (retry single-vol post-timeout).

**GitHub Actions ignora subdirectorios** de `.github/workflows/`, así que estos archivos NO se ejecutan
ni aparecen en la lista de "Workflows" del repo. La limpieza es funcional sin riesgo de re-ejecución.

## Por qué archivar en lugar de borrar

Historia metodológica: cada workflow representa un A/B real con data, profile dedicado y decisión documentada.
Mantenerlos accesibles facilita auditoría retroactiva si surge la pregunta "qué se probó y por qué se descartó".
Borrarlos perdería la traza de las hipótesis exploradas (H_D8_*, H8, P3.1, Test 1, etc.).

## Lista archivada (14 archivos)

| Workflow | Sesión origen | A/B testeaba | Estado |
|---|---|---|---|
| reproc-villarrica-test1.yml | S26 | Test 1 integrated-ROI (Coppola 2015 §2.2 Eq.1) sobre Villarrica solo, profile dedicado | Adoptado en mirova_equivalent S33+ |
| reproc-villarrica-test1-refs.yml | S26 | Variante del anterior — reproc solo días con refs MIROVA Villarrica (5 ventanas paralelas) | Adoptado vía test1 path |
| reproc-no-bt-path-15d.yml | S40 | Desactivar `bt_path_hot` y medir delta recall vs operacional (cleanup paths) | Refutado/decisión pendiente — bt_path mantenido |
| reproc-ab-p3-1.yml | S24 | P3.1 dual-ROI thresholds Coppola 2016a Table 2 (summit c1=0.003 vs scene c1=0.010) | Adoptado en mirova_equivalent (enable_dnti_dual_roi=true) |
| reproc-ab-test1.yml | S25 | A/B Test 1 integrated-ROI vs control, 4 vol (Villarrica + 3 controles) | Adoptado vía enable_test1_path=true |
| reproc-ab-test1pix-filter.yml | S32 | Driver B — filtro N·σ pixel-level (5σ summit / 10σ scene) sobre mask Test 1 antes de sumar VRP | Refutado S33 (bug mirovaEqVrp causó adopción auto-confirmatoria, revertido) |
| reproc-d8-d4-per-vol-15d.yml | S39 | Combo vent_anchored + D4 per-volcano (lbg_global_compatible) en Lascar+Lastarria 15d | Reemplazado por reproc-ab-lbg-global.yml (más reciente, activo) |
| reproc-ab-d8-combo.yml | S38 C.1 | Combo full D8 vent_anchored + H8 pixel filter + D4 lbg_global | Combo refutado; D8 vent_anchored adoptado solo |
| reproc-ab-d8-vent-anchored.yml | S38 | D8 verdadero — cluster_hotspots(strategy="vent_anchored") prioriza inner_radius | Adoptado en mirova_equivalent (enable_vent_anchored_clustering) |
| reproc-ab-h-d8-5.yml | S37 | H_D8_5 algoritmo MIROVA literal (ETI cuadrático scene-wide + second-pass + sum VRP) | Refutado empíricamente (delta TP=0 todos Tier A) — bug era cluster selection, no detección |
| reproc-ab-h8.yml | S35 | H8 pixel-level distance filter en store.append_record (descartaba anomaly_pixels si hotspot fuera radius) | Adoptado vía enable_pixel_level_distance_filter |
| reproc-ndc-retry.yml | S27 | Single-volcano retry NASA Earthdata transient outage (originalmente NdC, generalizado) | One-shot operacional reutilizable — reemplazable por `gh workflow run nrt.yml -f volcano=X` |
| reproc-vent-anchored-30d-preview.yml | S38 Bloque B | Reproc 30d preview pre-adopción operacional sobre _d8_vent_anchored | Pre-adopción ya completado — vent_anchored adoptado operacional |
| reproc-failed-tier-a.yml | S26 | Re-correr Chaitén/Villarrica/Lascar fallidos por timeout 220min en run 24994055814 (2 chunks paralelos) | One-shot S26 ya consumido |

## Lista archivada S73 cleanup F2.8 (20 archivos, 2026-05-23)

Audit S73 F2.8 confirmó que estos workflows ya cumplieron su propósito (features adoptadas/refutadas/cerradas documentado en `MEMORY.md` y `MIROVA_DIVERGENCES.md`):

| Workflow | Sesión | A/B testeaba | Estado |
|---|---|---|---|
| reproc-ab-mirova-literal.yml | S27 | Mirova-literal A/B | Cerrado |
| reproc-ab-local-kernel-bg.yml | S58 | Kernel-bg global | Adoptado per-vol |
| reproc-ab-local-kernel-bg-pp.yml | S61 | PP kernel-bg | Adoptado |
| reproc-ab-lastarria-tupungatito.yml | S62 | Lastarria/Tupungatito kernel-bg | Lastarria adoptado; Tupungatito refutado |
| reproc-ab-chaiten.yml | S63 | Chaiten kernel-bg | Adoptado |
| reproc-ab-pcc-kernel.yml | S63 | PCC kernel-bg | Adoptado |
| reproc-ab-dual-roi-bt.yml | S26 | Dual-ROI BT fix | Adoptado en main |
| reproc-ab-lbg-global.yml | S33 D4 | lbg_global_compatible | Refutado empíricamente |
| reproc-ab-phase2.yml | S33 | Driver B Phase 2 | Revertido (bug mirovaEqVrp) |
| reproc-ab-path-d-atm-gate.yml | S71 D9-A | Path D atm gate | Cerrado S72 |
| reproc-ab-path-d-covalidation.yml | S71 D9-B | Path D co-validation | Cerrado S72 |
| reproc-ab-path-d-cap.yml | S71 D9-C | Path D cap | Adoptado vía S71 cap |
| reproc-ab-bt-path-on-v1.yml | S72 F2.6.e | bt_path_on reactivation | Refutado empíricamente |
| reproc-ab-no-cap-v1.yml | S72 F2.6.b | No-cap S71 | Falsa alarma cerrada |
| reproc-ab-test1-retire-only.yml | S72 F2.3 | Test 1 retire only | Cerrado |
| reproc-ab-unsuitable-only.yml | S72 F1.2 | Unsuitable filter only | Cerrado |
| reproc-ab-unsuitable-filters.yml | S72 F2.4 | Unsuitable filters combo | Cerrado |
| reproc-s46-coppola-literal-ab.yml | S46 | Coppola literal A/B | Cerrado |
| reproc-mirova-literal-extend.yml | histórico | Mirova-literal extend | Completado |
| reproc-villarrica-refs.yml | histórico | Villarrica refs scrape | Completado |

## Cómo restaurar uno si se necesita

```bash
git mv .github/workflows/_archive/<nombre>.yml .github/workflows/
git commit -m "Restaurar workflow <nombre> para [razón]"
```

GitHub Actions detectará el workflow automáticamente cuando vuelva al directorio raíz.

## Referencia

- `tasks/plan_s70_1.md` Task 6 (esta tarea de archivado)
- Audit S70-0 final reviewer (PR #103) — lista de 14 candidatos
- `docs/SESSION_INDEX.md` — sesiones S24-S40 contexto histórico
- `docs/MIROVA_DIVERGENCES.md` — drifts adoptados/refutados consolidados
