# Bloque arranque S83 — prompt copy-paste para Nicolás

**Generado al cierre S82 (2026-05-26)** según feedback durable
`memory/feedback_session_close_handoff_prompt.md`.

---

## ✅ Hecho en S82 (2026-05-26)

- **PRs S81 mergeados**: PR #221 (VRP_TIR gate provisional + PCC mirova_center)
  + PR #222 (rescate docs S82-prep) mergeados vía `gh api ... /merge` (A39
  workaround porque `main` estaba checked-out en worktree raíz).
- **F-S81-A Fase 1 completa**: clasificación de los 857 FPs MODIS del audit
  S81 contra `data/mirova_equivalent/` enriquecidos con `final_hotspot_source`,
  `primary_cluster.*`, `diag_n_bt_path`, `diag_n_nti_path`,
  `diag_n_dnti_ctx_path`.
- **Hallazgo neto**: **99.5% de FPs MODIS son Path D (dNTI ctx 8-vecinos)
  puro**. 89% a >10 km del cráter. 53% a >20 km. 98% MIROVA tagged
  `RUTINA(vrp=0.0)` (decisión algorítmica, no falta de data). Distribución
  pareja entre 11 Tier A descarta hipótesis "incendio forestal puntual".
- **Decisión Fase 1.2 / 1.3 skipped justificado**: la distribución uniforme +
  MIROVA RUTINA 98% + magnitudes 100-1000 MW descartan hipótesis "incendio
  real" y "vegetación seca" sin necesidad de descargar MOD14/MOD13A2.
- **Design doc R5 Fase 2** escrito con 4 opciones consideradas, decisión
  preliminar **Opción A** (gate distancia per-volcán empírico desde percentil
  95 ALERTA_TERMICA MIROVA en `latest_consolidado.csv`).

## 📂 Outputs S82 (rama `claude/s81-vrp-tir-gate` → PR S82 pendiente)

| Archivo | Contenido |
|---|---|
| `docs/F_S81_A_FASE1_DIAGNOSIS.md` | Síntesis hallazgos Fase 1 (mecanismo Path D + far + cluster mixto) |
| `docs/superpowers/specs/2026-05-26-f_s81_a_gate_path_d_intra_radio.md` | R5 design doc Fase 2 con 4 opciones, decisión Opción A, pre-mortem, rollback |
| `experiments/_s82_intra_radio/fase1_1_clasificacion.py` | Script reproducible enriquecimiento + cross-tabs |
| `experiments/_s82_intra_radio/fase1_1_summary.md` | Cross-tabs y distribuciones (path, cluster, dist, vrp, MIROVA tag, volcán) |
| `experiments/_s82_intra_radio/fase1_1_modis_classified.csv` (gitignored) | 857 FPs MODIS enriquecidos. Regenerable con script. |

## 🎯 Pendiente confirmación Nicolás antes de implementar Fase 2

Fase 2 = implementar gate Path D MODIS restringido a `R_mirova_modis(volcan)`
(percentil 95 ALERTA_TERMICA del CSV scraper).

**Bloqueante**: tocar `pipeline/process_modis.py` requiere:
- A45 tag defensivo `pre-s8N-f-s81-a-gate-modis-path-d` antes del primer edit.
- A45 **confirmación explícita Nicolás** aunque tests estén verdes.

Plan Fase 2: 9 horas estimadas (script build_radius → test sintético → fix
process_modis → yaml patch → 2 profiles → workflow A/B → audit → adopción).
Detalle: `docs/superpowers/specs/2026-05-26-f_s81_a_gate_path_d_intra_radio.md`.

## Primer comando obligatorio S83

```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP-Chile-s80-consolidation"
git fetch origin --prune
git log --oneline HEAD..origin/main      # ¿algo nuevo?
git pull --ff-only                       # si la rama está atrás
gh pr list --state open                  # PR S82 abierto si existe
python -m pytest tests/ -q --tb=no | tail -3   # esperado: ~513 passed
```

## Copy-paste para Claude al inicio de S83

