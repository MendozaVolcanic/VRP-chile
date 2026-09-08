# Pre-registro del A/B de D1 y D2 — para la decisión de Nicolás

> **DECIDIDO por Nicolás el 2026-09-07.** Sus tres respuestas, textuales en lo esencial:
> autoriza tocar el pipeline; corre sobre los seis volcanes que deciden; y **«no debemos perder
> nada que MIROVA esté entregando, debemos ser lo más fiel posible y entender por qué sucede y
> arreglar cuando diferimos»**. Esa tercera frase endurece el criterio 1 de un 10 % a **cero**, y
> cambia qué se hace ante una diferencia: no se descarta el brazo, se investiga el mecanismo.
> Todo el documento quedó actualizado con eso; §«Lo que necesito de vos» se conserva al final
> como registro de lo que se preguntó.
>
> Estado de ejecución: tag defensivo `pre-s135-second-pass-condicionado` creado y subido; el
> segundo pase condicionado está implementado detrás de `ENABLE_SECOND_PASS_CONDITIONED`, en OFF
> en el perfil operacional, con 17 tests propios; los cinco perfiles de brazos existen y se
> verificó que **cada uno lee lo que declara**. Números de apoyo, todos de script:
> `experiments/_s135_probe_etapas/D19_HOY.md` y `RESULTADOS_PASO0.md`.
>
> **Tercera versión.** La primera midió el tamaño de efecto sobre un denominador que se movía
> solo y puso un umbral inalcanzable por construcción; las dos cosas las encontró un verificador
> con contexto limpio (gravedad 5) y están corregidas.

## El fenómeno, primero

En un cono nevado, de noche, el cráter no es lo más caliente que hay alrededor. La temperatura
sigue la altitud: la cumbre irradia a unos 250-260 K y el pie del cono, mil metros más abajo y
sin nieve, varios grados más. Dentro del disco de 3 km con que el Test 1 integra la energía del
infrarrojo medio, el píxel más caliente suele ser **el borde del disco**, no el cráter.

El pipeline hace dos cosas con eso, y las dos son discutibles:

**Una.** Cuando el filtro contextual no deja ningún píxel —la máscara de anomalía respecto de los
vecinos está vacía, que es lo normal en una noche tranquila— una regla llamada `keep_peak`
conserva igual el píxel más caliente del disco. Ese píxel del flanco se publica como una
detección *en el cráter, a 0,0 km*, con una magnitud de centésimas de megavatio medida contra un
anillo que se superpone al disco que está midiendo. En los volcanes nevados ese píxel está a
menudo **más frío que el fondo global de la escena**. Fabrica un nivel base falso: un inicio real
de 0,1 MW en el cráter queda indistinguible de él.

**Dos.** El segundo pase del algoritmo, que Coppola diseñó para recuperar los píxeles del borde
de un cúmulo ya detectado, corre en nuestro pipeline **aunque no se haya detectado nada** y sin
restringirse a los vecinos de lo detectado. El paper es explícito en las dos condiciones
(`documentacion/sp426_5.txt:329-341`). Corriendo suelto es una segunda detección más permisiva
que la primera, no una recuperación.

**Por qué no se arregla y ya.** El mismo `keep_peak` es el que entrega, en Lastarria, el campo
fumarólico del Lazufre a 2,2 km del cráter, que es actividad real y que MIROVA publica. Apagarlo
sin medir destruye señal buena (reglas A83/A84). Y el paso 0 mostró algo que ata las dos cosas:
hoy, con el segundo pase corriendo suelto, ese campo fumarólico **lo rescata el segundo pase**
aunque `keep_peak` esté apagado. Si se arregla el segundo pase, deja de rescatarlo.

> El costo de apagar `keep_peak` depende de si el segundo pase está arreglado o no.
> **No son dos decisiones: es una, con varias combinaciones.**

## De qué tamaño es el problema hoy (corregido)

Medido sobre **todos** los records de VIIRS 375 m, que es el denominador que no se mueve:

- El mecanismo produce el **39,0 %** [34,5-43,7] de los records, contra 49,1 / 40,0 / 49,5 % en
  junio, julio y agosto. **Está dentro de la variación mensual: no hay caída demostrada.**
- El artefacto se publica a razón de **unos diez records por día** en los 11 Tier A, tasa
  prácticamente igual a la del régimen anterior (11,1/día).
- Lo que sí cambió: de esa población, la porción que llega por la rama donde `keep_peak` decide
  bajó de **87 %** a **62,6 %**. El artefacto **se mudó de rama**, y hoy más de un tercio queda
  fuera del alcance de este experimento.

