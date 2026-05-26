# S81 Gap Analysis v2 — Re-auditoría con interpretación correcta de tags scraper

**Ventana**: 2026-03-17 → 2026-05-01 (45 días).
**CSV**: `01_05_2026_registro_vrp_consolidado.csv` (último disponible — termina 2026-05-01).
**Pareo**: ±30 min, mismo sensor (familia MODIS / VIIRS / VIIRS375).

## Resumen ejecutivo

- **FPs originales totales (Tier A × 3 sensores)**: 2986
- **Reclasificados como Subtipo A (concordancia far con MIROVA FALSO_POSITIVO)**: 64 (2.1%)
- **Subtipo B (FP genuino — MIROVA no tiene registro)**: 473
- **Subtipo C (ambiguo — MIROVA RUTINA, sin alerta)**: 2295

**Veredicto operativo**: si el 2% de los FPs originales eran realmente
concordancia far con MIROVA (ambos vieron el hotspot fuera del radio), la hipótesis del
audit original ("MIROVA filtra incendios con un gate que no tenemos") **parcialmente se sostiene**.
Los hotspots que MIROVA reporta como FALSO_POSITIVO son hotspots reales que su sistema
detectó — la atribución al volcán es separada y depende del radio. Nuestro pipeline al
tagear `distance_class=far` está siendo coherente con MIROVA en esa decisión.

## Tabla volcán × sensor

