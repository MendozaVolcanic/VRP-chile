# Plan Driver B — extensión geográfica del cluster contiguo

> S32 (2026-05-04). Driver A cerrado y commiteado. Driver B abierto.

## Síntoma

Después de Driver A (frontend reporta `primary_cluster.vrp_mw` summit-only),
ratio mediano global nuestro/MIROVA queda en **2.29×** (vs 6.25× pre-cambio).
Residual mayor en Chaiten (28×), Lastarria (18×), Planchón (16×), PCC (8×).

## Hipótesis de causa raíz

El `cluster_hotspots` 8-conn S31+ aplica vecindad de grilla **sin acotar
extensión geográfica**. En VIIRS 375m una cadena 8-conn puede llegar a 2-3 km
de extensión: pixel del cráter → pixel del flanco → pixel de fumarola →
pixel de afloramiento térmico contiguo. MIROVA reporta una región más
compacta (~1-2 km típico).

Evidencia indirecta (`experiments/62_driver_b_pixel_threshold.py`): cuando
reconstruyo el cluster acotando a **radio físico desde el centroid** (1 km
VIIRS 375, 2 km VIIRS 750, 3 km MODIS), el ratio mediano global cae a
**1.19×** sobre 299 muestras — paridad MIROVA prácticamente.

| Volcán (con radio físico + piso 0.05 MW) | n | Ratio mediano |
|---|---:|---:|
| Lascar | 112 | 1.10 |
| Isluga | 31 | 1.05 |
| Tupungatito | 21 | 0.55 |
| Planchón | 3 | 0.76 |
| Lastarria | 44 | 2.07 |
| Chaiten | 7 | 3.62 |
| PCC | 45 | 7.57 |
| GLOBAL | 299 | **1.19** |

## Pero (importante) — verificación pendiente antes de implementar

La reconstrucción del cluster por radio físico tiene dos limitaciones:

1. **`anomaly_pixels` exportado al JSON está incompleto**: sanity check
   `pc_vrp` reportado vs suma `anomaly_pixels` cercanos al centroid difiere
   60% mediano. Hay pixels en el cluster reportado que NO se exportaron
   (probable cap top-100 documentado como divergencia válida en MISSION.md
   sección "Cuándo SÍ se puede divergir"). Significa que la reconstrucción
   subestima el cluster real, y el "1.19× global" es optimista.

2. **No verificado contra MIROVA pixel-level**: el ratio 1.19× compara
   nuestro-reconstruido vs número CSV MIROVA, no vs los pixels que MIROVA
   efectivamente marca en el plot Latest10NTI. Sin esta verificación, el
   "radio físico" es un parámetro libre, no metodología MIROVA-derivada.

## Las 3 preguntas (MISSION.md)

1. **¿Está en papers MIROVA core?** Coppola 2016a SP 426.5 §2.2 "neighbor
   pixels" define vecindad pero NO menciona radio máximo. Borderline.
2. **¿Cierra divergencia?** D5 magnitud, parcialmente.
3. **¿Alineación interna?** No, toca pipeline si se implementa.

**Veredicto**: NO IMPLEMENTAR sin verificación pixel-level previa contra
MIROVA web. Saltarse el paso de verificación es exactamente el patrón
"parche sin causa raíz" que MISSION.md prohíbe.

## Plan de trabajo

### Fase 1 — Verificación empírica con MIROVA web (~2h)

Bajar 5 granules específicos donde MIROVA reportó VRP bajo y nuestro pc_vrp
es 8-30× mayor. Candidatos:

| Volcán | Sensor | Fecha UTC | MIROVA MW | Nuestro pc_vrp | Ratio | Tipo |
|---|---|---|---:|---:|---:|---|
| Lastarria | VIIRS375 | 2026-02-10 05:42 | 0.12 | 1.06 | 9× | summit típico |
| Lastarria | VIIRS375 | 2026-02-16 05:30 | 0.04 | 0.86 | 22× | low MIROVA |
| Planchón | VIIRS375 | (top peor del CSV) | <0.1 | >1 | 16× | summit |
| PCC | VIIRS375 | 2026-04-08 06:18 | 0.07 | (ring) | 489× | ring lacolítico |
| Chaiten | VIIRS375 | 2026-02-26 05:48 | 0.03 | 4.47 | 149× | extremo |

Pasos:
1. `pipeline/fetch.py` para descargar VNP02IMG/VNP03IMG de las fechas (Linux/CI
   o WSL local; pyhdf no requerido para VIIRS).
2. Replicar nuestra detección con `process_viirs.py`, capturar el array
   completo de pixels Test 1 anómalos del cluster (no el cap top-100).
3. Correlacionar con la imagen MIROVA Latest10NTI ya descargada en
   `experiments/60_audit_mirova_full/<volcán>/VIIRS375/Latest10NTI.png`.
4. Identificar pixel-por-pixel: ¿qué pixels marcó MIROVA dentro del granule?
   ¿extensión espacial? ¿VRP por pixel?

### Fase 2 — Decisión metodológica

Con datos pixel-level MIROVA en mano, responder:

- ¿MIROVA reporta cluster contiguo limitado por radio físico fijo?
- ¿O usa erode borde sobre el cluster 8-conn?
- ¿O aplica threshold pixel-level adicional (>0.05 MW)?
- ¿O es algo distinto (Test 1 mask sub-set, NTI gate por pixel)?

Solo entonces — con justificación basada en lo que MIROVA hace, no en lo
que conviene a nuestro recall — proponer fix de pipeline que pase las 3
preguntas con confianza.

### Fase 3 — A/B test (si aplica)

Patrón validado S24+S25: clonar `reproc-ab-test1.yml`, dos profiles
`_cluster_extent_{enabled,disabled}.yaml`, reprocesar 11 Tier A 90d, audit
delta. Si delta valida → push main.

## Diagnóstico lateral pendiente

`anomaly_pixels` exportado al JSON difiere del cluster real reportado. No
afecta nada operacional (el `pc_vrp` reportado sí es correcto), pero limita
análisis frontend-side. Si en el futuro se quiere agregar interactividad
"explorar pixels del cluster" en el dashboard, hay que decidir: ¿exportar
todos los pixels del cluster (no solo top-100 globales)? ¿O recomputar
client-side desde `pc_vrp` + n_pixels?

No urgente. Anotar como tema de schema futuro.

## Orden recomendado para próxima sesión

1. Repasar este plan + leer `MIROVA_DIVERGENCES.md` para ver si D5 puede
   re-abrirse formalmente con este hallazgo.
2. Decidir Fase 1 (~2h) o postponer a S33.
3. Si Fase 1: ejecutar 3-5 casos, escribir hallazgos en
   `experiments/63_pixel_level_audit/`.
4. Si confirmado → Fase 2-3.
