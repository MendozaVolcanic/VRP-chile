# Tarea 1.33 (a): por qué nuestra magnitud de Nevados de Chillán queda bajo la de MIROVA con K

> Escrito el 2026-10-20 (S157, sesión lateral del loop). Sólo lectura: no toca `pipeline/`, los perfiles ni
> `tasks/LOOP_OBJETIVOS.md`, y no despacha nada. Todos los números salen de `a_pasadas_salida.txt` y
> `b_mancha_mirova_salida.txt` (regla S91). **No adopta nada**: es el insumo para que Nicolás decida qué
> pre-registrar primero.

## En una línea

**En Chillán en erupción el fondo no es lo que falta: el déficit que crece con el ángulo es geométrico (el
píxel oblicuo diluye el foco y nosotros lo integramos con área nominal), y en VIIRS 750 y MODIS se le suma el
recorte del tablero. Recomendación: pre-registrar primero D17 (remuestreo), no D25.**

## 1. El fenómeno

Chillán tiene hoy un foco muy caliente y chico: en las pasadas en que MIROVA da 9 MW o más, el píxel más
caliente de VIIRS 375 está entre 328 y 347 K, sobre un anillo de 271 a 275 K. Ese calor ocupa una fracción de un píxel. Cuando el satélite mira de lado
(cenital de 50 a 68°), el píxel en el terreno es dos a cuatro veces más grande que a nadir: el mismo foco queda
repartido en más superficie y cada píxel brilla menos (a las 06:48 del 18-oct, el píxel de 750 m más caliente
marca 288 K contra 317 K a las 06:00 casi a nadir). La potencia física no cambió, pero si uno la calcula con el
área nominal del píxel, la subestima en la misma proporción en que el píxel creció. MIROVA, según sus papers,
remuestrea cada pasada a una malla de celdas de tamaño fijo antes de sumar, y así reparte el píxel grande en
varias celdas y conserva la energía; nosotros usamos el área nominal sin remuestrear (D17, S131).

El fondo es otra historia. La cumbre nevada está más fría que los valles del anillo de 5 a 25 km, así que
nuestra mediana del anillo resta un fondo algo más tibio que el de los vecinos del cráter (D25). Pero en un foco
de 330 K a 3,74 µm el fondo pesa poco: la radiancia del anillo es una fracción chica de la del píxel caliente.
Sólo en los píxeles diluidos (VIIRS 750 y MODIS de lado, 280 a 290 K) el fondo empieza a comerse una parte
importante del exceso.

## 2. Qué se midió, pasada por pasada

`a_pasadas.py` toma las alertas nocturnas de MIROVA en Chillán (referencia unificada remota de Mirova-v1,
pareo de ±2 min de `banco_paridad`), se queda con las pasadas con K (record con `codigo_sha`) que el tablero
publica (predicado de `frontend/index.html` ejecutado con node, A97) y separa la razón R = D / M (publicado
sobre MIROVA) en:

- **F_rec = D / S_in**, recorte del tablero: lo publicado sobre la suma de nuestros alertados dentro del inner
  de 5 km. Medición pura.
- **F_cero**: lo que aporta el recorte a cero del exceso negativo (S26). Siempre 1 o más: sube la magnitud.
- **G = S_in / M**, lo que queda para selección, fondo y área. Sin el Npix de MIROVA no se reparte entre los
  tres, pero se acota sin L1B:
  - **fondo**: G con los vecinos 5 y 10 K más fríos que el anillo (sensibilidad, no medición de D25) y G con
    fondo cero (techo absoluto: ningún fondo da más que eso con nuestros píxeles);
  - **área**: f_area, cuánto más grande es el píxel real que el nominal (modelo geométrico anclado al ATBD,
    brazo B de `experiments/_s131_audit/magnitud/02_correccion_area_por_angulo.py`); G·f_area es lo que
    daríamos si sumáramos con el área real, que es lo que el remuestreo de MIROVA equivale para la magnitud.
- **saturación**: I4 se descarta desde 361,27 K y no deja rastro en el record; se busca con el testigo de M13
  de la misma pasada.

