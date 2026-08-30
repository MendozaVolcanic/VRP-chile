# Auditoría S128 — evidencia exógena

> **Eje estrenado**: el archivo de GeoTIFF/KMZ de MIROVA (1.960 escenas, 11 volcanes ×
> 3 sensores, 2026-05-08 a 05-20) y los papers leídos **verbatim**, no a través de
> nuestras síntesis. Los tres ejes exógenos suman cinco usos en 128 sesiones.
>
> **Reglas aplicadas**: A (prohibido repetir el barrido de 6-8 ejes) · B (cierre por
> guard, no por prosa) · C (la deuda de S121/S125 es la puerta de entrada).
>
> Todos los números salen de un script que los persiste (S91). Ninguno transcrito a
> mano. Scripts en `experiments/_s128_deuda/` y `experiments/_s128_tif/`.

---

## Resumen ejecutivo

**Lo que más rinde**: una hipótesis nueva, medida, que conecta el gap de magnitud con
una decisión de diseño **documentada** de MIROVA. El sub-reporte crece con el ángulo
de vista del satélite —VIIRS375 pasa de 0,796 cerca del nadir a 0,570 entre 35° y 50°,
con intervalos de confianza que no se solapan— y MIROVA **descarta** justamente esas
pasadas mientras nosotros no descartamos ninguna. Tomamos el área nadir fija, que el
remuestreo de ellos justifica, sin pagar el peaje que ellos pagan.

**Lo segundo que más rinde**: el **GAP #A no era un mislabel** (§6bis). Cuatro
documentos lo dan por cerrado desde S115 con dos argumentos, y los dos son falsos contra
el código y contra el paper. Hoy los píxeles más calientes de la escena entran al fondo
que calcula μ y σ, inflan el umbral y vuelven la detección menos sensible. Queda con
guard, no con prosa.

**Lo que se cayó**: la sonda que prometía el primer falso positivo afirmado con
evidencia externa. Se refutó sola en el control.

| | |
|---|---|
| pendientes cerrados por medición | **21** de 28 |
| confirmados | 8 · **refutados 7** · obsoletos 3 · imposibles con su razón 3 |
| guards nuevos | **5 tests** (`test_guard_gap_a_pool_musigma_s128.py`); suite 1003 verdes |
| pendientes que quedan abiertos | 9 (§8) |
| creencias load-bearing que cambiaron de valor | **4** (D2, D5, A12 y el GAP #A) |

---

## 1. La hipótesis nueva: el ángulo de vista explica parte del gap de magnitud

### El fenómeno, primero

Un sensor que barre de lado no ve un píxel cuadrado. Fuera del nadir la huella se
estira: a 50° de cenit, un píxel MODIS cubre del orden de **3,7 veces** su área
nominal de 1 km². Si dentro de esa huella hay un foco caliente pequeño —un cráter
activo de unas decenas de metros—, su calor queda promediado sobre mucho más terreno
frío, y el exceso de radiancia que medimos sale diluido.

MIROVA resuelve esto de **dos** maneras a la vez, y las dos están documentadas:

1. **Remuestrea a una malla de paso fijo.** Campus et al. 2022 (Sensors 22, 1713,
   p. 7): *«Resampling is performed in a UTM 51 × 51 km grid, centered on the volcano
   summit … by keeping the nominal resolution of 750 m. This results in matrices of
   67 × 67 pixels rather than 51 × 51 pixels obtained from MODIS»*. Eso es lo que
   justifica usar un área de píxel constante.
2. **Descarta las pasadas de mala geometría.** Tesis Massimetti, cap. 4: *«VRP data
   were filtered to include exclusively i) nighttime MODIS and VIIRS alerts; ii)
   MODIS and VIIRS image with a Zenith scanning angle < 50°; iii) alerts into a 5 km
   from the volcano summit»*. Y en el cap. 3, más estricto todavía: *«keeping out
   images with unfavorable viewing geometry (Zenith > 40°)»*.

**Nosotros hacemos la primera mitad y no la segunda.** Adoptamos el área nadir fija en
S102/S103 —correctamente, y este trabajo lo respalda: el `A_pix = 0,5625` de la Eq. 1
de Campus es exactamente nuestro `k` de VIIRS M-band— pero **no filtramos por cenit en
ninguna parte**. Verificado: `MAX_SENSOR_ZENITH_DEG` sólo vive en la rama sec³, que es
código muerto desde que `nadir_fixed=True`.

### La medición

Ratio nuestro/MIROVA, un par por noche, máximo de ambos lados, estratificado por
ángulo de cenit del sensor. n = 1.046 pares nocturnos.

| cenit | VIIRS375 | VIIRS750 | MODIS |
|---|---|---|---|
| 0–20° | n=376 **0,796** IC[0,750–0,834] | n=88 0,824 | n=18 1,248 |
| 20–35° | n=201 **0,641** IC[0,597–0,685] | n=56 0,610 | n=16 0,986 |
| 35–50° | n=118 **0,570** IC[0,506–0,643] | n=27 0,828 | n=12 1,322 |
| 50–90° | n=107 0,603 IC[0,522–0,700] | n=23 2,311 | n=4 1,195 |

En VIIRS375 —el sensor que domina nuestro volumen— la degradación es monótona hasta
50° y **los intervalos de 0–20° y 35–50° no se solapan**. VIIRS750 no muestra el patrón
limpio y MODIS tiene n insuficiente fuera de Láscar.

### Qué significa y qué NO significa

Significa que una parte del sub-reporte global (0,73) es geométrica y no algorítmica:
restringido a cenit < 20°, VIIRS375 da 0,796, que entra en la banda de paridad.

**No significa que haya que filtrar ya.** Dos advertencias honestas:

- El filtro de cenit que encontré está en los **análisis de investigación** de
  Massimetti, no en una descripción del producto **NRT operacional**. Que MIROVA lo
  aplique en sus papers no prueba que su pipeline en línea lo aplique. Es exactamente
  el error de S127 —verificar que una cita existe no es verificar que dice lo que se
  le atribuye— y por eso queda como hipótesis, no como gap de fidelidad.
- Filtrar cuesta cobertura: quedarse bajo 20° descartaría cerca del 60 % de las
  pasadas. En un sistema de monitoreo eso es perder noches, que es el error caro.

### El mecanismo, y por qué el filtro NO es el fix

