# A6 — Relectura del canon buscando la contradicción (S128)

**Papers**: Coppola et al. 2016a (GSL Spec. Publ. **426**, 181–205) · Campus et al. 2022
(*Sensors* 22:1713) · Campus et al. 2024 (*Bull. Volcanol.* 86:25) · Aveni et al. 2024
(*RSE* **315**:114388).

**Sobre "página"**: los extraídos **no conservan la paginación** (SP426.5 sale en doble columna
intercalada). Cito por **sección + línea del archivo extraído**, verificable con `sed -n 'Np'`.
Donde el extracto trae el pie de página, lo doy.

---

## 0. Contradicciones, por impacto

- **C1** (frente 5) — Los píxeles del **Test 1 (K1)** deben salir del pool μ/σ. No salen. El
  "mislabel" de S115 se apoya en que "el second-run ya lo cubre", y el second-run **no** los excluye.
  Verificado: `ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK=False`.
- **C2** (frentes 3, 8) — **ROI1 es una caja de 5×5 km, igual para todos los volcanes.** Usamos un
  círculo de radio 3–20 km por volcán; en PCC el ROI1 queda **50×** más grande que el del paper.
- **C3** (frente 2) — `L4bk` = media de los píxeles **que rodean** al activo: el píxel caliente no
  entra en su propio fondo. Nuestro fondo es autorreferente (S126).
- **C4** (frente 6) — El **máximo diario NO es el producto publicado**: es capa de análisis, y cada
  paper usa una distinta. Publicar por pasada es **correcto**.
- **C5** (frente 7) — Saturación M15: Campus 2022 Tabla 1 da **343 K**; usamos **423 K**
  (`process_viirs_mod.py:194`).
- **C6** (frentes 3, 4, 8) — Aveni 2024 (canon Torino) usa máscaras de exclusión **por volcán**,
  referencias mensuales y test de nube: todo lo que MISSION.md llama drift.

---

## 1. Fórmulas (verbatim) y sus criterios

- **Coppola 2016a** Eq. 7 (l. 384): *"RP_PIX = 18.9 · A_PIX · ΔL4_PIX"*, con *"A_PIX is the pixel
  size (1 km2 for the resampled MODIS pixels)"* → **área nadir fija, confirma A66**. Eq. 6 (l. 358):
  *"L4bk is estimated from the arithmetic mean of all the pixels surrounding the active one (or
  around the active cluster)"*.
- **Campus 2022** (p. 7/24): *"VRP = ΔL_MIR · 1.97 × 10⁷ · A_pix"*, A_pix = 0,5625 km², válido
  *"between 600 and 1600 K"*; grilla (l. 413) *"UTM 51 × 51 km… matrices of 67 × 67 pixels"*.
- **Campus 2024** (p. 4/7): k = 18,0 µm·sr, A_pix = 140.625 m², error ~30 %, grilla *"regular 50×50
  km UTM"*; Eq. 2 pone el fondo **por píxel**, *"computed from the arithmetic mean of the radiance of
  the pixels surrounding the alerted one(s)"*, sumado sobre los N alertados.
- **Aveni 2024** (Eq. 5): VRP_TIR = σ·ε·Σ(BT⁴_alert−BT⁴_bg)·A, σ = 5,67×10⁻⁸, ε = 1, A = 140.625 m²
  → **idéntico a lo nuestro; D3 sigue bien cerrado**.

