# Informe del verificador con contexto limpio: `evaluar_v750a.py` (V750-A, S162)

Fecha de la corrida: 2026-10-24 a 2026-10-25. Verificador: sesión sin contexto previo del analizador. Archivos leídos:
`PREREGISTRO_V750A.md`, `evaluar_v750a.py`, `analizar_v750b.py`, `LECTURAS_EVALUAR_V750A.md`,
`probar_evaluar_v750a.py`, `mutar_evaluar_v750a.py`, `equivalencia_v750a.py` y las partes de `evaluar_d25.py` que el
analizador extrae (sha256 `2e5576973ef1df6969f517c40bedc271f76db8a8b4756613e5004fc05d976747`, verificado igual al fijado
en `analizar_v750b.py:48`). La lista de caminos de falla se escribió antes de abrir las pruebas:
`C:\vrp-trabajo\s162-v750a-eval\experiments\_s162_v750a\verificador\LISTA_CAMINOS_previa.md`.

## Veredicto

**Listo con cambios.** No encontré un camino por el que el analizador dé hoy un veredicto de adopción por una razón
distinta de la escrita en una población bien formada: las reglas de P1, P2, M, equivalencia y las compuertas se
comportan como las lecturas L1 a L17 dicen, y la línea base completa da 28 de 28 escenarios en verde. Lo que sí hay son
(a) tres lecturas o controles que pueden cambiar o cerrar el veredicto por un motivo que el pre-registro no escribió
(VA-01, VA-02, VA-03), (b) una sombra que da CUMPLE vacío (VA-04) y (c) un nulo de pruebas débil: de 41 roturas de una
línea, las pruebas del autor atrapan 6 y dejan pasar 35 (VA-07). Varias de las que pasan son reglas que deciden.

## Método y decisiones mías

- Línea base: `probar_evaluar_v750a.py` contra `evaluar_v750a.py` sin tocar: 28 de 28 `OK` y la línea final
  «TODOS LOS ESCENARIOS COMO SE ESPERA (28)» (`verificador\base_salida.txt`).
- Mutaciones: 41 copias con UNA línea rota cada una (`ver_mutar.py`, catálogo `MUT` adentro), nombradas
  `_ver_<id>_evaluar_v750a.py` y borradas al terminar. Corrí los 28 escenarios de las pruebas contra cada copia. Para ahorrar
  tiempo paré en la primera falla o caída (marcado «parada temprana»); las que no se atrapan corrieron completas. Una
  rotura cuenta como atrapada sólo si hay una falla por aserción y ninguna caída.
- Una de las atrapadas era falsa: V16 salió «atrapada» por un código de salida 3221225477 (0xC0000005, violación de acceso)
  del analizador en E20 con una salida que sólo trae el banner (`mut_salida.txt`, `mut\pruebas_V16\E20\stdout.txt`, 180
  bytes). Volví a correr V16 completa y pasa los 28 (`mut3_salida.txt`); E20 repetida 4 veces en paralelo contra el
  original dio 4 de 4 OK (`rep20_*`). Es un tropiezo no reproducible, pero muestra VA-08.
- Escenarios míos contra el analizador original (`ver_casos.py`, salidas en `casos_salida.txt` y `casos\*\stdout.txt`):
  CA a CK.
