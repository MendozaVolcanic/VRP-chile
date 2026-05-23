# F30 Frontend bugs 6-11 — implementation plan S74+

> 6 bugs UI menores sobreviven desde audit S67 (`tasks/frontend_bugs_s67_remaining.md`,
> commit `e778af0`). Este doc es el **plan de implementación bite-sized** per
> `writing-plans` skill. **NO implementado todavía**. Estimado total: **3.5–4.5 horas**
> (audit S73 estimó 6-8 h; refinamos abajo).
>
> **Por qué importa (geólogo first)**: el operador SERNAGEOMIN de turno usa el
> dashboard para tomar decisiones de alerta. Los 6 bugs no rompen ciencia (VRP correcto,
> summit/far correcto, MIROVA-comparison correcto post-S68), pero erosionan
> *confianza* del operador: un toggle que cumple a medias o un stat box que no
> coincide con la tabla de abajo planta la duda "qué más estará mostrando mal".
> Después de S33 el listón de confianza está alto. Estos fixes son polish, no rescate.

---

## Verificación pre-plan (estado real en `frontend/index.html` @ HEAD `73af5e7`)

Re-grepeado contra `frontend/index.html` (2120 líneas, post-S73 cleanup `applyS38Filter`).
Líneas shifteadas vs audit S70 (que decía 939/1844) por commits intermedios — la
lógica del bug sigue idéntica.

| Bug | Status | Línea(s) actual(es) | Audit S70 decía | Comentario |
|---|---|---|---|---|
| 6 — stat Detecciones diverge | **VIVO** | `955` | 939 | `addStat("Detecciones", String(allVrp.length), "granules");` confirmado |
| 7 — overview marker size lineal | **VIVO** | `1860` | 1844 | `7 + vrp * 2` confirmado (líneas 1330/1586/1805 ya usan `log10` — inconsistencia real) |
| 8 — auto-refresh 5min sin timestamp | **VIVO** | `2061-2068` | 2045 | `setInterval(..., 5 * 60 * 1000)` re-fetcha 45 vols |
| 9 — sensor legend toggle parcial | **VIVO** | handler `1699-1703`; callsites `buildDistanceData:1459`, `buildVREData:1471`, `buildComparisonData` (~1493) | 1683 | Handler solo llama `renderDetail()`, no propaga a charts secundarios ni overview map |
| 10 — toggles no persisten sessionStorage | **VIVO** | `595` sensorVisible, `603` includeFarDistance, `1997` removeItem comentario | 588/1981 | Convención existe (línea 614 comentario, 1997 remove) pero solo el flag `vrp_post_s38_only` la usó y fue removido S73 |
| 11a — distance scatter ignora toggle far | **VIVO** | `1459-1469` `buildDistanceData` | 1443 | No consulta `includeFarDistance` ni `isSummitDetection`. Otros loops (1114, 1317, 1728, 1857) sí lo consultan — inconsistencia |
| 11b — cards distance counts fijos 7d | **VIVO** | `852`, `1868` | 836/1852 | `distanceCounts(d.records, 7)` hardcoded en 2 sitios |

**N bugs vivos: 6** (ningún fix accidental detectado). **N FIXED ya: 0**. **N no
localizable: 0**.

---

## Plan por bug (formato bite-sized writing-plans)

Convención de cada plan:
- **Files**: paths absolutos relativos al repo root
- **Steps**: cada paso 2-5 min; cuando aplica, TDD micro (test sintético en
  `tests/frontend/` con jsdom o smoke test manual con checklist)
- **Pseudocódigo** del fix (no implementado)
- **Acceptance criteria** verificables

### Bug 6 — Stat "Detecciones" coincide con tabla / charts

**Por qué importa**: el operador ve "Detecciones: 47" arriba y la tabla NRT debajo lista 12 filas. Discrepancia visible.

- **File**: `frontend/index.html`
- **Línea**: 955 (def stat) + lectura `allVrp` ~901
- **Causa raíz**: `allVrp` es array pre-filtro distance/discard (incluye granules con vrp=0 que vienen del pipeline). Post-S68 el resto del panel usa `eqVrp(r) > 0`.
- **Decisión semántica antes del fix**: hay dos lecturas posibles del stat.
  - (a) "Detecciones útiles" = granules con `eqVrp(r) > 0` (coincide con tabla, chart, "Promedio activo").
  - (b) "Granules procesados" = total con cualquier dato (incluye descartados).
  - **Recomendado**: (a) + opcionalmente segundo stat "Granules procesados" si (b) interesa.

