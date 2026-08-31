# S130 · El A/B de los fondos no puede medir nada, y la razón es física

El A/B de los dos fondos autorreferentes que S129 dejó corriendo **no arroja un
veredicto negativo: no arroja veredicto**. Los brazos no difieren porque el mecanismo
que activan casi no tiene sobre qué actuar en nuestros volcanes.

Esto no invalida el diseño del experimento —el pre-registro y las cuatro firmas están
bien planteados— sino su **subconjunto**, y de paso dimensiona el GAP #A.

## Cómo apareció

Aplicando A16 se corrió la lectura sobre el **chunk 1**, ya rescatado, mientras el
chunk 2 seguía en CI. Las cuatro firmas dieron idénticas hasta el tercer decimal:

| firma | control | pool | bgmag |
|---|---|---|---|
| F1 ratio mediano | 0,718 | 0,718 | 0,718 |
| F2 n detecciones | 443 | 443 | 443 |
| F4 umbral mediano (K) | 280,11 | 280,11 | 280,11 |
| F3 brecha débil−fuerte | 0,046 | 0,046 | 0,046 |

Un empate perfecto en cuatro firmas independientes no es un empate: es la firma de que
los brazos son el mismo brazo. Control de instrumento, entonces, antes de creerle a la
sonda — comparación cruda record por record sobre 4.612 registros:

- **`pool` vs control: cero diferencias.** Mismos records, mismo `vrp_mw`, mismo
  `primary_cluster.vrp_mw`, mismo `diag_eff_threshold_k`.
- **`bgmag` vs control: 3 records**, y sólo en `diag_eff_threshold_k`. Ninguno en el VRP.

## Lo que NO era

Se descartaron las dos explicaciones baratas antes de buscar la real:

1. **No es el A89 de S129** (flags escritos bajo la sección equivocada). Leyendo
   `pipeline.profile` —nunca el YAML— los tres perfiles resuelven bien:
   `_s129_ab_pool` tiene `ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK = True` y
   `_s129_ab_bgmag` tiene `ENABLE_TEST1_K1_BG_EXCLUDE = True`, con el control en `False`
   para los dos.
2. **No es que el código ignore los flags.** Los tres procesadores los consumen
   (`process_modis.py`, `process_viirs.py`, `process_viirs_mod.py`).

Y los archivos de los tres brazos tienen hashes y tamaños distintos: el reproceso
corrió de verdad, con perfiles distintos.

## Lo que era: no hay sustrato

Los dos flags operan sobre los píxeles que cruzan el **umbral K1 de Coppola
(NTI > −0,8 de noche)**:

- `enable_test1_k1_retire_from_hot_mask` pasa `nti_path_hot` como máscara de fondo no
  apto. Máscara vacía, efecto nulo.
- `enable_test1_k1_bg_exclude` excluye esos mismos píxeles del pool del fondo. Si no hay
  ninguno, el fondo es idéntico.

Cuántas pasadas tienen al menos un píxel K1
(`experiments/_s130_ab_sustrato/medir_sustrato_k1.py`):

| sensor | records | con píxel K1 | |
|---|---|---|---|
| MODIS | 11.717 | 11 | **0,09 %** |
| VIIRS750 | 22.920 | 28 | **0,12 %** |
| VIIRS375 | 23.105 | 315 | **1,36 %** |

Y por volcán, que es donde se ve el problema del diseño:

| volcán | % con K1 | volcán | % con K1 |
|---|---|---|---|
| **Láscar** | **4,82** | Copahue | 0,07 |
| Nevados de Chillán | 1,44 | Villarrica | 0,05 |
| Isluga | 0,38 | Tupungatito | 0,04 |
| Planchón-Peteroa | 0,31 | PCC | 0,02 |
| Llaima | 0,16 | **Chaitén** | **0,00** |
| Lastarria | 0,13 | | |

El A/B eligió cinco volcanes —Chaitén, Láscar, Lastarria, Tupungatito, Villarrica— de
los cuales **cuatro no tienen sustrato**. Chaitén tiene exactamente cero en 5.865
records. El único con material es Láscar.

## Por qué, físicamente

El NTI de estos aparatos vive pegado a su piso, alrededor de −0,9, que es justamente lo
que **A80** describe para señal débil sobre nieve: el píxel mezcla roca tibia con nieve
y el índice normalizado se queda abajo. El umbral K1 = −0,8 fue calibrado contra
volcanes con **lava expuesta**, donde el sub-píxel incandescente sí empuja el MIR lo
suficiente. En los nuestros ese régimen es la excepción, no la regla — y Láscar, el
único con cráter caliente persistente y sin cobertura nival, es el único que lo cruza
con alguna frecuencia.

## Qué significa para el GAP #A

El GAP #A —el retiro de los píxeles Test 1 K1 del pool μ/σ, Coppola 2016a §298-300, que
S128 reabrió con guard— **sigue siendo una divergencia real de fidelidad literal**. Esto
no lo cierra.

Lo que hace es **dimensionarlo**: su impacto empírico sobre nuestro corpus toca el
**0,09 %** de las pasadas MODIS y el **1,36 %** de las VIIRS375. Es una divergencia
correcta de documentar y de bajo rendimiento para invertir en cerrarla, salvo que el
objetivo sea la fidelidad literal por sí misma — que en este proyecto es un objetivo
legítimo, pero distinto de mejorar la paridad.

## Si se quisiera medir de verdad

No repetir el mismo A/B sobre más meses: el sustrato es **estructural**, no estacional.
Un experimento con poder estadístico tendría que restringirse a las pasadas **con K1
presente** —Láscar aporta 219 de las 315 de VIIRS375— y medir sobre ellas, aceptando
que el n es chico y que el resultado no se extrapola a los otros diez volcanes.

Es decir: la pregunta del A/B tiene respuesta sólo en Láscar, y allí con n≈219.

## La lección

**Antes de gastar horas de CI en un A/B, medir cuántas veces el mecanismo bajo prueba
tiene ocasión de actuar.** Es el control de instrumento aplicado al diseño y no sólo a
la sonda: la pregunta previa a *¿este flag mejora algo?* es *¿este flag llega a
ejecutarse alguna vez?*, y se responde con un barrido de un diagnóstico ya persistido,
en un minuto y sin reprocesar nada.

El costo de no hacerlo, esta vez: dos chunks de reproceso, quince jobs, más de cinco
horas de CI, para tres records de diferencia en un campo de diagnóstico.
