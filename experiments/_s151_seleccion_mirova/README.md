# Tarea 1.4: qué objeto informa MIROVA cuando hay calor lejos del cráter

Estudio sin correr el pipeline, previo a cualquier código para que la réplica elija como MIROVA. Fecha
2026-10-14. Scripts y salidas en esta carpeta; los TIF y las láminas se bajan a un cache **fuera del repo**
(variable `VRP_TIF_CACHE`, 111 MB en esta corrida), por raw.githubusercontent, sin pull ni clone.

| script | salida | qué mide |
|---|---|---|
| `estudio.py` | `estudio_salida.txt`, `estudio_salida.json`, `pasadas.csv` | P1, P2 y P3 sobre los GeoTIFF |
| `lascar_20261001.py` | `lascar_20261001_salida.txt`, `.json` | georreferencia de las miniaturas de MIROVA y el caso Láscar 2026-10-01 05:18 |
| `comun_tif.py` | | bajar, fechar, leer y medir un TIF (una sola definición) |

## En una línea

**MIROVA no elige un objeto: los datos son compatibles con que sume todo lo que alertó en la escena y publique
la distancia del píxel alertado más lejano.** "El cráter si hay algo en el cráter" y "el más cercano al centro"
quedan refutados (28 pasadas VIIRS 375 en contra, 8 con el umbral estricto, ninguna clara a favor). "La mayor"
acierta la dirección en las mismas 28, pero falla en la magnitud: el VRP que MIROVA publica en esas pasadas es
mayor que el del objeto lejano solo y se parece a lejano más cráter (8 pasadas, p = 0,046). Y en Láscar
2026-10-01 05:18 la imagen de MIROVA sí muestra calor donde estaba nuestro píxel lejano: el "1,2 MW en el
cráter" no está establecido.

## 1. El fenómeno y por qué el TIF sirve

De noche, en el recuadro de 50 × 50 km de un volcán puede haber más de una fuente de calor: el cráter y, por
ejemplo, un incendio o un foco tibio a decenas de km. MIROVA publica una fila por pasada con un VRP y una
distancia sin rumbo, medida desde el centro de su grilla (D15, `../_s151_prereg_caja/distancia_mirova.py`). La
fila no dice dónde estaba el calor. El GeoTIFF que MIROVA publica de esa misma pasada sí: es el campo de
radiancia del infrarrojo medio. Un foco caliente se ve ahí como un **exceso local** sobre sus vecinos; el
gradiente de la topografía (valle tibio contra cumbre nevada, A69) se borra restándole al campo su mediana
móvil (S139). Ese exceso se mide en desvíos robustos (z) y, multiplicado por el coeficiente de Wooster, da una
energía aproximada (A24: el TIF no es VRP sumable, por eso se valida antes de usarla).

## 2. Datos, cobertura y controles de instrumento

- **Universo**: las 359 lejanas nocturnas (FALSO_POSITIVO de la tabla, hora UTC bajo 12, 2026-03-01 a
  2026-10-09; VERIFICADOR_DATOS D2), reproducidas exactas. Comparación: 1.377 ALERTA_TERMICA nocturnas y una
  muestra de 450 RUTINA (150 por sensor, semilla 151).
- **TIF de la misma pasada** (adquisición del índice a ±120 s; se descarta todo archivo cuyo md5 aparece con
  otra hora de adquisición, A106): 117 de las 359 lejanas (103 VIIRS 375, 6 VIIRS 750, 8 MODIS). De las otras
  242, 20 tienen md5 ambiguo y 222 no tienen TIF de esa pasada: 84 son anteriores al 2026-05-09 (inicio del
  archivo), 27 posteriores al 2026-09-22 y 111 caen dentro de la ventana pero el archivo no guardó esa pasada. **MIROVA dejó de actualizar sus GeoTIFF el 2026-09-22** (HEAD del 2026-10-14 al TIF de Láscar VIIRS
  375: `Last-Modified 22 Sep 2026 10:26 GMT`; el KMZ sí se actualiza, 14-oct). El archivo
  `mirova-tif-archive` sigue guardando láminas PNG, pero ningún TIF nuevo desde ese día.
