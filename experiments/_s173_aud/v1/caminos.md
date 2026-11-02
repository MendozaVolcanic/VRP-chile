# Caminos por los que cada afirmación podría estar mal (escrito ANTES de abrir ningún archivo citado)

Verificador V1, eje «censo de consumidores del flag enable_modis_codigo_mirova», PR A (0a0dae344) y PR B (c9525f994).
Sólo tengo título, lugar y gravedad del auditor. No he abierto ninguno de los archivos citados.

## 161 Tras el revert de B la vigilancia de K vuelve a contar como K los records MODIS de la vía y pide revertir K
- El revert de B deja el código de A; si A ya clasifica por `via_codigo_mirova` / `final_hotspot_source`, el hallazgo se refiere sólo a B y queda REFUTADO sobre A.
- La vigilancia puede identificar K por `codigo_sha`, por fecha, o por los tres flags de K: hay que ver cuál usa y si los records de la vía llevan los flags de K además del suyo.
- «Pide revertir K» puede ser un texto de aviso, no una acción: medir qué hace realmente (exit code, archivo, issue).
- La vigilancia puede correr sólo sobre la sombra (34 volcanes) y no sobre los 11 Tier A: ventana y universo.
- `pipeline/store.py:549` puede escribir el campo sólo bajo una condición (p. ej. sólo cuando la vía dispara) y los records sin disparo de la vía serían indistinguibles de K de todos modos.
- Escenario: ¿existen records reales de la vía? Si X3 es cierto (sólo sintéticos), el daño del revert es nulo hasta que B corra en producción; gravedad condicionada al tiempo que B esté encendida.

## 162 Tras el revert de B el marcador del mapa de un record de la vía vuelve al primer píxel alertado (14,89 km en V2)
- El marcador puede leer `final_hotspot_lat/lon`, que escribe el pipeline, no el tablero: entonces el revert del frontend no cambia la posición.
- El 14,89 km puede venir de un record sintético o de un caso de prueba, no de un dato real.
- La línea 1631 de A y 1618 de B pueden ser la misma función con distinto número; verificar por contenido (A101).
- Puede haber más de un lugar que pinte el marcador (index, diario, mosaico, comparacion): un segundo camino que el cambio de B no cubre.
- Si el predicado `isValidDetection` rechaza el record antes de pintar, el marcador no se ve y el hallazgo es invisible.

## 163 El revert de B borra de la ficha SDA y de MISSION el registro del período de MODIS con la vía; los datos quedan
- Es tautológico si el texto vive en B; la pregunta es si parte vive en A (y sobrevive al revert) y si el proyecto tiene una práctica de marcar reversiones (A113) que lo cubra.
- La ficha puede tener una versión v1.18 en A y otra en B: ver `git show` por rama.
- Gravedad: un doc borrado no tuerce una alerta; sí toca la transparencia algorítmica (CPLT). Lo mido como doc, no como alerta.

## 164 Una excepción de la vía distinta de pyproj deja MODIS mudo con el NRT en verde; el primer aviso llega a los 3 días
- `run_pipeline.py:279-280` puede atrapar sólo `ImportError`, o todo `Exception`: leer el except real.
- Si la excepción escapa, el job del NRT se pone rojo: entonces no es «verde».
- «Mudo» puede significar «sin records» o «records con K de reserva»: distinguir; si cae a K no está mudo.
- El healthcheck puede medir por volcán y por sensor con otro umbral que 3 días; medir el umbral real.
- `vigilancia_guardia_modis.py` puede correr más seguido (cron) y avisar antes.
- Control positivo: simular una excepción (monkeypatch en script propio) y ver si run_pipeline sigue y qué record escribe.

## 165 Documentos y comentarios operativos siguen diciendo producción = K o vía APAGADA; el aviso del tablero lo lee el operador
- `frontend/index.html:544` puede estar actualizado en B (el auditor pudo mirar A).
- El texto puede ser condicional a los datos (JS que lo cambia según `cambio_detector`).
- Un comentario de código no lo ve el operador: separar lo que ve el operador de lo que ve un programador.
- `pipeline/profile.py:906-907` puede ser un comentario histórico marcado con advertencia (práctica A113).

## 166 55 perfiles derivados heredan la vía sin declararla, entre ellos _s154_reproc_k_historico
- `pipeline/profile.py` resuelve `extends` un solo nivel: contar con un script propio cuántos perfiles heredan de mirova_equivalent y cuántos declaran la clave; el 55 puede incluir perfiles que heredan de otro padre.
- La clave puede leerse de `thresholds:` o de la raíz: si un perfil la declara en la sección equivocada, no la hereda ni la sobrescribe (A89 segunda forma).
- Que `_s154_reproc_k_historico` herede la vía sólo es defecto si alguien lo corre después de B: ver quién lo nombra (workflows, scripts) y si está archivado.
- `scripts/reemplazar_ventana_reproceso.py:7` puede ser un comentario o un default.
- Control positivo: cargar un perfil derivado con `VRP_PROFILE=<derivado>` desde la punta de B y leer `ENABLE_MODIS_CODIGO_MIROVA`.

