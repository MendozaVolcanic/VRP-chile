# S159, frente P3: relectura de los papers del linaje MODIS con el código de VIIRS 750 como llave

> S159, 2026-10-21. Sólo lectura: no se tocó `pipeline/`, `data/` ni `frontend/`, ni se hizo git. Todo lo de esta
> sesión vive en `C:\vrp-trabajo\s159-pruebas\experiments\_s159\p3\`. Toda cita a un PDF se tomó **de la página
> renderizada a imagen** (PNG en `png\`, generadas con `render.py`); la capa de texto (`ubicar.py`, `loc_*.txt`) sirvió
> sólo para elegir qué página renderizar. Las citas de código son de lectura propia en esta sesión. Lo que viene de
> otro documento y no reverifiqué lleva **(heredado)**.

## 0. En una pantalla

**El fondo del VRP de MODIS no tiene fuente que decida.** Las seis fuentes MODIS que leí describen el fondo como la
media de los píxeles que rodean al alertado (los vecinos inmediatos). El código de VIIRS 750 hace justo lo contrario:
deja fuera a esos vecinos con un halo e interpola por debajo. Y el texto de VIIRS 750 (Campus 2022, citado en D25)
también decía «media de los vecinos» aunque el código haga otra cosa, así que la redacción de los papers no distingue
entre los dos métodos. Trasladar a MODIS el halo y la interpolación del `.m` es una analogía que contradice la letra
de todas las fuentes MODIS, y la letra tampoco es una vara fiable. Lo nuestro (mediana de un anillo de 5 a 25 km y
recorte a cero) no lo respalda **ninguna** fuente. Ninguna fuente describe un recorte a cero.

**Suma, no máximo: cinco fuentes MODIS de acuerdo con el código.** Wright 2002 además dice que repartir un foco entre
dos píxeles por la respuesta triangular del barrido **no** es doble conteo. Nuestro `single_pixel_mode` (publica el
máximo en cúmulos de hasta 3 píxeles bajo 5 MW) no tiene respaldo en el linaje MODIS.

**Geolocalización: ninguna fuente dice cuál producto usa MIROVA.** Wright 2002 da 1 km por píxel con exactitud de
~200 m; Coppola 2021 dice que la de MIROVA yerra menos de 0,5 km a nadir. Nuestra interpolación (`_interp_geo`) se
come ese presupuesto entero ya en el nadir (0,5 km, aritmética propia), llega a una mediana de 3,4 km entre 40° y 55°
de cenit en un lado del barrido, y tiene además una componente a lo largo de la traza de hasta 2 líneas en el
comienzo y el final de cada gránulo que la segunda ronda no describió. Interpola además a través de los bordes de
barrido, que la guía L1B C7 desaconseja expresamente.

**Una frase de autoridad falsa en tres archivos de `pipeline/`**: «Wooster requiere ΔL ≥ 0». Wooster 2003 no lo dice
(Ec. 6b, p. 88), y el recorte que justifica es el mecanismo de los cúmulos de cumbre en 0 MW.

## 1. Respuestas a las cuatro preguntas del brief

**(a) ¿Algún paper describe el fondo del VRP de MODIS (anillo, halo, interpolación, recorte)? ¿Coincide con el `.m`?**
Sí lo describen, y **ninguno coincide con el `.m`**. Todos usan vecinos inmediatos, nunca halo ni interpolación ni
anillo regional, y ninguno recorta:

| fuente | qué dice del fondo (página renderizada) | contra el `.m` (V:63-85) |
|---|---|---|
| Wooster et al. 2003, RSE 86, p. 88, bajo la Ec. 5 | `L_MIR,bg` «estimated from neighbouring non-fire ‘ambient’ pixels»; Ec. 6b sin recorte | DISTINTO (vecinos contra halo) |
| Coppola et al. 2012, JVGR 215-216, p. 51, §3.4, bajo la Ec. 1a | media aritmética de los 8 píxeles que rodean al o a los alertados, no contaminados por nubes | DISTINTO |
| Coppola et al. 2014, IJRS, p. 3412, bajo la Ec. 4 | media aritmética de todos los píxeles que rodean al alertado (o al cúmulo), no nublados (Giglio 2003, BT11 < 255 K de noche) | DISTINTO |
| Coppola et al. 2020, Front. Earth Sci. 7:362, p. 3, bajo la ecuación del VRP | «average radiance of pixels surrounding the anomaly» | DISTINTO |
| Coppola et al. 2023, Front. Earth Sci. 11:1240107, p. 3, §2.2, Ec. 1; p. 6, Tabla 1 | «generally calculated from pixel(s) surrounding the anomaly»; `Tot_Lmir_bk` = suma del fondo de todos los alertados | DISTINTO en el método; IGUAL en la estructura (fondo por píxel alertado, sumado) |
| Aveni et al. 2024, RSE 315, p. 11, §4.3.5 y Ec. 5 (VIIRS 375, banda TIR, TIRVolcH) | quita las alertas e interpola los huecos con interpolación **bicúbica** de los píxeles no contaminados; fondo por píxel `BT_bg,i` | IGUAL en la familia (interpolar bajo las alertas); distinto interpolador, banda y sensor |

La única fuente del grupo que interpola bajo las alertas es de VIIRS 375 en TIR, no de MODIS en MIR. **Veredicto para
MODIS: SIN FUENTE que decida entre «media de vecinos» y «halo e interpolación».** Lo nuestro: Planck de la mediana de
la BT del anillo (`pipeline/process_modis.py:1083`, anillo de 5 a 25 km según el comentario de `:1095-1096`), kernel
de 3 × 3 sólo para los volcanes opt-in (`:1102-1112`, `ENABLE_LOCAL_KERNEL_BG = True` leído de `pipeline.profile`) y
recorte `np.maximum(hotpix_rad - L_bg, 0.0)` (`:1118`). Contra todas las fuentes: DISTINTO.

**(b) ¿Algún paper dice que MIROVA usa MOD03 o la geolocalización de MOD021KM, y cómo la interpola?** **No.**
Ninguna de las fuentes leídas nombra MOD03 ni la grilla de 5 km de MOD021KM, ni dice cómo se interpola:

- Coppola 2014, p. 3406, §2.1: la «location of each pixel (latitude and longitude)» se extrae de «the MODIS level 1
  granules»; no dice de qué archivo. CALLA.
- Coppola 2020, p. 3: los datos «Level 1b, calibrated radiances» se bajan de LANCE. CALLA sobre la geolocalización.
- Wright et al. 2002, RSE 82, p. 137: «The geolocation of MODIS pixels (which is 1 km for Bands 21, 22, and 32)», con
  exactitud de ~200 m tras las correcciones de actitud de Terra. Habla de geolocalización por píxel de 1 km (que es
  la de MOD03, no la de 5 km de MOD021KM), pero es MODVOLC (Hawái), no MIROVA (A9).
- Coppola et al. 2021, Sci. Rep. 11:13090, p. 12, «Methods», 2.º párrafo: las anomalías de MIROVA se geolocalizan con
  «errors in geolocation [...] less than 0.5 km for nadir acquisition» (ref. 60, Coppola 2016a). Es el único número de
  exactitud que el grupo publica.
- Aveni 2024, p. 5, §3.2: para VIIRS 375 usa el producto de geolocalización corregido por terreno (VNP03IMG). Que
  MIROVA use el análogo MODIS (MOD03) es **SOSPECHA** por analogía.

Lo que dicen los documentos del sensor, renderizados:

- Diccionario L1B C7, p. 66, Fig. 2.1.1: mapa de dimensión con **offset 2 e increment 5** a lo largo del barrido, y
  `1KM_geo_dim = Max_EV_Frames/5+1 = 271`. P. 100: `line_numbers = "3, 8"` y `frame_numbers = "3, 8, 13, ..."` (base
  1), o sea, los nodos de 5 km están en las líneas 2 y 7 de cada barrido de 10 y en las columnas 2, 7, 12, ... (base 0).
- Guía L1B C7, p. 11-12, §3.1.1: por el solape entre barridos, interpolar a través de los bordes de barrido «can
  produce inaccurate results»; «it is better to extrapolate from within the same scan [...] This is especially true of
  the 5KM subset stored in the 1km products».

Nuestro código: `read_modis_l1b` lee `Latitude`/`Longitude` de 406 × 271 del propio MOD021KM
(`pipeline/process_modis.py:265-266`) y los lleva a 1 km con `_interp_geo` (`:292-293`), que es
`scipy.ndimage.zoom(coarse, (scale_y, scale_x), order=1)` (`:385-396`). Ese `zoom` alinea esquina con esquina (el nodo
0 cae en el píxel 0 y el último en el último), así que ignora el offset 2, y es una interpolación global que cruza los
bordes de barrido. El docstring la llama «Bilinear interpolation» (`:386`) sin mencionar ninguna de las dos cosas. El
MOD03 se baja y se exige (`scripts/run_pipeline.py:224-229` salta el gránulo si no hay MOD03), pero
`calculate_vrp` no lo usa (`pipeline/process_modis.py:513`: «geo_path is accepted for API compatibility but not
used»). La medición M2 (§4) da el tamaño.

**(c) ¿Suma de todos los píxeles o máximo?** **Suma**, en todas las fuentes que lo dicen, igual que el código
(V:83-85):

- Coppola 2012, p. 51, Ec. 1a: ΔL = Σ sobre `nalert` de (L_alert − L_bk).
- Coppola 2014, p. 3413, Ec. 5 y 6: `VRP_PIX = 18.9 × A_PIX × ΔL4PIX` y, si hay un cúmulo, «the sum of the single
  VRP_PIX».
- Coppola 2020, p. 3: VRP = 18,9 · A_pixel · Σ (L_alert − L_bk)_i.
- Coppola 2023, p. 3, Ec. 1 («even a punctiform VTF can produce an excess of radiance that propagates not to one but to
  several pixels. Hence, the total excess radiance [...] is calculated as» la suma) y p. 6, Tabla 1 (`Tot_Lmir_hot`,
  «Sum of MIR radiance from all alerted pixels»).
- Wright 2002, p. 137: el foco puntual cae en uno o dos píxeles del barrido por la respuesta triangular, y eso «does
  not, however, lead to ‘double counting’ of radiance».
- Wooster 2003, p. 88: la Ec. 6b es por píxel individual; no trata cúmulos.

Lo nuestro: `apply_single_pixel_mode` en MODIS (`pipeline/process_modis.py:1246`), con
`ENABLE_SINGLE_PIXEL_SUB_MW_MODE = True`, tope 5,0 MW y hasta 3 píxeles (leído de `pipeline.profile`), publica el
máximo. DISTINTO de todas.

**(d) Frases de estas fuentes que el proyecto usa como autoridad y que el código o el paper contradicen** (candidatas a
marca A113): ver los hallazgos H4, H5 y H7 del §3. Resumen con ubicación:

| ubicación | frase | qué dice la fuente | ¿A45? |
|---|---|---|---|
| `pipeline/process_modis.py:1115`, `pipeline/process_viirs.py:1499`, `pipeline/vrp_regimes.py:332` | «Wooster requiere ΔL ≥ 0» | Wooster 2003 p. 88, Ec. 6b, sin recorte; el `.m` no recorta (V:83-85) | sí |
| `docs/MIROVA_DIVERGENCES.md:248` y `:329` | «La fórmula Wooster `vrp_mw = 18.9 × A_pix × BT⁸`», «potencia 8 de Wooster», «Wooster BT⁸» | Ec. 6b lineal en ΔL_MIR; la aproximación es L_MIR = aT⁴ (Ec. 4, p. 88) | no |
| `docs/MIROVA_DIVERGENCES.md:1127` | «Wooster MIR formula correctamente da 0» | el 0 exacto lo pone el recorte, no Wooster | no |
| `docs/MIROVA_DIVERGENCES.md:357` | cita «currently absent in all available algorithms» | la página dice «in all the operational systems» (Coppola 2020, p. 15, «Image Quality Assessment») | no |
| `docs/MIROVA_DIVERGENCES.md:385` | «data MIROVA OSF v2.5 entregada "as-are"» | Coppola 2023 p. 4, §2.5, habla de la base v.1 (MODIS 2000-2019), no del OSF v2.5 (A105) | no |
| `pipeline/process_modis.py:8, 86, 93, 97, 685, 774, 775, 1079`; `pipeline/process_viirs.py:860, 1027` | «Coppola 2015» como autoridad del NTI, del Test 1 y del método MIR | CLAUDE.md dice que esa cita es corrupta (heredado, no lo reverifiqué) | sí |

Verificadas sanas en esta sesión: CLAUDE.md:918 (Wright 2002 p. 141, «As the NTI is based on absolute radiance
values...»), los coeficientes MODIS de CLAUDE.md:106-108 (Wooster p. 88 y Coppola 2014 p. 3413) y la «remuestreo a
malla de área constante» de `docs/MIROVA_DIVERGENCES.md:2317` (Coppola 2014 p. 3406, §2.2), con el matiz de que
Coppola 2014 describe un algoritmo propio de Stromboli (p. 3405: «specifically developed for hot-spot detection at
Stromboli»); el remuestreo de MIROVA lo confirman Coppola 2020 p. 3 y 2023 p. 3.

## 2. La matriz

Columnas: lo que hace el `.m` de VIIRS 750 (H = `MIROVA_VIIRS750_hotspot_detection.m`, V = `MIROVA_VIIRS750_VRP.m`);
lo que dice cada fuente MODIS, con veredicto **contra el código** (IGUAL / DISTINTO / CALLA) y página renderizada; y
lo nuestro en MODIS. Siglas: W02 Wright 2002 (MODVOLC, no MIROVA), Wo03 Wooster 2003 (FRP, no MIROVA), C12 Coppola 2012
(Stromboli, pre MIROVA), C14 Coppola 2014 (Stromboli), C20 Coppola 2020 (sistema MIROVA), C21 Coppola 2021 (Klyuchevskoy,
con MIROVA), C23 Coppola 2023 (base MIROVA v.1, MODIS), Av24 Aveni 2024 (TIRVolcH, VIIRS 375), UG/DD guía y diccionario
L1B C7.

| # | paso | código V750 | fuentes MODIS | nuestro MODIS |
|---|---|---|---|---|
| 1 | remuestreo: origen, celda, interpolador | entra ya remuestreado (H:19-23); el README excluye la cadena operacional | C12 p. 50 §3.2: máscara de 50 × 50 km centrada en la cumbre a grilla UTM de 1 km; C14 p. 3406 §2.2: ídem, «equally spaced 1 km grid»; C20 p. 3: 50 × 50 km UTM; C23 p. 3 §2.1: 51 × 51 UTM centrada en la cumbre con coordenadas del GVP; Av24 p. 5 §3.2: 134 × 134 UTM «as per MIROVA workflow». IGUAL (hay remuestreo); interpolador: CALLA en todas | sin remuestreo (`ENABLE_UTM_REGRID = False`): DISTINTO (D17) |
| 2 | ROI y cajas | BOX 2 = 7 × 7 sensible, 1 = 21 × 19, 0 = resto (H:105-138 y matriz) | C23 p. 3: cumbre de 5 × 5 km con umbrales algo más bajos, más lejos algo más altos: IGUAL en concepto; C14: tres ROI concéntricas propias de Stromboli; W02: sin ROI (por píxel) | círculo `inner_radius_km` de 3 a 20 km: DISTINTO (D18) |
| 3 | nubes y validez | BT de M15 ≤ 200 K a NaN (H:150-154); escena rechazada con la mitad o más de NaN (H:163-167); el fondo del VRP no aparta nubes (V:63-81) | C12 p. 51: noche nublada si BT12 < 265 K, y el fondo usa sólo vecinos no nublados: DISTINTO; C14 p. 3412: BT11 < 255 K: DISTINTO; C23 p. 4 §2.5: VRP «as-are», sin corrección atmosférica ni fracción de nubes: CALLA sobre máscaras; C20 p. 15: cuantificar nubes por imagen «currently absent in all the operational systems» | `cloud_mask_bt_k = 0.0` (sin máscara), sin el filtro de 200 K ni el rechazo de escena |
| 4 | NTI y K1, día y noche | NTI = (M13 − M15)/(M13 + M15) (H:159); K1 −0,7 noche (H:178), −0,5 día (H:189); alerta directa (H:245) | W02 p. 145 Fig. 10 y p. 146: NTI con banda 22 (21 si satura) y **32**, umbral −0,80, sólo noche; C14 p. 3406 Ec. 1: L21ok y L32; C20 p. 3 y C23 p. 3: MIR 3,959 y TIR 12,02 µm. K1 −0,80 es de MODVOLC: DISTINTO del −0,7 del código y no es fuente MIROVA (A9) | banda 22 primaria (`ENABLE_MODIS_B22_PRIMARY = True`): IGUAL a W02 y C14; TIR banda 31 (`process_modis.py:262`): DISTINTO (D20); `NTI_K1_NIGHT = -0.8`; Test 1 integrado apagado (`ENABLE_TEST1_PATH = False`) |
| 5 | ETI y regresión | `polyfit` grado 2 sin alertas (H:343-350) | C20 p. 3 y C23 p. 3 nombran el ETI (Coppola 2016a) sin detalle: CALLA; W02, Wo03, C12, C14: no hay ETI | (no reverificado; D29 en el doc S158) |
| 6 | dNTI, ventana 3 × 3 | media de 3 × 3 con el central (H:281-294) | CALLA en todas (C12 p. 51 usa «el máximo NTI en una caja de 3 × 3 alrededor de la cumbre» para la alerta «potencial»: otro concepto) | 8 vecinos sin el central (heredado, doc S158 §3 punto 2) |
| 7 | umbrales C1 y C2 | H:180-199 | C23 p. 3: «slightly lower thresholds» en la cumbre, sin valores: CALLA | `DNTI_CONTEXTUAL_C1_SUMMIT = 0.003`, `_SCENE = 0.01` |
| 8 | compuerta de BT | no existe | W02: sólo NTI, sin compuerta: IGUAL; Av24 p. 11 test 11: `BT_candidate > BT_bg + ΔT_bg` (0,5 a 1 K) en TIR, otro algoritmo: DISTINTO; C14: no leí sus tests completos, SIN DATO | compuerta `bt > t_bg + 3 K` (heredado, D22) |
| 9 | segundo pase | siempre, recalcula la regresión (H:228-235) | CALLA en MODIS; Av24 p. 11 itera en TIR hasta que no aparecen alertas nuevas | (heredado, D26) |
| 10 | rama diurna | K1 −0,5, 15σ, mínimos 0,02, reflejo solar bajo 12° (H:83-89, 188-199) | W02 p. 145-146: sólo noche, el día «under development»; C12 p. 50: sólo noche; C14 p. 3409-3411: algoritmo diurno con corrección por banda 6 (Stromboli); C23 p. 4 §2.5: la base v.1 es sólo nocturna. OSF v2.5 (M3): 19.054 filas MODIS de día, todas sobre 50 MW | `ENABLE_DAYTIME_MODIS = False`: se rechaza todo el día (decisión D-10) |
| 11 | fondo del VRP | alertas más halo de 3, 5 o 7 celdas, `fillmissing2` lineal, sin recorte (V:63-85) | ver §1 (a): vecinos inmediatos en Wo03 p. 88, C12 p. 51, C14 p. 3412, C20 p. 3, C23 p. 3: DISTINTO; Av24 p. 11 interpola bicúbico en TIR: IGUAL en familia. Recorte: ninguna lo describe | mediana del anillo (`:1083`), kernel opt-in (`:1102-1112`), recorte (`:1118`): DISTINTO de todas |
| 12 | suma o máximo | suma de todos los alertados (V:83-85) | suma en C12 Ec. 1a, C14 Ec. 6, C20 p. 3, C23 Ec. 1 y Tabla 1; W02 p. 137 «no double counting»: IGUAL | `single_pixel_mode` (`:1246`) y cúmulo `vent_anchored`: DISTINTO (R2-3, D32) |
| 13 | coeficiente y área | 1,97 × 10⁷ y 0,5625 km² (V:88-91) | Wo03 p. 88 Ec. 6b: 1,89 × 10⁷ con A = 1,0 × 10⁶ m² en MODIS; C12 p. 52 Ec. 3; C14 p. 3413 Ec. 5 (A = 1 km² remuestreado); C20 p. 3; C23 p. 3 Ec. 2. OSF (M1): la identidad con A = 1 km² se cumple en 262.455 de 262.455 filas MODIS: IGUAL | `WOOSTER_COEFF = 18.9`, `ENABLE_NADIR_FIXED_PIXEL_AREA_MODIS = True`: IGUAL |
| 14 | cenit, barrido, bow tie | CALLA (sólo el reflejo solar usa el cenit) | C12 p. 50 §3.1: bow tie sobre 25° de barrido, quitado con Liu 2008; a 55° el píxel mide ~10 km² (2 × 4,8 km) y uno de 2 km² «became two equal area 1 km² pixels»; C14 p. 3406: igual; C23 p. 3: píxeles con bow tie «identified and removed»; C21 p. 12: el conjunto supervisado descarta cenit alto; C20 p. 4: VRP no corregido por geometría | sin bow tie (D28) ni remuestreo: DISTINTO |
| 15 | geolocalización | CALLA (el README excluye «geolocation diagnostics») | ver §1 (b): W02 p. 137 (1 km por píxel, ~200 m), C21 p. 12 (< 0,5 km a nadir), C14 y C20 CALLA; DD p. 66 y p. 100, UG p. 11-12 | `_interp_geo` con `zoom` alineado a esquinas (`:385-396`), MOD03 bajado e ignorado: DISTINTO |
| 16 | qué se publica | lista de alertas de la pasada y VRP de la unión (H:241-248; V) | C23 p. 6 Tabla 1: Npix, sumas de radiancia, VRP, lat y lon del píxel **más caliente**, distancia del alertado **más lejano**; W02 p. 146: por píxel, lat, lon y radiancias | cúmulo `vent_anchored` y campos `final_hotspot_*`: DISTINTO (D32) |

Una predicción de los papers que ya se cumplió: C12 p. 50 y C14 p. 3406 dicen que un píxel de 2 km² del barrido se
vuelve dos celdas de 1 km² al remuestrear. Eso predice que el Npix de MIROVA en MODIS **sube** con el ángulo, que es lo
que el verificador de la segunda ronda midió en el OSF (rho +0,30, R2 §1 fila 4). La cara MODIS de la caída con el
cenit es entonces el remuestreo (D17) según la letra del propio grupo, sin necesidad de suponerla.

## 3. Hallazgos, de peor a menos grave

### H1. El fondo del VRP de MODIS de MIROVA no tiene fuente que decida, y el traslado desde el `.m` contradice la letra de todas las fuentes MODIS
- **ARCHIVO:LÍNEA**: fuentes en §1 (a), PNG en `png\` (`1-s2.0-S0034425703000701-mai_idx005.png`,
  `coppola2012_jvgr_stromboli_1_idx004.png`, `coppola2014_ijrs_strombolian_idx011.png`,
  `Thermal_Remote_Sensing_for_G_idx002.png`, `feart-11-1240107_idx002.png`, `feart-11-1240107_idx005.png`,
  `Aveni_2024_TIRVolcH_RSE_idx010.png`); código `pipeline/process_modis.py:1083, 1102-1112, 1118`.
- **QUÉ PASA**: de noche un cráter con foco sub-píxel queda rodeado por vecinos que llevan parte de su calor (la
  respuesta del barrido lo reparte) y, más lejos, por terreno más frío o más tibio según el relieve. Las fuentes MODIS
  restan el promedio de esos vecinos inmediatos; el código de VIIRS 750 los aparta con un halo e interpola desde más
  afuera; nosotros restamos la mediana de un anillo de 5 a 25 km y recortamos. Las tres dan magnitudes distintas sobre
  el mismo píxel, y ningún texto del linaje MODIS habla de halo, interpolación ni recorte. Como el texto de VIIRS 750
  también decía «media de los vecinos» y el código hace otra cosa, la letra de los papers no sirve para elegir.
- **CÓMO SE VE EN EL DASHBOARD**: la magnitud MODIS y los cúmulos de cumbre MODIS en 0 MW ocultos (37 según R2-6, no
  medido aquí).
- **CÓMO REPRODUCIRLO**: `python render.py <pdf> <idx>` con los índices de §5, y abrir los PNG.
- **CONFIANZA**: CONFIRMADO para lo que dicen las fuentes; lo que hace el MIROVA operacional en MODIS: SIN DATO.
- **GRAVEDAD**: 3. Decide cómo se arma el brazo MODIS del frente N: si se le traslada el halo del `.m` y «acierta», no
  sabremos si acertó por la razón correcta. Pide un brazo con la media de vecinos y otro con el halo, no uno solo.

### H2. Suma, no máximo: ninguna fuente MODIS respalda `single_pixel_mode`
- **ARCHIVO:LÍNEA**: `pipeline/process_modis.py:1246`; fuentes en §1 (c); PNG `coppola2014_ijrs_strombolian_idx012.png`,
  `wright2002_rse_automated_vol_idx002.png`, `feart-11-1240107_idx002.png`, `feart-11-1240107_idx005.png`.
- **QUÉ PASA**: un foco pequeño reparte su radiancia en dos o tres píxeles por el ancho de la respuesta del sensor;
  MIROVA suma todos y nosotros, bajo 5 MW y con hasta 3 píxeles, publicamos sólo el más caliente. Wright 2002 trata
  justo ese reparto y dice que no es doble conteo. El propio docstring del módulo justifica el modo por datos (Tupungatito
  30×), no por paper.
- **CÓMO SE VE EN EL DASHBOARD**: magnitudes MODIS sub 5 MW de cúmulos de 2 o 3 píxeles publicadas bajas (R2 midió
  153 de 512 cúmulos MODIS con el modo y suma/publicado mediana 1,37; no lo medí).
- **CÓMO REPRODUCIRLO**: leer las páginas citadas; `VRP_PROFILE=mirova_equivalent python -c "import pipeline.profile as
  p; print(p.ENABLE_SINGLE_PIXEL_SUB_MW_MODE, p.SUB_MW_REGIME_THRESHOLD_MW, p.SINGLE_PIXEL_MAX_CLUSTER_PIXELS)"` da
  `True 5.0 3`.
