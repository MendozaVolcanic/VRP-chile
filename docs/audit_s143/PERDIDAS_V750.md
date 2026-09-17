# Las pasadas de VIIRS 750 que MIROVA publica y nosotros no

> Generado por `experiments/_s143_cobertura/perdidas_v750.py` desde `perdidas_v750.json`
> (2026-09-17T23:33:08+00:00). Ningún número escrito a mano (S91). Ventana **2026-09-01 a 2026-09-17**, régimen posterior al PR #571. Publicar = predicado del
> dashboard ejecutado con node. Referencia de MIROVA fijada por sha en el JSON.

**Por qué importa.** La regla del proyecto es tener al menos todo lo que MIROVA publica; esta
es la lista corta que hay que dejar en cero. Con n < 20 no se lee la tasa: se miran los casos.

## Los 5 casos

| volcán | pasada UTC | sensor | MIROVA (MW, km) | nuestro cúmulo | fondo K | máx I04 K | por qué no publica | ¿la noche quedó cubierta? |
|---|---|---|---|---|---|---|---|---|
| Isluga | 2026-09-05 05:42 | VIIRS_SNPP_750 | 0.24 MW a 0.0 km | 0.0 MW, 1 px a 0.676 km | 269.08 | 275.21 | cúmulo en el cráter con magnitud 0,0 MW (exceso recortado, D25) | sí |
| PuyehueCordonCaulle | 2026-09-07 05:30 | VIIRS_NOAA20_750 | 0.38 MW a 7.65 km | 0.0 MW, 1 px a 0.329 km | 269.6 | 277.68 | cúmulo en el cráter con magnitud 0,0 MW (exceso recortado, D25) | sí |
| PuyehueCordonCaulle | 2026-09-11 05:36 | VIIRS_SNPP_750 | 0.49 MW a 7.83 km | 0.0 MW, 1 px a 0.255 km | 267.45 | 276.41 | cúmulo en el cráter con magnitud 0,0 MW (exceso recortado, D25) | sí |
| PuyehueCordonCaulle | 2026-09-13 06:00 | VIIRS_NOAA21_750 | 0.45 MW a 7.83 km | 0.0 MW, 2 px a 0.22 km | 271.54 | 279.46 | cúmulo en el cráter con magnitud 0,0 MW (exceso recortado, D25) | sí |
| Villarrica | 2026-09-17 05:42 | VIIRS_NOAA20_750 | 0.16 MW a 1.06 km | 0.0 MW, 1 px a 0.339 km | 274.35 | 279.82 | cúmulo en el cráter con magnitud 0,0 MW (exceso recortado, D25) | sí |

## Qué dicen estos casos

- **5 de 5**: cúmulo en el cráter con magnitud 0,0 MW (exceso recortado, D25).

El fenómeno, en palabras: en los cinco casos **sí encontramos el foco en el cráter** (cúmulo
summit a 0,2 a 0,7 km) y lo que falla es la energía. El fondo con que se resta es la mediana
de un anillo regional de 5 a 25 km, lleno de valle sin nieve y más tibio que la cumbre; el
exceso sale negativo y se recorta a 0,0 MW. MIROVA, que promedia los píxeles vecinos del
alertado (SP426.5 p. 8, ec. 6), publica entre 0,16 y 0,49 MW en esas mismas pasadas. Es la
divergencia D25, la misma que el A/B abierto está midiendo en VIIRS 375.

**Consecuencia para el plan**: el flag del fondo por vecinos existe hoy sólo para VIIRS 375
(`ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS375`). Si el A/B lo respalda, la fase 2 del plan de paridad
debería llevarlo a VIIRS 750, que es donde está esta brecha de cobertura. No se propone antes
de tener el resultado del A/B: cinco casos muestran el mecanismo, no su tamaño (A94).

**Lo que NO dicen**: ninguna de estas cinco pasadas dejó una noche sin alerta, porque otra
pasada de la misma noche sí publicó. La pérdida es de fidelidad por pasada y de magnitud, no
de recall por noche.
