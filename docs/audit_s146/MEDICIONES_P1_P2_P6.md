# Mediciones P1, P2 y P6 (S146): tres preguntas contestadas con lo que ya estaba en disco

> Generado por `experiments/_s146_mediciones_p1_p2_p6/generar_informe.py`. Todos los números salen de `p1_resultados.json`, `p2_resultados.json` y `p6_resultados.json` de esa carpeta, o están pegados de la salida cruda de cada script (`p1_salida_cruda.txt`, `p2_salida_cruda.txt`, `p6_salida_cruda.txt`). Sólo lectura: no se tocó `pipeline/`, `frontend/`, `scripts/`, `data/` ni ningún documento existente, no se descargó nada y no se corrió pytest.

## 0. Control positivo: antes de atribuir nada, reproducir lo ya verificado

La carga es la de la Fase 1 importada tal cual (`sustrato_caminos.py`, que a su vez usa `scripts/banco_paridad.py` y ejecuta el predicado del dashboard con node). Con ella se reproduce la línea base de S145 y la atribución de la Fase 1:

| qué | esperado | medido hoy |
|---|---|---|
| VIIRS 375, publicación en negativos limpios | 0,8633 (n 373) | 0,8633 (n 373) |
| VIIRS 750 | 0,2138 (n 622) | 0,2138 (n 622) |
| MODIS con el corte de procesamiento de S145 | 0,1142 (n 438), el 0,114 de S145 | 0,1142 (n 438); sin corte 0,1139 (n 439), por un record procesado después |
| Fase 1, VIIRS 375: sostenidas sólo por el Test 1 | 186 de 322 | 186 de 322 |
| Fase 1, VIIRS 750 | 89 de 133 | 89 de 133 |

Reproduce: **sí**. Los tres scripts abortan si este control no da. Salida cruda:

```
CONTROL POSITIVO {"MODIS": {"n_neg_limpio": 439, "tasa_pub_neg": 0.1139, "n_pub_neg": 50, "T1_SOLO_neg": 8}, "VIIRS375": {"n_neg_limpio": 373, "tasa_pub_neg": 0.8633, "n_pub_neg": 322, "T1_SOLO_neg": 186}, "VIIRS750": {"n_neg_limpio": 622, "tasa_pub_neg": 0.2138, "n_pub_neg": 133, "T1_SOLO_neg": 89}, "MODIS_con_corte_S145": {"n_neg_limpio": 438, "tasa_pub_neg": 0.1142}, "reproduce_S145_y_Fase1": t
```

## 1. P1: la curva de dosis del Test 1 integrado

### El fenómeno

El Test 1 integrado no mira píxeles sueltos: suma todo el exceso de radiancia del infrarrojo medio dentro de un disco de 3 km alrededor del cráter y pregunta si esa suma supera en k veces el ruido del anillo de fondo. Sirve para ver calor débil y repartido (un lago de lava chico, un campo de fumarolas) que ningún píxel delata por sí solo. El problema es que un disco sobre un edificio volcánico nunca es térmicamente plano: hay laderas que guardan calor del día, roca oscura junto a nieve, valles más tibios que la cumbre. Todo eso suma exceso positivo aunque el volcán esté quieto, y más todavía porque el exceso se recorta en cero (lo frío no resta). Por eso a 3 sigmas el Test 1 dispara casi todas las noches, y eso es lo que el operador ve publicado donde MIROVA miró y no vio nada.

La pregunta de P1 es si basta con pedirle más sigmas. Hay dos resultados posibles y los dos sirven: o existe un k donde el relieve tibio queda abajo y el calor volcánico arriba (un umbral que separa), o las dos poblaciones se traslapan y lo único que hace subir k es apagar el detector de a poco.

### El mecanismo de la medición y lo que supone

Cada record guarda `test1_k_observed`, el número de sigmas que alcanzó la suma. Como k sólo entra en la comparación final (`pipeline/test1_integrated.py`, línea 435), una pasada con k observado mayor que el umbral nuevo queda idéntica: eso es exacto. Lo que es **cota y no simulación** es lo que pasa con las que quedan debajo: una pasada que la Fase 1 clasificó T1_SOLO se da por no publicada (se hereda el supuesto de la Fase 1, no se re-ejecuta el ensamblado); una T1_SOBRE_CTX queda SIN DATO, porque no se persiste cuánto valía el cúmulo contextual que el Test 1 reconstruyó; AMBOS y CTX_SOLO siguen porque no dependen del Test 1. También se supone, sin medirlo, que subir k no hace publicar nada que hoy no se publica (SOSPECHA razonable). Una noche positiva *sigue* si conserva al menos una pasada publicada segura, es *SIN DATO* si sólo le quedan pasadas SIN DATO, y *se pierde* si no le queda ninguna.

### Cobertura del campo, medida primero

| sensor | records | k_obs nulo | k_obs = 0 (no calculado o cero) | k_obs > 0 | disparos | disparos con k ≤ 3 | no disparó con k > 3 (falló el criterio relativo del 2 %) |
|---|---|---|---|---|---|---|---|
| MODIS | 457 | 0 | 318 | 139 | 16 | 0 | 0 |
| VIIRS375 | 954 | 0 | 45 | 909 | 800 | 1 | 24 |
| VIIRS750 | 949 | 0 | 167 | 782 | 200 | 0 | 10 |

El campo existe en los tres sensores y no hay nulos, así que la curva no sale de un cero que se lee como confirmación. El valor 0,0 es ambiguo (el código escribe 0,0 tanto si no calculó como si dio cero), pero no afecta la curva: sólo importan las pasadas donde el Test 1 disparó. El único disparo con k ≤ 3 es un redondeo a dos decimales. En MODIS el Test 1 dispara poco, así que ahí la curva casi no tiene sustrato.

```
COBERTURA {"MODIS": {"n_records": 457, "k_obs_None": 0, "k_obs_cero": 318, "k_obs_positivo": 139, "triggered_True": 16, "triggered_True_con_k_le_3": 0, "triggered_False_con_k_gt_3_(fallo_el_criterio_relativo_2pct)": 0, "cuantiles_k_obs_de_los_disparos": {"n": 16, "min": 3.04, "p10": 3.07, "p25": 3.29, "p50": 3.82, "p75": 4.59, "p90": 5.36, "max": 7.82}}, "VIIRS375": {"n_records": 954, "k_obs_None": 0, "k_obs_cero": 45, "k_obs_positivo": 909, "triggered_True": 800, "triggered_True_con_k_le_3": 1, "triggered_False_con_k_gt_3_(fallo_el_criterio_relativo_2pct)": 24, "cuantiles_k_obs_de_los_disparos": {"n": 800, "min": 3.0, "p10": 3.52, "p25": 4.05, "p50": 4.86, "p75": 6.02, "p90": 7.59, "max": 16.5}}, "VIIRS750": {"n_records": 949, "k_obs_None": 0, "k_obs_cero": 167, "k_obs_positivo": 782, "triggered_True": 200, "triggered_True_con_k_le_3": 0, "triggered_False_con_k_gt_3_(fallo_el_criterio_relativo_2pct)": 10, "cuantiles_k_obs_de_los_disparos": {"n": 200, "min": 3.01, "p10": 3.12, "p25": 3.32, "p50": 3.81, "p75": 4.53, "p90": 6.15, "max": 9.66}}}
```

### ¿Discrimina el estadístico?

Distribución de k observado entre las pasadas publicadas donde el Test 1 disparó:

| sensor | grupo | n | p25 | mediana | p75 | máx |
|---|---|---|---|---|---|---|
| VIIRS375 | neg_limpio, T1_SOLO | 186 | 3,89 | 4,54 | 5,61 | 12,49 |
| VIIRS375 | neg_limpio, T1_SOBRE_CTX | 56 | 3,83 | 4,41 | 5,83 | 8,68 |
| VIIRS375 | neg_limpio, AMBOS | 63 | 4,37 | 4,93 | 5,90 | 8,28 |
| VIIRS375 | pos, T1_SOLO | 2 | 5,64 | 5,91 | 5,91 | 5,91 |
| VIIRS375 | pos, T1_SOBRE_CTX | 23 | 4,52 | 5,64 | 7,40 | 9,01 |
| VIIRS375 | pos, AMBOS | 118 | 5,07 | 6,06 | 7,37 | 16,50 |
| VIIRS750 | neg_limpio, T1_SOLO | 89 | 3,28 | 3,90 | 4,89 | 8,07 |
| VIIRS750 | neg_limpio, T1_SOBRE_CTX | 11 | 3,11 | 3,43 | 4,34 | 7,42 |
| VIIRS750 | neg_limpio, AMBOS | 9 | 3,56 | 3,63 | 3,79 | 5,62 |
| VIIRS750 | pos, AMBOS | 8 | 3,86 | 4,24 | 7,96 | 9,34 |
| MODIS | neg_limpio, T1_SOLO | 8 | 3,29 | 4,10 | 4,17 | 7,82 |
| MODIS | neg_limpio, AMBOS | 1 | 3,42 | 3,42 | 3,42 | 3,42 |

- **VIIRS375**: probabilidad de que una pasada positiva tenga más sigmas que una de negativo limpio (AUC) = 0,7324 (n neg 305, n pos 143); **estratificada por volcán: 0,6912**.
- **VIIRS750**: probabilidad de que una pasada positiva tenga más sigmas que una de negativo limpio (AUC) = 0,6841 (n neg 109, n pos 8); **estratificada por volcán: 0,5612**.
- **MODIS**: probabilidad de que una pasada positiva tenga más sigmas que una de negativo limpio (AUC) = SIN DATO (n neg 12, n pos 0); **estratificada por volcán: SIN DATO**.

VIIRS 375 por volcán (AUC, n neg, n pos): Lascar 0,55 (22, 18); Lastarria 0,58 (19, 9); Isluga 0,99 (6, 33); Tupungatito 0,73 (13, 26); PlanchonPeteroa 0,50 (29, 8); NevadosDeChillan 0,68 (44, 4); Villarrica 0,60 (38, 5); PuyehueCordonCaulle 0,90 (15, 32); Chaiten 0,56 (32, 8).

Lectura: el estadístico discrimina **poco y de manera desigual**. Separa bien donde hay una fuente fuerte y persistente (Isluga, Puyehue-Cordón Caulle) y casi nada en el resto, donde está cerca de 0,5 a 0,6. Las distribuciones se traslapan de punta a punta: no hay un valle entre dos poblaciones. Parte del AUC agregado es composición por volcán (baja al estratificar), la misma paradoja de Simpson que la Fase 1 ya había medido.

```
== MODIS
   AUC_kobs_pos_vs_neg_entre_publicadas_con_disparo {'auc': None, 'n_neg': 12, 'n_pos': 0}
   AUC_estratificado_por_volcan None
   por volcan: {}
== VIIRS375
   AUC_kobs_pos_vs_neg_entre_publicadas_con_disparo {'auc': 0.7324, 'n_neg': 305, 'n_pos': 143}
   AUC_estratificado_por_volcan 0.6912
   por volcan: {'Lascar': {'auc': 0.548, 'n_neg': 22, 'n_pos': 18}, 'Lastarria': {'auc': 0.5789, 'n_neg': 19, 'n_pos': 9}, 'Isluga': {'auc': 0.9949, 'n_neg': 6, 'n_pos': 33}, 'Tupungatito': {'auc': 0.7263, 'n_neg': 13, 'n_pos': 26}, 'PlanchonPeteroa': {'auc': 0.5022, 'n_neg': 29, 'n_pos': 8}, 'NevadosDeChillan': {'auc': 0.6761, 'n_neg': 44, 'n_pos': 4}, 'Villarrica': {'auc': 0.6, 'n_neg': 38, 'n_pos': 5}, 'PuyehueCordonCaulle': {'auc': 0.9021, 'n_neg': 15, 'n_pos': 32}, 'Chaiten': {'auc': 0.5605, 'n_neg': 32, 'n_pos': 8}}
== VIIRS750
   AUC_kobs_pos_vs_neg_entre_publicadas_con_disparo {'auc': 0.6841, 'n_neg': 109, 'n_pos': 8}
   AUC_estratificado_por_volcan 0.5612
   por volcan: {'PlanchonPeteroa': {'auc': 0.4286, 'n_neg': 14, 'n_pos': 1}, 'PuyehueCordonCaulle': {'auc': 0.5833, 'n_neg': 12, 'n_pos': 7}}
```

### La curva

Publicación en negativos limpios por PASADA (rango mínimo a máximo: el mínimo da por caídas las SIN DATO, el máximo las da por publicadas) y NOCHES positivas por sensor:

**VIIRS375**

| k | neg. limpios que caen (T1_SOLO) | SIN DATO | tasa de publicación mín a máx | pasadas pos que caen / SIN DATO | noches pos: siguen / SIN DATO / se pierden / ya no publicadas hoy | contraste neg menos pos | nulo (p2,5 a p97,5) | fuera del nulo |
|---|---|---|---|---|---|---|---|---|
| 3,0 | 0 | 0 | 86,3 % a 86,3 % | 0 / 0 | 75 / 0 / 0 / 0 | 0,0000 | 0,0000 a 0,0000 | no |
| 3,5 | 20 | 9 | 78,5 % a 81,0 % | 0 / 0 | 75 / 0 / 0 / 0 | 0,0621 | -0,0024 a 0,0450 | sí |
| 4,0 | 54 | 17 | 67,3 % a 71,9 % | 0 / 3 | 75 / 0 / 0 / 0 | 0,1467 | 0,0279 a 0,1094 | sí |
| 4,5 | 88 | 30 | 54,7 % a 62,7 % | 0 / 5 | 74 / 1 / 0 / 0 | 0,2383 | 0,0503 a 0,1537 | sí |
| 5,0 | 121 | 35 | 44,5 % a 53,9 % | 0 / 9 | 74 / 1 / 0 / 0 | 0,3128 | 0,0790 a 0,1909 | sí |
| 6,0 | 148 | 44 | 34,8 % a 46,7 % | 2 / 15 | 72 / 3 / 0 / 0 | 0,3407 | 0,0595 a 0,1784 | sí |
| 7,0 | 165 | 47 | 29,5 % a 42,1 % | 2 / 17 | 71 / 4 / 0 / 0 | 0,3796 | 0,0851 a 0,2032 | sí |
| 8,0 | 177 | 51 | 25,2 % a 38,9 % | 2 / 21 | 71 / 4 / 0 / 0 | 0,3889 | 0,0781 a 0,2001 | sí |
| 10,0 | 183 | 56 | 22,2 % a 37,3 % | 2 / 23 | 71 / 4 / 0 / 0 | 0,3935 | 0,0595 a 0,1814 | sí |
| 12,0 | 185 | 56 | 21,7 % a 36,7 % | 2 / 23 | 71 / 4 / 0 / 0 | 0,3997 | 0,0610 a 0,1869 | sí |

**VIIRS750**

