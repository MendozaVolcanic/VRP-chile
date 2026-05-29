# BLOQUE ARRANQUE S87

**Sesión previa**: S86 (2026-05-28). **Sesión muy productiva con cambio de marco fundacional.** 9 subagentes paralelos en dos rondas, 4 docs durables, 0 cambios pipeline, 2 reglas vinculantes nuevas (A54+A55).

## §0 — Worktree canónico (post-S82-prep)

**Path**: `C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/` (raíz).

**Primer comando obligatorio**:
```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
git fetch origin --prune
git log --oneline HEAD..origin/main
git pull --ff-only
cat docs/AUDIT_S86.md           # marco fundacional post-S86
cat tasks/BLOQUE_ARRANQUE_S87.md
```

## §1 — Lo que cerró S86

### Cambio de marco (lo más importante)

**El "gap precisión 0.024" vs MIROVA es 95% artefacto metodológico, no bug del pipeline.** Composición empírica de los 3687 "FPs":

- **49.1%** MIROVA SÍ publicó (cruce falló por 4 bugs del loader local: OCR no consumido subcontamos 45%, distancias OCR mal parseadas, alias variantes nombres, Tupungatito coverage, FALSO_POSITIVO descartado por `limite_km`).
- **46.3%** features volcánicas reales no publicadas por MIROVA (Cerro Blanco NdC, Pichi-Llaima Llaima, Lazufre Lastarria, cráter El Agrio Copahue, complejo multi-cráter PP, lacolito difuso PCC, lava lake Villarrica).
- **0%** geotermal/lacustre no-volcánico (frontend ya las filtra desde S33).
- **4.6%** artefactos reales (Tupungatito ring glaciar + PCC cirrus alto).

**El proyecto NO es sub-óptimo — está haciendo trabajo distinto + ampliado respecto a MIROVA NRT.** Intuición de Nicolás S86 confirmada empíricamente.

### Hipótesis refutadas con datos (eliminación espacio de búsqueda)

1. **Mec 2 (gate t_bg≥260K)** — refutado: pierde evento eruptivo Lascar 2026-02-17 con cubierta nubosa fría (12 px, 119 MW, único path D activo).
2. **Mec 3 (coherencia temporal ≥2 noches)** — refutado: FPs persisten 79% (vs TPs 91%), diferencia 12 pp insuficiente. Nuestros FPs son cuerpos térmicos reales persistentes, no ruido pasajero.
3. **G1 (`sensor != VIIRS_M_750`)** — propuesto inicialmente, REFUTADO post-auditoría E: VIIRS_M_750 puede capturar features volcánicas reales no publicadas por MIROVA.

### Auditoría integral (5 subagentes E+F+G+H+I)

| Subagente | Hallazgo |
|---|---|
| **E** clasificación física FPs | 95% realidad física, 4.6% artefacto, 0% geotermal |
| **F** integridad scraper | scraper confiable, 4 bugs locales del loader VRP Chile |
| **G** tests + drifts | pipeline mejor del esperado, D1/D2/D3/D6 cerrados, bug A49 NO en main |
| **H** estado GitHub | repo saludable, NRT 79% éxito, ~70 min cleanup opcional |
| **I** coherencia docs | 7 contradicciones, C1/C2/C4/C7 resueltos S86, M8 reformulación propuesta |

### Anti-patrón emergente A55

PRs #224 (S83 path D intra-radio) + #229 (S85 second_pass intra-radio) son **redundantes** con `frontend mirovaEqVrp` desde S33. Análogo a S22-S26. Cualquier PR futuro tipo "gate intra-radio por path" requiere checks formales (verificar frontend, clasificar categoría, no destruir b).

### Bloque 1 ya ejecutado en cierre S86 (sincronización marco)