Coppola et al. 2014 —conseguido en esta sesión, y que resultó ser la pieza que
faltaba— explica en su §2.2 exactamente por qué remuestrean, y de paso da la aritmética:

> *«high scan angles contribute to the growth of the projected ground spatial element
> (up to approximately 10 km² for scan angles of 55°). **This leads the radiance of a
> potential sub-pixel hot-spot to be integrated over a variable area, thus introducing a
> further source of error in estimating its thermal output.**»*
>
> *«we cropped and resampled (into an equally spaced 1 km grid) the MODIS Level 1b data
> which fall within a mask (50 km × 50 km) centred over the summit … **This means that
> one hot-spot pixel, whose area is 2 km² in the original image, becomes two pixels with
> equal areas of 1 km² in the resampled image.**»* — p. 6

Ahí está todo. El remuestreo **parte** el píxel elongado en varias celdas de área
nominal. La energía total se conserva porque el número de celdas crece con la
elongación: dos celdas de 1 km² dan los 2 km² reales. Por eso Campus 2022 puede usar un
`A_pix` **constante** en su Eq. 1 — la elongación no vive en el área de la celda, vive
en **cuántas celdas** ocupa el foco.

**Nosotros tomamos el área constante y no hacemos el remuestreo.** Un píxel elongado
sigue siendo un píxel, al que le asignamos el área nadir. Perdemos la multiplicidad, y
la pérdida es justo el factor de elongación — que crece con el cenit. Eso es la tabla de
arriba.

Verificado: `ENABLE_UTM_REGRID = False`, `ENABLE_NADIR_FIXED_PIXEL_AREA_{MODIS,VIIRS}
= True`, leídos de `pipeline.profile`.

**Y esto conecta dos frentes que veníamos tratando por separado.** El regrid a malla
fija es exactamente lo que `ENABLE_UTM_REGRID` y `pipeline/geo_utils.py::get_grid_center()`
—escrita en S98, sin llamador desde entonces— existen para hacer. **D17 y el gap de
magnitud son el mismo problema.** No es que nos falte replicar una geometría por
prolijidad: la geometría **es** el mecanismo que conserva la energía off-nadir.

**Camino propuesto, corregido**: el fix fiel es **el remuestreo**, no un filtro de cenit.
El filtro es lo que MIROVA hace *además*, en sus análisis, para lo que el remuestreo no
alcanza a arreglar. Orden sugerido:

1. **A/B del regrid** (`ENABLE_UTM_REGRID` ON) con reproceso real y criterio
   pre-registrado, midiendo la paridad **estratificada por cenit**: la predicción
   falsable es que el gradiente 0,796 → 0,570 se aplane. Si no se aplana, el mecanismo
   no es éste y hay que volver a mirar.
   ⚠️ **El brazo tiene que ser bow-tie + regrid, no regrid solo.** Coppola 2012 §3.2 pone
   la remoción del *bow-tie* como paso (i) y el remuestreo como paso (ii), en ese orden:
   sobre 25° de barrido los barridos de MODIS se solapan, así que regridear sin
   de-solapar primero **duplicaría píxeles calientes** y el A/B mediría el bug en vez del
   fix. Para VIIRS el punto es menor —el sensor lo borra a bordo y leemos su relleno
   (`FLAG_DNS` con 65533 `Bowtie_Deleted`)— pero **para MODIS no hacemos ninguno de los
   dos**.
2. Recién después, y sólo si queda residuo, evaluar el filtro de cenit.

Los dos van al backlog con ciclo A45 completo, no al pipeline.

---

## 2. La grilla de MIROVA, desde afuera — y una lectura mía que hubo que corregir

### Lo que dice el dato externo

Sobre las 1.960 escenas del archivo (`experiments/_s128_tif/01_grilla_real.py`):

- **La malla es perfectamente fija.** Dispersión **0,0 m** en los cuatro bordes, en
  los 33 pares volcán×sensor, entre todas las pasadas. No es un recorte que sigue al
  hotspot: es una grilla estable, como el paper dice.
- Las formas coinciden **exactamente** con Campus 2022: 51×51 (MODIS), 67×67
  (VIIRS750), 134×134 (VIIRS375).
- Los tres sensores comparten el borde **oeste** (0–14,5 m de desacuerdo) y el **sur**
  (0–14,8 m), mientras el este y el norte difieren ~500 m.

### La corrección

Leí ese último punto como *«MIROVA ancla una esquina, no el centro»*. **Es falso como
afirmación sobre su grilla.** El CRS de los 33 pares es EPSG:4326: los GeoTIFF son la
grilla UTM **reproyectada** para web. Al reproyectar, el origen del extent queda en la
esquina suroeste y el borde noreste flota según el paso de cada sensor. La esquina
compartida es artefacto del *export*, no el ancla. El paper dice *centered on the
volcano summit*, y para replicar MIROVA hay que centrar en la cumbre — que es lo que
hacemos.

Lo anoto porque es la clase de error que esta auditoría vino a cazar: un patrón
geométrico real, leído como si fuera una decisión de diseño ajena.

### Lo que sí sobrevive, y es el contenido real de D17

**Un solo `mirova_center_lat/lon` por volcán es la forma equivocada del dato.** Como
los tres sensores tienen extensiones distintas, el centro de escena cae ~250 m distinto
en cada uno. Nuestro valor —derivado de los KMZ en S80— acierta el centro de **un**
sensor por volcán, y cuál varía sin patrón: Copahue, Llaima y PP aciertan en VIIRS375;
Villarrica, Tupungatito, NdC e Isluga en VIIRS750. Contra los otros dos queda un
residuo de **180–310 m**, que en VIIRS375 (píxel de 375 m) es casi un píxel entero.

Y el offset que importa de verdad, porque es de kilómetros y no de metros:

| volcán | centro del TIF vs nuestro `volcano_lat/lon` |
|---|---|
| **Tupungatito** | **2.753–3.002 m al SUR** |
| **Planchón-Peteroa** | **1.861–1.923 m al NORTE** |
| los otros nueve | 15–350 m (sub-píxel) |

Son los dos volcanes donde S65 y S97 ya habían encontrado problemas de ancla. La
cumbre que MIROVA usa como centro y la nuestra son puntos distintos, por kilómetros.

### Lo que el KMZ no es

