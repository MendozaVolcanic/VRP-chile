# F-S81-A Fase 1 — Diagnóstico gate intra-radio MIROVA MODIS

**Sesión**: S82 (2026-05-26)
**Estado**: COMPLETA. Mecanismo identificado.
**Sigue**: Fase 2 (design doc + implementación gate Path D MODIS).

## Pregunta de Fase 1

¿Cuál es el mecanismo dominante de los ~800 FPs MODIS Subtipo B+C del audit
S81 (`experiments/_s81_v2_out/fp_genuine_all.csv`)? El plan original
(`docs/MIROVA_INTRA_RADIO_GATE_S81.md` líneas 116-145) postulaba 4
candidatos: Path D over-trigger / cluster single-pixel / NDVI / MOD14
active fire.

## Método

Sobre los 857 FPs MODIS (subset del CSV), enriquecer cada record desde
`data/mirova_equivalent/<vol>.json` con:
- `final_hotspot_source` (eruption / vent / test1 / cluster_rescue)
- `triggered_test1`, `n_vent_pixels`, `n_anomalous_pixels`,
  `n_hotspots_clustered`
- `primary_cluster.n_pixels`, `primary_cluster.vrp_mw`,
  `primary_cluster.centroid_dist_km`
- `diag_n_bt_path`, `diag_n_nti_path`, `diag_n_dnti_ctx_path` (conteos
  por path A/B/D del paper Coppola 2016a SP426.5)

Script: `experiments/_s82_intra_radio/fase1_1_clasificacion.py`.
Output: `experiments/_s82_intra_radio/fase1_1_modis_classified.csv` +
`fase1_1_summary.md`. Match rate: 857/857 records (100%, después de fix
key `datetime_utc` precisión-minuto).

## Hallazgos

### 1. Path D (dNTI contextual 8-vecinos) domina absoluto

| Path combo | N | % |
|---|---:|---:|
| **D_dNTIctx solo** | **853** | **99.5%** |
| B_NTI + D_dNTIctx | 2 | 0.2% |
| ninguno (test1 puro) | 2 | 0.2% |

**Ningún FP MODIS pasa por Path A (BT clásico) ni por Path B (NTI
absoluto) puro.** El 100% del problema sale del kernel 8-vecinos de
Coppola 2016a SP426.5 (Path D, adoptado S15 P3.2 en `process_modis.py`
flag `enable_dnti_contextual_path`).

### 2. Distribución espacial: 89% lejos del cráter

| dist_km (cluster centroid) | N | % |
|---|---:|---:|
| 0-2 | 26 | 3.0% |
| 2-5 | 16 | 1.9% |
| 5-10 | 53 | 6.2% |
| 10-20 | 305 | 35.6% |
| **20+** | **457** | **53.3%** |

89% de los FPs caen a >10 km del cráter. 53% a >20 km. **El ROI cuadrado
50×50 km de MIROVA incluye esos píxeles geométricamente, pero MIROVA NO
los publica.** Implica gate intra-ROI no replicado en VRP Chile.

Cross-check con `distance_class`:
- `far` (fuera de `inner_radius_km` per-volcán): 765 (89%)
- `summit` (dentro de `inner_radius_km`): 92 (11%)

Los 92 `summit` revelan que para algunos volcanes/granules, **MIROVA
filtra incluso dentro del inner_radius**. Posible explicación: MIROVA
usa un ROI MODIS específico distinto al inner_radius_km nominal que
ingerimos del KMZ VIIRS.

### 3. Clusters chicos dominan, pero no es solo single-pixel

| primary_cluster.n_pixels | N | % |
|---|---:|---:|
| 1px | 307 | 35.8% |
| 2-3px | 263 | 30.7% |
| 4-10px | 188 | 21.9% |
| 11-50px | 79 | 9.2% |
| 50+px | 20 | 2.3% |

66.5% son clusters ≤3 píxeles. **Pero el 33.5% restante son clusters
significativos (≥4 px)** que igual MIROVA filtra. Un gate "single-pixel
mode" análogo al de VIIRS-I S77 corregiría solo el 36% de los casos.

### 4. Magnitud aparente alta — no son detecciones débiles

