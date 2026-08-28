

# Resultados de la noche — 2026-08-28 05:02 UTC

Orquestador: `scripts/orquestar_noche_s124.sh`. Plan: `docs/superpowers/plans/2026-08-27-plan-reprocesos-s124-s125.md`.

## Brazo B — grilla UTM + kernel de vecinos global (la hipotesis central)

Criterio pre-registrado en `pipeline/profiles/_f70_b.yaml` (escrito antes de correr, A66).
  [05:03] lanzado run 33143570963 — https://github.com/MendozaVolcanic/VRP-chile/actions/runs/33143570963
  [07:10] brazo B -> success

### Lectura apareada (brazo B vs control)

```
BRAZO _f70_b vs control (mirova_equivalent), ventana 2026-06-25..2026-08-24
volcan                pasadas  ratio med  aparecen  desaparecen  d.dist med
----------------------------------------------------------------------------
Lascar                    552       1.00        11           13      -0.01km
Isluga                    530       1.00        20           21      -0.03km
Lastarria                 556       1.00         7           23       0.00km
Llaima                    674       1.00        22           28      -0.05km
Copahue                   652       1.00        21           31      -0.03km
Tupungatito               614       1.00        18           25      -0.03km
NevadosDeChillan          664       1.00        21           11      -0.08km
Villarrica                682       1.00        25           40      -0.04km
Chaiten                   732       1.00        24           26      -0.02km
PlanchonPeteroa           621       1.00        14           22      -0.01km
PuyehueCordonCaulle       695       0.98        35           25       0.04km

TOTAL aparecen: 218   desaparecen: 265

ratio = VRP brazo / VRP control en pasadas donde AMBOS detectan.
1.00 = la grilla no cambia la magnitud. d.dist = migracion del cluster (A61).
BRAZO _f70_b vs control (mirova_equivalent), ventana 2026-06-25..2026-08-24
volcan                pasadas  ratio med  aparecen  desaparecen  d.dist med
----------------------------------------------------------------------------
Lascar                    552       1.00        11           13      -0.01km
Isluga                    530       1.00        20           21      -0.03km
Lastarria                 556       1.00         7           23       0.00km
Llaima                    674       1.00        22           28      -0.05km
Copahue                   652       1.00        21           31      -0.03km
Tupungatito               614       1.00        18           25      -0.03km
NevadosDeChillan          664       1.00        21           11      -0.08km
Villarrica                682       1.00        25           40      -0.04km
Chaiten                   732       1.00        24           26      -0.02km
PlanchonPeteroa           621       1.00        14           22      -0.01km
PuyehueCordonCaulle       695       0.98        35           25       0.04km

TOTAL aparecen: 218   desaparecen: 265

ratio = VRP brazo / VRP control en pasadas donde AMBOS detectan.
1.00 = la grilla no cambia la magnitud. d.dist = migracion del cluster (A61).
```

### Los 4 brazos, ratio mediano por volcan

```
Ratio mediano vs MIROVA (banda de la MEDIANA (0.7, 1.4)), 2026-06-25..2026-08-24

volcan                  n   control         A         B         C
------------------------------------------------------------------
Lascar                 32     0.47      0.46      0.58      0.58 
Isluga                 40     0.70*     0.69      0.81*     0.81*
Lastarria              27     0.36      0.34      0.34         --
Copahue                 1     1.02*     1.07*     1.07*     1.02*
Tupungatito            17     0.81*     0.82*     0.81*     0.81*
NevadosDeChillan        2     1.31*     1.31*     1.31*     1.31*
Villarrica              9     0.72*     0.72*     0.72*        --
Chaiten                11     1.29*     1.26*     1.26*        --
PlanchonPeteroa        11     0.96*     0.96*     0.96*        --

* = dentro de banda. JUEZ del criterio F70: Tupungatito (B debe
curarlo donde C no). GUARDA: Lastarria no debe romperse (A84).
```

## NdC experimental v2 (rehecho — el anterior salio con el merge roto)

El merge por trozos resucitaba meses sin reprocesar (fix commit del 27-ago).
  [07:10] lanzado run 33150492889 — https://github.com/MendozaVolcanic/VRP-chile/actions/runs/33150492889
  [08:17] NdC v2 -> success

### Se reproceso de verdad esta vez? (el test que destapo el bug)

```
records  antes: 518   ahora: 518   comunes: 518

records IDENTICOS byte a byte, por mes (100% = ese mes NO se reproceso):
   2026-05:  134/ 138 =  97%
   2026-06:    8/ 132 =   6%
   2026-07:   14/ 131 =  11%
   2026-08:   23/ 117 =  20%

VEREDICTO: todos los meses cambiaron. El reproceso si toco la data.
```

### Figuras regeneradas con la serie completa

C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s124_ndc_focus\plot_simple.py:294: UserWarning: This figure includes Axes that are not compatible with tight_layout, so results might be incorrect.
  fig.tight_layout(rect=(0, 0.055, 1, 1))
figura: C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s124_ndc_focus\ndc_simple_s124.png

MIROVA alertas V375: 3  |  réplica noches: 20  |  foco noches: 23
foco: mediana 0.045 MW, max 0.105
  coinciden 2026-06-16: MIROVA 0.06 vs foco 0.071
  coinciden 2026-08-18: MIROVA 0.07 vs foco 0.105
  coinciden 2026-08-20: MIROVA 0.09 vs foco 0.100
alertas MIROVA sin foco nuestro: []
figura: C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s124_ndc_focus\ndc_mapa_s124.png
