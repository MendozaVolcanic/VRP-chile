# Verificación independiente de F5b re-corrido (S177): la lámina PNG de MIROVA como vara de posición en Chillán

Verificador con contexto limpio. Modelo: Claude Opus 5.5; esfuerzo real: SIN DATO. Fecha: 2026-11-09.
Objeto: `C:\Users\nmend\vrp-temporales\s177_f5b\INFORME.md` y sus scripts. Sólo lectura sobre eso y sobre F5b y V5B; sin NASA, credenciales ni commits. Todo lo mío está en `C:\Users\nmend\vrp-temporales\s177_ver_f5b\`. C: terminó con 13,8 GB libres.

## 1. Veredicto: SE SOSTIENE EN PARTE

El cálculo está bien hecho y las cifras se reproducen con código independiente. Lo que falla es lo que se concluye de dos pruebas y una etiqueta.

- Se sostiene: la máscara corregida conserva la mancha en Chillán; nuestro punto cae dentro o al lado de la mancha saturada; casi toda la separación del nulo ingenuo es geometría de visada; MODIS sigue SIN DATO; nunca «el píxel».
- No se sostiene como está escrito: (a) que contra el nulo de geometría igualada «no hay evidencia» (esa prueba no tiene poder: una identidad perfecta daría casi lo mismo); (b) que el hallazgo 351 «no se sostiene», CONFIRMADO (depende de usar centroide; las celdas que reproducen la tabla de MIROVA quedan a 1,0 a 2,5 km de nuestro punto); (c) que la lámina «descarta» un foco desplazado y «habría detectado» 1 km (la prueba de sensibilidad da la misma curva con una lámina muerta).

## 2. Defectos

| ID | Gravedad | Etiqueta | Defecto |
|---|---|---|---|
| V177-01 | 3 | CONFIRMADO | El nulo N3 no puede distinguir identidad de ausencia de identidad: con identidad perfecta el margen de la clase sería casi el mismo |
| V177-02 | 3 | CONFIRMADO el cálculo; SOSPECHA la lectura física | «El hallazgo 351 no se sostiene» depende del centroide, de la unión de componentes y del control blando |
| V177-03 | 2 | CONFIRMADO | «Descartar foco desplazado, CONFIRMADO» dice más que los datos y contradice la sección 7.3 del propio INFORME |
| V177-04 | 2 | CONFIRMADO | La prueba de sensibilidad no prueba el instrumento: una lámina muerta da la misma curva en V750 |
| V177-05 | 2 | CONFIRMADO lo estadístico; SOSPECHA la causa | «Es la única señal que sobrevive» es falso: hay señal de la pasada en la posición del punto, más allá de la geometría |
| V177-06 | 1 | CONFIRMADO | Los controles 268 de 268 y 35 de 35 no podían fallar |
| V177-07 | 1 | CONFIRMADO | IC con pasadas tratadas como independientes y el nulo fijo; algo optimistas, sin cambiar la lectura |
| V177-08 | 1 | CONFIRMADO | Sección 8: «1 de 69 V375 con más de una componente» son 0 de 69 |
| V177-09 | 1 | CONFIRMADO | La dilatación une huecos de hasta 2 px, no de 1 px como dice el docstring |

## 3. Pregunta 1: el nulo

### Lo que está bien (CONFIRMADO)

- Mismo código para observado y nulo: `lib177.clase` en los dos brazos (`s03_clases_y_nulo.py` l. 88 a 90 y 168 a 172; `s04_robustez.py` l. 63 a 64 y 126 a 127). El control se aplica a la mancha y a la distancia de la pasada i, y no depende del punto j, así que no hay fuga por el filtro.
- Sin auto-pareo ni duplicados: `j != i` en N1 y N3; 0 duplicados de (volcán, sensor, hora) y de (lámina, panel) (`v00_explora.py`, ejecutado en sesión).
- Reproducción exacta con selector y matriz míos: N1 V375 0,983 / 0,615, AUC 0,818; N3 0,981 / 0,929, AUC 0,641; N1 V750 1,000 / 0,861, AUC 0,714; N3 1,000 / 0,989, AUC 0,609 (`v02_nulo.out.txt`, bloque A; compara con `s04_robustez.out.txt` l. 16 a 21).
- No es deriva temporal: el nulo a 1 día (0,581) no es mayor que a todas las pasadas (0,615) en V375 (`s03_clases_y_nulo.out.txt` l. 59 a 61). Los vecinos N3 casi no son de la misma noche: 7 % a menos de 36 h, mediana 312 h en V375; 5 % y 384 h en V750 (`v02_nulo.out.txt`, bloque F).
- La geometría explica de verdad el grueso: la distancia a otras pasadas baja de 0,76 a 0,38 km en V375 al igualar visada, y un modelo de geometría con satélite explica 93 % de la varianza este de nuestro punto en V375 (`v07_perm_estrecha.out.txt`). «Casi toda la separación del nulo ingenuo es geometría» se sostiene.
- El nulo de V5B reproducido: exacto con j entre pasadas con control ok da 0,721 y 0,766, contra 0,730 y 0,769 sorteados; la explicación por sorteo es aceptable (`v08_varios.out.txt`, punto 1).

### V177-01 (gravedad 3): N3 no tiene poder para lo que se le pide

Por qué: si el foco está fijo en el cráter, dos pasadas con igual visada ponen el píxel casi en el mismo lugar. El punto de otra pasada casi coincide con el propio aunque la lámina y nosotros veamos exactamente lo mismo. Entonces la clase binaria con tolerancia de 2 celdas está saturada antes de medir.

Lo medí poniendo como mancha la celda de la lámina que contiene nuestro punto, es decir la identidad perfecta con la cuantización de la lámina, con el mismo N3 (`v02_nulo.out.txt`, bloque C):

| | Observado | Identidad perfecta | Identidad + ruido 0,5 celda | Identidad + ruido 1 celda |
|---|---|---|---|---|
| V375 margen de clase (obs menos nulo) | +0,052 | +0,085 | +0,115 | +0,129 |
| V375 AUC N3 | 0,641 | 0,785 | 0,749 | 0,663 |
| V750 margen de clase | +0,011 | +0,006 | +0,056 | +0,079 |
| V750 AUC N3 | 0,609 | 0,856 | 0,715 | 0,628 |

Lectura. El margen observado en V375 y en V750 no se puede distinguir del que daría una identidad perfecta (en V750, el perfecto es menor que el observado). El AUC observado queda donde cae una identidad con un ruido cercano a 1 celda, que es justamente la precisión validada de la lámina (V5B-03; `f5b_lib.py` l. 5 a 7). Por eso «el margen casi desaparece» no es un hallazgo sobre la lámina: es lo que tenía que pasar. Ojo: tampoco prueba identidad; un AUC de 0,64 es compatible con varias cosas. El nulo no puede decidir, y eso es lo que el INFORME debe decir.

Además, el pre-registro de s04 (l. 16 a 18) dice «si el AUC se queda en ~0,5 con N3, lo que separa es la geometría». En V375 no se queda: 0,641 con IC [0,553; 0,727], y sigue fuera de 0,5 con mi bootstrap más duro [0,511; 0,777] (`v02_nulo.out.txt`, bloque B). El INFORME lo reporta, pero concluye por el margen binario.

### V177-05 (gravedad 2): hay señal más allá de la geometría

El INFORME dice que los cúmulos son «la única señal que sobrevive al nulo con geometría igualada» (l. 77) y que «no hay evidencia independiente» (l. 10). Con una prueba sin techo: permutación de nuestros puntos sólo entre pasadas de geometría compatible (cadena de intercambios, uniforme sobre permutaciones válidas), estadístico la distancia media (`v07_perm_estrecha.out.txt`):

| Ventana (zenit, azimut) | V375 km (propia contra permutación) | p | V750 km | p |
|---|---|---|---|---|
| 5°, 30° | 0,288 / 0,352 | 0,0003 | 0,505 / 0,583 | 0,0037 |
| 3°, 15° | 0,288 / 0,349 | 0,0003 | 0,505 / 0,585 | 0,0023 |
| 1,5°, 8° | 0,288 / 0,338 | 0,0003 | 0,505 / 0,561 | 0,0147 |
| 5°, 30° y mismo satélite | 0,288 / 0,305 | 0,0803 | 0,505 / 0,544 | 0,0317 |
| 3°, 15° y mismo satélite | 0,288 / 0,298 | 0,1916 | 0,505 / 0,543 | 0,0333 |

Control: 60 brazos barajados dentro de N3 dan p menor que 0,05 en 1 (V375) y 2 (V750) casos, mediana 0,56 y 0,53; el test no tiene sesgo a favor (`v07_perm_estrecha.out.txt`). Excluir vecinos a menos de 36 h no cambia (`v02_nulo.out.txt`, bloque D).

Residuos de un modelo de geometría con satélite: V375 este r = +0,33 (p 0,0026), norte +0,23 (p 0,030); V750 norte +0,56 (p 0,0001), este -0,02 (p 0,57) (`v07_perm_estrecha.out.txt`).

CONFIRMADO que hay información de la pasada en la posición, pequeña (0,05 a 0,08 km). SOSPECHA de su causa: con el mismo satélite en V375 la ventaja cae y deja de ser significativa, así que parte puede ser un desfase propio de cada satélite (el mismo L1B para los dos) y no el píxel de esa pasada. El resto de la señal de cúmulo (`s05`) tampoco se explica por tamaño: igualando el número de píxeles, cov_M sigue en +0,13 V375 y +0,19 V750 (`v08_varios.out.txt`, punto 3).

### V177-07 (gravedad 1): unidad de remuestreo

El bootstrap de s04 remuestrea pasadas i, deja fijo el nulo de cada i (l. 138 y 139) y trata como independientes pasadas de la misma noche. Por día y remuestreando también los j, el AUC N3 V375 pasa de [0,553; 0,728] a [0,511; 0,777], y V750 de [0,495; 0,723] a [0,454; 0,760] (`v02_nulo.out.txt`, bloque B). Cambia el ancho, no la lectura.

## 4. Pregunta 2: sensibilidad (V177-04, gravedad 2)

`s04_robustez.py` l. 91 a 97 suma un vector a NUESTRO punto y recalcula una distancia contra la mancha y el control intactos. Es aritmética de la tolerancia, no pasa por el instrumento. Comprobado con la pregunta 2 de la guía de auditorías: reemplacé el centroide de cada pasada por la mediana de los centroides, es decir una lámina que no aporta nada de la pasada (`v05_sensibilidad.out.txt`, fila B):

| Fracción clase i, k km | 0 | 0,5 | 1 | 1,5 | 2 |
|---|---|---|---|---|---|
| V375, s04 B | 0,98 | 0,81 | 0,10 | 0,00 | 0,00 |
| V375, lámina muerta | 0,79 | 0,56 | 0,19 | 0,03 | 0,01 |
| V750, s04 B | 1,00 | 0,99 | 0,86 | 0,43 | 0,08 |
| V750, lámina muerta | 0,94 | 0,95 | 0,84 | 0,43 | 0,08 |

En V750 no se distinguen. Lo que la prueba mide es que la tolerancia es 0,75 y 1,5 km.

Hice la prueba que faltaba: traslado en la imagen los píxeles de la mancha k km en 8 direcciones, relleno el hueco y corro el selector completo. Da casi lo mismo (V375 sin control: 0,92 a 0,5 km, 0,12 a 1 km; V750: 0,81 a 1 km, 0,42 a 1,5 km, 0,13 a 2 km; `v05_sensibilidad.out.txt`, fila C). CONFIRMADO, entonces: si la mancha ENTERA se corriera 1 km en V375 o 2 km en V750, la clase saldría fuera. Pero eso es lo único que prueba. No simula un foco movido DENTRO de la mancha, que el centroide no ve por construcción. Y en pasadas reales la mancha tiene celdas a más de 1 km de nuestro punto en 28 de 55 V750 y 6 de 69 V375; a más de la tolerancia en 6 de 55 y 12 de 69 (`v03_mascara.out.txt`, bloque F).

## 5. Pregunta 3: la máscara y el hallazgo 351

### La máscara conserva la mancha (CONFIRMADO en Chillán)

- Mi selector da las mismas manchas C1 y C2 en 301 de 303 (lat, lon, área, componentes). Las 2 diferencias son Láscar, misma luminancia, una celda de longitud (`v01_clases.out.txt`, `v08_varios.out.txt` punto 5). Ningún caso de Chillán.
- A ojo, `C:\Users\nmend\vrp-temporales\s177_ver_f5b\crops\mosaico.png`: en Chillán V750 2026-10-10 06:54 y 2026-10-27 05:36, MODIS 2026-10-16 01:40 y V375 2026-10-18 05:06 la mancha blanca es un foco claro sobre la cumbre oscura, con nuestro punto (cian) dentro o al lado; el cuadrado naranjo de F5b queda en el borde o fuera. El control sin mancha (V375 2026-10-01 06:00, luminancia máxima 157) no cambia.
- Las 19 VIIRS borradas de Chillán quedan a 0,49 km o menos de nuestro punto en su celda más cercana (`v08_varios.out.txt`, punto 4). Un hueco de sin dato caería al azar en el inner.
- Falsa retención contra el NaN del TIF, control que el INFORME no hizo: en 52 pares TIF y lámina de V5B, 0 componentes blancas pequeñas son NaN (0 de 11 de 20 a 399 px, 0 de 53 de menos de 20) (`v06_huecos_tif.out.txt`). Límite: ninguno es de Chillán ni fuerte, y 10 de las 14 componentes que tocan borde o son enormes no son NaN en el TIF, de modo que «toca el borde = sin dato» es un descarte seguro, no una identificación.
- En Caulle la componente conservada es una zona clara extensa y no un foco (mosaico, panel derecho; halo +69 sobre la mediana del panel, `v03_mascara.out.txt`). El INFORME ya deja Caulle fuera; su etiqueta «calor» para esos 4 de los 35 no aplica. SOSPECHA.

### V177-06 (gravedad 1)

En las 268 láminas sin componente borrada, las máscaras A y B difieren en 0 píxeles dentro del inner en las 268 (`v03_mascara.out.txt`, bloque C). El control «C1 igual a A» no podía fallar. Con 35 de 35 pasa lo mismo: una componente blanca en el inner es siempre el máximo. Son recuentos, no controles.

### V177-02 (gravedad 3): las 4 protegidas

Qué mueve cada una (`v03_mascara.out.txt`, bloque D/E; clase con control por centroide, control «alguna celda», sin control):

| Pasada | Tabla km | A | C1 | C2 | d nuestro a centroide | d nuestro a celdas de la mancha | Celdas que reproducen la tabla a ±1 celda: d a nuestro punto |
|---|---|---|---|---|---|---|---|
| V375 NOAA21 10-18 05:06 | 1,35 | iii iii iii | iii iii iii | iv i i | 0,19 | 0,19 a 1,02 | 1 celda: 1,02 |
| V750 NOAA20 10-10 06:54 | 2,37 | iii iii iii | iv i i | iv i i | 0,78 | 0,14 a 2,45 | 3 celdas: 1,77 a 2,45 |
| V750 NOAA20 10-16 06:42 | 2,12 | iii iii iii | i i i | i i i | 0,48 | 0,29 a 1,48 | 2 celdas: 1,23 a 1,48 |
| V750 NOAA21 10-29 06:42 | 2,37 | iii iii iii | iv i i | iv i i | 0,65 | 0,11 a 2,16 | 1 celda: 2,16 |

1. Sólo la máscara corrige 1 de 4 hasta (i). La V375 no cambia con la máscara: la mueve la unión de componentes con «mayor área». Dos V750 quedan en (iv) con el control por centroide.
2. Con control estricto (centroide), C2 deja 1 en (i) y 3 en (iv). El paso a (i) de las otras 3 necesita el control blando «alguna celda».
3. Incoherencia interna: en V375 10-18 el control pasa únicamente por una celda que está a 1,02 km de nuestro punto, y la clase se calcula con otro punto, el centroide, a 0,19 km. La misma mancha valida con su extremo y clasifica con su centro.
4. Si la `Distancia_km` de MIROVA se mide desde su centro, el píxel que MIROVA reporta está en el extremo de la mancha: a 1,0 a 2,45 km de nuestro punto en las 4, el mismo rango que afirmaba 351. A ±1 celda, 3 de 4 quedarían fuera de tolerancia. Es un dato de la tabla que el centroide ignora. En todo Chillán la tabla da 0,55 km (V375) y 1,05 km (V750) más que el centroide de la mancha en mediana, y en V375 42 de 69 pasadas no tienen ninguna celda de la mancha a ±1 celda de la tabla (`v03_mascara.out.txt`, bloque F).

Qué queda probado: el píxel que eligió F5b no era el centro de la mancha, y nuestro punto cae dentro o junto a la mancha. CONFIRMADO. Qué no: que MIROVA ponga su foco donde nosotros. Si la tabla da un extremo, si el origen de la tabla es otro (V5B-03) o si la mancha entera es «el foco», SIN DATO. La frase «El hallazgo 351 no se sostiene. CONFIRMADO» debe cambiar: refutada la lectura de 351 por píxel de F5b; abierta la de la tabla.

## 6. Pregunta 4: cifras recalculadas

Con código propio (selector, grilla y clases escritos aparte; sólo reutilizo la geometría guardada en `p8_clases.json` y los TIF). Salida: `C:\Users\nmend\vrp-temporales\s177_ver_f5b\v01_clases.out.txt`. Las 8 filas por 5 variantes de la tabla de la sección 4 del INFORME coinciden todas: Todos 172/15/118, 173/10/122, 194/21/90, 172/9/124, 207/96/2; Chillán V375 46/1/22, 46/1/22, 57/1/11, 46/0/23, 68/1/0; Chillán V750 44/3/8, 43/0/12, 54/0/1, 43/0/12, 55/0/0; MODIS 15/6/2, 18/4/1, 18/4/1, 18/4/1, 18/4/1; protegidas y resto también. CONFIRMADO. Láminas distintas: 291 (`v08_varios.out.txt`, punto 5). Porcentajes contra el nulo: sección 3 de este informe, bloque A.

V177-08 (gravedad 1): la sección 8 dice «sólo 1 de 69 VIIRS 375 y 1 de 22 MODIS tienen más de una componente». Con C2 son 0 de 69 y 1 de 22 (`v08_varios.out.txt` punto 2; `s02_manchas.out.txt` l. 31); el 1 de 69 es «C2 distinto de C1» y es la pasada 10-18 05:06.

V177-09 (gravedad 1): `lib177.py` l. 15 dice «separados por un hueco de 1 px»; la dilatación une huecos de 1 y 2 px (`v09_dilatacion.out.txt`). En V375, 2 px son casi 2 celdas. Sólo afecta a esa pasada en Chillán.

## 7. Pregunta 5: lo que el INFORME dice de más (V177-03, gravedad 2)

- Sección 1, punto 1: «Descartar que el foco de MIROVA esté desplazado. CONFIRMADO». Lo confirmado es «nuestro punto está cerca del centroide de la mancha saturada». El propio INFORME dice en 7.3 que el selector con anomalías fuertes es SIN DATO (no hay control positivo contra TIF con mancha saturada) y en 7.6 que el origen de la distancia no se sabe. Las dos cosas no caben con CONFIRMADO. Etiqueta justa: SIN DATO para «el foco de MIROVA»; CONFIRMADO para «la mancha».
- La clase i en V750 la cumple también un punto fijo en el cráter: 0,94 con lámina muerta (`v05_sensibilidad.out.txt`). «No hay desplazamiento» en V750 no aporta sobre el cráter.
- Sección 1, punto 2: «lo que queda es poco» y «no hay evidencia independiente»: ver V177-01 y V177-05. La frase honesta: «la prueba de clase no tiene poder; una prueba sin techo muestra una señal pequeña de la pasada, y el foco fijo impide separar la noche del cráter».
- Se sostiene sin cambio: MODIS SIN DATO; otros volcanes SIN DATO; nunca «el píxel»; límites de la sección 7.

## 8. Qué debería cambiar en la conclusión

Propuesta de redacción para informes al observatorio: «En Chillán la lámina NTI de MIROVA muestra una mancha saturada de varias celdas en la que nuestro punto cae dentro o a su lado (centroide a 0,75 km o menos en 68 de 69 pasadas VIIRS 375 y a 1,5 km o menos en 55 de 55 VIIRS 750). La lámina tiene precisión de una celda, no resuelve qué píxel de la mancha es el foco, y la distancia de la tabla de MIROVA no calza con el centroide. No se puede publicar como medición de la posición del foco de MIROVA; sí como concordancia con la mancha.» No hay validación contra TIF con anomalía saturada (SIN DATO); bajar un par TIF y lámina fuerte de Chillán anterior al 22-sep es lo que más movería esto.

## 9. Lo que no verifiqué

SIN DATO: origen físico de `Distancia_km` de MIROVA; pares TIF y lámina fuertes en Chillán; si el residuo es píxel de la pasada o desfase por satélite; cronología real del «pre-registro» de los scripts (fechas de archivo no lo prueban). No re-hice la georreferencia de la lámina (V5B la validó), no re-abrí la OCR de paneles ni revisé `s01`.

## 10. Reproducción

Desde `C:\Users\nmend\vrp-temporales\s177_ver_f5b\`, en orden: `v01_clases.py` (genera `v01_manchas.pkl`), `v02_nulo.py`, `v03_mascara.py`, `v04_crops.py`, `v05_sensibilidad.py`, `v06_huecos_tif.py`, `v07_perm_estrecha.py`, `v08_varios.py`, `v09_dilatacion.py`; salidas `.out.txt` al lado. Código común en `comun.py`.
