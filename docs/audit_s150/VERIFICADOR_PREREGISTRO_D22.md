# Verificador con contexto limpio: pre-registro S150 del A/B de la conectiva `max` sin la compuerta D22

> Objeto verificado: `experiments/_s150_ab_d22/PREREGISTRO.md` en `origin/s150-ab-d22`, commit `5c9ccee1c`.
> Leído con `git show`, sin checkout. Extracciones con `git archive` CON RUTA a un temporal fuera del repo
> (scratchpad de la sesión). No se modificó nada del repo salvo este informe; no se despachó nada.
> Fecha: 2026-10-09.

## Veredicto

**No despachar tal cual. Despachable tras cambios menores a moderados, todos en el pre-registro y en los
scripts de lectura; ninguno toca `pipeline/`.** El brazo está bien armado (el perfil difiere del control en
una sola cosa, verificado) y la pregunta es legítima, pero (a) lo que el A/B mide no es exactamente lo que el
pre-registro dice que mide (H1), (b) dos de sus reglas de decisión no las implementa ningún script (H2), (c) el
control de determinismo no puede ver ruido del tamaño del efecto que se busca (H3), y (d) P1 y P2 están casi
condenadas a excluirse si se cumple lo que la propia investigación midió, cosa que conviene escribir antes de
mirar (H4).

## Lo que sí se verificó y está bien

1. **Perfil.** Resolví los dos perfiles desde el árbol de la rama, como los resuelve el código (subproceso con
   `VRP_PROFILE`, A89): `_s147_ab_sin_test1_max` y `_s150_max_sin_d22` difieren en `DATA_SUBDIR`,
   `PROFILE_NAME` y `ENABLE_TESTS_23_NO_BT_GATE_VIIRS375` (False a True), 143 atributos. Reproduce
   `diff_perfiles_d22_salida.txt`. Además, en los dos: `ENABLE_TEST1_PATH False`, `PROSE_BRANCH True`,
   `SECOND_PASS_CONDITIONED False`, `ETI_QUADRATIC_SCENE False`, `FINAL_PIXEL_FILTER False`,
   `NTI_RELATIVE_PATH False`, `NTI_BT_SANITY_K 3.0`.
2. **Alcance por sensor.** El flag sólo se lee en `pipeline/process_viirs.py` (I-band); VIIRS 750 va por
   `process_viirs_mod.py` (`scripts/run_pipeline.py:278` y `:325`) y MODIS por `process_modis.py`, que no lo
   importan. Sólo VIIRS 375: correcto.
3. **Código del detector entre los runs viejos y la rama.** `gh run view` da como `headSha` de los runs
   35639417826 `d46b7ec59`, 37823348991 `327621e2c`, 35599902448 `0227dd7ac`, 35675490175 `bbd2f8385`,
   35728617326 `1c59ec255` y 35759688167 `c825d9491`. `git diff <sha> origin/s150-ab-d22 -- pipeline/` da en
   los seis lo mismo: perfiles nuevos `_s150_*` y `store.py` (+18 líneas, `first_processed_utc`, descriptivo,
   sólo en `append_record`). Fuera de `pipeline/` cambiaron `scripts/auto_audit_weekly.py`,
   `scripts/nrt_monitor_decision.js`, `scripts/rebuild_mirova_from_consolidado.py` (ninguno lo usa el reproceso)
   y el workflow (runner fijado a `ubuntu-24.04`, línea `FLAGS_BRAZO`, `tee -a`). La afirmación del §2 es
   cierta **para el código**; ver H9 para el entorno.
4. **Referencias congeladas.** Los diez CSV de `_congelado/<mes>/` (sólo locales, no están en git) coinciden con
   el sha256 de su `MANIFIESTO.json`. Salvedad: la referencia unificada lee además
   `data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado_respaldo_20260408.csv`, que no está en la
   carpeta congelada; es estático (un solo commit, `068773fa8`), así que no rompe nada, pero el pre-registro
   debería nombrarlo como insumo.
5. **El nulo de `recuperacion_d22.py` se reproduce.** Reconstruí las tablas de los cinco meses con
   `armar_tabla.py` (F viejo contra sí mismo, referencias congeladas): 14 de 14 y 22 de 22 claves en las tablas,
   F2 publica 0. Idéntico a `recuperacion_d22_prueba_salida.txt`.

## Hallazgos

### H1. El A/B no aísla la compuerta: para estas pasadas mide el sigma del primer pase contra el del segundo (D22 junto con D26). Gravedad 3

