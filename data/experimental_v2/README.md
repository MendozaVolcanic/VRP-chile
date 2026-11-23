# data/experimental_v2: sombra C0, CONGELADA desde el 2026-11-23 (S196)

**Qué es.** La serie del perfil `experimental` en los 11 Tier A: la detección que tenía producción el 2026-10-09
(conectiva `min` y Test 1 integrado, PR #771), congelada en S150 para guardar lo que el detector anterior veía. La
escribía `.github/workflows/experimental-diario.yml` una vez al día, y `.github/workflows/vigilancia-sombra.yml` la
comparaba contra producción y contra MIROVA para disparar la reversión de K.

**Por qué se congeló.** Desde el 2026-11-11 ningún sensor de producción corre K: los tres corren la vía «código
MIROVA». La vigilancia daba `SIN_OBJETO` cada día (última corrida automática: 2026-11-23 03:59 UTC,
`data/audit_continuous/sombra_latest.json`), así que la sombra ya no protegía ninguna adopción y costaba unos 186
minutos-job por día. Nicolás decidió retirarla el 2026-11-23 (D-B de `docs/PLAN_EXPERIMENTAL_MEJORAS_S196.md` §14,
textual: «lo que recomiendas»; es la opción D1-b de `docs/PLAN_EXPERIMENTAL_S190.md`).

**Qué quedó así.**

- Los dos workflows no tienen cron ni `workflow_run`; sólo el despacho manual. Despachar `experimental-diario.yml`
  vuelve a escribir esta carpeta, es decir, la descongela: eso lo decide Nicolás.
- Último dato commiteado al abrir el PR del retiro: 2026-11-22 21:19 UTC. Si el workflow alcanzó a correr antes del
  merge, el último es el de ese día (`git log -1 -- data/experimental_v2`).
- Los archivos NO se borran (A38). Borrarlos queda para el final del plan, con tag defensivo y confirmación.
- La pestaña «Laboratorio» del tablero (`frontend/experimental/index.html`) sigue leyendo estos archivos y muestra el
  aviso «SERIE CONGELADA». Cuando el laboratorio nuevo (`data/laboratorio_v1/`) tenga cron, la pestaña pasa a leerlo
  (paso 2 de P10).
- `scripts/vigilancia_sombra.py` se conserva: las vigilancias de guardia de MODIS y VIIRS importan sus funciones.
- `tests/test_retiro_sombra_c0_s196.py` vigila que los dos workflows sigan sin disparo automático.
