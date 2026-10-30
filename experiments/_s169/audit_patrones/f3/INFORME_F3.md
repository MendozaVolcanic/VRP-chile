# Informe F3: infraestructura común (sombra de código MIROVA, evaluador/banco/clase/calidad/referencia, auto-audit, líneas de log)

## 1. Encabezado

- Fecha y hora del servidor (UTC, `date -u`): viernes 2026-10-30 03:54 UTC (inicio 03:44).
- Commit medido: `cc3887290` de origin/main (árbol en `D:/vrp-trabajo/temporales/s169_audit_patrones/f3_comun/arbol/`, `git archive` sin data/).
- Modelo y esfuerzo: claude-sonnet-5-5, esfuerzo bajo.
- CARPETA: `D:/vrp-trabajo/temporales/s169_audit_patrones/f3_comun/` (scripts propios y su salida en `scripts_p3/`; `hallazgos.csv` aquí). Mis importaciones dejaron un `__pycache__` dentro de `arbol/scripts/` (dentro de CARPETA, el repo real no se tocó).
- Qué NO miré (mi silencio no es "todo bien"):
  - `scripts/auto_audit_weekly.py` líneas 120 a 330, 440 a 535, 586 a 655, 690 a 1000: no las leí. Sólo leí la cabecera, `es_pasada_diurna_descartada`, `aplicar_d9`, `cargar_filas_referencia`, `_hito_ocr_suomi_npp`, `main` y las funciones de frontera de detector.
  - `scripts/evaluador_comun.py` líneas 200 a 330 y 370 a 740 (P1b, estratos, bootstrap, placebos, pruebas de signos): no las leí.
  - `scripts/vigilancia_sombra.py` (lector de la sombra de K): sólo cabecera y `avisos_*`/`cargar_insumos`. No es el lector de la sombra «código MIROVA»; ese lector no existe en este árbol.
  - Los procesadores `process_modis/viirs/viirs_mod.py` y `mirova_v750_codigo.py`: sólo los bloques de la vía y de `procesar_grilla`; nada del detector.
  - No corrí el pipeline, ni descargué gránulos, ni abrí `data/` (no existe en el árbol), ni `data/sombra_codigo_mirova/`. Sin red.
  - `sync-mirova-csv.yml` y `nrt.yml`: sólo grep puntuales.
- Resultados de scripts: `scripts_p3/p3_01..p3_05_salida.txt` (cada uno con su script `.py` al lado).

## 2. En una pantalla

1. El lector común (`evaluador_comun.py`) da `COBERTURA OK` con exit 0 cuando la referencia de MIROVA está vieja, vacía o ilegible (BOM): cero pasadas es indistinguible de "todo cubierto" (P3-01, gravedad 4; control positivo en INVALIDO medido).
2. `revisar_sombra.py` queda ciego desde el 2º día: cuenta records de la ventana de 8 días que ya estaban commiteados, así que una corrida de hoy sin NADA sale verde; tampoco mira por sensor ni por volcán (P3-02 y P3-03, gravedad 3; la `vigilancia_sombra.py` de K sí lo hace).
3. Los gránulos que la vía descarta (`return None`) no dejan log, incidencia ni JSON de cobertura, y el workflow no guarda `pipeline.log` ni pasa `--cobertura-json`: lo perdido no se puede diagnosticar (P3-04, gravedad 3). Nada vigila el run de la sombra (P3-09).
4. `VRP_PROFILE` del entorno gana sobre el `setdefault` de evaluador y banco: con `_s154_ab_diurno_k_on` el lector deja de descartar pasadas diurnas (P3-06, medido). El evaluador no deja procedencia (sha de la referencia ni del código) ni limita parámetros libres (P3-07).
5. La línea de log de VIIRS 375 es ciega (idéntica con y sin detección, medido con la función real); las de MODIS y VIIRS 750 no lo son, pero no dicen si el record es de la vía o de K ni si el store lo escribió (P3-05, gravedad 2).

## 3. Hallazgos (peor primero)

