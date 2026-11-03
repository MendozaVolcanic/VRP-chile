# Verificacion de la investigacion VIIRS 375 en Nevados de Chillan (cenit): informe del verificador

## 1. Encabezado

- Fecha y hora del servidor al cerrar: **2026-11-03 01:08:56 GMT** (cabecera `Date` de `gh api -i repos/MendozaVolcanic/VRP-chile`; al abrir, 00:55:56 GMT).
- Commit sobre el que medi: **origin/main `5de08ebf62d1ea092c485c0a030f323f2cbdcf2a`** (el mismo que declara `C:/Users/nmend/vrp-wt/s173_cenit/v375/COMMIT_MAIN.txt`), tras `git fetch origin --prune`. Para la rama `loop/activo`: `ddd83c5b901e46451dfc0e422656162ad29a29cc`. Copias por `git archive` en `C:/Users/nmend/vrp-wt/s173_cenit/ver_v375/copia_main/` (scripts, pipeline, frontend, volcanoes.yaml, el JSON de Chillan, la referencia y `experiments/_s157_magnitud_chillan/`) y `.../copia_loop/experiments/_s162_v375/`.
- Modelo y esfuerzo reales: **Claude Fable 5.1, esfuerzo bajo** (el que trae la sesion; no se me paso otro).
- CARPETA: `C:/Users/nmend/vrp-wt/s173_cenit/ver_v375/`. Caminos escritos antes de abrir nada: `caminos.md` (sha256 `6f76ce54...a76e`, sellado 00:57:42 GMT; no editado despues).
- Prompt de la tarea: `D:/vrp-trabajo/temporales/s173_aud/prompts/ver_cenit_v375.txt`, sha256 `290c01be4cee0c7e793c1201be96cf28290ac0de33b827053d8113d3581a271c`.
- Lo que NO mire: el `INFORME.md` del auditor (a proposito); MODIS y VIIRS 750; el tablero en el navegador; la equivalencia entre la via del pipeline y el port del probe sobre granulos crudos (S165, `experiments/_s165_v375_via/`); los granulos L1B (no hay en disco); los otros informes de verificadores de S173. No despache workflows, no use credenciales, no toque nada fuera de CARPETA. Llamadas a la API de GitHub: 7 (de 40).
- Procesos pesados: uno a la vez (s01 2,4 s; s02 59 s). Disco al cerrar: C: 32 GB libres, D: 4,7 GB (no escribi en D:).

## 2. En una pantalla

1. Las seis afirmaciones se sostienen en el numero: los cuatro scripts del auditor (s01 a s04) re-corridos sobre mi copia de origin/main dan salidas **byte a byte identicas** (sha256 de los CSV y `diff` de los JSON), y un pareo escrito por mi sin sus helpers (`v01_pareo_propio.py`) recupera **los mismos 66 pares** de K, con la misma razon en los 66 (diferencia maxima 0,0): 0,745 bajo 30 grados (n 16) y 0,481 sobre 30 (n 50), Spearman -0,548, fuera del barajado global [-0,248; 0,234] y del barajado por plataforma [-0,256; 0,239] (200 barajados, semilla 173).
2. Lo que cae es la lectura, no el dato: (a) la sombra esta vacia **por diseno**, no por falla (`scripts/ventana_sombra.py` l. 23 `FECHA_MINIMA = date(2026, 11, 3)`; en las 4 corridas programadas el paso «Commit sombra data» salio `skipped`); (b) «los alertados de la via crecen con el cenit» es lo que el remuestreo hace por construccion y choca con la tarea 1.14 §3.2 (el Npix de MIROVA no crece hacia el borde): la «firma de D17» sigue siendo SOSPECHA, no sube; (c) «con el factor de area se aplana» es tautologico (f_area es monotono en el cenit, Spearman 0,873) y la version con fondo cero se pasa a 1,70 sobre 50 grados.
3. Los 13 de 46 desacuerdos con el C13 del probe son la degeneracion declarada del relleno `fillmissing2`: 9 caen dentro de la banda de jitter que el propio probe guardo, los 4 restantes son escenas de 1 y 4 pixeles (PREREGISTRO_E §8.6 punto 3); npix identico en 46 de 46; sobre 4 pixeles la diferencia maxima es 0,97 %.
4. Caminos cerrados: no hay granulos contados dos veces entre lotes (248 granulos, 248 claves); los 27 pares de B son todos K del reproceso `34cea39e` (un solo detector); el cenit del record (pixel del final_hotspot) difiere del del centro del volcan en 0,05 grados como maximo y ningun par cambia de tramo; CONS sola da las mismas medianas (n 60); la tolerancia (59, 120 o 600 s) no cambia nada; el pareo por noche si (0,283 y sin dependencia del cenit), como dijo el auditor S172.
5. Falta para decidir la palanca: una ablacion pieza a pieza en VIIRS 375 (no existe; la de VIIRS 750, `experiments/_s162_v750c/ablacion.py`, no tiene pieza de remuestreo ni familia 375) y el Npix por pasada de MIROVA (el scraper no lo trae).

