# La ambigüedad de «pasada útil» se resuelve con datos, no con una decisión

> Medición sobre `experiments/_s136/out/resultado_3brazos.json`, el mismo run 34274884640.
> Corrige la interpretación que quedó en `AUDITORIA_PROBE_Y_CAMINOS.md` y en #612.

## Lo que estaba en duda

El criterio pre-registrado dice «C, indeterminado: menos de 4 pasadas útiles en los nevados»,
sin definir *útil*. Con una lectura hay 3 y con otra 13. Se planteó como decisión del dueño. **No
lo era**: es medible cuál lectura responde la pregunta del experimento.

## El dato que lo resuelve

Ratio nuestro/MIROVA, mediana, separando las pasadas según el filtro **actúe o no**:

| clase | ¿el filtro actúa? | n | ACTUAL | SIN_FILTRO | movimiento |
|---|---|---|---|---|---|
| nevado | **sí** | **3** | 1,17 | **2,23** | **×1,91** |
| nevado | no | 10 | 0,91 | 0,91 | **×1,00** |
| control | sí | 4 | 0,84 | 1,22 | ×1,45 |
| control | no | 3 | 0,38 | 0,38 | **×1,00** |

Las pasadas donde el filtro no actúa dan movimiento **exactamente ×1,00**: son inertes por
construcción y no pueden aportar información sobre si el filtro cura. Incluirlas sólo diluye la
mediana. **La lectura «con sustrato» es la correcta, y eso queda medido, no elegido.**

## Y el desenlace apunta a B, no a A

En los nevados donde el filtro actúa, retirarlo lleva la mediana a **2,23**, que está **fuera de la
banda de paridad 0,5-2,0**, con un movimiento de **×1,91** que además excede el factor 1,5 que el
criterio A exigía. Eso es el desenlace **B, el filtro sigue curando**, no el A que el script
imprimió.

Formalmente sigue siendo **C** porque n = 3 < 4, el umbral pre-registrado. Pero la dirección de la
evidencia es la contraria a A: **retirar la intersección no es seguro**, y con la muestra ampliada
lo esperable es B.

Coherente con D10 (la intersección se adoptó para curar Tupungatito, 8-19×) y con A66/S103, que ya
había refutado con un A/B de 3 brazos que `ctxpeak` fuera un parche redundante del sec³.

## Corrección de una afirmación propia

En esta sesión escribí que el efecto «va en la dirección correcta, porque sub-reportamos». Con la
mediana de las pasadas que tienen sustrato, **se pasa de largo**: 2,23 supera el techo de la banda.
La afirmación era de las 7 pasadas mezclando nevados y control (1,00 → 1,30, que sí queda en
banda); estratificando por régimen (que es como manda medirse este proyecto) los nevados se salen.
Es el error de la mediana agrupada que ya está registrado como lección en S126.

## Consecuencia para el frente

El camino «retirar la intersección contextual del Test 1» queda **debilitado por medición**, no
cerrado: sigue siendo cierto que la intersección no está en el paper (gate MISSION, P1), pero
quitarla sola empeora la paridad en los nevados. Es la misma tensión que D10 documenta, y ahora con
número propio.
