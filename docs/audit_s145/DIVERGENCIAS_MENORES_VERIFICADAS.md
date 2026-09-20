# S145: las cuatro divergencias "menores" (D23, D24, D26, D29), verificadas

> Auditoría read-only sobre `origin/main` en `ec8816c12` (2026-09-20T02:16:30-03:00).
> Ningún número de este documento está escrito a mano: cada uno sale de un script de
> `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s145_menores\`
> que persiste su salida en JSON al lado. No se tocó `pipeline/`, no hay commits ni ramas.

## Por qué esta revisión

Las cuatro entradas se registraron en S138 con el impacto calificado de menor o nulo. En varias, ese
calificativo no salió de una medición sino de un razonamiento, y este proyecto ya sabe lo que cuesta
eso: la regla A95 dice que un corolario que cierra un frente hereda las premisas de la lectura con
que se derivó, y la A87, que un flag apagado no prueba que el problema se haya ido. Lo que se busca
acá es una cosa concreta: si el "efecto nulo" de alguna se apoya en una premisa que después se
refutó, hay un frente apagado por error.

## Cobertura primero

| | ¿se cubrió a fondo? | qué quedó afuera |
|---|---|---|
| **D23** | Sí | La magnitud sobre gránulos reales. Los records guardan conteos, no máscaras: el solape entre la máscara del Test 1 y la del primer pase no se reconstruye desde disco. |
| **D24** | Sí | El conteo real de píxeles saturados. Un píxel saturado ya es NaN cuando el record se escribe, así que es invisible por construcción a cualquier medida sobre `data/`. |
| **D26** | Sí, es el hallazgo principal | El pool del **segundo** pase no se persiste en ningún campo. La medición usa el pool del **primer** pase como proxy, y se declara como tal en cada número. |
| **D29** | Sí, con control sintético | Cuántos records reales cambia. El efecto se midió en dirección y tamaño sobre escenas construidas, no sobre gránulos. |

Las cuatro siguen vigentes en el código de hoy: los cuatro mecanismos se localizaron por contenido,
no por número de línea (`01_vigencia.py` → `01_vigencia.json`).

## La tabla

| | ¿medido o estimado? | premisa de la que depende el veredicto | ¿vigente hoy? | ¿se sostiene el veredicto? |
|---|---|---|---|---|
| **D23** | Medido en frecuencia, declarado SOSPECHA en magnitud (y el catálogo lo dice) | Que el corpus no contenga una colada de varios píxeles con interior | Sí: `process_modis.py:890`, `process_viirs.py:1299`, `process_viirs_mod.py:878` | **Sí**, y ahora con cota: en 24.023 records de VIIRS 375 sólo **7** tienen píxeles K1 que por conteo no caben en el primer pase |
| **D24** | **Estimado, y con el instrumento equivocado** | `sanity_cap_tocado = 0`, que mide otra cosa | Sí: `process_modis.py:246, 252, 557` | El veredicto ("invisible hoy") **se sostiene, pero por otra razón**: el píxel más caliente del corpus está a **115,6 K** de la saturación de la banda 21 |
| **D26** | **Estimado por silogismo**, no medido | "El piso C1 gobierna", tomada de S136 | Sí: `detection_context.py:923` contra `81` y `492` | **NO en VIIRS.** La premisa se midió sólo sobre el dNTI; en el dETI el piso no gobierna y hay **7.164** records expuestos |
| **D29** | Estimado ("probablemente mejora el fondo") | Ninguna, no había medición detrás | Sí: `detection_context.py:704, 770, 779`, sin flag y sin caller que lo apague | **Sí**: el efecto máximo medido es **0,32 · C1** y nunca cambia una detección |

---

## D26: el hallazgo principal. La premisa se midió sobre la mitad del test

### El fenómeno, primero

El paso de detección contextual le pregunta a cada píxel dos cosas a la vez, y las dos tienen que
dar que sí: que el píxel destaque del vecindario en el índice térmico normalizado (Test 2, el dNTI)
**y** que destaque en el índice corregido por la regresión de la escena (Test 3, el dETI). Cada una
de esas dos preguntas tiene su propio umbral, y cada umbral tiene dos formas de cumplirse: un piso
absoluto fijo (C1) o un contraste estadístico contra la escena (mu + C2 · sigma). Como basta con
superar una de las dos, el umbral que manda es **el menor de los dos**, y por eso el código escribe
`min(C1, mu + C2 · sigma)`.

D26 denuncia que el segundo pase calcula ese `mu` y ese `sigma` sobre un pool sucio: sin sacar los
píxeles de borde, ni los de dNTI muy negativo, ni los del Test 1, que el paper sí excluye (y el
primer pase sí excluye, `detection_context.py:492`). El catálogo lo cierra con un razonamiento
limpio: si el piso C1 siempre es el menor, ensuciar el sigma no mueve el umbral, luego el efecto es
nulo. La cadena entera cuelga de esa frase: **"el piso gobierna"**.

### Qué se midió realmente en S136

El script que produjo esa frase es
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s136\que_rama_manda.py`.
Se corrió de nuevo en esta sesión y reproduce sus números. Y mirando lo que lee, usa **sólo**
`diag_mu_dnti` y `diag_sd_dnti`. Nunca toca `diag_mu_deti` ni `diag_sd_deti`. O sea: midió el
Test 2 y se lo atribuyó a los dos. El Test 3, que va en conjunción y por lo tanto puede ser el que
decide, quedó sin medir.

