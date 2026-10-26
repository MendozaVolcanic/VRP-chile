# Verificador, segunda vuelta: pre-registro 1.23 (MxD03 sola), head `c101f9cc9`

PR #846. Worktree en `c101f9cc9` (comprobado), CI run 39057051690 `success` sobre ese mismo sha. No edité
ningún repo. Scripts nuevos: `v2_check.py`, `campo_bowtie.py` (y su salida), en
`C:\Users\nmend\AppData\Local\Temp\claude\verif_123\`.

## Veredicto: SELLABLE CON ARREGLOS (uno chico, de texto y de evaluador)

Los dos bloqueantes de la versión 1 quedaron resueltos. Queda uno nuevo, menor: la lectura 5 en el borde
del barrido sigue emitiendo un estado que el instrumento no sostiene, y la anotación que lo advierte no
lo condiciona.

## Lo que comprobé

| punto | resultado |
|---|---|
| tests del PR | 41 pasan (14,7 s) |
| SIERRA con el jacobiano viejo (mutación, `v2_check.py`) | falla de verdad: con ±1, ±2, ±3 y ±4 líneas el módulo sale 0,51, 0,51, 0,61 y 0,81 px; con ±5, 1,000. `test_jacobiano...` además barre 20 fases y exige los dos extremos (< 0,1 y > 1,9) |
| nulo en km | `vector_nulo(desp["km"], ang)`, rumbos geográficos; INVALIDO si el pedido no tiene el km del real. Correcto. Ese INVALIDO sigue siendo de construcción, y el README lo dice |
| lectura 4 con signo | los cuatro estados se alcanzan: MEJOR y SIN DIRECCION en el test del PR; PEOR y MIXTO los produje yo con el mismo armado (`v2_check.py`). Falta un test para PEOR y para MIXTO; no bloquea |
| `invariante_km_salida.txt` | en una grilla regular el km es invariante y el píxel no; con bow tie ninguna de las dos unidades lo es. El README lo dice antes de correr |
| regresiones | ninguna: la vara, el candado, la autenticación sólo con token, la cobertura A108 y el tiempo quedan iguales. `cruces_de_borde` cuesta poco (ventana de ±60 px, 3 radios) |

## El nulo en km en el borde: correcto en la unidad, pero no imita a M

El km es la unidad correcta para la traslación rígida. En el borde, sin embargo, el problema no es la
unidad sino la forma del campo. Con bow tie, MxD03 no es una traslación de `_interp_geo`. Dentro de cada
barrido de 10 líneas, el campo C - M a lo largo de la traza es un diente de sierra: según el modelo
(`campo_bowtie.py`, misma `zoom` del pipeline), en las líneas 2 a 7 casi no hay corrimiento, y en las
líneas extremas del barrido vale ±1,2 km con huella 1,3 (unos 35 a 40°), ±2,2 con 1,55 y ±3,8 con 1,95.
El nulo toma el tamaño de UN píxel, el más cercano al cráter según MxD03. Ese valor depende de la fase
de la línea, y ninguna traslación rígida reproduce el entrevero de líneas que hace M sobre el inner o el
ROI de 25 km. Es un modelo, SIN VERIFICAR sobre un gránulo real, pero coincide con lo que dijo #828: 0,2 a
1 km de terreno y bow tie después de corregir el offset.

**Consecuencia.** Lo que hace la anotación `tamano_del_nulo` (cruces de M contra cruces de los nulos) es
el diagnóstico correcto, y es mejor que mi punto (c). La razón km del nulo contra la de M vale 1 por
construcción, así que no aplicarlo tal cual es aceptable. Pero hoy la anotación no decide nada:
`borde_lectura` emite «MXD03 SALTA MAS / MENOS QUE EL AZAR» en 50-90 sin mirarla, el `print` final
muestra justo esa línea, y el README dice todavía «el borde se contesta sólo con la lectura 5».

## Arreglos antes de sellar

1. Pre-registrar que, sobre 35° de cenit, la lectura 5 y los cortes por cenit son **descriptivos**:
   estado «SIN NULO COMPARABLE (BOW TIE)», con los conteos y `tamano_del_nulo` al lado. También vale una
   regla medida en vez de un umbral inventado: el rango de los cruces de M entre los de los 20 nulos, por
   gránulo. Además, cambiar la frase «el borde se contesta sólo con la lectura 5» por «el borde no se
   contesta con este instrumento».
2. Informar el rango de las reglas 1 y 2 también restringido a cenit bajo 35°, como principal, y dejar
   el total como anotación. El nulo es comparable bajo 35°, y ahí viven casi todas las protegidas de
   Láscar.
3. Menor: agregar a `cruces_de_borde` el círculo de `radius_km` (25 km en Tier A), que es el ROI de escena.

## Lo que Nicolás debe saber al sellar

- Por la letra, MxD03 vuelve a dar PIERDE PROTEGIDA.
- Lo que puede decidir el probe: si la posición es mejor (vara, cenit bajo y medio, casi seguro MXD03 MAS
  CERCA por #828) y si las pérdidas de Láscar son azar o señal de una posición mejor (lectura 4 con signo).
- El borde del barrido (el caso Chillán) no lo contesta, porque ahí MxD03 no se parece a ninguna
  traslación de la grilla.
