# Verificador con contexto limpio del probe v2, después de la corrida (run 34967596160)

Fecha: 2026-09-15. Rama: `main` en `a54ce6d32`. Sólo lectura: no se modificó ningún archivo existente, no hubo commits,
ramas ni despachos. Scripts del verificador (nuevos) en
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s141_fase1_probe_v2\_verificador\`:
`reproducir.py`, `estratificar.py`, `sensibilidad.py`, `complementos.py`, `contraste_perdidos.py`. Todo número de este
informe sale de la salida de uno de ellos o de `criterio_total.json`; ninguno se transcribió de otro informe.

## 0. Veredicto global

**Veredicto reproducido: SÍ, bit a bit.** El criterio aplicado es el pre-registrado (constantes y reglas coinciden con
el plan §5). Los controles C1 a C4 dan 1,0 y tres de los cuatro pueden fallar.

Pero **la lectura física de "HETEROGENEO" que sugiere el rótulo es falsa en la limitante y engañosa en el contraste**:

- En la limitante no hay tests distintos en volcanes distintos. Dentro de cada ruta falla siempre el mismo test, y
  siempre contra el mismo umbral: el piso C1 = 0,003. Lo que cambia de pasada en pasada es **qué ruta publicó**
  (contextual o Test 1), y el agregado queda a 0,8 puntos del corte.
- En el contraste, el `VECINOS_TIBIOS` de Puyehue lo ponen los vecinos que **ya incluimos**. Si se mide sólo sobre los
  vecinos perdidos, 4 de 5 volcanes quedan SIN_CONTRASTE.

Ninguna de las dos cosas cambia el veredicto pre-registrado, que sigue siendo válido tal como está escrito, y ninguna
justifica un brazo de A/B.

## 1. Reproducción

**Artefactos iguales a los de CI.** `gh run download 34967596160` a un directorio del scratchpad, comparado con
`diff -rq` contra `experiments/_s141_fase1_probe_v2/artefactos`. Salida: `ARTEFACTOS_IDENTICOS_A_CI`. El run completó
6 jobs `success`, de 2 min 18 s (Chaitén) a 7 min 25 s (Láscar) (`gh run view 34967596160 --json jobs`). No es un job
verde sin datos: 38 filas `ok: true`.

**Re-agregación.** `reproducir.py` llama `juntar.resumen_total` sobre los artefactos, escribe
`_verificador/criterio_total_reproducido.json` (no pisa el original) y compara:

```
identico_objeto: True
identico_texto: True
total HETEROGENEO | HETEROGENEO | fondo vecinos HETEROGENEO | fondo cumulo NO_CIERRA {'n_ok': 38, 'n_sin_primary_cluster': 0, 'n_con_alineacion': 38, 'c1': 1.0, 'c2': 1.0, 'c3': 1.0, 'c4': 1.0, 'estado': 'OK'}
focal HETEROGENEO | HETEROGENEO | fondo vecinos HETEROGENEO | fondo cumulo NO_CIERRA {'n_ok': 36, ... 'c1': 1.0, 'c2': 1.0, 'c3': 1.0, 'c4': 1.0, 'estado': 'OK'}
nevado INDETERMINADO:pocos_volcanes {'n_ok': 2, ... 'estado': 'OK'}
```

## 2. ¿El veredicto sale del criterio tal como está escrito?

| Pre-registro (plan §5) | Código | ¿Coincide? |
|---|---|---|
| foco a ≤ 0,75 km, sin rama del cráter | `analisis_v2.py:34`, `:322` (`d_osf <= RADIO_FOCO_KM`) | Sí |
| ≥ 3 pasadas por volcán, ≥ 3 volcanes | `:35-36`, `:457`, `:482` | Sí |
| limitante con fracción ≥ 0,60 | `:37`, `:404-409` | Sí |
| ≥ 2/3 de volcanes y deja-uno-fuera sobre el agregado | `:38`, `:470-474` | Sí |
| contraste ≥ 1,0 K | `:39`, `:460-462` | Sí |
| fondo ≥ 0,5 CIERRA, < 0,2 NO_CIERRA | `:40`, `:412-415` | Sí |
| C1 ≥ 0,90, C2 ≥ 0,95, C3 = C4 = 1,0 | `:41`, `:386` | Sí |
| `Npix−1` vecinos (máx 8) de mayor BT | `:260-262` | Sí |
| pasada válida (lista del §5) | `:337-363` | Sí |

`test_constantes_pre_registradas` (`tests/test_probe_vecinos_v2_s141.py:513-517`) fija las mismas constantes.
La aritmética de las tres clases HETEROGENEO sale de las reglas: con 5 volcanes, 2/3 exige 4 de 5, y las tres
quedaron en 3 de 5 (contraste: VECINOS_TIBIOS en 2, SIN_CONTRASTE en 3; fondo de vecinos: PARCIAL en 3, NO_CIERRA en
2; limitante: apoyo 3 de 5).

## 3. Estratificación por volcán (estrato focal, 24 pasadas válidas)

Primero lo físico. En los cinco volcanes el píxel central es claramente anómalo (su exceso sobre el fondo local va de
5,5 K a 57 K, `estratificar.py`). Los vecinos que MIROVA sumaría y nosotros no, en cambio, casi nunca tienen un índice
espectral por encima del de sus propios vecinos.

| volcán | pasadas válidas (rutas) | limitante dominante y fracción | contraste (K) | margen rel. mediano | fondo vecinos | fondo cúmulo |
|---|---|---|---|---|---|---|
| Isluga | 6 (5 contextual, 1 Test 1) | `contextual:deti_2p+dnti_2p` 16/21 | −0,755 SIN_CONTRASTE | −1,331 | 0,099 NO_CIERRA | 0,188 NO_CIERRA |
| Láscar | 6 (5 contextual, 1 Test 1) | `contextual:deti_2p+dnti_2p` 14/19 | 1,663 VECINOS_TIBIOS | −1,056 | 0,063 NO_CIERRA | 0,079 NO_CIERRA |
| Lastarria | 3 (2 contextual, 1 Test 1) | DISPERSO (4/7) | −1,487 SIN_CONTRASTE | −0,945 | 0,448 PARCIAL | −0,051 NO_CIERRA |
| Planchón-Peteroa | 5 (2 contextual, 3 Test 1) | DISPERSO (6/11 `test1:bt_ctx+dnti_ctx`) | −0,105 SIN_CONTRASTE | −0,979 | 0,450 PARCIAL | −0,001 NO_CIERRA |
| Puyehue-Cordón Caulle | 4 (4 contextual) | `contextual:deti_2p+dnti_2p` 8/12 | 1,768 VECINOS_TIBIOS | −0,899 | 0,260 PARCIAL | −0,010 NO_CIERRA |

(Los números vienen de `criterio_total.json` `por_volcan`; las rutas y los conteos por pasada, de `estratificar.py`.)

**Excluidas (6 candidatos, `estratificar.py`):** Lastarria 2025-05-11, 2025-07-21 y 2025-10-03 por
`foco_mirova_lejos_hoy` (nuestro centro de hoy a 1,30, 1,74 y 1,21 km del punto OSF, aunque la muestra había filtrado
con el pico persistido a ≤ 0,75 km); Planchón-Peteroa 2025-10-21 y Puyehue 2025-07-03 y 2025-10-01 por
`ya_no_publica_menos` (hoy publicamos 4, 4 y 6 píxeles contra `Npix` 3, 4 y 3).

**Peso de una pasada (`estratificar.py`):** ningún volcán depende de una sola. La pasada con más vecinos pesa entre
0,263 (Láscar) y 0,429 (Lastarria) de los vecinos perdidos del volcán. Isluga 2025-02-25 (`Npix` 8) aporta 7 de 21.

## 4. Hallazgos, ordenados por gravedad

### G4.1 · HETEROGENEO en la limitante es la mezcla de dos rutas, no de tests; dentro de cada ruta falla siempre el mismo umbral

- **Archivo:línea:** `analisis_v2.py:400-401` (clave = `ruta:combinación exacta de tests`), `margenes.py:161-196`.
- **Qué pasa.** La clave del conteo junta la ruta con la combinación exacta de tests que fallan. Resultado de
  `estratificar.py` sobre los 70 vecinos calientes perdidos:
  ```
  contextual n 52 deti presente 52 dnti presente 45 bt presente 0 disco 0
  test1 n 18 deti presente 0 dnti presente 13 bt presente 18 disco 2
  ```
  Y `sensibilidad.py`: `Counter({('contextual', 0.003, 0.003): 52, ('test1', 0.003, None): 18})`. El umbral efectivo
  es el piso C1 de cumbre, 0,003, en los 70 casos: la rama estadística `mu + C2·sigma` no gobierna nunca (la conectiva
  es `min`, `ENABLE_TESTS_23_PROSE_BRANCH = False`, leído de `pipeline.process_viirs`).
  En la ruta contextual el dETI falla en 52 de 52 casos; en la del Test 1, la compuerta de BT falla en 18 de 18. Lo
  que separa a Lastarria y Planchón-Peteroa (DISPERSO) es que 1 de 3 y 3 de 5 de sus pasadas publicaron por el
  Test 1. El agregado queda en el filo:
  ```
  agregado dominante [('contextual:deti_2p+dnti_2p', 45)] n 70 frac 0.6429
   LOO sin Isluga ('contextual:deti_2p+dnti_2p', 29) 49 frac 0.5918
   sin PlanchonPeteroa -> PATRON:contextual:deti_2p+dnti_2p | HETEROGENEO | ...
  ```
- **Cómo cambia el veredicto.** El veredicto pre-registrado sigue siendo HETEROGENEO. Lo falso sería leerlo como "cada
  volcán pierde sus vecinos por un test distinto". Lo que muestran los datos es otra cosa: la ruta que publica varía
  pasada a pasada, y dentro de la ruta el resultado es uniforme. Además, la partición entre `deti_2p` y
  `deti_2p+dnti_2p` divide un mismo fenómeno en dos claves. Quitando un solo volcán (Planchón-Peteroa) el rótulo pasa
  a PATRON: es un veredicto frágil, no una heterogeneidad robusta.
- **Reproducir:** `python experiments/_s141_fase1_probe_v2/_verificador/estratificar.py` y `.../sensibilidad.py`.
- **Confianza:** CONFIRMADO. **Gravedad:** 4.

### G4.2 · El VECINOS_TIBIOS de Puyehue lo ponen los vecinos que ya incluimos, no los perdidos

- **Archivo:línea:** `analisis_v2.py:326` (`exceso_mediano_calientes_k` sobre `f["caliente"]`, incluidos o no).
- **Qué pasa.** El contraste promedia todos los vecinos calientes, y los incluidos son píxeles ya detectados, así que
  suben el exceso. La pregunta del probe es por los **perdidos**. Salida de `complementos.py` y
  `contraste_perdidos.py`:
  ```
  Lascar               n_calientes_incluidos=9 ... contraste_criterio=1.663 contraste_solo_perdidos=1.259 (VECINOS_TIBIOS) exceso_mediano_incluidos=7.68
  PuyehueCordonCaulle  n_calientes_incluidos=3 ... contraste_criterio=1.768 contraste_solo_perdidos=0.859 (SIN_CONTRASTE) exceso_mediano_incluidos=4.68
  clase global solo perdidos: SIN_CONTRASTE
  ```
  En Isluga, Lastarria y Planchón-Peteroa no hay vecinos calientes incluidos: su valor no cambia.
- **Cómo cambia el veredicto.** El código es fiel al texto del pre-registro ("los calientes"), así que el veredicto
  registrado no se toca. Pero el "HETEROGENEO" del contraste esconde que, medidos sobre lo que se pierde, 4 de 5
  volcanes no tienen vecinos más tibios que el control por 1 K, y esa clase sería estable al sacar cada volcán. Esta
  lectura es **post hoc** y no puede reemplazar al veredicto. Lo que sí queda falso es cualquier frase del tipo "en
  Láscar y Puyehue los vecinos perdidos son tibios".
- **Reproducir:** `python experiments/_s141_fase1_probe_v2/_verificador/contraste_perdidos.py`.
- **Confianza:** CONFIRMADO. **Gravedad:** 4.

### G3.3 · Los "vecinos calientes" elegidos por rango de BT no son, en su mayoría, vecinos con calor del foco

- **Archivo:línea:** `analisis_v2.py:190-192`, `:260-262`.
- **Qué pasa.** El fenómeno que el probe quiere medir es el calor del foco que se derrama hacia los vecinos. Pero el
  instrumento no elige los vecinos por ese calor: toma los `Npix−1` de mayor BT entre los 8. En una cumbre de noche,
  una BT más alta también puede venir de una ladera más baja o de la textura de nieve. Resultado (`sensibilidad.py`):
  ```
  margen_rel < -1 (indice del vecino bajo cero, no solo bajo el umbral) por volcan: {'Isluga': [13, 20], 'Lascar': [10, 17], 'Lastarria': [3, 6], 'PlanchonPeteroa': [5, 10], 'PuyehueCordonCaulle': [6, 12]}
  vecinos calientes perdidos con exceso_local <= 0 K por volcan: {'Isluga': [11, 21], 'Lascar': [2, 19], 'Lastarria': [2, 7], 'PlanchonPeteroa': [1, 11], 'PuyehueCordonCaulle': [3, 12]}
  ```
  En 37 de 65 casos con margen relativo, el índice del vecino es **negativo**: su NTI queda bajo la media de sus
  vecinos, no apenas bajo el umbral. Con `Npix` grande el criterio toma casi todo el anillo (Isluga 2025-02-25: `k=7`,
  exceso mediano −0,93 K).
- **Cómo cambia el veredicto.** "Por cuánto" (márgenes relativos medianos de −0,90 a −1,33) no mide cuánto le falta a
  un vecino tibio para pasar; mide sobre todo vecinos sin señal espectral. Leer el margen como "hay que bajar el umbral
  ~100 %" sería falso. El supuesto D17 declarado en el plan §5 (los `Npix` de MIROVA, que son celdas de su grilla
  remuestreada, se tratan como nuestros vecinos nativos) está detrás de esta elección de `k`.
- **Reproducir:** `python experiments/_s141_fase1_probe_v2/_verificador/sensibilidad.py`.
- **Confianza:** CONFIRMADO en los números; SOSPECHA en el mecanismo (topografía o textura), porque los artefactos no
  traen la grilla ni un modelo de elevación.
  **Gravedad:** 3.

### G3.4 · En la ruta del Test 1, la compuerta `bt > t_bg + 3 K` se mide contra el anillo regional, más tibio que la cumbre

- **Archivo:línea:** `pipeline/process_viirs.py:1034-1043` (`t_bg=t_bg_i04`, `bt_sanity_k=NTI_BT_SANITY_K` = 3,0),
  `:1798-1799` (cúmulo del Test 1 = Test 1 ∩ dNTI contextual más el pico); `margenes.py:132`.
- **Qué pasa.** De noche, el fondo del anillo de 5 a 25 km incluye terreno más bajo y más tibio que la cumbre (A69).
  Salida de `complementos.py`:
  ```
  PlanchonPeteroa      t_bg_anillo_ruta - mediana_BT_1a3km: mediana=6.16 K ... test1: vecinos perdidos con bt_ctx=7, de ellos superan mediana_1a3km+3K=1 | centros bajo la compuerta=[('2025-07-10 06:12', 'test1', -0.88), ('2025-08-07 05:24', 'test1', -3.7), ('2025-10-10 05:24', 'test1', -1.09)]
  PuyehueCordonCaulle  t_bg_anillo_ruta - mediana_BT_1a3km: mediana=4.57 K ...
  Lascar               t_bg_anillo_ruta - mediana_BT_1a3km: mediana=3.21 K ... de ellos superan mediana_1a3km+3K=3
  ```
  En las 3 pasadas del Test 1 de Planchón-Peteroa, el propio píxel central no pasa la compuerta y entra al cúmulo sólo
  por `keep_peak`. Con una referencia local (mediana de 1 a 3 km más 3 K) pasarían 6 de los 18 vecinos perdidos de esa
  ruta, no los 18.
- **Cómo cambia el veredicto.** `test1:bt_*` mezcla la compuerta de D22 con el desnivel topográfico del anillo, así que
  no es una limitante "térmica" pura. Si algún día saliera PATRON en `bt_ctx`, el brazo de A/B no podría ser "quitar
  la compuerta" sin separar primero esa mezcla. Al mismo tiempo, 12 de 18 vecinos tampoco superan la referencia local:
  el desnivel no lo explica todo.
- **Reproducir:** `python experiments/_s141_fase1_probe_v2/_verificador/complementos.py` (bloque B).
- **Confianza:** CONFIRMADO en los números; la atribución a la altitud es SOSPECHA (el anillo de 1 a 3 km es la
  mediana persistida por el probe S135, no una medición de elevación). **Gravedad:** 3.

### G2.5 · El fondo del cúmulo está sesgado hacia NO_CIERRA por construcción, pero la clase global resiste

- **Archivo:línea:** `analisis_v2.py:251` (`alerta = entrada | en_cumulo`), `:316`, `:175-180`.
- **Qué pasa.** El fondo local se calcula con **nuestra** máscara de alertas, así que los vecinos calientes no
  alertados entran al fondo del centro. Los `k` de mayor BT pesan al menos lo que el promedio del resto, de modo que
  incluirlos sólo puede subir el fondo y bajar el aporte. MIROVA, en cambio, sí los alerta y los saca del fondo.
  Recalculado para las pasadas con un solo píxel en el cúmulo (la recomputación del 3x3 reproduce el JSON: Isluga
  2025-02-25 `frac_fondo_probe=0.109 (json 0.109)`):
  ```
  Isluga               n=6 mediana_probe=0.188 (NO_CIERRA) mediana_mascara_miro=0.222 (PARCIAL)
  PlanchonPeteroa      n=5 mediana_probe=-0.001 (NO_CIERRA) mediana_mascara_miro=0.155 (NO_CIERRA)
  ```
  La fracción sube en las 17 pasadas de un píxel; Lastarria 2025-02-19 pasa de −0,068 a 0,376.
- **Cómo cambia el veredicto.** "Fondo del cúmulo NO_CIERRA" es un límite inferior, no una medición neutra. Con la
  máscara tipo MIROVA sólo Isluga cambiaría de clase (4 de 5 siguen NO_CIERRA), así que la clase global probablemente
  se mantiene. Esto es SOSPECHA para el cúmulo completo: sólo se pudo recalcular el centro en pasadas de un píxel.
- **Reproducir:** `complementos.py` (bloque C) y `sensibilidad.py`.
- **Confianza:** CONFIRMADO el sesgo y su dirección; SOSPECHA su tamaño fuera de esas pasadas. **Gravedad:** 2.

### G2.6 · C4 valida la decisión, casi nunca la magnitud del margen

- **Archivo:línea:** `margenes.py:79`, `:121`, `:152`.
- **Qué pasa.** C4 compara el "pasa" recalculado con la máscara real. Un error en el umbral o en la media sólo lo
  detecta si cruza la decisión. `estratificar.py`:
  `perdidos totales 70 tests de indice con |margen|<0.1|umbral| (zona donde C4 informa): 1`.
- **Cómo cambia el veredicto.** C4 = 1,0 respalda la limitante (qué test falla), no el "por cuánto". Con márgenes del
  orden de −100 % del umbral, un error moderado en la réplica pasaría sin que C4 se enterara.
- **Reproducir:** `estratificar.py`. **Confianza:** CONFIRMADO. **Gravedad:** 2.

### G2.7 · El foco de MIROVA está cuantizado (D15): `foco_ok` mide contra el centro de una celda

- **Archivo:línea:** `analisis_v2.py:257`, `:322`.
- **Qué pasa.** `estratificar.py`: `Lascar 8 pares unicos 1`, `Isluga 7 pares unicos 4`,
  `PlanchonPeteroa 6 pares unicos 3`. En Láscar, las 8 pasadas traen exactamente el mismo `LAT/LON` del OSF.
- **Cómo cambia el veredicto.** `foco_ok` garantiza que nuestro centro cae cerca de la celda que MIROVA reporta, no que
  el píxel caliente sea el mismo. No invalida la muestra (todos los centros válidos quedan a ≤ 0,43 km), pero la
  frase "mismo foco" es una cota, no una identidad.
- **Reproducir:** `estratificar.py`. **Confianza:** CONFIRMADO. **Gravedad:** 2.

### G1.8 · Lastarria entra justo con 3 pasadas; el veredicto no depende de ella

`criterio_total.json`: Lastarria `n_pasadas: 3`. `sensibilidad.py`:
`sin Lastarria -> HETEROGENEO | HETEROGENEO | fondo vecinos HETEROGENEO | fondo cumulo NO_CIERRA`. Sacar a Isluga, a
Láscar o a Puyehue cambia el fondo de vecinos o el contraste a una clase única; sacar a Planchón-Peteroa cambia la
limitante a PATRON (ver G4.1). CONFIRMADO. **Gravedad:** 1.

### G1.9 · Contraste por diferencia de medianas, no por pares

`analisis_v2.py:451-453`. La mediana de diferencias pareadas por pasada no cambia ninguna clase; Planchón-Peteroa
cambia de signo (−0,105 a 0,199) y sigue SIN_CONTRASTE (`sensibilidad.py`). CONFIRMADO. **Gravedad:** 1.

### G1.10 · "Incluido" y "sumado en lo publicado" difieren en 1 de 24 pasadas (H7 sigue)

`complementos.py` bloque D: `[('Lascar', '2025-11-13 05:06', 3, 6)]`: 3 índices en el cúmulo, 6 píxeles en el núcleo
F5. CONFIRMADO. **Gravedad:** 1.

### Descartado: el ángulo cenital no infla `Npix` en esta muestra (D17)

`sensibilidad.py`: `spearman(satzen, Npix) = 0.198 n 24`. No hay señal de que las pasadas oblicuas traigan más `Npix`.
El supuesto D17 (grilla remuestreada frente a la nativa) no se puede medir con estos artefactos: sigue como SOSPECHA
declarada del plan, no como defecto encontrado.

## 5. ¿Los controles pueden fallar?

| control | si lo medido estuviera roto, ¿fallaría? | si el instrumento estuviera muerto, ¿se vería distinto? |
|---|---|---|
| C1 captura = 1,0 (38/38) | Sí: sin coincidencia de `n_pixels` y centroide, `identificar_publicado` devuelve `sin_coincidencia` (`analisis_v2.py:88-89`) | Sí: sin eventos de cúmulo, `identificado` es False y C1 cae a 0 |
| C2 réplica F5 = 1,0 | **No** para el filtro: `nucleo_f5` y `f5_core_vrp_mw` corren sobre el mismo `rec_f5` (`ensamblar.py:22-24`), así que un filtro roto afecta a los dos por igual. Sólo detecta que el port diverja (tautológico, declarado H5) | Parcialmente: "ambos None" cuenta como acierto (`analisis_v2.py:369-370`) |
| C3 alineación = 1,0 (38 con comparación) | Sí: exige `len(indices) == n_pixels` y BT igual a ±0,006 K en la misma lat/lon (`:148-164`); un índice corrido cambia la BT. Sólo mira los píxeles publicados, pero los vecinos están en la misma grilla | Sí: sin nada que comparar devuelve None y no entra al denominador; los 38 tuvieron comparación |
| C4 réplica de márgenes = 1,0 | Sí para la decisión; casi nunca para la magnitud (G2.6). Tampoco detectaría que se tomó el evento equivocado, porque compara contra la salida de ese mismo evento. **Verificado aparte** que el evento es el correcto (§7) | Sí: sin márgenes `replica_ok` es None, la pasada sale como `sin_replica_de_margenes` y C4 no la cuenta como acierto |

## 6. Lectura legítima

**Qué afirma el probe v2 según su pre-registro.**

- Sobre 38 pasadas VIIRS 375 m del OSF 2025, el instrumento funcionó (C1 a C4 = 1,0, con C2 tautológico).
- En el estrato focal, con 5 volcanes evaluables, **ningún test limitante es común** según la regla de 0,60, 2/3 y
  deja-uno-fuera.
- El **fondo del cúmulo NO_CIERRA** en los 5 volcanes.
- El nevado queda INDETERMINADO:pocos_volcanes por construcción (sólo 2 controles de Chaitén).

**Qué justifica.** Nada. No hay PATRON, así que no hay brazo de A/B sobre ningún test. El fondo del cúmulo no CIERRA
ni es PARCIAL, así que tampoco hay brazo de D25 (aunque ese NO_CIERRA sea un límite inferior, G2.5).

**Qué NO afirma.**

- Que distintos volcanes pierdan vecinos por tests distintos (G4.1).
- Que en Láscar y Puyehue los vecinos perdidos sean tibios (G4.2).
- Que haya que bajar un umbral en ~100 % (G3.3).
- Que la compuerta D22 sea una limitante térmica pura (G3.4).
- Nada sobre nevados.
- Nada sobre la compuerta en la ruta contextual con segundo pase, que es imposible por construcción (plan §3.3).

**Descripción que no es veredicto (post hoc, no confirmatoria).** Dentro de cada ruta, el vecino perdido falla siempre
contra el piso C1 = 0,003, y la mayoría tiene el índice bajo cero. Es compatible con que los vecinos que MIROVA suma no
sean, en nuestra grilla nativa, vecinos detectables por NTI a 375 m. Pero salió de mirar estos datos y no se puede
confirmar con estas mismas 38 pasadas.

**Medición mínima para salir de HETEROGENEO.** Un v3 con pre-registro nuevo, escrito antes de ver datos nuevos:

1. Separar las rutas contextual y Test 1 en dos preguntas, con la **pasada** como unidad de conteo en vez del vecino.
2. Medir el contraste **sólo sobre vecinos perdidos**.
3. Elegir los vecinos por exceso de NTI o dNTI, o reportar ambas selecciones, en vez de por rango de BT.
4. Para la ruta del Test 1, reportar la compuerta contra el anillo regional y contra una referencia local.
5. Muestra nueva con suficientes pasadas por ruta en cada volcán.

Estas 38 pasadas ya se miraron: sirven para diseñar, no para confirmar.

## 7. VERIFICADO LIMPIO

- `criterio_total.json` se reproduce bit a bit desde los artefactos, y los artefactos son idénticos a los del run
  34967596160.
- Las constantes y reglas de `analisis_v2.py` coinciden con el plan §5 y con `test_constantes_pre_registradas`.
- **A89, selección del segundo pase:** las llamadas de `process_viirs.py:1149` y `:1164` pasan la máscara activa como
  argumento posicional; sólo la de `:1287` usa `active_mask=` por nombre. `_ultimo(eventos, "second_pass", via_kw)`
  (`analisis_v2.py:266`) toma la llamada correcta.
- En la ruta contextual con `ENABLE_FIRST_PASS_TESTS_2_AND_3` activo, `hot_mask_2d = fp_hot` (`process_viirs.py:1262`)
  pisa la combinación de rutas de `:1191`, y el segundo pase la reemplaza (`:1320`). La limitante contextual
  (`dnti_2p`, `deti_2p`) nombra los tests que de verdad alimentan ese cúmulo.
- Flags leídos de `pipeline.process_viirs` con `VRP_PROFILE=mirova_equivalent`: `DNTI_CONTEXTUAL_C1_SUMMIT` 0,003,
  `DNTI_CONTEXTUAL_C1_SCENE` 0,01, `NTI_BT_SANITY_K` 3,0, `ENABLE_TESTS_23_PROSE_BRANCH` False,
  `ENABLE_DUAL_ROI_SECOND_PASS` True, `ENABLE_NTI_RELATIVE_PATH` False.
- Ningún vecino sale `ninguno` ni `sin_datos` (no hay contradicción del instrumento en el conteo).
- Todas las brechas de las pasadas válidas son positivas; la recomputación del fondo del centro desde el 3x3 reproduce
  `fraccion_fondo` del JSON.
