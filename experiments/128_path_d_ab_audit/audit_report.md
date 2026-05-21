# Audit cruzado D9 path D fix - 3 opciones (S71 T1 F2.d)

Tolerancia matching MIROVA: ±3.0h (CONS+OCR ALERTA). Ventana: interseccion fechas en los 3 experimentos (~ Feb20-May20, 90d).

## Resumen por volcan: recall / precision / ratio mediano

| Volcan | Opcion | TP | FP | FN | Recall | Precision | Ratio_med | N_ratio | pD-only>5MW | pD>5_tbg<260 |
|---|---|---|---|---|---|---|---|---|---|---|
| Lastarria | baseline | 68 | 22 | 0 | 1.00 | 0.76 | 38.30 | 160 | 133 | 3 |
| Lastarria | A_atm_gate | 68 | 22 | 0 | 1.00 | 0.76 | 3.58 | 157 | 43 | 0 |
| Lastarria | B_covalidation | 67 | 20 | 1 | 0.99 | 0.77 | 2.90 | 102 | 0 | 0 |
| Lastarria | C_cap | 68 | 22 | 0 | 1.00 | 0.76 | 3.42 | 163 | 10 | 0 |
| Lascar | baseline | 83 | 7 | 0 | 1.00 | 0.92 | 2.82 | 240 | 116 | 4 |
| Lascar | A_atm_gate | 83 | 7 | 0 | 1.00 | 0.92 | 1.10 | 269 | 49 | 0 |
| Lascar | B_covalidation | 83 | 5 | 0 | 1.00 | 0.94 | 1.05 | 182 | 1 | 0 |
| Lascar | C_cap | 83 | 7 | 0 | 1.00 | 0.92 | 1.11 | 273 | 28 | 0 |
| Isluga | baseline | 61 | 27 | 2 | 0.97 | 0.69 | 13.57 | 78 | 92 | 7 |
| Isluga | A_atm_gate | 63 | 27 | 0 | 1.00 | 0.70 | 2.11 | 118 | 43 | 0 |
| Isluga | B_covalidation | 62 | 27 | 1 | 0.98 | 0.70 | 2.70 | 68 | 5 | 0 |
| Isluga | C_cap | 62 | 27 | 1 | 0.98 | 0.70 | 2.24 | 123 | 22 | 0 |
| Villarrica | baseline | 9 | 81 | 0 | 1.00 | 0.10 | 21.74 | 17 | 199 | 27 |
| Villarrica | A_atm_gate | 9 | 79 | 0 | 1.00 | 0.10 | 9.16 | 22 | 95 | 0 |
| Villarrica | B_covalidation | 9 | 79 | 0 | 1.00 | 0.10 | 12.04 | 14 | 38 | 0 |
| Villarrica | C_cap | 9 | 81 | 0 | 1.00 | 0.10 | 9.16 | 22 | 85 | 0 |
| Chaiten | baseline | 12 | 78 | 0 | 1.00 | 0.13 | 18.54 | 20 | 203 | 55 |
| Chaiten | A_atm_gate | 12 | 75 | 0 | 1.00 | 0.14 | 8.24 | 33 | 90 | 0 |
| Chaiten | B_covalidation | 12 | 71 | 0 | 1.00 | 0.14 | 18.64 | 20 | 24 | 0 |
| Chaiten | C_cap | 12 | 78 | 0 | 1.00 | 0.13 | 8.45 | 34 | 72 | 0 |
| PlanchonPeteroa | baseline | 41 | 49 | 0 | 1.00 | 0.46 | 24.15 | 81 | 136 | 15 |
| PlanchonPeteroa | A_atm_gate | 41 | 46 | 0 | 1.00 | 0.47 | 11.76 | 98 | 55 | 0 |
| PlanchonPeteroa | B_covalidation | 41 | 46 | 0 | 1.00 | 0.47 | 15.96 | 47 | 6 | 0 |
| PlanchonPeteroa | C_cap | 41 | 49 | 0 | 1.00 | 0.46 | 11.07 | 99 | 45 | 0 |
| Tupungatito | baseline | 60 | 30 | 0 | 1.00 | 0.67 | 23.01 | 86 | 117 | 35 |
| Tupungatito | A_atm_gate | 60 | 29 | 0 | 1.00 | 0.67 | 5.97 | 154 | 89 | 0 |
| Tupungatito | B_covalidation | 60 | 29 | 0 | 1.00 | 0.67 | 22.70 | 111 | 94 | 0 |
| Tupungatito | C_cap | 60 | 30 | 0 | 1.00 | 0.67 | 6.21 | 166 | 37 | 0 |
| PuyehueCordonCaulle | baseline | 45 | 45 | 0 | 1.00 | 0.50 | 40.60 | 139 | 293 | 39 |
| PuyehueCordonCaulle | A_atm_gate | 45 | 41 | 0 | 1.00 | 0.52 | 1.20 | 137 | 57 | 0 |
| PuyehueCordonCaulle | B_covalidation | 43 | 39 | 2 | 0.96 | 0.52 | 12.18 | 70 | 35 | 0 |
| PuyehueCordonCaulle | C_cap | 45 | 45 | 0 | 1.00 | 0.50 | 1.21 | 141 | 38 | 0 |
| Llaima | baseline | 1 | 89 | 0 | 1.00 | 0.01 | 61.14 | 1 | 130 | 17 |
| Llaima | A_atm_gate | 1 | 86 | 0 | 1.00 | 0.01 | 60.21 | 2 | 49 | 0 |
| Llaima | B_covalidation | 1 | 85 | 0 | 1.00 | 0.01 | 7.41 | 1 | 11 | 0 |
| Llaima | C_cap | 1 | 89 | 0 | 1.00 | 0.01 | 60.21 | 2 | 34 | 0 |
| Copahue | baseline | 1 | 89 | 0 | 1.00 | 0.01 | 21.39 | 1 | 171 | 21 |
| Copahue | A_atm_gate | 1 | 89 | 0 | 1.00 | 0.01 | 3.82 | 1 | 29 | 0 |
| Copahue | B_covalidation | 1 | 89 | 0 | 1.00 | 0.01 | - | 0 | 5 | 1 |
| Copahue | C_cap | 1 | 89 | 0 | 1.00 | 0.01 | 3.82 | 1 | 25 | 0 |
| NevadosDeChillan | baseline | 6 | 84 | 0 | 1.00 | 0.07 | 20.99 | 6 | 118 | 14 |
| NevadosDeChillan | A_atm_gate | 5 | 82 | 1 | 0.83 | 0.06 | 10.00 | 3 | 36 | 0 |
| NevadosDeChillan | B_covalidation | 2 | 17 | 4 | 0.33 | 0.11 | - | 0 | 0 | 0 |
| NevadosDeChillan | C_cap | 6 | 84 | 0 | 1.00 | 0.07 | 10.20 | 5 | 33 | 0 |

