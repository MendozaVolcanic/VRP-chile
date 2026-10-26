# Caminos por los que cada afirmación podría estar mal (escrito ANTES de abrir ningún archivo citado)

Verificador con contexto limpio, S162, frentes MOD-C, MOD-E, MOD-D. Sólo conozco los títulos de las
afirmaciones C1 a C5, E1 a E3 y D1 a D3 y la ruta donde mirar. Este archivo no se edita después de
sellarlo; lo que aprenda va al informe.

## MOD-C (pre-registro del lote de negativos neg_resto)

### C1. 01_seleccion.py reproduce 5.093 neg_resto, marco de 5.055 sin las 38 ya sorteadas, muestra proporcional 400 (semilla 162), 10 controles
- El instrumento mide otra cosa: «neg_resto» se define como negativo limpio donde PRODUCCIÓN no publica. Si el script decide «no publica» con un predicado propio (por ejemplo `vrp_mw == 0` o `primary_cluster` ausente) y no con el predicado del tablero ejecutado con node (`banco_paridad.correr_node`), el 5.093 es otra población.
- La vara es otra: «negativo limpio» exige que MIROVA miró y TODAS sus filas son RUTINA. Si el script toma «sin alerta» como negativo (incluye pasadas donde MIROVA no miró), el denominador se infla.
- La referencia no es la congelada: si lee el CSV vivo del scraper en vez de la referencia congelada declarada (sha256 o commit), el conteo cambia con el día. Comprobar que el pre-registro declara el sha256 y que el script lo usa.
- Las 38 «ya sorteadas»: pueden no estar identificadas por la misma clave (volcán + hora UTC redondeada) que el marco; si la clave difiere (segundos, sensor, product_version), la resta no quita 38 sino menos o más, y el marco no es 5.055 sin solapamiento.
- El pareo ±120 s: si el script parea por otra tolerancia o por noche en vez de pasada, el conteo no es comparable con S159.
- Proporcional: «proporcional» a qué (por volcán, por mes, por cenit). Si los redondeos no suman 400, o hay un estrato con 0 asignado, el muestreo no es el declarado.
- Semilla 162: si la semilla se fija pero el orden del marco depende de un diccionario o de `glob` (orden del sistema de archivos), la muestra no es reproducible entre máquinas (A152: argsort inestable).
- Controles: los 10 «de control» deben ser positivos (pasadas donde el port debe publicar); si son del mismo marco de negativos, no controlan nada.
- La ventana: A104 y A119. Si el marco cruza #535 (2026-08-28) o el flip de los gates intra-radio (2026-07-01) sin estratificar, mezcla dos detectores de producción. Si incluye enero (A119) la referencia es peor.
- El cero: si un volcán da 0 neg_resto, ¿es porque no hay o porque la clave de nombre falla (A14: variantes de nombre)?
- Modo de falla del instrumento: si el script no distingue «MODIS no publica» de «no hay record MODIS esa noche» (hueco 2025-11-16 a 2026-01-28), cuenta como neg_resto pasadas sin record.
- Copia local atrasada: el JSON de producción que lee ¿es el de origin/main del commit declarado o el del worktree?

### C2. Regla de decisión (Jeffreys + ΔE de los otros estratos de S159): INDECIDIBLE con S159; con n = 400 confirma sólo con x = 0, INDECIDIBLE con 1 a 7, refuta con 8 o más; ΔE reproduce el −44,0 de S159
- El instrumento mide otra cosa: «x» ¿cuenta pasadas donde el port publica, o píxeles, o cúmulos? Si el port puede publicar sin que el record sintético pase el predicado del tablero, el x no es el de la vara.
- Jeffreys: intervalo Beta(x+0,5; n−x+0,5). Verificar que con x = 0 el límite superior al nivel declarado, multiplicado por el tamaño del estrato (5.093 o 5.055), sumado a ΔE de los otros estratos, cae bajo cero (confirma) y que con x = 1 ya no. Si el umbral de x cambia con el nivel de confianza (95 % vs 90 %) o con el denominador (5.093 vs 5.055), la frase «sólo con x = 0» depende de una elección no declarada.
- ΔE −44,0: ¿qué unidades? (publicaciones netas esperadas port menos producción). Si el 02 recalcula a partir de las filas de S159 con una clave distinta, puede dar −44 por casualidad o no dar nada. Comprobar que la cuenta sale de filas, no de un número pegado.
- El «refuta con 8 o más»: con límite inferior de Jeffreys. Si el script usa el punto estimado en vez del límite inferior, refuta antes.
- Un segundo camino: la regla asume que los otros estratos de S159 están medidos sin error; si S159 tenía 150 pasadas con muestreo no proporcional, ΔE de los otros estratos lleva su propia incertidumbre que la regla no suma. Entonces «confirma con x = 0» puede ser falso aunque el cálculo esté bien.
- La regla no distingue K re-corrido de K leído del JSON: si el 03 toma la publicación de producción del JSON pero el lote re-corre K, un desacuerdo entre los dos K (A104, dos detectores) hace que x cuente otra cosa.
- Exhaustividad: ¿los tres resultados (confirma, indecidible, refuta) se pisan en algún x? ¿Qué pasa con pasadas que fallan (sin gránulo, timeout, A108)? Si el denominador baja de 400 la tabla de x cambia.

