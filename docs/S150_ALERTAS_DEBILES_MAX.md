# S150: las alertas de MIROVA que la conectiva `max` pierde, y por qué

> **Estado: investigación de un agente, SIN verificador con contexto limpio todavía.** Sus hipótesis
> orientan las próximas pruebas, que llevan su propio pre-registro y verificador antes de despacharse.

> Investigación de solo lectura. Brazo B = sin Test 1, conectiva `min` (perfil `_s146_ab_sin_test1`); brazo F = sin Test 1,
> conectiva `max` (perfil `_s147_ab_sin_test1_max`). Abril a agosto de 2026 (agosto hasta el 27), runs 35639417826 y
> 37823348991 (abril), 35599902448, 35675490175, 35728617326, 35759688167. Referencias congeladas de
> `experiments/_s149_prereg_invierno/_congelado/<mes>/`. Scripts y salidas en `experiments/_s150_debiles/`.
> Todo número de este documento sale de una salida guardada ahí; ninguno está transcrito de otro informe.

## 0. En una pantalla

**El fenómeno.** De noche, un foco débil (un lago de lava chico, una fumarola caliente, un domo) sube apenas la radiancia
MIR de un píxel sobre sus ocho vecinos. Con `min` basta que ese exceso supere un piso fijo (C1 = 0,003 en dNTI y en
dETI). Con `max` además tiene que destacar contra la variabilidad de toda la escena: más de 5 desviaciones (μ + 5σ) en
la cumbre. En una escena tranquila las dos exigencias son parecidas; en una escena ruidosa (nubes, nieve, borde del
barrido) la segunda sube y se come los focos que están en el límite.

**Lo medido.**
1. F pierde **46** de las **1.143** alertas de MIROVA que B publica (VIIRS 375: 42 de 988; VIIRS 750: 4 de 155). Sin las
   5 filas OCR de Suomi NPP con la imagen de otra pasada, **41**. Con etiqueta confiable (tabla, u OCR desde el
   2026-06-13, A119), **36** (32 de VIIRS 375 y 4 de VIIRS 750).
2. **Qué las rechaza.** En las 42 de VIIRS 375 el umbral de F en la cumbre es el estadístico μ + 5σ, entre 1,3 y 3,7
   veces C1 (mediana 2,49 veces en las perdidas contra 2,04 en las conservadas). Dos caminos distintos:
   - **27** las publicaba B con píxeles del primer pase: pasaron C1 en dNTI y en dETI y la compuerta de 3 K, y en F no
     pasaron μ + 5σ en al menos uno de los dos tests. **Cuál de los dos tests falla no se puede saber**: los records no
     guardan dNTI ni dETI por píxel.
   - **15** las publicaba B **sólo por el segundo pase**, con el píxel menos de 3 K sobre el fondo: la compuerta de
     temperatura del primer pase (D22, que el paper no tiene) las bloquea en **los dos** brazos. B las rescata con un
     segundo pase sin condicionar y sin compuerta; F también corre ese segundo pase, pero con μ₂ + 5σ₂ calculados sin
     los filtros de no aptos (D26), y μ₂, σ₂ no se persisten.
3. **El patrón.** Dentro del tramo débil (MIROVA bajo 0,10 MW) lo que separa perdidas de conservadas es **la σ de la
   escena**, no la debilidad del píxel: AUC 0,80 (σ dNTI) y 0,81 (σ dETI), y 0,85 ponderado dentro de tramos de
   magnitud de B. El cenit separa menos (0,70) y el satélite nada (12 a 13 % en los tres). Pero las perdidas son
   **indistinguibles del residual que `max` apaga con razón** en los mismos campos (σ dNTI AUC 0,48; exceso de BT 0,52;
   camino 0,53): ningún umbral sobre lo que guarda el record separa unas del otro.
4. **En la imagen de MIROVA de esas mismas pasadas** (10 perdidas con TIF), el píxel también está en el límite: el
   contraste máximo en un disco de 3 km es mediana **4,6 σ**, contra **10,0** en las conservadas y **3,1** en el
   residual; sólo 3 de 10 superan 5 σ. Es un proxy en radiancia MIR sola, no en NTI.

**Hipótesis con más evidencia, y la medición que decide cada una** (§6): (1) nuestra σ de escena es más alta que la de
MIROVA justo donde perdemos, por cómo se arma el campo sobre el que se mide (remuestreo interpolado de MIROVA, D17, y el
pozo de σ del segundo pase, D26); (2) la compuerta D22 más el segundo pase sin condicionar hacen depender 15 de las 42
de un paso que el paper no tiene; (3) MIROVA no decide estos casos límite con 5 σ de su propia escena (o lee la
conectiva como `min`, o su C2 efectivo para VIIRS es otro). Las tres se deciden con **una sonda por píxel** (§7) que
nadie ha despachado.

## 1. Instrumento, denominador y controles

- **Tabla por pasada**: `experiments/_s149_prereg_invierno/armar_tabla.py`, el mismo del pre-registro, con el predicado
  del tablero ejecutado con node. La corrí sobre mis extracciones (`extraer_y_tabular.py`, `git archive` con ruta a un
  temporal fuera del repo).
