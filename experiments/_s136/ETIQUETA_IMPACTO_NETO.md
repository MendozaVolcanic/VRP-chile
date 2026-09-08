# El bug de la etiqueta no es rentable: 4 noches de 946, y 3 son artefacto

> Medición read-only sobre `data/mirova_equivalent/` (11 Tier A, toda la serie en disco), ground
> truth CONS ∪ OCR hasta 2026-09-07. Cierra por medición el frente que yo mismo había puesto como
> «lo más rentable» tras el resultado de conformidad A6. **Era una recomendación mal dirigida.**

## De qué frente se trata

El caso A6 mostró que detectamos correctamente el cráter de Villarrica —con el respaldo del autor
del algoritmo— y que la etiqueta `distance_class = "far"` lo esconde del dashboard, porque la
etiqueta se deriva del `final_hotspot` y no del cúmulo. S113 ya había identificado esa cara y
dejado un «fix candidato» pendiente: promover a *summit* los cúmulos crateriana genuinos.

## Vía 1 — el discriminante geométrico: DESCARTADO

S113 dejó el fix pendiente porque exige distinguir el robo **legítimo** (Láscar: el Salar de
Atacama a 18-24 km roba el punto caliente y esconde un cúmulo crateriano que MIROVA confirma) del
**artefacto** (Nevados de Chillán: gradiente topográfico A69). A83 declara agotado el discriminante
**físico** per-record; probé el **geométrico**, que A83 no cubrió: ¿la distancia del hotspot robado
separa un caso del otro?

**No separa.** Sobre los ~9.350 records ocultos de los 11 Tier A (cifra consistente con los 9.196
medidos en S130, buen control de corpus):

| corte «hotspot robado a más de…» | Láscar (37 % confirmado) | Llaima (0 % confirmado) |
|---|---|---|
| 10 km | 100 % de sus ocultos | 94 % de sus ocultos |
| 15 km | 97 % | 78 % |
| 18 km | 92 % | 68 % |

En todos los cortes, entre el 51 % y el 100 % de los records de **todos** los volcanes caen del
lado «robo claro». La geometría del hotspot robado no distingue el caso legítimo del artefacto. Lo
único que separa es la tasa de confirmación de MIROVA por volcán (Láscar 37 %, Isluga 34 %,
Lastarria 31 % contra Llaima 0 %, Copahue 1 %, NdC 3 %), y usar el ground truth como discriminante
en producción es circular.

## Vía 2 — el impacto neto, contado en NOCHES: el frente no vale la pena

Un record oculto **no es una alerta perdida**: si otra pasada de la misma noche se publica como
*summit*, el operador ve el volcán encendido igual. Lo que se pierde de verdad son las noches
**enteramente** ocultas. Contado así (A93: el número sale de la definición del conjunto):

| | noches |
|---|---|
| noches con alerta de MIROVA (11 Tier A, toda la serie) | **946** |
| ya se publican | 897 |
| **enteramente ocultas por la etiqueta** | **4** |
| no tenemos nada esa noche, ni oculto | 45 |

**Recall del gate del dashboard: 94,8 % → 95,2 % si se promoviera. +0,4 puntos.**

Y de esas 4 noches, **3 son de Nevados de Chillán** — exactamente el artefacto A69 que S113 dijo
que no hay que destapar — y 1 de Tupungatito. **El beneficio real del fix es 1 noche sobre 946.**

Consistente con S113, que midió 84 noches con 73 de NdC: la proporción de NdC se mantiene (75-87 %)
y el absoluto bajó, con un corpus que casi se triplicó desde entonces (A90: no son cifras
comparables sin reconstruir la ventana, pero la conclusión es la misma y más fuerte).

## El frente que sí queda, y que la etiqueta no arregla

Las **45 noches** en que MIROVA publica y no tenemos **nada** — ni un cúmulo crateriano oculto:
Puyehue 14, Láscar 10, Lastarria 10, Planchón-Peteroa 5, Chaitén 4, Isluga 2. Eso es **4,8 % de
las noches** y es el falso negativo real. No lo cura ninguna etiqueta: es detección.

## Lección de método

Propuse este frente como «el más rentable» apoyado en un caso individual bien fundado —A6, con
respaldo del autor— sin haber medido su tamaño agregado. El caso era real y la etiqueta sí lo
esconde; lo que no era cierto es que arreglarlo rindiera. **Un caso de referencia sólido justifica
investigar un mecanismo, no priorizarlo**: la prioridad se decide con el agregado, y el agregado
había que contarlo en noches, no en records. Es el mismo error de unidades que A90 y A93 persiguen,
esta vez en la elección de qué hacer y no en un número reportado.
