# Design — F5' magnitud campo-frío VIIRS (desacoplar detección de magnitud)

**Sesión S94 (2026-05-31).** Brainstorming. Estado: DISEÑO, NO implementado.
Decisión de Nicolás: **display primero** (reversible, sin tocar NRT), luego pipeline
si convence (A45). Calibración pendiente de la data reprocesada limpia (FASE 1 recent).

Diagnóstico previo: `docs/AUDIT_S94_per_sensor_metrics.md` §7. Datos:
`experiments/_s94_audit/`.

## 1. Problema (fundado en papers + código)

**Cómo calcula MIROVA** (Coppola 2016a SP426.5, `documentacion/`): `VRP = Σ VRP_pix`
del **clúster** (componente conexa 8-vec), con `VRP_pix = k · A_pix · ΔL_MIR`. Los
píxeles que entran a la suma son los que pasan los tests de detección **dual-ROI**
(ROI1 summit C1=0.003/C2=5σ; ROI2 escena C1=0.01/C2=10σ).

**Nuestro código** (`process_viirs.py:1111-1113`): `vrp_mir_mw = Σ per_pixel_vrp_mw`
sobre `hot_rows,hot_cols = np.where(hot_mask_2d)` — la suma corre sobre **TODA la
máscara de detección**, incluido el path D contextual sensible. NO hay un umbral
separado para la magnitud: **el conjunto de detección = el conjunto de magnitud.**

**Mecanismo del artefacto:** sobre fondo glaciar (−30 °C), el path D marca el halo de
roca tibia-vs-nieve (ΔL chico pero positivo, contraste hielo↔roca). Sumar decenas de
esos píxeles infla la magnitud 3–20× (Tupungatito 10.78×). Láscar (cráter de roca
caliente, sin halo nevado) calibra a 0.93× porque no tiene halo. **No es calibración,
ni resolución (mismo sensor que MIROVA), ni suma-vs-foco (MIROVA también suma).**

## 2. La restricción de seguridad (el corazón del diseño)

Cualquier reducción de magnitud **NO debe sub-contar señal volcánica real débil**
(lava lake Villarrica 0.05–0.2 MW, cráter Tupungatito ~0.3 MW sub-píxel — la razón
de ser del recall VIIRS375).

**Dato duro (`experiments/_s94_audit`, cruce TP vs MIROVA):** las detecciones reales
confirmadas por MIROVA son **path-D-only** (sin BT/NTI duro): Tupungatito 100%,
Lastarria 99%, Isluga 96%, PCC 93%, Villarrica 89%, Láscar 75%.

→ **El tipo de path NO distingue halo-frío de volcánico-real.** Ambos son débiles y
contextuales. Esto **refuta** el enfoque "excluir path-D-only" (enfoque B) y la
co-validación tipo F3 para VIIRS: borrarían el 75–100% de las detecciones reales.
También **debilita** un gate de ΔL/NTI por píxel (enfoque A): el píxel del cráter y la
roca tibia-solar pueden tener intensidad parecida.

**El único discriminante robusto es ESPACIAL** (auditoría espacial §6): el foco real
está **concentrado cerca del cráter**; el halo está **disperso** sobre el glaciar. Esto
coincide con MIROVA (suma un clúster conexo; el campo disperso queda en componentes
separadas). Nuestro path D sensible engorda la componente conexa hasta tragarse el
halo → suma inflada. **F5' = desacoplar detección (sensible, recall intacto) de la
magnitud (núcleo concentrado).**

## 3. Las tres sub-variantes espaciales (a A/B-testear contra MIROVA)

Datos disponibles por record (post-reproc, consistentes): `anomaly_pixels[]` con
`{lat, lon, dist_km, bt_k, vrp_mw}` (top-100) + `primary_cluster {centroid_lat/lon,
n_pixels, vrp_mw}`. Las 3 son computables en el frontend (display-first) sobre estos
campos.

### D1 — Núcleo por densidad/conectividad (topológico)
- **Qué:** reportar solo la **sub-componente densa** del clúster. El foco real es una
  concentración densa de píxeles; el halo es ralo/disperso. Recortar píxeles cuyo
  vecindario local (radio r) tenga menos de `k_min` píxeles anómalos (DBSCAN-like:
  core points con ≥k_min vecinos en r). Sumar solo los core points.
- **Discrimina:** densidad espacial. Halo ralo → recortado; foco denso → conservado.
- **Modos de falla / pre-mortem:**
  - ⚠️ Un foco real **muy débil de 1–2 píxeles** (Villarrica lava lake) NO es "denso"
    → podría recortarse. **Mitigación:** excepción "siempre conservar el píxel pico y
    sus 8-vecinos inmediatos" (el foco nunca se anula).
  - Un halo glaciar que casualmente forma un parche denso local → conservado (falso
    negativo del filtro). Raro pero posible.
- **Parámetros a calibrar:** r (km), k_min (vecinos). 

### D2 — Decaimiento radial desde el pico (distancia)
- **Qué:** el píxel **pico** (mayor vrp) es el foco. Sumar píxeles dentro de un radio
  `R_core` del pico (o ponderar con peso que decae con la distancia al pico). Más allá
  de `R_core`, descartar (es cola dispersa).