- **CONFIANZA**: CONFIRMADO. Es R2-3 visto desde el papel.
- **GRAVEDAD**: 3 (magnitud de alertas débiles; ninguna protegida medida aquí).

### H3. La geolocalización MODIS gasta todo el presupuesto de error de MIROVA ya en el nadir, y tiene una componente a lo largo de la traza que la segunda ronda no describió
- **ARCHIVO:LÍNEA**: `pipeline/process_modis.py:265-266, 292-293, 385-396, 513`; `scripts/run_pipeline.py:224-229`;
  DD p. 66 y p. 100, UG p. 11-12 (PNG `MODIS_L1B_DataDictionary_C7_idx069.png`, `..._idx103.png`,
  `MODIS_L1B_UserGuide_C7_idx015.png`, `..._idx016.png`); C21 p. 12 (`s41598-021-92542-z_idx011.png`).
  SCRIPT `m2_interp_geo_aritmetica.py` → `m2_interp_geo_aritmetica.txt`.
- **QUÉ PASA**: el satélite entrega la posición sólo en uno de cada cinco píxeles, empezando por el tercero. Nuestra
  interpolación pone el primer nodo en el primer píxel, así que estira la grilla y corre la posición hasta 2 píxeles.
  Medido por aritmética de índices: 0,5 km ya en el nadir (lo mismo que MIROVA declara como error total a nadir), en
  un lado del barrido 1,3 km a 25° de cenit y mediana 3,4 km entre 40° y 55° (máx. 5,0), en el otro lado mediana 1,3
  km entre 40° y 55°; los dos lados, hacia el nadir. **A lo largo de la traza** pasa lo mismo: ±2 líneas en el
  comienzo y el final del gránulo, 0 en el medio, y la mitad de las líneas con más de 1 línea de error. Encima, la
  interpolación cruza los bordes de barrido, donde los barridos se solapan fuera del nadir (bow tie), que la guía L1B
  desaconseja. Y el MOD03, que trae la posición de cada píxel, se baja, se exige y no se usa.