**Criterios (el "por qué")**. *Resampleo* (l. 172-180): las altas oblicuidades hinchan el píxel
*"up to c. 10 km2 for scan angles of 55°"* y *"the hotspot detection scheme… requires homogenous
pixel scale"* — el resampleo es lo que **legitima** el área nadir fija; nosotros usamos el área nadir
**sin** el resampleo (D17): coherente en magnitud, pero el kernel de 8 vecinos no opera sobre escala
homogénea. *Dos ROIs* (l. 315-318): *"because of variable size and different chance of finding a
thermal anomaly in the two regions"* — criterio de **tamaño relativo**: ROI1 5×5 sobre 50×50 es el
1 % de la escena; PCC con r = 20 km es el **50 %**. *C2 = 5/10* (l. 407-16): *"C2 ≈ 10 will
efficiently avoid false detections but will cause the omission of more than 25% of the small alerts
(<10 MW)… C2 ≈ 3 will only lose 7% of the small alerts, at the expense of more than 7% false
detections"*; elegido *"omitted (c. 10%) and false (c. 5%)"*. *Nube* (l. 360-67): *"we are not
interested in discriminating cloudy pixels"*.

## 2. Tabla 1 verbatim

El extracto la desordena (los menos salen como "2"); reconstruida (l. 334-345):

| | Noche ROI1 | Noche ROI2 | Día ROI1 | Día ROI2 |
|---|---|---|---|---|
| K1 | −0,8 | −0,8 | −0,6 | −0,6 |
| C1 | 0,003 | 0,01 | 0,02 | 0,02 |
| C2 | 5 | 10 | 15 | 15 |

Nuestros C1/C2/K1 son **exactos** (`NTI_K1=-0.8` efectivo). La divergencia **no está en los
números: está en la geometría a la que se aplican** (C2).

---

## 3. El second-run y el pool μ/σ — C1

Tres frases, en el orden del paper:

1. Test 1 (l. 297-300): *"Pixels that satisfy Test 1 are flagged as 'active' and subsequently
   discarded (unsuitable) for further steps."*
2. Tests 2/3 (l. 326-329): *"…C1 and C2 are constants, and m and s are the arithmetic mean and
   standard deviation of all the **suitable** pixels within the image."*
3. Second run (l. 346-356): *"step 2 (spatial analysis) is performed a second time, being
   particularly careful to eliminate all of the 'active' pixels already detected. Hence, the previous
   step (contextual threshold: tests 2 and 3) are applied again to the new dNTI and dETI matrices."*

Encadenadas: Test 1 → `active` ⇒ `unsuitable`; μ/σ sólo sobre `suitable` ⇒ **los K1 no pueden
estar en el pool**. No es interpretación: es la cadena literal.

**Nuestro código (A48)**: `process_modis.py:791-793` hace `_test1_mask_for_fp = nti_path_hot if
ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK else None` y lo pasa como `test1_mask=` (l. 817). El flag es
**False** en `mirova_equivalent` (leído de `pipeline.profile`, no del YAML) → se pasa `None` →
`build_unsuitable_mask` no retira los K1 (`detection_context.py:135`). Igual en
`process_viirs.py:1204/1227` y `process_viirs_mod.py:778/801`.

**El argumento de S115 no se sostiene.** `MIROVA_DIVERGENCES.md:1310` dice que el retiro del pool
está *"ya cubierto por el second-run (full)"*. Pero el second-run recibe `active_mask=hot_mask_2d`
(`process_modis.py:852-854`) y `hot_mask_2d = fp_hot` (l. 819) = **sólo la salida de Tests 2∧3**;
`nti_path_hot` (los K1) es otra máscara, que nunca entra a `active_mask`. Falso negativo tipo **A89**:
el flag se llama `..._RETIRE_FROM_HOT_MASK` (reporte) pero gatea **también** el pool; S115 leyó el
nombre, no el uso.

**GAP #A está ABIERTO** y merece A/B propio. Ojo con el signo: sacar píxeles calientes del pool
**baja σ** → baja el umbral μ+C2σ → **más** detecciones débiles; puede empeorar el difuso (A69/A82).
El A/B debe medir FN sobre cat-b real, estratificado focal/nevado (A83).

---

## 4. Agregación temporal — C4

- **Coppola 2016a, l. 616-623** (sección TADR): *"To simplify this problem, we consider here the
  highest TADR recorded during a 24 h time window as being the most representative value for the
  daily eruption rate. Hence, the cumulative volume of erupted lava is calculated by integrating the
  daily TADR"*. Máximo diario **sólo** para integrar volumen, y sobre TADR, no sobre RP.
