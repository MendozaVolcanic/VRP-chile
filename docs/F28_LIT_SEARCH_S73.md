# F2.8 Búsqueda bibliográfica S73 — MIROVA post-2024 + saturation handling

**Sesión**: S73 (2026-05-23)
**Trigger**: Nicolás pidió evaluar si las skills nuevas instaladas (post-S72) aportan algo a búsqueda bibliográfica.

## Target

¿Hay literatura POST-2024 que (a) actualice el algoritmo MIROVA o thresholds, o (b) discuta saturation handling en sistemas VRP-like más allá de Wooster 2003?

## Experimento 4-way A/B/C/D

4 búsquedas paralelas con misma query target, distintos approaches:

| ID | Approach | Skill / Tool |
|---|---|---|
| **A** | Workflow viejo (control) | `investigacion` skill manual + Crossref + OpenAlex + arXiv MCP |
| **B** | Skill nueva orchestrator | `deep-research` skill (13-agent pipeline) |
| **C** | External web search | WebSearch built-in tool |
| **D** | Perplexity Academic vía Chrome | `Claude_in_Chrome` MCP + `/search/new?q=...&sources=scholar` |

## Resultados comparativos

| Approach | Papers nuevos | DOIs verified | Discovery | Synthesis | Speed |
|---|---|---|---|---|---|
| **A (investigacion manual)** | **9** (todos Crossref-verified) | ✓ | 🏆 Best | ❌ | 6 min |
| **B (deep-research skill)** | 6 (5 overlap A) | Parcial parafraseado | ⚠️ Mediano | ⚠️ Mediano | 1.5 min |
| **C (WebSearch + WebFetch)** | 3 únicos (incluye arxiv pre-prints) | ✓ | 🎯 Best arxiv | ❌ | 3 min |
| **D (Perplexity Academic vía Chrome)** | **0 nuevos específicos** | ✗ solo hostnames | ❌ Worst | 🏆 **Best synthesis narrative** | ~30s |

**D (Perplexity)** detalle: sesión Nicolás activa (login OK). Query enviada vía `/search/new?q=...&sources=scholar` URL pattern. Respuesta synthesis-style estructurada por sub-pregunta. Confirma independientemente "no newer canonical replacement of Wooster 2003". Pero NO encontró Dhage 2025 ni Coppola 2026 Lascar ni Aveni 2025 GRL específicos — cita 6 fuentes pero solo da hostnames ("mdpi", "frontiersin") no DOIs.

### Verdict sobre skills/tools nuevas

**Las skills nuevas (B, D) NO aportaron exclusividad** para búsquedas bibliográficas dirigidas. Su backend es WebSearch (B) o Perplexity API (D), y no tienen acceso a `paperzilla` ni `bgpt-paper-search` cargados. La skill `deep-research` y Perplexity Academic brillan en **synthesis narrative**, no en discovery.

**Combo operacional óptimo según use case**:

| Use case | Tool/Skill ganadora |
|---|---|
| **Discovery dirigido** (encontrame N papers) | **A** (`investigacion` manual + OpenAlex author IDs) + **C** (WebSearch arxiv) |
| **Synthesis narrative** (paragraph para paper) | **D** (Perplexity Academic vía Chrome) ó **B** (`deep-research` full mode) |
| **Verificación post-discovery** | `citation-audit` skill (no probado en S73) |

**NO usar B/D `deep-research`/`Perplexity` para "encontrame N papers"** — overhead alto, ganancia baja en discovery. Útiles para writing-mode.

## Hallazgos prioritarios (3 papers nuevos críticos)

### 🎯 1. Dhage 2025 — VIIRS undocumented filtering [DESCARGADO Y LEÍDO S73]

