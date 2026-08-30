# Steffke & Harris 2011 — la taxonomía del fondo

Steffke A.M. & Harris A.J.L. (2011), *A review of algorithms for detecting volcanic hot spots in
satellite infrared data*, Bull. Volcanol. 73:1109–1137, DOI 10.1007/s00445-011-0487-7. PDF en
`documentacion/`. Páginas = página de revista (PDF + 1108).

⚠️ **A9**: Harris es HIGP Hawái / Clermont, **NO canon MIROVA**. Vale como comparativa
*independiente* de métodos sobre los mismos datos; donde difiera de Coppola, manda Coppola.

---

## 1. ⭐ La taxonomía del fondo

El eje de clasificación **es el del fondo**:

> «Depending on whether a hot spot detection technique operates by assessing a pixel's radiance (or
> temperature) in a spectral, spatial or temporal space, hot spot detection methods can be divided
> into three categories: (1) fixed threshold, (2) contextual, or (3) temporal.» (p. 1112)

| Familia | El "fondo" es | Fundacional | Trade-off documentado |
|---|---|---|---|
| **Fijo (espectral)** | Ninguno espacial: el propio píxel vía ΔT o NTI | MODVOLC | Global, sin datos extra, ~3 % FP; **ciego a lo sutil** |
| **Contextual (espacial)** | Vecinos y/o región no-volcánica de la escena | VAST | Sensible, local; **FP hasta 68 %** |
| **Temporal** | Media y σ del **mismo píxel** en el archivo | RAT/RST | Mejor en sutiles; 22 TB/año global, geoloc. <1 km |

Híbridos entre vértices: Okmok (ctx+temporal), MYVOLC (fijo+ctx), MODVOLC2 (fijo+temporal), Fig. 2
p. 1112.

**La familia contextual tiene tres sub-definiciones, y las tres son nuestras**:

- **Doble región de escena** (= dual-ROI): VAST «defines two regions: a central volcanic region
  (containing the target volcano) and non-volcanic region surrounding the volcanic region» (p. 1114).
  Umbral = **máximo del fondo**, no N·σ: «if ΔT_diff for any pixel in the volcanic region exceeds
  the maximum encountered in the non-volcanic region, then the pixel is flagged as anomalous»
  (p. 1114).
- **Kernel de 8 vecinos** (= `local_kernel_bg`): «the difference in ΔT between a pixel and the mean
  ΔT of its eight neighboring pixels» (p. 1114).
- **Anillo regional con N·σ** (versión GOES): «any pixel with ΔT that was greater than the ΔT mean
  plus **3.3σ** for a 5-pixel-wide box surrounding a 10×10 pixel target zone» (p. 1113).

El trade-off nuclear:

> «Local precision and subtlety of the hot spot that can be detected by the algorithms have an
> inverse relationship with the global applicability. If an algorithm runs effectively on a global
> scale, it will have a high threshold which limits the number of false detections but precludes
> detection of subtle anomalies.» (p. 1131)

Tabla 10 (p. 1131), 5 criterios 0/1: **empate 3-3-3**. Tabla 11 (p. 1132): VAST 73 % correcto /
21 % falso; MODVOLC-MODIS 64 % / 3 %; RST 59 % / 6 %.

---

## 2. ⭐ El fondo autorreferente — APOYA, con dirección nombrada

> «RST could be improved by insuring that the mean and standard deviations are for periods when no
> activity is occurring. **An increase in activity at the volcano will result in the mean being
> higher than ambient and therefore will not allow more subtle anomalies to be detected.**» (p. 1132)

Es nuestro hallazgo S126 con respaldo independiente y **el signo correcto**. En el eje espacial la
exclusión es *arquitectural*: VAST separa volcánica de no-volcánica en el paso 2 (p. 1114) y los
píxeles calientes nunca entran al pool del umbral. Nosotros lo tenemos apagado en las dos caras —
verificado con `VRP_PROFILE=mirova_equivalent python -c "import pipeline.profile as p;
print(p.ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK, p.ENABLE_TEST1_K1_BG_EXCLUDE)"` → `False False`.

**Matiz**: atribuye la consecuencia a la **detección**, no a la **magnitud**, y no cuantifica factor
alguno. Apoya la dirección; **no cuantifica nuestro 0,73**.

El espejo: en Stromboli el fondo era mar homogéneo y «the threshold was often too low when applied
to the island, so that when the island was hotter than the surrounding ocean, we simply detect the
presence of the island» (p. 1125). Un fondo mal elegido rompe en las dos direcciones.

---

## 3. Terreno difícil — nuestra A69, escrita en 2011

> «False positives also frequently occurred at lower elevations on the volcano. At these locations,
> **the lower elevation pixels are warmer than the adjacent higher, cooler (sometimes snow covered)
> summit region and are therefore flagged as anomalous**. Again these false positives would be
> minimized if the ΔT image was used.» (p. 1124)