### C3. Costo 1,27 h de runner medido del lote de S159 (04_costo.py)
- El instrumento mide otra cosa: ¿minutos de job (incluye cola, setup, pip) o minutos de pasada? Si toma `run duration` del workflow y no la suma de jobs, con matrix paralela el tiempo de pared no es horas de runner.
- La ventana: el lote de S159 tenía 150 pasadas; si las 400 nuevas incluyen más gránulos por pasada (Terra + Aqua) o descargas MxD03 que S159 ya tenía en caché, el costo escala distinto de 400/150.
- Copia local atrasada: `jobs_39712862945.json` es una foto; si está truncada (paginación de la API a 30 jobs por página) la suma es parcial. Comprobar número de jobs contra el número declarado.
- Fallidos: si se excluyen los jobs fallidos o cancelados, el costo por pasada está subestimado.

### C4. envoltorio_nativo.py guarda el recorte nativo sin cambiar el resultado del port; su prueba atrapa 6 de 6 mutaciones por aserción
- Mutación «atrapada» por caída y no por aserción (regla de S152 y S156): si la prueba cuenta cualquier excepción como atrapada, el 6 de 6 es inflado. Comprobar que el conteo exige AssertionError o comparación explícita.
- Control de caída: ¿hay un control sin mutación que pasa? Si la prueba fallara también sin mutar, 6 de 6 es «todo falla».
- «Sin cambiar el resultado del port»: ¿se compara el resultado completo (VRP, celda, n píxeles, flags) o sólo un escalar? Un envoltorio que altera el orden de píxeles puede dar el mismo VRP y otra celda.
- Sintético vs real: sin pyhdf, la prueba corre sobre arreglos sintéticos; si el envoltorio depende de la forma del gránulo real (2030 × 1354, bandas de 10 líneas) y la prueba usa otra forma, lo que se prueba no es lo que corre.
- Línea y frame: ¿se guardan los índices del gránulo original o los de un recorte intermedio? Si el recorte se hace después de un reordenamiento (ej. por bow tie o por latitud), «línea» ya no es línea del gránulo.
- Tamaño estimado (06): ¿asume dtype float64 o float32 y cuántas bandas? Si el recorte real se guarda con metadatos y compresión, el estimado puede errar un orden de magnitud. Comprobar contra el presupuesto de disco de la autonomía (500 MB) y de los artefactos del runner.

### C5. probe-s162-negmodis.yml válido, sólo lectura, autentica sólo por EARTHDATA_TOKEN que falla vacío, comprueba blobs del instrumento y de los objetivos; 07_leer_lote.py aplica la regla de C2
- Validez YAML: «on» sin comillas (A43, Norway problem). Parsear con yaml.safe_load y mirar las claves.
- Sólo lectura: buscar `git push`, `git commit`, `gh release`, escritura a `data/`. Un `actions/upload-artifact` es lectura del repo pero escritura de artefactos; está bien si es eso lo que «sólo lectura» quiere decir.
- Token: buscar `EARTHDATA_USERNAME`/`PASSWORD` (A71, par vencido) y que haya un paso que falle si el token está vacío ANTES de cualquier llamada a NASA (si falla después, ya pudo bloquear la cuenta).
- Blobs: ¿compara sha256 del script contra un valor pegado en el yml o contra un archivo? ¿Qué cubre: el envoltorio, el port de S159 (que vive en otra rama), objetivos? Si el yml hace checkout de main pero el port está en s159-pruebas, el blob del port puede no estar en el árbol.
- Rama de checkout: si el workflow corre desde una rama con `ref` fijo y los scripts cambian después, el blob falla (bien) o no se comprueba (mal).
- 07_leer_lote.py: ¿lee la publicación del port con el predicado del tablero (node) o con un atajo? ¿Cuenta jobs fallidos como x = 0 (sesgo hacia «confirma»)? Ensayo en seco sobre S159: ¿reproduce INDECIDIBLE del 03?
- Cortacircuito que salta sin fallar (S157): un `continue-on-error` o `|| true` en un paso de descarga hace que una pasada sin dato cuente como negativo.
- El lector debe informar el denominador efectivo (pasadas con dato) y no asumir 400.

## MOD-E (bow tie, informe)