```
Inicio sesión S83 — VRP Chile. S82 cerró Fase 1 F-S81-A: diagnóstico
gate intra-radio MIROVA MODIS completo. Mecanismo identificado: 99.5%
FPs MODIS = Path D (dNTI ctx 8-vecinos) puro, 89% far, 98% MIROVA
RUTINA.

Worktree principal:
C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP-Chile-s80-consolidation/

Lectura obligatoria al inicio:
1. cat docs/F_S81_A_FASE1_DIAGNOSIS.md   # síntesis hallazgo S82
2. cat docs/superpowers/specs/2026-05-26-f_s81_a_gate_path_d_intra_radio.md
   # R5 design doc Fase 2 (Opción A recomendada)
3. cat docs/SESSION_INDEX_CONSOLIDATED_S80.md (sigue siendo ancla)
4. cat docs/META_RULES_S80.md

ESTADO POST-S82:
- F-S81-A Fase 1: COMPLETA. Mecanismo = Path D far + cluster mixto.
- F-S81-A Fase 2: DESIGN DOC LISTO, implementación bloqueada en
  confirmación Nicolás + tag defensivo A45.
- PR #221 (VRP_TIR provisional) MERGED main S82.
- PR #222 (rescate docs S82-prep) MERGED main S82.
- NRT operacional sano (post 2026-05-25).
- Worktree raíz VRP Chile/ apuntando a main (S82-prep).

TAREAS PRIORIZADAS S83:

P0:
1. F-S81-A Fase 2 implementación (9h estimadas) — bloqueado en
   confirmación Nicolás + tag defensivo A45 antes de tocar
   pipeline/process_modis.py. Plan completo en design doc.
   Pasos: script build_mirova_modis_radius.py → test sintético TDD →
   gate en process_modis.py → yaml patch → 2 profiles → workflow A/B →
   audit → decisión adopción.

2. F46 completo VRP_TIR (Coppola 2024 Eq.16) — 14-16h
   docs/F46_VRP_TIR_BUG_S76.md + docs/F46_VRP_TIR_GATE_S81.md.

P1:
3. F66 Tasks 7-15 (branch claude/s79-f66-hybrid-bg-gate, 8-12h).
4. Sesión data integrity dedicada (5-7h, tasks/backlog_data_integrity_session.md).
5. NdC recall 0% investigación (4h).

REGLAS VINCULANTES (durables):
- M2 persistencia in-vivo.
- A45 tag defensivo + confirmación Nicolás antes pipeline/process_*.py,
  store.py, mirova_equivalent.yaml.
- A47 NO paralelo data/mirova_equivalent/.
- A49 verificar git diff post-insert entre funciones (no comer return).
- A50 cross-source verify origin/main antes de etiquetar "pre-existing fail".
- A52 git fetch + pull en worktrees antes de asumir estado.
- M1 cap PRs/sesión soft 12 hard 20.

Comunicame como geólogo: fenómeno físico → mecanismo pipeline → fórmula al final.

¿Confirmás Fase 2 con Opción A (gate distancia per-volcán empírico)?
¿O preferís discutir Opción B (cluster ≥4 px) / D (A/B 3 opciones)?
```

---

## Hallazgos persistidos S82 (referencia rápida)

| Doc | Contenido |
|---|---|
| `docs/F_S81_A_FASE1_DIAGNOSIS.md` | Síntesis Fase 1 — mecanismo Path D far + cluster mixto + MIROVA RUTINA |
| `docs/superpowers/specs/2026-05-26-f_s81_a_gate_path_d_intra_radio.md` | R5 design doc — 4 opciones, decisión Opción A, pre-mortem, rollback |
| `experiments/_s82_intra_radio/fase1_1_summary.md` | Cross-tabs reproducibles |

## Tags defensivos S82

Ninguno creado en S82 (no se tocó pipeline). Próximos esperados S83:
`pre-s83-f-s81-a-gate-modis-path-d`.

## PRs S82

- PR #221 (VRP_TIR provisional) MERGED main S82 — heredado S81.
- PR #222 (rescate docs S82-prep) MERGED main S82 — heredado S81.
- PR S82-out (este bloque + Fase 1 outputs) — pendiente abrir.