- **Georreferencia**: el centro de cada raster cae a 0,01 a 0,49 km del centro de grilla de `volcanoes.yaml`
  (máximo por volcán); 0 cráteres fuera del raster. Control positivo: en las alertas VIIRS 375 el exceso en el
  cráter (z 7,2) supera al de discos iguales a 8 km en el 96,9 % (rutina: 37,3 %).
- **Atribución** (¿el TIF es de esta pasada?): temperatura de brillo del TIF contra la de nuestros píxeles de la
  misma pasada, con el nulo de los píxeles de otra pasada sobre el mismo TIF. VIIRS 375: mediana 0,61 K contra
  5,00 K del nulo. Los cortes (verificada ≤ 1 K, rechazada > 5 K) se eligieron después de ver estas dos
  distribuciones; se dice. En MODIS el control no separa (5,6 K contra 10,3 K) y queda sin dato. Se apartan 65
  pasadas rechazadas (entre ellas Láscar 2026-06-02 05:42, 30 K: MIROVA y nosotros vemos 1,5 a 1,8 MW en el
  cráter y el TIF no tiene nada ahí). Todo se repite con sólo las 404 verificadas; los resultados no cambian de
  sentido.
- **Umbrales medidos, no elegidos** (A110): el p95 del mismo estadístico en las RUTINA, donde MIROVA miró y no
  alertó nada. VIIRS 375: foco en el anillo z ≥ 10,6; calor en un disco del tamaño del cráter z ≥ 3,3; foco más
  fuerte de toda la zona lejana z ≥ 20,1.
- **Energía** (control que podía fallar): el exceso del foco por Wooster contra el VRP que MIROVA publica da
  Spearman 0,889 en las lejanas (n = 92) y 0,809 en las alertas del cráter (n = 441), con la energía del TIF
  un 20 a 40 % sobre el VRP en mediana. La energía del TIF sirve para comparar objetos.

## 3. P1: ¿el TIF muestra calor a la distancia que dice el CSV, y nosotros vemos lo mismo?

Sí, y en posición, no sólo en radio.

| VIIRS 375, sin las rechazadas | lejanas | alertas (anillo prestado) | rutina (nulo) |
|---|---|---|---|
| foco en el anillo a la distancia del CSV, z ≥ 10,6 | **84 de 97 (86,6 %)** | 16 de 350 (4,6 %) | 7 de 137 (5,1 %) |

- **Anillo corrido** 3 km afuera o adentro: el de la distancia del CSV gana en 89 de 92 lejanas con foco
  (rutina: 28,1 %). El foco está a la distancia que publica MIROVA, no en cualquier parte.
- **Posición contra nuestra pasada** (el foco del TIF girado alrededor del centro de grilla, 11 ángulos, como
  nulo): nuestro píxel alertado de más VRP (`hotspot_lat/lon`) cae a 1 km o menos del foco de MIROVA en
  **39 de 54** lejanas VIIRS 375 (72,2 %), contra **0 de 546** girados. Solo verificadas: 28 de 39 contra 0 de
  385. VIIRS 750: 3 de 3 (nulo 0 de 33). MODIS: 0 de 4.
- Pero la lista `anomaly_pixels` del record casi nunca lo guarda (4 de 57): cuando gana la Regla D, el
  procesador la rehace con los píxeles del Test 1 (`process_viirs.py:1978`). **Nuestro detector ve el objeto
  lejano de MIROVA; el record lo pierde después.** Para el brazo A2 eso es un consumidor más (A118).

## 4. P2 y P3: cuando hay calor en el cráter y lejos a la vez

Las cuatro reglas y lo que predicen en una pasada con las dos cosas:

- **R1 la mayor**: el objeto de más energía; si es el lejano, distancia lejana y VRP del lejano solo.
- **R2 el cráter si hay algo en el cráter**: distancia cercana.
- **R3 el más cercano al centro de grilla**: distancia cercana (el cráter está a 0 a 4,8 km del centro).
- **R4 todo lo alertado junto, con la distancia del píxel alertado más lejano** (Campus 2022 §3.2; S139, que
  ya lo dejó como SOSPECHA): distancia lejana siempre que el lejano esté alertado, y VRP igual a la suma.

