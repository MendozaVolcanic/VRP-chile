# Dormant audit — TODO/FIXME y comentarios con sustancia en código (S99)

Barrido case-insensitive (TODO/FIXME/HACK/XXX/pendiente/bug/drift/parche/backward
compat) en pipeline/ scripts/ frontend/. Solo items con sustancia (no cosméticos).

## Arquetipo de oro (el patrón que buscamos)
- `pipeline/profile.py:207` + `pipeline/test1_spatial_core.py:7` + `process_viirs.py:1418`
  — "factor 8-30× MIROVA" inflación magnitud Test 1. **YA en curso S99** (no dormido).

## Alto impacto (problema real aún presente)
1. `pipeline/profile.py:335` — `enable_test1_k1_retire_from_hot_mask` default OFF,
   ausente del yaml operacional. Cita SP426.5 §298-300. NEW-7 (ver drifts_abiertos.md).
2. `pipeline/path_d_intra_radio.py:3` + `process_viirs.py:~1292` — path D dNTI ctx:
   FPs sistémicos (S81: MODIS Tier A; mitigado por cap 5 MW, raíz abierta = D9).
3. `pipeline/process_viirs.py:~556,649` — S46 drift #1b: riesgo silent failure si
   NTI=None con bg_exclude flag (fragilidad, no bug activo en operacional).
4. `pipeline/vrp_regimes.py:6` — "R3 crater lake (pendiente)" Eq.25 Ruapehu nunca escrita.
5. `frontend/index.html:~2953` — vrp_tir Stefan-Boltzmann sin gate consistencia (F46;
   raro pero severo en escenas frío+cirrus).

## Medio
- `frontend/index.html:~1064` — drift A23/D9 cirrus contextual (display ya mitiga).
- `pipeline/detect_tirvolch.py:~169` — baseline temporal 10yr pendiente (Tier B+).
- Varios "backward compat" en aliases legacy (deuda de limpieza, no funcional).

Nota (A48/A50): los factores citados (8-30×, etc.) son textuales del código/doc, NO
re-verificados con reproc fresco aquí. Verificar antes de accionar.
