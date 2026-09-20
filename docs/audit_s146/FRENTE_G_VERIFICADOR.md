# Frente G: verificación con contexto limpio

Verificador sin acceso al razonamiento del auditor. Método por ítem: fuente primaria primero
(código con sus llamadores, banderas leídas de `pipeline.profile`, records, frontend), derivación
propia, medición por un camino propio, y recién al final la lectura de su informe. Todos los
números de este documento salen de una corrida de esta sesión y están pegados junto a su salida
cruda. Ventana del régimen actual: 2026-09-01 en adelante, sin cruzar el 2026-08-28 23:00 UTC.

Scripts propios en `C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/experiments/_s146_auditoria/verificador_G/`:
`v1_nulo_propio.py`, `v2_k_observado_real.py`, `v3_firma_de_ruido.py`, `v4_items_2_a_5.py`,
`v4b_items_2_y_3b.py`, `v5_predicado_operador.py`, cada uno con su JSON al lado.

## Tabla de veredictos

| Ítem | Afirmación | Veredicto | Gravedad |
|---|---|---|---|
| 1 (G-27) | El criterio "3 sigma" del Test 1 integrado se cumple con ruido puro | **CONFIRMADO** en VIIRS 375; **CONFIRMADO CON MATIZ** en VIIRS 750; **REFUTADO** el enlace con la sobre-publicación de MODIS | **5** |
| 2 (G-19) | `only_test1_source` exige en cero contadores que ya no arman la máscara; 132 V375 y 16 V750 | **CONFIRMADO CON MATIZ** (el conteo es exacto; el efecto que describe no es el que ocurre) | 3 |
| 3a | Segundo pase detecta con el primero en cero: 230 V375, 139 V750 | **CONFIRMADO** | 3 |
| 3b | 348 `test1_roi` de V375 a 0,0 km y `summit`, con el cúmulo a más de 1 km en 328 | **CONFIRMADO** la posición fabricada; **REFUTADO** que deje sin efecto la cerca por distancia | 2 |
| 4 | El modo de un píxel y el núcleo F5' se deshacen entre sí: mediana 1,74 en 82 records | **CONFIRMADO** | 3 |
| 5 | El tope de Villarrica no llega al operador (8 de 13), 105 records con `discarded_reason` publican, `diario.html` sin los predicados | **CONFIRMADO** (mecanismo incompleto, ver abajo) | 3 |

---

## Ítem 1 (G-27): el criterio absoluto del Test 1

### Qué ve el satélite

Sobre el cráter de un volcán nevado, de noche, el sensor no ve un objeto caliente: ve un campo de
temperatura de brillo con textura. Roca, nieve parcial, hielo, sombra de relieve y ruido del propio
detector producen una dispersión de entre medio grado y varios grados dentro de un disco de 3 km.
No hay lava en ese campo. Es la textura normal de un volcán apagado.

### El mecanismo

El Test 1 integrado toma la mediana de radiancia del anillo de 1 a 3 km como fondo, resta ese fondo
a cada píxel del disco de 3 km, **recorta a cero los que quedaron por debajo** y suma los que
quedaron por encima. Esa suma la compara contra `k · sigma_fondo · raíz(N)`.

Ahí está el defecto, y es de construcción, no de calibración. Por definición de mediana, la mitad de
los píxeles del disco queda por encima del fondo aunque no haya absolutamente nada caliente. Al
recortar los negativos, la suma deja de tener media cero bajo la hipótesis nula: cada píxel aporta en
promedio `0,399 · sigma` (la media del semieje positivo de una gaussiana), así que la suma vale en
promedio `0,399 · N · sigma`. Pero la vara contra la que se la compara, `3 · sigma · raíz(N)`, es la
desviación de una suma **sin recortar**, cuya media sí es cero. Numerador y denominador describen dos
variables distintas: se compara la **media** de una contra la **desviación** de la otra.

Como la media crece con `N` y la vara sólo con `raíz(N)`, existe un tamaño de disco a partir del cual
el criterio se cumple siempre sin nada que detectar:

    0,399 · N · sigma > 3 · sigma · raíz(N)   ⟺   raíz(N) > 7,52   ⟺   N > 56,6