**Steps (bite-sized)**:

1. (2 min) Agregar smoke checklist en `docs/F30_BUG6_CHECKLIST.md`: abrir dashboard local con Lascar 7d → anotar "Detecciones" stat vs nº filas tabla NRT vs nº puntos chart principal. Pre-fix los 3 difieren; post-fix los 3 coinciden.
2. (3 min) Reemplazar en `frontend/index.html:955`:
   ```js
   // antes:
   addStat("Detecciones", String(allVrp.length), "granules");
   // después:
   const detecciones = filtered.filter(r => eqVrp(r) > 0).length;
   addStat("Detecciones", String(detecciones), "granules");
   ```
3. (2 min) Abrir `python -m http.server` desde repo root, navegar a `frontend/index.html?volcano=Lascar`, verificar checklist.
4. (1 min) Commit: `fix(frontend): bug 6 — stat Detecciones usa eqVrp consistent con tabla`.

**Acceptance**: en Lascar 7d, stat Detecciones == nº filas tabla NRT == nº puntos chart principal (delta = 0).

**Costo**: 10 min.

---

### Bug 7 — Overview marker size: linear → log10

**Por qué importa**: el mapa overview de 45 volcanes es el "tablero de turno". Hoy 0.5 MW y 5 MW se ven casi igual (radios 8 vs 9 px) — justo el rango donde MIROVA discrimina Bajo de Moderado. Detail panel, distance scatter y popup ya usan log10 (líneas 1330/1586/1805). Bug 7 es inconsistencia interna.

- **File**: `frontend/index.html`
- **Línea**: 1860
- **Otras 3 referencias log10 ya en uso**: 1330, 1586, 1805

**Steps**:

1. (2 min) Reemplazar línea 1860:
   ```js
   // antes:
   const size = lv.key === "nd" ? 6 : Math.max(7, Math.min(16, 7 + vrp * 2));
   // después (alineado con línea 1805 "vrpShow"):
   const size = lv.key === "nd" ? 6 : Math.max(7, Math.min(16, 7 + Math.log10(Math.max(vrp, 0.01)) * 4));
   ```
2. (3 min) Verificación visual: abrir dashboard, observar que volcanes en niveles `Bajo`/`Moderado`/`Alto` tengan markers visualmente distintos. Tomar screenshot en `docs/F30_BUG7_BEFORE_AFTER.png`.
3. (1 min) Commit.

**Acceptance**: marker para vrp=0.1 MW (radio ~3 con cap 7) y vrp=10 MW (radio ~11) son visualmente distintos a ojo. Cap 16 sigue activo en >100 MW.

**Costo**: 6 min. Trivial.

---

### Bug 8 — Auto-refresh 5 min stale + sin timestamp + sin If-Modified-Since

**Por qué importa**: el cron NRT corre cada 2h, el scraper TIF cada 5 min. Polling cada 5 min genera ~540 fetches/h al CDN GitHub Pages — exceso para data que casi nunca cambió en el último intervalo. Además el usuario no sabe "cuán fresco" es lo que ve.

- **File**: `frontend/index.html`
- **Líneas**: 2061-2068 (setInterval), clock area (línea ~1954)

**Steps**:

1. (3 min) Subir intervalo a 15 min:
   ```js
   // línea 2068:
   }, 15 * 60 * 1000);   // 5 min → 15 min (cron NRT es 2h, suficiente)
   ```
2. (5 min) Agregar timestamp visible. Buscar el clock element (~1954) y añadir un span hermano `<span id="last-refresh-ts">--:--</span>`. En el setInterval, después del `renderDetail()` setear `document.getElementById("last-refresh-ts").textContent = new Date().toISOString().slice(11,16) + " UTC"`.
3. (10 min) [Opcional, no obligatorio para cerrar bug] Conditional fetch con `If-Modified-Since`. GitHub Pages devuelve `Last-Modified`. Cachear el header por archivo en `Map`, mandar `If-Modified-Since` en el siguiente fetch, si 304 saltar parse. Reduce ancho de banda ~90%.
4. (2 min) Smoke test manual: abrir dashboard, esperar 15 min, ver que el timestamp cambia. Network tab muestra 304s post-conditional fetch si se hizo (3).
5. (1 min) Commit.

