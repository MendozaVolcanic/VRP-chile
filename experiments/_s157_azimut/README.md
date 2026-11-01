# S157: ¿importa desde qué lado mira el satélite?

Pregunta de Nicolás tras S130 (`docs/s130/GRADIENTE_CENITAL.md`): además del ángulo cenital,
¿hay un efecto de azimut, o sea de si el satélite mira el volcán desde el este o desde el oeste?

## El fenómeno y lo que se esperaba

Un cráter profundo visto en oblicuo deja oculta la pared que da hacia el satélite y muestra la
opuesta. Si el foco caliente está pegado a una pared, mirar desde el este o desde el oeste cambia
cuánto de él entra en el píxel. Ese efecto lo sufren igual MIROVA y nosotros, porque los dos
leemos el mismo gránulo: la **razón** nuestra/MIROVA no debería depender del lado. Si depende, la
causa es de procesamiento (remuestreo de MIROVA a malla UTM, D17; bow tie; geolocalización).

## En corto

* Lo que resiste todos los controles es **la razón nuestra/MIROVA más baja cuando el satélite mira
  desde el este**, sobre todo en oblicuo (0,865 en el agregado, 0,685 desde 35°, 0,79 noche a noche
  sin Isluga). La razón se mueve porque se mueve MIROVA, no nosotros.
* El tamaño del efecto en MIROVA depende de Isluga: con él, 1,46; sin él, 1,2 a 1,4 según el
  control, y la prueba noche a noche deja de ser significativa.
* En VIIRS el lado no se puede separar de la hora de la pasada: son la misma variable.

## Cómo se sabe el lado

Cada record guarda `sensor_azimuth_deg` desde S122 (`pipeline/scan_geometry.py`,
`observation_geometry`, en el píxel más cercano al hotspot). En la ventana 2026 de los 11 Tier A
lo traen 30.812 records nocturnos y les falta a 309 (`nocturnos_en_ventana` en
`resultado_lado.json`). La convención se comprobó de dos formas dentro de `medir_lado_del_barrido.py`:

* contra el banner de MIROVA (columna `Azimut_Sat_deg` del CSV OCR), misma pasada a ±120 s:
  **252 de 252** con el mismo lado, diferencia mediana de azimut 0,64°. Esto sólo prueba que los
  dos usamos la misma convención (probablemente el mismo campo del L1B);
* por orden orbital, que es la prueba física: en una noche y plataforma, cada órbita siguiente cruza
  más al oeste, así que la primera pasada tiene que ver el volcán desde el este. En VIIRS sale con
  azimut positivo en **1.816 de 1.816** noches con pasadas pareables; las 45 excepciones son todas
  MODIS (Terra y Aqua tienen horas de nodo distintas).

Azimut positivo = satélite al **este** del volcán. Se usa `sin(azimut)`: sobre +0,3 este, bajo
−0,3 oeste; el resto (6 records cerca del nadir, donde el azimut no tiene sentido) queda fuera.

## Pareos

* **PASADA** (el limpio para esta pregunta): nuestro `primary_cluster.vrp_mw` contra la alerta de
  MIROVA de la **misma pasada** (±120 s, el TOL del banco de paridad). Numerador y denominador
  salen del mismo gránulo y tienen el mismo azimut.
* **S130** (literal de `medir_gradiente_cenital.py`): cada record nuestro contra el máximo de
  MIROVA de la fecha y el sensor. Con una pasada de cada lado por noche, las dos se comparan
  contra el mismo máximo, que salió de una sola: el lado queda mezclado.

Hallazgo al pasar: el docstring de S130 (`experiments/_s130_cenital/medir_gradiente_cenital.py`
l. 20, y la definición que escribe en l. 102-103) dice «un par por (volcán, fecha, bucket), el
máximo de cada lado», pero el bucle de l. 77-94 agrega un par por record (l. 92-94) contra el
máximo diario de MIROVA. Es justo lo que `experiments/_s126_lib.py` l. 9-11 pide no hacer. No
cambia la lectura de S130 sobre el cenit, pero el texto y el código no dicen lo mismo.

Resto de las definiciones, iguales a S130: MIROVA = alertas CONS ∪ OCR con los alias de
`experiments/_s126_lib.py`, VRP > 0, hora UTC 3 a 9; pasadas nuestras con `solar_zenith_deg` ≥ 90;
ventana 2026; tramos de cenit 0-15, 15-25, 25-35, 35-50, 50+. Detector por record con
`auto_audit_weekly.detector_de_record` (K si trae `codigo_sha`), y C0 partido en antes de #535 y
desde #535 hasta K (A104).

## Efecto y nulo

El efecto es la diferencia este menos oeste de la mediana de log10, calculada **dentro de cada
celda volcán × tramo de cenit** y promediada con peso nE·nO/(nE+nO); se informa como factor
este/oeste. El nulo sortea el lado dentro de cada celda (2.000 permutaciones, 500 por volcán,
semilla fija) y da el intervalo del 95 % bajo azar. Se calcula aparte para nuestro valor, el de
MIROVA y la razón (el control de numerador y denominador de S130). Como las pasadas de una misma
noche no son independientes, `robustez_lado.py` agrega una **prueba de signo por noche**.

