# S60 Per-vol opt-in offline audit — solo Villarrica necesita kernel-bg

**Fecha**: 2026-05-17
**Motivación**: PR #65 (S59) marcó `local_kernel_bg: true` en 4 vols (Villarrica, Copahue,
Llaima, PlanchónPeteroa) basándose en presencia de cuerpos de agua adyacentes. Antes de
disparar A/B reprocs adicionales, validar offline si el patrón Villarrica (gap LEGACY
vs MIROVA NRT alto → fix necesario) aplica a los otros 3.

## Método

Comparar LEGACY summit (`data/mirova_equivalent/<Vol>.json`) VIIRS375 window 04-16/05-15
contra MIROVA CSV NRT en el mismo window y mismo sensor. Ratio = LEGACY median / MIROVA
median. >1.0 = sobre-estimación (fix kernel ayudaría), <1.0 = sub-estimación (fix
empeoraría), ~1.0 = calibrado (fix neutral o dañino).

## Resultado (window 04-16/05-15 VIIRS375)

| Vol | MIROVA NRT (n, med) | LEGACY summit (n, med) | Gap LEGACY/MIROVA | Interpretación fix |
|---|---|---|---:|---|
| Villarrica | 4, 0.38 MW | 102, 2.16 MW | **5.68×** | Sobre-estima — fix necesario |
| Copahue | 7, 1.46 MW | 98, 1.66 MW | **1.14×** | Calibrado — fix marginal o dañino |
| Llaima | 10, 2.04 MW | 90, 2.06 MW | **1.01×** | Calibradísimo — fix dañino |
| Planchón-Peteroa | 0 (scraper no cubrió) | 86, 1.72 MW | desconocido | sin target, no decidible |

## Adicional: OSF v2.5 curated VIIRS375 class=1 (target histórico)

| Vol | OSF curated (n, med) | LEGACY all-time summit (n, med) | Gap |
|---|---|---|---:|
| Villarrica | 1817, 1.06 MW | 258, 2.88 MW | 2.73× sobre |
| Copahue | 2892, 0.26 MW | 245, 2.19 MW | 8.37× sobre |
| Llaima | 3, 0.05 MW | 229, 2.49 MW | 54.4× (no representativo, n=3) |

> El gap OSF agregado induce error: incluye 25 años de historia (Villarrica 2015 cuasi-erupción
> infla mediana OSF a 1.06 vs MIROVA NRT actual 0.38). El target operacional relevante es
> MIROVA CSV NRT, no OSF.

## Interpretación

### Por qué Villarrica sí y los otros no

Hipótesis física: el lago norte de Villarrica está aproximadamente a 4-7km del cráter, en
zona "interior del ring 5-25km" del background. En condiciones de Muy Bajo (no actividad
eruptiva pero cráter con calor residual), el lago calienta el ring y baja artificialmente
el ΔL contra background → infla ETI → infla VRP. Sin lago en zona-ring, el ring 5-25km
representa background "frío" honesto y el ΔL no se infla.

- **Copahue**: lago El Agrio dentro del cráter mismo (~0.5km del centro). En ring 5-25km
  hay terreno andino seco. Background ring NO contaminado.
- **Llaima**: lago Conguillío N a ~15km del cráter (probable en ring). Pero LEGACY median
  vs MIROVA NRT match perfecto (1.01×) sugiere que en práctica no contamina relevantemente.
- **PlanchónPeteroa**: laguna + glaciares. Sin scraper CSV, no se puede confirmar offline.
  Geometría sugiere laguna interior-cráter (no en ring).

### Implicación para S59 flag local_kernel_bg

El flag se asignó S59 por presencia de cuerpos de agua, pero **la métrica decisiva es el
gap empírico**, no la presencia geométrica. Recomendación re-evaluar:

| Vol | Flag actual S59 | Flag sugerido S60 | Justificación |
|---|---|---|---|
| Villarrica | true | **true** (confirmar) | Gap 5.68× confirma necesidad |
| Copahue | true | **false** (revertir) | Gap 1.14×, fix marginal o dañino |
| Llaima | true | **false** (revertir) | Gap 1.01×, fix empeoraría |
| PlanchónPeteroa | true | ??? (audit pendiente) | Sin target CSV, decidir post-reproc |
| Tupungatito | false | false (mantener) | Excluido S59 por ring frío glaciar |

### Riesgo de NO revertir

Cron NRT actualmente NO aplica el fix (flag profile `enable_local_kernel_bg: false` en
`mirova_equivalent.yaml` operacional). El per-vol flag es información pasiva en
`volcanoes.yaml` no activa hasta que se cambie el profile flag o se dispare A/B.

Por tanto **no hay regresión operacional inmediata** por mantener el flag actual S59.
Pero si en S61+ se adopta el fix globalmente, Copahue/Llaima recibirían el fix sin
necesidad y podrían bajar magnitudes en sus matches MIROVA correctos.

## Recomendación S60

1. **Aceptar Villarrica como caso confirmado** del beneficio del fix kernel-bg.
2. **Esperar resultado workflow C** (run 25998365888) para validar Villarrica sobre 5 ALERTAS
   en window 02-20/05-15.
3. **NO disparar A/B Copahue/Llaima por ahora** — la evidencia offline ya sugiere que no
   aportarían. Costo GH Actions evitable.
4. **Revisar `volcanoes.yaml`**: cambiar `local_kernel_bg: false` para Copahue, Llaima,
   PlanchónPeteroa pendiente de su audit (si scraper extiende a este vol).
5. **Si adopción operacional Villarrica al final S60**: cambiar profile flag
   `enable_local_kernel_bg: true` en `mirova_equivalent.yaml` Y mantener per-vol opt-in
   solo para Villarrica.

## Pendientes S61+

- Disparar reproc Copahue + Llaima si scraper CSV se actualiza y queremos confirmación
  empírica (no necesaria si offline ya descarta).
- Reproc PlanchónPeteroa cuando scraper Nicolás cubra ese vol (NO commit RUTINA actualmente).
- Refinamientos `kernel_size=5` o `p25` solo si se quiere converger más a OSF target en
  Villarrica (gap 42% se reducirá pero hay diminishing returns).
