# Schroeder et al. 2014 (RSE 143) + ATBD VIIRS 375 m v1.0 — lectura S128

**Fuentes** (`documentacion/`): `schroeder2014_rse_viirs375m_activefire_10.1016-j.rse.2013.12.008.pdf`
(RSE 143, 85–96, doi 10.1016/j.rse.2013.12.008) y `VIIRS_375m_ActiveFire_ATBD_v1.0_Dec2016.pdf`
(Schroeder & Giglio, UMD). **A9**: NASA/NOAA/UMD, no es canon MIROVA — es infraestructura
del sensor del que MIROVA *toma* los datos I-band.

## 1. ⭐ Cómo crece el píxel I-band con el ángulo (la pregunta central)

VIIRS **no** es un barredor ingenuo: agrega muestras a bordo en tres zonas (p. 86):

> «The native I-band image resolution prior to onboard aggregation is approximately
> 125 × 375 m at nadir. In the first image section (scan angles from 0° (nadir) to
> ±31.72°), every three native pixels are averaged … In the second image section (from
> ±31.72° to ±44.86°), every two native pixels are aggregated … Finally, no aggregation is
> performed in the third image section (from ±44.86° to ±56.28°) … **the effective footprint
> ranges from the nominal 375 m resolution (383 × 360 m) at the sub-satellite point to
> 795 × 784 m at a maximum scan angle of 56.28°**.» (p. 86)

El ATBD repite el esquema con bordes levemente distintos (31,59° / 44,68° / 56,06°) y aclara
que la agregación es **a bordo**: «aggregated onboard the spacecraft before the data are
transmitted» (p. 4).

**El número que importa**: 795×784 / 383×360 = **4,52×** de nadir a borde. No es 25× (sec³
sin agregar) ni 1× (constante). El bow-tie va aparte: se suprime **borrando filas** («are
replaced with fill values», p. 86), no promediando — no altera el área del píxel que
sobrevive.

Reconstruí la curva con la geometría de S-NPP (h = 829 km, ATBD p. 2) más el esquema de
agregación, validando contra el extremo publicado (modelo 4,54× vs. 4,52×). Área relativa al
nadir por **zenith de vista en superficie** (lo que persistimos en `sensor_zenith_deg`,
`pipeline/scan_geometry.py:239`):

| zenith | 0° | 20° | 35° | **36,3°** | 45° | 50° | **52,6°** | 69,7° |
|---|---|---|---|---|---|---|---|---|
| agregación | 3× | 3× | 3× | **2×** | 2× | 2× | **1×** | 1× |
| A/A_nadir | 1,00 | 1,19 | 1,72 | **1,20** | 1,70 | 2,17 | **1,44** | 4,54 |

(en negrita, los saltos de zona: el área **cae** al cambiar la agregación)

Promediando en cada bin de S128: **⟨A⟩(0–15°) = 1,03** y **⟨A⟩(35–50°) = 1,62** → razón
**1,57×**. Nuestro déficit medido (0,796 → 0,570) es **1,40×**. Sin agregación (sec³ tipo
MODIS) la predicción sería 2,27× — sobrepasa el dato.

**Conclusión: el paper APOYA la explicación del gradiente de cenit**, en su versión *con
agregación*. El residuo del 12 % es esperable: el bin no está poblado uniformemente y
MIROVA remuestrea a 1 km, no a área nadir I-band.

**Predicción falsable, gratis**: la curva es **diente de sierra**, no monótona — en zenith
≈36,3° y ≈52,6° el área **cae de golpe**. Si estratificamos el déficit en bins finos de
`sensor_zenith_deg` y aparece esa recuperación, el mecanismo queda probado por su firma, no
sólo por su magnitud. Si el déficit resulta monótono, la causa no es el área.

## 2. ¿VIIRS resuelve por hardware lo que MIROVA resuelve remuestreando?

**Parcialmente, y menos de lo que creíamos.** El paper lo plantea como atenuación, no como
solución: «The pixel size increase with scan angle … **is minimized** due to a unique data
aggregation scheme» (p. 86). *Minimized*, no *eliminated*: quedan 4,5×. Consecuencia: la
corrección faltante en VIIRS375 es **menor que en MODIS** (1,6× vs. 2,3× en 35–50°), pero
**no es cero**. Nuestro `A_pix` nadir-fijo (140.625 m², `pipeline/vrptir.py:63`, con
`ENABLE_NADIR_FIXED_PIXEL_AREA_VIIRS = True` verificado leyendo `pipeline.profile`) es
exacto sólo en la zona 1, cerca del nadir.

## 3. FRP a 375 m: **el paper no lo calcula; el ATBD sí, y con área variable**

Schroeder 2014 **se abstiene explícitamente** (p. 91):

