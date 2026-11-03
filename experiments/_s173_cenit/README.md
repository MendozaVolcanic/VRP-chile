# S173: qué pieza corrige la caída de magnitud con el cenit en Nevados de Chillán

Pedido de Nicolás (2026-11-02): las pruebas del ángulo cenital que el auditor de S172 dejó pendientes
(`experiments/_s172_chillan/auditor/INFORME.md` §10), en los tres sensores. Tres investigadores (Opus) y un
verificador limpio (Fable) por sensor. Los informes originales viven en `C:/Users/nmend/vrp-wt/s173_cenit/`; acá
están copiados sin las copias del repo ni los JSON de datos de más de 1,5 MB.

Ojo con el nombre: los encargos llamaron a D25 «geometría del borde del barrido». Es un error del coordinador. En el
catálogo D25 es el fondo de anillo regional con recorte a cero (`docs/MIROVA_DIVERGENCES.md`).

## Resultado, ya pasado por el verificador

| sensor | qué cae con el cenit | pieza | estado |
|---|---|---|---|
| VIIRS 750 | K (MIROVA plano) | fondo de anillo de K en la grilla; sin remuestreo queda 0,587 de la caída logarítmica | fondo CONFIRMADO EN PARTE; área/remuestreo SOSPECHA (pasa la condición necesaria del ATBD) |
| VIIRS 375 | K (0,745 / 0,481, 66 pares); V375-E no (0,92 / 1,00, 27) | sin aislar: no existe ablación por pieza | D17 SOSPECHA, en tensión con la tarea 1.14 §3.2 (gravedad 3) |
| MODIS | K; la vía no (producción 2026-11-02: 1,19 y 1,11 a 41° y 52°, n 2) | el recorte a cero cuando ninguna celda supera la mediana del anillo (5 de 10 oblicuas, 0 de 6 bajo 30°); D17 no extraíble del lote S162 (cenit y volcán confundidos) | CONFIRMADO EN PARTE |

## Segunda tanda: Tupungatito (VIIRS 375) y PCC (VIIRS 750), con verificador limpio

Pregunta de Nicolás: el código de MIROVA es uno por sensor, ¿el arreglo de Chillán no debería servir para todos? La
pregunta que decide es si la vía lleva a cada volcán cerca de 1.

| volcán | K (bajo / sobre 30°) | la vía | pieza | estado |
|---|---|---|---|---|
| Tupungatito V375 | 0,43 / 0,24 (168 pares) | V375-E 1,01 / 1,02 (23 pares, representativos de los 168) | nivel del fondo de anillo de K, 3 a 11 K más tibio que la cumbre (mediana 6,86 K); el recorte a cero casi no actúa | CONFIRMADA (pendiente de la vía: sin evidencia, n 23) |
| PCC V750 | 0,571 / 0,117 con ceros (53 alertas) | con la ROI de hoy (`def`, B0): 0 de 72 pasadas publicadas, pierde las 8 protegidas; con B1, B2, B3 o B5: 0,96 a 1,00 en los dos tramos, 0 protegidas perdidas | fondo de anillo de K (3,6 K más tibio que el fondo local; el lacolito sobresale 4,7 K) | CONFIRMADA EN PARTE |

Para la sesión de V750-B (urgente): en PCC la ROI `def` de `pipeline/grillas_mirova.yaml` deja la vía muda (control
positivo: una fuente sintética sí alerta con `def`). Y VPCC750-01 (gravedad 3): el oráculo de S162
(`oraculo_ablacion.py`) interpola el fondo con la Delaunay de scipy sin perturbar; la vía de producción usa la
triangulación perturbada que iguala a MATLAB. En 11 de 27 pasadas de PCC la vía da 1,3 a 40 % más VRP: toda lectura de
V750-B o V750-C hecha con el oráculo o el runner N hereda esa diferencia. Además el anillo del oráculo va de inner a 25
km, no de 5 a 25 (CPCC750-05).

Tupungatito, matices del verificador: dos de las 11 alertas que K no publica son protegidas por la regla oficial
(2,51 y 1,86 MW), pero son fuentes a 9 y 25 km atribuidas por el OCR con una imagen de 20 a 25 días después (A119); 2
de 168 pares comparan objetos distintos (A46). Seguimiento: VIIRS 750 en Tupungatito, K deja sin publicar 12 de 14
alertas (no medido).

