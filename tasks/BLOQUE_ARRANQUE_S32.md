# Bloque de arranque S32

> Pegar al inicio de la próxima sesión. Resumen estado al cierre S31+
> (2026-05-03 madrugada) + plan de trabajo + cosas a probar.

---

## CHECKLIST OBLIGATORIO ANTES DE ACTUAR

1. Leer [docs/MISSION.md](../docs/MISSION.md) — las 3 preguntas vinculantes.
2. Leer [docs/MIROVA_DIVERGENCES.md](../docs/MIROVA_DIVERGENCES.md) — D1-D5 estado.
3. Leer [docs/MIROVA_IMG_READING_GUIDE.md](../docs/MIROVA_IMG_READING_GUIDE.md) — cómo NO equivocarse leyendo plots online.
4. Leer milestone reciente: `~memory/milestone_s31_plus_frontier.md`.

Si una propuesta no pasa las 3 preguntas → anotarla en `tasks/backlog_*.md` y NO hacerla.

## Estado al cierre S31+ (2026-05-03 ~05:30 hora Chile)

### Lo logrado en sesión

| Métrica | Pre-sesión | **Post-sesión** | Δ |
|---|---:|---:|---:|
| Recall global | 75.4% | **83.5%** | **+8.1pp** |
| Ratio mediano global | 6-14× típico | **3.72×** | drástica mejora |
| Lascar recall | 57% | **68%** | +11pp |
| Lastarria ratio | 6.3× | **14.5×** | (subió por bug intermedio, mejoró desde 21.8 con S31+) |
| Volcanes a 100% recall | 4 | **5** (Lastarria/Planchón/Chaitén/Villarrica/Copahue) | +1 |

### Cambios committeados

- `pipeline/process_modis.py` — cascada Regla D Test 1-priority (S30) + VRP recompute + cluster_hotspots 8-conn primary_cluster (S31+).
- `pipeline/process_viirs.py` — primary_cluster fix con cluster_hotspots 8-conn (S31+).
- `pipeline/process_viirs_mod.py` — cascada Test 1 completa que faltaba desde S28 + primary_cluster fix (S30+ y S31+).
- `docs/MIROVA_IMG_READING_GUIDE.md` — guía leer plots MIROVA web sin errores.

### Tags git

- `s31-plus-frontier` (commit 07fd01d) — referencia del estado actual.
- `s29-frontier` (commit 7bff03c) — milestone S29 anterior.
- `pre-s27-baseline` (commit e02c768) — operacional pre-S27.

### Frontend (sin cambios desde S29)

- 7 fixes críticos visuales aplicados S29 (commit 12384af).
- 11 bugs LOW pendientes en backlog `tasks/backlog_s27.md`.

## ⚠️ NRT cron — REVISAR PRIMERA COSA EN S32

**Estado**: 9 de últimos 10 runs en `failure`. Solo 1 success (2026-05-03 18:58).

```bash
gh run list -R MendozaVolcanic/VRP-chile --workflow=nrt.yml -L 10 \
  --json status,conclusion,createdAt --jq '.[] | "\(.createdAt[:19]) \(.conclusion // .status)"'
```

**Hipótesis a investigar (en orden)**:

1. **NASA Earthdata transient** persistente → re-scrape Mirova-v1 logs.
2. **Cambio API/rate-limit** NASA Earthdata.
3. **Bug código** introducido en commits recientes que rompe NRT.
4. **Conflictos git** entre cron y reprocs simultáneos.

**Acción primera S32**: leer logs de los últimos 3 fallos NRT:
```bash
last_failed=$(gh run list -R MendozaVolcanic/VRP-chile --workflow=nrt.yml -L 1 --status failure --json databaseId --jq '.[0].databaseId')
gh run view $last_failed -R MendozaVolcanic/VRP-chile --log-failed | tail -60
```

Si es Earthdata transient simple, re-launch manual y monitorear. Si es bug, fix.

## Pendientes priorizados S32+

### Prioridad 1 — NRT cron fallando (URGENTE)

Sin cron NRT funcionando, no hay data nueva post-2026-04-29. El dashboard
queda congelado al milestone S31+. Investigar y arreglar antes de seguir.

### Prioridad 2 — Magnitud residual ratio 3.72× global

**Síntoma**: en Lastarria (14.5×), Villarrica (41.5×), Planchón (18.5×),
nuestro VRP del cluster contiguo principal sigue siendo ~10-40× MIROVA.

