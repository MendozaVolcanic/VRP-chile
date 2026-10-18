# Verificador con contexto limpio: A/B diurno de VIIRS (D-10, issue #813), W2 a W6

Fecha: 2026-10-18. Rama `loop/activo`, sin checkout ni commits. Sólo se escribió en esta carpeta.

## Veredicto: PARCIAL

**El NO ADOPTAR se sostiene para el detector C0 con que corrió el A/B.** Re-corrido el evaluador dos veces
(con y sin `--repetidas`), con un pareo propio y con el nulo calculado en forma exacta, el resultado no se
mueve: G3 CUMPLE, G1 FALLA en W2 a W6 con holgura, G2 FALLA en los dos sensores por dos órdenes de magnitud.

**Pero no se puede trasladar a K**, el detector de producción desde el 2026-10-18. La mitad de las
publicaciones diurnas, y la mitad de las alertas diurnas que el brazo recupera, salen sólo del Test 1
integrado, que K apagó. Sin ellas, G1 cambia de comportamiento (ver H4). Hay que repetir el A/B sobre K.
Lo más probable, por proyección, es que G2 siga fallando sobre K. El veredicto pasaría entonces de NO ADOPTAR
a «DECIDE NICOLÁS CON M4» si G1 cumple, o seguiría en NO ADOPTAR si no cumple. Eso no se puede decidir
sin correr el A/B.

El fenómeno, en una frase: de día el Sol calienta y refleja sobre todo el disco de 3 km del cráter, el Test 1
(que suma el infrarrojo medio absoluto de ese disco) dispara casi siempre (en 2.000 de las 2.077 publicaciones
de VIIRS 375 en negativos limpios), y eso satura la publicación igual que de noche. El brazo diurno publica
en el 89,3 % de los negativos diurnos limpios de VIIRS 375; el control, de noche, publica en el 88,8 %. Es la
misma banda de saturación (A114). Lo que este A/B midió es sobre todo el Test 1 de día, no la Tabla 1 diurna.

## Comandos y salidas (todo corrido en esta sesión)

