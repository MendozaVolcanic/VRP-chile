# R2 Gates by Regime — Referencia operacional VRP Chile

> Cuándo y cómo aplicar el método R2 retroactivo según régimen térmico del volcán.
> Síntesis empírica de S70-0 T3 (validación método) + S70-1 (5 vols Tier A) + S70-2 T1
> (PP multi-caso bimodal).

---

## 1. Qué es R2 retroactivo

El método R2 retroactivo es una validación **pixel-level** post-adopción que cruza dos
fuentes independientes para verificar que una calibración metodológica (p. ej. activar
`local_kernel_bg: true` en `mirova_equivalent.yaml`) no sólo cuadra a nivel de **agregado**
sino también a nivel de **caso individual** geométrica y energéticamente.

Concretamente, sobre una ALERTA MIROVA con TIF paralelo disponible en
`mirova-tif-archive`, se evalúa:

1. **Componente magnitud** — ratio entre lo que nuestro pipeline persiste (`pc.vrp_mw`
   del record en `data/mirova_equivalent/<Volcan>.json`) y lo que MIROVA publica en su
   `registro_vrp_consolidado.csv` para esa misma pasada. Banda objetivo `[0.5, 2.0]`
   (clon literal con tolerancia ±2× MIROVA, igual que D5).
2. **Componente geometría** — drift entre el centroide ponderado de los top-10 pixels
   positivos del TIF MIROVA filtrados a `<=3 km del vent` y nuestro `pc.centroid` del
   mismo record. Banda objetivo `<2 km` (Lastarria-style estricto) o `<3 km` (revisado).

**Atención**: el TIF MIROVA **NO** es un raster sumable de VRP por pixel — es un campo
continuo de radiancia/anomalía pintado sobre el bbox de ~50×50 km para visualización
(verdict S70-0 T3 Parte 1, ratio top10/CSV_VRP = 11.5× en Lastarria sin filtro). Por eso
el filtro `<=3 km del vent` es lo que rescata la región físicamente coherente con el
cráter; sin ese filtro, el método R2 no mide nada útil. Detalle en
`docs/MIROVA_DIVERGENCES.md` D6.

---

## 2. Por qué hay regímenes

Los volcanes chilenos Tier A no son térmicamente homogéneos. La señal que MIROVA
publica como "ALERTA_TERMICA" sale de mecanismos físicos distintos según el volcán:

- **Cráter activo compacto con magma cerca de superficie** (Lastarria, Lascar, Isluga):
  el calor se concentra en un punto, ΔT muy por encima del fondo, cluster pixel-discreto.
- **Lava lake o domo extendido con halo termal difuso** (Villarrica, Chaitén, Planchón-
  Peteroa): el cráter activo es un foco pequeño pero hay un anillo termal continuo a
  pocos km (calor de paredes, fumarolas perimetrales, halo radiativo).
- **Complejo multi-cráter co-activos a pocos km** (Planchón-Peteroa: Planchón Sur +
  Peteroa + Azufre): la ALERTA puede asignarse a cualquiera de los cráteres del complejo
  según la noche.
- **Intrusión / lacolito difuso sin foco térmico** (PuyehueCordónCaulle lacolito 2011,
  ~707 km²): no hay "cráter activo" puntual; la anomalía cubre un área grande sin pico
  identificable.

Cada uno de estos regímenes responde distinto a un gate "ratio in [0.5, 2.0] + drift
<2 km" estricto. Lo que es PASS contundente en Lastarria (cluster focal puro) puede ser
FAIL marginal en Villarrica (halo difuso) sin que el pipeline esté roto — la diferencia
está en la **agregación natural del fenómeno térmico**, no en error de detección.

**Por eso las gates R2 son régimen-dependientes**. Aplicar Lastarria-style a un vol Muy
Bajo como Chaitén genera FAIL artefactos que ocultan que la adopción de hecho funciona.

---

## 3. Clasificación de régimen

Antes de aplicar R2 a un vol nuevo, clasificar:

### Régimen A — Focal puro (Tier A Alto)

**Criterios observables**:
- ΔT máxima histórica del vol **>20 K** (consultar `volcanoes.yaml` notas, `MIROVA_DETAILED_CITATIONS.md`, o calcular de un granule reciente).
- Cluster térmico nuestro típicamente **<2 km²** (`pc.n_pixels` 1–5 VIIRS375).
- Calibración "natural" (sin `local_kernel_bg`) ya da ratio mediano cercano a 1×.
- Geológicamente: cráter activo único con magma cerca de superficie, fumarolas potentes,
  o erupción crónica.

**Ejemplos**: Lastarria, Lascar, Isluga.