**Acceptance**:
- setInterval = 15 min.
- Timestamp visible y cambia tras refresh.
- (Si se hizo 3) DevTools Network muestra 304 Not Modified para archivos sin cambios.

**Costo**: 20 min (sin 3) / 40 min (con 3 opcional).

---

### Bug 9 — Sensor legend toggle propaga a charts secundarios + overview

**Por qué importa**: el operador ve sobre-detección MODIS (caso conocido S67/S69 con Villarrica+Chaiten en granule 2026-05-17) y oculta MODIS desde el legend. El chart principal lo respeta, pero distance scatter, VRE chart, MIROVA comparison y overview hotspot map siguen mostrando puntos MODIS. Toggle promete pero cumple parcial.

- **File**: `frontend/index.html`
- **Líneas**:
  - Handler: 1699-1703
  - Callsites a actualizar: `buildDistanceData:1459`, `buildVREData:1471`, `buildComparisonData` (~1493), `buildOverviewMap` (~1857 forEach), hotspot layer (~1728).

**Steps**:

1. (3 min) Agregar guarda en `buildDistanceData` (línea 1461 dentro del for):
   ```js
   if (sensorVisible[r.sensor] === false) continue;
   ```
2. (3 min) Misma guarda en `buildVREData` y `buildComparisonData` (4 sensores: MODIS/VIIRS375/VIIRS750/MIROVA — ya existe el patrón sensorVisible.MODIS).
3. (5 min) En el handler línea 1700, agregar full rebuild post-toggle:
   ```js
   item.addEventListener("click", () => {
     sensorVisible[s.key] = !sensorVisible[s.key];
     item.classList.toggle("dim", !sensorVisible[s.key]);
     renderDetail();
     buildOverviewMap();   // re-render markers respect toggle
     buildCards();         // counts en cards también
   });
   ```
4. (2 min) En `buildOverviewMap` (~1857 forEach), saltar sensores ocultos al construir el latestVRP (puede requerir extender `latestVRP(records, includeFarDistance, innerKm, sensorVisible)`).
5. (5 min) Smoke checklist: ocultar MODIS, verificar (a) detail chart sin MODIS, (b) distance scatter sin puntos MODIS, (c) VRE chart sin MODIS, (d) overview map markers cambian si vol depende de MODIS, (e) re-toggle restaura todo.
6. (1 min) Commit.

**Acceptance**: ocultar MODIS desde legend hace desaparecer toda traza MODIS de los 5 paneles. Re-toggle restaura sin reload.

**Costo**: 35 min. Es el más riesgoso del lote — múltiples callsites + posible cambio de signature de `latestVRP`. Hacer aparte de Bug 6+7.

---

### Bug 10 — Toggles persisten en sessionStorage (helper común)

**Por qué importa**: operador SERNAGEOMIN entra/sale del dashboard varias veces por turno. "Solo cráter on + MODIS oculto + hotspot on" es config favorita; perderla cada reload molesta.

- **File**: `frontend/index.html`
- **Líneas**: 595 (`sensorVisible`), 603 (`includeFarDistance`), 1700 (toggle sensor), 1949 (hotspot layer btn), 2002/2010 (toggle far).

**Steps**:

1. (5 min) Definir helper cerca del top del `<script>` (post línea 590):
   ```js
   function persistedFlag(key, defaultValue) {
     const v = sessionStorage.getItem(key);
     if (v === null) return defaultValue;
     return v === "true";
   }
   function setPersistedFlag(key, value) {
     sessionStorage.setItem(key, String(!!value));
   }
   ```
2. (3 min) Migrar `includeFarDistance` (línea 603):
   ```js
   let includeFarDistance = persistedFlag("vrp_include_far", false);
   ```
   Y en los 2 toggles (2002/2010), después de asignar, llamar `setPersistedFlag("vrp_include_far", includeFarDistance)`.
3. (3 min) Migrar `sensorVisible`: serializar dict como JSON.
   ```js
   const sensorVisible = JSON.parse(sessionStorage.getItem("vrp_sensors") || 'null') 
     || { MODIS: true, VIIRS375: true, VIIRS750: true, MIROVA: true };
   ```
   En el handler (1700) añadir `sessionStorage.setItem("vrp_sensors", JSON.stringify(sensorVisible))`.
