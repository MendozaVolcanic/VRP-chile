# Diseño: sensibilidad por zona en el perfil experimental (S147)

> **Qué es este documento.** El diseño del paso 2 que pidió Nicolás: cómo bajar el umbral de
> detección donde sabemos que puede haber procesos volcánicos, sin inundarnos de calor no
> volcánico en los kilómetros de alrededor.
>
> **Qué NO es.** No es una adopción ni un plan de implementación aprobado. Nada de esto entra al
> pipeline sin pasar por el gate del proyecto (brainstorming de diseño, A/B con criterio
> pre-registrado y commiteado antes de correr, y ciclo A45 con tag defensivo y confirmación
> explícita). Tampoco entra **nunca** a `mirova_equivalent`.

## 1. El fenómeno, primero

Una anomalía térmica volcánica es un objeto chico. El lago de lava de Villarrica calienta su
propio píxel y entibia a los vecinos; un campo fumarólico levanta unas décimas de grado sobre unos
pocos cientos de metros. A 375 m de resolución, esas señales están **al borde de lo resoluble**, y
distinguirlas del ruido del sensor y de la textura del terreno es el problema central del sistema.

La tentación evidente es bajar el umbral hasta que aparezcan. El problema es qué más aparece.

**Cada píxel que miras es una oportunidad de equivocarte, y la cantidad de oportunidades crece con
el área.** Con VIIRS de banda I, el disco de 3 km alrededor del cráter tiene unos **200 píxeles**;
la escena de 25 km de radio con que trabaja el sistema tiene unos **14.000**. El mismo umbral,
aplicado a la escena entera, tiene **setenta veces más ocasiones** de confundirse que aplicado al
cráter.

Y las dos poblaciones no son comparables ni en su física. Cerca del cráter hay una fuente de calor
conocida, con una historia, y la probabilidad previa de que algo tibio sea volcánico es alta. A 20
km, un píxel caliente es casi siempre otra cosa: un incendio de pastizal, un salar que retiene
calor después del atardecer, una planta geotérmica, una faena minera, un flanco de roca oscura sin
nieve rodeado de glaciar.

De ahí sale el principio de diseño: **la sensibilidad y la especificidad no tienen por qué cambiar
juntas en todo el espacio.** Un umbral uniforme es la peor de las tres opciones posibles, porque o
es tan estricto que pierde el lago de lava, o es tan permisivo que inunda con incendios.

### El proyecto ya vivió este mecanismo, en su forma patológica

No es una analogía: es exactamente lo que S146 y S147 encontraron en el Test 1 integrado. Ese
criterio suma el exceso de radiancia del disco y lo compara contra una vara mal elegida, y el
resultado es que su valor de reposo con ruido puro vale `0,399·raíz(N)`, o sea que **crece con el
número de píxeles del disco**. Medido: el 90,9 % de los records de VIIRS 375 superan ese criterio
por puro ruido, contra el 11,9 % en MODIS, cuyo disco tiene siete veces menos píxeles.

O sea que el sistema ya tenía un umbral gobernado por el área, sin que nadie lo hubiera decidido.
Lo que este diseño propone es **decidirlo a propósito y en la dirección correcta**.

## 2. Lo que hay que respetar, y no es negociable

**Nada de esto toca `mirova_equivalent`.** Ese perfil vale porque reproduce a MIROVA literalmente,
y eso es lo que hace defendible el sistema frente a un tercero. Un umbral que depende de la zona
es, por construcción, una divergencia del clon. Vive en el laboratorio o no vive.

**No hay un discriminante físico mágico, y buscarlo está agotado.** S116 barrió 4.560 records
summit con todos los candidatos escalares por record: el mejor da AUC 0,859, pero su corte óptimo
es régimen dependiente y **cualquier corte global que rechace el 70 % del artefacto en nevados
destruye el 14 a 16 % de la señal real**. El único eje que separa el foco débil real del artefacto
a resolución gruesa es el **espacial**. Este diseño usa ese eje de frente, en vez de disfrazarlo de
física nueva.

**El sesgo topográfico de los nevados.** En volcanes con cumbre nevada, el campo de temperatura de
brillo en el infrarrojo medio está dominado por el gradiente de altitud, no por la actividad:
el valle tibio de baja altitud aparece como anomalía. Cualquier camino que mida exceso en **MIR
absoluto** hereda ese sesgo, y bajarle el umbral lo amplifica. El índice normalizado NTI lo atenúa
fuerte, porque el MIR y el TIR suben juntos sobre terreno tibio. **Si se baja el umbral en zona de
cráter de un nevado, debe hacerse por el camino del NTI, no por el del MIR crudo.**

