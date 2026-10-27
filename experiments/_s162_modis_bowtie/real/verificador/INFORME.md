# Verificación con contexto limpio: ablación real del bow tie MODIS (S162 MOD-E E3)

## 1. Encabezado

- Fecha y hora del servidor al empezar: Sat, 24 Oct 2026 19:18:15 GMT (header `Date` de api.github.com).
- Commit sobre el que medí: `6e3084df1fa8c9ca2285666711b9e245494bc0c8` (worktree `s162-modis-774bb0`, rama
  `claude/s162-modis-774bb0`). Instrumento del lote: el árbol `experiments/_s162_modis_verif_cde/arbol/` es el commit
  `0e18e1053` para `mirova_port.py`, `probe_portes.py`, `mirova_v750_r2.py`, `pipeline/process_modis.py`,
  `scripts/banco_paridad.py` y `frontend/index.html` (sha256 iguales tras normalizar CRLF a LF; sin normalizar
  difieren por los finales de línea de Windows, no por contenido).
- Modelo y esfuerzo: Claude Fable 5.1, verificador con contexto limpio (sin leer el INFORME.md del auditor hasta
  terminar `caminos.md`; sigo sin leerlo al escribir los veredictos, sólo recibí título, script y gravedad).
- CARPETA: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s162-modis-774bb0\experiments\_s162_modis_bowtie\real\verificador\`
- Scripts del auditor verificados (sha256 en `sha256_scripts_auditor.txt`): `comun.py`, `01_reproducir.py`,
  `02_cobertura.py`, `02b_rendijas.py`, `03_ablacion.py`, `04_casos.py`. Mis copias `rerun_*.py` sólo cambian la
  línea del `sys.path` para importar el `comun.py` del auditor y dejar las salidas en esta carpeta.
- Qué NO miré: el código MATLAB original de MIROVA (OSF) para saber qué método exacto de bow tie usa (D28 lo deja
  abierto); el pipeline de producción K (`process_modis.py`) más allá de `merge_mir_bands`; el PSF real del sensor
  (la huella que se usa es la nominal, paso entre centros, declarada así por el auditor); las 10 pasadas no
  evaluables (8 `volcan_fuera_del_granulo`, 2 `grilla_incompleta`); los 3 PNG o figuras que pueda haber hecho el
  auditor; VIIRS (no tiene bow tie de 10 detectores igual, fuera de alcance). Tampoco corrí nada contra GitHub
  (2 llamadas a la API, sólo para la hora del servidor).

## 2. En una pantalla

1. B1 CONFIRMADO: las cinco salidas y los dos json del auditor se reproducen bit a bit; además la B21 y la geometría de
   5 km rearmadas coinciden 403/403 con las variantes que el lote guardó; el árbol es el commit 0e18e1053.
2. B2 CONFIRMADO: la huella sale de la geolocalización (1,0 → 1,7 km a lo largo, 1,0 → 3,3 km a lo ancho), el «2+»
   es inter-barrido en más del 99 %, y las rendijas de A cierran ya al ×1,05 (63 %) y ×1,10 (87 %) mientras las de B y C no
   cierran ni al ×1,5. Precisión: A deja 8,4 % del suelo bajo dos barridos (quita sólo centros cubiertos).
3. B3 CONFIRMADO en conteos (11 protegidas publican con A; neg_resto 2 → 0 con A_ant, 2 → 1 con A_sig; B mata la
   protegida Chillán 141 de 5,18 MW). Pero los flips son al filo: márgenes NTI de 1e-6 a 8e-4 (VBT-01).
4. B4: «sólo donde el foco sale dos veces» REFUTADO (Láscar 79, cráter visto una vez, +8,7 % por σ global al quitar
   duplicados a 8 km, VBT-02); «el signo depende de la copia» EN PARTE (1 de 3); «det 0/9 no delimita» CONFIRMADO
   (28 de 102 en z>=50); «estrato 2+ huellas» EN PARTE (91 de 102, pero 1 de 2 cambios de publicación queda fuera).
5. Para D28: lo medido sostiene «A sin huecos, 11 protegidas intactas, 2 publicaciones menos»; no sostiene que el
   efecto esté confinado al foco duplicado ni que el conteo 2 → 0 sea una propiedad robusta del método.

## 3. Veredictos por afirmación

Convención: «todos» = el port tal cual (remuestrea con duplicados); A_ant = `A_centro_cubierto_ant` (conserva la
copia del barrido anterior); A_sig = `A_centro_cubierto_sig` (conserva la posterior); B = `B_filas_borde`; C =
`C_sin_det0` (control positivo de huecos). Denominador común: 403 pasadas evaluables de 413 objetivos MODIS del lote
40120713181 (8 `volcan_fuera_del_granulo`, 2 `grilla_incompleta`), ventana **2026-03-01 01:35 a 2026-10-21 08:05
UTC**, 11 volcanes Tier A; 390 `neg_resto` + 13 `control_s159` (11 protegidas). Estratos de cenit del sensor en el
cráter: z<15 n 55, 15-25 n 43, 25-40 n 78, 40-50 n 71, z>=50 n 156.

### B1. Rearmar la grilla desde el nativo reproduce el lote en 403 de 403 (npix, VRP, celdas), con control negativo B21

**Veredicto: CONFIRMADO.** Gravedad propia: 1 (no hay defecto; la reproducción es exacta y el instrumento ve cambios).

Evidencia de esta sesión:
- `rerun_01_reproducir.py` → `rerun_01_stdout.txt`: «reproduccion exacta (npix, VRP a 1e-9 MW y mismas celdas): 403
  de 403; max |dVRP| 4.179e-13 MW»; «control negativo (B21 primaria en vez de B22): distinto en 13 de 13 pasadas con
  deteccion». Idéntico a la salida del auditor.
- Caminos cerrados (`caminos.md` B1.1 a B1.8):
  - B1.1 «el port se compara contra sí mismo»: no. `01_reproducir.py:43` compara contra `res[i]["port"]["fisica"]`,
    que es el json `resultados_MODIS_*.json` escrito por el runner Linux (8 archivos, 413 filas: 405 `ok`, 8
    `volcan_fuera_del_granulo`; 2 `grilla_incompleta`), no una corrida local.
  - B1.2 tolerancia: `igual()` exige npix igual, |dVRP| ≤ 1e-9 MW e identidad de celdas (fila, columna) ordenadas
    (`01_reproducir.py:20-29`), no conteo. Control positivo mío (`v01_reproduccion_otro_camino.py` (3)): una celda
    corrida una columna → `igual = False`; VRP + 2e-9 MW → `False`; lat/lon corridas una fila → grilla distinta,
    `igual = False`, npix 8 → 6 en Chillán 141.
  - B1.3 control negativo débil: cierto que sólo informa sobre las 13 pasadas con detección (en las 390 vacías un
    «igual» vacío no distingue nada). Lo cubrí por otro camino: la B21 primaria rearmada coincide con la variante
    `port.fisica_b21` que el lote **también guardó**, 403 de 403 (5 con detección), y la geometría de 5 km
    (`lat_5km`/`lon_5km`) rearmada coincide con `port.fisica_geo5km` del lote, 403 de 403 (11 con detección), siendo
    la grilla con geo 5 km distinta de la MxD03 en 403 de 403. Tres variantes independientes reproducidas exactas: el
    rearme usa los mismos insumos que el runner. (`v01_reproduccion_otro_camino_salida.txt`.)
  - B1.4 el npz no es el insumo del lote: `envoltorio_nativo.py:62-97` guarda `lat_mxd03 = crop["lat"]` ya cortada
    por el probe «con las mismas rebanadas» y los índices `linea`/`frame` del gránulo; la reproducción 403/403 por
    tres variantes lo confirma empíricamente.
  - B1.5 universo: 413 npz en disco, 413 filas en los json, 403 evaluables por el mismo criterio que
    `07_leer_lote.py` (`comun.evaluable`). Las 10 excluidas están contadas, no silenciadas.
  - B1.6 copia atrasada: el árbol `arbol/` es el commit **0e18e1053** (el que `probe-s162-negmodis.yml:7` declara
    como instrumento congelado) para los 6 archivos clave, sha256 iguales tras normalizar CRLF.
  - B1.7 determinismo: `semillas=0` (`comun.py:117-118`), sin jitter; VRP coincide a 4e-13 MW entre el runner Linux y
    Windows, así que acá no aparece el argsort inestable de S152.
  - B1.8 ventana: 2026-03-01 a 2026-10-21, cruza #535 (2026-08-28) y el flip K (2026-10-18). Para el port eso no
    importa (no es producción), pero cualquier lectura de `neg_resto` hereda la definición de K del lote.

Pregunta 1 del instrumento: sí, una grilla mal rearmada se vería (lat/lon corridas una fila cambia npix 8 → 6).
Pregunta 2: sí, el comparador distingue (controles (3) de v01).

### B2. El método A quita duplicados sin abrir huecos reales (rendijas que cierran con huella +20 %); la regla B sí abre huecos

**Veredicto: CONFIRMADO, con dos precisiones** (abajo). Gravedad propia: 2 (las precisiones no cambian el veredicto,
pero una de ellas acota qué tan «sin duplicados» queda A).

Evidencia de esta sesión:
- `rerun_02_cobertura.py`: salida y `02_cobertura.json` **idénticos** a los del auditor (diff vacío; json igual,
  403 pasadas).
- **La huella nominal es la del sensor, no un modelo plano** (`v02_huella_y_duplicados.py` (a)): en el píxel del
  cráter, el paso entre detectores a lo largo (a) va de 1,00 km (z<15) a 1,71 km (z>=50, rango 1,44 a 2,12) y el paso
  entre frames a lo ancho (b) de 1,00 a 3,32 km (rango 2,13 a 5,29). Sale de la geolocalización MxD03 del npz, no de
  una fórmula. El paso entre barridos es 10,06 km (mín 9,82, máx 10,19) en todo el barrido, y 10 × a llega a 17,1 km
  en z>=50: los barridos vecinos se pisan en ~7 km de los 17. El cenit del npz en el píxel del cráter coincide con el
  `z` de la tabla de objetivos (máx |dif| 0,38°, mediana 0,04°). Es la huella NOMINAL (paso entre centros, sin PSF),
  declarada así en `comun.py:14-16`; para contar duplicados del bow tie basta, porque el traslape de barridos es de
  varios píxeles enteros, no de fracciones de PSF.
- **«Visto 2+ veces» sí mide duplicados del bow tie** (`v02` (b), separando por origen): en z>=50 con «todos», 0,6665
  del suelo de la caja ROI1 está bajo 2+ huellas y **0,6590 bajo 2+ barridos distintos**; el traslape de huellas del
  mismo barrido es 0,0075. En el nadir, 0,0042 / 0,0017 / 0,0025. Camino B2.2 de `caminos.md` cerrado: el doble conteo
  es inter-barrido en ≥ 99 % en los estratos oblicuos.
- **Las rendijas de A se cierran progresivamente, no sólo al 20 %** (`v02` (c)): huecos nuevos de A respecto de
  «todos» en z>=50: +0,0161 (huella ×1,00), +0,0060 (×1,05), +0,0021 (×1,10), +0,0003 (×1,20), +0,0001 (×1,50). Es
  decir, 63 % de los huecos nuevos desaparecen con 5 % de agrandamiento y 87 % con 10 %: son rendijas finas entre
  paralelogramos vecinos, no suelo sin mirar. Controles: los huecos de C (detector entero sin copia) **no** se cierran
  (nadir: +0,0968 → +0,0844 a ×1,20 → +0,0554 a ×1,50) y los de B tampoco (z>=50: +0,0484 → +0,0207 a ×1,20 →
  +0,0093 a ×1,50; 25-40: +0,0511 → +0,0322 → +0,0118). El 20 % no está ajustado al resultado: el orden A ≪ B < C se
  mantiene a cualquier escala.
- **B sí abre huecos reales** y además **mata una protegida** (ver B3): en 25-40 abre 5,1 % de suelo nuevo sin ver
  porque quita filas de borde donde todavía no hay traslape (en ese estrato A no quita casi nada en el cráter).
- **La asignación barrido/detector no depende de dónde empieza el recorte** (`v03_control_barrido_detector.py`): 297
  de 403 recortes NO empiezan en frontera de barrido (`linea[0,0] % 10` ∈ {2, 4, 6, 8}), pero `comun.geometria`
  usa `linea // 10` sobre la línea del gránulo (`comun.py:134-136`). Control positivo: con `linea + 1` la máscara de
  A_ant cambia en 156 de 156 pasadas z>=50 y sigue vacía en 55 de 55 del nadir. Y el salto en u del detector 9 al
  detector 0 del barrido siguiente es **−5.262 m** en z>=50 (el barrido siguiente arranca atrás del anterior: eso
  es el bow tie) contra +1.089 m en el nadir, con 1.000 m entre detectores vecinos.

