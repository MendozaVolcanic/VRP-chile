# Bloque de arranque S34

> Pegar al inicio de la próxima sesión. Resumen estado al cierre S33+ (2026-05-08
> tarde) + plan revert fix S33 + decisiones críticas pendientes.

---

## CHECKLIST OBLIGATORIO ANTES DE ACTUAR

1. Leer [docs/MISSION.md](../docs/MISSION.md) — las 3 preguntas vinculantes.
2. Leer [docs/PROCESS_RULES_S33.md](../docs/PROCESS_RULES_S33.md) — reglas R1-R8 anti-recurrencia.
3. Leer [docs/MIROVA_DIVERGENCES.md](../docs/MIROVA_DIVERGENCES.md) última sección "S33+ — Análisis TIF MIROVA".
4. Leer este documento entero.

Si una propuesta no pasa las 3 preguntas + las reglas R1-R8 → no implementar.

---

## Estado al cierre S33+ (2026-05-08 ~19h hora Chile)

### Operacional actual (en `main`, deployed Pages)

- **Driver A solo**: `enable_test1_pixel_filter: false`, `enable_final_pixel_filter: false`, `enable_test1_lbg_global: false`. Todos refutados.
- **Frontend `mirovaEqVrp` con fix S33**: descarta clusters con `pc.centroid_dist_km > inner_radius_km`. **DECISIÓN PENDIENTE: revertir** (ver más abajo).
- **Reglas R1-R8** instaladas: `pipeline/audit_metrics.py` + `tests/test_audit_metrics.py` (17 tests) + `experiments/76_audit_independent.py`.
- **Vista Diaria** publicada: `frontend/diario.html` accesible desde botón en header.
- Dashboard publicado: https://mendozavolcanic.github.io/VRP-chile/

### Métricas operacionales actuales (Driver A solo + fix S33 activo)

| Métrica | Valor |
|---|---:|
| Recall global | 74.2% |
| Ratio mediano | 2.53× |
| Lastarria | 100% / 18.5× |
| Villarrica | 100% / 64.9× |
| Planchón | 96.8% / 16.0× |
| Chaiten | 90.9% / 18.3× |
| PCC | 94.8% / 12.1× |
| Lascar/Isluga/Tupungatito/Copahue | 49-78% / 0.7-3× |

---

## Hallazgos críticos S33+ post-A/B (NO REPETIR ERRORES)

### 1. Bug `mirovaEqVrp` (S33) descubierto y fixeado

`distance_class==='summit'` se calcula con `final_hotspot_*` pero `primary_cluster`
se elige por VRP máximo — pueden discrepar (Lascar 2026-02-14: dist_class=summit
+ pc a 24km Salar = 19389 MW falso). Bug contaminó todos los audits S27→S31+→S32.

### 2. Driver B Phase 1, Phase 2, D4 REFUTADOS

Re-audit con métrica corregida (post-fix S33):
- Phase 1: recall 74.2% → 55.6%. -18.6pp catastrófico. Pixels Test 1 marginales
  formaban cluster crater real en Lastarria/Villarrica/Planchón.
- Phase 2: recall 73.6% → 10.5%. -63pp. Filtro 5σ a mask final destruye
  volcanes con std_bg heterogéneo (Tupungatito glaciar).
- D4 (L_bg global): efecto despreciable (0.1pp recall mejora). Diseñado para
  resolver problema que el bug S33 había auto-creado.

### 3. Hipótesis VRP integrated Coppola 2015 Eq.1 simulada → REFUTADA

`experiments/77_r2_eq1_simulation.py`: Eq.1 textual con `t_bg_global` da VRP=0
en 96% records test1 porque la suma sin clip se vuelve negativa cuando muchos
pixels Test 1 están más fríos que t_bg_global. Sin granules locales no podemos
simular con `t_bg_local`.

### 4. ⚠️ Análisis TIF MIROVA real (2026-05-08) — DESCUBRIMIENTO IMPORTANTE

`Pruebas/mirova_real/Lascar_VIIRS375_I04.tif` (público sin login):

- TIF tiene **17,911 pixels positivos** sumando 1680 MW pero MIROVA reporta
  solo **VRP: 0.2 MW** en header.
- **Conclusión**: el TIF NO es VRP per-pixel sumable. Es producto de
  **visualización** del campo de radiancia. El "VRP" reportado viene de
  selección de cluster específico, NO suma del TIF.
- Pico TIF (0.187 MW) está a **23 km del vent** (Salar Atacama), pero MIROVA
  reporta detección a 9.7 km — **otro cluster por criterio interno**.

### 5. ⚠️ MIROVA reporta clusters far — fix S33 diverge

Plot Distance MIROVA Last Year muestra MUCHÍSIMOS puntos grises (>5km, far)
junto a rojos (<5km, summit). **MIROVA reporta clusters far como detecciones
válidas**, solo los etiqueta con clase distance. NO los descarta.

Mi fix S33 (`pc_dist > inner_radius → return 0`) **diverge de clon literal
MIROVA**. Es remedio equivocado al síntoma correcto (D5 magnitud inflada
per-pixel, NO "cluster lejos = filtrar").

---

## ⚠️ DECISIÓN USUARIO PENDIENTE (sesión arranca con esto)

**Objetivo confirmado por Nicolás**:
- (A) Clon MIROVA literal — incluye clusters far. **Default operacional**.
- (C) Visualización dual con toggle — "Solo cráter" / "Incluir lejanas".

**Plan ejecutivo S34**:

### Fase 1 — Revertir fix S33 (~20 min)

1. **`pipeline/audit_metrics.py:mirova_eq_vrp`**:
   - Quitar validación `pc.centroid_dist_km > inner_radius`.
   - Solo respeta `distance_class === 'far'` heredado de pipeline.
   - Si `distance_class` no es 'far' (incluye None) y hay `primary_cluster`,
     devuelve `pc.vrp_mw`.

2. **`frontend/index.html:mirovaEqVrp`**:
   - Mismo cambio. Quitar parámetro `innerKm` que ya no se usa.
   - Actualizar callers (latestVRP, eqVrp wrapper, etc.).

3. **`frontend/diario.html:mirovaEqVrp`**:
   - Mismo cambio.
   - **Agregar toggle dual** "Solo cráter" / "Incluir lejanas" replicando
     patrón `includeFarDistance` de index.html.

### Fase 2 — Actualizar tests (~10 min)

`tests/test_audit_metrics.py`:
- `test_bug_s33_summit_class_pero_cluster_far_devuelve_cero` → renombrar a
  `test_clon_mirova_reporta_cluster_far` y assertar que devuelve 19389.8 MW
  (era 0). Documentar el cambio metodológico S34: clon MIROVA reporta lo que
  MIROVA reporta, incluyendo clusters far.
- Tests R1+R7 que validaban inner_radius por volcán pueden quedar como
  documentación histórica o eliminarse. Mantener test sintético "filter por
  distance_class==='far'".

### Fase 3 — Re-audit con métrica revertida (~10 min)

Actualizar `pipeline/audit_metrics.py` y correr `experiments/76_audit_independent.py`.

Predicción:
- **Recall global sube** a ~85-90% (clusters far ahora cuentan).
- **Ratio mediano sube** por outliers (Lascar Salar 19389 reaparece) — quizás
  3-5× mediano.
- Esto refleja la realidad clon MIROVA literal. **No es regresión** — es la
  verdad sin filtro.

### Fase 4 — Re-deploy + verificación R8 (~5 min)

Push a main → Pages deploy → curl tests + visual check.

### Fase 5 — Documentar D5 abierto (~5 min)

Lascar Salar 19389 MW outlier es síntoma D5. Plan a investigar S34+ con TIF
MIROVA reales descargados (volcanes con anomalías cráter persistente que
MIROVA reporte VRP comparable — PCC sin actividad reciente NO sirve, Lascar
sí pero la pasada actual está far).

---

## Pendientes ordenados por valor

### Prioridad 1 — Revert fix S33 + toggle dual (Fases 1-5 arriba, ~50 min)

Cierre del descubrimiento de hoy. Sin esto, dashboard diverge de MIROVA literal
en lo que reporta.

### Prioridad 2 — D5 magnitud (síntoma "Salar 19389 MW")

El revert S33 NO resuelve D5. Hipótesis pendientes:
- VRP integrated Eq.1 con `t_bg_local` (no global como simuló R2). Requiere
  granules para verificar.
- Algún post-procesamiento MIROVA (smoothing, normalización) que produce el TIF
  visualización con valores chicos. Difícil sin código MIROVA original.
- Cap por percentil (eliminar pixels extremos top-X%). Parche, NO en papers.

### Prioridad 3 — D4 sub-pixel summit (Tupungatito 48% recall)

Independiente de Phase 1/D4 refutados. Sigue abierto.

### Prioridad 4 — D3 Llaima (filtro persistencia MIROVA NRT)

460 detecciones nuestras vs 0 alertas MIROVA. Filtro MIROVA no documentado
en papers — divergencia D3.

### Pendientes técnicos menores

- Bug consolidate workflow (`git pull origin main` cuando branch s15-dev). Trivial.
- Goldens regenerar post-S33+.
- Re-scrape Mirova-v1 D2 (~30% gap VIIRS).
- Frontend bugs LOW restantes (cosméticos).

---

## Workflows disponibles (no lanzar sin necesidad)

- `nrt.yml` — cron 2h NRT. Ya OK con Driver A solo.
- `reproc-tier-a-operacional-phase1.yml` — sync 11 Tier A 90d.
- `reproc-ab-test1pix-filter.yml` — A/B Phase 1 (refutado, no relanzar).
- `reproc-ab-phase2.yml` — A/B Phase 2 (refutado).
- `reproc-ab-lbg-global.yml` — A/B D4 (refutado).
- `pages-deploy.yml` — Pages auto + dispatch.

---

## Files clave consultar al arrancar

- `pipeline/audit_metrics.py` (función `mirova_eq_vrp`).
- `frontend/index.html` (función `mirovaEqVrp` ~línea 628, `eqVrp` wrapper ~línea 815).
- `frontend/diario.html` (función `mirovaEqVrp` ~línea 197, agregar toggle).
- `tests/test_audit_metrics.py` (tests S33).
- `experiments/76_audit_independent.py` (audit independiente).
- `Pruebas/mirova_real/` (TIF + KMZ MIROVA reales).
- `Pruebas/output/` (nuestros TIF + KMZ del 8 y 19 abril).

---

## Resumen 2 líneas para pegar al primer prompt S34

> S33+ cerrada (2026-05-08): Phase 1/2/D4 refutados, fix S33 mirovaEqVrp listo
> pero pendiente REVERTIR (hallazgo TIF MIROVA muestra que clon literal incluye
> clusters far). Lee `tasks/BLOQUE_ARRANQUE_S34.md` con plan revert (~50 min).