**Hipótesis a probar**:

a) **MIROVA aplica threshold adicional pixel-por-pixel sobre Test 1 mask**.
   Test 1 dispara como integrated → trigger de evento. Pero después
   reporta solo pixels con BT > t_bg + N·σ adicional. Verificar bajando
   1 granule Lastarria con detección MIROVA "Muy Bajo" 0.11 MW y comparar
   pixel por pixel.

b) **MIROVA usa min_pixel_vrp para pixel reporting** (no solo para record).
   Cada pixel debe contribuir >X MW para entrar al cluster reportado.
   Default Coppola podría ser 0.05 MW.

c) **MIROVA descarta pixels en bordes de cluster** (erode 1 pixel?). Para
   eliminar pixels marginales que rozan el threshold.

**Plan**: bajar 5 granules específicos donde MIROVA reportó VRP bajo
(0.05-0.5 MW) y nosotros reportamos 5-20× más. Análisis pixel-por-pixel.

### Prioridad 3 — Lascar MODIS 68% recall (límite físico aceptado)

32% de FNs son MODIS pasadas donde Test 1 no dispara (bg ring 1-3km MODIS
solo ~25 pixels, threshold strict). Posibles caminos:

- **Bajar `TEST1_K_SIGMA` de 3 a 2.5 SOLO para MODIS**. Riesgo: más FPs.
- **Aumentar `TEST1_ROI_KM` de 3 a 5 SOLO para MODIS**. Recover bg ring.
  Pero ROI 5km incluye Salar Atacama → contamina background.
- **Aceptar como límite físico** y dejar 68% como techo.

Mi recomendación: aceptar como límite físico salvo evidencia de que el
65% restante es comportamiento MIROVA mismo y no debería ser TPs.

### Prioridad 4 — Llaima sobre-detección 347 vs 0 alertas reales MIROVA

Investigar (sin actuar) qué mecanismo MIROVA usa para descartar
sistemáticamente Llaima cráter. Coppola 2023 §2.5 supervisión humana es
solo OSF (no NRT) — debe haber otro filtro automático.

**Plan**: bajar 3 granules Llaima de últimos 30d donde MIROVA web dice
NONE pero nosotros tenemos detección summit. Comparar BT, NTI, dNTI,
Test 1 trigger. Buscar diferencia.

### Prioridad 5 — Re-scrape Mirova-v1 D2 (gap ~30% VIIRS)

Pendiente desde S27. CSV consolidado scrapeado tiene cobertura ~70% para
VIIRS. Re-scrape con repo Mirova-v1 cubriendo gaps temporales.

### Prioridad baja

- Frontend bugs LOW (11 pendientes) — CSV export, hardcoded defaults,
  etc. Cosméticos.
- Tests pre-S27 obsoletos (7 goldens + 3 sigma_cap=7). Regenerar o borrar.

## Workflows utilizables S32+

- `nrt.yml` — cron NRT cada 2h. **VERIFICAR que vuelva a funcionar**.
- `reproc-mirova-literal-extend.yml` — reproc 11×90d con `_mirova_literal`
  (que ahora es identical a `mirova_equivalent` desde S29 sync).
- `reproc-ndc-retry.yml` — single-volcano retry. Uso:
  ```bash
  gh workflow run reproc-ndc-retry.yml -R MendozaVolcanic/VRP-chile \
    --ref main -f volcano=Lascar -f start=2026-01-29 -f end=2026-04-29
  ```

## Verificación 30-segundos al arranque S32

```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"

# 1. Branch sync
git fetch origin && git status --branch --short
# Expected: ## s15-dev...origin/s15-dev limpio

# 2. Tests verde (excluyendo backlog)
pytest 2>&1 | tail -3
# Expected: 200 passed, 10 failed (los pre-existentes en backlog)

# 3. NRT estado
gh run list -R MendozaVolcanic/VRP-chile --workflow=nrt.yml -L 5 \
  --json status,conclusion,createdAt \
  --jq '.[] | "\(.createdAt[:19]) \(.conclusion // .status)"'
# Expected: si todos failure → arrancar con prioridad 1
```

## Resumen 2 líneas para pegar al primer prompt S32

> S31+ frontier (recall 83.5%, ratio 3.72×, tag s31-plus-frontier). NRT
> cron fallando (9/10 últimos). Lee `tasks/BLOQUE_ARRANQUE_S32.md` para
> plan completo y aplicar regla 3-preguntas de `docs/MISSION.md`.
