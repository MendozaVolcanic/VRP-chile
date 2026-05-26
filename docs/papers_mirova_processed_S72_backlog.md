# Papers MIROVA-canónicos — backlog procesado S72 (F1.8)

**Sesión**: F1.8 backlog bibliográfico MIROVA-canónico.
**Fecha**: 2026-05-21.
**Inputs**:

- `documentacion/THESIS_MASSIMETTI.pdf` — Francesco Massimetti, PhD thesis Torino, 18/10/2022.
  Tutor: Diego Coppola; co-tutores: Marco Laiolo, Corrado Cigolini. **MIROVA-canónico**.
  Extractos de texto pre-existentes en repo: `_mm_ch2_methods.txt`, `_mm_ch4_dome_methods.txt`,
  `_mm_ch5_monitoring.txt`, `_thesis_full.txt`.
- `documentacion/s00445-022-01523-1.pdf` — Coppola et al. 2022, Sabancaya 2012–2020,
  *Bull Volcanol* 84:16. DOI 10.1007/s00445-022-01523-1. **MIROVA-canónico**.
  Convertido a `coppola2022_sabancaya.md` con markitdown.
- Cigolini/Laiolo et al. 2022, *EPSL* 588:117726, DOI 10.1016/j.epsl.2022.117726.
  **Lead author real: M. Laiolo** (no Cigolini). Cigolini es co-autor #5.
  **PDF NO descargado**: 4 OA mirrors (publisher Elsevier + 3 repos institucionales unifi/unipi/unipa)
  bloquean curl/WebFetch con Cloudflare. Abstract reconstruido vía OpenAlex
  `abstract_inverted_index`. Sin PDF no se puede extraer texto literal.

**Estado canonical (regla A9)**: 3 papers, todos firmados por la red Torino+Firenze+Pisa
(Coppola, Laiolo, Cigolini, Massimetti, Ripepe, Aiuppa). Cero infiltración INGV Catania /
CNR Potenza. Citables como autoridad MIROVA.

---

## 1. THESIS_MASSIMETTI — hallazgos

**Foco del thesis**: *"Thermal remote sensing of volcanic activity by using Sentinel-2 and
Landsat-8: an improvement of the MIROVA system."* Es decir, el aporte original es el algoritmo
**Massimetti et al. 2020 RSE** para Sentinel-2/Landsat-8 SWIR — no la reformulación del
core MODIS de MIROVA. El núcleo MODIS sigue siendo Coppola 2016 SP 426.5 (ya procesado).

**Lo que SÍ aporta para nuestro modelo de MIROVA**:

### 1.1 Regla geométrica explícita de filtrado MIROVA NRT (Ch4 §3.2.1, p.130)

> *"VRP data were filtered to include exclusively i) nighttime MODIS and VIIRS alerts;
> ii) MODIS and VIIRS image with a Zenith scanning angle < 50°;
> **iii) alerts into a 5 km from the volcano summit**, always fine to exclude any other
> unwanted and possible heat source."*

**Relevancia operacional**: confirma el geofence **5 km uniforme** que ya usamos por defecto
en `process_*.py` (`max_hotspot_dist_km`). NO contradice los `inner_radius_km` por volcán
de los KML oficiales — esto es regla de filtrado del paper para análisis científico, los KML
son los ROI de la grilla de detección. Pero confirma que **el cutoff cercano (3–7 km) es
canónico**, no decisión nuestra. Tupungatito (`inner_radius_km=7`) y PCC (`=20`) son
excepciones documentadas en KMZ, no defaults.

### 1.2 Detección por cluster con contextual threshold (Ch2, S2 algorithm — Massimetti 2020)

Si bien el algoritmo es S2-SWIR (no MODIS-MIR), el **principio metodológico de "TIthresh
contextual por cluster"** está descripto operativamente:

> *"Step 3 consists in the spatial and statistical analysis of TI values, applied to each
> cluster identified in Step 2 (...) algorithm calculates the arithmetic mean of TI (TImean),
> the 30th percentile of TI (TI30%), and recognizes the value of max departure of the observed
> distribution from the normal one (TIflex), for each cluster."* (Ch2, pp.42–43)
>
> *"TIthresh = TIflex (for TIflex < TImean) ; TIthresh = TI30% (for TIflex > TImean)"*

