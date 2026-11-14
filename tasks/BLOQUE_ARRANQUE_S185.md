# Bloque de arranque S185 (cierre de S184, 2026-11-14 20:05 UTC)

S184 coordinó el loop desde la rama `loop/activo` como sesión dueña única, del 2026-11-14 16:59 al 20:05 UTC. Cerró
por contexto (pasó el 50 %). **La próxima sesión del loop es S185.** Ojo: la sesión «Gráficos por volcán como MIROVA:
primera tanda» (`local_cf79e659`) usa el prefijo `s184` en su rama (`claude/s184-graficos-como-mirova-0704e1`); no es
del loop.

**El estado se fijó con trabajo ajeno en curso:**
- la tanda de la historia de los 34 volcanes (sesión «Reemplazar la historia», `local_f37923b4`): run 43633062404,
  138 trozos desde main `dc0a1de3f` (ya con el arreglo de descarga), unas 11 a 13 horas, sin push;
- la sombra de los 34 (run 43628115933), que partió a las 18:42 UTC, antes del arreglo: puede fallar en runners de
  AWS us-west-2;
- la sombra código MIROVA (run de las 19:47 UTC, en cola), ya con el arreglo;
- la sesión de gráficos, que trabaja en su propio worktree y terminará en un PR para «mergea #N».

**Lo anterior.** `tasks/BLOQUE_ARRANQUE_S184.md` (cierre de S182) queda como histórico. La bitácora completa de S184
está en `tasks/LOOP_OBJETIVOS.md` §6, en las entradas «(S184)» del 2026-11-14 17:07 a 20:05 UTC.

## a. Todo en una pantalla

