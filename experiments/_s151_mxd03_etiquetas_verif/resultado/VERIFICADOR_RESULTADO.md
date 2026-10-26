# Verificador con contexto limpio: probe S151 tarea 1.17 (MxD03 contra `_interp_geo`, run 38894508138)

Fecha: 2026-10-16. Sólo lectura. Repo en `main` (`f035f2165`). Datos del probe:
`C:\Users\nmend\AppData\Local\Temp\claude\mxd03_117\` (artefactos de los 12 jobs, `resumen_local.json`).
Mis scripts, todos de lectura, en `C:\Users\nmend\AppData\Local\Temp\claude\verif_117r\`:

| script | qué mide |
|---|---|
| `v1_deteccion.py` | cuántas veces dispara `deteccion_cambia`; fuente del hotspot final en cada cambio de Láscar |
| `v2_pc_label.py` | si los 100 cambios sobreviven a una etiqueta sacada del cúmulo; los 12 cambios del control |
| `v3_mismo_pixel.py` | qué cambios son el mismo píxel reubicado, cuáles otro píxel y cuáles cambio de fuente |
| `v4_desplazamiento.py` | corrimiento medido contra predicho, por cenit, con sus componentes N y E |
| `v5_along_track.py` | hipótesis: el término a lo largo de la traza que falta en el modelo de #828 |
| `v6_c_vs_guardado.py` | brazo C contra el record guardado en `data/mirova_equivalent/` |

## Veredicto global: PARCIAL

Los números del resumen se reproducen (2 protegidas perdidas, 9 ganadas, 22 cambios en estratos
«inmóviles», 12 de 78 en el control, 462 de 470 iguales a lo guardado). El veredicto PIERDE PROTEGIDA
es el que manda el pre-registro con esos datos. Lo que **no** se sostiene es la lectura de que la
geolocalización MxD03 «pierde» esas alertas por posición: el cúmulo del cráter queda igual y más
cerca, y la etiqueta cae por la cadena asimétrica del hotspot final (A46/A81). Además, el modelo de
corrimiento con que se armaron los estratos está incompleto (le falta el término a lo largo de la
traza, encontrado acá con r = 0,955), así que el control no era control y Δ no es interpretable.

## Punto 1. Las 2 pérdidas: REFUTADO como pérdida de posición; CONFIRMADO como salida real de la cadena

**Qué pasa físicamente.** Las dos pasadas (Láscar Terra, 2026-04-20 01:30 y 2026-04-30 01:30) ven
el mismo calor en el cráter con las dos geolocalizaciones: cúmulo de 1,25 y 1,071 MW, idéntico en C y
en M, a 0,72 → 0,23 km y 0,86 → 0,48 km del cráter. Con MxD03 el cúmulo queda **más cerca** del
cráter, no más lejos. Lo que cambia es qué punto de la escena se elige como «hotspot final», y en
MODIS la etiqueta sale de ese punto, no del cúmulo.

**Mecanismo, con línea:**

1. `pipeline/process_modis.py:1278-1280`: `test1_summit_hit` exige que el Test 1 integrado dispare.
   El centroide del Test 1 vive dentro de su ROI de 3 km (`TEST1_ROI_KM = 3.0`, leído de
   `pipeline.profile`), que cae siempre dentro del inner de 5 km, así que `test1_summit_hit` es lo
   mismo que «el Test 1 disparó».
2. `pipeline/process_modis.py:1293-1310`: con eruption lejano y Test 1 en el cráter, gana `test1`
   (brazo C, igual que lo guardado: `triggered_test1 = True`, `test1_k_observed` 4,81 y 3,28). Si el
   Test 1 no dispara, gana `eruption`, que es el píxel de mayor VRP de la escena: el borde del Salar
   de Atacama a 19,09 y 21,55 km (brazo M).
3. `pipeline/process_modis.py:1328-1330` y `:319`: `distance_class` sale de `final_hotspot_dist_km`
   porque `ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER = False` (leído de `pipeline.profile`). Con el
   Salar como hotspot final, la etiqueta es `far`.
4. `pipeline/store.py:381-385` y `:393`: el rescate F47 sólo actúa si `hotspot_dist_km` supera
   `MAX_HOTSPOT_DIST_KM`, que para Láscar es `radius_km: 25` (`volcanoes.yaml:113`). El píxel del
   Salar está a 19 y 21 km, dentro de la cerca, así que no hay rescate y queda `far`.

O sea que la etiqueta de MODIS en Láscar depende de dos interruptores que no miran la posición del
cráter: si el Test 1 de 3 km dispara, y si el píxel del Salar cae a un lado u otro de los 25 km. La
otra cara del mismo mecanismo son las ganancias: las 16 etiquetas que cambian en Láscar tienen el
cúmulo dentro del inner en **los dos** brazos (máximo 2,63 km); 15 de 16 son cambio de fuente
(`test1`/`cluster_rescue` contra `eruption`) y una sola (`MOD021KM.A2026285.0050`, estrato A) es el
píxel reubicado. Sobre los 100 cambios del probe, **93 tienen el cúmulo dentro del inner en C y en
M**: con una etiqueta sacada del cúmulo no habrían existido.

**Por qué el Test 1 deja de disparar en M (SOSPECHA fuerte, no medido).** El probe no persiste
`triggered_test1` ni `test1_k_observed` del brazo M, así que esto es inferencia: si M terminó en
`eruption` con el Salar lejano, por el punto 1 el Test 1 no disparó. El Test 1 de MODIS integra un
disco de 3 km con anillo de fondo de 1 a 3 km sobre píxeles de 1 km
(`pipeline/test1_integrated.py:406-409`): unos 28 píxeles, con el píxel caliente del cráter a 0,8 a
0,9 km, justo en el borde del anillo. Un corrimiento de 0,4 a 1,3 km cambia qué píxeles entran al
disco y cuáles al fondo (mediana y MAD), y con eso el disparo. Es sensibilidad real del Test 1 a la
posición, no un artefacto del parche (C' = C en 24 de 24). Para cerrarlo hay que persistir esos dos
campos en el probe y repetir los dos gránulos.

**¿Las publica MIROVA?** Sí, las dos, en el consolidado
(`data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv`): 2026-04-20 01:30 MODIS
**1,36 MW a 1,0 km**, ALERTA_TERMICA, Bajo; 2026-04-30 01:30 MODIS **1,34 MW a 1,0 km**, Bajo
(distancia cuantizada a la celda, D15). El OCR las repite con 1,0 MW. MIROVA las ve en el cráter,
igual que nuestro cúmulo en los dos brazos.

**Por noche (A94).** Las dos noches tienen alerta de MIROVA también en VIIRS, y en las dos M **gana**
la pasada Aqua de la misma noche (`MYD021KM.A2026110.0740`, MIROVA 0,76 MW; `MYD021KM.A2026120.0730`,
MIROVA 0,99 MW, ambas 0→1). Ninguna noche queda sin publicación MODIS en M. La regla 1 se cuenta por
pasada, así que esto no cambia el veredicto, pero sí su lectura.

## Punto 2. «Otra detección» en 97 de 100: REFUTADO como diagnóstico

**Por qué cambia la detección.** Casi todo el detector MODIS depende de la posición de cada píxel:
el ROI de la escena por distancia al volcán (`pipeline/process_modis.py:516`), la distancia al
cráter efectivo (`:520`), la máscara summit/scene de umbrales duales N·σ 5/10 y C1 0,003/0,010
(`:791`, `:930`), la regresión cuadrática del ETI sobre `roi_mask`, el Test 1 de 3 km y el cúmulo
anclado al cráter. Con 1 a 7 km de corrimiento entran y salen píxeles del borde del ROI y de la
frontera del inner, cambian la media y la desviación de la escena y con ellas los umbrales. Es lo
esperable de cambiar la geolocalización en producción, no un efecto colateral del probe: C' = C en
24 de 24 y los tres brazos leen el mismo L1B (`probe_etiquetas.py:82-128`).

**Por qué el 97 de 100 no dice nada.** `comparar()` (`probe_etiquetas.py:173-181`) marca
`deteccion_cambia` si `n_anom` difiere en un píxel en cualquier parte de la escena de 50 km. Sale
verdadero en **460 de 470 gránulos**, también en 339 de los 370 que no cambian ni etiqueta ni
publicación. El instrumento está saturado y no separa «mismo calor, otra etiqueta» de «otro calor»:
las dos pérdidas cuentan como «otra detección» con el cúmulo idéntico (n_anom 81 → 80 y 74 → 70).

Partición que sí separa (`v3_mismo_pixel.py`), sobre los 100 cambios:

| tipo | n | dónde |
|---|---|---|
| misma fuente, el mismo píxel reubicado (se mueve lo que mide el corrimiento ± 1,5 km) | 36 | todos en el estrato A |
| cambia la fuente del hotspot final (`test1`/`cluster_rescue` contra `eruption`) | 32 | 15 en Láscar, los 12 del control |
| misma fuente `eruption`, otro píxel gana el máximo | 32 | sobre todo A |

Los 36 primeros son el efecto que el probe quería medir, y caen donde el modelo dice. Los otros 64
son la cadena de A46 y la competencia por el píxel más caliente.

## Punto 3. El control: REFUTADO como control; el modelo de corrimiento está incompleto

**El modelo.** El de #828 corrige sólo el eje del barrido: el frame *s* recibe la posición del frame
0,99778·*s* + 2. Eso es exactamente lo que hace `scipy.ndimage.zoom(order=1)` en `_interp_geo`
(`pipeline/process_modis.py:342-349`), que alinea esquina con esquina en vez de poner los nodos del
L1B en 5k + 2. Pero `zoom` hace lo mismo **a lo largo de la traza**: la línea *y* recibe la posición
de la línea 0,998029·*y* + 2 (405/2029 × 5), un corrimiento de 2 − 0,00197·*y* líneas, de +2 km al
inicio del gránulo, 0 al medio y −2 km al final. El modelo no lo tiene.

**La prueba** (`v5_along_track.py`, cenit bajo 30°, n = 157): la componente norte-sur medida contra
|2 − 0,00197·línea| da **r = 0,955**, mediana medida 1,124 km contra 1,142 predicha, residuo mediano
0,087 km. Los casos clave calzan al centésimo: 2026-04-30 línea 386, predicho 1,24, medido 1,213;
2026-04-20 línea 1136, predicho −0,24, medido −0,275; 2026-03-16 línea 1431, predicho −0,82, medido
−0,862. Por cenit (`v4_desplazamiento.py`): bajo 20°, |dn| mediano 1,07 km y |de| 0,47 contra 0,42
predicho; el término del barrido sí está bien, lo que falta es el de la traza. Eso explica el
«1,1 a 1,3 km medido contra 0,4 predicho».

**Consecuencias.**
- La banda por record quedó corta en cenit bajo, que es donde vive la muestra de Láscar: 87 de 470
  gránulos exceden banda + 1 km (18,5 %, sobre el 10 % del criterio 4). Records que debían estar en A
  quedaron en «fuera» o «control».
- Aun así, los 12 cambios del control **no** son reubicación del mismo píxel: los 12 son cambio de
  fuente del hotspot final (11) o cambio del cúmulo (NdC 2026-04-21, cúmulo 8,9 → 0,7 km). Un control
  definido por la distancia del hotspot final al límite no puede controlar una etiqueta que no es
  función de un hotspot fijo. Ni con el modelo corregido sería control.
- Δ de la regla 2 (−49,9 [−153,1; +62,6]) sólo suma A y B summit, que se armaron con el modelo
  incompleto, y excluye por diseño los 22 cambios de los estratos «inmóviles». No es interpretable.

## Punto 4. ¿PIERDE PROTEGIDA es lo que dice el pre-registro? CONFIRMADO por la letra, PARCIAL en su lectura

`evaluar_mxd03.py:164-181` implementa el orden del README (INVALIDO, INCOMPLETO, PIERDE PROTEGIDA,
BANDA CORTA, INDETERMINADO por modelo...). No es INVALIDO (C' = C en 24 de 24). No es INCOMPLETO: el
único error es Tupungatito `MOD021KM.A2026275.0225` (estrato A, negativo limpio, L1B no encontrado),
1 de 29 (3,4 %), ninguna protegida sin medir y los 12 jobs con C'. La regla 1 cuenta pérdidas en
todos los estratos, así que las dos del control bastan. El veredicto por la letra es PIERDE
PROTEGIDA, y el «motivos: -» del resumen se refiere a `motivos_incompleto`, no a los 22 casos del
modelo, que sí están listados en `modelo_falla`.

Lo que el pre-registro no previó: una protegida que se pierde **en el estrato que el propio modelo
declara inmóvil**, por un mecanismo que no es posición. Con los mismos datos se cumplen también
BANDA CORTA (18,5 %) e INDETERMINADO por modelo (22 casos), que el orden tapa. El informe debería
decir los tres. Y el probe no tiene un brazo que perturbe C con un corrimiento chico al azar: sin él
no se puede separar «M es peor» de «la etiqueta de MODIS cambia con cualquier perturbación». La
evidencia apunta a lo segundo: en 2026-04-20 bastaron 0,39 km para que el Test 1 dejara de disparar,
y el saldo de protegidas es 9 ganadas contra 2 perdidas (C publica 9 de 46, M 16 de 46).

## Punto 5. C contra lo guardado: CONFIRMADO en etiqueta y publicación; la detección deriva mucho más

`c_igual_a_guardada` (`probe_etiquetas.py:290-291`) compara sólo `distance_class` y publicación: 462
de 470. Comparando el record entero (`v6_c_vs_guardado.py`), `n_anomalous_pixels` difiere en **248
de 470** y la magnitud del cúmulo en **59 de 470** (la fuente del hotspot final coincide en 470). Ej.:
2026-04-20, 56 píxeles guardados contra 81 en C; 2026-03-16, 51 y 38,0 MW contra 87 y 49,0 MW. Es
deriva de código entre la corrida que guardó el record y el código de hoy (464 de 470 guardados son
Standard, así que no es NRT contra Standard). El README lo declara informativo y no decide, y el
efecto se mide C contra M con el mismo código, así que no invalida el probe; pero «C reproduce
producción» vale sólo para la etiqueta.

Las 8 restantes son todas negativos limpios, ninguna protegida: Chaitén 2026-03-06 07:00 (B summit)
y 2026-04-28 07:55, guardadas publicadas y C no (1→0); Isluga 2026-05-09, 05-18 y 05-19, guardadas
`far` y C `summit` (0→1, mismo cúmulo); Copahue 2026-03-06, Llaima 2026-03-11 y NdC 2026-03-19
cambian sólo la etiqueta (`summit`→`far`, sin publicación en ningún lado), con el cúmulo guardado en
0 MW y el de hoy a 6,9 a 20,7 km. Son deriva, no efecto de MxD03.

## Qué haría falta para cerrarlo

1. Persistir en el probe `triggered_test1`, `test1_k_observed`, `hotspot_dist_km` (post store) y
   `discarded_reason` de cada brazo, y repetir los dos gránulos perdidos para confirmar el mecanismo
   del punto 1.
2. Agregar al modelo de #828 el término de la traza (2 − 0,00197·línea) y rehacer los estratos.
3. Un brazo de ruido: C con un corrimiento chico al azar, para medir cuánto cambia la etiqueta sin
   MxD03.
4. Medir el mismo C contra M con la etiqueta sacada del cúmulo (el flag ya existe): si los 93 cambios
   desaparecen, la decisión sobre MxD03 se separa de la decisión sobre A46.

Nada de esto lo corrí: el probe baja L1B con credenciales de Earthdata y el encargo era sólo lectura.
