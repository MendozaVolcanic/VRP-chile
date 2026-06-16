# AUDIT S111 — FN de magnitud en régimen "Muy Bajo" (Test1 integrado VIIRS375)

**Disparador (2026-06-16, Nicolás)**: Nevados de Chillán mostró su **primera anomalía
térmica en un sitio eruptivo NUEVO del cráter** — MIROVA `VRP=0.06 MW, VIIRS375, ALERTA
"Muy Bajo"` (pasada 05:30 UTC). Es el evento de reactivación temprana que el sistema
existe para capturar. **No lo detectamos en magnitud** (reportamos 0.000).

## El caso (record nuestro, NdC 2026-06-16 05:30, VIIRS_NOAA21 I-band)
- `triggered_test1=True`, `n_test1_pixels=74`, `class=summit`, `dist=0.441 km` →
  **detección espacial CORRECTA** (el Test1 integrado vio la anomalía al cráter).
- `vrp_mw=0`, `primary_cluster={n_pixels:1, vrp_mw:0.0, single_pixel_mode:True}`,
  `final_hotspot_source=ctx_cluster`. ΔT = 287.06−275.79 = **11.3 K** (señal real débil).

## Mecanismo (dos sub-problemas distintos)
MIROVA cuantifica integrando el exceso de radiancia MIR sobre la región (Test1, Coppola
2015 Eq.1): 74 píxeles × exceso ínfimo = 0.06 MW. Nuestro pipeline **detecta con el
Test1 pero NO usa su magnitud**:

**(A) Cascada de `source` (process_viirs.py:1420-1439)** — el recompute completo de la
magnitud del Test1 (1545-1625) está gateado por `final_hotspot_source == "test1"`. La
cascada solo pone `source=test1` si `test1_summit_hit AND eruption_far`, o si
`only_test1_source` (ningún otro path contribuyó). Cuando existe un cluster cercano
DÉBIL (1 píxel, vrp≈0) que vino de otro path (dnti_ctx/nti), `eruption_far=False` y
`only_test1_source=False` → `source=eruption` → **el recompute del Test1 no corre** → la
magnitud queda la del cluster puntual (≈0). Es el patrón A46/A73 (una representación del
hotspot tapa a la otra).

**(B) Fondo local contaminado (1553, 1577)** — aun cuando `source=test1`, el recompute
usa `effective_L_bg = test1_L_bg_local` (anillo 1-3 km del cráter). En un cráter con
calor crónico ese anillo está **contaminado por la propia anomalía** → `delta_L =
max(L−L_bg,0)` se recorta a 0 → vrp=0. El flag `ENABLE_TEST1_LBG_GLOBAL` (D4, S33)
existe para esto pero requiere `lbg_global_compatible` per-volcán; NdC no lo tiene.

## Dimensión (cruce ALERTAS MIROVA VIIRS375 NdC vs nuestros records, CONS fresco)
6 ALERTAS MIROVA VIIRS375 NdC (VRP 0.02–0.49, mediana 0.06) en ~3 meses:
- **TP (capturamos magnitud): 0/6** — recall de magnitud 0% en alertas débiles VIIRS375.
- 3 = sub-problema (A) cascada (`source=ctx_cluster`, vrp=0, t1=True).
- 1 = sub-problema (B) recompute corrió pero dio 0 (`source=test1_roi`, 17-abr 0.02).
- 1 = sin pasada nuestra esa noche.
- 1 = FN de DETECCIÓN (22-mar 0.49 MW, `t1=False`) — frente distinto.

Sistémico: 2041 records en 11 Tier A con `t1 trig & vrp~0 & src!=test1` (candidatos;
solo los que cruzan ALERTA MIROVA son FN reales — patrón esperado en Villarrica lava
lake, Lastarria fumarolas).

## Direcciones de solución (a brainstormear, A45 — NO implementado)
- **(A)** cascada: cuando `test1_summit_hit` y el eruption/cluster es trivialmente débil
  (vrp≈0 / single_pixel_mode sin energía), `source=test1` → corre el recompute (con sus
  filtros pixel-level/contextual/spatial-core ya validados). Recupera los 3.
- **(B)** fondo local: revisar `effective_L_bg` para que el cráter con calor crónico no
  recorte a 0 (lbg_global per-vol, o fondo local de un anillo más externo). Recupera 1.
- **(C)** FN detección 22-mar: por qué Test1 no disparó (cobertura/nube/umbral). Aparte.

Trade-off (A54): recuperar la magnitud real (~0.06) SIN convertir RUTINA en ALERTA falsa
(recall sub-píxel sin romper precisión). Validación: A/B reproc vs las 6 ALERTAS MIROVA.
