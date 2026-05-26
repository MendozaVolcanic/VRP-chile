# Branches cleanup S80

> Auditoría S80: 36 branches `claude/*` en `origin`. 24 mergeadas + 12 con
> commits únicos.
>
> No se ejecuta delete destructivo en esta sesión. Comandos preparados
> para que Nicolás revise y apruebe.

## Categoría 1 — Mergeadas, sin commits únicos vs main (DELETE seguro)

24 branches cuyo commit HEAD ya está reflejado en `origin/main`. Son
remanentes de PRs cerrados que GitHub no auto-eliminó:

```
origin/claude/funny-mendeleev-99b1f4
origin/claude/s73-bloque-s74-update
origin/claude/s73-csv-path-dehardcode
origin/claude/s73-f28-saturation-guard
origin/claude/s73-f28-workflow-hotfix
origin/claude/s73-lit-search-update
origin/claude/s74-aveni-extract
origin/claude/s74-aveni-vrptir-plan
origin/claude/s74-claudemd-a40-a42
origin/claude/s74-claudemd-a43-yaml-norway
origin/claude/s74-f28-v3-token
origin/claude/s74-f28-workflow-rename
origin/claude/s74-frontend-bug8
origin/claude/s74-frontend-bugs-plan
origin/claude/s74-frontend-quick-wins
origin/claude/s74-vrptir-formula
origin/claude/s74-vrptir-pdf-verified
origin/claude/s75-aguilera-2021-peteroa-extract
origin/claude/s75-aveni-tirvolch-verify
origin/claude/s75-cierre-bloque-s76
origin/claude/s75-frontend-bug11b
origin/claude/s75-frontend-bug11b-v2
origin/claude/s75-vrptir-profile-flag
origin/claude/s75-vrptir-profile-flag-v2
```

**Comando de cleanup** (lote único, después de revisar):
```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP-Chile-s80-consolidation"
# Verificación final pre-delete
for b in funny-mendeleev-99b1f4 s73-bloque-s74-update s73-csv-path-dehardcode \
         s73-f28-saturation-guard s73-f28-workflow-hotfix s73-lit-search-update \
         s74-aveni-extract s74-aveni-vrptir-plan s74-claudemd-a40-a42 \
         s74-claudemd-a43-yaml-norway s74-f28-v3-token s74-f28-workflow-rename \
         s74-frontend-bug8 s74-frontend-bugs-plan s74-frontend-quick-wins \
         s74-vrptir-formula s74-vrptir-pdf-verified s75-aguilera-2021-peteroa-extract \
         s75-aveni-tirvolch-verify s75-cierre-bloque-s76 s75-frontend-bug11b \
         s75-frontend-bug11b-v2 s75-vrptir-profile-flag s75-vrptir-profile-flag-v2
do
    count=$(git log --oneline "origin/claude/$b" --not origin/main | wc -l)
    if [ "$count" = "0" ]; then
        git push origin --delete "claude/$b"
    else
        echo "ABORT $b: tiene $count commits únicos, no borrar"
    fi
done
```

## Categoría 2 — Con commits únicos, ACTIVAS (NO TOCAR)

| branch | commits únicos | razón |
|---|---|---|
| `claude/s79-f66-hybrid-bg-gate` | 10 | **Activa S80**: F66 Tasks 0-6 done, Tasks 7-15 pending |
| `claude/s80-bloque-arranque` | 1 | Cleanup post-merge S79 |
| `claude/s79-experiments-s76-backlog` | 1 | Mergeada PR #218, commit huérfano probablemente HEAD desincronizado |
| `claude/s79-workflows-cleanup` | 1 | Mergeada PR #217, idem |

## Categoría 3 — Con commits únicos, candidatos a investigar

| branch | commits únicos | hipótesis |
|---|---|---|
| `claude/nostalgic-aryabhata-e05d1e` | **40** | Branch de subagente claude largo trabajo, no mergeado. Investigar contenido antes de borrar |
| `claude/sweet-austin-b5413b` | 16 | Branch del worktree main-tracking, no es trabajo distinto |
| `claude/hardcore-gauss-68c3db` | 1 | research-workflow-refactor activo? |
| `claude/research-workflow-refactor` | 1 | research-workflow-refactor activo? |
| `claude/s73-lit-search-s73` | 1 | versión inicial de #136/#137 ya mergeados |
| `claude/s74-f28-v3` | 1 | versión sin token de #138 mergeada |
| `claude/s74-frontend-bug9` | 1 | mergeado vía commit directo según git activity report |
| `claude/s75-f31-tirvolch-detector` | 1 | mergeada vía PR #153 |

**Recomendación**: investigar `claude/nostalgic-aryabhata-e05d1e` antes de
cualquier acción (40 commits sin merge es trabajo que vale la pena rescatar
o documentar como descartado).

```bash
git log --oneline origin/claude/nostalgic-aryabhata-e05d1e --not origin/main | head -20
```

## Worktrees locales

Estado actual:
```
VRP Chile/                    branch s15-dev (legacy)
VRP-Chile-s70/                branch work-s78-bloque-arranque-s79 (huérfano, NO sync con remote)
VRP-Chile-s79-f66/            branch claude/s79-f66-hybrid-bg-gate (activo)
VRP-Chile-s80-consolidation/  branch claude/s80-consolidation (este)
VRP-Chile-s74-frontend-plan/  branch claude/s74-frontend-bugs-plan (mergeada — eliminable)
.claude/worktrees/sweet-austin-b5413b/  branch main (canónico de Claude)
.claude/worktrees/funny-mendeleev-99b1f4/  branch claude/... (mergeada — eliminable)
.claude/worktrees/hardcore-gauss-68c3db/   branch claude/... (investigar)
.claude/worktrees/nostalgic-aryabhata-e05d1e/  branch claude/... (investigar 40 commits)
```

**Cleanup propuesto** (manual, Nicolás aprueba):
```bash
# Eliminar worktrees obsoletos (sus branches huérfanos siguen accesibles si vuelven a hacer falta)
git worktree remove "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP-Chile-s74-frontend-plan"
git worktree remove --force "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP-Chile-s70"
git worktree prune
```

**NO TOCAR**: `VRP-Chile-s79-f66/`, `VRP-Chile-s80-consolidation/`, `.claude/worktrees/sweet-austin-b5413b/`.

## Política branches a futuro (META M11 candidate)

Para evitar acumulación de branches:
1. **Branch protection** GitHub: auto-delete head branches al mergear PR (`Settings → General → Pull Requests → Automatically delete head branches`)
2. **Naming**: prefijo `claude/sNN-<feature>` (ya se usa). Versión v2/v3 reusa la misma branch con `--force-with-lease` cuando sea retry de CI.
3. **Cleanup mensual** integrado a SESSION_CLOSE_CHECKLIST.
