# S131 · Pendientes publicados + infraestructura NRT/CI/seguridad

> Eje de esta auditoría (regla C del protocolo): empezar por los pendientes que
> `docs/AUDIT_S128.md` §8 dejó abiertos, más la salud de infraestructura (NRT/CI/
> seguridad/tests/disco) que ninguna auditoría reciente había vuelto a medir de punta
> a punta. Todo lo de abajo tiene comando + salida verificado hoy (servidor: **2026-09-02
> 20:08:43 UTC**, confirmado con `gh api -i`, A86). Repo local estaba **63 commits detrás**
> de `origin/main` — verificado que los 63 son sólo datos NRT/CSV (`git diff --stat HEAD
> origin/main -- .github/workflows/ pipeline/ docs/ CLAUDE.md` → vacío), así que el análisis
> de código es válido igual.

## Resultado primero

- **10 pendientes de S128 §8**: **2 cerrados** (#8 A/B GAP#A, #9 D18 ROI1 — ambos ya
  cerrados en S129-S130 con script y veredicto reproducibles), **1 resuelto en esta
  sesión** (#10 saturación M15, con cita verbatim), **7 siguen abiertos**, dos de ellos
  (#4 inyección de comandos, #5 timeout `nrt-retry.yml`) **exactamente en el mismo estado
  que en S128**, verificado con script, no con memoria.
- **NRT**: **100 % de éxito** en los últimos 7 días (27/27 runs) y **0 jobs fallidos** en
  una muestra de 55 (5 runs × 11 volcanes). Pero el **margen contra el timeout es más
  angosto de lo que el guard automático puede ver**: el peor job observado tardó
  **56,0 min contra un timeout de job de 60 min** (margen 7 %, muy por debajo del 30 %
  que pide A15) — y el guard que debería atraparlo (`test_guard_timeout_vs_ventana_s129.py`)
  **se salta `nrt.yml` a propósito** porque no puede parsear sus fechas dinámicas.
- **Seguridad**: no hay credenciales en texto plano en el árbol del repo (sólo el
  placeholder de `.env.example`). El PAT vivo en `~/.claude/settings.json` (fuera del
  repo, global) **sigue ahí** — alerta para Nicolás, sin imprimir el valor.
- **7 workflows, 31 ocurrencias** de interpolación directa de `github.event.inputs` dentro
  de bloques `run:` — el número exacto de S128, sin cambios, con `nrt.yml` (el cron que
  corre 12×/día con los secrets de NASA) entre ellos. El fix ya está en producción como
  patrón, sólo no se aplicó retroactivamente: `reproc-s129-ab-fondos.yml` y
  `reproc-s130-d18-roi1.yml` pasan todo por `env:` y el segundo lo dice en un comentario
  citando a S128.

---

## Parte 1 — Los 10 pendientes de AUDIT_S128 §8

| # | pendiente | veredicto | evidencia |
|---|---|---|---|
| 1 | A54 (95,4 % FP físicos reales) sin respaldo reproducible | **ABIERTO**, sin cambios | ver "Qué haría falta" abajo — no ejecutado, por instrucción |
| 2 | D13 (31 % vs 27,8 %) — denominador no declarado | **ABIERTO**, sin cambios | ver "Qué haría falta" abajo — no ejecutado, por instrucción |
| 3 | A/B del filtro de cenit (3 brazos, criterio pre-registrado) | **ABIERTO, con avance** | `docs/s131/REMUESTREO_LEY_DE_AREA.md` (hoy, antes de este agente) reencuadró el mecanismo: no es un filtro de cenit, es remuestreo/ley de área. Midió que el factor requerido (hasta 2,93× a 60°) entra bajo el disponible del ATBD (4,38×) — condición necesaria, no el A/B con reproceso real. El A/B en sí **no se corrió** |
| 4 | Inyección de comandos en 7 workflows | **CONFIRMADO, sin cambios** | script `experiments/_s131_audit/pendientes_infra/scan_injection.py`: **7 workflows, 31 ocurrencias**, idéntico a S128 |
| 5 | `nrt-retry.yml` sin `timeout-minutes` | **CONFIRMADO, sin cambios** | `grep -n "timeout-minutes" .github/workflows/nrt-retry.yml` → vacío |
| 6 | `mirova_center_lat/lon` por volcán×sensor (offsets km en Tupungatito/PP) | **ABIERTO, sin cambios** | `git log origin/main --grep="mirova_center" -10` → último commit relacionado es de S89, nada después de S128 |
| 7 | Duplicados del corpus + `git gc` | **PARCIAL — el `git gc` YA SE CORRIÓ** | `git count-objects -v`: **2 packs, 0 garbage**, `.git` = **6,5 GB** (era 10,6 GB/33 packs/1,57 GiB garbage en S128). Los duplicados de `documentacion/` (101,9 MB, 8 grupos) siguen sin decisión — es local-only, gitignoreado |
| 8 | A/B del GAP #A (encender `ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK`) | **CERRADO (S129-S130)** | `docs/s130/AB_FONDOS_SIN_SUSTRATO.md` + script `experiments/_s130_ab_sustrato/medir_sustrato_k1.py` (confirmado que existe y el doc cita sus números). Refutado por falta de sustrato, no por daño ni beneficio: K1 se cruza en 0,09 % MODIS / 0,12 % V750 / 1,36 % V375 |
| 9 | ROI1: caja de 5 km del paper vs círculo 3-20 km nuestro | **CERRADO (S130)** | `docs/s130/PREREGISTRO_AB_D18.md` + `docs/s130/VEREDICTO_AB_D18.md`, run `33456630043` (12/12 verdes). NO ADOPTAR: 0-0,8 % de detecciones perdidas, 0 noches MIROVA, la caja redistribuye (166 más, 200 menos) en vez de recortar |
| 10 | Saturación M15: 423 K nuestro vs 343 K Campus 2022 | **RESUELTO HOY, con cita verbatim** | ver sección dedicada abajo |

### Pendiente #10, resuelto — saturación M15

`pipeline/process_viirs_mod.py:193-196`:
```python
# M15 (10.76 µm TIR) sat ~423 K análogo a I05. Quality flags bit-2 schema
BT_LUT_MAX_MBAND = {"M13": 634.0, "M15": 423.0}
```

El comentario ya confiesa el problema: **423 K es el techo de I05, una banda distinta**
(I-band, no M-band). Verificado contra `documentacion/VIIRS_L1B_UserGuide_Aug2021.pdf`
(`pdftotext -layout`, tabla "I-bands 04-05 Brightness Temperature LUT"): I-band 05
Max = **423,33734 K**. Ese número es real — pertenece a otra banda.

La tabla correcta, "M-bands 12-16 Brightness Temperature LUT" del mismo UserGuide:

| banda | Max LUT (UserGuide, techo físico de la calibración) |
|---|---|
| M12 | 372,42 K |
| M13 | 665,92 K |
| M14 | 355,18 K |
| **M15** | **374,60 K** |
| M16 | 375,88 K |

Y Campus et al. 2022 (`documentacion/campus2022_extracted.txt:375-379`), Tabla 1,
"TMAX (SNR-NEdT on orbit)":
> *M-13 … TMAX 634 K (0.04) … M-15 … TMAX 343 K (0.03)*

Son dos magnitudes distintas por diseño: el LUT max es el techo duro de la tabla de
calibración (por encima de eso el valor se satura/trunca); el TMAX de Campus es el punto
donde la especificación SNR-NEdT deja de garantizarse — más conservador, y es la fuente
que **ya** usamos, textual, para `M13 = 634.0`. Nuestro `M15 = 423.0` no es ninguno de
los dos: es I05 mal copiado.

**Recomendación**: `M15 = 343.0`, por consistencia con la misma fuente ya citada para
M13 (Campus 2022 Tabla 1), documentando 374,6 K (UserGuide) como el techo físico de la
LUT. Jerarquía A35 (UserGuide manda sobre paper) no cambia la recomendación aquí porque
el UserGuide y Campus miden cosas distintas — el reemplazo correcto sigue siendo el
número que juega el mismo rol que 634 K juega para M13.

**No lo apliqué**: toca `pipeline/process_viirs_mod.py`, que cae bajo A45 (tag defensivo
+ confirmación explícita de Nicolás antes de tocar código de detección/magnitud
operacional).

### #1 y #2 — qué haría falta (no ejecutado, por instrucción del prompt)

- **A54** (95,4 % de los "FP" son rasgos físicos reales): la clasificación a/b/c/d de S86
  fue un juicio humano por record, con conocimiento del volcán, y **no hay campo en el
  schema** que la persista. Haría falta: (a) definir un criterio explícito y replicable
  por categoría, (b) re-etiquetar una muestra estratificada por volcán, (c) persistir la
  etiqueta en el JSON (o en un CSV aparte con `record_id`), (d) recién ahí un script puede
  recomputar el 95,4 %. Sin la etiqueta persistida, cualquier "confirmación" de A54 sería
  circular.
- **D13** (31 % vs recálculo de 27,8 %): el recálculo no declaró su denominador. Haría
  falta encontrar o rehacer ese script con el denominador explícito en el output (A90) y
  compararlo contra la afirmación original con la misma ventana temporal — sin eso
  cualquier "confirmación" repite el mismo error que A90 documenta.

### Lo que NO hay que reabrir (repetido desde S128, sigue vigente)

Confirmado sin cambios: el TIF público de MIROVA sigue sin poder adjudicar detección
(§3 S128), el área nadir fija sigue respaldada por Campus 2022 Eq.1, y la grilla de
MIROVA sigue centrada en la cumbre (no en una esquina).

---

## Otros pendientes que quedaron abiertos al cierre de S129/S130 (fuera de la lista de 10)

- **Suma-vs-clúster**: S129 midió que MIROVA suma todos los píxeles que alertó (no
  publica un solo clúster como nosotros) — 3 brazos: clúster 0,730 / suma <5km 0,798 /
  scene-wide 0,924. S130 lo dejó exactamente donde S129 lo dejó: **sin decisión**.
- **El remuestreo** (D5/gradiente cenital): confirmado en VIIRS (ratio 0,740→0,253 con el
  ángulo, MIROVA plano), **no probado en MODIS** (bins no monótonos, n=17-21). Hoy mismo,
  antes de este agente, `docs/s131/REMUESTREO_LEY_DE_AREA.md` avanzó el mecanismo
  (equivalencia área↔remuestreo para la magnitud, bow-tie ya resuelto en VIIRS por el
  sensor) pero **no implementó nada**: el brazo fiel es bow-tie+regrid en ese orden para
  MODIS, cirugía de núcleo, no un flag.
- **`mirova_center` por volcán×sensor** — mismo ítem que el #6 de la tabla.
- **Corpus duplicado / `git gc`** — el `git gc` ya se hizo (ver #7); los duplicados de
  `documentacion/` siguen esperando el ok de Nicolás.

---

## Parte 2 — Infraestructura

### a. NRT — éxito, duración, timeout, latencia

**Éxito** (`gh run list --workflow=nrt.yml --limit 40 --json conclusion,createdAt,updatedAt`,
ventana de 7 días desde el servidor):

```
Ultimos 7 dias (completados): 27
Exito ultimos 7d: 27/27 = 100.0%
```

**Duración a nivel de job** (lo que realmente compite contra el `timeout-minutes: 50` por
step y `timeout-minutes: 60` por job) — muestreado sobre 4 runs × 11 volcanes = 44 jobs
(`gh run view <id> --json jobs`):

```
Peores 5 jobs:
  56.0 min  success  process (Villarrica)          2026-09-02 08:24 UTC
  54.2 min  success  process (PlanchonPeteroa)     2026-09-02 08:24 UTC
  50.3 min  success  process (Llaima)              2026-09-01 22:23 UTC
  50.0 min  success  process (Copahue)             2026-09-01 22:23 UTC
  49.4 min  success  process (Llaima)              2026-09-02 14:05 UTC
No-success jobs: 0 de 44
```

**El hallazgo**: el job corre **dos steps secuenciales** (`mirova_equivalent` +
`experimental`), cada uno con su propio `timeout-minutes: 50` (`.github/workflows/nrt.yml:173,193`),
pero el **job entero** tiene `timeout-minutes: 60` (línea 69) — no 100 (50+50). El job-level
timeout es el que manda en la práctica, y el peor caso medido hoy (**56,0 min**) le deja
sólo **4 minutos, un margen del 7 %**. A15 pide margen ≥30 % (`timeout ≥ duración×1,3`);
con el peor caso observado, un timeout defendible sería **≥73 min** (56×1,3). Ningún job
falló todavía porque ninguno llegó a los 60 — pero el margen es mucho más angosto de lo
que "0 fallos en 7 días" sugiere.

**El guard automático no lo puede ver**: los 3 tests skipeados de la suite completa son
justo de este guard (`tests/test_guard_timeout_vs_ventana_s129.py`), y uno de los tres
saltados es **`nrt.yml`** — "no declara fechas por defecto parseables". El guard existe,
está bien diseñado para workflows con ventana fija, y **no cubre precisamente el cron que
importa más**.

**Latencia pasada→dato** (últimos 20 commits "NRT update", comparando el timestamp del
commit contra el `datetime_utc` máximo del JSON que ese commit agrega —
`git show origin/main:<path>` por commit):

```
n=20  p50=483.6 min (8.1 h)  p90=531.4 min (8.9 h)  max=793.6 min (13.2 h)  min=174.9 min (2.9 h)
```

⚠️ Esto **no es latencia pura de NASA**: mezcla la latencia real de LANCE (~3h, per
CLAUDE.md) con la cadencia de nuestro cron (cada 2h) y con que los overpasses de
VIIRS/MODIS sobre Chile no ocurren cada 2h — así que un commit puede estar "esperando" al
siguiente ciclo de cron después de que el dato ya estaba disponible. El número es real
(commit menos dato), pero no aísla dónde vive el retraso.

### b. Pipelines zombie

8 workflows con cron activo fuera de `_archive/` (`grep -l "cron:" .github/workflows/*.yml`):
`audit-weekly`, `nrt-healthcheck`, `nrt-monitor`, `nrt-retry`, `nrt`, `pages-deploy`,
`reproc-watchdog`, `sync-mirova-csv`. **Los 8 corrieron en verde en las últimas horas o
el último día**, y para los que producen commits (`nrt`, `sync-mirova-csv`,
`audit-weekly`) los commits están al día — **ninguno zombie**.

`sync-mirova-csv.yml`: sigue sincronizando. Último commit `data(mirova): sync CSV...`
en `2026-09-02T18:41:10Z`, con dato satelital hasta `2026-09-01 07:35`.

**El canal OCR partido (A17) sigue existiendo exactamente igual**:

```
data/mirova_reference/registro_vrp_ocr.csv                       235 filas, max 2026-03-28 (CONGELADO)
data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv     907 filas, max 2026-08-31 (VIVO)
```

**Pero la sub-afirmación específica de A17 sobre quién lo consume está OBSOLETA** (T9/A89):
CLAUDE.md dice *"`scripts/build_c2ab_windows.py:55` consume el congelado"*. Hoy esa línea
es un **comentario** que documenta que el bug ya se arregló:

```python
# scripts/build_c2ab_windows.py:55-64
# Antes `CONS` apuntaba al snapshot y `OCR` a una copia suelta un nivel más arriba que
# estaba construyendo las ventanas del A/B con cinco meses menos de canal OCR: 844...
_SNAP = REPO / "data" / "mirova_reference" / "mirova_v1_snapshot"
OCR = _SNAP / "registro_vrp_ocr.csv"     # ← apunta al VIVO, no al congelado
```

El split de archivos sigue siendo real (el congelado sigue en disco, sin usarse), pero
el consumidor citado como roto ya no lo está — línea movida de 55 a 64, y apunta al
snapshot vivo. Vale corregir CLAUDE.md tachando esa sub-frase, no la observación entera.

### c. Frescura del ground truth

```
latest_consolidado.csv (local)     : 35.204 filas, max satelital 2026-09-01 07:35
                                      último sync commit: 2026-09-02T18:41:10Z
Mirova-v1 (remote, gh api)         : último commit 2026-09-02T20:11:10Z
                                      ("Auto: Sincronización de datos e imágenes")
```

Sano: el scraper remoto está vivo casi al minuto del momento de esta auditoría, y
nuestro CSV sincronizado hace ~1,5 h respecto del servidor.

### d. Seguridad

- **Sin credenciales en texto plano en el árbol**: `git grep -nE "ghp_|github_pat_|EARTHDATA_PASSWORD\s*=|AKIA|api[_-]?key\s*="` sobre todo el repo (excluyendo PDFs) → **una sola coincidencia**, `.env.example:25: EARTHDATA_PASSWORD=your_password_here` (placeholder, no un valor real).
- `.gitignore` cubre `.env` (línea 12) y `documentacion/` (línea 2). `.netrc` no está en el
  árbol del repo (vive en el home del usuario, fuera del alcance de este `.gitignore` —
  no aplica).
- **Secrets**: `gh secret list` → `EARTHDATA_PASSWORD`, `EARTHDATA_TOKEN`,
  `EARTHDATA_USERNAME`. Los workflows sólo referencian esos tres más
  `secrets.GITHUB_TOKEN` (automático) — **cero secrets referenciados sin existir**, así
  que no hay riesgo A56/A60 de "resuelve a string vacío".
- **`permissions:`**: presente a nivel de job en 16 de 17 workflows relevantes (el
  patrón `contents: read` + lo mínimo necesario por workflow, ej. `nrt-retry.yml` sólo
  agrega `actions: write` para poder relanzar). El único sin bloque explícito es
  `tests.yml` (hereda el default del repo) — riesgo bajo, sólo corre pytest.
- **ALERTA para Nicolás** (no es hallazgo nuevo, pero sigue vigente y CLAUDE.md pide
  avisarlo cada sesión): `~/.claude/settings.json` (global, fuera de este repo) **todavía
  tiene un token con forma de PAT de GitHub**. No se imprime el valor. Pendiente: rotarlo
  y moverlo a variable de entorno.

### e. Tests

```
python -m pytest -q --no-header -p no:cacheprovider
1039 passed, 3 skipped in ~16-18s
```

Coincide exacto con el baseline citado en el prompt. Los 3 skips, los tres del mismo
guard:

```
SKIPPED tests/test_guard_timeout_vs_ventana_s129.py:102: backfill-tier-a.yml no declara fechas por defecto parseables
SKIPPED tests/test_guard_timeout_vs_ventana_s129.py:102: nrt.yml no declara fechas por defecto parseables
SKIPPED tests/test_guard_timeout_vs_ventana_s129.py:102: reproc-chunked.yml no declara fechas por defecto parseables
```

Diseño correcto (esos 3 workflows toman fechas por `workflow_dispatch`, no tienen
ventana fija que el guard pueda calcular) — pero es exactamente por eso que el margen
angosto de `nrt.yml` (item a) no tiene un guard que lo cubra hoy.

**Profile-awareness**: 25 de 129 archivos de test referencian `VRP_PROFILE` o
`monkeypatch` de perfil. De los 14 que importan `process_modis`/`process_viirs`/
`process_viirs_mod` directamente, 11 tienen señal explícita de profile-awareness; los 3
que no (`test_corona_single_pixel_coherencia_s127.py`, `test_local_kernel_modis.py`,
`test_vrp_tir_consistency_gate_f46.py`) se revisaron uno por uno: son tests unitarios de
una función puntual con inputs sintéticos (no corren el pipeline completo bajo un
perfil), o están marcados `xfail` a propósito pendientes de un fix documentado (F46). No
hay ninguno que mida en silencio un estado que no es el de producción.

### f. Disco y repo

```
.git           6,5 GB   (2 packs, 0 garbage — git count-objects -v)
data/          1,1 GB
documentacion/ 651 MB   (gitignoreado, sólo local)
experiments/   1,4 GB
```

El `git gc` que S128 dejó pendiente **ya se corrió**: de 33 packs/10,6 GB/1,57 GiB de
basura a **2 packs/6,1 GB de pack/0 garbage**. `.git` total bajó de 10,6 a 6,5 GB.

**Inventario de los directorios untracked** (ninguno tocado, sólo inventariado):

| directorio | tamaño | qué es | recomendación |
|---|---|---|---|
| `experiments/_s104_roi_probe/{anchor_a,anchor_b,baseline_mir,local_k20,local_k25,local_k30,nti_integral}/` | **~113 MB** | JSON de salida (records por volcán) de un A/B de ancla/kernel local, fechados **2026-08-28**. No están cubiertos por el `.gitignore` de `experiments/**/_dl_*` (eso son sólo cachés de descarga cruda, que sí están gitignoreados y no aparecen como untracked). Son reproducibles desde el script que los generó, no son datos únicos | huérfanos, candidatos a borrar tras inventario A38 — no son output de este agente, quedaron de una sesión anterior |
| `experiments/_s131_remuestreo/` | 24 KB | `factor_requerido.py/json` + `ley_atbd.py/json` — el trabajo de **hoy** que respalda `docs/s131/REMUESTREO_LEY_DE_AREA.md` | activo, probablemente se commitea al cerrar S131 — no tocar |
| `experiments/_s131_audit/pendientes_infra/` | — | los scripts de este agente (ver abajo) | mío, parte del entregable |

---

## Recomendaciones, priorizadas

**Mecánicas, bajo riesgo, fuera de `pipeline/`, se pueden hacer hoy:**

1. **Fix de inyección en los 7 workflows** (#4). El patrón ya existe en el repo
   (`reproc-s129-ab-fondos.yml`, `reproc-s130-d18-roi1.yml`): mover cada
   `${{ github.event.inputs.X }}` usado dentro de `run:` a un bloque `env:` del step y
   referenciarlo como `"$X"` en el shell. Orden por criticidad: `nrt.yml` primero (corre
   12×/día con secrets de NASA), después `reproc-chunked.yml` (mixto: ya tiene `env:`
   para secrets pero no para `profile`/`start`/`end`/`volcanoes`), después
   `backfill-geometry.yml`, `backfill-tier-a.yml`, `reproc-s120-eq16-villarrica.yml`,
   `reproc-s124-ndc-focus.yml`, `reproc-s124-villarrica-op-ab.yml`.
2. **`timeout-minutes` en `nrt-retry.yml`** (#5). El job sólo hace `gh run list`/
   `gh workflow run` — un timeout de 10-15 min es holgado y cierra el gap con A15.
3. **Revisar el timeout de job de `nrt.yml`** (hallazgo nuevo de esta sesión, item 2a):
   subir `timeout-minutes: 60` del job `process` a algo como **75-90 min** (1,3× el peor
   caso observado de 56 min), o separar los dos steps de perfil en jobs distintos de la
   matrix. Es config de workflow, no de `pipeline/`, pero al ser el cron operacional
   igual amerita el mismo cuidado que A45/A59 piden — bajo riesgo porque sólo ensancha
   un margen, no cambia lógica.
4. **Guard para el hallazgo 3**: extender o complementar
   `tests/test_guard_timeout_vs_ventana_s129.py` para que pueda evaluar `nrt.yml` contra
   su duración observada real (vía `gh run` histórico o un número fijo documentado), en
   vez de saltarlo. Cierra el hallazgo con test, como pide la Regla B del protocolo.
5. **Corregir CLAUDE.md A17**: tachar (no borrar) la sub-frase sobre
   `build_c2ab_windows.py:55` — el consumidor ya está arreglado, el split de archivos
   sigue existiendo.

**Requieren decisión de Nicolás (no mecánicas):**

6. Duplicados de `documentacion/` (101,9 MB, 8 grupos) — inventario ya en
   `docs/s128/CORPUS_HIGIENE.md`, falta el ok explícito (A38).
7. Borrar (o no) los ~113 MB huérfanos de `experiments/_s104_roi_probe/` listados arriba
   — mismo protocolo A38.
8. Fix de M15 (#10) — toca `pipeline/process_viirs_mod.py`, cae bajo A45: tag defensivo +
   confirmación explícita antes de cambiar `BT_LUT_MAX_MBAND["M15"]` de 423.0 a 343.0.

**No accionables hoy, quedan como pendientes puros:**

9. A54 (#1) y D13 (#2) — ver "qué haría falta" arriba.
10. `mirova_center` por volcán×sensor (#6), suma-vs-clúster (S129/S130), el A/B del
    remuestreo con reproceso real (bow-tie+regrid MODIS, #3).

---

## Scripts de este agente

`experiments/_s131_audit/pendientes_infra/`: `scan_injection.py` (detección de
inyección real dentro de `run:`), `analizar_nrt.py` + `latencia_nrt.py` (éxito/duración/
latencia NRT desde `gh run list` y `git show origin/main`), y los JSON crudos de
`gh run view --json jobs` de 5 corridas de `nrt.yml` usadas para el análisis de
duración por job.
