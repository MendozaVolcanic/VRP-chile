# Por qué la caja de 5 × 5 km no apaga ninguna publicación (S148)

> Traza de código y contraste con datos, sólo lectura. Tramo 2026-09-01 a 2026-09-17, VIIRS 375,
> brazo G (`_s147_ab_sin_test1_caja`) contra el control B (`_s146_ab_sin_test1`). Datos: copia
> local de trabajo de la lectura preliminar (no está en git). Scripts y salidas crudas en
> `experiments/_s148_caja_traza/`. No se tocó `pipeline/` ni se propone arreglo: se mide y se explica.

## 1. Respuesta corta

Es el camino **(b)**, y es un **defecto de cableado, no una propiedad del método**. La caja sí
actúa, pero sólo en el primer pase. El segundo pase (`second_pass_adjacent`) recibe su zona
permisiva armada con el **círculo** de `inner_radius_km`, sin mirar `_roi1_mask`; como además corre
siempre, sobre toda la escena y sin compuerta de temperatura, vuelve a capturar con el piso
permisivo (0,003) exactamente los píxeles que el primer pase acaba de rechazar con el estricto
(0,010). El resultado final es el mismo cúmulo, con otra etiqueta interna.

**El A/B del brazo G no midió la caja del paper. Midió la caja en un pase y el círculo en el otro.**
Escribir "la caja es inerte" sería un cierre en falso.

## 2. El fenómeno

Lo que se publica donde MIROVA calla, fuera de la caja, son píxeles aislados y apenas tibios en
el flanco del volcán, entre 2,6 y 5 km del cráter (hasta 17 km en Puyehue Cordón Caulle, cuyo
círculo es de 20 km). En 48 de los 51 casos el cúmulo es de un solo píxel. Su exceso de
temperatura de brillo sobre el fondo tiene mediana de 2,6 K, y en 28 de los 51 no llega a los 3 K;
en varios el píxel es incluso más frío que el fondo (Villarrica, -6,4 K). Son contrastes locales
chicos del índice NTI contra sus ocho vecinos, no calor en sentido absoluto.

La idea del paper es que a esa distancia de la cumbre un contraste tan chico no debe bastar: fuera
de la caja exige 0,010 en vez de 0,003. La pregunta del A/B era si, exigiéndolo, esos píxeles
dejan de publicarse.

## 3. El mecanismo en el código

Comprobado contra los archivos de hoy (`main`, commit `599c496c4` más lo que entró durante la sesión):

1. **La máscara se arma bien.** `pipeline/process_viirs.py:771-773`: si `ENABLE_ROI1_BOX_PAPER`,
   `_roi1_mask = roi_mask_bbox(lat, lon, vent_lat, vent_lon, ROI1_BOX_HALF_KM)`. Leído de
   `pipeline.profile` con el perfil de cada brazo: el flag vale False en B y True en G, medio lado
   2,5 km. El resto de los flags relevantes es idéntico en los dos (primer pase dual encendido,
   segundo pase encendido, **segundo pase dual encendido**, segundo pase condicionado apagado,
   conectiva `min`, compuerta de 3 K, Test 1 apagado, camino de BT apagado, filtro final apagado).
2. **Llega al primer pase.** `process_viirs.py:1274-1276` llama a `first_pass_tests_2_and_3(...,
   roi1_mask=_roi1_mask, ...)`, y adentro `pipeline/detection_context.py:526` la usa
   (`roi1_summit_mask`, l. 299-325: si viene máscara, el radio se ignora) para elegir el umbral de
   **los dos** tests, dNTI (l. 534) y dETI (l. 535). El camino (c) queda descartado en el primer
   pase: la caja se aplica a los dos tests.
3. **No llega al segundo pase.** `process_viirs.py:1313` arma
   `is_summit_mask = vent_dist_per_pixel <= inner_radius_km`, el círculo de siempre, y la l. 1331 se
   lo entrega a `second_pass_adjacent(is_summit=...)`. Esa función (`detection_context.py:822`) no
   tiene parámetro `roi1_mask`; su zona permisiva es lo que el llamador le pase (l. 949-950). El
   mismo patrón está en `pipeline/process_modis.py:923` y `pipeline/process_viirs_mod.py:892`.
   El docstring de `roi1_summit_mask` dice que centralizó la decisión que "estaba escrita en tres
   lugares de este archivo": la cuarta copia vive en los procesadores y quedó fuera (A102).