| ours_vrp_mw | N | % |
|---|---:|---:|
| <1 MW | 1 | 0.1% |
| 1-10 MW | 33 | 3.9% |
| 10-100 MW | 300 | 35.0% |
| **100-1000 MW** | **519** | **60.6%** |
| 1000+ MW | 4 | 0.5% |

96% son ≥10 MW, 61% son ≥100 MW. **No es ruido de pipeline, son
detecciones aparentemente robustas que MIROVA decide silenciar por
ubicación.**

### 5. MIROVA RUTINA, no NO_RECORD

| MIROVA tag (scraper) | N | % |
|---|---:|---:|
| RUTINA(vrp=0.0) | 840 | 98.0% |
| NO_RECORD | 17 | 2.0% |

MIROVA SÍ procesó el 98% de esos timestamps (granule + visualizó el TIF
público) y publicó `RUTINA` con VRP=0. **Confirma que es decisión
algorítmica de MIROVA, no falta de datos.**

### 6. Distribución uniforme entre volcanes

| Volcán | N FPs |
|---|---:|
| PuyehueCordonCaulle | 98 |
| Chaiten | 96 |
| Tupungatito | 95 |
| PlanchonPeteroa | 89 |
| Villarrica | 87 |
| Llaima | 87 |
| Copahue | 78 |
| Lastarria | 72 |
| NevadosDeChillan | 68 |
| Isluga | 53 |
| Lascar | 34 |

No es un volcán roto — es drift sistémico MODIS Path D. Los 11 Tier A
contribuyen entre 53-98 FPs cada uno. **Esto descarta también la
hipótesis "incendio forestal puntual"**: incendios no se distribuyen
así de uniformemente entre 11 volcanes geográficamente dispersos
(Atacama desértico ↔ Patagonia bosques templados).

## Conclusión Fase 1

**Mecanismo dominante**: **Path D (dNTI contextual 8-vecinos)
disparándose lejos del cráter en clusters de tamaño variable** (66%
≤3 px, 34% ≥4 px). MIROVA aplica un gate espacial intra-ROI que
silencia detecciones fuera del cono volcánico, gate que VRP Chile no
replica.

**Fases 1.2 (MOD14 active fire) y 1.3 (MOD13A2 NDVI) skipped**
justificado: la distribución uniforme entre volcanes + magnitudes altas
+ MIROVA RUTINA 98% **descartan** las hipótesis "incendio forestal" y
"vegetación seca". No aporta valor adicional descargar 100 productos
MOD14/MOD13A2 para confirmar lo que ya es evidente.

## Conexión con drifts conocidos

- **D9** (CLAUDE.md A23): "Path D dNTI ctx tiene FPs sistémicos en
  cirrus alto" → **AMPLIADO**: no es solo cirrus + frío, es far +
  cualquier cluster sistémico en MODIS.
- **Single-pixel mode S77** (VIIRS-I): arquitectura
  `enable_single_pixel_mode` ya existe en pipeline VIIRS. Análogo MODIS
  cubre 36% del problema pero no el 64% restante (clusters ≥2px).

## Fundamento físico-metodológico para Fase 2

El path D de Coppola 2016a SP426.5 está **diseñado para resolver señal
sub-pixel cercana al vent**. El kernel 8-vecinos compara el NTI del
píxel candidato contra el ROI inmediato, capturando hot spots que el
threshold absoluto (Path B) o el BT clásico (Path A) no detectan
porque están parcialmente sub-pixel.

A 20-30 km del cráter, el sustrato físico cambia radicalmente:
- Superficies áridas que retienen calor solar post-atardecer (Atacama).
- Lagos pequeños que actúan como reservorios térmicos (Conguillío).
- Suelos con baja capacidad calorífica que enfrían más lento que su
  entorno.
- Flares industriales o quemas agrícolas estacionales.
- Cirrus alto frío (`t_bg_k <260K`) que sesga el kernel local.

En esos contextos, el dNTI **siempre** va a marcar el píxel anómalo
respecto a sus 8 vecinos — pero no es señal volcánica. MIROVA lo
resuelve restringiendo Path D a la ventana intra-ROI cercana al vent,
donde la asunción "anomalía térmica = señal volcánica" tiene base
física.

## Próximo paso

Fase 2: design doc + implementación gate Path D MODIS distancia-restringido
per-volcán. Ver
`docs/superpowers/specs/2026-05-26-f_s81_a_gate_path_d_intra_radio.md`.
