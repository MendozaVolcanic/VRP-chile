# VIIRS 375 no ve el lava lake de Villarrica — y el número que publicamos no es el volcán

> Números de `experiments/_s126_villarrica/01_hay_senal_en_el_crater.py` (S91).
> Read-only sobre los brazos ya en disco.

## La pregunta que faltaba

S126 probó que el clúster que publicamos para Villarrica está a **2,74 km** del cráter
incluso en las noches que MIROVA confirma, con el píxel **4,74 K más frío** que el fondo
de la escena. Pero eso no dice cuál es el arreglo, porque hay dos mundos posibles y
piden cosas opuestas:

- **(A) El cráter emite y lo elegimos mal.** Existiría un píxel al cráter más caliente
  que su entorno inmediato, y el problema sería de **selección/ancla**. Arreglo: cambiar
  cómo se elige el píxel.
- **(B) El cráter no emite lo suficiente para 375 m.** No hay nada que elegir: el lava
  lake es sub-píxel a esta resolución. Arreglo: **dejar de reportar** un número que no
  viene del volcán.

## Cómo se separan

El brazo E (filtro contextual apagado) conserva ~50 píxeles por pasada cubriendo el
disco de 3 km, así que trae píxeles **del cráter** que el operacional descarta. Para
cada pasada se compara el contraste **local** —el píxel contra la mediana de su corona
de 0,8 km— en dos lugares: el píxel al cráter (<0,5 km del vent) y el píxel que hoy
publicamos.

**Control positivo: Láscar**, donde el foco es real y está al cráter. Si el método no
lo ve ahí, no sirve y el resto no significa nada.

| volcán | noches | pasadas | % con píxel al cráter | contraste al **cráter** | contraste del **publicado** |
|---|---|---|---|---|---|
| **Láscar** (control) | MIROVA confirma | 102 | 30 % | **+1,01 K** | +2,52 K |
| | sin alerta | 63 | 8 % | +7,24 | +1,66 |
| Planchón-Peteroa | MIROVA confirma | 70 | 67 % | +0,26 | +4,29 |
| | sin alerta | 234 | 41 % | −0,14 | +2,02 |
| **Villarrica** | **MIROVA confirma** | 50 | 20 % | **−0,09 K** | **+0,92 K** |
| | sin alerta | 305 | 18 % | −0,07 | +1,21 |

El control funciona: Láscar da contraste positivo al cráter. El método ve un foco real
cuando lo hay.

## Villarrica: mundo (B)

**El píxel del cráter es indistinguible de sus vecinos** (−0,09 K en las noches que
MIROVA confirma, −0,07 en las quietas: cero, dentro del ruido). El que destaca está a
2,8 km, con +0,92 K.

Y hay un refuerzo que sale del propio muestreo: en el **80 % de las pasadas ni siquiera
existe un píxel al cráter** en el conjunto del brazo E — porque `anomaly_pixels` sólo
guarda píxeles con VRP > 0, o sea los que superan la media del anillo. Que el cráter
falte 4 de cada 5 noches significa que **está por debajo del fondo de su propio
anillo**. Y el 20 % en que sí aparece es el subconjunto más favorable —las noches en que
el cráter está más tibio— y aun así el contraste local es cero.

La conclusión no es que Villarrica esté quieto. MIROVA publica alertas ahí y el lava
lake existe. La conclusión es más específica: **a 375 m, en la banda MIR, ese lava lake
no llena lo suficiente el píxel como para destacar sobre la nieve del cráter.** Es A77
en su forma más limpia — el foco es sub-píxel para este instrumento, y el canal correcto
sería SWIR de alta resolución (Landsat OLI 30 m / Sentinel-2 MSI 20 m, método NHI).

## Qué implica

**El arreglo de Villarrica no es de ancla.** Cambiar cómo se elige el píxel no puede
crear contraste donde no lo hay; sólo movería el número de un lugar equivocado a otro.

**Lo que corresponde es no generar el número.** Hoy publicamos ~380 detecciones desde
mayo con el 92 % del clúster a más de 1,5 km del cráter, todas en rojo como `summit`.
Eso es artefacto en el sentido de A72 —lo generamos nosotros, MIROVA no lo entrega— así
que se ataca en el algoritmo, no ocultándolo en el display.

El camino concreto queda ligado al frente del **fondo autorreferente**: si el fondo del
Test 1 deja de salir de la corona [1,5–3] km que solapa el 75 % del ROI, esa fluctuación
deja de dar ΔL positivo y el número desaparece solo, sin necesidad de un gate por
volcán. Es exactamente lo que el A/B de la corona está probando.

## Lo que NO hay que concluir

- **No "Villarrica no tiene actividad térmica"**: la tiene, y MIROVA la publica. Lo que
  no hay es señal resoluble en VIIRS 375 MIR.
- **No "hay que subir la sensibilidad"**: bajar umbrales sobre un contraste de −0,09 K
  sólo agrega más terreno. El problema es de resolución espacial, no de umbral.
- **No aplicar esto a los otros volcanes**: Láscar tiene foco real al cráter y Planchón
  lo tiene débil pero presente el 67 % de las pasadas. El diagnóstico es de Villarrica.

---

# Confirmación independiente: la propia imagen de MIROVA

Todo lo anterior sale de **nuestro** pipeline. Es evidencia consistente pero endógena:
si nuestro procesamiento tuviera un sesgo, todos esos números lo compartirían.

El repositorio `mirova-tif-archive` guarda el campo de radiancia **I04 de MIROVA** en
GeoTIFF (134×134, EPSG:4326, ~385 m/píxel) — la misma banda que usamos, procesada por
ellos. Eso permite preguntarle a **su** imagen dónde está caliente.

Contraste local (píxel contra la mediana de su corona de 0,8 km) sobre 105 TIFs de
Villarrica y 86 de Láscar, mayo 2026:

| volcán | TIFs | BT al cráter | contraste al **cráter** | contraste a **2,8 km O** |
|---|---|---|---|---|
| **Láscar** (control) | 86 | 292,80 K | **+1,34 K** | −0,06 K |
| **Villarrica** | 105 | 269,83 K | **−0,73 K** | **+0,05 K** |

**El control funciona**: el cráter de Láscar destaca +1,34 K en el campo de MIROVA, y
su BT es 292,8 K — 23 K por encima del de Villarrica.

**Villarrica queda confirmado desde fuera**: en la imagen de MIROVA el cráter tampoco
destaca, está **−0,73 K** por debajo de su entorno. No es que nuestro pipeline pierda
una señal que MIROVA sí ve: a 375 m no hay señal que perder.

Y hay un dato adicional que refina el diagnóstico: **el punto que publicamos a 2,8 km al
oeste tampoco es localmente caliente en el campo de MIROVA** (+0,05 K, cero). O sea que
ese píxel no corresponde a ningún rasgo térmico real — es el **argmax de un campo plano**,
seleccionado porque nuestro fondo autorreferente lo compara contra la media del mismo
anillo al que pertenece. Sin esa comparación circular, no habría nada ahí.

> **Advertencia de método (D6/A24)**: el TIF es el campo de radiancia para visualizar;
> el VRP que MIROVA reporta sale de una selección de clúster, **no** de la suma del
> raster. Acá se usó exclusivamente para la pregunta espacial —dónde está caliente—,
> nunca como magnitud.
