# Auditoría de sesiones S1 → S14 — VRP Chile

Fecha: 2026-04-21. Documento interno, sin suavizar.
Fuentes: `tasks/`, `memory/`, `experiments/`, `CLAUDE.md`, git log.

---

## 1. Timeline de sesiones

| # | Fecha | Foco | Entregable | Estado |
|---|---|---|---|---|
| S1–S3 | ~2026-03 | Fetch earthaccess, pipeline mínimo, Wooster MIR, frontend Chart.js/Leaflet | Pipeline NRT para Lascar/Villarrica/PCC + GitHub Pages | Cerrado |
| S4 | 2026-03 | Corrección `scan_geometry.py`: áreas de pixel dependientes del ángulo (MODIS sec³(θ), VIIRS bow-tie). | `scan_geometry.py` + reprocess Villarrica | Cerrado — pero bug L5.1 quedó latente |
| S5 | 2026-04-07 | Primera calibración Lascar vs MIROVA. "Capture rate 88.7%, ratio 1.02". | Reporte calibración | **Invalidado** (L7.9) — refs OCR ruidosos + bucket/best-match |
| S6 | 2026-04-08 | Diagnóstico MODIS Lascar: eruption-scale path devolvía 0 pixels (L6.2). σ_bg de 5–16 K en Lascar por orografía. | Fix E1 (vent-ROI fuera de p95), L6.1–L6.5 | Parcial — E1 resultó inerte |
| S7 | 2026-04-08 | Re-auditoría con pairing estricto. Descubrimiento: MODIS no tiene NTI dual (L7.4), vent-path 1K produce 62% FP en Lascar (L7.7). Regla OR vs MAX (L7.2). | `lessons.md` L7.1–L7.9 | Cerrado |
| S8 | 2026-04-08 | "Calibración masiva". | **Eliminada completa**: contaminación NULO (9324 de 9717 refs eran `clasificacion=NULO`, basura). Todo el audit corrido contra 96% ruido. | **Abandonada** (L7.10) |
| S9 | 2026-04-08 | Clean-slate post-NULO. `VALID_CLASSES={"Muy Bajo","Bajo"}` con assert. Baseline honesto: P=0.16, R=0.71, F1=0.26. 5 red flags. Fork plan (`mirova_equivalent` vs `experimental`). | `AUDIT_S9_baseline.md`, `fork_plan.md`, tiering A/B/C | Cerrado |
| S10 | 2026-04-12 | OCR como referencia complementaria, NTI dual-PATH portado a VIIRS 750m (L10.3), `enable_vent_path_modis=false` (L10.1 — MODIS S/N=2.5× vs VIIRS 4–5×), Llaima identificado como ruido térmico (L10.4). | Audit S10, `process_viirs_mod.py` con NTI | Cerrado |
| S11 | 2026-04-13 | Path C (NTI relativo) en `experimental`. 8 tests unitarios. Reprocesamiento Jan–Apr. Descubrimiento: PCC ratio 0.13→1.15, Lastarria 0.46→1.33; Lascar recall cayó 0.79→0.56; Villarrica sigue 0/6. | `process_viirs*.py` con Path C, dashboard dual | Parcial — Lascar regresión sin investigar |
| S12 | 2026-04-14→16 | NRT gap Apr 10–14 (LANCE fallback, `bf75df4`), F1b sigma cap en vent-path (+25 pp recall sistema), `product_version` tagging, vent coords de campo, geofencing per-volcano, frontend chart fix VIIRS375, merge Peteroa. Refs MIROVA 14042026. Audit 11 volcanes. | Auditoría 8 volcanes Tier A/B, E1+E4 experimentos | Cerrado |
| S13 | 2026-04-18 | Cierre bibliográfico: 62 PDFs, `BIBLIOGRAPHY_SYNTHESIS.md`, MIROVA OSF v2.5 descargada (615K refs — Villarrica pasa de 6 a 5,211 refs). Fix trivial `WOOSTER_COEFF 18.9→18.0` en VIIRS 375m. | Bibliografía + plan S14 + plan Test 1 integrado | Cerrado en biblio, Test 1 **nunca implementado** |
| S14 | 2026-04-21 | Calibración empírica de coeficientes contra OSF v2.5 (error ≤0.17%). Schema `final_hotspot_*` unificado. `radius_km=25` uniforme + `inner_radius_km` oficial MIROVA. `distance_class={summit,far}`. Dashboard con "Acerca de". WOOSTER_COEFF VIIRS 750m 18.9→19.7. | Experiments 21–24, `decisions_s14.md`, código modificado | **Sin commitear** — handoff a S15 para validación visual + commit |