> «Reintroducing the ΔT technique would also filter out the occurrence of false detections that
> occurred due to strong temperature contrasts at boundaries between two different land types (i.e.,
> **snow vs. lava fields** and island vs. sea).» (p. 1132)

ΔT = T_MIR − T_TIR es el hermano no normalizado del NTI y cancela el gradiente igual. **A69 tiene 15
años de respaldo independiente.** Dos advertencias nuevas: emisividad diferencial MIR/TIR mete hasta
8 °C de ΔT espurio (p. 1126); y el ΔT **se invierte** en focos grandes — «ΔT will begin to decline
once a hot spot reaches a sufficiently large size» (p. 1115) — el NTI hereda esa inversión.

Contrapunto: el fondo frío **ayuda**. RST ganó en Augustine porque «using the means of the
very-low-temperature background pixels it is easier to detect lower temperature thermal anomalies»
(p. 1130). Fondo frío bueno, *gradiente* malo: nuestros nevados tienen los dos.

---

## 4. ⭐ Desacuerdo entre métodos — reencuadra nuestro 0,73

Sobre la **misma escena**, dos algoritmos publicados difieren por **factor ~2** en potencia radiada:

> «MODVOLC detected six (60 %) of these pixels, which accounted for 797 Wm⁻² or 88 % of the total
> radiative power loss. RST detected four (40 %) […] 616 Wm⁻² or 68 % of the total power loss.»
> (Etna, anomalía intensa, p. 1134)

> «nondetection of 60 % of the pixels by MODVOLC resulted in an underestimation of the total
> radiative power loss by 50 %, **a result of the radiance being distributed more evenly across the
> entire anomaly in the low intensity case**.» (Augustine, domo, p. 1134 — RST recuperó 100 %)

Sub-reporte por píxeles perdidos: 12–32 % en régimen intenso, **50 % en baja intensidad**, porque la
radiancia va repartida y no en un núcleo. **Nuestro régimen es el segundo.**

Conecta directo con el código: el VRP que publicamos es **suma sobre los píxeles detectados del
clúster** — `pipeline/clustering.py:113`, `cluster["vrp_mw"] = float(np.sum(vrp_per_pixel[ii, jj]))`.
Cada píxel no detectado se resta de la magnitud. Nuestro 0,73 (perder ~27 %) cae **dentro** del rango
que dos algoritmos maduros producen entre sí sobre la misma escena: no es un bug, es la magnitud
normal del desacuerdo entre definiciones de fondo.

Dispersión en detección, régimen débil (Tabla 7, p. 1128, píxeles Augustine): VAST 18 %, MODVOLC
41 %, RST 81 % — **factor 4,5 entre métodos** en la misma erupción.

---

## 5. MODVOLC y los contextuales

NTI, Eq. 4 (p. 1114): `NTI = (L22 − L32)/(L22 + L32)`, umbral global **−0,8** nocturno, elegido
empíricamente para minimizar FP en búsqueda global. Costo medido: una fumarola de 4 m a 950 °C da
«a band 22 radiance of 0.33 Wm⁻² sr⁻¹ μm⁻¹, and a band 32 radiance of 8.5 Wm⁻² sr⁻¹ μm⁻¹, hence, an
**NTI of −0.92**» (p. 1128) — invisible bajo −0,8; en Stromboli 2006 costó el 85 % de las imágenes
(Tabla 6, p. 1127).

**Nos toca directo**: nuestro piso absoluto es el mismo −0,8 —
`pipeline/profiles/mirova_equivalent.yaml:43` (`nti_k1_night: -0.8`), aplicado en
`process_modis.py:602`, `process_viirs.py:952`, `process_viirs_mod.py:582`. Es el umbral **global**
de MODVOLC operando en un sistema **local** de 11 volcanes: el desajuste exacto que el paper señala.
MODLEN lo bajó a −0,83 y le agregó paso contextual de 8 vecinos (p. 1114); el paso contextual ya lo
tenemos (`enable_dnti_dual_roi`), el piso absoluto nunca lo revisamos.

**No evalúa MIROVA**: MIROVA es 2016; Coppola aparece una vez, como «a regional adjustment to the
NTI […] for Piton de la Fournaise» (p. 1114). **No citable como evaluación independiente de MIROVA.**

---

## 6. Régimen de baja magnitud

No usan MW ni proponen piso de VRP. Su piso es el del ground truth manual, y es físico:

> «A pixel was considered to be anomalous if the pixel-integrated temperature was elevated by ≥5 °C
> above its surrounding (non-anomalous) pixels. In order to elevate a 1-km pixel 5 °C above a
> background temperature of 20 °C, the sub-pixel hot spot must be greater than 2.1×10⁴ m² (for a
> 100 °C source) or 5,000 m² (for a 500 °C source).» (p. 1119)

**Frente 1**: **no apoya** un piso de magnitud. Apoya que bajo ~5 K sobre el fondo la verdad de
referencia deja de ser confiable — argumento de *incertidumbre*, no de *descarte*.

---

## 7. Contradicciones, silencios y citas

