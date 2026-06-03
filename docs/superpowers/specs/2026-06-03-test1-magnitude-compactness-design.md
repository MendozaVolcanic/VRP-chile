# Diseño S99 — Fix de magnitud Test 1 (compacidad espacial vs filtro por-píxel)

**Fecha**: 2026-06-03 · **Sesión**: S99 · **Estado**: DISEÑO (pendiente OK Nicolás).
**Origen**: §2 BLOQUE_ARRANQUE_S99 (19× Tupungatito) + auditoría S99
(`docs/S99_AUDIT_SYNTHESIS.md`, evidencia en `experiments/_s99_audit/`).

## 1. Problema (causa raíz confirmada en código + datos)

El Test 1 integrado-ROI (Coppola 2015, `pipeline/test1_integrated.py`) es un test de
**detección** sub-píxel: contesta "¿hay anomalía extendida en el ROI de 3 km?". Su
`mask_contributing` (línea 141) marca **todo píxel del ROI con radiancia > mediana del
fondo, por mínimo que sea el exceso**.

Cuando ese test es la fuente (`final_hotspot_source == "test1"`), el VRP se computa
sumando el VRP per-píxel de **todos** esos píxeles
([process_viirs.py:1446-1458](../../pipeline/process_viirs.py) y `:1474-1526`). El
comentario en `:1411-1415` ya lo documenta: *"nuestra mask test1_hot suma 14-49 pixels
marginales → factor 8-30× MIROVA"*.

**Error conceptual**: usamos el set de detección como el set de píxeles del foco. Sobre
el glaciar nevado de Tupungatito (5682 m), "todo lo que supera la mediana fría" = el
mosaico nieve/roca entero (anillo difuso de 1-3 km). MIROVA detecta con Test 1 pero
reporta el **foco compacto** → se queda plano en ~0.2 MW todo el año.

### Evidencia (S99, reproducible)
- **MIROVA no infla estacionalmente** (`latest_consolidado.csv`): VIIRS375 Tupungatito
  mediana de detecciones feb 0.24 / mar 0.22 / abr 0.24 / may 0.21 MW (plano). MODIS = 0
  detecciones (ciego). Lo que crece es nº de noches, no la magnitud/detección.
- **Nosotros inflamos** (`experiments/_s99_audit/`): cluster 2 px (marzo) → ~100 px
  (mayo) en disco/anillo 0.1-3.0 km (mediana 2.14 km), BT 250-274 K (glaciar frío).
  Solo ~7.3% de los px caen <0.75 km del pico; ~90% es halo lejano.
- **No es código nuestro que cambió** (`git_forensics.md`): mismo binario procesó
  mar y abr; el código viejo S65 muestra el mismo crecimiento → es input estacional.
- **Discriminante = ESPACIAL, no térmico**: gate por t_bg REFUTADO con datos (los
  records correctos de marzo también tienen t_bg 270-271 K). Coincide A54/S86.

## 2. Objetivo y criterios de aceptación

Que el `primary_cluster.vrp_mw` y `vrp_mir_mw` **almacenados** de records VIIRS375
fuente Test 1 reflejen el foco compacto (≈ MIROVA), SIN introducir falso negativo en
anomalías sub-píxel genuinas (lava lake Villarrica 0.05-0.21 MW).

1. **Tupungatito** (Test 1, invierno): ratio mediano Cluster/MIROVA de ~19× → banda
   [0.5, 2.0].
2. **Villarrica (CANARIO FN)**: recall vs MIROVA NO baja; las detecciones Test 1
   (lava lake) conservan VRP > 0. Es el criterio que puede vetar un candidato.
3. **Láscar (control, cráter compacto)**: magnitud y recall sin cambio.
4. **Recall global NO baja**.

## 3. Candidatos a medir (A/B real, A18)

| | Mecanismo | Costo | Riesgo |
|---|---|---|---|
| **Baseline** | actual, `ENABLE_TEST1_PIXEL_FILTER=False` | 0 | inflación 8-30× |
| **Cand. A** | `ENABLE_TEST1_PIXEL_FILTER` (ya existe, `:1417-1431`): intersecta test1_hot con umbral dual-ROI BT 5σ/10σ (Coppola 2016a Tabla 1) | flip flag + perfiles ya existen | **FN Villarrica**: lava lake sub-píxel no supera 5σ por-píxel → VRP=0 |
| **Cand. B** | NUEVO `ENABLE_TEST1_SPATIAL_CORE` (default OFF): suma solo píxeles a ≤ R_core del píxel de MÁXIMA energía; **siempre conserva el pico** (guard anti-FN); opcional `bt_k≥BT_EXT_K` para lava extendida real | implementar branch flag-gated + TDD | R_core arbitrario; sobre-corrige sanos; mitigado por peak-keep |