**Banda gates**: ratio `[0.5, 2.0]` + drift `<2 km`. PASS estricto exigible.

**Justificación física**: la señal es concentrada, ΔT alto, el centroide ponderado de
los top-10 pixels TIF cae casi exactamente sobre el pixel granule que el pipeline
clusterizó. No hay halo difuso que arrastre el centroide.

### Régimen B1 — Focal con halo (Tier A Muy Bajo simple)

**Criterios observables**:
- ΔT máxima del vol **<12 K**.
- Cluster nuestro típicamente **<5 km²** (`pc.n_pixels` 1–30 VIIRS375 en casos clean,
  pero ocasionalmente sube cuando el halo entra al cluster).
- Adopción requiere `local_kernel_bg: true` para calibrar a `[0.5, 3.0]` (ratio LEGACY
  pre-fix típicamente >5×, post-fix 1.5–3×).
- Geológicamente: lava lake activo, domo extendido con desgasificación continua, o
  cráter Muy Bajo con halo termal radiativo del cuerpo magmático.

**Ejemplos**: Chaitén, Villarrica.

**Banda gates**: ratio `[0.5, 2.0]` preferido + drift `<3 km` (revisado).

**Justificación física**: la señal es débil y el ΔT es bajo, por lo que el ruido
per-record es mayor (cualquier nube cirrus tenue, fluctuación del lava lake, o pixel
parcialmente cubierto cambia la magnitud). El halo termal del cráter activo pinta
pixels positivos a 1–3 km que entran al filtro `<=3 km` y arrastran el centroide
ponderado hacia un drift de 2–2.5 km. No es bug del pipeline — es la firma del fenómeno.

### Régimen B2 — Complejo multi-cráter (Tier A Muy Bajo complejo)

**Criterios observables**:
- Igual que B1 (ΔT <12 K, adopción `local_kernel_bg: true`).
- **Adicionalmente**: el vol tiene 2+ cráteres activos o sub-activos a **pocos km uno
  del otro** dentro del mismo edificio volcánico.
- Distribución per-record del ratio es **bimodal**, no normal: un modo con clusters
  pequeños (1–5 px, ratio 1–2×) y otro con clusters grandes (50+ px, ratio 10×+).

**Ejemplo único confirmado S70**: PlanchonPeteroa (Planchón Sur + Peteroa + Azufre en
~3–5 km).

**Banda gates**: ratio `[0.5, 2.0]` + drift `<3 km`, **pero validar con N≥5 casos**
(reportar mediana). Un único caso "representativo" en este régimen es engañoso porque
la distribución bimodal puede caer en Modo A (ratio 1–2×, PASS limpio) o Modo B
(ratio 10×, FAIL agudo) sin que ninguno de los dos sea representativo del agregado.

**Justificación física**: cuando la señal del cráter principal (en PP: Peteroa) es Muy
Baja, el pipeline a veces aísla 1–2 pixels del cráter (Modo A — ratio coherente con
MIROVA) y otras veces clusteriza un halo regional que abarca el cráter principal +
pixels al norte hacia un cráter vecino o halo orográfico (Modo B — cluster saturado,
ratio inflado 10×+). MIROVA en estas mismas escenas reporta VRP muy bajo (sin saturarse
al halo), lo que sugiere que su selección de cluster es más conservadora. **Es un
problema de cluster selection residual**, no del fix `local_kernel_bg`. La mediana
sobre N≥5 casos captura honestamente la mezcla de los dos modos.

### Régimen C — No focal (difuso)

**Criterios observables**:
- ΔT máxima baja o moderada, **pero cluster típico >50 km²** (PCC: anomalías cubriendo
  pixels a 5–10 km del vent nominal en patrón espacial extendido).
- Geológicamente: intrusión magmática, lacolito, domo extendido sin pico térmico
  discreto, campo geotermal post-eruptivo.

**Ejemplo**: PuyehueCordónCaulle (lacolito 2011, ~707 km², `inner_radius_km=20` por
ese motivo).

**Banda gates R2 con drift**: **NO APLICA**. La intrusión cubre cientos de km² sin pico
identificable, por lo que el centroide ponderado del campo TIF no representa ningún
cluster discreto y el drift contra `pc.centroid` es artefacto del método, no error
del pipeline (PCC R2 S70-1 T4: drift 9.77 km — el TIF y nuestro cluster están ambos
"en la zona difusa", pero a 9 km uno del otro, lo que físicamente significa nada).

