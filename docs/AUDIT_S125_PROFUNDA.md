# Auditoría profunda S125 — hallazgos clasificados

> Ejecuta la TAREA 0 de `tasks/BLOQUE_ARRANQUE_S125.md` siguiendo
> `docs/PROTOCOLO_AUDITORIA_PROFUNDA.md`. Seis subagentes adversariales en
> paralelo, con contexto autocontenido y sin historial de conversación (el
> sesgo del autor es lo que se quiere evitar).
>
> **Regla de lectura**: cada hallazgo dice si lo verifiqué YO con comando propio
> o si viene sólo del subagente. Los subagentes NO son fuente de verdad
> metodológica (A48) — en esta misma auditoría uno de ellos se equivocó, y está
> señalado abajo.

Ejes: (1) reglas A1-A45 · (2) reglas A46-A88 · (3) divergencias D1-D17 ·
(4) MISSION + los 17 flags del operacional · (5) capacidad dormida ·
(6) **cadena de magnitud file:line contra Coppola Eq. 6-8**.

---

## 0. El hallazgo principal — dónde vive el factor 2

La detección se auditó file:line en S114 y resultó fiel. La **magnitud** nunca
se había auditado. El eje 6 la recorrió contra Coppola 2016a y encontró que el
sub-reporte no está en la física —los tres coeficientes de Wooster, las
unidades y el área nadir están **correctos**, verificados aritméticamente— sino
en **dos reducciones aplicadas aguas abajo de la Eq. 8**, sobre la suma final
del cluster.

### R1 · `cluster_focal_vrp_mw` — suma un subconjunto en vez del cluster

`pipeline/vrp_regimes.py:213-247`, llamado desde `process_modis.py:1069` y
`:1317` (+ VIIRS 750). Flags `enable_focal_cluster_magnitude` y
`..._viirs750` en **`true`** (verificado con `pipeline.profile`).

Suma sólo los píxeles *contextualmente anómalos* del cluster. Si ninguno lo es,
colapsa al píxel pico y marca `focal_degraded`.

**Verificado por mí** — `experiments/_s125_magnitud/01_cuantificar_reducciones.py`
sobre los 45 JSON operacionales, resultado persistido en `01_resultado.json`:

| | |
|---|---|
| records con `primary_cluster` | 38.995 |
| con magnitud focal | 13.627 |
| **degradados a 1 píxel** | **8.301 (60,9 %)** |

Por volcán, el porcentaje degradado: PP 74,0 · Villarrica 72,3 · Lastarria 65,4 ·
Copahue 63,7 · Isluga 63,4 · Llaima 63,0 · NdC 60,9 · PCC 55,4 · Láscar 51,6 ·
Chaitén 48,4 · Tupungatito 44,5.

### R2 · `apply_single_pixel_mode` — máximo en vez de suma

`pipeline/single_pixel_mode.py:63-130`, llamado desde `process_modis.py:1093` y
`process_viirs.py:1768`. Si `vrp < 5 MW` **y** `n_pixels <= 3`, reemplaza la suma
del cluster por el **máximo** per-píxel.

**Verificado por mí, y acá corregí al subagente en la dirección contraria a la
que esperaba**: mi primer conteo dio 75,6 % de records afectados, que es el
número engañoso — la trampa T3 que esta misma sesión persigue. Al abrir la
distribución:

| `n_pixels` | records | efecto |
|---|---|---|
| 1 | 23.659 | **no-op** (el máximo *es* la suma) |
| 2 | 4.072 | recorta |
| 3 | 1.765 | recorta |

**Con efecto real: 5.837 records (15,0 %)**, no 75,6 %. El subagente tenía razón
y mi agregado global la tapaba.

⚠️ **No reproducible**: el ratio suma/máximo que el eje 6 reportó (mediana 1,50,
p90 2,00) **no se puede recomputar desde los JSON** — `per_pixel_vrp` no se
persiste. Queda **SIN RESPALDO** hasta que se mida con un probe read-only sobre
el granule. El docstring del propio módulo ilustra el mecanismo (2,5 → 1,2 MW),
así que la dirección no está en duda; la magnitud sí.

### Por qué esto importa físicamente

Un cráter activo con dos o tres píxeles calientes contiguos —lo normal en un
lava lake débil o un domo a 375 m— tiene su energía repartida entre esos
píxeles. MIROVA integra el cluster; nosotros, en ese régimen, reportamos sólo el
píxel más brillante y tiramos el resto. No es un error de física: es una
decisión de qué se suma, tomada aguas abajo de la ecuación.

