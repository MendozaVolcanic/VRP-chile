# Bloque de arranque S184 (cierre de S182, 2026-11-14 17:00 UTC)

S182 coordinó el loop desde la rama `loop/activo` como sesión dueña única, del 2026-11-13 00:12 al 2026-11-14 17:00 UTC. Cerró por contexto. **La próxima sesión del loop es S184**: el número S183 ya lo usaron las sesiones del tablero, en #1002 (mergeado) y #1005 (abierto).

**El estado se fijó con trabajo en curso.**
- El reproceso de Cordón Caulle (run 43467764489, intento 2) tenía 3 trozos corriendo: el 23 (04-21 a 05-10), el 29 (08-19 a 09-07) y el 33 (10-17 a 11-05). El 34 ya pasó en el relanzamiento.
- La sesión «Diagnosticar FileExistsError en las descargas de NASA» (`local_b54b4ce8-a635-4cdf-8adb-7749a0545657`) recién empezaba. Trabaja en su propio worktree, cortado de `main`.
- Hay otras sesiones de Nicolás abiertas sobre el mismo repo: «Comparar los 11 contra MIROVA» (`local_ea0ac6ca`), la del tablero que abrió #1005 y «Reemplazar la historia» (`local_f37923b4`). No toques sus ramas.

**Lo anterior.** `tasks/BLOQUE_ARRANQUE_S182.md` (cierre de S181) queda como histórico. La bitácora completa de S182 está en `tasks/LOOP_OBJETIVOS.md` §6, en las entradas «(S182)» del 2026-11-13 00:12 al 2026-11-14 16:30 UTC.

## a. Todo en una pantalla

