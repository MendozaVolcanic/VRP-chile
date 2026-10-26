# Distancia aproximada para las filas OCR sin distancia (Mirova-v1)

Estudio de sólo lectura, 2026-10-15. Nada se editó en Mirova-v1 ni en VRP-chile. Todo número sale de una salida en
`C:\Users\nmend\AppData\Local\Temp\claude\distancia_ocr\salidas\`; lo que no se comprobó va marcado SIN VERIFICAR.

## 1. Qué pasa físicamente (y en la página de MIROVA)

MIROVA publica, por volcán y sensor, una imagen `Dist.png` («Max Distance»). No es una foto de la pasada: es un
**gráfico de serie de tiempo**. El panel «Last Month» pone, para cada pasada con anomalía, un tallo vertical con un
marcador a la altura de su distancia máxima: círculo rojo bajo el límite, cuadrado negro sobre él. La pasada de la
cabecera («Last Update») lleva una estrella amarilla si la anomalía está activa. El eje y va de 0 a 25 km, y lo que
está más lejos **no se dibuja**. El eje x cubre 35 días, a unos 15,2 px por día, o sea 0,63 px por hora
(`salidas/zoom_chillan_0518.png`, `salidas/villarrica_1015.png`).

Consecuencias:
- La pasada de las 05:00 **sigue dibujada** en las `Dist.png` publicadas después, durante unos 30 días. Su distancia,
  la que calculó MIROVA, está en la imagen.
- Las pasadas de una misma noche (04:30 a 07:00 UTC) caen en la **misma columna**, separadas por menos de 2 px.
  No se distinguen por la hora, sólo por la altura. Si dos pasadas de la noche tienen casi la misma distancia, sus
  marcadores se tapan.
- El OCR de hoy (`scraper_ocr.py`, `ocr_utils.validar_con_estrella_verde`, l. 1130 a 1200) lee sólo la **estrella**,
  que es la pasada de la cabecera. Por eso, cuando la imagen ya es de una pasada posterior, deja la fila sin
  distancia (V31.1).

## 2. Inventario (`scripts/inventario.py` → `salidas/inventario_salida.txt`)

1.076 filas, del 2026-01-20 al 2026-10-15. Distancia medida (> 0): 451. Cero: 610. Vacía: 15 (las 15 son
`ALERTA_SIN_GEOMETRIA_OCR`: 11 VIIRS 375 y 4 VIIRS 750, 3 de ellas diurnas, todas desde el 2026-10-10).

| tramo A119 | cero | medida | vacía |
|---|---|---|---|
| antes del 03-01 | 76 | 2 | 0 |
| 03-01 a 06-10 | 518 | 48 | 0 |
| 06-11 a 06-12 | 8 | 1 | 0 |
| 06-13 a 08-05 | 3 | 168 | 0 |
| 08-06 a 10-08 | 5 | 220 | 0 |
| desde 10-09 | 0 | 12 | 15 |

- Antes del 06-13, **ninguna** `ALERTA_TERMICA_OCR` tiene distancia (583 con 0 fijo). Las 51 medidas de ese período
  son todas `FALSO_POSITIVO_OCR`, y su nota dice que la distancia se copió de `latest.php` al reclasificarlas
  («RECLASIFICADO 2026-06-15»): son distancias de la tabla, no del OCR.
- Desde el 06-13 quedan 8 ceros (7 VIIRS 375 y 1 VIIRS 750). Pueden ser «misma celda que el centro de grilla» (D15),
  no faltas.
- Por sensor: MODIS 35 ceros y 4 medidas; VIIRS 750 67, 21 y 4; VIIRS 375 508, 426 y 11.

## 3. Método: lectura de la columna de la noche en una `Dist.png` posterior

`scripts/dist_png.py` lee el panel: el techo (25 km) y el eje (0 km) de cada imagen, igual que `ocr_utils` V29; las
marcas semanales del eje x; los marcadores (plantillas de anillo y de cuadrado, con la x afinada al tallo), la
estrella y la línea punteada. `scripts/control_dist.py` cala el eje de tiempo **por imagen**: la fecha de la primera
marca semanal (tres candidatos separados por un día) y un desfase horario. Elige el par con más coincidencias con
pasadas conocidas, con la condición de que ningún marcador quede después de la hora en que se escribió el archivo.
El desfase medido es de +0,48 a +0,53 días según el mes: el dibujo pone cada pasada unas 12 h antes de su hora UTC
(`salidas/calibracion_por_imagen.csv`). El desfase se ajusta con unas 25 pasadas por imagen, entre ellas la de
control, así que el sesgo es chico pero existe.

**Eliminación.** Para una pasada P se toman los marcadores de su columna (±0,15 d) y se descuentan los que explican
las otras pasadas de esa noche cuya distancia se conoce (tabla, y OCR con geometría desde el 06-13). Si queda un solo
marcador, ésa es la distancia de P («único»). Si quedan varios, P cae en el intervalo [mín, máx] («ambiguo»). Si no
queda ninguno, P está tapada por un marcador conocido o está a más de 25 km («solapado»).

## 4. Control que podía fallar

Pasadas de la **tabla** VIIRS 375 con VRP > 0 y distancia publicada, leídas en una `Dist.png` archivada de 1 a 25 días
después: muestra de 429 imágenes (una cada 4 días por volcán, `scripts/bajar_dist.py`), ventana del 2026-04-14 al
2026-10-11.

- **MIROVA dibuja todas las pasadas con VRP > 0 hasta 25 km**: 1.347 de 1.368 tienen marcador a su hora y a ±0,6 km
  de su distancia (98,5 %; ALERTA 886 de 898, FALSO_POSITIVO 461 de 470).
- Caso «único»: n = 726. El error contra la tabla tiene **mediana 0,08 km y p90 0,64 km**. Pero 36 (5 %) fallan
  por más de 2 km: el marcador sobrante era de otra pasada de la noche que no está en nuestras referencias.
- Casos «solapado» y «ambiguo»: en 612 de 627 (97,6 %) la distancia real cae dentro del intervalo. El ancho tiene
  mediana 0,54 km, pero el p90 llega a 14,3 km.
- **Las pasadas a más de 25 km** (181 de 1.549, todas `FALSO_POSITIVO`) no se dibujan. En 123 no hay marcador en su
  columna, y en 17 el método las declara «cerca» por error.
- **Decisión cerca o lejos**, con el límite real de cada volcán (Lastarria y Planchón Peteroa 3 km, Copahue 4,
  Tupungatito 7, PCC 20, el resto 5; `scripts/decision.py` → `salidas/decision_salida.txt`): se decide en 1.246 de
  1.549 (80,4 %). De ésas yerra **56 (4,5 %)**: 38 cercanas llamadas lejanas (el marcador sobrante era de otra
  pasada) y 18 lejanas llamadas cercanas (17 de ellas a más de 25 km). «Sin marcador» ocurrió 138 veces, y en 129
  la pasada era lejana: la ausencia de marcador es señal de «más de 25 km».
- El error de posición de la lectura (mediana 0,08 km) es menor que la celda de MIROVA y mucho menor que el radio de
  cumbre más chico (3 km). El riesgo real **no es la precisión, es la atribución**: saber de qué pasada es cada
  marcador.

## 5. Las 15 filas sin geometría (`scripts/aplicar.py` → `salidas/sin_geometria_aplicado.csv`)

Se leyeron en la `Dist.png` archivada más reciente (2026-10-15, alrededor de las 14 UTC):

- **Cerca (11)**: Chillán VIIRS 375 del 10-15 a las 05:00 (22,13 MW; columna entre 0,41 y 1,49 km), las dos de
  Chillán VIIRS 750, las de Chillán del 10-14 a las 18:42 y del 10-10 a las 06:30, PCC 06:42 y 10-14 05:18 (≈7,7 a
  8,1 km, el cráter visto desde el centro de grilla), Isluga 10-14 05:12 y 10-11 06:06, y Planchón Peteroa 10-10.
- **Lejos (1)**: Villarrica 10-15 06:42 (0,23 MW). Es el único marcador de esa noche, a **21,5 km**, y las pasadas
  de la tabla de ese día son todas RUTINA con VRP 0. Comprobado a ojo en `salidas/villarrica_1015.png`; el
  calado de esa imagen es débil (8 coincidencias).
- **Indecidible (1)**: Chillán 10-11 06:12 (columna con 1,22 y 23,51 km).
- **Sin marcador (2)**: Isluga 10-13 18:18 (diurna; probablemente a más de 25 km, SIN VERIFICAR) y Chaitén VIIRS 750
  10-11 (calado nulo, sin dato).
- El resultado **depende de la imagen elegida**. Con la primera imagen posterior, en vez de la más reciente,
  cambiaron 4 clases (primera corrida, sobrescrita).
- VIIRS 750 y MODIS **no tienen control** (sólo se controló VIIRS 375): SIN VERIFICAR.

## 6. Miniatura Latest10NTI (no se corrió)

No hizo falta, porque `Dist.png` sirve. Su píxel mide unos 0,34 km (150 px sobre unos 50 km, según los bordes del
GeoTIFF de Láscar del estudio 1.4), y el estudio 1.4 midió un corrimiento entre el TIF y la miniatura de 0,42 km de
mediana (máximo 0,69). Pero la miniatura muestra luminancia, no los píxeles que MIROVA alertó: el píxel más brillante
no es necesariamente el de la «Max Distance». Su error contra la distancia publicada queda SIN VERIFICAR.

## 7. Recomendación (sólo la propuesta)

1. Sí: una columna aparte, por ejemplo `Distancia_aprox_km` con `Distancia_aprox_min_km`, `_max_km` y `_metodo`,
   **nunca** en `Distancia_km`. Método: la columna de la noche en la `Dist.png` más reciente que todavía la contenga
   (de 1 a 25 días después), descontando las pasadas conocidas de esa noche. Se guarda el intervalo, no un punto,
   salvo en el caso «único».
2. Para decidir cerca o lejos: si todo el intervalo cae bajo el límite menos 0,6 km, «cerca»; si cae sobre el límite
   más 0,6 km, «lejos»; si no, indecidible. «Sin marcador» se guarda como «posible a más de 25 km», no como cerca.
   Error esperado del control: 4,5 % de las decisiones, con 20 % sin decidir.
3. Hacia atrás vale **desde el 2026-04-14** en VIIRS 375: el archivo de PNG empieza el 2026-05-09 y el panel cubre
   30 días. Eso alcanza 280 de las 482 ALERTA VIIRS 375 con 0 fijo; con este método salen 163 cerca, 48 lejos
   (32 de Lastarria), 34 indecidibles y 35 sin marcador (`salidas/decision_cero_salida.txt`, aplicación sin control
   propio). Antes del 04-14 no hay imagen archivada. El panel «Last Year» llega más atrás pero no separa noches
   (SIN VERIFICAR).
4. Mejor todavía, en el scraper: guardar cada `Dist.png` y leer la columna de la noche cuando pasa la noche, no sólo
   la estrella.
