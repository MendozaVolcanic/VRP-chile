# Verificador limpio de la adenda 2 de V375-E (PREREGISTRO_E.md §8) y su código

CARPETA: C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\adoring-wright-dc0404\experiments\_s162_v375\e_adenda2\verificador\

## Encabezado
- Hora del servidor (gh api, header Date): 2026-10-28 04:51:58 GMT al empezar; 05:19 UTC al cerrar. Commit medido: 6c80ce7c0c17653669bd3a8c5d8a737c1c8c9a07 (rama claude/adoring-wright-dc0404). Modelo: Claude Sonnet 5.5, esfuerzo bajo.
- caminos.md escrito ANTES de abrir e_adenda2/ y la §8; sha256 bcf60fd0ee03907e69715405da49eaa910832aa206041e6d44cb727c2be8bcf9 (calculado antes de anotar la línea final), 04:52:14 UTC; no se editó después.
- NO miré: ninguna lectura de publicación de P sobre artefactos de S159, S162, S162b ni FAR (no corrí leer_posicion_v375e.py contra datos reales); el run FAR no existe; no verifiqué secretos de GitHub (EARTHDATA_TOKEN); no revisé MODIS ni VIIRS 750; no leí PDF de ningún paper (este informe no cita papers). Los JSON de objetivos sí (permitido); las grillas de tests/datos_s165_v375 sí (identidad de la vía y almacén).

## En una pantalla
1. VEREDICTO GLOBAL: SELLABLE CON CAMBIOS. Las cifras de la adenda se reproducen (330/329/1, 122 de 330, 10.087, T117/O1 131/O2 82, sha256, 8 pasadas y 4 protegidas, 40 de 329); la lista de lejanas se regenera idéntica byte a byte; la batería da 112 de 112 y el nulo del autor 62 de 63 (la que sobrevive es equivalente).
2. Defecto de diseño serio: el veto de la RP (§8.5 paso 1) lo decidirán las 3 protegidas OCR de Suomi NPP que K publica y que el port pierde en todas las posiciones (documentadas en V375-C): saldría «NINGÚN BRAZO PASA EL VETO» sin importar la posición (VE2-01).
3. La lista de lejanas depende de un archivo del repo no fijado en la adenda (capa histórica de filas perdidas): 15 de 330 lejanas sacan su fila FALSO_POSITIVO de ahí (VE2-02).
4. Una aserción de la batería nunca se ejecuta (else muerto, probar_adenda2.py:626-628) y 16 de mis 23 mutaciones sobreviven; entre ellas pesos distintos de 1, errores de negativos en la RP, umbral de cobertura y ancla de medida (VE2-03, VE2-04).
5. §8.3 describe bien la vía de #921; los tres brazos y la frontera son los de la vía; el almacén no altera la publicación de las variantes (18 de 18).

