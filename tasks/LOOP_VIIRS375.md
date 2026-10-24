# Loop de VIIRS 375 (S162, sesión hija de la coordinadora «Retomar», local_4152952c)

Única fuente de verdad entre vueltas. Worktree
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s162-viirs375-c1b864`, rama
`claude/s162-viirs375-c1b864`. Programa: `docs/superpowers/specs/2026-10-24-programa-replica-por-sensor.md` §4.
Carpeta del trabajo: `experiments/_s162_v375/`.

Reglas de esta sesión (las de la coordinadora, 2026-10-24): sólo este worktree y esta rama; no escribo
`tasks/LOOP_OBJETIVOS.md` ni archivos de las sesiones de instrumento, VIIRS 750 o MODIS; nada en `pipeline/` sin
pre-registro sellado, verificador limpio, tag defensivo y el sí de Nicolás (A45); **todo despacho de GitHub Actions se
pide a la coordinadora** (SendMessage a local_4152952c) con el pre-registro y la lista de brazos; ningún A/B nuevo antes
de que el instrumento entregue la cobertura contra la referencia (fase 0, PD0); sólo `EARTHDATA_TOKEN` (A71); nunca
`git stash`; `git add` por archivo; verificador con contexto limpio de otro modelo antes de aceptar cualquier resultado;
parada si C: o D: bajan de 3 GB. Puedo abrir sesiones propias (permiso de Nicolás vía coordinadora, 2026-10-24), cada
una en su worktree, con su archivo enlazado aquí, y avisando a la coordinadora con nombre e id; hoy no hay ninguna.

## Cola (en el orden del programa)

| id | qué | estado |
|---|---|---|
| V375-B | lote de negativos limpios neg_resto para el port (D-36) | **TERMINADO** (run 40116289866, verificado): NO RESUELTO por la regla (lote solo 4,10 % contra 3,85 %), del lado del silencio |
| V375-C | 10 brazos de ROI (mismo lote que B) | **TERMINADO** (verificado): caja **C13** en el cráter; compuesto por volcán valida en O; V375-D no necesario |
| V375-E | pre-registro del paquete V375 contra K, curva de cenit contra la de MIROVA | listo y verificado (`b9e9c9f97`); no despachable hasta PD1, PD3 y el evaluador común del instrumento (M con d′) |
| V375-D | números propios de 375 | sólo si B o C lo exigen (disparador en `PREREGISTRO_C.md` §5.3) |
| V375-F | Chillán sobre 3 MW (port 0,939, n 6) | después de V375-E |
| V375-A | etiqueta de protegida de cráter | la hace la sesión del instrumento; `evaluar.py --protegida-crater` la recibe |

Esperando de otros: cobertura contra la referencia de MIROVA (instrumento, `evaluar.py --cobertura`), V375-A
(instrumento), evaluador común con placebo y d′ (instrumento, para E), el despacho combinado de la fase 1 (coordinadora).

## Decisiones para Nicolás (con recomendación)

1. **Sellar V375-B y V375-C** después del verificador limpio. Recomendación: sí, con las correcciones que pida el
   verificador en una adenda.
2. **Tamaño del lote**: 709 pasadas nuevas (~4,9 h de runner, ~50 min de reloj con 8 en paralelo) para B y C juntos,
   o sólo los 400 negativos de B (~2,8 h). Recomendación: las 709; C sin sus 155 alertas bajo 1 MW nuevas no tiene con
   qué decidir la caja (S159 tenía 45 de 949).
3. **Marco**: el congelado de S159, hasta el 2026-10-21. Extenderlo hasta el 2026-11-02 12:59 UTC (antes del cese de
   Suomi NPP) sería una adenda con población nueva. Recomendación: no por ahora.

## Bitácora

### 2026-10-24 (vuelta 0, cierre)
- **Hecho**: `experiments/_s162_v375/` con selección (709 pasadas nuevas, semilla 162, 531 gránulos), brazos (10 cajas),
  runner (`probe_v375.py` + `probe-s162-v375.yml`, para la coordinadora), evaluador y tres borradores de pre-registro.
  Commit `041e7fc43`. Código del port de S159 traído de `ca034d66e` en `29d7a5bf4`.
- **Pruebas** (todas en verde): brazos recalculados sin red sobre las 149 grillas de S159 = runner de S159 en 149 de 149
  (M14, PIX7, SENS); escena sintética: foco débil en el cráter de Tupungatito invisible para M14 y visible para C13, C14,
  C21, M21, SENS, SENS_PT y CIRC; prueba de signos con pesos = la sellada de D-45 en 2.000 de 2.000 juegos; casos con
  respuesta conocida para P2, silencio, cota honesta, elección en T, pesos y decisión.
- **Humo del evaluador sobre el lote de S159 (ya visto)**: reproduce el informe de S159 con una implementación
  independiente (M14: recall bajo 1 MW 0,616 contra 0,618; SENS 0,905 y negativos 0,0481 contra 0,0480; neg_resto 0 de
  45). Controles nulo, NUNCA y PLACEBO en verde. **Cambió dos reglas, declaradas en `PREREGISTRO_C.md` §6**: el veto
  absoluto contra K bloqueaba a los diez brazos por las mismas 3 protegidas sólo OCR (pasó a veto relativo a M14 y el
  disparador de D cuenta la tabla sola), y se agregó desempate por caja más chica. Como ya vi los brazos nuevos sobre
  S159, **decide el lote S162 solo** y la unión confirma (§5.5).
- **Hallazgo de instrumento para V375-E**: el nulo de 750 (mismos pares ordenados por hora) no sirve en 375: el VRP de
  MIROVA baja de una pasada a la siguiente de la misma noche (mediana 0,818, n 365; ¿plataforma?, SOSPECHA). Nulo nuevo:
  pares de cenit parecido (< 5°) en orden al azar (MIROVA 0,98). Línea base de K medida: MIROVA cae 0,778 de la pasada
  menos oblicua a la más oblicua, K 0,573; razón doble 0,766 [0,722; 0,861], CAE MAS QUE MIROVA; sobre 50°, 0,733.
- Pendiente: verificador limpio (Sonnet) sobre los tres; resumen a la coordinadora en la carpeta de notas.

### 2026-10-24 (vuelta 1): verificador limpio y entrega
- Verificador limpio (Sonnet, `experiments/_s162_v375/verificador/INFORME.md`): el instrumento aguanta y B no tiene
  defecto que lo invalide. Confirmó población, pesos, Wilson 0,86 % con 0 de 445, hash de la selección y la prueba de
  signos (2.000 de 2.000; 0 falsos en 400). Encontró reglas que no podían fallar o eran más laxas que su texto; todas
  corregidas en `b9e9c9f97` (tabla en `PREREGISTRO_C.md` §8): validar en O exige GANA; disparador (b) de D contra el
  recall de K del marco (censo, 0,957); desempate por volcán a la caja más chica; veto de protegidas sobre la unión;
  nulo de cenit de E ordenado como la lectura (con orden al azar d y 1/d eran equiprobables) y sesgo de plataforma
  aparte (K: 0,66 / 0,64 / 0,61, sin sesgo); equivalencia de E sin tolerancia en la publicación; runner sobre float32.
- Humo sobre S159 con las correcciones (visto, no decide): global C13; por volcán C13 en Cordón Caulle y en
  Tupungatito, VALIDA EN O con GANA contra M14 y contra K; V375-D no necesario; 3 protegidas sólo OCR que pierden los
  diez brazos (riesgo para el veto de V375-E, dicho antes de medir).
- Entrega a la coordinadora: nota
  `C:\Users\nmend\AppData\Roaming\Claude\side-session-notes\local_4152952c-6afd-433a-82b3-b07575feee3b\VIIRS375_entrega_fase1.md`
  y SendMessage. No despaché nada. **Siguiente**: esperar el sello de Nicolás, la cobertura y V375-A del instrumento y el
  despacho de la coordinadora; cuando lleguen los artefactos, correr `evaluar.py` y pasar el resultado por un verificador.

### 2026-10-24 (vuelta 2): respuesta de la coordinadora y estado del instrumento
- La coordinadora mete V375-B, V375-C y V375-E en el despacho combinado de la fase 1 con V750-B y MOD-C, y pedirá un
  solo sello a Nicolás para los cuatro cuando estén los verificadores de V750-B y MOD-C. Me avisa con el número del run.
- Instrumento (leído en su `tasks/LOOP_INSTRUMENTO.md`, sin tocarlo): **V375-A hecha** como `protegida_de_crater` en
  `scripts/clase_mirova.py` (PR #903, sin mergear; cráter VIIRS 375: 123 de 248 protegidas). **Cobertura contra la
  referencia (su T1) todavía no.** Hallazgo suyo que me toca: 76 protegidas VIIRS sólo OCR sin ningún record de
  producción a ±10 min (ninguna entra a mi marco, que parte de nuestros records; van con la cobertura).
- Tarea nueva en la cola: cuando #903 se mergee, que `evaluar.py` llame a `protegida_de_crater` directamente (hoy espera
  un archivo en `--protegida-crater`), con prueba; cuando llegue T1, conectarla en `--cobertura`.

### 2026-10-24 (vuelta 3): #904 y #905 abiertos, cómo conectar la cobertura
- El instrumento abrió #904 (`scripts/evaluador_comun.py`: T1 cobertura contra la referencia, T2 «no observado», T5 P1b y
  publicaciones sobre RUTINA) y #905 (T3 placebo y d′). #902 a #905 siguen sin mergear; los decide la coordinadora.
- **Diseño de la conexión** (para hacerlo cuando #904 entre, sin depender de código sin mergear): `evaluador_comun`
  compara carpetas de records por brazo (un A/B completo). Mi lote es una MUESTRA armada desde los records de
  producción, así que su T1 se aplica al MARCO, no a los brazos: correr `cobertura()` con un solo lado, producción en
  533398f8f (`D:\vrp-trabajo\temporales\s159_n\data_main`), sobre la ventana del marco sin los días excluidos, y
  contar las pasadas de MIROVA (protegidas y alertas bajo 1 MW) sin record de producción: son las que el sorteo nunca
  pudo elegir. Una protegida en esa lista que el port sí vería es una falla de cobertura del marco y se informa antes
  del veredicto. La cobertura del lote (pasadas sorteadas sin estado ok) ya la hace `evaluar.py` §1.
- P1b de T5 lo tengo propio en `evaluar.py`; si el instrumento lo pide común, uso el suyo y comparo los dos.

### 2026-10-24 (vuelta 4): sello por D-48 y commits de disparo
- La coordinadora adelanta el lote (V750-B no sale antes del 2026-11-03) y sella B y C con **D-48** (Nicolás,
  2026-10-24: «sobre las decisiones mías haz lo que tú recomiendes»; verificado en su `tasks/LOOP_OBJETIVOS.md`), sobre
  la recomendación de 709 pasadas; revocable por Nicolás. Anotado en los dos pre-registros: commit `19d7f5e98`, tag
  `s162-v375-bc-sello`.
- **Hallazgo antes de disparar**: el `pipeline/` de `loop/activo` (mi rama) difiere del de 533398f8f (el código que
  escribió los records del marco) en 12 archivos (S157: λ por banda de MODIS apagada, perfiles de D25). Para que el
  control «K re-corrido = publicado» compare el mismo detector, el disparo NO sale de mi rama: los commits se armaron sin
  checkout sobre el árbol de `ca034d66e` (`pipeline/` idéntico a 533398f8f, ya trae el port y el oráculo) más
  `experiments/_s162_v375/` del sello (idéntico) y el workflow: humo `fd0ba12bb` (tag `s162-v375-disparo-humo`, 1 job,
  pasadas 1011 y 1062) y lote `798cac8ea` (tag `s162-v375-disparo-lote`, hijo del humo, 28 trozos). Sólo `main` y ramas
  propias disparan otros workflows por push: la rama `s162-v375-disparo` corre sólo éste. Autoprueba sin red del runner
  pasada sobre el árbol exacto del lote (extraído con `git archive` limitado a rutas, 8,8 MB).
- Comandos entregados a la coordinadora. **Siguiente**: cuando avise el run del humo, bajarlo a
  `C:\vrp-trabajo\temporales\s162_v375\`, revisar (estado ok en las 2, K re-corrido = publicado, grilla guardada,
  recálculo = runner) y darle el OK; después, el lote.

### 2026-10-24 (vuelta 5): humo en verde, OK dado; cobertura del marco OK
- Humo run **40115765406** (success, 2 min 15 s; artefactos en `C:\vrp-trabajo\temporales\s162_v375\run_40115765406\`):
  2 de 2 ok; Láscar 2026-04-05 05:30 port 1,521 MW en los 10 brazos contra MIROVA 1,52; K re-corrido 1,086 = publicado;
  Tupungatito 2026-05-04 06:30 en 0 píxeles y K no publica. Recálculo = runner 467 de 467; K 151 de 151. **OK dado a la
  coordinadora**; el lote sale después de MOD-C.
- El humo destapó un KeyError del evaluador en el camino del lote S162 (compuesto por volcán con el veto sobre la unión):
  arreglado sin cambiar reglas, adenda 1 de C (`a6a02071b`).
- **Cobertura del marco** con el evaluador común del instrumento (#904, `ff452671c`, sin mergear, corrido desde su árbol):
  COBERTURA OK, 1.208 alertas (unión) y 882 (tabla) con record de producción, 0 sin record; las 179 observadas fuera del
  marco son las sólo OCR antes del 06-13 (A119). Adenda 2 de C (`a01d50f57`). Referencia del marco reconstruida en
  `C:\vrp-trabajo\temporales\s162_v375\ref_marco\` (tabla y OCR de S159 más respaldo e histórico de `ca034d66e`).
- **Siguiente**: cuando avise el run del lote, bajarlo a `C:\vrp-trabajo\temporales\s162_v375\run_<RUN>\`, correr
  `evaluar.py --art162 <run> --cobertura cobertura_marco.json`, y pasar el resultado por un verificador limpio antes
  de informarlo.

### 2026-10-24 (vuelta 6): lote run 40116289866 terminado; cobertura del lote completa
- Run **40116289866** (rama `s162-v375-disparo` en `798cac8ea`, 17:28 a 18:24 UTC): 18 jobs success, 10 failure. Los 10
  en rojo son el exit 2 de diseño por pasadas no procesadas, no caídas. 28 de 28 artefactos bajados a
  `C:\vrp-trabajo\temporales\s162_v375\run_40116289866\` (86 MB). **709 de 709 con resultado**: 698 ok (698 grillas) y
  11 `volcan_fuera_del_granulo`.
- Diagnóstico de las 11 (antes de evaluar, A108): las 11 son neg_resto (MIROVA RUTINA, K no publica). El probe bajó el
  MISMO gránulo que el record de producción (mismo nombre, con la hora de proceso), así que no es una versión o reproceso
  distinto como el 12-oct. El píxel más cercano del gránulo queda a 5,1 a 24,6 km del centro de la grilla: el volcán está
  fuera o en el borde de la franja (producción deja record porque su círculo de 25 km roza el gránulo). 6 de 11 son
  pasadas partidas (el gránulo vecino tiene el volcán). Son «no observado» por la regla de #904: salen del denominador y
  su estrato se re-pondera; 11 de 400 neg_resto (2,75 %). Conservador para el port, porque la vara de K (133 / 3.456) sí
  las cuenta. Sin relanzar (bajaría el mismo gránulo). Informado a la coordinadora.
- Evaluación corriendo (`resultado_run40116289866/`); después, verificador limpio antes de informar.

### 2026-10-24 (vuelta 7): lectura del lote (SIN VERIFICAR todavía), commit `20719dc8f`
- Instrumento: recálculo sin red = runner 7.427 de 7.427; K re-corrido = publicado 847 de 847; controles nulo, NUNCA
  y PLACEBO en verde; cobertura del marco OK; ningún estrato sin representar.
- **B**: el port (M14) publica 4 de 434 neg_resto (0,95 % [0,37; 2,38]; la cota de 8,5 % de S159 baja a 2,4 %). Todos
  los negativos: unión 2,01 % [1,46; 3,39] contra K 3,85 %, SILENCIO ACOTADO; lote S162 solo 2,17 % [1,23; 4,10], NO
  RESUELTO. Por §5.5, **B = NO RESUELTO (depende del lote visto)**.
- **C**: global **C13** en el lote y en la unión; por volcán C13 en Cordón Caulle y en Tupungatito, **VALIDA EN O** en
  los dos; **V375-D no necesario** en los dos. C13: recall bajo 1 MW 0,954 [0,916; 0,976] contra K 0,957 (marco),
  negativos 2,03 %, P2 contra K GANA, M 0,999 (n 265). Las mismas 6 protegidas perdidas en todos los brazos (3 que K
  publica, las 3 sólo OCR, 0 de la tabla).
- Verificador limpio (Sonnet) lanzado sobre el resultado; NO informar a Nicolás como hecho hasta que vuelva.

### 2026-10-24 (vuelta 8): resultado VERIFICADO, `35e9560c2`
- Verificador limpio (`resultado_run40116289866/verificador/INFORME.md`): CONFIRMA el instrumento, las 11 no
  observadas, C13 global y por volcán, V375-D no necesario; ningún hallazgo cambia un veredicto. Reproduce todo con una
  implementación propia. Reparos: B en el lote solo depende de tratar neg_pub como muestra (113 de 133; como censo la cota
  baja a 3,80 % y se resolvería): **no se cambia la regla**, se informa como sensibilidad; «4 de 434» es la unión (lote:
  4 de 389); las 6 protegidas perdidas por los 10 brazos son de Suomi NPP, sólo OCR y del lote S159 (riesgo para el veto
  de V375-E, esperan V375-A); una línea sellada de B editada (adenda 1 de B).
- Informe: `experiments/_s162_v375/resultado_run40116289866/INFORME.md`. Va a PD1: **caja C13** (cráter de
  `volcanoes.yaml`); V375-D no se abre; B NO RESUELTO (resolverlo pide otra muestra de neg_resto, no reinterpretar).
- Cola: V375-B y V375-C **terminados**. Siguiente: V375-E (espera PD1 de Nicolás, PD3 en `pipeline/` y #903/#905), y
  después V375-F. El loop queda en espera.

### 2026-10-24 (vuelta 9): V375-B2 pedido por la coordinadora (D-48)
- Pedido: segunda muestra de neg_resto disjunta, pre-registrada antes de mirar nada, misma regla sellada, sin contar
  neg_pub como censo, tamaño el que la regla necesite.
- Traba medida: las 133 neg_pub del marco ya están todas medidas, así que en el conjunto que decide su cota queda fija
  (31 de 113, 36,5 %); la cota de neg_resto tiene que bajar de 2,80 % a 2,54 %. Simulación (`b2/tamano_b2_salida.txt`):
  con la tasa observada (1,16 %), 400 nuevas deciden en 91 %, **600 en 95 %**, 800 en 97 %; con tasa real de 2 %, ninguna.
- Borrador `b2/PREREGISTRO_B2.md` (commits `33567bd91`, `987e4f814`): 600 neg_resto nuevas, semilla 163, decide S162 +
  B2 con la regla sellada; se declara la segunda mirada (inflación hasta 5 % por cola) y se informa la lectura estricta
  (z 2,241). Ya visto al probar el evaluador: estricta 4,49 % con S162, 3,68 % con la unión. Evaluador extendido
  (`--objetivos-extra`, `--art-extra`, `--deciden`); regresión: la lectura publicada sale idéntica salvo el rótulo y la
  línea estricta. Workflow `b2/probe-s162-v375-b2.yml` (24 trozos, rama `s162-v375-b2-disparo`).
- Verificador limpio (Sonnet) del pre-registro corriendo. Después: correcciones, sello por D-48, commits de disparo
  (humo y lote sobre `ca034d66e`) y pedido de despacho a la coordinadora.

### 2026-10-24 (vuelta 10): verificador del B2 v1 y versión 2
- Verificador v1 (`b2/verificador/INFORME.md`): muestra disjunta, pesos y evaluador sin cambios en lo publicado,
  CONFIRMADOS. **F1 (gravedad 3)**: decidir con S162 + B2 reutilizaba lo ya visto, contra la lógica de C §5.5. Medido:
  en la frontera ese diseño declaraba ACOTADO en 11 a 20 % de los casos; con B2 sola, 1 a 3 %.
- **B2 v2** (`7ff23cc3a`): decide neg_resto de B2 sola + neg_pub de S162 (`--deciden S162b --neg-pub-de S162`); **1.200**
  neg_resto nuevas (93 % de decidir con la tasa observada; pesos 2,72 a 2,83; sha256 `6328988b…019a`); cobertura por lote y
  lote vacío invalida (F4, F5); potencia con tasa pareja declarada como SOSPECHA (F3). Regresión: la lectura publicada
  sale idéntica. Workflow de 48 trozos (~8,3 h de runner, ~90 min de reloj).
- Segundo verificador limpio (Sonnet) sobre el v2 corriendo.

### 2026-10-24 (vuelta 11): segundo verificador, B2 v3 listo, commits de disparo
- La coordinadora aprobó 1.200 por D-48, condicionado a que el segundo verificador diera conforme.
- Verificador v2 (`b2/verificador_v2/INFORME.md`): muestra, cuenta («decide B2 sola», 15 cifras con 1.200 fabricadas),
  tamaño en la frontera y workflow CONFIRMADOS. **Hallazgo 3 (gravedad 3)**: ningún control probaba que el port
  estuviera vivo en el run de B2 (un port muerto daba «calla» con el instrumento OK). Otros: el 93 % es condicional
  (predictiva 0,74 a 0,80), la cobertura por lote sólo avisaba, rótulos de la salida ambiguos.
- **B2 v3** (`ae65eaaaf`, tag `s162-v375-b2-listo`): control de vida de 20 pasadas re-medidas de S162 en el mismo run
  (ids 5000 a 5019, fuera de todo denominador; control 2.2b); la cobertura del lote que decide da NO DECIDE; línea
  «VEREDICTO B». Probado con runs fabricados: vivo, 20 de 20 iguales; muerto, INVALIDO. Regresión: lo publicado sólo
  cambia en los dos rótulos. Objetivos sha256 `f3285f3a…b419` (1.220 entradas).
- Disparo armado sobre `ca034d66e`: humo `74e368f6e` (tag `s162-v375-b2-disparo-humo`, pasadas 5000 y 3000), lote
  `a9331d51c` (tag `s162-v375-b2-disparo-lote`, 48 trozos). Pedido de sello y despacho enviado a la coordinadora: el
  hallazgo 3 está arreglado y probado pero no re-verificado; que lo confirme ella.

### 2026-10-24 (vuelta 12): humo de B2 despachado; re-verificación del delta
- Humo de B2: run **40128648709** (rama `s162-v375-b2-disparo` en `74e368f6e`); vigilante en segundo plano.
- Condición de la coordinadora para el lote: re-verificación corta, contexto limpio y OTRO modelo, sólo del delta v2→v3,
  midiendo el nulo con el port roto a mano. Lanzada con **Fable** (los dos anteriores fueron Sonnet), con la guía de
  prompting de Fable aplicada; informe en `b2/verificador_v3/`. Si da CONFORME y el humo sale bien, el sello queda firme
  con D-48 y doy el OK al lote.
- Humo 40128648709: success, 2 de 2 ok; control 5000 (Láscar) M14 5 px y 1,4126318824 MW = S162; muestra 3000 (Isluga)
  0 px, K re-corrido «far» 0,194 que no publica = record. Artefactos en `C:\vrp-trabajo\temporales\s162_v375\run_40128648709\`.
  Informado a la coordinadora; el OK al lote espera la re-verificación de Fable.

### 2026-10-24 (vuelta 13): Fable CONFORME, sello firme, OK al lote de B2
- Re-verificación del delta v2→v3 (Fable, `b2/verificador_v3/INFORME.md`): **CONFORME**. El control de vida atrapa solo
  (aislado del recálculo) seis modos de port roto; con un lote sano da SILENCIO ACOTADO. H1 (gravedad 3): el control
  dependía del archivo de objetivos; arreglado en `evaluar.py` (lote nuevo sin control da INVALIDO), probado con su caso
  (`muerto_v2obj`) y con el sano. El archivo del disparo sí trae el control (mismo blob `1999237b` en el listo y en el
  lote; sha LF `a7dd6b0d`, CRLF `f3285f3a`).
- Sello firme por D-48 y adenda 1 (H1 a H5) en `b2/PREREGISTRO_B2.md`, commit `09ab70123`. **OK al lote** enviado a la
  coordinadora (commit de lote `a9331d51c`, 48 jobs). Siguiente: evaluar el run cuando llegue (cobertura del lote antes
  de leer, verificador limpio antes de informar).
- Artefactos falsos del verificador v3 (1,8 GB) en `C:\vrp-trabajo\temporales\s162_v375\verif_v3\`: borrables cuando se
  cierre B2.
