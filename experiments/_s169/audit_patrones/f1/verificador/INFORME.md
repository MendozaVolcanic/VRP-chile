# Verificador F1 (V750-B, V750-A, rama de la ROI): veredictos sobre P1-01 a P1-14

## 1. Encabezado

- Fecha y hora: 2026-10-30 04:07 a 04:21 UTC (reloj del sistema con `date -u`; la tarea prohíbe red, así que no hay
  hora de un servidor remoto).
- Commits medidos: árbol `f1_v750/arbol/` (= `01ffd277b`, rama `claude/s162-viirs750-2-918174`); rama de la ROI
  `3c5c494b9` (extraída por mí a `roi_vf/` con `git -c core.autocrlf=false archive`, idéntica byte a byte a
  `f1_v750/roi/` en el script y la prueba, comprobado con `cmp`); `main` `443da8649` (extraído a `main443/`: scripts,
  pipeline, volcanoes.yaml, frontend/index.html) y `cc3887290`; tags `s162-v750b-sellado`, `s167-v750b-adenda3-sellada`,
  `s161-d25-lectura`.
- Modelo y esfuerzo: Claude Opus 5.5, esfuerzo bajo fijado por la sesión.
- CARPETA: `D:\vrp-trabajo\temporales\s169_audit_patrones\f1_verificador\`. `caminos.md` escrito antes de abrir
  ningún archivo citado; su sha256 (5de49aa2...) y la hora quedan anotados al final del propio archivo.
- No abrí el informe, el csv ni los scripts del auditor antes de cerrar estos veredictos (la sección 6 es posterior).
- Qué NO miré: el run real de V750-B (no existe todavía); el generador sobre datos reales (prohibido); el medidor de
  V750-A en curso (PID 1324) ni sus temporales; los otros once archivos de `adenda2/` y `adenda1/` salvo los citados;
  el workflow `probe-s162-v750b.yml`; `02_seleccion.py`; el contenido de `data/`.

## 2. En una pantalla

- 14 afirmaciones: 9 CONFIRMADO, 5 CONFIRMADO EN PARTE, 0 REFUTADO, 0 SIN DATO.
- Lo peor sigue en P1-02 y P1-03. P1-02: una sola bandera abre a la vez la cobertura y un censo que corrió y FALLÓ, y la
  marca que sale no dice que el censo falló. P1-03: un `VRP_PROFILE` diurno en el shell cambia el filtro nocturno del
  generador sin dejar rastro (medido). Las dos se cierran con el procedimiento del día, sin adenda.
- P1-01, P1-06 y P1-10 tienen efecto nulo o neutral hoy. P1-01: el predicado y los inner del tablero son idénticos
  entre el worktree y `main`. P1-06: la regla está escrita así en la adenda 3 sellada. P1-10: la regla está escrita así en el §4 sellado.
- Hallazgos nuevos: VF1-01, un censo apuntado a una ruta errada se imprime «FALLA», igual que un censo distinto (gravedad 2).
  VF1-02, aplicar la ROI dos veces deja el comentario del YAML con el brazo viejo (gravedad 2). VF1-03, el analizador no coteja
  volcán y hora del resultado contra el objetivo del mismo id (gravedad 2). VF1-04, el meta de la población trae un commit fijo, ya anotado (gravedad 1).

## 3. Veredictos

Dos preguntas del instrumento, comunes: cada script de medición lleva en su cabecera la respuesta y un control que
tiene que dar distinto del caso medido. Los números de este informe son de esos scripts (salida al lado, `*_salida.txt`).

### P1-02 · CONFIRMADO · gravedad 3 · clase (i)
- TÍTULO: `--leer-con-faltantes` abre la compuerta aunque el control del censo haya corrido y FALLADO.
- ARCHIVO:LÍNEA: `experiments/_s162_v750b/analizar_v750b.py:414` (`censo_pasa = censo_ok or (...) or bool(a.leer_con_faltantes)`),
  y `:406-408` (la marca). Vara: `PREREGISTRO_V750B.md:211-214`, TEXTO: «si después del relanzamiento siguen faltando
  pasadas o el control del censo no se puede correr, y la coordinadora con Nicolás deciden leer igual, se usa
  `--leer-con-faltantes`».
- SCRIPT:SALIDA: `p102_compuerta.py` → `p102_compuerta_salida.txt`. Ejecuta el texto literal de las líneas 405 a 416
  (sha256 LF del analizador `83b7159b...`, el sellado) con las entradas fijadas. Filas: censo corrido y fallado sin
  banderas, CERRADA; bandera de pruebas con censo corrido y fallado, CERRADA (control VB3-06, la extracción sirve);
  censo fallado con `--leer-con-faltantes`, **ABIERTA, rc 5**; cobertura insuficiente con censo fallado y el motivo de la bandera
  hablando sólo de cobertura, **ABIERTA, rc 5, marca `[LEÍDO CON FALTANTES: faltan 3 pasadas]`**.
- QUÉ PASA: el control del censo dice si el oráculo de B0 y B1 reproduce píxel a píxel al censo S159; si falla, las
  cajas del run no son las que se creen. El texto sellado permite la bandera sólo para un censo que «no se puede correr».
  El código la acepta también para uno que corrió y salió distinto. Y como una sola bandera cubre cobertura y censo, quien la pasa
  por un problema de cobertura salta sin saberlo un censo fallado. La marca repite el motivo humano, no el control que
  cayó (la línea «== control B0 y B1 ... FALLA» sí se imprime más arriba).
- CÓMO SE VE EN EL DASHBOARD: invisible; torcería la ROI que después pasa a `grillas_mirova.yaml`.
- CÓMO REPRODUCIRLO: `python -I p102_compuerta.py <arbol>/experiments/_s162_v750b/analizar_v750b.py`.
- Arreglo, clase (i): **basta el procedimiento** y no hace falta adenda, porque el texto sellado ya es más estricto
  que el código. La regla del día es esta: nunca pasar `--leer-con-faltantes` si la línea «== control B0 y B1 = censo S159»
  dice FALLA con alguna clave `*_DISTINTO`. Si dice FALLA con `{}` (VF1-01), primero se corrige la ruta y se relee. Si dice
  OK, la bandera cubre sólo la cobertura. La regla tiene que quedar escrita en R4 §4 antes de leer, no decidirse después de
  ver la salida.

### P1-03 · CONFIRMADO · gravedad 3 · clase (i)
- TÍTULO: la población del generador depende de `VRP_PROFILE` del shell; R4 §3 no lo fija ni lo imprime.
- ARCHIVO:LÍNEA: `scripts/banco_paridad.py:60` en `main` (`os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")`: con la
  variable ya puesta no la toca). El filtro va por `es_pasada_diurna_descartada` (`scripts/auto_audit_weekly.py`, con
  `flag_viirs_diurno()` leído vivo de `pipeline.profile`, `pipeline/diurno.py:79-83`), y lo llaman
  `banco_paridad.indexar_referencia` (filas de MIROVA) y `cargar_nuestros` (records). Para Tupungatito y el resto, el
  negativo limpio exige `not ns["alerta"]` sobre la noche UTC (`banco_paridad.etiquetar`).
