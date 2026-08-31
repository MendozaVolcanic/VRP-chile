# S129 · ¿A qué radio suma MIROVA? — resultado NEGATIVO

> `experiments/_s129_suma/02_radio_de_suma.py` → `02_radio_de_suma.json`.
> VIIRS375, 9 volcanes con n≥5 noches. Criterio pre-registrado antes de mirar.

## La pregunta

S129 estableció que MIROVA **suma todos los píxeles alertados** (Coppola 2019 p. 3) y
que nosotros publicamos un solo clúster. La primera medición, con un corte plano de
5 km, subió el ratio global de 0,730 a 0,798 — prometedor. Pero un corte elegido a
dedo mide el corte, no el fenómeno, así que había que barrer el radio.

Y sobre todo había que preguntarlo **como MISSION obliga**: no «cuál es el mejor radio
para cada volcán» —eso sería un parche per-volcán disfrazado de calibración— sino
**¿existe un radio uniforme que mejore el conjunto?**

## El resultado

| radio de suma | volcanes en banda [0,7–1,4] | error agregado |
|---|---|---|
| **el clúster actual** | **5 / 9** | 2,535 |
| 1 km | 2 / 9 | 2,188 |
| 3 km | 5 / 9 | 2,760 |
| 5 km | 5 / 9 | 2,844 |
| 7 km | 5 / 9 | 2,808 |
| **10 km** (mejor uniforme) | **6 / 9** | 2,410 |
| 25 km | 6 / 9 | 2,685 |

**El mejor radio uniforme gana UN volcán.** De 5 en banda a 6, con el error agregado
prácticamente igual. Con n = 9 volcanes, eso está dentro del ruido.

Y el detalle importa más que el total, porque no es que mejore parejo:

| volcán | clúster | 10 km | |
|---|---|---|---|
| **Lastarria** | 0,500 | **1,001** | ✓ entra |
| Tupungatito | 0,692 | 0,704 | ✓ entra, al filo |
| **Chaitén** | 1,156 | **1,836** | ✗ **sale** |
| PCC | 0,700 | 1,296 | mejora, sigue en banda |
| los otros cinco | | | se mueven poco |

**Dos entran, uno sale.** Y el que entra de verdad —Lastarria, +0,50— es el campo
fumarólico Lazufre, extendido y difuso, exactamente el régimen donde Steffke & Harris
documentan que perder píxeles marginales cuesta desproporcionadamente. El que sale
—Chaitén— ya sobre-reportaba, y sumarle más lo empeora.

## Lo que de verdad dice el barrido

El mejor radio **por volcán** es: Chaitén 1 · NdC 2 · Lastarria 3 · PP 3 · Tupungatito 3
· Villarrica 5 · PCC 10 · Isluga 25 · Láscar 25 km.

**Esa dispersión —de 1 a 25 km— es el resultado.** No hay un radio uniforme que sirva,
porque los once volcanes no comparten la geometría de su anomalía: un domo puntual
(Chaitén), un campo fumarólico extendido (Lastarria), un lacolito offset (PCC) y una
caldera con cuatro cráteres (Peteroa) no se resumen con el mismo número.

## Y una advertencia sobre la medición anterior

La mejora global que reportó `01_suma_vs_cluster.py` (0,730 → 0,798) **es real y no se
traduce en más volcanes en banda**. Es la lección de S126 otra vez: la mediana agregada
mejora mientras el conteo estratificado no se mueve. El agregado dice que sumamos más
energía; el estratificado dice que esa energía no cae donde hacía falta.

*(Nota metodológica honesta: los dos scripts eligen distinto la pasada representativa de
cada noche —`01` por `pc.vrp_mw`, `02` por energía próxima— así que sus medianas por
volcán difieren en centésimas. No cambia ninguna conclusión, pero no son estrictamente
comparables.)*

## Consecuencia para el A/B

**Reportar la suma en vez del clúster NO es una adopción obvia.** Pasa de candidato a
**brazo** del A/B, con dos cosas que vigilar:

1. **Lastarria es el caso que lo justifica** y Chaitén el que lo desaconseja. Si un
   brazo cura a uno rompiendo al otro, el criterio de decisión tiene que decir de
   antemano cuál pesa más — y eso es una decisión de Nicolás, no del script.
2. **El radio no puede ser per-volcán** (MISSION). Si la única forma de que funcione es
   un radio por volcán, entonces la respuesta correcta es **no adoptarlo**, y anotar por
   qué para que S130 no lo vuelva a intentar.
