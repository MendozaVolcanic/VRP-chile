# Insumos de S160 (bajados una vez por el orquestador, 2026-10-22 03:11 UTC)

- Código auditado: `origin/main` = `d516b9d8c0fad5b0ca458b9fb57cdf5e6f75f956` («SHA_MAIN»).
- Instantánea del código (pipeline, scripts, frontend, .github, tests, CLAUDE.md, docs): `D:\vrp-trabajo\temporales\s160_audit\main\`.
- **Datos**: los del worktree `C:\vrp-trabajo\s159-pruebas` NO son los de SHA_MAIN. Leer sólo
  `D:\vrp-trabajo\temporales\s160_audit\main\data\` (mirova_equivalent, mirova_reference) y
  `D:\vrp-trabajo\temporales\s160_audit\main\latest_consolidado.csv`, extraídos con `git archive` de SHA_MAIN.
  Si necesitas otro archivo de SHA_MAIN: `git -C C:\vrp-trabajo\s159-pruebas show d516b9d8c:<ruta>`.
- Referencia de MIROVA en dos versiones (regla del plan §11.2.1): tabla sola = `latest_consolidado.csv`
  (y `data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv` si existe); combinado = tabla más
  `data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv`. Calcula y declara el sha256 de lo que uses.
- Aquí: `hora_servidor.txt`, `rate_limit_inicio.json`, `commits_mirova_v1.tsv` y `commits_vrp_chile.tsv` (30 últimos),
  `runs_nrt.tsv` y `runs_sync-mirova-csv.tsv` (50 últimas corridas: id, creado, actualizado, estado, conclusión, evento,
  sha), `secretos_nombres_y_fecha.txt` (sólo nombres y fecha de actualización, nunca valores), `pr889.json`,
  `prs_abiertos.json`.
- Ramas de los A/B: `origin/s146-ab/<run>` (30 ramas). Extraer por ruta con `git show`, nunca `checkout` ni `pull`.
- PR #889: `origin/s159-instrumentos` (`d0968e389`). Arreglo de Suomi NPP en curso: worktree
  `C:\vrp-trabajo\s159-instrumentos` (rama local `s159-cese-snpp`, de otra sesión): sólo lectura.
