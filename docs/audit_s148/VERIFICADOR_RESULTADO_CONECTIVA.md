# Verificador independiente del resultado del A/B de la conectiva, ventana completa (S148)

> Verificador con contexto limpio. Objeto auditado: el documento de resultado del A/B de la
> conectiva (brazo F) que viene en el PR 735, rama s148-resultado-conectiva, y sus salidas crudas.
> Ventana 2026-09-01 a 2026-09-20. Datos: la copia local de trabajo "prelim_s148" (no está en
> git), brazos B (control, con Chaitén, Tupungatito y Villarrica de la reparación) y F (`max`).
> Scripts y salidas crudas de esta verificación: `experiments/_s148_verificador_resultado/`
> (`r1_tabla.py`, `r2_analisis.py`, `r3_nulo_y_costos_ocultos.py`, `r4_varios.py`, con
> `out_evaluar_mio.txt`, `out_r2.txt`, `out_r3.txt`, `out_r4.txt`). No se editó ningún archivo
> existente, no se corrió la suite, no se tocó `pipeline/`. `tabla.json` (2,4 MB) es regenerable
> con `r1_tabla.py`.

## Veredicto

1. **No logré romper el resultado central.** P1 a P4, la magnitud pareada por volcán, los 13
   cúmulos movidos y las dos pasadas perdidas se reproducen exactos con el evaluador y con un
   cálculo propio e independiente (predicado del tablero portado a Python: 0 discrepancias con
   node en 4.772 evaluaciones). Excluir del 18 al 20 no cambia nada, y el reemplazo de los tres
   volcanes reparados no introduce gránulos distintos.
2. **El costo está subcontado, no mal contado.** Fuera de las 143 pasadas positivas, el brazo
   apaga 50 publicaciones de VIIRS 375 en noches en que MIROVA sí alertó en ese volcán, y 7 de 15
   en pasadas que el scraper rotuló como detección lejana. El evaluador no las mira. Y hay dos
   noches afectadas, no una, según cómo se defina "noche perdida".
3. **Dos instrumentos del evaluador no miden lo que el documento dice que miden** (C8 lo cumple
   un apagador al azar en 200 de 200 sorteos; P2 con 10 sobrevivientes se cumple por azar 24 % de
   las veces). En este caso el brazo F igual sale bien parado por otra vía (Fisher, contrafactuales),
   así que no invalidan el resultado, pero no deben citarse como la prueba de selectividad.

## Hallazgos, por gravedad

### H1. El recall "sin costo serio" sólo mira las 143 pasadas con alerta; el brazo apaga 50 publicaciones más en noches con alerta de MIROVA
- **Dónde**: documento del PR 735, sección 4 ("Lo que cuesta"); `experiments/_s146_ab_sin_test1/evaluar.py:499` (`perdidas_pasada` sólo recorre las `pos`).
- **Qué pasa**: en VIIRS 375 hay 416 pasadas `sin_info`. De ellas, 171 caen en una noche en que
  MIROVA alertó en ese mismo volcán (en otra pasada). Ahí el control publica 84 y el brazo 34: se
  apagan **50**, repartidas en Chaitén 13, Puyehue Cordón Caulle 10, Tupungatito 8, Isluga 5,
  Villarrica 5, Lastarria 3, Planchón Peteroa 3, Láscar 2, Nevados de Chillán 1. Mediana de lo
  apagado 0,029 MW; 5 de las 50 tienen 0,1 MW o más. La tasa de apagado ahí (60 %) queda entre la
  de los negativos limpios (91 %) y la de las positivas (1,5 %), que es lo esperable de una mezcla
  de calor real y ruido: o sea, una parte de esas 50 es probablemente señal real sub-umbral del
  mismo episodio (categoría b de A54), que MIROVA no listó en esa pasada. Además, en `far_ref`
  (MIROVA publicó, el scraper la rotuló fuera de su límite) el control publica 15 de 30 y el brazo
  8: se apagan 7 (Isluga 3, Planchón Peteroa 2, Lastarria 1, Cordón Caulle 1). En VIIRS 750, 16 a 9.
- **Por qué importa**: para la réplica de MIROVA no es un falso negativo (MIROVA no alertó en esa
  pasada), pero el operador ve una noche activa con menos pasadas publicadas. El documento no lo
  menciona y la frase "lo que cuesta" queda incompleta.
- **Reproducir**: `r3_nulo_y_costos_ocultos.py`, bloque b (`out_r3.txt`).
- **CONFIANZA** alta en los conteos; media en la lectura física (no verifiqué píxel a píxel que
  sea calor real). **GRAVEDAD 3.**

