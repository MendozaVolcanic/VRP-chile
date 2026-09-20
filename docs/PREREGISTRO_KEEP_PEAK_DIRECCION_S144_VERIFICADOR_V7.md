# Séptimo verificador, contexto limpio, del pre-registro `keep_peak` con dirección (S144, v7)

**Veredicto: el instrumento y la compuerta nueva quedaron bien, y el estadístico pareado arregla de
verdad lo que rompió la v6. Lo que la v7 no vio es que su propia pregunta ya está contestada fuera de
la muestra del veredicto, y que la respuesta cae justo en el hueco de su regla.** Corrí el estadístico
literal de la v7 (`Δ_p = e_p − x_p`, pasada cruzada de 45 a 120 min, punto sorteado en la misma imagen)
sobre las 681 pasadas del estrato hermano, que están fuera del veredicto: da **`Δ = +0,0514`, intervalo
[+0,0264, +0,0766]**. Re-ponderado a la mezcla de volcanes de la muestra del veredicto da **+0,0511**, y
restringido a los 6 volcanes elegibles **+0,0354**. Con la estructura real de noches (601 pasadas, 349
noches), un efecto de ese tamaño entrega **INCONCLUSO el 90 % de las veces**: no alcanza para el
positivo y no cabe en la banda de equivalencia. El pre-registro declara su contaminación en §1 pero
**no declara este número**, que es el único disponible y el más predictivo de todos.

Lo bueno, y es mucho: **el nulo `N1` sí es cero**, en sus dos lecturas posibles (`-0,0029` [-0,0121 a
+0,0161] con la separación de 1,5 km, `+0,0044` [-0,0161, +0,0229] sin ella), o sea la compuerta que la
v6 se ponía en rojo sola ahora pasa con holgura. **No hay atrición asimétrica** (0 de 681 pasadas se
pierde por falta de `ΔL0`, en ninguno de los 8 puntos que evalué). **No hay efecto de borde**: el
ráster es de 134 por 134 celdas de 0,374 a 0,385 km, el borde más cercano al cráter queda a 18,4 km, y
la fracción sin dato es plana entre 0 y 4 km de radio.

Y el eje 1, medido, **estima un rasgo permanente**: con un ráster de otra noche a más de 3 días da
`+0,0441` sobre las mismas 681 pasadas, o sea el 86 % del efecto está ahí cualquier noche. La parte de
esta noche vale `+0,0073` [-0,0241, +0,0385]. La fila 2 de la tabla de §8 es la que el dato ya señala.