### P3-01
- TÍTULO: El evaluador común da COBERTURA OK (exit 0) con una referencia de MIROVA vieja, vacía o con BOM
- ARCHIVO:LÍNEA: `scripts/evaluador_comun.py:169` (veredicto), `:818-821` (carga de `--ref`), `:838` (`pasadas_mirova` sólo en el JSON); `scripts/referencia_mirova_unificada.py:112-121` (`leer_pasadas`, `csv.DictReader` sin chequeo de columnas). SCRIPT:SALIDA `scripts_p3/p3_03_evaluador_ref.py` → `p3_03_salida.txt` (B1a, B1b, B1c, B3a).
- QUÉ PASA: El veredicto de cobertura sólo se vuelve INVALIDO si encuentra una protegida faltante o un día vacío entre las pasadas de MIROVA; si la referencia no trae pasadas en la ventana (carpeta `--ref` congelada antes de tiempo, snapshot atrasado, archivo con BOM que hace que ninguna fila tenga `Volcan`), la lista de pasadas queda vacía y "no hay nada que cubrir" sale `COBERTURA OK`. No se imprime cuántas pasadas de MIROVA entraron, ni se compara la última fila de la referencia con `--hasta`. `vigilancia_sombra.avisos_referencia` (l. 395) sí lo hace; el evaluador común no.
- CÓMO SE VE EN EL DASHBOARD: invisible; sale como "COBERTURA OK" en el informe de un A/B o de la sombra, justo la precondición que el docstring (l. 8-16) pone antes de leer cualquier veredicto.
- CÓMO REPRODUCIRLO: `"C:/Users/nmend/AppData/Local/Programs/Python/Python312/python.exe" -I D:/vrp-trabajo/temporales/s169_audit_patrones/f3_comun/scripts_p3/p3_03_evaluador_ref.py`. Medido: B1a (referencia con una fila de 2026-10-01, ventana 2026-11-03 a 11-10, control y brazo con record) → `COBERTURA OK`, exit 0. Control positivo B1b (referencia al día, brazo sin el record que el control tiene) → `INVALIDO POR INSTRUMENTO`, exit 2. B3a: mismo CSV con BOM → 0 filas leídas (1 sin BOM).
- Dos preguntas del instrumento: (1) si la referencia estuviera rota, la medición del veredicto no lo ve (lo mostré); (2) con el instrumento muerto (siempre OK) B1b diferiría, así que el instrumento está vivo. Datos sintéticos, ventana 2026-11-03 a 2026-11-10, denominador 0 pasadas en B1a.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 4 (puede dejar pasar vacuamente el chequeo previo de un veredicto de A/B o de sombra).

### P3-02
- TÍTULO: `revisar_sombra` no ve una corrida vacía a partir del segundo día: cuenta records ya commiteados
- ARCHIVO:LÍNEA: `scripts/revisar_sombra.py:27` (`en_ventana`), `:40` (`via == 0`); `.github/workflows/sombra-codigo-mirova.yml:148-151`. SCRIPT:SALIDA `scripts_p3/p3_01_revisar_sombra.py` → `p3_01_salida.txt` (CASO A, CONTROL A).
- QUÉ PASA: La ventana es de 8 días (hoy y 7 atrás) y el JSON del checkout ya trae lo commiteado por las corridas anteriores. `revisar` pide "al menos un record de la vía en la ventana", sin distinguir si lo produjo ESTA corrida. Si NASA o CMR caen hoy (log con "Cobertura INCOMPLETA", cero records nuevos), los records de los días previos satisfacen la condición. Sólo el primer día (2026-11-03) está protegido. El único síntoma que sí atrapa es "ERROR processing", y un fallo de búsqueda no lo genera (queda en `fetch._registrar_falla` y exit 0).
- CÓMO SE VE EN EL DASHBOARD: invisible (la sombra no la lee el tablero); el job queda verde y nadie sabe que el día no se midió. El lookback de 7 días lo repara si NASA vuelve antes de 8 días; si no, el hueco se vuelve permanente.
- CÓMO REPRODUCIRLO: script anterior. Medido: JSON con 7 días previos × 3 sensores (21 records) y log vacío → `ok = True`, "21 de la vía"; control positivo (ventana de un día sin records) → `ok = False`; control de instrumento (`ERROR processing`) → `ok = False`.
- Dos preguntas: (1) si la corrida de hoy estuviera rota, la medición no lo ve; (2) con el instrumento muerto los controles diferirían (los tres controles dan False).
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 3 (puede ocultar días sin medir en una sombra pre-registrada; nada se decide solo, pero cae en el conteo de noches).

