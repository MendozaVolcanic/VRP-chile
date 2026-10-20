# Ensayo del reemplazo por el histórico con K (tarea 1.24, pasos b y c, S157)

**Qué es.** Ensayo, SIN aplicar, del reemplazo de la ventana 2025-02-15..2026-09-17 de
`data/mirova_equivalent/<Volcan>.json` por el reproceso con K de `data/_s154_reproc_k_historico/` (run
39125546355), para los 10 volcanes Tier A que no son NevadosDeChillan (Chillán se relanza aparte). Nada de
`data/mirova_equivalent/` se escribió: `ensayo.py` compara el sha256 de cada archivo operacional antes y después
y se detiene si cambia. Árbol: `origin/main` en `57d18ad78` (2026-10-20 03:16 UTC).

**Scripts** (todos desde la raíz del repo, en este orden):

| Script | Qué hace | Salida |
|---|---|---|
| `cobertura.py` | cuenta, por volcán, sensor y día, las pasadas (datetime_utc, sensor) de cada archivo en la ventana y ubica cada déficit en su trozo; rearma los trozos con `split_window(..., 37)` y se detiene si no coinciden con los jobs del run | `cobertura.json`, `cobertura.md` |
| `deficit_por_trozo.py` | las pasadas ausentes, por trozo y por `product_version` del record operacional | `deficit_por_trozo.md` |
| `ensayo.py` | corre `scripts/reemplazar_ventana_reproceso.py` sin `--aplicar` y con el tope del 2 % para cada volcán | `informe_<Volcan>.json`, `resumen.json` |

`jobs_run_39125546355.tsv` son los nombres y conclusiones de los 178 jobs del run, bajados con
`gh api repos/MendozaVolcanic/VRP-chile/actions/runs/39125546355/jobs`. Los 160 trozos de estos 10 volcanes
terminaron verdes; los 6 caídos son de Chillán.

## 1. Cobertura (A108)

Celda: pasadas en la operacional / en el reproceso (`-` sólo en la operacional, `+` sólo en el reproceso).

| Volcan | MODIS_AQUA | MODIS_TERRA | VIIRS_SNPP | VIIRS_NOAA20 | VIIRS_NOAA21 | VIIRS_SNPP_750 | VIIRS_NOAA20_750 | VIIRS_NOAA21_750 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Chaiten | 639/728 (-0 +89) | 622/710 (-0 +88) | 789/906 (-3 +120) | 820/933 (-3 +116) | 801/918 (-0 +117) | 783/898 (-3 +118) | 815/931 (-0 +116) | 800/917 (-0 +117) |
| Copahue | 579/661 (-1 +83) | 561/648 (-0 +87) | 744/850 (-5 +111) | 757/864 (-0 +107) | 743/850 (-0 +107) | 737/843 (-3 +109) | 749/854 (-2 +107) | 742/850 (-0 +108) |
| Isluga | 470/540 (-0 +70) | 456/523 (-0 +67) | 595/683 (-3 +91) | 615/708 (-0 +93) | 623/715 (-0 +92) | 593/681 (-3 +91) | 613/706 (-0 +93) | 620/712 (-0 +92) |
| Lascar | 482/553 (-0 +71) | 475/546 (-0 +71) | 629/719 (-3 +93) | 633/727 (-0 +94) | 620/709 (-0 +89) | 623/713 (-3 +93) | 627/720 (-0 +93) | 616/703 (-0 +87) |
| Lastarria | 491/560 (-0 +69) | 472/531 (-0 +59) | 650/745 (-3 +98) | 644/742 (-0 +98) | 622/716 (-0 +94) | 638/732 (-3 +97) | 629/726 (-0 +97) | 617/709 (-0 +92) |
| Llaima | 582/664 (-0 +82) | 562/633 (-0 +71) | 753/866 (-3 +116) | 783/897 (-0 +114) | 770/888 (-0 +118) | 750/860 (-3 +113) | 779/892 (-0 +113) | 768/885 (-0 +117) |
| PlanchonPeteroa | 552/637 (-0 +85) | 561/651 (-0 +90) | 698/805 (-3 +110) | 715/820 (-2 +107) | 719/824 (-1 +106) | 687/783 (-8 +104) | 712/813 (-4 +105) | 713/817 (-2 +106) |
| PuyehueCordonCaulle | 561/691 (-3 +133) | 554/679 (-1 +126) | 724/897 (-5 +178) | 751/924 (-1 +174) | 722/892 (-2 +172) | 723/895 (-4 +176) | 734/907 (-1 +174) | 714/884 (-0 +170) |
| Tupungatito | 540/617 (-0 +77) | 537/609 (-0 +72) | 694/793 (-4 +103) | 714/819 (-0 +105) | 714/818 (-0 +104) | 688/787 (-4 +103) | 707/811 (-0 +104) | 711/815 (-0 +104) |
| Villarrica | 666/666 (-0 +0) | 645/645 (-0 +0) | 857/858 (-0 +1) | 898/898 (-0 +0) | 888/888 (-0 +0) | 855/856 (-0 +1) | 894/894 (-0 +0) | 887/887 (-0 +0) |

