# Design — Ancla de detección/clustering = cráter, no centro del grid (S97→S98)

**Estado**: diseño aprobado-pendiente. Brainstorm S97 (contexto fresco). **Implementación
S98** (decisión Nicolás: diseñar ahora, ejecutar próxima sesión con A45 + reproc).
Enfoque elegido: **B (separar roles)**. Alcance 1er fix: **solo el ancla** (medir, después
decidir sobre selección de cluster).

## Problema (diagnóstico S97, ver docs/S97_TUPUNGATITO_ROOTCAUSE.md)
`get_effective_vent()` (geo_utils.py) devuelve `mirova_center` (centro del recuadro KMZ) con
prioridad sobre `vent_lat` (cráter). Para Tupungatito el centro del grid está **4.86 km al
sur del cráter** (PCC 7.57, PP 2.02; los otros 8 <0.55 km). Ese punto se usa como ancla en
**4 lugares** (mapa de impacto, subagente code-paths S97):
1. `process_viirs.py:511` — distancia por-píxel para la **detección dual-ROI** (summit 5σ vs
   scene 10σ). → la zona "summit sensible" queda 4.86 km al sur del cráter.
2. `clustering.py:116` (`vent_anchored`) — **selección de cluster** primario por proximidad
   al ancla. → elige el campo glaciar del centro del grid, no el cráter.
3. `process_viirs.py:1398` — **distance_class** (summit/far). → el cráter real queda "far".
4. gates intra-radio (path_d, second_pass) — enmascaran fuera del radio del ancla.

**Evidencia de que MIROVA reporta el cráter** (no el centro del grid): MIROVA reporta
Tupungatito a dist consistente ~5.2 km ≈ offset cráter↔centro (4.86). Hipótesis Nicolás
(autoridad): MIROVA mide la distancia desde el centro del recuadro TIF/KMZ y reporta el
cráter. Cross-volcán: el desplazamiento aparece SOLO en los de offset grande (Tupun/PCC/PP);
los 8 chicos detectan bien en el cráter.

**Por qué seguía roto**: S65 (PR #93) ya lo arregló (quitó mirova_center de Tupungatito →
ancla cae a vent_lat; validado S66: 56% curado, ratio 0.67×). **S80 (PR #220) regeneró los 11
mirova_center desde el KMZ → revirtió el fix.** Regresión-por-consolidación.

## Decisión: Enfoque B — separar roles
Hoy `mirova_center` cumple DOS roles conflados. Separarlos:
- **`get_grid_center(volcano)`** → `mirova_center` (o fallback). Uso: extent del grid/ROI +
  (opcional) cross-check contra la distancia reportada por MIROVA en auditorías. Fiel a la
  grilla de MIROVA.
- **`get_detection_anchor(volcano)`** → **`vent_lat/vent_lon` (cráter)** con prioridad, luego
  mirova_center, luego lat/lon. Uso: ancla de detección dual-ROI (#1), ancla de clustering
  vent_anchored (#2), y referencia de distance_class + distancia mostrada (#3).
- Gates intra-radio (#4): ya identificados redundantes S86 (A55) — fuera de scope de este
  fix; revisar por separado.

**Uniforme para los 11 (sin special-casing per-volcán)** → robusto a futuras consolidaciones
(la causa de la regresión S80 fue el special-case "quitar mirova_center de Tupungatito" que
se perdió). Para los 8 de offset <0.55 km, vent_lat ≈ mirova_center → cambio nulo. Para
Tupun/PCC/PP, el ancla se mueve al cráter.

### Distancia mostrada vs distancia MIROVA (decisión)
- **distance_class + distancia en tarjeta/mapa = desde el cráter** (vent_lat) → honesto e
  intuitivo (Tupungatito mostrará la distancia real al lago, no "0.8 km" falso).
- La distancia "estilo MIROVA" (desde el centro del grid) queda SOLO para el cross-check de
  auditoría (no para el display).

## Cambios de código (S98, A45)
1. `pipeline/geo_utils.py`: dividir `get_effective_vent` en `get_grid_center` +
   `get_detection_anchor` (vent_lat prioritario). Mantener `get_effective_vent` como alias
   deprecado si hay callers externos, o migrar todos.
2. `scripts/run_pipeline.py:202/245/291`: pasar `get_detection_anchor` como ancla de
   detección/clustering (lo que hoy es eff_vent). Pasar `get_grid_center` donde se necesite
   el extent del grid (revisar process_*.calculate_vrp firma).
3. `process_viirs.py` / `process_modis.py` / `process_viirs_mod.py`: el `vent_lat/lon` que
   reciben (para dual-ROI #1, clustering #2, distance_class #3) ahora es el cráter.
4. Verificar que el extent del grid/ROI (radius_km bbox) siga usando el grid center si
   corresponde (no romper la paridad de grilla MIROVA).

## Test de regresión (la salvaguarda que faltó)
`tests/test_detection_anchor.py` (TDD, escribir ANTES del fix):
- Para Tupun/PCC/PP: `get_detection_anchor()` devuelve el `vent_lat` (cráter), NO el
  mirova_center. Falla si alguien revierte (como S80).
- Para los 8 chicos: anchor ≈ mirova_center (offset <1 km) — sin cambio.
- Caso sintético: cluster cerca del cráter + cluster glaciar lejos → con anchor=cráter, el
  primary es el del cráter y distance_class=summit.

## Validación (A45 + reproc, A18: preview NO predice cluster selection)
1. `git tag pre-s98-detection-anchor` + push.
2. Reproc VIIRS de Tupun/PCC/PP + 2 controles (Lascar, Villarrica) sobre la ventana mayo
   (donde hay TIF + ground truth), a un data_subdir aislado.
3. Métricas (script reproducible, integridad §0.5):
   - **det→cráter** (mediana) DEBE bajar de ~5.9 a <2 km en Tupungatito (y PP, PCC según
     difuso).
   - **ratio Núcleo/MIROVA y Cluster/MIROVA** hacia 0.5-2.0 (S66 dio 0.67× en los curados).
   - **recall** NO debe caer; **los 8 controles NO deben cambiar** (offset <0.55).
4. Audit independiente + OK Nicolás antes de promover a operacional.

## Criterios de aceptación
- Tupungatito: mediana det→cráter <2 km (hoy 5.86); 0 regresión de recall.
- Los 8 de offset chico: sin cambio observable (anchor ≈ igual).
- Test de regresión verde; guard contra revert por consolidación.

## Pendiente para DESPUÉS (no en este fix)
- El 44% que S65 no curó: selección de cluster por VRP sumado vs pico NTI (estilo MIROVA).
  Medir cuánto cura B primero; si queda gap, su propio brainstorm/fix.
- Decisión de fondo C (sacar vent_anchored, replicar dual-ROI fiel) — objetivo mayor.
- Gates intra-radio redundantes (A55) — revisar/remover por separado.

## Handoff S98 (qué ejecutar)
1. Leer este doc + docs/S97_TUPUNGATITO_ROOTCAUSE.md.
2. TDD: escribir tests/test_detection_anchor.py (rojo).
3. Implementar B en geo_utils.py + callers. A45: tag primero.
4. Reproc validación (nube/local) + audit + OK Nicolás → promover.