4. (3 min) Hotspot layer btn (~1949): mismo patrón con key `"vrp_hotspot_on"`.
5. (3 min) Smoke test: configurar 3 toggles → F5 reload → verificar que persisten. Cerrar pestaña, abrir nueva → no persiste (sessionStorage es per-tab por diseño).
6. (1 min) Commit.

**Acceptance**: F5 conserva todos los toggles en la misma pestaña. Nueva pestaña arranca con defaults (es sessionStorage, no localStorage, intencional — turno = pestaña).

**Costo**: 18 min.

---

### Bug 11a — Distance scatter respeta toggle "Solo cráter"

**Por qué importa**: misma promesa rota que Bug 9, otro panel. Usuario toggle "Solo cráter" → stat se ajusta, scatter no.

- **File**: `frontend/index.html`
- **Línea**: 1459-1469 `buildDistanceData`

**Steps**:

1. (3 min) Modificar `buildDistanceData`:
   ```js
   function buildDistanceData() {
     const pts = [];
     for (const r of filtered) {
       const vrp = r.vrp_mw ?? 0;
       if (vrp <= 0 && !r.triggered_test1) continue;
       const dist = r.hotspot_dist_km ?? r.final_hotspot_dist_km ?? ...;
       if (dist == null) continue;
       // NEW: respetar toggle Solo cráter
       if (!includeFarDistance && dist > innerKm) continue;
       pts.push({ ... });
     }
     return pts;
   }
   ```
2. (2 min) Smoke: activar "Solo cráter" en Villarrica → scatter pierde puntos far. Desactivar → vuelven.
3. (1 min) Commit.

**Acceptance**: scatter responde 1:1 al toggle "Solo cráter" como el resto del panel.

**Costo**: 6 min. Trivial.

---

### Bug 11b — Cards distance counts dinámicos según rango (decisión: dinamizar o documentar)

**Por qué importa**: cards muestran "🎯 Cráter: N · 📍 Lejanas: M (7d)" hard-coded. Si el usuario cambió el rango global a 30d/90d, las cards siguen 7d. Label `(7d)` avisa, no es engaño, pero rompe la regla "todo responde al selector global".

- **File**: `frontend/index.html`
- **Líneas**: 852 (`distanceCounts(d.records, 7)` en buildCards), 1868 (popup overview)

**Decisión previa al fix**: hablar con Nicolás antes. Opciones:
- (i) **Dinamizar**: usar `currentRangeDays` del state global. Pero cards pueden inflarse a 90d con 200+ events → label se vuelve menos útil.
- (ii) **Documentar fijo 7d**: agregar tooltip "siempre últimos 7 días para no inflar tarjetas" y dejar el `7` en el código con comment.

**Steps (camino i, si dinamizar)**:
1. (3 min) Identificar variable global de rango (probablemente `currentRange` o `selectedDays` — revisar con grep).
2. (3 min) Pasar como parámetro a `distanceCounts(d.records, currentRangeDays)` en los 2 callsites.
3. (2 min) Actualizar el label de "(7d)" a `(${currentRangeDays}d)`.
4. (2 min) Smoke: cambiar rango a 30d → cards counts y label se actualizan.

**Steps (camino ii, si documentar)**:
1. (2 min) Cambiar `7` a constante con nombre: `const CARD_COUNT_WINDOW_DAYS = 7;`.
2. (1 min) Tooltip en cards: `title="Conteo de los últimos 7 días, no del rango global"`.

**Acceptance**: o las cards responden al rango y el label refleja, o el comportamiento está documentado en código + tooltip.

**Costo**: 10 min (i) o 5 min (ii).

**Requiere**: confirmación de Nicolás antes de implementar — decisión de diseño UX.

---

## Orden recomendado de implementación

Orden por costo/beneficio (ROI UX visible / esfuerzo):