El `LatLonBox` de los KMZ **no describe la extensión del TIF**: recorta hasta 1,6 km
en un eje (Villarrica). Pero el recorte es simétrico, así que el **centro** del KMZ sí
queda a menos de 200 m del centro del TIF. O sea: el `mirova_center` heredado del KMZ
está bien **como centro** y mal **como extensión**. La afirmación del prompt de S128
era cierta sobre los bounds y engañosa sobre el centro.

---

## 3. La sonda que se refutó sola

**P2 prometía el primer falso positivo nuestro afirmado con evidencia externa en 127
sesiones.** El resultado inicial fue justo lo anticipado: en **463 de 482** pasadas
donde publicamos VRP>0, la escena de MIROVA de esa misma pasada no muestra ningún
realce al cráter, ni al corte más laxo. Copahue, Isluga, Lastarria, Tupungatito y NdC
dan **cero** escenas con contraste sobre 150–173 escenas cada uno.

Antes de escribirlo corrí el control obligado (A62: asumir que uno se equivoca y tratar
de refutarse): **¿qué contraste tienen las pasadas donde MIROVA misma alertó?**

| clase de la pasada según MIROVA | n | z mediano al cráter | % con z≥3 |
|---|---|---|---|
| **ALERTA_TERMICA** | 89 | **−0,14** | **14,6 %** |
| FALSO_POSITIVO | 40 | −0,41 | 5,0 % |
| RUTINA | 1.378 | −0,62 | 4,5 % |
| *nuestras detecciones con VRP>0* | 482 | −0,62 | 3,9 % |

**El instrumento no separa.** En el 85 % de las pasadas donde MIROVA declaró alerta, su
propio GeoTIFF no muestra realce al cráter con este índice. Estratificado por sensor
tampoco se salva: en VIIRS375, el único con poder estadístico, el **81 %** de las
alertas de MIROVA no pasa el corte.

**Por qué falla, y es instructivo**: el TIF trae **una sola banda** (MIR) y no trae TIR,
así que el NTI no se puede reconstruir. El índice mide radiancia MIR **absoluta**, que
es exactamente la variable que A69 dice contaminada por el gradiente topográfico.
MIROVA no detecta por MIR absoluto; detecta por NTI, que cancela la topografía.

**Veredicto: los 257 falsos positivos que el prompt daba por afirmables no son
afirmables.** El hecho es cierto y no significa lo que se le atribuía.

**El subproducto que sí queda, y es bueno**: en las alertas de Láscar, el máximo de
radiancia MIR de la escena **de MIROVA** está sistemáticamente a **23 km del cráter**,
en el borde del recuadro. A69 —el gradiente topográfico domina el MIR absoluto en los
volcanes de altura— visible en el dato de la referencia, no sólo en el nuestro.

> **Guard para S129**: el archivo público de TIF **no puede adjudicar detección ni
> magnitud**, por falta de banda TIR. Sirve para geometría de grilla, para cobertura, y
> para ilustrar A69. No volver a intentar validar detecciones contra él (extiende A24).

---

## 4. D2 medida por primera vez en 127 sesiones

La creencia *«el CSV cubre ~70 % de las pasadas VIIRS»* nunca se midió porque no había
denominador: no se sabía cuántas pasadas hubo. El archivo de TIF **es** ese denominador.

| sensor | pasadas del archivo | en el CSV | perdidas | cobertura |
|---|---|---|---|---|
| MODIS | 535 | 456 | 79 | **85,2 %** |
| VIIRS750 | 788 | 614 | 174 | **77,9 %** |
| VIIRS375 | 637 | 482 | 155 | **75,7 %** |
| **global** | **1.960** | **1.552** | **408** | **79,2 %** |

Por volcán va de 75,1 % (Villarrica) a 82,5 % (Chaitén).

**D2 subestimaba y el README del scraper acertaba.** No es ~70 % en VIIRS: es 75,7 % y
77,9 %. Y es **cota superior** —el archivo también es un poller horario, así que una
pasada que perdieron los dos no entra en ningún término—: el CSV puede perder más,
nunca menos.

Consecuencia operacional: una de cada cuatro o cinco pasadas VIIRS que llamamos
«falso positivo» contra el CSV puede ser una pasada que MIROVA sí publicó y el scraper
no alcanzó a leer.

---

## 5. Los pendientes de S121 — 14 de 19 cerrados

| # | afirmación de S121 | veredicto | medición |
|---|---|---|---|
| L74 | 3 workflows interpolan inputs sin comillas en `run:` | **CONFIRMADO, peor** | **7 workflows, 31 ocurrencias**, `nrt.yml` entre ellos |
| L79 | `run_pipeline.py` dice «Cleaned up» aunque falle | **CONFIRMADO** | el `print` está fuera del `for _ in range(3)`, sin comprobar éxito |
| L84 | queda una flecha Unicode en un mensaje de runtime | **REFUTADO** | 15 apariciones, **0 en runtime**, 12 en comentarios |
| L111 | `data/` = 2,0 GB, operacional ~180 MB | **REFUTADO** | **1.034,7 MB**; operacional **274,6 MB** |
| L116 | AVTOD nunca integrado | **OBSOLETO** | se integró en S122 (`experiments/_s122_m2_avtod/crossval.py`); sigue sin entrar a `scripts/` ni `pipeline/` |
| L126 | un PDF duplicado, 26 MB | **CONFIRMADO, peor** | **6 grupos byte-idénticos, 101,7 MB** |
| L131 | `experiments/` 458 MB | **REFUTADO, peor** | **1.427,9 MB**; top-3 = 972,6 MB |
| L136 | contradicción documental del GAP #A | **OBSOLETO** | los 4 documentos concuerdan hoy |
| L178 | data = 83,8 % de commits; `.git` 3,1 GB | **CONFIRMADO, mucho peor** | **87,2 %** (7.341/8.418); `.git` = **10,6 GB** |
| L188 | el ground truth CSV está fresco | **CONFIRMADO** | `latest_consolidado.csv` llega a hoy |
| L193/198/203 | falta `concurrency` y `timeout` | **PARCIAL** | `nrt.yml` ya tiene grupo a nivel workflow; **`nrt-retry.yml` sigue sin `timeout-minutes`** |
| L208 | sin `echo`/`print` de secrets | **CONFIRMADO sano** | 0 fugas en 15 workflows |
| L213 | ~10 subdirs `mirova_equivalent_*` ≈ 556 MB | **REFUTADO** | **2 subdirs, 204,9 MB** |

### Los dos que hay que mirar