- **CÓMO SE VE EN EL DASHBOARD**: el punto MODIS corrido respecto del cráter; cuando el corrimiento cruza
  `inner_radius_km`, la clase cumbre o lejana; la distancia publicada.
- **CÓMO REPRODUCIRLO**: `PYTHONIOENCODING=utf-8 python m2_interp_geo_aritmetica.py` (sin red, sin datos).
- **CONFIANZA**: CONFIRMADO como error de índice dado el diccionario; la traducción a km es una Tierra esférica sin
  relieve (orden de magnitud); el efecto del bow tie en el borde de barrido: SOSPECHA, no medido.
- **GRAVEDAD**: 3. Matiz al diseño del frente M: estratificar también por la **posición del volcán dentro del
  gránulo** (comienzo, medio, final), no sólo por lado del barrido; un volcán en el medio del gránulo y del lado bueno
  casi no se mueve, uno en una esquina del lado malo se corre 5 km o más.

### H4. «Wooster requiere ΔL ≥ 0»: autoridad falsa en tres archivos de `pipeline/`, que protege el mecanismo del cráter en 0 MW
- **ARCHIVO:LÍNEA**: `pipeline/process_modis.py:1115`, `pipeline/process_viirs.py:1499`, `pipeline/vrp_regimes.py:332`;
  Wooster 2003 p. 88, Ec. 5 a 6b (PNG `1-s2.0-S0034425703000701-mai_idx005.png`).
