# Detección diurna MODIS — implementación + validación A/B (S90)

**Rastro metodológico para el paper.** Cierra la divergencia "MIR solo nocturno"
replicando la detección diurna MODIS documentada en MIROVA core.

## Provenance de parámetros (verbatim, MIROVA core)

Coppola 2016a SP426.5 Tabla 1 (`documentacion/sp426_5.txt:317-343`), confirmado
Coppola 2024 cap.11 Tabla 2 (`coppola2024_chapter.txt:1033-1037`):

| Parámetro | Noche | Día |
|---|---|---|
| K1 (NTI fijo, Test 1) | −0.8 | **−0.6** |
| C1 (dNTI/dETI contextual) | 0.003/0.010 (summit/scene) | **0.02** (ambos) |
| C2 (N·σ contextual) | 5σ/10σ (summit/scene) | **15σ** (ambos) |

MIROVA NO corrige el sol ni cambia de banda — sube umbral (15σ) + endurece K1
(−0.6). VIIRS se mantiene **nocturno**: ningún paper MIROVA core publica VIIRS
diurno (el n=8 es Di Bella 2024, INGV Catania, NO MIROVA — regla A9).

## Motivación (auditoría S90)

Las anomalías MÁS grandes que perdíamos en NdC/Villarrica eran pasadas diurnas
MODIS (NdC 1.06 MW 2026-03-17 13:15UTC solar 08:30; Villarrica 1.83 MW
2026-05-29 19:55UTC solar 15:06) — excluidas por el gate `store.py` (rechaza
solar elev>0). Ver `experiments/_s90_audit/RESULTS.md`.

## Implementación (PR #257, flag default OFF)

- `profile.py`: `NTI_K1_DAY=-0.6`, `N_SIGMA_MIR_DAY=15.0`, `DNTI_CONTEXTUAL_C1_DAY=0.02`, `ENABLE_DAYTIME_MODIS` (default False).
- `process_modis.py`: `_select_thresholds(is_day, enable_day)` + `_scene_is_day(filename, lat, lon)` (elevación solar de la pasada). `calculate_vrp` aplica el set vía rebinding local (los ~20 call-sites toman día/noche sin editarlos — scoping Python, A49-safe).
- `store.py`: `_reject_daytime` — MODIS diurno pasa con flag ON, VIIRS diurno SIEMPRE rechazado.
- Perfiles A/B `_daytime_modis_{enabled,disabled}` (data_subdir aislado).
- Tag defensivo `pre-s90-daytime-modis` @2f3f73aa (A45).
- TDD: `tests/test_daytime_modis.py` (4 tests). Suite 612 passed, **0 regresiones** (flag OFF = baseline).

## Validación A/B (Task 8 — gate de adopción, regla S33)

Workflow: `.github/workflows/reproc-daytime-modis-ab.yml` (matrix enabled vs
disabled, MODIS en GH Actions Linux por pyhdf).

**Run dispatched**: NevadosDeChillan 2026-03-01→2026-04-30 (run 26687718294).
Pendiente: Villarrica 2026-05-01→2026-05-30.

**Criterios de adopción** (NO setear `enable_daytime_modis` en operacional sin esto):
1. Recall diurno-MODIS sube en ≥1 vol vs disabled (computeMetrics).
2. Precisión global NO cae bajo 0.50 donde ya se medía (FP solares acotados).
3. ≥1 evento diurno validado pixel-level (R2) contra TIF MODIS MIROVA (NdC: 47 TIFs, PR #254).
4. R3: las nuevas TP diurnas matchean ALERTAS MIROVA reales (no ruido solar).
5. Si FP solares dominan → NO adoptar, documentar y mantener exclusión.

**Resultados** (completar tras el reproc):
- _(pendiente run)_ recall enabled vs disabled por volcán.
- _(pendiente)_ R2 pixel-level evento NdC 2026-03-17.

### Estado S91 (2026-05-30) — runs AÚN EN CURSO, A/B NO concluido

Al retomar en S91, los dos runs A/B seguían sin terminar (NO terminaron al cierre
de S90 como sugería el handoff):
- **NdC** run 26687718294 (mar-abr): job `enabled` in_progress, `disabled` queued.
  Ningún JSON commiteado a main todavía.
- **Villarrica** run 26687842353 (mayo): job `enabled` ✓ success (1h13m, JSON
  `data/_daytime_modis_enabled/Villarrica.json` en main), `disabled` in_progress.

Sin el perfil `disabled` no hay control para el A/B → **no se puede concluir**.
El reproceso MODIS es lento (~1-1.5 h por job, serializado por `max-parallel:1`).

**Herramienta lista (patrón A16)**: `experiments/_s90_daytime_modis/analyze_ab.py`
— smoke-tested. Compara enabled vs disabled por (vol, noche) contra MIROVA
(CONS+OCR vía `latest_consolidado.csv`), aísla las detecciones que SOLO aparecen
con el flag ON (key por `datetime_utc` al minuto; los records no persisten campo
día/noche, así que la diferencia enabled\disabled ES el path diurno), recalcula
elevación solar por record (mismo `_solar_elevation` del pipeline) y clasifica
cada nueva diurna como TP-MIROVA o FP-solar (R3). Uso:
`python experiments/_s90_daytime_modis/analyze_ab.py --volcano NevadosDeChillan
--start 2026-03-01 --end 2026-04-30`.

**Nota metodológica (integridad S88)**: la precisión ABSOLUTA por noche es baja
(~17%) por A54 (≈95% de los "FP" vs MIROVA son realidad física, no ruido solar).
El criterio de adopción mira el **Δ enabled−disabled** y la sección [3] (¿las
nuevas diurnas matchean ALERTA MIROVA o son FP solares?), NO el absoluto.

**Próximo paso S91→S92**: esperar que ambos runs terminen y commiteen los dos
JSON por volcán; correr `analyze_ab.py` para NdC y Villarrica; hacer R2
pixel-level del evento NdC contra TIF MODIS; recién entonces decidir adopción
(con tag + OK explícito de Nicolás, A45). Hasta entonces `enable_daytime_modis`
sigue OFF en operacional.

Si valida: con tag + OK Nicolás, `enable_daytime_modis: true` en
`mirova_equivalent.yaml` (A45) + reproc operacional + verificar dashboard.
