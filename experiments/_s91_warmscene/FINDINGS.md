# Warm-scene highs PCC — diagnóstico S91 (pendiente #2 del bloque S91)

**Estado: CERRADO. Mecanismo verificado directo + cruce MIROVA (OCR) verificado
de primera mano. Categoría b (real, magnitud sobre-estimada por agregación de
campo difuso). NO accionar (A55).**

NO es un fix — el escudo anti-drift prohíbe gates nuevos (A55). Rastro
metodológico para el paper.

## 1. Qué son los picos (verificado sobre data/mirova_equivalent/PuyehueCordonCaulle.json)

Los "645 / 338 / 222 MW" del bloque S91 son `mirova_eq_vrp` (primary_cluster
summit, lo que muestra el dashboard), NO el scene-wide `vrp_mw`.

**CORRECCIÓN DE INTEGRIDAD (auditoría S91)**: una primera versión llamó "Record
pico" al de 2026-01-31 (644.8 MW). Eso es el **top de los warm-scene con
t_max≥273K** (lo que pide el bloque #2), NO el pico absoluto de PCC. Los números
de abajo se reproducen con `audit_warmscene.py` (ver §6); NO transcribir a mano
(en S91 hubo 2 transcripciones erróneas — correr el script es la fuente de verdad).

Snapshot `data/mirova_equivalent/PuyehueCordonCaulle.json` (n=1374 records;
189 con t_max≥273K & meq>10; 14 con t_max<273K & meq>10):

**Warm-scene t_max≥273K** (categoría #2, NO los toca el filtro display #259):

| datetime_utc | mirova_eq_vrp | t_max | t_bg | dnti_ctx px | sensor |
|---|---|---|---|---|---|
| 2026-01-31 08:15 | 644.8 MW | 288.0 K | 272.1 K | 107 | MODIS_AQUA |
| 2026-05-05 07:30 | 337.7 MW | 275.0 K | 242.9 K | 362 | MODIS_AQUA |
| 2026-03-09 01:50 | 221.8 MW | 285.3 K | 248.8 K | 256 | MODIS_TERRA |
| 2026-03-01 01:35 | 146.8 MW | 287.6 K | 274.3 K | 71  | MODIS_TERRA |

(El bloque S91 citaba "645/338/222": los TRES se reproducen — 644.8 / 337.7 /
221.8. Mi primera "corrección" puso filas equivocadas; descartada.)

**Picos ABSOLUTOS de PCC tienen t_max<273K** (caen en la categoría cirrus/A23
que maneja el frente display #259, NO son #2):

| datetime_utc | mirova_eq_vrp | t_max | t_bg | dnti_ctx px | sensor |
|---|---|---|---|---|---|
| 2026-04-16 08:30 | 1362.0 MW | 272.8 K | 255.1 K | 107 | MODIS_AQUA |
| 2026-05-04 06:50 | 892.0 MW | 265.9 K | 252.5 K | 153 | MODIS_AQUA |

**Hallazgo de la auditoría**: los warm-scene (≥273K) y los cirrus-cold (<273K)
comparten el mismo mecanismo (path D dNTI-ctx puro: bt/nti/eti=0, campo difuso
71-362 px, MODIS Aqua y Terra sobre el lacolito). La frontera 273K que separa
"atenuado por #259" de "no atenuado" es de DISPLAY, no física — el fenómeno
subyacente (campo difuso del lacolito sumado por MODIS 1km) es el mismo.

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