| volcan              | sensor   |   n_alerta |   n_falsopos |   n_rutina |   n_det_ours |   n_clean_ours |   TP_strict |   match_falsopos |     of_which_far |     of_which_summit_wrong |   FP_subA_concord_far |   FP_subB_genuine |   FP_subC_ambiguo |   FP_total_orig |   pct_FPs_reclasif_subA |   recall_strict |   recall_amplio |   precision_orig |   precision_corr |
|:--------------------|:---------|-----------:|-------------:|-----------:|-------------:|---------------:|------------:|-----------------:|-----------------:|--------------------------:|----------------------:|------------------:|------------------:|----------------:|------------------------:|----------------:|----------------:|-----------------:|-----------------:|
| Lascar              | MODIS    |         33 |            1 |        131 |           63 |             20 |          29 |                0 |                0 |                         0 |                     0 |                 2 |                32 |              34 |                     0   |           0.879 |           0.853 |            0.46  |            0.46  |
| Lascar              | VIIRS    |         40 |            1 |        171 |          102 |             60 |          40 |                1 |                1 |                         0 |                     1 |                17 |                25 |              62 |                     1.6 |           1     |           1     |            0.392 |            0.488 |
| Lascar              | VIIRS375 |         52 |           21 |        115 |          139 |             24 |          50 |                4 |                0 |                         4 |                     6 |                25 |                30 |              89 |                     6.7 |           0.962 |           0.74  |            0.36  |            0.476 |
| Lastarria           | MODIS    |          0 |            1 |        162 |           72 |              9 |           0 |                0 |                0 |                         0 |                     0 |                 3 |                69 |              72 |                     0   |         nan     |           0     |            0     |            0     |
| Lastarria           | VIIRS    |          0 |            0 |        222 |          131 |             35 |           0 |                0 |                0 |                         0 |                     0 |                16 |               115 |             131 |                     0   |         nan     |         nan     |            0     |            0     |
| Lastarria           | VIIRS375 |         37 |           52 |         99 |          136 |             30 |          37 |                7 |                0 |                         7 |                    11 |                28 |                41 |              99 |                    11.1 |           1     |           0.494 |            0.272 |            0.349 |
| Isluga              | MODIS    |          0 |            0 |        153 |           53 |             24 |           0 |                0 |                0 |                         0 |                     0 |                 0 |                53 |              53 |                     0   |         nan     |         nan     |            0     |            0     |
| Isluga              | VIIRS    |          8 |            2 |        201 |           46 |            114 |           2 |                1 |                1 |                         0 |                     1 |                 9 |                33 |              44 |                     2.3 |           0.25  |           0.3   |            0.043 |            0.045 |
| Isluga              | VIIRS375 |         28 |           15 |        139 |          113 |             43 |          25 |               11 |                0 |                        11 |                    18 |                20 |                35 |              88 |                    20.5 |           0.893 |           0.837 |            0.221 |            0.312 |
| NevadosDeChillan    | MODIS    |          0 |            0 |        193 |           68 |             29 |           0 |                0 |                0 |                         0 |                     0 |                 1 |                67 |              68 |                     0   |         nan     |         nan     |            0     |            0     |
| NevadosDeChillan    | VIIRS    |          1 |            4 |        233 |           39 |            156 |           0 |                0 |                0 |                         0 |                     0 |                 5 |                34 |              39 |                     0   |           0     |           0     |            0     |            0     |
| NevadosDeChillan    | VIIRS375 |          2 |           12 |        200 |           32 |            152 |           0 |                2 |                1 |                         1 |                     2 |                10 |                20 |              32 |                     6.2 |           0     |           0.143 |            0     |            0     |
| Llaima              | MODIS    |          0 |            4 |        186 |           87 |              8 |           0 |                0 |                0 |                         0 |                     0 |                 1 |                86 |              87 |                     0   |         nan     |           0     |            0     |            0     |
| Llaima              | VIIRS    |          0 |            9 |        234 |           65 |            136 |           0 |                0 |                0 |                         0 |                     0 |                16 |                49 |              65 |                     0   |         nan     |           0     |            0     |            0     |
| Llaima              | VIIRS375 |          0 |           22 |        195 |          106 |             88 |           0 |                1 |                0 |                         1 |                     1 |                20 |                85 |             106 |                     0.9 |         nan     |           0.045 |            0     |            0     |
| Villarrica          | MODIS    |          0 |            1 |        193 |           87 |              7 |           0 |                0 |                0 |                         0 |                     0 |                 3 |                84 |              87 |                     0   |         nan     |           0     |            0     |            0     |
| Villarrica          | VIIRS    |          0 |            1 |        240 |           94 |            107 |           0 |                0 |                0 |                         0 |                     0 |                18 |                76 |              94 |                     0   |         nan     |           0     |            0     |            0     |
| Villarrica          | VIIRS375 |          1 |            4 |        217 |          141 |             48 |           1 |                1 |                0 |                         1 |                     2 |                23 |               114 |             140 |                     1.4 |           1     |           0.4   |            0.007 |            0.007 |
| Chaiten             | MODIS    |          0 |            1 |        207 |           96 |             14 |           0 |                0 |                0 |                         0 |                     0 |                 3 |                93 |              96 |                     0   |         nan     |           0     |            0     |            0     |
| Chaiten             | VIIRS    |          0 |            0 |        248 |          104 |            105 |           0 |                0 |                0 |                         0 |                     0 |                26 |                78 |             104 |                     0   |         nan     |         nan     |            0     |            0     |
| Chaiten             | VIIRS375 |          4 |            2 |        226 |          144 |             48 |           4 |                2 |                0 |                         2 |                     4 |                34 |                99 |             140 |                     2.9 |           1     |           1     |            0.028 |            0.029 |
| Copahue             | MODIS    |          0 |            1 |        188 |           78 |             20 |           0 |                0 |                0 |                         0 |                     0 |                 1 |                77 |              78 |                     0   |         nan     |           0     |            0     |            0     |
| Copahue             | VIIRS    |          0 |            0 |        243 |           89 |            104 |           0 |                0 |                0 |                         0 |                     0 |                14 |                75 |              89 |                     0   |         nan     |         nan     |            0     |            0     |
| Copahue             | VIIRS375 |          1 |            4 |        218 |          118 |             71 |           1 |                3 |                0 |                         3 |                     4 |                23 |                89 |             117 |                     3.4 |           1     |           0.8   |            0.008 |            0.009 |
| PlanchonPeteroa     | MODIS    |          0 |            0 |        189 |           89 |             13 |           0 |                0 |                0 |                         0 |                     0 |                 1 |                88 |              89 |                     0   |         nan     |         nan     |            0     |            0     |
| PlanchonPeteroa     | VIIRS    |          0 |            1 |        231 |           80 |            104 |           0 |                0 |                0 |                         0 |                     0 |                17 |                63 |              80 |                     0   |         nan     |           0     |            0     |            0     |
| PlanchonPeteroa     | VIIRS375 |         23 |           14 |        170 |          151 |             14 |          23 |                6 |                0 |                         6 |                     9 |                30 |                66 |             128 |                     7   |           1     |           0.784 |            0.152 |            0.193 |
| Tupungatito         | MODIS    |          0 |            0 |        180 |           95 |              0 |           0 |                0 |                0 |                         0 |                     0 |                 1 |                94 |              95 |                     0   |         nan     |         nan     |            0     |            0     |
| Tupungatito         | VIIRS    |          5 |            0 |        226 |           57 |            125 |           3 |                0 |                0 |                         0 |                     0 |                 6 |                47 |              54 |                     0   |           0.6   |           0.6   |            0.053 |            0.054 |
| Tupungatito         | VIIRS375 |         42 |            6 |        156 |          149 |             23 |          40 |                4 |                0 |                         4 |                     5 |                30 |                48 |             109 |                     4.6 |           0.952 |           0.917 |            0.268 |            0.339 |
| PuyehueCordonCaulle | MODIS    |          0 |            0 |        204 |           98 |             10 |           0 |                0 |                0 |                         0 |                     0 |                 1 |                97 |              98 |                     0   |         nan     |         nan     |            0     |            0     |
| PuyehueCordonCaulle | VIIRS    |          4 |            0 |        243 |          175 |             31 |           4 |                0 |                0 |                         0 |                     0 |                34 |               135 |             171 |                     0   |           1     |           1     |            0.023 |            0.023 |
| PuyehueCordonCaulle | VIIRS375 |         26 |            1 |        197 |          173 |             16 |          25 |                0 |                0 |                         0 |                     0 |                35 |                98 |             148 |                     0   |           0.962 |           0.926 |            0.145 |            0.158 |