Las dos nacieron como parche a un sesgo real **hacia arriba**: el fondo se
estima en un anillo regional de 5-25 km (`detection_context.py:945`) cuando la
Eq. 6 pide el entorno inmediato, y eso infla ΔL. Pero el parche se aplica sobre
la suma final, no sobre el fondo que lo causa — así que cuando la causa no
aplica, sigue mordiendo. Es el patrón que `MISSION.md` documenta como
anti-patrón histórico: remediar el síntoma de un drift en vez de la causa.

### Y la implementación fiel ya existe, apagada

`cluster_corona_background` (`vrp_regimes.py:103-185`) computa el fondo con la
corona del cluster contiguo — la Eq. 6 literal. Está **escrita, testeada y
cableada** en `process_modis.py:1049`. Y `ENABLE_LOCAL_CLUSTER_MAGNITUDE =
False` (verificado). Es capacidad dormida (T5) sobre el eje del factor 2.

**El A/B que corresponde no es agregar otro gate: es apagar R1+R2 y encender la
corona.** No lo ejecuto sin tag defensivo y confirmación explícita (A45).

---

## 1. FALSO — el dato de hoy contradice el documento

| # | qué dice | qué es | evidencia |
|---|---|---|---|
| F1 | `MISSION.md:126` — "Regla D Test 1-priority, **removido S27**" | **viva y sin flag** en los 3 procesadores; se amplió en S30, S44 y S111 | `process_viirs.py:1502-1568`, `process_modis.py:1167-1204`, `process_viirs_mod.py:1055` — *subagente, no re-verificado por mí* |
| F2 | `MISSION.md:74-79` — "MIROVA no conmuta de método por volcán" | el operacional **sí** conmuta: `enable_test1_lbg_global` se gatea con `lbg_global_compatible` per-volcán (Láscar, NdC, Lastarria con fondo global; los otros 8 local) | *subagente, no re-verificado por mí* |
| F3 | `MIROVA_DIVERGENCES.md` D14 — "sólo afecta a VIIRS 375; MODIS y V750 no la tienen" | MODIS **sí la tiene** (`process_modis.py:505,715`), inerte porque `CLOUD_MASK_BT_K = 0.0` | **verificado por mí** |
| F4 | catálogo l.1119 — Villarrica "MIROVA siempre reporta dist 0,84 km" | `0.0` en 3.284 de 3.338 (98,4 %) | ya corregido en CLAUDE.md (A13) en S124; **el catálogo no se corrigió** |
| F5 | `profile.py:701` — comentario que S124 escribió *para prevenir la trampa del nivel*: "todos los `enable_*` viven bajo `thresholds:`" | son **0 de 32** (32 bajo `paths:`, 4 en raíz). `ENABLE_UTM_REGRID` era la excepción, no la regla | *subagente; el conteo no lo re-verifiqué, la dirección sí* |

**Contradicción entre ejes, resuelta por mí**: el eje 4 afirmó que "la máscara
de nube BT<260 K NO está activa" apoyándose en `CLOUD_MASK_BT_K = 0.0`. **Es
falso para VIIRS 375**: `process_viirs.py:674` tiene `CLOUD_BT_THRESHOLD = 260.0`
**hardcodeado**, ignorando la perilla del perfil, y en `:678-681` se aplica a
`roi_mask` y `bg_mask`. La perilla existe y ese sensor no la lee. El eje 4
generalizó desde MODIS — ejemplo en vivo de por qué los hallazgos críticos se
verifican antes de aceptarlos (A48).

---

## 2. OBSOLETO — fue cierto, dejó de valer

| # | regla / doc | desde cuándo dejó de valer |
|---|---|---|
| O1 | **A69** cierra citando el rediseño "Test 1 integra NTI, `compute_test1_nti` #379" como desenlace | **`ENABLE_TEST1_NTI_INTEGRAL = False`** y la rama existe **sólo en `process_viirs.py:958`**; MODIS y V750 importan únicamente `compute_test1_mir`. La causa raíz que A69 describe sigue viva en los 3 sensores. **Verificado por mí.** Es el caso que A87 advierte: confundir el flag con el fenómeno |
| O2 | **A23** — "D9 ABIERTO", propone un A/B de 3 alternativas | D9 se cerró en S113 en sus dos caras (`MIROVA_DIVERGENCES.md:515`). Manda a reabrir trabajo cerrado — viola anti-A8 |
| O3 | **A17** — procedimiento manual `cp … latest_consolidado.csv` + commit | automatizado desde S77 por `sync-mirova-csv.yml` (cron 1 h), que cita a A17 como el bug que vino a arreglar |
| O4 | **A7** — dice que se persisten `std_bg_i04`, `threshold_mir`, `nti_std` | no existen en ninguno de los 2.547 records VIIRS de Villarrica; hoy son `diag_sigma_bg_k`, `diag_eff_threshold_k`, `diag_nti_std` |
| O5 | **A42** — describe el HTTP 422 como sin causa raíz | resuelto y documentado como A43 (Norway Problem, `"on":` quoted), aplicado en producción |
| O6 | **D12** del catálogo, congelada en S106/S108, presenta como pendiente el reproc que ya se probó | `docs/AUDIT_S121_D12_AB.md` = **VEREDICTO NO ADOPTAR**; el candidato siguiente (C2 peak-of-kernel) refutado en S122 |
| O7 | **A81** — su ejemplo de la cara espuria ("2 records Villarrica") | hoy `diag_a46_relabel` dispara en Chaitén 3 + PP 1, cero en Villarrica. El guard vive (`store.py:412-442`); caducó el ejemplo |
| O8 | `MAX_SIGMA_COMPONENT_K` "removido" | neutralizado **por valor** (999.0), no por código: el bloque corre en cada pasada y el **default es 7.0**. Un perfil que omita la clave resucita el parche |

