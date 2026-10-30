# Auditoría de patrones, frente MODIS: MOD-D fase 4 (candado del A/B)

## 1. Encabezado

- Hora: reloj local del computador, Fri Oct 30 03:44 UTC 2026 al empezar. La hora del servidor (`gh api -i`, header `Date`) es SIN DATO: no hay red en esta tarea.
- Commit medido: `743e89c48` (rama `claude/s168-modd-f4-sello`), extraído a `D:\vrp-trabajo\temporales\s169_audit_patrones\f2_modis\arbol\`. Pre-registro leído: `PREREGISTRO_MODD_F4.md` de ese árbol.
- Modelo: Sonnet 5.5. Esfuerzo: el arnés no lo declara.
- CARPETA: `D:\vrp-trabajo\temporales\s169_audit_patrones\f2_modis\`. Scripts propios y sus salidas en `scripts\`; `raiz_min\` es una raíz mínima armada con `git show` para poder importar `evaluar_f4.py` (blob de `evaluar_d25.py` verificado 1dbabf65).
- Qué NO miré (que mi silencio no se lea como "sano"): no corrí el ensayo en seco, el arnés, la batería ni el medidor de mutaciones (cupos ocupados). No toqué `data/` real, `mutar_evaluar_f4_salida.txt` vigente de otro worktree ni sus temporales. No leí `probar_identidad_f4.py` ni `contrato_poblacion_f4.py` línea por línea (sólo grep de `except`/`exit`). No verifiqué el texto sellado de MOD-D salvo la sección de Chillán (leída con `git show s162-modd-tag`). Nada de red: no puedo decir si LAADS/CMR sirven los archivos, ni cómo reacciona `earthaccess` real.

## 2. En una pantalla

1. El evaluador y el pre-registro calzan (P-G limpio en umbrales, y/o y desigualdades que revisé; sólo una omisión informativa, P2-14).
2. Lo más grave está en el runner, no en las reglas: el circuit-breaker de descarga de `pipeline/fetch.py` queda pegado en el proceso y `bajar_por_nombre` lo traga con 400 s de espera por gránulo; con 53 a 54 gránulos por parte, una sola caída de host consume el timeout de 240 min y deja pasadas sin fila (P2-01, gravedad 4).
3. Cuatro controles del candado pasan por la razón equivocada o no atan sus entradas: el evaluador no ata población, identidad y externos a la lectura (P2-02), el manifiesto se comprueba contra el checkout de la lectura y no contra el tag (P2-03), la clase de la identidad se recalcula en local (P2-04) y el ensayo en seco usa JSON compacto, por eso no pudo ver el P-A ya conocido (P2-05).
4. P-A: fuera de VC169-01 no hay otra huella CRLF viva en el candado; sí un mecanismo que lo explica (P2-05) y una dependencia del `autocrlf` del lector.
5. P-D: `ATRAPADA_CON_CAIDAS` existe y no cuenta (comprobado en el código y con entradas sintéticas); el medidor igual sale con código 0 con mutaciones vivas, y su salida commiteada (82 mutaciones, 3 controles) no es la del código (86 y 4).

## 3. Hallazgos

### P2-01
- TÍTULO: El breaker de hosts de descarga queda pegado en el proceso del arnés y `bajar_por_nombre` gasta 400 s por gránulo sin bajar nada
- ARCHIVO:LÍNEA: `experiments/_s166_modd_f4/probe_f4.py:413-442` (`bajar_por_nombre`), `:549-550` (L1B y MxD03 sin cortocircuito), `pipeline/fetch.py:950` (`_DOWN_DOWNLOAD_HOSTS`), `:1076` (RuntimeError), `:413` (`reset_transient_breakers`); SCRIPT: `scripts/p2_01_breaker_pegado_salida.txt`
- QUÉ PASA: Si una descarga del job cae en ConnectTimeout con el host sin responder al probe TCP, `download_granules` marca el host caído "para la corrida" y lanza RuntimeError al instante en todas las descargas siguientes. El arnés nunca llama `reset_transient_breakers()` (0 apariciones en el arnés y en el workflow), `bajar_por_nombre` captura la excepción, duerme 20+40+60+80 = 200 s y devuelve (None, None); lo repite para el MxD03. Medido: 400 s por gránulo; una parte tiene 53 o 54 gránulos (`p2_02`), o sea unas 6 h contra el timeout de 240 min: alcanzan 36 gránulos y los últimos 17 o 18 (unas 70 pasadas) quedan sin ninguna fila.
- CÓMO SE VE EN EL DASHBOARD: invisible (es un A/B de laboratorio); lo que se ve es el A/B: cobertura en rojo en C, todo INDECIDIBLE, después de gastar hasta 240 min de ese job. Si cae sólo en E, el protocolo saca E.
- CÓMO REPRODUCIRLO: `PYTHONIOENCODING=utf-8 C:/Users/nmend/AppData/Local/Programs/Python/Python312/python.exe -I D:/vrp-trabajo/temporales/s169_audit_patrones/f2_modis/scripts/p2_01_breaker_pegado.py`. Control positivo (breaker limpio, `earthaccess.download` sustituido) baja el archivo con 0 s de espera. No se simula la caída real del host (sin red): la probabilidad de que ocurra es SOSPECHA.
- CONFIANZA: CONFIRMADO el mecanismo y los 400 s; SOSPECHA la frecuencia
- GRAVEDAD: 4 (hace indecidible tras gastar runner)

### P2-02
- TÍTULO: El evaluador no ata las entradas que elige quien lee (población, identidad, externos), y el resultado no deja procedencia
- ARCHIVO:LÍNEA: `experiments/_s166_modd_f4/evaluar_f4.py:765` (`--poblacion`), `:770-771` (`idn["pasadas"]`, se ignoran `art`, `poblacion`, `censo` del archivo), `:772` (`--externos`), `:784` (`resultado_f4.json` se pisa); `identidad_f4.py` default `AQUI/identidad.json`
- QUÉ PASA: Las etiquetas (`lab`) que deciden salen del `--poblacion` que se pase al leer, la identidad de cualquier `identidad.json` y los controles externos de cualquier `externos.json`. `externos_f4` valida la población que él mismo lee (su `--poblacion`), no la del evaluador, y `identidad.json` guarda `art` y `poblacion` pero el evaluador no los compara con nada. Tras un "repetir la lectura" (el protocolo del §7 lo permite) puede quedar una `identidad.json` verde de la corrida anterior. El resultado tampoco registra los sha256 de lo que leyó.
- CÓMO SE VE EN EL DASHBOARD: invisible
- CÓMO REPRODUCIRLO: lectura de código en las líneas citadas; `scripts/p2_03_evaluador_demos_salida.txt` D2 muestra que una entrada de identidad sin procedencia es aceptada.
- CONFIANZA: CONFIRMADO
- GRAVEDAD: 3

### P2-03
- TÍTULO: El manifiesto y la procedencia no atan la lectura al commit del tag
- ARCHIVO:LÍNEA: `manifiesto_candado_f4.py:36` y `:98` (`comprobar(ruta=MANIFIESTO)` lee el manifiesto del checkout de la lectura), `:89-91` (`tag` y `commit_tag` quedan en None); `externos_f4.py:112-118` (`armar`: sólo compara las cabeceras de los jobs con el commit del tag y `frontend/index.html`; nunca `HEAD == tag`)
- QUÉ PASA: Un lector en un commit posterior, con evaluador y manifiesto cambiados juntos, obtiene `manifiesto: OK`. Lo que verifica la lectura es consistencia interna del checkout, no igualdad con lo que corrió en el runner. Emparentado con VC169-06 (blob sellado); aquí el defecto es que no se compara con el árbol del tag.
- CÓMO SE VE EN EL DASHBOARD: invisible
- CÓMO REPRODUCIRLO: lectura de código; `p2_02_poblacion_manifiesto_salida.txt` §4 (`commit_tag: None`).
- CONFIANZA: CONFIRMADO
- GRAVEDAD: 3

### P2-04
- TÍTULO: La identidad compara la clase recalculada en local, no la del record del runner, y 8 indicadores de coherencia no deciden
- ARCHIVO:LÍNEA: `identidad_f4.py:178-180` (`vr = via(...)`, `dc_r = ... vr.get("distance_class")` porque el npz no guarda `distance_class`: `probe_f4.py:209-220`), `:192`, `:206-210` (`box_igual`, `pos_crater_igual`, `captura_coherente`), `:251-253` (`igual` no los usa); `evaluar_f4.py:455` (`control_identidad` sólo lee `mismo_granulo`, `misma_mascara`, `dvrp`, `misma_clase`)
- QUÉ PASA: `misma_clase` compara la clase de la vía re-corrida en local con la `box` y la `pos` locales sobre la grilla del runner contra la misma re-corrida sobre la grilla del censo. La clase del record del runner (`v_slim_dc_igual`) sólo se informa; `captura_coherente` compara `vr` contra `dc_r`, que cuando falta `distance_class` en el npz es `vr` mismo, así que esa parte no puede fallar. El §8.2 pide "misma `distance_class`" de V del runner contra V-grilla.
- CÓMO SE VE EN EL DASHBOARD: invisible
- CÓMO REPRODUCIRLO: `scripts/p2_03_evaluador_demos_salida.txt` D2: con los ocho indicadores en rojo `control_identidad` da OK; control positivo (`misma_clase` False) da INDECIDIBLE.
- CONFIANZA: CONFIRMADO (código y demo)
- GRAVEDAD: 3

### P2-05
- TÍTULO: El ensayo en seco usa JSON compacto, por eso el control de huella con fin de línea no podía fallar
- ARCHIVO:LÍNEA: `ensayo_en_seco_f4.py:130` (`json.dumps(pob)` sin `indent`), `:135-137` (`poblacion_sha256 = sha256_bytes(pob_bytes)`); real: `poblacion_f4.py` y `reetiquetado_f4.py:171` usan `indent=0` y `PF.sha256` crudo
- QUÉ PASA: Sin saltos de línea, el sha256 con CRLF y con LF es idéntico; el ensayo 1 da "sin rojos" aunque la población real (226.696 saltos de línea) tenga dos huellas. Explica por qué el P-A de VC169-01 pasó el ensayo. Dependencia añadida: con VC169-01 sin corregir, el resultado de `referencia` y `reetiquetado` depende del `autocrlf` de quien lee (CRLF: coincide; LF o Linux: INDECIDIBLE).
- CÓMO SE VE EN EL DASHBOARD: invisible
- CÓMO REPRODUCIRLO: `scripts/p2_02_poblacion_manifiesto_salida.txt` §1 (sha LF e8315ba4…, CRLF 5e0147b0… = `externos_referencia.poblacion_sha256`) y `p2_03` D6 (`indent=0` genera CRLF con `Path.write_text` en Windows; compacto no).
- CONFIANZA: CONFIRMADO
- GRAVEDAD: 3 (el ensayo era la prueba de que el candado llega a un veredicto)

### P2-06
- TÍTULO: `pub_runner` de V, V-cercano y V-pico se guarda y nunca se compara con el evaluador
- ARCHIVO:LÍNEA: `evaluar_f4.py:635` (`control_k_produccion` sólo mira la clave `K`); `probe_f4.py:` fila `pub_runner` con las cuatro claves
- QUÉ PASA: El docstring del arnés dice que si el slim perdiera algo que el predicado lee "el control §8.1 lo vería", pero eso vale sólo para K. Si el slim de V perdiera un campo, el evaluador publicaría distinto del runner y nada lo señala.
- CÓMO SE VE EN EL DASHBOARD: invisible
- CÓMO REPRODUCIRLO: `p2_03_evaluador_demos_salida.txt` D1 (runner dice V=1, evaluador 0, control OK; control positivo con K da INDECIDIBLE).
- CONFIANZA: CONFIRMADO. Hoy `CAMPOS_JS` cubre los campos que leen las funciones de `index.html` que extraje, así que no encontré un caso real.
- GRAVEDAD: 2

### P2-07
- TÍTULO: El manifiesto omite archivos que el arnés o la lectura cargan en ejecución, y `externos_referencia.json` entra con su `estado` ya escrito
- ARCHIVO:LÍNEA: `manifiesto_candado_f4.py:37-45` (FIJOS), `MANIFIESTO_CANDADO_F4.json` (64 archivos); `externos_f4.py:96-109`
- QUÉ PASA: No están `scripts/run_pipeline.py` (importado en `probe_f4.py:523`, `identidad_f4.py:88`, `k_en_sha.py`; define `load_volcanoes` y `VOLCANIC_FEATURES`), `pipeline/fetch.py`, `pipeline/volcanic_features.yaml`, `externos_referencia.json` (aporta dos de los cinco controles externos con `estado: OK` y no se recomputan al leer), `head_e.json`. Detalle de VC169-02, no hallazgo nuevo salvo los nombres.
- CÓMO SE VE EN EL DASHBOARD: invisible
- CÓMO REPRODUCIRLO: `p2_02_poblacion_manifiesto_salida.txt` §4 (control positivo: `pipeline/store.py` sí está).
- CONFIANZA: CONFIRMADO
- GRAVEDAD: 2

### P2-08
- TÍTULO: Dependencias sin fijar y versiones de la cabecera que nadie compara entre las tres tandas
- ARCHIVO:LÍNEA: `.github/workflows/probe-s168-modd-f4.yml:122,189-190` (`pip install --upgrade pip`, `numpy scipy pyproj pandas ...` sin versiones, `pyhdf`); `probe_f4.py:496` (sólo python, numpy y scipy); `externos_f4.py:57-79` (`procedencia`: commit, tag, modo, partes; no versiones)
- QUÉ PASA: t1, t2 y t3 se despachan en momentos distintos; una versión nueva de scipy, pyproj o pyhdf entre tandas parte el A/B en dos pipelines (el caso A108), y sólo se registran tres versiones, sin control.
- CÓMO SE VE EN EL DASHBOARD: invisible
- CÓMO REPRODUCIRLO: lectura del workflow y de `procedencia`.
- CONFIANZA: CONFIRMADO lo que no se fija; SOSPECHA que una versión cambie el resultado
- GRAVEDAD: 2

### P2-09
- TÍTULO: `VRP_PROFILE` y `F4_RAIZ` pueden cambiar la lectura sin dejar rastro
- ARCHIVO:LÍNEA: `identidad_f4.py` (sin pin de perfil; `run_pipeline.load_volcanoes` aplica `VOLCANO_OVERRIDES` del perfil activo, `scripts/run_pipeline.py:152-176`); `probe_f4.py:84` y `manifiesto_candado_f4.py:54` (`setdefault` respeta un valor previo); `evaluar_f4.py:48` y `probe_f4.py:80` (`F4_RAIZ` redirige evaluador, `evaluar_d25.py`, `banco_paridad` y `index.html`)
- QUÉ PASA: `mirova_equivalent` no tiene overrides, pero `_f70_a`, `_f70_b` y `_s124_kernelbg_ab` sí; un `VRP_PROFILE` olvidado en el shell de la lectura cambia caja y posición de `identidad_f4` sin avisar. Nada registra el perfil ni la raíz usada (`p2_03` D5).
- CÓMO SE VE EN EL DASHBOARD: invisible
- CÓMO REPRODUCIRLO: lectura de código.
- CONFIANZA: SOSPECHA
- GRAVEDAD: 2

### P2-10
- TÍTULO: "Sin record guardado en data/" se lee como "K no difiere"
- ARCHIVO:LÍNEA: `probe_f4.py` (`registro_guardado`, `difiere`, `k_guardado = None`), `probe_mxd03_ab.py:113-121`, `probe_etiquetas.py:187-203` (`publica` da 0 para un record None); `evaluar_f4.py:635` no lee `k_guardado`
- QUÉ PASA: Con `guardado = None`, `pub_guardada` es 0 y `pc_vrp_guardada` None; si K tampoco publica ni tiene cúmulo, `k_difiere_de_guardado` sale False aunque no se comparó nada. Una pasada sin record en `data/` (clave `datetime_utc, sensor` que no calza) pasa el control §8.1 en vacío. En datos: Láscar, Isluga, Lastarria, Llaima, Chillán y Villarrica tienen MODIS hasta 2026-10-27 en el commit auditado y el formato de `datetime_utc` calza, así que hoy no se ve un caso real.
- CÓMO SE VE EN EL DASHBOARD: invisible
- CÓMO REPRODUCIRLO: lectura de código; fechas con `git show 743e89c48:data/mirova_equivalent/Lascar.json`.
- CONFIANZA: CONFIRMADO el mecanismo; SOSPECHA el impacto
- GRAVEDAD: 2

### P2-11
- TÍTULO: Un MxD03 ilegible se lee como "volcán fuera del gránulo", motivo sellado que saca la pasada del denominador
- ARCHIVO:LÍNEA: `pipeline/mirova_v750_codigo.py:842-861` (`leer_geo_mxd03` manda fuera de rango a NaN), `:788-808` (devuelve None si hay menos de 100 píxeles en 45 km); `probe_f4.py` (`motivo_y_marca`: cualquier None con grilla es `volcan_fuera_del_granulo`)
- QUÉ PASA: Sólo las 5.321 pasadas de C con grilla del censo tienen la defensa N-01. En las 144 de C sin grilla y en las 244 de E, una geolocalización rota deja la pasada fuera del denominador de todos los brazos sin falla. Se ve sólo si hay protegida con K publicando (DECIDE NICOLÁS) o en el conteo `fuera_del_denominador`.
- CÓMO SE VE EN EL DASHBOARD: invisible
- CÓMO REPRODUCIRLO: lectura de código; denominadores en `p2_02` §3 (5.709 pasadas).
- CONFIANZA: SOSPECHA
- GRAVEDAD: 2

### P2-12
- TÍTULO: P2 con 21 bloques o más depende del flujo aleatorio de numpy y el resultado no registra la versión
- ARCHIVO:LÍNEA: `evaluar_d25.py:542-546` (`default_rng(semilla).choice((-1,1), size=(10000,B))`, leído en `lectura/evaluar_d25_leido.py`); `evaluar_f4.py:564` (`rng.choice(len(negs), size=50, replace=False)`)
- QUÉ PASA: El pre-registro predice unos 50 bloques, o sea el camino por sorteos. Un valor-p cercano al 5 % puede cambiar de lado con otra versión de numpy y `p2()` no devuelve ni la versión ni la semilla. El conjunto de 50 inyectados también depende de ese flujo.
- CÓMO SE VE EN EL DASHBOARD: invisible
- CÓMO REPRODUCIRLO: `p2_03` D5 (el resultado no contiene "numpy").
- CONFIANZA: SOSPECHA
- GRAVEDAD: 2

### P2-13
- TÍTULO: Una fila del runner que no está en la población hace caer `evaluar()` con KeyError en vez de dar INDECIDIBLE
- ARCHIVO:LÍNEA: `evaluar_f4.py:766-769` (la mezcla no agrega `lab`), `p1()` (`f["lab"]`)
- QUÉ PASA: Los sobrantes que el §8.6 manda a rojo en cobertura nunca llegan a mostrarse: el programa muere antes del veredicto.
- CÓMO SE VE EN EL DASHBOARD: invisible
- CÓMO REPRODUCIRLO: `p2_03` D3 (`CAE con KeyError 'lab'`; control positivo con `lab` llega a veredicto).
- CONFIANZA: CONFIRMADO
- GRAVEDAD: 1

### P2-14
- TÍTULO: El resultado informa P2 por tramo pero no P2'
- ARCHIVO:LÍNEA: `evaluar_f4.py:716`; pre-registro §6, párrafo tras la tabla ("P2 y P2' se calculan sobre C ∪ E y se informan también por tramo", TEXTO)
- QUÉ PASA: `por_tramo` trae sólo `p2` (estado). Es informativo; no cambia el veredicto.
- CÓMO SE VE EN EL DASHBOARD: invisible
- CÓMO REPRODUCIRLO: `p2_03` D4 (claves: `['p2']`).
- CONFIANZA: CONFIRMADO
- GRAVEDAD: 1

### P2-15
- TÍTULO: El medidor de mutaciones sale con código 0 con mutaciones vivas, y su salida commiteada no es la del código
- ARCHIVO:LÍNEA: `mutar_evaluar_f4.py` (`resumir`: código 1 sólo si falla un control); `mutar_evaluar_f4_salida.txt`
- QUÉ PASA: `ATRAPADA_CON_CAIDAS` existe y no se cuenta como atrapada (confirmado con entradas sintéticas y control positivo), pero vivas, que caen, con caídas, rotas y no aplican dejan el código en 0; sólo lo lee un humano en la línea de resumen. La salida commiteada tiene 82 mutaciones y 3 controles; el código trae 86 y 4 (M83 a M86 y `CONTROL_CAIDA_VALUEERROR`) y la salida no contiene "ATRAPADA_CON_CAIDAS" (es parte de VC169-04). Las 89 mutaciones con texto aplican exactamente una vez.
- CÓMO SE VE EN EL DASHBOARD: invisible
- CÓMO REPRODUCIRLO: `scripts/p2_04_medidor_mutaciones_salida.txt` §1, §3 y §4.
- CONFIANZA: CONFIRMADO
- GRAVEDAD: 1

### P2-16
- TÍTULO: Tres filos menores del workflow y de la lectura de artefactos
- ARCHIVO:LÍNEA: `probe-s168-modd-f4.yml:66-71` (job `head_e` sin `if`: corre en humo, t1, t2 y t3 y usa el token); `:32-34` (`cancel-in-progress: false` deja un solo run pendiente: un tercer despacho desplaza al segundo); `evaluar_f4.py` (`cargar`) y `identidad_f4.py` (`leer_runner`): `**/f4_parte*.jsonl` incluye `f4_parte_humo.jsonl`
- QUÉ PASA: HEAD con token en cada tanda sin que el pre-registro lo pida; una tanda desplazada se pierde sin fila; si el humo comparte carpeta con las tandas, `repetidas` en cobertura o RuntimeError en identidad.
- CÓMO SE VE EN EL DASHBOARD: invisible
- CÓMO REPRODUCIRLO: lectura del workflow y del glob.
- CONFIANZA: CONFIRMADO lectura; SOSPECHA que ocurra
- GRAVEDAD: 1

## 4. SEGUIMIENTOS (fuera de mi eje)

- `poblacion_f4.json` y `reetiquetado_f4.py`: la prueba del etiquetador sobre E no tiene control positivo dentro de E (las tres pasadas de control de `poblacion_mxd03` caen fuera de la ventana: FALLA en `poblacion_f4_salida.txt` líneas 16 a 22, ignoradas por diseño). Compensa que 99 alertas de MIROVA coinciden con 99 pasadas etiquetadas protegida o bajo1. Confianza media.
- La población E sale de `data/mirova_equivalent` del checkout: pasadas que el NRT no guardó no entran, y nada verifica que `data/` llegue a la fecha final de E (hoy sí: 22 a 31 pasadas por día, 10 días). Confianza media.
- `reetiquetado_f4.py`, control de poder: sólo 2 etiquetas de C cambian con la referencia de hoy; la comparación contra el censo discrimina poco. Confianza media.

## 5. VERIFICADO LIMPIO

- P-G de `evaluar_f4.py` contra el pre-registro (vara: texto de `PREREGISTRO_MODD_F4.md` leído en esta sesión): P1/P1b/P2/P2', elegibilidad y desempate de §6 bis, orden de las seis filas del §7, protocolo del tramo E (frontera 16 al 17 de octubre), tope de 1 % de identidad, Chillán (`0,8 a 1,25`, `20*num <= den`, 5 pares, cenit 30°; vara adicional: `PREREGISTRO.md` de `s162-modd-tag` líneas 104 a 120). Sin diferencias de y/o, mayor/mayor o igual ni unidades, salvo P2-14.
- Partes: 1.285 claves de gránulo, cada una en una sola de las 24 partes (control positivo: quitar una da 1); 5.709 pasadas sin `l1b`, `geo`, `inner`, `lab`, `tramo` ni `z` vacíos (`p2_02` §2 y §3).
- P-A: `manifiesto_candado_f4.py`, `evaluar_f4.blob`, `probe_f4.sha256_lf` y `externos_f4` normalizan CRLF a LF; las CSV de referencia tienen `sha256` igual a `sha256_lf` (sin CRLF). VC169-01 reproducido con los hashes.
- P-D: `clasificar` y `controles_malos` correctos con control positivo; E53 acotado a `ValueError` con "math domain error".
- P-E: `evaluar_f4`, `identidad_f4` y `externos_f4` no leen el reloj para decidir.

## 6. SIN DATO

- Hora del servidor, frecuencia real del ConnectTimeout en el runner, si CMR/LAADS sirven hoy los archivos, tiempo real por pasada con re-corridas en sha: requieren red o runner.
- Que `earthaccess.download` deje un archivo parcial que luego se reuse: no lo pude probar.
- Resultado de la batería del arnés y del medidor: `probar_probe_f4.py --sin-mutaciones` y `mutar_evaluar_f4.py` no se corrieron (cupos).

## 7. FUERA DE ALCANCE

Fórmulas físicas de la vía (`mirova_v750_codigo.py`), calidad de la referencia de MIROVA, y arreglos: ninguno fue aplicado.
