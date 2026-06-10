# AUDIT S105 — Auditoría integral del proyecto (protocolo A51)

**Fecha**: 2026-06-10 · Pedido explícito de Nicolás. 6 subagentes paralelos read-only
(misión/drifts, código, reglas/memoria, data, git/operacional, docs/frontend).
Anterior: `docs/AUDIT_S86.md` (19 sesiones atrás — A51 al filo del plazo).
**Corrección A48 aplicada**: el eje-2 marcó `enable_test1_local_bg_nti` "refutado" —
FALSO, está en A/B (runs 27275241269/27276651420) al momento de esta auditoría.

## Veredicto global

El proyecto está **operacionalmente sano** (NRT 93% success, data íntegra 11/11, 0 PRs
huérfanos, frontend casi sincronizado) pero acumula **deuda documental y de configuración
significativa**: el catálogo de divergencias y el gate de misión están desactualizados,
2 flags contradicen un veredicto de auditoría previa hace 19 sesiones, y ~14 ramas de
flags refutados cargan el código. Por regla A51 (>3 contradicciones cross-source →
**consolidar antes de seguir con features**), tras cerrar el A/B en vuelo corresponde
una pasada de consolidación.

## Contradicciones cross-source (gatillo A51: hay >3)

| # | Contradicción | Fuentes |
|---|---|---|
| 1 | Gates intra-radio S84/S85 **ON** pese a veredicto A55 de AUDIT_S86 §C6 (anti-patrón, redundantes con frontend) | mirova_equivalent.yaml ↔ AUDIT_S86 |
| 2 | MISSION.md tabla anti-patrones dice "pisos VRP removidos S27" pero los 3 `min_vrp_mw_*` están vivos (y el MODIS ajustado S102 con justificación empírica) | MISSION.md ↔ yaml |
| 3 | Worktree canónico: CLAUDE.md dice raíz `VRP Chile/`; MEMORY.md dice `VRP-Chile-s80-consolidation/`; git real: **solo la raíz está registrada** | CLAUDE.md ↔ MEMORY.md ↔ git |
| 4 | Cap MEMORY.md: header dice ≤500 líneas (M9); META_RULES_S80 M9 dice rotación a 800. Real: 573 | MEMORY.md ↔ META_RULES_S80 |
| 5 | SESSION_CLOSE_CHECKLIST manda actualizar SESSION_INDEX.md (superseded S80) y DRIFTS_S17.md (cerrado) | checklist ↔ práctica real |
| 6 | CLAUDE.md sección "## Estado" congelada en **S35** (~70 sesiones stale, pendientes ya resueltos como "en curso") | CLAUDE.md ↔ realidad |

## Hallazgos por eje (síntesis)

### Eje 1 — Misión y drifts
- **Resueltas con cierre formal**: D1, D4, D5 (nadir+ctxpeak), D8/D8', D6/D7, sec³ (S102/103), NEW-7.
- **Abiertas**: D9 (path D cirrus, mitigación parcial), D2 (cobertura CSV), NEW-8 gaps 2-4,
  VIIRS750 glaciar (Tupun/PP 16.6×).
- **MIROVA_DIVERGENCES.md al día solo hasta S103.** Faltan: fix del ancla S98, **A69 FP
  topográfico (S104) como divergencia formal** (riesgo de hallazgo dormido, patrón S99),
  Test1-NTI V1/V2 no promovidos, fondo-local-NTI en A/B.
- **MISSION.md pregunta 2 lista solo D1-D5** — el gate vinculante decide con catálogo stale.
- AUDIT_S86 matizado por S98-S105: "95.4% FP = realidad física" era sub-dimensionado en
  cat-d (sec³ probó artefactos 3-5× y A69 FP topográficos); S86 no detectó la regresión
  del ancla (activa entonces, descubierta S97).

### Eje 2 — Código
- **~14 ramas if de flags refutados/muertos** en process_*.py: nti_covalidation (V1),
  nti_integral (V2 como modo standalone), test1_pixel_filter (vetado S99, triplicado),
  lava_lake_eq16, spatial_core, daytime_modis (A/B nunca concluyó), nti_relative_path.
  NOTA: `enable_test1_local_bg_nti` NO es deuda — está en A/B en vuelo.
- **Asimetrías cross-sensor**: ctxpeak (S100) SOLO en VIIRS375 (pendiente conocido S102§2);
  compute_test1_nti solo VIIRS375. Ancla S98 y nadir S102-103 sí consistentes ✓.
- **Bug S101 §5.1 sin arreglar**: `final_hotspot_*` = píxel suelto scene-wide en rama
  eruption — **en los 3 sensores** (process_modis.py:1033, process_viirs.py:1428,
  process_viirs_mod.py:978). Mitigación parcial: cluster_rescue F47 en store.py.
- **Hotspots de mantenimiento**: calculate_vrp triplicada (~3060 líneas: 1241+933+886,
  anidamiento 5-6). Es el vector estructural de los bugs A37/A49.
- Tests: fetch/store/clustering cubiertos ✓; gaps en test1_contextual_filter (1 test,
  siendo la magnitud operacional S100), single_pixel_mode, anomaly_pixels.

### Eje 3 — Reglas y memoria
- CLAUDE.md "## Estado" = S35 (~70 sesiones stale). El estado real vive en MEMORY +
  bloques de arranque. **Ruido activo para sesiones frías.**
- A69-A72 **ya persistidas** en CLAUDE.md (la nota "pendiente" del arranque S105 es stale).
- MEMORY.md: 573 líneas (cap autoimpuesto 500). Candidatos a archivo: bloques S80-S89
  (~265 líneas). Falta entrada índice S104. Orden no cronológico.