Las dos precisiones:
1. **A no deja la escena «sin duplicados»**: tras A_ant, en z>=50 queda 0,0841 del suelo de ROI1 bajo 2+ barridos
   distintos (contra 0,6590 con todos) y 0,0389 con la huella achicada a 0,8 (02b del auditor). A quita el píxel
   cuyo CENTRO cae dentro del tramo de centros del barrido anterior; los que se traslapan parcialmente (centro
   fuera, huella dentro en parte) se conservan. Es coherente con no abrir huecos, pero el brazo debería llamarse «sin
   duplicados de centro cubierto», no «sin duplicados». Sin consecuencia sobre el veredicto; sí sobre cómo se
   rotule el brazo en MOD-D.
2. En 25-40 A abre +0,0012 de huecos nominales (todos cierran a ×1,10). Rendijas, igual que en z>=50.

Pregunta 1: la cobertura ve huecos reales (C en el nadir: 10,7 %; B: 4,8 a 6,4 %). Pregunta 2: el nulo de «todos» en
el nadir es 0,0102 de huecos nominales → 0,0006 a ×1,20, 0,9856 visto una vez.

### B3. Con A las 11 protegidas siguen publicando; las 2 publicaciones de neg_resto se apagan (copia anterior) o queda 1 (copia siguiente); donde A no quita nada la grilla es idéntica

