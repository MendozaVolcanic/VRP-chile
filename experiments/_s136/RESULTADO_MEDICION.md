# S136 — ¿sigue existiendo el fenómeno que justificó la intersección contextual?

> Medición read-only pedida antes de diseñar el A/B. **Respuesta corta: no se puede responder
> read-only, y ahora se sabe por qué.** Lo que sí quedó medido, y un indicador propio refutado.

## Lo que se buscaba

D10 adoptó la intersección contextual (`ctxpeak`, S100) porque sobre el glaciar de Tupungatito la
magnitud del Test 1 se inflaba 8-19× contra MIROVA. Esa medición es previa a nadir-fijo (S103) y
a `#535` (S126, que apagó la máscara de nube y bajó el fondo global 6-8 K en nevados). Si el
fenómeno se hubiera apagado solo, la intersección habría quedado inerte y retirarla sería un
no-op.

## Resultado 1 — la paridad de hoy está en banda, con el filtro puesto

`paridad_por_regimen.py`. VIIRS 375 m, ground truth CONS ∪ OCR del cargador canónico, pareo por
pasada a ±20 min, magnitud `f5_core_vrp_mw` con fallback a `pc.vrp_mw` (A10 + S132/A46).

| volcán | previo a #535 | actual (desde 28-ago) |
|---|---|---|
| Tupungatito | **0,65×** (n=154) | 0,87× (n=6) |
| Planchón-Peteroa | 0,98× (n=123) | 0,93× (n=2) |
| Puyehue | 1,03× (n=203) | 1,12× (n=11) |
| Láscar (control) | 0,54× (n=277) | 0,68× (n=13) |
| Lastarria | 0,60× (n=192) | 0,88× (n=6) |
| Isluga | 0,60× (n=254) | 0,58× (n=19) |
| Villarrica | 0,95× (n=28) | — (n=0) |

Los once están dentro de la banda 0,5-2,0 en el régimen con n suficiente. **Nada del 18,9×.**

**Pero esto no responde la pregunta**: los records de los dos regímenes llevan el filtro puesto.
Mide que el filtro cumple su función (o que ya no hace falta), sin distinguir entre las dos.
El régimen actual tiene n de un dígito en cuatro volcanes: no sostiene un veredicto propio (A90).

## Resultado 2 — el indicador pre-filtro que iba a decidirlo NO mide el fenómeno (error propio)

`n_test1_pixels` se persiste **antes** del recorte (`process_viirs.py:1109`, previo al filtro de
la 1779), así que parecía el proxy ideal: si el Test 1 ya no barriera el mosaico nival, el
footprint se habría encogido. Medido:

| volcán | footprint previo | footprint actual |
|---|---|---|
| Tupungatito (glaciar, el caso de D10) | mediana 73 px (n=1556) | mediana 72 px (n=41) |
| Villarrica | 65 px | 71 px |
| **Láscar (control, sin problema de magnitud)** | **70 px** | **70 px** |
| Lastarria | 67 px | 68 px |

El control fue el que delató el problema: **Láscar tiene el mismo footprint que Tupungatito.** Si
midiera la extensión del mosaico nieve/roca, el desierto de Atacama y un glaciar a 5.682 m no
podrían dar el mismo número.

La causa está en `pipeline/test1_integrated.py:285`: `contributing_in_roi = excess_roi > 0`, es
decir **todo píxel del ROI cuyo NTI supere el fondo**. Eso es cerca de la mitad del disco por pura
estadística, en cualquier escena. El campo cuenta píxeles sobre el fondo, no extensión de anomalía.

**`n_test1_pixels` queda descartado como proxy del fenómeno de D10.** Es un error de instrumento
de la familia A93 — el instrumento medía otra cosa que la que decía medir — cazado por el control,
no por revisar el método.

## Resultado 3 — `final_hotspot_source` persistido no dice qué records pasaron por el filtro

El filtro se decide con `final_hotspot_source == "test1"` (`process_viirs.py:1779`), con el valor
legacy asignado en las líneas 1715/1726. Pero en la **línea 2006** `resolve_honest_anchor()`
(S106) **reasigna** esa misma variable antes de persistirla, con otro vocabulario:
`ctx_cluster` / `test1_roi` / `test1_nti_peak` / `vent` / `eruption_loose`.

Por eso el campo guardado no vale `"test1"` en ningún record de la serie, y una consulta que lo
busque devuelve cero — un cero que se lee como «el filtro no corre nunca» y es falso (A89, otra
vez del lado de quien audita). Cualquier auditoría futura que quiera saber qué records pasaron
por el filtro **no puede usar este campo**; hay que instrumentarlo en el probe.

## Conclusión

1. **El filtro no quedó inerte por el cambio de régimen.** No hay evidencia de que se pueda
   retirar como no-op, así que el A/B sigue siendo necesario.
2. **La pregunta original no tiene respuesta read-only**, por dos razones ahora entendidas: la
   data lleva el filtro puesto, y el único campo pre-filtro persistido no mide el fenómeno.
3. **Lo que hay que instrumentar en el probe** (A75, en CI, read-only sobre granules):
   `delta_L_integrated` del Test 1 antes y después del recorte, y el `final_hotspot_source`
   **legacy** de la línea 1779 — ninguno de los dos se persiste hoy.
4. La banda de paridad actual dice que el sistema, tal como está, publica magnitudes sanas en los
   nevados. Retirar el filtro sin medir pondría eso en riesgo.
