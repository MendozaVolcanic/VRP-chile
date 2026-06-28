# Design — A/B estratificado de los gates intra-radio C2 (S118)

**Fecha:** 2026-06-28 · **Sesión:** S118 · **Estado:** DISEÑO (aguarda OK de Nicolás
antes de implementar — A45) · **Gate brainstorming:** superpowers-brainstorming
(este doc es el output) · **Frente:** reabrir Test1/fondo-local → C2 (orden S105).

---

## 1. Problema (fenómeno físico → mecanismo del pipeline)

MIROVA **no cerca por geografía**: detecta por NTI contextual (Tests 1/2/3) en toda
la escena y reporta el cluster que su selección elige. Nuestro pipeline tiene en
cambio dos **cercas** en el `inner_radius` que descartan píxeles de fuera **antes**
de clusterizar:

| Gate (flag) | Sensor | Qué hace | file:line |
|---|---|---|---|
| `enable_path_d_intra_radio_gate` (yaml:188) | **MODIS only** | SUPRIME toda la máscara Path-D (dNTI 8-vec) fuera del inner | `path_d_intra_radio.py:44-49`; `process_modis.py:563-570` |
| `enable_second_pass_intra_radio_gate` (yaml:207) | **MODIS + VIIRS** | PRESERVA el first-pass; recorta solo la recaptura NUEVA del second_pass fuera del inner | `second_pass_intra_radio.py:65-72`; `process_modis.py:788-795`, `process_viirs.py:1083`, `process_viirs_mod.py:760` |

Ambos están **ON** en `mirova_equivalent.yaml`. S86 los marcó **anti-patrón (A55)**:
no están en papers MIROVA core, y el frontend `mirovaEqVrp` ya hace la supresión
**visual** desde S33. La auditoría S116 (`docs/AUDIT_S116_C2_GATES.md`) refinó el
framing: la redundancia con el frontend es **parcial** (vista vs dato), y el impacto
de los gates sobre los records es **bimodal**:

| Régimen | Volcanes (%TP preservado) | Naturaleza de lo preservado |
|---|---|---|
| **Focal / desértico** | Láscar 49 %, Lastarria 46 % (Lazufre), Isluga 36 %, PP 29 %, PCC 27 % (lacolito) | **cat-b REAL** (focos sub-umbral que MIROVA cuantifica) |
| **Cumbre nevada** | Llaima 0.4 %, Copahue 1.4 %, Villarrica 2 %, NdC 5 %, Tupungatito 22 % | **artefacto** topográfico/cirrus (A55/A69) |

**El gap que S116 NO pudo cerrar:** midió lo que el gate **PRESERVA** (intra-radio),
no lo que **REMUEVE** (extra-radio, enmascarado antes de contar → invisible en el
JSON). Y no pudo ver el efecto de **selección de cluster** (A18: el reproc real
re-elige el cluster desde cero; apagar la cerca devuelve píxeles al pool y un cluster
lejano puede robarle el primario al cráter). **Solo un reproc real gate-ON vs
gate-OFF lo mide.** Eso es este A/B.

El discriminante físico per-record está **agotado** (A83, `AUDIT_S116_FOLLOWUP.md`):
el mejor escalar (`test1_k_observed`, AUC 0.859) es régimen-dependiente y un cut
global destruye 14-16 % del cat-b real. **Solo el eje espacial separa.** Por eso el
A/B no busca un umbral nuevo — mide remoción y robo de cluster en el eje espacial.

---

## 2. Gate MISSION (3 preguntas) — desenlaces admisibles

Por gate (cada uno es independientemente un anti-patrón → la decisión se toma por
separado para cada uno):

| | P1 papers core | P2 cierra divergencia | P3 alineación infra | Veredicto |
|---|---|---|---|---|
| `path_d_intra_radio` | NO | NO (D9 cerró por cap C + nadir/focal) | GRIS, refutada | anti-patrón |
| `second_pass_intra_radio` | NO (docstring admite drift vs Coppola §347-356) | NO | GRIS, refutada | anti-patrón |

**Desenlaces admisibles del A/B (binario MISSION-puro, decidido por Nicolás S118):**
- **Gate → OFF** (clon-literal puro; remueve el anti-patrón).
- **Gate → ON uniforme** (excepción documentada, si el clon-literal puro pierde
  posición del cráter por robo de cluster).

**EXCLUIDO: per-régimen / per-volcán** (ON nevados / OFF focales). MISSION línea 77
lo prohíbe explícitamente: *"MIROVA NRT no conmuta de método por volcán ni por
régimen térmico"*. Es el mismo trap que la Eq.16 por-volcán (anti-patrón S99, movido
a beyond-MIROVA). Aunque S116 lo listó como "desenlace probable", **no es admisible**.

**A45 — qué toca este A/B:** profiles (config), un workflow (infra) y un script de
análisis (evaluación). **NO toca `pipeline/*.py`** (los flags ya existen; los profiles
solo los setean en `false`). Es alineación interna puerta-3. El **flip del default
operacional** que el A/B pudiera respaldar es un paso POSTERIOR y gateado aparte
(tag `pre-s<NN>-c2-flip` + OK explícito de Nicolás + R2/R3).