Raíces: `C:\Users\nmend\AppData\Local\Temp\claude\diurno_eval\W2a` a `W6b` (10). Repo:
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile`.

| qué | comando | salida |
|---|---|---|
| re-evaluación, igual que el agente | `python -I experiments/_s151_ab_diurno/evaluar_diurno.py --raiz <W2a> ... --raiz <W6b> --repetidas W2,W3,W5,W6 --out .../verificador/reeval_resultado.json` | `reeval_salida.txt`, `reeval_resultado.json` |
| re-evaluación sin `--repetidas` | ídem sin `--repetidas` | `reeval_sin_repetidas_salida.txt` |
| commit de cada record por raíz | `python -I verificador/v1_shas_y_raices.py <diurno_eval>` | `v1_salida.txt` |
| fuentes, contrafactual, nulo exacto, pareo propio | `python -I verificador/v2_fuentes_y_nulo.py <10 raíces>` | `v2_salida.txt` |
| commit por volcán en las raíces unidas | `python -I verificador/v3_por_volcan.py <diurno_eval> W3a W5a W6a` | `v3_salida.txt` |
| cobertura nocturna por raíz | `python -I experiments/_s151_ab_diurno/contar_pasadas_noche.py --control ... --brazo ... --inicio ... --fin ...` (10 veces) | `cobertura_noche_salida.txt` |
| proyección a K | `python -I -c "print(2236*37/863, 766*20/398, 1142*37/863, 357*20/398)"` | `proyeccion_k.txt` |
| diferencias de código | `git diff --stat <sha_i> <sha_j> -- pipeline/ frontend/index.html scripts/run_pipeline.py .github/workflows/reproc-s151-ab-diurno.yml volcanoes.yaml` y `git diff 087e53bfa2 origin/main -- pipeline/profiles/mirova_equivalent.yaml` | en el texto de H5 y H4 |

Cifras centrales reproducidas (de `reeval_salida.txt`): G3 9.762 pares nocturnos, 0 `distinto`; G1 W2 a W6
M1 78,1 % (25/32), q_neg 60,0 % (2.808/4.683), D = +0,1816; G1 W3 a W6 D = +0,2303 contra p95 +0,2303;
G2 VIIRS 375 2.236 de 2.511 (falla desde 20), VIIRS 750 766 de 2.466 (falla desde 6); veredicto
NO ADOPTAR, igual en SN y SE.

## Hallazgos

### H4. El NO ADOPTAR no se traslada a K: la mitad de lo publicado de día es sólo Test 1

- Dónde: los records del brazo diurno (`final_hotspot_source`, `triggered_test1`), y
  `pipeline/anchor.py:83-91` en el commit 087e53bfa2: `ctx_cluster` quiere decir que hay cúmulo contextual de
  los Tests 2 y 3; `test1_roi` quiere decir que no lo hay (o está lejos con el Test 1 en el cráter) y la
  posición sale sólo del Test 1.
- Qué pasa (`v2_salida.txt` §2): de las publicaciones diurnas en negativos limpios, VIIRS 375 tiene 987
  `test1_roi` y 1.090 `ctx_cluster` (de 2.077), con `triggered_test1` en 2.000; VIIRS 750 tiene 389 y 342
  (de 731). De las 22 alertas protegidas VIIRS 375 recuperadas, 11 son `test1_roi`, entre ellas las 8 de W2
  (Láscar y Lastarria, sólo OCR) y las 2 de Isluga. Por ventana, positivos publicados por cúmulo contextual:
  W2 0 de 8, W3 0 de 1, W4 4 de 5, W5 3 de 4, W6 7 de 7.
- Qué cambia K para VIIRS (`git diff 087e53bfa2 origin/main`): `enable_test1_path: false` y
  `enable_tests_23_prose_branch: true` (conectiva `max`). El resto de las diferencias en `pipeline/*.py` es el
  desempate estable `orden_vrp_descendente` y comentarios. Nada más toca VIIRS.
- Contrafactual «sin Test 1» (`v2_salida.txt` §3 y §4; sólo cuentan como publicadas las `ctx_cluster`):
  M1 14/32, q_neg 1.432/4.683. G1 W2 a W6: D +0,132 contra cuantil 95 exacto +0,195, **FALLA**. G1 W3 a W6:
  D +0,369, P(nulo ≥ D) = 0,001, **CUMPLE**. G2 sigue fallando: VIIRS 375 1.142 de 2.511 (umbral 20), VIIRS 750
  357 de 2.466 (umbral 6).
- Límite del contrafactual: no aplica la conectiva `max`, que de noche fue la palanca mayor. De noche, el
  control C0 publica en negativos limpios de VIIRS 375 con 747 `test1_roi` y 623 `ctx_cluster` (de 1.370,
  `v2_salida.txt` §5), o sea que sacar el Test 1 solo quitaría el 55 %. Pero según `experiments/_s153_fk_v2/v2.log`
  (l. 147 a 150; **leído, no reproducido en esta sesión**) K bajó esa publicación de 863 a 37 de 1.010 (VIIRS
  375) y de 398 a 20 de 1.829 (VIIRS 750). Si de día K quitara lo mismo, G2 quedaría en unas 96 publicaciones
  en VIIRS 375 y 38 en VIIRS 750 (`proyeccion_k.txt`), todavía sobre los umbrales 20 y 6. **SOSPECHA**: la
  proyección supone que de día `max` corta en la misma proporción que de noche, y de día C1 = 0,02 y C2 = 15.
- Consecuencia: sobre K, G2 probablemente falla igual, y G1 queda indeterminado: con q_neg mucho más bajo
  podría cumplir, porque las alertas fuertes de W4 a W6 (Villarrica 1,3 a 1,8 MW, Nevados de Chillán 0,7 a
  6,4 MW) tienen cientos de píxeles del primer pase. Pero las 12 de W2 dependen del Test 1. Si G1 cumple
  sobre K, el veredicto pre-registrado es «DECIDE NICOLÁS CON M4», no NO ADOPTAR.
- Reproducir: `v2_fuentes_y_nulo.py`, secciones 2, 3 y 5.
- Confianza: alta en la descomposición; media en la proyección. **Gravedad 4** (decide si el resultado sirve
  para producción).

### H1. El aviso de saturación A114 mira q_neg de los dos sensores juntos y no vio la saturación de VIIRS 375

- Dónde: `experiments/_s151_ab_diurno/evaluar_diurno.py:940` (`if r1["q_neg"] >= BANDA_SATURACION`, sobre el
  G1 de W2 a W6 con los dos sensores juntos).
- Qué pasa: el q_neg conjunto es 60,0 %, bajo 0,80, así que el aviso no sale. Por sensor, VIIRS 375 da 89,3 %
  (2.077/2.325), dentro de la banda 80 a 92 %. El pre-registro §5.6 dice que si q_neg sale cerca de 1 por el
  Test 1, «el A/B no puede decidir nada sobre la Tabla 1 diurna y lo dice». El evaluador no lo dijo.
- Cómo se ve: `reeval_salida.txt` §6 (fila «W2 a W6 VIIRS375») contra §11 (sin línea de SATURACIÓN).
- No cambia el veredicto. Cambia lo que se puede concluir: el A/B no midió la Tabla 1 diurna en VIIRS 375.
- Confianza alta. **Gravedad 3**.

### H2. El percentil 95 del nulo cambia de un proceso a otro con la misma semilla

- Dónde: `evaluar_diurno.py:635` (`for k in UW[w]["pos"] | UW[w]["tabla"]`, iteración de un conjunto de
  tuplas de strings, cuyo orden depende de la semilla de hash del proceso) y `:485-511` (el nulo reparte los
  sorteos por estrato en ese orden).
- Cómo se ve: p95 de G1 W2 a W6 = +0,2446 en la salida guardada y en `reeval_sin_repetidas_salida.txt`,
  +0,2760 en `reeval_salida.txt`; el control del nulo da 0,012/0,011, 0,057/0,046 y 0,009/0,012. El cuantil 95
  exacto (`v2_salida.txt` §4) es +0,2760. `python -I` ignora `PYTHONHASHSEED`, así que la variación es
  inevitable con el comando del pre-registro.
- No cambia el veredicto: el D observado (+0,1816) cae en la mediana del nulo; P(nulo ≥ D) exacta = 0,52.
  Es la misma familia que el defecto del caso 3 de la autoprueba que el pre-registro (§11) ya arregló.
- Confianza alta. **Gravedad 2**.

### H3. «Sin W2 también falla» es un empate

- Dónde: `evaluar_diurno.py:539` (`d > p95 + EPS_D`).
- Qué pasa: en W3 a W6 el D observado (+0,2303) es exactamente el cuantil 95 exacto. P(nulo ≥ D) = 0,106 y
  P(nulo > D) = 0,025 (`v2_salida.txt` §4). Con la regla estricta del pre-registro falla, y así está bien; pero
  es un borde, no una falla holgada. No pesa en la decisión porque §6 decide primero por W2 a W6.
- Confianza alta. **Gravedad 2**.

### H5. W5a mezcla dos intentos y la cobertura del cableado por log no cubre tres de sus jobs

- Dónde: raíz `W5a` (`v1_salida.txt`, `v3_salida.txt`).
- Qué pasa: Llaima y Nevados de Chillán (los dos brazos) y el brazo diurno de Planchón Peteroa vienen del
  commit eb97779f4 (intento 2); el resto, del 7b825ba04 (intento 1). El par de Planchón Peteroa cruza intentos.
  Los logs son del intento 1, así que la revisión de `FLAGS_BRAZO` y de las compuertas cerradas de esos tres
  jobs mira un log que no es el del job que escribió los records.
- Por qué no pesa: `git diff` entre los siete commits de las raíces (8b2bcd796, 1a6f595b4, 5d05036b3, 9fd82f269,
  7b825ba04, eb97779f4, 087e53bfa) en `pipeline/`, `frontend/index.html`, `scripts/run_pipeline.py`, el workflow y
  `volcanoes.yaml` sale vacío. Los records diurnos de esos volcanes traen `diag_umbrales_diurnos` (88, 87 y 86) y
  `regimen.perfil` correcto. G3 da 0 `distinto`.
- Confianza alta. **Gravedad 1**.

## Las dos preguntas del instrumento

1. **Si lo medido estuviera roto, ¿el evaluador lo vería?** En cableado, cobertura y referencia, sí: el nulo 1
   por sensor, el G3 por par, las huellas de `sustrato.json` y el control del índice responden, y la autoprueba
   con mutaciones existe. Hay un punto ciego: la saturación por sensor (H1). Un brazo que publica casi todo en
   VIIRS 375 y poco en VIIRS 750 promedia bajo 0,80 y no dispara el aviso. Ese era justo el riesgo que el
   pre-registro escribió en §1.
2. **Si el evaluador estuviera muerto, ¿el resultado se vería distinto?** Sí. Un pareo escrito aparte da
   0 estados distintos sobre 5.018 pasadas. El nulo exacto, sin muestreo, deja el D de W2 a W6 en la mediana
   (P = 0,52), y G2 se reproduce contando a mano. El resultado no depende del código del evaluador; sólo el
   p95 muestreado varía (H2).

## VERIFICADO LIMPIO

- Re-ejecución: los mismos números en todo, salvo el p95 muestreado y el texto del control del nulo (H2).
  Veredicto idéntico, también bajo SN y SE.
- `--repetidas W2,W3,W5,W6` no hace nada: ninguna ventana tiene más de 10 % sin procesar (positivos 0 de 32;
  peor tabla VIIRS 750 de W5, 7 de 549). Sin el argumento, el veredicto es el mismo.
- Cobertura nocturna pareja en las 10 raíces (faltan 0, sobran 0); el control no tiene día; el brazo diurno
  trae VIIRS 375 y 750 diurnos y nada de MODIS diurno.
- Las medias ventanas no se pisan y cubren exacto las ventanas del pre-registro (W2a 06-13 a 06-21, W2b 06-22 a
  06-30, y así hasta W6b 10-08 a 10-14). La unión entre raíces no tiene claves repetidas (0/0).
- Código homogéneo entre los siete commits (H5). Todo es C0: `ENABLE_TEST1_PATH True`,
  `ENABLE_TESTS_23_PROSE_BRANCH False`, `ENABLE_MODIS_B22_PRIMARY False` en `FLAGS_BRAZO`.
- Referencia: reproduce `sustrato.json` con identidad de positivos (lista completa) y huellas de negativos,
  tabla y alertas. El OCR que se leyó no es el del pre-registro (sha256 ec890166 contra a2e8cb67), pero las
  poblaciones derivadas son idénticas, así que no pesa.
- G2 cuenta lo que el pre-registro dice: todas las pasadas VIIRS diurnas de la tabla, procesadas (2.511 y 2.466),
  con p_MIROVA fijo 13/2.511 y 2/2.483.
- Denominadores: 32 positivos en W2 a W6 (37 menos los 5 de W1), todos procesados; negativos 2.325 y 2.358
  procesados.
