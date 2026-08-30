# S128 · Higiene del corpus bibliográfico

**Alcance**: trazabilidad de `documentacion/`, no lectura de papers. Qué archivo es qué,
quién firma qué, cuánto del corpus está realmente sintetizado y qué está duplicado.

**Fuente de verdad de todo número de este informe**:
`docs/s128/corpus_inventory.json`, generado por
`scripts/audit_corpus_documentacion.py`. Regla S91: acá no se transcribe nada a mano;
si un número de este documento no está en ese JSON, es un error.

- Inventario generado: **2026-08-30T12:54:53Z**
- Corpus: **120 archivos**, **649,1 MB**, **70 documentos distintos**
- Cache auxiliar de portadas (DOI + encabezado de cada PDF): `docs/s128/_pdf_page1_cache.json`

**Resumen ejecutivo**: los cuatro archivos reportados como rotos o mal identificados
**lo están, los cuatro**, y uno de ellos resultó ser el mismo incidente que otro (no dos
descargas fallidas, una sola repetida). Las atribuciones erradas de la síntesis no eran
cuatro sino **cinco**, y la quinta es la única que toca un número del pipeline. El «54 %»
de cobertura es viejo: hoy es **65,7 %**. Y los redundantes no son ~76 MB sino
**101,9 MB** — un tercio más de lo que se creía, con el disco al 98 %.

---

## 1 · Archivos rotos o mal identificados

### 1.1 `cigolini2022_epsl.pdf` → **CONFIRMADO: no es un PDF**

```
$ head -c 120 documentacion/cigolini2022_epsl.pdf
<!DOCTYPE html>
<html lang='en-us'>
<head>
  <meta content="text/html; charset=UTF-8" http-equiv="Content-Type" >
```

Los 833 KB son una página de ScienceDirect con SVGs y scripts embebidos. El texto
visible, extraído, son 642 caracteres:

> *"There was a problem providing the content you requested … Reference number:
> 9ff4da4b5a95f5f1 … IP Address: 181.172.94.164 … CPE00001 …
> ::CLOUDFLARE_ERROR_1000S_BOX::"*

**Renombrado** a `documentacion/cigolini2022_epsl.html.roto`. No se borró nada.

**Qué paper debería ser** (A89: no aparecía buscando «Cigolini» porque el apellido del
autor principal es otro; la respuesta ya estaba en el repo, en
`docs/papers_mirova_processed_S72_backlog.md:14` y `:173-178`):

| campo | valor |
|---|---|
| Autor principal real | **M. Laiolo** — Cigolini es co-autor #5, no primero |
| Título | *Shallow magma dynamics at open-vent volcanoes tracked by coupled thermal and SO₂ observations* |
| Revista | Earth and Planetary Science Letters **588**:117726 (2022) |
| DOI | `10.1016/j.epsl.2022.117726` |
| Licencia | CC-BY (debería ser descargable) |
| Estado | **NO descargado.** S72 probó Elsevier + flore.unifi.it + iris.unipa.it + arpi.unipi.it + Unpaywall + Semantic Scholar: los cuatro espejos OA están detrás de Cloudflare. Sólo hay abstract reconstruido vía OpenAlex |

**Canon MIROVA (A9)**: SÍ — Laiolo/Cigolini son Torino/Firenze. Es un paper que sí se
podría citar como autoridad; por eso vale la pena reconseguirlo (Chrome MCP con sesión
real, o pedirlo por acceso institucional SERNAGEOMIN).

### 1.2 `laiolo2022_epsl_openvent.md` → **CONFIRMADO: página de error de Elsevier**

```
$ head -c 100 documentacion/laiolo2022_epsl_openvent.md
[![Elsevier logo](data:image/svg+xml;base64...)ScienceDirect](/)
* Help
# There was a problem providing the content you requested
```

**Hallazgo no previsto**: no son dos incidentes distintos. Es **el mismo**. Los dos
archivos llevan la **misma referencia de Cloudflare `9ff4da4b5a95f5f1` y la misma IP
`181.172.94.164`** — o sea, la misma petición fallida guardada dos veces, una como
`.pdf` crudo y otra pasada por markitdown. En la contabilidad del corpus eran dos
papers; en realidad son cero.

**Renombrado** a `documentacion/laiolo2022_epsl_openvent.md.roto`.