- Para todo lo que cito: archivo:línea del repo de trabajo `C:\vrp-trabajo\s162-v750a-eval\`, o la salida del comando.
- Corriendo con `OMP_NUM_THREADS=1` (sin esto, 10 procesos de numpy a la vez saturaban los 12 núcleos). No toqué
  `pipeline/`, `data/`, `frontend/` ni los `_mut_*` del autor. No hice git.

## Hallazgos

### VA-01 (media) K = producción tolera 1 % de pasadas distintas y las saca de todos los brazos; el pre-registro dice «en todas»

- Pre-registro §7 (`PREREGISTRO_V750A.md:143`): «K = producción: publica igual y `pc.vrp_mw` a 0,001 MW en **todas** las
  pasadas ok».
- Analizador: `evaluar_v750a.py:361-367`: `k_ok = len(k_dist) <= AB.MAX_K_DISTINTO * max(1, len(oks0)) and not k_dist_prot`
  y después `oks = [i for i in oks0 if i not in set(k_dist)]`; `AB.MAX_K_DISTINTO = 0.01`
  (`analizar_v750b.py:49`, heredado de V750-B donde su §7 sí lo decía). Con 1.000 pasadas el control deja pasar 10
  distintas y las excluye en silencio de P1, P2 y M (se imprimen en la línea del control, pero no cierran nada).
- No está en `LECTURAS_EVALUAR_V750A.md` (L1 a L17): es una lectura no declarada.
- Las pruebas no lo fijan: E14 tiene 2 distintas, ambas protegidas, en 48 pasadas (4 %), así que está sobredeterminado.
  Roturas que pasan: V01 (quitar `and not k_dist_prot`), V03 (no sacar las distintas de `oks`), V02 (la mitad de `pc_vrp`
  a 0,001 MW: cambiar el corte a 1000 MW) (`mut_salida.txt`).
- Arreglo: poner el límite en 0 (o documentarlo como L18 y que Nicolás lo selle), y agregar un escenario con una sola
  pasada distinta no protegida (debe cerrar) y otro con `pc_vrp` distinto y `pub_prod` igual.

### VA-02 (media) El control «placebo de publicación» no es infalible: los filtros de artefacto del tablero sí miran la magnitud

- Pre-registro §7 (`:146`): «el predicado no mira la magnitud salvo VRP > 0». `LECTURAS_EVALUAR_V750A.md:29-31` lo repite
  («ningún escenario sintético … lo hace caer»).
- Falso para el predicado real. `frontend/index.html:1336-1340` (`isCirrusArtifact`: `t_max_k < 273,15` y VRP efectivo
  `> 10` => artefacto) y `:1355-1363` (`isDiffuseFieldArtifact`: `n_pixels >= 100`, `t_max_k < 278,15`, VRP `>= 50` y
  VRP/píxel `< 1`). Medido con el mismo node del analizador (`B.correr_node`): un record V750 de 9,0 MW con `t_max` 270 K
  publica (1), y ×1,2 = 10,8 MW no publica (0); lo mismo con 45 → 54 MW, 150 píxeles, `t_max` 276 K (salida `[1, 0, 1, 0]`).
- Efecto: `evaluar_v750a.py:411-414` marca el control FALLA y la compuerta se cierra (salida 3, sin veredicto) por un
  motivo que no es un defecto del analizador. Condición: una pasada de K con `t_max` frío y VRP entre 8,3 y 10 MW (o entre
  41,7 y 50 MW con campo extendido). En un nevado de noche `t_max` bajo 273 K es corriente; lo improbable es el VRP alto, pero
  Chillán en erupción lo hace posible.
- Arreglo: excluir del control las pasadas en que K o K×1,2 cruzan esos umbrales y listarlas aparte, o comparar la
  publicación bajo el predicado sin los dos filtros de artefacto. Corregir la frase de §7 y de las lecturas.

### VA-03 (media) La razón de M (0,9 a 1,1) se mide sobre otro conjunto que el de §5, y eso cambia el veredicto

- §5 (`PREREGISTRO_V750A.md:95-101`): M es la razón brazo/MIROVA «en las alertas que publican los dos». §6.2 dice «mediana
  de la razón de P … en las protegidas». L4 (`LECTURAS:12`) elige «protegidas publicadas por P (sin exigir K)» y dice que
  la fijan E06 y E07.
- Código: `evaluar_v750a.py:538-542`: `etiqueta == "prot" and en_ventana and pub(i, b) and mirova_vrp and vrp > 0`; no
  exige `pub(i, "K")`. Los pares del comparador (`m_pares`, `:387-400`) sí exigen K.
- Escenario CA (`casos_salida.txt`): a la población base le agregué 12 protegidas en O que K no publica y P publica al doble
  de MIROVA. Resultado: `O/tabla: M razón en protegidas 2.000 (n 23) | M comparador MEJORA (pares 13 …) -> no cumple: M razón 2.000`
  y `== §6 censo: NO CUMPLE`. La misma población con la lectura de §5 (copia con `and pub(i, "K")` en esa línea,
  `ver_ca_v38.py`, salida en `ca_v38_salida.txt`): `M razón en protegidas 1.000 (n 11) … -> cumple` y
  `== §6 censo: CUMPLE`. Las dos lecturas son defendibles; el veredicto depende de cuál se elige.
- L4 dice «prueba que la fija: E06, E07», pero esas pruebas no distinguen: las roturas V38 (exigir también K) y V28 (razón
  sobre protegidas y bajas) pasan los 28 escenarios.
- Arreglo: que Nicolás elija al sellar; imprimir las dos razones lado a lado (con y sin exigir K) y agregar un escenario
  como CA que fije la elegida.

### VA-04 (media-baja) La sombra puede dar CUMPLE sin haber visto una sola protegida; BLOQUEA pasa en la sombra

- Escenarios CJ y CK (`casos_salida.txt`): sombra con 8 pasadas, todas negativos limpios que nadie publica, ninguna
  protegida: `== §6.3 canal tabla: P1 0 (de 0) | P2 SIN SUSTRATO … == §6.3 sombra: CUMPLE (P1 = 0; P2 tabla SIN SUSTRATO,
  todo SIN SUSTRATO; con 4 bloques o menos la sombra sólo veta)`. Con una sola protegida, igual. El texto final no dice que
  no hubo nada que vetar; el «de 0» sólo está en las líneas por canal. Código: `evaluar_v750a.py:586-602`.
- Es coherente con §4.3 («sólo puede vetar»), pero una línea «CUMPLE» sin protegidas lee como un visto bueno. Arreglo:
  cuando `n_prot == 0` en un canal, escribir «SIN PROTEGIDAS: la sombra no pudo vetar» y no «CUMPLE».
- Aparte: L3 deja pasar P2 BLOQUEA en la sombra (`:594` sólo mira PIERDE) porque §6.3 dice «no PIERDE», mientras §6.2 dice
  «no PIERDE ni BLOQUEA» y en D-45 BLOQUEA «bloquea CUMPLE». Lectura literal, pero permisiva en la puerta final. Que Nicolás
  lo confirme (E23 lo fija; rotura V32 y V33 muestran que ningún escenario distingue los canales de la sombra).
- En el censo, L3 hace lo contrario: SIN SUSTRATO en un estrato (4 bloques o menos) cuenta como falla aunque no sea PIERDE
  ni BLOQUEA. Es estricto (el error va en el sentido seguro) y está documentado; también conviene sellarlo.

### VA-05 (baja) El diagnóstico S-1 se imprime agregado y antes de la puerta §6.1, y el contrato de la celda decisiva no se verifica

- §5 pide informar «por pasada» (a) el cambio de sd y (b) el margen c/u. El analizador imprime (a) como mediana y máximo por
  par y (b) sólo para las pasadas «decididas por la escena» (`evaluar_v750a.py:467-479`); el detalle por pasada no queda en
  la salida (sólo en los artefactos).
- El bloque S-1 (`:448-482`) corre antes de §6.1 (`:484-508`), así que cuando §6.1 falla (salida 6, «el censo no se mira»)
  ya se imprimió qué protegidas cambian de publicación entre P, P-def y O. Leve, pero contradice «no se mira el censo».
- El analizador no puede comprobar que `celda_decisiva` (pase, zona) sea la misma celda del cráter en los dos brazos; el
  pre-registro tampoco define qué es la celda decisiva cuando el cráter no alerta en ninguno de los dos pases. El oráculo
  `mirova_v750_r2.py:89-117` usa u1 en las zonas 0 y 1, u2 en la 2, lo que `_u` replica.
- Las pruebas no distinguen pase 1 de 2 ni NTI de ETI (los fixtures usan los mismos valores): V13 (umbral siempre de
  `pasada1`), V14 (la celda alerta sólo con NTI), V12 (se quita el par (P-def, O)), V27 (la etiqueta «decidida por la escena»
  de §6.1 nunca sale) y V41 (diag inválido tratado como válido) pasan.
- Arreglo: imprimir (o escribir a un CSV junto a la salida) una fila por pasada con (a) y (b); mover S-1 después de §6.1; y
  en los fixtures usar valores distintos en pase 1 y 2 y en NTI y ETI.

### VA-06 (baja) Tres caídas con datos mal formados; ninguna silenciosa

Todas salen con traceback y código 1, así que no producen un veredicto falso.
- `estado: null` en un resultado: `evaluar_v750a.py:243` (`r.get("estado", "sin_resultado")[:40]`) → TypeError (escenario CB).
- `Kgeo` presente pero sin `record`: `AB.slim(res[i]["brazos"][b]["record"])` → KeyError 'record' (escenario CG).
- Sombra con record de P publicado sin `primary_cluster` (record legado): `:341` → TypeError (escenario CC).
- Arreglo: `.get` con valores por defecto, o cobertura `falta_brazo`/SIN DATO para los dos primeros.

### VA-07 (alta para el uso, media para el veredicto) Nulo de las pruebas: 35 de 41 roturas pasan

Cada fila: rotura de una línea en una copia, 28 escenarios, resultado (`mut_salida.txt`, `mut2_salida.txt`, `mut3_salida.txt`).

Roturas que **las pruebas no atrapan** (salida 0, «TODOS COMO SE ESPERA»):

| id | rotura | por qué importa |
|---|---|---|
| V01 | K = prod sin `and not k_dist_prot` | una protegida con K distinto de producción deja de cerrar (VA-01) |
| V02 | `pc_vrp` a 0,001 MW → 1000 MW | la mitad del control K = prod no se prueba |
| V03 | las pasadas con K distinto no salen de los brazos | VA-01 |
| V04 | piso de la banda de M 0,9 → 0,5 | ningún escenario tiene razón bajo 0,9 |
| V05 | techo 1,1 → 1,25 | los escenarios usan 1,0 y 1,3 |
| V06 | `len(sin) + len(sin_g)` → `len(sin)` | las pasadas sin gránulo del generador nunca están en el archivo de prueba |
| V07 | una protegida SIN DATO deja de frenar sola | el 2 % ya cierra en E15 y E17 |
| V08 | el denominador de cobertura no saca fuera/sin_cráter | ningún escenario trae esos estados |
| V09 | la pasada diurna deja de ser SIN DATO | todos los escenarios tienen `dayflag` 0 |
| V10 | los pares de M sólo con protegidas | L4 |
| V11 | tolerancia de VRP P contra O 1e-6 → 5e-3 | la diferencia de prueba es 0,01 |
| V12 | S-1 sin el par (P-def, O) | VA-05 |
| V13 | umbral siempre de `pasada1` | VA-05 |
| V14 | la celda alerta sólo con NTI | VA-05 |
| V15 | equivalencia local sin mínimo de mutaciones atrapadas | L2 |
| V16 | equivalencia local sin exigir el control caído | L2 (la primera pasada salió «atrapada» por un crash, ver VA-08; rehecha completa pasa) |
| V17 | equivalencia local sin VERDE ni ausencia de ROJA | L2 |
| V18 | `--solo-controles` ignorado | ningún escenario usa el flag |
| V19 | el bloque de P2 pierde el volcán (sólo la noche) | dos volcanes la misma noche se fusionan; ningún escenario los junta |
| V20 | canal «decide» con T y O invertidos | afecta controles y tablas informativas |
| V21 | M sin piso de sustrato (5 pares, 3 noches) | ningún escenario tiene pocos pares |
| V22 | nulo del contador siempre OK | declarado por el autor (sin escenario posible) |
| V23 | placebo de M siempre OK | idem |
| V24 | placebo de publicación siempre OK | idem; ver VA-02 |
| V25 | P1b abajo: corte 1 MW → 100 MW | informativo |
| V26 | se ignora el flag `decide` del objetivo | el fixture pone `decide = lab == "pos"` siempre |
| V27 | la etiqueta «decidida por la escena» de §6.1 nunca sale | texto |
| V28 | razón de M sobre protegidas y bajas | VA-03 |
| V30 | el nulo K contra gemelo acepta M MEJORA/EMPEORA | sólo se prueba con P2 |
| V32 | sombra: P2 PIERDE sólo cuenta en el canal tabla | no hay escenario con la diferencia sólo en el canal «todo» |
| V33 | sombra: P1 sólo en el canal tabla | idem |
| V36 | censo: M comparador exigido sólo en el canal tabla | ningún escenario falla M sólo en «todo» |
| V37 | censo: razón de M exigida sólo en la ventana O | ningún escenario falla la razón sólo en T |
| V38 | razón de las protegidas exige también K | VA-03 |
| V41 | S-1 trata el diag inválido como válido | no hay diag presente pero inválido (NaN, u = 0) |

Roturas que **sí atrapan** (todas por aserción, con parada temprana): V29 (bloque de P2 por mes, E00), V34 (P1 del censo sólo en
canal tabla, E26), V35 (P2 del censo sólo en T, E04), V39 (la VRP de P contra O nunca se compara, E08), V40 (la banda
exime siempre que el campo exista, E08), V42 (equivalencia local ausente cierra, E10). Total: 6 de 41.

Lectura: las pruebas fijan bien las reglas gruesas que el autor mutó (M1 a M28: P1, P2, M, controles, equivalencia, sombra), pero
no fijan la **aritmética de borde** (bandas, tolerancias, mínimos), la **cobertura** (sin gránulo, fuera, sin cráter, diurna),
la **simetría de canales y ventanas** (qué falla sólo en «todo» o sólo en T) ni S-1. Las filas V22 a V24 son infalibles por
diseño y el autor ya las declaró; las demás no.
Las columnas «L» de `LECTURAS_EVALUAR_V750A.md` que citan una prueba que las fija son falsas en parte: L2 (V15, V16, V17),
L4 (V10, V28, V38), L12 (V12, V13, V14, V27), L13 (V11).

Arreglo propuesto, un escenario por rotura que pasa y del tamaño mínimo: (1) un escenario con 1 pasada K distinta no protegida y
otro con `pc_vrp` distinto; (2) razones 0,85 y 1,15; (3) archivo `sin_granulo` con una pasada, estados `volcan_fuera_del_granulo`
y `sin_crater`, y una pasada con `dayflag` 1; (4) diferencia de VRP de 1e-4 entre P y O; (5) dos volcanes la misma noche;
(6) un escenario con sólo 4 pares de M; (7) sombra y censo con la falla sólo en el canal «todo» y sólo en T; (8) fixtures
de S-1 con pase 1 distinto de pase 2 y NTI distinto de ETI, y un diag con NaN; (9) salida local con 3 mutaciones, sin
VERDE y con ROJA.

### VA-08 (baja) La batería clasifica un crash nativo como «falla por aserción»

- `probar_evaluar_v750a.py:394-398`: sólo la presencia del texto «Traceback» da CAÍDA; cualquier otro código de salida
  distinto del esperado cuenta como FALLA («código de salida X, se esperaba Y»). Un crash nativo (0xC0000005), un kill por
  memoria o un `sys.exit` sin traceback se cuentan como atrapada.
- Observado una vez: V16 salió «atrapada» por el código 3221225477 en E20 (arriba). En el nulo del autor
  (`mutar_evaluar_v750a.py`, `estado = ATRAPADA` si salida 1 y «FALLAS» en la línea) un crash así infla el conteo de roturas
  atrapadas con un falso positivo.
- Arreglo: CAÍDA si la salida es vacía o si el código no está entre los esperados por el analizador (0, 3, 5, 6).

### VA-09 (baja) La prueba de equivalencia local no está atada al módulo ni a una versión

- `evaluar_v750a.py:179-190`: se leen cuatro marcas de texto en un archivo libre (`VERDE:`, ausencia de `ROJA`, `mutaciones:
  TODAS COMO SE ESPERA`, líneas «atrapada por aserción» ≥ 5, control caído). `equivalencia_v750a.py` produce dos salidas
  distintas (la del módulo real y la de `--mutaciones`, que corre las mutaciones sobre el **oráculo**, no sobre el módulo);
  el archivo que se pasa tiene que ser su concatenación a mano. No hay sha de `pipeline/mirova_v750_codigo.py`, ni del
  commit, ni mínimo del número de casos (`E1 1020`, `E3 10`).
- Un `VERDE` de una versión vieja del módulo más unas mutaciones recientes pasan. Arreglo: que `equivalencia_v750a.py` imprima
  el sha256 del módulo y el commit, y que el analizador lo compare con el tag; exigir «E1 ≥ 1000 casos, E3 ≥ 10 recortes».
- Misma familia: `banda_triangulacion` la marca el productor del artefacto y exime máscara y VRP sin tope
  (`:491-492`); el pre-registro la define sólo para el VRP (20 semillas de jitter). SOSPECHA: un productor que marque de más
  esconde diferencias reales. La banda se lista aparte en la salida, y eso es lo que lo mitiga.

## Lo que revisé y está bien (para no repetirlo)

- Las etiquetas (`etiqueta`, `prot_tabla`, `en_ventana`) son la copia fiel de `analizar_v750b.py:329-349`; `en_ventana` usa
  «TODO» y todas las llamadas también (grep, 0 usos de «TO»).
- `p2`: el bloque (`hora_utc[:10]`, volcán) y la inclusión de bloques de suma 0 coinciden con `prueba_signos_p2` de
  `evaluar_d25.py` («incluidas las de suma 0»); `regla_signos_p2(neto, B, pr)` se llama con los argumentos correctos.
- `cargar_m`: revisé con `ast` que las piezas extraídas de `evaluar_d25.py` no usan ningún nombre global que falte (nombres
  libres sin definir: ninguno).
- P1 es la intersección que L1 dice (protegidas que K publica y P no); las que ni K ni P publican se listan (E02).
- Cobertura con pasadas sin gránulo del generador, protegida SIN DATO, `volcan_fuera_del_granulo`, `sin_cráter` y diurna: el
  comportamiento real es el correcto (escenarios CD y CE: cobertura INSUFICIENTE, protegidas «fuera» listadas y sin frenar,
  diurna como SIN DATO); lo que falta es la red de pruebas (V06 a V09).
- P-sinfiltro: el predicado del tablero (`index.html:1162-1180`, `:1609-1616`) sólo mira `distance_class` y
  `primary_cluster.centroid_dist_km` para la distancia, que son los dos campos que se neutralizan (L11).
- `pos` que no «decide»: no entra a ninguna métrica (escenario CH, CUMPLE sin cambios).
- Diag S-1 ausente: SIN DATO, se lista y no cierra la compuerta (escenario CF); es lo que L12 dice.
- Orden de salidas 3, 6, 5, 0 según L15/E08/E10/E12/E16 (corridas de la línea base).

## Roturas y escenarios: dónde están las salidas crudas

Todo en `C:\vrp-trabajo\s162-v750a-eval\experiments\_s162_v750a\verificador\`:
`base_salida.txt`, `mut_salida.txt` (V01 a V40), `mut2_salida.txt` (V38, V41, V42), `mut3_salida.txt` (V16 completa),
`casos_salida.txt` (CA a CK), carpetas `base\`, `mut\`, `mut2\`, `mut3\`, `casos\` (stdout de cada escenario),
`ver_mutar.py` (catálogo de roturas), `ver_casos.py` (escenarios míos), `LISTA_CAMINOS_previa.md`.
Las carpetas `art\` y `objetivos.json` de los escenarios se borraron para ahorrar espacio (se regeneran con los scripts).
Las copias `_ver_*_evaluar_v750a.py` se borraron.

## Lo que no pude comprobar

- El productor de los artefactos (celda decisiva, `banda_triangulacion`, `pos_crater`, etiquetas `lab`/`decide`/`protegida`,
  `pub_prod`, `pc_vrp`): el analizador los toma como contrato. SOSPECHA de que un productor que los arme distinto cambia el
  veredicto sin que el analizador se entere.
- Que los límites del contrato real (ventana del 2026-04-01 al 2026-11-02, exclusión de días) los aplique el generador:
  el analizador no los revisa (L16).
- Rendimiento con la población real: cada escenario sintético tarda 15 a 60 s; la población real (miles de pasadas) no
  se probó.
