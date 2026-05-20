# Calibracion umbral t_bg_k - Path D fix D9 (S71 T1)

**Params**: eqVrp >= 5.0 MW (path-D-only), match MIROVA +/- 3.0h (CONS+OCR ALERTA).

## Per-volcano summary (path-D-only records, eqVrp>5 MW)

| Volcan | total_records | N_pD_only | N_TP | t_bg_TP_median | N_FP | t_bg_FP_median |
|---|---|---|---|---|---|---|
| Lastarria | 1014 | 189 | 76 | 268.2 | 113 | 267.4 |
| Lascar | 1016 | 173 | 97 | 272.0 | 76 | 270.9 |
| Isluga | 971 | 141 | 40 | 273.5 | 101 | 269.2 |
| Villarrica | 1199 | 336 | 15 | 281.5 | 321 | 276.5 |
| Chaiten | 1252 | 298 | 7 | 280.3 | 291 | 269.7 |
| PlanchonPeteroa | 1136 | 203 | 34 | 277.3 | 169 | 277.1 |
| Tupungatito | 1118 | 214 | 40 | 269.5 | 174 | 268.6 |
| PuyehueCordonCaulle | 1246 | 458 | 151 | 275.9 | 307 | 270.0 |
| Llaima | 1198 | 189 | 0 | - | 189 | 275.8 |
| Copahue | 1182 | 262 | 0 | - | 262 | 275.6 |
| NevadosDeChillan | 1161 | 176 | 2 | 256.6 | 174 | 279.2 |

## Per-volcano t_bg_k distribution (TPs)

| Volcan | n | mean | p10 | p25 | median | p75 | p90 |
|---|---|---|---|---|---|---|---|
| Lastarria | 76 | 268.2 | 264.3 | 265.6 | 268.2 | 270.2 | 273.4 |
| Lascar | 97 | 270.6 | 266.6 | 269.6 | 272.0 | 274.3 | 275.9 |
| Isluga | 40 | 270.1 | 260.3 | 265.5 | 273.5 | 275.6 | 277.6 |
| Villarrica | 15 | 281.6 | 279.2 | 280.1 | 281.5 | 283.0 | 284.6 |
| Chaiten | 7 | 277.5 | 262.7 | 272.2 | 280.3 | 285.0 | 289.4 |
| PlanchonPeteroa | 34 | 276.4 | 267.8 | 272.5 | 277.3 | 280.8 | 282.8 |
| Tupungatito | 40 | 267.8 | 257.2 | 265.6 | 269.5 | 272.8 | 274.0 |
| PuyehueCordonCaulle | 151 | 275.9 | 268.2 | 272.6 | 275.9 | 280.3 | 283.8 |
| NevadosDeChillan | 2 | 256.6 | 241.8 | 247.4 | 256.6 | 265.8 | 271.3 |

## Per-volcano t_bg_k distribution (FPs)

| Volcan | n | mean | p10 | p25 | median | p75 | p90 |
|---|---|---|---|---|---|---|---|
| Lastarria | 113 | 267.1 | 262.7 | 264.6 | 267.4 | 269.8 | 272.4 |
| Lascar | 76 | 270.4 | 266.5 | 268.7 | 270.9 | 273.6 | 275.3 |
| Isluga | 101 | 265.6 | 253.7 | 263.7 | 269.2 | 272.8 | 274.6 |
| Villarrica | 321 | 273.8 | 260.2 | 269.4 | 276.5 | 281.3 | 284.5 |
| Chaiten | 291 | 268.0 | 254.2 | 261.7 | 269.7 | 275.3 | 280.2 |
| PlanchonPeteroa | 169 | 272.9 | 260.7 | 268.2 | 277.1 | 280.5 | 282.1 |
| Tupungatito | 174 | 265.6 | 248.5 | 263.8 | 268.6 | 271.7 | 273.7 |
| PuyehueCordonCaulle | 307 | 269.0 | 256.8 | 266.2 | 270.0 | 275.4 | 279.1 |
| Llaima | 189 | 272.9 | 256.2 | 267.8 | 275.8 | 281.4 | 284.1 |
| Copahue | 262 | 272.7 | 259.9 | 268.5 | 275.6 | 279.6 | 282.6 |
| NevadosDeChillan | 174 | 275.4 | 261.7 | 270.2 | 279.2 | 283.1 | 285.4 |

## ROC global: skip path D if t_bg_k < X

