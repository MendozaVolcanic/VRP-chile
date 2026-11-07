# caminos.md: caminos por los que cada afirmación de F3 podría estar mal

Escrito antes de abrir ningún archivo citado (sólo había leído el encargo y listado carpetas).
Base de medición: 752d348bc67190e53b610989877e2405d238a1bc.

## Caminos comunes a todas

- C1 La base es otra: el auditor leyó el árbol de trabajo o una copia atrasada, no el commit 752d348bc. Hay que leer con `git show 752d348bc:<ruta>`.
- C2 La línea citada derivó: el número de línea no contiene la frase, o la frase está pero en otro contexto (histórico, entre comillas, con marca de rebaja cercana).
- C3 La vara es otra: el auditor usó una definición de «vigente», «marcado» o «sin marca» más estricta o más laxa que la del proyecto (A113: marca al inicio del bloque, texto viejo conservado).
- C4 El instrumento mide otra cosa: un grep por subcadena que da falso verde o falso rojo (A92).
- C5 El hallazgo ya está corregido en otro punto de main posterior a 752d348bc, o está en una rama (loop/activo) que cuenta como «no en main» sólo por la vara del auditor.

## 251: SINTOMAS.md describe el MODIS de producción como K y con _interp_geo

- 251a Las líneas 25 y 127 podrían ser texto histórico explícitamente fechado (previo a S172), lo que A113 manda conservar; entonces no es defecto.
- 251b Podría llevar una marca «⚠️» en el encabezado de la sección, fuera de las líneas citadas, y entonces sí está rebajado.
- 251c Que MODIS corra por la vía depende de `enable_modis_codigo_mirova` en el perfil que lee el pipeline, no de CLAUDE.md; hay que mirar el flag y los records, no la prosa.
- 251d `_interp_geo` podría seguir siendo cierto para el camino K de guardia o para los records que caen a K (`sin_grilla`, `sin_mxd03`), de modo que la frase sería parcialmente verdadera.
- 251e La vía podría usar MxD03 y entonces `_interp_geo` ya no aplica al MODIS de producción; o la vía podría llamar igual a `_interp_geo` para algo. Hay que trazar el caller.

## 252: la nota A85 corregida por #950 sigue vigente sin marca en SINTOMAS.md

- 252a #950 podría haber corregido A85 en CLAUDE.md pero no ser el hecho relevante: la nota podría llevar otra marca en SINTOMAS (rebajada por otra sesión).
- 252b Las líneas 195 a 197 podrían ser una cita textual de A85 de la versión histórica, con su marca puesta en la línea previa.
- 252c El «hecho» que corrige #950 (records MODIS ene-jun 2026 con processed_utc de 2026-10) hay que medirlo en data/ de 752d348bc, no creerlo desde CLAUDE.md.
- 252d #950 podría no estar en 752d348bc, y la corrección sólo existir en la rama de la sesión top.

## 254: «Sí, arréglalos» (falsos verdes de cenit) no está en main; SIN SUSTRATO se publica como OK

- 254a `git merge-base --is-ancestor dd17fd97d 752d348bc` devuelve distinto de lo que el auditor entendió (códigos de salida: 0 ancestro, 1 no, 128 commit inexistente). Un 128 por sha mal escrito se leería como «no está».
- 254b dd17fd97d podría ser un commit de otra decisión, no la que contiene el arreglo; la decisión podría haberse implementado con otro sha (squash, cherry-pick con contenido equivalente). `git cherry`/ancestro miente con squash (A96): hay que verificar por contenido.
- 254c Las líneas 1227 y 1019 de leer_retro.py pueden no mostrar que SIN SUSTRATO se etiquete OK: puede haber un contador aparte, o el OK puede ser sólo de una subtabla, o el veredicto final puede verse después y volver rojo.
- 254d «Se publica» vs «se calcula»: hay que mirar si lo que sale al informe/dashboard pasa por ese branch, o si el lector es de laboratorio y no publica nada.
- 254e La decisión de Nicolás podría haber pedido arreglar otra cosa que lo que el auditor entendió.

## 253: Decisión 3 de S174 (sin_grilla/sin_mxd03 como K con aviso) aprobada y no implementada

- 253a La aprobación podría ser sólo una recomendación de la coordinadora, no una frase de Nicolás; en ese caso «aprobada» sería falso.
- 253b La implementación podría estar en otro archivo o en la rama de #952 (fuera de main), y en 752d348bc sólo faltar por estar fuera de main.
- 253c Las líneas 270, 271, 354 y 544 podrían no excluir sino sólo contar; «pone rojo» podría ser otra cosa (aviso amarillo).
- 253d El grep por subcadena de `sin_grilla|sin_mxd03` puede matchear comentarios o strings sin lógica.
- 253e Para los records con sin_grilla/sin_mxd03 el detector efectivo es K por definición del plan; que el lector los excluya podría ser deliberado y estar documentado.

## 257: el censo S145 no ve las dos líneas base rojas ni los cierres de S160 en adelante

- 257a El censo mide una cosa distinta (cierres de S1-S145 por patrón de texto) y que no vea S160+ puede ser su alcance declarado, no un defecto.
- 257b Los dos commits (77e54e8e0^ y 752d348bc) podrían correr con el mismo censo.py y dar lo mismo por razones ajenas; el control positivo sería que el censo vea algo que sí cambia.
- 257c «Las dos líneas base rojas» podría referirse a algo que el censo sí ve bajo otro nombre; hay que ver qué son.
- 257d `cierres_desde_s160.py` es un instrumento del auditor: su lista de cierres podría estar incompleta o contener falsos cierres; su conteo no vale si no tiene control positivo.
- 257e censo.py:54-66 podría haber cambiado entre 77e54e8e0^ y 752d348bc, de modo que «no ve» valga sólo para una de las dos.

## 258: parámetros del lector sellado de V750-A fijados por la coordinadora sin frase de Nicolás

- 258a Nicolás podría haber dado la frase en otro documento o fecha que el auditor no revisó (bitácora de loop/activo, mensajes). Probar un negativo («no hay frase») es lo más débil.
- 258b Los parámetros de evaluar_v750a.py:117-118 podrían derivar de una regla ya sellada y no ser elección nueva.
- 258c LOOP_OBJETIVOS.md:605,643 en 06de6876a: la afirmación «declarados» podría ser que el propio documento los declara como fijados por la coordinadora, y entonces no hay ocultamiento; el hallazgo sería de gravedad menor.
- 258d El commit 06de6876a podría no ser el de loop/activo vigente (395af8034 es el de referencia en el plan); la línea pudo haberse movido o corregido después.
- 258e El lector de V750-A (#945) está en 752d348bc, pero los parámetros que cita podrían ser de una versión anterior al merge.

## Controles que usaré

- Control positivo de cada grep/git: buscar una cadena que seguro existe en el mismo archivo y una que seguro no existe, para distinguir «no hay» de «no medí».
- Cada lectura con `git show 752d348bc:<ruta>` y comparación con el árbol de trabajo para detectar deriva.

---
sha256 del contenido anterior a esta linea: 3970662bf7553be5b62fb81ac2f90e463f57fbce985d4df331f111294a457bba
hora del servidor (GitHub): Sat, 07 Nov 2026 10:28:15 GMT