- **QUÉ PASA**: cuando el fondo que restamos es más tibio que el píxel alertado (cumbre helada, anillo con valles), el
  exceso sale negativo y se recorta a cero. El comentario atribuye ese recorte a Wooster, cuya ecuación es una resta
  sin recorte, válida para focos de 600 a 1.500 K; tampoco recorta el `.m` (V:83-85) ni ninguna ecuación MODIS del
  grupo (C12 Ec. 1a, C14 Ec. 4, C20 p. 3, C23 Ec. 1). La decisión es propia (S26), legítima o no, pero no de Wooster.
- **CÓMO SE VE EN EL DASHBOARD**: invisible como texto; su efecto son los cúmulos de cumbre en 0 MW ocultos.
- **CÓMO REPRODUCIRLO**: `grep -n "Wooster requiere" pipeline/*.py`; abrir el PNG de Wooster.
- **CONFIANZA**: CONFIRMADO que la p. 88 no lo dice; la búsqueda de «positive», «zero», «clip» y «less than» en la capa
  de texto de todo el paper no dio ninguna regla de recorte (la única coincidencia es la condición de 320 K de su
  simulación, que excluye píxeles dominados por el fondo, no recorta).
- **GRAVEDAD**: 2 (documentación de un SDA bajo la Resolución CPLT N°372; la marca va bajo A45).

