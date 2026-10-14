# Qué es una "alerta protegida" en el criterio de victoria (tarea 0.2 del loop)

> Escrito 2026-10-14 por el loop autónomo (tarea 0.2 de `tasks/LOOP_OBJETIVOS.md`) y corregido el mismo día
> con el verificador con contexto limpio de #780. Script: `scripts/clase_mirova.py`. Tests y control:
> `tests/test_clase_mirova_s151.py`. Decisión pendiente para Nicolás: D-4 en la cola del loop (§5 de este
> documento).

## 1. La pregunta

El criterio que Nicolás fijó el 2026-10-13 para la réplica dice: no se acepta ningún cambio que pierda una
alerta que MIROVA clasifique de "Bajo" para arriba; dentro de "Muy Bajo", una alerta perdida y una
publicación de más pesan igual. Para usarlo hay que saber qué es esa clase, porque la columna
`Clasificacion Mirova` del CSV trae "Bajo" de 0,04 MW y "Muy Bajo" de 0,99 MW, y una clase de intensidad
que no ordena la intensidad no sirve de umbral.

La hipótesis del plan era que la columna guardaba el nivel de la página del volcán (un agregado de días) y
no el de la pasada. **Quedó refutada**: la clase es de la pasada (§2).

## 2. Lo que se encontró

**La columna no la escribe MIROVA.** La calcula el scraper de Mirova-v1 desde el VRP de la pasada
(`volcanes.py:63`, llamada en `scraper.py:156` y en `scraper_ocr.py`). Ya lo había encontrado la auditoría
S139 (`docs/audit_s139/EJE_1_semantica_etiquetas_referencia.md`, H110), pero no llegó al plan del loop.
Historia según el verificador: `scraper.py` ya tenía los cortes 1, 10, 100 y 1.000 MW el 16-ene (commit
b1b6394a); el OCR usó otra escala (Muy Bajo bajo 0,2, Bajo bajo 1, Medio bajo 5, Alto) hasta que las dos se
unificaron el 12-jun (c7229712). Las filas viejas no se recalcularon.

Coherencia de la columna con la clase recalculada desde el VRP, sólo alertas (`scripts/clase_mirova.py`):

| canal | incoherente | coherente al 100 % desde |
|---|---|---|
| consolidado | 17 de 69 alertas de enero ("Bajo" bajo 1 MW, procesadas del 11 al 15-ene) | febrero de 2026 |
| OCR | 12 a 130 por mes de enero a junio (escala retirada, con clase "Medio") | julio de 2026 |

**El banner de MIROVA de hoy es por pasada y corta en 1 MW.** El OCR lee desde la versión 30 (agosto de
2026) el banner de la imagen, `Nivel_Anomalia_MIROVA`, que es el único campo de la referencia que sí viene
de MIROVA. Banner y VRP salen de la misma imagen y el nivel se pega sólo a la celda más reciente
(`ocr_utils.py`, `_marcar_mas_reciente`), así que corresponden a la misma pasada. El defecto de "imagen de
otra pasada" de Suomi NPP afecta a la distancia y al tipo, no al banner.

| banner de MIROVA | pasadas | VRP de la pasada |
|---|---|---|
| NONE | 9 | 0,02 a 0,05 MW |
| VERY LOW | 107 | 0,05 a 0,91 MW |
| LOW | 20 | 1,00 a 8,00 MW |

Ningún VERY LOW llega a 1 MW y ningún LOW queda bajo 1 MW. Y 14 pasadas VERY LOW tienen una alerta de 1 MW
o más del mismo volcán y sensor en las 48 h previas: un nivel agregado no las habría bajado a VERY LOW.

**El paper no fija el corte.** Coppola et al. 2016a (Geological Society Special Publication 426, figura 11,
p. 16 del PDF `documentacion/sp426.5.pdf`, leída sobre la página renderizada) se contradice consigo mismo.
El pie dice Low bajo 1 MW, Moderate de 1 a 10, High de 10 a 100, Very High de 100 a 1.000 y Extreme de
1.000 a 10.000 MW. La figura que ese pie describe pone las bandas en 10^7, 10^8, 10^9 y 10^10 W (Low bajo
10 MW, Very High de 1.000 a 10.000 MW), y su banner dice "VERY HIGH" con 6.797 MW, que según el pie sería
Extreme. La figura calza con el sitio de hoy, que agrega VERY LOW bajo 1 MW. **El corte de 1 MW lo
sostiene el banner de MIROVA de hoy, no el paper.**

## 3. Definición operativa (lectura A, la que usa el loop por defecto)

