# Probe A75 por etapa del ensamblado — diseño para GitHub Actions (S135)

**Sólo diseño.** No se crea ningún yml en `.github/workflows/` en S134. Prohibido correrlo local
(sin granules, disco al 100 %, credenciales dudosas — A71).

## Por qué hace falta
F3 (`F3_HALLAZGOS.md`) fijó el mecanismo con los píxeles persistidos: el Test 1 marca ~67 píxeles,
el filtro `keep_peak` (`process_viirs.py:1775-1786`) deja sólo `argmax(BT)`, y ese píxel del borde
del disco de 3 km es el cúmulo publicado. Lo que **no** queda escrito en ningún JSON es el footprint
del Test 1 ANTES del filtro. Sin él no se puede cuantificar cuántos píxeles del cráter había y con qué
exceso, ni qué habría quedado con `(Test1 ∩ dNTI_ctx)` sin el pico. El probe captura eso, read-only.

## Qué parchear (monkeypatch en el namespace de `pipeline.process_viirs`, NO en los módulos origen)
`process_viirs.py` importa por nombre (`from .test1_integrated import compute_test1_mir …` l. 208;
`from .detection_context import first_pass_tests_2_and_3, second_pass_adjacent` l. 198-206;
`from .clustering import cluster_hotspots` l. 53; `from .test1_contextual_filter import
apply_contextual_test1_filter`). Parchear `pipeline.detection_context.first_pass_tests_2_and_3`
**no cambia nada** en el procesador (trampa A89); hay que hacer
`pipeline.process_viirs.first_pass_tests_2_and_3 = wrapper`. El probe S110
(`experiments/_s110_ndc_probe/probe_ndc_assembly.py:47-66`, repo principal) ya usa este patrón sobre
`process_modis` (`pm.first_pass_tests_2_and_3 = _wrap_fp`).

| función a envolver | qué capturar (por granule) |
|---|---|
| `compute_test1_mir` | `mask_contributing` (bool 2D), `L_bg`, `sigma_bg`, `n_contributing`, `centroid_lat/lon`, `triggered`; además el `bt` del argumento para el perfil BT-vs-distancia |
| `apply_contextual_test1_filter` | máscara de entrada, `dnti_ctx_mask`, `keep_peak_rc`, máscara de salida |
| `first_pass_tests_2_and_3` | `hot` de salida, `diag` (μ/σ, `n_bg_used`) |
| `second_pass_adjacent` | `active_mask` de entrada y máscara de salida → `newly_active`; guardar también `bt[newly_active] - t_bg` para confirmar la compuerta faltante (H2) |
| `cluster_hotspots` | **las dos llamadas** (`:1454` contextual, `:1897` Test 1): máscara de entrada, `vrp_per_pixel`, ancla, lista devuelta (para ver todos los cúmulos candidatos, no sólo `[0]`) |

Derivar por granule, con `vent_lat/lon` de `volcanoes.yaml`:
1. Píxeles de `mask_contributing` a <0,5 km del cráter: n, exceso, BT. ¿Está el cráter en el Test 1?
2. Píxel `keep_peak`: distancia, BT, ¿es el más caliente del disco o sólo de la máscara?
3. `(Test1 ∩ dNTI_ctx)` sin pico: n y posición.
4. Perfil `BT mediana vs distancia al cráter` en anillos de 0,25 km hasta 3 km, por octante (A70):
   distingue «borde = cota baja en todas direcciones» de «valle de un lado».
5. Para H2: lista de `newly_active` con `n_first_pass==0` y su `bt - t_bg`.
6. Guardar todo en `experiments/_s135_probe_etapas/out/<vol>_<pasada>.json` + un `report.txt`.

## Pasadas (las 6 de `tabla_6_pasadas.json`)
| volcán | pasada UTC | sensor | esperado |
|---|---|---|---|
| Villarrica | 2026-07-01 05:00 | VIIRS_NOAA20 | pico 263,9 K < t_bg 270,1 a 2,68 km |
| Villarrica | 2026-08-14 04:42 | VIIRS_NOAA20 | pico a 2,86 km |
| Villarrica | 2026-08-31 05:06 | VIIRS_NOAA21 | 2 px (uno dNTI) a 2,58/2,97 km |
| Láscar | 2026-06-17 05:42 | VIIRS_SNPP | control: cráter 288,9 K, cúmulo a 0,09 km |
| Láscar | 2026-07-09 05:48 | VIIRS_NOAA20 | control |
| Láscar | 2026-07-10 05:30 | VIIRS_NOAA20 | control |

Fetch por fecha/volcán con `pipeline.fetch` como hace `scripts/run_pipeline.py` (día completo, filtrar
el granule por `_parse_datetime`). Standard L1B primero, LANCE sólo si no existe (A64: el
circuit-breaker por host ya está en `fetch.py`).

## Workflow a clonar
`.github/workflows/_archive/probe-s110-ndc-assembly.yml` → copiar a
`.github/workflows/probe-s135-etapas.yml` **sólo en S135**, con:
- `"on":` entre comillas (A43), `workflow_dispatch` con input `vol` y `fecha` opcionales.
- `timeout-minutes: 60`, `VRP_PROFILE: mirova_equivalent`, secrets `EARTHDATA_*` (los que usa `nrt.yml`).
- `pip install earthaccess numpy h5py scipy pyyaml` (sin `pyhdf`: sólo VIIRS).
- `upload-artifact` de la carpeta `out/`, `if: always()`. **No** `git push`: read-only, sin tocar
  `data/` ni la concurrencia `push-main`.
- Volver a archivar el yml al terminar (regla S80 de plantillas).

## Criterio pre-registrado (A91: en las unidades del objeto)
- H1 confirmada a nivel granule si, en las 3 pasadas de Villarrica, `mask_contributing` contiene ≥1
  píxel a <0,5 km del cráter **y** el `keep_peak_rc` está a >2 km, **y** en las 3 de Láscar el
  `keep_peak_rc` (si aplica) está a <0,5 km.
- H1 refutada si en Villarrica el cráter no está en `mask_contributing` (entonces el Test 1 ni siquiera
  ve el cráter y el problema está antes, en el ROI/fondo del Test 1).
- H2 confirmada si ≥90 % de los `newly_active` con `n_first_pass==0` tienen `bt - t_bg ≤ 3 K`.

---

**Corrido en S135** (run 34071793829, 6/6 pasadas OK): resultados y criterio aplicado en
`experiments/_s135_probe_etapas/RESULTADOS.md`. El yml quedó en `_archive/probe-s135-etapas.yml`.
