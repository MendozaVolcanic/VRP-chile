# Frontend bugs S67 remaining (S70-2 T3)

> Lista priorizada de los 6 bugs frontend menores (Bug 6-11) que sobrevivieron al fix S68 P0.
> Análisis solamente — implementación en S70-3+ o sesión dedicada de polish UX.
> **NO se modificó `frontend/`** en esta tarea.

---

## Fuente

### `docs/HYPOTHESIS_LOG.md` (H_S67_DASHBOARD_AUDIT_FINDINGS, líneas 138-188)

> ### Hallazgo 2: 11 inconsistencias frontend identificadas
>
> **Top 5 críticas**:
> 1. VRE chart `buildVREData` NO usa `mirovaEqVrp` → diverge de stat box VRE
> 2. MIROVA Comparison chart NO valida `pc.centroid_dist_km > innerKm` → potencial regresión bug S33
> 3. Toggle "Solo cráter" parcial: NO se propaga a VRE/Distance/MIROVA Comp/overview hotspot/cards counts
> 4. About modal desactualizado (cita S48 F1 98.3%, no menciona kernel-bg adoptions S61-S65)
> 5. No label visual distinguiendo vols con kernel-bg adoptado vs sin fix
>
> **Otros 6** (Bug 6-11): stat "Detecciones" ≠ tabla events count, fallback legacy sin distance check,
> marker size lineal (no log), hotspot layer stale 5min auto-refresh, sensor legend toggle parcial,
> toggles no persisten sessionStorage.

### `tasks/BLOQUE_ARRANQUE_S70.md` (sección 3 punto 6, líneas 137-145)

> **6. Frontend bugs menores 6-11** (audit S67):
>
> - Stat "Detecciones" vs tabla events count divergen
> - Overview marker size lineal (cambiar a log)
> - Hotspot layer auto-refresh 5min stale
> - Sensor legend toggle parcial
> - Toggles no persisten en sessionStorage
> - Distance scatter no respeta toggle far
> - Cards distance counts fijos 7d

**Nota**: BLOQUE_ARRANQUE lista 7 bullets, pero HYPOTHESIS_LOG dice "Otros 6". Uno
solapa: "fallback legacy sin distance check" (HYPOTHESIS_LOG) ≈ "Distance scatter no
respeta toggle far" (BLOQUE) — los trato como uno con dos facetas. Resultado: 6 bugs.

---

## Lista priorizada

### Bug 6: Stat "Detecciones" diverge de la tabla / VRE / chart

- **Descripción**: el stat box "Detecciones" en el panel de detalle muestra
  `allVrp.length` (todos los granules con algún VRP), pero la tabla NRT, el chart
  principal y la stat "Promedio activo" filtran por `eqVrp(r) > 0` (la función
  unificada post-S68). Resultado: el usuario ve "Detecciones: 47 granules" pero la
  tabla bajo solo lista 12 filas y eso es desconcertante.
- **File:line**: `frontend/index.html:939` (`addStat("Detecciones", String(allVrp.length), "granules");`).
- **Severidad UX**: **Media** — confunde al operador porque dos paneles del mismo
  detalle muestran cuentas distintas para el mismo período. Lo asociaría a un bug de
  filtrado.
- **Causa probable**: la stat se calcula sobre `allVrp` (variable temprana, pre-filtro
  distance/discard) mientras el resto del panel ya se movió al pipeline `eqVrp(r)`
  unificado del S68. Quedó residuo pre-S68.
- **Fix propuesto**: cambiar `allVrp.length` por `filtered.filter(r => eqVrp(r) > 0).length`
  (o `filtered.length` si el intento era "total granules procesados") y revisar la
  etiqueta — si la intención del stat es "detecciones útiles" usar el primero, si es
  "total granules" usar el segundo y renombrar.
- **Costo estimado**: trivial (1 línea + verificación visual con un volcán de prueba).

---

### Bug 7: Overview marker size lineal en VRP (debería ser log)

