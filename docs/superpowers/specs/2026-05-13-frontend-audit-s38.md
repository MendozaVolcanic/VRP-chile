# Audit profundo frontend post-S38 + filtro "Solo post-S38" (S38 cierre)

**Fecha**: 2026-05-13 post adopción operacional vent_anchored + H8
**Driver**: usuario pidió ver solo datos del operacional actual (sin
contaminación de iteraciones pasadas con primary_cluster equivocado) +
audit dashboard para limpiar bugs de iteraciones anteriores.

---

## Implementación filtro "🆕 Solo post-S38"

### Comportamiento

Toggle nuevo en `controls` que cuando activo, filtra `records.datetime_utc
>= "2026-05-13 03:00"` (cutoff de adopción S38, PR #28 mergeado 03:05 GMT).

- **Default**: OFF (muestra todo histórico, comportamiento previo).
- **Activado**: oculta records procesados con vrp_max strategy (Salar
  lejano como primary, etc.).
- **Persistencia**: `sessionStorage` key `vrp_post_s38_only`. Compartido
  entre `index.html` y `diario.html` para sincronización.

### Archivos modificados

1. **`frontend/index.html`**:
   - Estado: `let postS38Only`, `const S38_ADOPTION_CUTOFF_UTC`
   - Helper: `applyS38Filter(records)`
   - 5 funciones internas aplican filtro al inicio: `filterDays`,
     `latestVRP`, `latestSensors`, `lastEventTime`, `distanceCounts`
   - UI button `#btn-post-s38` antes del toggle distancia
   - Event handler con re-render completo

2. **`frontend/diario.html`**:
   - Mismo patrón con `sessionStorage` key compartido
   - Toggle dispara `location.reload()` (consistente con otros toggles del diario)

### Por qué este enfoque (vs alternativas)

| Approach | Pros | Contras | Decisión |
|---|---|---|---|
| Filtro datetime cutoff | Simple, reversible, no toca data | Si NRT pre-S38 reprocesado después con flags ON, filtra incorrectamente | ✅ ELEGIDO |
| Marcar records con flag schema | Más robusto | Requiere cambio backend store.py + reproc todo | ❌ Más invasivo |
| Borrar histórico pre-S38 | Solución radical | Pérdida data, no reversible | ❌ Destructivo |

---

## Audit findings frontend (no arreglados — documentar)

Audit profundo de `frontend/index.html` (2044 → 2091 lineas post-cambios)
e `index.html`. Identifico patrones acumulados de iteraciones S11-S37 sin
romper funcionalidad existente.

### A. Fallbacks legacy seguros (mantener)

Múltiples lugares con cadenas `r.vrp_mw ?? r.vrp_mir_mw ?? 0`:
- Líneas 635, 671, 681, 718, 981, 1000
- `vrp_mir_mw` fue normalizado a `vrp_mw` por `store.py` desde S22 (commit `f42f69b`).
- El fallback NO causa bugs (suma de `null` con OR es safe).
- Records muy viejos (pre-S22) podrían no tener `vrp_mw`, solo `vrp_mir_mw`.
- **Decisión**: mantener. Eliminar puede romper records históricos.

### B. Cadena `final_hotspot_dist_km` / `vent_hotspot_dist_km`

Línea 1018-1021:
```js
const dist = r.hotspot_dist_km
  ?? r.final_hotspot_dist_km
  ?? r.vent_hotspot_dist_km;
```
Campos S14 que existen en records con schema completo. Post-S22.1 `process_*`
los expone con paridad. Records muy viejos solo tenían `vent_hotspot_dist_km`.

**Decisión**: mantener. Es código defensivo apropiado.

### C. `mirovaEqVrp` con validación pc.centroid_dist_km

Función central líneas 632-644. Bug fix S33 integrado (validar
`pc.centroid_dist_km > innerKm`).

**Post-S38**: con vent_anchored adoptado, `primary_cluster` SIEMPRE está
cerca del vent en records nuevos. La validación `pc.centroid_dist_km > innerKm`
es redundante para records nuevos pero **sigue siendo crítica para records
legacy pre-S38** (que tienen primary = Salar/lago lejano).

**Decisión**: mantener. Cuando filtro "🆕 Solo post-S38" está activo, la
validación de safety queda inerte. Cuando está apagado, sigue protegiendo
records legacy.

### D. `isSummitDetection` lógica heterogénea

Líneas 652-660. 4 ramas (distance_class summit / far / legacy vent /
default). Con vent_anchored, `distance_class` debería siempre ser "summit"
para records con cluster cercano. Pero la asignación de `distance_class`
ocurre **antes** del clustering vent-anchored en process_*.py — está basada
en `final_hotspot_*` (Test 1 path), no en `primary_cluster.centroid_dist_km`.

**Implicación**: existe inconsistencia potencial: record nuevo con
`distance_class="far"` (final_hotspot vía Test 1 ya lejano) pero
`primary_cluster.centroid_dist_km` dentro del inner (porque vent_anchored
lo eligió). En este caso `isSummitDetection` retorna `false` pero
`mirovaEqVrp` retorna pc.vrp_mw correcto. Trade-off conocido.

**Decisión**: **mantener actual** para evitar romper records legacy.
Investigar como mejora S39+ si hay casos reportados.

### E. `distanceCounts` window hardcoded 7 días

Línea 737, parámetro default 7. Se llama con `7` en buildCards y
buildOverviewMap. No es bug — es un default razonable que se podría
exponer en UI si el usuario quiere otra ventana. **Decisión**: mantener.

### F. `latestVRP` window hardcoded 48h

Línea 666. Define "48h max" mostrado en cada card. Convención S14+.
No es bug. **Decisión**: mantener.

### G. NO encontrados (clean):

- ✅ Cero `console.log` / `debugger` residuales
- ✅ Cero `XMLHttpRequest` legacy (todo `fetch`)
- ✅ Cero variables `var` (todas `let`/`const`)
- ✅ Ningún campo schema que no exista en records actuales

---

## Recomendaciones S39+ (no implementadas)

1. **Frontend toggle dual primary vs sum_active**: cuando se adopte H_D8_5
   sum reporting (rechazado S37 actualmente), agregar UI para alternar entre
   `primary_cluster.vrp_mw` y `vrp_mw_sum_active`. No urgente.

2. **Investigar inconsistencia `distance_class` vs `primary_cluster`**:
   diferencia entre el campo `distance_class` (basado en final_hotspot) y
   la realidad post-vent_anchored. Si hay casos donde difieren mucho, podría
   reasignar `distance_class` en post-processing.

3. **Cleanup fallbacks `vrp_mir_mw`**: en S40+ cuando confirmemos que no hay
   records pre-S22 en operacional (probablemente ya hace tiempo), podemos
   simplificar las cadenas. No urgente.

4. **Default `postS38Only=true` en próximas semanas**: cuando la mayoría del
   histórico operacional sea post-S38, podemos cambiar el default a ON.
   Mientras tanto, OFF preserva continuidad visual.

---

## Verificación

- ✅ Smoke check: `applyS38Filter` 6x en index.html (1 def + 5 usages)
- ✅ Smoke check: `applyS38Filter` 2x en diario.html (1 def + 1 usage)
- ✅ Sessionstorage key compartido entre archivos
- ⏳ Test visual en GitHub Pages publicado (Nicolás verifica post-deploy)

---

## Test plan post-deploy

Cuando Pages publique:

1. **Test ON-OFF**: activar toggle, verificar que records pre-2026-05-13 desaparecen
2. **Persistencia**: refresh página, toggle sigue activo
3. **Cross-page**: activar en index → ir a diario → verificar que también está activo
4. **Cards overview**: si toggle ON y volcán solo tiene records pre-S38, mostrar
   "sin datos" en la card
5. **Charts**: confirmar timeline chart no muestra puntos pre-cutoff
6. **Tabla detail**: confirmar tabla no muestra records pre-cutoff
7. **Mapa**: confirmar markers solo de records post-cutoff