### H5. «La potencia 8 de Wooster» no existe
- **ARCHIVO:LÍNEA**: `docs/MIROVA_DIVERGENCES.md:248` y `:329`.
- **QUÉ PASA**: la explicación física de D9 dice que la fórmula de Wooster es `18.9 × A_pix × BT⁸` y que esa potencia
  amplifica el contraste nube y roca. La Ec. 6b es lineal en la radiancia MIR en exceso; lo que crece rápido con la
  temperatura es la radiancia de Planck a 4 µm, no la fórmula. El mecanismo de D9 puede seguir valiendo, pero no por
  esa razón.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `grep -n "BT⁸\|potencia 8" docs/MIROVA_DIVERGENCES.md`; PNG de Wooster p. 88.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD**: 2 (es parte del relato que sostuvo el tope de 5 MW; no decide nada hoy).

### H6. MIROVA guarda MODIS diurno en el OSF; nosotros lo rechazamos entero
- **ARCHIVO:LÍNEA**: SCRIPT `m3_modis_dia_osf.py` → `m3_modis_dia_osf.txt`.
- **QUÉ PASA**: el OSF v2.5 (2000-02-24 a 2025-12-31) trae 19.054 filas MODIS de día, todas sobre 50 MW; 219 en
  volcanes chilenos, 16 en 2025 (7 de Chillán, mediana 324 MW). Algunas huelen a reflejo solar (Lastarria 2025, 800 MW
  de mediana, A76): que sean calor real es SOSPECHA. Es la cara MODIS de R2-10 y cae en la decisión D-10.
