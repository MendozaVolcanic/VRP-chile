# ¿Reportamos el cluster de mayor VRP, como MIROVA? — medición (S124)

Pregunta de Nicolás: *"¿acaso en el operacional nosotros no reportamos la mayor?
Deberíamos hacerlo igual aunque en el frontend y en los gráficos haya filtros de
distancia."*

Script reproducible: `experiments/_s124_cluster_selection/max_vs_vent_anchored.py`

## Respuesta corta: no, no reportamos la mayor

`pipeline/clustering.py:118` — con `strategy="vent_anchored"` (activo en el
operacional vía `ENABLE_VENT_ANCHORED_CLUSTERING`) los clusters dentro del
`inner_radius_km` ganan *"independiente de `vrp_mw`"*, y entre ellos gana **el
más cercano al cráter**, no el más fuerte.

Se introdujo en S38 para tapar un modo de falla real: un cluster grande y lejano
(Salar de Atacama, lago Conguillío) se llevaba el `primary_cluster` y enterraba
la anomalía del cráter.

## La información NO se pierde

`anomaly_pixels` persiste **lat, lon, vrp_mw, bt_k y dist_km por píxel**. La
selección es una decisión escrita en `primary_cluster`, pero la materia prima
queda intacta: el cluster de VRP máximo se reconstruye **offline, sin
reprocesar**. Eso es lo que permite la medición de abajo.

## Medición: ¿cuál se parece más a MIROVA?

Ventana 2026-04-01..2026-08-24, noches pareadas, referencia nocturna. Se
re-agrupan los píxeles por enlace de distancia (single-linkage al espaciado del
sensor × 1,5, cubriendo la diagonal de la connectivity-8 del pipeline) y se
comparan los dos candidatos contra el VRP que MIROVA publicó:

| volcán | n | vent_anchored | vrp_max | más cerca de MIROVA |
|---|---|---|---|---|
| Lascar | 228 | 0,62 | **0,75** | MAX |
| Isluga | 131 | 0,61 | **0,68** | MAX |
| Lastarria | 95 | 0,47 | **0,54** | MAX |
| PuyehueCordonCaulle | 91 | 0,82 | **1,14** | MAX |
| Tupungatito | 76 | 0,74 | **0,76** | MAX |
| PlanchonPeteroa | 68 | 0,93 | **1,06** | MAX |
| Chaiten | 28 | **1,18** | 1,68 | vent |
| Villarrica | 26 | **1,02** | 1,40 | vent |
| NevadosDeChillan | 5 | 1,20 | **1,19** | MAX |
| Copahue | 5 | **1,33** | 1,57 | vent |
| Llaima | 2 | 0,36 | 0,36 | empate |
| **GLOBAL** | **755** | **0,71** | **0,83** | **MAX** |

**El máximo queda más cerca de la paridad (0,83 vs 0,71) y gana en 8 de 11.**
La intuición de Nicolás está respaldada por los datos.

Patrón: sub-reportamos sistemáticamente (ambos por debajo de 1,0) y el máximo
reduce esa sub-estimación. Donde gana `vent_anchored` (Chaitén, Copahue,
Villarrica) es justo donde ya sobre-reportamos, así que el máximo empeora.

## Por qué esto NO es todavía una recomendación de cambio

1. **Mide magnitud, no falsos positivos.** Compara sólo noches que MIROVA ya
   publicó. No prueba si el máximo reintroduce el robo de cluster que motivó
   `vent_anchored` en S38 (Salar, lago). Eso requiere el eje espacial (A61/A85).
2. **El re-agrupado offline es aproximado** (enlace por distancia vs la
   connectivity de grilla del pipeline).
3. **Está acoplado con la cerca del frontend** (ver abajo).

Corresponde un A/B con criterio pre-registrado, bajo A45. No un flip.

## El acoplamiento con la cerca del frontend (la "divergencia D")

Son **el mismo problema visto desde dos capas**:

- MIROVA publica el hotspot **esté donde esté**, con su distancia. Prueba: el CSV
  trae filas de MIROVA con distancias de 18, 19, 30 y 31 km. La etiqueta
  `FALSO_POSITIVO` que las acompaña es del **scraper de Nicolás**, no de MIROVA.
- Nuestro frontend (`mirovaEqVrp`) pone **VRP = 0** si el cluster quedó más lejos
  que el `inner_radius_km`. Medido en la misma ventana: **680 de 9.924 records
  (7 %)** con VRP real se muestran como 0.

| volcán | inner | records VRP>0 | apagados | % | VRP máx apagado |
|---|---|---|---|---|---|
| Villarrica | 5 | 1024 | 202 | 20 % | 89,78 |
| NevadosDeChillan | 5 | 584 | 93 | 16 % | 5,72 |
| Llaima | 5 | 913 | 86 | 9 % | 8,59 |
| Lastarria | 3 | 714 | 54 | 8 % | 5,00 |
| … | | | | | |
| **TOTAL** | | **9924** | **680** | **7 %** | |

**El acoplamiento**: si el pipeline pasara a reportar el máximo como MIROVA,
muchos de esos máximos caerían fuera del `inner_radius` y **la cerca del frontend
los apagaría igual**. Cambiar una capa sin la otra no mueve la aguja.

**Por qué llamarlo divergencia**: no es que la cerca esté mal — filtra el lago
Conguillío y compañía, y esa fue su razón de ser en S33. Es que **hace algo que
MIROVA no hace** y no está escrito en ninguna parte. Quien compare nuestro
dashboard con el de MIROVA ve una diferencia y no encuentra la explicación
documentada. Ese es el único reclamo: ponerlo por escrito en
`MIROVA_DIVERGENCES.md`.