**Días con menos pasadas en el reproceso** (detalle día por día en `cobertura.md`; por trozo en
`deficit_por_trozo.md`): entre 0 (Villarrica) y 20 pasadas (Planchón Peteroa) por volcán, 89 en total.

- **Trozo 15 (2026-07-18 a 2026-08-23), común a los 9:** 58 pasadas VIIRS Suomi NPP del 2026-08-05 y
  2026-08-06 (375 y 750 m). Los records operacionales son `nrt` (LANCE): el
  reproceso, que busca el producto estándar, no los encontró. Es el mismo patrón que la tarea 1.27 (Terra): puede
  que el estándar no exista y que repetir el trozo no los traiga. SIN VERIFICAR en CMR.
- **31 pasadas cuyo record operacional es `standard`**, o sea que el gránulo existía: NOAA-20 750 del
  2026-07-27 en Planchón Peteroa (trozo 15) y, en los trozos 2, 7, 11, 12, 14 y 16, Planchón Peteroa 2025-04-09 (9) y 2025-10-01 (4), Chaitén NOAA-20 2025-10-18 (3), Copahue
  2026-03-07, 07-02 y 07-05 (5), Puyehue Cordón Caulle 2026-04-25, 07-13 y 09-11 (9). Son cortes de NASA del
  run (A64, A108): repetir esos trozos debería traerlos.

**Pasadas que sólo trae el reproceso:** son, casi enteras, **el hueco de 2025-11-16 a 2026-01-28** de 9 de los 11
Tier A (y desde 2025-10-10 en Puyehue Cordón Caulle), el mismo de la marca S146 en `CLAUDE.md` (V-15). Villarrica,
el único continuo, sólo suma 2 (2026-08-10 05:36, Suomi NPP). Fuera del hueco hay 12 sueltas (Planchón Peteroa en
abril y octubre de 2025, MODIS Aqua diurno del 2026-07-20 21:45 en Chaitén y Puyehue Cordón Caulle). Ningún día
tiene a la vez pasadas que faltan y que sobran en el mismo sensor, así que no hay una misma pasada con dos horas
distintas que se duplicaría.

## 2. Veredicto del ensayo por volcán

| Volcan | Veredicto | En ventana | Reemplazados | Agregados | Se quedan en C0 | Fracción | C0 nrt / standard | Records antes, después |
|---|---|---:|---:|---:|---:|---:|---|---|
| Chaiten | PASA | 6069 | 6060 | 881 | 9 | 0,15 % | 6 / 3 | 6445, 7326 |
| Copahue | PASA | 5612 | 5601 | 819 | 11 | 0,20 % | 6 / 5 | 5958, 6777 |
| Isluga | PASA | 4585 | 4579 | 689 | 6 | 0,13 % | 6 / 0 | 4871, 5560 |
| Lascar | PASA | 4705 | 4699 | 691 | 6 | 0,13 % | 6 / 0 | 4999, 5690 |
| Lastarria | PASA | 4763 | 4757 | 704 | 6 | 0,13 % | 6 / 0 | 5069, 5773 |
| Llaima | PASA | 5747 | 5741 | 844 | 6 | 0,10 % | 6 / 0 | 6105, 6949 |
| PlanchonPeteroa | PASA | 5357 | 5337 | 813 | 20 | 0,37 % | 6 / 14 | 5691, 6504 |
| PuyehueCordonCaulle | PASA | 5483 | 5466 | 1303 | 17 | 0,31 % | 8 / 9 | 5861, 7164 |
| Tupungatito | PASA | 5305 | 5297 | 772 | 8 | 0,15 % | 8 / 0 | 5647, 6419 |
| Villarrica | PASA | 6590 | 6590 | 2 | 0 | 0,00 % | 0 / 0 | 6957, 6959 |

