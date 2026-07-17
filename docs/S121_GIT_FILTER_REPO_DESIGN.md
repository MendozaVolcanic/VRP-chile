# Diseño — reducción del `.git` con git filter-repo (S121)

> **Estado: DISEÑO. NO ejecutado.** Operación destructiva (reescribe historia, force-push).
> Requiere decisión y ventana coordinada de Nicolás. Este doc es el plan para cuando se decida.

## Problema

`.git` = **3.0 GB** mientras el working tree tracked (post-poda S121 PRs #492/#493) es
~180 MB operacional. El exceso es **historia de blobs** que ya no están en HEAD:
1. **~68 dirs A/B de data/** que sacamos con `git rm` (PRs #492/#493) — sus blobs siguen
   en cada commit histórico donde existieron (~1.5 GB de los pesados).
2. **Historia del NRT**: `data/mirova_equivalent/*.json` se commitea cada 2h desde
   2026-04. ~5000 commits, cada uno reescribe JSONs de 13-17 MB → miles de versiones
   completas de archivos grandes en el pack. Este es el motor dominante del crecimiento
   (AUDIT_S121 §4: ~30 MB/día promedio histórico).

`git rm` (lo ya hecho) NO reduce esto — los objetos viven en el pack hasta que se
reescribe la historia. Solo `git filter-repo` (o BFG) los purga.

## Qué purgar (dos niveles, elegir alcance con Nicolás)

**Nivel A — conservador (purga solo los A/B ya removidos):** borrar de TODA la historia
los paths de los dirs A/B que ya sacamos. Ahorro estimado: ~1.3-1.5 GB del pack. Riesgo
bajo de arrepentimiento (ya decidimos que no van al repo; backup local + tag los preserva).

**Nivel B — agresivo (además colapsa la historia del NRT):** mantener solo la ÚLTIMA
versión de cada `data/mirova_equivalent/*.json` (o snapshots mensuales), descartando las
miles de versiones intermedias del cron. Ahorro estimado: podría llevar `.git` a <500 MB.
Costo: se pierde el `git blame`/historia fina de la data NRT (cuándo entró cada record) —
pero esa historia rara vez se consulta y la data viva está en HEAD. **Requiere decisión
explícita**: ¿vale la historia commit-a-commit de la data NRT?

Recomendación: **empezar por Nivel A** (bajo riesgo, ~1.4 GB), medir, y decidir Nivel B
después si `.git` sigue incómodo.

## Procedimiento (Nivel A)

Precondiciones: `pip install git-filter-repo`. Repo con todo pusheado y sin trabajo local
pendiente. **Ventana coordinada**: pausar el cron NRT durante la operación (deshabilitar
`nrt.yml` temporalmente o elegir hueco entre corridas).

```bash
# 0. BACKUP TOTAL antes de nada (además del backup local ya existente):
cd ..                       # fuera del repo
git clone --mirror "VRP Chile/.git" VRP-chile-BACKUP-pre-filter.git   # espejo completo
tar czf VRP-chile-BACKUP-pre-filter.tar.gz VRP-chile-BACKUP-pre-filter.git

# 1. En un clon FRESCO (filter-repo exige repo limpio; NO correr sobre el working dir vivo):
git clone "VRP Chile" ../vrp-filter-work
cd ../vrp-filter-work

# 2. Purgar los paths A/B de toda la historia (lista en scripts/filter_repo_paths_A.txt):
git filter-repo --invert-paths --paths-from-file scripts/filter_repo_paths_A.txt

# 3. Verificar: tamaño nuevo del pack, que HEAD:data/mirova_equivalent/ sigue intacto,
#    que la suite pasa (806), que el frontend carga.
git count-objects -vH
python -m pytest -q

# 4. Force-push (DESTRUCTIVO — reescribe origin/main y TODAS las ramas/tags):
git remote add origin https://github.com/MendozaVolcanic/VRP-chile.git
git push --force --all
git push --force --tags
```

## Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Reescribe TODOS los SHAs → tags/commits viejos quedan colgados | Backup mirror (paso 0); los tags viejos (pre-sNN) se re-crean o se aceptan perdidos |
| Force-push rompe cualquier clon existente (tu PC, worktrees, Actions) | Re-clonar en todos lados post-operación; documentar en bloque de arranque |
| El cron NRT commitea durante la operación → conflicto | Pausar `nrt.yml` durante la ventana; re-habilitar después |
| PRs abiertos quedan invalidados | Mergear/cerrar todos los PRs antes |
| `.netrc`/credenciales para el force-push | Nicolás ejecuta el push (acción sensible; no la hago yo) |

## Lo que NO resuelve

El crecimiento FUTURO. Aunque purguemos, el NRT seguirá agregando ~30 MB/día. La solución
**sostenible** (AUDIT_S121 §4) es cambiar el modelo de "data commiteada a main para
siempre": repo satélite `VRP-chile-data`, o GitHub Releases con snapshots, o branch orphan
con squash periódico. **El filter-repo es limpieza puntual; la arquitectura de data es la
cura de fondo** — diseñar por separado.

## Recomendación final

1. Ejecutar Nivel A cuando Nicolás abra una ventana coordinada (bajo riesgo, ~1.4 GB).
2. NO Nivel B sin decisión explícita sobre la historia NRT.
3. En paralelo, diseñar la arquitectura de data sostenible (lo que evita repetir esto).
4. El force-push lo ejecuta Nicolás (acción destructiva sobre el remoto).
