# Bloque de arranque S190 (escrito por S189, 2026-11-17 00:27 UTC)

Anterior: `tasks/BLOQUE_ARRANQUE_S189.md` (histórico, no se toca). S189 fue corta: cerró por el aviso de
contexto (150 mil tokens) a las 00:25 UTC, recién aceptadas las recomendaciones de D1.

Estado fijado SIN trabajo local en vuelo, comprobado con `ps -ef | grep -E "cadena|vigilar|sleep"` vacío a las
00:25 UTC. Lo único que sigue corriendo es el run de Actions de la tanda 3.

## a. Todo en una pantalla

| Qué | Estado | Evidencia |
|---|---|---|
| Tanda 3 (DescabezadoGrande, CerroAzulQuizapu, LagunaDelMaule, NevadoDeLongavi, Antuco) | CORRIENDO | run 43906817147: 109 de 165 verdes, 0 rojos, 57 vivos a las 00:25 UTC |
| Cadena 4 a 7 | DETENIDA (no despachó nada) | log `D:\vrp-trabajo\temporales\s187_tanda2\cadena_4a7.log` vacío; S190 la relanza |
| `cadena_3a7.sh` (de S187) | MUERTA, no relanzar | ya despachó la tanda 3; su siguiente paso duplicaba el de `cadena_4a7.sh` |
| `cadena_4a7.sh` | con reintentos en el conteo de rojos | edición de S189, `bash -n` OK, no probada contra un corte real |
| D1 | DECIDIDA y con recomendaciones aceptadas, falta EJECUTAR la 1 | Nicolás «Sí, las tres» (≈00:20 UTC del 17): 1a, 2a, 3b |
| Respaldo para D1 | HECHO | `D:\vrp-trabajo\temporales\s189\respaldo_d1_rnvv\` (4 JSON + `MAIN_SHA.txt` = `7f864b885`) |
| Tandas 1 y 2 | APLICADAS en main | `bec44eb16` y `43ac1c5e6` |
| Alertas #1027 y #1028 | abiertas, sin acción | #1028: falla de descarga del 16 en Putana y SanJose; #1027: corrida en cola |
| Bitácora | al día hasta 00:26 UTC del 17 | entrada S189 en `tasks/LOOP_OBJETIVOS.md` §6 |

sha256 del respaldo: historia_34 OlcaParuma `fa97ff4b…a442f9`, Putana `3e71a7fb…13a40f`; sombra_34 OlcaParuma
`a972f5ab…2c9a`, Putana `169822f5…0cd6`.

## b. Decisiones que espera Nicolás

| # | Pregunta | Opciones | Recomendación |
|---|---|---|---|
| 1 | Merge del PR de retiro de Putana y OlcaParuma cuando exista | «mergea #N» o no | mergear tras suite verde y verificador limpio |
| 2 | Lastarria (no está en la RNVV, Tier A) | (a) se queda; (b) sale | (a), de los 11 de paridad (pregunta 4 de S189, no respondida explícitamente) |
| 3 | N1, D5, N2, D13, D15 | `tasks/DECISIONES_34_S187.md` §2 | las de esa hoja |
| 4 | Cada PR de tanda 3 a 7 | «mergea #N» | mergear con 0 huecos y 0 caídas a K |

## c. Lo aprendido

- Matar o cerrar la tarea de fondo de una sesión no garantiza matar el bash ni su `sleep` (quedan con PPID 1).
  S188 escribió «detenidos» sin `ps` y S189 encontró dos cadenas vivas que iban a despachar la tanda 4 dos
  veces. Regla general del workspace, en memoria `feedback_s189_cadenas_huerfanas.md`: comprobar con `ps` al
  abrir y al cerrar.
- El aviso de contexto saltó a los 150 mil tokens tras ≈15 llamadas: confirma la lección S188. S190 debe leer
  sólo con grep y delegar el PR de retiro a un subagente si se ve largo.

## d. Problemas abiertos e hipótesis

- CONFIRMADO: tanda 3 109 de 165 verdes y 0 rojos a las 00:25 UTC.
- CONFIRMADO: el tablero no lee `data/historia_34/` (Pages la excluye, `pages-deploy.yml:35` y `:86`); muestra
  a los 34 desde `data/sombra_34/` según la lista fija `VOLCANOES_ALL` de `frontend/index.html:837`.
- CONFIRMADO: `tests/test_sombra_34_s172.py:74` exige 34 y que la matriz de `sombra-34.yml` sea
  `volcanoes.yaml` activos menos el NRT; filtra por `v.get("active", True)`.
- SOSPECHA: el guard G9 («3 vistas coinciden», comentario en `volcanoes.yaml`) y
  `experiments/_s172_sombra34/vecinos.yaml` pueden romperse al retirar los dos; no lo miré.
- SOSPECHA: `A.LOS_34` de `experiments/_historia_34/aplicar_historia_34.py` podría ser una lista fija con los
  dos; no lo miré.
- SOSPECHA: mientras dure el reproceso, el NRT corre atrasado (estaba en cola a las 00:10 UTC).

## e. Ya cerrado, no rehacer

- Preguntas 1 a 3 de D1 respondidas (1a, 2a, 3b). La 3 queda como pendiente anotado: Tatara-San Pedro, Cay y
  Hornopirén no se agregan por ahora.
- Las alertas #1027 y #1028 ya están diagnosticadas (arriba); no piden cambio de código.
- El respaldo de los cuatro JSON ya está hecho.

## f. Prompt para S190

```
Eres S190 de VRP Chile, dueña única del loop (rama loop/activo en
C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile). Español de Chile, sin guiones largos ni
medios, rutas absolutas. El margen de contexto es corto (S189 llegó al aviso en ≈15 llamadas): grep en vez de
leer archivos enteros, nada de list_sessions, nunca leer tasks/LOOP_OBJETIVOS.md entero.