- **CÓMO SE VE EN EL DASHBOARD**: ningún punto MODIS diurno.
- **CÓMO REPRODUCIRLO**: `PYTHONIOENCODING=utf-8 python m3_modis_dia_osf.py`.
- **CONFIANZA**: CONFIRMADO el conteo; su valor como alerta: SOSPECHA.
- **GRAVEDAD**: 2 (ya es decisión tuya, D-10; el OSF es archivo filtrado, no el NRT).

### H7. Citas menores sin respaldo en `docs/MIROVA_DIVERGENCES.md` y en comentarios de `pipeline/`
- **ARCHIVO:LÍNEA**: `docs/MIROVA_DIVERGENCES.md:357` (cita alterada: el paper dice «all the operational systems»,
  Coppola 2020 p. 15, PNG `Thermal_Remote_Sensing_for_G_idx014.png`), `:384` (paráfrasis «cloud filter per-scene»: el
  paper habla de cuantificar nubes y geometría por imagen), `:385` («as-are» atribuido al OSF v2.5; C23 p. 4 habla de
  la base v.1), `:1127` (el 0 exacto lo pone el recorte); «Coppola 2015» en `pipeline/process_modis.py:8, 86, 93, 97,
  685, 774, 775, 1079` y `pipeline/process_viirs.py:860, 1027` (CLAUDE.md la da por corrupta; heredado); docstring
  «Bilinear interpolation» de `pipeline/process_modis.py:386`.