| k | neg. limpios que caen (T1_SOLO) | SIN DATO | tasa de publicación mín a máx | pasadas pos que caen / SIN DATO | noches pos: siguen / SIN DATO / se pierden / ya no publicadas hoy | contraste neg menos pos | nulo (p2,5 a p97,5) | fuera del nulo |
|---|---|---|---|---|---|---|---|---|
| 3,0 | 0 | 0 | 21,4 % a 21,4 % | 0 / 0 | 13 / 0 / 0 / 1 | 0,0000 | 0,0000 a 0,0000 | no |
| 3,5 | 27 | 6 | 16,1 % a 17,0 % | 0 / 0 | 11 / 1 / 1 / 1 | 0,2030 | -0,1348 a 0,2030 | no |
| 4,0 | 48 | 8 | 12,4 % a 13,7 % | 0 / 0 | 11 / 1 / 1 / 1 | 0,3609 | -0,0613 a 0,3609 | no |
| 4,5 | 61 | 9 | 10,1 % a 11,6 % | 0 / 0 | 11 / 1 / 1 / 1 | 0,4586 | -0,0480 a 0,3742 | sí |
| 5,0 | 68 | 9 | 9,0 % a 10,4 % | 0 / 0 | 11 / 1 / 1 / 1 | 0,5113 | -0,0723 a 0,4268 | sí |
| 6,0 | 78 | 9 | 7,4 % a 8,8 % | 0 / 0 | 11 / 1 / 1 / 1 | 0,5865 | -0,0816 a 0,4176 | sí |
| 7,0 | 86 | 10 | 5,9 % a 7,6 % | 0 / 0 | 11 / 1 / 1 / 1 | 0,6466 | -0,0214 a 0,4777 | sí |
| 8,0 | 88 | 11 | 5,5 % a 7,2 % | 0 / 0 | 11 / 1 / 1 / 1 | 0,6617 | -0,0064 a 0,4928 | sí |
| 10,0 | 89 | 11 | 5,3 % a 7,1 % | 0 / 0 | 11 / 1 / 1 / 1 | 0,6692 | -0,0064 a 0,5003 | sí |
| 12,0 | 89 | 11 | 5,3 % a 7,1 % | 0 / 0 | 11 / 1 / 1 / 1 | 0,6692 | -0,0064 a 0,5003 | sí |

**MODIS**

| k | neg. limpios que caen (T1_SOLO) | SIN DATO | tasa de publicación mín a máx | pasadas pos que caen / SIN DATO | noches pos: siguen / SIN DATO / se pierden / ya no publicadas hoy | contraste neg menos pos | nulo (p2,5 a p97,5) | fuera del nulo |
|---|---|---|---|---|---|---|---|---|
| 3,0 | 0 | 3 | 10,7 % a 11,4 % | 0 / 0 | 1 / 0 / 0 / 0 | 0,0000 | -1,0000 a 0,0000 | no |
| 3,5 | 3 | 3 | 10,0 % a 10,7 % | 0 / 0 | 1 / 0 / 0 / 0 | 0,0600 | -0,9600 a 0,0600 | no |
| 4,0 | 4 | 3 | 9,8 % a 10,5 % | 0 / 0 | 1 / 0 / 0 / 0 | 0,0800 | -0,9400 a 0,0800 | no |
| 4,5 | 7 | 3 | 9,1 % a 9,8 % | 0 / 0 | 1 / 0 / 0 / 0 | 0,1400 | -0,8800 a 0,1400 | no |
| 5,0 | 7 | 3 | 9,1 % a 9,8 % | 0 / 0 | 1 / 0 / 0 / 0 | 0,1400 | -0,8800 a 0,1400 | no |
| 6,0 | 7 | 3 | 9,1 % a 9,8 % | 0 / 0 | 1 / 0 / 0 / 0 | 0,1400 | -0,8800 a 0,1400 | no |
| 7,0 | 7 | 3 | 9,1 % a 9,8 % | 0 / 0 | 1 / 0 / 0 / 0 | 0,1400 | -0,8800 a 0,1400 | no |
| 8,0 | 8 | 3 | 8,9 % a 9,6 % | 0 / 0 | 1 / 0 / 0 / 0 | 0,1600 | -0,8600 a 0,1600 | no |
| 10,0 | 8 | 3 | 8,9 % a 9,6 % | 0 / 0 | 1 / 0 / 0 / 0 | 0,1600 | -0,8600 a 0,1600 | no |
| 12,0 | 8 | 3 | 8,9 % a 9,6 % | 0 / 0 | 1 / 0 / 0 / 0 | 0,1600 | -0,8600 a 0,1600 | no |

**Noches positivas con cualquier sensor** (la unidad del operador), y aparte la misma curva sin las noches que la Fase 1 dejó SIN DATO (Isluga 2026-09-19, Lastarria 2026-09-01, NevadosDeChillan 2026-09-18, Villarrica 2026-09-16; leídas del JSON de la Fase 1, no transcritas):

| k | noches pos | siguen | SIN DATO | se pierden seguro | sin las de la Fase 1: siguen de n |
|---|---|---|---|---|---|
| 3,0 | 78 | 78 | 0 | 0 | 74 de 74 |
| 3,5 | 78 | 78 | 0 | 0 | 74 de 74 |
| 4,0 | 78 | 78 | 0 | 0 | 74 de 74 |
| 4,5 | 78 | 77 | 1 | 0 | 74 de 74 |
| 5,0 | 78 | 77 | 1 | 0 | 74 de 74 |
| 6,0 | 78 | 75 | 3 | 0 | 74 de 74 |
| 7,0 | 78 | 74 | 4 | 0 | 74 de 74 |
| 8,0 | 78 | 74 | 4 | 0 | 74 de 74 |
| 10,0 | 78 | 74 | 4 | 0 | 74 de 74 |
| 12,0 | 78 | 74 | 4 | 0 | 74 de 74 |

Noches que dejan de estar aseguradas, por umbral (cualquier sensor):

```
{"4.5": [["Villarrica", "2026-09-16", "sin_dato"]], "5.0": [["Villarrica", "2026-09-16", "sin_dato"]], "6.0": [["Isluga", "2026-09-19", "sin_dato"], ["Lastarria", "2026-09-01", "sin_dato"], ["Villarrica", "2026-09-16", "sin_dato"]], "7.0": [["Isluga", "2026-09-19", "sin_dato"], ["Lastarria", "2026-09-01", "sin_dato"], ["NevadosDeChillan", "2026-09-18", "sin_dato"], ["Villarrica", "2026-09-16", "sin_dato"]], "8.0": [["Isluga", "2026-09-19", "sin_dato"], ["Lastarria", "2026-09-01", "sin_dato"], ["NevadosDeChillan", "2026-09-18", "sin_dato"], ["Villarrica", "2026-09-16", "sin_dato"]], "10.0": [["Isluga", "2026-09-19", "sin_dato"], ["Lastarria", "2026-09-01", "sin_dato"], ["NevadosDeChillan", "2026-09-18", "sin_dato"], ["Villarrica", "2026-09-16", "sin_dato"]], "12.0": [["Isluga", "2026-09-19", "sin_dato"], ["Lastarria", "2026-09-01", "sin_dato"], ["NevadosDeChillan", "2026-09-18", "sin_dato"], ["Villarrica", "2026-09-16", "sin_dato"]]}
```

Noches que dejan de estar aseguradas mirando sólo VIIRS 750 (siguen publicadas por VIIRS 375, por eso no aparecen arriba):

```
[["Isluga", "2026-09-05", "sin_dato"], ["PuyehueCordonCaulle", "2026-09-07", "se_pierde"]]
```

```
== MODIS
  k= 3.0: NEG cae   0 sin_dato   3 tasa 0.1071-0.1139 | POS pasadas cae 0 sd 0 | NOCHES {'n_noches_pos': 1, 'sigue': 1} | nulo {'observado': 0.0, 'nulo_media': -0.123, 'nulo_p2.5': -1.0, 'nulo_p97.5': 0.0, 'fuera_del_nulo': False}
  k= 3.5: NEG cae   3 sin_dato   3 tasa 0.1002-0.1071 | POS pasadas cae 0 sd 0 | NOCHES {'n_noches_pos': 1, 'sigue': 1} | nulo {'observado': 0.06, 'nulo_media': -0.218, 'nulo_p2.5': -0.96, 'nulo_p97.5': 0.06, 'fuera_del_nulo': False}
  k= 4.0: NEG cae   4 sin_dato   3 tasa 0.0979-0.1048 | POS pasadas cae 0 sd 0 | NOCHES {'n_noches_pos': 1, 'sigue': 1} | nulo {'observado': 0.08, 'nulo_media': -0.198, 'nulo_p2.5': -0.94, 'nulo_p97.5': 0.08, 'fuera_del_nulo': False}
  k= 4.5: NEG cae   7 sin_dato   3 tasa 0.0911-0.0979 | POS pasadas cae 0 sd 0 | NOCHES {'n_noches_pos': 1, 'sigue': 1} | nulo {'observado': 0.14, 'nulo_media': -0.138, 'nulo_p2.5': -0.88, 'nulo_p97.5': 0.14, 'fuera_del_nulo': False}
  k= 5.0: NEG cae   7 sin_dato   3 tasa 0.0911-0.0979 | POS pasadas cae 0 sd 0 | NOCHES {'n_noches_pos': 1, 'sigue': 1} | nulo {'observado': 0.14, 'nulo_media': -0.138, 'nulo_p2.5': -0.88, 'nulo_p97.5': 0.14, 'fuera_del_nulo': False}
  k= 6.0: NEG cae   7 sin_dato   3 tasa 0.0911-0.0979 | POS pasadas cae 0 sd 0 | NOCHES {'n_noches_pos': 1, 'sigue': 1} | nulo {'observado': 0.14, 'nulo_media': -0.138, 'nulo_p2.5': -0.88, 'nulo_p97.5': 0.14, 'fuera_del_nulo': False}
  k= 7.0: NEG cae   7 sin_dato   3 tasa 0.0911-0.0979 | POS pasadas cae 0 sd 0 | NOCHES {'n_noches_pos': 1, 'sigue': 1} | nulo {'observado': 0.14, 'nulo_media': -0.138, 'nulo_p2.5': -0.88, 'nulo_p97.5': 0.14, 'fuera_del_nulo': False}
  k= 8.0: NEG cae   8 sin_dato   3 tasa 0.0888-0.0957 | POS pasadas cae 0 sd 0 | NOCHES {'n_noches_pos': 1, 'sigue': 1} | nulo {'observado': 0.16, 'nulo_media': -0.2527, 'nulo_p2.5': -0.86, 'nulo_p97.5': 0.16, 'fuera_del_nulo': False}
  k=10.0: NEG cae   8 sin_dato   3 tasa 0.0888-0.0957 | POS pasadas cae 0 sd 0 | NOCHES {'n_noches_pos': 1, 'sigue': 1} | nulo {'observado': 0.16, 'nulo_media': -0.2527, 'nulo_p2.5': -0.86, 'nulo_p97.5': 0.16, 'fuera_del_nulo': False}
  k=12.0: NEG cae   8 sin_dato   3 tasa 0.0888-0.0957 | POS pasadas cae 0 sd 0 | NOCHES {'n_noches_pos': 1, 'sigue': 1} | nulo {'observado': 0.16, 'nulo_media': -0.2527, 'nulo_p2.5': -0.86, 'nulo_p97.5': 0.16, 'fuera_del_nulo': False}
== VIIRS375
  k= 3.0: NEG cae   0 sin_dato   0 tasa 0.8633-0.8633 | POS pasadas cae 0 sd 0 | NOCHES {'n_noches_pos': 75, 'sigue': 75} | nulo {'observado': 0.0, 'nulo_media': 0.0, 'nulo_p2.5': 0.0, 'nulo_p97.5': 0.0, 'fuera_del_nulo': False}
  k= 3.5: NEG cae  20 sin_dato   9 tasa 0.7855-0.8097 | POS pasadas cae 0 sd 0 | NOCHES {'n_noches_pos': 75, 'sigue': 75} | nulo {'observado': 0.0621, 'nulo_media': 0.0241, 'nulo_p2.5': -0.0024, 'nulo_p97.5': 0.045, 'fuera_del_nulo': True}
  k= 4.0: NEG cae  54 sin_dato  17 tasa 0.6729-0.7185 | POS pasadas cae 0 sd 3 | NOCHES {'n_noches_pos': 75, 'sigue': 75} | nulo {'observado': 0.1467, 'nulo_media': 0.072, 'nulo_p2.5': 0.0279, 'nulo_p97.5': 0.1094, 'fuera_del_nulo': True}
  k= 4.5: NEG cae  88 sin_dato  30 tasa 0.5469-0.6273 | POS pasadas cae 0 sd 5 | NOCHES {'n_noches_pos': 75, 'sigue': 74, 'sin_dato': 1} | nulo {'observado': 0.2383, 'nulo_media': 0.1025, 'nulo_p2.5': 0.0503, 'nulo_p97.5': 0.1537, 'fuera_del_nulo': True}
  k= 5.0: NEG cae 121 sin_dato  35 tasa 0.445-0.5389 | POS pasadas cae 0 sd 9 | NOCHES {'n_noches_pos': 75, 'sigue': 74, 'sin_dato': 1} | nulo {'observado': 0.3128, 'nulo_media': 0.135, 'nulo_p2.5': 0.079, 'nulo_p97.5': 0.1909, 'fuera_del_nulo': True}
  k= 6.0: NEG cae 148 sin_dato  44 tasa 0.3485-0.4665 | POS pasadas cae 2 sd 15 | NOCHES {'n_noches_pos': 75, 'sigue': 72, 'sin_dato': 3} | nulo {'observado': 0.3407, 'nulo_media': 0.1208, 'nulo_p2.5': 0.0595, 'nulo_p97.5': 0.1784, 'fuera_del_nulo': True}
  k= 7.0: NEG cae 165 sin_dato  47 tasa 0.2949-0.4209 | POS pasadas cae 2 sd 17 | NOCHES {'n_noches_pos': 75, 'sigue': 71, 'sin_dato': 4} | nulo {'observado': 0.3796, 'nulo_media': 0.1468, 'nulo_p2.5': 0.0851, 'nulo_p97.5': 0.2032, 'fuera_del_nulo': True}
  k= 8.0: NEG cae 177 sin_dato  51 tasa 0.252-0.3887 | POS pasadas cae 2 sd 21 | NOCHES {'n_noches_pos': 75, 'sigue': 71, 'sin_dato': 4} | nulo {'observado': 0.3889, 'nulo_media': 0.1412, 'nulo_p2.5': 0.0781, 'nulo_p97.5': 0.2001, 'fuera_del_nulo': True}
  k=10.0: NEG cae 183 sin_dato  56 tasa 0.2225-0.3727 | POS pasadas cae 2 sd 23 | NOCHES {'n_noches_pos': 75, 'sigue': 71, 'sin_dato': 4} | nulo {'observado': 0.3935, 'nulo_media': 0.1211, 'nulo_p2.5': 0.0595, 'nulo_p97.5': 0.1814, 'fuera_del_nulo': True}
  k=12.0: NEG cae 185 sin_dato  56 tasa 0.2172-0.3673 | POS pasadas cae 2 sd 23 | NOCHES {'n_noches_pos': 75, 'sigue': 71, 'sin_dato': 4} | nulo {'observado': 0.3997, 'nulo_media': 0.125, 'nulo_p2.5': 0.061, 'nulo_p97.5': 0.1869, 'fuera_del_nulo': True}
== VIIRS750
  k= 3.0: NEG cae   0 sin_dato   0 tasa 0.2138-0.2138 | POS pasadas cae 0 sd 0 | NOCHES {'n_noches_pos': 14, 'sigue': 13, 'no_publicada_hoy': 1} | nulo {'observado': 0.0, 'nulo_media': 0.0, 'nulo_p2.5': 0.0, 'nulo_p97.5': 0.0, 'fuera_del_nulo': False}
  k= 3.5: NEG cae  27 sin_dato   6 tasa 0.1608-0.1704 | POS pasadas cae 0 sd 0 | NOCHES {'n_noches_pos': 14, 'sin_dato': 1, 'sigue': 11, 'se_pierde': 1, 'no_publicada_hoy': 1} | nulo {'observado': 0.203, 'nulo_media': 0.0355, 'nulo_p2.5': -0.1348, 'nulo_p97.5': 0.203, 'fuera_del_nulo': False}
  k= 4.0: NEG cae  48 sin_dato   8 tasa 0.1238-0.1367 | POS pasadas cae 0 sd 0 | NOCHES {'n_noches_pos': 14, 'sin_dato': 1, 'sigue': 11, 'se_pierde': 1, 'no_publicada_hoy': 1} | nulo {'observado': 0.3609, 'nulo_media': 0.1256, 'nulo_p2.5': -0.0613, 'nulo_p97.5': 0.3609, 'fuera_del_nulo': False}
  k= 4.5: NEG cae  61 sin_dato   9 tasa 0.1013-0.1158 | POS pasadas cae 0 sd 0 | NOCHES {'n_noches_pos': 14, 'sin_dato': 1, 'sigue': 11, 'se_pierde': 1, 'no_publicada_hoy': 1} | nulo {'observado': 0.4586, 'nulo_media': 0.1718, 'nulo_p2.5': -0.048, 'nulo_p97.5': 0.3742, 'fuera_del_nulo': True}
  k= 5.0: NEG cae  68 sin_dato   9 tasa 0.09-0.1045 | POS pasadas cae 0 sd 0 | NOCHES {'n_noches_pos': 14, 'sin_dato': 1, 'sigue': 11, 'se_pierde': 1, 'no_publicada_hoy': 1} | nulo {'observado': 0.5113, 'nulo_media': 0.162, 'nulo_p2.5': -0.0723, 'nulo_p97.5': 0.4268, 'fuera_del_nulo': True}
  k= 6.0: NEG cae  78 sin_dato   9 tasa 0.074-0.0884 | POS pasadas cae 0 sd 0 | NOCHES {'n_noches_pos': 14, 'sin_dato': 1, 'sigue': 11, 'se_pierde': 1, 'no_publicada_hoy': 1} | nulo {'observado': 0.5865, 'nulo_media': 0.1784, 'nulo_p2.5': -0.0816, 'nulo_p97.5': 0.4176, 'fuera_del_nulo': True}
  k= 7.0: NEG cae  86 sin_dato  10 tasa 0.0595-0.0756 | POS pasadas cae 0 sd 0 | NOCHES {'n_noches_pos': 14, 'sin_dato': 1, 'sigue': 11, 'se_pierde': 1, 'no_publicada_hoy': 1} | nulo {'observado': 0.6466, 'nulo_media': 0.2246, 'nulo_p2.5': -0.0214, 'nulo_p97.5': 0.4777, 'fuera_del_nulo': True}
  k= 8.0: NEG cae  88 sin_dato  11 tasa 0.0547-0.0723 | POS pasadas cae 0 sd 0 | NOCHES {'n_noches_pos': 14, 'sin_dato': 1, 'sigue': 11, 'se_pierde': 1, 'no_publicada_hoy': 1} | nulo {'observado': 0.6617, 'nulo_media': 0.2345, 'nulo_p2.5': -0.0064, 'nulo_p97.5': 0.4928, 'fuera_del_nulo': True}
  k=10.0: NEG cae  89 sin_dato  11 tasa 0.0531-0.0707 | POS pasadas cae 0 sd 0 | NOCHES {'n_noches_pos': 14, 'sin_dato': 1, 'sigue': 11, 'se_pierde': 1, 'no_publicada_hoy': 1} | nulo {'observado': 0.6692, 'nulo_media': 0.2206, 'nulo_p2.5': -0.0064, 'nulo_p97.5': 0.5003, 'fuera_del_nulo': True}
  k=12.0: NEG cae  89 sin_dato  11 tasa 0.0531-0.0707 | POS pasadas cae 0 sd 0 | NOCHES {'n_noches_pos': 14, 'sin_dato': 1, 'sigue': 11, 'se_pierde': 1, 'no_publicada_hoy': 1} | nulo {'observado': 0.6692, 'nulo_media': 0.2206, 'nulo_p2.5': -0.0064, 'nulo_p97.5': 0.5003, 'fuera_del_nulo': True}
== CUALQUIER sensor, noches:
  k=3.0: {'n_noches_pos': 78, 'sigue': 78} | sin las SIN DATO F1: {'n_noches_pos': 74, 'sigue': 74}
  k=3.5: {'n_noches_pos': 78, 'sigue': 78} | sin las SIN DATO F1: {'n_noches_pos': 74, 'sigue': 74}
  k=4.0: {'n_noches_pos': 78, 'sigue': 78} | sin las SIN DATO F1: {'n_noches_pos': 74, 'sigue': 74}
  k=4.5: {'n_noches_pos': 78, 'sigue': 77, 'sin_dato': 1} | sin las SIN DATO F1: {'n_noches_pos': 74, 'sigue': 74}
  k=5.0: {'n_noches_pos': 78, 'sigue': 77, 'sin_dato': 1} | sin las SIN DATO F1: {'n_noches_pos': 74, 'sigue': 74}
  k=6.0: {'n_noches_pos': 78, 'sigue': 75, 'sin_dato': 3} | sin las SIN DATO F1: {'n_noches_pos': 74, 'sigue': 74}
  k=7.0: {'n_noches_pos': 78, 'sigue': 74, 'sin_dato': 4} | sin las SIN DATO F1: {'n_noches_pos': 74, 'sigue': 74}
  k=8.0: {'n_noches_pos': 78, 'sigue': 74, 'sin_dato': 4} | sin las SIN DATO F1: {'n_noches_pos': 74, 'sigue': 74}
  k=10.0: {'n_noches_pos': 78, 'sigue': 74, 'sin_dato': 4} | sin las SIN DATO F1: {'n_noches_pos': 74, 'sigue': 74}
  k=12.0: {'n_noches_pos': 78, 'sigue': 74, 'sin_dato': 4} | sin las SIN DATO F1: {'n_noches_pos': 74, 'sigue': 74}
```

