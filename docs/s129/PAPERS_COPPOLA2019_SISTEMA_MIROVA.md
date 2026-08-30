# Coppola et al. 2020 — *Thermal Remote Sensing for Global Volcano Monitoring: Experiences From the MIROVA System*

**Front. Earth Sci. 7:362 · doi 10.3389/feart.2019.00362** (recibido 17-sep-2019, publicado
27-ene-2020). Fuente leída: `documentacion/coppola2019_frontiers.md` (texto extraído del PDF de
21 páginas; las páginas citadas son las del PDF) + `documentacion/coppola2019_supp_datasheet.md`
(APPENDIX) + `Coppola_2019_supp_Table1.xlsx` / `Table2.xlsx`.

Es **la descripción del sistema que clonamos**. Delega el detalle numérico en SP426.5 ("*the
downloaded granules are then processed following several steps fully described in Coppola et al.
(2016a)*", p. 3), pero en sus tres páginas de método dice cosas que el paper de 2016 no dice —
y que nos contradicen.

> ⚠️ **Trampa de nomenclatura.** En ESTE paper, `Coppola et al. 2016b` = SP426.5 (doi
> 10.1144/sp426.5), el que nosotros llamamos "Coppola 2016a"; y `Coppola et al. 2016a` = Nyamulagira
> lava lake (Bull. Volcanol., doi 10.1007/s00445-016-1014-7). El cuerpo del texto los intercambia
> (le atribuye a "2016a" tanto la cadena de proceso como el ETI, que son de SP426.5). Cuando este
> paper cita "Coppola 2016b", es nuestro SP426.5.

---

## 1. La cadena de procesamiento, paso por paso (verbatim)

1. **Descarga.** L1B radiancias calibradas desde LANCE, latencia <3 h; barrido de las carpetas
   remotas **cada 5 minutos** (p. 3). Volumen: "*about 25 Gb per day*" (p. 3) para 216 volcanes.
2. **Selección de objetivos.** No es global: "*the data processing chain actually operates only for
   a list of selected target volcanoes*" (p. 3), tomada del catálogo Holoceno del GVP con un
   *operational flag*; los volcanes llevan el número identificador del GVP.
3. **Bandas.** "*the original spectral radiance data (recorded by MODIS in the Middle Infrared
   [MIR] at 3.959 µm and Thermal Infrared [TIR] at 12.02 µm)*" (p. 3). **12,02 µm = banda 32**,
   no la 31.
4. **Remuestreo.** "*…are resampled in regular grids of 50 × 50 km (in UTM coordinates)*" (p. 3).
   No dice interpolador, no dice tamaño de celda acá (SP426.5 lo fija en 1 km), y no dice a qué
   punto ancla la grilla más allá de que es una por volcán.
5. **Detección.** "*the MIROVA algorithm uses the middle infrared MIR bands at 3.959 µm and thermal
   TIR at 12.02 µm to calculate different spectral indices (such as the Normalized Thermal Index –
   NTI, Wright et al., 2004, and the Enhanced Thermal Index – ETI, Coppola et al., 2016a)*", más
   "*a series of spatial operations [that] allow us to highlight the pixels having these indices in
   excess with respect to their surroundings, thus constituting a hybrid and contextual approach*"
   (p. 3). El NTI se atribuye a **Wright et al. 2004 (MODVOLC)**, no a Wright 2002.
6. **Magnitud.** `VRP = 18.9 · A_pixel · Σ_{i=1..npix} (L_MIR,alert − L_MIR,bk)_i` (p. 3), "*where
   npix is the number of alerted pixels, L_MIR,alert is the pixel integrated MIR radiance of the ith
   alerted pixel, L_MIR,bk is the MIR radiance of the background (average radiance of pixels
   surrounding the anomaly), A_pixel is the pixel size (1 km² for the resampled MODIS pixels)*"
   (p. 3). Incertidumbre declarada: "*returns the VRP with an error of ± 30%*" (p. 3), sobre
   superficies con "*T > 500 K*".
7. **Publicación.** Cuatro salidas por volcán, actualizadas "*approximately four times per day
   (according to the number of MODIS overpasses)*", online 1–4 h post-adquisición (p. 4): últimas
   10 imágenes NTI, serie VRP, distancia a la cumbre y superposición Google Earth.
   **La agregación es por pasada**: "*Each stem represents a single detection (one MODIS passage)*"
   (p. 4).

**Lo que la cadena NO tiene**, declarado explícitamente: "*It is however important to emphasize
that the VRP and the color code provided by MIROVA are not corrected automatically for the
acquisition conditions (i.e., clouds/geometry) but they simply represent a measurement of the
thermal radiation reaching the sensor*" (p. 4). Y en la sección de límites, cuantificar nube y
geometría "*is currently absent in all the operational systems*" (p. 15). **No hay máscara de nube,
no hay filtro de ángulo cenital, no hay corrección topográfica.** El zenit y el azimut se **muestran**
al operador "*in order to permit a quick evaluation of the viewing geometry conditions*" (p. 4):
son metadato para el humano, no un gate del algoritmo.

