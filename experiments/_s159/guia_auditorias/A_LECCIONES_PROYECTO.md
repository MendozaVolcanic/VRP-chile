# Guía maestra de auditorías contra VRP Chile: qué se aplica, qué falta y qué le enseña el proyecto a la guía

> S159, 2026-10-21. Insumo para que otro paso integre cambios a
> `C:\Users\nmend\OneDrive\Escritorio\claude\GUIA_MAESTRA_AUDITORIAS.md` (214 líneas, revisión 2026-09-06) y a
> `C:\Users\nmend\OneDrive\Escritorio\claude\PLANTILLA_CAZA_DE_BRECHAS.md` (531 líneas). No edité ninguna de las dos.
>
> **Qué leí en esta sesión (y nada más se da por leído).** La guía y la plantilla enteras. Del worktree
> `C:\vrp-trabajo\s159-pruebas` (commit `b4adf13cf`): `CLAUDE.md` del proyecto (las citas `CLAUDE.md:NNNN` son de esta
> copia, que tiene 1.926 líneas y está más adelante que la del checkout principal), `docs/_prompts/PREAMBULO-AUDITOR.md`,
> `docs/PROTOCOLO_AUDITORIA_PROFUNDA.md`, `docs/META_RULES_S80.md`, `docs/PLAN_AUDITORIA_S158.md`, `S150`, `S149`, las
> primeras 60 líneas de `S146`, `docs/AUDIT_S158.md`, las secciones 0, 4 a 7 de `docs/AUDIT_S158_R2.md`, extractos de
> `docs/AUDIT_S146.md` y `docs/AUDIT_S155.md`, los cinco informes de verificador de
> `experiments\_s159\{m,n,pareo_modis,mxd03_prereg,chillan_modis}\verificador\INFORME.md`, el apéndice del censo en
> `experiments\_s159\n\INFORME.md` (l. 255 a 285) y
> `C:\vrp-trabajo\s159-evaluador\experiments\_s159\instrumentos\verificador_comparador\INFORME.md`. De la memoria del
> agente (`C:\Users\nmend\.claude\projects\C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile\memory\`):
> `feedback_s135_paridad_de_cobertura_antes_de_comparar.md`, `feedback_s146_metrica_sin_poder.md`,
> `feedback_s152_mutacion_que_cae.md`, `feedback_s156_vigilancia_ciega_y_control_de_mutaciones.md`,
> `feedback_s157_lecciones_generales.md`, `feedback_s158_lecciones_generales.md`.
>
> Abreviaturas de ruta: **GUIA** = la guía maestra; **PLANT** = la plantilla; **PRE** = el preámbulo del auditor;
> **PROT** = el protocolo de auditoría profunda; **VER_X** = `experiments\_s159\X\verificador\INFORME.md`;
> **VER_COMP** = el informe del verificador del comparador en `s159-evaluador`; **MEM_X** = el archivo de memoria X.
> Los tres comprobados de lo que traía el encargo están marcados con la evidencia que lo comprueba (§3, L1 a L5).

---

## 1. Lo que la guía ya tiene y VRP Chile aplica bien

- **Preámbulo canónico pegado entero.** GUIA l. 131 a 137; PRE l. 3 a 7 lo declara adaptado de ARSAND y l. 15 a 61 es
  el bloque. El plan S158 lo exige en el orden (a) preámbulo, (b) bloque común, (c) alcance (PLAN_AUDITORIA_S158 l. 110
  a 112).
- **Las dos preguntas del instrumento en el encabezado de cada medición.** GUIA l. 81 a 86; PRE l. 36 a 42. Los cinco
  verificadores de hoy las escriben arriba (VER_m l. 12 a 19; VER_pareo_modis l. 18 a 21; VER_chillan_modis l. 15 a 16).
- **Verificador con contexto limpio que re-corre y encuentra cosas propias.** GUIA l. 140 a 147. Hoy: VER_m
  «Hallazgos propios» l. 86 a 97 (4); VER_chillan_modis §7 y §8; VER_pareo_modis l. 119 a 127 (3); VER_COMP H1 a H7.
  El proyecto lo llevó más lejos (§3, L10).
- **SIN DATO distinto de FALLA y de OK.** GUIA l. 90; PRE l. 40. VER_n l. 29 a 30 cuenta «0 protegidas perdidas de
  78 medidas» y deja la 79 como SIN DATO en vez de redondear a «0 de 79».
- **Cobertura primero, con confianza y gravedad; el filtro es de otro.** GUIA l. 138 a 139; PRE l. 53 a 54.
- **Sección VERIFICADO LIMPIO.** PRE l. 56 a 59; los seis informes de verificador la traen.
- **Verificar contra el código de hoy antes de creer un pendiente.** GUIA l. 56 a 58; PRE l. 31 a 32; regla A8
  (`CLAUDE.md:260`).
- **Objetivo y límites, bloque de autonomía, informe incremental para sobrevivir al corte.** GUIA l. 152 a 159;
  PLAN_AUDITORIA_S158 l. 133 a 141 y l. 149.
- **Modelo por tipo de tarea.** GUIA l. 160 a 161; PRE l. 73 a 74; PLAN_AUDITORIA_S158 l. 201 a 203.
- **Cuando el dueño contradice, revisar el propio método.** GUIA l. 54 a 55; regla A62 (`CLAUDE.md:812`).
- **Persistir el hallazgo en el momento.** GUIA l. 64; META_RULES_S80 M2 (l. 35 a 59).
- **Planes por familia y tabla de decisiones del dueño con recomendación.** GUIA l. 168 a 170 y 184 a 185;
  AUDIT_S158 §4 (l. 100 a 113).

---

## 2. Lo que la guía tiene y VRP Chile NO aplica, o aplica a medias

### 2.1 La cola de validación en campo, persistente y con IDs (aplica a medias)

- **Guía.** GUIA l. 21 a 22 (toda auditoría entrega pruebas de campo), l. 180 a 182 (los ítems se pegan en la cola y se
  comprueba con `grep` que cada ID existe), l. 212 a 213 (abrir la cola y que cada auditoría declare cuántos ítems le
  aporta).
- **Proyecto.** Cada auditoría trae su propia lista: AUDIT_S158 §5 «Cola de pruebas» (l. 115 a 122) y su decisión 10
  «revisión tuya en el tablero y en los TIF, 3 a 5 casos» (l. 113); PLAN_AUDITORIA_S150 l. 44 pide «la lista de pruebas
  de campo»; AUDIT_S158_R2 tiene una «Guía para revisar con tus ojos» (§9, encabezado en l. 279, no leí el cuerpo).
  Pero la frase «cola de validación» aparece en un solo plan (`docs/superpowers/plans/2026-09-05-auditoria-s134-anillo-y-paridad.md`,
  por `grep -rli`), y no encontré un archivo vivo con IDs que acumule entre auditorías. Si la revisión visual pedida
  en S158 se hizo: SOSPECHA, no lo verifiqué.
- **Qué cambiaría.** Las revisiones de Nicolás en el tablero y en los TIF son el equivalente del «sistema corriendo»
  de GUIA §0, y hoy se pierden de una auditoría a la siguiente igual que los pendientes que el protocolo llama Fuga 2
  (PROT l. 270 a 272). Con una cola única con ID, «qué mirar · qué decide · de dónde sale», cada auditoría podría decir
  cuántas abrió y cuántas cerró.

### 2.2 El frente de magnitudes con unidades (no aplica)

- **Guía.** GUIA l. 118 a 122: censo de toda constante que manda, con sus unidades, y qué pasa con un rango chico,
  medio y grande; instrumento portable con control positivo.
- **Proyecto.** `grep -rli "censo de magnitudes"` en `docs/` y `experiments/_s14*`, `_s15*`: 0 archivos. Lo más
  cercano es el frente C de S150 («cada constante calibrada en reposo, ¿qué hace con 2 a 50 MW?»,
  PLAN_AUDITORIA_S150 l. 34), que mira régimen pero no unidades. Y el proyecto sí tiene defectos de unidades: el
  mínimo de dNTI de MIROVA es 0,02 en sus unidades y 0,0225 en las nuestras de 8 vecinos (AUDIT_S158 l. 30 a 31); un
  radio comparado con otro radio se leyó como distancia entre puntos (A93, `CLAUDE.md:1293`).
- **Qué cambiaría.** Un censo de constantes con columna de unidades habría puesto el 0,02 contra el 0,0225 sin
  necesitar el código de MIROVA, y habría marcado cada umbral cuyo espacio (por píxel, por cúmulo, por noche, por
  kernel de 8 o de 9) no está declarado.

### 2.3 La línea base roja, para guardas y pruebas (aplica a medias, y el proyecto la superó por otro camino)

- **Guía.** GUIA l. 88: correr la prueba sobre la versión SIN el arreglo y guardar el rojo.
- **Proyecto.** «línea base roja» aparece en 2 documentos con uso real (AUDIT_S134 l. 141, HYPOTHESIS_LOG l. 1490).
  La regla B del protocolo exige cerrar cada hallazgo con una guarda (PROT l. 267 a 268), pero no exige ver esa guarda
  en rojo. A92 (`CLAUDE.md:1270`) es el costo: una guarda siguió en verde después de que desapareció la llamada que
  vigilaba. El proyecto respondió con baterías de mutaciones con control (MEM_feedback_s156 l. 17 a 20), y hoy
  VER_COMP H3 (l. 103 a 120) encontró cuatro mutaciones de una regla sellada que ninguna prueba atrapa.
- **Qué cambiaría.** Que toda guarda nueva nazca con su rojo registrado (la mutación del cableado que vigila) y que la
  regla B diga «guarda vista en rojo», no sólo «guarda».

### 2.4 Pruebas con azar (aplica a medias, y con un matiz, ver §4 C1)

- **Guía.** GUIA l. 76 a 77: marcar la prueba como variable y exigir ×3, o fijar la semilla.
- **Proyecto.** VER_COMP H2 (l. 83 a 101): la calibración con semilla fija cayó justo sobre el tope en un estrato
  (11 falsos de 200 contra un tope de 10) y apagaba mejoras reales; con 20 semillas el mismo estadístico falla 1 de 20.
  Se corrigió hoy con 1.000 repeticiones y semilla sellada antes del tag (commit `b3baa45b5`). El protocolo no tiene una
  regla general de semillas (lo leí entero).

### 2.5 El instrumento va al repo el mismo día (aplicado hoy, violado en el pasado y todavía citado)

- **Guía.** GUIA l. 62 a 63.
- **Proyecto.** El AUC 0,859 de A83 «no tiene script en el repo» (`CLAUDE.md:1114`); A84 se apoya en
  `scratchpad/probe_ctx_cluster_s117.py` (`CLAUDE.md:1148`); el ejemplo numérico de A87 quedó sin verificar porque sus
  fuentes «no dicen qué campo midieron ni con qué script» (`CLAUDE.md:1192` en adelante). Los verificadores de hoy
  cumplen (cada uno lista scripts y salidas en su carpeta, por ejemplo VER_pareo_modis l. 10 a 16).
- **Qué cambiaría.** Barrer las reglas vinculantes que todavía se apoyan en un número sin script y rebajarlas (ya se
  hizo con A83 y A87; el censo de S145 dio 50 de 89 cierres sin respaldo citable, PLAN_AUDITORIA_S146 l. 44 a 47).

### 2.6 Todo arreglo trae su regresión sobre la familia completa (aplica a medias)

- **Guía.** GUIA l. 59 a 61 (familia completa) y patrón 6, «un arreglo que cubre un camino de dos» (l. 37).
- **Proyecto.** A102 (`CLAUDE.md:1381`): un detector se arregló y la expresión vieja siguió un mes en tres copias.
  A118 (`CLAUDE.md:1562`): un flag de geometría llegó al primer pase y no al segundo, y el A/B dio cero. Hoy VER_chillan_modis
  §3 (l. 54 a 58) encontró lo mismo en un contrafactual (ver §3, L4). La regla existe desde S141 y S148, pero el patrón
  reaparece en experimentos, no sólo en arreglos.

### 2.7 Cobertura primero sin verificación de lo menor (tensión, ver §4 C6)

- PLAN_AUDITORIA_S158 l. 100 a 101 manda al verificador sólo gravedad 3 o más; AUDIT_S158 l. 76 a 78 deja sin verificar
  los de gravedad 1 y 2. PROT l. 270 a 276 midió que ese inventario sin verificar es lo que la auditoría siguiente
  reporta como nuevo.

---

## 3. Lecciones del proyecto que la guía no tiene, como reglas generales

Formato: regla · origen · ejemplo · dónde iría · valor. «Sección nueva» quiere decir que no cabe en ninguna de las
ocho actuales. Ordenadas por familia, no por valor.

### Familia A: nulos y controles

**L1. Un nulo que corre el mismo código en el mismo proceso no mide ruido: es una identidad, y da cero por construcción.**
- Origen: VER_mxd03_prereg H1 (l. 27 a 48): el gemelo K2 «corre el mismo código en el mismo proceso: no puede discrepar
  de K (M: 85 de 85), así que "ruido = 0" no es una medición, es la definición»; con ruido 0 una sola pasada neta sobre
  49 decide el veredicto. VER_n l. 99 lo llama «nulo débil: mismo proceso determinista, no vería un envoltorio roto».
  COMPROBADO al leerlo.
- Ejemplo: un A/B cuyo veredicto exigía que el brazo nuevo superara el ruido medido por un gemelo idéntico: el ruido
  daba 0 y cualquier diferencia de una unidad decidía.
- Regla: el ruido se mide con perturbaciones de la misma clase que el efecto (varias semillas de una perturbación de
  tamaño comparable) y sólo sobre las unidades donde el resultado puede cambiar. El gemelo idéntico se conserva como
  control de identidad (prueba el envoltorio), nunca como nulo.
- Dónde: GUIA §3, junto a «control negativo». Valor: **alto**.

**L2. Un control se valida midiendo su nulo, no razonándolo; y un control que da verde sobre un instrumento ya refutado está roto.**
- Origen: A110 (`CLAUDE.md:1422` a 1441): cuatro controles «obvios» fallaron seguidos (un punto reflejado medía
  textura, nulo +0,1014; otro era ciego por construcción a las fuentes permanentes; un intercambio de roles atenuaba el
  sesgo cinco veces; un estrato hermano contenía la señal). AUDIT_S146 V-16 (l. 134 a 137): «C1 es una identidad y los
  nulos N1 y N2 están vacíos por construcción».
- Ejemplo: un control de «sitio espejo» parecía cancelar el sesgo y medido daba +0,10 sin nada que detectar.
- Dónde: GUIA §3. Valor: **alto**. (Matiza el «≈ 0» de GUIA l. 90, ver §4 C2.)

**L3. Un nulo que mueve al azar algo que ya coincide da «empeora» siempre; el nulo correcto sortea el signo de la diferencia de errores, por bloque.**
- Origen: MEM_feedback_s157 l. 19 a 21. Ejemplo: sortear el signo del efecto alejaba de la referencia a las unidades
  que ya calzaban. Dónde: GUIA §3. Valor: **medio**.

**L4. Contar como atrapada sólo la mutación que falla por aserción, con una mutación de control que sólo hace caer el programa.**
- Origen: MEM_feedback_s152 l. 11 a 18 (cuatro mutaciones contadas como atrapadas porque el evaluador se caía);
  MEM_feedback_s156 l. 17 a 20 (leer el JUnit XML y exigir `AssertionError`); VER_COMP H3 (l. 103 a 120: cuatro
  mutaciones de una regla sellada no atrapadas; el corredor tiene control sin mutar y tres mutaciones sí atrapadas).
- Ejemplo: una batería «completa» cuyas mutaciones «atrapadas» eran excepciones de clave faltante.
- Dónde: GUIA §3, como la forma madura de la línea base roja. Valor: **alto**.

**L5. Toda métrica de decisión pasa antes por un placebo: un tratamiento falso de efecto conocido (una ganancia uniforme, un desplazamiento sin información) no puede aprobar.**
- Origen: AUDIT_S158 l. 44 a 45 («D = 1,10·K da MEJORA en dos estratos que deciden [...] Mientras K esté bajo MIROVA,
  cualquier subida gana»); R2-8 en AUDIT_S158_R2 l. 160; VER_COMP respuesta 2 (l. 165 a 170: 0 de 56 ganancias
  uniformes y 0 de 54 por volcán dan MEJORA con el comparador); VER_mxd03_prereg H2 (l. 50 a 66: con el sistema bajo
  la referencia en 77 de 80 pares, un 3 % de baja uniforme bloquea).
- Regla general: si el sistema está sistemáticamente de un lado de la referencia, cualquier perturbación monótona mueve
  todos los pares en la misma dirección y una prueba de signo la declara significativa. El placebo lo destapa.
- Dónde: GUIA §3 o sección nueva «Experimentos comparativos». Valor: **alto**.

**L6. Declarar la curva de poder antes de leer: un «sin efecto» no distingue «no hay efecto» de «hay efecto con dispersión».**
- Origen: VER_COMP H1 (l. 38 a 81): con dispersión por unidad de 0,10 en log10 el comparador deja el «cumple» en 1 de
  12 aunque el mecanismo cierre la mitad de la brecha; sin comparador, 12 de 12. PROT T8 (l. 104 a 110): «una mediana
  sin intervalo no decide nada». MEM_feedback_s146 l. 8 a 12: barajar las etiquetas dentro de cada estrato antes de
  fijar el umbral; «78 de 78» lo cumplía el azar.
- Ejemplo: un criterio «no perder noches» que cualquier brazo, incluso uno malo, cumplía.
- Dónde: sección nueva «Experimentos comparativos» (o GUIA §3). Valor: **alto**.

### Familia B: poblaciones, muestras y denominadores

**L7. Una población elegida porque el sistema ya la marcó está condicionada al resultado: cualquier perturbación apaga más de lo que enciende.**
- Origen: VER_m l. 50 a 54 («La población está condicionada a que A publicó [...] Cualquier perturbación de la posición
  sobre records elegidos por pasar un umbral apaga más de lo que enciende (A109). Lo que se puede leer es el pareo con
  MIROVA (7 de 9), no el saldo»). COMPROBADO al leerlo. A109 (`CLAUDE.md:1410` a 1421) es la forma hermana: medir una
  detección contra un producto derivado del mismo insumo la infla (+0,1214 contra +0,0786 con otro insumo de la misma
  noche).
- Regla: si la muestra se eligió por el resultado del sistema, el saldo de cambios no tiene dirección legible; se lee
  sólo contra una vara externa, o se muestrea también lo no marcado.
- Dónde: GUIA §7 o la sección nueva de experimentos. Valor: **alto**.

**L8. Antes de muestrear y ponderar, preguntar si el cambio sólo puede actuar sobre un subconjunto contable; si se puede, se cuenta entero. Y todo estimador se compara con su techo físico.**
- Origen: VER_n afirmación 1 (l. 24 a 54): la variante «no toca la detección» (mismo conjunto de píxeles en 391 de
  391), así que sólo puede encender donde ya hay un cúmulo no publicado; esos son 119 de 5.476 y el estimador ponderado
  daba 152,3, sobre el máximo posible; la muestra sacó 6 elegibles de 140 cuando en la población son 60 de 5.476; un
  estrato con 3 de 6 sorteados elegibles y peso 20,8 cada uno estimaba 62,5 donde el estrato entero tiene 20. El censo
  (`experiments\_s159\n\INFORME.md` l. 266) dio ΔE **+12**, no +104. COMPROBADO.
- Ejemplo: un efecto «del orden de cien» que contado era una decena.
- Dónde: GUIA §7. Valor: **alto**.

**L9. Comparar unidades con el mismo número de oportunidades: una unidad con dos registros que «publica si publica cualquiera» tiene dos chances contra una.**
- Origen: VER_pareo_modis l. 83 a 86: el exceso 13 de 147 contra 2,63 % tenía p 0,0002 tratado como una chance; con
  dos chances se esperan 7,6 y p queda en 0,043. Dónde: GUIA §7. Valor: **medio**.

**L10. Un conteo absoluto sobre un corpus vivo no es comparable entre sesiones; todo número lleva denominador y ventana temporal de los datos.**
- Origen: A90 (`CLAUDE.md:1249` a 1268; el corpus creció hacia atrás por un relleno histórico y el conteo pasó de
  2.527 a 9.196 con la tasa plana); A93 (`CLAUDE.md:1293`: «24 de 24 verdes» leído como universo completo cuando la
  ventana era un tramo); PRE l. 41 a 42 lo exige en cada medición. AUDIT_S158_R2 §6 (l. 225): 235 de 855 contra 595 de
  2.359, «las dos dicen 25 a 27 %».
- Dónde: GUIA §3 o §7. Valor: **alto**.

**L11. El impacto se cuenta en la unidad en que el usuario lo vive; un caso de referencia prueba que el mecanismo existe, no su tamaño.**
- Origen: A94 (`CLAUDE.md:1312` a 1331): el defecto afectaba ~9.350 registros y una noche útil de 946. AUDIT_S158_R2 §6
  (l. 226): «0 noches perdidas» contra «55 de 266 noches sin el sensor», unidades distintas y compatibles.
- Dónde: GUIA §6 (priorización). Valor: **alto**.

**L12. Una métrica cuya ventana cruza un cambio de régimen mezcla dos sistemas, y la frontera hay que ponerla en la fecha de los datos, no en la del cambio de código; un reproceso la mueve.**
- Origen: A104 (`CLAUDE.md:1387` a 1389: 62,1 % antes y 87,1 % después); R2-12 en AUDIT_S158_R2 l. 164 y l. 230 (todo
  el corpus se reprocesó con el detector nuevo, así que la fecha de observación ya no separa detectores).
- Dónde: GUIA §7. Valor: **alto**.

**L13. Un recurso de resiliencia que salta sin fallar produce brazos incomparables en verde: antes de comparar dos corridas, comparar el conjunto de unidades procesadas.**
- Origen: MEM_feedback_s135 l. 8 a 23 (un brazo procesó 149 de 203 pasadas por un cortacircuito y sus «pérdidas»
  eran días que no miró); A108 (`CLAUDE.md:1406` a 1409); MEM_feedback_s157 l. 13 a 15 (326 pasadas perdidas en trozos
  verdes); AUDIT_S158 l. 41 a 43 («Cero gránulos se registra como "Cobertura: completa"»).
- Diferencia con lo que la guía ya tiene: PLANT P9 y B11 hablan de fallos silenciosos del sistema; esto es la
  consecuencia para un experimento comparativo.
- Dónde: sección nueva de experimentos, o GUIA §7. Valor: **alto**.

**L14. La calidad de la referencia externa cambia con el tiempo; antes de elegir una ventana, mirar desde cuándo sirve cada canal, y desconfiar de una fuente que puede perder datos hacia atrás.**
- Origen: A119 (`CLAUDE.md:1586` en adelante); R2-13 en AUDIT_S158_R2 l. 165 (el proveedor devuelve hoy cero
  gránulos de un día que producción procesó). Dónde: GUIA §7. Valor: **alto** para todo proyecto con vara externa.

**L15. «Sin efecto» no es lo mismo que «efectos que se cancelan»: reportar la distribución, no la mediana; y estratificar antes de agregar (paradoja de Simpson).**
- Origen: PROT T3 (l. 57 a 63: mediana 0,000 que promediaba +0,11 y −0,10); A83 (`CLAUDE.md:1117`: AUC global 0,762 y
  0,554 dentro de cada estrato). Dónde: GUIA §7. Valor: **alto**.

**L16. Una palanca que satura la métrica esconde a todas las demás: si la métrica casi no varía entre estratos físicos, algo la satura y hay que sacarlo antes de medir otra cosa.**
- Origen: A114 (`CLAUDE.md:1498` a 1513): con un camino encendido todo daba 80 a 92 %; un A/B corrido así «no midió
  nada». Relación: PLANT 8b ya tiene «el delator es un número que no se mueve» (l. 335 a 339), pero para un instrumento
  muerto, no para un sistema saturado. Dónde: GUIA §7. Valor: **alto**.

### Familia C: experimentos y pre-registro

**L17. Un contrafactual que cambia una etapa cuando el interruptor real gobierna dos mide una configuración que no existe.**
- Origen: VER_chillan_modis §3 (l. 54 a 58): «F2 aplica `min` sólo al primer pase, una configuración que no existe en
  producción, porque el flag gobierna los dos pases (l. 942 y 996). El brazo MIN, que es el flag de verdad, detecta [...]
  por sí solo». También VER_chillan_modis l. 51 a 53 confirma que el contrafactual de banda sí cambió sus cinco
  consumidores. A118 (`CLAUDE.md:1562`) es el mismo defecto en un arreglo. COMPROBADO.
- Regla: antes de un contrafactual, listar con búsqueda todos los consumidores del valor que el interruptor cambia, y
  aplicar el cambio a todos o declarar por qué no.
- Dónde: GUIA §1 patrón 6, ampliado a experimentos. Valor: **alto**.

**L18. Pre-registrar: regla de decisión, estimador, nulo y población escritos y commiteados antes del dato; el verificador comprueba con `git diff` que no cambiaron, y lo agregado después se rotula post hoc.**
- Origen: VER_n l. 14 a 20 («sin cambios [...] después de `0b20eb1f3`, comprobado con `git diff` [...] No
  pre-registrado: el oráculo contado como brazo»); VER_mxd03_prereg H3 (l. 68 a 79: «un candado que se reescribe
  después del sello es un criterio no pre-registrado»); AUDIT_S146 V-16 (l. 136 a 137: «el orden del pre-registro no es
  demostrable, todo estaba sin commitear»). La guía no menciona el pre-registro en ninguna parte (la leí entera).
- Dónde: sección nueva «Experimentos comparativos». Valor: **alto**.

**L19. El nombre del veredicto no puede prometer más que lo que la regla prueba.**
- Origen: VER_mxd03_prereg H6 (l. 112 a 123): «CUMPLE» se obtenía con el brazo idéntico al control; se propuso «CUMPLE
  SIN DAÑO». Es la regla de la etiqueta de GUIA l. 99 a 100 aplicada a los veredictos de un experimento.
- Dónde: GUIA §3, junto a la regla de la etiqueta. Valor: **medio**.

**L20. La tolerancia de un control tiene que ser menor que el efecto que decide, y estar atada a la condición que la justifica.**
- Origen: VER_mxd03_prereg H9 (l. 149 a 158: el 2 % tolerado son hasta 109 unidades, más que las 49 que deciden);
  MEM_feedback_s152 l. 12 a 18 (una tolerancia admitía diferencias donde su justificación física no actuaba).
- Dónde: GUIA §3. Valor: **medio**.

**L21. Medir el efecto de un cambio antes de llamarlo arreglo.**
- Origen: A116 (`CLAUDE.md:1530` en adelante): un cambio «cierto en la forma» movía 0 de 4.448 registros.
- Diferencia con la guía: GUIA l. 100 dice «actividad ≠ resultado» para lo que ve el usuario; esto es para el propio
  arreglo. Dónde: GUIA §6. Valor: **medio**.

**L22. Si un criterio necesita un umbral, se le pregunta a la referencia antes que al dueño; y cuando la vara es la referencia externa y cuando es la verdad, los criterios son distintos, no el mismo con otro umbral.**
- Origen: A115 (`CLAUDE.md:1514` a 1529): un umbral inventado disparaba en 94 de 96 casos fuera del universo que la
  referencia puede arbitrar. A54 (`CLAUDE.md:760`): 95 % de los «falsos positivos» contra la referencia eran señal real
  que la referencia no publica. Relación: PLANT T1 «reflexividad» (l. 64 a 90) intuye lo mismo.
- Dónde: GUIA §2 o sección nueva. Valor: **alto**.

**L23. Una regla que se sospecha rota recibe la misma verificación que un arreglo: predecir qué vería cada modelo y buscar un experimento natural que los separe.**
- Origen: VER_pareo_modis §2 (l. 39 a 61): la regla de pareo se creía defectuosa; dos plataformas con órbitas invertidas
  en el tiempo coinciden en el lado (57 a 3 y 70 a 0), lo que descarta toda explicación por orden temporal; y el modelo
  alternativo predecía 28,7 alertas donde se observaron 0, con control 25,4 contra 24. Ensanchar la tolerancia
  empeoraba (l. 34 a 37: el pareo ancho sólo duplica). COMPROBADO: la regla estaba bien.
- Dónde: GUIA §2 (como contraparte de la regla 2, «una ausencia no se valida sola»). Valor: **medio a alto**.

### Familia D: independencia y verificación

**L24. Independencia de verdad: veredictos propios commiteados antes de leer la ronda anterior, otro modelo replica, y un port se valida contra el intérprete original, no contra otro port.**
- Origen: AUDIT_S158_R2 l. 8 a 14 (veredictos en `VEREDICTOS_ANTES_DE_COMPARAR.md` commiteados antes de abrir la
  primera ronda; Fable replica a Opus; los verificadores «no habían encontrado nada de lo que verifican»);
  MEM_feedback_s158 l. 11 a 14 (dos ports coincidían entre sí sin que nadie los corriera contra el original; GNU
  Octave lo hizo en una hora). MEM_feedback_s146 l. 10 a 12: cinco reproducciones con el mismo banco probaban que el
  banco es determinista, no que midiera.
- Dónde: GUIA §5. Valor: **alto**. (Matiza GUIA §2 regla 1, ver §4 C3.)

**L25. El verificador escribe sus caminos de ruptura antes de leer el informe del auditor.**
- Origen: VER_chillan_modis l. 7 a 11 (seis caminos enumerados antes de leer); VER_n l. 4 a 5 («Leí el pre-registro,
  pensé cómo romper cada afirmación y recién después leí el INFORME»). Dónde: GUIA §5. Valor: **medio**.

**L26. Todo VERIFICADO LIMPIO dice contra qué vara se verificó.**
- Origen: PLAN_AUDITORIA_S158 l. 44: S146 dio por verificada una tabla contra el paper de un sensor, y contra el
  código de otro esa verificación no podía fallar. Dónde: GUIA §5 (en el formato del preámbulo). Valor: **medio a alto**.

**L27. Medir con el predicado literal que usa el producto, ejecutado por el mismo intérprete, nunca con una reconstrucción.**
- Origen: A97 (`CLAUDE.md:1359` a 1360); VER_m l. 7 a 9 y VER_n l. 10 a 12 ejecutan el predicado del tablero con node.
- Relación: GUIA §0 dice «el sistema corriendo»; esto lo vuelve operativo cuando el sistema es un filtro de
  publicación. Dónde: GUIA §0 o §3. Valor: **alto**.

**L28. Cuatro definiciones de «lo mismo» entre frentes son cuatro instrumentos: la definición de cada término de la vara y la tolerancia de pareo van en el bloque común.**
- Origen: AUDIT_S158_R2 §7 (l. 254 a 256): «Cuatro definiciones de "alerta de MIROVA" entre frentes, y pareos de 20, 8,
  5 minutos y minuto exacto». Dónde: GUIA §5. Valor: **medio a alto**.

**L29. Dos escalares que coinciden no identifican el mismo objeto; comparar en el espacio completo y con estadísticos robustos de la dirección.**
- Origen: A93 (`CLAUDE.md:1293`: la diferencia de dos radios es una cota inferior de la distancia entre puntos, 0,21 km
  contra una cota real de 15,6 km); A107 (`CLAUDE.md:1402`); A61 (`CLAUDE.md:803`) y A70 (`CLAUDE.md:943`: la mediana
  del desplazamiento y la distribución de rumbos, no la media de la distancia). Dónde: GUIA §7. Valor: **medio**.

### Familia E: cierres, propagación y método de la auditoría

**L30. Un cierre apaga trabajo futuro y hereda las premisas de la lectura con que se derivó; sin respaldo citable es una creencia, y sin respaldo no es lo mismo que refutado.**
- Origen: A95 (`CLAUDE.md:1332`), A111 (`CLAUDE.md:1442` a 1461; censo: 50 de 89 cierres sin respaldo citable);
  PROT T6 (l. 83 a 92: prioridad a lo que dice «cerrado», «agotado», «no reabrir»); PROT «Regla de salida» (l. 151 a
  164: falso, obsoleto, sin respaldo y confirmado se tratan distinto; nunca borrar).
- Relación: GUIA §2 regla 9 dice que la lista de «ya verificado» envejece; esto agrega que los cierres son el objeto
  de auditoría de mayor rendimiento y cómo clasificarlos. Dónde: GUIA §2. Valor: **alto**.

**L31. Una rebaja se propaga a todo lo que la cita, en el mismo cambio, con una marca al inicio del pasaje y el texto viejo conservado; primero donde se lee primero.**
- Origen: A113 (`CLAUDE.md:1476` a 1497: de 50 cierres sin respaldo, 27 se verificaron; el defecto dominante fue la
  falta de propagación); AUDIT_S158_R2 §7 (l. 251 a 253: propagación incompleta otra vez, U1 a U14).
- Dónde: GUIA §6 (al cerrar). Valor: **alto**.

**L32. El rendimiento de una auditoría es del eje de comparación nuevo, no de la profundidad: prohibido repetir el barrido general; cada auditoría estrena un eje y lo declara.**
- Origen: PROT l. 226 a 248 (las cuatro auditorías con menos de 20 % de eje nuevo produjeron sólo deuda documental; las
  cinco con 50 % o más, todos los cambios del pipeline). PROT l. 278 a 302 (registro de ejes; los exógenos, 4 usos en
  127 sesiones, encontraron algo las 4 veces).
- Dónde: GUIA §4 o §8. Valor: **alto**. Complementa PLANT «inventario de cobertura» (l. 240 a 254), que pide la tabla
  de lo mirado pero no mide el rendimiento por eje.

**L33. Cerrar cada hallazgo con una guarda, y empezar la auditoría siguiente por los pendientes de la anterior.**
- Origen: PROT reglas B y C (l. 252 a 276): nueve hallazgos se redescubrieron en más de una auditoría, uno de ellos
  cuatro veces; la única auditoría que cerró con guardas fue la única sin reincidencias.
- Dónde: GUIA §6. Valor: **alto**.

**L34. «Esto no se usa / no está en ningún lado» es la afirmación que más falla, y falla del lado del auditor: el nombre en el punto de uso no es el de la definición.**
- Origen: A89 (`CLAUDE.md:1225` a 1248) y PROT T9 (l. 189 a 205): cinco falsos negativos en una sesión, las cinco veces
  del auditor; tres formas (parámetro con otro nombre, clave leída de otra sección, llamada calificada o renombrada).
- Relación: GUIA §2 regla 2 dice «una ausencia no se valida sola»; esto da el mecanismo más frecuente y la búsqueda
  correcta (trazar cómo lo lee el código). Dónde: GUIA §2. Valor: **alto**.

**L35. Una guarda que verifica por subcadena da verde por coincidencia cuando el nombre viejo queda dentro del nuevo.**
- Origen: A92 (`CLAUDE.md:1270` a 1292). Dónde: GUIA §7. Valor: **medio**.

**L36. Buscar capacidad construida y no conectada: lo que sólo llaman las pruebas es la señal más fuerte.**
- Origen: PROT T5 (l. 73 a 81: una función escrita 26 sesiones antes para el problema exacto, nunca cableada).
  Dónde: GUIA §1, como octavo patrón. Valor: **medio**.

**L37. Una afirmación con N = 1 que es condición necesaria no es causa general; y una hipótesis sobre un tercero no se escribe como hecho del tercero.**
- Origen: AUDIT_S158_R2 §6 (l. 224: «la primera convirtió una necesidad en causa general (M1 H4)»; l. 229: «la primera
  escribió una hipótesis como hecho de NASA»); AUDIT_S158 §2 (l. 82 a 90: cuatro afirmaciones del orquestador cayeron,
  «inferencias mías que ningún instrumento había puesto a prueba»). Dónde: GUIA §2. Valor: **alto**.

**L38. Un vigilante ciego no da error, da verde: cada insumo que puede morir necesita su propio aviso, y el umbral se mide contra los datos antes de fijarlo.**
- Origen: MEM_feedback_s156 l. 13 a 16. Relación: PLANT P9 y B11 son la versión del sistema; esto es la del
  instrumento de vigilancia. Dónde: GUIA §3. Valor: **alto**.

**L39. Un perfil o configuración que se define en relación con otro se vigila por la relación, no por un valor fijo.**
- Origen: A117 (`CLAUDE.md:1544` a 1561): el laboratorio fue más ciego que el instrumento que estudia durante 17
  sesiones, con una prueba en verde que fijaba el valor viejo. Dónde: GUIA §1 (patrón 3, lista de clientes) o §7.
  Valor: **medio**.

**L40. Una suite corriendo en segundo plano mientras se edita no es línea base; el delator es que las fallas cambian de identidad entre corridas del mismo estado.**
- Origen: A112 (`CLAUDE.md:1462` a 1475). Relación: GUIA §7 ya tiene «dos builds simultáneos sobre el mismo árbol»
  (l. 198). Dónde: GUIA §7, junto a esa línea. Valor: **medio**.

**L41. «0 checks» recién abierto un PR es SIN DATO, no verde.**
- Origen: A39 enmienda S142 (`CLAUDE.md:1614` a 1616). Dónde: GUIA §3 (SIN DATO). Valor: **medio**.

**L42. Un flag apagado o una métrica que volvió a banda no prueban que el problema se fue: verificar el mecanismo en los registros.**
- Origen: A87, lección de método (`CLAUDE.md:1192` en adelante, texto original conservado al final de la regla; el
  ejemplo numérico quedó SIN VERIFICAR). Dónde: GUIA §2. Valor: **medio**.

**L43. El bloque canónico que se copia sin leer también propaga sus errores: revisarlo al inicio de cada plan.**
- Origen: PRE l. 9 a 11: la carpeta de los scripts estaba mal desde S133 y se parchó sólo en los prompts de S138 y
  S149. Dónde: GUIA §5 (junto al preámbulo). Valor: **medio**.

**L44. El informe del auditor cierra con «Lo que no pude medir» y «Fuera de alcance», además de VERIFICADO LIMPIO.**
- Origen: PLAN_AUDITORIA_S158 l. 136 a 141; AUDIT_S158 §7 (l. 132 a 136); VER_mxd03_prereg l. 189 a 190. Dónde: GUIA
  §5 (formato). Valor: **medio**.

**L45. Una cita de un documento se lee sobre la página renderizada, no sobre la capa de texto; y la cita no puede agregar números que el documento no trae.**
- Origen: A95 (`CLAUDE.md:1332` y siguientes: la capa de texto convierte `<` en coma y `=` en otro símbolo);
  VER_mxd03_prereg H4 (l. 84 a 96: el borrador le atribuía al paper «sobre ~50°» y el paper trae sólo «>30°» para otra
  cosa). Dónde: GUIA §2 o PLANT fase 4. Valor: **medio** (alto en proyectos que citan papers o normas).

**L46. Las esperas y los verificadores van en primer plano; un agente que entrega con su verificación en segundo plano entrega sin resultado.**
- Origen: MEM_feedback_s157 l. 22 a 24. Dónde: GUIA §5 (agentes largos). Valor: **medio**.

**L47. Una aprobación del dueño reenviada entre sesiones no vale; el sello se registra donde el dueño lo dijo, con su frase.**
- Origen: MEM_feedback_s157 l. 16 a 18. Dónde: GUIA §6. Valor: **bajo a medio**.

**L48. La evidencia con derechos de autor (páginas renderizadas, descargas) no va al repo público, aunque el instrumento sí.**
- Origen: MEM_feedback_s158 l. 15 a 17 (52 páginas llegaron a una rama pública). Dónde: GUIA §2 regla 7, como
  excepción. Valor: **medio**.

**L49. Anclar «hoy» a la hora del servidor en sesiones largas.**
- Origen: A86 (`CLAUDE.md:1185`). Dónde: GUIA §7. Valor: **bajo**.

---

## 4. Contradicciones y reglas de la guía que el proyecto matizó

**C1. «Exigir ×3 o fijar la semilla» (GUIA l. 76 a 77) no son equivalentes.** Fijar la semilla hace reproducible el
veredicto, pero si el estadístico cae cerca de un tope, la semilla decide el lado: VER_COMP H2 (l. 85 a 96) midió 11
falsos de 200 contra un tope de 10 con la semilla sellada, y 1 de 20 con semillas distintas. La salida que adoptó el
proyecto es muchas repeticiones (1.000) y la semilla sellada antes de leer (commit `b3baa45b5`). Propuesta: «fijar la
semilla da reproducibilidad, no validez; si la decisión está cerca del borde, subir las repeticiones hasta que la
semilla no decida, y sellarla antes del dato».

**C2. «Control negativo (la misma medición sin el fenómeno, ≈ 0)» (GUIA l. 89 a 90).** El proyecto midió controles
negativos que no daban ≈ 0 (el punto reflejado, +0,1014, A110 `CLAUDE.md:1425`) y controles que daban exactamente 0
porque eran identidades (VER_mxd03_prereg H1 l. 30 a 33; AUDIT_S146 V-16 l. 134 a 135). Un «≈ 0» esperado acepta el
segundo caso como éxito. Propuesta: «el nulo del control se mide; un cero exacto es sospechoso hasta mostrar que el
control podía dar distinto de cero».

**C3. «Verificar con dos herramientas independientes» (GUIA l. 48 a 49) no basta tal como está escrita.** Dos ports
escritos leyendo el mismo texto coincidían entre sí y podían compartir el error (MEM_feedback_s158 l. 11 a 14); cinco
reproducciones con el mismo banco probaban determinismo (MEM_feedback_s146 l. 10 a 11). PLANT 8c (l. 341 a 357) ya lo
dice para mediciones; la guía no lo trae. Propuesta: subir 8c a la guía y agregar «la vara final es el original
cuando existe un intérprete».

**C4. «La fuente de verdad es el sistema corriendo» y «mirar la salida renderizada» (GUIA l. 17 a 22; PLANT l. 452 a
467).** En VRP Chile el sistema corriendo (el tablero) es necesario pero el árbitro es una referencia externa, que
tiene su propia política de publicación (A54, `CLAUDE.md:760`) y su propia calidad por tramo (A119). Y la salida
renderizada de la referencia resultó peor árbitro que su número para una pregunta concreta: «S131 refutó el GeoTIFF
como árbitro de POSICIÓN (error mediano 4,80 km [...] pierde contra el nulo)» (PROT l. 293). Propuesta: «mirar la
salida renderizada es obligatorio, pero también es un instrumento y se valida contra un nulo antes de que arbitre».

**C5. «Repetir dos veces antes de creer un rojo que cambió» (GUIA l. 60 a 61).** Vale contra instrumentos inestables;
en un sistema determinista repetir sólo prueba determinismo (MEM_feedback_s146 l. 10 a 12). Propuesta: decir para qué
sirve la repetición y pedir un camino independiente cuando el sistema es determinista.

**C6. «Cobertura primero; el filtrado es de otro» (GUIA l. 138 a 139) produce inventario sin verificar.** El proyecto
midió que ese inventario es lo que la auditoría siguiente reporta como nuevo (PROT l. 270 a 272: 19 hallazgos «sin
verificación individual» en S121, 9 en S125), y el plan S158 sigue mandando al verificador sólo gravedad 3 o más
(PLAN_AUDITORIA_S158 l. 100 a 101; AUDIT_S158 l. 76). No es contradicción, es una consecuencia que la guía no nombra.
Propuesta: «todo lo no verificado se publica con su conteo y es la puerta de entrada de la auditoría siguiente» (regla
C del protocolo, L33).

**C7. «Un instrumento que sirvió para medir un hallazgo va al repo el mismo día» (GUIA l. 62 a 63).** Matiz de
MEM_feedback_s158 l. 15 a 17 y de los verificadores de hoy, que borran sus temporales grandes al terminar
(VER_pareo_modis l. 5 a 6): el script va al repo; la evidencia con derechos o pesada (páginas renderizadas, espejos de
datos), no.

**C8. Sin contradicción, pero con brecha de alcance: la guía no tiene una sección de experimentos comparativos.** De las
lecciones de §3, L5, L6, L7, L8, L13, L17, L18 y L20 son sobre A/B y pre-registros, que la guía (escrita desde
ARSAND, donde se audita un sistema interactivo) no trata. Es la mayor parte del valor que VRP Chile le puede devolver.

---

## Comprobación de este archivo

Guiones largos y medios: 0 y 0, contados con Python sobre este archivo (conteo de los caracteres U+2014 y U+2013).
