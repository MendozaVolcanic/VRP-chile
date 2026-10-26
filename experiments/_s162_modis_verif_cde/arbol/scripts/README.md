# scripts/ — utilities y reprocesos one-off

Inventario auditado S23 T20 (2026-04-26).

## Activos / útiles regularmente

| Script | Propósito | Sesión origen | Status |
|---|---|---|---|
| **`run_pipeline.py`** | Entry point del cron NRT y reprocesos manuales. Soporta multiprofile (`--profile`), volcán específico (`--volcano`), rangos de fechas. | S1 (core) | ✅ **CRÍTICO operacional** — usado por `.github/workflows/nrt.yml`. |
| **`verify_reproc.py`** | Auditoría post-reproceso (M2, S19): coefs NOAA-21 OK, exclusion zones aplicadas, records sospechosos, cobertura sensores. | S19 | ⚠️ Útil pero raramente invocado. Recomendable correr manualmente después de cualquier reproceso. |
| **`vault_link_papers_to_project.py`** | Agrega `proyecto: "[[VRP Chile]]"` al frontmatter de papers Vault. Idempotente (S21). | S21 | ✅ Re-correr cuando se procesen papers MIROVA nuevos. |

## Scripts de reproceso/migración histórico (legacy, conservar)

Estos son artefactos de sesiones específicas. Funcionaron, hicieron su trabajo,
y se preservan como evidencia + posibilidad de re-uso si surge necesidad similar.

| Script | Sesión | Función original | Status |
|---|---|---|---|
| `backfill_nov_2025.py` | S14 | Re-descarga histórico noviembre 2025 contra OSF. | Legacy. Re-uso si surge gap histórico. |
| `clean_feb_p32_only_artifacts.py` | S15 | Limpieza records P3.2 que se aplicaron mal. | Legacy. Específica de bug S15 ya resuelto. |
| `convert_mirova_csv.py` | S12 | Convertir CSV MIROVA a JSON para frontend. | Útil — reusable si se actualiza CSV ground truth. |
| `daytime_p31_validation.py` | S15 | Reproceso diurno combinado P3.1+P3.2. | Legacy. P3.1/P3.2 ya validados o documentados. |
| `e1_reprocess.py` | S16 | Reproceso E1 (profile `s9_vent_permissive`) para refutar H1. | Legacy. H1 refutada en S17. |
| `migrate_scope_to_mirova_only.py` | S15 | Tema E cleanup scope — migrar 34 no-Tier-A a `data/archive/`. | Legacy. Una sola corrida exitosa. |
| `normalize_data.py` | S12 | Normaliza campos JSON antiguos al schema actual. | Legacy si el schema no cambia. |
| `overnight_p32_validation.py` | S15 | Reproceso nocturno P3.2 autonomo. | Legacy. |
| `rebuild_mirova_from_consolidado.py` | S14 | Rebuild `data/mirova/` desde CSV consolidado. | Útil si se rehacen las refs canónicas. |
| `rebuild_mirova_lascar.py` | S11 | Reproceso Lascar específico contra OSF v2.5. | Legacy. |
| `reprocess_bbox_beneficiarios.py` | S15 | Reproceso Llaima + Copahue con bbox ROI. | Legacy. |
| `validate_lascar_vs_mirova.py` | S12 | Validador Lascar contra refs MIROVA. | Útil — patrón replicable para otros volcanes. |

## Cuándo invocar cada script

**Cron NRT (automático)**: solo `run_pipeline.py`.

**Reproceso histórico manual**:
1. `run_pipeline.py --profile X --volcano Y --start ... --end ... --overwrite`
2. `verify_reproc.py` (post-reproceso, M2 sanity)
3. (opcional) Forense replicable: `experiments/forense_h17_replicable.py`

**Auditoría papers**:
- `vault_link_papers_to_project.py` cuando hay papers nuevos.

**Resto**: invocar bajo demanda específica de la sesión que documente la
intención (ej: nuevo backfill histórico, nueva limpieza artifact-driven).

## Política de mantenimiento

- **Activos**: actualizar tests + docs cuando cambien.
- **Legacy**: NO mantener activamente. Si surge bug, decidir entre fix+test
  vs deprecar definitivamente.
- **Nuevo script**: agregar entrada a esta tabla con sesión + propósito antes
  de commitear.