## 3. La idea, en una frase

En vez de elegir un umbral y descubrir después qué tasa de falsas alarmas produce, **se fija la
tasa de falsas alarmas aceptable por zona y se deriva el umbral desde el ruido medido**.

Eso invierte el orden habitual y tiene una ventaja concreta: la tasa de falsa alarma es la cantidad
que el operador sufre, así que es la que debe decidirse; el umbral es un número interno que nadie
mira.

## 4. Las zonas, que ya existen

No hay que inventar configuración. `volcanoes.yaml` ya define por volcán, con valores oficiales de
los KML de MIROVA, el radio interno que delimita la huella del rasgo volcánico conocido:

| volcán | inner_radius_km | qué es esa zona |
|---|---|---|
| Lastarria, Planchón-Peteroa | 3 | cráter y campo fumarólico inmediato |
| Copahue | 4 | cráter El Agrio |
| Villarrica, Láscar, Isluga, Nevados de Chillán, Llaima, Chaitén | 5 | cráter activo |
| Tupungatito | 7 | complejo de cráteres y lago |
| Puyehue Cordón Caulle | 20 | el lacolito, desplazado unos 7 km del cráter |

Ese número ya codifica el prior que se quiere explotar, y con matices que un radio uniforme
perdería: Puyehue no tiene 20 km porque sí, sino porque su rasgo activo está desplazado, y
Lastarria tiene 3 km porque su campo fumarólico Lazufre es compacto y está al norte del cráter.

**Zona A (interna)**: dentro del `inner_radius_km`. **Zona B (externa)**: entre el inner y los 25
km de la escena.

## 5. Qué se cambia, exactamente

El laboratorio gana un umbral de detección **dependiente de la zona**, con dos valores por sensor:
uno permisivo en la zona A y uno igual o más estricto que el operacional en la zona B. El
parámetro natural para modularlo es el multiplicador de sigma del criterio contextual, porque es
el que gobierna cuánta evidencia se exige por encima del fondo.

Lo que **no** cambia: la geometría del ROI, el ancla, el fondo, el cálculo de la magnitud, ni la
selección del cúmulo. Un cambio de umbral que además mueva la geometría produce diferencias de
geometría disfrazadas de diferencias de umbral, que es exactamente el error que S124 documentó en
la v1 de `experimental_ndc_focus`.

## 6. Cómo se elige cada umbral, sin elegirlo a ojo

Para cada zona y cada sensor:

1. Tomar los **negativos limpios**: pasadas donde MIROVA listó ese gránulo con VRP 0, o sea que lo
   procesó y no vio nada. Es el único negativo honesto que tenemos.
2. Barrer el umbral candidato y medir, **por pasada**, la tasa de publicación en esos negativos,
   por zona y por sensor.
3. Elegir el umbral como el más permisivo que cumple la tasa objetivo de esa zona.

Las tasas objetivo son una **decisión del dueño**, no una derivación. Como punto de partida para
discutir, y con la lógica de que en la zona A un falso positivo cuesta poco y un falso negativo
cuesta mucho, mientras que en la zona B pasa lo contrario:

| zona | tasa objetivo en negativos limpios | por qué |
|---|---|---|
| A, dentro del inner | hasta ~30 % de las pasadas | es el cráter: el operador va a mirar ahí de todos modos, y lo que aparezca tiene prior alto |
| B, fuera del inner | ~2 % o menos | son 70 veces más píxeles y casi todo lo que brilla ahí no es volcánico |

## 7. Cómo se valida, y por qué no sirve MIROVA

Acá está el punto más delicado del diseño. **La validación no puede ser contra MIROVA**, porque
por definición se está buscando lo que MIROVA no publica: medir contra su catálogo haría que todo
lo nuevo cuente como falso positivo.

La verdad de terreno tiene que ser otra, y hay tres fuentes:

1. **Episodios conocidos por OVDAS**: cambios de nivel de alerta, reportes de actividad, informes
   de terreno. Es la vara que importa operacionalmente.