---

## 2. Decisiones metodológicas clave por sesión

**S4**: Corrección scan-angle. *Por qué*: un pixel MODIS a 45° de nadir no cubre 1 km² sino ~2 km² efectivos; la radiancia por unidad de área se diluye y el VRP se subestima si se usa área nadir. *Ojo — luego se descubrió en S14 A1 que MIROVA NO aplica corrección zenithal: usa A_pix nadir fijo. Esta decisión S4 resultó inconsistente con la referencia y se revirtió implícitamente al validar empíricamente los coeficientes.*

**S5**: Adoptar MIROVA como ground truth cuantitativo. *Por qué*: no hay validación publicada independiente en volcanes andinos — MIROVA era el único referente. *Costo*: todas las métricas S5 citadas ("2% de calibración") fueron invalidadas en S7 por pairing incorrecto y refs OCR ruidosos.

**S6**: No elegir E1 a ciegas (L6.1 "fix the bug you can prove"). *Por qué*: E1 se asumió como FP driver pero instrumentación demostró que el constraint vinculante era `3σ_bg`, no `roi_p95`. La lección es permanente.

**S7**: OR con floor vs MAX (L7.2). *Por qué físico*: MIROVA usa `Test2 OR Test3` donde el floor fijo rescata detecciones cuando σ explota (cielo heterogéneo). Nuestro `max(floor, N·σ)` forzaba siempre la rama más restrictiva. En atmósferas andinas donde σ_bg crece por nieve parcial y orografía, el MAX mata toda detección.

**S8**: — (abandonada). Única decisión útil fue la lección post-mortem L7.10 sobre defense-in-depth (hard-fail assert en `clasificacion`).

**S9**: Fork `mirova_equivalent` vs `experimental`. *Por qué*: tres objetivos contradictorios en un solo pipeline (operacional limpio, laboratorio permisivo, descubrir lo que MIROVA pierde). Tiering A/B/C. *Tensión*: Llaima/Copahue/NdC entran como Tier C por 0–2 refs MIROVA — en S13 con OSF v2.5 Copahue tiene 4,168 refs y Llaima 741. **El tiering S9 era falso por dataset incompleto, y se mantuvo operacional 5 sesiones sin revisitarse.**

**S10**: `enable_vent_path_modis=false` en meq (L10.1). *Por qué físico*: un pixel MODIS de 1 km diluye una fumarola sub-pixel; S/N activa/control es 2.5× MODIS vs 4.3–5.0× VIIRS. **S12 lo revirtió** (`enable_vent_path_modis=true` con threshold 2.5K y floor 0.3 MW) bajo experimento E1. Contradicción no registrada explícitamente: la decisión S10 fue "MODIS 1 km físicamente no puede", S12 dice "sí con umbrales altos". Ninguna re-evaluó si el argumento de S10 seguía en pie con los nuevos umbrales.

**S11**: Path C solo en `experimental`. *Por qué*: abrir un tercer path relativo (3σ_NTI) sube sensibilidad pero arriesga FPs — gate conservador. *Problema descubierto*: el bloqueante `store.py MAX_HOTSPOT_DIST_KM=5` mata los 24 detectados de PP porque caen a 5–10 km del cráter principal. Pregunta a Nicolás sobre extensión fumarólica de PP **no resuelta** en sesión; nunca se volvió al tema.

**S12**: F1b sigma cap (`MAX_VENT_SIGMA_CONTRIB_K=3K` en meq, 5K en exp). *Por qué físico*: volcanes de >5000 m con σ_bg inflado por nieve/roca mixta producían umbral efectivo 6–10 K, matando señales reales de 1–2 K sub-pixel. *Resultado*: recall sistema 35% → 60%. *Trade*: FPs extras aceptados como sub-MIROVA-threshold (0.1–1 MW).

