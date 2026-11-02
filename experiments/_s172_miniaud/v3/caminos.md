# caminos.md: caminos por los que cada afirmacion podria estar mal

Escrito ANTES de abrir cualquier archivo citado. Solo conozco titulo, archivo:linea y gravedad de cada item.
Objeto: PR B (b42823194, worktree D:/vrp-trabajo/worktrees/s172-miniaud-b), PR A (c83882fcf, solo git show), base d3cd0b2ae.

## MA172-303: 55 perfiles derivados pasan de via MODIS apagada a encendida; sus workflows de despacho no instalan pyproj
1. El conteo "55" puede venir de contar archivos YAML y no perfiles que realmente heredan (extends) de mirova_equivalent; o contar perfiles que ya tenian el flag fijado explicitamente en false.
2. `extends` puede resolverse en un solo nivel (ver DATO-COORD): el censo cambiaria (podrian ser mas o menos de 55).
3. El flag se lee de pipeline.profile y no del YAML (A89): un perfil puede declararlo pero el cargador no lo propagar; o puede haber una lista blanca de claves que el perfil hijo hereda (merge profundo vs superficial: `thresholds:` anidado).
4. "Pasan de apagada a encendida sin escribirlo" puede ser cierto de herencia pero irrelevante: los perfiles de archivo/experimentos que no se ejecutan jamas (sin consumidor vivo).
5. "Sus workflows de despacho no instalan pyproj": el workflow puede instalar pyproj via requirements.txt, un paso `pip install -r`, un cache, o pyproj puede no ser necesario para MODIS si la via importa pyproj perezosamente; o el workflow no corre MODIS (MODIS solo corre en Linux Actions; los de despacho pueden ser de VIIRS).
6. Que pyproj falte no rompe si la via cae a K con aviso (degradacion con gracia); la gravedad podria ser menor o mayor.
7. La copia del worktree (b42823194) vs. el HEAD de PR A: el defecto podria existir solo en una de las dos ramas, o requerir ambas.
8. El perfil `guardia_k_modis.yaml` (PR A) fija el flag explicitamente a false? Si es asi el aviso no aplica a la guardia.
9. Un test existente (guard de coherencia de perfiles) podria ya cubrir el censo, haciendo el hallazgo inocuo.

## MA172-304: el audit semanal descarta sin aviso los records MODIS de K en noches de la via (tras revert y caidas a K)
1. El descarte puede estar intencional y documentado (detector VIA_MODIS filtra por via_codigo_mirova); "sin aviso" puede ser falso si se emite un contador en el informe.
2. La logica de descarte puede ser de 2 caminos distintos (lineas 432-437 vs 471-475): uno afecta y el otro no; el auditor puede haber mezclado.
3. "tras un revert y caidas a K": depende de que records de K tengan via_codigo_mirova ausente o false; si el campo no existe en records de K, el filtro por `is True` los descarta; si el filtro es por `!= False`, no.
4. El audit semanal tiene ventana temporal; si cubre 7 dias, un revert breve afecta una fraccion; la gravedad depende del denominador.
5. La clave de record puede incluir sensor/fecha y el store hace dedupe: records de K y de via en la misma pasada no coexisten, entonces "descartar" es imposible.
6. El script puede no correr en CI con datos reales (solo auditoria offline).
7. Que sea PR A o PR B: el detector VIA_MODIS es de PR A; con el flag apagado (PR A solo) es inerte.

## MA172-305: los cron reales llegan 4 a 5,7 h tarde; la separacion de horarios de la guardia (17:40) no existe y se solapara con laboratorio, sombra y NRT
1. La medicion de la demora de cron: depende de que runs consultaron (ventana), el estrato (otros workflows), si GitHub retraso por carga; la guardia aun no tiene runs (no existe en main), entonces la inferencia es por otros workflows, no por la guardia.
2. El workflow tiene `concurrency` group; si esta en `push-main` o un grupo propio, el solape no importa (se serializa) y "se solapara" seria benigno; o al reves, un grupo compartido desplaza a runs pendientes (regla del proyecto: solo un pendiente por grupo).
3. El cron en UTC vs hora de Chile; el auditor pudo confundir zona horaria (cron-job.org usa zona del trabajo, pero GitHub schedule siempre UTC).
4. Los "4 a 5,7 h" pueden ser de cron de GitHub con `schedule` (inexacto) y el proyecto ya usa cron-job.org externo para despachar (workflow_dispatch), en cuyo caso el schedule de GitHub es respaldo.
5. "No existe separacion" puede ser cierto pero sin consecuencia si la guardia no comparte archivos con el NRT.
6. La fecha usada para el cron: si hay workflow_dispatch por cron-job.org con hora propia, el yml tiene otra hora.