**Validación alternativa**:
1. Ratio per-record vs ratio agregado adopción (PCC S63: agregado 0.29×, T4 caso individual 0.575× → coherente).
2. Confirmación geométrica: verificar que el cluster nuestro está **dentro de la zona
   difusa** marcada por MIROVA (no en el vent nominal, no en flanco lejano). Para PCC:
   cluster a 5.6–8.5 km del vent, MIROVA reporta @ 7.73 km — ambos en el cuerpo del
   lacolito.

---

## 4. Tabla resumen

| Régimen | ΔT vol | Cluster típico | Ejemplos | Banda ratio | Banda drift | N casos requerido |
|---|---|---|---|---|---|---|
| A — Focal puro | >20 K | <2 km² | Lastarria, Lascar, Isluga | [0.5, 2.0] | <2 km | 1 (PASS limpio) |
| B1 — Focal con halo | <12 K | <5 km² | Villarrica, Chaitén | [0.5, 2.0] | <3 km revisado | 1–3 |
| B2 — Complejo multi-cráter | <12 K | bimodal 1–70 px | PlanchonPeteroa | [0.5, 2.0] mediana | <3 km mediana | **N≥5, mediana** |
| C — No focal (difuso) | variable | >50 km² | PuyehueCordónCaulle | **R2 con drift no aplica** | — | usar magnitud agregada + confirmación geométrica |

---

## 5. Patrón de aplicación R2 (paso a paso)

Reproducible para cualquier vol nuevo. Detalle en `experiments/120_audit_tif_vrp_sumable/README.md`
Parte 2.

1. **Clasificar régimen** del vol con sección 3 antes de empezar. Si Régimen C, ir a
   sección 7.
2. **Identificar caso(s)**: tomar la(s) ALERTA(s) MIROVA con TIF paralelo disponible
   en `mirova-tif-archive/data/tif/<Volcan>/`. Para Régimen A y B1 basta 1 caso reciente;
   para B2 elegir N≥5 ALERTAs en una ventana del TIF archive.
3. **Cross-match**: por cada caso, sacar `pc.vrp_mw`, `pc.centroid`, `pc.n_pixels` y
   `pc.centroid_dist_km` del record correspondiente en
   `data/mirova_equivalent/<Volcan>.json`. Cruzar contra `registro_vrp_consolidado.csv`
   (Mirova-v1 scraper) por `Fecha_Satelite_UTC` exacto para sacar `VRP_MW` MIROVA y
   `Distancia_km`.
4. **R2 magnitud**: ratio = `pc.vrp_mw / VRP_MW_MIROVA`. Validar contra banda del
   régimen (sección 4).
5. **R2 geometría**: cargar TIF, filtrar pixels positivos a `<=3 km` del vent
   (`volcanoes.yaml`), tomar top-10 ponderados, calcular centroide. Drift = distancia
   geodésica entre ese centroide y `pc.centroid`. Validar contra banda del régimen.
6. **Verdict por caso** (Régimen A, B1) o **mediana N≥5** (Régimen B2).
7. **Documentar** en `experiments/NN_r2_<vol>/` con `audit_<vol>.py`, `results.json` y
   `README.md`. Sumar entry a `docs/HYPOTHESIS_LOG.md` si corresponde.

---

## 6. Sensitivity `max_km` por régimen

El parámetro `max_km` del filtro espacial (default 3.0) es el más sensible del método.
Recomendaciones por régimen, basadas en S70-1 T1.5 (Lastarria) y T3 (PP):

| Régimen | max_km recomendado | Nota |
|---|---|---|
| A — Focal puro | 3.0 km | Robusto a 2.0–3.0. Lastarria: drift <1.1 km en 6/9 combinaciones. |
| B1 — Focal con halo | 2.0–3.0 km | Probar AMBOS. Con max_km=2 el drift suele bajar a <1.5 km (cluster correcto); max_km=3 captura el halo. Documentar ambos. |
| B2 — Complejo multi-cráter | 2.0 km mejor, 3.0 principal | Diferencia clara: PP con max_km=2 da drift 0.27–0.41 km (cluster sobre Peteroa); con max_km=3 sube a 2.0–2.2 km porque entran pixels al N hacia Planchón Sur. |
| C — No focal | irrelevante | Sin filtro espacial sensato — la anomalía cubre >50 km². |

`top_n` (default 10) es robusto: variar entre 5/10/20 produce drifts muy similares
(Lastarria sensitivity: rango drift 0.24–3.64 km dominado por `max_km`, no por `top_n`).

---

## 7. Cuándo NO usar R2 (criterios de exclusión)

R2 retroactivo NO debe aplicarse, o su resultado no es informativo, si:

- **Régimen C** (no focal): el drift es artefacto. Validar adopción por ratio agregado
  + confirmación geométrica del cluster en la zona difusa.
- **TIF no disponible** para el caso en `mirova-tif-archive/data/tif/<Volcan>/`
  (timestamp exacto match requerido).