**Veredicto: CONFIRMADO en los conteos; la interpretación «A apaga las 2» hay que leerla con VBT-01** (cada flip
está al filo del umbral). Gravedad propia: 3.

Evidencia de esta sesión:
- `rerun_03_ablacion.py` y `rerun_04_casos.py`: salidas y `03_ablacion.json` **idénticos** a los del auditor (diff
  vacío). Conteos reproducidos: neg_resto n 390, «todos» publica 2 (1120 Llaima 2026-07-24 01:05 z 62,9; 1251
  Láscar 2026-05-11 07:55 z 38,1); A_ant publica 0 (pierde 1120 y 1251), A_sig publica 1 (pierde 1120), B publica 1
  (pierde 1251), C publica 2 (gana 1093, pierde 1251). Protegidas n 11: A_ant, A_sig y A_huella publican 11; **B
  publica 10 (pierde 141, Chillán 5,18 MW de MIROVA)**; C publica 10 (pierde 89). Nulo por construcción: «pasadas
  sin quitar nada con grilla distinta» = 0 en los 5 métodos; A_ant quita algo en 311 pasadas y la grilla cambia en 299.
- «Publica» es la vara declarada: `03_ablacion.py:65-71` arma `record_port` (`04_analizar.py:59-72`, vrp_mw =
  primary_cluster.vrp_mw = VRP del código, summit si el centroide ≤ inner) y lo evalúa con `B.correr_node`, el mismo
  camino que `07_leer_lote.py:99-108`. Camino B3.1 de `caminos.md` cerrado.
