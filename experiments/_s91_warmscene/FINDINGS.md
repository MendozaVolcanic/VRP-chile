# Warm-scene highs PCC — diagnóstico S91 (pendiente #2 del bloque S91)

**Estado: CERRADO. Mecanismo verificado directo + cruce MIROVA (OCR) verificado
de primera mano. Categoría b (real, magnitud sobre-estimada por agregación de
campo difuso). NO accionar (A55).**

NO es un fix — el escudo anti-drift prohíbe gates nuevos (A55). Rastro
metodológico para el paper.

## 1. Qué son los picos (verificado sobre data/mirova_equivalent/PuyehueCordonCaulle.json)

Los "645 / 338 / 222 MW" del bloque S91 son `mirova_eq_vrp` (primary_cluster
summit, lo que muestra el dashboard), NO el scene-wide `vrp_mw`.

Record pico (verificado con `pipeline.audit_metrics.mirova_eq_vrp`):

| datetime_utc | mirova_eq_vrp | vrp_mw escena | t_max | t_bg | dnti_ctx px | class | sensor |
|---|---|---|---|---|---|---|---|
| 2026-01-31 08:15 | 644.7 MW | 1609.5 MW | 288 K | 272 K | 107 | summit | MODIS_AQUA |

(los otros dos picos 338/222 MW siguen el mismo patrón — top por mirova_eq_vrp).

## 2. Mecanismo físico (verificado)

- **NO es cirrus frío**: t_max=288 K, t_bg=272 K. El fix display #259 (S90) filtra
  solo t_max<273 K — correctamente NO los toca. El criterio cirrus usa t_max, no
  t_bg (escudo anti-drift).
- **Disparados por path D (dNTI contextual)**: `diag_n_dnti_ctx_path=107`. El
  kernel de 8 vecinos marca 107 píxeles que sobresalen levemente de su entorno
  sobre un campo extendido.
- **Geología**: el lacolito del Cordón Caulle es una intrusión somera de ~707 km²
  (A20/A24) que dejó terreno tibio en un área amplia. Con background no congelado
  (272 K = −1 °C), el path contextual detecta un campo difuso de decenas de
  píxeles, cada uno con ΔT modesto (~16 K).
- **Por qué se infla la magnitud**: el VRP es la SUMA de la radiancia de todos los
  píxeles del cluster. 107 píxeles × anomalía pequeña = magnitud agregada enorme,
  aunque cada píxel sea débil. MIROVA colapsa el mismo campo a un cluster puntual
  chico. Es el patrón A20/A21/A24 (anomalía difusa no focal): divergencia por
  DISEÑO físico del método de suma, no bug.
- **Categoría (marco S86)**: anomalía físicamente REAL (categoría b) con
  SOBRE-estimación de magnitud por agregación de campo difuso. NO es FP solar (es
  pasada nocturna, 08:15 UTC ≈ 05:15 local en enero) ni cirrus.

## 4. Cruce MIROVA — VERIFICADO de primera mano (OCR latest, A11/A17)

El CONS (`latest_consolidado.csv`) no tenía estas fechas PCC; las alertas están en
OCR (`registro_vrp_ocr.csv` de Mirova-v1, descargado vía raw GitHub). Confirma
A11 (universo MIROVA = CONS + OCR). Filas PCC verificadas:

| Fecha (UTC) | Nuestro mirova_eq_vrp | Nuestro sensor | MIROVA VRP | MIROVA sensor |
|---|---|---|---|---|
| 2026-01-31 05:30 | 644.7 MW (08:15 AQUA) | MODIS 1km | **0.13 MW** | VIIRS375 |
| 2026-04-02 06:30 | — | — | 0.26 MW | VIIRS375 |
| 2026-04-04 05:30 | ~cientos MW | MODIS 1km | 0.51 MW | VIIRS375 |
| 2026-04-04 05:54 | ~cientos MW | MODIS 1km | 0.63 MW | VIIRS375 |

(OCR PCC: 66 filas, rango 2026-01-20..2026-05-30, todas ALERTA_TERMICA_OCR @ 0 km.)

**Lectura geológica del contraste**: MIROVA detecta el lacolito con VIIRS 375m
como un foco puntual débil (~0.1–0.6 MW @ 0 km). Nosotros, con MODIS 1km, vemos el
MISMO terreno tibio extendido como un campo difuso de 107 píxeles vía path D
contextual y SUMAMOS su radiancia → cientos de MW. El factor ~5000× NO es error de
calibración: es la diferencia física entre "sumar un campo difuso de píxeles de
1km" y "reportar un foco de 375m". Patrón A20/A21/A24 (anomalía no-focal),
divergencia por DISEÑO del método de suma.

**Categoría (marco S86): b — anomalía REAL (MIROVA la confirma), magnitud
sobre-estimada por agregación.** No es FP (MIROVA detecta), no es cirrus (t_max
288 K), no es FP solar (pasada nocturna 05:30 local). NO accionar: meter gate de
magnitud/nº-píxeles sería A55 y además borraría señal real. Documentado para el
paper como divergencia conocida MODIS-difuso vs VIIRS-focal.

## 5. A36 (off-nadir sec³) — NO verificable desde JSON

Repetido aquí por completitud: los records no persisten scan/zenith angle. El
mecanismo dominante del record top es dNTI-ctx difuso (107 px), no un píxel
off-nadir único. A36 no se puede confirmar ni descartar sin releer geolocation
L1B; no es necesario para la conclusión (el cruce VIIRS-vs-MODIS ya explica el
factor).
