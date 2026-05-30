# BLOQUE ARRANQUE S90

**Sesión previa**: S89 (2026-05-30). 3 PRs mergeados a main + Pages deploy success.
100% offline salvo el deploy automático. 1 bug latente real arreglado de raíz.

## §0 — Worktree + primer comando

```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
git fetch origin --prune && git pull --ff-only
cat tasks/BLOQUE_ARRANQUE_S90.md
```

## §1 — Lo que cerró S89 (los 3 frentes pendientes de S88)

- **#5 (PR #248)** — sync `mirova_center` PCC del frontend al KMZ oficial MIROVA
  (`-40.5903,-72.1187`). El frontend medía distancias de PCC desde el viejo
  centroide térmico del lacolito (S48), 1.39 km corrido. Solo PCC estaba stale;
  los otros 10 Tier A no hardcodean center (resuelve también el spawn-task S88).
- **#2 (PR #249)** — `volcanic_features.yaml`: **solo Lazufre** es extension
  genuina (12.1 km del vent Lastarria, inner=3). Las otras 4 sub-features S86
  NO necesitan entrada (Cerro Blanco 4km / Pichi-Llaima 1.3km ya son summit;
  El Agrio = vent; Planchón N sin coord verificable). Coord de Lazufre =
  centroide EMPÍRICO (S85), no GVP — etiquetado como tal. TDD 4 tests nuevos.
- **#3 (PR #250)** — `mirova_confirmed` por-record en frontend (anillo verde
  `#00e676`). **Bug latente arreglado**: `datetime_utc` se parseaba sin `Z` =
  hora local → recall=0 fuera de UTC. Helper `parseUtcMs`. Verificado preview
  (UTC-4): Láscar recall 0→0.87, 433 anillos verdes. Ver
  [memory/reference_frontend_datetime_utc_tz_bug.md].
- **UX (decisión Nicolás)**: extensions **ocultas por defecto** (sin cambio).

## §2 — Pendientes S90 (NO bloqueantes, ninguno urgente)

1. **Coord GVP catalogada de Planchón N** — sigue sin coord verificada distinta
   del centro del complejo PP. Regla S88: no inventar. Tarea de investigación;
   si no aparece coord catalogada, queda como TODO permanente y está bien.
2. **Upgrade coords empíricas → GVP catalogadas** (opcional): Lazufre, lacolito
   PCC usan centroides empíricos. Si se consiguen coords GVP de catálogo,
   reemplazar (mismo estándar, mejor fuente). No urgente.
3. **Verificación visual de `geo_class=extension` (naranja)**: requiere que el
   NRT cron pueble Lazufre con geo_class real (empieza el próximo cron tras
   PR #249). En S89 se verificó el render de `mirova_confirmed` (anillo verde)
   pero NO el naranja de extension (no había data extension cargada). Verificar
   con preview cuando haya un cluster Lazufre etiquetado.
4. **(opcional) Migrar los `new Date(r.datetime_utc)` de los filtros de ventana
   a `parseUtcMs`** si alguna vez se comparan contra tiempos MIROVA. Hoy son
   ours-only contra `Date.now()`, internamente consistentes — NO tocados (scope).

## §3 — Escudo anti-drift (vigente)

1. NO cambiar criterio de selección (vent_anchored validado S87/S88).
2. NO gate `t_bg<260K` en ninguna forma (refutado S86).
3. NO huella/G1/exclude_zones/gate-intra-radio nuevo (A55).
4. `geo_class` y `mirova_confirmed` son ETIQUETAS descriptivas — NO filtran ni
   cambian detección/VRP. Mantener así.

## §4 — Reglas vinculantes activas

A45 (tag + OK antes de pipeline), A47, A52, A54, A55, A18, M1, M2, M8.
Integridad (S88): números/afirmaciones solo del output verificado del script.
Verificación frontend: cargar en preview en navegador no-UTC, no solo
`node --check` (lección S89 bug TZ).

## §5 — Comunicación con Nicolás

Geólogo: fenómeno físico → mecanismo pipeline → fórmula al final.
