# Bloque de arranque S189 (escrito por S188, 2026-11-17 00:10 UTC)

Anterior: `tasks/BLOQUE_ARRANQUE_S187.md` (histórico, no se toca). S188 fue corta: cerró por el aviso de
contexto (152 mil tokens) a las 00:06 UTC, apenas Nicolás decidió D1.

Estado fijado SIN trabajo local en vuelo: S188 detuvo su vigilante y su `cadena_4a7.sh` a las 00:07 UTC para
que S189 sea la única dueña. Lo único que sigue corriendo es el run de Actions de la tanda 3.

## a. Todo en una pantalla

| Qué | Estado | Evidencia |
|---|---|---|
| Tanda 3 (DescabezadoGrande, CerroAzulQuizapu, LagunaDelMaule, NevadoDeLongavi, Antuco) | CORRIENDO | run 43906817147: 104 de 165 verdes, 0 rojos a las 00:05 UTC; fin estimado 04 a 05 UTC del 17 |
| Cadena 4 a 7 | DETENIDA (no despachó nada) | `D:\vrp-trabajo\temporales\s187_tanda2\cadena_4a7.log` vacío; S189 la relanza |
| Tandas 1 y 2 | APLICADAS en main | `bec44eb16` y `43ac1c5e6` (tag `pre-historia-34-tanda2` = `33c6796f9`) |
| Auditoría semanal 2026-11-16 | VERDE | run 43938585128; copia `D:\vrp-trabajo\temporales\s188\latest_1116.json` |
| #973 | CERRADO | comentario con la tabla de los tres motivos resueltos |
| D1 | DECIDIDA por Nicolás, falta ejecutarla | 2026-11-17 00:05 UTC: «vamos con los 43 de la RNVV por mientras. continua con todo» |
| Bitácora | al día hasta 19:55 UTC del 16 | `b4d9140c0` en `loop/activo`; la entrada de D1 va en el commit de este bloque |

## b. Decisiones que espera Nicolás

Cruce por distancia de los 45 de `volcanoes.yaml` con los 43 de la RNVV
(`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\WEBRNVV\fichas_nuevas_json\_lista.json`), script
`D:\vrp-trabajo\temporales\s188\cruce_rnvv.py` (CONFIRMADO, corrido en S188):

| # | Pregunta | Opciones | Recomendación |
|---|---|---|---|
| 1 | Putana y Olca-Paruma no tienen entrada en la RNVV y ya están aplicados en `data/historia_34/` (tandas 2 y 1). ¿Cómo se retiran? | (a) PR que quita sólo `Putana.json` y `OlcaParuma.json` de `data/historia_34/` y los saca de la sombra y el tablero; (b) volver al tag de cada tanda (borra también a los otros 4 de cada una) | (a), guardando los resultados en `D:\vrp-trabajo\temporales\` para reponerlos si D1 cambia («por mientras») |
| 2 | La RNVV agrupa Descabezado Grande y Cerro Azul-Quizapu en «Grupo Descabezados» (7 km) y no lista Tolhuaca aparte (queda a 9,2 km de Lonquimay). ¿Siguen como volcanes propios? | (a) seguir con los dos de cada par; (b) dejar sólo el de la ficha RNVV | (a): son volcanes distintos y la ficha RNVV los cubre; el doble foco de Descabezado y Cerro Azul se resuelve con N2/«también visto desde», no sacando uno |
| 3 | La RNVV trae Tatara-San Pedro, Cay y Hornopirén, que no tenemos (tenemos MacaCay y YateHornopiren juntos). ¿Se agregan? | (a) agregar después de la tanda 7; (b) no por ahora | (b) por ahora: cada uno pide geometría y radio nuevos; anotarlo como pendiente |
| 4 | Lastarria no está en la RNVV pero es Tier A de MIROVA. | (a) se queda; (b) sale | (a): es de los 11 de paridad, fuera del alcance de los 34 |
| 5 | Siguen abiertas N1, D5, N2, D13, D15 | ver `tasks/DECISIONES_34_S187.md` §2 | las recomendaciones de esa hoja |

Mientras Nicolás no conteste 1 a 3, la cadena puede seguir procesando (sólo cuesta minutos de runner); lo que
se decide es qué se APLICA. No aplicar Putana ni Olca-Paruma de nuevo, y no despachar volcanes nuevos.

## c. Lo aprendido

- El aviso de contexto saltó a los 152 mil tokens con muy poco trabajo hecho: el prompt base y los CLAUDE.md
  pesan mucho. Regla general del workspace: abrir la sesión ya sabiendo que el margen útil es corto; leer
  sólo lo justo (grep, nunca archivos enteros) y no listar sesiones. Va a memoria (feedback S187 ampliado).
- Antes de cerrar una sesión que lanzó un script de despacho en cadena, detenerlo: dos cadenas vivas en dos
  sesiones despacharían la misma tanda dos veces (ambas esperan «0 corridas vivas» y disparan a la vez).
  Propio del proyecto; va a memoria.
- «Los 43 de la RNVV» no es un subconjunto de nuestros 45: hay 3 sin par, 2 fusiones y 3 que no tenemos.
  Una decisión de lista se cruza por coordenadas antes de ejecutarla.

## d. Problemas abiertos e hipótesis

- CONFIRMADO: la tanda 3 iba 104 de 165 sin rojos a las 00:05 UTC.
- CONFIRMADO: la cadena no despachó nada antes de detenerse (log vacío; seguía esperando la tanda 3).
- SOSPECHA: `cadena_4a7.sh` da un falso «DETENIDO» si `gh run view` falla por la red (ROJOS queda vacío y se
  compara con «0»). Si sale con exit 2, mirar primero si el run de verdad tiene rojos.
- SOSPECHA: la sombra de los 34 y el tablero siguen mostrando Putana y Olca-Paruma; no lo revisé en S188.

## e. Ya cerrado, no rehacer

- #973 cerrado con evidencia; la auditoría del 11-16 no necesita más comparación.
- Tandas 1 y 2 aplicadas y verificadas por S187 (29.866 nuevos en la 2, igual al ensayo).
- La pregunta «¿qué quiso decir con 43?» está respondida: la lista de la RNVV.

## f. Prompt para S189

```
Eres S189 de VRP Chile, dueña única del loop (rama loop/activo en
C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile). Español de Chile, sin guiones largos ni
medios, rutas absolutas. El margen de contexto es corto: grep en vez de leer archivos enteros, nada de
list_sessions salvo necesidad, nunca leer tasks/LOOP_OBJETIVOS.md entero.