Control: el VRP de los 223 píxeles se reproduce con la fórmula del procesador (223 de 223). Universo: 95
pasadas con alerta, las 95 con K, 87 publicadas (las 8 no publicadas están listadas en la salida).

### 2.1 El caso que pidió Nicolás: NOAA-21, 2026-10-18 06:48, cenital 67,6°

| | MIROVA | publicado | R | F_rec | G | G con vecinos 10 K más fríos | G con fondo 0 | f_area | G con área real |
|---|---|---|---|---|---|---|---|---|---|
| VIIRS 750 | 22,85 | 2,84 | 0,12 | 0,42 | 0,30 | 0,55 | 0,96 | 3,72 | 1,11 |
| VIIRS 375 | 25,79 | 8,93 | 0,35 | 0,95 | 0,36 | 0,41 | 0,47 | 3,73 | 1,36 |

Y las de la misma mañana casi a nadir, para contraste:

| | cenital | MIROVA | publicado | R | F_rec | G | G fondo 0 | G con área real |
|---|---|---|---|---|---|---|---|---|
| VIIRS 750, 05:42 | 20,5 | 20,87 | 14,03 | 0,67 | 1,00 | 0,67 | 0,92 | 0,80 |
| VIIRS 750, 06:00 | 22,3 | 18,98 | 13,60 | 0,72 | 1,00 | 0,72 | 0,98 | 0,89 |
| VIIRS 375, 06:00 | 22,3 | 9,94 | 7,20 | 0,72 | 1,00 | 0,72 | 0,89 | 0,90 |

**Lectura de las 06:48 en VIIRS 750.** Alertamos 6 píxeles que suman 6,84 MW, pero el tablero publica sólo el
cúmulo en modo de un píxel (2,84 MW): el recorte se lleva más de la mitad (F_rec 0,42). Lo que queda (0,30) no
lo cierra el fondo: ni restando cero llegamos a la cifra de MIROVA (0,96), y con vecinos 10 K más fríos
quedamos en 0,55. Con el área real del píxel (3,7 veces la nominal) sí: 1,11. Un píxel alertado está a 268,9 K,
bajo la mediana del anillo (272,0 K), o sea que el entorno inmediato del cráter está más frío que el anillo: la
dirección de D25 es correcta, su tamaño no alcanza.

**En VIIRS 375 de la misma pasada** el recorte no pesa (0,95). El fondo casi no mueve nada: fondo cero da 0,47.
El área real lo pasa de largo (1,36), como ya vio S133 en el borde del barrido (`docs/s133/AB_AREA_VEREDICTO_CHUNK1.md`).

### 2.2 Estratificado por cenital (medianas por pasada, 87 pasadas)

| sensor | cenital | n | R | F_rec | G | alza con vecinos -10 K | G con fondo 0 | f_area | G con área real |
|---|---|---|---|---|---|---|---|---|---|
| VIIRS 375 | < 30° | 12 | 0,73 | 1,00 | 0,73 | ×1,09 | 0,98 | 1,11 | 0,80 |
| VIIRS 375 | 30 a 50° | 13 | 0,58 | 1,00 | 0,58 | ×1,06 | 0,64 | 1,75 | 0,94 |
| VIIRS 375 | ≥ 50° | 19 | 0,45 | 1,00 | 0,45 | ×1,28 | 0,68 | 2,34 | 0,95 |
| VIIRS 750 | < 30° | 9 | 0,84 | 1,00 | 0,91 | ×1,19 | 1,22 | 1,20 | 0,97 |
| VIIRS 750 | 30 a 50° | 12 | 0,41 | 1,00 | 0,45 | ×1,35 | 0,96 | 1,71 | 0,79 |
| VIIRS 750 | ≥ 50° | 11 | 0,16 | 0,57 | 0,32 | ×2,00 | 1,18 | 2,35 | 0,59 |
| MODIS | < 30° | 5 | 0,75 | 1,00 | 0,75 | ×1,38 | 1,48 | 1,19 | 0,78 |
| MODIS | 30 a 50° | 3 | 0,20 | 0,71 | 0,34 | ×1,71 | 1,27 | 1,90 | 0,64 |
| MODIS | ≥ 50° | 3 | 0,20 | 0,70 | 0,20 | ×2,56 | 1,12 | 4,17 | 0,85 |