- **Denominador**: alertas de MIROVA (etiqueta `pos`) de VIIRS 375 y 750, abril a agosto, en pasadas que los dos
  brazos procesaron y que **B publica**. Pérdida = F no publica esa pasada.
- **Control de reproducción** (`perdidas_max.py`): mis conteos dan B 988 / F conserva 946 en VIIRS 375 y 155 / 151 en
  VIIRS 750, idénticos a `experiments/_s149_prereg_invierno/resultados/agregado_abril_agosto.txt`. Las pasadas por mes
  (3.433, 3.682, 3.520, 3.497, 3.135) coinciden con las de los resultados del pre-registro en abril, junio, julio y
  agosto (mayo no imprime ese total en su archivo de resultado). Si el pareo con los records
  crudos estuviera roto, estos conteos no coincidirían.
- **μ y σ no dependen de la conectiva**: en las 1.143 pasadas, `diag_mu_dnti`, `diag_sd_dnti`, `diag_mu_deti` y
  `diag_sd_deti` de B y de F son idénticos (0 distintos). O sea que el umbral de F se puede reconstruir desde el record
  de B: μ + 5σ en la cumbre (`pipeline/detection_context.py:525-535`, C1 = 0,003, C2 = 5; C1 = 0,010, C2 = 10 en la
  escena, leídos de `pipeline.profile` con `VRP_PROFILE=_s147_ab_sin_test1_max`).
- **Lo que no verifiqué**: que el job de GitHub haya aplicado esos valores (los logs no imprimen los flags; mismo SIN
  VERIFICAR que `S150_RESULTADO_MESES.md` §6). Leí el perfil de hoy, no el del día del despacho. La coincidencia de μ y
  σ entre brazos y la caída de publicación en negativos son consistentes con que la única diferencia fue la conectiva.

## 2. La lista completa (46)

Columnas: «umbral F» es μ + 5σ de la cumbre con el μ y la σ del record (μ es del orden de 1e-5, despreciable; la σ es
el umbral dividido por 5). «B: px 1.er / 2.o pase» son conteos de **toda la escena** (`diag_n_first_pass_pixels`,
`diag_n_second_pass_recapture`), no del píxel publicado. «BT píxel - t_bg» es el máximo de los píxeles publicados por B
menos el fondo del anillo (`t_bg_k`), que es la misma resta que usa la compuerta de 3 K. «F: px» es el total de píxeles
de F en la escena y la distancia de su cúmulo al cráter. Generada por `listar.py filas.json --md` (`tabla_perdidas.md`).

