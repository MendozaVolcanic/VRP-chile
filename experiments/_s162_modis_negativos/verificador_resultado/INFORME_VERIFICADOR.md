# Verificador con contexto limpio: resultado del lote MOD-C (run 40120713181)

## 1. Encabezado

- **Hora del servidor** (header `Date` de api.github.com): inicio Sat, 24 Oct 2026 18:41:37 GMT; `caminos.md` sellado
  a las 18:43:11 GMT (sha256 `918468c2f4bb39df1c79b89eb03786e7204727b9a099d0e5a9e6bb1666791f95`); última medición
  18:56:01 GMT.
- **Commit sobre el que medí**: el worktree estaba en `11570ab307c3adcee5d2b7b8b96afb01450c86a9` al empezar y pasó a
  `674de538cbdc2b650add6380e8929a0b965e4a1c` durante la sesión (otra sesión commitea en este worktree, ver VRC-04).
  Los archivos que medí de `experiments/_s162_modis_negativos/` (objetivos, 07, 03, filas, envoltorio) son iguales por
  blob al commit de disparo `ffc1abc1be95db1a9bac87b3dddf839604c76436` en los dos HEAD (`v05b_arbol_crlf_salida.txt`).
  Commit base del port: `0e18e1053bb1cdc3fe1a4ef8d0c1aa72bbe60e64`. `origin/main` al medir: `31da3ce89`.
