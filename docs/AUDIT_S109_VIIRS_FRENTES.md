# AUDIT_S109 — Frentes VIIRS (#3 ratio magnitud + #2 ctxpeak V750): ambos RESUELTOS, sin acción

**Fecha**: 2026-06-14 · **Sesión**: S109 (paralelo al frente MODIS §1 en vuelo).
**Método**: workflow 2 agentes + cross-check propio (A48). Read-only, no toca pipeline.
**Veredicto de los dos**: **no accionar ahora** — con razones de datos. Evita 2 cambios que serían drift (A66).

## #3 — Ratio de magnitud VIIRS: RESUELTO. Es PARIDAD, no sub-estimación a la mitad.

Había 3 números en conflicto. Resueltos: **son el mismo dataset bajo distintas agregaciones**, no data distinta.

| Fuente | Ratio V375 | Ratio V750 | Qué es |
|---|---|---|---|
| `per_sensor_metrics.json` (S94) | 1.99× | 1.53× | **STALE pre-nadir** (commit 1705aac0, antes del flip nadir S103) → regenerado S109 |
| por-pasada ±60min (AUDIT_S108) | 0.52× | 0.54× | data fresca, **agregación por-pasada** |
| **por-noche / R3 (CANÓNICO)** | **0.77×** | **0.81×** | data fresca, **agregación por-noche** = como reporta MIROVA |

**Por qué por-noche es el canónico**: MIROVA publica **UN VRP por noche-volcán-sensor** (una detección),
no uno por pasada satelital. Nosotros tenemos **3–5 pasadas/noche** (SNPP+NOAA20+NOAA21, asc/desc). El
método por-pasada cruza CADA pasada —incluidas las oblicuas/débiles donde la señal sub-píxel se atenúa—
contra el único número de MIROVA → **sub-cuenta estructuralmente** (de ahí el 0.52×). El por-noche toma
la pasada más brillante = comparación apples-to-apples. Reproduce exactamente R3 (S103): V375 0.78×, V750 0.80×.

**Veredicto**: bajo el método canónico VIIRS está en **paridad baja (0.78–0.81×)**, dentro de la banda
0.5–2.0 y cerca del target del nadir. **NO es bug de calibración.** El residuo ~0.8× (mostramos ~¾ de MIROVA
en el pico de la noche) tiene causa probable en el **área nadir-fija** (S103/A66/A67: área menor → integral
de radiancia Test1 baja). El coef Wooster está validado (S14, ≤0.17% vs OSF) → la causa NO es el coeficiente.

**Acciones (hechas)**: (a) `per_sensor_metrics.json` **regenerado** (1.99→0.52 raw, fin del artefacto stale);
(b) método canónico documentado. **Regla durable**: reportar SIEMPRE el ratio **por-noche**, nunca el por-pasada.
**Prioridad**: por debajo del frente MODIS D12. Si alguna vez se afina VIIRS→1.0×, con A/B de área (A66), post-MODIS.
Script reproducible: `experiments/_s94_audit/ratio_method_resolution_s109.py` (+ `.json`).

## #2 — Portar ctxpeak a VIIRS750: la PREMISA CAE. No portar.

S102 §2 scopeó "VIIRS750 glaciar = portar ctxpeak" para curar la dispersión 18.9× del halo nival.
**Hoy esa dispersión YA NO EXISTE** — la curaron el **nadir-fijo (S103)** + el **ancla honesta V750 (S108)** +
el **cap D9 (5.0 MW)**:

| Vol | V750 max pc.vrp | records >5 MW | Mecanismo |
|---|---|---|---|
| Tupungatito | 5.0 (= techo cap D9) | **0** | nadir + ancla + cap ya curaron |
| PlanchonPeteroa | 8.23 | 4 (acotados) | residuo menor |

(Cross-check propio coincide con el agente, A48.) Lo que queda **no es inflación de magnitud sobre eventos
compartidos** — es **over-detección de RUTINA** (días con MIROVA=0 MW donde marcamos 1–8 MW) = **cat-b sub-umbral
real (A54)** o display (A68/A72), **otro frente**, no magnitud.

**Por qué NO portar (A62)**:
1. Resolvería un problema que ya no existe = anti-patrón "apilar dos correcciones del mismo drift" (A66).
2. **Riesgo FN real**: en records >1 MW de PP, 42/68 tienen `n_dnti_ctx_path==0`; ahí ctxpeak vaciaría el Test1
   salvo el keep-peak (1 píxel) → colapsa la magnitud y puede perder señal cat-b. El glaciar es el régimen donde
   estos filtros se comportan al revés (A19/A66).
3. **Bug latente del porte directo**: en el M-band `dnti_ctx_hot` es default-zeros (NO `None` como en I-band) → el
   guard `is not None` del I04 no cortocircuita; haría falta un `n_dnti_ctx_path > 0` extra para no vaciar Test1.
4. `enable_test1_contextual_filter` ya está ON global → el porte NO sería flag-OFF (activaría V750 en producción).

**Veredicto**: NO portar sin re-verificar la premisa con TIF/ground-truth fresco. El frente real V750 hoy es la
over-detección cat-b (A54/A68/A72), que es display/clasificación, no magnitud. Scoping completo (por si se reabre):
imports + bloque entre `process_viirs_mod.py:1025–1027` (espejo de `process_viirs.py:1498-1509`) + `"I04"→"M13"` +
guard `n_dnti_ctx_path>0` + flag nuevo OFF + A/B aislado midiendo FN a nivel record (A67).

## Implicación para la misión

VIIRS (los dos sensores) está **sano**: recall alto (V375 96% / V750 86%), magnitud en paridad (0.78–0.81×
canónico), anclas honestas vivas, nadir adoptado. **No hay frente de magnitud VIIRS accionable hoy.** El gap
real del proyecto sigue siendo **MODIS summit-gated recall 10.8% (D12)** — el frente §1 en vuelo (run 27521928757).