La medición de esta sesión (`02_d26_piso_vs_sigma.py` → `02_d26_piso_vs_sigma.json`), sobre el corpus
completo de `data/mirova_equivalent/`, ventana 2025-02-15 a 2026-09-20, con los umbrales efectivos
del perfil operacional (C1 cumbre 0,003 / C1 escena 0,010; C2 5 y 10):

| bucket | records con diag | piso gobierna en los 4 umbrales | al menos un umbral lo fija el sigma |
|---|---|---|---|
| MODIS | 12.166 | **12.166 (100 %)** | 0 |
| VIIRS 375 | 21.568 | 8.898 (41,3 %) | **12.670 (58,7 %)** |
| VIIRS 750 | 23.833 | 5.970 (25,0 %) | **17.863 (75,0 %)** |

Desglosado por umbral, el que rompe la premisa es el **dETI de escena**: el sigma lo gobierna en el
58,6 % de VIIRS 375 y el 74,9 % de VIIRS 750. Y en el ROI de cumbre, que es el que publica, el dETI
lo gobierna el sigma en el 7,4 % y el 16,6 %. El dNTI de cumbre, en cambio, da 99,889 % y 99,853 %:
es exactamente el "99,9 % de VIIRS" que quedó escrito en `pipeline/profile.py` y de ahí pasó al
catálogo. El número era correcto; lo que estaba mal era lo que nombraba.

### El sustrato existe, así que la premisa importa

Antes de discutir el efecto hay que ver si el paso llega a ejecutarse
(`04_d26_exposicion_segundo_pase.py`). El segundo pase **sí** agrega píxeles a la máscara publicada:
en el 98,3 % de los records de MODIS (818.742 píxeles), el 30,3 % de VIIRS 375 y el 22,6 % de
VIIRS 750.

Cruzando las dos condiciones (`05_d26_interseccion.py`), los records donde el segundo pase recaptura
**y** además el umbral no lo fija el piso:

| bucket | expuestos | de ésos, en un umbral de **cumbre** |
|---|---|---|
| MODIS | **0** | 0 |
| VIIRS 375 | 3.704 (17,2 %) | 548 (2,5 %) |
| VIIRS 750 | 3.460 (14,5 %) | 1.041 (4,4 %) |

**En MODIS el veredicto del catálogo es correcto y queda medido: el piso gobierna los cuatro
umbrales en el 100 % de los records, así que el pool sucio no puede mover nada.** En VIIRS el
"efecto nulo" es falso: hay 7.164 records donde el umbral depende del pool que D26 denuncia y el
segundo pase está agregando píxeles, y 1.589 de ésos en el ROI de cumbre.

