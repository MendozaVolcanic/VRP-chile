# BLOQUE ARRANQUE S84

**Sesión previa**: S83 (2026-05-26). Cerró F-S81-A Fase 2 (A-simplificada)
implementación + PR #224 mergeado + workflow A/B disparado.

## Estado al cierre S83

- **PR #224 merged a main** SHA `eb68f8c4` ([link](https://github.com/MendozaVolcanic/VRP-chile/pull/224)).
- **Workflow A/B run [26465457074](https://github.com/MendozaVolcanic/VRP-chile/actions/runs/26465457074)** disparado 2026-05-26 17:52Z desde main.
  - Profiles: `mirova_equivalent_f_s81_a_intra_radio_{enabled,disabled}`.
  - Ventana: 2026-04-12 → 2026-05-26 (45d).
  - 11 Tier A × 2 profiles = 22 jobs, max-parallel 8.
  - Outputs: `data/mirova_equivalent_f_s81_a_intra_radio_{enabled,disabled}/<vol>.json`.
  - ETA: ~1-2h GH Actions.
- **Tag defensivo** `pre-s83-f-s81-a-gate-modis-path-d` apuntando al main pre-S83.
- **Operacional `mirova_equivalent` SIN cambio**: flag `ENABLE_PATH_D_INTRA_RADIO_GATE` default OFF. NRT cron 2h sigue corriendo legacy hasta adopción S84.
- **Tests**: 513 + 24 skipped + 10 nuevos = 0 regresiones.

## Hallazgo durable S83 (Fase 1b sanity)

El método "p95 ALERTA_TERMICA MODIS empírico" del design doc S82 colapsa al fallback `inner_radius_km` en 10/11 Tier A — solo Lascar tiene N≥10 ALERTAs MODIS (107 total: 75 CONS + 32 OCR, p95=2.0 km, max=2.24 km). Por eso A-simplificada: gate puro a `inner_radius_km` del KMZ MIROVA ya en `volcanoes.yaml`, sin script offline ni yaml patch.

Doc: `docs/F_S81_A_FASE1B_SANITY_P95.md`.

## Plan ejecutivo S84

### P0 — Cerrar Fase 2 (depende del run A/B terminado)

1. **Verificar run 26465457074 success**:
   ```bash
   cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
   git fetch origin --prune && git pull --ff-only
   gh run view 26465457074 --json status,conclusion,jobs | head -50
   ```
   Si conclusion != "success" → investigar jobs fallidos. Workflows reproc previos S60+ típicamente 11/11 success.

2. **Pull data A/B**:
   ```bash
   ls -la data/mirova_equivalent_f_s81_a_intra_radio_enabled/
   ls -la data/mirova_equivalent_f_s81_a_intra_radio_disabled/
   # Deberían existir 11 JSONs cada uno
   ```

3. **Escribir audit script** `experiments/_s83_f_s81_a/audit.py`:
   - Para cada Tier A × cada profile: contar records, contar TPs (vs ALERTA MIROVA en CSV consolidado ±60 min), FPs (records no-matched a ALERTA), calcular precision/recall/F1/ratio_med.
   - Tabla comparativa enabled vs disabled vs baseline operacional.
   - R3 cruzado: contar records con `final_hotspot_source='eruption'` y `pc.centroid_dist_km > inner_radius_km` en profile enabled (debe ser 0 o muy bajo).
   - Output: `experiments/_s83_f_s81_a/audit_results.md` + JSON tabla.

   **Umbrales paridad (docs/F_S81_A_FASE1B_SANITY_P95.md)**:
   - Precision MODIS Tier A: objetivo ≥0.70 (vs baseline ~0.4-0.5).
   - Recall vs ALERTA MIROVA: mantener ≥0.85 (Lascar, PCC summit).
   - FPs/vol-mes MODIS: ≤15 (vs actual 70-100).
   - R3: cero records 'eruption' con cluster fuera de inner_radius.

4. **Decisión adopción** (Task 7):
   - **Si todos los umbrales OK + ningún Tier A regresiona recall >5pp**: PR adopción a `pipeline/profiles/mirova_equivalent.yaml` agregar `enable_path_d_intra_radio_gate: true`. Tag `pre-s84-f-s81-a-adoption` antes (A45). Validar dashboard R8 post-deploy.
   - **Si recall cae**: NO adoptar. Documentar en `experiments/_s83_f_s81_a/regression.md`. Pasar a Fase 2.5 (combinar con cluster ≥4 px o cap Lascar específico).

### P1 — Fase 2.5 (si quedan FPs `summit` residuales)

Los 92 FPs `summit` (11% del audit Fase 1) están dentro de `inner_radius_km` y el gate NO los cubre. Si el audit S84 muestra que persisten:
- Opción B agregada: Path D MODIS requiere `primary_cluster.n_pixels ≥ 4` cuando cluster está fuera del cono inmediato (entre `inner_radius_km/2` y `inner_radius_km`).
- Cap Lascar específico: si residual entre 2.2 km (max ALERTA) y 5 km (inner) → cap a 2.5 km para Lascar solo.

Decisión: solo arrancar P1 si el audit S84 lo justifica empíricamente.

### P2 — Backlog pendientes pre-S83

- F46 completo VRP_TIR (Coppola 2024 Eq.16) — 14-16h. Ver `docs/F46_VRP_TIR_BUG_S76.md` + `docs/F46_VRP_TIR_GATE_S81.md`. PR #221 (provisional gate) ya merged S81.
- F66 Tasks 7-15 — branch `claude/s79-f66-hybrid-bg-gate` con Tasks 0-6 done (incluido fix regresión `compute_bg_stats` A49). 8-12h.
- NdC recall 0% investigación (4h granules VIIRS-I sub-pixel).
- Sesión data integrity dedicada (5-7h, `tasks/backlog_data_integrity_session.md`).

### P3 — Deuda técnica

- Tests sintéticos process_viirs core 14%→50% cobertura (4-6h).
- Regenerar golden records (2-3h).
- Worktrees huérfanos: `nostalgic-aryabhata`, `s70`, `s74`, `funny-mendeleev`, `hardcore-gauss` — decidir archivar.
- EARTHDATA_TOKEN expira 2026-07-20 — calendario rotación.

## Reglas vinculantes activas (recordatorio)

- **A45** tag defensivo + confirmación Nicolás antes de `pipeline/process_*.py`, `store.py`, `mirova_equivalent.yaml`.
- **A47** NO paralelo local sobre `data/mirova_equivalent/`. El A/B usa `data_subdir` aislados → OK.
- **A49** verificar `git diff` post-insert entre funciones (no comer return ni bloques adyacentes).
- **A50** cross-source verify `origin/main` antes de etiquetar "pre-existing".
- **A52** `git fetch + pull` en worktrees antes de asumir estado.
- **M1** cap PRs/sesión soft 12 hard 20.

## Comunicación

Hablarle a Nicolás como geólogo: fenómeno físico → mecanismo pipeline → fórmula al final. Cuando proponga adopción operacional, explicar primero qué hace el gate físicamente sobre el campo térmico, después por qué el audit valida.
