# Backlog S27 (descubierto durante implementación, no en plan original)

## 7 golden records desfasados con metodología MIROVA literal

**Origen**: el commit `S27 dashboard — sobrescribir 10 Tier A con MIROVA literal 90d`
sobrescribe `data/mirova_equivalent/{Lascar,Lastarria,Tupungatito,...}.json` con
records reprocesados bajo `_mirova_literal` (sin parches). Los tests
`tests/test_golden_records.py` validan valores específicos que reflejan la
metodología vieja (con vent-path, cap=7K, exclude_zones).

**Tests afectados** (7):
- `test_golden_record_present[tupungatito_regla_d_edge_no_coords_2026_01_08]`
- `test_golden_record_values[lascar_strong_summit_noaa21_2026_04_12]`
- `test_golden_record_values[lascar_summit_noaa21_2026_04_08]`
- `test_golden_record_values[chaiten_vent_summit_v750_2026_04_12]`
- `test_golden_record_values[tupungatito_vent_subpixel_noaa21_2026_04_08]`
- `test_golden_record_values[tupungatito_regla_d_modis_2026_04_16]`
- `test_golden_record_values[lastarria_path_d_contextual_viirs_2026_04_08]`

**Por qué fallan**:
- Records de vent-path (chaiten_vent_summit_*, tupungatito_vent_subpixel_*) ya no
  existen en JSON literal porque `enable_vent_path: false`.
- Records de Regla D (regla_d_edge, regla_d_modis) ya no aplican porque
  `enable_test1_path: false` y `enable_dnti_dual_roi: true` se aplica diferente.
- Records con NTI/dNTI específico (path_d_contextual_viirs) tienen valores
  ligeramente distintos sin cap=7K.

**Decisión** (no fixear en S27):
1. Estos tests están atados a la metodología operacional pre-S27. La nueva
   data en `mirova_equivalent/` es metodología literal — los goldens están
   midiendo la cosa equivocada.
2. Eliminar los goldens significa perder cobertura sobre esos casos físicos
   específicos. NO hacerlo.
3. Reescribir los goldens con valores literal es lo correcto, pero requiere:
   - Verificar que los nuevos records son correctos físicamente (no solo
     "lo que sale del pipeline").
   - Decidir si vent-path goldens (que ya no existen) se reemplazan con
     casos equivalentes de NTI/dNTI o si se borran sin reemplazo.
   - ~30-60 min de trabajo cuidadoso.

**Próxima sesión (S28)**:
- Revisar caso por caso los 7 goldens.
- Reemplazar valores con MIROVA literal o documentar por qué se eliminan.
- Re-correr suite: target 191/191 verde.

**Workaround temporal**: los goldens NO bloquean el dashboard. El push del
S27 procede aunque suite tenga 7 fallos. NRT cron sigue corriendo OK porque
no usa esos tests.

## NdC fallo persistente NASA Earthdata transient

4+ fallos consecutivos en NevadosDeChillan en runs distintos del workflow
`reproc-mirova-literal-extend.yml`. Patrón: el runner asignado a NdC al inicio
del job no tiene conectividad a urs.earthdata.nasa.gov.

Hipótesis para S28:
- ¿Race condition con max-parallel=8 saturando el endpoint de auth?
- ¿Runner pool específico de GitHub Actions con problema regional?
- ¿Algo en el orden alfabético del matrix que asigna NdC al runner problemático?

**Mitigación inmediata** (S27): workflow `reproc-ndc-retry.yml` lanzado
2026-04-29. Si ese también falla, NdC mantiene data pre-S27 (no es Tier A
primario, calibración secundaria).

## _mirova_legacy.yaml borrado en T7 cleanup

Cumplido en S27. El `_mirova_literal.yaml` se mantiene como infraestructura
para H_S27_1 a H_S27_4 (próximas sesiones).