- **Descripción**: en el mapa overview (los 45 volcanes globales), el radio del
  marker crece linealmente con VRP (`7 + vrp * 2`). Esto deja volcanes con 0.5 MW
  casi indistinguibles del baseline (radio ~8 px) y volcanes con 30-80 MW saturando
  el cap (radio = 16 px). Pierde resolución visual justo donde discrimina actividad
  real (rango 0.5-10 MW = "Bajo/Moderado" en escala MIROVA).
- **File:line**: `frontend/index.html:1844` (`const size = lv.key === "nd" ? 6 : Math.max(7, Math.min(16, 7 + vrp * 2));`).
- **Severidad UX**: **Media** — el detail panel y el distance scatter ya usan log10
  (líneas 1314, 1570, 1789), entonces hay inconsistencia interna además de mala
  discriminación. Operador no distingue 1 MW de 5 MW a primera vista.
- **Causa probable**: este marker se diseñó S6-S8 antes de adoptar log10 como
  convención. Quedó sin migrar.
- **Fix propuesto**: reemplazar la fórmula por la convención local
  `Math.max(7, Math.min(16, 7 + Math.log10(Math.max(vrp, 0.01)) * 4))` (o
  consistente con la usada en el detail panel, línea 1789, que ya está validada
  para rango 0.01-100 MW).
- **Costo estimado**: trivial (1 línea + revisión visual del mapa overview con un
  volcán al menos en cada nivel de alerta).

---

### Bug 8: Hotspot layer / auto-refresh stale 5 min

- **Descripción**: el botón "🔥 Anomalías" (overview map hotspot layer) se refresca
  via `setInterval` cada 5 min junto con todo el dashboard (línea 2045). Pero el
  cron NRT corre cada 2h (no cada 5 min), y el TIF archive scraper corre cada 5 min
  en GH Actions. Resultado: el usuario ve "datos refrescados hace 30 s" pero los TIF
  más recientes ya tienen 4 min y los JSON del pipeline cron tienen hasta 2 h. No
  hay timestamp visible de cuán fresco es cada layer. Además 5 min de polling sobre
  los 9 Tier A + 45 vols genera 540 fetches/h al CDN, exceso para data que cambia
  cada 2h.
- **File:line**: `frontend/index.html:2044-2052` (setInterval 5*60*1000 fetcheando
  todos los volcanes).
- **Severidad UX**: **Baja** — no es bug funcional, es eficiencia + transparencia.
  El operador no se confunde activamente, pero gasta cuota fetch innecesaria.
- **Causa probable**: 5 min fue el período elegido S6 cuando solo había overview y
  cron era horario. Quedó sin recalibrar tras pasar a cron 2h + 9 Tier A + 45 vols.
- **Fix propuesto**:
  1. Subir intervalo a 15-30 min (alineado con cron 2h: refresh 4-8× por ciclo
     captura cualquier cambio).
  2. Agregar timestamp "última actualización: HH:MM UTC" visible cerca del clock.
  3. Conditional fetch con `If-Modified-Since` (GitHub Pages soporta) para no
     re-bajar JSON sin cambios — reduce ancho de banda 90%.
- **Costo estimado**: 15 min para (1)+(2); 1 h para (3) si querés hacer todo bien.

---

### Bug 9: Sensor legend toggle parcial

- **Descripción**: el sensor legend (top-right) tiene click handlers que togglean
  `sensorVisible[s.key]`, hacen `item.classList.toggle("dim")`, y llaman
  `renderDetail()` (línea 1683-1687). Esto redibuja el chart principal correctamente,
  PERO **no afecta**: distance scatter (línea 1570 — los puntos siguen apareciendo
  con color del sensor "oculto"), VRE chart (línea 1602 — `buildVREData` no filtra
  por sensor), MIROVA comparison chart, overview hotspot layer, ni cards counts.
  Resultado: si el usuario oculta MODIS porque sabe que tiene over-detection (caso
  S67/S69), igual lo ve en todos los otros gráficos.
