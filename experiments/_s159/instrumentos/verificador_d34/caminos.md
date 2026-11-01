# caminos.md: por donde podria estar mal cada afirmacion (escrito ANTES de abrir ningun archivo citado)

Verificador del diff 63e310af5..c44709e27 (evaluador del A/B de D25). Commit del worktree
C:\vrp-trabajo\s159-evaluador: c44709e2755a5e6f6eb464bf83a997142a0d6378, rama s159-evaluador-d25.
Hora del servidor al abrir: Thu, 22 Oct 2026 04:53:09 GMT (header Date de gh api).

Lo unico que vi antes de escribir esto: `git diff --stat`, el listado de experiments/_s159/instrumentos/
y el espacio en disco. No abri ningun archivo citado.

## Afirmacion 1. D-30 (1): M MEJORA + calibracion de d' falla => INDECIDIBLE, no NEUTRO

- a. El veredicto INDECIDIBLE existe como literal pero se asigna en otra rama (por ejemplo cuando M
  no da MEJORA) y la rama MEJORA+calibracion-falla sigue dando NEUTRO o CUMPLE.
- b. La calibracion "falla" se define por otro predicado que el de la adenda (p. ej. solo cuando la
  tasa de falsos supera X, o solo cuando falta la cola de mejora, o cuando falla cualquiera de dos colas).
- c. El JSON de salida escribe INDECIDIBLE en un campo y NEUTRO en otro (dos representaciones del
  mismo veredicto; patron A46 del proyecto), y el consumidor lee el que no se cambio.
- d. La prueba que lo cubre arma un caso donde la calibracion falla por una causa distinta (comparador
  apagado, sin sustrato) y entonces no mide la rama de la afirmacion.
- e. Orden de evaluacion: si "sin sustrato" o "comparador apagado" se evalua despues, puede pisar
  INDECIDIBLE con otra cosa.
- f. El estrato sin MEJORA en M (EMPATE/EMPEORA) con calibracion fallida: que dice la adenda? Si la
  adenda tambien manda INDECIDIBLE ahi y el codigo no, es desviacion no cubierta por el titulo.

## Afirmacion 2. D-30 (2): la calibracion de d' exige solo la cola de mejora

- a. El codigo evalua las dos colas (mejora y empeora) con `and`, o evalua la cola de empeora en vez
  de la de mejora (signo invertido: segun como se defina d' positivo).
- b. "Solo la cola de mejora" esta en el §5 de la adenda pero el codigo lee un parametro
  (`--colas` o similar) con default distinto, o el caller pasa ambas.
- c. La prueba usa un placebo simetrico donde ambas colas fallan o pasan juntas, asi que no
  distingue "solo mejora" de "ambas".
- d. El tope de 5 % se aplica a la cola equivocada (p. ej. a la suma de las dos colas, o a la cola
  de empeora).
- e. La definicion de "mejora" en d' puede ser distinta de la de M (signo del neto: D menos K vs K
  menos D); si las dos difieren, la cola "de mejora" en d' puede ser la de empeora en M.

## Afirmacion 3. D-30: con --calibracion sellada el comparador queda apagado y el JSON lo marca

- a. El flag existe pero no se propaga a la funcion que decide (se lee en main y se pierde en el
  caller; A89/A6: el nombre del punto de uso no es el de la definicion).
- b. "Apagado" significa que no se calcula d' pero el veredicto sigue usando una rama que lo exige
  (entonces produce INDECIDIBLE en todo, o NEUTRO en todo).
- c. El JSON marca el estado del comparador en un campo nuevo pero otro campo viejo (p. ej.
  `comparador_resultado`) sigue con un valor por defecto que parece "calculado".
- d. El valor "sellada" es una cadena comparada con `==` y el argparse admite mayusculas o espacios
  distintos; o el default del argumento ya es "sellada" y entonces la produccion corre siempre apagada
  sin que nadie lo pida (o al reves: default "calcular" y nadie pasa el flag).