### P3-03
- TÍTULO: `revisar_sombra` no exige records por sensor ni por volcán-sensor; la sombra puede perder un sensor entero y salir verde
- ARCHIVO:LÍNEA: `scripts/revisar_sombra.py:28` (suma total de la vía), `:40`; contraste: `scripts/vigilancia_sombra.py:362-382` (`_avisos_frescura` por volcán y sensor). SCRIPT:SALIDA `p3_01_salida.txt` (CASO B).
- QUÉ PASA: Los tres pre-registros miden un sensor cada uno (V750-A, V375-E, MOD-D). Un sensor que no produce nada (p. ej. todos los MODIS sin MOD03 caen en `_sin_geolocalizacion` en `run_pipeline.py:247-250` y se saltan antes de llamar al procesador, con lo que la rama `sin_mxd03` del procesador es inalcanzable desde `run_pipeline`) deja el total de la vía > 0 gracias a los otros dos y el job verde. La propia vigilancia de K documenta este modo («sin MODIS (13 protegidas MODIS sin mirar, VERDE)», `vigilancia_sombra.py:364-365`, TEXTO).
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `p3_01`: sólo records VIIRS 375 (7) → `ok = True`.
- Dos preguntas: (1) no ve la pérdida de un sensor; (2) con instrumento muerto no cambia: por eso SIN control positivo posible hasta que se cambie la regla.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 3.

### P3-04
- TÍTULO: Gránulos descartados por la vía y cobertura del run no dejan rastro (sin aviso, sin JSON de cobertura, sin `pipeline.log` guardado)
- ARCHIVO:LÍNEA: `pipeline/process_viirs.py:773,781`; `pipeline/process_viirs_mod.py:509,517`; `pipeline/process_modis.py:657` (`return None` sin print ni incidencia); `pipeline/mirova_v750_codigo.py` (0 `print`); `.github/workflows/sombra-codigo-mirova.yml:122-123` (sin `--cobertura-json`, `tee pipeline.log`, sin `upload-artifact`); `scripts/run_pipeline.py:578-674` (`informar_cobertura` sale 0 sin `--estricto-cobertura`).
- QUÉ PASA: La vía devuelve `None` si el gránulo no cubre la grilla (menos de 100 píxeles en el recorte de 45 km, o el píxel más cercano al centro a más de 5 km en V375 y MODIS) o si falta una banda; K, en cambio, sólo devuelve `None` si su ROI está vacía (`process_viirs.py:841`). Esa asimetría produce justo "gránulos que K tiene y la vía no" sin una línea que lo diga. Además `pipeline.log` vive sólo en el runner y en el log de Actions, y el JSON de cobertura que `evaluador_comun --cobertura` espera como insumo (l. 811-812, 849-853) no se genera: toda ausencia caerá en la causa `sin_registro`. (El NRT tampoco lo genera, por lo que el control tiene el mismo hueco.)
- CÓMO SE VE EN EL DASHBOARD: invisible; para el lector aparece como `falta_cobertura` del brazo (INVALIDO si es una protegida, `evaluador_comun.py:135-166`) sin causa diagnosticable.
- CÓMO REPRODUCIRLO: lectura de código (grep `_rad is None|_rec is None`). Correr el pipeline para medir cuántos gránulos caen en estas ramas queda como SIN DATO: `python scripts/run_pipeline.py --profile sombra_codigo_mirova --volcano <V> --start 2026-10-21 --end 2026-10-28 --cobertura-json x.json` (el run 40945613044 ya midió 77 de 77 records en Láscar, pero no cuenta los gránulos sin record).
- Mitigante: el lookback de 8 días reintenta fallos de NASA, no estos `None`, que son deterministas.
- CONFIANZA: CONFIRMADO (código); la cuantía, SIN DATO.
- GRAVEDAD: 3.

