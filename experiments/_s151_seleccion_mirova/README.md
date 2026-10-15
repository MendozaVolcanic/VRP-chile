# Tarea 1.4: qué objeto informa MIROVA cuando hay calor lejos del cráter

Estudio sin correr el pipeline, previo a cualquier código para que la réplica elija como MIROVA. Fecha
2026-10-14, versión 3 tras dos verificadores con contexto limpio del PR #809 (los dos PARCIAL; sus puntos están
atendidos en §8). Scripts y salidas en esta carpeta; los TIF y las láminas se bajan a un cache **fuera del
repo** (variable `VRP_TIF_CACHE`, 111 MB), por raw.githubusercontent, sin pull ni clone.

| script | salida | qué mide |
|---|---|---|
| `estudio.py` | `estudio_salida.txt`, `estudio_salida.json`, `pasadas.csv` | P1 a P4 sobre los GeoTIFF |
| `lascar_20261001.py` | `lascar_20261001_salida.txt`, `.json` | georreferencia de las miniaturas de MIROVA y el caso Láscar 2026-10-01 05:18 |
| `comun_tif.py` | | bajar, fechar, leer y medir un TIF (una sola definición) |

## En una línea

**MIROVA no elige el cráter por ser el cráter. Que informe lejos depende de la fuerza del foco lejano, absoluta o
relativa al cráter (los datos no las separan), con el cráter como segundo predictor.** Con calor en el cráter y un
foco lejano a la vez, MIROVA informa lejos en las 15 de 15 pasadas con foco lejano de z ≥ 30 en el TIF, y en 12 de
27 bajo ese corte (prueba continua p = 9e-5). En las 15 alertas del cráter con un foco débil en nuestro píxel
lejano, el VRP que publica es el del cráter solo: ese foco no entró en su VRP. La causa candidata en nuestro lado
es la conectiva `min` de los Tests 2 y 3 (SOSPECHA, §4). **"La mayor" contra "la suma" NO está demostrado**, y el
diseño del brazo A2 queda en espera del A/B de F y K (§4).

## 1. El fenómeno y por qué el TIF sirve

De noche, en el recuadro de 50 × 50 km de un volcán puede haber más de una fuente de calor: el cráter y, por
ejemplo, un incendio o un foco tibio a decenas de km. MIROVA publica una fila por pasada con un VRP y una
distancia sin rumbo, medida desde el centro de su grilla (D15, `../_s151_prereg_caja/distancia_mirova.py`). La
fila no dice dónde estaba el calor. El GeoTIFF que MIROVA publica de esa misma pasada sí: es el campo de
radiancia del infrarrojo medio. Un foco caliente se ve ahí como un **exceso local** sobre sus vecinos; el
gradiente de la topografía (valle tibio contra cumbre nevada, A69) se borra restándole al campo su mediana móvil
(S139). Ese exceso se mide en desvíos robustos (z) y, por el coeficiente de Wooster, da una energía aproximada
(A24: el TIF no es VRP sumable, por eso se valida antes de usarla). Lo que el TIF **no** dice es qué píxeles
alertó MIROVA: su prueba usa también la banda térmica, que el TIF no trae.

## 2. Datos, cobertura y controles de instrumento

- **Universo**: las 359 lejanas nocturnas (FALSO_POSITIVO de la tabla, hora UTC bajo 12, 2026-03-01 a
  2026-10-09; VERIFICADOR_DATOS D2), reproducidas exactas. Comparación: 1.377 ALERTA_TERMICA nocturnas y una
  muestra de 450 RUTINA (150 por sensor, semilla 151).
- **TIF de la misma pasada** (adquisición del índice a ±120 s; fuera todo archivo cuyo md5 aparece con otra hora
  de adquisición, A106): 117 de las 359 lejanas (103 VIIRS 375, 6 VIIRS 750, 8 MODIS). De las otras 242, 20
  tienen md5 ambiguo y 222 no tienen TIF de esa pasada: 84 son anteriores al 2026-05-09 (inicio del archivo), 27
  posteriores al 2026-09-22 y 111 caen dentro de la ventana pero el archivo no guardó esa pasada. **MIROVA dejó
  de actualizar sus GeoTIFF el 2026-09-22** (HEAD del 2026-10-14 al TIF de Láscar VIIRS 375: `Last-Modified 22
  Sep 2026 10:26 GMT`; el KMZ sí se actualiza). El verificador lo confirmó con 9 TIF y `index.csv`.
