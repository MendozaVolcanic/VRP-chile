# Caminos por los que cada afirmación podría estar mal (verificador F3)

Escrito antes de abrir ningún archivo citado. Sólo conozco: id, gravedad, título, archivo:línea.

## Caminos generales (valen para todos)
- G1. Las líneas citadas no corresponden al árbol cc3887290 (cita desfasada): el defecto puede existir en otra línea o no existir.
- G2. El árbol en f3_comun/arbol puede no ser idéntico a cc3887290 (copia atrasada, autocrlf, archivos tocados por el auditor). Comprobar con git show contra el árbol.
- G3. El caller transforma el argumento (A6): el defecto en la función puede estar neutralizado por quien la llama, o por el workflow.
- G4. Un segundo camino cubre el hueco (otro script, otro job, un guard, un test) y el defecto no tiene efecto.
- G5. La vara es otra: el auditor juzga contra una regla que el instrumento no promete cumplir (p. ej. el instrumento no pretende vigilar eso).
- G6. La gravedad está inflada: el defecto existe pero no puede torcer un veredicto (sólo lo deja indecidible o confunde al lector).
- G7. Ausencia afirmada por grep (A89): el nombre en el punto de uso no es el de la definición; "nadie lo hace" puede ser falso.

## Por afirmación
- P3-01 (referencia vieja/vacía/BOM da COBERTURA OK): (a) puede haber un chequeo de frescura o de filas mínimas en otra parte (referencia_mirova_unificada o banco_paridad) que aborta antes; (b) COBERTURA OK puede medir sólo nuestros lados, no la referencia, y ser correcto por diseño; (c) BOM puede ser absorbido por encoding="utf-8-sig"; (d) referencia vacía puede producir 0 positivos que otro criterio marca indecidible.
- P3-02 (revisar_sombra no ve corrida vacía desde 2.º día): (a) puede filtrar por fecha de la corrida (ventana_sombra) y no por total; (b) el workflow puede fallar antes si no hay records nuevos (git diff vacío); (c) el script puede comparar con conteo previo.
- P3-03 (no exige records por sensor/volcán-sensor): (a) un sensor puede no tener pasadas un día legítimamente, y exigirlo daría falsas alarmas (vara errónea); (b) vigilancia_sombra puede ya cubrirlo y correr en el mismo workflow.
- P3-04 (gránulos descartados por return None sin rastro): (a) los return None citados pueden ser rutas de error previas a la vía (no de la vía); (b) puede haber un print/log antes del return; (c) el workflow puede subir artefacto de log; (d) --cobertura-json puede existir con otro nombre (A89).
- P3-05 (log VIIRS 375 ciego): (a) la línea puede imprimir n_pixels o vrp que difiere; (b) puede haber otra línea que dice si el store escribió.
- P3-06 (VRP_PROFILE ambiental cambia lectura de diurna): (a) la función de diurna puede no depender del perfil (constante); (b) el evaluador puede fijar VRP_PROFILE antes de importar; (c) el perfil experimental y mirova_equivalent pueden tener el mismo valor del parámetro, efecto nulo hoy.
- P3-07 (evaluador sin procedencia, --salida pisa): (a) puede escribir sha en el JSON con otro nombre; (b) parámetros libres pueden estar en un pre-registro sellado que se verifica por hash; (c) --salida pisar puede ser lo esperado.
- P3-08 (sha del código en record = HEAD en disparo): (a) el workflow puede hacer checkout de un sha fijo; (b) el record puede tener otro campo con sha de pipeline/; (c) HEAD en disparo puede ser igual al código ejecutado (lo es por definición si no hay cambios locales), el defecto sería sólo que no identifica pipeline/ en particular.
- P3-09 (nadie vigila el run): (a) puede existir workflow de vigilancia (nrt-retry, alertas por incidente, workflow_run) que cubre todos los workflows; (b) GitHub manda mail en fallo al dueño; (c) vigilancia_sombra puede abrir issue.
- P3-10 (cargar_lado no filtra via_codigo_mirova ni cuenta fechas ilegibles): (a) el directorio de la sombra puede contener sólo records de la vía, haciendo innecesario el filtro; (b) el filtro puede estar en el caller; (c) fechas ilegibles pueden no existir en la práctica.
- P3-11 (--ref: respaldo y filas perdidas opcionales en silencio, nombres distintos): (a) los nombres pueden ser mapeados; (b) el default puede apuntar al archivo correcto; (c) "silencio" puede tener un print.
- P3-12 (VRP nan cuenta como protegida): (a) la comparación nan >= 1 da False en Python, así que nan NO cuenta (el auditor puede haber invertido); depende de si usan `not (vrp < 1)`; (b) puede haber limpieza previa de nan.
- P3-13 (cargar_filas_referencia cae en silencio al canónico): (a) puede imprimir aviso; (b) la caída puede ser intencional y documentada.
- P3-14 (evaluador_comun nunca llama avisar): (a) A89: puede llamarlo vía banco_paridad.indexar_referencia (que imprime los hitos), o con alias; (b) la ventana de la sombra empieza 2026-11-03, después de todos los hitos A119, entonces avisar no imprimiría nada: efecto nulo.
- P3-15 (fecha mínima aplicada a fechas pedidas, no a datetime_utc): (a) fetch puede filtrar granulos por fecha exacta; (b) un gránulo del 02-nov 23:59 podría entrar al pedir 03-nov (borde UTC/día), o no; (c) revisar_sombra puede filtrar por datetime_utc.


---
sha256 (del contenido previo a este pie): 0ecbf3a417122ee5ecdf7996271b30349e7c314034329b184ae3541b2b8b40ce
Hora: 2026-10-30 03:59:05 UTC (reloj local del computador, sin red; no hay servidor accesible en esta tarea)
