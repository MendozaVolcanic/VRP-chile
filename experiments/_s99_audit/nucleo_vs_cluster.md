# S99 — Núcleo F5' vs Cluster: ¿cuál se asemeja más a MIROVA? (por sensor)

Ventana: **2026-05-01..2026-05-18** (snapshot MIROVA CONS+OCR versionado, A17).
Records matcheados (nuestro detectado ∩ ALERTA MIROVA, mismo sensor-familia, ±15 min): **216**.

Magnitudes comparadas contra `VRP_MW` de MIROVA:
- **Cluster** = `primary_cluster.vrp_mw` filtrado igual que el display (summit + dentro de inner). Es el `mirovaEqVrp` base del frontend.
- **Núcleo F5'** = `mirovaEqVrpCore`/`f5CoreMagnitude` replicado verbatim de `frontend/index.html` (R_core=0.75 km, BT_ext=295 K). SOLO se aplica a VIIRS375; en MODIS/VIIRS750 el núcleo = cluster por diseño.
- `ratio = VRP_nuestro / VRP_MIROVA`. 1.0 = calibración perfecta. Banda tolerable [0.5, 2.0].

## 1. Resultado POR SENSOR (lo que pidió Nicolás)

| Sensor | n | Cluster mediana | Cluster en banda % | Núcleo mediana | Núcleo en banda % |
|---|---:|---:|---:|---:|---:|
| MODIS | — | — | — | — | — |
| VIIRS375 | 216 | 1.159 | 67.1 | 1.525 | 57.4 |
| VIIRS750 | — | — | — | — | — |
| TOTAL | 216 | 1.159 | 67.1 | 1.525 | 57.4 |

> **Limitación de datos (honesta).** Los 216 matches son **todos VIIRS375**. En esta ventana MIROVA publicó 251 alertas VIIRS375, **solo 12 MODIS** (9 Láscar, ninguna matcheó por timing/familia) y **0 VIIRS750**. MIROVA no usa VIIRS750 como fuente de magnitud (A11/S93); nuestro pipeline sí genera MODIS (431) y VIIRS750 (854) records en la ventana, pero **no hay ground truth MIROVA para compararlos**. Conclusión: el contraste Cluster vs Núcleo solo es medible en VIIRS375. En MODIS/VIIRS750 el Núcleo es idéntico al Cluster por diseño, así que la pregunta es vacua ahí.

## 2. Resultado POR VOLCÁN (todos VIIRS375 en esta ventana)

| Volcán | n | Cluster mediana | Cluster en banda % | Cluster max | Núcleo mediana | Núcleo en banda % | Núcleo max |
|---|---:|---:|---:|---:|---:|---:|---:|
| Lascar | 66 | 0.817 | 86.4 | 3.311 | 1.033 | 83.3 | 3.337 |
| Isluga | 34 | 0.914 | 61.8 | 31.929 | 1.263 | 73.5 | 8.387 |
| Lastarria | 31 | 1.3 | 67.7 | 19.443 | 1.524 | 48.4 | 7.556 |
| Tupungatito | 15 | 18.935 | 20.0 | 83.333 | 2.277 | 20.0 | 24.09 |
| PlanchonPeteroa | 22 | 1.5 | 40.9 | 90.611 | 2.307 | 31.8 | 10.681 |
| PuyehueCordonCaulle | 37 | 1.237 | 73.0 | 58.725 | 2.014 | 45.9 | 18.176 |
| Villarrica | 4 | 1.895 | 75.0 | 21.68 | 2.066 | 50.0 | 2.182 |
| Chaiten | 6 | 1.486 | 66.7 | 3.525 | 2.994 | 0.0 | 12.085 |
| Llaima | 1 | 12.441 | 0.0 | 12.441 | 2.711 | 0.0 | 2.711 |
| NevadosDeChillan | 0 | — | — | — | — | — | — |
| Copahue | 0 | — | — | — | — | — | — |

(NdC y Copahue: 0 matches — MIROVA no publicó alertas que coincidieran con nuestras detecciones en la ventana.)

## 3. Lectura

**Mediana global**: Cluster 1.159× vs Núcleo 1.525×. En MEDIANA el Cluster queda más cerca de 1.0.
**% en banda [0.5,2.0]**: Cluster 67.1% vs Núcleo 57.4%. El Cluster acierta la banda más seguido.

Pero la mediana esconde el problema que motivó F5':
- El **Cluster tiene cola larga catastrófica**: max 90.6× (PP), 58.7× (PCC), 31.9× (Isluga), 83.3× (Tupun). Son los artefactos de campo frío/glaciar (A12/A23).
- El **Núcleo aplana esa cola**: max baja a 24.1× (Tupun), 18.2× (PCC), 10.7× (PP), 8.4× (Isluga). Recorta la sobre-estimación de halo.
- El precio: el Núcleo **empuja los ya-bien-calibrados hacia arriba** (Chaitén 1.49×→2.99×, PCC 1.24×→2.01×, PP 1.50×→2.31×), sacándolos de banda. Por eso baja el % en banda.

**Caso Tupungatito** (el que importa, §2 S99): Cluster mediana **18.9×** (solo 20% en banda) → Núcleo **2.28×**. El Núcleo es claramente superior acá: corta el 19× a ~2.3×. Coincide con la dirección de S95 (Núcleo Tupun 2.52×) — la diferencia (2.28 vs 2.52) es esperable: data reprocesada en S98 con ancla al cráter + ventana distinta.

**Control Láscar** (cráter de roca, sin halo nevado): Cluster 0.82× / Núcleo 1.03×, ambos en banda alta (86% / 83%). El Núcleo lo deja casi perfecto sin romperlo. Confirma que el Núcleo no daña al caso sano.

## 4. Cotejo con docs/F5_CALIBRATION_S95.md

S95 reportó: Cluster mediana 5.64×, Núcleo 1.74×, Tupun Núcleo 2.52×, Villarrica 2.07×, Láscar 0.84×.
S99 da Cluster mediana global 1.159× (no 5.64×). **La diferencia es real y esperada**, no un bug:
1. S95 midió sobre `data/_s94_reproc` (deuda histórica con artefactos viejos sin curar, A18); S99 mide sobre `data/mirova_equivalent` **post-promoción S98** (ancla al cráter, históricos backfilleados). El ancla al cráter ya bajó mucha sobre-estimación antes de aplicar F5'.
2. La ventana y el universo de records difieren.
El veredicto direccional de S95 se mantiene: el Núcleo corta la cola; Láscar ~0.8-1.0×; Tupun Núcleo ~2.3-2.5×.

## 5. Limitaciones reportadas explícitamente
- Replica de `f5CoreMagnitude`: **exacta** (mismo R_core, BT_ext, gate VIIRS375, anclaje al píxel de máxima energía dentro de innerKm del centroide, guard S96 nunca-borra, cap 50000). No hubo ambigüedad que obligara a inventar.
- Sin ground truth MODIS/VIIRS750 utilizable en la ventana → la respuesta 'por sensor' es **solo VIIRS375**. Para MODIS habría que ampliar la ventana a meses con alertas MODIS MIROVA (Láscar mayormente) y re-correr.