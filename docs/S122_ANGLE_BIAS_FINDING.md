# S122 — El ángulo de visión sesga la magnitud VRP (hallazgo exploratorio)

> Scripts (S91): `experiments/_s122_geometry_backfill/analyze_angle_effect.py` y
> `angle_bias_vs_mirova.py`. Data: 20.529 records con geometría de observación
> persistida (feb–ago 2026, 11 Tier A). Read-only, no toca pipeline.

## El fenómeno

Cuando el satélite mira el volcán de forma oblicua, el píxel se estira sobre el terreno.
El foco térmico —que es chico, sub-píxel, y no cambia— queda promediado con más superficie
fría alrededor, y la señal atraviesa más atmósfera. La consecuencia esperable es que la
**misma** anomalía se lea más débil, y que las más débiles directamente no se detecten.

Los datos lo confirman, y **no es un artefacto de nuestro cálculo de área**: el pipeline usa
área de píxel nadir-fija (A66/A67), o sea que no hay ninguna corrección geométrica que
pudiera introducir por sí sola una dependencia con el ángulo.

## Magnitud (normalizada por volcán Y sensor — control estricto)

| zenith satélite | MODIS | VIIRS375 | VIIRS750 |
|---|---|---|---|
| 0-20° | 1.20 (n=90) | **1.34** (n=1066) | **1.29** (n=499) |
| 20-35° | 0.93 (n=74) | 1.16 (n=1022) | 1.07 (n=402) |
| 35-50° | 1.10 (n=77) | 1.03 (n=1216) | 1.03 (n=437) |
| 50-60° | 0.83 (n=83) | 0.88 (n=1146) | 0.82 (n=383) |
| 60-90° | 0.98 (n=53) | **0.75** (n=1264) | **0.62** (n=300) |

**VIIRS375 cae 1.8× y VIIRS750 2.1×**, monótonamente, del nadir a la visión oblicua.
**MODIS no muestra tendencia** (y su n por bin es chico).

Que MODIS sea plano es coherente con el cierre de D12 (`AUDIT_S122_C2_PASO0.md`): a 1 km el
foco **ya está diluido de entrada** —no forma ni siquiera un núcleo— así que agregarle
oblicuidad no cambia mucho. VIIRS375 es el que mejor resuelve el foco y por eso es el que
más pierde al diluirlo. Dos análisis independientes apuntando al mismo límite de resolución.

## Detección (tasa de detección summit)

| zenith | MODIS | VIIRS375 | VIIRS750 |
|---|---|---|---|
| 0-20° | 18.3% | **79.0%** | 37.1% |
| 60-90° | 9.0% | **53.9%** | 13.0% |

Se pierden eventos reales en las pasadas oblicuas, en los tres sensores.

## ¿El sesgo es NUESTRO o del MÉTODO? (867 noches emparejadas vs MIROVA)

Ratio nuestro/MIROVA en las mismas noches (CONS∪OCR, A11):

| zenith | VIIRS375 | VIIRS750 |
|---|---|---|
| 0-20° | **0.78** (n=326) | 0.79 (n=73) |
| 20-35° | 0.62 (n=181) | 0.59 (n=51) |
| 35-50° | 0.58 (n=102) | 0.79 (n=24) |
| 50-60° | 0.56 (n=72) | — |
| 60-90° | **0.59** (n=16) | — |

**Respuesta: las dos cosas, en proporciones distintas.** Si el sesgo fuera puramente
nuestro, el ratio caería el 1.8× completo; si fuera puramente del método, sería plano. Lo
que se ve es que **MIROVA también pierde magnitud con la oblicuidad** (por eso el ratio no
cae 1.8×), pero **nosotros perdemos ~25-30% más** (0.78 → ~0.57).

Matiz honesto: la caída del ratio es un **escalón** entre el primer y el segundo bin
(0.78 → 0.62) y después se aplana (0.58, 0.56, 0.59), no una pendiente continua. Con n=16
en el bin más oblicuo, ese extremo es débil. MODIS no entra: MIROVA publica muy pocas
ALERTAs MODIS (98 en total) y no hay ≥10 por bin.

## Qué significa y qué queda pendiente

1. **Para el paper (obj-2)**: es un sesgo instrumental cuantificado del VRP satelital que
   afecta a MIROVA igual que a nosotros. Un valor de VRP no es comparable entre pasadas sin
   considerar el ángulo. Es un aporte metodológico defendible, con 20.529 records de respaldo.
2. **Como lead accionable**: ese ~25-30% extra que perdemos nosotros es margen de mejora
   real en VIIRS. Hipótesis a testear (NO implementada, requiere A/B + A45): con footprint
   más grande, el anillo de fondo del ROI se contamina distinto y el contraste cae más de lo
   que debería. Ojo: cualquier corrección por ángulo sería una divergencia del clon literal
   → pasa por las 3 preguntas de MISSION.md.
3. **Uso inmediato sin tocar nada**: al auditar magnitud, estratificar por ángulo. Comparar
   una noche oblicua contra una nadir es comparar cosas distintas.

## Caveats

- **Exploratorio**, no confirmatorio: bins elegidos a mano, sin control por estación,
  cobertura de nubes, ni nivel de actividad del volcán.
- 1.3% de los records MODIS traen zenith >70° (hasta 75°), por encima del máximo geométrico
  del sensor (~65°) — casi seguro la interpolación de la grilla 5 km → 1 km extrapolando en
  el borde del barrido. Son las observaciones más oblicuas; conviene filtrarlas o mirarlas
  aparte.
- La primera pasada del análisis, mezclando sensores, daba una caída de 2.3×; el control
  estricto por volcán Y sensor la bajó a 1.8×. **La cifra válida es la del control estricto.**
