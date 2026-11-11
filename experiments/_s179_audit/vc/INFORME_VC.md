# Verificación del frente C (instrumento y retrospectiva), auditoría S179

## 1. Encabezado

- Hora del servidor: inicio 2026-11-11 01:32:03 GMT; cierre de las mediciones 2026-11-11 01:55:14 GMT (cabecera Date de
  api.github.com; 2 llamadas de las 5 permitidas).
- Código medido: el lector de la retrospectiva en la ref de lectura `s178-retro-lectura` (`ba5ef81c5`, worktree
  `D:\vrp-trabajo\worktrees\s178-lectura`, rama `claude/s178-retro-lectura`, fuera de main). Su `leer_retro.py` es
  idéntico al de main `438a60a1e` (diff vacío, 1.469 líneas). Pre-registro: tag `s173-prereg-retro-sellado`, igual byte a
  byte al de `loop/activo` `0472cd95e`; no existe en main. Documentos del loop en `0472cd95e` (copia local comparada con
  `git show`, igual). K de disco: `e7cfbaf54`. Vía: artefactos de D2 y D4; K-gemelo: D3 (`C:\Users\nmend\vrp-temporales\s177_d{2,3,4}`).
- Modelo: Claude Opus 5.5. Esfuerzo: lo fija quien me lanzó; no lo veo desde dentro (SIN DATO).
- CARPETA: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s179_audit\vc\`. Temporal:
  `D:\vrp-trabajo\temporales\s179-audit\vc\` (286 MB).
- Caminos de falla escritos antes de abrir ningún archivo citado: `caminos.md` (sha256 `048b6874…` y hora al pie).
- Qué NO miré: el informe y `hallazgos.csv` del auditor (obstáculo deliberado); `c13_escribir_hallazgos_csv.py` del
  auditor (lo salté porque reproduce su CSV); `docs/PLAN_AUDITORIA_S179.md` y otras carpetas `_s179_*`; el código de
  `pipeline/` (no re-corrí ninguna pasada de la vía: no hay datos L1B locales y no se llama a NASA); el texto de V375-E y
  V750-A (no los necesité para estas afirmaciones); la vigilancia y la sombra; el frontend en navegador.

### Cómo medí (lo común a todo)

`vc01_insumos.py` arma los insumos con código propio (no reusé el aplanado del auditor). `vc02_reproducir_lectura.py`
importa el lector del worktree sin tocarlo y repite los pasos de su `main` con los mismos argumentos de la lectura
(`--caja-v750 B4`, `--v750a-sellado no`, montaje, excepciones y trozos de `experiments/_s178_lectura/`). Control: los
bloques `sensores`, `osf` y `alertas_de_la_tabla_sin_pasada_nuestra` salen **iguales** al `lectura.json` commiteado
(`vc02_reproducir_lectura_salida.txt`). Sobre esa tabla por pasada (43.061 filas) corren `vc03_analisis.py` y
`vc05_final.py` (vc03 cayó en su bloque 517 por un error de nombre mío, `LR.F4`; sus bloques 0 a 514 quedaron en su salida y los bloques 517 y NUEVO se corrieron aparte en vc05), que usan las funciones del propio lector donde la vara es el lector, y código propio donde la
afirmación dice que el lector no calcula algo. `vc04_banda_v375.py` mide C-montaje de VIIRS 375.

Las dos preguntas del instrumento, comunes: (1) si la tabla estuviera rota, la igualdad con `lectura.json` no se daría
(control positivo cumplido); (2) si el instrumento estuviera muerto, cada bloque imprime su denominador y aborta con 0.
Cada bloque de `vc03_analisis_salida.txt` lleva su propio control y su ventana.

## 2. En una pantalla

- De 17 afirmaciones y 4 juicios de decisión: 15 CONFIRMADOS, 6 CONFIRMADOS EN PARTE (501, DEC-2, 503, 504, 507, 510), 0 REFUTADOS, 0 SIN DATO. Ningún veredicto de la lectura cambia con lo medido.
- Lo más serio: el brazo radiante de VIIRS 375 (con el que el record publica hoy) pierde 3 protegidas sólo del OCR que K publica (2 en Isluga); la exención N-3 y un comparador de brazos que no mira esa condición las dejan fuera, y nunca se listaron. El brazo que decide (cercano) no pierde ninguna.
- Dos cifras del auditor son del brazo radiante, no del que decide en VIIRS 375: el sorteo da GANA por azar en 28,1 % con cercano (no 10,3 %), y la tabla de bajo 1 MW del OSF es 1.449 de 1.485 con cercano.
- Controles que no pueden fallar, confirmados: el «puede fallar» del nulo de runner (sigue verde con el K-gemelo roto a propósito) y el candado armado desde la misma ref de lectura.
- El §7, las capas de la referencia y K de disco: medido efecto 0 (cifras del §7 reproducidas exactas; 0 etiquetas cambian sin capas; K idéntico en 46.468 records).

## 3. Veredicto por afirmación (orden de gravedad propia, lo peor primero)

### 501 y DEC-2. Exención N-3 (L4) y protegidas sólo del OCR

- Veredicto: **CONFIRMADO EN PARTE**. Gravedad propia: **3**. Se funde con DEC-2 y con mi hallazgo VC-01.
- Lo confirmado. El texto sellado del §4.1 (pre-registro l. 232 a 234, TEXTO): «una protegida sólo del OCR **no veta**;
  se lista con la cabecera de la imagen revisada (A61) y, si la vía la pierde y K la publica, el sensor va a DECIDE
  NICOLÁS» y termina «N-3 queda subsumida». La fila 4 del §8.1 (l. 487) nombra «pérdida sólo OCR que K publica». El
  lector, en cambio, exime de la fila 4 a las protegidas N-3 (`leer_retro.py` l. 42 a 43, L4; `es_n3` l. 417 a 421;
  `solo_ocr_perdidas` l. 423 a 431; llamada con `n3=sensor != "MODIS"` l. 1309). Es una lectura más permisiva que la letra.
- Lo medido (`vc03_analisis_salida.txt`, bloque 501; F26-V, VIIRS 375, 2.556 pasadas evaluables, 2026-02-01 a 03-31):
  21 pasadas son protegida sólo en la unión con el OCR, todas Suomi NPP y todas N-3. Con el brazo **cercano** (el que
  decide), con o sin N-3: **0 pérdidas**. Con el brazo **radiante**, sin N-3: **3 pérdidas que K publica**: Isluga
  2026-03-20 05:06 (OCR 2,21 MW), Isluga 2026-03-24 05:30 (1,51 MW) y Láscar 2026-03-15 05:00 (1,54 MW). En VIIRS 750: 0
  con y sin N-3. `lectura.json` no trae `lab_union` en ningún campo: las 21 no se listaron, ni con su cabecera.
- Lo que no se sostiene tal cual: «con la letra del §4.1 sería fila 4» depende de qué brazo cuenta. Sobre el brazo que
  decide (§8.1, «sobre el brazo de posición que decide») la fila sigue siendo 6 aunque se quite N-3. Sólo sería fila 4 si
  el veredicto «al lado» del radiante (§5.1 l. 312, R-13) incluyera esa condición; y el lector no puede verlo aunque se
  quite N-3 (ver VC-01).
- Por qué gravedad 3: el §5.1 l. 312 dice que el record de la vía «publica hoy con radiante». Es lo que vería el
  operador si el paquete se enciende tal como está, y dos de las tres son de Isluga, un volcán de señal débil. Atenuante:
  son filas sólo OCR de Suomi NPP anteriores al 2026-10-09, donde la distancia y la clase pueden venir de otra pasada
  (hito impreso por el propio lector en su salida).

### 509. Nombre del veredicto de VIIRS 375 sin conteos

- Veredicto: **CONFIRMADO**. Gravedad propia: **2**.
- Bloque 509: en F26-V las 26 protegidas de la tabla son todas de Láscar. Isluga (2), Planchón-Peteroa (14) y
  Cordón Caulle (28) entran al nombre sólo por las protegidas OSF de 2025 (`nombre_fila6`, l. 1260 a 1265, une los dos
  conjuntos sin conteo ni tramo). El pre-registro l. 492, TEXTO: «El nombre de la fila 6 lo arma el lector con los
  conteos por volcán». El nombre reproducido es idéntico al de la lectura. Gravedad 2 porque ese nombre va a la Compuerta
  B (R-11) y sugiere evidencia de 2026 en volcanes débiles que no existe.

### 503 y DEC-3. Sorteo del §7 con la vía contra K

- Veredicto: 503 **CONFIRMADO EN PARTE** (las cifras de VIIRS 375 son de otro brazo); DEC-3 **CONFIRMADO** (no se aplicó). Gravedad propia: **2**.
- Confirmado: la decisión 2 de S174 (`tasks/LOOP_OBJETIVOS.md` l. 1179 en `0472cd95e`, TEXTO: «Lectura del §7
  (VPR940b-01): la vía contra K con las etiquetas barajadas, rotulada post hoc») no se aplicó: `sorteo_etiquetas`
  (l. 1156 a 1177) sigue con K contra K y la consola de la lectura dice «Cómo leer el §7 lo decide Nicolás».
- Medido (bloque 503; barajador del propio lector, 1.000 sorteos, semilla 172, estrato volcán por tramo de 10°):
  MODIS 8,4 % GANA (igual al auditor). VIIRS 375 con el brazo que decide (**cercano**): **28,1 %** GANA, 93,1 % GANA o
  EMPATE; con radiante 10,2 % (el 10,3 % del auditor es de radiante). VIIRS 750: 0,6 %. Lo observado sí se sostiene por
  otro camino: el neto observado (-7, -30, -11) es igual o más extremo que el barajado en 13, 0 y 1 de 1.000 sorteos.
  Control negativo: K contra K da SIN SUSTRATO en 1.000 de 1.000.
- Lectura: «GANA» como nombre no distingue a la vía del azar en VIIRS 375 (28 %); el tamaño del neto sí.

### 502. P2 de VIIRS 750 sin las pasadas miradas por nombre

- Veredicto: **CONFIRMADO**. Gravedad propia: **2** (el auditor dio 3).
- Bloque 502: VIIRS 750 con (b) GANA, B 17, neto -11; sin las 9 pasadas de (b): **EMPATE, B 9, neto -3**. MODIS: GANA B 6
  neto -7, sin (b) SIN SUSTRATO B 4 neto -4. `lectura.json` guarda sólo el número de fila sin (b) (`regla_sin_pasadas_b`,
  l. 1326 a 1328 y 1352) y el booleano `cambia_sin_pasadas_b`; nunca B, neto ni estado de P2 sin (b). El §3.1 l. 171 a 173
  pide informar «P1, P2 y M de F26-M y de F26-V (750) con y sin las pasadas de (b)».
- Por qué baja a 2: en VIIRS 750 la fila es 4 por V750-A sin sellar, con o sin (b); y EMPATE también pasa la regla de
  V750-A («GANA o EMPATE», §5.6 l. 390). Hoy no tuerce un veredicto; sí oculta que la ventaja de la vía en 750 descansa
  en las pasadas miradas por nombre.

### 505 y DEC-9. Candado y manifiesto

- Veredicto: **CONFIRMADO** (505 entero, incluido «efecto medido 0») y **CONFIRMADO** (DEC-9). Gravedad propia: **2** y **1**.
- Mismo ref, 31 s: commit `ba5ef81c5` 05:39:24 -0300 (ref de lectura con el lector de #979) y `f8304c161` 05:39:55
  (manifiesto «16 archivos desde s178-retro-lectura»). `armar_manifiesto.py` l. 68 a 69 calcula todo con `git show
  <ref>`; el lector compara contra el disco del mismo ref (l. 910 a 920). Así el candado no puede fallar por un cambio
  del lector posterior al despacho. Medido: sha256 LF de `leer_retro.py` en `s172-retro-d1`, `d2` y `d4` = `42bf4cb2…`;
  en la ref de lectura = `de9ec59c…` (cambió con D2 a D4 ya en disco). El propio docstring de `armar_manifiesto.py` l. 8
  dice que el ref «es el tag del despacho» y la bitácora l. 693 planeaba `--ref s172-retro-d2`.
- Fuera del manifiesto (`REQUERIDOS_MANIFIESTO` l. 890 a 893): `scripts/auto_audit_weekly.py` (importado por
  `banco_paridad.py` l. 63, define la noche), `volcanoes.yaml` (`banco_paridad.py` l. 105 y `leer_retro.py` l. 1435),
  `frontend/cambio_detector.js` (cargado por el predicado, `banco_paridad.py` l. 148) y las capas de historia y respaldo
  que `cargar_referencia_unificada` carga por defecto (`referencia_mirova_unificada.py` l. 161 a 163).
- Efecto 0, medido por dos caminos: (a) los blobs de esos cuatro archivos son iguales en el tag de despacho `a7a6ae360` y
  en la ref de lectura; (b) sin las capas, 0 de 8.384 etiquetas fuera de R25 cambian (bloque 505; control: la unión con
  capas tiene 46.710 filas contra 46.673).
- DEC-9: §11 se titula «Candado (sin esto no se despacha)» (l. 604). D1 salió el 2026-11-08 17:56 UTC «tras revisar el
  candado del §11» (bitácora l. 751), pero el 2026-11-10 01:17 UTC la bitácora todavía lista el manifiesto entre lo que
  falta (l. 693). No hubo manifiesto previo al despacho. Gravedad 1: lo que corrió está atado por los tags
  (`s172-retro-d1` a `d4` = `a7a6ae360`, medido).

### 510. C-montaje con la banda post hoc de VIIRS 375

- Veredicto: **CONFIRMADO EN PARTE**. Gravedad propia: **1** (el auditor dio 2).
- Confirmado: `montaje.json` de la lectura dice `"estado": "OK"`, `"diferencias": []`, sin rótulo; `lectura.json` no
  contiene «post hoc» (medido). El rótulo vive en la PROPUESTA (l. 113 y 122), en la bitácora (l. 630) y en un comentario
  de `montaje_ab.py` l. 130.
- Confirmado: el rango. Las 12 diferencias van de **-3,37 % a +7,43 %** (mínima en valor absoluto 0,03 %), no «entre
  0,3 % y 3 %» como dice `PROPUESTA_C_MONTAJE.md` l. 103 (`vc04_banda_v375_salida.txt` y, por otro camino, la salida
  commiteada `montaje_dm_salida.json`).
- Confirmado: la banda conserva poder. De 51 pasadas con celdas alertadas, quedan fuera de la banda 44 con un sesgo de
  +2 %, 46 con +3 %, 48 con +5 % y 47 con -5 %; con sesgo 0, 0 (control).
- En parte: «la causa triangulación no se probó re-corriendo». No encontré un artefacto de una re-corrida: el estado de
  `montaje_dm_salida.json` dice «re-correr con el código del tag de origen» como pendiente, y la PROPUESTA l. 110 afirma
  su resultado entre paréntesis. No puedo re-correr la vía (sin L1B, sin NASA): SOSPECHA, no medido.

### 512 y DEC-7. Tags de C-montaje fijados después de D3

- Veredicto: **CONFIRMADO**. Gravedad propia: **1** (el auditor dio 2).
- Decisión 6 de S174 (bitácora l. 1183, TEXTO: «se fijan antes del despacho de D3»). D3 salió el 2026-11-09 05:28 UTC
  (l. 738). El 2026-11-10 06:14 UTC: «ningún documento declara el tag de origen» (l. 666). Declaración en `c592ac2d2`,
  2026-11-10 08:04 UTC, con D2 (l. 736), D3 y D4 (l. 696) en disco. Atenuante: la declaración se commiteó antes de
  correr el comparador y dice no haber mirado D2 salvo el campo `roi` (PROPUESTA l. 3 y 60). Los tags elegidos salen del
  mensaje de cada tag y del `head_sha` de cada run (PROPUESTA l. 27 a 30), no de una elección libre.

### 504. Cobertura del K-gemelo sobre las pasadas que deciden P2

- Veredicto: **CONFIRMADO EN PARTE**. Gravedad propia: **1**.
- Bloque 504, brazo que decide: MODIS 2 de 7 discordantes cubiertas por el K-gemelo; VIIRS 375 4 de **44** (cercano; el
  46 del auditor no corresponde al brazo que decide); VIIRS 750 6 de 17. Total 12 de 68. Todas las cubiertas son de
  Láscar. Días del K-gemelo elegidos el 2026-11-09 al despachar D3 (l. 738, «antes de mirar datos»), una semana después
  del sello; el §10.3 (l. 568) no los fija. Por qué 1: C-K dio 0 diferencias en 3.138 pasadas y K de disco es idéntico
  entre `47cdc446f`, `a7a6ae360` y `e7cfbaf54` en las ventanas (517).

### 506. Curva de cenit sin veredicto y curva de R25 no calculada

- Veredicto: **CONFIRMADO**. Gravedad propia: **1** (el auditor dio 2).
- SIN SUSTRATO en los tres sensores (`lectura_salida.txt`); sabido desde el ensayo de S174 (bitácora l. 1104 a 1111,
  2026-11-06 13:11 UTC). `curva_cenit` sólo recibe las filas del tramo que decide (l. 1273 y 1310); R25 tiene sólo una
  mediana global (`razon_cota_mediana`, l. 1028 a 1031), sin cenit, aunque el §5.3 (l. 343 a 344) y la predicción 5
  (l. 530) la piden.
- Calculada aquí (bloque 506; OSF nocturno, class 1, dentro del radio, pareado a ±120 s, los dos brazos publican):
  K/OSF cae con el cenit (Spearman -0,43 MODIS n 226; -0,30 VIIRS 375 n 1.697; -0,41 VIIRS 750 n 17, este último dentro
  del nulo). La vía no cae (+0,06; +0,035; +0,14). Mediana de la vía por tramo de 10° entre 0,97 y 1,09 en MODIS y 1,00
  en VIIRS 375. Por qué 1: en R25 la razón es sólo cota (§4.3) y no decide; el resultado va a favor de la vía.

### 507. Bajo 1 MW del OSF en R25 no informadas

- Veredicto: **CONFIRMADO EN PARTE**. Gravedad propia: **1**.
- `p1_osf` (l. 971 a 1038) sólo trata protegidas, lejanas y ambiguas; el §4.2 l. 280 pide informar las bajo 1 MW.
  Cifras (bloque 507, VIIRS 375, 8 volcanes): 1.440 de 1.485 (97,0 %) es el brazo **radiante** sin piso SN; con el brazo
  que decide (cercano) 1.449 (97,6 %); K 1.399 (94,2 %). Con piso SN de 0,05 MW: cercano 1.332 de 1.354 (98,4 %), K 1.306
  (96,5 %). MODIS: vía 77 de 79, K 67 de 79. Control: con 1 MW o más el mismo código da 317 de 317, como `p1_osf`.

### 508. Noche del operador vacía en VIIRS

- Veredicto: **CONFIRMADO**. Gravedad propia: **1**.
- Bloque 508: 627 noches-volcán en F26-V; las 627 tienen una pasada NOAA-21 y todas las NOAA-21 evaluables son `sin_info`
  (868 en 375, 889 en 750); limpias calladas [0, 0] en la vía y en K, sin aviso (`noche_operador` l. 1203 a 1224). Sin
  exigir NOAA-21 serían 23 (375) y 46 (750). Es la letra del §5.5 (l. 369 a 370) aplicada a una población que el propio
  §3.2 (l. 189) ya sabía sin fila. Informa (R-10): no decide.

### 511. El control «el nulo de runner puede fallar»

- Veredicto: **CONFIRMADO**. Gravedad propia: **1**.
- `nulo_runner` l. 716 a 721: `puede` es verdadero si la mediana de d del placebo contra K no es 0, y esa cuenta no usa
  el K-gemelo. Medido (bloque 511): la mediana es -0,07918 = -log10(1,2) porque 265 de 353 pares tienen K bajo
  MIROVA/1,2. Con el K-gemelo roto a propósito (igual a la vía, o publicando todo), `puede` sigue True y la mediana no
  se mueve. El nulo mismo sí cae en esas mutaciones (B 34 y 294, ROJO): por eso gravedad 1.

### 513. M de MODIS

- Veredicto: **CONFIRMADO**. Gravedad propia: **1**.
- Bloque 513: vía d MEJORA (IC [-0,48; -0,20]); K x 1,2 también d MEJORA (IC [-0,079; -0,079]); d′ de la vía NEUTRO,
  mediana -0,034, IC [-0,1745; 0,000] (el auditor da -0,171; la diferencia es menor y no cambia nada), n 11, todos de
  Láscar. En la regla de MOD-D (`evaluar_f4.py` l. 660 a 681) M sólo actúa si es EMPEORA, así que no cambia la fila.

### 514. Lista de alertas sin pasada nuestra

- Veredicto: **CONFIRMADO**. Gravedad propia: **1**.
- Ventana del lector 2026-02-01 a 2026-10-16 (l. 351): 1.094 (igual a `lectura.json`), 1.089 fuera de todo tramo
  (abril 213, mayo 240, junio 211, julio 131, agosto 122, septiembre 165, octubre 7). Dentro de F26: 5, todas bajo 1 MW,
  0 protegidas; 3 son de Tupungatito antes del 02-23, fuera de la población, así que quedan las 2 del auditor (Lastarria
  y Cordón Caulle, 2026-03-10). DM: 0.

### 515. Decisiones 2, 3 y 4 del bloque S175

- Veredicto: **CONFIRMADO**. Gravedad propia: **1**.
- Bloque S175 l. 50 a 52; S176 l. 46 (decisión 7); S177 l. 45 (dentro de la 10). El S178 (l. 47, «Heredadas») ya no las
  nombra y el S179 tampoco (grep de «VPR952-04», «l. 409», «bloque S175» y «cenit»: 0). La frase «si a todo lo que
  recomiendes» (bitácora l. 834 a 837) enumera lo que cubre y no las nombra. Sin efecto en la lectura: cenit SIN SUSTRATO
  en los tres sensores.

### 516. sha256 del sello

- Veredicto: **CONFIRMADO**. Gravedad propia: **1**.
- Mensaje del commit `aa2a63079` y del tag anotado sin sha256. sha256 LF del archivo sellado: `b58a225404c8…`. El §11
  (l. 614 a 616) pide ese sha256 «en el mensaje del commit y en el tag del sello». La identidad la da el blob de git
  (`armar_manifiesto.py` l. 72 a 75).

### 517. Cifras del §7 no recalculadas

- Veredicto: **CONFIRMADO**. Gravedad propia: **1**.
- `recalcular_s7_ref_congelada.py` no tiene commits después del 2026-11-02 (`fcbb50c0e`). Entre `47cdc446f` y
  `a7a6ae360` cambiaron `frontend/index.html`, `cambio_detector.js`, `banco_paridad.py` y `auto_audit_weekly.py` (blobs
  distintos). Medido: K igual en las ventanas (46.468 de 46.468; `vc01_insumos_salida.txt`, con control: fuera de las
  ventanas difieren 107 y 638 claves) y las cifras del §7 se reproducen exactas con el código y el K de la lectura
  (`vc05_final_salida.txt`: protegidas 9/26/30, bajo 1 MW 5/158/25, bloques donde K yerra 6/48/18, K pierde Láscar
  2026-02-16 01:20). La omisión no cambió nada.

## 4. Hallazgos propios

- TÍTULO: VC-01. El comparador «cercano contra radiante» de VIIRS 375 no ve las condiciones de la fila 4 que no salen de la regla
- ARCHIVO:LÍNEA: `experiments/_s172_retro_paquete/leer_retro.py` l. 1330 a 1333 (main `438a60a1e` y ref de lectura)
- QUÉ PASA: la cámara ve el mismo calor con dos posiciones de cúmulo; con la posición radiante el tablero calla en 3
  pasadas donde el OCR de MIROVA vio 1,5 a 2,2 MW y K publicó. El lector compara cercano y radiante sólo por
  `_fila_regla` de `regla_v375`, que no incluye pérdidas sólo OCR, candidatas OSF ni la curva; además `solo_ocr_perdidas`
  sólo se calcula para el brazo que decide. Aunque se quitara N-3, las 3 pérdidas de radiante no llegarían al veredicto.
- CÓMO SE VE EN EL DASHBOARD: invisible en la lectura. Si se enciende el paquete con radiante, el operador no vería esas 3
  pasadas (Isluga 2026-03-20 05:06 y 03-24 05:30, Láscar 03-15 05:00, Suomi NPP).
- CÓMO REPRODUCIRLO: `python vc02_reproducir_lectura.py` y luego `python vc03_analisis.py 1000`, bloque 501.
- CONFIANZA: CONFIRMADO. GRAVEDAD 1-5: 3 (fundido con 501).

- TÍTULO: VC-02. P1-OSF de VIIRS 375 se calcula con el brazo radiante, no con el que decide
- ARCHIVO:LÍNEA: `leer_retro.py` l. 1436 (`p1_osf(filas, ...)` sin brazo; por defecto `"V"`, l. 971)
- QUÉ PASA: las candidatas a veto contra el OSF de 2025 y las lejanas publicadas como cumbre se miran con radiante en
  los tres sensores; en VIIRS 375 decide cercano. Medido: con cercano da lo mismo (317 de 317, 0 candidatas).
- CÓMO SE VE EN EL DASHBOARD: invisible; efecto medido 0.
- CÓMO REPRODUCIRLO: `python vc05_final.py`, bloque NUEVO.
- CONFIANZA: CONFIRMADO. GRAVEDAD 1-5: 1.

- TÍTULO: VC-03. Dos cifras del auditor del frente C son del brazo radiante en VIIRS 375
- SCRIPT:SALIDA: `vc03_analisis_salida.txt`, bloques 503 y 507; `c07_sorteo_s7.py` y `c02_tabla_pasadas.py` del auditor usan `pub_V` (record tal cual)
- QUÉ PASA: el 10,3 % del sorteo y el 1.440 de 1.485 son de radiante. Con cercano: 28,1 % y 1.449. No cambia la
  dirección de 507; en 503 empeora el poder del nombre GANA.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python vc03_analisis.py 1000`.
