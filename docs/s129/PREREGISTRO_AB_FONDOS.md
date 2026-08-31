# Pre-registro · A/B de los dos fondos autorreferentes (S129)

> Congelado ANTES de lanzar el reproceso. Si algo de acá cambia después de ver
> resultados, se anota el cambio y la razón — no se reescribe.

## Brazos

| brazo | perfil | único flag distinto |
|---|---|---|
| control | `_s129_ab_control` | ninguno (clon reprocesado del operacional) |
| A · pool | `_s129_ab_pool` | `enable_test1_k1_retire_from_hot_mask: true` |
| B · fondo magnitud | `_s129_ab_bgmag` | `enable_test1_k1_bg_exclude: true` |

Ventana: 2026-03-01 a 2026-08-24. Volcanes: Lascar, Lastarria, Villarrica,
Tupungatito, Chaiten. Sensor primario de lectura: VIIRS375.

## Las cuatro firmas, con su predicción

| # | firma | cómo se mide | predicción A (pool) | predicción B (fondo) |
|---|---|---|---|---|
| F1 | ratio mediano vs MIROVA | un par por noche, máximo de ambos lados, sobre la INTERSECCIÓN de pasadas de los 3 brazos | sube | sube |
| F2 | nº de detecciones con `pc.vrp_mw > 0` | conteo sobre la intersección | **sube** | **no cambia** (±2 %) |
| F3 | dependencia del régimen: ratio en el tercil DÉBIL menos ratio en el tercil FUERTE de `t_max − t_bg` | por volcán y agregado | **la brecha se achica** | **la brecha no cambia** |
| F4 | umbral efectivo `diag_eff_threshold_k` mediano | por volcán | **baja** | no cambia |

F2 y F3 son las que atribuyen. Si los dos brazos mueven F1 pero sólo A mueve F2 y
F3, la atribución es limpia.

## Criterios de decisión, en orden

1. **ADOPTAR** un brazo si: F1 sube, el nº de volcanes dentro de la banda de
   paridad [0,7 – 1,4] **no baja**, y no pierde detecciones que MIROVA confirma
   (FN nuevos = 0 sobre noches con contraparte).
2. **NO ADOPTAR** si pierde alguna noche MIROVA-confirmada, aunque mejore F1.
   Recall antes que paridad, que es la prioridad declarada de `mirova_equivalent`.
3. **INCONCLUSO** si los IC95 de F1 se solapan entre control y brazo. Se reporta
   como inconcluso, no se fuerza.
4. Los dos brazos se evalúan **por separado**. Este A/B no prueba la combinación;
   si los dos pasan, la combinación necesita su propia corrida (puede interactuar:
   A sube el nº de píxeles y B cambia el fondo de cada uno).

## Lo que este A/B NO responde

- No prueba el remuestreo ni la suma vs clúster (planes aparte).
- No vale para MODIS fuera de Láscar: los otros diez tienen **cero** alertas MODIS
  nocturnas en el ground truth, así que cualquier veredicto MODIS ahí es INDEFINIDO,
  no débil.
- A18: el reproceso vuelve a correr la selección de clúster desde cero. Ningún
  preview offline predice esto.