## MA172-205: tras una reversion la marca del tablero sigue diciendo que MODIS viene de la via y el escalon de vuelta queda sin marca
1. La marca del tablero (cambio_detector.js) puede basarse en los datos (campo via_codigo_mirova de los records): tras revert, los records historicos conservan el campo, entonces la marca refleja la fecha de cada record, no el estado actual; "sigue diciendo" puede ser correcto y deseado (historico).
2. El "escalon de vuelta" (revert) puede estar fuera de diseno declarado (la regla de reversion borrador); el hallazgo puede ser un requisito no especificado.
3. cambio_detector.js puede estar en PR A y no depender del flag; hay que ver si la logica lee fechas fijas (constante) o datos.
4. Puede haber una prueba JS/py que ejecuta el archivo con node y cubre el caso.
5. La vista que consume (index/diario/mosaico) puede no incluir cambio_detector.js (copia local de helpers).
6. Quedaria "sin marca" pero hay otra marca K existente (la de #850) que cubre el tramo; el efecto visible puede ser nulo.

## MA172-211 y MA172-307: nulo de la guardia da diferencias por version de producto (NRT vs estandar), no por detector
1. Son el mismo defecto (duplicados): fundir. Confirmar que las lineas coinciden (236-246 vs 232-247) y ambos apuntan a vigilancia_guardia_modis.py.
2. El nulo compara guardia (K) vs produccion (K sin via?) ; si ambos usan el mismo fetch en el mismo run, la version del producto es la misma y no hay diferencia; si cada uno baja por separado en momentos distintos, NRT->Standard upgrade puede ocurrir entre ambos.
3. CLAUDE.md dice: Delta BT <0.1K, despreciable para VRP; el efecto podria ser sub-umbral.
4. El script puede ya comparar `product_version` y excluir los pares con versiones distintas; el hallazgo seria falso.
5. Workflow lineas 117-118: pueden fijar el producto o pasar `--product standard`.
6. Un control positivo: fabricar dos records con distinto product_version y ver que dice el script (el arnes sintetico).
7. Que el nulo "se vea" afectado depende de la regla de decision (umbral de diferencias); si ESTA tolerancia absorbe, no hay INVESTIGAR falso.

## DATO-COORD: `extends` resuelve un solo nivel en _load_profile
1. Puede resolver recursivamente: leer la funcion, no inferir; hacer prueba con perfil sintetico de 3 niveles (en mi carpeta, sin tocar el repo: usar una copia de modulo o monkeypatch de ruta de perfiles).
2. Aun si es un nivel, cambia el censo solo si hay perfiles de 2 niveles reales; hay que contarlos con script (A89: leer pipeline.profile, no el YAML).
3. Puede haber un chequeo que lanza error si extends apunta a un perfil con extends (falla ruidosa en vez de silenciosa).
4. Merge de `thresholds:` anidado: hijo con thresholds parcial puede borrar el flag del padre (merge superficial) o no (merge profundo); distinto del tema de niveles.
5. El censo "55" del auditor puede depender de cuanto-nivel; si el cargador es recursivo, el numero lo fija el auditor correctamente; si es un nivel, algunos de los 55 NO heredarian, entonces el hallazgo sobrestima; o algunos perfiles de 2 niveles heredarian "por accidente" (si el cargador recursa por otra via).

## Comunes a todos
- La ventana/denominador: cada numero necesita su denominador (A90).
- El worktree comparte HEAD b42823194: PR A solo (c83882fcf) vs PR B tienen historias distintas (dato de git: padre de PR B es da67fa417, no la punta de PR A); un hallazgo "de PR A" puede estar verificado sobre el arbol de PR B que no contiene c83882fcf; hay que mirar cual archivos existen en cual.
- Verificar que los scripts de los auditores corren y leen lo que dicen; re-correr con control positivo.
- Un cero no distingue "no hay" de "no medi": cada medicion lleva control positivo.
- El flag se lee de pipeline.profile, no del YAML (A89).
- Espacio en D: es 6.6 GB; C: 35 GB: cuidar escrituras.

---
sha256 del contenido anterior a esta nota: ca5b99dec8ebc67c2c1a5dc80d029880d728c9d9b01d9271b20fe9420d0be8ce
Hora del servidor (date -u): Mon Nov  2 01:36:07 UTC 2026 (header Date de GitHub: 01:35:33 GMT)
No se vuelve a editar.