Nótese que `sigma` se cancela. El criterio absoluto no depende de cuánto ruido hay: depende de cuántos
píxeles tiene el disco. Y el valor que el pipeline persiste como `test1_k_observed` tiene, bajo ruido
puro, un valor predicho sin ningún parámetro libre:

    k_observado  ≈  0,399 · raíz(N_roi)  ≈  0,399 · raíz(2 · n_contribuyentes)

Con el disco de 3 km: VIIRS 375 m da unos 208 píxeles (k predicho 5,75), VIIRS 750 m unos 50 (2,88),
MODIS unos 32 (2,26). Sólo el primero pasa el corte de 3 sin nada que detectar.

### Los números

**Simulación propia** (`v1_nulo_propio.py`, semilla 20146, llama a la función real
`compute_test1_mir` con `TEST1_K_SIGMA=3.0`, `TEST1_ROI_KM=3.0`, `TEST1_INNER_RING_KM=1.0`,
`TEST1_MIR_RELATIVE=0.02` leídos de `pipeline.profile`):

```
caso                                   n_roi   trig    abs    rel   k_med  k_pred
VIIRS375_I04/nulo_blanco_1K              208   0.79   1.00   0.79   5.993   5.754
VIIRS375_I04/nulo_correlado_1K           208   0.60   1.00   0.60   5.951   5.754
VIIRS375_I04/nulo_t3_1K                  208   0.14   1.00   0.14   7.197   5.754
VIIRS375_I04/nulo_blanco_0p3K            208   0.00   1.00   0.00   5.840   5.754
VIIRS375_I04/barrido_0.9K                208   0.42   1.00   0.42   5.996   5.754
VIIRS375_I04/barrido_1.1K                208   0.93   1.00   0.93   6.029   5.754
VIIRS375_I04/CONTROL_con_senal_60K       208   1.00   1.00   1.00  22.380   5.754
VIIRS375_I04/CONTROL_sin_dispersion      208   0.00   0.00   0.00   0.000   5.754
VIIRS750_M13/nulo_blanco_1K               52   0.35   0.51   0.46   3.035   2.877
VIIRS750_M13/CONTROL_con_senal_60K        52   1.00   1.00   1.00  32.074   2.877
MODIS_B21/nulo_blanco_1K                  32   0.15   0.19   0.47   2.306   2.257
MODIS_B21/CONTROL_con_senal_60K           32   1.00   1.00   1.00  37.343   2.257
```

Los dos controles funcionan: un foco de +60 K dispara el 100 % de las veces en los tres sensores, y
un campo sin dispersión no dispara nunca. El instrumento está vivo, así que los ceros y los unos de
arriba son mediciones y no artefactos del arnés.

La columna `abs` es el criterio absoluto: **1,00 en VIIRS 375 bajo los tres modelos de ruido que
probé** (blanco, correlacionado espacialmente y de colas pesadas), y ninguno de los ataques que
preparé lo salva. La correlación espacial no lo rescata porque no cambia la media marginal del
exceso recortado, sólo su varianza. Las colas pesadas lo empeoran, porque la MAD subestima la
dispersión. La amplitud del ruido no lo mueve en absoluto: 0,3 K y 2,0 K dan el mismo `abs = 1,00`
y casi el mismo `k_med`, tal como predice la fórmula.

Lo único que frena es el piso relativo del 2 %, que pide `0,399 · sigma_L > 0,02 · L_fondo`. Como la
sensibilidad relativa de la radiancia MIR ronda 5,3 % por kelvin a 270 K, eso equivale a una
dispersión de alrededor de 0,95 K, y el barrido lo confirma: 0 % a 0,7 K, 42 % a 0,9 K, 93 % a 1,1 K.
La afirmación de "cerca de 1 K" es exacta.

**Los records reales** (`v3_firma_de_ruido.py`, 1016 pasadas con el Test 1 disparado desde
2026-09-01). Esta es la prueba que más me costó imaginar cómo podía fallar, porque la predicción no
tiene parámetros que ajustar:

