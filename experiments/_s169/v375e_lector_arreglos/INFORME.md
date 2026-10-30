# S169 V375-E: arreglos del lector de la sombra (VS168-01 a 14)

Rama `claude/s169-v375e-lector`, desde `origin/claude/s168-v375e-sello` en `3f7e8814c`. Hecho el 2026-10-30 entre las
01:30 y las 03:00 UTC (hora del servidor, `date -u`). **Sin tag**: el tag va después del nulo y de un verificador corto
de otro modelo. No se abrió ningún dato de `data/sombra_codigo_mirova/` ni de `data/mirova_equivalent/`: lo único que
corrió fue la batería sintética y cinco corridas de la batería contra copias del lector rotas a mano.

## Por qué

El verificador limpio de S168 (`experiments/_s168/v375e_sombra/verificador/INFORME.md`) dejó el lector en SELLABLE CON
CAMBIOS con un hallazgo de gravedad 3: quien corría el lector podía elegir, después de ver salidas provisionales, en qué
noche terminaba la ventana que decide, y desde cuál empezaba. Una lectura así deja de ser una prueba, porque el corte se
puede mover hasta que aparezca el resultado que uno quiere. Los de gravedad 2 eran huecos del mismo tipo: salidas que
el texto no fijaba (una protegida sin dato, (c) sin sustrato, un régimen de código mezclado, una referencia con rezago)
o cableado que la batería no veía.

## Dónde está

- Texto (manda sobre el código): §11 de `experiments/_s162_v375/PREREGISTRO_E.md`, borrador sin sello. Las reglas nuevas
  quedaron en la sección que corresponde y la tabla de §11.11 dice qué hallazgo cierra cada una. §1 a §10 sin tocar:
  el sha256 de las primeras 727 líneas sin CR es `5af76cd5…348c` antes y después.
- Código: `experiments/_s168/v375e_sombra/leer_sombra_v375e.py`.
- Batería: `experiments/_s168/v375e_sombra/probar_sombra.py`. Nulo: `experiments/_s168/v375e_sombra/mutar_sombra.py`.
- Comprobación en rojo: `experiments/_s169/v375e_lector_arreglos/ver_en_rojo.py` (salidas en
  `experiments/_s169/v375e_lector_arreglos/rojo_{A,B,C,D,E}.txt`).

## Qué cambió, por hallazgo

«En rojo» dice qué rotura (id de `mutar_sombra.py`) se aplicó a mano en una copia, en qué grupo de `ver_en_rojo.py`, y
que la aserción nombrada salió FALLA.