### Dos salvedades honestas, las dos en la misma dirección

1. **El proxy.** `diag_mu_*` y `diag_sd_*` salen de `fp_diag`, o sea del primer pase
   (`process_modis.py:1540-1549`). El pool del segundo pase no se persiste. Lo medido es el régimen
   de cada escena, no el pool exacto que D26 denuncia.
2. **El proxy es conservador.** El control sintético M4 de S138
   (`experiments/_s138_audit/eje2/01_controles_sinteticos_resultado.json`) muestra que el sigma del
   **primer** pase también se mueve con el outlier, de 0,00116 a 0,00378 (×3,3), aunque menos que el
   del segundo (0,00085 a 0,01044, ×12,2). El catálogo dice "mientras el primer pase lo excluye", y
   eso vale para la pertenencia al pool pero no para el sigma resultante: el outlier corre la media
   de 8 vecinos de sus vecinos. Como el sigma persistido ya viene algo inflado, el `mu + C2 · sigma`
   que usé está sobreestimado, y por lo tanto el conteo de records donde el sigma gobierna es un
   **piso**, no un techo.

### Y la premisa además está bajo sospecha por el otro lado

Aunque el piso gobernara siempre, "efecto nulo **bajo la conectiva `min`**" hereda la conectiva. Hoy
la conectiva es `min` (`detection_context.py:525` y `943`, con
`ENABLE_TESTS_23_PROSE_BRANCH = False` verificado en el perfil efectivo), así que la premisa se
cumple. Pero el propio S136 midió que `min` **no reproduce a MIROVA**: en los tres casos negativos
del Apéndice A del paper detectamos donde el autor publica que su algoritmo no detecta
(`experiments/_s136/VEREDICTO_CONECTIVA.md`). La rama alternativa tampoco sirve (pierde 4 de 6
positivos), y por eso el frente se cerró. O sea: D26 descansa sobre una conectiva que el proyecto
sabe defectuosa, y el catálogo no lo dice. Esto es literalmente el caso que describe A95, y el
frente que A95 nombra como "pool de mu y sigma" **es** D26.

### Qué hacer con D26

Cambiar el encabezado. Hoy dice *"ABIERTA, efecto nulo bajo la conectiva `min`"*. Lo medido sostiene:
*"ABIERTA. Efecto nulo MEDIDO en MODIS (el piso gobierna los 4 umbrales en 12.166 de 12.166 records).
En VIIRS NO es nulo: el piso no gobierna el dETI y hay 3.704 records de I-band y 3.460 de M-band con
recaptura activa y umbral dependiente del pool, 1.589 de ellos en cumbre"*. La gravedad de 1 vale
para MODIS; para VIIRS no está medida y no corresponde inventarla acá.

---

## D23: el veredicto se sostiene, y ahora con cota

El mecanismo está vigente: el K1 se calcula (`process_modis.py:666`), entra a `combine_hot_paths`
(`:828`), y la línea siguiente `hot_mask_2d = fp_hot` (`:890`) pisa ese resultado con la salida del
primer pase. Igual en `process_viirs.py:1299` y `process_viirs_mod.py:878`. El `test1_mask` que se le
pasa al primer pase es `None` de hecho, porque `ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK = False`.

La frecuencia del catálogo se reproduce sobre el corpus de hoy (`03_d23_test1_exposicion.py`):

| bucket | records con K1 | % | píxeles K1 | máx. en un record | K1 fuera del primer pase (piso) |
|---|---|---|---|---|---|
| MODIS | 11 / 12.699 | 0,087 % | 20 | 4 | 0 |
| VIIRS 375 | 320 / 24.023 | 1,332 % | 520 | 25 | 7 records, 8 píxeles |
| VIIRS 750 | 28 / 23.833 | 0,117 % | 69 | 10 | 0 |

El "K1 fuera del primer pase" es un piso duro, no el total: cuando `n_nti_path` supera a
`n_first_pass_pixels`, sobran píxeles K1 que el primer pase no pudo contener. Donde los conteos no
se contradicen, no se puede decidir desde disco.