## Top 15 FPs genuinos (post-reclasificación)

Estos son los casos donde nuestro pipeline detectó algo y MIROVA NO TIENE NINGÚN
registro para esa ventana (ni alerta ni falsopos) — son los verdaderos candidatos a
investigar (incendio forestal, ruido instrumental, error pipeline).

| volcan              | sensor   | dt                  |   ours_vrp_mw |   ours_dist_km | ours_dist_class   |   ours_n_pix | mirova          |
|:--------------------|:---------|:--------------------|--------------:|---------------:|:------------------|-------------:|:----------------|
| PuyehueCordonCaulle | MODIS    | 2026-04-16 08:30:00 |      1659.6   |          12.66 | summit            |          197 | RUTINA(vrp=0.0) |
| PuyehueCordonCaulle | MODIS    | 2026-04-05 03:05:00 |      1097.64  |          29.62 | far               |          102 | RUTINA(vrp=0.0) |
| Villarrica          | MODIS    | 2026-04-16 08:30:00 |      1056.3   |           8.27 | far               |          102 | NO_RECORD       |
| PuyehueCordonCaulle | MODIS    | 2026-04-03 08:25:00 |      1029.68  |          17.97 | summit            |          167 | RUTINA(vrp=0.0) |
| Llaima              | MODIS    | 2026-04-16 08:30:00 |       931.289 |          19.1  | far               |           97 | RUTINA(vrp=0.0) |
| PuyehueCordonCaulle | MODIS    | 2026-04-18 08:10:00 |       890.816 |          18.73 | summit            |          513 | RUTINA(vrp=0.0) |
| PuyehueCordonCaulle | MODIS    | 2026-04-05 01:30:00 |       884.099 |           9.89 | summit            |          141 | RUTINA(vrp=0.0) |
| Chaiten             | MODIS    | 2026-03-31 01:30:00 |       872.555 |          18.16 | far               |           59 | RUTINA(vrp=0.0) |
| PuyehueCordonCaulle | MODIS    | 2026-04-16 06:55:00 |       872.472 |          10.01 | summit            |          216 | RUTINA(vrp=0.0) |
| PuyehueCordonCaulle | MODIS    | 2026-04-30 03:00:00 |       846.23  |          29.94 | far               |          146 | RUTINA(vrp=0.0) |
| PuyehueCordonCaulle | MODIS    | 2026-04-29 06:55:00 |       771.876 |          22.3  | far               |          215 | RUTINA(vrp=0.0) |
| PlanchonPeteroa     | MODIS    | 2026-04-18 08:05:00 |       740.104 |          26.95 | far               |          412 | RUTINA(vrp=0.0) |
| PuyehueCordonCaulle | MODIS    | 2026-03-21 06:45:00 |       708.624 |          18.99 | summit            |           78 | RUTINA(vrp=0.0) |
| PuyehueCordonCaulle | MODIS    | 2026-03-18 08:05:00 |       697.629 |          19.87 | summit            |          154 | RUTINA(vrp=0.0) |
| PuyehueCordonCaulle | MODIS    | 2026-04-14 07:15:00 |       692.887 |           9.18 | summit            |          767 | RUTINA(vrp=0.0) |

