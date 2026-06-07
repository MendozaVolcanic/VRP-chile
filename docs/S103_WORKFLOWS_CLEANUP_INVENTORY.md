# S103 — Inventario de limpieza de workflows GH Actions (A38)

**Fecha**: 2026-06-07 · Cleanup de workflows `reproc-*` one-off de sesiones cerradas
que ensucian la lista de CI (25 → 12). A38: inventario + tag defensivo
`pre-s103-workflows-cleanup` antes de borrar. Recuperable: `git checkout
pre-s103-workflows-cleanup -- .github/workflows/<archivo>` o desde el historial.

Todos los archivados son `workflow_dispatch`-only (sin cron) → 0 impacto operacional.
Las RUNS históricas en la pestaña Actions NO se borran (solo la definición del yml).

## KEEP (12)
### Operacionales (6)
- `nrt.yml` — cron NRT cada 2h (núcleo del sistema).
- `nrt-retry.yml` — cron retry +30min.
- `nrt-monitor.yml` — alerta si fallan 3+ corridas.
- `nrt-healthcheck.yml` — healthcheck.
- `pages-deploy.yml` — deploy del dashboard a GitHub Pages.
- `sync-mirova-csv.yml` — sync del CSV ground-truth MIROVA.

### Últimas 3 sesiones (referencia / live) (6)
- `reproc-s103-viirs-nadir-promote.yml` — **LIVE, corriendo run 27098410956**. NO tocar.
- `reproc-s102-nadir-promote.yml` — template de promoción (clonado para s103).
- `reproc-s102-viirs-nadir-ab.yml`, `reproc-s102-viirs-noctx-ab.yml` — A/B VIIRS S102.
- `reproc-s101-nadir-validation.yml`, `reproc-s101-sec3-ab.yml` — S101.

## ARCHIVE / DELETE (13) — reprocs one-off de sesiones cerradas
- `reproc-ab-f-s81-a-intra-radio.yml` (S81-S84, gate adoptado en main)
- `reproc-ab-f-s81-b-prime.yml` (S85, gate adoptado en main)
- `reproc-daytime-modis-ab.yml` (S90, flag OFF, A/B cerrado)
- `reproc-s88-lascar-validation.yml` (S88)
- `reproc-s94-f2-validation.yml` (S94)
- `reproc-s94-f2-viirs.yml` (S94)
- `reproc-s97-refresh-viirs.yml` (S97, refresh promovido)
- `reproc-s98-anchor.yml` (S98, ancla promovida)
- `reproc-s99-test1-ab.yml` (S99, A/B cerrado)
- `reproc-s100-promote-ctxpeak.yml` (S100, ctxpeak promovido)
- `reproc-s100-test1-ab-full.yml` (S100)
- `reproc-s100-test1-ab-heavy3.yml` (S100)
- `reproc-s100-test1-ab-paired.yml` (S100)

Resultado: 25 → 12 workflows. Recuperación: tag `pre-s103-workflows-cleanup`.