---

## 3. Criterio pre-registrado (fijado ANTES de correr — A66)

La pregunta física que decide, **por gate**:

> ¿Apagar la cerca deja que un cluster lejano (Salar, incendio, valle topográfico)
> le **robe el primario al cráter** en un volcán **focal**?

**Métrica primaria = robo de cluster espacial (A61, NO % de magnitud — decisión
Nicolás S118):**

- Para cada noche **MIROVA-confirmada** de cada volcán focal, comparar el
  `primary_cluster.centroid` (re-anclado al GVP, A61) entre baseline (gate ON) y el
  brazo gate-OFF.
- **Robo de cluster** = el `pc.centroid` **sale del `inner_radius_km`** con el gate
  OFF cuando con el gate ON estaba dentro. (El cráter deja de ser el primario.)

**Decisión por gate:**

| Resultado en focales (noches MIROVA-conf) | Acción |
|---|---|
| Gate OFF **NO** produce robo de cluster en **ningún** focal | **Gate → OFF** (clon-literal; el frontend ya suprime lo extra-radio nuevo que MIROVA no confirme) |
| Gate OFF produce robo de cluster en **≥1** focal | **Gate → ON uniforme** (excepción documentada: la cerca compra posición que el puro pierde por mecánica de selección) |

**Controles / métricas secundarias (no deciden, contextualizan):**
- **Lado nevado** (control): con gate OFF vuelven píxeles de artefacto. Verificar que
  (a) tampoco roben cluster, y (b) el frontend los filtre (`distance_class != summit`)
  → inerte en display. Si un artefacto nevado roba cluster, es ruido que el frontend
  ya tapa, no degradación de cat-b.
- **Cruce de lo REMOVIDO vs MIROVA (A10):** de los records que el gate-OFF **agrega**
  (extra-radio que la cerca tapaba), ¿cuántos confirma MIROVA (`pc.vrp_mw`, ±1 día)?
  Si MIROVA los confirma → el gate estaba escondiendo cat-b real (argumento extra
  pro-OFF). Si no → es el ruido esperado (el frontend lo tapa).
- **Interacción entre gates** (brazo both-OFF): en MODIS ambos gates tocan píxeles
  solapados. Comparar both-OFF vs efecto sumado de los single-OFF para detectar
  no-aditividad.

---

## 4. Diseño experimental

### 4.1 Brazos (4 profiles, opción 3 exhaustiva — decisión Nicolás S118)

Regenerados **limpios desde el operacional actual** (los `_f_s81_*` existen pero
están sobre el SHA de S81, cuando los gates se adoptaban — baseline obsoleto, A50).
Cada uno con `data_subdir` aislado (A47).

| Profile | `path_d_intra_radio` | `second_pass_intra_radio` | Rol |
|---|---|---|---|
| `_c2ab_baseline` | true | true | = operacional, aislado (control) |
| `_c2ab_pathd_off` | **false** | true | aísla el gate MODIS Path-D |
| `_c2ab_2pass_off` | true | **false** | aísla el gate second-pass (MODIS+VIIRS) |
| `_c2ab_both_off` | **false** | **false** | clon-literal puro + interacción |

Única diferencia entre profiles = los dos flags. Todo lo demás idéntico al operacional.

### 4.2 Volcanes — 11 Tier A, clasificados por régimen (A21/R2_GATES_BY_REGIME)

- **Focales** (donde se decide; el robo de cluster es la métrica clave):
  **Láscar, Lastarria, Isluga, PlanchonPeteroa, PuyehueCordonCaulle.**
- **Nevados** (control de artefacto): **Llaima, Copahue, Villarrica,
  NevadosDeChillan, Tupungatito.**
- **Chaitén** (11º, Tier A muy bajo, domo nevado) → grupo nevado/control.

### 4.3 Ventanas dirigidas (anti-timeout — patrón s112, A15/A64/A26)

**NO historia full ciega.** Por volcán, ventanas estrechas (≤14 días/chunk como
s112) construidas alrededor de **clusters de fechas ALERTA** (de los CSV consolidado
+ OCR de MIROVA) **+ una muestra RUTINA** de control. Un script reproducible las
extrae (sin transcribir fechas a mano, S91):

- `scripts/build_c2ab_windows.py` → lee `data/mirova_reference/.../registro_vrp_consolidado.csv`
  + `registro_vrp_ocr.csv`, agrupa fechas ALERTA por volcán (gap >7 días = cluster
  nuevo), emite ventanas `[min-2d, max+2d]` por cluster + 1 ventana RUTINA aleatoria
  de control. Salida: `experiments/_s118_c2ab/windows.json` (consumido por el matrix).
- Cota dura por job: chunk ≤14 días → bajo el timeout 290 min con margen amplio
  (s112 con ventanas así corría holgado).

### 4.4 Workflow (infra — patrón reproc-s112)