- **DOI/Source**: arxiv:2510.26816 (Oct 28, 2025)
- **Autor**: Rohit Rajendra Dhage (Independent Researcher)
- **Status**: **PDF descargado + .md procesado** (`documentacion/dhage2025_viirs_filtering.pdf`, 257 KB, 461 líneas .md). Nota Vault skeleton creada (`Vault/10_Bibliografia/99_por_clasificar/dhage2025viirs.md`).
- **Aporte verbatim del abstract**:
  - Analiza **21,540,921 fire detections** ene 2023-ene 2024 desde NASA FIRMS Active Fire Product
  - **Ausencia COMPLETA de "low confidence" classifications en nighttime** observations: 6,007,831 nighttime fires, **CERO low-confidence** (vs 696,908 esperados)
  - χ² = 1,474,795, **p < 10⁻¹⁵**, Z = −833 — bulletproof estadísticamente
  - Persiste global: todos los meses, latitudes, NOAA-20 + Suomi-NPP
  - ML reverse-engineering 88.9% accuracy confirma constraint algorítmico (no geofísico)
  - **Detecciones nocturnas con BT<~295K se excluyen completamente** del producto
  - **Afecta 27.9% de todas las detecciones VIIRS**
- **Implicancia exacta VRP Chile** (post-lectura S73):

| Aspecto | Status |
|---|---|
| ¿Nuestro pipeline sufre el bug? | ❌ **NO** — consumimos VNP02IMG/VJ102IMG **L1B directo**, no FIRMS |
| ¿MIROVA NRT sufre? | ⚠️ Probable NO — MIROVA consume L1B directo per Coppola 2025 cap.11 |
| ¿Afecta comparaciones contra FIRMS? | ✅ **SÍ** — FIRMS sesgado nocturno (no nuestro pipeline) |
| ¿Refuerza A37? | ✅ **SÍ** — documenta "undocumented algorithmic constraints" como **patrón general** |
| ¿Worth citing en paper VRP Chile P5? | ✅ **SÍ** — sustenta decisión "L1B directo en lugar de FIRMS" |

- **Veredicto**: paper **complementario a F2.8**, no superpuesto. Nuestro bug F2.8 H2 era en *nuestra* lectura L1B. Dhage encontró bug en *FIRMS* derived product. Ambos confirman A37 patrón general.
- **Encontrado solo por C** (arxiv pre-print, fuera de Crossref)

### 🎯 2. Aveni 2025 — VRPTIR crater lakes + hydrothermal [YA LOCAL DESDE S72]

- **DOI**: 10.1029/2024GL113324 (GRL, 2025)
- **Autores**: Aveni S. (Sapienza Roma) — grupo MIROVA canónico
- **Status**: **YA local desde S72** en `Vault/10_Bibliografia/99_por_clasificar/aveni2025_crater_lakes.md` (1,064 líneas). Subagente de descargas confirmó (principio rector §1 lit search), no re-descargó. Nota Vault adicional creada para sync (`aveni2025grl.md` marked as `already_local`).
- **Aporte**: extension TIRVolcH (Aveni 2024 RSE) a crater lakes + hydrothermal systems usando single TIR band. Validación contra Ruapehu, etc.
- **Relevancia VRP Chile**: **Primer update canónico post-Coppola 2025 cap.11**. **ALTA relevancia P3 T1.5** (drift remanente Villarrica lava lake, PCC laguna lacolito, Chaiten crater lake).
- **Encontrado por A + B + C** (DOI verificado)
- **Acción S74**: leer el `.md` ya local (1064 líneas) y extraer fórmulas/thresholds operacionales para integrar a fix VRP Chile baja-T régimen

### 🎯 3. Coppola 2026 — Lascar SO2 multiparametric [BLOCKED, descarga manual]

- **DOI**: 10.2139/ssrn.6481652 (SSRN preprint open access)
- **Autor**: Coppola
- **Status**: **Cloudflare challenge** bloqueó curl en SSRN landing + mirror Sapienza IRIS. Unpaywall reporta `oa_status=green` pero `best_oa_location` es loop al DOI sin `url_for_pdf` directa. Nota Vault skeleton creada (`coppola2026lascar.md` con status `blocked_paywall`).
- **Aporte**: VRP+SO2 integrado Lascar 2017-2021 — **volcán chileno Tier A NUESTRO**
- **Relevancia VRP Chile**: integración futura con OVDAS, dataset extension
- **Encontrado solo por A** (OpenAlex barrido autor)
- **Acción S74**: **descarga manual** Nicolás con sesión SSRN (web UI directa, navegador con cookies), o esperar mirror Torino IRIS. Después procesar con `markitdown`.

## Hallazgos secundarios (11 papers)

