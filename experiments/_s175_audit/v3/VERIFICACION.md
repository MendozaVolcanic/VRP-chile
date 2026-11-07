# VERIFICACION F3 (S175): decisiones y cierres S160 a S174

## Encabezado

- Hora del servidor: sábado 2026-11-07, 10:27 a 10:36 GMT (cabecera `Date` de github.com; `date -u` local coincide con 5 s de diferencia).
- Base de medición: `752d348bc67190e53b610989877e2405d238a1bc`. Bitácora de `loop/activo`: `395af8034` (y `06de6876a` donde la afirmación lo cita).
- Modelo: Sonnet 5.5 (`claude-sonnet-5-5`). Esfuerzo real con que corro: SIN DATO (el arnés no me lo informa; no hice sonda).
- Contexto limpio: no abrí `INFORME.md` del auditor ni sus columnas de razonamiento. Leí sus `.py` y sus salidas `censo_*` y `salida_cierres_desde_s160.txt` (permitido por el encargo) y el §3 del plan.
- `caminos.md` escrito antes de abrir ningún archivo citado: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378\experiments\_s175_audit\v3\caminos.md` (sha256 del cuerpo 3970662bf7553be5b62fb81ac2f90e463f57fbce985d4df331f111294a457bba, hora 10:28:15 GMT).
- Carpeta: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378\experiments\_s175_audit\v3\`. Mis scripts y sus salidas, y las copias de lo que leí en 752d348bc, están en `...\v3\instrumentos\`. Temporal: `C:\Users\nmend\vrp-temporales\s175_audit\v3\` (árbol 752 parcial de 71 MB, descartable).
- Llamadas a la API de GitHub: 1 (`gh pr view 952`). Nada tocado fuera de mi carpeta; sin git add, commit, stash ni checkout. `git status` del worktree sólo muestra carpetas sin seguimiento de otras sesiones y la mía.
- NO miré: los otros 18 hallazgos de F3 (sólo las seis afirmaciones recibidas); el contenido de los 308 encabezados de la bitácora; si #952 contiene exactamente `dd17fd97d` en su cabeza actual (`adc1c06e4`; la rama `claude/s174-cenit-falsos-verdes` lo contiene según `git branch -a --contains`); ningún PDF ni paper (no hubo citas de fuentes externas).

## En una pantalla

1. 251 CONFIRMADO EN PARTE (127 pleno; 25 sólo para MODIS), g3. 252 CONFIRMADO, g2.
2. 254 CONFIRMADO y ampliado: con el código de 752d348bc, insumo vacío y alertas sin cenit también salen `SIN SUSTRATO`, que `leer_retro.py:1227` rotula `OK`. g2 (lector de laboratorio; arreglo en #952 borrador, ya declarado en la bitácora).
3. 253 CONFIRMADO EN PARTE: el lector no maneja `sin_grilla`/`sin_mxd03` aparte y los excluye por la ruta genérica `via_sin_marca`, pero el `git grep` citado sólo encuentra un docstring; la «aprobación» consta sólo en el registro de la coordinadora. g1.
4. 257 CONFIRMADO: las dos líneas base rojas no se marcan (medido con los detectores de 752d348bc) y hay 65 coincidencias de cierre fuera de `censo.DOCS`. 258 CONFIRMADO EN PARTE: el valor 5 por semana consta como pendiente de Nicolás; la cita `:643` es de otro parámetro (`--sha-desde`). g2 ambos.

## Veredictos

### 251: CONFIRMADO EN PARTE, gravedad 3 (auditor 3)

Pregunta 1: si SINTOMAS describiera bien el MODIS de producción, ¿la medición lo vería? Sí: busco la marca S172 en el archivo y comparo contra el flag y los records. Pregunta 2: instrumento muerto daría 0 records y la marca S162 (control positivo) no aparecería; ambos aparecen.

- El fenómeno: desde el 2026-11-02 el MODIS de producción corre la vía «código MIROVA» con la geolocalización de 1 km del MxD03, no el detector K con la grilla de 5 km interpolada. Evidencia de código (752d348bc): `pipeline/profiles/mirova_equivalent.yaml:38` `enable_modis_codigo_mirova: true`; `pipeline/process_modis.py:637-648` (rama de la vía que lee MxD03 con `_MV.leer_geo_mxd03`); `docs/MISSION.md:7` marca S172. Evidencia de datos: `instrumentos\via_en_datos_todos.salida.txt`: de los records MODIS con `datetime_utc >= 2026-11-02 18:00` en los JSON de `data/mirova_equivalent` (denominador 98), 98 traen `via_codigo_mirova: true`; antes de esa fecha 15.351 sin la clave y 22 con `true` (reescritura de la ventana de 8 días, coherente con la marca S172 de MISSION).
- `docs/SINTOMAS.md` (copia en `instrumentos\sint.md`, 248 líneas): `grep -n -E 'S172|MOD-D|código MIROVA'` da 0 líneas relevantes; el archivo no tiene ninguna marca S172. Las marcas ⚠️ son S160 (l. 8, 23, 226), S162 (l. 122) y una de otro asunto (l. 73).
- l. 127 (dentro de la marca S162 de §3): «Sigue abierta: producción usa `_interp_geo` hasta que MxD03 entre con el paquete MODIS». Falso para MODIS desde S172: la vía lee MxD03. Sólo sigue cierto para los records que caen a K (`sin_grilla`, `sin_mxd03`) y para la guardia K. CONFIRMADO.
- l. 25 («Régimen vigente: el detector K está en producción desde #850 ... banda 22 primaria en MODIS (D21)... En los datos rige desde la observación del 2026-09-18 ... salvo 26 records MODIS Terra»). Es cierto para VIIRS 375 y 750 y la banda 22 sigue siendo primaria en la vía; es falso para MODIS (98 de 98 records recientes son de la vía) y no lleva marca S172. EN PARTE.
- Por qué importa: el propio encabezado (l. 17-19) manda leer SINTOMAS «antes de proponer una palanca»; quien lo lea atribuiría un corrimiento de posición MODIS a `_interp_geo` o estratificaría por K/C0 cuando MODIS ya es otro detector.
- Ningún commit posterior a 752d348bc toca SINTOMAS en `origin/main` (`git log 752d348bc..origin/main -- docs/SINTOMAS.md` vacío, tras `git fetch`).
- Cómo reproducirlo: `git show 752d348bc:docs/SINTOMAS.md | sed -n '25p;127p'`; `python -I instrumentos\via_en_datos_todos.py` (desde la raíz del repo).

### 252: CONFIRMADO, gravedad 2 (auditor 3)

Pregunta 1: la medición vería una A85 todavía válida (daría `processed_utc` de antes de #883). Pregunta 2: instrumento muerto daría total 0; da 4.804. Control positivo: records de noviembre tienen `processed_utc` 2026-11 (143).

- `CLAUDE.md` a 752d348bc, A85 (l. 179): «los 4.286 records MODIS de ene-jun 2026 de los 11 Tier A tienen `processed_utc` de 2026-10». Lo medí: `instrumentos\a85_en_datos.salida.txt`, MODIS con `datetime_utc` 2026-01-01..2026-06-30 en todos los JSON de `data/mirova_equivalent`: 4.804 records, 4.286 con `processed_utc` 2026-10 y 518 sin `processed_utc`. Los 518 son de los 34 volcanes fuera del cron (`a85_sin_processed.salida.txt`: 34 archivos, 12 a 18 records cada uno, `first_processed_utc` y `regimen` ausentes). La corrección de #950 es correcta para los 11 Tier A.
- `docs/SINTOMAS.md:195-197` (copia `sint.md`) sigue diciendo «A85, marca S153: records MODIS de enero a junio de 2026 escritos con los gates intra-radio encendidos» como frontera a no cruzar, sin marca A113. La marca S160 de l. 226 sólo cubre #883 en el punto «Cambio de régimen», no esta línea. El texto es falso hoy para los Tier A.
- Gravedad 2 (no 3): es una advertencia de método, no una cifra; el daño es que alguien excluya o estratifique enero a junio de MODIS por una frontera que ya no existe.
- Esto es el síntoma que la línea base roja (1) del plan quería ver y que el censo no ve (ver 257).

### 254: CONFIRMADO, gravedad 2 (auditor 3)

Pregunta 1: si el reparo estuviera en main, `git merge-base --is-ancestor` daría 0 y el lector daría ROJO en insumo vacío; ambas cosas se miden. Pregunta 2: si el instrumento estuviera muerto, `probar_cenit_752.py` daría traceback o un ROJO «error interno»; en un intento previo con un entorno incompleto sí dio `ROJO: error interno`, así que el instrumento distingue.

- `git merge-base --is-ancestor dd17fd97d 752d348bc` → `exit=1` con ambos objetos presentes (`git cat-file -t` = commit), por lo que es «no es ancestro» y no un sha mal escrito. `git branch -a --contains dd17fd97d`: sólo `claude/s174-cenit-falsos-verdes` y su remota. `gh pr view 952`: `OPEN`, `isDraft: true`, `mergedAt: null`, cabeza `adc1c06e4`.
- `experiments/_s172_retro_paquete/leer_retro.py` en 752d348bc, l. 1226-1227: `_ec = cur["controles_cenit"]["estado"]` y `ctl["controles_cenit"] = {"estado": "OK (sin sustrato: la curva no se lee)" if _ec == "SIN SUSTRATO" else _ec, ...`; l. 1019: la excepción de `curva_cenit` se rotula `SIN SUSTRATO`. En `veredicto` el color se decide con `startswith("OK")`, de modo que ese rótulo no es rojo.
- Medición propia (`instrumentos\probar_cenit_752.salida.txt`, código idéntico a 752d348bc en `experiments/_s172_retro_paquete`, `_s162_v375`, `_s151_prereg_fk_11`, `_s157_prereg_d25` y `scripts/`, comprobado con `git diff --stat 752d348bc HEAD`): `controles_cenit` con insumo vacío (0 pasadas), con una pasada evaluable sin alertas y con una alerta sin cenit devuelve en los tres casos `{'estado': 'SIN SUSTRATO'}`, que l. 1227 convierte en `OK`. Es decir, no sólo falta el número de noches: un insumo vacío sale verde. El auditor y la bitácora (`LOOP_OBJETIVOS.md` l. 607 en 395af8034) lo dicen igual.
- Matiz: es una decisión de diseño documentada en el comentario de l. 1224-1225 («no es un control caído»). El defecto es que el verde no distingue «no hay curva» de «no hay insumo». Es un lector de laboratorio de la retrospectiva; no toca lo que ve el operador. Que quede fuera de main está rotulado y en curso (#952 borrador).
- La frase «Sí, arréglalos» consta en `tasks/LOOP_OBJETIVOS.md` l. 595 (395af8034) como «decisión de Nicolás». No tengo su transcripción: SIN DATO sobre si la frase es literal, pero está registrada.
- Cómo reproducirlo: `git merge-base --is-ancestor dd17fd97d 752d348bc; echo $?`; `git show 752d348bc:experiments/_s172_retro_paquete/leer_retro.py | sed -n 1225,1228p`; `python instrumentos\probar_cenit_752.py <raíz>\experiments\_s172_retro_paquete\leer_retro.py` (ruta en formato Windows).

### 253: CONFIRMADO EN PARTE, gravedad 1 (auditor 2)

Pregunta 1: la medición vería un lector que sí manejara las marcas (habría una rama con `sin_grilla`/`sin_mxd03`); no hay. Pregunta 2: control positivo del grep, `git grep` sobre todo el repo encuentra otros archivos con las cadenas, así que el instrumento no está ciego.

- El `git grep -n -E 'sin_grilla|sin_mxd03' 752d348bc -- experiments/_s172_retro_paquete` del auditor devuelve una sola línea, `controles_via.py:50`, un docstring. No muestra las líneas citadas. El mecanismo real es genérico: `leer_retro.py:270-271` (`elif rv.get("via_codigo_mirova") is not True: f["estado"] = "via_sin_marca:" + str(...)`), `:354` (`f["_evaluable"] = f["estado"] == "ok"`, la pasada sale de la evaluación) y `c_via` (l. 536 y 544/546: `ROJO` en R25 si más de 10 % de una clase, `ROJO` con una sola en los demás tramos). Eso se cumple, no por las cadenas sino porque `str('sin_mxd03')` no es `True`. Las líneas 270-271 y 354 son exactas; 544 es la rama R25 y 546 la de los otros tramos.
- «No implementada» CONFIRMADO: `leer_retro.py` no menciona las cadenas; `BLOQUE_ARRANQUE_S175.md` l. 22 y `LOOP_OBJETIVOS.md` l. 677 (395af8034) dicen «NO IMPLEMENTADO todavía». Aprobación: sólo consta en el registro de la coordinadora («Sí, a todo», Nicolás); sin transcripción, SIN DATO sobre la literalidad.
- Contexto que cambia la gravedad: en la producción el audit semanal sí trata esos records como K (`tests/test_auto_audit_via_modis_s172.py:53`, `detector_de_record(...) == "K"`; `scripts/auto_audit_weekly.py` en 752d348bc). Lo que falta está sólo en el lector de la retrospectiva, y falla hacia el rojo (se detiene y se ve), no hacia un verde falso.
- Ocurrencias: de los 98 records MODIS recientes ninguno es una cadena distinta de `true` (`via_en_datos_todos.salida.txt`); en la retrospectiva `_s172_retro_paquete` no hay salidas versionadas, así que cuántos records caerían ahí es SIN DATO.

### 257: CONFIRMADO, gravedad 2 (auditor 2)

Pregunta 1: si el censo viera las líneas base rojas, `tipos_de_cierre` daría algo en esas líneas. Pregunta 2: control positivo con una frase sintética (`['cerrada','no_reabrir','despreciable']`); el instrumento está vivo.

- `censo.py` de 752d348bc l. 54-66: `DOCS` son cinco archivos (`MIROVA_DIVERGENCES`, `CLAUDE.md`, `MISSION`, `HYPOTHESIS_LOG`, `META_RULES_S80`) y `PATRONES` son palabras clave de cierre. El propio docstring lo llama «un PISO» y dice «NO juzga ninguna».
- Línea base roja (1), `77e54e8e0^`: la línea de A85 en `CLAUDE.md` l. 177 da `tipos=[]` (`instrumentos\censo_lineas_base.salida.txt`). El desfase está contra los datos, y el censo no lee datos. No podía marcarla por construcción.
- Línea base roja (2), `d516b9d8c`: la frase «C0 antes del 2026-09-18» sólo está en `docs/SINTOMAS.md` l. 9 (0 coincidencias en las cinco `DOCS`), con `tipos=[]` y fuera de `DOCS`. No la ve.
- «Cierres de S160 en adelante»: medí por otra ruta que la del auditor. Con los mismos detectores sobre archivos fuera de `DOCS`: 65 coincidencias de palabra de cierre en `tasks/LOOP_OBJETIVOS.md` (47, de 7.629 líneas, en 395af8034), `BLOQUE_ARRANQUE_S160/S161/S163/S164/S175` (8), `docs/AUDIT_S155/S158/S160` (9) y `SINTOMAS.md` (1) (`instrumentos\censo_fuera_de_docs.salida.txt`). No todas son cierres nuevos ni todas de S160 en adelante (no las separé por fecha), pero el hecho de que `LOOP_OBJETIVOS` y los bloques de arranque queden fuera del censo basta: la bitácora de la rama es donde nacen las decisiones y los cierres.
- Lo del auditor (censo idéntico en `77e54e8e0^` y 752d348bc, 132 filas, 74 sin respaldo; 0 cierres con blame posterior a 2026-10-22 fuera de CLAUDE/HISTORIA): coincide con lo que vería un censo que no cubre esos documentos. No es una verificación de «no hay cierres nuevos», y hay que leerlo así. El censo declara ser piso, de modo que el defecto es de uso (usarlo como vara) y no del script.
- Gravedad 2: afecta al instrumento de la auditoría, no a una alerta.

### 258: CONFIRMADO EN PARTE, gravedad 2 (auditor 2)

Pregunta 1: si Nicolás hubiera dado una frase para los valores, estaría en el registro de la bitácora; la medición busca ese texto. Pregunta 2: control positivo, las otras frases de Nicolás sí aparecen en el mismo archivo («14 noches», «Ventana fija, una vuelta», «Sí, sexta vuelta»). Un negativo («no hay frase») es la medición más débil: sólo vale para lo que revisé (la bitácora en 395af8034 y el bloque S175).

- `experiments/_s162_v750a/evaluar_v750a.py` en 752d348bc: l. 116 comentario «Decisiones de la coordinadora (default reversible, Nicolás no eligió; LR3 las deja pendientes de confirmar)»; l. 117 `NOCHES_MIN_SEMANA = 5`; l. 118 `SEMANA_EXIGE_SIN_CAMBIO = False`. Los dos valores están declarados como de la coordinadora y la salida impresa lo repite (l. 1002 «coordinadora 5 por semana»).
- `LOOP_OBJETIVOS.md` en 06de6876a l. 605: «Defaults de la coordinadora, sin elección de Nicolás: umbral 5 por semana y exigencia sólo en conjunto y cambiados». En 395af8034 l. 620: «Pendiente de Nicolás: NOCHES_MIN_SEMANA = 5 y SEMANA_EXIGE_SIN_CAMBIO = False (decisiones de la coordinadora)». CONFIRMADO para el 5 por semana.
- Corrección: l. 643 de 06de6876a es otro asunto: la coordinadora aplicó `--sha-desde` obligatorio en la sombra «sin frase explícita de Nicolás» (R2-02). No es `l. 117-118`. La afirmación junta dos decisiones distintas bajo una cita.
- `SEMANA_EXIGE_SIN_CAMBIO = False` quedó rebajada por una decisión de Nicolás posterior: «Sí, sexta vuelta» (R5-03, `LOOP_OBJETIVOS.md` 395af8034 l. 594 y 600) añadió `NOCHES_MIN_SIN_CAMBIO = 14` para los nueve volcanes sin cambio; el código lo marca con «⚠️ S174 (R5-03, A113)» en l. 120 y define el valor en l. 126. Por lo tanto sólo el umbral 5 por semana (y el `False` para la exigencia por semana) sigue sin frase.
- Sellado: «lector sellado» es inexacto a 752d348bc; `LOOP_OBJETIVOS.md` l. 574 (395af8034) dice que quedan «la corrida completa del medidor de V750-A para el sello». #945 se mergeó con «Sí, mergea el 945» (l. 574), que cubre el PR pero no consta que Nicolás viera estos dos valores.
- Gravedad 2: no hay efecto en el dashboard del operador; con ventana fija y 5 por semana una semana vacía deja la lectura en PROVISORIO para siempre (nota del autor, l. 620), es decir, el riesgo es una decisión de adopción bloqueada, no una alerta torcida.

## Hallazgos propios

### V3-01: una cita del hallazgo 258 mezcla dos decisiones distintas

- ARCHIVO:LÍNEA: `tasks/LOOP_OBJETIVOS.md` 06de6876a l. 605 y 643; `experiments/_s162_v750a/evaluar_v750a.py` 752d348bc l. 117-118.
- QUÉ PASA: la afirmación 258 cita dos líneas de la bitácora como si respaldaran lo mismo, pero l. 643 trata de `--sha-desde` obligatorio, que es un cambio de uso del lector y no un parámetro. Es un defecto de la cita de la auditoría, no del sistema.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `git show 06de6876a:tasks/LOOP_OBJETIVOS.md | sed -n '605p;643p'`.
- CONFIANZA: CONFIRMADO. GRAVEDAD: 1.

### V3-02: 518 records MODIS de enero a junio de 2026 de los 34 volcanes fuera del cron no tienen `processed_utc` ni `regimen`

- ARCHIVO:LÍNEA: SCRIPT:SALIDA `instrumentos\a85_sin_processed.salida.txt` (34 archivos, 12 a 18 records cada uno).
- QUÉ PASA: esos records nunca se reprocesaron con K (sin marca de vintage), así que no se puede afirmar de ellos lo que A85 dice de los 11 Tier A. Es el denominador oculto de la frase «los 4.286 records MODIS de ene-jun 2026».
- CÓMO SE VE EN EL DASHBOARD: invisible (los 34 no se publican en el cron).
- CÓMO REPRODUCIRLO: `python -I instrumentos\a85_sin_processed.py` desde la raíz del repo, sobre 752d348bc.
- CONFIANZA: CONFIRMADO. GRAVEDAD: 1. Seguimiento, fuera de eje.

### Fundidos con el auditor

Los seis veredictos de arriba cubren las seis afirmaciones. No encontré duplicados entre hallazgos ajenos que fundir (sólo vi estas seis).

## SEGUIMIENTOS

- `docs/SINTOMAS.md` tiene otras frases dependientes del detector MODIS de producción que no revisé línea por línea (sólo las citadas).
- `docs/SINTOMAS.md:9` conserva «C0 antes del 2026-09-18, K después» con la marca S160 sólo en el párrafo de l. 8; el hallazgo 281 de S160 ya está tratado, no lo repito.
- `v2_conf204.py` sin seguimiento en la raíz del worktree es de otra sesión; no lo toqué.

## VERIFICADO LIMPIO

- La corrección de A85 en `CLAUDE.md` (4.286 con `processed_utc` 2026-10 en los Tier A) es correcta contra los datos de 752d348bc. Comando: `python -I instrumentos\a85_en_datos.py`. Vara: los JSON versionados en 752d348bc, no los de GitHub vivo.
- `git merge-base --is-ancestor dd17fd97d 752d348bc` devuelve 1 de verdad (no 128).

## SIN DATO

- Esfuerzo real con que corro.
- Literalidad de las frases de Nicolás («Sí, arréglalos», «Sí, a todo»): sólo consta el registro de la coordinadora.
- Cuántos records de la retrospectiva caerían en `sin_grilla`/`sin_mxd03` (no hay salidas versionadas del lector).
- Si `dd17fd97d` sigue siendo ancestro de la cabeza actual `adc1c06e4` de #952 (no lo consulté).

## FUERA DE ALCANCE

Arreglar SINTOMAS, el lector o el censo; verificar los otros hallazgos de F3; el contenido de PRs fuera de main más allá de lo citado.

Hora del servidor al cerrar: sábado 2026-11-07, 10:36 GMT.