**La inyección de comandos es más ancha de lo declarado.** Siete workflows interpolan
`${{ github.event.inputs.X }}` directamente dentro de bloques `run:`, con 31
ocurrencias: `nrt.yml` (el cron que corre 12 veces al día con los secrets de NASA),
`backfill-geometry`, `backfill-tier-a`, `reproc-chunked`, `reproc-s120-eq16-villarrica`,
`reproc-s124-ndc-focus` y `reproc-s124-villarrica-op-ab`. El modelo de amenaza es
acotado —disparar un `workflow_dispatch` exige permiso de escritura en el repo— pero el
patrón es el que GitHub documenta como *script injection*, el fix es mecánico (pasar por
`env:` y citar la variable), y el blanco son credenciales de NASA.

**El disco no lo llena `data/`: lo llena `.git`.** 10,6 GB, con 7,38 GiB empaquetados en
**33 packs**, 263 objetos *prune-packable* y **1,57 GiB de basura** — cuatro archivos
`tmp_pack_*` que quedaron de empaquetados interrumpidos. Un `git gc` recupera esa basura
y consolida los packs. Es mantenimiento estándar y no reescribe historia. **No lo corrí:
es tu llamado.**

```bash
git -C "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile" gc --prune=now
```

---

## 6. Los pendientes de S125 — 7 de 9 cerrados

### D5 · CONFIRMADO, y con el signo invertido

El ratio de hoy, n=1.055 pares nocturnos: mediana **0,73**, IC95 **[0,704–0,767]**.
D5 dice «calibración lograda, ratio 1,35×». **1/0,73 = 1,37.** D5 tenía el número
correcto y el signo al revés: no sobre-reportamos por 1,35×, **sub-reportamos** por ese
mismo factor. La divergencia marcada «resuelta» describe el frente abierto.

Por sensor, el sub-reporte vive en VIIRS375 (Lastarria 0,57, Isluga 0,58, Láscar 0,60,
Tupungatito 0,69). VIIRS750 es disperso y con n chico. **MODIS sólo existe en Láscar**
(1,08) — confirmado: los otros diez suman cero alertas MODIS nocturnas.

### A12 · REFUTADA

La regla clasifica volcanes por ΔT = t_max − t_bg, citando «Láscar 21,6 K, Isluga ~20 K»
y un umbral de 12 K para necesitar kernel-bg. Medido hoy sobre todos los records:

| | v375 | v750 | MODIS |
|---|---|---|---|
| Láscar | 16,9 | 15,1 | 15,9 |
| **Isluga** | **8,3** | **6,8** | **8,9** |
| Tupungatito | 14,2 | 15,2 | 16,6 |
| los otros ocho | 7,6–12,0 | 6,8–11,6 | 8,7–13,4 |

Isluga no está en ~20 K: está en 8. **Ningún volcán supera 17 K en ningún sensor**, así
que con los umbrales que la propia regla cita, hoy nueve de once caerían en «necesita
kernel-bg» y **ninguno** en «ya calibrado». A12 quedó inutilizable con sus propios
valores.

### D9 · REFUTADO el residuo, y la lectura se invierte

El residuo «24-83× post-cap» del path dNTI contextual es de S71, anterior a nadir-fijo.
Re-medido hoy, el path D puro da mediana **0,28–1,02** contra MIROVA, no 24-83×. Y algo
que nadie esperaba: **en 10 de 11 volcanes el path D puro está MÁS CERCA de la paridad
que los demás paths** (Láscar 0,41 vs 0,14; Villarrica 0,82 vs 0,22; Llaima 0,28 vs
0,05). El path que era sospechoso de inflar es hoy el menos sub-reportado.

### D14 · CONFIRMADA, ahora con A/B pareado en vez de una correlación sin script

El `r = −0,23` que sostenía «la máscara de nube no es el driver del gap» no tenía script,
ni n, ni IC. El A/B pareado que ya estaba en disco mide lo mismo mejor:

| volcán · sensor | pares | máscara ON | máscara OFF |
|---|---|---|---|
| Láscar · VIIRS375 | 35 | 0,434 | **0,510** (+17,5 %) |
| Villarrica · VIIRS375 | 8 | 0,764 | **0,832** (+8,9 %) |
| Láscar · VIIRS750 | 16 | 0,560 | 0,560 (idéntico) |
| Villarrica · VIIRS750 | 5 | 0,879 | 0,879 (idéntico) |

Apagar la máscara sube la magnitud entre 9 % y 18 % en VIIRS375 y **cero** en VIIRS750.
El gap es de ~37 %. **La conclusión se sostiene** —la máscara no es el driver— pero con
un matiz que la versión en prosa no tenía: no es cero, es cerca de un tercio del gap en
Láscar.

### R2 · medido, con un hallazgo de schema de regalo

Para clústeres multi-píxel, la suma es **2,3–5,5×** el máximo (mediana por volcán), con
cola hasta 57×. Y entre el **43 % y el 69 %** de los clústeres son de un solo píxel,
donde suma ≡ máximo por definición. Elegir suma o máximo cambia la magnitud por un
factor ~3 en la mitad de los records y por nada en la otra mitad.

**El hallazgo de schema**: el JSON **no persiste qué píxeles del `anomaly_pixels`
pertenecen al `primary_cluster`**. La pertenencia hay que reconstruirla por cercanía al
centroide. Eso hace que el invariante de S127 —para un clúster de un píxel, suma ≡
máximo— **no sea auditable desde el dato publicado**, sólo desde el código. Es la misma
familia de A46: una representación del mismo objeto que no se puede cruzar con la otra.

*(Y un A89 propio: `primary_cluster` no tiene lista de píxeles, así que el primer intento
concluyó «imposible». El VRP por píxel existe — está en `anomaly_pixels`, en la raíz del
record.)*

### Los dos que no se pueden cerrar, con su razón

- **A54** (el 95,4 % de los FP son físicamente reales) — **IMPOSIBLE de recomputar
  automáticamente**. La clasificación a/b/c/d de S86 fue un juicio **físico** por record
  (rasgo volcánico real vs artefacto), hecho a mano con conocimiento del volcán, y **no
  hay etiqueta persistida en el schema** que permita reproducirlo. Lo único automatizable
  es el denominador, que no es lo que A54 afirma. Para cerrarla haría falta re-etiquetar
  una muestra estratificada por volcán con criterio explícito y **persistir la etiqueta**.
  Sigue siendo la creencia más load-bearing del catálogo y sigue sin respaldo reproducible.