Cand. B es el análogo en pipeline del Núcleo F5' display (`f5CoreMagnitude`,
frontend/index.html), que ya está validado como físicamente correcto para este modo de
falla (recorta el anillo nival, conserva el foco). R_core=0.75 km y BT_EXT_K=295 K como
punto de partida (mismos que S95), a calibrar con el A/B.

## 4. Mecánica del A/B (A18 + A47 + A45)

- **3 perfiles aislados** con `data_subdir` propio (A47, sin race):
  `_s99_test1_baseline` / `_s99_test1_pixfilter` (Cand A) / `_s99_test1_core` (Cand B).
- **Volcanes**: Tupungatito (cura) + Villarrica (canario FN) + Láscar (control). Los 3
  son VIIRS375 → reproc **local** en Windows (no requiere Linux/MODIS).
- **Ventana**: 2026-04-01 .. 2026-05-31 (captura inflación invernal Tupun + detecciones
  Villarrica). Ground truth = `latest_consolidado.csv` + OCR (cubren feb-jun, A17).
- **Reproc secuencial** dentro de un solo proceso por perfil (A47: nunca paralelo sobre
  el mismo data_subdir).
- **Auditoría**: reusar `experiments/_s98_anchor/audit_ratio.py` (matching CONS+OCR,
  A14) + medir recall por volcán y ratio por sensor. Script nuevo
  `experiments/_s99_audit/ab_test1_audit.py`, números reproducibles (S91).
- **A45**: implementar Cand. B toca `pipeline/process_viirs.py` → tag defensivo
  `pre-s99-test1-spatial-core` ANTES del primer edit + **OK explícito de Nicolás**.
  El flag entra default OFF (no cambia operacional hasta adoptar).

## 5. Plan de implementación (post-aprobación diseño)

1. `git tag pre-s99-test1-spatial-core <sha>` + push (A45).
2. **TDD** (`test-driven-development`): test que captura (a) inflación del halo nival
   sintético se desinfla con Cand B, (b) un foco compacto sub-píxel (Villarrica-like)
   conserva VRP>0 con Cand B. Tests primero, rojo, después implementación.
3. Implementar `ENABLE_TEST1_SPATIAL_CORE` flag-gated en process_viirs.py (default OFF),
   reutilizando la lógica de compacidad del Núcleo. Suite verde, 0 regresiones.
4. Crear 3 perfiles A/B aislados.
5. Reproc local secuencial 3 vols × 3 perfiles, ventana abr-may.
6. `ab_test1_audit.py` → tabla magnitud + recall por candidato/volcán.
7. **Veredicto** contra criterios §2 (Villarrica es veto). Presentar a Nicolás.
8. Si gana un candidato: adoptar (flip flag en `mirova_equivalent.yaml`) con A45 + reproc
   operacional + verificación 3 vistas + R8 público. Si ninguno cumple, documentar y
   quedarnos con el Núcleo display.

## 6. Pre-mortem (R4)
- **Cand A mata Villarrica** (FN) → lo descarta el criterio 2; por eso medimos juntos.
- **Cand B sobre-corrige sanos** (PCC/PP/Chaitén ya calibran bien crudos) → por eso solo
  aplica a la rama Test 1, no al cluster general; los sanos no van por Test 1.
- **R_core mal calibrado** → A/B con 1-2 valores (0.5, 0.75) si 0.75 no cierra.
- **Preview offline engaña** (A18) → solo el reproc real decide.
- **Alcance**: este fix es VIIRS375/Test 1. El PCC >1000 MW de MODIS (campo difuso,
  MIROVA=0) y el popup del mapa son frentes separados (ver §7).

## 7. Fuera de alcance (frentes separados, documentados)
- **PCC MODIS cientos de MW**: MIROVA reporta 0 desde MODIS (ciego a sub-píxel). Es
  campo difuso warm-scene (A23/A18), NO es Test1/VIIRS375. Fix propio futuro.
- **Popup del mapa muestra suma scene-wide cruda** (`index.html:2455`) = el ">1000 MW"
  que vio Nicolás. Fix display separado (quick win, 3 vistas).
- **¿Mantener Cluster + Núcleo display?**: sí (S99 audit): sirven a regímenes distintos.
