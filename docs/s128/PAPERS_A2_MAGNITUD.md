# S128 · Racimo A2 — MAGNITUD

Lectura profunda de las dos fuentes primarias de la magnitud VRP.

- **P1** = Coppola, Laiolo, Piscopo, Cigolini (2013), *Rheological control on the radiant density of active lava flows and domes*, **JVGR 249: 39–48**. Archivo: `documentacion/j.jvolgeores.2012.09.005.pdf`.
- **P2** = Coppola, James, Staudacher, Cigolini (2010), *A comparison of field- and satellite-derived thermal flux at Piton de la Fournaise*, **Bull. Volcanol. 72: 341–356**. Archivo: `documentacion/s00445-009-0320-8.pdf`.

Los dos son canon MIROVA (Torino, A9). Páginas citadas = numeración impresa del journal.

---

## P1 — Coppola et al. 2013 (JVGR 249:39–48)

### 1. Qué mide y con qué fórmula

El VRP no es el tema del paper: es el **insumo**. La cadena está en el Apéndice 2 (p. 46).

> «the resampled radiance at 4 and 12 μm (original MODIS band 21/22 and 32) are then used to calculate the Normalised Thermal Index (NTI) of each pixel (Wright et al., 2002)» (p. 46)

**Eq. (A.1)**, p. 46: `ΔL4 = Σ_1^{n_active} (L4active − L4bk)`

> «L4bk, is estimated from the arithmetic mean of all the pixels surrounding the active one or cluster of active pixels.» (p. 46)

**Eq. (A.2)**, p. 46: `VRP = 1.89 × 10⁷ × ΔL4`, VRP en W, ΔL4 en W m⁻² µm⁻¹ sr⁻¹.

El objeto propio del paper es la **densidad radiante**:

**Eq. (4)** p. 41: `VRP = A σ ε Te⁴` (σ = 5.67×10⁻⁸ W m⁻² K⁻¹).
**Eq. (5)** p. 41: `c_rad = VRP / TADR = σ ε Te⁴ / x`, en **J m⁻³**.
**Eq. (6)** p. 41: `c_rad = Γ* σ ε Te⁴ / h̄`.
**Eq. (7)** p. 41: `Vol = VRE / c_rad`.
**Eq. (8)** p. 44: `c_rad = 6.45 × 10²⁵ × (X_SiO2)^−10.4`, R² = 0.92, ±50 %.

**Respuesta directa a la pregunta 2**: `c_rad` es un parámetro **empírico río abajo del VRP**, en J m⁻³, que convierte energía radiada en volumen de lava. **No entra en ningún lado del cálculo del VRP** — Eq. (5) lo define como el cociente `VRP/TADR`, es decir, el VRP es su numerador, no su producto. **Frente cerrado**: no calcularlo no nos cuesta nada en magnitud.

### 2. Decisiones de diseño y su criterio

- **Resampleo**: «Pre-processing … consists in the removal of the bow-tie effect and resampling into an equal area projection with 1 km pixel size» (p. 46). El criterio es *equal area*: la grilla existe para que cada píxel valga lo mismo. Es el respaldo primario de nuestro nadir-fijo (A66) y del frente #3.
- **Umbral NTI por erupción**: «a preliminary analysis of the resulting NTI time-series is then used to define an appropriate NTI threshold which takes into account the normal fluctuation of this index due to the local and seasonal conditions» (p. 46). Criterio: el NTI es absoluto y por lo tanto sensible a geografía y estación.
- **Descarte, no corrección**: «A post processing and a visual inspection of all the images allows us to discard all the cases in which the VRP estimates are clearly affected by cloud attenuation and/or by extreme viewing geometry (with a satellite zenith > 50°)» (p. 46).
- **Suficiencia de muestra**: solo erupciones con >10 % de pasadas utilizables (p. 46).

### 3. Frentes abiertos

- **#2 (fondo)**: la Eq. (A.1) define el fondo como la media aritmética **del entorno del clúster activo** — local y con los activos fuera. No es un anillo regional.
- **#3 (grilla)**: proyección equiárea de 1 km, bow-tie removido antes de medir.
- **#4/#7 (nube y geometría)**: inspección visual manual + corte duro en zenith 50°.
- **#5 (NTI)**: umbral calibrado por caso, no global.
- **#9 (incertidumbre)**: acá nace el ±30 % (ver abajo). El ±50 % es de la **VRE** integrada, no del VRP instantáneo.

