# BLOQUE ARRANQUE S92

**Sesión previa**: S91 (2026-05-30). 7 PRs (#261–267), todos offline, 0 cambios
al pipeline. Marcada por **4 errores de integridad de números** (todos corregidos)
por un entorno que entrelazaba/corrompía salidas de comandos. Nicolás pidió
auditoría → se hizo + auditoría independiente (subagente) → 4/4 archivos PASS tras
las correcciones.

## §0 — Worktree + primer comando
```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
git fetch origin --prune && git pull --ff-only
cat tasks/BLOQUE_ARRANQUE_S92.md
```

## §0.5 — ⚠ REGLA DURA DE INTEGRIDAD (aplicar TODA la sesión)

S91 produjo 4 afirmaciones numéricas falsas porque copié cifras a mano desde
salidas de tool que el entorno entrelazaba. Ver `~memory/feedback_s91_no_transcribir_numeros.md`.
Vinculante:
1. **Ningún número entra a doc/PR/commit transcrito a mano.** Escribir un script
   reproducible (ej. `experiments/_s91_warmscene/audit_warmscene.py`) que sea la
   fuente de verdad; el doc apunta a él.
2. **Verificación programática doc==fuente antes de commitear**: un `python -c`
   que compare cada cifra del doc contra el JSON e imprima OK/MISMATCH +
   ALL_VERIFIED. Recién con ALL_VERIFIED se commitea.
3. **Un tool call por mensaje** si el entorno muestra cancelaciones en cascada /
   salidas entrelazadas (pasó toda la S91).
4. **JSON/txt con BOM (utf-8-sig) = lo escribió un subagente** → números NO
   verificados de 1ª mano (A48). Re-verificar o descartar.

## §1 — Estado al cierre de S91 (qué quedó hecho y qué NO)

**A/B detección diurna MODIS — CORRIDO pero NO VALIDÓ EL PATH.**
Los dos runs GH Actions terminaron `success` (NdC 26687718294, Villarrica
26687842353) y los 4 JSON están en `data/_daytime_modis_{enabled,disabled}/`.
Corrí `analyze_ab.py` sobre ambos:
- **Villarrica**: Δ recall=0, 0 detecciones nuevas. Trivial: la mayoría de las
  escenas son VIIRS (el path es solo-MODIS).
- **NdC**: Δ recall=0, 0 detecciones nuevas — PERO el diagnóstico mostró que NdC
  tiene 135 records MODIS y **0 clasificados como diurnos** (134 noc + 1 sin
  coord). **El A/B no probó el path porque no hubo escenas diurnas sobre las que
  actuar.** Esto es lo que hay que resolver primero en S92 (pendiente #1).

`enable_daytime_modis` **sigue OFF**. El path NO está validado ni a favor ni en
contra. NO adoptar hasta resolver #1.

**Warm-scene PCC — CERRADO** (no reabrir salvo dato nuevo). Anomalía real
categoría b (lacolito difuso) sobre-estimada por suma de campo difuso MODIS 1km
vs foco VIIRS de MIROVA (cruce OCR verificado 0.13–0.63 MW). NO accionar (A55).
Detalle: `experiments/_s91_warmscene/FINDINGS.md`.

Refs memoria: `reference_s91_warmscene_pcc_closed`,
`reference_s91_daytime_ab_pending`, `feedback_s91_no_transcribir_numeros`.

## §2 — PENDIENTES S92 (en orden de valor)

### 2.1 — BUG BLOQUEANTE: el A/B no tiene escenas MODIS diurnas
**Por qué importa**: sin escenas diurnas, el A/B no puede validar la detección
diurna — todo el trabajo S90/S91 queda sin veredicto. Es el cuello de botella.

**Síntoma (verificado 1ª mano)**: NdC mar-abr tiene 135 records MODIS, 0 con
`_solar_elevation>0`. Pero el evento que motivó todo esto —**NdC 2026-03-17
~13:15 UTC = mediodía solar**— es diurno y debería estar.

**Investigar (systematic-debugging, offline salvo logs)**:
1. ¿La escena MODIS diurna del 2026-03-17 se descargó/procesó en el run? Revisar
   logs del run 26687718294 (`gh run view 26687718294 --log`) o `fetch.py` para
   esa fecha. Quizá MODIS Aqua/Terra no tiene pasada útil ese día, o LANCE no la
   sirvió.
2. ¿`_scene_is_day(filename, lat, lon)` en `process_modis.py:272` clasifica bien?
   Test directo: tomar el granule del 03-17 y ver si da `True`. Ojo: `_scene_is_day`
   parsea la fecha del NOMBRE del granule; si el parse falla → devuelve `False`
   (noche conservadora) y el path diurno nunca se activa.
3. Mi cálculo en `analyze_ab.py:rec_solar_elev` usa `datetime_utc` + coords del
   record YA guardado — si el record diurno fue rechazado por el gate store, ni
   siquiera está en el JSON para contarlo. Distinguir "no se procesó" de "se
   procesó y se clasificó noc" de "se procesó diurno pero el gate lo rechazó".

**No tocar pipeline para 'arreglar' sin antes entender** cuál de los 3 es. Si hay
que tocar `process_modis.py`/`store.py` → tag + OK explícito Nicolás (A45).

### 2.2 — BUG SOSPECHADO: el flag diurno altera records VIIRS
**Síntoma (hipótesis fuerte, NO confirmado — entorno S91 degradado)**: el diff
enabled vs disabled de Villarrica mostró ~108 records con `mirova_eq_vrp` distinto,
casi todos **VIIRS** (NOAA20/SNPP/NOAA21, t_max 277–299K). Por diseño
`enable_daytime_modis` NO debería tocar VIIRS (nocturno, design doc §11). En NdC
los JSON enabled/disabled también difieren en md5 (cambió algo) aunque el A/B no
lo mostró (mide summit).

**Investigar (systematic-debugging, offline)**:
- Re-correr en LIMPIO un diff estructurado enabled vs disabled (Villarrica y NdC),
  salida a archivo, leer con Read. Confirmar el conteo y los sensores de 1ª mano.
- **Distinguir la causa**: ¿cambia `vrp_mw` (scene-wide)? → fuga de scope de
  thresholds a VIIRS = BUG real. ¿O solo cambia `mirova_eq_vrp`/cluster con
  `vrp_mw` igual? → cluster selection no determinista del reproc = ruido (A18),
  NO bug del flag.
- Revisar `process_viirs.py` / `process_viirs_mod.py`: cómo leen
  `nti_k1_day`/`n_sigma_mir_day`/`dnti_contextual_c1_day` y si
  `_select_thresholds`/`_reject_daytime` (en store.py) fugan día→VIIRS.
- Si es bug real de scope, el A/B diurno NO es limpio (el flag contamina VIIRS) →
  hay que aislarlo antes de cualquier adopción. Tag + OK antes de tocar pipeline.

### 2.3 — Cerrar A/B diurno (depende de 2.1)
Solo si 2.1 revela que SÍ hay/habrá escenas diurnas procesables:
- `python experiments/_s90_daytime_modis/analyze_ab.py --volcano NevadosDeChillan --start 2026-03-01 --end 2026-04-30`
- **R2 pixel-level** evento diurno NdC vs TIF MODIS (47 TIFs, PR #254):
  `scripts/compare_tif_mirova_vs_ours.py`.
- Criterios §7: `docs/superpowers/specs/2026-05-30-daytime-modis-detection-design.md`.
- **Si valida** → `enable_daytime_modis: true` en `mirova_equivalent.yaml` con
  **TAG + OK explícito Nicolás (A45)** + reproc operacional + verificar dashboard.
- Si FP solares dominan → NO adoptar, documentar.

### 2.4 — Tabla v2 frontend (no empezada)
Rotular/atenuar artefactos cirrus en la tabla del dashboard. **Requiere preview
en navegador NO-UTC** (no solo `node --check`; lección S89 bug TZ). Offline.

### 2.5 — (opcional) Cargar OCR en `data/mirova/<vol>.json`
Hoy solo CONS → mejora precisión REPORTADA, no recall (A54). Tooling.

### 2.6 — (cosmético, bajo) Corregir "0.51 MW" mal-fechado
En `FINDINGS.md` §4 el "0.51 MW @ 2026-04-04" es de 2026-01-22; el OCR de 04-04
tiene 0.55/0.63. No afecta la conclusión. La auditoría independiente S91 lo marcó.

## §3 — Escudo anti-drift (vigente, NO violar)
1. NO vent_anchored nuevo (validado S87/S88).
2. NO gate `t_bg<260K` (refutado S86). Criterio cirrus usa `t_max`, NO `t_bg`.
3. NO huella/exclude_zones/gate-intra-radio nuevo (A55).
4. geo_class/mirova_confirmed/supresión cirrus = ETIQUETAS/display, NO filtran.
5. Detección diurna MODIS **flag OFF** hasta validar A/B (NO setear sin tag+OK).

## §4 — Reglas vinculantes
A45 (tag+OK antes de pipeline), A47, A48, A52, A54, A55, A18, M1, M2, M8 +
**integridad S91 (§0.5)**. Frontend: verificar en preview navegador no-UTC.

## §5 — Herramientas listas (no reescribir, usar)
- `experiments/_s90_daytime_modis/analyze_ab.py` — A/B por (vol,noche), aísla
  nuevas diurnas (enabled∖disabled), R3 TP-MIROVA vs FP-solar, elevación solar por
  record. Tiene guard que aborta si un perfil está vacío.
- `experiments/_s91_warmscene/audit_warmscene.py` — fuente de verdad de las tablas
  warm-scene PCC (reproducible).

## §6 — Comunicación con Nicolás
Geólogo: fenómeno físico → mecanismo pipeline → fórmula al final. El "por qué"
antes del "cómo". **Todo queda registrado para el paper futuro** (provenance de
parámetros, hipótesis, A/B, criterios).