## Veredictos por pregunta
1. §8.3 vs #921: CONFIRMADO EN PARTE (gravedad 1). Blob de pipeline/mirova_v750_codigo.py a9c00eaf137896231c5cb43759b1110b1e0d539c en HEAD, bd711db63 y 55c95c705 (git rev-parse). ENABLE_V375_CODIGO_MIROVA=False en los tres perfiles leído de pipeline.profile (pipeline/profile.py:933; default False, ningún yaml lo menciona). Almacén: store.py:357,362,401,455,614 saltan la vía como dice. Equivalencia: experiments/_s165_v375_via/equivalencia_v375e_salida.txt («igual en 2004 de 2012; protegidas distintas 4», «289 de 329», «40 calzan»). Omite: el relabel A46 del almacén (store.py ~485) y geo_class leen pc.centroid_dist_km, por eso las variantes deben reescribir ese campo (§8.4 lo hace, §8.3 no lo dice); el corte de 5 km al centro (FAMILIAS dist_max_centro_km); «bloque al inicio de calculate_vrp» está en la línea ~758 de una función que empieza en 702.
2. Brazos: CONFIRMADO EN PARTE (gravedad 2). Radiante y pico salen de procesar_grilla/_cumulo_del_mas_radiante (C5 los ata; identidad sobre 6 grillas reales de tests). Cercano = alertado más cercano al cráter, mismo punto: ve_ancla_grilla_salida.txt (ancla = get_detection_anchor en 11 de 11; grilla de la vía = grilla de la lista en epsg, n, ul_x, ul_y, x0, y0; inner yaml = inner del tablero en 11 de 11). Frontera inclusiva igual a la vía (`dcen <= inner_km`). El predicado del tablero lee distance_class y pc.centroid_dist_km (frontend/index.html:1175, 1179) y f5CoreMagnitude cae a pc.vrp_mw porque los píxeles de la vía no traen vrp_mw (index.html:1248-1262): lo que se cambia es justo eso. Cada variante pasada por store.append_record: 18 de 18 sin cambio de clase, VRP ni publicación (ve_almacen_variantes_salida.txt, con control positivo). Reservas: VE2-08 y VE2-04 (el ancla de medida no la protege ningún test).
3. Lista de lejanas: CONFIRMADO EN PARTE (gravedad 2). Regenerada en D:\vrp-trabajo\temporales\s166_v375e_verif\gen (regen_salida.txt): objetivos_far d968aafe…c46c7d, objetivos_run 4abc0630…51ad47, población aff8822a…cd0a7d (el que imprime el script con LF; sha256sum crudo da 9617b6e0… por el CRLF de Windows), sin_granulo 745016b9…; cmp byte a byte de objetivos_far y sin_granulo contra los del autor: iguales. Referencia bajada de fe2d0a57/4ddd5481 (sha256 0a4fc79c…, f03bfeb9…). Separación: 311 tabla sola, 18 tabla+OCR, 1 OCR sola (Láscar 2026-08-01 05:00 SNPP). Premisa «lo correcto es no publicar» contra el radio del tablero: 0 de 329 far_tabla con Distancia_km de MIROVA <= inner (ve_far_vs_inner_salida.txt; mínimo 3,46 km en Planchón-Peteroa con inner 3). Conteo independiente desde los CSV (ve_far_independiente_salida.txt): 317 de 330, ninguna de más; las que faltan son la capa histórica (VE2-02). Clases que Nicolás pide y faltan: ninguna (las FALSO_POSITIVO con ALERTA en la misma pasada están en `pos`, declarado en §8.10).
4. RP (§8.5): CONFIRMADO EN PARTE (gravedad 4). Falla en las dos direcciones (ELEGIDO cercano/pico/radiante, NINGÚN BRAZO, NO RESUELTO, NO DECIDE; todas las ramas están en la batería). Huecos: VE2-01 (veto estructural), VE2-09 (ciclo), VE2-12 (pesos), VE2-13 (poder). Pesos medidos en la lista (ve_pesos_salida.txt): pos_prot 1,0; pos_bajo 4,75 a 5,33; neg_pub 1,0; neg_resto 1,98 a 2,12; far_tabla 1,0: ninguna lejana queda aplastada, pero una alerta bajo 1 MW perdida pesa ~5 veces una protegida perdida o una lejana publicada. El veto heredado del §5.4 (a) no es el que corresponde a una regla que elige posición (VE2-01).
5. A119 y A104: CONFIRMADO EN PARTE (gravedad 2). En T (hasta 2026-06-12) el marco no trae alertas solo-OCR (ve_tramos_salida.txt: pos_prot 38 y pos_bajo 72, todas de la tabla); vara 3 usa OCR desde 2026-06-13 (FRONTERA_OCR; la mutación V30 del borde sobrevive). La RP que decide cuenta alertas solo-OCR (O1: 3 prot + 20 bajo; O2: 11 + 11) y las 4 protegidas motivadoras son solo-OCR, dos de Suomi NPP antes del 2026-10-09 (VE2-07). A104: sólo se informa cuántos bloques discordantes aporta cada tramo, sin veredicto por tramo (VE2-06). La tasa con que K publica en lejanas es plana por tramo (0,39 / 0,35 / 0,37), así que el riesgo práctico es bajo. Vara 3 informa y no entra en decidir_brazo ni en regla_posicion: CONFIRMADO (A93 respetado).
6. Batería y nulo: CONFIRMADO EN PARTE (gravedad 3). probar_adenda2.py: 112 de 112 (probar_repro_salida.txt). mutar_adenda2.py: IDENTIDAD PASA, CONTROL CAÍDA, 62 de 63 atrapadas, sobrevive L20, 0 caídas; salida idéntica a la del autor (restaurada con git checkout). L20 es equivalente (far_ocr no suma error en err_pos y regla_posicion excluye CLASES_FAR del veto). Mis 23 mutaciones (mutar_ve2.py + probar_mio.py, mutación en memoria): control positivo M00 ATRAPADA, identidad pasa, control de importación CAÍDA; 6 atrapadas, 16 sobreviven (VE2-03, VE2-04, VE2-05). El clasificador distingue caída de aserción.
7. Lectura anticipada y workflow: CONFIRMADO EN PARTE (gravedad 2). Batería y nulo no leen artefactos reales (escenas sintéticas, tests/datos_s165_v375, artefacto falso con directorios vacíos). Pero leer_posicion_v375e.py:73-76 y :558-560 dejan por defecto las rutas reales de S159/S162/S162b: correrlo sin --art-far ya imprime la vara 1 retrospectiva (VE2-10). Workflow: diff contra probe-s162-v375-b2.yml (commit 74e368f6e): sólo cambian nombre, rama, grupo, OBJETIVOS, matriz 0..13, --nchunks 14, nombre del artefacto; "on" entre comillas, sólo EARTHDATA_TOKEN con falla si viene vacío, permissions contents: read; 350 pasadas = 14 x 25; probe_v375.py guarda grilla_{id:04d}.npz y E.grilla_npz busca {03d} y {04d}: los ids de 5 dígitos calzan. Vigencia del token: SIN DATO. Comentario con referencia errada (VE2-11).
8. Cifras: CONFIRMADO. 330/329/1, 122 de 330, T 117/O1 131/O2 82, 10.087 contra 10.087 (objetivos_far_v375_salida.txt, reproducido en regen_salida.txt); tres sha256 reproducidos; 8 pasadas, 4 protegidas, 289 de 329 / 40 calzan (equivalencia_v375e_salida.txt); el 338 de S165 (origin/loop/activo experiments/_s165_regla_posicion/verificador/05_far_ref_fuera_del_universo_salida.txt). Las 4 protegidas están en objetivos con pub_prod=1 y solo-OCR (ve_protegidas_salida.txt).

