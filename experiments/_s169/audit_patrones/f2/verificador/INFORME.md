# Verificador F2 (MOD-D fase 4, candado): veredictos sobre P2-01 a P2-12

## 1. Encabezado

- Fecha y hora: 2026-10-30 04:03 a 04:30 UTC, reloj local del sistema (`date -u`). La tarea prohíbe red, así que no
  pude pedir la hora del servidor de GitHub (A86): la marco como hora local.
- Commit medido: `743e89c488d2ffaa4d9cf2baaa04e3fb4d99a026` (rama `claude/s168-modd-f4-sello`), árbol extraído en
  `D:/vrp-trabajo/temporales/s169_audit_patrones/f2_modis/arbol/`. Los archivos que faltaban en el árbol los saqué con
  `git -c core.autocrlf=false show 743e89c48:<ruta>`. Vara: el pre-registro sellado
  (`3768e9431`, tag `s168-modd-f4-sellado`); comprobé que la copia del árbol es idéntica byte a byte, salvo los fines
  de línea (`diff` vacío).
- Modelo: Claude Opus 5.5, esfuerzo bajo, por orden del orquestador.
- CARPETA: `D:\vrp-trabajo\temporales\s169_audit_patrones\f2_verificador\` (scripts `m*.py` con su salida `m*_salida.txt`
  al lado; `caminos.md` sellado antes de abrir los archivos citados, sha256 `c2d0982b…`, 04:04:16 UTC).
- Lo que NO miré: el informe del auditor, su CSV y sus scripts (no los abrí en ningún momento); la carpeta
  `s168_mut` ni la corrida de mutaciones en curso; `probe_etiquetas.py` más allá de `publica`; el comportamiento real
  de `earthaccess.download` frente a un ConnectTimeout (versión sin fijar, sin red); la frecuencia real de las caídas
  de host de LAADS; el número B de bloques que tendrá P2 en la corrida real. No corrí el arnés, el ensayo en seco ni
  el medidor de mutaciones. Mi silencio sobre el resto del arnés no quiere decir «todo bien».

## 2. En una pantalla

- P2-01 CONFIRMADO, gravedad 3. Lo reproduje sin red sobre el `fetch.py` y el `bajar_por_nombre` reales: un solo
  ConnectTimeout en la primera descarga, con el host ya recuperado, hace perder 6 de 6 gránulos, con 400 s de espera
  por gránulo; si se resetea el breaker por gránulo, bajan 5 de 6. El peor caso deja entre 67 y 95 pasadas por parte
  sin fila. Se arregla sólo en `probe_f4.py` y conviene hacerlo antes del tag.
- P2-03 CONFIRMADO, gravedad 3. Medido en copia: un `evaluar_f4.py` cambiado para dar siempre PROPONER ADOPCIÓN, con
  el manifiesto regenerado, pasa `comprobar` en OK. Ninguna pieza de la lectura compara contra el tag el
  `sha256_evaluar_f4` que trae cada cabecera. P2-02 CONFIRMADO, gravedad 3. Arreglar los dos antes del tag, en
  `externos_f4.py` (sólo en experiments/).
- P2-05 (variante de VC169-01, que se funde con él), P2-06, P2-07 y P2-08: CONFIRMADOS, gravedad 2. P2-04, P2-09,
  P2-10 y P2-11: CONFIRMADOS EN PARTE, gravedad 1 o 2. En P2-10 la base es de 0 de 5.709 pasadas; en P2-11, el MxD03
  que no se puede abrir da error y no «fuera». P2-12: CONFIRMADO EN PARTE, gravedad 1.
- Ningún arreglo toca `pipeline/`. Hallazgo nuevo VF2-01: `evaluar_f4.py` del árbol (`8a1edc14…`) no es el sha256
  `c01e0824…` del §13 sellado. Queda como seguimiento: sospecho que es el cambio VS-01 a VS-08 que las mutaciones de
  hoy vuelven a certificar.

## 3. Veredictos

Formato: TÍTULO, ARCHIVO:LÍNEA, QUÉ PASA, CÓMO SE VE EN EL DASHBOARD, CÓMO REPRODUCIRLO, CONFIANZA, GRAVEDAD (la mía),
y además VEREDICTO, (a) antes del tag o declarado, (b) toca `pipeline/` o sólo el arnés.

### P2-01. Breaker de descarga pegado: un ConnectTimeout envenena la parte entera
- ARCHIVO:LÍNEA: `experiments/_s166_modd_f4/probe_f4.py:413-443` (`bajar_por_nombre`: 4 intentos con
  `time.sleep(espera * (intento + 1))`, o sea 20+40+60+80 = 200 s por archivo), `:549-550` (L1B y MxD03 de cada gránulo,
  los dos siempre), `:551-557` (fila `no_bajado`); `pipeline/fetch.py:950` (`_DOWN_DOWNLOAD_HOSTS`, estado de módulo),
  `:1072-1076` (si los hosts están en el conjunto, `raise RuntimeError("download host(s) down this run")` al
  instante), `:413-423` (`reset_transient_breakers`, que sólo llama `scripts/run_pipeline.py:665`; el arnés no la llama:
  `grep reset_transient experiments/_s166_modd_f4/*.py` da 0).
- QUÉ PASA: si NASA corta la conexión una vez (en `fetch.py:1100-1121` basta un ConnectTimeout con la sonda TCP en
  falso, o cuatro seguidos en el mismo gránulo), el host queda marcado como caído para todo el proceso, y en el arnés
  el proceso es la parte entera. Desde ahí cada gránulo gasta 400 s de espera y no baja nada, aunque el host ya haya
  vuelto. También se pierde el gránulo donde ocurrió la caída: sus reintentos chocan contra el breaker. Y con una
  excepción nunca se llega al respaldo «vigente 6.1» de las l. 433-439.
- Medición (m01b_simular_breaker.py, sin red; earthaccess falso que lanza `requests.ConnectTimeout` sólo en la
  primera descarga): con el arnés tal cual bajan 0 de 6 gránulos y hay 2.400 s de espera, 400 s por gránulo. Control
  positivo, con `reset_transient_breakers()` antes de cada gránulo: bajan 5 de 6 y la espera es de 400 s. Salida:
  `m01b_salida.txt`. Pregunta 1: si el breaker no estuviera pegado, los gránulos 2 a 6 bajarían, y el control lo
  muestra. Pregunta 2: el control positivo sale distinto, así que el instrumento está vivo.
- Tamaño (m01_granulos_por_parte.py, población de 5.709 pasadas, 24 partes de 53 o 54 grupos L1B+MxD03): en el peor
  caso (la caída en el primer gránulo) el timeout de 240 min (`probe-s168-modd-f4.yml:161`) alcanza para unos 36
  gránulos. Quedan entre **67 y 95 pasadas por parte sin fila** (todas las partes: 67 a 95), y el resto sale con fila
  `no_bajado`. Las filas `no_bajado` se escriben sin `flush` (`probe_f4.py:553`; el `flush` está sólo en la l. 573),
  así que al matar el job se pierde la cola del búfer y no se escribe el `pie`. El «~70» del auditor queda dentro del
  rango.
- Consecuencia en el evaluador: las pasadas que faltan quedan en `faltan` y las `no_bajado` en
  `falla_arnes_no_bajado`, y las dos dejan la cobertura en INDECIDIBLE (`evaluar_f4.py:599-618`). No tuerce el
  veredicto: lo deja INDECIDIBLE después de gastar hasta 8 runners por 4 h. La procedencia exige cada parte una sola
  vez (`externos_f4.py:69-73`), así que la salida es repetir la tanda entera.
- CÓMO SE VE EN EL DASHBOARD: no se ve (es el A/B, no el NRT).
- CÓMO REPRODUCIRLO: `python -I D:/vrp-trabajo/temporales/s169_audit_patrones/f2_verificador/m01b_simular_breaker.py`.
- CONFIANZA: CONFIRMADO, por código y por simulación. Lo que no verifiqué es si la versión de earthaccess sin fijar
  propaga el ConnectTimeout (SOSPECHA a favor: el comentario de `fetch.py:942-949` documenta el incidente S102 con
  esa propagación).
- GRAVEDAD: 3.
- (a) Antes del tag. Es barato, y cada tanda de 4 h queda expuesta a un solo corte de NASA. (b) Sólo el arnés. **Sí
  se puede arreglar sólo en `probe_f4.py`**: `pipeline.fetch.reset_transient_breakers()` es pública y existe para esto
  (su docstring dice que `run_pipeline` la llama por fecha). Lo que importa es dónde se llama. Si se llama por
  gránulo, se pierde el gránulo de la caída; si se llama antes de cada `descargar(...)` dentro del bucle de intentos,
  un corte pasajero no cuesta ni ese gránulo. Con un host caído de verdad, en cambio, resetear en cada intento cuesta
  un ConnectTimeout (60 a 183 s según `fetch.py:943`) por intento y por archivo, más que hoy. Hay que acompañarlo con
  un tope: por ejemplo, reconocer el `RuntimeError` del breaker y no dormir, o dar la parte por terminada con filas
  `no_bajado` explícitas (y con `flush`) después de N gránulos seguidos sin bajar. Esa es una decisión de política del
  orquestador. Cualquiera de las dos cambia `probe_f4.py`, así que obliga a volver a correr `probar_probe_f4.py` y a
  regenerar el manifiesto antes del tag. `fetch.py` no se toca.

### P2-02. El evaluador no ata la población, la identidad ni los externos, y el resultado sale sin procedencia
- ARCHIVO:LÍNEA: `evaluar_f4.py:765-772` (lee `--poblacion`, `--identidad` y `--externos` por ruta, sin sha256);
  `:766` (`filas, _cab = cargar(a.art)`: descarta las cabeceras); `:784-788` (escribe `res` sin commit, sin sha de los
  insumos, sin versiones).
- QUÉ PASA: la cifra de la decisión sale de tres archivos que el evaluador no reconoce. `externos_f4.py:94-100` compara
  la población de **su** `--poblacion` (por omisión `AQUI/poblacion_f4.json`) con el `sha256_poblacion` de las
  cabeceras, pero el evaluador puede recibir otra ruta. `identidad.json` no lo ata nadie: guarda `poblacion` y `art`
  (`identidad_f4.py:269`) y nadie los lee. Una identidad de otra corrida completa, con las 5.321 iguales, pasaría.
- CÓMO SE VE EN EL DASHBOARD: no se ve.
- CÓMO REPRODUCIRLO: `grep -n "_cab\|sha256" experiments/_s166_modd_f4/evaluar_f4.py` (sin uso de `_cab` ni de sha
  de insumos); `grep -rn "\"poblacion\"\|\"art\"" experiments/_s166_modd_f4/evaluar_f4.py experiments/_s166_modd_f4/externos_f4.py`
  (nadie lee lo que registra la identidad).
- CONFIANZA: CONFIRMADO (leído). No medí una corrida con una identidad cambiada.
- GRAVEDAD: 3. Para torcer el resultado hace falta un error de operación, pero un tercero no puede saber con qué
  insumos se llegó al veredicto.
- (a) Antes del tag. (b) Sólo el arnés, y se puede hacer sin tocar el evaluador: `res["controles"]` copia cada externo
  completo (`evaluar_f4.py:694-695`), así que si `externos_f4.armar` agrega los sha256 LF de la población y de la
  identidad que se le pasan, el commit del checkout de la lectura y las versiones, todo eso queda dentro de
  `resultado_f4.json`. Que además decida (por ejemplo, la procedencia en rojo si `identidad.json` no apunta al mismo
  `art`) se puede meter en una clave que ya existe.

### P2-03. El manifiesto y la procedencia no atan la LECTURA al commit del tag
- ARCHIVO:LÍNEA: `manifiesto_candado_f4.py:89-93` (`escribir` deja siempre `tag` y `commit_tag` en `None`; el
  comentario dice que «se llenan al regenerar justo antes del tag», pero el código no lo hace); `:98-114` (`comprobar`
  compara el checkout contra el manifiesto **del mismo checkout**, nunca contra `git show <tag>:…`);
  `externos_f4.py:112-124`. Del tag sólo usa el commit, para las cabeceras, y el `index.html`. Las cabeceras traen
  `sha256_evaluar_f4` y `sha256_probe_f4` (`probe_f4.py:493`), pero nadie las compara: grep, 0 lectores.
- QUÉ PASA: si después del tag alguien cambia `evaluar_f4.py` (por ejemplo, un arreglo de buena fe al ver el
  resultado) y regenera el manifiesto con `--escribir`, la lectura sale OK. La docstring del manifiesto
  (`manifiesto_candado_f4.py:5-9`) dice que existe justo para ver eso.
- Medición (m03_manifiesto_no_atado.py, copia completa de los 64 archivos del manifiesto en `m03_raiz/`): (0) la copia
  intacta da OK; (1) control positivo, con el evaluador cambiado a `return 'PROPONER ADOPCIÓN'` y sin regenerar, da
  INDECIDIBLE con `distintos = [evaluar_f4.py]`; (2) el mismo cambio con el manifiesto regenerado da **OK**. Salida:
  `m03_salida.txt`.
- CÓMO SE VE EN EL DASHBOARD: no se ve.
- CÓMO REPRODUCIRLO: `python -I .../f2_verificador/m03_manifiesto_no_atado.py`.
- CONFIANZA: CONFIRMADO, medido.
- GRAVEDAD: 3. Si alguien cambia el evaluador puede torcer el veredicto sin dejar rastro, aunque hace falta que lo
  cambie.
- (a) Antes del tag: son dos líneas en `externos_f4.armar`. Una compara los bytes LF del `MANIFIESTO_CANDADO_F4.json`
  local con los de `git show <tag>:experiments/_s166_modd_f4/MANIFIESTO_CANDADO_F4.json`; la otra, el
  `sha256_evaluar_f4` de cada cabecera con el sha256 LF del `evaluar_f4.py` local. Cualquier diferencia pone
  `manifiesto` o `procedencia` en INDECIDIBLE. (b) Sólo el arnés.

### P2-04. La identidad compara una clase recalculada en local; 8 indicadores de coherencia no deciden
- ARCHIVO:LÍNEA: `identidad_f4.py:183-187` (`vr = via(...)` sobre la grilla del runner, corrida **aquí**; `dc_r` sale de
  `vr` porque el npz de `probe_f4.py` no guarda `distance_class`); `:214-216` (`captura_coherente`); `:251-253`
  (`igual()` decide con 4 campos); `evaluar_f4.py:455-482` (`control_identidad` lee sólo `mismo_granulo`,
  `misma_mascara`, `dvrp` y `misma_clase`). Los 8 que no deciden: `captura_coherente`, `box_igual`, `pos_crater_igual`,
  `grilla_igual_float32`, `geom_distinta`, `n_nan_distinto`, `v_slim_vrp_igual`, `v_slim_dc_igual`. Los conté y son 8.
- QUÉ PASA: la máscara y el VRP del runner sí se comparan, tal como salen del npz. La clase no: en los dos lados de la
  comparación la calcula el código local. Si la clase que dio el runner no fuera la que da la re-corrida local, nadie
  lo vería, porque `captura_coherente` y `v_slim_dc_igual` sólo informan.
- Por qué es sólo EN PARTE: `control_posicion` (`evaluar_f4.py:485-510`) amarra la clase del record de V del runner
  (`v_slim.distance_class`) a `clase_dc(distancia radiante del arnés, inner)`. Lo único que no queda amarrado es el
  paso entre la clase del runner y la de la re-corrida local, y ese paso se abre de verdad cuando el código de la
  lectura no es el del tag (P2-03).
- CÓMO SE VE EN EL DASHBOARD: no se ve.
- CÓMO REPRODUCIRLO: leer las líneas citadas; `grep -n "captura_coherente\|v_slim_dc_igual" experiments/_s166_modd_f4/evaluar_f4.py`
  da 0.
- CONFIANZA: CONFIRMADO EN PARTE: el mecanismo es real, pero el daño posible queda acotado por `control_posicion`.
- GRAVEDAD: 2.
- (a) Puede quedar declarado si P2-03 se arregla. (b) Sólo el arnés: o `guardar_npz` de `probe_f4.py` guarda
  `distance_class`, o `externos_f4` cuenta las `captura_coherente False` y las lleva a un externo que ya existe.

### P2-05. El ensayo en seco escribe la población en una sola línea y no puede ver el P-A de CRLF
- ARCHIVO:LÍNEA: `ensayo_en_seco_f4.py:130` (`write_text(json.dumps(pob))`, sin saltos de línea), `:135` (fabrica
  `externos_referencia.json` con `sha256_bytes` de esos bytes, sin pasar por `reetiquetado_f4.py`);
  `reetiquetado_f4.py:171` (`PF.sha256(a.poblacion)`, crudo: `poblacion_f4.py:95`, `lf=False` por omisión).
- Medición (m05_crlf.py): la población real tiene 226.696 líneas y está en LF en el árbol (sha `e8315ba4…` = el del
  manifiesto). `externos_referencia.json` trae `5e0147b0…`, que es **el sha256 de la versión CRLF** (lo que
  VC169-01 ya decía), con `checkout 3768e9431`. `externos_f4.referencia_y_reetiquetado` lo acepta sólo si se lee en un
  checkout CRLF; en uno LF (el runner, o Windows con `autocrlf=false`) lo rechaza. El JSON de juguete del ensayo no
  tiene ni un `\n`: su sha256 LF y su sha256 CRLF son iguales, así que el ensayo no puede fallar por esto. Salida:
  `m05_salida.txt`.
- QUÉ PASA: el ensayo prueba la cadena con un insumo en el que el defecto no puede aparecer, y además se salta el
  productor real del sha (reetiquetado). Es la ceguera del instrumento que dejó pasar a VC169-01.
- CÓMO SE VE EN EL DASHBOARD: no se ve.
- CÓMO REPRODUCIRLO: `python -I .../f2_verificador/m05_crlf.py`.
- CONFIANZA: CONFIRMADO. **Se funde con VC169-01**: el defecto de fondo es ese; P2-05 es que el ensayo no lo ve.
- GRAVEDAD: 2 la ceguera. VC169-01 por sí mismo deja la lectura en INDECIDIBLE después de ~14 h de runner si se lee en
  un checkout LF, y su gravedad ya la fijó el verificador anterior.
- (a) Si VC169-01 se arregla antes del tag, como corresponde, la ceguera puede quedar declarada. Lo sano es que el
  ensayo escriba la población con `indent` y la lea en las dos variantes de fin de línea. (b) Sólo el arnés.

### P2-06. La publicación del runner de V, V-cercano y V-pico nunca se compara
- ARCHIVO:LÍNEA: `probe_f4.py:388` (escribe `pub_runner` con los cuatro brazos); `evaluar_f4.py:609-612` y `:643-647`
  (sólo usan `pub_runner["K"]`). En todo el evaluador no hay ninguna otra lectura de `pub_runner` (grep).
- QUÉ PASA: el evaluador vuelve a calcular la publicación de los brazos V con node sobre los records reducidos y nunca
  la coteja con la del runner. Si el recorte (`slim`, `CAMPOS_JS`) perdiera un campo que sólo pesa en los records de
  V, no se vería; la comparación de K no lo cubre, porque K ejercita otros campos.
- Medición: no encontré ese campo. `frontend/index.html` no nombra `via_codigo_mirova` (grep, 0), y `publica` del
  runner (`probe_etiquetas.py`, l. 187-201 del commit) reduce con los mismos `CAMPOS_JS` y los mismos campos de píxel.
  El riesgo es latente.
- CÓMO SE VE EN EL DASHBOARD: no se ve.
- CONFIANZA: CONFIRMADO, leído. Que pueda cambiar algo hoy: SOSPECHA de que no.
- GRAVEDAD: 2.
- (a) Puede quedar declarado. (b) Sólo el arnés: se puede llevar a un externo sin tocar el evaluador.

### P2-07. El manifiesto deja fuera run_pipeline.py, fetch.py, volcanic_features.yaml y externos_referencia.json
- ARCHIVO:LÍNEA: `manifiesto_candado_f4.py:37-45` (`FIJOS`) y `:52-62` (la sonda importa sólo `probe_f4`,
  `evaluar_f4` e `identidad_f4`; `run_pipeline` y `pipeline.fetch` se importan dentro de funciones:
  `probe_f4.py:418` y `:523-524`, `identidad_f4.py:85`). En `MANIFIESTO_CANDADO_F4.json`: `fetch.py` 0,
  `run_pipeline.py` 0, `volcanic_features` 0, `externos_referencia` 0 (grep -c).
- QUÉ PASA: en el runner los cubre la comprobación del commit (`probe-s168-modd-f4.yml:196-197`). En la lectura no los
  cubre nada. `identidad_f4.contexto` usa `run_pipeline.load_volcanoes` (inner y ancla) y `externos_f4` lee
  `externos_referencia.json` local; si cualquiera de los dos cambia después del tag, nadie se entera.
- CÓMO SE VE EN EL DASHBOARD: no se ve.
- CÓMO REPRODUCIRLO: `grep -c "fetch.py\|run_pipeline.py\|volcanic_features\|externos_referencia" experiments/_s166_modd_f4/MANIFIESTO_CANDADO_F4.json`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2.
- (a) Antes del tag, porque el manifiesto se regenera igual antes del tag: son 4 entradas en `FIJOS`. (b) Sólo el
  arnés.

### P2-08. Las dependencias no están fijadas y nadie compara entre tandas las versiones de la cabecera
- ARCHIVO:LÍNEA: `.github/workflows/probe-s168-modd-f4.yml:122` y `:189-190` (`pip install earthaccess numpy h5py scipy
  pyyaml pyproj pandas`, y `pyhdf`, sin versiones); `probe_f4.py:496` (la cabecera guarda sólo python, numpy y scipy;
  no earthaccess, pyhdf, h5py, pyproj ni node); `externos_f4.py:57-79` (la procedencia no mira `versiones`). En todo el
  arnés nadie lee `versiones` (grep).
- QUÉ PASA: las tres tandas se despachan en momentos distintos y pip puede resolver otras versiones. earthaccess
  decide cómo se propaga una caída (P2-01), y numpy y scipy entran en K y en V. Si cambian, nadie lo ve.
- CÓMO SE VE EN EL DASHBOARD: no se ve.
- CONFIANZA: CONFIRMADO, leído. Que haya un efecto numérico entre versiones: SOSPECHA, no medido.
- GRAVEDAD: 2.
- (a) Recomendado antes del tag: fijar versiones en el workflow (es `.github/`, no `pipeline/`), registrar earthaccess,
  pyhdf y node en la cabecera, y poner la procedencia en rojo si las versiones difieren entre cabeceras. (b) Sólo el
  arnés y el workflow.

### P2-09. VRP_PROFILE y F4_RAIZ cambian la lectura sin dejar rastro
- ARCHIVO:LÍNEA: `evaluar_f4.py:48` y `probe_f4.py:80` (`RAIZ = F4_RAIZ o la raíz real`); `probe_f4.py:84`
  (`setdefault VRP_PROFILE`); `scripts/run_pipeline.py:152-176` (`apply_volcano_overrides`); `pipeline/profile.py:35`.
- Medido: (1) `F4_RAIZ` sólo lo ponen `mutar_evaluar_f4.py:196` y `probar_probe_f4.py:535`, en el entorno de un
  subproceso o del propio proceso, y siempre con la raíz real; ninguna herramienta lo deja exportado en la terminal de
  quien lee. Si quedara puesto, `banco_paridad` y `index.html` se tomarían de otro árbol mientras `externos_f4`
  (que no lo lee) comprueba el de verdad: el mecanismo existe. (2) `VRP_PROFILE` en la lectura: `procesar_grilla` y
  `evaluar_f4` no leen el perfil (`mirova_v750_codigo.py` sólo importa math, functools, pathlib y numpy), y los únicos
  `volcano_overrides` que hay (`_f70_b`, `_s124_kernelbg_ab`) tocan sólo `local_kernel_bg`, que la identidad no usa.
  Hoy no tiene efecto. En el runner el workflow lo fija (`yml:194`, `:203`) y la cabecera guarda los flags.
- CÓMO SE VE EN EL DASHBOARD: no se ve.
- CONFIANZA: CONFIRMADO EN PARTE: el mecanismo es real, pero con los perfiles y las herramientas de hoy no actúa.
- GRAVEDAD: 1.
- (a) Puede quedar declarado. Barato: que `externos_f4` registre `RAIZ` y `VRP_PROFILE`, o que falle si `F4_RAIZ` está
  puesto. (b) Sólo el arnés.

### P2-10. «Sin record guardado en data/» se lee como «K no difiere»
- ARCHIVO:LÍNEA: `probe_f4.py:282-288` (`registro_guardado` devuelve `None`), `:291-295` y `:380-382` (`publica(None)`
  da 0: `probe_etiquetas.publica`, l. 187-201 del commit); `experiments/_s162_mxd03/probe_mxd03_ab.py:113-121`. Si no
  hay record, K no publica y no hay cúmulo, `k_difiere_de_guardado` sale False, y `control_k_produccion`
  (`evaluar_f4.py:642-652`) no mira `k_guardado is None`.
- Medición (m10_guardado.py, las 5.709 pasadas contra `data/mirova_equivalent` de `743e89c48`, con la llave
  `(datetime_utc, sensor)` del arnés): **0 de 5.709 sin record**. El control de que el instrumento está vivo es el
  formato de `datetime_utc` (`'2025-02-15 03:15'`), que es el mismo de la población: las 5.709 casan. Salida:
  `m10_salida.txt`.
- QUÉ PASA: el mecanismo existe (una ausencia de comparación cuenta como acierto, P-D), pero hoy no tiene base. Sólo
  aparecería si el `data/` del commit del tag fuera distinto del que usó la población.
- CÓMO SE VE EN EL DASHBOARD: no se ve.
- CÓMO REPRODUCIRLO: `python -I .../f2_verificador/m10_guardado.py`.
- CONFIANZA: CONFIRMADO EN PARTE: mecanismo leído, base medida en 0.
- GRAVEDAD: 1.
- (a) Puede quedar declarado. Conviene volver a correr m10 sobre el commit del tag cuando exista. (b) Sólo el arnés
  (por ejemplo, que `difiere` dé `None` cuando no hay guardado).

### P2-11. Un MxD03 «ilegible» se lee como «volcán fuera del gránulo» (motivo sellado)
- ARCHIVO:LÍNEA: `pipeline/mirova_v750_codigo.py:805-811` (`calcular_vrp_granulo` devuelve `None` con menos de 100
  píxeles finitos a 45 km); `:842-861` (`leer_geo_mxd03`: lo que cae fuera de rango pasa a NaN);
  `pipeline/process_modis.py:648-659`; `probe_f4.py:267-271` (`motivo_y_marca`: `devolvio_none` da
  `volcan_fuera_del_granulo` sin mirar `crater_dist_km`, que la captura sí registra en `probe_f4.py:139-146`).
- Lo que se refuta: un MxD03 que pyhdf **no puede abrir** lanza una excepción en `leer_geo_mxd03`, que sube por
  `calculate_vrp` hasta `probe_f4.py:568` y queda `estado: error` (falla, en rojo), no «fuera». Lo que se confirma: un
  MxD03 que sí se abre pero trae lat y lon de relleno cumple al pie de la letra la definición sellada («menos de 100
  píxeles a 45 km») y sale del denominador de todos los brazos. La captura deja `crater_dist_km = inf`, pero nadie lo
  mira.
- Base expuesta (m11_sin_grilla.py): la protección N-01 (`evaluar_f4.py:462-468`) cubre las 5.321 pasadas con grilla
  del censo. Quedan expuestas **388**: 144 de C (pasadas en que el censo no tuvo grilla, coherente con que estén
  «fuera») y **244 de E**, entre ellas 6 protegidas y 1 bajo1. Salida: `m11_salida.txt`.
- CÓMO SE VE EN EL DASHBOARD: no se ve.
- CONFIANZA: CONFIRMADO EN PARTE. Con qué frecuencia trae relleno un MxD03 que sí se abre: SIN DATO.
- GRAVEDAD: 2. Puede sacar en silencio una pasada de E del denominador (P-D), con muy poca probabilidad.
- (a) Puede quedar declarado. (b) Sólo el arnés: que `motivo_y_marca` exija `crater_dist_km` finito para dar
  «fuera», y si no, que lo marque como falla. Eso es coherente con la regla sellada de que «una vía que no corrió deja
  el control en rojo».

### P2-12. P2 con 21 bloques o más depende de cómo numpy genera los sorteos, y el resultado no registra la versión
- ARCHIVO:LÍNEA: `experiments/_s157_prereg_d25/evaluar_d25.py:542-546` (blob `1dbabf65`, comprobado con
  `git hash-object`): `default_rng(162).choice((-1, 1), size=(10000, B))`; también `:198-207` (`pesos_bloque`,
  `default_rng(157).integers`, el bootstrap de M y del placebo). `evaluar_f4.py:562-565` (el contador, `choice` sin
  reposición, sólo un autocontrol).
- QUÉ PASA: con B de 21 o más el valor-p sale de sorteos, y la serie de números del `Generator` de numpy no tiene
  estabilidad garantizada entre versiones. Eso es SOSPECHA: en esta sesión no leí la política de numpy. P2 y M se
  calculan en la lectura con el numpy local (aquí 2.4.4), y `resultado_f4.json` no lo registra. La cabecera sólo
  trae el numpy del runner, que no es el que calcula P2.
- CÓMO SE VE EN EL DASHBOARD: no se ve.
- CONFIANZA: CONFIRMADO EN PARTE. El camino y la falta de registro, leídos; que el flujo cambie entre versiones y que B
  pase de 20: SOSPECHA.
- GRAVEDAD: 1. Sólo podría mover un valor-p que quede justo en el borde del 5 %.
- (a) Puede quedar declarado. Barato: anotar la versión de numpy de la lectura en externos (va dentro del resultado).
  (b) Sólo el arnés. `evaluar_d25.py` es un blob sellado y no se toca.

## 4. Hallazgos propios

### VF2-01. `evaluar_f4.py` del árbol no es el sellado del §13
- ARCHIVO:LÍNEA: `PREREGISTRO_MODD_F4.md:390-392` (sha256 `c01e0824…` para `evaluar_f4.py`) frente al
  `evaluar_f4.py` del árbol `743e89c48`: sha256 crudo y LF `8a1edc14…` (`sha256sum`).
- QUÉ PASA: el evaluador cambió después del sello. Por el mensaje del commit `3db87f50d` («VS-01 a VS-08 cerrados en
  bateria y medidor») y por la corrida de mutaciones de hoy, sospecho que es intencional y que las mutaciones lo
  vuelven a certificar. Si no fuera así, la tabla del §13 certifica otro archivo.
- CONFIANZA: CONFIRMADO que el sha256 es distinto; que sea intencional: SOSPECHA.
- GRAVEDAD: 2, si el orquestador ya lo sabe. Va como SEGUIMIENTO, fuera de mi eje.

### VF2-02. La procedencia que escribe la cabecera es letra muerta
- ARCHIVO:LÍNEA: `probe_f4.py:490-496` escribe `sha256_evaluar_f4`, `sha256_probe_f4`, `blob_evaluar_d25`, `flags` y
  `versiones`. En `externos_f4.py` y `evaluar_f4.py` nadie lee ninguno de esos campos (grep; sólo `sha256_poblacion` y
  `sha256_frontend_index` tienen lector).
- QUÉ PASA: es la pieza que cerraría P2-03, P2-08 y parte de P2-02 sin agregar nada nuevo: los datos ya vienen en cada
  cabecera y sólo falta compararlos en `externos_f4`.
- CONFIANZA: CONFIRMADO. GRAVEDAD: 2. (a) Antes del tag, junto con P2-03. (b) Sólo el arnés.

## 5. SEGUIMIENTOS (fuera de mi eje)
- VF2-01, arriba.
- `m05_crlf.py` reconfirma VC169-01: `externos_referencia.json` lleva `poblacion_sha256 = 5e0147b0…` (CRLF), con
  `checkout 3768e9431`; la causa está en `reetiquetado_f4.py:171`, que usa `PF.sha256` crudo.
- Nota de método para quien repita esto: `python -I` ignora `PYTHONIOENCODING` (porque `-I` implica `-E`), así que la
  salida con tildes queda mal codificada si el script no hace `sys.stdout.reconfigure(encoding="utf-8")`. Mis
  m03/m10/m11 lo hacen; `m01_salida.txt` y `m05_salida.txt` tienen tildes rotas en el texto, pero los números están
  bien.

## 6. VERIFICADO LIMPIO
- La copia del pre-registro en el árbol es idéntica a la sellada (`git show 3768e9431:…` contra el árbol, `diff` vacío
  sin contar CR). Vara: el tag `s168-modd-f4-sellado` → `3768e9431`.
- La llave `(datetime_utc, sensor)` del arnés casa con `data/` en las 5.709 pasadas (m10). Vara: la población sellada.
- El workflow exige el commit del tag en `prueba` y en `probe` (`yml:128-129`, `:196-197`) y el blob de evaluar_d25
  (`yml:130`, `:198`). Vara: §8.8.
- `comprobar` del manifiesto ve un archivo cambiado cuando no se regenera (m03, paso 1). Vara: su propia docstring.

## 7. SIN DATO
- Si la versión de earthaccess que instala el runner propaga el ConnectTimeout hasta `download_granules` (P2-01): no
  hay red y no está fijada.
- Con qué frecuencia trae relleno un MxD03 que sí se abre (P2-11).
- B real de P2 y de P2' en la corrida (P2-12).
- `data/` del commit del tag: el tag del candado no existe todavía (P2-10).

## 8. FUERA DE ALCANCE
- Corrida de mutaciones en curso y `s168_mut`; arnés, ensayo en seco y medidor sin correr (por orden de la tarea).
- Abrí el informe del auditor sólo después de escribir estos veredictos (ver §9).

## 9. Después de los veredictos
Después de escribir los veredictos, miré sólo los encabezados del informe del auditor y su P2-01. En P2-01 coinciden
el mecanismo, los 400 s por gránulo y las ~70 pasadas sin fila. Mi medición agrega tres cosas que no vi en lo que
leí: también se pierde el gránulo de la caída, porque sus propios reintentos chocan con el breaker; el reset tiene
que ir por intento y no por gránulo; y las filas `no_bajado` salen sin `flush`. Yo le doy gravedad 3 y no 4: el
veredicto queda INDECIDIBLE y se ve, no se tuerce. No cambié ningún veredicto. Los P2-13 a P2-16 del auditor no
estaban en mi encargo y no los verifiqué.
