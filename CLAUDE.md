# VRP Chile

Sistema VRP independiente para volcanes chilenos (equivalente MIROVA, propio).
Repo: https://github.com/MendozaVolcanic/VRP-chile

## ⚡ Working worktree canónico (LEER PRIMERO en cada sesión nueva)

**Path canónico post-S82-prep**: `C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/` (raíz del repo).

**Primer comando obligatorio de cualquier sesión Claude**:

```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
git fetch origin --prune
git pull --ff-only
ls tasks/BLOQUE_ARRANQUE_S*.md | tail -1   # leer el último bloque de arranque
cat docs/SESSION_INDEX_CONSOLIDATED_S80.md  # ancla canónica post-S80
cat docs/AUDIT_S86.md                       # marco fundacional post-S86 (95% FPs son realidad física)
```

**Razón actualización S86 (resuelve C1 auditoría I)**: S82-prep reapuntó la raíz `VRP Chile/` a `main` (commit `81c38e7b`) tras detectar que estaba quedada en branch `s15-dev` stale (S33). La raíz es el worktree principal y se mantiene siempre en main al día. El worktree antiguo `VRP-Chile-s70/` quedó en branch huérfano `work-s78-bloque-arranque-s79` y NO se debe usar como canónico (regla A52: worktrees no-main pueden estar atrasados). Otros worktrees (`VRP-Chile-s80-consolidation/`, `VRP-Chile-s79-f66/`) sirven para trabajo específico de sus branches pero NO son canónicos.

**Bloques de arranque por sesión**: cada cierre de sesión persiste `tasks/BLOQUE_ARRANQUE_S{N+1}.md` con el plan ejecutivo de la siguiente. Leer ese archivo **antes** de empezar trabajo. Última actualización: ver `MEMORY.md` index.

## Misión vinculante (LEER ANTES DE TOCAR PIPELINE)

**Objetivo: clon literal MIROVA NRT.** Antes de implementar cualquier feature,
fix, threshold, exclusion, path o transformación en `pipeline/`, leer
[docs/MISSION.md](docs/MISSION.md) y aplicar las 3 preguntas. Si las 3 dan NO,
NO IMPLEMENTAR — anotar en `tasks/backlog_*.md` con la razón.

Lecciones acumuladas: cada parche que agregamos en sesiones pasadas
(`MAX_SIGMA_COMPONENT_K=7K`, vent-path, `exclude_zones`, Reglas D, cloud mask,
pisos VRP) era remediación de un drift previo, no causa raíz. Acumulados,
anulaban la diferenciación summit/scene de MIROVA. **Volver a meter ese tipo
de parche NO está autorizado** — primero pasar por las 3 preguntas en MISSION.md.

## Documentación bibliográfica (source of truth — leer ANTES de buscar online)

**PDFs papers + síntesis viven en `VRP Chile/documentacion/`** (NO en el Vault).

### `documentacion/BIBLIOGRAPHY_SYNTHESIS.md` — SOURCE OF TRUTH bibliográfico

429 líneas con síntesis algoritmo + umbrales + tablas canónicas + sistemas
competidores. Creado S13 (2026-04-18). Cobertura **30/60 PDFs (54%)**.
**Antes de investigar cualquier paper MIROVA, leer este doc primero.**
Contiene:
- Algoritmo Coppola 2016a SP426.5 completo (ETI cuadrático + Tests 1/2/3 + second-pass)
- Tabla canónica umbrales por sensor (MODIS / VIIRS750 / VIIRS375)
- Sistemas competidores (HotLINK USGS AVO +22% recall, MOUNTS, NHI, V-STAR, etc.)
- MIROVA OSF v2.5 stats (615k filas globales, 5211 Villarrica refs)
- Coppola 2025 book chapter resumen

### `documentacion/` archivos clave (paper completo / texto extraído)
- `sp426.5.pdf` + `sp426_5.txt` — Coppola 2016a SP426.5 (algoritmo MIROVA core)
- `THESIS_MASSIMETTI.pdf` + `_mm_ch[2,4,5]_*.txt` — tesis con detalle VIIRS adaptation
- `coppola2024_chapter.txt` — Coppola 2025 book chapter "Thermal Monitoring"
- `feart-12-1345104.pdf` — HotLINK (Saunders-Shultz 2024)
- `Advancing_Volcanic_Activity_Monitoring_A_Near-Real.pdf` — Di Bella 2024 RSDF
- `campus2024_extracted.txt` — Campus 2024 Vulcano VIIRS 375m
- `coppola2021thermal.txt` — Coppola 2021 thermal monitoring

### Workflow obligatorio ANTES de investigar papers (lección S36 fallo)

1. `find "VRP Chile/documentacion/" -iname "*<topic>*"` — verificar PDF disponible local
2. Leer `BIBLIOGRAPHY_SYNTHESIS.md` sección correspondiente
3. Si paper NO está sintetizado → leer PDF directo o `.txt` extraído antes de
   buscar online
4. **NUNCA** dar por sentado que un paper no está disponible sin haber buscado
   en `documentacion/` primero
5. S36 fallo: yo busqué Coppola 2016a SP426.5 online cuando el PDF estaba
   en `documentacion/sp426.5.pdf` desde abril. **Costo: 1h investigación
   innecesaria + falsa conclusión "no podemos implementar sin paper"**.

## Integración con el vault Obsidian (secundario — notas resumidas)

