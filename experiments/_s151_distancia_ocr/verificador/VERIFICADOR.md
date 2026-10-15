# Verificador con contexto limpio: distancia por serie de tiempo de Dist.png

2026-10-15. Sólo lectura. Todo lo mío vive en `C:\Users\nmend\AppData\Local\Temp\claude\verifdist\`.
Lecturas de las 449 PNG con el lector del estudio sin cambios (`scripts\leer_todo.py` → `lecturas.pkl`, 0 sin geometría).
Documento escrito por partes (plazo duro); lo que no alcancé va SIN VERIFICAR.

## 1. Control del §4

Script: `C:\Users\nmend\AppData\Local\Temp\claude\verifdist\scripts\v2_control.py` (reimplementación vectorizada con las
mismas reglas del estudio), salida `C:\Users\nmend\AppData\Local\Temp\claude\verifdist\v2\control_salida.txt`,
tabla `...\verifdist\v2\control_variantes.csv`. Variantes:
A = estudio; B = calado del eje de tiempo SIN las pasadas conocidas de la noche de control (±0,5 d), o sea sin
circularidad; C = imagen más reciente de 1 a 25 d (la que recomienda el §7 y usa el §5, no la que se controló);
D = B + C.

| variante | dibujadas | «único» mediana / p90 / >2 km | intervalo contiene | decididas | erradas |
|---|---|---|---|---|---|
| A (estudio) | 1.347/1.368 (98,5 %) | 0,08 / 0,64 / 36 (5,0 %) | 612/627 (97,6 %) | 1.246/1.549 (80,4 %) | 56 (4,5 %) |
| B sin la noche en el calado | 1.328 (97,1 %) | 0,08 / 0,64 / 36 | 609/625 (97,4 %) | 1.240 (80,1 %) | 56 (4,5 %) |
| C imagen más reciente | 1.334 (97,5 %) | 0,08 / 0,60 / 35 | 622/638 (97,5 %) | 1.246 (80,4 %) | 56 (4,5 %) |
| D = B + C | 1.286 (94,0 %) | 0,08 / 0,60 / 35 | 618/634 (97,5 %) | 1.236 (79,8 %) | 56 (4,5 %) |

- **CONFIRMADO** los cuatro números del §4 (variante A reproduce exacto).
- **Circularidad del calado: medida, no cambia el veredicto.** Sacar del calado la noche evaluada baja el «dibujadas»
  1,4 puntos (98,5 a 97,1 %), y 4,5 puntos con la imagen más reciente (94,0 %), pero el error de la decisión no se
  mueve. El calado se sostiene con las otras ~25 pasadas de la imagen.
- **Elección de imagen: el control del §4 usó la PRIMERA imagen 1 a 25 d después (mediana 3,1 d); el §7 recomienda la
  MÁS RECIENTE (mediana 22,5 d).** Medida la recomendada (C), da lo mismo. CONFIRMADO que el método recomendado tiene
  el error declarado, aunque el §4 no lo midió así.
- **Hallazgo propio, importante: el 4,5 % no mide la población a la que se aplica.** Entre las pasadas ALERTA del control
  decididas (783), **ninguna es lejana** (la tabla llama ALERTA sólo a lo que cae bajo el límite): todas las «lejos»
  del control son FALSO_POSITIVO. Para ALERTA el único error posible es cerca→lejos, y vale 38 de 783 (4,9 %). La
  capacidad de decir «lejos» bien (o «cerca» mal) se midió sólo sobre FALSO_POSITIVO, la mayoría a más de 25 km. Las
  filas a las que se aplicará son ALERTA del OCR cuya distancia real no se conoce: la tasa de «cerca falso» sobre una
  alerta lejana a menos de 25 km no tiene muestra propia (las 18 lejos→cerca del §4 son 17 a más de 25 km).

## 2. Las 451 distancias medidas por el OCR contra la serie de tiempo

Script `C:\Users\nmend\AppData\Local\Temp\claude\verifdist\scripts\v2_ocr.py` → `...\verifdist\v2\ocr_salida.txt` y
`...\verifdist\v2\ocr_vs_serie.csv`. Calado SÓLO con pasadas de la tabla y eliminación SÓLO con pasadas de la tabla (ninguna
distancia OCR entra al instrumento). Sólo VIIRS 375 (426 de 451; las 21 VIIRS 750 y 4 MODIS no tienen imagen archivada en la
muestra). Árbitro de tres vías: `...\verifdist\scripts\v2_arbitro.py` → `...\verifdist\v2\arbitro_salida.txt`. Cambios de
lado: `...\verifdist\scripts\v2_cambios.py` → `...\verifdist\v2\cambios_salida.txt`. Cifras con la imagen más reciente
(variante C); con la primera imagen (A) son casi iguales (ver salida).

| tramo | filas (V375 con imagen) | discrepancia OCR contra serie: mediana / p90 | > 2 km | OCR y serie a distinto lado del límite | > 2 km con firma «otra pasada» |
|---|---|---|---|---|---|
| antes del 06-11 | 50 (36) | 0,07 / 0,54 | 1 de 22 (4,5 %) | 0 de 19 | 1 |
| 06-11 a 06-12 | 1 (1) | 0,06 | 0 de 1 | 0 de 1 | 0 |
| 06-13 a 08-05 | 168 (160) | 0,12 / 8,49 | 36 de 152 (23,7 %) | 23 de 129 | 23 |
| 08-06 a 10-08 | 220 (209) | 0,13 / 8,52 | 51 de 207 (24,6 %) | 25 de 188 | 24 |
| desde 10-09 | 12 (7) | 0,00 / 0,23 | 0 de 7 | 0 de 5 | 0 |

(«discrepancia» = |OCR − lectura| en el caso «único», y distancia de la cifra OCR al intervalo en «solapado/ambiguo»;
«firma otra pasada» = la cifra OCR coincide a ±0,3 km con una pasada de la tabla 0 a 1,5 d posterior, o con un marcador de
una columna posterior.)

Lectura:
- **Antes del 06-13 y desde el 10-09 hay acuerdo** (casi todo son FALSO_POSITIVO con la distancia copiada de la tabla, lo
  que confirma la nota del inventario y valida el lector: 34 duplicados con la tabla, error OCR-tabla 0,00).
- **Del 06-13 al 10-08, una de cada cuatro distancias del OCR discrepa más de 2 km de la serie**, y 48 caen al otro lado
  del límite cerca/lejos (casi todas: OCR «cerca», serie «lejos»).
- **¿Quién tiene razón? El árbitro dice la serie.** 218 filas OCR tienen la misma pasada en la tabla (±3 min). En los
  tramos 3 y 4, el OCR discrepa de la tabla > 2 km en 8 + 17 = 25 filas; la serie, en 3 + 4 = 7. En las 25 donde el OCR
  falla, la serie da la cifra de la tabla. **Hallazgo propio: esas 25 no son «otra pasada»** (0 con firma): son un sesgo
  geométrico del OCR, sobre todo en Puyehue-Cordón Caulle (OCR 3,5 a 3,8 km donde la tabla y la serie dan 7,7 a 8,2) y
  Tupungatito (OCR 1,3 a 2,3 contra 4,9 a 5,2). Ninguna cambia de lado (límites 20 y 7 km), pero el OCR del tramo
  06-13 a 10-08 **no es una referencia de distancia confiable ni siquiera cuando sí midió**.
- **Los 41 cambios de lado en filas «solo OCR»** (sin pasada en la tabla; 14 Lastarria, 10 Isluga, 8 Láscar, 6 Tupungatito):
  39 de 41 llevan la firma «otra pasada». El patrón típico es una columna con dos marcadores, uno a la cifra del OCR
  (que también es la de una pasada de la tabla de esa noche) y otro lejano que nadie explica; la eliminación le asigna al
  OCR el lejano. **PARCIAL**: es lo esperable si el OCR copió la distancia de la pasada de la cabecera (Mirova-v1#20), pero
  no es independiente: en Láscar 1,22 km es la celda del cráter (cuantización, D15), así que dos pasadas de cráter dan dos
  marcadores superpuestos que el lector funde en uno, y la misma columna es compatible con «el OCR acertó y hay una
  pasada lejana que no está en ninguna referencia». La tasa base de esa segunda explicación en el control es 5 % (36 de
  726); acá los cambios son 25 % (41 de 166), así que la mayoría debe ser error del OCR, pero no cuáles. Doce de los 41
  (contadas a mano en `cambios_salida.txt`) no tienen ningún marcador a la cifra del OCR en su columna, y las doce son
  diurnas, 17 a 18 UTC (p. ej. Láscar 2026-09-19 17:30, OCR 1,22, columna [17,07]; Lastarria 2026-06-28, tres filas, columna
  [10,16, 10,70]); ésas contradicen al OCR sin la ambigüedad de la superposición, y el control sí cubre las diurnas: 362 de
  las 1.549 pasadas de control son de 12 a 22 UTC, 247 de 253 dibujadas y 0 errores en 244 decididas
  (`C:\Users\nmend\AppData\Local\Temp\claude\verifdist\v2\diurnas_control.txt`). Esas doce son error del OCR.
- Consecuencia de método: el estudio usa las distancias OCR del 06-13 en adelante como **conocidas** para eliminar
  (`control_dist.py` y `aplicar.py`, `ocr_geo`). Con 24 % de ellas a más de 2 km de lo dibujado, eso puede descontar el
  marcador equivocado. En el control casi no pesa (la tabla domina), pero en las 15 filas de octubre sí entra.

## 3. Las 15 filas sin geometría (§5)

No recorrí `aplicar.py`; leí su salida `C:\Users\nmend\AppData\Local\Temp\claude\distancia_ocr\salidas\sin_geometria_aplicado.csv`.
- **La clase depende de la imagen: CONFIRMADO por el propio estudio** (4 de 15 cambian con la primera imagen; esa corrida
  se sobrescribió y no la reproduje, SIN VERIFICAR el número 4).
- **Fuera del rango controlado.** Las imágenes usadas son del 2026-10-15 a las 13:55 a 14:10 UTC: para las pasadas del 10-14
  y 10-15 la imagen tiene entre 7 h y 1,4 d, mientras que el control sólo midió imágenes de 1 a 25 d (`imagen_para`
  con `min_dias=1`). Con un desfase de dibujo de ~12 h, una imagen de 7 h puede tener la noche aún sin cerrar.
- **Las «conocidas» de esas noches incluyen distancias OCR** (`aplicar.py`, `conocidas_de`), y el §2 muestra que del
  06-13 al 10-08 una de cada cuatro está mal; desde el 10-09 el acuerdo es bueno (7 de 7), así que para octubre el riesgo
  es menor, pero el código no distingue tramos.
- **Villarrica 10-15 06:42 a 21,5 km: SIN VERIFICAR, no se sostiene como dato.** Un solo marcador en la columna, calado de
  8 pareos (el mínimo del lote), imagen 7,5 h posterior (fuera del control) y ninguna otra pasada de la noche con VRP > 0
  para anclar. Es compatible con «la pasada estaba a 21,5 km», pero también con que el marcador sea de una pasada vecina
  mal ubicada por el calado. No comprobé la imagen a ojo.
- Chillán: los intervalos (0,41 a 1,49; 1,06 a 2,44) caen bajo 5 km con holgura; «cerca» es robusto a la imagen salvo
  10-11 06:12 (0,54 a 23,51), que ya va como indecidible.

## 4. VIIRS 750 y MODIS

**No se pueden controlar con lo que hay en disco.** La muestra archivada (`datos\dist375\muestra_VIIRS375.csv`) es sólo
VIIRS 375; de VIIRS 750 hay sólo las PNG de `datos\dist_sg` (las de las filas sin geometría). El mismo control sería
posible (la tabla trae VIIRS 750 y MODIS con distancia y `index_png.csv` lista sus `Dist.png`), bajando una muestra por la
API, pero no lo hice: SIN VERIFICAR. Además en esos sensores el píxel es 2 a 3 veces más grande y la cuantización de la
distancia es más gruesa, así que no se debe extrapolar el 4,5 %.

## 5. Veredicto por afirmación

| afirmación | veredicto |
|---|---|
| 98,5 % dibujadas | CONFIRMADO (97,1 % sin circularidad; 94,0 % con la imagen recomendada y sin circularidad) |
| «único»: mediana 0,08, p90 0,64 | CONFIRMADO, robusto a calado e imagen |
| 97,6 % dentro del intervalo | CONFIRMADO (97,4 a 97,5 % en las variantes) |
| 4,5 % de error, 80,4 % decidido | CONFIRMADO numéricamente; PARCIAL como estimación del error de aplicación: entre ALERTA no hay ninguna lejana en el control, así que «lejos» sólo se midió sobre FALSO_POSITIVO |
| el desfase circular es chico | CONFIRMADO (medido: 0 cambio en errores de decisión) |
| el §7 «imagen más reciente» tiene ese error | CONFIRMADO por mí (el §4 no lo midió así) |
| 15 filas (§5) | PARCIAL: dependen de la imagen, usan imágenes < 1 d fuera del control; Villarrica 21,5 km SIN VERIFICAR |
| aplicación hacia atrás (163/48/34/35) | SIN VERIFICAR (no la recorrí) |
| VIIRS 750 y MODIS | SIN VERIFICAR (el estudio ya lo decía) |

## 6. Veredicto global

**Se puede implementar `Distancia_aprox_km` con rango, con cambios.** El instrumento es bueno cuando sabe de qué pasada es
cada marcador, y es mejor que el OCR: en las 218 pasadas OCR que también están en la tabla, el OCR falla > 2 km en 25 y la
serie en 7, y en las 25 la serie da la cifra de la tabla. Cambios exigidos:
1. **No usar distancias OCR como «conocidas» para eliminar** fuera del tramo desde el 2026-10-09 (o no usarlas nunca);
   eliminar sólo con la tabla. Del 06-13 al 10-08 una de cada cuatro discrepa más de 2 km de lo dibujado.
2. **Imagen con al menos 1 día de edad** respecto de la pasada (y a lo sumo 25 d). Lo de < 1 d queda «pendiente», no se
   escribe; se recalcula cuando llegue una imagen más vieja.
3. **Guardar el calado** (número de pareos) y no escribir valor si el calado es débil; umbral a fijar contra el control
   (SIN VERIFICAR cuál, el de Villarrica, 8, es el mínimo del lote del §5).
4. **Rotular el error esperado por población**: para filas ALERTA el error medido es «cerca leído como lejos» 4,9 %; el
   error «lejos leído como cerca» por debajo de 25 km no tiene muestra.
5. **Sólo VIIRS 375** hasta que exista un control propio de VIIRS 750 y MODIS.
6. **Abrir también la columna para las 451 que sí tienen `Distancia_km`**, no sólo para las vacías o en 0: del 06-13 al
   10-08 el OCR medido está mal en ~24 % (> 2 km), con dos mecanismos (pasada de otra cabecera, y un sesgo geométrico en
   PCC y Tupungatito que no es «otra pasada»). Al menos marcar la discrepancia; `Distancia_km` se deja intacta como pide
   el estudio.
