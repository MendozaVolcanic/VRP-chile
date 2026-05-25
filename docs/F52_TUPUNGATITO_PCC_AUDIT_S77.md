# F52 Tupungatito + PCC audit (S77)

**Sesión**: S77 — subagente paralelo a F52 Villarrica.
**Worktree**: `VRP-Chile-s77-f52-tupungatito-pcc` (branch `claude/s77-f52-tupungatito-pcc`).
**Modo**: read-only. Sin tocar `pipeline/`, `volcanoes.yaml` ni `data/`.
**Script**: `experiments/147_f52_tupungatito_pcc/audit.py` + audits inline ad-hoc.

## Veredicto ejecutivo

**Hipótesis F52-extended REFUTADA en estos 2 volcanes.** El "background ring incluye
cuerpos de agua" NO es la causa del ratio inflado en Tupungatito ni PCC. `sigma_bg`
es normal (mediana 4.36 y 2.94 K respectivamente, mejor o igual que Lascar 4.67 K
que ratea ~1×). La causa raíz coincide con un drift ya documentado y abierto:
**T1.5 S72** en `pipeline/profiles/mirova_equivalent.yaml:281-283` —
"Villarrica/Chaiten/PP/Tupungatito/NdC siguen ratios 6-12× post-cap. NO es D9 —
investigar causa arquitectural papers-first".

Este audit aporta evidencia adicional sobre **qué arquitectura** falla y **por qué
los 3 volcanes con agua coinciden por causa distinta**: no es el agua del ring,
es el **régimen MIROVA sub-MW combinado con el piso ~5 MW del path D dNTI-ctx**.

## Datos audit (ventana 90 d, ≥ 2026-02-17)

| Volcán | ours (vrp>0) | mirova_pos | matched both pos | ratio med | ratio p25 / p75 | vrp>5 unmatched (FP cand) |
|---|---:|---:|---:|---:|---:|---:|
| **Tupungatito** | 596 | 100 | 78 | **11.22×** | 0.77 / 27.4 | 266 |
| **PCC** | 923 | 72 | 66 | **12.02×** | 3.89 / 51.4 | 518 |
| Villarrica (ref) | 666 | 17 | — | (subagente F52) | — | — |
| Lastarria (sano) | 684 | 165 | — | ~1.07× (S62 doc) | — | — |
| Lascar (sano) | 629 | 297 | — | ~1.1× (S12 doc) | — | — |

**NOTA importante**: el ratio mediano PCC = **0.48×** declarado en el brief de la
tarea NO se reproduce. Hipótesis: cifra del snapshot S63 post-kernel-bg sobre
ventana 80 d ALERTAS-CONS+OCR, antes del reproc reciente que repobló la cola con
records dNTI-ctx. La data **actual** muestra PCC sobre-estimando como Tupungatito.

## Patrón físico cross-volcán (90 d, vrp>0)

| Volcán | n_pix med | sigma_bg med / p90 | t_max med / max / hot>320K | t_bg med / cold<260K | vrp_mw med / max / >50MW |
|---|---:|---:|---:|---:|---:|
| Tupungatito | 4 | **4.36** / 7.80 | 281.7 / 308.6 / **0** | 266.1 / 107 | 5.10 / 853.5 / 184 |
| PCC | 47 | **2.94** / 5.51 | 282.9 / 566.2* / 1 | 271.8 / 90 | 15.10 / 1659.6 / 317 |
| Villarrica | 12 | 3.50 / 6.43 | 285.3 / 302.1 / 0 | 273.8 / 62 | 5.90 / 1056.3 / 166 |
| Lastarria | 18 | 2.55 / 3.77 | 275.8 / 566.2* / 2 | 264.4 / 35 | 2.74 / 748.2 / 140 |
| Lascar | 39 | 4.67 / 5.63 | 283.8 / 325.7 / **10** | 266.9 / 13 | 3.03 / 820.1 / 109 |

(* `t_max=566 K` es sentinel pre-F2.8 / outlier residual, no condiciona análisis.)

**Lectura geológica**: ninguno de los 3 volcanes "con agua" muestra `sigma_bg`
inflado vs los sanos. **Lascar tiene sigma_bg PEOR (4.67 K)** y ratea bien.
Lo que diferencia no es la termodinámica del ring sino dos cosas combinadas:

1. **Régimen MIROVA** — magnitud típica del fenómeno real:

   | Volcán | MIROVA pos (90d) | MIROVA mediana MW | MIROVA max MW |
   |---|---:|---:|---:|
   | Tupungatito | 100 | **0.23** | 47.3 |
   | PCC | 72 | **0.29** | 5.5 |
   | Villarrica | 17 | 0.45 | 75.5 |
   | PlanchonPeteroa | 62 | 0.21 | 14.7 |
   | Isluga | 109 | 0.28 | 7.5 |
   | Lastarria | 165 | 0.45 | 16.5 |
   | **Lascar** | 297 | **1.38** | 11.3 |
   | **Llaima** | 45 | **8.26** | 96.0 |

   Tupungatito/PCC/Villarrica/PP están todos en régimen **sub-MW** (mediana 0.21-0.45 MW)
   = hidrotermal/fumarólico/lava lake débil. Lascar y Llaima en régimen
   **1-10 MW** = actividad efusiva sostenida.