| hallazgo | texto (§) | código (función) | aserción nueva | en rojo |
|---|---|---|---|---|
| VS168-01 (3) el corte que decide queda libre | §11.1 ventana; §11.4 S1; §11.8 entero | `control_s1` exige `desde == DESDE_P`; `noche_parada` (primera noche con 30 y 40); `analizar` recorta a N y antes de N devuelve sólo controles y contadores; `main` con `--dir-salida`, nombre `lectura_sombra_corte_<N>`, no sobrescribe y rechaza volver a leer un corte (sale 2) antes de calcular | «S1: desde DESPUÉS del 2026-11-03 también cae»; «antes de la parada analizar no lee»; «el corte que decide es la noche de la parada»; «la noche N es la PRIMERA»; «con --hasta posterior lee sólo hasta la noche de la parada»; «leer otra vez el mismo corte sale 2»; «la lectura que decide sale 0 y se llama…»; «antes de la parada sale 5…» | sí: V14 (D), N01 (B), N02 (C), N03 (C), N04 (D), N05 (B), N06 (A) |
| VS168-02 (2) con un control caído se imprime el detalle | §11.4, «Qué se imprime» | `MOTIVO`; `reporte_controles(detalle=…)`; `para_json` | «antes de la parada los controles salen sin detalle»; «con S1 caído no salen conteos ni nombres»; «con S7 caído sale 3, sólo el motivo» | sí: N07 (A), N08 (C), N09 (B) |
| VS168-03 (2) protegida SIN DATO que K publica | §11.6 (a); §11.4 S7 | `paquete` arma `sin_dato_prot`; `leer_brazo` la suma a `veta` y la lista en `P1_sin_dato` | «una protegida SIN DATO que K publica veta»; «una SIN DATO que K calla no veta pero se lista»; «main: la protegida SIN DATO que K publica veta a cercano» | sí: N10 (B), N11 (C), N12 (C) |
| VS168-04 (2) régimen y módulos sin identificar | §11.4 S0 y S8; §11.1 | `SHA_SELLO_LECTOR` (8 archivos) en `cargar_deps`; `control_s8` y `diff_git` contra `c42ee0eb7`; `criterios_sombra(regimen_ok)`; `--commit` obligatorio; el lector imprime su sha256 y el `HEAD` de su checkout | «S0: banco_paridad.py e index.html distintos del sello no cargan nada»; ocho de S8 (perfil, `--commit`, sin régimen, sha no resoluble, base, cambio); «S8 en analizar…»; «criterios (S8)…» | sí: N13, N16 (E), N17 a N20 (D), N14 (C), N15 (B) |
| VS168-05 (2) la referencia pierde filas y tiene rezago | §11.1; §11.4 S9; §11.8 salidas | `control_s9` (tabla hasta N + 2 días); la lectura del corte se escribe una vez | «S9: tabla hasta 1 día después del corte cae»; «en analizar, la referencia fresca hace caer la lectura»; «main: con la tabla a 1 día del corte S9 cae» | sí: N21 (D), N22 (B), N23 (C) |
| VS168-06 (2) (c) SIN SUSTRATO da NO CUMPLE | §11.6 (c); §11.7 | `estado_c_sombra` | «(c): M SIN SUSTRATO en la sombra da DECIDE NICOLAS»; «estado_c_sombra da DECIDE NICOLAS sólo con SIN SUSTRATO» | sí: N28 (B) |
| VS168-07 (2) controles de la curva sólo del brazo | §11.6 | `paquete` corre `controles_curva(…, "K")` y `leer_brazo` usa `cae_curva or cae_k` | «los controles de la curva de K se calculan»; «un control de la curva de K caído lleva (d) a DECIDE NICOLAS»; «los controles corren también para K y ven su sesgo» | sí: N29 (B), V06 (E) |
| VS168-08 (2) la batería no ataba (b), (c), (d) ni S6 | §11.4 S6 | `control_s6` exige sustrato e informa sus pares; `b_sin_evidencia` | (b), (c) y (d) por valor en la escena principal; cableado de `leer_brazo` con módulos sustitutos (P2, P2-L, M, curvas en los dos órdenes); rama sin `neg_pub`; S6 en verde, con MEJORA, sin sustrato y en `analizar` | sí: N27 (A), N38 (A), V01 a V03 (C), V05 (B); V04 es equivalente (abajo) |
| VS168-09 (1) sólo la vuelta conjunta del borde | §11.5 | `borde_mixto`; `estado_final(base, vueltas)` | «borde mixto…» (dos); «la vuelta mixta que cambia el estado da DECIDE NICOLAS»; «analizar calcula la vuelta conjunta y la mixta» | sí: N30 (C), N31, N32 (B) |
| VS168-10 (1) S4 puede caer por redondeo | §11.4 S4 | `control_s4` excluye las de radiante a 0,0005 km del radio y las cuenta | «radiante a 0,0004 km se excluye y no cae»; «a 0,002 km sí cae» | sí: N26 (D) |
| VS168-11 (1) alertados sin distancias | §11.4 S10 | `control_s10` | «S10: una pasada con alertados y sin distancias cae»; «brazos deja dist None…»; «S10 en analizar» | sí: N24 (D), N25 (B) |
| VS168-12 (1) lo que la retrospectiva informaba | §11.2 (partida, aceptada); §11.6 | `alertas_sin_record` en `main`; `lejanas_ocr`; listas de S7 y de la lectura completas | «las alertas de MIROVA sin record de K se informan»; «far_ocr se informa por brazo y para K»; «la lista de SIN DATO va completa» | sí: N33, N34 (B), N39 (D) |
| VS168-13 (1) los brazos que informan imprimen estado | §11.7 | `reporte` imprime criterios sólo de cercano; `para_json` los quita a los demás | «main (VS168-13): radiante y P-sinfiltro sin criterios ni estado» | sí: N35 (C), N36 (B) |
| VS168-14 (1) `--commit` opcional, referencia, mitades | §11.1; §11.7 | `--commit` obligatorio | «sin --commit no corre» | sí: N37 (A) |

