# caminos.md: por donde podria estar mal cada afirmacion (V33A, verificador)

Escrito ANTES de abrir ningun archivo citado. Base 752d348bc; origin/main de hoy cc32ab1fc
(hora del servidor GitHub: Sun, 08 Nov 2026 14:15:00 GMT). Solo tengo titulo, archivo:linea
o script:salida y gravedad de cada afirmacion; no abri INFORME.md ni razonamientos.

Caminos generales que aplican a todas:
- G1 la cita archivo:linea envejecio: la linea existe en la base pero en origin/main se movio o se arreglo (hay que remapear por contenido en los dos commits).
- G2 el flag o constante se lee de otro lado (perfil YAML, env, override en el caller) y la linea citada es codigo muerto o no ejecuta en produccion (MODIS corre por la via desde S172; el camino K no corre en MODIS).
- G3 la afirmacion es "abierto" heredado de una lista anterior (S160/S175) y nadie comprobo que el codigo de hoy siga igual: la lista envejece hacia el falso positivo.
- G4 el script del auditor mide otra cosa, corre sobre una copia local atrasada o su cero no distingue "no hay" de "no medi".
- G5 la vara: la afirmacion compara contra una vara (paper, MIROVA, regla) que no es la que el codigo declara; o la "gravedad" supone un consumidor del dashboard que no existe.
- G6 el defecto es real en el codigo pero no hay datos que lo activen (latente): entonces es CONFIRMADO EN PARTE con "latente", no FALLA observada.

## [f0] 112 (241 a medias: plataforma muda, codigo 0 en estricto)
- C1 `return 3 if (estricto and cuentan) else 0`: "cuentan" puede ser verdadero cuando una plataforma entera falta; hay que leer que define `cuentan` y si la nota "faltan plataformas enteras" alimenta `cuentan`.
- C2 el modo estricto puede activarse por otra bandera o por la env del workflow nrt.yml, y el exit code que ve Actions puede venir de otra capa (wrapper bash, `continue-on-error`).
- C3 `fetch.py:789 "sin_granulos": False` puede ser el caso correcto (busqueda OK, cero granulos reales) y no "muda"; confundir "sin granulos" con "plataforma muda" seria el error del auditor.
- C4 origin/main pudo cambiarlo despues de la base.
- C5 que signifique "plataforma muda": puede que el nrt.yml tenga un healthcheck aparte que si lo detecta (nrt-healthcheck.yml), y entonces la gravedad baja.

## [f0] 116 (V2-10: dist_km desde el centro, popup dice "al crater")
- C1 `dist[r,c]` puede medirse desde `get_detection_anchor()` (crater efectivo) y no desde el centro: hay que leer como se construye `dist` en process_viirs_mod.py y en los otros dos procesadores.
- C2 el popup de index.html:3159 puede no ser el que muestra VIIRS 750; puede haber otro popup por sensor; diario.html y mosaico.html tienen copias.
- C3 el "centro del volcan" y el "crater" pueden coincidir para los 11 Tier A (volcanoes.yaml vent == centro) y entonces el defecto es de forma.
- C4 la linea pudo moverse en origin/main.

## [f0] 117 (V2-11: VRE suma 6 h por deteccion)
- C1 `DT_HOURS = 6` puede usarse solo para un sensor o solo para display acumulado con rotulo que lo declare (entonces es decision documentada, no defecto).
- C2 la vara: MIROVA calcula VRE por integracion trapezoidal entre pasadas (hay que leer que dice la referencia en documentacion/ antes de llamar "sin base fisica"); si MIROVA tambien usa un dt fijo, REFUTADO en la premisa.
- C3 lineas 2500 y 3319 pueden ser otros usos (tooltip) y no la suma.
- C4 copias en diario.html / mosaico.html pueden diferir.

## [f0] 118 (V2-12: tope 50 GW juzga t_max_k antes de que exista en VIIRS 375)
- C1 `_apply_sanity_cap` puede leer `t_max_i04_k` o `vrp_mw` y no `t_max_k`; o puede tolerar ausencia (`get` con default) y entonces es inocuo.
- C2 el orden 559 vs 564-565 puede estar invertido en origin/main (arreglado).
- C3 el record VIIRS 375 puede llegar a store.py ya con `t_max_k` puesto por process_viirs.py (entonces la copia posterior es redundante y el tope si lo ve).
- C4 el tope de 50 GW puede ser inalcanzable fisicamente (VRP max observado ~ GW) y la gravedad real es 1 latente.