### Las noches SIN DATO de la Fase 1, una por una

Son las únicas noches positivas cuyo sostén pasa por el Test 1. En las cuatro, la pasada que MIROVA alertó la sostiene el Test 1 (sola o reconstruyendo el cúmulo contextual), con estos sigmas:

| noche | pasada | sensor | etiqueta | clase | k observado | MW publicados |
|---|---|---|---|---|---|---|
| Lastarria 2026-09-01 | 05:18 | VIIRS375 | sin_info | T1_SOLO (test1_roi) | 3,32 | 0,0338 |
| Lastarria 2026-09-01 | 05:36 | VIIRS375 | pos | T1_SOBRE_CTX (ctx_cluster, rival_debil_lt_0.01MW) | 4,84 | 0,1101 |
| Lastarria 2026-09-01 | 06:24 | VIIRS375 | sin_info | T1_SOBRE_CTX (ctx_cluster, fuente_unica) | 5,05 | 0,0407 |
| Isluga 2026-09-19 | 05:00 | VIIRS375 | far_ref | T1_SOBRE_CTX (ctx_cluster, rival_debil_lt_0.01MW) | 4,14 | 0,0705 |
| Isluga 2026-09-19 | 05:42 | VIIRS375 | pos | T1_SOLO (test1_roi) | 5,91 | 0,0531 |
| Isluga 2026-09-19 | 06:18 | VIIRS375 | sin_info | T1_SOLO (test1_roi) | 4,18 | 0,0517 |
| Isluga 2026-09-19 | 06:42 | VIIRS375 | sin_info | T1_SOBRE_CTX (ctx_cluster, fuente_unica) | 5,26 | 0,0696 |
| Isluga 2026-09-19 | 06:42 | VIIRS750 | sin_info | T1_SOLO (test1_roi) | 3,39 | 0,2060 |
| NevadosDeChillan 2026-09-18 | 05:06 | VIIRS375 | sin_info | T1_SOBRE_CTX (ctx_cluster, fuente_unica) | 3,69 | 0,0319 |
| NevadosDeChillan 2026-09-18 | 05:24 | VIIRS375 | pos | T1_SOLO (test1_roi) | 5,64 | 0,0473 |
| NevadosDeChillan 2026-09-18 | 06:06 | VIIRS375 | far_ref | T1_SOBRE_CTX (ctx_cluster, rival_debil_lt_0.01MW) | 6,34 | 0,0522 |
| NevadosDeChillan 2026-09-18 | 06:42 | VIIRS375 | sin_info | T1_SOLO (test1_roi) | 4,33 | 0,0425 |
| Villarrica 2026-09-16 | 05:42 | VIIRS375 | sin_info | T1_SOLO (test1_roi) | 4,21 | 0,0298 |
| Villarrica 2026-09-16 | 06:00 | VIIRS375 | pos | T1_SOBRE_CTX (ctx_cluster, fuente_unica) | 3,93 | 0,1053 |

Ninguna se *pierde seguro* a ningún k, porque todas tienen alguna pasada T1_SOBRE_CTX, que es SIN DATO y no pérdida. Pero eso es una propiedad de la cota, no del volcán: para saber si esas cuatro noches se publicarían por el camino contextual hace falta el probe que la Fase 1 dejó especificado.

### Por volcán (VIIRS 375)

| volcán | neg. limpios publicados / n | caen a k = 4 | k = 5 | k = 6 | k = 8 | k = 12 | pasadas pos publicadas | pos que dejan de estar seguras a k = 4 / 5 / 6 / 8 / 12 | noches pos: siguen a k = 5 / 8 de n |
|---|---|---|---|---|---|---|---|---|---|
| Lascar | 22 / 25 | 2 | 6 | 7 | 7 | 8 | 18 | 0 / 2 / 3 / 3 / 3 | 10 / 10 de 10 |
| Lastarria | 21 / 24 | 1 | 6 | 9 | 12 | 13 | 9 | 0 / 2 / 2 / 3 / 3 | 7 / 6 de 7 |
| Isluga | 7 / 9 | 1 | 1 | 1 | 1 | 1 | 33 | 1 / 1 / 5 / 8 / 9 | 15 / 14 de 15 |
| Tupungatito | 13 / 14 | 0 | 3 | 5 | 5 | 6 | 26 | 1 / 2 / 4 / 6 / 7 | 12 / 12 de 12 |
| PlanchonPeteroa | 30 / 35 | 7 | 12 | 15 | 18 | 20 | 8 | 0 / 0 / 0 / 0 / 0 | 6 / 6 de 6 |
| NevadosDeChillan | 44 / 48 | 2 | 13 | 18 | 26 | 26 | 4 | 0 / 0 / 1 / 1 / 1 | 4 / 3 de 4 |
| Llaima | 45 / 57 | 12 | 19 | 22 | 26 | 26 | 0 | 0 / 0 / 0 / 0 / 0 | 0 / 0 de 0 |
| Villarrica | 40 / 48 | 10 | 22 | 24 | 27 | 27 | 5 | 1 / 2 / 2 / 2 / 2 | 5 / 5 de 6 |
| Copahue | 48 / 57 | 15 | 30 | 34 | 37 | 39 | 0 | 0 / 0 / 0 / 0 / 0 | 0 / 0 de 0 |
| PuyehueCordonCaulle | 17 / 18 | 0 | 0 | 1 | 1 | 2 | 32 | 0 / 0 / 0 / 0 / 0 | 12 / 12 de 12 |
| Chaiten | 35 / 38 | 4 | 9 | 12 | 17 | 17 | 8 | 0 / 0 / 0 / 0 / 0 | 6 / 6 de 6 |

La dosis rinde donde el relieve manda y no hay fuente (Copahue, Villarrica, Llaima, Nevados de Chillán, Planchón-Peteroa, Chaitén) y casi no mueve nada en Puyehue-Cordón Caulle ni en Isluga, que publican por el camino contextual. Llaima y Copahue no tienen noches positivas en la ventana: ahí el costo en recall es SIN DATO, no cero.

### Veredicto de P1

- **No existe un umbral que separe.** El k observado de los negativos limpios y el de los positivos se traslapan entero (AUC estratificado 0,6912 en VIIRS 375 y 0,5612 en VIIRS 750). La curva es una rampa sin codo: a k = 4 caen 54 de 186 T1_SOLO, a k = 5 caen 121, y para sacar casi todos (185) hay que ir a k = 12, que es lo mismo que apagar el Test 1.
- **Pero la dosis funciona igual, por otra razón**: no porque el Test 1 distinga, sino porque el recall casi no depende de él. El contraste queda fuera del nulo barajado en VIIRS 375 desde k = 3,5, y en noches con cualquier sensor no se pierde ninguna con seguridad a ningún k: todas siguen hasta k = 4, una pasa a SIN DATO a k = 4,5 y son 4 SIN DATO desde k = 7 (las mismas cuatro de la Fase 1).
- **Cuánto rinde**: en VIIRS 375 la publicación en negativos limpios iría de 86,3 % a entre 67,3 % y 71,9 % con k = 4, y a entre 44,5 % y 53,9 % con k = 5. En VIIRS 750, de 21,4 % a entre 9,0 % y 10,4 % con k = 5. MODIS casi no tiene sustrato (el Test 1 sostiene 8 de 50) y un solo positivo: SIN DATO.
- **Qué dice para el A/B**: un umbral intermedio no compra nada que no compre mejor mudar el Test 1 al experimental. No hay un k «natural» que defender; cualquier k entre 4 y 8 es un punto arbitrario de una rampa. Si igual se quiere un brazo graduado, k = 4 es el último sin ninguna noche en duda y k = 5 el que tiene una sola (Villarrica 2026-09-16). El piso que queda sin el Test 1 (la publicación por el camino contextual, que es el del paper) no lo toca ningún k.
- **Límites**: 20 días de un solo régimen; cota y no re-ejecución; las pasadas T1_SOBRE_CTX (56 en negativos de VIIRS 375) son SIN DATO y ensanchan el rango; en Láscar, Nevados de Chillán y Lastarria el Test 1 corre con el anillo intermedio de S112 y su k observado no es comparable uno a uno con el de los otros volcanes (no lo separé: SOSPECHA).