## Seguimientos abiertos

- VMODIS-01 (gravedad 3): el arnés del PR #937 nunca llama a `auth()`; las 27 pasadas saldrían sin bajar. Corregir
  antes de pedir el merge.
- S1 de `ver_modis/` (gravedad 3): la regla de cirrus del tablero (`frontend/index.html`, `t_max` bajo 273,15 K y más
  de 10 MW) puede ocultar alertas reales de la vía en pasadas oblicuas; una ya cayó (2026-10-01 08:35, 11,44 MW).
  `frontend/` necesita tag y sí de Nicolás (A45).
- VV750-01 a 07 y VV375-01 a 06: defectos de instrumento de gravedad 1 a 2 (ventana efectiva de 12 noches en V750,
  controles débiles, una pasada topada por D9).
- La sombra de V375-E está vacía por diseño hasta el 2026-11-03 (`scripts/ventana_sombra.py`, `FECHA_MINIMA`).

## Tercera tanda: ablación por pieza en MODIS (run 41588951267, PR #937)

Corrida del 2026-11-03 06:17 UTC sobre `main` `f4ec1061d`: 27 de 27 pasadas, sin errores. Datos y lectura en
`ablacion_modis/` (`leer.py` y `leer.out`; los recortes `nativos/*.npz` quedan en D:/vrp-trabajo/temporales/s173_aud/ablacion_modis_run/).
Controles: K igual campo a campo al record guardado en 27 de 27; V0 igual a V en 27 de 27.

| brazo | bajo 30° (n 10) | sobre 30° (n 17) | Spearman con el cenit |
|---|---|---|---|
| K | 0,678 | 0,137 | -0,90 |
| V (la vía) | 0,947 | 1,054 | +0,25 |
| FA (fondo de K) | 0,488 | 0,351 | -0,38 |
| NAT (sin remuestreo) | 0,960 | 0,460 | -0,93 |
| G5 (geolocalización de 5 km) | 0,985 | 0,415 | -0,75 |
| NAT_AREA | 1,145 | 1,387 | +0,22 |

Verificador limpio (Fable, `ver_ablmodis/INFORME.md`): reproduce el JSON desde los recortes nativos con `piezas.py`
de `f4ec1061d` en 27 de 27; los números de la tabla, CONFIRMADOS; se repiten dentro de Terra y de Aqua, sin confusor
de fecha. Lo que cambia en la lectura:

- VABLMODIS-01 (gravedad 4): «la pieza es el remuestreo», CONFIRMADA EN PARTE. NAT no usa la geolocalización de 5 km
  (no comparten causa), pero G5 también hunde la razón: la geolocalización de K corre el píxel del cráter 1,5 km bajo
  30° y 2,8 km sobre 30° (máximo 6,5; Spearman +0,81 con el cenit) y saca el cúmulo de la caja en 9 de 27. En MODIS
  la caída oblicua la arreglan dos piezas de la vía, el remuestreo y la geolocalización de 1 km. «Al revés que en
  VIIRS 750»: SIN EVIDENCIA, no se midió.
- VABLMODIS-02 (gravedad 3): el fondo de K baja la magnitud parejo (sin ceros, 0,488 / 0,471), pero en 6 de 17
  pasadas oblicuas (0 de 10 bajo 30°) recorta la magnitud a cero con la detección intacta, y ahí están los 5 ceros de
  K. En PUBLICACIÓN el fondo sí hace la caída.
- VABLMODIS-04: RN no es neutro (Spearman +0,50 fuera del nulo).
- VABLMODIS-03 (gravedad 2): `registros_iguales` no puede dar verdadero en el arnés (`regimen.codigo_sha` = GITHUB_SHA);
  el control vale campo a campo.
- VABLMODIS-05 (gravedad 3): 7 de 27 records de la vía tienen `t_max_k` bajo 273,15 K, todos con cenit de 35° o más;
  una alerta real de la vía sobre 10 MW se ocultaría en el tablero como cirrus (la regla S1, ya anotada arriba).