- SCRIPT:SALIDA: `p103_perfil.py` → `p103_perfil_salida.txt` (código de `main` 443da8649, un proceso por perfil). En Láscar, la
  pasada V750 del 2026-10-15 17:00 UTC (mediodía local) sale «descartada» con perfil vacío, con `mirova_equivalent` y con
  `experimental`, y **«no descartada» con `_s154_ab_diurno_k_on`**. Control: la nocturna de las 06:00 UTC no se
  descarta en ninguno, y MODIS diurno se descarta en todos.
- QUÉ PASA: con un perfil diurno en el shell entran las filas diurnas de MIROVA. Una alerta diurna del mismo día UTC marca
  la noche «con alerta» y saca a los negativos limpios nocturnos de esa fecha, que pasan a `sin_info` sin error y sin
  rastro (el perfil no se imprime ni va al meta de `poblacion_completa.json`). Los dos generadores corren en el mismo shell,
  así que el control de la adenda 2 sale IGUALES igual. Magnitud sobre datos reales: SIN DATO (no corrí el generador).
- CÓMO SE VE EN EL DASHBOARD: invisible; cambia E y P2 del veredicto.
- CÓMO REPRODUCIRLO: `python -I p103_perfil.py` (en la CARPETA, con `main443/` extraído).
- Arreglo, clase (i): en R4 §3, `unset VRP_PROFILE` (o `export VRP_PROFILE=mirova_equivalent`) y `echo "VRP_PROFILE=$VRP_PROFILE"`
  dentro de `gen1_salida.txt`, antes de los dos generadores y del lector.