## 2. P2: re-lectura de los A/B de S135 y S143, por volcán y en unidades del operador

> **Esto es una re-lectura posterior y exploratoria.** Los dos A/B tienen pre-registro (`docs/PREREGISTRO_AB_D1_D2_S135.md`, `docs/PREREGISTRO_AB_D22_D25_S143.md`) y veredicto NO ADOPTAR, y eso **no cambia**: el criterio se fijó antes de ver los datos y un brazo no se adopta por una lectura hecha después. Lo que sigue sirve para decidir qué brazos vale la pena llevar a un A/B nuevo, con ventana nueva.

### El fenómeno y por qué releer

Los dos experimentos tocaron la misma pieza: `keep_peak`, la regla que conserva el píxel pico del Test 1 cuando el filtro contextual no deja nada. Físicamente ese píxel es muchas veces relieve tibio a 2 o 3 km del cráter, no la fuente. Los dos veredictos cayeron por criterios que no están en las unidades del operador: S135 por una mediana agregada de magnitud que empeoraba 0,016, y S143 por 5 noches «perdidas» según una cota escalar de radios que después se mostró incapaz de identificar el objeto (A107). La pregunta del operador es otra: esa noche, ¿se publicó o no?, y en las pasadas donde MIROVA miró y no vio nada, ¿publicamos o no?

### El mecanismo de la re-lectura

Se leen los JSON por brazo y volcán tal como salieron de GitHub Actions (S135: `experiments/_artefactos_ab/s135ab-*`, los dos tramos fusionados en memoria; S143: la carpeta fusionada que cita `resultado_ab_s143.json`). Se les aplica el banco de paridad de S145, con la referencia fijada por sha de `experiments/_s143_evaluador/_dl_referencia`. Ventana 2026-06-01 a 2026-08-31, sólo VIIRS 375. La ventana cruza el 2026-08-28, pero acá no mezcla regímenes: todos los brazos son reprocesos hechos en septiembre con un mismo código (ver `processed_utc` en la salida cruda), no datos de producción. Recall por NOCHE de dos maneras, ninguna con cota de distancia: (a) el brazo publica alguna pasada esa noche; (b) el brazo publica la misma pasada que MIROVA alertó. Publicación por PASADA pareada contra el control, con prueba de signos exacta. Regla de lectura fijada antes de mirar la tabla: muestra suficiente = 30 negativos limpios y 10 noches positivas; GANA = 0 noches perdidas y baja la publicación con p < 0,05; EMPATA = 0 noches perdidas y diferencia indistinguible; PIERDE = pierde alguna noche o sube la publicación.

### Controles del instrumento

- Control positivo: con el control y el `literal` de S143 reproduzco los números publicados por el evaluador de S143 (n = 1170 negativos limpios, control 0,9171, literal 0,5470, 442 pasadas que sólo publica el control): **sí**. Noches con alerta por volcán iguales a las del evaluador: **NO**.
- Control contra sí mismo (instrumento muerto): control contra control da {'S143': {'solo_control': 0, 'solo_brazo': 0, 'perdidas': 0}, 'S135': {'solo_control': 0, 'solo_brazo': 0, 'perdidas': 0}} discordantes.
- Cobertura pareja (A108): volcanes excluidos por pasadas de menos, S143 ninguno, S135 ninguno.
- Nulo: si brazo y control fueran lo mismo, los discordantes se repartirían al azar y ganaría a lo más 1 volcán por brazo (p97,5).

```
REFERENCIA 92f26b98b490_registro_vrp_consolidado.csv f9805ad397dc_registro_vrp_ocr.csv filas nocturnas en ventana: 7842 | evaluador S143 uso: 7842
CONTROL POSITIVO S143 {"esperado_del_json_de_S143": {"neg_n": 1170, "tasa_control": 0.9171, "tasa_literal": 0.547, "solo_control_literal": 442, "noches_alerta": {"Isluga": 74, "Lascar": 61, "Lastarria": 50, "PlanchonPeteroa": 28, "PuyehueCordonCaulle": 37, "Tupungatito": 29, "Chaiten": 14, "Villarrica": 11, "NevadosDeChillan": 5}}, "mio": {"neg_n": 1170, "tasa_control": 0.9171, "tasa_literal": 0.547, "solo_control_literal": 442, "noches_alerta": {"Isluga": 74, "Lascar": 61, "Lastarria": 50, "PlanchonPeteroa": 28, "PuyehueCordonCaulle": 37, "Tupungatito": 28, "Chaiten": 14, "Villarrica": 11, "NevadosDeChillan": 5}}, "reproduce": true, "noches_alerta_iguales": false}
   processed_utc: {'_s142_ab_control': ('2026-09-17T19:47:28Z', '2026-09-19T01:51:09Z'), '_s142_ab_literal': ('2026-09-17T19:47:20Z', '2026-09-19T16:10:29Z'), '_s142_ab_lit_sin_fondo': ('2026-09-17T19:46:59Z', '2026-09-19T02:08:35Z'), '_s142_ab_lit_con_compuerta': ('2026-09-17T19:47:01Z', '2026-09-19T02:07:36Z'), '_s142_ab_lit_sp_suelto': ('2026-09-17T19:47:00Z', '2026-09-19T02:32:30Z'), '_s142_ab_lit_keep_peak': ('2026-09-17T19:46:59Z', '2026-09-19T02:43:29Z')}
   NULO: {"_s142_ab_literal": {"n_vol_suficientes": 7, "gana_bajo_nulo_media": 0.127, "gana_bajo_nulo_p97.5": 1}, "_s142_ab_lit_sin_fondo": {"n_vol_suficientes": 7, "gana_bajo_nulo_media": 0.109, "gana_bajo_nulo_p97.5": 1}, "_s142_ab_lit_con_compuerta": {"n_vol_suficientes": 7, "gana_bajo_nulo_media": 0.137, "gana_bajo_nulo_p97.5": 1}, "_s142_ab_lit_sp_suelto": {"n_vol_suficientes": 7, "gana_bajo_nulo_media": 0.131, "gana_bajo_nulo_p97.5": 1}, "_s142_ab_lit_keep_peak": {"n_vol_suficientes": 7, "gana_bajo_nulo_media": 0.0, "gana_bajo_nulo_p97.5": 0}}
   processed_utc: {'_s135_ab_a_control': ('2026-09-08T00:35:27Z', '2026-09-08T17:32:26Z'), '_s135_ab_b_nokeeppeak': ('2026-09-08T00:35:27Z', '2026-09-08T18:02:46Z'), '_s135_ab_c_cond': ('2026-09-08T00:35:21Z', '2026-09-08T18:27:41Z'), '_s135_ab_d_ambos': ('2026-09-08T00:35:26Z', '2026-09-08T18:21:13Z'), '_s135_ab_e_sp_off': ('2026-09-08T00:35:47Z', '2026-09-08T18:26:41Z')}
   NULO: {"_s135_ab_b_nokeeppeak": {"n_vol_suficientes": 5, "gana_bajo_nulo_media": 0.078, "gana_bajo_nulo_p97.5": 1}, "_s135_ab_c_cond": {"n_vol_suficientes": 5, "gana_bajo_nulo_media": 0.0, "gana_bajo_nulo_p97.5": 0}, "_s135_ab_d_ambos": {"n_vol_suficientes": 5, "gana_bajo_nulo_media": 0.084, "gana_bajo_nulo_p97.5": 1}, "_s135_ab_e_sp_off": {"n_vol_suficientes": 5, "gana_bajo_nulo_media": 0.0, "gana_bajo_nulo_p97.5": 0}}
CONTROL CONTRA SI MISMO {'S143': {'solo_control': 0, 'solo_brazo': 0, 'perdidas': 0}, 'S135': {'solo_control': 0, 'solo_brazo': 0, 'perdidas': 0}}
```

### S143: tabla por brazo y volcán

**_s142_ab_literal**

| volcán | muestra suficiente | neg. limpios: brazo / control (n) | sólo control / sólo brazo | p | noches pos | publicadas (a) brazo / control | publicadas (b) brazo / control | razón de magnitud brazo / control (pares) | lectura |
|---|---|---|---|---|---|---|---|---|---|
| Isluga | no | 66,7 % / 90,5 % (21) | 6 / 1 | 0,1250 | 74 | 74 / 74 | 74 / 74 | 0,881 / 0,632 (131) | EMPATA |
| Lascar | sí | 48,0 % / 82,0 % (50) | 18 / 1 | 0,0001 | 61 | 61 / 61 | 61 / 61 | 0,740 / 0,629 (110) | GANA |
| Lastarria | sí | 51,9 % / 96,2 % (52) | 23 / 0 | 0,0000 | 50 | 50 / 50 | 50 / 50 | 0,974 / 0,965 (74) | GANA |
| PlanchonPeteroa | sí | 42,4 % / 95,1 % (144) | 76 / 0 | 0,0000 | 28 | 28 / 28 | 28 / 28 | 0,995 / 0,956 (44) | GANA |
| PuyehueCordonCaulle | sí | 86,3 % / 95,9 % (146) | 14 / 0 | 0,0001 | 37 | 37 / 37 | 37 / 37 | 1,022 / 1,021 (86) | GANA |
| Tupungatito | sí | 71,3 % / 94,3 % (122) | 29 / 1 | 0,0000 | 28 | 28 / 28 | 28 / 28 | 1,113 / 0,562 (51) | GANA |
| Chaiten | sí | 62,7 % / 93,2 % (220) | 67 / 0 | 0,0000 | 14 | 14 / 14 | 14 / 14 | 1,481 / 1,296 (17) | GANA |
| Villarrica | sí | 36,7 % / 88,1 % (218) | 112 / 0 | 0,0000 | 11 | 11 / 11 | 11 / 11 | 0,893 / 0,860 (11) | GANA |
| NevadosDeChillan | no | 42,1 % / 88,3 % (197) | 97 / 6 | 0,0000 | 5 | 5 / 5 | 5 / 5 | 1,321 / 1,208 (6) | GANA |
| TODOS | sí | 54,7 % / 91,7 % (1170) | 442 / 9 | 0,0000 | 308 | 308 / 308 | 308 / 308 | 0,945 / 0,773 (530) | GANA |

Con muestra suficiente (7 volcanes): gana en 7 (Lascar, Lastarria, PlanchonPeteroa, PuyehueCordonCaulle, Tupungatito, Chaiten, Villarrica), empata en 0 (ninguno), pierde en 0 (ninguno). Nulo: ganaría en 1 a lo más. Noches perdidas (b) en todos los volcanes, con o sin muestra: 0.

**_s142_ab_lit_sin_fondo**

| volcán | muestra suficiente | neg. limpios: brazo / control (n) | sólo control / sólo brazo | p | noches pos | publicadas (a) brazo / control | publicadas (b) brazo / control | razón de magnitud brazo / control (pares) | lectura |
|---|---|---|---|---|---|---|---|---|---|
| Isluga | no | 42,9 % / 90,5 % (21) | 10 / 0 | 0,0020 | 74 | 74 / 74 | 72 / 74 | 0,582 / 0,632 (125) | PIERDE(noches) |
| Lascar | sí | 30,0 % / 82,0 % (50) | 26 / 0 | 0,0000 | 61 | 61 / 61 | 61 / 61 | 0,626 / 0,631 (109) | GANA |
| Lastarria | sí | 51,9 % / 96,2 % (52) | 23 / 0 | 0,0000 | 50 | 50 / 50 | 50 / 50 | 1,012 / 0,965 (74) | GANA |
| PlanchonPeteroa | sí | 42,4 % / 95,1 % (144) | 76 / 0 | 0,0000 | 28 | 28 / 28 | 28 / 28 | 0,997 / 0,956 (44) | GANA |
| PuyehueCordonCaulle | sí | 86,3 % / 95,9 % (146) | 14 / 0 | 0,0001 | 37 | 37 / 37 | 37 / 37 | 1,028 / 1,021 (86) | GANA |
| Tupungatito | sí | 60,7 % / 94,3 % (122) | 41 / 0 | 0,0000 | 28 | 28 / 28 | 28 / 28 | 0,494 / 0,556 (50) | GANA |
| Chaiten | sí | 62,7 % / 93,2 % (220) | 67 / 0 | 0,0000 | 14 | 14 / 14 | 14 / 14 | 1,493 / 1,296 (17) | GANA |
| Villarrica | sí | 36,7 % / 88,1 % (218) | 112 / 0 | 0,0000 | 11 | 11 / 11 | 11 / 11 | 0,893 / 0,860 (11) | GANA |
| NevadosDeChillan | no | 24,9 % / 88,3 % (197) | 125 / 0 | 0,0000 | 5 | 2 / 5 | 2 / 5 | 1,160 / 1,160 (2) | PIERDE(noches) |
| TODOS | sí | 49,5 % / 91,7 % (1170) | 494 / 0 | 0,0000 | 308 | 305 / 308 | 303 / 308 | 0,748 / 0,768 (518) | PIERDE(noches) |

Con muestra suficiente (7 volcanes): gana en 7 (Lascar, Lastarria, PlanchonPeteroa, PuyehueCordonCaulle, Tupungatito, Chaiten, Villarrica), empata en 0 (ninguno), pierde en 0 (ninguno). Nulo: ganaría en 1 a lo más. Noches perdidas (b) en todos los volcanes, con o sin muestra: 5 (Isluga 2026-06-30; Isluga 2026-07-28; NevadosDeChillan 2026-06-16; NevadosDeChillan 2026-08-18; NevadosDeChillan 2026-08-20).

**_s142_ab_lit_con_compuerta**

| volcán | muestra suficiente | neg. limpios: brazo / control (n) | sólo control / sólo brazo | p | noches pos | publicadas (a) brazo / control | publicadas (b) brazo / control | razón de magnitud brazo / control (pares) | lectura |
|---|---|---|---|---|---|---|---|---|---|
| Isluga | no | 28,6 % / 90,5 % (21) | 13 / 0 | 0,0002 | 74 | 69 / 74 | 64 / 74 | 0,859 / 0,614 (106) | PIERDE(noches) |
| Lascar | sí | 14,0 % / 82,0 % (50) | 34 / 0 | 0,0000 | 61 | 61 / 61 | 61 / 61 | 0,740 / 0,629 (104) | GANA |
| Lastarria | sí | 26,9 % / 96,2 % (52) | 36 / 0 | 0,0000 | 50 | 48 / 50 | 46 / 50 | 0,910 / 1,008 (65) | PIERDE(noches) |
| PlanchonPeteroa | sí | 25,0 % / 95,1 % (144) | 101 / 0 | 0,0000 | 28 | 23 / 28 | 23 / 28 | 0,904 / 0,905 (31) | PIERDE(noches) |
| PuyehueCordonCaulle | sí | 78,8 % / 95,9 % (146) | 25 / 0 | 0,0000 | 37 | 37 / 37 | 37 / 37 | 0,985 / 1,021 (80) | GANA |
| Tupungatito | sí | 42,6 % / 94,3 % (122) | 63 / 0 | 0,0000 | 28 | 26 / 28 | 25 / 28 | 1,075 / 0,539 (39) | PIERDE(noches) |
| Chaiten | sí | 40,0 % / 93,2 % (220) | 117 / 0 | 0,0000 | 14 | 13 / 14 | 10 / 14 | 1,277 / 1,474 (13) | PIERDE(noches) |
| Villarrica | sí | 20,2 % / 88,1 % (218) | 148 / 0 | 0,0000 | 11 | 10 / 11 | 10 / 11 | 0,876 / 0,877 (10) | PIERDE(noches) |
| NevadosDeChillan | no | 21,3 % / 88,3 % (197) | 132 / 0 | 0,0000 | 5 | 2 / 5 | 2 / 5 | 1,425 / 1,160 (2) | PIERDE(noches) |
| TODOS | sí | 34,5 % / 91,7 % (1170) | 669 / 0 | 0,0000 | 308 | 289 / 308 | 278 / 308 | 0,880 / 0,750 (450) | PIERDE(noches) |