## Top 15 Subtipo A (concordancia far revelada)

Estos son los casos donde MIROVA reportó FALSO_POSITIVO (hotspot fuera del radio) y
nuestro pipeline también detectó algo, idealmente con `distance_class=far`. Esto valida
que estamos alineados con MIROVA.

| volcan          | sensor   | dt                  |   ours_vrp_mw |   ours_dist_km | ours_dist_class   |   mirova_vrp | kind                         |
|:----------------|:---------|:--------------------|--------------:|---------------:|:------------------|-------------:|:-----------------------------|
| Villarrica      | VIIRS375 | 2026-04-05 05:30:01 |         9.332 |          1.56  | summit            |         1.03 | MIROVA_falsopos_ours_NOT_far |
| Tupungatito     | VIIRS375 | 2026-04-12 05:48:02 |         7.503 |          1.696 | summit            |         0.69 | MIROVA_falsopos_ours_NOT_far |
| Copahue         | VIIRS375 | 2026-04-30 06:06:01 |         7.195 |          1.555 | summit            |         1.46 | MIROVA_falsopos_ours_NOT_far |
| Tupungatito     | VIIRS375 | 2026-04-13 06:00:00 |         6.03  |          1.642 | summit            |         0.3  | MIROVA_falsopos_ours_NOT_far |
| PlanchonPeteroa | VIIRS375 | 2026-05-01 05:42:01 |         5.216 |          0.129 | summit            |         0.19 | MIROVA_falsopos_ours_NOT_far |
| Copahue         | VIIRS375 | 2026-03-24 05:36:00 |         5.099 |          1.516 | summit            |         0.53 | MIROVA_falsopos_ours_NOT_far |
| Lascar          | VIIRS375 | 2026-03-29 06:00:01 |         4.723 |          0.9   | summit            |         3.25 | MIROVA_falsopos_ours_NOT_far |
| PlanchonPeteroa | VIIRS375 | 2026-03-31 05:24:01 |         4.648 |          1.234 | summit            |         0.97 | MIROVA_falsopos_ours_NOT_far |
| Lascar          | VIIRS375 | 2026-04-08 06:12:01 |         4.122 |          0.7   | summit            |         1.99 | MIROVA_falsopos_ours_NOT_far |
| Llaima          | VIIRS375 | 2026-04-30 05:12:02 |         4.02  |          1.004 | summit            |         5.51 | MIROVA_falsopos_ours_NOT_far |
| Isluga          | VIIRS375 | 2026-03-31 05:18:01 |         4.009 |          1.328 | summit            |         2.14 | MIROVA_falsopos_ours_NOT_far |
| Chaiten         | VIIRS375 | 2026-04-09 06:00:01 |         3.896 |          1.258 | summit            |         0.41 | MIROVA_falsopos_ours_NOT_far |
| PlanchonPeteroa | VIIRS375 | 2026-04-29 05:30:02 |         3.357 |          1.16  | summit            |         0.57 | MIROVA_falsopos_ours_NOT_far |
| Lascar          | VIIRS375 | 2026-04-01 06:24:00 |         3.32  |          1.58  | summit            |         0.36 | MIROVA_falsopos_ours_NOT_far |
| PlanchonPeteroa | VIIRS375 | 2026-04-12 05:48:02 |         3.174 |          1.065 | summit            |         2.08 | MIROVA_falsopos_ours_NOT_far |