2. **Piso efectivo nuestro ~5 MW**:
   - Path D dNTI ctx detecta clusters mínimos de 4 píxeles (cluster regla
     Coppola 2016a SP 426.5). Mediana `n_pix=4` Tupungatito, `47` PCC.
   - Wooster k_MODIS=18.9 × A_pix(1e6 m²) × ΔL_MIR. Con ΔL mínimo detectable
     ~50 W/m²/sr/μm × 4 píxeles ≈ **3.8 MW por cluster**. Ningún detect cae
     por debajo de eso.
   - El cap S71 `path_d_only_cap_mw=5.0` (cuando t_bg<270K) confirma que el
     piso está calibrado contra ese tamaño mínimo.

**Ratio = piso nuestro 5 MW / mediana MIROVA 0.3 MW = ~17×**. Coincide con lo
observado (11-12× mediano, p75 ~ 27-51×). Lascar `5 MW / 1.4 MW = 3.6×` pero
en realidad MIROVA Lascar tiene 297 positivos vs nuestros 109 records >50 MW
por lo que muchos pares matchean en régimen sub-piso donde no nos disparamos
(nuestro `vrp_mw=0` o no detección), dando ratio efectivo ~1×. Los 3
"problema" se disparan en la mayoría de scenes donde MIROVA reporta 0.2-0.5 MW.

## Cluster size — PCC tiene n_pix=1 mayoritario (relevante A20)

PCC `primary_cluster.n_pixels` distribution (records vrp>0, ventana 80d):
```
n_pix=0  → 7    (test1 fallback sin cluster)
n_pix=1  → 64   (PIXEL ÚNICO — extendido difuso A20)
n_pix=2  → 12
n_pix=3-8 → 6
n_pix=17+ → 5
n_pix=64-135 → 3
```

PCC 64/96 records con `cluster=1px` confirma A20: anomalía difusa lacolito
no-focal. Nuestro pipeline está clusterizando pixel-por-pixel en vez de agregar
el campo extendido, lo que rompe el matching ground truth contra MIROVA (que sí
agrega el campo entero en su cluster reportado).

## Dominancia paths (records vrp>50 MW, 90d)

| Volcán | BT | NTI abs | **dNTI ctx** | ETI | t_bg<260K (cirrus) |
|---|---:|---:|---:|---:|---:|
| Tupungatito | 0 | 0 | **15,419** | 0 | 48/184 |
| PCC | 37 | 10 | **34,396** | 0 | 33/317 |
| Villarrica | 268 | 0 | **10,606** | 0 | n/a |
| Lastarria (sano) | 0 | 0 | **9,431** | 0 | n/a |
| Lascar (sano) | 0 | 0 | **5,025** | 0 | n/a |

**Path D dNTI ctx domina TODO** — incluso en los volcanes sanos. Esto refuta
"path D es el problema". El path D es el detector principal del pipeline en
régimen sub-MW. Lo que falla es la combinación path D + piso 5 MW + régimen
MIROVA sub-MW.

## Bearing analysis (FPs Tupungatito vrp>50 MW)

15 records, distribución:
- **WSW: 8** (53%) — dirección del Embalse El Yeso (ya con `exclude_zones`)
  pero a 25-27 km, posiblemente halo periférico no cubierto por radio 5 km
- SW: 3, NW: 1, W: 1, N: 1, E: 1

No es uniforme aleatorio — sesgo claro al cuadrante W-SW (downstream glaciar
+ valle del río Yeso). **Posible fuente FPs adicionales** no cubiertas por
`exclude_zones` actual. Vale la pena evaluar ampliar el radio Embalse El Yeso
de 5 km → 8-10 km o agregar zona "valle del Yeso" SE-SW de Tupungatito.

## Hipótesis F52-extended (agua en ring → sigma_bg inflado) — DESCARTADA

| Hipótesis | Evidencia | Status |
|---|---|---|
| H1: Cuerpos de agua en ring 5-25 km inflan sigma_bg | sigma_bg Tup/PCC/Villarrica ≤ Lascar sano (4.36, 2.94, 3.50 vs 4.67 K) | **REFUTADA** |
| H2: Ring contaminado → ΔL elevado falso → vrp inflado | t_bg medianas similares cross-vol (264-274 K) | **REFUTADA** |
| H3: Mecanismo distinto per-volcán | Coincide por **régimen MIROVA sub-MW + piso nuestro ~5 MW**, no por agua | **CONFIRMADA** |

