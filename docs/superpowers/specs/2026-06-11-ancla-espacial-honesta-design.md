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
