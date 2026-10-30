# Caminos por los que cada afirmacion podria estar mal (escrito ANTES de abrir ningun archivo citado ni INFORME.md)

Fuente unica: el texto de la tarea. Ningun archivo del arbol se habia leido todavia.

## B1 (juzga solo records con processed_utc posterior al inicio, con sha del disparo, + JSON de cobertura)
1. processed_utc no lo escribe store.py para los records de la via "codigo MIROVA" (otro escritor, otro campo, o solo en una rama): el filtro descarta todo (falso rojo) o nada (falso verde).
2. Reloj del runner vs reloj del inicio anotado: el inicio se anota con `date` del shell de un paso anterior; processed_utc usa datetime del proceso Python; si el formato difiere (Z, +00:00, naive, segundos vs microsegundos) la comparacion de strings falla o miente.
3. Comparacion lexicografica de strings vs datetime: formatos distintos dan orden equivocado.
4. store.py reescribe un record como duplicado o auto-upgrade NRT->Standard: puede conservar el processed_utc viejo (record de esta corrida no cuenta: falso rojo) o actualizarlo sin haber procesado nada nuevo (falso verde).
5. Corrida que escribe 0 records nuevos porque ya existian (reintento, segunda corrida del mismo dia): falso rojo; o falso verde si el record viejo cuenta.
6. El "sha del disparo": comparado contra GITHUB_SHA, contra el sha del record o el de la rama? workflow_dispatch en otra rama; sha corto vs largo.
7. JSON de cobertura ausente = falla: tambien cuando el paso que lo escribe se salta legitimamente? Busquedas fallidas parciales (una plataforma muerta, Suomi NPP cesada) cuentan como falla y dejan rojo diario?
8. Direccion del filtro: `>=` vs `>`; inicio anotado "antes de correr" pero despues del checkout; records del mismo segundo.
9. El job juzga solo lo producido por su corrida, pero data/ se commitea por otro job (merge): el JSON leido es el del job o el de main? Archivo de otro job de la matrix o checkout viejo.

## B2 (>=1 record por sensor y volcan; NOTA "miro y no hubo pasada" cuando todas las plataformas vivas respondieron sin granulos)
1. "Plataformas vivas": lista fija en codigo con Suomi NPP incluida sin fecha de cese (2026-11-02 13:00 UTC): desde el 3-nov, si se exige que todas respondan, o si un "sin granulos" de NPP se confunde con falla, rojo diario VIIRS. O al reves: si NPP cesada da error de busqueda en vez de lista vacia, "busqueda fallida" = rojo.
2. Corte por fecha usando hora local/naive o dia UTC del job vs hora de la pasada; borde 2026-11-03 15:00 UTC.
3. MODIS Terra y Aqua: se exigen ambas? Un dia sin pasada nocturna valida sobre el volcan.
4. Sensor con granulos pero sin ningun record (la via devuelve None en process_viirs.py l.773/781, process_viirs_mod.py l.509/517, process_modis.py l.657): causas legitimas (nube, datos faltantes, fuera de limites, calidad) y frecuentes: falso rojo diario. Medir en data/mirova_equivalent/ de main cuantas pasadas-dia por volcan-sensor no tienen record. Leer las ramas.
5. NOTA se escribe cuando "todas las plataformas vivas respondieron sin granulos"; si UNA falla la busqueda y otra viva dice vacio, debe ser rojo: lo es?
6. Cobertura JSON vacio/clave faltante interpretado como "sin granulos": falso verde (instrumento muerto == no hay pasada).
7. Volcanes: los 11 Tier A; se exige por los 11 o por los del matrix?
8. VIIRS 375 y 750 son sensores distintos en la sombra; se exigen ambos?

