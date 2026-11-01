# Segundo oráculo de MIROVA VIIRS 750 (segunda ronda S158)

Port de `MIROVA_VIIRS750_hotspot_detection.m` y `MIROVA_VIIRS750_VRP.m` escrito sin ver
`experiments/_s158_oraculo_mirova/`. Cada bloque de `mirova_v750_r2.py` cita la línea del `.m` que traduce.

## Resultado en Etna (control contra producción de MIROVA)

`control_etna.py` (salida en `control_etna_salida.txt`), pasada de la matriz de ejemplo, NOAA-20, 2023-05-19 00:54 UTC,
contra la fila del OSF v2.5 (Resolution 750, Satellite 4):

| magnitud | segundo oráculo | OSF v2.5 |
|---|---|---|
| Npix | 5 (los 5 en BOX == 2, el cuadro central de 7 × 7) | 5 |
| Tot_Lmir_hot | 1,965342180 | 1,965342180 |
| Tot_Lmir_bk | 1,080443826 (triangulación por defecto de Qhull) | 1,072886152 |
| VRP | 9.805.780 W (razón 0,9915) | 9.889.528 W |

La detección es exacta (mismos píxeles, misma radiancia). La diferencia está entera en el fondo.

## El fondo depende de una elección que el `.m` no fija

`fillmissing2(...,'linear')` no documenta su método (la página de MathWorks sólo dice «Linear interpolation of nonmissing
entries»). `firma_fillmissing2.py` (salida en `firma_fillmissing2_salida.txt`) prueba candidatos sobre los mismos 5
píxeles:

- interpolación por filas, por columnas, su promedio y un relleno armónico: fuera por 1 a 18 %;
- interpolación lineal sobre una triangulación de Delaunay: en una grilla regular la triangulación no es única (cuatro
  puntos cocirculares por celda). Triangulando con coordenadas perturbadas e interpolando con las exactas, 400 semillas
  dan **67 triangulaciones con fondo distinto**, de 1,060077 a 1,085909 (VRP de 10,03 a 9,75 MW, ±1,3 %), y **una de
  ellas da 1,072886152, igual al OSF a 3e-10** (el CSV trae 9 decimales). Por azar, que una de 67 caiga a menos de 1e-9
  del valor del OSF tiene probabilidad del orden de 5e-6.

Conclusión: `fillmissing2` 'linear' es interpolación lineal sobre una triangulación de Delaunay (CONFIRMADO con un
número de producción de MIROVA), y la diagonal que elige MATLAB en cada celda no es la de Qhull por defecto. Cualquier
port en Python reproduce el VRP de MIROVA sólo dentro de una banda que depende de la escena: ±1,3 % en Etna.

## Comparación con el primer oráculo (`comparar_oraculos.py`, salida en `comparar_oraculos_salida.txt`)

El primero se usó como caja negra (sólo se leyeron sus firmas). En Etna su fondo es 1,073661545, que es **otra** de las
67 triangulaciones (VRP 9,881 MW, razón 0,9991): su 0,09 % salió de una triangulación más cercana, no de una
reproducción exacta del interpolador.

Escenas sintéticas: el fondo de Etna con el núcleo aplanado, ruido y gradiente, y de 0 a 5 focos de 1,02 a 15 veces la
radiancia en la caja externa, el anillo y la cumbre, con vecino débil para ejercer el segundo pase; noche, día, sun-glint
de 5 a 20° y escenas con 30 a 60 % de M15 inválido.

| comparación | escenas | con alerta | máscaras distintas |
|---|---|---|---|
| segundo contra primer oráculo | 600 | 378 | **0** |
| control: mínimo NTI de la cumbre 0,003 → 0,03 | 200 | 129 | 42 |
| control: sigma de ROI1 y ROI2 intercambiados | 200 | 129 | 25 |
| control: sin segundo pase | 200 | 129 | 25 |
| control: K1 nocturno −0,7 → −0,8 | 200 | 129 | **0** |

Las tres primeras mutaciones se ven, así que la comparación puede fallar. La de K1 no se ve: en estas escenas todo píxel
con NTI entre −0,8 y −0,7 también pasa el test contextual, y el conjunto final de alertas es el mismo aunque cambie por
qué camino entra. Eso dice algo del código de MIROVA, no del instrumento: **el valor de K1 casi no decide qué se publica
en escenas de este tipo**; decide qué píxeles salen de la población de fondo (TRASLADADO a escenas reales, no medido).

El VRP, con las mismas máscaras, difiere entre los dos oráculos en más de 1 % en 52 de 378 escenas y en más de 5 % en
23 (máximo 82 %, un foco en el borde de la grilla): es la misma ambigüedad de triangulación, más la extrapolación fuera
de la envolvente convexa, que el `.m` tampoco fija. **Ningún oráculo en Python sirve como vara del VRP al 1 %**; sirve
para la detección (exacta) y para el VRP dentro de unos pocos por ciento.

## Lo que este oráculo no puede decir

- La extrapolación de `fillmissing2` en el borde (este port usa el vecino más cercano fuera de la envolvente).
- Que el código publicado sea el operacional completo: el README se declara compacto; el control de Etna es una sola
  pasada de 2023.