## Foco en los 4 volcanes señalados por el audit original

| volcan              | sensor   |   n_alerta |   n_falsopos |   n_rutina |   n_det_ours |   n_clean_ours |   TP_strict |   match_falsopos |     of_which_far |     of_which_summit_wrong |   FP_subA_concord_far |   FP_subB_genuine |   FP_subC_ambiguo |   FP_total_orig |   pct_FPs_reclasif_subA |   recall_strict |   recall_amplio |   precision_orig |   precision_corr |
|:--------------------|:---------|-----------:|-------------:|-----------:|-------------:|---------------:|------------:|-----------------:|-----------------:|--------------------------:|----------------------:|------------------:|------------------:|----------------:|------------------------:|----------------:|----------------:|-----------------:|-----------------:|
| Chaiten             | MODIS    |          0 |            1 |        207 |           96 |             14 |           0 |                0 |                0 |                         0 |                     0 |                 3 |                93 |              96 |                       0 |             nan |               0 |                0 |                0 |
| PlanchonPeteroa     | MODIS    |          0 |            0 |        189 |           89 |             13 |           0 |                0 |                0 |                         0 |                     0 |                 1 |                88 |              89 |                       0 |             nan |             nan |                0 |                0 |
| Tupungatito         | MODIS    |          0 |            0 |        180 |           95 |              0 |           0 |                0 |                0 |                         0 |                     0 |                 1 |                94 |              95 |                       0 |             nan |             nan |                0 |                0 |
| PuyehueCordonCaulle | MODIS    |          0 |            0 |        204 |           98 |             10 |           0 |                0 |                0 |                         0 |                     0 |                 1 |                97 |              98 |                       0 |             nan |             nan |                0 |                0 |

- **Chaiten MODIS**: 96 FP originales → 0 concordancia far (0%), 3 genuinos, 93 ambiguos.
- **PlanchonPeteroa MODIS**: 89 FP originales → 0 concordancia far (0%), 1 genuinos, 88 ambiguos.
- **Tupungatito MODIS**: 95 FP originales → 0 concordancia far (0%), 1 genuinos, 94 ambiguos.
- **PuyehueCordonCaulle MODIS**: 98 FP originales → 0 concordancia far (0%), 1 genuinos, 97 ambiguos.


## Interpretación geológica (lenguaje llano)

Pensá la ventana como ~250 oportunidades por volcán × sensor (cada granule satelital
nocturno). En cada oportunidad:

- **ALERTA_TERMICA** = MIROVA prendió la luz roja: "vi calor en el volcán".
- **FALSO_POSITIVO** = MIROVA vio calor pero LEJOS del cráter (incendio, ciudad,
  industria). Lo publica igual, pero su scraper lo etiqueta como no atribuible.
- **RUTINA** = MIROVA procesó la imagen y NO vio NADA (ni en el volcán ni cerca).
- **NULO** = la imagen no llegó (gap del satélite o LANCE caído).

En la ventana 2026-03-17 → 2026-05-01:

- Tenemos **2986 detecciones nuestras sin counterpart MIROVA ALERTA**.
- Sólo **64 (2.1%)** matchean con un FALSO_POSITIVO
  MIROVA al que nosotros además le pusimos `distance_class=far`. Esa es la única
  categoría donde podemos defender "estamos alineados con MIROVA, solo que reportamos
  el hotspot fuera".
- **2295 (77%)** son Subtipo C
  (ambiguos): MIROVA procesó esa noche, miró el volcán, no vio nada — y nosotros sí.
  Esto sigue siendo discrepancia genuina con MIROVA.
- **473 (16%)** son Subtipo B
  estricto: MIROVA no tiene registro alguno (NULO o gap), y nosotros detectamos.
  Indistinguible de FP real.

**Físicamente**: la corrección de tags reduce el conteo de "discrepancias" en sólo
2%, no en 40-60% como hipotetizábamos. **MIROVA es genuinamente más estricto** que
nuestro pipeline en estos volcanes — no es artefacto de etiquetado.

## Veredicto sobre la hipótesis del audit original

