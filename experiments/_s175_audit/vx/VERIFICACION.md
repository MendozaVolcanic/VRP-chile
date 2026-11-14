# VERIFICACION.md: verificador VX de cuatro hallazgos de la auditoría S175 (302, 108, 111, 256)

## 1. Encabezado

- Fecha y hora del servidor: empecé a las `Sun, 08 Nov 2026 04:03:09 GMT` y terminé las mediciones a las
  `Sun, 08 Nov 2026 04:18:54 GMT` (header `Date` de `gh api -i repos/MendozaVolcanic/VRP-chile`).
- Commit base de las afirmaciones: `752d348bc67190e53b610989877e2405d238a1bc` («NRT update Copahue 2026-11-07 03:38 UTC»).
  Todo lo que cito como «base» lo leí con `git show 752d348bc:<ruta>`. HEAD del worktree donde escribo:
  `d1367c6f063ddc38a77492f74099d8ad9f8330f3` (rama `claude/relaxed-almeida-d17378`, la de #955). `git diff --stat
  752d348bc HEAD -- pipeline/mirova_v750_codigo.py pipeline/process_modis.py pipeline/fetch.py docs/COLA_CAMPO.md` da
  vacío: esos cuatro archivos son idénticos en la base y en HEAD. `data/mirova_equivalent/` sí difiere (11 archivos),
  por eso los datos los saqué siempre de la base.
- Modelo: Claude Fable 5.1 (claude-fable-5-1). Esfuerzo real: SIN DATO (no veo el parámetro con que me lanzaron).
- CARPETA: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378\experiments\_s175_audit\vx\`
  Temporal: `C:\Users\nmend\vrp-temporales\s175_audit\vx\` (quedó en 4 KB: borré mi copia de los 11 JSON de la base,
  164 MB, al terminar las mediciones; se regenera con `vx_datos_base.py`).
- `caminos.md` escrito y sellado ANTES de abrir ningún archivo citado: sha256 del contenido
  `f729df02b3656b21d4dcfddd1c836b719116b32ae99fb14a1dbd7c0a5e4acbb1`, hora del servidor `04:04:38 GMT`. No se volvió a
  editar.
- Llamadas a la API de GitHub: 4 de las 5 permitidas (tres `gh api -i` para la hora del servidor y un
  `gh issue view 943 --json`, guardado en `C:\Users\nmend\vrp-temporales\s175_audit\vx\issue_943.json`).
- Disco: al empezar C: 5,3 GB y D: 4,9 GB libres. **Al terminar las mediciones (04:17 GMT) C: estaba en 2,3 GB (2,46 GB
  tras borrar mi copia), bajo el piso de 3 GB.** Mi temporal nunca pasó de 164 MB, así que el consumo fue de otro proceso.
  Según la regla me detuve ahí: no lancé nada más pesado que escribir este informe y el CSV. Al cerrar (04:22 GMT) C:
  había vuelto a 5,74 GB: fue una bajada transitoria de otro proceso (seguimiento S-08).
- Qué NO miré, para que mi silencio no se lea como «todo bien»: ningún `INFORME.md` ni `hallazgos.csv` de los frentes
  de S175 (por diseño del verificador); el tablero en navegador; la rama `loop/activo` salvo `docs/COLA_CAMPO.md`
  (`git diff` contra la base: idéntico); el PNG de MIROVA de Chillán 2026-10-18 06:48 (no bajé imágenes); la página de
  LAADS del decomiso (no tengo web en esta tarea). Sí abrí por accidente, con un `git grep`, cuatro líneas sueltas de
  `experiments/_s160_audit/f3/INFORME.md` (auditoría S160, no S175): las uso sólo como puntero a la fuente primaria
  del decomiso, que leí aparte.
- Instrumento: scripts míos en CARPETA (`vx_datos_base.py`, `vx_302_sensibilidad.py`), copias literales de los del
  auditor F5 con la salida redirigida a CARPETA (`rerun_i2_extension.py`, `rerun_i2_tif.py`); cada uno con su salida al
  lado (`*_salida.txt`, `*_out.json`, `rerun_*.out.txt`).

## 2. En una pantalla

1. **302 (F5): CONFIRMADO EN PARTE, gravedad 2.** Los números del auditor se reproducen bit a bit (714 de 715 aciertos con
   distancia de la tabla «compatibles»; el único «fuera» es Chillán V375 2026-10-18 06:48, por 0,10 km). Pero la frase
   «son el mismo foco o cúmulo» excede al instrumento: es una prueba escalar sobre un radio (A107). Con las distancias de
   MIROVA barajadas entre pares del mismo volcán y sensor, el 93 % sigue saliendo «mismo cúmulo» (nulo 91 a 95 %, 300
   barajados), y el caso Chillán cambia de lado con el origen (desde el vent: compatible) y con la tolerancia (a la mitad:
   15 «fuera», 5 protegidas de Chillán). Lo que sí está medido: ningún acierto es incompatible a más de 2 píxeles.
2. **108 (F0): CONFIRMADO, gravedad 2.** Las 10 filas de `docs/COLA_CAMPO.md` dicen «abierto» en la base (último commit
   `b941c8052`, 2026-10-22), en HEAD de #955 y en `loop/activo`; el issue #943 (abierto 2026-11-04T19:01:09Z, OPEN hoy)
   responde C-06. Imprecisión del título: el clasificador cubre 7 filas (C-02, C-03, C-06 a C-10), no «C-02 a C-10».
   Además C-05 tiene respuesta parcial que nadie anotó (la vía de producción usa el MxD03, ver 256).
3. **111 (F0): CONFIRMADO, gravedad 2.** Ningún script ni workflow de la base mide la fracción NRT de MODIS
   (`product_version` sólo en `scripts/reparar_product_version_modis_s133.py` y en `pipeline/`); `fetch.py` 212 a 218
   pide sólo `6.1` y `6.1NRT`; la fecha del decomiso (2026-09-30, aviso LAADS 199534 citado en S159) pasó y la 6.1 sigue
   produciendo (867 gránulos `061` desde el 2026-10-01). Noviembre: 14 de 143 records MODIS son NRT (9,8 %); medido con
   el campo y con el nombre del gránulo, cero discrepancias. Hallazgo propio: un record NRT del 2026-11-02 lleva 5 días
   sin subir a Standard (VX-04).
4. **256 (F3): CONFIRMADO, gravedad 2.** La memoria (`project_modis_geo_interp_offset.md` l. 3 y 11; `MEMORY.md` l. 114)
   dice que el MxD03 «se baja y se ignora» y «probe pendiente»; en la base `process_modis.py` l. 648 llama a
   `mirova_v750_codigo.py::leer_geo_mxd03` (l. 842) con `enable_modis_codigo_mirova: true` (perfil l. 38), y 120 de 120
   records MODIS de los 11 Tier A procesados desde el 2026-11-02T20:11:43Z llevan `via_codigo_mirova: true`. Sigue siendo
   cierto para la guardia K y para records que caigan a K (`sin_mxd03`, `sin_grilla`: 0 en la base).
5. Lo que decide #955: el hallazgo 302 sostiene su conclusión central sólo en su parte medible (compatibilidad radial);
   la identidad de foco no está medida y el instrumento casi no distingue (VX-01). Recomiendo reescribir esa frase antes
   del merge, no retirar el hallazgo.

## 3. Veredictos por afirmación

### 302 (frente F5). «Con la distancia de la tabla los aciertos por misma pasada son el mismo foco o cúmulo; una protegida al borde (Chillán V375 2026-10-18 06:48)»

**Veredicto: CONFIRMADO EN PARTE. Gravedad propia: 2.**

Qué parte se confirma (medido en esta sesión):
- `rerun_i2_extension.py` (copia literal de `experiments/_s175_audit/f5/i2_extension.py`, sólo cambia a dónde escribe)
  reproduce la salida del auditor **idéntica** (`diff` vacío; `i2_extension_out.json` igual). `rerun_i2_tif.py` sobre los 8
  TIF de `C:\Users\nmend\vrp-temporales\s175_audit\f5\tif_descargas\` también idéntica. Nota: el comando de mi tarea dice
  `if_descargas`; la carpeta real es `tif_descargas` (seguimiento S-05).
- Vara: los pares vienen de `i2_pares.csv` (881 pares, «recs del banco con lab pos (D-9 SN) y pub=1 (predicado del
  tablero), ventana 2026-06-11/2026-11-07», `f5_medir_out.json` I2.universo). Comprobé en la base que `TOL_S = VENTANA_S`
  (`scripts/banco_paridad.py` l. 78), `correr_node` en l. 156, `etiquetar` en l. 317 y `alerta_protegida` con lectura A y
  umbral en `scripts/clase_mirova.py` l. 65 a 75: es la vara del preámbulo. La copia `root` del auditor es la base
  (`volcanoes.yaml` idéntico sin CR; `NevadosDeChillan.json` igual como JSON, 6.910 records; los sha256 difieren sólo por
  CRLF).
- Con la distancia de la tabla (estrato CONS: 715 pares; de ellos 54 de clase iii, o sea nuestro punto a más de una
  tolerancia del radio de MIROVA), la prueba de extensión del auditor da **714 compatibles y 1 «fuera»**: Chillán
  VIIRS_NOAA21 2026-10-18 06:48, MIROVA 25,79 MW a 1,88 km, nuestros 8 píxeles entre 0,189 y 1,031 km de `mirova_center`,
  margen 1,88 - (1,031 + 0,75) = **0,099 km** (`vx_302_sensibilidad_salida.txt`, bloque 1 y 3). Es protegida (CONS,
  ≥1 MW). Eso es exactamente lo que dice el título.

Qué parte NO se sostiene o va más allá de lo medido:
- **«Son el mismo foco o cúmulo» no está medido** (VX-01). La prueba es `min(d) - tol <= d_MIROVA <= max(d) + tol` sobre
  distancias radiales a un punto: un píxel al otro lado del cráter a la misma distancia pasa igual (regla A107: «una cota
  de distancia escalar sirve para descartar, no para identificar el objeto»). Nulo por permutación (A110): barajando la
  distancia de MIROVA entre los pares CONS del mismo volcán y sensor, **el 93,2 % (mediana; mínimo 91,3 %, máximo
  95,0 %, 300 barajados) sale «mismo cúmulo»** contra 99,86 % observado. Por sensor: VIIRS 375 nulo 92,5 % contra
  99,8 % (n 560); VIIRS 750 nulo 95,0 % contra 100 % (n 120); MODIS nulo 100 % contra 100 % (n 35: en MODIS la prueba no
  puede fallar con tol 3 km). La prueba distingue poco; lo que sí dice es «ningún acierto es incompatible a más de dos
  píxeles», que es una cota, no una identidad.
- **El «al borde» de Chillán depende del origen y de la tolerancia** (VX-02). Desde el `vent` de `volcanoes.yaml`
  (-36,863, -71,377; a 0,385 km de `mirova_center`) el mismo caso queda **compatible** (margen -0,065 km) y en cambio
  salen «fuera» Lascar 2026-06-25 05:12, Chillán VIIRS_SNPP 2026-10-30 07:00 (protegida) y Cordón Caulle VIIRS_NOAA20
  2026-10-29 05:54 (protegida, 8,39 km). Con la mitad de la tolerancia desde `mirova_center`: 15 «fuera» entre los 54 iii,
  5 de ellos protegidas de Chillán (09-28, 10-10, 10-15, 10-16, 10-18). Con tolerancia 0 (rango estricto): 32 de 54 iii y
  **519 de 715 CONS** quedan fuera del rango de nuestros píxeles (VX-03). El propio control del auditor (`i2_tif.py`)
  reproduce la distancia de la tabla desde `mirova_center` en **5 de 8** TIF (`georef_reproduce_distancia` False en
  Lastarria 06-17, Cordón Caulle 07-06 y Láscar V375 06-25), o sea la vara «distancia desde mirova_center» tiene una
  incertidumbre del orden de 1 km, diez veces el margen de 0,099 km del «borde».
- Cota 2-D del caso Chillán (bloque 3): el alcance máximo de nuestro cúmulo V375 (píxel más lejano más una diagonal de
  píxel) es 1,56 km desde `mirova_center` y 1,73 km desde el vent; el píxel alertado de MIROVA está a 1,88 km. **No es
  ninguno de nuestros 8 píxeles ni un vecino inmediato**: MIROVA alertó al menos un píxel que nuestro V375 no, lo que
  cuadra con 25,79 MW de MIROVA contra 8,93 MW publicados (`f5_core_vrp_mw`) y 9,37 (`vrp_mw`). La fila V750 de la misma
  pasada (tabla: 22,85 MW a 2,70 km; nuestro V750 tiene un píxel de 1,34 MW a 2,29 km, ENE del cráter, lon -71,355) dice
  que hay calor a 2 a 3 km del centro esa noche. Que sea el mismo campo de lava o un foco distinto: SIN DATO sin la
  imagen. Dónde se ve: el tablero publica `summit` igual (inner 5 km); el operador ve la alerta en ambos, con magnitud
  distinta; no cambia la decisión de alerta de esa noche.
- Control positivo del instrumento: los 29 pares OCR de clase iii dan 25 «fuera» y 4 «mismo cúmulo» con la misma prueba
  (Tupungatito a 4,8 a 5,4 km, Cordón Caulle a 7,3 a 7,9 km): la prueba sí ve un foco a varios kilómetros. Pregunta 2:
  881 pares leídos, igual que el auditor; el nulo da un valor intermedio, no 0 ni 100 %.

Denominador y ventana: 881 pares (lab pos y pub=1), 715 con distancia de la tabla, 54 de clase iii, 2026-06-11 a
2026-11-07; records de la base 752d348bc (copia con sha256 igual a `git show`, `vx_datos_base_salida.txt`).

Cómo reproducirlo: `cd C:\Users\nmend\vrp-temporales\s175_audit\vx && python -I "...\experiments\_s175_audit\vx\vx_datos_base.py"`
(regenera la copia de la base) y luego `python -I "...\experiments\_s175_audit\vx\vx_302_sensibilidad.py"`; las copias del
auditor: `python -I rerun_i2_extension.py` y `python -I rerun_i2_tif.py C:\Users\nmend\vrp-temporales\s175_audit\f5\tif_descargas`
desde CARPETA.

### 108 (frente F0). «La cola de campo no se mantuvo desde S160: los 10 casos siguen abierto, también C-06, que ya tiene respuesta»

**Veredicto: CONFIRMADO. Gravedad propia: 2** (no toca ninguna detección; su costo es que la auditoría número treinta
vuelva a abrir lo que la S160 dejó por escrito y que un verificador use una cola envejecida como lista de pendientes).

Evidencia de esta sesión:
- `git log --format='%h %ad %s' --date=short 752d348bc -- docs/COLA_CAMPO.md`: dos commits, `fdc6642a0` y `b941c8052`,
  ambos 2026-10-22 (S160). Ninguno después.
- `git show 752d348bc:docs/COLA_CAMPO.md`: 21 líneas; filas C-01 a C-10 (10 filas) y las 10 terminan en `| abierto |`
  (C-06 en `| abierto (fecha fija) |`). El documento exige mantenerla: l. 5, TEXTO: «un ítem cerrado no se borra, se marca
  con la fecha y el resultado»; l. 8, TEXTO: «Dónde vive y quién la mantiene es decisión de Nicolás (plan §9, decisión 4)».
- C-06 (l. 17) pregunta si «el tablero o algún aviso muestra que Suomi NPP dejó de llegar» el 2026-11-02 después de las
  13:00 UTC. `gh issue view 943`: estado **OPEN**, creado `2026-11-04T19:01:09Z`, etiqueta `plataforma-cese`, título
  TEXTO: «Cese esperado confirmado: Suomi NPP dejó de producir records (informativo)»; cuerpo: `VIIRS_SNPP` y
  `VIIRS_SNPP_750` con 0 records en 72 h, último 2026-11-01 06:24, y «El tablero ya lo avisa al operador
  (frontend/cese_plataformas.js)». La pregunta de C-06 tiene respuesta y la fila no lo registra.
- Otros caminos de `caminos.md`: la copia no está atrasada (`git diff 752d348bc 395af8034 -- docs/COLA_CAMPO.md` vacío:
  `loop/activo` tiene el mismo archivo; `git diff 752d348bc HEAD` vacío: #955 tampoco lo actualiza, aunque
  `docs/AUDIT_S175.md` l. 184 ya propone «actualizar la cola de» C-04 y C-06). El clasificador del auditor
  (`f0_clasificador.py` l. 137 a 139) usa una regex anclada a inicio y fin de fila, no una subcadena.
- Imprecisión del título: el clasificador recorre `("C-02", "C-03", "C-06", "C-07", "C-08", "C-09", "C-10")` (7 filas) y
  C-10 además como `dec6`; C-04 y C-05 no están, y «filas C-02 a C-10» sugiere 9. Los 10 «abierto» los conté yo en el
  documento, no salen del script. No cambia el veredicto.
- Hallazgo adjunto: **C-05 también tiene respuesta parcial** («si la geolocalización MODIS se corre hacia el nadir»): desde
  S172 la vía de producción usa el MxD03 (ver 256), así que la pregunta vale sólo para la guardia K; tampoco está anotado.

Cómo reproducirlo: `git show 752d348bc:docs/COLA_CAMPO.md | grep -c '| abierto'` (da 10); `gh issue view 943 -R
MendozaVolcanic/VRP-chile --json state,createdAt,title`.

### 111 (frente F0). «243 abierto: nadie mide la fracción de records MODIS que llegan como NRT; la fecha de decomiso de la colección 6.1 ya pasó»

**Veredicto: CONFIRMADO. Gravedad propia: 2** (hoy el Standard llega; el riesgo es el día en que deje de llegar y nadie lo
vea; mientras, la vía MODIS corre sobre NRT en el 9,8 % de los records de noviembre, sin aviso).

Evidencia de esta sesión:
- «Nadie mide»: `git grep -n 'product_version' 752d348bc -- pipeline scripts .github frontend tests`: en `scripts/` sólo
  `scripts/reparar_product_version_modis_s133.py`; en `.github/` ninguno; en `frontend/` ninguno; `pipeline/store.py` l. 696
  a 697 lo usa sólo para el auto-upgrade NRT a Standard. `scripts/auto_audit_weekly.py` y `scripts/vigilar_plataformas.py`
  mencionan «NRT» sólo como el cron que puede caerse (l. 101, 338, 342; 78, 153, 187), no la colección. El predicado del
  auditor (`f0_clasificador.py` l. 87 a 89) busca `product_version` en `auto_audit_weekly.py` y `nrt-healthcheck.yml`;
  mi grep es más ancho y da lo mismo. Camino A89 («no aparece» con otro nombre): busqué `_NRT`, `is_nrt`, `nrt_fraction`,
  `fraccion.*nrt`, `proporcion.*nrt` en `scripts`, `pipeline/store.py` y `.github/workflows`: nada que cuente.
- `pipeline/fetch.py` base l. 212 a 218: `MOD021KM`/`MYD021KM` y `MOD03`/`MYD03` con `"version": "6.1"` y NRT `"6.1NRT"`;
  ninguna otra versión. El rango de líneas del hallazgo es correcto en la base.
- Fecha del decomiso: `docs/AUDIT_S160.md` l. 66, TEXTO: «MODIS 6.1 tiene decomiso anunciado (2026-09-30) y no
  ejecutado». Fuente primaria citada en el repo: `experiments/_s159/biblio_2026/INFORME.md` l. 66 a 69 (base), TEXTO: la 6.1
  «will remain available for the next six months before being decommissioned on September 30, 2026», atribuido al aviso
  LAADS 199534 del 17-mar-2026. No pude abrir la página de LAADS (sin web): la fecha es CONFIRMADA como cita del repo y
  SOSPECHA como hecho externo vigente (el mismo S159 l. 83 a 84 ya la marcaba SOSPECHA: «anunciada y no ejecutada»).
  Hoy es 2026-11-08: la fecha pasó. Y no se ejecutó: 867 records MODIS desde el 2026-10-01 con colección `061` en el nombre
  del gránulo (`f0_proporcion_nrt_modis_salida.txt`, reproducido por `vx_datos_base.py`).
- Re-corrida del instrumento del auditor por otro camino: `vx_datos_base.py` cuenta NRT con el campo `product_version` y
  con el nombre del gránulo (`.NRT.`), sobre los 14.953 records MODIS de los 11 Tier A en la base: **0 discrepancias**;
  2026-04 a 2026-10 0 % NRT (696 a 761 records por mes); **2026-11: 14 de 143 (9,8 %)**, concentrados el 11-06 (11 de 22)
  y el 11-07 (2 de 2), más 1 del 11-02. La copia `base_data` de F0 tiene sha256 igual a `git show` en los 11 archivos.
  Control positivo: existen records con `.NRT.` en el nombre, y el campo los etiqueta `nrt`. Pregunta 2: la columna
  `sin_campo`/`sin_granule` está vacía en los 14.953.
- Advertencia del propio instrumento: el `f0_proporcion_nrt_modis.py` emite `SyntaxWarning: invalid escape sequence '\{'`
  (l. 12, `f"{D}\{v}.json"`); corre igual (seguimiento S-06).

Cómo reproducirlo: `python -I "...\experiments\_s175_audit\vx\vx_datos_base.py"` (salida `vx_datos_base_salida.txt`);
`git show 752d348bc:pipeline/fetch.py | sed -n '212,218p'`; `git grep -n product_version 752d348bc -- scripts .github`.

### 256 (frente F3). «La memoria del agente dice que el MxD03 se baja y se ignora; la vía de producción lo usa desde 2026-11-02»

**Veredicto: CONFIRMADO. Gravedad propia: 2** (no toca detección; engaña al agente que audite la posición MODIS: con la
memoria tal cual, atribuiría a `_interp_geo` un corrimiento que la vía ya no produce, o dejaría de buscar el que la vía sí
pueda producir).

Evidencia de esta sesión:
- Memoria (fuera del repo, archivo de hoy, modificado 2026-10-15 09:27 -03):
  `C:\Users\nmend\.claude\projects\C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile\memory\project_modis_geo_interp_offset.md`
  l. 3 (description), TEXTO: «MxD03 se baja y se ignora»; l. 11, TEXTO: «El pipeline YA baja MxD03 (geolocalizacion de 1 km
  corregida por terreno) y `calculate_vrp` la ignora (`process_modis.py:470`)»; l. 17, TEXTO: «El arreglo propuesto (leer
  MxD03 detras de un flag, A45) espera el probe contra MxD03 en GitHub Actions». `MEMORY.md` l. 114, TEXTO: «MxD03 se baja
  y se ignora; probe pendiente». Ninguna marca S172/S174 en el archivo (grep de `S172`, `S174`, `vía`, `via_codigo`: 0).
- Código en la base: `pipeline/profiles/mirova_equivalent.yaml` l. 38 `enable_modis_codigo_mirova: true`;
  `pipeline/process_modis.py` l. 637 a 662: con el flag encendido, si el volcán tiene grilla de MIROVA y hay `geo_path`,
  l. 648 `_lat, _lon, _ang = _MV.leer_geo_mxd03(geo_path)` y l. 650 a 662 `calcular_vrp_granulo(...)` devuelve el record de
  la vía; si no, `_via_marca` = `sin_grilla` (l. 643), `sin_mxd03` (l. 645) o `geo_distinta` (l. 652) y sigue K.
  `pipeline/mirova_v750_codigo.py` l. 842 `def leer_geo_mxd03(ruta)`; l. 845, TEXTO: «POR QUÉ el MxD03 y no la grilla de
  5 km del MxD021KM que interpola producción: el censo MOD-D corrió con el MxD03». La función existe desde `c4efdc78c`
  (2026-10-27, S164, APAGADA); el flag pasó a `true` en `33f889bc5` (2026-11-02 10:36 -03) y entró a main con el merge de
  #934, `499935c37` (2026-11-02 14:18 -03).
- Datos en la base (`vx_datos_base_salida.txt`): de 14.953 records MODIS de los 11 Tier A, `via_codigo_mirova` es
  `True` en **120** y está ausente en 14.833; **0** con `sin_grilla`, `sin_mxd03` o `geo_distinta`. Primer `True`:
  datetime 2026-11-02 01:15 UTC (Puyehue Cordón Caulle), `processed_utc` mínimo `2026-11-02T20:11:43Z`; último
  2026-11-07 01:15 (Copahue). «Desde 2026-11-02» es correcto en la fecha de los datos y en la del merge. El único record
  MODIS del 11-02 en adelante sin la marca es Planchón-Peteroa MODIS_TERRA 2026-11-02 01:15, procesado a las 02:28Z,
  antes del merge (y es NRT, ver VX-04).
- Caminos de `caminos.md` cerrados: (1) el alcance de «se ignora» es absoluto en la memoria («calculate_vrp la ignora»),
  no acotado a K; (2) la vía es condicional, pero en la base la condición se cumple en 120 de 120; para la guardia K
  (`pipeline/profiles/guardia_k_modis.yaml`) y para records que caigan a K la frase de la memoria sigue siendo verdad: el
  hallazgo debería decirlo; (3) l. 842 no drifteó (base = HEAD); (5) no hay marca de rebaja en ninguna línea del archivo
  ni en `MEMORY.md` l. 114; (7) la memoria no está en el repo: se verifica contra el archivo de hoy, no contra un commit.
- Lo que la memoria tiene además de viejo: «probe pendiente» (`MEMORY.md` l. 114) cuando el propio cuerpo l. 15 ya dice
  «Probe contra MxD03 (run 38733452917, PR #828, verificado)»; y la cita `process_modis.py:470` no la comprobé contra el
  código de hoy (SOSPECHA de drift, regla A101).
- Pregunta 1: si la vía no usara el MxD03, no habría `leer_geo_mxd03` en el camino de l. 648, o los records no llevarían
  la marca; pregunta 2: el control positivo son los 14.833 records anteriores sin la llave (K no la escribe).

Cómo reproducirlo: `grep -n 'se ignora' "<memoria>\project_modis_geo_interp_offset.md"`; `git show
752d348bc:pipeline/process_modis.py | sed -n '637,662p'`; `python -I "...\vx\vx_datos_base.py"` (bloque «(256)»).

## 4. Hallazgos propios (VX-01 en adelante)

### VX-01
- TÍTULO: La prueba de «extensión» de F5 (hallazgo 302) casi no distingue: con las distancias de MIROVA barajadas entre pares del mismo volcán y sensor, el 93 % igual sale «mismo cúmulo».
- SCRIPT:SALIDA: `experiments\_s175_audit\vx\vx_302_sensibilidad.py` → `vx_302_sensibilidad_salida.txt` (bloque 2) y `vx_302_sensibilidad_out.json` (`nulo_permutacion`); instrumento auditado: `experiments\_s175_audit\f5\i2_extension.py` l. 33 a 34.
- QUÉ PASA: las anomalías de estos volcanes se apiñan a menos de 1 a 2 km del centro, así que casi cualquier radio de MIROVA cae dentro del rango radial de casi cualquier pasada nuestra con dos píxeles de tolerancia; la prueba mide esa concentración, no la identidad del foco (A107). Observado 714 de 715 (99,86 %); nulo mediana 93,15 % (91,3 a 95,0 %, 300 barajados; VIIRS 375 92,5 %, VIIRS 750 95,0 %, MODIS 100 %).
- CÓMO SE VE EN EL DASHBOARD: invisible (es una conclusión de auditoría, no un dato publicado).
- CÓMO REPRODUCIRLO: `python -I "...\vx\vx_datos_base.py" && python -I "...\vx\vx_302_sensibilidad.py"` desde `C:\Users\nmend\vrp-temporales\s175_audit\vx`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2 (puede torcer la conclusión central de AUDIT_S175, no una alerta).

### VX-02
- TÍTULO: El «al borde» de Chillán V375 2026-10-18 06:48 cambia de lado con el origen de la distancia y con la tolerancia; la vara «distancia desde mirova_center» reproduce la tabla en 5 de 8 TIF.
- SCRIPT:SALIDA: `vx_302_sensibilidad_salida.txt` bloques 1 y 3; `experiments\_s175_audit\f5\i2_tif.out.txt` (campo `georef_reproduce_distancia`, 5 True de 8).
- QUÉ PASA: el margen es 0,099 km desde `mirova_center` y -0,065 km desde el `vent` (0,385 km aparte); con la mitad de la tolerancia salen «fuera» 15 de 54 iii (5 protegidas de Chillán); con tolerancia 0, 519 de 715 CONS. Un veredicto que se decide en 0,1 km sobre una vara con incertidumbre de ~1 km no es un veredicto.
- CÓMO SE VE EN EL DASHBOARD: invisible; esa noche el tablero publica `summit` (inner 5 km) y 8,93 MW contra 25,79 de MIROVA.
- CÓMO REPRODUCIRLO: igual que VX-01; ver «fuera:» bajo `vent|tol_x1.0|iii` y `mirova_center|tol_x0.5|iii`.
- CONFIANZA: CONFIRMADO (la sensibilidad); SOSPECHA (qué origen usa MIROVA: 5 de 8 TIF no bastan para fijarlo).
- GRAVEDAD: 2.

### VX-03
- TÍTULO: Sin tolerancia, la distancia de la tabla de MIROVA cae fuera del rango radial de nuestros píxeles en 519 de 715 aciertos: hay un desfase sistemático entre su distancia y la nuestra que la tolerancia de dos píxeles tapa.
- SCRIPT:SALIDA: `vx_302_sensibilidad_salida.txt`, `mirova_center|tol_x0.0|todos_CONS: {'fuera': 519, 'mismo_cumulo': 196}` (desde el vent 546 de 715).
- QUÉ PASA: puede ser cuantización de la distancia de MIROVA a su celda (D15), otro origen, o que MIROVA mide al píxel alertado más lejano o más caliente y nosotros al centroide; no lo perseguí (fuera de mi eje).
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: igual que VX-01.
- CONFIANZA: SOSPECHA (el número está medido; la causa no).
- GRAVEDAD: 2.

### VX-04
- TÍTULO: Un record MODIS NRT del 2026-11-02 01:15 (Planchón-Peteroa, Terra) lleva 5 días en la base sin subir a Standard y quedó procesado por K antes del merge de la vía: hoy es el único MODIS de la semana con «detector efectivo» K.
- SCRIPT:SALIDA: `vx_datos_base_salida.txt`, línea «records nrt con fecha anterior al 2026-11-04»: `MOD021KM.A2026306.0115.061.2026306020645.NRT.hdf`, `processed_utc 2026-11-02T02:28:24Z`, `via_codigo_mirova` ausente. `pipeline/store.py` base l. 695 a 702 (auto-upgrade sólo cuando llega un record Standard de la misma clave).
- QUÉ PASA: el auto-upgrade depende de que el cron vuelva a procesar esa pasada cuando LAADS publique el Standard («typically 3-5 days», comentario l. 692 a 693); si la ventana del cron ya no cubre la pasada, el record queda NRT y K para siempre, en silencio. Es el mecanismo exacto que el hallazgo 243 teme para el decomiso, ya ocurriendo en pequeño.
- CÓMO SE VE EN EL DASHBOARD: el punto de Planchón-Peteroa de esa noche existe (K, NRT); nada lo distingue.
- CÓMO REPRODUCIRLO: `python -I "...\vx\vx_datos_base.py"`; buscar `nrt_viejos` en `vx_datos_base_out.json`.
- CONFIANZA: CONFIRMADO el hecho; SOSPECHA la causa (no leí qué ventana de fechas pide `nrt.yml`; sólo vi `--start/--end` opcionales en l. 199 a 200 y 240 a 241).
- GRAVEDAD: 2.

### VX-05
- TÍTULO: Ningún record MODIS declara qué geolocalización se usó (MxD03 o `_interp_geo`): la llave `geo_fuente` de `posicion_de_calculo` no se persiste y la vía sólo deja `via_codigo_mirova`.
- SCRIPT:SALIDA: `vx_datos_base_salida.txt`, «llaves con 'geo' o 'mxd03' en los records MODIS: {}» (14.953 records); `pipeline/process_modis.py` base l. 531 a 537 (devuelve `geo_fuente`) y l. 1767 (sólo se escribe `via_codigo_mirova`).
- QUÉ PASA: para auditar la posición (A61) hay que inferir la fuente desde la marca de vía y la fecha; un record K con `enable_modis_geo_mxd03: true` en otro perfil sería indistinguible.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python -I "...\vx\vx_datos_base.py"` (línea `llaves_geo`).
- CONFIANZA: CONFIRMADO (ausencia en los datos; la lectura de l. 1767 es de la base).
- GRAVEDAD: 1.

## 5. SEGUIMIENTOS (fuera de mi eje, dejados reproducibles)

- S-01: `docs/COLA_CAMPO.md` C-05 tiene respuesta parcial no anotada (la vía MODIS de producción usa el MxD03; la pregunta sigue viva sólo para la guardia K). Evidencia: 256. Confianza CONFIRMADO.
- S-02: `docs/AUDIT_S175.md` l. 184 (HEAD) propone actualizar la cola para C-04 y C-06 pero el PR #955 no toca `docs/COLA_CAMPO.md` (`git diff --stat 752d348bc HEAD -- docs/COLA_CAMPO.md` vacío). Confianza CONFIRMADO.
- S-03: memoria `project_modis_geo_interp_offset.md` l. 11 cita `process_modis.py:470` para «calculate_vrp la ignora»: posible drift de cita (A101); no comprobado. SOSPECHA.
- S-04: `MEMORY.md` l. 114 dice «probe pendiente» y el cuerpo de la nota l. 15 dice que el probe se hizo (PR #828). CONFIRMADO (texto contra texto).
- S-05: el comando de reproducción del hallazgo 302 en mi tarea termina en `C:\Users\nmend\vrp-temporales\s175_audit\f5 if_descargas`; la carpeta real es `...\f5\tif_descargas` (8 TIF). Tal como está escrito, el comando no corre. CONFIRMADO (`ls`).
- S-06: `experiments\_s175_audit\f0\f0_proporcion_nrt_modis.py` l. 12 emite `SyntaxWarning: invalid escape sequence '\{'`; corre igual. CONFIRMADO.
- S-07: `f0_clasificador.py` l. 137 cubre 7 de las 10 filas de la cola; el título del hallazgo 108 dice «C-02 a C-10». CONFIRMADO.
- S-08: C: bajó de 5,3 a 2,3 GB libres durante esta sesión sin que mi temporal pasara de 164 MB: algo más está escribiendo en C:. SIN DATO de qué.

## 6. VERIFICADO LIMPIO (qué miré, está sano, y contra qué vara)

- Copias de los auditores = base: `C:\Users\nmend\vrp-temporales\s175_audit\f0\base_data\*.json` sha256 igual a `git show 752d348bc:data/mirova_equivalent/<v>.json` en los 11 Tier A; `...\f5\root\volcanoes.yaml` igual a la base sin CR; `...\f5\root\data\mirova_equivalent\NevadosDeChillan.json` igual como JSON (6.910 records). Vara: `git show` de la base.
- Referencia de los insumos: `snapshot_consolidado_base.csv` sha256 `f833bfde...`, `snapshot_ocr_base.csv` `577a336e...`, `latest_consolidado_base.csv` `dee76837...`: coinciden con el preámbulo.
- Scripts del auditor F5 re-corridos desde copias en CARPETA: `i2_extension` y `i2_tif` salida y JSON idénticos.
- Vara del preámbulo en la base: `scripts/banco_paridad.py` l. 78 `TOL_S = VENTANA_S`, l. 156 `def correr_node`, l. 317 `def etiquetar`; `scripts/clase_mirova.py` l. 65 `alerta_protegida` lectura A.
- `pipeline/fetch.py` l. 212 a 218 sólo `6.1`/`6.1NRT` (vara: el texto de la base).
- `pipeline/mirova_v750_codigo.py`, `process_modis.py`, `fetch.py`, `docs/COLA_CAMPO.md`: idénticos entre base y HEAD de #955.
- Issue #943 OPEN con el contenido que C-06 pide (vara: la API, no la memoria).

## 7. SIN DATO

- La imagen de MIROVA de Chillán 2026-10-18 06:48 (PNG `imagenes_satelitales/Nevados_de_Chillan/2026-10-18/06-48-02_..._VIIRS375_Latest.png` del scraper): no la bajé; sin ella, «mismo campo de lava o foco distinto» no se decide.
- La página LAADS 199534 (fecha del decomiso de la 6.1 y si se postergó): sin web en esta tarea.
- La causa de VX-04 (ventana del cron NRT).
- El esfuerzo con que corrí.
- Qué origen usa MIROVA para `Distancia_km` (5 de 8 TIF reproducen `mirova_center`; no alcanza).

## 8. FUERA DE ALCANCE

- Los INFORME.md y hallazgos.csv de los frentes; la decisión de qué hacer con la cola y con la memoria (A45, Nicolás); arreglar
  el instrumento de F5 (es un seguimiento, no un arreglo mío); el resto de los hallazgos de S175.

## Archivos en CARPETA

`caminos.md` (sellado), `VERIFICACION.md`, `hallazgos.csv`, `vx_datos_base.py` + `vx_datos_base_salida.txt` +
`vx_datos_base_out.json`, `vx_302_sensibilidad.py` + `vx_302_sensibilidad_salida.txt` + `vx_302_sensibilidad_out.json`,
`rerun_i2_extension.py` + `rerun_i2_extension.out.txt` + `i2_extension_out.json`, `rerun_i2_tif.py` + `rerun_i2_tif.out.txt`
+ `i2_tif_out.json`. Temporal: `C:\Users\nmend\vrp-temporales\s175_audit\vx\issue_943.json`.
