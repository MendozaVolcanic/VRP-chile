# Handoff S27 → mañana (2026-04-30 AM)

> Pegá este archivo al iniciar la sesión mañana. Resume estado y deja
> los 3-4 pasos finales para cerrar S27.

## Estado al cierre 2026-04-29 noche

### Trabajo completado

- **T1-T4**: profiles `_mirova_literal` + `_mirova_legacy`, flag
  `ENABLE_EXCLUDE_ZONES` con TDD (5 tests nuevos, suite 192/192), workflows
  A/B y extend.
- **A/B principal 14d** (run [25090815876](https://github.com/MendozaVolcanic/VRP-chile/actions/runs/25090815876)):
  8/8 success. Delta report en `experiments/56_mirova_literal_ab/DELTA_REPORT.md`.
  - **Veredicto: NO APROBADO**.
  - Recall cae 27.6 pp (límite 10 pp).
  - FP_far cae solo 3.5% (esperaba ≥40%).
  - **Ratio mediano de magnitud cae 70× → 1.35×** (mejora drástica, único PASS).
- **Snapshot pre-S27**: tag git `pre-s27-baseline` pusheado + carpeta local
  `data/mirova_equivalent_pre_s27/` (gitignored, 195 MB).
- **Hallazgo persistido** en `~memory/project_s27_mirova_literal_negativo.md`
  con 4 hipótesis arquitecturales (H_S27_1 a H_S27_4) para próximas sesiones.

### Workflow corriendo overnight (independiente de tu PC)

**Run**: [25092057763](https://github.com/MendozaVolcanic/VRP-chile/actions/runs/25092057763)
- 11 Tier A × `_mirova_literal` × **90 días** (2026-01-29 → 2026-04-29).
- Timeouts: 350 min job / 320 min step (margen contra hard cap GitHub 6h).
- Dispatched: 2026-04-29 ~05:09 UTC (≈ 02:09 hora Chile).
- Estimado: **3-6 horas total** → completion entre **05:00 y 08:00 hora Chile**.

**Verificar estado al despertar**:
```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
gh run view 25092057763 -R MendozaVolcanic/VRP-chile --json status,conclusion,jobs --jq '{status, conclusion, jobs: [.jobs[] | "\(.conclusion // .status) \(.name)"]}'
```

Esperado: `status: completed, conclusion: success` con los 11 jobs en
`success`. Si alguno está en `failure`, leer log para descartar bug código:
```bash
gh run view 25092057763 -R MendozaVolcanic/VRP-chile --log-failed | tail -60
```

Patrón conocido: `Network is unreachable` a `urs.earthdata.nasa.gov` =
NASA Earthdata transient outage. Re-launch el workflow:
```bash
gh workflow run reproc-mirova-literal-extend.yml -R MendozaVolcanic/VRP-chile --ref main -f start=2026-01-29 -f end=2026-04-29
```

Solo afecta los volcanes que fallaron (ver matrix), pero el workflow re-procesa los 11 igual. Si querés solo los que fallaron, ajustá la matrix temporal.

## Pasos finales para mañana (cuando workflow esté success)

### 1. Pull data nueva del workflow

```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
git pull origin main
```

Esto trae los 11 JSONs reprocesados a `data/_mirova_literal/`.

### 2. Sobrescribir `data/mirova_equivalent/` con la versión literal

```bash
# Sobrescribir SOLO los 11 Tier A (no afectar los otros 39 volcanes)
for vol in Lascar Lastarria Tupungatito Villarrica PuyehueCordonCaulle Copahue NevadosDeChillan Llaima Chaiten PlanchonPeteroa Isluga; do
  cp "data/_mirova_literal/${vol}.json" "data/mirova_equivalent/${vol}.json"
done
ls -la data/mirova_equivalent/Lascar.json   # debería pesar ~3-5 MB ahora (no 54 MB)
```

### 3. Commit + push

```bash
git add data/mirova_equivalent/
git commit -m "S27 dashboard — sobrescribir 11 Tier A con MIROVA literal 90d

Reproceso _mirova_literal 90d (2026-01-29 -> 2026-04-29) sobrescribe
data/mirova_equivalent/{11 Tier A}.json. Pre-S27 preservado en git tag
pre-s27-baseline + data/mirova_equivalent_pre_s27/ local.

Dashboard ahora muestra resultados clon literal MIROVA puro:
5sigma summit / 10sigma scene Coppola 2016a Tabla 1, sin parches
(sin cap=7K, sin vent-path, sin exclude_zones, sin Test 1, sin
cloud mask BT<260K).

Veredicto A/B 14d (NO APROBADO operacional): recall cae 27.6pp
vs operacional pero ratio mediano de magnitud mejora 70x->1.35x.
Ver memory/project_s27_mirova_literal_negativo.md para hipótesis
arquitecturales (H_S27_1 a H_S27_4) próximas sesiones."

git push origin s15-dev
git checkout main && git pull origin main && git merge s15-dev --no-edit && git push origin main && git checkout s15-dev
```

GitHub Pages publica el dashboard 1-2 min después.

### 4. Cleanup opcional T7

El plan T7 step 2 dice "Borrar profiles A/B (cleanup)". Recomendación:

- **Borrar `_mirova_legacy.yaml`**: ya no se usa, control mirror del operacional.
- **Mantener `_mirova_literal.yaml`**: lo usaríamos para H_S27_1-4 próximas sesiones.

```bash
rm pipeline/profiles/_mirova_legacy.yaml
git add pipeline/profiles/
git commit -m "S27 cleanup — remove _mirova_legacy.yaml (control A/B sin uso futuro)"
git push origin s15-dev
```

## Pendientes para próximas sesiones (S28+)

1. **H_S27_1 — Test 1 summit-only**: A/B `_mirova_literal_test1_summit` con
   `enable_test1_path: true` solo cuando `distance_class=summit`. Esperado:
   recuperar gran parte del recall perdido en Lastarria (12 detecciones).
2. **H_S27_2 — dNTI cooling**: explorar C1 negativo en Path D contextual.
3. **H_S27_3 — Path TIR-only Aveni 2024 RSE**: agregar detección via I05/M15
   para señales sub-pixel.
4. **H_S27_4 — Composición cascada vs OR**: investigar si MIROVA NRT compone
   paths con prioridad/cascada en vez de OR puro.

Detalle completo en `~memory/project_s27_mirova_literal_negativo.md`.

## Comandos útiles si necesitás reabrir el snapshot pre-S27

```bash
# Restaurar mirova_equivalent al estado pre-S27 (años de history operacional):
git checkout pre-s27-baseline -- data/mirova_equivalent/

# O simplemente leer data del backup local:
ls data/mirova_equivalent_pre_s27/   # 50 archivos, 195 MB
```