| Threshold K | TP_lost | TP_total | Recall_kept | FP_eliminated | FP_total | FP_elim_frac |
|---|---|---|---|---|---|---|
| 255 | 11 | 462 | 0.976 | 184 | 2177 | 0.085 |
| 260 | 20 | 462 | 0.957 | 277 | 2177 | 0.127 |
| 265 | 45 | 462 | 0.903 | 475 | 2177 | 0.218 |
| 268 | 97 | 462 | 0.790 | 718 | 2177 | 0.330 |
| 270 | 156 | 462 | 0.662 | 886 | 2177 | 0.407 |
| 273 | 227 | 462 | 0.509 | 1182 | 2177 | 0.543 |
| 275 | 297 | 462 | 0.357 | 1371 | 2177 | 0.630 |
| 278 | 366 | 462 | 0.208 | 1611 | 2177 | 0.740 |
| 280 | 394 | 462 | 0.147 | 1763 | 2177 | 0.810 |

## ROC per volcano (TPs lost / FPs eliminated at each threshold)

### Lastarria

| Threshold K | TP_lost/TP_total | FP_eliminated/FP_total |
|---|---|---|
| 255 | 0/76 | 2/113 |
| 260 | 0/76 | 3/113 |
| 265 | 10/76 | 33/113 |
| 268 | 36/76 | 64/113 |
| 270 | 56/76 | 86/113 |
| 273 | 64/76 | 106/113 |
| 275 | 72/76 | 110/113 |
| 278 | 76/76 | 113/113 |
| 280 | 76/76 | 113/113 |

### Lascar

| Threshold K | TP_lost/TP_total | FP_eliminated/FP_total |
|---|---|---|
| 255 | 4/97 | 2/76 |
| 260 | 4/97 | 2/76 |
| 265 | 6/97 | 6/76 |
| 268 | 15/97 | 15/76 |
| 270 | 30/97 | 33/76 |
| 273 | 60/97 | 52/76 |
| 275 | 80/97 | 67/76 |
| 278 | 96/97 | 74/76 |
| 280 | 97/97 | 75/76 |

### Isluga

| Threshold K | TP_lost/TP_total | FP_eliminated/FP_total |
|---|---|---|
| 255 | 3/40 | 11/101 |
| 260 | 4/40 | 19/101 |
| 265 | 10/40 | 34/101 |
| 268 | 11/40 | 46/101 |
| 270 | 15/40 | 58/101 |
| 273 | 19/40 | 76/101 |
| 275 | 24/40 | 92/101 |
| 278 | 39/40 | 100/101 |
| 280 | 40/40 | 101/101 |

### Villarrica

| Threshold K | TP_lost/TP_total | FP_eliminated/FP_total |
|---|---|---|
| 255 | 0/15 | 22/321 |
| 260 | 0/15 | 32/321 |
| 265 | 0/15 | 49/321 |
| 268 | 0/15 | 75/321 |
| 270 | 0/15 | 88/321 |
| 273 | 0/15 | 117/321 |
| 275 | 0/15 | 142/321 |
| 278 | 1/15 | 190/321 |
| 280 | 3/15 | 220/321 |

### Chaiten

| Threshold K | TP_lost/TP_total | FP_eliminated/FP_total |
|---|---|---|
| 255 | 0/7 | 38/291 |
| 260 | 1/7 | 61/291 |
| 265 | 1/7 | 96/291 |
| 268 | 2/7 | 126/291 |
| 270 | 2/7 | 149/291 |
| 273 | 2/7 | 193/291 |
| 275 | 2/7 | 216/291 |
| 278 | 2/7 | 242/291 |
| 280 | 3/7 | 259/291 |

### PlanchonPeteroa

| Threshold K | TP_lost/TP_total | FP_eliminated/FP_total |
|---|---|---|
| 255 | 0/34 | 13/169 |
| 260 | 0/34 | 17/169 |
| 265 | 1/34 | 31/169 |
| 268 | 4/34 | 42/169 |
| 270 | 5/34 | 48/169 |
| 273 | 9/34 | 60/169 |
| 275 | 13/34 | 70/169 |
| 278 | 19/34 | 91/169 |
| 280 | 23/34 | 119/169 |

### Tupungatito

| Threshold K | TP_lost/TP_total | FP_eliminated/FP_total |
|---|---|---|
| 255 | 2/40 | 24/174 |
| 260 | 5/40 | 32/174 |
| 265 | 7/40 | 53/174 |
| 268 | 13/40 | 84/174 |
| 270 | 22/40 | 103/174 |
| 273 | 30/40 | 147/174 |
| 275 | 38/40 | 165/174 |
| 278 | 40/40 | 174/174 |
| 280 | 40/40 | 174/174 |

### PuyehueCordonCaulle

| Threshold K | TP_lost/TP_total | FP_eliminated/FP_total |
|---|---|---|
| 255 | 1/151 | 25/307 |
| 260 | 5/151 | 43/307 |
| 265 | 9/151 | 71/307 |
| 268 | 15/151 | 120/307 |
| 270 | 25/151 | 153/307 |
| 273 | 42/151 | 201/307 |
| 275 | 66/151 | 226/307 |
| 278 | 91/151 | 263/307 |
| 280 | 110/151 | 281/307 |

