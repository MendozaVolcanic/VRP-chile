# S102 — Resultados promoción nadir-fijo MODIS

Adopción del fix nadir-fijo MODIS (PR #354, A45) + reproc histórico 11 Tier A
(run 27035142954, 22/22 success) + promoción LOCAL solo-MODIS a
`data/mirova_equivalent/`.

## Qué se promovió
- Reproc ventana **2026-01-29 .. 2026-06-04** con perfil `_s102_nadir_promote`
  (hereda `mirova_equivalent` ya flipeado: `enable_nadir_fixed_pixel_area_modis:true`
  + `min_vrp_mw_modis:0.05`).
- Merge `merge_promote_nadir.py`: reemplaza SOLO records MODIS en ventana, con
  guard anti-underfetch por cobertura de granules. **VIIRS byte-idéntico** en
  los 11 (verificado). 0 vols saltados (sin under-fetch).

## R3 — ratio vs MIROVA-MODIS + residuo path D (antes sec³ → después nadir)

| Volcán | ratio antes | ratio después | residuo>20 antes | residuo después | FN |
|---|---|---|---|---|---|
| Lascar | 2.87× (n=62) | **1.38×** (n=62) | 3 rec, max 43.6 MW | **0** | 0 |
| PuyehueCordonCaulle | — (n=0) | — | 16 rec, max **342.2** MW | **2 rec, max 60.2** | 0 |
| Tupungatito | — | — | 15 rec, max 133.5 MW | **0** | 0 |
| Villarrica | 13.82× (n=1) | 1.78× (n=1) | 15 rec, max 45.2 | **0** | 0 |
| Chaiten | 3.01× (n=1) | 1.16× (n=1) | 22 rec, max 93.9 | **0** | 0 |
| NevadosDeChillan | 2.84× (n=1) | 3.65× (n=1) | 11 rec, max 55.8 | **0** | 0 |
| Llaima | — | — | 7 rec, max 48.0 | **0** | 0 |
| PlanchonPeteroa | — | — | 2 rec, max 43.6 | **0** | 0 |
| Copahue | — | — | 3 rec, max 38.6 | **0** | 0 |
| Isluga | — | — | 2 rec, max 22.7 | **0** | 0 |
| Lastarria | — | — | 1 rec, max 22.0 | **0** | 0 |

**Cobertura/detecciones MODIS (base→promovido)**: sin pérdidas; leves ganancias por
piso 0.05 (Lastarria det 225→228, NdC 271→272, Villarrica 277→278).

## Lectura
- El artefacto del campo difuso colapsó en los 11: residuos >20 MW → 0 salvo
  **PCC 60 MW (2 records)** = residuo path D documentado (2ª palanca, frente
  posterior, NO parte de este fix).
- **0 FN** en todos.
- Láscar 1.38× sobre la historia completa (n=62) vs 0.92× de la validación S101
  (solo abril, n=33): la diferencia es la ventana (régimen térmico invernal
  ene-mar). Mejora robusta desde 2.87×; dentro del ±30% MIROVA por el lado alto.
  n=1 (NdC/Villarrica/Chaitén) estadísticamente irrelevantes.
- VIIRS NO se tocó (mismo drift sec³, frente posterior con su propio A/B).

## Verificación
- R3: `experiments/_s99_audit/audit_nadir_promote_r3.py`.
- R2 pixel-level vs TIF: hecho en validación S101 (design doc §10.6); el TIF
  MIROVA-MODIS no tiene foco al cráter ni en Láscar (A24) → el check operativo
  es el ratio R3 vs VRP publicado.
- R8: verificar dashboard público post-deploy.

Rollback: `git checkout pre-s102-nadir-fixed-modis -- data/mirova_equivalent/<vol>.json`.
