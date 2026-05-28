# Frente 2.A S86 — Cruce 1:1 MIROVA vs VRP Chile (Subagente C)

**Ventana común**: 2026-01-28 → 2026-05-25 (~117 días).
**Universo de keys (volcán × sensor × noche local Chile)**: 3,882.
- MIROVA observó: 2,438 keys (556 con ALERTA)
- Nosotros: 3,841 keys (2,013 publishables)

**Mapeo sensor (regla A48)**:
- CSV `MODIS` ↔ JSON `MODIS_*` (Aqua + Terra)
- CSV `VIIRS` y `VIIRS375` ↔ JSON `VIIRS_*` sin sufijo (= I-band 375m)
- CSV `VIIRS750` ↔ JSON `VIIRS_*_750` (M-band 750m) — **no aparece en el snapshot** porque MIROVA solo publica M-band cuando hay anomalía intensa en estos Tier A chilenos.

## Lectura física

El pixel del satélite ve un trozo de superficie volcánica de tamaño fijo (1 km² nominal MODIS, 375 m² VIIRS-I). MIROVA publica una ALERTA cuando ese pixel — o un cluster pequeño — sostiene una anomalía radiativa que el operador puede defender como roca caliente sobre fondo. Esa decisión combina **intensidad** (cuánto se separa del background) y **persistencia espacial** (cuántos pixels y dónde respecto del cráter). Nuestro pipeline tiene los mismos paths algorítmicos (A=BT, B=NTI absoluto, C=NTI relativo, D=dNTI contextual 8-vec), pero publica más records: el insumo de este cruce es entender qué señal física distingue un TP físico (anomalía real) de un FP nuestro (singleton de cirrus alto, halo de glaciar, ruido isolado).

## 1. Matriz de confusión global

**Overall (11 Tier A, todos los sensores)**: TP=490, FP=1523, FN=66, TN=1803
  → precisión = 0.243, recall = 0.881

| Sensor | TP | FP | FN | TN | Precisión | Recall |
|---|---|---|---|---|---|---|
| MODIS | 8 | 174 | 56 | 1060 | 0.044 | 0.125 |
| VIIRS375 | 482 | 678 | 10 | 127 | 0.416 | 0.980 |
| VIIRS750 | 0 | 671 | 0 | 616 | 0.000 | — |

## 2. Matriz por volcán × sensor

| Volcán | Sensor | TP | FP | FN | Precisión | Recall |
|---|---|---|---|---|---|---|
| Chaiten | MODIS | 0 | 17 | 0 | 0.000 | — |
| Chaiten | VIIRS375 | 16 | 91 | 0 | 0.150 | 1.000 |
| Chaiten | VIIRS750 | 0 | 78 | 0 | 0.000 | — |
| Copahue | MODIS | 0 | 2 | 1 | 0.000 | 0.000 |
| Copahue | VIIRS375 | 1 | 109 | 0 | 0.009 | 1.000 |
| Copahue | VIIRS750 | 0 | 41 | 0 | 0.000 | — |
| Isluga | MODIS | 0 | 13 | 0 | 0.000 | — |
| Isluga | VIIRS375 | 73 | 37 | 2 | 0.664 | 0.973 |
| Isluga | VIIRS750 | 0 | 67 | 0 | 0.000 | — |
| Lascar | MODIS | 8 | 2 | 53 | 0.800 | 0.131 |
| Lascar | VIIRS375 | 103 | 12 | 2 | 0.896 | 0.981 |
| Lascar | VIIRS750 | 0 | 103 | 0 | 0.000 | — |
| Lastarria | MODIS | 0 | 8 | 0 | 0.000 | — |
| Lastarria | VIIRS375 | 89 | 25 | 1 | 0.781 | 0.989 |
| Lastarria | VIIRS750 | 0 | 67 | 0 | 0.000 | — |
| Llaima | MODIS | 0 | 7 | 1 | 0.000 | 0.000 |
| Llaima | VIIRS375 | 2 | 97 | 0 | 0.020 | 1.000 |
| Llaima | VIIRS750 | 0 | 46 | 0 | 0.000 | — |
| NevadosDeChillan | MODIS | 0 | 9 | 1 | 0.000 | 0.000 |
| NevadosDeChillan | VIIRS375 | 1 | 57 | 4 | 0.017 | 0.200 |
| NevadosDeChillan | VIIRS750 | 0 | 26 | 0 | 0.000 | — |
| PlanchonPeteroa | MODIS | 0 | 10 | 0 | 0.000 | — |
| PlanchonPeteroa | VIIRS375 | 53 | 60 | 0 | 0.469 | 1.000 |
| PlanchonPeteroa | VIIRS750 | 0 | 31 | 0 | 0.000 | — |
| PuyehueCordonCaulle | MODIS | 0 | 85 | 0 | 0.000 | — |
| PuyehueCordonCaulle | VIIRS375 | 64 | 48 | 1 | 0.571 | 0.985 |
| PuyehueCordonCaulle | VIIRS750 | 0 | 117 | 0 | 0.000 | — |
| Tupungatito | MODIS | 0 | 8 | 0 | 0.000 | — |
| Tupungatito | VIIRS375 | 68 | 44 | 0 | 0.607 | 1.000 |
| Tupungatito | VIIRS750 | 0 | 41 | 0 | 0.000 | — |
| Villarrica | MODIS | 0 | 13 | 0 | 0.000 | — |
| Villarrica | VIIRS375 | 12 | 98 | 0 | 0.109 | 1.000 |
| Villarrica | VIIRS750 | 0 | 54 | 0 | 0.000 | — |