- **Gap numérico A27-A34**: no existen en ningún doc (grep 0 hits). Documentar o renumerar.
- A51 vence ya (esta auditoría lo cumple). M4 (flags trimestral) sin evidencia de ejecución.

### Eje 4 — Data (sana)
- **Integridad 11/11 Tier A: OK** — parsean, cobertura diaria completa 30d, 0 duplicados,
  0 vrp negativos/NaN. Backfill uniforme desde 2026-01-29.
- Schema drift solo aditivo (campos discarded_*/vrp_mir_mw de S100-103); frontend sin riesgo.
- ⚠️ 2 records Villarrica 06-10 vent-path sin primary_cluster (pc=null, vrp>0) — patrón
  A46 menor, vigilar.
- **~750 MB de data/ A/B stale >1 mes** (top: mirova_equivalent_pre_s27 195 MB). Limpieza
  A38 (inventario + tag + OK Nicolás). 34 vols experimental congelados 04-25.

### Eje 5 — Git/operacional (sano, con housekeeping pendiente)
- NRT: 13/15 success (~93%), fallo único aislado (flakiness LANCE tolerada post-A64). ✓
- **15 workflows one-off activos** a archivar (S101-S104 ahora; S105 tras cerrar el A/B).
  `_archive/` existe con 44 — la política funciona, está atrasada.
- **~85-90 branches remotas squash-merged** borrables (deuda S100 que creció de 76).
- 52 tags pre-* sin política de expiración (costo bajo; definir criterio).
- Worktrees: git solo registra la raíz — la doc de worktrees en CLAUDE/MEMORY está stale.
- 0 PRs abiertos ✓.

### Eje 6 — Docs/frontend
- **111 docs sin índice maestro**; ~35-40 obsoletos (SESSION_INDEX superseded, brainstorms
  F60-F66 resueltos, cierres puntuales, DRIFTS_S17). Crear docs/INDEX.md + docs/archive/.
- **3 vistas frontend bien sincronizadas** (parseUtcMs/isCirrus/isDiffuse idénticas; F5'
  default Núcleo en las 3). 2 gaps menores: `diario.html:222` fallback sin cap 50000;
  mosaico sin toggle includeFar (¿deliberado? sin doc).
- **El gate central del frontend depende del campo corrupto**: `distance_class` (derivado
  del hotspot suelto) oculta HOY por accidente los MODIS inflados. Si se arregla el campo
  en pipeline sin tocar frontend, **reaparecen**. Acople ya documentado S101 §4.
- **README.md stale S19 (~86 sesiones)**: 4 volcanes (real 11), cron 6h (real 2h), sin
  NOAA-21/nadir/3 vistas. Es la cara pública del entregable SERNAGEOMIN.

## Plan de consolidación priorizado (propuesto, NO ejecutado)

**P0 — decisiones de Nicolás (bloquean el resto)**
1. Gates intra-radio S84/S85: ¿revertir (veredicto A55/S86) o re-justificar y documentar?
2. Pisos min_vrp_mw: reconciliar MISSION.md (actualizar tabla anti-patrones con la
   justificación S102) o remover pisos.
3. Limpieza data/ ~750 MB y branches ~85: OK para ejecutar con tag defensivo A38.

**P1 — consolidación documental (1 sesión, sin tocar pipeline)**
4. MIROVA_DIVERGENCES.md: agregar S98 ancla + A69 topográfico (divergencia formal) +
   V1/V2 no promovidos + fondo-local en A/B. Actualizar MISSION.md pregunta 2 (D1-D10+A69).
5. CLAUDE.md: reemplazar "## Estado" S35 por puntero a MEMORY + arranque. Corregir
   sección worktrees (solo raíz). MEMORY.md: rotar S80-S89 a archivo, unificar cap M9,
   agregar entrada S104.
6. README.md actualizar (cara pública). SESSION_CLOSE_CHECKLIST: refs frescas.
7. docs/INDEX.md maestro + mover ~35 obsoletos a docs/archive/ (tag defensivo).

**P2 — deuda de código (con A45, post-A/B)**
8. Purga de flags refutados (V1, pixel_filter, eq16, spatial_core, nti_relative) — decisión
   por flag: borrar rama o documentar por qué se conserva. V2/local: según resultado A/B.
9. Bug final_hotspot rama eruption (3 sensores) — acoplado al gate frontend (ver eje 6);
   diseñar juntos (el design doc S101 §5.1 ya lo scopea).
10. Portar ctxpeak a VIIRS750 (pendiente S102§2, cura dispersión glaciar V750).
11. Tests para test1_contextual_filter (magnitud operacional con 1 solo test).

**P3 — estructural (cuando haya ventana, idea para discutir)**
12. La triplicación calculate_vrp (~3060 líneas) es el vector de bugs A37/A49/F47.
    Evaluar extracción incremental de helpers compartidos (NO big-bang rewrite; el
    código operacional NRT manda — A45 estricto, un helper por PR con tests).

## Para el paper (subproducto de esta auditoría)
- La secuencia V1→V2→fondo-local (S104-S105) con predicciones pre-registradas es un
  case study metodológico completo (Methods/Validation).
- El re-diagnóstico MODIS S105 (subagente infló 10× con campos corruptos, atrapado por
  verificación A48/A10) es material de "lessons learned" sobre auditoría con LLMs.
- AUDIT_S86 → AUDIT_S105: la evolución del marco "95% FP físicos" → "FP topográficos
  sistemáticos en MIR-absoluto" documenta cómo el ground truth probe-based corrige
  conclusiones estadísticas agregadas.
