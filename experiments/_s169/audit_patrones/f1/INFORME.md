# Auditoría S169, frente VIIRS 750 (V750-B del 2026-11-03, V750-A, rama de la ROI)

## 1. Encabezado

- Fecha y hora del servidor: viernes 2026-10-30, 04:02 UTC (`date -u` en esta sesión; 03:44 UTC al empezar).
- Commits sobre los que medí: árbol `01ffd277b` (rama `claude/s162-viirs750-2-918174`, el que me dieron en `arbol/`); `main` `443da8649` para lo que el árbol no trae (`experiments/_s159/n`, `scripts/banco_paridad.py` de main, `pipeline/mirova_v750_codigo.py`, `volcanoes.yaml`, `frontend/index.html`); rama de la ROI `3c5c494b9` (en `roi/`); tags `s162-v750b-sellado`, `s162-v750b-adenda2-sellada`, `s167-v750b-adenda3-sellada`, `s161-d25-lectura`.
- Modelo y esfuerzo: Sonnet 5.5, esfuerzo bajo (el que fijó el entorno).
- CARPETA: `D:\vrp-trabajo\temporales\s169_audit_patrones\f1_v750\` (scripts de la auditoría con su salida `*_salida.txt` al lado; copias de insumos de main en `bp_main_443da8649.py`, `mv_main_443da8649.py`, `vy_main.yaml`, `idx_main_443da8649.html`, `grilla_tif_salida_main.txt`; árbol de pruebas `roi_run/`).
- Lo que NO miré (el silencio no es "todo bien"):
  - No corrí el generador, el arnés, el medidor de V750-A ni ningún despacho (límite de recursos). Todo lo que sólo se verifica así va a SIN DATO.
  - No leí línea por línea `adenda2/leer_posicion_v750b.py` (312 líneas, informa y no decide), `bateria_regla_v750b.py`, `mutaciones_regla_s6_v2.py`, `prueba_local_510.py`, `evaluar_v750a.py` (893 líneas) fuera de lo citado, ni `probar_adenda1/2.py`. Sí revisé cómo clasifican "atrapada" los medidores de V750-A, de la adenda 3 y de la batería de V750-B.
  - No miré `experiments/_s159/n/probe_n.py` ni `experiments/_s158_audit_r2/` más allá de lo que el probe importa de ellos.
  - No abrí `data/sombra_codigo_mirova/`. Sin red, sin credenciales.
  - El `.github/workflows/probe-s162-v750b.yml` lo leí en el tag y en el árbol (idénticos); no verifiqué cómo se comporta GitHub Actions con él.

## 2. En una pantalla

- No encontré nada de gravedad 5 ni 4. Los números sellados (5 sha256 de los lectores y del evaluador) coinciden con los blobs de los tags; las cajas que mide el probe (B0, B1, B2, B3, B5) son idénticas celda por celda a las que arma la vía (`caja_roi`) en los 11 volcanes (246.895 celdas, 0 distintas); el sha256 de los objetivos no depende de CRLF.
- Lo más serio para el 2026-11-03 son cinco defectos de gravedad 3: (P1-01) el lector del §4 corre desde un worktree 1.446 commits atrás de main, con su propio predicado del tablero; (P1-02) `--leer-con-faltantes` abre la compuerta aunque el control del censo haya corrido y fallado; (P1-03) el generador cambia de población si el shell trae `VRP_PROFILE` de un A/B diurno; (P1-04) el generador no avisa si `--data` es viejo; (P1-05) la salida del veredicto no lleva la identidad de sus insumos y se puede releer y pisar.
- V750-A: el medidor clasifica bien las caídas (no cuentan como atrapadas; control CAIDA verificado en su salida). Pero la batería actual (77 escenarios) nunca se corrió completa con M63 a M85; los resultados son de 61 escenarios (M1 a M62) y de 13 (M63 a M80), M81 a M85 sin salida.
- Rama de la ROI: 21 de 21 pruebas reproducidas; mis 10 mutaciones del script: 5 atrapadas por aserción (mapa brazo a tipo), 5 NO atrapadas (todo `main()`: `--escribir`, qué se escribe, CRLF, el rechazo de duplicados, `choices`).
- Informe completo en `D:\vrp-trabajo\temporales\s169_audit_patrones\f1_v750\INFORME.md`; tabla en `hallazgos.csv` (misma carpeta).

## 3. Hallazgos (ordenados por gravedad)

### P1-01

- TÍTULO: El lector del 2026-11-03 corre desde un worktree atrasado y evalúa "publica" con el tablero de ese worktree, no con el de main del día
- ARCHIVO:LÍNEA: `experiments/_s162_v750b/r4/INFORME.md:70-71` (R = raíz del worktree, O = árbol de R4); `experiments/_s162_v750b/analizar_v750b.py:36-42` (RAIZ = AQUI.parents[1], importa `scripts/banco_paridad`, `clase_mirova`, el oráculo); `scripts/banco_paridad.py` (`HTML = ROOT/frontend/index.html`, `correr_node`). Medición: `diff_clase_mirova_rama_vs_main.txt`, `diff_oraculo_rama_vs_main.txt`.
- QUÉ PASA: El generador (R4/arbol) y el runner usan main del día, pero el §4 manda leer con `python $R/adenda3/leer_n3_v750b.py`, y ese script resuelve `scripts/`, `frontend/index.html` y el oráculo desde la raíz del worktree `s162-viirs750-2-918174`. Esa rama está 1.446 commits detrás de `origin/main` (`git rev-list --count`). La pregunta física "¿el operador vería esta alerta?" se contesta ejecutando con node el `isValidDetection` del `index.html` del worktree, no el de main. Hoy la diferencia es inocua (el `index.html` difiere en 3 líneas de comentario o aviso, el oráculo es idéntico, `clase_mirova` sólo agrega funciones), pero si el predicado del tablero cambia en main antes del 11-03 el lector no lo verá. El control "K = producción" compara `pub_prod` (calculado por el generador con el tablero de main) con el K publicado por el lector (tablero del worktree): si divergen más de 1 % o hay una protegida cae la compuerta (se pierde el run ya gastado); si divergen menos, esas pasadas salen en silencio de todos los brazos.
- CÓMO SE VE EN EL DASHBOARD: invisible si no cambia el predicado; si cambia, el veredicto mide una publicación que el operador ya no vería.
- CÓMO REPRODUCIRLO: `git -C "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile" rev-list --count claude/s162-viirs750-2-918174..origin/main` (dio 1446); `diff <(tr -d '\r' < arbol/frontend/index.html) <(tr -d '\r' < idx_main_443da8649.html)` (3 hunks, sólo comentarios y aviso). Para el efecto real: antes de leer, comparar el sha256 de `frontend/index.html` y `scripts/banco_paridad.py` del worktree contra los de `$R4/arbol`.
- CONFIANZA: CONFIRMADO la estructura (el comando del §4 y el atraso de la rama); SOSPECHA el efecto el 11-03.
- GRAVEDAD: 3 (puede dejar la lectura indecidible tras el runner o descartar pasadas sin aviso).

### P1-02

- TÍTULO: `--leer-con-faltantes` abre la compuerta aunque el control del censo haya corrido y FALLADO
- ARCHIVO:LÍNEA: `experiments/_s162_v750b/analizar_v750b.py:406-416` (en especial l. 414: `censo_pasa = censo_ok or (a.censo_omitido_solo_pruebas and not censo_pedido) or bool(a.leer_con_faltantes)`); texto: `PREREGISTRO_V750B.md:212-214` ("si ... el control del censo no se puede correr").
- QUÉ PASA: El pre-registro autoriza leer con faltantes cuando el censo "no se puede correr". El código lo autoriza también cuando el censo corrió y B0 o B1 dieron DISTINTO del censo S159, que es la señal de que el oráculo cambió (el control más duro de todo el A/B). Basta cualquier motivo en `--leer-con-faltantes` (por ejemplo por cobertura) para que el censo caído no cierre. La línea "control B0 y B1 = censo S159 ... FALLA" sale impresa y el veredicto lleva la marca, pero hay veredicto. La bandera de pruebas sí se corrigió para este caso (VB3-06, l. 412); la de faltantes no.
- CÓMO SE VE EN EL DASHBOARD: invisible; se ve en la salida del veredicto como una línea "FALLA" y una marca "[LEÍDO CON FALTANTES: ...]", código de salida 5.
- CÓMO REPRODUCIRLO: sin ejecutar (necesita artefactos): con una escena en que `cnt` tenga un "DISTINTO", llamar `analizar_v750b.py ... --leer-con-faltantes "x"` y mirar si imprime "ROI elegida". Equivalente lógico: línea 414 con `censo_ok=False`, `censo_pedido=True`, `leer_con_faltantes="x"` da True.
- CONFIANZA: CONFIRMADO (leído; no ejecutado).
- GRAVEDAD: 3 (puede torcer un veredicto si un humano usa la bandera por cobertura sin ver que el censo falló).

### P1-03

- TÍTULO: La población del generador depende del `VRP_PROFILE` del shell y el §3 de R4 no lo fija ni lo imprime
- ARCHIVO:LÍNEA: `scripts/banco_paridad.py:60` (main 443da8649: `os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")`); `scripts/auto_audit_weekly.py:249-254` (`es_pasada_diurna_descartada` usa `ENABLE_DAYTIME_MODIS` y `flag_viirs_diurno()`); `pipeline/diurno.py` (`flag_viirs_diurno` lee `pipeline.profile`); `pipeline/profile.py:35` (`os.environ.get("VRP_PROFILE")`); perfiles con `enable_daytime_viirs: true`: `pipeline/profiles/_s151_ab_diurno_on.yaml:29`, `_s154_ab_diurno_k_on.yaml:15`; `r4/INFORME.md` §3 (exporta TEMP, TMP, PYTHONIOENCODING, no VRP_PROFILE).
- QUÉ PASA: `setdefault` respeta un `VRP_PROFILE` ya presente. Si el shell del 11-03 trae el de un A/B diurno de sesiones anteriores, `cargar_nuestros` deja pasar las pasadas VIIRS diurnas. La lista de objetivos sale con pasadas de día; en el analizador (`analizar_v750b.py:206`) toda pasada observada con `dayflag != 0` es SIN DATO, así que la cobertura pasa del 2 % y la compuerta cierra después de gastar el runner. El propio `diurno.py` declara este consumidor indirecto ("cualquier cifra que produzca bajo un perfil con el flag encendido no se compara con las de hoy"). El generador no imprime qué perfil usó.
- CÓMO SE VE EN EL DASHBOARD: invisible; aparece como "SIN DATO por motivo: ... diurna" y compuerta cerrada (exit 3) tras 2 h de runner.
- CÓMO REPRODUCIRLO: con red y datos (no lo corrí): `VRP_PROFILE=_s154_ab_diurno_k_on python experiments/_s162_v750b/objetivos_v750b.py --data data/mirova_equivalent --ref-dest <c> --hasta 2026-10-29` y comparar el número de objetivos y el sha256 contra el mismo comando sin la variable. Barato: `env | grep VRP_PROFILE` antes de generar.
- CONFIANZA: CONFIRMADO la cadena de código (leída); SOSPECHA el efecto (no ejecutado).
- GRAVEDAD: 3 (lista distinta sin rastro; cierre de compuerta después de gastar el runner).