## B3 (VF3-01: un record de K caido de un dia anterior ya no deja rojo el job de hoy, pero uno de hoy si)
1. "de hoy" definido por processed_utc >= inicio de corrida y no por fecha de observacion: un record caido de hoy con fecha de observacion de ayer (pasada nocturna cruzando UTC) cuenta?
2. La "caida" se detecta por un campo (error/caida a K/motivo) que el pipeline no escribe o escribe con otro nombre (A89): el test pasa con datos sinteticos y la rama nunca dispara en produccion.
3. Records caidos de dias anteriores quedan en el JSON (ventana de 8 dias): que no tapen un fallo de hoy parecido.
4. Un record de hoy caido legitimo deja rojo diario?

## B4 (nrt-monitor.yml + scripts/nrt_monitor_decision.js, decidirSombra)
1. Zona horaria/borde: 2026-11-03 15:00 UTC vs hora de Chile; Date.parse de string sin Z; GitHub retrasa crons (30-60 min): con 26 h de umbral, margen de solo 2 h sobre un cron diario: falso rojo recurrente. Abre issue falso antes de la primera corrida?
2. Contar solo event == schedule: filtro del API (`event=schedule`) o a mano? Paginacion (per_page 30) puede dejar fuera la corrida verde; conclusion success vs skipped/cancelled.
3. Duplicados: busqueda del issue abierto por label/titulo; paginacion; label inexistente; concurrencia.
4. Permisos del workflow: `permissions: issues: write` y actions: read; si el workflow tiene permisos solo de lectura: 403.
5. Despacho manual verde que tapa fallo del cron: debe excluir workflow_dispatch; el modo medir=true no debe cerrar el issue.
6. Cerrar el issue cuando vuelve una corrida verde: corrida verde mas vieja que la que abrio el issue (cierre prematuro).
7. El paso nuevo falla y deja rojo el job NRT existente (acoplamiento); la decision del NRT existente no debe cambiar (regresion).
8. El monitor mismo corre por cron y puede ser retrasado: silencio == instrumento muerto.

## B5 (workflow: --cobertura-json, artefactos if: always(), "on" con comillas, solo EARTHDATA_TOKEN)
1. `if: always()` pero el path no existe cuando el paso falla temprano: if-no-files-found.
2. Orden de pasos: si el revisor sale con 1, los pasos siguientes (commit de datos) no corren y se pierden records buenos.
3. La cobertura la escribe el pipeline (pipeline/ congelado): quien la escribe? Si el diff toca pipeline/ viola el congelamiento.
4. Credenciales nuevas: grep de secrets.* en el diff; EARTHDATA_USERNAME/PASSWORD reaparecidas (A71).
5. `"on":` con comillas; input medir (booleano de workflow_dispatch llega como string "true"; comparar `== true` falla): el modo medir=true podria no activarse.
6. concurrency / push a main: grupo push-main o retry propio (guard G4).
7. Variable de inicio anotada via GITHUB_ENV en un paso con shell distinta; anotada antes de checkout o despues del pipeline.
8. Matrix de 11 jobs: nombres de artefacto duplicados (upload-artifact v4 da 409): el nombre debe incluir el volcan.

## B6 (pruebas: 23 nuevas; 20/23 rojas contra main; 23/23 con arreglo; 43/43; 149/149 con 4 saltadas)
1. "Rojas contra main" por ImportError/archivo faltante: rojas por ausencia, no por detectar el defecto.
2. Pruebas con datos sinteticos que reflejan la logica del autor (circularidad); reloj mockeado; tests que no ejercen el YAML real.
3. Pruebas del JS requieren node: las 4 saltadas pueden ser exactamente las que cubren B4 (node ausente) y dejan B4 sin cobertura real.
4. Suite corrida con arbol cambiando (A112): yo corro sobre arbol quieto.
5. Encoding/CRLF: el arbol es git archive con autocrlf=false (LF).
6. Los conteos 149 incluyen o no las 23: no mezclar.

## Vara
Contra el codigo del arbol (commit 16d9e894d) y los datos de main (git show, solo lectura). Sin red, sin escribir fuera de la carpeta.

---
sha256 del contenido anterior a esta linea: f0a4d2fbccabc4f9d548133dcf2252ac0d4ec05e565cd18c6671a8f6193a614a
hora: Fri Oct 30 04:42:09 UTC 2026