## [f0] 119 (V0b-03: minimo de cumbre 0,003 gobierna el umbral del dETI)
- C1 `c1_deti_summit=_c1_sum` puede ser reasignado dentro de la funcion llamada (un override `c1_deti_summit_override` del perfil) y la linea 1341 ser solo el default.
- C2 el dETI puede tener su propio piso en el perfil (`enable_*`) que se aplica despues.
- C3 la vara: MIROVA en VIIRS 375 no tiene dETI (es propio, D30/D31): entonces "gobierna" es cierto pero el defecto no es de fidelidad sino de diseno propio.
- C4 origin/main pudo separar los pisos.

## [f0] 120 (V0b-02: alerta Lascar 2026-03-04 05:06 fuera de la tabla)
- C1 el grep con "2026-03-04 05:0" puede fallar por formato de fecha (ISO con T, con segundos, zona local vs UTC, 04/03/2026).
- C2 la fila puede estar bajo otro nombre de volcan (A14: `Lascar`, `Láscar`, `LASCAR`).
- C3 la alerta puede estar en el OCR (snapshot_ocr_base.csv) y no en la tabla: entonces "fuera de la tabla" es cierto pero "fuera de la referencia" no.
- C4 la hora puede ser hora local MIROVA o la pasada estar a 05:12 o 04:5x (tolerancia TOL_S).
- C5 la premisa "cota cero negativos sobre -0,8 depende de la referencia" es una inferencia del auditor que no puedo verificar sin su razonamiento: solo verifico la ausencia de la fila.

## [f0] 121 (regla de adopcion de K sin cambio; vigilancia-sombra usa paso 9)
- C1 `git diff --stat` puede omitir cambios si la regla vive en otro directorio (docs/, scripts/) y no en experiments/_s151_prereg_fk_11/.
- C2 vigilancia-sombra.yml:135 puede haberse movido o el workflow estar deshabilitado/archivado en origin/main.
- C3 "sin uso pendiente" es juicio; verifico solo lo factual (diff vacio salvo v1_cobertura, linea 135).

## [f0] 122 (inventario S160 VIIRS y unidades: F2-210, 212, 230 a 236)
- C1 cada constante puede haber cambiado de linea; grep por contenido en base y en main.
- C2 F2-233 (5 clases vs 4 en leyenda): puede que la 5a clase no se use en datos (grep en JSON) o que la leyenda la agrupe a proposito.
- C3 F2-234 (`<= 0` vs `< 0.0`): pueden ser predicados sobre campos distintos (vrp_mw vs dist) y no una inconsistencia.
- C4 F2-235 `np.std` sin ddof: puede ser deliberado (MIROVA .m usa std poblacional? el .m de Octave usa std con N-1 por defecto): la vara es el codigo MIROVA, hay que mirar.
- C5 F2-212 `eti_for_second_pass = fp_diag.get("eti")`: puede que el None se maneje aguas abajo.
- C6 el clasificador f0 puede clasificar por grep de subcadena (A92) y dar "abierto" por una coincidencia espuria.

## [f0] 123 (inventario dependencias: 249, 251, 252, 254, 255)
- C1 nrt-retry.yml puede estar archivado o sin trigger; "solo NASA_DOWN" puede ser por diseno.
- C2 `versions ["2.1","2","1"]` puede ser correcto segun LAADS hoy (no puedo llamar a NASA: SIN DATO en la parte factual externa).
- C3 `earthaccess>=0.9.0` sin pin: hay que ver si existe lock o pin en el workflow (pip install con version).
- C4 sync_mirova_csv.sh:110 `|| continuing`: puede haber un paso posterior que falle si el rebuild fallo.
- C5 255 (cadencias del healthcheck): el script f0_cadencias.py lee runs_nrt-healthcheck.json de insumos (ventana de 49 runs); el "hueco 27,8 h" puede ser un cron a las 12 UTC que Actions atrasa (A: cron de Actions horas tarde, S171); hay que ver si el cron es `0 12 * * *` y los created_at. Un hueco puede ser un run cancelado o la ventana de la API (solo ultimas N paginas).

## [f0] 124 (247 salvo borde: token desconocido sin issue)
- C1 el paso puede tener otro camino que abra issue para "desconocido" (un `exit 1` o un step posterior `if: failure()`).
- C2 el "secret ausente" se resuelve a string vacio en Actions: puede que otro paso anterior falle por token vacio y el workflow se ponga rojo igual (entonces hay aviso aunque no issue).
- C3 origin/main pudo cambiar el bloque.

