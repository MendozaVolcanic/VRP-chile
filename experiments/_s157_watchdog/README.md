# S157: el reproc-watchdog juzga cada job y no repite avisos (arreglo 7 de AUDIT_S155)

## Qué pasaba

El workflow `.github/workflows/reproc-watchdog.yml` vigila cada hora los reprocesos y avisa en una
issue si uno falla o se cuelga. La auditoría S155 (F3-10, `docs/AUDIT_S155.md`, arreglo 7) midió
que llamaba «colgada» a una corrida por la **edad del run** (`created_at`, umbral 7 h), cuando el
techo de GitHub es de 6 h **por job**. Un reproceso por trozos de 178 jobs con `max-parallel: 8`
vive más de 30 h sin que nada esté colgado: el run 39125546355 (2026-10-18 12:01 a 2026-10-19
20:22 UTC) no tuvo ningún job sobre 2,86 h y salió «colgado» cada hora. Como el texto decía
«hace X h», cada comentario era distinto del anterior y la issue #824 juntó 28 comentarios en 4
días. El daño no es la molestia: ese ruido tapa la falla verdadera cuando llegue.

## Qué cambió

- **Colgado = un job `in_progress` cuyo `started_at` pasa las 7 h.** Los jobs se leen paginados
  (`github.paginate(listJobsForWorkflowRun)`). Un job en cola no cuenta, aunque la API le ponga
  `started_at` (el verificador lo vio en un run real). Se miran también las corridas en curso
  detrás de la última (dos trozos relanzados a la vez), con `per_page: 5`.
- **Estancada**: una corrida viva hace más de 72 h sin ningún job corriendo (huérfana o en cola
  eterna) se avisa. Recupera la cobertura que el criterio viejo daba por accidente, con un techo
  que no confunde la cola normal de `max-parallel` con un problema.
- **La ventana de 14 días se cuenta desde `run_started_at`** (el último intento), no desde
  `created_at`: un re-run de una corrida vieja ya no queda invisible.
- **Reintentos ante 502**: `retries: 3` en `actions/github-script@v7` (plugin-retry reintenta los
  5xx; confirmado por el verificador en el código fuente).
- **SIN DATO no es verde**: si la API de jobs no responde tras los reintentos, la corrida queda
  SIN DATO, la issue abierta no se cierra y el job de Actions queda en rojo. Ese SIN DATO no entra
  al texto del aviso (si entrara, un 502 intermitente lo haría alternar y repetir).
- **No repetir**: el texto ya no lleva edades sino fechas fijas (creación del run, arranque del
  job), lleva la marca `<!-- reproc-watchdog -->`, y se comenta sólo si difiere del último aviso
  escrito por `github-actions[bot]` con esa marca (o del cuerpo de la issue si no hay ninguno).
- El mensaje de cierre dice lo que de verdad mira: la última corrida de cada reproceso, los jobs y
  las corridas estancadas.

## Evidencia

| qué | dónde | resultado |
|---|---|---|
| Pruebas nuevas (funciones puras y el script entero con un GitHub simulado) | `tests/test_reproc_watchdog_por_job_s157.py` | 18 pruebas; junto con `tests/test_reproc_watchdog_vivos_s133.py`, 29 en verde |
| Caso real | `tests/datos_s157/watchdog_run_39125546355_jobs.json` (178 jobs bajados de la API; el verificador comprobó que coinciden con la API) | barrido hora a hora de la vida del run: 0 avisos; control positivo con un job forzado a colgado: «colgada» |
| Contra el código de `origin/main` | las mismas pruebas sobre el yml viejo | 11 de 14 fallan; la simulación reproduce el texto falso de #824 («lleva 25.6 h en `in_progress`») |
| Mutaciones (A110) | `mutaciones.py`, `mutaciones_salida.txt` | 23 de 23 atrapadas por aserción; el control M00 (sintaxis rota) sale CAIDA, no atrapada |
| Verificador con contexto limpio | `VERIFICADOR.md`, `casos_borde_verificador.py` | A1 a A7 CONFIRMADAS; H1, H2 (gravedad 2) y H4, H5, H6 corregidos; H3 cubierto con «estancada» |

`casos_borde_verificador.py` es el script del verificador tal como lo corrió, **sobre la versión
anterior a sus correcciones**: sus salidas `rerun_viejo`, `huerfano`, `cola_eterna` y `humano_cita`
describen el defecto que se corrigió después, no el estado final.

## Lo que queda abierto

- F3-07 en su forma original (`scripts/auto_audit_weekly.py` y `.github/workflows/audit-weekly.yml`:
  causa «S124» puesta sin medir, banda declarada distinta de la del código, issue semanal sin
  deduplicar) **no** se tocó acá: este arreglo aplica al watchdog la parte de deduplicar.
- A6 (que `github.paginate` aplana `{total_count, jobs}`) está confirmada por el código fuente de
  Octokit, no por una corrida real: el primer run del watchdog tras el merge no debe decir «sin
  dato de jobs».
- Previsión del verificador: tras cerrar #824, la falla del 2026-10-15 de `reproc-s151-ab-caja.yml`
  (dentro de la ventana hasta el 2026-10-29) abrirá **una** issue nueva, sin repetir.
