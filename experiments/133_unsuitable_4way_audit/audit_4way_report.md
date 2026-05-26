# S72 F2.4 — 4-way A/B audit (Lascar regression culprit)

Ventana: 2026-02-20 → 2026-05-20 (90d)
Matching MIROVA: ±60 min sensor-aware (per-record, CONS+OCR ALERTAs)
Bug D9: pc.vrp_mw>5.0 MW AND ctx-only (n_bt=0 & n_nti=0) AND t_bg<260.0 K

## Setups

| Setup | §267-273 first_pass | §267-273 pathD | K1 retire | Data source |
|---|---|---|---|---|
| baseline | ON | OFF | OFF | `data/mirova_equivalent/` |
| F2.1     | ON | OFF | ON  | `data/mirova_equivalent_unsuitable_filters_v1/` |
| A/B-1    | ON | **ON** | OFF | extracted from commit `dc4b286` |
| A/B-2    | OFF | OFF | ON  | extracted from commit `a775a7d` |

## Per-volcano 4-way (recall / precision / ratio_med / D9_bug / det)

| Volcan | n_alert | Setup | n_det | TP | FP | FN | Recall | Prec | Ratio | D9 |
|---|---|---|---|---|---|---|---|---|---|---|
| Lascar | 327 | baseline | 655 | 506 | 149 | 114 | 0.82 | 0.77 | 1.29 | 4 |
| Lascar | 327 | f21 | 433 | 303 | 130 | 116 | 0.72 | 0.70 | 0.94 | 0 |
| Lascar | 327 | ab1 | 433 | 303 | 130 | 116 | 0.72 | 0.70 | 0.94 | 0 |
| Lascar | 327 | ab2 | 433 | 303 | 130 | 116 | 0.72 | 0.70 | 0.94 | 0 |
| Lastarria | 92 | baseline | 679 | 349 | 330 | 5 | 0.99 | 0.51 | 11.92 | 3 |
| Lastarria | 92 | f21 | 425 | 180 | 245 | 5 | 0.97 | 0.42 | 1.35 | 0 |
| Lastarria | 92 | ab1 | 425 | 180 | 245 | 5 | 0.97 | 0.42 | 1.35 | 0 |
| Lastarria | 92 | ab2 | 425 | 180 | 245 | 5 | 0.97 | 0.42 | 1.35 | 0 |
| Isluga | 111 | baseline | 526 | 238 | 288 | 20 | 0.92 | 0.45 | 1.84 | 7 |
| Isluga | 111 | f21 | 433 | 181 | 252 | 22 | 0.89 | 0.42 | 1.33 | 0 |
| Isluga | 111 | ab1 | 433 | 181 | 252 | 22 | 0.89 | 0.42 | 1.33 | 0 |
| Isluga | 111 | ab2 | 433 | 181 | 252 | 22 | 0.89 | 0.42 | 1.33 | 0 |
| Villarrica | 10 | baseline | 701 | 40 | 661 | 1 | 0.98 | 0.06 | 14.75 | 27 |
| Villarrica | 10 | f21 | 510 | 25 | 485 | 1 | 0.96 | 0.05 | 15.89 | 0 |
| Villarrica | 10 | ab1 | 510 | 25 | 485 | 1 | 0.96 | 0.05 | 15.89 | 0 |
| Villarrica | 10 | ab2 | 510 | 25 | 485 | 1 | 0.96 | 0.05 | 15.89 | 0 |
| Chaiten | 16 | baseline | 726 | 51 | 675 | 1 | 0.98 | 0.07 | 7.97 | 55 |
| Chaiten | 16 | f21 | 526 | 42 | 484 | 1 | 0.98 | 0.08 | 2.84 | 0 |
| Chaiten | 16 | ab1 | MISSING | | | | | | | |
| Chaiten | 16 | ab2 | 526 | 42 | 484 | 1 | 0.98 | 0.08 | 2.84 | 0 |
| PlanchonPeteroa | 54 | baseline | 652 | 192 | 460 | 4 | 0.98 | 0.29 | 10.34 | 16 |
| PlanchonPeteroa | 54 | f21 | 477 | 127 | 350 | 5 | 0.96 | 0.27 | 4.00 | 0 |
| PlanchonPeteroa | 54 | ab1 | 477 | 127 | 350 | 5 | 0.96 | 0.27 | 4.00 | 0 |
| PlanchonPeteroa | 54 | ab2 | 477 | 127 | 350 | 5 | 0.96 | 0.27 | 4.00 | 0 |
| Tupungatito | 90 | baseline | 596 | 229 | 367 | 13 | 0.95 | 0.38 | 11.61 | 36 |
| Tupungatito | 90 | f21 | 482 | 187 | 295 | 13 | 0.94 | 0.39 | 9.52 | 0 |
| Tupungatito | 90 | ab1 | 482 | 187 | 295 | 13 | 0.94 | 0.39 | 9.52 | 0 |
| Tupungatito | 90 | ab2 | 482 | 187 | 295 | 13 | 0.94 | 0.39 | 9.52 | 0 |
| PuyehueCordonCaulle | 85 | baseline | 930 | 314 | 616 | 13 | 0.96 | 0.34 | 8.65 | 39 |
| PuyehueCordonCaulle | 85 | f21 | 562 | 161 | 401 | 13 | 0.93 | 0.29 | 0.51 | 0 |
| PuyehueCordonCaulle | 85 | ab1 | 562 | 161 | 401 | 13 | 0.93 | 0.29 | 0.51 | 0 |
| PuyehueCordonCaulle | 85 | ab2 | MISSING | | | | | | | |
| Llaima | 1 | baseline | 569 | 3 | 566 | 0 | 1.00 | 0.01 | 23.38 | 19 |
| Llaima | 1 | f21 | 489 | 3 | 486 | 0 | 1.00 | 0.01 | 23.38 | 0 |
| Llaima | 1 | ab1 | 489 | 3 | 486 | 0 | 1.00 | 0.01 | 23.38 | 0 |
| Llaima | 1 | ab2 | 489 | 3 | 486 | 0 | 1.00 | 0.01 | 23.38 | 0 |
| Copahue | 1 | baseline | 657 | 4 | 653 | 0 | 1.00 | 0.01 | 5.85 | 22 |
| Copahue | 1 | f21 | 483 | 1 | 482 | 0 | 1.00 | 0.00 | 3.18 | 0 |
| Copahue | 1 | ab1 | 483 | 1 | 482 | 0 | 1.00 | 0.00 | 3.18 | 0 |
| Copahue | 1 | ab2 | 483 | 1 | 482 | 0 | 1.00 | 0.00 | 3.18 | 0 |
| NevadosDeChillan | 8 | baseline | 381 | 1 | 380 | 4 | 0.20 | 0.00 | 45.65 | 14 |
| NevadosDeChillan | 8 | f21 | MISSING | | | | | | | |
| NevadosDeChillan | 8 | ab1 | MISSING | | | | | | | |
| NevadosDeChillan | 8 | ab2 | MISSING | | | | | | | |

