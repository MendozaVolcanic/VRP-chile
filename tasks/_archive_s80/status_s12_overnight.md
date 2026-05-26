# S12 Estado nocturno (2026-04-15 → 2026-04-16)

## Reprocesos en curso (11 dispatches, ambos perfiles, ETA ~2h)

Los 11 volcanes Tier A/B/C están reprocesando Jan 1 – Apr 15
con overwrite=true. Incluyen:

### Cambios aplicados en este batch:
1. **E1 (MODIS vent-path ON en mirova_equivalent)**
   - `enable_vent_path_modis: true`
   - `modis_vent_threshold_k: 2.5`
   - `modis_vent_vrp_floor_mw: 0.3`
   - Esperado: +3 TP Lascar, -19 FP (validado vs experimental).

2. **E4 (min_vent_pixels=2 en experimental)**
   - Requiere 2+ pixeles calientes en vent radius para declarar
     detección vent-path.
   - mirova_equivalent mantiene min_vent_pixels=1 (sin cambio).
   - Esperado: FPs experimental ↓↓ (mata 1-pixel noise).

3. **Bug fixes ya incluidos en el código:**
   - `vent_hotspot_lat/lon/dist_km` real del pixel detectado.
   - Geofencing per-volcano con radios MIROVA-OVDAS.
   - `product_version` tagging (nrt/standard).
   - Chart VIIRS375 corregido (usa vrp_mw, no vrp_mir_mw).
   - Floor VRP por sensor (0.02/0.15/0.27).
   - NRT cada 2h con matrix parallelizada.

## Para mañana (Nicolás)

1. **Esperar que los 11 runs terminen** (~2h desde dispatch).
2. **Revisar dashboard volcán por volcán** (Ctrl+Shift+R para cache).
3. **Verificar:**
   - Lascar: ¿aparecen más detecciones MODIS? ¿sin FPs nuevos?
   - Chaitén: ¿pixeles sobre el domo, no spiral artificial?
   - Putana/Irruputuncu: ¿barras fantasma desaparecieron?
   - Tabla: ¿distancias numéricas en vez de "vent"?
4. **Correr auditoría** (ambos perfiles):
   ```
   python experiments/11_strict_audit.py --all
   python experiments/11_strict_audit.py --all --profile experimental
   ```
5. **Comparar E4**: experimental min_vent_pixels=2 vs mirova_equivalent 1.
   Si experimental tiene menos FPs con recall similar → mover a meq.

## Pendientes S13

| Item | Prioridad | Esfuerzo |
|---|---|---|
| Test 1 integrado-ROI (Villarrica 0%) | Alta | 2h prototipo + 2h integración |
| E2: Path C 3σ (Isluga/PP recall) | Media | 30 min tune + reprocess |
| E5: Ratio Tupungatito 0.71 (subestimación) | Baja | 1h análisis |
| Click-to-highlight en tabla → mapa | Media | 1h frontend |
| Filtro fecha custom (rango) | Baja | 30 min frontend |
