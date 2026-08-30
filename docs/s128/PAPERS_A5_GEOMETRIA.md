# A5 · Geometría de píxel y resampleo — lectura de fuentes

Fuentes: `THESIS_MASSIMETTI.pdf` (204 pp.), `JPSS_ATBD_VIIRS_Imagery_RevE.pdf`,
`VIIRS_L1B_UserGuide_Aug2021`, `JPSS_VIIRS_SDR_Radiometric_ATBD_RevC` y —por necesidad—
`campus2022_sensors_22_1713.pdf`. Páginas del PDF salvo aviso.

## Veredicto

**Sí hay un documento que describe la grilla de MIROVA, pero NO es Massimetti: es Campus et
al. 2022.** Y describe la grilla **centrada en la cumbre**, no anclada a una esquina. La
esquina suroeste que medimos en el archivo GeoTIFF es, casi con certeza, una convención de
exportación, no la geometría interna de MIROVA.

## 1. La grilla sí está documentada — Campus et al. 2022, p. 7

> "The NRT processing chain is made of 4 successive steps: (i) download; (ii) resampling;
> (iii) hot-spot detection and (iv) calculation of the VRP." (p. 7)

> "Resampling is performed in a UTM 51 × 51 km grid, centered on the volcano summit
> (consistent with MODIS MIROVA images) by keeping the nominal resolution of 750 m. This
> results in matrices of 67 × 67 pixels rather than 51 × 51 pixels obtained from MODIS
> (Figures 2 and 3)." (p. 7)

Esto **confirma nuestra medición en las formas y la refuta en el ancla**:

- Las formas coinciden **exactamente**: `01_grilla_real.json` da 51×51 (MODIS), 67×67
  (VIIRS750), 134×134 (VIIRS375 = 2×67, el I-band a mitad de paso). Es la grilla del paper.
- El resampleo es un **paso propio y explícito** de la cadena NRT, anterior a la detección.
  Nosotros no lo tenemos (`ENABLE_UTM_REGRID = False`, verificado importando
  `pipeline.profile` con `VRP_PROFILE=mirova_equivalent`).
- Pero el paper dice **"centered on the volcano summit"**. Un cuadro centrado de 51 km
  (MODIS) contra uno de 50,25 km (VIIRS, 67×750 m) daría desacuerdo **simétrico** de 375 m
  por lado. Medimos 0 m al oeste/sur y ~500 m al este/norte.

La explicación está en el propio JSON: el CRS de los TIF es **`EPSG:4326`**, no UTM. Los
GeoTIFF publicados son la grilla UTM **reproyectada** para despliegue web; al warpear, el
origen del ráster queda en la esquina inferior-izquierda del extent y el número de columnas
se conserva, así que el borde NE "flota" según el paso de cada sensor. Eso da justo el patrón
observado. **Operacionalmente: la esquina SW compartida es artefacto del export; para
replicar MIROVA hay que centrar en la cumbre, no anclar la esquina.**

## 2. Lo que Massimetti NO dice (negativo establecido)

Barrido sobre las 204 páginas del PDF y sobre `_thesis_full.txt`: `nadir` **0** ocurrencias;
`bow-tie`/`bowtie` **0**; `resampl` sólo para Landsat-8 30 m → 20 m (p. 138); `UTM` sólo para
tiles Sentinel-2 100×100 km (p. 37); `grid` sólo "the same geometric grid" S2/L8 (p. 139).

**La tesis no describe la grilla de MIROVA: ni tamaño, ni proyección, ni ancla, ni método de
remuestreo.** Tampoco es —contra lo que se le atribuye— la tesis que documenta la adaptación
a VIIRS: es una tesis sobre SWIR de alta resolución (Sentinel-2/Landsat-8) y ella misma
delega, *"The same MIROVA algorithm has been recently applied to the VIIRS imagery dataset
(Campus et al., 2022)"* (p. 138).

Lo que la tesis **sí** aporta es el área de píxel MODIS como constante:

> "where PIXEL is the pixel size of **1 km2** for the MODIS MIR image, the constant 1.97 ×
> 10⁷ represents the Wooster's empirical coefficient…" (p. 90; página impresa 82)

y el error del método: *"with an error of ca. 30%"* (p. 139), coherente con Laiolo 2026.

## 3. Bow-tie y área efectiva — ATBD Imagery RevE

> "At nadir, three detector footprints are aggregated to form a single VIIRS 'pixel.' …
> **At 31.59 degrees in scan angle, the aggregation scheme is changed from 3x1 to 2x1. A
> similar switch from 2x1 to 1x1 aggregation occurs at 44.68 degrees.** The VIIRS scan
> consequently exhibits a pixel growth factor of only **2** both along track and along scan,
> compared with a growth factor of **6** along scan which would be realized without the use
> of the aggregation scheme." (p. 21)

También (p. 21): el HSR del I-band debe ser "no greater than **400 m at nadir and 800 m at
the edge of the scan**"; el barrido llega a **56°** por lado. Figura 7 (p. 22): HSI del
I-band **371 m** a nadir, **606 m** en la zona agregada-2, **800 m** en el borde.