### H2. C8 (nulo por etiquetas barajadas) lo cumple un apagador al azar: el nulo no es el que el documento describe
- **Dónde**: `experiments/_s146_ab_sin_test1/evaluar.py:385` a `:428`; documento, tabla de la sección 2 ("que la caída sea selectiva y no un endurecimiento parejo").
- **Qué pasa**: el nulo baraja etiquetas entre **todas** las pasadas del estrato, publicadas o no,
  y el criterio es bilateral (`obs < lo or obs > hi`). Un brazo que apagara al azar la misma
  cantidad de publicaciones que F dentro de cada volcán y sensor da un contraste mediano de
  **+0,215** (rango +0,153 a +0,277), **fuera del intervalo [0,050; 0,146] en 200 de 200
  semillas**: C8 le daría verde. La razón es que las positivas están publicadas al 96 % y los
  negativos al 30 %, así que apagar al azar entre lo publicado golpea más a las positivas que lo
  que el barajado de etiquetas supone. El docstring dice que un apagador al azar "caería dentro
  del nulo": medido, no cae.
- **Lo que sí se sostiene**: reimplementé el nulo y reproduzco -0,1082 contra [0,0498; 0,146]. Y
  el brazo F queda del lado **opuesto** a los tres contrafactuales que probé: apagado al azar
  (+0,215), un corte parejo de magnitud en MW (+0,304, perdería 62 positivas) y un corte parejo por
  sensor (+0,105, perdería 33 positivas y dejaría 31 negativos en VIIRS 375). F pierde 2 y deja 10.
  O sea que la selectividad respecto de la etiqueta de MIROVA es real y grande; lo que está mal es
  el instrumento que el documento cita como prueba, no la conclusión.
- **Reproducir**: `r3_nulo_y_costos_ocultos.py` bloque a, `r4_varios.py` bloque a.
- **CONFIANZA** alta. **GRAVEDAD 3** para el evaluador (certificaría un brazo malo), 1 para este
  resultado.

### H3. P2, "la que decide", tiene poco poder cuando el brazo apaga el 91 %
- **Dónde**: documento, sección 3; pre-registro `experiments/_s147_ab_conectiva/PREREGISTRO.md:107` y `:111`.
- **Qué pasa**: con sólo 10 sobrevivientes, si el brazo apagara **parejo** (sin mirar la zona),
  P2 menor o igual a 1,3 se cumpliría por azar en **24,2 %** de 5.000 sorteos (y la razón queda
  indefinida en 8 %). El pre-registro dice que P2 existe justo para distinguir "selectivo" de
  "apaga de todo un poco", y a esta tasa de apagado no distingue bien. El documento ya advierte
  que 0,25 sale de 2 contra 6, pero sostiene que "P2 en 1,3 o menos es robusto": como umbral
  cumplido sí, como evidencia de selectividad no.
- **Lo que sí sostiene la selectividad**: supervivencia de las publicaciones del control en
  negativos limpios: nadir 6 de 24, zona media 2 de 17, borde 2 de 70; Fisher nadir contra borde
  p = 0,003. Y el valor observado 0,25 o menor sale por azar en 0,24 % de los sorteos. P3 también:
  borde con fondo de 260 K o menos, 45 de 77 a 2 de 77 (y es estable al mover el corte: 255 K da
  35 de 51 a 0; 265 K da 55 de 108 a 2).
- **Matiz**: la magnitud del control en los negativos publicados baja hacia el borde (mediana
  0,050 MW en nadir, 0,037 en zona media, 0,025 en borde), así que "selectivo del borde" y "apaga
  lo más débil" están confundidos en parte. No los separé.
- **Reproducir**: `r4_varios.py` bloque b; `r3_nulo_y_costos_ocultos.py` bloque e; `r2_analisis.py` bloque 2b.
- **CONFIANZA** alta. **GRAVEDAD 2.**

### H4. Las noches afectadas son dos, no una
- **Dónde**: documento, sección 4; `experiments/_s146_ab_sin_test1/evaluar.py:489`.
- **Qué pasa**: el evaluador cuenta una noche como perdida si el brazo no publica **ninguna pasada
  de cualquier etiqueta** esa noche: da Isluga 2026-09-19. Pero esa noche se pierde por una pasada
  `far_ref` (05:00, 0,036 MW), no por una positiva. Si la noche se define sobre las pasadas en que
  MIROVA alertó, la perdida es **Lastarria 2026-09-04**: su única pasada positiva (06:24) se
  apaga, y la noche "sobrevive" en el evaluador sólo porque el brazo publica la de las 06:00, que
  es `sin_info` y cuyo cúmulo se corre 0,84 km. Las dos son bajo 0,15 MW de MIROVA.