## Lo que se decide

| | qué haría | qué necesita |
|---|---|---|
| **D1** | apagar `keep_peak`: si el filtro contextual no deja píxeles, no se publica un cúmulo del Test 1 | sólo un flag de perfil (`ENABLE_TEST1_CONTEXTUAL_KEEP_PEAK`), **sin tocar código** |
| **D2** | condicionar el segundo pase a que el primero haya detectado algo, y restringirlo a la vecindad de 8 de lo detectado | **código nuevo** en `pipeline/detection_context.py` (hoy devuelve `active_mask \| newly_active` sin ninguna de las dos condiciones, l. 878) → **A45: tag + tu autorización** |

D2 no es un parche nuestro: es volver a lo que dice el paper, y pasa la puerta 1 de MISSION con
cita verbatim. D1 tampoco agrega nada: quita una regla que S100 introdujo con una justificación
—«el pico es el cráter»— que el probe de S135 mostró falsa en los nevados de señal débil.

## Los brazos

| brazo | `keep_peak` | segundo pase | qué responde | ¿toca código? |
|---|---|---|---|---|
| **A** (control) | ON | suelto | producción de hoy | no |
| **B** | OFF | suelto | ¿alcanza con quitar `keep_peak`? | no |
| **E** | ON | **apagado entero** | cota superior del efecto del segundo pase | no (flag `ENABLE_SECOND_PASS_ADJACENT`) |
| **C** | ON | condicionado | ¿alcanza con arreglar el segundo pase? | **sí** |
| **D** | OFF | condicionado | fidelidad literal en los dos puntos | **sí** |

El brazo **E** lo señaló el verificador y vale la pena: apagar el segundo pase entero es más
brusco que condicionarlo, pero **acota por arriba** cuánto depende de él el rescate del campo de
Lastarria, y se corre con un flag que ya existe. Si no autorizás tocar código, A + B + E ya
responden la pregunta principal, aunque no den la solución fiel.

## Universo y ventana

- **Volcanes**: los **seis que deciden** (Isluga, Láscar, Lastarria, Puyehue-Cordón Caulle,
  Planchón-Peteroa, Tupungatito), estratificados como manda A83 en **focales** (Láscar,
  Lastarria) y **nevados de señal débil** (los otros cuatro). Un criterio único los mezcla y
  esconde el daño. Los cinco restantes quedan fuera del reproceso por costo, y su tabla se
  completa después si el resultado se adopta.
- **Ventana**: 2026-06-01 → 2026-08-31, reprocesada **con el código de hoy** en todos los brazos.
  No sirve comparar contra los records ya guardados: se grabaron con otro régimen de fondo. Y no
  sirve usar sólo el régimen nuevo: tiene nueve días, de los cuales tres tienen ground truth.
- **Sensor**: VIIRS 375 m. Es donde vive el mecanismo; MODIS y VIIRS 750 m no llevan `keep_peak`.

## Criterio pre-registrado

En las unidades del objeto (A91), fijado antes de ver los resultados.

**1. Lo que no se puede perder (falsos negativos sobre señal real).**
Una «noche cat-b» es una noche con alerta de MIROVA en VIIRS 375 m que el brazo control publica
como detección en el cráter. **FN = noches cat-b que el control publica y el brazo no**, por
volcán y con su denominador. Los denominadores reales en la ventana, medidos:

| volcán | noches cat-b | de ellas por `test1_roi` | 10 % = |
|---|---|---|---|
| Isluga | 74 | 38 | 7,4 |
| Láscar | 61 | 39 | 6,1 |
| Lastarria | 51 | 48 | 5,1 |
| Puyehue-Cordón Caulle | 37 | 10 | 3,7 |
| Planchón-Peteroa | 28 | 24 | 2,8 |
| Tupungatito | 28 | 28 | 2,8 |
| Chaitén 15 · Villarrica 14 · Copahue 3 · Nevados de Chillán 3 · Llaima 0 | | | <1,5 |

> **Umbral, decidido por Nicolás: CERO.** No se adopta un brazo que pierda **ninguna** noche que
> MIROVA esté entregando, en ninguno de los once volcanes. El 10 % que proponía la versión
> anterior queda descartado.

Y la consecuencia práctica, que es lo que cambia el trabajo: **una pérdida no descarta el brazo,
abre una investigación.** Si el brazo más fiel al paper pierde una noche que MIROVA publica, la
respuesta no es volver al comportamiento actual, es entender por qué el algoritmo literal no ve
lo que MIROVA sí ve. Las posibilidades son tres y hay que distinguirlas caso por caso, a nivel
de pasada:

1. **Nos falta algo que MIROVA hace** y no habíamos implementado. Se implementa.
2. **MIROVA lo publica por su supervisión humana**, no por su algoritmo (descarta nubes a mano,
   quita falsas alarmas a mano). Entonces el algoritmo literal *debe* no verlo, y lo que hay que
   arreglar es nuestra expectativa, no el código.
3. **Nuestra reconstrucción de esa noche difiere** por un dato de entrada distinto (granule NRT
   contra estándar, cobertura, geometría). Se documenta y no cuenta como pérdida algorítmica.

Los seis volcanes de la tabla siguen siendo los que **deciden** la adopción, por tener
denominador suficiente; los otros cinco se reportan igual y cualquier pérdida en ellos también
se investiga. La primera versión nombraba sólo a Lastarria, Tupungatito e Isluga, dejando fuera
a Láscar (61 noches) y a Puyehue (37): corregido.

**2. Lo que se quiere quitar (el nivel base falso).**
Un «record de nivel base falso» es un record summit de VIIRS 375 m con cúmulo de **un solo
píxel**, cuyo píxel está **más frío que el fondo global** de su propia escena, y **sin alerta de
MIROVA** esa noche. En el régimen vigente son 91, de los cuales sólo 57 (62,6 %) llegan por la
rama que este experimento puede mover.

> **Éxito = el brazo elimina al menos el 70 % de la porción alcanzable** (la que llega por
> `test1_roi`), medida sobre la misma ventana reprocesada.

La primera versión pedía el 70 % del total, que **ningún brazo puede alcanzar**: el 37,4 % que
llega por el path contextual no depende de `keep_peak` ni del segundo pase. Un umbral que ningún
brazo puede cumplir por construcción no es un criterio, es un veto encubierto. El resto —lo que
quede por el path contextual— se reporta como remanente conocido, y es material para otra
decisión, no para ésta.

**3. Lo que no debe empeorar (paridad de magnitud).**
La razón entre nuestra magnitud y la de MIROVA, emparejando por pasada (±20 min), mediana por
volcán. **La mediana agregada del brazo no puede alejarse de 1,0 más que la del control.**

**4. Desempate.** Si dos brazos cumplen 1, 2 y 3, gana el que esté **más cerca del paper**:
D sobre C sobre B sobre E. La fidelidad literal es el objetivo del proyecto, no un empate técnico.
Con el criterio 1 en cero, el orden de trabajo es: se corre D (el más fiel), se miran una por una
las noches que pierda respecto del control, se clasifica cada una en los tres casos de arriba, y
sólo si queda una pérdida del caso 1 sin explicación se baja a C o a B.

## Lo que este A/B no decide

- Qué es el objeto a 2,97 km al este del cráter de Villarrica que apareció en el probe del 31 de
  agosto. Es una pregunta volcanológica tuya.
- MODIS: el sesgo topográfico a 1 km quedó cerrado como irreducible en S114 (A82).
- El frontend ni la etiqueta *summit*: eso es D13, otra decisión.
- El tercio del artefacto que llega por el path contextual.

## Costo y riesgo

Tres o cinco reprocesos de tres meses sobre 11 volcanes en GitHub Actions, particionados por
volcán y brazo. Riesgo operacional bajo: cada brazo escribe en su propio directorio y el cron de
producción no los toca. El riesgo real es el otro: **si el brazo D gana y se adopta, cambia lo que
el operador ve en el dashboard todos los días**, con menos detecciones en el cráter en noches
tranquilas. Por eso el criterio 1 está puesto donde está.

## Lo que se preguntó y lo que se decidió (2026-09-07)

| pregunta | respuesta de Nicolás |
|---|---|
| ¿Autorizás tocar `pipeline/detection_context.py` para los brazos C y D? | **Sí.** Tag defensivo `pre-s135-second-pass-condicionado` creado antes del primer edit (A45); el cambio entró detrás de un flag en OFF, con 17 tests. |
| ¿Umbral del criterio 1? | **Cero pérdidas**, más exigente que el 10 % propuesto. «No debemos perder nada que MIROVA esté entregando.» |
| ¿Los 11 Tier A o los seis que deciden? | **Los seis**: Isluga, Láscar, Lastarria, Puyehue-Cordón Caulle, Planchón-Peteroa y Tupungatito. |
| (no preguntado, instruido) | **«Ser lo más fiel posible y entender por qué sucede y arreglar cuando diferimos.»** Incorporado al criterio 1 y al desempate: una diferencia se investiga, no se esquiva. |
