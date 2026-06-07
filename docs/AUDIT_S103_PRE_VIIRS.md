# AUDIT S103 — Auditoría profunda pre-adopción nadir-fijo VIIRS

**Fecha**: 2026-06-07 · **Método**: 7 subagentes paralelos read-only (A26/A51), un eje cada uno.
**Objetivo** (pedido Nicolás): antes de adoptar nadir-fijo VIIRS (A45), detectar fallas
latentes, gaps de testing y riesgos en todo el proyecto (tests, dashboard, CI/GitHub,
git, datos/CSVs, código pipeline, TIF/R2).

## Veredicto global

**El proyecto está sano para proceder con la adopción VIIRS.** Cero corrupción de datos,
cero credenciales expuestas, suite verde (667 passed / 0 fallas reales), NRT resuelto,
dashboard coherente, mecanismo nadir VIIRS correcto end-to-end. Hay **2 cosas a hacer
antes/durante el flip** y **1 limitación a aceptar conscientemente**:

1. **(antes — TDD)** Falta UN test: integración por sensor que confirme que el flag
   `enable_nadir_fixed_pixel_area_viirs` cambia el área en el **cómputo de VRP** de
   `process_viirs.py` y `process_viirs_mod.py` (hoy solo se prueba `viirs_pixel_areas()`
   aislado a nivel `scan_geometry`). Es el gap A45 análogo al de MODIS.
2. **(durante — obligatorio o rompe CI)** Actualizar el tripwire GR2
   (`test_gr2_profile_invariants.py`): flag VIIRS `False→True` (L109) + agregarlo a
   `const_to_yaml` (L138). El test está diseñado para fallar ante un flip — hay que
   moverlo deliberadamente.
3. **(limitación R2)** El archivo de TIFs MIROVA está **congelado en 2026-05-08/20**.
   La validación pixel-level R2 post-flip solo es posible en esos ~13 días de mayo;
   el histórico ene–abr es irrecuperable (MIROVA sobrescribe sus TIF). La validación se
   apoyará en R3 (ratios vs CSV, toda la ventana) + R2 restringido a mayo + R8 público.

---

## Eje 1 — Tests y cobertura

- **VERDE**: `pytest -q -s` → **667 passed, 24 skipped, 0 failed, 0 errors**. (`-q` sin `-s`
  rompe en teardown por bug de captura conocido S96, NO es falla de tests.)
- Los 24 skips son todos justificados: pyhdf/Windows (`test_pipeline_integration_f28`),
  recursos externos (`test_r2_pixel_level`, freshness CSV), xfail-TDD ya resueltos
  (F46/F47/F50). **Único stale real, no bloqueante**: `test_golden_records.py:40` (goldens
  pre-S27 obsoletos, no cubren nadir).
- **MEDIO/ALTO — gap de cobertura (lo que faltaba testear)**: no existe test de integración
  por proceso para nadir. `test_drift7_nadir_fixed_pixel.py` cubre `modis_pixel_areas()` y
  `viirs_pixel_areas()` aislados, pero no que `process_viirs.py:518` / `process_viirs_mod.py:326`
  propaguen el flag al VRP. **Recomendación: escribirlo antes del flip (TDD).**
- **Acción durante flip (no rompe nada si se hace)**: GR2 pinea hoy
  `ENABLE_NADIR_FIXED_PIXEL_AREA_VIIRS: False` (L109) y pisos VIIRS 0.02/0.15 (L200-205).
  Flip → actualizar L109 a `True` + L138 `const_to_yaml`. Pisos VIIRS se mantienen → ese
  test sigue verde tal cual.

## Eje 2 — Dashboard / frontend (3 vistas)

- **VERDE**: preview levantó, 3 vistas cargan, **0 errores consola / 0 requests fallidos**,
  los 11 JSON + `latest_consolidado.csv` → HTTP 200.
- **Consistencia cross-vista OK**: `mirovaEqVrp`, `f5CoreMagnitude`, `isCirrusArtifact`,
  `isDiffuseFieldArtifact`, toggle `USE_F5_CORE`, constantes (R_core=0.75) → idénticos en
  las 3. (S92 L5 respetado en estos helpers.)