- ✅ `docs/MISSION.md` cabecera reescrita (objetivos 1+2 simultáneos) + fila anti-patrón "gate intra-radio sin paper"
- ✅ `CLAUDE.md` proyecto: worktree canónico corregido + A54 (gap precisión es artefacto metodológico) + A55 (anti-patrón gate intra-radio) + nota A56-A60
- ✅ `docs/MIROVA_DIVERGENCES.md` D8' (cluster selection Puyehue S35) cerrado formalmente como RESUELTO S38
- ✅ `MEMORY.md` entrada S86 persistida
- ✅ `docs/AUDIT_S86.md` síntesis durable (entrada principal)
- ✅ `docs/F_PRECISION_GAP_INVESTIGATION_S86.md` actualizado con conclusiones E+F

### PR cierre S86

[Ver descripción del PR — generado al cierre con tag commit S86]

## §1.5 — HALLAZGO CENTRAL S86 tardío (el foco real de S87)

Nicolás refinó el objetivo a fin de S86: **lo que importa es si la anomalía que MIROVA reporta como la mayor en cada pasada satelital es también la que nosotros detectamos como la mayor. Si no coincide, descubrir cómo arreglarlo.**

### Corrección conceptual (vinculante)

**NO usar "huella canónica" como gate ni como área fija.** MIROVA no fija un área canónica — estudia toda la escena, reporta la mayor anomalía, y entrega la distancia para clasificación visual (summit/far). Imponer una huella violaría objetivo (1) clon + anti-patrón A55. La huella (experimento J) queda SOLO como **instrumento de auditoría** — mide divergencia con MIROVA, no filtra.

El criterio correcto sigue siendo: **la mayor anomalía de la escena + su distancia** (esquema dual S14 + frontend mirovaEqVrp).

### Validación preliminar L (3 vols control, solo OCR)

Ver `experiments/_s86_exp_huella/L_dominant_anomaly_match_PRELIM.md`.

| Volcán | Match nuestra-mayor = MIROVA-mayor | Diagnóstico |
|---|---|---|
| Tupungatito | 92% (24/26) | Sano |
| Chaitén | 62% (5/8) | Divergencia moderada |
| **PCC** | **0% (0/34)** | 🔴 Reportamos punto totalmente distinto |

**PCC es el bug**: MIROVA reporta el lacolito Cordón Caulle a ~12-14 km del vent Puyehue (la mayor anomalía real, fisura erupción 2011). Nosotros reportamos a ~0.4-1 km (pegados al vent Puyehue). Causa raíz: fix D8 `vent_anchored` ancla al vent nominal (Puyehue) + el vent está en el centro equivocado. El lacolito está dentro del `inner_radius=20km` pero vent_anchored prioriza proximidad sobre magnitud → nunca lo elige. MIROVA hace lo opuesto (reporta la mayor).

### Bloque CENTRAL S87 — Validación 1:1 anomalía dominante

1. Tras Bloque 2 (fix loader → distancia MIROVA limpia CONS+OCR), correr validación completa los 11 Tier A: % pasadas donde nuestra-mayor = MIROVA-mayor.
2. **Reproceso con flag diagnóstico** que persista TODOS los clusters por escena (hoy el JSON solo guarda el primary ya elegido — no sabemos si detectamos la mayor pero la descartamos).
3. **A/B criterio de selección**: `vent_anchored` (actual) vs `vrp_max_inner` (la mayor dentro del inner) vs mover ancla PCC al Cordón Caulle. Métrica: % match anomalía dominante. Controles: Tupungatito (92%, no romper), Lascar (compacto), PCC (0%, arreglar).
4. **Cuidado** (experimento K): `vrp_max` puede empeorar sobre-reporte de MAGNITUD per-vol. Ubicación (qué punto) y magnitud (cuántos MW) son problemas separados — el A/B mide ambos.

## §2 — Plan S87 (detalle)

### Bloque 2 — Fix loader CSV + rehacer cruce TP/FP (PRIORITARIO, habilita el bloque central)