- **Georreferencia**: el centro de cada raster cae a 0,01 a 0,49 km del centro de grilla de `volcanoes.yaml`;
  0 cráteres fuera del raster. Control positivo: en las alertas VIIRS 375 el exceso en el cráter (z 7,2) supera
  al de discos iguales a 8 km en el 96,9 % (rutina: 37,3 %).
- **Atribución** (¿el TIF es de esta pasada?): temperatura de brillo del TIF contra la de nuestros píxeles de la
  misma pasada, con el nulo de los píxeles de otra pasada sobre el mismo TIF. VIIRS 375: mediana 0,61 K contra
  5,00 K del nulo. Cortes (verificada ≤ 1 K, rechazada > 5 K) elegidos **después** de ver las dos distribuciones.
  En MODIS el control no separa y queda sin dato. Se apartan 65 pasadas rechazadas; todo se repite con las 404
  verificadas.
- **Umbrales medidos, no elegidos** (A110): p95 del mismo estadístico en las RUTINA, donde MIROVA miró y no
  alertó nada. VIIRS 375: foco en un anillo o en un punto z ≥ 10,6; calor en un disco del tamaño del cráter
  z ≥ 3,3; foco más fuerte de toda la zona lejana z ≥ 20,1.
- **Energía** (control que podía fallar): el exceso del foco por Wooster contra el VRP que MIROVA publica da
  Spearman 0,889 en las lejanas (n = 92) y 0,809 en las alertas del cráter (n = 441); la energía del TIF queda un
  20 a 40 % sobre el VRP en mediana.

## 3. P1: ¿el TIF muestra calor a la distancia que dice el CSV, y nosotros vemos lo mismo?

Sí, y en posición. **Firme** (el verificador lo confirmó con su propio nulo).

| VIIRS 375, sin las rechazadas | lejanas | alertas (anillo prestado) | rutina (nulo) |
|---|---|---|---|
| foco en el anillo a la distancia del CSV, z ≥ 10,6 | **84 de 97 (86,6 %)** | 16 de 350 (4,6 %) | 7 de 137 (5,1 %) |

- **Anillo corrido** 3 km afuera o adentro: el de la distancia del CSV gana en 89 de 92 lejanas con foco
  (rutina: 28,1 %).
- **Posición**: nuestro píxel alertado de más VRP (`hotspot_lat/lon`) cae a 1 km o menos del foco de MIROVA en
  **39 de 54** lejanas VIIRS 375. Nulo de **otras noches** (nuestro píxel de más VRP de otras noches del mismo
  volcán, a más de 5 km del cráter, 20 por pasada): se esperan **0,40** coincidencias, se observan 39. El nulo de
  la versión 1 (el foco girado alrededor del centro, 0 de 546) daba cero casi por construcción, porque cada punto
  girado queda a 5 km o más del foco; se conserva en la salida pero ya no se usa como argumento. Solo verificadas:
  28 observadas contra 0,00 esperadas.
- **Las 15 sin coincidencia** (con píxel nuestro): **9** tienen distancia del CSV sobre 25,5 km (8 de 11 entre
  las verificadas), o sea caen en la esquina de la grilla de 51 km de MIROVA, fuera de nuestro radio de 25 km.
  Otras 30 lejanas no tienen ningún píxel alertado nuestro.
- La lista `anomaly_pixels` del record casi nunca guarda el objeto lejano (4 de 57). El verificador precisó el
  mecanismo: lo gatilla `_test1_wins` (`pipeline/process_viirs.py:1770`), no sólo la Regla D, y la reconstrucción
  posterior pisa también `vrp_mir_mw`. **Nuestro detector ve el objeto; el record lo pierde después**: un
  consumidor más para cualquier cambio (A118).

## 4. P4: las 36 alertas en que MIROVA informó el cráter con nuestro píxel lejano encendido

