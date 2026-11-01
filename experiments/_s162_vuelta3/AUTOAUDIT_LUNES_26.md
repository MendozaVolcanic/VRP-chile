# Simulación del auto-audit del lunes 2026-10-26: main contra #900

**Hora del servidor** (`gh api -i repos/MendozaVolcanic/VRP-chile | grep -i date`): `Sun, 25 Oct 2026 02:18:50 GMT` (primera lectura 02:10:16 GMT). El lunes 26 es en unas 31 horas.
**Commits medidos**: `origin/main` = `f9e22f8d6ec94dfa06275d8061538a1847ee3bea` (commit 2026-10-25 01:35 UTC); PR #900 head `7ab5e64f65b16a58e7d0d2ebfb57b0e19f147f4f` (abierto, CI verde, CLEAN, base `3bbd18d2c`).
**Carpeta**: `C:\Users\nmend\AppData\Local\Temp\claude\C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile\a3efc9fd-8a35-470a-aad1-531abaec64d8\scratchpad\vuelta3\autoaudit_lunes`

## Resumen (cinco líneas)

1. **Lunes 26, main y #900 dan lo mismo**: `FUERA_DE_BANDA`, 11 flags (1 de recall V750, 5 de magnitud, 5 alertas protegidas), y abriría un issue NUEVO titulado `⚠ Auto-audit semanal FUERA DE BANDA` + guion largo + `2026-10-26` (el título lleva ese guion, como el de #864). No actualiza #864: esa rama del workflow no mira issues abiertos, así que #864 y el nuevo quedarían abiertos a la vez.
2. **#900 no mueve ningún número ni el veredicto**: JSON idéntico salvo la clave nueva `plataformas`, consola idéntica; lo único que cambia es que el cuerpo del issue gana una sección "Sensores sin juzgar por un cese de plataforma" con el texto `- ninguno` (el corte de Suomi NPP empieza a juzgarse el 2026-11-03, así que el 26-oct no hay nada que recortar).
3. **Contra #864**: los 10 flags de #864 siguen todos (las 5 alertas protegidas son las mismas y el MODIS de Chillán sigue en 0,485x n=7) y aparece 1 nuevo: Puyehue Cordón Caulle VIIRS 750 en 0,517x (n=10). Los números cambian de tamaño, no de signo: recall V750 73,3 % (n=30) pasa a 72,9 % (n=48) y Tupungatito VIIRS 375 de 0,266x (n=8) a 0,448x (n=19).
4. **Casi todo el cambio es del instrumento, no del volcán**: al mover la frontera de K a 2025-02-15 (#883) la ventana juzgada pasó de 31 a 60 días (n de V750 de 30 a 48; n de Tupungatito de 8 a 19). Lo que sí es de los volcanes entre el 19 y el 25-oct es poco: 3 noches nuevas de Chillán VIIRS 375 (razón mediana 1,89) y 2 noches de VIIRS 750 que acertaron; ninguna alerta protegida nueva sin publicar con datos hasta el 2026-10-24.
5. **Bordes que pueden cambiar el informe**: MODIS recall está en 69,2 % con n=13 (el flag exige n=15; si llega, saldría un flag nuevo bajo la banda de 95 %); Chillán VIIRS 750 está a 0,006 de la banda; si el NRT se atrasa y el último día con datos queda 2 días atrás, el veredicto pasa a `DEGRADADO` con otro título. SIN DATO: la unión histórica de la semana y los datos del 25 y 26-oct.

## Cómo se hizo

- `git fetch origin --prune` (sólo refs; no hice pull, ni cambié de rama, ni toqué el árbol de trabajo; `git status` antes y después igual, rama `loop/activo`).
- `git archive origin/main` extraído en `...\autoaudit_lunes\main` (A). El árbol de #900 (B) es el mismo árbol de main con `scripts/auto_audit_weekly.py` y `audit-weekly.yml` del head de #900. Es lo que quedaría tras el merge: entre la base de #900 y main, `git diff --stat 3bbd18d2c origin/main -- scripts/ .github/workflows/audit-weekly.yml pipeline/profile.py` está vacío (136 commits, todos de datos u otros archivos).
- Referencia de MIROVA: como hace el paso "Refresh ground truth" del workflow, bajé `registro_vrp_consolidado.csv` y `registro_vrp_ocr.csv` de `raw.githubusercontent.com/MendozaVolcanic/Mirova-v1/main/...` (sin credenciales) y reemplacé el snapshot en los árboles. La unión histórica quedó la commiteada (regenerada el 2026-10-19, `hasta: 2026-10-19`), porque regenerarla exige la API autenticada.
- Reloj fijo, sin editar el script: `run_sim.py` inyecta un módulo `datetime` con `now()` fijo y ejecuta `scripts/auto_audit_weekly.py` real con `python -I`. Cada corrida tarda unos 8 s.
- El paso real "Open issue if out of band" del workflow, extraído del YAML, se ejecuta con `gh` y `date` simulados (`simular_issue.sh`), para ver título y cuerpo exactos.
- **Validación del simulador**: con la frontera vieja (2026-09-18) y el reloj en 2026-10-19 16:29 (corrida `F_1019`), los 10 flags salen idénticos a los de #864, uno por uno (mismos valores y mismas n, incluida Chillán). Que el verdicto de esa réplica sea DEGRADADO y no FUERA_DE_BANDA es otra cosa: hoy hay 3.442 records de K con fecha anterior a la frontera vieja y el audit lo avisa; eso es lo que #883 resolvió.

## Dos relojes, porque el dato de hoy no llega al lunes

Hoy el último día con datos nuestros es 2026-10-24. El workflow corre con `today` = fecha UTC del run, y su cron es lunes 09:00 UTC, pero las corridas reales del lunes salieron a las 16:16 (10-19), 18:42 (10-12) y 18:04 UTC (10-05) (`gh run list --workflow audit-weekly.yml`). Para el lunes habrá datos del 25 y de parte del 26.

- **Reloj 2026-10-25** (ventana 2026-08-26 a 2026-10-25): es el mejor proxy, con el último día con datos a 1 día de la cola (el máximo tolerado, `MAX_COLA_SIN_DATOS_DIAS = 1`). Corridas `A_1025` (main) y `B_1025` (#900).
- **Reloj 2026-10-26** (ventana exacta del lunes, 2026-08-27 a 2026-10-26): la cola sin datos es de 2 días porque aún no existen el 25 y el 26, y eso dispara `DEGRADADO`. Es un artefacto de simular hoy, no una predicción. Corridas `A_1026` y `B_1026`.

## Las dos simulaciones lado a lado

| | A: código de main (sin #900) | B: código de #900 |
|---|---|---|
| Veredicto, reloj 10-25 | `FUERA_DE_BANDA`, 11 flags | `FUERA_DE_BANDA`, 11 flags |
| Veredicto, reloj 10-26 | `DEGRADADO` (cola de 2 días), 11 flags | `DEGRADADO` (cola de 2 días), 11 flags |
| ¿Abre issue? | Sí, uno nuevo (no deduplica con #864) | Sí, uno nuevo (no deduplica con #864) |
| Título (FUERA_DE_BANDA) | `⚠ Auto-audit semanal FUERA DE BANDA` + guion largo + `2026-10-26` | idéntico |
| Título (DEGRADADO, si no hay otro abierto) | `⚠ Auto-audit semanal DEGRADADO: 2026-10-26` | idéntico |
| `latest.json` | de referencia | igual salvo la clave `plataformas` (`juzga_desde` MODIS, VIIRS750 y VIIRS375 en null; `sin_juzgar` vacío; `aparte` null; cese Suomi NPP con `primer_dia_sin` 2026-11-03) |
| Consola | de referencia | idéntica (`diff` vacío en 10-25 y 10-26) |
| Línea de `history.jsonl` | de referencia | gana `plataformas_juzga_desde` |
| Cuerpo del issue | flags + detalle + protocolo | lo mismo + al final: "Sensores sin juzgar por un cese de plataforma (no se midieron, no están en banda): - ninguno" (en el DEGRADADO, antes de "Detalle") |

El título y el cuerpo salen de `res\issue_A_1025.txt`, `res\issue_B_1025.txt`, `res\issue_A_1026.txt` y `res\issue_B_1026.txt`. (La consola de Windows muestra mojibake en las tildes de esos archivos por el `python -c` del paso; en el runner Linux sale en UTF-8.)

Cuándo importa #900: con el corte de Suomi NPP del 2026-11-02 13:00 UTC, `juzga_desde` de VIIRS recién deja de ser null el 2026-11-03, así que el primer informe recortado es el del lunes 9-nov. El del 26-oct y el del 2-nov son iguales a main. La revisión previa (`experiments/_s162_vuelta1/REVISION_900_Y_MODIS.md` en origin/loop/activo) llegó a lo mismo para el 26-oct sobre otro head (`a7d1c0b91`); esta vez medí el head actual `7ab5e64f6`, que ya trae el aviso de PR162-01 en el workflow.

## Los 11 flags contra los 10 de #864

Ventanas: #864 = recall y magnitud 2026-08-20 a 2026-10-19, pero sólo noches desde la frontera 2026-09-18 (31 días). Hoy = ventana de 60 días completa, frontera 2025-02-15.

| flag | #864 (corrida real del 10-19) | Lunes, reloj 10-25 (A = B) | Lunes, reloj 10-26 (A = B) |
|---|---|---|---|
| recall V750 (banda 79,5 %) | 73,3 % n=30 | 72,9 % n=48 | 72,3 % n=47 |
| magnitud Chillán MODIS | 0,485x n=7 | 0,485x n=7 | 0,485x n=7 |
| magnitud Chillán VIIRS 375 | 0,65x n=16 | 0,662x n=19 | 0,662x n=19 |
| magnitud Chillán VIIRS 750 | 0,687x n=13 | 0,694x n=14 | 0,694x n=14 |
| magnitud Tupungatito VIIRS 375 | 0,266x n=8 | 0,448x n=19 | 0,448x n=19 |
| magnitud Puyehue VIIRS 750 | no está (n=4, bajo el mínimo de 5) | **0,517x n=10 (NUEVO)** | 0,517x n=10 |
| protegida Tupungatito V375 2026-09-28 05:18 | 2,51 MW | 2,51 MW | 2,51 MW |
| protegida Tupungatito V375 2026-09-29 04:54 | 1,86 MW | 1,86 MW | 1,86 MW |
| protegida Puyehue V750 2026-10-10 05:54 | 1,19 MW | 1,19 MW | 1,19 MW |
| protegida Chillán MODIS 2026-10-12 07:20 | 2,18 MW | 2,18 MW | 2,18 MW |
| protegida Chillán MODIS 2026-10-15 01:05 | 1,72 MW | 1,72 MW | 1,72 MW |
| **total de flags** | **10** | **11** | **11** |

Definiciones (A90): **recall** = noches UTC con alerta de MIROVA (regla D-9 SN, nocturnas, VIIRS 750, 11 volcanes del audit) en que tenemos algún record de ese sensor, y el porcentaje es la fracción con cúmulo de cráter (A10); **magnitud** = mediana por volcán y sensor de max(publicado de la noche) / VRP de MIROVA, sobre las noches comunes con VRP de MIROVA mayor que 0; el flag exige n mínimo 5 y banda [0,7 a 1,4]x; **protegida** = alerta de MIROVA de 1 MW o más (lectura A), sin mínimo de noches. El recall se flaggea sólo con n mínimo 15.

Sin flag pero fuera de banda: Isluga V375 0,51x (n=44), Láscar V375 0,552x (n=25), Láscar V750 0,275x (n=7), Lastarria V375 0,664x (n=15). Están en la lista de sub-banda conocida del script (`UNDER_BAND_KNOWN`, sólo flaggean si superan 1,4x), igual que en #864.

Falsas publicaciones (no generan alarma; ventana 2026-09-01 a la fecha del reloj; denominador = pasadas negativas limpias, es decir pasadas donde MIROVA miró y no vio nada): reloj 10-25 MODIS 1,0 % de 1.142, V750 0,8 % de 1.649, V375 4,0 % de 1.100. En #864 salió 1,1 % de 658, 1,1 % de 949 y 3,0 % de 656. Los porcentajes se parecen y los denominadores no: pasaron de 658/949/656 a 1.142/1.649/1.100. Es el mismo efecto de instrumento (abajo), no más pasadas del volcán.

## Qué es del volcán y qué es del instrumento

Descompuse con 4 corridas del código de main: la réplica de #864 (frontera vieja, reloj 10-19, `F_1019`), sólo frontera nueva (`N_1019`), sólo reloj nuevo (`F_1025`) y ambas (`A_1025`). Las cuatro están en `res\`.

| flag | #864 réplica (F_1019) | sólo frontera (N_1019) | sólo reloj (F_1025) | ambas (A_1025) | lectura |
|---|---|---|---|---|---|
| recall V750 | 73,3 % n=30 | 70,9 % n=55 | 75,0 % n=32 | 72,9 % n=48 | **Instrumento.** Desglose en A_1025: 13 noches perdidas de 48; 5 de 16 antes del 18-sep y 8 de 32 desde el 18-sep. Las 8 de después son las de #864 (8 de 30): las 2 noches nuevas de VIIRS 750 acertaron. |
| Tupungatito V375 | 0,266x n=8 | 0,489x n=22 | 0,281x n=9 | 0,448x n=19 | **Instrumento.** Las 10 noches de antes del 18-sep tienen mediana 0,582x; las 8 de 18-sep a 19-oct, 0,266x; 1 noche nueva, 0,824x. No es mejora. |
| Puyehue V750 | sin flag (n=4) | 0,576x n=11 | 0,375x n=5 | 0,517x n=10 | **Mixto.** Aparece cuando n pasa de 4 a 5 o más por cualquiera de las dos vías: 5 noches de antes del 18-sep (mediana 0,659x) o 1 noche nueva (razón 3,939x, atípica). |
| Chillán V375 | 0,65x n=16 | 0,65x n=16 | 0,662x n=19 | 0,662x n=19 | **Volcán/datos.** La frontera no lo toca (Chillán no tiene noches comunes con MIROVA antes del 18-sep). Las 3 noches nuevas (20 al 25-oct) tienen mediana 1,89x. |
| Chillán V750 | 0,687x n=13 | 0,687x n=13 | 0,694x n=14 | 0,694x n=14 | **Volcán/datos.** 1 noche nueva con 0,7x. |
| Chillán MODIS | 0,485x n=7 | 0,485x n=7 | 0,485x n=7 | 0,485x n=7 | Sin cambio: ninguna noche MODIS nueva de Chillán con alerta de MIROVA desde el 10-19 en estos datos. |
| 5 protegidas | 5 flags (6 sin publicar, una rotulada C0 que no flaggea) | 6 (aparece Láscar V375 2026-08-22 05:06, 1,65 MW) | 5 | 5 | **Instrumento y ventana.** Esa de Láscar existía en #864 pero estaba rotulada C0 y no flaggeaba; con la frontera nueva sí cuenta, y sale de la ventana el 10-25. Para el lunes ya no está. |

En una frase para el OVDAS: lo que se lee distinto en el issue del lunes (n más grandes, Tupungatito de 0,27x a 0,45x, un volcán más en la lista) se debe a que el audit ahora juzga 60 días con K y antes juzgaba 31. Lo que cambió en los volcanes en esta semana es pequeño. Con n=19 y n=14 en Chillán, un par de noches fuertes más sacarían los dos flags de Chillán V375 y V750 de la lista; eso sería ruido de n chico, no recuperación (causa del déficit sin medir, como dice #864).

Otro efecto de instrumento, de método y no de frontera: los records anteriores al 18-sep ahora llevan la marca de K (el audit cuenta 3.442 records de K con fecha anterior a la frontera vieja; reproceso #883; `_detector` asigna K por la presencia de `codigo_sha`), por eso el denominador de falsas de V375 con el mismo reloj del 10-19 subió de 656 (corrida real) a 993 (réplica con datos de hoy). Leído en `scripts/auto_audit_weekly.py:423-440`; no medí qué fracción de esos records aportó el reproceso.

## Denominadores y ventanas (A90, A104)

- Ventana de recall y magnitud: 60 días hacia atrás desde la fecha del reloj, ambos extremos incluidos (61 fechas): 10-25 es 2026-08-26 a 2026-10-25; 10-26 es 2026-08-27 a 2026-10-26. Cobertura propia 98,4 % (60 de 61 días con datos) con reloj 10-25 y 96,7 % (59 de 61) con reloj 10-26.
- Ventana de falsas: desde 2026-09-01 (`INICIO_REGIMEN_FALSAS`, después de #535 de 2026-08-28 23:00 UTC y #571) hasta la fecha del reloj. Recall y magnitud NO se recortan en #535: la ventana del lunes 26 todavía incluye 08-27 y 08-28, antes de #535. El propio script dice que el recall no se movió con #535. Esa ventana deja de cruzar #535 en la corrida del lunes 2-nov.
- Referencia de MIROVA: tabla y OCR al 2026-10-25, última fecha del CSV consolidado 2026-10-24 (`gt_stale_dias` = 1 con reloj 10-25). La advertencia A119 de ventana que pisa dos tramos con defectos conocidos se imprime tal cual en stderr (`res\A_1025.err`); decide la tabla y el OCR.
- Alertas diurnas de MIROVA excluidas por la regla del pipeline: 31 (reloj 10-25), 33 en la corrida real de #864.

Desglose por volcán de las 13 noches de V750 que no tienen cúmulo de cráter (A_1025, desde el script `desglose.py`): Láscar 5 de 13, Isluga 4 de 4, Puyehue 2 de 12, Chillán 1 de 15, Villarrica 1 de 2; todas con VRP de MIROVA entre 0,16 y 0,38 MW. No saqué conclusión sobre la causa (A8, A54).

## Riesgos para el lunes

1. **MODIS recall**: 69,2 % con n=13 (reloj 10-25 y 10-26); con la frontera nueva en la réplica del 10-19 había salido 64,3 % con n=14. La banda es 95,0 % con n mínimo 15. Dos noches más con alerta de MIROVA para MODIS bastan para que aparezca un flag de recall MODIS que hoy está oculto por n bajo. No sería una caída del volcán ni del detector. Las 4 noches MODIS sin cráter son Láscar 10-08, Chillán 09-29, Chillán 10-12 (2,18 MW) y Villarrica 09-25.
2. **Chillán V750 a 0,006 de la banda** (0,694 contra 0,7): un solo dato puede sacarlo de la lista o dejarlo.
3. **Hora real del run**: probablemente entre 16 y 19 UTC del lunes, no 09:00. Si el NRT va atrasado y el último día con datos queda 2 días atrás, el veredicto es `DEGRADADO` y abre `⚠ Auto-audit semanal DEGRADADO: 2026-10-26` sólo si no hay otro DEGRADADO abierto; con ese veredicto el cuerpo trae los flags sin interpretar. El NRT va sano: los últimos 5 runs de `nrt.yml` están en success o en cola (`gh run list -R MendozaVolcanic/VRP-chile --workflow nrt.yml`, 2026-10-25 02:1x UTC).
4. **#864 queda abierto en paralelo**: el workflow nunca comenta ni cierra issues anteriores en la rama FUERA_DE_BANDA. Los issues anteriores (#779, #757, #661...) se cerraron a mano. Habrá dos issues abiertos con los mismos 10 flags, y el nuevo no menciona que la frontera cambió, así que n=48 contra n=30 se lee como si el volcán hubiera cambiado. Esto se arregla con un comentario a mano (no lo hice), no con código.
5. **Referencia desactualizada en el repo**: el snapshot commiteado en main (`registro_vrp_consolidado.csv`) termina el 2026-10-19; el workflow lo refresca antes de auditar. Con el snapshot viejo (corrida `R_1025`) el resultado sale 71,7 % n=46 en V750 y Chillán V375 n=17, y Tupungatito V375 n=18 con 0,41x: la sensibilidad a la referencia es de unas 2 noches.

## SIN DATO

- La unión histórica del lunes (`--union-historica`, hasta 25 minutos, regenera con la API): puede agregar filas que el consolidado perdió entre el 10-19 y el 10-26. Dirección del efecto: SIN DATO.
- Datos nuestros y de MIROVA del 25 y el 26-oct: no existen todavía en mi copia.
- Python 3.11 y Ubuntu del runner contra Python 3.12.10 y Windows local, y la versión de node del runner (local v22.16.0): no comparé. `git archive` aplicó conversión CRLF a los archivos de texto del árbol A; Python los lee igual.
- No corrí las pruebas de #900 (`tests/test_auto_audit_cese_plataforma_s161.py` y las otras); sólo medí la simulación. La revisión previa reporta 135 y 57 passed sobre otro head.
- Causa del déficit de Chillán, de Tupungatito y de V750: sin medir, como dice #864. Este informe no la mide.

## Archivos

Todos bajo `C:\Users\nmend\AppData\Local\Temp\claude\C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile\a3efc9fd-8a35-470a-aad1-531abaec64d8\scratchpad\vuelta3\autoaudit_lunes`:

- `INFORME.md` (este), `run_sim.py` (reloj fijo), `desglose.py` (noches y razones por período), `simular_issue.sh`, `paso_issue_A.sh`, `paso_issue_B.sh`.
- `res\A_1025`, `A_1026` (main), `B_1025`, `B_1026` (#900), `F_1019` (réplica #864), `N_1019`, `F_1025`, `R_1025`, `real_864` (el latest.json real del 10-19, commit `2e1bc0e31`); cada una con `.json` y `.txt` (`.err` con la advertencia de referencia).
- `res\issue_A_1025.txt`, `issue_B_1025.txt`, `issue_A_1026.txt`, `issue_B_1026.txt`: título y cuerpo simulados.
- Árboles extraídos: `main\` (1,1 GB, archivo completo de origin/main), `pr900\`, `main_fOld\` (frontera 2026-09-18), `main_refC\` (snapshot de referencia commiteado). Se pueden borrar.