### P1-05 · CONFIRMADO · gravedad 2 (el auditor da 3) · clase (i)
- TÍTULO: el veredicto no registra la identidad de sus insumos, se puede releer con otros argumentos y la salida se pisa.
- ARCHIVO:LÍNEA: `analizar_v750b.py:219` calcula `sha_obj` y sólo lo usa para cotejar `sin_granulo` (`:223`): no lo imprime.
  No imprime ningún sha de `--art`, `--censo-art` ni `--censo-objetivos`. `:198-200`, `salir()` hace `write_text` sin mirar si
  el archivo existe. `adenda3/leer_n3_v750b.py:151-152` pone por defecto una ruta fija dentro de la carpeta `adenda3/`.
  Vara: `PREREGISTRO_V750B.md:210-211`, TEXTO: «los resultados se juntan (un resultado "ok" reemplaza a uno fallido) y se
  lee una sola vez». Nada en el código impide la segunda lectura.
- QUÉ PASA: dos lecturas con insumos distintos (otro subconjunto de artefactos, otra lista) dejan la misma ruta de
  salida con la última, sin decir con qué insumos salió. Bajo el umbral de gravedad del auditor: equivocar la lista de
  objetivos casi siempre cae en el control K = producción (VF1-03), y en ese caso la lectura queda indecidible, no torcida.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: lectura del código, citado arriba (no corrí el analizador con datos).
- Arreglo, clase (i): guardar los sha256 de objetivos, sin_granulo, evaluador y artefactos (`sha256sum` en un archivo al
  lado), usar una salida con nombre nuevo que no exista y commitear la salida antes de mostrarla.

### P1-04 · CONFIRMADO · gravedad 2 (el auditor da 3) · clase (i)
- TÍTULO: el generador no avisa si `--data` está viejo o incompleto.
- ARCHIVO:LÍNEA: `objetivos_v750b.py:89-127` no mira la fecha máxima de los records. El único control de `01_poblacion.py`
  (`main`, l. 71) es `assert n_ref > 0 and recs`, que sólo detecta un instrumento muerto. El propio R4 lo dice
  (`r4/INFORME.md:25-26`, TEXTO: «con datos viejos la lista sale más corta sin aviso»).
- QUÉ PASA: un NRT detenido días antes del 11-03 (pipeline zombi) deja la ventana O sin sus últimas noches. La lista sale
  más corta sin error y el análisis lee menos pasadas, con menos poder, y puede que sin alguna protegida reciente. No se
  tuerce la dirección de ningún brazo en particular: todos pierden las mismas pasadas.
- CÓMO REPRODUCIRLO: lectura (no se corre el generador sobre datos reales).
- Arreglo, clase (i): antes del generador, por volcán, `max(datetime_utc)` de los records V750 de `data/mirova_equivalent`
  de main ≥ 2026-11-02, y que la fecha del último run verde de `nrt.yml` sea consistente con eso (regla 6 del workspace).

### P1-01 · CONFIRMADO EN PARTE · gravedad 2 (el auditor da 3) · clase (i)
- Confirmado: el lector corre desde el worktree (`r4/INFORME.md:70`, `R=<raíz del worktree>/experiments/_s162_v750b`).
  `analizar_v750b.py:36-42` toma `RAIZ = AQUI.parents[1]`, y `leer_n3_v750b.py:133` ejecuta con el `__file__` del sellado del
  worktree. Así `banco_paridad`, `clase_mirova`, el oráculo y `frontend/index.html` salen del worktree y no de `main`.
- No confirmado, el efecto: `p101_tablero.py` → `p101_tablero_salida.txt`. Hoy son idénticos entre `01ffd277b`, `443da8649` y
  `cc3887290` el texto de las 10 funciones que extrae `banco_paridad._JS`, las 2 constantes y los 11 `inner_radius_km`.
  `index.html` difiere en 6 líneas de aviso y comentario, y ese es el control positivo: el extractor ve la diferencia. Los diffs de
  `banco_paridad.py` y `clase_mirova.py` (worktree contra main) sólo agregan cosas, sin tocar `alerta_protegida`,
  `correr_node`, `CAMPOS_JS` ni `inner_desde_html` (`p101_diff_*.txt`). Además, una divergencia futura del predicado o
  de los inner caería en el control «K = producción»: `pub_prod` se calcula con el tablero de main al generar, y
  `P[(i,"K")]` con el del worktree al leer (`analizar_v750b.py:292`). La consecuencia sería una compuerta cerrada
  (indecidible), no un veredicto torcido.
