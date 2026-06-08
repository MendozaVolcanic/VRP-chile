# S103 — Resultados promoción nadir-fijo VIIRS (11 Tier A)

**Fecha**: 2026-06-08 · A45 (espejo de nadir-fijo MODIS S102). Reproc histórico
runs 27098410956 (11 vols, 22/22 success) + 27140784929 (re-reproc PCC/Tupun por
under-fetch de días recientes). Promoción solo-VIIRS (`merge_promote_viirs_nadir.py`,
guard anti-underfetch por cobertura, MODIS byte-idéntico). Validación R3
(`audit_viirs_nadir_promote_r3.py`, ventana 2026-01-29..06-07).

## R3 — ratio mediano ours/MIROVA por volcán y sensor (baseline pre-nadir → post)

| Volcán | V375 antes→post | V750 antes→post | FN V375 | FN V750 |
|---|---|---|---|---|
| Lascar | 1.41→**0.72** | 1.42→0.76 | 0 | 4 |
| PuyehueCordonCaulle | 2.38→**0.95** | 2.00→1.02 | 0 | 0 |
| Tupungatito | 11.19→**0.71** | 19.23→16.62¹ | 0 | 7 |
| Chaiten | 6.90→**1.19** | — | 0 | 0 |
| Villarrica | 18.30→**1.00** | — | 0 | 0 |
| Llaima | 2.01→**1.02** | — | 0 | 0 |
| PlanchonPeteroa | 7.32→**1.08** | 16.59¹ | 0 | 2 |
| Copahue | 3.18→**1.62** | — | 0 | 0 |
| Isluga | 3.33→**0.59** | 4.76¹ | 0 | 9² |
| Lastarria | 1.98→**0.69** | — | 0 | 0 |
| NevadosDeChillan | — | 0.64 | 4³ | 0 |
| **GLOBAL** | **2.27→0.78** | **1.59→0.80** | **4³** | 22² |

¹ Residuo glaciar VIIRS750 (Tupun/PP/Isluga) PERSISTE = §2 path D (frente aparte).
² Isluga V750 +2 FN nuevos (7→9; global 20→22) — ACEPTADO S103. Mecanismo: el área
   nadir reduce la energía integrada del Test1 → 2 detecciones glaciar borderline
   (sobre-detecciones pre-nadir 5.0/2.56 MW vs MIROVA 0.19/0.25) dejan de disparar.
   Ver `docs/MIROVA_DIVERGENCES.md` S103.
³ Los 4 FN VIIRS375 son todos NevadosDeChillan, **pre-existentes** (NdC apenas detecta,
   física sub-píxel) — **0 FN nuevos por el nadir en VIIRS375**.

## Veredicto
Clava el target pre-registrado (design doc 2026-06-06 §5bis): VIIRS375 ~0.78×,
VIIRS750 ~0.80×, 0 FN nuevos VIIRS375. Curados los grandes (Villarrica 18.3→1.0×,
Tupun 11.2→0.71×, PP 7.3→1.1×, Chaitén 6.9→1.2×, PCC 2.4→0.95×). MODIS intacto.

## Efecto adicional (no solo magnitud)
El nadir reduce también la CANTIDAD de detecciones (vía el Test1): Villarrica
636→602, Isluga 550→535, Llaima 557→540 → mitiga parcialmente la sobre-detección.

## Rollback
`git checkout pre-s103-nadir-fixed-viirs -- data/mirova_equivalent/<vol>.json`
