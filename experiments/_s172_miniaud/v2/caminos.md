# caminos.md: caminos por los que cada afirmación podría estar mal

Escrito ANTES de abrir ningún archivo citado, sólo con título, archivo:línea y gravedad de la lista.
Modelo: Sonnet 5.5, esfuerzo alto.

## MA172-201 y MA172-301 (pyproj en el NRT; son el mismo defecto, dos frentes)

Afirmación: el workflow nrt.yml no instala pyproj, la vía de MODIS lo importa en cada gránulo, y con el PR B producción deja de escribir MODIS.

Caminos por los que podría estar mal:
1. nrt.yml instala pyproj por otra línea (requirements.txt, `pip install -r`, un paso previo, un extra de otro paquete como earthaccess, rasterio, geopandas o cartopy que lo trae por dependencia transitiva). Leer sólo las líneas 140-143 y concluir «no se instala» es un falso negativo de forma A89 (el nombre en el punto de uso no es el del punto de definición).
2. El import de pyproj en pipeline/mirova_v750_codigo.py:204 o :814 está dentro de un try/except o es perezoso en una función que MODIS no llama; o la vía de MODIS no pasa por esa función (la vía de VIIRS 750 sí).
3. El caller (process_modis.py:637,652 / run_pipeline.py:279-280) atrapa la excepción y cae al detector K (fallback), así que «deja de escribir MODIS» sería falso: escribiría K con via_codigo_mirova=False. Hay que trazar el caller (A6).
4. El flag se lee de otro lado: el job de MODIS corre en un job/matrix distinto del que tiene el paso de pip; o `VRP_PROFILE` en el workflow no es mirova_equivalent para MODIS; o el perfil con extends sobreescribe el flag.
5. pyproj ya está en el runner ubuntu-latest (preinstalado, o por el setup-python con cache). El runner real manda, no el yml: hay que mirar logs de un run pasado (`pip list` o un import) por la API de GitHub.
6. La rama en que se mira el workflow es la equivocada: el nrt.yml de la punta del PR B vs el de main de hoy (14fb62030) vs el de PR A. Si PR B toca nrt.yml o requirements, la afirmación cambia.
7. La gravedad 5 contra 4: el mismo defecto con dos gravedades distintas; la gravedad depende de si el fallo es silencioso (sin issue, sin rojo) o ruidoso. Hay que ver si hay una compuerta (vigilancia de «cero records MODIS en N horas») que lo atrape.
8. Windows vs Linux: MODIS sólo corre en Linux (pyhdf), así que ninguna prueba local lo reproduce; la prueba sintética que importe pyproj en Anaconda pasa porque pyproj está en Anaconda. Un test verde local no refuta el fallo del runner.
9. Fusión: si ambos hallazgos citan los mismos archivos pero uno dice 4 y otro 5, hay que decidir la gravedad propia.

## MA172-202 (la vigilancia no cuenta como producción calla una pasada sin record de producción)

Caminos:
1. El instrumento mide otra cosa: «pasada sin record de producción» puede estar capturada en otra rama del código (vigilancia_sombra.py), con otro estado (SIN_PRODUCCION, NO_EVALUABLE) que sí abre issue; leer sólo las líneas 185-189 pierde la rama.
2. El workflow (vigilancia-guardia-modis.yml:128-137) convierte un estado distinto de OK en issue por un camino que el script no muestra (grep en la salida, exit code).
3. Que «el peor caso de la regla no dispara» dependa de la definición de la regla de reversión (borrador) y no del código: la vara es el borrador de loop/activo, no un documento sellado.
4. Caso real: ¿existe alguna vez una pasada de la guardia sin record de producción cuando producción corre MODIS cada 2 h? Si ocurre sólo con un hueco del NRT, el hueco lo ve otra vigilancia (zombie, A64).
5. Prueba sintética del auditor con datos inventados: el mismo código con datos reales podría comportarse distinto (denominador, ventana).

## MA172-203 (guardia muerta hasta 3 días deja la vigilancia en VERDE)

Caminos:
1. La línea 61 puede ser una constante de tolerancia (3 días) que el diseño declara a propósito; entonces no es defecto sino decisión documentada. Mirar el diseño.
2. El rojo del job: si el job falla (exit != 0), GitHub manda correo/notificación al dueño del repo por defecto; «nadie lo convierte en issue» no equivale a «nadie lo ve». Verificar si hay un paso `if: failure()` que abre issue.
3. «Hasta 3 días» puede ser por caducidad del artefacto de la guardia; la guardia muerta la detectaría otro chequeo («frescura de la guardia»).
4. Ventana: el escenario requiere una protegida que producción calla y guardia muerta a la vez; la probabilidad es otra cuestión de la gravedad.
5. El script depende de la fecha de ejecución (hoy); la reproducción cambia con el día.

## MA172-204 (referencia sin filas MODIS y con VIIRS fresco deja la vigilancia ciega en VERDE)

Caminos:
1. A119: la referencia MODIS está completa y plana desde marzo; el caso «sin filas MODIS» puede ser imposible en la práctica (el scraper trae MODIS en el mismo CSV que VIIRS). Medir en la referencia real: filas MODIS por día.
2. El código de 395-406 puede tener una rama «referencia vieja» que mira la frescura global (VIIRS) pero otra que mira por sensor; falta leer el contexto.
3. Sin filas MODIS para la ventana es lo mismo que «MIROVA no vio nada en MODIS» legítimamente (días sin alertas): el cero de «no hay» y «no medí» se confunden (pregunta 2 del instrumento); pero la elección de fallar el job con un día plano sin alertas daría falsos rojos. Ver qué es peor.
4. El frescor se mide con la fecha del archivo o del último commit del sync (data(mirova): sync CSV consolidado), no con la del último dato MODIS.

