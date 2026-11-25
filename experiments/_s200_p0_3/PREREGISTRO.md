# Pre-registro: P0 parte (3), enmascaramiento en la detección de la vía (VIIRS 750)

Escrito el 2026-11-25 antes de correr la medición. Lo único corrido antes son exploraciones de las entradas
(`explorar.py`, `explorar_halo.py`, `explorar_matriz.py`, `explorar_pesos.py`, con su salida al lado), que no miden
ningún contraste mínimo. Lo que mostraron y condiciona el diseño:

- De las 10 escenas, sólo Nevados de Chillán 2026-10-10 05:54 tiene una anomalía fuerte (5 celdas alertadas, 13,1 MW).
  Las otras ocho con alerta tienen 1 o 2 celdas de 0,15 a 1,2 MW en el cráter, y Llaima no tiene ninguna
  (`explorar_salida.txt`). Todas son de noche (dayflag 0), con reflejo solar sobre 113 grados.
- En Chillán el pase 1 sube el umbral sensible de NTI de unos 0,0057 a 0,0158 (sd_nti 0,00317), y el pase 2, sin las
  celdas que alertaron, lo baja de nuevo a 0,0057. Como la máscara final es la unión de los dos pases, lo que importa es
  el pase 2.
- No hay halo tibio en la temperatura de brillo M13 alrededor de ninguna anomalía: el perfil radial de la mediana es
  negativo de 0,5 a 10 km (la cumbre es más fría que el anillo de 8 a 12 km), salvo Chaitén
  (`explorar_halo_salida.txt`).
- La interpolación lineal de producción es lineal en los valores con la triangulación fija: la matriz de interpolación
  armada con la misma triangulación que `griddata` reproduce la grilla de producción a 1,8e-15 y el impulso de
  `remuestrear_grilla` a 5,6e-17 (`explorar_matriz.py`).

## 1. Detector y armado de la escena

Detector: `detectar_mirova` de `pipeline/mirova_v750_codigo.py` de origin/main en `b7626b03c`, copiado con
`git archive` a `main_snapshot/` y llamado sin modificar, con perfil `mirova_equivalent` (zona A del laboratorio
apagada). La escena se arma como `calcular_vrp_granulo`: grilla de MIROVA del volcán (`grilla_del_volcan`), recorte de
45 km de su centro, `remuestrear_grilla`, caja `caja_roi` con la ROI de `grillas_mirova.yaml` (crater en Cordón Caulle,
sens en Tupungatito, def en el resto), cráter con `get_detection_anchor`, dayflag y reflejo solar con los cuatro ángulos
del píxel más cercano al centro (guardados en `resultados.json` del mismo run S158).

## 2. Cómo se inserta el foco

- **Dónde**: en el gránulo, antes de remuestrear, en UN píxel del recorte (un foco sub-píxel). Es lo físico: el calor
  de un foco chico cae en un píxel del barrido y la interpolación lineal lo reparte en las celdas vecinas. Por
  linealidad, la grilla con el foco es la grilla base más delta por la columna del píxel en la matriz de interpolación
  (control C2 abajo).
- **Píxel**: el píxel del recorte más cercano al punto objetivo entre los que tienen peso máximo sobre alguna celda de
  0,3 o más. POR QUÉ: el 59 % de los píxeles del recorte de 45 km queda fuera del cuadro de 50 km y no llega a ninguna
  celda; dentro del cuadro, un píxel de peso muy bajo daría «no se ve» en los dos brazos por la interpolación y no por
  el enmascaramiento. Se anota la distancia real del píxel al punto objetivo.
- **Radiancia, físicamente coherente**: píxel mezcla con una fracción f a temperatura T_hot y el resto con la radiancia
  que ya tenía: L_b = (1 - f) L_b,pix + f B_b(T_hot), en M13 (4,05 um) y M15 (10,763 um), con la Planck del .m
  (`temperatura_a_radiancia`). T_hot principal 1000 K (lava o conducto incandescente), secundaria 600 K (suelo muy
  caliente, fumarola de alta temperatura).
- **Escala del contraste**: el barrido va en potencia equivalente del foco, VRP_eq = 1,97e7 x 0,5625 km2 x
  (L13 nuevo - L13 del píxel) / 1e6 MW, la misma fórmula y coeficiente con que la vía convierte exceso de M13 en MW
  (`COEF_VRP_V750`). f sale de VRP_eq; se anota f y la BT M13 del píxel. Si la BT M13 del píxel pasa 634 K (techo de
  M13) se marca, no se descarta.
- **Barrido**: 25 valores de VRP_eq en escala logarítmica de 0,02 a 200 MW; desde el primer acierto, 7 bisecciones en
  logaritmo entre el último fallo y el primer acierto. Resultado: el VRP_eq mínimo que alerta. Si después del primer
  acierto algún valor mayor de la grilla gruesa no alerta, se marca «no monótono». Si no alerta a 200 MW: «> 200».

## 3. Criterio de alerta del foco