- Arreglo, clase (i): correr el lector desde `$R4/arbol`, que ya trae el `index.html` de main y la carpeta sellada, o
  comprobar `sha256` de `frontend/index.html` del worktree contra `git show $M:frontend/index.html` antes de leer.

### P1-14 · CONFIRMADO · gravedad 2 · clase (i)
- TÍTULO: los dos generadores bajan la referencia viva de Mirova-v1 por separado.
- ARCHIVO:LÍNEA: los dos pasan por `01_poblacion.py` (`main`, l. 62: `bajar_remoto(Path(a.ref_dest))`; sellado
  `objetivos_v750b.py:95-99`; adenda 2 `objetivos_supl_v750b.py:115-120` y `:152-161`). `referencia_mirova_unificada.bajar_remoto`
  (main l. 191-200) pide en cada llamada el **último** commit que tocó cada CSV (`sha_remoto`, l. 184-188) y reescribe los
  archivos en `--ref-dest`. Ningún generador recibe el sha del otro ni lo compara.
- QUÉ PASA: si el scraper commitea entre las dos corridas, gen2 trabaja con otra referencia. El control
  (`objetivos_supl_v750b.py:150-161`, pos y neg_limpio campo por campo) cae si el cambio toca esas pasadas: rc 1, sin lista,
  y queda indecidible. Si el cambio toca sólo pasadas `far_ref` o `sin_info`, el control pasa y la lista suplementaria sale de
  otra referencia que la sellada, en silencio (sólo la adenda 2, que no decide). Los dos imprimen «referencia remota: {...}»: el
  rastro existe pero nadie lo coteja. En el ensayo del 10-30 los dos shas coincidieron (`r4/ensayo_20261029/gen1_salida.txt`
  y `gen2_salida.txt`, leídos con grep); en `verificador_v2` el sha era otro, de otra fecha.
- Arreglo, clase (i): comparar las dos líneas «referencia remota» (`diff <(grep "referencia remota" gen1) <(grep ... gen2)`)
  y, si difieren, rehacer las dos corridas. Las dos son selladas, así que no se tocan.

### P1-11 · CONFIRMADO · gravedad 2 · clase (ii) `experiments/_s162_v750a/evaluar_v750a.py` (sin tag de sello; pre-registro V750-A en BORRADOR, l. 3)
- ARCHIVO:LÍNEA: `evaluar_v750a.py:240-258`.
- SCRIPT:SALIDA: `p111_equivalencia_texto.py` → `p111_equivalencia_texto_salida.txt`. Un archivo escrito a mano, sin módulo,
  sin commit y sin sha, da `(True, ...)`. Control: la salida real del repo (línea base ROJA) da False, y el escrito a mano
  sin la línea VERDE da False. Además la línea VERDE de `equivalencia_v750a.py:206` no imprime ni el módulo
  (`--modulo` es libre, l. 175) ni su sha ni el commit, así que ni una salida verdadera se puede atar al módulo que juzgó.
- QUÉ PASA: un VERDE viejo, de un módulo anterior a un cambio, pasaría el §6.1 local.
- CÓMO REPRODUCIRLO: `python -I p111_equivalencia_texto.py <arbol>/experiments/_s162_v750a/evaluar_v750a.py <arbol>/experiments/_s162_v750a/equivalencia_v750a_salida.txt`.

### P1-12 · CONFIRMADO · gravedad 2 · clase (i) (es una corrida pendiente, no un cambio de código)
- SCRIPT:SALIDA: `p112_medidor.py` → `p112_medidor_salida.txt`. `mutar_evaluar_v750a.py` define M1 a M85, sin huecos, y
  `probar_evaluar_v750a.py`, 77 escenarios (E00 a E76). Ninguna salida del árbol cubre todas las mutaciones contra la
  batería entera. La mayor es `mutar_evaluar_v750a_salida.txt`, con M1 a M62 contra 61 escenarios y M1, M33, M34 y M36 en CAÍDA
  donde se esperaba ATRAPADA. El medidor no las cuenta como atrapadas, así que ahí no hay P-D. Luego vienen M63 a M80
  contra sólo 13 escenarios (E61 a E73) y M34 y M36 contra 61. **M81 a M85 no aparecen en ninguna salida.** Vara:
  `PREREGISTRO_V750A.md:284-286`, TEXTO: «Falta: la corrida completa del medidor sobre la batería entera».