**ETA**: 1-2h. **Toca**: scripts de audit + módulo `pipeline/mirova_csv_loader.py`. **NO toca pipeline NRT** (cero riesgo A45, ningún tag defensivo requerido).

#### ✅ PARTE 1 HECHA (PR #232 mergeado, commit `a4a22f4e`)

`pipeline/mirova_csv_loader.py` creado con TDD (20 tests, suite 558 passed 0 regresiones). Resuelve:
- ✅ **F-B1** CONS∪OCR dedup por `(timestamp, vol, sensor)` priorizando CONS.
- ✅ **F-B2** distancia OCR parseada de `Nota_Validacion` (`parse_ocr_distance`).
- ✅ **F-B4** alias `Peteroa → PlanchonPeteroa` + todas las variantes A14 (`normalize_volcano_name`).
- ✅ **A48** sensor bucket (`normalize_sensor`).

**Verificado contra datos reales**: 977 ALERTAs Tier A (654 CONS + 323 OCR únicas) = **+49% sobre solo-CONS**, 100% con `dist_km` resuelta. Confirma subconteo ~45% del Subagente F.

API: `load_mirova_alertas(cons_path, ocr_path, volcano=None)` → lista de dicts `{timestamp, volcano, sensor_bucket, vrp_mw, dist_km, tipo, source, clasificacion, fecha_utc, fecha_local}`.

#### ⏳ PARTE 2 PENDIENTE (arranque próxima sesión)

1. **Refactorizar los ~15 scripts de audit** para consumir `load_mirova_alertas` en vez de reimplementar la carga (el Explore S87 detectó VOL_CSV_MAP + sensor_family replicados 10-15 veces). Eliminar duplicación.
2. **F-B3**: documentar que Tupungatito CONS arranca 2026-02-14 (35d después). Recortar ventanas de audit a coverage real o reportar separado. (Pendiente — el loader no lo maneja, es decisión del script de audit.)
3. **F-I2**: política `Tipo_Registro=FALSO_POSITIVO` CONS (363 filas): decidir si tratarlas como detección MIROVA lejana (`far`) en vols con anomalía extendida (PCC). (Pendiente — el loader actual las descarta; reconsiderar.)
4. **Rehacer el cruce TP/FP** con el loader nuevo → medir nuevo gap precisión.

#### Validación post-fix (Parte 2)

Re-ejecutar cruce TP/FP con loader corregido sobre mismo 117d window. Comparar:
- TPs antes vs después (esperado: ↑)
- FPs antes vs después (esperado: ↓)
- Precision antes vs después (esperado: ↓ "FPs" residuales → precision ↑ hacia ~0.5)

Output: `experiments/_s87_bloque2/cruce_corregido.{md,json}` + actualización de tablas en `docs/AUDIT_S86.md` con la nueva métrica.

**Si precision residual sigue ≤0.3** después del fix → revisar metodología nuevamente (probablemente el residual 46.3% categoría b es lo que queda — pasar a Bloque 3).

### Bloque 3 — Etiquetar honestamente las detecciones (3-4h, 1-2 sesiones)

**Toca**: `pipeline/store.py` (campo derivado) + `frontend/index.html` (rendering por categoría) → **regla A45 requiere tag defensivo + tu OK explícito**. Tag propuesto: `pre-s87-classification-field`.

#### Diseño campo `pc.classification` (4 valores)

```python
pc["classification"] = (
    "mirova_confirmed"   if matches_mirova_canon (CONS∪OCR post-Bloque2) else
    "vrp_chile_volcanic_extension" if dist_to_known_volcanic_feature <= 2km else
    "artifact_candidate" if (t_bg<260K AND only_path_D AND n_pixels<=1) or (vol=="Tupungatito" AND ring_glacier_pattern) else
    "vrp_chile_summit_unconfirmed"
)
```

#### Cartografía features volcánicas conocidas

