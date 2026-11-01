# Verificación de PREREGISTRO_B2.md versión 2 (V375-B2, S162)

- Hora del servidor al empezar: Sat, 24 Oct 2026 19:35:18 GMT; al terminar: 19:57:12 GMT (`gh api -i repos/MendozaVolcanic/VRP-chile`, header Date).
- Commit revisado: `7ff23cc3a` (el HEAD del worktree es `6adbaac66`, que sólo agrega 10 líneas a `tasks/LOOP_VIIRS375.md`). Modelo: Sonnet 5.5, contexto limpio.
- Carpeta de trabajo: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s162-viirs375-c1b864\experiments\_s162_v375\b2\verificador_v2\`. Las grillas falsas (unos 300 MB) quedaron en el scratchpad `C:\Users\nmend\AppData\Local\Temp\claude\C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile--claude-worktrees-s162-viirs375-c1b864\3314638d-6b0b-401c-8eb1-92df9921586d\scratchpad\v2\` y no se publican.
- NO miré: `probe_v375.py` por dentro, `brazos.py` ni la física del port; la cobertura del marco contra MIROVA (usé `cobertura_marco.json`, COBERTURA OK); el código de `pipeline/` (sólo comprobé que `533398f8f` y `ca034d66e` no difieren en `pipeline/`); nada de red ni de Earthdata. Las pasadas reales de B2 no existen: todo lo que dice «fabricado» sirve para probar cableado, no dice nada del port.
- Nada editado fuera de mi carpeta. Sin commits, stash, push, workflows ni credenciales. C: 41 GB y D: 9,7 GB libres (sobre 3 GB).

## En una pantalla

1. La muestra se sostiene: 1.200 pasadas neg_resto, todas del marco congelado, disjuntas de S159 y de S162, estratificadas volcán x cenit con pesos 2,72 a 2,83; el sha256 se reproduce (`6328988b…019a`) y el workflow es idéntico al sellado salvo nombre, trozos y ruta.
2. El evaluador «decide B2 sola» hace lo declarado: con 1.200 pasadas fabricadas mi cuenta a mano da el mismo neg_resto, ponderado e intervalo que la salida (18 de 1.200, [0,00951; 0,02359], igual a 15 cifras), y los arreglos pedidos por el verificador v1 (F1, F4, F5, F6) quedaron bien atendidos.
3. Lo más grave: ningún control prueba que el port esté VIVO en la corrida de B2 (los controles de vida leen S159 y S162). Una corrida de B2 con el port muerto da 0 de 1.200, «INSTRUMENTO OK» y SILENCIO ACOTADO BAJO K; lo reproduje (`fakeC.txt`). Falta un control positivo dentro del lote.
4. El «93 %» de probabilidad de decidir es condicional a la tasa puntual de 1,16 %; integrando la incertidumbre de 4 de 389 baja a 0,74 a 0,80. Y la cobertura por lote sólo avisa: con 10,8 % sin dato la salida igual imprime SILENCIO ACOTADO BAJO K (el texto dice «se informa y no decide»).
5. La salida trae tres lecturas de B (la de la unión en §3, la que decide, y 4b con el rótulo «S162»), y §7 dice que las secciones 4 y 4b no se leen cuando ahí viven el veredicto y el acuerdo que §5.2 exige: hay que fijar cuál línea es el veredicto.

## Caminos escritos ANTES de leer las salidas y el informe del v1 (resumen de `CAMINOS_ANTES.md`, escrito a las 19:35 GMT)

C1 «decide B2 sola» no es lo que hace el evaluador (global, V375-D y 4b sobre un conjunto sin protegidas; acuerdo de 4 claves). C2 neg_pub entra con otros pesos (N de meta 133 contra 113; rama «censo»). C3 la muestra no es disjunta, no es del marco o no es proporcional; sorteo del remanente ponderado con el N completo del estrato. C4 potencia y error en la frontera mal simulados (tasa pareja, neg_pub fijo, dependencia intra-noche). C5 el workflow corre otra cosa. C6 un control que no puede fallar (lote vacío, cobertura por lote, control positivo que no toca B2, port muerto). C7 régimen T/O1/O2 mezclado (A104). C8 re-ponderación al quitar no observadas.

## Veredictos por afirmación principal

| # | Afirmación | Veredicto | Grav. |
|---|---|---|---|
| 1 | 1.200 pasadas neg_resto nuevas, del mismo marco, ninguna de S159 ni S162, semilla 163, sha `6328988b…019a` | CONFIRMADO (`v_marco.py`, `rs.py`) | 0 |
| 2 | Proporcional al estrato volcán x cenit: pesos 2,72 a 2,83, ningún estrato sin pasadas; T 346 / O1 517 / O2 337; 41 partidas; 658 gránulos; quedan 1.678 | CONFIRMADO | 0 |
| 3 | Decide B2 sola en neg_resto más neg_pub de S162 (`--deciden S162b --neg-pub-de S162`) | CONFIRMADO EN PARTE: el cálculo es el declarado; la salida mezcla tres lecturas y las rotula mal (H4) | 2 |
| 4 | «La misma regla sellada», neg_pub como muestra de 113 | CONFIRMADO EN PARTE: es la cuenta que produjo el NO RESUELTO de S162; el §5 literal de B decía «neg_pub censo». Lo pidió la coordinadora y el texto lo declara | 1 |
| 5 | Con 1.200: 93 % de decidir con la tasa observada; 600: 59 %; 1.000: 88 %; 1.500: 98 % | CONFIRMADO EN PARTE: reproducido (0,928), pero condicional al punto 1,16 % (H2) | 2 |
| 6 | En la frontera (tasa real 2,54 %) declara ACOTADO en 1 a 3 % | CONFIRMADO: 1,7 % exacto (`v_potencia2.py`); depende de la tasa real de neg_pub (ver VERIFICADO LIMPIO) | 0 |
| 7 | El v1 (S162 más 600) declaraba ACOTADO en la frontera 11 a 20 % | CONFIRMADO EN PARTE: es el error CONDICIONAL a las 4 de 389 ya vistas; el incondicional del v1 es de ~2 % (H5) | 1 |
| 8 | Controles nuevos: cobertura por lote y lote vacío | CONFIRMADO EN PARTE: ambos funcionan (probados); el de cobertura avisa y no frena (H3) | 2 |
| 9 | El workflow corre lo mismo que V375-B | CONFIRMADO (diff ignorando CR: sólo nombre, rama, concurrencia, ruta, 48 trozos, `--nchunks 48`, nombre del artefacto) | 0 |
| 10 | Los siete controles de B §4 cubren esta corrida | REFUTADO en el alcance: ninguno prueba que el port viva en la corrida B2 (H1) | 3 |
| 11 | Costo 8,3 h de runner, ~90 min de reloj, ~140 MB | CONFIRMADO (1.200 x 25 s; 48/8 = 6 oleadas de ~14 min; 1.200 x ~110 kB); nota de 1.200 descargas (H7) | 1 |

## Estado de los hallazgos del verificador del v1

| v1 | Estado en el v2 | Cómo lo comprobé |
|---|---|---|
| F1 reutilizaba S162 para decidir | ATENDIDO: B2 sola decide en neg_resto; el tamaño sube a 1.200 para conservar potencia | `en_decide` (evaluar.py:806) y fakeA: la línea de la decisión «lotes S162b (DECIDE)» tiene neg_resto [18, 1200], sólo B2 |
| F2 segunda mirada sobredeclarada | ATENDIDO: se retira; con B2 sola el tamaño en la frontera es 1,7 % (más 0,3 % de la primera mirada, que ya se tomó) | `v_potencia2.py` |
| F3 potencia con tasa pareja | DECLARADO como SOSPECHA en §3; sigue sin medirse (H2, H6) | texto |
| F4 cobertura por lote | ATENDIDO en código (evaluar.py:598-604) y probado: 130 de 1.200 sin dato => AVISO por lote; sólo avisa (H3) | `fakeB.txt` línea 14 |
| F5 lote vacío | ATENDIDO (evaluar.py:810-815): sin artefactos de B2 => INVALIDO POR INSTRUMENTO | `sinb2.txt` líneas 79 y 114 |
| F6 «con 2 %» | ATENDIDO: reescrito con la tabla nueva (1.200 a 2 % = 0,18) | texto contra `tamano_b2_salida.txt` |
| F7 pesos al quitar no observadas | ATENDIDO: se re-ponderan y se informa (probado con 130 sin dato) | `fakeB.txt` |
| F8 tres miradas | SIN CAMBIO, cosmético | |
| F9 etiquetas | SIN CAMBIO y ahora pesa más: `decision_s162` del JSON guarda la decisión de B2 y 4b imprime «S162» (H4) | `fakeA.txt` líneas 78 y 97 |
| F10 el bloque de C no se lee | ATENDIDO en §7, pero choca con §5.2 (H4) | texto |

## Hallazgos

**H1. Ningún control prueba que el port esté vivo en la corrida de B2 (gravedad 3, confianza alta en la ausencia del control, media en que importe).**
Dónde: `evaluar.py:712-715` (control positivo: sólo `pos_prot` de Láscar y Chillán, que son de S159 y S162), 2.4 nulo, 2.5 NUNCA y 2.6 PLACEBO (se cumplen con 0 publicaciones), 2.2 «K re-corrido = publicado» (en neg_resto K no publica: una corrida muerta también «coincide»). B2 sólo trae neg_resto, así que su lote no tiene una sola pasada que deba publicar. Tampoco ayuda la señal intermedia: en las 389 neg_resto de S162, M14 tiene píxeles (`npix` > 0) exactamente en las 4 que publica, así que un port muerto y uno callado se ven igual hasta en npix. El workflow instala sin versiones (`pip install earthaccess numpy h5py scipy pyyaml pyproj pandas`), de modo que la pila de B2 puede no ser la de S162.
Reproducir: `fakeC.txt` (`v_fake3.py` copia, para los 1.200 ids de B2, sólo pasadas S162 sin eventos): «ESTADO DEL INSTRUMENTO: OK», 2.3 con 65 de 65, línea 81 «B: neg_resto [0, 1200] ... SILENCIO ACOTADO BAJO K», línea 97 «DE ACUERDO». Es justo lo que mostraría una corrida con el port roto.
Cómo se cierra (no lo aplico): meter en el lote B2 unas 20 pasadas ya medidas de S162 (por ejemplo 10 protegidas de Láscar y Chillán y los 4 eventos de neg_resto) y exigir que reproduzcan el npix y el VRP de S162; o fijar las versiones del pip. Cuesta 20 x 25 s, unos 8 min de runner.

**H2. El «93 %» es condicional a la tasa puntual; la probabilidad predictiva de decidir es 0,74 a 0,80 (gravedad 2, confianza alta en el número, la lectura es de diseño).**
`tamano_b2_salida.txt`, fila 0,0116 / 1200: 0,93 (reproducido: 0,928, con 19 eventos como máximo que aún deciden). Pero 0,0116 es el punto estimado de 4 de 389. Con la posterior de esa muestra (Beta(4,5; 385,5), prior de Jeffreys) la probabilidad predictiva de decidir es 0,798; con prior plano 0,738; con heterogeneidad entre estratos (media común, desvío por estrato con CV 1, `v_pred_estrato.py`, modo `partial`) 0,786. El texto del pre-registro dice «con la tasa observada», que es literalmente cierto, pero un lector se queda con «93 %». No cambia el diseño; cambia lo que se le promete a Nicolás: una de cada cuatro o cinco veces B2 saldrá NO RESUELTO aunque el port sea tan callado como se observó.
Reproducir: `python -I v_potencia2.py` y `python -I v_pred_estrato.py`.

**H3. La cobertura por lote avisa, no frena (gravedad 2, confianza alta, reproducido).**
`evaluar.py:598-604` agrega el AVISO y `veredicto_instr.append("cobertura_<lote>_<clase>")`, pero `invalido` (línea 749) excluye todo lo que empieza con «cobertura». `PREREGISTRO_B2.md` §4 dice que si B2 pasa el 10 % «la lectura de B2 se informa y no decide». En `fakeB.txt` (130 de 1.200 sin dato, 10,8 %): línea 14 el AVISO, pero línea 83 «B: neg_resto [17, 1070] ... -> SILENCIO ACOTADO BAJO K» sin marca, y línea 118 «VEREDICTO: los de §3 y §4b; avisos de cobertura: [...]». La regla queda en manos de que el lector lea el aviso. Es el mismo patrón que en B, pero ahora decide un solo lote y la línea que se copia al informe no lleva la marca. Arreglo barato: que la línea «B:» de la decisión repita el aviso, o que el veredicto diga «NO DECIDE» cuando el lote que decide pasa el 10 %.

**H4. La salida trae tres lecturas de B y §7 se contradice con §5.2 (gravedad 2, confianza alta).**
(a) La primera que aparece, `== 3. V375-B` (evaluar.py:765), es la de la UNIÓN: neg_pub como censo (intervalo puntual) y 1.634 neg_resto. Dice SILENCIO ACOTADO BAJO K casi con seguridad (en S162 ya daba 3,4 % contra 3,85 % y B igual quedó NO RESUELTO). La que decide está más abajo, en «decisión sobre: lotes S162b (DECIDE)». (b) El bloque 4b imprime «B: S162 ... | unión ...»: el rótulo «S162» es el nombre de la variable `dec_n`, que ahora contiene la decisión de B2; el JSON la guarda bajo `decision_s162`. (c) 4b compara también `global`, `valida_en_O` y `V375_D_necesario`; con un conjunto que decide sin positivas esas líneas pueden salir «DEPENDE DEL LOTE VISTO: NO RESUELTO» (fakeA.txt línea 98: `global S162 M13 | unión C13`), y §5.2 dice «si el conjunto que decide y la unión no coinciden, B queda NO RESUELTO»; un lector literal puede leerlo mal. (d) §7 dice que las secciones 4 y 4b «no se leen», pero el veredicto de B2 y su acuerdo con la unión viven justo ahí. Arreglo: escribir en el pre-registro cuál es la línea que decide (la «B:» del bloque `lotes S162b (DECIDE)`), cuál la que confirma (la «B:» de 4b), y que lo demás de esos bloques no se lee.

**H5. El «11 a 20 %» de error en la frontera del v1 es condicional (gravedad 1, confianza alta).**
`tamano_b2_salida.txt`, segunda tabla, fila 0,0254: 0,20 / 0,16 / 0,12 / 0,11 / 0,14. Esa tabla fija las 4 de 389 ya observadas y sortea sólo lo nuevo; si la tasa real fuera 2,54 %, esas 4 serían un resultado raro (P(≤4 de 389) ≈ 0,04). Incondicionalmente el v1 declaraba ACOTADO en la frontera ~2 % (S162 más 600 como una sola muestra: kmax de 989 = 15, P = 0,020). La conclusión de diseño se sostiene (decidir con lo no visto es lo fiel a C §5.5), pero la cifra de §3 que la apoya mezcla «error de la regla» con «error dado lo que ya vimos». Reproducir: `v_potencia2.py` (kmax y P para n = 989 y 1.589).

**H6. Dependencia entre pasadas no simulada (gravedad 1 a 2, confianza baja, SOSPECHA).**
`tamano_b2.py` es binomial independiente. 237 de las 1.200 pasadas de B2 comparten volcán y noche (noche = fecha UTC menos 6 h) con una neg_resto ya medida de S159 o S162, y hay hasta 4 pasadas por volcán-noche dentro de B2 (892 volcán-noches). Tres de los cuatro eventos de S162 tienen pasadas de B2 del mismo volcán a menos de 36 h (Lastarria 2026-09-27 y 2026-10-09: ids 4014, 3529, 3563, 4043; Tupungatito 2026-07-25: 3305, 3816; Llaima 2026-08-05: sin vecina de B2 en ese plazo, sí de S162). Si el encendido es un episodio de varios días y no ruido por pasada, la varianza real supera la binomial. Con un efecto de diseño de 1,18 el máximo de eventos que deciden baja de 19 a 18 y la potencia de 0,93 a 0,89 (cuenta a mano); un episodio de semanas pesaría más y no tengo datos para medirlo. No lo doy por hecho.

**H7. El reparto por módulo descarga cada gránulo muchas veces (gravedad 1, confianza alta).**
`probe_v375.py:133` (`n % nchunks == chunk`) con los objetivos ordenados por gránulo deja 25 gránulos distintos en cada trozo: 1.200 descargas contra 658 gránulos únicos (calculado sobre `objetivos_v375_b2.json`). No afecta la validez, pero duplica el tráfico contra LAADS y LANCE, que es donde falló A64 y donde A108 vio pasadas perdidas por `SEARCH_CMR_TIMEOUT`. Con el umbral de 10 % por lote (H3), perder pasadas por red tiene ahora consecuencia sobre lo que decide.

## VERIFICADO LIMPIO (y contra qué vara)

- **Muestra** (vara: `v_marco.py`, que rehace el marco desde `poblacion_completa.json` con su propia definición `lab != pos` y `pub_prod` falso, sin importar `seleccion.clase`): marco neg_resto 3.323; B2 en el marco 1.200 de 1.200; claves (volcán, hora) únicas; 0 en común con S159 (45 neg_resto) y con S162 (400 neg_resto); todos los campos de B2 iguales a los del marco; `pub_prod` 0, tipos de MIROVA sólo RUTINA, `mirova_vrp` mayor que 0,05: 0; ninguna fecha excluida (12, 13, 17 a 20 de octubre), rango 2026-04-01 a 2026-10-21; 41 partidas; ids 3000 a 4199 sin choque; sin gránulo vacío.
- **Proporcionalidad** (vara: recomputo desde la población): desvío máximo del n por estrato respecto de 1.200 x N_h/3.323 = 0,58 pasadas; 22 estratos, mínimo 6 pasadas por estrato; pesos de B2 sola 2,719 a 2,833; `estrato` consistente con volcán y cenit; el N por estrato de B2 coincide con el `meta` de S162.
- **Reproducción de la selección**: `rs.py` (copia de `seleccion_b2.py` con rutas ajustadas) da `6328988b861a4d32c3c8fc717a1426bd164d4447c62cabeccea85fe867e4019a`, igual al del pre-registro y al archivo del repo; salida idéntica (quedan 2.878, T 346 / O1 517 / O2 337, 658 gránulos).
- **Cableado del evaluador con datos fabricados** (vara: `v_mano.py`, cálculo a mano con los pesos de `meta`, Kish y Wilson): fakeA: 18 de 1.200, ponderado 0,014999, n efectivo 1.199,95, IC [0,009508; 0,023586] = salida del evaluador (línea 81); fakeB (130 sin dato, re-ponderadas): 17 de 1.070, IC [0,009629; 0,024818] = salida. La cota de todos los negativos 0,0367 (fakeA) coincide con (133 x 0,3652 + 3.323 x 0,02359)/3.456. neg_pub entra como muestra (N representado 130 de 133, porque 3 viven sólo en S159), no como censo.
- **El evaluador sin B2 no cambia lo publicado** (vara: `resultado_run40116289866\evaluar.json`): corrida por defecto => JSON idéntico salvo las claves `B_estricto`; sólo cambian dos etiquetas de texto.
- **Lote vacío**: sin artefactos de B2, INVALIDO POR INSTRUMENTO (`sinb2.txt` 79 y 114), aunque la línea «ESTADO DEL INSTRUMENTO» (27) diga OK antes: cosmético.
- **Tamaño y error en la frontera** (vara: `v_potencia2.py`, binomial exacto): límite de neg_resto 0,025407; kmax 19 de 1.200; tamaño en la frontera 1,7 %; si el neg_pub verdadero fuera el observado, 27 %, la frontera de neg_resto sube a 2,92 % y el error cae a 0,2 %; si fuera 40 %, 3,3 %. La primera mirada (S162) casi no suma: con 389 el máximo que decide es 3 eventos, P = 1,05 %, y ya se tomó sin declarar.
- **Workflow** (vara: `diff` de `git show s162-v375-bc-sello:experiments/_s162_v375/probe-s162-v375.yml` contra el b2, ignorando CR; el b2 tiene CRLF en el árbol y LF en el índice): sólo cambian nombre, comentario de B2, rama de disparo `s162-v375-b2-disparo`, grupo de concurrencia, ruta de OBJETIVOS, lista de 48 trozos, `--nchunks 48` y nombre del artefacto; `git diff 533398f8f ca034d66e -- pipeline` vacío; 48 trozos de exactamente 25 pasadas; autenticación sólo por EARTHDATA_TOKEN con falla inmediata (A71).
- **Régimen** (A104): los tres tramos (T, O1, O2) se informan por separado en §3 y B2 los trae en proporción al marco; la regla no los mezcla sin decirlo.
- **Sesgo del sorteo sobre el remanente** (camino C3): B2 se sortea de lo que queda sin medir y se pondera con el N completo del estrato; si los lotes anteriores fueron al azar dentro del estrato, el remanente es una muestra aleatoria y el sesgo esperado es de décimas de punto como mucho (las 434 ya medidas son 13 % del marco).

## SIN DATO

- Qué hará el port en las 1.200 pasadas: no están corridas.
- Heterogeneidad real por volcán y dependencia temporal (H2, H6): con 4 eventos no se puede medir.
- Si los 658 gránulos se pueden seguir bajando hoy (no probé red ni credenciales) y si el runner de Actions reproduce el de S162 con la pila de paquetes de ese día (H1).
- `probe_v375.py`, `brazos.py` y la física del port: no los leí.
- La cobertura contra la referencia de MIROVA fuera del marco congelado: es el mismo marco, no lo recalculé.

Scripts y salidas en esta carpeta: `v_marco.py`, `rs.py`, `v_potencia2.py`, `v_pred_estrato.py`, `v_mano.py`, `v_fake2.py`, `v_fake3.py`, `defecto.txt` y `.json`, `sinb2.txt` y `.json`, `fakeA`, `fakeB` y `fakeC` (`.txt` y `.json`), `CAMINOS_ANTES.md`.
