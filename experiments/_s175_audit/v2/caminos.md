# Caminos por los que cada afirmación de F2 podría estar mal

Escrito antes de abrir ningún archivo citado ni script del auditor (verificador V2, frente F2).
Base de medición declarada: 752d348bc67190e53b610989877e2405d238a1bc.

## Caminos transversales (aplican a las ocho afirmaciones)

T1. La copia del árbol del auditor (`f2\arbol_752d348bc`) no es el commit 752d348bc: archivos de más, de menos o editados. Hay que comparar blob a blob contra `git` y no contra el árbol del auditor.
T2. El árbol del auditor es una extracción parcial (sólo data, frontend, pipeline, scripts, volcanoes.yaml): puede faltar un archivo que el banco lee y degradar en silencio a vacío.
T3. La ventana 2026-03-01 a 2026-11-07 incluye días sin tabla de MIROVA (la tabla termina el 2026-11-02): los denominadores pueden incluir noches sin referencia.
T4. «Publicada» se mide con el predicado del tablero ejecutado con node; si el auditor ejecutó otro `index.html`, o una versión reconstruida a mano (regla A97), el número mide otra cosa.
T5. Las etiquetas (protegida, negativo limpio) salen de `etiquetar` con D-9; si el script llama a la etiqueta original, las categorías cambian.
T6. Hora UTC contra hora local en el pareo (TOL_S); una pasada cerca de la medianoche cae en otra noche.
T7. Un resultado que el script imprime pero cuyo archivo de salida es de otra corrida (salida vieja guardada junto al script).
T8. El instrumento puede estar muerto y devolver el mismo número: falta control positivo y control nulo.
T9. Denominadores que se mueven (A90): el corpus de records crece hacia atrás; hoy no es el mismo corpus que el de ayer.
T10. Sensor equivocado: VIIRS375 contra VIIRS750, o plataformas mezcladas (SNPP, NOAA20, NOAA21).

## F2-201: 5 de 171 pasadas protegidas V375 no publicadas; por noche 111 de 111

C201a. «Pasada protegida» podría contar la misma fila de MIROVA contra varias pasadas nuestras (pareo uno a muchos) y 171 no ser el denominador de filas.
C201b. Las 5 perdidas podrían ser pasadas sin record nuestro (cobertura: no corrió, no descargó) y no pasadas con record y sin publicar; la causa es otra y la gravedad también.
C201c. Las 5 podrían ser filas de MIROVA que sólo existen en la tabla OCR (complemento, A11) y cuya magnitud D-4 proviene de una imagen de otra pasada (reference_ocr_imagen_de_otra_pasada).
C201d. «Por noche 111 de 111» depende de la definición de noche: si una noche se cuenta publicada con una sola pasada publicada, el 111/111 es casi tautológico y no vería nada roto (pregunta 1 del instrumento).
C201e. Las 5 podrían estar fuera del predicado por una condición de cenit/rango que no es un fallo (p. ej. píxel fuera del swath), no pérdida de detección.

## F2-202: pérdidas concentradas en cenit >= 50 y Suomi NPP

C202a. 4 de 36 es una muestra mínima: el intervalo de confianza de 4/36 contra 1/135 es ancho; «concentradas» podría ser consecuencia de n pequeño. Falta un test exacto (Fisher).
C202b. El cenit del script podría calcularse del lugar equivocado (el del volcán contra el del pixel/ancla) o con una fórmula que no es el cenit de la pasada.
C202c. Cenit y plataforma están confundidos (SNPP tiene un patrón de órbita que lo pone más en el borde): la atribución a cada uno por separado no es identificable con 5 eventos.
C202d. Que las 4 de 5 estén en cenit alto puede deberse a que MIROVA mismo escribe ahí alertas débiles (borde de swath) y no a un fallo nuestro.
C202e. 97,1 % = 166/171: comprobar aritmética (166/171 = 97,08 %).