Con muestra suficiente (7 volcanes): gana en 2 (Lascar, PuyehueCordonCaulle), empata en 0 (ninguno), pierde en 5 (Lastarria, PlanchonPeteroa, Tupungatito, Chaiten, Villarrica). Nulo: ganaría en 1 a lo más. Noches perdidas (b) en todos los volcanes, con o sin muestra: 30 (Chaiten 2026-08-10; Chaiten 2026-08-18; Chaiten 2026-08-22; Chaiten 2026-08-23; Isluga 2026-06-26; Isluga 2026-06-30; Isluga 2026-07-01; Isluga 2026-07-16; Isluga 2026-07-22; Isluga 2026-07-23; Isluga 2026-07-28; Isluga 2026-07-31 y más).

**_s142_ab_lit_sp_suelto**

| volcán | muestra suficiente | neg. limpios: brazo / control (n) | sólo control / sólo brazo | p | noches pos | publicadas (a) brazo / control | publicadas (b) brazo / control | razón de magnitud brazo / control (pares) | lectura |
|---|---|---|---|---|---|---|---|---|---|
| Isluga | no | 66,7 % / 90,5 % (21) | 6 / 1 | 0,1250 | 74 | 74 / 74 | 74 / 74 | 0,881 / 0,632 (131) | EMPATA |
| Lascar | sí | 48,0 % / 82,0 % (50) | 18 / 1 | 0,0001 | 61 | 61 / 61 | 61 / 61 | 0,740 / 0,629 (110) | GANA |
| Lastarria | sí | 51,9 % / 96,2 % (52) | 23 / 0 | 0,0000 | 50 | 50 / 50 | 50 / 50 | 0,974 / 0,965 (74) | GANA |
| PlanchonPeteroa | sí | 42,4 % / 95,1 % (144) | 76 / 0 | 0,0000 | 28 | 28 / 28 | 28 / 28 | 0,995 / 0,956 (44) | GANA |
| PuyehueCordonCaulle | sí | 86,3 % / 95,9 % (146) | 14 / 0 | 0,0001 | 37 | 37 / 37 | 37 / 37 | 1,022 / 1,021 (86) | GANA |
| Tupungatito | sí | 71,3 % / 94,3 % (122) | 29 / 1 | 0,0000 | 28 | 28 / 28 | 28 / 28 | 1,113 / 0,562 (51) | GANA |
| Chaiten | sí | 62,7 % / 93,2 % (220) | 67 / 0 | 0,0000 | 14 | 14 / 14 | 14 / 14 | 1,481 / 1,296 (17) | GANA |
| Villarrica | sí | 36,7 % / 88,1 % (218) | 112 / 0 | 0,0000 | 11 | 11 / 11 | 11 / 11 | 0,893 / 0,860 (11) | GANA |
| NevadosDeChillan | no | 42,1 % / 88,3 % (197) | 97 / 6 | 0,0000 | 5 | 5 / 5 | 5 / 5 | 1,321 / 1,208 (6) | GANA |
| TODOS | sí | 54,7 % / 91,7 % (1170) | 442 / 9 | 0,0000 | 308 | 308 / 308 | 308 / 308 | 0,945 / 0,773 (530) | GANA |

Con muestra suficiente (7 volcanes): gana en 7 (Lascar, Lastarria, PlanchonPeteroa, PuyehueCordonCaulle, Tupungatito, Chaiten, Villarrica), empata en 0 (ninguno), pierde en 0 (ninguno). Nulo: ganaría en 1 a lo más. Noches perdidas (b) en todos los volcanes, con o sin muestra: 0.

**_s142_ab_lit_keep_peak**

| volcán | muestra suficiente | neg. limpios: brazo / control (n) | sólo control / sólo brazo | p | noches pos | publicadas (a) brazo / control | publicadas (b) brazo / control | razón de magnitud brazo / control (pares) | lectura |
|---|---|---|---|---|---|---|---|---|---|
| Isluga | no | 95,2 % / 90,5 % (21) | 0 / 1 | 1,0000 | 74 | 74 / 74 | 74 / 74 | 0,868 / 0,632 (131) | EMPATA |
| Lascar | sí | 82,0 % / 82,0 % (50) | 1 / 1 | 1,0000 | 61 | 61 / 61 | 61 / 61 | 0,740 / 0,629 (110) | EMPATA |
| Lastarria | sí | 96,2 % / 96,2 % (52) | 0 / 0 | 1,0000 | 50 | 50 / 50 | 50 / 50 | 0,922 / 0,960 (76) | EMPATA |
| PlanchonPeteroa | sí | 94,4 % / 95,1 % (144) | 1 / 0 | 1,0000 | 28 | 28 / 28 | 28 / 28 | 0,936 / 0,956 (44) | EMPATA |
| PuyehueCordonCaulle | sí | 95,9 % / 95,9 % (146) | 0 / 0 | 1,0000 | 37 | 37 / 37 | 37 / 37 | 1,022 / 1,021 (86) | EMPATA |
| Tupungatito | sí | 94,3 % / 94,3 % (122) | 1 / 1 | 1,0000 | 28 | 28 / 28 | 28 / 28 | 1,108 / 0,562 (51) | EMPATA |
| Chaiten | sí | 92,7 % / 93,2 % (220) | 1 / 0 | 1,0000 | 14 | 14 / 14 | 14 / 14 | 1,277 / 1,296 (17) | EMPATA |
| Villarrica | sí | 87,6 % / 88,1 % (218) | 1 / 0 | 1,0000 | 11 | 11 / 11 | 11 / 11 | 0,893 / 0,860 (11) | EMPATA |
| NevadosDeChillan | no | 90,9 % / 88,3 % (197) | 1 / 6 | 0,1250 | 5 | 5 / 5 | 5 / 5 | 1,321 / 1,208 (6) | EMPATA |
| TODOS | sí | 92,0 % / 91,7 % (1170) | 6 / 9 | 0,6072 | 308 | 308 / 308 | 308 / 308 | 0,914 / 0,770 (532) | EMPATA |

Con muestra suficiente (7 volcanes): gana en 0 (ninguno), empata en 7 (Lascar, Lastarria, PlanchonPeteroa, PuyehueCordonCaulle, Tupungatito, Chaiten, Villarrica), pierde en 0 (ninguno). Nulo: ganaría en 0 a lo más. Noches perdidas (b) en todos los volcanes, con o sin muestra: 0.

### S135: tabla por brazo y volcán

**_s135_ab_b_nokeeppeak**

| volcán | muestra suficiente | neg. limpios: brazo / control (n) | sólo control / sólo brazo | p | noches pos | publicadas (a) brazo / control | publicadas (b) brazo / control | razón de magnitud brazo / control (pares) | lectura |
|---|---|---|---|---|---|---|---|---|---|
| Isluga | no | 42,9 % / 90,5 % (21) | 10 / 0 | 0,0020 | 74 | 74 / 74 | 72 / 74 | 0,582 / 0,632 (125) | PIERDE(noches) |
| Lascar | sí | 30,0 % / 82,0 % (50) | 26 / 0 | 0,0000 | 61 | 61 / 61 | 61 / 61 | 0,626 / 0,631 (109) | GANA |
| Lastarria | sí | 51,9 % / 96,2 % (52) | 23 / 0 | 0,0000 | 50 | 50 / 50 | 50 / 50 | 1,012 / 0,965 (74) | GANA |
| PuyehueCordonCaulle | sí | 86,3 % / 95,9 % (146) | 14 / 0 | 0,0001 | 37 | 37 / 37 | 37 / 37 | 1,021 / 1,021 (86) | GANA |
| PlanchonPeteroa | sí | 42,4 % / 95,1 % (144) | 76 / 0 | 0,0000 | 28 | 28 / 28 | 28 / 28 | 0,997 / 0,956 (44) | GANA |
| Tupungatito | sí | 59,8 % / 94,3 % (122) | 42 / 0 | 0,0000 | 28 | 28 / 28 | 28 / 28 | 0,494 / 0,556 (50) | GANA |
| TODOS | sí | 58,1 % / 93,8 % (535) | 191 / 0 | 0,0000 | 278 | 278 / 278 | 276 / 278 | 0,723 / 0,749 (488) | PIERDE(noches) |

Con muestra suficiente (5 volcanes): gana en 5 (Lascar, Lastarria, PuyehueCordonCaulle, PlanchonPeteroa, Tupungatito), empata en 0 (ninguno), pierde en 0 (ninguno). Nulo: ganaría en 1 a lo más. Noches perdidas (b) en todos los volcanes, con o sin muestra: 2 (Isluga 2026-06-30; Isluga 2026-07-28).

**_s135_ab_c_cond**

| volcán | muestra suficiente | neg. limpios: brazo / control (n) | sólo control / sólo brazo | p | noches pos | publicadas (a) brazo / control | publicadas (b) brazo / control | razón de magnitud brazo / control (pares) | lectura |
|---|---|---|---|---|---|---|---|---|---|
| Isluga | no | 90,5 % / 90,5 % (21) | 0 / 0 | 1,0000 | 74 | 74 / 74 | 74 / 74 | 0,644 / 0,634 (130) | EMPATA |
| Lascar | sí | 82,0 % / 82,0 % (50) | 0 / 0 | 1,0000 | 61 | 61 / 61 | 61 / 61 | 0,629 / 0,629 (110) | EMPATA |
| Lastarria | sí | 96,2 % / 96,2 % (52) | 0 / 0 | 1,0000 | 50 | 50 / 50 | 50 / 50 | 0,924 / 0,960 (76) | EMPATA |
| PuyehueCordonCaulle | sí | 95,2 % / 95,9 % (146) | 1 / 0 | 1,0000 | 37 | 37 / 37 | 37 / 37 | 0,980 / 1,021 (86) | EMPATA |
| PlanchonPeteroa | sí | 93,1 % / 95,1 % (144) | 3 / 0 | 0,2500 | 28 | 28 / 28 | 28 / 28 | 0,927 / 0,956 (44) | EMPATA |
| Tupungatito | sí | 91,0 % / 94,3 % (122) | 4 / 0 | 0,1250 | 28 | 28 / 28 | 28 / 28 | 0,576 / 0,562 (51) | EMPATA |
| TODOS | sí | 92,3 % / 93,8 % (535) | 8 / 0 | 0,0078 | 278 | 278 / 278 | 278 / 278 | 0,748 / 0,749 (497) | GANA |

Con muestra suficiente (5 volcanes): gana en 0 (ninguno), empata en 5 (Lascar, Lastarria, PuyehueCordonCaulle, PlanchonPeteroa, Tupungatito), pierde en 0 (ninguno). Nulo: ganaría en 0 a lo más. Noches perdidas (b) en todos los volcanes, con o sin muestra: 0.

**_s135_ab_d_ambos**

| volcán | muestra suficiente | neg. limpios: brazo / control (n) | sólo control / sólo brazo | p | noches pos | publicadas (a) brazo / control | publicadas (b) brazo / control | razón de magnitud brazo / control (pares) | lectura |
|---|---|---|---|---|---|---|---|---|---|
| Isluga | no | 28,6 % / 90,5 % (21) | 13 / 0 | 0,0002 | 74 | 69 / 74 | 64 / 74 | 0,614 / 0,614 (106) | PIERDE(noches) |
| Lascar | sí | 14,0 % / 82,0 % (50) | 34 / 0 | 0,0000 | 61 | 61 / 61 | 61 / 61 | 0,629 / 0,629 (104) | GANA |
| Lastarria | sí | 26,9 % / 96,2 % (52) | 36 / 0 | 0,0000 | 50 | 48 / 50 | 46 / 50 | 0,957 / 1,008 (65) | PIERDE(noches) |
| PuyehueCordonCaulle | sí | 78,8 % / 95,9 % (146) | 25 / 0 | 0,0000 | 37 | 37 / 37 | 37 / 37 | 0,993 / 1,021 (80) | GANA |
| PlanchonPeteroa | sí | 25,0 % / 95,1 % (144) | 101 / 0 | 0,0000 | 28 | 23 / 28 | 23 / 28 | 0,905 / 0,905 (31) | PIERDE(noches) |
| Tupungatito | sí | 42,6 % / 94,3 % (122) | 63 / 0 | 0,0000 | 28 | 26 / 28 | 25 / 28 | 0,539 / 0,539 (39) | PIERDE(noches) |
| TODOS | sí | 43,0 % / 93,8 % (535) | 272 / 0 | 0,0000 | 278 | 264 / 278 | 256 / 278 | 0,720 / 0,730 (425) | PIERDE(noches) |

Con muestra suficiente (5 volcanes): gana en 2 (Lascar, PuyehueCordonCaulle), empata en 0 (ninguno), pierde en 3 (Lastarria, PlanchonPeteroa, Tupungatito). Nulo: ganaría en 1 a lo más. Noches perdidas (b) en todos los volcanes, con o sin muestra: 22 (Isluga 2026-06-26; Isluga 2026-06-30; Isluga 2026-07-01; Isluga 2026-07-16; Isluga 2026-07-22; Isluga 2026-07-23; Isluga 2026-07-28; Isluga 2026-07-31; Isluga 2026-08-19; Isluga 2026-08-31; Lastarria 2026-06-02; Lastarria 2026-07-02 y más).

**_s135_ab_e_sp_off**