- Matiz: el medidor en curso (PID 1324) puede ser justo esa corrida. Su resultado es SIN DATO para mí, porque no lo toqué.
- Arreglo: esperar esa corrida y no sellar V750-A sin una salida que liste M1 a M85 contra los 77.

### P1-13 · CONFIRMADO · gravedad 2 · clase (ii) `scripts/roi_v750b_a_grillas.py` y su prueba (rama `s169-roi-v750`, sin tag de sello)
- ARCHIVO:LÍNEA: `scripts/roi_v750b_a_grillas.py:64-76`. La prueba `tests/test_roi_v750b_variantes_s169.py` llama sólo a
  `R.variante` y `R.roi_por_volcan`, nunca a `main()`.
- SCRIPT:SALIDA: `p113_mutar_roi.py` → `p113_mutar_roi_salida.txt` (pytest sobre copias de `roi_vf/`). Identidad: verde,
  21 de 21. Control C1 (variante siempre `def`): ATRAPADA, 11 fallas. Control C2 (import roto): CAÍDA, no contada como
  atrapada. M5 (comentario sólo con B1): ATRAPADA. **NO ATRAPADAS: M1 (`--escribir` no escribe), M2 (escribe el YAML
  viejo), M3 (ignora `--brazo`, siempre B4) y M4 (acepta B6)**: 21 de 21 verdes en las cuatro. El control directo de `main()`
  sí escribe: B1 con `--escribir` deja `sens` en 11 de 11.
- QUÉ PASA: el paso que el día de la lectura escribe la ROI en el YAML no está probado. M2 y M3 dejarían en el YAML una ROI
  distinta de la elegida con la prueba en verde.
- CÓMO SE VE EN EL DASHBOARD: cuando se encienda la vía, la caja de VIIRS 750 sería otra que la elegida. Invisible al operador.
- Mitigación del día, clase (i): después de `--escribir`, `git diff` del YAML contra lo que espera el brazo, comparado a mano
  o con `yaml.safe_load`.

### P1-09 · CONFIRMADO · gravedad 1 (el auditor da 2) · clase (i)
- ARCHIVO:LÍNEA: `analizar_v750b.py:67-68`, `sha256` sobre bytes crudos. `r4/INFORME.md:70` da una copia ya hecha
  (`D:/vrp-trabajo/temporales/evaluar_d25_s161.py`) sin decir cómo se obtiene.
- SCRIPT:SALIDA: `p109_sha_evaluador_salida.txt`. `git show s161-d25-lectura:...evaluar_d25.py` da `2e557697...` con 0 CR,
  igual a `SHA_EVALUADOR`, y la misma con CRLF (control) da `93c26d62...`. La copia en disco hoy da `2e557697...` con 0 CR, y el
  repo tiene `core.autocrlf=true`, así que una copia hecha con checkout no pasaría.
- Por qué baja la gravedad: una copia con CRLF hace caer el `assert` antes de cualquier control. El analizador sale con
  error y la lectura no sigue: falla ruidosa, sin veredicto torcido y sin gasto de runner (la lectura es local).
- Receta, clase (i): `MSYS_NO_PATHCONV=1 git show s161-d25-lectura:experiments/_s157_prereg_d25/evaluar_d25.py > $EV` y
  `sha256sum $EV`.

### P1-07 · CONFIRMADO · gravedad 1 (el auditor da 2) · clase (ii) (script de informe nuevo, fuera de lo sellado)
- ARCHIVO:LÍNEA: `PREREGISTRO_V750B.md:106`, TEXTO: «Cortes informados por tramo: #535 (no separa brazos), adopción de K
  (2026-10-18 09:57 UTC).» Sólo hay estratos por cenit (`analizar_v750b.py:485-495`). `grep -rn "535\|08-28\|10-18"
  --include=*.py` sobre `experiments/_s162_v750b` da sólo `EXCLUIDOS` del generador (`objetivos_v750b.py:34`): nada informa
  por tramo.