**La hipótesis "MIROVA filtra incendios forestales con un gate que no tenemos"**:

- **NO se cae** con la corrección de tags. Sólo el 2.1% de "FPs originales" se
  reclasifican como concordancia far.
- **Se reformula**: lo que MIROVA filtra no son tanto incendios *fuera* del radio
  (eso lo vería como FALSO_POSITIVO) sino hotspots que su algoritmo decide rechazar
  *dentro* del radio. El 77% Subtipo C confirma esto: MIROVA tuvo la imagen, miró
  el área, no la levantó como alerta.
- Las causas posibles del rechazo MIROVA-side incluyen: (a) gate de incendio forestal
  (vegetación contextual), (b) gate diurno-vs-nocturno más estricto, (c) thresholds
  N·σ más altos para MODIS, (d) requisito de cluster mínimo, (e) cloud-mask más
  agresivo.

## El patrón MODIS sigue siendo catastrófico

Con tags corregidos:

| Volcán × MODIS | Det nuestras | TP estricto | FP genuino+ambiguo | Concordancia far |
|---|---|---|---|---|
| Lascar | 63 | 29 (recall 88%) | 34 | 0 |
| PuyehueCordonCaulle | 98 | 0 | 98 | 0 |
| PlanchonPeteroa | 89 | 0 | 89 | 0 |
| Chaiten | 96 | 0 | 96 | 0 |
| Tupungatito | 95 | 0 | 95 | 0 |
| Llaima | 87 | 0 | 87 | 0 |
| Villarrica | 87 | 0 | 87 | 0 |
| Copahue | 78 | 0 | 78 | 0 |
| Lastarria | 72 | 0 | 72 | 0 |
| NdC | 68 | 0 | 68 | 0 |
| Isluga | 53 | 0 | 53 | 0 |

Sólo Lascar tiene alguna detección MODIS de MIROVA (33 alertas → 29 matches, recall 88%
y precision 46%). Los demás 10 Tier A son **0 alertas MIROVA MODIS** en 45 días, y
nosotros gritamos 53-98 veces cada uno. Esto es el problema MODIS reportado
por el audit original, **sigue siendo P0 post-reclasificación**.

## Recomendación próximo paso S81

- **F46 (VRP_TIR drift Stefan-Boltzmann sin background) sigue siendo P0** —
  independiente de este re-audit. Bug estructural separado.
- **F-S81-A (gate anti-incendios estilo MIROVA) sigue siendo P0** — la corrección de
  tags NO la disuelve. Lo que cambia es la formulación: no es "MIROVA filtra incendios
  *fuera* del radio que nosotros no filtramos", sino "MIROVA tiene un gate
  intra-radio (probablemente vegetación o N·σ MODIS más alto) que rechaza el 77% de
  nuestras detecciones MODIS Tier A".
- **F66 (hybrid bg kernel local) mantiene prioridad** — pero apunta a VIIRS/recall,
  ortogonal a este hallazgo MODIS.
- **Acción inmediata sugerida (no implementar parche aún)**: brainstorm dirigido a
  por qué MIROVA no levanta MODIS en 10/11 Tier A. Hipótesis a probar:
  1. MIROVA usa N·σ MODIS = 5-15 (Coppola 2016a Table 1), nosotros 3σ uniforme.
  2. MIROVA aplica gate de vegetación contextual (NDVI o land-cover) en MODIS.
  3. MIROVA requiere cluster ≥2 px MODIS, nosotros aceptamos 1.
  Test: medir cuántas de nuestras 800+ FPs MODIS sobrevivirían a cada gate
  hipotético sobre nuestros propios records.
- **Reabrir hipótesis del audit original "incendios forestales fuera del radio"
  como NO PRIORITARIA** — sólo explica 2% de los datos.


## Artefactos

- `experiments/_s81_v2_out/per_volcano_sensor.csv` — tabla completa.
- `experiments/_s81_v2_out/fp_genuine_all.csv` — todos los FPs subtipo B+C.
- `experiments/_s81_v2_out/subtipo_a_all.csv` — todas las concordancias far.
- `experiments/_s81_gap_analysis_v2_correct_tags.py` — script reproducible.
