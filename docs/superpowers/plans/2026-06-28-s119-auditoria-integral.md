# Auditoría Integral S119 — Plan de ejecución

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) o superpowers:executing-plans para ejecutar tarea por tarea. Checkboxes
> (`- [ ]`) para tracking. Ejes 1-6 son READ-ONLY (auditoría); solo Eje 7 propone cambios
> y cada uno queda gateado (A45 donde aplique).

**Goal:** auditar TODO el trabajo S118 (flip C2 + A/B + vista Beyond MIROVA) y el estado
de ambos frentes (clon MIROVA + beyond MIROVA) con data fresca post-flip, antes de avanzar.

**Arquitectura:** 6 ejes de auditoría paralelizables (subagentes A26/A51-style, worktrees
dedicados si tocan git A44, read-only donde aplique) + 1 eje de plan de avance. El eje 1
(post-flip) es BLOQUEANTE: si detecta regresión operacional, se ejecuta el rollback
(`git checkout pre-s118-c2-flip -- pipeline/profiles/mirova_equivalent.yaml` + revert
guards) ANTES de seguir con el resto.

**Contexto mínimo para sesión fría:** S118 flipeó a OFF los 2 gates intra-radio del
operacional (PR #474, tag `pre-s118-c2-flip`, evidencia `docs/AUDIT_S118_C2_GATES_AB.md`:
0 robos de cluster en 214 noches focales; costo = cola inflada 0.5-1.3% mayormente far).
El NRT (cron 2h) procesa con gates OFF desde el merge. También se creó
`frontend/experimental/beyond-mirova.html` (pestañas: 2a zonas geo · 1 fidelidad · 2b
placeholder Eq.16). PRs S118: #470-474.

---

## Eje 1 — Verificación post-flip C2 (BLOQUEANTE, correr primero)

**Fenómeno a vigilar:** con las cercas OFF, la recaptura extra-radio vuelve al dato
persistido (~4-6× más píxeles en el footprint). Esperado: `far` records nuevos que el
frontend filtra + footprints más grandes. NO esperado (= regresión): summit records
inflados sistemáticos, robo de cluster real, NRT fallando por tamaño/tiempo.

- [ ] **1.1 NRT verde post-flip.** Run:
  `gh run list --workflow=nrt.yml --limit 12 --json conclusion,createdAt,displayTitle`
  Pass: ≥90% success en los runs posteriores al merge de #474 (2026-06-28+). Fail →
  leer logs del step que falla (`gh run view <id> --log-failed | tail -50`); si la causa
  es timeout por footprint/JSON gigante → candidato rollback.
- [ ] **1.2 Records post-flip existen y llevan la firma del flip.** Script (adaptar de
  `experiments/_s118_c2ab/analyze.py` helpers): para cada Tier A, filtrar records de
  `data/mirova_equivalent/<vol>.json` con `datetime_utc >= 2026-06-28 20:00` y comparar
  mediana de `diag_n_second_pass_recapture` contra records pre-flip de la misma semana.
  Pass: recaptura mediana igual o mayor (el gate ya no recorta); n_records/noche estable.
- [ ] **1.3 Sin inflación summit sistemática.** Sobre los records post-flip:
  `pc.vrp_mw` de summit vs la mediana histórica 30d del mismo vol/sensor (usar
  `experiments/_s118_c2ab/analyze.py` como base). Pass: ratio mediano en [0.5, 2.0]
  (banda paridad). Vigilar PCC especialmente (la noche difusa 56 MW del A/B es el modo
  de falla conocido; si aparece 1 caso aislado NO es rollback — es la cola aceptada;
  si aparece >10% de noches PCC → sí).
- [ ] **1.4 Dashboard renderiza sano.** Preview de `frontend/index.html` + `diario.html`
  + `mosaico.html` (server local, patrón S118). Pass: 0 errores consola, 11 Tier A
  cargan, chips "MIROVA dist" ok. NOTA lección S118: el preview headless tiene
  viewport 0×0 — verificar por eval/console/data, NO por screenshot.
- [ ] **1.5 Tamaño de JSONs bajo control.** `du -sh data/mirova_equivalent/` y
  `git log --stat -3 -- data/mirova_equivalent/` (commits NRT). Pass: crecimiento
  per-commit comparable al pre-flip (el cap top-100 anomaly_pixels ya acota; confirmar).