- Por qué la gravedad baja a 1: el texto dice «informados», no decide. La adopción de K cae dentro de los días excluidos (17
  al 20 de octubre), así que el corte es limpio por fecha y lo puede informar un script aparte sobre los mismos
  artefactos, sin tocar lo sellado.

### P1-08 · CONFIRMADO · gravedad 1 (el auditor da 2) · clase (ii)
- ARCHIVO:LÍNEA: `PREREGISTRO_V750B.md:112-113`, TEXTO: «Si la sesión del instrumento ya mergeó el arreglo de
  FALSO_POSITIVO, se informa con y sin.» La condición se cumple: `git log -S "def resumir_pasadas"` da `744d8190b`
  (2026-10-25, «S162 instrumento T4+T6 ... (la tabla manda)», #903) en main. `git grep "resumir_pasadas|es_protegida|ocr_contradice"`
  sobre `experiments/_s162_v750b` en `01ffd277b` da 0: nada lo informa.
- Identificación: que «el arreglo de FALSO_POSITIVO» sea #903 lo deduzco de su docstring (punto 1: tabla FALSO_POSITIVO
  contra OCR ALERTA). Está bien apoyado, pero es una lectura mía. El mismo informe T4/T6 dice 0 casos medidos, de ahí la gravedad 1.

### P1-06 · CONFIRMADO EN PARTE · gravedad 1 (el auditor da 2) · clase (iii) si se quiere cambiar
- Confirmado: `adenda3/leer_n3_v750b.py:61-64` corta por día (`hora_utc[:10] < "2026-10-09"`), y el arreglo de Mirova-v1#20 llegó
  el 2026-10-09 a las 14:01 UTC (`scripts/clase_mirova.py:299-300` en main, TEXTO: «el arreglo de Suomi NPP llego el
  2026-10-09 a las 14:01 UTC, asi que las filas de esa manana quedan como de crater»). Una protegida sólo-OCR de Suomi NPP del
  09-oct de madrugada sigue vetando.
- No es texto contra código: `ADENDA3_V750B.md` §2, TEXTO: «la del 2026-10-09 en adelante siguen vetando». Es la
  convención por día de todo el proyecto (`clase_mirova`, `evaluar_d25.HITO_SNPP`), y va en la dirección conservadora (veta de más).
- Efecto en el ensayo: `r4/ensayo_20261029/n3_salida.txt` da 76 protegidas que deciden, 5 sin alerta de la tabla, 4 de
  Suomi NPP y las 4 N-3 (06-27, 07-03, 10-01, 10-05). **Ninguna del 09-oct** (ventana 2026-04-01 a 2026-10-29, con datos más
  viejos que main). El 11-03 se ve en esa misma cuenta de R4.

### P1-10 · CONFIRMADO EN PARTE · gravedad 1 (el auditor da 2) · clase (iii)
- Confirmado: `analizar_v750b.py:149-160`. «fuera» y «sin_crater» salen del denominador. Las protegidas no observadas se
  imprimen por nombre (`:228-230`) pero no entran a `prot_sin` (`:213, 227`), así que no frenan. `probe_v750b.py:149-151` y `:277-278`
  no cuentan «volcan_fuera_del_granulo» como faltante, y por eso el probe sale 0.
- No es defecto de código: lo manda el §4 sellado (`PREREGISTRO_V750B.md:114-115`, §4 (a), TEXTO: «(a) «no observada», fuera del denominador y contada aparte: volcán
  fuera del gránulo, o celdas sin dato en el 7 × 7 alrededor del **cráter**»).
  Además, la exclusión es pareja entre brazos, porque todos comparten el gránulo. Una protegida con cráter sin dato no puede hacer que un
  brazo pierda P1 frente a otro, sólo sale de P1 para todos. Puede esconder que el brazo elegido la pierde, pero lo imprime
  por nombre. Frecuencia en datos reales: SIN DATO.

## 4. Hallazgos propios

### VF1-01 · CONFIRMADO · gravedad 2
- TÍTULO: un censo apuntado a una ruta que no existe se imprime «FALLA», igual que un censo que salió distinto.
- SCRIPT:SALIDA: `p102b_censo_vacio.py` → `p102b_censo_vacio_salida.txt`. `cargar()` (`analizar_v750b.py:91-98`) sobre una
  ruta inexistente devuelve 0 pasadas sin excepción, y el control con un archivo real devuelve 1. Con 0 pasadas comunes,
  `cnt` queda vacío y `censo_ok = bool(cnt) and ...` (`:317`) es False: la salida es «control ... : {} FALLA».