- e. Que la adenda diga eso. Puede que la adenda diga "apagado salvo que se pida", o que diga que se
  calcula igual y se informa sin decidir. Hay que leer el texto.
- f. Con comparador apagado, que pasa con la regla 1 (INDECIDIBLE si calibracion falla)? Si el
  comparador esta apagado no hay calibracion; el codigo puede caer en INDECIDIBLE por "falla" de
  calibracion ausente, o en CUMPLE sin la guarda.

## Afirmacion 4. D-32: calibracion de d' con 1.000 repeticiones, tope 5 % por cola, semilla fija, escritos en §5

- a. El 1.000 esta en el script de instrumentos (calib_dprima_1000.py) pero evaluar_d25.py usa otro
  default (p. ej. 200) y la adenda cita 1.000: el evaluador real corre con otro numero.
- b. La semilla "fija" se deriva de algo variable (hash de ruta, nombre de brazo, hora) o difiere entre
  el script de instrumentos y evaluar_d25.py.
- c. El tope "5 % por cola" se implementa como 5 % total (2,5 % por cola) o como 10 %, o se compara
  con `<` donde la adenda dice "a lo mas" (`<=`), o al reves.
- d. "Proporcional": el tope es una fraccion del numero de repeticiones (50 de 1.000) y el codigo usa
  un entero fijo que solo coincide con 1.000; con otro numero de repeticiones se descalibra.
- e. La adenda §5 cita numero y semilla, pero no los mismos que el codigo (p. ej. semilla 20251021 en
  la adenda y 2025 en el codigo).
- f. La salida de calib_dprima_1000 no es reproducible (sin semilla, o la semilla no alcanza a numpy
  y a random a la vez).
- g. El script calib_dprima_1000.py corre sobre datos reales del A/B (prohibido para mi): entonces
  solo puedo verificar que el codigo cite esos numeros, no reproducir la salida. Anotar SIN DATO.

## Afirmacion 5. D-34: P2 decidido como M (neto de errores sobre discordantes, bootstrap por bloques noche-volcan, GANA/PIERDE/EMPATE/BLOQUEA/SIN SUSTRATO, listas informativas)

- a. "Neto de errores": signo. La adenda dice "alertas bajo 1 MW que el brazo no publica, mas
  publicaciones en negativos limpios, D menos K". Si el codigo suma errores de D menos errores de K,
  el lado "bueno" es negativo. Un signo invertido en GANA/PIERDE o en BLOQUEA es el camino mas probable.
- b. "Sobre las pasadas discordantes entre K y D": el codigo puede calcular el neto sobre todas las
  pasadas (donde las concordantes aportan 0 y diluyen la varianza del bootstrap: el intervalo se
  angosta o se ensancha segun como se bloquee) o sobre discordantes definidos por otro predicado
  (publica distinto vs error distinto; una pasada puede publicar distinto sin cambiar el error si no
  es alerta ni negativo limpio).
- c. Bloques noche-volcan: el remuestreo puede ser por pasada (ignora la correlacion dentro de la
  noche, intervalo demasiado angosto, tasa GANA+PIERDE bajo nulo > 5 %), o por volcan, o por noche
  sin volcan. "Con la maquinaria y semilla de M": puede usar otra semilla, u otra funcion de bootstrap
  (percentil vs BCa), u otro numero de repeticiones.
- d. "Intervalo entero del lado bueno": GANA si limite inferior > 0 o >= 0? Con intervalos enteros
  (neto es conteo) el borde en 0 importa. La adenda debe decir si 0 cruza o no.
- e. BLOQUEA: "si el neto va en contra sin llegar a PIERDE". El codigo puede usar la estimacion
  puntual (neto observado < 0) o la media del bootstrap; y "bloquea CUMPLE" significa que el veredicto
  global no puede ser CUMPLE; puede estar implementado como "no cambia nada" o como que fuerza
  INDECIDIBLE o NO CUMPLE. Que la adenda diga cual.
