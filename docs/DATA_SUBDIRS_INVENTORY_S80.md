# Inventario data/ subdirs S80

> Auditoría S80. 696 MB en 41 subdirs A/B aislados acumulados desde S44.
> No se prune en S80 (sin urgencia de espacio). Documentado para decisión futura.

## Subdirs operacionales (NO TOCAR)

| subdir | tamaño aprox | propósito |
|---|---|---|
| `data/mirova_equivalent/` | — | **NRT operacional**. Dashboard publica desde aquí. |
| `data/mirova_reference/` | 0 | Vacío, placeholder histórico |
| `data/mirova/` | 22 archivos | Referencia legacy pre-S29 |
| `data/experimental/` | — | Profile experimental general |
| `data/archive/` | 46 archivos | Backup histórico |

## Subdirs A/B aislados (drifts S46) — 367 MB

Outputs de A/B tests S46 sobre drifts Coppola 2016a:

| subdir | MB | drift testeado | estado |
|---|---|---|---|
| `_baseline_s44` | 28 | Baseline pre-driftN | ✅ ref histórico (mantener) |
| `_coppola_full` | 15 | drifts 1ab+234+7 todos ON | Validado S46, no operacional |
| `_drift1a_only` | 28 | Test1 K1 retire from hot_mask | Refutado/diferido |
| `_drift1ab_only` | 28 | Test1 K1 retire + bg exclude | Refutado/diferido |
| `_drift1b_only` | 28 | Test1 K1 bg exclude only | Activable manualmente (`ENABLE_TEST1_K1_BG_EXCLUDE`) |
| `_drift234_only` | 15 | Drift 2+3+4 combo | Validado S46 |
| `_drift23_dual_only` | 12 | Drift 2+3 dual ROI | Validado S46 |
| `_drift23_only` | 19 | Drift 2+3 only | Validado S46 |
| `_drift4_only` | 23 | Drift 4 (NTI relativo) | Refutado (Path B no dispara Andes) |
| `_drift7_*` (3 subdirs) | 82 | Drift 7 MODIS/VIIRS local p95 threshold | Diferido D7 |
| `_no_bt_path` | 13 | sin BT path | Validado (no degrada) |
| `_dibella_n12_viirs_only` | 19 | 12σ noche Di Bella (NO MIROVA) | Refutado |

**Recomendación**: archivable a `data/_archive_drifts_s46/` o eliminar tras
backup S3/Google Drive. Estos outputs son reproducibles desde tags S46.

## Subdirs R2 pixel-level (S31-S44) — 109 MB

Outputs A/B de calibración R2 pixel-level Driver A+B:

| subdir | MB | param | estado |
|---|---|---|---|
| `_r2_C1_001_summit` | 18 | C1=0.001 vs default 0.003 | Validado (C1=0.003 mejor) |
| `_r2_C2_3_summit` / `_4_summit` / `_8_summit` | 46 | C2 override sweep | Validado (C2=4 mejor) |
| `_r2_baseline_drift234` | 15 | Baseline post-S46 drift234 | Ref |
| `_r2_drift234_modis_only` / `_viirs_only` | 15 | Sensor isolation | Ref |
| `_r2_drift4_alone` | 15 | Drift 4 R2 ablation | Refutado |
| `_r2_uniform_no_dual` | 15 | dual_roi disabled | Refutado (dual mejor) |

**Recomendación**: archivable. Resultados consolidados en
`experiments/87_results.md` (S46 Ronda 1).

## Subdirs D8 vent-anchored (S32-S44) — 90 MB

| subdir | MB | estado |
|---|---|---|
| `_d8_combo_full` / `_disabled` | 26 | Validado ON operacional |
| `_d8_d4_per_vol` | 13 | Validado |
| `_d8_vent_anchored` / `_disabled` | 38 | Validado ON operacional |

**Recomendación**: mantener `_d8_vent_anchored` como referencia, archivar resto.

## Subdirs misceláneos — 130 MB

- `_local_kernel_bg_enabled` (20 MB, S60-S65 validación adopción)
- `_h_d8_5_full` / `_disabled` (26 MB, H_S33 D8/D5 combo)
- `_h8_pixel_filter_*` (14 MB)
- `_p3_1_*`, `_test1_*`, `_dual_roi_bt_*` (16 MB, incompletos parciales)
- `_mirova_literal` (78 MB, modo paridad estricto)
- `_mirova_legacy` (4 MB)

## Subdirs experimentales sueltos

- `low_vent_cap/`, `nsigma_mir_*`, `s9_vent_permissive/`, `backups_pre_scanfix/`

## Decisión S80

**No pruning destructivo en esta sesión.** Razones:
1. Espacio no apremia (696 MB sobre repo de 1.5 GB total)
2. Algunos subdirs son referencia auditable para futuras decisiones
3. Tag defensivo `pre-s80-consolidation` cubre rollback si se decidiera pruning
4. La regla M4 (audit trimestral) reevaluará en S100

**Para pruning futuro**:
```bash
# Backup defensivo
git tag pre-s100-data-prune origin/main
tar -czf data_drifts_s46_backup.tar.gz data/_drift*/ data/_r2_*/ data/_d8_*/
# Mover a S3 / OneDrive / Drive
# Después:
rm -rf data/_drift*/ data/_r2_*/ data/_d8_*/  # excepto _d8_vent_anchored
```

**Crítico**: NUNCA tocar `data/mirova_equivalent/` ni `data/mirova/` sin
respaldo. NRT consume el primero, el segundo es referencia legacy.