- **Modelo y esfuerzo**: Claude Fable 5.1, esfuerzo medio, subagente verificador sin acceso al razonamiento del autor.
- **CARPETA**: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s162-modis-774bb0\experiments\_s162_modis_negativos\verificador_resultado\`
  (scripts `v01` a `v13` con su `_salida.txt` al lado; `07_recorrido_salida.txt` es mi re-corrida del lector).
- **Qué NO miré** (para que el silencio no se lea como «todo bien»): no re-corrí el port ni K sobre gránulos (sin
  pyhdf en Windows; lo que verifico es la lectura del lote, no el detector); no verifiqué la geolocalización MxD03 de
  ningún gránulo (el §10 del pre-registro lo deja como SOSPECHA abierta y sigue abierto); no bajé los logs de GitHub de
  los jobs (usé los `probe_MODIS_<k>.log` del artefacto, que son el mismo stdout, más la API de jobs: 3 llamadas de 10);
  no verifiqué las 149 filas congeladas de S159 (`filas_lote_s159_modis_fisica.json`) contra el run de S159, sólo que
  reproducen ΔE_otros = −44,0; no leí `experiments/_s162_modis_verif_cde/INFORME.md` ni `ronda2/`. Leí
  `INFORME.md` del autor sólo después de sellar `caminos.md`, para comparar la redacción de R4.

## 2. En una pantalla

1. **R1 CONFIRMADO.** Re-corrí `07_leer_lote.py`: salida **idéntica byte a byte** a la del autor. Con mi propia
   implementación de la regla (otra semilla, otro flujo): x = 2 de n = 390 da punto −18,1, IC [−44,4; +40,1],
   INDECIDIBLE (el autor: [−43,8; +40,1]; la diferencia es ruido de Monte Carlo). n cuenta lo que la regla dice: las
   400 son `neg_resto` de la población congelada por mi propia derivación (0 fuera), sin repetidas, `pub_prod` = 0 en las
   400, y las 10 no evaluables salen de n como manda el §6.
2. **R2 CONFIRMADO.** 413 de 413 con resultado, 405 `ok` + 8 «volcán fuera del gránulo», 2 `escena_invalida`; K
   re-corrido publica igual que lo declarado en 403 de 403 (con poder: 9 de las 11 protegidas tienen `pub_prod` = 1 y K
   las publica, 2 no y K calla); 13 de 13 controles iguales a S159 leídos directo de su JSON (npix, VRP, píxeles y
   gránulo); 11 de 11 protegidas publican; los 413 `.npz` abren, con capas, forma y gránulo coherentes (1 salvedad de
   nombre, VRC-02).
3. **R3 CONFIRMADO.** `probe_portes.py:445-455` devuelve 2 si alguna pasada tiene `estado != ok`; los 8 «fuera del
   gránulo» caen en los trozos 1 a 7 (el 2 tiene dos) y el trozo 0 tiene cero: exactamente los 7 rojos y el 1 verde de
   la API. Ningún `estado` empieza con `error`, ningún record trae `traza`, ningún K trae `error`.
4. **R4 CONFIRMADO EN PARTE.** Las dos publicaciones son un píxel (n_p1 = 1, n_p2 = 0, n_abs = 0), Láscar a 1,0 km del
   centro de grilla y **0,17 km del cráter** (`vent`), Llaima a 2,0 km del centro y 2,06 km del cráter; ambas nocturnas.
   La frase «del orden de la de producción (0,76 %)» compara denominadores distintos: 2/390 es la tasa en `neg_resto`,
   donde K publica 0 por definición; en el denominador de K (5.132 negativos limpios) el port da **0,54 %** punto
   (VRC-01). La conclusión (REPRODUCE a R3) no cambia.
5. **Lo que más importa**: el veredicto se aplicó sin margen. Pero **las dos publicaciones son decisivas**: con x = 0
   (n = 388 o 390) la regla daría CONFIRMA. Verifiqué que son robustas al instrumento: mismas con el `index.html` de
   `origin/main` de hoy, presentes en las variantes `fisica`, `pixel` y `sensible`, y no hay ningún otro `neg_resto`
   con npix > 0 en `fisica` al borde del `inner` (sólo esas 2 de 390). Dependen de la banda 22 y del MxD03: en
   `fisica_b21` y `fisica_geo5km` las dos dan 0 (VRC-05, informativo).

## 3. Veredicto por afirmación

| | Veredicto | Mi gravedad | Evidencia (esta sesión) |
|---|---|---|---|
| R1 | **CONFIRMADO** | n/a | `07_recorrido_salida.txt` (idéntico), `v02`, `v03`, `v03b`, `v06`, `v07` |
| R2 | **CONFIRMADO** | n/a | `v01`, `v02`, `v07` (§3), `v08`, `v11` |
| R3 | **CONFIRMADO** | n/a | `v01` (por trozo), `v04_logs`, `v04_jobs_api`, `v09_probe_codigo` |
| R4 | **CONFIRMADO EN PARTE** (geometría sí; la comparación de tasas mezcla denominadores) | 2 | `v07` §1, `v12` |

### R1, detalle de los caminos de `caminos.md` que probé

- *El instrumento mide otra cosa*: no. «Publica» es el predicado del tablero ejecutado con node
  (`banco_paridad.py:103-139`, `_JS` extrae `isSummitDetection`, `isValidDetection`, `isThermalArtifact`,
  `mirovaEqVrpDisplay` del `frontend/index.html`), sobre `record_port` (`04_analizar.py:59-73`). Lo corrí además con el
  `index.html` de `origin/main` de hoy: 0 de 806 casos cambian (`v07` §3).
- *n no cuenta lo que la regla dice*: derivé el estrato desde `poblacion_completa.json` con mi propio clasificador
  (tipo de fila de MIROVA, `pub_prod`), sin el 17 al 20 de octubre: `neg_resto` 5.093, marco 5.055, `pos_prot` 50,
  K 39 de 5.132 (`v03b`). Las 400 del lote están en el estrato (0 fuera), todas con fila sólo `CONS`, ninguna repetida
  por (volcán, hora, sensor), ninguna de las 38 de S159 (`v02`, `v03`). Pesos 12,33 a 13,57 y suma 5.055,0.
- *La regla cambió después de ver datos*: `03_regla_decision.py` y `07_leer_lote.py` son el mismo blob en el commit de
  disparo y en HEAD (`v05b`). El §5 del pre-registro no cambió (`v05c_diff_prereg_salida.txt`); lo que cambió es
  texto del §6 a §8 y la adenda 2, ver VRC-03.
- *El IC no corresponde a 2/390*: Jeffreys Beta(2,5; 388,5) da IC [0,0011; 0,0164], o sea [5; 83] pasadas del marco;
  sumado al bootstrap de ΔE_otros ([−59,5; −29,5], reproducido exacto) da [−44,4; +40,1] (`v06`). Las fronteras de la
  tabla del §3 se reproducen con n = 390: x = 7 INDECIDIBLE, x = 8 REFUTA, x = 0 CONFIRMA; controles de la regla
  (40/400 REFUTA, 0/400 CONFIRMA) pasan.
- *La ventana no contiene el fenómeno*: la muestra va del 2026-03-01 al 2026-10-21 sin el 17 al 20, con los 11 volcanes
  en proporción al estrato (Chaitén 45 contra 45,1 esperado, Láscar 21 contra 22,7, etc.) y por cenit 170/230 contra
  2.188/2.983 (`v03`).
- *El árbol no es el commit base*: los 388 archivos del árbol que existen en `0e18e1053` son idénticos por blob tras
  normalizar CRLF (387 tenían CRLF por el checkout en Windows; **0 distintos de verdad**); `04_analizar.py` es el blob de
  `origin/s159-pruebas` (`v05b`). Los tres blobs que el workflow exige coinciden con el commit base.

## 4. Hallazgos (orden de gravedad; ninguno cambia el veredicto)

### VRC-01
- TÍTULO: La comparación «0,5 % del orden de 0,76 %» de R4 mezcla dos denominadores
- SCRIPT:SALIDA: `v12_tasa_comparable.py` : `v12_tasa_comparable_salida.txt`; texto en `INFORME.md` del autor, «En una
  pantalla» punto 2
- QUÉ PASA: 2/390 es la tasa del port en `neg_resto`, un estrato donde K publica 0 por construcción; 39/5.132 es la de K
  en todos los negativos limpios. En el mismo denominador que K, el port da (2,0 de `neg_pub` + 5.055 · 2/390)/5.132 =
  **0,54 %** punto, y el R3 pre-registrado ya lo mide como IC [0,14 %; 1,66 %] con REPRODUCE. La conclusión se
  sostiene; la frase compara peras con manzanas (A90, A93).
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python -I experiments/_s162_modis_negativos/verificador_resultado/v12_tasa_comparable.py experiments/_s162_modis_negativos`
- CONFIANZA: CONFIRMADO
- GRAVEDAD: 2