- **El producto publicado es lo contrario** (l. 723-727): *"the RP time series obtained by MIROVA are
  provided 'as they are' and may be affected by the presence of meteorological and/or volcanic
  clouds"*.
- **Campus 2022** usa **media semanal** (`VRPw`, l. 612) y deja los datos crudos (l. 468-473,
  p. 8/24): *"we have left the datasets 'as they are', that is without applying image inspections or
  filters that discard cloudy scenes or scenes acquired in unfavorable geometric conditions (e.g.
  high satellite zeniths). Actually, under these conditions, we test the potential efficiency of the
  algorithm in NRT applications where such supervision is not applied"*. Ese párrafo **valida
  directamente** dos decisiones nuestras: publicar por pasada y la nube apagada.
- **Campus 2024** (p. 4/7): *"the data were not corrected atmospherically or filtered by a maximum
  value of zenith"* — un valor por escena.

El máximo diario de Laiolo 2026 vive, entonces, en la capa de análisis. La traducción correcta **no
es cambiar el pipeline**: es aplicarlo en la **auditoría de paridad**, donde hoy comparamos pasada
contra pasada y la nube castiga en las dos direcciones.

---

## 5. Los otros frentes

**F1 — piso VRP.** El canon **no** pone piso: la escala publicada arranca bajo 1 MW (Fig. 11,
*"Low <1 MW; Moderate 1–10 MW…"*) y el histograma de Láscar de Campus 2022 parte en 0,1 MW. Coppola
(l. 688-695) sí dice que los FP *"typically radiate less than 5 MW"*, que son **diurnos**, y que
*"reducing the false detection rate will cause numerous genuine alerts of low intensity (<10 MW) to
be missed"*. Nuestro artefacto es **nocturno** y de 0,04–0,06 MW: no es ese fenómeno. Un piso duro no
tiene respaldo canónico.

**F2 — fondo local (C3).** Ambos papers de magnitud excluyen el píxel activo (Coppola Eq. 6,
Campus 2024 Eq. 2) y difieren entre sí en granularidad: Coppola admite corona de **clúster**; Campus
2024, fondo **por píxel** sumado. Nuestro fondo autorreferente contradice a los dos; el brazo
"corona" de S127 es la lectura Coppola-2016a y **tiene respaldo textual**.

**F4 — nube.** Si MIROVA filtrara, el test está en Aveni §4.3.1: residual **negativo** contra una
referencia mensual (`RES = OBS − REF`; `RES < ABS_CL`, con ABS_CL = 0 ó −5 K según el percentil 99,5
de RES). Nube = **anomalía fría** respecto de la climatología del píxel, no un umbral absoluto de BT.
Coppola remite además a **Zaksek 2013** (Kalman) como la vía *"computer-based"*.

**F7 — saturación (C5).** Campus 2022 Tabla 1: MODIS B21 **500 K**, B22 331, B31 400; VIIRS M13
**634 K**, M15 **343 K**. Nuestro guard MODIS 500,0 y M13 634 coinciden, pero `BT_LUT_MAX_MBAND` usa
**M15 = 423 K** contra 343 — 80 K sobre la banda que alimenta VRP_TIR. No lo resuelvo (A35: manda el
UserGuide); queda señalado.

**F8 — difuso vs foco.** Aveni (l. 138-148): los algoritmos MIR *"are not designed to detect
low-temperature (≤600 K) volcanic phenomena"*, y ahí el MIR *"provides only a minimum value"*
(Coppola l. 697-704). Aveni resuelve el sesgo espacial con lo que a nosotros nos está vedado:
**VSExcROI**, máscara de exclusión **por volcán** (2 / 5 km / sin restricción) construida *"based on
the type of volcanism and on the distance from the summit reached by lava flows… within the last 2
decades"*. Es la máscara por distancia que MISSION.md rechaza, firmada por el canon (C6).