### 4. En qué nos contradice

1. **El fondo.** Nuestro `L_bg` por defecto sale del anillo regional 5–25 km (`pipeline/process_modis.py:951-954`, `L_bg_global` desde la BT mediana del anillo), y solo se vuelve local vía kernel 3×3 cuando `ENABLE_LOCAL_KERNEL_BG` **y** el flag por volcán coinciden (`process_modis.py:972`; verificado: `grep -n local_kernel_bg volcanoes.yaml` → **5 en `true`** de 11 Tier A). El paper no admite esa condicionalidad: el fondo es siempre el entorno del clúster. Apoya el frente #2 de S126.
2. **Bandas del NTI.** El paper usa 4 y **12 µm (banda 32)**; nosotros usamos banda 21 (3.929) y **banda 31 (11.03)** (`process_modis.py:73-76`). Coppola 2016a sí lista banda 31 como canal TIR, así que es evolución del método, no error nuestro — pero la fuente primaria del `k` no respalda nuestra banda.
3. **Geometría extrema.** El paper **descarta** zenith >50°. Nosotros no filtramos por zenith en ningún sensor (verificado: `grep -rni "zenith" pipeline/*.py` no devuelve ningún corte, solo lectura de `sensor_zenith` para geolocalización) y encima aplicamos área nadir fija, que a 50° **subestima** el área real. Son dos decisiones que MIROVA no toma juntas.

### 5. Bibliografía que no tenemos

- **Wright, R., Flynn, L.P., Garbeil, H., Harris, A.J.L., Pilger, E. (2002)**, *Automated volcanic eruption detection using MODIS*, RSE **82**: 135–155 — **origen del NTI, frente #5. No está en `documentacion/`.**
- **Wright, R., Glaze, L., Baloga, S.M. (2011)**, Geology **39**: 1127–1130 — la distribución de temperaturas que **justifica** aplicar Eq. (A.2) a lavas. Ausente.
- Wright, Blake, Harris, Rothery (2001), EPSL **192**: 223–233. Harris & Baloga (2009). Pieri & Baloga (1986), JVGR 30:29–45. Ausentes.
- Wooster, Zhukov, Oertel (2003), RSE 86:83–107 — **sí lo tenemos** (`documentacion/1-s2.0-S0034425703000701-main.pdf`).

### 6. Qué NO dice

- **No deriva el 1.89×10⁷.** Lo cita de Wooster 2003 y aclara que «This equation is generally used for fire radiative power estimates» (p. 46). No hay supuestos de emisividad ni de temperatura declarados en P1 para esa constante.
- **No da versiones VIIRS.** Nuestros 19.7 y 18.0 (`process_viirs_mod.py:63`, `process_viirs.py:74`) no tienen respaldo acá.
- **No dice que el VRP sea la potencia radiada por la lava.** Al contrario:

> «the “above background” radiance … is not directly correlated with the heat radiated by the “entire lava area” but, more likely, it is representative of the radiative power (± 30%) emitted by a smaller, hotter and younger portion of the lava surface (such as the active lava area at temperature equal or higher than 600 K)» (p. 46)

Y el rango de validez, verbatim: «the linearity expressed by the Eq. (A.2) is restricted to targets that have an integrated temperature comprised between ~600–1500 K» (p. 46). **Ese es el ±30 % que Laiolo 2026 declara, y su alcance es más chico de lo que se le atribuye**: es la fidelidad con que ΔL4 representa la porción >600 K, no un error contra terreno.

- **No declara ningún piso en MW** (pregunta 3). El único filtro de calidad es el par nube/geometría y el 10 % de pasadas.

---

## P2 — Coppola et al. 2010 (Bull. Volcanol. 72:341–356)

### 1. Qué mide y con qué fórmula

Compara radiancia MODIS contra cámara térmica FLIR ortorrectificada en Piton de la Fournaise (mayo–julio 2003).