### P3-06
- TÍTULO: `VRP_PROFILE` ambiental cambia lo que el evaluador y el banco leen como pasada diurna (P-E)
- ARCHIVO:LÍNEA: `scripts/evaluador_comun.py:53` y `scripts/banco_paridad.py:60` (`os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")`); `scripts/auto_audit_weekly.py:295-300` (`es_pasada_diurna_descartada` lee `ENABLE_DAYTIME_*` del perfil activo). SCRIPT:SALIDA `p3_04_vrp_profile_env.py` → `p3_04_salida.txt`.
- QUÉ PASA: `setdefault` respeta una variable ya presente. Con `VRP_PROFILE=_s154_ab_diurno_k_on` (perfil real de un A/B), la misma pasada diurna de VIIRS 375 sobre Láscar deja de descartarse (`False` en vez de `True`), entran pasadas diurnas a las referencias, a `cargar_lado` y a `pasadas_nocturnas`. Lo único que lo delata es una línea de stderr `[VRP profile=...]`; ni el JSON de `--salida` ni el de `banco_paridad` la guardan.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `p3_04`: sin variable → perfil `mirova_equivalent`, descarta=True; `_s154_ab_diurno_k_on` → descarta=False; `experimental` → True.
- Dos preguntas: (1) lo mide; (2) control = proceso sin variable, distinto del caso con variable.
- CONFIANZA: CONFIRMADO. En el runner de la sombra no hay variable (workflow sin `env:` de perfil), así que el riesgo es de lecturas locales.
- GRAVEDAD: 3.

### P3-07
- TÍTULO: El evaluador común no deja procedencia y deja libres referencia, regla, canal y días excluidos; `--salida` pisa
- ARCHIVO:LÍNEA: `scripts/evaluador_comun.py:799-813` (argumentos), `:835-853` (dict de salida), `:897` (escritura que pisa).
- QUÉ PASA: El JSON de salida guarda ventana, sensores, canal, regla de mínimas y días excluidos, pero no el sha de los CSV de `--ref`, ni el de los JSON de los lados, ni el commit del código ni el hash de `frontend/index.html` (el predicado `pub` se ejecuta con node sobre el HTML del árbol de trabajo). `banco_paridad.py` sí guarda `sha_index_html` y los sha de la referencia (l. 518 y `main`). No hay límite a repetir la lectura con otro `--ref`, `--regla-minimas`, `--canal` o `--excluir-dias` ni nada que registre cuántas lecturas se hicieron: la regla de una sola lectura de la sombra pre-registrada queda fuera del código. Tampoco valida que los lados sean del perfil esperado (`regimen.perfil`), como sí hace `vigilancia_sombra.avisos_perfiles`.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: lectura de código: `res = {...}` (l. 835-846) no contiene procedencia.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 3.

### P3-08
- TÍTULO: El "sha del código" de cada record es el HEAD del repo en el disparo, no una identidad de `pipeline/`; el commit de la sombra no lo lleva
- ARCHIVO:LÍNEA: `pipeline/store.py:89-94` (`_marca_regimen`: `GITHUB_SHA`), `:549`; `.github/workflows/sombra-codigo-mirova.yml:135` (mensaje de commit sin sha).
- QUÉ PASA: Cada record lleva `regimen.perfil` y `regimen.codigo_sha = GITHUB_SHA`. En un disparo `schedule` ése es el último commit de main, que incluye los commits de datos horarios del NRT; por eso dos días distintos tendrán shas distintos aunque `pipeline/` no haya cambiado (semántica de GitHub conocida, no probada aquí). Para verificar el congelamiento de `pipeline/` durante la sombra (decisión de la vuelta 11) un lector tiene que hacer `git diff sha1 sha2 -- pipeline/ scripts/run_pipeline.py volcanoes.yaml pipeline/profiles pipeline/grillas_mirova.yaml` con historia completa (P-C: depende de que git tenga los objetos; `actions/checkout` por defecto es superficial). Y con `--overwrite` ausente, un record guardado no se recalcula (`store.py:687-704`, sólo NRT→estándar), así que un mismo JSON puede mezclar versiones de código; `revisar_sombra` no chequea que todos los shas de la ventana coincidan en `pipeline/`.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: lectura de código; verificar con un `git log` real de dos shas con sólo commits de datos entre ellos queda SIN DATO (no hay git del repo en el árbol auditado).
- CONFIANZA: CONFIRMADO para lo que contiene el record y el mensaje; SOSPECHA para la semántica de `GITHUB_SHA` en `schedule`.
- GRAVEDAD: 3 (puede dejar indecidible, tras gastar runner, la pregunta "¿corrió todo con el mismo código?").

