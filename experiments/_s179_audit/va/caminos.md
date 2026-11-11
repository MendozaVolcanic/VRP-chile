# Caminos por los que cada afirmación del frente A podría estar mal

Escrito antes de abrir los archivos citados. Verificador VA, auditoría S179.

## 401: el plazo de la reversión pre-autorizada se agota hacia el 20 de noviembre y sólo con alertas de Chillán
- La proyección de fecha usa un ritmo de protegidas MODIS medido en una ventana corta o sesgada (erupción de Chillán), y el ritmo futuro es otro.
- El contador del plazo puede no ser «protegidas» sino otra cosa (noches, pares, alertas con record), o puede contar sólo las que la guardia miró.
- El plazo puede ser «lo que ocurra último» y no «lo primero» (29 protegidas O 120 días): si es AND/último, el 20-nov no agota nada.
- El instante de inicio del conteo puede ser otro (merge del PR B, primer record de la vía, sellado de la regla) y la fecha cambia.
- La regla sellada en main puede diferir del borrador citado (versión en loop/activo o en otro commit), y el texto de l. 308-314 puede no ser §4.6.
- «Sólo con alertas de Chillán» puede ser cierto en el pasado y no implicar nada del futuro; o las protegidas vienen también de Láscar/Villarrica.
- Qué pasa al agotarse: puede que el plazo agotado no quite la pre-autorización sino que la convierta en otra cosa (decisión de Nicolás), y la gravedad cambia.
- La copia local de datos o de la referencia MIROVA puede estar atrasada respecto de lo que la vigilancia usa en Actions.

## 402: la vigilancia da VERDE cuando la vía pierde una protegida que K tampoco publica o que la guardia no miró (3 de 11)
- El predicado de «pérdida» de la vigilancia puede ser deliberado (la regla define pérdida como «K publica y la vía no»): entonces es diseño, no defecto, y hay que ver si la regla lo dice.
- El conteo 3 de 11 puede usar otro predicado que el del tablero (reconstrucción a mano), otra ventana o otra referencia (CONS vivo vs copia).
- «La guardia no miró» puede ser falta de record de guardia por cobertura (gránulo no procesado) y la vigilancia puede marcarlo en otro campo (SIN DATO, ciego) en vez de VERDE.
- La salida VERDE puede depender de un estado agregado por día; quizás esos días el estado global fue ÁMBAR/CIEGA por otra causa.
- Las líneas citadas pueden haber cambiado entre 438a60a1e y el checkout que usó el auditor.
- Las 11 protegidas pueden incluir alertas protegidas sin pasada nuestra pareada (TOL_S), donde ningún detector podía publicar.

## 403: revertir el PR B por git revert ya choca (6 archivos sobre main, 11 tras VIIRS); el flag revierte limpio
- El commit de merge 499935c37 puede no ser el PR B (#934), o el revert de un merge exige -m 1 y el auditor usó otro padre.
- El «choque» puede ser de archivos de datos (JSON) que no importan para la reversión funcional.
- Las ramas origin/claude/s177-b1-v375 y s178-b2-sobre-b1 pueden haber cambiado desde que se midió (refs móviles), o no existir local.
- La regla de reversión puede no exigir git revert del merge sino el apagado del flag (y entonces el choque es irrelevante para la pre-autorización).
- Un revert simulado sobre un árbol sucio da conflictos espurios.

## 405: el reemplazo de la historia (#981) dejaría la vigilancia en VIGILANCIA_CIEGA todos los días (nulo sin pares) y el plan no lo trata
- El nulo puede alimentarse de otra fuente que la historia reemplazada (p. ej., data/ de la guardia, que el plan no toca).
- El plan puede tratarlo en una sección que el auditor no leyó, o en el PR #981 y no en el doc.
- «Todos los días» puede ser sólo hasta que se acumulen pares nuevos (un transitorio de N días).
- El doc del plan citado es de 62ccb8830 (fuera de main): hay que rotular «fuera de main».

## 410: el único control de que MODIS sigue vivo volcán por volcán está dentro de la vigilancia de la guardia
- Puede haber otro control: tests de frescura, el audit semanal, el workflow de NRT que falla si no hay records, el vigilante de plataformas, un guard en tests/.
- auto_audit_weekly puede sí revisar MODIS por volcán en otra función que las líneas citadas.
- vigilar_plataformas.py puede leer los JSON de detecciones y no sólo los runs.

## 412: la regla sellada no registra los cambios que S175 le hizo al instrumento (#959)
- La regla puede citar el instrumento por sha256 o por commit y ese registro sí existe en otra parte (bitácora, README del experimento).
- #959 puede no haber cambiado la semántica (sólo forma), y el «no registra» no tiene consecuencia.
- La regla puede haber sido resellada después de #959 en loop/activo.

## DEC-10: D7 (al día siguiente de revertir, apartar records de la vía) DEBILITADA en su premisa
- Hay que saber cuál es la premisa; puede depender de cómo el frontend lee esos records (si el tablero filtra por via_codigo_mirova o no).
- El auditor puede confundir D7 de esta regla con otra D7 (catálogo de divergencias).

## DEC-12: §4.6 (plazo 29 protegidas o 120 días) DEBILITADA
- Igual que 401: el «o» puede ser el que ocurra después; el 29 puede tener una justificación estadística (poder) que el auditor no leyó.
- El ritmo de protegidas usado para juzgarlo puede ser de otra ventana o sensor.

## DEC-15: #937 en main sin entrada de bitácora del merge ni frase de Nicolás
- La entrada puede estar en otra parte de la bitácora (otra fecha, otro nombre del PR), en el PR mismo (comentario de Nicolás), o en un bloque de arranque.
- f4ec1061d puede no ser el merge de #937.
- La bitácora citada es de 0472cd95e; la entrada puede estar en un commit posterior de loop/activo.
- El merge pudo hacerlo Nicolás desde la web (entonces la frase es el merge mismo).

## Generales
- La instantánea de main en D: puede no ser 438a60a1e exacto.
- Re-correr los scripts del auditor puede leer el checkout de trabajo (rama loop/activo) en vez de 438a60a1e.

---
sha256 del contenido anterior a este bloque: 67d220312bfb59baff6b0c9e88328229b63c18436757e67ca7e898bb24903e30
Hora del servidor al cerrar: Date: Wed, 11 Nov 2026 01:06:33 GMT