Además, del verificador: S2 con la primera pasada que no publica (V13), S3 con 0,0062 y 0,0048 km (V08), S7 con 1 de 9
protegidas sin dato (V10), el borde a 0,0045 km (V09), la ganancia pareja con un instrumento que no es invariante a la
escala (V12), las mitades con su cuenta de pasadas (V07) y P-sinfiltro en la lectura (V11). Ésas no se rompieron a mano
(no son reglas nuevas); las mide el nulo.

**Lo que se eligió distinto de la propuesta del traspaso** (con la razón en el §11): S8 no hace caer la lectura (la
propuesta decía «LECTURA NO LEGIBLE y decide Nicolás») sino que la marca y lleva los CUMPLE de (b), (c) y (d) a DECIDE
NICOLÁS, que es la variante del verificador: no falla el instrumento, la ventana mezcla dos detectores, y Nicolás tiene
que ver la lectura para decidir. Y S0 fija también `frontend/index.html` (la propuesta lo dejaba «informado»): es el
predicado que dice qué publica cada brazo, y con el lector corrido desde su tag queda fijo sin costo.

**Aceptado sin código** (gravedad 1, razón en §11.11): la marca de pasada partida, las listas de `lecturas_far`
truncadas a 40 por el lector sellado, el cenit tomado del record de K, y el Wilson sobre `neg_resto`.

## La comprobación en rojo

Cinco corridas de la batería contra copias rotas (`ver_en_rojo.py --grupo A` a `E`), cada grupo con roturas elegidas
para que no se tapen entre sí. Las 39 reglas nuevas (N01 a N39) y las roturas de cableado del verificador que tocan una
regla (V01 a V06 y V14) salieron EN ROJO, con dos repeticiones:
- en el grupo D, N16 (comparar contra la base) **no se vio**: la prueba usaba records con el mismo sha que la base, así
  que comparar el sha consigo mismo daba lo mismo. Se agregó a la prueba un record de otro commit; en el grupo E,
  N16 sale EN ROJO;
- en el grupo B, V06 (`cae_curva or cae_k` fijo en falso) **no se vio** porque V05, en el mismo grupo, ya llevaba (d) a
  DECIDE NICOLÁS. Sola, en el grupo E, sale EN ROJO.

**V04 es una mutación equivalente.** Cruzar P2 contra K con P2-L en la llamada a `criterios_sombra` no cambia (b) para
ningún par de valores: en el alfabeto de `regla_signos` (GANA, EMPATE, SIN SUSTRATO, PIERDE, BLOQUEA) el conjunto que
(b) acepta para P2 es el complemento exacto del que rechaza para P2-L, así que (b) es CUMPLE si y sólo si los dos están
en {GANA, EMPATE, SIN SUSTRATO}, en cualquier orden. Se espera que sobreviva al nulo.

Para que una mutación que quita una clave se vea como aserción fallida y no como caída de la batería, los resultados del
lector se envuelven en un dict que devuelve vacío para una clave ausente, y cada sección registra una excepción como
FALLA con su nombre. La carga del lector queda fuera de toda sección, así que una rotura de la importación sigue siendo
CAÍDA (el control del nulo).