## Hallazgos (ordenados por gravedad)

### VE2-01
- TÍTULO: El veto de la RP lo deciden pérdidas ajenas a la posición: saldría «NINGÚN BRAZO PASA EL VETO» sin medir nada
- ARCHIVO:LÍNEA: experiments/_s162_v375/PREREGISTRO_E.md:264 (§8.5 paso 1) y 113-118 (§5.4 riesgo conocido); e_adenda2/leer_posicion_v375e.py función regla_posicion (veto sobre `pos_prot`, `x["K"]` y `not x["X"][("VIA", a)]`); SCRIPT:SALIDA verificador/ve_veto_estructural_salida.txt, verificador/ve_protegidas_salida.txt
- QUÉ PASA: Las 3 protegidas solo-OCR de Suomi NPP que K publica (Tupungatito 2026-08-01 05:00, Isluga 2026-09-09 06:06, Tupungatito 2026-09-14 06:18) las pierden los diez brazos de ROI según el verificador de V375-C (experiments/_s162_v375/resultado_run40116289866/verificador/INFORME.md:43, TEXTO: «Las 6 protegidas que los 10 brazos pierden son todas Suomi NPP, sólo OCR, del lote S159»; «K "publica" 3 de ellas»), y la vía tiene la misma máscara que C13 en 2012 de 2012 (equivalencia_v375e_salida.txt). Si nada alertado cae cerca del cráter, ninguna posición las publica y el veto saca a los tres brazos. Demo sintética con las escenas de la batería: una sola protegida solo-OCR que K publica y ningún brazo ve basta para «NINGUN BRAZO PASA EL VETO», mientras la variante «tabla sola» elige CERCANO.
- CÓMO SE VE EN EL DASHBOARD: invisible (decisión de método); la lectura diría «P no cumple (a) con ninguna regla» y la medición de posición quedaría sin elegir.
- CÓMO REPRODUCIRLO: `python -I verificador/ve_veto_estructural.py`; protegidas en `python -I verificador/ve_protegidas.py`. Lo que pasa con datos reales NO lo medí (restricción): es inferencia desde documentos del repo y máscara idéntica.
- CONFIANZA: CONFIRMADO el mecanismo (demo); SOSPECHA alta que ocurra con los datos reales.
- GRAVEDAD: 4