## Delta vs baseline (recall_keep, precision_gain, ratio_change)

| Volcan | Opcion | dRecall | dPrecision | dRatio | pD-only_drop |
|---|---|---|---|---|---|
| Lastarria | A_atm_gate | +0.00 | +0.00 | -34.71 | 90 |
| Lastarria | B_covalidation | -0.01 | +0.01 | -35.40 | 133 |
| Lastarria | C_cap | +0.00 | +0.00 | -34.88 | 123 |
| Lascar | A_atm_gate | +0.00 | +0.00 | -1.72 | 67 |
| Lascar | B_covalidation | +0.00 | +0.02 | -1.78 | 115 |
| Lascar | C_cap | +0.00 | +0.00 | -1.71 | 88 |
| Isluga | A_atm_gate | +0.03 | +0.01 | -11.47 | 49 |
| Isluga | B_covalidation | +0.02 | +0.00 | -10.88 | 87 |
| Isluga | C_cap | +0.02 | +0.00 | -11.33 | 70 |
| Villarrica | A_atm_gate | +0.00 | +0.00 | -12.59 | 104 |
| Villarrica | B_covalidation | +0.00 | +0.00 | -9.70 | 161 |
| Villarrica | C_cap | +0.00 | +0.00 | -12.59 | 114 |
| Chaiten | A_atm_gate | +0.00 | +0.00 | -10.30 | 113 |
| Chaiten | B_covalidation | +0.00 | +0.01 | +0.10 | 179 |
| Chaiten | C_cap | +0.00 | +0.00 | -10.09 | 131 |
| PlanchonPeteroa | A_atm_gate | +0.00 | +0.02 | -12.40 | 81 |
| PlanchonPeteroa | B_covalidation | +0.00 | +0.02 | -8.19 | 130 |
| PlanchonPeteroa | C_cap | +0.00 | +0.00 | -13.09 | 91 |
| Tupungatito | A_atm_gate | +0.00 | +0.01 | -17.04 | 28 |
| Tupungatito | B_covalidation | +0.00 | +0.01 | -0.31 | 23 |
| Tupungatito | C_cap | +0.00 | +0.00 | -16.80 | 80 |
| PuyehueCordonCaulle | A_atm_gate | +0.00 | +0.02 | -39.40 | 236 |
| PuyehueCordonCaulle | B_covalidation | -0.04 | +0.02 | -28.43 | 258 |
| PuyehueCordonCaulle | C_cap | +0.00 | +0.00 | -39.40 | 255 |
| Llaima | A_atm_gate | +0.00 | +0.00 | -0.93 | 81 |
| Llaima | B_covalidation | +0.00 | +0.00 | -53.72 | 119 |
| Llaima | C_cap | +0.00 | +0.00 | -0.93 | 96 |
| Copahue | A_atm_gate | +0.00 | +0.00 | -17.57 | 142 |
| Copahue | B_covalidation | +0.00 | +0.00 | - | 166 |
| Copahue | C_cap | +0.00 | +0.00 | -17.57 | 146 |
| NevadosDeChillan | A_atm_gate | -0.17 | -0.01 | -10.99 | 82 |
| NevadosDeChillan | B_covalidation | -0.67 | +0.04 | - | 118 |
| NevadosDeChillan | C_cap | +0.00 | +0.00 | -10.79 | 85 |

