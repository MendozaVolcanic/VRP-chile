# Variante «cumbre primero» de la regla de posición: informe (S193)

Preregistro: `experiments/_s193_radiante_variante/PREREGISTRO.md`, commit `4a29495d5`, escrito y subido antes de correr.
Base de datos y código: `origin/main` `76f52c7ec` (2026-11-21 21:01 UTC). Sólo experimento: no se tocó `pipeline/`,
`frontend/` ni `data/`. Números de `medir_variante.py` (salida `medir_variante_salida.txt`, `resultado.json`) y
`detalle_cambios.py` (salida `detalle_cambios_salida.txt`), todos en
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s193_radiante_variante\`.

## Veredicto según el preregistro: DECIDE NICOLÁS

La variante pasa el veto (no calla ninguna protegida que hoy se publica, con la tabla ni con tabla y OCR) y tiene sustrato
(recupera las 12 protegidas sólo OCR de Codex, una por una). No pasa el corte de costo: la concordancia de clase con la tabla
de MIROVA baja 5,14 puntos (98,73 % a 93,59 %; el corte era 0,5), porque publica como cumbre 114 pasadas en que la tabla de
MIROVA ubicó la fuente lejos. Falsas alarmas nuevas en negativos limpios: 0.

En una línea para decidir: **12 protegidas que sólo el OCR de MIROVA dice que están en la cumbre, contra 114 pasadas en que
la tabla de MIROVA dice que el calor estaba lejos y nosotros pasaríamos a publicarlo como cumbre.** Es, con otros números de
protegidas, el mismo canje que se rechazó el 2026-11-15 (sección 4).

## 1. El fenómeno

En algunas pasadas nocturnas el detector alerta un píxel débil sobre el cráter y, a 13 a 23 km, un cúmulo más caliente (en
Láscar e Isluga, típicamente el salar o la roca tibia del altiplano, o un borde de nube). La vía suma todos los alertados
para la potencia, como MIROVA, pero el record necesita un lugar. «Radiante» lo pone en el cúmulo más caliente: queda lejos,
la clase es `far` y la vista por defecto del tablero no lo publica. «Cumbre primero» lo pone en el cráter cuando hay al menos
un alertado dentro de `inner_radius_km`. La potencia publicada es la misma en las dos (la suma de todos los alertados), así
que lo único que cambia es si la pasada aparece como calor del volcán.

El costo físico es simétrico: la misma regla que rescata una alerta débil real en el cráter publica como «del volcán» la
potencia de una fuente lejana cada vez que hay, además, un alertado tibio cerca de la cumbre.

## 2. Resultado (ventana principal: noches del 2026-03-01 al 2026-11-18; 11 Tier A; pasadas nocturnas de la vía)

28.840 pasadas; la variante cambia la posición en 218 y la publicación en las mismas 218.

| Métrica (preregistro §5) | Tabla sola | Tabla y OCR (lectura A) |
|---|---|---|
| Protegidas en la ventana | 395 | 490 |
| Protegidas no publicadas con «radiante» | 0 | 20 |
| G1, protegidas recuperadas | 0 | **12** |
| L1, protegidas perdidas por la variante | **0** | **0** |
| G2, alertas recuperadas (cualquier VRP) | 9 | 40 |
| L2, publicaciones nuevas en negativos limpios | **0** | 0 |
| L3, publicaciones nuevas donde MIROVA ubicó la fuente lejos (`far_ref`) | **114** | 114 |
| Publicaciones nuevas en pasadas sin información de MIROVA (`sin_info`) | 95 | 61 |
| L4, clase igual a la de MIROVA, «radiante» | 98,73 % (2.017 de 2.043) | 96,52 % (2.388 de 2.474) |
| L4, clase igual a la de MIROVA, variante | 93,59 % (1.912 de 2.043) | 93,53 % (2.314 de 2.474) |

En la unidad del operador (noche-satélite con alguna protegida, A94), tabla y OCR: 456 noches; sin publicación con
«radiante» 18, con la variante 6; recuperadas 12, perdidas 0. Con la tabla sola: 363 noches, 0 sin publicación con
cualquiera de las dos.

La L4 de «radiante» con la tabla sola (98,73 % en 2.043 pasadas) coincide con el 98,7 % en 2.037 que cita D8', con un
instrumento propio (el de S185 no está en disco): la definición calza.

### Por sensor (tabla sola para el costo, tabla y OCR para la ganancia)

| Sensor | Cambian | G1 (tabla y OCR) | L1 | L2 (tabla) | L3 (tabla) | L4 tabla «radiante» a variante |
|---|---|---|---|---|---|---|
| MODIS | 1 | 0 | 0 | 0 | 1 | 100,00 % a 99,28 % |
| VIIRS 375 | 215 | 12 | 0 | 0 | 113 | 98,45 % a 91,65 % |
| VIIRS 750 | 2 | 0 | 0 | 0 | 0 | 99,45 % a 99,72 % |

Todo pasa en VIIRS 375: con píxeles de 375 m el salar y la roca tibia alrededor del cráter quedan resueltos como cúmulos
aparte. En MODIS y VIIRS 750 la variante casi no tiene sustrato (1 y 2 pasadas); el único cambio MODIS es la pasada de
Láscar Aqua 2026-03-30 07:25: publicaría 11,685 MW como cumbre, con el cúmulo más radiante a 26,22 km y una `far_ref` de
la tabla (la misma pasada que S185 citó contra «cercano» en MOD-D fase 4, con MIROVA a 26,87 km).

### Por volcán (VIIRS 375; el detalle por volcán y sensor de las dos lecturas está en `resultado.json`)

| Volcán | Cambian | G1 (tabla y OCR) | L3 (tabla) | L4 tabla «radiante» a variante |
|---|---|---|---|---|
| Isluga | 66 | 6 | 35 | 98,68 % a 88,12 % |
| Láscar | 53 | 4 | 28 | 96,77 % a 87,81 % |
| Lastarria | 45 | 1 | 26 | 99,03 % a 87,44 % |
| Tupungatito | 23 | 0 | 11 | 98,40 % a 92,55 % |
| Planchón-Peteroa | 19 | 0 | 9 | 98,54 % a 91,97 % |
| Cordón Caulle | 4 | 1 | 1 | 98,88 % a 98,32 % |
| Chaitén, Villarrica | 2 y 2 | 0 | 1 y 2 | 97,87 a 95,74 y 100 a 92,86 % |
| Chillán | 1 | 0 | 0 | 99,23 % sin cambio |

Ganancia y costo caen en los mismos volcanes del norte (Isluga, Láscar, Lastarria). Tupungatito y Planchón-Peteroa sólo
pagan.

## 3. Las 12 protegidas recuperadas

| Volcán | Satélite | Pasada (UTC) | MIROVA (OCR) | Publicaría | Cociente | Centroide «radiante» | Centroide variante |
|---|---|---|---|---|---|---|---|
| Láscar | Suomi NPP | 2026-03-15 05:00 | 1,54 MW | 1,198 MW | 0,78 | 12,985 km | 0,317 km |
| Láscar | NOAA-21 | 2026-04-25 05:00 | 1,72 | 1,716 | 1,00 | 22,398 | 0,117 |
| Láscar | NOAA-21 | 2026-06-12 05:00 | 1,04 | 1,072 | 1,03 | 15,292 | 0,28 |
| Láscar | NOAA-21 | 2026-10-01 05:18 | 1,2 | 1,046 | 0,87 | 18,99 | 0,123 |
| Lastarria | Suomi NPP | 2026-05-30 06:18 | 2,33 | 1,807 | 0,78 | 17,509 | 1,075 |
| Isluga | Suomi NPP | 2026-03-20 05:06 | 2,21 | 2,199 | 1,00 | 18,94 | 1,427 |
| Isluga | Suomi NPP | 2026-03-24 05:30 | 1,51 | 1,214 | 0,80 | 23,272 | 0,885 |
| Isluga | Suomi NPP | 2026-04-07 06:12 | 4,12 | 4,125 | 1,00 | 17,186 | 0,885 |
| Isluga | NOAA-21 | 2026-06-17 05:06 | 1,64 | 1,636 | 1,00 | 15,632 | 1,15 |
| Isluga | Suomi NPP | 2026-09-28 05:12 | 1,63 | 1,515 | 0,93 | 15,882 | 1,051 |
| Isluga | Suomi NPP | 2026-10-03 05:18 | 1,62 | 1,574 | 0,97 | 22,779 | 1,026 |
| Cordón Caulle | Suomi NPP | 2026-05-09 06:18 | 1,13 | 1,139 | 1,01 | 20,822 | 0,109 |

Tres cosas que un geólogo querría saber de estas 12:

1. **La tabla de MIROVA no lista ninguna de las 12 pasadas** (las 12 quedan `sin_info` con la tabla sola). Son alertas que
   sólo el OCR de la imagen leyó.
2. **El VRP de MIROVA es nuestra suma de todos los alertados** (cociente 0,78 a 1,03), que incluye el cúmulo lejano. Es
   decir, MIROVA también suma la fuente lejana; lo que el OCR afirma es la clase, no que el calor esté sólo en el cráter.
3. **La clase del OCR es dudosa en 10 de las 12** (A119, hitos de `scripts/calidad_referencia_mirova.py`): 8 son anteriores
   al 2026-06-13, cuando el OCR no medía la distancia (no se sabe si MIROVA ubicó el calor dentro del radio), y 2 son de
   Suomi NPP antes del 2026-10-09, cuando la distancia y la clase del OCR podían venir de otra pasada. Sólo 2 (Láscar
   2026-10-01 y Isluga 2026-06-17, ambas NOAA-21) tienen una clase de OCR leída en su propia imagen con distancia.

## 4. El costo, y por qué es el mismo canje que ya se rechazó

Las 114 publicaciones nuevas en `far_ref` son pasadas en que la tabla de MIROVA dice FALSO_POSITIVO lejano y nosotros
pasaríamos a publicar como cumbre: mediana 0,658 MW (0,192 a 11,685), 31 de ellas de 1 MW o más; el cúmulo más radiante
está a una mediana de 19,8 km (3,3 a 33,4) y hay de 1 a 10 alertados dentro del inner (mediana 2). Más 95 publicaciones
nuevas en pasadas que la tabla no lista (mediana 0,737 MW), de las que no se puede decir si son acierto o falsa alarma.

En estos datos la variante da lo mismo que S185 midió para «cercano» (cúmulo más cercano al cráter; D8', hasta el
2026-11-15): allá 9 alertas `pos` recuperadas de 1.664, 114 `far_ref` más, concordancia de 98,7 % a 93,6 % con la tabla y de
96,5 % a 93,5 % con tabla y OCR; aquí (hasta el 2026-11-18) 9 de 1.669, 114, de 98,73 % a 93,59 % y de 96,52 % a 93,53 %. Es
razonable: cuando hay un
alertado en el cráter, el cúmulo de la alertada más caliente del inner es casi siempre el cúmulo más cercano. Nicolás
eligió «radiante» el 2026-11-15 frente a este mismo canje, con el dato de que costaba 5 protegidas sólo OCR; el dato
corregido es 12, y 10 de esas 12 tienen la clase de MIROVA sin respaldo de distancia propia.

## 5. Si Nicolás la adopta: el cambio A45 (no implementado)

En `pipeline/mirova_v750_codigo.py`, `procesar_grilla`: antes de `cu = _cumulo_del_mas_radiante(mascara, m13g)`, calcular
la distancia al cráter (`pos_crater`, `paso_km`) de cada alertado; si alguno está a `inner_km` o menos, sembrar el cúmulo
8-conexo en el de mayor `m13g` entre ellos (una función hermana de `_cumulo_del_mas_radiante` con la semilla como
argumento); si no, como hoy. Vale para los tres sensores (los tres pasan por `procesar_grilla`). `vrp_mw`, la máscara y los
píxeles no cambian. Pide: tag defensivo y confirmación (A45); reemplazar `tests/test_guard_regla_posicion_radiante_s186.py`
(fija lo contrario) por una prueba con el caso débil en el cráter y fuerte lejos que exija `summit`; D8' y la ficha SDA
(fila al mergear); y reaplicar la posición a la historia publicada, que con este método no exige reprocesar gránulos
(sección 6, C1 a C3). En la práctica el cambio sólo mueve VIIRS 375.

## 6. Controles (preregistro §4)

| Control | Resultado |
|---|---|
| C1, «radiante» recalculado igual a lo guardado (clase y distancia del centroide a 0,001 km) | 3.697 de 3.697 records, 0 excepciones |
| C2, distancia de cada alertado desde `posicion_de` igual a `dist_km` guardado (0,006 km) | 11.548 de 11.548 |
| C3, publicación de node igual entre records originales y reescritos con «radiante» recalculado | 29.012 de 29.012 pasadas (ventana hasta el 2026-11-20) |
| C4, sintético débil en el cráter y fuerte a 15 km (Láscar, VIIRS 750) | «radiante» `far` a 15,147 km, no publica; variante `summit` a 0,306 km, publica |
| C5, protegidas no publicadas con un alertado dentro del inner, contra las 12 de Codex F12-V301 | 12 y 12, las mismas, ninguna de más ni de menos |

Empates de temperatura en la semilla (el orden por `bt_k` redondeado a 0,01 K reemplaza al orden por radiancia): 1 entre los
218 cambios, Isluga NOAA-21 2026-10-16 05:36, una `far_ref`; no mueve el veredicto (L3 sería 113).

## 7. Verificación independiente

Un subagente sin este razonamiento escribió su propio instrumento antes de abrir `medir_variante.py`
(`D:\vrp-trabajo\temporales\s193_radiante_variante_verif\verificar.py`, salidas `salida.txt` y `salida_verificador.json`,
fuera del repo). **Reproduce todos los números** de G1, L1, L2, L3 y L4 por lectura y sensor, las informativas (G2 9 y 40;
218 cambios, todos de no publicar a publicar; `sin_info` 95 y 61; `sin_geometria` 3) y los controles C1, C2, C3 y C5
(C4 con otro sintético: `far` y no publica, `summit` y publica). Su veredicto según §6: DECIDE NICOLÁS.

Diferencias de método que encontró, ninguna mueve un número:

- Desempate de la semilla: aquí por (temperatura, menor distancia), él por orden de lista y probando el segundo empatado:
  en los 6 empates de la variante el cúmulo y la clase salen iguales con cualquier desempate.
- Ancla del cráter: aquí `vent` o `lat`/`lon`, como el procesador; `get_detection_anchor` pasa además por `mirova_center`.
  No cambia nada porque los 11 tienen `vent` (y C2 reproduce las distancias).
- `t_max_k`: aquí se reescribe con el pico del cúmulo elegido, como haría producción (`procesar_grilla`); §3 no lo lista. No
  pesa: los filtros de artefacto térmico eximen a la vía, y para la vía el predicado lee sólo `distance_class`,
  `primary_cluster.centroid_dist_km` y `primary_cluster.vrp_mw`.
- `veredicto()` omite la cláusula «G1 tabla ≥ 0 sin L1 tabla» del corte 3; es redundante con el veto (L1 = 0).

## 8. Límites

- La referencia es el snapshot del repo con sus capas históricas (`cargar_referencia_unificada()` por defecto), no la
  bajada del día: el conteo puede moverse en una o dos pasadas si Mirova-v1 agregó filas.
- La «clase de MIROVA» de L4 sale de la etiqueta del scraper (`pos` = alerta dentro de su radio, `far_ref` = falso
  positivo lejano), que depende de la distancia de la tabla; no es la posición de MIROVA, que sigue SIN DATO en el NRT (D8').
- Las 95 publicaciones nuevas `sin_info` no tienen con qué juzgarse.
- No se midió ninguna otra variante (por ejemplo, exigir que el alertado del cráter supere un mínimo, o publicar la cumbre
  sólo con el VRP del cúmulo del cráter): elegir una después de ver estos números sería ajustar al resultado. Si interesa,
  va con su propio preregistro.