- **Reproducir**: `r4_varios.py` bloque c.
- **CONFIANZA** alta. **GRAVEDAD 2.**

### H5. Números del documento que no salen de las salidas crudas de la ventana completa
- **"30 de 124 positivas de VIIRS 375 publican sin ningún píxel del primer pase"** (sección 6.1):
  es el número del tramo de 17 días. En la ventana completa son **34 de 135** (en el tramo 01 a 17
  reproduzco 30 de 124). El encabezado dice que ningún número viene de otra parte.
- **"Nevados de Chillán 1"** (sección 6.3): Nevados de Chillán tiene **4** pasadas positivas en
  VIIRS 375; 1 es lo que publican ambos brazos. Villarrica 5 es correcto.
- **"1 de 399 contra 397 de 399"** en MODIS (sección 5): el documento lo atribuye a la lectura
  preliminar, correcto, pero en la ventana completa es **1 de 467 contra 465 de 467** (en
  negativos limpios, 0 de 440 contra 439 de 440). La conclusión no cambia.
- **"111 de 372"**: el evaluador da 111 de **373**; la tabla por zonas bota una pasada sin
  `t_bg_k`. Porcentaje idéntico (29,8 %). Lo mismo con nadir 129 contra 130.
- **"no cambia en Láscar"**: Láscar pasa de 0,4775 a 0,4730 y cambian 4 de sus 18 pares, los 4
  alejándose de MIROVA. "Casi no cambia" sería exacto.
- **"antes al control le faltaban 71"** y **"2362 de 2362 idénticas" contra el run 35521542153**:
  el segundo figura en el JSON de resultado del documento; **SIN VERIFICAR** por mí, porque el
  brazo B de ese run no está en la copia local. Ojo: ese control comparó la intersección (2362),
  así que 24 pasadas del control de hoy no tienen contraparte en el run viejo.
- **Reproducir**: `r2_analisis.py` bloques 2, 5 y 8; `r4_varios.py` bloque d.
- **CONFIANZA** alta. **GRAVEDAD 2.**

### H6. La magnitud: "el mismo déficit de A99, agravado" es cierto en el agregado y mixto en Cordón Caulle
- **Qué pasa**: de 135 pares, cambian 31. En 20 el brazo queda más lejos de MIROVA y en 11 más
  cerca. Los 11 son casi todos de Cordón Caulle (10 más cerca, 11 más lejos): ahí el control
  sobrestimaba (1,06) y el brazo, al perder el vecino, a veces cae justo sobre MIROVA (por ejemplo
  2026-09-18 06:48: 0,635 a 0,296 contra 0,30 de MIROVA). En Láscar (4 de 4) y Tupungatito (3 de
  3), que ya subestimaban, siempre se aleja. El error logarítmico absoluto mediano no cambia
  (0,5097 en los dos) y el medio sube de 0,660 a 0,667. Seis positivas pierden más de la mitad de
  su magnitud respecto del control (mínimo 0,25, Cordón Caulle 2026-09-08 06:30), pero contra
  MIROVA las que quedan bajo un cuarto pasan de 7 a 8, no más.
- **Reproducir**: `r3_nulo_y_costos_ocultos.py` bloque d; `r2_analisis.py` bloque 3.
- **CONFIANZA** alta. **GRAVEDAD 1.**

### H7. `sensor_zenith_deg` difiere entre brazos sobre el mismo gránulo
- **Qué pasa**: en 817 de 2.386 pasadas el ángulo cenital del sensor difiere entre B y F (hasta
  2,6 grados, 169 sobre 1 grado), con gránulo, `t_bg_k` y `t_max_k` idénticos. **SOSPECHA**: el
  campo se toma en el píxel del punto caliente, que cambia de brazo a brazo. Consecuencia: 13
  pasadas cambian de zona según el brazo con que se clasifiquen, y por eso las tablas por zona del
  documento muestran denominadores distintos por brazo en VIIRS 750 y MODIS (209 contra 208, 147
  contra 150). En VIIRS 375 no mueve ninguna conclusión (P2 da 2,17 y 0,25 clasificando todo con
  el ángulo del control).
- **Reproducir**: `r3_nulo_y_costos_ocultos.py` bloque c.
- **CONFIANZA** alta en el hecho, baja en la causa. **GRAVEDAD 1.**

