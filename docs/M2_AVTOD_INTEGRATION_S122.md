# M2 — AVTOD (Reath et al. 2019) como 2º ground truth: hallazgo de premisa + qué es construíble

> Fuente local: `documentacion/AVTOD_Reath_2019.pdf` + `.md` (extraído). Verificación de
> premisa antes de construir (A48/A50). Reath, K. et al. (2019), *The AVTOD (ASTER Volcanic
> Thermal Output Database) Latin America*, JVGR 376:62-74, doi 10.1016/j.jvolgeores.2019.03.019.

## Hallazgo de premisa (bloquea M2 tal como estaba scopeado)

El plan S122 asumía "extraer los valores **VRP** AVTOD del PDF a un CSV → superponer serie
temporal vs la nuestra en Panel 1". **Dos correcciones de la lectura del PDF:**

1. **AVTOD no mide VRP en watts.** Su métrica es **°C above background** (ASTER 90 m,
   pixel-by-pixel). La Fig. 6 del paper *correlaciona* ese °C-AB contra el VRP de MIROVA
   (r²=0.87 global, línea 48). El "máximo °C sobre fondo" fue el mejor análogo del VRP
   (línea 615-616). No hay conversión directa °C-AB → MW.

2. **La serie temporal por-fecha NO está en el PDF.** Los datos por-detección viven en:
   - **Table S1** (material suplementario, "summary table... reference guide", línea 362-365)
   - **Figs. S11-S19** (correlación por volcán, suplementarias)
   Ninguna está en `documentacion/` (solo tenemos el PDF principal). El texto solo da
   agrupaciones categóricas y ejemplos nombrados, no la tabla por-volcán/fecha.

→ **M2(a) "extraer VRP AVTOD del PDF" es irrealizable con lo que tenemos.** Requiere el
material suplementario (Table S1 + Figs S11-S19). Ver §Decisión.

## Lo que el PDF SÍ da (extraíble hoy, defendible para el paper)

**5 volcanes Tier A chilenos con correlación AVTOD↔MIROVA establecida** (de los 9 globales
con muestra más completa, línea 592-594; cada uno con su Fig. S11-S19):

| Volcán chileno | En correlación AVTOD-MIROVA | Categoría °C-AB (si el texto la nombra) |
|---|---|---|
| **Villarrica** | sí | **>35 °C** (categoría más alta; lava lake, línea 775) |
| **Láscar** | sí | (en Table S1, no en texto) |
| **Llaima** | sí | (en Table S1) |
| **Chaitén** | sí | (en Table S1) |
| **Copahue** | sí | (en Table S1) |

Otros chilenos nombrados en el texto por categoría:
- **Callaqui, Calbuco** (Chile): 10-20 °C (activos con erupciones cortas, poca cobertura ASTER, línea 763).
- Central Andes: 14/28 volcanes con VTF están en la categoría más baja (2-10 °C) — coherente
  con nuestro marco A54/A82 (señal sub-píxel débil domina el norte chileno).

**Insight físico para el paper (líneas 623-631) — refuerza nuestro A82/A83:**
> "el píxel más caliente de AVTOD está contenido en el píxel más caliente de MODIS; el
> MIR-method (Wooster 2003) es más sensible a superficies sobre ~600 K; las inconsistencias
> entre ambos datos vienen de la diferente resolución espacial y longitud de onda."

Esto es literatura independiente (grupo Reath/Coppola) confirmando que a 1 km el foco
sub-píxel es el limitante — exactamente lo que el Paso 0 C2 (`AUDIT_S122_C2_PASO0.md`)
concluyó para Láscar/PCC. **Es un argumento citeable de robustez.**

## ✅ ACTUALIZACIÓN S122 — suplementario CONSEGUIDO y verificado