- Camino B3.2 («A apaga el foco porque le quitó el píxel caliente»): **no**. En 1120 con A_ant el nativo más caliente
  (barrido 127, det 7, 265,5 K a 0,07 km) se conserva; lo que cambia es el fondo local 3 × 3 de la celda (27,25): su
  contraste c_nti baja de +0,00393 a +0,00244 contra un umbral de cumbre de 0,003 (`v04_mecanismo_cambios_salida.txt`).
  En 1251 con A_ant la celda (24,25) cambia 0,01 K y su c_nti pasa de +0,00445 a +0,00358 contra u_nti2 = 0,00359:
  queda **1e-6 por debajo** (`v04c`: «max margen no alertadas −0,000001»). Con A_sig el mismo píxel queda +0,00068
  arriba y publica. Es exactamente el camino B3.3: la copia conservada decide un contraste de 1e-5 en NTI.
- Camino B3.4 (grilla idéntica es tautológico): sí lo es, pero el control sirve para descartar no determinismo del
  remuestreo: `griddata` lineal sobre los mismos puntos da bit a bit lo mismo (0 de 92 pasadas sin quitar nada con
  grilla distinta en A_ant).
- Camino B3.5 (magnitud de las protegidas): ninguna protegida cruza 1 MW hacia abajo con A (mínimo con A_sig: 147
  Chillán 1,343 MW contra 2,18 de MIROVA; 97 Láscar ya estaba en 0,973 con «todos» y no cambia). Con A_sig la
  mediana port/MIROVA de las 11 baja de 1,074 a 0,956 y el rango de [0,760; 1,734] a [0,616; 1,645]: ver B4.