- QUÉ PASA: un error de tipeo en `--censo-art` (R4 §4 lo pasa como ruta absoluta escrita a mano) y un oráculo que de verdad
  no reproduce el censo dan la misma palabra. Si quien lee aplica P1-02 al pie de la letra, una ruta errada puede llevar
  a pasar la bandera («el censo no se pudo correr»), o a no pasarla cuando sí correspondía.
- CÓMO REPRODUCIRLO: `python -I p102b_censo_vacio.py <arbol>/experiments/_s162_v750b/analizar_v750b.py`.
- Clase (i): antes de leer, `ls <censo-art>/**/resultados_*.json | wc -l` mayor que 0, y en la salida mirar si el dict viene vacío.

### VF1-02 · CONFIRMADO · gravedad 2
- TÍTULO: aplicar la ROI dos veces deja el comentario del YAML diciendo el brazo de la primera.
- ARCHIVO:LÍNEA: `scripts/roi_v750b_a_grillas.py:56-60` (rama `s169-roi-v750`). El comentario se reemplaza sólo si
  `COMENTARIO_VIEJO` aparece una vez, y después de la primera aplicación ya no aparece.
- SCRIPT:SALIDA: `p113_mutar_roi_salida.txt`, última sección. B1 y luego B4, ambos con `--escribir`, dejan los valores en B4
  (sens en 2, def en 9), pero el comentario sigue diciendo «Puesto por la lectura de V750-B: brazo B1». La prueba no lo ve,
  porque `test_variante_no_toca_otras_lineas` parte siempre del YAML de hoy.
- QUÉ PASA: el comentario que dice qué ROI rige puede mentir si alguien prueba un brazo y después aplica el elegido en el mismo
  árbol (P-G). Los valores, que son lo que lee la vía, quedan bien.
- Clase (ii): el script no está sellado.

### VF1-03 · CONFIRMADO (por lectura) · gravedad 2
- TÍTULO: el analizador empareja resultados con objetivos sólo por `id`, sin cotejar volcán ni hora.
- ARCHIVO:LÍNEA: `analizar_v750b.py:91-98` (`res[r["id"]] = r`) y `:205-209`. Cada resultado del probe trae `volcan` y `hora_utc`
  (`probe_v750b.py:140`), pero el analizador no los compara con `obj[i]`.
- QUÉ PASA: artefactos de un run despachado con otra versión de `objetivos_v750b.json` (ids reasignados por
  `objetivos_v750b.py:114-116`) se leerían contra otras pasadas. Lo atraparía casi siempre el control K = producción
  (K de otra pasada contra `pub_prod` y `pc_vrp` de ésta) y la compuerta se cerraría, pero no lo dice con su nombre. Un
  caso con casi todos los K vacíos y `pub_prod` falso podría pasar: SOSPECHA, no lo medí.
- Clase (i): verificar que el sha de `objetivos_v750b.json` en el tag del disparo sea el que se pasa a `--objetivos`.

### VF1-04 · CONFIRMADO · gravedad 1 (seguimiento ya anotado, sin arreglar)
- TÍTULO: `poblacion_completa.json` (que se commitea con los objetivos) lleva en el meta un commit fijo de los records.
- ARCHIVO:LÍNEA: `experiments/_s159/n/01_poblacion.py:145` en `main` 443da8649: `"data_records": "origin/main " + "533398f8f"`
  sea cual sea `--data`. Ya está anotado como seguimiento en `PREREGISTRO_V750B.md:539-540`, TEXTO: «`01_poblacion.py`
  escribe en el meta un commit fijo (`533398f8f`) aunque los records sean de otro».
- Clase (i): anotar `M` en el mensaje del tag del disparo (R4 ya lo hace en el `git tag -a`). El meta sigue mintiendo, pero no decide.

## 5. Secciones aparte

SEGUIMIENTOS
- `roi_v750b_a_grillas.py:70-75`: lee con `read_text` (que normaliza CRLF a LF) y escribe con `newline=""`. En un checkout
  de Windows con `core.autocrlf=true` cambia los finales de línea del archivo entero en el árbol de trabajo. Git lo
  normaliza al commitear, así que el contenido no cambia. No lo medí con un YAML en CRLF (mi copia es LF: «CRLF antes 0
  después 0»). SOSPECHA de ruido en `git status`, gravedad 1.