- **Discrimina:** proximidad al foco. El halo disperso cae fuera de `R_core`.
- **Modos de falla / pre-mortem:**
  - ⚠️ **Erupción real extendida** (Láscar fuerte, lava que cubre área grande): píxeles
    reales calientes más allá de `R_core` se recortarían → **sub-estima un evento
    real**. **Mitigación crítica:** `R_core` adaptativo — si los píxeles fuera del
    radio son **calientes de verdad** (bt alto / ΔL alto), extender el radio (son lava,
    no halo). Combina radial + intensidad solo para la EXTENSIÓN del radio.
  - Si el pico cae en un píxel de halo casual (no en el cráter), el radio se ancla mal.
    **Mitigación:** anclar el pico al píxel más cercano al vent entre los top-N, no al
    máximo global (consistente con vent_anchored).
- **Parámetros:** R_core (km), regla de extensión por intensidad.

### D3 — Trimming robusto de outliers espaciales (estadístico)
- **Qué:** calcular el centroide del clúster y la dispersión robusta de las distancias
  píxel→centroide (mediana + MAD). Recortar píxeles cuya distancia al centroide sea
  outlier robusto (> centroide + `c·MAD`). Sumar el núcleo coherente.
- **Discrimina:** coherencia espacial. El halo disperso son outliers de distancia; el
  foco coherente no.
- **Modos de falla / pre-mortem:**
  - ⚠️ Si el halo es la **mayoría** de los píxeles (campo difuso domina), el centroide y
    el MAD se corren hacia el halo → el "núcleo robusto" queda mal definido y puede
    incluir halo / excluir el foco real chico. **Mitigación:** anclar el centroide al
    vent (no al centroide de masa de los píxeles), y medir dispersión desde ahí.
  - Erupción extendida real: dispersión grande pero **coherente** (no outliers) → el
    MAD crece y conserva todo. ✓ (ventaja sobre D2).
- **Parámetros:** c (factor MAD), ancla (vent vs centroide de masa).

## 4. Matriz de modos de falla (por qué A/B-testear las 3)

| Escenario | D1 densidad | D2 radial | D3 trimming |
|---|---|---|---|
| Halo disperso glaciar (Tupun) — **recortar** | ✓ ralo→fuera | ✓ lejos del pico | ✓ outliers |
| Foco real débil 1-2px (Villarrica) — **conservar** | ⚠ riesgo (no denso) | ✓ es el pico | ✓ no outlier |
| Erupción extendida real (Láscar) — **conservar** | ✓ denso | ⚠ riesgo (fuera de R) | ✓ coherente |
| Lacolito difuso REAL (PCC, cat. b) — **¿?** | trata como halo | trata como halo | trata como halo |

**Observación clave:** ninguna es perfecta sola. D3 (anclado al vent) parece la más
robusta a los extremos (débil-real y extendido-real), D2 necesita la regla de extensión
por intensidad, D1 necesita la excepción del píxel-pico. **PCC (lacolito difuso real,
707 km²) es un caso aparte** — es campo extendido genuino (cat. b, A20/A24); las 3 lo
recortarían como halo. Para PCC hay que decidir aparte (quizá no aplicar F5', o
reportar el foco aceptando que sub-estima el lacolito que MIROVA tampoco resuelve bien).

## 5. Plan de calibración (cuando llegue la data reciente limpia)

`experiments/_s94_audit/f5_magnitude_candidates.py` (ya parametrizado con
`VRP_DATA_DIR`) extendido a las 3 variantes. Para cada una, barrer sus parámetros y
medir el **ratio mediano vs MIROVA por volcán**. Criterio de aceptación:
1. **Láscar (cráter caliente) se mantiene 0.9–1.1×** (no romper el caso ya bueno).
2. **Tupungatito/Villarrica/Lastarria bajan a ~0.8–1.3×** (curar el campo frío).
3. **Ningún record confirmado por MIROVA cae a VRP=0** (no perder señal real débil).
4. **R2 pixel-level** vs TIF MIROVA en ≥1 caso (Tupungatito tiene alertas; falta TIF —
   usar PCC/Láscar que sí tienen TIF en `mirova-tif-archive`).
Elegir la variante (o híbrido) que cumpla las 4. Si dos empatan, preferir la de menos
parámetros (navaja de Occam) y menos riesgo en los extremos (D3 anclado-vent candidata).

## 6. Implementación (display primero, A45)
- Réplica de la variante elegida en `frontend/` (3 vistas) como `mirovaEqVrpCore(r)` —
  recomputa la magnitud desde `anomaly_pixels` del record (post-reproc consistente).
- Validación = preview real navegador (no node --check), las 3 vistas (S92 L5).
- Solo si convence visualmente + contra MIROVA → bajar a `process_viirs.py` (un segundo
  umbral/selección para la suma de magnitud, detección intacta) con tag+OK+TDD+reproc+R2.

## 7. Escudo anti-drift
- **Detección NUNCA se toca** (recall intacto — la magnitud es un post-proceso del set).
- NO co-validación / NO excluir path-D-only (refutado §2: borra reales).
- NO kernel-bg en glaciar (A19).
- PCC (lacolito real) decidido aparte, no forzar (A55).
- Calibrar SOLO contra data reprocesada consistente (no histórica — confound A18/A50).
