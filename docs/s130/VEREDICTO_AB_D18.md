# S130 · Veredicto del A/B de D18 — la caja del paper casi no cambia nada

**No adoptar.** No por daño —no lo hay— sino por ausencia de beneficio: la geometría
del ROI1 resulta ser una divergencia de fidelidad **real** con consecuencia
operacional **marginal**.

Criterios congelados de antemano en [`PREREGISTRO_AB_D18.md`](PREREGISTRO_AB_D18.md).
Run `33456630043`, 12/12 verdes, seis volcanes × dos brazos, 2026-05-29 a 08-24.

## El control de instrumento pasa

Lo primero, porque el A/B anterior de esta misma sesión no lo pasó: **el flag actuó**.
Sobre 5.551 records comunes a los dos brazos, **366 (6,59 %)** cambian de
`primary_cluster.vrp_mw`. Por volcán, PCC llega al **17,98 %**, coherente con que su
ROI1 sea 50,3× el área del paper.

Pero el signo del cambio ya anticipa el veredicto: de esos 366, la caja da **más** en
166 y **menos** en 200. **Redistribuye, no recorta.**

## Los resultados

| volcán | régimen | det. círculo | det. caja | % pierde | offset círc. | offset caja | ratio círc. | ratio caja | noches MIROVA perdidas |
|---|---|---|---|---|---|---|---|---|---|
| PCC | difuso | 749 | 743 | **0,8 %** | 1,676 | 1,657 | 0,361 | **0,401** | 0 |
| Láscar | focal | 403 | 403 | 0 % | 0,418 | 0,418 | 0,314 | 0,314 | 0 |
| Lastarria | focal (canario) | 366 | 366 | 0 % | 2,032 | 2,032 | 0,400 | 0,400 | 0 |
| Llaima | nevado | 390 | 390 | 0 % | 2,755 | 2,746 | 0,045 | 0,045 | 0 |
| Copahue | nevado | 402 | 402 | 0 % | 2,712 | 2,698 | 0,820 | **0,840** | 0 |
| Villarrica | nevado | 430 | 430 | 0 % | 2,630 | 2,631 | 0,267 | 0,267 | 0 |

## Contra los criterios congelados

**Ningún límite de no-adopción se cruza.** Lastarria —el canario del cat-b— pierde
0,0 % contra un límite del 20 %, y PCC 0,8 % contra 50 %. La caja **no destruye señal
real**: el Lazufre y el lacolito sobreviven enteros. Cero noches MIROVA-confirmadas
perdidas en los seis volcanes.

**Pero el criterio de adopción tampoco se cumple.** Pedía que el offset del clúster
bajara en los tres nevados, y Villarrica **sube** 1 m sobre 2,63 km. Los otros dos
bajan 9 y 14 metros sobre offsets de 2,7 km: eso es ruido, no efecto. La firma que
tenía que arbitrar —¿recorta artefacto o recorta señal?— **no arbitra nada, porque no
recorta**.

Lo único que se mueve es la paridad de magnitud, y poco: **+0,040 en PCC** y
**+0,020 en Copahue**, nulo en los otros cuatro. Cambiar la geometría del perfil
operacional para eso, alterando el 6,6 % de las magnitudes en direcciones opuestas, no
se justifica.

## El error de predicción, y lo que enseña

Antes del A/B se midió que **el 42 % de las detecciones summit tienen su clúster fuera
de la caja** y se lo presentó como «lo que está en juego». El A/B dice que lo que
realmente se pierde es **0 a 0,8 %**. La predicción sobrestimó el efecto unas cincuenta
veces.

El error no fue de cálculo sino de **qué se estaba contando**: se contó **dónde cae el
clúster** respecto de la caja, no **si la detección sobrevive** al umbral más estricto.
Y casi todas sobreviven.

De ahí sale el hallazgo real de este A/B, que es más interesante que el veredicto:

> **El umbral laxo del ROI1 casi nunca es lo que decide.** Las detecciones de estos
> volcanes pasan con margen suficiente como para no depender de si el píxel recibe
> N·σ = 5 o N·σ = 10. La diferenciación summit/scene existe, es fiel al paper en sus
> valores, y resulta **casi inerte** en la práctica.

Eso también explica por qué Llaima, Villarrica y Láscar —con `inner_radius_km = 5`, o
sea 3,1× el área del paper— no cambian **nada**: el terreno extra que su círculo cubre
de más no contiene detecciones que dependan del umbral laxo.

## Relación con el A/B de los fondos

Es el segundo mecanismo de esta sesión que resulta tener menos efecto del que su
descripción sugería, pero **por una razón distinta**, y la diferencia importa:

- El A/B de los **fondos** falló por **falta de sustrato**: el mecanismo casi nunca
  tenía ocasión de ejecutarse (K1 se cruza en el 0,09 % de las pasadas MODIS).
- El A/B de **D18** tuvo sustrato de sobra —6,59 % de los records cambian— pero el
  mecanismo **no es el que decide el resultado**.

La lección que suma es la segunda: **estar en el ámbito de un mecanismo no es depender
de él**. Contar cuántos casos un mecanismo *toca* sobrestima cuántos *decide*. El
control de instrumento correcto para un A/B de umbrales no es «¿cuántos píxeles caen
bajo esta regla?» sino «¿cuántos están lo bastante cerca del umbral como para que
cambiarlo los mueva?».

## Qué queda

**D18 sigue abierta como divergencia de fidelidad literal** — nuestra geometría no es
la del paper, eso no cambió. Lo que cambia es su prioridad: **su consecuencia empírica
está medida y es marginal**, igual que el GAP #A tras el A/B de los fondos.

El flag `enable_roi1_box_paper` queda en el código, **OFF**, con sus 7 tests. Si algún
día se busca fidelidad literal por sí misma, está listo y medido. Adoptarlo hoy sería
cambiar el operacional a cambio de nada.