### Llaima

| Threshold K | TP_lost/TP_total | FP_eliminated/FP_total |
|---|---|---|
| 255 | 0/0 | 18/189 |
| 260 | 0/0 | 24/189 |
| 265 | 0/0 | 33/189 |
| 268 | 0/0 | 49/189 |
| 270 | 0/0 | 56/189 |
| 273 | 0/0 | 74/189 |
| 275 | 0/0 | 90/189 |
| 278 | 0/0 | 116/189 |
| 280 | 0/0 | 126/189 |

### Copahue

| Threshold K | TP_lost/TP_total | FP_eliminated/FP_total |
|---|---|---|
| 255 | 0/0 | 18/262 |
| 260 | 0/0 | 27/262 |
| 265 | 0/0 | 43/262 |
| 268 | 0/0 | 63/262 |
| 270 | 0/0 | 70/262 |
| 273 | 0/0 | 101/262 |
| 275 | 0/0 | 123/262 |
| 278 | 0/0 | 170/262 |
| 280 | 0/0 | 199/262 |

### NevadosDeChillan

| Threshold K | TP_lost/TP_total | FP_eliminated/FP_total |
|---|---|---|
| 255 | 1/2 | 11/174 |
| 260 | 1/2 | 17/174 |
| 265 | 1/2 | 26/174 |
| 268 | 1/2 | 34/174 |
| 270 | 1/2 | 42/174 |
| 273 | 1/2 | 55/174 |
| 275 | 2/2 | 70/174 |
| 278 | 2/2 | 78/174 |
| 280 | 2/2 | 96/174 |

## Recommendation

**Recommended threshold: skip path D if t_bg_k < 265 K**

- Recall preserved (TPs kept): 0.903 (417/462)
- FPs eliminated: 475/2177 (21.8%)

## Caveats y heterogeneidad por volcan

1. **El umbral T_bg < 265 K es conservador y de bajo rendimiento**: solo elimina ~22% de los FPs path-D-only. El problema D9 no se reduce a "cirrus alto < 265 K". Las distribuciones t_bg_k de TPs y FPs **se solapan fuertemente** en todos los Tier A (FP_median y TP_median difieren <2 K en Lastarria, Lascar, Isluga, PlanchonPeteroa, PuyehueCordonCaulle, Tupungatito).
2. **Cross-check S70-2 T4 NO se reproduce a escala**: el reporte previo afirmaba "91% FPs Lastarria con t_bg<270K". Aqui Lastarria FP_p90 = 272.4 K (no <270). El analisis previo era sobre 22 records >5 MW; aqui hay 113 FPs. Posible diferencia: definicion de FP, ventana temporal, o universo de records.
3. **Heterogeneidad fuerte por volcan**:
   - **Villarrica, Chaiten** (regimen Muy Bajo): pocos TPs (15, 7) - umbrales agresivos (270 K) eliminan ~25-50% FPs sin perder TPs. Estos volcanes si responden a un cutoff t_bg_k.
   - **Lastarria, Lascar, Tupungatito** (ΔT moderado, t_bg TP y FP solapan ~268-272 K): cualquier umbral 265-270 K saca tantos TPs como FPs. **No es separable por t_bg_k solo.**
   - **Llaima, Copahue, NevadosDeChillan**: 0-2 TPs, 174-262 FPs - todo path-D-only se podria considerar FP, pero n_TP=0 no permite calibrar (sub-pixel real?).
4. **Sample insuficiente per-vol para Villarrica/Chaiten/NdC** (n_TP < 20). El umbral global se domina por Lastarria+Lascar+PuyehueCordonCaulle (324/462 TPs).
5. **Conclusion operacional**: si la decision es agregar un guard `t_bg_k < 265 K` como Opcion A, el costo es 45 TPs perdidos a cambio de 475 FPs eliminados (ratio FP/TP ~10.5). Aceptable como **mitigacion parcial**, no como fix definitivo. **El fix D9 requiere mas que un solo umbral t_bg_k** - probablemente Opcion B/C (rechazar path D si NTI absoluto bajo + bg homogeneo, o requerir confirmacion otra path) o por-volcan-tuneo.
6. **Decision sugerida**: aplicar **Opcion A con t_bg_k < 265 K como guard inicial** (gana 22% FPs sin perder 10% recall) y planear A/B contra Opcion B en S71 T1 follow-up. Recall por vol critico: Lastarria/Lascar/PuyehueCordonCaulle mantienen 87-94% TPs; Tupungatito pierde 17% TPs (7/40).
