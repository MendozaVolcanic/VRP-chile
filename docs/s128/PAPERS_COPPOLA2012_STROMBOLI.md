# Coppola et al. 2012 — *Radiative heat power at Stromboli volcano during 2000–2011*

**JVGR 215–216, 48–60** · doi:10.1016/j.jvolgeores.2011.12.001 · canon MIROVA (Torino + Firenze).
PDF en `documentacion/`. Páginas citadas = **de revista** (48–60), no del PDF.

---

## Resumen

**El método de interpolación del remuestreo NO está en el paper.** El paso existe y está
descrito, pero el algoritmo nunca se nombra: *interpolation*, *nearest*, *bilinear* y
*cubic* no aparecen en ninguna de las 14 páginas (verificado con `grep -i` sobre el texto
extraído). Tampoco declara zona UTM, datum ni anclaje de la celda. Da sólo el **efecto**,
y ese efecto fija la aritmética:
*«the original MODIS level1b data, falling within a mask (50 × 50 km) centred over the
summit of Stromboli, has been cropped and resampled into UTM grid of 1 km in cell size.
This means that hot-spot pixel whose area was 2 km², in the original image, became two
equal area 1 km² pixels in the resampled image»* (p. 50, §3.2). Dos celdas de **igual
área** que heredan la radiancia de la original: eso es **replicación** (vecino más
cercano), no promedio con vecinos fríos. Negativo bien establecido para el método
explícito; positivo fuerte para la consecuencia.

La consecuencia es lo que nos importa. Si el píxel caliente se replica, la suma
`ΔL4 = Σ(L4alert − L4bk)` crece con el ángulo de barrido en la misma proporción en que
crece el área proyectada. Con `VRP = 1,89×10⁷ × ΔL4` y coeficiente fijo, MIROVA
**recupera el área off-nadir por vía geométrica**, no por un factor sec³ multiplicativo.
Nosotros usamos área nadir fija y **no** remuestreamos (`ENABLE_UTM_REGRID = False`,
verificado leyendo `pipeline.profile`, no el YAML), así que perdemos exactamente ese
factor. Es el mecanismo físico detrás del 0,796 → 0,570 medido en S128.

Segundo hallazgo, igual de operativo: el remuestreo es el **paso ii** y va después del
**paso i**, la eliminación del *bow-tie* (Liu et al. 2008). Nosotros no hacemos ninguno de
los dos (`grep -i bowtie pipeline/process_modis.py` → cero). Sobre 25° de barrido los
barridos adyacentes se solapan, así que **regridear sin de-solapar primero duplicaría**
píxeles calientes. Van juntos o no van.

Tercero: sí aplican corte inferior, y es de **1 MW** — veinte veces nuestro piso MODIS.

---

## 1. Qué mide y con qué fórmula (p. 49–53)

Seis pasos (§3, p. 49): *«(i) removal of bow–tie effect, (ii) resampling into UTM
projection, (iii) detection of the thermal-anomalous pixel/s, (iv) calculation of the
apparent anomaly at 4 μm (ΔL4STR), (v) subtraction of the residual background and
estimation of L4VOLC, (vi) estimation of the volcanic radiative power (VRP)»*.

- **Eq. 1a** (p. 51): `ΔL4STR = Σ₁^nalert (L4alert − L4bk)`.
- **Eq. 2** (p. 52): `L4VOLC = ΔL4STR − ΔL4SAL` — resta de un **control no volcánico**, la
  isla Salina a 42 km, procesada con los mismos pasos i–iv.
- **Eq. 3** (p. 52): `VRP = 1,89×10⁷ × L4VOLC` (Wooster 2003), *«±30% when the target
  temperature is higher than 600 K»*.
- `c_rad = VRP_ave / ER` (p. 53) = *«1.75 ± 0.65 × 10⁸ J m⁻³»*. Origen del coeficiente.

## 2. Decisiones de diseño y su CRITERIO

- **Bow-tie (i, p. 50)**: *«may thus produce a double counting … that may cause an
  overestimate of the total thermal anomaly»*.
- **Remuestreo (ii, p. 50)**: *«This leds the radiance of a potential subpixel hotspot to
  be integrated over a variable area, according to the viewing geometry. To avoid this
  problem…»*; a 55° *«the pixel samples approximatively 10 km² (2 × 4.8 km)»*. Y el
  alcance, la frase que más nos falta: *«In the next steps any processing is applied to
  these resampled pixels»* — detección, fondo y kernel corren **sobre la grilla**.
- **Detección (iii, p. 51)**: umbral NTI **adaptado estacionalmente** más un rescate — si
  ninguno lo supera, *«the pixel having the maximum NTI within a 3 × 3 pixels box, around
  the summit … is flagged as alert (potentially)»*, porque el umbral fijo *«fails to detect
  some small anomalies»*.
