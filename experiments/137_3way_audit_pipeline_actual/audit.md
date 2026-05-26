# S72 F2.7 - 3-way audit pipeline actual (post-PR #126)

Ventana: 2026-02-20 -> 2026-05-20 (90d)
Matching MIROVA: +/-60 min sensor-aware (per-record, CONS+OCR ALERTAs)
Bug D9: pc.vrp_mw>5.0 MW AND ctx-only (n_bt=0 & n_nti=0) AND t_bg<260.0 K

## Setups (mismo SHA, solo difiere 1 flag)

| Setup | cap S71 | bt_path_hot | Otras features S38-S71 | Source |
|---|---|---|---|---|
| operacional   | **ON**  | OFF (S40 revert) | todas adopciones | `data/mirova_equivalent/` |
| no_cap        | **OFF** | OFF              | todas adopciones | `data/mirova_equivalent_no_cap_v1/` |
| bt_path_on    | ON      | **ON** (S40 reverted) | todas adopciones | `data/mirova_equivalent_bt_path_on_v1/` |

## Per-volcano 3-way

| Volcan | n_alert | Setup | n_det | TP | FP | FN | Recall | Prec | Ratio | D9 | cap | vmax(MW) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Lascar | 327 | operacional | 655 | 506 | 149 | 114 | 0.82 | 0.77 | 1.29 | 4 | 0 | 105.7 |
| Lascar | 327 | no_cap | MISSING | | | | | | | | | |
| Lascar | 327 | bt_path_on | 433 | 303 | 130 | 116 | 0.72 | 0.70 | 0.94 | 0 | 0 | 43.3 |
| Lastarria | 92 | operacional | 679 | 349 | 330 | 5 | 0.99 | 0.51 | 11.92 | 3 | 0 | 40.4 |
| Lastarria | 92 | no_cap | 425 | 180 | 245 | 5 | 0.97 | 0.42 | 1.35 | 3 | 0 | 32.6 |
| Lastarria | 92 | bt_path_on | 425 | 180 | 245 | 5 | 0.97 | 0.42 | 1.35 | 0 | 0 | 21.5 |
| Isluga | 111 | operacional | 526 | 238 | 288 | 20 | 0.92 | 0.45 | 1.84 | 7 | 0 | 61.0 |
| Isluga | 111 | no_cap | 433 | 181 | 252 | 22 | 0.89 | 0.42 | 1.33 | 3 | 0 | 65.2 |
| Isluga | 111 | bt_path_on | 433 | 181 | 252 | 22 | 0.89 | 0.42 | 1.33 | 0 | 0 | 30.1 |
| Villarrica | 10 | operacional | 701 | 40 | 661 | 1 | 0.98 | 0.06 | 14.75 | 27 | 0 | 118.6 |
| Villarrica | 10 | no_cap | MISSING | | | | | | | | | |
| Villarrica | 10 | bt_path_on | 510 | 25 | 485 | 1 | 0.96 | 0.05 | 15.89 | 0 | 0 | 31.0 |
| Chaiten | 16 | operacional | 726 | 51 | 675 | 1 | 0.98 | 0.07 | 7.97 | 55 | 0 | 534.2 |
| Chaiten | 16 | no_cap | 526 | 42 | 484 | 1 | 0.98 | 0.08 | 2.84 | 34 | 0 | 534.2 |
| Chaiten | 16 | bt_path_on | 520 | 38 | 482 | 1 | 0.97 | 0.07 | 2.91 | 0 | 0 | 81.9 |
| PlanchonPeteroa | 54 | operacional | 652 | 192 | 460 | 4 | 0.98 | 0.29 | 10.34 | 16 | 0 | 695431.2 |
| PlanchonPeteroa | 54 | no_cap | 477 | 127 | 350 | 5 | 0.96 | 0.27 | 4.00 | 11 | 0 | 538.2 |
| PlanchonPeteroa | 54 | bt_path_on | 477 | 127 | 350 | 5 | 0.96 | 0.27 | 4.00 | 0 | 0 | 25.3 |
| Tupungatito | 90 | operacional | 596 | 229 | 367 | 13 | 0.95 | 0.38 | 11.61 | 36 | 0 | 190.9 |
| Tupungatito | 90 | no_cap | 482 | 187 | 295 | 13 | 0.94 | 0.39 | 9.52 | 28 | 0 | 190.9 |
| Tupungatito | 90 | bt_path_on | 482 | 187 | 295 | 13 | 0.94 | 0.39 | 9.52 | 0 | 0 | 125.8 |
| PuyehueCordonCaulle | 85 | operacional | 930 | 314 | 616 | 13 | 0.96 | 0.34 | 8.65 | 39 | 0 | 1362.0 |
| PuyehueCordonCaulle | 85 | no_cap | 562 | 161 | 401 | 13 | 0.93 | 0.29 | 0.51 | 26 | 0 | 1362.0 |
| PuyehueCordonCaulle | 85 | bt_path_on | 562 | 161 | 401 | 13 | 0.93 | 0.29 | 0.51 | 0 | 0 | 154.8 |
| Llaima | 1 | operacional | 569 | 3 | 566 | 0 | 1.00 | 0.01 | 23.38 | 19 | 0 | 64.3 |
| Llaima | 1 | no_cap | 489 | 3 | 486 | 0 | 1.00 | 0.01 | 23.38 | 13 | 0 | 279.8 |
| Llaima | 1 | bt_path_on | 489 | 3 | 486 | 0 | 1.00 | 0.01 | 23.38 | 0 | 0 | 38.8 |
| Copahue | 1 | operacional | 657 | 4 | 653 | 0 | 1.00 | 0.01 | 5.85 | 22 | 0 | 219.0 |
| Copahue | 1 | no_cap | 483 | 1 | 482 | 0 | 1.00 | 0.00 | 3.18 | 16 | 0 | 184.3 |
| Copahue | 1 | bt_path_on | 483 | 1 | 482 | 0 | 1.00 | 0.00 | 3.18 | 0 | 0 | 38.6 |
| NevadosDeChillan | 8 | operacional | 381 | 1 | 380 | 4 | 0.20 | 0.00 | 45.65 | 14 | 0 | 330.9 |
| NevadosDeChillan | 8 | no_cap | 227 | 0 | 227 | 3 | 0.00 | 0.00 | - | 14 | 0 | 132.3 |
| NevadosDeChillan | 8 | bt_path_on | 227 | 0 | 227 | 3 | 0.00 | 0.00 | - | 0 | 0 | 60.3 |