0. Verificar antes de creer: `git fetch origin --prune`, `git status -sb` (rama loop/activo),
   `git rev-parse HEAD` contra `git ls-remote origin -h refs/heads/loop/activo`; `date -u`;
   `gh run view 43906817147 --json status,conclusion` y `gh run list -w reproc-historia-via.yml --limit 3`
   (confirmar que no hay otra cadena despachando: S188 detuvo la suya a las 00:07 UTC del 17).
1. Leer tasks/BLOQUE_ARRANQUE_S189.md entero (es corto) y la memoria project_s188_estado.md.
2. Lanzar en segundo plano `bash D:/vrp-trabajo/temporales/s187_tanda2/vigilar_run.sh 43906817147` (si la
   tanda 3 sigue viva) y `bash D:/vrp-trabajo/temporales/s187_tanda2/cadena_4a7.sh`. NO cadena_3a7.sh.
3. Preguntar a Nicolás las decisiones 1 a 3 del §b del bloque (Putana y Olca-Paruma, pares fusionados,
   volcanes que faltan), con la recomendación de cada una.
4. Tanda 3 terminada: relanzar rojos si hay; `bajar_trozos.sh <run> D:/vrp-trabajo/temporales/historia_34/tanda3/run1`;
   `BASE=D:/vrp-trabajo/temporales/historia_34/tanda3 WT=D:/vrp-trabajo/worktrees/s189-tanda3 RAMA=s189-historia34-tanda3 bash D:/vrp-trabajo/temporales/s187_tanda2/unir_tanda2.sh <run>`;
   exigir 0 huecos y marcas sólo `:true`; verificador limpio de otro modelo con effort high; PR con los
   .json.gz, el informe y TANDAS.md al día (modelo: cuerpo de #1026) que anote la decisión D1;
   esperar «mergea #N»; `gh pr merge N --merge --match-head-commit <sha completo>`; aplicar con
   aplicar-reemplazo.yml (confirmacion=si, script=experiments/_historia_34/aplicar_historia_34.sh,
   pruebas=tests/test_historia_34.py tests/test_sombra_34_s172.py, tag=pre-historia-34-tanda3);
   verificar el commit en main; quitar el worktree; bitácora (`date -u` antes). Igual para 4 a 7.
5. Ejecutar lo que Nicolás decida sobre Putana y Olca-Paruma (PR aparte, A45 si toca pipeline).

Reglas duras: merges a main y A45 sólo con «mergea #N» de Nicolás; merge commit, nunca squash; H3 autoriza
aplicar cada tanda tras su merge, con tag y sólo con 0 huecos y 0 caídas a K; sólo EARTHDATA_TOKEN;
temporales y worktrees en D:\vrp-trabajo; export MSYS_NO_PATHCONV=1; tope de 5 agentes y 2 procesos
pesados; git add por archivo; nunca git stash; nada de experiments/_s176_codex/; texto con rutas de Windows
se escribe con Write a un .py, nunca heredoc ni sed; red local cortada con api.github.com: scripts con
reintentos. Si el hook de contexto avisa: terminar el paso, /cierre, abrir S190 como sesión propia y
DETENER antes los procesos en segundo plano propios (vigilante y cadena).
```
