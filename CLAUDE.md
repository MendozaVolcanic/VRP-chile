# VRP Chile

Sistema VRP independiente para volcanes chilenos (equivalente MIROVA, propio).
Repo: https://github.com/MendozaVolcanic/VRP-chile

## Reglas científicas (no negociables)
- **VRP MIR (Wooster)**: `VRP = 18.9 × A_pix × ΔL_MIR` — Coppola 2015 Eq.7. NO Stefan-Boltzmann.
- **VRP TIR (I05)**: Stefan-Boltzmann (Aveni 2024).
- **NTI**: umbral 3σ sobre background, mínimo 0.005.
- **MIR solo nocturno** (contaminación solar diurna).
- Bandas: MODIS 21/22 (3.929/3.959 μm), VIIRS I04 (3.74 μm) / I05 (11.45 μm).
- Constantes físicas **exactas** de los papers, nunca aproximar. Citar paper en cualquier cambio metodológico.
- Si dudas de un método con datos geofísicos, **dilo** — nunca adivines.

## Arquitectura
- `pipeline/`: fetch.py (earthaccess), process_modis.py, process_viirs.py, process_viirs_mod.py, store.py, scan_geometry.py
- `frontend/index.html` (Chart.js + Leaflet, GitHub Pages)
- `volcanoes.yaml` (45 configurados, 11 con data, 34 sin pull)
- `.github/workflows/nrt.yml` (cron 6h)
- `data/` JSON por volcán (committed). Raw L1B/HDF **nunca** committed.

## Constraints técnicos
- **pyhdf roto en Windows** → MODIS solo corre en GitHub Actions Linux.
- NASA LANCE NRT ~3h latencia.
- NOAA-20: buscar v2 **y** v2.1 (disponibilidad variable).
- Secrets en GitHub: EARTHDATA_USERNAME, EARTHDATA_PASSWORD.

## Estado
Calibración de sesiones 4-5 **INVALIDADA** en sesión 8 (refs OCR-noisy + pairing débil + sin contar FPs). **No hay baseline validado** hasta terminar auditoría estricta. Leer `tasks/todo.md` antes de cualquier "fix" y `tasks/lessons.md` L7.6-L7.9 para el diagnóstico. Detalles históricos en memoria `project_vrp_chile.md`.
