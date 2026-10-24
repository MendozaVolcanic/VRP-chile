# V750-C (S162): qué pieza del código de MIROVA calla las cumbres tibias de un píxel, y qué pieza da la magnitud

- Hora del servidor: 2026-10-24 15:44 UTC. Commit de partida `b05d60527` (rama `claude/s162-viirs750-f63ef4`).
  Modelo: Opus 5.5. Sesión hija de S162 (loop VIIRS 750, `tasks/LOOP_VIIRS750.md`).
- Sólo lectura y sólo local: sin red, sin GitHub Actions, sin tocar `pipeline/`, `data/` ni `frontend/`. Programa:
  `docs/superpowers/specs/2026-10-24-programa-replica-por-sensor.md` §3, V750-C.
- Insumos: las 510 grillas GEO lineales de 67 × 67 del frente N de S159 (391 del lote, run 39682867040, y 119 del
  censo, run 39693661527), leídas en su lugar en `D:\vrp-trabajo\temporales\s159_n\`; resultados y objetivos de N y el
  port de R2, extraídos de `origin/s159-pruebas` (`812624cc6`) con `extraer_insumos.sh`.
- Scripts: `oraculo_ablacion.py` (el oráculo con piezas intercambiables) y `ablacion.py` → `ablacion_salida.txt` y
  `ablacion_por_pasada.csv`. Reproducir: `bash extraer_insumos.sh <carpeta>` y después
  `python ablacion.py --insumos <carpeta> --grillas D:\vrp-trabajo\temporales\s159_n` (unos 5 minutos).
- **Sin verificador todavía.** Ventana: VIIRS 750 nocturno, 2026-04-01 a 2026-10-21 sin el 18 ni el 19 de octubre
  (la de N); el 12-oct sin las pasadas que N dejó SIN DATO.

## En una pantalla

1. **Lo que calla las cumbres tibias es el remuestreo lineal a la grilla fija** (SOSPECHA FUERTE: se midió con
   sustitutos, no con el barrido nativo). En las 60 cumbres del censo que K deja en 0,0 MW en noches en que MIROVA no
   vio nada, el código de MIROVA en su grilla detecta 1. Cambiando sus piezas por las de K una a la vez, ninguna
   recupera más de 5; todas las de K juntas, sobre la misma grilla, 8. Con remuestreo de vecino más cercano (que
   conserva el valor nativo del píxel en vez de promediarlo) detecta 23, las 23 en el píxel de K. Y la interpolación
   lineal reduce a la mitad el exceso de ese píxel sobre el fondo del código (mediana 0,536 de su exceso nativo).
2. **No hay un paquete «sin remuestreo» que calle lo que MIROVA calla.** El sustituto más cercano al barrido nativo
   (vecino más cercano) publica 25 negativos limpios del lote (114 ponderados) contra 4 del código con interpolación
   lineal. El remuestreo lineal (D17) es condición del paquete **también para la detección**, no sólo para la magnitud.
3. **La magnitud la da el fondo del código**: con el fondo de anillo de K, el mismo código, en la misma grilla y con
   los mismos píxeles, baja de 0,999 a 0,458 de MIROVA (K publica 0,510). Sin el halo dilatado, 0,935 (1 píxel 0,846).
   El recorte a cero no pesa (cambia 1 pasada de 510).
4. **No deciden**: la regresión recalculada en el segundo pase (actúa en 165 pasadas, no cambia ninguna detección),
   el recorte, K1 y los mínimos de K (−4 alertas, +1 negativo), la media de 8 vecinos (+4 cumbres, −2 alertas) y la
   compuerta de 3 K en el primer pase (0 alertas perdidas; baja la razón de los cúmulos de varios píxeles).
5. **La caja sigue siendo la pieza de riesgo para las protegidas**: con la caja por defecto el código detecta 71 de
   78; con la sensible de 21 × 21 o con el círculo `inner_radius_km` como zona sensible, 78 de 78 (insumo de V750-B).

## Qué pasa, como geólogo

De noche, en la cumbre de Isluga, Láscar, Tupungatito o Planchón-Peteroa aparece a veces un píxel de 750 m algo más
tibio que sus vecinos: puede ser una fumarola, roca expuesta sin nieve o ruido del sensor. Nuestro detector lo mira en
la geometría original del gránulo y lo encuentra; después lo deja en 0,0 MW porque es más frío que el anillo de 5 a 25
km. MIROVA, antes de detectar, interpola el gránulo a una grilla fija de 750 m. Como las celdas de esa grilla no caen
justo sobre los píxeles del satélite, cada celda es una mezcla lineal de cuatro píxeles vecinos: un píxel tibio aislado
queda repartido y su contraste con los vecinos baja a la mitad. A esa altura ya no pasa los umbrales contextuales, y
MIROVA calla. Que la detección dependa de dónde cae la celda se ve directamente: corriendo la grilla media celda (la
de R2) el mismo código detecta 13 de las 60 en vez de 1.

Lo que esto significa para la réplica: si queremos callar donde MIROVA calla, hay que ver el gránulo como lo ve
MIROVA, interpolado a su grilla. Un detector que mira el píxel nativo (como K, o como el código sin remuestrear) va a
encender esas cumbres tibias.

## Brazos y resultados (de `ablacion_salida.txt`)

Cada brazo es el código del `.m` (port de R2, validado contra Octave en S159 O1) con una pieza reemplazada por la de K.
`todoK` junta todas las piezas de K que existen en la grilla (8 vecinos, regresión del primer pase, K1 y mínimos,
compuerta en el primer pase, círculo sensible, recorte, fondo de anillo); **no es K**: es el esqueleto del `.m` con
piezas de K, sin el resto del algoritmo de K. Las cuatro filas del final son variantes de remuestreo que N corrió en el
runner, leídas de sus resultados con la posición de cada píxel.

| brazo | censo 60: en el píxel de K | lote 6 neg: en el píxel de K | lote 48 donde MIROVA alertó: en el píxel de K | alertas que deciden publicadas (de 181) | protegidas (de 78) | negativos del lote publicados, crudo (ponderado) | razón brazo/MIROVA, mediana [q1, q3] |
|---|---|---|---|---|---|---|---|
| O (el `.m`) | 1 | 0 | 33 | 145 | 71 | 4 (4,0) | 0,999 [0,978; 1,007] |
| 8 vecinos | 5 | 0 | 32 | 143 | 71 | 6 (6,0) | 1,000 [0,978; 1,010] |
| regresión del pase 1 | 1 | 0 | 33 | 145 | 71 | 4 (4,0) | 0,999 [0,978; 1,007] |
| K1 −0,8, mínimo 0,010 | 1 | 0 | 33 | 141 | 70 | 5 (5,0) | 0,999 [0,976; 1,007] |
| compuerta en los dos pases | 0 | 0 | 0 | 62 | 55 | 1 (1,0) | 0,783 [0,585; 0,965] |
| compuerta en el pase 1 (como K) | 1 | 0 | 33 | 145 | 71 | 4 (4,0) | 0,996 [0,928; 1,007] |
| caja sensible 21 × 21 | 4 | 0 | 44 | 175 | 78 | 8 (8,0) | 0,999 [0,973; 1,009] |
| círculo `inner_radius_km` sensible | 4 | 0 | 44 | 175 | 78 | 12 (12,0) | 0,999 [0,976; 1,011] |
| recorte a cero | 1 | 0 | 33 | 145 | 71 | 4 (4,0) | 0,999 [0,978; 1,007] |
| fondo de anillo | 1 (0 publica) | 0 | 33 (0 publica) | 89 | 65 | 2 (2,0) | 0,458 [0,307; 0,698] |
| fondo sin halo | 1 | 0 | 33 | 145 | 71 | 4 (4,0) | 0,935 [0,784; 1,021] |
| todoK | 8 (1 publica) | 0 | 43 (0 publica) | 106 | 73 | 13 (37,8) | 0,463 [0,267; 0,703] |
| todoK sin compuerta, fondo del `.m` | 8 | 0 | 43 | 169 | 77 | 18 (42,8) | 1,001 [0,976; 1,018] |
| vecino más cercano (runner) | 23 | 4 | 31 | 133 | 71 | 25 (114,3) | 1,226 [0,951; 1,454] |
| cúbico (runner) | 7 | 2 | 30 | 136 | 71 | 11 (50,7) | 1,206 [1,115; 1,286] |
| grilla R2, lineal (runner) | 13 | 3 | 19 | 113 | 71 | 15 (84,5) | 1,000 [0,868; 1,108] |
| grilla R2, vecino más cercano (runner) | 26 | 4 | 30 | 129 | 70 | 23 (122,3) | 1,238 [0,937; 1,512] |

«En el píxel de K»: alguna celda alertada a una celda o menos de la que contiene el centroide del cúmulo de K. «Publica»:
el predicado de N (al menos un píxel, VRP mayor que 0 y el píxel más radiante a no más de `inner_radius_km` del centro).

Medidas en el entorno del píxel de K (`ablacion_salida.txt`, bloques `--`):

| grupo | margen del pase 1 del `.m` (1 = umbral), mediana [q1, q3] | radiancia M13 de la grilla / nativa | exceso sobre el fondo del código, grilla / nativo |
|---|---|---|---|
| censo 60 (MIROVA RUTINA) | 0,534 [0,229; 0,795] | 0,918 | 0,536 [0,401; 0,689] |
| lote, 6 negativos | 0,788 [0,653; 0,908] | 0,921 | 0,504 [0,414; 0,610] |
| lote, 48 donde MIROVA alertó | 1,101 [0,402; 1,322] | 0,969 | 0,780 [0,545; 0,948] |

La radiancia nativa y su fondo son los de N (`F_L_hot_pc`, `F_L_bk_pc`: el fondo del código aplicado en la geometría
del gránulo, `probe_n.py:121-136`). El exceso de la grilla se mide forzando la alerta en la celda más radiante del
entorno 3 × 3 con el mismo fondo del código. En los 60 el remuestreo conserva el 92 % de la radiancia pero sólo el 54 %
del exceso; en las alertas de MIROVA conserva el 78 %. La señal que sobrevive al remuestreo separa lo que MIROVA alertó
de lo que calló.

Por volcán, las 23 que el vecino más cercano recupera: Isluga 14 de 22, Láscar 6 de 10, Planchón-Peteroa 3 de 6,
Tupungatito **0 de 17**, Cordón Caulle 0 de 4, Lastarria 0 de 1. En Tupungatito ni siquiera el valor nativo
remuestreado pasa: ahí el silencio no es sólo el promedio, y queda SIN ATRIBUIR (puede ser la geometría nativa misma,
la caja o la nieve, A69).

## Hallazgos, de mayor a menor gravedad

### V750C-1. El remuestreo lineal calla las cumbres tibias de un píxel; D17 es condición del paquete también para la detección

- SCRIPT:SALIDA: `ablacion.py` → `ablacion_salida.txt`, bloques del censo y del lote, y la tabla de alertas.
- QUÉ PASA: el promedio lineal de la grilla reparte el exceso de un píxel aislado (54 % en mediana) y lo deja bajo el
  umbral contextual (margen 0,53). Ninguna otra pieza del `.m` explica el silencio (máximo 5 de 60 con una pieza, 8 con
  todas las de K). Las variantes que conservan el valor nativo lo recuperan (vecino más cercano 23, en el píxel de K) y
  el desplazamiento de media celda cambia el resultado (13).
- CÓMO SE VE EN EL DASHBOARD: invisible hoy (las cumbres quedan en 0,0 MW). Decide el paquete de la ola 3: un detector
  sin remuestreo encendería esas cumbres apenas el fondo dejara de recortarlas (es lo que vio F en N).
- CONFIANZA: SOSPECHA FUERTE. Las dos mediciones que la sostienen son sustitutos: (a) el vecino más cercano es otra
  grilla (duplica o salta píxeles nativos), no el barrido nativo, y la diferencia entre 1 y 23 puede deberse al
  interpolador y no a la falta de remuestreo; (b) el exceso nativo usa el fondo del código en la geometría del gránulo
  con la máscara de K, no con la del código. Lo cierra el probe de ventana nativa (abajo).
- GRAVEDAD: 4.

### V750C-2. La magnitud de MIROVA la da el fondo local del código, no el recorte ni la detección

- SCRIPT:SALIDA: `ablacion_salida.txt`, tabla de alertas y razón por número de píxeles.
- QUÉ PASA: con los mismos píxeles alertados, el fondo de anillo (la mediana de 5 a 25 km, como K) da 0,458 de MIROVA,
  y el fondo del código 0,999. El halo dilatado alrededor del hueco pesa en los cúmulos de 1 píxel (0,846 sin halo
  contra 0,996). El recorte a cero cambia 1 pasada de 510. Esto apoya en la grilla lo que S158 vio en Etna (la brecha es
  el fondo) y lo que N midió con F sobre la geometría nativa (0,990, pero con cuartiles 0,70 a 1,29: el remuestreo da la
  precisión pasada a pasada).
- CONFIANZA: CONFIRMADO en la grilla (un solo instrumento, controles en verde).
- GRAVEDAD: 3.

### V750C-3. Cinco piezas del `.m` no deciden en esta población

- Regresión recalculada en el segundo pase: el coeficiente cambia en las 165 pasadas que tienen excluidos, el contraste
  ETI se mueve como mucho 0,0004 y ninguna detección cambia (control 3b).
- Recorte: 1 pasada. K1 −0,8 y mínimo 0,010: 32 máscaras, −4 alertas, +1 negativo. 8 vecinos: 21 máscaras, +4 cumbres,
  −2 alertas. Compuerta en el primer pase, como K: 25 máscaras, 0 alertas perdidas, razón 0,996 con cuartil bajo 0,928
  (le quita píxeles tibios a los cúmulos de varios píxeles). Puesta en los dos pases publica 62 alertas de 181 contra 145 del `.m`: no es la
  compuerta de K, se informa para que nadie la use como tal.
- CONFIANZA: CONFIRMADO en esta población. GRAVEDAD: 2 (achica la lista de piezas que el paquete tiene que traer
  exactas; no autoriza a cambiarlas: el paquete sigue siendo el `.m` entero).

### V750C-4. La caja es la pieza de riesgo para las protegidas (insumo de V750-B)

- Caja por defecto 71 de 78 protegidas; sensible 21 × 21 y círculo `inner_radius_km` sensible, 78 de 78. El círculo
  publica 12 negativos del lote contra 8 de la sensible (crudo, sin ponderar). Las 48 cumbres donde MIROVA alertó: 33
  con la caja por defecto, 44 con cualquiera de las dos sensibles.
- CONFIANZA: CONFIRMADO en la muestra de N (no es censo). GRAVEDAD: 3.

### V750C-5. «Las 55 cumbres que K deja en 0 MW» no son todas silencio de MIROVA

- De las 55 del lote, en 48 MIROVA alertó (`pos_nopub`), 6 son negativos limpios y 1 está fuera de ventana. La pregunta
  «qué las calla» vale para los 66 negativos (60 del censo y 6 del lote); en las 48 el código detecta 33 a 44 según la
  caja. GRAVEDAD: 1 (de redacción del programa, §3).

## Controles (leídos antes de los resultados)

| pregunta | control | resultado |
|---|---|---|
| ¿el módulo es el `.m`? | identidad contra el port de R2 (máscara y VRP) | 510 de 510 |
| ¿las grillas son las del runner? | O = `geo_linear` de los resultados de N (npix y VRP a 1e-6) | 510 de 510 |
| ¿cada reemplazo actúa? | pasadas con máscara o VRP distinto de O | todos los brazos > 0, menos la regresión (0), que actúa sobre el coeficiente (3b) |
| ¿el instrumento puede dar distinto de cero en las cumbres? | brazos que detectan en el píxel de K | sí: 4 a 26 según el brazo |
| ¿podía el «en el píxel de K» engañar? | se informa al lado «con algún píxel» | coinciden en todos los brazos del censo salvo los dos todoK (8 en el píxel de K, 9 con algún píxel); fondo de anillo y todoK detectan pero casi no publican, porque su VRP queda ≤ 0 |

## Lo que no se midió, y el probe que lo cierra

- **El barrido nativo.** Las grillas de N traen sólo la GEO lineal (`probe_n.py:383`), no la ventana nativa; la
  SOSPECHA del programa de que la trajeran queda refutada. ¿Cambia el veredicto sin ella? La parte práctica no: D17 ya
  era obligatorio por la magnitud (N-2), y este informe agrega que la detección lo pide también. La atribución fina sí
  depende: si con el barrido nativo el código detectara las 60, el silencio sería del remuestreo; si no, habría una
  pieza más (la geometría nativa, la caja, Tupungatito). **Probe pedido a la coordinadora para el despacho de la fase 1**
  (sólo lectura): guardar, para las 66 negativas, las 48 alertas de cumbre y una muestra de negativos sin píxel de K,
  la ventana nativa del gránulo (lat, lon, M13, M15 a 45 km, float32) y correr el `.m` sobre la geometría nativa como
  brazo. Diseño en el pre-registro de V750-B (mismo run).
- Tupungatito (0 de 17 aun con vecino más cercano): SIN ATRIBUIR.
- Diurno: fuera (V750-E). VIIRS 375 y MODIS: fuera.

## VERIFICADO LIMPIO

- El módulo con las piezas del `.m` es el port de R2 en 510 de 510 grillas (vara: `mirova_v750_r2.detectar` y `vrp`).
- Las grillas de disco son las que usó el runner (vara: `geo_linear` de los resultados de N, 510 de 510).
- La regresión del segundo pase no decide (vara: coeficiente del pase 1 contra el del pase 2, 165 de 165 distintos).

## Candidatas para BEYOND_MIROVA_EXTENSIONS §12

| qué | por qué podría ser mejor | evidencia | estado |
|---|---|---|---|
| Cumbres tibias de un píxel en la geometría nativa (Isluga, Láscar, Planchón-Peteroa) | El remuestreo de MIROVA las calla por geometría de grilla, no por física; si son fumarolas o roca tibia reales, son categoría b (A54) | V750C-1; validar contra OVDAS y SWIR | hipótesis (amplía la de N) |
