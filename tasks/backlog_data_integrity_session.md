# Sesión dedicada Data Integrity — pendiente (creado S81 2026-05-26)

**Trigger**: Nicolás S81 explícito al diferir A.3 dedup PCC + endurecer
`store.upsert_record`. Quoting: "vamos con 3 [documentar como deuda y saltar]
pero recuerda la sesion de data integrity".

## Scope

Sesión enfocada en data integrity de `data/mirova_equivalent/`:

### Items confirmados a abordar

1. **Dedup PCC duplicados** — 15 filas en `data/mirova_equivalent/PuyehueCordonCaulle.json`
   entre 2026-05-18 y 19, 7 con datos divergentes (vrps `[113.84, 309.99,
   113.84]`, `distance_class` `[far, summit, far]`). Causa: overlap reproc
   S62 dos commits sobre mismo rango sin dedup. Script puntual + tag
   defensivo. 15 min.

2. **Endurecer `pipeline/store.py::upsert_record`** — agregar dedup key
   `(datetime_utc, sensor, granule)` o `(datetime_utc, sensor,
   final_hotspot_lat, final_hotspot_lon)`. Si key existe → overwrite, no
   append. Test sintético `tests/test_store_dedupe.py`. A45 confirmación
   antes de tocar. 30 min. Requiere tag `pre-data-integrity-store-dedupe`.

3. **`vrp_mw=0` con `n_anomalous_pixels>0`** — 2117 records (16% del
   corpus). Sin flag de razón. Agregar `vrp_zero_reason ∈ {diurnal,
   mir_only_fail, all_excluded, ...}` al schema. Auditar si NdC 400 records
   afectados son orbitas diurnas legítimas o señal perdida. 2-3h.

4. **`n_hotspots_clustered > n_anomalous_pixels`** — 228 records físicamente
   imposible. Leer `pipeline/scan_geometry.py` clustering, documentar
   invariante en docstring, agregar assert/test. PP+Lastarria concentran
   100. 1-2h.

5. **σ_bg outlier patológico** — Lastarria 2026-04-23 01:50 MODIS_TERRA
   `diag_sigma_bg_k=149.18K`, fisicamente imposible (esperado 3-15 K).
   Agregar guard en `compute_bg_stats` (assert σ<50K) + test sintético.
   Detectaría granules corrupted. 30 min.

6. **Schema gaps `diag_*`** — 10/13207 records (0.08%). Bug residual
   H_S21_11. Aceptable, pero mientras estamos limpiando vale el sweep.

7. **Regla M11 en `docs/META_RULES_S80.md`** — agregar: "Reprocesos
   manuales del mismo volcán × rango temporal no se lanzan en ventanas
   <24h sin verificar git log primero. Si hay segundo reproc necesario,
   cancelar el primero o esperar a su merge". Causa raíz del damage PCC
   fue humana, no race CI. 15 min.

### Pre-requisitos para arrancar

- A45 confirmación Nicolás explícita en sesión.
- Tag defensivo `pre-data-integrity-session-<date>` antes del primer commit.
- Worktree dedicado o branch dedicada `claude/data-integrity-fixes`.
- Suite verde 507+/0 antes de arrancar.

### Estimado total

~5-7h en una sesión enfocada. Items 1+2+5+7 son los core (~2h); items 3+4
son investigación más profunda que puede diferirse a segunda sesión.

### Por qué se difirió en S81

S81 priorizó cierre de hallazgos críticos visibles (gate VRP_TIR público,
mirova_center PCC para R2). Data integrity es interna — no expone bug al
operador / Nicolás / SERNAGEOMIN. Es deuda real pero no urgente.

### Lectura previa al arrancar

- `docs/AUDIT_INTEGRAL_S81.md` frente #3 + #12 (hallazgos completos)
- `memory/reference_mirova_csv_scraper_tags.md` (interpretación correcta tags CSV)
- Commits PCC reproc overlap: `1cd3da8d`, `2cf6c9ac`
- `docs/META_RULES_S80.md` (donde agregar M11)