- [ ] **1.6 Registrar veredicto Eje 1** en `docs/AUDIT_S119.md` §1 con números del
  script (S91). Si CUALQUIER criterio falla en modo sistemático → rollback con tag +
  reportar a Nicolás ANTES de continuar.

## Eje 2 — Paridad clon MIROVA con data nueva (subagente A)

- [ ] **2.1 Refrescar ground truth (A17).** Descargar
  `https://raw.githubusercontent.com/MendozaVolcanic/Mirova-v1/main/monitoreo_satelital/registro_vrp_consolidado.csv`
  y `registro_vrp_ocr.csv` → reemplazar en `data/mirova_reference/mirova_v1_snapshot/`
  (el snapshot del loader quedó en ~2026-06; el root `latest_consolidado.csv` está más
  fresco pero el loader canónico lee el snapshot). Commit del snapshot nuevo.
- [ ] **2.2 Recall por sensor (patrón S114/S116).** Con loader canónico
  (`pipeline/mirova_csv_loader.load_mirova_alertas`) cruzar noches ALERTA vs records
  summit nuestros, por bucket (VIIRS375/VIIRS750/MODIS), ventana completa 2026.
  Referencia S116: VIIRS375 98.4% / V750 85% / MODIS-cráter 100%. Pass: sin caída >5pp.
- [ ] **2.3 Magnitud A10.** Ratio mediano `pc.vrp_mw` nuestro/MIROVA por vol (noches
  comunes). Referencia S118 Panel 1: Láscar 0.71×. Pass: banda [0.5, 2.0] en Tier A
  focales; documentar outliers con categoría física (A54: a/b/c/d) antes de llamarlos bug.
- [ ] **2.4 Eje espacial A61/A70.** Offset direccional MEDIANO (Δlat/Δlon + rumbo) del
  `final_hotspot` y del `pc.centroid` al vent físico, por vol y sensor, sobre data
  post-flip. Referencia: sesgo N ~1-1.5 km en nevados es el residuo A69 conocido
  (irreducible, NO reabrir). Pass: sin sesgo NUEVO (>2 km o rumbo distinto al conocido).
- [ ] **2.5 Cobertura del A/B S118 (honestidad).** Documentar en AUDIT_S119 §2 los
  límites del A/B: 6 chunks/vol focales DROPPED (cap 4, `windows.json > summary`),
  nevados Llaima/Copahue con 1 sola noche MIROVA (control débil), ventanas ene-may 2026.
  El veredicto focal es robusto (214 noches); el control nevado era secundario.

## Eje 3 — Vista Beyond MIROVA (subagente B + sesión con Nicolás)

- [ ] **3.1 Navegador real.** Nicolás abre `frontend/experimental/beyond-mirova.html`
  (Pages o local) y revisa las 3 pestañas. El render de píxeles NUNCA se validó en
  viewport real (lección S118 preview 0×0) — esta es la validación pendiente.
- [ ] **3.2 Afinar zonas 2a por volcán (criterio geológico de Nicolás).** Para c/u de
  los 11: arrastrar radios proximal/extensión hasta que la zona naranja coincida con el
  cuerpo volcánico real (Lazufre, lacolito, El Agrio, Pichi-Llaima...). Persistir los
  valores elegidos en el objeto `ZONES` del HTML (Edit + commit; hoy solo PCC tiene
  valores documentados, Lastarria/Villarrica preset, resto default inner_radius).
- [ ] **3.3 Panel 2a con data post-flip.** Los gates OFF persisten MÁS píxeles far →
  re-mirar PCC y Láscar en 2a: ¿la cola de dispersión creció? ¿las zonas siguen
  separando bien? (esto conecta Eje 1 con la vista).
- [ ] **3.4 Panel 1 barrido 11 vols.** Anotar ratio mediano por vol en AUDIT_S119 §3 y
  cruzar contra 2.3 (deben coincidir — misma data, si difieren hay bug en un loader).
- [ ] **3.5 Discoverability.** Agregar link a beyond-mirova.html en
  `frontend/experimental/index.html` (hoy no está linkeada — solo URL directa). Commit.
