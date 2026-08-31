# S129 · El ROI1: el paper usa una caja de 5 km, nosotros un círculo de 3 a 20

> `experiments/_s129_roi1/01_caja_vs_circulo.py` → `01_caja_vs_circulo.json`.
> Read-only. Es el **eje geométrico que A82 nunca auditó**, y por el que S124 la rebajó.

## Lo que dice el canon

Coppola 2016a SP426.5, verbatim:

> *«the inner region (ROI1) consists of a **box (5 × 5 km)** centred on the volcano's
> summit»*

Una caja de 25 km², **igual para todos los volcanes**. Y el criterio del propio paper
para tener dos regiones es que tengan *«variable size and different chance of finding a
thermal anomaly»* — o sea, el ROI1 es chico **a propósito**: es la zona donde una
anomalía es esperable, y por eso ahí los umbrales son laxos.

## Lo que hacemos

Un **círculo** de radio `inner_radius_km`, **distinto por volcán**.

| volcán | r (km) | área km² | veces el ROI1 del paper | píxeles que hoy reciben umbral *summit* | los que también caen en la caja | **perdería el trato** |
|---|---|---|---|---|---|---|
| **PuyehueCordonCaulle** | **20** | 1.256,6 | **50,3×** | 53.307 | 4.791 | **91,0 %** |
| Tupungatito | 7 | 153,9 | 6,2× | 5.484 | 932 | 83,0 % |
| Chaitén | 5 | 78,5 | 3,1× | 9.802 | 5.104 | 47,9 % |
| Isluga | 5 | 78,5 | 3,1× | 6.200 | 3.306 | 46,7 % |
| Láscar | 5 | 78,5 | 3,1× | 3.919 | 2.070 | 47,2 % |
| Llaima | 5 | 78,5 | 3,1× | 4.929 | 2.481 | 49,7 % |
| NevadosDeChillán | 5 | 78,5 | 3,1× | 2.427 | 1.092 | 55,0 % |
| Villarrica | 5 | 78,5 | 3,1× | 9.003 | 4.549 | 49,5 % |
| Copahue | 4 | 50,3 | 2,0× | 4.309 | 2.497 | 42,1 % |
| Lastarria | 3 | 28,3 | 1,1× | 2.833 | 2.510 | 11,4 % |
| Planchón-Peteroa | 3 | 28,3 | 1,1× | 5.052 | 4.022 | 20,4 % |

**De los 107.265 píxeles que hoy reciben el umbral laxo de *summit*, sólo 33.354 caerían
dentro del ROI1 del paper. El 68,9 % lo recibe por una geometría que el canon no
respalda.**

Y ni siquiera el radio «estándar» de 5 km se acerca: es **3,1×** el área de la caja.
Los únicos dos que quedan cerca del paper son los de radio 3 km.

## Por qué importa y no es cosmético

El ROI1 decide **qué umbrales se aplican**: adentro rigen los de *summit* (N·σ = 5,
C1 = 0,003) y afuera los de *scene* (N·σ = 10, C1 = 0,010). Agrandar el ROI1 **afloja el
umbral sobre más terreno**.

Con PCC el número es difícil de defender: su ROI1 es **cincuenta veces** el del paper, o
sea que media escena hereda los umbrales pensados para el cráter. Y ahí el propio
criterio de Coppola —«distinta probabilidad de encontrar una anomalía»— deja de
cumplirse: a 20 km del centro la probabilidad ya no es la del cráter.

**Y es per-volcán, que `MISSION.md` excluye explícitamente.** Esto no es un parche
agregado tarde: está en la geometría base de la detección desde S14, y se justificó con
los valores oficiales de los KML de MIROVA (regla A5). Es decir, hay un argumento real
del otro lado — pero el paper dice otra cosa, y la contradicción nunca se había medido.

## Lo que este hallazgo NO dice

**No dice que esos 73.911 píxeles sean falsos positivos.** Con la caja del paper no
desaparecerían: pasarían a los umbrales de *scene*, que son más estrictos, y **algunos**
dejarían de pasar. La dirección del cambio es **menos detecciones**.

Y ahí está el conflicto que hay que nombrar antes de tocar nada: `mirova_equivalent`
tiene como prioridad declarada **el recall por sobre la precisión**, porque un falso
negativo en monitoreo volcánico es el error caro. Achicar el ROI1 mejora la fidelidad
al paper y empeora la sensibilidad. **No es una decisión técnica: es de misión, y es de
Nicolás.**

## Cómo se relaciona con A82

A82 concluyó que el far→summit de MODIS es «físicamente irreducible», y S124 la rebajó
justamente porque la auditoría S114 en que se apoyaba cubrió umbrales, tests, kernel y
second-run **pero no la geometría del ROI**.

Este trabajo cierra ese hueco a medias: **mide** la divergencia geométrica, pero no
prueba que corregirla cure el far→summit. Es una **hipótesis nueva y falsable**: si el
umbral laxo aplicado sobre 3 a 50 veces el terreno que el paper autoriza está dejando
pasar píxeles marginales del campo difuso, achicar el ROI1 debería reducirlo. Eso se
mide con un A/B, no con este script.

## Propuesta

**No tocar nada todavía.** Registrarlo como divergencia con su número, y evaluarlo como
un brazo más cuando se decida el frente de geometría — junto con el remuestreo a malla
fija, que es del mismo eje y ya tiene plan escrito.

Si se evalúa, el brazo fiel es **una caja de 5 × 5 km uniforme**, no un círculo de radio
uniforme: el paper dice caja, y la forma importa en las esquinas.
