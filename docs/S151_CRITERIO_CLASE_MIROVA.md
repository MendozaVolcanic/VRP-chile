# Qué es una "alerta protegida" en el criterio de victoria (tarea 0.2 del loop)

> Escrito 2026-10-14 por el loop autónomo (tarea 0.2 de `tasks/LOOP_OBJETIVOS.md`). Script:
> `scripts/clase_mirova.py`. Tests y control: `tests/test_clase_mirova_s151.py`.

## 1. La pregunta

El criterio que Nicolás fijó el 2026-10-13 para la réplica dice: no se acepta ningún cambio que pierda una
alerta que MIROVA clasifique de "Bajo" para arriba; dentro de "Muy Bajo", una alerta perdida y una
publicación de más pesan igual. Para usarlo hay que saber qué es esa clase, porque la columna
`Clasificacion Mirova` del CSV trae "Bajo" de 0,04 MW y "Muy Bajo" de 0,99 MW, y una clase de intensidad
que no ordena la intensidad no sirve de umbral.

La hipótesis del plan era que la columna guardaba el nivel de la página del volcán (un agregado de días) y
no el de la pasada. **Quedó refutada**, por dos caminos independientes.

## 2. Lo que se encontró

**La columna no la escribe MIROVA.** La calcula el scraper de Mirova-v1 desde el VRP de la pasada
(`volcanes.py:63`, llamada en `scraper.py:156` y en `scraper_ocr.py`), con cortes en 1, 10, 100 y
1.000 MW. Hasta junio de 2026 los dos scrapers usaban escalas distintas (lo dice el propio docstring:
"unificado 2026-06") y las filas viejas nunca se recalcularon. Esto ya lo había encontrado la auditoría
S139 (`docs/audit_s139/EJE_1_semantica_etiquetas_referencia.md`, H110), pero no llegó al plan del loop.

Coherencia de la columna con la clase recalculada desde el VRP, sólo alertas (`scripts/clase_mirova.py`,
snapshot del 2026-10-14):

| canal | incoherente | coherente al 100 % desde |
|---|---|---|
| consolidado | 17 de 69 alertas de enero ("Bajo" bajo 1 MW) | febrero de 2026 |
| OCR | 12 a 130 por mes de enero a junio (escala retirada, con clase "Medio") | julio de 2026 |

**Los cortes son los de MIROVA.** Coppola et al. 2016a (Geological Society Special Publication 426, figura
11, p. 16 del PDF `documentacion/sp426.5.pdf`, leída sobre la página renderizada a imagen): el color del
recuadro de anomalía del sitio se fija según la escala Low bajo 1 MW, Moderate de 1 a 10, High de 10 a
100, Very High de 100 a 1.000 y Extreme de 1.000 a 10.000 MW. Los cortes coinciden con los del scraper,
pero **los nombres del paper están corridos un nivel** respecto de los del sitio actual.

**El banner de MIROVA de hoy es por pasada y usa esos cortes.** El OCR lee desde la versión 30 (agosto de
2026) el texto del banner de la imagen, `Nivel_Anomalia_MIROVA`, que es el único campo de la referencia
que sí viene de MIROVA. Contra el VRP de la misma pasada:

| banner de MIROVA | pasadas | VRP de la pasada |
|---|---|---|
| NONE | 9 | 0,02 a 0,05 MW |
| VERY LOW | 107 | 0,05 a 0,91 MW |
| LOW | 20 | 1,00 a 8,00 MW |

Ningún VERY LOW llega a 1 MW y ningún LOW queda bajo 1 MW. Un nivel agregado de varios días no separaría
así las pasadas, de modo que la clase es de la pasada. "Muy Bajo" del scraper equivale a VERY LOW del
banner, y "Bajo" a LOW.

## 3. Definición operativa

> Una pasada de la referencia es **alerta protegida** si es alerta (`ALERTA_TERMICA` del consolidado o
> `ALERTA_TERMICA_OCR`) y su `VRP_MW` es de **1 MW o más**, recalculado desde el VRP y nunca leído de la
> columna `Clasificacion Mirova`.

Función: `scripts/clase_mirova.py::alerta_protegida`. Las dos lecturas posibles del criterio (la escala del
paper y el banner de hoy) dan el mismo corte, así que no queda una decisión abierta para Nicolás.

Por qué recalcular importa: leyendo la columna, la unión de la referencia (tarea 0.1) tendría **764**
alertas protegidas; recalculando, **536**. Las 228 de diferencia son "Bajo" de menos de 1 MW de escalas
retiradas, y con la columna el criterio habría vetado cambios por alertas que el propio MIROVA llama VERY
LOW.

Denominador hoy (unión histórica, todas las fechas): 2.657 alertas, 536 protegidas (VIIRS 375: 254 de
2.111; VIIRS 750: 189 de 401; MODIS: 93 de 145). Por volcán: Láscar 372, Nevados de Chillán 65, Lastarria
34, Puyehue Cordón Caulle 21, Isluga 19, Villarrica 16, Tupungatito 6, Planchón Peteroa 2, Chaitén 1.
Antes de usar una ventana, aplicar A119 (calidad de la referencia por tramo).

## 4. Control

- Positivo: sobre las pasadas con banner, la clase recalculada separa VERY LOW de LOW sin un solo error
  (`test_control_coincide_con_el_banner_de_mirova`).
- Negativo: con un corte equivocado de 0,5 MW el mismo control fallaría, porque hay VERY LOW sobre 0,5 MW
  (`test_control_negativo_un_umbral_equivocado_falla_contra_el_banner`).
- Caso real: Villarrica VIIRS 375 del 2026-01-14 05:48, 0,07 MW, columna "Bajo": no es protegida
  (`test_la_clase_sale_del_vrp_no_de_la_columna`).

## 5. Límites y preguntas abiertas

- El banner sólo existe desde agosto de 2026 y sólo para la adquisición más reciente de cada volcán; LOW
  tiene 20 pasadas y no hay MODERATE ni más arriba en la muestra. Los cortes superiores (10, 100 MW) vienen
  del paper y del scraper, no se observaron en el banner.
- **MIROVA dice NONE para 9 pasadas que el scraper registra como alerta** (0,02 a 0,05 MW). En el borde de
  0,05 MW hay pasadas con NONE y con VERY LOW, probablemente por el redondeo del VRP mostrado. Si esas
  pasadas deben contar como alerta "Muy Bajo" en la suma de errores, o como pasadas donde MIROVA no vio
  nada, cambia el lado del error de la réplica en señales mínimas. Queda anotado; no afecta a las alertas
  protegidas.
- Consecuencia para la tarea 1.10: las 4 alertas de VIIRS 750 de 0,32 a 0,65 MW que `max` pierde son
  "Muy Bajo", no protegidas. Entran en la suma de errores, no en el veto.