## Batería y nulo

**Batería: 190 de 190** (antes 104), corrida sobre el árbol quieto después del último cambio, en este computador, un
proceso, entre las 02:46 y las 02:52 UTC del 2026-10-30. Salida en `experiments/_s168/v375e_sombra/probar_sombra_salida.txt`.
Comando: `PYTHONIOENCODING=utf-8 python -I experiments/_s168/v375e_sombra/probar_sombra.py`. Las escenas tienen de 2 a
25 noches; para llegar a la parada sin fabricar 30 noches, algunas pruebas bajan los umbrales con `parada_de_prueba`, y
las pruebas de `noche_parada` usan los de verdad (30 y 40, con una aserción que los fija). Después de esa corrida sólo
cambió una palabra del docstring de la batería («2 a 24 noches» pasó a «2 a 25»); no se volvió a correr por eso.

**Nulo: no se corrió** (los dos cupos pesados del equipo estaban ocupados). Tiene **111 mutaciones**: las 55 de S168
(seis reescritas sobre el código nuevo: M20, M28, M34, M36, M53 y M55), las 14 que el verificador creía sobrevivientes
(17 mutaciones: V07 en tres variantes y V08 en dos) y 39 de las reglas nuevas (N01 a N39). Todas aparecen exactamente
una vez en el lector (`comprobar_unicas()` da vacío). Comando:

```
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"   # o el worktree de la rama
PYTHONIOENCODING=utf-8 C:/Users/nmend/AppData/Local/Programs/Python/Python312/python.exe -I experiments/_s168/v375e_sombra/mutar_sombra.py --hilos 1
```

Cuenta: 111 mutaciones más la identidad y el control son 113 corridas de la batería; a unos 7 minutos cada una, cerca de
**13 horas con un hilo** (6 a 7 con dos). Cabe antes del 2026-11-03 15:00 UTC, pero no en una tarde. Escribe
`experiments/_s168/v375e_sombra/mutar_sombra_salida.txt`.

## Lo que quedó sin resolver

- El nulo (arriba) y el verificador corto de otro modelo sobre este delta; después, el tag y Nicolás.
- La batería tarda unos 7 minutos, por encima de los 5 que pide el límite de procesos livianos (la de S168 tardaba 4).
  Lo que más pesa son las lecturas completas (bootstrap y calibración del evaluador común) en ocho escenas. No se
  recortó para no perder cobertura; si el cupo del nulo no alcanza, se puede bajar con escenas más chicas.
- El cenit del record de K contra `geometria_centro` del run sigue SIN VERIFICAR (como lo dejó el verificador).
- Los perfiles que S8 espera: el de K está comprobado (los 18 records VIIRS 375 de Láscar del 2026-10-25 al 2026-10-29
  06:36 en `origin/main`, anteriores a la ventana, traen `regimen.perfil` igual a `mirova_equivalent`). El de la vía
  (`sombra_codigo_mirova`) sale de leer el código de `origin/main` (`.github/workflows/sombra-codigo-mirova.yml` l. 122
  corre `run_pipeline.py --profile sombra_codigo_mirova`; `pipeline/profile.py` l. 69 y 76 toman ese nombre;
  `pipeline/store.py` l. 93 lo escribe), pero no lo vi en un record, porque no hay ninguno y no se abren: SIN VERIFICAR
  contra datos. Si no calza, S8 marcará la lectura y lo dirá.

## Ronda 2 (verificador limpio de S169, VL169-01 a 10)

Hecha el 2026-10-30 desde las 03:40 UTC. El verificador (Sonnet, sobre `983f6f28d`) dejó SELLABLE CON CAMBIOS con un
hallazgo de gravedad 3 y seis de gravedad 2 (`experiments/_s169/v375e_lector_verificador/INFORME.md`, rama
`loop/activo`). Las decisiones de cómo cerrarlos son de la coordinadora de S169; las reglas están en el §11 antes que el
código (tabla en §11.12; §1 a §10 siguen intactos: sha256 de las primeras 727 líneas sin CR `5af76cd5…348c`).