| # | volcán | sensor | pasada UTC | sat. | MIROVA MW | origen | cenit ° | t_bg K | σ BT anillo K | umbral F dNTI | umbral F dETI | B: px 1.er / 2.o pase | B: VRP cúmulo MW, dist km | BT píxel - t_bg K | F: px, cúmulo dist km |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Tupungatito | VIIRS375 | 2026-04-06 06:30 | SNPP | 0.09 | tabla | 59.0 | 266.4 | 4.46 | 0.0075 | 0.0052 | 1 / 2 | 0.006, 0.2 | 5.1 | 0, - |
| 2 | Chaiten | VIIRS375 | 2026-04-07 04:54 | N20 | 0.08 | tabla | 53.1 | 266.7 | 10.67 | 0.0096 | 0.0077 | 4 / 0 | 0.089, 0.3 | 14.9 | 0, - |
| 3 | PlanchonPeteroa | VIIRS375 | 2026-04-10 05:36 | N20 | 0.06 | tabla | 7.6 | 275.3 | 4.42 | 0.0075 | 0.0032 | 0 / 1 | 0.060, 0.5 | -1.1 | 0, - |
| 4 | PuyehueCordonCaulle | VIIRS375 | 2026-04-10 06:30 | N21 | 0.08 | tabla | 55.0 | 278.8 | 3.35 | 0.0104 | 0.0058 | 3 / 45 | 0.077, 0.3 | 5.1 | 0, - |
| 5 | Isluga | VIIRS375 | 2026-04-14 06:00 | N20 | 0.08 | tabla | 20.3 | 268.7 | 3.06 | 0.0039 | 0.0037 | 0 / 2 | 0.018, 3.7 | 1.4 | 1, 1.0 |
| 6 | Tupungatito | VIIRS375 | 2026-04-22 06:00 | N21 | 0.03 | tabla | 33.4 | 254.2 | 5.99 | 0.0068 | 0.0036 | 0 / 1 | 0.018, 0.1 | 2.5 | 0, - |
| 7 | PlanchonPeteroa | VIIRS375 | 2026-04-23 06:12 | SNPP | 0.08 | solo OCR | 40.8 | 267.9 | 5.99 | 0.0081 | 0.0044 | 1 / 1 | 0.035, 0.6 | 22.3 | 1, 19.3 |
| 8 | Lastarria | VIIRS375 | 2026-05-02 05:06 | SNPP | 2.36 | solo OCR (imagen de otra pasada) | 59.5 | 263.1 | 2.92 | 0.0098 | 0.0089 | 1 / 1 | 0.033, 1.0 | 41.0 | 1, 19.5 |
| 9 | PuyehueCordonCaulle | VIIRS375 | 2026-05-03 05:06 | N20 | 0.08 | tabla | 46.0 | 270.2 | 6.07 | 0.0083 | 0.0051 | 5 / 19 | 0.058, 0.1 | 10.2 | 0, - |
| 10 | Tupungatito | VIIRS375 | 2026-05-03 06:30 | SNPP | 0.06 | solo OCR | 54.3 | 265.7 | 5.20 | 0.0070 | 0.0050 | 0 / 2 | 0.015, 6.0 | 1.3 | 0, - |
| 11 | PuyehueCordonCaulle | VIIRS375 | 2026-05-05 05:54 | SNPP | 0.23 | solo OCR | 3.9 | 241.9 | 9.89 | 0.0079 | 0.0068 | 2 / 15 | 0.012, 8.8 | 30.1 | 1, 22.7 |
| 12 | Tupungatito | VIIRS375 | 2026-05-18 06:48 | SNPP | 0.05 | tabla | 66.7 | 258.7 | 4.96 | 0.0078 | 0.0055 | 2 / 1 | 0.054, 4.0 | 5.7 | 0, - |
| 13 | Chaiten | VIIRS375 | 2026-05-19 05:06 | N20 | 0.07 | tabla | 43.8 | 278.6 | 3.46 | 0.0080 | 0.0038 | 0 / 1 | 0.068, 0.2 | 2.5 | 0, - |
| 14 | Chaiten | VIIRS375 | 2026-05-19 06:48 | N20 | 0.05 | tabla | 65.6 | 278.6 | 2.96 | 0.0082 | 0.0052 | 0 / 2 | 0.053, 0.4 | 1.1 | 0, - |
| 15 | Tupungatito | VIIRS375 | 2026-05-23 04:42 | N21 | 0.12 | tabla | 66.4 | 259.3 | 5.46 | 0.0078 | 0.0053 | 1 / 4 | 0.076, 7.0 | 7.5 | 0, - |
| 16 | Tupungatito | VIIRS375 | 2026-05-24 06:36 | SNPP | 0.05 | tabla | 59.3 | 260.2 | 6.04 | 0.0075 | 0.0055 | 0 / 3 | 0.021, 0.2 | 2.2 | 0, - |
| 17 | Isluga | VIIRS375 | 2026-05-25 06:30 | N20 | 0.04 | tabla | 59.2 | 265.2 | 2.15 | 0.0064 | 0.0049 | 0 / 1 | 0.014, 0.8 | 1.2 | 0, - |
| 18 | Isluga | VIIRS375 | 2026-05-29 04:54 | SNPP | 0.86 | solo OCR (imagen de otra pasada) | 69.0 | 265.1 | 2.97 | 0.0084 | 0.0072 | 1 / 2 | 0.013, 4.9 | 24.3 | 1, 18.6 |
| 19 | PuyehueCordonCaulle | VIIRS375 | 2026-05-31 04:42 | N20 | 0.02 | tabla | 62.7 | 252.1 | 10.51 | 0.0093 | 0.0092 | 31 / 170 | 0.014, 0.6 | 23.8 | 0, - |
| 20 | Lastarria | VIIRS375 | 2026-06-02 06:30 | N21 | 0.03 | tabla | 62.9 | 256.2 | 5.23 | 0.0059 | 0.0054 | 0 / 2 | 0.024, 1.0 | 2.6 | 0, - |
| 21 | Copahue | VIIRS375 | 2026-06-10 04:36 | SNPP | 0.05 | solo OCR | 69.1 | 262.3 | 3.43 | 0.0078 | 0.0062 | 1 / 3 | 0.013, 3.2 | 4.5 | 0, - |
| 22 | PuyehueCordonCaulle | VIIRS375 | 2026-06-12 05:06 | N21 | 0.12 | solo OCR | 46.6 | 226.7 | 4.55 | 0.0066 | 0.0066 | 25 / 9 | 0.010, 2.7 | 34.2 | 1, 23.5 |
| 23 | Lastarria | VIIRS375 | 2026-06-17 05:06 | N21 | 0.46 | solo OCR | 50.2 | 260.3 | 2.84 | 0.0064 | 0.0045 | 5 / 0 | 0.038, 2.3 | 22.0 | 4, 7.1 |
| 24 | PlanchonPeteroa | VIIRS375 | 2026-06-17 05:12 | N21 | 0.04 | solo OCR | 43.6 | 270.8 | 6.44 | 0.0083 | 0.0041 | 0 / 2 | 0.066, 0.4 | 0.2 | 0, - |
| 25 | Chaiten | VIIRS375 | 2026-06-17 05:12 | N21 | 0.19 | solo OCR | 38.3 | 275.9 | 4.59 | 0.0085 | 0.0046 | 2 / 0 | 0.098, 0.3 | 4.0 | 0, - |
| 26 | PlanchonPeteroa | VIIRS375 | 2026-06-17 06:06 | N20 | 0.07 | tabla | 32.8 | 268.9 | 6.33 | 0.0110 | 0.0104 | 3 / 4 | 0.087, 0.5 | 4.1 | 0, - |
| 27 | PuyehueCordonCaulle | VIIRS375 | 2026-06-19 04:36 | N21 | 0.03 | solo OCR | 66.0 | 254.8 | 4.92 | 0.0062 | 0.0064 | 12 / 14 | 0.037, 0.4 | 9.7 | 0, - |
| 28 | Lascar | VIIRS375 | 2026-06-25 04:54 | SNPP | 0.51 | solo OCR (imagen de otra pasada) | 66.9 | 261.7 | 3.71 | 0.0068 | 0.0062 | 1 / 4 | 0.014, 0.2 | 22.4 | 1, 21.3 |
| 29 | Lastarria | VIIRS375 | 2026-06-30 06:42 | SNPP | 0.07 | tabla | 63.7 | 257.4 | 3.27 | 0.0064 | 0.0055 | 0 / 2 | 0.032, 1.1 | 3.0 | 0, - |
| 30 | NevadosDeChillan | VIIRS375 | 2026-07-15 04:48 | N21 | 0.02 | tabla | 62.3 | 227.1 | 6.27 | 0.0084 | 0.0084 | 8 / 7 | 0.003, 0.7 | 7.5 | 0, - |
| 31 | Tupungatito | VIIRS375 | 2026-07-21 04:30 | N21 | 0.01 | tabla | 69.0 | 235.2 | 6.70 | 0.0071 | 0.0071 | 1 / 0 | 0.011, 1.6 | 4.2 | 0, - |
| 32 | Copahue | VIIRS375 | 2026-07-27 05:18 | N20 | 0.04 | tabla | 40.3 | 247.2 | 5.00 | 0.0061 | 0.0055 | 2 / 0 | 0.046, 2.7 | 8.1 | 1, 26.0 |
| 33 | Lastarria | VIIRS375 | 2026-08-04 05:06 | N21 | 0.20 | solo OCR | 49.4 | 258.7 | 3.36 | 0.0056 | 0.0037 | 1 / 2 | 0.027, 0.9 | 2.5 | 1, 28.4 |
| 34 | PlanchonPeteroa | VIIRS375 | 2026-08-14 04:36 | N20 | 0.02 | solo OCR | 68.1 | 251.3 | 6.17 | 0.0099 | 0.0075 | 2 / 2 | 0.033, 2.5 | 3.3 | 0, - |
| 35 | Lascar | VIIRS375 | 2026-08-17 05:00 | SNPP | 0.60 | solo OCR (imagen de otra pasada) | 63.4 | 242.7 | 5.91 | 0.0097 | 0.0096 | 4 / 3 | 0.005, 1.5 | 5.8 | 2, 24.6 |
| 36 | Chaiten | VIIRS375 | 2026-08-18 05:48 | N21 | 0.06 | tabla | 14.8 | 266.7 | 3.70 | 0.0041 | 0.0047 | 0 / 2 | 0.033, 0.2 | 1.6 | 0, - |
| 37 | Lastarria | VIIRS375 | 2026-08-21 05:24 | SNPP | 0.15 | solo OCR | 42.2 | 256.3 | 3.64 | 0.0070 | 0.0045 | 4 / 1 | 0.016, 1.0 | 12.9 | 1, 5.9 |
| 38 | Tupungatito | VIIRS375 | 2026-08-21 06:30 | N21 | 0.04 | tabla | 63.0 | 257.9 | 4.40 | 0.0068 | 0.0045 | 0 / 3 | 0.002, 0.2 | 0.2 | 1, 0.2 |
| 39 | Lascar | VIIRS375 | 2026-08-22 05:06 | SNPP | 1.65 | solo OCR (imagen de otra pasada) | 59.2 | 261.6 | 6.01 | 0.0085 | 0.0074 | 2 / 3 | 0.018, 0.3 | 27.3 | 2, 8.2 |
| 40 | PuyehueCordonCaulle | VIIRS375 | 2026-08-22 05:30 | N20 | 0.06 | tabla | 24.0 | 245.1 | 9.64 | 0.0056 | 0.0054 | 3 / 7 | 0.031, 0.3 | 12.4 | 0, - |
| 41 | Chaiten | VIIRS375 | 2026-08-23 06:54 | N20 | 0.05 | tabla | 66.1 | 275.4 | 3.96 | 0.0073 | 0.0056 | 0 / 1 | 0.060, 0.4 | 0.5 | 0, - |
| 42 | PlanchonPeteroa | VIIRS375 | 2026-08-24 06:12 | SNPP | 0.04 | solo OCR | 33.1 | 268.2 | 4.67 | 0.0063 | 0.0041 | 0 / 2 | 0.047, 0.5 | 2.5 | 0, - |
| 43 | PuyehueCordonCaulle | VIIRS750 | 2026-04-30 06:06 | N20 | 0.41 | tabla | 30.8 | 268.2 | 2.85 | 0.0102 | 0.0057 | 9 / 8 | 0.466, 0.2 | 9.4 | 1, 17.6 |
| 44 | PuyehueCordonCaulle | VIIRS750 | 2026-05-02 06:18 | N21 | 0.39 | tabla | 44.3 | 269.9 | 3.50 | 0.0100 | 0.0022 | 0 / 1 | 0.113, 0.5 | 1.0 | 0, - |
| 45 | Isluga | VIIRS750 | 2026-07-13 05:18 | N21 | 0.32 | tabla | 45.7 | 263.5 | 2.36 | 0.0095 | 0.0029 | 1 / 0 | 0.321, 0.7 | 3.4 | 0, - |
| 46 | PuyehueCordonCaulle | VIIRS750 | 2026-08-22 06:18 | N21 | 0.65 | tabla | 45.1 | 247.8 | 3.54 | 0.0059 | 0.0042 | 0 / 1 | 0.038, 0.3 | 0.9 | 0, - |

