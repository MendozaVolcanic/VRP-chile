# S192: reemplazo de los records MODIS con fondo nulo (sigue a #1065)

## El fenómeno

El VRP es el exceso de radiancia del píxel caliente sobre el suelo que tendría sin la anomalía. Cuando el píxel alertado
queda junto a un hueco de datos (borde del barrido, celdas sin dato), el halo del código de MIROVA se come a sus
vecinos útiles y la interpolación (`fillmissing2`) no llega hasta él: el fondo queda vacío. El código de MIROVA lo suma
como cero y publica la radiancia entera del píxel como si fuera exceso. En MODIS, MIROVA no tiene ninguna detección así
en su base de 2000 a 2025 y el único caso cotejable fue un falso positivo nuestro (Cordón Caulle, 2026-03-16 03:10).
Nicolás decidió el 2026-11-20 (opción a) que esa escena MODIS es **no medida**; en VIIRS se publica como MIROVA y se
marca. #1065 (ficha v1.51) lo aplica a las pasadas nuevas. Este directorio lleva los records ya guardados a la misma
forma, sin reprocesar.

## Qué hace el script

`reemplazo_fondo_nulo.py` recorre `data/mirova_equivalent`, `data/historia_34` y `data/sombra_34` y toma cada record
MODIS de la vía (`via_codigo_mirova: true`) con `diag_codigo_mirova.L_bk == 0` exacto y algún alertado. Lo deja en la
forma exacta de la rama vacía de `pipeline/mirova_v750_codigo.py::procesar_grilla`: 0 MW, sin píxeles, cúmulo, clase,
temperaturas y posiciones nulas, `motivo_vacio: "fondo_no_estimado"` y `alertados_sin_fondo` = el
`n_anomalous_pixels` anterior. Conserva `L_hot`, `L_bk`, el resto del diagnóstico, los ángulos, el gránulo,
`processed_utc` y `regimen` (la detección la hizo ese código; sólo cambia qué se publica de ella). `vrp_mw` queda en 0
entero, como `store.py` guarda toda escena vacía de la vía.

No toca VIIRS, ni MODIS con fondo (un solo alertado con fondo da `L_bk > 0`), ni records de K, ni escenas ya vacías.
Cada archivo se reescribe en su mismo formato (sangría, ASCII, saltos de línea); si ningún formato conocido lo
reproduce byte a byte, o un record trae claves que una escena vacía no tiene, rehúsa antes de escribir (código 2).

**Por qué equivale a reprocesar.** `L_bk` es la suma de los fondos que existen. Con `L_bk == 0` exacto ningún alertado
tuvo fondo, que es justo la condición (`n_sin_fondo == npix`) con que la vía nueva toma la rama vacía. La prueba
`tests/test_reemplazo_fondo_nulo_s192.py` lo comprueba sobre la pasada real 3933: el record del código del tag
`pre-s192-fondo-nulo` (`tests/datos_s192_fondo_nulo/pre_s192_3933.json`, armado con `armar_fixture_pre.py`),
transformado, es igual en claves, valores y orden al que da `procesar_grilla` de hoy.

## Ensayo en seco

`ensayo/informe.json`: corrida sin `--aplicar` sobre main en `77cb81540` (2026-11-20, después del merge de #1067),
con los records por carpeta y volcán y la VRP, los alertados y la clase que tenían. En un worktree desechable además se
aplicó: el `git diff` tocó sólo los archivos con objetivos y, dentro de ellos, sólo esos records; una segunda pasada no
encontró nada; y los 113 archivos de `tests/` que leen `data/mirova_equivalent`, `data/historia_34` o `data/sombra_34`
pasaron sobre ese estado aplicado (1659 pasan, 12 saltadas). Después se revirtió.

Tablero: `efecto_tablero.py` (salida en `efecto_tablero_salida.txt`) evalúa en node las funciones reales de
`frontend/index.html` sobre los records de `data/mirova_equivalent` antes y después. `data/historia_34` no la lee
ninguna página hoy (el tablero toma a los 34 de `data/sombra_34`).

**El ensayo se repite justo antes de aplicar**, sobre el main de ese momento: la tanda 7 de la historia de los 34 (run
44768057665) puede agregar records con fondo nulo, y el NRT no, porque desde #1065 escribe ya la forma nueva.

```bash
python experiments/_s192_fondo_nulo/reemplazo_fondo_nulo.py --informe experiments/_s192_fondo_nulo/ensayo/informe.json
```

## Aplicar (sólo con el sí de Nicolás, A45)

```bash
gh workflow run aplicar-reemplazo.yml -R MendozaVolcanic/VRP-chile --ref main -f confirmacion=si -f script=experiments/_s192_fondo_nulo/aplicar_fondo_nulo.sh -f "pruebas=tests/test_reemplazo_fondo_nulo_s192.py tests/test_via_fondo_nulo_s192.py tests/test_historia_34.py" -f tag=pre-s192-reemplazo-fondo-nulo -f "mensaje=S192: records MODIS de la via con fondo nulo pasan a escena no medida (fondo_no_estimado), sigue a #1065"
```

El informe de la aplicación queda en `aplicado/informe.json` (lo commitea el workflow junto con los datos).

## Lo que no hace

- Los records VIIRS con fondo nulo conservan su VRP (decisión de Nicolás), pero los guardados antes de #1065 no tienen
  la marca `alertados_sin_fondo` y su `t_bg_k` es 0,0 K (la fórmula vieja `L_bk / npix`). Marcarlos es otro reemplazo.
- No toca `regimen` ni `processed_utc`: el record no dice por sí solo que fue transformado; la traza es el tag
  defensivo, el commit del workflow y `aplicado/informe.json`.