- **CONFIANZA**: CONFIRMADO salvo la corrupción de «Coppola 2015» (heredado).
- **GRAVEDAD**: 1.

## 4. Mediciones

### M1. ¿MIROVA recorta ΔL a cero? (`m1_recorte_osf.py` → `m1_recorte_osf.txt`)
- Pregunta 1 (si estuviera roto, ¿lo vería?): **NO**. El OSF trae sólo filas sobre un umbral de VRP por sensor
  (mínimos exactos: MODIS 1,0 × 10⁵ W de noche y 5,0 × 10⁷ de día; VIIRS 375 1,0 × 10⁴; VIIRS 750 5,0 × 10⁶). Una fila
  con ΔL ≤ 0 nunca puede estar en el archivo, recorte o no. **SIN DATO**, no cuenta como verificación.
- Pregunta 2 (si el instrumento estuviera muerto): control positivo, la identidad VRP = k · A · (Tot_hot − Tot_bk) se
  cumple en 262.455 de 262.455 filas MODIS (A = 1 km²) y en 252.374 de 252.374 de VIIRS 375; en VIIRS 750, 92.402 de
  100.641 (el escalón de 50° de R2-10 y F6). Las columnas se leen bien.
- Denominador y ventana: 615.470 filas, 2000-02-24 a 2025-12-31.

### M2. Error de índice de `_interp_geo` (`m2_interp_geo_aritmetica.py` → `.txt`)
- Pregunta 1: sí lo vería; un `_interp_geo` correcto da error 0 en el interior.
- Pregunta 2: control positivo, `np.interp` sobre los índices verdaderos da error máximo 0,0 en el interior.
- Resultado en §3 H3. Denominador: las 1.354 columnas y las 2.030 líneas de un gránulo de 203 barridos; no son datos.

