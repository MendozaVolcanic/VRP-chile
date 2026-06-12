# Diseño S106 — Ancla espacial honesta (unifica D11-posición + bug final_hotspot + gate frontend)

**Estado**: DISEÑO — pendiente OK Nicolás (A45) para implementación flag-OFF + A/B.
**Origen**: refutación del fondo-local-NTI (design 2026-06-10 §15-16) + pregunta de
Nicolás "¿nos estamos alejando de MIROVA?" + auditoría papers/código/CSV S106.
**Principio rector (Nicolás)**: probemos todo lo que sea necesario; algoritmo sobre
display (A72); 1 algoritmo uniforme, no per-volcán.

## 1. El replanteo (por qué este frente reemplaza al anterior)

Tres fixes (V1, V2, fondo-local) intentaron hacer al **detector** Test1-MIR inmune a
la topografía y los tres fueron refutados con ground truth: a escala local, la señal
débil real es espacialmente suave e indistinguible de la suavidad topográfica
(design 2026-06-10 §15).

La auditoría S106 papers-first cambió el diagnóstico: **el problema no es de detección
sino de POSICIÓN**.

- MIROVA detecta SOLO con NTI y derivados contextuales (Tests 1/2/3, Coppola 2016a
  `sp426_5.txt` L294-356) — inmunes a topografía por construcción (A69). Nuestros
  paths D (dNTI) y ETI-scene SON esos tests y están ON.
- Nuestro "Test1 integrado" usa la Eq.1 de Coppola (fórmula de CUANTIFICACIÓN de
  energía sub-pixel) como detector de presencia. Es extensión nuestra, valiosa
  (cura FN sub-pixel, recall Villarrica 50→80% S25-S27) y NO se toca.
- El daño lo hace que su **centroide** (ponderado por exceso de MIR absoluto) gane la
  cascada del ancla (`final_hotspot`, Regla D S26 + S44): una integral sobre un ROI
  afirma "hay exceso de energía a <3 km del cráter" — no tiene posición por píxel.
  Al inventarle una, heredamos la topografía.

**Un test integrado no tiene posición; dejar de fingir que la tiene.**

## 2. Evidencia empírica (probes S106 sobre baseline en disco, A2)

Scripts: `experiments/_s104_roi_probe/probe_anchor_design.py`, `probe_anchor_design2.py`,
`probe_villarrica_alert_detail.py`, `probe_tupun_cascade.py`. Data: `baseline_mir/` (90 d,
VIIRS375, 5 vols).

1. **Tupungatito**: los records eruption-source tienen el píxel contextual EN el cráter
   (pc mediana 0.36 km, en noches ALERTA 0.27 km). Pero 306/540 records anclan por
   centroide Test1 (1.60 km N) — y en los casos con píxel suelto scene-wide medible,
   77/91 estaban far (mediana 11.57 km) → **la Regla D se dispara por el ancla eruption
   corrupta (bug §5.1-S101) y pisa al cluster bueno**. El fix del ancla cura Tupun sin
   tocar detección.
2. **Villarrica (noches ALERTA, detalle por pasada)**: las pasadas que VEN el cráter
   (típicamente NOAA20 ~06:00 — geometría de visada; las paredes del cráter ocultan el
   lago en ángulos oblicuos) disparan dNTI EN el cráter → pc 0.12-0.30 km, ancla buena
   YA. Las pasadas oblicuas (SNPP/NOAA21 04:42-05:36) no tienen píxel contextual de
   cráter: el "cluster" es 1 píxel suelto de borde glaciar a 2.4-3.0 km (rumbos
   variados) y el ancla queda en el centroide Test1 (1.2-1.65 km N). **Para estas
   pasadas NO EXISTE representación per-pixel honesta de la posición.**
3. **pc NO siempre es contextual**: para records Test1-only el primary_cluster se
   construye DE los píxeles del Test1 (Tupun test1-src: pc mediana 2.46 km) → usar
   "pc.centroid" uniforme NO cura; hay que distinguir pc-contextual de pc-test1.