Los 10 pasan el tope del 2 % con margen (el peor, 0,37 %). Salida cruda de cada uno en `resumen.json`
(`stdout`, `codigo_salida`).

**Lo que el PASA no dice, y que quien aplique (paso d) tiene que saber:**

1. **El reemplazo no sólo reemplaza: llena el hueco.** Agrega 7.518 records en los 10 volcanes, casi todos de
   noviembre de 2025 a enero de 2026. El operador vería en el tablero 74 días de datos que nunca tuvo (111 en
   Puyehue Cordón Caulle). Es dato real y con K, pero es un cambio de la serie distinto de "cambiar de detector",
   y conviene decirlo en el commit y en la ficha.
2. **Quedan 89 pasadas en C0 sin marca de régimen** (ningún record operacional de la ventana trae `regimen`), mezcladas
   con las de K, que sí la traen (`perfil: _s154_reproc_k_historico`). Se distinguen por esa marca; si se quieren
   K, hay que repetir los trozos de la lista de arriba (los 31 `standard`) antes de aplicar.
3. **Cuánto cambia lo publicado.** `reemplazos_que_cambian_vrp_mw` y `reemplazos_que_cambian_distance_class` en
   `resumen.json` cuentan los reemplazos donde cambia el número (entre 2.548 en Láscar y 4.068 en Puyehue Cordón
   Caulle). Es una diferencia de campo, no la publicación del tablero: no se pasó por `isValidDetection`.

## 3. Verificador con contexto limpio (paso c)

Ver `verificador/INFORME.md`. Recibió sólo las rutas y los scripts, sin el resultado esperado.
Sus scripts están en `verificador/scripts/`. Resumen, de mayor a menor gravedad (detalle y salida cruda en el informe):

- **G4. No hay una frontera de detector correcta si Chillán queda aparte.** `DATOS_K_DESDE_UTC`
  (`frontend/cambio_detector.js:26`, hoy 2026-09-18) es una sola fecha para todos los volcanes, y la leen el
  tablero y `scripts/auto_audit_weekly.py`. Si no se mueve, el aviso rotula C0 a 19 meses de K de 10 volcanes; si
  se mueve al 2025-02-15, rotula K a la historia de Chillán. Comprobado por quien orquesta. Consecuencia para el
  paso d: o se aplican los 11 juntos (como dice el plan), o la frontera pasa a ser por volcán.
- **G3. El tope del 2 % no garantiza cobertura.** Quitando en memoria todo VIIRS_SNPP 375 de un trozo de 37 días,
  los 10 pasan; quitando 375 y 750, Villarrica sigue pasando (Llaima se rehúsa). La compuerta real es `cobertura.py`,
  que no corta.
- **G3. Las 89 pasadas que quedan en C0 publican unas 40 veces** en el tablero (port en Python de `mirovaEqVrp`, no
  node), entre ellas Puyehue Cordón Caulle MODIS Terra del 2026-07-13 con 5,0 MW. El tablero no lee la marca.
- **G3. El ensayo no medía lo publicado.** Lo publicado en la ventana cae, por ejemplo, de 2.133 a 17 en Llaima y de
  2.761 a 86 en Villarrica: es el efecto de K, pero no se cruzó con las alertas de MIROVA de 1 MW o más (SIN PROBAR).
  Docstring de `ensayo.py` corregido.
- **G2.** El script exige el perfil pero no el `codigo_sha` (los relanzamientos de Chillán corren sobre otro sha);
  con `--aplicar` la escritura no es atómica; quedan 1 a 4 records C0 por volcán después de la ventana.
- **G1.** Los agregados no tienen tope; el arnés podría leer un informe viejo si el script se cae.

Verificado limpio por él: números reproducidos, fuera de la ventana el archivo no cambia un byte, sin duplicados
C0 contra K, reproceso de un solo commit, ningún reemplazo baja de `standard` a `nrt`, cuentas del README.