## Resultados (pareo PASADA)

Cifras de `resultado_lado.json` y `resultado_robustez.json`. Factor este/oeste, entre corchetes el
IC95 del nulo.

| detector · sensor | pares | nuestro | MIROVA | razón |
|---|---|---|---|---|
| C0 · VIIRS 375 | 1.369 | 1,145 [0,89 a 1,12] p 0,016 | **1,460** [0,89 a 1,14] p < 0,001 | **0,865** [0,93 a 1,07] p < 0,001 |
| C0 · VIIRS 750 | 232 | 0,830 [0,75 a 1,37] | 0,713 [0,73 a 1,40] p 0,044 | 0,840 [0,85 a 1,15] p 0,026 |
| C0 · MODIS | 48 | sin poder | sin poder | sin poder |
| K · VIIRS 375 | 198 | 0,481 [0,45 a 2,25] | 0,774 [0,48 a 2,11] | 0,689 [0,68 a 1,42] p 0,051 |
| K · VIIRS 750 / MODIS | 45 / 8 | sin poder | sin poder | sin poder |

**Crece con el cenit en MIROVA, no en nosotros** (C0, VIIRS 375, efecto estratificado): bajo 35°
MIROVA 1,16, nosotros 1,16, razón 1,06 (nada distinto del azar); desde 35° MIROVA **1,91** (nulo
0,83 a 1,27), nosotros 1,13 (dentro del nulo), razón **0,685**. A cenit 50+, mediana de MIROVA
0,32 MW desde el este contra 0,10 desde el oeste; la nuestra 0,10 contra 0,07.

**Por volcán** (C0, VIIRS 375, MIROVA este/oeste): Isluga 2,49, Tupungatito 1,57, Lastarria 1,41
(los tres con p ≤ 0,02), Puyehue-Cordón Caulle 1,30 (p 0,05), Láscar 1,22, Planchón-Peteroa 1,02 y
Chaitén 0,89 dentro del azar; Chillán, Villarrica, Llaima y Copahue sin pares suficientes por celda.

**Isluga pesa mucho.** Nuestro 1,145 es sólo Isluga: sin él queda en 1,03 (p 0,63). MIROVA sin
Isluga baja a 1,27 (p 0,001). En Isluga lo vemos los dos (nosotros 1,70, MIROVA 2,49), y es el único
volcán donde podría haber algo físico del cráter.

**Controles** (C0, VIIRS 375). Factor este/oeste de MIROVA y de la razón:

| variante | MIROVA | razón |
|---|---|---|
| base | 1,46 | 0,865 |
| celdas con plataforma | 1,41 | 0,877 |
| celdas con mes (nivel de actividad) | 1,52 | 0,840 |
| sólo tabla `latest.php`, sin OCR | 1,43 | 0,920 (p 0,047) |
| desde el 2026-06-13 (A119) | 1,48 | 0,863 |
| sin Isluga, celdas con mes | 1,22 (p 0,032) | 0,891 (p 0,042) |
| sin Isluga, desde 35°, celdas con mes | 1,39 (p 0,008) | 0,829 (p 0,011) |

**Prueba de signo por noche** (una noche, un voto: la pasada este y la oeste de la misma noche con
cenit a 10° o menos una de otra):

| | noches | nuestro | MIROVA | razón |
|---|---|---|---|---|
| todos | 124 | 1,09 (p 0,65) | **1,50** (E > O en 80 de 122, p < 0,001) | **0,76** (E > O en 33 de 124, p < 0,001) |
| sin Isluga | 99 | 0,97 (p 0,69) | 1,18 (p 0,15) | **0,79** (E > O en 28 de 99, p < 0,001) |

**Con el pareo literal de S130 no aparece** (MIROVA 1,02, razón 1,05 en C0 · VIIRS 375): la mezcla
de lados lo borra. Y explica algo de S130: «MIROVA es plano con el cenit» es el promedio de dos
pendientes opuestas, MIROVA sube con el cenit desde el este y baja desde el oeste.

## Lo que no se puede separar: lado y hora son la misma variable en VIIRS

En una órbita heliosincrónica la hora local a la que el satélite pasa sobre un punto queda fijada
por cuán al este o al oeste va la traza, y SNPP, NOAA-20 y NOAA-21 comparten la hora de nodo.
`hora_y_lado.py` mide la correlación entre la hora UTC y el cenit con signo (+ este): **Spearman
entre −0,990 y −0,996** en los 22 pares volcán × sensor VIIRS (MODIS −0,43 a −0,50, porque mezcla
Terra y Aqua). Al pedir celdas volcán × tramo × hora con los dos lados, sobreviven 437 de 1.369
pares y **ninguno** tiene cenit ≥ 35°: ese control borra el efecto porque borra las pasadas donde
vive, no porque lo explique (`+hora`, MIROVA 1,07 con un nulo de 0,83 a 1,19). Las noches en que la
primera pasada viene del oeste son todas MODIS. Así que «desde el este» y «primera pasada de la
noche, una hora a hora y media antes» no se distinguen con VIIRS.

