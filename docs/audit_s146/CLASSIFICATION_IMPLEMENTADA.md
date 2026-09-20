# `classification`: el eje de referencia, implementado como post-proceso (S146)

> Todos los números de este informe salen de
> `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\scripts\clasificar_referencia.py --stats`
> y viven en
> `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s146_classification\distribucion.json`.
> El informe mismo lo escribe `experiments\_s146_classification\hacer_informe.py` leyendo ese JSON:
> ningún número está transcrito a mano (S91). Ventana **2026-09-01 a 2026-09-20**, los 11 Tier A, pasadas
> nocturnas. No cruza el cambio de régimen del 2026-08-28 23:00 UTC (A104).

## 1. El porqué, antes del cómo

De noche, sobre un volcán, pueden pasar dos cosas que en el dashboard se ven igual. Una: hay calor
que MIROVA, el sistema de referencia, también publicó. Otra: hay calor que sólo vemos nosotros. La
segunda no es sinónimo de error. El lago de lava de Villarrica, el campo fumarólico de Lastarria y
el lacolito de Cordón Caulle son calor real que MIROVA muchas veces no publica. S145 midió que
ninguna regla física separa eso de lo que no es volcánico sin destruir lo que MIROVA confirmó (la
mejor marcaba 397 de 414 confirmadas). Entonces lo honesto es rotular lo único que sí se sabe: **qué
hizo la referencia con esa pasada**. Eso es lo que se implementó, y nada más.

## 2. Qué se implementó

| archivo | qué hace |
|---|---|
| `scripts/clasificacion_referencia.py` | la lógica, importable. Llama a `banco_paridad.etiquetar` tal cual y le suma la pregunta "¿MIROVA alertó esa misma noche en otra pasada?" |
| `scripts/clasificar_referencia.py` | el script del job: ventana móvil (30 días por defecto, con piso en 2026-09-01), escribe un JSON por volcán |
| `data/clasificacion_referencia/<Volcan>.json` | la salida, 11 archivos. Indexada por `datetime_utc|sensor`, que es la clave de deduplicación de `pipeline/store.py` |
| `tests/test_clasificacion_referencia_s146.py` | 12 pruebas |

`scripts/banco_paridad.py` **no se movió ni se tocó**: ya vivía en `scripts/` y se importa limpio.

Los cinco valores, exactamente los del diseño aprobado (§5.2), con la lectura llana que acompaña a
cada uno dentro del JSON:

| valor | lectura para el geólogo |
|---|---|
| `mirova_confirmed` | Confirmado por MIROVA: publico alerta en esta misma pasada |
| `mirova_same_night` | Confirmado por MIROVA esa noche: publico alerta en otra pasada del mismo volcan |
| `mirova_silent` | Solo nuestro: MIROVA miro esta pasada y no publico nada |
| `mirova_saw_outside` | MIROVA vio calor fuera del limite del volcan: sin informacion sobre el crater |
| `no_reference` | Sin dato de referencia: MIROVA no listo esta pasada o su registro aun no llega |

Ninguno dice ni insinúa un juicio físico sobre la anomalía. `no_reference` es el SIN DATO
explícito: no es lo mismo que la referencia haya mirado y callado (`mirova_silent`) a que no haya
mirado, o a que su registro todavía no llegue.

Propiedades de la salida: claves ordenadas, el único float (`dist_ref_km`, sólo en
`mirova_saw_outside`) se redondea a 2 decimales al serializar, fin de línea LF, y **sin hora de
generación**, así que dos corridas sobre el mismo estado dan los mismos bytes. El script se niega a
escribir dentro de `data/mirova_equivalent/` (A47) y nunca abre esos archivos para escritura.

## 3. Supuestos que tomé (donde la especificación era ambigua)

1. **Se clasifican todas las pasadas nocturnas de la ventana, no sólo las publicadas.** El diseño
   contó sobre lo publicado, pero el pedido dice "cada record de la ventana". Publicar es cosa del
   dashboard y puede cambiar; el eje de referencia no depende de eso. Las tablas de abajo dan los
   dos denominadores.
2. **Precedencia**: la misma de `experiments/_s145_classification/sustrato_clasificacion.py`
   (`reparto`): misma pasada, después misma noche del volcán (cualquier sensor), después fuera de
   límite, después silencio, y el resto sin dato. La alerta de la misma noche manda sobre el
   silencio porque el evento es el mismo.
3. **`no_reference` hereda el `sin_info` del banco**, que es un poco más ancho que "MIROVA no listó
   la pasada": incluye la pasada que sólo aparece en el canal OCR como RUTINA, la RUTINA con VRP
   mayor que cero, y la RUTINA de una noche en que ese sensor tuvo un fuera de límite en otra pasada.
   En los tres casos lo correcto es no afirmar nada, y por eso la lectura llana dice "sin dato".
