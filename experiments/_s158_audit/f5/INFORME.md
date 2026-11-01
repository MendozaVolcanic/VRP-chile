# F5, auditoría S158: los instrumentos contra el código de MIROVA

Frente F5 (metrólogo). Rama `s158-d17-diseno`, worktree `D:\vrp-trabajo\temporales\s158_d17`, 2026-10-21. Solo lectura:
todo lo que escribí está en `D:\vrp-trabajo\temporales\s158_d17\experiments\_s158_audit\f5\`. Leí enteros los dos `.m`
de MIROVA (`experiments/_s158_d17_diseno/osf_codigo_mirova/MIROVA_VIIRS750_hotspot_detection.m`, 444 líneas, y
`MIROVA_VIIRS750_VRP.m`, 92 líneas) antes de afirmar nada sobre MIROVA. Lo que digo de MIROVA en VIIRS 375 o MODIS va
marcado TRASLADADA.

Ventana de la referencia: `scripts/calidad_referencia_mirova.py` (`avisar`) sobre 2026-09-18 a 2026-10-18 y 2026-08-23 a
2026-10-21 avisa de los hitos del OCR del 2026-10-09 y 2026-10-10 (Suomi NPP y filas sin geometría); ninguna de mis
mediciones decide con filas sólo OCR de Suomi NPP. Todas usan la referencia congelada de V1 del pre-registro de D25
(`experiments/_s157_prereg_d25/_congelado_v1/`, Mirova-v1@35a5ea86), salvo la m5, que usa `latest_consolidado.csv` como
lo hace `libro_de_cuentas.py`.

## Hallazgos, de mayor a menor gravedad

### F5-01. El A/B de D25 ya terminó, sin el 2026-10-18 entero, y ningún control del evaluador lo ve

- **SCRIPT:SALIDA** `m6_cobertura_ab_d25.py` → `m6_salida.txt`; `gh run view 39530508296`; `evaluar_d25.py:504-526`.
- **QUÉ PASA.** La mañana del 18 de octubre, con Chillán en erupción (en producción, VIIRS de 2,8 a 14,0 MW en las ocho
  pasadas de esa mañana), es justo el caso por el que el pre-registro estiró V1 hasta el 18 (§4: «con V1 estirada hasta
  el 18-oct para meter la mañana de Chillán»). Los tres brazos del run no tienen **ninguna** pasada VIIRS de ese día en
  ninguno de los 11 volcanes: 86 pasadas faltan contra producción, más 44 del 12 y 22 del 13 de octubre (152 de 4.762
  pasadas VIIRS de producción en la ventana V1, 3,2 %). En el log del brazo de control de Chaitén (el trozo 4 de Chaitén
  terminó en verde), las búsquedas del 18 devuelven `n=0` en el estándar y en el NRT de todas las plataformas VIIRS
  (`_rama/log_ctrl_Chaiten.log` l. 3932 a 3977: `VNP02IMG_NRT v2 2026-10-18..2026-10-18 n=0`, `VJ102IMG_NRT ... n=0`,
  `VJ202IMG_NRT ... n=0`). Una búsqueda que da cero no es una falla, así que `--estricto-cobertura` no sale con 3.
  En la ventana V1 de la referencia congelada hay, el 18, 6 filas de alerta protegida de VIIRS 375 y 5 de VIIRS 750 de
  Chillán; el 12 y el 13, otras 3 de Chillán y 1 de Isluga (filas, no pasadas: la tabla y el OCR pueden repetir una
  pasada).
- **Por qué ningún control lo ve.** (1) El chequeo del workflow (`recolectar`, «COBERTURA PAREJA») compara brazos entre
  sí, y los brazos de un trozo comparten los gránulos: un día sin gránulos falta en todos por igual (salida del run:
  4.610 pasadas por brazo, 0 faltan). (2) El control del evaluador contra producción (`evaluar_d25.py:518-522`) corta en
  5 % por volcán y sensor; el máximo medido es 3,8 % (Isluga), así que pasa en los 22 pares volcán-sensor. (3) La
  lista de protegidas sin record (`evaluar_d25.py:514-516`) se arma sobre `todas`, que son las claves de las tablas de
  los brazos (l. 504): una protegida que no tiene record en **ningún** brazo no entra a `todas` y no puede faltar. El
  evaluador diría «cobertura pareja: OK».
- **Estado del run, que contradice el prompt de esta auditoría («en cola»).** Run 39530508296 `completed / failure`,
  intento 2, actualizado 2026-10-21 13:55:42 UTC. Intento 1: 44 trozos verdes, Llaima-4 y Villarrica-4 con código 3
  por descargas de MODIS Aqua (`nrt3.modaps` ConnectTimeout; MODIS está apagado en los brazos pero se baja, H17), y su
  `recolectar` publicó la rama `s146-ab/39530508296` (4b6d7f5f, 09:11:53 UTC). Intento 2: re-corrió esos dos trozos y su
  `recolectar` falló al empujar (la rama ya existía, «fetch first», 5 intentos); su salida quedó sólo como artefacto
  `s146ab-todo` (13:55:31 UTC). Hay dos versiones de los resultados y nada dice cuál evalúa.
- **CÓMO SE VE EN EL DASHBOARD.** Invisible: es un A/B. Lo que cambia es la decisión que de él salga.
- **CÓMO REPRODUCIRLO.** `python -B experiments/_s158_audit/f5/m6_cobertura_ab_d25.py` (usa las copias de la rama en
  `_rama/`; se bajan con `gh api repos/MendozaVolcanic/VRP-chile/contents/experiments/_s146_ab_sin_test1/salidas/39530508296/_s157_ab_d25_k_control/<volcán>.json?ref=s146-ab/39530508296 -H "Accept: application/vnd.github.raw"`). Chillán 2026-10-18 05:06, 05:42, 06:00 y 06:48 UTC, I y M.
- **Instrumento.** (1) Si faltara un día entero, la m6 lo ve: cuenta por fecha. (2) Con archivos vacíos el total daría
  0; dio 4.610, igual que el workflow. Control positivo: Chaitén, trozo verde, pierde el mismo día (el defecto no es
  del código 3).
- **CONFIANZA** CONFIRMADO (faltantes y lógica del evaluador). SOSPECHA la causa del `n=0` del NRT el 18 (¿retención de
  LANCE, colección?): no la medí.
- **GRAVEDAD 3.** El A/B no se sesga entre brazos (falta igual en todos), pero pierde el caso que lo motivó y unas 4 a 5
  protegidas que deciden por sensor en V1 (el pre-registro calculó el poder del veto con 31 y 29), y el evaluador lo
  declararía completo.

### F5-02. La métrica M del A/B de D25 da MEJORA con una ganancia constante sin física

- **SCRIPT:SALIDA** `m1_pares_y_predicados.py` → `m1_salida.txt`, secciones (a) y (a2).
- **QUÉ PASA.** Físicamente, D25 cambia el fondo que se le resta al píxel caliente. La métrica M pregunta otra cosa: si
  el VRP del brazo queda más cerca del VRP que MIROVA publicó. Mientras K esté por debajo de MIROVA en un estrato (razón
  mediana 0,35 a 0,68 en los cuatro estratos que deciden, sobre los pares de producción con K, 2026-09-18 a 2026-10-18),
  **cualquier** subida de la magnitud acerca: para todo par con K·c < MIROVA, d = −log10(c) exacto, y el intervalo del
  bootstrap colapsa a un punto. Apliqué la regla del evaluador (`regla_m`, `pesos_bloque`, `calibrar_simetrico` y la
  regla de dos volcanes de la adenda sellada D-27, importadas de `evaluar_d25.py` sin cambios) a un brazo placebo
  D = c·K:

  | estrato (modo) | n pares / noches | K/MIROVA | c = 1,10 | c = 1,28 |
  |---|---|---|---|---|
  | VIIRS750 z≤40 (decide) | 21 / 19 | 0,678 | **MEJORA** (3 volcanes) | **MEJORA** |
  | VIIRS750 z>40 (decide) | 19 / 10 | 0,353 | NEUTRO (1 volcán) | NEUTRO (1 volcán) |
  | VIIRS375 sin kernel z≤40 (decide) | 58 / 49 | 0,503 | **MEJORA** (4 volcanes) | **MEJORA** |
  | VIIRS375 sin kernel z>40 (bloquea) | 59 / 40 | 0,418 | NEUTRO (no cuenta) | NEUTRO |

  Con la calibración simétrica en vigor, una ganancia de 10 % sin ningún cambio de fondo cumple el criterio de M del
  §8 d («MEJORA en al menos un estrato que decide», ninguno EMPEORA). P1 y P2 no lo atajan: una subida no oculta
  protegidas, y los filtros del tablero que podrían apagarla no dispararon nunca en siete meses (F5-07). Con la
  calibración sellada original, c = 1,28 da INDECIDIBLE en los tres estratos que deciden y c = 1,10 da MEJORA en VIIRS 375
  sin kernel con cenit bajo (`m1_salida.txt` (a2)).
- **Por qué importa con el código a la vista.** `MIROVA_VIIRS750_VRP.m:83-91` suma el exceso de **todos** los píxeles
  alertados de la ventana de 67 × 67 (los tres dominios BOX, `MIROVA_VIIRS750_hotspot_detection.m:241-248`), con un
  fondo interpolado bajo un hueco dilatado y sin recorte. El déficit de K tiene entonces al menos tres causas posibles
  (fondo, selección de píxeles, recorte), y M no separa ninguna: premia al brazo que suba, compense lo que compense. El
  pre-registro lo sabe a medias (§9: «D25 no agrega píxeles»), pero su resumen sellado dice que el fondo de vecinos es
  «lo que hace MIROVA» (`RESUMEN_SELLO.md:3`; también `PREREGISTRO.md:34-35`), y el código dice que no: MIROVA aparta
  justo esos vecinos (`MIROVA_VIIRS750_VRP.m:68-78`) e interpola desde más afuera (l. 81). Un CUMPLE se leería como
  «adoptamos el fondo de MIROVA».
- **Matiz que juega a favor de D25 (m2).** En la única pasada con verdad de MIROVA (Etna 2023-05-19, matriz de ejemplo),
  sobre los mismos 5 píxeles: fondo del código 9,881 MW; D (media de los 8 vecinos no alertados) 10,152 MW (+2,74 %);
  una **aproximación** de nuestro fondo de VIIRS 750 (mediana de la BT de M13 en el anillo de 5 a 25 km del centro de la
  grilla remuestreada, con recorte) 2,748 MW (−72,2 %, un píxel recortado). En ese caso D25 sí se acerca al fondo del
  código y M premiaría la dirección correcta. Es un caso, de un volcán costero y alto, con un anillo que no es el de
  producción (que se arma sobre el barrido nativo, `pipeline/detection_context.py:1042`).
- **CÓMO SE VE EN EL DASHBOARD.** Invisible hasta la adopción. Si D25 se adopta por M, la magnitud publicada sube.
- **CÓMO REPRODUCIRLO.** `python -B experiments/_s158_audit/f5/m1_pares_y_predicados.py` (7 s);
  `python -B experiments/_s158_audit/f5/m2_etna_tres_fondos.py`.
- **Instrumento.** (1) Si M estuviera rota (siempre NEUTRO), c = 1,10 no daría MEJORA: la da. (2) Control positivo en
  las dos direcciones: c = 1 da NEUTRO con intervalo [0,000; 0,000] en los seis estratos, y en los estratos con kernel,
  donde K ya calza (0,96 y 0,78), c = 4 da EMPEORA en los dos y c = 2 en el de cenit bajo.
- **CONFIANZA** CONFIRMADO (medido con las funciones del evaluador). Límite: pares de producción, no del brazo K del run,
  y con la regla de etiquetas original (no SN).
- **GRAVEDAD 3.** Puede llevar a adoptar un cambio de método por una razón que no es la que se cree. Lo frenan el ciclo
  A45, la verificación R2 por píxel y el «sí» de Nicolás, pero el veredicto que llega a esa mesa diría MEJORA.
- **Arreglo posible (decide quien orquesta).** Un brazo o un contraste placebo: comparar D contra K·mediana(D/K) en
  dispersión de log10(D/MIROVA), no sólo en nivel. Si D25 sólo sube el nivel, su dispersión es la de K.

### F5-03. La regla SN cuenta como «MIROVA no vio nada» pasadas en que el detector de MIROVA sí alertó (TRASLADADA)

- **ARCHIVO:LÍNEA** `scripts/clase_mirova.py:97` y `:167` (SN: alerta de VIIRS 375 de 0,05 MW o menos pasa a RUTINA con VRP 0);
  `MIROVA_VIIRS750_VRP.m:45-52` y `:83-91`.
- **QUÉ PASA.** En el código de MIROVA un VRP publicado mayor que cero sólo existe si la lista de píxeles alertados no
  está vacía: con la lista vacía la función devuelve NaN (l. 45-52), y no hay umbral de magnitud para llamar alerta a
  una detección. Una fila de 0,04 MW es, en VIIRS 750, una detección del algoritmo con poca energía. La regla SN la
  convierte en negativo limpio, y entonces una publicación nuestra ahí cuenta como error (P2) en vez de acierto. La
  regla se apoya en el banner NONE de la imagen, que es una categoría de presentación de la cadena operacional, que el
  código compacto no incluye (README: excluye «near-real-time reporting»). La regla es sólo de VIIRS 375, donde no hay
  código: lo de arriba es TRASLADADO desde VIIRS 750.
- **CÓMO SE VE EN EL DASHBOARD.** Invisible; cambia el puntaje de los A/B en VIIRS 375 bajo 0,05 MW (155 pasadas según
  la docstring de `clase_mirova.py:93`, no recontadas por mí).
- **CÓMO REPRODUCIRLO.** Lectura de las líneas citadas. Los evaluadores informan también la regla original y «manda la
  más estricta» (`evaluar_d25.py` constante `ORDEN`), lo que limita el daño a la decisión.
- **CONFIANZA** CONFIRMADO lo que dice el código de VIIRS 750; SOSPECHA que valga para VIIRS 375.
- **GRAVEDAD 2.** D-9 es decisión de Nicolás; el código agrega un argumento que D-9 no tenía a la vista.

### F5-04. «Negativo limpio» = fila RUTINA con VRP 0,0, y el código da al menos tres caminos distintos a ese 0,0

- **SCRIPT:SALIDA** `m3_csv_vrp.py` → `m3_salida.txt`; `scripts/banco_paridad.py:324-325`.
- **QUÉ PASA.** En la tabla congelada, las 8.451 filas RUTINA traen el texto exacto `0.0`, ninguna fila trae VRP negativo
  ni vacío, y la alerta más chica vale 0,01. El código de MIROVA produce: NaN si no hay alerta o la escena se rechaza
  (sun-glint bajo 12°, l. 87-89; la mitad o más de NaN, l. 163-167, con los píxeles de M15 bajo 200 K convertidos en NaN,
  l. 150-154), y un VRP **negativo o casi cero** si hay alertas pero el exceso sobre el fondo interpolado no es
  positivo, porque no recorta (VRP.m:83-85). Si la tabla publica los tres como 0,0, el negativo limpio mezcla «el detector
  no vio nada», «la escena no se pudo usar» y «el detector vio algo y el fondo se lo comió». Para la réplica las tres
  son «MIROVA no publicó», así que contar una publicación nuestra ahí como error es correcto. Lo que no es correcto es
  leer la tasa de publicación en negativos como «gritamos fuego sin fuego»: en la tercera clase hay calor detectado y
  nuestro recorte por píxel (`process_viirs_mod.py:1056`, según el punto 12 de `docs/S158_CODIGO_MIROVA_VS_VRP_CHILE.md`)
  lo dejaría positivo.
- **CÓMO SE VE EN EL DASHBOARD.** Invisible.
- **CÓMO REPRODUCIRLO.** `python -B experiments/_s158_audit/f5/m3_csv_vrp.py`.
- **CONFIANZA** CONFIRMADO el contenido del CSV y del código; SOSPECHA cómo codifica la tabla de MIROVA un NaN o un
  negativo (no lo puedo ver desde aquí; S146 I-11 no encontró imagen con calor y tabla RUTINA en 400 pares, que es
  evidencia en contra de la tercera clase).
- **GRAVEDAD 2.**

### F5-05. `libro_de_cuentas.py` está fuera de banda hoy y nadie lo corre; además su noche de MIROVA deja fuera a Terra

- **SCRIPT:SALIDA** `_libro_copia.py` (copia del libro con la salida a mi carpeta y sin `pytest`) → `libro_salida.txt`;
  `m5_libro_recall_por_mes.py` → `m5_salida.txt`; `m4_noche.py` → `m4_salida.txt`.
- **QUÉ PASA.** (1) Hoy el libro da `recall_v750_dash` **75,44 %** contra 85,06 declarado y banda de 78 a 92
  (FUERA_DE_BANDA), y `D5_ratio_global` 0,692 contra 0,73 (DERIVA). El último `docs/LIBRO_DE_CUENTAS.json` es del
  2026-09-02 (b0066a6c7) y decía 85,12; ningún workflow ni prueba lo corre (`grep libro_de_cuentas .github/ tests/`: 0).
  Por mes, el recall cae también antes de K (enero a agosto 76,5 % sobre 238 noches; septiembre y octubre 69,8 % sobre 43),
  así que no es sólo el detector: SIN ATRIBUIR. (2) Su recall mezcla los dos detectores en una sola cifra (ventana 2026
  entera, A104). (3) `experiments/_s126_lib.py:139`, que el libro usa como lado MIROVA, llama nocturna a una alerta sólo
  si su hora UTC está entre 03 y 09: de las 20 filas de alerta MODIS nocturnas por elevación solar de 2026 en la
  referencia congelada, 7 (35 %) caen a las 01 o 02 UTC (pasadas nocturnas de Terra) y quedan fuera. En VIIRS las dos
  definiciones coinciden (448 de 448 y 85 de 85). Además ese cargador no usa la unión histórica ni el respaldo (A11, S150).
- **CÓMO SE VE EN EL DASHBOARD.** Invisible: el libro alimenta documentos, no decisiones de alerta.
- **CÓMO REPRODUCIRLO.** `python -B experiments/_s158_audit/f5/_libro_copia.py`; `python -B experiments/_s158_audit/f5/m5_libro_recall_por_mes.py`.
- **Instrumento.** El libro se marca a sí mismo FUERA_DE_BANDA, o sea que funciona; lo que falta es que alguien lo mire.
  `git_mb` da 0,0 en este worktree porque `.git` es un archivo: artefacto del worktree, no del repo.
- **CONFIANZA** CONFIRMADO.
- **GRAVEDAD 2.**

### F5-06. El documento S158 da por físico que el halo inmediato está más tibio; el oráculo, en su único caso, dice lo contrario

- **ARCHIVO:LÍNEA** `docs/S158_CODIGO_MIROVA_VS_VRP_CHILE.md` §4.3 (párrafo «El fondo del VRP es el caso más delicado»);
  `experiments/_s158_oraculo_mirova/mutar_oraculo_salida.txt` y mi `m2_salida.txt`.
- **QUÉ PASA.** El documento dice que el halo de un foco «todavía lleva calor» y que D25, al tomarlo como fondo, «se
  come parte del exceso» (o sea, D bajaría el VRP respecto de MIROVA). En Etna pasa al revés: con la media de los 8
  vecinos no alertados el VRP **sube** 2,74 % sobre el del código, y sin la dilatación sube 0,76 %: allí los vecinos
  inmediatos están más fríos que el fondo interpolado desde más afuera. Es un caso, pero es el único con verdad, y la
  afirmación no lleva la marca [LECTURA PROPIA] que el documento usa para lo suyo.
- **CÓMO SE VE EN EL DASHBOARD.** Invisible.
- **CÓMO REPRODUCIRLO.** `python -B experiments/_s158_audit/f5/m2_etna_tres_fondos.py`.
- **CONFIANZA** CONFIRMADO para Etna; el signo en los volcanes chilenos no está medido.
- **GRAVEDAD 2.** Orienta la lectura de D25 y la recomendación a Nicolás del §7 de ese documento.

### F5-07. Los filtros de artefacto del tablero no dispararon nunca en siete meses: P5 del pre-registro no tiene sustrato

- **SCRIPT:SALIDA** `m7_rama_artefacto.py` → `m7_salida.txt`.
- **QUÉ PASA.** De 27.063 records nocturnos de los 11 Tier A entre 2026-03-01 y 2026-10-20, 3.060 son cumbre y válidos,
  y en **ninguno** dispara `isThermalArtifact` (cirrus o campo difuso, `frontend/index.html`, función `isCirrusArtifact`
  y siguientes). El pre-registro de D25 (§3, fila «filtros del tablero») los lista como consumidor que podría apagar
  una publicación que D25 sube; con K y con el detector anterior, ese camino no se ha usado en el periodo.
- **CÓMO SE VE EN EL DASHBOARD.** No cambia nada hoy.
- **CONFIANZA** CONFIRMADO. **GRAVEDAD 1.**

## Fuera de alcance (anotado y sigo)

- **A76 contra el código.** `CLAUDE.md` A76 dice que MIROVA limpia los artefactos solares diurnos «por supervisión
  MANUAL, no gate automático». El código tiene un rechazo automático de escena por sun-glint bajo 12°
  (`MIROVA_VIIRS750_hotspot_detection.m:87-89`) y procesa el día con umbrales propios (l. 188-199: K1 −0,5, 15σ, 0,02).
  No cubre toda reflexión solar sobre nube (el glint especular es otra geometría), pero «no gate automático» queda
  refutado para VIIRS 750. Es de F2. El comentario de `experiments/_s126_lib.py:140` («A76: artefacto de reflexión
  solar») justifica con A76 el corte de horas de F5-05.
- **El intento 2 del run 39530508296 no pudo publicar** y dejó dos versiones de los resultados (F5-01). Es de
  infraestructura del workflow (`recolectar` no contempla una rama ya existente en un re-intento).

## VERIFICADO LIMPIO

- **El criterio «dash» del auto-audit coincide con el predicado del tablero ejecutado con node, record por record.**
  Vara: `banco_paridad.cargar_nuestros` (node sobre `frontend/index.html`, A97). Ventana 2026-09-18 a 2026-10-18,
  3.573 records nocturnos: 0 discordancias en MODIS (706), VIIRS 375 (1.439) y VIIRS 750 (1.428); en pasadas con alerta
  de MIROVA, 0 de 252. Comando: `python -B experiments/_s158_audit/f5/m1_pares_y_predicados.py`, sección (b). Límite:
  la rama de artefactos del predicado no se ejercitó (F5-07).
- **La réplica en Python de `libro_de_cuentas.r_recall_v750_dash` coincide con el predicado con node** en los mismos
  3.573 records (sección (c) de la m1): 0 discordancias. Con K el camino `triggered_test1` no se ejercita.
- **`INNER` del auto-audit = `inner_radius_km` del tablero = `volcanoes.yaml`** en los 11 Tier A (m1, sección (d)).
- **La noche por elevación solar es robusta en el crepúsculo**: 0 filas de alerta de 2026 con elevación entre −12° y 0°
  (m4). El `dayflag` de MIROVA no se publica (es una entrada del `.m`, l. 31-33), así que no se puede comparar, pero no
  hay casos de borde donde pudiera discrepar.
- **La conectiva y los umbrales de cumbre que codifican los instrumentos de K son los del código**: `max(μ + Nσ,
  mínimo)` (`hotspot_detection.m:306-312`, `:376-382`) y, en la caja de 7 × 7 que es BOX==2, 5σ y 0,003 de noche
  (l. 181, 184, 187). Vara: el `.m`. La regla de adopción de K midió contra MIROVA con el predicado del tablero, que es
  lo que el código dice que importa: lo publicado.
- **El oráculo reproduce Etna**: 5 píxeles y 9,8809 MW con el fondo del código (m2), igual a `README.md` del oráculo.
- **Pruebas del evaluador de D25 corridas hoy**: `python -B experiments/_s157_prereg_d25/probar_evaluar_d25.py
  experiments/_s158_audit/f5/_probar_d25_tmp` da «RESUMEN: 27 de 27 casos OK» en 9 min (`probar_d25_hoy.txt`), igual que
  `probar_salida.txt`. Límite: ninguna de las 27 pruebas siembra un día sin gránulos en todos los brazos (F5-01) ni un
  brazo placebo de ganancia constante (F5-02); por eso pasan.
- **La referencia que usan los evaluadores no tiene VRP negativos ni texto raro**: 8.451 RUTINA en `0.0`, alertas con
  VRP de 0,01 o más (m3).

## Lo que no pude medir

- **La causa del `n=0` del NRT el 2026-10-18** en las búsquedas del run (F5-01): no consulté CMR.
- **Si la salida del intento 2 (artefacto `s146ab-todo`) tiene el 18**: no la bajé (3,6 MB, y descargar artefactos pide
  permiso); por el conteo de su `recolectar` (4.610 por brazo, idéntico al intento 1) lo más probable es que tampoco.
- **El veredicto del A/B**: no corrí `evaluar_d25.py` sobre el run, a propósito, para no mirar resultados antes de que
  quien orquesta decida qué hacer con F5-01 (pre-registro §7).
- **`evaluar_fk.py`** lo revisé en su construcción de la tabla (comparte `armar_tabla.py`, `banco_paridad` y
  `clase_mirova` con el de D25, así que F5-01 a F5-04 le aplican igual en su lógica), pero no re-corrí su
  `probar_evaluar_fk.py` ni sus mutaciones: no alcanzó el tiempo.
- **`vigilancia_sombra.py`**: leí su salida vigente (`data/audit_continuous/sombra_latest.json`, VERDE, 2026-10-21 01:59
  UTC, 154 de 257 pasadas de alerta con record de la sombra, sombra desde el 2026-10-02) y su definición de MIROVA
  (scraper, lectura A, nocturna), que coincide con la de los otros instrumentos. No medí su poder ni le hice mutaciones.
- **Cuánto de la caída del `recall_v750_dash` del libro (85 a 75) es de los datos y cuánto del denominador** (F5-05):
  no reconstruí el corpus de S130 (A90).