0. Verificar antes de creer: `git fetch origin --prune`, `git status -sb` (rama loop/activo),
   `git rev-parse HEAD` contra `git ls-remote origin -h refs/heads/loop/activo`; `date -u`;
   `ps -ef | grep -E "cadena|vigilar|sleep" | grep -v grep` (DEBE estar vacío; si no, matar por PID y volver
   a mirar); `gh run view 43906817147 --json status,conclusion`; `gh run list -w reproc-historia-via.yml --limit 3`.
1. Leer tasks/BLOQUE_ARRANQUE_S190.md entero (es corto) y la memoria feedback_s189_cadenas_huerfanas.md.
2. Lanzar en segundo plano `bash D:/vrp-trabajo/temporales/s187_tanda2/vigilar_run.sh 43906817147` (si la
   tanda 3 sigue viva) y `bash D:/vrp-trabajo/temporales/s187_tanda2/cadena_4a7.sh > .../cadena_4a7.log 2>&1`.
   NUNCA cadena_3a7.sh.
3. PR de retiro de D1 (Nicolás aceptó 1a): rama desde origin/main en un worktree de D:\vrp-trabajo\worktrees;
   `active: false` con comentario D1 en Putana y OlcaParuma de volcanoes.yaml (editar con Edit), sacarlos de
   la matriz de .github/workflows/sombra-34.yml, filtrarlos de VOLCANOES_ALL en frontend/index.html (filtro,
   no borrar la entrada, por G9), `git rm` de data/historia_34/ y data/sombra_34/ de los dos, prueba 34 a 32;
   revisar G9, vecinos.yaml y A.LOS_34; suite completa; anotar en experiments/_historia_34/TANDAS.md y
   tasks/DECISIONES_34_S187.md; PR; esperar «mergea #N». Si el contexto aprieta, delegarlo a un subagente
   con effort high y tope de disco 500 MB.
4. Tanda 3 terminada: relanzar rojos si hay; `bajar_trozos.sh <run> D:/vrp-trabajo/temporales/historia_34/tanda3/run1`;
   `BASE=D:/vrp-trabajo/temporales/historia_34/tanda3 WT=D:/vrp-trabajo/worktrees/s190-tanda3 RAMA=s190-historia34-tanda3 bash D:/vrp-trabajo/temporales/s187_tanda2/unir_tanda2.sh <run>`;
   0 huecos y marcas sólo `:true`; verificador limpio de otro modelo con effort high; PR (modelo: cuerpo de
   #1026) que anote D1; esperar «mergea #N»; `gh pr merge N --merge --match-head-commit <sha completo>`;
   aplicar con aplicar-reemplazo.yml (confirmacion=si, script=experiments/_historia_34/aplicar_historia_34.sh,
   pruebas=tests/test_historia_34.py tests/test_sombra_34_s172.py, tag=pre-historia-34-tanda3); verificar el
   commit en main; quitar el worktree; bitácora (`date -u` antes). Igual para 4 a 7.

Reglas duras: merges a main y A45 sólo con «mergea #N» de Nicolás; merge commit, nunca squash; H3 autoriza
aplicar cada tanda tras su merge, con tag y sólo con 0 huecos y 0 caídas a K; no volver a aplicar Putana ni
OlcaParuma; no despachar volcanes nuevos; sólo EARTHDATA_TOKEN; temporales y worktrees en D:\vrp-trabajo;
export MSYS_NO_PATHCONV=1; tope de 5 agentes y 2 procesos pesados; git add por archivo; nunca git stash;
nada de experiments/_s176_codex/; texto con rutas de Windows con Write a un .py, nunca heredoc ni sed. Si el
hook de contexto avisa: terminar el paso, matar vigilante y cadena por PID y COMPROBAR con ps que no queda
nada, /cierre, abrir S191 como sesión propia.
```