### P1-04

- TÍTULO: El generador no avisa si `--data` es viejo o incompleto (la lista sale más corta sin aviso)
- ARCHIVO:LÍNEA: `experiments/_s162_v750b/objetivos_v750b.py:89-127` (ninguna comprobación de la fecha máxima de los records contra `--hasta`); `r4/INFORME.md:25-26` (lo reconoce: "con datos viejos la lista sale más corta sin aviso"); `PREREGISTRO_V750B.md:98-101` (ventana hasta el 2026-11-02 12:59).
- QUÉ PASA: La ventana de O termina el 2026-11-02 pero nada compara el último record de cada volcán con esa fecha. Si el NRT se atrasó o el `git archive` se hizo con un `origin/main` sin fetch, faltan noches al final de la ventana y el script imprime un total plausible. Es el patrón de la regla 6 del workspace (pipeline zombie: el run verde no prueba datos). El número que sí se imprime ("records V750 nocturnos en ventana") no se compara con nada.
- CÓMO SE VE EN EL DASHBOARD: invisible; el A/B se decide sobre una ventana recortada y declarada completa.
- CÓMO REPRODUCIRLO: con los datos del árbol del 2026-10-29 el ensayo dio 5.654 objetivos contra más en main (INFORME §1). Comando de comprobación que falta: para cada `data/mirova_equivalent/<vol>.json`, `max(datetime_utc)` de records V750 y compararlo con 2026-11-02 12:59.
- CONFIANZA: CONFIRMADO (código leído: no hay la comprobación; el ensayo del INFORME lo documenta).
- GRAVEDAD: 3 (recorta la población sin que nadie lo vea; no torcería por sí solo un veredicto, pero lo toma sobre menos noches).