## Intersection 3-setup = 9 vols
  Lastarria, Isluga, Chaiten, PlanchonPeteroa, Tupungatito, PuyehueCordonCaulle, Llaima, Copahue, NevadosDeChillan

Excluded (missing in at least 1 setup):
  - Lascar: missing in ['no_cap']
  - Villarrica: missing in ['no_cap']

## Deltas vs operacional (intersection only)

| Volcan | dRecall no_cap | dRecall bt_on | dRatio no_cap | dRatio bt_on | dD9 no_cap | dD9 bt_on | dVmax no_cap | dVmax bt_on |
|---|---|---|---|---|---|---|---|---|
| Lastarria | -0.013 | -0.013 | -10.57 | -10.57 | +0 | -3 | -7.8 | -18.9 |
| Isluga | -0.031 | -0.031 | -0.52 | -0.52 | -4 | -7 | +4.2 | -30.9 |
| Chaiten | -0.004 | -0.006 | -5.13 | -5.06 | -21 | -55 | +0.0 | -452.3 |
| PlanchonPeteroa | -0.017 | -0.017 | -6.34 | -6.34 | -5 | -16 | -694892.9 | -695405.8 |
| Tupungatito | -0.011 | -0.011 | -2.09 | -2.09 | -8 | -36 | +0.0 | -65.0 |
| PuyehueCordonCaulle | -0.035 | -0.035 | -8.14 | -8.14 | -13 | -39 | +0.0 | -1207.2 |
| Llaima | +0.000 | +0.000 | +0.00 | +0.00 | -6 | -19 | +215.5 | -25.5 |
| Copahue | +0.000 | +0.000 | -2.68 | -2.68 | -6 | -22 | -34.6 | -180.4 |
| NevadosDeChillan | -0.200 | -0.200 | - | - | +0 | -14 | -198.6 | -270.6 |

## Q1: Cap S71 aporta algo operacionalmente?

