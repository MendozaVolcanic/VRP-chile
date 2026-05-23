# Bloque arranque S73 — VRP Chile (post cierre S72 2026-05-22)

> Continuación tras cierre S72. 20 PRs mergeados (#112-#130). Investigación F2.5-F2.6 cerrada con verdict: **deriva S26→S71 validada, NO revertir features S38-S71**.

## 1. Estado al cierre S72

### Validaciones completadas

- ✅ **Cap S71 (Opción C, PR #112)** funciona correctamente. F2.6.a code review + 467 records `d9_capped=True` todos en 5.0 exacto + 6 tests anti-regresión (PR #123).
- ✅ **Deriva S26→S71 = mejora arquitectural**. 3 fuentes independientes:
  - AVTOD ASTER (Coppola coautor, PR #127) — Tupungatito FP MIROVA + régimen Muy Bajo físicamente justificado.
  - MIROVA NRT CONS+OCR (F2.6.h) — 16/16 records "lost summit >500 MW" inflados 1000× sobre MIROVA.
  - Geográfico Salar Atacama (F2.6.g) — 67% lost summit far en zona Salar.
- ✅ **NRT local Windows** completamente funcional (PR #129 + #130):
  - `.env` loader minimal (parse sin python-dotenv).
  - EARTHDATA_TOKEN bypassea throttling NASA-Azure.
  - VIIRS 375m (I-band) + 750m (M-band) procesan correctamente.
  - MODIS sigue skip por pyhdf Windows.
  - `scripts/nrt_local.bat` listo para Task Scheduler.

### Verdicts derivados (NO revertir)

- ❌ "Lascar regression -9.3pp recall" — ILUSORIA. Records "perdidos" eran FPs Salar Atacama + inflación 1000× pre-S40.
- ❌ Reactivar `bt_path_hot` (revertir S40) — REFUTADO. bt_path_on REDUCE recall en 9/9 vols, no infla.
- ❌ Adoptar fix "unsuitable filters / K1 retire" — INNECESARIO. F2.4 mostró output idéntico entre setups (flag dominante es `enable_first_pass_tests_2_and_3`).
- ❌ Per-vol opt-in cap S71 — NO. Cap funciona en todos, no aporta selectividad.

## 2. Priorización S73 (en orden ejecutar)

### P1 — F2.8: investigar PP vmax 695,431 MW (URGENTE)

**Hallazgo F2.7 audit**: record PlanchonPeteroa 2026-03-18 MODIS_AQUA con `pc.vrp_mw = 695,431 MW` (medio millón). Visible en producción dashboard. NO bug D9 (criterios no cumplen). Posible cluster NTI mal segmentado.

**Sub-tarea**: subagente extrae record completo + diagnóstico campos (n_pixels, n_nti_path, t_bg, ratio_anómalo). Cross-check timestamp con CSV MIROVA. Verdict: bug local o ground truth raro.

**Costo**: ~30-45 min subagente. Si bug local → fix + reproc 1 día. Si raro pero válido → documentar caso especial.

### P2 — Task Scheduler Windows + observación 48h

```powershell
schtasks /Create /TN "VRP_Chile_NRT" /TR "C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP-Chile-s70\scripts\nrt_local.bat" /SC HOURLY /MO 2 /F
```

Setup cron cada 2h. Observar 48h:
- Verificar logs en `logs/nrt_local/`.
- Confirmar push exitoso a main.
- Race con GH Actions cron — el bat hace `git pull --rebase -X theirs` antes de push.

**Si funciona 48h** → comentar `cron:` en `.github/workflows/nrt.yml` (deshabilitar GH Actions cron). Mantener `workflow_dispatch` para reprocs manuales.

### P3 — T1.5: drift remanente Villarrica/Chaiten/PP/PCC (OBJETIVO REAL desde S71)

**Estado actual**: ratios 6-12× contra MIROVA NRT en régimen Tier A Muy Bajo. Cap S71 acota magnitudes path-D-contextual-only en cirrus, pero ratios fuera de [0.5, 2.0] indican drift remanente NO atribuible a path D.

**Hipótesis abiertas post-F2.6**:
- HT1.5-NEW-1 cluster scene-wide: **CONFIRMADA en lit MIROVA** pero F2.4 mostró que nuestro `primary_cluster` ya hace lo correcto (output idéntico cross-setups). El drift no viene de cluster aggregation.
- HT1.5-NEW-2 L_bk excluye TODOS hot pixels: F1.3 ✅ PASS. Ya implementado correctamente.
- HT1.5-NEW-3 Method-2 weekly minima: post-processing temporal, NO aplica NRT real-time.
- HT1.5-NEW-4 coord vent geométrico: F1.1 REFUTADA 4/5 vols (Villarrica/Chaiten/PCC/PP centroide térmico p50 <1 km vent).
- **NUEVA HT1.5-NEW-5**: ¿es C2·σ contextual de Tests 2&3 demasiado permisivo en régimen Muy Bajo? Massimetti 2024 §561-562 dice MIROVA usa Tabla 1 C2=5/10 estándar. Pero quizá nuestra σ_bg está distinto por sensor (VIIRS I-band 375m vs MIROVA referencia MODIS 1km).

**Sub-tareas S73+**:
- F3.1 — análisis per-record drift Villarrica/Chaiten/PP/PCC: ¿ratio inflado viene de pixels marginales o pixels brillantes? Si marginales → C2 más estricto. Si brillantes → otro mecanismo.
- F3.2 — A/B Tests 2&3 con C2=10 summit / C2=15 scene (más estricto que defaults Tabla 1).
- F3.3 — verificar que dual_roi_first_pass está bien wireado per-vol Muy Bajo.

### P4 — M-band kernel-bg implementation (TODO F2.9)

`process_viirs_mod.calculate_vrp` actualmente acepta `local_kernel_bg_compatible` como **no-op**. Implementar block real replicando `process_viirs.py:856-867`:

```python
if ENABLE_LOCAL_KERNEL_BG and local_kernel_bg_compatible:
    t_bk_local = compute_local_background(bt, hot_rows, hot_cols, kernel_size=3)
    t_bk_arr = np.array(t_bk_local, dtype=np.float64)
    if not np.isnan(t_bg):
        t_bk_arr = np.where(np.isnan(t_bk_arr), t_bg, t_bk_arr)
    L_bg = bt_to_spectral_radiance(t_bk_arr, M13_LAMBDA)
else:
    L_bg = bt_to_spectral_radiance(np.float64(t_bg), M13_LAMBDA)
```

**Impacto esperado**: simetría I-band/M-band para vols opt-in (Villarrica/PP/Lastarria/Chaiten/PCC). Probable mejor calibración Muy Bajo régimen → contribuye a T1.5.

### P5 — Paper open source VRP Chile iteración

`docs/PAPER_VRP_CHILE_DRAFT_S72.md` (PR #119). 3 decisiones pendientes:
- **Venue**: Frontiers Earth Sci Vulcanology (recomendado) vs RS MDPI vs JVGR vs GMD.
- **Authorship**: Nicolás lead. Co-autores SERNAGEOMIN/MIROVA team. Claude/Anthropic NO co-author (policy 2026) → Acknowledgments + Code availability.
- **Scope**: literal-clone vs incluir extensions D9 cap + Tupungatito + AVTOD.

Iteración requiere T1.5 cerrado. Estimación 4-6 meses draft + 8-12 meses publicación post-Frontiers submission.

## 3. Backlog adicional (sin urgencia)

- **AVA ASTER Volcano Archive scrapear** (F1.11 backlog) — combinable con AVTOD para validation multi-sensor.
- **AVTOD Table S1 supplementary** descarga manual desde Elsevier Appendix A o https://ava.jpl.nasa.gov/avtod.php.
- **Cigolini 2022 EPSL** (DOI 10.1016/j.epsl.2022.117726) — Cloudflare 4 fuentes bloqueadas. Alternative: pedir a autor via ResearchGate.
- **Massimetti THESIS** extracción exhaustiva (ya convertido a .md, pero no procesado citas literales).
- **Bug get_effective_vent fallback chain** (F1.6 hallazgo arqueológico) — post-S65 cae a `volcano_lat` en lugar de `vent_lat` cuando `mirova_center` ausente.

## 4. Quick start S73

```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP-Chile-s70"

# Sync con main
git fetch origin --prune
git checkout main && git pull

# Verificar estado
gh pr list  # PRs abiertos
python -m pytest tests/ -q  # tests OK (target 380+ passed)

# NRT cron local (ver si está activo)
schtasks /Query /TN "VRP_Chile_NRT"

# Ver últimas alertas operacional
ls -lt data/mirova_equivalent/ | head -5
```

**Arrancar S73 leyendo**: este doc + `docs/F26_VERDICT_CONSOLIDATED_S72.md` (verdict final) + `docs/MIROVA_DIVERGENCES_CATALOG_S71.md` (catálogo divergencias).

## 5. Aprendizajes meta documentados S72

| ID | Aprendizaje | Source |
|---|---|---|
| **A30** | `mirova_center` es anchor empírico de cluster selection MIROVA paridad, NO verdad geológica | F1.6+F1.7 Tupungatito |
| **A31** | Perplexity Pro Deep Research es complementario a APIs gratis (69% overlap), no sustituto | F1.9+F1.11 |
| **A32** | Separar drifts (cerrar) vs hipótesis priorizadas (investigar) vs extensions (publicar) en docs distintos | BEYOND_MIROVA_EXTENSIONS doc |
| **A33** | Trust but verify SHAs en audits cross-comparativos. Datasets son acumulativos | F2.5.b falsa alarma |
| **A34** | Hallazgos contra-intuitivos requieren 3+ fuentes independientes con metodologías distintas | F2.5.b → F2.6 cadena |

## 6. PRs S71-S72 mergeados (referencia rápida)

| # | PR | Contenido |
|---|---|---|
| 112 | S71 adopción Opción C cap 5MW path D D9 | Validado R1+R2+R3 |
| 113 | S71 papers MIROVA exhaustivo + citas H1-H6 | 3 papers canónicos |
| 114 | S72 verdicts Fase 1 audits (5 hipótesis) | F1.1-F1.5 |
| 115 | S72 F2.1 unsuitable filters + flag Test 1 | F2.4 mostró redundante |
| 116 | S72 Tupungatito finding + plan mirova_center | Re-abre S65 |
| 117 | S72 F1.7-F1.9 + REFS_TIER1 + re-interpretación HT1.5-NEW-1 | Tupungatito sub-MW |
| 118 | S72 BEYOND_MIROVA_EXTENSIONS backlog | 12 extensions documentadas |
| 119 | S72 paper VRP Chile skeleton publicación | Draft pendiente decisiones |
| 120 | S72 doc corrections Fan 2015 + Bernstein 2013 | AP21 Perplexity hallucinations |
| 121 | S72 F1.15 EARTHDATA_TOKEN auth bypass | NRT cron parcial fix |
| 122 | S72 F2.3 split flags 2×2 A/B aislados | F2.4 mostró flags no respetados |
| 123 | S72 F2.6.a 6 tests anti-regresión cap S71 | Bug F2.5.b confirmado falso |
| 124 | S72 A33 lección falsa alarma F2.5.b | Trust SHAs |
| 125 | S72 F2.6.b A/B no_cap_v1 pipeline-actual | Comparativa limpia |
| 126 | S72 F2.6.e A/B bt_path_on_v1 revert S40 | Test hipótesis F2.6.c |
| 127 | S72 F2.6.f AVTOD cross-validation | Tupungatito FP MIROVA confirmed |
| 128 | S72 F2.6 verdict consolidado deriva validada | NO revertir |
| 129 | S72 local NRT setup .env + cron Windows bat | Workaround NASA-Azure |
| 130 | S72 F2.9 fix VIIRS 750m kwarg TypeError | Bug local descubierto |
| 131 | (este) S72 cierre + BLOQUE_ARRANQUE_S73 | Cierre sesión |

## 7. Cierre S72 — métricas

- **20 PRs** mergeados (#112-#131).
- **48+ tasks** tracked (51 actuales).
- **9 audits sistemáticos** completados.
- **4 A/B reprocs** ejecutados.
- **3 fuentes validación independientes** (MIROVA OSF + NRT + AVTOD).
- **5 aprendizajes meta** documentados.
- **1 bug fixed inline** (F2.9 VIIRS 750m).
- **1 bug backlog** (F2.8 PP vmax 695,431 MW).
- **0 regresiones operacional**.
- **NRT local 100% funcional** post-fix.
- **NRT cron GitHub 20% success** (insuficiente → P2 S73).