- f. SIN SUSTRATO: "menos de 5 discordantes o menos de 3 noches": el `<` vs `<=` en 5 y 3; y "noches"
  = noches distintas entre los discordantes, o noches del estrato entero.
- g. Las dos listas informativas (gemelo y D-33) podrian no informarse, o informarse pero tambien
  decidir (p. ej. la regla gemelo sigue siendo la que decide y D-34 solo se informa: inversion).
- h. P2 "como M" pero sobre que estrato: M se decide por estrato (sensor x volcan?) y P2 puede ser
  global; o P2 por estrato con sustrato que casi nunca alcanza.
- i. Que "publica" sea el predicado del frontend con node (A97) y no una reconstruccion en Python para
  P2.
- j. La regla SN (0,05 MW o menos en VIIRS 375 cuenta como "no vio nada") y la original: P2 debe
  informar ambas; puede aplicar solo una.
- k. "Alertas bajo 1 MW que el brazo no publica": las protegidas (1 MW o mas) no entran al neto de
  P2; si entran, P2 mezcla con P1.

## Afirmacion 6. Las tres guardas que pidio el verificador anterior estan puestas

- a. Se pusieron dos de tres, o se pusieron tres pero una de ellas no es la pedida (otra guarda con
  nombre parecido).
- b. La guarda existe como funcion pero nadie la llama en el camino de produccion (A89).
- c. La guarda esta como `assert` que se desactiva con `python -O`, o como `warnings.warn` que no
  detiene nada.
- d. La guarda vigila un valor fijo (p. ej. "semilla == 2025") y no la propiedad (A117: vigilar por
  direccion, no por valor).
- e. No se cual es el informe del verificador anterior: tengo que leer solo la lista de guardas pedidas
  en verificador_comparador/, no sus argumentos. Riesgo: el informe de ese verificador puede listar mas
  o menos de tres; "tres" puede ser una cuenta del implementador.

## Afirmacion 7. Pruebas: roja 11/11 por asercion antes, verde 31/31 despues; probar_evaluar_d25 31/31; mutaciones 17/17 por asercion; suite 2.373 con arbol quieto

- a. "Roja por asercion" puede ser roja por ImportError/AttributeError (la funcion no existia antes):
  eso es caida, no asercion, y una prueba que cae antes del cambio no prueba que mida la regla.
- b. 31 verde incluye las 11 nuevas + 20 viejas, o 31 nuevas; contar.
- c. Mutaciones "atrapadas por asercion": el script puede contar como atrapada cualquier salida != 0
  (caida incluida). Comprobar que mutar_comparador.py distingue AssertionError de Exception y que su
  salida lo imprime por mutacion.
- d. Las 17 mutaciones pueden ser todas del comparador de M (D-30/D-32) y ninguna de P2 (D-34): la
  bateria no cubriria la regla nueva.
- e. 2.373 de la suite: puede haber corrido con el arbol en edicion (A112), o con `-x`, o excluir
  tests marcados; o el numero incluye skips. Re-correr sobre el arbol quieto y comparar.
- f. Las salidas .txt se escribieron a mano o estan truncadas; re-correr es lo unico que vale.
- g. La suite puede depender del disco (TMP en C vs worktree en D; reference_onedrive_no_sincroniza):
  acá el worktree esta en C:, asi que ese modo de falla no aplica, pero anotar si falla por relpath.
- h. Las pruebas de P2 pueden usar un bootstrap con pocas repeticiones (p. ej. 50) para correr rapido y
  entonces no miden la cobertura del intervalo; la cobertura la mido yo con sinteticos.

## Afirmacion 8 (agregada por quien orquesta antes de sellar). Signo del termino de alertas en P2 segun PREREGISTRO.md §5, fila «P2 suma bajo 1 MW»: una alerta bajo 1 MW que D publica y K no RESTA un error a D; una que K publica y D no SUMA un error a D