## F2-203: sobre-publicación en negativos limpios: 3,9 % agregado; Lastarria 25,6 %; Puyehue 11,6 %

C203a. Un «negativo limpio» exige que MIROVA no tuviera nada; si la tabla de MIROVA tiene huecos (A119, calidad por mes), la pasada sin fila no es un negativo limpio sino sin dato. La ventana contiene meses con tabla mala (enero no se usa; OCR mal calibrado hasta 2026-06-11).
C203b. Lastarria 25,6 %: denominador por volcán podría ser muy chico (volcán con pocos negativos limpios), y un porcentaje alto sobre n bajo no es hallazgo.
C203c. La sobre-publicación en Lastarria/Puyehue podría ser real térmica (fumarolas, lago tibio, nieve), no un defecto del detector: A54 dice que 95 % de los «FP» son anomalías reales. Gravedad 3 puede sobrar o faltar según eso.
C203d. «Por noche 13,5/54,9/41,9 %» podría usar un agregado distinto (noche con alguna pasada publicada) y ser inflado por la multiplicidad de pasadas por noche (varias pasadas, una basta).
C203e. D-9 manda sólo para VIIRS375 ≤0,05 MW como «MIROVA no vio nada»; si el script sustituye mal la clase, los negativos limpios cambian.
C203f. El script d9_por_volcan.py y la tabla de f2_banco_v375.py podrían dar números distintos entre sí por filtros distintos.

## F2-204: confirmación de MIROVA en el tablero: ±60 min, sin distancia ni D-9; 647 de 2225 sin alerta de su pasada

C204a. Las líneas citadas de frontend/index.html (1544, 1548, 1559, 1337, 1356, 1422, 1452) han derivado: A101, remapear por contenido. El archivo de hoy en main no es el de 752d348bc.
C204b. «±60 min» podría estar en una constante que el auditor leyó de un comentario y no del código ejecutado.
C204c. «Sin alerta de su pasada» depende de la definición de «su pasada»; si el predicado del tablero empareja por ventana de 60 min pero el banco por TOL_S, las dos medidas no son comparables y la diferencia no es defecto.
C204d. Los 647 pueden incluir filas con RUTINA propia y filas «sólo mínimas»: los subconjuntos 143 y 113 podrían superponerse, y el total no ser suma.
C204e. Que el tablero sea más permisivo que el banco es una decisión de diseño (el operador ve el contexto), no defecto; gravedad 3 puede ser alta.
C204f. 2225 publicados: denominador de qué ventana (fecha de corte), qué sensor, y si incluye los días posteriores al 2026-11-02 donde falta tabla (ver F2-207).

## F2-205: la regla sellada de V375-E da (b) CUMPLE sin negativos; S7 no cae con clases vacías

C205a. El lector del tag `s172-v375e-lector-resellado` está fuera de main; el auditor podría haber leído un tag distinto o una copia local.
C205b. La cita de líneas (584, 617, 364) puede estar corrida; el comportamiento «CUMPLE con clases vacías» puede ser sólo de la ruta que usa el auditor (entrada sintética), y la ruta real nunca tiene clases vacías.
C205c. Que una corrida sintética dé CUMPLE con sustrato vacío no prueba que la corrida real lo haga: hay que correr el lector sobre datos reales de la sombra.
C205d. «SIN SUSTRATO» podría estar ya manejado por una guarda aguas arriba (aborta antes de la regla).
C205e. La entrada sintética del auditor podría estar mal formada (esquema equivocado) y el lector la procesa a vacío por otra razón (instrumento muerto).
C205f. Conjunto de sombra real: si la sombra V375-E no tiene negativos limpios por construcción de la ventana, la regla (b) no puede discriminar y eso es un diseño, no un bug.

## F2-206: el lector sella el index.html del 2026-11-02; el de la base exime a la vía del filtro de cirro