## Deltas vs baseline (recall / D9)

| Volcan | dRecall F2.1 | dRecall A/B-1 | dRecall A/B-2 | dD9 F2.1 | dD9 A/B-1 | dD9 A/B-2 |
|---|---|---|---|---|---|---|
| Lascar | -0.093 | -0.093 | -0.093 | -4 | -4 | -4 |
| Lastarria | -0.013 | -0.013 | -0.013 | -3 | -3 | -3 |
| Isluga | -0.031 | -0.031 | -0.031 | -7 | -7 | -7 |
| Villarrica | -0.014 | -0.014 | -0.014 | -27 | -27 | -27 |
| Chaiten | -0.004 | MISSING | -0.004 | -55 | MISSING | -55 |
| PlanchonPeteroa | -0.017 | -0.017 | -0.017 | -16 | -16 | -16 |
| Tupungatito | -0.011 | -0.011 | -0.011 | -36 | -36 | -36 |
| PuyehueCordonCaulle | -0.035 | -0.035 | MISSING | -39 | -39 | MISSING |
| Llaima | +0.000 | +0.000 | +0.000 | -19 | -19 | -19 |
| Copahue | +0.000 | +0.000 | +0.000 | -22 | -22 | -22 |
| NevadosDeChillan | MISSING | MISSING | MISSING | MISSING | MISSING | MISSING |

## Cross-comparison fairness: vols comunes a los 4 setups = 8
  Lascar, Lastarria, Isluga, Villarrica, PlanchonPeteroa, Tupungatito, Llaima, Copahue

Exclusiones (missing en al menos 1 setup):
  - Chaiten: missing in ['ab1']
  - PuyehueCordonCaulle: missing in ['ab2']
  - NevadosDeChillan: missing in ['f21', 'ab1', 'ab2']

## Lascar regression analysis (focus)

| Setup | Recall | dRecall vs baseline | D9_bug | Diagnosis flag |
|---|---|---|---|---|
| baseline | 0.816 | +0.000 | 4 | stable |
| f21 | 0.723 | -0.093 | 0 | REGRESS >5pp |
| ab1 | 0.723 | -0.093 | 0 | REGRESS >5pp |
| ab2 | 0.723 | -0.093 | 0 | REGRESS >5pp |