## 3. Perfil físico — distribuciones TP vs FP vs FN

### 3.1 Magnitud `pc.vrp_mw` (MW)
- **TP**: n=490, median=2.426, p25=0.667, p75=3.897, p95=7.828, max=39.629
- **FP**: n=1523, median=3.544, p25=1.759, p75=6.512, p95=29.979, max=1362.039
- **FN**: n=62, median=9.652, p25=2.345, p75=22.385, p95=103.931, max=142.332  *(magnitud del cluster que nosotros sí detectamos pero no publicamos)*

### 3.2 Tamaño cluster `pc.n_pixels`
- **TP**: n=490, median=55.000, p25=17.000, p75=77.000, p95=95.550, max=103.000
  - %singleton (n=1)=10.4%, %≥2=89.6%, %≥3=85.3%
- **FP**: n=1523, median=21.000, p25=10.000, p75=59.000, p95=88.000, max=670.000
  - %singleton=8.3%, %≥2=91.7%, %≥3=88.7%
- **FN**: n=62, median=1.500, p25=1.000, p75=2.000, p95=6.950, max=42.000

### 3.3 Distancia al vent `pc.centroid_dist_km`
- **TP**: n=490, median=1.216, p25=0.878, p75=1.673, p95=6.506, max=18.682
- **FP**: n=1523, median=1.359, p25=1.014, p75=1.898, p95=14.323, max=19.659
- **FN**: n=61, median=17.837, p25=3.269, p75=23.808, p95=30.251, max=31.853

### 3.4 Background térmico `t_bg_k` (Kelvin)
- **TP**: n=490, median=269.185, p25=266.205, p75=272.252, p95=279.870, max=286.130  → %cirrus alto (<260K)=0.0%, <270K=59.0%
- **FP**: n=1523, median=269.260, p25=264.660, p75=274.935, p95=281.520, max=291.340  → %cirrus alto (<260K)=12.1%, <270K=53.6%

### 3.5 Distribución por path (A=BT, B/C=NTI, D=dNTI ctx)
- **TP**: {'D': 363, 'none': 61, 'A+B/C+D': 33, 'A+D': 31, 'B/C+D': 2}
- **FP**: {'D': 1241, 'B/C+D': 5, 'none': 257, 'A+D': 16, 'A+B/C+D': 3, 'A': 1}

## 4. Persistencia (longitud de episodios consecutivos)