### VE2-02
- TÍTULO: La lista de lejanas (y el marco) dependen de archivos del repo que la adenda no fija; 15 de 330 lejanas toman su FALSO_POSITIVO de la capa histórica
- ARCHIVO:LÍNEA: PREREGISTRO_E.md:226-227 y e_adenda2/objetivos_far_v375.py (el meta guarda sólo los 2 commits); scripts/referencia_mirova_unificada.py:160-178; SCRIPT:SALIDA verificador/ve_far_capas_salida.txt
- QUÉ PASA: cargar_referencia_unificada(cons, ocr) agrega por defecto data/mirova_reference/union_historica/consolidado_filas_perdidas.csv (sha256 LF 2613e7cc03e75c2f6b0be41d11051ae847dece00be817d305b7e77d95bbf59e7; 2.153 filas) y el respaldo del 2026-04-08 (183aff7f38c6ca9ef93c8e0951f8190dd12be2690d54dbacb7d7acabaaa93568, no aportó filas). Son filas que la tabla de Mirova-v1 tuvo y perdió. 13 far_tabla las toman sólo de ahí y 2 más (con FALSO_POSITIVO_OCR al lado) también: sin esa capa serían far_ocr o no estarían. C-G3 mantiene consistente el marco hoy, pero ni la adenda ni el meta fijan esos hashes.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python -I verificador/ve_far_capas.py` (ej. Chaiten 2026-04-09 06:00, Isluga 2026-04-16 05:18).
- CONFIANZA: CONFIRMADO
- GRAVEDAD: 2

### VE2-03
- TÍTULO: Una aserción de la batería nunca se ejecuta (else muerto)
- ARCHIVO:LÍNEA: e_adenda2/probar_adenda2.py:626-628
- QUÉ PASA: `ok("main() sobre 5 grillas reales: máscara vía = port C13 ..., VRP ..., publicación por brazo igual")` quedó dentro del `else:` de `if lascar.exists():`. Con la copia de 533398f8f presente jamás corre; probar_adenda2_salida.txt no la contiene. La §8.11 la cita como verificada («5 de 5»); los números se imprimen en el log de main() pero sin aserción. Si faltara el archivo de D:, el else sumaría un FALLA fijo.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `grep -n "main() sobre 5 grillas" experiments/_s162_v375/e_adenda2/probar_adenda2_salida.txt` (sin resultados); `sed -n 618,630p e_adenda2/probar_adenda2.py`.
- CONFIANZA: CONFIRMADO
- GRAVEDAD: 2

### VE2-04
- TÍTULO: Mutaciones propias que importan y la batería deja pasar
- ARCHIVO:LÍNEA: SCRIPT:SALIDA verificador/mutar_ve2_salida.txt (mutar_ve2.py, probar_mio.py)
- QUÉ PASA: Con control positivo M00 atrapado, identidad en verde y control de importación CAÍDA, sobreviven: V01 (pesos N/n_ok puestos a 1: la batería arma meta con N igual al conteo, así que nunca prueba pesos distintos de 1; en el marco real valen 1 a 5,3); V03 (la RP sin los errores de negativos limpios); V04 y V05 (la regla de 10 % de lejanas SIN DATO, §8.5 paso 5, no tiene test); V06 (C7 sin exigir píxeles); V08 (rango de ids CTLF); V15 (main con posición y referencia cambiadas: C5 lo frenaría al correr, la batería no lo afirma); V17 (main con C6 siempre verde; empíricamente el almacén no cambia nada, 18 de 18); V30 (borde 2026-06-13 del OCR); V50 (la vía armada con el centroide del volcán en vez del cráter: invisible porque C5 compara contra la misma posición; hoy es correcto, ancla = get_detection_anchor en 11 de 11); V51 (pos_ref con ejes cambiados: el test usa una grilla simétrica); V55 (ciclo); V57 (el inner del tablero no se ejercita porque la variante ya fija la clase); V54 y V56 equivalentes o débiles.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python -I verificador/mutar_ve2.py` (unos 10 minutos).
- CONFIANZA: CONFIRMADO (los sobrevivientes); que cada uno sea defecto real, SOSPECHA salvo V01, V03, V04 y V05 (reglas del pre-registro sin test).
- GRAVEDAD: 3

