# Caminos por los que cada afirmación del frente F4t podría estar mal

Escrito antes de abrir ningún archivo citado. Sólo conozco título, archivo:línea y gravedad.
Base declarada: 752d348bc67190e53b610989877e2405d238a1bc. El worktree está en otro commit
(d1367c6f0), así que todo archivo se lee con `git show 752d348bc:<ruta>`, no del disco.

## Caminos generales (aplican a todas)

- G1. Copia atrasada o adelantada: el auditor leyó el disco de otro commit y no 752d348bc; las líneas no coinciden.
- G2. El simulador mide otra cosa: el monkeypatch reemplaza una función distinta de la que llama el camino real
  (por ejemplo parchea `earthaccess.search_data` pero el pipeline usa otro import, o parchea antes de que el
  módulo se recargue), y el resultado sale del parche, no del código.
- G3. La excepción simulada no tiene la forma real: el auditor inventa el texto o el tipo de excepción que
  earthaccess levanta; con la forma real el clasificador sí reconocería el caso.
- G4. Versión de librería: el comportamiento depende de la versión de earthaccess (0.17 local vs 0.19 CI); el
  auditor midió una y afirma la otra.
- G5. Un segundo camino aguas abajo atrapa el caso: aunque fetch.py no lo clasifique, otro guard (en
  run_pipeline, en nrt.yml, en el healthcheck, en un paso de "contar records") hace fallar el job o avisa.
- G6. El flag o la variable se lee de otro lado: el YAML del workflow pasa el token por otra variable, o el
  pipeline usa netrc, o el step tiene `continue-on-error`.
- G7. "Verde" se confunde con "success del job" vs "success del run": un step puede fallar sin que el run quede
  rojo, o viceversa.
- G8. La vara es otra: "nadie se entera" se mide por suscriptores del repo, pero el aviso podría llegar por
  correo de fallo de Actions al dueño (notificación de workflow fallido), que no depende de suscriptores.

## Por afirmación

- 381 (clasificador no lee status HTTP): G2, G3. Además: el status sí podría estar dentro del texto de la
  excepción que earthaccess arma (p.ej. "401 Client Error"), y el regex lo captura; el regex podría tener
  más alternativas de las citadas en l. 467-471; podría haber un chequeo previo de login (earthaccess.login
  con strategy) que falla antes del CMR. CMR search público no exige token: un 401 en CMR podría no darse en
  la realidad (escenario irreal). "Verde sin datos" depende de G5.
- 382 (guard de descarga ciego a DownloadFailure): G3, G4. DownloadFailure podría no existir en 0.17 o en 0.19;
  earthaccess.download podría devolver lista vacía sin excepción (entonces el guard ni siquiera ve una
  excepción, y la forma del fallo es otra). El test S124 podría sí cubrir esa forma. G5.
- 383 (avisos a un repo sin lectores): G8. subscribers_count cuenta "watchers" no estrellas; el dueño del repo
  recibe notificaciones de issues que abre un bot? (issues creados por github-actions no notifican al dueño
  si no es watcher; pero el dueño puede estar en "participating"). Fallos de workflow programado notifican
  por correo a quien lo creó/último que editó el cron. Puede haber otro canal (correo, Slack) en otro
  workflow. La fecha de la consulta API.
- 384 (gh label create sin --force): la línea podría tener `|| true` o `--force` en 752d348bc; el run citado
  podría ser de otro commit (anterior a un arreglo); el fallo podría ser otro step. El script f4t_04 podría
  simular gh en vez de medir.
- 385 (nrt.yml no exige escribir algo): G5, G7: podría haber un paso que cuenta commits/records o un
  healthcheck posterior que lo detecte (staleness). "único productor con cron" depende del inventario: otro
  workflow con cron podría tampoco exigirlo.
- 386 (21 workflows de despacho con USERNAME/PASSWORD sin guarda): el conteo depende del awk sobre un TSV
  generado por el auditor (instrumento propio); columnas mal asignadas; los secretos USERNAME/PASSWORD podrían
  ya no existir en el repo (entonces se resuelven a vacío y no hay login con el par vencido); earthaccess con
  token presente podría no usar el par (estrategia environment usa token primero). "8 logins por job" es un
  número a recontar. Son despacho manual: nadie los dispara sin Nicolás.
- 387 (token desconocido no abre issue): la línea 385-387 podría sí abrir issue en el caso "desconocido";
  token_edad podría devolver un código que el workflow trata como fallo (run rojo = correo). "48 a 72 h" de
  staleness viene de otra parte: verificar el umbral real.
- 388 (pipeline nunca mira exp): la afirmación es de ausencia (A89: el cero de un grep). Podría haber un
  chequeo de exp en otro módulo (scripts/, run_pipeline). La consecuencia (JWT vencido = texto cualquiera)
  depende de G3.
- 389 (earthaccess sin pin): requirements.txt podría pinnear y nrt.yml instalar sin requirements; la versión
  "0.19.0 en CI" hay que verla en un log, no suponerla; pip index necesita red (a PyPI, permitido, no NASA).
- 390 (primer aviso 2026-11-28): depende de la fecha de emisión del token (registro, no el valor), del umbral
  en token_edad.py l. 27 y del cron del healthcheck l. 21; la "fecha de rotación a 50 días" viene del
  registro de credenciales; aritmética de días con zona horaria.


---
sha256 del contenido anterior a este pie: 2385efbed424cfb2a75ac658f3fc0b1d3c61a0eeb9a99533689bae0eb8d472f7
Hora del servidor (github.com header): Date: Sun, 08 Nov 2026 04:38:10 GMT