### P1-05

- TÍTULO: El veredicto no registra la identidad de sus insumos, se puede releer con argumentos distintos y la salida se pisa
- ARCHIVO:LÍNEA: `experiments/_s162_v750b/analizar_v750b.py:185,198-200,203-204` (`--salida` por defecto en la carpeta sellada, `write_text` sin exclusividad; la primera línea de salida sólo da conteos); `adenda3/leer_n3_v750b.py:149-152` y `adenda1/leer_v750b.py:39` (misma convención); `PREREGISTRO_V750B.md:211` ("se lee una sola vez").
- QUÉ PASA: Ningún sha256 de `objetivos_v750b.json`, del censo, del lector ni de la carpeta de artefactos entra al texto del veredicto (sólo el prefijo del sha del analizador en la cabecera de la adenda 3). `--art`, `--objetivos`, `--sin-granulo`, `--censo-art`, `--censo-objetivos` y `--leer-con-faltantes` son libres. Releer con otro subconjunto de `--art` o con otra marca deja un archivo que sustituye al anterior en la misma ruta, y nada lo delata. El pre-registro dice "se lee una sola vez" pero eso es una convención.
- CÓMO SE VE EN EL DASHBOARD: invisible; la procedencia de la ROI que se llevará a `grillas_mirova.yaml` no es reconstruible desde el archivo de veredicto.
- CÓMO REPRODUCIRLO: leer el código: `grep -n "sha256" analizar_v750b.py` sólo muestra el del evaluador, el del archivo sin gránulo y la cabecera de la adenda 3. Correr dos veces con el mismo `--salida` y comparar.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 3 (permite elegir la lectura después de ver el resultado, sin dejar rastro).

