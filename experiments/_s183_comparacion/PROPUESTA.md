# S183: comparar la vía «código MIROVA», K y MIROVA en los 11 Tier A

Pedido de Nicolás (2026-11-13): que sea fácil comparar los 11 volcanes contra MIROVA para asegurarnos de que la vía nueva
es la más fiable. Fase 1 (medida) y fase 2 (propuesta). **Nada construido en el tablero: espera visto bueno.**

## Qué había

- `frontend/comparacion.html` (preview S115): histograma de distancia, dispersión 1:1 y extensión de Cordón Caulle. Lee el
  CSV de MIROVA y la serie de producción; no distingue detector ni da recall o precisión.
- Pestaña «Comparar con MIROVA» de cada volcán en `index.html` y `diario.html`: VRP nuestro contra MIROVA en el tiempo,
  un volcán a la vez y sólo con producción (hoy, la vía).
- Vigilancias de las guardias (`scripts/vigilancia_guardia_modis.py`, `scripts/vigilancia_guardia_viirs.py`): cada día
  buscan alertas protegidas que la vía calla y K publica. Están en VERDE, pero no dicen cuál detector se parece más a
  MIROVA en conjunto.
- `scripts/banco_paridad.py`: recall en positivos y publicación en negativos limpios, sólo para producción.
- El texto de métricas de `index.html` (línea 544) avisa que sus números son de julio de 2026: el tablero no tiene
  métricas vigentes de la vía.

## Fase 1: la medida

`medir_via_k_mirova.py` importa el etiquetado y el predicado del tablero de `banco_paridad.py` (node sobre
`frontend/index.html`) y compara los dos detectores sobre las mismas pasadas. Tablas en `RESUMEN_TABLAS.md` (las genera
`resumen.py` desde `salida/via_k_mirova.json`; ningún número escrito a mano). Referencia bajada del remoto de Mirova-v1
(`--remoto`): el snapshot del repo lo refresca sólo el auto-audit semanal y estaba en el 2026-11-09.

Lectura (los números, en `RESUMEN_TABLAS.md`):

1. **En los tres sensores la vía se parece más a MIROVA que K**, en la historia (marzo a octubre de 2026) y desde la
   adopción: más alertas de MIROVA publicadas, menos falsas alarmas en noches que MIROVA miró sin ver nada, y un VRP que
   en la mediana es el de MIROVA (cociente 1,00), mientras K entrega cerca de la mitad.
2. **Alertas protegidas.** Con la tabla de MIROVA sola, la vía no pierde ninguna en ningún sensor ni ventana; K pierde
   las de Nevados de Chillán MODIS de octubre y noviembre y la de Cordón Caulle VIIRS 750 del 2026-10-10.
3. **Las 15 protegidas VIIRS 375 que sólo K publica** aparecen sólo al sumar el OCR. Las 15 son filas sólo-OCR anteriores
   al 2026-10-09; en todas, el foco más fuerte de la vía está a 13 a 28 km del centro de MIROVA con casi el mismo VRP que
   MIROVA reporta. Lectura: MIROVA midió ese foco lejano y la clase «alerta» la puso el OCR leyendo la imagen de otra
   pasada (falla conocida de Mirova-v1, arreglada el 2026-10-09 en Mirova-v1#20). K publicaba ahí una señal de cumbre
   10 a 100 veces más débil que la de MIROVA: coincidió en el sí, no en lo que MIROVA vio. 11 de 15 son Suomi NPP, el
   satélite que nombra el hito; en las 4 de NOAA-21 el patrón es el mismo, pero el mecanismo queda SIN VERIFICAR.
4. **Cobertura.** En la historia ninguna alerta de MIROVA se esconde en pasadas que un detector tiene y el otro no. Desde
   la adopción sí hay alertas en pasadas de producción sin record en la guardia, que quedan fuera de la comparación. Las
   protegidas entre ellas son todas del 2026-11-13 (Nevados de Chillán y Cordón Caulle), día que la guardia aún no
   procesa, y la vía las publica todas (detalle en `salida/via_k_mirova.json`, clave `sin_par_via`). A la guardia VIIRS
   además le faltan unas pocas pasadas del 4, 7 y 12 de noviembre: seguimiento aparte, SIN INVESTIGAR.

Límites: la historia de la vía es un reproceso de S181 con el código de hoy y algunas decisiones de la vía (región sensible
de VIIRS 750, descarte de borde) se tomaron mirando esta misma historia, así que puede haber algo de optimismo a su favor.
La ventana desde la adopción es corta (12 días en MODIS, 3 en VIIRS). El nulo de las guardias (K de la guardia igual a K
de producción antes del reemplazo) está sellado en `experiments/_s181_guardias_reemplazo/nulo_sellado.json`.

## Fase 2: la vista propuesta

Maqueta con los números reales: `maqueta/maqueta_comparacion.html` (la genera `maqueta/generar_maqueta.py`).

Una pestaña nueva, primera de `comparacion.html` («Vía, K y MIROVA»), sin tocar las tres de S115 ni `index.html`:

1. **Selector de referencia**: tabla de MIROVA (por defecto, lo más creíble) o tabla más OCR. **Selector de ventana**:
   historia, desde la adopción, VIIRS con guardia.
2. **Una tarjeta por sensor** con la vía y K lado a lado: alertas de MIROVA publicadas, silencios, falsas alarmas,
   precisión, protegidas perdidas y VRP nuestro sobre MIROVA; resaltado el mejor.
3. **Grilla volcán por sensor**: alertas publicadas y falsas alarmas de cada detector.
4. **Lista de las protegidas en desacuerdo**, una por fila, con la distancia y el VRP de cada lado, para leerlas una a una.
5. **(Por construir, no está en la maqueta)** franja por noche de cada volcán: tres filas (MIROVA, vía, K) con un punto por
   noche-satélite, para ver de un vistazo dónde se separan; y la lista completa de noches en desacuerdo, no sólo las
   protegidas.

Datos: un JSON que escribe el medidor. La historia de K está fija (el tag); lo de después de la adopción crece cada día con
la guardia. Propuesta: correrlo una vez al día dentro del workflow de la vigilancia de las guardias y commitear
`data/audit_continuous/comparacion_via_k.json` (es auditoría, no datos de detección). La página no recalcula nada.

## Decisiones para Nicolás

1. ¿Va como pestaña nueva de `comparacion.html` (recomendado) o en otra parte?
2. ¿Se refresca a diario en el workflow de la guardia (recomendado) o a mano?
3. ¿Se suma la franja por noche (punto 5) en esta misma entrega?