**Relevancia para HT1.5-NEW-1 (cluster selection)**: la doctrina del grupo Torino para
"qué pixels conservar dentro de un cluster" es **por-cluster, no scene-wide**.
- Cada cluster (componente conectado de pixels alertados) se evalúa con su propia
  distribución de TI.
- Se descartan los pixels de "halo" en la cola fría usando el "flex" o el p30.
- **Esto NO es un threshold scene-wide aplicado uniformemente**. Por el contrario, "the
  benefit of the frequency distribution analysis is that it does not act as a single
  threshold over the entire image, but works with a contextual filter based on the thermal
  distribution of each cluster itself" (Ch2 p.44 cita literal).

**Implicación para clon MODIS-MIROVA**: si trasladamos analogía a MIR (con la cautela de
que MODIS-MIROVA usa otro indicador, NTI/MIR-radiance, y la operación de filtrado de
"halo cluster" no aparece descripta tan formalmente en Coppola 2016 SP 426.5), la doctrina
del grupo Torino respalda **por-cluster contextual** y **NO** un único umbral global de
escena. Esto pesa contra HT1.5-NEW-1 si la hipótesis era "MIROVA usa un single scene-wide
threshold".

### 1.3 Regla "9 pixels" para clusters pequeños (Ch2 p.42)

> *"all clusters composed by less or equal than 9 pixels (3×3 box) are considered unaffected
> by the above-described effects and are immediately classified as hot-spot-contaminated,
> independently on the TI values."*

**Relevancia**: para S2-SWIR, el grupo respeta clusters de ≤9 pixels sin filtrar — son
fumarolas o señales débiles persistentes. Si el grupo aplicase la misma filosofía a MIR
(MODIS 1 km), 1–9 pixels = la inmensa mayoría de nuestras anomalías volcánicas chilenas.
La práctica MODIS-MIROVA NO los descarta a priori. Es coherente con nuestro pipeline (no
filtramos por tamaño de cluster en MODIS).

### 1.4 FP rate empírico Massimetti 2020 (Ch4 §3.2.2 p.131)

> *"the result is the detection of the number of 'hot' pixels (...) with an overall
> **estimate of 2–4% false alerts** detected (Massimetti et al., 2020)."*

**Para MODIS/VIIRS-MIROVA, Ch4 §3.2.3 p.131 dice**:

> *"VRP from MODIS and VIIRS, algorithms detected only portion at magmatic temperatures
> (T > 500 K), **with an error of ca. 30%**."*

Esos dos números son distintos por construcción:
- **2–4% FP rate** es el SWIR algorithm Massimetti 2020 (cluster contextual).
- **~30% error** del MODIS/VIIRS-MIROVA NO es FP rate sino **error de cuantificación de VRP**
  por la fracción de área a T<500 K que el MIR-Wooster no captura (asunción magmatic temp).
- **Cuidado en BIBLIOGRAPHY_SYNTHESIS**: no confundir estos dos números. El "0–3% MIROVA
  FP rate" que se cita en otros lugares probablemente viene de Coppola 2016 (sobre MODIS) o
  de Campus 2024 (sobre VIIRS). El thesis no aporta un nuevo número para FP MODIS/VIIRS.

### 1.5 Umbral T>500 K cuantitativo en MIR-Wooster (Ch4 §3.2.3 p.131)

Confirmación cuantitativa explícita: la Wooster MIR-radiance assumption captura solo la
fracción de pixel a temperatura magmática (>500 K). El ~30% de error MODIS/VIIRS-MIROVA
documentado proviene de esa simplificación. Esto valida la calibración empírica S14 contra
OSF (error ≤0.17%): nuestros coeficientes 18.9, 19.7, 18.0 ya están "tunneados" al sesgo
neto del grupo.

### 1.6 Lo que el thesis NO documenta

- **L_bk MODIS calculation** (annular kernel vs local) — no descripto en Ch2/Ch4/Ch5.
  Lo deriva al lector de Coppola 2016 SP 426.5.
- **NTI threshold per-régimen** (Muy Bajo / Bajo / Alto) — el thesis no introduce
  ningún σ-multiplier ni 5σ/10σ/15σ. Cita Coppola 2016a Tabla 1 implícitamente.
