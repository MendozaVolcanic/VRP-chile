# S133 · Por qué MIROVA tenía la anomalía de las 07:50 y nosotros no

**Causa raíz: el camino casi-en-tiempo-real de MODIS nunca funcionó, porque pedíamos una
colección que no existe.** Un nombre de colección equivocado no produce un error en el
catálogo de NASA: produce **cero resultados**, y cero resultados es indistinguible de
«todavía no hay dato». Por eso pasó inadvertido.

El caso que lo destapó: el 2026-09-04 a las 07:50 UTC, MIROVA publicó una anomalía térmica
MODIS de **4,75 MW a 1,41 km del cráter de Villarrica**. Nosotros no la teníamos.

## El fenómeno, primero

Un satélite pasa sobre el volcán y graba. Ese dato crudo llega a tierra por dos caminos
distintos, y la diferencia entre ellos es de horas o de días.

El camino **casi-en-tiempo-real** (LANCE) publica el granule unas tres horas después de la
pasada, con una calibración provisional y conservándolo apenas una o dos semanas. El camino
**estándar** (LAADS) publica el mismo granule con la calibración definitiva y lo guarda para
siempre, pero tarda de horas a días.

Para monitoreo operacional los dos importan, y por eso el pipeline los usa en cascada: busca
primero el estándar, porque su calibración es la buena, y si todavía no está, cae al
casi-en-tiempo-real. Esa caída es exactamente lo que permite ver una anomalía la misma noche
en vez de dos días después. MIROVA hace lo mismo.

## Qué estaba roto

Nuestra tabla de productos pedía, para el camino NRT de MODIS:

    MOD021KM_NRT  versión 61
    MYD021KM_NRT  versión 61

Esas colecciones **no existen**. LANCE nombra sus colecciones de MODIS con el **mismo**
short_name que el estándar, y marca lo casi-en-tiempo-real en la **versión**:

    MYD021KM  versión 6.1NRT

Verificado contra el catálogo el 2026-09-04, sobre Villarrica y ese día:

| producto | lo que pedíamos | granules | lo correcto | granules |
|---|---|---:|---|---:|
| MODIS Terra L1B | `MOD021KM_NRT` v61 | **0** | `MOD021KM` v6.1NRT | 3 |
| MODIS Terra geo | `MOD03_NRT` v61 | **0** | `MOD03` v6.1NRT | 3 |
| MODIS Aqua L1B | `MYD021KM_NRT` v61 | **0** | `MYD021KM` v6.1NRT | **1 — la de 07:50** |
| MODIS Aqua geo | `MYD03_NRT` v61 | **0** | `MYD03` v6.1NRT | 1 |

La consulta con el nombre correcto devuelve **exactamente la pasada de las 07:50**, la misma
que MIROVA publicó.

## De dónde salió el error, y por qué es instructivo

Para **VIIRS**, el sufijo `_NRT` en el short_name **sí es el esquema correcto**:
`VNP02IMG_NRT`, `VJ102IMG_NRT` existen y devuelven datos. El error fue extrapolar el
esquema de un sensor al otro.

Es la misma familia que la regla A37, que nació de descubrir que MODIS y VIIRS marcan la
saturación de maneras distintas: **el esquema de un sensor no se traslada al otro, hay que
leer la documentación de cada uno**. Acá volvió a pasar, en otro punto del pipeline.

Por eso el test de regresión fija las **dos** convenciones, no sólo la que estaba mal: sin
el control de VIIRS, alguien podría «arreglar» VIIRS por simetría con MODIS y romper lo
único que funcionaba.

## Por qué se vio justo ahora

El fallback estaba roto desde siempre, pero sólo se nota cuando el camino estándar se
atrasa. Y ahora está atrasado, de forma desigual entre satélites. Medido el 2026-09-04:

| colección | último granule publicado | atraso |
|---|---|---:|
| MOD021KM (Terra) | 2026-09-04 05:55 | 11,6 h |
| **MYD021KM (Aqua)** | **2026-09-03 05:55** | **35,6 h** |
| VNP02IMG (VIIRS SNPP) | 2026-09-04 05:42 | 11,8 h |
| VJ102IMG (VIIRS NOAA-20) | 2026-09-04 07:42 | 9,8 h |

Aqua sobre Villarrica: 3 o 4 granules por día hasta el 2 de septiembre, y **cero** el 3 y el
4. Con el estándar de Aqua a 36 horas y el NRT roto, no había por dónde entrara.

Terra sí entró: la pasada de las 02:15 está en nuestros datos con 0,2 MW a 18,7 km,
clasificada *far*, y MIROVA marca esa misma pasada como RUTINA en 0,0. En todas las pasadas
comparables de ese día coincidimos; faltaba justo la que MIROVA marcó como alerta.

## El arreglo

`pipeline/fetch.py`: las cuatro entradas NRT de MODIS pasan a `<short_name>` + versión
`6.1NRT`. VIIRS **no se toca**.

`tests/test_nrt_short_names_modis_s133.py` fija la forma de la tabla, con 26 casos. Es
**offline a propósito**: un test que consulte el catálogo de NASA fallaría por causas ajenas
—red, mantenimiento— y terminaría ignorado, que es como mueren los guards.

## Lo que este arreglo NO hace

No recupera lo perdido. Los granules de LANCE se conservan una o dos semanas, así que se
puede reprocesar hacia atrás sólo dentro de esa ventana; más allá, sólo queda el estándar
cuando NASA lo publique.

Tampoco cambia la calibración de nada ya guardado: el pipeline marca cada record con su
`product_version` y `store.py` reemplaza solo el NRT por el estándar cuando éste aparece.

Y no explica por qué el estándar de Aqua está a 36 horas. Eso es de NASA y no se determinó.
