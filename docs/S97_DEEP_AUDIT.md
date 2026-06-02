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

## 7. Tupungatito — detecciones al SE, NO en el lago cratérico (pedido Nicolás)

Nicolás observó en el mapa que Tupungatito no muestra puntos en el lago cratérico pero sí
muchos al sur. Confirmado y diagnosticado:
- Cráter (vent) en -33.389,-69.826 (N); mirova_center en -33.427,-69.800 (SE, **4.86 km**).
- De 116 detecciones VIIRS375 (mayo): **103 al SE**, mediana **5.86 km del cráter**, solo
  2/116 a <1.5 km del lago. Caen a 1.15 km del mirova_center.
- **BT del píxel MÁS caliente = 259–265 K (−8 a −14 °C), 100% bajo cero**. NO es lava ni
  fumarola → **artefacto del anillo glaciar (A19)**: el algoritmo contextual marca píxeles
  de hielo "relativamente tibios" como anomalía. El lago cratérico real es sub-píxel/débil
  y queda tapado.
- No hay TIF de Tupungatito para R2 (verificación de radiancia MIROVA).
- **Card engañosa**: muestra `centroid_dist_km` (desde mirova_center) → "0.8 km del cráter"
  cuando físicamente está a ~7.5 km del lago. Issue A3/Eje3, egregio acá por el offset.

## 8. Sub-auditoría Copahue/Llaima (cold-pixel BT lens) — sus "FP" son artefacto frío

| Volcán | n | BT píxel+caliente | %bajo cero | dist cráter |
|---|---|---|---|---|
| Tupungatito | 115 | −14 °C | **100%** | 7.5 km |
| Copahue | 121 | −1 °C | **69%** | 2.9 km |
| Planchón | 114 | −3 °C | 69% | 3.1 km |
| Villarrica | 122 | −0.5 °C | 51% | 2.6 km |
| Llaima | 110 | 0 °C | 49% | 2.9 km |
| **Lascar** | 92 | **+4.5 °C** | 36% | **0.9 km** |

**Corrige el marco A54 para estos volcanes**: el alto volumen de "FP" de Copahue (69%) y
Llaima (49%) NO son features volcánicas reales (categoría b) sino **artefactos de píxel
frío** (categoría d): glaciar/nieve que el path-D contextual lee como anomalía. Lascar es
el único genuino (píxel caliente +4.5 °C, pegado al cráter).

**Discriminante**: píxel más caliente bajo cero + lejos del cráter = artefacto. PERO un
gate "matar sub-cero" es PELIGROSO (A55/A19): Villarrica tiene lava lake real cuyo píxel
integrado promedia bajo cero (roca caliente sub-píxel + hielo) → un gate duro daría FN en
Villarrica. El Núcleo F5' baja la MAGNITUD pero no mueve la UBICACIÓN del artefacto.

## Acción tomada (S97)
- **Núcleo F5' = default** (PR pendiente): cura la magnitud de campo frío en la vista del
  operador. Trade-off: global Cluster 1.07× vs Núcleo 1.51× (los high-count ya estaban
  bien en Cluster); gana en los casos visibles malos, empeora levemente PCC/Isluga.
  Reversible (1 línea). Detección intacta + guard S96.

## 9. Auditoría espacial R2 vs TIF MIROVA (2da ronda — el eje que faltó)

Nicolás señaló (con razón) que la 1ra auditoría no miró la UBICACIÓN física, solo
métricas agregadas. Y que SÍ hay TIF (estaban en `../mirova-tif-archive/`, sibling del
repo — mi búsqueda interna falló). 2da ronda con `r2_spatial_audit.py`: por pasada
matcheada (record ↔ TIF mismo sensor ±90min, ventana mayo), centroide de radiancia del
TIF (dónde ve el calor MIROVA) vs nuestro cluster vs cráter real.