```
sensor         n n_contrib   k_obs  k_pred   razon    p10    p90
MODIS         16        11   3.820   1.871   2.074  1.559  3.167
VIIRS375     800        70   4.860   4.720   1.056  0.820  1.602
VIIRS750     200        19   3.810   2.459   1.621  1.272  2.464

CONTROL (decil superior de magnitud publicada vs mitad baja):
  VIIRS375   razon alto=1.355 (VRP med 0.148)   razon bajo=0.999 (VRP med 0.030)
  VIIRS750   razon alto=1.694 (VRP med 0.603)   razon bajo=1.546 (VRP med 0.068)
```

En VIIRS 375 el `k_observado` real está a **5,6 % de la curva del ruido puro**, con mediana 1,056 y
mitad central entre 0,82 y 1,60. La mitad de las pasadas con menos magnitud publicada da razón
**0,999**: sobre la curva del ruido, exactamente. El control se comporta como debe: el decil de mayor
magnitud se despega a 1,355, de modo que la relación no es una identidad algebraica del código sino
una medición, y cuando hay un foco real el estadístico sí se levanta.

**Discriminación contra la referencia** (`v2_k_observado_real.py`, etiquetas del banco de paridad
reusadas por importación, no reescritas):

```
 [VIIRS375] n_pos=122 n_neg=287 trig_test1 pos=1.0 neg=0.8327526132404182
   test1_k_observed     AUC=0.7802  pos_med=5.94  neg_med=4.41
   pc_vrp               AUC=0.8826  pos_med=0.094 neg_med=0.039
CONTROLES: oraculo=1.0  barajado_dentro_de_volcan_auc_medio=0.6429 (min 0.591, max 0.699)
```

El control de barajado es el que ordena la lectura: barajando las etiquetas dentro de cada volcán el
AUC agrupado no cae a 0,5 sino a **0,643**, porque los volcanes con más positivos son también los de
`k` más alto (efecto de Simpson). Contra ese nulo, el 0,780 agrupado es poca cosa. Estratificado por
volcán, que es la lectura honesta, los AUC quedan en 0,540 (Láscar), 0,562 (Chaitén), 0,618 (PP),
0,727 (Tupungatito), 0,789 (Lastarria), 0,901 (PCC) y 1,000 (Isluga, con sólo 6 negativos).

Y el número que decide: **el Test 1 dispara en el 83,3 % de las pasadas VIIRS 375 en que MIROVA miró
y no vio nada** (239 de 287 negativos limpios), contra el 100 % en las confirmadas. En VIIRS 750,
22,8 % contra 66,7 %.

### Veredicto ítem 1

**CONFIRMADO** para VIIRS 375, gravedad **5**. Mi derivación cerrada, mi simulación escrita sin ver
la suya y los records reales coinciden: el criterio absoluto se satisface con ruido puro el 100 % de
las veces en ese sensor, el `k_observado` real se sienta sobre la curva del nulo, y el único freno es
un piso relativo que la textura normal de un volcán supera casi siempre.

**CONFIRMADO CON MATIZ** para VIIRS 750: mi nulo da 0,47 a 0,51 de criterio absoluto contra su rango
declarado de 0,35 a 0,55 (la diferencia es el tamaño de la grilla: su disco tiene 49 píxeles y el mío
52), y la tasa real de disparo en negativos limpios es 22,8 %, no 35 a 55 %.

**REFUTADO** el tramo de MODIS de la afirmación relayada, que dice que las tasas del nulo van "en el
mismo orden que la sobre-publicación medida por sensor". Para MODIS el nulo da 13 a 19 % de criterio
absoluto (el mío, 13 a 19 %, idéntico), pero en los records reales el Test 1 dispara en sólo
**16 de 457 pasadas** (3,5 %) y en 3,2 % de los negativos limpios, mientras la sobre-publicación de
MODIS es 11,4 %. En MODIS el Test 1 no es el sostén de la brecha. Para VIIRS la correspondencia sí es
estrecha: 83,3 % de disparo en negativos contra 86,3 % de sobre-publicación en 375, y 22,8 % contra
21,4 % en 750.

### Qué diría un criterio estadísticamente correcto

El defecto no es que el umbral sea bajo. Es que **el estadístico y su vara describen cosas
distintas**. Un test integrado correcto compara el exceso observado contra la distribución nula **del
mismo estadístico que se calculó**, y hay dos formas de conseguirlo:

1. **No recortar.** Integrar `suma(L − L_fondo)` sobre el disco, sin el `max(0, ·)`. Esa suma sí tiene
   media cero bajo ruido y desviación `sigma·raíz(N)`, de modo que `k·sigma·raíz(N)` pasa a ser la
   vara correcta y el `k` recupera su sentido de "veces la desviación". El costo físico: una fuente
   compacta se diluye contra el ruido de todo el disco, que es justamente lo que el recorte quería
   evitar.
2. **Recortar y centrar.** Si se conserva el recorte porque una fuente sub-píxel sólo aporta en
   positivo, hay que restarle al estadístico su propia media nula y dividir por su propia desviación
   nula, que no son las de la suma sin recortar: media nula `E[max(0,Z)]·N·sigma` y desviación nula
   `raíz(Var(max(0,Z))·N)·sigma`, con `Var(max(0,Z)) = 0,5 − 0,399² = 0,341`. Es decir, la vara pasa a
   ser `0,399·N·sigma + k·0,584·sigma·raíz(N)` en vez de `k·sigma·raíz(N)`.

En los dos casos el rasgo esencial es el mismo y es el que hoy falta: **la vara tiene que crecer con
`N` al mismo ritmo que crece el estadístico cuando no hay nada**. Hoy crece con `raíz(N)` mientras el
estadístico crece con `N`, y por eso el resultado depende del tamaño del disco y no del volcán.

Cualquiera de las dos correcciones deja el `k` centrado en 0 bajo ruido. Traducido a lo que hoy se
persiste: `k_efectivo = (k_observado − 0,399·raíz(N)) / 0,584`. Con los valores medidos en VIIRS 375
(`k_observado` mediano 4,86 y 70 píxeles contribuyentes, o sea unos 140 en el disco), el `k_efectivo`
mediano queda en **0,1**, no en 4,86.

**Cuánto de la sobre-publicación de VIIRS 375 explicaría: acotado, no resuelto.** Puedo acotar la
población: el criterio del Test 1 se satisface en 239 de 287 pasadas de negativo limpio (83,3 %), y
un criterio centrado en su nulo se satisfaría ahí con la frecuencia nominal, así que ese es el techo
de lo que la corrección podría sacar. El piso no lo puedo dar con los records: apagar el Test 1 no
sólo quita un criterio, también cambia la máscara caliente y el recálculo de magnitud aguas arriba,
y eso no se contesta desde el dato persistido. **SIN DATO** para la fracción exacta; hace falta un
A/B con reproceso, y es lo que este hallazgo justifica.

Una advertencia, porque la afirmación tiene mucha palanca y el riesgo de sobrecorregir es real: que
el criterio se cumpla con ruido **no** implica que las detecciones sean falsas. El propio control
muestra que cuando hay magnitud el estadístico se levanta, y la regla A54 de este proyecto está
construida sobre la observación de que la mayoría de lo que MIROVA no publica es calor real
sub-umbral. Lo que el defecto destruye es la **capacidad del criterio de decidir**: hoy no aporta
información, deja pasar todo lo que el piso relativo del 2 % no frene. El Test 1 subió el recall de
50 a 80 % cuando se adoptó, y eso es compatible con lo anterior: una compuerta que deja pasar casi
todo sube el recall por construcción. Lo que no está medido es cuánto de esa ganancia sobrevive a un
criterio que discrimine.

---

## Ítem 2 (G-19): `only_test1_source` mira contadores que ya no arman la máscara

El mecanismo está en el código y es exactamente el que describe. `pipeline/process_viirs.py:1747-1753`
exige que los cuatro contadores heredados estén en cero:

```python
    only_test1_source = (
        test1_triggered and test1_centroid_lat is not None
        and (n_bt_path or 0) == 0
        and (n_nti_path or 0) == 0
        and (n_dnti_ctx_path or 0) == 0
        and (n_eti_path or 0) == 0
    )
```

Pero cien líneas antes, en `process_viirs.py:1236-1240`, el propio comentario del código dice qué pasó
con esos contadores (comentario de la línea 1236, citado desde "first-pass"): *"first-pass Tests 2 ∧ 3 ... Reemplaza hot_mask_2d con la
conjunción Test 2 ∧ Test 3 + dual-ROI Tabla 2. Paths legacy se calcularon arriba (diag) pero no
contribuyen cuando ON"*, y `ENABLE_FIRST_PASS_TESTS_2_AND_3` está en `True` (leído de
`pipeline.profile`). En `process_viirs.py:1299` la máscara se reasigna (`hot_mask_2d = fp_hot`). Los
cuatro contadores quedaron de diagnóstico y el predicado sigue preguntándoles a ellos.

