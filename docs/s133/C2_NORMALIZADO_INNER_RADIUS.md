# S133 · C2 en unidades de `inner_radius`: el criterio que S132 no pudo aplicar

**El C2 de S132 era tautológico, y ahora está verificado que lo era.** No es que estuviera
mal calibrado en el sentido de exigir de más: exigía una cosa distinta de la que creía
exigir, y en su versión normalizada ingenua no puede fallar nunca. Acá está la formulación
que sí discrimina, y el diagnóstico retrospectivo de qué habría pasado con ella.

Fuente de todos los números: `experiments/_s133/c2_normalizado_inner_radius.json`
(regla S91). Denominador (A90): los 9.218 records MODIS del flip far→summit del A/B de
S132, ventana 2025-02-15 01:40 a 2026-09-01 07:35 UTC, cada fila un record y no una noche
ni una pasada. Los 9.218 tienen distancia de cúmulo; ninguno usó el fallback.

## Qué medía C2 en realidad

C2 pedía «≥ 80 % del flip con el cúmulo a ≤ 2 km del cráter», y dio 52,73 %. Pero el corte
que define la etiqueta *summit* es el `inner_radius_km` de cada volcán, que va de 3 km en
Lastarria y Planchón-Peteroa a 20 km en Puyehue-Cordón Caulle. Un umbral fijo de 2 km es
más estricto que el cambio mismo en diez de los once volcanes.

Normalizar es lo natural: `d_norm = distancia del cúmulo / inner_radius`. Pero **d_norm ≤ 1
es exactamente la definición del flip**, y se verificó en vez de suponerlo: la fracción
observada es 1,000000. Un C2 escrito así pasaría siempre, en cualquier corrida, sin
informar nada.

## La distribución, por volcán

Estratificada, porque una mediana agrupada puede invertir un veredicto (S126):

| volcán | n | inner (km) | p25 | mediana | p75 | ≤ 0,5 |
|---|---|---|---|---|---|---|
| Villarrica | 1.120 | 5 | 0,245 | 0,368 | 0,501 | 74,7 % |
| Chaitén | 1.044 | 5 | 0,232 | 0,350 | 0,488 | 77,2 % |
| Tupungatito | 937 | 7 | 0,241 | 0,403 | 0,561 | 65,4 % |
| Llaima | 870 | 5 | 0,284 | 0,470 | 0,669 | 53,9 % |
| Copahue | 866 | 4 | 0,343 | **0,526** | 0,698 | 46,5 % |
| Planchón-Peteroa | 857 | 3 | 0,313 | 0,464 | 0,629 | 56,1 % |
| Láscar | 808 | 5 | 0,246 | 0,382 | 0,532 | 71,4 % |
| Isluga | 801 | 5 | 0,278 | 0,413 | 0,575 | 64,4 % |
| Lastarria | 800 | 3 | 0,296 | 0,457 | 0,612 | 56,0 % |
| Nevados de Chillán | 755 | 5 | 0,311 | **0,505** | 0,706 | 49,8 % |
| Puyehue-Cordón Caulle | 360 | 20 | 0,072 | 0,118 | 0,193 | 96,9 % |
| **agregado** | **9.218** | — | 0,255 | 0,410 | 0,581 | **63,7 %** |

Micro y macro casi no separan: mediana agrupada 0,410 contra promedio de medianas 0,405.
La dispersión real está en los extremos, no en el centro.

## C2' propuesto, no adoptado y no pre-registrado

> En cada uno de los 11 Tier A por separado, la mediana de `d_norm` del flip ≤ 0,5; y en el
> agregado, ≥ 60 % del flip con `d_norm` ≤ 0,5.

No es tautológico porque medio inner es estrictamente interior al corte que define el flip.
La referencia contra la cual leerlo: si los cúmulos cayeran al azar y repartidos por área
dentro del disco, la fracción esperada con `d_norm` ≤ 0,5 sería 25 % y la mediana 0,707. Lo
observado es 63,7 % y 0,410, o sea el flip está concentrado sobre el edificio y no repartido
por el disco.

**Diagnóstico retrospectivo, que no es veredicto**: con C2' el flip de S132 fallaría en
Copahue (0,526) y en Nevados de Chillán (0,505), y pasaría el agregado. Eso es precisamente
la prueba de que discrimina. No se movió el umbral hasta que pasaran los once, que sería
repetir A91 con otro disfraz.

## Dos advertencias que limitan la propuesta

**Normalizar no arregla Puyehue-Cordón Caulle.** Con inner de 20 km cualquier cúmulo sobre
el edificio da `d_norm` chico y el criterio queda vacío ahí. Ese inner es una decisión de
MIROVA sobre el lacolito difuso del Cordón Caulle, unos 707 km² a 7 km del vent; no es una
medida de cercanía al cráter. Es la misma tensión que el marcador «extensión» que quedó
esperando decisión volcanológica.

**`d_norm` no separa señal de artefacto.** Los confirmados por MIROVA dan mediana 0,403 y
65,1 % bajo 0,5; los no confirmados, 0,416 y 62,7 %. Prácticamente lo mismo. C2' mide que
el flip apunte al edificio, no que sea real. La pregunta de A83 —si existe un discriminante
per-record entre foco débil real y artefacto topográfico— sigue sin responderse por esta
vía, y por A83 probablemente no se responde por ninguna vía que no sea espacial.

## Lo que queda para Nicolás

La decisión de fondo no cambió y sigue siendo suya. Lo que cambió es que ahora el criterio
que la juzgaría está en las unidades correctas, con su referencia de azar y su diagnóstico
retrospectivo. Si decides reabrir el frente, el A/B se vuelve a correr con C2' pre-registrado
antes de mirar nada; si decides archivarlo, queda archivado con el número bien medido en vez
de con un criterio que no medía lo que decía.
