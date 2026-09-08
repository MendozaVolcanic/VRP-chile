# S136 — resultado del probe de 3 brazos: **el control de validez falla, no hay veredicto**

> Run 34274884640, `success`, 20/20 pasadas con los tres brazos. Criterio de
> `docs/PREREGISTRO_PROBE_S136_TEST1_CONTEXTUAL.md`, fijado antes de correr.

## El resultado es el control, no los ratios

El criterio pre-registrado puso una condición delante de todo: **si el brazo ACTUAL no reproduce
la magnitud que la producción ya tiene para esas mismas pasadas (dentro del 10 %), el probe no
está midiendo la producción y ningún otro número del run es interpretable.**

**Reproducen 10 de 20.** El umbral era 16 de 20. Así que **no se emite desenlace**, aunque los
ratios estén calculados y se vean razonables. Esa disciplina es justamente para lo que el
pre-registro existía: mirar los ratios ahora sería elegir el resultado después de verlo.

Las diferencias son de factor 1,5 a 2,5, en ambas direcciones:

| pasada | probe | persistido |
|---|---|---|
| Tupungatito 2026-06-08 05:30 | 0,0930 | 0,1679 |
| Tupungatito 2026-06-30 06:06 | 0,0393 | 0,0966 |
| Láscar 2026-07-10 05:12 | 0,2290 | 0,1466 |
| Lastarria 2026-06-01 05:06 | 0,0515 | 0,0077 |

## Antes de creerle al control: el comparador estaba roto (cuarto error de instrumento)

La primera corrida del evaluador dijo «reproducen 5 de 20» y listó discrepancias absurdas
(persistido 0,0000 contra probe 0,0930; persistido 1,3560 contra probe 0,0844). Era **el
comparador**, no el probe: `magnitud_persistida()` buscaba el record más cercano en el tiempo
**sin filtrar por sensor**, y en cada pasada hay un record de VIIRS 750 m con el **mismo
timestamp** que el de 375 m. Como el de 750 no tiene `f5_core_vrp_mw`, caía al `pc.vrp_mw`, que
es otra cantidad — la escena, no el núcleo.

Con el filtro por sensor y una ventana de 3 minutos (la misma pasada, no una cercana),
Planchón-Peteroa 06-01 reproduce **exacto** (0,0844 contra 0,0844) y el conteo sube de 5 a 10.

Es el **cuarto** error de instrumento de esta sesión, todos de la misma familia (A93): el
instrumento medía otra cosa que la que decía medir. Los otros tres fueron `n_test1_pixels` como
proxy del mosaico nival, el máximo global del TIF como «el foco» de Isluga, y
`final_hotspot_source` persistido como registro de qué rama corrió.

**Y el evaluador tenía un segundo defecto**: imprimía el desenlace igual, después de avisar que
el control había fallado. Contradecía su propio criterio. Corregido: ahora se detiene.

## Los ratios, para el registro — NO son un veredicto

Se dejan escritos por trazabilidad, con la etiqueta puesta: **no sostienen ninguna conclusión**
mientras el control no pase.

| brazo | nevados (n=13) | control no nevado (n=7) |
|---|---|---|
| ACTUAL | 0,91 | 0,69 |
| SIN_KEEP | 0,91 | 0,79 |
| SIN_FILTRO | 0,97 | 0,97 |

Lo único que se puede decir sin violar el pre-registro: **el brazo SIN_FILTRO no explota**. No
aparece nada parecido al 8-19× de D10 en ninguna de las 20 pasadas (el máximo del brazo
SIN_FILTRO es 4,57× y está en el control, no en un nevado). Si el control de validez se
resolviera y estos números se sostuvieran, el desenlace sería el A del pre-registro. Pero eso hay
que ganárselo, no suponerlo.

## Qué hay que hacer antes de leer estos ratios

Entender por qué la mitad de las pasadas no reproduce. Descartado ya: no es la versión del
producto (los persistidos son `standard`). Candidatos, en orden de sospecha:

1. **El probe llama a `calculate_vrp` directo**, mientras la producción pasa además por
   `store.py` (auto-upgrade NRT→Standard, pisos, `f5_core`, y lo que haya en el camino). Si
   `store.py` toca la magnitud, el probe mide una etapa anterior. Es lo más barato de verificar.
2. **Granule distinto para la misma pasada**: el `stamp` se arma con la hora del record, y si la
   plataforma tiene más de un granule cerca, el probe puede haber tomado otro. En Tupungatito
   06-08 el probe da 0,0930 y el record SNPP de las 05:12 vale 0,0937 — sospechosamente cerca
   para ser casualidad, siendo que el caso pedía el NOAA20 de las 05:30.
3. Casos donde el persistido tiene `f5_core_vrp_mw = None` y el comparador cae a `pc.vrp_mw`
   (Lastarria 07-24): ahí la comparación es entre dos cantidades distintas y habría que
   excluirla, no contarla como fallo.

El (2) tiene una consecuencia incómoda si se confirma: querría decir que el probe procesó una
pasada distinta de la que el caso nombra, y entonces **los ratios son de otro objeto**.
