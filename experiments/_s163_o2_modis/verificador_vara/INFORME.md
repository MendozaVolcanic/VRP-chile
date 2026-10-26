# Verificación de la vara preliminar del fondo (O2 MODIS), verificador con contexto limpio

Carpeta: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s162-modis-2-0dd578\experiments\_s163_o2_modis\verificador_vara\`
Fecha del servidor al correr: 2026-10-26. Los caminos de error se escribieron en `CAMINOS.md` antes de abrir el script.
Todo lo que sigue sale de salidas de herramientas de esta sesión (cada script y su `_salida.txt` están en esta carpeta). Lo no medido va como SOSPECHA o SIN DATO.

## En una pantalla

1. Los números del resultado se reproducen: re-corrí el script en una copia y el `.json` y el `_salida.txt` salieron byte a byte iguales (md5 `b13eec2d...` y `364bd0de...`). El hueco lo reimplementé yo desde el `.m`: coincide con el del script en 404 de 404 escenas.
2. La regla contra MATLAB la reproduje por mi cuenta sobre los resultados de VIIRS 750: 166 de 166 en el delta de fondo (LBK) y, en las 84 escenas con matriz de fondo guardada, la matriz entera dentro del hueco. Con 1 píxel, MATLAB promedia las dos celdas a 2 columnas del píxel (51 de 51), y esa forma cerrada reproduce la regla en 167 de 168 escenas MODIS de 1 píxel (la 168 tiene NaN en esa pareja).
3. Las 404 «escenas» son 191 distintas (87, 57, 37 y 10 por número de píxeles) y 355 de las 404 filas son de Láscar. Las conclusiones valen para Láscar, no para «MODIS».
4. La mediana «1,000» de 1 píxel esconde el efecto: en 139 de 168 filas el port elige la otra pareja de celdas; la razón queda bajo 1 en 72 y sobre 1 en 67, y la diferencia típica es 9,1 % (no 0). Las diferencias de 4 píxeles salen casi todas (14 de 15) de una sola forma, el bloque compacto de 2 x 2, que ninguna escena de VIIRS validó contra MATLAB.
5. Pendiente de verdad: que el fondo de MODIS en MIROVA sea el mismo del `.m` de VIIRS 750 (premisa heredada, no verificable aquí) y la corrida en MATLAB real del paquete MODIS.

## Veredicto por afirmación del RESULTADO (leído recién en el paso 3)

| # | afirmación | veredicto | ancla |
|---|---|---|---|
| A1 | 404 escenas, 116 pasadas, lotes S159 y MOD-C | EN PARTE | 404 filas y 116 (lote,id) correctas; son 105 pasadas por (volcán,hora), 11 están en ambos lotes, y 191 escenas distintas por grilla+máscara (`modis_hueco_y_escenas_salida.txt`) |
| A2 | La construcción reproduce el VRP del port en 404 de 404 (máx. 2e-16), así que lo que sigue es sólo la regla | CONFIRMADO | re-corrida idéntica; el control puede fallar: con halo 5 rompe 404/404, sin halo 404/404, máscara traspuesta 376/404, corrida una columna 404/404 (`mutantes_identidad_salida.txt`) |
| A3 | «0 aristas ilegales» | EN PARTE | lo reproduce, pero usa el mismo predicado que construye la triangulación; sólo vigila el algoritmo de volteos, no la regla (VV-08) |
| A4 | Nulo: marco cambiado discrepa en 196 de 404 | CONFIRMADO | idéntico en mi re-corrida. Contra MATLAB el marco cambiado coincide en 0 de 51 escenas de 1 píxel (`regla_vs_matlab_viirs_salida.txt`) |
| A5 | Ninguna alerta fuera de la envolvente convexa | CONFIRMADO, pero trivial | 0 también con mi `ConvexHull` (`envolvente_y_raros_salida.txt`); las alertas están a 18 celdas o más del borde (VV-04) |
| A6 | Regla confirmada en 166 de 166 escenas de VIIRS 750 | CONFIRMADO | 166/166 en LBK con mi hueco; matriz completa en 84/84 (`regla_lbk_todas_salida.txt`, `regla_166_salida.txt`). 51 de las 166 son de 1 píxel |
| A7 | Tabla por número de píxeles (168/132/77/27; 132, 2, 1, 15; 79, 0, 0, 12; 29, 129, 76, 7) | CONFIRMADO numérico | recalculado desde el `.json` (`estadistica_distintas_salida.txt`) |
| A8 | «port/regla, mediana 1,000» (1 píxel) | EN PARTE | el valor es exacto pero no describe el efecto (VV-02) |
| A9 | Variante `fisica`: 36 de 1 píxel, razón 0,75 a 3,78, 19 sobre 10 %; 7 de 4 píxeles, mediana 1,12 | CONFIRMADO | `fisica_y_casos_salida.txt` (0,7486 a 3,7767; 19; 1,116) |
| A10 | Llaima 2026-07-24 01:05 baja de 0,43 a 0,11 MW; Láscar 2026-05-11 07:55 de 0,30 a 0,21 | CONFIRMADO | 0,4304 a 0,1140 y 0,2969 a 0,2111; ambas reproducidas con la forma cerrada |
| A11 | Llaima es «la publicación que MOD-C atribuyó a artefacto de gradiente»; Láscar «candidata a experimental» | SIN DATO | no lo miré |
| A12 | «La detección no cambia (la regla sólo toca el fondo)» | CONFIRMADO por construcción | el script toma la máscara tal cual; ningún VRP cambia de signo (mínimo con la regla 0,074 MW, ninguno <= 0) |
| A13 | Cuatro centros cocirculares y «con un solo píxel, ese centro es todo el fondo» | EN PARTE | lo segundo vale; lo primero, para 1 píxel, son cuatro celdas a distancia 2 sobre los ejes (VV-07) |
| A14 | «Nuestro port elige como lo hace scipy» | CONFIRMADO | Qhull elige la pareja de filas en 139 y la de columnas en 28 de 168 (un caso con NaN no aplica) (`un_pixel_forma_cerrada_salida.txt`) |
| A15 | Cambia la magnitud en 1 y 4 píxeles | EN PARTE | 1 píxel sí. 4 píxeles es el bloque 2 x 2 y está extrapolado (VV-03) |
| A16 | «con ella la prueba M y la curva de cenit del censo» | SIN DATO | no lo miré |
| A17 | «El censo guarda la grilla 51 x 51 de cada pasada; se calcula fuera de línea sin otro despacho» | SIN DATO | no lo miré |
| A18 | «El código de MIROVA estima el fondo ... halo de 3 x 3 ...» aplicado a MODIS | SIN DATO | el `.m` es de VIIRS 750 (VV-05) |

## Hallazgos propios

**VV-01 (gravedad 3, confianza alta). Las «escenas» no son independientes ni son 404.** Colapsando filas con la misma grilla y la misma máscara quedan 191 (1 píxel: 168 a 87; 2: 132 a 57; 3: 77 a 37; 4: 27 a 10). `sensible` y `pixel` repiten a `fisica` y la razón port/regla es idéntica entre filas de la misma firma (0 excepciones). Hay 11 pasadas (volcán, hora) en ambos lotes y 39 claves (volcán, hora, variante) repetidas. Por volcán: 355 filas de Láscar (161 de las 191 distintas), 33 de Nevados de Chillán, 16 repartidas en otros siete volcanes. Las diferencias de 1 píxel mayores a 10 % son 79 filas, 37 escenas distintas (35 de Láscar); la escena de x3,78 de Llaima aparece tres veces (tres variantes, una firma). Efecto: los porcentajes de la tabla sobreestiman el tamaño de muestra y describen sobre todo a Láscar.

**VV-02 (gravedad 3, confianza alta). La mediana de la razón no mide el efecto.** Con 1 píxel hay 72 razones bajo 1 y 67 sobre 1 (29 iguales); la mediana de |razón-1| es 0,091 (0,085 en escenas distintas; 0,115 en `fisica`). El signo es simétrico porque la regla es una pareja de celdas y Qhull casi siempre la otra: no hay sesgo, hay ruido por escena de un 9 % típico y hasta 3,8 veces. Quien lea «mediana 1,000» concluirá que no hay efecto en la mediana del censo y se equivocará en cualquier métrica por pasada (prueba M, umbral por escena).

**VV-03 (gravedad 3, confianza media). El efecto de 4 píxeles está extrapolado.** De las 15 filas de 4 píxeles que difieren más de 1 %, 14 son el bloque compacto de 2 x 2 (19 filas, 6 escenas distintas; 4 distintas difieren). Entre las 147 escenas VIIRS de 1 a 4 píxeles que usé (50 formas) no hay ninguna con esa forma (`por_forma_salida.txt`). Sí hay 19 de 5 a 30 píxeles (huecos compactos de 5 x 5 o más) que coinciden con MATLAB, así que la regla probablemente se extiende, pero eso es SOSPECHA, no dato. Las formas de 3 píxeles sin cobertura en VIIRS (61 de 77 filas) dan la misma respuesta en el port y en la regla (0 diferencias), por lo que no dependen de la regla.

**VV-04 (gravedad 2, confianza alta). «Cero fuera de la envolvente» es cierto por diseño de la ventana.** Las alertas están a 18 celdas o más del borde de la grilla de 51 x 51; el borde no es alcanzable en este paquete. Hay dos escenas con más de 1000 celdas NaN originales a 2 y 3 celdas de la alerta (Nevados de Chillán `fisica_geo5km`, Puyehue `sensible`), donde la razón es 1,0000 y donde en Puyehue la pareja de columnas contiene NaN (la forma cerrada no aplica). VIIRS sí validó huecos con NaN originales: 83 de las 166 escenas.

**VV-05 (gravedad 3, SIN DATO). Premisa heredada: el fondo de MODIS en MIROVA es el del `.m` de VIIRS 750.** El `.m` público es de VIIRS 750; `armar_paquete_o2_modis.py` y el LEEME suponen que «no depende del sensor salvo por el coeficiente», incluidos el halo de 3 x 3 para 4 píxeles o menos y `fillmissing2`. Nada en el paquete lo prueba. Si MIROVA MODIS rellena distinto, la «vara» mide el `.m` de VIIRS sobre grillas MODIS, no a MIROVA MODIS.

**VV-06 (gravedad 2, SOSPECHA). La regla se validó sólo en una grilla de 67 x 67 y una versión de MATLAB.** `resultado_o2.mat` trae `R2026b (26.2.0.3386108)`; el `.m` declara R2024a o posterior; MODIS es de 51 x 51. Con 1 píxel la elección fue la misma en 73 escenas, 27 posiciones distintas y las cuatro paridades de (fila, columna) (`posiciones_viirs_salida.txt`), lo que apoya que no depende de la posición; que no dependa del tamaño ni de la versión no está probado. Las 168 escenas MODIS de 1 píxel están en 21 posiciones distintas, todas con la columna entre 22 y 32.

**VV-07 (gravedad 1, confianza alta). Lectura útil y precisión de redacción.** Con 1 píxel el hueco es de 3 x 3 y el círculo vacío más grande tiene cuatro celdas sobre los ejes a distancia 2 (rombo), no «cuatro centros vecinos». MATLAB reproduce el promedio de las celdas (fila, col-2) y (fila, col+2) en 51 de 51 escenas VIIRS (`un_pixel_forma_cerrada_salida.txt`). El nombre «marco x = fila» del script significa, en la práctica, esa pareja de columnas; conviene escribirlo así para que nadie lea «pareja de filas». La forma cerrada además da la vara de 1 píxel sin Delaunay ni MATLAB.

**VV-08 (gravedad 2, confianza alta). El control de «0 aristas ilegales» no es independiente.** Usa `lado_perturbado`, el mismo predicado con que se construye la triangulación; sólo detecta un fallo del algoritmo de volteos. La evidencia independiente de la regla es la comparación con MATLAB (A6) y la forma cerrada de 1 píxel.

**VV-09 (gravedad 1, confianza alta). El control de identidad es ciego a los NaN originales.** Sin tapar los NaN originales, la identidad se rompe sólo en 1 de 404 escenas. Ese manejo lo cubre la validación con VIIRS (83 escenas con NaN), no el control del armado.

**VV-10 (gravedad 1, confianza alta). Errores míos corregidos en el camino.** (a) Primera versión de mi máscara con `reshape(order='F')` sobre un arreglo C-contiguo: modificaba una copia y el LBK salió 0 en todas; lo corregí y está así en los scripts finales. (b) Mi primera forma cerrada comparaba contra NaN con `>` (da False) y dejó pasar la escena de Puyehue como «sin diferencias»; ahora cuenta aparte las escenas sin forma cerrada (1). Los resultados de arriba son los de las versiones corregidas.

## Caminos de CAMINOS.md y su resultado

1. Hueco distinto al del `.m`: descartado. Reimplementación propia (indices lineales columna-primero, base 1, dilatación cuadrada por bucle, NaN originales incluidos): 0 diferencias en 404.
2. Máscara o matriz traspuesta: descartado. La máscara del `.mat` coincide con `npix` en 404/404; la traspuesta rompe el control de identidad en 376/404.
3. Marco equivocado: descartado para 1 píxel (51/51 contra MATLAB, 0/51 con el marco cambiado); para 2 a 30 píxeles coincide en LBK 166/166 (el marco cambiado coincide en 38 de 147 en 1 a 4 píxeles y 4 de 19 en 5 a 30).
4. Control de identidad que no puede fallar: descartado (VV-09 es el único punto ciego).
5. «Fuera de la envolvente» mide otra cosa: mide lo que dice, pero es vacío por diseño (VV-04).
6. Escenas repetidas: confirmado (VV-01).
7. Fondo vs VRP: las razones son de VRP; no hay VRP <= 0 ni no finitos.
8. Reproducibilidad: confirmada byte a byte.
9. Ventana recortada: el `.m` recibe la misma matriz de 51 x 51; sin diferencia de marco.
10. Reporte con NaN: sin NaN ni infinitos en las razones.

## Afirmaciones del RESULTADO que van más allá de lo verificado

- «Llaima ... la publicación que el diagnóstico de MOD-C atribuyó a un artefacto de gradiente» y «Láscar ... la candidata a experimental» (no leí MOD-C).
- «Lo que cambia es ... la prueba M y la curva de cenit del censo» (consecuencia no medida).
- «El censo de MOD-D guarda la grilla 51 x 51 ... se puede calcular después ... sin otro despacho» (no verificado).
- «El código de MIROVA estima ese fondo tapando ... halo de 3 x 3 ...» para MODIS (VV-05).
- «Nuestro port elige como lo hace scipy» como explicación causal de la diferencia: medí qué pareja elige (139/28), no el mecanismo interno de Qhull.
- «Cuatro centros vecinos están sobre un mismo círculo» en el caso de 1 píxel (VV-07).
- La tabla hablada como si fueran 404 escenas independientes de «MODIS» (VV-01).
- Las cifras de 4 píxeles como efecto de la regla de MATLAB (VV-03).

## VERIFICADO LIMPIO

- Reproducibilidad total de `.json` y `_salida.txt` (misma máquina, Python 3.12.10).
- Hueco (orden de máscara, NaN, halo, base 1, columna primero) idéntico al del `.m` en las 404 escenas.
- Regla contra MATLAB: 166/166 en LBK, 84/84 en matriz completa, con hueco propio y el módulo `delaunay_perturbado.py` del blob citado (el blob no lo re-hasheé; el script lo comprueba por asserción y corrió sin fallar).
- Forma cerrada independiente de 1 píxel: 167/168 en MODIS, 51/51 en VIIRS.
- Cifras de la tabla, de `fisica` y de los casos de Llaima y Láscar.
- Ningún VRP no positivo ni no finito; la detección no cambia.
- Control de identidad capaz de fallar frente a cinco de seis mutaciones del hueco y de la máscara.

## Archivos de esta carpeta

`CAMINOS.md`; `copia\` (script, regla, entradas y salidas re-corridas); `viirs_matlab\` (entradas y resultado de MATLAB de VIIRS 750 extraídos de `origin/s163-o2-paquete`, 19 MB, para repetir la validación); scripts `modis_hueco_y_escenas.py`, `regla_vs_matlab_viirs.py`, `regla_166.py`, `regla_lbk_todas.py`, `un_pixel_forma_cerrada.py`, `por_forma.py`, `formas_y_cerrada.py`, `estadistica_distintas.py`, `mutantes_identidad.py`, `envolvente_y_raros.py`, `fisica_y_casos.py`, `insp_viirs.py`, cada uno con su `_salida.txt`. Nada se escribió fuera de esta carpeta; sin commit, push ni stash.
