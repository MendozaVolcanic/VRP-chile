# S159, frente «bibliografía y avisos 2025-2026»: inventario de fuentes del grupo MIROVA y avisos de NASA de octubre de 2026

> 2026-10-21. Sólo búsqueda y lectura: no toqué `pipeline/`, `data/`, `frontend/` ni git. Todo lo de este frente vive en
> `C:\vrp-trabajo\s159-pruebas\experiments\_s159\biblio_2026\` (scripts, salidas, PNG) y los PDF descargados en
> `D:\vrp-trabajo\temporales\s159_biblio\` (fuera del repo, por copyright). Disco al terminar: C: 19 GB, D: 12 GB libres.
>
> **Cómo se citó.** Toda cita a un PDF se leyó en la página **renderizada a imagen** (PNG en `png\`, con `render.py`);
> la capa de texto (`ubicar.py`) sólo sirvió para elegir qué página renderizar. Lo que viene de una página web (avisos
> de NASA, resúmenes de EGU, OpenAlex) se marca **(HTML)** y lleva URL y fecha. Lo que no pude abrir se marca **SIN LEER**.
> Lo que heredo de los informes P2 y P3 de hoy se marca **(heredado)** y no lo reverifiqué.

## 0. En una pantalla

1. **Suomi NPP deja de entregar datos el 2 de noviembre de 2026 a las 13:00 UTC** (aviso NASA del 21-oct, LAADS del 6-oct,
   NESDIS del 3-ago). Nuestro pipeline pide `VNP02IMG`/`VNP02MOD` de SNPP como dos de sus seis plataformas VIIRS
   (`pipeline/fetch.py:196-209`, `:797`, `:803`). En doce días la serie `VIIRS_SNPP` y `VIIRS_SNPP_750` se corta y nadie
   recibe un error. Es el hallazgo más grave del frente y no es bibliográfico.
2. **MODIS Colección 6.1, la que pedimos, tiene decomiso anunciado para el 30-sep-2026** (LAADS 199534, 17-mar-2026) y la
   Colección 7 ya corre en paralelo en CMR. Hoy la 6.1 sigue produciendo (último gránulo sobre Chile 2026-10-21 03:15 UTC),
   o sea que la fecha no se ejecutó, pero cuando se ejecute el Standard de MODIS cae en silencio al NRT 6.1.
3. **El hueco del 17 al 20 de octubre es de las colecciones Standard (LAADS), no de CMR ni de los satélites**: las
   colecciones NRT (LANCE) tienen 8 a 11 gránulos por día sobre Chile en esos días; las Standard dan 0 el 18 y el 19 en
   los dos sensores y en las dos colecciones MODIS. **Ningún aviso de NASA lo explica (SIN AVISO)**. El del 12-13 sí tiene
   aviso: «VIIRS Data Product Processing Delay», huecos de nivel 0 en SNPP, JPSS-1 y JPSS-2, activo, resolución TBD.
4. **«Ningún paper describe VIIRS 375» queda matizado, no refutado**: Coppola et al. 2022 (Front. Earth Sci. 10:964372,
   descargado hoy) dice por escrito que el 375 m sigue «the procedure already used for MODIS ... and VIIRS ... at 1 km and
   750 m» (p. 5), sin ningún parámetro; y Aveni et al. 2024 (RSE 315, p. 5 §3.2) da la grilla de VIIRS 375: **134 × 134 UTM
   centrada en la cumbre del GVP, con la geolocalización VNP03IMG corregida por terreno**. Lo que sigue sin fuente son K1,
   C1, C2, la ventana y el segundo pase para 375 m.
5. Dos contradicciones chicas con autoridad: Coppola 2022 da **k_MIR(I04) ≈ 7,16 µm sr** donde Campus 2024 y el OSF dan
   18,0; y el «Campus et al. 2021» que Sabancaya 2022 cita como origen del VIIRS 375 es un **póster de VIIRS 750 m** (M13 y
   M15, Stromboli 2019), que además trae el único diagrama de flujo público del detector de 750 m.
6. Lo nuevo de 2025-2026 que **no está en `documentacion/`**: Aveni, Coppola y Laiolo 2026, RSE 115626 («synergistic
   thermal framework», OA CC BY, 20-ago-2026, sucesor anunciado del capítulo 11), la tesis doctoral de Aveni (Sapienza,
   29-ene-2026) y la versión publicada del Láscar SO2 (JVGR 2026). Ninguna pude abrir (ScienceDirect y IRIS bloquean
   robots; el captcha no se resuelve). El resumen del RSE 2026 no promete nada sobre detección en VIIRS 375 ni MODIS.

---

## 1. Hallazgos, de lo más grave a lo menos grave

### H1. Suomi NPP cesa el 2026-11-02 13:00 UTC y el pipeline pide dos plataformas de SNPP
- **ARCHIVO:LÍNEA**: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\pipeline\fetch.py:196-199`
  (`VIIRS_SNPP_L1B` = `VNP02IMG` v2 y `VNP02IMG_NRT`), `:206-209` (`VNP02MOD`), `:797` y `:803` (las plataformas
  `VIIRS_SNPP` y `VIIRS_SNPP_750` dentro de `all_platforms`). Avisos (HTML, todos leídos el 2026-10-21):
  NASA Earthdata «Reminder: Suomi NPP Observations to Cease on November 2, 2026» (emitido 21-oct-2026, «Active Outage»,
  «13:00 UTC on November 2, 2026 (day 2026/306)», «this date may change»,
  https://www.earthdata.nasa.gov/data/alerts-outages/reminder-suomi-npp-observations-cease-november-2-2026);
  LAADS 199516 «Cessation of Suomi National Polar-orbiting Partnership (S-NPP) data to users on November 02, 2026»
  (6-oct-2026; tabla de reemplazo `VNP02IMG` a `VJ102IMG`/`VJ202IMG`, `VNP03IMG` a `VJ103IMG`/`VJ203IMG`; «will remain
  available from the LAADS archive», https://ladsweb.modaps.eosdis.nasa.gov/alerts-and-issues/199516); LDOPE «SNPP
  Decommission 11/02/2026» (abierto 3-ago, actualizado 7-oct, https://landweb.modaps.eosdis.nasa.gov/displayissue?id=1479);
  NESDIS (3-ago-2026) decía 1-nov; las páginas de NASA pasaron de 1-nov a 2-nov entre agosto y octubre.
- **QUÉ PASA**: el satélite más antiguo de la constelación VIIRS se apaga para ciencia; su I-band (375 m) y M-band
  (750 m) son dos de las seis plataformas con que el pipeline arma las noches. El código no sabe que SNPP se termina: la
  búsqueda de CMR devolverá 0 gránulos y el cortacircuito de hosts (A64) no distingue «no hay más» de «no hubo hoy».
- **CÓMO SE VE EN EL DASHBOARD**: desde el 2-nov desaparecen los puntos `VIIRS_SNPP` y `VIIRS_SNPP_750`; la densidad de
  pasadas nocturnas por noche baja (una de tres plataformas I-band) y una noche que antes cubría SNPP puede quedar sin
  pasada. El operador ve menos detecciones y puede leerlo como que el volcán se calmó. Ningún aviso en pantalla.
- **CÓMO REPRODUCIRLO**: `grep -n "SNPP" pipeline/fetch.py`; `curl -s "https://cmr.earthdata.nasa.gov/search/granules.json?short_name=VNP02IMG&version=2&bounding_box=-76,-46,-66,-17&temporal=2026-11-03T00:00:00Z,2026-11-03T23:59:59Z&page_size=1" -D - | grep CMR-Hits` después del 3-nov.
- **CONFIANZA**: CONFIRMADO (código y tres avisos leídos). La fecha exacta es «subject to change» según NASA.
- **GRAVEDAD**: 4. No tuerce una alerta por sí sola, pero recorta la cobertura del sensor que más publica sin que nadie
  lo vea, y la auditoría por detector (S156) perdería un tercio de su población I-band.

### H2. MODIS Colección 6.1 tiene decomiso anunciado y el pipeline sólo pide 6.1
- **ARCHIVO:LÍNEA**: `pipeline/fetch.py:187-192` (`MOD021KM`/`MYD021KM` `version: "6.1"`, NRT `6.1NRT`); comentario
  `:178`. Aviso LAADS 199534 «Version 7.0 MODIS Calibrated Radiances and Geolocation Data Products: Now Available»
  (17-mar-2026, HTML): la 6.1 «will remain available for the next six months before being decommissioned on
  September 30, 2026» (https://ladsweb.modaps.eosdis.nasa.gov/alerts-and-issues/199534). Medición propia
  `cmr_modis_c61_vs_c7.py` → `cmr_modis_c61_vs_c7_salida.txt`: CMR lista `MOD021KM` en versiones `7`, `6.1` y `6.1NRT`;
  sobre Chile en 2026 la 6.1 tiene 2.423 gránulos (último 2026-10-21T03:15Z) y la 7 tiene 2.426 (último
  2026-10-21T12:45Z); `MOD03` igual.
- **QUÉ PASA**: NASA ya produce la Colección 7 en paralelo (la «final reprocessing» previa al apagado de Terra y Aqua
  «in late 2026/early 2027», aviso «Transition from MODIS to VIIRS», 2-may-2025, HTML). Cuando la 6.1 se decomise de
  verdad, `fetch.py` dejará de encontrar Standard y caerá al NRT 6.1 (`6.1NRT`, LANCE) para todo MODIS, que es el camino
  flaky de A64. Además la geolocalización MOD03 v7 es la que el frente M quiere usar; pedirla en 6.1 es pedir la vieja.
- **CÓMO SE VE EN EL DASHBOARD**: hoy, nada. El día que se ejecute: `product_version` pasa a `nrt` en todos los records
  MODIS y, si LANCE falla, MODIS desaparece de las noches sin error visible.
- **CÓMO REPRODUCIRLO**: `PYTHONIOENCODING=utf-8 python -I experiments\_s159\biblio_2026\cmr_modis_c61_vs_c7.py`.
- **Las dos preguntas**: (1) si la 6.1 hubiera dejado de producirse el 30-sep, el último gránulo 6.1 sería anterior a esa
  fecha: no lo es, luego el decomiso anunciado no se ejecutó; (2) control positivo: la versión 7 devuelve gránulos del
  mismo día y `7.0` devuelve 0 (el identificador correcto es `7`).
- **CONFIANZA**: CONFIRMADO el anuncio, la coexistencia y la configuración del pipeline; SOSPECHA la fecha efectiva del
  decomiso (anunciada y no ejecutada; no encontré un aviso que la postergue).
- **GRAVEDAD**: 3.

### H3. El hueco del 17 al 20 de octubre es de las colecciones Standard; las NRT están; y nadie lo avisó
- **SCRIPT:SALIDA**: `cmr_conteo_chile_oct2026.py` → `cmr_conteo_chile_oct2026_salida.txt` (bbox Chile -76,-46,-66,-17;
  gránulos por día y colección, 8 a 21 de octubre, corrido el 2026-10-21 ~22:00 Chile); `cmr_v7_y_versiones_salida.txt`.
- **QUÉ PASA**: el 18 y el 19 de octubre las colecciones **Standard** dan 0 sobre Chile en `VNP02IMG`, `VJ102IMG`,
  `VJ202IMG`, `MOD021KM` (6.1 y 7), `MYD021KM` y `MOD03`; el 17 y el 20 están a medias (VNP02IMG 5 y 6, MYD021KM 2 y 7).
  Las mismas fechas en las colecciones **NRT** (`*_NRT`, `6.1NRT`) dan 8 a 11 gránulos por día. O sea que los satélites
  observaron y LANCE procesó; lo que falta es la producción Standard de LAADS de esos días, en los dos sensores a la vez.
  El 12 y el 13 son otro fenómeno: `VNP02IMG` y `VJ202IMG` caen a 4 (contra 8 a 11 los días vecinos) y `VJ102IMG` a 5 el
  13, con NOAA-20 el 12 intacto; coincide con el aviso **«VIIRS Data Product Processing Delay»** (emitido 16-oct,
  actualizado 20-oct, «Active Outage», «Gaps in Level 0 SNPP, JPSS1, and JPSS2 VIIRS data between October 12 and 13,
  2026», «The science team is working to fill the gaps», resolución TBD,
  https://www.earthdata.nasa.gov/data/alerts-outages/viirs-data-product-processing-delay). Para el 17 al 20 no hay nada:
  ni en «Data Alerts and Outages», ni en LAADS «Alerts and Issues» (único ítem de octubre: el de SNPP), ni en
  `status.earthdata.nasa.gov` (CMR «No Active Incidents»), ni en las métricas semanales ESDIS del 5 y del 12 de octubre
  (la del 19 no existe, 404), ni en el foro de Earthdata. Lo más cercano: ESDIS 5-oct atribuye gránulos tardíos de
  VIIRS-SNPP-Land del 27-sep y 3-oct a «delays in L0 data», y la migración a «Consolidated Ingest and Archive» del
  28 al 30 de octubre interrumpirá la ingesta en PO.DAAC, ASF DAAC y GES DISC (no nombra LAADS).
- **CÓMO SE VE EN EL DASHBOARD**: si el pipeline corrió esas noches con Standard vacío y NRT disponible, debería tener los
  records con `product_version: "nrt"`; si no los tiene, el camino NRT falló por otra causa (A64: ConnectTimeout del host
  LANCE) y las noches del 18 y 19 quedan como «sin pasada», que el operador no distingue de «no hubo nada».
- **CÓMO REPRODUCIRLO**: `PYTHONIOENCODING=utf-8 python -I experiments\_s159\biblio_2026\cmr_conteo_chile_oct2026.py`.
- **Las dos preguntas**: (1) si CMR no sirviera un día, ese día daría 0 en todas las colecciones; el 18 y 19 dan 0 sólo en
  las Standard y 8 a 11 en las NRT, así que el instrumento ve la diferencia; (2) control positivo: del 8 al 11 todas las
  Standard dan 5 a 11 y las NRT 0 (LANCE retiene unos siete días; el 0 de las NRT antes del 15 es retención, no falla).
  **Lo que no mide**: si el archivo se puede descargar (sólo cuenta lo que CMR lista) ni lo que hizo nuestro cron.
- **CONFIANZA**: CONFIRMADO el conteo y la ausencia de aviso; SOSPECHA la causa del hueco Standard.
- **GRAVEDAD**: 2 (operativo, acotado a cuatro días). Contradice la premisa del encargo: «CMR no sirve Chile del 17 al
  20» vale para las colecciones Standard, no para las NRT.

### H4. Sí hay texto de MIROVA sobre VIIRS 375: declara «el mismo procedimiento» y da la grilla, pero no los umbrales
- **ARCHIVO:LÍNEA**: `D:\vrp-trabajo\temporales\s159_biblio\Coppola_2022_FrontEarthSci_Vulcano_VIIRS_imaging_bands.pdf`
  p. 4-5 (PNG `png\coppola2022_vulcano_p4.png`, `_p5.png`); `documentacion\Aveni_2024_TIRVolcH_RSE.pdf` p. 5 §3.2 y p. 18
  (PNG `png\aveni2024_p5.png`, `_p18.png`). Contra `experiments\_s159\p2\INFORME.md` H1 y §3 (b) («Origen exacto de la
  grilla e interpolador: ninguna fuente lo dice»; Aveni 2024 «ubicada, no renderizada»).
- **QUÉ PASA**: (a) Coppola, Laiolo, Campus y Massimetti 2022, Front. Earth Sci. 10:964372 (Torino, OA CC BY, brief
  report de 9 páginas, el primer uso de banda I por MIROVA según CA22 [103]) dice en Methods: «The data have been
  elaborated by applying the MIROVA algorithm to the VIIRS Imaging Bands, following the procedure already used for MODIS
  (Coppola et al., 2015) and VIIRS (Campus et al., 2022) bands, at 1 km and 750 m resolution, respectively» (p. 4 último
  párrafo a p. 5 primer párrafo). Es la única frase del grupo que ata la detección de 375 m a la de MODIS y 750 m, y lo
  hace por declaración, sin K1, C1, C2, ventana ni segundo pase (`ubicar.py` sobre `NTI|ETI|neighbo|K1|second`: cero).
  (b) Aveni et al. 2024, RSE 315:114388 (Sapienza y Torino) §3.2: «The original granules, as per MIROVA workflow, are
  resampled to a regular 134 × 134 UTM grid centred on the volcano summit according to the coordinates provided by the
  Global Volcanism Program (2023). This step ensures consistency across all the scenes that now cover an area of ~2500
  km²» (p. 5, columna derecha, 2.º párrafo), con los insumos «VNP02IMG and VJ102IMG 6-Min L1B Swath 375 m ...
  atmospherically uncorrected» y «VNP03IMG and VJ103IMG Imagery Resolution Terrain-Corrected Geolocation» (mismo párrafo)
  y la remisión «(see Coppola et al., 2016b for details)». En p. 18 (§6, fin): precisión de posición «±1 pixel (375 m), to
  account for geolocation offsets and PSF-induced blurring effects». 134 × 375 m = 50,25 km, igual que los 67 × 750 m de
  CA22. El interpolador del remuestreo sigue sin fuente.
- **CÓMO SE VE EN EL DASHBOARD**: invisible; cambia qué se puede citar al decidir el remuestreo de VIIRS 375 (D17) y
  la geolocalización (frente M): hay cita para «UTM, 134 × 134, centro GVP, geolocalización corregida por terreno».
- **CÓMO REPRODUCIRLO**: `python render.py <pdf> 5 out.png 150` sobre los dos PDF; `ubicar.py <pdf> "134|UTM|VNP03"`.
- **CONFIANZA**: CONFIRMADO (páginas renderizadas y leídas).
- **GRAVEDAD**: 2. Matiza el H1 de P2: la cadena de citas no termina en un paper que no trata el 375; termina en uno que
  lo trata y dice «mismo procedimiento», sin números. «Manda el paper» sigue sin tener números que mandar.

### H5. Coppola 2022 da k_MIR(I04) ≈ 7,16 µm sr; Campus 2024 y el OSF dan 18,0
- **ARCHIVO:LÍNEA**: Coppola et al. 2022 p. 5, columna izquierda, bajo la Ec. 1 (PNG `png\coppola2022_vulcano_p5_zoom_k.png`):
  «the constant k_MIR which, in the case of I04 band, centered at 3.74 μm, has a value equal to ~7.16 μm sr (for details
  on how to calculate the constant see Wooster, 2003)», con «A_pix is the pixel size (140625 m² for VIIRS Imaging Bands)».
  Contra CA24 p. 4 (18,0 µm sr, **heredado** de P2 H7) y el OSF (VRP = ΔL × 18,0 × 140.625 en todos los tramos, **heredado**
  de P2 `escalon_fino_salida.txt`), y contra `CLAUDE.md` del proyecto («VIIRS I-band 375m (I4): k = 18.0 × A_pix(140625)»).
- **QUÉ PASA**: la física de Wooster da k = σ/a; para 3,74 µm a es del orden de 3 × 10⁻⁹ y k queda cerca de 18, no de 7.
  El 7,16 es 2,5 veces menor: o es una errata del brief report, o la serie de Vulcano 2012-2022 de ese paper (línea base
  0,17 MW, umbral 0,32 MW, 696 anomalías) está en otra escala que el OSF. No lo medí.
- **CÓMO SE VE EN EL DASHBOARD**: invisible. Nuestro k = 18,0 está validado contra el OSF (S14); no hay nada que cambiar.
- **CONFIANZA**: CONFIRMADO lo que dice la página; SOSPECHA la implicación sobre la escala de ese paper.
- **GRAVEDAD**: 1. Advertencia para quien use los umbrales de Vulcano 2022 (0,32 MW) como referencia de «baseline».

### H6. El «Campus et al. 2021» que Sabancaya 2022 cita como origen del VIIRS 375 es un póster de VIIRS 750 m
- **ARCHIVO:LÍNEA**: `D:\vrp-trabajo\temporales\s159_biblio\Campus_2021_Poster_OSF_wv8yt_VIIRS.pdf` (OSF wv8yt, archivo
  `Campus A._Poster.pdf`, creado 2021-04-05; PNG `png\campus2021_poster.png`). Título «Monitoring volcanic thermal emission
  using VIIRS», Campus A. y Coppola D., Università di Torino, IV Conferenza Rittmann «Giovani Ricercatori», 6-9 abril
  2021. Texto (italiano): «è possibile utilizzare il VIIRS con risoluzione 750 m per studiare il calore emesso»; figuras
  de «banda M13 del VIIRS centrate a ... 4,05 µm»; tabla VIIRS contra MODIS, Stromboli 3-jul a 31-ago-2019.
- **QUÉ PASA**: P2 (H1) ya anotó que SAB atribuye el 375 m a «Campus et al., 2021» y que es un póster; lo que agrego es que
  el póster **no es de 375 m**: es M13/M15 a 750 m. La cadena de citas del 375 m en el grupo es: SAB → póster de 750;
  CA22 → «trabajo futuro»; C26 → CA22; el único que lo trata es Coppola 2022 Front. (H4), que remite a MODIS y a CA22.
  Valor lateral: el póster trae el **diagrama de flujo público del detector de 750 m** (cajas BOX, NTI y NTIapp, `dNTI <
  -0.1 → NaN`, `colfilt[3 3]`, μ y σ por región, «2nd Run», condiciones de alerta por región), que es la única figura
  pública de la lógica del `.m` de VIIRS 750. No lo comparé con el código.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CONFIANZA**: CONFIRMADO (póster renderizado y leído).
- **GRAVEDAD**: 1.

### H7. Tres fuentes nuevas del grupo (2026) que no están en `documentacion/` y no pude leer
- **SCRIPT:SALIDA**: `barrer_openalex.py` → `openalex_2025_2026.md` (35 obras únicas de Coppola, Laiolo, Massimetti y
  Campus desde 2025-01-01) y `openalex_aveni_salida.txt` (15 de Aveni). OpenAlex (HTML, 2026-10-21):
  1. **Aveni S., Coppola D., Laiolo M. (2026)**, «A synergistic thermal framework for monitoring, quantifying, and
     classifying volcanic activity from space», *Remote Sensing of Environment*, 10.1016/j.rse.2026.115626, publicado
     2026-08-20, **OA CC BY (hybrid)** según Unpaywall y Semantic Scholar; afiliación Sapienza y Torino. Es la versión
     completa del EGU26-13139 que la síntesis S73 marcó como «posible sucesor cap. 11». Resumen (OpenAlex, HTML):
     VRP_Tot = MIR + TIR, VRP_Ratio = VRP_MIR / VRP_TIR como proxy de temperatura efectiva, «existing MIR-only inventories
     underestimate total heat release by factors of 2-20», precursores en Sabancaya meses antes de nov-2016. **No pude
     bajarlo**: ScienceDirect responde 403 a `curl` y a WebFetch, y el navegador cae en un captcha («Are you a robot?»),
     que no se resuelve (acción prohibida). Hay que bajarlo a mano. El resumen no menciona VIIRS 375, MODIS, grilla ni
     umbrales; por el EGU26-13139 (HTML) tampoco: ninguna de esas palabras aparece.
  2. **Aveni S. (2026-01-29)**, tesis doctoral Sapienza, «Renewing the role of Thermal InfraRed (TIR) channels for remote
     sensing of volcanic activity and integration with multispectral data for near-real-time monitoring»,
     https://hdl.handle.net/11573/1760095. IRIS Sapienza responde 403; no sé si está embargada.
  3. **Coppola et al. (2026)**, «Analysis of SO₂ variability at Lascar Volcano using a multiparametric approach
     (2017-2021)», *JVGR*, 10.1016/j.jvolgeores.2026.108702 (2026-07-26), versión publicada del SSRN 6481652 que la
     síntesis S73 dejó pendiente. Volcán Tier A nuestro. Sin indicación de OA en OpenAlex.
  Los dos resúmenes de EGU26 (13139 y 19440, HTML, meetingorganizer.copernicus.org) no mencionan VIIRS 375, MODIS,
  MIROVA, grilla ni remuestreo; el 19440 (Aveni, Ganci de INGV Catania, Coppola) habla de TIRVolcH y VRP_TIR.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CONFIANZA**: CONFIRMADO que existen y que no están en `documentacion/` (`ls` del 2026-10-21); SIN LEER el contenido.
- **GRAVEDAD**: 1 para la réplica (nada en los resúmenes toca el detector); 2 para `experimental` (VRP_Ratio es justo el
  tipo de métrica que §12 pide anotar).

### H8. «Aveni (Sofia)» en la lista canónica: se llama Simone Salvatore Aveni y desde 2026 firma también por INGV Catania
- **ARCHIVO:LÍNEA**: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\docs\RESEARCH_WORKFLOW.md:44`
  («- Aveni (Sofia)»). Fuentes: OpenAlex autor A5068651821 «Simone Salvatore Aveni» (HTML); EGU26-13139 «Simone Aveni ...
  Sapienza ... University of Turin» (HTML); Aveni 2024 RSE p. 1 firma «S. Aveni» con Sapienza y Torino (PNG
  `png\aveni2024_p1.png`); Tamburello et al. 2026, EPS, 10.1186/s40623-026-02498-5, p. 1: «Simone Aveni 2,3» con las
  afiliaciones 2 = Torino y 3 = INGV (capa de texto de `D:\vrp-trabajo\temporales\s159_biblio\Coppola_2026_EPS_Vulcano_LaFossa.pdf`,
  no renderizada); OpenAlex lo lista en «INGV Osservatorio Etneo» en 2026.
- **QUÉ PASA**: el nombre de pila está mal en la regla A9 del proyecto, y la regla «MIROVA = Torino, Firenze, Sapienza»
  se aplica por persona cuando debería aplicarse por paper: Aveni firma en 2026 con Ganci (INGV Catania) y por INGV.
- **CONFIANZA**: CONFIRMADO el nombre; CONFIRMADO por capa de texto la doble afiliación 2026.
- **GRAVEDAD**: 1.

---

## 2. Inventario de fuentes del grupo MIROVA, 2025-2026

Denominador: 35 obras únicas de los perfiles OpenAlex de Coppola (A5050861768), Laiolo (A5072242410), Massimetti
(A5033162135) y Campus (A5022710971) con `from_publication_date:2025-01-01`, más 15 de Aveni (A5068651821), corrida
2026-10-21 sin API key (presupuesto compartido; `list/filter`, no `search`, salvo los cinco `authors?search`). Control
positivo: Coppola et al. 2026 Scientific Data (ya en `documentacion/`) aparece. **No busqué AGU, IAVCEI ni CoV**: una
búsqueda web dirigida no devolvió nada de 2025-2026 sobre VIIRS 375 y esos portales no están indexados en OpenAlex.
Tabla completa con DOI y URL OA: `openalex_2025_2026.md` y `openalex_aveni_salida.txt`. Acá sólo lo que importa a la réplica:

| fuente | tipo, año | afiliación verificada | paso que describe | cita localizada | dónde está |
|---|---|---|---|---|---|
| Coppola, Laiolo, Campus, Massimetti 2022, Front. Earth Sci. 10:964372 | artículo (brief), 2022 | Torino + NatRisk (p. 1, PNG) | VIIRS 375: «misma procedura» que MODIS y 750; VRP = A k ΔL con A = 140.625 m²; k ≈ 7,16 (H5); 7.723 imágenes nocturnas 2012-2022; sólo Suomi-NPP en la energía acumulada (Fig. 3) | p. 4-5, PNG `coppola2022_vulcano_p4.png`, `_p5.png` | **nuevo**, `D:\vrp-trabajo\temporales\s159_biblio\` |
| Campus, Coppola 2021, póster Rittmann (OSF wv8yt) | póster, 2021 | Torino (cabecera) | diagrama de flujo del detector de **750 m**; no 375 | PNG `campus2021_poster.png` | **nuevo**, `D:\...\Campus_2021_Poster_OSF_wv8yt_VIIRS.pdf` |
| Aveni et al. 2024, RSE 315:114388 | artículo, 2024 | Sapienza + Torino (p. 1) | grilla VIIRS 375: 134 × 134 UTM, centro GVP, VNP03IMG corregido por terreno; ±1 píxel de posición | p. 5 §3.2; p. 18 (PNG) | ya en `documentacion/Aveni_2024_TIRVolcH_RSE.pdf` (P2 no la había renderizado) |
| Coppola et al. 2026, Scientific Data 10.1038/s41597-026-08100-7 | data paper, 2026-08-18 | Torino, Sapienza, UNAM (heredado S141) | umbrales de archivo por sensor, DBSCAN, MOD03 (heredado P2 y P3) | heredado | ya en `documentacion/` |
| Aveni, Coppola, Laiolo 2026, RSE 10.1016/j.rse.2026.115626 | artículo, 2026-08-20, OA CC BY | Sapienza + Torino (OpenAlex) | VRP_Tot y VRP_Ratio; resumen no toca detección | resumen OpenAlex (HTML) | **SIN LEER**, bloqueado por captcha |
| Aveni 2026, tesis Sapienza, hdl 11573/1760095 | tesis, 2026-01-29 | Sapienza | desconocido (TIR, integración multiespectral, NRT) | ninguna | **SIN LEER**, IRIS 403 |
| Coppola et al. 2026, JVGR 10.1016/j.jvolgeores.2026.108702 (Láscar SO₂) | artículo, 2026-07-26 | Torino (OpenAlex) | aplicación en Láscar 2017-2021 | ninguna | SIN LEER; preprint SSRN 6481652 OA |
| Laiolo et al. 2026, Bull. Volcanol. 88 (Stromboli switching), 10.1007/s00445-025-01932-y | artículo, 2026-01-09 | Torino, Sapienza | aplicación | heredado | ya en `documentacion/s00445-025-01932-y.pdf` |
| Coppola et al. 2026, Bull. Volcanol. 88:119 (Mt Michael), 10.1007/s00445-026-02040-1 | artículo, 2026-09-15, OA | Torino (capa de texto) | aplicación; `ubicar.py` no halla NTI, ETI, grilla ni umbrales | ninguna de método | **nuevo**, `D:\...\Coppola_2026_BullVolc_MtMichael.pdf` |
| Tamburello et al. 2026, EPS, 10.1186/s40623-026-02498-5 (Vulcano) | artículo, 2026-07-22, OA | INGV + Torino | Sentinel-2 y suelo; una mención a 375 m (p. 7); no describe MIROVA | ninguna de método | **nuevo**, `D:\...\Coppola_2026_EPS_Vulcano_LaFossa.pdf` |
| EGU26-13139 y EGU26-19440 | resúmenes, 2026-03 | Sapienza, Torino; 19440 con Ganci (INGV Catania) | marco MIR + TIR; nada de 375, MODIS, grilla | HTML | sólo web |
| Resto 2025-2026 (Fernandina RS 17:1191, Piton JGR, Ambae CEE, Nyamulagira SRS, lava cooling RS 17:2543, Aveni GRL 2025, Popocatépetl JSAES, El Chichón, Stromboli JGR 2026, Cotopaxi SSRN, Virunga Zenodo, Fentale) | artículos y preprints | según OpenAlex | aplicaciones; ninguno con título de método MIR | no leídos | varios ya en `documentacion/` o Vault (`aveni2025grl`, `aveni2025tracking`, `coppola2025rapid`, `coppola2026lascar`) |

**Lectura del inventario.** En 2025-2026 el grupo no publicó ningún texto nuevo sobre la **detección** en VIIRS 375 ni
sobre el **fondo de MODIS**; lo nuevo va por TIR (VRP_TIR, TIRVolcH, VRP_Ratio) y por aplicaciones. Los huecos 1 y 2 del
encargo siguen abiertos por falta de fuente, con dos matices (H4): hay cita para «mismo procedimiento» y para la grilla.

---

## 3. Avisos de NASA, octubre de 2026 (HTML, leídos el 2026-10-21)

| aviso | fecha | qué dice | nos toca |
|---|---|---|---|
| Earthdata «Reminder: Suomi NPP Observations to Cease on November 2, 2026» | 21-oct-2026, activo | fin de datos científicos SNPP 13:00 UTC 2-nov-2026 (2026/306), «may change»; archivo sigue; pasar a NOAA-20 y NOAA-21 | **H1** |
| LAADS 199516 «Cessation of S-NPP data to users on November 02, 2026» | 6-oct-2026 | tabla de reemplazo VNP02/03 → VJ102/103 y VJ202/203; «will remain available from the LAADS archive»; no dice qué pasa con NRT | H1 |
| LDOPE 1479 «SNPP Decommission 11/02/2026» | 3-ago, act. 7-oct | «SNPP L1B data for the dates and times listed and all downstream products» | H1 |
| NESDIS «Cessation of S-NPP data to users on/after November 01, 2026» | 3-ago-2026 | 1-nov 13:00 UTC; NOAA-21 primario, NOAA-20 secundario | H1 (NASA lo corrió al 2-nov) |
| Earthdata «VIIRS Data Product Processing Delay» | 16-oct, act. 20-oct, activo, TBD | huecos de nivel 0 SNPP, JPSS-1 y JPSS-2 del 12 al 13-oct; «science team is working to fill the gaps»; afecta LP DAAC, NSIDC, LAADS | **H3**: los gránulos del 12 pueden volver; no hay fecha |
| ESDIS Weekly Metrics 5-oct | 5-oct | VIIRS-SNPP-Land tardío el 27-sep y 3-oct por «delays in L0 data»; NOAA-20-Atmosphere «planned outage» 30-sep y 3-oct; VIIRS-SNPP-Land 77 % de NRT en 3 h | contexto |
| ESDIS Weekly Metrics 12-oct | 12-oct | latencias VIIRS Atmosphere 8-oct por «upstream delay»; nada de MODIS, LAADS, LANCE, CMR | contexto; la del 19-oct no existe (404) |
| Banner Earthdata «Consolidated Ingest and Archive» | 28 a 30-oct-2026 | interrumpe ingesta en PO.DAAC, ASF DAAC y GES DISC | no nombra LAADS ni LANCE |
| LAADS 199534 «Version 7.0 MODIS Calibrated Radiances and Geolocation» | 17-mar-2026 | C7 disponible; C6.1 «decommissioned on September 30, 2026» | **H2** |
| Earthdata «Transition from MODIS to VIIRS» | 2-may-2025 | Terra y Aqua se apagan «in late 2026/early 2027»; «final reprocessing of MODIS data» | H2 |
| LAADS 199513 «LAADS Systems Emergency Maintenance» | 11-sep-2026 | mantención de emergencia ese día | no explica octubre |
| status.earthdata.nasa.gov | 21-oct | CMR y Earthdata Login «No Active Incidents» (ventana 45 días) | el hueco 17-20 no es de CMR (H3) |

**Sin aviso**: la ausencia de producción Standard del 18 y 19 de octubre (H3). **Sin aviso** tampoco de cambio de
colección VIIRS: CMR lista una sola versión por producto (`VNP02IMG` 2, `VJ102IMG` 2.1, `VJ202IMG` 2.1), las mismas que
pide `fetch.py:196-224`.

---

## 4. Lo que no pude hacer

- Leer el RSE 2026 (captcha de ScienceDirect, prohibido resolverlo) ni la tesis de Aveni (IRIS 403) ni el JVGR 2026
  de Láscar. Los tres van a mano.
- Comprobar en los PDF de aplicaciones 2025-2026 si alguno describe el fondo de MODIS: sólo pasé `ubicar.py` por Mt
  Michael y EPS 2026 (cero coincidencias de método); el resto no se descargó.
- Confirmar si nuestro cron del 17 al 20 de octubre usó las NRT (H3): no miré `data/` ni los runs de Actions; otro
  agente lista LAADS.
- Verificar la doble afiliación de Aveni 2026 en página renderizada (quedó en capa de texto).
- AGU 2025, IAVCEI 2025 y Cities on Volcanoes 2026: no están en OpenAlex y la búsqueda web no devolvió nada.

---

## 5. Candidatas para `docs/BEYOND_MIROVA_EXTENSIONS.md` §12

| id propuesto | qué | por qué podría ser mejor | evidencia | estado |
|---|---|---|---|---|
| MEJ-7 | **Vigilar la vida de las colecciones y plataformas** (fin de SNPP el 2-nov-2026; decomiso de MODIS C6.1; apagado de Terra y Aqua 2026-2027) con una prueba que falle cuando CMR deje de devolver una plataforma pedida por `fetch.py` | MIROVA no publica qué hace cuando una plataforma muere; un SDA tiene que saber por qué bajó su cobertura. Hoy un 0 de CMR y un «no hubo pasada» son indistinguibles | H1, H2; `cmr_modis_c61_vs_c7_salida.txt` | idea; el problema vence el 2-nov |
| MEJ-8 | **VRP_Ratio = VRP_MIR / VRP_TIR por cúmulo** en el perfil `experimental` (ya calculamos VRP_TIR de I05) | Aveni, Coppola y Laiolo 2026 (RSE 115626) lo proponen como proxy de temperatura efectiva que separa hidrotermal, domo, boca abierta y efusivo, y reportan precursores en Sabancaya; MIROVA NRT no lo publica | H7 (resumen; el paper queda por leer) | hipótesis; medir contra OVDAS, no contra MIROVA (A115) |
| MEJ-9 | **Grilla de 375 m declarada y citada** (134 × 134 UTM, centro GVP, geolocalización corregida por terreno) y, para `experimental`, grilla anclada al cráter | hay cita del propio grupo para la grilla de 375 (H4) que D17 no tenía; complementa MEJ-4 | Aveni 2024 p. 5 §3.2 | idea |
| MEJ-10 | **Escala de las líneas base publicadas**: antes de usar un umbral de la literatura del grupo (0,32 MW de Vulcano 2022) comprobar con qué k se calculó | Coppola 2022 declara k ≈ 7,16 donde el OSF usa 18,0 (H5) | PNG `coppola2022_vulcano_p5_zoom_k.png` | sospecha de errata; no medida |

---

## 6. VERIFICADO LIMPIO

- **El barrido por autor funciona y es completo para lo indexado**: OpenAlex sin key (presupuesto compartido) devolvió
  los cinco perfiles con afiliación Torino o Sapienza y el control positivo (Scientific Data 2026). Comando:
  `PYTHONIOENCODING=utf-8 python experiments\_s159\biblio_2026\barrer_openalex.py`. Aveni no se encuentra como «Sofia
  Aveni» (0 resultados): buscar «Aveni» a secas.
- **Las versiones de colección VIIRS que pide `fetch.py` (VNP02IMG 2, VJ102IMG 2.1, VJ202IMG 2.1) son las únicas que
  CMR lista** (`cmr_v7_y_versiones_salida.txt`). No hay cambio de colección VIIRS pendiente.
- **CMR está sano** (status.earthdata «No Active Incidents»; conteos del 8 al 16 de octubre normales en todas las
  Standard). El problema de octubre no es de CMR.
- **La síntesis S73 (`BIBLIOGRAPHY_SYNTHESIS.md` §10) ya tenía 11 de las 35 obras 2025-2026 de OpenAlex** (Fernandina,
  Piton, Ambae, Nyamulagira, Stromboli switching, Popocatépetl, lava cooling, Aveni GRL, Láscar SSRN, los dos EGU26);
  lo que faltaba son las publicadas después de mayo de 2026 (RSE 115626, Mt Michael, Láscar JVGR, Stromboli JGR,
  tesis de Aveni, EPS Vulcano). No hace falta rehacer S73.
- **Coppola 2022 Front. Earth Sci. es de Torino** (p. 1 renderizada: «Dipartimento di Scienze della Terra, Università
  degli Studi di Torino»; «NatRisk»), OA CC BY, 9 páginas, 2,37 MB, `%PDF-` verificado.
- **Las afiliaciones de 2025-2026 en OpenAlex son Torino o Sapienza en todas las obras del grupo salvo las de Aveni
  2026 con INGV** (H8); ninguna obra de Del Negro, Corradino, Di Bella, Marchese ni Pergola se coló en el barrido por
  autor (el filtro es por `author.id`, no por nombre).
- Comandos de verificación: `render.py <pdf> <página> <png> [dpi]`, `ubicar.py <pdf> <regex>`,
  `cmr_conteo_chile_oct2026.py`, `cmr_modis_c61_vs_c7.py`; cada script imprime su control positivo y su denominador.