Documento verificado:
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\docs\PREREGISTRO_KEEP_PEAK_DIRECCION_S144.md`
(v7 del 2026-09-19, rama `s144-prereg-keep-peak-direccion`, commit `1b0c37a5d`).

Mis scripts están fuera del repo, en
`C:\Users\nmend\AppData\Local\Temp\claude\C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile\3a2a7912-9e56-4be4-b449-f2c2c5bbe439\scratchpad\v7\`:
`b7.py` (el instrumento con la regla literal de la v7 y los seis puntos de comparación), `r1.py`
(pasada cruzada), `r2.py` (otra noche), `r3.py` (imagen propia, control B), `a1.py`, `a2.py`, `a3.py`
(análisis e intervalos), `eje2.py` (el eje 2 literal), `sim7.py` (potencia y alcance de las tres
salidas), `tr7.py` (tramos y anchos), `geo7.py` (geometría del ráster y sin dato por radio), `rad7.py`
(gradiente radial del instrumento), `cel7.py` (variante de celda exacta), `clim7.py` (climatología
espacial del exceso). Reusan `common3.py` de la ronda 3, `base4.py` de la ronda 4, `zc5.pkl` de la
ronda 5 y `e6.pkl` de la ronda 6. **No modifiqué ningún archivo del repo salvo este informe.**

## Aviso de contaminación (léelo antes de tocar la v7)

1. Corrí el procedimiento completo de §5 con la regla literal de la v7 sobre las **1.289 pasadas con
   patrón, publicadas, fuera de Lastarria, con etiqueta `far_ref` o `sin_info`** (el estrato hermano,
   fuera de la muestra del veredicto). 681 tienen imagen cruzada usable. De ahí salen H1, H5, H8 y H9.
2. Corrí el mismo procedimiento sobre ese estrato con el ráster de **otra noche** (1.289 pasadas) y con
   la **imagen propia** (194 pasadas).
3. Evalué `Z` en posiciones `P` que pertenecen a pasadas de la muestra del veredicto sólo en cuanto son
   el mismo punto repetido en otras noches; **nunca en el ráster que le corresponde a una pasada del
   veredicto**, así que ningún `e_p` del veredicto quedó calculado.
4. Usé el embudo de la muestra del veredicto que contó la ronda 6 (`e6.pkl`: 601 pasadas, 349 noches)
   para la estructura de noches de la simulación. **No evalué `Z` en el `P` de ninguna de esas pasadas
   y no clasifiqué ninguna pasada de M1.**
5. Los nulos, los embudos, la potencia y las propiedades del instrumento se midieron sobre estratos
   ajenos, tal como pide el encargo.

---

## Hallazgos nuevos (ordenados por gravedad)

### H1. El estadístico de la v7 ya está medido fuera de la muestra, vale +0,0514, y ese valor cae exactamente en el hueco entre las dos salidas: la regla entrega INCONCLUSO el 90 % de las veces

- **Dónde**: v7 l. 133-134 (`Δ_p = e_p − x_p`), l. 203-212 (las dos condiciones del veredicto), l. 38-50
  (§1, la contaminación declarada, que no incluye este número).
- **Evidencia** (`python r1.py && python a1.py && python sim7.py`), todo sobre el estrato hermano:

  | qué | n | `Δ` | IC 95 % | tasa P | tasa X |
  |---|---|---|---|---|---|
  | **eje 1 literal de la v7** (P contra punto sorteado, mismo ráster cruzado) | 681 | **+0,0514** | [+0,0264, +0,0766] | 0,0837 | 0,0323 |
  | re-ponderado a la mezcla de volcanes del veredicto | 681 | **+0,0511** | | | |
  | sólo los 6 volcanes elegibles del veredicto | 401 | **+0,0354** | | | |

  Y la regla de §7 aplicada con la estructura real de noches de la muestra del veredicto (349 noches,
  601 pasadas, 6 volcanes elegibles), con los bloques de nulo reales (pares sorteados `A − B`):

  | efecto inyectado | `Δ` medido | ancho del IC | "cae sobre un exceso" | "no se distingue" | INCONCLUSO |
  |---|---|---|---|---|---|
  | 0 | -0,0041 | 0,047 | 0 % | **97 %** | 3 % |
  | 0,020 | +0,0175 | 0,053 | 0 % | 67 % | 33 % |
  | 0,035 | +0,0314 | 0,055 | 0 % | 25 % | **75 %** |
  | **0,050** | **+0,0460** | 0,060 | 1 % | 7 % | **91 %** |
  | 0,064 | +0,0586 | 0,061 | 8 % | 2 % | 90 % |
  | 0,083 | +0,0750 | 0,064 | 35 % | 0 % | 65 % |
  | 0,100 | +0,0916 | 0,067 | 63 % | 0 % | 37 % |
  | 0,131 | +0,1215 | 0,071 | 97 % | 0 % | 3 % |

- **Qué pasa (el fenómeno y el mecanismo)**: el estrato hermano son pasadas donde el pipeline publicó
  exactamente el mismo objeto, con el mismo patrón, y lo único distinto es qué fila escribió MIROVA esa
  noche. La propia v6 y la ronda 6 discutieron largo que el fenómeno, si existe, tiene que estar en los
  dos estratos por igual: un rasgo permanente del campo no sabe qué publicó MIROVA. Entonces `+0,051`
  es la mejor predicción disponible de lo que va a dar el veredicto. Y la regla de §7 pide que el
  intervalo entero quede sobre +0,05 para el positivo, o entero dentro de ±0,05 para la equivalencia,
  con un ancho real de 0,047 a 0,060: la zona muerta va de un `Δ` de +0,023 a uno de +0,10. **El valor
  medido está en el medio de esa zona.**
- **Cómo se ve en el resultado**: tres meses de corrida para llegar a un INCONCLUSO que la tabla de §8
  manda a "informar y no mover nada", y que después se va a leer como si la medición hubiera fallado,
  cuando la medición hizo exactamente lo que este cálculo anticipa.
- **Cómo reproducirlo**: `python r1.py && python a1.py && python sim7.py`.
- **CONFIRMADO. Gravedad 4.**
- **Lo que hay que hacer, y hay que elegir por escrito antes de medir**: (a) declarar en §1 el valor
  fuera de muestra con su intervalo, que es lo mínimo; (b) achicar la zona muerta, por ejemplo bajando
  el umbral del positivo al nivel que la potencia sí alcanza, o subiendo la tolerancia de equivalencia,
  con el costo escrito; (c) cambiar a un estadístico con más información por pasada, sabiendo lo que
  dice H7 sobre el sesgo de radio de la versión continua; o (d) asumir el INCONCLUSO probable y decir
  de antemano qué se hace con él, que es lo que la fila 4 de §8 ya insinúa pero sin advertir que es la
  salida más probable.

### H2. El mapa de potencia de §7 no es el de este estadístico, y además mezcla dos rondas: el 87 % que cita es el número de la v5, que la ronda 6 ya había reemplazado por 56 %

- **Dónde**: v7 l. 214-219 ("Mapa de potencia declarado (medido por la ronda 6 con la estructura real
  de noches) ... +0,064 da el positivo el 13 % de las veces, +0,083 el 87 % y +0,131 el 100 %"), contra
  el informe de la ronda 6, H8, que dice textualmente "`+0,064` lo da 13 %, `+0,083` lo da **56 %** (la
  v5 daba 87 %)".
- **Evidencia** (`python sim7.py`, misma tabla de arriba, y `python tr7.py`):

  | `Δ` | v7 §7 declara | ronda 6 midió (estadístico de la v6) | yo mido (estadístico de la v7) |
  |---|---|---|---|
  | +0,064 | 13 % | 13 % | **8 %** |
  | +0,083 | **87 %** | **56 %** | **35 %** |
  | +0,131 | 100 % | 100 % | **97 %** |
  | ancho del IC bajo el nulo | (no lo dice) | 0,041 | **0,047** |
  | ancho del IC, tramo posterior a #535 | **0,083** (l. 218) | 0,083 | **0,0975** |

- **Qué pasa**: el estadístico cambió de `e_p` menos la fracción de **5** sitios de referencia a `e_p`
  menos **un** indicador binario. El promedio de cinco binarios tiene un quinto de la varianza de uno
  solo, así que el término de comparación pasó de casi constante a tan ruidoso como el observado. La
  varianza por pasada sube de unos 0,057 a unos 0,095 y el intervalo se ensancha alrededor de un 15 %
  en la muestra completa y un 17 % en el tramo posterior a #535. Importar la potencia del estadístico
  anterior subestima la probabilidad de INCONCLUSO justo donde el efecto real parece estar.
- **Cómo se ve en el resultado**: alguien lee "+0,083 sale el 87 % de las veces", la corrida da +0,075
  con un INCONCLUSO, y concluye que pasó algo raro. No pasó nada raro: a ese nivel el positivo sale un
  tercio de las veces.
- **Cómo reproducirlo**: `python sim7.py` y `python tr7.py`.
- **CONFIRMADO. Gravedad 4.**

### H3. El +0,0005 del eje 2 es de otro estadístico: la ronda 5 midió `e_P` menos los 5 sitios de referencia en un ráster de otra noche, no `e_p` menos la tasa del mismo `P` en otras noches

- **Dónde**: v7 l. 140-143 ("`Θ_p = e_p` menos la fracción de `e` en el **mismo punto `P_p`** evaluado
  en los rásteres cruzados de otras noches ... La quinta ronda lo midió fuera de la muestra: `+0,0005`
  [-0,017, +0,018]"), contra `scratchpad/v5/persist5.py:43-53`, que calcula
  `e = 1.0*(Z(R_otra_noche, P) >= zc)`, `rf = media de (Z(R_otra_noche, sitio_i) >= zc)` sobre los 5
  sitios, y `d = e - rf`. Ese `d` es el `+0,0005` de la tabla del informe de la ronda 5, l. 67.
- **Evidencia** (`python eje2.py`, eje 2 literal de la v7 sobre el estrato hermano):

  | | n | valor | IC 95 % | `e_p` | base en otras noches |
  |---|---|---|---|---|---|
  | **`Θ` literal de la v7** (5 rásteres usables de otras noches, mismo `P`) | 681 | **+0,0132** | [-0,0089, +0,0343] | 0,0837 | 0,0705 |
  | versión pareada con un solo ráster de otra noche | 681 | +0,0103 | [-0,0189, +0,0370] | 0,0837 | 0,0734 |

- **Qué pasa**: los dos números dan "compatible con cero", así que la **lectura** de §8 se sostiene, pero
  el número citado y su procedencia no. Y hay un detalle que sí cambia el sentido: la base del eje 2 es
  **0,0705**, es decir el mismo punto `P` supera el umbral el 7,1 % de las noches cualesquiera, contra
  el 3,2 % de un punto sorteado. Eso no es "el sitio no destaca": es "el sitio destaca siempre". El eje
  2 mide, correctamente, que **no destaca más esta noche**, que es otra cosa.
- **Cómo se ve en el resultado**: §8 fila 2 se lee como si el eje 2 dijera que el sitio es corriente,
  cuando lo que dice es que el exceso del sitio no depende de la noche.
- **Cómo reproducirlo**: `python eje2.py`, y la lectura de `persist5.py:43-53`.
- **CONFIRMADO. Gravedad 3.**

### H4. "Δ = estimación agrupada" tiene dos implementaciones legítimas que difieren en 0,020, y el umbral del veredicto está justo en el medio

- **Dónde**: v7 l. 199-201 ("`Δ_v` = media de `Δ_p` por volcán; `Δ` = estimación agrupada con
  remuestreo por noche de volcán (A94), estratificado **por volcán**"). El texto define primero la
  media por volcán y después llama "agrupada" a otra cosa, sin decir si el agrupamiento pesa por pasada
  o por volcán. El remuestreo descrito fija cómo se construye el intervalo, no cómo se pondera el punto.
- **Evidencia** (`python a3.py`), estrato hermano:

  | lectura | valor |
  |---|---|
  | agrupado por pasada (lo que hacen todos los scripts de las rondas 3 a 6) | **+0,0514** |
  | media de las medias por volcán, 10 volcanes | **+0,0713** |
  | media de las medias, sólo los 6 elegibles | +0,0416 |
  | agrupado por pasada, sólo los 6 elegibles | +0,0354 |

- **Qué pasa**: la diferencia entre las dos lecturas es 0,020, o sea el 40 % de la tolerancia entera, y
  una queda sobre el umbral del positivo y la otra debajo. El mecanismo es conocido y está medido:
  Isluga aporta 62 pasadas con `Δ = 0,000` exacto y Láscar 18 con `Δ = +0,167`, así que pesar por
  volcán le da a Láscar el mismo voto que a Copahue con 97.
- **Cómo se ve en el resultado**: dos personas con el mismo dato discuten si el veredicto fue positivo.
  Es el mismo defecto que la ronda 6 marcó en H6 para `R`, trasladado al estimador principal.
- **Cómo reproducirlo**: `python a3.py`, último bloque.
- **CONFIRMADO. Gravedad 3.**

### H5. "La misma comparación da +0,1091 con la imagen propia y +0,0145 con la cruzada" ya no es la misma comparación, y con el estadístico de la v7 la cruzada no baja a cero: baja a +0,079, con el intervalo fuera del cero

- **Dónde**: v7 l. 120-122 ("Esa imagen viene de un gránulo que **no** eligió nuestro píxel, que es lo
  que corta la maldición del ganador: medido, **la misma comparación** da +0,1091 con la imagen propia y
  +0,0145 con la cruzada"). Esos dos números son de la ronda 5, l. 64-65, medidos con `e_p` menos los 5
  sitios de referencia, que es el estadístico que la propia v7 **descartó** en §0 por sesgado.
- **Evidencia** (`python r3.py`), estrato hermano, con el estadístico de la v7:

  | | n | `Δ` | IC 95 % | tasa P | tasa X |
  |---|---|---|---|---|---|
  | imagen **propia** | 140 | **+0,1214** | [+0,0652, +0,1799] | 0,1357 | 0,0143 |
  | imagen **cruzada**, las mismas 140 | 140 | **+0,0786** | [+0,0340, +0,1241] | 0,0857 | 0,0071 |
  | diferencia (lo que corta la pasada cruzada) | 140 | +0,0429 | [-0,0148, +0,1034] | | |
  | imagen propia, las 194 que la tienen | 194 | +0,1289 | [+0,0781, +0,1814] | | |

- **Qué pasa**: con el estadístico viejo la pasada cruzada parecía cortar el 87 % del sesgo y dejar un
  residuo cuyo intervalo incluía al cero. Con el estadístico nuevo corta alrededor de un tercio y lo
  que queda **no** incluye al cero. La diferencia entre las dos lecturas no es que el instrumento haya
  empeorado: es que el brazo de referencia viejo estaba inflado (H5 de la ronda 6, razón de tasas 27,8
  en Láscar) y se comía la señal del sitio. El párrafo de §5 usa números del instrumento viejo para
  justificar una pieza del instrumento nuevo.
- **Cómo se ve en el resultado**: el documento promete que la pasada cruzada deja el residuo casi en
  cero, la corrida da un nivel de sitio que no baja de +0,05, y como la regla ahora mide contra cero
  (que es lo correcto, esta vez), ese nivel entra entero al veredicto.
- **Cómo reproducirlo**: `python r3.py`.
- **CONFIRMADO. Gravedad 3.**

### H6. El sorteo de `X` con la restricción de separación no está definido, y rompe la cláusula de "dos números por pasada" con que §4 fija la reproducibilidad

- **Dónde**: v7 l. 129-131 ("un punto `X_p` sorteado uniforme en área en el anillo de 1,5 a 3,0 km ... a
  más de 2T (1,5 km) de `P_p`, con `random.Random(7144)` y el orden de extracción declarado como en
  §4"), contra §4 l. 102-104 ("un único `random.Random(144)` ... **dos números por pasada** (primero
  `u` para `r`, después el acimut)").
- **Evidencia** (`python a1.py`): con la lectura de "re-sortear el par completo hasta que cumpla", el
  **19,2 %** de las pasadas necesita al menos un re-sorteo, hasta 3, así que el consumo de números por
  pasada va de 2 a 8 y el estado del generador deja de ser predecible. Con la lectura de "conservar el
  radio y re-sortear sólo el acimut" el resultado es otro:

  | lectura del rechazo | `Δ` | IC 95 % |
  |---|---|---|
  | re-sortear el par completo | **+0,0514** | [+0,0264, +0,0766] |
  | re-sortear sólo el acimut | **+0,0485** | [+0,0238, +0,0720] |

  Hay una tercera ambigüedad, sin efecto sobre la distribución pero sí sobre la reproducibilidad: §5 no
  dice **en qué punto del embudo** se hace el sorteo (antes o después de comprobar que hay imagen
  cruzada usable), y de eso depende qué número le toca a cada pasada.
- **Qué pasa**: la semilla 7144 no reproduce nada si tres implementadores honestos consumen el
  generador de tres maneras. La diferencia entre las dos lecturas es chica (0,003) comparada con el
  ancho del intervalo, así que no cambia un veredicto, pero sí impide que dos corridas den el mismo
  número, que es para lo que está la semilla.
- **Cómo reproducirlo**: `python a1.py`, bloques de `X` y de `Xaz`.
- **CONFIRMADO. Gravedad 2.**

### H7. La asimetría de radio entre `P` y el punto sorteado es real y grande, pero no muerde con el indicador binario; muerde si se pasa al estadístico continuo que §9 deja abierto

- **Dónde**: v7 l. 101-103 (el sorteo uniforme en área en el anillo de 1,5 a 3,0 km), l. 45-46 ("radio
  mediano 2,79 km, máximo 3,00 km") y l. 249-251 (§9, "se informa también el rango de `Z_q(P_p)` ...
  como estadístico continuo descriptivo").
- **Evidencia** (`python a1.py`, `python rad7.py`, `python cel7.py`):

  | | `P` | `X` sorteado |
  |---|---|---|
  | radio mediano | **2,779 km** | 2,348 km |
  | fracción más allá de 2,5 km | **76,5 %** | 41,7 % |

  El instrumento binario **no** tiene gradiente radial: con 17.370 sorteos repartidos en cinco anillos,
  la probabilidad de que `Z(X)` supere `zc` vale 0,0415 en el anillo de 1,50 a 1,90 km y 0,0400 en el de
  2,75 a 3,00. Pero la **mediana de z sí sube** con el radio, de **-0,101** a **+0,010**, que es el
  gradiente topográfico de A69 visto desde adentro del anillo. Y el contraste directo entre un punto al
  radio de `P` y uno uniforme da `+0,0206` con intervalo [+0,0000, +0,0408], o sea toca el cero: es
  compatible con ruido, no con un sesgo establecido.
- **Qué pasa**: con el umbral alto que usa el indicador (`zc` va de 2,32 a 6,07) el corte cae en la cola
  y la cola no depende del radio, así que la asimetría geométrica no se traduce en sesgo. Un
  estadístico continuo (el rango, la media de z, el propio `Z`) sí la hereda: el exceso medio de la
  celda de `P` vale **+0,349** en unidades de z y el corrimiento que regala el radio vale **+0,11**, o
  sea un tercio del efecto, gratis y sin volcán.
- **Cómo se ve en el resultado**: si en la corrida alguien reemplaza el binario por el continuo para
  ganar potencia (que es la tentación obvia después de H1 y H2), se lleva de regalo un tercio del
  efecto, y ese tercio es relieve puro.
- **Cómo reproducirlo**: `python rad7.py` y `python cel7.py`.
- **CONFIRMADO. Gravedad 2.**

### H8. Lo que el eje 1 estima está acotado y es medible: el 86 % es permanente, y tres cuartos de lo que queda lo produce el máximo sobre el disco, no la celda

- **Dónde**: v7 l. 237-239 (§9, "El eje 1 no distingue **relieve tibio** de **fuente volcánica** ...
  Esa separación es la que A83 declara agotada por vía física"). Eso es cierto, pero el documento deja
  la impresión de que no hay nada acotable, y sí lo hay.
- **Evidencia** (`python a2.py`, `python cel7.py`, `python clim7.py`), siempre sobre las mismas 681
  pasadas del estrato hermano:

  | descomposición del eje 1 | `Δ` | IC 95 % |
  |---|---|---|
  | total, ráster de la misma noche (45 a 120 min) | **+0,0514** | [+0,0264, +0,0766] |
  | el mismo con un ráster de **otra noche** (más de 3 días) | **+0,0441** | [+0,0223, +0,0668] |
  | **componente de esta noche** (la resta pareada) | **+0,0073** | [-0,0241, +0,0385] |
  | contra un punto del **mismo radio** y acimut sorteado | +0,0308 | [+0,0072, +0,0538] |
  | contra el **reflejo** de `P` por el cráter | +0,0441 | [+0,0193, +0,0674] |
  | con la **celda exacta** en vez del máximo sobre el disco de 0,75 km | **+0,0132** | [+0,0030, +0,0232] |

  Y la climatología espacial del exceso, construida con 18 a 77 rásteres por volcán:

  | | en el sitio de `P` | en el sitio de `X` | en el sector de ±15° de `P` | en la banda entera |
  |---|---|---|---|---|
  | fracción de rásteres en que se supera `zc` | **0,0338** | 0,0185 | 0,0048 | 0,0039 |

- **Qué pasa (el fenómeno)**: el sitio donde `keep_peak` publica supera el umbral 1,82 veces más seguido
  que un punto cualquiera, **en rásteres de cualquier noche**, mientras que su sector de acimut apenas
  está 1,24 veces sobre la banda. O sea el exceso no es un flanco entero tibio: es un punto fijo, chico
  y repetido. Y tres cuartos del efecto binario los produce el operador "máximo sobre las once o doce
  celdas del disco de 0,75 km", no la celda de `P`, que es exactamente la rugosidad direccional que la
  ronda 3 describió en su H1. La separación entre relieve y fuente sigue sin poder hacerse con el TIF,
  pero **lo que el eje 1 va a encontrar ya está identificado**: un rasgo fijo del campo de radiancia, no
  un evento.
- **Cómo se ve en el resultado**: la fila 3 de la tabla de §8 ("cae sobre un exceso" con el eje 2
  claramente positivo) está prácticamente excluida por el dato de afuera, y la fila 2 es la que va a
  salir. Conviene que el pre-registro lo diga antes, no después.
- **Cómo reproducirlo**: `python a2.py && python cel7.py && python clim7.py`.
- **CONFIRMADO. Gravedad 2.**
- **Lo que se puede agregar y es medible** (para §5 o §9, eligiendo antes de medir): (1) informar el
  brazo de **otra noche** junto al del veredicto, que es la cota directa de cuánto es permanente y
  cuesta una corrida más del mismo instrumento; (2) informar la variante de **celda exacta**, que separa
  la rugosidad del operador del exceso del lugar; (3) informar la **climatología por sector**, que acota
  el aporte del acimut. Las tres se corren con el mismo código y ninguna toca el pipeline. Lo que **no**
  sirve es el reflejo, ya refutado en la ronda 3 y que aquí vuelve a salir sesgado (el reflejo de `P`
  supera el umbral menos seguido, 0,0396, que un punto al mismo radio con acimut sorteado, 0,0529).

### H9. Detalles que dejan dos implementaciones legítimas, o números que no reproducen

- **`Δ_v > 0` y los ceros exactos** (l. 205): con un indicador binario los empates exactos son comunes.
  En el estrato hermano Isluga da `Δ = 0,000` sobre 62 pasadas. Con la redacción actual un cero cuenta
  en contra del positivo, lo que es defendible, pero conviene decirlo, porque un volcán mudo puede
  hundir la condición de los dos tercios sin aportar información. (Hoy no muerde: entre los 6 elegibles
  del veredicto, 5 tienen `Δ_v > 0` en el estrato hermano.)
- **El eje 2 y los "rásteres cruzados de otras noches"** (l. 140-141): no está dicho si son los 5
  rásteres usables más cercanos a más de 3 días, o las **parejas cruzadas** de las 5 noches más
  cercanas. Yo implementé lo primero. Son dos poblaciones distintas de imágenes.
- **`random.Random(144)` para el remuestreo** (l. 200): todas las rondas anteriores usaron
  `numpy.random.default_rng(144)`. Son generadores distintos, así que la semilla no reproduce el
  intervalo entre implementaciones. Y el 144 se usa además para el sorteo de `zc_punto` en §4, con lo
  que dos cosas distintas comparten semilla sin que eso sea intencional.
- **"razón de tasas ... 4,37 contra 6,70 agrupado"** (l. 147): esos dos números son **tasas en por
  ciento** (0,0437 y 0,0670) de la tabla de la ronda 6, no una razón. La razón es 1,53. Los otros dos
  (27,8 y 11,7) sí son razones. La frase mezcla las dos cosas.
- **"máximo 3,00 km"** (l. 45): el máximo medido es **3,002 km**. Es el redondeo del sorteo, no importa,
  pero el anillo de comparación llega exactamente a 3,0 y algún `P` queda un metro afuera.
- **§9 dice "la ronda 6 midió 72,1 %" de `Δ_p` en cero** (l. 249-250). Con el estadístico de la v7 son
  **89,0 %** (y 92,7 % en el nulo). El número se quedó del estadístico anterior, y la diferencia importa
  porque es la razón de H2.
- **CONFIRMADO (lectura del texto y medición). Gravedad 1.**

---

## VERIFICADO LIMPIO

Lo que la v7 arregló y lo que medí y quedó en pie:

- **`N1` es una compuerta que se puede pasar, y esa era la pregunta 1.** Con dos puntos sorteados sobre
  el estrato hermano, con la regla literal: **`-0,0029` [-0,0220, +0,0161]** con la separación de
  1,5 km entre los dos puntos, y **`+0,0044` [-0,0161, +0,0229]** sin ella. Las dos lecturas quedan
  cómodamente dentro de ±0,05, aplicando la regla al intervalo como pide §5. El `-0,0984` que hundía a
  la v6 desapareció, y desapareció por la razón correcta: el suelo del instrumento ahora se cancela por
  construcción en vez de estimarse sobre un pool mezclado.
- **No hay ninguna asimetría escondida entre "`P`" y "punto sorteado" fuera de la hipótesis**, y la
  busqué por cuatro caminos. Los contrastes entre puntos sorteados, que por simetría deben dar cero,
  dan cero: libre contra libre `+0,0044` [-0,0161, +0,0229]; libre contra el que lleva la separación
  respecto de `P`, `+0,0073` [-0,0105, +0,0262]; el que lleva la separación respecto de `A` contra `A`,
  `+0,0029` [-0,0161, +0,0220]; reflejo contra uniforme `+0,0073` [-0,0104, +0,0245]. El único que
  toca el borde es "mismo radio que `P`" contra uniforme, `+0,0206` [+0,0000, +0,0408], y el gradiente
  radial medido aparte lo explica como ruido (H7).
- **No hay atrición y no hay atrición asimétrica**: `Z` devolvió un valor en **681 de 681** pasadas para
  los ocho puntos que evalué (`P`, el `X` literal, el `X` de acimut, los dos del nulo, el nulo libre, el
  de mismo radio y el reflejo). Ninguna pasada se pierde porque uno de los dos puntos caiga sin dato, así
  que el pareo nunca se rompe de un lado solo.
- **No hay efecto de borde del ráster de 134 por 134.** Las 132 imágenes que abrí miden 134 por 134
  celdas de 0,374 a 0,385 km, o sea unos 50 km de lado; el borde más cercano al cráter está a **18,4 km**
  (Cordón Caulle) y a 25,3 km en el mejor caso, contra los 3,0 km del anillo. La fracción de celdas sin
  `ΔL0` es **plana en radio** entre 0 y 4 km, y sólo dos volcanes tienen alguna (Llaima 12,5 % y Nevados
  de Chillán 12,5 a 17,2 %, igual de repartida en todos los anillos). Una de las 132 imágenes está en
  EPSG:32719, consistente con las ocho adquisiciones UTM que A106 documenta.
- **Las tres salidas son alcanzables con la muestra real**, que era la pregunta 3: bajo el nulo la regla
  da "no se distingue" el 97 % de las veces y no produjo **ningún** falso positivo en 200 repeticiones;
  el positivo sale el 97 % de las veces con un efecto de +0,12; y el INCONCLUSO aparece en el medio. Los
  mínimos de §7 se cumplen con holgura: **349 noches de volcán** contra 30, y **6 volcanes con 20 noches**
  contra 3.
- **El embudo reproduce exacto**: 1.113 pasadas candidatas (patrón, publicadas, `neg_limpio`, fuera de
  Lastarria) y, con la ventana de 45 a 120 minutos, **601 pasadas en 349 noches**, con Copahue 66,
  Llaima 63, Villarrica 55, Chaitén 52, Nevados de Chillán 38 y Planchón-Peteroa 27. Los seis números
  de l. 49 son los seis que mido.
- **La tabla de `zc_punto` de §4 reproduce exacto** con la regla literal: Chaitén 4,22 [3,19, 4,66],
  Cordón Caulle 4,25, Planchón-Peteroa 3,23, Nevados de Chillán 2,47, Isluga 6,07 [2,04, 7,69] sobre 13
  pasadas. Y el intervalo de Isluga ya dice 2,04 en **las dos** partes del documento: la contradicción
  entre §4 y §9 que marcó la ronda 6 quedó cerrada.
- **La geometría que cita §2 y §6 reproduce**: `mirova_center` está a **0,12 km** del cráter en
  Lastarria, **7,57 km** en Cordón Caulle, **4,86 km** en Tupungatito y **2,02 km** en Planchón-Peteroa.
  El control congelado de M1 son **19 archivos** (`git ls-files` los cuenta) y
  `pipeline/geo_utils.py:53-78` es efectivamente `get_detection_anchor` completa.
- **El radio mediano de nuestros `P` es 2,779 km**, que es el 2,79 de l. 45.
- **Los números que la ronda 6 refutó ya no están**: `grep` de "2.541", "1.824", "1.594", "42 de 43" y
  "2,50" en el documento devuelve **cero líneas**. La fila final de la tabla de §8 ya decide sobre `G` y
  `N1`, y `C1` y `C2` aparecen una sola vez, para decir que no existen.
- **El filtro diurno es efectivamente redundante**, como declara l. 126: sobre 1.289 más 1.289 pasadas
  el estado `cruzada_diurna` no apareció ni una vez. La ventana de 120 minutos las corta antes.
- **El documento no tiene ningún guion largo ni medio**: un `grep -c` del carácter U+2014 sobre el
  pre-registro devuelve 0.

**No verificado** (queda abierto y lo marco como SOSPECHA): los `Z(P)` de la muestra del veredicto y
las clases de M1, que no calculé a propósito; si los controles `G` y `H` pasan sus criterios, porque no
los corrí; el conteo de 12 pasadas de M1 y el 97,1 % de `P` con vecino, que verificaron las rondas 5 y 4
y yo no repetí; la sensibilidad de `Distancia_km` con OCR; y si el brazo de otra noche se sostiene
cuando el ráster de otra noche cae en un régimen de nieve distinto, porque la ventana entera es invierno
austral y no pude separarla.

---

## Correcciones para una v8, por gravedad

1. **(4) Declarar en §1 el valor fuera de muestra del estadístico de la v7 y decidir qué hacer con la
   zona muerta (H1).** El número es `+0,0514` [+0,0264, +0,0766], `+0,0511` re-ponderado a la mezcla del
   veredicto y `+0,0354` en los 6 volcanes elegibles. Con la regla escrita, un efecto así entrega
   INCONCLUSO el 90 % de las veces. Hay que elegir por escrito una de cuatro: declararlo y aceptar el
   INCONCLUSO probable diciendo de antemano qué se hace con él; bajar el umbral del positivo a un valor
   que la potencia alcance; ensanchar la banda de equivalencia con el costo escrito; o cambiar de
   estadístico leyendo antes H7. Lo que no se puede es dejar el número afuera: es el dato más predictivo
   que hay y está a una corrida de distancia.
2. **(4) Reemplazar el mapa de potencia de §7 por el de este estadístico (H2).** Medido con la
   estructura real de noches y los bloques de nulo reales: +0,064 da el positivo el **8 %**, +0,083 el
   **35 %** y +0,131 el **97 %**; bajo el nulo, "no se distingue" 97 % y ningún falso positivo en 200
   repeticiones. Y el ancho del intervalo del tramo posterior a #535 es **0,0975**, no 0,083.
3. **(3) Corregir el número y la procedencia del eje 2 (H3).** El `+0,0005` de la ronda 5 es
   `e_P` menos los 5 sitios de referencia en un ráster de otra noche, no `Θ`. El `Θ` literal, medido
   fuera de la muestra, vale **`+0,0132` [-0,0089, +0,0343]**, y su base es 0,0705, que conviene escribir
   al lado porque dice que el sitio destaca **siempre**, no que no destaque.
4. **(3) Fijar si `Δ` pesa por pasada o por volcán (H4).** Agrupado por pasada da +0,0514 y la media de
   las medias por volcán +0,0713, con el umbral del positivo justo en el medio. Lo natural es pesar por
   pasada, que es lo que hacen todos los scripts de las rondas anteriores, pero hay que escribirlo.
5. **(3) Reescribir el párrafo que justifica la pasada cruzada (H5).** Con el estadístico de la v7 la
   cruzada baja de **+0,1214** a **+0,0786** sobre las mismas 140 pasadas, y el intervalo de la cruzada
   **no** incluye al cero. Los +0,1091 y +0,0145 son del estadístico descartado y hay que sacarlos o
   etiquetarlos como tales.
6. **(2) Definir el sorteo de `X` con la restricción (H6)**: si se re-sortea el par completo o sólo el
   acimut (las dos lecturas dan +0,0514 y +0,0485), y en qué punto del embudo se extrae. Con el rechazo
   del par, el 19,2 % de las pasadas consume más de dos números y la cláusula de §4 deja de valer.
7. **(2) Escribir la asimetría de radio y su consecuencia (H7)**: `P` tiene radio mediano 2,78 km contra
   2,35 km del sorteo, el indicador binario es insensible a eso (0,0415 contra 0,0400 sobre 17.370
   sorteos) pero cualquier versión continua no lo es, porque la mediana de z sube +0,11 a lo ancho de la
   banda contra un exceso propio de `P` de +0,35.
8. **(2) Agregar a §5 los tres brazos que acotan lo que el eje 1 estima (H8)**: el de otra noche
   (+0,0441 de +0,0514, o sea el 86 % es permanente), el de celda exacta (+0,0132, o sea tres cuartos
   del efecto binario los pone el máximo sobre el disco) y la climatología por sector (el sitio de `P`
   está 1,82 veces sobre el de `X`, su sector sólo 1,24 veces sobre la banda). Ninguno separa relieve de
   fuente, que sigue siendo cierto, pero los tres acotan y los tres se corren con el mismo código.
9. **(1) Cerrar los detalles de H9**: los ceros exactos en la condición de los dos tercios; qué son los
   "rásteres cruzados de otras noches" del eje 2; qué generador implementa el remuestreo; el 4,37 contra
   6,70, que son tasas y no una razón; y el 72,1 % de §9, que con este estadístico es 89,0 %.

---

## Resumen

El instrumento quedó bien y la compuerta también. `N1` es cero en sus dos lecturas (`-0,0029` y
`+0,0044`, las dos dentro de ±0,05), no hay atrición, no hay borde de ráster, no hay gradiente radial
del indicador binario, y los cuatro contrastes entre puntos sorteados dan cero. El estadístico pareado
arregla de verdad lo que la v6 rompió.

Lo que la v7 no vio es que su pregunta ya tiene respuesta afuera. Corrí su estadístico literal sobre el
estrato hermano: **`Δ = +0,0514` [+0,0264, +0,0766]**, y re-ponderado a la mezcla del veredicto
+0,0511. Con la estructura real de noches, un efecto así entrega **INCONCLUSO el 90 % de las veces**:
cae justo entre el umbral del positivo y la banda de equivalencia. El mapa de potencia de §7 no es de
este estadístico y además copió el 87 % de la v5 donde la ronda 6 había medido 56 %; lo real es 35 %.

Y el eje 1, medido, estima un **rasgo permanente**: con un ráster de otra noche da +0,0441 de los
+0,0514, así que lo de esta noche vale +0,0073 [-0,0241, +0,0385]. Tres cuartos del efecto los produce
el máximo sobre el disco de 0,75 km y no la celda. El sitio de `P` supera el umbral 1,82 veces más
seguido que un punto cualquiera en cualquier noche; su sector de acimut, sólo 1,24. La fila 2 de la
tabla de §8 es la que el dato ya señala.

Quedan además cinco defectos menores: el +0,0005 del eje 2 es de otro estadístico (el literal vale
+0,0132), "estimación agrupada" admite dos pesos que difieren en 0,020 con el umbral en el medio, los
+0,1091 contra +0,0145 son del instrumento descartado, el sorteo con separación no está definido, y el
72,1 % de §9 hoy es 89,0 %.

**No es viable tal como está.** Con las correcciones 1 y 2 hechas antes de medir, sí.