- Camino B3.6 (los 2 controles no protegidos): no publican con ningún método (n 2, «todos» 0).
- Camino B3.7 (poder): 2 de 390 publicaciones en neg_resto es 0,5 %; apagar 2 no es una «mejora» medible de la
  paridad, es la supresión de dos flips al filo. El auditor no afirma mejora en la tarea que me dieron; lo anoto para
  quien orqueste MOD-D.

### B4. La magnitud de las protegidas cambia sólo donde el foco sale dos veces; el signo depende de la copia; «cráter en detector 0 o 9» no delimita la franja duplicada sobre 50°; el estrato útil es «cráter cubierto por 2+ huellas»

**Veredicto por partes:**
- «cambia sólo donde el foco sale dos veces»: **REFUTADO** (gravedad 3). Caso 79 (Láscar 2026-03-15 07:45, z 30,5,
  cráter cubierto por **1** huella, detector 2): con A_ant y A_sig el VRP sube de 1,953 a 2,123 MW (×1,087) y npix de 3
  a 4. A quita 557 nativos, **ninguno en la caja ROI1**, el más cercano a 8,1 km del cráter; con A_sig **0 de 225
  celdas de ROI1 cambian** de valor y las celdas alertadas no cambian ni 0,001 K ni en c_nti/c_eti. La celda (24,24)
  entra por la **pasada 2** porque la desviación GLOBAL del contraste NTI (sobre las 51 × 51 celdas) baja de 0,000717
  a 0,000714 al cambiar ~130 celdas a más de 8 km, y el umbral de cumbre u_nti2 = μ + 5σ baja de 0,003585 a
  0,003568, mientras la celda vale 0,003577: margen −7e-6 → +9e-6 (`v04b_pasada2_caso79_salida.txt`). También 75
  (Láscar z 40,5, 1 huella) cambia ×1,004 con A_sig. La frase correcta es: la magnitud cambia donde el foco sale dos
  veces **y además** en cualquier pasada oblicua donde una celda del cráter esté a menos de ~1e-5 del umbral
  global, porque quitar duplicados en el borde de la grilla mueve σ.
- «su signo depende de qué copia se conserva»: **CONFIRMADO EN PARTE** (gravedad 2). De las 3 protegidas con el
  cráter bajo 2+ huellas, sólo en **65** el signo cambia con la copia (A_ant ×1,059, A_sig ×0,949); en **141**
  (×0,937 / ×0,824) y **147** (×0,918 / ×0,736) las dos copias **bajan** la magnitud, la posterior más. Con n = 3 la
  afirmación general sobre el signo es anécdota; lo que sí se sostiene es que conservar la copia posterior baja más
  (3 de 3), y que el auditor dejó el signo de la magnitud como SIN DATO (mensaje del commit c805fed19), lo que es
  correcto.