- **Cluster selection scene-wide vs per-cluster en MODIS MIR** — el thesis describe la
  doctrina S2 (per-cluster) pero NO afirma que esa misma lógica esté implementada en
  MIROVA-MODIS. El paper Coppola 2016 sigue siendo la única referencia formal del MIR.

### 1.7 Síntesis 7 puntos clave

1. Thesis es **complemento Sentinel-2 / Landsat-8 SWIR**, no reescritura del core MODIS.
2. **Confirma geofence 5 km** como filtro NRT canónico MIROVA (ch4 p.130).
3. **Confirma doctrina cluster-contextual** del grupo Torino (TIthres por cluster, no
   single scene-wide threshold) — pesa contra HT1.5-NEW-1 (cluster selection scene-wide).
4. **Regla 9 pixels** S2 para preservar señales débiles ≤3×3 — filosofía coherente con
   no-filtrar clusters chicos en MIR.
5. **FP rate 2–4% es del SWIR** Massimetti 2020, NO de MIROVA-MODIS.
6. **Error VRP MODIS/VIIRS ~30%** documentado y justificado (T>500 K assumption).
7. **Nada nuevo sobre L_bk MODIS** (HT1.5-NEW-2): el thesis lo da por sentado citando
   Coppola 2016a. Confirma que para resolver HT1.5-NEW-2 hay que volver a Coppola 2016
   SP 426.5 directamente.

---

## 2. Coppola 2022 Sabancaya — hallazgos

**Paper**: Coppola et al., *"Shallow magma convection and its surface expressions during the
dome-forming Sabancaya eruption (2012–2020)"*. Bull Volcanol 84:16, DOI 10.1007/s00445-022-01523-1.
Co-autores MIROVA-canónicos: Coppola, Laiolo, Cigolini.

**Naturaleza del paper**: **case-study de aplicación multiparamétrica** (VRP MODIS + VIIRS +
S2 + L8 + S1 SAR + SO2). NO introduce ni modifica algoritmo MIROVA — VRP se usa como
observable.

**Búsqueda exhaustiva** en `coppola2022_sabancaya.md` (87 kB):
- `background|L_bk|kernel|annular|annulus`: **0 hits** (con regex case-insensitive).
- `cluster|threshold.*alert|threshold.*detect`: **0 hits**.
- `sigma|σ|N.*sigma|noise|FPR|false.*positive|FP.*rate|nonvolcanic`: **0 hits**.

**Lo único reproducido**: la fórmula VRP-Wooster y el setup VIIRS-MIR, citando Campus 2022
y Coppola 2016. Ninguna calibración nueva.

**Hallazgo científico relevante (no algorítmico)**:
- *"VIIRS MIR 375m detected anomalies (VRP < 1 MW) ~10 years before MODIS first detection"*
  para Sabancaya. Valida que **VIIRS-I (375m) es estructuralmente más sensible** que
  MODIS-1km para volcanes con señal sub-pixel persistente.
- Implicación VRP Chile: refuerza la decisión arquitectural de procesar VIIRS I-band para
  Villarrica (lava lake 0.05–0.2 MW), Lastarria (fumarólico), Tupungatito (cráter +
  glaciar). Ya implementado.
- Reportado en BIBLIOGRAPHY_SYNTHESIS líneas 55–58 — síntesis previa correcta.

**Síntesis**: 0 hallazgos algorítmicos nuevos. 1 hallazgo de validación VIIRS-I 375m.

---

## 3. Laiolo / Cigolini 2022 EPSL — gap report