---

## 3. SIN RESPALDO — puede ser cierto, nadie lo probó

Regla de salida: **no borrar**. Rebajar de "cerrado" a "abierto pendiente de prueba".

- **D5** dice "calibración lograda, ratio 1,35x" mientras la tabla de hoy da
  mediana ~0,75 = **sub-reporte**. La divergencia marcada resuelta describe, con
  el signo invertido, el frente principal abierto de S125. *(pendiente de que yo
  corra `04_tabla_brazos.py`)*
- **D13** (31 %): el script que la produce no está en el directorio citado; el
  re-cálculo independiente del eje 3 dio 27,8 % (denominador no declarado). La
  sustancia se sostiene, el número no reproduce.
- **D14** `r = -0,23` (base de "la máscara no es el driver del gap"): sin script,
  sin n, sin IC.
- **D9** residuo "24-83x post-cap": es de S71, **anterior** a nadir-fijo
  (S102/S103, que llevó la magnitud global a 0,78-0,80x). Nadie lo re-midió.
- **A54** (95,4 % de los FP son físicamente reales): los porcentajes salen de
  `AUDIT_S86.md` sobre 13.207 records; hoy son 43.618, con nadir S102-103, ancla
  S98 y gates OFF S118 de por medio. Nunca se recomputó.
- **A12** ΔT por volcán: no reproduce — la mediana `t_max_k - t_bg_k` da Láscar
  15,8 K (regla: 21,6) e **Isluga 7,8 K** (regla: ~20), o sea Isluga cae bajo el
  umbral de 12 K con que la regla lo declara "ya calibrado".
- **A84**: su probe (`scratchpad/probe_ctx_cluster_s117.py`) nunca entró a git →
  sus números no se recomputan. Su otra pata (A/B S106) sí está firme.
- **Cuatro adopciones operacionales cuyo "doc de adopción" es un plan sin
  ejecutar** — uno dice textualmente "no mergear sin ejecutar este A/B" y se
  mergeó igual: `enable_single_pixel_sub_mw_mode`, `enable_dual_roi_first_pass`
  y `..._second_pass` (la tabla citada muestra **delta cero** para ambos; el
  +0,69 pp es todo de `second_pass_adjacent`), `enable_nadir_fixed_pixel_area_viirs`
  (A/B sólo con CONS, sin OCR, que es ~80 % del ground truth VIIRS).
- **R2 · ratio suma/máximo** — ver §0.

**Ninguno de éstos es motivo para apagar nada del operacional.** Son motivo para
marcarlos pendientes de prueba.

---

## 4. CONFIRMADO — verificado, no re-auditar

- **Los 17 flags `true` del operacional están realmente activos y en el nivel
  correcto** (leídos vía `pipeline.profile`, no del YAML). Ninguno apagado en
  silencio.
- **Suite: 906 tests verdes** (`pytest tests/ -q` → `906 passed in 67s`).
- **NRT sano**: último run verde 2026-08-28 04:02 UTC, commiteó datos 04:50 del
  mismo día. No es pipeline zombie.
- **Los coeficientes de Wooster y las unidades son correctos** (verificados
  aritméticamente): MODIS 18,9x1e6 · VIIRS 375 18,0x140.625 · VIIRS 750
  19,7x562.500. Área nadir fija consistente entre ΔL y el producto en los 8
  call-sites. ΔL per-píxel y kernel 3x3, fieles. **No hay pi perdido, ni factor
  hemisférico, ni error de unidades.**
- **Premisa de D17 confirmada** (`run_pipeline.py:248/293/338` pasan
  `volcano["lat"/"lon"]` al regrid; `get_grid_center` sólo aparece en su
  definición y en tests; los 11 offsets se reprodujeron idénticos).
- **A63** (`pytest tests/test_detection_anchor.py` → 10 passed), A73 (probe NdC
  0/31 artefacto vs 57 real), A79, A83, A85 (214 focales, 0 robos), A47, A61/A70,
  A66/A67, A45, A44, A38/A39, A18, A20/A21, A35, A5, A9, A3.