## Verdict

- F2.1 Lascar regression: True
- A/B-1 Lascar regression (§267-273 pathD only): True
- A/B-2 Lascar regression (K1 retire only): True

**HALLAZGO CRÍTICO — F2.1, A/B-1 y A/B-2 producen métricas IDÉNTICAS en TODOS los volcanes**, no solo Lascar. Recall, precision, TP, FP, FN, ratio_med, D9_bug coinciden bit-exact entre los 3 setups en los 8 vols comunes (verificado a nivel `pc.vrp_mw` per-record). Diff byte-level entre los JSONs SOLO toca el contador diagnóstico `diag_n_dnti_ctx_path` (no afecta cluster selection ni outputs operacionales).

**Implicación**: el split F2.3 (separar §267-273 first_pass + pathD vs K1 retire) NO logra aislar contribuciones individuales. Las 3 configuraciones convergen al mismo resultado final. Hipótesis del bug split:

1. **`enable_first_pass_tests_2_and_3: true`** (común a los 3 perfiles) ya aplica los floors `unsuitable_dnti_floor/deti_floor` cuando `enable_unsuitable_filters_267_273` está OFF — el flag de gating parece no estar siendo respetado en el código.
2. **K1 retire podría no estar conectado** a la ruta que recorta candidatos (n_det baja igual: 433 en Lascar para los 3), siendo `enable_first_pass_tests_2_and_3` el feature dominante.
3. Alternativa: las tres rutas (§267-273 first_pass, §267-273 path D, K1 retire) eliminan el MISMO subconjunto de pixels Lascar (las que pasaron `first_pass_tests_2_and_3`), por overlap total → un OR redundante.

**Verdict bibliográfico-respaldado**: NO adoptar ningún setup. La regression Lascar -9.3pp recall persiste idéntica con cualquier subset → el culpable NO se puede aislar con esta arquitectura de flags. Antes de pasar a F2.5, **investigar en código** (`pipeline/process_*.py` + `pipeline/cluster_*.py`):
- Verificar que `enable_unsuitable_filters_267_273=false` realmente desactive los floors en first_pass.
- Verificar que `enable_test1_k1_retire_from_hot_mask=false` realmente bypasee el retire.
- Si los flags están conectados pero no afectan output, la causa raíz de Lascar regression es algún feature compartido que se activa via `enable_first_pass_tests_2_and_3` o `enable_dual_roi_first_pass`.

## Adopción S33 (criterio relajado por sample reducido)

Criterios:
- Bug D9 drop >50% en ≥5/N vols (N = common vols).
- Recall NO degrada >5pp en ningún vol con n_mirova≥10.
- Precision NO degrada en ningún vol.

| Setup | Vols con D9>0 base | D9 drop≥50% | Recall OK (n≥10) | Prec no-degrade | Pasa criterio |
|---|---|---|---|---|---|
| f21 | 8 | 8 | 5/6 | 2/8 | NO |
| ab1 | 8 | 8 | 5/6 | 2/8 | NO |
| ab2 | 8 | 8 | 5/6 | 2/8 | NO |

Notas:
- F2.1 = combo (pathD OFF, K1 ON) — replica condicion testeada F2.2.
- A/B-1 = pathD ON, K1 OFF — aisla §267-273 firstpass + extension.
- A/B-2 = K1 ON solo — aisla retire mechanism.
- NdC missing en F2.1 + A/B-1 + A/B-2 (failures workflow).
- Chaiten missing en A/B-1 (failure workflow run 26258435593).
- PCC missing en A/B-2 (failure workflow run 26258437263).

## Plan adopción concreto

**NO adoptar A/B-1 ni A/B-2 ni F2.1 a operacional.** Lascar regress -9.3pp en los 3, idéntico.

**Acciones F2.5 (próximas)**:
1. Auditar código `pipeline/process_modis.py` y `pipeline/process_viirs*.py` buscando dónde se consultan los flags `enable_unsuitable_filters_267_273` y `enable_test1_k1_retire_from_hot_mask`. Confirmar que el `false` value efectivamente bypassea la lógica.
2. A/B test sintético con `enable_first_pass_tests_2_and_3: false` solamente, dejando el resto operacional baseline. Si recall Lascar vuelve a 0.82 → ese feature (no §267-273 ni K1) es la causa raíz de la regress.
3. Si confirmado (2), revisar Coppola 2016a §259-273 para validar si `first_pass_tests_2_and_3` se debe aplicar como hard filter o solo como diagnostic.

**Cambios yaml**: ninguno hasta resolver la causa raíz.