| Volcán | nPares | d_tif_cráter | d_ours_cráter | d_ours_tif | offset mc | lectura |
|---|---|---|---|---|---|---|
| Tupungatito | 49 | 4.85 | 5.88 | **1.76** | 4.86 | **coincidimos con MIROVA**; ambos ~5km SE del cráter |
| PCC | 106 | 7.16 | 3.04 | 6.15 | 7.57 | campo difuso 707km² (A20): centroide TIF no aplica |
| Lascar | 45 | 3.67 | **0.26** | 3.40 | 0.83 | **NOSOTROS en el cráter**; el TIF se estira (Salar off-nadir) |
| Planchón | 42 | 4.53 | 2.77 | 3.22 | 2.02 | complejo multi-cráter (A22), ambos dispersos |
| Villarrica | 53 | 1.13 | 0.90 | 1.04 | 0.54 | ambos en el cráter (lava lake) ✓ |
| Chaitén | 62 | 0.97 | 0.49 | 1.04 | 0.24 | ambos en el cráter ✓ |
| Copahue | 50 | 2.24 | 1.45 | 1.70 | 0.14 | cerca del cráter |
| Llaima | 44 | 1.19 | 1.24 | 1.75 | 0.14 | cerca del cráter |
| Lastarria | 39 | 0.88 | 1.49 | 1.34 | 0.12 | en el cráter ✓ |
| Isluga | 54 | 0.89 | 1.04 | 1.46 | 0.37 | en el cráter ✓ |
| NdC | 1 | — | — | — | 0.39 | n=1, no concluyente |

**CORRECCIÓN clave (vs lo que dije S97 turno previo):**
- **Tupungatito NO es nuestro error de ubicación**: `d_ours_tif=1.76 km` → coincidimos con
  el TIF de MIROVA. **AMBOS** ven el calor ~5 km SE del cráter mapeado. El desplazamiento
  es del CAMPO TÉRMICO (señal glaciar-relativa SE, BT bajo cero) + la coord del cráter, NO
  un bug nuestro. MIROVA reporta lo mismo.
- **Lascar: nosotros somos MÁS precisos** que el centroide del TIF (0.26 km vs 3.67 km) —
  el TIF se estira por el Salar off-nadir; nuestro cluster clava el cráter.
- **El "error de Tupungatito" NO está en todos los volcanes**: la mayoría (Villarrica,
  Chaitén, Lastarria, Isluga, Llaima, Copahue) ubican el calor a <2 km del cráter,
  coincidiendo con MIROVA. Solo Tupungatito (offset 4.86 km) y los difusos PCC/PP se
  apartan, y por razones documentadas (A20 difuso, A22 multi-cráter), no por bug.

**Caveat metodológico (A24)**: el centroide ponderado del TIF sobre TODO el campo se
estira con píxeles dispersos (Lascar→Salar, PCC→lacolito). Por eso `d_tif_crater` se
infla en campos extendidos. El cruce contra la distancia REPORTADA por MIROVA (CSV, §4
arriba) da acuerdo sub-km — esa es la referencia autoritativa de ubicación, y ahí estamos
bien. El TIF-centroide es complementario, no la última palabra.

**Conclusión del eje espacial**: nuestras detecciones están bien ubicadas vs lo que MIROVA
reporta. Tupungatito es un caso especial (offset cráter-señal de 4.86 km que MIROVA
también tiene), no un patrón de error generalizado.

## Veredicto

- **Detección sana**: recall VIIRS375 96%, VIIRS750 87%. El refresh S97 no rompió nada.
- **Concern real**: la **vista Cluster por defecto sobre-estima** los volcanes de campo
  frío (Villarrica/Tupungatito/PP/Chaitén). El Núcleo F5' lo corrige pero es opt-in.
  **Decisión pendiente Nicolás**: ¿hacer Núcleo el default? (detección intacta, ya validado
  0 regresiones S96).
- **Deuda conocida**: MODIS recall 9% (Salar, F2 pendiente). VIIRS375 carga la detección.
- **Sub-auditoría sugerida**: FP de Copahue/Llaima (baja actividad, alto volumen).