| Qué | Estado | Evidencia |
|---|---|---|
| Texto falso del modal (`frontend/index.html:544`) | INTEGRADO y PUBLICADO | #997, merge `11df97a2b` (2026-11-14 16:12 UTC); Pages run 43614347128; el sitio muestra «Estado al 2026-11-13». El selector F5' ya había salido en S180 |
| Cordón Caulle V750 2026-10-21 05:48 (10,1 contra 0,36 MW de MIROVA) | EXPLICADO y VERIFICADO | Lo causa la caja `sens`, no el port: con `crater` da 0,345 MW a 6,45 km. `experiments/_s182_pcc_crater/` en la rama de #999; 3 verificadores Sonnet |
| Caja del cráter en PCC (B4c) | PR #999 ABIERTO, CI verde, sin merge | Rama `claude/s182-pcc-crater` (`d6344e06e`), tag `pre-s182-pcc-crater` = `46b2d0b5e`. Analizador sellado de V750-B: 101/101 protegidas, E 29 contra 31, EMPATE contra B1. Ficha SDA v1.26 PROPUESTA |
| Reproceso de la historia VIIRS 750 de PCC con crater | 32 de 35 trozos OK; 3 en curso (intento 2) | run 43467764489. Las fallas del intento 1 fueron `FileExistsError` de descarga (23, 29, 33) y día parcial (34) |
| 522 pasadas V750 de borde que la vía agregó | MEDIDO | 499 son escenas inválidas guardadas como 0 MW (el `.m` da NaN); 23 son completas. No hay corte por ángulo de vista en K, en el `.m` ni en el port |
| Escenas inválidas (1.916 records con 0 MW) | MEDIDO y VERIFICADO | No se publican. Entran como `neg_limpio` en `scripts/banco_paridad.py` (246), lo que mejora en apariencia una milésima la tasa de publicación en negativos. #1005 (otra sesión) las saca del tablero |
| Guardia K de VIIRS | VERDE | run 43356545581: 4 de 29 protegidas vistas, 0 calladas por la vía |
| Disco | 31 GB libres en C: y 41 GB en D: | 37 worktrees quitados (antes eran 14 y 9,7 GB). Respaldo en `D:\vrp-trabajo\papelera_s182\`. Quedan 6 worktrees |
| Falla de descarga `FileExistsError` | SIN DIAGNOSTICAR, sesión aparte en curso | Tumba #998 (sombra código MIROVA), #1004 (sombra de los 34) y los trozos del reproceso |

## b. Decisiones que espera el dueño

| # | Pregunta | Opciones | Recomendación |
|---|---|---|---|
| 1 | Reemplazar la serie VIIRS 750 de PCC con el reproceso crater y mergear #999 | aplicar con #999 / sólo #999 sin reemplazo / esperar | Cuando estén los 35 trozos: script de aplicación sólo para PCC VIIRS 750, verificador, y después «mergea #999» y el sí a `data/` juntos, para que la serie no quede con dos cajas |
| 2 | Arreglo de la falla de descarga en `pipeline/fetch.py` | A45 cuando haya causa demostrada | Sí, con la causa demostrada y la prueba en rojo antes del arreglo. Lo pide la sesión de diagnóstico |
| 3 | Escenas inválidas en `scripts/banco_paridad.py` (`cargar_nuestros`, l. 302-343) | filtrarlas / dejarlas | Filtrar, en un PR aparte con su nulo antes y después (el banco lo usan instrumentos sellados). Es la misma idea que #1005 aplica al tablero: coordinar con esa sesión |
| 4 | Mecanismo de reversión (decisión 4 de S182) | revert del PR / apagar el flag | Apagar el flag. Tras el reemplazo, revertir también exige restaurar la historia K desde el tag |
| 5 | Vigilante diario de «la vía calla y K también» (decisión 5 de S182) | sí / no | Sí |
| 6 | «Código abierto» sin LICENSE en los mazos; los 42 pasajes del paper | (de Nicolás) | Sin cambio desde S182 |
| 7 | Rotar `EARTHDATA_TOKEN` | antes del 2026-11-27 | Hacerlo ya: si vence, se apaga el NRT |

## c. Lo aprendido

- **Regla general del workspace:** cada worktree trae su propia copia de `data/` (~1,3 GB). Había 44 que sumaban 53,6 GB. Quita el worktree cuando su PR se mergea. Antes de quitar uno, revisa:
  - `git status --ignored`;
  - commits que sólo existen en local;
  - **`list_sessions` justo antes de cada remove**: en S182 se borró la carpeta de una sesión que Nicolás estaba retomando en ese momento;
  - los PR abiertos de esa rama.

  Memoria: `feedback_s182_worktrees_acumulados.md`.
- **Del proyecto:** para medir una opción que no estaba sellada, corre el analizador sellado sin modificar el archivo, parcheando sólo en memoria la función que define el brazo, y ajusta el control que el cambio rompe por construcción (aquí, el control negativo restringido a Tupungatito). Así salen números comparables con la lectura sellada.
- **Del proyecto:** en el port, BOX 0 se evalúa con el umbral conservador, igual que BOX 1 (también en el `.m`). Poner «0» no excluye nada de la búsqueda.
- **Del proyecto:** un cambio intencional en `grillas_mirova.yaml` rompe dos guardias por construcción: `test_sombra_34_s172` (bytes del bloque de los 11) y `vigilancia_guardia_viirs.volcanes_sens`. Hay que actualizarlas en el mismo PR.
- **Del proyecto:** para leer bien una falla de Actions, baja el log completo del job (`gh api .../jobs/<id>/logs`) y cuenta por día. Una lectura rápida concluyó «sólo el primer día», pero en el trozo 33 fallaron todos los días, con 0 descargas exitosas.

## d. Problemas abiertos e hipótesis

| Problema | Marca |
|---|---|
| `FileExistsError` de `earthaccess` al renombrar `partial_*`; en el trozo 33 fallan todas las descargas de todos los días (`D:\vrp-trabajo\temporales\s182\job33.log`) | CONFIRMADO el síntoma |
| Causa: en Linux, un rename con errno 17 indica que el destino es un directorio no vacío, quizá por enlaces de descarga sin nombre de archivo | SOSPECHA (los enlaces CMR que se miraron sí tienen nombre) |
| MODIS ya publica en CMR la colección 007 (.nc) junto a la 061 (.hdf) | CONFIRMADO el hecho; si tiene que ver con la falla es SOSPECHA |
| Qué ROI usa MIROVA de verdad en Cordón Caulle | SIN DATO |
| Chillán 2026-10-13 06:42 V750 10,94 MW: MIROVA no tiene ninguna fila VIIRS de ningún volcán ese día antes de las 17:18 UTC | CONFIRMADO el hueco; que sea calor real es SOSPECHA |
| El lector de la retrospectiva (`caja_v750_de`, `tests/test_leer_retro_s172.py`) conoce B4 y no B4c | CONFIRMADO; sólo importa si se vuelve a leer una retrospectiva con records nuevos de PCC |
| Los 6 valores OCR de PCC en `objetivos_run_v750b.json` valen exactamente 1,0 MW | SOSPECHA de un valor por defecto |
| #973: auditoría semanal fuera de banda desde el 2026-11-09; la próxima es el 11-16 | ABIERTO |
| Plazo MODIS: 17 de 29 protegidas, cierra hacia el 19 o 20 de noviembre | ABIERTO |

## e. Lo que ya está cerrado y no hay que rehacer

- #997 integrado y publicado; el selector F5' ya había salido en S180. No hay que volver a tocar `index.html:544`.
- El caso de los 10,1 MW de Cordón Caulle está explicado por la caja `sens`; el port coincide con el `.m`.
- Las 522 pasadas de borde no se deben a un corte por ángulo de vista. Están medidas.
- Las escenas inválidas no cambian el aviso de frescura del tablero (no hay huecos reales mayores de 30 h). Su efecto en la paridad está medido.
- B4c está medido con el analizador sellado. No hace falta repetirlo antes del merge de #999.
- La limpieza de disco está hecha. Quedan 6 worktrees: `wt_s182_pcc`, `s180-reemplazo`, `relaxed-almeida-d17378`, `s178-955`, `s178-plan` y el restaurado `s180-tablero-por-sensor-3da0a8`.
- #995 cerrado.

## f. Prompt para la próxima sesión

```text
Sesión S184 de VRP Chile, dueña única del loop (respondes sólo a Nicolás; S183 lo usaron las
sesiones del tablero). Carpeta C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile,
rama loop/activo. Hay otras sesiones de Nicolás abiertas en este repo: no toques sus ramas.