Medido (`v4b_items_2_y_3b.py`), el conteo reproduce el suyo al dígito:

```
 "item2_G19": {
  "VIIRS375": { "n_sensor": 954, "only_test1_source_verdadero": 336,
                "de_esos_con_pixeles_contextuales_en_la_mascara": 132,
                "y_ancla_termina_en_test1_roi": 5, "mediana_second_pass": 1 },
  "VIIRS750": { "n_sensor": 949, "only_test1_source_verdadero": 75,
                "de_esos_con_pixeles_contextuales_en_la_mascara": 16,
                "y_ancla_termina_en_test1_roi": 0 }
 }
```

**132 y 16, exactos.** El matiz está en la consecuencia. Él dice que "el cúmulo contextual se descarta
sin quedar escrito", y eso ocurre en **5 de los 132**, no en los 132: en los otros 127 el ancla honesta
(`pipeline/anchor.py:83-89`) igual se queda con el `ctx_cluster`, porque esa cascada corre después y
sobrescribe sólo la posición. Lo que `only_test1_source` decide de verdad es la **magnitud**: fuerza
`final_hotspot_source = "test1"` en la semántica interna que habilita el recálculo del VRP con
píxeles del Test 1, mientras la posición publicada sigue apuntando al cúmulo contextual. O sea el
número y el punto del mapa salen de objetos distintos, que es la familia de incoherencias A46 y es
arguiblemente peor que lo que afirma.

**Veredicto: CONFIRMADO CON MATIZ, gravedad 3.** El conteo y el mecanismo son correctos; el efecto
descrito aguas abajo vale para 5 de 132.

## Ítem 3a: el segundo pase detecta con el primero en cero

```
 "item3a_segundo_pase_solo": {
  "VIIRS375": {"n_con_ambos_campos": 954, "primer_pase_0_y_segundo_detecta": 230,
               "complemento": 724, "de_esos_publicables_pc_vrp_gt0": 220},
  "VIIRS750": {"n_con_ambos_campos": 949, "primer_pase_0_y_segundo_detecta": 139,
               "complemento": 810, "de_esos_publicables_pc_vrp_gt0": 54},
  "MODIS":    {"n_con_ambos_campos": 457, "primer_pase_0_y_segundo_detecta": 1}
 }
```

**230 y 139, exactos.** Los campos tienen cobertura 1,0 en los tres sensores, así que ninguno de esos
ceros es un campo ausente. En VIIRS 375, 220 de esas 230 pasadas llevan además un cúmulo con energía.
**CONFIRMADO, gravedad 3.**

## Ítem 3b: el ancla que pone 0,0 km

En `pipeline/anchor.py:89`, cuando el Test 1 disparó y no hay cúmulo contextual que gane, el ancla
devuelve literalmente `(vent_lat, vent_lon, 0.0, "test1_roi")`: la posición publicada es el cráter
nominal y la distancia es cero por construcción, no por medición. Como `0 <= inner_radius_km` siempre,
`distance_class` queda `summit` sin excepción.

```
 "item3b_ancla": {
  "VIIRS375": {"source_test1_roi": 348, "dist_exactamente_0km": 348, "y_summit": 348,
               "y_cumulo_a_mas_de_1km": 328, "mediana_dist_cumulo_en_lejos": 2.75,
               "max_dist_cumulo_en_lejos": 3.0},
  "VIIRS750": {"source_test1_roi": 138, "dist_exactamente_0km": 138, "y_summit": 138,
               "y_cumulo_a_mas_de_1km": 104}
 }
```

**348, 348, 348 y 328, exactos.** Pero la última cláusula, "dejando sin efecto la cerca por distancia
del dashboard", no se sostiene. El cúmulo está acotado por el propio ROI del Test 1, que mide 3 km, y
el radio interior más chico de la flota es 3 km (Lastarria y Planchón-Peteroa). Medido:

```
V375 test1_roi con cumulo >1km: 328  de esos quedarian FAR si se clasificara por el cumulo: 0
inner: Lascar 5.0, Lastarria 3.0, Isluga 5.0, Tupungatito 7.0, PlanchonPeteroa 3.0,
       NevadosDeChillan 5.0, Llaima 5.0, Villarrica 5.0, Copahue 4.0, PCC 20.0, Chaiten 5.0
```

Ninguna de las 328 cambiaría de lado si se la clasificara por donde está el cúmulo. **CONFIRMADO** que
la posición publicada es fabricada (y eso importa: un operador que mire el mapa ve el punto en el
cráter cuando el calor está a 2,75 km de mediana, y cualquier auditoría espacial posterior queda
ciega, que es el modo de falla A61). **REFUTADO** el efecto sobre la cerca. Gravedad **2**, porque el
daño es de posición y de auditabilidad, no de qué se publica.

## Ítem 4: el modo de un píxel contra el núcleo F5'

Medido sólo donde el modo efectivamente cambia el número, es decir con `single_pixel_mode = true` y
más de un píxel en el cúmulo (con un solo píxel el máximo y la suma son lo mismo):

```
V375, single_pixel_mode aplicado Y n_pixels>1 (el modo cambio el numero): 82
mediana f5/pc = 1.748
p10/p90 = 1.0 3.867
n con razon >1.05: 68   <0.95: 0
por volcan: PCC 26, Lascar 14, Isluga 13, Tupungatito 12, Chaiten 11, PP 3, Lastarria 1, Llaima 1, Villarrica 1
CONTROL n_pixels==1 (el modo no cambia nada): n=742  mediana f5/pc = 1.0
```

**82 records y mediana 1,748, exactos.** El control cierra la lectura: donde el modo no puede cambiar
nada la razón es exactamente 1,000 sobre 742 records, así que el 1,748 no es un sesgo del cálculo sino
el efecto del modo. El fenómeno es el que describe: el modo de un píxel baja la magnitud al píxel más
caliente para no inflar el régimen sub-MW, y el núcleo F5' vuelve a sumar el entorno del pico, de
modo que una corrección deshace a la otra y ninguna de las dos ve a la otra. Ninguno de los 82 va en
el sentido contrario (0 casos bajo 0,95). **CONFIRMADO, gravedad 3.**

## Ítem 5: el tope de Villarrica y `diario.html`

Medido con el predicado del operador **ejecutado con node** desde `frontend/index.html`
(`v5_predicado_operador.py`, reusando el arnés `correr_node` del banco de paridad; sha del HTML en el
JSON), no portado a mano:

```
item5a resumen: {'topados': 13, 'publican': 8, 'de_los_que_publican_con_trigger_test1': 8,
                 'de_los_que_publican_SIN_trigger_test1': 0,
                 'isValidDetection_verdadero': 13, 'isSummitDetection_verdadero': 8, 'artefacto': 0}

 "item5b_discarded_reason": {"con_discarded_reason": 508, "publican": 105,
   "por_razon": {"cluster_too_large_for_volcano": {"n": 13, "publican": 8},
                 "eruption_hotspot_too_far": {"n": 6, "publican": 0},
                 "partial_eruption_hotspot_too_far": {"n": 455, "publican": 63},
                 "single_pixel_far_overridden_by_cluster": {"n": 34, "publican": 34}}}

 "item5c_diario": {"isValidDetection":  {"diario.html": 0, "index.html": 13},
                   "isSummitDetection": {"diario.html": 0, "index.html": 6},
                   "mirovaEqVrp":       {"diario.html": 6, "index.html": 11}}
```

**8 de 13, 105 y los dos ceros de `diario.html`: exactos.** Los tres números salen del predicado real.

