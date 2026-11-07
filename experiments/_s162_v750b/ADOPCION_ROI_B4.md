# V750-B: adopción de la ROI B4 en `roi_v750` (2026-11-03)

## 1. Qué cambia

`pipeline/grillas_mirova.yaml`, clave `roi_v750`: Cordón Caulle (`PuyehueCordonCaulle`) y Tupungatito pasan de
`def` a `sens`. Los otros nueve Tier A siguen en `def`, y los 34 volcanes de la sombra (#932) también, sin cambios.
El comentario del archivo dice ahora qué brazo rige («Puesto por la lectura de V750-B: brazo B4»). El cambio lo
escribió `scripts/roi_v750b_a_grillas.py --brazo B4 --escribir`, no la mano.

**Como geólogo.** El código de MIROVA mira cada volcán en una ventana de 67 × 67 celdas de 750 m. Con su matriz de
ejemplo, sólo un cuadro de 7 × 7 al centro (unos 5 km de lado) se prueba con los umbrales sensibles de noche, y el
resto con los conservadores. En la mayoría de los volcanes el calor está en el cráter y ese cuadro basta. En Cordón
Caulle el calor que MIROVA reporta cae a 4,6 a 10,5 km del centro de la grilla (pre-registro de V750-B, §8), y en
Tupungatito el cráter está a 4,9 km del centro. Con el cuadro por defecto, el detector prueba esas zonas con el umbral conservador y calla
donde MIROVA alerta: con B0 se pierden 11 de 11 alertas protegidas de Cordón Caulle. B4 hace sensible toda la
región de 21 × 21 en esos dos volcanes y deja el resto como en el ejemplo. Ese cuadro llega a 7,9 km del centro, así
que en Cordón Caulle no cubre todo el rango de 4,6 a 10,5 km; en la lectura bastó para publicar las 11 protegidas.

## 2. Por qué B4 (lectura de V750-B)

Lector sellado de la adenda 3, run 41615021658 más el relanzamiento 41693265163, leído una vez el 2026-11-03.
Lectura, informes y verificador limpio en la rama `claude/s162-viirs750-2-918174`,
`experiments/_s162_v750b/r4/lectura_20261103/` (commits `70c5b2808`, `1c10db660`, `d7d15b450`):

- Compuerta abierta: los controles salieron verdes (nulo, K = producción, censo S159, negativo y positivo) y la
  cobertura alcanza (1 SIN DATO de 5.867, no protegida).
- Elegibles B1, B2, B3 y B4 (0 protegidas perdidas). Ninguno gana contra B1. Entre los que no son peores que B1, el
  orden de cercanía al `.m` del §6.3 pone primero a B4. Sin la regla N-3 da lo mismo.
- Verificador limpio de la lectura (subagente Fable 5.1, effort high; su informe no enuncia un veredicto global):
  A1, A2, A3, A5 y A6 CONFIRMADAS y A4 CONFIRMADA EN PARTE, sólo por una frase mía sobre B3, que no cambia la
  elección. Siete hallazgos, todos de gravedad 1.

## 3. §6.5 del pre-registro: B4 es fidelidad al `.m`, no un gate nuestro

B4 es una ROI distinta por volcán. MISSION excluye los gates por volcán cuando son nuestros (A85). Éste no lo es:
el propio código operacional de MIROVA lo declara. `experiments/_s158_d17_diseno/osf_codigo_mirova/
MIROVA_VIIRS750_hotspot_detection.m`, l. 120 a 123 (dentro del comentario de la matriz BOX, l. 105 a 125):

> «This BOX configuration represents the default spatial arrangement used by the algorithm. For specific volcanoes,
> ROI1 and ROI2 can be shifted, reshaped or resized to better match the expected location and spatial extent of
> thermal anomalies.»

O sea, la matriz de ejemplo (B0) es la configuración por defecto, y MIROVA ajusta la ROI por volcán. B4 es el ajuste
mínimo (sólo dos volcanes) que reproduce lo que MIROVA publica en ellos, elegido por la regla escrita antes de los
datos. Lo que no sabemos es la ROI exacta que usa MIROVA en esos dos volcanes: la matriz del OSF es un ejemplo. B4
es nuestra mejor reconstrucción medida, no la copia de su configuración.

**Confirmación de Nicolás**, relayada por la coordinadora S173 el 2026-11-03, textual: «Sí, confirmo B4». Vale como
la confirmación del §6.5 y como la frase para aplicar B4 en la rama de la ROI y abrir el PR. **El merge a `main` pide
otra frase de Nicolás.**

## 4. Excepción al congelamiento y alcance

Durante la sombra de V750-A, `pipeline/` está congelado salvo la ROI de VIIRS 750 (decisión de Nicolás, programa por
sensor, `docs/superpowers/specs/2026-10-24-programa-replica-por-sensor.md` en `loop/activo`, sección desde la l. 452; la
excepción está en las l. 460 y 461). Ésta es esa
excepción:

- **Sensor:** sólo VIIRS 750 (clave `roi_v750`; `roi_modis` y la ROI de VIIRS 375 no se tocan).
- **Commit:** el de este PR (se anota el sha del merge al mergear).
- **Quién lo lee:** sólo la vía «código MIROVA» de VIIRS 750 (`ENABLE_V750_CODIGO_MIROVA`). En producción
  (`mirova_equivalent`) la vía está **apagada**, comprobado con `pipeline.profile` el 2026-11-03: producción no
  cambia. La leen los perfiles `sombra_codigo_mirova` (11 Tier A, `.github/workflows/sombra-codigo-mirova.yml`,
  cron 15:00 UTC) y `sombra_34` (los 34, que siguen en `def`: no cambian). Producción sí abre el archivo desde la
  vía MODIS, pero lee la clave `roi_modis`, que no existe y vale `def`: este cambio no la toca.
- Tag defensivo sobre `main` antes del cambio: `pre-s173-roi-v750-b4` (= `82b55de0d`, A45).

## 5. La noche del cambio, para el lector de la sombra de V750-A

La sombra de los 11 de VIIRS 750 corre con B0 hasta el merge de este PR, y con B4 desde la primera corrida de
`sombra-codigo-mirova.yml` posterior al merge. Sólo cambian las pasadas VIIRS 750 de Cordón Caulle y Tupungatito; los
otros nueve volcanes dan el mismo resultado con B0 y con B4.

- **Al mergear**, anotar aquí, en el §11 de V750-A y en `tasks/LOOP_OBJETIVOS.md` §6 de `loop/activo` (lo pide el
  §12.6 del programa por sensor): el sha del merge, su hora UTC y la primera corrida de sombra con
  ese sha (su run id y qué noches procesó).
- ⚠️ **S173, en curso (PR en borrador, rama `claude/s173-vpr939-03`, sin mergear)**: `evaluar_v750a.py --fase sombra`
  lee la ROI y el sha de cada record de P, exige `--roi-brazo` (sin él cierra la compuerta), saca de la lectura las
  pasadas de otra ROI y, con `--sha-desde`, las de código anterior; LECTURA LR1 de `LECTURAS_EVALUAR_V750A.md`. Hasta
  el merge vale el texto que sigue. S174 (segunda vuelta, VPR945, LECTURA LR2): la sombra no dice CUMPLE antes
  de las 4 semanas del §4.3 (PROVISORIO, salida 4; el reloj parte del corte con `--sha-desde`), un volcán fuera
  del mapa de ROI es SIN DATO y `--sha-desde` exige un sha. S174 (tercera vuelta, VPR945-R2, LECTURA LR3):
  `--sha-desde` es obligatorio en la sombra; la lectura empieza en lo más tardío entre el 2026-11-03 y la hora del
  commit del corte (ya no hay reloj desde el corte: las pasadas anteriores no se leen); CUMPLE exige además 14 noches
  distintas (decisión de Nicolás); una pasada de otra ROI con código posterior al corte cierra la compuerta, así que
  la lectura con B4 tiene que cortar en el merge de #939 (`58edb9788`) o después. S174 (cuarta vuelta, VPR945-R3,
  LECTURA LR3): las 14 noches van repartidas, 7 en cada mitad del lapso, y Cordón Caulle y Tupungatito (los que B4
  traduce distinto de B0) piden cada uno ese reparto sobre sus pasadas leídas, impresas por volcán (con 0 pasadas,
  PROVISORIO); `--sha-desde` es el commit de merge (`58edb9788`), no el sha de la primera corrida de sombra.
  ⚠️ S174 (quinta vuelta, VPR945-R4, LECTURA LR3; Nicolás: «Ventana fija, una vuelta»): el reparto de 7 y 7 por
  mitad del lapso de la cuarta vuelta queda retirado. La ventana es fija: de lo más tardío entre el 2026-11-03 y la
  hora del commit del corte, 28 días (con `58edb9788`, del 2026-11-05 03:23 al 2026-12-03 03:23 UTC), en 4 semanas
  fijas; CUMPLE exige que la fecha de referencia («ahora», `--ahora` o el reloj de la máquina) haya llegado al fin y
  5 noches en cada semana (y 14 en total) en el conjunto y en Cordón Caulle y Tupungatito; lo posterior al fin o a
  «ahora» no se lee y se cuenta como «fuera de ventana».
  ⚠️ S174 (sexta vuelta, VPR945-R5, LECTURA LR3; decisión de Nicolás del 2026-11-06, «Sí, sexta vuelta»): además,
  cada uno de los otros nueve volcanes (ROI igual a B0) pide 14 noches distintas en la ventana, sin mínimo semanal
  (antes sólo se imprimían); cada noche cuenta una sola vez, en la semana de su primera pasada; `--ahora` acepta ISO
  con zona y la convierte a UTC.
  Texto original:
- **Pendiente, no hecho**: el lector de la sombra de V750-A todavía no separa por ROI (ningún script de
  `experiments/_s162_v750a/` lee `regimen.codigo_sha` ni `diag_codigo_mirova.roi`; VPR939-03 del verificador del
  PR). Los insumos ya están en cada record (`pipeline/store.py` l. 89 a 93, `pipeline/mirova_v750_codigo.py` l. 708).
  Hay que agregarlo antes de leer la sombra: las pasadas de Cordón Caulle y Tupungatito con B0 y con B4 no se
  mezclan en una misma métrica (A104).
- Si el PR se mergea antes de la primera corrida de la sombra de los 11 (cron 15:00 UTC; al 2026-11-03 19:29 UTC
  todavía no había datos de sombra en `main`), toda la sombra de VIIRS 750 corre con B4 y no hay noche de cambio.
- Si la sombra reprocesa noches anteriores al merge, esas noches quedan con B4 desde entonces: lo que decide es el
  sha con que corrió, no la fecha de la observación (lección S155: la marca va en los datos, no en el merge).