- **D13** (el 31 %) — pendiente: el re-cálculo independiente dio 27,8 % con denominador
  no declarado. Hay que declarar el denominador antes de poder medir nada.

---

## 6bis. El GAP #A no era un mislabel: está abierto

> Guard: `tests/test_guard_gap_a_pool_musigma_s128.py` (5 tests).

Cuatro documentos —`CLAUDE.md`, `MISSION.md`, `MIROVA_DIVERGENCES.md` y `AUDIT_S114`—
declaran el GAP #A **«RESUELTO S115 = mislabel, NO reabrir»**. Salió en la relectura del
canon con las seis preguntas, y lo verifiqué eslabón por eslabón antes de aceptarlo,
porque reabrir algo cerrado tiene la barra alta (anti-A8).

### El fenómeno

Coppola 2016a manda calcular la media y el desvío del fondo sobre los píxeles
*suitable*, y define como no-suitable justamente a los que ya dispararon el Test 1:

> *«Pixels that satisfy Test 1 are flagged as 'active' and subsequently discarded
> (unsuitable) for further steps.»* — `sp426_5.txt:297-300`
>
> *«m and s are the arithmetic mean and standard deviation of all the suitable pixels
> within the image.»* — `sp426_5.txt:326-329`

Tiene sentido físico directo: los píxeles del Test 1 son, por construcción, los más
calientes de la escena. Dejarlos dentro del fondo infla μ y sobre todo σ. El umbral de
los Tests 2 y 3 es `μ + C2·σ`, así que **un fondo contaminado sube el umbral y vuelve la
detección menos sensible**. El error va hacia el falso negativo, que en monitoreo
volcánico es el error caro.

### El cierre de S115 se apoya en dos afirmaciones, y las dos son falsas

**(a) «"discarded for further steps" = fuera del pool μ,σ, ya cubierto por el
second-run».** El second-run recibe `active_mask=hot_mask_2d`
(`process_modis.py:853`), y antes `hot_mask_2d = fp_hot` (`:821`), que son **sólo los
Tests 2 y 3**. Los píxeles del Test 1 (`nti_path_hot`) nunca entran ahí. El second-run
no cubre nada de esto.

**(b) «el flag `ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK` controla el REPORTE, no el
pool».** Es al revés, y la cadena es de tres saltos:

```
process_modis.py:791-793   _test1_mask_for_fp = nti_path_hot
                             if ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK else None
detection_context.py:364     first_pass_tests_2_and_3(..., test1_mask=...)
detection_context.py:135     unsuitable = unsuitable | test1_mask     ← ES el pool μ/σ
```

El comentario del propio código, dos líneas arriba, cita la sección exacta del paper:
*«pasar Test 1 K1 mask como unsuitable bg si flag retire ON (Coppola 2016a SP 426.5
§298-300)»*. **Y el flag está en `False`** — leído de `pipeline.profile`, no del YAML.

**Es A89 de manual**: el flag se juzgó por su **nombre** —«…RETIRE_FROM_HOT_MASK» suena
a reporte— en vez de por cómo lo lee el código. Segunda vez en dos sesiones que un flag
mal nombrado produce un cierre falso.

### Qué hice y qué no

Corregí las tres frases falsas en los documentos (tachadas, no borradas: el historial se
conserva) y escribí el guard, que **falla si alguien vuelve a declararlas**. No encendí
nada: adoptar el retiro exige su propio A/B con reproceso real (A45/A18), y va al
backlog como pendiente #8.

**Y una advertencia sobre la dirección**: esto no explica el sub-reporte de magnitud
(§1, §6-D5) — el fondo para ΔL sale del anillo, no de este pool. Explicaría **falta de
detección**, que es coherente con D12 (los ~70 de 79 falsos negativos de MODIS en
Láscar). No mezclar los dos frentes.

### Otras contradicciones de la relectura del canon

- **La geometría del ROI1.** El paper: *«the inner region (ROI1) consists of a box
  (5 × 5 km) centred on the volcano's summit»* — una caja de 5 km, igual para todos.
  Nosotros usamos un **círculo** de radio 3 a 20 km, distinto por volcán. En PCC
  (r = 20 km) el ROI1 interior es del orden de 50 veces el del paper, así que media
  escena hereda los umbrales laxos de *summit*. Y el criterio del propio paper para
  tener dos ROIs —*«variable size and different chance of finding a thermal anomaly»*—
  se rompe con un radio así. **Éste es el eje geométrico que A82 nunca auditó** y por el
  que S124 la rebajó. Va al backlog.
- **El fondo.** Coppola Eq. 6: *«L4bk is estimated from the arithmetic mean of all the
  pixels surrounding the active one (or around the active cluster)»*, y Campus 2024
  Eq. 2 lo repite por píxel. El fondo autorreferente que S126 identificó contradice a
  los dos, y **el brazo "corona" de S127 tiene respaldo textual explícito** — dato
  relevante para la decisión que quedó en «no adoptar».
- **El máximo diario NO es el producto de MIROVA.** Esto corrige la premisa del prompt
  de S128. Coppola usa la ventana de 24 h para integrar **volumen**, sobre TADR; del
  producto publicado dice lo contrario: *«the RP time series… are provided "as they
  are"»*. Y Campus 2022 usa **media semanal** y deja los datos crudos *«without applying
  image inspections or filters that discard cloudy scenes»*, probando explícitamente el
  modo NRT sin supervisión. O sea: **publicar por pasada y con la máscara de nube
  apagada está validado por el canon**. El máximo diario, si se usa, va en la auditoría
  de paridad, no en el pipeline.
- **Saturación de M15.** Campus 2022 Tabla 1 da TMAX de 634 K para M13 y **343 K para
  M15**. Nuestro código usa 634,0 para M13 —coincide exacto— y **423,0 para M15**, que
  el propio comentario admite puesto *«análogo a I05»*, no tomado de una fuente.
  Pendiente de resolver contra el VIIRS L1B UserGuide, que por la jerarquía de A35 manda
  sobre el paper.
- **La Tabla 1 de umbrales, verificada verbatim**: K1 −0,8/−0,6, C1 0,003/0,01/0,02,
  C2 5/10/15. **Nuestros números son exactos.**

---

## 6ter. Coppola 2014 dice lo contrario de lo que se le atribuía

