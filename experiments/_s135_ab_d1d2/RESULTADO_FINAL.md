# A/B de D1 y D2 — veredicto sobre la ventana completa

> Ventana **2026-06-01 → 2026-08-31**, los 6 volcanes que deciden, los 2 chunks fusionados
> (`fusionar_chunks.py`; ventanas disjuntas, sin solape). Chunk 1 run 34173711390 (30/30 verde,
> con el rerun del job degradado de Puyehue) y chunk 2 run 34208191011 (30/30 verde). Criterio de
> `docs/PREREGISTRO_AB_D1_D2_S135.md` con la decisión de Nicolás: **cero pérdidas** sobre lo que
> MIROVA entrega. Números de `evaluar_ab.py` → `resultado_final.json`.

## El veredicto: ninguno de los cinco brazos resuelve el problema

**260 noches confirmadas** (Isluga 71, Láscar 52, Lastarria 48, Puyehue 33, Planchón-Peteroa 28,
Tupungatito 28), tras excluir pasadas diurnas y coincidencias de fecha con objetos distintos.

| brazo | pierde noches | quita el artefacto | paridad | falla en |
|---|---|---|---|---|
| A control | 0 | — | 0,708 | (es el control) |
| B sin `keep_peak` | 0 | **100 %** | **0,692** | criterio 3, por poco |
| C sólo 2º pase condicionado | 0 | **−46,6 %** | 0,713 | criterio 2 |
| D ambos (el más fiel) | **12** | **100 %** | 0,713 | criterio 1 |
| E 2º pase apagado | 0 | **−46,6 %** | 0,672 | criterios 2 y 3 |

**Ningún brazo cumple los tres.** Esto es más fuerte que el resultado parcial del primer tramo,
donde el brazo B parecía cumplir: con la ventana completa su paridad se aleja de 1,0 un poco más
que la del control (0,692 contra 0,708), y el criterio 3 dice que no puede empeorar. Es marginal
—dos centésimas— y merece que Nicolás lo pondere, pero el criterio se fijó antes de ver los
datos y no se ajusta después.

## Lo que el experimento sí dejó probado

**1. Arreglar sólo el segundo pase empeora el artefacto.** Los brazos C y E producen un 47 %
**más** registros de nivel base falso que el control. Al condicionar o apagar el segundo pase, el
camino contextual deja de ganar la selección y el Test 1 pasa a ser la fuente con su píxel único.
Tocar D2 sin tocar D1 está descartado por medición, no por opinión.

**2. Apagar `keep_peak` sí elimina el artefacto por completo**, en los dos brazos que lo apagan,
sin perder ninguna noche cuando el segundo pase sigue suelto (brazo B).

**3. El brazo más fiel al paper pierde 12 noches confirmadas**, repartidas en cuatro volcanes:
Planchón-Peteroa 5, Isluga 3, Lastarria 2, Tupungatito 2. Las cinco del primer tramo se
investigaron una por una y son **un solo mecanismo**: el primer pase entrega entre 0 y 2 píxeles,
el Test 1 integrado sí encuentra la señal con 65 a 98, y lo que llega a publicarse depende de
`keep_peak` o del segundo pase suelto. Las siete del segundo tramo quedan por investigar con
`investigar_perdidas.py`, pero el patrón es el mismo en las cinco ya miradas.

## Qué se concluye

**El eje del experimento no contiene la solución.** Las dos reglas que se pusieron en cuestión
—conservar el pico del Test 1 cuando el filtro contextual no deja nada, y correr el segundo pase
sin las condiciones del paper— son ambas infieles a Coppola, y aun así el sistema depende de
ellas para ver señal que MIROVA publica. Quitarlas por separado empeora las cosas; quitarlas
juntas pierde doce noches confirmadas.

Eso deja el problema donde la investigación de las cinco noches lo había puesto: **el Test 1
integrado detecta la señal y algo aguas abajo la anula.** Ese algo es la intersección con la
máscara contextual, que se introdujo en S99 y no está en el paper, donde el Test 1 es un camino
de detección propio y no un candidato a filtrar.

**La recomendación es no adoptar ningún brazo** y pasar la hipótesis del Test 1 por las tres
preguntas de la misión. Adoptar B —el que más cerca estuvo— cerraría el problema en falso:
quitaría el artefacto conservando un segundo pase que sabemos que no es el de Coppola, y con una
paridad que empeora respecto de hoy.

## Límites de este resultado

- Seis volcanes de once, tres meses, sólo VIIRS 375 m. No dice nada de MODIS ni de la banda M.
- Las siete pérdidas nuevas del segundo tramo no están investigadas una por una.
- La cota que decide si dos detecciones son el mismo objeto es una cota **inferior**: descarta
  con seguridad lo distinto, pero puede aceptar como igual algo que no lo sea.
- La paridad de magnitud se mide contra un ground truth cuya cobertura es parcial (D2 del
  catálogo) y que llega hasta el 2026-09-07.