### 1.3 `coppola2025_cap11_extracted.pdf` → **CONFIRMADO: no contiene el capítulo 11**

El archivo sí es un PDF válido (`%PDF-1.7`, producido por pypdf), 36 páginas, pero su
contenido es índice del libro + capítulo 1:

```
pág. 1-2 : "Contents / Time-Variable Volcano Gravimetry ... 1 / Daniele Carbone / ..."
pág. 3   : "1 · Time-Variable Volcano Gravimetry · Daniele Carbone · Abstract
            Among the geophysical techniques used to monitor volcanic unrest, only
            gravimetry can supply direct information on changes in the distribution
            of underground mass over time..."
```

El índice del propio archivo confirma además **que la numeración «cap. 11» es correcta**:
contando las entradas, *Thermal Monitoring of Volcanoes from Space · Diego Coppola ·
p. 325* es la undécima. Corrobora: `978-3-031-86841-2_9.pdf` es el capítulo 9
(*Remote Monitoring of Volcanic Gases*, Robin Campion). El nombre estaba bien; la
extracción salió mal.

**Renombrado** a
`documentacion/NO_ES_cap11__frontmatter_y_cap1_gravimetria.pdf`.

**Verificación de la afirmación «el texto real sí está en `coppola2024_chapter.txt`»:
CONFIRMADA.**

```
$ head -c 120 documentacion/coppola2024_chapter.txt
===PDF_IDX=328 BOOK_PAGE=325===
Thermal Monitoring of Volcanoes from Space
Diego Coppola

$ grep -c BOOK_PAGE documentacion/coppola2024_chapter.txt      -> 40
$ grep -oE 'BOOK_PAGE=[0-9]+' ... | head -1                    -> BOOK_PAGE=325
$ grep -oE 'BOOK_PAGE=[0-9]+' ... | tail -1                    -> BOOK_PAGE=364
```

Páginas 325 a 364, sin huecos: el capítulo **entero** (el siguiente, Sandri et al.,
empieza en 365). Es el archivo que hay que leer. El libro completo también está, en
`978-3-031-86841-2.pdf` (93 MB).

### 1.4 `MCDWD_UserGuide_RevC.pdf` → **CONFIRMADO: es el producto de inundaciones**

Portada, verbatim (página 1 de 40):

> *"MODIS NRT Global Flood Product — MODIS Aqua+Terra Global Flood Product L3 NRT 250m —
> Provided by NASA LANCE — User Guide — Revision C — Author: Dan Slayback, Science Systems
> & Applications, Inc., & Biospheric Sciences Lab, Code 618, NASA Goddard Space Flight
> Center"*

Y el pie de la figura de portada: *"The 2-Day flood product showing extensive flooding
(in red) in the lower Mekong region of Cambodia and Vietnam, and normal water (in cyan)"*.

Mapea **agua superficial anómala**, no nubosidad. La síntesis lo llamaba *"producto
máscara nubes/agua MODIS — no lo estamos usando, podría mejorar nuestro cloud masking
actual (gap)"*: eso es falso y además es una pista muerta justo en el frente abierto #4
(filtrado de nube). El producto que corresponde mirar para ese frente es MOD35/MOD06 —
`Platnick_MODIS_MOD06_ATBD.pdf` y `Frey_2008_MODIS_CloudMask_Collection5.pdf`, **los dos
ya están en el repo y ninguno está sintetizado**.

El nombre del archivo es correcto (MCDWD *es* el código del producto de flood), así que
no se renombró. Se corrigió la descripción en `BIBLIOGRAPHY_SYNTHESIS.md` §5.

> ⚠️ **Queda una copia de la descripción vieja fuera de mi alcance de edición**:
> `docs/DATA_SOURCES.md:147` dice *"MCDWD User Guide | Cloud-water mask (no usado
> actualmente, gap)"*. Reemplazo sugerido: *"MODIS NRT Global Flood Product L3 250 m
> (LANCE) — producto de inundaciones, NO máscara de nubes"*.

---

## 2 · Atribuciones erradas en `BIBLIOGRAPHY_SYNTHESIS.md`