Las **notas resumidas** de papers viven en `C:\Users\nmend\OneDrive\Escritorio\claude\Vault\`.
Los PDFs completos están en `documentacion/` (ver arriba). El Vault es útil
para cross-linking con conceptos volcanológicos pero NO contiene los PDFs.

- **Procesar papers nuevos**: ver `..\..\Vault\CLAUDE.md` sección "Workflow de
  procesamiento de papers". Útil para crear notes resumidas en Vault, NO para
  consultar contenido completo.
- **Índice de proyectos** (cross-project linking): `..\..\Vault\00_Meta\proyectos.md`.
- **Convenciones del vault** (kebab-case, frontmatter `ai_generated`/`confidence`/
  `explored`, links `[[]]`, tags jerárquicos): ver `..\..\Vault\CLAUDE.md`.

## Reglas científicas (no negociables)
- **VRP MIR (Wooster)** por sensor, coeficientes **empíricamente validados S14
  contra MIROVA v2.5 OSF (error ≤0.17% sobre 48,360 filas)**:
  - MODIS 1 km (B21/22): `k = 18.9 × A_pix(1e6)` = **18,900,000** (`WOOSTER_COEFF=18.9`)
  - VIIRS M-band 750m (M13): `k = 1.97×10⁷ × A_pix(km²)` = **11,081,250** (`WOOSTER_COEFF=19.7`)
  - VIIRS I-band 375m (I4): `k = 18.0 × A_pix(140625)` = **2,531,250** (`WOOSTER_COEFF=18.0`)
  - MIROVA usa **A_pix nadir fijo** (sin corrección zenithal) para los 3 sensores.
  - NO usar Di Bella 2024 k=2.48×10⁷ para VIIRS 375m — no reproduce OSF (empírico).
- **VRP TIR (I05)**: Stefan-Boltzmann puro (`σ = 5.67×10⁻⁸`). **Drift D3 RESUELTO S17**: Aveni 2024
  RSE (TIRVolcH, mismo grupo MIROVA) usa Stefan-Boltzmann igual que Coppola 2024 y nuestro código.
  La Eq.9 con k_TIR=60.17 de Aveni 2025 GRL es investigación no adoptada operacionalmente. Referencia
  correcta ahora: Coppola 2024 cap Springer Eq.16 + Aveni 2024 RSE Eq.5. Ver `docs/DRIFTS_S17.md`.
- **NTI**: umbral 3σ sobre background, mínimo 0.005. **DRIFT D2 S17**: ningún paper autoritativo
  respalda 3σ uniforme. Coppola 2016a Tabla 1 dice 5σ summit / 10σ scene / 15σ diurno para MODIS.
  Di Bella 2024 §3.3 dice VIIRS 12σ noche / 8σ día. Test A/B pendiente S18 — ver `docs/DRIFTS_S17.md`.
- **Kernel 8-vecinos dNTI contextual**: `np.mean` aritmética (Coppola 2016a + Campus 2024). **Drift D1
  RESUELTO S17** — previamente usábamos `np.median` sin respaldo documental.
- **MIR solo nocturno** (contaminación solar diurna).
- Bandas: MODIS 21/22 (3.929/3.959 μm) + 31 (11 μm TIR),
  VIIRS I04 (3.74 μm) / I05 (11.45 μm), VIIRS M13 (4.05 μm) / M15 (10.76 μm).
- Constantes físicas **exactas** de los papers, nunca aproximar. Citar paper en cualquier cambio metodológico.
- Si dudas de un método con datos geofísicos, **dilo** — nunca adivines.

## Reglas geométricas S14 (MIROVA-equivalent)
- **`radius_km = 25 km` uniforme** para volcanes chilenos — replica grilla
  MIROVA UTM 51×51 km (radio inscrito 25.5 km).
- **`inner_radius_km` por volcán** (valores oficiales MIROVA de los KML):
  | Volcán | inner | Volcán | inner |
  |---|---|---|---|
  | Lastarria | 3 | Lascar, Isluga, NdC, Llaima, Villarrica, Chaiten | 5 |
  | Planchón-Peteroa | 3 | Tupungatito | 7 |
  | Copahue | 4 | PuyehueCordonCaulle | **20** |
- **Esquema dual "detectar amplio + clasificar visual"**: detecciones dentro
  de `inner_radius_km` → `distance_class="summit"` (rojo, anomalía real).
  Fuera → `"far"` (gris, posible lejana). **No se filtran**, se clasifican.
- **Campo unificado `final_hotspot_lat/lon/dist_km`** con fallback
  eruption→vent. El dashboard y las auditorías usan **solo** este campo, no
  `hotspot_*` o `vent_hotspot_*` por separado.

## Reglas operacionales S14 (aprendizajes)
- **A1. Calibración empírica > derivación teórica**: cuando haya data pública
  del mismo grupo (OSF, Zenodo), calcular coeficientes empíricos antes de
  confiar en un número de paper. Resolvió en 1 min discrepancia Di Bella vs
  Laiolo que ocupó un mes de discusión teórica.
- **A2. Diagnósticos paralelos antes de reprocesos caros**: agotar análisis
  sobre data ya en disco antes de descargar más. Paso 0+1a+diagnósticos
  A/B/D resolvieron 80% de dudas sin fetch. Solo entonces tiene sentido
  reprocesar.
- **A3. Campos "distance" en schema deben documentar desde qué punto miden**:
  `hotspot_dist_km` se medía desde `volcano_lat/lon` (centro) no desde el
  vent. Ahora `final_hotspot_dist_km` unifica y documenta.
- **A4. MIROVA es arquitecturalmente más simple que lo que creíamos**:
  no hay máscaras geométricas ni radios adaptativos. Es grilla UTM 51×51 +
  NTI/ETI/contextual (Coppola 2016a) + clasificación visual post-detección.
  La complejidad está en los umbrales, no en la geometría.
- **A6. Trazar callers cuando concluyas comportamiento (S21)**: leer firma+cuerpo
  de un callee NO basta. El caller puede transformar args. S21 leí
  `process_viirs.py:518` (vent_dist=haversine(vent_lat,...)) y concluí "vent-path
  usa vent_lat nominal" — falso: `run_pipeline.py:220` pasa eff_vent_lat de
  `get_effective_vent()` que ya fallbackea a mirova_center. ~30 min perdidos
  en hipótesis ya implementada S15.
- **A7. Schema gaps: "no calculado" ≠ "calculado pero no persistido" (S21)**:
  cuando un campo aparece None en JSONs, ANTES de proponer "agregar cómputo"
  verificar si la variable local YA se calcula y solo falta el key en el return
  dict. H_S21_11: process_viirs.py calculaba `std_bg_i04`, `threshold_mir`,
  `nti_std` — solo no los retornaba. Fix de 6 líneas, no 60.
- **A5. Los valores MIROVA oficiales (KML, OSF) son datos no opiniones**:
  usarlos tal cual es más defendible que inventar umbrales. Solo divergir
  con experimentos propios y en el perfil `experimental`, no en
  `mirova_equivalent`.
- **A8. Verificar data fresca antes de asumir problema (S25)**: cuando un
  handoff o CLAUDE.md afirme "X tiene problema Y" (ej: "Villarrica recall
  0%"), reprocesar primero un día con código actual sobre profile destino
  antes de proponer fix. Costo verificación = 5-15 min. Costo de saltarla:
  S25 implementó Test 1 Coppola 2015 (~4h) que resultó redundante porque
  data stale en `data/mirova_equivalent/Villarrica.json` reportaba 4%
  recall mientras código S25 daba 94% real.
- **A9. Verificar afiliación de paper antes de citarlo como autoridad MIROVA
  (S26)**: por ~10 sesiones citamos Di Bella 2024 §3.3 (12σ VIIRS noche)
  como "thresholds MIROVA". Di Bella es del grupo INGV Catania (sistema
  RSDF), NO MIROVA. Auditoría S26 detectó 13 papers más confundibles
  (Catania + CNR Potenza). Regla canonical:
  - **MIROVA = Torino + Firenze + Sapienza Roma**: Coppola, Laiolo,
    Massimetti, Campus, Aveni, Cigolini.
  - **NO MIROVA aunque sea italiano**: INGV Catania (Del Negro, Corradino,
    Di Bella, Torrisi, Cariello, Amato, Malaguti) → sistemas RSDF/V-STAR/
    FastVRP/CNN. CNR-IMAA Potenza (Marchese, Pergola, Genzano, Filizzola)
    → sistema NHI.
  - Lista completa en `~memory/reference_papers_mirova_canonical.md`.

## Reglas operacionales S60-S62 (aprendizajes adicionales)
- **A10. Audit vs MIROVA usar `pc.vrp_mw` (NO `record.vrp_mw`)**: `record.vrp_mw` es sum
  scene-wide de todos hot_pixels; `pc.vrp_mw` (primary_cluster.vrp_mw) es solo cluster summit
  = lo que MIROVA reporta. Dashboard (frontend/index.html:680) usa pc.vrp_mw. Audits con
  campo equivocado ocultaron problemas: Lastarria 1.04× → real 7.67×, Llaima 1.01× → real
  11.82×, PCC 52.77× → real 6.9×.
- **A11. Universo MIROVA = CONS + OCR**: `registro_vrp_ocr.csv` (Mirova-v1) tiene 457
  ALERTA_TERMICA_OCR adicionales (~2-3× más data que solo consolidado). OCR es COMPLEMENTO
  (no validación) — MIROVA publica en `latest.php` (CONS) y otros datos solo en imágenes
  por vol (OCR extrae). `FALSO_POSITIVO_OCR` es etiqueta del scraper Nicolás (no MIROVA),
  significa que el OCR no pudo confirmar visualmente.
- **A12. Patrón térmico Tier A — qué necesita kernel-bg**: vols con ΔT mediano (t_max - t_bg)
  <12K en régimen Muy Bajo + ring background frío sufren ΔL inflado en Test 1 integrated-ROI
  → magnitud 8-15× MIROVA. Vols con ΔT >20K (Lascar 21.6K, Isluga ~20K) calibrados
  naturalmente sin fix. Fix kernel-bg (Coppola 2024 L1129) reduce 70-90% del gap en Muy
  Bajo (validado Villarrica/PP S61).
- **A13. `Distancia_km` MIROVA Villarrica fija 0.84 km = idiosincrasia**: MIROVA mide dist
  desde coord Smithsonian GVP nominal (no centroide variable). Smithsonian Villarrica
  (-39.42,-71.93) está a 0.85 km del cráter actual (-39.420292,-71.939908). NO afecta
  nuestra magnitud VRP. Otros vols con cráter grande sí muestran dist variable. NO
  interpretar como bug.
- **A14. Nombre vol en CSV — TODAS las variantes**: el scraper Mirova-v1 normaliza algunos
  nombres. `PlanchonPeteroa` (sin guión), `Puyehue-Cordon Caulle` (con guión), `Nevados de
  Chillan` (espacios). S60 perdió 46 ALERTAS PlanchonPeteroa por buscar con
  `Planchon-Peteroa`. Siempre verificar variantes.
- **A15. Workflow timeout vs duración**: reproc Villarrica 90 días tarda ~175 min, timeout
  default 110 min era too tight (PR #68 lo extendió a 300 min). Patrón seguro:
  `timeout >= duración_esperada × 1.3`.
- **A16. Pre-escribir audit scripts mientras corren workflows**: patrón productivo S61-S62.
  Cuando audit script + bloque arranque + hipótesis log entries están pre-escritos, el
  cierre post-workflow toma <15 min en lugar de 1-2h. Workflow de 3h se "amortiza" haciendo
  trabajo paralelo offline.
- **A17. CSV consolidado del scraper Nicolás actualizable**: el CSV en
  `data/mirova_reference/mirova_v1_snapshot/` tiene fecha de snapshot. Para audits con data
  fresca: descargar latest desde
  `https://raw.githubusercontent.com/MendozaVolcanic/Mirova-v1/main/monitoreo_satelital/registro_vrp_consolidado.csv`
  y reemplazar el local. Misma URL para `registro_vrp_ocr.csv`.
  - **S73 dehardcode (root del repo)**: `frontend/diario.html` y
    `.github/workflows/pages-deploy.yml` ya NO referencian el archivo fechado.
    Consumen `latest_consolidado.csv` (copia del CSV más reciente en root del
    repo). **Cuando llegue un nuevo consolidado**: `cp <nuevo>_registro_vrp_consolidado.csv
    latest_consolidado.csv`, `git add -f latest_consolidado.csv && git commit && git push`.
    El frontend tiene fallback al snapshot fechado `01_05_2026_*.csv` si `latest`
    no existe (deploys históricos siguen funcionando). Los experimentos
    históricos en `experiments/` mantienen el path fechado adrede (snapshot
    reproducible).
- **A18. Preview offline NO predice cluster selection real** (S62 lección dura):
  para parámetros que afectan `cluster_hotspots(vent_anchored)` o cualquier path
  de selección (inner_radius_km, exclude_zones, vent_radius_km), validar SIEMPRE
  con reproc REAL (workflow GH Actions). Preview offline filtra records ya
  seleccionados con el parámetro viejo, pero el reproc real rerunnea cluster
  selection desde cero — puede elegir cluster DIFERENTE. S62 PCC: preview offline
  predijo inner=7 → ratio 1.86× pero reproc real dio 3.64× (peor que baseline).
- **A19. Patrón térmico no es universal: Tupungatito refuta kernel-bg** (S62):
  Lastarria (ΔT 12K, ring desierto frío) responde a kernel-bg = 6.78× → 1.07×.
  Pero Tupungatito (similar ΔT pero ring **glaciar**) EMPEORA con kernel-bg
  10.37× → 18.46×. Mecanismo opuesto: vecinos directos del hot pixel en glaciar
  son "warm relativo" para escena gigante (no pure ice) → L_bg local sube → ΔL
  no se reduce → magnitud no cura. Decisión per-vol DEBE validar empíricamente
  con A/B, NO extrapolar de patrón ΔT solo.

## Reglas operacionales S70 (aprendizajes A20-A26)
- **A20. R2 con centroide NO aplica a anomalías difusas** (S70-1 T4 PCC):
  el método R2 retroactivo (centroide ponderado top-N pixels TIF) asume cluster
  focal puntiforme. Para vols con anomalía extendida (lacolito PCC ~707 km²,
  domos extensos, intrusiones) el centroide del campo sin foco no representa
  cluster discreto — drift resultante es artefacto del método (PCC 9.77 km),
  NO error del pipeline. Validar adopción por **magnitud agregada** (ratio
  per-record vs agregado S6X) + **confirmación geométrica** (cluster nuestro
  está EN la zona difusa, ej. PCC 5.6-8.5 km del vent coincide con MIROVA
  @ 7.73 km). Ver D7 en MIROVA_DIVERGENCES.md.
