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

> Nota de versionado (S92, post-pivote): los números 342/657 y "0 diferencias"
> son del A/B **mar-abr** (sin pasadas diurnas → enabled==disabled). Tras el reproc
> de **mayo** (pivote, §5) el JSON de NdC cambió a **812/846 records** y enabled≠
> disabled **en MODIS** (las pasadas diurnas, esperado). La afirmación #2.2 se
> **re-confirmó** con la data de mayo: `verify_findings.py` chequea ahora que
> **0 records VIIRS comunes difieren** (con tolerancia de redondeo) → el flag sigue
> sin tocar VIIRS. Villarrica (no reprocesado) mantiene 342/0-difieren.

---

## Implicación para S92
El A/B actual **no tiene veredicto** sobre la detección diurna (puerta de fetch
cerrada). Para obtenerlo hay que re-correr con la 1ª compuerta abierta en el
perfil enabled. `enable_daytime_modis` sigue **OFF**; sin A/B válido no se adopta
(escudo anti-drift §3.5). Opciones de implementación a decidir con Nicolás (no
tocar pipeline sin tag+OK, A45).

## 5. Cierre del A/B (S92) — pivote a mayo por disponibilidad de TIF

El fix del workflow (PR #269, `--no-night-filter` en el perfil enabled) abre la
compuerta. Pero al planificar el cierre apareció un **desajuste de ventanas**:

- Los TIF de MIROVA para NdC (`../mirova-tif-archive/data/tif/ChillanNevadosde/`)
  solo existen **2026-05-09 → 05-20** (inicio del scraping de TIF). El evento
  motivante 03-17 **no tiene TIF** → el **R2 pixel-level (§7.3) es imposible** en
  mar-abr.
- Mayo tiene **10 TIF MODIS diurnos** de NdC (13:25/14:00 UTC, etc.).

→ **Decisión**: cancelar el reproc mar-abr (26694976220) y disparar **mayo**
(run **26695436240**, NdC 2026-05-08→05-21). Una sola ventana cierra §7: A/B
recall + R3 CSV + R2 pixel-level. Sin TIF, mar-abr solo daba R3 (correlación a
nivel evento), que NO descarta FP solar — y la regla S33 prohíbe adoptar sin R2.

### Hallazgo TIF MODIS diurno (afecta el diseño del R2)
El TIF MIROVA MODIS diurno de NdC NO es un mapa de hotspots: `20260509_132500_MODIS`
tiene **2582/2601 píxeles positivos** (casi toda la grilla 51×51), valores
0.13–0.51 MW; `20260517_134000` 2581 pos, 0.16–0.51. Es el **campo de radiancia
diurno completo** — de día el sol calienta toda la escena en el MIR (A24: el TIF
"Last" es producto de visualización, no VRP-per-pixel sumable). Implicación: el R2
MODIS diurno NO puede medir "concordancia de todos los píxeles" (daría "solo
MIROVA" ≈ toda la grilla). Debe medir si el **pico** del TIF MIROVA (el cráter,
~0.51) coincide ESPACIALMENTE con nuestro hotspot. `compare_tif_mirova_vs_ours.py`
(hoy VIIRS-only) necesita adaptación: (1) buscar record MODIS, (2) apuntar al TIF
MODIS de mayo, (3) leer del perfil `_daytime_modis_enabled`, (4) métrica de
concordancia del pico, no suma.

### Plan de cierre (cuando termine run 26695436240)
1. `git pull` (traer los 2 JSON de mayo).
2. `python experiments/_s90_daytime_modis/analyze_ab.py --volcano NevadosDeChillan
   --start 2026-05-08 --end 2026-05-21` → [1] Δrecall/precisión, [2] nuevas
   diurnas, [3] R3 TP-MIROVA vs FP-solar. OJO: usa CONS (latest_consolidado.csv);
   el GT diurno de NdC puede estar en OCR (A11) → cruzar también OCR si CONS=0.
3. R2 pixel-level de ≥1 evento MODIS diurno vs su TIF (concordancia del pico).
4. Criterio §7: recall diurno ↑ en ≥1 vol SIN precisión global <0.50 + ≥1 evento
   validado pixel-level. Si FP solares dominan → NO adoptar, documentar.
5. Si valida → `enable_daytime_modis:true` en mirova_equivalent.yaml con TAG + OK
   explícito Nicolás (A45) + reproc operacional + dashboard.

## 6. VEREDICTO A/B (NdC mayo 08-21) — NO ADOPTAR (inconcluso, path inocuo)
Fuente reproducible: `analyze_ab.py` + `close_ab.py` (este dir).

**Composición**: enabled MODIS=63 vs disabled MODIS=29 (+34 pasadas diurnas
bajadas por `--no-night-filter` → el fix #2.1 funcionó, el path por fin tuvo
escenas diurnas). De ellas **23 son MODIS diurnas** (elev>0).

**Resultado**:
- **22 de 23 pasadas diurnas → meq=0.00** (sin detección), incluso con t_max
  280–298 K (terreno calentado por sol). Los umbrales diurnos (K1=-0.6, 15σ) NO
  se dispararon → **el path NO genera FP solares masivos** (el riesgo central de
  la detección diurna NO se materializó).
- **1 sola detección diurna**: 2026-05-20 20:45 (elev 10°=atardecer, MODIS_AQUA,
  3.91 MW, 3.44 km=summit). NO matchea ALERTA MIROVA (CONS ni OCR).
- **MIROVA OCR = 0 ALERTAS de NdC en toda la ventana** → NO hubo eventos diurnos
  reales que capturar. Δrecall=0, Δprecisión=−8.3% (la única detección suma 1 FP).
- **R2 pixel-level INVIABLE**: las pasadas de mediodía (donde hay TIF MODIS, p.ej.
  05-09 13:25) dan meq=0 → no hay detección nuestra que comparar contra el TIF. La
  única detección (05-20 atardecer) no tiene TIF de su pasada.

**Criterio §7 NO se cumple**: recall diurno no subió (no había eventos MIROVA
diurnos), 0 eventos validados pixel-level. → **enable_daytime_modis se mantiene
OFF.** El A/B fue **inconcluso por ventana inadecuada** (mayo NdC sin actividad
diurna MIROVA), NO por fallo del path. Lo único demostrado (valioso): el path es
**inocuo** (no inunda de FP solares). Para un veredicto DEFINITIVO se necesita una
ventana con actividad diurna MIROVA confirmada + TIF de esa pasada (el evento
motivante 03-17 mediodía sería ideal, pero NO tiene TIF — A24 scraping empezó may).
El 05-20 (3.91 MW, sol bajo, no publicado) es indistinguible entre FP solar y
señal real débil no-publicada (A54) sin TIF/OCR.