Cargar coords Smithsonian GVP para los 11 Tier A + sub-features identificadas por Subagente E:
- Cerro Blanco (NdC) sub-complejo
- Pichi-Llaima (Llaima) cráter secundario
- Lazufre (Lastarria) complejo regional
- Cráter El Agrio + 9 cráteres alineados E-W (Copahue)
- Cráter Planchón N + Azufre (PP)
- Lacolito difuso 707 km² (PCC)
- Lava lake (Villarrica)
- Cráter cumbre (Tupungatito)

YAML nuevo `pipeline/volcanic_features.yaml` con `additional_centers` per-vol.

#### Frontend rendering

Modificar `frontend/index.html`:
- "ALERTA MIROVA confirmada" (color rojo intenso) — `classification == "mirova_confirmed"`
- "Detección VRP Chile (feature volcánica no-MIROVA)" (color naranja) — `classification == "vrp_chile_volcanic_extension"`
- "Detección summit sin confirmación MIROVA" (color amarillo) — `classification == "vrp_chile_summit_unconfirmed"`
- "Candidato artefacto" (color gris) — `classification == "artifact_candidate"`

Dashboard pasa de "clon MIROVA" a "monitoreo VRP Chile con desglose MIROVA".

#### Validación

- Tests sintéticos `tests/test_store_classification.py` con 4 casos canónicos.
- R2 verificación pixel-level: muestra de 30 records clasificados auto, validar manualmente contra Google Earth + KMZ.
- A/B reproc 117d: verificar que `mirova_confirmed` matchea las 1812 ALERTAs MIROVA del cruce corregido (Bloque 2).

### Bloque 4 — Cerrar gaps coverage tests (opcional, ~2h)

Cerrar riesgos G-R1/R2/R3 del Subagente G:
- **R1** Tests sintéticos `process_viirs_mod.py` paridad con `process_viirs.py` (coverage 25% → ≥50%).
- **R2** Tests invariantes `profile.py` (defaults Coppola 2016a, flags consistentes cross-profile).
- **R3** Test directo "MIR solo nocturno" rechazo records day-time.

### Bloque 5 — Cleanup cosmético GitHub (opcional, ~70 min)

Del Subagente H:
- Cerrar issue #1 (ya resuelto) + PR #223 (superseded).
- Archivar 3 reproc workflows obsoletos (`reproc-f28-pp-saturation`, `reproc-ab-f-s81-a-intra-radio`, `reproc-ab-f-s81-b-prime`).
- Fix A43 `"on":` quoted en `nrt.yml` + `nrt-monitor.yml`.
- Cleanup branches `claude/*` (regla `docs/BRANCHES_CLEANUP_S80.md`).
- ⚠️ **Rotar GitHub PAT** en `~/.claude/settings.json` (pendiente desde sesión anterior).

## §3 — Lo que NO debemos hacer S87+ (escudo anti-drift)

1. **NO implementar Frente 1.A G1 ciego** (`sensor != VIIRS_M_750`). El gate destruye categoría (b) "features volcánicas reales no publicadas por MIROVA". Si se quiere filtrar VIIRS750 selectivamente, primero clasificar pixel-level qué fracción de VIIRS750 publishable es categoría (b) vs (d).
2. **NO extender exclude_zones**. Categoría (c) = 0% (frontend ya filtra fuera del inner_radius). Las features no-volcánicas catalogadas en `docs/F_S81_C_1_ZONES_CATALOG.md` (Las Máquinas Copahue, Río Diguillín NdC, ladera Malargüe PP) están **fuera del inner_radius operacional** y no entran al universo publishable.
3. **NO seguir adoptando "gates intra-radio por path"** (anti-patrón A55).
4. **NO implementar `t_bg<260K` como gate global**. Pierde evento eruptivo Lascar 2026-02-17 (cubierta nubosa fría, único path D activo). Si se quiere fix cirrus path D, condicional a `t_bg<260K AND n_pixels<=2 AND vrp<5MW` (preserva eventos eruptivos).
5. **NO implementar coherencia temporal como gate principal**. Solo aporta +2 pp precision con costo 9% recall + arquitectura dual-flag NRT compleja.

