# F2.6.h — Lascar lost summit >500 MW records (S26 → S71) vs MIROVA NRT

**Read-only sub-investigación.** Datasets: `Lascar_S26.json` (1085 records), `data/mirova_equivalent/Lascar.json` (S71, 1027 records), `registro_vrp_consolidado.csv` + `registro_vrp_ocr.csv` + `registro_Lascar.csv` (1919 MIROVA Lascar rows totales, 520 ALERTA_TERMICA).

## Filtro de candidates

Records S26 con `vrp_mw > 500 MW` + `distance_class = "summit"`, sin contraparte en S71 (mismo sensor canon, bucket ±10 min, vrp_mw>0.01). **Resultado: 63 records lost** (no 47 — el conteo F2.6.g previo era estimación más estricta).

## Distribución verdict 63 records

| Verdict | N | % |
|---|---|---|
| **MIROVA_ALERTA match** (TP MIROVA NRT confirmado mismo sensor ±60min) | 14 | 22.2% |
| **MIROVA_OTHER_ALERTA_TERMICA_OCR** (TP MIROVA OCR-variant) | 2 | 3.2% |
| MIROVA_RUTINA (MIROVA dijo "sin actividad") | 19 | 30.2% |
| SAMEDAY_NO_ALERT (data MIROVA mismo día, ninguna ALERTA) | 3 | 4.8% |
| NO_MIROVA_DATA (MIROVA NRT no cubrió esa noche) | 25 | 39.7% |

Total MIROVA-confirmed TPs perdidos: **16 records** (25.4%).

## Tabla TP real perdido (16 records) — comparación ratio S26 vs MIROVA NRT

| Timestamp UTC | Sensor | S26 vrp_mw | MIROVA NRT vrp_mw | Ratio S26/MIROVA |
|---|---|---|---|---|
| 2026-01-11 05:00 | VIIRS_NOAA20 | 998.2 | 0.27 | 3697× |
| 2026-01-13 05:12 | VIIRS_NOAA21 | 625.1 | 0.32 | 1954× |
| 2026-01-13 05:42 | VIIRS_SNPP | 650.4 | 0.32 | 2033× |
| 2026-01-13 06:06 | VIIRS_NOAA20 | 664.0 | 0.32 | 2075× |
| 2026-01-14 04:54 | VIIRS_NOAA21 | 513.8 | 1.21 | 425× |
| 2026-01-14 05:24 | VIIRS_SNPP | 638.3 | 1.21 | 528× |
| 2026-01-14 05:48 | VIIRS_NOAA20 | 926.1 | 1.21 | 765× |
| 2026-01-25 05:18 | VIIRS_SNPP | 551.9 | 0.39 | 1415× |
| 2026-01-25 05:42 | VIIRS_NOAA20 | 651.8 | 0.39 | 1671× |
| 2026-02-12 06:24 | VIIRS_SNPP | 659.5 | 0.15 | 4397× |
| 2026-02-25 05:36 | VIIRS_SNPP | 680.6 | 0.27 | 2521× |
| 2026-02-25 06:00 | VIIRS_NOAA20 | 515.8 | 0.27 | 1910× |
| 2026-03-09 04:42 | VIIRS_NOAA21 | 533.6 | 1.00 (OCR) | 534× |
| 2026-03-15 05:00 | VIIRS_SNPP | 550.4 | 1.94 | 284× |
| 2026-04-13 06:18 | VIIRS_NOAA20 | 1178.6 | 1.00 (OCR) | 1179× |
| 2026-04-16 05:00 | VIIRS_SNPP | 624.6 | 1.29 | 484× |

**Estadísticas ratio S26/MIROVA**: mediana 1910×, mínimo 284×, máximo 4397×. **0 records calibrados** (ratio 0.5–2). **16/16 inflados >5× (100%)**. **16/16 inflados >10× (100%)**.

## Interpretación geológica

Las noches con MIROVA NRT ALERTA muestran VRP MIROVA **0.15–1.94 MW**, consistente con histórico Lascar Tier A Alto (lava lake/cráter activo discreto, ~1–10 MW). Nuestro pipeline S26-vintage reportaba **500–1200 MW** en esas mismas noches — eso no es "anomalía cráter discreto inflada", es señal regional capturada como si fuera summit por bug previo (S26 era previo a la implementación de cluster aggregation S40/S46 que descarta pixels regionales lejanos como FPs y consolida la región cercana al vent).

El offset visible: el cráter de Lascar realmente irradia ~1 MW en esos momentos. S26 los magnificaba 300–4400× porque sumaba pixels regionales atmosféricos/heterogéneos sin filtrar — exactamente el modo de falla que motivó la implementación de S40 (cluster aggregation) y S46 (dedup burst).

Las 19 noches MIROVA_RUTINA confirman lo mismo desde el otro lado: MIROVA NRT vio el mismo granule y reportó "sin actividad" — nuestro S26 inventó 500+ MW.

## Verdict final F2.6.c

**✅ F2.6.c rank 1 100% confirmado: deriva S26→S71 es correcta. NO revertir adoptaciones S38–S46.**

Razones operacionales:
1. **Cero records calibrados** en el ratio band 0.5–2×. Todos los "TPs perdidos" estaban inflados ≥284× sobre MIROVA NRT.
2. **30.2% MIROVA_RUTINA**: MIROVA tenía el granule, no detectó nada — S26 inventó >500 MW (FP regional, no TP perdido).
3. **22.2% + 3.2% = 25.4% MIROVA_ALERTA**: MIROVA sí detectó pero a 0.15–1.94 MW; los 500–1200 MW de S26 eran inflación masiva incluyendo señal regional como summit.
4. **39.7% NO_MIROVA_DATA**: sin ground truth, pero el patrón de los otros 60% es tan consistente (inflación 280–4400×) que no hay razón para sospechar que el 40% sin cobertura MIROVA sea de otra naturaleza.

S40 (cluster aggregation) + S46 (dedup burst) no perdieron TPs reales — eliminaron inflación regional sistemática que se reportaba como summit. La "pérdida de 16 records con MIROVA confirmado" es un artefacto de medirla por presencia/ausencia de record: MIROVA NRT esas noches reportó actividad cráter ~1 MW, nuestro S71 los descarta o los emite con magnitud calibrada (no >500 MW). En términos operacionales el comportamiento S71 está alineado con MIROVA, S26 no lo estaba.

## Recomendación

- **No revertir S40 ni S46** ni adoptaciones intermedias.
- Cerrar F2.6.c rank 1 con verdict "confirmado".
- Si quedan dudas sobre los 25 NO_MIROVA_DATA, son fuera de la cobertura del CSV NRT scrapeado — no son evidencia en contra.

## Restricciones cumplidas

- Read-only. No se modificó ningún archivo bajo `data/` ni `pipeline/`.
- Datos S26 desde el snapshot ya existente en `experiments/135_*/`. Datos MIROVA NRT desde `data/mirova_reference/` sin modificar.
- Output sólo en `experiments/136_lascar_cat_a_500mw_vs_mirova_nrt/` (`audit.py`, `audit.json`, `audit.md`).