4. **Por qué eso basta para deshacer la caja.** Con `conditioned=False` el segundo pase corre
   aunque el primero no haya detectado nada, no se restringe a vecinos de lo ya detectado, y no
   reaplica la compuerta `bt > t_bg + 3 K` (l. 903-967; ya medido en
   `docs/audit_s148/MEDICION_H2_H3_CONECTIVA.md`). Si el primer pase queda vacío, el dNTI y el dETI
   que recalcula son los mismos del primer pase (no hay activos que excluir de los vecinos), y les
   aplica 0,003 dentro del círculo. Todo píxel de la corona que pasaba el primer pase de B pasa el
   segundo de G.
5. Los otros usuarios de `_roi1_mask` (camino de BT l. 987, dNTI contextual heredado l. 1065,
   filtro final l. 1369, filtro por píxel del Test 1 l. 1824) no deciden nada acá: están apagados (el último depende del Test 1, apagado en los dos brazos) o, en el caso del dNTI
   contextual, se calcula sólo como diagnóstico porque el primer pase reemplaza la máscara
   (`hot_mask_2d = fp_hot`, l. 1299). Por eso `diag_n_dnti_ctx_path` cambia en cientos de records
   sin efecto alguno.

**Demostración con las funciones reales** (`demo_sintetica_segundo_pase.py`, salida en
`demo_sintetica_salida.txt`): un píxel a 3,4 km del centro, con exceso de 0,006 y 5 K sobre el fondo.

| caso | primer pase | resultado final |
|---|---|---|
| B: círculo en los dos pases | detecta | detecta |
| G como está cableado: caja en el primero, círculo en el segundo | **no detecta** | **detecta** (recaptura 1) |
| contrafactual: caja en los dos pases | no detecta | **no detecta** |

## 4. El contraste con los datos

Salida cruda: `experiments/_s148_caja_traza/traza_51_salida.txt`.

Sobre los **51 negativos limpios publicados con el cúmulo fuera de la caja**:

| medida | control B | brazo G |
|---|---|---|
| píxeles del primer pase (suma) | 86 | **7** |
| píxeles recapturados por el segundo pase (suma) | 98 | **175** |
| píxeles anómalos totales | 184 | 182 |
| pasadas con el primer pase vacío en toda la escena | 23 | **47** |
| pasadas con recaptura del segundo pase | | 51 de 51 |

- En 26 de las 51 el primer pase pierde píxeles en G, y en esas mismas 26 el segundo pase gana.
  En 49 de 51 lo que pierde uno es exactamente lo que gana el otro, y el cúmulo primario
  (posición, magnitud, número de píxeles) es idéntico en las 51.
- En 47 de 51 el primer pase de G no detecta **nada** en toda la escena: la publicación de G sale
  entera del segundo pase. Las 4 restantes (Láscar 09-06 y 09-08 05:06, Villarrica 09-10 05:18 y
  05:54) conservan algún píxel de primer pase, pero también ahí hay recaptura.
- Los 51 cúmulos de G tienen todos sus píxeles fuera de la caja, y 49 de 51 los tienen todos dentro
  del círculo, que es justo la corona donde el segundo pase sigue siendo permisivo.
- **El camino (a) queda refutado para lo que se puede medir**: 79 de los 86 píxeles de primer pase
  del control (92 %) **no** superan el umbral estricto, porque el primer pase de G los rechaza. Es lo
  que la pista del pre-registro anticipaba. Sólo 7 lo superan.

El mismo patrón aparece en los 44 de dentro de la caja (primer pase 142 a 33, segundo 217 a 322:
el primer pase escanea toda la escena, no sólo el cúmulo) y en los 125 positivos (210 a 170, 267 a
300). Sobre todos los records del tramo (`balance_pases_salida.txt`): VIIRS 375 primer pase 1026 a
372 y segundo 1347 a 1882; VIIRS 750 110 a 28 y 290 a 354; MODIS 26.175 a 23.206 y 28.162 a 29.586.