La tabla completa, pasada por pasada (las 87), está en `a_pasadas_salida.txt`. MODIS tiene 3 a 5 pasadas por
banda: no se afirma nada con eso.

## 3. Qué componente crece con el ángulo

- **VIIRS 375: sólo G, y el área lo explica.** El recorte es plano (1,00 en las tres bandas). El fondo no puede:
  con fondo cero G llega a 0,64 y 0,68 en las bandas oblicuas, y en 25 de 32 pasadas oblicuas ni el fondo cero
  cierra la brecha. Con el área real, G queda en 0,80 / 0,94 / 0,95: la curva se aplana. Lo que sobra a nadir
  (0,73 a 0,80) es otra cosa, selección o fondo, y es parejo.
- **VIIRS 750: crecen tres cosas a la vez.** El recorte del tablero aparece en el borde (F_rec 0,57; el cúmulo en
  modo de un píxel, tarea 1.8), el área crece igual que en 375, y la sensibilidad al fondo crece mucho (×1,19 a
  ×2,00). Lo último es consecuencia de lo primero: un píxel diluido de 285 K está a pocos kelvin del fondo, y
  cualquier error del fondo se come una fracción grande del exceso. D25 y D17 están acoplados: la dilución
  geométrica es lo que hace que el fondo importe.
- **MODIS: igual dirección que VIIRS 750**, con muy pocas pasadas.
- **Saturación: no explica la diferencia con MIROVA.** Nuestra razón entre VIIRS 750 y VIIRS 375 de una misma
  pasada sigue a la de MIROVA (correlación 0,79 en logaritmo, 30 pasadas): cuando a uno le falta energía en
  375 respecto de 750 (p. ej. 2026-10-16 05:42 casi a nadir, razón 3,09 nuestra y 2,93 de MIROVA), al otro
  también. Es lo esperado si los dos descartamos los mismos píxeles saturados de I4, pero sin L1B no está
  verificado que sea saturación: lo que sí está medido es que la falta es común y no separa a MIROVA de nosotros.
- **Recorte a cero: sube, no baja.** Está en 25 de 87 pasadas y su factor es 1,00 a 1,73 (en 2 de ellas el exceso total sin recorte es negativo y
  el factor no se define).

## 4. La mancha de MIROVA crece con el ángulo (indicio)

`b_mancha_mirova.py` cuenta los px blanco puro alrededor del cráter en las miniaturas «Latest10NTI» que MIROVA
publicó de Chillán el 17 y 18 de octubre (archivo `mirova-tif-archive`, data/png). Si MIROVA remuestrea, un píxel
oblicuo se reparte en más celdas y la mancha crece; si suma píxeles nativos, no.

| sensor | cenital 20 a 28° | 45 a 49° | 67,6° |
|---|---|---|---|
| VIIRS 375 (px blancos) | 2 a 3 | 2 y 7 | 19 |
| VIIRS 750 (px blancos) | 12 a 24 | 20 y 20 | 46 |

Pendiente de log(px blancos) contra log(f_area) en las pasadas de potencia parecida (MIROVA 9 MW o más): 2,00 en
VIIRS 375 y 0,85 en VIIRS 750 (n = 5 cada una). Control: las 8 pasadas que aparecen en dos láminas dan el mismo
conteo en las dos.

**Lo que no es.** El blanco puro es el tope de la escala de grises, no la máscara de alertados de MIROVA (A24):
también depende de la intensidad (la pasada débil del 17-oct 04:42, 2,47 MW en VIIRS 750, casi no deja blanco y
por eso la pendiente con todas las pasadas da -0,72 en 750). Con n = 5 y la potencia de MIROVA creciendo hacia el
borde en el subconjunto de 375, es un **indicio**, no una medición. Choca con la tarea 1.14 (§3.2), que no vio
crecer el Npix del OSF de 2025 con el ángulo; esa contradicción queda **abierta** (otro año, otro régimen de
actividad y otra variable: Npix alertado contra mancha del mapa).

