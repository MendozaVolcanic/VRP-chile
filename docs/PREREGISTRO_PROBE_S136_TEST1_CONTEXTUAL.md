# Pre-registro — probe de 3 brazos sobre la intersección contextual del Test 1 (S136)

> Escrito **antes** de correr el probe y de ver ninguna magnitud de salida (A18/A91). Lo que se
> mide, con qué se compara y qué desenlace corresponde a cada resultado quedan fijados acá.

## La pregunta

¿Cuánto se inflaría la magnitud publicada **sin** la intersección contextual del Test 1, con el
código de hoy? D10 la adoptó en S100 porque sin ella Tupungatito se iba a 8-19× contra MIROVA,
pero esa medición es previa a nadir-fijo (S103) y a `#535` (S126). La medición read-only de S136
(`experiments/_s136/RESULTADO_MEDICION.md`) mostró que **no se puede responder sobre la data
persistida**: lleva el filtro puesto, y el único campo pre-filtro (`n_test1_pixels`) no mide el
fenómeno.

## Diseño

**Tres brazos sobre el mismo granule**, procesado tres veces. El probe no edita `pipeline/`:
`process_viirs.py` importa los flags al namespace del módulo (línea 176), así que el probe los
reasigna ahí para cada corrida (patrón A75, monkeypatch read-only; la trampa A89 de parchear el
módulo origen está documentada en el probe de S135).

| brazo | `..._CONTEXTUAL_FILTER` | `..._CONTEXTUAL_KEEP_PEAK` | qué representa |
|---|---|---|---|
| **ACTUAL** | ON | ON | la producción de hoy (línea base) |
| **SIN_KEEP** | ON | OFF | contextual puro — el brazo B de S135, que dio 0 pérdidas |
| **SIN_FILTRO** | OFF | (inerte) | **la hipótesis**: Test 1 como camino propio, sin intersección |

**20 pasadas** (`experiments/_s136/pasadas_s136.json`), junio-agosto 2026, todas con ALERTA
MIROVA VIIRS375 a ≤20 min y con el Test 1 disparado: Tupungatito 6 (el caso de D10), Villarrica 4,
Planchón-Peteroa 3, y **7 de control no nevado** (Láscar 4, Lastarria 3). El control es
deliberado: en esta sesión ya fue un control el que refutó un indicador que parecía correcto.

El régimen lo fija el **código que procesa**, no la fecha del granule, así que usar pasadas de
junio-agosto da ground truth abundante sin salirse del régimen actual.

**Métrica**: la magnitud que publicaría el dashboard (`f5_core_vrp_mw`, con fallback a
`primary_cluster.vrp_mw` — A10 + S132/A46), contra el VRP de MIROVA de esa pasada. Se reporta
**mediana del ratio por brazo y por clase** (nevado / control), con n explícito (A90).

## Criterio de desenlace — fijado antes de ver los datos

Sea `R_sin` la mediana del ratio nuestro/MIROVA del brazo SIN_FILTRO en los **nevados**, y
`R_act` la del brazo ACTUAL sobre las **mismas** pasadas (pareado; si una pasada falta en un
brazo, se excluye de los dos — paridad de cobertura primero, lección de S135).

- **A — el filtro quedó sin función.** `R_sin` dentro de la banda 0,5-2,0 **y** dentro de un
  factor 1,5 de `R_act`. Desenlace: la intersección ya no cura nada; retirarla es volver al
  literal (P1 del gate) y se propone el A/B de adopción con reproceso completo.
- **B — el filtro sigue curando.** `R_sin` fuera de la banda 0,5-2,0, o peor que `R_act` por más
  de un factor 1,5. Desenlace: **no** se retira sola. El problema pasa a ser «qué mecanismo
  documentado nos falta que hace que MIROVA no lo necesite», con el máximo diario de Laiolo 2026
  como primer candidato.
- **C — indeterminado.** Menos de 4 pasadas útiles en los nevados, o el control se mueve tanto
  como los nevados (lo que indicaría un efecto universal, no del glaciar). Desenlace: no se
  concluye; se reporta el motivo y se amplía la muestra.

**Control de validez** (se evalúa siempre, no es opcional): si el brazo ACTUAL del probe no
reproduce la magnitud persistida de esas mismas pasadas dentro de un 10 %, el probe no está
midiendo la producción y **ningún otro número del run es interpretable**. Se reporta cuántas
pasadas reproducen y cuántas no antes que cualquier veredicto. (En S135, 2 de 3 pasadas no
reprodujeron y eso fue el hallazgo más importante del probe.)

## Límites aceptados de antemano

- 20 pasadas no son un A/B de adopción; esto mide un **mecanismo**, no autoriza un flip.
- Sólo VIIRS 375 m. El filtro no existe en MODIS ni en la banda M, así que no dice nada de ellos.
- El pareo con MIROVA usa ±20 min y su distancia es un radio sin acimut: sirve para descartar
  objetos distintos, no para afirmar que dos detecciones son el mismo punto (A93).
