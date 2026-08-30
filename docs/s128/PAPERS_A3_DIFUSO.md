# A3 · Señal difusa vs foco discreto — Girona, Realmuto & Lundgren (2021)

**Paper**: T. Girona, V. Realmuto, P. Lundgren, *Large-scale thermal unrest of volcanoes for
years prior to eruption*, **Nature Geoscience** 14, 238–241 (2021).
DOI [10.1038/s41561-021-00705-4](https://doi.org/10.1038/s41561-021-00705-4).
PDF local: `documentacion/s41561-021-00705-4.pdf` (6 págs.: 238–241 + Methods sin numerar,
que cito como *PDF p.5* / *PDF p.6*). Afiliación: **JPL/Caltech** — **no es canon MIROVA** (A9);
es un grupo externo cuyo resultado MIROVA sí cita (ver §4).

## Respuesta a la pregunta central

**NO: lo que nosotros llamamos artefacto topográfico NO es lo que ellos llaman señal.** Son
objetos observacionales distintos en las cuatro dimensiones que importan (banda, cola de la
distribución, escala espacial, escala temporal). Pero el paper **sí erosiona la justificación
física** con que cerramos A69/A82, y eso está en §4.

---

## 1. Qué mide y con qué fórmula

Mide **radiancia espectral TIR de la banda 31 de MODIS (10,780–11,280 µm)** del producto L1B
crudo (MOD021KM/MYD021KM + geolocalización MOD03/MYD03) — **no MIR, no producto LST**:
*"this study focuses on band 31 (10.780–11.280 μm) only because it is more sensitive to surface
temperature variations"* … *"we use the level-1B radiance product, instead of land surface
temperature products, because we want to explore the heat flux radiated by volcanic surfaces
using data with little previous processing"* (Methods, PDF p.5).

El observable es la **anomalía mediana** `δT`, construida así (Methods, PDF p.5):

1. Cuadrángulo de 0,30° lat × 0,48° lon centrado en la coordenada GVP (900–1.700 km², N≈900–1.700 px).
2. `L_c,M` = radiancia mediana de los **M = 11 píxeles MÁS FRÍOS** (~18–22 km²) = las partes altas
   del edificio. `L_h,K` = mediana de los K = N−101 restantes = fondo regional.
3. Conversión a temperatura de brillo por Planck invertida, **Eq. (1)**, verbatim (Methods, PDF p.5):
   *"T_x = C2 / (λ ln(1 + C1/(λ⁵ L_x)))"*, con *"C1 = 1.19 × 10−16 m2 W−1; C2 = 1.44 × 10−2 m K−1;
   and λ is the central wavelength of band 31 (11.03 μm)"*.
4. `ΔT_M,K = T_c,M − T_h,K` (siempre **negativo**: la cumbre es más fría).
5. Mediana **diaria** de ΔT, interpolación lineal de huecos.
6. Filtro pasabajos (10× MODWT symlets-8 + mediana móvil de orden 2 años), corrido 1 año → `δT`.

No hay VRP, ni Wooster, ni Stefan-Boltzmann, ni `c_rad`. La magnitud reportada es **grados**.

## 2. Decisiones de diseño — el criterio

- **Por qué la cola FRÍA y no la caliente**: es una elección explícita de contraste con el
  paradigma nuestro: *"This approach contrasts with previous algorithms aimed at detecting the
  emergence of hotspots (that is, pixels that are hotter than the surrounding pixels) associated
  with magma exposure at the surface or fumarolic activity"* (Methods, PDF p.5). Las refs que cita
  ahí (32–39) incluyen MODVOLC y **las dos de MIROVA** (Coppola 2015 SP426; Coppola 2020 Frontiers).
- **Por qué la mediana**: *"The median is the statistical estimator chosen because it minimizes the
  effect of outliers (for example, owing to cloud coverage, pixel mosaicking, geolocation errors,
  or overlap of scan lines)"* (Methods, PDF p.5).
- **Por qué el contraste cumbre−fondo**: tres objetivos declarados — resaltar la variación que
  ocurre en la cumbre y no alrededor; *"to minimize any local/regional atmospheric effect, as well
  as the possible artefacts of jointly combining daytime/nighttime scenes"*; y minimizar artefactos
  de usar dos sensores (Terra/Aqua) (Methods, PDF p.5).
- **Por qué necesitan topografía fuerte** (esto es lo central para nosotros): los volcanes deben
  *"have substantial topography, such that volcano summits are colder than the surroundings owing
  to an altitude effect; this is used by our algorithm to automatically identify cloud-free
  scenes"* (p.238).

## 3. Cómo tratan topografía, nieve y estacionalidad (lo que veníamos a buscar)

**No corrigen la topografía: la usan como instrumento.** El gradiente de altitud es un ordenador
determinista de la escena; si el píxel más frío no cae en el área auxiliar `A_aux` donde
históricamente cae, la escena tiene nube o inversión térmica y **se descarta**. Es un filtro de
nube puramente geométrico-estadístico, sin banda de nube ni umbral radiométrico, y es brutal:
*"This approach yields a percentage of scenes discarded between ~62% for Ruapehu and ~84% for
Calbuco"* (Methods, PDF p.5). Nótese que también descarta *"days with temperature inversion (that
is, if the mountain is warmer than the surroundings due to atmospheric conditions)"* — es decir,
las noches en que el valle deja de ser más tibio que la cumbre son, para ellos, basura.

**La nieve no se enmascara**: es parte del emisor. El mecanismo propuesto incluye
*"slightly warming the soil and snow cover over extensive areas of the volcanic flanks"* (p.240).

**La estacionalidad no se modela: se filtra.** El ciclo anual queda dentro de `ΔT_M,K(t)` y lo
elimina el pasabajos, cuyo diseño se calibró con >100.000 experimentos Monte Carlo. Los límites
son explícitos: *"For imposed periods Timp ≲6–7 years, our filtering method cannot accurately
retrieve long-term trends independently of the SNR"* y *"When our filtering process is applied to a
synthetic signal without an imposed trend (or with very low SNR), a spurious trend can be
retrieved"* (Methods, PDF p.6).

**Escala y amplitud**: años (>1 año; rampas de 2–7 años), decenas de km² (M=11 px ≈ 20 km²),
amplitud pre-eruptiva **0,20–0,82 °C** (Tabla 1, p.239): Ontake 0,72; Calbuco 0,32; Redoubt 0,47;
Pico do Fogo 0,82. Usan escenas **diurnas y nocturnas juntas** (Methods, PDF p.5).

**¿Cae en nuestro régimen sub-MW?** Sí, y ahí está la trampa numérica. Si uno pasara un
calentamiento uniforme de 0,1–1,0 K a 270 K por nuestra fórmula Wooster MIR
(`VRP = 18,9 · A_pix · ΔL`, λ=3,959 µm, píxel MODIS 1 km²) daría **0,017–0,17 MW/píxel** —
exactamente el rango 0,04–0,06 MW que llamamos artefacto. En Stefan-Boltzmann, 0,5 K sobre
20 km² son ~45 MW integrados. *(Cálculo propio con Planck y σ=5,67e-8; no está en el paper.)*
Es decir: **la magnitud no discrimina** — coherente con A83.

## 4. En qué nos contradice

**No nos contradice en la clasificación operacional**, por cuatro diferencias verificables:

| eje | Girona 2021 | VRP Chile (verificado) |
|---|---|---|
| banda | TIR b31 11 µm | MIR (I04/M13/B21-22) para detección y VRP |
| cola de la distribución | 11 píxeles **más fríos** | percentiles siempre del lado caliente (`process_modis.py:550` p95; `detect_tirvolch.py:308` p99,95) |
| escala temporal | mediana diaria + filtro de años | **por pasada**; `grep -rni "detrend\|wavelet\|seasonal\|rolling" pipeline/*.py` → **cero** |
| objeto | difuso de edificio (~20 km²) | píxel/clúster anómalo |

Además **descartan explícitamente** que su señal sean focos discretos: *"the pre-eruptive variations
of δT_I reflect the emergence of small-scale (<1 km2) volcano-related hotspots (that is, lava domes
or fumaroles). This is not feasible because gradual, long-term δT_I variations reflect gradual shifts
of the radiant temperature distribution of the ground"* (p.240). Y el canon MIROVA ya leyó este paper
y lo dejó **fuera de scope a propósito**: Coppola 2024 cap. Springer lo cataloga como
*"very low-temperature VTFs (~ambient temperature): diffuse heat emissions at the spatial scale of a
crater (Mannini et al. 2019) or entire volcanic edifice (Girona et al. 2021; Chan et al. 2021), with
anomalies of up to a few °C above the background"* y acto seguido dice *"in this work I will focus on
the application of remote sensing techniques to track the appearance and evolution of the first two
groups of VTFs"* (`documentacion/coppola2024_chapter.txt`, BOOK_PAGE=326). **Para el clon literal,
no hacer nada con esto es la conducta fiel.**

**Sí nos contradice en la justificación física de A69.** A69 dice que el gradiente altitudinal
nocturno es ruido a cancelar. Girona muestra que, sobre años, parte del campo térmico difuso de
flanco *puede ser volcánico* — y su caso testigo es **Calbuco, Chile, 2015** (0,32 °C, rampa de
7 años, sin deformación detectada). Nuestro corolario A82 («el foco sub-píxel y el gradiente
topográfico son el mismo objeto a 1 km») queda intacto como afirmación sobre **medibilidad por
pasada**, pero no como afirmación sobre **ontología**. Redacción honesta: «no resoluble por pasada
en MIR», no «físicamente inexistente». Nada de esto pide tocar el pipeline; pide corregir el texto
de A69/A82 y —si algún día se abre un frente *beyond MIROVA*— saber que el observable correcto es
**otro** (TIR, cola fría, años), no un umbral distinto sobre el mismo dato.

**Otros frentes nuestros que toca**: #4 filtro de nube — su test es puramente geométrico
(«¿el píxel más frío está donde siempre?»), barato de portar y ortogonal a la máscara que apagamos
en S127, aunque descartar 62–84 % de escenas es inaceptable para NRT; #6 agregación temporal —
usan **mediana diaria**, no máximo diario como MIROVA (Laiolo 2026), y dicen por qué (robustez a
outliers día/noche): el estadístico correcto depende del objeto, no es una preferencia de gusto.

## 5. Qué cita que no tenemos (con DOI)

- **Chan, Konstantinou & Blackett (2021)**, *Spatio-temporal surface temperature variations … at
  Merapi*, JVGR 420:107405 — [10.1016/j.jvolgeores.2021.107405](https://doi.org/10.1016/j.jvolgeores.2021.107405).
  (Vía Coppola 2024; el "gemelo" de Girona y la otra mitad de la categoría VTF ~ambiente.)
- **Wenny et al. (2013)**, *Long-term band-to-band calibration stability of MODIS thermal emissive
  bands*, SPIE 8724:872412 — [10.1117/12.2015807](https://doi.org/10.1117/12.2015807). **Relevante
  a nuestro frente #7** (calibración cruzada, deriva entre bandas y entre Terra/Aqua).
- **Caudron et al. (2019)**, *Change in seismic attenuation as a long-term precursor of gas-driven
  eruptions*, Geology 47:632 — [10.1130/G46107.1](https://doi.org/10.1130/G46107.1).
- **Lundgren et al. (2020)**, *The dynamics of large silicic systems … Domuyo*, Sci. Rep. 10:11642 —
  [10.1038/s41598-020-67982-8](https://doi.org/10.1038/s41598-020-67982-8).
- **Wright et al. (2004)**, MODVOLC, JVGR 135:29 — [10.1016/j.jvolgeores.2003.12.008](https://doi.org/10.1016/j.jvolgeores.2003.12.008).
- **Reath et al. (2016)**, JVGR 321:18 — [10.1016/j.jvolgeores.2016.04.027](https://doi.org/10.1016/j.jvolgeores.2016.04.027).
- **Li et al. (2013)**, *Satellite-derived LST: current status and perspectives*, RSE 131:14 —
  [10.1016/j.rse.2012.12.008](https://doi.org/10.1016/j.rse.2012.12.008).
- **Mannini, Harris & Jessop (2019)** ya lo tenemos (`documentacion/Geophysical Research Letters -
  2019 - Mannini …pdf`) — conviene leerlo junto a este.

## 6. Qué NO dice (contra lo que se le podría atribuir)

- **No dice que se pueda detectar unrest térmico difuso en una pasada, ni en un mes.** Su método
  *no puede*: períodos ≲6–7 años son irrecuperables (Methods, PDF p.6), hay 55 % de huecos diarios
  en el peor caso (Calbuco) y el filtro mete ~1 año de retardo que corrigen a mano.
- **No dice que su señal sea magmática.** Dice hidrotermal, y en condicional: *"Pre-eruptive
  variations of the radiant characteristics of volcano surfaces **probably** reflect subsurface
  hydrothermal activity"* (p.240), con cambios de emisividad y humedad de suelo como alternativa viva.
- **No dice que sirva como predictor operacional.** n=5 volcanes elegidos *ex post* por erupción
  conocida y por aplicabilidad del algoritmo; no hay tasa de falsa alarma. La probabilidad de
  Fig. 1f es sólo contra ruido sintético, no contra volcanes que no erupcionaron.
- **No dice nada sobre VRP, MIR ni umbrales de detección.** Leerlo como aval de un umbral nuestro
  sería extrapolación.
- **No valida su señal contra MIROVA ni contra ningún catálogo de hotspots.**

---

*Verificaciones propias (A48)*: `pipeline/test1_integrated.py:317` (`compute_test1_mir` recibe `bt`
MIR); `pipeline/process_modis.py:675` y `pipeline/process_viirs_mod.py:665` importan **sólo**
`compute_test1_mir` (`ENABLE_TEST1_NTI_INTEGRAL` default `False`, `pipeline/profile.py:283`);
`grep -rni "detrend\|wavelet\|seasonal\|long_term\|rolling" pipeline/*.py` → sin resultados;
percentiles del lado caliente en `process_modis.py:550`, `process_viirs.py:920`,
`process_viirs_mod.py:532`, `detect_tirvolch.py:308`.