### E1. Las grillas guardadas del port no traen píxeles nativos (INFORME.md E-1)
- Cómo se comprobó: ¿se abrió un .npz/.json del run 39712862945 y se listaron las claves, o se dedujo del código? Si es del código, SOSPECHA.
- «No traen» ¿para los 150 o se miró una muestra? Un archivo distinto (ej. el de Chillán) podría traerlos.
- La afirmación sirve para justificar un sintético; si en realidad alguna salida trae línea/frame (ej. el centro del cúmulo), la ablación podía haberse hecho sobre datos reales en parte.

### E2. La razón port/MIROVA sube con el cenit, también dentro de Láscar (E-2)
- El instrumento mide otra cosa: ¿«cenit» es el del sensor en el píxel del cúmulo, o el del centro de la grilla, o el del gránulo? Si viene de la referencia de MIROVA (que no trae cenit) o de una columna que es ángulo de barrido y no cenit, el eje está mal rotulado.
- La razón: ¿mediana por estrato con n declarado? Con 150 pasadas y pocos estratos de cenit, los estratos extremos pueden tener n < 5 y la tendencia ser ruido. Comprobar n por estrato y si hay prueba de tendencia (Spearman, signo por bloque) o sólo lectura visual.
- Confusor: la razón puede subir con el cenit porque la MAGNITUD de MIROVA baja con el cenit (su área es fija, nadir) y no porque el port suba. O porque las pasadas de alto cenit son de otro volcán o de otra fase (A154: Chillán cae con el cenit). «También dentro de Láscar» controla el volcán pero no la fecha ni la fase eruptiva.
- Duplicados: la razón port/MIROVA en pares; si una pasada tiene dos gránulos (Terra y Aqua) y se parean ambos a la misma fila de MIROVA, hay pseudorreplicación.
- Dirección del signo: «sube» ¿por encima de 1 o desde abajo de 1 hacia 1? Si la razón va de 0,7 a 1,0 con el cenit, «el port sobreestima a alto cenit» es otra lectura que «el port se acerca a MIROVA a alto cenit».
- La ventana: pares de S159 (150 pasadas, elegidas con alertas de MIROVA). Sesgo de selección: las alertas de MIROVA a alto cenit son las fuertes (las débiles no sobreviven al píxel grande), así que la razón a alto cenit se mide sobre otra población.

### E3. En el sintético, quitar duplicados no cambia la mediana hasta ~45° y la baja ~25 % a 50° (E-3)
- Modelo del bow tie: en MODIS el solapamiento entre barridos (bow tie) empieza cerca de 24° de ángulo de barrido (≈ 27° de cenit) y crece hasta ~50 % de las líneas a 55°. Si el sintético pone el inicio del solapamiento en 45°, no modela el bow tie de MODIS sino otra cosa, y el «no cambia hasta 45°» es consecuencia del supuesto, no una medición. Ojo: cenit del sensor vs ángulo de barrido difieren (cenit ≈ barrido × ~1,2 al borde); si el informe mezcla los dos, 45° de barrido ya es ~55° de cenit.
- ¿Los duplicados ven el foco? Si el sintético pone el foco en un píxel y los «duplicados» se generan copiando píxeles vecinos sin el foco (o copiando el foco en una posición que el recorte de 51 × 51 no cubre), quitar duplicados no cambia nada por construcción, no por física.
- ¿SIN_DUP quita lo que dice? Si el brazo SIN_DUP quita píxeles al azar, o quita los que no son duplicados, o quita la mitad de las líneas sin mirar cuáles solapan, mide otra cosa. Comprobar con un control: un caso donde el duplicado contiene el foco debe cambiar el VRP al quitarlo.
- Cómo se insertan los duplicados: ¿se duplican líneas enteras (como el bow tie real, que repite líneas en los bordes de cada barrido de 10 líneas) o píxeles sueltos? ¿Y la geolocalización de los duplicados cae en la misma celda de la grilla de 1 km (lo que haría que el regrid los sume) o en celdas vecinas?
- Fondo: el port de MIROVA calcula μ y σ sobre la grilla; duplicar píxeles de fondo cambia σ muy poco. Duplicar el foco cambia la suma. Si el sintético sólo duplica fondo, la mediana no cambia por construcción.
- 1 MW y 3 MW: dos niveles de foco. Si a 1 MW el foco no se detecta en muchos casos (x píxeles con VRP = 0), la mediana de la razón puede estar dominada por ceros y «no cambia» es «nada se detecta».
- «Mediana no cambia» con n = ¿cuántas realizaciones? Sin intervalo, un cambio de 5 % puede ser invisible. Control positivo: a 55° debería cambiar; si tampoco cambia, el instrumento está muerto.
- Lectura del informe: «sin efecto hasta ~52° de cenit» (commit) vs «hasta ~45°» (afirmación): ¿los dos números son del mismo eje? Si uno es barrido y otro cenit, el informe se contradice o se traduce mal.
- Consecuencia práctica: ¿cuántas pasadas del lote de S159 y del lote de 400 están sobre 45°/50°? Si la mayoría de las alertas protegidas están a bajo cenit, el efecto importa poco; si Chillán a 58° es el caso, importa.

