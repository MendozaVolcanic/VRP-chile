# F5 · Regla C mecánica — S134

Worktree: `VRP-Chile-s134-f5` (branch `s134-f5`). Sin cambios de estado git (solo `git log`/`git show`).

## Control positivo del instrumento

```
grep -n "inner_radius_km" volcanoes.yaml | wc -l   -> 11   (esperado >= 11) OK
grep -rn "f5_core_vrp_mw" pipeline/ | wc -l          -> 4    (esperado >= 1) OK
```

Instrumento del script P4 (`p4_duplicados.py`) probado con control positivo propio:
inyecté 1 record duplicado (mismo `granule`) en una copia temporal de `Villarrica.json`
y `cuenta_dup()` lo detectó (`n=6445 dup_keys=1 extra=1`). El script en modo normal
sobre el mismo archivo real da 0 — confirma que el cero es "no hay", no "no mide".

## Tabla P1–P12

| # | comando clave | salida esencial | veredicto |
|---|---|---|---|
| P1 | `grep -n features volcanoes.yaml` → 0; pero `find . -iname "*volcanic_feature*"` → `pipeline/volcanic_features.yaml` (84 líneas, 2 entradas: PCC lacolito, Lastarria/Lazufre) | A89: el gazetteer NO vive en `volcanoes.yaml`, vive en archivo separado `pipeline/volcanic_features.yaml`, consumido por `geo_class` (S88/S89) | **CERRADO** en `c4dcdef0b` (S88, campo) + `8fe378e42` (S89, Lazufre) |
| P2 | `grep -n D13 docs/MIROVA_DIVERGENCES.md` → sección "ABIERTA (documental)" S124, con sub-bloque "Clasificación cumplida — S126" y "Estado S126: clasificación CERRADA... documental sin acción propia"; script citado `experiments/_s126_d13/01_que_apaga_la_cerca.py` confirmado por `git log --oneline -- experiments/_s126_d13` → commit `722ce0888` (no visible en este worktree, sparse-checkout no lo trae) | el denominador SÍ se midió (31,0% / 10.773 de 34.763, S124) y se reclasificó (S126). El encabezado sigue diciendo literalmente "ABIERTA" pero el contenido dice que es una decisión cerrada de no tocar | **SIGUE ABIERTO (documental, sin acción — clasificación ya cerrada S126)**, refleja fielmente el estado actual del doc |
| P3 | `grep -c mirova_center volcanoes.yaml` → 35 líneas (incluye comentarios); `grep -n mirova_center` muestra `mirova_center_lat/lon` **uno por volcán**, extraído de UN solo KMZ por sensor (ej. "extraído de kmz/Villarrica_VIIRS750_Last_GE.kmz") | no hay estructura por sensor, es un único punto por volcán tomado de un sensor específico | **SIGUE ABIERTO** |
| P4 | `python experiments/_s134_audit/f5/p4_duplicados.py` sobre `~/ab_area` (24 dirs, n=12.186 records, ventana S133) y sobre los 11 Tier A canónicos (`data/mirova_equivalent/`, historia completa a 2026-09-05, n total ≈58.335) con clave `(sensor,granule)` y `(sensor,datetime_utc)` | 0 duplicados en ambos universos, en ambas claves | **CERRADO / medido limpio** (no era un bug — instrumento validado con control positivo) |
| P5 | `grep -n nti_max pipeline/process_modis.py` → variable local `nti_max` (línea 1188) se persiste como `diag_nti_max` (línea 1509); confirmado en datos reales: 226/226 records MODIS de Villarrica desde 2026-06-01 tienen `diag_nti_max` no-nulo | A89: el nombre en el punto de uso (`diag_nti_max`) no es el de la variable local (`nti_max`) — el grep literal `nti_max` sí lo encuentra porque es substring, pero un grep de la CLAVE persistida (`diag_nti_max`) confirma presencia | **CERRADO** en `59846e897` |
| P6 | `grep -rln nrt.yml tests/` → 4 archivos; ninguno mide timeout-vs-duración: `test_guard_timeout_vs_ventana_s129.py` solo cubre workflows de reproceso con inputs `start`/`end` (nrt.yml no los tiene, es cron puro); `test_cadencia_cron_s133.py` mide cadencia del cron, no timeout; `test_reproc_watchdog_vivos_s133.py` mide vigencia del watchdog, no timeout. `nrt.yml:69` tiene `timeout-minutes: 80` con comentario manual citando S131 ("peor job observado 56 min") pero sin test que lo verifique | ningún guard ejecutable compara el timeout de `nrt.yml` contra la duración real observada | **SIGUE ABIERTO** |
| P7 | `grep -rni npixhot pipeline/ scripts/ .github/` → 0; `grep -rni "\bOLI\b\|\bMSI\b"` → solo comentarios de texto citando Sentinel-2/Landsat como corroboración manual en `pipeline/profiles/*.yaml`, ningún workflow ni script scrapea el producto | no hay scraper ni pipeline para OLI/MSI NPixHot | **SIGUE ABIERTO** (confirma la premisa del pendiente) |
| P8 | `grep -rn "0.17\|OSF" tests/test_coefficients.py` → docstring cita "validated ... error <=0.17% across 48,360 rows" pero el cuerpo del test (`test_modis_wooster_coeff`, etc.) SOLO hace `assert WOOSTER_COEFF == 18.9` (guard de regresión de constante); ningún test recalcula el error contra un dataset OSF | el 0,17% es citado, no medido por ningún test ejecutable | **SIGUE ABIERTO** |
| P9 | Mecanismo geo_class="extension" SÍ existe en producción (`frontend/index.html:2828` `primary_cluster.geo_class === "extension"`, naranja); PCC tiene entrada en `volcanic_features.yaml` (lacolito). Medido en datos reales: `PuyehueCordonCaulle.json` (n=5.340, historia completa) → `Counter({'summit':4321,None:1006,'far':13})`, **0 registros con `geo_class=="extension"`** | el marcador existe en código pero nunca se activa para PCC en la práctica — el propio comentario del YAML lo anticipa ("inner_radius=20, efecto marginal chico"). La premisa del pendiente ("no se hace") es imprecisa: el mecanismo SÍ está, pero es un no-op medido, no ausente | **CERRADO como mecanismo, pero NO-OP verificado para PCC** (0/5.340) — matiz A89, no encaja en ninguno de los 3 veredictos limpios |
| P10 | `grep -rn d9_capped pipeline/` → variable interna `_d9_capped`/`_d9_capped_t`, persistida como `primary_cluster["d9_capped"]`; activo en `mirova_equivalent.yaml:463-464` (`path_d_only_cap_mw: 5.0`, `path_d_only_cap_tbg_max_k: 270.0`); en datos reales PCC: 269/5.340 records con `d9_capped=True` | SÍ está en el perfil operacional y SÍ se persiste en registros reales | **CERRADO** (activo en producción) |
| P11 | `gh run list --workflow reproc-s133-area-ab.yml` → 2 runs: `33872836355` (2026-09-04 12:27, **failure**, murió en Lascar/geoloc) y **`33912398561`** (2026-09-04 19:40, **success**, 24/24 jobs verdes = 8 volcanes × 3 brazos control/corona/geoloc). `~/ab_area` tiene exactamente 24 dirs con ese patrón, ya bajados | la premisa "faltan chunks 2 y 3" está **desactualizada**: hubo un rerun completo posterior que sí terminó verde con el universo completo (no por chunks, corrió entero) | **CERRADO** — el A/B del área SÍ corrió completo (run `33912398561`); no aplica reintentar |
| P12 | `gh run list --workflow reproc-s133-b22-ab.yml` → 1 solo run (`33872821788`, success, 2026-09-04). `~/ab_b22` tiene 4 dirs = 2 volcanes (Lascar, Villarrica) × 2 brazos (control, enabled) | confirma la ventana angosta (n=2 pares) que ya reportó S133; no se amplió | **SIGUE ABIERTO** (tal como documentado — ventana angosta, sin ampliar) |

