# BLOQUE ARRANQUE S106

**Sesión S105 (2026-06-09/10)** — MUY larga y productiva. 9 PRs (#384-392). Registro:
`project_s105_estado` (memoria) + `docs/AUDIT_S105.md` (auditoría integral A51) +
`docs/MIROVA_DIVERGENCES.md` D11 (divergencia formal nueva).

## §0 — Primer comando
```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
git fetch origin --prune && git pull --ff-only
cat docs/AUDIT_S105.md            # marco actual del proyecto
# estado de los A/B en vuelo:
gh run view 27275241269 --json status,conclusion   # fondo-local k=3.0 (10 jobs)
gh run view 27276651420 --json status,conclusion   # barrido k=2.0/2.5 (20 jobs)
```

## ✅ Cerrado en S105
- **A/B V2 (Test1-NTI-anillo): NO promover** — corrige ~50m de ~1000-1500m; k_sigma y
  anclas de brillo refutados offline; controles Lascar/Lastarria sin cambio (inocuo).
- **Discriminante núcleo-anillo**: separa lava/topo sin error en Villarrica pero NO
  generaliza como gate (Tupun = cat-b real casi continuo, confirmado Nicolás; Llaima
  lava débil no destaca). Fue la pista hacia el fondo local.
- **Llaima aclarado**: offset = lago Conguillío al N (71% de 478 dets), vent nominal OK.
  NO es Pichi-Llaima (fumarolas al S, sub-umbral, beyond-MIROVA futuro).
- **⭐ Fondo LOCAL sobre NTI implementado** (PR #386, flag `enable_test1_local_bg_nti`
  OFF, A45 completo: tag pre-s105-test1-local-bg-nti + TDD 6 tests + suite 695 + OK
  Nicolás). Diseño: `docs/superpowers/specs/2026-06-10-test1-local-bg-nti-design.md`
  (§12 predicciones PRE-REGISTRADAS, §13 límite de escala — riesgo Lastarria a la baja).
- **Fase 3 MODIS re-dimensionada**: el "campo difuso universal" era artefacto de un
  subagente con campos corruptos (A48). Real: residuo path D = 131/3072 (4.3%), 0%
  MIROVA, artefacto de magnitud CERCA del cráter. Frente SECUNDARIO. Design 2026-06-05 §11.
- **AUDIT_S105 (A51) + consolidación P1**: 6 contradicciones cerradas (MISSION pregunta 2
  viva, D11 formal, CLAUDE.md Estado→puntero, README reescrito, docs/INDEX.md maestro,
  checklist refs, M9=500, MEMORY rotado 573→~170).

## §1 — PRIORIDAD S106: analizar el A/B del fondo-local (decisión central)
**Los 3 brazos + baselines:**
| brazo | dónde |
|---|---|
| MIR-anillo (baseline) | `experiments/_s104_roi_probe/baseline_mir/` (en disco) |
| NTI-anillo (V2) | `experiments/_s104_roi_probe/nti_integral/` (en disco) |
| NTI-local k=3.0 | run 27275241269 → artifacts `s105local-<vol>-<chunk>` |
| NTI-local k=2.0/2.5 | run 27276651420 → artifacts `s105sweep-_test1_nti_local_ks{20,25}-<vol>-<chunk>` |

**Procedimiento** (todo pre-escrito):
1. Descargar artifacts → `merge_chunks.py <staging> <out>` (2 chunks por vol).
2. `python experiments/_s104_roi_probe/audit_local_sweep.py MIR-anillo:baseline_mir \
   NTI-anillo:nti_integral local-k3.0:<dir> local-k2.0:<dir> local-k2.5:<dir>`
3. **Contrastar contra las predicciones PRE-REGISTRADAS** (design 2026-06-10 §12, A66 —
   NO racionalizar post-hoc): nevados offN→0 + recall preservado; Lascar sin cambio;
   Lastarria offset fumarólico CONSERVADO (§13); Tupun trig_t1 no se desploma; Llaima
   05-15 = riesgo FN conocido.
4. Decisión pre-comprometida (§12): éxito uniforme → promover (A45: OK Nicolás + reproc
   11 + R2/R3/R8 + MIROVA_DIVERGENCES D11 cierre). Lastarria pierde → límite del método,
   NO promover. Llaima FN → elegir k del barrido. Tupun se desploma → refuta hipótesis.

## §2 — Después (orden)
1. **Deuda P2 jugosa**: bug `final_hotspot` rama eruption (píxel suelto scene-wide, los
   3 sensores: process_modis.py:1033 / process_viirs.py:1428 / process_viirs_mod.py:978)
   — ACOPLADO al gate frontend (distance_class corrupto hoy oculta por accidente los
   MODIS inflados; arreglar pipeline sin frontend los destapa). Diseñar JUNTOS.
   Scope previo: design 2026-06-05 §5.1 + AUDIT_S105 eje 6.
2. Portar ctxpeak a VIIRS750 (pendiente S102§2, cura dispersión glaciar V750).
3. Purga de flags refutados (V1, pixel_filter, eq16, spatial_core, nti_relative; V2/local
   según resultado §1) — decisión por flag: borrar rama o documentar.
4. Paper: draft S72 + case study V1→V2→fondo-local con predicciones pre-registradas.

## §3 — Decisiones de Nicolás PENDIENTES (registradas, no urgentes)
- Gates intra-radio S84/85: "decidir con más datos" al cerrar el frente fondo-local
  (anotado en MIROVA_DIVERGENCES).
- Limpieza pesada POSPUESTA: ~750MB data A/B stale + ~85 branches squash-merged +
  15 workflows one-off (S101-S104 archivables ya; S105 tras cerrar el A/B). Inventario
  en AUDIT_S105 eje 4/5.
- 7 docs "REVISAR" de docs/INDEX.md.
- 🔐 .netrc local Earthdata inválido (Nicolás; Actions OK, A71).

## Prompt copy-paste S106
```
Sesión S106 — VRP Chile. Sincronizá (raíz en main: git fetch origin --prune && git pull
--ff-only) y leé tasks/BLOQUE_ARRANQUE_S106.md + project_s105_estado (memoria) +
docs/AUDIT_S105.md.
S105 cerró V2 (no promover), implementó el FONDO LOCAL sobre NTI (PR #386, flag OFF,
uniforme, Coppola 2024 Eq.13) y dejó el A/B corriendo: run 27275241269 (k=3.0) +
27276651420 (barrido k=2.0/2.5). También: AUDIT_S105 integral + consolidación P1 +
divergencia formal D11.
PRIORIDAD §1: analizar el A/B contra las predicciones PRE-REGISTRADAS (design
2026-06-10 §12 — no racionalizar post-hoc). Baselines en disco
(experiments/_s104_roi_probe/{baseline_mir,nti_integral}), audit pre-escrito
(audit_local_sweep.py), merge_chunks.py para los artifacts. Criterios duros: 0 FN +
nevados offN→0 + Lastarria conservado + Tupun trig_t1 vivo. Si cumple → promoción A45
(tag ya existe: pre-s105-test1-local-bg-nti; falta OK Nicolás + reproc 11 + R2/R3/R8).
RECORDÁ: A45, A48 (verificar campos pc.* no final_hotspot_* corrupto), A66 (criterio
pre-registrado), A70 (mediana direccional), explicame como geólogo. 🔐 .netrc local
Earthdata inválido (usar Actions).
```