### VRC-05
- TÍTULO: Las dos publicaciones deciden el veredicto y existen sólo con banda 22 y geolocalización MxD03
- SCRIPT:SALIDA: `v07_publicaciones_y_silencios.py` : `v07_publicaciones_y_silencios_salida.txt` (§1 «otras variantes»)
  y `v06_veredicto_independiente_salida.txt` (x = 0, n = 388: CONFIRMA)
- QUÉ PASA: con x = 0 la regla daría CONFIRMA (IC [−56,5; −10,0] a n = 388), así que todo el veredicto cuelga de dos
  píxeles de 0,30 y 0,43 MW. Las dos aparecen en `fisica`, `pixel` y `sensible` y desaparecen en `fisica_b21` y
  `fisica_geo5km`: son publicaciones que sólo la configuración principal produce. No es un defecto de instrumento (el
  pre-registro declara `fisica` como la única que decide), pero quien lea el INDECIDIBLE debe saber que lo producen dos
  eventos y qué palancas los producen. En la variante `sensible` hay 7 de 390 con npix > 0 (descriptivo).
- CÓMO SE VE EN EL DASHBOARD: si el port fuera producción, el operador vería dos anomalías `summit` de un píxel (Láscar
  0,30 MW a 0,17 km del cráter; Llaima 0,43 MW a 2,06 km) en noches que MIROVA dejó en RUTINA.
- CÓMO REPRODUCIRLO: `python -I experiments/_s162_modis_negativos/verificador_resultado/v07_publicaciones_y_silencios.py experiments/_s162_modis_negativos experiments/_s162_modis_verif_cde/arbol C:/vrp-trabajo/temporales/s162_negmodis/run_40120713181 experiments/_s162_modis_negativos/verificador_resultado`
  (Láscar 2026-05-11 07:55 UTC, Llaima 2026-07-24 01:05 UTC)
- CONFIANZA: CONFIRMADO
- GRAVEDAD: 2

### VRC-06
- TÍTULO: 6 de las 10 pasadas «partidas» del sorteo son no evaluables, contra 4 de 390 en las demás
- SCRIPT:SALIDA: `v13_partidas_salida.txt`
- QUÉ PASA: una pasada partida (el volcán cerca del borde del gránulo) cae con más frecuencia en «volcán fuera del
  gránulo» o «escena inválida». El pre-registro (§3) dice que las partidas «entran y se informan aparte» y el lector las
  informa (0 de 4 evaluables); lo que no está dicho es que la no evaluabilidad se concentra en ellas (6 de 10 contra
  4 de 390). Como la regla aplica la tasa de las evaluables a todo el marco y en las no evaluables el port no puede
  publicar, es conservador en la dirección declarada; sólo cambia la lectura de «10 no evaluables al azar».
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: comando en `v13_partidas_salida.txt` (heredoc en el historial); ids 1212, 1230, 1260, 1355, 1367,
  1394.
