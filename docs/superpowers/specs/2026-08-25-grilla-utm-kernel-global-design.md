# Diseño F70 — Grilla UTM resampleada + kernel-bg global (el clon literal que falta)

> **Estado**: DISEÑO (aprobado por Nicolás 2026-08-25 como frente mayor).
> **Regla de oro**: todo se prueba en perfil aislado; `mirova_equivalent` no se toca
> hasta el veredicto final (A45 + 3 preguntas MISSION + confirmación explícita).

## 1. El fenómeno físico (por qué)

Un píxel de satélite no es un cuadrado fijo: lejos del nadir se estira hasta ~10 km²
(MODIS). Cuando el algoritmo pregunta "¿este píxel es más caliente que sus vecinos?",
la respuesta depende de la GEOMETRÍA de esos vecinos tanto como de su temperatura.
Sobre un volcán con glaciar, un vecino elongado off-nadir promedia hielo + roca + valle
en proporciones que cambian en cada pasada — el "fondo" que se le resta al foco es un
objeto distinto cada noche.

MIROVA elimina ese problema ANTES de detectar: recorta y **resamplea cada escena a una
grilla regular de 1 km** (50×50 km UTM centrada en la cumbre) y computa TODO sobre esa
grilla. Nosotros computamos sobre el swath crudo. Esa es la divergencia estructural.

## 2. Evidencia (papers, verificado 2026-08-25 sobre documentacion/ local)

- **Coppola 2016a** (`sp426_5.txt` ~L162): *"we cropped and resampled (into an equally
  spaced 1 km grid) the MODIS Level 1B data that fall within a grid (50 × 50 km)
  centred on the volcano's summit"*. Y la razón (~L150-160): el esquema de detección
  *"requires homogenous pixel scale"*.
- Las estadísticas contextuales (μ/σ) son de *"all the suitable pixels within the
  image"* — la matriz resampleada (~L327). El kernel 8-vecinos opera sobre celdas
  regulares. La universalidad de la Tabla 1 se afirma justo ahí: *"whatever the
  surface type sampled by each pixel"* (~L370-377).
- **Fondo de magnitud, Eq. 6** (~L355-360): *"L4bk is estimated from the arithmetic
  mean of all the pixels surrounding the active one (or around the active cluster)"*
  — el kernel local es EL método, global, sin excepciones per-volcán.
- **Campus 2024** (`campus2024_extracted.txt` L102-104, L119-122): VIIRS 375m usa el
  mismo esquema — *"after an initial resampling of the original granule in a regular
  50×50 km UTM grid"* + fondo por vecinos del píxel alertado.
- Ningún paper del canon menciona corrección por nieve/hielo/elevación. La robustez
  multi-terreno descansa en grilla + kernel + limpieza manual a posteriori (A76).

## 3. Qué explica esto (el diagnóstico)

1. **La polaridad de `local_kernel_bg` está invertida**: lo tenemos como excepción
   per-volcán (5 de 11, adoptado S59-S63 por A/B) cuando en MIROVA es la regla
   universal. La contradicción con MISSION l.74-79 nace de ahí.
2. **Por qué el kernel empeora Tupungatito** (A19, el caso que impidió hacerlo global
   en S62): lo aplicamos sobre swath. Sobre celdas regulares de 1 km, el anillo de
   glaciar deja de estar deformado por la geometría de escaneo. Hipótesis central:
   **la grilla cura lo que el kernel solo no puede**.
3. Probablemente conecta también con A69/A82 (sesgo topográfico, far→summit MODIS):
   el campo difuso que "gana" el hotspot está muestreado en píxeles gigantes off-nadir
   que la grilla normalizaría. NO lo asumimos — se mide en el A/B.

## 4. Diseño técnico propuesto

**Módulo nuevo `pipeline/regrid.py`** (puro, testeable):
- Entrada: lat/lon/radiancias del granule (las bandas ya leídas por process_*).
- Salida: matrices 2D regulares (51×51 @ 1 km MODIS/VIIRS750; resolución I-band a
  definir en F70.1 leyendo Campus 2022 — BIBLIOGRAPHY_SYNTHESIS §1 da 67×67 @ 750 m)
  en proyección UTM local centrada en `mirova_center` (ya lo tenemos de los KML).
- Método de resampling: **vecino más cercano** por defecto (conserva radiancias; un
  promedio inventaría mezclas). Documentar la elección; los papers no especifican el
  interpolador — es la única decisión no-literal, dejarla como parámetro.
- Celdas sin muestra (bordes, gaps bow-tie MODIS): NaN + máscara `suitable`.