---

## 5. Bugs de infraestructura encontrados de paso

**B1 · Ground truth OCR partido en dos, y un script usa el congelado.**
Verificado por mí con pandas:

| archivo | filas | cubre hasta |
|---|---|---|
| `data/mirova_reference/registro_vrp_ocr.csv` | 235 | **2026-03-28** |
| `data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv` | 887 | 2026-08-24 |

El de nombre "snapshot" es el fresco. `scripts/build_c2ab_windows.py:55` consume
el congelado → pierde 5 meses y ~73 % del canal OCR. `auto_audit_weekly.py:48`
usa el correcto.

**B2 · Trampa del nivel del YAML, viva en los 39 perfiles.** Verificado por mí:
`modis_vent_threshold_k` está **duplicado** en `mirova_equivalent.yaml` — l.101
bajo `thresholds:` (1.0, la que gana) y l.171 bajo `paths:` (2.5, **nunca
corrió**). Ídem `modis_vent_vrp_floor_mw` (0.0 gana, 0.3 muerta). Inerte en el
operacional porque `enable_vent_path_modis=False`, pero **vivo en 2 perfiles A/B
que sí lo prenden** — uno es el brazo de tratamiento de `enable_dual_roi_bt`.

**B3 · `audit_metrics.py:52 mirova_eq_vrp()` — creada para evitar drift entre
frontend y audit, está muerta (sólo `tests/`) y ya divergió** de las 3 copias
JS: le falta el cap de 50.000 MW, el fallback `vrp_mir_mw`, `includeFar` y el
Núcleo F5', que es el default del dashboard desde S97/S100. Un audit que la use
mide otra magnitud que la que ve Nicolás en pantalla. 114 días.

**B4 · Las 3 copias JS de `mirovaEqVrp` tienen 4 divergencias reales** (cap
ausente en el fallback de `diario`, orden invertido `distance_class` vs `!pc`,
`vrp_mir_mw` faltante, default inner 5 vs 10) — pero medido sobre 60.132
records **el impacto hoy es 0**. Es latente, no bug activo. Aparte: existe una
**4a vista live**, `comparacion.html`, enlazada desde el header, que muestra
`pc.vrp_mw` crudo sin filtro de display.

**B5 · `A86`, `A87` y `A88` no existen en `CLAUDE.md`** (`grep` → 0). Viven sólo
en la memoria del agente, aunque `MEMORY.md` las declara vinculantes. A87 es
justo la regla que habría atrapado O1.

**B6 · La rebaja de A82 no se propagó**: `CLAUDE.md:1200` sigue listando "D11
far→summit (irreducible A82)" entre las cerradas, y A83/A84 heredan la versión
fuerte.

**B7 · Capacidad dormida de alto valor**: `../mirova-tif-archive` tiene 15.606
PNG + 1.966 TIF + 1.965 KMZ **sin ningún lector**, con el polling parado desde
2026-05-20 (100 días). Es el único ground truth **por pasada** — `latest.php`
pierde ~80 % de las pasadas según su propio README. También: 16 flags que el
código lee y el YAML operacional no declara (2 encendidos por default oculto);
22 campos `diag_*` con 0 lectores (31 MB, 17,7 % del dato) que
`build_recent_json.py` no filtra del payload del dashboard; y `solar_zenith_deg`
del granule ignorado — `store.py` recomputa una aproximación sin ecuación del
tiempo para un gate que **descarta** records.

**B8 · Higiene del catálogo**: "D9" nombra dos divergencias distintas (l.203 y
l.837), igual que el D8/D8' ya reconocido → el próximo ID libre es **D18**. Y
`docs/D9_PATH_D_CIRRUS_FP.md` (citado en l.1156) no existe.

---

## 6. Qué hacer con esto

**Correcciones documentales aplicadas en esta sesión** (docs, no pipeline):
las de §1 y §2, citando la evidencia y conservando el texto original por
historia, según la regla de salida del protocolo.

**Lo que NO se toca sin tag defensivo + confirmación explícita de Nicolás
(A45)**: todo lo que roce `pipeline/`. Eso incluye el A/B de magnitud de §0, el
`260.0` hardcodeado de VIIRS 375, y la duplicación del YAML (B2).

**Orden propuesto para lo que sigue**, revisando la prioridad del bloque de
arranque a la luz de esto: el eje 6 encontró el mecanismo que explica un factor
2 en el régimen de pocos píxeles, que es exactamente el régimen donde vive el
sub-reporte. El brazo D de F70 mueve 0,11 sobre un hueco de 0,53 y perdió su
respaldo empírico; R1+R2 operan sobre el 61 % y el 15 % de los records
respectivamente. **La magnitud pasa a ser el frente principal.**
