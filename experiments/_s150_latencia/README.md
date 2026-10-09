# Latencia del NRT contra MIROVA (medición "antes", S150)

Traídos al repo desde la sesión del congreso (2026-10-05) para repetir la misma medición después de activar
el disparador externo del NRT (`docs/audit_s142/CRON_EXTERNO_PASO_A_PASO.md`).

**Qué mide.** Latencia = tiempo desde la adquisición del satélite hasta que el dato se ve.
- VRP Chile: primer commit `NRT update` que trae la pasada (`first_seen.py`, recorre el historial de git de
  `data/mirova_equivalent/<Volcan>.json`) más el término del siguiente deploy de Pages (`pages_runs.json`).
- MIROVA: primera vez que el scraper de Mirova-v1 vio la pasada (`Fecha_Proceso_GitHub` del CSV consolidado,
  en hora de Chile, convertida a UTC en `pair.py`).
- Pareo: mismo volcán, misma familia de sensor, adquisición con 3 min o menos de diferencia.

**Resultado "antes"** (11 Tier A, pasadas nocturnas del 2026-09-14 al 2026-10-02, 1.660 pares,
`pares_antes_2026-09-14_a_2026-10-02.csv`): VRP Chile mediana 5,05 h (p10 2,66, p90 9,05); MIROVA 2,77 h
(p10 1,93, p90 5,00); VRP Chile llega primero en 319 de 1.660.

**Salvedades verificadas en S150.** `processed_utc` no sirve para esto: `pipeline/store.py` lo reescribe a
propósito en cada guardado. Todos los primeros commits del período son del bot del NRT (no hay reprocesos
mezclados). La latencia de MIROVA incluye el atraso del propio scraper, que también corre en GitHub, así que
la ventaja de MIROVA es igual o mayor que la medida.

**Para repetir.** Bajar `pages_runs.json` (`gh run list --workflow pages-deploy.yml -L 500 --json
createdAt,updatedAt,conclusion`) y el CSV consolidado de Mirova-v1, correr `first_seen.py <Volcanes>` desde
esta carpeta y después `pair.py` (ajustar la ventana de fechas en `pair.py`).