## §4 — Reglas vinculantes activas

- **A45** tag defensivo + confirmación Nicolás antes de `pipeline/process_*.py`, `store.py`, `mirova_equivalent.yaml`.
- **A47** NO paralelo local sobre `data/mirova_equivalent/`.
- **A52** `git fetch + pull` en worktrees, no asumir estado.
- **A54 (NUEVA S86)** Gap precisión es 95% artefacto metodológico. Antes de "fix de precisión", clasificar categoría (a/b/c/d) de records que el fix filtraría.
- **A55 (NUEVA S86)** Anti-patrón gate intra-radio por path. Cualquier propuesta requiere verificar frontend + clasificar categoría + no destruir b.
- **A56-A60** preventivos NRT en `docs/META_RULES_S80.md`.
- **M1** cap PRs/sesión soft 12 hard 20.
- **M2** persistencia in-vivo.
- **M8** auditoría cada 10 sesiones O 25 PRs (reformulación S86 propuesta por I).
- **calidad-paso-a-paso (S85)** — investigar antes de implementar, registrar descartes con datos.
- **when-to-close-session (S85)** — zona verde/amarilla/roja.

## §5 — Comunicación con Nicolás

Geólogo: fenómeno físico → mecanismo pipeline → fórmula al final. Cuando propongas adopción operacional, explicar primero qué hace el cambio sobre el campo térmico, después por qué el audit valida.

## §6 — Prompt copy-paste para S87

```
Sesión S87 — VRP Chile. S86 cerró con cambio de marco fundacional:
el "gap precisión 0.024" es 95% artefacto metodológico (49% bugs loader,
46% features volcánicas reales no publicadas MIROVA, 0% geotermal, 4.6%
artefactos). 5 subagentes auditoría integral (E/F/G/H/I) + 4 subagentes
investigación gap (A/B/C/D). 2 reglas vinculantes nuevas: A54 (gap es
artefacto) + A55 (anti-patrón gate intra-radio).

Worktree: C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile

Primer comando:
  cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
  git fetch origin --prune && git pull --ff-only
  cat docs/AUDIT_S86.md
  cat tasks/BLOQUE_ARRANQUE_S87.md

Lectura obligatoria:
1. tasks/BLOQUE_ARRANQUE_S87.md (este doc — plan 4 bloques)
2. docs/AUDIT_S86.md (marco fundacional + síntesis 5 subagentes E/F/G/H/I)
3. docs/F_PRECISION_GAP_INVESTIGATION_S86.md (gap precision, conclusiones)
4. docs/MISSION.md (objetivos 1+2 simultáneos + anti-patrón gate intra-radio)
5. CLAUDE.md proyecto secciones A54 + A55 nuevas

Bloque prioritario S87:
- Bloque 2 (1-2h, sin riesgo NRT): fix loader CSV (CONS∪OCR + distancia
  OCR parseada + alias Peteroa + Tupungatito coverage + FALSO_POSITIVO
  política). Después rehacer cruce TP/FP. Predicción: gap precisión → ≤0.5.

Escudo anti-drift (NO hacer):
- NO implementar G1 ciego (suprime categoría b).
- NO extender exclude_zones (categoría c=0%).
- NO seguir adoptando gates intra-radio (anti-patrón A55).
- NO implementar t_bg<260K global (pierde Lascar eruptivo 17/02).

Reglas activas: A45, A47, A52, A54, A55, A56-A60, M1, M2, M8 (reformulada),
calidad-paso-a-paso, when-to-close-session.

Comunicame como geólogo: fenómeno → mecanismo pipeline → fórmula al final.
```
