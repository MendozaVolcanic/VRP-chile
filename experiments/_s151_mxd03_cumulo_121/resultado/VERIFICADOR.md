# Verificador con contexto limpio: resultado del probe 1.21 (MxD03 y etiqueta desde el cúmulo)

**Veredicto: CONFIRMADO**, con tres matices que cambian cómo se lee (puntos 3, 4 y 6).

Fuentes: artefactos en `C:\Users\nmend\AppData\Local\Temp\claude\probe_121\art\` (runs 39033482528 y
39034846297), artefactos de la 1.17 en `C:\Users\nmend\AppData\Local\Temp\claude\mxd03_117\art\`, el
pre-registro `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s151_mxd03_cumulo_121\README.md`
y los records guardados en el commit `bca47c6ad`. Scripts y salidas en esta carpeta:
`analisis.py` (`analisis_salida.txt`), `comparar_117.py` (`comparar_117_salida.txt`),
`resumen_repro.json` y `evaluar_repro.log`.

## 1. Reproducción: CONFIRMADO

Corrí `evaluar_cumulo.py` sobre los 12 artefactos y el `resumen.json` que sale es **idéntico** al
guardado (comparación de los dos JSON como objetos). Además rehice los números clave con un script
propio que no usa el evaluador (`analisis.py`): 46 protegidas, C publica 9, CC 46, M 16, MC 45, R 10,
RC 46; MC contra C, 0 perdidas y 36 ganadas; M contra C, 2 perdidas y 9 ganadas; R contra C, 4 y 5.
El delta de la principal se descompone así: alertas bajo 1 MW, 38 ganadas y 0 perdidas (−38); negativos
limpios observados +223 y −7 en 365, expandidos por celda a +3.582,5; total +3.544,5. Ninguna celda
quedó sin medir.

## 2. Cobertura: CONFIRMADO

- 12 jobs, un solo commit (`e472c673b1673334f3e287669499ebccb8aade19`) y un solo ref
  (`refs/tags/s151-1.21-probe`) en los 12.
- Cada job trae **exactamente** los gránulos que `poblacion.json` le asigna (comparación de conjuntos,
  job por job). Láscar-1 y Láscar-2 no se solapan.
- 471 pedidos, 470 `ok`. El único que falta es Tupungatito `MOD021KM.A2026275.0225` (estrato A,
  negativo limpio, fuera del censo), con error «no encontrado o no bajado (L1B)», y es el que declara
  `archivo_cmr.json`. Ninguna alerta queda fuera.
- Instrumento: C' corrió en 24 gránulos (2 por job), los 24 iguales a C; el espía vio
  `desde_cluster` al derecho en los seis brazos; el ruido aplicado difiere del pedido en 2 m como
  máximo. El único gránulo sin record es Copahue `MOD021KM.A2026175.0250` en R y RC (los seis brazos
  publican 0 ahí; no toca nada).

## 3. Las pérdidas de protegidas

**M contra C: son las mismas dos de la 1.17**, Láscar Terra 2026-04-20 01:30 (`A2026110.0130`, 1,36 MW)
y 2026-04-30 01:30 (`A2026120.0130`, 1,34 MW). Y los brazos C y M de la 1.21 reproducen los de la 1.17
gránulo por gránulo: misma publicación en los 470, mismos campos salvo la distancia del hotspot final
en 3 (C) y 2 (M) gránulos que no cambian ni etiqueta ni publicación (ver punto 6).

Por qué pierde: **etiqueta (A46), no posición del calor.** Ahora está medido, ya no inferido: con
`_interp_geo` el Test 1 dispara (`test1_k_observed` 4,81 y 3,28) y la fuente final es `test1`, a 0,9 y
0,8 km del cráter; con MxD03 el Test 1 no dispara (2,56 y 2,83), la fuente pasa a `eruption`, el
hotspot salta al borde del Salar a 19,1 y 21,6 km, la etiqueta queda `far` y el tablero no publica. El
cúmulo, con MxD03, queda **más cerca** del cráter (0,23 y 0,48 km) y con la misma magnitud (1,25 y
1,07 MW). MC publica las dos.

**MC contra CC: una sola, Nevados de Chillán Aqua 2026-10-12 07:20** (`MYD021KM.A2026285.0720`), MIROVA
2,18 MW a 2,24 km. Ésta **sí es de posición, pero no del tipo «mismo píxel reubicado»**: cenit 59°,
frame 61 (borde del barrido), corrimiento medido 5,43 km. Con `_interp_geo` el cúmulo es de 6 píxeles,
1,38 MW, a 1,68 km (coherente con los 2,24 km de MIROVA). Con MxD03 la selección anclada al cráter
elige **otro objeto**: 2 píxeles, 1,31 MW, a 9,7 km, casi 11 km al norte del cúmulo de C. Si fueran los
mismos píxeles corridos por el desplazamiento medido, quedarían a unos 4,2 km, dentro del inner de 5.
Con la distancia escalar de MIROVA sólo se puede decir que el cúmulo de M está al menos a 7,5 km del
objeto de MIROVA (diferencia de radios, A93), o sea que no es el mismo. RC no lo pierde (3,7 km). C
tampoco lo publica, por eso la principal no lo cuenta.

## 4. FRÁGIL y el nulo

R pierde 4 protegidas, todas de Láscar y de cenit bajo: 2026-03-11 01:35, 04-05 01:35, **04-30 01:30**
y 05-03 07:45. Con M comparte sólo la del 04-30, así que, por la letra, M es FRÁGIL sólo en esa
(`fragil_pasadas`) y la del 04-20 queda en `perdidas_que_el_nulo_no_pierde`. Las 4 de R tienen el
mismo mecanismo que las de M: el Test 1 o el rescate por cúmulo deja de actuar y el hotspot cae al
Salar (20 a 27 km).

Lectura: **las pérdidas de M no se distinguen del ruido de posición.** Con la etiqueta de producción,
cualquier corrimiento de 0,4 a 1,7 km rompe entre 2 y 4 de las 46 publicaciones protegidas de Láscar,
porque dependen de que una integral cruce un umbral. M contra R da 3 perdidas y 9 ganadas. Del otro
lado, M gana más que el ruido (9 contra 5; publica 16 de 46, R 10, C 9), lo que apunta a favor de
MxD03 pero con n chico y **un solo sorteo de ruido por gránulo**: no hay distribución del nulo, sólo una
realización. Con la etiqueta del cúmulo la posición casi no mueve protegidas (MC contra CC cambia 1 de
46; RC contra CC, 0).

## 5. De dónde salen las ~3.500 publicaciones de más

Son de la etiqueta, no de MxD03: CC contra C da +3.695, RC contra C +3.680, MC contra C +3.545, y MC
contra CC −151 [−590; 289], INDETERMINADO, igual que su nulo (−15).

En los negativos limpios medidos, CC publica 309 de 365 (84,7 %) y MC 303 (83,0 %), contra 87 (23,8 %)
de C (muestra estratificada; en la población C publica 587 de 5.047). Las 223 adiciones de MC:

- **todos los volcanes** (Chaitén 33, Lastarria 28, Planchón Peteroa 28, Isluga 23, Villarrica 23,
  Tupungatito 20, Copahue 18, Llaima 18, PCC 17, Nevados de Chillán 8, Láscar 7) y **los dos
  satélites** (Terra 119, Aqua 104), en todos los estratos, incluido «control»;
- 218 de 223 son la misma figura: C dejó la pasada `far` porque el hotspot de escena está lejos
  (`partial_eruption_hotspot_too_far`, mediana 16 km) y hay un cúmulo dentro del inner;
- magnitud del cúmulo: mediana 0,60 MW, 53 bajo 0,3 MW, 36 en el tope de 5 MW, 69 de un solo píxel.

Contra la predicción: el replay daba 312 publicaciones de CC en esos 365 y se midieron 309. Acuerdo del
replay: 407 de 409 en el resto, 46 de 46 en protegidas, 14 de 15 en la fuente `test1`. El Δ predicho de
CC, +3.829, cae dentro del intervalo medido [3.158; 4.232]. La rama del Test 1 no apagó ninguna
protegida en CC. La predicción se sostiene.

Nota: el intervalo de Wilson por celda de la principal, [−573; 4.373], no decide el signo. Según el
pre-registro es informativo; el intervalo que decide tiene su cobertura medida, así que no cambia el
veredicto.

## 6. Las 8 diferencias de C contra lo guardado

Son las **mismas 8, con valores idénticos, que en la 1.17**: Isluga Aqua 2026-05-09, 05-18 y 05-19
(guardado `far`, hoy `summit` y publica), Nevados de Chillán Terra 03-19, Llaima Terra 03-11 y Copahue
Terra 03-06 (guardado `summit`, hoy `far`, sin publicar en ninguno de los dos), y Chaitén Aqua 03-06 y
04-28 (guardado publica, hoy no). Todas negativos limpios, ninguna protegida.

- **No es el no determinismo de D-16**: dos corridas independientes sobre el mismo L1B dan lo mismo en
  las 8.
- **No es la entrada NRT contra Standard**: los 8 records guardados son `standard`.
- Lo que sí cambia es la detección: hoy salen más píxeles anómalos (Isluga 48, 99 y 64 guardados contra
  71, 143 y 122; Chaitén 37 y 275 contra 67 y 405), coherente con los 248 de 470 que midió la 1.17. Es
  **deriva de código entre el que escribió esos records y el de hoy**; el commit responsable no lo
  identifiqué (SIN VERIFICAR).
- D-16 sí aparece, pero en otro lado: entre la 1.17 y la 1.21 cambia la distancia del hotspot final en
  Copahue 2026-08-22, Llaima 07-31 (C y M) y Nevados de Chillán 07-18 (C), sin cambiar etiqueta ni
  publicación.

## Para decidir MxD03 en producción

- **La etiqueta desde el cúmulo no entra**: EMPEORA por unas 3.500 publicaciones de más, en todos los
  volcanes.
- **MxD03 solo** cae por la letra de la regla 1 (2 perdidas), pero esas dos pérdidas son la cadena
  de etiqueta A46 de Láscar y un corrimiento al azar del mismo tamaño pierde otras 4. El balance es
  indeterminado (−32 [−433; 369]). No queda refutado como arreglo de posición; tampoco hay evidencia de
  que mejore la réplica.
- La única pérdida que sí parece de posición es la de Nevados de Chillán en el borde del barrido, y
  sólo con la etiqueta del cúmulo.

Qué faltaría medir:

1. un nulo con varios rumbos por gránulo (por ejemplo 20), para tener una distribución de protegidas
   perdidas al azar en vez de una sola realización;
2. una vara de posición independiente: el cúmulo MODIS con las dos geolocalizaciones contra el cúmulo
   VIIRS 375 de la misma noche (geolocalización propia) o contra los TIF UTM de MIROVA;
3. por qué el Test 1 de Láscar cruza el umbral con 0,4 km de corrimiento: el problema de fondo es la
   fragilidad de la etiqueta, no MxD03;
4. el caso de cenit alto y borde del barrido (Nevados de Chillán), corrigiendo antes la anisotropía
   del nulo sobre 50°.