**Integración** (flag-OFF, `enable_utm_regrid`):
- En process_modis/process_viirs/process_viirs_mod: si el flag está ON, después de
  leer bandas se regrilla TODO (MIR, TIR) y la detección corre sin cambios sobre las
  matrices regulares. La clave del diseño: los Tests 1/2/3, el kernel 8-vecinos, el
  second-pass y el clustering NO se tocan — solo cambia el sustrato geométrico. El
  área de píxel pasa a ser constante por construcción (nadir-fijo S102/S103 se vuelve
  redundante-consistente, no conflictivo).
- `enable_local_kernel_bg` global (los 11) SOLO en el brazo del A/B que corresponde.

**Lo que NO se hace**: tocar umbrales, tocar el frontend, tocar mirova_equivalent,
ni "aprovechar de" arreglar otra cosa en el mismo PR (anti-A55).

## 5. A/B pre-registrado (3 brazos + control, patrón A66)

Perfiles aislados `_f70_regrid_{a,b,c}` sobre ventana 2026-05-01..2026-08-24, 11 Tier A:

| brazo | grilla | kernel-bg | pregunta que contesta |
|---|---|---|---|
| control | OFF | per-volcán (actual) | baseline = serie operacional |
| A | ON | per-volcán (actual) | ¿la grilla sola mejora paridad? |
| B | ON | **global (11/11)** | **la hipótesis central (clon literal)** |
| C | OFF | global (11/11) | aísla el efecto kernel (réplica del fallo S62) |

**Criterios de éxito pre-registrados (fijados antes de correr)**:
1. **Tupungatito es el juez**: el brazo B debe curarlo (ratio → banda 0.5-2.0) donde
   el brazo C debe replicarlo roto (~18×, como S62). Si B lo cura y C no, la grilla
   era la pieza que faltaba. Si B también lo rompe, la hipótesis se refuta y se
   documenta en DIVERGENCES.
2. Lastarria NO debe romperse en B (hoy 1.07× con kernel; debe seguir en banda).
3. Paridad global: mediana de ratios de los 11 en B ≥ control; recall al cráter sin
   caídas >2 pp por sensor. A79: verificar además los eventos específicos (NdC
   16-jun, noches ancla), no solo agregados.
4. Espacial (A61): offset mediano al cráter por volcán en B ≤ control.
5. Si B pasa 1-4 → en el perfil promovido se apagan los flags per-volcán y MISSION
   queda sin contradicción. Si falla → los flags per-volcán se declaran excepción
   documentada (la salida (i) de la decisión de agosto).

## 6. Fases

- **F70.1** `pipeline/regrid.py` + tests unitarios sintéticos (grilla conocida,
  píxel caliente conocido → celda esperada). Sin tocar procesadores. Incluye
  resolver la resolución I-band (Campus 2022).
- **F70.2** Integración flag-OFF en los 3 procesadores + tests de integración
  (granule sintético → mismas detecciones con grid en el caso trivial nadir).
  Medición de costo computacional por granule.
- **F70.3** A/B (workflows clonando el patrón reproc, data_subdirs aislados).
- **F70.4** Análisis contra los criterios pre-registrados + veredicto con Nicolás.
- **F70.5** Solo con veredicto positivo: promoción con tag defensivo + reproc
  histórico + actualización FICHA SDA (cambio metodológico mayor, CPLT) + apagado
  de los flags per-volcán.

## 7. Riesgos conocidos

- **Costo computacional**: el regrid agrega interpolación por granule. Se mide en
  F70.2; el cron tiene margen (50 min/step).
- **Bordes y datos faltantes**: el 50×50 km puede caer parcialmente fuera del
  granule → máscara suitable honesta, sin rellenos.
- **El interpolador no está publicado**: decisión documentada, parametrizada, con
  sensibilidad chequeada (nearest vs media-por-celda) en F70.1.
- **A49**: las inserciones en los procesadores van con diff-review de que ninguna
  función pierda su return.

## 8. Trazabilidad

- Origen: pregunta de Nicolás 2026-08-25 ("¿qué nos falta descubrir? ¿dónde están
  las claves?") + investigación bibliográfica del mismo día (citas en §2).
- Decisión de Nicolás: implementar la grilla como camino de vuelta a la misión,
  probándolo en experimental primero. Este doc es la fase de diseño previa.
- Relacionados: A12/A19 (kernel-bg per-vol), A66/A67 (nadir-fijo), MISSION l.74-79,
  AUDIT_S123 §1.1 (la contradicción), issue #513 (Villarrica).