---

## 2. Divergencias, por impacto

| # | Qué dice el paper | Qué hacemos | Verificado con |
|---|---|---|---|
| **1** | TIR del NTI = **12,02 µm** (B32), p. 3 | B31 (11,03 µm) | `pipeline/process_modis.py:76` `BAND31_LAMBDA = 11.03`; `:249` `band31 = calibrate(...)  # E3: TIR for NTI` |
| **2** | Remuestreo a **grilla regular UTM 50×50 km**, p. 3 | swath crudo | `VRP_PROFILE=mirova_equivalent python -c "import pipeline.profile as p; print(p.ENABLE_UTM_REGRID)"` → `False` |
| **3** | VRP = **suma sobre todos los píxeles alertados**, sin selección de clúster, p. 3 | publicamos `primary_cluster.vrp_mw` | `ENABLE_SUM_VRP_REPORTING = False` (mismo comando); `pipeline/store.py:520` |
| **4** | `L_MIR,bk` = "*average radiance of pixels **surrounding the anomaly***", p. 3 | anillo global 5–25 km salvo 5 volcanes opt-in | `BG_INNER_KM=5.0` / `BG_OUTER_KM=25.0`; parse de `volcanoes.yaml` → `local_kernel_bg ON: ['PuyehueCordonCaulle','Villarrica','Chaiten','PlanchonPeteroa','Lastarria']` |
| **5** | Proximal/distal con **5 km uniforme**, p. 4 | `inner_radius_km` 3–20 por volcán | `grep inner_radius_km volcanoes.yaml` |
| **6** | Distancia = "*the distance from the **farthest hot pixel** to the summit*", p. 4 | distancia del hotspot final (clúster) | `pipeline/store.py:515` documenta `hotspot_dist_km_furthest`, pero su flag está OFF (ver #3) |
| **7** | 4 pasadas/día, **sin distinción día/noche** en todo el paper | sólo noche | `ENABLE_DAYTIME_MODIS = False` |
| **8** | MIROVA en 2020 es **sólo MODIS**; VIIRS "*constitutes a relatively simple step to implement*", aún no hecho (p. 16) | 3 sensores | — |

Las divergencias 1 a 4 tocan directamente el número que publicamos. La #4 es la que más rinde:
nuestro anillo 5–25 km no es "los píxeles que rodean la anomalía", y el fondo autorreferente que
S126 identificó es consecuencia directa de esa distancia.

---

## 3. Los frentes abiertos, uno por uno

**1 · Piso VRP.** El paper **no declara ningún piso**, y hay que leer el párrafo entero porque en
dos líneas dice las dos cosas: "*As a whole MIROVA may detect thermal anomalies with VRP spanning
from **less than ~1 MW** to about ~50 GW. According to the Stephan-Boltzmann's law, **the lower
detection limit (1 MW)** would correspond to two end-member cases: (i) a hot case characterized by a
vent of ~7 m² and a temperature of 1000°C, or (ii) a cold case characterized by a fumarole field
having an area of ~143 m² and a temperature of 300°C*" (p. 3). Es decir: 1 MW es una **escala de
sensibilidad nominal**, ilustrada con dos casos físicos, no un umbral operacional — el sistema
entrega valores por debajo. **Esto no autoriza un piso duro.** Dato nuestro: el 53,2 % de los 33.448
records con VRP>0 están bajo 1 MW, y los pisos por sensor (`MIN_VRP_MW_MODIS=0.05`, `V375=0.02`,
`V750=0.15`) ya anulan 1.631 records, **todos VIIRS, ninguno MODIS** (conteo sobre
`data/mirova_equivalent/*.json`). El paper no respalda esos pisos ni los prohíbe: los ignora.

**2 · Fondo local vs regional.** El paper es local: "*pixels surrounding the anomaly*" (p. 3).
"*Surrounding*" además implica que el fondo no incluye la anomalía. Es la lectura de Coppola 2016a
Eq. 6 y de Aveni 2023 Eq. 3, dicha otra vez y en el paper del sistema.

**3 · Geometría de grilla.** Zanjado: grilla UTM regular de 50×50 km, con `A_pixel = 1 km²`
constante y declarado como tal dentro de la propia ecuación de VRP — el área fija no es una
aproximación nuestra, es el sustrato del cálculo. Nuestro `regrid.py` ya cita esta línea en su
cabecera; falta encenderlo. Nota fina: el paper dice **50×50** y nuestro `half_km` por defecto es
25,5 (51×51, tomado de SP426.5).

**4 · Nube.** Contestado, y en contra de enmascarar: MIROVA no corrige ni enmascara (p. 4), y el
paper advierte del daño de hacerlo mal: "*in many cases thermal anomalies within high-altitude
summit craters may be discarded or classified as strongly attenuated, because the surroundings
pixels are cloudy (although the crater is actually without cloud cover)*" (p. 15). Eso es
exactamente nuestro D14 y las 181 noches ciegas. **La decisión S127 de apagar la máscara queda
respaldada por el paper del sistema.**

**5 · NTI.** Origen atribuido acá a **Wright et al. 2004** (MODVOLC, doi
10.1016/j.jvolgeores.2003.12.008), no a Wright 2002. SP426.5 dice 2002. Tenemos el 2002; **no
tenemos el 2004**.

**6 · Agregación temporal.** El paper dice **por pasada**, no máximo diario (p. 4). El máximo diario
aparece en literatura posterior; en 2020 la serie publicada es un *stem* por pasada de MODIS.
Nuestra elección coincide con el sistema tal como está descrito acá.

**7 · Saturación.** Sólo el canal MIR dual low/high gain "*providing an extended range of
unsaturated data*" (p. 3). Nada operacional.

**8 · Señal difusa.** El paper no la nombra. Lo más cercano son los falsos positivos, "*generally
comprised between 0 and 3% (number of false alerts/number of MODIS overpasses)*" (p. 14), que
"*depend on the regional and local environmental conditions as climate, elevation, topography and
land cover type*" — atribuidos a Coppola et al. 2016b = SP426.5. Es el orden de magnitud contra el
que corresponde medir nuestro artefacto topográfico: **0–3 % de las pasadas, no de las detecciones.**

**9 · Incertidumbre.** El **± 30 %** que le atribuimos a Laiolo 2026 está acá desde 2020 (p. 3), con
la misma condición (`T > 500 K`). Nuestra banda de paridad [0,5–2,0] es mucho más laxa que el ±30 %
que el propio sistema se declara.

---

## 4. Qué NO dice, contra lo que se le atribuye

- **No dice nada de bow-tie.** Ese paso está en SP426.5, no acá.
- **No dice que sea nocturno.** La palabra *night* no aparece en el cuerpo del método; las cuatro
  pasadas diarias de Terra+Aqua incluyen las diurnas.
- **No filtra por ángulo cenital.** Lo muestra al operador; no lo usa como gate. Los 40°/50° de la
  tesis de Massimetti y el ≤40° de Aveni 2023 **no vienen de MIROVA-el-sistema**.
- **No corrige topografía**: la remite a "*case by case correction models (Zakšek et al., 2017)*"
  como pendiente (p. 15).
- **No calcula TADR en la cadena**: es producto de segundo nivel, "*subject to a calibration of the
  conversion factors*" (p. 9), que hace el usuario. Confirma que no tener `c_rad` no es un gap.
- **No hay tabla de parámetros por volcán.** El APPENDIX son las 17 encuestas a observatorios;
  `Table S1` es el catálogo de sistemas competidores (18 filas: HOTVOLC, MODVOLC, RSTvolc, FIRMS,
  MOUNTS…, con MIROVA como "UNITO / MODIS / MIR,TIR / ~1 km / 6-12 h"); `Table S2` son los
  observatorios usuarios. **Chile: SERNAGEOMIN, 99 volcanes holocenos, 15 objetivos MIROVA.**
- Dato para la misión: la respuesta de OVDAS (Claudia Bucarey, 23-10-2018) a la pregunta 11 dice
  "*Now we are interested in start a local system of satellite thermal monitoring and include all the
  monitored volcanoes (45) by OVDAS*" (APPENDIX, p. 4). Y el propio paper contempla la figura:
  "*the development of 5 or 6 local systems (MIROVA clones), hosted by respective volcanological
  observatories*" (p. 18). VRP Chile es, literalmente, la respuesta que este paper pide.

## 5. Citas que no tenemos (con DOI)

- **Wright, R. et al. (2004)** *MODVOLC*, JVGR 135, 29–49 — doi 10.1016/j.jvolgeores.2003.12.008.
  **Es la fuente del NTI según este paper.** Prioridad alta.
- **Koeppen, W. C., Pilger, E., Wright, R. (2011)** Bull. Volcanol. 73, 577–593 —
  doi 10.1007/s00445-010-0427-y. Atenuación de nube píxel a píxel, la "solución ideal" que MIROVA
  descarta por costo (p. 15). Relevante al frente 4.
- **Blackett, M. (2015)** MODIS vs VIIRS, RSE 171, 75–82 — doi 10.1016/j.rse.2015.10.002. El
  argumento de por qué VIIRS admite "*direct application of the algorithms behind MIROVA*" (p. 16).
- **Zakšek, K., Pick, L., Coppola, D., Hort, M. (2017)** EGU 19, EGU2017-12016. Topografía sobre
  cuantificación de flujos de lava — sólo abstract.
- **Coppola, D. et al. (2016a)** *Birth of a lava lake: Nyamulagira 2011-2015* — doi
  10.1007/s00445-016-1014-7.