C206a. «Sella» podría significar guarda un hash de referencia, no usa ese archivo para el predicado; entonces el lector evalúa la sombra con el predicado de hoy.
C206b. La diferencia entre predicados (tag y base) podría ser cosmética (renombrar variable) y la salida igual; ver `predicado_tag_vs_base` con ventana 2026-11-03 a 2026-11-07, donde la tabla de MIROVA no tiene datos, así que cualquier comparación contra MIROVA se queda sin vara.
C206c. «Exime a la vía del filtro de cirro (S173 S1)» refiere a una decisión documentada y deliberada (S173); no es defecto sino cambio de régimen. Hay que revisar si es intencional y si el lector tendría que moverse con él.
C206d. Diferencias entre tag y base pueden venir de que main avanzó (merge de #946/#945) y no de un error del lector.
C206e. Línea 71 de leer_sombra_v375e.py puede estar corrida en el tag respecto del archivo del auditor.

## F2-207: la tabla de MIROVA del snapshot termina el 2026-11-02

C207a. El snapshot es una copia congelada en 752d348bc; la tabla remota viva podría tener datos posteriores: la afirmación sería cierta de la copia y falsa de la fuente (A25, consultar el remoto). La vara declarada es la copia, así que la afirmación es sobre la copia, pero el efecto (sin negativos limpios desde el 03) depende de que sea sólo la copia.
C207b. El awk de la afirmación toma `$5=="VIIRS375"` y `substr($2,1,10)`: si la columna 2 no es la fecha de adquisición (podría ser fecha de scraping) o hay comas dentro de campos, el awk cuenta mal.
C207c. Hueco de fecha por conteo: «termina el 2026-11-02» exige el último día con filas, no la última fila escrita; un día con 1 fila contado no es día completo.
C207d. La fecha de la última modificación (79f410697) podría no ser el último commit que tocó el archivo en 752d348bc.
C207e. Que el 3 al 7 de noviembre no tengan negativos limpios puede ser por simple retraso de captura (el scraper corre cada 5 min pero la consolidación diaria), no una falla del scraper.

## F2-212: banco_paridad.main y clasificacion_referencia usan la etiqueta original y no D-9

C212a. `git grep -n "indexar_referencia("` lista llamadas, no el uso de la etiqueta; que la llamada exista no prueba que la etiqueta usada sea la original. Hay que leer lo que cada llamada hace con el resultado.
C212b. La línea 227 y la 526 de banco_paridad.py y 149 de clasificacion_referencia.py son de 752d348bc; en main de hoy podrían haber cambiado.
C212c. `etiquetar` (l. 317) aplica D-9 internamente; si `main` llama luego a `etiquetar`, la etiqueta original sólo se usa para indexar y D-9 después. Entonces la afirmación sería falsa.
C212d. Que el reporte de `banco_paridad.main` use la etiqueta original podría ser deliberado (reportar la tabla tal cual, con D-9 como lectura aparte).
C212e. Efecto: si ambas rutas difieren, qué números del banco cambian y cuántos; sin medirlo la gravedad 2 es un supuesto.

## Qué mediré por otro camino que el del auditor

- Reconstruir los números 171/5 y 36/4 desde el CSV del banco con mi propio script sobre la salida cruda del banco, sin pasar por los filtros del auditor.
- Test exacto de Fisher para F2-202 (cenit alto y SNPP).
- Control positivo: la misma medición con una pasada que sé publicada y una forzada a no publicada.
- Para F2-207 contar días con filas desde el CSV con Python y no con awk.
- Para F2-212 leer las funciones y ejecutar `etiquetar` con una fila sintética D-9 (≤0,05 MW VIIRS375) y ver qué etiqueta recibe cada consumidor.

---
Sellado. sha256 del contenido anterior a esta linea: dfd4a708825eea4620062e6f54d82c0593ff20b920143b3057642422973c38e2
Hora del servidor (GitHub, header Date): Date: Sat, 07 Nov 2026 10:28:33 GMT
No se vuelve a editar; lo aprendido va a VERIFICACION.md. (Llamada API de GitHub 1 de 5.)