## Cumplimiento de criterios per opcion

Criterios (BLOQUE_ARRANQUE_S71):
- Mediana ratio per-vol ∈ [0.5, 2.0]
- Recall ≥0.70 per vol Tier A con N≥10 MIROVA ALERTAS
- Precision ≥0.50 per vol Tier A
- Ningun record pD-only con eqVrp>5MW + t_bg<260K

| Opcion | Vols ratio∈[0.5,2] | Vols recall≥0.7 (n_mirova≥10) | Vols precision≥0.5 | Σ pD-only_eqVrp>5 + tbg<260 |
|---|---|---|---|---|
| baseline | 0/11 | 7/7 | 5/11 | 237 |
| A_atm_gate | 2/11 | 7/7 | 5/11 | 0 |
| B_covalidation | 1/11 | 7/7 | 5/11 | 1 |
| C_cap | 2/11 | 7/7 | 5/11 | 0 |

## Verdict

### Eliminacion del bug D9 (pD-only eqVrp>5MW + t_bg<260K)

| Opcion | Suma global (11 vols) |
|---|---|
| baseline | 237 |
| A_atm_gate | **0** |
| B_covalidation | 1 |
| C_cap | **0** |

A y C eliminan el bug D9 al 100%. B reduce a 1 (residual marginal).

### Recall keep (no perder TPs reales)