Lo importante es el fenómeno: D23 muerde en el **interior** de una colada, donde los píxeles están
rodeados de píxeles igual de calientes y por eso no destacan de sus vecinos. Para que haya interior
hace falta un cúmulo. En todo el corpus hay **8 records de VIIRS 375 y 1 de VIIRS 750** con 9 o más
píxeles K1, y ninguno en MODIS. El corpus, simplemente, no contiene el evento donde esto importa.
El catálogo ya lo dice con todas las letras ("la magnitud del efecto es SOSPECHA") y esa etiqueta es
la correcta. Sugerencia menor: agregarle la cota de 7 records y el dato de que el máximo observado
son 25 píxeles K1, para que la próxima sesión no tenga que volver a contarlo.

---

## D24: el veredicto se sostiene, pero la evidencia que lo respalda mide otra cosa

El mecanismo está vigente: `INVALID_SI_THRESHOLD = 32767` (`process_modis.py:246`),
`rad[dn > INVALID_SI_THRESHOLD] = np.nan` (`:252`), guard secundario sobre BT de 500 K (`:557`).

**El problema es la evidencia.** El catálogo respalda el "invisible hoy" con
`sanity_cap_tocado = 0`. Ese contador se prende cuando el VRP supera 50 GW
(`pipeline/store.py:130-144`): es el detector del bug F28 de S73, cuando los píxeles saturados **se
colaban** y hacían explotar la magnitud a 695.431 MW. Con el fix vigente pasa lo contrario: el píxel
saturado se vuelve NaN y la magnitud **baja**. El tope de cordura no puede prenderse por esta causa,
así que un cero ahí no dice nada sobre D24. Es la familia A92: el instrumento mide algo distinto de
lo que dice medir, y da verde por la razón equivocada.

El instrumento que sí corresponde es cuánto se acerca la escena a la saturación de la banda primaria
(`06_d24_saturacion.py`). Hoy la primaria es la 21 (`ENABLE_MODIS_B22_PRIMARY = False`), que satura
entre 450 K y 500 K según `docs/F28_SATURATION_INVESTIGATION.md`. Sobre los 12.699 records de MODIS:

- mediana de la BT MIR máxima: **281,0 K**; p99: 295,2 K; p99,9: 303,3 K
- **máximo de todo el corpus: 334,4 K** (Nevados de Chillán, 2025-02-28 02:05, 152,9 MW, 27 píxeles)
- margen al umbral nominal de la banda 21: **115,6 K**

O sea: el corpus no tiene ningún paroxismo cerca del régimen donde D24 muerde, y el veredicto
"invisible hoy" queda en pie, ahora con el instrumento correcto. **Pero hay un detalle que merece
quedar anotado**: el margen a la saturación de la banda **22** es de **0,6 K**. La banda 22 satura a
335 K, y el récord del corpus es 334,4 K. Con la configuración de hoy eso no importa, porque la
banda 22 es sólo el respaldo. Si se adoptara D21 (que es la lectura literal del paper: banda 22
primaria, banda 21 sólo donde la 22 satura), el caso de saturación pasaría a ser frecuente en los
eventos energéticos. La buena noticia es que en esa dirección `merge_mir_bands` hace lo correcto: con
`b22_primary=True`, el NaN de la 22 cae a la 21, que es exactamente la regla de Coppola. El agujero
de D24 es específico de la configuración de hoy, donde el NaN de la 21 cae a una banda 22 que saturó
165 K antes. Conviene anotar esa interacción en D24 y en D21.

---

## D29: el veredicto se sostiene, y era el único medible sin gránulos

El mecanismo está vigente y sin control externo: `iterative_refit: bool = True`
(`detection_context.py:704`), el bloque de refit en `:770`, el criterio de 3 sigma en `:779`. Ningún
caller lo pasa: los tres procesadores llaman a `compute_eti_scene_quadratic` sin ese argumento
(`process_modis.py:782`, `process_viirs.py:1173`, `process_viirs_mod.py:772`), así que corre siempre
en True. No tiene flag de perfil, como dice el catálogo.