> «we opted to **defer the retrieval of sub-pixel fire characteristics such as FRP, size and
> temperature to future studies** pending proper investigation of the complementary use of
> the dual-gain M13 channel data»

El ATBD (2016) sí lo implementa, y acá está la frase clave (p. 12):

> «Co-located M13 aggregated radiances … are used in the FRP retrieval following Wooster
> et al. [2003] … **Where A is the pixel area which varies as a function of scan angle**, σ
> is the Stefan-Boltzmann constant (5.67×10⁻⁸ Wm⁻²K⁻⁴), a is a channel-specific constant
> (VIIRS M13 = 2.88×10⁻⁹ Wm⁻²sr⁻¹µm⁻¹K⁻⁴)»

**(a)** σ/a = 5,67e-8 / 2,88e-9 = **19,69**, exactamente nuestro `WOOSTER_COEFF = 19.7` de
M13 (`pipeline/process_viirs_mod.py:63`): el coeficiente M-band **es** el del ATBD.
**(b)** El producto oficial usa **A(θ) variable**; nosotros A fija. **(c)** Divergencia
arquitectónica que no teníamos vista: **el FRP oficial de VNP14IMG no se mide en I4**. Se
mide en M13 750 m y se **reparte**: «A single pixel 750 m FRP retrieval is divided among the
number of coincident 375 m fire pixels, with each sub-pixel receiving the same resulting
value in MW» (p. 12). El producto «375 m» es detección a 375 m + magnitud a 750 m. Nuestro
`WOOSTER_COEFF = 18.0` de I4 (`pipeline/process_viirs.py:74`) **no tiene respaldo acá**:
ninguna fuente publica una constante `a` para I4, porque desaconsejan usar I4 para magnitud.

## 4. Umbrales y fondo

Contextual, ventana **dinámica** 11×11 → 31×31 hasta ≥25 % o ≥10 píxeles válidos (p. 89).
Estadístico: **media y desviación absoluta media (MAD)**, no σ. De noche:
«ΔBT₄₅ > ΔBT₄₅ᵦ + 3 × δ₄₅ᵦ; ΔBT₄₅ > ΔBT₄₅ᵦ + 9; BT₄ > BT₄ᵦ + 3 × δ₄ᵦ» (p. 89). Los válidos
**excluyen** nube, agua, píxeles de fuego de fondo y todo `QF ≠ 0` incluido el relleno del
bow-tie: **el fondo no es autorreferente** (nuestro frente 2). Nube nocturna:
«BT₅ < 265 K AND BT₄ < 295 K», con BT₄ agregado a propósito «to improve algorithm response
to fires occurring under semi-transparent clouds (e.g., cirrus)» (p. 88) — pertinente a D14.

## 5. Saturación de I4

Nominal **367 K** (p. 87, `QF4 = 9`); el ATBD baja el efectivo a «≈358 K» (p. 5). Sobre
fuegos extremos el conteo digital **se pliega** y BT₄ cae a **208 K**, piso del rango (p. 87).
I5 satura a 380 K; M13 a 634 K (p. 85) / «≈659 K» (ATBD p. 5). I4 saturado se delata porque
**BT₄ < BT₅** (p. 88). Tasa nocturna: 1 % (p. 91).

## 6. En qué nos contradice, y qué NO dice

- **Contradicción frontal** en el área: el producto oficial usa A(θ); nosotros A fija.
- **Un comentario nuestro está mal**: `pipeline/scan_geometry.py:193-195` dice que el área
  I-band agregada «varies only between ~0.32 and ~0.6 km²» (≈1,9×). Schroeder p. 86 da
  **0,138 → 0,623 km² = 4,52×**. El código está inactivo (`nadir_fixed=True`), pero el
  comentario desinformaría una decisión futura. Corregirlo.
- **NO dice** que la agregación deje el área constante. Dice *minimized*.
- **NO avala** calcular VRP en I4: lo desaconseja («sub-pixel fire characterization should
  be avoided in that channel», ATBD p. 5).
- **NO habla de volcanes, VRP, MIROVA ni nieve**: los umbrales se ajustaron sobre biomasa.
- **NO declara incertidumbre ni sesgo del FRP con el ángulo.** El 1,57× es **cálculo mío**
  sobre sus números, no una cifra publicada.

## 7. Bibliografía citada que no tenemos

- **Wolfe et al. 2013**, JGR-Atmos 118, 11508–11521, doi:10.1002/jgrd.50873 — calibración
  geométrica VIIRS. **Fuente primaria del área por ángulo. Prioridad 1.**
- **Cao et al. 2013**, IEEE TGRS, doi:10.1109/TGRS.2013.2247768 — desempeño en órbita.
- Giglio, Schroeder & Justice 2016, RSE 178, 31–41 — MODIS C6 activo.