Método: abrir la primera página de cada PDF citado en la síntesis y comparar la línea de
autores con lo que la síntesis afirma. Se encontraron **cinco**, no cuatro. Las cinco
están corregidas en el archivo, cada una con una nota `*(S128: …)*` que dice qué decía
antes, para que la corrección no se lea como si el texto siempre hubiera estado bien.

| # | Archivo | La síntesis decía | Autores reales (portada) | Grupo | ¿Contaminó metodología? |
|---|---|---|---|---|---|
| M1 | `remotesensing-16-02001-v2.pdf` | «**Trasatti** et al. 2024» | **Corradino, C.; Malaguti, A.B.; Ramsey, M.S.; Del Negro, C.** | INGV Catania + Univ. Pittsburgh — **NO canon** | No. Sólo trazabilidad |
| M2 | `remotesensing-17-02102-v2.pdf` | «**Marchese / Ganci** et al. 2025» | **Filizzola, C.; Mazzeo, G.; Marchese, F.; Pietrapertosa, C.; Pergola, N.** | CNR-IMAA Potenza — **NO canon** | No. **Ganci ni siquiera firma** el paper; Marchese es #3 |
| M3 | `remotesensing-18-00006.pdf` | «**Marchetti** et al. 2026» | **Torrisi, F.; Di Bella, G.S.; Corradino, C.; Cariello, S.; Malaguti, A.B.; Del Negro, C.** | INGV Catania — **NO canon** | No. Marchetti no firma |
| M4 | `Advancing_Volcanic_Activity_Monitoring_A_Near-Real.pdf` | «**Sansosti / Marchetti** et al. 2024 — RSDF, RS 16:2879 … *bajar*» | **Di Bella, G.S.; Corradino, C.; Cariello, S.; Torrisi, F.; Del Negro, C.** | INGV Catania — **NO canon** | No metodológicamente, **sí operativamente**: la entrada mandaba a *bajar* un paper que ya estaba en el repo y que la propia síntesis describe en §1 como «Di Bella 2024» |
| M5 | `s00445-024-01721-z.pdf` | «**Laiolo** 2024 (18.0 × A_pix)» en §1 y en la tabla de umbrales canónicos §6 | **Campus, A.; Aveni, S.; Laiolo, M.; Massimetti, F.; Coppola, D.** | Torino/Firenze — **SÍ canon MIROVA** | **No, por suerte** — ver abajo |

### Por qué M5 es la que importa

Es la única de las cinco que toca un número del pipeline. `WOOSTER_COEFF = 18.0` de
`pipeline/process_viirs.py:74` — el coeficiente k_MIR de VIIRS I4 375 m — sale de ese
paper, y la síntesis lo atribuía a «Laiolo 2024». El paper dice, verbatim (extraído del
PDF completo):

> *"…the constant value k MIR represents the proportionality between the spectral radiance
> in the MIR bands and the radiant flux density (W m⁻²) for bodies with temperatures
> between 600 and 1500 K (see Wooster et al. 2003 for details). It is related to the
> wavelength of the band and in the case of VIIRS I4 band has a value of **18.0 μm sr**."*

O sea: **el número está bien, el grupo está bien (Campus, Aveni, Laiolo, Massimetti y
Coppola son todos canon Torino/Firenze), y quien firma primero es Campus**. Laiolo es
co-autor #3. La confusión no contaminó ninguna decisión metodológica: sólo hacía que un
`grep laiolo` no encontrara la fuente del coeficiente y que un `grep campus` la
encontrara sin que nadie lo esperara — otra instancia de A89.

Las otras cuatro (M1-M4) son todas de grupos **no canon** (Catania y Potenza), que por
regla A9 no se citan como autoridad metodológica. Ahí el daño era distinto: el riesgo no
era importar un método ajeno, era **buscar y no encontrar** — y en M4, salir a bajar por
segunda vez un PDF que ya estaba en disco.

### Correcciones adicionales, del mismo barrido

- «**Bella** et al. 2024» → **Di Bella**. El apellido es compuesto; aparecía truncado en
  el encabezado de §4 y en dos celdas de la tabla de §6.
- «Paper SLSTR 2025 … *(citación pendiente de confirmar autoría)*» → resuelta:
  **Falconieri, A.; Marchese, F.; Ciancia, E.; Genzano, N.; Mazzeo, G.; Pietrapertosa, C.;
  Pergola, N.; Plank, S.; Filizzola, C.**, Sensors 25:1658, `10.3390/s25061658` (CNR-IMAA,
  no canon). El PDF ya está en el repo: `sensors-25-01658-v2 (1).pdf`.