**El fenómeno.** En las 14 pérdidas del camino D22 el brazo B no tuvo **ni un píxel** del primer pase en toda la
escena (`diag_n_first_pass_pixels = 0` en las 14, `filas.json`). Entonces, en F, el segundo pase corre con la
máscara de activos vacía, y con máscara vacía la media de los 8 vecinos es la misma del primer pase: el dNTI y
el dETI del píxel son **idénticos** en los dos pases. Lo único que cambia entre "el primer pase de F2 sin
compuerta" y "el segundo pase de F" es el umbral: `max(C1, mu1 + 5 sd1)` con el pozo de fondo del primer pase
(sin borde, sin dNTI o dETI bajo -0,1; `detection_context.py:492-510`) contra `max(C1, mu2 + 5 sd2)` con el pozo
del segundo pase, que no aplica esos filtros (`detection_context.py:922-929`, D26).

**Consecuencia.** F2 recupera uno de esos píxeles si y sólo si su dNTI y su dETI caen entre los dos umbrales,
o sea si `sd2 > sd1` lo bastante. Un brazo "F más los filtros de no aptos en el segundo pase" (D26) recuperaría
esos mismos 12 píxeles **con la compuerta puesta**. El texto del pre-registro ("si falla: la compuerta no es la
causa") está bien en esa dirección, pero si P1 se cumple **no** se puede concluir que la compuerta es la causa:
la causa es la conjunción de D22 con D26. Las dos son divergencias literales, así que el resultado sigue siendo
útil, pero la atribución no.

**Además, 2 de las 14 no son recuperables por esta vía.** En Isluga 2026-04-14 06:00 y Tupungatito 2026-08-21
06:30, F ya detecta un píxel cerca del cráter (1,0 y 0,2 km, por el segundo pase) con `pc.vrp_mw = 0,0`: lo que
las apaga es la magnitud nula (recorte del exceso, D25), no el test. El techo realista de P1 es 12, y 7 de 14 es
en la práctica 7 de 12.

**Corrección propuesta.** (a) Escribir la salvedad en el §1 y en el "si falla/si se cumple" de P1. (b) Para las
14, informar por etapa (A75, A118 b): `diag_n_first_pass_pixels`, `diag_n_second_pass_recapture`,
`n_anomalous_pixels`, distancia y magnitud del cúmulo en F y en F2, para separar "el test no pasa" de "pasa pero
la magnitud es cero". (c) Declarar el techo de 12. (d) Si se quiere separar D22 de D26, el brazo que falta es
F + D26, que hoy no tiene flag (requiere código, A45); como mínimo, dejarlo escrito como lo que el A/B no puede
distinguir.

### H2. Las reglas de P2 y P4 no las implementa ningún script, y el evaluador imprime veredictos con otras reglas. Gravedad 3

El pre-registro dice que P2 a P4 salen de `medir_predicciones.py`. Ese script tiene sus umbrales fijos
(`UMBRAL_P1, UMBRAL_P2, MIN_ZONA, FRAC_P4, MW_P4 = 0.18, 1.3, 10, (118, 141), 0.5`):

- **P2 del pre-registro** ("F2 ≤ F + 3 puntos en cada mes y ≤ 18 %"): el script sólo evalúa "brazo ≤ 18 %" y,
  como el control F publica entre 1,5 y 3,7 % de los negativos limpios, imprimirá **"INDECIDIBLE: el control ya
  publica 18 % o menos"** en los cinco meses. La comparación contra F + 3 puntos no la calcula nadie. Además el
  "≤ 18 %" no puede atar nunca: F + 3 ≤ 6,7 % en el peor mes.
- **P4 del pre-registro** ("≥ 98 % de lo que F publica, ninguna de 1 MW o más"): el script usa
  `ceil(n x 118/141)` (≈ 84 %) y 0,5 MW, e imprimirá CUMPLE o FALLA con esa vara.
- **Numeración cruzada**: la P1 del script es la P2 del pre-registro, la P2 del script es la P3, la P5 del
  script (pasadas con VRP 0 en noche con alerta) no tiene nada que ver con la P5 del pre-registro. Quien lea la
  salida sin el pre-registro al lado va a leer veredictos que no son los pre-registrados.
- **A119 en P4**: abril y mayo empiezan antes del 2026-06-13; el pre-registro no dice si P4 decide con la tabla
  sola (como hizo S149) o con tabla y OCR.

**Corrección.** Un script de lectura propio (o un modo de `medir_predicciones.py` con parámetros) que imprima P2
como `tasa_F2 - tasa_F` en puntos por mes y P4 con 98 % y 1 MW, con la etiqueta que decide según A119; y una
frase en el §5: "las líneas CUMPLE/FALLA/INDECIDIBLE de `medir_predicciones.py` no son las de este
pre-registro".

### H3. El control de determinismo no puede ver ruido del tamaño del efecto, y P1 no exige que el F nuevo calle. Gravedad 3

"Misma decisión de publicar en 98 de cada 100 pasadas" se cumple casi por construcción, porque la mayoría de
las pasadas no publica en ningún brazo. Contado sobre las tablas de F viejo (por mes, pasadas / publicadas por
F / cambios que tolera el 2 %):

| mes | MODIS | VIIRS 375 | VIIRS 750 |
|---|---|---|---|
| abril | 696 / 1 / 13 | 1.375 / 361 / 27 | 1.362 / 80 / 27 |
| mayo | 733 / 0 / 14 | 1.478 / 450 / 29 | 1.471 / 90 / 29 |
| junio | 740 / 0 / 14 | 1.395 / 330 / 27 | 1.385 / 67 / 27 |
| julio | 761 / 1 / 15 | 1.374 / 247 / 27 | 1.362 / 38 / 27 |
| agosto | 660 / 2 / 13 | 1.243 / 188 / 24 | 1.232 / 31 / 24 |

En MODIS el control pasa aunque se inviertan todas las publicaciones; en VIIRS 750 tolera cambiar entre 30 y
90 % de lo publicado; en VIIRS 375, 24 a 29 pasadas por mes, cuando el efecto que se busca es del orden de 3
pasadas por mes (P1) y de 10 a 17 (P2). El determinismo previo medido en el proyecto fue **exacto** (Láscar,
`determinismo_lascar_contra_B.txt`: 100 % en marzo, abril y junio), así que no hay razón para tolerar 2 %.
Además, `evaluar_ventana.py` calcula el determinismo agregado sobre los tres sensores (no "por sensor") y lo da
por FALLA si falta una sola pasada (`len(amb) == len(G)`), o sea mezcla cobertura (A108) con determinismo.

Y P1 cuenta `g["F2"]`, las pasadas que F2 publica, sin exigir que el F **de este run** no las publique. Si el F
nuevo publica alguna de las 14 por ruido de entorno o de datos, se cuenta como recuperación de F2.

**Corrección.** (a) Determinismo F nuevo contra F viejo: **exacto** en las 36 claves de la lista fija, y sobre
el conjunto publicado (no sobre todas las pasadas), por sensor, con cobertura informada aparte. (b) Agregar el
nulo gratis que el diseño ya trae: **F contra F2 en VIIRS 750 y MODIS dentro del mismo run** tiene que dar
idéntico (el flag no llega a esos procesadores), y conviene compararlo en `n_anomalous_pixels` y magnitud, no
sólo en la decisión de publicar, porque MODIS casi no publica. Ese nulo mide el ruido entre jobs del mismo run,
que es justo el que afecta a P2 y P4. (c) P1 = F2 publica **y** el F de este run no publica; informar aparte las
claves donde el F nuevo publica.

### H4. Con lo que la investigación ya midió, P1 y P2 casi se excluyen: falta escribir la previa y medir selectividad. Gravedad 3

La investigación (`docs/S150_ALERTAS_DEBILES_MAX.md` §4) mide que las pérdidas y el residual que `max` apaga con
razón son indistinguibles en lo que guarda el record (sigma dNTI AUC 0,48, exceso de BT 0,52, camino 0,53).
Calculé la cota superior de lo que F2 puede reabrir en negativos limpios de VIIRS 375 con los runs viejos
(script en el Anexo). El argumento: un píxel nuevo de F2 tiene BT ≤ t_bg + 3 K y pasa `max(C1, ...)` ≥ C1; en B
ese píxel falla la compuerta pero lo rescata el segundo pase (`min(C1, ...)` ≤ C1, y el dNTI no baja al excluir
vecinos activos), así que lo nuevo de F2 cae dentro de lo que B publica y F no.

| mes | negativos limpios | F publica | residual (B sí, F no) | camino D22 en el residual | algún píxel bajo t_bg + 3 K |
|---|---|---|---|---|---|
| abril | 429 | 15 (3,5 %) | 122 | 49 (+11,4 pt) | 103 (+24,0 pt) |
| mayo | 349 | 8 (2,3 %) | 97 | 41 (+11,7 pt) | 75 (+21,5 pt) |
| junio | 473 | 7 (1,5 %) | 148 | 59 (+12,5 pt) | 110 (+23,3 pt) |
| julio | 505 | 12 (2,4 %) | 223 | 65 (+12,9 pt) | 155 (+30,7 pt) |
| agosto | 568 | 21 (3,7 %) | 176 | 57 (+10,0 pt) | 133 (+23,4 pt) |
| total | 2.324 | 63 (2,7 %) | 766 | **271 (+11,7 pt)** | 576 (+24,8 pt) |

O sea: P2 **puede** fallar (bien), y el estrato D22 es el 35 % del residual pero sólo el 12 % de las alertas que
B publica (122 de 988). Si F2 recuperara las dos poblaciones a la misma tasa, cumplir P1 (al menos 50 % de las
14) costaría unos +5,9 puntos en negativos y P2 fallaría. P1 y P2 juntas se cumplen sólo si el primer pase sin
compuerta es **selectivo** (recupera al menos la mitad de las 14 y reabre menos de una cuarta parte de los 271),
justo lo que la investigación dice que el record no separa. El antecedente apunta igual: en S143 quitar D22 sumó
unos +20 puntos de sobre-publicación (otra configuración: Test 1 encendido, `min`, segundo pase condicionado).

**Corrección.** (a) Escribir esta previa en el §4 antes de despachar, con los números. (b) Congelar ahora, como
`filas.json`, la lista de los 271 negativos del camino D22 (y los 576 del criterio amplio) y agregar una
predicción de selectividad dentro del mismo estrato: tasa de recuperación en las 14 contra tasa de reapertura en
los 271. Es la medición que decide la hipótesis H2 de la investigación; P1 y P2 por separado sólo la rodean.

### H5. La unidad del operador es la noche, y en noches el premio de P1 es como mucho 4. Gravedad 3

De las 14 pérdidas del camino D22, en **10** el F viejo publica otra pasada del mismo volcán esa misma noche
(misma fecha UTC; todas las pasadas están entre 04:30 y 07:00 UTC). Sólo 4 noches quedan sin publicación de F:
Tupungatito 2026-04-22, Planchón Peteroa 2026-04-10, Planchón Peteroa 2026-08-24 y Chaitén 2026-08-18. Aun si
P1 se cumple entera, el operador gana como mucho 4 noches en cinco meses (A94). El costo de P2, en cambio, se
mide en pasadas, y una pasada nueva en un negativo limpio puede ser una noche nueva que MIROVA miró sin ver nada.

**Corrección.** Informar P1 y P2 también en noches (las mismas 4 noches como numerador posible; y las noches
nuevas con publicación de F2 donde MIROVA no vio nada) y decidir en la unidad del operador, o declarar
explícitamente que la meta es paridad por pasada y por qué.

### H6. El cableado está descrito mal en el pre-registro, en el perfil y en el catálogo. Gravedad 2

- El §2 y el comentario de `_s150_max_sin_d22.yaml` dicen que el flag llega "al primer pase (`_eti_gate_bt`) y al
  segundo (`apply_bt_gate`)". No es así: `apply_bt_gate` (`process_viirs.py:1301`) es el **primer** pase
  (`first_pass_tests_2_and_3`); `_eti_gate_bt` (`process_viirs.py:1216`) es el camino ETI cuadrático, inerte
  porque `ENABLE_ETI_QUADRATIC_SCENE = False`. El segundo pase (`second_pass_adjacent`) nunca tuvo compuerta.
- El efecto sobre el segundo pase es **indirecto**: más píxeles activos en el primer pase cambian la media de
  vecinos (se excluyen) y el pozo de mu2 y sd2 del segundo pase, que corre sin condicionar sobre toda la escena.
  Lo nuevo que publique F2 puede venir de esa cascada y no sólo del primer pase; por eso P6 debería atribuir por
  etapa con `diag_n_first_pass_pixels` y `diag_n_second_pass_recapture`.
- `pipeline/profile.py` (comentario del flag) y D22 en `docs/MIROVA_DIVERGENCES.md` dicen que el flag quita la
  compuerta también en `contextual_dnti_hot_mask` y `dual_roi_contextual_dnti_hot_mask`. Los helpers aceptan el
  parámetro, pero las llamadas de `process_viirs.py` (el bloque del camino D, unas 15 líneas antes de
  `n_dnti_ctx_path = int(np.sum(dnti_ctx_hot))`) **nunca lo pasan** (`git log -S` sólo muestra #681, que cableó
  el primer pase y el ETI). Es la forma de A118. **En este A/B es inerte**: con el primer pase encendido
  `hot_mask_2d = fp_hot` pisa esa máscara, y su otro consumidor, el filtro contextual del Test 1, no corre con el
  Test 1 apagado. Pero sí toca el antecedente: en S143, con el Test 1 encendido y
  `ENABLE_TEST1_CONTEXTUAL_FILTER = True`, el filtro del Test 1 siguió aplicando la compuerta en el brazo "sin
  D22". Ese brazo quitó D22 sólo en parte.

**Corrección.** Corregir las dos frases (pre-registro y YAML), y anotar en D22 del catálogo que el camino D nunca
recibió el flag (o cablearlo, con A45, si se va a volver a usar con el Test 1 encendido).

### H7. P4 se cumple casi por construcción. Gravedad 2

Por el mismo argumento de H4 al revés: quitar la compuerta sólo agrega píxeles al primer pase, y más activos
sólo agregan recaptura en el segundo; la máscara de F2 contiene a la de F. P4 sólo puede fallar por un efecto
lateral de cúmulo o magnitud (A18: un píxel nuevo que cambia el cúmulo primario o su distancia) o por ruido entre
jobs. Está bien como guarda de regresión, pero el pre-registro debería decirlo y no presentarla como una
predicción con poder.

### H8. La prueba nula de `recuperacion_d22.py` se cumple por construcción; le faltaba el control positivo, que corrí. Gravedad 2

F contra sí mismo da 0 recuperadas aunque el instrumento estuviera mal en todo salvo el pareo de claves, porque
las 14 se definieron justamente como pasadas que ese F no publica (A116: un cero se acepta cuando se mostró que
el instrumento puede dar distinto de cero). Corrí el control positivo con las mismas tablas, **control F viejo,
brazo B viejo** (B publica las 36 por definición):

```
B solo 2.o pase, BT < t_bg+3K ... confiable   n 14 | en las tablas 14 | publica F 0 | publica F2 14
B por 1.er pase ...                 confiable   n 18 | en las tablas 18 | publica F 0 | publica F2 18
P1 (camino D22, etiqueta confiable): F2 publica 14 de 14 ... | CUMPLE
P5 (informativa, camino primer pase): F2 publica 22 de 22
```

El instrumento ve las recuperaciones cuando las hay. **Corrección**: guardar esta salida junto a la del nulo
(tablas armadas con `armar_tabla.py --control <F viejo> --brazo <B viejo>`, abril con Chaitén de B tomado de
37823348991, como hizo S149).

### H9. "Mismo código" no es "mismo entorno", y el despacho "desde main" pide mergear antes. Gravedad 2

- El workflow instala `numpy`, `scipy`, `h5py` y `earthaccess` sin versión (`pip install earthaccess numpy h5py
  scipy pyyaml`), y los gránulos se vuelven a bajar de NASA. Entre el 2026-09-22 y hoy pueden haber cambiado
  versiones y productos (reprocesos, estándar contra NRT). Por eso H3 importa: el control de determinismo es lo
  único que liga la lista fija (definida con el F viejo) con el run nuevo. Efecto lateral bueno: los runs viejos
  no registraban los flags (SIN VERIFICAR en `S150_RESULTADO_MESES.md` §6); un F nuevo idéntico al viejo, con su
  `FLAGS_BRAZO` en el log, lo verifica retroactivamente. Conviene decirlo.
- El perfil `_s150_max_sin_d22.yaml` y la línea `FLAGS_BRAZO` nueva sólo existen en la rama
  (`git diff origin/s150-ab-d22 origin/main` los muestra como ausentes en main). "Desde `main`" exige mergear el PR
  primero; despachado antes, el brazo F2 caería con `ValueError` de perfil desconocido. Escribirlo en el §2.
- El pre-registro debería listar el run viejo de F por mes para el determinismo: abril 35639417826 (no
  37823348991, que sólo trae a Chaitén de B), mayo 35599902448, junio 35675490175, julio 35728617326, agosto
  35759688167.

### H10. Brazos: falta uno útil y sobra uno que la consigna sugería. Gravedad 2

- **B sin D22** (conectiva `min`) no aporta: con `min` el segundo pase sin condicionar ya rescata todo lo que la
  compuerta bloquea, y el test sintético de S142 mostró que quitarla sola mueve píxeles del segundo pase al
  primero sin cambiar lo publicado. Sería un brazo que confirma lo conocido.
- **F2 con el segundo pase condicionado** (`enable_second_pass_conditioned: true`, flag existente, sin código) es
  la receta del paper: sin compuerta y con segundo pase sólo sobre vecinos de lo ya detectado. La investigación
  (H2, §6) dice que con el segundo pase del paper las 15 pérdidas "no existirían mientras siga la compuerta"; este
  brazo responde la pregunta complementaria: sin compuerta y con segundo pase literal, ¿cuánto queda del residual
  que hoy viene del segundo pase sin condicionar? Cuesta 11 jobs más por run. Opcional, pero es el brazo que
  responde lo que el pre-registro dice buscar ("si MIROVA no tiene la compuerta...").
- El brazo que separaría D22 de D26 (H1) requiere código.

### H11. Detalles. Gravedad 1

- El comentario del YAML dice "16 son un píxel apenas más caliente"; el pre-registro y la investigación dicen
  14 en VIIRS 375 con etiqueta confiable (16 suma las 2 de VIIRS 750, que este flag no toca). Unificar.
- Falta la regla para cuando alguna de las 14 no esté en las tablas del run nuevo (A108): hoy el denominador
  queda en 14 y la pasada faltante cuenta como no recuperada. Declararlo INDECIDIBLE para esa clave o repetir el
  job.
- Lastarria 2026-06-30 06:42 entra al camino D22 con un exceso que se imprime como 3,0 K (es menor que 3 por
  redondeo). Es el caso borde; conviene mirarlo aparte si decide P1 por una unidad.
- Potencia: con 14 casos, si la tasa real de recuperación fuera 50 %, P1 se cumple con probabilidad cercana a
  0,6. Es lo que hay, pero conviene que el veredicto lo diga.

## Qué cambiar antes de despachar (resumen)

1. Salvedad D22 junto con D26 y techo de 12 en P1 (H1); trazado por etapa de las 14 (H1, H6).
2. Script de lectura que implemente P2 (F2 menos F en puntos, por mes) y P4 (98 %, 1 MW, etiqueta según A119), y
   aviso de que los veredictos de `medir_predicciones.py` no son los del pre-registro (H2).
3. Determinismo exacto en las 36 claves y sobre lo publicado, por sensor; nulo F contra F2 en VIIRS 750 y MODIS
   dentro del run; P1 = F2 publica y F nuevo no (H3).
4. Previa escrita y predicción de selectividad en el estrato D22, con la lista de los 271 negativos congelada (H4).
5. P1 y P2 también en noches (H5).
6. Corregir la descripción del cableado; mergear antes de despachar; listar los runs viejos (H6, H9).

## Anexo: cómo se midió

- Extracción: `git fetch` de `refs/heads/s146-ab/<run>` y `git archive origin/s146-ab/<run>
  experiments/_s146_ab_sin_test1/salidas/<run>` a un temporal; código desde `git archive origin/s150-ab-d22
  <rutas>`; CSV congelados copiados del árbol local y comprobados contra el sha256 del manifiesto.
- Tablas: `armar_tabla.py --control <F viejo> --brazo <F viejo>` (nulo) y `--brazo <B viejo>` (positivo), por mes,
  con las ventanas del pre-registro. Los conteos de pasadas (3.433, 3.682, 3.520, 3.497, 3.135) coinciden con los
  de la investigación.
- Cota de H4: para cada negativo limpio de VIIRS 375 con B publica y F no, se lee el record de B y se cuenta (a)
  camino D22 = `diag_n_first_pass_pixels == 0` y `max(anomaly_pixels.bt_k) - t_bg_k < 3`, la misma regla de
  `clases_rechazo.camino`; (b) criterio amplio = `min(anomaly_pixels.bt_k) - t_bg_k < 3`. Con la regla (a) los
  totales cuadran con el residual de 766 de la investigación.
- Noches de H5: misma fecha UTC y mismo volcán, cualquier sensor, publicada por F viejo, sobre las tablas del nulo.
- Lo no verificado: que `ubuntu-latest` fuera 24.04 el día de los runs viejos (SIN VERIFICAR); qué versiones de
  numpy y scipy instalaron (los logs no las guardan; SIN VERIFICAR); la cota de H4 asume que la publicación es
  monótona en la máscara, lo que puede romperse por cambios de cúmulo (por eso es cota, no predicción).