### P1-06

- TÍTULO: La regla N-3 corta por fecha (2026-10-09) pero el arreglo del OCR de Suomi NPP ocurrió el 2026-10-09 a las 14:01 UTC
- ARCHIVO:LÍNEA: `adenda3/leer_n3_v750b.py:61-64` (`o["hora_utc"][:10] < HITO_N3`); `adenda3/ADENDA3_V750B.md:1-31` (§1 y §2: "antes del 2026-10-09"); `r4/ensayo_20261029/gen1_salida.txt` (hito: "Arreglo en Mirova-v1#20, 2026-10-09 14:01 UTC").
- QUÉ PASA: Físicamente, una alerta sólo del OCR de Suomi NPP puede traer la imagen de otra pasada hasta que el scraper se arregló, a las 14:01 UTC del 9 de octubre. Las pasadas nocturnas de Suomi NPP del 2026-10-09 (entre 00:00 y 14:01 UTC) ocurren antes del arreglo pero no son N-3, así que una protegida sólo-OCR de ese día vetaría a un brazo aunque pueda ser de otra pasada. La adenda 3 §2 fija "anterior al 2026-10-09" y lo prueba (N2: el borde veta); es una decisión de Nicolás ("Sí a todo"), pero el motivo físico escrito apunta a un instante, no a un día. Lo que no está medido es cuántas protegidas sólo-OCR hay ese día.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: sobre la lista del 11-03: `[o for o in obj if o["protegida"] and not o["alerta_tabla"] and o["sensor"]=="VIIRS_SNPP_750" and o["hora_utc"].startswith("2026-10-09")]`.
- CONFIANZA: SOSPECHA (falta contar en la lista real).
- GRAVEDAD: 2.

### P1-07

- TÍTULO: El pre-registro promete informar "por tramo" #535 y la adopción de K; el analizador sólo estratifica por cenit
- ARCHIVO:LÍNEA: `PREREGISTRO_V750B.md:106` ("Cortes informados por tramo: #535 (no separa brazos), adopción de K (2026-10-18 09:57 UTC)"); `analizar_v750b.py:485-495` (único tramo: cenit de 10 grados); `grep -n "535\|2026-10-18\|adopci" analizar_v750b.py` no da nada.
- QUÉ PASA: La ventana T u O cruza #535 (2026-08-28 23:00 UTC, regla A104 del proyecto: una métrica con ventana que cruza #535 mezcla dos regímenes). El texto afirma que se informa por tramo y que "no separa brazos"; el código no tiene cómo comprobarlo. La afirmación queda como creencia (regla A111).
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: el `grep` de arriba.
- CONFIANZA: CONFIRMADO (texto contra código).
- GRAVEDAD: 2.

### P1-08