4. **Lastarria (control de señal real offset)**: 543/676 píxeles contextuales al NW =
   campo fumarólico real (dato de campo A69). El ancla contextual lo preserva (2.26 km
   NW). Los 41 records test1-only son la minoría.
5. **Llaima**: contextuales dominados por entorno del lago Conguillío (N/NE, cat-c
   conocido S58/S105); los test1-src heredan el sesgo N (2297 m). El vent nominal es
   correcto (S105 §3).
6. **Estratificación por sensor verificada** (pedido Nicolás): CSV MIROVA tiene
   Sensor ∈ {MODIS, VIIRS, VIIRS375}; todo el análisis de noches ALERTA acá usa
   VIIRS375-vs-VIIRS375 (`audit_sensor_strat.py`).

## 3. El diseño

### 3.1 Cascada de ancla honesta (uniforme, 3 sensores)

Prioridad de `final_hotspot_*` (reemplaza la lógica actual rama eruption + Regla D):

1. **pc-contextual** (primary_cluster construido de píxeles de paths duros
   dNTI/ETI/BT/NTI): ancla = `pc.centroid_*`. (Es la posición MIROVA-real: píxeles
   flaggeados por tests contextuales, inmunes a topografía.)
2. **Test1-dominante** (sin píxel contextual, o Regla D revisada decide que el
   contextual es far y el Test1 summit): ancla = **variante A: el vent** (semántica
   honesta "exceso integrado en el ROI del cráter", `final_hotspot_source="test1_roi"`)
   o **variante B: el píxel de NTI máximo del ROI** (conserva información de posición
   cuando la fuente real está offset — p.ej. fumarólico — y el NTI es plano sobre
   topografía A69; requiere persistir lat/lon del NTI-max, campo nuevo).
3. **Fallback** (sin pc): píxel suelto solo si no hay nada mejor (comportamiento
   actual documentado como last resort).

La **Regla D** se re-evalúa con el ancla eruption honesta (pc-contextual), no con el
píxel suelto scene-wide → deja de pisar clusters buenos (Tupun caso 1).

**Qué NO cambia**: ningún gatillo de detección (Test1/paths intactos → 0 FN por
construcción, a nivel record), magnitudes (vrp/pc.vrp intactos), cluster selection.

### 3.2 Las dos variantes del paso 2 — A/B con discriminador pre-registrado

- **Variante A (vent)**: simple, MIROVA-consistente con su comportamiento publicado
  (Villarrica Distancia fija 0.84 km desde coord GVP, A13 — publican el cráter).
  Costo: si una fuente real está offset y solo la ve el Test1, su posición se pierde
  (se reporta el cráter).
- **Variante B (NTI-peak del ROI)**: conserva posición de fuente real offset; sobre
  topografía pura el NTI es plano → el peak es ruido SIN sesgo direccional sistemático
  (mediana offN ~0, por registro ruidosa). Costo: campo nuevo + posiciones por-record
  más ruidosas en noches sin señal.
- **Discriminador: Lastarria test1-only** (n=41): si sus NTI-peaks caen en el campo
  fumarólico NW (como los contextuales) → B conserva información real que A borraría.
  Si caen aleatorios → B no aporta y gana A por simplicidad.

### 3.3 Acople MODIS (destape) — va en el mismo paquete

`distance_class` honesto reclasifica far→summit los **131 records MODIS path-D-only
pc.vrp>5 MW (0% confirmados MIROVA = artefacto de magnitud, S105 §5)** que el campo
corrupto hoy esconde por accidente. Per A72 (algoritmo > display) el paquete incluye el
fix de raíz de magnitud path D MODIS, con los 2 candidatos ya scopeados S103 §2:
- **C1: cap D9 273K** (extiende el cap cirrus existente 270→273K), o
- **C2: ctxpeak port a MODIS** (magnitud contextual del path D, espejo del fix S100
  VIIRS375 que curó Tupun 18.9×).
