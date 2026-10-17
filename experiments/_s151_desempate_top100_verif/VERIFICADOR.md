# Verificador con contexto limpio: PR #844 (desempate del top-100)

Rama `loop/1.22-desempate-top100`, cabeza `ba7209131`, base y tag defensivo `pre-s151-desempate-top100` = `4943bfb79`.
Fecha: 2026-10-17. No edité el repo ni mergeé. Todo lo que corrí vive en `C:\Users\nmend\AppData\Local\Temp\claude\verif_844\`.

## Veredicto: MERGEABLE CON ARREGLOS

El código es correcto y hace lo que dice. Los arreglos son de alcance y de texto, no de lógica:
sacar el commit cosmético a otro PR y corregir tres afirmaciones del cuerpo (abajo). La decisión de
fondo es de Nicolás (A45): si acepta fijar por convención una elección que hoy hace la CPU, sabiendo
que en unos 29 records históricos esa elección decide si se publican.

## Qué pasa físicamente, antes del código

MODIS entrega la radiancia como enteros escalados, así que la temperatura de brillo toma valores
discretos. Con el área de píxel fija y el fondo como un solo número, dos píxeles con el mismo entero
tienen exactamente la misma potencia. Cuando el píxel más caliente de la escena está empatado con
otro, el pipeline tiene que elegir uno como "hotspot", y esa elección decide la etiqueta
cráter/lejana y, por el rescate de `store.py`, a veces la magnitud. Hasta hoy la elegía el algoritmo
de ordenamiento de numpy, que cambia según las instrucciones del procesador del runner. El PR la
fija por posición en la grilla (fila y luego columna), que es arbitraria pero siempre la misma.

## 1. Mecanismo: REPRODUCIDO

- `orden_por_cpu.py` en este computador (numpy 2.4.4, con AVX-512): con y sin
  `NPY_DISABLE_CPU_FEATURES=X86_V3` el top-100 del `argsort` por defecto cambia
  (md5 `61acf935b9` contra `0d7e87f5ec`); `kind="stable"` y `lexsort` dan `fd739f8459` en las dos.
- Pares entre intentos, con un criterio propio (`pares_independiente.py`, `pares_detalle.py`): la
  secuencia de valores (vrp_mw, bt_k) del top-100 es idéntica puesto a puesto en 94 pares, y en 63 el
  multiconjunto de kept + discarded es idéntico (un empatado cruzó `radius_km`). O sea, **ninguna**
  diferencia de lista se explica por otra cosa que el empate.
- Diferencias con el autor, menores: cuento **157** pares MODIS con algún campo no diagnóstico
  distinto, no 153. Los 4 extra: 3 son diferencias de 1 ulp en `final_hotspot_lat` (aritmética, no
  empate) y 1 es Llaima Terra 2026-09-24 02:05, con el hotspot de escena a 24,06 km contra 7,1 km y la
  lista guardada idéntica (fuente `test1`, la lista de la ruta eruptiva no se guarda). El
  clasificador del autor no lo ve porque salta los pares con lista y `vrp_mw` iguales. VIIRS: 2 pares
  de 26.793, uno V375 (orden) y uno V750 (Tupungatito, un empatado a 29,8 km contra 22,8 km, cambia
  `vrp_mir_mw` 172,12 contra 173,68). Coincide con el PR.
- Los 2 casos de `vrp_mw` distinto (Llaima 2026-10-06, Copahue 2026-06-18) **no se pueden comprobar
  como empate desde el record**: la lista que lo probaría no se guarda. Son consistentes con el
  mecanismo, no demostrados.

## 2. Diseño

- `lexsort((cols, rows, -vrp))` es correcto: NaN al final como antes, y como `hot_rows/hot_cols`
  salen de `np.where` (orden fila-mayor), equivale a `argsort(kind="stable")`. Es uno de los órdenes
  que el código ya podía producir.
- ¿Flag? Mi lectura: no hace falta y no serviría. A45 exige tag y el sí de Nicolás, no un flag. Un
  brazo "apagado" no es un comportamiento definido, es la CPU de turno: como control de un A/B mide
  ruido. Lo que sí vale es medir el efecto antes (punto 4).
- Otros desempates revisados leyendo el código: `np.argmax`/`nanargmax` (primera ocurrencia por
  contrato), `list.sort` de `clustering.py` y `store.py` (estables sobre entrada determinista),
  `store.py:296` y `vrp_regimes.py:378` (`max` con clave, primera ocurrencia sobre lista ya
  ordenada). **Queda uno**: `pipeline/regrid.py:117`, `np.argsort(-d2[validas])` sin desempate, mismo
  patrón; hoy inerte (`ENABLE_UTM_REGRID = False`, leído de `pipeline.profile`). No bloquea, pero
  quien encienda la grilla UTM hereda el problema.
- **"Independiente de la CPU" es demasiado fuerte.** Con el arreglo, regenerar el golden S142 sin
  AVX2 sigue cambiando `diag_mu_deti`, `diag_sd_deti`, `diag_mu_dnti` y `diag_sd_dnti` (hasta 4e-5
  relativo con AVX2 apagado; 1e-9 entre runners reales). Ninguna lista ni decisión cambió en mis
  corridas, pero la aritmética sigue dependiendo de la CPU. El PR lo dice en "Sin verificar"; el
  título no.

## 3. El test: FALLA SIN EL ARREGLO Y CORRE EN EL CI

- En una copia con el arreglo revertido (`copia_sin\`): 6 de 9 fallan (los dos de comportamiento y
  los cuatro de fuente). Con el arreglo (`copia_con\`): 9 de 9 pasan.
- CI (run 39045362736, `-q`): ubiqué los 9 por posición de colección (puestos 719 a 727 de 2.006);
  caen en las líneas de puntos 10 y 11, sin `s`. **Corrieron y pasaron**, incluido el control de
  instrumento, que se habría saltado si el runner no mostrara la dependencia.
- Defecto menor: en la escena MODIS sintética el hotspot es **el mismo** con y sin SIMD también sin
  el arreglo (`escena_hotspot.py`); sólo cambia el top-100. La aserción del hotspot no discrimina, y
  el cuerpo del PR dice "antes del arreglo da OTRO hotspot", que en este computador es falso.

## 4. Efecto: reproducido, pero el 50 es 29

`efecto_corpus.py` da exacto 13.353 / 5.747 (43,0 %) / 1.425 (10,7 %) / 50. Pero **22 de los 50
no pueden cambiar de etiqueta**: tienen entre los descartados un píxel con más VRP que el empate, a más
de 25 km, que ya es el hotspot y deja la clase en `far` (`c50_desglose.py`, los 22 con
`final_hotspot_dist_km > 25`). Contando el grupo empatado sobre kept + discarded salen **29**
candidatos (28 de los 50 más uno con el compañero de empate entre los descartados).

¿Hacia dónde? Estimación SIN reprocesar (`direccion_estimada.py`), suponiendo que la fila es el orden
de barrido (Terra de noche sube, Aqua de noche baja; el bow-tie lo vuelve aproximado): **11 de los 29
cambiarían**, 9 de `far` a `summit` (se publicarían, varios con 5,0 MW, el tope D9: Isluga 4,
Llaima 3, Láscar 1, Tupungatito 1) y 2 de `summit` a `far` (dejarían de publicarse: PCC 2025-09-25,
Tupungatito 2026-07-08). Es SOSPECHA. Y el PR no reprocesa el histórico: el efecto real es hacia
adelante, en la misma proporción.

Cómo medirlo antes de adoptar: reproceso acotado en GitHub Actions (MODIS no corre en Windows), perfil
con `data_subdir` propio, sobre las pasadas de los 29 más un control de pasadas con empate sin cruce y
sin empate. Dos brazos: (fila, columna) ascendente, el del PR, y descendente, sólo experimental. Cada
brazo dos veces en runners distintos (D-13). Criterio pre-registrado: cuántos records cambian
publicación, clase o `vrp_mw` entre los dos brazos (eso es lo que la convención decide), y cruzar esos
records con la referencia de MIROVA (A119) para ver si las publicaciones nuevas caen en negativos
limpios (A98).

## 5. Commit cosmético

AST idéntico con las docstrings vaciadas en los 4 archivos (`ast_igual.py`); las constantes que no
son docstring no cambian, y cada archivo conserva su número de líneas (las citas `archivo:línea`
siguen valiendo). Pero son 229 de las 278 líneas agregadas en `pipeline/`: sin él, el diff de
producción queda en 49 más y 7 menos. **Recomiendo sacarlo a un PR aparte.**

## 6. Golden S142: bien

Regenerado en 4 condiciones (`golden_{con,sin}_{simd,nosimd}.json`). Código viejo con SIMD = golden de
`main`; código nuevo con SIMD = golden del PR; la única diferencia es el intercambio de 2 píxeles
empatados (0,8527 MW, 300 K) de `v375 foco_3x3|kernel=False`, que quedan en orden fila-mayor. Con el
código viejo y sin SIMD el orden también cambia: el golden viejo dependía de la CPU. El "8 píxeles"
del mensaje del commit es inexacto (el grupo empatado son 8, se mueven 2); el cuerpo del PR ya lo
corrige.

## Lo que Nicolás debe saber

1. El arreglo no mejora la física: congela una elección arbitraria que hoy hace el procesador.
2. En ~0,2 % de los records MODIS (29 de 13.353) esa elección decide la publicación, y la estimación
   apunta más a publicar que a callar, con varios de 5,0 MW (tope D9).
3. Después del merge, un A/B no puede mezclar brazos corridos antes y después: los empates los
   distinguen.
4. Queda un sitio igual en `regrid.py:117`, inerte hoy.

## Archivos

Scripts: `pares_independiente.py`, `pares_detalle.py`, `ast_igual.py`, `c50_desglose.py`,
`direccion_estimada.py`, `escena_hotspot.py`, copia de `orden_por_cpu.py` y `efecto_corpus.py`.
Salidas: `ci_log.txt`, `collect.txt`, `c50_desglose.txt`, `direccion_estimada.txt`,
`golden_*.json`. Copias del pipeline: `copia_con\`, `copia_sin\`.