**S13**: Re-tiering implícito con OSF v2.5, *pero no ejecutado*. Se identificó la disponibilidad pero el re-audit con 615K refs quedó pendiente. Fix trivial `WOOSTER_COEFF=18.0` en VIIRS 375m.

**S14 D1–D5**: El gran aprendizaje arquitectural. *Por qué físico*: MIROVA no tiene máscaras geométricas. Es grilla cuadrada UTM 51×51 km + clasificación visual por distancia al vent. Toda la complejidad S9–S12 (geofencing per-volcano, polígonos Llaima/Conguillío) fue re-invención de una física que MIROVA nunca usó. *Validación empírica*: coeficientes MIR por sensor derivados directamente de OSF v2.5 (`VRP / (Tot_hot - Tot_bk)`) reprodujeron cada fila con error ≤0.17%. Resolvió en 1 minuto la duda Di Bella k=2.48×10⁷ vs Laiolo k=18.0 que había ocupado S11–S13.

---

## 3. Aprendizajes operacionales consolidados (patrones transversales)

Estos son los patrones que se repiten entre sesiones, distintos de A1–A5 ya en CLAUDE.md:

**A6 — El constraint vinculante se mueve al fixear otro constraint.** L6.1 → L7.3 → S12 F1b. Cada vez que se arregló un gate, el que era inerte se volvió binding. La regla "correr diagnósticos **después** del fix, no solo antes" debería ser skill automática.

**A7 — Los datasets de referencia mutan silenciosamente.** OCR (S5) → consolidado (S7) → clasificación NULO descubierta (S8) → consolidado 10042026 (S10) → consolidado 14042026 (S12) → OSF v2.5 615K (S13). Cada cambio invalidó métricas anteriores y re-escribió tiering. **Ninguna sesión chequeó primero "¿cambió el dataset de referencia desde última vez?".** Todas las calibraciones hasta S14 usaron refs incompletos/sesgados.

**A8 — Cuando una regresión aparece sin explicación, NO avanzar.** S11: Lascar recall 0.79→0.56 (+44 FN) al introducir Path C. "Sin investigar — posible causa MODIS". S12 siguió con F1b, S13 con biblio, S14 con geometría. **Cuatro sesiones después la regresión Lascar sigue sin auditar**; puede haber quedado oculta dentro de los números S12 "recall Lascar 55%".

**A9 — Las preguntas geológicas a Nicolás se abandonan.** S11 preguntó "¿la actividad fumarólica de PP llega a 5–8 km?" → no respondida; Path C quedó gated. S9 preguntó por Peteroa/PlanchonPeteroa merge → resuelto recién S12. Regla: cualquier pregunta abierta a Nicolás debería tener fecha de seguimiento, no morir en el markdown.

**A10 — "Validado empíricamente con data publicada" > "derivado de paper".** S14 reprodujo A1 a escala grande: OSF v2.5 resolvió en minutos discrepancias (k_MIR, arquitectura MIROVA, tiering real) que ocuparon sesiones. **Corolario**: la bibliografía S13 fue útil pero sobredimensionada — el Rosetta stone era la base de datos publicada, no los 62 papers.

**A11 — Los fixes triviales se pierden entre sesiones.** `WOOSTER_COEFF=18.0` se descubrió S13 como "no crítico, el próximo NRT refleja el cambio". En S14 resultó que ni eso era correcto (19.7 para VIIRS M-band). Un fix anunciado pero no verificado en el NRT siguiente no cuenta como aplicado.

**A12 — El perfil `experimental` acumula deuda.** Path C, E4 min_vent_pixels=2, E5 Tupungatito ratio 0.71, sigma cap 5K. Ninguno fue promovido ni rechazado formalmente. El perfil funciona como cajón de sastre, no como laboratorio con criterios de salida.

---

## 4. Deuda técnica y cosas olvidadas