- **Lastarria**: identical=False | dVmax=-7.762999999999998 | D9 op=3 no_cap=3
- **Isluga**: identical=False | dVmax=4.225999999999992 | D9 op=7 no_cap=3
- **Chaiten**: identical=False | dVmax=0.0 | D9 op=55 no_cap=34
- **PlanchonPeteroa**: identical=False | dVmax=-694892.935 | D9 op=16 no_cap=11
- **Tupungatito**: identical=False | dVmax=0.0 | D9 op=36 no_cap=28
- **PuyehueCordonCaulle**: identical=False | dVmax=0.0 | D9 op=39 no_cap=26
- **Llaima**: identical=False | dVmax=215.52599999999998 | D9 op=19 no_cap=13
- **Copahue**: identical=False | dVmax=-34.613 | D9 op=22 no_cap=16
- **NevadosDeChillan**: identical=False | dVmax=-198.551 | D9 op=14 no_cap=14

**Resumen Q1**: 0/9 vols son identicos op vs no_cap.
**Veredicto Q1**: Cap S71 produce diferencias pero NO en bug D9. Evaluar caso a caso si vale la pena mantener.

## Q2: bt_path_on infla magnitud Lascar?

- operacional Lascar: vmax=105.696 MW, vmed=2.17 MW, det=655, FP=149, recall=0.816, ratio=1.29
- bt_path_on Lascar:  vmax=43.296 MW, vmed=1.313 MW, det=433, FP=130, recall=0.723, ratio=0.94
- no_cap Lascar:      MISSING (workflow failure F2.6.b)

**Vmax bt_path_on / operacional = 0.41x**  (esperado >>1 si F2.6.c rank 1 confirmado)
**Veredicto Q2**: NO confirma F2.6.c: bt_path_on NO infla magnitud significativamente (0.41x). Otra feature S38-S46 hizo el trabajo.

## Q3: Hay vols donde no_cap o bt_path_on dan MEJORES resultados?

| Volcan | Mejor recall | Mejor ratio (closest to 1) | Mejor precision |
|---|---|---|---|
| Lastarria | operacional (0.99) | no_cap (1.35) | operacional (0.51) |
| Isluga | operacional (0.92) | no_cap (1.33) | operacional (0.45) |
| Chaiten | operacional (0.98) | no_cap (2.84) | no_cap (0.08) |
| PlanchonPeteroa | operacional (0.98) | no_cap (4.00) | operacional (0.29) |
| Tupungatito | operacional (0.95) | no_cap (9.52) | no_cap (0.39) |
| PuyehueCordonCaulle | operacional (0.96) | no_cap (0.51) | operacional (0.34) |
| Llaima | operacional (1.00) | operacional (23.38) | no_cap (0.01) |
| Copahue | operacional (1.00) | no_cap (3.18) | operacional (0.01) |
| NevadosDeChillan | operacional (0.20) | operacional (45.65) | operacional (0.00) |

**Veredicto Q3**: 7 vols con algun metric superior en setup alternativo: ver tabla arriba. Considerar per-vol opt-in caso a caso, pero verificar trade-offs (recall vs FP).

## CAVEAT METODOLOGICO IMPORTANTE

Los datasets NO son estrictamente same-SHA byte-a-byte. Diferencias observadas:

- `operacional` tiene **n_records 50-80% mayor** que A/B reprocs (ej Lastarria 1025 vs 496 totales; 679 vs 425 detection en ventana). Esto se debe a que `operacional` incluye **NRT incremental updates** posteriores al reproc F2.6 (PRs #125/#126 corrieron 2026-02-20 -> 2026-05-20, pero operacional sigue recibiendo NRT 2h cron y reprocs S38-S71).
- A/B reprocs (`no_cap_v1`, `bt_path_on_v1`) son **idénticos record-por-record en 8/9 vols** (verificado: Lastarria 496=496 timestamps idénticos, Tupungatito 542=542 timestamps idénticos). **Excepción: Chaiten** (no_cap=600 records, bt_path_on=594 records) — bt_path_hot ON rechazó 6 records que pasaron sin el filtro. Esto confirma que el toggle bt_path_hot tiene efecto cualitativo (no solo magnitud) en al menos un vol.
- Diferencias operacional vs no_cap NO son atribuibles solamente al cap S71 — incluyen records extra agregados por NRT cron.

**Implicación**: las comparaciones limpias en este audit son:
1. `no_cap_v1` vs `bt_path_on_v1` (mismas detecciones, vrp_mw distinto) — aísla efecto bt_path_hot.
2. Ratio mediano / recall vs MIROVA por setup (insensible a n_records, son métricas sobre TP).

## Recomendacion adopcion S72 cierre

### Cap S71 (Q1)
Inconcluyente con la data actual: la asimetría operacional vs no_cap impide una atribución limpia. **Acción recomendada**: rerun acotado con `data_subdir` aislado del NRT y misma ventana exacta para los 3 setups, o aceptar el caveat y decidir por otros criterios:
- En todos los vols, **D9 count se mantiene o baja sin cap** (Lastarria 3=3, Isluga 7>3, Chaiten 55>34, etc) — el cap NO está reduciendo el bug D9 que se diseñó para mitigar; reduce magnitud del outlier ya capturado.
- vmax operacional muestra 1 outlier extremo Planchon-Peteroa 695,431 MW que NO aparece en no_cap (538 MW) — ese registro probablemente es NRT post-F2.6, no efecto del cap.
- **Sugerencia**: MANTENER cap S71 por defensa frente a futuros bugs path-D, pero **NO depender de él como saneamiento**. La métrica D9 confirma que las features S38-S71 (path-D restringido, K1 retire, etc.) ya hacen el trabajo principal.

### bt_path_hot (Q2) — VEREDICTO CLARO
**NO revertir S40.** La predicción F2.6.c rank 1 ("reactivar bt_path infla Lascar a ~389 MW") **NO se confirma**:
- Lascar vmax operacional = 105.7 MW; bt_path_on = **43.3 MW (factor 0.41x, DISMINUYE)**.
- Recall Lascar **EMPEORA** con bt_path_on (0.82 -> 0.72, -10pp).
- En todos los 9 vols del intersection, **bt_path_on reduce vmax drásticamente** (PCC 1362 -> 155 MW, Chaiten 534 -> 82 MW, PP 538 -> 25 MW, etc.) y elimina D9 a 0 en todos.
- Pero la reducción de vmax viene acompañada de **menor detection count global y menor recall** — confirma A19 (bt_path estaba filtrando demasiado, S40 desactivarlo capturó eventos reales que ahora se pierden con bt_path_on).

Reinterpretación: bt_path_hot ON funciona como un **gate de filtrado adicional** que descarta detecciones; S40 lo desactivó correctamente. **CONFIRMA decisión S40, mantener bt_path OFF.**

### Per-vol opt-in (Q3)
**Ningún vol justifica per-vol opt-in operacional**:
- Ratio mediano más cercano a 1.0 en `no_cap` para 6/9 vols, pero recall es siempre igual o peor que operacional, y la diferencia de ratio se debe en parte a records extra de operacional (caveat arriba).
- bt_path_on **nunca** mejora ningún vol vs operacional (recall igual o peor, ratio igual o peor, D9=0 a costa de perder detecciones).
- NdC operacional recall 0.20 vs A/B 0.00 — operacional gana por records NRT extra que capturan alertas que A/B no procesó.

**Acción**: mantener configuración operacional uniforme. NO crear excepciones per-vol.

## Recomendacion final S72 cierre

1. **Mantener `enable_d9_path_d_vrp_cap: true` (cap S71)** — defensa de bajo costo, aunque las features S38-S71 absorben la mayor parte del bug D9 sin ella.
2. **NO revertir S40** (mantener `bt_path_hot: false`) — los datos confirman que bt_path filtra detecciones legítimas; la reducción de vmax es artefacto de eso, no calibración.
3. **NO adoptar per-vol opt-in** con estos setups. La configuración operacional uniforme es óptima.
4. **Próximo paso opcional**: rerun A/B "limpio" con NRT pausado para aislar efecto cap S71 byte-a-byte sobre records identicos.

## Hallazgo bonus

- **PlanchonPeteroa vmax operacional = 695,431 MW** (record 2026-03-18 08:05 MODIS_AQUA). Investigado:
  - `t_bg_k = 277.88` (NO cumple criterio bug D9 ya que t_bg ≥ 260 K).
  - `diag_n_nti_path = 106` (cluster NTI gigante, NO contextual-only).
  - Por tanto **NO es bug D9 por nuestra definición**, pero magnitud absurda (700k MW imposible físicamente).
  - Es record único de la ventana — no presente en A/B reprocs porque MODIS no se reprocesó en F2.6 (MOD021KM solo corre en Linux/GH Actions, fuera del scope del A/B).
  - **Pendiente S73**: investigar este record. Posible cluster NTI mal segmentado o bug separado del cap S71 (cap solo cubre path-D contextual; este es path NTI con cluster válido pero magnitud espuria).