**Merge de `origin/main`** (VL169-05): `dcec35a8c`, sin conflictos, sin rebase ni force. `c42ee0eb7` es ancestro
(`git merge-base --is-ancestor`). S0 se recalculó sobre ese árbol: de los ocho archivos que ya fijaba sólo cambió
`scripts/auto_audit_weekly.py` (`3afd3e65…` a `9c4da61e…`); se sumaron `pipeline/store.py`, `pipeline/profile.py`,
`pipeline/f5_core.py` y `pipeline/profiles/mirova_equivalent.yaml`. El tag se corta sobre un descendiente de ese merge.

| hallazgo | texto (§) | código (función) | aserción nueva | en rojo |
|---|---|---|---|---|
| VL169-01 (3) una lectura por nombre y carpeta, no por ventana | §11.8 «Una sola lectura por ventana» | `ventana_ya_leida`, `registro_local`, `registro_remoto`, `leer_registro`, `anotar_registro`; `main` se niega (rc 2, sin escribir) antes de cargar nada y anota el registro antes de imprimir la lectura | el caso de `probe_b1b.py` con parada de prueba 9 y 12: primera lectura corte 11-12; otra referencia en la misma carpeta, rc 2; en otra carpeta, rc 2 (registro local); desde otro checkout, rc 2 (registro de `loop/activo`); `loop/activo` sin resolver, rc 2; sin guardas, la otra referencia da otro N (el mecanismo existe); la línea del registro; `registro_remoto` real (None y []); la línea ilegible | sí: R16, R18, R21, R22 (G); R17, R19 (H); R20 (K); R23 y N05 (J) |
| VL169-02 (2) caída contada como ATRAPADA | §11.10 y §11.12 | `seccion()` de la batería registra CAE y la batería sale 2; `correr()` del nulo da CAIDA con salida 2; `CONTROL_SECCION` | el control de caída (grupo F) | sí: `CONTROL_SECCION` sale con exit 2 y la sección del borde como CAE (F) |
| VL169-03 (2) S8 marcaba por todo `pipeline/` | §11.4 S8 «Qué se compara» | `nombres_git`, `mostrar_git`, `ast_sin_docstrings`, `grillas_sin_roi`, `cambio_significativo`, `diff_git` | no marcan: sólo `roi_v750`, sólo docstring y comentario, un perfil ajeno; marcan: `x0`, clave nueva, volcán nuevo, grilla ilegible, código de un `.py` de la vía, `.py` ilegible, `.py` nuevo, los dos perfiles | sí: R05, R09 (G); R06, R10, R11 (H); R07, R08 (I) |
| VL169-04 (2) fuera de `pipeline/` | §11.4 S8 | `RUTAS_REGIMEN` | marcan `volcanoes.yaml`, el workflow y `run_pipeline.py`; las rutas fijas | sí: R04 (G) |
| precisión de la coordinadora: la base de S8 | §11.4 S8 «La base de la ventana» y «El hueco» | `base_regimen`; `control_s8` compara contra la base e informa `c42ee0eb7` contra la base | la base es el primer record de la vía de la primera noche; mismo régimen no marca; una noche del medio que cambia marca; `c42ee0eb7` contra la base se informa sin marcar; sin records de la vía, marca | sí: R24 a R27 (J); N16 (I) |
| VL169-05 (2) objetos git | §11.4 S0 | merge; S0 recalculado | «c42ee0eb7 se resuelve en este checkout» | sin rotura: es procedimiento |
| VL169-06 (2) VRP_PROFILE y módulos sin sha | §11.4 S0 | `cargar_deps` | VRP_PROFILE con otro perfil no carga; sin VRP_PROFILE lo fija; `store.py` distinto no carga; los nombres fijados | sí: R01, R02 (G); R03 (H) |
| VL169-07 (2) S9 de cualquier sensor | §11.4 S9 | `main` filtra `sensor_bucket == "VIIRS375"` | con la fila tardía de MODIS y la última de VIIRS 375 el día del corte, S9 cae | sí: R12 (G) |
| VL169-08 (1) sin contadores con control caído | §11.4 | `analizar` deja `parada` en la salida reducida; `main` y `para_json` los imprimen | con 2 noches cae S6, rc 3 y salen «noches 2 de 30» | sí: R13 (G); R14 (H); R15 (I) |
| VL169-09 (1) rojo por grupos | §11.12 | ninguno | aceptado: lo cierra el nulo | no aplica |
| VL169-10 (1) V04 sin marca | §11.10 | `EQUIVALENTES` en `mutar_sombra.py` | se rotula en la salida del nulo | no aplica |