| volcán | muestra suficiente | neg. limpios: brazo / control (n) | sólo control / sólo brazo | p | noches pos | publicadas (a) brazo / control | publicadas (b) brazo / control | razón de magnitud brazo / control (pares) | lectura |
|---|---|---|---|---|---|---|---|---|---|
| Isluga | no | 90,5 % / 90,5 % (21) | 0 / 0 | 1,0000 | 74 | 74 / 74 | 74 / 74 | 0,632 / 0,634 (130) | EMPATA |
| Lascar | sí | 82,0 % / 82,0 % (50) | 0 / 0 | 1,0000 | 61 | 61 / 61 | 61 / 61 | 0,614 / 0,629 (110) | EMPATA |
| Lastarria | sí | 96,2 % / 96,2 % (52) | 0 / 0 | 1,0000 | 50 | 50 / 50 | 50 / 50 | 0,874 / 0,960 (76) | EMPATA |
| PuyehueCordonCaulle | sí | 95,2 % / 95,9 % (146) | 1 / 0 | 1,0000 | 37 | 37 / 37 | 37 / 37 | 0,740 / 1,021 (86) | EMPATA |
| PlanchonPeteroa | sí | 93,1 % / 95,1 % (144) | 3 / 0 | 0,2500 | 28 | 28 / 28 | 28 / 28 | 0,886 / 0,956 (44) | EMPATA |
| Tupungatito | sí | 91,0 % / 94,3 % (122) | 4 / 0 | 0,1250 | 28 | 28 / 28 | 28 / 28 | 0,551 / 0,562 (51) | EMPATA |
| TODOS | sí | 92,3 % / 93,8 % (535) | 8 / 0 | 0,0078 | 278 | 278 / 278 | 278 / 278 | 0,696 / 0,749 (497) | GANA |

Con muestra suficiente (5 volcanes): gana en 0 (ninguno), empata en 5 (Lascar, Lastarria, PuyehueCordonCaulle, PlanchonPeteroa, Tupungatito), pierde en 0 (ninguno). Nulo: ganaría en 0 a lo más. Noches perdidas (b) en todos los volcanes, con o sin muestra: 0.

Salida cruda completa de las dos tablas:

```
===== S143 cobertura despareja: {}
   processed_utc: {'_s142_ab_control': ('2026-09-17T19:47:28Z', '2026-09-19T01:51:09Z'), '_s142_ab_literal': ('2026-09-17T19:47:20Z', '2026-09-19T16:10:29Z'), '_s142_ab_lit_sin_fondo': ('2026-09-17T19:46:59Z', '2026-09-19T02:08:35Z'), '_s142_ab_lit_con_compuerta': ('2026-09-17T19:47:01Z', '2026-09-19T02:07:36Z'), '_s142_ab_lit_s
-- _s142_ab_control
   Isluga               neg   19/21   tasa 0.9048 (ctl 0.9048) -0 +0 p=1.0 | noches pos  74 pubA 74/74 pubB 74/74 perdA 0 perdB 0 ganB 0 | mag n=131 0.6316 (ctl 0.6316) | suf=False -> CONTROL
   Lascar               neg   41/50   tasa 0.82 (ctl 0.82) -0 +0 p=1.0 | noches pos  61 pubA 61/61 pubB 61/61 perdA 0 perdB 0 ganB 0 | mag n=110 0.6287 (ctl 0.6287) | suf=True -> CONTROL
   Lastarria            neg   50/52   tasa 0.9615 (ctl 0.9615) -0 +0 p=1.0 | noches pos  50 pubA 50/50 pubB 50/50 perdA 0 perdB 0 ganB 0 | mag n=76 0.9598 (ctl 0.9598) | suf=True -> CONTROL
   PlanchonPeteroa      neg  137/144  tasa 0.9514 (ctl 0.9514) -0 +0 p=1.0 | noches pos  28 pubA 28/28 pubB 28/28 perdA 0 perdB 0 ganB 0 | mag n=44 0.9558 (ctl 0.9558) | suf=True -> CONTROL
   PuyehueCordonCaulle  neg  140/146  tasa 0.9589 (ctl 0.9589) -0 +0 p=1.0 | noches pos  37 pubA 37/37 pubB 37/37 perdA 0 perdB 0 ganB 0 | mag n=86 1.021 (ctl 1.021) | suf=True -> CONTROL
   Tupungatito          neg  115/122  tasa 0.9426 (ctl 0.9426) -0 +0 p=1.0 | noches pos  28 pubA 28/28 pubB 28/28 perdA 0 perdB 0 ganB 0 | mag n=51 0.562 (ctl 0.562) | suf=True -> CONTROL
   Chaiten              neg  205/220  tasa 0.9318 (ctl 0.9318) -0 +0 p=1.0 | noches pos  14 pubA 14/14 pubB 14/14 perdA 0 perdB 0 ganB 0 | mag n=17 1.296 (ctl 1.296) | suf=True -> CONTROL
   Villarrica           neg  192/218  tasa 0.8807 (ctl 0.8807) -0 +0 p=1.0 | noches pos  11 pubA 11/11 pubB 11/11 perdA 0 perdB 0 ganB 0 | mag n=11 0.86 (ctl 0.86) | suf=True -> CONTROL
   NevadosDeChillan     neg  174/197  tasa 0.8832 (ctl 0.8832) -0 +0 p=1.0 | noches pos   5 pubA 5/5 pubB 5/5 perdA 0 perdB 0 ganB 0 | mag n=6 1.2083 (ctl 1.2083) | suf=False -> CONTROL
   TODOS                neg 1073/1170 tasa 0.9171 (ctl 0.9171) -0 +0 p=1.0 | noches pos 308 pubA 308/308 pubB 308/308 perdA 0 perdB 0 ganB 0 | mag n=532 0.7701 (ctl 0.7701) | suf=True -> CONTROL
-- _s142_ab_literal
   Isluga               neg   14/21   tasa 0.6667 (ctl 0.9048) -6 +1 p=0.125 | noches pos  74 pubA 74/74 pubB 74/74 perdA 0 perdB 0 ganB 0 | mag n=131 0.8808 (ctl 0.6316) | suf=False -> EMPATA
   Lascar               neg   24/50   tasa 0.48 (ctl 0.82) -18 +1 p=7.6e-05 | noches pos  61 pubA 61/61 pubB 61/61 perdA 0 perdB 0 ganB 0 | mag n=110 0.7401 (ctl 0.6287) | suf=True -> GANA
   Lastarria            neg   27/52   tasa 0.5192 (ctl 0.9615) -23 +0 p=0.0 | noches pos  50 pubA 50/50 pubB 50/50 perdA 0 perdB 0 ganB 0 | mag n=74 0.9743 (ctl 0.9646) | suf=True -> GANA
   PlanchonPeteroa      neg   61/144  tasa 0.4236 (ctl 0.9514) -76 +0 p=0.0 | noches pos  28 pubA 28/28 pubB 28/28 perdA 0 perdB 0 ganB 0 | mag n=44 0.9953 (ctl 0.9558) | suf=True -> GANA
   PuyehueCordonCaulle  neg  126/146  tasa 0.863 (ctl 0.9589) -14 +0 p=0.000122 | noches pos  37 pubA 37/37 pubB 37/37 perdA 0 perdB 0 ganB 0 | mag n=86 1.0221 (ctl 1.021) | suf=True -> GANA
   Tupungatito          neg   87/122  tasa 0.7131 (ctl 0.9426) -29 +1 p=0.0 | noches pos  28 pubA 28/28 pubB 28/28 perdA 0 perdB 0 ganB 0 | mag n=51 1.1125 (ctl 0.562) | suf=True -> GANA
   Chaiten              neg  138/220  tasa 0.6273 (ctl 0.9318) -67 +0 p=0.0 | noches pos  14 pubA 14/14 pubB 14/14 perdA 0 perdB 0 ganB 0 | mag n=17 1.4809 (ctl 1.296) | suf=True -> GANA
   Villarrica           neg   80/218  tasa 0.367 (ctl 0.8807) -112 +0 p=0.0 | noches pos  11 pubA 11/11 pubB 11/11 perdA 0 perdB 0 ganB 0 | mag n=11 0.8931 (ctl 0.86) | suf=True -> GANA
   NevadosDeChillan     neg   83/197  tasa 0.4213 (ctl 0.8832) -97 +6 p=0.0 | noches pos   5 pubA 5/5 pubB 5/5 perdA 0 perdB 0 ganB 0 | mag n=6 1.3208 (ctl 1.2083) | suf=False -> GANA
   TODOS                neg  640/1170 tasa 0.547 (ctl 0.9171) -442 +9 p=0.0 | noches pos 308 pubA 308/308 pubB 308/308 perdA 0 perdB 0 ganB 0 | mag n=530 0.9449 (ctl 0.773) | suf=True -> GANA
-- _s142_ab_lit_sin_fondo
   Isluga               neg    9/21   tasa 0.4286 (ctl 0.9048) -10 +0 p=0.001953 | noches pos  74 pubA 74/74 pubB 72/74 perdA 0 perdB 2 ganB 0 | mag n=125 0.5824 (ctl 0.6316) | suf=False -> PIERDE(noches)
   Lascar               neg   15/50   tasa 0.3 (ctl 0.82) -26 +0 p=0.0 | noches pos  61 pubA 61/61 pubB 61/61 perdA 0 perdB 0 ganB 0 | mag n=109 0.6259 (ctl 0.6314) | suf=True -> GANA
   Lastarria            neg   27/52   tasa 0.5192 (ctl 0.9615) -23 +0 p=0.0 | noches pos  50 pubA 50/50 pubB 50/50 perdA 0 perdB 0 ganB 0 | mag n=74 1.0117 (ctl 0.9646) | suf=True -> GANA
   PlanchonPeteroa      neg   61/144  tasa 0.4236 (ctl 0.9514) -76 +0 p=0.0 | noches pos  28 pubA 28/28 pubB 28/28 perdA 0 perdB 0 ganB 0 | mag n=44 0.9969 (ctl 0.9558) | suf=True -> GANA
   PuyehueCordonCaulle  neg  126/146  tasa 0.863 (ctl 0.9589) -14 +0 p=0.000122 | noches pos  37 pubA 37/37 pubB 37/37 perdA 0 perdB 0 ganB 0 | mag n=86 1.0285 (ctl 1.021) | suf=True -> GANA
   Tupungatito          neg   74/122  tasa 0.6066 (ctl 0.9426) -41 +0 p=0.0 | noches pos  28 pubA 28/28 pubB 28/28 perdA 0 perdB 0 ganB 0 | mag n=50 0.4944 (ctl 0.5564) | suf=True -> GANA
   Chaiten              neg  138/220  tasa 0.6273 (ctl 0.9318) -67 +0 p=0.0 | noches pos  14 pubA 14/14 pubB 14/14 perdA 0 perdB 0 ganB 0 | mag n=17 1.4927 (ctl 1.296) | suf=True -> GANA
   Villarrica           neg   80/218  tasa 0.367 (ctl 0.8807) -112 +0 p=0.0 | noches pos  11 pubA 11/11 pubB 11/11 perdA 0 perdB 0 ganB 0 | mag n=11 0.8933 (ctl 0.86) | suf=True -> GANA
   NevadosDeChillan     neg   49/197  tasa 0.2487 (ctl 0.8832) -125 +0 p=0.0 | noches pos   5 pubA 2/5 pubB 2/5 perdA 3 perdB 3 ganB 0 | mag n=2 1.16 (ctl 1.16) | suf=False -> PIERDE(noches)
   TODOS                neg  579/1170 tasa 0.4949 (ctl 0.9171) -494 +0 p=0.0 | noches pos 308 pubA 305/308 pubB 303/308 perdA 3 perdB 5 ganB 0 | mag n=518 0.748 (ctl 0.768) | suf=True -> PIERDE(noches)
-- _s142_ab_lit_con_compuerta
   Isluga               neg    6/21   tasa 0.2857 (ctl 0.9048) -13 +0 p=0.000244 | noches pos  74 pubA 69/74 pubB 64/74 perdA 5 perdB 10 ganB 0 | mag n=106 0.8585 (ctl 0.6137) | suf=False -> PIERDE(noches)
   Lascar               neg    7/50   tasa 0.14 (ctl 0.82) -34 +0 p=0.0 | noches pos  61 pubA 61/61 pubB 61/61 perdA 0 perdB 0 ganB 0 | mag n=104 0.7401 (ctl 0.6287) | suf=True -> GANA
   Lastarria            neg   14/52   tasa 0.2692 (ctl 0.9615) -36 +0 p=0.0 | noches pos  50 pubA 48/50 pubB 46/50 perdA 2 perdB 4 ganB 0 | mag n=65 0.91 (ctl 1.0082) | suf=True -> PIERDE(noches)
   PlanchonPeteroa      neg   36/144  tasa 0.25 (ctl 0.9514) -101 +0 p=0.0 | noches pos  28 pubA 23/28 pubB 23/28 perdA 5 perdB 5 ganB 0 | mag n=31 0.9042 (ctl 0.905) | suf=True -> PIERDE(noches)
   PuyehueCordonCaulle  neg  115/146  tasa 0.7877 (ctl 0.9589) -25 +0 p=0.0 | noches pos  37 pubA 37/37 pubB 37/37 perdA 0 perdB 0 ganB 0 | mag n=80 0.9846 (ctl 1.021) | suf=True -> GANA
   Tupungatito          neg   52/122  tasa 0.4262 (ctl 0.9426) -63 +0 p=0.0 | noches pos  28 pubA 26/28 pubB 25/28 perdA 2 perdB 3 ganB 0 | mag n=39 1.0755 (ctl 0.5391) | suf=True -> PIERDE(noches)
   Chaiten              neg   88/220  tasa 0.4 (ctl 0.9318) -117 +0 p=0.0 | noches pos  14 pubA 13/14 pubB 10/14 perdA 1 perdB 4 ganB 0 | mag n=13 1.2773 (ctl 1.4738) | suf=True -> PIERDE(noches)
   Villarrica           neg   44/218  tasa 0.2018 (ctl 0.8807) -148 +0 p=0.0 | noches pos  11 pubA 10/11 pubB 10/11 perdA 1 perdB 1 ganB 0 | mag n=10 0.8765 (ctl 0.8767) | suf=True -> PIERDE(noches)
   NevadosDeChillan     neg   42/197  tasa 0.2132 (ctl 0.8832) -132 +0 p=0.0 | noches pos   5 pubA 2/5 pubB 2/5 perdA 3 perdB 3 ganB 0 | mag n=2 1.425 (ctl 1.16) | suf=False -> PIERDE(noches)
   TODOS                neg  404/1170 tasa 0.3453 (ctl 0.9171) -669 +0 p=0.0 | noches pos 308 pubA 289/308 pubB 278/308 perdA 19 perdB 30 ganB 0 | mag n=450 0.8801 (ctl 0.7504) | suf=True -> PIERDE(noches)
-- _s142_ab_lit_sp_suelto
   Isluga               neg   14/21   tasa 0.6667 (ctl 0.9048) -6 +1 p=0.125 | noches pos  74 pubA 74/74 pubB 74/74 perdA 0 perdB 0 ganB 0 | mag n=131 0.8808 (ctl 0.6316) | suf=False -> EMPATA
   Lascar               neg   24/50   tasa 0.48 (ctl 0.82) -18 +1 p=7.6e-05 | noches pos  61 pubA 61/61 pubB 61/61 perdA 0 perdB 0 ganB 0 | mag n=110 0.7401 (ctl 0.6287) | suf=True -> GANA
   Lastarria            neg   27/52   tasa 0.5192 (ctl 0.9615) -23 +0 p=0.0 | noches pos  50 pubA 50/50 pubB 50/50 perdA 0 perdB 0 ganB 0 | mag n=74 0.9743 (ctl 0.9646) | suf=True -> GANA
   PlanchonPeteroa      neg   61/144  tasa 0.4236 (ctl 0.9514) -76 +0 p=0.0 | noches pos  28 pubA 28/28 pubB 28/28 perdA 0 perdB 0 ganB 0 | mag n=44 0.9953 (ctl 0.9558) | suf=True -> GANA
   PuyehueCordonCaulle  neg  126/146  tasa 0.863 (ctl 0.9589) -14 +0 p=0.000122 | noches pos  37 pubA 37/37 pubB 37/37 perdA 0 perdB 0 ganB 0 | mag n=86 1.0221 (ctl 1.021) | suf=True -> GANA
   Tupungatito          neg   87/122  tasa 0.7131 (ctl 0.9426) -29 +1 p=0.0 | noches pos  28 pubA 28/28 pubB 28/28 perdA 0 perdB 0 ganB 0 | mag n=51 1.1125 (ctl 0.562) | suf=True -> GANA
   Chaiten              neg  138/220  tasa 0.6273 (ctl 0.9318) -67 +0 p=0.0 | noches pos  14 pubA 14/14 pubB 14/14 perdA 0 perdB 0 ganB 0 | mag n=17 1.4809 (ctl 1.296) | suf=True -> GANA
   Villarrica           neg   80/218  tasa 0.367 (ctl 0.8807) -112 +0 p=0.0 | noches pos  11 pubA 11/11 pubB 11/11 perdA 0 perdB 0 ganB 0 | mag n=11 0.8931 (ctl 0.86) | suf=True -> GANA
   NevadosDeChillan     neg   83/197  tasa 0.4213 (ctl 0.8832) -97 +6 p=0.0 | noches pos   5 pubA 5/5 pubB 5/5 perdA 0 perdB 0 ganB 0 | mag n=6 1.3208 (ctl 1.2083) | suf=False -> GANA
   TODOS                neg  640/1170 tasa 0.547 (ctl 0.9171) -442 +9 p=0.0 | noches pos 308 pubA 308/308 pubB 308/308 perdA 0 perdB 0 ganB 0 | mag n=530 0.9449 (ctl 0.773) | suf=True -> GANA
-- _s142_ab_lit_keep_peak
   Isluga               neg   20/21   tasa 0.9524 (ctl 0.9048) -0 +1 p=1.0 | noches pos  74 pubA 74/74 pubB 74/74 perdA 0 perdB 0 ganB 0 | mag n=131 0.8682 (ctl 0.6316) | suf=False -> EMPATA
   Lascar               neg   41/50   tasa 0.82 (ctl 0.82) -1 +1 p=1.0 | noches pos  61 pubA 61/61 pubB 61/61 perdA 0 perdB 0 ganB 0 | mag n=110 0.7401 (ctl 0.6287) | suf=True -> EMPATA
   Lastarria            neg   50/52   tasa 0.9615 (ctl 0.9615) -0 +0 p=1.0 | noches pos  50 pubA 50/50 pubB 50/50 perdA 0 perdB 0 ganB 0 | mag n=76 0.922 (ctl 0.9598) | suf=True -> EMPATA
   PlanchonPeteroa      neg  136/144  tasa 0.9444 (ctl 0.9514) -1 +0 p=1.0 | noches pos  28 pubA 28/28 pubB 28/28 perdA 0 perdB 0 ganB 0 | mag n=44 0.9361 (ctl 0.9558) | suf=True -> EMPATA
   PuyehueCordonCaulle  neg  140/146  tasa 0.9589 (ctl 0.9589) -0 +0 p=1.0 | noches pos  37 pubA 37/37 pubB 37/37 perdA 0 perdB 0 ganB 0 | mag n=86 1.0221 (ctl 1.021) | suf=True -> EMPATA
   Tupungatito          neg  115/122  tasa 0.9426 (ctl 0.9426) -1 +1 p=1.0 | noches pos  28 pubA 28/28 pubB 28/28 perdA 0 perdB 0 ganB 0 | mag n=51 1.1079 (ctl 0.562) | suf=True -> EMPATA
   Chaiten              neg  204/220  tasa 0.9273 (ctl 0.9318) -1 +0 p=1.0 | noches pos  14 pubA 14/14 pubB 14/14 perdA 0 perdB 0 ganB 0 | mag n=17 1.2773 (ctl 1.296) | suf=True -> EMPATA
   Villarrica           neg  191/218  tasa 0.8761 (ctl 0.8807) -1 +0 p=1.0 | noches pos  11 pubA 11/11 pubB 11/11 perdA 0 perdB 0 ganB 0 | mag n=11 0.8931 (ctl 0.86) | suf=True -> EMPATA
   NevadosDeChillan     neg  179/197  tasa 0.9086 (ctl 0.8832) -1 +6 p=0.125 | noches pos   5 pubA 5/5 pubB 5/5 perdA 0 perdB 0 ganB 0 | mag n=6 1.3208 (ctl 1.2083) | suf=False -> EMPATA
   TODOS                neg 1076/1170 tasa 0.9197 (ctl 0.9171) -6 +9 p=0.607239 | noches pos 308 pubA 308/308 pubB 308/308 perdA 0 perdB 0 ganB 0 | mag n=532 0.9141 (ctl 0.7701) | suf=True -> EMPATA
   NULO: {"_s142_ab_literal": {"n_vol_suficientes": 7, "gana_bajo_nulo_media": 0.127, "gana_bajo_nulo_p97.5": 1}, "_s142_ab_lit_sin_fondo": {"n_vol_suficientes": 7, "gana_bajo_nulo_media": 0.109, "gana_bajo_nulo_p97.5": 1}, "_s142_ab_lit_con_compuerta": {"n_vol_suficientes": 7, "gana_bajo_nulo_media": 0.137, "gana_bajo_nulo_p97.
===== S135 cobertura despareja: {}
   processed_utc: {'_s135_ab_a_control': ('2026-09-08T00:35:27Z', '2026-09-08T17:32:26Z'), '_s135_ab_b_nokeeppeak': ('2026-09-08T00:35:27Z', '2026-09-08T18:02:46Z'), '_s135_ab_c_cond': ('2026-09-08T00:35:21Z', '2026-09-08T18:27:41Z'), '_s135_ab_d_ambos': ('2026-09-08T00:35:26Z', '2026-09-08T18:21:13Z'), '_s135_ab_e_sp_off': ('20
-- _s135_ab_a_control
   Isluga               neg   19/21   tasa 0.9048 (ctl 0.9048) -0 +0 p=1.0 | noches pos  74 pubA 74/74 pubB 74/74 perdA 0 perdB 0 ganB 0 | mag n=131 0.6316 (ctl 0.6316) | suf=False -> CONTROL
   Lascar               neg   41/50   tasa 0.82 (ctl 0.82) -0 +0 p=1.0 | noches pos  61 pubA 61/61 pubB 61/61 perdA 0 perdB 0 ganB 0 | mag n=110 0.6287 (ctl 0.6287) | suf=True -> CONTROL
   Lastarria            neg   50/52   tasa 0.9615 (ctl 0.9615) -0 +0 p=1.0 | noches pos  50 pubA 50/50 pubB 50/50 perdA 0 perdB 0 ganB 0 | mag n=76 0.9598 (ctl 0.9598) | suf=True -> CONTROL
   PuyehueCordonCaulle  neg  140/146  tasa 0.9589 (ctl 0.9589) -0 +0 p=1.0 | noches pos  37 pubA 37/37 pubB 37/37 perdA 0 perdB 0 ganB 0 | mag n=86 1.021 (ctl 1.021) | suf=True -> CONTROL
   PlanchonPeteroa      neg  137/144  tasa 0.9514 (ctl 0.9514) -0 +0 p=1.0 | noches pos  28 pubA 28/28 pubB 28/28 perdA 0 perdB 0 ganB 0 | mag n=44 0.9558 (ctl 0.9558) | suf=True -> CONTROL
   Tupungatito          neg  115/122  tasa 0.9426 (ctl 0.9426) -0 +0 p=1.0 | noches pos  28 pubA 28/28 pubB 28/28 perdA 0 perdB 0 ganB 0 | mag n=51 0.562 (ctl 0.562) | suf=True -> CONTROL
   TODOS                neg  502/535  tasa 0.9383 (ctl 0.9383) -0 +0 p=1.0 | noches pos 278 pubA 278/278 pubB 278/278 perdA 0 perdB 0 ganB 0 | mag n=498 0.748 (ctl 0.748) | suf=True -> CONTROL
-- _s135_ab_b_nokeeppeak
   Isluga               neg    9/21   tasa 0.4286 (ctl 0.9048) -10 +0 p=0.001953 | noches pos  74 pubA 74/74 pubB 72/74 perdA 0 perdB 2 ganB 0 | mag n=125 0.5824 (ctl 0.6316) | suf=False -> PIERDE(noches)
   Lascar               neg   15/50   tasa 0.3 (ctl 0.82) -26 +0 p=0.0 | noches pos  61 pubA 61/61 pubB 61/61 perdA 0 perdB 0 ganB 0 | mag n=109 0.6259 (ctl 0.6314) | suf=True -> GANA
   Lastarria            neg   27/52   tasa 0.5192 (ctl 0.9615) -23 +0 p=0.0 | noches pos  50 pubA 50/50 pubB 50/50 perdA 0 perdB 0 ganB 0 | mag n=74 1.0117 (ctl 0.9646) | suf=True -> GANA
   PuyehueCordonCaulle  neg  126/146  tasa 0.863 (ctl 0.9589) -14 +0 p=0.000122 | noches pos  37 pubA 37/37 pubB 37/37 perdA 0 perdB 0 ganB 0 | mag n=86 1.021 (ctl 1.021) | suf=True -> GANA
   PlanchonPeteroa      neg   61/144  tasa 0.4236 (ctl 0.9514) -76 +0 p=0.0 | noches pos  28 pubA 28/28 pubB 28/28 perdA 0 perdB 0 ganB 0 | mag n=44 0.9969 (ctl 0.9558) | suf=True -> GANA
   Tupungatito          neg   73/122  tasa 0.5984 (ctl 0.9426) -42 +0 p=0.0 | noches pos  28 pubA 28/28 pubB 28/28 perdA 0 perdB 0 ganB 0 | mag n=50 0.4944 (ctl 0.5564) | suf=True -> GANA
   TODOS                neg  311/535  tasa 0.5813 (ctl 0.9383) -191 +0 p=0.0 | noches pos 278 pubA 278/278 pubB 276/278 perdA 0 perdB 2 ganB 0 | mag n=488 0.7231 (ctl 0.7492) | suf=True -> PIERDE(noches)
-- _s135_ab_c_cond
   Isluga               neg   19/21   tasa 0.9048 (ctl 0.9048) -0 +0 p=1.0 | noches pos  74 pubA 74/74 pubB 74/74 perdA 0 perdB 0 ganB 0 | mag n=130 0.6437 (ctl 0.634) | suf=False -> EMPATA
   Lascar               neg   41/50   tasa 0.82 (ctl 0.82) -0 +0 p=1.0 | noches pos  61 pubA 61/61 pubB 61/61 perdA 0 perdB 0 ganB 0 | mag n=110 0.6287 (ctl 0.6287) | suf=True -> EMPATA
   Lastarria            neg   50/52   tasa 0.9615 (ctl 0.9615) -0 +0 p=1.0 | noches pos  50 pubA 50/50 pubB 50/50 perdA 0 perdB 0 ganB 0 | mag n=76 0.924 (ctl 0.9598) | suf=True -> EMPATA
   PuyehueCordonCaulle  neg  139/146  tasa 0.9521 (ctl 0.9589) -1 +0 p=1.0 | noches pos  37 pubA 37/37 pubB 37/37 perdA 0 perdB 0 ganB 0 | mag n=86 0.9803 (ctl 1.021) | suf=True -> EMPATA
   PlanchonPeteroa      neg  134/144  tasa 0.9306 (ctl 0.9514) -3 +0 p=0.25 | noches pos  28 pubA 28/28 pubB 28/28 perdA 0 perdB 0 ganB 0 | mag n=44 0.9274 (ctl 0.9558) | suf=True -> EMPATA
   Tupungatito          neg  111/122  tasa 0.9098 (ctl 0.9426) -4 +0 p=0.125 | noches pos  28 pubA 28/28 pubB 28/28 perdA 0 perdB 0 ganB 0 | mag n=51 0.5763 (ctl 0.562) | suf=True -> EMPATA
   TODOS                neg  494/535  tasa 0.9234 (ctl 0.9383) -8 +0 p=0.007812 | noches pos 278 pubA 278/278 pubB 278/278 perdA 0 perdB 0 ganB 0 | mag n=497 0.7476 (ctl 0.7485) | suf=True -> GANA
-- _s135_ab_d_ambos
   Isluga               neg    6/21   tasa 0.2857 (ctl 0.9048) -13 +0 p=0.000244 | noches pos  74 pubA 69/74 pubB 64/74 perdA 5 perdB 10 ganB 0 | mag n=106 0.6137 (ctl 0.6137) | suf=False -> PIERDE(noches)
   Lascar               neg    7/50   tasa 0.14 (ctl 0.82) -34 +0 p=0.0 | noches pos  61 pubA 61/61 pubB 61/61 perdA 0 perdB 0 ganB 0 | mag n=104 0.6287 (ctl 0.6287) | suf=True -> GANA
   Lastarria            neg   14/52   tasa 0.2692 (ctl 0.9615) -36 +0 p=0.0 | noches pos  50 pubA 48/50 pubB 46/50 perdA 2 perdB 4 ganB 0 | mag n=65 0.9567 (ctl 1.0082) | suf=True -> PIERDE(noches)
   PuyehueCordonCaulle  neg  115/146  tasa 0.7877 (ctl 0.9589) -25 +0 p=0.0 | noches pos  37 pubA 37/37 pubB 37/37 perdA 0 perdB 0 ganB 0 | mag n=80 0.9934 (ctl 1.021) | suf=True -> GANA
   PlanchonPeteroa      neg   36/144  tasa 0.25 (ctl 0.9514) -101 +0 p=0.0 | noches pos  28 pubA 23/28 pubB 23/28 perdA 5 perdB 5 ganB 0 | mag n=31 0.905 (ctl 0.905) | suf=True -> PIERDE(noches)
   Tupungatito          neg   52/122  tasa 0.4262 (ctl 0.9426) -63 +0 p=0.0 | noches pos  28 pubA 26/28 pubB 25/28 perdA 2 perdB 3 ganB 0 | mag n=39 0.5391 (ctl 0.5391) | suf=True -> PIERDE(noches)
   TODOS                neg  230/535  tasa 0.4299 (ctl 0.9383) -272 +0 p=0.0 | noches pos 278 pubA 264/278 pubB 256/278 perdA 14 perdB 22 ganB 0 | mag n=425 0.72 (ctl 0.7297) | suf=True -> PIERDE(noches)
-- _s135_ab_e_sp_off
   Isluga               neg   19/21   tasa 0.9048 (ctl 0.9048) -0 +0 p=1.0 | noches pos  74 pubA 74/74 pubB 74/74 perdA 0 perdB 0 ganB 0 | mag n=130 0.6325 (ctl 0.634) | suf=False -> EMPATA
   Lascar               neg   41/50   tasa 0.82 (ctl 0.82) -0 +0 p=1.0 | noches pos  61 pubA 61/61 pubB 61/61 perdA 0 perdB 0 ganB 0 | mag n=110 0.6144 (ctl 0.6287) | suf=True -> EMPATA
   Lastarria            neg   50/52   tasa 0.9615 (ctl 0.9615) -0 +0 p=1.0 | noches pos  50 pubA 50/50 pubB 50/50 perdA 0 perdB 0 ganB 0 | mag n=76 0.8736 (ctl 0.9598) | suf=True -> EMPATA
   PuyehueCordonCaulle  neg  139/146  tasa 0.9521 (ctl 0.9589) -1 +0 p=1.0 | noches pos  37 pubA 37/37 pubB 37/37 perdA 0 perdB 0 ganB 0 | mag n=86 0.7401 (ctl 1.021) | suf=True -> EMPATA
   PlanchonPeteroa      neg  134/144  tasa 0.9306 (ctl 0.9514) -3 +0 p=0.25 | noches pos  28 pubA 28/28 pubB 28/28 perdA 0 perdB 0 ganB 0 | mag n=44 0.8856 (ctl 0.9558) | suf=True -> EMPATA
   Tupungatito          neg  111/122  tasa 0.9098 (ctl 0.9426) -4 +0 p=0.125 | noches pos  28 pubA 28/28 pubB 28/28 perdA 0 perdB 0 ganB 0 | mag n=51 0.5507 (ctl 0.562) | suf=True -> EMPATA
   TODOS                neg  494/535  tasa 0.9234 (ctl 0.9383) -8 +0 p=0.007812 | noches pos 278 pubA 278/278 pubB 278/278 perdA 0 perdB 0 ganB 0 | mag n=497 0.696 (ctl 0.7485) | suf=True -> GANA
   NULO: {"_s135_ab_b_nokeeppeak": {"n_vol_suficientes": 5, "gana_bajo_nulo_media": 0.078, "gana_bajo_nulo_p97.5": 1}, "_s135_ab_c_cond": {"n_vol_suficientes": 5, "gana_bajo_nulo_media": 0.0, "gana_bajo_nulo_p97.5": 0}, "_s135_ab_d_ambos": {"n_vol_suficientes": 5, "gana_bajo_nulo_media": 0.084, "gana_bajo_nulo_p97.5": 1}, "_s135
```