### M3. MODIS diurno en el OSF (`m3_modis_dia_osf.py` → `.txt`)
- Pregunta 1: un 0 mostraría que MIROVA no guarda MODIS de día; da 19.054.
- Pregunta 2: control, VIIRS 750 de día da 17.859 (lo que R2-10 vio en NRT).
- Límite: filtrado por umbral (A105); un 0 en un volcán no prueba silencio de MIROVA. Ventana 2000-02-24 a 2025-12-31;
  «Chile» es una caja de lat. −17 a −56 y lon. −76 a −66.

## 5. Páginas renderizadas (índice 0 de PyMuPDF → página impresa)

Wright 2002: idx 2 (p. 137), 6 (p. 141), 10 (p. 145), 11 (p. 146). Wooster 2003: idx 5 (p. 88). Coppola 2012: idx 3, 4,
5 (p. 50, 51, 52). Coppola 2014: idx 4, 5, 10, 11, 12 (p. 3405, 3406, 3411, 3412, 3413). Coppola 2020 (archivo
`Thermal_Remote_Sensing_for_Global_Volcano_Monitori.pdf`): idx 2 (p. 3), 14 (p. 15). Coppola 2021 Sci. Rep.
(`s41598-021-92542-z.pdf`): idx 11 (p. 12). Coppola 2023 (`feart-11-1240107.pdf`): idx 2, 3, 5 (p. 03, 04, 06). Aveni
2024: idx 4, 10, 11 (p. 5, 11, 12). Diccionario L1B C7: idx 69 (p. 66), 103 (p. 100). Guía L1B C7: idx 15, 16 (p. 11,
12).

## Lo que no pude medir

- **El método exacto del fondo MODIS de MIROVA**: no hay código MODIS publicado y la letra no discrimina (H1).
- **El efecto del bow tie en la geolocalización** cerca de los bordes de barrido: requiere MOD03 y un gránulo real.
- **La geolocalización en km sobre gránulos reales** (frente M): mi conversión es esférica y sin relieve.
- **Si MIROVA recorta ΔL**: el OSF es ciego por construcción (M1).
- **Coppola 2016a y el capítulo Springer** quedaron fuera de mi frente por diseño; las filas 5 a 9 dependen de ellos.
- **Los tests de detección de Coppola 2014** (p. 3407-3410) no los leí completos: la fila 8 queda SIN DATO para esa
  fuente. Tampoco reverifiqué D22, D26, D29 ni la ventana de 8 vecinos (marcados «heredado»).
- **Coppola 2019 como PDF**: el archivo `Thermal_Remote_Sensing_for_Global_Volcano_Monitori.pdf` es Coppola et al.
  2020 (Front. Earth Sci. 7:362, publicado el 27 de enero de 2020, doi 10.3389/feart.2019.00362); es el que el
  proyecto llama «Coppola 2019».

## VERIFICADO LIMPIO

- Coeficiente y área MODIS (CLAUDE.md:106-108): Wooster p. 88 Ec. 6b (1,89 × 10⁷, A = 1,0 × 10⁶ m²) y Coppola 2014 p.
  3413 Ec. 5; OSF con identidad en 262.455 de 262.455 filas (M1); `WOOSTER_COEFF = 18.9` y área nadir fija leídos de
  `pipeline.profile`. No hay que volver a mirarlo.
- La cita de Wright 2002 de CLAUDE.md:918 está en la p. 141, palabra por palabra (PNG `wright2002_..._idx006.png`).
- «MIROVA remuestrea a malla de área constante» (`docs/MIROVA_DIVERGENCES.md:2317`): Coppola 2014 p. 3406 §2.2,
  confirmada para el sistema MIROVA por Coppola 2020 p. 3 y 2023 p. 3.
- La banda 22 primaria con la 21 si satura (`ENABLE_MODIS_B22_PRIMARY = True`) coincide con Wright p. 146 y Coppola
  2014 p. 3406; la banda TIR 32 de Coppola 2020 y 2023 ya está registrada en D20, no es nueva.
- El bow tie en el linaje MODIS (Coppola 2012 p. 50, 2014 p. 3406, 2023 p. 3) ya está en D28; no hay nada nuevo que
  agregar salvo su relación con la geolocalización (H3).
- La suma de todos los alertados del `.m` coincide con todas las fuentes MODIS (fila 12): esa parte del código no es
  una rareza de VIIRS 750.
- Comando de flags: `VRP_PROFILE=mirova_equivalent python -c "import pipeline.profile as p; print(p.ENABLE_UTM_REGRID,
  p.ENABLE_NADIR_FIXED_PIXEL_AREA_MODIS, p.CLOUD_MASK_BT_K, p.ENABLE_LOCAL_KERNEL_BG, p.ENABLE_DAYTIME_MODIS,
  p.ENABLE_MODIS_B22_PRIMARY, p.ENABLE_SINGLE_PIXEL_SUB_MW_MODE, p.NTI_K1_NIGHT, p.ENABLE_TEST1_PATH)"` da `False True
  0.0 True False True True -0.8 False`.