### P3-09
- TÍTULO: Nadie vigila el run de la sombra: un job rojo o ausente sólo deja una X en Actions (zombie)
- ARCHIVO:LÍNEA: grep en `.github/` y `scripts/`: `sombra-codigo-mirova` sólo aparece en su propio workflow, el perfil, `revisar_sombra.py`, `ventana_sombra.py` y el test; `nrt-healthcheck.yml`/`nrt-monitor.yml`/`vigilar_plataformas.py` no lo nombran.
- QUÉ PASA: La regla 6 del CLAUDE.md global (zombie: último run verde contra último dato commiteado) no está implementada para la sombra. Un workflow desactivado por GitHub tras 60 días sin actividad de commits, un cron perdido, o 11 jobs rojos, no abren issue. Antes del 2026-11-03 sale verde por diseño, así que no hay línea base.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `grep -rn "sombra-codigo\|sombra_codigo" arbol/.github arbol/scripts`.
- CONFIANZA: CONFIRMADO (ausencia en este commit); puede existir en una rama del lector.
- GRAVEDAD: 3.

### P3-10
- TÍTULO: `cargar_lado` no filtra `via_codigo_mirova` ni cuenta los records descartados por fecha ilegible
- ARCHIVO:LÍNEA: `scripts/evaluador_comun.py:755-776` (`slim` sin `via_codigo_mirova`; `except ValueError: continue` en l. 767 sin contador); `scripts/banco_paridad.py:cargar_nuestros` (`except (KeyError, ValueError): continue`); `scripts/revisar_sombra.py:1-20` (docstring: "el lector lo tiene que poder filtrar").
- QUÉ PASA: Un record de la sombra que cayó a K (`via_codigo_mirova` = "sin_grilla", "sin_mxd03", "geo_distinta") se evalúa como si fuera de la vía. `revisar_sombra` pone el job rojo ese día, pero el record queda en el JSON y el lector no lo distingue. Un `datetime_utc` con otro formato (la vía lo arma con `_parse_datetime`, formato `%Y-%m-%d %H:%M`, ok hoy) se descartaría sin aviso.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: lectura de código (`CAMPOS_JS` en `banco_paridad.py` no incluye la clave).
- CONFIANZA: CONFIRMADO (código); que el lector de la sombra use `evaluador_comun` es SOSPECHA.
- GRAVEDAD: 3.

### P3-11
- TÍTULO: `--ref` del evaluador: los archivos de respaldo y de filas perdidas son opcionales en silencio y sus nombres no coinciden con los del repo
- ARCHIVO:LÍNEA: `scripts/evaluador_comun.py:806-807` (ayuda: la carpeta "con ... consolidado_filas_perdidas.csv y respaldo_20260408.csv"), `:818-821` (`opc(...)` devuelve None si no existen); `scripts/referencia_mirova_unificada.py:74` (en el snapshot el respaldo se llama `registro_vrp_consolidado_respaldo_20260408.csv`); SCRIPT:SALIDA `p3_03_salida.txt` (B2).
- QUÉ PASA: Con una carpeta con la forma del snapshot versionado, el respaldo no se encuentra y la referencia pierde filas sin aviso (1 fila contra 2 en el caso sintético). Con datos reales el respaldo trae 244 pasadas (17 ALERTA_TERMICA) de enero a abril (`referencia_mirova_unificada.py` docstring); las filas que el consolidado remoto pierda en el futuro sólo entran por `consolidado_filas_perdidas.csv`. Una alerta perdida no cuenta como alerta y su noche sale del recall.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `p3_03` bloque B2.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 3 (puede sacar una protegida de la referencia).