**F9 — incertidumbre.** Coppola (l. 693-699): *"when the hot emitter has an integrated temperature
higher than 600K… this method provides RP estimates with an uncertainty of ±30%"*. Igual a Laiolo
2026: **no es cifra nueva**, viene de Wooster 2003. Nuestra banda [0,5–2,0] es 3–4× más ancha: es
paridad **de sistema**, no incertidumbre instrumental — decirlo así en la ficha SDA.

---

## 6. Qué citan que no tenemos

- ⭐ **Wright et al. 2002**, RSE 82:135–155, `10.1016/S0034-4257(02)00030-5` — **origen del NTI** y
  de K1 = −0,8 (frente 5); único respaldo del umbral fijo. **Prioridad 1.**
- ⭐ **Zaksek et al. 2013**, GSL SP 380:137–160, `10.1144/SP380.5` — la vía *"computer-based"* de
  control de nube que Coppola señala (frente 4).
- Wright et al. 2004 MODVOLC, `10.1016/j.jvolgeores.2003.12.008` — validación global de los umbrales.
- Tramutoli 1998/2005 (RAT/RST) — origen de la máscara de exclusión y de la referencia temporal de
  Aveni. Leys et al. 2013, `10.1016/j.jesp.2013.03.013` — el 3·MAD de la referencia mensual.
- Coppola et al. 2012 (radiant density) — `c_rad`, que no calculamos.

---

## 7. Qué NO dicen, contra lo que se les atribuye

En `BIBLIOGRAPHY_SYNTHESIS.md` §"Detalle algorítmico Coppola 2016a" (l. 53-70) **todo lo afirmado es
textualmente correcto**; el problema es lo que **omite**, y las tres omisiones son las tres
divergencias vivas:

1. **"ROI1 = 5×5 km summit"** (l. 64) — omite *"consists of a **box** (5 × 5 km) centred on the
   volcano's summit"* y que es **la misma para todos**. Así leído, un `inner_radius_km` circular de
   3 a 20 km parece compatible (C2).
2. **"Segunda pasada refina pixeles adyacentes"** (l. 62) — omite la cláusula del mecanismo
   (*"eliminate all of the 'active' pixels already detected"*) y la frase de Test 1
   (*"subsequently discarded (unsuitable)"*). Con esa omisión, el "mislabel" de S115 era casi
   inevitable (C1).
3. **"VRP = Σ VRP_pix del clúster"** (l. 67) — trae Eq. 7 y 8 pero **no Eq. 6**, la que define el
   fondo como la media de los píxeles *que rodean* al activo. Sin ella, un fondo autorreferente no
   choca contra nada escrito (C3).

Y una atribución sin respaldo: **que MIROVA NRT es algorítmico puro, sin supervisión humana**
(memoria `feedback_mirova_no_human_supervision`). Coppola dice lo contrario para el archivo:
*"a visual inspection of the images allows the quality of each acquisition to be assessed, and
cloud-affected data to be discarded (a posteriori)"* (l. 364-67) y *"a human-based or computer-based
procedure should be carried out"* (l. 610-13). Campus 2022 lo confirma por contraposición: para NRT
**deliberadamente** apagan esa supervisión y lo declaran como elección de experimento. Lo correcto:
**el NRT no supervisado es un caso de uso que el canon prueba, no la definición del sistema.**

---

## 8. Lo que rinde

1. **Reabrir GAP #A** (C1) con la cadena de las tres citas: es el único gap de fidelidad **literal**
   que queda en la detección.
2. **Auditar el eje geométrico del ROI1** (C2): caja vs círculo, 5×5 fijo vs 3–20 por volcán. A82
   quedó rebajada en S124 justamente porque este eje nunca se miró.
3. **Máximo diario en la auditoría de paridad, no en el pipeline** (C4). No toca `pipeline/`.
4. **La corona tiene respaldo textual** (C3, Eq. 6): si el 2×2 dice no-adoptar, que sea por el dato,
   no por "no está en el paper".