MODIS sí desacopla lado y hora (Terra y Aqua), pero no tiene poder. Además, el filtro heredado de
S130 (hora UTC 3 a 9 para las alertas de MIROVA) descarta como diurnas las alertas nocturnas de MODIS
Terra de las 01 a 02 UTC; por eso quedan 48 pares en C0. Arreglar ese filtro es lo primero para
intentar separar lado de hora.

Lo que sí separa algo: si fuera un efecto físico del volcán (oclusión por una pared, o el suelo que
se enfría durante la noche), lo veríamos también nosotros en el mismo gránulo, y fuera de Isluga
nuestro numerador no se mueve. Lo que cambia es MIROVA.

## Lectura

* La caída de la razón con el cenit que encontró S130 vive sobre todo en las pasadas desde el este:
  razón mediana de 0,74 a 0,39 del nadir a 50+ desde el este, de 0,77 a 0,66 desde el oeste (medianas
  agrupadas por tramo, sin estratificar por volcán; el estratificado está arriba).
* En VIIRS 750 el signo de MIROVA se invierte (0,71, dominado por Láscar con 162 de 232 pares) y la
  razón también cae desde el este (0,84). Con 9 noches pareables no hay prueba por noche.
* No se identificó el mecanismo en MIROVA. Candidatos sin verificar: algo del remuestreo a malla UTM
  (D17) que no sea simétrico entre los dos lados del barrido; paralaje de una cumbre de 5 a 6 km si la
  geolocalización que usa MIROVA no corrige por terreno; o algo ligado a la hora de la pasada.

## No verificado

* El mecanismo en MIROVA. Pedirá mirar los GeoTIFF de MIROVA de pasadas este y oeste del mismo
  volcán (A106: la grilla UTM nativa sólo existió del 14 al 15 de septiembre).
* Lado contra hora: inseparable en VIIRS; en MODIS falta arreglar el filtro de 3 a 9 UTC.
* Detector K: 198 pares en VIIRS 375, dominados por Chillán (51); la razón cae desde el este (0,69,
  p 0,051) igual que en C0, pero MIROVA no repite el 1,46. Esperar más noches con K.
* MODIS: 48 pares en C0, 8 en K. Sin poder.
* Nuestro valor es `primary_cluster.vrp_mw`, el de S130; en VIIRS 375 el tablero publica
  `f5_core_vrp_mw`. Un verificador midió que con ese campo nuestro efecto cambia; no está commiteado.
* El filtro «ALERTA» heredado incluye filas ALERTA_SIN_GEOMETRIA_OCR; su efecto no se midió.
* Sin la regla D-9, para que el pareo sea el de S130.
* Sólo se parean pasadas donde detectamos los dos. Un verificador midió que, cuando MIROVA alerta,
  tenemos cúmulo en proporción casi igual desde los dos lados; tampoco está commiteado.
* Muchas comparaciones a la vez: lo que va con p < 0,001 sobrevive a cualquier corrección razonable;
  los p de 0,01 a 0,05 por volcán, en VIIRS 750 o en los controles sin Isluga, no.

## Reproducir

```bash
cd <worktree>
python experiments/_s157_azimut/medir_lado_del_barrido.py   # ~2,5 min
python experiments/_s157_azimut/robustez_lado.py
python experiments/_s157_azimut/hora_y_lado.py
```

## Verificadores con contexto limpio

Dos verificadores independientes, con código propio (no importaron estos scripts), reprodujeron
exactas las cifras centrales (1,460 / 1,145 / 0,865; 1,91 desde 35°) y confirmaron:

* la convención del azimut, contra el banner de MIROVA y por orden orbital (en VIIRS sin excepciones);
* el pareo: desfase 0 s en todos los pares, ninguna alerta de MIROVA usada dos veces, ningún record
  con dos candidatas; los duplicados CONS/OCR tienen hora idéntica y se funden con el máximo;
* el nulo: con efecto sintético 1,00 da 5 % de p < 0,05, con 1,15 recupera 1,145 y con 1,46
  recupera 1,451; con el lado sorteado desde el inicio, 4 % de p < 0,05;
* la discrepancia entre el docstring y el código de S130, con archivo y línea;
* que lado y hora no se separan con VIIRS.

Matizaron: nuestro efecto es sólo Isluga, el de MIROVA sin Isluga se debilita con control de
actividad, y lo más sólido es la razón. Encontraron además el filtro de 3 a 9 UTC que deja a MODIS
sin poder. Este README ya incorpora esas correcciones, y los controles por mes y por noche están en
`robustez_lado.py`. Sus scripts quedaron fuera del repo, en el directorio temporal de la sesión.