- El encabezado de §1 «Vulcano 2024 (s00445-024-01721-z)» pasó a nombrar al autor y a
  citar el volumen correcto: **Bull Volcanol 86:25** (decía «86» a secas en §8bis).

---

## 3 · El ítem fantasma de `MISSION.md`

`docs/MISSION.md` listaba «Coppola 2015 (Test 1, NTI)» y «Coppola 2016a SP 426.5» como dos
papers core distintos. **Son uno solo.**

El hash original no se puede re-correr: `documentacion/coppola2015.pdf` ya no existe en
disco, y `documentacion/` está en `.gitignore` (`git check-ignore -v` →
`.gitignore:2:documentacion/`), así que tampoco hay historia de git donde recuperarlo. Pero
la verificación sustantiva es más fuerte que el hash y sí se pudo hacer, por dos lados:

**(a) El `Test 1` está dentro de SP426.5.**

```
$ grep -n "Test 1" documentacion/sp426_5.txt
298:threshold:      Pixels that satisfy Test 1 are flagged as `active'
300:NTIPIX . K1  (Test 1)
```

**(b) El único Coppola realmente fechado 2015 que hay en el repo no es esto.** Es
`1-s2.0-S0377027315003716-main.pdf` — *Fifteen years of thermal activity at Vanuatu's
volcanoes (2000–2015) revealed by MIROVA*, Coppola, Laiolo, Cigolini, JVGR,
`10.1016/j.jvolgeores.2015.11.005`. Barrido sobre sus 14 páginas completas:

| patrón | apariciones |
|---|---|
| `Test 1` | **0** |
| `NTI` | **0** |
| `K1` | **0** |
| `SP426` | 1 (en la bibliografía — o sea, lo *cita*) |

No es la fuente del Test 1; es un paper de aplicación que cita a SP426.5. El «2015» del
nombre de archivo era la fecha de publicación online de SP426.5; el «2016», la del volumen
impreso — exactamente lo que `BIBLIOGRAPHY_SYNTHESIS.md:23-26` ya documentaba desde S13 y
que `MISSION.md` nunca incorporó.

**Corregido**: la lista canónica de `MISSION.md` ahora encabeza con
*"Coppola 2016a SP 426.5 (Test 1 + NTI; Tabla 1 N·σ …)"* y lleva la nota de una línea que
pedía el encargo, para que S129 no lo re-descubra. **La lista tiene 11 papers, no 12.**
Se normalizaron además las otras dos citas internas a «Coppola 2015» (`MISSION.md:138` y
`:197`), que apuntaban al mismo fantasma.

---

## 4 · Cobertura real de la síntesis

El «**30/60 PDFs (54 %)**» es de S13 (2026-04-18) y nunca se volvió a medir. Re-medido con
`scripts/audit_corpus_documentacion.py`:

| métrica | valor |
|---|---|
| Archivos en `documentacion/` | **120** |
| **Documentos distintos** | **70** |
| **Con entrada en la síntesis** | **46** |
| **Cobertura** | **65,7 %** |
| Sólo PDFs (denominador comparable con el «/60» viejo) | 46 / 68 = **67,6 %** |

**Cómo se cuenta un «documento»** (importa, porque de acá salen las diferencias con
mediciones previas):

- un PDF y su `.md`/`.txt` extraído son **uno**;
- dos archivos con el **mismo md5** son **uno** (copias renombradas);
- las extracciones parciales, suplementos y capítulos sueltos se declaran en el mapa
  `SAME_DOC` del script (los cinco `.txt` de la tesis de Massimetti son un documento, no
  cinco; los `.xlsx` suplementarios de Coppola 2019 van con su paper);
- las síntesis **nuestras** (`BIBLIOGRAPHY_SYNTHESIS.md`, los dos
  `perplexity_deep_research_S72*.md`, `MIROVA_DETAILED_CITATIONS.md`, la revisión de
  índices de vegetación) no son papers y quedan fuera del denominador.

**Cómo se decide «cubierto»**: unión de dos señales exactas —el DOI de la portada, o el
identificador de editorial (`s00445-024-01721-z`, `feart-11-1240107`, `16:2001`)— más un
mapa curado `COVERED_ANCHORS` para los papers que la síntesis cita por apellido y año sin
DOI (Wooster 2003, Reath 2018/2019, AVTOD, los ATBD instrumentales). **Cada ancla del mapa
es un texto verbatim que el script exige que siga existiendo en la síntesis**: si alguien
la reescribe, el script lo reporta en `coverage.missing_anchors` en vez de dejar el número
caer en silencio (A87).

> **Por qué no se dejó todo automático.** Se probó primero el match por trigramas del
> título y falla en las dos direcciones: la frase «thermal remote sensing» hacía matchear
> el paper de Klyuchevskoy contra la sección de Coppola 2019 (falso positivo), y los
> papers citados por apellido+año quedaban fuera (falso negativo). Un porcentaje construido
> sobre eso no es auditable. Hay además tres documentos que la síntesis **nombra sin
> sintetizar** —el PDF mal extraído del cap. 11 y los dos ATBD de nube que quedaron
> señalados como pendientes en §5— y que están declarados explícitamente en `NOT_COVERED`
> con su razón: mencionar no es sintetizar, y contarlos habría inflado la cifra sin que
> nadie leyera nada.

**Actualizado en**: `docs/RESEARCH_WORKFLOW.md:21` y `docs/REAUDITORIA_S52.md:150`, los dos
apuntando ahora al script en vez de a un número fijo.

> ⚠️ **Tercer lugar, fuera de mi alcance de edición**: `CLAUDE.md:51` (instrucciones
> vinculantes del proyecto) todavía dice *"Creado S13 (2026-04-18). Cobertura **30/60 PDFs
> (54%)**"*. Reemplazo sugerido: *"Creado S13 (2026-04-18), cobertura re-medida S128:
> **46/70 documentos distintos (65,7 %)** — el número lo produce
> `scripts/audit_corpus_documentacion.py`, no se transcribe a mano."*

### Los 21 documentos sin sintetizar

Vale mirarlos porque cuatro tocan frentes abiertos de S128:

| documento | por qué importa |
|---|---|
| `Platnick_MODIS_MOD06_ATBD.pdf` · `Frey_2008_MODIS_CloudMask_Collection5.pdf` | **frente #4 (filtrado de nube)** — son los ATBD que el gap pedía, y estaban confundidos con el producto de inundaciones |
| `s41561-021-00705-4.pdf` (Girona et al. 2021, Nature Geosci) | **frente #8** — el «unrest térmico de gran escala» contra el que hay que leer nuestro «artefacto topográfico» |
| `j.jvolgeores.2012.09.005.pdf` (Coppola et al. 2013, *Rheological control on the radiant density*) | es la fuente del `c_rad` que la síntesis usa en §3 citando a Galetto |
| `The_Capabilities_of_FY-3DMERSI-II_Sensor_to_Detect.pdf` (Aveni, Laiolo, Campus, Massimetti, Coppola 2023) | canon MIROVA calibrando k_MIR en un sensor nuevo — el molde metodológico |
| `rs11131528.pdf` (MOUNTS), `rs12193232.pdf` (NHI), `Volcanic_Anomalies_Monitoring_System_VOLCANOMS_a_L.pdf` | los tres aparecen **sólo como fila de tabla** de sistemas competidores, sin síntesis |
| resto (11) | Bernstein/Pallister Chaitén, Fan cirrus, Mannini GRL, Corradino Annals, infrasonido Yasur, cap. 9 del libro, Coppola 2009 Piton, Klyuchevskoy, USGS SIR, VNP14, dos ATBD JPSS |

La lista completa con evidencia está en `corpus_inventory.json` → `uncovered`.

---

## 5 · Redundantes — **NO SE BORRÓ NADA**

**8 grupos de archivos byte-idénticos, 101,9 MB recuperables** sobre 649,1 MB de corpus.
El reporte previo decía «~76 MB»: el conteo de archivos era correcto, la cifra de MB estaba
**26 MB baja**.

| canónico propuesto | duplicado a eliminar | md5 (compartido) | bytes c/u | MB recup. |
|---|---|---|---|---|
| `feart-12-1345104.pdf` | `SaundersShultz_2024_HotLINK.pdf` | `0ad57d0443202fc7f23a34e64b7beb21` | 47.249.796 | 47,2 |
| `Aveni_2024_TIRVolcH_RSE.pdf` | `1-s2.0-S0034425724004140-main.pdf` | `ab8addd8fd284cccc195dbbb1e8656ae` | 26.807.091 | 26,8 |
| `rs11131528.pdf` | `Valade_2019_MOUNTS_AI.pdf` | `3c001f28341c185188bd289311331eeb` | 10.908.310 | 10,9 |
| `campus2022_sensors_22_1713.pdf` | `The_Transition_from_MODIS_to_VIIRS_for_Global_Volc.pdf` | `877d18485125b6ecdf050664b7b0ecdf` | 8.357.087 | 8,4 |
| `feart-11-1240107.pdf` | `Coppola_2023_GlobalRadiantFlux_MIROVA.pdf` | `191b64649bbb7fcc0d096e20d39f0cbd` | 5.131.092 | 5,1 |
| `AVTOD_Reath_2019.pdf` | `1-s2.0-S0377027318304165-main.pdf` | `ff4d2d4e3169568f07314f914257f829` | 3.196.682 | 3,2 |
| `Aveni_2024_TIRVolcH_RSE.md` | `1-s2.0-S0034425724004140-main.md` | `bd963fe92dad274b6d93e7b99a861915` | 167.109 | 0,2 |
| `coppola2023_frontiers.md` | `Coppola_2023_GlobalRadiantFlux_MIROVA.md` | `12e5230e55bee518e4b4ef00a7b93afd` | 80.888 | 0,1 |

**Criterio para elegir el canónico**: se conserva **el nombre que ya está referenciado en
docs del repo**, para que borrar el otro no rompa ninguna cita. Conteo de archivos `.md`
que nombran cada variante (excluyendo `docs/s128/`, que es este mismo informe):

| par | refs al canónico | refs al duplicado | dónde |
|---|---|---|---|
| HotLINK | `feart-12-1345104` → **1** | `SaundersShultz_2024_HotLINK` → **0** | la única cita está en **`CLAUDE.md:64`**, archivo de instrucciones vinculantes |
| Aveni TIRVolcH `.pdf` | `Aveni_2024_TIRVolcH_RSE` → **4** | `1-s2.0-S0034425724004140-main` → **4** | **empate.** Ver nota abajo |
| MOUNTS | `rs11131528` → **4** | `Valade_2019_MOUNTS_AI` → **2** | |
| Campus 2022 | `campus2022_sensors_22_1713` → **1** | `The_Transition_from_MODIS_to_VIIRS…` → **0** | la cita es la propia síntesis |
| Coppola 2023 `.pdf` | `feart-11-1240107` → **2** | `Coppola_2023_GlobalRadiantFlux_MIROVA` → **1** | |
| AVTOD | `AVTOD_Reath_2019` → **5** | `1-s2.0-S0377027318304165-main` → **1** | |
| Coppola 2023 `.md` | `coppola2023_frontiers` → **2** | `Coppola_2023_GlobalRadiantFlux_MIROVA.md` → **1** | |

**El par de Aveni TIRVolcH está empatado 4-4** y ahí el criterio no decide: propongo
quedarse con `Aveni_2024_TIRVolcH_RSE.pdf` porque es el nombre por el que un futuro
`grep aveni` lo encuentra (A89: buscar por apellido y obtener cero es cómo se pierden
archivos que sí están), pero eso deja **4 documentos citando el nombre Elsevier**
(`AUDIT_S121_MEJORA_INTEGRAL.md`, `BEYOND_MIROVA_EXTENSIONS.md`, `PAPERS_AUDIT.md`,
`superpowers/specs/2026-05-15-s46-coppola-literal-design.md`) que habría que actualizar en
el mismo commit. Su `.md` extraído tiene el mismo empate y debería seguir la misma suerte.

En unos casos gana el nombre descriptivo y en otros el identificador de editorial. No es
elegante, pero es lo que no rompe nada; **unificar el criterio de nombres es una decisión
aparte** y no se debería mezclar con un borrado.

### Un noveno candidato, que el hash NO detecta

`1-s2.0-S0377027316305248-main.pdf` y `nuevos/laiolo2017.pdf` tienen **exactamente el mismo
tamaño (2.457.763 bytes) pero md5 distinto** (`396c568130…` vs `3f529f9e68…`). Son el mismo
paper —Laiolo et al. 2017, Santa Ana, `10.1016/j.jvolgeores.2017.04.013`— bajado dos veces;
difieren en metadatos embebidos (marca de descarga de Elsevier). Recuperaría 2,4 MB más,
pero **requiere verificación visual antes de tocarlo**: md5 distinto no permite afirmar que
el contenido es idéntico.

### Recomendación

**Ninguna de estas dos listas se ejecuta en esta sesión.** Un borrado masivo (>10 archivos
o >50 MB) exige la regla **A38** del proyecto: inventario clasificatorio → `git tag`
defensivo → confirmación explícita de Nicolás. El inventario ya está hecho (es este
documento más `corpus_inventory.json`); el tag y la confirmación son de él.

Matiz honesto sobre la urgencia: `documentacion/` está en `.gitignore`, así que estos
101,9 MB **no pesan en el repo ni en los checkouts de CI**. Pesan sólo en el disco local,
que está al 98 % con 13 GB libres. Recuperar 102 MB no resuelve un disco al 98 %: es
higiene, no rescate. Si el disco es el problema real, el candidato serio está en otro
lado —`978-3-031-86841-2.pdf` son 93 MB de un libro del que usamos un capítulo que ya está
extraído en texto—, y esa también es decisión de Nicolás.

---

## 6 · Qué quedó pendiente para decisión de Nicolás

1. **Borrar los 8 duplicados** (101,9 MB) siguiendo A38: tag defensivo + confirmación.
   Opcionalmente el noveno par (Laiolo 2017, 2,4 MB) previa verificación visual.
2. **Reconseguir Laiolo et al. 2022 EPSL 588:117726** (`10.1016/j.epsl.2022.117726`).
   Es canon MIROVA y hoy el repo tiene dos archivos que fingen ser ese paper y son la misma
   página de error. Los mirrors OA están bajo Cloudflare; el camino que queda es navegador
   con sesión real o acceso institucional.
3. **Editar `CLAUDE.md:51`** — cobertura «30/60 PDFs (54 %)» → 46/70 (65,7 %). No lo toqué:
   es archivo de configuración/instrucciones del proyecto.
4. **Editar `docs/DATA_SOURCES.md:147`** — MCDWD descrito como «cloud-water mask». Fuera del
   alcance de edición que se me dio; texto de reemplazo propuesto en §1.4.
5. **Los cuatro documentos sin sintetizar que tocan frentes abiertos** (§4): MOD06 + Frey
   2008 para el frente de nube, Girona 2021 para el frente de señal difusa, Coppola 2013
   para `c_rad`.

---

## Archivos tocados en esta sesión

| archivo | qué se hizo |
|---|---|
| `documentacion/cigolini2022_epsl.pdf` | → `cigolini2022_epsl.html.roto` (renombrado, no borrado) |
| `documentacion/laiolo2022_epsl_openvent.md` | → `laiolo2022_epsl_openvent.md.roto` |
| `documentacion/coppola2025_cap11_extracted.pdf` | → `NO_ES_cap11__frontmatter_y_cap1_gravimetria.pdf` |
| `documentacion/BIBLIOGRAPHY_SYNTHESIS.md` | 5 atribuciones + «Di Bella» + autoría SLSTR + descripción MCDWD + bloque de higiene al tope + puntero al texto bueno del cap. 11 + refuerzo de la nota Coppola 2015/2016a |
| `docs/MISSION.md` | lista canónica 12 → **11** papers, con nota; 2 citas internas normalizadas |
| `docs/RESEARCH_WORKFLOW.md` · `docs/REAUDITORIA_S52.md` | cobertura 30/60 (54 %) → 46/70 (65,7 %), apuntando al script |
| `scripts/audit_corpus_documentacion.py` | **nuevo** — mide y persiste el inventario |
| `docs/s128/corpus_inventory.json` | **nuevo** — fuente de verdad numérica |
| `docs/s128/_pdf_page1_cache.json` | **nuevo** — portadas (DOI + encabezado) de los 77 PDFs, cache para no re-extraer |
| `docs/s128/CORPUS_HIGIENE.md` | este informe |
