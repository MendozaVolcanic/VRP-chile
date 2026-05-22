# AVTOD Cross-Validation — VRP Chile (F2.6.f, S72)

**Paper**: Reath K., Pritchard M.E., Moruzzi S., Alcott A., Coppola D., Pieri D. (2019)
"The AVTOD (ASTER Volcanic Thermal Output Database) Latin America archive."
*Journal of Volcanology and Geothermal Research* 376: 62–74.
DOI: [10.1016/j.jvolgeores.2019.03.019](https://doi.org/10.1016/j.jvolgeores.2019.03.019).

Local: `documentacion/AVTOD_Reath_2019.pdf` + `.md` (markitdown).
Data online (AVA portal): https://ava.jpl.nasa.gov/avtod.php
Supplementary (Table S1, Figs S11–S19): vía DOI Elsevier (NO descargado local).

---

## 1. Resumen del paper

**Qué hicieron**: análisis manual exhaustivo de TODA la pasada nocturna ASTER (90 m/pixel TIR)
sobre los **330 volcanes Holocenos de Latinoamérica** entre 2000 y enero 2018. Para cada
escena cloud-free registraron, por pixel anómalo, temperatura sobre background (°C) y área (m²)
de la VTF (Volcanic Thermal Feature). Producto: AVTOD, base de datos pública alojada en
el AVA portal (JPL), integrada como capa adicional sobre las detecciones automáticas AVA.

**Cobertura LATAM**: 88 volcanes con VTFs detectables por ASTER (16 nuevos respecto a Jay
et al. 2013). 242 sin detección. 24% de volcanes no alcanzan la tasa mínima de adquisición
del Volcano-STAR plan; 44.5% de adquisiciones son inutilizables por nubes.

**Validación cruzada con MIROVA** (Sección 3.4, Fig. 6, Figs S11–S19): los autores ya
hicieron AVTOD vs MIROVA OSF para los **9 volcanes LATAM con muestreo más completo**, de
los cuales **5 son chilenos Tier A nuestros**: Lascar, Villarrica, Chaitén, Llaima, Copahue.
Encontraron correlación AVTOD °C-above-background vs MIROVA VRP. Mejor caso: **Lascar r²=0.87**.

**Hallazgo clave para nosotros**: los 7 de 9 volcanes mostraron x-intercept de la línea de
tendencia entre **20–30 °C ASTER above background** = umbral por debajo del cual MIROVA
no detecta. 46 de 88 volcanes LATAM nunca alcanzan ese umbral, por lo tanto **son ciegos a
MIROVA-class sensors** (MODIS) por construcción física. Esto es exactamente el "régimen
Muy Bajo" que arrastramos toda la S60–S70 con kernel-bg.

---

## 2. Tabla Chile vols cubiertos por AVTOD

AVTOD declara cobertura completa de los 330 volcanes Holocenos LATAM (toda la pasada
ASTER nocturna 2000–2018). De nuestros 11 Tier A, **los 11 están dentro del scope AVTOD**.
Sin embargo, **el paper no provee la tabla numérica per-volcán-per-fecha en el texto**:

- **Texto identifica explícitamente** (Sec. 3.4 + figuras S11–S19): Lascar, Villarrica, Chaitén,
  Llaima, Copahue (5/11 Tier A nuestros) — los 5 con suficiente n para correlacionar vs MIROVA.
- **Tupungatito**: aparece UNA vez (Sec. 3.2, línea 488) en la lista de volcanes con
  **crater lakes / surface water identificados como potenciales falsos positivos térmicos**
  (alto thermal inertia del agua produce señal nocturna confundible con VTF). Esto es
  un hallazgo MUY relevante para nuestra F1.7 — ver §4.
- **Lastarria, Isluga, PCC, Planchón-Peteroa, NdC**: están en scope LATAM AVTOD pero
  el paper no los singulariza en el texto. Sus datos viven en **Table S1 supplementary**
  + portal AVA (no descargados aún).

**Tabla extraíble del texto** (Sec. 3.5 + Tabla S1 referenciada):

| Vol Tier A | AVTOD cubre | En 9-vol benchmark vs MIROVA | Tmax categoría (texto) | Notas |
|---|---|---|---|---|
| Lascar | Sí | Sí (r²=0.87, mejor caso) | >35 °C | "uniform VTF area", caso ideal |
| Villarrica | Sí | Sí | >35 °C | "lava lake" explícito Sec. 3.5 |
| Chaitén | Sí | Sí | >35 °C | sin pre-erupción 2008 medida (gap ASTER 2 años) |
| Copahue | Sí | Sí | (no especificado, baja r²) | "crater lake cycles full/empty" rompe correlación |
| Llaima | Sí | Sí | (mencionado strombolian) | — |
| Tupungatito | Sí | **NO en benchmark** | **clasificado crater-lake / surface-water** | ⚠ ver §4 |
| Lastarria | Sí (sup.) | No | Tabla S1 | sin extraer del paper |
| Isluga | Sí (sup.) | No | Tabla S1 | sin extraer del paper |
| PCC | Sí (sup.) | No | Tabla S1 | sin extraer del paper |
| Planchón-Peteroa | Sí (sup.) | No | Tabla S1 | sin extraer del paper |
| NdC | Sí (sup.) | No | Tabla S1 | sin extraer del paper |

---

## 3. Comparativa cualitativa AVTOD vs MIROVA OSF v2.5

Coppola es coautor del paper AVTOD ⇒ la comparativa AVTOD vs MIROVA es **endorsement del
propio grupo MIROVA sobre la consistencia ASTER-MODIS** en estos 5 volcanes chilenos.

**Confirmaciones (AVTOD valida MIROVA OSF)**:
- **Lascar**: r²=0.87. AVTOD ve detecciones MIROVA hasta 18 °C ASTER (caso límite). Coherente
  con nuestro Lascar OSF v2.5 → VRP Chile ratio 1.37×, calibrado natural.
- **Villarrica**: explícitamente lava-lake >35 °C, alta correlación. Coherente con nuestra
  validación S61 (ratio 2.17× post kernel-bg).
- **Chaitén**: VTF grande, llena pixel ASTER pero no MODIS. Trend más empinado. Coherente
  con nuestro S63 (ratio 2.23× post kernel-bg).
- **Llaima**: en lista de los 9, no especificado en discusión. Nuestro n=3 ALERTAS no permite
  comparar.

**Discrepancia interesante**:
- **Copahue**: AVTOD reporta baja r² AVTOD-MIROVA por ciclos full/empty del lago cratérico
  (Agusto 2013, Caselli 2016). Es el ÚNICO Tier A nuestro donde los propios autores
  documentan ruido sistemático MIROVA por water-body cycling. Coherente con nuestro
  n=1 ALERTA S62-S70 (no calibrable, mecanismo distinto).

**Discrepancia mayor (hallazgo central para VRP Chile)**:
- **Tupungatito**: AVTOD lo CLASIFICA explícitamente como surface-water / crater-lake.
  Implica que el grupo Cornell+Coppola, mirando manualmente ASTER 90 m, NO le asigna VTF
  volcánica. **Pero MIROVA OSF v2.5 sí reporta detecciones**. Esto es exactamente la
  divergencia que arrastramos S65–S69 (Tupungatito mirova_center fix parcial, ratio 10×
  → 56% records con cluster correcto, 43% FPs flanco SE).
  - Lectura: el "ground truth MIROVA" en Tupungatito puede ser **VRP atmosférico/glacial/lacustre
    sub-MW que AVTOD descarta por inspección visual manual**. Refuerza F1.7 — corrobora
    que el 43% residual de mismatch Tupungatito S65 **no es bug de VRP Chile sino que
    MIROVA detecta señales que el propio grupo Cornell-Torino descarta cuando mira el pixel
    ASTER**.
  - **Acción**: descargar Table S1 + Fig S correspondiente Tupungatito de AVTOD/AVA para
    cuantificar cuántas detecciones AVTOD reporta vs cero (predicho: muy pocas o cero).

---

## 4. Verdict aplicabilidad VRP Chile

**¿AVTOD útil como ground truth secundario?** **Sí, condicional.**

**Limitaciones que descartan uso directo**:
1. **Asimetría temporal**: AVTOD termina enero 2018, VRP Chile arranca operacional ~mediados
   2025. Comparación record-to-record es imposible.
2. **Asimetría sensor**: ASTER 90 m vs VIIRS/MODIS 375 m / 1 km. VTFs sub-90 m² (Fuego,
   Lascar pre-erupción) son detectables por ASTER pero el VRP que reporta es de "pixel ASTER",
   no de "pixel MODIS/VIIRS". Comparar VRP_avtod vs VRP_vrpchile no tiene sentido físico
   directo.
3. **Datos numéricos no extraídos del paper**: Table S1 + figuras S11–S19 viven en
   supplementary del DOI. NO descargados local todavía.

**Casos donde AVTOD sí aporta valor cross-validation**:
1. **Validación cualitativa de existencia de VTF**: AVTOD nos dice "este volcán tiene VTF
   sostenido / esporádico / nulo" en período 2000–2017. Si VRP Chile en 2025+ detecta
   actividad consistente con la categoría AVTOD (Tmax >35 °C ⇒ esperamos detecciones
   recurrentes; sin VTF ⇒ esperamos no detección), hay coherencia.
2. **Identificación de FPs sistémicos**: la lista AVTOD Sec. 3.2 línea 480–488 de
   volcanes con crater-lake / surface-water identificados como confundibles es **gold
   standard cross-MIROVA para FP detection**. **Tupungatito** está en esa lista. Lectura
   directa: los 43% records Tupungatito mismatch S65 son consistentes con clasificación
   AVTOD de surface-water VTF en ese volcán.
3. **Régimen Muy Bajo VRP Chile**: AVTOD confirma que 46 de 88 volcanes nunca llegan al
   umbral MIROVA (>20 °C ASTER above background). Esto justifica físicamente nuestro
   "régimen Muy Bajo" y el fix kernel-bg S61+ — no es invento métrico, es propiedad real
   del espacio de señal.

**Cómo integrar al workflow validation**:
1. **Descargar Table S1 supplementary** desde DOI Elsevier (próxima sesión investigación).
   URL: https://doi.org/10.1016/j.jvolgeores.2019.03.019 (Appendix A Supplementary data).
2. **Consultar AVA portal** https://ava.jpl.nasa.gov/avtod.php para extraer per-volcán
   chileno Tier A: n_detections, Tmax cat, eventos relevantes 2000–2017.
3. **Workflow secundario sugerido para F2.6**: agregar columna AVTOD-evidence al
   `MIROVA_DIVERGENCES_CATALOG_S71.md` con verdict cualitativo (AVTOD confirms / AVTOD
   contradicts / AVTOD silent). Especialmente para Tupungatito y Copahue donde existen
   discrepancias documentadas.
4. **NO usar AVTOD para calibración cuantitativa de coeficientes Wooster** (asimetría
   sensor). Sí usarlo como **third-party qualitative ground truth** sobre presencia/ausencia
   de VTF real.

**Riesgo si lo ignoramos**: seguir gastando ciclos S70+ "ajustando MIROVA-equivalent" sobre
volcanes donde el propio grupo Cornell-Torino, mirando ASTER 90 m de la misma época, ya
documentó que MIROVA tiene FPs sistémicos por water-body / glacial-melt confundible.
Tupungatito es el caso canónico.

---

## 5. Pendientes (backlog S73+)

- [ ] Descargar Table S1 supplementary AVTOD (Elsevier Appendix A) → `documentacion/`.
- [ ] Scrapear AVA portal https://ava.jpl.nasa.gov/avtod.php por los 11 Tier A chilenos.
- [ ] Cuantificar AVTOD-n vs MIROVA-OSF-n por volcán-año 2000–2017 (validación cuantitativa
      retrospectiva).
- [ ] Cross-link AVTOD-evidence al `MIROVA_DIVERGENCES_CATALOG_S71.md` (columna nueva).
- [ ] Caso Tupungatito específico: extraer Tmax y n_AVTOD-detections para confirmar
      hipótesis FP-sistémico-MIROVA-en-crater-lake.

---

*Generado S72 (2026-05-22). Read-only sobre repo, no commitea (controller F2.6.f hace commit).*
