# A/B de la conectiva: lectura PRELIMINAR (S147, después del cierre)

> ⚠️ **ESTO NO ES EL VEREDICTO.** El run **35548121381** terminó con 22 de 22 reprocesos en verde
> pero con el brazo de **control corto en 71 pasadas**. La regla pre-registrada es INDECIDIBLE hasta
> reparar, y se respeta: la reparación está despachada (run **35558196104**, repetición 1 de 2).
> Lo de abajo es una lectura sobre el tramo de la ventana donde la cobertura es **exacta**
> (2026-09-01 a 2026-09-17, 2022 pasadas contra 2022), para que la próxima sesión sepa qué esperar.
>
> ⚠️ **Y una mejora de este tamaño NO SE CREE sin auditoría independiente.** Es regla del proyecto
> (tabla de skills de `CLAUDE.md`: resultado de A/B con mejora sobre 30 % exige depuración
> sistemática y un audit independiente, por el caso S33 de la métrica que se confirmaba a sí misma).
> Acá la tasa falsa cae **90 %**. Antes de proponer nada: verificador con contexto limpio.

## 1. La cobertura, y un arreglo de hoy que se pagó a las pocas horas

| brazo | pasadas | faltan | sobran |
|---|---|---|---|
| B, control (`_s146_ab_sin_test1`) | 2315 | 0 | 0 |
| F, conectiva de prosa (`_s147_ab_sin_test1_max`) | 2386 | 0 | **71** |

Al control le faltan 24 pasadas en Chaitén, 23 en Tupungatito y 24 en Villarrica, **todas del 18 al
20 de septiembre** y en todos los sensores: es la firma de un corte de disponibilidad de NASA para
las fechas más recientes (A64). Los otros ocho volcanes tienen paridad exacta.

**Hasta esta misma sesión el contador de cobertura ignoraba este lado.** Sólo fallaba cuando al
*brazo* le faltaban pasadas; `sobran` se calculaba y no se usaba. El verificador con contexto limpio
lo marcó (hallazgo H3), se arregló a simétrico, y a las pocas horas cazó justo este caso. Sin el
arreglo, el script habría impreso "COBERTURA PAREJA" y la lectura de abajo se habría tomado por
veredicto sobre un control mutilado.

## 2. La lectura, en VIIRS 375

Instrumento: `experiments/_s147_lectura/lectura_por_tramo.py`, que **aborta** si la cobertura del
tramo no es exacta. Su control (el control contra sí mismo) da columnas idénticas.

| | B: fórmula (`min`) | F: prosa (`max`) | predicción |
|---|---|---|---|
| publica en negativos limpios | 29,3 % (95 de 324) | **3,1 %** (10 de 324) | P1: 18 % o menos |
| en el nadir | 19,0 % (22 de 116) | 5,2 % (6 de 116) | |
| en la zona media | 21,8 % (12 de 55) | 3,6 % (2 de 55) | |
| en el borde | 39,9 % (61 de 153) | **1,3 %** (2 de 153) | |
| borde con fondo frío | 61,8 % (42 de 68) | **2,9 %** (2 de 68) | P3: 30 % o menos |
| razón borde sobre nadir | 2,10 | **0,25** | **P2: 1,3 o menos** |
| recall por pasada | 96,9 % (125 de 129) | **96,1 %** (124 de 129) | P4 |

Sobre este tramo las cuatro predicciones se cumplirían con margen grande. **P2, la que decidía la
hipótesis, no sólo se cumple: se invierte.** Con `max` el borde publica *menos* que el nadir, que
es la forma de la curva de MIROVA (su eficiencia por pasada cae de 1,41 a 0,65 del nadir al
borde). Tiene lectura física: en el borde cada píxel es más ruidoso, el sigma de la escena sube, y
con él sube el umbral.

**Lo que se pierde**: un solo positivo en todos los sensores, Lastarria VIIRS 375 del 2026-09-04
06:24 UTC, que MIROVA publicó con 0,14 MW (la réplica mostraba 0,042). Bajo el límite de 0,5 MW
que el perfil declara inaceptable. El recall por volcán no cambia en ningún otro: Villarrica
conserva sus 4 de 4, que era el caso que más se temía.

**VIIRS 750**: negativos limpios de 5,3 % (30 de 562) a 0,5 % (3 de 562); positivos 11 de 16 en
los dos brazos.

## 3. El cero que NO hay que creer: MODIS

MODIS pasa de 8,8 % (34 de 385) a **0,0 %** (0 de 385). Un cero así se mide antes de creerlo
(A116), y medido **no es fidelidad, es un detector apagado**:

| pasadas MODIS con píxeles del primer pase | B (`min`) | F (`max`) |
|---|---|---|
| | **397 de 399** | **1 de 399** |

Con la banda 21, que es la que usa la réplica, el sigma del dNTI es 3,5 a 4,7 veces mayor que con
la banda 22 del paper (D21), así que bajo `max` el umbral adaptativo se va tan alto que el camino
contextual de MODIS deja de existir. Y con una sola pasada positiva de MODIS en la ventana, el
recall no se puede juzgar. La batería del Apéndice A ya lo había mostrado: `max` con banda 21
pierde tres casos reales (A1, A5 y A6), y sólo la combinación banda 22 con `max` los recupera.
**En MODIS la conectiva no se adopta sola: va junto con D21.** El pre-registro ya lo decía.

Y el lado B deja un dato que vale por sí mismo: con `min` el camino contextual de MODIS tiene
píxeles del primer pase en **397 de 399 pasadas**. O sea que dispara en prácticamente todas, y lo
que lo contiene después es la geometría (casi todo cae fuera del radio interno), no el detector.

## 4. Lo que todavía NO se miró, y tiene que mirarse antes de proponer nada

- **La ventana completa**, con el control reparado. Es lo único que da veredicto.
- **La magnitud pareada y la posición del cúmulo**: el evaluador completo no se corrió, porque con
  el control corto da INDECIDIBLE por diseño.
- **El nulo por etiquetas barajadas**: que la caída sea selectiva y no un endurecimiento parejo. La
  inversión de P2 apunta a que sí, pero no está medido.
- **La muestra de positivos es de 129 pasadas en 17 días**, dominada por Isluga (31), Puyehue
  Cordón Caulle (27), Tupungatito (19) y Láscar (18). Villarrica aporta 4 y Nevados de Chillán 1.
  Un recall de 96 % sobre esa mezcla no dice qué pasa con un lago de lava débil en invierno.
- **El auditor independiente** que la regla del proyecto exige para una mejora de este tamaño.
- **Los brazos G y H** (la caja de 5 × 5 km), que al momento de escribir esto siguen corriendo
  (run 35548604513).

## 5. Cómo se retoma

```
git fetch origin
gh run view 35558196104 --json status,conclusion        # la reparación del control
git archive origin/s146-ab/35558196104 experiments/_s146_ab_sin_test1/salidas/35558196104 \
    | tar -x -C experiments/_s147_lectura               # SIEMPRE con la ruta
# reemplazar Chaiten, Tupungatito y Villarrica del brazo B del run 35548121381 por los reparados,
# contar cobertura (contar_pasadas.py), y recién entonces evaluar.py y lectura_por_tramo.py
# con --fin 2026-09-20.
```
