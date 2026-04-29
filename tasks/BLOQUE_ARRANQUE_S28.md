# Bloque de arranque S28

> **Pegar este bloque al inicio de la próxima sesión.**

---

## CHECKLIST OBLIGATORIO ANTES DE ACTUAR

**Antes de tocar `pipeline/` o proponer cambios metodológicos**:

1. Leer [docs/MISSION.md](../docs/MISSION.md) — las 3 preguntas vinculantes.
2. Leer [docs/MIROVA_DIVERGENCES.md](../docs/MIROVA_DIVERGENCES.md) — D1-D5 documentadas.
3. Si lo que voy a hacer **no pasa las 3 preguntas → anotarlo en backlog y NO HACERLO**.

Si Nicolás pide algo que no pasa, contestar explícitamente:
> "Esto sería divergencia metodológica — no cumple la regla MIROVA literal.
> Lo anoto en `tasks/backlog_*.md`. ¿Querés excepción explícita en MISSION.md?"

## Estado al cierre S27 (2026-04-29 ~16:00)

### Lo logrado
- ✅ Plan MIROVA literal puro ejecutado (T1-T7).
- ✅ A/B 14d → NO APROBADO (recall −27.6pp); pero ratio mediano 70× → 1.35× ✓.
- ✅ Reproc 11×90d completado en 2 rondas (1ra sin clustering, 2da con clustering).
- ✅ Dashboard sobrescrito con 10 Tier A literal puro 90d (NdC pendiente).
- ✅ Frontend toggle "Solo principal vs Todos los pixels" — alineado con
  convención MIROVA (1 marker/record).
- ✅ Cluster aggregation implementado (`pipeline/clustering.py` + 10 tests).
  Cierra D1 a nivel data layer.
- ✅ Snapshot pre-S27 preservado (tag `pre-s27-baseline` + carpeta local).
- ✅ Misión vinculante escrita en MISSION.md + memoria + CLAUDE.md +
  este bloque (4 puntos de redundancia anti-scope-creep).

### Pendientes inmediatos (push final)

Ver `tasks/HANDOFF_S28_MORNING.md` para los comandos exactos. Resumen:

```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
git pull origin main
# Sobrescribir 10 Tier A con _mirova_literal/ (último reproc 90d con clustering)
for vol in Lascar Lastarria Tupungatito Villarrica PuyehueCordonCaulle Copahue Llaima Chaiten PlanchonPeteroa Isluga; do
  cp "data/_mirova_literal/${vol}.json" "data/mirova_equivalent/${vol}.json"
done
git add data/mirova_equivalent/
git commit -m "S27 dashboard final - 10 Tier A literal 90d con cluster aggregation"
git push origin s15-dev
git checkout main && git pull origin main && git merge s15-dev --no-edit && git push origin main && git checkout s15-dev
```

NdC sigue con data legacy mixta (4 fallos NASA Earthdata transient — fallback
aceptado).

### Hallazgos de auditoría visual (S27, persistidos en MIROVA_DIVERGENCES.md)

- **H1** D4 confirmado: Lastarria/Planchón sub-detectan, Llaima/Copahue
  sobre-detectan.
- **H2** Llaima 78 detecciones summit vs 0 alertas reales MIROVA — filtro
  automático MIROVA que no replicamos (probable lago Conguillío persistente).
- **H3** NdC 16 vent-path markers — residual pre-S27 (se limpia con reproc
  final).
- **H4** Toggle "Solo cráter" + clasificación summit/far funcionan ✓.

### Hipótesis arquitecturales abiertas (S28+)

Solo si acercan a clon fiel MIROVA (ver memoria
`project_s27_mirova_literal_negativo.md`):

- **H_S27_1** Test 1 summit-only más agresivo (Coppola 2015 §2.2 Eq.1).
- **H_S27_2** dNTI con C1 negativo (cooling).
- **H_S27_3** path TIR-only Aveni 2024 RSE TIRVolcH.
- **H_S27_4** composición paths cascada vs OR.
- **H_S27_5 RECHAZADA** subir `inner_radius_km` (es parche).

### Backlog S28+ explícito

`tasks/backlog_s27.md`:
- **B**: re-scrape Mirova-v1 cubriendo gap ~30% VIIRS del CSV consolidado.
  Solo si acerca a clon fiel.
- **C**: investigación D4 sub-pixel summit Lastarria/Planchón. Solo si
  acerca a clon fiel.
- **7 golden tests** desfasados con metodología literal. Reescribir en S28.
- **NdC retry**: si NASA Earthdata recupera, lanzar
  `reproc-ndc-retry.yml` para completar el 11/11.

## Verificación 30-segundos al arranque S28

```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
git fetch origin && git status --branch --short
# Expected: ## s15-dev...origin/s15-dev limpio o cerca

pytest 2>&1 | tail -3
# Expected: 193 passed (10 cluster_hotspots ✓), 7 goldens en backlog

gh run list -R MendozaVolcanic/VRP-chile --workflow=reproc-mirova-literal-extend.yml -L 1 --json conclusion --jq '.[0].conclusion'
# Expected: success (run 25110402836)
```

## Recordatorios al arrancar S28

1. **Leer en este orden** (top-to-bottom):
   - Este bloque.
   - `docs/MISSION.md` (regla vinculante).
   - `docs/MIROVA_DIVERGENCES.md` (estado divergencias).
   - `~memory/MEMORY.md` (índice + feedback misión).
   - `tasks/backlog_s27.md` (pendientes con condición "solo si acerca a clon").

2. **NO INVENTAR FEATURES**. Si una idea suena bien, primero pasar por las
   3 preguntas. Si Nicolás propone una idea que no pasa, decirle.

3. **NO REINTRODUCIR PARCHES BORRADOS** (cap=7K, vent-path, exclude_zones,
   Reglas D, cloud mask BT<260K, pisos VRP por sensor). Lista completa en
   `~memory/project_s26_parches_no_mirova.md`.

4. **Persistencia in-vivo**: cuando descubras un hallazgo, persistirlo
   INMEDIATAMENTE en `docs/MIROVA_DIVERGENCES.md` o `~memory/`. La sesión
   puede cortarse.

5. **Auditoría obligatoria al cierre**: revisar `git diff` y verificar que
   cada cambio en `pipeline/` cumple las 3 preguntas. Si no, revertir o
   documentar excepción explícita en `docs/MISSION.md`.

## Resumen 2 líneas para pegar al primer prompt S28

> Cierre S27: A/B literal NO APROBADO (recall -27.6pp pero magnitud 70x→1.35x).
> Dashboard 10/11 Tier A con literal puro 90d + cluster aggregation. Misión
> vinculante en `docs/MISSION.md` (3 preguntas). Lee `tasks/BLOQUE_ARRANQUE_S28.md`.
