# S137 · Tres divergencias del paper corregidas a la vez: la batería del Apéndice A llega a 5 de 6 y 3 de 3

> Ocho brazos de la batería, tabla generada por `comparar_brazos_apendice.py` en
> `COMPARACION_8_BRAZOS.txt` (regla S91). Brazos nuevos: runs 34747955039 (fórmula) y 34747956519
> (prosa), con banda 22, sin compuerta de temperatura en los Tests 2 y 3, y fondo local de la magnitud.
> Criterio fijado en S136, sin cambios: 6/6 positivos y 3/3 negativos.

## El resultado

| brazo | positivos | negativos | cumple |
|---|---|---|---|
| B21, fórmula (lo de hoy) | 6/6 | 0/3 | no |
| B21, prosa | 2/6 | 3/3 | no |
| B22, fórmula | 4/6 | 2/3 | no |
| B22, prosa | 4/6 | 3/3 | no |
| B22 sin compuerta, fórmula | 4/6 | 2/3 | no |
| B22 sin compuerta, prosa | 4/6 | 3/3 | no |
| B22 sin compuerta, fondo local, fórmula | 6/6 | 2/3 | no |
| **B22 sin compuerta, fondo local, prosa** | **5/6** | **3/3** | no |

El mejor brazo, con las tres correcciones y la conectiva de la prosa, reproduce ocho de los nueve
veredictos del autor. El que falta es Eyjafjallajökull, y falla por la evaluación, no por la detección.

## Qué hizo cada corrección, en el caso que la motivó

Villarrica (A6), pasada de las 05:55, la de la figura del paper:

| brazo | primer paso | cúmulo | VRP |
|---|---|---|---|
| B21 | 100 píxeles en la escena | a 1,0 km, 21 píxeles | 0,59 MW, apoyado en ruido |
| B22 | 0 píxeles | a 0,8 km | 0,0 MW |
| B22 sin compuerta | 2 píxeles | en el cráter, a 0,81 km | 0,0 MW |
| B22 sin compuerta, fondo local | 2 píxeles | en el cráter, a 0,81 km | **0,539 MW** |

Cada paso quitó un bloqueo distinto: la banda 22 quitó el ruido, sacar la compuerta devolvió la
detección del cráter helado, y el fondo local le devolvió la magnitud. La predicción pre-registrada
(Villarrica pasa a conforme) **se cumplió en los dos brazos**.

## Dos lecturas que no hay que tomar al pie de la letra

**El 6 de 6 del brazo con la fórmula no es mejor que el 5 de 6.** Su "conforme" en Eyjafjallajökull sale
de un cúmulo de 0,31 MW a 1,2 km al **norte** de la cumbre (pasada de las 03:00). La figura A2 del autor
pone su detección a 9,6 km al **este**. Es otro objeto, del mismo tipo que el que hoy cuenta la banda
21. Además ese brazo sigue detectando en Dubbi, donde el autor no detecta (1,2 MW a 4,1 km).

**El faltante del brazo de la prosa es de la evaluación.** Con la evaluación secundaria declarada post
hoc (cúmulo a 3 km o menos de la detección del autor), Eyjafjallajökull es conforme en **3 pasadas**. Esa
evaluación no se usa para adoptar, porque se definió después de ver la figura.

## El riesgo pre-registrado

Se anotó que el fondo local podía volver falso positivo algún negativo con cúmulo detectado en 0 MW. En
el brazo de la prosa **no pasó**: los tres negativos siguen sin publicar. En el de la fórmula Dubbi sigue
como falso positivo, pero ya lo era sin el fondo local.

## Lo que esto NO autoriza

- **Sobreajuste.** Son tres cambios evaluados sobre nueve escenas. Mitiga que ninguno es un parámetro
  libre: los tres son elementos literales del paper (banda L21ok, Tests 2 y 3 sin condición de
  temperatura, fondo de la ecuación 6 con los píxeles vecinos). Pero nueve escenas no son un A/B.
- **Adoptar.** Dos de las tres correcciones no existen como flag del pipeline: la compuerta dentro de
  los Tests 2 y 3 y el fondo local uniforme sólo están en la batería. Crearlas es código en
  `pipeline/process_*.py` y en `detection_context.py`, así que exige tag defensivo y confirmación de
  Nicolás (A45), y después un A/B sobre los Tier A. La compuerta aparece en unos 13 lugares de los tres
  sensores; el fondo local hoy es opt-in en 5 volcanes.
- **VIIRS.** Nada de esto se probó en VIIRS, que no tiene banda 22 pero sí tiene la compuerta y el
  fondo del anillo.

## Decisiones que quedan para Nicolás

1. Si se implementan como flags apagados en el pipeline las dos correcciones que hoy sólo viven en la
   batería (compuerta en los Tests 2 y 3, fondo local uniforme), con tag y tests, para poder correr el
   A/B en los Tier A.
2. Qué conectiva lleva ese A/B: la prosa es la única que cura los tres negativos en esta serie.
3. Si la evaluación de Eyjafjallajökull se corrige en la batería para que mida lo que el autor detecta,
   con la figura A2 como referencia, y desde qué sesión rige.
