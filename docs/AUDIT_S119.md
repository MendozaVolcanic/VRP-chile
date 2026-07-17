# AUDIT S119 — Auditoría integral post-S118 (flip gates C2 OFF)

**Fecha**: 2026-07-01 · **Plan**: `docs/superpowers/plans/2026-06-28-s119-auditoria-integral.md`
**Contexto**: S118 flipeó a OFF los 2 gates intra-radio (PR #474, tag `pre-s118-c2-flip`).
NRT corre con gates OFF desde 2026-06-28 ~21:00 UTC. Scripts fuente de los números (S91):
`experiments/_s119_audit/`.

## §1 — Verificación post-flip C2 (Eje 1, BLOQUEANTE) — ✅ VERDE, MANTENER OFF

**Veredicto: MANTENER OFF. Ningún criterio falla en modo sistemático. No se ejecuta rollback.**

| Check | Resultado | Evidencia |
|---|---|---|
| 1.1 NRT verde | **PASS** — 100% success en ~20 runs post-flip (2026-06-28 21:00 → 2026-07-01) | `gh run list --workflow=nrt.yml` |
| 1.2 Firma del flip | **PASS** — recaptura mediana estable (0→0 en 10/11; Isluga 1→0.5); records/noche estable (±15%, leve suba Villarrica 10.9→13.7 por rampa térmica real) | `eje1_postflip.py` → `eje1_postflip.json` |
| 1.3 Sin inflación summit | **PASS con matiz** — ver análisis abajo | ídem |
| 1.4 Dashboard sano | **PASS** — index (45 cards), diario (12 canvas), mosaico (11 celdas): 0 errores consola, 0 requests fallidos | preview localhost:8091, eval headless (lección S118 viewport-0) |
| 1.5 JSONs bajo control | **PASS** — 549 ins/commit post-flip vs 682 pre-flip (cap top-100 anomaly_pixels contiene el footprint) | `git log --shortstat -- data/mirova_equivalent/` 06-21→07-01 |

### Análisis 1.3 — los flags de Villarrica NO son el flip

El script flaggeó Villarrica con ratio summit 2.3–5.4× vs mediana histórica 30d en todos los
sensores VIIRS. Diagnóstico (fenómeno primero):

1. **La subida empieza el ~16-jun, 12 días ANTES del flip, con gates ON.** Mediana summit
   `pc.vrp_mw` VIIRS375 por bin de 5 días: 0.04–0.09 MW (26-may→15-jun) → **1.28 MW
   (16-jun)** → 1.40 → 1.59 → **1.53 MW post-flip (plano)**. El flip no movió el régimen;
   la ventana de referencia de 30d mezclaba la quincena fría y por eso el ratio salió alto.
   Físicamente: escalada térmica del sistema (o amplificación invernal A69 con nieve nueva);
   MIROVA consolidado muestra 0.0/RUTINA en las mismas noches → el exceso es el
   sobre-registro sistémico Villarrica ya documentado (A68), PRE-existente al flip.
2. **Cola path-D (el costo aceptado del flip)**: records summit path-D-dominados
   (Test1=0, pc>1 MW): PCC 16 en 14d pre-flip (~1.1/día, con gates ON) vs 3 en ~2.8d
   post (~1.1/día) — **tasa plana**. Villarrica 1 pre → 3 post (durante su rampa).
   Único outlier: **MODIS_AQUA 2026-06-30 07:00, 28.8 MW, 4 píxeles todos path-D** =
   modo peor-caso que el A/B S118 ya predijo y aceptó (análogo PCC 56 MW). 1 caso ≠
   rollback (criterio del plan). PCC watch: 0/3 noches con summit >20 MW (umbral 10%).
3. Tupungatito 0.31× (n=3) es deflación con n chico, dirección opuesta a la que produciría
   el flip — ruido.

**Item para Eje 2/3**: la rampa Villarrica 06-16 (0.06→1.4 MW mediana, MIROVA en 0.0)
merece el cruce espacial A61 y la mirada de Nicolás en el dashboard — ¿lago de lava
reactivado (cat-b real) o amplificación de nieve fresca invernal (A69)?

## §2 — Paridad clon MIROVA con ground truth refrescado (Eje 2, subagente) — ✅ SIN REGRESIÓN

Fuente: `experiments/_s119_audit/eje2_*.{py,json}`.

- **2.1 Ground truth A17 refrescado**: CONS 17,966 → **25,210** filas (+7,244); OCR 520 →
  **737** (+217). Snapshot del loader canónico reemplazado (committed en esta sesión).
- **2.2 Recall al cráter (criterio S114)**: ventana comparable → VIIRS375 **98.4%** (=S116),
  VIIRS750 **84.5%** (−0.5pp), MODIS-cráter **100%**. Sin caída >5pp. El full-2026 más bajo
  (91.9/79.7/97.5) es efecto ventana (ene-abr predata los fixes S102-S112), no regresión.
- **2.3 Magnitud A10** (mediana pc/MIROVA, noches comunes 2026): 9/11 en banda, nadie
  sobre-estima. Fuera solo por abajo: Lastarria 0.466 (cat-b Lazufre conocido — MIROVA
  integra el campo, nuestro pc ancla el cluster) y Llaima 0.357 (n=2, sin significancia).
- **2.4 Espacial A61/A70: SIN sesgo nuevo.** Flags >2 km se descomponen en conocidos
  (A46/A82 far MODIS; residuo A69 N/NE 0.5-1.5 km; dispersión PCC A19). **WATCH menor**:
  Copahue VIIRS375 rumbo **S** ~1.2-1.3 km direccional (n=110, estable) — cotejar posición
  del cráter El Agrio vs vent configurado (−37.856, −71.183) con Nicolás (Eje 3).
- **2.4-extra Villarrica 16-jun — REAL confirmado por OCR + amplificación invernal encima.**
  El OCR fresco tiene 4 ALERTA_TERMICA_OCR jun-2026 (VIIRS375: 03-jun 0.39, 06-jun 0.28,
  **15-jun 0.54 MW @ 0.81 km**, **16-jun 0.46 MW @ 0.95 km**): MIROVA ve el lago de lava AL
  CRÁTER pero no lo publica en consolidado (patrón A11). Nuestra serie post-16: mediana
  1.44 MW @ 1.29 km. Veredicto: **reactivación real del lago (~0.5 MW según MIROVA-OCR),
  nuestra magnitud ~3× por régimen nevado invernal** — vigilar, no es artefacto puro ni bug.
- **2.5 Límites del A/B S118 (honestidad)**: ventana ene-may (no cubre invierno ni
  post-flip); cap 4 chunks/vol dropeó ~50-60% de noches ALERTA en 5 focales; control nevado
  débil (Llaima/Copahue 1 noche c/u). El "0 robos" focal es robusto (214 noches); el nevado
  descansa en n chico — el post-flip live (§1) es ahora el control continuo.

### Cruce 3.4 vs 2.3 — discrepancia EXPLICADA (mezcla de sensores en Panel 1)

El Panel 1 da PCC 5.07× / Chaitén 6.14× donde el Eje 2.3 da 0.889 / en banda. No es bug de
datos: el Panel 1 cruza **máximo diario mezclando sensores** — nuestro máx viene del sensor
grueso (PCC: 43/74 días MODIS + 26/74 VIIRS750, solo 5/74 VIIRS375) mientras MIROVA publica
mayormente VIIRS375. Reproducido exacto por script (5.07×). El difuso a resolución gruesa
domina el máximo diario → ratio inflado. **Fix candidato (frontend puro, Eje 7)**: matchear
por bucket de sensor o agregar filtro de sensor al Panel 1.

## §3 — Vista Beyond MIROVA (Eje 3, parcial — 3.1/3.2 requieren a Nicolás en navegador)

- **3.4 Panel 1 barrido 11 vols** (ratio mediano geométrico días-comunes, ventana 365d,
  fuente `experiments/_s119_audit/eje3_panel1.json`):

  | Vol | ratio | n días | Vol | ratio | n días |
  |---|---|---|---|---|---|
  | Láscar | 0.70× | 135 | Copahue | 1.62× | 2 |
  | Lastarria | 1.27× | 106 | Llaima | 1.02× | 1 |
  | Isluga | 1.09× | 105 | Villarrica | 1.00× | 8 |
  | Tupungatito | 1.10× | 82 | **PCC** | **5.07×** | 71 |
  | NdC | 1.18× | 5 | **Chaitén** | **6.14×** | 24 |
  | **PP** | **2.58×** | 64 | | | |

  8/11 en banda [0.5, 2.0]. Fuera de banda: PCC (lacolito difuso, cat-b sobre-estimada por
  suma a resolución gruesa — conocido S91/A19), Chaitén (domo, mismo mecanismo — cruzar con
  Eje 2.3) y PP (complejo multi-cráter bimodal A22 — conocido). Cruce con Eje 2.3 pendiente
  de consolidación (deben coincidir; si difieren hay bug de loader).
- **3.3 Panel 2a post-flip**: zonas siguen separando bien — Láscar 97% proximal (980/1015);
  PCC dominado por extensión cat-b (1170/1440) con dispersión 240 (~17%, la cola VIIRS750
  conocida A19); Villarrica 1003 proximal / 90 dispersión. Sin salto atribuible al flip
  (records/noche estables §1). La cola de dispersión concentra MW grandes far (honestidad
  del display, el operacional los filtra).
- **3.5 Discoverability**: ✅ link a `beyond-mirova.html` agregado al banner de
  `frontend/experimental/index.html` (verificado en preview).
- **3.1/3.2 (Nicolás, navegador real)**: pendiente validación visual de las 3 pestañas +
  afinado de zonas 2a por volcán (hoy solo PCC documentado, Lastarria/Villarrica preset).
- **3.6 Panel 2b Eq.16**: diseño confirmado viable (flag `enable_test1_lava_lake_eq16`
  cableado flag-OFF, perfil `_s99_test1_eq16` existe) — reproc dirigido Villarrica queda
  como candidato Eje 7.

## §4 — Integridad de datos e higiene (Eje 4, subagente) — ✅ SANO

Fuente: `experiments/_s119_audit/eje4_integridad.json` + `eje4_workflows_profiles.json`.

- **4.1 Integridad 45 JSONs: PASS** — 0 errores de parseo (A47), 0 duplicados
  (datetime_utc, sensor), guard A46 en 0 (ningún summit con centroide fuera del inner sin
  `cluster_rescue`). Los 481 records `primary_cluster` null con `vrp_mw>0` NO son bug:
  475 Tier C schema legacy scene-wide + 6 Villarrica vent-path sub-píxel.
- **4.5 Suite: 797 passed, 0 failed, 0 skipped** (con `-s`, workaround S96 vigente) —
  idéntico a S118, R2 pixel-level activo (encuentra el TIF archive sibling).
- **4.3 Workflows**: 6 activos necesarios; **28 candidatos a archivar** (probe-s10x +
  reproc-s101..s118, todos con última corrida ≤2026-06-28; destino existente
  `.github/workflows/_archive/`). Incluye `reproc-s118-c2-gates-ab.yml`.
- **4.4 Profiles**: 122 yaml — 2 operacionales; 4 `_c2ab_*` QUEDAN (reproducibilidad flip);
  22 referenciados por tests (NO archivar sin refactor); ~90 huérfanos candidatos a archive
  bajo tag A38 (lista en JSON).
- **4.2 Artifacts S118**: 86 MB gitignored, borrado seguro (results.json + windows.json
  committed) — **decisión de Nicolás pendiente**.

## §5 — Docs vivos (Eje 5) — ✅ ACTUALIZADOS

- `MIROVA_DIVERGENCES.md`: entrada gates S84/S85 → **RESUELTO S118** (flip OFF + post-flip
  verde) con el detalle del A/B y la exclusión del per-régimen (MISSION l.77).
- `MISSION.md`: P2-lista → resuelto S118; tabla anti-patrones → "Removido S118"; sección
  familia gate intra-radio → párrafo de cierre.
- `HYPOTHESIS_LOG.md`: nueva entrada `H_S118_C2_GATES_NO_THEFT` → **REFUTADA** (0 robos).
- `CLAUDE.md` proyecto: **regla A85** agregada (medir robo real antes de cercar; per-régimen
  excluido por MISSION l.77) — a validar por Nicolás.
- Backlog vivo: sin muertos nuevos; lista priorizada en §7.

## §6 — Cabos sueltos S118 (Eje 6, subagente) — ✅ CERRADOS

Fuente: `experiments/_s119_audit/eje6_*.{py,json}`.

- **6.1 Mecanismo pathd_off — EXPLICADO (A48 cerrado; hipótesis μ/σ REFUTADA).** Los
  11 records (6 Láscar + 5 NdC, todos MODIS) con VRP distinto y npix idéntico difieren
  solo en `diag_n_dnti_ctx_path` y `pc.vrp_mw`. El gate path-D (`process_modis.py:563-570`)
  no participaba de la detección (first-pass la reemplaza, `:736`) pero SÍ recortaba la
  máscara de selección de la **magnitud núcleo-focal S109** (`cluster_focal_vrp_mw`,
  `process_modis.py:986/:1235`, `vrp_regimes.py:214`). Gate OFF → el halo ctx-anómalo del
  cluster vuelve a contar en la magnitud focal (11/11 con pc.vrp mayor, varios saturando el
  cap D9 de 5.0 MW). Efecto solo de magnitud, acotado por el cap, detección intacta.
- **6.2 Encoding cp1252**: 7 scripts ofensores / 14 líneas (lista en
  `eje6_2_encoding_scan.json`; `_s118_c2ab/` limpio). Fix barato pendiente (bajo).
- **6.3 Guard A46 LIVE**: 7 tests passed + spot-check post-flip 368 records / 182 summit /
  **0 violaciones**.
- **6.4 Breakers NRT**: 12/12 runs success; breaker LANCE tripeó 2/4 runs muestreados
  (2026-07-01, `nrt3.modaps` ConnectTimeout 188s → skip instantáneo en cascada, A64
  degradando con gracia); 0 trips CMR. LANCE intermitente sin impacto operacional.
- **6.5 R2 post-flip**: agendado — cuando MIROVA publique TIF comparable de una fecha
  post-flip, correr 1 R2 pixel-level de la era gates-OFF (backlog S120).

### Hallazgos adicionales S119 (descubiertos consolidando, fixes aplicados)

- **Pytest recolectaba pseudo-tests de `experiments/`** (`_s90_display_artifact/
  test_criterion.py`, `_s99_audit/modis_diffuse/test_crater_core.py`): al correr la suite
  sin ruta explícita, re-ejecutaban análisis históricos sobre data ACTUAL y sobreescribían
  sus outputs committeados (test_criterion.txt +1405 records, test_*_result.json). Outputs
  históricos restaurados con `git checkout`; **fix: `testpaths = tests` en `pytest.ini`**.
  Conteo limpio de la suite: **796 passed** (el "797" de S118 incluía 1 pseudo-test).
- **Crash cp1252 en suite local**: el mensaje `_diag` del breaker CMR
  (`pipeline/fetch.py:451`) imprime `→`; con `-s` en consola Windows cp1252 los 5 tests
  que ejercitan ese path crasheaban con UnicodeEncodeError (en GH Actions Linux no pasa).
  **Fix sin tocar pipeline (A45): `tests/conftest.py` reconfigura stdout/err a utf-8.**
  Queda propuesto (Eje 7, trivial) cambiar `→` por `->` en los mensajes runtime de
  `fetch.py` la próxima vez que se abra ese archivo con ciclo A45.

## §7 — Plan de avance (Eje 7 — priorizar con Nicolás)

Con Ejes 1-6 verdes, candidatos ordenados por mi recomendación (decide Nicolás):

**Clon MIROVA:**
1. **Backfill histórico VIIRS375+V750** (AUDIT_S112) — con gates OFF la data backfilled
   nace ya clon-literal; es el momento natural. Corre local (A15/GH 6h limit).
2. ~~**GAP #A** (retiro píxeles Test1 K1 del pool μ/σ)~~ — **RESUELTO S115 = mislabel, NO
   es gap** (corregido S121; ver DIVERGENCES:1292 + AUDIT_S114:232). NO reabrir.
3. **NEW-8 pool m,σ** — re-evaluar contra data post-flip (D9 curada la rebajó).

**Beyond MIROVA:**
4. **Panel 2b Eq.16** — reproc dirigido Villarrica perfil `_s99_test1_eq16` (diseño 3.6);
   oportuno con el lago reactivado (§2.4-extra).
5. **Zonas 2a afinadas por Nicolás** (3.2, navegador) + cotejo cráter El Agrio Copahue
   (WATCH §2.4) → después considerar promover a `geo_class` display experimental.
6. **Panel 1 match por sensor** (fix display §2-cruce) + integrar distancias OCR (F-B2).

**Higiene (batch único, bajo riesgo):**
7. Archivar 28 workflows one-shot + ~90 profiles huérfanos (tag defensivo A38) + borrar
   `_s118_c2ab/_artifacts/` 86 MB (OK de Nicolás) + fix 7 scripts encoding + `→` en
   fetch.py (ciclo A45 conjunto).

## §8 — Mejoras a la auditoría (pedido de Nicolás S119: "¿se puede mejorar?")

La auditoría integral actual (A51, cada ~20 sesiones + Eje 1-7 ad-hoc) cubre bien
detección/paridad/docs. Los huecos están en las etapas que NO miramos por episodio.
Mapa etapa-por-etapa del pipeline con el gap y la mejora concreta:

| Etapa | Qué auditamos hoy | Gap | Mejora concreta |
|---|---|---|---|
| **Fetch/adquisición** | NRT verde/rojo, breakers (episódico) | No medimos **cobertura**: pasadas esperadas vs procesadas por plataforma/noche. Un sensor que desaparece en silencio (ej. NOAA-21 v2.1) es invisible hasta que cae el recall | Script de cobertura: records/plataforma/día vs baseline 30d; alerta si una plataforma cae >50% 3 días seguidos |
| **Latencia NRT** | Nada | No sabemos el lag pasada→dato-en-dashboard (el valor operacional para OVDAS) | Métrica `datetime_utc` vs timestamp commit NRT; percentiles semanales |
| **Proceso/detección** | Paridad recall/magnitud/espacial vs MIROVA (episódico, manual) | La auditoría es **episódica**: un drift entre auditorías vive semanas (ej. rampa Villarrica la vimos por casualidad del Eje 1) | **Auto-audit continuo**: job semanal (cron GH) que corra recall/ratio/espacial rolling-30d contra CSV fresco y committee un JSON + badge; si sale de banda → issue automático. Convierte A51 en monitoreo |
| **Store/schema** | Integridad 4.1 (episódico) | Un campo nuevo asimétrico (vector A46) entra sin chequeo | Validación de schema (jsonschema) como test de la suite + en el step NRT antes del commit |
| **Data/ground truth** | A17 refresh manual por sesión | El snapshot del loader queda stale entre sesiones (hoy: 7,244 filas atrasado) | Extender `sync-mirova-csv` para refrescar también el snapshot del loader (hoy solo root) |
| **Frontend** | Preview manual 3 vistas + eval | Sin CI: una regresión de display (ej. datetime S115) espera a que alguien mire | Smoke-test CI en PR: headless que cargue las 4 páginas y falle con console errors / data no cargada |
| **Suite/tests** | passed/failed (episódico) | Hoy encontramos 2 debilidades: pseudo-tests de experiments + crash cp1252 (ambas arregladas). El patrón: la suite local y la de CI difieren de entorno | Correr la suite también en CI Windows (matrix) o al menos documentar el entorno canónico |
| **Docs/memoria** | Eje 5 manual | Links rotos / referencias stale entre docs (INDEX, specs) no se detectan | Linkcheck script sobre docs/ (barato, en el auto-audit semanal) |
| **Seguridad/ops** | Nada recurrente | PAT en settings.json (pendiente global), .netrc local inválido (A71), secrets sin rotación programada | Checklist trimestral en el auto-audit + recordatorio de rotación |
| **Runtime/perf** | Timeouts cuando explotan (A15) | No trackeamos la duración por volcán del NRT (creep silencioso hacia el timeout de 50 min) | Parsear duración de steps de los runs en el auto-audit semanal; alerta si p95 >35 min |

**Recomendación central**: el ítem de mayor palanca es el **auto-audit semanal** (fila 3):
un workflow cron que ejecute los mismos scripts S91 de esta auditoría (recall, ratio A10,
espacial A61, cobertura, integridad) contra el CSV fresco y persista
`data/audit_continuous/latest.json`. La auditoría integral humana (A51) pasa de "redescubrir
el estado" a "revisar excepciones". Los scripts ya existen (`experiments/_s119_audit/`) —
es empaquetarlos. Costo: 1 sesión. Propuesto para S120 si Nicolás prioriza.