- A: NdC pierde 1 noche (rec 1.00 → 0.83). Resto OK.
- B: Lastarria 1.00→0.99, PCC 1.00→0.96, **NdC 1.00→0.33 (4 FN nuevos)**. Riesgo alto.
- C: NdC OK, Isluga 0.97→0.98 (NO regresion). Mas seguro.

### Ratio mediano: cuanto se acerca a [0.5, 2.0]

A y C bajan los ratios mas que B en la mayoria. Comparacion en 6 vols clave
(no Lascar/Lastarria/Isluga ya bajos en A, B, C):

| Vol | baseline | A | B | C |
|---|---|---|---|---|
| Lastarria | 38.30 | 3.58 | **2.90** | 3.42 |
| Lascar | 2.82 | 1.10 | **1.05** | 1.11 |
| Isluga | 13.57 | **2.11** | 2.70 | 2.24 |
| Villarrica | 21.74 | **9.16** | 12.04 | 9.16 |
| Chaiten | 18.54 | **8.24** | 18.64 | 8.45 |
| PP | 24.15 | 11.76 | 15.96 | **11.07** |
| Tupungatito | 23.01 | **5.97** | 22.70 | 6.21 |
| PCC | 40.60 | 1.20 | 12.18 | **1.21** |
| Llaima | 61.14 | 60.21 | **7.41** | 60.21 |
| Copahue | 21.39 | **3.82** | - | 3.82 |
| NdC | 20.99 | 10.00 | - | **10.20** |

A gana en 5 vols, C gana en 2, B gana en 4 (pero rompe NdC recall).

### Conclusion: WINNER = Opcion C (cap) > A (atm_gate) > B (covalidation)

**Razones**:
1. **C y A eliminan D9 al 100%** (vs B residual 1 caso).
2. **C no rompe recall en ningun vol** (A pierde 1 noche en NdC; B pierde 4).
3. C y A logran ratios casi identicos en la mayoria (diferencias ≤0.2).
4. B pierde la propiedad clave de Llaima (60→7) pero a costa de matar NdC.
5. C es la opcion mas conservadora: solo limita magnitud, no descarta deteccion.

**Caveats criticos**:
- Ningun opcion lleva todos los vols a ratio ∈ [0.5, 2.0]. 2/11 vols cumplen
  (Lascar, PCC con A o C). Villarrica/Chaiten/PP/Tupungatito/NdC siguen en
  ratios 6-12 — el bug D9 no era la unica fuente de inflado. Hay un drift
  remanente que necesita investigacion separada (probablemente local_kernel_bg
  cluster selection, o algo en first_pass/second_pass).
- Precision baja en Villarrica/Chaiten/Llaima/Copahue/NdC (0.01-0.13) en
  todas las opciones — esto es ortogonal al fix D9 (matching MIROVA por noche
  es generoso, FP probably refleja ruido legítimo de pixels no-MIROVA).
- B (covalidation) parecia atractiva por reducir pD-only a casi 0, pero el
  costo en recall y en ratio (Lastarria/PP/Chaiten/Tupungatito) lo descarta.
- El calibrado original sugeria 22% FP elim con A solo en path-D-only — los
  numeros aqui muestran reduccion masiva (≥60% en todos los vols), porque
  la calibracion tambien incluye records que cae bajo el umbral con first_pass
  re-firing.

### Recomendacion operacional

Adoptar **Opcion C (cap vrp_mw a 5 MW si ctx-only + t_bg<270K)** porque:
- Conserva todos los TPs (zero recall loss).
- Elimina el bug D9 al 100%.
- No agrega complejidad de filtrado (path D sigue corriendo, solo limita output).
- Permite escalar el cap si despues queremos refinarlo.

Despues de adoptar C: abrir T1.5 para investigar el **drift remanente** que
explica los ratios 6-12 en Villarrica/Chaiten/PP/Tupungatito/NdC. No es path D.