A/B MODIS propio (brazos C1/C2/off) con criterio pre-registrado: los 131 caen a
magnitud MIROVA-like (<5 MW) o quedan suprimidos; Láscar MODIS (~78 dets reales,
ratio 0.92× S102) intacto; 0 FN MODIS.

### 3.4 Frontend (post-promoción, 3 vistas — S92 L5)

- `distance_class` pasa a ser confiable → el gate `mirovaEqVrp` queda igual pero deja
  de depender de un campo corrupto; verificación visual en preview de los 11.
- Sincronizar `mirovaEqVrp` de `diario.html` con index/mosaico (drift detectado S106:
  firma distinta, sin fallback pre-S27).
- `final_hotspot_source` nuevo (`test1_roi`/`nti_peak`) disponible para distinguir en
  mapa "posición = cráter por semántica" de "posición = píxel detectado" (tooltip), sin
  ocultar nada.

## 4. Predicciones PRE-REGISTRADAS del A/B (A66 — escritas ANTES del reproc)

Brazos VIIRS: base (en disco) / ancla-A (vent) / ancla-B (NTI-peak). 5 vols, 90 d.

| vol | predicción | criterio duro |
|---|---|---|
| Tupungatito | offN 1047→≤300 m vía pc-contextual (Regla D ya no pisa); trig_t1 IDÉNTICO (465); recall 72/72 V375 | recall+trig_t1 sin cambio; offN ≤300 m |
| Villarrica | pasadas con cráter visible: igual (~0.7-1.0 km); oblicuas → vent (A) o NTI-peak (B); offN 748→≤200 m (A) | recall 7/10 V375 sin cambio; dist mediana ≤1.0 km |
| Llaima | test1-src → ancla cráter; eruption-src lago quedan (cat-c, fuera de scope) | recall 1/1; offN mediana ↓ fuerte |
| Lascar | sin cambio (eruption-src al cráter dominan) | offN/dist/recall sin cambio |
| Lastarria | contextuales conservan NW real (2.26 km); test1-only n=41: A→vent, B→¿NW? (discriminador 3.2) | recall 94/105 sin cambio; mediana NW de contextuales CONSERVADA |
| MODIS (11 si aplica / 5) | 131 path-D-only <5 MW o suprimidos; Láscar 0.92× intacto | 0 FN MODIS; Láscar conserva ~78 dets |

**Decisión pre-comprometida**: si recall o trig_t1 cambian en CUALQUIER brazo del ancla
→ hay un bug (el ancla no debe tocar detección) → investigar antes de seguir. Si
Lastarria-B muestra NTI-peaks en el fumarólico → adoptar B; si aleatorios → A. Si los
131 MODIS no se curan con C1 ni C2 → NO mergear el ancla MODIS (evitar destape) y
re-diseñar; el ancla VIIRS puede promoverse sola (el destape es MODIS-específico).

## 5. Plan de implementación (A45 — espera OK de Nicolás)

1. Tag defensivo `pre-s106-honest-anchor` + push.
2. TDD: tests sintéticos de la cascada (pc-contextual gana; test1-only → vent/NTI-peak;
   Regla D con ancla honesta; pc=null fallback; F47 cluster_rescue sigue coherente)
   ANTES del código (R1/R7).
3. Implementación flag-OFF: `enable_honest_anchor` (+ `honest_anchor_test1_mode:
   vent|nti_peak`) en los 3 process_*.py + persistir `final_hotspot_source` nuevo y
   (variante B) `nti_peak_lat/lon`. Cuidado A49 (returns) + A46/A47.
4. Fix magnitud path D MODIS flag-OFF (`enable_path_d_cap_273k` o ctxpeak port).
5. A/B GH Actions (patrón S105: 2 chunks × vol, data_subdir aislado): brazos ancla-A,
   ancla-B (VIIRS 5 vols) + C1/C2 (MODIS). Baselines ya en disco.
6. Audit pre-escrito contra §4 + R3 independiente. Promoción solo si criterios duros
   pasan (A45: OK Nicolás + reproc 11 + R2/R3/R8 + frontend 3.4 + cierre D11 en
   MIROVA_DIVERGENCES + actualizar AUDIT_S105 P2-9).