- CONFIANZA: CONFIRMADO
- GRAVEDAD: 1

### VRC-02
- TÍTULO: Pasada 1399 planeada con gránulo NRT y leída con el Standard; el record conserva el nombre planeado
- SCRIPT:SALIDA: `v11_control_s159_y_errores_k.py` : `v11_control_s159_y_errores_k_salida.txt`; `v08_nativos_salida.txt`
- QUÉ PASA: el objetivo 1399 (Aqua 2026-10-21 08:05) tiene `granule = MYD021KM.A2026294.0805.061.2026294095729.NRT.hdf`
  y el recorte nativo declara `l1b = MYD021KM.A2026294.0805.061.2026294223512.hdf` (Standard, misma adquisición). El
  record de producción del estrato se escribió con el NRT; el K re-corrido usó el Standard y publicó igual (0). Es la
  única de 413 (1 objetivo NRT, 0 leídos NRT). El campo `granule` del resultado repite el del objetivo, no el leído: para
  saber qué archivo se procesó hay que mirar `nativo.l1b`.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python -I experiments/_s162_modis_negativos/verificador_resultado/v11_control_s159_y_errores_k.py experiments/_s162_modis_negativos C:/vrp-trabajo/temporales/s162_negmodis/run_40120713181 D:/vrp-trabajo/temporales/s159_portes/run_39712862945 experiments/_s162_modis_verif_cde/arbol`
- CONFIANZA: CONFIRMADO
- GRAVEDAD: 1

### VRC-03
- TÍTULO: El cuerpo sellado del pre-registro se editó en sitio después del commit de disparo (texto, no la regla)
- ARCHIVO:LÍNEA: `experiments/_s162_modis_negativos/PREREGISTRO.md` l. 132, 135, 142, 165 (diff `ffc1abc1b..HEAD` en
  `v05c_diff_prereg_salida.txt`)
- QUÉ PASA: el propio documento dice (l. 5) «Lo que cambie después del commit de este archivo va en una adenda fechada al
  final, nunca reescribiendo esto». El commit `b6edffb92` (16:53:56 GMT) corrigió en sitio «10 pasadas» por «13», «6 de
  6» por «8 de 8» y el costo, además de agregar la adenda 2 que lo declara. Es anterior al arranque del run
  (18:26:31 GMT) y no toca §1 a §5; la regla de decisión está intacta y es el mismo blob de `03_regla_decision.py`.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `git diff ffc1abc1be95db1a9bac87b3dddf839604c76436 HEAD -- experiments/_s162_modis_negativos/PREREGISTRO.md`
- CONFIANZA: CONFIRMADO
- GRAVEDAD: 1

### VRC-04
- TÍTULO: El worktree cambió de commit durante la verificación (otra sesión commitea en él)
- SCRIPT:SALIDA: `git rev-parse HEAD` al inicio `11570ab30`, al final `674de538c` (log de esta sesión; `v05b` y
  `v10_commits_salida.txt`)
- QUÉ PASA: una línea base sobre un árbol que se mueve no es línea base (A112). Lo cubrí comparando por blob los archivos
  que leo contra el commit de disparo (iguales en los dos HEAD), pero quien repita mis comandos debe fijar el commit.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `git log --oneline 11570ab30..HEAD`
- CONFIANZA: CONFIRMADO
- GRAVEDAD: 1

## 5. SEGUIMIENTOS (fuera de mi eje, reproducibles)

- K no publica en 2 de las 11 protegidas de control (Chillán 2026-10-12 07:20 y 2026-10-15 01:05, `pub_prod` = 0,
  `pc = None`) y el port sí (npix 3 y 5): `v07_publicaciones_y_silencios_salida.txt` §3 y `v11`. Es el frente del
  «gana» de S159, no de este lote. Confianza CONFIRMADO en el dato; sin juicio.
- 12 evaluables tienen el centro de grilla a 1,5 a 2,0 km del centro del píxel MxD03 más cercano del recorte
  (`v08_nativos_salida.txt`): es el tamaño del píxel al borde del barrido, no un recorte corrido; lo anoto para MOD-E
  (bow tie), que es donde importa. Los dos casos a 3,7 y 4,3 km son los `escena_invalida`.
- `caminos.md` R1.9 (pareo por fecha local) no aplica: `hora_utc` se usa como cadena UTC en todo el lector
  (`07_leer_lote.py:167`).

## 6. VERIFICADO LIMPIO (qué, con qué comando, contra qué vara)

| Qué | Comando | Vara |
|---|---|---|
| El lector reproduce la salida del autor | `python -I experiments/_s162_modis_negativos/07_leer_lote.py --raiz experiments/_s162_modis_verif_cde/arbol --art C:/vrp-trabajo/temporales/s162_negmodis/run_40120713181 --s159 D:/vrp-trabajo/temporales/s159_portes/run_39712862945 --salida <CARPETA>/07_recorrido_salida.txt` y `cmp` | byte a byte con `07_leer_lote_salida.txt` |
| 413 ids, sin duplicados, 405 ok + 8 fuera, 2 escena_invalida con `grilla_incompleta` | `v01_estructura.py` | JSON del run |
| Las 400 son `neg_resto` de la población congelada; estrato 5.093, marco 5.055 | `v02_objetivos.py`, `v03_estrato.py`, `v03b_estrato_sin_oct.py` | mi propia derivación desde `poblacion_completa.json` (no la del autor) |
| Blob `2d57443d` del objetivos; 07/03/filas/envoltorio iguales al commit de disparo | `v05b_arbol_crlf_salida.txt` | `git rev-parse ffc1abc1b:<ruta>` |
| Árbol = `0e18e1053` (388 iguales tras CRLF, 0 distintos); `04_analizar.py` = `origin/s159-pruebas` | `v05_…`, `v05b_…` | `git ls-tree -r 0e18e1053` |
| Pipeline del commit base difiere de `origin/main` sólo en `fetch.py`, `run_pipeline.py` e `index.html` (2 líneas) | `v10_pipeline_base_vs_main_salida.txt` | `git diff --stat` |
| Veredicto con otra implementación y otra semilla: INDECIDIBLE; fronteras x = 0/7/8; controles de la regla | `v06_veredicto_independiente.py` | regla del §5 escrita por mí |
| Predicado idéntico con `index.html` de hoy (0 de 806 casos cambian) | `v07` §3 | `origin/main:frontend/index.html` |
| Sólo 2 de 390 `neg_resto` con npix > 0 en `fisica`; ninguno al borde del `inner` | `v07` §2 | `dist_centroide` recomputada |
| 7 rojos = trozos con `estado != ok`; código 2 explícito; 0 errores, 0 trazas, 0 K con error | `v01`, `v04_jobs_api`, `v09_probe_codigo`, `v11` | API de jobs + código `probe_portes.py:445-455` |
| 13 controles iguales a S159 en npix, VRP (1e-6), píxeles y gránulo; S159 `neg_resto` 38/38/36/0 | `v11` | JSON crudo de `run_39712862945` |
| 413 `.npz` abren, 13 capas, forma = `nativo.forma`, rebanadas y gránulo coherentes (salvo nombre 1399) | `v08_nativos.py` | contenido del `.npz` |
| Adenda 2 anterior al arranque del run (16:53:56 GMT < 18:26:31 GMT) | `v10_commits_salida.txt` | API del run |

## 7. SIN DATO

- La geolocalización MxD03 de cada gránulo (si viene corrida): nada en el lote la mide (lo dice el §10 del pre-registro);
  las dos publicaciones dependen de ella (VRC-05).
- Si las dos publicaciones son calor real sub-umbral (Láscar tiene fuente persistente, el píxel cae a 0,17 km del
  cráter) o artefacto (Llaima a cenit 63°): este lote no lo puede decidir y yo tampoco con lo que hay; pedirían otra
  pasada de la misma noche (A109) o el TIF de MIROVA.
- Costo del job `prueba` y de los trozos: no lo medí (fuera del encargo).

## 8. FUERA DE ALCANCE

El «gana» de S159 (ΔE_otros, las 149 filas congeladas), el diseño del censo MOD-D, la ablación MOD-E, y cualquier arreglo.
No modifiqué nada fuera de CARPETA; no hice commit, push ni despacho; usé 3 de 10 llamadas a la API de GitHub; sin
EARTHDATA_TOKEN. Disco al empezar: C: 40,9 GB, D: 9,6 GB libres.

---
Informe cerrado. Hora del servidor: Sat, 24 Oct 2026 18:59:39 GMT. HEAD del worktree al cerrar: 674de538c. sha256 de este archivo antes de esta linea: e0c6717a4c7d4c1372d58e6995561eb6efb633dfebf396e3e4726755c6459ea8