- «“cráter en detector 0 o 9” no delimita la franja duplicada sobre 50°»: **CONFIRMADO** (gravedad 2).
  `v05_estratos_crater.py` sobre mi `02_cobertura.json` (idéntico al del auditor): en z>=50 (n 156) A quita el píxel
  del cráter en 102 pasadas; de ellas sólo 28 tienen el cráter en det 0 o 9, y 74 no. A_ant quita el cráter en
  detectores {0: 18, 1: 14, 2: 15, 3: 8, 4: 1}, A_sig en {6: 13, 7: 12, 8: 11, 9: 10}: la franja duplicada sobre 50°
  abarca ~4 detectores por lado, no 1 (coincide con la fracción quitada por detector del 02 del auditor:
  [0,96; 0,96; 0,92; 0,54; 0,01; 0; …]). Y los 6 cambios de npix con A_ant caen todos en «det 0/9 = False» (n 343),
  ninguno en «True» (n 60).
- «el estrato útil es “cráter cubierto por 2 o más huellas”»: **CONFIRMADO EN PARTE** (gravedad 3). En z>=50 el
  estrato captura 91 de las 102 pasadas donde A quita el píxel del cráter (11 se le escapan: cráter bajo 1 huella
  nominal pero centro cubierto) y mete 17 donde A no quita el cráter. Para los cambios reales de A_ant: de 2 cambios
  de publicación, 1 cae dentro (1120) y **1 fuera** (1251, z 38, 1 huella); de 6 cambios de npix, 4 dentro y **2 fuera**
  (79, 1251). El estrato no delimita el efecto porque el efecto tiene dos caminos, uno local (la copia del cráter) y
  otro global (σ de la escena, VBT-02). Un estrato mejor para el camino local es «A quita el píxel del cráter» (no
  depende de la huella: 132 pasadas), pero tampoco cubre el camino global (mismos 2 cambios fuera).

Lo que más importaba («que lo concluido sobre D28 se siga de lo medido»): **se sigue en los conteos** (A no abre huecos
reales, conserva las 11 protegidas, apaga 2 publicaciones de neg_resto), **no se sigue** la lectura de que el efecto
esté confinado al foco duplicado, y la huella nominal no fabrica el efecto (los cambios de publicación y de magnitud
salen del detector, con la huella sólo se estratifica).

## 4. Hallazgos propios (VBT-01 en adelante)

### VBT-01. Los dos apagados en neg_resto y los dos cambios de npix en protegidas son flips al filo del umbral (márgenes de 1e-6 a 8e-4 en NTI), no una propiedad robusta del método
- ARCHIVO:LÍNEA / SCRIPT:SALIDA: `v04c_margenes_13_detecciones.py` → `v04c_margenes_13_detecciones_salida.txt`;
  `v04_mecanismo_cambios_salida.txt` (casos 1120, 1251); oráculo `arbol/experiments/_s158_audit_r2/oraculo/mirova_v750_r2.py:88-94`
  (u_nti2 = max(μ + 5σ, 0,003)).
- QUÉ PASA: el contraste NTI de la celda alertada contra su umbral de cumbre vale +0,00063 en 1120 y +0,00078 en 1251
  con «todos» (umbrales ~0,003 a 0,005, σ de la escena ~0,0007 a 0,001). Quitar duplicados mueve el fondo local 3 × 3
  o σ global en 1e-5 a 1e-3 y el píxel cae (1251 con A_ant queda a −1e-6). En 147 la celda (25,23) sale con A_sig con
  margen previo de +2,9e-5. Tres de las celdas que entran o salen con A tenían |margen| < 1e-4 en «todos». El resultado
  binario «A apaga 2 / A_sig apaga 1» es correcto como medición y frágil como conclusión: cualquier otra perturbación
  del remuestreo del mismo tamaño (otra triangulación, otra copia) daría otro conteo.
- CÓMO SE VE EN EL DASHBOARD: una alerta MODIS de 0,3 a 0,4 MW en Llaima o Láscar que aparece o desaparece según el
  método de bow tie, sin que el volcán haya cambiado.
- CÓMO REPRODUCIRLO: `python -I v04c_margenes_13_detecciones.py` en CARPETA; Llaima 2026-07-24 01:05 UTC, Láscar
  2026-05-11 07:55 UTC.
