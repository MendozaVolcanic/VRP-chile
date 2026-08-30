# S128 · Racimo A1 — NUBES

Lectura profunda de los 4 documentos de nube del repo, contra el frente abierto #4
(*apagamos la máscara de nube; ¿qué test usaría MIROVA si filtrara?*).

**Respuesta corta a la pregunta central**: ninguno de estos documentos respalda un
umbral único de brillo absoluto como test de nube nocturno sobre tierra alta. MOD35 no
usa nada parecido: usa **diferencias entre bandas** (BTD), un **fondo de modelo**
(SFCT), y **textura espacial**. Y donde el terreno es frío y montañoso, MOD35 hace lo
que nosotros terminamos haciendo por otra vía: **apaga el test**.

---

## 1. Frey et al. 2008 — *Cloud Detection with MODIS. Part I* (JTECH 25, 1057-1072)

**(1) Qué mide.** Un árbol de tests umbral por dominio (tierra/mar/nieve × día/noche ×
polar). Cada test da una confianza de cielo despejado `F(i,j)`; se agrupan por mínimo
`G_j = min[F(i,j)]` (Ec. 1, p.1058) y se combinan como `Q = (Π G_j)^(1/N)` (Ec. 2,
p.1058) → 4 clases: *confident clear* `Q>0.99`, *probably clear* `Q>0.95*, *uncertain*
`Q>0.66`, *cloudy* `Q≤0.66` (p.1058).

**Tests NOCTURNOS con bandas MIR/TIR y sus umbrales (Tabla 1, p.1068):**

| Test | Umbral (0.0 / 0.5 / 1.0) | Escena |
|---|---|---|
| **11 µm BT ("freezing")** | 267, 270, 273 K | **sólo océano** |
| **11−3.9 BTD** | si 11−12 > +1 K: −2.0/−2.5/−3.0 K; si 11−12 < −1 K: +5.0/+4.5/+4.0 K; entre medio interpolación lineal entre −2.5 y +4.5 K | noche tierra |
| **11−3.9 BTD** | 0.7, 0.6, 0.5 K | noche nieve/hielo |
| **11−3.9 BTD** | BT11<235 K: −0.1/−0.2/−0.3 K · BT11>265 K: +1.1/+1.0/0.0 K · LI entre 235 y 265 K | noche polar tierra/nieve |
| **3.9−12 BTD** | 15, 10, 5 K | noche tierra |
| **3.9−12 BTD** | 4.5, 4.0, 3.5 K | noche nieve |
| **11−12 BTD (cirrus fino)** | función de VZA y BT11, tomada de Key (2002) | todo salvo Antártica |
| **SFCT − 11 µm** | 12 K (no árida) / 20 K (árida-semiárida), corregido por VZA y por 11−12 BTD | noche tierra |
| **7.2−11 BTD** | −8, −10, −11 K | noche tierra |
| **Variabilidad 11 µm** | contar vecinos con |ΔBT| ≥ 0.5 K sobre kernel 3×3; nube = 3, despejado = 7 | océano |

**(2) Criterio de diseño.** Explícito, y es empírico: *"the tuned thresholds are
empirical in nature"* (apéndice, p.1071); se eligen *"so that they detect the maximum
number of cloudy pixels without generating unacceptably large numbers of 'false
alarms'"* (p.1058). El algoritmo es **conservador hacia el cielo despejado**, no hacia
la nube.

**(3) Nuestros frentes.** Frente #4 y el problema altitud-vs-cirrus. Frey lo enfrenta
tres veces y las tres veces **rehúsa el test**:
- 3.9−12: *"the test cannot be used on the very coldest and driest scenes (surface
  elevations greater than 2000 m)… the test is not performed in polar night conditions
  when the elevation exceeds 2000 m"* (p.1059).
- SFCT: *"Because of large variations of SFCT in mountainous areas and large diurnal
  swings in desert regions that are not always well characterized in the gridded data,
  **the test is not performed there**"* (p.1062).
- Restauración de cielo despejado por BT11 absoluto: *"thresholds adjusted for
  elevation"* (Tabla 3, p.1071).

**(4) En qué nos contradice.** En tres cosas concretas:
- El único test de MOD35 que es un **umbral absoluto de BT** (267/270/273 K) está
  restringido a **océano** (Tabla 1, p.1068). Sobre tierra el BT absoluto sólo aparece
  como *restoral* — o sea en dirección opuesta (restaurar a despejado), y **corregido
  por elevación**. Nuestro `cloud_mask_bt_k` hacía justo lo contrario.
- El signo de la señal de nube en 11−3.9 **no es fijo**: *"The nighttime BTD may be
  either negative or positive depending on cloud optical depth and particle size"*
  (p.1059). Un umbral de un solo lado no puede capturarla.
- MOD35 **no separa cirrus alto de terreno frío de altitud con un solo canal**. Lo hace
  con 11−12 (Key 2002) y con 7.2−11 — ambas necesitan una banda extra.

**(5) Bibliografía que no tenemos.** `Ackerman et al. 1998, JGR 103(D24), 32141-32157`
(base de MOD35). `Ackerman et al. 2006, MOD35 ATBD C005, 129 pp`. `Liu, Key, Frey,
Ackerman, Menzel 2004, RSE 92, 181-194` (teoría de los BTD polares nocturnos — es LA
referencia de fondo). `Key 2002, CASPR user's guide v4.0` (umbrales 11−12 extendidos a
T baja). `Saunders & Kriebel 1988, IJRS 9, 123-150`.