| prueba (VIIRS 375, sin las rechazadas) | R1 | R2 | R3 | R4 |
|---|---|---|---|---|
| T1: lejanas con calor en el cráter, z ≥ 3,3 (28 de 84; en rutina el cráter supera ese umbral en 20 de 134): MIROVA informó lejos en las 28 | 28 a favor | **28 en contra** | **28 en contra** | 28 a favor |
| T1 estricto: cráter tan caliente como la mediana de las alertas, z ≥ 7,2 (8 de 84; rutina 4 de 134) | 8 a favor | **8 en contra** | **8 en contra** | 8 a favor |
| T3 magnitud, esas 8: log10(energía TIF / VRP MIROVA) | lejano solo **+0,020** contra la calibración +0,106 (lejanas con cráter frío, n = 56): Mann-Whitney **p = 0,046**, en contra | | | lejano más cráter **+0,181** contra la calibración con el ruido de sumar un cráter frío +0,130: p = 0,757, a favor |
| T4: alertas (MIROVA informó el cráter) con un foco lejano z ≥ 20,1 | 6 en contra si el lejano estaba alertado | 6 a favor | 6 a favor | 6 en contra si el lejano estaba alertado |
| T4 con z ≥ 40,2 | 0 casos | | | |

Cuánto de T1 es ruido: con el umbral laxo el cráter de las rutinas lo pasa en el 15 % (20 de 134), así que de
las 28 unas 13 podrían ser azar; con el estricto se esperarían unas 2,5 de 84 y hay 8. Por eso el resto del
análisis (T3) usa el estricto.

Lo que decide T4: con un foco lejano del TIF de z 20 a 40, MIROVA informa lejos sólo en el 43,3 % de las
pasadas que lo tienen (rutina pesada por su muestreo); con z ≥ 40,2, en el **100 % (39 de 39)**, sin una sola
alerta ni rutina. O sea, un foco débil del TIF muchas veces no es un píxel alertado por MIROVA (su prueba usa
también la banda térmica, que el TIF no trae), y los 6 casos de T4 caen justo en esa banda: no pesan contra R1
ni contra R4. En ellos el VRP publicado se parece al del cráter solo (Láscar 2026-06-28: MIROVA 0,30 MW, TIF
cráter 0,31 MW, lejano 0,58 MW), que es lo esperable si el lejano no se alertó.

Solo verificadas: T1 16 y 7, T3 lejano solo +0,028 (p = 0,048) y lejano más cráter +0,178 (p = 0,560), T4 3
casos en la banda débil. MODIS (2 casos de T1) y VIIRS 750 (1) van en el mismo sentido y no deciden nada solos.

**Veredicto de P3.** R2 y R3 quedan refutadas (28 en contra, 8 con el umbral estricto; los únicos a favor son
los 6 casos débiles de T4). R1 y R4 no se separan por la dirección; se separan por la magnitud, y la magnitud
favorece a R4 con 8 casos y p = 0,046: el VRP de las filas lejanas con cráter activo incluye al cráter. Es la
lectura de los papers (Campus 2022, Coppola 2026: suma de todos los píxeles alertados de la pasada) y la de la
rebaja de A10 / D32 (la suma de escena era el mejor candidato contra MIROVA en VIIRS 375). **Con 8 casos es
evidencia, no demostración**: el umbral del cráter y la calibración de la energía tienen su ruido.

**Consecuencia para el código de la tarea 1.4.** Cambiar `vent_anchored` por `vrp_max` (elegir el cúmulo más
energético) no es lo que hace MIROVA según esto. Lo compatible es: VRP = suma de todos los píxeles alertados de
la escena, y distancia = la del píxel alertado más lejano medida desde el centro de grilla. Antes de escribir
ese brazo conviene que Nicolás lo mire, porque cambia el diseño del A/B pre-registrado (`../_s151_ab_vrp_max/`).

## 5. Láscar, NOAA-21, 2026-10-01 05:18