## Los tres números

- **Confirmados abiertos**: P2 (documental sin acción, refleja el estado real), P3, P6, P7, P8, P12 → **6**
- **Ya cerrados**: P1, P4, P5, P9 (matizado — mecanismo cerrado, resultado no-op), P10, P11 → **6**
- **Sin poder verificar**: **0**

(P9 se cuenta como cerrado-con-matiz: el mecanismo que el pendiente pedía existe y está probado contra datos reales, aunque el resultado observado sea "no dispara para PCC" — eso es información, no ausencia de instrumento.)

## Guards propuestos para los CERRADOS (una línea cada uno, sin escribir)

- **P1**: test que falle si `pipeline/volcanic_features.yaml` deja de tener ≥1 entrada por volcán con lacolito/campo difuso catalogado (PCC hoy).
- **P4**: correr `p4_duplicados.py` (o equivalente) como parte de la suite sobre los 11 Tier A, con umbral 0 duplicados por `(sensor,granule)`.
- **P5**: `assert "diag_nti_max" in record` para una muestra de records MODIS reales recientes (no solo un `grep` del nombre en el código).
- **P9**: test que confirme que `geo_class=="extension"` sigue siendo alcanzable en teoría (existe al menos 1 entrada en `volcanic_features.yaml` con `ext_km` que cae fuera de `inner_radius_km` del volcán) aunque hoy dé 0 en PCC.
- **P10**: `assert primary_cluster.get("d9_capped") in (None, True)` + smoke test de que `path_d_only_cap_mw` sigue seteado en `mirova_equivalent.yaml`.
- **P11**: ninguno — es un hecho histórico (el run ya corrió), no un invariante a vigilar.