El mecanismo que nombra es correcto pero **incompleto**, y esto es un hallazgo propio. Él atribuye la
fuga a `isSummitDetection`, que en `frontend/index.html:1484` deja pasar todo record con
`triggered_test1`. Es cierto y es la compuerta que decide las 8. Pero hay un segundo agujero, anterior
y más ancho: en `pipeline/store.py:405-411` el tope pone `vrp_eruption = 0` y escribe
`discarded_reason`, y **nunca toca `primary_cluster.vrp_mw`**; y `isValidDetection`
(`frontend/index.html:1472`) resuelve con `if (r?.primary_cluster) return (r.primary_cluster.vrp_mw ?? 0) > 0`.
Es decir, el tope es invisible para el predicado de validez: los **13 de 13** lo pasan, no sólo los 8.
Se ve en el detalle, donde los cinco que no publican traen `valid: 1` y caen recién en `summit: 0`. Si
mañana un record topado quedara `summit` por distancia sin `triggered_test1`, publicaría igual. El
tope de Villarrica no tiene un agujero, tiene dos, y el de abajo no depende del Test 1.

**CONFIRMADO, gravedad 3.**

---

## Hallazgos propios

1. **Un error mío, del tipo que este proyecto ya tiene catalogado (A89).** En mi primera medición de
   los ítems 2 y 3b filtré por `final_hotspot_source == "test1"` y obtuve **cero** en VIIRS, contra
   los 132 y 348 del auditor. Estuve a un paso de reportarlo como refutación. El código escribe
   `"test1_roi"` (`pipeline/anchor.py:89`), que es otra cadena: el filtro con el nombre equivocado no
   da error, da cero, y el cero se lee como ausencia. Con la cadena correcta los números coinciden al
   dígito. Queda como `v4_items_2_a_5.py` (con el error) y `v4b_items_2_y_3b.py` (corregido), a
   propósito, para que el caso quede registrado.
2. **El auditor subestima su propio hallazgo del ítem 1.** Su `k_observado_vs_nulo.json` compara la
   mediana real de 4,86 con 70 píxeles contra 5,75 con 104 del nulo, y presenta la diferencia como
   una brecha. No es una brecha: el nulo predice `0,399·raíz(2·n_contribuyentes)`, y con los 70
   contribuyentes reales eso da 4,72 contra 4,86 observado, o sea una razón de **1,056**. El dato real
   está más cerca del ruido puro de lo que él afirma.
3. **Su nulo no lleva controles.** `nulo_test1_ruido_puro.py` no tiene un brazo con señal conocida que
   el test deba detectar ni un brazo de dispersión cero. Sus números resultaron correctos, pero sin
   esos brazos no había forma de distinguir "el criterio dispara siempre" de "el arnés devuelve
   siempre verdadero", que es justo la lectura que esta afirmación necesita blindada (A110). Los agregué
   en `v1_nulo_propio.py` y pasan.
4. **El nulo agrupado del AUC no es 0,5.** Barajando etiquetas dentro de cada volcán, el AUC agrupado
   de `test1_k_observed` da 0,643, no 0,5, porque los volcanes con más positivos son los de `k` más
   alto. Cualquier AUC agrupado que se reporte en este frente sin ese control sobreestima la
   discriminación en unos 0,14 puntos.
5. **El enlace entre el nulo y la sobre-publicación no vale para MODIS.** La afirmación relayada dice
   que las tasas del nulo van "en el mismo orden que la sobre-publicación medida por sensor". Para
   VIIRS es estrecho (83,3 % contra 86,3 %, y 22,8 % contra 21,4 %); para MODIS el Test 1 dispara en
   3,5 % de las pasadas y la sobre-publicación es 11,4 %, así que ahí la brecha tiene otro origen y
   arreglar el Test 1 no la toca.
6. **El segundo agujero del tope de Villarrica**, descrito en el ítem 5.

## Lo que no verifiqué

- **SOSPECHA**: no medí qué fracción de la sobre-publicación de VIIRS 375 desaparecería con el
  criterio corregido. Requiere A/B con reproceso, porque apagar el Test 1 cambia la máscara y la
  magnitud aguas arriba.
- **SOSPECHA**: la simulación usa grillas lat/lon regulares. El arreglo real de VIIRS crece fuera del
  nadir (efecto corbatín), así que el número de píxeles del disco en una pasada concreta puede diferir
  del nominal. No cambia la conclusión (la fórmula usa el `N` que haya, y los records reales confirman
  la relación con el `N` efectivo), pero las tasas por sensor del nulo son nominales.
- **SIN DATO**: no comprobé el resto de las 31 filas del inventario del frente G. Sólo las cinco de
  este encargo.