El diseño de S128 puso a Coppola et al. 2014 como **la prioridad de toda la fase
bibliográfica**, con este razonamiento: Laiolo 2026 cita «(Coppola et al. 2014; 2016)»
para sostener que los valores bajo 0,1 MW son probablemente nube o mala geometría, así
que *«la fuente del argumento que reencuadra nuestro piso VRP es un paper que no
tenemos»*.

Ahora lo tenemos. **Y argumenta en contra del piso, no a favor.** Tres pasajes, todos
verificados verbatim sobre el PDF:

> *«all the "False" detections consist of small-amplitude thermal anomalies (i.e. VRP
> < 2 MW), and they could be easily eliminated by **setting a cutoff at 2 MW**. However,
> such a cutoff will also produce a strong reduction of the efficiency of the algorithm,
> with the "Correct" detections decreasing from ~79% to less than 59%. … **we preferred
> to keep some false alerts than missing several real hot-spots.**»* — p. 3413

Evaluaron un corte, midieron lo que costaba, y lo **rechazaron**. Es exactamente el
criterio operacional nuestro —recall por sobre precisión en `mirova_equivalent`— escrito
por la fuente.

> *«The "Very Low" radiating regime (VRP < 1 MW) represents about 17% of the data and
> includes essentially most of the false alerts detected by the algorithm. **However, in
> 75% of cases the detection of a Very Low regime represents a genuine hot-spot** which
> may be associated with the presence of a single vent (with a radius of ~1 m and
> temperature of 950 °C).»* — pp. 3417-3418

Tres de cada cuatro detecciones sub-MW son señal real, según el canon. Eso **corrobora
A54 desde la fuente primaria**, que es más de lo que A54 tenía hasta hoy (§6 la dejó sin
respaldo reproducible por el lado de nuestros datos).

**Y el número 0,1 MW no aparece en el paper.** Los puntos de inflexión que Coppola
identifica están en 1, 10, 100 y 1000 MW. La atribución «<0,1 MW = nube o mala
geometría» no se apoya en esta fuente. Es la tercera vez en dos sesiones que una cita
verificada como existente resulta decir algo distinto de lo que se le atribuía.

**Consecuencia para la decisión pendiente del piso VRP**: el argumento de autoridad que
la reencuadraba se cayó. La recomendación de S126 —quitarlo, porque hoy es un no-op que
además miente, y **no** aplicarlo a `pc.vrp_mw`— queda ahora respaldada por el canon en
lugar de sólo por nuestros datos.

### Un regalo para el frente de nube

> *«L4bk is estimated from the arithmetic mean of all pixels surrounding the alerted one
> (or around the alerted cluster) **not contaminated by clouds**. Accordingly, cloudy
> pixels are detected using the method described by Giglio et al. (2003):
> cloud = [BT11 < 255] (condition 4, for night-time data)»* — p. 3412

MIROVA **sí** enmascara nube, pero para un uso distinto del nuestro: no descarta escenas,
**excluye los píxeles nublados del fondo `L4bk`**. Y el umbral canónico es **255 K**, no
los 260 K que usábamos antes de apagar la máscara en S127/D14. Que descartemos escenas y
ellos limpien el fondo son dos operaciones distintas con el mismo nombre — vale
revisarlo cuando se retome ese frente, sin reabrir la decisión de D14, que sigue medida
y en pie (§6).

---

## 6quater. La segunda tanda de lectura — el mecanismo confirmado por el canon

Wright 2002, Schroeder 2014 y Aveni 2023 (FY-3D) se leyeron después de escribir §1. Dos
de los tres tocan directamente lo que §1 propone, y uno obliga a matizar una regla
vinculante.

### El grupo MIROVA describe nuestro sesgo por ángulo, por escrito

Aveni, Laiolo, Campus, Massimetti & Coppola 2023 —los cinco del canon— pp. 15-16:

> *«the only increase in the satellite zenith corresponds to a decrease in the VRP …
> **Although this is partially corrected during the resampling step**, residual
> artefacts can hardly be removed entirely»*

Es exactamente el gradiente que medimos (0,796 → 0,570), nombrado por ellos, con el
remuestreo identificado como la corrección **parcial**. Y confirman que el remuestreo es
parte de la cadena, no un detalle de ese paper (p. 8):

> *«Following the MIROVA structure, MERSI-II bands 21 and 24 were resampled to a regular
> **UTM 51 × 51 km grid, centred on the volcano's summit** as per coordinates provided by
> the Global Volcanism Program»*

Mismos parámetros que Campus 2022 para VIIRS 750 m. **Dos sensores, dos papers, la misma
grilla.** Y antes de remuestrear **borran los píxeles bow-tie**, porque *«duplicate pixels
might lead to overestimation»* — o sea la multiplicidad del remuestreo no son duplicados,
son celdas reales. Eso cierra la duda de §1: el A/B del regrid es el camino, y el filtro
de cenit es lo secundario. *(Su corte de análisis, dicho sea de paso, es **≤ 40°**, no 50°.)*

### Una SEGUNDA autorreferencia del fondo, y ésta sí es del lado de la magnitud

El paper define el fondo de la magnitud sin ambigüedad (Eq. 3, p. 8):

> *«L_MIRbk is the radiance of the background, namely the average radiance of the
> surrounding, **non-alerted** pixels»*

Y Coppola 2016a Eq. 6 dice lo mismo: *«L4bk is estimated from the arithmetic mean of all
the pixels **surrounding** the active one (or around the active cluster)»*.

**Nuestro `t_bg` no excluye los píxeles alertados.** `ENABLE_TEST1_K1_BG_EXCLUDE = False`,
leído de `pipeline.profile`. Ese flag alimenta `compute_bg_stats`, que produce el `t_bg`
del que sale `L_bg`, que entra en `delta_L = max(hotpix_rad − L_bg, 0)` y por lo tanto en
el VRP. El comentario del propio código cita la línea exacta del paper (`process_modis.py:504`,
*«Test 1 K1 active … del bg per Coppola 2016a:352-356»*) y el flag está apagado.

**La dirección es sub-reporte**: incluir los píxeles calientes sube `t_bg`, sube `L_bg`,
baja `ΔL`, baja el VRP. Y eso explica lo que el mecanismo del regrid **no** explica — que
incluso cerca del nadir estemos en 0,796 y no en ~1,0.