## 169 Tras el revert el audit semanal saca a K de MODIS y la marca del tablero sigue diciendo vía
- El detector VIA_MODIS vive en A (según la definición del PR A): sobrevive al revert de B. Entonces el audit semanal sigue detectando la vía por records, no por flag: verificar qué lee.
- `cambio_detector.js` puede leer un JSON que el audit semanal regenera cada semana: el desfase sería como máximo una semana.
- Puede ser el mismo fenómeno que 161 con otro instrumento: fundir si procede.

## 167 La prueba serie pura K identifica K por codigo_sha y da por K los records de la vía
- Si la vía modifica `process_modis.py`, el `codigo_sha` cambia y la prueba vería «no K»: el hallazgo depende de cómo se calcula el sha (qué archivos entran).
- La prueba puede estar `skip` o acotada a una ventana de fechas.
- B puede haber modificado la prueba.

## 168 El tablero no lee via_codigo_mirova y el CSV exportado no la trae
- `final_hotspot_source` puede estar en el CSV y llevar «codigo_mirova»: entonces la vía sí viaja, con otro nombre.
- B puede agregar la columna (el auditor pudo mirar A).
- ¿Es defecto? Depende de si el operador necesita distinguir records de la vía: lo mido como trazabilidad (CPLT), no como alerta.

## 170 Filtros de artefacto calibrados con K aplicados a records de la vía con magnitud de unión y conteo de cúmulo
- Los filtros de `index.html:1336-1363` pueden aplicar sólo a VIIRS o a un sensor: ver la condición.
- `mirova_v750_codigo.py:735-737` es del código V750; ver si MODIS usa el mismo módulo y qué campos escribe (vrp_mw de unión vs pc.vrp_mw).
- Con 0 records reales de la vía (X3) el efecto hoy es 0; medirlo sobre los sintéticos y sobre un record K para ver si el filtro puede actuar (control positivo).

## X1 En las puntas de A y B ningún workflow que corre un perfil con la vía deja de instalar pyproj
- El workflow puede instalar por `requirements.txt` (y pyproj estar o no ahí) y no por `pip install pyproj` literal: grep de las dos formas.
- Un workflow puede correr un perfil derivado que hereda la vía (166) sin nombrar `mirova_equivalent`: cruzar la lista de perfiles de 166 con los yml.
- Workflows archivados en `_archive/` no corren: excluirlos pero decirlo.
- La vía puede degradar a K si falta pyproj (164): entonces «no instalar» no rompe, sólo silencia.

## X2 El `git revert` del merge de B sale limpio sobre main con o sin la rama claude/s172-sombra-34 (PR #932) mergeada antes, y las pruebas pasan sobre el árbol revertido
- «main del día» se mueve (NRT commitea data cada 2 h): medir sobre `origin/main` de hoy, no sobre a3c5a9b49.
- B aún no está mergeado: hay que simular el merge (squash o merge commit) y después revertir; el resultado depende de la estrategia (squash cambia el patch).
- sombra-34 puede tocar `scripts/vigilancia_sombra.py`, que B también toca: conflicto posible.
- «Las pruebas pasan» sin la suite completa (prohibida aquí): correré los archivos de prueba que B toca y los guards nombrados; lo demás SIN DATO.
- Disco: D: tiene 6,0 GB libres; un worktree nuevo puede acercarse al límite de 3 GB; medir `du` antes.

## X3 No existe ningún record real de la vía de MODIS en data/ (sólo sintéticos)
- Buscar `via_codigo_mirova` y `"codigo_mirova"` en TODO `data/` (todos los perfiles, no sólo mirova_equivalent) y en `origin/main` de hoy (la copia del worktree puede estar atrasada).
- Un record puede llevar el campo en `false` (K) y otro en `true`: contar por valor.
- Ramas: sombra-34 y loop/activo pueden traer records que main no tiene.
- Sintéticos: identificar por ruta (tests/fixtures, experiments) y por `volcano` ficticio.

## Patrón 6 (mover a A los cambios de B que leen records de la vía)
- Si A pasa a leer `via_codigo_mirova` y la guardia K de A exige «producción = K», puede chocar con una prueba o con el detector VIA_MODIS: ver qué guards de A fijan el estado.
- Un cambio de frontend en A sin records de la vía es inerte (bien), pero `cambio_detector.js` podría marcar «vía» por algún sintético.
- Preguntar: después de mover, ¿queda en B algo más que el flip del YAML y los docs? Si queda código, el revert sigue dejando consumidores huérfanos.

---
sha256 (antes de esta línea): 621cf4684ba8945f7546e85b11cfb2fc1ee8c9808ab7122ec1f6ebc2e51ed2ff
hora del servidor: Date: Mon, 02 Nov 2026 12:51:14 GMT