### P3-05
- TÍTULO: La línea de log de VIIRS 375 es ciega; las de MODIS y VIIRS 750 no, pero tampoco dicen la vía ni si el store escribió
- ARCHIVO:LÍNEA: `scripts/run_pipeline.py:321-327` (V375), `:274-278` (MODIS), `:366-370` (V750). SCRIPT:SALIDA `p3_02_log_ciego.py` → `p3_02_salida.txt`.
- QUÉ PASA: La línea de V375 imprime `vrp_mir_mw`, `vrp_tir_mw`, `t_max_i04_k`, `n_vent_pixels`, que el record de la vía no llena, así que sale `None` con o sin detección. Con los records reales de `procesar_grilla` sobre una grilla sintética (un píxel de 340 K), el texto es idéntico con y sin detección: `VIIRS_NOAA20 (375m) | VRP_MIR=None MW | VRP_TIR=None MW | T_max=None K | VRP_VENT=0.0 MW (Nonepx)`. Las de MODIS (`VRP=47.696 MW | T_bg=278.04 K...` contra `VRP=0.0 MW | T_bg=None K...`) y V750 sí cambian. Pero ninguna lleva `via_codigo_mirova`, así que un record K de respaldo (`sin_grilla`) se ve igual; y las tres se imprimen después de `store.append_record`, sin saber si el store lo rechazó por diurno (`STORE REJECT`) o lo ignoró por duplicado (clave `(datetime_utc, sensor)` sin `--overwrite`), de modo que describen `result` y no lo guardado.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `p3_02` (las f-strings se extraen con `ast` del archivo real).
- Dos preguntas: (1) el script ve la ceguera (compara textos); (2) el control positivo son MODIS y V750, que cambian entre los dos casos.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2.

### P3-12
- TÍTULO: `alerta_protegida` y `es_protegida` cuentan como protegida un VRP "nan"
- ARCHIVO:LÍNEA: `scripts/clase_mirova.py:72` (`if v is None or v < umbral`), `:281`; `scripts/referencia_mirova_unificada.py:_float` (`float("nan")` es válido). SCRIPT:SALIDA `p3_03_salida.txt` (B3b).
- QUÉ PASA: `nan < 1.0` es False, así que una fila ALERTA con `VRP_MW = "nan"` pasa el umbral y es protegida lectura A (medido: `True`; vacío → `False`; 0,4 → `False`; 1,2 → `True`). Si el scraper o el OCR llegara a escribir "nan" como texto, aparecería una protegida fantasma que ningún sensor puede cumplir.
- CÓMO SE VE EN EL DASHBOARD: invisible; sale como "protegida sin publicar" en el audit.
- CONFIANZA: CONFIRMADO (comportamiento del código); que los CSV reales traigan "nan" es SIN DATO.
- GRAVEDAD: 2.

### P3-13
- TÍTULO: `cargar_filas_referencia` del auto-audit cae en silencio al cargador canónico
- ARCHIVO:LÍNEA: `scripts/auto_audit_weekly.py:659-665` (`except Exception: return None`), `:1029-1030` y `:536-555` (`aplicar_d9` con `filas_ref=None`).
- QUÉ PASA: Si la referencia unificada no se puede leer, D-9 se aplica sobre las alertas ya deduplicadas del cargador, que el propio docstring dice que diverge en dos casos sintéticos (`:543-545`). Ningún aviso va a `cobertura_avisos` ni a `latest.json`.
- CÓMO SE VE EN EL DASHBOARD: invisible (veredicto del audit semanal sin marca).
- CONFIANZA: CONFIRMADO (lectura).
- GRAVEDAD: 2.