| # | Bug | Tiempo | Razón orden |
|---|-----|--------|-------------|
| 1 | **Bug 7** marker log10 | 6 min | Trivial, mejora discriminación visual a primera vista en el mapa global. Win inmediato. |
| 2 | **Bug 6** stat Detecciones | 10 min | Trivial, elimina la confusión más visible del panel detalle. |
| 3 | **Bug 11a** distance scatter respeta toggle | 6 min | Cumple promesa del toggle en otro panel. |
| 4 | **Bug 10** sessionStorage toggles | 18 min | Comodidad operador recurrente. Bajo riesgo (3 keys aislados). |
| 5 | **Bug 9** sensor legend propaga | 35 min | Mayor superficie de cambio (5 callsites). Hacer cuando haya foco. |
| 6 | **Bug 8** auto-refresh + timestamp | 20-40 min | Eficiencia (no UX visible). Si If-Modified-Since incluido, lo más riesgoso. |
| 7 | **Bug 11b** cards 7d dinámico | 5-10 min | Requiere decisión de Nicolás. Puede dejarse como issue para después. |

**Lote "quick wins" sugerido** (45 min): Bug 7 + 6 + 11a + 10. Trivial pero alto retorno en confianza.
**Lote "polish toggles + eficiencia"** (otra sesión, 1-1.5 h): Bug 9 + 8.
**Decisión Nicolás**: Bug 11b separado.

---

## Total estimate vs S73 audit estimate

| Estimate | Min | Max |
|---|---|---|
| Audit S73 (BLOQUE_ARRANQUE_S74) | 6 h | 8 h |
| **Este plan (refinado tras re-grep)** | **3.5 h** | **4.5 h** |

Ahorro: el re-grep S73 confirmó que las líneas y la lógica de fix son más simples
que lo estimado en S70 (varios bugs son 1-3 líneas, no refactor). El estimate
audit S73 era conservador para incluir contingencia + TDD frontend. Si se hace
sin tests automatizados (smoke manual), el lote completo cabe en **una sesión
de 4 horas**. Si se quiere TDD jsdom riguroso (instalar harness frontend), sumar
2-3 h al primer bug y luego rinde.

---

## Test strategy

**Hoy no hay test harness frontend en el repo**. Opciones:

- (a) **Smoke manual** con checklists por bug (los doc-checklists arriba). Bajo
  esfuerzo, suficiente para bugs visuales menores.
- (b) **Jsdom + vitest mínimo**: setup ~1 h una sola vez en `tests/frontend/`.
  Tests determinísticos para Bug 6 (stat = filtered.filter count), Bug 9 (sensor
  toggle filtra correctamente), Bug 10 (sessionStorage write/read). Bug 7/8/11
  siguen necesitando smoke visual.
- (c) **Playwright e2e**: otro proyecto del workspace (`Valles volcánicos`,
  `Lago Caburga` según CLAUDE.md raíz Volcanologia) tiene setup Playwright;
  reusable. Costo ~2 h setup + 30 min/bug. Mejor inversión si se planea trabajo
  frontend recurrente.

**Recomendación**: (a) para este lote (3.5-4.5 h ya cabe en ventana de sesión).
Diferir (b)/(c) a sesión específica de infra frontend si los bugs siguen
acumulándose.

---

## Riesgo de NO implementar (resumen de audit S70)

Ninguno afecta corrección científica. Los riesgos son:

1. **Pérdida de confianza operador** (Bug 6, 9): dos cuentas distintas para
   "Detecciones" o toggle que cumple a medias siembran "qué más estará mal" —
   especialmente sensible post-S33.
2. **Discriminación visual baja en overview** (Bug 7): tablero de turno no
   separa Bajo de Moderado a primera vista.
3. **Eficiencia/coste de polling** (Bug 8): 540 fetches/h al CDN para data que
   cambia cada 2 h. No es bug funcional, pero acumula.
4. **Fricción operador recurrente** (Bug 10): reconfigurar toggles cada reload.

Recomendación final: cerrar **lote quick wins (Bug 6+7+10+11a, ~45 min)** en
S74 como parte de cualquier sesión de polish, dejar Bug 8+9 para sesión dedicada.

---

## Cross-refs

- `tasks/frontend_bugs_s67_remaining.md` (audit S70, commit `e778af0`)
- `tasks/BLOQUE_ARRANQUE_S74.md` (backlog actual)
- `docs/HYPOTHESIS_LOG.md` H_S67_DASHBOARD_AUDIT_FINDINGS (origen)
- `CLAUDE.md` — Skill triggers OBLIGATORIO (writing-plans aplicado a este doc)