**Nos contradice**

1. **Su marco FP↔detección no es comparable.** Benchmark = inspección manual con corte de 5 K: toda
   anomalía real bajo ese corte es **FP por construcción**. Nuestra A54 midió que ~95 % de nuestros
   "FP" son físicamente reales. Sus tasas de FP no son las nuestras.
2. **Exige supervisión humana**: «manual checking should always be completed» (p. 1135) — contra
   nuestro clon NRT algorítmico puro. Es Harris, no MIROVA (A9); A76 ya documentó que MIROVA sí
   limpia a mano su producto per-volcán.
3. **El multiplicador σ no es sagrado**: 3,3σ (p. 1113) vs. nuestros 5σ summit / 10σ scene.
4. **Descarta la familia temporal por costo** (22 TB/año global, p. 1131): para 11 volcanes **no
   aplica**. La familia temporal sigue abierta y el paper no la cierra.

**Qué NO dice**

- **No define ningún fondo en km.** Todo VAST es en píxeles (30×30, 25×25/20×20, 10×10 + anillo de
  5 px). **Sin respaldo acá para nuestro anillo 5–25 km.**
- **No estudia nevados de altura.** Islas mediterráneas y una isla de Alaska. La frase de nieve
  (p. 1124) es una observación sobre flancos del Etna: valida el diagnóstico, no un fix.
- **No enmascara nubes algorítmicamente**: pre-selecciona escenas despejadas a mano (Tabla 3,
  p. 1113) y recomienda un test de piso TIR, **`T4 > −10 °C`** (Tablas 12–13, p. 1133). Lo más
  concreto que hemos leído para el frente 4.
- **No reporta VRP ni MW.** Usa Kaufman et al. (1998) Eq. 5, `E_f = 4,34×10⁻¹⁹ (T_h⁸ − T_b⁸)`
  (p. 1134): aproximación T⁸, no Wooster MIR. **Sin calibración cruzada.**
- **Higiene**: «NTI ≥0.8» (p. 1114, debe ser ≥ −0,8); atribuye MODLEN a «Kervyn et al. (2008)»,
  que en la lista (p. 1136) es el paper de topografía ASTER-vs-SRTM, no MODLEN (Kervyn 2006); dos
  ecuaciones numeradas Eq. 4; llama «MIR (AVHRR band 4)» al TIR; y discrepa consigo mismo (1.084
  píxeles en p. 1120 vs 1.065 en Tabla 4). **Confiar en las direcciones, no en el tercer dígito.**

**Citas que no tenemos** (el paper casi no trae DOI)

| Ref | Dato | Frente |
|---|---|---|
| Higgins & Harris (1997), *Comput Geosci* 23(6):627–645 | VAST: doble región = ancestro del dual-ROI | 2 |
| Harris et al. (2001), *Int J Remote Sens* 22(6):947–967 | El 3,3σ sobre anillo — **origen real del N·σ**, no Wright 2002 | 5 |
| Tramutoli (1998), EUROPTO, pp. 101–113 | RAT: fondo temporal per-píxel | 2, 6 |
| Pergola, Marchese & Tramutoli (2004), *Remote Sens Environ* 93:311–327 | RST operacional con MIR en Etna | 2 |
| Koeppen, Pilger & Wright (2011), *Bull Volcanol* | **MODVOLC2** = fijo + temporal | 2, 6 |
| Kervyn et al. (2006), IAMG, Liège | MODLEN: NTI −0,83 + paso contextual | 1, 5 |
| Kaufman et al. (1998), *JGR* 103(D24):32.213–32.238 | Potencia radiativa T⁸ | 7 |
| **Wooster & Rothery (1997b), *Bull Volcanol* 58:566–579** | **Láscar**, ATSR 1992–1995 | nuestro |
| **Oppenheimer et al. (1993), *JGR* 98:4269–4286** | **Láscar**, térmico 1984–1992 | nuestro |
| **Francis & Rothery (1987), *Geology* 15:614–617** | **Láscar**, el primero (Landsat TM) | nuestro |

---

## Veredicto operacional

1. **Fondo autorreferente**: **apoya** la dirección (p. 1132) y muestra la exclusión arquitectural
   (p. 1114). Encenderlo se justifica como *fidelidad al diseño canónico*, no como fix cuantificado.
2. **Nuestro 0,73 es normal**: el desacuerdo entre métodos llega a factor 2 y **crece en régimen de
   baja intensidad** (p. 1134). La banda [0,5–2,0] está bien calibrada.
3. **A69 confirmada** por fuente independiente y anterior (p. 1124), misma cura, más dos
   advertencias (emisividad; inversión del ΔT en focos grandes).
4. **Piso de VRP: sin respaldo.** Incertidumbre bajo 5 K, no descarte.
5. **Accionable barato, frente 4**: `T_TIR > −10 °C` (p. 1133).
6. **Revisar `nti_k1_night = -0.8`**: umbral global en sistema local (pp. 1128, 1131).
