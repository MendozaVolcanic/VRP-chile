# Verificador con contexto limpio, ronda 2: los nueve arreglos (VMX-01 a VMX-09)

## 1. Encabezado

- **Hora del servidor** (`Date` de `api.github.com`): inicio 16:20:29 GMT, cierre 16:26:31 GMT, Sat, 24 Oct 2026.
- **Commit medido**: `D:\vrp-trabajo\s162-mxd03`, rama `s162-mxd03-codigo`, HEAD `704097a952eb7fb769c9096f4643698ad1d449cc` (`git fetch origin --prune` previo). `origin/main` sigue en `80b819828`; `git diff --stat 80b819828f16 HEAD -- pipeline scripts volcanoes.yaml frontend data/mirova_equivalent` sigue vacío.
- **Modelo**: Claude Fable 5.1; esfuerzo fijado por la sesión que me lanzó.
- **CARPETA**: `D:\vrp-trabajo\s162-mxd03\experiments\_s162_mxd03\verificador\ronda2\`. Sin commit, push ni despacho; 0 llamadas a la API REST (sólo el header `Date`). Fuera de mi carpeta no cambié nada: el único efecto transitorio fue un `git worktree add --detach` en `ronda2\arbol_prueba` para simular el paso nuevo del workflow, quitado con `git worktree remove --force` (`git worktree list | grep -c arbol_prueba` = 0).
- **Qué NO miré**: el runner real (`git fetch --depth 1` por sha en un checkout superficial no se puede simular en local: en un repo completo `--depth` escribiría `.git/shallow`, compartido con el checkout de C:); HDF reales; el informe del auditor ni el razonamiento de la coordinadora más allá de la tabla `RESPUESTA_VERIFICADOR.md`.
- **Vara**: la misma de la ronda 1 (pre-registro sellado). Comprobé que la copia que viaja en la rama (`experiments/_s159/mxd03_prereg/PREREGISTRO_MXD03.md`, HEAD) es **idéntica byte a byte** a la copia sellada que leí en la ronda 1 (`diff` exit 0); en `80b819828` y `87e91adf0` el archivo estaba sin el bloque del sello (mismo blob `d7dec543`), lo que explica las 39 líneas agregadas en la rama.

## 2. Veredicto global

**Se puede despachar el humo.** Los nueve arreglos hacen lo que la tabla dice; ninguno rompe otra cosa que yo haya podido medir (22 de 22 pruebas, 5 de 5 mutaciones del auditor, 0 de 22 contra el vacío, punta a punta OK, mis 11 mutaciones propias ahora atrapadas 11 de 11, arnés sintético 4 de 4). Dos quedan **ARREGLADO EN PARTE** por razones declaradas y sin peso en el veredicto del A/B: VMX-06 (el homónimo sigue tapando al evaluador después de `import probe_mxd03_ab`, en los caminos reales no se pisa) y VMX-08 (el `fetch --depth 1` por sha sólo lo puede probar el runner; el paso nuevo lo hace al arrancar cada job, así que el humo lo decide). Tres hallazgos nuevos, los tres de gravedad 1 y de operación (VMX-10 a VMX-12).

## 3. Veredicto por hallazgo

| hallazgo | veredicto | evidencia de esta ronda |
|---|---|---|
| VMX-01 humo sin control 1 | **ARREGLADO** | `probe-s162-mxd03.yml:32`: `solo=MYD021KM.A2026073.0705,…` (4 gránulos); `yaml.safe_load` → claves `['name','on','concurrency','jobs']`, ramas exactas, pasos en orden `Token presente, checkout, setup-python, Dependencias, Codigo del job…, Arnes, Control 4, Upload`. El gránulo trae Láscar `bajo1` expuesta (z 44,59) y es el del control S151 (`probe_mxd03_ab.py:84`) |
| VMX-02 sin dedupe | **ARREGLADO** | `verif_duplicados_artefactos_r2_salida.txt`: una copia `DUPLICADOS=OK`, dos copias en subcarpetas `DUPLICADOS=INDECIDIBLE` (P2 sigue contando doble, -1 a -2, pero el veredicto queda INDECIDIBLE por `veredicto()` l. 377). Prueba 20 del auditor. Nota VMX-11 |
| VMX-03 suite no fija el camino real | **ARREGLADO** | `rerun_probar_evaluar_mxd03_salida.txt`: 22 de 22 y 5 de 5; `rerun_probar_evaluar_contra_vacio_salida.txt`: 0 de 22 (el vacío gana `vara_desde_estado`, `p1b`, `control_*` que devuelven OK, así que las pruebas 13 a 22 fallan por aserción, no por excepción); `rerun_verif_mutaciones_propias_evaluador_salida.txt`: **11 de 11** atrapadas (V1 por 15, V2 por 16, V3 y V4 por 18, V5 por 19, V6 por 17, V9 por 13, V10 por 14 y 22, V11 por 16) |
| VMX-04 union tautológica, sin re-etiquetado | **ARREGLADO** | Camino real medido: `evaluar_ref_real_salida.txt` (evaluador con `--ref D:/vrp-trabajo/temporales/s162_mxd03/ref`, población real, artefacto con sólo una cabecera): `control reetiquetado OK` (0 distintas, 0 sobran), `referencia OK`, `predicado OK`, `duplicados OK`; el subproceso `poblacion_mxd03.py --sin-bajar --salida` corrió entero. Sin `--ref`: `rerun_probar_punta_a_punta_salida.txt` muestra `control reetiquetado INDECIDIBLE`. `control_reetiquetado_salida.txt` de la coordinadora reproduce lo mismo sobre la población real. Prueba 21. Nota: compara `lab, z, partida, vrp_mirova`, no `pub_guardada`, `expuesta` ni `r_nulos` (esos alimentan `decide()` y los nulos del arnés, ya corridos; peso bajo) |
| VMX-05 a `bajo1` partida fuera de P2 | **ARREGLADO** | `_invisible` l. 99-104 exige `lab == "neg_limpio"`; prueba 22 (`delta_x == 2` con una `bajo1` partida y un negativo partido) pasa, y mi mutación V7 la atrapa la 6 |
| VMX-05 b P6 parcial | **ARREGLADO** | `p6` l. 210-217: toda partida que cambia, con `invisible` y `en_p2`; prueba 22 exige los dos casos en P6 |
| VMX-05 c signo de P2 sin CC | **ARREGLADO** (por lectura) | `main` l. 483-486: imprime «ATENCION (§6)» si `sgn(sin_cc) != sgn(p2)`. No lo ejercité con un caso de signos distintos; es una línea de salida, no decide |
| VMX-05 d sha256 del predicado | **ARREGLADO** | `probe_mxd03_ab.py:267-270` escribe `sha256_frontend_index` en la cabecera; `evaluar_mxd03.py:443-447` exige igualdad con el html local. Medido: con el sha correcto `predicado OK` (`evaluar_ref_real_salida.txt`); sin él (cabecera de punta a punta) `predicado INDECIDIBLE` |
| VMX-06 homónimo | **ARREGLADO EN PARTE** | `vara_mxd03.py:40-45`: `append` de las carpetas de 1.17 a 1.23 y `AQUI` al frente; medido: `import vara_mxd03, evaluar_mxd03` → `experiments\_s162_mxd03\evaluar_mxd03.py` ✓. Pero `probar_probe_mxd03_ab.py:35-36` sólo ordena hasta que importa `probe_mxd03_ab`, cuyas líneas 66-67 reinsertan `_s151_mxd03_etiquetas` al frente: medido, tras `import probar_probe_mxd03_ab` esa carpeta queda en el índice 1 y la del A/B en el 17, y `import evaluar_mxd03` resuelve al de la 1.17. Ver VMX-10 |
| VMX-07 vara sin control de sesgo | **ARREGLADO** | `vara_desde_estado` l. 259-263 → «DETIENE SIN CONTROL DE SESGO»; `veredicto` l. 389-391 → DECIDE NICOLÁS. Pruebas 15 y 16; mi caso E (sólo Aqua, 34 gránulos, INTERP más cerca): `evaluar_sola` → `INTERP MAS CERCA SIN CONTROL DE SESGO`, evaluador → `DETIENE SIN CONTROL DE SESGO` (`verif_vara_evaluar_sintetico_r2_salida.txt`); casos A, B, D como en la ronda 1; C da INDECIDIBLE por diseño de la 1.23 |
| VMX-08 fetch por sha sin probar | **ARREGLADO EN PARTE** | Paso «Codigo del job = main congelado, y fetch por sha» (yml l. 67-78): `git fetch --depth 1 origin <sha mayoritario>`, `worktree add --detach`, `test -f …/pipeline/process_modis.py`, `worktree remove --force`; corre con el `bash -e` por defecto de Actions, antes del arnés. Simulé en local todo salvo el `fetch --depth 1`: `worktree add` del sha `3695f6758…` OK, `test -f` OK, `remove` OK, sin rastro. El `fetch` sólo lo prueba el runner: el humo lo decide antes de gastar una parte. Queda EN PARTE porque sigue sin medición propia |
| VMX-09 el job no comprobaba su código | **ARREGLADO** | Mismo paso: `git diff --quiet "$base" HEAD -- pipeline scripts volcanoes.yaml frontend data/mirova_equivalent || exit 1`, con `base` leído de `poblacion.json["checkout"]`. Simulado en local: `diff vacio OK`. Control negativo: `git diff --quiet 3695f67580e8 HEAD -- <rutas>` → exit 1 (el instrumento sí acusa) |

## 4. Hallazgos nuevos

### VMX-10
- **TÍTULO**: El arreglo de VMX-06 en la prueba del arnés no sobrevive al `import probe_mxd03_ab`.
- **ARCHIVO:LÍNEA**: `D:\vrp-trabajo\s162-mxd03\experiments\_s162_mxd03\probe_mxd03_ab.py:66-67` (reinserta `_s151_mxd03_etiquetas` y `_s151_mxd03_cumulo_121` en `sys.path[0]`); `probar_probe_mxd03_ab.py:35-39`; `experiments\_s151_mxd03_etiquetas\probar_probe_mxd03.py:20-21`.
- **QUÉ PASA**: medido en esta ronda: tras `import probar_probe_mxd03_ab`, `_s151_mxd03_etiquetas` queda en el índice 1 de `sys.path` y la carpeta del A/B en el 17; `import evaluar_mxd03` toma el de la 1.17. En los caminos reales no se pisa (el evaluador se lanza por ruta en `probar_punta_a_punta.py` y en mis scripts, y `recorrer_en_sha.py` no lo importa), pero la frase de la tabla «la prueba del arnés deja su carpeta primero» vale sólo hasta la línea 39 de esa prueba.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `cd experiments/_s162_mxd03 && python -c "import sys;sys.path.insert(0,'.');import probar_probe_mxd03_ab,evaluar_mxd03;print(evaluar_mxd03.__file__)"`.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 1.

### VMX-11
- **TÍTULO**: `control_duplicados` hace INDECIDIBLE el escenario «repetir la parte» del §10 si el artefacto viejo no se quita.
- **ARCHIVO:LÍNEA**: `evaluar_mxd03.py:293-298` (cuenta `(vol, dt)` sobre todas las filas `record`, incluidas `estado` `error` y `no_bajado`).
- **QUÉ PASA**: el §10 manda repetir una parte INCOMPLETA sobre el mismo código. Si el artefacto de la corrida fallida y el de la repetición quedan en la misma carpeta `--art`, cada pasada aparece dos veces (una `no_bajado`/`error`, otra `ok`) y el control da INDECIDIBLE. Es fail-safe (mejor que el doble conteo de antes) y es exactamente lo que el control debe hacer, pero quien evalúe tiene que **reemplazar** el artefacto de la parte repetida, no sumarlo.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `verif_duplicados_artefactos_r2.py` (dos copias → `DUPLICADOS=INDECIDIBLE`).
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 1 (operación).

### VMX-12
- **TÍTULO**: El re-etiquetado con `--ref` exige correr el evaluador desde el checkout del tag.
- **ARCHIVO:LÍNEA**: `poblacion_mxd03.py:114-121` (`head = git merge-base HEAD origin/main`; se niega con `data/` sucio o con HEAD distinto del merge-base en las rutas de producción); `evaluar_mxd03.py:427-440` (lo lanza en subproceso); `control_reetiquetado` l. 301-309 no compara `checkout`.
- **QUÉ PASA**: desde el worktree de la rama, `merge-base` es `80b819828` y todo cuadra (medido: `reetiquetado OK`). Si el evaluador se corriera desde un `main` posterior (por ejemplo tras mergear la rama), `merge-base` sería el propio HEAD, el `git diff` pasaría trivialmente y la población se regeneraría con el `data/` de ese día: cualquier record reescrito por el NRT en la ventana daría INDECIDIBLE (fail-safe), y si ninguno cambió pasaría sin aviso de que el checkout no es el congelado (el `predicado` sí acusaría un `frontend/index.html` distinto). No es un defecto del control, es una condición de uso que conviene dejar escrita junto al despacho: **evaluar desde el checkout del tag `s162-mxd03-codigo`**.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: n/a (lectura de `poblacion_mxd03.py:114-121`).
- **CONFIANZA**: CONFIRMADO (leído). **GRAVEDAD**: 1 (operación).

## 5. Observaciones sin ID (no son defectos)

- «SESGO POR SATELITE» sigue llegando a CUMPLE SIN DAÑO si lo demás está en verde (`veredicto` no lo manda a Nicolás): es lo que el §8 prueba 10 del texto sellado dice («no detiene»), y queda impreso en `vara`. Lo anoto para que no sorprenda.
- Mi caso C de la vara (Terra con interp más cerca, Aqua con MxD03 más cerca, simétricos) da INDECIDIBLE en `evaluar_sola.estado_vara`, no SESGO: la 1.23 sólo declara SESGO cuando el IC global excluye el cero. Es diseño de la 1.23, fuera de mi eje.
- La prueba 12 y la mutación «pareo a 300 s» siguen probando `pareadas`, que `main()` no usa; ahora el efecto real de `TOL_S` lo cubre el `reetiquetado` (la población se regenera con `TOL_S = 120` de `poblacion_mxd03.py`) y el control `pareo` de `main` (l. 421-422). Sin peso.

## 6. VERIFICADO LIMPIO

- Rutas de producción idénticas a `origin/main 80b819828` (diff vacío) con la rama 3 commits adelante.
- Pre-registro de la rama = copia sellada (diff exit 0).
- `probar_probe_mxd03_ab.py`: caso base OK, 4 de 4 (`rerun_probar_probe_mxd03_ab_salida.txt`).
- `probar_evaluar_mxd03.py --mutaciones`: 22 de 22, 5 de 5; `--modulo evaluar_vacio`: 0 de 22; `probar_punta_a_punta.py`: OK con `reetiquetado INDECIDIBLE` y `predicado INDECIDIBLE` además de `geometria INDECIDIBLE` (lo esperado sin `--ref` y sin cabecera real).
- `verif_mutaciones_propias_evaluador.py`: 11 de 11.
- Camino real `--ref` sobre la población real: `reetiquetado OK`, `referencia OK`, `predicado OK`, `duplicados OK` (`evaluar_ref_real_salida.txt`, `art_cabecera/resultado_mxd03.json`).
- Cadena de la vara, 5 casos (`verif_vara_evaluar_sintetico_r2_salida.txt`): A NO DETIENE, B DETIENE, C INDECIDIBLE → NO DETIENE, D SIN VARA → NO DETIENE, E DETIENE SIN CONTROL DE SESGO.
- Workflow: YAML válido, paso nuevo simulado (diff, worktree add/test/remove) con control negativo.

## 7. SIN DATO

- `git fetch --depth 1 origin <sha>` en el runner (VMX-08): lo decide el humo, antes del arnés.
- HDF reales (igual que en la ronda 1).

## 8. Archivos de esta carpeta

`rerun_probar_probe_mxd03_ab_salida.txt`, `rerun_probar_evaluar_mxd03_salida.txt`, `rerun_probar_evaluar_contra_vacio_salida.txt`, `rerun_probar_punta_a_punta_salida.txt`, `rerun_verif_mutaciones_propias_evaluador_salida.txt`, `rerun_verif_vara_evaluar_sintetico_salida.txt` (copia de la ronda 1, caso C con la expectativa vieja), `verif_vara_evaluar_sintetico_r2.py` + salida (5 casos), `verif_duplicados_artefactos_r2.py` + salida, `evaluar_ref_real_salida.txt` + `art_cabecera/` (cabecera con el sha256 real y `resultado_mxd03.json`), `hallazgos_ronda2.csv`, este informe.