Huella del foco: las celdas con peso de M13 de 0,25 o más. El foco alerta si al menos una celda de la huella queda en
la máscara de `detectar_mirova`. Un punto se descarta en los dos brazos («solapado») si alguna celda de la huella o
una de sus 8 vecinas ya está alertada sin foco en cualquiera de los brazos, o si la huella toca el borde de la grilla
(caja NaN) o una celda sin dato.

## 4. Distancias y direcciones

Origen: la celda alertada de mayor M13 de la anomalía fuerte (en el trasplante, la celda del cráter, donde se pone el
pico). Distancias 2, 5, 10 y 20 km; 8 direcciones por distancia (0, 45, ..., 315 grados desde el norte). Los puntos
que caen fuera del cuadro o sobre el borde se descartan y se cuentan.

## 5. Brazos

**Serie R (escenas reales, 10).**
- R-con: la escena tal cual.
- R-sin: la escena con su anomalía quitada: las celdas alertadas sin foco, dilatadas con el halo del .m (3, 5 o 7
  celdas según cuántas alertaron, `vrp_mirova` l. 68-74), pasan a NaN y se rellenan con `_fillmissing2_lineal` de
  producción, en M13 y en M15 por separado. Es el fondo con que la vía mide el VRP. POR QUÉ este brazo y no escenas sin
  calor: misma pasada, misma nube, mismo ángulo y mismo terreno; sólo cambia la anomalía. Se verifica que R-sin no
  alerte dentro de la zona quitada.
- R-sin9 (sensibilidad): lo mismo con un halo de 9 celdas (3 km). Como el perfil radial no muestra halo tibio, se espera
  igual a R-sin; si difiere, se dice.
- Llaima no tiene alerta: sus dos brazos son iguales por construcción y es la escena del control C3.

**Serie T (trasplante de una anomalía real).** Como sólo Chillán es fuerte, su anomalía real (exceso de M13 y de M15
sobre el fondo de R-sin, en las celdas quitadas) se suma a la grilla de las otras 9 escenas con el pico en la celda del
cráter, a escala 1, 3 y 10 (13, unos 40 y unos 130 MW). Escalar el exceso de M13 y M15 por el mismo factor es
multiplicar el área caliente a la misma temperatura: físicamente coherente. No es un halo inventado: es el de Chillán.
- T-sin: la escena destino tal cual (con su anomalía chica del cráter, si la tiene).
- T-con-1, T-con-3, T-con-10: más el trasplante.

**Control positivo del enmascaramiento (C4).** En las 10 escenas, ruido blanco gaussiano (semilla 20261125) sumado a
M13 de la grilla con la amplitud que en NTI vale sqrt(3) veces sd_nti del pase 1 de la escena, o sea cerca del doble de
sd. Brazo N-con contra la escena tal cual.

## 6. Qué se reporta

Por escena, serie, brazo y distancia: el VRP_eq mínimo por dirección, su mediana, la razón con-sobre-sin por dirección
(mediana y máxima), cuántas direcciones válidas, la zona de la caja de la huella (0, 1 o 2) y los umbrales de los dos
pases (u_nti y u_eti, zonas 1 y 2) en cada brazo sin foco. El cenit del sensor de cada escena va en la tabla.

## 7. Qué llamaría enmascaramiento relevante (fijado antes)

Razón por dirección r = VRP_eq mínimo con la anomalía / sin ella, con T_hot 1000 K.
- **Relevante**: mediana de r de 1,5 o más en alguna distancia de 5 km o más, en una escena real o en el trasplante a
  escala 1 o 3 (las magnitudes que hoy tienen los volcanes chilenos); o que en el 25 % o más de las direcciones válidas
  de una distancia de 5 km o más un foco que sin la anomalía alerta con 1 MW o menos pase a necesitar más de 1 MW.
- **Menor**: mediana de r entre 1,1 y 1,5.
- **Nulo**: mediana de r bajo 1,1.
La escala 10 se reporta como «evento grande» con el mismo criterio pero por separado. A 2 km se reporta igual, pero
2 km es el borde del cráter y no «otra parte del edificio».

## 8. Controles y cuándo pasan

- **C1 identidad**: sin foco, la máscara del arnés es la de `calcular_vrp_granulo` de producción llamado con el
  recorte (mismas celdas alertadas y mismo VRP a 3 decimales) en las 10 escenas.
- **C2 linealidad**: en 20 casos al azar (semilla 7) en el umbral (el VRP_eq mínimo hallado y uno 5 % menor), la
  máscara con el foco insertado en el gránulo y `remuestrear_grilla` de producción es la misma que con la matriz.
  Pasa con 40 de 40.
- **C3 el instrumento puede dar distinto de cero**: en Llaima (sin calor), con 0 MW ningún punto alerta (32 de 32) y con
  200 MW alertan 30 o más de los válidos.
- **C4 el instrumento puede ver enmascaramiento**: con el ruido que duplica sd, la mediana de r en la zona sensible es
  1,3 o más. Si no pasa, un nulo en el resultado no se puede creer.
