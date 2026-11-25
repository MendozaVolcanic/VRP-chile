# P0 parte (3): ¿una anomalía grande esconde un foco débil en otra parte del edificio? (VIIRS 750)

Sesión S200, 2026-11-25. Detector de producción de origin/main `b7626b03c` sin modificar. Todo lo de esta carpeta
(`D:\vrp-trabajo\temporales\s200\p0_3\`) sale de scripts con su salida al lado; no se tocó `pipeline/` ni el checkout.

## 1. Respuesta corta

**En el flanco, no.** En las 10 pasadas reales y con la anomalía de Chillán trasplantada a otros 9 volcanes a 13, 40,
134 y 403 MW, un foco nuevo a 5, 10 o 20 km del calor conocido necesita la misma potencia para alertar con la anomalía
que sin ella: la razón con/sin es 1,000 en mediana y no pasa de 1,25 en ninguna dirección de las zonas 0 y 1 (Tabla 2).
Por el criterio fijado antes de medir es un **resultado nulo** para «otra parte del edificio», salvo en Tupungatito,
cuya región sensible abarca el edificio entero y donde el efecto es **menor** (razón mediana hasta 1,10 con el
trasplante de 13 MW y 1,17 con el de 134 MW a 5 km).

**Pegado al cráter (2 km), sí hay un enmascaramiento chico.** Dentro de la región sensible la razón mediana agrupada va
de 1,00 a 1,10 (Tabla 2); por escena llega a 1,30 a 2 km y a 2,04 en una sola dirección. Se explica entero por el
mecanismo que el plan describía, pero el segundo pase lo desarma casi todo.

**Lo que de verdad decide si un foco nuevo en el flanco se ve es dónde cae respecto de la caja, no la anomalía.** Sin
anomalía, un foco a 1000 K alerta desde 0,34 MW en la región sensible (unos 5 m² de superficie a 1000 K) y desde 1,4 MW
fuera de ella (unos 22 m²): cuatro veces más, por el piso fijo de 0,02 en NTI (§5.3). Y la nube o el ruido de la escena
mueven el umbral mucho más que cualquier anomalía (control C4).

Los cuatro controles pasaron (§6). El trasplante tal como se pre-registró tenía un defecto que sólo se vio al correrlo
(escalaba también el déficit frío de la cumbre) y su escala 10 es un artefacto; se dice en §4.4 y se corrigió con una
variante post hoc declarada antes de correrla (`ADENDA_POSTHOC.md`).

## 2. El fenómeno, en lenguaje de geólogo

Imagina Cordón Caulle con el lacolito caliente en el cráter, o Villarrica con su lago de lava, y que en el flanco se abre
una fisura chica, un domo o una fumarola que empieza a calentarse. Desde el satélite ese foco nuevo ocupa una fracción
mínima de un píxel de 750 m: unos metros cuadrados a cientos de grados. Para saber si un píxel está «caliente», MIROVA no
mira su temperatura absoluta sino cuánto se aparta de lo normal en la escena: compara cada celda con sus vecinas y exige
que ese contraste supere un umbral que crece con lo «revuelta» que esté la escena (media más s veces la desviación
estándar de todos los contrastes de la grilla de 50 km, con un piso fijo).

La preocupación de Nicolás es razonable: si la escena tiene una anomalía grande, sus celdas calientes y su borde tibio
agrandan la desviación estándar, el umbral sube en toda la grilla, y un foco nuevo y débil en el flanco quedaría bajo
ese umbral más alto: escondido detrás de la anomalía conocida. El código de MIROVA tiene un remedio parcial: corre la
detección dos veces y en la segunda saca de la estadística las celdas que ya alertaron. Lo que no saca es el borde tibio
que no alcanzó a alertar. La pregunta era cuánto pesa eso en la práctica.

## 3. Por qué el resultado es casi nulo (el mecanismo, con los números de la escena de Chillán)

En Nevados de Chillán 2026-10-10 05:54 (5 celdas alertadas, 13,1 MW) el primer pase sí ve el efecto: la desviación
estándar del contraste NTI sube de 0,0009 (la misma escena sin la anomalía) a 0,0032, y el umbral sensible de 0,0045 a
0,0158 (Tabla 3). Pero el segundo pase saca las 5 celdas calientes y la desviación vuelve a 0,00115: el umbral sensible
queda en 0,0057, un 27 % sobre el de la escena limpia. La máscara final es la unión de los dos pases, así que lo que
manda es el segundo. Dos razones más lo achican:

1. **No hay halo tibio que quede.** En las 9 escenas con alerta, la mediana de la temperatura de brillo M13 de 0,5 a
   10 km del pico es más fría que el anillo de 8 a 12 km (la cumbre está más alta y más fría), salvo Chaitén con +1 K
   (`explorar_halo_salida.txt`). El «borde tibio» del que se temía es, en estas escenas, la mancha que deja la
   interpolación lineal de un píxel sobre las celdas vecinas, y esas celdas alertan con el pico o quedan muy cerca.
2. **Fuera de la región sensible manda el piso, no la anomalía.** En las zonas 0 y 1 el umbral es max(mu + 10·sd,
   0,02). Con sd de 0,001 del segundo pase, mu + 10·sd ronda 0,01: el piso de 0,02 queda arriba y la anomalía no lo mueve.
   Para que lo mueva, sd del segundo pase tendría que pasar de unos 0,002, y ningún trasplante físico lo logró (máximo
   0,0017, Tabla 3 y `resumen_posthoc_salida.txt`).

Un detalle que no se esperaba: la razón no crece con la potencia de la anomalía. Con el trasplante de 403 MW es menor
que con el de 13 MW (zona sensible, mediana 1,02 contra 1,10). Una anomalía muy fuerte supera el Test 1 (NTI > -0,7) en
todas sus celdas y sale entera de la estadística ya en el primer pase; una moderada deja celdas a medio camino.

## 4. Método

### 4.1 Pre-registro

`PREREGISTRO.md`, sha256 `bc8036ef14dda369284a9ed24a88f3828eb1f87f0b7ce4f27625b85a6c379777`, escrito antes de medir
(sólo se habían corrido las exploraciones de entrada que nombra). La adenda post hoc `ADENDA_POSTHOC.md`, sha256
`0239c685076936881bd8f41d556106d562687d59f931750a97eb3fe20d5656cb`, se escribió después de ver la serie T y antes de
correr su variante. Los dos sha256 se verifican con `sha256sum -c PREREGISTRO.sha256 ADENDA_POSTHOC.sha256` (OK al
cierre).

### 4.2 Escena y detector

Los 10 recortes de S158 (píxeles de VIIRS 750 a menos de 45 km del volcán, con M13 y M15 en radiancia) se arman como
`calcular_vrp_granulo`: grilla de MIROVA del volcán, interpolación lineal a 67 × 67 celdas de 750 m
(`remuestrear_grilla`), caja de `grillas_mirova.yaml` (def en la mayoría, crater en Cordón Caulle, sens en Tupungatito),
cráter de `get_detection_anchor`, y noche y reflejo solar con los cuatro ángulos del píxel central que guardó el mismo
run (`resultados.json`). Las 10 son nocturnas, con reflejo solar entre 113 y 149 grados. El detector se importa de una
copia de `pipeline/` de origin/main hecha con `git archive` (`main_snapshot/`), con perfil `mirova_equivalent`.

### 4.3 El foco

Un píxel mezcla en el gránulo, antes de interpolar: una fracción f del píxel a 1000 K (lava o conducto incandescente;
600 K como secundaria) y el resto con la radiancia que ya tenía, en M13 y M15 con la Planck del .m. La potencia del foco
se expresa como VRP_eq = 11,08 MW por unidad de exceso de M13 (el coeficiente de la vía, 1,97e7 × 0,5625 km²). El
píxel es el más cercano al punto objetivo entre los que llegan con peso de 0,3 o más a alguna celda. Como la
interpolación lineal con triangulación fija es lineal en los valores, la grilla con el foco es la base más el exceso por
la columna del píxel en la matriz de interpolación (control C2). Barrido logarítmico de 0,02 a 200 MW en 25 pasos y 7
bisecciones: resolución mejor que 0,4 %. El foco «alerta» si alguna celda de su huella (peso 0,25 o más) queda en la
máscara del detector. Distancias 2, 5, 10 y 20 km desde la celda más radiante de la anomalía, en 8 direcciones. Se
descartan los puntos cuya huella toca una celda ya alertada (o vecina) en cualquier brazo, o el borde.

### 4.4 Brazos

- **R (real)**: la escena tal cual contra la misma con la anomalía quitada (celdas alertadas más el halo del .m, 3, 5 o
  7 celdas según cuántas, rellenadas con `_fillmissing2_lineal` de producción, el mismo fondo con que la vía mide el
  VRP). Sensibilidad con halo de 9 celdas: igual (razón mediana 1,00 en todas las distancias de 5 km o más,
  `resumen_salida.txt`).
- **T (trasplante, pre-registrado)**: sólo Chillán tiene una anomalía fuerte, así que su exceso real de M13 y M15 se
  sumó al cráter de las otras 9 escenas a escala 1, 3 y 10. **Defecto visto al correrlo**: 34 de las 45 celdas del
  parche tienen exceso negativo, porque la cumbre de Chillán es más fría que el fondo interpolado; a escala 10 ese
  déficit frío produce celdas con M13 de cero o menos y BT15 de hasta 143 K (`diag_parche_salida.txt`). Esa escala da
  razones de hasta 38 (Tupungatito 2026-08-21), pero es un artefacto: la anomalía misma deja de detectarse (3 celdas
  contra 9 a 13 en las demás escenas, sd del pase 1 de 0,033, Tabla 3 y `resumen_salida.txt`). Se reporta en la Tabla 2 y no se usa para concluir. Lo que sí
  enseña: si muchas celdas anómalas escapan al Test 1 y al primer pase, el segundo pase no alcanza a limpiar la
  estadística y el detector colapsa. Si una anomalía real extensa (un campo de lava de muchas celdas tibias) puede
  provocarlo: SIN DATO; ningún trasplante físico, hasta 403 MW, lo hizo.
- **T+ (post hoc, declarado)**: el mismo trasplante con sólo la parte caliente (exceso positivo de cada banda), a escala
  1, 3, 10 y 30; la vía mide 12,6 a 14,4, 38 a 42, 132 a 137 y 400 a 405 MW (`vrp_trasplantes_salida.txt`).

## 5. Resultados

### Tabla 1. Foco a 1000 K: VRP_eq mínimo sin la anomalía y razón con/sin (mediana de las direcciones; máximo)

R: la escena real con su anomalía contra la misma con la anomalía quitada. T+: trasplante del exceso caliente de Chillán al cráter, escala 1, 3, 10 y 30 (unos 13, 40, 134 y 403 MW medidos por la vía, `vrp_trasplantes_salida.txt`), contra la escena destino sin trasplante. Zona: 2 sensible, 1 conservadora, 0 resto de la grilla (umbrales conservadores).

| escena | cenit | d km | zona | n dir R | VRP_eq mín sin (MW) | r R | n dir T+ | r T+ x1 | r T+ x3 | r T+ x10 | r T+ x30 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Chaiten_2026-10-06_0530 | 13,0 | 2 | 2 | 8 | 0,38 | 0,99; 1,01 | 3 | 1,15; 1,19 | 1,12; 1,15 | 1,08; 1,11 | 1,01; 1,01 |
| Chaiten_2026-10-06_0530 | 13,0 | 5 | 1 | 8 | 1,49 | 1,00; 1,00 | 8 | 1,00; 1,00 | 1,00; 1,00 | 1,00; 1,00 | 1,00; 1,00 |
| Chaiten_2026-10-06_0530 | 13,0 | 10 | 0,1 | 8 | 1,49 | 1,00; 1,00 | 8 | 1,00; 1,00 | 1,00; 1,00 | 1,00; 1,00 | 1,00; 1,00 |
| Chaiten_2026-10-06_0530 | 13,0 | 20 | 0 | 8 | 1,67 | 1,00; 1,00 | 8 | 1,00; 1,00 | 1,00; 1,00 | 1,00; 1,00 | 1,00; 1,00 |
| Lascar_2026-09-26_0548 | 0,4 | 2 | 1,2 | 8 | 0,58 | 1,01; 1,10 | 4 | 1,29; 1,31 | 1,05; 1,05 | 1,15; 1,17 | 1,02; 1,02 |
| Lascar_2026-09-26_0548 | 0,4 | 5 | 1 | 8 | 1,39 | 1,00; 1,00 | 8 | 1,00; 1,00 | 1,00; 1,00 | 1,00; 1,00 | 1,00; 1,00 |
| Lascar_2026-09-26_0548 | 0,4 | 10 | 0,1 | 8 | 1,19 | 1,00; 1,00 | 8 | 1,00; 1,00 | 1,00; 1,00 | 1,00; 1,00 | 1,00; 1,00 |
| Lascar_2026-09-26_0548 | 0,4 | 20 | 0 | 8 | 1,31 | 1,00; 1,00 | 8 | 1,00; 1,00 | 1,00; 1,00 | 1,00; 1,00 | 1,00; 1,00 |
| Lascar_2026-10-08_0542 | 1,4 | 2 | 2 | 7 | 0,26 | 1,00; 1,11 | 4 | 1,30; 1,36 | 1,06; 1,16 | 1,19; 1,52 | 1,04; 2,02 |
| Lascar_2026-10-08_0542 | 1,4 | 5 | 1 | 8 | 0,97 | 1,00; 1,00 | 8 | 1,00; 1,00 | 1,00; 1,00 | 1,00; 1,00 | 1,00; 1,00 |
| Lascar_2026-10-08_0542 | 1,4 | 10 | 0,1 | 8 | 1,25 | 1,00; 1,00 | 8 | 1,00; 1,00 | 1,00; 1,00 | 1,00; 1,00 | 1,00; 1,00 |
| Lascar_2026-10-08_0542 | 1,4 | 20 | 0 | 8 | 1,56 | 1,00; 1,00 | 8 | 1,00; 1,00 | 1,00; 1,00 | 1,00; 1,00 | 1,00; 1,00 |
| Llaima_2026-10-10_0554 | 23,1 | 2 | 2 | 8 | 0,28 | 1,00; 1,00 | 2 | 1,21; 1,22 | 1,01; 1,04 | 1,10; 1,14 | 1,02; 1,03 |
| Llaima_2026-10-10_0554 | 23,1 | 5 | 1 | 8 | 1,41 | 1,00; 1,00 | 8 | 1,00; 1,00 | 1,00; 1,00 | 1,00; 1,00 | 1,00; 1,00 |
| Llaima_2026-10-10_0554 | 23,1 | 10 | 0,1 | 8 | 1,53 | 1,00; 1,00 | 8 | 1,00; 1,00 | 1,00; 1,00 | 1,00; 1,00 | 1,00; 1,00 |
| Llaima_2026-10-10_0554 | 23,1 | 20 | 0 | 8 | 1,65 | 1,00; 1,00 | 8 | 1,00; 1,00 | 1,00; 1,00 | 1,00; 1,00 | 1,00; 1,00 |
| NevadosDeChillan_2026-10-10_0554 | 22,4 | 2 | 1,2 | 2 | 0,66 | 1,09; 1,19 | 0 | n/a | n/a | n/a | n/a |
| NevadosDeChillan_2026-10-10_0554 | 22,4 | 5 | 1 | 8 | 1,54 | 1,00; 1,00 | 0 | n/a | n/a | n/a | n/a |
| NevadosDeChillan_2026-10-10_0554 | 22,4 | 10 | 0,1 | 8 | 1,61 | 1,00; 1,00 | 0 | n/a | n/a | n/a | n/a |
| NevadosDeChillan_2026-10-10_0554 | 22,4 | 20 | 0 | 8 | 1,68 | 1,00; 1,00 | 0 | n/a | n/a | n/a | n/a |
| PuyehueCordonCaulle_2026-10-10_0554 | 23,8 | 2 | 2 | 7 | 0,69 | 1,00; 1,10 | 3 | 1,06; 1,06 | 1,07; 1,07 | 1,04; 1,04 | 1,01; 1,01 |
| PuyehueCordonCaulle_2026-10-10_0554 | 23,8 | 5 | 0,1 | 8 | 1,49 | 1,00; 1,00 | 8 | 1,00; 1,00 | 1,00; 1,00 | 1,00; 1,00 | 1,00; 1,00 |
| PuyehueCordonCaulle_2026-10-10_0554 | 23,8 | 10 | 0,1 | 8 | 1,18 | 1,00; 1,00 | 8 | 1,00; 1,00 | 1,00; 1,00 | 1,00; 1,00 | 1,00; 1,00 |
| PuyehueCordonCaulle_2026-10-10_0554 | 23,8 | 20 | 0 | 7 | 1,91 | 1,00; 1,00 | 7 | 1,00; 1,00 | 1,00; 1,00 | 1,00; 1,00 | 1,00; 1,00 |
| PuyehueCordonCaulle_2026-10-16_0542 | 4,8 | 2 | 2 | 8 | 0,54 | 1,00; 1,34 | 3 | 1,09; 1,12 | 1,11; 1,14 | 1,05; 1,06 | 1,00; 1,00 |
| PuyehueCordonCaulle_2026-10-16_0542 | 4,8 | 5 | 0,1 | 8 | 1,63 | 1,00; 1,00 | 8 | 1,00; 1,00 | 1,00; 1,00 | 1,00; 1,00 | 1,00; 1,00 |
| PuyehueCordonCaulle_2026-10-16_0542 | 4,8 | 10 | 0,1 | 8 | 1,66 | 1,00; 1,00 | 8 | 1,00; 1,00 | 1,00; 1,00 | 1,00; 1,00 | 1,00; 1,00 |
| PuyehueCordonCaulle_2026-10-16_0542 | 4,8 | 20 | 0 | 7 | 1,41 | 1,00; 1,00 | 7 | 1,00; 1,00 | 1,00; 1,00 | 1,00; 1,00 | 1,00; 1,00 |
| Tupungatito_2026-03-01_0536 | 5,9 | 2 | 2 | 8 | 0,44 | 1,01; 1,09 | 3 | 1,12; 1,16 | 1,03; 1,04 | 1,07; 1,10 | 1,02; 1,02 |
| Tupungatito_2026-03-01_0536 | 5,9 | 5 | 0,2 | 8 | 0,53 | 1,00; 1,00 | 8 | 1,10; 1,11 | 1,02; 1,03 | 1,06; 1,07 | 1,02; 1,02 |
| Tupungatito_2026-03-01_0536 | 5,9 | 10 | 0,2 | 8 | 1,04 | 1,00; 1,01 | 8 | 1,00; 1,25 | 1,00; 1,06 | 1,00; 1,16 | 1,00; 1,04 |
| Tupungatito_2026-03-01_0536 | 5,9 | 20 | 0 | 7 | 1,66 | 1,00; 1,00 | 7 | 1,00; 1,00 | 1,00; 1,00 | 1,00; 1,00 | 1,00; 1,00 |
| Tupungatito_2026-08-21_0548 | 6,0 | 2 | 2 | 8 | 0,21 | 1,00; 1,15 | 4 | 1,03; 1,07 | 1,06; 1,17 | 1,18; 1,54 | 1,06; 2,04 |
| Tupungatito_2026-08-21_0548 | 6,0 | 5 | 0,2 | 8 | 0,37 | 1,00; 1,00 | 8 | 1,03; 1,03 | 1,05; 1,06 | 1,17; 1,19 | 1,06; 1,07 |
| Tupungatito_2026-08-21_0548 | 6,0 | 10 | 0,2 | 8 | 0,80 | 1,00; 1,00 | 8 | 1,00; 1,03 | 1,00; 1,06 | 1,00; 1,18 | 1,00; 1,06 |
| Tupungatito_2026-08-21_0548 | 6,0 | 20 | 0 | 7 | 1,19 | 1,00; 1,00 | 7 | 1,00; 1,00 | 1,00; 1,00 | 1,00; 1,00 | 1,00; 1,00 |
| Villarrica_2026-09-19_0548 | 13,5 | 2 | 1,2 | 8 | 0,51 | 1,00; 1,18 | 3 | 1,02; 1,02 | 1,02; 1,03 | 1,08; 1,08 | 1,02; 1,25 |
| Villarrica_2026-09-19_0548 | 13,5 | 5 | 1 | 8 | 1,31 | 1,00; 1,00 | 8 | 1,00; 1,00 | 1,00; 1,00 | 1,00; 1,00 | 1,00; 1,00 |
| Villarrica_2026-09-19_0548 | 13,5 | 10 | 0,1 | 8 | 1,12 | 1,00; 1,00 | 8 | 1,00; 1,00 | 1,00; 1,00 | 1,00; 1,00 | 1,00; 1,00 |
| Villarrica_2026-09-19_0548 | 13,5 | 20 | 0 | 8 | 1,10 | 1,00; 1,00 | 8 | 1,00; 1,00 | 1,00; 1,00 | 1,00; 1,00 | 1,00; 1,00 |

### Tabla 2. Razón con/sin agrupada por zona de la caja (todas las escenas y distancias, foco a 1000 K)

| comparación | zona | n | r mediana | r percentil 90 | r máx |
|---|---|---|---|---|---|
| R real | 2 | 80 | 1,003 | 1,098 | 1,342 |
| R real | 1 | 89 | 1,000 | 1,000 | 1,009 |
| R real | 0 | 139 | 1,000 | 1,000 | 1,003 |
| T+ x1 | 2 | 42 | 1,097 | 1,274 | 1,362 |
| T+ x1 | 1 | 75 | 1,000 | 1,000 | 1,009 |
| T+ x1 | 0 | 124 | 1,000 | 1,000 | 1,127 |
| T+ x3 | 2 | 42 | 1,052 | 1,120 | 1,169 |
| T+ x3 | 1 | 75 | 1,000 | 1,000 | 1,024 |
| T+ x3 | 0 | 124 | 1,000 | 1,000 | 1,055 |
| T+ x10 | 2 | 42 | 1,104 | 1,186 | 1,545 |
| T+ x10 | 1 | 75 | 1,000 | 1,000 | 1,084 |
| T+ x10 | 0 | 124 | 1,000 | 1,000 | 1,183 |
| T+ x30 | 2 | 42 | 1,020 | 1,065 | 2,041 |
| T+ x30 | 1 | 75 | 1,000 | 1,000 | 1,248 |
| T+ x30 | 0 | 124 | 1,000 | 1,000 | 1,065 |
| T pre-registrado x1 | 2 | 22 | 1,129 | 1,211 | 1,450 |
| T pre-registrado x1 | 1 | 75 | 1,000 | 1,000 | 1,009 |
| T pre-registrado x1 | 0 | 124 | 1,000 | 1,000 | 1,172 |
| T pre-registrado x3 | 2 | 22 | 1,138 | 1,217 | 1,318 |
| T pre-registrado x3 | 1 | 75 | 1,000 | 1,000 | 1,030 |
| T pre-registrado x3 | 0 | 124 | 1,000 | 1,000 | 1,204 |
| T pre-registrado x10 (artefacto) | 2 | 22 | 12,902 | 34,568 | 37,969 |
| T pre-registrado x10 (artefacto) | 1 | 75 | 1,256 | 1,449 | 1,549 |
| T pre-registrado x10 (artefacto) | 0 | 124 | 1,263 | 11,319 | 26,023 |
| C4 ruido (control) | 2 | 80 | 1,860 | 2,469 | 6,474 |
| C4 ruido (control) | 1 | 89 | 1,091 | 2,771 | 3,288 |
| C4 ruido (control) | 0 | 139 | 1,158 | 2,060 | 3,115 |

### Tabla 3. Umbral de NTI de cada pase, sin foco (Chillán real y el trasplante a Láscar 2026-10-08)

| escena | brazo | celdas alertadas | sd NTI pase 1 | u sensible pase 1 | sd NTI pase 2 | u sensible pase 2 | u conservador pase 2 |
|---|---|---|---|---|---|---|---|
| NevadosDeChillan_2026-10-10_0554 | R-con | 5 | 0,00317 | 0,0158 | 0,00115 | 0,0057 | 0,0200 |
| NevadosDeChillan_2026-10-10_0554 | R-sin | 0 | 0,00090 | 0,0045 | 0,00090 | 0,0045 | 0,0200 |
| NevadosDeChillan_2026-10-10_0554 | N-con | 3 | 0,00617 | 0,0309 | 0,00542 | 0,0271 | 0,0542 |
| Lascar_2026-10-08_0542 | T-sin | 1 | 0,00089 | 0,0044 | 0,00088 | 0,0044 | 0,0200 |
| Lascar_2026-10-08_0542 | T-con-10 | 11 | 0,00483 | 0,0243 | 0,00275 | 0,0138 | 0,0275 |
| Lascar_2026-10-08_0542 | T+-con-1 | 4 | 0,00353 | 0,0176 | 0,00113 | 0,0057 | 0,0200 |
| Lascar_2026-10-08_0542 | T+-con-3 | 7 | 0,00223 | 0,0111 | 0,00093 | 0,0046 | 0,0200 |
| Lascar_2026-10-08_0542 | T+-con-10 | 7 | 0,00232 | 0,0116 | 0,00103 | 0,0051 | 0,0200 |
| Lascar_2026-10-08_0542 | T+-con-30 | 7 | 0,00320 | 0,0160 | 0,00091 | 0,0046 | 0,0200 |
| Tupungatito_2026-08-21_0548 | T-con-10 | 3 | 0,03322 | 0,1667 | 0,03322 | 0,1667 | 0,3328 |

### 5.1 Lectura por el criterio pre-registrado (§7, foco a 1000 K, 5 km o más)

- Escenas reales: mayor mediana de r 1,003, ninguna dirección pasa de alertar con 1 MW o menos a necesitar más:
  **nulo** (`resumen_salida.txt`, «Veredicto»).
- Trasplante T+ a 13, 40, 134 y 403 MW: mayor mediana de r 1,096, 1,054, 1,174 y 1,062, todas en Tupungatito (región
  sensible de 21 × 21 celdas, unos 7,9 km del centro a cada lado); ninguna dirección cruza 1 MW: **nulo** a escala 1,
  3 y 30, **menor** a escala 10 (`resumen_posthoc_salida.txt`, «Veredicto»).
- Trasplante T pre-registrado a escala 1 y 3: mayores medianas 1,127 y 1,194, también en Tupungatito: **menor**. Escala
  10: artefacto (§4.4).
- A 2 km (borde del cráter): razón mediana de 0,99 a 1,30 según escena y escala, máximo 2,04 en una dirección
  (Tabla 1). Pocos puntos válidos en el trasplante (2 a 4 de 8) porque la propia anomalía ocupa ese anillo.

### 5.2 Temperatura del foco

Con el foco a 600 K las medianas de la razón por zona difieren de las de 1000 K en 0,001 o menos
(`resumen_600k_salida.txt` contra la Tabla 2), y el VRP_eq mínimo cambia un 1 % (mediana 600 K / 1000 K = 1,012). Lo que cambia es el área:
el mismo umbral en MW pide de 11 a 12 veces más superficie caliente a 600 K (§5.3).

### 5.3 Lo que sí limita ver un foco nuevo en el flanco

| T_hot K | zona | n | VRP_eq mín mediana (MW) | rango (MW) | f mediana | área caliente mediana (m2) |
|---|---|---|---|---|---|---|
| 1000 | 2 | 80 | 0,34 | 0,12 a 0,82 | 9,50e-06 | 5 |
| 1000 | 1 | 89 | 1,42 | 0,75 a 2,72 | 3,98e-05 | 22 |
| 1000 | 0 | 139 | 1,37 | 0,57 a 3,04 | 3,83e-05 | 22 |
| 600 | 2 | 80 | 0,34 | 0,12 a 0,83 | 1,05e-04 | 59 |
| 600 | 1 | 89 | 1,44 | 0,76 a 2,75 | 4,43e-04 | 249 |
| 600 | 0 | 139 | 1,38 | 0,58 a 3,08 | 4,26e-04 | 240 |

(`area_umbral_salida.txt`; área = f × 0,5625 km², el área nadir del píxel que usa el coeficiente.) Un foco de lava de
unos 5 m² alerta si cae en la región sensible; fuera de ella hacen falta unos 22 m². Ese factor 4 es el mecanismo 3 del
plan (la ventana de búsqueda), y es mucho mayor que el mecanismo 2 medido aquí. Y la escena misma (nube, ruido) mueve el
umbral más que cualquier anomalía: el control C4, que sólo duplica la desviación estándar, sube la potencia necesaria
1,86 veces en la región sensible. Coincide con la firma de `experiments/_s196_plan_mejoras/salida_m0_enmascaramiento.txt`
en main: en las pasadas sin calor (todas las familias) el máximo del umbral sensible del segundo pase va de 0,0106 a
0,0198 según el volcán, y en 10 de 11 volcanes supera el máximo de las escenas de 10 a 100 MW (0,0119).

## 6. Controles

- **C1 identidad (pasa)**: sin foco, el arnés da las mismas celdas alertadas y el mismo VRP que `calcular_vrp_granulo`
  de producción llamado con el recorte, en 10 de 10 escenas (`control_c1_salida.txt`). Además la matriz de
  interpolación reproduce la grilla de producción con error máximo 1,8e-15 (`explorar_matriz_salida.txt`).
- **C2 linealidad (pasa)**: en 20 casos al azar, al VRP_eq mínimo y a 0,95 de él, insertar el foco en el gránulo y
  llamar a `remuestrear_grilla` da la misma máscara que la matriz en 40 de 40 (diferencia máxima en M13 de 5,6e-17;
  `control_c2_salida.txt`).
- **C3 el instrumento puede dar distinto de cero (pasa)**: en Llaima, sin calor, ningún punto alerta con 0 MW (0 de 32)
  y los 32 alertan con 200 MW o menos (mediana 1,41 MW) a 1000 K y a 600 K (`resumen_salida.txt`). En toda la medición:
  0 alertas con 0 MW, 0 puntos sin alerta a 200 MW, 0 barridos no monótonos, 0 píxeles sobre el techo de 634 K de M13.
- **C4 el instrumento puede ver enmascaramiento (pasa)**: con ruido blanco que duplica la desviación estándar de la
  escena, la razón mediana en la región sensible es 1,86 (criterio 1,3) y 1,32 en todas las zonas
  (`resumen_salida.txt`). El nulo de §5.1 no es ceguera del instrumento.

## 7. Limitaciones

- **Una sola anomalía fuerte real.** De los 10 recortes sólo Chillán pasa de 1,2 MW; las otras son de 0,15 a 1,2 MW.
  La fuerza del resultado sobre anomalías grandes viene del trasplante de esa única anomalía (5 celdas), escalada en
  intensidad con la misma forma. Una anomalía real de 100 MW o más suele ser más extensa (un flujo, un campo de lava), y
  esa forma no está probada; es justo el caso donde podría aparecer el colapso visto en el artefacto de §4.4.
- **Sólo VIIRS 750, sólo de noche.** De día el .m usa s = 15 y piso 0,02 en todas las zonas; no se midió.
- **Foco sintético de un píxel.** Un foco real puede repartirse entre dos píxeles (traslape de barrido fuera del nadir)
  o en varios; el píxel se eligió con peso de 0,3 o más sobre alguna celda, lo que deja fuera los píxeles que la
  interpolación casi no ve.
- **Pocas escenas, ángulos bajos.** Cenit de 0,4 a 23,8 grados, ninguna pasada de borde de franja, donde el píxel crece
  y la escena es más ruidosa. Con 10 escenas no se puede estratificar por cenit; se reporta por escena (Tabla 1).
- **Lectura del L1B de S158.** Los recortes se leyeron con el corte de banderas viejo (DN de 65528 o más); producción
  hoy usa el valid_max de cada variable. Sólo cambia algo en píxeles M13 sobre unos 512 K; el píxel más caliente de los 10
  recortes tiene 308,3 K (`bt_max_recortes_salida.txt`) y ningún píxel quedó sin dato (`explorar_pesos_salida.txt`),
  así que no afecta.
- **Distancia desde el pico, no desde el borde.** A 2 km muchos puntos caen sobre la propia anomalía y se descartan.

## 8. Qué haría falta para MODIS y VIIRS 375

El arnés sirve tal cual: `detectar_mirova` recibe las longitudes de onda y la caja, y `FAMILIAS` trae paso, bandas,
coeficiente y caja de cada sensor. Faltan los insumos y tres ajustes:

1. **Recortes con ángulos.** Un probe en Actions (el token de NASA sólo existe ahí) que, como `probe_granulos.py` de
   S158, guarde lat, lon, las dos bandas y los cuatro ángulos de cada pasada, para MODIS (MxD021KM más MxD03, bandas 22
   o 21 y 31) y VIIRS 375 (I04 e I05). Conviene elegir de una vez las 167 escenas de Chillán de 10 a 100 MW y las de
   Cordón Caulle que nombra el plan, más escenas de ángulo alto y nubladas.
2. **Caja y distancias.** En MODIS la región sensible es 5 × 5 celdas de 1 km al centro de la grilla (en Cordón Caulle
   el cráter queda afuera, D36 punto 7) y la grilla tiene 51 celdas; en VIIRS 375, la C13 en el cráter (`caja_v375`) con
   celdas de 375 m. El halo del .m y la huella se cuentan en celdas, así que 2 km son 2, 2,7 o 5,3 celdas según el
   sensor.
3. **Foco y coeficiente.** El área del píxel cambia (1 km² en MODIS, 0,14 km² en VIIRS 375) y el VRP_eq se convierte
   con `COEF_VRP_MODIS` o `COEF_VRP_V375`. En MODIS hay que decidir cuál de las bandas 21 y 22 recibe el foco (la vía usa
   la 22 y cae a la 21 cuando satura, D21).

## 9. Archivos

Todo en `D:\vrp-trabajo\temporales\s200\p0_3\`:
- `PREREGISTRO.md`, `PREREGISTRO.sha256`, `ADENDA_POSTHOC.md`, `ADENDA_POSTHOC.sha256`
- `comun.py` (armado de la escena y matriz de interpolación), `medir.py` y `medir_posthoc.py` (medición),
  `resultados.jsonl`, `resultados_posthoc.jsonl`, `umbrales.json`, `umbrales_posthoc.json`
- `resumen.py`, `resumen_posthoc.py`, `resumen_600k.py`, `area_umbral.py`, `vrp_trasplantes.py`, `diag_parche.py`,
  `tabla_informe.py`, `bt_max_recortes.py`, `armar_informe.py`, cada uno con su `*_salida.txt` o `tabla_informe.md`
- `control_c1_identidad.py`, `control_c2_linealidad.py` y sus salidas
- `explorar*.py` y sus salidas (exploración previa al pre-registro), `prueba_rapida.py` (prueba de humo)
- `main_snapshot\` (copia de `pipeline/` y `volcanoes.yaml` de origin/main `b7626b03c`, sólo lectura)
