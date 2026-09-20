# Resultado del A/B "sin el Test 1 integrado" (S147)

> Run **35521542153**, despachado el 2026-09-20 16:04 UTC, 4 h 40 min, 33 de 33 reprocesos en
> verde. Criterios pre-registrados y commiteados **antes** de correr, en
> `experiments/_s146_ab_sin_test1/PREREGISTRO.md` con su adenda S147, después de que un
> verificador con contexto limpio encontrara 18 defectos en ellos, dos de los cuales daban vuelta
> el veredicto solos.
>
> **Veredicto: NO ADOPTAR.** Falla C2, C4 y C7. Pero el resultado no es "el experimento salió
> mal": el mecanismo quedó **confirmado** y lo que falló dice exactamente por dónde seguir.

## 1. La cobertura, antes de mirar nada

| brazo | pasadas | faltan | sobran |
|---|---|---|---|
| control | 2362 | 0 | 0 |
| **sin Test 1** | **2362** | **0** | **0** |
| sin prioridad por rival débil | 2318 | 44 (Láscar 22, Lastarria 22) | 0 |

El job `recolectar` **falló a propósito** por el tercer brazo, que es justo lo que A108 pide: un
run 100 % verde no prueba cobertura pareja. La comparación que decide, control contra sin Test 1,
tiene paridad exacta, así que se evaluó esa. El brazo C se relanzó (repetición 1 de las 2 que el
pre-registro autoriza).

**Control positivo del control**: reproduce producción en el **99,96 %** de 2362 pasadas
comparadas (1 sola diferencia de publicación). El reproceso es fiel.

## 2. Lo que el experimento confirmó

**La sobre-publicación cae exactamente como predijo el mecanismo.**

| sensor | control | sin Test 1 | caída |
|---|---|---|---|
| VIIRS 375 | 86,1 % | **28,7 %** | 57,4 puntos |
| VIIRS 750 | 21,4 % | **5,9 %** | 15,5 puntos |
| MODIS | 5,1 % (sin PCC) | 2,5 % | 2,7 puntos |

El 28,7 % cae **dentro de la banda 21,4 a 36,5 %** que la Fase 1 había inferido desde lo
persistido, sin reprocesar. La inferencia era buena.

**Y la caída es selectiva, no al azar.** El contraste entre positivos y negativos queda fuera del
nulo de etiquetas barajadas (observado -0,186 contra un intervalo de -0,040 a 0,058). Un brazo que
apagara publicaciones al azar daría las dos caídas iguales; éste no.

**El orden por sensor se cumple**: 57,4 > 15,5 > 2,7, que es lo que predice un defecto gobernado
por el número de píxeles del disco (201 en VIIRS 375, 50 en VIIRS 750, 28 en MODIS).

**Y el recall aguanta**: 135 de 141 pasadas en VIIRS 375 (piso pre-registrado 118) y 13 de 13 en
VIIRS 750. Las 6 pasadas perdidas están todas bajo 0,15 MW de MIROVA, ninguna llega al umbral de
0,5 MW que el perfil declara como pérdida inaceptable.

## 3. Por qué igual sale NO ADOPTAR, y esto es lo interesante

**Apagar el Test 1 no es una amputación limpia.** El pre-registro decía que el brazo "no toca la
máscara contextual", y es cierto a nivel de máscara, pero el Test 1 **compite por la fuente del
ancla**, y el ancla decide qué cúmulo es el primario. Apagarlo cambia, de rebote, qué cúmulo se
publica.

**C7, posición (criterio nuevo de S147, sugerido por el verificador).** De 532 pasadas que los dos
brazos publican, **96 mueven el cúmulo más de 500 m**, con p90 de 2,74 km. En todas las que
inspeccioné la fuente es `ctx_cluster` en los dos brazos: o sea que no es que el Test 1 deje de
poner el ancla, es que **al sacarlo se elige otro cúmulo contextual**. Este criterio no existía
antes de hoy: se calculaba y no decidía nada.

**C2, noches perdidas fuera de lo previsto.** Dos noches de Nevados de Chillán, el 2026-09-05
(MIROVA 0,14 MW) y el 2026-09-14 (0,09 MW), que la Fase 1 no había anticipado. Y el detalle que lo
explica: de las 6 pasadas perdidas, **4 tenían fuente `ctx_cluster` en el control**, no `test1`.
O sea que no las sostenía el Test 1 directamente: se pierden por ese mismo efecto de segundo orden
sobre la selección del cúmulo.