- TÍTULO: "Si se mergeó el arreglo de FALSO_POSITIVO, se informa con y sin": el arreglo está mergeado y nada informa con y sin
- ARCHIVO:LÍNEA: `PREREGISTRO_V750B.md:112-113`; `scripts/clase_mirova.py` en main 443da8649 (`resumir_pasadas`, #903, commit `744d8190b`); `experiments/_s159/n/01_poblacion.py:111` (`prot = any(alerta_protegida(f) for f in ref)`, por fila).
- QUÉ PASA: El pre-registro condiciona un informe "con y sin" al merge del arreglo por pasada (la tabla manda si dice FALSO_POSITIVO o RUTINA y el OCR dice ALERTA). `git log` muestra el arreglo en main (744d8190b, #903). La población sellada sigue usando la definición por fila y no hay variante. El propio comentario de `clase_mirova.py` dice que el caso es "latente", 0 casos medidos en la auditoría de Mirova-v1; por eso gravedad baja.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `git log origin/main --oneline --grep="#903"` y `grep -n "FALSO_POSITIVO" analizar_v750b.py` (vacío).
- CONFIANZA: CONFIRMADO (condición cumplida, informe ausente); SOSPECHA el efecto sobre un veredicto.
- GRAVEDAD: 2.

### P1-09

- TÍTULO: El analizador hashea el evaluador sobre bytes crudos, sin normalizar fin de línea, y R4 no dice cómo producir esa copia
- ARCHIVO:LÍNEA: `analizar_v750b.py:67-68` (`hashlib.sha256(crudo)`); `r4/INFORME.md:70` (`EV=D:/vrp-trabajo/temporales/evaluar_d25_s161.py`, sin receta); este equipo: `git config` de sistema con `core.autocrlf=true`.
- QUÉ PASA: Los otros sha256 del flujo (analizador, lectores, compañero) se normalizan a LF (`sha_lf`); el del evaluador no. Un `git checkout s161-d25-lectura` en Windows lo deja con CRLF y la lectura se detiene con AssertionError después del runner. Hoy la copia de D: está bien (sha `2e557697...`, 0 CR, medido). Es la vía P-A clásica, pero falla cerrada.
- CÓMO SE VE EN EL DASHBOARD: invisible; traceback de `cargar_signos`.
- CÓMO REPRODUCIRLO: `verificar_shas_selladas.py` (blob del tag: 0 CR, hash correcto); `sha256sum D:/vrp-trabajo/temporales/evaluar_d25_s161.py`.
- CONFIANZA: CONFIRMADO el código; SOSPECHA que alguien la regenere mal.
- GRAVEDAD: 2.

### P1-10

- TÍTULO: Una protegida "fuera del gránulo" o "sin cráter" sale del denominador y de P1 sin frenar la lectura, y el probe sale 0 con ella
- ARCHIVO:LÍNEA: `probe_v750b.py:149-151` y `277-278` (`volcan_fuera_del_granulo` no cuenta como `faltan`); `analizar_v750b.py:152-160,228-230,233` (el analizador la lista por nombre, sin condicionar `cob_ok`); `PREREGISTRO_V750B.md:119-122`.
- QUÉ PASA: El diseño declara "no observada" aparte, pero una protegida de MIROVA existe porque el gránulo miraba el volcán; que el probe la declare fuera (distancia mínima mayor a 5 km del centro de la grilla) es raro y puede delatar un gránulo mal asignado. Esa protegida no puede vetar a ningún brazo. Se imprime por nombre (no es ciega), pero no hay umbral que pare la lectura.
- CÓMO SE VE EN EL DASHBOARD: invisible; una línea "protegidas no observadas (fuera del denominador, por nombre)".
- CÓMO REPRODUCIRLO: lectura del código; en la salida real mirar esa línea antes de leer el veredicto.
- CONFIANZA: SOSPECHA (de diseño; no sé cuántas habrá).
- GRAVEDAD: 2.

### P1-11

- TÍTULO: V750-A: la parte local del §6.1 se lee de un archivo de texto cualquiera, sin atarlo al módulo ni al commit
- ARCHIVO:LÍNEA: `experiments/_s162_v750a/evaluar_v750a.py:240-258` (`leer_equivalencia_local`); `forjar_equivalencia_local.py`.
- QUÉ PASA: La compuerta lee la salida impresa de `equivalencia_v750a.py` con regexes (`VERDE: E1 1020 casos, E3 10 recortes`, `mutaciones: TODAS COMO SE ESPERA`, seis nombres, `control_que_se_cae ... caída`). Un archivo escrito a mano con esas líneas devuelve True (medido). Tampoco lleva sha256 del módulo candidato ni commit, así que una salida VERDE de un módulo anterior pasa.
- CÓMO SE VE EN EL DASHBOARD: invisible; "§6.1 equivalencia: CUMPLE (... prueba local: verde ...)".
- CÓMO REPRODUCIRLO: `PYTHONIOENCODING=utf-8 python -I forjar_equivalencia_local.py` (salida: ausente False, roja False, forjado True).
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2 (V750-A no se despacha el 11-03; es disciplina del operador).

### P1-12

- TÍTULO: V750-A: el medidor de mutaciones nunca corrió completo contra la batería actual
- ARCHIVO:LÍNEA: `mutar_evaluar_v750a.py:38-234` (M1 a M85); salidas: `mutar_evaluar_v750a_salida.txt` ("de 61", M1 a M62), `mutar_evaluar_v750a_posicion_salida.txt` (13 escenarios, M63 a M80); `probar_evaluar_v750a_salida.txt` (77 escenarios); `PREREGISTRO_V750A.md:284-286` ("Falta: la corrida completa del medidor").
- QUÉ PASA: Las 85 mutaciones del script contra 77 escenarios no tienen una corrida única. M81 a M85 (del verificador limpio de posición) no tienen salida en ningún archivo (`grep -l "M81\|M85"` sólo da el script). M63 a M80 se midieron con `--escenarios E61..E73`, que el script llama "no reemplaza la corrida entera". La corrida del 2026-10-28 13:50 UTC "completa" es la que ocupa los cupos hoy (`medidor_todo4.log`, no abierto). El pre-registro lo declara, así que no es un error de honestidad; es lo que falta para decir "85 de 85".
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `grep -l "M81\|M85" experiments/_s162_v750a/*.txt` (vacío).
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2.

### P1-13

- TÍTULO: Rama de la ROI: la prueba cubre el mapa brazo a tipo pero no `main()`; "4 mutaciones atrapadas" no tiene instrumento en la rama
- ARCHIVO:LÍNEA: `scripts/roi_v750b_a_grillas.py:64-76` (`main`, `--escribir`, `write_text`); `tests/test_roi_v750b_variantes_s169.py` (ninguna prueba llama `main`); mensaje del commit `3c5c494b9` ("4 mutaciones del script atrapadas por aserción"; `git show --stat` no lista ningún script de mutación).
- QUÉ PASA: Medí 10 mutaciones propias (`mutar_roi_propio.py`) con clasificador validado (identidad verde; control CAIDA da caída; atrapada sólo si todas las fallas son aserción): ATRAPADAS m1 (B2 a sens), m2 (B4 sin Tupungatito), m3 (B3 a def), m4 (B5 a sens), m5 (sin comentario). NO ATRAPADAS: m6 (el modo sin `--escribir` escribe igual), m7 (escribe el contenido viejo), m8 (escribe CRLF), m9 (acepta una línea de volcán repetida), m10 (`choices` sin B5). Es decir, la garantía "sin `--escribir` sólo muestra el diff" y "escribe lo que mostró" no está vigilada, justo la parte que toca `pipeline/grillas_mirova.yaml` de producción (regla A45).
- CÓMO SE VE EN EL DASHBOARD: invisible hasta que la ROI equivocada llegue a producción.
- CÓMO REPRODUCIRLO: `PYTHONIOENCODING=utf-8 python -I mutar_roi_propio.py` desde la carpeta (usa `roi_run/`, un árbol armado con la rama, `pipeline/mirova_v750_codigo.py` y `volcanoes.yaml` de main 443da8649); salida en `mutar_roi_propio_salida.txt`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2.

### P1-14

- TÍTULO: Los dos generadores bajan la referencia viva de Mirova-v1 por separado; el control puede caer por una fila nueva entre uno y otro
- ARCHIVO:LÍNEA: `adenda2/objetivos_supl_v750b.py:115-120,152-161`; `objetivos_v750b.py:95-99`; `r4/INFORME.md:60-61` (gen2 después de gen1 con el mismo `--ref-dest`).
- QUÉ PASA: Cada generador llama a `01_poblacion.main()`, que descarga `registro_vrp_consolidado.csv` y `registro_vrp_ocr.csv` del remoto en ese momento (el scraper actualiza cada 5 min y cada hora el OCR). Si una fila de las últimas noches cambia entre las dos corridas, el control de la adenda 2 sale "DISTINTAS" y no escribe (cae cerrado). Costo: tiempo y un reintento; si cambia sólo una pasada `far_ref`, la lista suplementaria sale de una referencia distinta de la sellada sin que el control lo vea.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: comparar el `referencia remota: {...}` impreso por `gen1_salida.txt` y `gen2_salida.txt` (los dos sha de archivos).
- CONFIANZA: SOSPECHA.
- GRAVEDAD: 2.

### P1-15

- TÍTULO: `poblacion_completa.json` lleva un `data_records` escrito a mano que no corresponde al `--data` usado
- ARCHIVO:LÍNEA: `experiments/_s159/n/01_poblacion.py:144-146` (main 443da8649: `"data_records": "origin/main " + "533398f8f"`).
- QUÉ PASA: El metadato de procedencia del archivo que se commitea con los objetivos dice siempre `533398f8f`, cualquiera sea la carpeta de datos. Quien audite después la procedencia leerá un commit que no es.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `sed -n 144,146p` del archivo (en `git show 443da8649:experiments/_s159/n/01_poblacion.py`).
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 1.

### P1-16

- TÍTULO: En Windows, `poblacion_completa.json` y `poblacion_supl.json` salen con CRLF y su sha256 no es el del texto (latente, nadie los hashea)
- ARCHIVO:LÍNEA: `01_poblacion.py:143-147` (`indent=0` más `write_text`); `adenda2/objetivos_supl_v750b.py:162` (renombra); `r4/armar_rama_disparo.sh:36-38` (`hash-object --no-filters` conserva los bytes).
- QUÉ PASA: Medido (`crlf_generadores.py`): con `indent=0` hay 34 CR en 34 LF y el sha256 de los bytes (967de58b...) difiere del del texto (196a475b...); los objetivos y `sin_granulo` (una sola línea) tienen 0 CR y coinciden. Hoy ningún lector hashea la población, así que no tuerce nada. Si más tarde una verificación en Linux compara el sha del archivo con el del generador, dará distinto.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `PYTHONIOENCODING=utf-8 python -I crlf_generadores.py`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 1.

### P1-17

- TÍTULO: Aplicar la ROI dos veces deja el comentario del YAML diciendo otro brazo
- ARCHIVO:LÍNEA: `scripts/roi_v750b_a_grillas.py:56-60` (el comentario se reescribe sólo si aparece el texto viejo).
- QUÉ PASA: B4 y luego B1 deja valores `sens` pero el comentario "Puesto por la lectura de V750-B: brazo B4"; B4 y luego B0 deja `def` con el comentario de B4; el resultado de B4 y luego B0 no es el archivo original. Medido en `roi_doble_aplicacion.py`.
- CÓMO SE VE EN EL DASHBOARD: invisible; el YAML de producción tendría una procedencia falsa.
- CÓMO REPRODUCIRLO: `PYTHONIOENCODING=utf-8 python -I roi_doble_aplicacion.py`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 1.

### P1-18

- TÍTULO: `equivalencia_v750a.py` llama "no existe todavía" a cualquier ImportError, incluido uno interno del módulo candidato
- ARCHIVO:LÍNEA: `experiments/_s162_v750a/equivalencia_v750a.py:196-200`.
- QUÉ PASA: `except ImportError` sobre `importlib.import_module` lee igual "módulo ausente" y "el módulo existe y falla al importar una dependencia"; sale 2 con el texto "ROJA: el módulo ... no existe todavía". Confunde al lector humano, no cambia un veredicto.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: lectura del código.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 1.

### P1-19

- TÍTULO: `mutar_bateria.py` (V750-B) cuenta ATRAPADA sin exigir el código de salida 1
- ARCHIVO:LÍNEA: `experiments/_s162_v750b/mutar_bateria.py:90-95`.
- QUÉ PASA: Clasifica PASA si rc 0, CAÍDA si hay Traceback en algún `stdout.txt` o falta "FALLAS" en la línea, y ATRAPADA en cualquier otro caso, sin mirar rc. El medidor de V750-A y el de la adenda 3 sí exigen rc 1 y la línea de fallas. Una salida con "FALLAS" y rc distinto de 1 sin Traceback (por ejemplo una salida nativa) contaría como atrapada. No encontré un camino concreto que lo produzca.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: lectura del código.
- CONFIANZA: SOSPECHA.
- GRAVEDAD: 1.

## 4. SEGUIMIENTOS (fuera de mi eje, o a decidir por quien orquesta)

- `adenda1/leer_v750b.py:61-75`: con `--leer-con-faltantes`, la marca se agrega a cada línea que empieza con "== " y se reescribe el archivo de salida; no revisé el caso con salida vacía (confianza baja).
- Adenda 3, reemplazo 3 de `adenda3/leer_n3_v750b.py:82-92`: la lista aparte de N-3 sale de `oks`, es decir sin las pasadas con K distinto de producción (`analizar_v750b.py:298`); una N-3 con K distinto no se lista. Gravedad 1, SOSPECHA.
- `_s162_v750a/evaluar_v750a.py:211-214` (`diag_valido`): `except (KeyError, TypeError)` convierte un error de programa en "diagnóstico inválido" (SIN DATO) sin dejar traza. Gravedad 1.
- `r4/armar_rama_disparo.sh:42-45`: el chequeo "diff contra main fuera de V750-B y del workflow" sólo imprime; sale 0 aunque no esté vacío. Los sha256 impresos no se comparan con los del generador (se hace a ojo). Gravedad 1.
- Si `adenda3/mutar_adenda3.py` o `_s162_v750a/mutar_evaluar_v750a.py` se interrumpen a mitad, las copias `_mut_*` quedan dentro de la carpeta sellada (`finally` no corre ante un kill). Gravedad 1.
- Estado del equipo: C: con 18 GB libres y D: con 19 GB libres al empezar (sobre el umbral de 3 GB); no hubo parada.

## 5. VERIFICADO LIMPIO (con la vara contra la que lo verifiqué)

1. Las 5 constantes sha256 de los lectores y del evaluador son las de los blobs de los tags (0 CR en cada blob; control negativo: `probe_v750b.py` da DISTINTO). Vara: el blob del tag, no el árbol. `python -I verificar_shas_selladas.py` (`verificar_shas_selladas_salida.txt`).
2. `probe-s162-v750b.yml` del tag = el del árbol (diff vacío), 0 CR, y la línea `  OBJETIVOS: "experiments/_s162_v750b/objetivos_v750b.json"` aparece exactamente 1 vez, que es lo que exige `armar_rama_disparo.sh:42-43`. Vara: la expresión exacta del script. Los tres .py (probe, generador, analizador) del tag = los del árbol.
3. Los objetivos y `sin_granulo` no dependen de CRLF: `json.dumps` sin indent no emite saltos de línea (0 CR, 0 LF medidos) y su sha256 de bytes = el del texto; control positivo en el mismo script: la población con `indent=0` sí trae CR (`crlf_generadores_salida.txt`). Por eso el sha256 de `sin_granulo_v750b.json` contra `objetivos_v750b.json` se cumple en Windows y en el runner.
4. Ni la carpeta de V750-B del tag `s167-v750b-adenda3-sellada` ni la de la rama traen archivos generados (`objetivos_v750b.json`, `poblacion_*.json`, `sin_granulo_*.json`): `git ls-tree` sólo da los .py y verificadores. Un `rc != 0` del generador no puede dejar pasar archivos viejos a `armar_rama_disparo.sh`.
5. Cajas: `probe_v750b.cajas()` (extraída con ast) contra `MV.caja_roi` de la vía para los 11 volcanes y los 5 tipos (B0 def, B1 sens, B2 crater, B3 inner, B5 corona): 246.895 celdas comparadas, 0 distintas; la grilla del generador (`02_seleccion.grillas`) y la de `grillas_mirova.yaml` coinciden en ul_x y ul_y (diferencia 0,000 m) y en la celda del cráter (p. ej. Cordón Caulle (23, 30), Tupungatito (27, 30)); control positivo: correr el cráter una celda da 14 celdas distintas. Vara: la función de la vía de main 443da8649. `equivalencia_cajas_probe_vs_via_salida.txt`. Esto prueba que lo que V750-B mide es lo que la vía ejecutaría, para B0 a B5 como están escritos.
6. `inner_radius_km` de `frontend/index.html` (lo que usa B3 del probe) = el de `volcanoes.yaml` (lo que usa la vía y la prueba de la rama) en los 11 volcanes; control positivo: cambiar uno se ve (`inner_yaml_vs_html_salida.txt`).
7. Contra el texto del pre-registro, el código implementa sin diferencia: ventana (T desde 2026-04-01, O hasta 2026-11-02 12:59, `CORTE_SNPP`), días excluidos (12, 13, 17 a 20 de octubre), orden de cercanía `PREF = (B4, B2, B5, B1, B3)`, desempate por menor E y luego orden, condición "no peor" (`GANA` o `EMPATE`, o `SIN SUSTRATO` con neto menor o igual a 0), controles de la compuerta, 2 % de cobertura con el denominador sin "fuera" ni "sin_crater", y el formato de hora `"%Y-%m-%d %H:%M"` (la comparación de texto con `CORTE_SNPP` es válida). Vara: `PREREGISTRO_V750B.md` §3, §5, §6, §7, §9 leído hoy.
8. Medidores: el de V750-A (`mutar_evaluar_v750a.correr`) cuenta ATRAPADA sólo con rc 1 y la línea "== PRUEBAS: FALLAS"; una caída (Traceback o rc fuera de 0, 3, 5, 6) hace rc 2 y se cuenta CAÍDA; un tiempo agotado es SIN DATO; su `probar_evaluar_v750a.py` no tiene `except` amplio que convierta excepciones en salida normal (`grep -n "except"`: una sola, en `diag_valido`). Vara: salidas reales: M1, M33, M34, M36 aparecen CAÍDA en la corrida principal y ATRAPADA al repetir (`mutar_evaluar_v750a_caidas_salida.txt`), y el control CAIDA da CAÍDA 61 de 61. Lo mismo vale para el de la adenda 3 (rc 1 y línea de fallas; rc 2 y "CAÍDA DEL LECTOR").
9. La prueba de la rama de la ROI: 21 de 21 reproducidas en mi árbol armado (`roi_pytest_control_salida.txt`).

## 6. SIN DATO (no pude medirlo; comando exacto)

- Efecto de `VRP_PROFILE` diurno sobre la lista: `VRP_PROFILE=_s154_ab_diurno_k_on python experiments/_s162_v750b/objetivos_v750b.py --data <data main> --ref-dest <carpeta> --hasta 2026-10-29` contra el mismo comando sin la variable (necesita red y el generador).
- Cuántas protegidas sólo-OCR de Suomi NPP hay el 2026-10-09 y cuántas pasadas "fuera del gránulo" hay en una lista real: requieren la lista del día.
- Medidor completo de V750-A con M1 a M85 sobre 77 escenarios: `python experiments/_s162_v750a/mutar_evaluar_v750a.py --dest <tmp> --evaluador D:/vrp-trabajo/temporales/evaluar_d25_s161.py --hilos 1` (unas 7 h, ocupa los cupos).
- Si el worktree `s162-viirs750-2-918174` se actualiza antes del 11-03 (con lo cual P1-01 se reduce a la disciplina de actualizar): depende de lo que haga la coordinadora.
- Comportamiento de GitHub Actions con el workflow (timeouts, `max-parallel`): no lo probé.

## 7. FUERA DE ALCANCE

- La corrección de la regla de selección (lo que el A/B decide), de los umbrales de MIROVA, del oráculo (validado contra Octave en S159) y de `probe_n.py`.
- Arreglos de cualquier tipo: los decide quien orquesta, con tag defensivo y confirmación de Nicolás cuando toquen `pipeline/` (A45).
