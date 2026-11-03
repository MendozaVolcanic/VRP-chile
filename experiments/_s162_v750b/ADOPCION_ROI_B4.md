# V750-B: adopción de la ROI B4 en `roi_v750` (2026-11-03)

## 1. Qué cambia

`pipeline/grillas_mirova.yaml`, clave `roi_v750`: Cordón Caulle (`PuyehueCordonCaulle`) y Tupungatito pasan de
`def` a `sens`. Los otros nueve Tier A siguen en `def`, y los 34 volcanes de la sombra (#932) también, sin cambios.
El comentario del archivo dice ahora qué brazo rige («Puesto por la lectura de V750-B: brazo B4»). El cambio lo
escribió `scripts/roi_v750b_a_grillas.py --brazo B4 --escribir`, no la mano.

**Como geólogo.** El código de MIROVA mira cada volcán en una ventana de 67 × 67 celdas de 750 m. Con su matriz de
ejemplo, sólo un cuadro de 7 × 7 al centro (unos 5 km de lado) se prueba con los umbrales sensibles de noche, y el
resto con los conservadores. En la mayoría de los volcanes el calor está en el cráter y ese cuadro basta. En Cordón
Caulle el calor que MIROVA reporta cae a 4,6 a 10,5 km del centro de la grilla, y en Tupungatito el cráter está a
unos 4 km del centro. Con el cuadro por defecto, el detector prueba esas zonas con el umbral conservador y calla
donde MIROVA alerta: con B0 se pierden 11 de 11 alertas protegidas de Cordón Caulle. B4 hace sensible toda la
región de 21 × 21 en esos dos volcanes y deja el resto como en el ejemplo.

## 2. Por qué B4 (lectura de V750-B)

Lector sellado de la adenda 3, run 41615021658 más el relanzamiento 41693265163, leído una vez el 2026-11-03.
Lectura, informes y verificador limpio en la rama `claude/s162-viirs750-2-918174`,
`experiments/_s162_v750b/r4/lectura_20261103/` (commits `70c5b2808`, `1c10db660`, `d7d15b450`):

- Compuerta abierta: los controles salieron verdes (nulo, K = producción, censo S159, negativo y positivo) y la
  cobertura alcanza (1 SIN DATO de 5.867, no protegida).
- Elegibles B1, B2, B3 y B4 (0 protegidas perdidas). Ninguno gana contra B1. Entre los que no son peores que B1, el
  orden de cercanía al `.m` del §6.3 pone primero a B4. Sin la regla N-3 da lo mismo.
- Verificador limpio (Fable): CONFIRMA. A4 sale CONFIRMADA EN PARTE sólo por una frase mía sobre B3, que no cambia
  la elección. Siete hallazgos, todos de gravedad 1.

## 3. §6.5 del pre-registro: B4 es fidelidad al `.m`, no un gate nuestro

B4 es una ROI distinta por volcán. MISSION excluye los gates por volcán cuando son nuestros (A85). Éste no lo es:
el propio código operacional de MIROVA lo declara. `experiments/_s158_d17_diseno/osf_codigo_mirova/
MIROVA_VIIRS750_hotspot_detection.m`, l. 120 a 125 (comentario del bloque de la matriz BOX, l. 105 a 125):

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
sensor, `docs/superpowers/specs/2026-10-24-programa-replica-por-sensor.md` en `loop/activo`, l. 458). Ésta es esa
excepción:

- **Sensor:** sólo VIIRS 750 (clave `roi_v750`; `roi_modis` y la ROI de VIIRS 375 no se tocan).
- **Commit:** el de este PR (se anota el sha del merge al mergear).
- **Quién lo lee:** sólo la vía «código MIROVA» de VIIRS 750 (`ENABLE_V750_CODIGO_MIROVA`). En producción
  (`mirova_equivalent`) la vía está **apagada**, comprobado con `pipeline.profile` el 2026-11-03: producción no
  cambia. La leen los perfiles `sombra_codigo_mirova` (11 Tier A, `.github/workflows/sombra-codigo-mirova.yml`,
  cron 15:00 UTC) y `sombra_34` (los 34, que siguen en `def`: no cambian).
- Tag defensivo sobre `main` antes del cambio: `pre-s173-roi-v750-b4` (= `82b55de0d`, A45).

## 5. La noche del cambio, para el lector de la sombra de V750-A

La sombra de los 11 de VIIRS 750 corre con B0 hasta el merge de este PR, y con B4 desde la primera corrida de
`sombra-codigo-mirova.yml` posterior al merge. Sólo cambian las pasadas VIIRS 750 de Cordón Caulle y Tupungatito; los
otros nueve volcanes dan el mismo resultado con B0 y con B4.

- **Al mergear**, anotar aquí y en el §11 de V750-A: el sha del merge, su hora UTC y la primera corrida de sombra con
  ese sha (su run id y qué noches procesó).
- El lector de la sombra separa las pasadas de Cordón Caulle y Tupungatito por la ROI con que se procesaron (antes o
  después de esa corrida, o por el sha de `main` que registra la corrida). No se mezclan en una misma métrica (A104).
- Si la sombra reprocesa noches anteriores al merge, esas noches quedan con B4 desde entonces: lo que decide es el
  sha con que corrió, no la fecha de la observación (lección S155: la marca va en los datos, no en el merge).