- **A21. Bandas gates R2 son régimen-dependientes** (S70-1 cross-vol):
  banda estricta `[0.5-2.0]` ratio + drift `<2 km` (Lastarria-style) solo
  aplica a **Tier A Alto** (ΔT >20K) con cluster focal puro. **Tier A Muy Bajo**
  (Chaiten/Villarrica/PP, ΔT <12K) requiere banda revisada con drift `<3 km`
  porque la cola térmica del halo difuso del lava lake/domo es físicamente
  real (no error del cluster). **Vols no focales**: R2 no aplica.
  Doc operacional: `docs/R2_GATES_BY_REGIME.md`.
- **A22. PP es bimodal en cluster selection** (S70-2 T1 multi-caso N=7):
  pipeline a veces aísla cráter Peteroa (Modo A ratio ~1×), a veces se va al
  halo regional del complejo multi-cráter Planchón+Peteroa+Azufre (Modo B
  ratio 10×). Mediana N=7 dio 2.08× pero **varianza alta** = single record es
  ruidoso. Para verdict robusto Tier A Muy Bajo: **multi-caso (3-5 ALERTAs)** +
  reportar moda + frecuencia, no single record. Mismo mecanismo que Tupungatito
  43% residual. Pendiente arquitectural S71+.
- **A23. Path D dNTI ctx tiene FPs sistémicos en cirrus alto** (D9 ABIERTO, S70-2 T4):
  cuando `t_bg_k <260K` (cirrus alto frío) el path D dNTI contextual puede
  dispararse falsamente e inflar `pc.vrp_mw` **20-150×** vs ground truth. Trigger
  mecánico: kernel local 8-vecinos sobre cirrus uniforme da `dNTI` artificial
  altísimo aun sin actividad volcánica real. **Co-validación con BT path o
  NTI absoluto requerida** antes de adoptar record path D-only en condiciones
  atmosféricas frías. Fix S71+: papers-first (Coppola 2016a §SP 426.5,
  Campus 2024, Coppola 2024) → si no resuelven, A/B test 3 alternativas
  (gate atm `t_bg ≥260K`, co-validación obligatoria, cap magnitud).
- **A24. TIF MIROVA NO es VRP per-pixel sumable** (D6, S70-0 T3):
  el TIF "Last" descargado público de mirovaweb tiene ~17,911 pixels positivos
  sumando ~1680 MW pero el header MIROVA reporta solo "VRP: 0.2 MW @ 9.7 km".
  El TIF es **producto de visualización del campo de radiancia** — el "VRP
  reportado" viene de **selección de cluster específica**, no suma del TIF.
  **No usar suma de pixels TIF como ground truth de magnitud**. El método R2
  S69 verdadero (centroide ponderado top10 pixels <3km del vent) sí valida
  contra el cluster MIROVA específico cuando es focal.
- **A25. Worktrees Claude no contaminan main pero filesystem local queda desfasado**:
  sesiones Claude con `isolation: worktree` corren en branches aislados
  (`claude/sNN-*`) que mergean directo a `origin/main` sin tocar el filesystem
  local de Nicolás. Resultado: `git log main` local puede mostrar S33 mientras
  `git log origin/main` ya está en S69. **Hacer `git fetch origin --prune` al
  inicio de cada sesión** para detectar trabajo nuevo. NO asumir que `git log
  main` refleja origin/main. Si hay desfase grande: crear worktree limpio
  sobre `origin/main` para la sesión (`git worktree add ../proyecto-sNN
  origin/main`) y dejar el local viejo como red de seguridad.
