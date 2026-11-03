# S173: cenit MODIS de Chillán, ablación por pieza de la vía «código MIROVA»

## Por qué

Cuando MODIS mira el domo de Nevados de Chillán de lado, el píxel nativo crece y el calor del foco queda repartido en
más suelo. K (el detector de producción hasta S172) pierde magnitud con el cenit: contra MIROVA en la misma pasada la
razón es 0,75 bajo 30° y 0,20 sobre 30° (S172, n 12), y las alertas protegidas a ~58° no se publican. La vía MOD-D
(encendida en producción desde el 2026-11-02 20:11 UTC) lleva la razón cerca de 1 en todos los cenit, pero cambia
varias piezas juntas. Este arnés reemplaza las piezas de la vía de a una para saber cuál corrige la caída: el remuestreo
a la grilla fija (D17) o el fondo que se resta (D25).

## Qué hay

| archivo | qué es |
|---|---|
| `piezas.py` | los brazos (V0, X2, FA, FSH, SC, FA_SC, RN, G5, NAT, NAT_AREA), con el porqué de cada uno en el docstring |
| `ablacion_cenit_modis.py` | el arnés del runner: por pasada baja L1B y MxD03, corre K, V y los brazos, compara con producción |
| `pasadas_chillan_modis.json` | las 27 pasadas MODIS de Chillán con alerta de MIROVA (2026-09-29 a 2026-11-02): gránulo, cenit, VRP de MIROVA, razón de K y razón del brazo V del A/B de MOD-D |
| `probar_local.py` | controles sin red y sin pyhdf (corre en Windows y en el runner antes de la ablación) |
| `.github/workflows/s173-cenit-modis.yml` | el workflow: sólo `workflow_dispatch`, sólo `EARTHDATA_TOKEN`, sin push, artefacto `s173-cenit-modis` |

## Controles

- K = record de producción guardado (salvo marcas de hora). Si el record lo escribió otro commit y no calza, el
  resultado lo dice (`control_produccion_dif`, `guardado_codigo_sha`) y esa pasada no sirve para atribuir.
- En las 2 pasadas del 2026-11-02 producción ya escribió con la vía: ahí el control es V = record guardado.
- V0 (los brazos) = V (la vía por `calculate_vrp`): mismas celdas y mismo VRP (`control_V0_igual_V`).
- V / MIROVA = razón del brazo V de la lectura del A/B de MOD-D (campo `razon_V_lectura_ab` de la lista, 16 pasadas).
- X2 dobla el VRP sin mover celdas (control positivo); cada brazo tiene que cambiar algo en alguna pasada.

## Qué haría falta para correrlo

1. Mergear esta rama a `main` (un `workflow_dispatch` sólo se puede despachar si el yml está en la rama por defecto,
   S73). Es un archivo nuevo de workflow y una carpeta de `experiments/`; no toca `pipeline/`, `data/` ni `frontend/`.
2. Que `EARTHDATA_TOKEN` esté vigente en los secretos del repositorio (el workflow falla al instante si viene vacío).
3. Despachar: `gh workflow run s173-cenit-modis.yml --ref main` (todas) o con `-f solo=2026-10-17_0850,...`.
4. Bajar el artefacto `s173-cenit-modis` y leer `s173_cenit_modis.json`: por brazo, razón contra MIROVA partida en
   z < 30 y z >= 30, y Spearman con el cenit con 200 barajados (semilla 173). La lectura local de los recortes que
   quedan en `nativos/` se puede repetir sin volver a NASA.

## Cómo se lee

Una pieza «corrige la caída oblicua» si al REEMPLAZARLA por la de K, con el resto de la vía intacto, la razón sobre 30°
vuelve a caer hacia la de K mientras la de bajo 30° se mueve poco. Si dos brazos hunden la razón, las dos piezas
interactúan y no se pueden adoptar por separado.