1. Verifica antes de creer:
   - git fetch origin --prune; git status -sb; df -h /c /d. Con C: bajo 3 GB, para y avisa.
   - gh pr list --state open y gh issue list --state open. Avísale a Nicolás los issues de
     alerta abiertos antes de cualquier otra tarea.
   - gh run view 43467764489: ¿terminaron los trozos 23, 29 y 33 del reproceso de PCC
     (intento 2)? Si alguno volvió a fallar con FileExistsError, no lo relances otra vez.
   - Lee la nota de la sesión «Diagnosticar FileExistsError en las descargas de NASA»
     (local_b54b4ce8-a635-4cdf-8adb-7749a0545657) con list_sessions {"linked": true}.
   - python -I D:\vrp-trabajo\temporales\s181_verif994\chequeo_post_nrt.py origin/main tiene
     que decir OK.
2. Lee CLAUDE.md, tasks/BLOQUE_ARRANQUE_S184.md y las entradas (S182) de
   tasks/LOOP_OBJETIVOS.md §6.
3. Trabajo, en orden:
   a. Con los 35 trozos completos: une los artefactos del reproceso
      (experiments/_s180_reemplazo_via/unir_trozos.py como modelo) y escribe un script de
      aplicación SÓLO para VIIRS 750 de PuyehueCordonCaulle, en la rama de #999. Lo corre
      aplicar-reemplazo.yml. Que lo revise un verificador limpio de otro modelo. Después pide a
      Nicolás «mergea #999» y el sí para aplicar a data/.
   b. Sigue la sesión de diagnóstico de descargas; cuando tenga la causa demostrada, lleva a
      Nicolás su pedido de A45.
   c. Plazo MODIS (cierra hacia el 19 o 20 de noviembre): lista de las 29 protegidas por
      volcán; auditoría semanal del 11-16 (#973).
   d. Escenas inválidas en scripts/banco_paridad.py: coordina con #1005 antes de abrir un PR.
Reglas duras:
- Los merges a main, toda A45 nueva y aplicar a data/ son sólo de Nicolás, con «mergea #N».
- Merge commit con gh pr merge --merge --match-head-commit; nunca squash.
- Nada en pipeline/, data/ ni frontend/ sin tag y su sí.
- Sólo EARTHDATA_TOKEN.
- Verificador limpio de otro modelo antes de aceptar un resultado; effort high explícito.
- Temporales y worktrees en D:\vrp-trabajo; export MSYS_NO_PATHCONV=1 y rutas D:/ en
  git worktree.
- Máximo 5 agentes y 2 procesos pesados; tope de 500 MB por agente.
- Quita tu worktree al mergear, revisando list_sessions justo antes.
- git add por archivo; nunca git stash; nada de experiments/_s176_codex/.
- date -u antes de cada encabezado de bitácora.
- Rutas de Windows en Python como string crudo.
- Español de Chile, sin guiones largos ni medios; rutas absolutas para Nicolás.
- Nombra la referencia de MIROVA leyendo el loader (tabla, OCR o ambos).
Si la sesión no alcanza: deja en la bitácora qué quedó a medias y cierra con /cierre al 50 % del
contexto; Nicolás autorizó que la sesión que cierra inicie la siguiente.
```
