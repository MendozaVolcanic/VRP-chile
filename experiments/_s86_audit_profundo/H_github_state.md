# Subagente H — Estado GitHub `MendozaVolcanic/VRP-chile` (S86 auditoría profunda)

**Fecha**: 2026-05-28 18:40 UTC
**Veredicto**: 🟢 **REPO SALUDABLE**. NRT operacional verde, dashboard live, CSV sincronizado. Drifts detectados son cosméticos/housekeeping — ninguno compromete confiabilidad NRT.

---

## 1. NRT cron health (últimos 30 runs)

| Métrica | Valor |
|---|---|
| Success | 23 / 30 (79.3%) |
| Failure | 6 / 30 |
| In progress | 1 (corriendo ahora) |
| Última corrida exitosa | 2026-05-28 15:55Z |
| Frecuencia real | ~2.5-4.5h (cron declarado cada 2h — drift habitual GHA) |

**Burst de fallos único** (2026-05-24 15:03Z → 2026-05-25 08:20Z, 7 corridas consecutivas):
- **Root cause**: `NASA_AUTH_UNREACHABLE` (LANCE/Earthdata DNS timeout, budget ~2 min).
- **Recovery**: F51 + F55 fixes (PRs #190, #199, #225) + NASA volvió. Desde 2026-05-25 13:28Z corre verde.
- **Issue #1** se auto-generó (nrt-monitor.yml) durante el burst — sigue **OPEN aunque ya está resuelto operacionalmente**.

Como geólogo: el pipeline térmico es robusto. El "fail rate" del 21% es 100% atribuible a un outage upstream NASA puntual (no infraestructura propia). La cadena `nrt.yml` + `nrt-retry.yml` + `nrt-monitor.yml` + healthcheck funcionó como red de seguridad.

---

## 2. Workflows (8 activos en disco + 9 archivados en `_archive/`)

| Workflow | Rol | Última corrida | Salud |
|---|---|---|---|
| `nrt.yml` | NRT cron 2h matrix por volcán | in_progress | OK |
| `pages-deploy.yml` | Deploy dashboard | 2026-05-28 17:32Z ✓ | OK |
| `nrt-monitor.yml` | Alerta 3+ fails consecutivos | 2026-05-28 16:38Z ✓ | OK |
| `nrt-retry.yml` | Retry post NASA recovery | 2026-05-28 18:22Z ✓ | OK |
| `nrt-healthcheck.yml` | Detecta Tier A staleness | 2026-05-28 15:24Z ✓ | ⚠️ solo 1 run en 5 — chequear cron |
| `sync-mirova-csv.yml` | Sync CSV ground truth Mirova-v1 | 2026-05-28 19:44Z ✓ | OK |
| `reproc-f28-pp-saturation.yml` | S73-S74 F2.8 PP saturation A/B | obsoleto | 🟡 archivar |
| `reproc-ab-f-s81-a-intra-radio.yml` | S83 A/B (adoptado PR #226) | obsoleto | 🟡 archivar |
| `reproc-ab-f-s81-b-prime.yml` | S85 A/B (adoptado PR #229) | obsoleto | 🟡 archivar |

**A43 Norway YAML 1.1 check**: 2 workflows con `on:` sin quote → `nrt.yml`, `nrt-monitor.yml`. Riesgo HTTP 422 latente no-determinístico (en práctica nunca falló, schedule-triggered no usa dispatch). **Fix defensivo gratis: 5 min**.

---

## 3. Branches (72 remotas, 42 namespace `claude/*`)

- **safe-delete mergeadas a main**: ~30 (BRANCHES_CLEANUP_S80.md las identifica).
- **Stale sin PR cerrado >30 días**: ~10 (`claude/s7X-*` experimentales legacy + pre-namespace `s70-*`, `s71-*`, `s72-*`).
- **`origin/s15-dev`**: legado S33. S82-prep ya reapuntó el worktree raíz a `main` — descartable.

Plan completo de cleanup ya documentado en `docs/BRANCHES_CLEANUP_S80.md`. Pendiente ejecutar.

---

## 4. Pull Requests (últimos 50: #181-#230)

- **49/50 MERGED**, **1 OPEN** (#223).
- **PR #223 OPEN superseded**: "F-S81-A Fase 1 diagnóstico" → Fase 2 ya adoptada (#226). Acción: cerrar como superseded o mergear como docs.
- **0 PRs del bot Claude abandonados**: todos los PRs son `author=MendozaVolcanic`; Claude commitea pero los abre Nicolás.

**Top 5 mergeados recientes** (todos S85 cierre):
- #230 cierre Fase C investigada+descartada
- #229 adoptar F-S81-B' gate intra-radio
- #228 audit script F-S81-B' pre-escrito
- #227 preventivos NRT + Fase B'
- #226 adoptar F-S81-A gate Path D MODIS

---

## 5. Issues

- **1 OPEN**: #1 "NRT cron: 3+ corridas consecutivas fallaron" (`nrt-alert`, `priority-high`).
  Auto-generado por monitor durante burst NASA 24-25/05. **Ya resuelto operacionalmente** — el monitor no auto-cierra.
- **Labels canónicos observados**: `nrt-alert`, `priority-high`.
- No hay protocolo de cierre automático post-recovery → drift de inbox.

---

## 6. GitHub Pages dashboard

- ✅ Live, build_type `workflow`.
- ✅ Últimos 5 deploys exitosos (2-2.5 min cada uno), ~4/día post-cada NRT run.
- ✅ Último: 2026-05-28 17:32Z.
- ✅ `latest_consolidado.csv` actualizado (2026-05-28 13:57Z, 2.96 MB) — A17 satisfecho.
- ✅ `sync-mirova-csv.yml` cron corriendo limpio.

---

## 7. Worktrees locales (8)

| Worktree | Branch | Estado |
|---|---|---|
| `VRP Chile/` (raíz) | main `fb291e30` | ✅ OK post-S82-prep |
| `VRP-Chile-s80-consolidation/` | `claude/s81-vrp-tir-gate` | ✅ S81-S85 work |
| `VRP-Chile-s79-f66/` | `claude/s79-f66-hybrid-bg-gate` | ✅ F66 pending S82+ |
| `VRP-Chile-s70/` | `work-s78-bloque-arranque-s79` | ⚠️ A52 huérfano, no usar |
| `VRP-Chile-s74-frontend-plan/` | `claude/s74-frontend-bugs-plan` | 🟡 stale |
| `.claude/worktrees/nostalgic-aryabhata-e05d1e/` | `claude/nostalgic-aryabhata-e05d1e` | 🟡 Nicolás descarta S81 |
| `.claude/worktrees/funny-mendeleev-99b1f4/` | idem | 🟡 stale |
| `.claude/worktrees/hardcore-gauss-68c3db/` | `claude/research-workflow-refactor` | 🟡 stale |

---

## 8. Drifts TOP 5 detectados

| # | Drift | Severidad | Fix |
|---|---|---|---|
| 1 | Issue #1 NRT-alert OPEN ya resuelto operacionalmente | 🟢 BAJA | 2 min |
| 2 | PR #223 OPEN superseded por #226 (Fase 2 adoptada) | 🟢 BAJA | 3 min |
| 3 | 3 reproc workflows obsoletos sin archivar | 🟡 BAJA-MEDIA | 10 min |
| 4 | A43: nrt.yml + nrt-monitor.yml sin `"on":` quoted | 🟡 MEDIA latente | 5 min |
| 5 | 42 branches `claude/*` + 7 worktrees locales huérfanos | 🟢 BAJA cosmético | 30-45 min |

---

## 9. Acciones recomendadas (suma ~70 min, todas opcionales)

1. **[2 min, alta]** Cerrar issue #1 con referencia a PRs #190/#199/#225.
2. **[3 min, media]** Cerrar PR #223 como superseded.
3. **[5 min, media]** Defensivo A43 en `nrt.yml` + `nrt-monitor.yml` (`on:` → `"on":`).
4. **[10 min, baja]** Archivar 3 reproc workflows obsoletos a `_archive/` (patrón PR #217).
5. **[30 min, baja]** Ejecutar `docs/BRANCHES_CLEANUP_S80.md`.
6. **[15 min, baja]** Cleanup worktrees huérfanos (s70, sweet-austin filesystem, nostalgic-aryabhata).
7. **[5 min, media]** Verificar cron `nrt-healthcheck.yml` (1 corrida en 5 — posible cron mal seteado).

---

## 🔐 Seguridad

- ⚠️ **GitHub PAT en `settings.json` pendiente rotar** (CLAUDE.md global lo marca desde sesión anterior). No revisé el archivo en esta auditoría — recordatorio para cierre.
- No detecté tokens cleartext en archivos del repo durante el muestreo.

---

## Conclusión geológica

El sistema térmico VRP-Chile está **operacionalmente confiable**: NRT corre, recovery automático funciona, dashboard publica continuo, ground truth sincroniza. Los drifts son **acumulación de cruft de 117 PRs en S70-S85** (predicción de la regla M1 cap PRs/sesión). No hay nada urgente — todo housekeeping diferible.

**Paths relevantes**:
- `C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/experiments/_s86_audit_profundo/H_github_state.{md,json}`
- `C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/docs/BRANCHES_CLEANUP_S80.md`
- `C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/.github/workflows/`