`.github/workflows/reproc-s118-c2-gates-ab.yml`:
- `"on":` **quoted** (Norway Problem, A43). Verificar pre-merge con
  `python -c "import yaml; print(list(yaml.safe_load(open(p)).keys()))"`.
- `runs-on: ubuntu-latest`, `timeout-minutes: 300` (job) / `290` (step).
- `strategy: { fail-fast: false, max-parallel: 12 }`.
- `matrix: profile(4) × volcano(11) × chunk(N por volcán)`.
- Instala `pyhdf earthaccess numpy h5py scipy pyyaml` + `libhdf4-dev` (MODIS corre en
  GH Actions Linux; pyhdf roto en Windows). VIIRS corre en el mismo job (uniforme).
- **Cada job sube su artifact** `s118c2ab-<profile>-<volcano>-<chunk>` con
  `data/<profile>/<volcano>.json` (sin commit → **sin race A47/A25**). El merge y el
  análisis se hacen offline al descargar los artifacts.
- Secrets: `EARTHDATA_TOKEN/USERNAME/PASSWORD`.

Coste estimado: 4 × 11 × (~2-3 ventanas) ≈ 90-130 jobs. Repo público = minutos
ilimitados; max-parallel 12 → varias tandas. Cada job ≪ 290 min por ventana estrecha.

### 4.5 Análisis (offline, reproducible — S91)

`experiments/_s118_c2ab/analyze.py`:
1. Descargar/mergear artifacts por profile → `data/_c2ab_*/`.
2. Por (volcán focal, noche MIROVA-confirmada): `pc.centroid` re-anclado al GVP (A61),
   distancia al cráter, dentro/fuera del `inner_radius`, baseline vs cada brazo.
3. Tabla de **robo de cluster** por gate × volcán focal.
4. Cruce de lo removido/agregado vs MIROVA `pc.vrp_mw` ±1 día (A10).
5. Control nevado + interacción both-OFF.
6. **Verificación programática doc==fuente** antes de escribir números a cualquier
   doc/PR (S91: ningún número transcrito a mano).
7. Salida: `docs/AUDIT_S118_C2_GATES_AB.md` + JSON crudos en `experiments/_s118_c2ab/`.

---

## 5. Plan de implementación (orden; cada paso es bite-sized)

1. `git tag pre-s118-c2ab-infra <sha> && git push --tags` (A38/A45 defensivo, aunque
   sea infra — toca profiles/workflow).
2. `scripts/build_c2ab_windows.py` + correr → `windows.json`. **Verificar** que las
   ventanas cubren fechas ALERTA reales de focales (A79: confirmar el evento objetivo,
   no solo la métrica agregada).
3. Generar los 4 profiles `_c2ab_*` desde el operacional (Edit puntual de los 2 flags
   + `data_subdir`; NO rewrite con yaml.safe_dump — destruye comentarios).
4. `reproc-s118-c2-gates-ab.yml` con el matrix poblado desde `windows.json`. Validar
   `"on":` parsea como string. Merge a main (workflow_dispatch requiere default branch).
5. Dispatch. Esperar (run_in_background / notificación; sin polling con sleep).
6. `analyze.py` → tablas → `AUDIT_S118_C2_GATES_AB.md`.
7. Presentar a Nicolás (revisa en resultados, no en código — feedback S107). El **flip**
   es su punto de decisión, gateado aparte (paso 8, NO en este sprint salvo OK).
8. *(Posterior, gateado)* Si el A/B respalda OFF para un gate: tag `pre-s<NN>-c2-flip`,
   editar el operacional, R2/R3, reproc, dashboard.

---

## 6. Fuera de scope (YAGNI / anti-A8)

- **Per-régimen / per-volcán gate** — MISSION línea 77 (§2).
- **Discriminante físico per-record** — agotado (A83).
- **Flip del default operacional** — paso 8, gateado, NO en este sprint.
- **far→summit MODIS / D11 / A69-como-bug** — cerrado S114 (A82).
- **Re-ancla ctx_cluster** — cerrado S117 (A84).
- **Tocar `pipeline/*.py`** — este A/B es config+infra+análisis, cero lógica.

---

## 7. Riesgos

| Riesgo | Mitigación |
|---|---|
| Timeout por ventanas largas / LANCE lento (A64) | Ventanas ≤14 días dirigidas (s112 probado); circuit-breaker LANCE ya en fetch.py |
| Race sobre `data/<profile>/<vol>.json` | Artifact-upload por job, sin commit (A47); merge offline |
| `"on":` parsea como bool → HTTP 422 (A43) | Quoted + verificación pre-merge |
| Pocas noches MIROVA-conf en focales → poca potencia | Ventanas construidas alrededor de TODOS los clusters ALERTA del CSV; reportar N por volcán (no ocultar cobertura baja) |
| Confundir robo-de-cluster real con artefacto de ancla (A3) | Re-anclar SIEMPRE al GVP antes de medir distancia (A61) |
| Interpretar artefacto nevado como FN (contar mal) | FN solo sobre cat-b REAL confirmado por MIROVA; nevado es control, no objetivo |
