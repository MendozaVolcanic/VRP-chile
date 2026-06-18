# AUDIT S112 — Dashboard + datos vs MIROVA (paridad, PCC, integridad, datos extraños)

**Pedido por Nicolás (2026-06-17). Workflow 5 agentes (wf_e78ded8e). Probes reproducibles en
`experiments/_s112_audit/`** (parity_by_vol_sensor.py + parity_result.json, pcc_deepdive.py/
pcc_final.py, probe_weird_records.py + weird_records_result.json).

## Paridad actual vs MIROVA (post-adopción VIIRS375 S112) — SANA
- **VIIRS375 (sensor dominante MIROVA, 206 ALERTAS mayo-jun): EN PARIDAD** — recall 75-100%,
  ratio mediano 0.52-1.2× (leve sub-estimación, calibración sana). Adopción NdC validada
  (recall 75%, ratio 1.2×, las 3 ALERTAS aparecen). Ningún flag.
- **VIIRS750: INFLADO 8-20×** — Tupungatito 19.9× (n=2), PlanchonPeteroa 12.5× (n=3), Isluga
  8.26× (n=11). Foco sub-píxel real (MIROVA 0.15-0.43 MW) pero sumamos escena glaciar → 2-4 MW.
  = artefacto A69; **lo cura el A/B focal V750 en vuelo (run 27762249160)**.
- **MODIS casi ciego** (18 ALERTAS total, física sub-píxel; solo Lascar regular recall 93.8%/
  2.2×). Sobre-detección RUTINA 91-98% = campo difuso A69 (frente abierto, A72 raíz no display).
- Lascar = mejor cobertura multi-sensor (V375 100%/0.55×, V750 93.9%/0.64×, MODIS 93.8%/2.2×).

## Caso PCC (pista de Nicolás) — RESUELTO: artefacto cirrus path-D, no el lacolito
- Señal MIROVA real PCC: SOLO VIIRS, 7.28-8.55 km del centro (lacolito Cordón Caulle ~7.7km NO),
  0.02-1.22 MW, 0 MODIS publicado. La conservamos (recall 100%, ratio ~1×).
- Las "raras lejanas": **56 detecciones >10 km, dispersas omnidireccional** (mediana 16.6 km
  DESDE el lacolito), **86% path-D ctx_cluster, 77% t_bg<270K** = firma cirrus path-D dNTI
  (A23/D9). **35/56 en noches sin ALERTA MIROVA → no salen en los CSV.** Peor sensor V750 (41).
- `inner_radius=20km` (KML por lacolito 707km²) = amplificador VISUAL (pinta summit-rojo las 56).

## Lista priorizada (separa artefacto-a-limpiar de cat-b-real-a-preservar, A54)
| # | Sev | Qué | Fix |
|---|---|---|---|
| 1 | EN CURSO | VIIRS750 inflado 8-20× (Tupun/PP/Isluga) | A/B focal V750 (run 27762249160) |
| 2 | ALTA | **D9/A23 cirrus path-D** (56 lejanas PCC + ~210 records cirrus en los 11) | Co-validación / gate atm t_bg<270K al path-D — raíz A72 |
| 3 | ✅ RESUELTO S113 | **Incoherencia A46**: el flagship se auto-curó (ancla honesta); bug genuino = 2 records Villarrica (artefacto). PCC 54 = efecto inner=20 (issue #5, no A46). | Guard unidireccional store.py summit→far. Ver `docs/S113_A46_COHERENCE_GUARD.md` |
| 4 | MEDIA | Campo difuso MODIS A69 (91-98% sobre-detección) | Frente MODIS abierto (focal MODIS + co-val) |
| 5 | MEDIA | inner_radius=20 PCC infla visual | Evaluar bajar a ~10km (lacolito real ≤8.5km) |
| 6 | BAJA | 20 MODIS PCC clavados en 5.0 MW (¿cap?); diario:432 datetime sin Z (S89) | Revisar / parseUtcMs |

## Integridad dashboard — SANA
3 vistas leen pc.vrp bien (no vrp_mir, S12), parseUtcMs OK (salvo diario:432 ref MIROVA, BAJA),
sensores A48 OK, cirrus suppression presente, CSV fresco, 19123 records 0 NaN/None. Único bug
real = #3 (A46 coherencia summit/far).

## Orden recomendado (aprobado Nicolás "el que recomiendes")
1. Cerrar A/B focal V750 (#1). 2. #3 coherencia A46 (bug contenido, confunde operador).
3. #2 cirrus D9/A23 (mayor impacto, pista PCC + 210 records). Luego #4 MODIS difuso / #5 display / #6.