**(6) Qué NO dice.** No dice nada de anomalías térmicas, volcanes ni píxeles calientes:
un píxel volcánico es para MOD35 una escena rara, no un caso tratado. Y **no ofrece un
test de nube nocturno sobre montaña alta**: lo que ofrece ahí es abstención.

---

## 2. `Platnick_MODIS_MOD06_ATBD.pdf` — portada verificada: **NO es de Platnick**

**Autores reales**: W. Paul Menzel, Richard A. Frey, Bryan A. Baum (p.1), *"Cloud Top
Properties and Cloud Phase ATBD"*, mayo 2015, versión 11, y es **Collection 6**, no C5.

**(1)** No detecta nube: la asume detectada y le calcula presión/altura/temperatura de
tope (CO₂ slicing, bandas 33-36) y fase (razones β con pares 7.3/11, 8.5/11, 11/12 µm,
p.24). *"Both algorithms are based solely on infrared (IR) measurements"* (p.3).
**(2)** Usa pares espectralmente cercanos para que la razón de emisividades se cancele
(p.25). **(3-4)** **Nos contradice por inaplicabilidad**: ninguna de sus bandas está en
nuestro set. Y su umbral de fase — *"the likelihood of finding ice clouds is less than
5% for CTT ≥ 268K, and greater than 95% for CTT ≤ 238K"* (p.45) — dice que a **270 K la
nube es agua, no hielo**: nuestro proxy `t_bg<270 K` como "firma cirrus" está mal
calibrado en su propio término. **(5)** `Baum et al. 2012`, `Holz et al. 2008`,
`Heidinger & Pavolonis 2009`, `Hu et al. 2009/2010`, `Seeman et al. 2008`. **(6)** No
dice cómo enmascarar nube en NRT ni con qué umbral. Se le atribuye ser "el ATBD de la
máscara MODIS" y **no lo es** — ése es Ackerman et al. 2006, que no tenemos.

---

## 3. Fan et al. 2015 — *Daytime LST under Cirrus* (Sensors 15, 9942-9961)

**(1)** Corrige el split-window: `ΔT_COD = k · COD` (Ec. 3, p.9947), con `k` modelo
lineal múltiple de las BT de canales MODIS 31-34 y `COD` de una LUT de reflectancia de
cirrus a **0.55 µm**. **(2)** Criterio: la profundidad óptica domina la depresión de
BT, no el radio efectivo. **(3)** Frente #4, cuantitativamente: *"the detection
limitation of the MODIS cloud mask products is approximately 0.4 for COD for the
visible bands"* (p.9944) — **hay cirrus que MOD35 no ve**, y ese residuo sesga el TIR:
*"The STD and bias reach up to 4.1 K and −12.8 K, respectively, when COD = 0.4 and
VZA = 60°"* (p.9947); a COD=0.04 el sesgo ya es −1.2 K. **(4)** Nos contradice en el
método: su corrección es **diurna por construcción** (reflectancia 0.55 µm), y el
propio paper descarta el MIR de día porque *"cannot be used to retrieve LST during the
daytime"* (p.9943). Somos sólo nocturnos: inaplicable tal cual. **(5)** `Fan et al.
[10]` (algoritmo de 3 canales **con MIR**, sí nocturno-compatible), `Xu & Sun [8]`.
**(6)** No dice cómo *detectar* cirrus de noche; corrige suponiendo que ya sabes que
hay cirrus y cuánto.

---

## 4. VNP14 User Guide v1.3 — el linaje de fuego, no el de nube

**(1-2)** Documenta la máscara de fuego, no la de nube. Dato arquitectural clave: la
clase 4 son *"cloud-covered pixels that are classified using the algorithm's **internal
cloud detection tests**"* (p.9) — el producto de fuego **no consume MOD35/VCM**, se
hace su propio test barato. **(3)** Sus tests nocturnos (Tabla 2, p.6) son
contextuales, no absolutos: `DBT45 > DBT45B + 3×δ45B`, `DBT45 > DBT45B + 9 K`,
`BT4 > BT4B + 3×δ4B`. Candidato nocturno: `BT4 > 295 K AND DBT45 > 10 K`. **(4)** Nos
contradice el 3σ como número natural: acá el N·σ nocturno es **3**, no 5/10 — pero
sobre un fondo distinto y con un umbral absoluto de entrada (295 K) que nosotros no
tenemos. **(5)** No tenemos ninguno de los dos ATBD que cita:
`https://viirsland.gsfc.nasa.gov/PDF/ATBD_VIIRS_375m_activefire_algorithm.pdf` (p.5) y
`https://viirsland.gsfc.nasa.gov/PDF/VIIRS_activefire_ATBD750_v1.pdf` (p.8) — **ahí
está el test de nube interno con sus umbrales, y es lo que falta**. `Schroeder et al.
2014`, `Giglio et al. 2016`. **(6)** No da el test de nube: lo delega al ATBD.

---

## 5. `MCDWD_UserGuide_RevC.pdf` — confirmado: NO es una máscara de nubes

Portada (p.1): *"MODIS NRT Global Flood Product — MODIS Aqua+Terra Global Flood Product
L3 NRT 250m — Provided by NASA LANCE"*, autor **Dan Slayback** (NASA GSFC), Rev C,
12-ene-2023. Es el producto de **inundaciones** de LANCE. La síntesis del repo que lo
llama "máscara de nubes MODIS" está equivocada y hay que corregirla.