- La fila de MIROVA (1,2 MW a 1,22 km) es **solo OCR**: no está en la tabla `latest.php`. Desde S150 se sabe que
  en esas filas el VRP es de su pasada pero la distancia viene de la estrella de otra (memoria
  `reference_ocr_imagen_de_otra_pasada`, Mirova-v1#20). La fila de las 05:54 trae la misma distancia, 1,22 km.
- No hay GeoTIFF (MIROVA dejó de publicarlos el 22-sep). Sí están las láminas "Latest" que el scraper guardó
  (cabecera "Last Update 06:18:01"): diez miniaturas del mismo campo, de 150 × 150 píxeles.
- **Georreferencia de las miniaturas, calibrada contra TIF** (`lascar_20261001.py` §1): en 12 de 14 láminas
  de lejanas anteriores al 22-sep la miniatura de esa pasada muestra el foco (z ≥ 10) a 0,66 km en mediana
  (máximo 1,09 km) de donde lo pone el TIF; la misma ventana en las otras nueve miniaturas da z 2,7 en mediana
  y nunca pasa de 10.
- **La miniatura de las 05:18:02** (la cabecera dice ZEN 32°, AZI 101°; nuestro record NOAA-21 tiene 32,36° y
  101,77°: es la misma pasada; la celda es idéntica pixel a pixel en las dos láminas que la traen): el foco más
  fuerte de toda la escena (z 28,9) está a **0,54 km de nuestro píxel lejano** y a 19,5 km del cráter. En
  nuestro píxel lejano z 28,9; el mismo punto girado alrededor del centro, mediana 1,2 y máximo 3,5. El cráter
  también tiene calor (z 15,5).
- En las miniaturas de las 05:54 y 06:18 de esa noche ese punto no tiene nada (z 1,1 y 0,5) y el foco más fuerte
  es el cráter: el objeto lejano duró una sola pasada.

**Respuesta**: nuestro objeto lejano es real y MIROVA lo tenía en su imagen, más fuerte que el cráter. No hay
evidencia de que MIROVA lo haya ignorado: el 1,2 MW de su cabecera (unas 9 veces nuestro cúmulo del cráter,
0,138 MW) se explica mejor como lejano más cráter, y la distancia de 1,22 km no es de esa pasada. El caso no
sirve como contraejemplo de R1 ni de R4, y la premisa de P5 del pre-registro del A/B ("MIROVA 1,2 MW en el
cráter") queda **sin respaldo**.

Observación sin explicar (leída a ojo, no medida): en la lámina "Latest" que el archivo de TIF guardó a las
12:37 del mismo día (`data/png/Lascar/20261001_123714_VIIRS375_Latest10NTI.png`) las celdas de las 05:18 y
05:54 ya no aparecen; después de las 06:18 viene directamente el 30-sep 19:00.

## 6. Lo que no se pudo resolver

- **Qué píxeles alertó MIROVA.** El TIF trae sólo el infrarrojo medio; la prueba de MIROVA usa también el
  térmico. Por eso T4 no puede decir si un foco lejano débil estaba alertado, y R1 contra R4 descansa en T3,
  con 8 casos.
- **Las 242 lejanas sin TIF** (antes del 9-may, después del 22-sep o con md5 ambiguo). Después del 22-sep sólo
  quedan las miniaturas, y sólo se miró el caso de Láscar.
- **MODIS**: el control de atribución no funciona (el pipeline guarda la BT de otra banda o de otra geometría;
  sin verificar) y hay 4 lejanas con foco. Nada de lo de arriba vale para MODIS.
- **El origen exacto de la distancia** (centro del raster contra nodo de la grilla, S139 §5) se absorbió en la
  tolerancia del anillo (0,75 km en VIIRS 375); no se midió.
- **La naturaleza de los focos lejanos** (incendio, faena minera, nube): no se miró.

## 7. Cómo se reproduce

```
set VRP_TIF_CACHE=<carpeta fuera del repo>
python experiments/_s151_seleccion_mirova/estudio.py
python experiments/_s151_seleccion_mirova/lascar_20261001.py
```

Fijados: índice de TIF en el commit `3660cdfa77` de `MendozaVolcanic/mirova-tif-archive`, láminas en el commit
`f14f721f57` de `MendozaVolcanic/Mirova-v1`, referencia de MIROVA con el sha256 que imprime la salida. Baja
unos 1.050 TIF y unas 20 láminas (111 MB en total).