## 6. Riesgos y pre-mortem

- **Lastarria pierde el offset real en variante A**: mitigado — los contextuales (la
  mayoría) lo conservan; el discriminador 3.2 decide si B es necesaria.
- **Destape MODIS si el ancla mergea sin el fix de magnitud**: bloqueado por la
  decisión pre-comprometida §4 (no mergear ancla MODIS sin C1/C2 validado).
- **store.py F47 asume el ancla vieja**: revisar cluster_rescue para que no
  re-sobrescriba el ancla honesta (test dedicado).
- **A55**: el fix MODIS C1/C2 es de MAGNITUD de artefacto (cat-d, 0% MIROVA), no gate
  intra-radio por path — clasificación física hecha (S105 §5). No reabre el ciclo.
- **Schema**: `final_hotspot_source` ya existe (F47); valores nuevos son aditivos.
  Frontend usa distance_class + pc.* — sin breaking change (A46).

## 7. Preparación Fase 2 (S106, mientras corría el A/B run 27343409067) — descartes con datos

Probes sobre `data/mirova_equivalent/` en disco (`experiments/_s106_fase2/`):

**C1 (cap D9 270→273K) REFUTADO**: los 132 records MODIS inflados (pc.vrp>5) NO son
cirrus — `t_bg` mediana 279-288K (escena tibia), campos path legacy en None, la
detección viene del **first-pass contextual** (Tests 2∧3, 15-78 píxeles). Un cap por
`t_bg<273K` atraparía **0** de los 132. El framing "cirrus" de S103 §2 era de la era
pre-first-pass; estos artefactos son otro mecanismo.

**Piso de energía-por-píxel (variante C2) REFUTADO — discriminante INVERTIDO**:

| población | n | npx cluster med | vrp/px med | dist med |
|---|---|---|---|---|
| Inflados pc>5 (11 vols, 0% MIROVA) | 132 | 11 | **0.687 MW/px** | 1.66 km |
| Láscar real (control 0.92×) | 248 | 4 | **0.213 MW/px** | 1.92 km |

La señal MODIS real es de clusters chicos y débiles; el artefacto es un blob de
píxeles MÁS calientes. Cualquier piso por píxel conserva el artefacto y mata lo real
(thr=0.5: 89% inflados escapan, Láscar pierde 83%). El tamaño (npx 11 vs 4) separa
parcialmente pero solapa (p90 Láscar = 11). "ctxpeak port" no aplica (no son records
Test1).

**Estado**: el fix de magnitud del destape MODIS queda como pregunta de diseño
ABIERTA para la Fase 2 (candidatos restantes: dispersión/compactez espacial del
design 2026-06-05 §5.2 — ahora con first-pass framing —, co-validación, o el
análogo algorítmico del descarte visual MIROVA sp426_5 L689-696 "typically <5 MW").
Mientras tanto la decisión pre-comprometida §4 rige: **el ancla MODIS NO se mergea
sin este fix** (el ancla VIIRS puede promoverse sola).

**Recon de inserción MODIS/V750** (agente Explore, verificar líneas al implementar,
A48): cascada MODIS 1020-1052 / V750 965-993 (espejo exacto de VIIRS); cluster build
MODIS 913-930 / V750 876-893; recompute test1 MODIS 1144-1162 / V750 1081-1099;
first-pass existe en ambos (`hot_mask_2d = fp_hot` MODIS:702, V750:692); NTI y
vent_dist_per_pixel existen en ambos; sin Eq.16 ni ctxpeak (solo VIIRS375).

## 8. RESULTADOS S106 del A/B (run 27343409067, 20/20 + reruns) — vs predicciones §4

**Incidente de cobertura (lección operacional)**: 2 jobs del brazo A salieron truncados
con conclusion=success (Lastarria ch1: 4 días de 62; Llaima ch1: hasta 03-20) — el
circuit-breaker A64 degrada con gracia en NRT pero en REPROC produce data parcial
SILENCIOSA. Detectado por audit de cobertura de fechas pre-análisis (verificar SIEMPRE
rangos de fechas de cada chunk antes de auditar un A/B). Reruns seriales con
`gh run rerun --job` (GitHub no permite 2 reruns simultáneos del mismo run).