### VE2-05
- TÍTULO: El cableado de main() (C6, posición contra referencia) no tiene test; falla en seguro salvo C6
- ARCHIVO:LÍNEA: e_adenda2/leer_posicion_v375e.py main() (dc_ok; `distancias(mascara, mir, pos, pos_ref(g), ...)`)
- QUÉ PASA: V15 y V17 sobreviven; un cableado equivocado de main se vería recién con datos reales (C5 daría exit 3), salvo C6, que quedaría verde.
- CÓMO SE VE EN EL DASHBOARD: invisible. CÓMO REPRODUCIRLO: mutar_ve2.py V15/V17. CONFIANZA: CONFIRMADO. GRAVEDAD: 2

### VE2-06
- TÍTULO: No hay veredicto por tramo (A104), sólo conteo de bloques discordantes
- ARCHIVO:LÍNEA: PREREGISTRO_E.md:273-275 (§8.5 final) y leer_posicion_v375e.py p2_con (bloques_por_tramo)
- QUÉ PASA: El veto, P2-L contra K y la RP se calculan sobre T+O1+O2 juntos; A104 pide medir por tramo. La tasa con que K publica en lejanas es plana por tramo (0,39 / 0,35 / 0,37), así que hoy se mezcla poco, pero el pre-registro no dice qué hacer si el signo cambia entre O1 y O2.
- CÓMO SE VE EN EL DASHBOARD: invisible. CÓMO REPRODUCIRLO: `python -I verificador/ve_tramos.py`. CONFIANZA: CONFIRMADO. GRAVEDAD: 2

### VE2-07
- TÍTULO: Las 4 protegidas que motivan la adenda son solo-OCR y dos son de Suomi NPP antes del 2026-10-09
- ARCHIVO:LÍNEA: PREREGISTRO_E.md §8.1; SCRIPT:SALIDA verificador/ve_protegidas_salida.txt; objetivos_far_v375_salida.txt (hito 2026-10-09 de la referencia)
- QUÉ PASA: Isluga 2026-09-28 05:12 y 2026-10-03 05:18 son VIIRS_SNPP solo-OCR; para ese tramo la referencia avisa que distancia y clase del OCR pueden ser de otra pasada. Su estatus de «protegida de cráter» es dudoso y la RP que decide las cuenta en el veto y en el error de posición.
- CÓMO SE VE EN EL DASHBOARD: invisible. CÓMO REPRODUCIRLO: ve_protegidas.py. CONFIANZA: SOSPECHA (no contrasté con el TIF). GRAVEDAD: 3