**Eq. (4)** p. 349: `L4MOD,flow = Σ_1^n (L4MOD,alert) − n·L4MOD,bk`, con el fondo tomado como «the minimum BT12 recorded by the alerted pixels» (p. 349).
**Eq. (5)** p. 353: `QRflow / TADR = c_rad`.
**Eq. (6)** p. 353: `TADR/A_flow = ε σ Te⁴ / c_rad = cA`, con **ε = 0.97** (p. 353).
**Ajuste de terreno**, p. 353: `QRflow = 2.69 × 10⁷ × L4flow`, para superficies de 12 h con Te ≈ 575 K.
**Eq. (7)** p. 353: `TADR = 0.128 × L4flow`, ±40 %.
`c_rad` medido = **2.5 ± 1 × 10⁸ J m⁻³** para superficies de 6–24 h, con Te entre 500 y 625 K (p. 353).

### 2. Decisiones de diseño y su criterio

- **Umbral NTI rebajado a −0.86** (contra −0.8 noche / −0.6 día de MODVOLC), tras corregir reflexión solar diurna restando el 4.26 % de la radiancia a 1.6 µm; criterio explícito: MODVOLC «did not trigger an alert» con actividad en curso (p. 346).
- **Validación manual de las alertas nuevas**: «the validity of these alerts were manually confirmed by verifying that the pixel locations … corresponded to the volcano summit» (p. 347).
- **Corte por bow-tie**: «we decided to eliminate only alerted pixels collected at scan angles > 40°, and to correct pixels collected at scan angles between 25° and 40°» — dividiendo la radiancia sumada por 2 (p. 348). El criterio del corte no es físico sino de muestra: el corte estricto en 25° «would significantly reduce the available dataset (by about 75%)».

### 3. Frentes abiertos

- **#4 y #7**: cuantifica lo que nosotros apagamos. De 47 pasadas, «only four (17 %) acquired under clear sky and satzen <40° conditions» (p. 354). El 51 % no detectó nada por nube o ángulo.
- **#3**: el doble conteo bow-tie infla la radiancia sumada — es un argumento independiente a favor de resamplear a grilla.
- **#1 (piso)**: no da un piso en MW, pero da el equivalente en radiancia (abajo).
- **#9**: ±40 % en TADR, ~10 % en radiancia bajo condiciones óptimas.

### 4. En qué nos contradice

1. **El coeficiente.** El ajuste calibrado contra terreno es **2.69 × 10⁷**, un 42 % por encima del 1.89 × 10⁷ de Wooster que usamos (`process_modis.py:82`). No es un error de Wooster: mide otra cosa (el flujo radiativo total de la superficie de 12 h, no la porción >600 K). Pero significa que **nuestro VRP es, por construcción, un límite inferior del calor radiado**, y explica por qué nuestras medianas caen bajo MIROVA. Nota A9: el 2.48×10⁷ de Di Bella que rechazamos en S14 queda justo entre ambos.
2. **El fondo, otra vez y distinto**: acá es el **mínimo BT12 de los píxeles alertados** — o sea local, del propio clúster. Ninguna de las dos fuentes primarias usa anillo regional.
3. **Emisividad 0.97 explícita** (p. 353). Nuestro VRP TIR es Stefan-Boltzmann puro sin ε (verificado: `grep -rni "emissiv" pipeline/*.py` no devuelve ninguna constante de emisividad).

### 5. Bibliografía que no tenemos

- **Nishihama et al. (1997)**, *MODIS level 1A earth location*, ATBD v3.0 — la referencia del bow-tie.
- **Cahoon et al. (1992)**, Nature 245:812–815 — «For scan angles > 45°, more than 60% of the area viewed within a pixel is also viewed by adjacent pixels» (p. 348).
- **Wooster, Rothery, Kaneko (1998)**, IJRS 19:2585–2591, *Geometric considerations for the remote monitoring of volcanoes*.
- Wright & Flynn (2004), Geology 32:189–192.

### 6. Qué NO dice

