# Bloque de arranque S181 (cierre de S180, 2026-11-12 04:42 UTC)

S180 coordinó el loop desde la rama `loop/activo`. Cerró por contexto (lo habían compactado una vez) a pedido de Nicolás:
«has lo que recomiendes en la siguiente sesion abrela tu mismo, que no sea hija de estas».

**El estado se fijó con trabajo en curso.**
- El reproceso de Tupungatito (`reproc-historia-via.yml`, run 43146587816) seguía `in_progress` a las 04:42 UTC. Lo
  espera un vigía en segundo plano de la sesión «Reemplazar la historia» (`local_f37923b4-e8f2-4ba9-9fe2-d9b6a6739563`,
  worktree `D:\vrp-trabajo\worktrees\s180-reemplazo`).
- La sesión «Rediseño del tablero» (`local_ad53d287-3e01-4a6e-9548-807d57866a84`) figuraba corriendo a las 04:42 UTC,
  sin pedido de S180. Su PR #986 ya está integrado.
- En S180 no queda ningún agente ni proceso local vivo.

Lo anterior: `tasks/BLOQUE_ARRANQUE_S180.md` (cierre de S179) queda como histórico. La bitácora completa de S180 está en
`tasks/LOOP_OBJETIVOS.md` §6, en las entradas «(S180)» de 2026-11-11 09:28 a 2026-11-12 04:40 UTC.

## a. Todo en una pantalla