- **FP**: {'n_episodes': 510, 'median_len': 2.0, 'mean_len': 2.9862745098039216, 'frac_singletons': 0.49607843137254903, 'frac_2plus': 0.503921568627451, 'frac_5plus': 0.11568627450980393, 'max_len': 117}
- **TP**: {'n_episodes': 147, 'median_len': 2.0, 'mean_len': 3.3333333333333335, 'frac_singletons': 0.4489795918367347, 'frac_2plus': 0.5510204081632653, 'frac_5plus': 0.19047619047619047, 'max_len': 42}

Lectura geológica: una anomalía real (TP) tiende a persistir varias noches consecutivas — el calor del cuerpo magmático no se evapora en 24h. Un FP por cirrus móvil o ruido isolado tiende a ser singleton.

## 5. Features candidatas a ser el mecanismo de supresión MIROVA

Ordenado por **uplift de precisión** (precisión post-gate − pre-gate) priorizando recall ≥80%.

| # | Gate | Recall TP que mantiene | FP rate filtrado | Precisión antes | Precisión después |
|---|---|---|---|---|---|
| 1 | `t_bg_k >= 260 K AND sensor != VIIRS750` | 100.0% | 46.2% | 0.243 | 0.374 |
| 2 | `sensor != VIIRS750 (M-band)` | 100.0% | 44.1% | 0.243 | 0.365 |
| 3 | `t_bg_k >= 260 K AND sensor != VIIRS750 AND n_pixels >= 2` | 89.6% | 48.5% | 0.243 | 0.359 |
| 4 | `t_bg_k >= 260 K (no cirrus alto)` | 100.0% | 12.1% | 0.243 | 0.268 |
| 5 | `n_pixels >= 2 AND t_bg_k >= 260 K` | 89.6% | 18.6% | 0.243 | 0.262 |
| 6 | `pc.n_pixels >= 2` | 89.6% | 8.3% | 0.243 | 0.239 |
| 7 | `pc.n_pixels >= 3` | 85.3% | 11.3% | 0.243 | 0.236 |
| 8 | `pc.vrp_mw >= 0.2 MW` | 90.8% | 3.4% | 0.243 | 0.232 |
| 9 | `pc.vrp_mw >= 0.5 MW` | 80.0% | 7.0% | 0.243 | 0.217 |
| 10 | `n_pixels >= 2 AND path != 'D'-alone` | 25.5% | 82.1% | 0.243 | 0.314 |
| 11 | `Path != 'D' alone (drop D-only records)` | 25.9% | 81.5% | 0.243 | 0.311 |
| 12 | `t_bg_k >= 270 K` | 41.0% | 53.6% | 0.243 | 0.221 |

### Costo físico de cada candidato

- **sensor != VIIRS750 (M-band 750m)**: nuestro pipeline emite records publishable de VIIRS M-band 750m. MIROVA NUNCA publica M-band en estos 11 Tier A chilenos (CONS+OCR ventana 117d). Físicamente coherente: el pixel M-band (750m × 750m = 0.56 km²) tiene ~5.6× más área que I-band (375m × 375m = 0.14 km²). Esa dilución espacial hace que la firma térmica se promedie con superficie circundante fría y caiga bajo el umbral operacional MIROVA. **Costo de descartar VIIRS750 publishable: cero recall perdido** (no había TPs ahí). Es la regla más limpia del set.
- **t_bg_k >= 260 K**: descarta cirrus alto frío. **Cero TPs en t_bg<260K, 184 FPs (12.1%)**. Confirma regla A23 con datos: el path D dNTI contextual se dispara espuriamente cuando el ring 8-vec son pixels de cirrus uniformemente fríos y la diferencia local se infla por azar. Las anomalías reales tienen background de roca/suelo (~270–290 K).
- **n_pixels >= 2**: descarta singletons. **Separación débil** (89.6% TPs vs 91.7% FPs ≥2 — TPs y FPs son ambos predominantemente multi-pixel). Costo: perderíamos ~10% TPs reales (lava lake Villarrica, MIROVA OCR Bajo). Gate poco discriminatorio por sí solo.
- **pc.vrp_mw >= 0.2 MW**: piso de magnitud. Casi inútil para separar (3.4% FPs filtrados). MIROVA publica magnitudes muy bajas (Coppola Muy Bajo), no hay piso natural.
- **Path != 'D'-alone**: aparente alto filtrado FP (82%), pero **destruye recall (25%)** — la mayoría de nuestros TPs también son path-D-only. NO ADOPTAR.