- `adenda1/leer_v750b.py:61` lanza el analizador con `sys.executable` sin `-I`. Si el lector se corre con el cwd dentro de
  una carpeta con un `json.py` u otro módulo homónimo, se carga ese. Fuera de mi eje, SOSPECHA, gravedad 1.

VERIFICADO LIMPIO (y contra qué vara)
- El analizador del árbol es el sellado: sha256 LF `83b7159b...` igual a `SHA_ANALIZADOR_LF` de `leer_n3_v750b.py:48`
  (`p102_compuerta_salida.txt`, primera línea). Vara: el tag `s162-v750b-sellado`, vía la constante del lector de la adenda 3.
- La copia del evaluador en disco tiene el sha del tag (`p109_sha_evaluador_salida.txt`). Vara: `git show` del tag
  `s161-d25-lectura`, hecho por mí.
- El predicado, los inner y `alerta_protegida` son idénticos entre el worktree y main hoy (`p101_*`). Vara: el texto de las
  funciones que extrae `banco_paridad._JS`, no el archivo entero (que sí difiere, y ése es el control).
- El medidor de V750-A no cuenta una CAÍDA como atrapada (`p112_medidor_salida.txt`: M1, M33, M34 y M36 salen «fuera de lo
  esperado»). Vara: el propio texto «(tiene que ser ATRAPADA)» de cada línea.

SIN DATO
- Magnitud sobre datos reales de P1-03, P1-04, P1-10 y P1-14: haría falta correr el generador o el run (prohibido).
- El resultado del medidor de V750-A en curso (PID 1324): no se toca.

FUERA DE ALCANCE
- El probe en GitHub Actions, el workflow, el oráculo `mirova_v750_r2.py` y la vía `pipeline/mirova_v750_codigo.py` más allá de
  `grilla_del_volcan` y `caja_roi`, que usa la prueba de la ROI.

## 6. Comparación con el auditor (hecha después de cerrar los veredictos de arriba)

Leí `f1_v750/INFORME.md` sólo después de escribir las secciones 1 a 5. No cambié ningún veredicto. Las coincidencias y
diferencias son estas:
- Coincidencia con medición independiente: P1-02, P1-13 (mis 4 mutaciones de `main()` y sus 5 NO ATRAPADAS de `main`
  y `--escribir` cuentan lo mismo, con clasificadores distintos) y P1-11.
- Duplicados: mi VF1-02 es su P1-17 y mi VF1-04 es su P1-15. Los encontré sin leerlo; cuentan una vez.
- Diferencias de confianza: P1-14 lo da como SOSPECHA y yo como CONFIRMADO en el mecanismo, por lectura de
  `bajar_remoto`/`sha_remoto`: cada corrida pide el último commit y reescribe `--ref-dest`. Que haya pasado o no el 11-03
  es SIN DATO para los dos. P1-06 lo da como SOSPECHA a falta de contar. Yo conté sobre la lista del ensayo (0 del 09-oct)
  y encontré que la regla está escrita así en la adenda 3, de ahí CONFIRMADO EN PARTE y gravedad 1. P1-10 lo da como SOSPECHA
  de diseño y yo como CONFIRMADO EN PARTE: el código hace lo que dice, el §4 sellado lo manda y la exclusión es pareja entre brazos.
- Diferencias de gravedad: bajo P1-01, P1-04 y P1-05 de 3 a 2 porque, medidos, desembocan en compuerta cerrada o en
  menos poder, no en un veredicto torcido. P1-01, además, tiene efecto nulo hoy. El dato del auditor, rama 1.446 commits detrás
  de main, refuerza el riesgo futuro y no cambia lo medido hoy. Bajo P1-06 a P1-10 a 1. P1-02 y P1-03 quedan en 3.
- Su P1-01 agrega un matiz que no anoté y que comparto, porque está en `analizar_v750b.py:298`: las pasadas con K distinto
  bajo el 1 % salen de todos los brazos y se listan por nombre (l. 296), no en silencio total.
- Sus P1-16, P1-18 y P1-19 no estaban en mi lista y no los verifiqué.