### P3-14
- TÍTULO: `evaluador_comun` no cumple A119(d): nunca llama a `calidad_referencia_mirova.avisar`
- ARCHIVO:LÍNEA: grep `avisar(` en `scripts/`: sólo `banco_paridad.py:224-227` y la definición; CLAUDE.md, A119 (d), TEXTO: «un script nuevo que lea los CSV sin pasar por `banco_paridad` llama a `calidad_referencia_mirova.avisar(desde, hasta)` en su primera línea».
- QUÉ PASA: `evaluador_comun.main` lee la referencia con `cargar_referencia_unificada` directamente. Para ventanas desde 2026-11-03 `avisos_de_ventana` devuelve vacío (todos los hitos son anteriores al 2026-10-10), así que no pierde nada hoy; sí para cualquier A/B con ventana anterior. `avisar` además sólo escribe a stderr y el resultado no entra a ningún JSON.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2.

### P3-15
- TÍTULO: La fecha mínima 2026-11-03 se aplica a las fechas pedidas, no a `datetime_utc` de cada record
- ARCHIVO:LÍNEA: `scripts/ventana_sombra.py:39-46`; `pipeline/fetch.py:608-632` (CMR cruza por traslape con bordes incluidos; día consultado = [D 00:00:00, D 23:59:59]); `scripts/revisar_sombra.py:27` (sólo cuenta dentro de la ventana). SCRIPT:SALIDA `p3_05_ventana_y_hash.py` → `p3_05_salida.txt`.
- QUÉ PASA: `ventana_sombra` es correcto en lo que hace (medido: 11-02 sin ventana; 11-03 → `11-03 11-03`; 11-20 → `11-13 11-20`; start antes de la mínima → exit 2). Pero ni el procesador ni el store ni `revisar_sombra` verifican que cada record tenga `datetime_utc >= 2026-11-03`. Sólo un gránulo que toque la medianoche podría colarse; los gránulos MODIS y VIIRS están alineados a 5 y 6 minutos desde 00:00, así que es improbable. Medido también: `end` hasta 2027-06-30 se acepta en modo commit.
- CONFIANZA: SOSPECHA (borde no probado con gránulos reales).
- GRAVEDAD: 2.

### P3-16
- TÍTULO: Menores del workflow y del perfil de la sombra
- ARCHIVO:LÍNEA: `.github/workflows/sombra-codigo-mirova.yml:66-70` (un `volcano` mal escrito hace que los 11 jobs se salten y el run salga verde, sin error); `pipeline/profiles/sombra_codigo_mirova.yaml:22` (comentario: "que no tiene schedule: encenderlo es otro sí de Nicolás", falso desde S168; P-G); `.github/workflows/audit-weekly.yml` (`runs-on: ubuntu-latest` mientras los demás fijaron 24.04 por la migración a 26.04; audit-weekly no necesita pyhdf).
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 1.

## 4. SEGUIMIENTOS (fuera de mi eje o sin medir)

- `scripts/banco_paridad.py:indexar_referencia` define la "noche" por la fecha UTC de la pasada (`f["fecha_utc"][:10]`); una noche invernal chilena cruza la medianoche UTC. Probablemente irrelevante porque las pasadas nocturnas caen entre ~02 y ~09 UTC. Confianza: SOSPECHA, no medida.
- `scripts/clase_mirova.py:resumir_pasadas` usa por defecto `regla_minimas="SN"` y `banco_paridad.indexar_referencia` usa `"original"`; está documentado en ambos, pero dos entradas del mismo concepto con valores por defecto distintos.
- `normalize_sensor` (`pipeline/mirova_csv_loader.py:63-83`) devuelve la etiqueta en mayúsculas si no es MODIS ni VIIRS; un sensor nuevo cae fuera de todo bucket sin aviso (`bucket not in sensores`).
- `auto_audit_weekly.main` añade a `history.jsonl` con `open(..., "a")` en cada corrida; un `workflow_dispatch` el mismo día duplica la línea.
- El audit semanal corre los lunes 09:00 UTC; el cese de Suomi NPP es lunes 2026-11-02 13:00 UTC, así que la primera lectura con el régimen nuevo es el 2026-11-09. Existe manejo (`plataformas`, `juzga_desde`), sin auditar aquí.