| Qué | Estado | Evidencia |
|---|---|---|
| **Vía «código MIROVA» en VIIRS 375** (#974) | ENCENDIDA. Excepción explícita a §5: se encendió con 1 de 3 noches de guardia («si pero publiquemos todo con la via nueva») | merge `e23054dcb`, 2026-11-11 13:09 UTC, tag `pre-s180-b1-encendido` |
| **Vía en VIIRS 750** (#983, B2) | ENCENDIDA | merge `9a6cf976d`, 13:22 UTC, tags `pre-s180-b2-comentario` y `pre-s180-b2-encendido` |
| Primera corrida del NRT con las tres vías | VERDE | run 43030686918. Chillán 2026-11-11 06:54 UTC: VIIRS 375 pasa de 8,350 MW con K a 31,889 MW con la vía |
| Tablero por sensor (tarjeta mínima y página por volcán y sensor) | EN MAIN Y PUBLICADO | #986, merge `2b29405b2`, Pages 43082026810; revisado en el navegador |
| La vía queda fuera del Núcleo F5' | EN MAIN Y PUBLICADO | #988, merge `11509852a`, Pages 43105335430. En el sitio, Chillán 06:54 con la vía da 31,889 MW con el núcleo en null; K sigue usando su núcleo |
| Código del reemplazo de la historia (#987) | EN MAIN, **nada aplicado a `data/`** | merge `fa90366e8`, 2026-11-12 03:11 UTC. Tramo VIIRS del 10 y 11-11 relanzado y en verde (run 43146594080, 11 de 11). Tupungatito corriendo |
| Vigilancia de la sombra ciega (#989) | ARREGLADA | #991, merge `352a16f17`. Run 43156018354: VERDE, 0 avisos, `sensores_k: []`. #989 y #990 cerrados |
| Guardia K de VIIRS | 2 noches verdes desde el arreglo | runs 42929475700 (11-11 00:12 UTC) y 43135861587 (11-12 01:38 UTC), los dos success con 11 de 11 jobs. Detalle sin leer |
| Issues abiertos | #973 (auto-audit fuera de banda, 11-09), #943 (Suomi NPP, informativo), #813 (alertas diurnas, decisión de Nicolás) | `gh issue list --state open` |
| PR abiertos | #981, #980, #955, #913, todos en borrador y sin tocar en S180. #975 figura integrado porque quedó dentro de #983 | `gh pr list --state open` |
| Disco | C: 7,8 GB libres; D: 16 GB libres | `df -h`, 04:42 UTC |

## b. Decisiones que espera el dueño

| # | Pregunta | Opciones | Recomendación |
|---|---|---|---|
| 1 | Aplicar el reemplazo de la historia a `data/` | sí con tag, o esperar | Sí, pero cuando termine Tupungatito y **después** de comprobar el punto 4 del resumen de `docs/AUDIT_S179.md`: que el reemplazo no deje ciegas las guardias (sus controles bajaban de 167 y 223 pares a 0) y que la fecha de encendido de VIIRS siga siendo el 2026-11-11, no el mínimo de `processed_utc`. Hoy esto es SOSPECHA abierta (ver d) |
| 2 | Quitar el selector «Cluster / Núcleo F5'» del tablero | quitarlo o dejarlo | Quitarlo cuando la historia esté en la vía: el núcleo sólo tiene sentido para K |
| 3 | Decisión 5 de `docs/AUDIT_S179.md`: mecanismo de reversión | revert del PR o apagar el flag | Apagar el flag como camino principal. Revertir el PR de B1 con B2 adentro choca en la ficha y en 8 pruebas |
| 4 | Decisión 7: vigilar «la vía calla y K también» | vigilante diario o audit semanal | Vigilante diario, sobre todo ahora que la sombra de K quedó en reposo (ver c) |
| 5 | Decisión 8: tres decisiones sin frase registrada | #937, #972, fila 4 de VIIRS 750 | Que Nicolás confirme o rechace cada una en una línea |
| 6 | Cierre del plazo de MODIS (cerca del 11-19 o 11-20) | dejar la vía o revertir | Decidir con la lista de las 29 en mano. Son todas de Chillán, así que «29 de 29» no prueba nada general |

## c. Lo aprendido

Va a la memoria del proyecto en `feedback_s180_lecciones.md`.
- **REGLA GENERAL: `x or DEFAULT` confunde «vacío» con «no me dijeron».** En `scripts/vigilancia_sombra.py`, una lista
  vacía de sensores en K (los tres con la vía) volvía a los tres sensores y dejaba la vigilancia ciega (#989). Cuando
  vacío es un valor con sentido, usar `DEFAULT if x is None else x`.
- **Una vigilancia que pierde su objeto da VERDE.** Con ningún sensor en K, la sombra de K ya no tiene qué comparar. Su
  VERDE quiere decir «no hay K», no «K no pierde». Al apagar un detector en producción hay que revisar qué vigilancias
  lo tenían de objeto y decir qué vigila ahora la vía.
- **REGLA GENERAL (repetida): rutas de Windows dentro de un texto de Python.** Dos veces en S180 un `D:\vrp-...` escrito
  en un string normal (heredoc a `python -`) se volvió `D:<tab vertical>rp-trabajo<tab>mp`, en el cuerpo de un PR y en
  la bitácora. Se cazó leyendo lo publicado. Escribir esas rutas en un string crudo o con barras normales, y releer lo
  publicado.
- Un PR cuya rama quedó dentro de otro que se integró aparece en GitHub como integrado (#975 dentro de #983). No hay que
  cerrarlo.

## d. Problemas abiertos e hipótesis

| Problema | Marca | Nota |
|---|---|---|
| El reemplazo de la historia podría dejar ciegas las guardias o correr la fecha de encendido de VIIRS (punto 4 del resumen de `docs/AUDIT_S179.md`) | SOSPECHA | En el cuerpo de #987 no encontré mención de las guardias. `aplicar_via.py` habla de «corte en el encendido» y hereda `first_processed_utc`. Comprobarlo antes del sí de la decisión 1 |
| En K, Chillán 2026-11-11 05:12 UTC tiene `f5_core_vrp_mw` 13,41 MW y cúmulo 6,69 MW: el núcleo del pipeline supera al cúmulo | CONFIRMADO (leído en el sitio) | Pierde relevancia con el reemplazo; no se tocó |
| Con `?volcano=` de un nombre desconocido, el tablero cae al primer volcán (Taapaca) | CONFIRMADO | Menor |
| La sombra de K queda en reposo: no vigila nada de producción | CONFIRMADO | La pérdida de la vía la vigilan las guardias K de MODIS y VIIRS |
| Qué hacía la sesión del tablero «corriendo» a las 04:42 UTC | SIN DATO | No la lanzó S180 |

## e. Lo que ya está cerrado y no hay que rehacer

- El encendido de VIIRS 375 y 750 está hecho y la primera corrida del NRT salió verde. No hay que repetir el «¿enciendo?».
- La vía queda fuera del Núcleo F5' (#988).
- El tablero por sensor (#986) está terminado; su sesión no tiene pendientes.
- La vigilancia ciega #989 quedó arreglada (#991), y #990 era el tramo del día incompleto, ya relanzado.
- #968, #969, #915 y #936 se cerraron el 11-11 con «Sí, ciérralos». #975 quedó integrado dentro de #983.
- La guardia K de VIIRS no hay que «esperar» para encender: la excepción ya se tomó. Sigue corriendo de noche, sin
  publicarse.

## f. Prompt para la próxima sesión

```
Sesión S181 de VRP Chile (coordinadora del loop). Carpeta:
C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile, rama loop/activo. Única dueña del loop.
Las tres vías «código MIROVA» (MODIS, VIIRS 375 y VIIRS 750) se publican desde el 2026-11-11. Lo que falta es reemplazar
la historia con la vía (código en main por #987, nada aplicado a data/) y las decisiones de la sección b.

1. Verifica antes de creer: date -u; git fetch origin --prune; git status -sb; git rev-parse HEAD contra
   git ls-remote origin -h refs/heads/loop/activo (el commit del cierre de S180 o posterior);
   gh run list --workflow reproc-historia-via.yml --limit 3 (¿terminó Tupungatito, run 43146587816?);
   gh run list --workflow guardia-k-viirs.yml --limit 3; gh run list --workflow vigilancia-sombra.yml --limit 2;
   gh issue list --state open; gh pr list --state open; df -h /c /d; get_usage.
   Sesiones de S180 que pueden seguir vivas: «Reemplazar la historia» (local_f37923b4-e8f2-4ba9-9fe2-d9b6a6739563,
   worktree D:\vrp-trabajo\worktrees\s180-reemplazo) y «Rediseño del tablero» (local_ad53d287-3e01-4a6e-9548-807d57866a84).
   No las retomes ni les escribas sin preguntarle a Nicolás: tú eres la dueña del loop.
2. Lee: CLAUDE.md; tasks/BLOQUE_ARRANQUE_S181.md entero; las entradas (S180) de la bitácora §6 de tasks/LOOP_OBJETIVOS.md;
   docs/AUDIT_S179.md §1 punto 4 y las decisiones 5 a 8.
3. Avísale a Nicolás del issue #973 y de los demás abiertos, y pídele las decisiones de la sección b con su recomendación.
4. Trabajo en este orden:
   a. Comprueba la SOSPECHA de la sección d: que aplicar el reemplazo no deje ciegas las guardias (controles de 167 y 223
      pares) ni corra la fecha de encendido de VIIRS. Si lo hace, arréglalo en un PR antes de aplicar.
   b. Cuando Tupungatito esté y la sospecha esté despejada: muéstrale a Nicolás qué cambia y aplica a data/ con tag y su
      sí (A45). Comprueba el tablero publicado (regla de publicación).
   c. Después: propón quitar el selector Cluster / Núcleo F5'.
   d. Lee el detalle de la guardia K de VIIRS de las noches desde el 11-11 y anótalo en la bitácora.
   e. Auditoría semanal del 11-16 (#973) y cierre del plazo de MODIS hacia el 11-19 o 11-20.

Reglas duras: los merges a main, toda A45 nueva y aplicar a data/ son sólo de Nicolás, con la frase «mergea #N» en tu
conversación (el clasificador bloquea frases indirectas); gh pr merge --merge --match-head-commit (merge commit, nunca
squash, para que la reversión sea git revert -m 1). Nada en pipeline/, data/ ni frontend/ sin tag y sí de Nicolás (A45).
Sólo EARTHDATA_TOKEN (A71); ninguna llamada a NASA desde verificadores; verificador limpio de otro modelo antes de aceptar
un resultado; effort high explícito y carpeta temporal propia (en D:); máximo 5 agentes y 2 procesos pesados locales;
tope de 500 MB por agente, sin git init, git add del árbol ni copias del árbol; parada bajo 3 GB libres en C: o D:
(C: tiene 7,8 GB: worktrees y temporales en D:\vrp-trabajo); git add por archivo; nunca git stash; no incluyas archivos
de experiments/_s176_codex/; date -u antes de cada encabezado de bitácora; un PR sin checks no es verde;
export MSYS_NO_PATHCONV=1 en git show; rutas de Windows en Python siempre como string crudo (en S180 se rompieron dos
veces dentro de un heredoc) y relee lo publicado; español de Chile con tú y sin guiones largos ni medios; rutas
absolutas completas para Nicolás.

Si la sesión no alcanza: deja el estado del reemplazo (aplicado o no, con qué tag) y la guardia anotados en la bitácora,
y cierra con /cierre al 50 % del contexto.
```