## MOD-D (pre-registro del paquete)

### D1. Los hechos citados están respaldados por los archivos que cita
- D33 «no existe dentro del port salvo píxeles con B22 saturada»: D33 es una divergencia del catálogo; comprobar en MIROVA_DIVERGENCES.md qué es D33 y si el port de S159 realmente hace lo que D33 describe (si D33 es «banda 21 donde 22 satura», el port de MIROVA en VIIRS 750 no tiene banda 21: ¿cómo lo resolvió el port a MODIS?).
- «0 de 149 saturados»: ¿149 o 150? Si el lote fue de 150 y uno falló, el 149 debe estar explicado. ¿Saturado se mide con el sentinel 65533 (A37) o con BT ≥ 500 K? Si el port lee radiancia ya escalada, el sentinel se perdió.
- «El port detecta las dos protegidas de Chillán a 58°»: ¿58° es cenit del sensor en el cúmulo? ¿Las dos protegidas son alertas de MIROVA de 1 MW o más (vara)? ¿«detecta» es «publica» con el predicado del tablero sobre el record sintético?
- `prueba_signos_p2` y calibración de d′ «en la rama citada»: `git show` de la rama; si el nombre de la función difiere o la calibración está en otro archivo, la cita está rota.
- El costo: ¿sale del 04 de MOD-C o de otro cálculo? ¿Escala con el número de pasadas del paquete (que no es 400)?
- Copia atrasada: la rama s159-evaluador-d25 puede haber avanzado; el pre-registro debe fijar un commit.

### D2. Las reglas §4 a §6 producen resultados que pueden ocurrir y no se pisan
- Enumerar casos borde: empate en la prueba de signos; bloques con n par; pasadas sin dato (A108) que dejan el denominador por debajo del plan; una protegida perdida (¿es NO CANDIDATO automático o DECIDE NICOLÁS?).
- Ambigüedad típica: «ganancia pareja» sin número; «mejora» sin dirección; umbrales expresados en porcentaje sin denominador (A90); «salvo que» sin lista cerrada.
- Las tres salidas de Chillán: comprobar si son mutuamente excluyentes y exhaustivas (¿qué pasa si el port detecta 1 de 2?).
- Orden de evaluación: si §5 dice CANDIDATO y §6 dice NO CANDIDATO para el mismo dato, ¿cuál manda?
- Placebo: ¿está definido ANTES con su umbral de rechazo (A110: nulo medido)? Si el placebo se mira después, se puede justificar cualquier cosa.
- Lectura A vs B de MIROVA: el pre-registro debe fijar la lectura.

### D3. Lo que falta para que MOD-D sea despachable
- Candado: hash del código del port + del evaluador + de la referencia; tag defensivo.
- Evaluador: existe `evaluar_d25.py` en otra rama; MOD-D necesita el suyo o una adaptación; ¿está escrito? ¿Tiene pruebas con mutaciones y control de caída (S156)?
- Lista de pasadas del paquete (objetivos) con su sha256.
- Workflow con token, sin par usuario/clave, con fallo al vacío.
- Verificación de que K (producción) del commit declarado es el que corre.
- Verificador limpio después del resultado (ya previsto por el programa §2, comprobar).

## Caminos transversales
- Hora del servidor para «hoy» (A86). Commit medido: 045d6f8adbb0e678f8e3384cf06ebea17934a46b (rama claude/s162-modis-774bb0).
- Insumos de S159 están en otra rama (s159-pruebas): la copia extraída del scratchpad puede no coincidir con `origin/s159-pruebas`; comparar sha256 de los archivos clave antes de usarla.
- Los artefactos del run en D:\vrp-trabajo\temporales\s159_portes\ pueden no existir en esta máquina (df no ve D:). Si no están, E1 y parte de C2/C3 quedan SIN DATO por ese camino y se verifican sólo por la copia local.
- Sin pyhdf no se puede leer HDF: toda prueba del envoltorio y del sintético corre sobre arreglos fabricados; declararlo.
- Encoding: salidas con σ y → pueden haberse escrito con cp1252 y tener caracteres rotos; no confundir con error del script.

---
Sellado. sha256 del contenido anterior a esta línea: a32f490793b25e2174c350871fd2cdc477f0b7ee7ffb015e5c39071b3088f49d
Hora del servidor (GitHub, header Date): Sat, 24 Oct 2026 16:07:55 GMT
Commit: 045d6f8adbb0e678f8e3384cf06ebea17934a46b