### Veredicto de P2, por brazo (exploratorio)

- **S143 `literal` y `lit_sp_suelto`** (idénticos en esta lectura): perdieron por 5 noches según la cota escalar. En unidades del operador **no pierden ninguna noche en ningún volcán**, ni por (a) ni por (b) (308 de 308), y bajan la publicación en negativos limpios de 91,7 % a 54,7 %. Ganan en 7 de los 7 volcanes con muestra suficiente, contra 1 que daría el azar. Es el caso «perdió en el agregado, gana en todos los volcanes». Dos salvedades que no son menores: publicar la misma pasada no prueba que sea el mismo objeto (el verificador de S143 mostró que en esas 5 noches el píxel pico es el mismo y cambia qué píxel define el cúmulo); y en Nevados de Chillán el brazo publica 6 negativos limpios que el control no, que es el riesgo de relieve tibio. La magnitud se acerca a 1 en el total (0,773 a 0,945) pero se pasa de largo en Tupungatito (0,562 a 1,113) y empeora en Chaitén (1,296 a 1,481).
- **S143 `lit_keep_peak`**: empata en todos los volcanes (92,0 % contra 91,7 %, p 0,607). Confirma que todo el descenso de publicación sale de apagar `keep_peak`, no de D22 ni de D25.
- **S143 `lit_sin_fondo`**: gana en publicación donde hay muestra, pero pierde noches por (b) en 2 volcanes (Isluga 2, NevadosDeChillan 3). **`lit_con_compuerta`**: pierde noches en 7 de los 9 volcanes (Isluga 10, Lastarria 4, PlanchonPeteroa 5, Tupungatito 3, Chaiten 4, Villarrica 1, NevadosDeChillan 3). Ninguno de los dos revierte su veredicto.
- **S135 brazo B (sin `keep_peak`)**: perdió por 0,016 de paridad agregada. Por volcán gana en publicación en los 5 con muestra suficiente (93,8 % a 58,1 %) y no pierde ninguna noche por (a). Por (b) pierde 2 noches, las dos en Isluga (2026-06-30; 2026-07-28), que queda sin muestra suficiente de negativos (n 21). La paridad de magnitud, que fue lo que lo tumbó, por volcán es **mixta y no uniforme**: mejora en Lastarria (0,965 a 1,012) y Planchón-Peteroa (0,956 a 0,997), no cambia en Láscar ni en Puyehue, y empeora en Tupungatito (0,556 a 0,494) e Isluga (0,632 a 0,582). O sea: el criterio agregado no escondía una victoria pareja, escondía una mezcla.
- **S135 C y E** (tocar sólo el segundo pase): empatan en todos los volcanes con muestra; la baja agregada de 8 pasadas de 535 no aparece en ningún volcán por separado. **S135 D**: pierde noches en 4 de 6 volcanes (Isluga 10, Lastarria 4, PlanchonPeteroa 5, Tupungatito 3). Sin cambios respecto de sus veredictos.
- **Observación sin interpretar (SOSPECHA)**: `lit_sin_fondo` de S143 da casi los mismos conteos que el brazo B de S135, y `lit_con_compuerta` los mismos que el D, volcán por volcán. No comparé los perfiles; lo anoto porque, si son el mismo tratamiento, S143 replicó a S135 en otro arnés.
- **Qué dice para el A/B que viene**: el brazo que sale mejor parado de la re-lectura es el `literal` de S143 (sin `keep_peak`, sin compuerta, con fondo por vecinos). Llevarlo a una ventana nueva y fuera de muestra, con criterio en noches y pasadas, es lo que esta lectura habilita. No habilita adoptarlo. Y sigue en pie el límite de S144: sin dirección (acimut) no se separa relieve tibio de fuente permanente.

## 3. P6: la regla de preferencia entre banda I y banda M

### Qué dice el paper

Coppola et al. 2026, *Scientific Data* (`documentacion/Coppola_2026_SciData_Global_VRP_Dataset_s41597-026-08100-7.pdf`), **página 7 de 25 del PDF, sección «Data aggregation», tercer párrafo**. Validado renderizando la página a imagen con PyMuPDF a 200 dpi y leyéndola (la capa de texto coincide en este pasaje). Cita textual, única de este informe:

> «For coincident VIIRS detections, the 750 m observation was retained»

El mismo párrafo dice antes que las detecciones de 375 m sin par de 750 m se conservan, y las de 750 m sin par de 375 m también; y después, que no hubo control de calidad adicional ni revisión manual en ese paso. La razón que da es instrumental: el canal I4 satura antes sobre fuentes intensas porque tiene una sola ganancia. La figura 2 (página 14 del PDF) repite la regla en su leyenda.

### Lo que la regla es y lo que no es

Es una regla para **no contar dos veces la misma detección** al fundir tres archivos ya filtrados en uno: si las dos bandas detectaron en el mismo paso, se queda la de 750 m; si detectó una sola, se queda ésa. **No es un veto**: el paper no dice que una detección de 375 m se descarte cuando la banda de 750 m miró y no vio nada. Al revés, dice que se conserva. Y es una regla del archivo OSF filtrado, no del canal NRT (A105).

**El paper dice lo que el censo cita, pero no lo que el censo infiere.** El frente F supuso que aplicar la regla «reduciría la sobre-publicación de las pasadas coincidentes sin tocar ningún umbral». Por construcción no puede: una unión deduplicada publica exactamente los mismos pasos. Lo único que cambia es qué record representa al paso.

### Medición sobre los records (ventana 2026-09-01 a 2026-09-20)

El pareo I con M funciona: de 954 pasos VIIRS nocturnos, 949 tienen record de las dos bandas (mismo satélite, mismo minuto).

| combinación | publicación en negativos limpios por PASO | noches positivas publicadas (VIIRS) |
|---|---|---|
| hoy (publica la I o la M) | 88,2 % (469 de 532) | 77 de 77 |
| regla del paper (unión deduplicada) | 88,2 % (469 de 532) | 77 de 77 |
| veto, que NO está en el paper (la I sólo vale si la M también publica) | 19,7 % (105 de 532) | 45 de 77 |

- **Regla del paper**: cambia 0 pasos publicados. Reemplaza el record de 375 m por el de 750 m en 103 pasos de negativo limpio y 56 positivos: es un cambio de qué magnitud se muestra, no de si se publica. Recall por noche, sin cambio.
- **Por qué la unión no ayuda**: en los pasos con negativo limpio en la banda I y las dos bandas presentes (n 372), la I publica sola en 254, las dos en 68, la M sola en 2. La sobre-publicación de 375 m ocurre justo donde la de 750 m calla, que es el caso que el paper manda conservar.
- **El veto** bajaría la publicación a 19,7 %, pero perdería 32 de 77 noches positivas: en los pasos positivos la M calla en 89 de 143. Y no discrimina: borra 78,9 % de las I publicadas en negativos y 62,2 % en positivos; el contraste 0,1664 cae dentro del nulo barajado por volcán (0,0740 a 0,2146). Es apagar VIIRS 375 con otro nombre.
- **La sospecha del cruce (una fila de MIROVA contra dos records nuestros) queda REFUTADA para el NRT**: la referencia trae fila de las dos bandas en 633 minutos, de sólo 375 m en 54 y de sólo 750 m en 44. MIROVA NRT no deduplica. Y el propio MIROVA alerta en 375 m con la fila de 750 m del mismo minuto en silencio 131 veces, contra 22 con las dos alertando: MIROVA tampoco aplica un veto en su NRT.

```
CONTROL POSITIVO {'VIIRS375': [373, 0.8633], 'VIIRS750': [622, 0.2138]} reproduce: True
REFERENCIA NRT minutos con fila por banda: {('VIIRS375', 'VIIRS750'): 633, ('VIIRS375',): 54, ('VIIRS750',): 44}
REFERENCIA NRT alertas y la otra banda: {'VIIRS375|otra_banda_fila_sin_alerta': 131, 'VIIRS375|otra_banda_alerta': 22, 'VIIRS375|otra_banda_sin_fila': 34, 'VIIRS750|otra_banda_fila_sin_alerta': 2, 'VIIRS750|otra_banda_alerta': 15, 'VIIRS750|otra_banda_sin_fila': 1}
PAREO I-M: pasos 954 {'IM': 949, 'I-': 5}
2x2 (etiqueta de la banda I): {"neg_limpio": {"n": 372, "I_si_M_si": 68, "I_si_M_no": 254, "I_no_M_si": 2, "I_no_M_no": 48, "lab_M": {"neg_limpio": 350, "sin_info": 20, "far_ref": 1, "pos": 1}}, "pos": {"n": 143, "I_si_M_si": 54, "I_si_M_no": 89, "I_no_M_si": 0, "I_no_M_no": 0, "lab_M": {"neg_limpio": 88, "sin_info": 39, "far_ref": 1, "pos": 15}}}
== HOY: neg por paso {'n': 532, 'pub': 469, 'tasa': 0.8816} | con etiqueta de I {'n': 373, 'pub': 324, 'tasa': 0.8686} | noches {'n_noches_pos_viirs': 77, 'publicadas_viirs': 77, 'publicadas_con_modis': 77, 'perdidas_viirs': []}
== L1_PAPER: neg por paso {'n': 532, 'pub': 469, 'tasa': 0.8816} | con etiqueta de I {'n': 373, 'pub': 324, 'tasa': 0.8686} | noches {'n_noches_pos_viirs': 77, 'publicadas_viirs': 77, 'publicadas_con_modis': 77, 'perdidas_viirs': []}
== L2_VETO: neg por paso {'n': 532, 'pub': 105, 'tasa': 0.1974} | con etiqueta de I {'n': 373, 'pub': 70, 'tasa': 0.1877} | noches {'n_noches_pos_viirs': 77, 'publicadas_viirs': 45, 'publicadas_con_modis': 47, 'perdidas_viirs': [['Chaiten', '2026-09-06'], ['Chaiten', '2026-09-07'], ['Chaiten', '2026-09-12'], ['Chaiten', '2026-09-13'], ['Isluga', '2026-09-02'], ['Isluga', '2026-09-09'], ['Lascar', '2026-09-07'], ['Lascar', '2026-09-11'], ['Lascar', '2026-09-12'], ['Lascar', '2026-09-16'], ['Lastarria', '2026-09-01'], ['Lastarria', '2026-09-02'], ['Lastarria', '2026-09-04'], ['Lastarria', '2026-09-07'], ['Lastarria', '2026-09-13'], ['Lastarria', '2026-09-15'], ['NevadosDeChillan', '2026-09-05'
L1 cambia pasos publicados: 0 | records I reemplazados por M: {'neg_limpio': 103, 'pos': 56, 'sin_info': 38, 'far_ref': 8}
NULO L2: {'frac_I_neg_borradas': 0.7888, 'frac_I_pos_borradas': 0.6224, 'contraste_obs': 0.1664, 'nulo_media': 0.1417, 'nulo_p2.5': 0.074, 'nulo_p97.5': 0.2146, 'fuera_del_nulo': False}
```

### Veredicto de P6

**El paper no dice lo que el censo esperaba, y la medición lo confirma.** La regla de Coppola 2026 es una deduplicación de un archivo filtrado: aplicada a nuestros records no mueve ni la publicación en negativos limpios ni el recall por noche. No hay brazo de A/B que sacar de acá para la sobre-publicación. Lo único aprovechable es de presentación y de magnitud: cuando las dos bandas publican el mismo paso, MIROVA se queda con la de 750 m en su archivo, y una comparación de magnitud contra el OSF (no contra el NRT) debería hacer lo mismo. La lectura de veto no tiene respaldo en el paper ni en el comportamiento del NRT de MIROVA, y costaría cerca de cuatro de cada diez noches.

## 4. Qué no se hizo y qué queda como SOSPECHA

- P1 no re-ejecuta el ensamblado: es una cota sobre campos persistidos. Llevarla a simulación pide el probe de la Fase 1.
- P1: no se separó el efecto del anillo intermedio de S112 en Láscar, Nevados de Chillán y Lastarria.
- P2: recall por noche sin verificar identidad del objeto. La igualdad de tratamientos entre brazos de S143 y S135 no se comprobó contra los perfiles.
- P2: MODIS y VIIRS 750 no están en esos A/B; nada de lo dicho vale para ellos. La ventana es en muestra para los dos experimentos.
- P6: no se midió el efecto de la regla sobre la paridad de magnitud.
- Los artefactos de S143 se leyeron del scratchpad de otra sesión (ruta en `resultado_ab_s143.json`, `meta.dir_artefactos`); si esa carpeta temporal se borra, P2 de S143 deja de ser reproducible salvo que se vuelvan a bajar los runs.