Controles del instrumento (`controles_salida.txt`): el control contra sí mismo da cero campos
distintos y sumas iguales; con el brazo de la conectiva los 51 quedan en 0 píxeles en los dos
pases (ahí el segundo pase también usa `max`, por eso no deshace nada). Las diferencias en
`diag_mu_deti` y `diag_sd_deti` entre B y G son ruido de máquina (máximo 3 × 10⁻¹³ relativo a sigma).

## 5. Qué se puede decir del contrafactual, y qué no

Con la caja también en el segundo pase, **al menos 11 de las 51** quedarían candidatas a apagarse
con seguridad razonable: son las pasadas donde en B todos los píxeles eran de primer pase, sin
recaptura, y en G el primer pase quedó vacío (esos píxeles fallaron el umbral estricto, y hoy
vuelven sólo por el segundo pase). Otras 23 ya eran sólo de segundo pase en B; su exceso de NTI no
está persistido, así que no se sabe si superarían 0,010, aunque su exceso de temperatura (casi todos
bajo 3 K) sugiere que no. **SOSPECHA, no medición**: el umbral del segundo pase sale de una media y
un sigma calculados sobre otra población (todo el recorte menos los activos, no el ROI filtrado), y
bajo `min` podría quedar por debajo del piso. Sólo un reproceso lo dice.

## 6. Segundo encargo: de dónde salió el "43 de 135"

No hay script en el repo que lo produzca (`grep` de "43 de 135" y "63 de 105": sólo el pre-registro
y la lectura preliminar). Lo reconstruí sobre los datos del mismo run 35521542153 (brazo sin Test 1,
rama `origin/s146-ab/35521542153`, extraídos a un temporal) probando diez definiciones
(`origen_43_de_135.py`, salida en `origen_43_de_135_salida.txt`). **Una sola reproduce los seis
números del pre-registro exactos** (43/135 y 63/105; 9/13 y 23/36; 0/1 y 30/39): el centroide de
`primary_cluster` contra una caja centrada en la **coordenada nominal del volcán** (`lat`, `lon` de
`volcanoes.yaml`, la de `_coords_por_volcan`), no en el ancla de detección. Con el ancla, que es
donde el pipeline centra la caja (`scripts/run_pipeline.py:277-281` pasa `get_detection_anchor` como
`vent_lat`), da 0/135 y 58/105.

Los 43 son 31 de Puyehue Cordón Caulle y 12 de Tupungatito, los dos volcanes cuya ancla está lejos
de la coordenada nominal (7,6 km y 2,7 km; `offset_ancla_coord_salida.txt`). Sus positivos están
pegados al ancla, así que caen dentro de la caja real. **El número del pre-registro usó el centro
equivocado; el instrumento `lectura_caja.py` usa el correcto.** Q3 queda sin sustrato de verdad: no
hay positivos publicados fuera de la caja en esta ventana.

## 7. Lo que no cubrí

- No reprocesé nada: el contrafactual de la sección 5 es una cota y una sospecha, no un resultado.
- Los records no dicen por qué pase entró cada píxel; trabajé con los contadores por record
  (`diag_n_first_pass_pixels`, `diag_n_second_pass_recapture`) y con el exceso de temperatura por píxel.
- En MODIS el segundo pase compensa exacto sólo en 37 de 166 records donde cambia el primer pase, y
  el total de píxeles baja 2,8 %. No tracé por qué ahí la compensación es parcial ni si alcanza a
  explicar que tampoco cambie ninguna publicación. VIIRS 750 sólo en agregado.
- El brazo H (caja más `max`) no se leyó: no tiene cobertura exacta en el tramo.
- 2 de los 51 cúmulos tienen píxeles con `dist_km` mayor que el inner; ese campo puede medirse desde
  otro punto que el ancla (A3) y no lo verifiqué.
- SOSPECHA sin verificar: el A/B de S130 de la misma caja corrió con este mismo cableado, así que su
  "redistribuye, no recorta" tendría dos causas superpuestas (el Test 1 y el segundo pase). No revisé
  el código de esa fecha ni `tests/test_d18_roi1_caja_s130.py` más allá de comprobar que no menciona
  el segundo pase.
- No revisé si el paper dice en forma explícita que el segundo pase usa los umbrales duales de la
  Tabla 1; el código ya lo asume (`ENABLE_DUAL_ROI_SECOND_PASS` encendido).