Es el dato que define la regla de MIROVA. Son las pasadas VIIRS 375 en que MIROVA informó el cráter (ALERTA)
mientras nuestro píxel de más VRP estaba a más de 5 km del cráter y nuestro cúmulo en el inner. Se comparan con
las 42 lejanas del mismo patrón nuestro, donde MIROVA sí informó lejos.

- En **15 de las 36** el TIF muestra un foco (z ≥ 10,6) a 1 km o menos de nuestro píxel lejano (nulo de otras
  noches: 0,1). En las otras 21 el TIF no tiene nada ahí: nuestro píxel lejano no es un objeto que MIROVA vea.
- En las lejanas: 38 de 42 (nulo 0,7).

La energía del foco se mide como el **exceso del píxel pico** por Wooster (la suma 3 × 3 de la versión 2 mezcla
vecinos y en Isluga no separa; se conserva en la salida).

| las 15 alertas contra las 38 lejanas con foco en nuestro píxel | cerca (MIROVA: cráter) | lejos (MIROVA: lejos) | Mann-Whitney |
|---|---|---|---|
| z del foco lejano (mediana) | 15,3 | 28,7 | p = 0,0001 |
| exceso del píxel pico lejano | 0,13 MW | 0,29 MW | p < 0,0001 |
| exceso del píxel pico del cráter | 0,06 MW | 0,04 MW | p = 0,008 |
| log10(pico lejano / pico cráter) | +0,34 | +1,01 | p < 0,0001 |
| distancia del lejano al centro de grilla | 16,5 km | 19,3 km | p = 0,52 |
| lejano a más de 25,5 km del centro | 0 de 15 | 0 de 38 | |
| MIROVA alerta ese sitio en otra pasada (a 2 km) | 3 de 15 | 5 de 38 | |
| log10(cráter TIF, suma 3 × 3 / VRP MIROVA) | **+0,12** | | |
| log10(cráter + lejano TIF / VRP MIROVA) | +0,55 | | |

- Permutando la etiqueta **dentro de cada volcán** (10.000 sorteos), la diferencia en z del lejano da p = 0,0001:
  no la produce la mezcla de volcanes.
- **No es un factor único.** Regresión logística (lejos = 1, n = 53), AIC: z del lejano 49,2; pico lejano 40,9;
  razón pico lejano / pico cráter 44,2; pico cráter solo 59,4; **pico lejano más pico cráter 30,7**. Agregar el
  cráter al pico lejano mejora la verosimilitud con p = 0,0005. O sea: **fuerza absoluta o relativa del lejano, sin
  separar, con el cráter como segundo predictor** (más cráter, más "cerca"). Parte de eso es selección: en las
  alertas MIROVA alertó el cráter, así que ahí el cráter tiene que estar caliente.
- **La frontera es blanda**: con z del lejano entre 18 y 26 hay 5 "cerca" y 10 "lejos", y en Isluga el
  2026-09-19 la pasada de las 05:00 se informó lejos con z 24,4 y la de las 05:42 cerca con z 20,5.
- No separan la distancia al centro, la esquina de la grilla ni que el sitio sea recurrente.
- En las 15 el VRP que MIROVA publica calza con el **cráter solo** (+0,12, igual que la calibración de las alertas,
  +0,14), no con cráter más lejano (+0,55): **el foco lejano no entró en el VRP de MIROVA**. En 12 de las 15 el
  foco lejano pesa más que el cráter en el TIF, así que si MIROVA lo hubiera alertado, "la mayor" informaría lejos
  y "la suma" también. Lo más simple compatible es que MIROVA **no lo alertó**: el foco pasa nuestra prueba y no la
  de MIROVA.

Volcanes de las 15: Isluga 6, Láscar 5, Lastarria 2, Llaima 1, Puyehue Cordón Caulle 1. Satélites: NOAA-21 11,
NOAA-20 4 (en las 38 lejanas: NOAA-21 19, NOAA-20 14, Suomi NPP 5). Cada caso con fecha, energías y distancia
está en `estudio_salida.txt` §P4. Solo verificadas: 9 de 23 alertas con foco, mismas diferencias (z p = 0,0005;
permutación dentro de volcán p = 0,0005; pico lejano más cráter AIC 17,3 contra 24,8 del pico lejano solo).