## VERIFICADO LIMPIO

- **Reemplazo de los tres volcanes reparados (camino 1)**: en las 2.386 pasadas, **0** gránulos
  distintos y **0** `product_version` distintos entre control y brazo, incluidos los días 18 a 20
  (111 estándar y 253 de tiempo casi real en **ambos** brazos) y las 680 pasadas de los tres
  reparados, que se procesaron unas 4 a 7 horas después (06:44 a 07:41 UTC contra 00:35 a 03:28).
  `t_bg_k` y `t_max_k` idénticos en todas. No hubo promoción de gránulos entre medio.
- **Sensibilidad a la ventana**: sin los días 18 a 20, VIIRS 375 da P1 29,2 % a 3,1 % (95 y 10 de
  325), P2 2,12 a 0,25, P4 125 a 124 de 129. Sólo días 18 a 20: 16 de 48 a 0 de 48, P4 12 a 11 de
  14. Sólo gránulos estándar: 31,0 % a 2,8 %. Sin los tres volcanes reparados: 27,1 % a 3,3 %,
  P2 1,75 a 0,29, P4 99 a 98 de 104. Nada depende del tramo nuevo ni de la reparación.
- **INDECIDIBLE (camino 2)**: es cierto lo que dice el documento. `control_positivo_control`
  (`evaluar.py:431`) exige identidad, cobertura y banda; en el JSON del documento identidad 1,0,
  cobertura 1,0 y 0 diferencias en los siete campos; falla sólo la banda, en VIIRS 375 (0,2976
  contra 0,80 a 0,92) **y también en VIIRS 750** (0,0595 contra 0,16 a 0,27; el documento nombra
  sólo la primera). Las bandas están calibradas sobre producción con el Test 1 encendido
  (`parametros.json`, clave `_banda_por_que`). Corrí el evaluador contra la producción congelada:
  el bloque del brazo sale idéntico al del documento (comparación de JSON, `r4_varios.py` bloque e).
- **P1 a P4 (camino 3)**: reproducidos con el evaluador y con port propio. Etiquetas: mi
  etiquetador tosco discrepa del evaluador en 7 de 2.386 (las llama `sin_info`), ninguna positiva.
- **Magnitud pareada**: 0,7895 a 0,7129 (n = 135) y los nueve volcanes coinciden al cuarto decimal.
- **Cúmulos movidos**: 13 de 228, Lastarria 10 (0,76 a 1,83 km), Tupungatito 3,06, Cordón Caulle
  3,93, Villarrica MODIS 1,33. De los 13, sólo 2 son pasadas positivas (Lastarria 09-02 06:06,
  0,76 km con magnitud idéntica, y el MODIS de Villarrica); 3 son negativos limpios y 8 `sin_info`.
- **Pasadas perdidas (camino 5)**: son todas. Transiciones en positivas VIIRS 375: 135 publican
  ambos, 2 sólo el control, 6 ninguno, 0 sólo el brazo. Ninguna positiva queda "publicada" con el
  cúmulo a más de 2 km ni desplazada fuera del radio interior.
- **Por volcán (camino 6)**: ningún volcán va contra la corriente. El brazo no gana **ninguna**
  publicación en ningún estrato, sensor ni etiqueta (es un subconjunto estricto del control). Los
  10 negativos que sobreviven: Lastarria 4 de 8, Láscar 3 de 12, Planchón Peteroa 2 de 9, Chaitén 1
  de 18; los otros siete volcanes quedan en cero. Todos los sobrevivientes son del 1 al 17.
  Pérdidas de positivas: Lastarria 9 a 8 y Tupungatito 25 a 24.

## LO QUE NO CUBRI

- No abrí ningún gránulo ni TIF de MIROVA: no sé si las 50 publicaciones del H1, los 10
  sobrevivientes o los cúmulos movidos de Lastarria son calor real. Eso es la verificación a nivel
  de píxel que el documento ya propone.
- No verifiqué el control positivo contra el run 35521542153 ni las 71 pasadas faltantes previas.
- No revisé el código del brazo F en `pipeline/` (que el flag haga lo que dice), ni el segundo
  pase (dependencia 6.1), ni los brazos G y H.
- No separé "selectivo del borde" de "apaga lo más débil" (matiz de H3).
- No evalué VIIRS 750 y MODIS más allá de reproducir sus conteos; con 18 y 1 positivas no hay poder.
- La ventana son 20 días de septiembre; nada de lo anterior dice qué pasa en invierno.
