# S139, eje 5 de 5: ¿se puede ejecutar el plan? Reprocesos, flags y costo

Fecha del servidor al medir: 2026-09-13 19:51 UTC (header `Date` de `gh api -i`, A86).
Commit local al empezar: `b16bb8fab`. Sólo lectura: no se disparó ningún workflow, no se tocó `pipeline/`.
Scripts y salidas crudas: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s139_audit\eje5\`.

## Resumen en cinco líneas

1. De los cuatro brazos del camino A, **dos tienen flag y cableado hoy** (banda 22 primaria y segundo pase condicionado); **dos no existen en `pipeline/`** (fondo de VRP por vecinos uniforme en los 3 sensores, y quitar la compuerta `bt > t_bg + 3 K`). Lo que S137 corrió con esos nombres fueron parches en el namespace de un script de probe, no código del pipeline, y el "sin compuerta" de S137 sólo tocó uno de los varios sitios donde vive la compuerta.
2. Un brazo completo (11 Tier A, 2026-01-01 a 2026-09-12, 3 sensores) cuesta **unas 107 horas de runner** con el ritmo mediano medido (2,3 min por día de ventana) y **hasta 183 h** con el más lento medido (3,92 min por día). Seis brazos: 650 a 1.100 h de runner, del orden de **3 a 5 días de reloj** sin chocar con el NRT.
3. El reloj de A15 del repo (2,4 min por día, `tests/test_guard_timeout_vs_ventana_s129.py`) **está por debajo de lo que se mide** en brazos con cómputo extra: aprobaría ventanas que después mueren por timeout, como ya pasó en S133 (19 de 24 jobs, 48 h de runner perdidas).
4. El token de Earthdata del CI se actualizó el 2026-08-04 y vive 60 días: **vence cerca del 2026-10-03**, justo dentro de un plan de varios días que empiece a fines de septiembre.
5. El tamaño mínimo que permite decidir: 6 volcanes de régimen opuesto, 2026-06-01 a 2026-08-31, 3 brazos. Unas 63 h de runner y menos de un día de reloj.

---

## Hallazgos (ordenados por gravedad)

### H501. El fondo de VRP por vecinos uniforme (D25) no existe en el pipeline, y en VIIRS 750 no existe ni siquiera opt-in

- **ARCHIVO:LÍNEA**: `pipeline/process_modis.py:1041` y `pipeline/process_viirs.py:1398` (el kernel 3x3 exige `ENABLE_LOCAL_KERNEL_BG and local_kernel_bg_compatible`); `scripts/run_pipeline.py:244, 288, 334` (el segundo operando sale de `volcano.get("local_kernel_bg", False)` en `volcanoes.yaml`); `pipeline/process_viirs_mod.py:433-440` (docstring: "la implementación kernel-local para M-band aún no existe"); `pipeline/process_viirs_mod.py:1189` (la magnitud del Test 1 usa `effective_L_bg` del `t_bg` global).
- **QUÉ PASA**: en una cumbre helada, el fondo del VRP sale de la mediana de un anillo de 5 a 25 km lleno de valle tibio; el cráter queda "más frío que el fondo" y su exceso se recorta a cero. El código sólo permite el fondo local 3x3 en MODIS y VIIRS 375, y sólo para los volcanes que el YAML marca; no hay flag que lo encienda uniforme, y en M-band no hay implementación. Flag leído con `VRP_PROFILE=mirova_equivalent python -c "import pipeline.profile as p; ..."`: `ENABLE_LOCAL_KERNEL_BG True` (el flag global está encendido; lo que gatea es el campo por volcán).
- **Lo que hizo S137**: `experiments/_s136/conformidad_apendice.py:275-280` reasigna `pm.ENABLE_LOCAL_KERNEL_BG = True` en el namespace del procesador MODIS y usa una global `FONDO_LOCAL`. Es un probe de 9 casos MODIS, no un brazo reproducible sobre los 3 sensores.
- **Código nuevo necesario (SOSPECHA en las cifras de líneas, no escrito)**: (a) un flag de perfil `enable_local_kernel_bg_uniform` en `pipeline/profile.py` (unas 5 líneas) que ignore el campo por volcán en los 3 sitios de `run_pipeline.py` o dentro de cada procesador; (b) portar el bloque `compute_local_background` a `process_viirs_mod.py` (unas 30 a 60 líneas más test); (c) decidir si el camino de magnitud del Test 1 (`process_viirs_mod.py:1185-1217` y sus equivalentes) también cambia de fondo, porque hoy usa el global; (d) si D25 pide la **media** aritmética de los vecinos, verificar qué estadístico usa `compute_local_background` (no lo leí: SOSPECHA). Toca `process_*.py`: A45, tag y confirmación.
- **CÓMO SE VE EN EL DASHBOARD**: invisible hoy. Es lo que deja cúmulos summit en 0,0 MW.
- **CÓMO REPRODUCIRLO**: `grep -n "local_kernel_bg" scripts/run_pipeline.py pipeline/process_*.py`.
- **CONFIANZA**: CONFIRMADO (leído).
- **GRAVEDAD**: 4. El brazo 3 del plan no se puede lanzar sin este código; lanzarlo con el flag global da un brazo idéntico a la base en 6 de 11 volcanes MODIS y en los 11 de V750.

### H502. La compuerta `bt > t_bg + 3 K` (D22) no tiene flag, vive en al menos cinco sitios por sensor, y el "sin compuerta" de S137 sólo quitó uno

- **ARCHIVO:LÍNEA**: MODIS `pipeline/process_modis.py:665` (camino NTI absoluto), `:693` y `:701` (camino D contextual), `:868` (argumento del primer paso de los Tests 2 y 3), `:821` (restricción posterior al segundo pase, dentro del bloque ETI que hoy está apagado: `ENABLE_ETI_QUADRATIC_SCENE False`). Iguales en `pipeline/process_viirs.py:976, 998, 1038, 1046, 1178, 1240` y `pipeline/process_viirs_mod.py:624, 643, 677, 685, 780, 832`. La constante es una sola: `pipeline/profile.py:88` `NTI_BT_SANITY_K = float(_t["nti_bt_sanity_k"])`.
- **QUÉ PASA**: la compuerta nació para el camino del NTI absoluto (sin contraste espacial) y se reutiliza en los caminos contextuales. S137 la quitó envolviendo sólo `first_pass_tests_2_and_3` con `bt_sanity_k=-1e9` (`experiments/_s136/conformidad_apendice.py:220-233, 268`): los caminos D contextual (`dual_roi_contextual_dnti_hot_mask`) quedaron con compuerta. Y bajar `nti_bt_sanity_k` en el YAML no es la alternativa, porque además quita la compuerta del camino NTI absoluto, que es otro experimento.
- **Código nuevo necesario (SOSPECHA en líneas)**: un flag propio (por ejemplo `enable_bt_gate_tests_23`) y decidir, por escrito en el pre-registro, qué sitios representan "los Tests 2 y 3": como mínimo el argumento del primer paso y el camino D contextual en los 3 procesadores (6 sitios, unas 20 líneas más guard). Si el brazo no lo declara, el resultado de "sin compuerta" depende de qué sitios tocó quien lo escribió.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `grep -n "NTI_BT_SANITY_K" pipeline/process_modis.py pipeline/process_viirs.py pipeline/process_viirs_mod.py`.
- **CONFIANZA**: CONFIRMADO (leído). Que el camino D contextual con compuerta haya alterado el resultado de la batería S137: SOSPECHA, no medido.
- **GRAVEDAD**: 4. Un brazo "sin compuerta" mal delimitado puede dar un veredicto sobre D22 que en realidad mide otra combinación.

### H503. El reloj de A15 del repo (2,4 min por día) está por debajo de la duración medida y ya dejó pasar un A/B que murió

- **SCRIPT:SALIDA**: `experiments/_s139_audit/eje5/duraciones.py` y `horas_runner.py` sobre los jobs de la API de GitHub.
  - Encabezado de la medición. P1: un job que no procesó nada dura segundos y aparece con su conclusión; un job muerto por timeout aparece como `failure` al minuto exacto del reloj. P2: si la API no trae steps, la fila sale `step=None`, no 0. Control positivo: el run fallido 33872836355 aparece con 19 `failure`, todos en 150,2 min.
  - Ritmo por job exitoso (minutos de step divididos por días de ventana; ventana leída del log de un job con las líneas `>>> Volcán | fecha`):

    | run | qué | días por job | mediana min/día | máx min/día | n jobs |
    |---|---|---|---|---|---|
    | 33370202265 | A/B S129, 5 volc x 3 brazos | 89 | 2,50 | 2,97 | 15 |
    | 33412422099 | A/B S129 | 88 | 2,53 | 3,25 | 15 |
    | 33456630043 | A/B S130 D18 | 88 | 2,49 | 3,05 | 12 |
    | 33872821788 | A/B S133 B22 | 31 | 2,47 | 2,89 | 4 |
    | 33912398561 | A/B S133 área (corona, geoloc) | 61 | **3,11** | **3,92** | 24 |
    | 34173711390 | A/B S135 chunk 1 | 45 | 2,08 | 2,77 | 30 |
    | 34208191011 | A/B S135 chunk 2 | 47 | 2,20 | 3,23 | 30 |

  - Run 33872836355 (primer intento del A/B del área): 19 de 24 jobs `failure` a 150,2 min con ventana de 61 días; 48,0 h de runner perdidas. El fix fue el commit `82e1ff0c5` ("el timeout del A/B del área estaba por debajo de la duración real").
- **QUÉ PASA**: `tests/test_guard_timeout_vs_ventana_s129.py` fija `MIN_POR_DIA = 2.4` (1,82 medido x 1,3). Para 61 días exige 146 min y el workflow declaraba 150: el guard pasa y 19 jobs mueren. Los brazos con cómputo extra corren a 3,1 a 3,9 min por día; un brazo D25 con kernel en los 3 sensores es de ese tipo (SOSPECHA de que lo sea, no medido).
- **CÓMO SE VE EN EL DASHBOARD**: invisible. Se ve como un A/B con volcanes faltantes.
- **CÓMO REPRODUCIRLO**: `cd experiments/_s139_audit/eje5 && bash dump_jobs.sh && python duraciones.py`.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD**: 3. Resultados parciales que se leen como hallazgos (un brazo sin los volcanes lentos, que son justamente los nevados).
- **Consecuencia para el plan**: dimensionar trozos con 3,92 x 1,3 = 5,1 min por día. Con el step de 170 min de `reproc-chunked.yml:136`, el trozo máximo es 33 días; usar 30.

### H504. El cron NRT no corre doce veces al día: corre cinco desde el 2026-08-27, y sigue así

- **SCRIPT:SALIDA**: `experiments/_s139_audit/eje5/nrt_por_dia.py` sobre 242 runs de `nrt.yml` creados 2026-08-14 a 2026-09-13 (240 `schedule`, 2 `workflow_dispatch`, 242 `success`).
  - P1: si el cron llegara como declara `0 */2 * * *` (`nrt.yml:12`), habría 12 por día; si no corriera, 0. P2: archivo vacío saldría `SIN_DATO`. Control positivo: del 08-15 al 08-25 da 12 cada día.
  - Salida: 12 por día hasta el 08-26 (11), luego 2, 2, 5, 5, 4, 5... y **5 a 7 por día hasta el 09-12**. Mediana de los 29 días completos: 6.
- **QUÉ PASA**: ya documentado en `.github/workflows/nrt-healthcheck.yml:281-295` (S133: "GitHub dejó de entregar la mitad de los eventos `schedule`"). Lo nuevo es que **sigue vivo 17 días después** y con más de la mitad perdida. Para el plan importa por dos cosas: la afirmación "doce veces al día" del contexto de esta auditoría es falsa hoy, y cada run NRT ocupa el grupo `push-main` unos 80 min (ejemplos del 09-13: 18:32 a 19:49, 14:03 a 15:24).
- **CÓMO SE VE EN EL DASHBOARD**: dato con hasta ~5 h de antigüedad entre actualizaciones (huecos entre creaciones de run del 09-08: 03:11, 08:37, 14:08, 19:15, 22:22).
- **CÓMO REPRODUCIRLO**: `gh api "repos/MendozaVolcanic/VRP-chile/actions/workflows/nrt.yml/runs?created=2026-08-14..2026-09-13&per_page=100" --paginate --jq '.workflow_runs[].created_at'`.
- **CONFIANZA**: CONFIRMADO el conteo. La causa (GitHub, no el repo): SOSPECHA heredada del comentario de S133; no hubo cambio de cron en `git log` de `nrt.yml` desde el 08-20 (commits `772f000c4`, `4d76cb152`, `b0066a6c7`, ninguno toca la línea del cron).
- **GRAVEDAD**: 3. No es del A/B, pero es latencia de alerta en el sistema que el A/B quiere mejorar.

### H505. El token de Earthdata del CI vence cerca del 2026-10-03, dentro de la ventana de ejecución del plan

- **ARCHIVO:LÍNEA**: `gh secret list`: `EARTHDATA_TOKEN 2026-08-04T07:19:42Z`. `docs/EARTHDATA_TOKEN_SETUP.md` §4: "Token vida 60 días". `pipeline/fetch.py:259` y siguientes: `auth()` prefiere el token; `pipeline/fetch.py` en `fetch_for_volcano` relanza `EarthdataCredentialError` en vez de degradar (comentario S123).
- **QUÉ PASA**: 2026-08-04 + 60 días = 2026-10-03. Un plan de 3 a 5 días de reloj que arranque después de consolidar el frente pausado cae encima de esa fecha. Lo bueno: con la credencial muerta el run muere ruidoso (no es el zombie verde de A64). Lo malo: los A/B no commitean y un brazo a medias queda como artefacto parcial.
- **Además**: `C:\Users\nmend\OneDrive\Escritorio\claude\REGISTRO_CREDENCIALES.md:28` y `:135` dicen "EXPIRADO ~2026-07-20" y "sin ingesta térmica desde el 2026-07-17". Está desactualizado: el secret se renovó el 08-04 y hoy hay commits "NRT update" del 2026-09-13.
- **CÓMO SE VE EN EL DASHBOARD**: si vence, el NRT también se detiene (misma credencial).
- **CÓMO REPRODUCIRLO**: `gh secret list`.
- **CONFIANZA**: CONFIRMADO la fecha de actualización del secret; la fecha de vencimiento es derivada (60 días documentados, no verificados contra el panel de NASA).
- **GRAVEDAD**: 3.

### H506. Dos A/B grandes simultáneos más el NRT se acercan al límite de jobs concurrentes; el NRT ya esperó 40 minutos en cola

- **SCRIPT:SALIDA**: `experiments/_s139_audit/eje5/concurrencia_s135.py` sobre los 60 jobs de S135 (runs 34173711390 y 34208191011) y 33 jobs NRT de los runs 34182666375, 34205461552, 34236407989 (2026-09-08).
  - P1: si hubiera saturación, la concurrencia tocaría el techo y la espera de los jobs NRT crecería. P2: jobs sin timestamps se cuentan aparte (0).
  - Salida: concurrencia máxima 15 (7 A/B + 8 NRT) a las 14:09 UTC; espera en cola de los jobs NRT: mediana 0,0 min, **máximo 40,5 min** (n = 33).
- **QUÉ PASA**: `reproc-chunked.yml:114-116` usa `max-parallel: 8` por run y su grupo de concurrencia es por perfil (`reproc-chunked.yml:57-59`), así que dos brazos despachados a la vez suman 16 jobs más los 8 del NRT = 24. El límite de 20 jobs para repo público lo cita el propio workflow (`reproc-chunked.yml:51`); no lo verifiqué contra la documentación de GitHub (SOSPECHA). Que los 40,5 min de espera se deban a los A/B y no a otra cosa: SOSPECHA.
- **CÓMO SE VE EN EL DASHBOARD**: actualización NRT atrasada.
- **CÓMO REPRODUCIRLO**: `cd experiments/_s139_audit/eje5 && python concurrencia_s135.py`.
- **CONFIANZA**: CONFIRMADO la medición; SOSPECHA la causalidad.
- **GRAVEDAD**: 2.

### H507. Los resultados de A/B viven 14 días como artefactos; tres series anteriores vencen esta semana y la próxima

- **ARCHIVO:LÍNEA / SALIDA**: `reproc-s135-ab-d1d2.yml` y `reproc-s133-b22-ab.yml` (`retention-days: 14`, `permissions: contents: read`). API: `s129ab-...` vence 2026-09-15; `s133b22-...` 2026-09-18; `s135ab-...` 2026-09-22. `reproc-chunked.yml` guarda trozos 7 días y **sí** commitea a `main` (job `merge`, `git add -f "data/$PROFILE"/*.json`).
- **QUÉ PASA**: el banco de prueba del eje 2 tiene que bajar los artefactos antes de que venzan o reprocesar. Si se usa `reproc-chunked`, cada brazo entra al repo: medido, los 11 Tier A pesan 276 MB para 59.310 records (4.100 a 6.500 bytes por record, `tamano_resultados.py`); un brazo de 2026 (26.866 records) serían unos **125 MB** (supuesto: mismo tamaño por record que producción). El pack de git ya pesa 6,61 GiB (`git count-objects -vH`). En disco local (11 GB libres, 98 %) 6 brazos descomprimidos son unos 750 MB: caben, pero dentro de OneDrive.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `gh api repos/MendozaVolcanic/VRP-chile/actions/runs/34173711390/artifacts --jq '.artifacts[0].expires_at'`.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD**: 2.

### H508. La producción tiene un hueco de 28 días en enero de 2026, así que "enero a septiembre" no tiene línea base persistida

- **SCRIPT:SALIDA**: `records_por_mes.py`, `version_producto.py`, `cobertura_enero.py` sobre `data/mirova_equivalent/`.
  - P1: un hueco de backfill aparece como días faltantes contiguos. P2: un volcán sin archivo sale `SIN_DATO` (ninguno).
  - Records de los 11 Tier A en 2026-01: 662; en cada mes de febrero a agosto: 3.314 a 3.682. Días con records en enero: Láscar 3 (01-29 a 01-31), Nevados de Chillán 3, Villarrica 31 (reprocesado en S124). Denominador: 3 volcanes revisados día a día, los 11 por mes.
- **QUÉ PASA**: la base no puede tomarse de producción (tampoco conviene: S135 ya decidió reprocesar el control), y el hueco dice que nadie ha probado que los granules de enero bajen bien. Que LAADS los sirva: SOSPECHA razonable (febrero a junio salen 100 % `standard`), no verificada.
- **CÓMO SE VE EN EL DASHBOARD**: serie de enero vacía en 10 de 11 volcanes.
- **CONFIANZA**: CONFIRMADO en los 3 volcanes revisados.
- **GRAVEDAD**: 2.

### H509. `backfill-tier-a.yml` escribe sobre producción; no sirve de plantilla para brazos

- **ARCHIVO:LÍNEA**: `.github/workflows/backfill-tier-a.yml:89-90` (`--profile mirova_equivalent`), `:43-51` (grupo `push-main`), `:107` (push con `pull --rebase -X theirs`).
- **QUÉ PASA**: es el único workflow de reproceso largo con matrix de 11 Tier A ya armada, y es exactamente el que pisa `data/mirova_equivalent/`. Copiarlo para un brazo cambiando sólo el perfil funciona; copiarlo olvidando el perfil pisa la serie operacional. `reproc-chunked.yml` sí rehúsa `mirova_equivalent` (paso `plan`).
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 2.

### H510. `keep_peak` (D19) sólo tiene palanca en VIIRS 375; en MODIS y V750 el brazo D19 se reduce al segundo pase

- **ARCHIVO:LÍNEA**: `ENABLE_TEST1_CONTEXTUAL_KEEP_PEAK` se importa sólo en `pipeline/process_viirs.py:178` y se usa en `:1788`. MODIS y M-band usan otro concepto, `FOCAL_CLUSTER_KEEP_PEAK` (`process_modis.py:1154, 1404`; `process_viirs_mod.py:1254`).
- **QUÉ PASA**: un brazo "D19 en los 3 sensores" que apague `enable_test1_contextual_keep_peak` no cambia nada en MODIS ni V750 por esa vía. No es un defecto; hay que escribirlo en el pre-registro para que un MODIS idéntico a la base no se lea como "D19 no tiene efecto en MODIS".
- **CONFIANZA**: CONFIRMADO (grep). **GRAVEDAD**: 2.

### H511. Con banda 22 primaria, la radiancia del VRP se recalcula a la longitud de onda de la banda 21

- **ARCHIVO:LÍNEA**: `pipeline/process_modis.py:548` (`bt_mir` sale de B22 a 3,959 µm cuando el flag está ON); `:1022` y `:1025` (`L_bg_global` y `hotpix_rad` con `BAND21_LAMBDA` = 3,929 µm); `:767` (lo mismo para `nti_app`, en el bloque ETI apagado).
- **QUÉ PASA**: la temperatura de brillo medida en la banda 22 se devuelve a radiancia con la longitud de onda de la banda 21. Las dos bandas están a 0,03 µm, así que el sesgo debería ser chico, pero el brazo B22 mide magnitud y ese sesgo va dentro. No medí su tamaño.
- **CONFIANZA**: CONFIRMADO el código; SOSPECHA el efecto. **GRAVEDAD**: 2.

### H512. `reproc-chunked.yml` interpola entradas de matrix dentro del `run:`

- **ARCHIVO:LÍNEA**: `.github/workflows/reproc-chunked.yml`, step "Reprocesar": `--volcano ${{ matrix.job.vol }} --start ${{ matrix.job.start }} --end ${{ matrix.job.end }}`, que vienen del input `volcanoes` sin sanitizar.
- **QUÉ PASA**: el patrón que S128 contó en 7 workflows y que los A/B de S133 y S135 ya evitan pasando por `env`. Sólo lo puede disparar quien tiene escritura en el repo.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 1.

---

## Respuestas a las seis preguntas

### 1. Flags y código

| Brazo | Flag en `pipeline/profile.py` | Cableado | Test | Código nuevo |
|---|---|---|---|---|
| Banda 22 primaria (D21) | `ENABLE_MODIS_B22_PRIMARY` (l. 557), hoy False | `process_modis.py:544, 548, 561` vía `merge_mir_bands` | `tests/test_b22_primaria_modis_s132.py` | ninguno (ver H511) |
| Segundo pase condicionado (D19/D2) | `ENABLE_SECOND_PASS_CONDITIONED` (l. 403), hoy False | 3 sensores: `process_modis.py:796, 813, 936`; `process_viirs.py:1157, 1172, 1301`; `process_viirs_mod.py:759, 774, 893`; lógica en `detection_context.py:887` | `tests/test_second_pass_conditioned_s135.py` | ninguno |
| `keep_peak` OFF | `ENABLE_TEST1_CONTEXTUAL_KEEP_PEAK` (l. 264), hoy True | sólo VIIRS 375 (H510) | perfiles `_s135_ab_b/d` | ninguno |
| Fondo por vecinos uniforme (D25) | no existe | MODIS y V375 opt-in por volcán; V750 sin implementar | no | sí (H501) |
| Quitar compuerta (D22) | no existe; sólo la constante compartida | 5 a 6 sitios por sensor | no | sí (H502) |

Los perfiles nuevos son baratos: `extends: mirova_equivalent` está soportado (`pipeline/profile.py:47-56`) y `run_pipeline.py:57` descubre cualquier YAML de `pipeline/profiles/`. Los flags se leyeron con `VRP_PROFILE=mirova_equivalent python -c "import pipeline.profile as p; ..."` (A89).

Estimación de código nuevo (SOSPECHA, no escrito): D25, 60 a 100 líneas en 3 procesadores más `profile.py` y 2 tests; D22, 20 a 40 líneas más un guard que verifique los sitios elegidos. Todo bajo A45. Riesgo principal: que el flag apagado no sea un no-op (lección S126): hace falta un test que compare la salida de un granule con el flag OFF contra la de hoy.

### 2. Costo real de reprocesos

- Ritmo medido: tabla de H503. Base y brazos sin cómputo extra: **2,1 a 2,5 min por día** (mediana por run); con cómputo extra: 3,1 mediana, 3,9 máximo.
- Horas de runner por run (`horas_runner.py`): S135 chunk 1, 48,8 h en 14,5 h de reloj; chunk 2, 53,1 h en 9,4 h; los dos juntos corrieron de 00:33 a 18:28 UTC del 2026-09-08 (30 + 30 jobs, `max-parallel: 6` cada uno). S133 área: 72,1 h en 10,7 h. Backfill 11 Tier A, 90 días de 2025: 43,5 h en 8,1 h.
- Reparto red contra cómputo (`tiempo_red_vs_cpu.py`, 5 logs): la descarga es **28 a 36 %** del tiempo; cada par L1B más geolocalización baja en 3 a 6 s desde LAADS. El resto es búsqueda y proceso. No hay caché: `run_pipeline.py:352-363` borra los granules al terminar cada día.
- Por sensor: no separable con los logs actuales (los granules de las 8 plataformas se procesan dentro del mismo día). Un brazo sólo MODIS (con `sensors` del perfil) sería más barato, pero cuánto: SIN DATO.

Extrapolación (ventana 2026-01-01 a 2026-09-12 = 255 días, 11 volcanes):

| | min por día | h de runner por brazo | jobs por brazo (trozos de 30 días) |
|---|---|---|---|
| ritmo mediano | 2,3 | 107 | 99 |
| ritmo lento medido | 3,92 | 183 | 99 |

Seis brazos (base, B22, completo, tres ablaciones): **645 a 1.100 h de runner**. Con 12 jobs simultáneos para no pasar de 20 con el NRT: 54 a 92 h de reloj puro, **3 a 5 días** con despachos. Toda la historia útil (desde 2025-02-15) agrega 320 días: multiplicar por 2,25.

### 3. Datos de entrada

- Banda 22: se lee de `EV_1KM_Emissive`, índice 2, en cada granule que ya se descarga (`process_modis.py:199, 254`). No hay que bajar nada nuevo.
- Producto: MOD021KM/MYD021KM v6.1 Standard con respaldo `6.1NRT` (`fetch.py:187-194`). En producción, febrero a junio de 2026 son 100 % `standard`; julio 97 NRT de 3.495; agosto 64 de 3.660; septiembre 14 de 1.558 (`version_producto.py`). Los logs de S135 bajan con prefijo `LAADS:`.
- Pasadas nocturnas procesadas en 2026, 11 Tier A: MODIS 5.501, V375 10.725, V750 10.640 (`records_por_mes.py`). MODIS por volcán en agosto: 59 a 77. Control positivo: Villarrica agosto 70, igual a lo que declara `reproc-s133-b22-ab.yml`.
- Filtro de noche antes de descargar: `fetch.py:797-808` (log: "kept 1 of 2 granules").
- Credenciales: `EARTHDATA_TOKEN`, `EARTHDATA_USERNAME`, `EARTHDATA_PASSWORD` presentes en secrets (H505 por el vencimiento).

### 4. Dónde quedan los resultados

Ver H507. Recomendación: los A/B de decisión como artefactos (patrón S133 y S135, `contents: read`, no tocan `main`), bajados con `gh run download <id> --dir <destino fuera de OneDrive>` el mismo día; el banco del eje 2 los lee por `data_subdir`. No usar `reproc-chunked` sin quitarle el commit, o aceptar unos 125 MB por brazo en el repo.

### 5. Riesgos operacionales

- Pisar producción: sólo `backfill-tier-a.yml` (H509). Los A/B de S133 y S135 declaran `contents: read`.
- Carrera de push: los A/B como artefactos no pushean; `reproc-chunked` pushea desde un único job `merge` con reintentos.
- A47: cada brazo en su `data_subdir` (patrón de los perfiles `_s135_ab_*`). Dos trozos del mismo brazo y volcán nunca deben escribir el mismo JSON en el mismo job; en artefactos cada job tiene runner propio, así que no hay carrera local.
- Jobs verdes que no producen: los A/B suben con `if-no-files-found: warn`, así que un volcán sin JSON deja el run en verde. Conviene `error` (como `reproc-chunked.yml`) y el paso "Verificar que el brazo LEE lo que declara" de S135.
- Timeouts: H503.
- Credencial: H505. Cadencia NRT y cola: H504, H506.

### 6. Propuesta de ejecución

Supuestos: los flags D25 y D22 se escriben antes (A45); el frente D21/D22 está pausado por A51 hasta que Nicolás decida S138-B y S138-C.

**Paso 0 (antes de gastar runner)**. Renovar el token si faltan menos de 15 días para el 10-03. Subir `MIN_POR_DIA` del guard a un valor que cubra lo medido (3,92 x 1,3 = 5,1) o exigir trozos de 30 días. Test de no-op de los flags nuevos.

**Paso 1, tamaño mínimo viable (unas 63 h de runner, menos de 1 día de reloj)**. 6 volcanes de régimen opuesto (los de S135: Isluga, Láscar, Lastarria, Puyehue-Cordón Caulle, Planchón-Peteroa, Tupungatito), ventana 2026-06-01 a 2026-08-31 (92 días, en dos trozos de 45 y 47 como S135, que ya se midieron: 102 h para 5 brazos, o sea unas 20 h por brazo), 3 brazos: base reprocesada, completo (B22 + D25 + segundo pase condicionado), y completo sin D25. Cuenta: 6 x 92 x 2,3 / 60 = 21 h por brazo, x 3 = 63 h; con `max-parallel: 6` por run y los dos trozos a la vez, unas 10 a 15 h de reloj. Decide si D25 mueve algo en noches de volcán, que es la unidad del operador.

**Paso 2, sólo si el paso 1 muestra efecto**. Extender a los 11 Tier A y a 2026-02-01 a 2026-09-12 (224 días; enero se deja fuera por H508 hasta verificar que baja), con trozos de 30 días. Unos 94 h por brazo; 4 brazos más, de a 2 a la vez, 2 a 3 días de reloj.

**Paso 3, opcional**. La historia de 2025 sólo para el brazo ganador y la base.

---

## VERIFICADO LIMPIO

| Qué | Comando | Resultado |
|---|---|---|
| El flag B22 existe, se lee del perfil y está cableado en MODIS | `grep -n "ENABLE_MODIS_B22_PRIMARY" pipeline/*.py` | `profile.py:557`, `process_modis.py:167, 544, 548, 561` |
| El segundo pase condicionado llega a los 3 procesadores y a `detection_context.py` | `grep -n "ENABLE_SECOND_PASS_CONDITIONED\|conditioned" pipeline/process_*.py pipeline/detection_context.py` | 9 llamadas más `detection_context.py:887` |
| Los perfiles A/B heredan de producción con `extends` y aíslan `data_subdir` | `cat pipeline/profiles/_s135_ab_d_ambos.yaml` | `extends: mirova_equivalent`, `data_subdir: _s135_ab_d_ambos` |
| `reproc-chunked.yml` rehúsa `mirova_equivalent` y perfiles sin `data_subdir` | leer paso `plan` | dos `SystemExit("REHUSADO ...")` |
| Los A/B de S133 y S135 no pueden pushear | `grep -n "permissions" -A1 .github/workflows/reproc-s13*.yml` | `contents: read` |
| Las credenciales no se interpolan en `run:` en los A/B de S133 y S135 | leer steps "Run reprocess" | fechas y perfil por `env` |
| La descarga no es el cuello de botella | `python tiempo_red_vs_cpu.py log_*.txt` | 28 a 36 % del tiempo |
| La banda 22 ya se descarga y calibra en cada granule | `sed -n 240,260p pipeline/process_modis.py` | `band22 = calibrate(BAND22_IDX, ...)` |
| Una credencial muerta hace fallar el run en vez de dejarlo verde | `sed -n 810,820p pipeline/fetch.py` | `except EarthdataCredentialError: raise` |
| Ningún resultado de A/B de S133 o S135 está commiteado en `data/` | `git ls-files data \| grep "^data/_s13[3-5]"` | vacío |
| Artefactos de S135 aún disponibles | `gh api .../runs/34173711390/artifacts` | 30 artefactos, `expired false`, vencen 2026-09-22 |

Lo que NO miré y queda abierto: el tiempo de cómputo por sensor; si `compute_local_background` usa media o mediana; el límite exacto de jobs concurrentes de GitHub; si LAADS sirve enero de 2026; el tamaño del sesgo de H511.