**Por qué nuestro detector alerta focos que MIROVA no (SOSPECHA).** La versión 2 proponía el umbral más exigente
fuera de la cumbre (dual ROI). **Eso quedó refutado**: en `pipeline.profile` (leído hoy) el dual ROI está
encendido en los dos pases (`ENABLE_DUAL_ROI_FIRST_PASS` y `_SECOND_PASS` en True; C1 0,003 en la cumbre y 0,010
en la escena; C2 5 y 10), los 15 píxeles lejanos quedan fuera de nuestro inner, así que ya les aplicamos el umbral
de escena, y en 7 de las 15 `diag_n_second_pass_recapture = 0`, o sea que los alertó el primer pase (Tests 2 y 3),
no la recaptura. El candidato ya medido es la **conectiva `min`** de los Tests 2 y 3
(`ENABLE_TESTS_23_PROSE_BRANCH = False`, S148): con `min` basta superar el menor de los dos umbrales (el piso C1 o
μ + C2·σ), y S148 midió que `max`
baja los falsos de VIIRS 375 de 29,8 a 2,7 %. Es SOSPECHA porque los flags leídos son los de hoy, no los de la
fecha de cada record. **El A/B de F y K en curso (conectiva `max`, run 38639658446) puede contestarla**: si con
`max` esos píxeles lejanos débiles dejan de alertarse, la causa era la conectiva.

**Costo para un brazo A2.** Si la réplica eligiera la anomalía mayor con nuestro detector actual, en estas 36
pasadas informaría lejos donde MIROVA informó el cráter: en las 15 con foco real porque nuestro detector alerta
focos que MIROVA no alerta, y en las 21 sin foco porque ahí nuestro píxel lejano ni siquiera es un objeto visible
en la imagen de MIROVA. **El diseño del brazo A2 queda en espera del resultado de F y K**, y antes de inventar un
umbral fuera de la cumbre hay que medir la conectiva.

## 5. P2 y P3: la tabla simétrica

La versión 1 contaba sólo filas lejanas ("28 en contra de cráter primero"), y eso es circular: la muestra ya eran
pasadas que MIROVA informó lejos. Ahora: todas las pasadas VIIRS 375 con TIF (lejanas y alertas) con calor en el
cráter y un foco lejano fuerte a la vez, contando cuántas informó MIROVA lejos y cuántas cerca. "Foco lejano
fuerte" de dos maneras: el más fuerte de la escena fuera del corte del scraper y a más de 5 km del cráter
(z ≥ 20,1), o el que está en nuestro píxel lejano (z ≥ 10,6). Las 15 alertas de §4 entran aquí.

| VIIRS 375, sin las rechazadas | lejos | cerca |
|---|---|---|
| cráter z ≥ 3,3; foco de escena | 22 | 5 |
| cráter z ≥ 3,3; foco en nuestro píxel | 18 | 14 |
| cráter z ≥ 3,3; cualquiera de los dos | 27 | 15 |
| cráter tan caliente como la mediana de las alertas (z ≥ 7,2); cualquiera | 8 | 9 |
| **por fuerza del foco lejano** (cráter z ≥ 3,3): z 10,6 a 20 | 5 | 10 |
| z 20 a 40 | 12 | 5 |
| z 40 o más | **10** | **0** |

Solo verificadas: 2 contra 6, 8 contra 3 y 6 contra 0 en los mismos tramos de fuerza.

Tres advertencias sobre esta tabla:
- **Contiene a §4**: de sus 15 "cerca", 14 son los mismos casos de P4. No es evidencia independiente.
- **Los cortes 20 y 40 vienen de la versión 1** y se eligieron sabiendo que sobre 40 había 0 "cerca". Sin cortes,
  la prueba continua (Mann-Whitney del z del lejano, lejos contra cerca) da **p = 9e-5**; con otro corte, z ≥ 30:
  **15 lejos contra 0 cerca**, y bajo 30, 12 contra 15. Solo verificadas: p = 0,0008; z ≥ 30, 8 contra 0.
- El z del foco lejano es la mayor de las dos definiciones; la logística de §4 dice que el cráter también pesa.

**Veredicto de P3, por regla:**
- **El cráter si hay algo en el cráter** y **el más cercano al centro**: en contra con **10 de 10** cuando el foco
  lejano es fuerte (27 en total con cualquier fuerza). A favor sólo cuando el foco lejano es débil, y ahí (§4) el
  foco no entró en el VRP de MIROVA, así que esas pasadas no prueban una preferencia por el cráter.
