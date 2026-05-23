# F2.8 Búsqueda bibliográfica S73 — MIROVA post-2024 + saturation handling

**Sesión**: S73 (2026-05-23)
**Trigger**: Nicolás pidió evaluar si las skills nuevas instaladas (post-S72) aportan algo a búsqueda bibliográfica.

## Target

¿Hay literatura POST-2024 que (a) actualice el algoritmo MIROVA o thresholds, o (b) discuta saturation handling en sistemas VRP-like más allá de Wooster 2003?

## Experimento 3-way A/B/C

3 búsquedas paralelas con misma query target, distintos approaches:

| ID | Approach | Skill / Tool |
|---|---|---|
| **A** | Workflow viejo (control) | `investigacion` skill manual + Crossref + OpenAlex + arXiv MCP |
| **B** | Skill nueva orchestrator | `deep-research` skill (13-agent pipeline) |
| **C** | External web search | WebSearch built-in tool |

## Resultados comparativos

| Approach | Cobertura | DOIs verified | Speed | Recommendation |
|---|---|---|---|---|
| **A (investigacion manual)** | 9 papers — Coppola author-ID OpenAlex barre TODA su biblio post-2024 | ✓ Crossref-verified | 6 min | **Default para queries dirigidas** |
| **B (deep-research skill)** | 6 papers, 5 overlap A | WebSearch paraphrased | 1.5 min | **Solo full mode synthesis, NO para lookups** |
| **C (WebSearch)** | 3 papers únicos — captura arxiv pre-prints que A/B miss | WebSearch | 3 min | **Complemento arxiv para A** |

### Verdict sobre skills nuevas

**Las skills nuevas (B) NO aportaron exclusividad** para búsquedas bibliográficas dirigidas. Su backend es el mismo WebSearch que C, y no tienen acceso a `paperzilla` ni `bgpt-paper-search` cargados. La skill `deep-research` brilla en **full mode synthesis (reportes APA-7 completos)**, no en lookups.

**Combo operacional óptimo para queries bibliográficas dirigidas**: **A + C**
- A barre la bibliografía completa de un autor via OpenAlex author IDs
- C complementa con arxiv pre-prints fuera de Crossref

**NO usar B `deep-research` para "encontrame N papers"** — overhead alto, ganancia baja.

## Hallazgos prioritarios (3 papers nuevos críticos)

### 🎯 1. Dhage 2025 — VIIRS undocumented filtering

- **DOI/Source**: arxiv:2510.26816 (Nov 2025)
- **Autor**: Rohit Rajendra Dhage
- **Aporte**: documenta filtering no documentado en VIIRS Active Fire Product. Low-confidence nighttime detections systematically excluded.
- **Relevancia VRP Chile**: **VALIDACIÓN INDEPENDIENTE A37** (VIIRS y MODIS L1B usan esquemas distintos, downstream consumers deben leer quality flags + ser defensivos). Recomendaciones del paper coinciden 1:1 con nuestro fix F2.8 H2.
- **Encontrado solo por C** (arxiv pre-print fuera de Crossref)
- **Acción S74**: download + procesar + considerar citar en paper VRP Chile P5

### 🎯 2. Aveni 2025 — VRPTIR crater lakes + hydrothermal

- **DOI**: 10.1029/2024GL113324 (GRL, 2025)
- **Autores**: Aveni S. (Sapienza Roma) — grupo MIROVA canónico
- **Aporte**: extension TIRVolcH (Aveni 2024 RSE) a crater lakes + hydrothermal systems usando single TIR band
- **Relevancia VRP Chile**: **Primer update canónico post-Coppola 2025 cap.11**. Validación contra Ruapehu (precedente para PCC laguna lacolito). **ALTA relevancia P3 T1.5** (drift remanente Villarrica lava lake, PCC, Chaiten crater lake).
- **Encontrado por A + B + C** (DOI verificado)
- **Acción S74**: download (AGU paywalled, probar preprint EarthArXiv) + procesar

### 🎯 3. Coppola 2026 — Lascar SO2 multiparametric

- **DOI**: 10.2139/ssrn.6481652 (SSRN preprint open access)
- **Autor**: Coppola
- **Aporte**: VRP+SO2 integrado Lascar 2017-2021 — **volcán chileno Tier A NUESTRO**
- **Relevancia VRP Chile**: integración futura con OVDAS, dataset extension
- **Encontrado solo por A** (OpenAlex barrido autor)
- **Acción S74**: download cuando se trabaje P5 (paper VRP Chile)

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

**A40. Para queries bibliográficas dirigidas, manual `investigacion` > skill orchestrators** (S73 búsqueda 3-way). OpenAlex permite barrer toda la biblio de un autor por ID, con metadata Crossref-verified. Skills tipo `deep-research` orquestan pero usan WebSearch como backend (parafrasea DOIs → riesgo "vibe citing"). **Combo óptimo: A (manual) + C (WebSearch dirigido a arxiv pre-prints)**.

## Sincronización con BIBLIOGRAPHY_SYNTHESIS

`documentacion/BIBLIOGRAPHY_SYNTHESIS.md` (en worktree `VRP Chile/`, NO versionado en git) actualizado con sección "10. Búsqueda S73" en S73 cierre. Este doc (`F28_LIT_SEARCH_S73.md`) es la versión versionada del resumen ejecutivo + acciones.