- **No valida la ecuación de Wooster.** Nunca usa 1.89×10⁷. Lo que valida es (a) la **radiancia**: «for clear-sky conditions and moderate-to-low viewing angles (satellite zenith <40°), the satellite measurements represent ∼90% of the at-surface radiance» (p. 341), y (b) el **TADR** contra GPS, a ±40 %. Atribuirle «Coppola 2010 validó el VRP contra terreno con error X» es más de lo que dice.
- **No da un umbral de detección en MW**, pero sí el error que lo condiciona: «under optimal conditions (clear sky and satzen < 40°), a systematic error of ± 0.3 W m⁻² µm⁻¹ sr⁻¹ … is induced by atmospheric effects» (p. 351), y «at low emissions of 2–3 W m⁻² µm⁻¹ sr⁻¹ an error of ±0.3 … represents 10–15 % of L4flow,MOD» (p. 354).

**Traducción a nuestro régimen** (aritmética explícita, no del paper): con `k_MODIS = 1.89×10⁷`, un artefacto de 0.05 MW corresponde a `ΔL4 = 5×10⁴ / 1.89×10⁷ ≈ 2.6×10⁻³ W m⁻² µm⁻¹ sr⁻¹`, unas **cien veces por debajo** del error sistemático atmosférico que el propio paper declara **en condiciones óptimas**. Con `k_V375 = 18.0 × 140625 = 2.53×10⁶`, los mismos 0.05 MW son `≈2×10⁻² W m⁻² µm⁻¹ sr⁻¹`, todavía ~15× bajo ese error. Cautela: el ±0.3 es de Piton, para una suma multi-píxel y un perfil atmosférico concreto; no es un umbral publicado. Pero fija la escala: **nuestro régimen de artefacto vive muy por debajo de la incertidumbre declarada por la fuente primaria.**

---

## Verificaciones de código hechas para este informe (A48)

| Afirmación | Comando | Resultado |
|---|---|---|
| `k` MODIS = 18.9 | `sed -n '70,95p' pipeline/process_modis.py` | `WOOSTER_COEFF = 18.9` en **`pipeline/process_modis.py:82`**; comentario lo atribuye a «Coppola 2015, Eq.7» — la fuente primaria es **P1 Eq. (A.2), p. 46** |
| `k` VIIRS I04 = 18.0 / M13 = 19.7 | `sed -n '65,85p' pipeline/process_viirs.py`; `grep WOOSTER_COEFF pipeline/*.py` | `process_viirs.py:74` = 18.0; `process_viirs_mod.py:63` = 19.7 |
| No calculamos `c_rad`/TADR | `grep -rni "c_rad\|crad\|tadr\|radiant_density" pipeline/` | **cero coincidencias** |
| Fondo VRP por defecto = anillo regional | `grep -n "L_bg_global\|ENABLE_LOCAL_KERNEL_BG" pipeline/process_modis.py` | `:954` `L_bg_global` desde BT mediana del anillo 5–25 km; `:972` el kernel local exige flag por volcán |
| Kernel local en 5 de 11 | `grep -n "local_kernel_bg" volcanoes.yaml` | 5 `true`, 2 `false` explícitos, resto por defecto |
| Sin filtro de zenith | `grep -rni "zenith\|satzen" pipeline/*.py` | solo lectura de `sensor_zenith` para geolocalización/área; **ningún corte** |
| Sin emisividad | `grep -rni "emissiv\|0\.97" pipeline/*.py` | ninguna constante de emisividad |
| Área nadir fija activa | `VRP_PROFILE=mirova_equivalent python -c "import pipeline.profile as p; print(p.ENABLE_NADIR_FIXED_PIXEL_AREA_MODIS)"` | `True` (MODIS y VIIRS) |
| Wright 2002 / Wright 2011 ausentes | `grep -rni "Wright.*2002\|MODVOLC" documentacion/BIBLIOGRAPHY_SYNTHESIS.md` + `ls documentacion/` | no están |

**Comentario stale detectado de paso** (bajo impacto, no lo corregí — read-only): `pipeline/process_modis.py:77-78` sigue diciendo «actual area is computed per-pixel from scan column index … (sec^3(theta_z) correction)», contradiciendo A66/A67 (nadir fijo adoptado S102/S103). Mismo texto en `process_viirs.py:62` y `process_viirs_mod.py:51`. Instancia de «declarado ≠ efectivo» (S127 T9).