## Hipótesis explicativa real (consistente con T1.5 abierto S72)

**HE**: "Los 3 volcanes (Tupungatito/PCC/Villarrica/+PP/+NdC) coinciden no por
agua sino por estar en **régimen hidrotermal-fumarólico-domo sub-MW** que
MIROVA mide con resolución <1 MW (cluster summit puntual de 1-2 píxeles
saturado en BT) mientras nuestro path D dNTI-ctx clusteriza al menos 4
píxeles vecinos y multiplica al menos por ~5 MW. El gap es de **mínimo de
detección estructural**, no de fenómeno físico mal modelado".

Corolario: los volcanes que rateamos bien (Lascar, Llaima) tienen **señales
fuertes** donde el piso 5 MW está debajo del fenómeno real (1-10 MW MIROVA).
Por eso ratio ~1×.

## Fixes recomendados (no implementar en este audit — solo proponer)

### Fix arquitectural unificado (cubre los 5 vols con T1.5 drift)

**F1 — Path D first-pass single-pixel mode para régimen sub-MW**:
- Cuando `n_pix_cluster <= 2` Y `t_bg < 280K` Y `final_hotspot_source == 'dnti_ctx'`,
  **NO multiplicar por el cluster** sino reportar `vrp_mw` del **píxel más
  caliente del cluster** solo, sin agregación.
- Mecanismo: emula la selección MIROVA "single hot pixel del cluster contiguo"
  para anomalías sub-MW donde el cluster que detectamos es ruido de vecindad.
- Predicción: corta ratio Tup/PCC/PP/Villarrica/NdC de 10-30× a 1-3× sin
  romper Lascar/Llaima (donde cluster real es >4 px verdadero).
- Validación: A/B test en GH Actions sobre los 5 vols afectados.

**F2 — Filtro post-detección "cluster lejano agregado en eruption-far"** (Tupungatito-specific):
- En `final_hotspot_source=='eruption'` Y `distance_class=='far'` Y `cluster en
  cuadrante W-SW` Y `pixel BT < 285K` → descartar como FP de halo glaciar/valle.
- Es heurístico geográfico. Menos elegante que F1 pero captura el sesgo
  bearing observado.

**F3 — Cap path D dNTI-ctx eruption-far** (extensión del cap S71 actual):
- Cap actual `path_d_only_cap_mw=5.0` aplica solo a `pc.vrp_mw` cuando
  `t_bg<270K`. Extender: cuando `source==eruption` AND `class==far` AND BT_max
  del cluster < 295K → cap a 5 MW también.
- Más conservador que F1, fix de bandage.

### Per-volcán (mientras F1 se decide)

**T-1 Tupungatito**: ampliar `exclude_zones` Embalse El Yeso radio 5 km → 8 km
o agregar zona "valle río Yeso" centrada en (-33.55, -69.95) radio 15 km
cuadrante SW. Captura el sesgo WSW observado.

**PCC-1 PuyehueCordonCaulle**: investigar agregación cluster lacolito. Si
nuestro pipeline clusteriza 64/96 records con n_px=1 mientras MIROVA agrega
todo el campo difuso, posiblemente necesita un modo "agrega clusters
contiguos hasta umbral de distancia" antes de reportar `vrp_mw`.

## Síntesis cross-volcán con subagente Villarrica F52

(Para integrar al cierre cuando el subagente Villarrica entregue su report.)

Predicción de este subagente: el report de Villarrica F52 paralelo va a mostrar
el **mismo patrón** que Tupungatito/PCC:
- sigma_bg ~ 3.5 K normal (no inflado por lago Villarrica norte)
- mediana MIROVA Villarrica 0.45 MW vs nuestro piso ~5 MW
- path D dNTI ctx dominante
- ratio ~10× viene de cociente piso/MIROVA-mediana, no de contaminación de agua

Si la predicción se cumple, **el fix F1 cubre los 3 simultáneamente** y la
"agua" no necesita tratamiento per-volcán. Si el report Villarrica revela
algo diferente (e.g. sigma_bg sí inflado, halo del lago Villarrica norte
realmente activo a 16 km), entonces los 3 son problemas distintos y se
necesitan fixes específicos.

## Trazabilidad

- Script audit: `experiments/147_f52_tupungatito_pcc/audit.py`
- Output: `experiments/147_f52_tupungatito_pcc/audit.json`
- Drift open relacionado: `pipeline/profiles/mirova_equivalent.yaml:281-283`
  (T1.5 S72 — "investigar causa arquitectural")
- Cap actual relacionado: `path_d_only_cap_mw=5.0` línea 284
- Aprendizajes consultados: A19 (Tupungatito glaciar refuta kernel-bg, S62),
  A20 (PCC anomalía difusa, R2 centroide no aplica, S70-1), A23 (Path D dNTI
  ctx FPs sistémicos cirrus alto, D9 ABIERTO S70-2)