- [ ] **3.6 Panel 2b Eq.16 — plan concreto.** El flag `enable_test1_lava_lake_eq16` YA
  está cableado flag-OFF (`pipeline/vrp_regimes.py:105`, EXT-11, perfil `_s99_test1_eq16`
  existente). Tarea: reproc dirigido Villarrica (ventanas con lava lake activo, patrón
  `build_c2ab_windows.py`) sobre el perfil `_s99_test1_eq16` → artifacts → cablear la
  pestaña 2b leyendo `data/_s99_test1_eq16/Villarrica.json` como serie comparada
  (cruda vs Eq.16). NO toca operacional (perfil aislado). Diseñar en S119, ejecutar ahí
  o S120.

## Eje 4 — Bases de datos e higiene (subagente C, read-only + propuestas)

- [ ] **4.1 Integridad JSONs.** Script: parsear los 45 `data/mirova_equivalent/*.json`;
  reportar (a) parse errors (A47-style corrupción), (b) duplicados por
  `(datetime_utc, sensor)`, (c) mezcla `product_version` nrt/standard %, (d) records
  con `primary_cluster` null pero `vrp_mw>0` (incoherencia A46-style). Pass: 0 (a), 0 (b).
- [ ] **4.2 Artifacts locales S118.** `experiments/_s118_c2ab/_artifacts/` = 86 MB
  local gitignored. Propuesta: borrar (los datos viven en el run 28312968093 7 días +
  results.json committed destila lo que importa). Pedir OK a Nicolás (A38 espíritu).