> **Dos mecanismos, dos firmas.** El fondo autorreferente produce un déficit **uniforme**;
> el regrid faltante produce el **gradiente con el cenit**. Los dos tienen respaldo
> verbatim del canon. Es la primera vez que el gap de magnitud tiene una explicación
> mecánica completa en lugar de un factor empírico.

### Corrección a mi propio §6bis: son DOS pools, no uno

`AUDIT_S114` (§243) decía que «el mecanismo del pool es otro flag,
`ENABLE_TEST1_K1_BG_EXCLUDE`». Al revisarlo resultó que **hay dos fondos distintos, cada
uno con su flag, y los dos apagados**:

| fondo | qué es | flag | estado | lo pide |
|---|---|---|---|---|
| **detección** | μ y σ de dNTI/dETI para los Tests 2 y 3 | `ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK` | **False** | Coppola 2016a §326-329 («*all the suitable pixels*») |
| **magnitud** | `t_bg` → `L_bg` → `ΔL` | `ENABLE_TEST1_K1_BG_EXCLUDE` | **False** | Coppola 2016a Eq. 6 + Aveni 2023 Eq. 3 («*non-alerted*») |

§6bis se sostiene —el docstring de `first_pass_tests_2_and_3` dice literalmente que
`test1_mask` filtra «el pool μ/σ», y `build_unsuitable_mask` devuelve el `bg_mask` que lo
computa— pero S114 tenía razón en que existía **otro** flag, y ninguno de los dos vio que
eran **dos problemas paralelos**. El de magnitud es el que importa para el 0,73.

### Wright 2002 obliga a matizar A69

A69 dice, como regla vinculante, que *«el NTI cancela la topografía»*. El paper que
**inventó el NTI** dice lo contrario, p. 141:

> *«As the NTI is based on **absolute radiance values**, variations in geography and
> season will influence its value, as MODIS Bands 21, 22, and 32 are all sensitive to
> variations in the ambient background temperature»*

El NTI **atenúa** el gradiente —lo bastante como para que nuestra medición empírica de
A69 (I04−I05 plano donde I04 tiene 15 K de gradiente) siga siendo válida— pero **no lo
cancela**. Lo que cancela es la forma **diferencial**: el ETI = NTI − NTI_bk, que es
aporte de Coppola, no de Wright. La lección de A69 vale entera; la palabra «cancela» no.
Corregido en `CLAUDE.md`.

*(Y el umbral: el −0,80 de Wright es empírico sobre histogramas globales y **sólo
nocturno**. Nuestro `nti_k1_night = -0.8` coincide con el origen; el **−0,6 diurno no
viene de Wright**, y habrá que rastrear de dónde salió.)*

### Una divergencia real que resultó no importar

Wright y Coppola 2016a construyen el NTI con la **banda 32** (12,02 µm); nosotros usamos
la **31** (11,03 µm), y nunca quedó registrado. Antes de anotarlo como gap lo cuantifiqué
con Planck: el corrimiento del NTI entre las dos bandas va de **0,0001** (250 K) a
**0,0054** (290 K), contra un margen de ~0,14 entre el NTI típico de escena y el umbral
K1. Y en el `dNTI` se cancela, porque el corrimiento es casi uniforme en la escena.
**Real, nunca registrado, y numéricamente despreciable.** Queda anotado para no
re-descubrirlo (regla B).

### Y una que matiza A1

Aveni 2023 deriva el `k` del sensor nuevo **teóricamente** —Planck más un ajuste del
coeficiente α(λ)— no empíricamente. Nuestra regla A1 dice «calibración empírica > derivación
teórica». Los números coinciden: σ/α da 19,155 (MODIS), 19,688 (M13) y ~17,99 (I04
interpolado a 3,74 µm), o sea nuestros 19,7 y 18,0 caen dentro del 0,1 %; el 18,9 de MODIS
queda 1,3 % por debajo. A1 acertó el resultado por otro camino, y eso vale como validación
cruzada — pero la regla no debería decir que el camino teórico no sirve.

### El test decisivo: la magnitud del efecto calza, la firma fina no alcanza

Schroeder 2014 p. 86 da el número exacto que faltaba, verificado verbatim:

> *«the effective footprint ranges from the nominal 375 m resolution (383 × 360 m) at
> the sub-satellite point to **795 × 784 m at a maximum scan angle of 56.28°**»*

Son **4,52×** de área en el extremo del barrido — muy lejos del ~25× que daría un
barredor sin agregación, porque VIIRS agrega muestras a bordo (3× cerca del nadir, 2×
después, 1× en el extremo). De ahí salió una **predicción pre-registrada**, hecha antes
de mirar los bins: la razón del ratio entre cenit 0-15° y 35-50° debía ser **1,57×** si
el área es la causa, **2,27×** si no hubiera agregación, y **1,00×** si el área no
tuviera nada que ver.

Medido (`experiments/_s128_tif/04_firma_del_area_de_pixel.py`, sólo VIIRS I-band):

| | n | mediana | IC95 |
|---|---|---|---|
| cenit 0–15° | 301 | **0,804** | [0,759 – 0,840] |
| cenit 35–50° | 118 | **0,570** | [0,506 – 0,643] |
| **razón** | | **1,41×** | los IC **no se solapan** |

**1,41 contra 1,57 predicho y 1,00 si no fuera el área.** Cae del lado correcto, en el
orden de magnitud correcto, y por debajo de la predicción — que es lo esperable, porque
el remuestreo de MIROVA corrige *parcialmente* (palabra de ellos) y porque el ratio es
nuestro sobre el de ellos, no el factor geométrico crudo.

**La segunda firma, en cambio, no se estableció.** El área no crece suave: cae de golpe
en cada cambio de zona de agregación, y esa firma de diente de sierra no la puede imitar
ningún otro mecanismo —ni el fondo autorreferente ni la topografía tienen razón para
saltar en un ángulo de barrido concreto—. En bins de 5° aparecen cuatro subidas, incluida
una de +0,114 justo pasando los 40°, **pero las cuatro caen dentro del ruido**: con 33 a
44 pares por bin los intervalos se solapan. **No confirma ni refuta**: está sub-potenciada.
Para resolverlo haría falta más ventana temporal, no más análisis.

*(Y un error de nuestro código que sale de paso: el comentario de
`pipeline/scan_geometry.py:193-195` afirma que el área I-band agregada varía «only
between ~0.32 and ~0.6 km²» — un factor 1,9×. Schroeder da 0,138 → 0,623 km², que es
**4,52×**. Está en la rama inactiva por `nadir_fixed=True`, así que no afecta ningún
número publicado, pero desinformaría exactamente la decisión que viene. No lo toqué:
`scan_geometry.py` está bajo A45.)*