- **La mayor** y **la suma de todo lo alertado** (con la distancia del más lejano): las dos predicen lejos si el
  foco lejano está alertado. Ninguna queda refutada, porque los casos "cerca" son focos que MIROVA muy
  probablemente no alertó, y ninguna se separa de la otra con la dirección.
- **Un corte blando por fuerza absoluta o relativa del foco lejano, con el cráter como segundo predictor**: es lo
  que mejor describe los datos. No es una regla de selección medida: es lo que se ve desde fuera sin saber qué
  píxeles alertó MIROVA.

## 6. T3: magnitud, "la mayor" contra "la suma"

En las lejanas con el cráter tan caliente como en una alerta (n = 8), log10(energía TIF / VRP MIROVA): lejano solo
+0,020 contra la calibración +0,106 (lejanas con cráter frío, n = 56); lejano más cráter +0,181 contra la
calibración con ruido +0,130. **No es una p = 0,046 firme**:

- sacando un caso a la vez, la p del "lejano solo" va de **0,005 a 0,120**;
- por volcán: Láscar (4 de los 8) da +0,029 con p = 0,48; los otros cuatro, −0,000 con p = 0,028;
- rechazando el TIF dudoso sobre 3 K (Planchón Peteroa 2026-05-17, 3,33 K): p = **0,109**;
- solo verificadas (n = 7): p entre 0,004 y 0,107 sacando un caso a la vez;
- y en §4, en las 38 lejanas con foco en nuestro píxel (cráter más débil), el VRP calza mejor con el lejano solo
  (+0,11) que con la suma (+0,19) contra la misma calibración.

**"La suma" frente a "la mayor": no demostrado.** El dato apunta débilmente a la suma cuando el cráter está
caliente y no distingue nada cuando el cráter es débil.

## 7. Láscar, NOAA-21, 2026-10-01 05:18