### VE2-08
- TÍTULO: La variante «cercano» no es un record completo
- ARCHIVO:LÍNEA: e_adenda2/leer_posicion_v375e.py función variante()
- QUÉ PASA: Cambia distance_class, centroid_dist_km y final_hotspot_dist_km, pero deja centroid_lat/lon, final_hotspot_lat/lon y n_pixels: un record real «cercano» pondría el marcador en el centroide lejano con clase cumbre. El predicado no lo lee, la medición es válida, pero P no es exactamente lo que se implementaría.
- CÓMO SE VE EN EL DASHBOARD: marcador lejano etiquetado como cumbre. CÓMO REPRODUCIRLO: lectura de variante(). CONFIANZA: SOSPECHA. GRAVEDAD: 2

### VE2-09
- TÍTULO: decidir_brazo con un ciclo devuelve un texto vacío
- ARCHIVO:LÍNEA: e_adenda2/leer_posicion_v375e.py decidir_brazo (últimas líneas); mutación V55 sobrevive
- QUÉ PASA: con a vence b, b vence c, c vence a, no_vencidos queda vacío y devuelve «NO RESUELTO ENTRE  (decide Nicolas)». El pre-registro no cubre el ciclo. Improbable.
- CÓMO SE VE EN EL DASHBOARD: invisible. CÓMO REPRODUCIRLO: no hay caso real. CONFIANZA: SOSPECHA. GRAVEDAD: 1

### VE2-10
- TÍTULO: El lector lee artefactos reales por defecto
- ARCHIVO:LÍNEA: e_adenda2/leer_posicion_v375e.py:73-76 (ART) y :558-560 (argparse)
- QUÉ PASA: Sin --art-far y con las rutas de S159/S162/S162b presentes, `python leer_posicion_v375e.py` calcula la vara 1 retrospectiva de cada brazo. La regla de no mirar antes del sello es de convención.
- CÓMO SE VE EN EL DASHBOARD: invisible. CÓMO REPRODUCIRLO: no lo corrí (restricción); lectura de código. CONFIANZA: CONFIRMADO. GRAVEDAD: 2

### VE2-11
- TÍTULO: Referencias internas erradas
- ARCHIVO:LÍNEA: PREREGISTRO_E.md:359 («pendiente (§8.12)», no existe §8.12); e_adenda2/probe-s166-v375e-far.yml:11 («§8.7» para los trozos; son §8.4 y §8.8) y :4 («sellada antes de este disparo»; hoy no está sellada)
- QUÉ PASA: referencias que no llevan a nada. CÓMO SE VE EN EL DASHBOARD: invisible. CÓMO REPRODUCIRLO: `grep -n "8.12" experiments/_s162_v375/PREREGISTRO_E.md`. CONFIANZA: CONFIRMADO. GRAVEDAD: 1

### VE2-12
- TÍTULO: En el error de posición una alerta bajo 1 MW perdida pesa ~5 veces una protegida perdida o una lejana publicada
- ARCHIVO:LÍNEA: PREREGISTRO_E.md:265-268; SCRIPT:SALIDA verificador/ve_pesos_salida.txt
- QUÉ PASA: pos_bajo 4,75-5,33; pos_prot 1; far_tabla 1 (censo). Coherente con la población, pero como el criterio de Nicolás pone a la protegida primero, el paso 3 de la RP quedará gobernado por las alertas bajo 1 MW.
- CÓMO SE VE EN EL DASHBOARD: invisible. CÓMO REPRODUCIRLO: `python -I verificador/ve_pesos.py`. CONFIANZA: CONFIRMADO los pesos; SOSPECHA que sea inconveniente. GRAVEDAD: 2

### VE2-13
- TÍTULO: La RP no exige poder estadístico sobre las lejanas
- ARCHIVO:LÍNEA: PREREGISTRO_E.md:271 (§8.5 paso 5)
- QUÉ PASA: «Cobertura» cuenta pasadas con dato, no pasadas con algún alertado en la caja. Si pocas lejanas tienen alertado, P2-L queda SIN SUSTRATO y la RP se resuelve por «SE QUEDA RADIANTE» sin que las lejanas hayan pesado. El lector imprime con_alertado, pero no condiciona la regla.
- CÓMO SE VE EN EL DASHBOARD: invisible. CÓMO REPRODUCIRLO: lectura del pre-registro. CONFIANZA: SOSPECHA. GRAVEDAD: 2