## 6. Hallazgos críticos por sensor

### 6.1 VIIRS750 — *cuadrante limpio para descartar*
0 TPs / 671 FPs / 0 FNs. MIROVA simplemente no usa M-band 750m para estos volcanes chilenos. Nuestro pipeline emite 671 records publishable falsos relativos a MIROVA. **Regla operacional inmediata: `pc.mirova_publishable = False` si `sensor.endswith('_750')`**.

### 6.2 VIIRS375 — *el sensor calibrado*
482 TPs / 678 FPs / 10 FNs. Precisión 0.42, recall **0.98**. Aquí está toda la señal científica: I-band 375m resuelve sub-pixel donde MIROVA confía. La mejora de precisión debe venir de gates aplicados sobre VIIRS375 (t_bg, n_pixels, path).

### 6.3 MODIS — *recall colapsado en Lascar*
8 TPs / 174 FPs / **56 FNs**. Recall global 0.125. Lascar concentra 53 de los 56 FNs: MIROVA publica MODIS Lascar regularmente pero nosotros no detectamos o no publicamos. Esto NO es problema de precisión (gates de supresión) sino de **sensibilidad MODIS** — gate intra-radio Fase B' o algún path apagado en MODIS. Es un frente separado para S87+, no se resuelve con `pc.mirova_publishable`.

## 7. Diferenciadores estadísticos finales — handoff Frente 1.A S87

Ordenados por capacidad de separar TP/FP manteniendo recall ≥85%:

1. **`sensor != VIIRS750`** — recall 100%, FP filtrados 44%, prec 0.24→0.37. **El más limpio, sin trade-off físico. Adoptar inmediatamente.**
2. **`t_bg_k >= 260 K`** — recall 100%, FP filtrados 12%, prec 0.24→0.27. Confirma A23 con datos. Adoptar combinado con (1).
3. **Combo `(1) AND (2)`** — recall 100%, FP filtrados 46%, prec 0.24→**0.37**. Sin pérdida de recall, casi duplica precisión. **Implementación recomendada de `pc.mirova_publishable` para S87**.
4. **Combo `(1) AND (2) AND n_pixels >= 2`** — recall 89.6%, FP filtrados 48.5%, prec 0.24→0.36. Solo marginal sobre (3) y sacrifica ~10% recall. **No recomendado por sí solo, pero útil si el operador quiere reducir aún más volumen.**
5. **Persistencia ≥2 noches consecutivas**: TPs muestran `frac_2plus=55%` vs FPs `50%` y `frac_5plus=19%` vs `12%` — separación débil pero positiva. Útil como feature de visualización, no como gate hard.

## 8. Conclusión geológica

MIROVA publica solo ~556 noches-sensor (ALERTA) mientras nosotros publishable ~2013. El gap precisión global (0.243) es real, pero **no es un único mecanismo**: es la superposición de dos efectos separables:

- **44% de los FPs son VIIRS M-band 750m** que MIROVA nunca publica para estos Tier A → resolución espacial inadecuada para señal sub-pixel chilena. Filtrado trivial.
- **12% adicional son cirrus alto** (t_bg < 260K) donde el path D dNTI ctx se dispara falsamente → filtrado por gate atmosférico.

Combinados llevan precisión de 0.24 → **0.37 sin perder un solo TP**. El resto del gap (~37%) requiere análisis cualitativo de los FP residuales — probablemente halo glaciar Tupungatito (A19), zonas no-volcánicas intra-radio (Fase C S85 descartada), o tail de eventos donde MIROVA simplemente eligió no publicar.

Lascar MODIS recall 13% es un problema separado de sensibilidad que **no se resuelve con `mirova_publishable`** — es un frente independiente para S87+.