- **File:line**: `frontend/index.html:1683-1687` (handler) +
  callsites `buildDistanceData` (1443), `buildVREData` (1456), `buildComparisonData`
  (1469).
- **Severidad UX**: **Media** — el toggle promete una acción pero la cumple solo
  parcialmente. Confunde porque "creo que oculté MODIS pero sigo viendo sus puntos".
- **Causa probable**: el toggle se implementó solo para el chart principal en S6.
  Los chart secundarios y mapas se agregaron después (S12-S20) sin tocar el toggle.
- **Fix propuesto**: agregar filtro `sensorVisible[r.sensor] !== false` al inicio
  del loop de `buildDistanceData`, `buildVREData`, `buildComparisonData`, y al
  `forEach` de overview/hotspot layer. Re-render todos los gráficos secundarios en
  el handler.
- **Costo estimado**: 30-45 min (4-5 callsites + verificación que el toggle se
  propaga visualmente correcto en cada uno).

---

### Bug 10: Toggles no persisten en sessionStorage

- **Descripción**: hay varios toggles en el dashboard (Solo cráter, sensor legend,
  hotspot layer, "todos los pixels") que se pierden con cada reload. El operador
  que tiene una configuración favorita ("MODIS oculto, solo cráter, hotspot layer
  on") tiene que reconfigurarla cada vez. El comentario en línea 588 menciona que
  sí hay un patrón de sessionStorage para `vrp_post_s38_only` (y línea 1981 lo
  limpia explícitamente), entonces la convención existe pero no se aplicó a los
  otros toggles.
- **File:line**: `frontend/index.html` varios: línea 577 (`includeFarDistance`),
  línea ~1684 (`sensorVisible`), línea 1949 (`hotspot-layer-btn`). Más cualquier
  otro toggle global.
- **Severidad UX**: **Baja-Media** — no es funcional, es comodidad. Pero para
  operadores SERNAGEOMIN que usan el dashboard varias veces al día, suma.
- **Causa probable**: el patrón sessionStorage existió temporalmente para un flag
  específico S38 y se limpió. No se generalizó como sistema.
- **Fix propuesto**: definir una mini-función `persistedToggle(key, default)` que
  encapsule lectura/escritura sessionStorage, y reescribir las 3-4 declaraciones de
  toggles globales para usarla. Ej:
  ```js
  let includeFarDistance = persistedToggle("vrp_include_far", false);
  // al toggle: includeFarDistance = !includeFarDistance; sessionStorage.setItem("vrp_include_far", String(includeFarDistance));
  ```
- **Costo estimado**: 45 min (helper + 3-4 toggles + verificación que ningún flag
  se confunde entre reloads).

---

### Bug 11: Distance scatter no respeta toggle "Solo cráter" + cards distance counts fijos 7d

- **Descripción** (doble): este bullet combina dos issues relacionados de la lista
  original.
  - **(a) Distance scatter**: cuando el usuario activa "Solo cráter" (que filtra
    `pc.centroid_dist_km <= innerKm`), el scatter sigue mostrando puntos far. La
    función `buildDistanceData` (línea 1443-1453) no consulta `includeFarDistance`
    ni `isSummitDetection(r)` — todos los records con VRP > 0 entran. El stat box
    se ajusta pero el gráfico no.
  - **(b) Cards distance counts**: el conteo "🎯 Cráter: N · 📍 Lejanas: M" en cada
    card del grid (línea 836) y en el popup del overview (línea 1852) está
    hardcodeado en 7d (`distanceCounts(d.records, 7)`). Si el usuario cambia el
    rango de tiempo a 30d o 90d arriba, los conteos siguen siendo "(7d)". Está
    declarado explícito en el label ("(7d)"), entonces no es un bug oculto, pero
    es inconsistente con el resto del dashboard que sí responde al selector de
    rango.
- **File:line**: 
  - (a) `frontend/index.html:1443-1453` (`buildDistanceData`).
  - (b) `frontend/index.html:836` (`distanceCounts(d.records, 7)` en cards),
    `frontend/index.html:1852` (idem en popup overview).
- **Severidad UX**: 
  - (a) **Media** — toggle promete acción y no la cumple (mismo patrón Bug 9).
  - (b) **Baja** — el "(7d)" label avisa, pero rompe la regla de "todo escucha al
    selector global de rango".
- **Causa probable**: 
  - (a) `buildDistanceData` quedó pre-S36 cuando el toggle se introdujo.
  - (b) Diseño S18 que fijó 7d para que las tarjetas no se inflen en períodos
    largos. Nunca se revisó si convenía dinámico.
- **Fix propuesto**: 
  - (a) Filtrar dentro de `buildDistanceData`:
    `if (!includeFarDistance && !isSummitDetection(r)) continue;`
  - (b) Si querés dinamizar: pasar el rango actual desde el state global como
    parámetro a `distanceCounts(d.records, currentRangeDays)` y actualizar el
    label. Si la decisión es "queda 7d para no inflar tarjetas en 90d", explicitar
    en docs y mover el comentario al código.
- **Costo estimado**: 15 min para (a); 15 min para (b) si se mantiene 7d hard (solo
  documentar); 30 min si se dinamiza.

---

## Orden recomendado de fix (S70-3+)

Ordenado por costo/beneficio (UX visible / esfuerzo):

1. **Bug 7** (overview marker size lineal → log): trivial, mejora discriminación
   visual del mapa global de los 45 volcanes para todo operador. **Empezar aquí.**
2. **Bug 11a** (distance scatter respeta toggle far): 15 min, cumple promesa del
   toggle "Solo cráter" en otro panel.
3. **Bug 6** (stat Detecciones inconsistente con tabla): trivial, elimina la
   confusión más visible del panel detalle.
4. **Bug 9** (sensor legend toggle parcial): 30-45 min, propaga el toggle a 4
   panels secundarios — alto retorno en consistencia.
5. **Bug 10** (toggles no persisten): 45 min, comodidad para uso recurrente.
6. **Bug 8** (auto-refresh 5min stale + sin timestamp): 15 min (a)+(b), 1 h si se
   agrega If-Modified-Since. Hacer al final porque toca lógica de fetching que es
   más arriesgada y el beneficio es eficiencia, no UX visible.
7. **Bug 11b** (cards distance counts 7d): si llegás hasta acá, decidir si
   dinamizar o solo documentar la decisión.

**Lote sugerido para una sesión dedicada**: Bug 6+7+11a en ~45 min como "quick wins
UX". Bug 9+10+8 en otra sesión de 2-3 h como "polish toggles + eficiencia".

---

## Riesgo de NO fixearlos

Estos 6 bugs son **menores y no afectan la corrección científica del dashboard**.
Los números del VRP, la magnitud de las anomalías, la clasificación summit/far, los
records adoptados/rechazados, y la comparación con MIROVA — todo eso es correcto
post-S68 P0. El operador SERNAGEOMIN puede usar el dashboard live hoy y tomar
decisiones correctas.

Lo que se acumula si no se resuelven:
- **Pérdida de confianza del operador**: ver dos conteos distintos para "Detecciones"
  (Bug 6), o un toggle que solo afecta un gráfico (Bug 9), planta la duda "qué más
  estará mostrando mal" — y los operadores SERNAGEOMIN ya están en modo "verificar
  todo dos veces" tras S33.
- **Discriminación visual baja en overview map** (Bug 7): el dashboard a primera
  vista no separa Bajo de Moderado, lo que reduce su valor como "tablero de turno".
- **Inconsistencia entre paneles**: cada bug menor que queda es una caja oscura que
  exige documentar workaround ("ignorá Detecciones, contá la tabla"). Estos
  workarounds tienden a perderse en handoffs.

**Recomendación**: liquidar Bug 6+7+11a en la próxima sesión de polish (45 min de
trabajo, mejora UX visible inmediata). Bug 8-10 pueden esperar a una sesión
dedicada cuando haya tiempo de TDD frontend (no es imposible — hay setup Playwright
en el repo de otros proyectos del workspace para reusar).