## VERIFICADO LIMPIO

- Control positivo del propio instrumento (`inner_radius_km`, `f5_core_vrp_mw`) — sano.
- `p4_duplicados.py` con control positivo (dup inyectado detectado) — instrumento válido, y 0 duplicados reales en 11 Tier A + 24 dirs de `~/ab_area`.
- `diag_nti_max` persistido en 226/226 records MODIS recientes de Villarrica — no hace falta re-auditar P5.
- `d9_capped` activo y persistido en datos reales de PCC (269/5.340) — no hace falta re-auditar P10.
- El A/B del área **SÍ terminó completo** (run `33912398561`, 24/24 verde) — no reintentar P11; sí falta que alguien (fuera de este frente) actualice el estado en `docs/superpowers/plans/2026-09-05-*` y en `MEMORY.md`, que todavía dicen "faltan chunks 2 y 3".

---

## Corrección de quien orquesta (verificación cruzada, 2026-09-05 14:58 UTC)

**P11 está mal en la tabla de arriba.** «Chunk» en el A/B del área es una **ventana temporal**,
no un subconjunto de volcanes: el yml tiene inputs `start`/`end` con default `2026-04-01` →
`2026-05-31` y un input `overwrite` que dice «true en el PRIMER chunk (pisa), false en los
siguientes (agrega)» (`.github/workflows/reproc-s133-area-ab.yml:108-119`). Los 24 artefactos del
run `33912398561` cubren exactamente esa ventana — medido sobre los JSON bajados:
Chaitén 578 records 2026-04-01 04:48 → 2026-05-31 06:24; Isluga 441, 04-01 → 05-31; Láscar 452,
04-01 → 05-31. Es el **chunk 1 completo** (rerun del que murió a las 12:27), no «el universo
completo». Los chunks 2 y 3 (junio en adelante) **no corrieron**, tal como decía el plan.

Veredicto corregido de P11: **SIGUE ABIERTO como dato, y se CIERRA POR DECISIÓN**: no se corren,
porque el veredicto NO ADOPTAR no cambia con más datos (`docs/s133/AB_AREA_VEREDICTO_CHUNK1.md`).
El pendiente se archiva con esa razón. No hace falta corregir el plan ni `MEMORY.md` en ese punto.

**Los tres números corregidos**: confirmados abiertos **7** (P2, P3, P6, P7, P8, P11, P12) ·
ya cerrados **5** (P1, P4, P5, P9 con matiz, P10) · sin poder verificar **0**.

Lección para el registro: el auditor leyó «24/24 verdes» como «universo completo» sin mirar la
ventana de los datos. Es la forma más común de A90 (un conteo sin ventana) y la razón de que el
que verifica no sea el que encontró.

**Seguimiento descartado tras verificar**: el `timeout-minutes: 80` de `nrt.yml:69` es del JOB;
los pasos de pipeline siguen en `timeout-minutes: 50` (`nrt.yml:179` y `:206`), que es lo que el
`CLAUDE.md` del proyecto declara («50 min per-step»). No hay deuda documental ahí.