## 3. Veredicto por afirmacion de la tarea

### (1) 27 pasadas pareadas: K 0,75 / 0,56 (Spearman -0,52, fuera), V375-E 0,92 / 1,00 (+0,28, dentro); V375-E/K 1,21 a 1,76. **CONFIRMADA**

- Mi medida: `rerun/s03_salida.json` (`diff` contra el del auditor: identico). B_K n 27: 0,753 (<30, n 7) / 0,562 (>=30, n 20), Spearman -0,515, barajado [-0,432; 0,333], fuera. B_via_publicada: 0,922 / 1,000, Spearman +0,283, barajado [-0,343; 0,327], dentro. B_via_sobre_K: 1,205 / 1,758, Spearman +0,556, fuera. Ventana de los pares: 2026-09-28 04:42 a 2026-10-16 06:42; 27 pasadas en 14 noches distintas (contadas en `rerun/s03_salida.txt`, DETALLE B').
- Caminos comprobados (`v02_salida.json`): (a) granulos contados dos veces: 248 granulos distintos, 248 claves (plataforma, hora), `granulo_con_dos_horas = {}`, `clave_con_dos_granulos = {}` (control positivo: un duplicado artificial sube el contador a 1); las 6 entradas «duplicada» que el s02 del auditor reporta son el mismo granulo en dos lotes y se fundieron en una fila (`lotes = S162+S162b+FAR`, 2 de los 27). (b) Detectores mezclados (A104): los 27 K de B tienen `codigo_sha 34cea39e` y `processed_utc` entre 2026-10-18 11:25 y 11:56 (el reproceso K), un solo detector. (c) Cenit: `K_z` (pixel del final_hotspot) contra `z_via` (geometria del centro del volcan del lote): diferencia maxima **0,05 grados**, 0 pares cambian de tramo en 30. (d) Barajado: el s03 baraja en un solo bucket (comentario l. 81-82 del script, «un solo bucket, VIIRS375»); barajando dentro de cada plataforma (mi v01, sobre los 66 de A) los veredictos no cambian.
- Reservas: n 7 bajo 30 grados; el tramo >= 50 (n 11) da K 0,506 y via 1,000. La via de B no es produccion: es `pipeline.mirova_v750_codigo.procesar_grilla` de origin/main corrida sobre grillas que el probe (S159 port, `experiments/_s162_v375/probe_v375.py`) remuestreo; ver VV375-05.

### (2) K de produccion completo, 66 pares hasta el 2026-11-02: 0,745 / 0,481, Spearman -0,55. **CONFIRMADA**

- Mi medida propia, sin banco_paridad ni node (`v01_pareo_propio.py`, `v01_salida.json`): 66 pares, los **mismos 66** que el auditor (`pares_mios_vs_auditor: comunes 66, solo_mios [], solo_auditor []`), razon identica en los 66 (`dif_max 0.0`); 0,745 (n 16) / 0,481 (n 50) / 0,347 sobre 50 (n 30); Spearman -0,548, barajado global [-0,248; 0,234], por plataforma [-0,256; 0,239]: fuera en los dos. Ventana de los pares 2026-09-28 04:42 a 2026-11-02 06:18, **27 noches distintas**. Denominador: 941 records VIIRS 375 nocturnos de Chillan y 1.188 filas CONS + 57 OCR de VIIRS375 entre 2026-04-01 y 2026-11-02.
- Robustez: tolerancia 59 s, 120 s y 600 s dan los mismos 66 pares; CONS sola (sin OCR) n 60, 0,745 / 0,481, Spearman -0,538, fuera; 6 de 66 toman el VRP de una fila OCR (5 de Suomi NPP, 2026-09-29 a 2026-10-09; el hito A119 del 2026-10-09 afecta distancia y clase de esas filas, no el VRP) y sin ellas la mediana por tramo no se mueve. Jackknife (Spearman sin cada par): [-0,580; -0,529]: ningun par gobierna.
- Pareo por noche (maximo de MIROVA de la noche): n 89, mediana 0,283, Spearman -0,177 **dentro** del barajado: la dependencia del cenit solo aparece pareando por pasada, como dice la vara.
- Controles: razon x cos(z)^2 da Spearman -0,880 fuera (positivo); x2 dobla la mediana (1,095); referencia corrida +1 dia: 14 «pares» (Chillan alerta noches seguidas a la misma hora, el control de corrimiento es debil en erupcion; el auditor obtuvo los mismos 14).
- Detectores (A104): los 66 K los escribieron **21 shas** de codigo (41 el reproceso `34cea39e` del 2026-10-18; 25 el NRT, 20 shas, 2026-10-18 a 2026-11-02; todos perfil `mirova_equivalent`). Entre `34cea39e` y origin/main los commits a `pipeline/process_viirs.py` y vecinos son adiciones bajo flag apagado para VIIRS 375 (`git log 34cea39e..origin/main -- pipeline/...`: 5b676337d V375-E «APAGADA», fb87ef554/3a02ad28f V750-A apagada, c4efdc78c/33f889bc5 MODIS) y `ENABLE_V375_CODIGO_MIROVA = False` en produccion (leido de `pipeline.profile` en copia_main). Los dos grupos caen igual: reproceso 0,737 (n 11) a 0,548 (n 30); NRT 0,810 (n 5) a 0,375 (n 20).

### (3) `data/sombra_codigo_mirova/` no existe en origin/main (n = 0) aunque el workflow corre con exito desde el 2026-10-31. **CONFIRMADA EN PARTE: el hecho si; «aunque» no: esta vacia por diseno (SIN DATO, no FALLA)**

- Hecho: `git ls-tree -l origin/main -- data/sombra_codigo_mirova/` da NO EXISTE (re-corri `s00_sombra_existe.py`: identico); ademas recorri **todas** las ramas remotas (`git for-each-ref refs/remotes/origin/`) y ninguna tiene archivos bajo esa ruta.
- Donde escribe de verdad el workflow (`.github/workflows/sombra-codigo-mirova.yml` en origin/main, TEXTO): commitea solo `data/sombra_codigo_mirova/${{ matrix.volcano }}.json` (paso «Commit sombra data», `git add "data/sombra_codigo_mirova/..."`, `git pull --rebase -X theirs origin main && git push`), o sea a **main**; y sube artifacts (`pipeline.log`, `cobertura.json`) solo si corrio. No escribe en otra rama ni en otra ruta.
- Por que esta vacia: el paso de correr llama `scripts/ventana_sombra.py`, que devuelve nada mientras `hoy < FECHA_MINIMA`; `scripts/ventana_sombra.py` l. 23, TEXTO: «`FECHA_MINIMA = date(2026, 11, 3)`», y l. 44-45: «`if hoy < minima:` / `return None`». El workflow entonces escribe `commit=false` y sale 0 («Todavia no toca: la sombra parte el 2026-11-03.»). Corridas (API: `actions/workflows/sombra-codigo-mirova.yml/runs`): programadas el 2026-10-30 19:52, 10-31 19:09, 11-01 19:24 y 11-02 23:00 UTC, las cuatro `success` en main; el job `process (NevadosDeChillan)` de la del 11-02 tiene «Run VRP pipeline» `success` y «Commit sombra data», «Revisar que salieron records», «Tachar» y «Guardar log» `skipped`. Hubo ademas un dispatch `medir` el 10-30 09:37 en main y otro el 10-29 en la rama `s167-sombra-medir` (medir no commitea).
- Consecuencia: «corre con exito» es verde sin datos (lo que S141 llama job verde sin datos), y el primer dia con ventana es **hoy 2026-11-03**: el cron dice 15:00 UTC pero las cuatro corridas observadas salieron 4 a 8 horas tarde. Hasta esa corrida no hay nada que leer de la sombra (SIN DATO).

### (4) La caja no es la pieza (n 14); el fondo no explica la pendiente; los alertados de la via crecen con el cenit (+0,53) y los de K no: firma de D17, SOSPECHA. **CONFIRMADA EN PARTE: los tres numeros se reproducen; la lectura «firma de D17» no sube de SOSPECHA y tiene una contradiccion sin resolver**

- Caja: `rerun/s03_salida.json` `ROI_brazos_sobre_MIROVA`: M14, C13, C21, CIRC y SENS dan exactamente lo mismo (n 14, mediana 1,001; 0,908 bajo 30 con **n 3**; 1,002 sobre 30 con n 11; Spearman 0,068 dentro de [-0,525; 0,556]); PIX7 0,996. Reproducido identico. Reserva: n 3 en el tramo bajo, y los brazos son del port ORA del probe (`experiments/_s162_v375/brazos.py` l. 1-27 y 34-36, TEXTO: «`import mirova_port as MP`», «`ORA = MP.ORA`»), no del pipeline; como todos coinciden entre si, la conclusion «la caja no mueve la razon en Chillan» se sostiene.
- Fondo: `rerun/s04_salida.json` `tbgK_menos_tbgvia_K`: mediana 7,63 K, 7,43 bajo 30 y 7,66 sobre 30, Spearman -0,007 dentro. Reproducido identico. Ojo con lo que compara: el `t_bg_k` de K es la temperatura del anillo regional y el de la via es la temperatura de brillo del fondo medio interpolado bajo los alertados (`pipeline/mirova_v750_codigo.py` l. 735-736, TEXTO: «fondo medio del .m bajo los alertados, en temperatura de brillo (para el log y el tablero; no decide nada)»). Son los dos fondos que cada camino usa, asi que «la diferencia de fondo no crece con el cenit» esta bien medida; pero una diferencia constante de 7,6 K (K mas tibio) es por si sola un deficit de magnitud grande e independiente del angulo, que el auditor no cuantifica.
- Alertados: `npix_via_por_tramo` 6,0 / 7,5 / 11,0 (>= 50), Spearman +0,534 fuera de [-0,426; 0,417]; `npos_K_por_tramo` 3 / 2 / 3, Spearman +0,146 dentro. Reproducido identico. **Dos reparos**: (a) el crecimiento del conteo de la via con el cenit es lo que el remuestreo a celdas fijas de 375 m hace por construccion (un pixel oblicuo mas grande cae en mas celdas), asi que mide que la via remuestrea, no que el remuestreo sea la pieza que corrige la razon; (b) choca con la tarea 1.14 §3.2 (`experiments/_s151_presupuesto_magnitud/README.md` l. 78-84, TEXTO: «Si eso fuera el remuestreo de MIROVA (D17), su Npix creceria hacia el borde ... **No crece**: medianas de 3, 5, 5 y 4 en las cuatro bandas (Tabla A3)»). Si la via da la magnitud de MIROVA (via/M 1,00) pero su Npix crece y el de MIROVA no, o la medida de 1.14 es de otra poblacion (OSF 2025, otros volcanes) o la via cuenta distinto que MIROVA; con el scraper no se puede saber (no trae Npix). Ver VV375-03.

### (5) No existe ablacion por pasada en VIIRS 375. **CONFIRMADA**

- `pipeline/mirova_v750_codigo.py` (origin/main): `procesar_grilla` l. 687-688 solo admite `coef` y `familia`; `detectar_mirova` l. 397-398 solo `lam_mir` y `lam_tir`; `vrp_mirova` l. 584 solo `coef`. No hay parametro que cambie remuestreo, fondo, media 3 x 3, umbrales ni compuerta.
- `experiments/_s162_v375/brazos.py` (loop/activo) solo varia la caja (docstring l. 13-23). `experiments/_s162_v375/PREREGISTRO_E.md` l. 39, TEXTO: «La atribucion pieza a pieza no es de aqui: va en ablaciones locales sobre las grillas guardadas.» No encontre esas ablaciones: `git grep -i ablaci` en `experiments/_s165_v375_via`, `_s172_chillan`, `_s172_proyeccion_v375` y `_s168` solo devuelve la de VIIRS 750.
- La ablacion de VIIRS 750 existe (`experiments/_s162_v750c/ablacion.py`, en main y loop/activo) con piezas `O_8vec`, `O_regp1`, `O_umbK`, `O_comp`, `O_sens`, `O_circ`, `O_rec`, `O_fanillo`, `O_sinhalo` (l. 46-55), pero no tiene pieza de remuestreo ni ninguna mencion a 375 (`grep -i 375`: 0). O sea que el instrumento mas cercano tampoco separa D17.

### (6) 13 de 46 pasadas re-corridas difieren del probe C13 en mas de 1e-3 MW. **CONFIRMADA EN PARTE: el conteo si; es la degeneracion declarada del relleno, no un desacuerdo de codigo**

- Reproducido identico (`rerun/s02_v375e_salida.txt`: n 46, 13 sobre 1e-3, maximo 0,0895 MW). Camino propio (`v02_salida.json`): npix identico en los 46; de los 13, **9 caen dentro de `vrp_banda`** (el rango que el probe guardo corriendo `ORA.vrp` con 20 semillas de perturbacion de 1e-6 en la triangulacion, `experiments/_s159/portes/mirova_port.py` l. 116-118); los 4 que quedan fuera son escenas de 1 pixel (3) y 4 pixeles (1), donde `PREREGISTRO_E.md` l. 132-134 (TEXTO: «La vara del paso 1 (equivalencia) cambia en el fondo de 1 a 4 pixeles. La via de main rellena con el `fillmissing2` de MATLAB y `brazos.py` con el port viejo») declara que el relleno difiere. Sobre 4 pixeles (4 pasadas: 5, 14, 11 y 8 pixeles) la diferencia relativa maxima es **0,97 %** y las 4 estan dentro de la banda. La mayor diferencia absoluta (2026-05-31 06:24, NOAA-20, 1 pixel: 0,320 contra 0,410, 22 %) queda en el borde de la banda [0,3205; 0,4095].
- Gravedad 1 se sostiene: ninguna de las 13 esta entre los 27 pares de B con razon decisiva salvo 2026-09-29 05:00 (0,48 %), 2026-09-29 06:00 (0,22 %) y 2026-10-05 06:24 (0,03 %).

## 4. Veredicto por hallazgo del auditor (`hallazgos.csv` del auditor, solo titulo, archivo:linea y gravedad)

| ID | Veredicto | Mi gravedad | Evidencia de esta sesion |
|---|---|---|---|
| CV375-01 | CONFIRMADO | 4 | (1) y (2) arriba; `rerun/s03_salida.json` identico; `v01_salida.json` |
| CV375-02 | CONFIRMADO EN PARTE (vacia por diseno hasta el 2026-11-03; la gravedad es de espera, no de falla) | 2 | (3) arriba; `ventana_sombra.py` l. 23; jobs del run 41541988051 |
| CV375-03 | CONFIRMADO EN PARTE (los numeros si; «firma de remuestreo» sigue SOSPECHA y contradice 1.14 §3.2) | 3 | (4) arriba; VV375-03 |
| CV375-04 | CONFIRMADO EN PARTE (fondo cero sigue cayendo: Spearman -0,363 contra [-0,323; 0,299], apenas fuera; «con el area se aplana» es por construccion) | 2 | `rerun/s04_salida.json` identico; VV375-04 |
| CV375-05 | CONFIRMADO (n 14, n 3 bajo 30; brazos del port ORA, no del pipeline) | 3 | (4) arriba |
| CV375-06 | CONFIRMADO: `docs/MIROVA_DIVERGENCES.md` l. 2861 (origin/main), TEXTO: «## D25: El fondo del VRP es la mediana de un anillo regional de 5 a 25 km, no la media de los pixeles que rodean al activo; y el exceso se recorta a cero.» La «geometria del borde del barrido» del encargo es D17 (l. 2317) y D28 (l. 3034, «El bow tie de MODIS ... parte de D17») | 2 | `git show origin/main:docs/MIROVA_DIVERGENCES.md | sed -n 2861p` |
| CV375-07 | CONFIRMADO | 2 | (5) arriba |
| CV375-08 | CONFIRMADO EN PARTE (conteo si; causa: relleno degenerado, declarado) | 1 | (6) arriba |
| CV375-09 | CONFIRMADO: 2026-08-20 05:12 NOAA-21 (CONS, 0,06 MW a 0,38 km; K 0 pixeles; via 0,073) y 2026-09-05 05:48 Suomi NPP (CONS, 0,14 MW a 1,91 km; K 0 pixeles; via 0,196). Con la regla SN (umbral 0,05) las dos son alerta; la de 0,06 queda a 0,01 del umbral | 2 | `rerun/s01_k_pasadas.csv` filas de esas pasadas; `rerun/s03_salida.txt` «via_pub_K_no» |

## 5. Hallazgos propios (VV375-01 en adelante), ordenados por gravedad

### VV375-01
- TITULO: La «firma de remuestreo» del auditor contradice la tarea 1.14 §3.2 y mide lo que el remuestreo hace por construccion
- ARCHIVO:LINEA: `experiments/_s151_presupuesto_magnitud/README.md:78-84` (origin/main); `C:/Users/nmend/vrp-wt/s173_cenit/ver_v375/rerun/s04_salida.json` (`npix_via_por_tramo`, `npos_K_por_tramo`)
- QUE PASA: fisicamente, un pixel oblicuo de VIIRS cubre mas terreno; al interpolarlo a celdas fijas de 375 m la misma mancha ocupa mas celdas, asi que el conteo de alertados de la via crece con el cenit **siempre**, haya o no deficit que corregir. La tarea 1.14 midio que el Npix de MIROVA no crece hacia el borde. Si la via reproduce la magnitud de MIROVA (via/M 1,00 en B) pero su conteo crece y el de MIROVA no, hay una de dos: 1.14 midio otra poblacion, o la via cuenta distinto que MIROVA. Nadie lo ha medido pasada a pasada en Chillan.
- COMO SE VE EN EL DASHBOARD: invisible (la via no publica).
- COMO REPRODUCIRLO: `python -B rerun/s04_firmas_por_cenit.py rerun/s02_v375e_pasadas.csv rerun/s01_k_pasadas.csv ../v375/_s157_a_pasadas.json rerun/s04_salida.json`; `git show origin/main:experiments/_s151_presupuesto_magnitud/README.md | sed -n '76,84p'`.
- CONFIANZA: CONFIRMADO en la contradiccion y en el mecanismo por construccion; SOSPECHA en cual de las dos salidas vale.
- GRAVEDAD: 3 (es la decision de que palanca tirar).

### VV375-02
- TITULO: La via de los lotes retrospectivos no es la via de produccion entera: el remuestreo es del probe (port S159), el resto del pipeline
- ARCHIVO:LINEA: `C:/Users/nmend/vrp-wt/s173_cenit/v375/s02_v375e_retro.py:56-72` (carga `grilla_{id}.npz` y corre `MV.procesar_grilla`); `experiments/_s162_v375/brazos.py:34-36` (loop/activo)
- QUE PASA: la grilla de cada pasada la escribio el probe de S159/S162 con su propio remuestreo; `procesar_grilla` de origin/main se corre encima. Si el `remuestrear_grilla` del pipeline (`pipeline/mirova_v750_codigo.py:198`) difiere del del probe, la razon de «V375-E» medida aqui no es la de la via de `pipeline/`. La equivalencia se midio en S165 (`experiments/_s165_v375_via/equivalencia_v375e.py`), que no re-corri.
- COMO SE VE EN EL DASHBOARD: invisible.
- COMO REPRODUCIRLO: leer `s02_v375e_retro.py` l. 56-72; comparar con `pipeline/mirova_v750_codigo.py:198-224` y `:788-830`.
- CONFIANZA: SOSPECHA (hay que correr la equivalencia o esperar la sombra del 2026-11-03).
- GRAVEDAD: 2.

### VV375-03
- TITULO: «Con el factor de area se aplana» es por construccion, y el techo con fondo cero mas area se pasa a 1,70 sobre 50 grados
- ARCHIVO:LINEA: `experiments/_s157_magnitud_chillan/a_pasadas.py:25-28,246-247` (origin/main); `rerun/s04_salida.json` (`s157_f_area`, `s157_G_area`, `s157_G_area_fondo0`)
- QUE PASA: `G_area = G x f_area(cenital)` donde `f_area` es un modelo geometrico monotono en el cenit (Spearman 0,873 contra el cenit, n 44); multiplicar una curva que cae por un factor que sube la aplana por definicion. Es un techo (asi lo llama el docstring), no una atribucion. Y `G_area_fondo0` da 1,116 / 1,172 / **1,702** (>= 50): area y fondo cero juntos sobran, asi que no pueden ser las dos piezas a la vez.
- COMO SE VE EN EL DASHBOARD: invisible.
- COMO REPRODUCIRLO: el mismo comando de VV375-01; leer `a_pasadas.py` l. 21-28.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2.

### VV375-04
- TITULO: El «cenit» del record de K es el del pixel mas cercano al final_hotspot, no el del volcan; en Chillan no cambia ningun tramo
- ARCHIVO:LINEA: `pipeline/process_viirs.py:2249-2253` (origin/main, TEXTO: «`**observation_geometry(geo["lat"], geo["lon"], geo.get("angles"), final_hotspot_lat if final_hotspot_lat is not None else vent_lat, ...`»); `pipeline/scan_geometry.py:395-430`
- QUE PASA: la vara pide el cenit «en el volcan»; el record guarda el del pixel del hotspot final (o del crater si no hay). Medido en los 27 pares de B contra la geometria del centro del volcan del lote: diferencia maxima 0,05 grados, 0 cambios de tramo (`v02_salida.json`). En un volcan con hotspot lejano (25 km) el desvio podria ser de un grado o dos; aqui no.
- COMO SE VE EN EL DASHBOARD: invisible.
- COMO REPRODUCIRLO: `python -I v02_lotes_cenit_c13.py rerun/s02_v375e_pasadas.csv rerun/s01_k_pasadas.csv v02_salida.json` (claves `B_dz_max_Kz_menos_zvia`, `B_cambian_de_tramo_30_segun_cenit`).
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 1.

### VV375-05
- TITULO: Los 66 pares de K los escribieron 21 shas de codigo (41 reproceso, 25 NRT); todos K, los dos grupos caen con el cenit
- ARCHIVO:LINEA: `v01_salida.json` (`por_codigo_sha`); `v00_salida.txt`; `git log --oneline 34cea39e..origin/main -- pipeline/process_viirs.py ...`
- QUE PASA: no es defecto, es el camino A104 cerrado: ningun commit posterior a K cambio la ruta de VIIRS 375 en produccion fuera de codigo bajo flag apagado (`ENABLE_V375_CODIGO_MIROVA = False` leido de `pipeline.profile`); reproceso 0,737 a 0,548, NRT 0,810 a 0,375.
- COMO SE VE EN EL DASHBOARD: invisible.
- COMO REPRODUCIRLO: `python -I v01_pareo_propio.py copia_main rerun/s01_k_pasadas.csv v01_salida.json` y el bloque inline guardado en este informe (grupos por sha).
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 1.

### VV375-06
- TITULO: La primera corrida con datos de la sombra es la de hoy y el cron llega 4 a 8 horas tarde
- ARCHIVO:LINEA: `scripts/ventana_sombra.py:23`; corridas 41118756898, 41232878558, 41341608741, 41541988051 (19:52, 19:09, 19:24 y 23:00 UTC contra `cron: "0 15 * * *"`)
- QUE PASA: quien lea la sombra el 2026-11-03 a las 15:00 UTC puede encontrarla vacia todavia; el primer record esperable es en la tarde o noche UTC del 11-03, o el 11-04 si la corrida se desplaza mas.
- COMO SE VE EN EL DASHBOARD: invisible (el tablero no lee la sombra).
- COMO REPRODUCIRLO: `gh api "repos/MendozaVolcanic/VRP-chile/actions/workflows/sombra-codigo-mirova.yml/runs?per_page=10"`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 1.

## 6. SEGUIMIENTOS (fuera de mi eje, dejados reproducibles)

- S-1. El fondo de K es 7,6 K mas tibio que el de la via en los 27 pares, constante con el cenit (`rerun/s04_salida.json` `tbgK_menos_tbgvia_K`). Ese sesgo constante no explica la pendiente pero si parte del nivel (via/K 1,55 de mediana). Nadie lo convirtio a MW. Confianza CONFIRMADO en el numero, SOSPECHA en cuanto pesa.
- S-2. El control negativo de corrimiento +1 dia del s01 del auditor (y de mi v01) da 14 pares en vez de ~0 porque Chillan en erupcion alerta noches seguidas a la misma hora de pasada: en erupcion ese control no distingue «pareo roto» de «pareo bueno». Un control mejor es corrir +1 dia y exigir misma plataforma y minuto exacto (mi tolerancia 59 s con +1 dia no lo corri). Confianza CONFIRMADO.
- S-3. `s03_estratos_cenit.py` l. 81-82 (auditor) dice barajar «dentro del sensor» y baraja en un solo bucket; en VIIRS 375 el sensor es uno, asi que coincide con la vara, pero el comentario induce a leer que estratifica por plataforma. Por plataforma (mi v01) los veredictos no cambian. Confianza CONFIRMADO, gravedad 1.
- S-4. La referencia local `mirova_v1_snapshot` esta al dia (CONS maximo 2026-11-02 12:20; OCR 2026-11-02 06:18; ultimo commit remoto de Mirova-v1 al CSV 2026-11-03 01:01 UTC, el scraper corre cada 5 min): el camino «copia atrasada» esta cerrado para esta ventana.

## 7. VERIFICADO LIMPIO

- Re-corrida de los cuatro scripts del auditor sobre mi copia de origin/main (`git archive 5de08ebf6`): `rerun/s01_k_pasadas.csv` sha256 `5c083820...2c76` igual al del auditor; `rerun/s02_v375e_pasadas.csv` sha256 `65bde011...6819` igual; `rerun/s03_salida.json` y `rerun/s04_salida.json` `diff` vacio. Vara: la misma del auditor (referencia del snapshot, regla SN, predicado del tablero con node); por eso ademas medi por otro camino.
- Pareo propio (`v01_pareo_propio.py`): mismos 66 pares y mismas razones; predicado aproximado (`distance_class == summit` y magnitud > 0, f5_core con fallback a pc.vrp_mw) coincide con el de node en los 66 (`desacuerdo_predicado_aprox_vs_node_auditor: 0`). Vara: CSV crudo y JSON crudo de origin/main.
- Insumos (`v00_salida.txt`): 0 duplicados (sensor, datetime_utc) en los 6.879 records de Chillan (control positivo +1 artificial: 1); 151 records VIIRS 375 en la ventana de los pares, todos `product_version standard`; 0 minutos con dos plataformas; nombre del volcan en la referencia una sola variante («Nevados de Chillan», 4.348 filas CONS, 102 OCR).
- Copia de `_s157_a_pasadas.json` del auditor: sha256 `b42bd8f4...e84f0` igual al blob de origin/main.
- `s00_sombra_existe.py` re-corrido: salida identica (NO EXISTE; `DESDE_P = 2026-11-03`; cron `0 15 * * *`).

## 8. SIN DATO

- V375-E prospectiva (sombra): 0 records hasta la corrida del 2026-11-03; nada que medir.
- Npix por pasada de MIROVA en Chillan (el scraper no lo trae; el OSF llega a 2025): sin el no se cierra VV375-01.
- Equivalencia entre la via del pipeline sobre granulo crudo y el port del probe sobre las mismas pasadas (S165): no re-corrida (no hay L1B en disco, no hay credenciales que yo pueda usar).
- Un 2.5 % del barajado con 200 barajados sobre n 7 y n 3 (tramos bajos de B y de ROI) es ruidoso: los intervalos de B (p. ej. [-0,432; 0,333]) son asimetricos por eso, no por un defecto.

## 9. FUERA DE ALCANCE

- MODIS y VIIRS 750 en Chillan (otros verificadores). La decision D25 contra D17. El tablero en el navegador. Mirova-v1 (el scraper) y la calidad del OCR mas alla de los hitos A119 que afectan a los 66 pares.

## 10. Instrumentos de esta carpeta

- `caminos.md` (sellado antes de leer), `v00_insumos.py` (+ `v00_salida.txt`), `v01_pareo_propio.py` (+ `v01_salida.json`, `v01_salida.txt`), `v02_lotes_cenit_c13.py` (+ `v02_salida.json`, `v02_salida.txt`), `v05_hallazgos_csv.py` (+ `hallazgos.csv`), `rerun/` (copias de s01 a s04 del auditor con mis salidas y `s0N_time.txt`), `copia_main/` y `copia_loop/` (git archive, con `COMMIT.txt`).

---
sha256 al cerrar (sin este pie): INFORME.md 44f15441c53099c6 | hallazgos.csv ae862db76c68e95a | caminos.md fc5b69b5...2173 | hora del servidor 2026-11-03 01:13:57 GMT
