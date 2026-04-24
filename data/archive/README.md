# data/archive/ — archivo histórico VRP Chile

Esta carpeta contiene datos que **ya no se cargan en el dashboard operacional**
pero se preservan para auditoría histórica. La historia git completa de cada
archivo está intacta (el movimiento se hizo con `git mv`), así que cualquier
consulta tipo `git log --follow data/archive/<ruta>/<archivo>` devuelve el
historial original desde antes del movimiento.

## Subcarpetas

### `mirova_equivalent_pre_s18/`

**34 JSONs** de volcanes **NO monitoreados por MIROVA** que fueron procesados
por el perfil `mirova_equivalent` entre S4 y S17 antes de la limpieza S18.

**Qué contienen**: historial de detecciones del pipeline VRP Chile sobre
volcanes que MIROVA no tiene en su catálogo oficial (Taapaca, Parinacota,
Guallatiri, Laguna del Maule, Osorno, Calbuco, Villarrica austral, etc.).

**Por qué se archivaron**: el perfil `mirova_equivalent` es, por definición,
"clon MIROVA operacional". Procesar volcanes sin ground truth MIROVA dentro
de ese perfil confundía el dashboard y la auditoría. Nicolás (S18 2026-04-24)
pidió limpieza: "que no se muestre data antigua en el dashboard, pero sin
perder información para auditar en el futuro".

**Cuándo usarlos**:
- Auditoría tipo "¿cómo respondió el detector S15 a Laguna del Maule?".
- Comparación cross-versión ("¿el fix S18 NOAA-21 mejoró la detección en
  Osorno?"). Para eso basta con reprocesar ese volcán con el código S18
  actual en perfil `experimental` y comparar contra el JSON archivado.
- Recuperación: si en el futuro MIROVA agrega un volcán chileno a su
  catálogo, mover su JSON de vuelta a `data/mirova_equivalent/` con
  `git mv`.

**Última sesión que escribió**: S17 NRT cron auto (hasta 2026-04-24 antes
del mover).

### `mirova_old_refs_pre_s18/`

**12 JSONs** con las **referencias MIROVA previas a la consolidación** en
un solo CSV (`21_04_2026 registro_vrp_consolidado.csv`). Archivos con
sufijos `_OLD_pre_consolidado.json` (11) y `_OLD_with_OCR.json` (1).

**Por qué se archivaron**: después de S14 las refs MIROVA se consolidan en
`data/mirova/<Volcano>.json` directo (sin sufijo). Los `_OLD_*` quedaron
huérfanos de dead code S10/S11 — ningún script los lee desde entonces,
pero muestran la historia de cómo se scrapeó MIROVA en fases iniciales.

**Cuándo usarlos**:
- Reconstrucción histórica del scraper Mirova-v1 (ver el repo
  github.com/MendozaVolcanic/Mirova-v1).
- Diagnóstico tipo "¿qué cambió entre la ref MIROVA pre-consolidado y la
  actual?".

## Regla operacional

**No mover archivos DE VUELTA** a `data/mirova_equivalent/` o `data/mirova/`
sin una razón documentada (ej: MIROVA oficial agregó el volcán al catálogo,
o descubrimos un bug en la consolidación que afecta el archivo `_OLD_`).

**No eliminar archivos** de `archive/`. Si el espacio es un problema futuro,
comprimir o mover a un backup externo fuera del repo, pero preservar el
historial.

---

Archivado S18 — 2026-04-24 — Nicolás Mendoza (SERNAGEOMIN) + asistente Claude.
