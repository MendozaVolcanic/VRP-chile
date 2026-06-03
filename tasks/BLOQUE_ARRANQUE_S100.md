# BLOQUE ARRANQUE S100

**Sesión previa S99 (2026-06-03).** Muy larga. 7 PRs (#324-330), 3 A/B VIIRS corridos.
main al día. Foco: fix de magnitud 19× Tupungatito (VIIRS375 Test1) + auditoría
retrospectiva de hallazgos dormidos + blindaje de guías. Detalle:
`docs/S99_TEST1_AB_RESULTS.md`, `docs/S99_DORMANT_FINDINGS_AUDIT.md`,
`docs/S99_AUDIT_SYNTHESIS.md`, `docs/MISSION.md` (regla verbatim nueva).

## §0 — Primer comando
```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
git fetch origin --prune && git pull --ff-only
cat docs/S99_TEST1_AB_RESULTS.md   # tabla A/B + veredicto candidatos
cat tasks/BLOQUE_ARRANQUE_S100.md
```

## §1 — PRIORIDAD: cerrar el fix de magnitud VIIRS Test1 (A/B en vuelo)

**Estado: A/B del híbrido CORRIENDO al cierre S99.** Run **26903265998**
(perfiles `_s99_test1_baseline` / `_s99_test1_core` / `_s99_test1_ctxpeak` ×
Tupun/Villarrica/Lascar, ventana 2026-04-01..05-31). Tarda **~5 h** (download VIIRS).

**Al terminar — un comando:**
```bash
gh run download 26903265998 -D experiments/_s99_audit/_ab_art
python experiments/_s99_audit/ab_test1_audit.py   # tabla recall/ratio/FN por perfil
```

**Veredicto acumulado de candidatos (todos los flags OFF en operacional):**
| Candidato | flag | resultado | estado |
|---|---|---|---|
| A pixfilter | enable_test1_pixel_filter | recall 59→22, **41 FN** | VETADO (S99) |
| B core/espacial | `enable_test1_spatial_core` | 18.9→**2.46×**, recall 59/59, **0 FN** | ✓ GANADOR validado |
| eq16 lava lake | enable_test1_lava_lake_eq16 | drift + anula sub-píxel | beyond-MIROVA (EXT-11) |
| C ctx puro | enable_test1_contextual_filter | mejor ratio **1.22×** pero **31 FN** | VETADO (cráter embebido) |
| **C+keep-peak** | ctx_filter + `enable_test1_contextual_keep_peak` | **← decide el run 26903265998** | PENDIENTE tabla |

**Decisión S100**: si ctxpeak da ratio < 2.46× con **0 FN** y recall = baseline →
adoptar ctxpeak (flagging fiel MIROVA + recall garantizado). Si NO mejora a core o
reaparece FN → adoptar **Cand B (core)**. Cualquiera: gate ya cerrado (MISSION 3-preg:
es divergencia documentada justificada — literal probado crea FN), falta solo:
1. Flip flag(s) en `pipeline/profiles/mirova_equivalent.yaml` — **A45: tag
   `pre-s100-test1-magnitude-adopt` + OK explícito Nicolás**.
2. Reproc operacional VIIRS de los Tier A (local Windows OK, secuencial A47) o GH.
3. Verificación 3 vistas (preview real, S92 L5) + R8 público.
4. Documentar en `docs/MIROVA_DIVERGENCES.md` la divergencia (literal contextual crea
   31 FN por cráter embebido; proxy compacto/keep-peak cura sin FN).

## §2 — Frente MODIS campo difuso (SCOPEADO, no resuelto)
`experiments/_s99_audit/modis_diffuse/scope.md`. **Distinto del de VIIRS**: es path D
(dNTI contextual) sobre escena tibia, NO Test1. 15 records >50 MW en Tier A (PCC 342,
Tupun 133, Chaitén 94); MIROVA-MODIS ≈ 0; **cat d artefacto** (campo disperso mediana
16 km del cráter, no foco). Escapa el cap `PATH_D_ONLY_CAP_MW` (gateado t_bg<270K cirrus;
estos son escena tibia t_bg~274K) y el filtro display campo-difuso (pide t_max<5°C ∧
npix≥100 ∧ vrp/px<1; estos fallan las 3). **Tercer régimen no cubierto.**
Opciones (ninguna implementada): (a) display — discriminante ESPACIAL (dispersión, A61)
para régimen tibio, bajo riesgo; (c) co-validación solo-MODIS (S93 F3); (b) recorte
compacidad path-D MODIS (raíz, riesgo A55 + reproc GH/Linux obligatorio, pyhdf roto local).
**Encarar como frente propio con brainstorming + A45 después de §1.**

## §3 — Pendientes menores (auditoría dormidos, registro docs/S99_DORMANT_FINDINGS_AUDIT.md)
- **DF-3/NEW-7 reclasificar**: verificación verbatim S99 mostró que "Drift #1a"
  (`enable_test1_k1_retire`) es un MALENTENDIDO — SP426.5 L298-300 "discarded for
  further steps" = sacar del pool estadístico, NO del reporte (los píxeles Test1 SÍ se
  reportan). Nuestro código actual (flag OFF) ya es fiel. **Pendiente: reclasificar en
  `docs/MIROVA_DIVERGENCES.md` F1.2/NEW-7 como "lectura equivocada, resuelto S99"** (Nicolás
  ya leyó el texto y concordó el sentido).
- DF-2 (integrated Eq.1) → beyond-MIROVA (EXT-11, junto a eq16).
- GitHub **issue #1** (NRT alert) — causa muerta desde S35/H7, cerrar.
- ~70 ramas stale → poda (`clean_gone`).
- D9 raíz, phase2: ver registro (probablemente cierran con el fix §1).

## Reglas/guías nuevas S99 (consultar)
- **MISSION.md regla verbatim**: "SÍ está en papers" exige cita de que el SISTEMA NRT
  *aplica* X (verbo activo), no que un paper lo *mencione*. Design docs NO son
  autoritativos sobre MIROVA sin cotejo primario. **Hecho canónico: MIROVA = 1 algoritmo
  por SENSOR, uniforme entre volcanes** (no per-volcán/régimen). Atrapó 2 malentendidos
  en S99 (eq16 lava lake, NEW-7).
- Antes de construir un "fix raíz", **chequear la historia** (HYPOTHESIS_LOG / A##):
  fondo-local kernel-bg ya estaba REFUTADO para Tupun (S62/A19) — casi se reconstruye.

## Tags defensivos S99
pre-s99-test1-spatial-core, pre-s99-eq16-wire, pre-s99-test1-contextual.

## Worktree canónico
Raíz `VRP Chile/` en main al día (igual que S98/S99).
