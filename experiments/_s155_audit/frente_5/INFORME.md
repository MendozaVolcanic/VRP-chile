# S155 auditoria, frente 5: la magnitud de Nevados de Chillan en erupcion, pasada por pasada

Worktree `D:\vrp-trabajo\worktrees\s155-audit-f5` (detached en `cb90031a`, origin/main del 2026-10-19). Nada del
repositorio fue modificado; todo lo de esta carpeta es medicion. Sin L1B (no se bajo nada ni se autentico contra
Earthdata). Hora del servidor de GitHub al bajar la referencia: 2026-10-19 10:43:30 GMT.

## 0. Que se midio, contra que, y con que instrumento

**Ventana**: 2026-09-28 a 2026-10-19 (la primera alerta de MIROVA de 1 MW o mas en Chillan es 2026-09-28 04:42;
`pareo_pasadas_salida.txt`). **Referencia**: consolidado y OCR remotos de Mirova-v1, bajados a
`D:\vrp-trabajo\temporales\frente_5\` (sha256[:16] consolidado `7cad3675e4e1ff86`, OCR `0741c3d71daf541a`); el
consolidado pisa al OCR, igual que `experiments/_s154_chillan/razon_por_cenit.py`. **Pareo**: misma hora al minuto y
mismo grupo de sensor. **Magnitud publicada**: nucleo F5' en VIIRS 375 y `primary_cluster.vrp_mw` en MODIS y VIIRS 750
(`frontend/index.html:1181` y `:1306`, leido).

**Denominadores** (A90): 229 records nuestros en la ventana, 0 claves duplicadas; 125 filas ALERTA de MIROVA, de las
cuales **105 se parean** y **20 no** (las 20 son diurnas, 12:45 a 20:50 UTC, y el perfil no procesa de dia:
`ENABLE_DAYTIME_MODIS/VIIRS = False`, `flags_mirova_equivalent.txt`). De las 105, **85 son protegidas** (MIROVA de 1 MW o
mas): **83 con cumulo publicado** (37 VIIRS 375, 35 VIIRS 750, 11 MODIS) y **2 FN** (MODIS).

**Regimen**: los 105 pares son de codigo K (campo `regimen.codigo_sha`; los nueve sha presentes descienden del merge
de #850, `34cea39e4`, comprobado con `git merge-base --is-ancestor`). Quedan **3 records C0** en la ventana y **ninguno
se parea** (F5-08). La separacion C0 contra K que pedia el encargo es **SIN DATO** para esta erupcion.

**Calidad de la referencia (A119)**: la ventana pisa dos hitos del OCR (2026-10-09 Suomi NPP, 2026-10-10 estrato
`ALERTA_SIN_GEOMETRIA_OCR`). 10 de los 83 pares usan ese estrato (VRP propio de la pasada, sin distancia). Sin ellos las
medianas por cenit no cambian de forma (`calidad_ref_salida.txt`).

**Controles del instrumento** (comunes a todas las mediciones):
- *Control positivo*: la razon publicado/MIROVA reproduce las 10 filas del 2026-10-18 de
  `experiments/_s154_chillan/razon_por_cenit_salida_20261018.txt` (0,24 / 0,46 / 0,41 / 0,64 / 0,67 / 0,72 / 0,72 /
  0,35 / 0,12 / 0,49), `pareo_pasadas_salida.txt`.
- *Reconstruccion del VRP por pixel*: para cada pixel persistido despejo el fondo implicito
  `L(BT) - VRP/(A_nadir * k)` con la lambda, el k y el area de cada procesador; coincide con `L(t_bg_k)` del anillo con
  desviacion relativa maxima de 3e-3 en todas las pasadas con pixeles (columna `dev`). O sea: reproduzco la formula del
  codigo, el area persistida es la nadir fija y Chillan no usa nucleo local de fondo (no tiene `local_kernel_bg` en
  `volcanoes.yaml:245-270`). Si mi formula estuviera mal, `dev` seria grande.
- *Identidad del pareo*: en 43 pares el OCR trae el cenit que MIROVA lee en su imagen; la diferencia con el nuestro es
  de 1,02 grados como maximo, 0 pares sobre 1,5 (`control_cenit_ocr_salida.txt`). Un pareo con otro satelite a la
  misma hora daria decenas de grados.

**Definiciones** (todas razones contra el VRP de MIROVA de la misma pasada; `estratos.py`):
`R pub` lo publicado; `R cumulo sin modo 1 px` el cumulo primario sumado (miembros reconstruidos por centroide, n <= 3);
`R todo alertado <= 5 km` todos los pixeles alertados a 5 km o menos del centro (en los protegidos es toda la escena salvo
2 pasadas VIIRS 375 con 6,6 % o menos de su VRP fuera de 5 km; `comprobaciones_informe_salida.txt`); `R fondo -20 K` lo mismo con el fondo del anillo 20 K mas frio (sensibilidad
ilustrativa, NO medicion); `R fondo 0` con fondo cero (cota superior absoluta de lo que cualquier fondo puede
recuperar); `f req` el factor que haria falta para que la pasada quede como la mediana de las de cenit < 30 del mismo
sensor; `fs`, `fa` factores de huella del MODELO geometrico (solo eje de barrido / area completa; Tierra esferica,
H = 829 km VIIRS y 705 km MODIS, zonas de agregacion VIIRS a 31,589 y 44,680 grados de barrido). El modelo da 1,63 x 1,66
km al borde para la banda M (ATBD: 1,60 x 1,58), control grueso; es modelo, no medicion.

## 1. Hallazgos, de mas grave a menos

### F5-01 El tablero publica un cumulo parcial en VIIRS 750 y MODIS: descarta cumulos vecinos del crater y aplica el "modo de un pixel" en plena erupcion
- **ARCHIVO:LINEA**: `pipeline/clustering.py:119-160` (estrategia `vent_anchored`: gana el cumulo con centroide mas
  cercano al crater, el VRP solo desempata); `pipeline/single_pixel_mode.py:157-183` con
  `SUB_MW_REGIME_THRESHOLD_MW = 5.0` y `SINGLE_PIXEL_MAX_CLUSTER_PIXELS = 3` (leidos de `pipeline.profile`); llamadas en
  `pipeline/process_viirs_mod.py:1102-1131` y `pipeline/process_modis.py:1197`. SCRIPT: `estratos_salida.txt`,
  `seleccion_detalle_salida.txt`.
- **QUE PASA**: en la erupcion la zona caliente del crater sale como 2 o 3 grupos de pixeles separados por menos de un
  pixel en el terreno. MIROVA suma todos los pixeles alertados de la pasada; nosotros publicamos solo el grupo cuyo
  centro esta mas cerca del crater, aunque el otro tenga mas energia, y si ese grupo suma menos de 5 MW con 3 pixeles o
  menos, publicamos solo su pixel mas caliente. El modo de un pixel se diseno para el regimen de 0,2 a 0,45 MW
  (docstring de `single_pixel_mode.py`), pero su umbral de 5 MW se evalua sobre NUESTRO cumulo, que en erupcion queda
  bajo 5 MW justamente porque ya esta subestimado: los dos recortes se encadenan.
- **Tamano**: en VIIRS 750 afecta 12 de 35 pasadas protegidas (9 por modo de un pixel, 8 por cumulo vecino descartado;
  se solapan); la mediana de `todo alertado / publicado` es 1,00 bajo 45 grados, **1,46** entre 45 y 60 y **1,92** sobre
  60. En MODIS, 4 de 11, mediana 1,40 a 1,42 sobre 30 grados. En VIIRS 375, 3 de 37 y mediana 1,00 a 1,05: el nucleo F5'
  rehace la suma desde todos los pixeles a 5 km del centroide (`pipeline/f5_core.py:61-104`), asi que VIIRS 375 queda
  practicamente inmune.
- **La pasada sospechosa de las 06:48 (VIIRS 750, 67,6 grados)**: publicado 2,84 MW = el pixel pico de un cumulo de 2
  (suma 4,39); hay 4 pixeles alertados mas, todos a menos de 2 km del crater, en otro cumulo; todo lo alertado suma 6,84.
  Razon 0,12 -> 0,19 (sin modo de un pixel) -> 0,30 (todo lo alertado). **La sospecha se confirma a medias**: la
  seleccion explica un factor 2,4 de los 8 del deficit; queda 0,30 contra 0,82 de nadir (f req 2,74), que es angular
  (F5-03, F5-04). Y la propia seleccion esta ligada al angulo (F5-02).
- **Peor caso**: 2026-10-10 06:30 VIIRS 750 (50,5 grados): publicado 4,33 MW, alertado 25,89 MW, MIROVA 32,0 MW (el
  maximo de MIROVA del mes). El pixel mas caliente de la escena (320,4 K, 16,2 MW, a 0,93 km del centro) queda fuera del
  cumulo publicado porque el otro grupo tiene el centroide a 0,28 km. Es fila `ALERTA_SIN_GEOMETRIA_OCR` (estrato aparte
  de A119), pero el VRP es de su pasada. Casos del consolidado: 2026-10-18 05:06 V750 8,10 publicado contra 15,06
  alertado (MIROVA 19,63); 2026-10-15 07:35 MODIS 3,12 contra 7,40 (MIROVA 15,27); 2026-10-16 06:42 V750 2,01 contra 4,43
  (MIROVA 14,02).
- **CÓMO SE VE EN EL DASHBOARD**: en esas pasadas la curva de VIIRS 750 y MODIS aparece 1,5 a 6 veces mas baja que lo que
  el propio pipeline detecto, y en una misma pasada VIIRS 750 queda muy por debajo de VIIRS 375 (10-10 06:30: 4,33 contra
  11,82). En el pico eruptivo la curva se ve mas tranquila de lo que es.
- **REPRODUCIR**: `python experiments/_s155_audit/frente_5/pareo_pasadas.py`, luego `estratos.py` y
  `seleccion_detalle.py`; pasadas 2026-10-10 06:30 y 2026-10-18 06:48 VIIRS_NOAA21_750 / VIIRS_SNPP_750.
- **CONFIANZA**: CONFIRMADO (codigo leido; miembros reconstruidos con control: la suma de los miembros da `pc_sum` en
  los 19 casos con membresia (`comprobaciones_informe_salida.txt`)).
- **GRAVEDAD**: 4. En erupcion tuerce la magnitud que el operador lee en dos de los tres sensores, en el sentido de
  "menos actividad", y mas cuanto mas fuerte el evento (es cuando mas pixeles hay para fragmentarse).

### F5-02 La fragmentacion en cumulos es de la topologia del arreglo, no del terreno: los grupos descartados estan pegados al publicado
- **ARCHIVO:LINEA**: `pipeline/clustering.py:95` (`ndi_label` sobre `hot_mask_2d`: conexidad 8 en filas y columnas del
  granulo, no en el suelo). SCRIPT: `costura.py` -> `costura_salida.txt`.
- **QUE PASA**: lejos del nadir VIIRS borra filas del borde de cada barrido (bow-tie) y los barridos vecinos se
  solapan en el suelo. Dos pixeles vecinos en el terreno pueden quedar en filas no contiguas del arreglo y salir como
  dos cumulos. En las 8 pasadas con membresia reconstruida y cumulo descartado de VIIRS 750, la menor distancia en el
  suelo entre un pixel publicado y uno descartado es **0,46 a 0,87 km = 0,62 a 1,17 pasos de traza** (0,742 km) y menor
  que la huella de barrido del modelo (0,55 a 0,85); cuando el publicado tiene 2 o 3 pixeles, los
  de DENTRO estan mas separados entre si (1,07 a 2,07 km). En VIIRS 375, 2026-10-17 04:42 (68 grados) trae dos pixeles alertados a **40 m** uno de otro en
  cumulos distintos: el mismo punto del suelo visto por dos barridos. MIROVA remuestrea a grilla antes de agregar, asi
  que no tiene este efecto.
- **Por que importa para la atribucion**: convierte parte de la "seleccion" (F5-01) en un mecanismo que crece con el
  angulo. La seleccion de V750 aparece sobre 45 grados (mediana 1,46 y 1,92) y su mediana es 1,00 bajo 45: consistente.
- **CÓMO SE VE EN EL DASHBOARD**: invisible como tal; se ve como la caida de F5-01.
- **REPRODUCIR**: `python experiments/_s155_audit/frente_5/costura.py`.
- **CONFIANZA**: SOSPECHA fuerte. Las distancias son medidas; que la separacion sea una fila borrada o una costura de
  barrido solo se prueba con el L1B (ver seccion 4, medicion M1). En MODIS (2,2 km = 1 huella de barrido) no se puede
  distinguir de un pixel no alertado entremedio: sin conclusion.
- **GRAVEDAD**: 3 (es el mecanismo de F5-01 en las pasadas oblicuas; sumado a F5-01 es 4).

### F5-03 En VIIRS 375 el fondo NO puede explicar la caida con el angulo; el area (remuestreo) si podria
- **SCRIPT**: `estratos_salida.txt` (bloque VIIRS375) y la columna `frac fondo pico` de la tabla.
- **QUE PASA (fisica)**: en la erupcion el pixel de 375 m del crater esta muy caliente (BT maxima por pasada 281,5 a
  356,0 K en los protegidos, `comprobaciones_informe_salida.txt`) y la radiancia del fondo es el **9 %** de la suya en
  la mediana (minimo 4 %). Restar
  mas o menos fondo mueve poco: con **fondo cero** (cota imposible de superar por cualquier eleccion de fondo, incluida
  D25) las medianas por cenit quedan **0,89 / 0,68 / 0,68 / 0,47** (0-30 / 30-45 / 45-60 / 60+ grados) y la caida
  persiste (Spearman cenit -0,53, n = 37). El contraste nadir contra borde pasa de 0,75/0,32 = 2,34 a 0,89/0,47 = 1,89:
  aun en el caso extremo el fondo explica a lo mas un cuarto del contraste en escala logaritmica. Con area completa del
  modelo, `R todo alertado * fa` queda **plano**: 0,90 / 0,91 / 1,02 / 0,90 (Spearman +0,08); con solo eje de barrido no
  aplana (0,85 a 0,47). El factor requerido (1,00 / 1,31 / 1,26 / 2,32) cae entre `fs` y `fa`.
- **Lectura**: para VIIRS 375 en erupcion **D25 cae como mecanismo principal de la curva** (cota, no estimacion) y el
  candidato que queda en pie es la falta de remuestreo con conservacion de energia (area nadir fija sin grilla, D17).
  Ademas queda un deficit casi uniforme de ~0,9 que no depende del angulo.
- **CÓMO SE VE EN EL DASHBOARD**: VIIRS 375 cae de ~0,75 de MIROVA en pasadas cenitales a ~0,32 en las de borde; la
  serie oscila segun la geometria de la pasada y no segun el volcan.
- **REPRODUCIR**: `python experiments/_s155_audit/frente_5/estratos.py`.
- **CONFIANZA**: CONFIRMADO que el fondo no alcanza (es una cota sobre BT persistidas). SOSPECHA que el area sea la
  causa: `fa` es un modelo, y la verificacion 1.19 dejo dicho que la ley de area del ATBD no esta medida punto a punto.
- **GRAVEDAD**: 4 como insumo: decide que pre-registrar en 1.29. Para el pre-registro de D25 sobre K: en VIIRS 375
  de Chillan D25 puede subir la magnitud a lo mas x1,18 (nadir) a x1,49 (borde) en la mediana; un resultado de D25 que
  "aplane la curva" de VIIRS 375 seria imposible con estos pixeles y deberia leerse como error del instrumento.

### F5-04 VIIRS 750 tiene una caida angular EXTRA respecto de VIIRS 375 en la misma pasada, del tamano de un cambio de fondo moderado
- **SCRIPT**: `misma_pasada.py` -> `misma_pasada_salida.txt` (n = 34 pasadas con ambos productos protegidos).
- **QUE PASA (fisica)**: en la misma pasada (mismo satelite, hora y cenit) el pixel de 750 m diluye la lava en cuatro
  veces mas superficie, su BT queda cerca del fondo (maxima por pasada 268,5 a 326,9 K) y el fondo pesa el **44 %** de su radiancia en la
  mediana, y mas cuanto mas oblicua la pasada (Spearman cenit contra `frac_bg` +0,55). Q = R(750)/R(375) por pasada vale
  **1,06** en nadir (control: si el pareo estuviera roto no daria ~1) y cae a 0,95 / 0,83 / **0,62** (Spearman -0,57). Con
  fondo 20 K mas frio, Q se invierte y sube (1,21 a 1,67), y con fondo cero mas (1,27 a 2,10): un cambio de fondo de
  pocos kelvin bastaria para aplanar Q.
- **Lectura**: en VIIRS 750 hay dos mecanismos apilados: el comun con VIIRS 375 (geometrico, F5-03) y uno propio de la
  banda M que crece con el angulo. Para ese segundo quedan en pie **dos** candidatos que el record no separa: (i) el
  fondo (D25 sobre M13), cuyo tamano encaja; (ii) una ley de area distinta para M13: segun el verificador de la tarea
  1.19 (`experiments/_s151_angular_119/verificador/VERIFICADOR.md:41`, rama del loop, leido pero NO verificado por mi),
  la Tabla 2.2-1 del ATBD dice que M13 "not along-scan aggregated on-board", y queda abierto si la agregacion se hace en
  tierra. Con fondo cero, `R` de VIIRS 750 queda plano (1,10 / 0,96 / 1,19 / 1,03; Spearman -0,03): el fondo **no se
  puede descartar** en VIIRS 750, al reves que en 375.
- **CÓMO SE VE EN EL DASHBOARD**: en pasadas oblicuas VIIRS 750 queda por debajo de VIIRS 375 aun despues de corregir
  la seleccion.
- **CONFIANZA**: CONFIRMADO el Q y su tendencia; SOSPECHA la atribucion entre fondo y ley de area de M13.
- **GRAVEDAD**: 3.

### F5-05 Dos alertas protegidas de MODIS a 58 grados no se detectan
- **SCRIPT**: `fn_modis_diag.py` -> `fn_modis_diag_salida.txt`.
- **QUE PASA**: 2026-10-12 07:20 MODIS Aqua (58,2 grados, MIROVA 2,18 MW) y 2026-10-15 01:05 MODIS Terra (57,6 grados,
  1,72 MW): 0 pixeles en primer pase, 0 recapturas; el maximo de BT del ROI esta a 24 y 29 km (valle), o sea el detector
  miro y la cumbre no sobresalio. A 58 grados el pixel MODIS se estira ~3,2 veces en barrido segun el modelo (`fs`, `pareo_pasadas_salida.txt`), la senal del
  crater se diluye y ya no supera el contexto. Es la cara de deteccion del mismo efecto angular. Son 2 de 13 protegidas
  MODIS, las dos sobre 57 grados.
- **CÓMO SE VE EN EL DASHBOARD**: nada en esa pasada MODIS. Por noche (A94) no se pierde la alerta: las dos noches tienen
  pasadas VIIRS 375 publicadas (10-12 05:18 2,88 MW; 10-15 05:00 10,36 MW, `pareo_pasadas_salida.txt`).
- **CONFIANZA**: CONFIRMADO (record leido). Por que no disparo cada test: SIN DATO sin el L1B.
- **GRAVEDAD**: 2.

### F5-06 Tope D9 de 5 MW: inactivo en las alertas de esta erupcion, pero con las condiciones cumplidas en 42 records
- **ARCHIVO:LINEA**: `pipeline/process_viirs_mod.py:1009-1016` y `:1110-1112`; `pipeline/process_viirs.py:1440-1447`.
  SCRIPT: `tope_d9_latente.py` -> `tope_d9_latente_salida.txt`.
- **QUE PASA**: el tope recorta a 5 MW cuando el disparo es solo contextual y el anillo esta bajo 270 K. En la ventana,
  de 110 records con cumulo, **42** cumplen las dos condiciones y ninguno de esos lleva hoy un cumulo sobre 5 MW, salvo el
  C0 de F5-08. En una noche fria con un evento mas fuerte, VIIRS 750 y MODIS publicarian 5,0 MW contra 10 a 30 de MIROVA.
  VIIRS 375 escaparia porque F5' suma los VRP por pixel, que no pasan por el tope. Ningun par protegido fue topado
  (`d9_capped` falso en los 105).
- **CÓMO SE VE EN EL DASHBOARD**: hoy, nada. Latente: una meseta en 5,0 MW en V750 y MODIS.
- **CONFIANZA**: CONFIRMADO (codigo y conteo). Latente, no activo.
- **GRAVEDAD**: 2.

### F5-07 MODIS con banda 22 primaria convierte la BT a radiancia con la longitud de onda de la banda 21
- **ARCHIVO:LINEA**: `pipeline/process_modis.py:552-554` (BT de B22 donde no satura) contra `:1034` y `:1039`
  (`BAND21_LAMBDA`). SCRIPT: `lambda_modis.py` -> `lambda_modis_salida.txt`.
- **QUE PASA**: el exceso de radiancia sale ~5 % mas bajo (razon 0,943 a 0,951, mediana 0,948, n = 20 pixeles MODIS
  pareados) que convertido a 3,959 um. El k = 18,9 se calibro en S14 con banda 21 primaria; bajo K la coherencia banda,
  lambda y k no esta revisada.
- **CÓMO SE VE EN EL DASHBOARD**: MODIS ~5 % mas bajo; imperceptible frente al resto.
- **CONFIANZA**: CONFIRMADO el desajuste y su tamano; SOSPECHA que deba corregirse (depende del k).
- **GRAVEDAD**: 1.

### F5-08 Tres records C0 siguen dentro de la ventana reprocesada con K
- **SCRIPT**: `c0_restantes.py` -> `c0_restantes_salida.txt`.
- **QUE PASA**: MODIS Terra NRT 2026-09-28 01:25 y 01:30 y 2026-10-10 01:05 no tienen `regimen` (procesados el 09-28 y
  10-10). Los tres son `far`; el de 09-28 01:30 trae el cumulo topado en 5,0 MW (D9) a 1,19 km del crater y MIROVA dijo
  RUTINA. Mezclan regimenes en la serie (A104).
- **CÓMO SE VE EN EL DASHBOARD**: invisible por defecto (`mirovaEqVrp` devuelve 0 para lo que no es `summit`,
  `frontend/index.html:1175`); aparece con "incluir lejanas".
- **CONFIANZA**: CONFIRMADO. Por que el reproceso no los reescribio: SIN DATO.
- **GRAVEDAD**: 1.

### F5-09 Duplicados de bow-tie en el borde podrian inflar la suma de escena
- **SCRIPT**: `seleccion_detalle_salida.txt` (2026-10-17 04:42 VIIRS 375: dos pixeles alertados a 0,04 km).
- **QUE PASA**: si el mismo punto del suelo entra dos veces, cualquier suma de "todo lo alertado" lo cuenta doble en las
  pasadas de borde. Es el sentido contrario al deficit; afecta a las columnas `R todo alertado` de esta auditoria y a
  cualquier arreglo que sume escena.
- **CONFIANZA**: SOSPECHA (un caso; confirmar con filas del L1B).
- **GRAVEDAD**: 1.

## 2. Hipotesis por sensor: que queda en pie y que cae

| mecanismo | VIIRS 375 (n = 37) | VIIRS 750 (n = 35) | MODIS (n = 11, mas 2 FN) |
|---|---|---|---|
| (a) seleccion de cumulo | **CAE** (mediana x1,00 a x1,05; F5' la neutraliza). Confianza alta | **EN PIE y medida**: x1,46 (45-60) y x1,92 (60+); ligada al angulo por F5-02. Alta | **EN PIE**: x1,40 sobre 30 grados. Media (n chico) |
| (b) fondo (anillo contra vecinos, D25) | **CAE como causa de la curva** (cota de fondo cero deja la caida: 0,89 a 0,47). Alta | **EN PIE**: con fondo cero queda plano; Q del mismo paso pide un efecto propio de M del tamano de pocos K. Media | **EN PIE** (fondo 37 a 87 % de la radiancia del pico). D25 no existe para MODIS (`process_modis.py`: 0 usos de `VRP_BG_NEIGHBOR`). Baja |
| (c) recortes (D9, lista de 100) | **CAE** (0 topados; maximo 8 pixeles alertados por pasada) | **CAE** hoy; D9 latente (F5-06) | **CAE** hoy; D9 latente |
| (d) saturacion | **CAE** a nivel record (BT max 355,96 K contra corte 361,27) y por L1B en la tarea 1.18 | **CAE** (326,89 K contra 633,5) | **CAE** (299,74 K; B22 satura ~331 K) |
| (e) area nadir y angulo (sin remuestreo) | **EN PIE, principal candidato**: `fa` aplana (0,90 a 1,02). Media (modelo) | **EN PIE** junto con (b); ley de M13 sin resolver. Baja | **EN PIE**, no separable de (b). Baja |

## 3. Respuesta a la sospecha de la pasada de las 06:48

VIIRS 750 2026-10-18 06:48 (NOAA-21, 67,6 grados): las dos cosas. La seleccion (modo de un pixel y cumulo vecino
descartado) explica x2,4 (0,12 a 0,30); lo que queda (0,30 contra 0,82 de nadir) es angular, y de eso el fondo puede ser
todo o casi nada (fondo cero da 0,96). En la misma pasada VIIRS 375 publica 8,93 contra 25,79 (0,35) sin perdida por
seleccion: su deficit es angular y no es fondo.

## 4. Mediciones que faltan (cada una necesita el L1B; para quien orquesta)

- **M1, topologia (F5-02)**: en `VJ202MOD.A2026291.0648.021.2026291130237.nc` (+ VJ203MOD de la misma hora),
  `VJ202MOD.A2026291.0506.021.2026291103813.nc` y `VNP02MOD.A2026283.0630.002.2026283143201.nc`, ubicar en fila y columna
  los pixeles alertados (lat/lon en `granulos_l1b_salida.txt`) y ver si entre el cumulo publicado y el descartado hay
  filas con DN 65533 (Bowtie_Deleted, `FLAG_DNS` de `process_viirs_mod.py:68`) o una costura de barrido (fila multiplo de
  16). Si la hay, F5-02 pasa a CONFIRMADO. Mismo ejercicio para VIIRS 375 2026-10-17 04:42 (`VJ102IMG.A2026290.0442...`)
  por el duplicado de 40 m (F5-09).
- **M2, fondo real (D25)**: en las mismas pasadas, mas una nadir (`VNP02MOD.A2026291.0542.002.2026291121847.nc`), leer M13
  e I04 de los 8 vecinos NO alertados de cada pixel alertado y recalcular con el fondo de vecinos. Para VIIRS 375 el
  resultado tiene que caer dentro de la cota de F5-03 (x1,18 a x1,49); si no, el instrumento esta mal.
- **M3, area real**: la huella geolocalizada de esos pixeles (VNP03/VJ103: espaciado lat/lon de vecinos, o
  `scan_geometry.pixel_areas_from_geolocation`) para reemplazar el modelo `fs`/`fa`.
- **M4, ley de M13**: leer en el ATBD de SDR de VIIRS si la agregacion de las bandas de doble ganancia se hace en tierra.
  Decide si el candidato (ii) de F5-04 existe.
- **M5, FN de MODIS**: `MYD021KM.A2026285.0720.061.2026286023420.hdf` y `MOD021KM.A2026288.0105.061.2026288131238.hdf`:
  BT de B22 y dNTI del pixel del crater contra sus umbrales del primer pase.

## 5. VERIFICADO LIMPIO (no hace falta volver a mirarlo para esta erupcion)

- **La formula del VRP persistido es la del codigo, con area nadir fija y fondo del anillo**: desviacion del fondo
  implicito <= 3e-3 en todas las pasadas (`python experiments/_s155_audit/frente_5/pareo_pasadas.py`, columna `dev`).
- **Ningun objeto lejano compite**: en 81 de los 83 protegidos todo pixel alertado esta a 5 km o menos; en los otros 2
  (VIIRS 375 2026-10-01 05:24 y 2026-10-05 05:06) lo de fuera es 6,6 % o menos del VRP de escena
  (`comprobaciones_informe_salida.txt`).
- **Sin truncamiento de lista**: maximo 8 pixeles alertados por pasada pareada, lejos de 100 (columna `n_anom`).
- **D9 no recorto ninguna pasada pareada** (`tope_d9_latente.py`; `d9_capped` falso en los 105).
- **Saturacion**: BT maxima por sensor bajo el techo de descarte (`estratos.py`, linea "BT maxima"); la tarea 1.18 la
  leyo en el L1B (0 saturados en 385 granulos, con verificador; texto en `tasks/LOOP_OBJETIVOS.md:317` de la rama del
  loop, leido, no re-ejecutado por mi).
- **Pareo**: cenit OCR contra nuestro <= 1,02 grados en 43 pares (`control_cenit_ocr.py`); 0 claves duplicadas.
- **Regimen**: todos los pares son K (`git merge-base --is-ancestor 34cea39e4 <sha>` para los 9 sha).
- **F5' en VIIRS 375 no pierde energia por seleccion** (3 de 37 afectadas, mediana x1,00 a x1,05).
- **Las 20 alertas sin par son diurnas** (lista al pie de `pareo_pasadas_salida.txt`) y el perfil no procesa de dia.
- **Flags** leidos de `pipeline.profile`, no del YAML (`flags_mirova_equivalent.txt`).

## 6. Tabla pasada por pasada

105 pares de la ventana (protegidos y no protegidos); `f req` y `R fondo -20 K` solo para protegidos con cumulo. Generada
por `tabla_md.py` (ningun numero transcrito a mano). Las 20 alertas diurnas sin par estan al pie de
`pareo_pasadas_salida.txt`.

| pasada UTC | grupo | satelite | cenit | MIROVA MW (fuente) | reg | publicado MW | R pub | R cumulo sin modo 1 px | R todo alertado <=5 km | R fondo -20 K | R fondo 0 | frac fondo pico | f req | fs | fa | modo 1 px | cumulos |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-09-28 04:42 | VIIRS375 | NOAA21 | 65.1 | 2.58 (cons) | K | 0.49 | 0.19 | 0.26 | 0.26 | 0.35 | 0.39 | 0.26 | 2.88 | 1.54 | 3.00 | si | 1 |
| 2026-09-28 04:42 | VIIRS750 | NOAA21 | 65.1 | 0.23 (cons) | K | FN (sin cumulo) | - | - | 0.00 | - | 0.00 | - | - | 1.54 | 3.00 | - | 0 |
| 2026-09-28 05:18 | VIIRS375 | SNPP | 49.2 | 0.05 (ocr) | K | 0.07 | 1.43 | 1.43 | 1.43 | - | 4.98 | 0.71 | - | 1.46 | 2.08 | si | 1 |
| 2026-09-28 06:18 | VIIRS375 | NOAA21 | 51.4 | 0.60 (cons) | K | 0.26 | 0.44 | 0.44 | 0.44 | - | 0.73 | 0.40 | - | 1.58 | 2.34 | si | 2 |
| 2026-09-29 05:00 | VIIRS375 | SNPP | 62.1 | 1.41 (ocr) | K | 0.21 | 0.15 | 0.15 | 0.15 | 0.28 | 0.34 | 0.57 | 5.09 | 1.30 | 2.36 | si | 1 |
| 2026-09-29 05:18 | VIIRS375 | NOAA20 | 42.6 | 5.73 (cons) | K | 3.17 | 0.55 | 0.55 | 0.55 | 0.61 | 0.64 | 0.08 | 1.35 | 1.17 | 1.52 | si | 1 |
| 2026-09-29 05:18 | VIIRS750 | NOAA20 | 42.6 | 5.48 (cons) | K | 2.11 | 0.39 | 0.39 | 0.39 | 0.65 | 0.79 | 0.51 | 2.13 | 1.18 | 1.53 | si | 1 |
| 2026-09-29 06:00 | VIIRS375 | NOAA21 | 31.2 | 3.92 (cons) | K | 2.31 | 0.59 | 0.59 | 0.59 | 0.67 | 0.72 | 0.11 | 1.26 | 1.34 | 1.53 | si | 1 |
| 2026-09-29 06:00 | VIIRS750 | NOAA21 | 31.1 | 2.52 (cons) | K | 0.72 | 0.28 | 0.28 | 0.28 | 1.41 | 2.09 | 0.77 | 2.88 | 1.34 | 1.53 | si | 1 |
| 2026-09-29 06:36 | VIIRS375 | SNPP | 55.7 | 2.11 (cons) | K | 2.68 | 1.27 | 0.62 | 1.27 | 1.62 | 1.79 | 0.17 | 0.59 | 0.95 | 1.51 | si | 2 |
| 2026-09-29 06:36 | VIIRS750 | SNPP | 55.8 | 2.03 (cons) | K | 0.33 | 0.16 | 0.16 | 0.33 | 1.71 | 2.43 | 0.86 | 2.46 | 0.95 | 1.51 | si | 2 |
| 2026-09-29 07:20 | MODIS | MODIS_AQUA | 58.4 | 0.13 (cons) | K | FN (sin cumulo) | - | - | 0.00 | - | 0.00 | - | - | 3.26 | 5.57 | - | 0 |
| 2026-10-01 01:45 | MODIS | MODIS_TERRA | 2.3 | 6.17 (cons) | K | 4.80 | 0.78 | 0.78 | 0.78 | 1.38 | 1.75 | 0.41 | 0.96 | 1.00 | 1.00 | si | 1 |
| 2026-10-01 04:42 | VIIRS375 | NOAA20 | 67.9 | 0.88 (cons) | K | 0.23 | 0.27 | 0.14 | 0.31 | - | 1.03 | 0.56 | - | 1.85 | 3.85 | si | 2 |
| 2026-10-01 04:42 | VIIRS750 | NOAA20 | 68.0 | 0.09 (cons) | K | 0.00 | 0.00 | 0.00 | 0.00 | - | 12.08 | 1.13 | - | 1.85 | 3.86 | si | 1 |
| 2026-10-01 05:24 | VIIRS375 | NOAA21 | 27.9 | 6.28 (ocr) | K | 3.25 | 0.52 | 0.52 | 0.52 | 0.58 | 0.60 | 0.09 | 1.44 | 1.26 | 1.40 | si | 2 |
| 2026-10-01 05:24 | VIIRS750 | NOAA21 | 27.9 | 9.00 (ocr) | K | 2.65 | 0.29 | 0.50 | 0.50 | 0.83 | 1.00 | 0.46 | 1.65 | 1.26 | 1.40 | si | 1 |
| 2026-10-01 06:00 | VIIRS375 | SNPP | 11.1 | 5.07 (ocr) | K | 8.37 | 1.65 | 1.65 | 1.65 | 1.79 | 1.86 | 0.07 | 0.45 | 1.04 | 1.05 | no | 1 |
| 2026-10-01 06:00 | VIIRS750 | SNPP | 11.1 | 10.00 (ocr) | K | 11.08 | 1.11 | 1.11 | 1.11 | 1.54 | 1.77 | 0.27 | 0.74 | 1.04 | 1.05 | no | 1 |
| 2026-10-01 06:18 | VIIRS375 | NOAA20 | 45.8 | 7.28 (cons) | K | 4.21 | 0.58 | 0.58 | 0.58 | 0.62 | 0.64 | 0.06 | 1.29 | 1.30 | 1.76 | si | 1 |
| 2026-10-01 06:18 | VIIRS750 | NOAA20 | 45.8 | 7.06 (cons) | K | 2.49 | 0.35 | 0.41 | 0.41 | 0.79 | 0.99 | 0.45 | 1.98 | 1.30 | 1.76 | si | 1 |
| 2026-10-01 08:35 | MODIS | MODIS_AQUA | 50.5 | 5.18 (cons) | K | 1.08 | 0.21 | 0.21 | 0.38 | 1.33 | 1.79 | 0.69 | 1.98 | 2.31 | 3.39 | si | 2 |
| 2026-10-03 06:24 | VIIRS375 | NOAA21 | 56.4 | 0.54 (cons) | K | 0.33 | 0.60 | 0.60 | 0.60 | - | 1.33 | 0.42 | - | 0.97 | 1.57 | si | 1 |
| 2026-10-04 05:06 | VIIRS375 | SNPP | 58.5 | 0.58 (ocr) | K | 0.19 | 0.32 | 0.32 | 0.32 | - | 0.63 | 0.49 | - | 1.08 | 1.81 | si | 1 |
| 2026-10-04 06:06 | VIIRS375 | NOAA21 | 39.0 | 2.54 (cons) | K | 1.90 | 0.75 | 0.75 | 0.75 | 0.80 | 0.82 | 0.09 | 1.00 | 1.07 | 1.32 | si | 1 |
| 2026-10-04 06:06 | VIIRS750 | NOAA21 | 39.0 | 2.30 (cons) | K | 1.81 | 0.79 | 0.79 | 0.79 | 1.27 | 1.51 | 0.48 | 1.04 | 1.07 | 1.32 | si | 1 |
| 2026-10-04 06:42 | VIIRS375 | SNPP | 60.0 | 0.86 (cons) | K | 0.49 | 0.57 | 0.57 | 0.57 | - | 0.95 | 0.36 | - | 1.16 | 2.01 | si | 1 |
| 2026-10-05 04:48 | VIIRS375 | SNPP | 68.3 | 0.04 (ocr) | K | 0.00 | 0.00 | 0.00 | 0.00 | - | 5.61 | 1.24 | - | 1.90 | 4.00 | si | 1 |
| 2026-10-05 05:06 | VIIRS375 | NOAA20 | 53.6 | 5.77 (cons) | K | 2.92 | 0.51 | 0.51 | 0.51 | 0.61 | 0.66 | 0.10 | 1.47 | 0.86 | 1.33 | si | 2 |
| 2026-10-05 05:06 | VIIRS750 | NOAA20 | 53.6 | 3.43 (cons) | K | 1.44 | 0.42 | 0.42 | 0.42 | 1.16 | 1.59 | 0.60 | 1.96 | 0.86 | 1.33 | si | 1 |
| 2026-10-05 05:48 | VIIRS375 | NOAA21 | 12.5 | 4.35 (cons) | K | 3.28 | 0.75 | 0.75 | 0.75 | 0.80 | 0.82 | 0.08 | 0.99 | 1.05 | 1.07 | si | 1 |
| 2026-10-05 05:48 | VIIRS750 | NOAA21 | 12.4 | 7.86 (cons) | K | 7.15 | 0.91 | 0.91 | 0.91 | 1.11 | 1.22 | 0.26 | 0.90 | 1.05 | 1.07 | no | 1 |
| 2026-10-05 06:24 | VIIRS375 | SNPP | 44.8 | 8.24 (ocr) | K | 4.47 | 0.54 | 0.54 | 0.54 | 0.59 | 0.61 | 0.07 | 1.37 | 1.26 | 1.68 | si | 1 |
| 2026-10-05 06:24 | VIIRS750 | SNPP | 44.8 | 7.00 (ocr) | K | 3.98 | 0.57 | 0.57 | 0.57 | 0.91 | 1.13 | 0.36 | 1.44 | 1.25 | 1.68 | si | 1 |
| 2026-10-05 06:48 | VIIRS375 | NOAA20 | 64.3 | 4.71 (cons) | K | 1.51 | 0.32 | 0.32 | 0.32 | 0.42 | 0.48 | 0.15 | 2.32 | 1.47 | 2.81 | si | 1 |
| 2026-10-05 06:48 | VIIRS750 | NOAA20 | 64.3 | 2.66 (cons) | K | 0.26 | 0.10 | 0.10 | 0.10 | 0.91 | 1.40 | 0.88 | 8.43 | 1.47 | 2.81 | si | 1 |
| 2026-10-05 07:50 | MODIS | MODIS_AQUA | 23.6 | 3.50 (cons) | K | 2.22 | 0.64 | 0.64 | 0.64 | 1.20 | 1.48 | 0.57 | 1.17 | 1.18 | 1.27 | si | 1 |
| 2026-10-08 05:48 | VIIRS375 | NOAA20 | 2.0 | 0.82 (cons) | K | 0.64 | 0.78 | 0.78 | 0.78 | - | 1.12 | 0.30 | - | 1.00 | 1.00 | si | 1 |
| 2026-10-09 05:12 | VIIRS375 | SNPP | 54.4 | 0.21 (ocr) | K | 0.16 | 0.74 | 0.74 | 0.74 | - | 1.50 | 0.51 | - | 0.89 | 1.39 | si | 1 |
| 2026-10-09 05:30 | VIIRS375 | NOAA20 | 27.7 | 0.50 (cons) | K | 0.29 | 0.57 | 0.57 | 0.57 | - | 0.93 | 0.39 | - | 1.26 | 1.40 | si | 1 |
| 2026-10-09 05:30 | VIIRS750 | NOAA20 | 27.7 | 0.35 (cons) | K | 0.40 | 1.13 | 1.13 | 1.13 | - | 5.42 | 0.79 | - | 1.26 | 1.40 | si | 1 |
| 2026-10-09 06:12 | VIIRS375 | NOAA21 | 45.7 | 1.22 (cons) | K | 0.81 | 0.66 | 0.66 | 0.66 | 0.85 | 0.93 | 0.22 | 1.13 | 1.29 | 1.75 | si | 1 |
| 2026-10-09 06:12 | VIIRS750 | NOAA21 | 45.8 | 0.82 (cons) | K | 0.85 | 1.04 | 1.04 | 1.04 | - | 2.82 | 0.63 | - | 1.29 | 1.75 | si | 1 |
| 2026-10-10 04:54 | VIIRS375 | SNPP | 65.5 | 5.72 (cons) | K | 0.76 | 0.13 | 0.16 | 0.16 | 0.26 | 0.32 | 0.28 | 4.72 | 1.58 | 3.10 | si | 1 |
| 2026-10-10 04:54 | VIIRS750 | SNPP | 65.5 | 2.48 (cons) | K | 0.24 | 0.10 | 0.10 | 0.10 | 0.66 | 0.95 | 0.90 | 8.38 | 1.58 | 3.11 | si | 1 |
| 2026-10-10 05:12 | VIIRS375 | NOAA20 | 48.6 | 8.75 (cons) | K | 2.58 | 0.30 | 0.30 | 0.30 | 0.32 | 0.33 | 0.11 | 2.52 | 1.42 | 2.01 | si | 1 |
| 2026-10-10 05:12 | VIIRS750 | NOAA20 | 48.6 | 6.42 (cons) | K | 1.75 | 0.27 | 0.27 | 0.27 | 0.69 | 0.94 | 0.57 | 3.01 | 1.42 | 2.01 | si | 1 |
| 2026-10-10 05:54 | VIIRS375 | NOAA21 | 22.4 | 7.55 (cons) | K | 5.56 | 0.74 | 0.74 | 0.74 | 0.84 | 0.89 | 0.10 | 1.01 | 1.16 | 1.24 | no | 1 |
| 2026-10-10 05:54 | VIIRS750 | NOAA21 | 22.4 | 13.13 (cons) | K | 10.48 | 0.80 | 0.80 | 0.80 | 1.05 | 1.19 | 0.21 | 1.03 | 1.16 | 1.24 | no | 1 |
| 2026-10-10 06:30 | VIIRS375 | SNPP | 50.5 | 12.17 (ocr) | K | 11.82 | 0.97 | 0.54 | 0.97 | 1.09 | 1.16 | 0.05 | 0.77 | 1.53 | 2.23 | no | 2 |
| 2026-10-10 06:30 | VIIRS750 | SNPP | 50.5 | 32.00 (ocr) | K | 4.33 | 0.14 | 0.14 | 0.81 | 0.99 | 1.09 | 0.12 | 1.01 | 1.53 | 2.23 | si | 2 |
| 2026-10-10 06:54 | VIIRS375 | NOAA20 | 67.5 | 13.78 (cons) | K | 7.87 | 0.57 | 0.31 | 0.60 | 0.71 | 0.76 | 0.08 | 1.25 | 1.80 | 3.72 | no | 2 |
| 2026-10-10 06:54 | VIIRS750 | NOAA20 | 67.6 | 15.26 (cons) | K | 2.51 | 0.16 | 0.19 | 0.32 | 0.81 | 1.06 | 0.44 | 2.60 | 1.80 | 3.72 | si | 2 |
| 2026-10-10 07:40 | MODIS | MODIS_AQUA | 35.1 | 3.95 (cons) | K | 0.54 | 0.14 | 0.14 | 0.14 | 1.00 | 1.55 | 0.86 | 5.44 | 1.46 | 1.74 | si | 1 |
| 2026-10-11 04:54 | VIIRS375 | NOAA20 | 61.8 | 0.30 (cons) | K | 0.33 | 1.09 | 1.09 | 1.09 | - | 1.75 | 0.37 | - | 1.27 | 2.30 | si | 1 |
| 2026-10-11 05:36 | VIIRS375 | NOAA21 | 8.6 | 1.38 (cons) | K | 1.22 | 0.89 | 0.89 | 0.89 | 1.33 | 1.52 | 0.24 | 0.84 | 1.02 | 1.03 | no | 1 |
| 2026-10-11 05:36 | VIIRS750 | NOAA21 | 8.6 | 1.03 (cons) | K | 0.87 | 0.84 | 1.62 | 1.62 | 3.52 | 4.42 | 0.62 | 0.51 | 1.02 | 1.03 | si | 1 |
| 2026-10-11 06:12 | VIIRS375 | SNPP | 29.8 | 0.42 (ocr) | K | 0.11 | 0.26 | 0.26 | 0.26 | - | 0.63 | 0.37 | - | 1.30 | 1.48 | si | 2 |
| 2026-10-12 05:18 | VIIRS375 | NOAA21 | 35.8 | 7.31 (cons) | K | 2.88 | 0.39 | 0.39 | 0.39 | 0.42 | 0.44 | 0.10 | 1.89 | 1.48 | 1.77 | si | 1 |
| 2026-10-12 05:18 | VIIRS750 | NOAA21 | 35.8 | 8.44 (cons) | K | 3.46 | 0.41 | 0.41 | 0.41 | 0.61 | 0.73 | 0.44 | 2.00 | 1.48 | 1.77 | si | 1 |
| 2026-10-12 05:54 | VIIRS375 | SNPP | 0.4 | 0.85 (cons) | K | 0.43 | 0.51 | 0.51 | 0.51 | - | 1.41 | 0.41 | - | 1.00 | 1.00 | si | 1 |
| 2026-10-12 05:54 | VIIRS750 | SNPP | 0.5 | 0.40 (cons) | K | FN (sin cumulo) | - | - | 0.00 | - | 0.00 | - | - | 1.00 | 1.00 | - | 0 |
| 2026-10-12 07:20 | MODIS | MODIS_AQUA | 58.2 | 2.18 (cons) | K | FN (sin cumulo) | - | - | 0.00 | - | 0.00 | - | - | 3.22 | 5.48 | - | 0 |
| 2026-10-14 05:36 | VIIRS375 | NOAA20 | 18.6 | 0.12 (cons) | K | 0.03 | 0.27 | 0.27 | 0.27 | - | 1.84 | 0.85 | - | 1.11 | 1.16 | si | 2 |
| 2026-10-14 06:18 | VIIRS375 | NOAA21 | 51.5 | 2.54 (cons) | K | 2.97 | 1.17 | 0.66 | 1.24 | 1.52 | 1.63 | 0.14 | 0.60 | 1.59 | 2.35 | no | 2 |
| 2026-10-14 06:18 | VIIRS750 | NOAA21 | 51.5 | 2.00 (cons) | K | 1.17 | 0.59 | 1.06 | 2.00 | 3.24 | 3.80 | 0.39 | 0.41 | 1.59 | 2.35 | si | 2 |
| 2026-10-15 01:05 | MODIS | MODIS_TERRA | 57.6 | 1.72 (cons) | K | FN (sin cumulo) | - | - | 0.00 | - | 0.00 | - | - | 3.13 | 5.25 | - | 0 |
| 2026-10-15 05:00 | VIIRS375 | SNPP | 62.4 | 22.13 (ocr) | K | 10.36 | 0.47 | 0.24 | 0.47 | 0.53 | 0.55 | 0.07 | 1.59 | 1.31 | 2.40 | no | 2 |
| 2026-10-15 05:00 | VIIRS750 | SNPP | 62.4 | 14.00 (ocr) | K | 1.88 | 0.13 | 0.15 | 0.36 | 0.88 | 1.16 | 0.55 | 2.30 | 1.31 | 2.40 | si | 2 |
| 2026-10-15 05:18 | VIIRS375 | NOAA20 | 42.7 | 13.74 (cons) | K | 5.85 | 0.43 | 0.43 | 0.43 | 0.49 | 0.52 | 0.07 | 1.75 | 1.18 | 1.53 | no | 1 |
| 2026-10-15 05:18 | VIIRS750 | NOAA20 | 42.7 | 14.02 (cons) | K | 5.18 | 0.37 | 0.37 | 0.37 | 0.48 | 0.54 | 0.32 | 2.22 | 1.18 | 1.53 | no | 1 |
| 2026-10-15 06:00 | VIIRS375 | NOAA21 | 31.3 | 14.67 (cons) | K | 9.45 | 0.64 | 0.64 | 0.64 | 0.71 | 0.75 | 0.07 | 1.16 | 1.34 | 1.54 | no | 2 |
| 2026-10-15 06:00 | VIIRS750 | NOAA21 | 31.3 | 30.10 (cons) | K | 20.42 | 0.68 | 0.68 | 0.68 | 0.74 | 0.77 | 0.12 | 1.21 | 1.34 | 1.54 | no | 1 |
| 2026-10-15 06:36 | VIIRS375 | SNPP | 55.5 | 19.07 (cons) | K | 11.40 | 0.60 | 0.60 | 0.60 | 0.66 | 0.68 | 0.05 | 1.25 | 0.93 | 1.49 | no | 1 |
| 2026-10-15 06:36 | VIIRS750 | SNPP | 55.5 | 15.15 (cons) | K | 8.51 | 0.56 | 0.56 | 0.56 | 0.97 | 1.18 | 0.27 | 1.46 | 0.94 | 1.49 | no | 1 |
| 2026-10-15 07:35 | MODIS | MODIS_AQUA | 44.3 | 15.27 (cons) | K | 3.12 | 0.20 | 0.24 | 0.48 | 0.99 | 1.27 | 0.51 | 1.54 | 1.87 | 2.50 | si | 2 |
| 2026-10-16 01:40 | MODIS | MODIS_TERRA | 3.2 | 12.39 (cons) | K | 9.25 | 0.75 | 0.75 | 0.75 | 1.21 | 1.46 | 0.37 | 1.00 | 1.00 | 1.00 | no | 1 |
| 2026-10-16 05:00 | VIIRS750 | NOAA20 | 58.0 | 8.36 (cons) | K | 1.61 | 0.19 | 0.20 | 0.34 | 1.11 | 1.53 | 0.61 | 2.45 | 1.05 | 1.76 | si | 2 |
| 2026-10-16 05:42 | VIIRS375 | NOAA21 | 2.0 | 5.33 (cons) | K | 4.80 | 0.90 | 0.90 | 0.90 | 0.99 | 1.03 | 0.07 | 0.83 | 1.00 | 1.00 | si | 1 |
| 2026-10-16 05:42 | VIIRS750 | NOAA21 | 2.0 | 15.63 (cons) | K | 14.84 | 0.95 | 0.95 | 0.95 | 1.16 | 1.29 | 0.16 | 0.86 | 1.00 | 1.00 | no | 1 |
| 2026-10-16 06:18 | VIIRS375 | SNPP | 37.6 | 11.24 (ocr) | K | 9.34 | 0.83 | 0.83 | 0.83 | 0.89 | 0.93 | 0.04 | 0.90 | 1.03 | 1.26 | no | 1 |
| 2026-10-16 06:18 | VIIRS750 | SNPP | 37.6 | 13.00 (ocr) | K | 8.12 | 0.62 | 0.62 | 0.62 | 0.97 | 1.19 | 0.25 | 1.31 | 1.03 | 1.26 | no | 1 |
| 2026-10-16 06:42 | VIIRS375 | NOAA20 | 60.6 | 14.63 (cons) | K | 6.59 | 0.45 | 0.45 | 0.45 | 0.51 | 0.54 | 0.10 | 1.65 | 1.19 | 2.10 | no | 1 |
| 2026-10-16 06:42 | VIIRS750 | NOAA20 | 60.6 | 14.02 (cons) | K | 2.01 | 0.14 | 0.32 | 0.32 | 0.65 | 0.83 | 0.55 | 2.60 | 1.19 | 2.10 | si | 1 |
| 2026-10-16 08:15 | MODIS | MODIS_AQUA | 19.9 | 13.70 (cons) | K | 11.61 | 0.85 | 0.85 | 0.85 | 1.39 | 1.70 | 0.38 | 0.88 | 1.12 | 1.19 | no | 1 |
| 2026-10-17 02:20 | MODIS | MODIS_TERRA | 54.0 | 12.97 (cons) | K | 2.64 | 0.20 | 0.20 | 0.20 | 0.41 | 0.53 | 0.62 | 3.67 | 2.66 | 4.17 | si | 1 |
| 2026-10-17 04:42 | VIIRS375 | NOAA20 | 68.0 | 7.39 (cons) | K | 0.84 | 0.11 | 0.04 | 0.20 | 0.29 | 0.34 | 0.29 | 3.80 | 1.86 | 3.88 | si | 2 |
| 2026-10-17 04:42 | VIIRS750 | NOAA20 | 68.0 | 2.47 (cons) | K | 0.22 | 0.09 | 0.09 | 0.09 | 0.70 | 1.03 | 0.91 | 9.03 | 1.86 | 3.88 | si | 1 |
| 2026-10-17 05:24 | VIIRS375 | NOAA21 | 27.8 | 11.03 (cons) | K | 4.99 | 0.45 | 0.45 | 0.45 | 0.51 | 0.54 | 0.08 | 1.65 | 1.26 | 1.40 | si | 1 |
| 2026-10-17 05:24 | VIIRS750 | NOAA21 | 27.8 | 21.00 (ocr) | K | 11.59 | 0.55 | 0.55 | 0.55 | 0.64 | 0.69 | 0.20 | 1.49 | 1.26 | 1.40 | no | 1 |
| 2026-10-17 06:00 | VIIRS375 | SNPP | 10.5 | 11.74 (ocr) | K | 10.34 | 0.88 | 0.88 | 0.88 | 0.96 | 1.00 | 0.06 | 0.85 | 1.03 | 1.05 | no | 1 |
| 2026-10-17 06:00 | VIIRS750 | SNPP | 10.5 | 17.00 (ocr) | K | 14.32 | 0.84 | 0.84 | 0.84 | 0.95 | 1.00 | 0.16 | 0.97 | 1.03 | 1.05 | no | 1 |
| 2026-10-17 06:18 | VIIRS375 | NOAA20 | 45.7 | 11.36 (cons) | K | 6.67 | 0.59 | 0.59 | 0.59 | 0.65 | 0.68 | 0.07 | 1.27 | 1.29 | 1.75 | no | 1 |
| 2026-10-17 06:18 | VIIRS750 | NOAA20 | 45.7 | 21.94 (cons) | K | 10.57 | 0.48 | 0.48 | 0.48 | 0.62 | 0.70 | 0.20 | 1.70 | 1.29 | 1.75 | no | 1 |
| 2026-10-17 08:50 | MODIS | MODIS_AQUA | 62.8 | 7.09 (cons) | K | 0.54 | 0.08 | 0.11 | 0.11 | 0.77 | 1.12 | 0.87 | 6.92 | 4.10 | 7.71 | si | 1 |
| 2026-10-18 01:20 | MODIS | MODIS_TERRA | 37.6 | 14.39 (cons) | K | 3.45 | 0.24 | 0.34 | 0.34 | 0.73 | 0.95 | 0.56 | 2.22 | 1.55 | 1.90 | si | 1 |
| 2026-10-18 05:06 | VIIRS375 | NOAA21 | 48.6 | 21.25 (cons) | K | 9.78 | 0.46 | 0.27 | 0.46 | 0.54 | 0.58 | 0.08 | 1.60 | 1.43 | 2.02 | no | 2 |
| 2026-10-18 05:06 | VIIRS750 | NOAA21 | 48.7 | 19.63 (cons) | K | 8.10 | 0.41 | 0.41 | 0.77 | 1.04 | 1.19 | 0.25 | 1.07 | 1.43 | 2.02 | no | 2 |
| 2026-10-18 05:42 | VIIRS375 | SNPP | 20.5 | 11.03 (ocr) | K | 7.00 | 0.64 | 0.64 | 0.64 | 0.72 | 0.76 | 0.10 | 1.17 | 1.13 | 1.20 | no | 1 |
| 2026-10-18 05:42 | VIIRS750 | SNPP | 20.5 | 20.87 (cons) | K | 14.03 | 0.67 | 0.67 | 0.67 | 0.83 | 0.92 | 0.27 | 1.22 | 1.13 | 1.20 | no | 1 |
| 2026-10-18 06:00 | VIIRS375 | NOAA20 | 22.3 | 9.94 (cons) | K | 7.20 | 0.72 | 0.72 | 0.72 | 0.83 | 0.89 | 0.08 | 1.03 | 1.16 | 1.24 | no | 1 |
| 2026-10-18 06:00 | VIIRS750 | NOAA20 | 22.3 | 18.98 (cons) | K | 13.60 | 0.72 | 0.72 | 0.72 | 0.88 | 0.98 | 0.16 | 1.14 | 1.16 | 1.24 | no | 1 |
| 2026-10-18 06:48 | VIIRS375 | NOAA21 | 67.6 | 25.79 (cons) | K | 8.93 | 0.35 | 0.16 | 0.36 | 0.43 | 0.47 | 0.09 | 2.05 | 1.81 | 3.73 | no | 2 |
| 2026-10-18 06:48 | VIIRS750 | NOAA21 | 67.6 | 22.85 (cons) | K | 2.84 | 0.12 | 0.19 | 0.30 | 0.72 | 0.96 | 0.48 | 2.74 | 1.80 | 3.72 | si | 2 |
| 2026-10-18 07:50 | MODIS | MODIS_AQUA | 23.1 | 18.36 (cons) | K | 8.91 | 0.49 | 0.49 | 0.49 | 0.76 | 0.91 | 0.39 | 1.54 | 1.17 | 1.26 | no | 1 |