## SEGUIMIENTOS
- La batería depende de una ruta fija de D: (probar_adenda2.py:618) y falla (no queda SIN DATO) si no está. Confianza alta, fuera de eje.
- `_cumulo_del_mas_radiante` elige la semilla con `max` sobre un set (pipeline/mirova_v750_codigo.py:670-684): con empates exactos de radiancia (I04 saturado) el desempate depende del orden del set. No medí cuántos empates hay. SOSPECHA, gravedad 1.

## VERIFICADO LIMPIO
- Regeneración de la lista: `python -I e_adenda2/objetivos_far_v375.py --data D:\vrp-trabajo\temporales\s159_n\data_main --ref-dest ...\ref --dest ...\gen`; vara: sha256 del autor y cmp byte a byte; control: C-G1/C-G2/C-G3 del propio script salen OK.
- Ancla de medida y grilla (ve_ancla_grilla.py): iguales en 11 de 11 (las 11 diferencias que imprime son la clave `paso`, ausente en la lista; control positivo detecta x0 + 1 m).
- Almacén contra variantes (ve_almacen_variantes.py): 18 de 18 sin cambio, con control positivo (VRP 0 sí cambia); vara: predicado del tablero con node.
- Premisa de lejana contra el radio del tablero: 0 de 329 (ve_far_vs_inner.py).
- Flag apagado en los tres perfiles (pipeline.profile). Workflow clon fiel del de B2 (diff).

## SIN DATO
- Qué hace la RP con los datos reales (prohibido leer).
- Si las 3 pérdidas de VE2-01 también ocurren con cercano medido desde el cráter (documentado sólo para el cercano de X0, Y0 de evaluar.py).
- Vigencia del secreto EARTHDATA_TOKEN; si cada trozo completa en 60 minutos.
- Origen real de la distancia OCR de las 4 protegidas (VE2-07).

## FUERA DE ALCANCE
MODIS y VIIRS 750; la vía misma (sólo su descripción); las lecturas del §5 (magnitud, curva de cenit).

## VEREDICTO GLOBAL: SELLABLE CON CAMBIOS
1. PREREGISTRO_E.md:264 (§8.5 paso 1): el veto cuenta sólo protegidas que K publica y el brazo calla Y que otro brazo sí publica (pérdida atribuible a la posición); las pérdidas de todos los brazos (las 3 OCR de S159, por nombre) se informan aparte como causa de que (a) del §5.4 falle. Alternativa: declarar ex ante que decide la versión con el veto de la tabla sola.
2. PREREGISTRO_E.md:226-227 (§8.4.2) y objetivos_far_v375.py (meta): fijar el sha256 de consolidado_filas_perdidas.csv (2613e7cc03e75c2f6b0be41d11051ae847dece00be817d305b7e77d95bbf59e7) y del respaldo (183aff7f38c6ca9ef93c8e0951f8190dd12be2690d54dbacb7d7acabaaa93568) y decir que 15 lejanas dependen de esa capa.
3. probar_adenda2.py:626-628: sacar los dos `ok(...)` del `else` (quitar la sangría) para que la aserción de main() corra.
4. probar_adenda2.py: tests para pesos distintos de 1 (V01), negativos en la RP (V03), regla de 10 % SIN DATO (V04, V05), C7 sin píxeles (V06), rango CTLF (V08) y el ancla de record_de_la_via contra get_detection_anchor (V50).
5. PREREGISTRO_E.md:273-275 (§8.5): agregar el veredicto por tramo O1 y O2 de P2-L y del paso 3 de la RP, y qué se hace si el signo cambia.
6. leer_posicion_v375e.py:73-76 y :558-560: sin rutas reales por defecto (exigir --art-s159 etc. o un --sellado).
7. Corregir PREREGISTRO_E.md:359 (§8.12) y el comentario del yml (§8.7, «sellada»).