## 5. Recomendación: pre-registrar primero D17

1. **En Chillán, D25 no puede cerrar el déficit oblicuo de VIIRS 375**, que es el sensor que publica más
   pasadas: su techo físico (fondo cero) es 0,64 a 0,68. Ningún A/B de D25 puede pasar un criterio de magnitud
   en Chillán oblicuo.
2. **D17 es la única palanca con la dependencia angular correcta** (G con área real 0,80 / 0,94 / 0,95) y con la
   magnitud suficiente, y el mapa de MIROVA lo sugiere por otra vía (§4).
3. **Pero no como fórmula de área.** S133 ya probó el área geolocalizada y se pasó de largo en el borde (0,62 a
   1,36), y aquí la pasada de las 06:48 en 375 también se pasa (1,36). El brazo a pre-registrar es el
   remuestreo literal (la grilla F70 ya existe tras `ENABLE_UTM_REGRID`, hoy apagada, centrada con
   `geo_utils.get_grid_center()`, que nunca se cableó; D17 y D28), y el criterio tiene que ir **por banda de
   cenital**, con Chillán como caso y con el contraste a cenital ≤ 40° que pide D17 (S141). Como el remuestreo
   cambia también μ, σ y la contigüidad, el pre-registro lleva los criterios de detección de K (ninguna
   protegida perdida, negativos limpios), no sólo magnitud.
4. **D25 queda segundo, no descartado**: su dirección es correcta (el entorno del cráter está más frío que el
   anillo) y pesa más justo donde el píxel está diluido (VIIRS 750 y MODIS oblicuos). Medirlo después de D17, o
   en el mismo A/B como brazo propio, evita atribuirle a D25 lo que es geometría. En volcanes con anomalía débil
   (Láscar, Isluga) la tarea 1.14 lo dejó como la palanca más fuerte; Chillán en erupción es otro régimen.
5. **El recorte del tablero en VIIRS 750** (F_rec 0,57 en el borde, modo de un píxel) es una tercera palanca,
   independiente de las dos, ya abierta en la tarea 1.8.

## 6. Lo que no se pudo resolver

- **El reparto selección contra fondo a nadir** (G 0,73 a 0,91): sin el Npix de MIROVA ni el L1B no se separa.
- **El fondo real de los vecinos**: sin L1B. Las credenciales locales son el par usuario y clave vencido que ya
  bloqueó la cuenta (A71), y el NRT corre con un token de la misma cuenta en plena erupción: no se intentó. Para
  medir D25 en estas pasadas hace falta el L1B (un probe en Actions con `EARTHDATA_TOKEN`, que esta sesión no
  despacha).
- **La contradicción con 1.14 sobre el Npix** (§4).
- **MODIS**: 11 pasadas en total.

## 7. Hallazgo lateral (no es de esta tarea)

Con K, MODIS toma la temperatura de la banda 22 (D21), pero el VRP vuelve a radiancia con la longitud de onda
de la banda 21 (`pipeline/process_modis.py:1036` y `:1040`). Así es como se reproducen los 223 píxeles; con la
longitud de onda de la banda 22 la magnitud MODIS sería 1,052 a 1,059 veces mayor en las 11 pasadas (campo
`f_lambda_modis` de la salida). Es chico frente al déficit, pero es una inconsistencia que nació con D21 y no
se ha medido si el k = 18,9 calibrado sobre la banda 21 vale para la 22.

## 8. Reproducir

```bash
python -I experiments/_s157_magnitud_chillan/a_pasadas.py --dest <temporal>      # baja la referencia de Mirova-v1
python -I experiments/_s157_magnitud_chillan/b_mancha_mirova.py --png <temporal>  # baja 4 láminas por la API
```

Referencia de la corrida final: consolidado `25114fe720225050bdb9245236097cdec06cd86c`, OCR
`7bf81852cd5d9103e03ed957ba998c0c90d73586`; records de `data/mirova_equivalent/NevadosDeChillan.json` en
`57d18ad78` (sha del archivo en la salida). Una corrida anterior con el consolidado `7968fa1b` dio las mismas 87
pasadas.