> Una **pasada** (volcán, sensor, hora al minuto) es **alerta protegida** si en la referencia unificada
> tiene una fila de alerta (`ALERTA_TERMICA` del consolidado o `ALERTA_TERMICA_OCR`) con `VRP_MW` de
> **1 MW o más**, recalculado desde el VRP y nunca leído de la columna `Clasificacion Mirova`.

Función: `scripts/clase_mirova.py::alerta_protegida` (por fila) y `pasadas_protegidas` (por pasada). Se
cuenta por pasada porque 377 pasadas de alerta están a la vez en el consolidado y en el OCR; ninguno de
esos pares queda a lados distintos de 1 MW, así que la definición es coherente entre canales.

Denominador hoy (unión histórica de la tarea 0.1, todas las fechas): 44.019 pasadas, 2.280 con alerta,
**439 protegidas** (VIIRS 375: 232; VIIRS 750: 149; MODIS: 58). Por volcán: Láscar 299, Nevados de Chillán
52, Lastarria 34, Puyehue Cordón Caulle 18, Isluga 17, Villarrica 10, Tupungatito 6, Planchón Peteroa 2,
Chaitén 1. Leyendo la columna en vez del VRP, el criterio habría vetado cambios por alertas que el propio
MIROVA llama VERY LOW (en filas: 764 contra 536).

De las 439, **174 vienen sólo del OCR y 131 de ellas son anteriores al 2026-06-13**: su tipo ALERTA depende
de una geometría del OCR sin calibrar (A119). En una ventana anterior a esa fecha deciden las de la tabla;
las del OCR se informan aparte.

## 4. Control

- Positivo: `alerta_protegida`, aplicada a las pasadas con banner, separa VERY LOW de LOW sin error
  (`test_control_la_funcion_coincide_con_el_banner`).
- Negativo: la misma función con un umbral equivocado (0,5 o 1,01 MW) falla contra el banner
  (`test_control_negativo_umbral_equivocado_falla`). El control sólo pasa entre 0,92 y 1,00 MW.
- Caso real: Villarrica VIIRS 375 del 2026-01-14 05:48, 0,07 MW, columna "Bajo": no es protegida.

## 5. Límites y la decisión que queda abierta

- **D-4 para Nicolás: ¿qué es "lo que MIROVA clasifica"?** El tipo ALERTA también es del scraper: VRP
  mayor que 0 y distancia dentro de su `limite_km` (`scraper.py`). El banner de MIROVA dice LOW en 3 pasadas
  que el scraper marca FALSO_POSITIVO_OCR (por ejemplo Isluga 2026-09-06, 2,27 MW). Hay dos lecturas:
  - **A** (por defecto): sólo alertas del scraper con VRP de 1 MW o más. **439 pasadas.** Protege lo que
    MIROVA ve cerca del cráter, que es lo que la réplica publica.
  - **B**: toda pasada en que MIROVA ve 1 MW o más, cualquiera sea la distancia. **992 pasadas**, 553 más
    (VIIRS 375: 439; VIIRS 750: 73; MODIS: 41; sobre todo Lastarria 151, Láscar 93, Llaima 79, Isluga 59,
    Nevados de Chillán 54, Copahue 37). Incluye anomalías lejanas que el tablero oculta por diseño.
  - Recomendación del loop: **A**, porque la réplica compara el cúmulo del cráter y B vetaría cambios por
    calor lejano que la réplica no publica en ningún brazo. Mientras Nicolás no decida, el loop evalúa
    con las dos lecturas en paralelo, como pide el plan.
- **Cobertura del banner.** Los 107 VERY LOW son todos VIIRS 375; 7 de los 20 LOW son VIIRS 750 con VRP
  truncado a entero (1,0 a 8,0); **MODIS no tiene ni una pasada con banner**. El corte está observado en
  VIIRS 375 y se extiende a los otros sensores por la escala del scraper, no por observación. El banner
  sólo existe desde agosto de 2026 y no hay MODERATE ni más arriba en la muestra.
- **MIROVA dice NONE para 9 pasadas que el scraper registra como alerta** (0,02 a 0,05 MW). En el borde de
  0,05 MW hay pasadas con NONE y con VERY LOW, probablemente por el redondeo del VRP mostrado. Si esas
  pasadas cuentan como alerta "Muy Bajo" en la suma de errores o como pasadas donde MIROVA no vio nada
  cambia el lado del error en señales mínimas. Queda anotado; no afecta a las protegidas.
- La tabla `latest.php` podría traer un nivel propio en columnas que el scraper no lee (lee la 0, 1, 3, 4 y
  5): SIN VERIFICAR.
- Consecuencia para la tarea 1.10, por escala y SIN VERIFICAR sobre las filas: las 4 alertas de VIIRS 750
  de 0,32 a 0,65 MW que `max` pierde serían "Muy Bajo", suma de errores y no veto.