---

## 7. Higiene del corpus bibliográfico

Verificado y corregido (informe completo en `docs/s128/CORPUS_HIGIENE.md`):

- **Los cuatro archivos rotos, confirmados los cuatro.** `cigolini2022_epsl.pdf` es HTML
  y `laiolo2022_epsl_openvent.md` también — y **no son dos incidentes, es el mismo**:
  misma referencia Cloudflare, la misma petición fallida guardada dos veces. El paper que
  ambos deberían ser es Laiolo et al. 2022 EPSL, DOI `10.1016/j.epsl.2022.117726`.
  `coppola2025_cap11_extracted.pdf` es índice + capítulo 1 de gravimetría; el capítulo 11
  real sí está completo en `coppola2024_chapter.txt`. `MCDWD_UserGuide_RevC.pdf` es el
  producto de **inundaciones** de LANCE, no una máscara de nubes. **Ninguno borrado**:
  renombrados con sufijo.
- **Las atribuciones erradas son cinco, no cuatro.** La única que toca el pipeline: el
  `k_MIR = 18,0` de VIIRS I4 (`process_viirs.py:74`) se atribuía a «Laiolo 2024» y es
  **Campus et al. 2024**. Grupo correcto y número correcto — sólo se rompía la
  trazabilidad. Las otras cuatro son Catania/Potenza (no canon), así que no contaminaron
  nada metodológico.
- **El ítem fantasma de `MISSION.md`, resuelto.** «Coppola 2015» y «Coppola 2016a
  SP426.5» son el mismo paper: el Test 1 está dentro de `sp426_5.txt:300`, y el único
  Coppola realmente de 2015 en el repo (Vanuatu, JVGR) no menciona NTI ni Test 1 ni K1
  una sola vez. **La lista canónica tiene 11 entradas, no 12.**
- **Cobertura re-medida: 46/70 documentos = 65,7 %**, no el 54 % de S13. Script
  reproducible en `scripts/audit_corpus_documentacion.py`.
- **Redundantes: 101,9 MB en 8 grupos byte-idénticos.** Matiz: `documentacion/` está
  gitignoreado, así que pesan sólo en disco local. Si el problema es el 98 %, el
  candidato serio es `978-3-031-86841-2.pdf` (93 MB, del que usamos un capítulo ya
  extraído). **Borrar exige A38** — inventario, tag defensivo y tu confirmación.

---

## 8. Lo que queda abierto (puerta de entrada de S129, regla C)

1. **A54** — sin respaldo reproducible. Necesita re-etiquetado con criterio explícito y
   etiqueta persistida en el schema.
2. **D13** — necesita que se declare el denominador.
3. **El A/B del filtro de cenit** (§1) — tres brazos, criterio pre-registrado, midiendo
   paridad *y* noches perdidas.
4. **La inyección de comandos en 7 workflows** (§5) — fix mecánico vía `env:`.
5. **`nrt-retry.yml` sin `timeout-minutes`.**
6. **`mirova_center_lat/lon` es por volcán y debería ser por volcán×sensor** (§2), y los
   offsets de kilómetros de Tupungatito y PP.
7. **Los duplicados del corpus y el `git gc`** — decisiones tuyas.
8. **El A/B del GAP #A** (§6bis) — encender `ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK` con
   reproceso real y criterio pre-registrado, midiendo recall (la dirección esperada es
   ganar detecciones) y magnitud. Es el candidato más directo para D12.
9. **El ROI1: caja de 5 km del paper vs nuestro círculo de 3-20 km** (§6bis) — el eje
   geométrico que A82 nunca auditó, y por el que S124 la rebajó.
10. **La saturación de M15** (423 K nuestro «por analogía» vs 343 K de Campus 2022) —
   resolver contra el VIIRS L1B UserGuide, que manda sobre el paper (A35).

### Lo que NO hay que reabrir

- **El archivo público de TIF no adjudica detección ni magnitud** (§3). Sirve para
  geometría, cobertura y para ilustrar A69.
- **El área nadir fija está respaldada por el paper primario**: el `A_pix = 0,5625` de la
  Eq. 1 de Campus 2022 es exactamente nuestro `k` de VIIRS M-band. S102/S103 acertó.
- **La grilla de MIROVA está centrada en la cumbre**, no anclada a una esquina (§2). El
  patrón de esquina compartida es artefacto de la reproyección a EPSG:4326.

---

## 9. Método — lo que esta auditoría dice sobre auditar

**A89 apareció cuatro veces.** Tres fueron mías, auditando; la cuarta es la que produjo
el cierre falso del GAP #A en S115, y es la misma forma: un flag juzgado por su nombre
—«…RETIRE_FROM_HOT_MASK» suena a reporte, gobierna el pool de μ/σ— en vez de por cómo lo
lee el código. Segunda sesión seguida en que un flag mal nombrado cierra algo que está
abierto. Mi sonda leyó
`mirova_center` cuando la clave es `mirova_center_lat`/`_lon`, devolvió `None` en los
once, y por un momento lo leí como «no está configurado». El segundo: `primary_cluster`
no tiene lista de píxeles, y concluí «R2 es imposible» cuando el VRP por píxel estaba en
`anomaly_pixels`. El tercero: buscar el filtro de cenit por nombre de constante en vez de
trazar si algo lo usa. **El cero de una búsqueda se sigue leyendo como ausencia, y la
técnica se equivoca en la misma dirección que el defecto que busca.**

**El control salvó la sonda estrella.** P2 habría entrado al catálogo como «257 falsos
positivos afirmados con evidencia externa» si no se corría el control de instrumento.
Costó un script de veinte minutos. **Toda sonda que produzca un veredicto sobre nosotros
necesita medir primero si el instrumento distingue a MIROVA de sí misma.**

**El eje exógeno rindió, pero no donde se esperaba.** La sonda diseñada para ser la más
filosa (P2) se cayó; las dos «de infraestructura» (P1 y P3) cerraron una divergencia y
midieron una creencia de 127 sesiones; y el hallazgo que más rinde —el ángulo de vista—
salió del **cruce** entre un paper leído verbatim y un dato nuestro que ya estaba
persistido, sin descargar nada. El Lote C del diseño («leer no sirve si no se cruza»)
era la parte correcta.