### TODOs abiertos explícitos
- **Test 1 integrado-ROI (Coppola 2015 Eq.1)**. Plan completo en `plan_s13_test1_integrated_roi.md`, presupuesto 5–7 h. **Nunca implementado**. Villarrica sigue 0% recall desde S9 hasta S14. Única respuesta al gap arquitectural, seis sesiones postergada.
- **Lascar recall regression** (0.79→0.56 en S11 con Path C). Flagged como "sin investigar — posible causa MODIS". Nunca auditado.
- **store.py `MAX_HOTSPOT_DIST_KM=5`** como bloqueante Path C en PP. Respuesta de Nicolás pendiente desde S11. S14 lo oculta bajo `inner_radius_km=3` para PP pero no resuelve: la lógica `store.py` sigue zerando `vrp_eruption` a >5 km.
- **Re-tiering con OSF v2.5**. Anunciado en S13 ("Villarrica pasa de 6 a 5,211 refs reales"). Jamás ejecutado. El audit S14 sigue citando números S12 contra refs 14042026.
- **NdC timeout en GitHub Actions** (step 25 min) — mencionado S12, sin fix.
- **Chaitén precision 0.12** (134 FPs vent-only 0.1–1 MW). S12 flagged "fumarolas reales vs ruido estructural". Sin investigar.
- **E4 decision** (`min_vent_pixels=2` en meq): −39% FPs, −15 pp recall. Trade-off sin resolver desde S12.
- **E5 Tupungatito ratio 0.71**: subestimación sistemática. Abierto desde S12.
- **Click-to-highlight tabla→mapa**, filtro fecha custom: features S12 en `todo.md`, jamás tocados.
- **Pritchard 2022 duplicado PDF**: marcado en S13, no verificado.
- **Decisión pendiente S14**: commit + push o review visual primero. Handoff dice "B primero, después commit". Al iniciar S15 retomar.

### Archivos huérfanos en `experiments/`
- `Chaiten_pre_F1.json`, `Isluga_pre_F1.json`, `Lascar_pre_F1.json`, etc. — snapshots pre-F1 de S9/S10. No referenciados por ningún código activo. OK para archivar/borrar.
- `lascar_baseline_pre_E1.json`, `lascar_session5_snapshot.json` — baselines S5/S6. Valor histórico pero cero uso operativo.
- `F0_validation.md`, `F1_validation.md`, `ROOT_CAUSE_S9.md` — docs vivos S9–S11, no referenciados desde S12. Estado desconocido de RF1/RF2/RF5 allí.
- `audit_s9/`, `audit_s10/`, `audit_s11_experimental/`, `audit_s12_experimental/` — snapshots por sesión sin limpieza. La convención implícita es "un directorio por sesión" pero nadie lo compacta.
- `frontend/llaima_anomalies.png`, `frontend/planchonpeteroa_anomalies.png` — diagnósticos S11/S12 sueltos en frontend, marcados en handoff S11 como "NO commitear", siguen en working tree.
- `data/mirova/PlanchonPeteroa_OLD_pre_consolidado.json` — modificado en S14 sin relación directa al cambio, flagged en handoff para revisar antes de commit.
- `volcanoes.yaml.S13backup` — rollback local S14, no commitear.

### Cosas prometidas en S_n y nunca hechas
- S7 pidió cross-check independiente (SERNAGEOMIN eruption logs, Sentinel-2, NOAA HMS). Cero progreso hasta S14. Seguimos calibrando contra MIROVA circularmente — L7.1 sigue vigente en 2026-04-21.
- S9 Phase 4 "Memory and docs cleanup" — READ-only hasta S14; `memory/project_vrp_chile.md` citado como "8 días viejo" con claims posiblemente falsos.
- S10 Task 5 "Re-auditoría final con FNs explicados" — el audit S10 se corrió pero la tabla "cada FN con explicación" nunca se produjo.
- Publicación formal de paper/reporte: mencionada en S12 como motivación de `mirova_equivalent`, sin avance.

---

## 5. Riesgos latentes

**R1 — Cero tests en producción.** Los únicos tests son `tests/test_nti_relative_path.py` (8 unit tests para Path C S11). `pipeline/process_modis.py`, `process_viirs*.py` — cero tests. Cada fix desde S6 se validó por reprocess + audit, que tarda horas y es manual. Una regresión silenciosa (como la Lascar S11) no se detecta en CI. **Llevamos 14 sesiones operacionales sin safety net.**

**R2 — Coeficientes nunca re-verificados post-cambio.** `WOOSTER_COEFF` cambió en S13 (18.9→18.0) y S14 (750m→19.7). La verificación S14 es empírica vs OSF (error ≤0.17%), pero S13 fue "voy a confiar en Laiolo". *Hasta S14 corrió 5 días de NRT con coeficiente teóricamente malo* que nadie auditó. El pipeline lleva commits NRT diarios con cambios no validados.