Es la única de las cuatro que se puede medir sin reprocesar gránulos, porque vive en una función
pura cuyo parámetro se puede apagar desde afuera sin tocar el pipeline. `07_d29_refit.py` construye
escenas sintéticas físicamente (campo de BT del TIR con gradiente y ruido, radiancia MIR de Planck
del mismo BT, más un cúmulo con fracción sub-píxel a 700 K), computa el NTI con la función real del
pipeline y corre la regresión real con refit y sin refit.

La dirección es la esperada: el refit saca del ajuste los píxeles calientes, la parábola se queda en
el terreno frío, y el exceso del cúmulo sale **mayor**. O sea, el refit nos hace detectar **más** que
el ajuste único del paper, no menos. El tamaño:

| % de escena caliente | diferencia en el ETI del cúmulo, en unidades de C1 cumbre |
|---|---|
| 0,003 % a 0,15 % | 0,00 a 0,02 |
| 0,6 % | 0,01 a 0,07 |
| 2,8 % | 0,07 a **0,32** |
| 11 % | 0,00 a 0,03 |

En ningún caso cambia la decisión: el cúmulo supera C1 con refit y sin refit en las doce escenas. Lo
que sí hace el refit es mantener el fondo centrado en cero: sin refit, con 900 píxeles calientes en
la escena, el ETI mediano del fondo se corre a -0,0006 (0,2 · C1) y con 3.600 a -0,0025 (0,8 · C1).
Se probó además la objeción obvia, que un refit a 3 sigma sobre ruido gaussiano casi no tiene a quién
sacar: se repitió con una banda de cirrus que corre el NTI del 5 %, el 18 % y el 35 % de la escena, y
la diferencia máxima baja a **0,01 · C1**.

Conclusión: D29 es menor, y ahora lo es con una medición en vez de un "probablemente". Vale agregar
un matiz al catálogo: no es que "probablemente mejore el fondo", es que **mejora el fondo en una
cantidad que nunca alcanza el piso de decisión**, y que el signo del efecto va del lado de detectar
de más, que es el lado del problema conocido (A98, la brecha con MIROVA es sobre-publicación).
Limitación declarada: es sintético. No dice cuántos records reales cambia.

---

## Resumen de una línea por divergencia

- **D23**: vigente, correctamente etiquetada como sospecha. Cota nueva: 7 records de 24.023 en
  VIIRS 375, y el corpus no contiene el evento donde el mecanismo muerde.
- **D24**: vigente, veredicto correcto por una razón distinta de la escrita. La evidencia del
  catálogo (`sanity_cap_tocado`) mide el fenómeno contrario. Margen real: 115,6 K.
- **D26**: vigente. **El "efecto nulo" es válido en MODIS y falso en VIIRS.** La premisa se midió
  sólo sobre el Test 2; en el Test 3 el piso no gobierna. 7.164 records expuestos, 1.589 en cumbre.
- **D29**: vigente, menor, ahora medida: 0,32 · C1 en el peor caso sintético y ninguna decisión
  cambiada.

## Scripts y salidas

Todos en `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s145_menores\`:

| script | salida | qué responde |
|---|---|---|
| `01_vigencia.py` | `01_vigencia.json` | dónde está hoy cada mecanismo, buscado por contenido |
| `02_d26_piso_vs_sigma.py` | `02_d26_piso_vs_sigma.json` | cuánto gobierna el piso C1 en los 4 umbrales |
| `03_d23_test1_exposicion.py` | `03_d23_test1_exposicion.json` | frecuencia del Test 1 y píxeles fuera del primer pase |
| `04_d26_exposicion_segundo_pase.py` | `04_d26_exposicion_segundo_pase.json` | si el segundo pase recaptura algo |
| `05_d26_interseccion.py` | `05_d26_interseccion.json` | records con recaptura Y umbral dependiente del sigma |
| `06_d24_saturacion.py` | `06_d24_saturacion.json` | distancia del corpus a la saturación de cada banda |
| `07_d29_refit.py` | `07_d29_refit.json` | control sintético del refit, con y sin cola pesada |