4. **Referencia "ya sincronizada en el repo"** = `latest_consolidado.csv` de la raíz (lo refresca
   `sync-mirova-csv.yml` cada hora) más `data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv`
   (semanal) más el respaldo del 2026-04-08. No se bajó nada. Consecuencia medida en §5.
5. **Las pasadas diurnas descartadas no reciben valor** (mismo filtro que el banco). El pipeline ya
   las rechaza, así que casi no existen en los JSON.
6. **Piso de la ventana en 2026-09-01**: si la ventana móvil pide una fecha anterior, el script
   la recorta y avisa. Lo que ya salió de la ventana se conserva en el archivo tal como quedó; lo
   que está dentro se recalcula entero en cada corrida.
7. **El nombre del campo queda como `valor` dentro de un archivo aparte**, no como
   `primary_cluster.classification` dentro del record: es lo que pide el límite de no escribir en
   `data/mirova_equivalent/`. `geo_class` no se tocó.

## 4. Distribución (2026-09-01 a 2026-09-20)

Referencia usada: consolidado hasta **2026-09-20 02:45:00** UTC, OCR hasta
**2026-09-14 06:42:01** UTC (huellas `35029c6189a95052` y `e15c02b67c321cea`).

### 4.1 Denominador: las 1050 pasadas que el dashboard PUBLICA

"Publica" es el predicado de `frontend/index.html` ejecutado con node (A97), sha
`24fba8a157`. De 2285 pasadas nocturnas se publican 1050
(46,0 %).

| sensor | confirmado, misma pasada | confirmado, misma noche | MIROVA miró y calló | MIROVA vio fuera | sin dato | total |
|---|---|---|---|---|---|---|
| MODIS | 1 | 24 | 26 | 0 | 1 | 52 |
| VIIRS375 | 128 | 166 | 323 | 15 | 169 | 801 |
| VIIRS750 | 13 | 72 | 91 | 0 | 21 | 197 |

| volcán | confirmado, misma pasada | confirmado, misma noche | MIROVA miró y calló | MIROVA vio fuera | sin dato | total |
|---|---|---|---|---|---|---|
| Chaiten | 7 | 20 | 52 | 1 | 23 | 103 |
| Copahue | 0 | 0 | 58 | 1 | 26 | 85 |
| Isluga | 31 | 47 | 10 | 1 | 7 | 96 |
| Lascar | 20 | 24 | 26 | 1 | 9 | 80 |
| Lastarria | 9 | 17 | 23 | 4 | 18 | 71 |
| Llaima | 0 | 0 | 60 | 0 | 24 | 84 |
| NevadosDeChillan | 4 | 11 | 49 | 0 | 17 | 81 |
| PlanchonPeteroa | 8 | 20 | 40 | 3 | 23 | 94 |
| PuyehueCordonCaulle | 36 | 73 | 44 | 1 | 17 | 171 |
| Tupungatito | 22 | 35 | 20 | 3 | 14 | 94 |
| Villarrica | 5 | 15 | 58 | 0 | 13 | 91 |

Lectura: de las 1050 publicadas, **404 (38,5 %) tienen una alerta de
MIROVA detrás** (misma pasada o misma noche), **440
(41,9 %) son pasadas que MIROVA miró sin publicar**, y
**191 (18,2 %) no tienen dato**. Copahue y Llaima
siguen sin una sola pasada confirmada en la ventana: si eso es calor real no publicado (El Agrio,
Pichi Llaima) o gradiente topográfico, este eje no lo dice, y no pretende decirlo.

### 4.2 Denominador: las 2285 pasadas nocturnas (publicadas o no)

| sensor | confirmado, misma pasada | confirmado, misma noche | MIROVA miró y calló | MIROVA vio fuera | sin dato | total |
|---|---|---|---|---|---|---|
| MODIS | 1 | 153 | 290 | 0 | 10 | 454 |
| VIIRS375 | 128 | 195 | 374 | 17 | 204 | 918 |
| VIIRS750 | 18 | 304 | 436 | 1 | 154 | 913 |

| volcán | confirmado, misma pasada | confirmado, misma noche | MIROVA miró y calló | MIROVA vio fuera | sin dato | total |
|---|---|---|---|---|---|---|
| Chaiten | 7 | 54 | 123 | 1 | 43 | 228 |
| Copahue | 0 | 0 | 159 | 1 | 51 | 211 |
| Isluga | 32 | 102 | 29 | 1 | 11 | 175 |
| Lascar | 20 | 75 | 70 | 1 | 17 | 183 |
| Lastarria | 9 | 61 | 81 | 5 | 32 | 188 |
| Llaima | 0 | 0 | 162 | 2 | 55 | 219 |
| NevadosDeChillan | 4 | 38 | 132 | 0 | 46 | 220 |
| PlanchonPeteroa | 8 | 56 | 103 | 3 | 37 | 207 |
| PuyehueCordonCaulle | 39 | 106 | 60 | 1 | 23 | 229 |
| Tupungatito | 22 | 110 | 51 | 3 | 18 | 204 |
| Villarrica | 6 | 50 | 130 | 0 | 35 | 221 |