2. **SWIR de alta resolución**: Landsat 8 y 9 a 30 m y Sentinel-2 a 20 m, que es el método NHI.
   Cuando un foco es sub-píxel para 375 m, ése es el instrumento correcto, y el proyecto ya tiene
   los repositorios que lo producen. Si la zona A empieza a marcar noches en que el SWIR de alta
   resolución muestra píxeles calientes, la sensibilidad ganada es real.
3. **Persistencia**: una fuente volcánica real, incluso débil, tiende a repetirse en el mismo
   lugar noche tras noche. El ruido no. Esto no es un criterio de detección (sería un filtro
   temporal, otra discusión), pero **sí** es un criterio de validación del experimento.

## 8. Cómo llega al operador

Lo que aparezca en la zona A con umbral bajo es **señal real sub-umbral**, no artefacto, así que
la regla del proyecto dice que el display es legítimo para distinguirla, no para esconderla. El
tablero tiene que poder decir tres cosas distintas:

- **equivalente MIROVA**: lo que defenderíamos públicamente, del perfil operacional;
- **laboratorio, zona del cráter**: señal real bajo el umbral de MIROVA, con su magnitud;
- **laboratorio, fuera del cráter**: lo que hoy se rotula `far`, con la advertencia de que ahí la
  mayor parte no es volcánica.

Si el operador no puede distinguir las tres, la vista pierde valor para decidir alerta, que es
para lo que existe.

**Transparencia algorítmica**: el sistema es un SDA bajo la Resolución CPLT N°372. Si el
laboratorio se publica, necesita su ficha, y un umbral que depende de la zona es exactamente el
tipo de decisión que la ficha tiene que declarar.

## 9. Los riesgos, dichos antes

**El que más me preocupa: esto es un gate per volcán disfrazado.** S116 lo dice con todas las
letras. Un criterio estratificado por régimen es un gate per volcán con otra ropa, y el proyecto
tiene una historia larga de parches per volcán que individualmente parecían justificados y
acumulados anularon la diferenciación que se quería reproducir. La defensa es que esto vive **sólo
en el laboratorio** y se declara como lo que es: un prior por zona, no física nueva.

**El segundo: la zona A no es chica en todos lados.** En Puyehue Cordón Caulle el inner son 20 km,
o sea unos 8.900 píxeles en VIIRS 375: casi dos tercios de la escena. Ahí el argumento del área no
aplica y bajar el umbral va a producir mucho. Puyehue probablemente necesite su propio tratamiento,
o quedar fuera de la primera tanda.

**El tercero: sin el Test 1 resuelto, esto no se puede medir.** Con el 90,9 % de los records de
VIIRS 375 superando el criterio absoluto por puro ruido, cualquier barrido de umbrales mide el
defecto y no el fenómeno. **El A/B que corre ahora es requisito previo**, no una tarea paralela.

## 10. El orden, y qué decide cada paso

| # | paso | qué decide | bloqueado por |
|---|---|---|---|
| 0 | cerrar el A/B "sin Test 1" | sobre qué línea base se construye | corriendo |
| 1 | pisos del laboratorio en 0,0 | que el laboratorio no vea menos que el operacional | **hecho, S147** |
| 2 | este diseño, revisado por Nicolás | las tasas objetivo por zona | este documento |
| 3 | implementar el umbral por zona detrás de un flag apagado | nada todavía | ciclo A45 |
| 4 | barrido de umbrales sobre negativos limpios, por zona y sensor | los dos umbrales por sensor | paso 0 y 3 |
| 5 | reproceso del laboratorio y validación contra OVDAS y SWIR de alta resolución | si la sensibilidad ganada es real | paso 4 |
| 6 | display de tres estados en el tablero | que el operador pueda usarlo | paso 5 |

## 11. Lo que este documento no resuelve

- **Las tasas objetivo son una decisión, no un resultado.** El 30 % y el 2 % son un punto de
  partida para discutir, no una derivación.
- **No cubre el filtro temporal.** Usar la persistencia como criterio de detección, y no sólo de
  validación, es un diseño distinto y probablemente mejor para señal muy débil. Queda anotado.
- **No dice qué hacer con Puyehue Cordón Caulle**, cuyo inner de 20 km rompe el argumento del área.
- **No mide nada todavía.** Todos los números de este documento salen de mediciones previas con su
  fuente citada; los umbrales concretos no existen hasta el paso 4.