- **Fondo (iv, p. 51)**: *«the arithmetic mean of the 8 pixels surrounding the alerted
  one/s, which are not contaminated by clouds»*; *«night time pixels are flagged as cloudy
  if the single condition BT12 < 265 K is satisfied»*.
- **Salina (v, p. 51)**: el criterio es que ese fondo de 8 vecinos falla en islas chicas y
  empinadas, porque los vecinos *«are likely affected by an important topographic thermal
  gradient»*. Es **nuestro A69 escrito en 2011**, y la respuesta no fue un gate sino un
  control externo.

## 3. Nuestros frentes abiertos

- **Frente 3 (grilla)**: resuelto en lo esencial. Máscara **50 × 50 km centrada en la
  cumbre** (no 51 × 51, no anclada al borde oeste), celda 1 km, UTM, sin zona ni datum, sin
  método de interpolación.
- **Frente 1 (piso)**: corte duro — *«we prefer to apply a cut-off to L4VOLC at 1 MW to
  exclude these noisy data from further analysis»* (p. 52), sobre el ~90 % del dataset,
  atribuido a *«overpasses during cloudy conditions or under extreme viewing geometry»*.
  Semántica de **cero, no de descarte**: *«by assigning a value equal to 0 to any
  overpasses which falls below the noise threshold (VRP < 1 MW), and including these in the
  monthly average»* (p. 55) — idéntica a `pipeline/store.py:466-470`. Solo cambia el número.
- **Frente 4 (nube)**: BT12 < 265 K aplicado **al anillo de fondo** — el mismo rol que
  nuestro `CLOUD_MASK_BT_K` (`pipeline/process_modis.py:506`, `bg_cloud_free`), hoy en
  `0.0`. Coppola usa 265 K, no 260.
- **Frente 6**: publican **por pasada**, como nosotros; el máximo diario no aparece — lo
  que agregan es el promedio mensual `VRPm`. **Frente 9**: ±30 % sobre 600 K, igual que
  Laiolo 2026.

## 4. En qué nos contradice

1. **El piso.** 1 MW contra nuestros **0,05 (MODIS) / 0,02 (V375) / 0,15 (V750) MW**
   efectivos — verificado con `VRP_PROFILE=mirova_equivalent python -c "import
   pipeline.profile"`; defaults en `pipeline/profile.py:121-123`. **El brief de S128 dice
   que el piso «hoy es un no-op»: no lo es.** Nuestro artefacto topográfico (0,04–0,06 MW)
   cae justo en el borde del piso MODIS y 1,3 órdenes bajo el corte de Coppola.
2. **El área.** Nadir fija sin regrid pierde el factor que ellos recuperan replicando.
3. **El bow-tie.** No lo removemos; ellos sí, y **antes** de remuestrear.
4. **Fondo autorreferente (frente 2).** El fondo son los 8 vecinos del alertado, que nunca
   se incluye a sí mismo. Pero el paper **no dice** que se excluyan los *otros* píxeles
   alertados del anillo: `ENABLE_TEST1_K1_BG_EXCLUDE = False` no queda ni contradicho ni
   respaldado.

## 5. Qué cita que no tenemos

- **Liu, Wen, Dong & Dai (2008)**, CISP 2008, 663–667, **doi:10.1109/CISP.2008.404** — el
  algoritmo del paso i. **La que más falta nos hace.**
- **Nishihama et al. (1997)**, *MODIS Level 1A Earth Location ATBD v3.0*, SDST-092, NASA
  GSFC (sin DOI) — geometría de píxel.
- **Wright et al. (2002a)**, RSE 82, 135–155 — **origen del NTI** (frente 5).
- **Giglio et al. (2003)**, RSE 87, 273–282 — el fondo de 8 vecinos y el BT12 < 265 K.
- **Piscopo (2010)**, tesis doctoral, Torino, 119 pp. — el detalle que el paper comprime.

## 6. Qué NO dice, contra lo que se le atribuye

- **No dice el método de interpolación.** Aveni 2023 lo cita como la referencia del
  remuestreo; el paper describe el paso, no el algoritmo.
- **No filtra por ángulo cenital.** Ni 40° ni 50°: no hay corte angular en ninguna parte
  (`grep -i "zenith|scan angle"` da solo descripciones de geometría). El remuestreo **es**
  su tratamiento del ángulo; los cortes de Massimetti y Aveni son posteriores.
- **No es MIROVA.** Es de 2012, sobre **un** volcán, con un control externo que un sistema
  global no puede tener, y con **inspección visual manual**: *«we conducted a visual
  inspection of the images … to select only cloud free data»* (p. 53).
- **El corte de 1 MW es de análisis, no de producto** — *«to exclude these noisy data from
  further analysis»*. No contradice el rechazo del corte de 2 MW de Coppola 2014.
- **La energía acumulada (1,8 × 10¹⁴ J, p. 58) es análisis, no producto**: sale *«by
  integrating the VRPm over the 12 analysed years»* — integra el **promedio mensual con
  ceros incluidos**, no la serie de pasadas.
