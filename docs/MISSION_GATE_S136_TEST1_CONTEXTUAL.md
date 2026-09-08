# Gate MISSION — retirar la intersección contextual del Test 1 (S136)

> Hipótesis que dejó abierta el A/B de S135: **el Test 1 integrado no debe intersectarse con la
> máscara contextual**. Este documento pasa las 3 preguntas de `docs/MISSION.md` ANTES de tocar
> nada. Read-only: no se modificó código ni perfiles.

## Qué es exactamente el mecanismo en cuestión

`pipeline/process_viirs.py:1773-1791`. Cuando el Test 1 gana la selección
(`final_hotspot_source == "test1"`) y el sensor es VIIRS 375 m (`"I04" in bands`), la máscara del
Test 1 se **intersecta** con la máscara contextual dNTI: un píxel del Test 1 sólo sobrevive si
además es anómalo contra sus 8 vecinos. `keep_peak` es el guard que rescata siempre el píxel más
caliente de esa máscara, para que el cráter no se pierda.

Los dos flags se encendieron juntos en S100 (PR #340, «ctxpeak») y hoy están en `true`
(`pipeline/profiles/mirova_equivalent.yaml:315-316`, verificado leyendo `pipeline.profile`).
**Sólo aplica a VIIRS 375 m**: MODIS y la banda M no tienen este bloque.

Consecuencia para D19: `keep_peak` y esta intersección son **el mismo bloque**. Apagar la
intersección vuelve a `keep_peak` irrelevante, porque `keep_peak` sólo existe para mitigar el
falso negativo que la intersección introduce.

## Pregunta 1 — ¿está documentado en papers MIROVA core? **SÍ, y a favor de retirarlo**

Cita verbatim, `documentacion/sp426_5.txt:298-300` (Coppola 2016a SP426.5, sección «Fixed NTI
threshold»):

> «Pixels that satisfy Test 1 are flagged as `active' and subsequently discarded (unsuitable) for
> further steps.»

Y el cierre de los tests contextuales, `sp426_5.txt:324`:

> «In addition, pixels flagged as `active' by means of tests 2 and 3 are subsequently eliminated
> from further analysis.»

En Coppola el Test 1 es un **camino de detección propio**: un píxel que lo satisface ya es activo
y **sale** del pool; no se somete después a los Tests 2 y 3. Los conjuntos se **unen**
(Test 1 ∪ (Test 2 ∧ Test 3)), no se intersectan. La intersección que corre hoy es la operación
contraria a la del paper.

**Veredicto P1: pasa.** Retirar la intersección es acercarse al literal, no alejarse.

## Pregunta 2 — ¿cierra una divergencia documentada? **SÍ**

`D19` (abierta) es este mismo bloque. Retirar la intersección la cierra por la raíz en vez de por
el guard.

**Veredicto P2: pasa.** No hace falta llegar a la pregunta 3.

## La tensión que esto abre: D10

`docs/MIROVA_DIVERGENCES.md:1201-1214`. La intersección se adoptó en S100 por una razón medida,
no por gusto: sobre el glaciar de Tupungatito el Test 1 integra el mosaico invernal nieve/roca
entero y la magnitud se infla **8-19×** contra MIROVA. El A/B pareado de S100 (416 pares) la curó
a 1,33× sin perder detecciones. Y S103 probó explícitamente la hipótesis «esto es un parche del
sec³» con un A/B de 3 brazos: quedó **refutada** — nadir sin ctxpeak dio 2,43× peor (A66,
mecanismos ortogonales: el área contra el fondo del ROI).

Así que la intersección es infiel al paper **y** cura un problema real. Ese es exactamente el
caso que `MISSION.md` prevé en «Si encontrás que el literal puro pierde recall»: la respuesta no
es conservar el parche ni quitarlo a secas, sino **buscar qué mecanismo documentado estamos
pasando por alto** que hace que MIROVA no necesite el parche.

Candidato ya escrito en el propio catálogo (anti-patrón «Cloud mask», verificado verbatim en
S128 contra Laiolo 2026 p. 4): MIROVA **filtra por distancia e intensidad y por doble conteo
entre detectores, quedándose con el 12 %** de las detecciones (9.712 de 82.329), y su mitigación
de nube es quedarse con el **máximo diario**. Nada de eso está implementado. Es la clase de
mecanismo que podría explicar por qué su magnitud no se infla sin necesitar una intersección que
el paper no describe.

## Lo que hay que remedir antes de diseñar el A/B

Las dos mediciones que sostienen el estado actual son **del régimen de fondo anterior**, y una de
ellas ya quedó sin respaldo:

| medición | qué dice | por qué hay que remedirla |
|---|---|---|
| D10 S99: «contextual puro crea **31 FN** en Tupungatito» (cráter embebido) | justifica `keep_peak` | el brazo B de S135 es contextual puro y da **0 pérdidas** en 260 noches, con Tupungatito entre los 6 volcanes (28 noches). Ventanas y tamaños distintos, así que no está refutada — pero **hoy no tiene respaldo** |
| D10 S100 / S103: Tupungatito 18,9× → 1,33×; nadir sin ctxpeak 2,43× peor | justifica la intersección | ambas son previas a `#535` (S126), que apagó la máscara de nube y bajó el fondo global 6-8 K en nevados. El bloque de arranque de S136 ya declara que los conteos de ese régimen no valen |

Es el patrón A87/A90: un número que dejó de medir lo que medía porque el corpus o el régimen se
movió debajo.

## Recomendación

1. **Pasa el gate**: la hipótesis puede investigarse (P1 y P2 dan SÍ).
2. **No es un A/B de dos brazos.** El eje correcto tiene tres estados —intersección actual /
   contextual puro (brazo B de S135) / **sin intersección**— y el brazo nuevo es el tercero, que
   nunca se corrió en este régimen.
3. **Medir primero, sin tocar pipeline**: la magnitud de Tupungatito y de los nevados con el
   código de hoy, para saber si el 18,9× que justificó la intersección sigue existiendo después
   de nadir-fijo y de `#535`. Si ya no existe, la intersección quedó sin función y retirarla es
   sólo volver al literal. Si existe, el A/B debe incluir el mecanismo de Laiolo (máximo diario)
   como cuarto brazo, no elegir entre parche y pérdida.
4. Cualquier cambio en `pipeline/` requiere tag defensivo y confirmación explícita de Nicolás
   (A45), y criterio pre-registrado antes de ver los datos (A18/A91).

---

## Adenda S136 — la medición del punto 3 ya se hizo (read-only)

`experiments/_s136/RESULTADO_MEDICION.md`. Resumen: **la pregunta no tiene respuesta read-only.**
La paridad de hoy está en banda en los 11 (Tupungatito 0,65× con n=154 antes de `#535`; 0,87× con
n=6 después), pero esos records llevan el filtro puesto, así que no distinguen «el filtro cumple
su función» de «el filtro ya no hace falta». Y el único campo pre-filtro persistido
(`n_test1_pixels`) **quedó refutado como proxy**: cuenta píxeles del ROI sobre el fondo
(`test1_integrated.py:285`), no extensión de anomalía — el control Láscar tiene el mismo footprint
que el glaciar de Tupungatito.

Consecuencia para el punto 3 de la recomendación: **no se puede saltar el reproceso**. El probe en
CI debe instrumentar `delta_L_integrated` antes y después del recorte, y el
`final_hotspot_source` **legacy** de la línea 1779 (el persistido lo sobrescribe
`resolve_honest_anchor` en la 2006 y no sirve para esto).