- **A26. Calidad sobre tokens** (feedback Nicolás S70-2 cierre):
  **gastar los tokens que sean necesarios para hacer buen trabajo**. NO
  optimizar costo si compromete calidad. Las herramientas se usan cuando
  aportan valor, no se recortan por presupuesto:
  - **Subagentes**: usar libremente para investigaciones independientes,
    paralelización, dispatching-parallel-agents. El costo de un fix mal
    hecho > costo de una sesión cara.
  - **Skills**: invocar todas las que apliquen — `superpowers-brainstorming`,
    `systematic-debugging`, `writing-plans`, `verification-before-completion`,
    `test-driven-development`. Regla meta de CLAUDE.md global ("si dudás,
    invocala igual") se mantiene.
  - **Brainstorming + design docs** antes de adopciones metodológicas:
    paso ineludible. Aunque tome 30 min y muchos tokens, evita refactors
    posteriores que cuestan 10×.
  - **Auditoría integral** cuando Nicolás lo pide: despachar 5-7 agentes
    en paralelo cubriendo todos los ejes (misión, código, docs, git,
    ground truth) es la forma correcta. No recortar a 2 agentes por
    economía.
  - **Verificación pixel-level + audit independiente** antes de declarar
    "listo": obligatorios en adopciones (regla S33). NO saltarlos.
  - **Persistencia in-vivo**: documentar hallazgos INMEDIATAMENTE en docs
    cuando aparecen, no al cierre. La memoria viva vale los tokens.

  Costos que SÍ vale evitar (no comprometen calidad):
  - Re-leer un archivo que ya leíste en la sesión sin que haya cambiado.
  - Loops de polling con `sleep` cuando se puede usar `run_in_background`
    + notificación automática.
  - Tool output gigantes pegados al contexto (snapshots, listados largos):
    delegar a subagente con pedido de resumen, o escribir a JSON.
  - Decisiones obvias preguntadas innecesariamente al usuario.

- **A35. Notas Vault `ai_generated: true` necesitan verificación verbatim para
  valores numéricos críticos** (S73 F2.8): cuando un threshold, fórmula o
  constante entra a un test/PR/código, cotejar contra el PDF original del paper
  antes de citarlo como autoridad. La nota Vault `wooster2003fire.md` decía
  "Saturación MODIS B21 ~57.6 W/m²/sr/µm como criterio operacional" — pero el
  PDF Wooster muestra que ese 57.6 W es **valor de ejemplo de Figure 4** (un
  caso que YA satura MODIS, BT=473 K), no el threshold mismo (que es BT≈450 K
  per Wooster, actualizado a 500 K por Coppola 2025 Cap.11). El costo de la
  confusión sería 50 K de drift en el umbral del fix.

  **Jerarquía de autoridad cuando hay conflicto**:
  1. UserGuide oficial del sensor (Toller & Isaacman 2025 MODIS L1B C7, VIIRS
     L1B UserGuide Aug 2021) — autoritativo absoluto para sentinels / LUT max.
  2. Paper canon-MIROVA reciente (Coppola 2025 Cap.11 Springer) — autoritativo
     para thresholds operacionales actualizados (vs valores nominales históricos).
  3. Paper algorithm-MIROVA histórico (Coppola 2016, Wooster 2003) — referencia
     fundacional para mecanismos y rangos.
  4. Notas Vault `ai_generated` — síntesis útil para ideas, NO para valores
     numéricos sin verificación cruzada.

- **A36. sec³(θ_z) scan-angle elongation puede multiplicar discrepancias
  factor 1-5×** (S73 F2.8): MODIS pixels off-nadir tienen área efectiva mucho
  mayor que nominal 1km². Para sensor angle θ_z = 50° → factor 3.74. Cualquier
  análisis manual o script de verificación que ignore esto produce
  discrepancias factor 1-5× (S73: cálculo inicial dio 185K MW, real fue 695K).
  El pipeline ya lo aplica via `modis_pixel_areas()` con sec³ correction;
  análisis manuales/audits ad-hoc también deben.

- **A37. VIIRS L1B y MODIS L1B usan esquemas distintos para saturation flagging**
  (S73 F2.8 audit cross-sensor): MODIS reporta `SI=65533` sentinel para
  "Detector saturated" (Tabla 5.6.1 L1B C7 UserGuide), parte de un esquema
  general donde `SI > 32767 = invalid` (14 sentinels en 65500-65535). VIIRS NO
  usa sentinel uint16 para saturation: clampea la radiancia al "Reported Range"
  value y setea bit-2 (=4) del SDS de quality flags separado (Tabla C.1 L1B
  UserGuide Aug 2021). Code que asume uniformidad de esquema entre sensores
  produce gaps de protección distintos. **Regla operacional**: cuando trabajés
  con un sensor L1B nuevo, leé el UserGuide específico de ese sensor — NO
  extrapoles de MODIS asumiendo que VIIRS hace lo mismo.

- **A38. Tag git defensivo antes de cleanup destructivo** (S73 data/_*/ audit):
  cualquier `git rm`/borrado masivo (>10 archivos o >50 MB) requiere PRIMERO:
  (a) inventario clasificatorio en `docs/<F##>_<scope>_INVENTORY.md` con
  recomendación archivar/conservar por item, (b) `git tag -a pre-<scope>-cleanup
  -m "snapshot defensivo..."` + `git push --tags`, (c) confirmación explícita
  del usuario si tiene dudas. Recovery: `git checkout <tag> -- path/` o
  navegar el tag en GitHub.com UI. Costo: 1 comando. Beneficio: recovery 100 %
  si dudas surgen después. **Anti-pattern S73**: casi lanzo subagente para
  `git rm` masivo data/_*/ sin pensar bien beyond-MIROVA value — Nicolás me
  paró. La regla nació de ahí.

- **A39. Claude es responsable de mergear PRs cuando CI/review OK** (S73): NO
  esperar a Nicolás. Verificación pre-merge obligatoria:
  (a) `gh pr view <N> --json mergeStateStatus,statusCheckRollup,reviewDecision`,
  (b) si `mergeStateStatus=CLEAN` y checks pasados (o no requeridos) y tests
  locales 0 regresiones → ejecutar `gh pr merge <N> --squash --delete-branch`
  (o el strategy del repo), (c) si hay conflicts/fails → reportar y pedir
  instrucciones, NO mergear a ciegas. Excepción: PRs con cambios de alta
  criticidad (data destructiva, security, breaking changes) → pedir
  confirmación explícita aunque CI esté verde.

  **Workaround S74 cuando `gh pr merge` falla porque `main` está en otro
  worktree**: `gh api --method PUT repos/<owner>/<repo>/pulls/<N>/merge -f
  merge_method=merge`. Esto bypassa el local checkout y mergea via GitHub API
  directo. Probado funcional en PRs #133-#142.

- **A40. Para queries bibliográficas dirigidas, manual `investigacion` >
  skill orchestrators** (S73 4-way A/B/C/D). OpenAlex permite barrer toda la
  biblio de un autor por ID con metadata Crossref-verified. Skills tipo
  `deep-research` orquestan pero usan WebSearch como backend (parafrasea DOIs
  → riesgo "vibe citing"). Perplexity Academic vía Chrome genera synthesis
  bien estructurada pero **0 papers nuevos específicos**.

  **Combo óptimo por use case**:
  - **Discovery dirigido**: A (manual investigacion) + C (WebSearch arxiv
    pre-prints)
  - **Synthesis writing (paper P5)**: D (Perplexity Academic vía Chrome) o B
    (`deep-research` full mode)
  - **Verificación post-discovery**: `citation-audit` skill (no probado, pre-
    submission)

- **A41. `Claude_in_Chrome` MCP funciona para Perplexity Pro con sesión
  activa** (S73). Workflow validado:
  1. `list_connected_browsers` → `select_browser <deviceId>`
  2. `tabs_context_mcp createIfEmpty:true` → tab disponible
  3. **Navegar directo URL pattern**:
     `https://www.perplexity.ai/search/new?q=<URL_ENCODED>&sources=scholar`
  4. `get_page_text` para extraer respuesta

  **Caveats**:
  - Textbox de Perplexity es `<div contenteditable>` (no `<input>`/`<textarea>`)
    → `form_input` falla con "DIV not supported". Usar `computer` action `type`
    con `ref` post-click, **o URL navigate directo (más confiable)**.
  - No requiere `PERPLEXITY_API_KEY` env var — usa cookies de la sesión Chrome
    activa de Nicolás.
  - El MCP `perplexity` server-side configurado en `~/.claude/settings.json`
    requiere `PERPLEXITY_API_KEY` env var — si no está seteada, fallback a
    Chrome MCP es la opción.

- **A42. GH Actions `workflow_dispatch` puede rechazar workflows con HTTP 422
  incluso post-merge a default branch** (S73 F2.8.f). Workarounds intentados:
  (1) extract Python heredoc a script externo (PR #134, no resolvió),
  (2) rename del archivo yml para forzar nuevo workflow ID (PR #138, no resolvió),
  (3) yml minimal scratch desde cero (PR pendiente S74). El parser puede ser
  más estricto de lo documentado — posibles culprits: encoding (BOM/CRLF/UTF-8
  con tildes en comments), formato `on:` multi-líneas, indent específico.

  **Si falla post-3-intentos**: el fix mergeado a main sigue siendo aplicado
  por NRT cron automático. El reproc histórico empírico es nice-to-have, no
  bloqueante operacional.

- **A44. Worktrees dedicados por subagente paralelo** (S75 cierre, 3 race
  conditions documentadas): cuando lances 2+ subagentes en background que
  toquen git en el mismo repo, cada uno debe trabajar en su propio worktree.
  Mecanismo: `git worktree add ../VRP-Chile-s76-<task> origin/main` previo
  al spawn. Razón: `git checkout -b` cambia la branch global del worktree
  compartido; otros procesos atrapan branch incorrecta. Mitigaciones
  reactivas (stash + cherry-pick + branch v2) funcionan pero comen tiempo
  y carga mental. Caveat espacio: cada worktree es checkout completo
  (~hundred MB). Para disco al 98% considerar shallow clone o sparse-checkout.
  Cleanup post-merge con `git worktree remove`.

- **A45. Tag defensivo + confirmación explícita son OBLIGATORIOS antes de
  modificar pipeline NRT operacional** (S75 lección aplicada por Nicolás):
  refuerzo de A38+A39 cuando el target es `pipeline/process_modis.py`,
  `pipeline/process_viirs.py`, `pipeline/process_viirs_mod.py`,
  `pipeline/store.py` o cualquier `pipeline/profiles/mirova_equivalent.yaml`.
  Pasos no-opcionales:
  1. `git tag pre-s<NN>-<feature>-integration <sha>` antes del primer edit
     y `git push origin <tag>`.
  2. Pedirle a Nicolás confirmación explícita aunque los tests baseline
     estén verdes y el plan parezca seguro.
  Razón: NRT cron corre 12 veces/día sobre 11+ volcanes. Un bug que pasa
  tests pero rompe semántica VRP se replica a 132+ records antes de
  detectarlo. Lección concreta S75: Nicolás preguntó *"no tienes que salvar
  la configuración actual antes? eso no sería más conservador?"* justo
  cuando yo iba a empezar A2 — fue el sanity check correcto, y por eso
  hoy existe el tag `pre-s75-vrptir-a2-integration` que respalda PR #158.

- **A46. Schema asimétrico hotspot single vs primary_cluster es vector de bugs
  sistémicos** (S77, lección F47 H4): cuando un record tiene dos representaciones
  del "punto caliente" computadas por paths distintos del pipeline (e.g.
  `hotspot_*` del pixel hottest scene-wide vs `primary_cluster.*` vent-anchored),
  cualquier gate posterior que use UNA sola de las representaciones para tomar
  decisiones binarias (rollup vs zero-out) es candidato directo a producir
  resultados incoherentes con la otra. El bug F47 H4 hizo invisible ~400 records
  VRP en 11 Tier A durante meses por exactamente este patrón.
  - **How to apply**: cuando agregues una nueva representación del hotspot al
    schema (S20 vent_hotspot, S14 final_hotspot, S27 primary_cluster, S25 Test1
    integrated, etc.), audit los gates downstream que evalúen otras
    representaciones del mismo concepto. Si un gate puede dar VRP=0 con cluster
    válido cerca, es un F47-style bug latente.
  - **Etiqueta diagnóstica**: el fix S77 introdujo `final_hotspot_source =
    "cluster_rescue"` cuando el cluster vent-anchored gana al pixel single far.
    Auditorías posteriores pueden contar `records con source='cluster_rescue'`
    para medir impacto del bug y exposure.

- **A47. Reproc paralelo sobre `data/mirova_equivalent/` corrompe JSONs por
  race condition** (S77, lección 2026-05-25): 4 procesos `run_pipeline.py`
  concurrentes sobre el mismo volcán o sobre directorio compartido produjeron
  JSON parse error "Expecting ',' delimiter" en Tupungatito.json (escritura
  interleaved del mismo archivo). Reglas:
  - **Reproc local NUNCA paralelo** sobre el mismo `data_subdir`. Usar
    `for V in $VOLS; do python ... --volcano $V; done` (loop bash secuencial)
    dentro de UN solo background process.
  - **Paralelo sí seguro** cuando cada proceso usa profile distinto con
    `data_subdir` aislado (patrón A/B test S24/S25 — perfiles
    `_f46_disabled/_enabled` con dirs distintos).
  - **GH Actions matrix NRT** ya tiene `max-parallel:1` global por workflow,
    cron cada 2h, sin race observado — el race es local solamente.
  - Si race ocurre y JSON queda corrupto: `git checkout origin/main -- data/mirova_equivalent/<vol>.json` restaura.

- **A48. Subagentes pueden inventar regex/heurísticas que parecen razonables
  pero rompen la convención real del proyecto** (S77, lección 2026-05-25):
  el subagente F49 audit comprehensivo PR #196 escribió
  `sensor_bucket_ours(sensor)` con regex `"375" in s` ó `"_I" in s` para
  detectar VIIRS I-band. PERO la convención real es:
  - `VIIRS_SNPP`/`VIIRS_NOAA20`/`VIIRS_NOAA21` (sin sufijo) = I-band 375m.
  - `VIIRS_*_750` = M-band 750m.
  - El regex del subagente clasificó nuestros I-band como M-band → audit
    concluyó "pipeline no procesa VIIRS375" (FALSO). Conclusión #1 del PR
    inválida. Corregido en addendum v2 PR #197.

  Mitigaciones aplicables a sesiones futuras con subagentes:
  - **Validar convención del proyecto antes** de inventar regex/heurísticas:
    `grep ^sensor data/mirova_equivalent/*.json` o ver `Counter(r['sensor'])`.
  - **Cross-check conclusión "alto impacto"** del subagente con sanity test
    rápido antes de aceptarla. Si dice "pipeline no procesa X", un
    `python -c "import json; ..."` debería confirmarlo en 30 segundos.
  - Subagentes son útiles para investigaciones de alto volumen pero NO
    son source-of-truth metodológica. Sus regex/heurísticas reflejan
    educated guess, no convenciones verificadas.

- **A49. Insertar código entre dos funciones no debe comer el `return`
  final de la función anterior** (S80, lección regresión `compute_bg_stats`):
  el commit `a73775cd` (F66 Task 1) insertó el helper
  `apply_f66_consistency_gate` inmediatamente después de
  `compute_bg_stats`, borrando accidentalmente la línea
  `return t_bg, std_bg, n_bg` final. Como el return temprano por
  `n_bg < min_bg_pixels` SÍ retornaba tupla, la función "parecía
  funcionar" pero retornaba `None` implícito en el camino exitoso.
  `process_modis.py:316` desempaca `None` → `TypeError`. Pasó 1 sesión
  sin detección porque S79 etiquetó los 6 tests fallidos como
  "pre-existing" sin verificar contra `origin/main`.

  Mitigación: antes de commitear cualquier `Edit`/`Write` que **inserte
  código entre dos estructuras existentes** (funciones, clases, bloques),
  verificar con `git diff` que la última línea de la estructura anterior
  y la primera de la siguiente siguen intactas. Para inserciones >20
  líneas, usar `Edit` con `old_string` incluyendo 5 líneas de contexto
  antes y después.

- **A50. "Pre-existing fails" requiere verificación cross-source con
  `origin/main`** (S80, complemento A49): antes de etiquetar un test
  fallido como "pre-existing" (sugiriendo bug histórico), correr
  `git show origin/main:<archivo>` y comparar el cuerpo de la función
  afectada. Si la función fue modificada en algún commit del branch
  actual, es candidato a regresión. Costo verificación = 30 segundos;
  costo de no verificar = 1 sesión perdida (S79 S80).

- **A51. Auditoría completa cada 20 sesiones** (S80, regla M8 de
  `docs/META_RULES_S80.md`): la velocidad de cambio del proyecto
  (117 PRs en S70–S80) supera la capacidad de `MEMORY.md` para
  trackear. Cada 20 sesiones ejecutar el protocolo de 5 subagentes
  paralelos (inventario sesiones / drifts+hipótesis / git activity /
  profile flags / estado operacional) y producir `docs/AUDIT_S<N>.md`.
  Si detecta >3 contradicciones cross-source, **pausar features
  nuevas y consolidar primero**.

- **A52. Worktrees no-main pueden estar atrasados (siempre `git fetch +
  pull`)** (S80, lección worktree `VRP-Chile-s70/` en branch huérfano):
  el worktree canónico declarado en CLAUDE.md estaba en branch
  `work-s78-bloque-arranque-s79` sin remote, mostrando 17 workflows
  reproc-* activos cuando `origin/main` ya los había archivado (PR
  #217). Confundió a un subagente. Política: al entrar a worktree,
  verificar siempre `git fetch origin --prune && git log --oneline
  HEAD..origin/main`. Si la branch local no es `main` y diverge por
  >10 commits, **no asumir que el estado del worktree refleja el
  proyecto**.

- **A53. Cap PRs/sesión y persistencia in-vivo agresiva** (S80, regla
  M1+M2): pasado **12 PRs por sesión** (cap soft) Claude debe pausar
  y proponer consolidación + actualización `MEMORY.md` antes de seguir
  abriendo PRs. Pasado **20 PRs** (cap hard) bloquear merges hasta
  ejecutar `SESSION_CLOSE_CHECKLIST` y revisar el batch. Excepción:
  cleanups masivos de cosas equivalentes (ej. archive workflows),
  documentar en el PR. Y todo hallazgo no trivial (schema gap, source
  externa, regresión, default operacional cambiado) → persistir
  **inmediatamente** en doc/memoria, no esperar al cierre.

- **A54. El gap precisión vs MIROVA es mayormente artefacto metodológico,
  no bug del pipeline** (S86 auditoría profunda Subagentes E+F+G):
  composición real de los "FPs" del cruce estricto contra MIROVA CONS:
  49.1% MIROVA SÍ publicó pero el cruce falló por bugs del loader local
  (OCR no consumido, distancias OCR mal parseadas, alias nombres
  variantes, Tupungatito coverage start date, FALSO_POSITIVO filtrados
  por `limite_km` scraper); 46.3% son features volcánicas reales no
  publicadas por MIROVA (Cerro Blanco NdC, Pichi-Llaima Llaima,
  Lazufre Lastarria, cráter El Agrio Copahue, complejo multi-cráter PP,
  lacolito difuso PCC, lava lake Villarrica); 0% geotermal/lacustre no
  volcánico (el gate `inner_radius_km` del frontend ya los filtra desde
  S33); **4.6% artefactos reales** (cirrus path D PCC + ring glaciar
  Tupungatito). 95.4% de los "FPs" son anomalías térmicas físicamente
  reales. **How to apply**: antes de proponer cualquier "fix de
  precisión" o gate adicional, primero clasificar la categoría (a/b/c/d)
  de los records que el fix filtraría. Si filtra (b), eso es destruir
  valor agregado VRP Chile. El "bug a cerrar" reside en el loader CSV
  + en la metodología de evaluación + en el etiquetado del dashboard,
  NO en los algoritmos del pipeline.

- **A55. Anti-patrón emergente "gate intra-radio por path"** (S86
  hallazgo I-C6): PRs #224 (S83 path D intra-radio) + #229 (S85
  second_pass intra-radio) pasaron MISSION 3-preguntas solo por puerta 3
  GRIS "infra alineación" pero el hallazgo S85 (`frontend mirovaEqVrp`
  desde S33) reveló que **eran redundantes** — el frontend ya aplicaba
  exactamente esa supresión. Patrón análogo al S22-S26 que MISSION.md
  documenta como anti-patrones (acumulación de parches que parecían
  justificados individualmente pero anulaban diferenciación
  summit/scene MIROVA). **How to apply**: cualquier PR que proponga un
  gate "intra-radio por path X" requiere verificar primero (a) que el
  frontend no hace ya esa supresión, (b) clasificar categoría
  físicamente (A54 / E S86) de los records filtrados, (c) confirmar
  que no se está destruyendo categoría (b). Si entra un PR más sin
  estas verificaciones, se reabre el ciclo cerrado S27.

- **A56-A60. Reglas preventivas NRT (S82)**: viven en
  [docs/META_RULES_S80.md](docs/META_RULES_S80.md). Consultar ahí cuando
  se mencionen en bloques de arranque o handoffs. **Nota S86 (resuelve
  C2 auditoría I)**: A54 y A55 antes eran gap numérico — ahora llenas
  por las reglas S86. A56-A60 quedan en META_RULES_S80 por ahora;
  migración a CLAUDE.md proyecto pendiente para S87+ si se vuelve a
  citar mucho.

- **A61. AUDIT-SPATIAL: auditar detección SIEMPRE incluye el eje espacial**
  (S97, lección dura — fallé 2 auditorías por saltarlo). Comparar la
  **lat/lon** de nuestras detecciones contra (a) el cráter físico (`vent_lat`)
  y (b) la radiancia LOCAL del TIF MIROVA alrededor del cráter — NUNCA solo
  números de distancia. Las distancias nuestra y de MIROVA pueden compartir el
  mismo ancla (centro del grid) y "coincidir" estando ambas corridas del cráter
  físico. El bug Tupungatito (detecciones 5 km al sur del lago) era invisible a
  una auditoría de número-vs-número; solo aparece comparando ubicaciones.

- **A62. AUDIT-ADVERSARIAL: la insistencia del experto de dominio es señal, no
  ruido** (S97, pedido explícito Nicolás "qué hacer para que te fijes"). Al
  concluir "estamos bien", y MÁS aún cuando Nicolás (geólogo, conoce el volcán)
  disiente, **asumir que hay un error y refutarlo con datos** antes de reafirmar.
  No defender la propia conclusión. S97: estuve sobreconfiado, me contradije
  varias veces, y solo cavé hondo cuando Nicolás insistió. Herramientas que SÍ
  tengo y debo usar antes de decir "no puedo": **Chrome MCP** (mirovaweb/Maps),
  **TIF en `../mirova-tif-archive`** (sibling del repo, NO interno).

- **A63. Consolidar config NO debe revertir fixes deliberados** (S97, regresión
  S65→S80 git-confirmada). S65 (PR #93) quitó deliberadamente el `mirova_center`
  de Tupungatito (ancla al cráter, validado S66 56%). S80 (PR #220, "consolidación
  post-pérdida-contexto, 11/11 mirova_center") regeneró los 11 desde el KMZ y
  **revirtió el fix sin saberlo**. Regla: al regenerar/consolidar config
  (mirova_center, coords, flags), revisar `git log -S`/comentarios por excepciones
  deliberadas previas ANTES de sobrescribir. Defensa durable: un **test de
  regresión** que asegure la intención (ej. `get_detection_anchor` ancla al
  cráter en Tupun/PCC/PP) — falla si una consolidación lo revierte.

- **A64. NRT timeout = hang de fetch a un host caído; circuit-breaker por host, no
  solo por auth** (S102, incidente resuelto). El cron NRT fallaba ~50% desde 2026-06-04
  por timeout 50min en vol aleatorio. Root cause (probado con instrumentación, run
  27089474584): el host LANCE NRT `nrt3.modaps.eosdis.nasa.gov` da ConnectTimeout a
  183s; `download_granules` reintentaba 4× por granule × N plataformas VIIRS NRT →
  acumulaba >50min. El auth ya estaba blindado (probe S70-0, budget ≤22min) pero la
  DESCARGA no. Fix (`pipeline/fetch.py`, #364): circuit-breaker por host — al 1er
  ConnectTimeout/ConnectionError marcar el host caído PARA LA CORRIDA y saltar sus
  descargas siguientes al instante (devuelve lo de LAADS). Errores genéricos
  (ReadTimeout) conservan retries. Degrada con gracia (nunca peor que el hang). Patrón
  análogo a `_probe_nasa_auth`. **How to apply**: cualquier blindaje de red NASA debe
  cubrir AUTH **y** DOWNLOAD por separado; LANCE (`nrt3.modaps`) es flaky para fechas
  recientes (Standard/LAADS no existe aún → cae a LANCE). Distinguir ConnectTimeout
  (host caído, no reintentar) de ReadTimeout (transient, reintentar).

- **A65. Instrumentación-primero para hangs de CI con timeout-kill** (S102, método
  validado). Cuando un job de GH Actions timeoutea, GitHub NO flushea el stdout del
  proceso al matarlo → los logs `--log-failed` solo muestran el cleanup, no dónde se
  colgó. El argumento por eliminación (budgets acotados vs duración real) es fuerte pero
  no definitivo. La prueba definitiva: agregar markers de borde **print-only con
  `flush=True`** (timestamped) en las etapas (auth/search/download/process), mergear
  (bajo riesgo), y la próxima falla muestra EXACTO dónde se cuelga (ej: `DOWNLOAD_START`
  sin `DOWNLOAD_DONE`). S102: la instrumentación convirtió "download sin timeout" en el
  diagnóstico preciso "LANCE host ConnectTimeout 183s × 4 retries × N granules". Vale 1
  ciclo de cron; barato vs adivinar el fix.

- **A66. nadir-fijo es el modo de área clon-literal de MIROVA para los 3 sensores; un
  parche de magnitud previo puede estar parcheando el mismo drift** (S102). El sec³(θ)
  off-nadir activo era un DRIFT; MIROVA resamplea a grid 1km de área constante
  (calibración S14 `experiments/21_results.json` a_pix_mode=nadir_fijo para MODIS+
  VIIRS750+VIIRS375). El WOOSTER_COEFF ya es para área nadir → activar nadir-fijo
  RESTAURA la calibración, NO la rompe. **MODIS adoptado S102** (#354: PCC 342→60MW,
  Lascar 0.92×, 0 FN con piso 0.05). **VIIRS decidido S102** (adoptar + mantener
  ctxpeak). Lección de método clave: sospeché que ctxpeak (adoptado S100 para curar
  Tupun 18.9×) era un parche redundante del sec³ → lo testée con un **A/B de 3 brazos
  con criterio pre-registrado** (base / nadir+ctx / nadir-SIN-ctx). Los datos REFUTARON
  la hipótesis (nadir-sin-ctx = 2.43× peor; ctxpeak cura el anillo nival del Test1, otro
  mecanismo). **How to apply**: antes de apilar dos correcciones de magnitud, aislar con
  un A/B de 3 brazos + criterio pre-registrado (evita confirmation bias, A62). El sec³
  afecta el ÁREA; ctxpeak/Test1 afecta el FONDO del ROI — son ortogonales.

## Regla de comunicación con Nicolás
**Explicar como geólogo, no como programador.** Cuando discutas resultados, bugs,
decisiones de umbrales, o cambios metodológicos:

1. **Primero el fenómeno físico**: qué está pasando realmente en el volcán, el
   pixel del satélite, la atmósfera, el background. Describirlo en lenguaje natural
   — "el cráter mantiene calor residual después del atardecer y produce un gradiente
   térmico local", "la nube fina alta enfría el background porque irradia desde
   -40°C", "el pixel VIIRS de 375m mezcla roca caliente con nieve y el promedio queda
   en valores intermedios".
2. **Después el mecanismo del pipeline**: cómo el código interpreta ese fenómeno,
   qué umbrales lo filtran, qué paths lo capturan. Explicar por qué esa elección de
   código tiene o no tiene sentido frente al fenómeno físico.
3. **Recién al final, si aplica, los números y fórmulas**, y solo los estrictamente
   necesarios para apoyar el razonamiento. Nunca empezar por la fórmula.
4. **El "por qué" antes del "cómo"**. Si hay un trade-off científico (por ejemplo
   falsos positivos vs falsos negativos en monitoreo volcánico), nombrarlo
   explícitamente y decir cuál es el costo de cada lado.
5. **Tablas comparativas y métricas agregadas sí**, son útiles. Pero las derivaciones
   matemáticas largas, constantes de Planck, conversiones de radiancia — esas viven
   en los papers y en los comentarios de código, no en la conversación con Nicolás.
6. **Nunca adivinar** un valor físico o un dato instrumental. Si no sabés el ΔT real
   de un volcán, dilo y andá a mirarlo antes de proponer un umbral.

## Arquitectura
- `pipeline/`: fetch.py (earthaccess), process_modis.py, process_viirs.py, process_viirs_mod.py, store.py, scan_geometry.py
- `frontend/` — **3 vistas standalone, cada una con su copia de helpers** (`mirovaEqVrp`, etc.): `index.html` (dashboard Chart.js+Leaflet), `diario.html` (tendencia 90d/volcán), `mosaico.html` (overview 48h/30d). **Un cambio de display/filtro (ej. supresión cirrus) debe replicarse en las 3** (S92 L5). Verificación = preview real navegador (no `node --check`): sirven desde `/frontend/`, `BASE_PATH=/`, data en `/data/...`. GitHub Pages (deploy on push a `frontend/**`).
- `volcanoes.yaml` (45 configurados, 11 con data, 34 sin pull)
- `.github/workflows/nrt.yml` (cron cada 2h, matrix por volcán, **timeout 50 min per-step**)

**Aprendizaje S15 sobre reprocesos largos (obligatorio respetar)**:
- GitHub Actions free tier: **6h hard limit por job, 50 min soft timeout en nuestro workflow**.
- **Nunca** lanzar reproceso full-history en GitHub Actions — timeout seguro.
- Reprocesos de historia (más de 1 día) **deben correr en máquina local de Nicolás**
  via `scripts/run_pipeline.py --profile X --volcano Y --start ... --end ...`.
- GitHub Actions NRT solo procesa 1 día / cron (paraleliza por volcán, cabe en 50 min).
- `data/` JSON por volcán (committed). Raw L1B/HDF **nunca** committed.

## Skill triggers (OBLIGATORIO invocar proactivamente)

**Regla fuerte**: Claude DEBE invocar `Skill` ANTES de actuar cuando el trabajo
encaje con la tabla. No es "proactivo opcional", es **vinculante**. El costo
de invocar de más es bajo; el costo de saltarla es un fix mal hecho que
después hay que revertir.

| Situación | Skill a invocar | Por qué |
|---|---|---|
| Cualquier bug, FP/FN inesperado, anomalía, regresión de métricas, "no entiendo por qué pasa esto" | `superpowers-systematic-debugging` | Forzar hipótesis → evidencia → root cause. 4 fases obligatorias. Prohibido proponer fix sin investigación previa |
| Antes de escribir fix que toque `pipeline/` con >20 líneas | `writing-plans` | Plan bite-sized con criterios de aceptación antes de tocar código |
| **Paso atrás metodológico, revisión integral de trabajo, "estamos haciendo las cosas bien?"** | **`superpowers-brainstorming`** | Gate de diseño antes de seguir con implementación |
| Ejecutar un plan ya escrito paso a paso | `executing-plans` | Checkpoints y no saltarse pasos |
| Antes de editar `pipeline/process_*.py` o `scan_geometry.py` | `test-driven-development` | Primero el test que captura el bug, después el fix |
| Antes de declarar un fix "listo", pushear a main, o cerrar item | `verification-before-completion` | Re-audit obligatoria sobre Tier A completo antes del push |
| **Antes de cambiar `enable_*: true` en `pipeline/profiles/mirova_equivalent.yaml`** (adopción operacional metodológica) | **`superpowers-brainstorming` OBLIGATORIO + R2 verificación pixel-level** | S33: bug `mirovaEqVrp` causó adopción Driver B Phase 1 con métrica auto-confirmatoria. Sin R2 (pixel-level vs MIROVA web) NO adoptar. Ver `docs/PROCESS_RULES_S33.md` |
| **Antes de aceptar resultado A/B con "mejora" >30%** | **`superpowers-systematic-debugging` + R3 audit independiente** | S33: cuestionar la métrica antes de confirmar resultado. Audit independiente (`experiments/76_audit_independent.py`) debe coincidir |
| **Antes de modificar `pipeline/audit_metrics.py` o cualquier función de métrica** | **R1 + R7 — tests sintéticos antes del cambio** | Bug S33 era detectable con 1 test unitario. Ver `tests/test_audit_metrics.py` |
| 2+ investigaciones independientes que se pueden hacer en paralelo | `dispatching-parallel-agents` | Paralelismo real vía subagentes, no serie |
| Nicolás pide "automatiza X", "cada vez que Y", "antes de Z hacé W" | `update-config` | Esto es un hook de settings.json, no instrucción conversacional |
| Trabajo con HDF/NetCDF/DataFrames grandes de records satelitales | `pandas-pro` | Operaciones vectorizadas, no loops |
| Audit script que tarda >5 min | `python-performance-optimization` | Perfilar antes de "optimizar a ojo" |
| Diseñar nuevo experimento (`experiments/NN_*.py`) | `writing-plans` + `test-driven-development` | Mismo rigor que código de producción |
| A/B test cuantitativo de un fix con profile flag | clonar `.github/workflows/reproc-ab-p3-1.yml` o `reproc-ab-test1.yml` como template + 2 profiles `_<feature>_{enabled,disabled}.yaml` con `data_subdir` aislado | Patrón validado S24+S25, no contamina operacional |
| **Cerrar sesión con learnings nuevos** | **`revise-claude-md` + `anthropic-skills:consolidate-memory`** + seguir [`docs/SESSION_CLOSE_CHECKLIST.md`](docs/SESSION_CLOSE_CHECKLIST.md) bloque por bloque | El trigger sin checklist falló S20 (gaps redescubiertos S21). Checklist obligatorio bloques A-F |

**Regla meta (reforzada S16)**: si Claude duda si una skill aplica, la invoca igual.
Costo invocar = 30 segundos. Costo de NO invocar = sesión entera perdida por
fix mal hecho (ej: S15 S12 F1 sigma-gating que se aplicó sin systematic-debugging
previo y tardamos 4 sesiones en entender la regresión).

**Regla meta-meta (S21)**: persistencia in-vivo, no al cierre. Cuando descubras un
hallazgo durante la sesión (schema gap, source externa, dato nuevo), persistilo
INMEDIATAMENTE en memoria/docs antes de continuar con el trabajo. La sesión puede
cortarse abruptamente. La regla del cierre (Bloque A del SESSION_CLOSE_CHECKLIST) es
red de seguridad, no la persistencia primaria.

## Glosario obligatorio (usar estos términos siempre en discusiones de resultados)

Pensá la auditoría como un examen donde MIROVA es la hoja de respuestas y nuestro
pipeline es el alumno. Cada noche-satélite de cada volcán es una pregunta.

- **TP (True Positive)** — MIROVA detectó anomalía térmica esa noche y nosotros
  también. Acertamos: hay actividad real y la vimos.
- **FP (False Positive)** — Nosotros detectamos, MIROVA no. Ejemplos físicos
  típicos: lago que retiene calor post-atardecer, nube fina que deforma el
  background, ruido sobre nieve parcial. "Grito de fuego" sin fuego.
- **FN (False Negative)** — MIROVA detectó, nosotros perdimos. **Lo más grave en
  monitoreo**: un evento real sin alerta. Típico en señales sub-pixel (lava lake
  Villarrica, 0.05–0.2 MW) que MIROVA ve integrando ROI completo.
- **TN (True Negative)** — Ambos coinciden en que no hay nada. No se tabula.
- **Cluster vs pixel (S23 T14, hallazgo factor 42)** — MIROVA reporta
  `n_hotspots` (regiones espacialmente contiguas, conectividad ~1km).
  VRP Chile reporta `n_anomalous_pixels` (pixels individuales del granule).
  Para 1 cluster MIROVA esperamos 5-50 pixels nuestros (depende tamaño región
  hot). NO es bug — diferencia de agregación al reportar. Recall/precision no
  afectados. Ver `experiments/50_FACTOR_42_HALLAZGO.md` para detalles
  empíricos (Lastarria 77px=3 clusters@1km, ratio 25.7).

Métricas derivadas:
- **Precision** = TP / (TP+FP). De lo que gritamos, cuánto era real. Baja =
  ruido de falsa alarma, operador deja de confiar.
- **Recall** = TP / (TP+FN). De lo real, cuánto detectamos. Baja = perdemos
  eventos. **Para `mirova_equivalent` priorizamos recall sobre precision**.
- **F1** = media armónica de ambas. Un solo número para comparar.
- **Ratio ours/mirova** = VRP nuestro / VRP MIROVA en la misma noche. 1.0 =
  calibración perfecta. Mediana sobre muchas noches = sesgo sistemático.

Conceptos de detección:
- **Tier A/B/C** — A ≥30 refs MIROVA (calibración), B 5–29 (corroboración), C <5
  (solo NRT, no calibramos).
- **vent-path** — detecta un solo pixel del cráter cuando supera background
  (señal débil persistente). Más sensible, menos específico.
- **eruption-path** — requiere clúster de varios pixels (señal fuerte). Más
  específico, ciego a sub-pixel.
- **σ_bg** — desvío estándar de T en el anillo de fondo. Se infla con terreno
  heterogéneo (nieve parcial, orografía) y rompe gates `N·σ`.
- **Path A / B / C** — A=umbral BT clásico; B=NTI absoluto (>-0.8);
  C=NTI relativo (supera 3σ local, S11+).

## Regla de publicación en dashboard (obligatorio)

Cualquier cambio que modifique detecciones (nuevo perfil, ajuste de umbral,
reproceso masivo, fix en pipeline/) **debe reflejarse en el dashboard antes
de declarar el trabajo completo**. Flujo:

1. Correr el reproceso/fix.
2. Commit + push del JSON bajo `data/mirova_equivalent/`.
3. Verificar que GitHub Pages publicó la nueva data (o que el JSON local abrió
   correctamente en el dashboard) antes de cerrar el tema.
4. Si el cambio es solo del perfil `experimental`, mencionarlo explícitamente
   y no contaminar la vista operacional.

El dashboard es el entregable final para Nicolás/SERNAGEOMIN. Auditoría en
stdout es trabajo interno — no cuenta como resultado hasta que es visible.

## Regla de delegación a subagentes (control de contexto)

Para minimizar compactaciones automáticas ("session continued..."):

- **Lecturas exploratorias** de archivos >500 líneas o de múltiples archivos
  relacionados → delegar a `Explore` subagent con pedido de resumen <500 tokens,
  no cargar el archivo completo al contexto principal.
- **Salidas de auditoría largas** (>200 líneas stdout) → leer directamente el
  JSON del snapshot (`experiments/audit_s*/Volcano.json`) en vez de reimprimir
  el stdout crudo.
- **Investigaciones paralelas** (2+ volcanes independientes, 2+ RF a la vez)
  → `dispatching-parallel-agents`, cada rama en su propio contexto.
- **Estado entre sesiones** → memoria (`MEMORY.md` + archivos) en vez de
  re-derivar al inicio de cada sesión.
- No re-leer archivos ya leídos en la misma sesión salvo que haya cambio
  observable.

## Constraints técnicos
- **pyhdf roto en Windows** → MODIS solo corre en GitHub Actions Linux.
- NASA LANCE NRT ~3h latencia.
- NOAA-20: buscar v2 **y** v2.1 (disponibilidad variable).
- Secrets en GitHub: EARTHDATA_USERNAME, EARTHDATA_PASSWORD.
- **NRT vs Standard L1B**: fetch.py intenta Standard primero, cae a `_NRT`
  (LANCE). Records llevan `product_version: "standard"|"nrt"`. store.py
  auto-upgrade NRT→Standard. Delta BT <0.1K, despreciable para VRP.
- **Encoding Windows**: scripts Python que imprimen Unicode (σ, →, ✓) deben
  usar `sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')`.
- **volcanoes.yaml**: `yaml.safe_dump` destruye comentarios. Preferir `Edit`
  tool para cambios puntuales, no rewrite completo con Python.
- **GitHub Actions**: repo público = minutos ilimitados. Matrix 45 volcanes,
  max-parallel=8, fail-fast=false, cron cada 2h. Timeout 25 min/step puede
  ser corto para reprocess full history (NdC timeout recurrente).
- **Radios geofencing MIROVA-OVDAS**: cada volcán tiene radius_km propio
  (3-15 km). store.py usa `max_hotspot_dist_km` per-volcano, no global 5km.
  Refs: https://github.com/MendozaVolcanic/Mirova-v1
- **Refs MIROVA son NRT**: los CSV consolidado/OCR scrapeados de mirovaweb.it
  contienen datos NRT. Comparar contra NRT es operacionalmente correcto.
  OCR cubre ~80% VIIRS, MODIS completo. No re-scrapear para homogeneizar.
- **Frontend chart gotcha**: VIIRS 375m debe usar `vrp_mw` (filtrado), no
  `vrp_mir_mw` (pre-filtro). Bug S12: barras fantasma de detecciones
  descartadas por geofencing.
- **Race condition matrix paralelo sobre mismo archivo (S25)**: workflows
  con matrix-de-fechas que escriben al MISMO `data/<profile>/<vol>.json`
  tienen race con `pull --rebase -X theirs origin main`: cada commit
  posterior puede borrar records del anterior. Mitigación: `max-parallel: 1`
  o split a archivos distintos por chunk + merge final. Patrón A/B
  vol×profile (`reproc-ab-*.yml`) NO afecta porque cada job toca archivo único.
- **earthaccess granule API**: `g["umm"]` (dict-like, no `g.umm`).
  Estructura: `g["umm"]["TemporalExtent"]["RangeDateTime"]["BeginningDateTime"]`.
- **GH Actions `workflow_dispatch` limitation** (S73): solo es invocable si el yml
  está en la default branch (`main`). En feature branches retorna HTTP 422
  "Workflow does not have 'workflow_dispatch' trigger" aunque el yml SÍ lo tenga
  configurado. Solución: mergear PR primero, después `gh workflow run --ref main ...`.
- **GH Actions YAML 1.1 "Norway Problem"** (S74 F2.8.f breakthrough, A43): tokens
  como `on`, `off`, `yes`, `no`, `true`, `false` (case-insensitive, SIN quotes)
  parsean como **booleans** en YAML 1.1 estricto. GitHub Actions normalmente trata
  `on:` como special key, pero bajo ciertas condiciones de cache/indexing aplica
  parse YAML 1.1 estricto y ve la key como `True` → rechaza el workflow con
  HTTP 422 "Workflow does not have workflow_dispatch trigger" aunque el yml SÍ
  lo tenga configurado.

  **Fix universal**: quote la key como `"on":` string explícito. **Defensivo gratis**:

  ```yaml
  # ✗ Puede fallar HTTP 422 random:
  on:
    workflow_dispatch:
      inputs: ...

  # ✓ Siempre funciona:
  "on":
    workflow_dispatch:
      inputs: ...
  ```

  S74 F2.8.f: 2 workflows previos (`reproc-f28-pp-saturation.yml`,
  `reproc-f28-pp-sat-v2.yml`) fallaron HTTP 422 13+ horas hasta que v3
  (`reproc-f28-v3.yml`, PR #143 commit `d2ea629`) usó `"on":` y dispatched al
  primer intento. Diferencias adicionales que **pudieron** contribuir (no
  aislado, no vale el ROI determinar cuál): bloque comentarios largo encima de
  `on:`, `cache: "pip"` sin lockfile (silently fails), inputs múltiples + commit
  messages multilínea con literal newlines en `-m`.

  **Anti-pattern S75+**: cualquier yml nuevo de GH Actions con `on:` debe usar
  `"on":` quoted. También vale para otros tokens YAML 1.1 problemáticos (no,
  off, false). Verificar pre-merge con `python -c "import yaml;
  print(list(yaml.safe_load(open(<path>)).keys()))"` — si la key aparece como
  `True`/`False`/`None` en vez de string, falla.

## Estado

**S35 en curso (2026-05-10) — fix H8 + revelación D8 cluster selection.**

### Hallazgos S35 (2026-05-10)

1. **Bug H8 descubierto**: `pipeline/store.py:119` filtro all-or-nothing descartaba
   anomaly_pixels enteras cuando hotspot_dist (= pixel más caliente individual) >
   radius_km. Reach 13.7% records Tier A en 30d. **20 ALERTA_TERMICA MIROVA
   confirmadas como pérdidas** (Lacolito Puyehue, cráter Lascar, summit Isluga/
   Lastarria/Tupungatito, Planchón).

2. **R2 pixel-level CONFIRMADO** (caso Puyehue lacolito 05:42 GMT):
   - TIF MIROVA en `mirova-tif-archive/data/tif/PuyehueCordonCaulle/20260509_054202_VIIRS375.tif`
   - 56 pixels VRP-chile descartó en zona lacolito (5-10km) tienen valores TIF reales
   - Top hottest @ 7.99km, val=0.18 (50% sobre mean bg)
   - Coincide pixel-by-pixel con MIROVA (0.18 MW @ 7.73km lacolito)

3. **Fix H8 implementado** (commit `9570375`, PR #3 mergeado main):
   - Nueva función `_filter_pixels_by_distance` en store.py
   - Filtra pixel-por-pixel, recalcula vrp_mir_mw + hotspot_* desde in_range
   - Flag `enable_pixel_level_distance_filter` por profile (default OFF, opt-in)
   - 5 tests sintéticos en `tests/test_store_eruption_filter_bug.py`
   - Suite verde 231/0/16

4. **A/B reproceso H8 disparado** (run 25623575250, 25d × 11 Tier A × 2 perfiles):
   - `_h8_pixel_filter_enabled` vs `_h8_pixel_filter_disabled`
   - Adopción operacional pendiente de validación R2 + R6 + R3.

5. **D8 NUEVO**: cluster selection diverge de MIROVA. `pipeline/clustering.py`
   sort by vrp_mw desc o n_pixels desc (línea 99/101). MIROVA aparentemente
   usa otro criterio (posiblemente proximidad-al-vent o anomaly score relativo).
   Caso Puyehue: VRP-chile elige cluster cráter principal (99 px, vrp=4.94 MW)
   cuando MIROVA reporta lacolito (35 px, vrp=0.18 MW). Frontend `mirova_eq_vrp`
   retorna pc.vrp_mw del cluster equivocado. Ratio inflado 27×. Pendiente
   investigación papers Coppola.

6. **Mejora process compliance** instalada:
   - R5 design doc: `docs/superpowers/specs/2026-05-10-h8-eruption-filter-pixel-level.md`
   - R1+R7 tests sintéticos antes del fix
   - R2 verificación pixel-level via mirova-tif-archive
   - R3 audit independiente: `experiments/77_r2_h8_pixel_audit.py`
   - R4 pre-mortem en design doc
   - R6 pendiente (cuestionar resultado A/B)
   - R8 pendiente (URL pública post-deploy)

### Fix H7 S35 también (commit anterior)

NRT VRP Pipeline fallaba 24+ runs consecutivos por OSError 101 Network unreachable.
Fix: socket.getaddrinfo monkey-patch IPv4-only en fetch.py + extender retries
4→6 attempts (delays 0/5/15/45/90/180s). PR #2 mergeado.

### Pendientes inmediatos S35→S36

- [ ] Esperar A/B run 25623575250 termina (~22 jobs, ~1-2h)
- [ ] Audit comparativo H8 enabled vs disabled vs mirova_equivalent baseline
- [ ] R6 cuestionar si recall sube >30%
- [ ] Decidir adopción operacional H8 (cambiar mirova_equivalent.yaml)
- [ ] Investigar D8 cluster selection (paper Coppola 2016a §)
- [ ] Decidir revert fix S33 mirovaEqVrp (cierre S33+ pendía)
- [ ] Toggle dual "Solo cráter / Incluir lejanas" en frontend (cierre S33+)

---

**S17 cerrada (2026-04-23) — investigación sistemática + arquitectura de memoria instalada.**

**Hallazgos críticos S17** (ver `docs/DRIFTS_S17.md`, `docs/PAPERS_AUDIT.md`, `docs/HYPOTHESIS_LOG.md`):
1. **H10 CONFIRMADA**: falta NOAA-21 (VJ202IMG/VJ202MOD) en `fetch.py`. MIROVA sí lo procesa.
   El cuello de botella real de recall Tupungatito/Chaitén no era sigma-gating (H1 refutada) sino
   un satélite entero faltante. Implementación S18.
2. **Fix performance Path D** aplicado (commit `ad030f5`): `generic_filter` crop al bbox ROI,
   factor ~2400× más rápido.
3. **3 drifts detectados** entre código vs papers autoritativos (ver DRIFTS_S17.md).
4. **Arquitectura de memoria**: `docs/` con 5 documentos vivos (drifts, papers audit, data sources,
   hypothesis log, session index). Mantener al cierre de cada sesión.

**Próxima sesión S18**: fix D1 (median→mean), agregar NOAA-21, test A/B D2 (N·σ), reproceso 3
volcanes Tier A, si valida push main. Leer `docs/SESSION_INDEX.md` para plan.

**Handoff S16→S17 original**: `tasks/handoff_s17_2026_04_23.md` (parcialmente superado por S17 —
H1 de ese handoff fue refutada, H10 es la real).

### Fixes S15 aplicados (commits locales, pendientes push):

1. **P3.2 — dNTI contextual 8-vecinos** (Coppola 2016a SP 426.5): Path D en
   hot_mask de los 3 procesadores. Gate local NTI vs vecinos inmediatos,
   inmune a heterogeneidad regional. Flag `enable_dnti_contextual_path: true`.

2. **P3.1 — Dual-ROI thresholds** (Coppola 2016a Table 2): Path D con umbrales
   distintos según distancia al vent. Summit `c1=0.003` sensible; scene
   `c1=0.010` estricto. Flag `enable_dnti_dual_roi: true`.

3. **Tema E — ROI bbox cuadrado** (paridad MIROVA KMZ GroundOverlay): reemplazar
   `roi_mask = dist <= radius_km` (círculo) por bbox cuadrado 50×50 km via
   `scan_geometry.roi_mask_bbox()`. Recupera las esquinas donde MIROVA publica
   detecciones (Llaima Conguillío a 28 km, Copahue lejanas). +27% área.

4. **Tema F — Sigma-cap eruption-path VIIRS**: paridad con MODIS que ya tenía
   `MAX_SIGMA_COMPONENT_K=7.0` desde S6. Aplicado a VIIRS 375m y 750m. Cura
   Tupungatito recall 0.04 donde σ_bg inflado (glaciar) saturaba el threshold
   a 9-12 K, rechazando pixels reales a ΔT=8-9 K.

### Scope limpieza S15 (aplicada):

- Perfil `mirova_equivalent` ahora procesa SOLO los 11 volcanes Tier A que
  MIROVA efectivamente monitorea (flag `mirova_monitored: true` en yaml).
- Los 34 volcanes restantes (Laguna del Maule, Calbuco, Osorno, Parinacota,
  etc.) fueron movidos a `data/experimental/` — siguen procesables bajo
  perfil `experimental` pero fuera del dashboard operacional mientras modo (1).

### Ground truth canónico S15:

- **CSV MIROVA NRT** (`21_04_2026 registro_vrp_consolidado.csv`, scraper
  Mirova-v1 contra latest.php): 13.7k filas, 3.5 meses, ~100% MODIS / ~80%
  VIIRS. **Ground truth operacional primario bajo objetivo (1) clon MIROVA.**
- **OSF v2.5 archive** (`data/mirova_reference/`): 615k filas globales, 48k
  chilenas 2000-2025. Ground truth algorítmico histórico. 10/11 Tier A
  calibrables. Tupungatito no aparece (caso singular OSF=0 NRT=60 AT).
- **KMZ oficiales MIROVA** (`kmz/`): 15 archivos, GroundOverlay 50×50 km.
  Revelaron offset Tupungatito 3 km SE y Planchón-Peteroa 1.87 km N del
  vent Nicolás → `mirova_center_lat/lon` en volcanoes.yaml (Fase 0.7 S15).

### Umbrales paridad MIROVA (acordados bajo objetivo 1):

- Ratio VRP individual tolerable 0.5-2.0 (MIROVA declara ±30% error).
- Ratio mediano volcán tolerable 0.7-1.4.
- Recall tolerable ≥0.60 por volcán.
- Precision tolerable ≥0.50 por volcán.
- Max FP individual ≤5× MIROVA-max mensual.

### Objetivo actual:

**(1) Clon MIROVA operacional**. Ligeras diferencias aceptables (dentro de
umbrales arriba), groseras inaceptables. Fase (2) herramienta independiente
es futuro no inmediato.

### Pendientes S15 (post-reproceso validación):

- Leer `experiments/30_p32_delta_report.md` (o similar) para veredicto fixes.
- Si validan: push main para sincronizar NRT.
- Plan P3.6 water-aware filter escrito en `tasks/plan_s15_p3_6_water_aware_filter.md`
  para fase (2) cuando Laguna del Maule vuelva a scope.
- Lascar S11 regresión: en investigación agent forense (S15 2026-04-22).

### Pre-S15 (S14 histórico):

Fix S14 geometría MIROVA-equivalent: `radius_km=25` uniforme + `inner_radius_km`
oficial MIROVA + schema unificado `final_hotspot_*` + `distance_class` +
WOOSTER_COEFF 19.7 VIIRS_M + dashboard About/credits. OSF v2.5 en
`data/mirova_reference/` (no commitear 98 MB). Validación empírica
coeficientes (error ≤0.17%) en `experiments/21_results.json`.

**S12 baseline (2026-04-16)**: 45 volcanes operacionales, 11 con refs MIROVA
(14042026 consolidado, 494 refs). Auditoría contra MIROVA:
- Recall top: Chaitén 87%, Lastarria 85%, Tupungatito 83%, PCC 82%.
- Lascar (Tier A): recall 55%, precision OCR-adj 0.69, ratio 1.11.
- Villarrica 0% recall: gap arquitectural, requiere Test 1 integrado-ROI
  (plan en `tasks/plan_s13_test1_integrated_roi.md`).
- FPs principales: vent-only detecciones sub-MIROVA-threshold (0.1-1 MW).
- Experimental prueba `min_vent_pixels=2` (E4): −39% FPs vs meq.
- Leer `tasks/status_s12_overnight.md` y `tasks/todo.md` para pendientes.
- Coords de vent actualizadas por Nicolás (campo): PCC lacolito, Chaitén
  domo, Villarrica lava lake, Lascar cráter V.