- La fila de MIROVA (1,2 MW a 1,22 km) es **solo OCR**: no está en la tabla `latest.php`. En esas filas el VRP es
  de su pasada pero la distancia viene de la estrella de otra (memoria `reference_ocr_imagen_de_otra_pasada`,
  Mirova-v1#20). La fila de las 05:54 trae la misma distancia, 1,22 km.
- No hay GeoTIFF. Sí están las láminas "Latest" que guardó el scraper (cabecera "Last Update 06:18:01"): diez
  miniaturas del mismo campo, de 150 × 150 píxeles.
- **Georreferencia de las miniaturas, calibrada contra TIF** (`lascar_20261001.py` §1, con las coordenadas a 5
  decimales): en 12 de 14 láminas de lejanas anteriores al 22-sep la miniatura de esa pasada muestra el foco
  (z ≥ 10) a **0,42 km en mediana** (máximo 0,69 km) de donde lo pone el TIF; la misma ventana en las otras nueve
  miniaturas da z 2,8 y nunca pasa de 10. El criterio de calibración se escribió **después** de la primera
  corrida (la primera pedía que la mejor celda doblara la correlación de la segunda, y casi ninguna lo cumplía).
  La versión 1 leía coordenadas con 4 cifras significativas y daba 0,66 km.
- **La miniatura de las 05:18:02** (cabecera ZEN 32°, AZI 101°; nuestro record NOAA-21: 32,36° y 101,77°; la celda
  es idéntica pixel a pixel en las dos láminas que la traen): el foco más fuerte de la escena está a **0,54 km de
  nuestro píxel lejano**, a 19,5 km del cráter, con z 28,9 (el mismo punto girado: mediana 1,2, máximo 3,5). El
  cráter también tiene calor (z 15,5). En las de las 05:54 y 06:18 ese punto no tiene nada (z 1,1 y 0,5).
- **Ojo**: el z de la miniatura es exceso de **luminancia** de la imagen, con una escala de color desconocida.
  "Más fuerte que el cráter" compara luminancias dentro de una misma miniatura, no MW.

**Respuesta**: nuestro objeto lejano es real y MIROVA lo tenía en su imagen. Por fuerza (z 28,9 en luminancia, que
no es el z del TIF) no se puede ubicar en los tramos de §5. El 1,2 MW (unas 9 veces nuestro cúmulo del cráter,
0,138 MW) se explicaría mejor con el lejano incluido, pero no se puede pasar luminancia a MW, y la distancia de
1,22 km no es de esa pasada. La premisa de P5 del pre-registro ("MIROVA 1,2 MW en el cráter") queda **sin
respaldo**, y el caso no decide la regla.

Observación sin explicar (leída a ojo): en la lámina "Latest" que el archivo de TIF guardó a las 12:37 del mismo
día (`data/png/Lascar/20261001_123714_VIIRS375_Latest10NTI.png`) las celdas de las 05:18 y 05:54 ya no aparecen.

## 8. Qué cambió respecto de la versión 1 (verificador del PR #809)

1. Nueva §4 con las 36 alertas: la fuerza del foco lejano separa cerca de lejos; la conclusión principal pasó de
   "la suma" a "un corte por fuerza".
2. La tabla circular de las "28 en contra" se reemplazó por la simétrica (§5), que incluye las alertas.
3. T3 se presenta sacando un caso a la vez, por volcán y sin el TIF dudoso (§6); "la suma" quedó como no
   demostrada.
4. Se agregó el nulo de otras noches (§3); el girado se conserva pero ya no sostiene nada.
5. `pasadas.csv` guarda 7 cifras significativas (lat/lon con 5 decimales); la calibración de las miniaturas bajó
   de 0,66 a 0,42 km en mediana; se dice que el criterio es posterior a la primera corrida y que el z de la
   miniatura es luminancia.
6. Se dice cuántas de las lejanas sin coincidencia caen en la esquina de la grilla de MIROVA (§3).

Versión 3 (segundo verificador, sobre 8394d0a63; confirmó la separación por fuerza y que el VRP de MIROVA calza
con el cráter solo):

1. La SOSPECHA del dual ROI quedó refutada (§4) y se reemplazó por la conectiva `min`, también como SOSPECHA,
   con el A/B de F y K como prueba.
2. "La fuerza decide" pasó a "fuerza absoluta o relativa, sin separar, con el cráter como segundo predictor"
   (logística, §4), con la frontera blanda y el caso de Isluga.
3. §5 dice que contiene a §4, que sus cortes son de la v1, y agrega la prueba continua y el corte en 30.
4. La energía del foco lejano es el exceso del píxel pico, no la suma 3 × 3.
5. El brazo A2 queda en espera de F y K; antes de un umbral nuevo fuera de la cumbre, medir la conectiva.

## 9. Lo que no se pudo resolver

- **Qué píxeles alertó MIROVA.** Es la pieza que falta para separar "la mayor" de "la suma" y para fijar el corte
  por fuerza. Sólo el OSF (que trae píxel más caliente, píxel más lejano y número de píxeles por fila) o una
  respuesta de Coppola lo dirían.
- **Las 242 lejanas sin TIF.** Después del 22-sep sólo quedan las miniaturas, y sólo se miró el caso de Láscar.
- **MODIS y VIIRS 750**: pocos casos (4 y 4 lejanas con foco); nada de lo de arriba vale para ellos solos. En
  MODIS el control de atribución no funciona.
- **El origen exacto de la distancia** (centro del raster contra nodo de la grilla, S139 §5) se absorbió en la
  tolerancia del anillo (0,75 km en VIIRS 375); no se midió.
- **La naturaleza de los focos lejanos** (incendio, faena, nube): no se miró.

## 10. Cómo se reproduce

```
set VRP_TIF_CACHE=<carpeta fuera del repo>
python experiments/_s151_seleccion_mirova/estudio.py
python experiments/_s151_seleccion_mirova/lascar_20261001.py
```

Fijados: índice de TIF en el commit `3660cdfa77` de `MendozaVolcanic/mirova-tif-archive`, láminas en el commit
`f14f721f57` de `MendozaVolcanic/Mirova-v1`, referencia de MIROVA con el sha256 que imprime la salida. Baja
unos 1.050 TIF y unas 20 láminas (111 MB en total). `lascar_20261001.py` lee `pasadas.csv`: correr primero
`estudio.py`.
