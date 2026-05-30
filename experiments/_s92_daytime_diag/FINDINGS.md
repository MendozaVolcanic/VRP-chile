# S92 — Diagnóstico del A/B de detección diurna MODIS (#2.1 y #2.2)

**Fecha**: 2026-05-30. **Método**: systematic-debugging, 100% offline sobre los
JSON del A/B ya commiteados (`data/_daytime_modis_{enabled,disabled}/`).

**Integridad (§0.5 BLOQUE_ARRANQUE_S92)**: todos los números de este doc salen
de scripts reproducibles en este mismo directorio. Verificación programática:
`python verify_findings.py` → debe imprimir `ALL_VERIFIED`.

- `diag.py` — fuente de verdad de #2.1 (clasificación día/noche por granule).
- `diag_viirs_leak.py` — fuente de verdad de #2.2 (comparación vrp_mw / cluster).
- `diag_deep_diff.py` — cierre de #2.2 (deep diff campo por campo).

---

## #2.1 — Por qué el A/B no validó el path diurno (CAUSA RAÍZ IDENTIFICADA)

### Síntoma
El A/B (NdC, Villarrica) terminó `success` pero Δrecall=0 y 0 detecciones nuevas.
El diagnóstico S91 ya había visto "0 records MODIS diurnos" en NdC sin explicar
por qué.

### Hallazgo (verificado de 1ª mano, `diag.py`)
De los 135 records MODIS de NdC en el rango del A/B (mar–abr 2026), la hora UTC de
las pasadas se concentra en `{01:32, 02:36, 06:10, 07:39, 08:18}` — **todas
nocturnas** (Terra ~01–02 UTC ≈ 22–23 local; Aqua ~06–08 UTC ≈ 03–05 local).
**No hay ni una sola pasada en el rango diurno (~13–17 UTC).** Resultado de
`_scene_is_day` sobre el granule persistido: `day=0 night=135 unparsed=0`.

El evento motivante —NdC 2026-03-17 a mediodía— tampoco está: ese día solo hay
2 granules, ambos nocturnos (`MOD…A2026076.0210` 02:10 UTC, `MYD…A2026076.0725`
07:25 UTC). La pasada de mediodía nunca llegó al pipeline.

### Veredicto de las 3 hipótesis del bloque
- **H1 (no se procesaron escenas diurnas) → CONFIRMADA.**
- **H2 (`_scene_is_day` clasifica mal) → REFUTADA.** `unparsed=0`; parsea bien los
  135 granules y clasifica los nocturnos correctamente. La función funciona.
- **H3 (el gate de store rechazó el diurno) → REFUTADA.** No hay granule diurno
  que rechazar.

### Causa raíz (doble compuerta en serie)
1. `pipeline/fetch.py:472` `fetch_granules(..., nighttime_only=True)` por defecto,
   y `:524` `_filter_nighttime_granules` descarta las pasadas diurnas **antes de
   descargar**.
2. `pipeline/store.py:63` `_reject_daytime` rechaza records diurnos salvo MODIS
   con el flag ON (segunda red).

El A/B controla la 2ª compuerta vía perfil (`enable_daytime_modis`) pero **NO la
1ª**: `nighttime_only` se controla por el flag CLI `--no-night-filter`
(`scripts/run_pipeline.py:395`, `nighttime_only = not args.no_night_filter`), que
el workflow `reproc-daytime-modis-ab.yml` (líneas 74–79) **no pasa**. Por eso el
perfil enabled bajó solo pasadas nocturnas y el path diurno nunca tuvo escena
sobre la cual actuar.

**Conclusión: NO es bug del pipeline** (el path diurno y `_scene_is_day` están
bien). Es un **defecto del diseño del experimento A/B**: las dos compuertas
(filtro de fetch ↔ flag de thresholds/gate) están desacopladas y el experimento
solo abrió una. Para validar el path hay que correr el perfil enabled con
`--no-night-filter` (decisión de implementación abierta — ver más abajo).

> Caveat honesto: que el night filter sea la causa del experimento está
> confirmado (código + datos). Si además el catálogo LANCE/earthaccess tiene o no
> la pasada diurna útil del 03-17 (geometría de swath) solo se sabrá al re-correr
> fetch con `--no-night-filter`. Físicamente MODIS pasa de día sobre Chile central
> casi a diario, así que es muy probable que sí.

---

## #2.2 — ¿El flag diurno altera records VIIRS? (REFUTADO)

### Síntoma (S91, NO confirmado — entorno degradado)
El diff S91 enabled vs disabled de Villarrica habría mostrado ~108 records con
`mirova_eq_vrp` distinto, casi todos VIIRS.

### Hallazgo (verificado de 1ª mano, `diag_viirs_leak.py` + `diag_deep_diff.py`)
- Villarrica: 342 records emparejados (276 VIIRS + 66 MODIS). **0 difieren en
  `vrp_mw` (scene-wide). 0 difieren en `primary_cluster.vrp_mw`.**
- NdC: 657 records (522 VIIRS + 135 MODIS). Idéntico: **0 diferencias.**
- Deep diff: el **único** campo que difiere es el top-level `updated` (timestamp
  de fin de reproc; Villa 16:51 vs 18:07). El orden de records es idéntico y
  **ningún campo de ningún record cambia**. El md5 distinto era solo el timestamp.

### Confirmación en código
- `process_viirs.py` / `process_viirs_mod.py`: **0 referencias** a daytime/`_day`/
  flag. El flag no entra al procesamiento VIIRS.
- `store.py:_reject_daytime`: de noche acepta siempre (flag irrelevante); de día
  la rama de excepción exige `sensor.startswith("MODIS")`, así que VIIRS diurno se
  rechaza con o sin flag. **El flag no puede tocar VIIRS por ninguna vía
  determinista.**

**Veredicto: no hay fuga de scope. La sospecha #2.2 fue un artefacto del diff
degradado de S91** (reordenamiento de claves / timestamp leídos como "diff").

---

## Implicación para S92
El A/B actual **no tiene veredicto** sobre la detección diurna (puerta de fetch
cerrada). Para obtenerlo hay que re-correr con la 1ª compuerta abierta en el
perfil enabled. `enable_daytime_modis` sigue **OFF**; sin A/B válido no se adopta
(escudo anti-drift §3.5). Opciones de implementación a decidir con Nicolás (no
tocar pipeline sin tag+OK, A45).
