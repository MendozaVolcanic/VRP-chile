# Caso A2 de la batería del Apéndice A: criterio pre-registrado para una erupción de flanco (S146)

> Escrito el 2026-09-20, ANTES de escribir el script evaluador y ANTES de abrir ningún JSON de
> salida de la batería en esta sesión. El hash de este archivo se anota en
> `docs/audit_s146/A2_RESULTADO_VARA_CORREGIDA.md`. Si este archivo cambia después de esa anotación,
> el pre-registro queda invalidado y hay que decirlo.

## 0. Contaminación declarada: qué sabía quien escribe esto

Este pre-registro NO es ciego, y conviene decirlo de entrada. Antes de escribirlo leí:

- `docs/audit_s145/A2_EL_FALLO_ES_DEL_CRITERIO.md`, que da los cuatro cúmulos del mejor brazo en A2:
  7,37 a 10,86 km de la cumbre, rumbos 75,8° a 104,0°, hasta 58,3 MW.
- `docs/audit_s138/EJE_5_bateria_apendice_instrumento.md` §1, que ubica la máscara de alerta de la
  figura A2 del autor a 10,98 km y rumbo 83° del centro de la grilla, y da separaciones de 2,5 a
  3,6 km entre nuestros cúmulos y ese punto en los cuatro brazos que guardan posición.
- `experiments/_s136/conformidad_apendice.py`, que ya trae una evaluación "post hoc" de A2 contra un
  punto a 9,6 km y rumbo 83° con radio de 3 km. Ese punto salió de la figura sin script (S138, H7).

O sea: sé aproximadamente dónde cayeron nuestros cúmulos y sé que, con casi cualquier caja razonable
puesta al este, el mejor brazo acierta. Un criterio anclado en esos cúmulos, o en el punto "post hoc"
de S137, sería un criterio ajustado al resultado. Por eso este documento hace tres cosas:

1. **Ancla el punto de referencia en una fuente externa e institucional** (el Boletín del Global
   Volcanism Program), que publicó la coordenada de la fisura años antes de que este proyecto
   existiera. No usa nuestros cúmulos ni el punto de S137.
2. **No inventa un radio nuevo**: usa el mismo de 5 km que la batería ya aplicaba a los nueve casos.
   La vara se traslada, no se agranda.
3. **Pone el peso de la prueba en los controles con nulo medido** (§4), que son lo único que no
   conozco de antemano: nadie midió todavía si una caja del mismo tamaño puesta a la misma
   distancia pero en otro rumbo sale vacía.

Lo que sigue siendo cierto pese a todo: si el resultado del tiempo 2 es "acierto", eso no sorprende a
nadie y vale poco por sí solo. Lo que puede aportar información nueva son los nulos y el
comportamiento de los otros siete brazos.

## 1. El fenómeno: dónde estaba el calor el 7 de abril de 2010

Eyjafjallajökull tuvo en 2010 dos erupciones distintas en dos lugares distintos. La primera fue
efusiva y de flanco: una fisura corta con fuentes de lava de tipo hawaiano en el paso de
Fimmvörðuháls, el portezuelo libre de hielo entre los casquetes de Eyjafjallajökull y Mýrdalsjökull.
La segunda fue explosiva y subglacial, en la caldera de la cumbre, y es la de la ceniza que cerró el
espacio aéreo europeo. La fecha del caso A2, 7 de abril, cae dentro de la primera y una semana antes
de la segunda. Ese día la cumbre estaba fría y bajo hielo; el único material incandescente expuesto
era la lava del flanco.

Fuente: Global Volcanism Program, 2010. Report on Eyjafjallajokull (Iceland). Bulletin of the Global
Volcanism Network, 35:3. Smithsonian Institution. https://doi.org/10.5479/si.GVP.BGVN201003-372020
(el sitio `volcano.si.edu` responde con un muro de verificación a las descargas automáticas; leí la
copia archivada del 2024-07-29:
`https://web.archive.org/web/20240729103950id_/https://volcano.si.edu/ShowReport.cfm?doi=10.5479/si.GVP.BGVN201003-372020`).
Citas textuales del informe:

- "From 20 March to 12 April 2010 the eruption's first phase occurred from a fissure 9 km ENE of the
  summit, an area named Fimmvörðuháls, located between the Eyjafjallajökull and Mýrdalsjökull
  icecaps".
- "The eruption broke out with Hawaiian-style fire fountains (figure 5) on a ~ 500-m-long,
  NE-oriented fissure (at 63° 38.1' N, 19° 26.4' W)."
- "Lava advanced N into the Hrunagil and Hvannárgil valleys".
- "On the evening of 31 March, scientists noted the opening of a new short fissure immediately N of
  the previous one."