**Verificación pareada al granule (criterio duro 1)**: en la intersección exacta de
(sensor, datetime) base∩A — Tupungatito 540, Villarrica 592, Láscar 486, Lastarria
488 granules — **trig_t1 difiere en 0 granules** en los 4 vols completos. Los deltas
agregados (Villarrica 461 vs 462, Lastarria 448 vs 441) son variabilidad de
disponibilidad NASA entre corridas (granules extra/faltantes), NO lógica. ✓ EL ANCLA
NO TOCA LA DETECCIÓN, exactamente como se diseñó.

| vol | offN base→A (m) | dist base→A (km) | recall | veredicto §4 |
|---|---|---|---|---|
| Tupungatito | 1047 → **0** | 1.50 → 0.00 | 75/75 ✓ | **PASA** (≤300 ✓) |
| Villarrica | 748 → **0** | 1.56 → 0.00 | 8/11 ✓ | **PASA** (≤200 ✓) |
| Llaima | 1097 → **0** | 1.64 → 0.00 | 1/1 ✓ | PASA (pendiente rerun ch1 para cifras finales) |
| Láscar (ctrl) | 23 → 1 | 0.32 → 0.16 | 117/127 ✓ | **PASA** (sin cambio) |
| Lastarria (ctrl) | 886 → **960 conservado** | 1.22 → 1.12 | 94/105 ✓ | **PASA** (NW fumarólico vivo vía ctx_cluster 300/453) |

**Discriminador A-vs-B (§3.2, Lastarria test1-only n=153 brazo B)**: NTI-peaks
NW 70 / SW 42 / SE 23 / resto 18 — NW es moda (46%) pero con dispersión alta; y en
los nevados el brazo B EMPEORA el offN (Villarrica 884 vs 748 base; Llaima 2263):
en noches débiles el campo NTI es plano y su máximo cae en ruido o en el lago.
**Decisión pre-comprometida: GANA EL BRAZO A (vent)** — B no conserva señal con
suficiente fidelidad para justificar su ruido.

**CIFRAS FINALES (rerun Llaima attempt 3 completo)**: Llaima trig_t1 428=428 exacto,
0 diffs pareados, offN 1097→0, recall 1/1. **Los 5 vols pasan TODOS los criterios
duros** (0 diffs de trig_t1 pareados en los 5; offN nevados → 0; controles intactos;
Lastarria NW conservado). Brazo B descartado formalmente (Villarrica 884/Llaima 2263 m
— el pico NTI cae en ruido/lago en noches débiles; discriminador Lastarria 46% NW
insuficiente).

## 9. PROMOCIÓN S106 (OK Nicolás "confirmo... continua con todo")

- **Flip**: `enable_honest_anchor: true` (modo vent) en mirova_equivalent.yaml — NRT
  produce anclas honestas desde el merge. Espejos MODIS/V750 implementados con flags
  SEPARADOS OFF (PR #401; MODIS gateado por fix destape §7).
- **Data promovida** (merge_promote_honest_anchor.py, semántica de UNIÓN S101): los 5
  vols del A/B desde los artifacts del brazo A (Villarrica +1 granule legacy
  conservado). R3 sobre data/mirova_equivalent: offN 0/0/0/1/948(NW) ✓.
- **6 Tier A restantes**: reproc flag-ON en vuelo (run 27422803708, 12 jobs,
  workflow reproc-s106-anchor-rest.yml) → promoción al aterrizar (mismo script).
- Los records NRT post-2026-06-08 quedan con ancla legacy hasta que el cron los
  regenere (transitorio aceptado, patrón S103).
- Rollback completo: tag `pre-s106-honest-anchor`.
- **Pendiente Fase 2**: fix magnitud destape MODIS (§7, pregunta abierta) → activar
  espejo MODIS; validación V750; frontend 3 vistas (sync diario.html); cierre D11.