Ojo al leer MODIS y VIIRS 750 acá: "misma noche" mira la noche del volcán con cualquier sensor, así
que puede venir de una alerta de VIIRS 375 y no de una propia (no medí cuántas).

## 5. Controles del instrumento

- **Reproduce el diseño al número.** Con la misma referencia que usó S145 (la copia bajada en
  `experiments/_s145_classification/_dl_referencia/`), el reparto de las publicadas da
  157 / 257 / 433 /
  15 / 188, total 1050: idéntico a la tabla de §5.2
  del diseño (157 / 257 / 433 / 15 / 188). Las etiquetas del banco también: `{'far_ref': 32, 'neg_limpio': 1433, 'pos': 162, 'sin_info': 658}`.
- **La diferencia con §4 es sólo la referencia, y es el fenómeno que el diseño anunció.** Con la
  referencia del repo salen 142 confirmadas en la misma pasada en vez de
  157, porque el OCR del repo termina el 2026-09-14. La
  etiqueta cambia con el tiempo: eso justifica la ventana móvil.
- **Mismo recorrido que el banco**: `True` (el cargador liviano
  del módulo, sin node, recorre exactamente las mismas 2285 pasadas que
  `banco_paridad.cargar_nuestros`). Identidad del predicado contra el guard S139:
  `True`.
- **Control positivo** (test): recorrido independiente desde el CSV, cada alerta del consolidado con
  record nuestro a 2 minutos recibe `mirova_confirmed`. **Instrumento muerto** (test): con la
  referencia vacía, todas las pasadas reales dan `no_reference`.
- **Mutación**: forzando que el sin dato caiga en `mirova_silent` fallan 3 pruebas; llevando la
  tolerancia del pareo a 0 s falla la del confirmado. Las pruebas fallan por lo que dicen medir.

## 6. Qué falta para que el operador lo VEA (no hecho, a propósito)

1. **Programarlo.** Propuesta de workflow, NO creado. Usa retry propio y no el grupo `push-main`,
   por la regla de concurrencia del proyecto (o grupo compartido, o retry propio, nunca los dos):

```yaml
name: clasificar-referencia
"on":
  schedule:
    - cron: "37 */6 * * *"
  workflow_dispatch: {}
permissions:
  contents: write
jobs:
  clasificar:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r requirements.txt
      - run: python scripts/clasificar_referencia.py --dias 30
      - name: commit con reintento
        run: |
          git config user.name "vrp-clasificacion-bot"
          git config user.email "noreply@github.com"
          git add data/clasificacion_referencia/
          git diff --cached --quiet && exit 0
          git commit -m "data(clasificacion): eje de referencia, ventana movil (auto)"
          for i in 1 2 3 4 5; do
            git pull --rebase origin main && git push origin HEAD:main && exit 0
            sleep $((i * 15))
          done
          exit 1
```

   Sólo toca `data/clasificacion_referencia/`, así que no compite por archivos con `nrt.yml`. Falta
   confirmar que `requirements.txt` trae lo que importa `auto_audit_weekly` (no lo verifiqué en un
   runner). Como el OCR del repo sólo se refresca con el auto audit semanal, conviene que este job,
   o `sync-mirova-csv.yml`, traiga también `registro_vrp_ocr.csv`; si no, las confirmaciones que
   dependen del OCR llegan con hasta una semana de atraso.
2. **Publicarlo con Pages.** `pages-deploy.yml` ya copia `data/` entero al sitio (`cp -r data _site/data`)
   y se dispara con cambios en `data/**`, así que los JSON quedarían servidos apenas se commiteen.
   No lo probé en un deploy real.
3. **Mostrarlo.** Las tres vistas live (`index.html`, `diario.html`, `mosaico.html`) tienen helpers
   duplicados, y hoy sólo `index.html` calcula `_mirova_confirmed` en el cliente. La decisión de
   reemplazar ese cálculo por la lectura de estos JSON (y replicarlo en las tres) es aparte.
4. **Ficha SDA.** Agregar este eje a `docs/FICHA_SDA_VRP_CHILE.md` cuando se despliegue. Hoy no está
   en producción, así que no lo toqué.
5. **`docs/MISSION.md`** todavía dice que `pc.classification` no existe; corregir esa frase es
   decisión del dueño.
6. El segundo eje del diseño (§5.4, "estado de base o cambio") no se implementó: no era parte del pedido.
