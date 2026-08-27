# F70 brazo C — el kernel de vecinos, solo, no alcanza

> Run [33006952492](https://github.com/MendozaVolcanic/VRP-chile/actions/runs/33006952492),
> 12/12 trozos verdes. Perfil aislado `_s124_kernelbg_ab`, ventana
> 2026-06-25..2026-08-24, 6 volcanes. Evaluado contra el criterio escrito
> **antes** de correr (A66). Números de script reproducible (S91).

## Qué brazo es esto

El diseño [F70](superpowers/specs/2026-08-25-grilla-utm-kernel-global-design.md)
§5 pre-registra cuatro brazos:

| brazo | grilla UTM | kernel-bg | qué contesta |
|---|---|---|---|
| control | OFF | per-volcán | baseline = serie operacional |
| A | ON | per-volcán | ¿la grilla sola mejora? |
| **B** | **ON** | **global** | **la hipótesis central** |
| **C** | **OFF** | **global** | aísla el kernel — *"réplica del fallo S62"* |

Este A/B se lanzó en S124 sin haber revisado que el experimento ya estaba
diseñado, y resultó ser **el brazo C** sobre 6 de los 11 (trampa A50,
documentada en [`AUDIT_S124.md`](AUDIT_S124.md) §4). Sirve igual: el diseño
necesita el brazo C como control.

## El resultado

Ratio mediano contra MIROVA CONS (VIIRS 375 m, noches cruzadas):

| volcán | n | control | brazo C | movimiento |
|---|---|---|---|---|
| **Láscar** | 32 | 0,47 | **0,58** | +23 %, sigue fuera de banda |
| **Isluga** | 40 | 0,70 | 0,81 | +16 %, ya estaba dentro |
| Tupungatito | 17 | 0,81 | 0,81 | sin cambio |
| NevadosDeChillán | 2 | 1,31 | 1,31 | sin cambio |
| Copahue | 1 | 1,02 | 1,02 | sin cambio |
| Llaima | — | — | — | sin noches cruzadas en la ventana |

## Veredicto: NO ADOPTAR

El criterio primario pedía que **los sub-reportadores entraran en la banda
[0,7-1,4]**. Láscar se mueve en la dirección correcta pero se queda en 0,58 —
lejos del 0,70 que hace falta. El brazo falla su criterio.

Dos lecturas, y la segunda es la que importa:

1. **El signo es el esperado.** Cambiar el fondo del anillo lejano (5-25 km) por
   los ocho vecinos —que es lo que pide Coppola Eq. 6— sube el ratio en los dos
   volcanes con muestra suficiente. La física del mecanismo se confirma: si el
   anillo lejano es más tibio que el entorno inmediato del cráter, el
   ΔL = L_hot − L_bk sale comprimido y el VRP sale chico.

2. **La magnitud no alcanza, y eso es exactamente lo que el diseño predijo.**
   El brazo C está rotulado en §5 como *"réplica del fallo S62"*: el kernel
   aplicado **sobre el swath crudo**, donde los ocho vecinos son objetos
   geométricamente distintos en cada pasada. La hipótesis central de F70 es que
   **la grilla es lo que hace que el kernel funcione**. Este resultado no la
   prueba, pero es consistente con ella y descarta la alternativa simple
   ("bastaba con prender el kernel").

## Una anomalía que conviene mirar en F70.3

Tres de los seis volcanes dan ratio **idéntico a dos decimales** entre control y
brazo C (Tupungatito 0,81 / NdC 1,31 / Copahue 1,02). Con n = 17, 2 y 1 puede
ser tamaño de muestra —el kernel y el anillo coinciden cuando el cluster es de
un solo píxel y el entorno es homogéneo— pero también podría ser que la rama del
kernel no se ejecute en esos casos.

Láscar (n=32) e Isluga (n=40) **sí** cambian, así que el flag funciona. Antes de
leer F70.3 conviene confirmar con un contador explícito cuántas veces se tomó
cada rama, en vez de inferirlo del resultado.

## Qué sigue

Con F70.2 completo (los tres procesadores cableados tras `ENABLE_UTM_REGRID`,
PRs #525 y #527), el brazo que falta es el **B**. F70.3 debe correr los cuatro
sobre los **11** Tier A, no 6, y evaluarse contra los criterios ya escritos:
Tupungatito es el juez (B debe curarlo donde C debe romperlo), Lastarria no debe
romperse, la paridad global no debe empeorar, el offset espacial no debe crecer
(A61) y hay que verificar eventos concretos, no solo agregados (A79).