Notas. La distancia de MIROVA no está en la tabla a propósito: se mide desde el centro de su marco, no desde el cráter
(en Tupungatito el marco está a 4,86 km del cráter, D17), y no trae acimut (A93). Los campos completos de B y F de cada
pasada (incluidos `diag_nti_std`, `nti_max`, `diag_n_bg_used_first_pass`, `final_hotspot_source`, `f5_core_vrp_mw`)
están en `filas.json`; la salida plana con más columnas, en `listar_salida.txt`.

## 3. Qué condición las rechaza en F

`clases_rechazo.py` (salida en `clases_rechazo_salida.txt`):

| camino por el que B publicó | VIIRS 375: F pierde | VIIRS 750: F pierde |
|---|---|---|
| B tiene píxeles del primer pase en la escena | 27 de 864 (3 %) | 2 de 110 (2 %) |
| sólo segundo pase, píxel publicado con BT menos de 3 K sobre el fondo | **15 de 122 (12 %)** | 2 de 45 (4 %) |
| sólo segundo pase, BT de 3 K o más | 0 de 2 | sin casos |

**Lo que se puede deducir de los records, y lo que no.**
- **Primer pase.** En B el umbral de la cumbre es C1 = 0,003 en las 983 pasadas sin las filas malas (μ + 5σ supera C1
  en 983 de 983 para dNTI y en 882 de 983 para dETI, `estratos_salida.txt`). Un píxel del primer pase de B pasó dNTI >
  0,003, dETI > 0,003 y BT > t_bg + 3 K. En F ese mismo píxel tuvo que fallar dNTI > μ + 5σ o dETI > μ_e + 5σ_e, con
  los valores de la tabla del §2. **Cuál de los dos falla no se puede saber** salvo en un caso: en Isluga VIIRS 750
  2026-07-13 (#45, primer pase) el umbral de dETI de F queda en C1 (μ_e + 5σ_e = 0,0029), así que **lo que falla es el
  dNTI**. Salvedad: «B tiene píxeles del primer pase» cuenta píxeles de toda la escena; el píxel publicado podría venir
  del segundo pase igual.
- **Segundo pase.** Cuando B no tiene ni un píxel del primer pase (15 casos de VIIRS 375), lo publicado salió del
  segundo pase, que hoy corre aunque el primero esté vacío (`conditioned=False`, `process_viirs.py:1331-1350`) y no
  aplica la compuerta de temperatura. En los 15 el píxel está entre -1,1 y +3,0 K del fondo: **la compuerta D22 lo
  bloquea en el primer pase de los dos brazos**, así que ahí la conectiva no decide en el primer pase. Decide en el
  segundo, donde F exige max(C1, μ₂ + 5σ₂) con μ₂ y σ₂ calculados sobre todo el ROI sin los filtros de no aptos
  (`detection_context.py:922-929`, D26). **μ₂ y σ₂ no se guardan**: falta el campo.
- **Estado de F** en las 42 de VIIRS 375: sin ningún píxel en 28; con píxeles pero cúmulo a 5 km o más en 12 (F sólo
  ve algo lejos, el tablero no lo publica); con píxeles cerca del cráter en 2 (#5 y #38: F detecta 1 píxel a 1,0 y 0,2
  km pero con VRP 0,000, así que en esos dos **lo que lo apaga es la magnitud nula, no el test**; SOSPECHA: el exceso
  recortado a cero de D25).

**Campos que faltan para cerrar la pregunta 2**: dNTI y dETI por píxel publicado (en B y en F), y μ₂, σ₂ del segundo
pase. Con eso se sabría para cada pérdida qué test falla y por cuánto.

## 4. Patrones, contra las que F conserva y contra el residual

**Contra las conservadas, mismo instrumento** (`patrones.py`, `estratos.py`; sin las 5 filas malas):

| variable | perdidas (n 30), MIROVA < 0,10 MW | conservadas débiles (n 208) | AUC |
|---|---|---|---|
| σ dNTI (mediana) | 0,00150 | 0,00117 | 0,80 |
| σ dETI (mediana) | 0,00108 | 0,00076 | 0,81 |
| σ BT del anillo | 4,98 K | 3,31 K | 0,76 |
| cenit | 57,0° | 40,8° | 0,70 |
| VRP de MIROVA | 0,05 MW | 0,07 MW | 0,33 |
| VRP del cúmulo de B | 0,033 MW | 0,053 MW | 0,33 |
| píxeles del pozo de fondo | unos 11.800 | unos 13.600 | 0,28 |

- **La σ de la escena manda, no la debilidad.** Dentro de tramos de magnitud de B, la σ dNTI separa con AUC ponderado
  **0,85** (0,96 en 0,05 a 0,10 MW); dentro de cada banda de cenit, 0,69; dentro de cada volcán, 0,70. La σ dETI separa
  0,74 a 0,82 en los tres estratos. El cenit, controlado por volcán, 0,72; por magnitud, 0,67.
- **Satélite**: no importa (en el tramo débil pierde 12 % N20, 13 % N21, 13 % SNPP).
- **Borde y fondo frío**: pierde 21 % con cenit de 50° o más contra 8 % bajo 50°; 19 % con t_bg bajo 260 K contra 10 %.
- **Volcán** (tramo débil): Tupungatito 7 de 24, Chaitén 5 de 17, PCC 5 de 27, Planchón 6 de 36; Láscar 0 de 10,
  Lastarria 2 de 86. Escenas con glaciar y nieve, o nubosas del sur.
- **Fuente**: tabla 13 % y OCR 12 % en el tramo débil; no es un efecto de la etiqueta.

**Contra el residual que `max` apaga con razón** (`sigma_residual.py`): las perdidas (n 37) y el residual apagado
(n 766, negativos limpios que B publica y F no) son **indistinguibles** en σ dNTI (AUC 0,48), exceso de BT (0,52),
camino de publicación (0,53) y tamaño del cúmulo (0,53); se separan algo en t_bg (0,68: el residual es más frío,
mediana 249,6 K contra 260,3) y en magnitud (0,68). Las conservadas débiles, en cambio, se separan bien del residual
(σ dNTI 0,20, σ dETI 0,10). **Consecuencia para el diseño**: un ajuste de C2, un umbral por zona o un corte sobre
cualquier campo del record movería perdidas y residual juntos. El arreglo tiene que salir de información que el record
no tiene (por píxel) o de cambiar cómo se calcula la σ.

**Las dos preguntas del instrumento.** Si la tabla estuviera mal pareada, el control de reproducción fallaría (no
falla). Si las variables no midieran nada, las conservadas débiles no se separarían del residual (se separan, AUC
0,10 a 0,20), y la magnitud de B separaría perdidas de conservadas en todos los estratos por construcción, cosa que no
pasa dentro de tramos de magnitud (0,43).

## 5. Lo que hay en la imagen de MIROVA de esas pasadas

`tif_contraste.py`, `tif_que_separa.py` y `tif_disco_perdidas.py`, sobre los GeoTIFF de VIIRS 375 que ya estaban en disco
(`experiments/_s144_conteo_tif/_dl_tif/`, desde el 2026-05-09; no se bajó nada). Pareo por `acquisition_utc` a ±180 s,
descartando md5 que el índice asigna a más de una hora (A106). Estadístico: dL = radiancia de la celda menos la media de
sus 8 vecinos, normalizado por la media y la desviación de dL de toda la imagen sin el borde. Es el Test 2, pero en
radiancia MIR sola.

| grupo | n con TIF | z máximo en disco de 3 km, mediana | supera 5 σ |
|---|---|---|---|
| conservadas por F | 286 | 10,04 | 92 % |
| conservadas débiles (z ventana 3×3) | 77 | 6,65 | 74 % |
| **perdidas por F** | **10** | **4,59** | **3 de 10** |
| residual (MIROVA no vio nada) | 340 | 3,05 | 10 % |

- **Control positivo**: las conservadas de 0,5 MW o más dan z mediano 21,6 y 36 de 38 sobre 5. **Nulo**: ventanas
  sorteadas en la misma imagen dan z mediano 1,0 a 1,2 y 0,5 % sobre 5. El instrumento ve el calor donde lo hay y no lo
  inventa donde no.
- En 7 de las 10 perdidas el máximo del disco está a 0,1 a 0,3 km de nuestro píxel: MIROVA y nosotros miramos el mismo
  objeto. En Nevados de Chillán (#30) y Tupungatito 05-18 y 05-24 (#12, #16) el máximo está a 2,5 a 3,0 km, y ahí no
  se puede afirmar que sea el mismo objeto (A107).
- **Lectura**: en la imagen de MIROVA las perdidas también están en el límite, entre el residual y las conservadas
  (AUC contra el residual 0,75, contra 0,91 de todas las alertas bajo 0,10 MW). Con un umbral de 5 σ de su propia
  escena en radiancia MIR, MIROVA tampoco vería 7 de las 10. Como sí las alertó, o su criterio efectivo para estos casos
  es menos exigente que 5 σ de toda la escena, o el NTI y el ETI (que este proxy no tiene) cambian el orden.
- **Ningún criterio de una sola variable reproduce a MIROVA en este proxy**: el z y el exceso absoluto separan igual
  (AUC 0,92 a 0,93 sobre todas las alertas). Un corte en z que deje pasar 8 de las 10 perdidas (z ≥ 2,87) deja pasar
  104 de 343 residuales (30 %); uno que deje pasar 9 de 10 (z ≥ 2,42), 152 (44 %) (`tif_que_separa_salida.txt`).
  MIROVA no publicó ninguno de esos residuales.
- **SOSPECHA, no medido**: la σ de dNTI aproximada en la grilla de MIROVA (2 dL / L_TIR con la BT del fondo) es 0,63 a
  0,65 de la nuestra en perdidas y residual, y 0,84 a 0,88 en conservadas. El proxy omite la parte del TIR (nubes), que
  agrega varianza, así que está sesgado a favor de la hipótesis y no decide nada.

Límites: n = 10 perdidas (las otras 27 no tienen TIF con hora a ±180 s; abril no tiene TIF); el TIF sale del mismo
gránulo que nuestra detección (A109), así que describe el campo de MIROVA, no certifica la detección.

## 6. Hipótesis, ordenadas por evidencia

**H1. Nuestra σ de escena es más alta que la de MIROVA justo en las escenas donde perdemos, por cómo armamos el campo.**
- A favor: σ dNTI y σ dETI son lo que más separa perdidas de conservadas, también dentro de magnitud, cenit y volcán
  (§4). MIROVA mide sobre una grilla remuestreada de 134 × 134 celdas («after an initial resampling of the original
  granule in a regular 50×50 km UTM grid», Campus et al. 2024, Bull. Volcanol. 86:25, p. 3, leído en
  `documentacion/campus2024_extracted.txt:102-105`); el paper calcula μ y σ sobre «all the suitable pixels within the
  image», y llama no aptos a los del borde de la matriz remuestreada y a los de dNTI o dETI bajo -0,1
  (`documentacion/sp426.5.pdf`, páginas renderizadas 5 y 7 del PDF). Nosotros medimos sobre el gránulo nativo y en el
  borde del barrido el pozo tiene menos píxeles (mediana 12.021 con cenit de 50° o más contra 16.323 bajo 30°). El
  TIF de MIROVA es suave (autocorrelación a una celda 0,968, S147 H3), lo que podría bajar la σ del ruido más que el pico.
- En contra: en MODIS el remuestreo al vecino más cercano **subió** la σ 13 a 15 % (`experiments/_s137/RESULTADO_SIGMA_DNTI.md`);
  y en la imagen de MIROVA 7 de 10 perdidas no superan 5 σ (§5). Para VIIRS 375 con interpolación nunca se midió.
- **Medición que decide**: la sonda del §7 calcula, para las mismas pasadas, dNTI, dETI, μ y σ en (a) el gránulo nativo,
  (b) la grilla UTM de vecino más cercano que ya existe (`ENABLE_UTM_REGRID`, `pipeline/regrid.py`) y (c) una grilla
  interpolada sobre la georreferencia exacta del TIF de MIROVA de esa pasada, validada contra el TIF. **Confirma** si en
  (c) los píxeles de las perdidas pasan μ + 5σ en los dos tests y los del residual no. **Refuta** si en (c) las perdidas
  siguen bajo μ + 5σ o el residual también pasa.

**H2. 15 de las 42 dependen de un paso que el paper no tiene: la compuerta D22 más el segundo pase sin condicionar.**
- A favor: medido (§3). Los 15 tienen el píxel entre -1,1 y +3,0 K del fondo; la compuerta los bloquea en los dos
  brazos y sólo el segundo pase los rescata. El paper (p. 7 del PDF, renderizada) dice que la segunda corrida se aplica
  «only if one or more pixels have been detected by the previous tests» y sólo a los adyacentes. Con el segundo pase del
  paper, estos 15 no existirían en ningún brazo **mientras siga la compuerta**. En el segundo pase, μ₂ y σ₂ salen de un
  pozo sin los filtros de no aptos (D26), así que el umbral de F ahí puede ser mayor que el del primer pase.
- **Medición que decide**: un A/B con flags que ya existen (sin tocar código): F + `enable_tests_23_no_bt_gate_viirs375:
  true` en la sección `paths:` (D22 apagada; `pipeline/profile.py:131` y `:499`; sólo existe para VIIRS 375) sobre la
  misma ventana. S143 ya probó D22 con otra configuración (NO ADOPTAR, según la memoria del proyecto; no lo verifiqué);
  bajo `max` y sin Test 1 nunca se midió. Si el primer pase de F captura esos 15 sin que el residual vuelva, la pérdida era
  de la compuerta, no de la conectiva. Más barato aún: que la sonda del §7 guarde μ₂, σ₂ y el dNTI del píxel en el
  primer pase sin compuerta.

**H3. MIROVA no decide estos casos límite con 5 σ de su escena: o la conectiva es `min`, o su C2 efectivo para VIIRS
es otro.**
- A favor: en su propia imagen las perdidas tienen z mediano 4,6 y 7 de 10 quedan bajo 5 σ (§5), y MIROVA las alertó.
  Los umbrales C1 y C2 de Coppola 2016a están calibrados para MODIS (Tabla 1, p. 7) y Campus 2022 no da otros para VIIRS
  (`documentacion/BIBLIOGRAPHY_SYNTHESIS.md:103`).
- En contra: con `min` el residual también pasaría. En el proxy, 83 de 343 residuales superan C1 en dNTI aproximado y
  MIROVA no publicó ninguno; y B, que es `min`, publica 35,7 % de los negativos limpios. Una conectiva sola no reproduce
  las dos cosas a la vez, ni en nuestro dato ni en el de MIROVA.
- **Medición que decide**: la misma sonda, sobre el campo (c), evaluando las dos conectivas: si con `min` el residual
  pasa y con `max` las perdidas no, ninguna lectura reproduce a MIROVA y lo que falta es otro paso (H1 o H4); si con
  `max` en el campo (c) se separan, la conectiva estaba bien y el defecto es el campo.

**H4. La etiqueta.** 10 de las 42 de VIIRS 375 tienen etiqueta débil: 5 filas OCR con la imagen de otra pasada y 5 OCR
anteriores al 2026-06-13 (A119). Con etiqueta confiable quedan 32 (24 de tabla). No explica el patrón (la tasa de
pérdida en el tramo débil es igual con tabla y con OCR), pero cualquier conteo de recall debería informarlo aparte.

**Descartadas o sin apoyo con estos datos**: el satélite o la banda (pierde igual en los tres); la magnitud del píxel
como causa principal (dentro de tramos de magnitud la σ sigue separando, y la magnitud no); el camino del Test 1 (los dos
brazos lo tienen apagado).

## 7. Sonda mínima (diseñada, no despachada)

**Pregunta**: en las pasadas donde `max` pierde una alerta de MIROVA, ¿qué test falla, por cuánto, y pasaría en el
campo remuestreado como lo arma MIROVA?

**Población** (pre-registrar antes de correr): las 42 perdidas de VIIRS 375 y las 4 de VIIRS 750 (`filas.json`); 80
conservadas débiles y 80 residuales apagados sorteados con semilla fija, del mismo volcán y mes cuando se pueda; 40
residuales que sobreviven a F como control del otro lado.

**Qué guarda por pasada** (read-only, monkeypatch como A75, sin tocar `pipeline/` ni perfiles):
1. Para cada píxel publicado por B y por F, y para todo píxel del ROI1 con dNTI > C1: NTI, dNTI, dETI del primer pase,
   dNTI y dETI del segundo pase, BT I04 e I05, distancia al cráter, cenit, y qué test pasa con `min` y con `max`.
2. μ, σ del primer pase (ya se guardan) y **μ₂, σ₂ del segundo pase** (no se guardan hoy), con el tamaño de cada pozo.
3. Lo mismo sobre (b) la grilla UTM de vecino más cercano y (c) una grilla interpolada a la georreferencia exacta del TIF
   de MIROVA de esa pasada.
4. **Control del instrumento**: correlación y diferencia mediana entre la I04 de (c) y el valor del TIF, celda a celda.
   Si (c) no reproduce el TIF, la comparación del punto 3 no vale. Control negativo: los residuales que sobreviven a F
   deben pasar en el campo nativo con `max` (lo hacen en el A/B); si la sonda no los ve pasar, está rota.

**Cómo se decide**: H1 se confirma si en (c) al menos la mitad de las perdidas con etiqueta confiable pasan μ + 5σ en
los dos tests y la tasa de residual que pasa no sube sobre la de F nativo; H2, si con la compuerta apagada el primer
pase con `max` captura al menos la mitad de los 15; H3 queda en pie si ni (b) ni (c) separan.

**Insumos**: gránulos VNP02IMG/VJ102IMG/VJ202IMG con su geolocalización (por token, A71; nunca usuario y clave) y los TIF
de MIROVA de esas pasadas. Los TIF de abril no existen; los de mayo a agosto que falten se bajarían por la API de
GitHub, nunca con pull (17 GB). Bajar archivos requiere el sí de Nicolás.

## 8. Lo que queda abierto

- Qué test falla en cada pérdida (salvo #45): falta dNTI y dETI por píxel.
- μ₂ y σ₂ del segundo pase: no se persisten.
- Que el job haya aplicado los flags declarados: SIN VERIFICAR (mismo pendiente de `S150_RESULTADO_MESES.md` §6).
- El proxy del TIF es radiancia MIR, no NTI ni ETI: lo del §5 orienta, no decide.
- 27 de las 37 perdidas sin filas malas no tienen TIF pareable en disco.

## 9. Archivos

Todos en `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s150_debiles\`:
`extraer_y_tabular.py`, `perdidas_max.py` (y `filas.json`), `listar.py` (`listar_salida.txt`, `tabla_perdidas.md`),
`clases_rechazo.py` (`clases_rechazo_salida.txt`), `patrones.py` (`patrones_salida.txt`), `estratos.py`
(`estratos_salida.txt`), `sigma_residual.py` (`sigma_residual_salida.txt`), `tif_contraste.py` (`tif_contraste.json`,
`tif_contraste_salida.txt`), `tif_que_separa.py` (`tif_que_separa_salida.txt`), `tif_disco_perdidas.py`
(`tif_disco_salida.txt`). Las extracciones de los runs vivieron en un temporal fuera del repo y se borraron al terminar.
