# S90 — Auditoría VRP alto (11 Tier A) + fix tarjeta "última detección"

**Fecha**: 2026-05-30. Disparador: Nicolás observó (a) tarjetas mostrando un valor
de una pasada anterior y no la última, (b) valores extraños de cientos/miles de MW
en el gráfico de PCC (892 MW el 4-may), (c) preguntó si MIROVA reporta algo en el
"cluster 17" de Lastarria (~12 km).

Scripts: `audit_high_vrp.py` (extremos VRP por volcán) + `cross_mirova.py` (cruce con
referencia MIROVA + firma de fechas recurrentes). Outputs: `*.txt`.

## Hallazgo 1 — `record.vrp_mw` (suma scene-wide) es estructuralmente enorme

Los 11 Tier A tienen `record.vrp_mw` de cientos a 1660 MW, casi siempre
`dist_class=far`, casi siempre MODIS. Es la **suma de todos los pixeles anómalos
del grid 50×50 km** (incluye off-nadir sec³ A36, salares, nubes). NO es un VRP
volcánico y **NO se grafica** — el dashboard usa `mirovaEqVrp` (= `pc.vrp_mw`,
cluster, summit-gated). Confirmado: el 892 MW que vio Nicolás = `pc.vrp_mw` de PCC,
no la suma scene.

## Hallazgo 2 — los picos de cientos/miles de MW en PCC son artefactos de cirrus (A23/D9)

Records PCC con `pc.vrp_mw` 892–1362 MW:

| fecha | t_bg | t_max ("hot") | VRP | mecanismo |
|---|---|---|---|---|
| 2026-04-16 | 255 K | **272 K (−1 °C)** | 1362 MW | `diag_n_dnti_ctx=107` |
| 2026-05-04 | 252 K | **266 K (−7 °C)** | 892 MW | `diag_n_dnti_ctx=153` |

`t_max` BAJO CERO → no es lava/fumarola, es cima de nube. El VRP sale del **path D
(dNTI contextual)** disparando sobre un campo de cirrus uniforme (kernel 8-vecinos
fabrica gradiente artificial). Es exactamente el drift **A23 / D9** documentado como
abierto. **Firma confirmatoria**: el 4-may pican 6 volcanes a la vez (Chaitén,
Llaima, Planchón, PCC, Tupungatito, Villarrica) y el 6-may otros 5 — cirrus regional,
no volcanismo coordinado. **MIROVA no reportó nada** en ninguna de esas fechas.

PCC los muestra y los demás no porque su `inner_radius=20 km` deja caer el cluster
artefactual a 0.7–3 km como "summit" → pasa `mirovaEqVrp`. En los otros (inner 3–7 km)
caen "far" → `mirovaEqVrp=0` → no se grafican.

**Decisión Nicolás S90**: solo diagnóstico, NO tocar pipeline. El fix obvio (gate
`t_bg<260 K`) está PROHIBIDO (refutado S86: mata la erupción real de Láscar 17-feb
bajo nube fría; escudo anti-drift S90 §3). A23/D9 sigue abierto para sesión futura
con brainstorming + A45.

## Hallazgo 3 — cluster 17 Lastarria: MIROVA reporta SOLO el cráter (1.2–2.7 km)

108 refs MIROVA Lastarria, todas a 1.2–2.7 km (mediana 2.2). **Cero** a >8 km.
El centroide empírico del "cluster 17" (~12 km WSW, coord de la entrada Lazufre en
`volcanic_features.yaml`) NO tiene corroboración MIROVA. Probable dispersión de
pixeles, no feature térmica genuina. → revisar la entrada Lazufre (ver
[[reference_s90_coord_research_closed]]).

## Fix aplicado — tarjeta muestra "última detección", no "48h máx"

`latestVRP` (máximo de 48h, desacoplado del timestamp) → nueva `latestDetection`
(la detección summit MÁS RECIENTE de 48h, valor + timestamp acoplados; desempate por
VRP mayor ante igual timestamp). `latestVRP` ahora delega para mantener consistentes
tarjetas + barra de alertas + markers overview. Bug TZ corregido de paso
(`new Date` → `parseUtcMs` en el corte de 48h). Verificado en preview (navegador
Santiago UTC-4): PCC 5.00→0.51, Chaitén 5.00→0.91, Copahue 1.68→0.68; barra de
estado 8 Bajo/3 Muy Bajo → 4 Bajo/7 Muy Bajo. Solo display, no toca detección/VRP.
