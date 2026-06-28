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
- Por **A72**: la cola >8.5 km es mayormente **artefacto de dispersión VIIRS750** (A19/A66, el
  centroide vaga sobre glaciar/bosque) — NO cirrus MODIS (solo 3 de 219 son MODIS). El centroide
  del cluster YA la ignora (no contamina posición ni magnitud) → el residuo es cosmético en el mapa.

**Datos S115 (CORREGIDO post-verificación adversarial — ver `reference_s115_pcc_anchor_parity`)**:
PCC summit+vrp>0 n=1254. **⚠️ El `centroid_dist_km` se mide desde el ancla LACOLITO**
(`vent_lat/lon` PCC = −40.5255,−72.1461), NO desde el GVP Puyehue. Por eso la "mediana 1.41 km"
NO significa que detectemos proximal — re-anclado al GVP (apples-to-apples con MIROVA `Distancia_km`)
nuestra mediana es **7.78 km ≈ MIROVA 7.83 km**, y el centroide cae a 0.39 km del píxel-pico MIROVA
en el TIF. **Nuestro cluster está ALINEADO con MIROVA en el lacolito Cordón Caulle (~7.8 km NNW de
Puyehue); NO desalineado.** La cola >8.5 km (del ancla lacolito) = 219 records: ~73% artefacto
dispersión VIIRS750, 21% cat-b plausible NW, 6% MIROVA-confirmada. 72/119 días de cola sin ALERTA
MIROVA. Lección A3/A61: comparar distancias vs MIROVA EXIGE re-anclar al GVP (esto confundió la
lectura preliminar).

**Alternativa MISSION-compliant SI se quiere atacar el display** (frontend puro, MISSION
pregunta 3): el mecanismo `geo_class="extension"` (naranja #ff9800, S88/S90) **hoy NO se aplica
a PCC** (sus records tienen `geo_class` = summit/None). Esa sería la palanca de display real —
render naranja para la extensión cat-b, sin tocar clasificación ni zeroing. Requiere diseño
frontend dedicado. NO es prioridad (Nicolás eligió "no tocar" en S115).

## Deuda — cabeceras FICHA SDA en archivos núcleo (CPLT N°372) — ✅ RESUELTO S116

**RESUELTO S116** (sprint de consolidación AUDIT_S116, OK explícito de Nicolás, A45 con tag
`pre-s116-ficha-headers`): se agregaron las 6 cabeceras FICHA SDA Nivel-1 (comment-only, 0 lógica,
suite 791 passed). Ficha publicable → v1.1. Pendiente solo la pasada exhaustiva opcional a los ~11
módulos de detección secundarios (`test1_*`, `path_d_*`, `second_pass_*`, `exclusion_zones`,
`single_pixel_mode`) — backlog de menor prioridad. El registro histórico abajo se conserva.

**Decisión Nicolás (S115): backlog para sesión dedicada de transparencia.**

La regla SDA (CLAUDE.md raíz Volcanologia + `GUIA_MAESTRA_TRANSPARENCIA_ALGORITMICA.md`) exige
cabecera FICHA Nivel-1 (la caja `════ FICHA SDA ════`) en todo archivo que participe en la
detección/clasificación. Estado **CORREGIDO S116** (AUDIT_S116 C1 — el inventario S115 era
erróneo):
- **Con cabecera FICHA Nivel-1**: **solo `pipeline/vrp_regimes.py`** (formato canónico, líneas 1-16).
  ⚠️ `pipeline/anchor.py` **NO la tiene** — el inventario S115 la dio por presente, pero solo tiene
  un docstring + un comentario etiquetado "Nivel 2" interno (`honest_anchor_applies`). El grep
  `FICHA SDA` matcheó por substring. `anchor.py` participa en la clasificación (cascada de posición
  → `distance_class`) → **necesita Nivel-1**.
- **SIN cabecera (gap real = 6 archivos núcleo)**: `pipeline/process_modis.py`, `pipeline/process_viirs.py`,
  `pipeline/process_viirs_mod.py`, `pipeline/store.py`, **`pipeline/anchor.py`**, `pipeline/detection_context.py`
  (gate dNTI contextual — decide si un píxel se detecta). El contenido propuesto de cada cabecera
  está en `experiments/_s116_audit/eje6_transparencia.json`.
- **NO requieren Nivel-1** (logística/IO/auditoría, excluidos Res.372 4.8): `fetch.py`, `scan_geometry.py`,
  `clustering.py`, `audit_metrics.py`, loaders/constantes/utils.

Agregarlas = solo comentarios (sin lógica), pero toca `pipeline/` → requiere **A45** (tag
defensivo + verificar suite). La **ficha publicable** (`docs/FICHA_SDA_VRP_CHILE.md`) ya está al
día (v1.0 — 2026-06-22, S115). Las cabeceras de código son complemento de trazabilidad, no
bloquean la publicación de la ficha.