| Qué | Estado | Evidencia |
|---|---|---|
| Caja del cráter en Cordón Caulle VIIRS 750 (#999) | INTEGRADO | Merge commit `9ab98b121` (19:38:12 UTC), CI verde en `b7da74eb3`; ficha SDA v1.29 |
| Serie VIIRS 750 de PCC con la caja del cráter | REEMPLAZADA y PUBLICADA | 2025-02-15 a 2026-11-13: `aplicar-reemplazo.yml` run 43633201356, commit `0f92dcc4d`, tag `pre-s184-pcc-crater-historia`; 2.994 reemplazadas, 0 sin par. 2026-11-14: `nrt.yml` con `overwrite` (run 43633405344), commit `6882f28f1`. `chequeo_caja.py`: 2.997 de 2.997 con `crater`. Pages (run 43633693529) publica el 2026-10-21 05:48 con 0,345 MW (antes 10,1; MIROVA 0,36) |
| Efecto del reemplazo | MEDIDO y VERIFICADO | 64 de 2.994 cambian de potencia (50 suben, 14 bajan; 17 ganan detección, 10 la pierden; de 1 MW o más, 129 a 135). Las 50 que suben ganan un píxel en celdas del norte que `sens` dejaba fuera (50 de 50; 0 de 14 en las que bajan). `experiments/_s184_pcc_crater_aplicar/` (README, `efecto_reemplazo_salida.txt`). Verificador Sonnet, dos vueltas: CORRECTO |
| Falla de descarga `FileExistsError` | CAUSA DEMOSTRADA y ARREGLO INTEGRADO | Runners de GitHub en AWS us-west-2: earthaccess 0.17.0 (última para Python 3.11) baja por S3 y revienta. #1007 (merge `dc0a1de3f`, 19:34 UTC) fuerza HTTPS. Comprobado por S184 en el log del trozo 33: «Region: us-west-2», «Cloud: AWS», earthaccess-0.17.0 |
| Ficha SDA al día (#1008) | INTEGRADO | Merge `81e36eb85` (20:00 UTC): la fila v1.29 dice que la serie ya se reemplazó; texto original conservado |
| Sombras #998 y #1004 | ABIERTAS, deberían volver a verde | Las fallidas eran todas por la falla de descarga. Falta ver una corrida verde con el arreglo |
| Plazo MODIS | 19 de 29 protegidas, las 19 de Nevados de Chillán | Informe de la guardia MODIS del 2026-11-14 02:41 UTC; producción publica las 19; 0 candidatas a reversión. Reproducido con la referencia fresca de Mirova-v1 (tabla consolidada + OCR) en `D:\vrp-trabajo\temporales\s184\protegidas_modis2.py` |
| #973 | ABIERTO, se juzga el 11-16 | Se midió el 11-09 con el detector K, antes del reemplazo de la historia |
| Disco | 29 GB libres en C: y 42 GB en D: | `df -h` 20:00 UTC. Worktrees de S184 quitados (`wt_s182_pcc`, `wt_s184_main`, `wt_s184_ficha`) |

## b. Decisiones que espera el dueño

| # | Pregunta | Opciones | Recomendación |
|---|---|---|---|
| 1 | Escenas inválidas (0 MW guardadas por la vía) en `scripts/banco_paridad.py::cargar_nuestros` | filtrarlas / dejarlas | Filtrar, en un PR aparte con su nulo antes y después, porque el banco lo usan instrumentos sellados. #1005 ya las sacó del tablero y #1006 de la comparación; el banco es el último que las cuenta como «sin anomalía» |
| 2 | Numeración de la ficha SDA entre PR paralelos | numerar al abrir (hoy) / numerar al mergear | Numerar al mergear: hoy #999 tuvo que renumerarse dos veces (v1.27, v1.28, v1.29) por #1002, #1005 y #1006. El que mergea toma el número siguiente; hay un resolutor en `D:\vrp-trabajo\temporales\s184\resolver_ficha_n.py` |
| 3 | Seguimiento de la sesión «Comparar los 11 contra MIROVA»: la guardia K de VIIRS y la K del tag difieren en ~7 noches-satélite del 3 al 10-nov | investigar / dejar | Investigar en el loop (una tarde): el nulo sellado decía 0 diferencias |
| 4 | Mecanismo de reversión (decisión 4 de S182) | revert del PR / apagar el flag | Sin cambio desde S182: apagar el flag |
| 5 | Vigilante diario de «la vía calla y K también» | sí / no | Sin cambio: sí |
| 6 | «Código abierto» sin LICENSE; los 42 pasajes del paper | (de Nicolás) | Sin cambio |
| 7 | Rotar `EARTHDATA_TOKEN` | antes del 2026-11-27 | Hacerlo ya: si vence, se apaga el NRT |

## c. Lo aprendido

- **Regla general del workspace (reforzada, se volvió a romper tres veces hoy):** una ruta de Windows dentro de Python
  embebido en un heredoc de bash se corrompe (`\v` pasa a tabulación vertical, `\r` a retorno de carro, `\t` a
  tabulación). Y unas comillas invertidas dentro de una cadena de bash entre comillas dobles se ejecutan como
  comandos. Para escribir texto con rutas o comillas invertidas: herramienta Write a un `.py` y luego `python -I` sobre
  ese archivo. Ya estaba en `feedback_s180_lecciones.md`; ahora también en `feedback_s184_lecciones.md`.
- **Regla general del workspace:** para reproducir un conteo de un workflow, usa las mismas entradas que el workflow
  (aquí, la tabla y el OCR frescos de Mirova-v1); el snapshot del repo puede tener días de atraso.
  `feedback_s184_referencia_del_workflow.md`.
- **Regla general del workspace:** cuando una falla de Actions aparece «a veces», mira la cabecera del log del job
  («Region:», «Cloud:»). La misma imagen corre en nubes distintas y una librería puede cambiar de comportamiento según
  dónde cree estar.
- **Del proyecto:** `experiments/_s180_reemplazo_via/aplicar_via.py` no sirve cuando la serie publicada ya es de la vía
  (nunca pisa un record con marca de vía). Para un cambio dentro de la vía (por ejemplo, la caja), reemplazo por pasada
  más un chequeo directo del campo que cambia (`diag_codigo_mirova.roi`). Modelo: `experiments/_s184_pcc_crater_aplicar/`.
- **Del proyecto:** el NRT sólo reescribe una pasada existente si sube de `nrt` a `standard` o con `overwrite`. Para
  cubrir la cola entre el fin de un reproceso y el merge: `nrt.yml` con `profile`, `volcano`, `start`, `end` y
  `overwrite=true`, y después el chequeo.
- **Del proyecto:** la API de jobs de Actions puede dejar un job terminado como «queued» sin fecha de término. Antes de
  creerle, mira su log y su artefacto.

## d. Problemas abiertos e hipótesis

| Problema | Marca |
|---|---|
| #998 y #1004 vuelven a verde con #1007 | SOSPECHA: no hay todavía una corrida verde posterior al arreglo |
| Plazo MODIS: 19 de 29, se cumpliría hacia el 18 o 19-nov a ~2 por día | 19 CONFIRMADO (informe 02:41 UTC); la fecha es SOSPECHA |
| #973 fuera de banda; la auditoría del 11-16 es la primera sobre la vía | CONFIRMADO que se midió con K; el resultado del 11-16, SIN DATO |
| Guardia K de VIIRS contra K del tag, ~7 noches del 3 al 10-nov | SOSPECHA (lo informa otra sesión; S184 no lo midió) |
| Tanda de los 34 (run 43633062404) termina sin trozos rojos | SIN DATO (en curso) |
| El lector de la retrospectiva (`caja_v750_de`, `tests/test_leer_retro_s172.py`) conoce B4 y no B4c | CONFIRMADO en S182; sólo importa si se relee una retrospectiva con records nuevos de PCC |
| Chillán 2026-10-13 06:42 V750 10,94 MW sin fila de MIROVA | CONFIRMADO el hueco; que sea calor real es SOSPECHA |
| Los 6 valores OCR de PCC de 1,0 MW exactos en `objetivos_run_v750b.json` | SOSPECHA de valor por defecto |
| Quedan sin prueba reglas menores del aplicador de PCC (volcán de la unión, claves de nivel superior) | CONFIRMADO por el verificador; sin efecto en datos |

## e. Lo que ya está cerrado y no hay que rehacer

- #999 integrado y la serie VIIRS 750 de PCC entera con `crater` (2.997 de 2.997); no hay que reprocesar ni aplicar nada
  más de PCC. Los 34 trozos del run 43467764489 están completos; no se relanzan.
- La causa de `FileExistsError` está demostrada y arreglada (#1007). No es pasajera ni de los enlaces LAADS.
- #1003 está cerrado (era el intento 1 del reproceso de PCC).
- Las 50 pasadas que suben con `crater` están explicadas por la geometría (celdas del norte).
- La ficha SDA está al día hasta la v1.29 (#1008).
- El snapshot de la tabla consolidada de MIROVA no es un sincronizador roto: lo refresca la auditoría semanal.
- Esta sesión ya no cuelga de la cadena S178 a S182 en el sidebar (pedido de Nicolás).

## f. Prompt para la próxima sesión

```text
Sesión S185 de VRP Chile, dueña única del loop (respondes sólo a Nicolás). Carpeta
C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile, rama loop/activo. Hay otras
sesiones de Nicolás en este repo (gráficos como MIROVA, historia de los 34): no toques sus ramas.

1. Verifica antes de creer:
   - git fetch origin --prune; git status -sb; df -h /c /d. Con C: bajo 3 GB, para y avisa.
   - gh pr list --state open y gh issue list --state open. Avísale a Nicolás los issues de
     alerta abiertos antes de cualquier otra tarea.
   - ¿#998 y #1004 tienen una corrida verde posterior al 2026-11-14 19:34 UTC (merge de #1007)?
     gh run list -w sombra-codigo-mirova.yml -L 3 y lo mismo con sombra-34.yml. Si una falla,
     mira «Region:» en el log del job antes de concluir.
   - python -I D:\vrp-trabajo\temporales\s181_verif994\chequeo_post_nrt.py origin/main tiene
     que decir OK. Y git show origin/main:data/mirova_equivalent/PuyehueCordonCaulle.json >
     archivo temporal + python experiments/_s184_pcc_crater_aplicar/chequeo_caja.py <archivo>
     tiene que dar 0 (ninguna VIIRS 750 de PCC sin crater).
2. Lee CLAUDE.md, tasks/BLOQUE_ARRANQUE_S185.md y las entradas (S184) de
   tasks/LOOP_OBJETIVOS.md §6.
3. Trabajo, en orden:
   a. Plazo MODIS: lee data/audit_continuous/guardia_modis_latest.json (duracion); al llegar a
      29 protegidas, prepara el informe de cierre del plazo para Nicolás. Para listar por volcán
      usa la referencia fresca de Mirova-v1, como el workflow.
   b. Auditoría semanal del 11-16 (#973): primera sobre la vía; clasifica cada flag (A54) antes
      de proponer nada.
   c. Decisiones b.1 a b.3 del bloque: llévalas a Nicolás con su recomendación.
   d. Sigue la tanda de los 34 sólo si su sesión lo pide; no despaches en su grupo de
      concurrencia sin avisarle.
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
- Texto con rutas de Windows o comillas invertidas: escríbelo con Write a un .py, nunca
  dentro de un heredoc de bash.
- Ficha SDA: el número de versión se toma al mergear, no al abrir el PR.
- Español de Chile, sin guiones largos ni medios; rutas absolutas para Nicolás.
- Nombra la referencia de MIROVA leyendo el loader (tabla, OCR o ambos).
Si la sesión no alcanza: deja en la bitácora qué quedó a medias y cierra con /cierre al 50 % del
contexto; Nicolás autorizó que la sesión que cierra inicie la siguiente.
```