- "By 7 April lava emissions had stopped from the original craters, but continued at the 31 March
  fissure. When IES surveyed the new landscape on 7 April (figure 9), they found 1.3 km2 of new
  lava".
- "The second, more explosive eruptive phase, began on 14 April 2010 at the subglacial, central
  summit caldera."

La Oficina Meteorológica de Islandia confirma la ubicación cualitativa, sin coordenada
(https://en.vedur.is/about-imo/news/nr/1845, nota del 21-03-2010): "The eruption fissure is about
0.5 km long and is located on the norhern side of Fimmvörðuháls, east of the Eyjafjallajökull ice
cap."

**Punto de referencia de A2, fijado acá**: 63° 38,1' N, 19° 26,4' O, es decir **lat 63,6350,
lon -19,4400**. Respecto de la coordenada de cumbre de `apendice_a.yaml` (63,633, -19,633, que es la
misma que encabeza el informe del GVP) queda a **9,53 km con rumbo 88,6°** (cálculo por haversine,
el mismo de `conformidad_apendice.py`; lo repite el script evaluador y lo imprime).

Debilidades de este punto, declaradas:

- El GVP dice "9 km ENE" y su propia coordenada da 9,5 km casi al E exacto (88,6°). La discrepancia
  es de redacción del boletín; uso la coordenada, que es el dato más preciso, y no el texto.
- La coordenada es la de la fisura del 20 de marzo. El 7 de abril la que seguía activa era la del
  31 de marzo, "immediately N" de la primera, sin coordenada propia publicada. La lava avanzó hacia
  el norte. El calor del 7 de abril está entonces en la fisura o algo al norte de ella, a una
  distancia que el informe no cuantifica (el campo de lava completo medía 1,3 km²).
- La precisión de la coordenada es de 0,1 minuto de arco, unos 0,19 km en latitud.

Coherencia con el paper, como segunda pata y no como ancla: en la figura A2 (página 19 del PDF,
renderizada a imagen en esta sesión) la máscara de alerta del autor es un grupo de celdas en torno
a x = 35 a 37, y = 26 a 28 de una grilla de 51 por 51 km cuyo centro es la celda 26. Eso es unos
10 km al este del centro y 1 km al norte, y nada en el centro de la grilla. El título de la figura
dice "07-Apr-2010 04:40:00". La lectura a ojo es mía; la medición con script es la de S138 (10,98 km,
83°). El autor detecta el flanco, no la cumbre.

## 2. La regla general: cuándo un caso se evalúa contra un punto que no es la cumbre

Un caso POSITIVO de la batería se evalúa contra un punto distinto de la coordenada del catálogo si,
y sólo si, se cumplen LAS DOS condiciones siguientes. Ninguna mira nuestras detecciones.

**Condición 1, fuente externa.** Un informe institucional (Boletín o informe semanal del GVP, o el
observatorio nacional a cargo del volcán) documenta que, EN LA FECHA DEL CASO, la boca activa estaba
fuera de la cumbre, y publica su coordenada. Esa coordenada tiene que quedar a más de 5 km de la
coordenada del catálogo (si queda a 5 km o menos, la caja de cumbre ya la contiene y no hay nada que
corregir).

**Condición 2, el propio paper.** La máscara de alerta que el autor publica en la figura del caso
está a más de 5 km del centro de su grilla, y del mismo lado que la boca de la condición 1 (rumbo a
menos de 45° de diferencia).

Si se cumplen las dos, el punto de referencia es **la coordenada de la fuente externa** (no la
máscara del autor medida en la figura, que depende de una lectura de imagen, ni nuestro cúmulo). Si
se cumple una sola, el caso se queda en la cumbre y la discrepancia se anota como pendiente.

Para los casos NEGATIVOS la regla no aplica nunca: no hay máscara ni boca activa que ubicar. Se
evalúan en la cumbre, igual que antes. Un negativo no puede "mejorar" por esta regla.

Cuando un caso pasa a evaluarse contra una boca de flanco, **la caja de la cumbre deja de contar
para ese caso**. Un cúmulo a menos de 5 km de la cumbre de Eyjafjallajökull el 7 de abril de 2010 no
es la erupción (la cumbre no estaba activa): es otro objeto, y contarlo como acierto sería el mismo
defecto de instrumento que S138 encontró (premiar "publicamos algo" en vez de "publicamos el objeto
del autor"). Esto hace la vara MÁS dura para los brazos que hoy aparecen "conformes" en A2 con un
cúmulo junto a la cumbre.

Aplicación a ciegas a los otros ocho casos, con lo que ya está en el repo (posiciones de máscara de
S138 §1.1, medidas desde las figuras, y notas de `apendice_a.yaml`):

| caso | condición 1 | condición 2 | punto de evaluación |
|---|---|---|---|
| A1 Bezymianny | no se buscó boca de flanco; máscara en la cumbre lo hace innecesario | máscara a 1,00 km del centro: no | cumbre |
| A2 Eyjafjallajökull | sí, GVP BGVN 35:3, 9,53 km | máscara a ~11 km al E: sí | **fisura GVP** |
| A3 Erta Ale | innecesario | 0,74 km: no | cumbre |
| A4 Dubbi | negativo | sin máscara | cumbre |
| A5 Ubinas | innecesario | 1,29 km: no | cumbre |
| A6 Villarrica | innecesario | 0,21 km: no | cumbre |
| A7 Tolbachik | negativo; además la erupción de flanco empezó el 27-nov, 7 días DESPUÉS de la fecha del caso, así que en la fecha no había boca activa | sin máscara | cumbre |
| A8 Etna | innecesario | 1,15 km: no | cumbre |
| A9 Stromboli | negativo | sin máscara | cumbre |

Como la condición 2 es necesaria y en los cinco positivos restantes la máscara está a menos de 1,3 km
del centro, no hizo falta buscar informes del GVP para ellos: la regla ya los deja en la cumbre.

## 3. La tolerancia espacial, fijada antes de mirar

**Radio: 5,0 km alrededor del punto de referencia.** Es el mismo `INNER_KM = 5.0` que la batería
aplica a los nueve casos (el ROI1 del paper, D18). La razón principal es de método: así la corrección
cambia UNA sola cosa (el centro de la caja) y no agrega ningún parámetro libre que yo pudiera haber
elegido mirando los cúmulos.

La justificación física, para comprobar que 5 km no es absurdo en ninguno de los dos sentidos:

- Tamaño del píxel MODIS fuera de nadir. El píxel de 1 km en el nadir crece hasta cerca de 2 km a lo
  largo de la órbita por 4,8 km a lo largo del barrido en el borde de la pasada (valor nominal del
  instrumento, de memoria y sin cita a mano: SOSPECHA hasta cotejarlo con el MODIS L1B User Guide).
  Una fuente puntual puede quedar registrada en un píxel cuyo centro está hasta a medio píxel de
  ella: hasta unos 2,4 km en el peor caso.
- Extensión de la fuente. No es un punto: fisura de 0,5 km, segunda fisura "inmediatamente al N",
  1,3 km² de lava que avanzó al norte hacia dos quebradas. Uno a dos kilómetros de corrimiento del
  centro de calor respecto de la coordenada publicada es esperable.
- El centroide del cúmulo es un promedio ponderado de varios píxeles, que además pueden incluir
  vecinos tibios.
- Geolocalización de MODIS y precisión de la coordenada: décimas de km, despreciables.

Sumado, un corrimiento de hasta 4 a 5 km entre la coordenada del GVP y el centroide de un cúmulo que
sí es la lava es físicamente posible; más de 5 km ya pide otra explicación. Del otro lado, una caja
de 5 km de radio a 9,5 km de la cumbre NO alcanza la cumbre (queda a 4,5 km de ella en su borde más
cercano) ni la costa sur, que es el confusor que el propio autor nombra.

Sensibilidad, informativa y NO decisoria: el script reporta también el resultado con radio 3 km. Si
con 3 km cambia el veredicto de un brazo, el acierto se rotula "frágil" en la tabla, pero el
veredicto lo da el radio de 5 km.

## 4. Qué cuenta como ACIERTO, FALLO e INDECIDIBLE, y los controles

Universo de pasadas: el mismo de S136, todas las pasadas nocturnas MODIS de la fecha UTC del caso
que el brazo procesó. No lo cambio, para mover una sola pieza. Como dato secundario se reporta
además el resultado usando sólo la pasada de la figura del autor (04:40 UTC).

Para A2, por brazo:

- **ACIERTO**: al menos una pasada tiene cúmulo primario con `vrp_pc_mw > 0` y posición
  (`pc_lat`, `pc_lon`) a 5,0 km o menos del punto GVP, Y los controles N1 de ese brazo salen vacíos.
- **FALLO**: el brazo guarda posiciones y ninguna pasada cumple lo anterior. Un cúmulo junto a la
  cumbre no salva el caso.
- **INDECIDIBLE (SIN DATO)**: el brazo no guarda `pc_lat`/`pc_lon`. Con sólo la distancia a la
  cumbre `d`, la distancia al punto GVP está acotada entre `|d - 9,53|` y `d + 9,53` (A93). Un
  acierto NO se puede probar sólo con el radio. Sí se puede probar el fallo: si para todas las
  pasadas con magnitud la cota inferior supera 5 km (o sea `d < 4,53` o `d > 14,53`), es FALLO. En
  cualquier otro caso es INDECIDIBLE, y eso no es ni acierto ni fallo.
- También INDECIDIBLE si el brazo acierta pero alguno de sus controles N1 no sale vacío: en ese caso
  la vara regala aciertos en esa escena y el acierto no distingue nada.

Para los otros ocho casos el predicado es el de S136 sin tocar (incluido su control de validez por
NTI en A5, A6 y A8).

Aprobación del brazo: 9 de 9, como fijó S136. No se mueve.

### Controles, cada uno con su nulo medido (A110)

**C0, el instrumento está vivo.** (a) Identidad: mi reimplementación del predicado, con la vara
vieja, tiene que reproducir los veredictos ya commiteados de todos los brazos y casos; si no los
reproduce, nada de lo demás vale. (b) Control positivo: con radio 0,01 km todos los positivos tienen
que caer a fallo; si no caen, el predicado no está mirando la distancia.

**C1, los negativos siguen negativos.** A4, A7 y A9 con la vara nueva tienen que dar, brazo por
brazo, el mismo veredicto que con la vieja. Por construcción de la regla esto es una identidad, así
que por sí solo prueba poco; se reporta porque se pidió y porque una diferencia delataría un error
del script. El control con contenido es N2.

**N1, la caja rotada en la misma escena (nulo de A2).** La misma caja de 5 km, a la misma distancia
de la cumbre (9,53 km), pero con el rumbo girado 90°, 180° y 270° respecto del de la fisura (o sea
aproximadamente al S, al O y al N). Las cuatro cajas son disjuntas (centros a 13,5 km entre
vecinas). En ninguna de las tres rotadas hay nada volcánico que detectar; la del sur además mira
hacia la costa, que es el confusor declarado del caso. Esperado: las tres vacías en todas las
pasadas. Si alguna tiene cúmulo con magnitud, el acierto de ese brazo en A2 pasa a INDECIDIBLE.

**N2, la caja desplazada en los otros ocho casos (tasa de regalo de la vara).** El mismo
desplazamiento (9,53 km; rumbos 88,6°, 178,6°, 268,6° y 358,6°) aplicado a la coordenada de cada uno
de los otros ocho volcanes, por brazo. Ahí no hay ninguna fisura documentada, así que todo cúmulo
que caiga en esas cajas es un acierto regalado. Se reporta la tasa: cajas con cúmulo sobre cajas
evaluadas, por brazo y total. Esperado: cero o casi cero. No fijo un umbral de aprobación para N2
porque no tengo base para elegirlo; se reporta el número y se lee junto con N1.

**Límite de N1 y N2, declarado antes de medirlos.** La batería guarda UN cúmulo por pasada, el
primario, y la selección del pipeline está anclada al cráter: si hay un cúmulo cerca de la cumbre,
ése es el que queda guardado, y uno lejano en la misma pasada no aparece. Los nulos miden entonces
"el cúmulo primario cae en la caja", no "hay alguna alerta en la caja". Eso sesga los nulos hacia
vacío en las pasadas donde hay algo cerca de la cumbre. El mismo sesgo juega EN CONTRA del acierto de
A2 (un cúmulo espurio junto a la cumbre taparía la fisura), así que no favorece al resultado, pero sí
debilita a los nulos como prueba. Medir alertas por píxel exigiría re-procesar los gránulos, y eso
sólo corre en GitHub Actions.

**Las dos preguntas del instrumento**, que el encabezado del script debe responder: (1) si lo que
mide estuviera roto (la vara regala aciertos), ¿fallaría? Sí, por N1 y N2. (2) Si el instrumento
estuviera muerto (no mira posiciones), ¿el resultado se vería distinto? Sí, por C0: identidad y
control positivo.

## 5. Qué NO decide este criterio

- No decide adoptar nada. Un 9 de 9 mide fidelidad al Apéndice A en MODIS, nueve escenas, una fecha
  por caso. No dice nada sobre la paridad con MIROVA en las pasadas del régimen actual.
- No arregla los otros defectos del instrumento que S138 documentó (mezcla de pasadas de dos noches,
  cúmulos del camino D con tope de 5 MW contados como aciertos, sensibilidad al radio en los casos de
  cumbre). Esos siguen como estaban.
- No verifica que el cúmulo sea "el objeto del autor" celda por celda; verifica que esté donde una
  fuente independiente dice que estaba la lava.
