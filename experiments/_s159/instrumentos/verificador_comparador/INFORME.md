# Verificador con contexto limpio del comparador D-28 en el evaluador de D25

Fecha: 2026-10-21. Objeto: `experiments/_s157_prereg_d25/evaluar_d25.py` en `b4258040c` (PR #890), contra la
especificación sellada `experiments/_s157_prereg_d25/ADENDA_PLACEBO.md` (D-28), que se apoya en
`ADENDA_CALIBRACION.md` (D-27). Diff revisado: `git diff 2629f5a16 b4258040c`.

**No se corrió el evaluador sobre V1, V2a ni V2b, no se bajó ningún artefacto de esos runs y no se leyó su
veredicto.** Todo lo medido aquí sale de los pares REALES de K solos (D = K transformado por una función conocida),
armados con la misma selección que `placebo_real.py`, y de los casos sintéticos de las pruebas. No se tocó ningún
archivo fuera de esta carpeta, no se hizo git.

Ventanas y denominadores (salida de `armar_pares.py`, idéntica a `placebo_real_salida.txt`):

| estrato | modo | V1 (2026-08-29 a 2026-10-18) | V2 (2026-04-01 a 2026-06-12) |
|---|---|---|---|
| VIIRS 750 z<=40 | decide | 29 pares, 27 noches (Chillán 13, PCC 8, Láscar 6, otros 2) | 64 pares, 64 noches (Láscar 41, Isluga 11, PCC 11, Tupungatito 1) |
| VIIRS 750 z>40 | decide | 23 (Chillán 19) | 27 (Láscar 24) |
| VIIRS 375 sin kernel z<=40 | decide | 103, 82 noches (Isluga 44, Láscar 23, Tupungatito 20, Chillán 16) | 108, 107 noches (Láscar 39, Isluga 36, Tupungatito 32, Copahue 1) |
| VIIRS 375 sin kernel z>40 | bloquea | 91 | 97 |

Dispersión de log10(K/MIROVA) en los estratos que deciden: 0,21 a 0,39 (desviación estándar); K sobre MIROVA en sólo
2 a 14 % de los pares. Los dos estratos de cenit sobre 40° no pueden dar MEJORA (uno tiene un solo volcán con 3 pares,
el otro sólo bloquea), así que **un CUMPLE depende enteramente de VIIRS 750 z<=40 y VIIRS 375 sin kernel z<=40, en las
dos ventanas.**

## Veredicto global: PARCIAL

**La implementación CONFIRMA**: hace lo que dice el §2 de D-28 punto por punto, ninguna ganancia uniforme ni por
volcán da MEJORA en 0 de 110 brazos sobre pares reales, EMPEORA sigue sobre d, la compuerta está retirada, el nulo de
la calibración de d′ está centrado. **Como instrumento queda PARCIAL** por tres cosas que no son errores del código:
(1) el comparador pierde casi todo el poder cuando el efecto de D varía de pasada en pasada en más de ~0,05 a 0,075
en log10, (2) la calibración de d′ con su semilla fija cae justo sobre el tope en V2 VIIRS 750 z<=40 y ahí apaga
MEJORA reales, y (3) dos piezas del §2.3 (opción A sobre d′ y calibración de d′) no tienen ninguna prueba que las
vigile.

## Hallazgos (de mayor a menor gravedad)

### H1. Con dispersión por pasada del efecto, el comparador deja al A/B casi sin poder

- SCRIPT:SALIDA `poder.py` -> `poder_salida.txt`; también `experimentos.py` (familia C2) -> `resumen.txt`.
- Instrumento. (1) Si el comparador no actuara, la columna «MEJORA por d» (sin comparador) y «MEJORA final» serían
  iguales; no lo son, así que lo que se ve es el comparador. (2) Control positivo: con ruido 0 el brazo da MEJORA en
  los cuatro estratos que pueden; control negativo: ganancia 1,3 con ruido (familia E) da MEJORA final 0 de 96 brazos.
- QUÉ PASA. Físicamente, el fondo por vecinos no cambia la magnitud en la misma proporción en todas las pasadas: depende
  de cuán fríos estén los vecinos respecto del anillo, que cambia con la nieve, la nube y la geometría. En el código,
  d′ compara a D contra la ganancia uniforme ĝ·K; cualquier dispersión de D/K que no esté correlacionada con la
  distancia a MIROVA hace crecer |log10(D/MIROVA)| en promedio, y eso se suma a d′ con signo positivo. Un mecanismo que
  sí acerca los pares correctos pierde contra el comparador en cuanto esa dispersión es comparable a lo que corrige.
  Medido con un brazo que lleva cada par una fracción alfa del camino hacia MIROVA en log, con ruido lognormal por par,
  12 semillas, tamaños reales:

  | alfa | sigma (log10) | proxy CUMPLE con comparador | proxy CUMPLE sólo con d (D-27) |
  |---|---|---|---|
  | 0,50 | 0,00 a 0,05 | 12 de 12 | 12 de 12 |
  | 0,50 | 0,075 | 7 de 12 | 12 de 12 |
  | 0,50 | 0,10 | 1 de 12 | 12 de 12 |
  | 0,50 | 0,15 | 0 de 12 | 12 de 12 |
  | 0,25 | 0,03 | 7 de 12 | 12 de 12 |
  | 0,25 | 0,05 | 3 de 12 | 12 de 12 |
  | 0,25 | 0,075 o más | 0 de 12 | 12 de 12 (7 de 12 con 0,15) |

  (proxy CUMPLE = MEJORA final en algún estrato de V1 y en alguno de V2 con la misma semilla, P1 y P2 dados por buenos.)
  Alfa 0,5 es un efecto grande (cierra la mitad de la brecha en log); sigma 0,10 es un factor de ±26 % por pasada,
  menos de la mitad de la dispersión que K ya tiene contra MIROVA.
- ¿Es plausible esa dispersión en D25? **SOSPECHA**, no medible sin los brazos del A/B. Lo único que hay es el probe del
  L1B de Chillán (`probe_l1b/README.md`, tabla «Qué hace D25 sobre la magnitud publicada»): en VIIRS 375 D25 dio
  ×1,082 a ×1,094 en cuatro pasadas, sin relación con la razón contra MIROVA (0,72 a 0,35), o sea casi una ganancia
  uniforme, que el comparador marcaría NEUTRO tal como D-28 quiere; en VIIRS 750 dio ×1,13 a ×1,14 en tres pasadas y
  ×2,16 en la oblicua con razón 0,12, o sea una ganancia que sí sigue al déficit pero con una sola pasada fuera de la
  nube. Entre volcanes, 1.14 midió ×1,72 en Isluga y ×2,37 en Tupungatito: esa diferencia actúa, dentro de un estrato,
  como dispersión del mismo orden que la de la tabla.
- CÓMO SE VE EN EL DASHBOARD. Invisible directamente. La consecuencia es de decisión: un D25 que sí acerca la magnitud
  a MIROVA puede salir SIN EFECTO, se lee como «D25 no sirve», no se adopta, y el operador sigue viendo VRP de VIIRS en
  0,52 a 0,66 veces lo de MIROVA en esos estratos.
- CÓMO REPRODUCIRLO. `python armar_pares.py <TMP>` y `python poder.py` en esta carpeta (unos 6 minutos con 8
  procesos).
- CONFIANZA. CONFIRMADO el poder medido; SOSPECHA que D25 real tenga esa dispersión.
- GRAVEDAD 4. Puede convertir una mejora real en SIN EFECTO en las dos ventanas. Lo grave no es que el comparador
  sea estricto (eso lo eligió Nicolás) sino que la curva de poder no está declarada: sin ella, un SIN EFECTO no
  distingue «D25 no acerca» de «D25 acerca con dispersión». Recomendación al coordinador: declararla en la adenda
  antes del tag de lectura, y que el evaluador informe la dispersión de log10(D/K) por estrato junto a ĝ.

### H2. La calibración de d′ con su semilla fija cae sobre el tope en V2 VIIRS 750 z<=40 y apaga MEJORA reales

- SCRIPT:SALIDA `nulo_dprima.py` -> `nulo_dprima_salida.txt`; `experimentos.py` -> `experimentos_salida.json`;
  `poder_salida.json`.
- Instrumento. (1) Si la calibración estuviera rota, la tasa media sobre 20 semillas se alejaría del 2,5 % nominal;
  no se aleja (2,6 % por cola). (2) Control positivo: con todos los d′ hacia MIROVA la regla da MEJORA (poder True en
  los seis casos).
- QUÉ PASA. En V2 VIIRS 750 z<=40 (64 pares, 41 de Láscar) la calibración de d′ con la semilla sellada
  (`SEMILLA_CALIB_DPRIMA = SEMILLA + 3`, `evaluar_d25.py:105`) da 11 falsos MEJORA de 200 (0,055) contra un tope de 10,
  en 10 de 66 brazos de ese estrato. Con 20 semillas distintas el mismo d′ falla en 1 de 20: es la cola binomial
  (P(>= 11 de 200 | 2,5 %) = 0,0126) fijada por la semilla, no un nulo descentrado. Como el §2.3 se implementó literal
  (d MEJORA, d′ no da MEJORA -> NEUTRO), en 1 brazo de `experimentos.py` (alfa 0,5, sigma 0,05, semilla 5: d MEJORA,
  d′ MEJORA, 3 volcanes con d′ negativa) y en hasta 14 de 488 de `poder.py`, todos en ese estrato, el MEJORA se apagó
  sólo por la calibración. En los otros estratos y en la calibración de d: 0 fallas en 416 brazos.
- CÓMO SE VE EN EL DASHBOARD. Invisible; afecta la decisión de adoptar D25 como H1.
- CÓMO REPRODUCIRLO. `python nulo_dprima.py` en esta carpeta.
- CONFIANZA. CONFIRMADO.
- GRAVEDAD 3. Es el estrato que más pesa en V2. Ver pregunta 5.1: la elección NEUTRO o INDECIDIBLE cambia qué pasa
  aquí.

### H3. Dos piezas del §2.3 de D-28 no tienen ninguna prueba

- SCRIPT:SALIDA `mutaciones_propias.py` -> `mutaciones_propias_salida.txt` (control sin mutar: 0 fallas).
- Instrumento. (1) Una mutación que no cambia ninguna prueba es justo lo que esta medición ve. (2) El corredor tiene
  control: la copia sin mutar da 0 fallas, y tres mutaciones sí quedan atrapadas por aserción (sin redondeo, ĝ con el
  signo invertido, ĝ media en vez de mediana), así que el corredor no está muerto.
- QUÉ PASA. Quedan **NO ATRAPADAS** por `tests/test_evaluar_d25_placebo_s159.py`:
  - retirar la opción A sobre d′ (`"dprima_da_mejora": bool(r_p == "MEJORA" and calibrada)`, sin los dos volcanes);
  - ignorar la calibración de d′ (`calibrada = True`): sobre pares reales cambia al menos el brazo de H2 de NEUTRO a
    MEJORA;
  - contar la opción A de d′ con d en vez de d′;
  - exigir sólo la cola MEJORA en la calibración de d′ (ésta es una alternativa legítima, ver 5.2, no un defecto).
  El código de hoy hace lo correcto (leído en `evaluar_d25.py:267` a `291`); lo que falta es la guarda: una edición
  futura puede borrar dos condiciones de la regla sellada sin que nada se ponga rojo.
- CÓMO SE VE EN EL DASHBOARD. Invisible hoy.
- CÓMO REPRODUCIRLO. `python mutaciones_propias.py` en esta carpeta (unos 15 minutos).
- CONFIANZA. CONFIRMADO.
- GRAVEDAD 2.

### H4. El control positivo (ii) depende de la dispersión de K, y la prueba vieja se reemplazó por eso

- SCRIPT:SALIDA `mitad_dispersion_salida.txt`.
- QUÉ PASA. Físicamente, si K quedara bajo MIROVA en la misma proporción en todas las pasadas, ningún mecanismo sería
  distinguible de una ganancia: los pares «que deben subir» serían todos por igual. El brazo a mitad de camino de la
  prueba unitaria da NEUTRO con dispersión de K de 0,03 y de 0,10, y MEJORA con 0,20 y 0,30. El implementador cambió
  la prueba de 0,03 a 0,3 y lo declaró en el PR. Con los pares reales (dispersión 0,21 a 0,39) el brazo determinista
  pasa en los cuatro estratos con alfa 0,5, pero **con alfa 0,25 queda NEUTRO en V2 VIIRS 375 sin kernel z<=40**
  (dispersión 0,21, la más baja), ya sin ruido.
- CÓMO SE VE EN EL DASHBOARD. Invisible.
- CONFIANZA. CONFIRMADO.
- GRAVEDAD 2. Es una propiedad de D-28, no un error; conviene que la adenda la diga.

### H5. Un D que corrige sólo los pares más lejos no puede dar MEJORA, pero el bloqueo es de d (D-27), no de d′

- SCRIPT:SALIDA `resumen.txt`, familia C3 (la mitad de los pares más lejos de MIROVA llevada a mitad de camino, el
  resto igual): MEJORA por d 0 de 6 estratos; la mediana de d cae en el borde porque la mitad de los pares no cambia.
- CONFIANZA. CONFIRMADO. GRAVEDAD 2. Límite de la mediana del D-27 sellado, fuera del cambio revisado.

### H6. Una ganancia que depende sólo de la magnitud de K no se pudo probar

- La correlación entre log10(K) y log10(K/MIROVA) es 0,31 a 0,84 en los estratos que deciden: los débiles son los
  que más se quedan cortos. Una ganancia mayor para los píxeles débiles, sin ninguna información de MIROVA, podría
  pasar d′ por esa correlación. Con beta 0,2 y 0,4 (familia D) la regla sobre d ya no da MEJORA, así que el comparador
  nunca se ejercitó. SOSPECHA, GRAVEDAD 1.

### H7. El redondeo a 1e-12 no se mostró necesario en 6 casos, pero el riesgo existe

- SCRIPT:SALIDA `redondeo_salida.txt`. Sin redondeo, los 6 placebos (2 sintéticos, 4 reales) siguen NEUTRO, con
  extremos del intervalo de d′ como -2,8e-17 y 0,0: a un ulp de dar «entero bajo 0». El redondeo no puede ocultar
  ningún efecto físico (1e-12 en log10). CONFIRMADO, GRAVEDAD 1, no requiere cambio.

Nota de mi instrumento: en `mutaciones_propias_salida.txt` aparece un `UnicodeDecodeError` en un hilo lector de
`subprocess` (salida de pytest en cp1252). No afecta la clasificación, que se lee del JUnit XML.

## Respuestas por pregunta

1. **¿Hace lo del §2 punto por punto? CONFIRMA.** ĝ = mediana de log10(D/K) (`evaluar_d25.py:267`); d′ =
   |log10(D/M)| − |log10(ĝK/M)| (l. 268); ĝ recalculado por réplica con los mismos pesos W que la mediana de d′
   (l. 270 a 272); calibración simétrica de d′ con ĝ fijo, tope por cola (l. 275 y 276); opción A sobre d′ (l. 278 a
   281); MEJORA exige las dos (l. 291 y 432 a 438). EMPEORA sigue sobre d: el comparador sólo reescribe MEJORA a
   NEUTRO (l. 434 y 435); con pares reales K×0,8 da EMPEORA en los 4 estratos de V1 y V2. La compuerta se retiró de
   `evaluar_m` y de `global_ventana` (diff), y el placebo K×1,2 y K×0,8 sigue informado sin comparador.
2. **Ganancia uniforme y por volcán: CONFIRMA.** Sobre pares reales: g = 0,5; 0,8; 1,2; 1,5; 2; 3 y g* (la que centra
   la mediana de K en MIROVA, ×1,52 a ×2,83 según estrato), en los 4 estratos que deciden o bloquean de cada ventana:
   MEJORA final 0 de 56, aunque d sola da MEJORA en 34 de ellos.
   Ganancia por volcán, uniforme dentro de cada uno: la que centra cada volcán en MIROVA (el peor caso del límite
   declarado en el §3) y 8 sorteos en [1,2; 3,0]: MEJORA final 0 de 54, d′ MEJORA 0 de 54. El límite del §3 no se
   materializó en estas configuraciones.
3. **Poder con los tamaños reales: PARCIAL.** Mecanismo limpio (mitad de camino sin ruido, o con ruido de 0,05 o
   menos): MEJORA en los dos estratos que pueden, en las dos ventanas. Con ruido por pasada de 0,10 el proxy de CUMPLE
   cae a 1 de 12, y con alfa 0,25 desde 0,075 a 0 de 12 (H1). «Sólo los pares más lejos» no puede dar MEJORA, pero
   por d (H5).
4. **Nulo de la calibración de d′: CONFIRMA.** Centrado: media de las medianas nulas +0,0003 con error 0,0005 (V2
   VIIRS 750 z<=40) y dentro de un error estándar en los seis casos medidos; tasas medias por cola 2,4 a 3,0 % sobre
   20 semillas. El tope por cola se aplica tal cual (l. 276). Matiz: el nulo **realista** (ganancia más ruido, sin
   información de MIROVA) no está centrado para d′, sino corrido hacia EMPEORA (+0,009 a +0,054 de mediana en la
   familia E). Eso protege contra falsos MEJORA (0 de 96) y es el mismo mecanismo que quita poder en H1.
5. **Las cinco preguntas del PR.**
   - 5.1 NEUTRO o INDECIDIBLE si falla la calibración de d′. Consecuencia medida: el caso ocurre sólo en V2 VIIRS 750
     z<=40, por la cola binomial con semilla fija (H2). NEUTRO (lo implementado) apaga ese MEJORA pero deja que VIIRS
     375 z<=40 de V2 dé MEJORA solo; INDECIDIBLE deja **toda la ventana V2** INDECIDIBLE (`global_ventana` l. 576), y
     con eso el combinado no puede dar CUMPLE. Lo coherente con D-27 es INDECIDIBLE: en D-27 un estrato con
     calibración fallida no decide, y aquí d′ es condición necesaria del MEJORA, así que no se sabe si hay MEJORA. Lo
     literal del §2.3 es NEUTRO. Cualquiera de las dos, conviene que la adenda lo diga, y bajar el riesgo de que una
     semilla decida (más repeticiones de calibración, por ejemplo 1.000, reduce la cola binomial al borde).
   - 5.2 Una o dos colas. Consecuencia medida: ninguna en estos datos; la cola EMPEORA de d′ nunca pasó de 0,03 en 416
     brazos (0,06 una vez en 120 corridas con semillas alternativas). Lo coherente con D-27 (en el estrato que sólo
     bloquea se exige sólo la cola que puede decidir) es exigir sólo la cola MEJORA, porque d′ sólo se usa para
     MEJORA. Exigir las dos es más estricto sin ganancia.
   - 5.3 El caso `sellada`. La lectura del implementador es la coherente: D-27 §1 llama «el caso `sellada`» al brazo a
     mitad de camino, y el caso de `probar_evaluar_d25.py` con ese nombre corre con la calibración anterior a D-27,
     donde da INDECIDIBLE por diseño (lo dice `probar_evaluar_d25_salida_comparador.txt`). El control (ii) lo cumplen
     `mejora750` (MEJORA) y la prueba unitaria con dispersión 0,3, con la salvedad de H4.
   - 5.4 Comparador apagado con `--calibracion sellada`. Consecuencia: ese modo aprobaría un placebo. Riesgo bajo: el
     defecto es `simetrica` (`evaluar_d25.py:863`) y el evaluador imprime qué modo usa. Coherente con D-28, que se
     escribió sobre D-27. Sugerencia mínima: que el JSON de salida marque ese veredicto como no válido para decidir.
   - 5.5 Detalles numéricos. Redondeo 1e-12: inocuo y prudente (H7). Semilla propia de d′: no cambia el centrado; sí
     fija en qué lado del tope cae V2 VIIRS 750 z<=40 (H2), por lo que el valor de la semilla importa en el borde y
     debería sellarse antes del tag, no elegirse después. ĝ puntual sin pesos: es la mediana por par, el mismo
     estimador que centra el bootstrap por bloques (que pesa por par según cuántas veces sale su bloque); no medí una
     alternativa ponderada por noche.
6. **¿Mutaciones y pruebas fallan por aserción y por la razón que dicen? CONFIRMA para las cuatro requeridas, con el
   hueco de H3.** El corredor del implementador lee el tipo de falla del JUnit XML y tiene control sin mutar
   (`mutar_comparador.py`, leído; su salida `comparador_mutaciones.txt`, leída, no re-ejecutada). Mi corredor, con el
   mismo método, reproduce el control en 0 fallas sobre `b4258040c` y atrapa por aserción tres mutaciones propias.
   Las pruebas tienen guarda de poder (`test_placebo_como_brazo_no_puede_dar_mejora` exige que d sola apruebe el
   placebo antes de exigir que el comparador lo bloquee). Debilidad menor: en `probar_evaluar_d25.py`,
   `.get("dprima_max_abs", 0.0)` pasa en vacío si el comparador falta; lo cubre la condición «ningún MEJORA» porque
   la regla sobre d sí da MEJORA en esa ventana.

## VERIFICADO LIMPIO

- Pares reales de K idénticos a los del implementador: `python armar_pares.py <TMP>` da 29/23/103/91 (V1) y
  64/27/108/97 (V2), igual que `placebo_real_salida.txt`.
- Ninguna ganancia uniforme da MEJORA (0 de 56) ni ganancia por volcán (0 de 54): `python experimentos.py` y
  `python resumir.py`, familias A, B1 y B2 en `resumen.txt`.
- Nulo con ruido sin información de MIROVA no da MEJORA: familia E, 0 de 96 en estratos que deciden.
- EMPEORA sigue sobre d y K×0,8 da EMPEORA en los 4 estratos de V1 y V2 (familia A, g = 0,8).
- La compuerta no existe: `grep -n "PLACEBO\"\|INVALIDO: " experiments/_s157_prereg_d25/evaluar_d25.py` sólo
  encuentra el orden de estados y textos; `global_ventana` (l. 563 a 595) no lee ningún placebo.
- El nulo de la calibración de d′ está centrado y en la tasa nominal: `python nulo_dprima.py`.
- `medianas_ponderadas_filas` coincide con `medianas_ponderadas` (prueba `test_medianas_por_fila_coinciden...`,
  verde en el control de `mutaciones_propias.py`).
- Las 15 pruebas de `tests/test_evaluar_d25_placebo_s159.py` pasan sobre la copia sin mutar (control de
  `mutaciones_propias.py`, 0 fallas).
- La calibración de d (D-27) no falló en ninguno de los 416 brazos de `experimentos.py`.
- El defecto del CLI es la calibración simétrica: `evaluar_d25.py:863`.

## Archivos de esta verificación

Todos en `C:\vrp-trabajo\s159-evaluador\experiments\_s159\instrumentos\verificador_comparador\`: `armar_pares.py`,
`pares_k.json`, `experimentos.py`, `experimentos_salida.json`, `experimentos_salida.txt`, `resumir.py`,
`resumen.txt`, `poder.py`, `poder_salida.json`, `poder_salida.txt`, `nulo_dprima.py`, `nulo_dprima_salida.txt`,
`mutaciones_propias.py`, `mutaciones_propias_salida.txt`, `redondeo.py`, `redondeo_salida.txt`, `mitad_dispersion.py`,
`mitad_dispersion_salida.txt`.