- CONFIANZA: CONFIRMADO. GRAVEDAD 1-5: 1.

Duplicados fundidos: DEC-2 con 501 y VC-01; DEC-3 con 503; DEC-7 con 512; DEC-9 con 505.

## 5. SEGUIMIENTOS (fuera de mi eje)

- Con qué regla de posición publica la vía de VIIRS 375 en el encendido B1 (#974): si es radiante, VC-01 deja de ser
  sólo de la retrospectiva. No lo miré. SOSPECHA.
- `PROPUESTA_C_MONTAJE.md` l. 103 («entre 0,3 % y 3 %») está mal; no la corrijo (no es mi eje).

## 6. VERIFICADO LIMPIO

- La lectura es reproducible con insumos armados por otro camino: `sensores`, `osf` y la lista de C-cobertura iguales a
  `lectura.json` (vara: el JSON commiteado en `ff8a39972`). `python vc02_reproducir_lectura.py`.
- Candado OK al re-correrlo contra el manifiesto commiteado (vara: el manifiesto; ver 505 sobre lo que no puede ver).
- K de disco idéntico en las ventanas entre los tres commits (vara: igualdad de JSON por record). `python vc01_insumos.py`.
- Aplanado de D2+D4 y D3: 223 y 30 archivos de trozo, 42.389 y 3.282 records, 0 claves repetidas.
- Capas de la referencia: 0 etiquetas cambian (vara: las etiquetas de la tabla sola y de la unión del propio lector).

## 7. SIN DATO

- Si re-correr la vía de VIIRS 375 sobre los 12 gránulos de DM da otro VRP (causa triangulación): sin L1B local y sin
  llamar a NASA, no se puede medir.
- Esfuerzo con que corrí.

## 8. FUERA DE ALCANCE

- Si la regla de MOD-D debía usar d o d y d′ para M (texto de MOD-D fase 4 no leído).
- La validez del texto de V375-E §8.13 (N-3) y de V750-A §6 ter.