Bow-tie deletion, verbatim (p. 23):

> "An additional reduction in the bowtie effect is achieved by **deleting 4 of the 32
> detectors** from the output data steam for the middle (Aggregate 2) part of the scan and
> **8 of the 32 detectors** for the edge (No aggregation) part of the scan."

El L1B UserGuide (§2.3) agrega que la eliminación es a bordo y que los píxeles borrados vienen
marcados (`65533 = Bowtie_Deleted`). Campus 2022 Tabla 1 (p. 6) cierra el contraste: **VIIRS
0,75–0,375 km a nadir → 1,5–0,75 km en el borde; MODIS 1 km → 4 km en el borde.**

## 4. ¿El área nadir fija es defendible?

**Sí, y con respaldo directo.** Campus 2022 Eq. (1), p. 7:

> "VRP = ΔL_MIR · 1,97 × 10⁷ · A_pix … where **A_pix is the pixel surface in km² (equal to
> 0.5625 for VIIRS M-bands)**."

0,5625 km² = 750 m a nadir al cuadrado, **constante**, sin sec³. Es exactamente nuestro
número: nuestro `k` de VIIRS750 es 11.081.250 = 1,97e7 × 0,5625. Lo mismo con MODIS = 1 km²
(tesis p. 90) y con I-band = 0,140625 km². El área constante **no es licencia nuestra: es la
consecuencia lógica del paso (ii) resampling** — remuestreada a una malla de paso fijo, la
celda tiene área fija por construcción. S102/S103 acertó.

## 5. En qué nos contradice

1. **No filtramos por ángulo cenital y MIROVA sí.** Massimetti p. 138: *"VRP data were
   filtered to include exclusively i) nighttime MODIS and VIIRS alerts; ii) MODIS and VIIRS
   image with a **Zenith scanning angle < 50°**"*. Verificado en nuestro código: no existe
   ningún gate de cenit. `MAX_SENSOR_ZENITH_DEG = 70.0` (`pipeline/scan_geometry.py:73`) sólo
   vive dentro de la rama sec³, hoy **código muerto** porque `nadir_fixed=True` retorna antes
   (`scan_geometry.py:140` y `:218`; ambos flags `= True` en `pipeline.profile`).
   **Es lo más grave del racimo**: MIROVA puede darse el lujo de un A_pix constante porque
   (a) remuestrea y (b) **bota las pasadas de cenit alto**, donde la huella real es 2× (VIIRS)
   o 4× (MODIS) la nominal. Nosotros tomamos el lujo sin pagar ninguno de los dos peajes. El
   dato ya está leído y persistido (`process_viirs.py:502`, `process_modis.py:261`,
   `process_viirs_mod.py:360`) — el gate cuesta una línea.
2. **No remuestreamos** (paso ii de la cadena de 4 pasos, ausente en nosotros).
3. Nuestro docstring dice "grid UTM **50x50** km" (`scan_geometry.py`, docstring de
   `modis_pixel_areas`). El paper dice **51 × 51**. Nit de "declarado ≠ efectivo".

## 6. Citas que no tenemos

- Cao et al. 2017, *VIIRS SDR User's Guide v1.3*, NOAA Tech. Report NESDIS 142a — ref. [45]
  de Campus 2022 para el esquema de agregación. No está en `documentacion/`.
- Coppola et al. 2022, *Thermal unrest of a fumarolic field tracked using VIIRS imaging
  bands: La Fossa*, Front. Earth Sci. 10:964372, doi 10.3389/feart.2022.964372 — canon MIROVA
  sobre el I-band 375 m, pertinente a nuestro régimen sub-MW.
- Shevchenko et al. 2021, Front. Earth Sci. 9:680051, doi 10.3389/feart.2021.680051.

## 7. Lo que queda sin respuesta documental (alimenta D17)

- **Método de remuestreo**: ni Campus ni la tesis dicen si es vecino más cercano, bilineal o
  agregación por celda. Decide si el remuestreo *suaviza* el píxel caliente (bilineal ⇒ ΔL
  menor, anomalía repartida) o lo *preserva*. Sin esto no se puede cablear
  `get_grid_center()` con fidelidad.
- **Zona UTM y ancla exacta**: "centered on the volcano summit" no dice qué coordenada de
  cumbre ni si la celda se alinea a un múltiplo redondo de la zona.
- **El residuo de ~500 m NE** del archivo TIF no lo explican los tamaños documentados (51 km
  vs 50,25 km predicen 750 m). Chequeo barato pendiente: leer `transform`/`res` de un TIF por
  sensor y confirmar que el paso no es 1000/750/375 m exactos, lo que probaría el warp.
- **Qué hace MIROVA con los huecos de bow-tie**: el L1B UserGuide dice que "are removable
  through interpolation … as part of the geolocation process" (§2.3), pero ningún documento
  MIROVA dice si los interpola, los enmascara o los ignora.