**C4, magnitud.** Falla en tres estratos, los tres de VIIRS 375, y en los tres la razón contra
MIROVA **se aleja de 1 hacia abajo**:

| estrato | n | control | sin Test 1 | |
|---|---|---|---|---|
| Láscar VIIRS 375 | 18 | 0,655 | 0,477 | empeora 0,177 |
| Isluga VIIRS 375 | 31 | 0,582 | 0,469 | empeora 0,113 |
| Tupungatito VIIRS 375 | 24 | 0,540 | 0,436 | empeora 0,103 |
| Lastarria VIIRS 375 | 9 | 1,195 | 1,015 | **mejora** 0,180 |
| Villarrica VIIRS 375 | 5 | 0,837 | 1,014 | **mejora** 0,149 |

Tiene lectura física: donde el Test 1 **recompone** la magnitud (su recómputo está gateado por
`source == 'test1'`), apagarlo deja un número más chico; donde el Test 1 la **inflaba**, apagarlo
acerca a 1. Nótese que este criterio es el que S147 hizo **pareado** por recomendación del
verificador: sin parear, la selección sola habría movido la mediana más que el propio umbral.

## 4. Qué se concluye, y qué no

**Se concluye** que el defecto del Test 1 es real, que explica la mayor parte de la
sobre-publicación de VIIRS 375, y que quitarlo la baja 57 puntos sin costar recall grueso.

**No se concluye** que haya que apagarlo. Lo que el A/B muestra es que **apagarlo entero arrastra
efectos que no queremos**: mueve el cúmulo publicado en 1 de cada 5 pasadas, baja la magnitud en
los tres volcanes con más muestra, y pierde dos noches de un volcán en reactivación.

**La salida que esto señala es la que el propio pre-registro anticipaba como "el brazo siguiente"**
y que S147 ya dejó implementada detrás de un flag apagado: el **estadístico corregido**, que
conserva el Test 1 y sólo le quita el piso de ruido. La diferencia con apagarlo es que el Test 1
sigue existiendo para las pasadas que de verdad superan el ruido, así que para ésas el ancla y el
cúmulo no se mueven.

**Cuidado con extrapolar eso.** Para las pasadas cuyo disparo muere con el estadístico corregido
(según la cota sobre lo persistido, el 88 % en VIIRS 375), el efecto sobre el ancla **es el mismo
que apagarlo**. O sea que el brazo corregido va a tener una parte de estos mismos efectos de
segundo orden, más chica pero no nula. Es SOSPECHA hasta que se corra: no hay que suponer que el
estadístico corregido los evita.

## 5. Lo que hay que hacer con esto

1. **Terminar el brazo C** (relanzado, repetición 1 de 2) para cerrar el run entero.
2. **Correr el brazo del estadístico corregido** con estos mismos criterios, que ahora miden lo
   que hay que mirar: posición del cúmulo, magnitud pareada y las noches de Nevados de Chillán.
3. **Antes de eso, decidir C7**. El tope de "0 cúmulos movidos más de 500 m" lo puse yo hoy y es
   estricto: con 96 de 532 en el brazo B, cualquier brazo que toque el Test 1 lo va a fallar. La
   pregunta para Nicolás no es si relajarlo, es **cuánto movimiento del cúmulo publicado es
   aceptable** para el geólogo que mira el mapa, que es una decisión de operación y no de
   estadística.
4. **No tocar `mirova_equivalent`** con nada de esto sin el ciclo A45 completo.

## 6. Límites declarados

- Ventana de 20 días, del 2026-09-01 al 2026-09-20, entera posterior al cambio de régimen de #535.
- La vara de recall de VIIRS 750 está rotulada **débil** desde la adenda S147: con un nulo que
  preserva la correlación entre pasadas de la misma noche, el azar alcanza el observado.
- MODIS informa y no decide: una sola pasada positiva en la ventana.
- El brazo del estadístico corregido **no se corrió**: todo lo que se dice de él en §4 es cota o
  sospecha, con su etiqueta.
