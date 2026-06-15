# S109 §1 — Hallazgos magnitud MODIS (en progreso)

## H1 (verificado): la magnitud Test1 de MODIS NO tiene ctxpeak; VIIRS sí.
`apply_contextual_test1_filter` (ctxpeak, S100/D10) se aplica SOLO en process_viirs.py:1508.
process_modis.py no lo importa ni lo llama. Flag `enable_test1_contextual_keep_peak:true` (yaml:251)
gatea solo el path VIIRS. → Asimetría real (patrón A46/A48 VIIRS-tiene-X-MODIS-no).

## H2 (REFUTA el fix obvio): los inflados MODIS son src=eruption (105/121), no test1 (10/121).
breakdown_inflated_source.py:
| Vol | nMODIS | nInfl | src eruption | src test1 | medNpix | medΔT |
|---|---|---|---|---|---|---|
| Chaiten | 334 | 38 | 34 | 4 | 11.5 | 10.05K |
| Villarrica | 295 | 28 | 22 | 1 (+2 vent +3 rescue) | 8.0 | 10.4K |
| Llaima | 296 | 9 | 7 | 1 | 11 | 10.47K |
| Tupungatito | 290 | 18 | 15 | 3 | 11.5 | 14.37K |
| PCC | 317 | 27 | 26 | 1 | 13 | 12.15K |
| Lascar (CONTROL) | 256 | 1 | 1 | 0 | 9 | 14.9K |
GRAND: eruption=105, test1=10, vent=2, cluster_rescue=4.

→ Portar ctxpeak a MODIS curaría SOLO ~10/121. La inflación está en la magnitud del
cluster del path ERUPTION (process_modis.py:827-946), donde vrp_mw=nansum(per_pixel) sobre
el hot_mask union, y pc.vrp_mw = suma del cluster contiguo (~11 px a ΔT~10K → ~7 MW).
dNTI contextual disparó en casi todos → los píxeles del cluster incluyen dnti_ctx_hot.

## Pendiente (workflow wf_6d6caf1c-dba): papers (qué píxeles cuenta MIROVA), per-pixel VRP
dentro del cluster (foco vs difuso), cross-sensor VIIRS.

## H3 (papers, verbatim — DECISIVO): MIROVA es "fundamentally insensitive to diffuse heat".
Coppola 2023:464-466 VERBATIM: "VRP ... is fundamentally insensitive to the diffuse heat
dispersed from the crater area at a few degrees above the background (zones of diffuse
degassing)". VRP = A_pix × k × Σ_Npix(L_hot,i − L_bk), Npix = solo píxeles ALERTADOS
(superan umbral NTI/dNTI/ETI). MIROVA NO suma el campo difuso. Un algoritmo por sensor,
uniforme entre volcanes (Coppola 2024 cap.11:1135-1145). MISSION: (a) PASS, (d) PASS,
(b) FAIL (combina sensores, no es mecanismo MIROVA), (c) FAIL (no hay cap duro, ±30%).

## H4 (datos, DECISIVO): la magnitud inflada ES el campo difuso sumado.
max_pixel/sum del cluster = 0.157-0.204 (el píxel más caliente aporta solo 16-20% de
pc.vrp_mw; el 80-84% son ~8-13 píxeles de ~0.4-1.5 MW). BT pico ~283-287K, ΔT (t_max-t_bg)
~10-14K: NINGÚN píxel sobresale como foco; toda la "anomalía" es el campo ~10K sobre fondo
frío = firma del gradiente topográfico nocturno A69, NO lava. Control Lascar (n=1): max/sum
0.253 (55% agregado), ΔT 14.9K → más foco-like (único MODIS-foco real). Cuantificación:
experiments/_s109_diffuse_probe/.

## H5 (paths, REFINA el root-cause): el difuso entra por dNTI ctx + SECOND-PASS recapture.
diag_n_*_path medianas en inflados-eruption: bt=0, nti_abs=0, eti=0; dnti_ctx=1-70,
**2ndpass_recapture=14-185**, nAnom=43-268, cluster pcNpix=8-13. → NO es NTI absoluto ni BT.
Es la semilla dNTI contextual + la recaptura del second-pass (Coppola 2016a) que arrastra
el campo tibio topográfico. La recaptura/umbral NO logra la "insensibilidad al difuso" que
los papers atribuyen a MIROVA. Es la cara-magnitud de D11/A69 (la cara-posición se trabajó
S104-S106).

## H6 (cross-sensor): MIROVA publica 0-1 MODIS ALERTA en estos 5 vols (vs 82 Lascar).
VIIRS375 cubre ~100% de las noches; ratio MODIS-inflado/VIIRS-nuestro = 5-54×. PERO candidato
(b) cap cross-sensor = divergencia MISSION (MIROVA reporta cada sensor por separado, nunca
combina). VIIRS sirve como DIAGNÓSTICO/validación, no como operador sobre el VRP MODIS. El
camino fiel per-sensor: que la magnitud MODIS al cráter sea ~0 donde no hay foco MODIS
resoluble (todos menos Lascar) = exactamente lo que MIROVA hace (MODIS silenciado, VIIRS reporta).

## SÍNTESIS para brainstorming
Causa raíz = magnitud MODIS suma el campo difuso topográfico (~10K sobre fondo frío) que
MIROVA, por diseño de umbral, ignora ("fundamentally insensitive"). El fondo-local (S106/S107,
refutado) atacaba el FONDO (L_bk); los papers apuntan a atacar la SELECCIÓN DE PÍXELES (solo
sumar los genuinamente focales/contextuales). Eso lleva estos vols a ~0 MODIS (= MIROVA vía
VIIRS) y preserva Lascar (control). Riesgo a vigilar (lección S106): a escala local la señal
real débil es tan suave como la topografía → un filtro contextual de magnitud podría matar
foco real → C3 Lascar es el control duro; A/B obligatorio.