## MA172-206 (el encendido desde los datos cae hasta ~4,5 días antes del merge por upgrade NRT a estándar que hereda first_processed_utc)

Caminos:
1. store.py:677-700: el upgrade NRT a Standard puede heredar o NO heredar first_processed_utc; leer la rama exacta y trazar al caller (A6).
2. «Encendido desde los datos» = el primer record con via_codigo_mirova=True; si el upgrade reescribe un record NRT viejo (computado con K) como estándar con la vía, y first_processed_utc quedó de la versión NRT, el record sale con un sello previo al merge, pero el campo via_codigo_mirova de ese record sería True aunque el sello sea anterior. Hay que ver qué campo marca la frontera.
3. «4,5 días»: es la latencia entre NRT y Standard de LAADS (días). Verificar contra datos de producción.
4. El script de la guardia (33-36, 86-102) puede usar otra frontera (processed_utc, no first_processed_utc); el PR_B_CUERPO.md 43-44 puede describir otra cosa. Contraponer.
5. Si el upgrade sólo ocurre cuando existe Standard y la vía no procesa el estándar (sólo NRT), el caso no existe.
6. Gravedad 2: se arregla con una nota o ajuste de la frontera; no bloquea.

## MA172-207 (la regla cuenta desde CAMBIO_DETECTOR_MODIS_UTC y esa constante no existe)

Caminos:
1. La constante puede existir con otro nombre exacto (A89): CAMBIO_DETECTOR_MODIS, CAMBIO_DETECTOR_UTC, cambio_detector.js (frontend), una clave de YAML; buscar por frontera y no por el nombre. Ojo: el borrador dice «nombre» de forma genérica y el código puede usar una constante de otro módulo (frontend/cambio_detector.js).
2. El borrador de la regla es un BORRADOR en loop/activo, no sellado: es un defecto de documento por sellar, no de código. Verificar si el borrador final (la punta de PR A o B) ya lo corrige.
3. «Hora del merge» vs «otra frontera»: si el código usa el primer record con la vía, la frontera es de datos y es mejor; la divergencia sería deliberada.
4. Existencia en qué ref: la constante podría existir en la rama de PR A y no en la de B (PR B tiene otro padre, da67fa417).

## MA172-208 (el nulo de la guardia con 0 pares no avisa y da VERDE)

Caminos:
1. El nulo con 0 pares puede estar protegido por otra parte del código (un `if n_pares == 0: estado = SIN_DATO`), a distintas líneas de las citadas (232-248, 267).
2. «VERDE» a nivel de job vs a nivel de estado del reporte: puede que el reporte diga SIN_DATO y el job sea verde a propósito (no abrir issue por falta de datos en un día plano). Pregunta 2 del instrumento: ¿se distingue «no hay» de «no medí»?
3. Los 0 pares ocurren cuando la guardia está muerta (se cruza con MA172-203) o con ventana corta; revisar el umbral (n mínimo).
4. El nulo se calcula sobre qué población: el nulo de la guardia es contra K sobre K (placebo). Con 0 pares da media vacía; NaN puede propagar a comparaciones que dan False y por tanto VERDE (comparar NaN, S132).

## MA172-209 (el factor 1,1 a 1,25 no mide la vía de MODIS)

Caminos:
1. El factor puede ser del tiempo de corrida del job del NRT (minutos), medido en una sombra con tres vías (V750, V375-E, MODIS); si la sombra corría MODIS con la vía encendida, sí mide. Leer nrt.yml:179,195,332-333 por contexto (qué jobs, qué matrix).
2. VR172-04 es un hallazgo del frente 1 u otro; «confirmado» no se hereda: hay que probarlo sin verlo.
3. «Dentro del ruido de K»: depende de la varianza medida del NRT; se necesita una serie de duraciones de runs reales (API de GitHub, dentro del tope de 30 lecturas).
4. El borrador de reversión (138-139) puede decir otra cosa en la rama actual de loop/activo: la copia citada puede estar atrasada.
5. Qué es «el factor»: ¿de cuántas veces se alarga el job con la vía (tiempo)? ¿o de magnitud VRP? Si es de tiempo, y el rango 1,1 a 1,25 es un umbral de reversión, entonces mide si la vía encarece el job, no la calidad.

## Caminos generales
- Todos los archivos se leen en la punta del PR B (worktree), pero PR A y la base tienen otras versiones: confirmar el ref para cada cita.
- Línea citada corrida: citas archivo:línea del auditor pueden ser de otra revisión (A101, remapear por contenido).
- El árbol compartido está en otra rama: no leer ahí, sólo git show.
- Un test verde local con pyproj de Anaconda no prueba nada sobre el runner ubuntu.
- Disco: D: tiene 6,6 GB libres; ok sobre 3 GB.


---
sha256 del contenido anterior a este pie (archivo con linea en blanco final): 0f7a7ac5291838e0e1efd5538728b4bd976415b3e637c987d43def368781319d
Hora del servidor (GitHub Date): Mon, 02 Nov 2026 01:35:33 GMT (consultada antes de escribir; este pie escrito unos minutos despues)
No se edita mas; lo aprendido va al INFORME.
