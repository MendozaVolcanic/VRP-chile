# Encendido de la vía «código MIROVA» en MODIS: diseño de los dos PR (S172)

Fecha: 2026-11-01. Autor: coordinadora S172. Estado: diseño aprobado para preparar (Nicolás, 2026-11-01: «Sí,
prepáralo» y «lo que recomendabas antes también hazlo»). Nada se mergea sin la frase de Nicolás; el PR B pide además su
sí de A45 con la pre-autorización de la reversión. Tag defensivo: `pre-s171-adopcion-modd` (`d3cd0b2ae`, empujado).

Regla que este diseño implementa: `experiments/_s171_modd_adopcion/REGLA_REVERSION_MODD_BORRADOR.md` (rama
`loop/activo`), sobre todo §3 (guardia), §4 (reversión e investigación) y §5 (lista del PR). Modelo: la adopción de K,
`experiments/_s151_prereg_fk_11/REGLA_ADOPCION.md` paso 9, y su vigilancia (`scripts/vigilancia_sombra.py`,
`.github/workflows/vigilancia-sombra.yml`, `frontend/cambio_detector.js`, `scripts/auto_audit_weekly.py` §S156).

## Por qué, como geólogo

MODIS con K pierde más de un tercio de las noches en que MIROVA alerta (recall 62,5 % en 16 noches, audit del
2026-10-26, #915) y en Chillán, con el domo activo, marca 0,56 de la magnitud de MIROVA. La vía que corre el código
publicado por MIROVA ganó el A/B pre-registrado de MOD-D (tag `s170-modd-f4-lectura`). Nicolás decidió no esperar la
sombra de 28 noches: se enciende antes y K queda corriendo aparte como guardia. Si la vía calla una alerta protegida que
K habría publicado, se revierte el mismo día.

## Decisión de diseño 1: dos PR, para que la reversión sea limpia

La reversión pre-autorizada es un `git revert`. En S157 el revert de K ya no salía limpio (chocaba en tres archivos).
Por eso el encendido se parte:

- **PR A (infraestructura, inerte con el flag apagado)**: la guardia K, su vigilancia, el audit por detector y la marca
  del tablero. Con el flag apagado no cambia ningún record de producción y la marca del tablero no dibuja nada (no hay
  records de la vía en `data/mirova_equivalent/`). Se puede mergear antes y dejar correr la guardia unos días como
  **identidad**: mientras producción siga en K, guardia y producción tienen que publicar lo mismo en MODIS. Ese es el
  nulo medido de la guardia (A110), gratis.
- **PR B (el encendido, lo único que se revierte)**: la línea del flag, las pruebas que fijan su valor, la ficha SDA y
  las marcas A113. Revertirlo deja la infraestructura y la guardia corriendo.

## Decisión de diseño 2: la guardia, perfil y workflow nuevos

`pipeline/profiles/guardia_k_modis.yaml`: `extends: mirova_equivalent`, `thresholds: enable_modis_codigo_mirova:
false`, sólo MODIS (`sensors: modis: true, viirs_375: false, viirs_750: false`), `output: data_subdir: guardia_k_modis`
(A47). Workflow nuevo `.github/workflows/guardia-k-modis.yml`, calcado de `sombra-codigo-mirova.yml` (matriz de los 11
Tier A, sólo `EARTHDATA_TOKEN` con falla inmediata si viene vacío (A71), `"on":` entre comillas (A43), grupo de
concurrencia propio, push con reintento, revisión de cobertura). Por qué no editar la sombra: la aserción de la l. 110
del workflow de la sombra se compara como texto en el S8 del lector de V375-E y marcaría régimen; un perfil y un
workflow nuevos no están en `PERFILES_REGIMEN` ni en `RUTAS_REGIMEN` (re-sellado S172, rama
`claude/s172-v375e-relector`).

## Decisión de diseño 3: la vigilancia de la guardia, un script nuevo

`scripts/vigilancia_guardia_modis.py`, que reutiliza por import las funciones de `scripts/vigilancia_sombra.py` sin
modificar ese archivo (vigila K, y su plazo de 120 días corre hasta ~2026-02-15). Compara cada día, en MODIS: producción
(la vía) contra la guardia (K) contra MIROVA. Disparadores, de §4 de la regla: reversión candidata (alerta protegida A,
1 MW o más, regla SN de D-9, que MIROVA publica, la guardia publica y producción calla); investigación (i) Muy Bajo
perdidas, cota 2; (ii) sobre-publicación en negativos limpios, cota 3; (iii) pasadas que la guardia registra y
producción no (descarte de borde 171-01), contadas por semana; vigilancia ciega (sin datos frescos de la guardia o de
producción). Plazo: 29 protegidas A nocturnas de MODIS vistas en la guardia o 120 días desde el encendido; la fecha del
encendido sale de los datos (primer record MODIS de producción con `via_codigo_mirova: true`), no de una constante que
alguien tiene que llenar. Corre por un workflow propio enganchado al de la guardia (`workflow_run`) con un cron de
respaldo, como `vigilancia-sombra.yml`. El workflow no revierte: abre el issue.

## Decisión de diseño 4: el audit semanal, un detector más

`scripts/auto_audit_weekly.py` clasifica hoy «K» a todo record con `codigo_sha` (`_detector`, docstring S156). Tras el
encendido, los records MODIS de la vía también traen `codigo_sha` y se contarían como K. Se agrega el detector
`VIA_MODIS` para los records MODIS con `via_codigo_mirova: true`; en MODIS decide el detector vigente con la misma regla
de S156 (cada detector se informa entero, sólo el vigente decide los flags). **Las bandas no se recalibran** antes de ver
datos (A115 y §3b de la guía de auditorías: un umbral elegido después del dato no es pre-registro); se acepta que el
issue semanal salte y se anota en #915.

## Decisión de diseño 5: la marca del tablero, desde los datos

`frontend/cambio_detector.js` (un solo lugar, A102) suma una segunda marca, sólo en las series de MODIS: línea vertical y
aviso desde la primera pasada MODIS con `via_codigo_mirova: true`. Sin records de la vía no dibuja nada. El aviso dice,
en lenguaje del operador, que desde esa fecha la magnitud de MODIS sube y aparecen alertas que K callaba, y que en
Chillán ese escalón no es «la erupción crece».

## Lo que no entra

Los tres flags de MxD03 (van aparte, con su A/B, después del encendido). VIIRS 375 y VIIRS 750 de producción. Ningún
reproceso histórico: la vía corre desde el merge del PR B hacia adelante.

## Pruebas que cada pieza trae (con su rojo)

Perfil de la guardia leído desde `pipeline.profile` (A89); aserción del workflow; clasificación del detector en el
audit con records sintéticos; marca del tablero con y sin records de la vía (node); vigilancia de la guardia con
escenas sintéticas: una protegida que la guardia publica y producción calla dispara, una que las dos publican no, una
guardia sin datos frescos da vigilancia ciega. Cada prueba nueva se ve en rojo antes del verde.