**El hueco que abre la base tomada de los datos** (escrito en §11.4 S8): el lector ya no comprueba que la primera noche
haya corrido con el código pre-registrado; si antes del 2026-11-03 entra a `main` un cambio que altera la vía o K, la
ventana sería coherente consigo misma y no marcaría. Queda a la vista porque la lectura informa, sin marcar, la
comparación entre `c42ee0eb7` y la base, con la lista de archivos; juzgarla es de Nicolás.

**Batería**: **227 de 227** sobre el árbol final, un proceso, en este computador, de las 06:17 a las 06:37 UTC del 2026-10-30 (salida en `experiments/_s168/v375e_sombra/probar_sombra_salida.txt`). Con el equipo cargado tarda de 15 a 20 minutos (antes, 7). Después de esa corrida no cambió ningún archivo de la batería ni del lector.

**Nulo**: **no se corrió**. Tiene **138 mutaciones** (las 111 de la primera ronda, dos de ellas reescritas sobre el código nuevo, M34 y N05, y N16 ajustada a la base; y 27 de la ronda 2, R01 a R27), más la identidad y dos controles de caída (`CONTROL` y `CONTROL_SECCION`). `comprobar_unicas()` da vacío. V04 queda declarada equivalente en `EQUIVALENTES`. Cuenta: 141 corridas de la batería; a 7 minutos son unas 16 horas con un hilo, y con el equipo cargado como hoy (15 a 20 min) más de 35. Comando:

```
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"   # o el worktree de la rama
PYTHONIOENCODING=utf-8 C:/Users/nmend/AppData/Local/Programs/Python/Python312/python.exe -I experiments/_s168/v375e_sombra/mutar_sombra.py --hilos 1
```

**La comprobación en rojo de la ronda 2** (`ver_en_rojo.py`, grupos F a K, salidas `rojo_F.txt` a `rojo_K.txt`): las 27 roturas R y N05 y N16 salieron EN ROJO. Tres tropiezos, todos del instrumento y no del lector: G no arrancó la primera vez porque R22 y R23 tocan la misma línea (R23 pasó a J), y la segunda vez R01 hizo caer la sección S0 de la batería y arrastró a las demás (se arregló el `next` de esa prueba y G se repitió entera); I pasó el tope de 30 minutos porque R20 hace que cada corrida que debía rechazarse haga la lectura entera (R20 pasó sola a K, con tope de 90 minutos); y en H, N05 no se vio porque el registro local también rechazaba: se agregó una prueba en que sólo la guarda de la carpeta puede rechazar, y en J N05 sale EN ROJO.

**Lo que quedó sin cerrar**: el nulo; un verificador corto de otro modelo sobre este delta; el tag (sobre un descendiente de `dcec35a8c`); el cenit del record de K (SIN VERIFICAR, igual que antes); el perfil `sombra_codigo_mirova` en un record real (SIN VERIFICAR contra datos); y el hueco de la base tomada de los datos, que queda informado pero no cerrado.