**R3 — NRT corre con código no-matcheado al working tree.** S14 está full of working-tree changes **sin commitear** mientras el NRT cron genera JSONs con el código S12. Riesgo: si hoy (2026-04-21) un volcán activa y MIROVA detecta, nuestro dashboard lo muestra con el schema viejo (`hotspot_*` en vez de `final_hotspot_*`). El handoff lo documenta pero no hay hook que detecte esta divergencia.

**R4 — Fork `experimental` como colador.** Path C, E4, E5, sigma cap 5K — son cuatro decisiones que "viven en experimental". Nadie recuerda cuáles eran trade-offs accesorios vs cuáles son hipótesis activas. El perfil se parece más a deuda que a laboratorio.

**R5 — MIROVA circularity.** L7.1 lo advirtió hace 14 días. Sigue vigente. Las decisiones S14 "MIROVA es autoridad" (A5) **refuerzan** la circularidad, no la rompen. Si MIROVA sub-detecta a 5500 m altiplano, nuestro pipeline "equivalente" también lo hará, y ninguna auditoría detectará esa clase de error.

**R6 — `data/mirova_reference/` sin plan de commit.** 98 MB CSV OSF v2.5 en working tree. S14 handoff sugiere `.gitignore` + README. Si alguien hace `git add -A` por error → push rejected (50 MB warning) o peor: LFS accidental sin configuración. Es una bomba latente.

**R7 — Vent coords de campo de Nicolás (S12) no documentadas como "ground truth frozen".** PCC lacolito -40.525499, Chaitén domo -42.834, Villarrica lava lake -39.420, Lascar V -23.363, Tupungatito -33.389. Están hardcoded en `volcanoes.yaml`, pero no hay nota de procedencia. Si alguien hace refactor y los toma por valores MIROVA, el pipeline pierde la base física validada por el geólogo.

**R8 — Llaima 139 FPs documentados como "lake thermal noise" (memoria) sin filtro.** S14 dice "los hits del Conguillío caen en distance_class=far, problema resuelto". Pero `far` aún se dibuja (en gris). El operador puede interpretarlos como señal si no lee la leyenda. El diseño MIROVA sí los dibuja también — pero MIROVA tiene la autoridad de su marca; nosotros no.

---

## 6. Recomendaciones concretas para S15+

1. **Test suite mínima antes de cualquier nuevo feature.** Un test por path (A/B/C + vent + eruption) con granule fixture. Fail si `WOOSTER_COEFF` no coincide con OSF dentro de 0.2%. Si un commit cambia detecciones en Lascar Feb 2026 sin update de fixture → CI roja. Costo estimado: 4–6 h. Paga después del primer rebuilt silencioso.

2. **Cerrar la regresión Lascar S11 antes de commitear S14.** 44 FN aparecieron con Path C. O Path C tiene efecto secundario en MODIS, o el reprocess S11 rompió algo en pairing. Correr audit comparativo `data/mirova_equivalent/Lascar.json` pre-S11 vs post-S11 (snapshots existen). Si el diagnóstico tarda <1 h, hacerlo. Si no, al menos abrir issue explícito con fecha y no cerrarlo con S14.

3. **Re-audit completo con OSF v2.5 antes de declarar paridad.** El handoff S14 propone Paso 1b (Nov 2025, 4 volcanes, cross-match contra OSF). Ejecutarlo **antes** del commit+push S14, no después. Si paridad [0.8–1.25] no se cumple, el commit S14 es prematuro.

4. **Plan formal para el perfil `experimental`.** Inventariar qué vive ahí (Path C, E4, E5, sigma cap 5K). Para cada uno: criterio de salida (métrica numérica) + deadline. Los que no cumplan en 2 sesiones → eliminados explícitamente, no solo abandonados.

5. **Implementar Test 1 integrado-ROI (Coppola 2015 Eq.1) o cerrar formalmente Villarrica como "non-calibratable".** No puede quedar "0% recall, ver backlog" por sexta sesión consecutiva. Si no hay budget → decisión explícita: Villarrica queda Tier D (documented limitation), y se lo comunica en el dashboard. Lo que no se hace, se archiva con honestidad.

---

*Fin auditoría S1 → S14.*
