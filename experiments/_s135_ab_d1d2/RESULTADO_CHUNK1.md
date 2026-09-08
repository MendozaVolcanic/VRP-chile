# A/B de D1 y D2 — resultado del primer tramo

> Ventana 2026-06-01 → 2026-07-15, run 34173711390, **30 de 30 jobs en verde**. Criterio de
> `docs/PREREGISTRO_AB_D1_D2_S135.md` con la decisión de Nicolás del 2026-09-07: cero pérdidas
> sobre lo que MIROVA entrega, y ante una diferencia entender el mecanismo en vez de descartar el
> brazo. Todos los números salen de `evaluar_ab.py` → `resultado_chunk1.json`. El segundo tramo
> (07-16 → 08-31, run 34208191011) se agrega encima y el veredicto final se recalcula sobre la
> ventana completa.

## Antes del veredicto: un brazo no había mirado lo mismo

El primer cruce dio cuatro pérdidas del brazo B, todas en Puyehue. No eran del algoritmo: **ese
job procesó 149 pasadas contra 203 de los otros cuatro**, y las cuatro «noches perdidas» eran
días que nunca miró. La causa está en su propio log: el cortacircuitos de búsqueda de CMR (A64,
S116) saltó por un `ConnectionResetError` de NASA y, por diseño, se salteó todas las búsquedas
restantes de esa corrida. Degradó con gracia, que es lo que debe hacer, pero dejó al brazo con
menos datos.

Es el caso 3 del pre-registro —la entrada difiere— y es un defecto del experimento, no del
sistema. El job se relanzó y el evaluador ahora **verifica la paridad de cobertura antes de
comparar nada**: un volcán cuyos brazos no procesaron las mismas pasadas queda fuera del
veredicto y se lista aparte. Sin ese control, el resultado habría dicho que apagar `keep_peak`
pierde cuatro noches en Puyehue, que es falso.

## El cuadro, con los cinco volcanes de cobertura pareja

| brazo | pierde noches | quita el artefacto | paridad | veredicto |
|---|---|---|---|---|
| A control | 0 | — | 0,649 | — |
| **B sin `keep_peak`** | **0** | **100 %** | 0,649 | **cumple los tres** |
| C sólo segundo pase | 0 | **−57,9 %** | 0,649 | no cumple |
| D ambos (el más fiel) | **5** | 100 % | 0,655 | pierde cinco |
| E segundo pase apagado | 0 | **−57,9 %** | 0,643 | no cumple |

Universo: 136 noches confirmadas (Isluga 38, Lastarria 30, Láscar 26, Planchón-Peteroa 23,
Tupungatito 19), después de excluir las pasadas diurnas y las coincidencias de fecha con objetos
distintos.

**Arreglar sólo el segundo pase empeora el problema.** Los brazos C y E producen un 58 % **más**
registros de nivel base falso que el control. Al condicionar o apagar el segundo pase, el camino
contextual deja de ganar la selección y el Test 1 pasa a ser la fuente, con su píxel único. El
artefacto no se reduce: cambia de rama y se multiplica. Es el argumento más fuerte contra tocar
D2 sin tocar D1.

## Las cinco pérdidas del brazo fiel son un solo mecanismo

Investigadas una por una con `investigar_perdidas.py`, comparando contra lo que MIROVA publicó
esa noche y midiendo las distancias desde su centro de grilla:

| volcán y noche | pasada que MIROVA confirma | primer pase | Test 1 | recaptura | la sostienen |
|---|---|---|---|---|---|
| Isluga 01-jul | 05:42 NOAA-21 | 0 px | 89 px | 1 | B, C, E |
| Lastarria 02-jul | 06:18 NOAA-20 | 0 px | 82 px | 3 | B, C, E |
| Planchón-Peteroa 22-jun | 06:12 NOAA-20 | 1 px | 65 px | 1 | B, C, E |
| Planchón-Peteroa 26-jun | 05:42 NOAA-21 | 0 px | 98 px | 1 | B, C, E |
| Tupungatito 07-jul | 05:36 NOAA-21 | 2 px | 96 px | 1 | B, C, E |

**Cinco de cinco, en cuatro volcanes, con fuentes físicas distintas** —el cráter de Isluga, el
campo fumarólico del Lazufre, el complejo multicráter de Planchón-Peteroa, el glaciar de
Tupungatito— y siempre lo mismo: el contraste contra vecinos no marca nada, el Test 1 integrado
sí encuentra la señal con decenas de píxeles, y lo que llega a publicarse depende de `keep_peak`
o del segundo pase suelto. Cuando se quitan los dos, no queda nada.

En dos de los casos la magnitud lo confirma sin margen de duda: Lastarria publica 0,057 MW
contra los 0,06 de MIROVA, y Planchón-Peteroa 0,098 contra 0,06 con las fuentes a 2,04 y
2,02 km del mismo punto.

## Qué se concluye y qué no

**Se concluye** que el eje del experimento no contiene la solución. `keep_peak` encendido
fabrica el nivel base falso; apagado, junto con el segundo pase arreglado, pierde señal que
MIROVA confirma. Y arreglar sólo el segundo pase empeora las dos cosas. El brazo B cumple los
tres criterios en este tramo, pero lo hace apoyándose en un segundo pase que sabemos infiel al
paper: es el menos malo del eje, no una solución.

**No se concluye** todavía nada definitivo: falta el segundo tramo de la ventana, y Puyehue
quedó fuera hasta que se re-corra. El veredicto se recalcula con todo junto.

**La hipótesis que dejan los cinco casos** sigue siendo la misma que apareció con el primero, y
ahora con cinco: que el Test 1 integrado no debería intersectarse con la máscara contextual. Es
un camino de detección propio en Coppola, no un candidato a filtrar. Si su cúmulo se formara
sobre el footprint completo —entre 65 y 98 píxeles en estos casos— habría detección sin
necesitar ni `keep_peak` ni el segundo pase suelto. Eso se mide después, y pasa por las tres
preguntas de la misión antes que por cualquier flag.
