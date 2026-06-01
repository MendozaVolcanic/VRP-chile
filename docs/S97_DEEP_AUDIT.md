# S97 — Auditoría profunda del dashboard vs MIROVA (CONS ∪ OCR)

Script reproducible: `experiments/_s97_audit/deep_audit_dashboard.py`. Salida:
`out_deep_audit.txt`. Cruce a nivel noche-satélite por bucket de sensor, match ±60 min,
sobre la ventana completa ene29–may31 (post-refresh S97). Integridad §0.5: números del
script. Expectativas (CLAUDE.md S15): recall≥60%, precision≥50%, ratio individual 0.5–2.0.

## 1. VIIRS375 (caballo de batalla — decide el recall real)

| | TP | FN | Recall | medCluster/MIR | medNúcleo/MIR |
|---|---|---|---|---|---|
| **GLOBAL** | 662 | 29 | **96%** | 1.07× | 1.51× |
| Lascar | 146 | 17 | 90% | 0.55× | 0.75× |
| Lastarria | 111 | 6 | 95% | 1.23× | 1.13× |
| Isluga | 108 | 1 | 99% | 1.00× | 1.28× |
| PCC | 102 | 1 | 99% | 0.51× | 1.89× |
| Tupungatito | 97 | 0 | 100% | **11.11×** | 2.87× |
| PlanchonPeteroa | 64 | 0 | 100% | **6.40×** | 2.73× |
| Chaitén | 22 | 0 | 100% | **4.30×** | 3.33× |
| Villarrica | 10 | 0 | 100% | **18.97×** | 2.50× |
| Copahue | 1 | 0 | 100% | 0.03× | 2.95× (n=1) |
| Llaima | 1 | 0 | 100% | **45.10×** | 9.83× (n=1) |
| NdC | 0 | 4 | 0% | — | — |

**Lectura geológica:**
- **Recall excelente (96% global)**: captamos casi todo lo que MIROVA publica en VIIRS375.
  Por encima de la expectativa (60%). ✓
- **La magnitud Cluster (vista DEFAULT del dashboard) sigue inflada en volcanes de campo
  frío**: Villarrica 19×, Tupungatito 11×, Planchón 6.4×, Chaitén 4.3× sobre MIROVA. Es el
  fenómeno A54/A19: el VRP de Wooster sobre fondo gélido/glaciar lee el contraste
  nieve↔roca como fondo↔lava. El **Núcleo F5'** lo cura fuerte (caen a 2.5–3.3×) pero es
  toggle opt-in (default = Cluster). Los volcanes de cráter caliente (Lascar 0.55×,
  Isluga 1.00×, Lastarria 1.23×) están bien calibrados sin Núcleo.
- **Llaima/Copahue tienen n=1 TP** → ratios ruidosos (no robustos).
- **NdC recall 0% VIIRS375 (4 FN)**: faint sub-píxel, MODIS-ciego — deuda conocida S90.

## 2. MODIS — recall bajo (deuda conocida, NO regresión S97)

GLOBAL recall **9%** (7 TP, 72 FN). Lascar 9% (7 TP, **69 FN**). Es la **deuda Salar S88/S94
F2**: MODIS 1km off-nadir mete píxeles del Salar de Atacama (sec³, A36) que desplazan el
cráter, y es casi ciego al sub-píxel. El refresh S97 **no tocó la detección MODIS** (solo
magnitud/anomaly_pixels vía #297, aditivo). VIIRS375 carga la detección. Fix MODIS = F2
pendiente (bt_path OFF + reproc), fuera de scope S97.

## 3. VIIRS750 — recall 87% (consistente S94)

GLOBAL recall **87%** (147 TP, 22 FN). Lascar 0.85× (bien), Tupungatito 19.23× e Isluga
2.28× (campo frío, mismo mecanismo que VIIRS375 Cluster).

## 4. Acuerdo de distancia (TP con ambas distancias)

| Sensor | n | mediana Δ | ours | MIROVA |
|---|---|---|---|---|
| VIIRS375 | 658 | 0.71 km | 1.22 km | 2.02 km |
| VIIRS750 | 145 | 0.75 km | 0.91 km | 1.68 km |
| MODIS | 7 | 0.27 km | 0.92 km | 1.41 km |

Acuerdo sub-km. Nuestro centroide queda algo MÁS cerca del vent que la distancia que
reporta MIROVA (1.22 vs 2.02 km) — consistente con el offset de ancla A3/Eje3 (MIROVA mide
desde coord GVP nominal). No es error.

## 5. Titulares del dashboard hoy (última detección summit ≤48h)

Todos plausibles, del día (2026-06-01), niveles Muy Bajo/Bajo, VIIRS (salvo NdC=MODIS):
PCC 0.79 MuyBajo · Villarrica 1.16 Bajo · Lascar 1.39 Bajo · Copahue 2.47 Bajo ·
NdC 5.00 Bajo (MODIS) · Llaima 4.08 Bajo · Chaitén 1.18 Bajo · PP 0.25 MuyBajo ·
Lastarria 0.12 MuyBajo · Isluga 0.28 MuyBajo · Tupungatito 0.80 MuyBajo.
(Copahue 2.47 coincide con la tarjeta que mostró Nicolás.)

## 6. Precision vs MIROVA — baja POR DISEÑO (marco A54)

VIIRS375 precision global **15%** (662 TP / 3639 "FP"). NO es error: detectamos más pasadas
que las que MIROVA **publica** (recall-prioritized). Per A54, ~95% de esos "FP" son features
volcánicas reales no publicadas en CONS (lava lake persistente Villarrica 455, lacolito PCC
408, complejo PP 344, Tupungatito 340). **A vigilar**: Copahue (422 FP, 1 TP) y Llaima (409
FP, 1 TP) son volcanes de baja actividad — ese volumen de detecciones merece una
categorización A54 dedicada (¿señal real débil o artefacto cirrus/campo frío?). Candidato a
sub-auditoría.

## Veredicto

- **Detección sana**: recall VIIRS375 96%, VIIRS750 87%. El refresh S97 no rompió nada.
- **Concern real**: la **vista Cluster por defecto sobre-estima** los volcanes de campo
  frío (Villarrica/Tupungatito/PP/Chaitén). El Núcleo F5' lo corrige pero es opt-in.
  **Decisión pendiente Nicolás**: ¿hacer Núcleo el default? (detección intacta, ya validado
  0 regresiones S96).
- **Deuda conocida**: MODIS recall 9% (Salar, F2 pendiente). VIIRS375 carga la detección.
- **Sub-auditoría sugerida**: FP de Copahue/Llaima (baja actividad, alto volumen).
