# BLOQUE ARRANQUE S97

**Sesión previa S96 (2026-06-01 UTC).** 3 PRs mergeados (#300, #301, #302). main al día.
Entorno de tools inestable (screenshots timeout, pytest rompe teardown de captura → usar
`-s`). Detalle: [[reference_s96_nrt_current_day]], [[reference_s96_f5_display]].

## §0 — Primer comando
```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
git fetch origin --prune && git pull --ff-only
cat tasks/BLOQUE_ARRANQUE_S97.md
cat docs/F5_DISPLAY_S96.md          # estado F5' display + validación vs MIROVA
```

## §0.5 — Integridad (REFORZADA S95/S96)
Entorno entrelaza/vacía stdout. Número/conclusión NUNCA antes del dato; salida a archivo
único + leer con `cat`/`Read`; un tool call por mensaje. Para pytest usar `-s`
(`--capture=no`) — el teardown de captura se rompe en este entorno. A45 para pipeline.

## Estado al cierre S96
- **P0 NRT día en curso (PR #300)**: el cron procesa hoy+ventana 7d. Verificación pendiente
  pasiva: tras el cron diurno UTC (~08:00–10:00), el último record de cada Tier A debe ser
  la pasada del día en curso. Solo mirar, no hay acción.
- **P1 F5' display (PR #301 + guard #302)**: toggle Cluster⟷Núcleo en las 3 vistas, default
  Cluster, **deployado y seguro**. Guard: el Núcleo nunca borra una detección (0 regresiones).
  Aproxima mejor a MIROVA (1.59× vs 2.00×, gana 8/11 vols). DETECCIÓN INTACTA.
- **P2 rotar token Earthdata**: Nicolás dijo que NO le interesa → descartado.

## §1 — PRIORIDAD S97: reparar la RAÍZ A46/A07 (pipeline, A45) — solo si Nicolás quiere F5' pleno

**Por qué**: F5' display cae al fallback (cluster, sin cura) en ~30% de records VIIRS375
porque `anomaly_pixels` no carga la energía del cluster. El guard lo hace seguro pero NO
cura la raíz. Reparar esto desbloquea F5' pleno en Villarrica/PP (los sub-píxel) y es
prerequisito para bajar F5' al pipeline.

**Diagnóstico S96 (punto de partida — NO re-investigar desde cero)**:
- Los records afectados **disparan Test1** (`triggered_test1=True`, `final_hotspot_source=test1`).
  Son los sub-píxel débiles (Villarrica lava lake, PP cráteres tibios).
- Mecanismo aparente: Test1 ([process_viirs.py:1486](pipeline/process_viirs.py)) pobla
  `anomaly_pixels = build_anomaly_pixels(t1_vrp_2d)` = píxeles scene-wide con `t1_vrp_2d>0`
  (en campo frío, poquísimos, y los más fuertes son fuentes lejanas/incendios). El **cluster**
  (`t1_clusters[0]`, 19 px, 0.819 MW) sale de `cluster_hotspots(test1_hot_filtered, vrp_per_pixel=t1_vrp_2d)`.
- **ANOMALÍA SIN RESOLVER (clave para el debug)**: en el caso PP 2026-05-30 06:24 SNPP,
  `pc.vrp_mw=0.819` (19 px) pero `anomaly_pixels`=3 (máximo cerca del cráter 0.22 MW). **Esos
  números NO cuadran** — si el cluster sumara 0.819 desde `t1_vrp_2d`, esos píxeles deberían
  estar en `anomaly_pixels`. Sugiere que `primary_cluster` y `anomaly_pixels` salen de paths
  o grids DISTINTOS, no solo de un filtro de umbral. **Primer paso del debug: reconciliar de
  dónde sale exactamente `pc.vrp_mw=0.819` vs los 3 píxeles persistidos.**

**Plan (systematic-debugging + A45)**:
1. `superpowers-systematic-debugging`: trazar, para un record Test1 (PP 2026-05-30 06:24 SNPP
   o Villarrica 2026-02-26 05:24), QUÉ path setea `primary_cluster` y QUÉ path setea
   `anomaly_pixels`, y por qué `pc.vrp_mw` no se reconstruye desde los píxeles persistidos.
   Reproducir el record localmente (un solo granule) para inspeccionar `t1_vrp_2d`,
   `test1_hot_filtered`, `t1_clusters[0]["pixels"]`.
2. `writing-plans` + `test-driven-development`: el fix probable = persistir en `anomaly_pixels`
   **exactamente los píxeles del cluster seleccionado** (`t1_clusters[0]`) con su VRP, no el
   top-100 scene-wide. Test sintético que capture la inconsistencia ANTES del fix.
3. A45 completo: tag `pre-s97-test1-anomaly-pixels-cluster` + reproc validación + OK Nicolás.
   Espejo en `process_modis.py` y `process_viirs_mod.py` si aplica (A46 es transversal).
4. Tras el fix: re-correr `experiments/_s96_audit/f5_display_vs_mirova.py` → el % de fallback
   debe bajar y los ratios Núcleo/MIROVA mejorar en Villarrica/PP.

## §2 — R2 pixel-level vs TIF MIROVA (antes o después de §1, read-only)
Verificación mandada por CLAUDE.md/S33 antes de adopción metodológica: comparar la magnitud
Núcleo contra el TIF público de MIROVA (no solo el número agregado del CSV). TIF en
`mirova-tif-archive/data/tif/<Volcan>/` (ver S35). Caveat A24: el TIF NO es VRP per-pixel
sumable — usar el método R2 S69 (centroide ponderado top-N <3km del vent). Da confianza
antes de invertir en el fix de raíz, o lo confirma después.

## §3 — Bajar F5' al pipeline (futuro, tras §1 + §2)
Solo si Nicolás aprueba visualmente el display + §1 + §2 OK. `process_viirs.py`: segundo
umbral de magnitud (suma núcleo D2-safe v2), DETECCIÓN INTACTA. A45 completo. Re-validar el
ancla centroide-restringido (el script S95 `f5_d2safe.py` usa ancla global).

## Scripts/docs S96 de referencia
- `experiments/_s96_audit/f5_display_vs_mirova.py` — Cluster vs Núcleo vs MIROVA (reproducible).
- `docs/F5_DISPLAY_S96.md` — implementación + validación + guard + pendientes.
- Frontend: `mirovaEqVrpCore` / `f5CoreMagnitude` en index/diario/mosaico (el algoritmo display).
