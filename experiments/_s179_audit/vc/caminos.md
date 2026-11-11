# Caminos por los que cada afirmación del frente C podría estar mal

Escrito antes de abrir ningún archivo citado. Sólo con el título, la cita y la gravedad de cada afirmación.

## Caminos comunes a todas

- G1. Ref equivocada: la línea citada se leyó en otra ref (loop/activo en vez de main 438a60a1e, o un tag distinto), y en la ref nombrada el contenido es otro.
- G2. Copia local atrasada: la instantánea en D:\vrp-trabajo\temporales\s179-audit\main\ no coincide con `git show 438a60a1e:<ruta>`.
- G3. Número recalculado con un script del auditor que mide otra cosa que el pre-registro (otro predicado, otra ventana, otra etiqueta, otra referencia congelada).
- G4. Vara equivocada: la retrospectiva se juzga contra la referencia viva o la del repo en 438a60a1e en vez de sus copias congeladas (CONS 811c4c07, OCR 01c9478d).
- G5. El pre-registro sí permite lo que el auditor llama desvío (una enmienda, un párrafo posterior, una nota de pie) y el auditor leyó una sola sección.
- G6. Una decisión de Nicolás registrada en otro lugar (PR, bitácora de otra rama) que el auditor no vio, o al revés: lo que el auditor tomó por decisión es una aprobación reenviada.
- G7. Script del auditor no reproducible: no corre, depende de rutas de su temporal, o su salida en disco no es la que produce hoy.

## Por afirmación

- 501. La exención N-3 podría estar autorizada por el §4.1 (texto que el auditor no leyó entero) o por una enmienda; la «fila 4 con la letra» podría depender de cómo el auditor contó; las 3 protegidas «sólo del OCR» podrían estar listadas en otra salida del lector (no en la que miró) o no ser protegidas con la regla D-9; las líneas 42-43, 417-431, 1309 podrían no ser la exención.
- 502. «Pasadas miradas por nombre» podría ser una exclusión que el pre-registro manda (l. 155-157, 171-173); B 9 neto -3 podría salir de un recálculo con otro denominador; el lector podría informarlo en otra parte de su salida (otro archivo, otro bloque).
- 503. El sorteo podría haberse corrido en otro script o rama; la «decisión 2» podría decir otra cosa (sorteo distinto al que el auditor corrió); 8,4 % y 10,3 % dependen de semilla y número de sorteos: re-correr con otra semilla podría cambiar el lado del umbral; el umbral del pre-registro (l. 469-470) podría no ser 5 %.
- 504. «Pasadas que deciden P2» podría ser una categoría inventada por el auditor; el conteo 12 de 70 podría depender de la unión de días; «elegidos tras el sello» requiere fechas: el sello y la elección podrían ser del mismo día, o la elección podría estar en el pre-registro con otra palabra.
- 505. El manifiesto podría ser legítimamente de la misma ref (el pre-registro podría pedir eso); «31 s antes» depende de horas de commit vs de archivo; los archivos «dejados fuera» podrían estar cubiertos por otro mecanismo (sha del árbol, tag); «efecto medido 0» significa que no hay daño, lo que baja la gravedad; el lector podría no cambiar con los datos.
- 506. «Sin sustrato» podría ser lo que el pre-registro prevé como resultado válido; la curva R25 podría calcularse en otro script; «K/OSF cae con el cenit» podría depender de los cortes de cenit y del estrato; podría ser el mismo efecto que la cobertura del OSF.
- 507. El §4.2 podría pedir «informar» en otro producto; los conteos 1.440/1.485 y 1.399 dependen de la definición de bajo 1 MW (D-9 a 0,05 MW) y de la ventana R25; los porcentajes deben salir del cociente.
- 508. «0 de 0» podría ser un 0 de 627 bien informado; la causa NOAA-21 podría ser otra (pareo, TOL_S); el pre-registro podría excluir NOAA-21 y el lector no; la definición de noche limpia del §5.5 podría ser distinta.
- 509. El nombre del veredicto podría ser texto fijo que no dice incluir conteos; «26 protegidas todas de Láscar» depende de la ventana F26 y de la etiqueta; los otros tres podrían venir de R25, no del OSF 2025.
- 510. montaje.json podría vivir en una rama fuera de main (rotular); el rango -3,4 a +7,4 podría ser de otra métrica; «48 de 51 con 5 % de más» depende de cómo se infló; la PROPUESTA podría declarar el rango de otra cosa.
- 511. El placebo podría estar construido distinto de lo que dice el título; «0 por construcción» exige leer el código; la mediana -0,0792 constante podría variar con la semilla; el pre-registro podría no llamarlo «control que puede fallar».
- 512. La decisión 6 podría tener otro texto (antes de D3 de qué); las fechas de fijación podrían ser las de un commit posterior de un fijado anterior; D2 a D4 «en disco» depende de la fecha de los archivos.
- 513. «Criterio d» y «d prima» podrían ser lo que el pre-registro define; K x 1,2 podría no ser control pre-registrado; el IC depende del bootstrap; n 11 todo Láscar depende del estrato.
- 514. Conteo 1.094 depende de la ventana; «dentro de F26» depende de la definición de F26; el lector podría sí acotar la lista en otra línea.
- 515. Las decisiones podrían tener respuesta en otro archivo (bitácora, PR) o en un bloque posterior S178/S179; «salieron de la cola» podría ser una reformulación.
- 516. El §11 podría pedir el sha en otro lugar (un archivo de sello); el tag podría ser anotado y llevar el sha; el commit podría tenerlo en el cuerpo.
- 517. «Recalcular» podría no ser obligatorio si K no cambió; «K idéntico» depende de qué campos se comparan; 46.468 records depende de la ventana.
- DEC-2/3/7/9: el juicio depende de la vara (texto del pre-registro y de la decisión); pueden fundirse con 501, 503, 512 y 505.

---
sha256 del texto de arriba (antes de esta nota): 048b68745753b383b35305191c4087a2d6e88fb1518b94557967f2abdab3075e
Hora del servidor (cabecera Date de api.github.com): Date: Wed, 11 Nov 2026 01:32:03 GMT