- [ ] **4.3 Workflows viejos.** `reproc-s118-c2-gates-ab.yml` ya corrió; archivarlo
  (patrón PR #217: mover a `.github/workflows-archive/`). Ídem los `reproc-s10x` que
  queden activos sin uso.
- [ ] **4.4 Profiles A/B huérfanos.** Los `_c2ab_*` quedan (reproducibilidad del A/B
  citado por el flip). Los `_f_s81_*` (baseline S81 obsoleto) son candidatos a archive —
  proponer, no borrar (A38: tag defensivo si se remueven).
- [ ] **4.5 Suite + skips.** `python -m pytest -q -s` y `pytest -rs | grep -i skip`.
  Pass: 797+ passed; skips solo los conocidos/documentados (S116 cerró los 16+7).

## Eje 5 — Hipótesis, divergencias y docs vivos (subagente D, git-writing → worktree A44)

- [ ] **5.1 MIROVA_DIVERGENCES.md.** La entrada "gates intra-radio S84/S85 pendiente de
  decisión (S105)" → actualizar a **RESUELTO S118** (flip OFF, evidencia AUDIT_S118).
  Revisar abiertas restantes: D2 (cobertura CSV), D3 (FP explícito MIROVA), NEW-8
  (pool m,σ — S116 la rebajó, re-evaluar contra data post-flip), cara-posición D11.
- [ ] **5.2 MISSION.md.** Tabla anti-patrones l.130 ("Gate intra-radio por path...
  Identificado S86") → estado "**Removido S118** (A/B 0 robos, PR #474)". La sección
  l.137-147 (familia gate intra-radio) gana una línea de cierre. También P2-lista
  l.97-99 ("Pendiente de decisión... gates intra-radio") → resuelto.
- [ ] **5.3 CLAUDE.md proyecto — regla A85 candidata.** Lección S118 destilada: "la
  selección de cluster vent-anchored es robusta a píxeles extra-radio (A/B S118: 0
  robos con recaptura 4-6×); una cerca geométrica que 'protege' la selección es carga
  sin beneficio — medir robo real antes de cercar". Proponer texto a Nicolás.
- [ ] **5.4 HYPOTHESIS_LOG.md** entrada S118 (hipótesis "la cerca protege al cráter de
  robo de cluster" → REFUTADA con run 28312968093).
- [ ] **5.5 Backlog vivo.** Revisar `tasks/backlog_*.md` + bloque S118: qué sigue vivo
  (backfill VIIRS, FICHA exhaustiva opcional, display PCC extension, GAP #A retiro K1
  flag-OFF) y qué murió. Producir lista priorizada para Eje 7.

## Eje 6 — Bugs y cabos sueltos S118 (subagente E)

- [ ] **6.1 Mecanismo pathd_off no-explicado.** En el A/B, 6 records Láscar + 5 NdC
  difieren en VRP con `n_anomalous_pixels` IDÉNTICO y product_version idéntica.
  Hipótesis: los píxeles path-D far re-entrantes se descartan luego por geofence
  (`discarded_anomaly_pixels`) pero cambian μ/σ del second-run → misma cuenta, distinto
  VRP. Comprobar con 1 record (`experiments/_s118_c2ab/_artifacts`, comparar
  `discarded_n_pixels` y `diag_mu_dnti` entre brazos). Cerrar la explicación en
  AUDIT_S119 §6 (A48: no dejar mecanismos sin explicar en una adopción).
- [ ] **6.2 Encoding cp1252.** `grep -L "reconfigure\|utf-8" scripts/*.py` sobre scripts
  que impriman Unicode — el bug analyze.py se arregló; verificar que build_c2ab_windows
  y futuros no lo repitan (imprime `→`? sí, línea del warning — ya salió con `�` en
  S118; fix barato).
- [ ] **6.3 Guard A46 sigue LIVE** post-flip: correr el test
  (`pytest tests/ -k "coherence or a46" -q`) y 1 spot-check en data post-flip
  (records `summit` con `pc.centroid_dist_km > inner`: deben ser 0 o `cluster_rescue`).
- [ ] **6.4 Breakers NRT.** En logs del último NRT run buscar `CIRCUIT`/`BREAKER`
  markers: ¿tripearon LANCE/CMR esta semana? Frecuencia = salud de red NASA.
- [ ] **6.5 R2 pixel-level post-flip.** Los 7 tests R2 comparan contra TIFs de fechas
  viejas (pre-flip) — siguen válidos. PERO: agendar 1 R2 nuevo sobre una fecha
  post-flip cuando MIROVA publique TIF comparable (validación de la era gates-OFF).

## Eje 7 — Plan de avance ambos frentes (con Nicolás, al cierre de la auditoría)

Con los veredictos de Ejes 1-6 sobre la mesa, decidir prioridades. Candidatos:

**Clon MIROVA:**
- [ ] 7.1 Backfill histórico VIIRS375+V750 (AUDIT_S112; ahora con gates OFF la data
  backfilled nace ya literal — buen momento).
- [ ] 7.2 GAP #A (retiro píxeles Test1 K1 del pool μ/σ, §298-300 Coppola, flag OFF) —
  único gap literal restante; evaluar A/B propio (afloja el gate; medir FP/FN).
- [ ] 7.3 NEW-8 pool m,σ: re-evaluar contra data post-flip (5.1).

**Beyond MIROVA:**
- [ ] 7.4 Panel 2b Eq.16 (diseño 3.6) — reproc Villarrica perfil `_s99_test1_eq16`.
- [ ] 7.5 Zonas 2a afinadas por Nicolás → considerar promover a `geo_class` display
  en el dashboard experimental (NO operacional; A72: es señal real cat-b, display ok).
- [ ] 7.6 Integrar distancias OCR (F-B2) al Panel 1 como serie de posición MIROVA.

---

## Protocolo de ejecución

1. **Eje 1 primero, inline, bloqueante.** Sin Eje 1 verde no se despachan los demás.
2. Ejes 2/3(parcial)/4/6 → **4 subagentes paralelos** (A26: usarlos libremente;
   read-only, sin worktree). Eje 5 escribe docs → worktree dedicado (A44) o inline
   secuencial post-paralelo.
3. Eje 3.1-3.2 requiere a **Nicolás en el navegador** (no delegable).
4. Cierre: consolidar `docs/AUDIT_S119.md` (números de scripts, S91), actualizar
   memoria + MEMORY.md + `tasks/BLOQUE_ARRANQUE_S120.md`, Eje 7 con Nicolás.
5. Reglas siempre: A45 (nada de pipeline sin tag+OK), A61/A62 (re-anclar, adversarial),
   A48/A50 (file:line, cross-source), A10 (`pc.vrp_mw`), explicar como geólogo.

## Criterio de éxito de la auditoría

- Veredicto explícito post-flip: **mantener OFF / rollback** con evidencia numérica.
- 0 contradicciones cross-source nuevas sin registrar (patrón A51).
- Docs vivos (DIVERGENCES/MISSION/HYPOTHESIS_LOG) reflejan el estado real post-S118.
- Lista priorizada Eje 7 acordada con Nicolás para S120.