- **Record nuestro sin `pc.vrp_mw`** o sin `pc.centroid`, o con `distance_class != summit`.
- **Snapshot CSV ground truth anterior** al caso (sin row en `registro_vrp_consolidado.csv`
  para esa pasada).
- **`pc.n_pixels` saturado** (>>50 en B2 cuando se esperaba clean): el caso es Modo B,
  no representativo si se intenta usar single-case.

---

## 8. Validación multi-caso vs single-case

Cuándo basta un solo caso vs cuándo requiere mediana sobre N:

| Régimen | Single-case basta | Requiere N≥5 mediana |
|---|---|---|
| A — Focal puro | ✓ Sí (Lastarria 2026-05-14: PASS 4/4 estricto, suficiente para validar adopción) | — |
| B1 — Focal con halo | ✓ Sí en casos clean (Chaiten T1: PASS 2/2 revisado, Villarrica T2: PASS 2/2 revisado) | Si el caso individual cae marginal (FAIL g1 por <0.2), considerar N=3–5 |
| B2 — Complejo multi-cráter | ✗ No — sesgo bimodal | ✓ **Obligatorio**. PP S70-1 T3 single-case (2026-05-18) dio FAIL marginal 2.08×/2.20 km; PP S70-2 T1 multi-caso N=7 dio mediana 2.08×/2.20 km (marginal coherente), revelando estructura bimodal (Modo A 1–2× / Modo B 10×+) que single-case oculta |
| C — No focal | N/A (R2 con drift no aplica) | — |

---

## Edge case: path D dNTI contextual en cirrus alto

Independiente del régimen (A/B1/B2/C), si el background es muy frío (t_bg <270K) por cobertura cirrus alta, el path D (dNTI contextual S15 P3.2) puede disparar espuriamente — el contraste local entre el pixel del cráter (270K normal) y los vecinos enfriados (245-270K) supera 3σ aunque no haya calor volcánico real.

**Síntomas**:
- pc.vrp_mw alto (5-30 MW) con `diag_n_bt_path=0, diag_n_nti_path=0, diag_n_dnti_ctx_path>0`.
- t_bg <270K y t_max <280K (pixels fríos, no calientes).
- MIROVA NO reporta ALERTA en el mismo timestamp.

**Verdict R2 en estos casos**: NO usar el record para validar adopción — flagear como path-D-solo y referir a D9.

**Pendiente arquitectural**: gate atmosférico sobre path D (ver D9 opciones 1-3). S71+.

---

## 9. Referencias

**Divergencias documentadas**:
- `docs/MIROVA_DIVERGENCES.md` **D6** — TIF MIROVA no es VRP per-pixel sumable (verdict
  S70-0 T3 Parte 1).
- `docs/MIROVA_DIVERGENCES.md` **D7** — Método R2 retroactivo tiene aplicabilidad
  limitada por régimen del vol (S70-1 T5).
- `docs/MIROVA_DIVERGENCES.md` **D9 path D cirrus** — Path D dNTI contextual genera FPs +
  amplificación en cirrus alto (S70-2 T4, bug abierto, fix DIFERIDO S71).

**Hipótesis log**:
- `docs/HYPOTHESIS_LOG.md` **H_S70_TIF_VRP_SUMABILITY** — TIF es campo radiancia +
  método R2 verdadero validado.
- `docs/HYPOTHESIS_LOG.md` **H_S70_R2_RETROACTIVO_4VOLS** — cierre audit S67 con 5/5
  Tier A R2 evaluados.
- `docs/HYPOTHESIS_LOG.md` **H_S69_R2_RETROACTIVO_LASTARRIA** — adopción S62 Lastarria
  validada R2 pixel-level (caso fundacional del método).
- `docs/HYPOTHESIS_LOG.md` **H_S70_PATH_D_CIRRUS_FP** — Path D dNTI contextual genera
  FPs masivos + amplificación VRP en cirrus alto (S70-2 T4, CONFIRMADA + fix DIFERIDO S71).

**Experimentos**:
- `experiments/120_audit_tif_vrp_sumable/` — Lastarria template + sensitivity (S70-0 T3
  + S70-1 T1.5).
- `experiments/122_r2_chaiten/` — Chaiten T1 (Régimen B1).
- `experiments/123_r2_villarrica/` — Villarrica T2 (Régimen B1).
- `experiments/124_r2_planchon_peteroa/` — PP T3 single-case + `results_multi.json` PP
  S70-2 T1 multi-caso N=7 bimodal (Régimen B2).
- `experiments/125_r2_pcc/` — PCC T4 (Régimen C, R2 con drift no aplica).