- CONFIANZA: CONFIRMADO (medido).
- GRAVEDAD: 3 (torcería la lectura de «qué cambia al quitar duplicados» si se tomara el conteo 2 → 0 como efecto del
  método; no toca ninguna protegida).

### VBT-02. Quitar duplicados a más de 8 km del cráter cambia la detección en el cráter por la σ GLOBAL del umbral de cumbre (segundo camino que el estrato del auditor no cubre)
- SCRIPT:SALIDA: `v04b_pasada2_caso79.py` → `v04b_pasada2_caso79_salida.txt`; `v04_mecanismo_cambios_salida.txt`
  (caso 79: quitados en ROI1 = 0, más cercano 8,11 km, celdas de ROI1 cambiadas 0 de 225 con A_sig).
- QUÉ PASA: el umbral de la pasada 2 del oráculo se calcula con μ y σ del contraste sobre toda la grilla de 51 × 51 km
  (`mirova_v750_r2.py:88-90`). Al quitar ~130 celdas duplicadas en el borde, σ baja 3e-6 y una celda del cráter que
  estaba 7e-6 bajo el umbral entra: Láscar 79 pasa de 3 a 4 píxeles y de 1,953 a 2,123 MW (+8,7 %) con el cráter
  visto una sola vez. Es el camino B4.6 de `caminos.md`.
- CÓMO SE VE EN EL DASHBOARD: una magnitud MODIS de Láscar 8,7 % mayor según el brazo, en una noche en que la escena
  del cráter es idéntica.
- CÓMO REPRODUCIRLO: `python -I v04b_pasada2_caso79.py`; Láscar 2026-03-15 07:45 UTC.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 3 (es también la razón por la que «cambia sólo donde el foco sale dos veces» está refutado; para MOD-D
  implica que el brazo sin duplicados puede mover magnitudes en pasadas 25-50° sin ningún duplicado en el cráter).

### VBT-03. La regla de filas de borde (B) mata una alerta protegida de 5,18 MW (Chillán 141) porque quita las dos copias del foco
- SCRIPT:SALIDA: `03_ablacion_salida.txt` (mi re-corrida idéntica): «B_filas_borde publica 10 | pierde 1 [141]»;
  `04_casos_salida.txt` caso 141: los dos nativos más calientes (barrido 18 det 8, 272,7 K; barrido 19 det 1, 270,9 K)
  llevan «x» en la columna B.
- QUÉ PASA: a z = 50,5° el foco está en el detector 8 de un barrido y en el detector 1 del siguiente; B conserva un
  detector sólo si su centro está a menos de medio paso de barrido del centro de su barrido, así que borra los dos y
  deja un hueco justo sobre el cráter (`v02` (c): B abre +4,8 % de huecos reales en z>=50 que no cierran con la huella
  ×1,5).
- CÓMO SE VE EN EL DASHBOARD: Chillán sin alerta MODIS la noche del 2026-10-01 08:35 UTC, con MIROVA en 5,18 MW.
- CÓMO REPRODUCIRLO: `python -I rerun_03_ablacion.py`; Nevados de Chillán 2026-10-01 08:35 UTC.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 5 si B se adoptara (pierde una protegida); 1 como está (el auditor lo mide y lo descarta). Lo anoto
  porque es la prueba de que un método «sin duplicados» mal elegido calla focos reales, y debe quedar escrito donde
  MOD-D elija el método.

### VBT-04. A deja 8,4 % del suelo de ROI1 bajo 2 barridos distintos en z>=50: el brazo no es «sin duplicados» sino «sin duplicados de centro cubierto»
- SCRIPT:SALIDA: `v02_huella_y_duplicados_salida.txt` (b): A_ant z>=50 «2+ barridos: 0,0841» contra 0,6590 con todos;
  `02b_rendijas_salida.txt` (A z>=50, 2+ con huella 0,8x: 0,0389).
