# S101 — Rendimiento por sensor + caracterización MODIS (datos para el paper)

**Fecha**: 2026-06-05 · **Fuente de números (S91)**:
`experiments/_s99_audit/modis_diffuse/{recall_by_sensor,characterize_target}.py`
(ningún número a mano; cada cifra reproducible desde los JSON `*_result.json`).
Cruce contra `latest_consolidado.csv` (MIROVA NRT, ALERTA_TERMICA, ene–jun 2026).

## 1. Rendimiento por sensor vs MIROVA (11 Tier A, días-volcán)

| Sensor | MIROVA det | nuestras det | TP | **Recall** | **Precisión cruda** |
|---|--:|--:|--:|--:|--:|
| **VIIRS375** (I-band, 375 m) | 524 | 1281 | 475 | **90.6 %** | 37.1 % |
| VIIRS750 (M-band, 750 m) | 154 | 860 | 122 | 79.2 % | 14.2 % |
| **MODIS** (1 km) | 67 | 1391 | 65 | 97.0 % | **4.7 %** |

**Lectura para el paper:**
- **VIIRS375 es el sensor operativo** ("caballo"): recall 90.6 %, cubre la mayor parte
  del ground truth MIROVA (524 de 745 días-sensor). Coppola 2024 (Sabancaya): VIIRS375
  detecta 2 años antes que MODIS — coherente.
- **MODIS tiene recall alto (97 %) pero precisión 4.7 %**. No es un problema de
  cobertura: cuando MIROVA publica MODIS (67 días, **64 = Láscar**, +3 singletons), lo
  detectamos (65/67). El problema es que generamos **1391 records MODIS (20× los 67 de
  MIROVA)**; el ~95 % es **campo difuso** que MIROVA no publica → falsos positivos.
- **El frente MODIS es de PRECISIÓN, no de recall.** (Reencuadre S101 — corrige la
  narrativa previa de "MODIS bajo recall".)

## 2. Qué detecta MIROVA desde MODIS (target de fidelidad)

`characterize_target.py` (consolidado + OCR, 5 meses):

| Volcán | nº alertas MODIS | VRP (min/med/max) MW | Dist (med/max) km |
|---|--:|---|---|
| **Láscar** | 78 (+30 OCR) | 0.2 / 1.3 / **3.9** | 1.4 / 2.2 |
| Villarrica / Chaitén / NdC / Copahue / Llaima | 1 c/u | 0.7–2.0 | 1.4–3.6 |

MIROVA-MODIS es SIEMPRE ≤4 MW (OCR ≤15), al cráter (≤3.6 km), clase Muy Bajo/Bajo.
**PCC y Tupungatito: 0 MODIS en 5 meses** (nuestro pipeline les pone 342/133 MW).

**Físico (paper):** MODIS 1 km no resuelve los focos sub-píxel de los volcanes andinos
en reposo (lava lake, domo, lacolito). Solo Láscar (cráter caliente grande) supera el
piso. El TIF de MIROVA confirma que en MODIS no hay foco al cráter ni en Láscar
(radiancia en el borde del recuadro). La señal real vive en VIIRS375.

## 3. Distinción crítica para beyond-MIROVA (anotación)

La baja precisión cruda NO es toda "ruido" — hay que separar dos categorías (S86):

- **cat-b — beyond-MIROVA real** (features volcánicas no publicadas por MIROVA): pesa
  en VIIRS375 (precisión 37 %). Ej.: lacolito Cordón Caulle, Lazufre (Lastarria),
  Pichi-Llaima, complejo multi-cráter PP, lava lake Villarrica (A54). **Esto es valor
  agregado de VRP Chile**, no error.
- **cat-d — artefacto**: domina la baja precisión de MODIS (4.7 %). El campo difuso
  MODIS (contraste nube/nieve gélida leído por path D + inflado por sec³ off-nadir) es
  artefacto, **NO una capacidad beyond-MIROVA**. No confundir en el paper: generar más
  records MODIS que MIROVA no es "detectar más", es ruido.

**Regla para el paper/beyond-MIROVA**: el valor agregado de VRP Chile se mide en
VIIRS375 (cat-b, al cráter/flanco, físicamente real), NO en el volumen de records MODIS.
El frente MODIS (S101) es limpieza de cat-d, no pérdida de cat-b.

### 3.1 Candidatos beyond-MIROVA VIIRS375 (cruce limpio)

`beyond_mirova_viirs375.py`: detecciones nuestras VIIRS375 **al cráter** (summit) en
días donde MIROVA **procesó pero NO alertó** (RUTINA) — descarta la falta de cobertura,
deja FP nominales sólidos. **783 días-volcán** de señal térmica débil al cráter que
MIROVA no publica:

| Volcán | cand | mag med/max MW | Volcán | cand | mag med/max MW |
|---|--:|--|---|--:|--|
| Copahue | 126 | 1.35 / 5.57 | PlanchónPeteroa | 72 | 0.25 / 5.22 |
| Llaima | 123 | 0.97 / 6.98 | Isluga | 49 | 0.32 / 6.66 |
| Villarrica | 119 | 0.81 / 7.80 | Tupungatito | 41 | 0.21 / 5.00 |
| Chaitén | 102 | 0.45 / 4.17 | Lastarria | 34 | 0.06 / 0.69 |
| PCC | 63 | 0.09 / 3.97 | NdC | 29 | 0.09 / 2.25 |
| Láscar | 25 | 0.13 / 4.30 | **TOTAL** | **783** | (≤8 MW) |

**Lectura (paper)**: la magnitud es siempre baja (mediana <1.4 MW, max ≤8) — consistente
con señal volcánica débil real **bajo el umbral de alerta de MIROVA** (lava lake
Villarrica, fumarolas, domo Chaitén, lacolito PCC). Es el régimen de **mayor
sensibilidad** de VRP Chile. **Son CANDIDATOS, no confirmados**: la composición cat-b
(real) vs cat-d (artefacto débil) se estimó en A86 (~46 % cat-b / loader + 4.6 %
artefacto); validar por volcán con eje espacial es pendiente (sección de aporte del paper).

## 4. Pendiente (S102)
- Palanca **sec³** (A/B run 27012025326): cuantifica cuánto de la precisión 4.7 % MODIS
  es geometría de escaneo vs detección path D. `analyze_sec3_ab.py`.
- Caracterización cat-b VIIRS375 por volcán (cuáles features beyond-MIROVA detectamos),
  para la sección de aporte del paper.
