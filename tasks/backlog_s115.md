# Backlog S115

Items evaluados en S115 y diferidos con razón explícita.

## #5 — inner_radius PCC 20→10 km — RECHAZADO (MISSION)

**Decisión Nicolás (S115): no tocar el radio del pipeline.**

Razón "no cumple regla MIROVA literal":
- `inner_radius_km=20` para PCC es el **dato oficial MIROVA del KML** (A5, `volcanoes.yaml:17`).
  Bajarlo a 10 nos haría **más restrictivos que MIROVA** (ellos cuentan 15 km como "dentro";
  nosotros lo mandaríamos a `far`) → divergencia de clasificación.
- MISSION lo lista como **anti-patrón** (`docs/MISSION.md` línea 128: "Subir inner_radius_km
  ad-hoc — Rechazado S27"; H_S27_5 "RECHAZADA"). Las 3 preguntas dan NO en la cara pipeline.
- Toca `store.py` (`distance_class` + guard A46 S113) → A18 (reproc real obligatorio, el
  inner_radius afecta `cluster_hotspots`) + A45 (tag + OK Nicolás).
- Por **A72**: la cola 8.5–20 km es **artefacto cirrus** (A23/D9) → la raíz se ataca en el
  **algoritmo (D9)**, no escondiéndola con un radio de display.

**Datos S115** (PCC summit+vrp>0, n=1229, mediana 1.41 km): 82.7% del lacolito real cae ≤8.5 km
(0–5: 920; 5–8.5: 95); cola 8.5–20 km = 214 records (17.4%, cirrus/distante). Confirma el
constraint "lacolito real ≤8.5 km".

**Alternativa MISSION-compliant SI se quiere atacar el display** (frontend puro, MISSION
pregunta 3): el mecanismo `geo_class="extension"` (naranja #ff9800, S88/S90) **hoy NO se aplica
a PCC** (sus records tienen `geo_class` = summit/None). Esa sería la palanca de display real —
render naranja para la extensión cat-b, sin tocar clasificación ni zeroing. Requiere diseño
frontend dedicado. NO es prioridad (Nicolás eligió "no tocar" en S115).

## Deuda — cabeceras FICHA SDA en archivos núcleo (CPLT N°372)

**Decisión Nicolás (S115): backlog para sesión dedicada de transparencia.**

La regla SDA (CLAUDE.md raíz Volcanologia + `GUIA_MAESTRA_TRANSPARENCIA_ALGORITMICA.md`) exige
cabecera FICHA en todo archivo que participe en la detección/clasificación. Estado S115:
- **Con cabecera FICHA**: `pipeline/anchor.py`, `pipeline/vrp_regimes.py`.
- **SIN cabecera (gap)**: `pipeline/process_modis.py`, `pipeline/process_viirs.py`,
  `pipeline/process_viirs_mod.py`, `pipeline/store.py` — son el núcleo de detección/clasificación.

Agregarlas = solo comentarios (sin lógica), pero toca `pipeline/` → requiere **A45** (tag
defensivo + verificar suite). La **ficha publicable** (`docs/FICHA_SDA_VRP_CHILE.md`) ya está al
día (v1.0 — 2026-06-22, S115). Las cabeceras de código son complemento de trazabilidad, no
bloquean la publicación de la ficha.