**Aplicaciones MIROVA 2024-2026 sin update algorítmico**:
- Coppola Stromboli 10yr (JGR, `10.1029/2024jb029143`)
- Coppola Fernandina Galápagos rapid response (RS, `10.3390/rs17071191`)
- Coppola Piton de la Fournaise 24yr (JGR, `10.1029/2024jb030962`)
- Coppola Ambae sub-plinian VRP+SO2 (Comms Earth Env, `10.1038/s43247-025-02018-5`)
- Galetto/Coppola Nyamulagira SAR+thermal (Sci Rem Sens, `10.1016/j.srs.2025.100261`)
- Laiolo Stromboli switching (Bull Volcanol, `10.1007/s00445-025-01932-y`)
- Massimetti Popocatépetl long-term (JSAES 2026)

**Sistemas alternativos NO MIROVA**:
- Falconieri/Marchese NHI-SLSTR SWIR Etna 2025 (Sensors, `10.3390/s25061658`) — grupo Potenza CNR-IMAA

**EGU26 abstracts (paper full pendiente 2026 H2)**:
- Coppola "Synergistic Thermal Framework" (`10.5194/egusphere-egu26-13139`) — **posible sucesor cap.11** como referencia canónica MIROVA
- Coppola "TIR Remote Sensing Recent Advances" (`10.5194/egusphere-egu26-19440`) — roadmap MIROVA futuro

**Otros relevantes**:
- "Tracking Lava Flow Cooling 2025" (RS, `10.3390/rs17152543`) — cooling curves, bypass MIR saturation con TIR. R²=0.947 sobre 68 eruptions

## Verdict literatura saturation handling

**NO hay literatura nueva post-Wooster 2003 sobre MIR B21 saturation handling**. Confirmed por A + B + C independientemente. Wooster 2003 + Coppola 2025 cap.11 Table 1 siguen siendo state-of-the-art.

→ **Nuestro fix F2.8 está al state-of-the-art**. El approach (filtrar L1B sentinels per Sec 5.6 + quality_flag bit-2 VIIRS + BT defense Coppola 2025) es el método más actualizado disponible.

Sin update saturation handling per se, hay **vías alternativas** que valen vigilancia:
- **Aveni 2025 GRL VRPTIR** ataca por single-band TIR baja-T (complementario, no reemplaza MIR)
- **Lava Flow Cooling 2025** propone cooling curves para volume retrieval (post-eruption, no NRT)

## A40 — aprendizaje meta

**A40. Para queries bibliográficas dirigidas, manual `investigacion` > skill orchestrators** (S73 búsqueda 4-way A/B/C/D actualizado). OpenAlex permite barrer toda la biblio de un autor por ID con metadata Crossref-verified. Skills tipo `deep-research` (B) orquestan pero usan WebSearch como backend → parafrasea DOIs → riesgo "vibe citing". Perplexity Academic vía Chrome (D) genera synthesis bien estructurada pero **0 papers nuevos específicos**. **Combo óptimo discovery: A + C** (manual + WebSearch arxiv). **Combo óptimo synthesis writing**: B (`deep-research` full mode) o D (Perplexity Academic).

**A41. `Claude_in_Chrome` MCP funciona para Perplexity Pro con sesión activa del usuario** (S73). Workflow validado: `list_connected_browsers` → `select_browser` → `tabs_context_mcp createIfEmpty:true` → **navegar directo URL pattern** `/search/new?q=<URL_ENCODED>&sources=scholar`. Evita problemas typing en contenteditable divs de Perplexity (textbox NO es `<input>`/`<textarea>` — `form_input` falla con error "DIV not supported"). Usar `computer` action `type` con `ref` post-click, o URL navigate directo (más confiable). No requiere `PERPLEXITY_API_KEY` env var — usa cookies de la sesión Chrome activa de Nicolás.

## Sincronización con BIBLIOGRAPHY_SYNTHESIS

`documentacion/BIBLIOGRAPHY_SYNTHESIS.md` (en worktree `VRP Chile/`, NO versionado en git) actualizado con sección "10. Búsqueda S73" en S73 cierre. Este doc (`F28_LIT_SEARCH_S73.md`) es la versión versionada del resumen ejecutivo + acciones.