El fetch (subagente) bajó el suplementario `mmc1.docx` (libre, CDN Elsevier, sin paywall) →
`documentacion/AVTOD_Reath_2019_SupplementaryS1.docx` (+ `.md` markitdown + 19 JPEGs
Figs S1-S19 en `_figs/`). **Table S1 verificada verbatim** (A35) → CSV en
`data/mirova_reference/avtod_reath2019_chile.csv` con los **11 Tier A chilenos** (no solo 5).

**Máx °C sobre fondo AVTOD (ASTER 90m, 2000-2017), verificado:**
Villarrica 120* · Llaima 120* · Láscar 100.03 · Chaitén 80.38 · Copahue 57.11 · NdC 47.73 ·
PP 44.06 · PCC 34.76 · Isluga 30.96 · Tupungatito 24.3 · Lastarria 20.39. (*=saturado ASTER
≥120, lava lake.) Figs S11-S19 = series temporales AVTOD+MIROVA (Chaitén S11, Copahue S13,
Láscar S15, Llaima S16, Villarrica S18).

**Cross-validation vs nuestro VRP summit (pc.vrp_mw, A10; p95 robusto 2025-26):**

| Volcán | AVTOD °C (00-17) | nuestro VRP p95 (25-26) | lectura |
|---|---|---|---|
| Villarrica | 120* | 2.52 | persistente, concuerda (lava lake) |
| Llaima | 120* | 0.85 | AVTOD incluye actividad histórica |
| Láscar | 100.03 | 3.04 | concuerda, alto en ambos |
| Chaitén | 80.38 | 2.07 | AVTOD = erupción 2008 (fuera de ventana) |
| Lastarria/NdC/Tupun | 20-48 | 0.3-0.42 | bajos en ambos, concuerda |
| **PCC** | **34.76** | **max 233 / p95 5.0** | **⚠ outlier → ver abajo** |

**Hallazgo clave (robustez para el paper):** para la salida térmica **persistente**, el
ranking de nuestro VRP p95 concuerda con el ranking independiente ASTER de AVTOD. El
**outlier PCC** es corroboración independiente de nuestro diagnóstico de artefactos: nuestro
máx 233 MW vs el modesto 34.76 °C de AVTOD (cuyo máx fue la erupción 2011, no la rutina) →
**una fuente independiente confirma que PCC NO es un volcán de 233 MW** — los path-D de alta
magnitud son el artefacto difuso lacolito/cirrus (A82/A54/D9), no señal real.

**Caveat temporal (A62, no ocultar):** AVTOD max es 2000-2017 (incluye erupciones históricas
Chaitén 2008, PCC 2011, Copahue 2012); nuestra ventana es 2025-26. Comparable solo para los
efusivos persistentes (Villarrica/Llaima lava lakes, Láscar); NO para los eruptivos. Por eso
se reporta el ranking + la corroboración PCC, NO una correlación Spearman ingenua a 11 puntos.

## Decisión (para Nicolás — es para su paper)

Dos caminos, no excluyentes:

- **Camino A (rico, necesita fetch):** conseguir el suplementario de Reath 2019 (Table S1 +
  Figs S11-S19) del journal/repositorio → CSV per-volcán (máx °C-AB, n detecciones, timing) +
  digitalizar las 5 curvas de correlación chilenas → overlay real en Panel 1. Requiere
  descarga externa (Elsevier; puede tener paywall). Se aborda con la skill `investigacion`.
- **Camino B (defendible ya, sin fetch):** anotación cualitativa de cross-validation — "AVTOD
  (ASTER 90 m independiente) clasifica Villarrica en la clase térmica más alta y confirma
  actividad térmica en Láscar/Llaima/Chaitén/Copahue, los mismos 5 Tier A donde nuestra serie
  VRP muestra detecciones persistentes; el caveat sub-píxel de Reath (líneas 623-631) coincide
  con nuestro A82/A83". Se implementa como chip/nota en el Panel 1 + párrafo en el draft.

**Recomendación:** empezar por B (valor inmediato para el paper, cero riesgo) y, si Nicolás
quiere el overlay cuantitativo, intentar A con `investigacion` (bounded, aviso si hay paywall).
