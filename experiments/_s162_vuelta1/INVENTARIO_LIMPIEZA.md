# Inventario de worktrees, carpetas, PRs en borrador, sin seguimiento y stashes

Fecha: 2026-10-24. Solo lectura: no se borró, movió, hizo fetch ni stash de nada. `origin/main` local coincide con el remoto (e850152b5, comprobado con `gh api`). Disco medido con `df`: C: 33 GB libres (94 % usado), D: 8,6 GB libres (97 % usado).
Tabla completa en `C:\Users\nmend\AppData\Local\Temp\claude\C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile\a3efc9fd-8a35-470a-aad1-531abaec64d8\scratchpad\vuelta1\inventario\inventario.csv` (63 filas).

## Resumen

1. Los 14 worktrees están sin cambios en archivos versionados y con su rama en el remoto en el mismo commit, así que borrar los directorios no pierde commits. Lo que sí se perdería es lo no versionado: archivos ignorados por `.gitignore` o carpetas sin seguimiento, en 5 worktrees: s159-pruebas 118 MB ignorados + 28 MB sin seguimiento, gracious-merkle 6,6 MB, s158-audit-r2 2,8 MB, s158_d17 1,9 MB y s159-evaluador 5,5 KB.
2. BORRAR SEGURO: 9 worktrees (7 en C: = 7,5 GB, 2 en D: = 2,0 GB), la clonación `D:\vrp-trabajo\mirova-v1` (885 MB, PR #26 de Mirova-v1 sigue abierto) y 2 carpetas pytest temporales (18 MB). Para D: eso libera unos 2,9 GB (8,6 a unos 11,5 GB libres).
3. Cuidado con las ramas, no con los directorios: `s159-oraculo-censo` (110 archivos) y `s159-portes` (64) no tienen PR y sus archivos no están en main; solo viven en esas ramas remotas. Si se borran los directorios, no borrar esas ramas.
4. PREGUNTAR: 4 worktrees con datos ignorados (C: 3,7 GB, D: 1,1 GB) y 6,8 GB de salidas de sesiones S155 a S160 en `D:\vrp-trabajo\temporales\` (la mayor, `s160_audit`, 2,0 GB, la citan 22 archivos de main). De los 10 PR en borrador, #888 está superado por contenido (se puede cerrar) y #889 está en conflicto con main; #776 y #880 quedan sin poder decidirse.
5. CONSERVAR: worktree `s159-evaluador` (en uso hoy, D25 espera a Nicolás) y los PR #886, #887, #889, #890, #898, #900, #901.

## 1. Worktrees (14 más el principal `loop/activo`)

Qué se comprobó en cada uno: `git status --porcelain` (cambios en archivos versionados y sin seguimiento), `status --ignored` (archivos no versionados), `rev-parse @{u}` y `log @{u}..HEAD` (commits sin subir), `ls-remote` (la rama remota existe y tiene el mismo SHA), PR por rama con `gh pr list --state all --head`, y contenido por blob: para cada archivo que la rama cambió respecto de su merge-base con `origin/main`, si el blob es idéntico en `origin/main`. No se usó `git cherry`. Los que dicen "ancestro" son ramas que `git merge-base --is-ancestor` confirma contenidas en main. Los tamaños son `du -sh`. Ninguno tiene commits sin subir (los 14 tienen rama remota con SHA igual al local).

| Worktree | Disco | Tam. | Rama / commit | Sin commitear | PR | Contenido en main | No versionado | Recomendación |
|---|---|---|---|---|---|---|---|---|
| `.claude\worktrees\cool-chaum-e3be8d` | C | 1,1 G | s161-cese-snpp-nrt / bcc654ab8 | 0 | #897 MERGED | 10 de 10 idénticos | .claude/ 8 KB | BORRAR SEGURO |
| `.claude\worktrees\fix-sync-sin-rebase-4b2c2f` | C | 1009 M | s160-sync-mirova-sin-rebase / 494880ced | 0 | #895 MERGED | 2 idénticos, 2 editados después | .claude/ 8 KB | BORRAR SEGURO |
| `.claude\worktrees\frosty-lamport-3fef52` | C | 1,1 G | claude/frosty-lamport-3fef52 / 92b632138 | 0 | #901 borrador | 0 de 30 (solo en rama remota) | .claude/, pycache | BORRAR SEGURO (solo el directorio) |
| `.claude\worktrees\gracious-merkle-6447d8` | C | 1,1 G | claude/gracious-merkle-6447d8 / 7ae738900 | 0 | #898 borrador | 0 de 25 (solo en rama remota) | 16 archivos ignorados, 6,6 MB | PREGUNTAR |
| `.claude\worktrees\nice-ishizaka-62d0a8` | C | 1,1 G | s161-auto-audit-cese-snpp / a7d1c0b91 | 0 | #900 borrador | 3 distintos, 2 ausentes | .claude/ | BORRAR SEGURO (solo el directorio) |
| `.claude\worktrees\s158-audit-r2-0eeee2` | C | 1,1 G | claude/s158-audit-r2-0eeee2 / 7a8f9fe61 | 0 | #888 borrador | 261 de 264 idénticos | 6 CSV ignorados, 2,8 MB | PREGUNTAR |
| `C:\vrp-trabajo\s159-evaluador` | C | 1014 M | s159-evaluador-d25 / e634f819f | 0 | #890 borrador | 0 de 366 | 2 CSV, 5,5 KB | CONSERVAR (en uso hoy) |
| `C:\vrp-trabajo\s159-instrumentos` | C | 1009 M | s159-cese-snpp / f995d7101 | 0 | #892 MERGED | 14 de 15 idénticos | pytest_cache | BORRAR SEGURO |
| `C:\vrp-trabajo\s159-m` | C | 1,1 G | s159-oraculo-censo / 812624cc6 | 0 | ninguno | 0 de 110 | ninguno | BORRAR SEGURO (solo el directorio; rama remota única, no borrar) |
| `C:\vrp-trabajo\s159-n` | C | 1,1 G | s159-portes / ca034d66e | 0 | ninguno | 0 de 64 | pycache | BORRAR SEGURO (solo el directorio; rama remota única) |
| `C:\vrp-trabajo\s159-pruebas` | C | 1,5 G | s160-auditoria / b042607c2 | 1 carpeta sin seguimiento (28 MB) | #893 MERGED (ancestro) | rama contenida en main | 1.792 archivos ignorados, 118 MB, más 28 MB sin seguimiento | PREGUNTAR |
| `D:\vrp-trabajo\temporales\s158_d17` | D | 1,1 G | s158-d17-diseno / e81bfadd5 | 0 | #885 MERGED (ancestro) | rama contenida en main | 8 CSV ignorados, 1,9 MB | PREGUNTAR |
| `D:\vrp-trabajo\temporales\s158_tupun` | D | 1009 M | s158-tupungatito / 55598b847 | 0 | #886 borrador | 0 de 41 (solo en rama remota) | pycache | BORRAR SEGURO (solo el directorio) |
| `D:\vrp-trabajo\temporales\s158_v750` | D | 1009 M | s158-v750-recall / c18d3b141 | 0 | #887 borrador | 0 de 29 (solo en rama remota) | ninguno | BORRAR SEGURO (solo el directorio) |

Notas que importan:

- "Solo el directorio" quiere decir que `git worktree remove` no pierde commits porque la rama remota tiene el mismo SHA. Borrar la rama remota o cerrar el PR es otra decisión y en esos casos sí se perdería trabajo no integrado.
- `s159-pruebas` (rama s160-auditoria) está mergeada, pero sus 118 MB de ignorados (caché CMR, descargas, PNG, salidas) y 28 MB sin seguimiento no están en ningún remoto. Por el nombre (`_cache`, `descargas`) son regenerables; no lo probé.
- El worktree `s159-m` tiene `origin/s159-pruebas` como upstream, y `s159-n` también, pero ambas ramas existen en el remoto con su propio nombre y el mismo SHA que el local (`ls-remote`). `s159-portes` es ancestro de `s159-oraculo-censo`: su contenido está dentro de la otra rama.
- El nombre de la carpeta `C:\vrp-trabajo\s159-instrumentos` engaña: tiene la rama `s159-cese-snpp` (PR #892, mergeado). La rama `s159-instrumentos` del PR #889 no tiene worktree.
- `s158-audit-r2-0eeee2` no tiene upstream configurado localmente, pero la rama remota existe con el mismo SHA.
- Ningún worktree está bloqueado (`git worktree list` no muestra `locked`).
- El repo principal (`loop/activo`) está al día con su remoto (0 commits sin subir). Tiene además `.venv` de 308 MB (`du -sh`), fuera del alcance pedido.

### Espacio que liberaría la sección 1 (suma de las cifras `du -sh`, redondeadas)

| Recomendación | C: | D: |
|---|---|---|
| BORRAR SEGURO | 7,5 GB (7 worktrees) | 2,0 GB (2 worktrees) |
| PREGUNTAR | 3,7 GB (3 worktrees) | 1,1 GB (1 worktree) |
| CONSERVAR | 1,0 GB (1 worktree) | 0 |

## 2. Carpetas grandes que no son worktrees

`D:\vrp-trabajo\temporales\` pesa 9,4 GB en total (`du -sh`); 3,1 GB son los 3 worktrees de arriba y el resto son las carpetas de esta tabla. Ninguna es repo git (sin `.git`), salvo `mirova-v1`. La sesión sale del nombre y la fecha de modificación. Que "no esté citada en origin/main" se midió con `git grep -F "temporales/<nombre>"` y no descarta citas con otra forma de ruta.

| Carpeta | Tam. (MB) | Sesión (por nombre) | Qué es / citada | Recomendación |
|---|---|---|---|---|
| `temporales\s160_audit` | 1996 | S160 | Salidas de la auditoría S160 (f1b 861, f1a 419, v4 295, main 204). 22 archivos de origin/main la citan | PREGUNTAR |
| `temporales\s157_pcc865` | 631 | S157 | verif 315, c0_union 185, k_union 130; no citada | PREGUNTAR |
| `temporales\s156_sombra` | 615 | S156 | verificadores de la sombra; no citada | PREGUNTAR |
| `temporales\verif_d29` | 575 | S160 | verificación de D29; no citada | PREGUNTAR |
| `temporales\s160_probar_d29` | 527 | S160 | pruebas de D29; no citada | PREGUNTAR |
| `temporales\s156_audit` | 516 | S156 | auditoría; no citada | PREGUNTAR |
| `temporales\verif_eval` | 336 | S157 | verificadores del evaluador; no citada | PREGUNTAR |
| `temporales\s157_chillan` | 303 | S157 | descargas de runs de GitHub y salidas; no citada | PREGUNTAR |
| `temporales\s159_n` | 206 | S159 | descargas de 4 runs + data_main; no citada | PREGUNTAR |
| `temporales\verif_s157` | 126 | S157 | scripts y salidas; no citada | PREGUNTAR |
| `temporales\s157d25` | 120 | S157 | material del pre-registro D25; no citada | PREGUNTAR |
| `temporales\tmp_s160` | 97 | S160 | temporales y respaldos .bak; no citada | PREGUNTAR |
| `temporales\s159_gemelo` | 69 | S159 | corridas del gemelo de D25; 7 archivos de main la mencionan (resumen commiteado) | PREGUNTAR |
| `temporales\frente_3` | 64 | S155 | audit_hoy y 2 carpetas c_*; no citada | PREGUNTAR |
| `temporales\s157-lambda` | 54 | S157 | profile.bak y PNG | PREGUNTAR |
| `temporales\s157_cenit` | 42 | S157 | scripts y salidas | PREGUNTAR |
| `temporales\s157_propagar_k` | 35 | S157 | scripts y README | PREGUNTAR |
| `temporales\s159_portes` | 35 | S159 | descargas de runs de humo | PREGUNTAR |
| `temporales\s157_busqueda` | 31 | S157 | logs | PREGUNTAR |
| `temporales\s157_sintomas` | 21 | S157 | loop.md, pytest-of-nmend | PREGUNTAR |
| `temporales\s159_oraculo` | 19 | S159 | descargas de los runs 39713438252 y 39715348772; artefactos vencen desde 2026-11-21 | PREGUNTAR |
| `temporales\s157_magnitud` | 19 | S157 | PNG y logs | PREGUNTAR |
| `temporales\pytest_tmp` | 18 | S155 | temporal de pytest | BORRAR SEGURO |
| `temporales\s159_biblio` | 12 | S159 | PDF de papers externos | PREGUNTAR |
| `temporales\frente_5` | 8 | S155 | copias del CSV de MIROVA del 19-oct | PREGUNTAR |
| `temporales\pytest-of-nmend` | 1 | S157 | temporal de pytest | BORRAR SEGURO |
| `temporales` (resto de archivos y carpetas sueltas) | ~7 (aprox.) | S155 a S159 | 30 ítems de menos de 2 MB cada uno | PREGUNTAR |
| `D:\vrp-trabajo\mirova-v1` | 885 | S160/S161 | Clon de Mirova-v1, rama fix/referencia-estable, limpio, 0 sin subir, 0 stashes; PR #26 de Mirova-v1 abierto | BORRAR SEGURO (se reclona si se necesita) |
| `D:\vrp-trabajo\mirova-v1-auditoria` | 177 | S160 | auditoría de Mirova-v1 (frente4_operacion 123 MB); un test de main la menciona | PREGUNTAR |
| `D:\vrp-trabajo\tmp` | 110 | S155 a S157 | verif_bytes 55, pytest-of-nmend 28, pt_full 21, mut.log; no revisé archivo por archivo | PREGUNTAR |
| `D:\vrp-trabajo\carrera_s160` | 55 | S160 | carpetas A, B, C, final.csv, logs; no citada | PREGUNTAR |
| `C:\vrp-trabajo\tmp_s161` | 0,14 | S161 | bt_p2s159, mut_final, verdes | PREGUNTAR |
| `D:\vrp-trabajo\worktrees` | 0 | | carpeta vacía (4 KB) | trivial |

Por qué casi todo es PREGUNTAR: son salidas de verificadores, mutaciones y descargas de runs que no están en ningún remoto. Los resúmenes y scripts de esas sesiones sí están commiteados (los PR mergeados #893, #885 y los borradores), pero no puedo comprobar que las salidas se regeneren sin costo. Los artefactos de GitHub Actions de S159 que medí (runs 39713438252 y 39715348772, 31 artefactos, 0 vencidos) duran hasta 2026-11-21; para los runs de S157 (`s157_chillan`) y los 4 runs de `s159_n` no consulté la fecha: SIN DATO.

### Espacio que liberaría la sección 2 (suma de las tablas, aprox.)

| Recomendación | C: | D: |
|---|---|---|
| BORRAR SEGURO | 0 | 0,9 GB (mirova-v1 885 MB + 2 pytest 18 MB) |
| PREGUNTAR | 0,14 MB | 6,8 GB |

## 3. PRs en borrador (10 abiertos con isDraft; #885 ya está MERGED aunque fue borrador)

`gh pr list --state open --draft` devuelve 10: #776, #880, #886, #887, #888, #889, #890, #898, #900, #901. `mergeable` según `gh pr view`.

| PR | Rama | Creado | Worktree local | Estado | ¿Superado? | Recomendación |
|---|---|---|---|---|---|---|
| #776 | s150-sonda-tres-campos | 2026-10-09 (act. 10-20) | ninguno | MERGEABLE/CLEAN, 20 archivos que main no tiene | `tasks/LOOP_OBJETIVOS.md:158` la lista como tarea 1.2 pendiente. Si K (S153) la dejó obsoleta: SIN DATO | PREGUNTAR |
| #880 | s157-saturacion | 2026-10-20 | ninguno | MERGEABLE/CLEAN, 16 archivos no están en main | No. Resultado "no alcanza para decidir"; la cita `docs/DISENO_D17_REMUESTREO_UTM.md` (caso P0-4) | PREGUNTAR |
| #886 | s158-tupungatito | 2026-10-21 | `D:\...\s158_tupun` | MERGEABLE/CLEAN, 41 archivos no están en main | No. #901 la refina, no la reemplaza | CONSERVAR |
| #887 | s158-v750-recall | 2026-10-21 | `D:\...\s158_v750` | MERGEABLE/CLEAN, 29 archivos no están en main | No. Alimenta lo que evalúa #890 | CONSERVAR |
| #888 | claude/s158-audit-r2-0eeee2 (base s158-d17-diseno) | 2026-10-21 | `.claude\worktrees\s158-audit-r2-0eeee2` | MERGEABLE/UNSTABLE | **Sí, por contenido**: su base ya entró con #885; 261 de 264 archivos son idénticos en main (los 3 distintos los editó main después) | BORRAR SEGURO (cerrar el PR; la rama remota queda) |
| #889 | s159-instrumentos | 2026-10-21 | ninguno | **CONFLICTING/DIRTY**, 17 archivos ausentes y 5 distintos en main | No integrado. Dice "no mergear sin el sí de Nicolás" (toca `pipeline/fetch.py`) | CONSERVAR |
| #890 | s159-evaluador-d25 | 2026-10-21 (act. 10-24) | `C:\vrp-trabajo\s159-evaluador` | MERGEABLE/CLEAN | Activo, D25 espera decisión | CONSERVAR |
| #898 | claude/gracious-merkle-6447d8 | 2026-10-23 | `.claude\worktrees\gracious-merkle-6447d8` | MERGEABLE/CLEAN | No; #901 depende de él | CONSERVAR |
| #900 | s161-auto-audit-cese-snpp | 2026-10-23 | `.claude\worktrees\nice-ishizaka-62d0a8` | MERGEABLE/CLEAN | No; el cese de Suomi NPP es el 2026-11-02 13:00 UTC | CONSERVAR |
| #901 | claude/frosty-lamport-3fef52 | 2026-10-23 | `.claude\worktrees\frosty-lamport-3fef52` | MERGEABLE/CLEAN | No | CONSERVAR |

Contexto: `docs/AUDIT_S160.md` (en origin/main, líneas 160 a 175) ya recomendaba el orden de merge #893, #888, #885, #886, #887, #880, `s159-pruebas`, `s159-portes`, y por último #889 y #890. #893 y #885 ya están mergeados. Dos ramas de ese orden, `s159-pruebas`/`s159-oraculo-censo` y `s159-portes`, siguen sin PR. Los merges los decide Nicolás (A39).

## 4. Carpetas sin seguimiento en la raíz del repo

| Carpeta | Tam. | Archivos | Qué es | ¿Algo parecido commiteado? | Recomendación |
|---|---|---|---|---|---|
| `...\VRP Chile\experiments\_s140` | 5,8 MB | 5 | `banco_paridad_*.json`, `magnitud_osf_out.json` y `_dl_referencia/` (CSV de referencia, ignorados) | No: `git log -- experiments/_s140` está vacío en todas las ramas. El repo la declara regenerable (`tasks/BLOQUE_ARRANQUE_S141.md:30`; `_s146_espacio/inventario_ignorados.json`: REGENERABLE_DESCARGA) | BORRAR SEGURO |
| `...\experiments\_s160_espacial\_censo_s159` | 14 MB | 36 | Resultados crudos del censo del oráculo (runs 39713438252 y 39715348772), `objetivos.json`, `probe_n.py`, `.tar.gz` | El `INFORME.md` commiteado de `_s160_espacial` los cita como insumo. Hay copia en `D:\...\s159_oraculo`. `probe_n.py` no está versionado en ninguna parte | PREGUNTAR |
| `...\experiments\_s160_espacial\data` | 44 MB | 4 | Copia de 3 JSON de `data/mirova_equivalent` (Isluga, Cordón Caulle, Tupungatito) del commit db0dfe847 | `Isluga.json` tiene el mismo md5 que `git show db0dfe847:data/mirova_equivalent/Isluga.json`; los otros dos no se compararon uno a uno | BORRAR SEGURO |

Espacio: BORRAR SEGURO 50 MB y PREGUNTAR 14 MB, todo en C:.

## 5. Stashes (solo listados, no abiertos)

| Stash | Fecha | Descripción | Archivos | Recomendación |
|---|---|---|---|---|
| stash@{0} | 2026-05-25 | On work-s78-audit-final: WIP audit fresh | 2 archivos, +1073 -4542 | PREGUNTAR |
| stash@{1} | 2026-05-23 | WIP on claude/s74-frontend-bugs-plan: 73af5e7 | 3 archivos, +20 -1 | PREGUNTAR |
| stash@{2} | 2026-05-23 | WIP on s72-cierre-bloque-s73: 153f9ec | 1 archivo, +225 -7 | PREGUNTAR |
| stash@{3} | 2026-05-22 | WIP on s72-f2.6b-no-cap-ab: 1fc7bcb | 1 archivo, +72 -16 | PREGUNTAR |

Los cuatro existen solo en el repo local, no en el remoto, y no puedo saber si su contenido llegó a main. Regla A96 y A38: no tocar sin tag defensivo. El peso en disco es SIN DATO (despreciable, son objetos de git).

## Resumen por disco (secciones 1, 2 y 4; cifras redondeadas)

| Recomendación | C: | D: |
|---|---|---|
| BORRAR SEGURO | 7,7 GB | 2,9 GB |
| PREGUNTAR | 3,8 GB | 7,9 GB |
| CONSERVAR | 1,0 GB | 0 |

Si se hace solo lo BORRAR SEGURO, D: pasaría de 8,6 GB a unos 11,5 GB libres (todavía cerca del 95 % de uso). Para ganar margen real en D: hay que decidir sobre las salidas de `temporales\` (6,8 GB) y `s158_d17` (1,1 GB).

## Qué no pude comprobar (SIN DATO)

- Si los archivos ignorados o sin seguimiento de la sección 1 (gracious-merkle 6,6 MB, s158-audit-r2 2,8 MB, s158_d17 1,9 MB, s159-pruebas 118 MB + 28 MB) se regeneran con los scripts versionados: lo deduje por nombre y por el `.gitignore`, no corrí nada.
- Si el detector K de S153 dejó obsoleto a #776.
- La fecha de vencimiento de los artefactos de los runs de `s157_chillan` y `s159_n`.
- Contenido archivo por archivo de las carpetas de `temporales\` y de `D:\vrp-trabajo\tmp`: se clasificaron por nombre, subcarpetas y búsqueda de la ruta en `origin/main`.
- Peso en disco de los stashes.
