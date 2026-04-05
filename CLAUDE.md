## Workflow Orchestration

### 1. Plan Mode Default
- Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions)
- If something goes sideways, STOP and re-plan immediately - don't keep pushing
- Use plan mode for verification steps, not just building
- Write detailed specs upfront to reduce ambiguity
- For satellite data pipelines: plan the full fetch → process → validate → store → render chain before coding

### 2. Subagent Strategy
- Offload research, exploration, and parallel analysis to subagents
- One task per subagent for focused execution
- For multi-sensor analysis: one subagent per sensor (MODIS Terra, MODIS Aqua, VIIRS I-band, VIIRS M-band)
- Cap at 3-5 parallel subagents to avoid supervisor bottleneck

### 3. Self-Improvement Loop
- After ANY correction: update 'tasks/lessons.md' with the pattern
- Scientific corrections are critical: if a VRP calculation, spectral band interpretation, or NTI threshold is wrong, document the correct methodology permanently
- Review lessons at session start

### 4. Verification Before Done
- Never mark a task complete without proving it works
- For VRP calculations: verify against MIROVA reference data and known eruption events
- For satellite processing: confirm spectral bands, units (W/m²/sr/μm), and pixel area match NASA documentation
- Evidence chain required: test command → actual output → verification against calibration data
- Run `python pipeline/process_modis.py` and `python pipeline/process_viirs.py` to confirm pipeline integrity

### 5. Demand Elegance (Balanced)
- For non-trivial changes: pause and ask "is there a more elegant way?"
- Skip this for simple fixes - don't over-engineer
- Challenge your own work before presenting it

### 6. Autonomous Bug Fixing
- When given a bug report: just fix it
- Point at logs, errors, failing tests → then resolve them
- For pipeline bugs: check NASA product availability first (NOAA-20 multi-version, missing granules)

### 7. Scientific Rigor
- Never approximate physical constants — use exact values from Coppola et al. papers
- VRP formula (Wooster MIR): `VRP = 18.9 × A_pix × ΔL_MIR` (NOT Stefan-Boltzmann)
- NTI threshold: 3σ above background, minimum 0.005
- Nighttime-only processing for MIR bands (solar contamination in daytime)
- Always cite the source paper for any methodology change
- If in doubt about a scientific method, say so — never guess with geophysical data

## Task Management

1. **Plan First**: Write plan to 'tasks/todo.md' with checkable items
2. **Verify Plan**: Check in before starting implementation
3. **Track Progress**: Mark items complete as you go
4. **Explain Changes**: High-level summary with the reasoning behind decisions
5. **Document Results**: Add review to 'tasks/todo.md'
6. **Capture Lessons**: Update 'tasks/lessons.md' after corrections

## Core Principles

- **Simplicity First**: Make every change as simple as possible. Impact minimal code.
- **No Laziness**: Find root causes. No temporary fixes. Senior developer standards.
- **Minimal Impact**: Changes should only touch what's necessary.
- **Data Integrity**: Raw satellite data (L1B, GeoTIFF) is NEVER modified. Processing outputs are always regenerable.
- **Reproducibility**: Every pipeline step must be reproducible. Document parameters and sensor versions.

## Project Context

### Architecture
```
VRP Chile/
├── pipeline/
│   ├── fetch.py          — NASA Earthdata download (earthaccess)
│   ├── process_modis.py  — MODIS Band 21/22 (3.93μm, 1km)
│   ├── process_viirs.py  — VIIRS I-band I04/I05 (375m)
│   ├── process_viirs_mod.py — VIIRS M-band M13 (750m)
│   └── store.py          — JSON persistence
├── frontend/index.html   — MIROVA-style Chart.js dashboard
├── volcanoes.yaml        — Volcano config (coords, radii)
├── .github/workflows/nrt.yml — 6-hourly NRT automation
└── Historial_*.csv       — Validated detection history
```

### Current State
- 4 volcanoes active (Puyehue-CC, Villarrica, Láscar, Copahue)
- Goal: expand to 43 volcanoes (Copernicus-v1 list)
- Nighttime-only filter active, 12/12 detections validated
- Next priorities: cloud masking, expand volcano coverage, commit calibrated data

### Technical Constraints
- NASA Earthdata authentication required (user has account)
- NASA LANCE NRT: ~3h latency
- GitHub Actions: 6-hourly runs, limited compute
- MODIS bands 21/22 (3.929μm / 3.959μm), VIIRS I04 (3.74μm) / I05 (11.45μm)
- NOAA-20 products: search multiple versions (v2, v2.1) for availability

### User (Nicolás)
- Geologist at SERNAGEOMIN (Chilean geological survey)
- Prefers detailed explanations with reasoning ("why" before "how")
- Spanish-language communication
- Goal: independence from mirovaweb.it, own scientific capability