- QUÉ PASA: A quita el píxel cuyo centro cae dentro del tramo de centros del barrido anterior (`comun.py:199-200`);
  los traslapes parciales (centro fuera, mitad de la huella dentro) quedan. Físicamente es el 87 % del suelo
  duplicado, y es lo que hace que A no abra huecos: quitar también los parciales (A_huella_entera_ant es lo opuesto,
  más conservador aún) abriría rendijas más anchas. No es un defecto: es el nombre.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python -I v02_huella_y_duplicados.py`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 1.

## 5. SEGUIMIENTOS (fuera de mi eje, sin perseguir)

- S-1. **El umbral de cumbre del oráculo depende de σ de toda la grilla de 51 km** (`mirova_v750_r2.py:88-90`, l.
  303-308 del .m según el propio oráculo). Para el port de MODIS eso significa que cualquier cambio en el borde de la
  grilla (duplicados, nubes, el regrid de D17) mueve la detección en el cráter. Es propiedad del código de MIROVA que
  se portó, no un bug del port, pero conviene tenerlo presente al leer A/B de remuestreo (D17, D28). CONFIRMADO en el
  caso 79; alcance general SOSPECHA.
- S-2. El estrato «cráter con 2+ huellas» del auditor se arma con la misma huella nominal con que se mide la cobertura;
  «A quita el píxel del cráter» (`02_cobertura.json` → `quita_det_crater`) es un estrato equivalente que no depende de
  la huella (en z>=50: 91 de 102 coinciden). Si MOD-D estratifica, prefiero el segundo. SOSPECHA de utilidad, medido
  el solapamiento.
- S-3. `tail` del shell de este entorno no acepta `-1` con dos archivos; sin consecuencia.

## 6. VERIFICADO LIMPIO

- Reproducción bit a bit de las cinco salidas del auditor (01, 02, 02b, 03, 04) y de los dos json (02_cobertura,
  03_ablacion) con mis copias `rerun_*.py` (misma `comun.py`, misma máquina Windows): diffs vacíos. Vara: la salida
  del auditor y el `resultados_MODIS_*.json` del runner Linux.
- Árbol del instrumento = commit 0e18e1053 (sha256 LF) para `mirova_port.py`, `probe_portes.py`,
  `mirova_v750_r2.py`, `process_modis.py`, `banco_paridad.py`, `index.html`. Vara: `git show 0e18e1053:<ruta>`.
- Comparador `igual()` ve una celda corrida, 2e-9 MW y una fila corrida (v01 (3)). Vara: controles positivos míos.
- Tres variantes del lote reproducidas 403/403 (fisica, fisica_b21, fisica_geo5km). Vara: json del runner.
- Asignación barrido/detector con la línea del gránulo, insensible al inicio del recorte; `linea + 1` cambia la máscara
  en 156/156 oblicuas y 0/55 en el nadir (v03). Vara: control positivo y nulo.
- Huella nominal creciente con el cenit (1,00 → 1,71 km a lo largo; 1,00 → 3,32 km a lo ancho), paso de barrido 10,06
  km, salto negativo de −5,3 km entre barridos en z>=50 (v02 (a), v03 (c)). Vara: la geolocalización MxD03 del npz.
- «Publica» = `banco_paridad.correr_node` sobre `record_port` (03_ablacion.py:65-71; 07_leer_lote.py:99-108). Vara:
  la definición del encargo.

## 7. SIN DATO

- Qué método exacto de bow tie usa MIROVA (Coppola 2010 o Liu 2008, D28): no está en el repo; no se puede decir si A
  es el método de MIROVA. Las conclusiones valen para A como método propio.
- Signo del efecto de quitar duplicados sobre la magnitud de las protegidas: n = 3 casos duplicados (65, 141, 147), 1
  cambia de signo con la copia, 2 bajan con ambas. Sin poder para generalizar; el auditor ya lo declaró SIN DATO.
- Efecto del brazo A sobre la producción K (`process_modis.py`): no medido, el experimento es sobre el port.
- Las 10 pasadas no evaluables.

## 8. FUERA DE ALCANCE

- VIIRS (bow tie distinto, con borrado a bordo), el regrid de D17, el PSF del sensor, la elección del brazo para MOD-D
  (la decide quien orquesta), cualquier arreglo.

---
Hora del servidor al cerrar el informe: Date: Sat, 24 Oct 2026 19:48:08 GMT. Llamadas a la API de GitHub en la sesión: 3 (sólo hora). Escrito en CARPETA: 1.5M.
