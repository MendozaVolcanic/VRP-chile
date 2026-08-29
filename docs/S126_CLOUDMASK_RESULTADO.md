# A/B de la máscara de nube — resultado: sostener el apagado, con una salvedad

> Números de `experiments/_s126_cloudmask/02_veredicto.py` → `02_veredicto.json` (S91).
> El script se escribió **antes** de que terminaran los reprocesos (A16), así que los
> criterios no se acomodaron al resultado.
>
> Runs [33257081431](https://github.com/MendozaVolcanic/VRP-chile/actions/runs/33257081431) (ON)
> y [33257082834](https://github.com/MendozaVolcanic/VRP-chile/actions/runs/33257082834) (OFF),
> ambos `success` con su `merge` pusheado.

**Recordatorio de encuadre**: este A/B **no decidía si apagarla**. El PR #535 la apagó en
producción el 28-ago creyendo que era no-op. Así que la pregunta era *cuánto cuesta
tenerla apagada, y si ese costo justifica revertir*.

## Veredicto: no revertir

### 1. Recupera 176 de 181 noches ciegas — y 157 tenían detección

| volcán | pasadas | ciegas con máscara | ciegas sin | recuperadas | de ellas, con detección |
|---|---|---|---|---|---|
| Nevados de Chillán | 630 | 83 | 5 | **78** | 68 |
| Villarrica | 653 | 69 | **0** | **69** | 62 |
| Láscar | 544 | 29 | **0** | **29** | 27 |

Una noche ciega es una pasada donde el filtro descartaba el ROI entero y el record
quedaba como *"sin señal"* sin que nadie hubiera mirado. Eran 181; quedan 5.

### 2. La magnitud no se degrada — mejora

| volcán | n | con máscara | sin máscara |
|---|---|---|---|
| Villarrica | 8 | 0,764 ✓ | **0,832 ✓** |
| Láscar | 35 | 0,434 ✗ | **0,501 ✗** |

Ningún volcán sale de banda, y los dos con muestra suficiente se acercan a 1,0. NdC no
tiene pares suficientes en la ventana.

### 3. La cara negativa existe, y es chica

La máscara se adoptó para que los topes de nube fríos no bajaran el fondo. Medido sólo
sobre las pasadas donde efectivamente filtraba:

| volcán | pasadas filtradas | t_bg con máscara | sin máscara | Δ |
|---|---|---|---|---|
| Nevados de Chillán | 167 | 267,73 K | 266,10 | **−0,52 K** |
| Villarrica | 174 | 267,43 | 265,81 | **−0,82 K** |
| Láscar | 189 | 264,34 | 261,92 | **−1,97 K** |

El fondo baja entre medio grado y dos. Es real —el mecanismo que la máscara vino a
cubrir existe— pero de un orden que no mueve la magnitud fuera de banda (punto 2).

## La salvedad: lo que se vuelve visible es, en su mayoría, el artefacto

Las detecciones casi se duplican (NdC 99→229, Villarrica 171→236, Láscar 110→200).
Dónde caen las **nuevas**:

| volcán | nuevas | dist. mediana | % a más de 1,5 km | en noche con alerta MIROVA | venían de noche ciega |
|---|---|---|---|---|---|
| Nevados de Chillán | 130 | 2,40 km | 72 % | 3 | 68 |
| Villarrica | 66 | 2,45 | 73 % | 1 | 62 |
| Láscar | 90 | 2,70 | 86 % | 17 | 27 |

**Sólo 21 de 286 detecciones nuevas caen en noches que MIROVA confirma**, y la mediana
de distancia (2,4–2,7 km) es exactamente la firma del artefacto topográfico del anillo
[1,5–3] km que S126 documentó.

O sea: apagar la máscara **devuelve la visibilidad** —dejamos de decir "sin señal" sin
mirar— pero lo que se ve en esas noches es mayormente la misma fluctuación del anillo,
no señal volcánica nueva. Las dos cosas son ciertas a la vez y no se contradicen: el
problema de la máscara era que ocultaba el hecho de no estar mirando; el problema de lo
que aparece al mirar es **otro frente**, el del fondo autorreferente.

## Recomendación

**Sostener el apagado.** Es el comportamiento MIROVA-literal (`MISSION.md`, Laiolo 2026),
es lo que el perfil declara desde S29, recupera 176 noches de visibilidad, no saca a
nadie de banda y su costo medido —medio grado a dos de fondo— no alcanza para revertir.

**Pero no cerrar el tema como "resuelto".** El aumento de detecciones no es un beneficio:
es el artefacto que dejó de estar tapado. Ese frente se cierra con el fondo
autorreferente, no con la máscara. Si el A/B de la corona sale bien, buena parte de esas
286 detecciones nuevas debería desaparecer sola, porque una fluctuación medida contra su
corona inmediata da ΔL ≈ 0.

**Lo que sí queda pendiente de tu decisión**: el apagado llegó sin la compuerta que lo
debía autorizar. Este documento es esa compuerta, corrida a posteriori. Si preferís que
el orden se respete formalmente —revertir y volver a encender con el A/B en la mano— es
un cambio de un valor en el perfil, y pasa por el ciclo A45.

## Lo que NO hay que concluir

- **No "la máscara era inútil"**: el mecanismo que cubría es real y está medido (el fondo
  baja hasta 2 K). Lo que falla es la relación costo-beneficio, no la idea.
- **No "ahora detectamos más"**: detectamos más *records*, casi todos a 2,4–2,7 km del
  cráter y sin contraparte en MIROVA. Contarlo como mejora de recall sería leerlo al
  revés.
- **No mover el umbral a un valor intermedio**: el problema no es dónde está el corte
  entre nieve y nube — a 3.200 m en invierno irradian igual. Un umbral de temperatura de
  brillo no puede separarlas.
