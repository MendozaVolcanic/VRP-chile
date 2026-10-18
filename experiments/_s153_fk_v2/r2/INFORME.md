# R2 de la adopción de K: cinco pasadas contra las imágenes de MIROVA

Tarea de solo lectura, 2026-10-18 (regla `experiments/_s151_prereg_fk_11/REGLA_ADOPCION.md` §4, paso 4). Ningún
archivo del repo editado. Todo lo de aquí sale de `C:\Users\nmend\AppData\Local\Temp\claude\r2_fk\`.

## 0. En una línea

**Cinco de cinco COINCIDEN.** En los tres negativos limpios K calla igual que MIROVA, y lo que C0 publicaba cae en
un punto que la imagen de MIROVA muestra como ruido. En las dos alertas de VIIRS 375 el cúmulo de K cae a 0,18 y
0,24 km del foco caliente de MIROVA. En la alerta MODIS que K recupera, su píxel queda en la celda vecina al foco de
MIROVA (1,34 km), dentro de la tolerancia de MODIS pero no sobre la celda misma. Hubo una sorpresa en el caso 3: la
pasada elegida primero no se puede usar, porque su GeoTIFF no corresponde a esa pasada (§3).

## 1. Fuentes y método

- **Pasadas, etiquetas y decisiones**: `C:\Users\nmend\AppData\Local\Temp\claude\r3_fk\pasadas_V1.jsonl` y
  `pasadas_V2.jsonl` (`pub_C0`, `pub_K`, `neg`, `protA`). Records de C0 (`_s146_ab_control`) y K
  (`_s149_ab_sin_test1_b22_max`) de las uniones `v1_38639658446\union_2766`, `v2a_38648773684\union_2766` y
  `v2b_39033530622\union`. Filas de MIROVA de `_congelado_v1` y `_congelado_v2` (CONS y OCR, a ±3 min).
- **Imágenes**: `index.csv` de `MendozaVolcanic/mirova-tif-archive` (blob `19c9273e`, leído por la API) y **9
  GeoTIFF** bajados de a uno por la API (`r2_fk\tif\`). El TIF se empareja por `acquisition_utc` del índice a ±15
  min, nunca por el nombre del archivo, y se comprueba el md5 local contra el del índice. Los nueve tienen el md5
  asociado a una sola hora de adquisición (A106).
- **Lectura**: con el lector del repo `experiments/_s151_seleccion_mirova/comun_tif.py` (importado, no modificado):
  el campo de radiancia MIR menos su mediana móvil, en desvíos robustos (z). El campo crudo no sirve, porque el
  máximo de la imagen siempre cae en el valle tibio (A69, S139 §3.2). La primera corrida, con el campo crudo
  (`analizar.py`, `analizar_salida.txt`), lo mostró: en las cinco pasadas el pico global está a 17 a 29 km del
  cráter.
- **Umbrales**: los p95 que S151 midió sobre pasadas RUTINA de VIIRS 375 (`comun_tif.py`, README de
  `_s151_seleccion_mirova`), o sea lo que la imagen de MIROVA muestra cuando MIROVA miró y no alertó: un foco
  puntual con **z ≥ 10,6** y calor en un disco del tamaño del cráter con **z ≥ 3,3**. Para MODIS no hay p95 medido.
- **Control de atribución (A109)**: la BT del TIF contra la BT de nuestros píxeles de la misma pasada
  (`dbt_mediana`, mejor celda 3×3). Un valor menor de 1 K significa que el TIF salió del **mismo gránulo** que leyó
  nuestro detector. Pasó en los casos 1, 2, 3 y 5, así que la comparación **no es independiente**: la imagen de
  MIROVA es el mismo campo de radiancia que vio nuestro detector. R2 comprueba entonces dónde puso MIROVA el calor y
  si alertó, no si el calor es real. En MODIS este control no separa (S151), y queda sin dato.
- Scripts: `candidatos.py` (lista por categoría con TIF), `analizar.py` (filas de MIROVA, md5, campo crudo),
  `analizar2.py` (exceso local, atribución, figuras `exceso_*.png`), `shift3.py` y `desplazamiento.py` (§3).
  Salidas: `analizar_salida.txt` y `analizar2_salida.txt`.

## 2. Tabla

z = exceso local de la imagen de MIROVA en la celda (entre paréntesis, el máximo de la 3×3). «Foco del cráter» =
máximo del exceso a ≤ 1,5 km del vent (2,5 km en MODIS).

| caso | pasada | MIROVA | C0 | K | imagen de MIROVA en el píxel de K / de C0 | atribución | veredicto |
|---|---|---|---|---|---|---|---|
| 1. negativo limpio, borde, fondo frío | Chaitén NOAA-20 2026-09-10 04:36, cenit 66,1°, t_bg 244,5 K | calla (RUTINA, 0 MW) | publica, 1 px, 0,020 MW a 3,84 km | calla | C0: z 3,2 (3,2), bajo el p95 de RUTINA. Foco del cráter z 1,6. No hay calor que publicar | 0,21 K, mismo gránulo | **COINCIDE** |
| 2a. negativo limpio, nadir | Láscar NOAA-20 2026-09-06 05:42, cenit 1,2°, t_bg 262,6 K | calla (RUTINA) | publica, 1 px, 0,082 MW a 2,68 km (Test 1 encendido, 92 px) | calla | C0: z 2,7. Foco del cráter z 2,5 | 0,05 K | **COINCIDE** |
| 2b. negativo limpio, cerca del nadir, grilla UTM (celda exacta) | Copahue NOAA-21 2026-09-15 05:24, cenit 24,9°, t_bg 263,3 K | calla (RUTINA) | publica por `test1_roi` (ancla en el vent, cúmulo de 1 px a 2,57 km, 0,017 MW) | calla | C0: z 1,0. Foco del cráter z 0,3 | 0,44 K | **COINCIDE** |
| 3. protegida V375 Láscar | Láscar NOAA-20 2026-06-03 05:24, cenit 33,4° | alerta 1,52 MW, «Bajo» | publica | publica, 3 px, 0,46 MW (núcleo 0,64), a 0,16 km | K: z 28,4 en su píxel más caliente; el foco de MIROVA (z 34,8, ~1,36 MW) está a **0,18 km** del cúmulo de K | 1,05 K (4 px) | **COINCIDE** |
| 3c (refuerzo) | Láscar NOAA-20 2026-06-01 06:00 | alerta 1,69 MW | publica | publica, 2 px, 0,72 MW (núcleo 0,94) | foco de MIROVA z 56,0 (~1,69 MW) a **0,15 km** del cúmulo de K | 5,15 K (2 px calientes, remuestreo) | COINCIDE |
| 4. MODIS que K recupera con la banda 22 | Láscar MODIS Terra 2026-05-10 01:25 | alerta protegida 1,07 MW, 1,0 km | **calla** (la etiqueta pasa a `far` porque `final_hotspot` salta a un píxel a 24,5 km, A46) | publica, 1 px, 0,66 MW a 1,09 km del vent | foco de MIROVA z 10,9 (~1,08 MW) a 0,29 km del vent. El píxel de K cae en la **celda vecina** (z −3,1 propia, 10,9 en la 3×3), a **1,34 km** del foco | sin dato en MODIS (1,22 K en 1 px) | **COINCIDE con salvedad** |
| 5. cúmulo movido > 0,5 km | Tupungatito NOAA-20 2026-06-03 05:24 | alerta 0,17 MW, «Muy Bajo», 5,41 km | publica, cúmulo a 2,71 km del vent (z 2,7) | publica, cúmulo a 0,24 km del vent; se movió **2,48 km** | foco de MIROVA z 5,6 a **0,24 km** del cúmulo de K. Desde el centro del raster: foco 5,14 km, K 4,97 km, C0 7,05 km; MIROVA declara 5,41 km | 0,20 K (K) | **COINCIDE** |

## 3. Lo que cambió en el caso 3 (dicho en orden)

1. Primero elegí **Láscar NOAA-20 2026-06-02 05:42** (cenit 0,1°, alerta 1,8 MW). Su TIF no tiene calor en el
   cráter (BT 254 K en la celda de nuestro píxel de 310 K), y el foco más fuerte de la imagen (z 82, 298 K, ~1,72 MW)
   está a **17,5 km rumbo 239°**. La atribución da **8,2 K**, que S151 rechaza (> 5 K). Lo mismo con NOAA-21
   2026-06-03 06:12: foco a 22,3 km rumbo 224°, atribución **28,5 K**. Las filas de MIROVA de esas dos pasadas dicen
   1,5 y 1,19 km, o sea el cráter. Conclusión: esos dos TIF **no son la imagen de esa pasada** (o su georreferencia
   está corrida). No sirven para R2, y quedan **SIN IMAGEN** válida.
2. Probé si era un corrimiento fijo de la georreferencia (`shift3.py`): al trasladar nuestros píxeles al foco, uno
   de cuatro coincide (268,6 contra 269,2 K) y otro no (267,5 contra 258,8). **No lo puedo decidir**, así que queda
   SIN VERIFICAR. Es un defecto de los TIF de MIROVA o del índice, no de K: las cuatro protegidas de Láscar con TIF
   de junio tienen exactamente la misma decisión en C0 y en K.
3. Reemplacé esas pasadas por las dos protegidas de Láscar cuyo TIF pasa la atribución (06-03 05:24 y 06-01 06:00).
   **El reemplazo se hizo después de ver el fallo**, y lo dejo dicho.

## 4. Notas por caso

- **Caso 4, sin imagen de marzo ni abril.** Las 33 protegidas MODIS de Láscar de V2 que K recupera son de marzo y
  abril, y el archivo de TIF empieza el 2026-05-08 21:43. Elegí la más cercana con imagen: la protegida del
  2026-05-10 01:25, la única protegida de mayo a junio que K recupera y que tiene TIF. K recupera otras nueve
  alertas MODIS de Láscar en ese período: dos protegidas sin TIF (2026-05-03 01:45 y 2026-06-03 07:45) y siete
  bajo 1 MW. El píxel de K no cae sobre la celda caliente de MIROVA sino en la
  de al lado, hacia el sur. 1,34 km es menos que la tolerancia de 2 km que S151 usa para MODIS y está dentro del
  corrimiento de 1 a 3 km de la geolocalización MODIS que ya está documentado (memoria
  `project_modis_geo_interp_offset`). Pero en sentido estricto no está «en» el área caliente. Lo cuento como
  coincidencia con salvedad, no como discrepancia.
- **Caso 5, magnitud.** La posición coincide, pero el cúmulo de K suma 0,008 MW contra los 0,17 de MIROVA, y C0
  tenía 0,098. R2 no mide magnitud (eso es §5 de la regla). Lo anoto porque es el tipo de diferencia que P3 no ve.
- **Caso 3, distancia de MIROVA.** MIROVA declara 3,02 km, mientras el foco de su TIF está a 0,96 km del centro del
  raster y K a 0,93. Puede ser el píxel de 1,82 km del cúmulo, pero no lo resolví (SIN VERIFICAR). No cambia el
  veredicto.
- **Negativos.** En los tres, lo que publicaba C0 cae en una celda con z de 1,0 a 3,2, bajo el p95 de las RUTINA en
  el disco del cráter (3,3) y muy lejos del de un foco puntual (10,6). La imagen de MIROVA no muestra nada que
  MIROVA debiera haber alertado, y K, igual que MIROVA, calla. En el 2b, C0 publicaba por el ancla del Test 1 en el
  vent con el cúmulo a 2,57 km: el patrón `keep_peak` de D19.

## 5. Límites

- Una pasada por categoría (dos en la 3): R2 es un control de ojo, no una tasa.
- La imagen viene del mismo gránulo que nuestro detector (A109). En los negativos esto juega a favor de K (el campo
  mismo no tiene calor), pero no prueba que la decisión sea correcta respecto del volcán.
- No miré las láminas PNG de Mirova-v1 (Latest y Dist). En el caso 3 original (06-02 05:42) existen, y servirían
  para resolver el punto 2 del §3 (SIN VERIFICAR).
- `index.csv` leído en el blob `19c9273e` (al 2026-10-18), no fijado a un commit con nombre.
- Según la regla, una discrepancia se explica antes de seguir. Aquí no hay ninguna; la salvedad del caso 4 la
  dejo escrita para que Nicolás decida si la considera discrepancia.