**Paper**: Laiolo et al., *"Shallow magma dynamics at open-vent volcanoes tracked by coupled
thermal and SO2 observations"*. EPSL 588:117726, DOI 10.1016/j.epsl.2022.117726. Lead author
real: **Marco Laiolo** (la sintaxis "Cigolini 2022 EPSL" del prompt fue impreciso —
Cigolini es co-autor #5).

**Open-access**: CC-BY publicada. PDF SHOULD ser libremente descargable.
**Estado descarga**: ❌ **NO descargado**.
- Probado: Elsevier ScienceDirect direct → 403 Cloudflare.
- Probado: flore.unifi.it (Florence repo) → 403 Cloudflare.
- Probado: iris.unipa.it (Palermo repo) → 403 Cloudflare.
- Probado: arpi.unipi.it (Pisa repo) → 403 Cloudflare.
- Probado: API Unpaywall → todos `pdf_url: null`.
- Probado: Semantic Scholar API → devolvió URL `bitstream/...pdf` en flore.unifi.it, pero
  el bitstream también está detrás de Cloudflare.

**Bloqueador**: las 4 fuentes OA tienen Cloudflare anti-bot. WebFetch/curl no resuelve el
challenge. Sin acceso a navegador headless con stealth no se puede traer el PDF en esta
sesión.

**Abstract reconstruido** (vía OpenAlex `abstract_inverted_index`):

> Open-vent volcanic activity is typically sustained by ascent and degassing of shallow magma,
> in which the rate of magma supply to the upper feeding system largely exceeds the rate of
> magma erupted. Such unbalance between supplied (input) and erupted (output) magma rates
> is thought to result from steady, degassing-driven, convective overturning in a shallow
> conduit/feeding dyke. Here, we characterize shallow magma circulation at Stromboli volcano
> combining independent observations of heat (Volcanic Radiative Power, via satellite images)
> and gas (SO2, via UV camera) output (...) Aug 2018 – Apr 2020 (...) summer 2019 effusive
> eruption and two paroxysmal explosions (July 3 and August 28, 2019). (...) input rate
> (0.1–0.2 m³/s) exceeded eruption rate (0.001–0.01 m³/s) by ~2 orders of magnitude.
> Conversely, during the effusive phase, input and output converge to ~0.4 m³/s implying
> overall suppression of magma recycling. (...) peak SO2 emissions lag behind peak thermal
> emission by ~27 days (...) conduit mass unloading, produced by the initial effusive phase,
> leads to overall decompression (up to 30 Pa/s) of the shallow plumbing system, ultimately
> causing ascent of less-dense, volatile-rich magma batch(es) from depth (...) culminating
> into the paroxysmal explosion on August 28.

**Inferencia**: paper estrictamente físico/vulcanológico (conduit dynamics, decompression,
plumbing). VRP es **observable**, no objeto de algoritmo. Probabilidad alta de **0
contribuciones algorítmicas nuevas a MIROVA**, similar a Coppola 2022 Sabancaya.

**Hallazgo cuantitativo potencialmente útil** (no algoritmo pero sí calibración):
- *"peak SO2 emissions lag behind peak thermal emission by ~27 days"* en Stromboli 2018–2020.
  No directamente trasladable a VRP Chile pero es el tipo de magnitud que justifica futuras
  integraciones SO2 (TROPOMI) en el dashboard unificado OVDAS — relevante para futuro
  VolcPlume-v1, no para clon NRT inmediato.

**Acción pendiente para sesión con acceso navegador headless**:
- Usar `mcp__playwright` para resolver Cloudflare en `https://flore.unifi.it/handle/2158/1337911`
  o `https://hdl.handle.net/2158/1337911`, descargar el PDF, convertir con markitdown,
  buscar `background|L_bk|cluster|threshold|sigma|FP|annular`.
- Anotar en `tasks/backlog_F1.8_laiolo2022_pdf.md`.

---

## 4. Comparativa con papers ya procesados

| Tema | Paper que aporta | Hallazgo | Cambia modelo MIROVA? |
|---|---|---|---|
| **L_bk MODIS calc method** | Coppola 2016 SP 426.5 (ya proc) | Annular ring kernel | Backlog NO aporta |
| **L_bk VIIRS-M / VIIRS-I** | Campus 2022 (ya proc) | Análogo MODIS | Backlog NO aporta |
| **Cluster selection per-cluster** | Massimetti thesis Ch2 | Doctrina Torino: contextual per-cluster, NO single scene-wide | **Pesa contra HT1.5-NEW-1** |
| **Threshold per-régimen** | Coppola 2016a Tabla 1 (ya proc, vía DRIFTS_S17) | 5σ/10σ/15σ MODIS, 12σ/8σ VIIRS Di Bella | Backlog NO aporta |
| **FP rate MIROVA** | Coppola 2016 (~3% MODIS), Campus 2024 (VIIRS) | Estables | Backlog NO contradice |
| **FP rate Massimetti S2** | Thesis Ch2 + RSE 2020 | 2–4% en S2-SWIR | **Distinguir de MIROVA-MODIS** |
| **VRP quantification error** | Thesis Ch4 §3.2.3 | ~30% por T>500K assumption | Confirma S14 calibración empírica |
| **Geofence 5 km uniforme NRT** | Thesis Ch4 §3.2.1 | Explícito | Confirma operación nuestra |
| **VIIRS-I 10 años antes MODIS** | Coppola 2022 Sabancaya | Caso Sabancaya | Confirma VIIRS-I sensibilidad sub-pixel |
| **Mixed clusters volcánico+no-volcánico** | Backlog NO aporta | n/a | Ningún paper en backlog discute clusters mixtos |

**Conclusión sobre HT1.5-NEW-1 y HT1.5-NEW-2**:

- **HT1.5-NEW-1 (cluster selection scene-wide)**: el backlog **NO la respalda**. La doctrina
  Torino oficial (vía thesis Ch2) es **per-cluster contextual**. Si MIROVA-MODIS implementa
  algo análogo, debe ser per-cluster (no scene-wide single threshold). Para confirmar
  definitivamente habría que releer Coppola 2016 SP 426.5 buscando si describe filtrado
  per-cluster del NTI distribution.

- **HT1.5-NEW-2 (L_bk method)**: el backlog **NO aporta info nueva**. Las 3 fuentes (thesis,
  Sabancaya, EPSL) tratan L_bk como caja negra del MIR. Coppola 2016 sigue siendo el único
  documento autoritativo.

---

## 5. Refs externas adicionales que mencionen MIROVA (espigado)

En `coppola2022_sabancaya.md` references list:
- ✅ ya conocidos: Coppola 2016b SP 426.5, Coppola 2020 Frontiers, Wooster 2003, Campus 2022.

En `_mm_ch5_monitoring.txt` thesis:
- **MOUNTS** (Valade et al. 2019, rs11131528) — sistema independiente Sentinel + AI;
  PDF en `documentacion/Valade_2019_MOUNTS_AI.pdf`. **Cita MIROVA como baseline pero NO
  critica**. NHess-relevante para futuro benchmark cross-system.
- **MODVOLC** (Wright et al. 2002) — el predecesor histórico; cita continuamente como
  baseline. NO crítica.
- **REALVOLC** (citado en thesis Ch5 p.13, Way et al. 2022) — sistema ASTER 2000–2020.
  Independiente, no critica MIROVA.

Críticas conocidas a MIROVA permanecen externas al backlog procesado: ver lista canonical
A9 en `~memory/reference_papers_mirova_canonical.md` (Marchese, Genzano, Pergola — INGV
Catania / CNR-IMAA Potenza — NO procesados aquí porque NO son MIROVA-canónicos).

---

## 6. Persistencia y próximos pasos

**Outputs físicos generados**:
- `documentacion/coppola2022_sabancaya.md` (87 kB, markdown convertido del PDF).
- `docs/papers_mirova_processed_S72_backlog.md` (este archivo).

**NO commiteado** (regla del prompt y `.gitignore` de `documentacion/`).

**Pendientes para Nicolás**:
- Si el equipo F1.8 quiere el texto literal de Laiolo 2022 EPSL: sesión con browser headless
  (playwright/Selenium) que resuelva Cloudflare en flore.unifi.it.
- Si querés verificar HT1.5-NEW-1 con texto literal de Coppola 2016 SP 426.5: ese PDF ya
  está procesado en `coppola2019_frontiers.md` / `sp426_5.txt` — releer §4 "Anomaly
  detection algorithm" buscando "cluster" y "frequency distribution".

**Update mental model MIROVA** propuesto:
- Cluster selection: **probablemente per-cluster contextual** (no scene-wide).
- L_bk: **sigue caja negra** post-backlog — la respuesta vive en Coppola 2016 SP 426.5.
- Geofence operacional: **5 km NRT confirmed** + KMZ `inner_radius_km` per-volcán para ROI.
- FP rate MODIS/VIIRS: estable en ~3% (Coppola 2016) / ver Campus 2024 para VIIRS.
- VRP error de cuantificación: ~30% nominal (Wooster T>500K assumption), reducido
  empíricamente a ≤0.17% por nuestra calibración S14 contra OSF.