- a. El encargo al implementador traia el signo al reves: el codigo puede seguir el encargo y no el
  texto sellado. Hay que leer la fila P2 del pre-registro y comparar con `contribuciones_p2` y con lo
  que llama de evaluar_fk.py, sin asumir que la adenda GEMELO repite bien la fila.
- b. El signo puede estar bien en `contribuciones_p2` pero invertido en quien lo consume (A6: el
  caller transforma el argumento), por ejemplo al armar "D menos K" o al mapear a GANA/PIERDE.
- c. La funcion de evaluar_fk.py puede devolver "error" ya con signo (p. ej. 1 = error de D) y
  `contribuciones_p2` puede volver a aplicar el signo (doble inversion que da bien por azar en los
  casos simetricos de las pruebas).
- d. La prueba que cubre P2 puede usar un caso simetrico (mismo numero de alertas que D publica y que
  K publica) donde el signo no cambia el veredicto: la bateria no lo atraparia. Mi mutacion propia:
  invertir el signo del termino de alertas y ver si alguna prueba cae.
- e. "Alerta que D publica y K no" solo resta error a D si la alerta decide (bajo 1 MW, lectura A;
  SN en VIIRS 375). Si el codigo resta tambien por alertas que no deciden (0,05 MW o menos en V375,
  regla SN), suma mejora inexistente.
- f. La contraparte: "publicaciones en negativos limpios" tienen signo contrario (D publica y K no =
  +1 error de D). Si el codigo trata las dos categorias con el mismo signo, uno de los dos esta mal.

## Transversales

- La vara es el texto sellado (PREREGISTRO v2, ADENDA_CALIBRACION, ADENDA_PLACEBO §5, ADENDA_GEMELO) y
  las filas D-28/D-30/D-32/D-34 de LOOP_OBJETIVOS.md §5. Si el codigo cumple la adenda pero la adenda
  no recoge la fila de Nicolas, eso es hallazgo (vara equivocada).
- Las adendas pueden haberse editado en el mismo diff (ADENDA_PLACEBO +89 lineas, ADENDA_GEMELO
  nueva): el texto "sellado" se escribio junto con el codigo. Hay que mirar si el texto vino antes
  (commit 7cbee245a) o junto (c44709e27), y si algo del texto se ajusto al codigo en vez de al reves.
- Copia local: el worktree dice igual al remoto; verificar con `git fetch` sin pull? No puedo hacer
  git que cambie nada; `git fetch` cambia refs remotas. Uso `gh api` para leer el sha de la rama remota.
- Mis mutaciones propias: invertir el lado de BLOQUEA; cambiar 5 -> 4 y 3 -> 2 en SIN SUSTRATO;
  remuestrear por pasada; otra semilla; NEUTRO donde va INDECIDIBLE; `and` en vez de solo cola de
  mejora; tope 5 % -> 10 %; 1.000 -> 999 repeticiones; quitar discordantes del neto; sumar protegidas
  al neto de P2.
- Cobertura del bootstrap de P2 con sinteticos propios: nulo verdadero (GANA+PIERDE cerca o bajo 5 %),
  efecto grande (decide), y un nulo con correlacion intra-noche fuerte (si remuestrea por pasada, la
  tasa sube sobre 5 %: eso distingue bloque de pasada).

## Lo que NO voy a mirar

- El veredicto de D25, los datos reales del A/B, los artefactos de runs: prohibido.
- La implementacion de D-28 (b4258040c): ya verificada PARCIAL por otro; solo donde el diff la toca.
- El informe del verificador anterior mas alla de la lista de guardas pedidas.

---
Sellado. sha256 del contenido de arriba (sin esta linea ni la siguiente): 11a1db71b143e265d162194cda5925d9f51e5d4e2a35067ded01a4a06025108c
Hora del servidor al sellar: Thu, 22 Oct 2026 04:54:54 GMT