## 5. VERIFICADO LIMPIO

- `ventana_sombra.py` (CLI real): 9 casos de borde en `p3_05_salida.txt`. Vara: el docstring del módulo (l. 8-14) y `test_ventana_respeta_la_fecha_minima`. Medido: 11-02 → vacío, exit 0; 11-03 → `2026-11-03 2026-11-03`; 11-20 → `2026-11-13 2026-11-20` (8 días); start antes de la mínima, invertida, sin end, fecha inválida y `--medir` sin fechas → exit 2. Control positivo = esos mismos exit 2.
- Perfil `sombra_codigo_mirova.yaml`: los flags de K (`enable_test1_path`, `enable_tests_23_prose_branch`, `enable_modis_b22_primary`) están en las mismas secciones que lee `pipeline/profile.py` (`paths` l.175 y 736; raíz l.636), no en una sección equivocada (A89). Vara: `profile.py` leído, no el YAML. El paso del workflow además afirma `DATA_SUBDIR` y las tres vías (l. 99-100 del yml).
- `VRP_PROFILE` en el runner de la sombra: el paso del perfil es inline para el chequeo y `--profile` en `run_pipeline` (`run_pipeline.py:76-80` asigna `os.environ`), sin `env:` de perfil a nivel de job; no hay `VRP_*` en el workflow salvo `VRP_MEDIR/START/END` (que no son de perfil).
- P-A, hash con fin de línea: `banco_paridad.sha_git` usa `git hash-object <ruta>` con `cwd=ROOT` (aplica filtros). Medido en un repo temporal con `core.autocrlf=true` y un CSV CRLF: con filtros = sha del blob LF; `--no-filters` ≠. Limpio mientras se ejecute dentro del repo.
- Mapeo de sensores de la vía: `process_viirs_mod._sensor_label_from_filename` devuelve `_750` y `process_modis._sensor_modis` devuelve `MODIS_TERRA/AQUA`; el `bucket()` de banco/evaluador los clasifica bien (lectura).
- Token: el paso aborta con exit 1 si `EARTHDATA_TOKEN` viene vacío; `fetch` re-lanza `EarthdataCredentialError` (`fetch.py` "S123"), que deja el job rojo.
- Commit: sólo `git add data/sombra_codigo_mirova/<volcán>.json`, bucle de 5 reintentos, grupo de concurrencia propio; el test `test_el_workflow_commitea_solo_la_carpeta_de_la_sombra_y_con_grupo_propio` lo respalda.
- `calidad_referencia_mirova.HITOS` frente a A119: coincide el hito 2026-06-13 en `etiqueta_que_decide` y los de 2026-03-01, 04-01 y 06-11.

## 6. SIN DATO

- Cuántos gránulos por día caen en los `return None` de la vía: requiere correr el pipeline. Comando: `python scripts/run_pipeline.py --profile sombra_codigo_mirova --volcano Lascar --start 2026-10-21 --end 2026-10-28 --cobertura-json salida.json` con credenciales y cupo de procesos pesados.
- Si los CSV reales de Mirova-v1 tienen BOM o "nan" en VRP: no hay `data/` en el árbol.
- Si `GITHUB_SHA` cambia entre dos corridas diarias con sólo commits de datos en medio: requiere el historial real de git del repo.
- El predicado de `pub` (node sobre `index.html`) para records de la vía: no lo corrí con records de la vía (la cola de `f5CoreMagnitude` cae a `pc.vrp_mw` por lectura de `index.html:1248-1315`).

## 7. FUERA DE ALCANCE

- Detector y matemática de `mirova_v750_codigo.py`, A/B pre-registrados, bootstrap y placebos de `evaluador_comun`, métricas de `auto_audit_weekly` (recall, magnitud, falsas publicaciones).
- Arreglos de cualquier hallazgo (A45 para `pipeline/`, confirmación de Nicolás).
