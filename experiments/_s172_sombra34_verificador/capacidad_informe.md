# Capacidad del NRT para 45 volcanes (S172)

Medido el 2026-11-02 00:27 UTC (hora del servidor GitHub, `Date` de `gh api -i`). Código leído en `origin/main`
`14fb62030a18` (2026-11-01 23:34 UTC). Sólo lectura: no se despachó nada ni se tocó el repo. Carpeta de trabajo:
`D:\vrp-trabajo\temporales\s172_capacidad_nrt\`.

## Conclusión (una línea)

**Cabe con cambios:** a 45 jobs con el `max-parallel: 8` actual NO cabe (pared de 104 min, p95 110, contra un ciclo
horario de 60 min en las horas de despacho y 120 min del cron); cabe con `max-parallel: 20` (pared 46 a 50 min, p95 50
a 55, margen de 5 a 10 min contra los 60) más editar las dos listas `contains(fromJson(...))` de `nrt.yml`, o mejor con
los 34 en un workflow aparte; el límite de 50 min por paso no es el problema (paso máximo observado 26,7 min).

## Tabla resumen

| Pregunta | Dato | Denominador y ventana | Origen |
|---|---|---|---|
| Matriz hoy | 11 Tier A escritos a mano en `nrt.yml`; `max-parallel: 8`; job 80 min; paso 50 min; grupo `push-main` (`cancel-in-progress: false`) | `nrt.yml` de `origin/main` | leído |
| Job de volcán, Tier A, hoy | mediana 16,7 min, p95 22,0, máx 28,4 | 429 jobs, 39 corridas verdes, 2026-10-30 07:10 a 2026-11-01 22:16 UTC | `gh run view --json jobs` |
| Paso del pipeline, Tier A, hoy | mediana 15,2 min, p95 20,5, máx 26,7 | los mismos 429 jobs | ídem |
| Pared de una corrida de 11 jobs | mediana 32,6 min, p95 38,5, máx 40,3 | 39 corridas (primer job iniciado a último job terminado) | ídem |
| Los 34 chicos, medidos (perfil `experimental`, código de abril a junio) | paso mediana 9,9 min, p95 13,2; job completo mediana 12,5, p95 18,0 | 5.588 pasos y 12.316 jobs en 378 corridas de 45 jobs, 2026-04-19 a 2026-06-04 | `gh run view`, tabla 3 |
| Los 34 chicos bajo `mirova_equivalent` hoy | paso mediana 14 a 16 min, p95 19 a 21 | **ESTIMACIÓN** (ver §3), nunca corrieron ese perfil en el cron | modelo |
| Pared con 45 jobs, `max-parallel` 8 | mediana 96 a 104 min, p95 102 a 110 | simulación (§4), validada contra las 39 corridas de 11 jobs | modelo |
| Pared con 45 jobs, `max-parallel` 15 | mediana 55 a 59 min, p95 60 a 64 | ídem | modelo |
| Pared con 45 jobs, `max-parallel` 20 | mediana 46 a 50 min, p95 50 a 55 | ídem | modelo |
| Con vía MODIS a 1,25 en todo el paso (cota superior) | 118 a 127 (mp 8), 67 a 73 (mp 15), 56 a 61 (mp 20) de mediana | ídem | modelo |
| Margen contra el paso de 50 min | máx observado 26,7 min (x 1,25 = 33,4): quedan 17 min | 429 pasos | medido + cota |
| Cadencia efectiva | despachos externos cada hora a las :10 UTC de las 01 a las 12; cron `0 */2` de GitHub llega con horas de atraso | últimas 100 corridas, 2026-10-26 a 2026-11-01 | `gh run list` |

## 1. Cómo arma hoy `nrt.yml` la corrida

- **Lista**: `strategy.matrix.volcano` con los 11 Tier A escritos a mano (comentario S101: los 34 se quitaron el 2026-06-05,
  tag `pre-s101-nrt-remove-experimental`). No sale de `volcanoes.yaml`.
- **Paralelismo**: `max-parallel: 8`, `fail-fast: false`. Con 11 jobs son dos tandas (8 + 3).
- **Timeouts**: job 80 min; cada paso de pipeline 50 min (`timeout-minutes: 50`). El peor job histórico que cita el yml
  es de 56 min (Villarrica, 2026-09-02); no lo re-medí (fuera de mi ventana).
- **Concurrencia**: a nivel de workflow, `group: push-main`, `cancel-in-progress: false`. Comparten ese grupo
  `sync-mirova-csv.yml` (cron :12 cada hora) y `backfill-tier-a.yml` (despacho manual). GitHub guarda UN solo run pendiente
  por grupo, así que un run nuevo desplaza al pendiente anterior.
- **Disparo real**: además del cron `0 */2 * * *` (que GitHub dispara con atraso de horas, p. ej. 04:12, 11:43, 16:51,
  21:00, 23:27 UTC), hay despachos externos (`workflow_dispatch`) a las :10 de CADA hora entre las 01 y las 12 UTC:
  29 de las 39 corridas de mi ventana. **En esas horas el ciclo efectivo es de 60 min, no de 120.** Evidencia de
  desplazamiento: de las últimas 100 corridas, 2 despachos quedaron `cancelled` (2026-10-28 01:10 y 08:10) y de las últimas
  60 de `sync-mirova-csv` 3 quedaron `cancelled` (mediana de creación a cierre 2,1 min, máx 37,7).
- **Dos listas fijas más**: el paso del pipeline (`mirova_equivalent`) y el paso A57 tienen
  `contains(fromJson('["Lascar", ... 11 nombres ...]'), matrix.volcano)`. **Agregar volcanes sólo a la matriz NO
  corre nada para ellos**: el paso se salta y el job termina verde en ~1,5 min con "No changes to commit". Hay que editar
  las dos listas.
- **`--volcano X` explícito** ignora el filtro `mirova_monitored` (`scripts/run_pipeline.py`, "Cuando se pide --volcano X
  explicito, se respeta"), así que el script sí puede correr los 34 con el perfil `mirova_equivalent`.
- **Cada job procesa 8 días** (hoy + 7 atrás, `default_date_window`), ~1,7 a 3,0 min por día en el job de Villarrica del
  2026-11-01 21:43 UTC (log, 8 fechas). Cada job es un runner distinto: cada volcán busca y baja sus propios gránulos,
  así que 45 jobs hacen ~4,1 veces las descargas a LAADS de hoy (SIN DATO: tope de LAADS o de la cuenta Earthdata).
- **Otros workflows que comparten recursos** (cada uno en su grupo, pero todos en el mismo pool de jobs simultáneos de la
  cuenta):
  - `experimental-diario.yml`: cron 14:00 UTC pero llega ~17 a 19 UTC; 11 jobs, `max-parallel: 4`; job mediana 19,8 min,
    p95 29,8 (165 jobs, 15 corridas verdes); pared de la corrida mediana 60,9 min, p95 81,9, máx 86,0.
  - `sombra-codigo-mirova.yml`: cron 15:00 UTC (llega ~19 a 20 UTC); 11 jobs, `max-parallel: 4`; paso 75 min, job 100.
    **Hoy es un no-op de ~1,5 min por job** ("la sombra parte el 2026-11-03"), así que su costo real NO está medido
    (los dos despachos de Láscar de S168 dieron 13,3 y 8,6 min, de ventana desconocida). Desde el 3-nov pasa a costar.
  - `vigilancia-sombra`, `nrt-healthcheck`, `nrt-monitor`, `nrt-retry`, `reproc-watchdog`: livianos (5 a 30 min tope,
    `ubuntu-latest`). `audit-weekly` (lunes) 45 min.
  - Plan de la cuenta: SIN DATO (la API no devuelve `plan`). Por la documentación de GitHub, el plan Free permite 20 jobs
    simultáneos en total; si es el caso, NRT a `max-parallel: 20` más 4 + 4 de la experimental y la sombra superaría ese
    tope cuando se solapan (a partir de ~16 UTC los tres pueden coincidir).

## 2. Duración por volcán, NRT de hoy (11 Tier A)

Ventana: 39 corridas verdes (de las últimas 100), 10 `schedule` + 29 `workflow_dispatch`, jobs iniciados entre
2026-10-30 07:10 y 2026-11-01 22:16 UTC. n = 39 por volcán (429 en total). Se excluyó la corrida 41290080234, que es un
re-intento con marcas de tiempo inconsistentes (job termina antes de empezar; 5 jobs con duración negativa). "Paso" es el
paso `mirova_equivalent`; "job" incluye checkout (mediana 1,0 min, p95 1,1), instalación y commit (sobrecarga mediana 1,55 min).

| Volcán | latitud | job med | job p95 | job máx | paso med | paso p95 | paso máx |
|---|---|---|---|---|---|---|---|
| PuyehueCordonCaulle | -40,6 | 19,0 | 22,8 | 24,2 | 17,3 | 21,2 | 22,4 |
| Chaiten | -42,8 | 18,3 | 22,5 | 28,4 | 16,9 | 20,8 | 26,7 |
| NevadosDeChillan | -36,9 | 18,0 | 22,0 | 22,3 | 16,5 | 20,3 | 20,5 |
| Villarrica | -39,4 | 17,9 | 22,3 | 24,0 | 16,1 | 20,8 | 22,4 |
| PlanchonPeteroa | -35,2 | 17,4 | 20,0 | 21,4 | 15,6 | 18,5 | 19,8 |
| Tupungatito | -33,4 | 16,9 | 22,6 | 23,5 | 15,5 | 20,8 | 21,8 |
| Copahue | -37,9 | 16,7 | 21,5 | 23,5 | 15,1 | 20,0 | 21,7 |
| Llaima | -38,7 | 16,5 | 22,0 | 24,5 | 14,9 | 20,4 | 22,8 |
| Lastarria | -25,2 | 16,1 | 18,9 | 24,4 | 14,5 | 17,4 | 22,8 |
| Isluga | -19,2 | 15,1 | 18,8 | 19,1 | 13,5 | 17,2 | 17,4 |
| Lascar | -23,4 | 14,5 | 19,1 | 22,4 | 13,2 | 17,6 | 20,9 |
| **Todos** | | **16,7** | **22,0** | **28,4** | **15,2** | **20,5** | **26,7** |

- **Sesgo de selección**: sólo cuento corridas verdes. En las últimas 100 corridas hubo 97 verdes, 1 roja y 2 canceladas;
  la roja (2026-11-01 05:10) fue Chaiten con el paso cortado por el timeout de 50 min (job de 52,3 min), es decir 1 paso
  colgado en ~1.100 jobs. Ese es el modo de falla de cola: un cuelgue fija la pared en >= 52 min. Con 45 jobs, la
  probabilidad de al menos un cuelgue por corrida sube de ~1 % a ~4 % (aritmética sobre ese 1 en 1.100).
- **La latitud manda**: el paso crece con |latitud| (más pasadas y gránulos por día al sur), regresión sobre los 11:
  0,146 min por grado, ordenada 10,4, r = 0,87, n = 11. No es un efecto de aleatoriedad: los tres más lentos son los
  tres más al sur.
- **MODIS contra VIIRS**: SIN DATO por tiempo. El log imprime los resultados de todos los sensores juntos al final de cada
  día y no marca el inicio ni el fin de cada sensor. Lo único medido es el reparto de gránulos y fases de un job de Copahue
  (S167, `experiments/_s167_sombra/COSTO.md`, un solo job): 83 gránulos nocturnos (32 VIIRS 375, 32 VIIRS 750, 19 MODIS),
  15,7 min buscando y bajando, 10,8 min procesando. En el job de Villarrica de hoy el reparto fue otro (~30 s de
  búsqueda y descarga por día, ~72 s de proceso por día), así que ese reparto varía entre jobs.

## 3. Los 34 volcanes chicos

**Hay corridas con los 34**: antes del 2026-06-05 el NRT corría los 45. Rescaté los jobs de 378 corridas
(`nrt.yml`, 2026-04-19 a 2026-06-04; la lista llegó al tope de 400 y no cubre antes del 19-abr), todas con 45 jobs,
`max-parallel: 8`, job con tope de 60 min. Allí los 34 corrían sólo el perfil `experimental` (radio 5 km) y los Tier A
corrían `mirova_equivalent` + `experimental`.

| Medida (paso, min) | n | mediana | p95 | máx |
|---|---|---|---|---|
| 34 chicos, paso `experimental` | 5.588 | 9,9 | 13,2 | 48,3 |
| 11 Tier A, paso `experimental` (mismo código) | 1.810 | 11,2 | 14,5 | 39,1 |
| 11 Tier A, paso `mirova_equivalent` | 1.645 | 14,5 | 19,0 | 41,5 |
| 34 chicos, job completo | 12.316 | 12,5 | 18,0 | 49,9 |
| 11 Tier A, job completo | 3.967 | 26,3 | 36,3 | 60,0 |

- **Lectura**: a igual perfil y época, un chico cuesta ~0,88 de un Tier A (9,9 contra 11,2), y comparando volcanes de la
  misma latitud ~0,9 (Michinmahuida 11,1 contra Chaiten 11,9; Sollipulli 10,1 contra Llaima 12,0). El radio de 5 km contra 25 km
  ahorra ~10 % (el proceso es chico) y el costo dominante es buscar, bajar y leer los gránulos, que no depende del radio.
  Misma tendencia con la latitud: de 8,4 min (Taapaca, -18,1) a 12,2 (Hudson, -45,9). Tabla completa por volcán en
  `old_salida.txt` (último bloque).
- **ESTIMACIÓN para hoy, bajo `mirova_equivalent`** (los chicos nunca corrieron este perfil en el cron):
  (a) 0,9 x paso Tier A de hoy = mediana ~13,7, p95 ~18,5; (b) regresión por latitud de §2 evaluada en los 34:
  13,0 (Taapaca) a 17,1 (Hudson), media 15,6 (extrapola hasta 46°; el máximo medido hoy es 42,8°). Uso 14 a 16 min de
  mediana y 19 a 21 de p95. En las simulaciones corro dos casos: chicos = Tier A (techo) y chicos = 0,9 x Tier A.
- **Fallas de entonces** (OJO, código anterior a la corrección A64 de S102, junio): 727 de 17.010 jobs no verdes (4,3 %);
  chicos 536 de 12.852 (4,2 %), Tier A 191 de 4.158 (4,6 %). La tasa por job es igual en ambos grupos, no peor en los
  chicos: lo que sí es peor es el conteo (3 de cada 4 fallas son de chicos solo porque son 34 de 45). A 45 jobs y p = 4,3 %
  una corrida salía roja casi siempre; de las 378, 41 (10,8 %) tuvieron pared >120 min y 14 >150 (pared mediana 94 min,
  p95 145, máx 279). El paso `Commit updated data files` falló 0 veces en las 378 x 45 con `max-parallel: 8`; con 20 jobs
  terminando juntos eso NO está medido (cinco reintentos de 10 a 50 s de espera).
- **El "ventana corta de abril" de `data/mirova_equivalent/`** (67 a 94 records por chico) no está en estos jobs como
  duración propia; no la usé.

## 4. Pared de una corrida de 45 jobs

**Modelo**: lista de espera con `max-parallel` cupos; cada job saca su duración al azar del conjunto de 429 jobs de §2
(sobrecarga de job + paso x factor); 8.000 a 20.000 repeticiones por celda, semilla 172 (`mc.py`, `mc_salida.txt`).
**Validación (control A110)**: con 11 jobs y `max-parallel` 8 el modelo da mediana 33,9, p95 38,6; lo observado es 32,6 y
38,5 en las 39 corridas. El modelo acierta el p95 y sobreestima la mediana en 1,3 min. Limitación: supone jobs
independientes y condicionados a corrida verde (no incluye cuelgues).

Pared en minutos (mediana / p95). "Chicos = A" usa para los 34 la misma distribución de los Tier A; "0,9 x A" los
escala 0,9 sobre el paso. Vía MODIS: factor sobre todo el paso (cota superior, pues MODIS no es todo el paso).

| Escenario | max-parallel 8 | 10 | 15 | 20 |
|---|---|---|---|---|
| 11 jobs actuales, K | 33,9 / 38,6 | n/a | n/a | n/a |
| 11 jobs actuales, MODIS 1,25 en todo el paso | 41,6 / 47,4 | n/a | n/a | n/a |
| 45 jobs, chicos = A, K | 103,9 / 109,9 | 85,4 / 90,8 | 59,0 / 64,1 | 50,0 / 54,5 |
| 45 jobs, chicos = 0,9 x A, K | 96,5 / 101,9 | 79,4 / 84,2 | 55,1 / 59,7 | 46,2 / 50,2 |
| 45 jobs, chicos = A, MODIS 1,25 | 127,2 / 135,0 | 105,0 / 111,9 | 72,7 / 79,0 | 61,3 / 66,7 |
| 45 jobs, chicos = 0,9 x A, MODIS 1,25 | 118,3 / 125,0 | 97,4 / 103,7 | 67,6 / 73,2 | 56,5 / 61,5 |
| 45 jobs, chicos = 0,9 x A, MODIS 1,06 (25 % del paso x 1,25, aritmética mía) | 101,8 / 107,5 | n/a | 58,1 / 62,9 | 48,6 / 52,8 |

Contra los dos ciclos:

- **Ciclo de 60 min (despachos horarios 01 a 12 UTC)**: no cabe con `max-parallel` 8 ni 10; con 15 está en el borde
  (p95 60 a 64); con 20 cabe en el caso K (p95 50 a 55) y deja de caber con MODIS 1,25 (61 / 67). Una corrida más larga
  que 60 min hace que el despacho de la hora siguiente espere o desplace al pendiente (ya hay 2 cancelados).
- **Ciclo de 2 h (cron)**: con `max-parallel` 8 cabe en el caso K (p95 102 a 110, margen ~10 min), no con MODIS 1,25
  (125 a 135). Y entonces el NRT dejaría de ser horario.
- **Paso de 50 min / job de 80 min**: no se acerca. Paso máximo 26,7 (x 1,25 = 33,4) y job máximo 28,4 (simulado 35,1
  con 1,25 en todo el paso). Sólo un cuelgue (el caso Chaiten de 52 min) lo toca, y no es consecuencia de la carga.
- **Vía "código MIROVA" de MODIS (1,1 a 1,25 x K por pasada MODIS, SOSPECHA hasta medir)**: acotado, no medido. Si MODIS
  fuera todo el paso, 1,25 sube el paso mediano de 15,2 a 19,0 y el p95 de 20,5 a 25,6. Con el reparto de gránulos de
  Copahue (19 de 83 son MODIS, 23 %), el factor sobre el paso sería ~1,06 (aritmética mía, el tiempo por gránulo MODIS
  puede diferir). En ambos casos el margen contra los 50 min se conserva; lo que se mueve es la pared de la corrida.
  Costo en minutos de runner de una corrida de 45 jobs: ~694 job-min (11 x 16,7 + 34 x 15,0) contra ~184 de hoy (3,8x);
  repo público, sin tope propio de minutos, SIN DATO sobre uso razonable.

## 5. Cambios que haría falta (para decidir)

1. Editar `nrt.yml`: matriz, y las dos listas `contains(fromJson(...))` (pipeline y A57). Si no, los 34 pasan verdes sin
   procesar nada.
2. Subir `max-parallel` a 20 (sólo así la corrida de 45 cabe en 60 min en el caso K), con las advertencias: tope de 20
   jobs simultáneos del plan Free (plan SIN DATO) compartido con la experimental y la sombra desde el 3-nov; commit
   simultáneo de ~20 jobs sin medir; un cuelgue deja la pared >= 52 min.
3. Alternativa de menos riesgo: dejar el NRT horario de los 11 como está (pared 33 / 38,5 / 40,3, margen ~20 min contra 60)
   y correr los 34 en un workflow aparte con su propio grupo y su propio reintento de push (molde `experimental-diario`):
   34 jobs con `max-parallel` 8 dan pared mediana 74 a 81 min (p95 79 a 87), con 10 dan 61 a 67 (p95 66 a 73), con 6 dan
   94 a 104 (p95 100 a 110); sirve para un ciclo de 2 a 6 h, no horario. Simulación de §4 con el mismo modelo.
4. Antes de lanzar: el dashboard (`frontend`) filtra por Tier A; no revisé qué hace con 34 archivos nuevos de
   `data/mirova_equivalent/` (fuera de esta pregunta).

## SIN DATO

- Tiempo por sensor (MODIS, VIIRS 375, VIIRS 750) dentro del paso: el log no lo marca.
- Costo real de la vía "código MIROVA" (sombra aún no corre; arranca el 2026-11-03).
- Plan de la cuenta y tope de jobs simultáneos (la API no lo devuelve).
- Tope o limitación de LAADS/Earthdata con ~4 veces las descargas.
- Contención de push con 20 jobs terminando a la vez.
- Los 34 con el perfil `mirova_equivalent` en el cron: nunca corrieron; los números de §3 para hoy son estimación.
- Cuelgues a 45 jobs: frecuencia extrapolada de 1 caso en ~1.100 jobs (n muy chico).

## Reproducción

Scripts y salidas en esta carpeta: `stats.py` (§2, `stats_salida.txt`), `lat.py` (regresión), `old.py` (§3,
`old_salida.txt`, `old_rows.json`), `stats2.py` (experimental-diario y sombra), `mc.py` (§4, `mc_salida.txt`). Crudos en
`jobs/`, `jobs_old/`, `jobs_exp/`, `jobs_sombra/`, `runs_*.json`; `nrt.yml`, `volcanoes.yaml`, `run_pipeline.py` y `wf/`
son copias de `origin/main`.