## [f0] 125 (245 en parte: copia que se encoge avisa y entra igual; union de perdidas 37 filas)
- C1 `|| true` y `mv` puede estar rodeado de un gate anterior que rechace la copia si se encoge mas de X % (hay que leer todo el bloque, no solo 32-36).
- C2 el script f0_245 puede contar llaves perdidas contra una copia local atrasada (insumos del 7-nov) y el numero 37 cambia con la ventana.
- C3 "ninguna alerta" depende de la definicion de alerta (etiquetar del banco) o de un umbral del script: mirar que umbral usa.

## [f0] 126 (Suomi NPP callado 31 h antes; vigilante avisa a las 54 h)
- C1 "cese anunciado": la fecha puede estar mal transcrita; sin fuente externa es SOSPECHA. No puedo llamar a NASA.
- C2 el script puede contar records por `sensor` y confundir VIIRS_SNPP con VIIRS_SNPP_750 (A48) o mezclar hora de pasada con processed_utc.
- C3 el issue #943 (2026-11-04T19:01:09Z): la "54 h" depende de la hora de cese que use; verifico el issue con 1 llamada a la API si hace falta.
- C4 en MIROVA la ausencia puede ser del scraper (Mirova-v1) y no del satelite.

## [f0] 127 (decision 2 por otra via: placebo del 1 % nunca entro)
- C1 el placebo del 1 % puede vivir en otro script (experiments/_s160*, _s157*/otro archivo) y no en evaluar_d25.py.
- C2 MIROVA_DIVERGENCES.md l. 2863 puede haberse movido; buscar por `c8423ce9a`.
- C3 que "S160 pedia" un placebo del 1 % es afirmacion sobre un doc que no debo abrir si es INFORME; puedo leer docs/AUDIT_S160 si existe (es doc del repo, no informe del auditor S175).

## [f0] 128 (V1a-05 en parte: v1_cobertura llego a main; datos de adopcion SIN VERIFICAR)
- C1 el `git log` puede mostrar el commit pero el contenido puede estar en LFS o vacio.
- C2 "datos con que se adopto K" puede estar en otra carpeta (_s153_fk_v2) y entonces si estan.

## [f0] 129 (12 pendientes de proceso F1b sin cambio)
- C1 el diff vacio solo dice que esos archivos no cambiaron; un arreglo pudo entrar en otro archivo (p. ej. docs/MIROVA_DIVERGENCES.md o CLAUDE.md) que marque el pendiente como cerrado.
- C2 varios de los paths pueden no existir en la base (diff vacio por inexistencia, no por igualdad): control: `git ls-tree`.

## [f1] 159 (via muerta en 11 volcanes: INVESTIGAR vs VIGILANCIA_CIEGA)
- C1 `evaluar` puede tener otra rama que convierta "0 records de la via en los 11" en INVESTIGAR; la mutacion M2b del auditor puede mutar el estado que no es el de produccion.
- C2 el root_base del auditor en vrp-temporales/f1 puede estar atrasado o no existir ya (temporal de otro agente, S173).
- C3 la clase del issue puede decidirse en el workflow (vigilancia-guardia-modis.yml) y no en el script.
- C4 la via "muerta" en los 11 puede ser fisicamente indistinguible de "sin pasadas nocturnas" (ventana de 1 dia): entonces INVESTIGAR podria ser peor (falso rojo).

## [f1] 160 (JSON ausente vacia la guardia; aviso culpa a los 11)
- C1 `except FileNotFoundError` puede ser por volcan (lazo) y no global: hay que leer si el try envuelve el lazo entero.
- C2 `cargar_nuestros` del banco puede ser la que lanza, y puede tener su propio manejo.
- C3 en produccion el JSON ausente puede ser imposible (el workflow lo genera antes) y el defecto es latente.
- C4 origin/main pudo arreglarlo.

## [f1] 161 (pixeles de la via sin vrp_mw por pixel)
- C1 la lista `pix` puede llevar otro nombre de campo (`vrp`, `vrp_pix_mw`, `radiancia`) y el censo busca `vrp_mw` literal: falso positivo de nombre.
- C2 el consumidor (store.py comentario S165 V375-E, frontend) puede no necesitar vrp por pixel en MODIS; entonces es de forma.
- C3 los datos del censo son de e75a7d52d (copia en vrp-temporales/f1/datos): pueden estar atrasados; mirar data/ de la base y de main.
- C4 la vara: MIROVA suma pixeles (S158); si el frontend suma `vrp_mw` por pixel para mostrar algo, la ausencia si se ve.

---
sha256 (antes de esta linea): 56836b262007afbaa0797a82d98810b633affeb0eee3f3ccbdc287cbfb264833
hora del servidor GitHub al cerrar: Sun, 08 Nov 2026 14:15:00 GMT (ultima llamada); no se vuelve a editar.