- **MEDIO — `parseUtcMs` (fix S89/PR#250) solo en index.html.** `diario.html` y `mosaico.html`
  usan `new Date(r.datetime_utc)` crudo (sin "Z"). Impacto acotado: solo afecta el borde de
  ventana (90d/48h/30d), ~3-4h de corrimiento, NO recall-0 (el matching cross-source está
  protegido en index). Viola S92 L5; replicar para coherencia. **No bloquea VIIRS.**
- **OK verificación nadir MODIS**: PCC MODIS máx `pc.vrp` = **60.2 MW** (no 342). Tarjetas con
  hora local Chile + UTC. CSV con `latest_consolidado.csv` + fallback dateado.

## Eje 3 — GitHub Actions / CI

- **VERDE — NRT resuelto confirmado**: los 2 runs sobre el sha con el fix #364 → SUCCESS,
  commits NRT frescos de los 11 vols hoy (10:54-10:59 UTC). Las fallas de hoy fueron en shas
  **pre-fix** (patrón A64 confirmado en logs). `pages-deploy` últimos 10 SUCCESS → **dashboard
  avanzó** (ya no clavado en 06-04). `nrt-retry` verde.
- **MEDIO — A43 "Norway problem"**: 2 de 24 ymls NO quotean `on:` →
  **`nrt-monitor.yml` y `nrt-retry.yml`** (riesgo HTTP 422 si se disparan manual). Los 22
  restantes (incluidos los reproc-s10x) quotean bien. No bloquea el reproc VIIRS.
- **BAJO — 17 reproc-* stale** archivables (A/B de sesiones cerradas). Ninguno corre por cron.
- **Template VIIRS LISTO**: clonar `reproc-s102-nadir-promote.yml` (patrón artifacts + merge
  local con guard anti-underfetch, A47-safe) → `_s103_viirs_nadir_promote`. Timeout 300/290
  (A15 OK). **Seguro disparar el reproc histórico VIIRS.**

## Eje 4 — Git / branches / worktrees

- **VERDE — raíz limpia** en `main`, 0 ahead/behind. Working tree: solo artifacts bajo
  `experiments/_s99_audit/_*_art/` (cubiertos por `.gitignore`, verificado `git check-ignore`).
- **SIN credenciales vivas**: no `.env`/`settings.json`/`*.local.*` trackeados; solo
  `.env.example` con placeholders; refs a secrets vía `${{ secrets.* }}`. **No CRÍTICO.**
- Worktrees hermanos (~6 GB): seguros borrar (0 commits) = `funny-mendeleev`, `VRP-Chile-s70`,
  `VRP-Chile-s74-frontend-plan`; **CONSERVAR `VRP-Chile-s79-f66` (10 commits F66 Tasks 7-15)**;
  DECIDIR `s80-consolidation` (6 commits S82) y `nostalgic-aryabhata` (40, ya declarado
  descartable, tag existe), `hardcore-gauss` (1 trivial).
- **MEDIO/BAJO — `*.tif` no en `.gitignore` global** (17 trackeados, 1.2 MB; 4 en kmz/ son R2
  ground truth intencionales). `Pruebas/` ignorado pero 27 archivos ya trackeados. JSON >10MB
  de perfiles de experimentos viejos inflan el repo (candidatos a archivar). 86 branches
  remotas stale (podar las `--merged origin/main`).

## Eje 5 — Datos JSON operacionales + CSVs

- **VERDE — 11/11 JSON parsean, cero corrupción A47.** Cero NaN/Inf, cero negativos, cero
  `pc.vrp_mw`>1000, cero `final_hotspot` faltante con detección.
- **Verificación nadir MODIS S102 ✓**: PCC MODIS `pc.vrp` máx **60.18 MW** (no 342).
- **ALTO (matizado) — Tupungatito MODIS `pc.vrp` máx = 13.57 MW** (S102 dijo "~0"). NO es
  falta de promoción (fechas llegan a 06-04, promo aplicada). Es el **residual del campo
  glaciar/nieve estacional** ya documentado (A19, frente §2 path D), no del flip VIIRS. El
  "~0" de S102 se refería al pico difuso de 133 MW, que sí desapareció.
- **MEDIO — `datetime_utc` sin `Z` universal** (formato de almacenamiento intencional).
  index lo maneja vía `parseUtcMs`; subsisten ~12 call-sites crudos (ver Eje 2).
- **Baseline VIIRS pre-flip** (debe bajar ~0.78× post-nadir): V375 picos 4-5 MW
  (Llaima 5.0, Villarrica 5.12, Tupun 4.28); V750 hasta 8.75 (Villarrica), varios en 5.0
  (¿cap D9? ver Eje 6); Lastarria el más bajo (V375 0.175).
- **CSVs frescos**: `latest_consolidado.csv` mtime HOY 06:07; snapshot consolidado 12d; OCR 9d.

## Eje 6 — Código pipeline + drifts

- **VERDE — mecanismo nadir VIIRS correcto end-to-end** (trazado anti-A48):
  `profile.py:438` → `process_viirs.py:117/518` (I) + `process_viirs_mod.py:102/326` (M) →
  `scan_geometry.py viirs_pixel_areas(nadir_fixed=...)`. `True` → área constante (I 140625 m²,
  M 562500 m²); `False` → factor lineal `1+(sec z−1)·0.5` capado a 2.0. **(Matiz: la impl
  VIIRS "off-nadir" NO es sec³ puro como dice el comentario, es lineal-capado.)** VRP escala
  lineal con el área en los 3 paths (scene/Test1/M-band) → nadir reduce magnitud sin tocar
  detección. **Por eso 0 FN esperado.**
- **A49 SIN riesgo**: `compute_bg_stats` retorna intacto; diffs S98→HEAD aditivos (lógica S99
  en módulos nuevos). **A46 SIN riesgo**: gates de zero-out/cap usan distancia/conteo, no área
  → el flip no cambia ninguna decisión binaria.
- **Promoción solo-VIIRS factible (cambio trivial)**: clonar `merge_promote_nadir.py`
  invirtiendo el predicado de sensor (`not startswith("MODIS")`) + guard de cobertura VIIRS;
  MODIS queda byte-idéntico.
- **ALTO a re-verificar post-flip — cap D9 es magnitud-based** (`process_viirs.py:1132`
  `apply_d9_scene_cap`): nadir baja la magnitud → mueve el umbral efectivo del cap (records
  antes >cap pueden caer bajo él). Fue calibrado con sec³/lineal activo. No rompe nada, pero
  re-verificar que sigue acotando bien (es el frente §2 path D de todos modos).
- Coherencia profile↔yaml OK (el flip = agregar la línea VIIRS; `.get(...,False)` no rompe).

## Eje 7 — TIF archive / R2 readiness

- **DISPONIBLE**: `../mirova-tif-archive` (sibling, A62), estructura `data/tif/{Volcano}/
  {timestamp}_{sensor}.tif` + `index.csv` (2685 filas). Script reutilizable
  `experiments/_s97_audit/r2_spatial_audit.py` (match ±90min, centroide ponderado A24).
- **ALTO/CRÍTICO para R2 — archive CONGELADO en 2026-05-08/20** (13 días). NO cubre ene–abr
  ni 21-may→jun. La ventana del reproc (ene–jun) solo tiene TIF en esos 13 días de mayo.
  El histórico ene–abr es **irrecuperable** (MIROVA sobrescribe). Cobertura VIIRS densa en
  mayo para los 11 (50-77 TIF/vol) → R2 factible **restringido a mayo**.
- **Casos canónicos R2 recomendados** (todos may-08/20): Lascar V375 (control ~0.93×),
  Villarrica V375 (lava lake sub-píxel), Tupungatito V375 (caso glaciar), PCC V375 (lacolito),
  PP V750 (M13).
- **Recomendación higiene**: si se quiere R2 fuera de mayo, reactivar el polling
  (`mirova-tif-archive/polling/poll.py` + `poll.yml`) — solo sirve hacia adelante.

---

## Acciones — orden propuesto

### Pre-flip (recomendado, TDD)
- [ ] Escribir test de integración por sensor: flag ON → área uniforme en el VRP de
      `process_viirs.py` + `process_viirs_mod.py` (espejo MODIS). Cierra gap A45.

### Durante el flip (A45, espejo MODIS #354/#355/#356)
- [ ] `git tag pre-s103-nadir-fixed-viirs` + push.
- [ ] GR2: flag VIIRS `False→True` (L109) + `const_to_yaml` (L138); pisos VIIRS intactos.
- [ ] `enable_nadir_fixed_pixel_area_viirs: true` en `mirova_equivalent.yaml` (NO tocar
      ctxpeak ni pisos ni MODIS).
- [ ] Reproc histórico (clonar `reproc-s102-nadir-promote.yml` → `_s103_viirs_nadir_promote`).
- [ ] Promoción solo-VIIRS (espejo `merge_promote_nadir.py`, predicado invertido, guard
      cobertura). MODIS byte-idéntico.
- [ ] R3 (ratios vs CSV, toda la ventana) + R2 (restringido a mayo) + R8 público + preview.
- [ ] Post-flip: re-verificar cap D9 con magnitudes reducidas.

### Backlog (no bloqueante, higiene)
- [ ] Replicar `parseUtcMs` en diario.html + mosaico.html (S92 L5).
- [ ] Quotear `"on":` en `nrt-monitor.yml` + `nrt-retry.yml` (A43).
- [ ] Limpieza worktrees (~6 GB) + podar branches remotas mergeadas + `*.tif` a `.gitignore`
      (decidir destino de s79-f66 y s80-consolidation antes — §3 arranque S103).
- [ ] (Opcional) Reactivar polling TIF archive para recuperar capacidad R2 hacia adelante.
