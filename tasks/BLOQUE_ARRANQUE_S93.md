# BLOQUE ARRANQUE S93

**Sesión previa**: S92 (2026-05-30). 5 PRs (#269-273), todos mergeados, **0 cambios
al pipeline operacional** (todo display-only / infra / docs). Working tree limpio,
main al día. CI sano (NRT cron normal, deploys success).

## §0 — Worktree + primer comando
```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
git fetch origin --prune && git pull --ff-only
cat tasks/BLOQUE_ARRANQUE_S93.md
```

## §0.5 — Regla dura de integridad (sigue vigente de S91/S92)
1. Ningún número entra a doc/PR/commit transcrito a mano. Script reproducible =
   fuente de verdad; verificación programática `python -c`/verify antes de commit.
2. `experiments/_s92_daytime_diag/verify_findings.py` debe imprimir `ALL_VERIFIED`
   antes de tocar ese FINDINGS.
3. Un tool call por mensaje si el entorno entrelaza salidas (no pasó en S92, el
   entorno estuvo estable).

## §1 — Qué se hizo en S92 (cerrado, NO re-derivar)

### A/B detección diurna MODIS — CERRADO: NO ADOPTAR (flag OFF)
- **#2.1 causa raíz**: el A/B S91 dio Δ=0 porque el workflow no abría la 1ª compuerta
  de fetch (`nighttime_only`). Fix: perfil enabled corre con `--no-night-filter`
  (PR #269). **No era bug del pipeline** (`_scene_is_day` funciona).
- **#2.2 fuga VIIRS**: REFUTADA (re-confirmada con data mayo: 0 records VIIRS comunes
  difieren). El flag no toca VIIRS.
- **Veredicto (PR #273)**: reproc mayo OK (enabled 63 MODIS vs disabled 29). De 23
  pasadas diurnas, **22 → meq=0.00** (path INOCUO, no FP solares masivos). 1 sola
  detección dudosa (05-20, sol 10°, 3.91 MW). **MIROVA OCR=0 alertas NdC** en la
  ventana → no hubo eventos diurnos reales → A/B **inconcluso por ventana
  inadecuada**, NO por fallo. R2 inviable (mediodía da meq=0). `enable_daytime_modis`
  sigue **OFF**. Detalle: `experiments/_s92_daytime_diag/FINDINGS.md §6`,
  [[reference_s91_daytime_ab_pending]], [[project_s92_findings]] (L1-L4).

### Limpieza cirrus — COMPLETA en las 3 vistas
- index.html tabla v2 (atenuar+badge, #270) + diario.html/mosaico.html (filtro
  portado, #272). Verificado en preview. [[reference_s90_display_cirrus_suppression]].

### Auditoría PCC (a pedido de Nicolás)
- El pico 337 MW que vio en el dashboard es **warm-scene difuso real-pero-
  sobreestimado** (860 px tibios sumados vs foco MIROVA 0.3 MW), NO cirrus (el
  filtro cirrus sí oculta los 5 picos t_max<273). Deploy verificado OK.

## §2 — PENDIENTES S93 (en orden de valor)

### 2.1 — Veredicto DEFINITIVO detección diurna (si Nicolás quiere retomar)
El A/B mayo fue inconcluso (ventana NdC sin actividad diurna MIROVA). Para un
veredicto firme: **buscar una ventana volcán+fecha con ALERTA diurna MIROVA
confirmada (OCR/CONS) Y TIF disponible** (`../mirova-tif-archive/data/tif/<Vol>/`,
TIF desde 2026-05-09). Candidatos: cruzar OCR de los 11 Tier A buscando ALERTAS con
elevación solar>0 entre 05-09 y hoy. Si existe → reproc esa ventana con el workflow
`reproc-daytime-modis-ab.yml` (ya tiene el fix `--no-night-filter`) → analyze_ab +
R2 (adaptar `compare_tif_mirova_vs_ours.py` a MODIS, hoy es VIIRS-only). Si no hay
actividad diurna en ningún Tier A → el path queda "inocuo pero sin beneficio
demostrado", documentar y NO adoptar. Herramientas listas: `analyze_ab.py`,
`close_ab.py`, `diag*.py` en `experiments/_s92_daytime_diag/`.

### 2.2 — Warm-scene PCC: mejora DISPLAY (Nicolás difirió en S92, retomar con cuidado)
Feedback de Nicolás (operador): el dashboard muestra PCC 337 MW cuando MIROVA
reporta 0.3 MW (campo difuso sumado). Es real (cat. b) pero engañoso. **NO tocar
pipeline** (gate de magnitud = A55). Opción display-only: brainstorming OBLIGATORIO
+ validar criterio "0 detecciones reales atrapadas" (como cirrus S90). Candidatos:
badge "campo difuso — magnitud agregada" / mostrar foco junto a suma / atenuar.
Detalle + auditoría: [[reference_s91_warmscene_pcc_closed]] addendum S92.

### 2.3 — PR #223 abierto (S82, gate intra-radio MIROVA MODIS)
Sigue abierto, ajeno a S92. Revisar si procede cerrar/mergear/descartar (puede ser
stale; ojo A55 — los gates intra-radio fueron cuestionados S86 I-C6).

### 2.4 — (opcional, bajo) cargar OCR en `data/mirova/<vol>.json`
Hoy solo CONS → mejora precisión REPORTADA, no recall (A54). Tooling.

## §3 — Escudo anti-drift (vigente, NO violar)
1. NO vent_anchored nuevo (validado S87/S88).
2. NO gate `t_bg<260K` (refutado S86). Criterio cirrus usa `t_max`, NO `t_bg`.
3. NO huella/exclude_zones/gate-intra-radio nuevo (A55).
4. geo_class/mirova_confirmed/cirrus/geo display = ETIQUETAS/display, NO filtran.
5. **Detección diurna MODIS flag OFF** (veredicto S92: inocuo pero inconcluso; NO
   setear sin nuevo A/B válido con TIF + tag + OK A45).
6. Warm-scene PCC: anomalía real cat. b; NO meter gate de magnitud en pipeline (A55).

## §4 — Reglas vinculantes
A45 (tag+OK antes de pipeline), A47, A48, A52, A54, A55, A18, M1, M2, M8 +
integridad §0.5. Learnings de método S92: L1-L6 en [[project_s92_findings]].
Frontend: verificar en preview navegador (no solo node --check) — las 3 vistas
sirven desde `/frontend/`, BASE_PATH=`/`, data en `/data/...`.

## §5 — Comunicación con Nicolás
Geólogo: fenómeno físico → mecanismo pipeline → fórmula al final. El "por qué"
antes del "cómo". Todo queda registrado para el paper futuro (provenance).
