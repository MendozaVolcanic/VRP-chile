# Verificador F3 (instrumentos de la sombra «código MIROVA»)

## 1. Encabezado

- Fecha y hora: 2026-10-30 04:13 UTC, reloj local del computador. Esta tarea prohíbe la red, así que no pude pedir la hora a un servidor.
- Commit medido: cc3887290 (origin/main), sobre el árbol `D:/vrp-trabajo/temporales/s169_audit_patrones/f3_comun/arbol/`. Comprobé que los 16 archivos que toco son idénticos byte a byte a `git show cc3887290:<ruta>` (sha256 IGUAL en los 16).
- Modelo: Claude Opus 5.5, esfuerzo bajo-medio, verificador con contexto limpio.
- CARPETA: `D:/vrp-trabajo/temporales/s169_audit_patrones/f3_verificador/`. Los scripts están en `scripts_v/` y cada salida, al lado (`*_salida.txt`).
- `caminos.md` quedó escrito y sellado antes de abrir cualquier archivo citado: sha256 0ecbf3a4..., a las 03:59:05 UTC.
- Lo que NO miré: los pre-registros (V750-A §4.3, V375-E §3.3, MOD-D §12.6), así que no sé si exigen un mínimo de pasadas o de protegidas, y eso condiciona la gravedad de P3-01. Tampoco miré `data/sombra_codigo_mirova/` (prohibido), la configuración de notificaciones de GitHub de Nicolás ni la retención de logs del repo. No abrí el informe del auditor (`INFORME_F3.md`, `hallazgos.csv`, `scripts_p3/`): todos los veredictos salen de mediciones mías. No corrí el pipeline ni bajé nada.

## 2. En una pantalla

- Confirmo los 15 hallazgos al menos en parte; ninguno queda refutado entero. La parte del BOM en P3-01 sí la refuto: con el encabezado real (la primera columna es `timestamp`), un BOM deja las 42.907 filas igual.
- Lo más grave: el evaluador común da `COBERTURA OK` con salida 0 cuando la referencia trae 0 pasadas en la ventana. Pasa con la referencia vieja (el snapshot de cc3887290 termina el 2026-10-26), con una vacía o con un sensor que no calza. No da ningún aviso (P3-01, gravedad 4).
- Desde el 2.º día, `revisar_sombra` no ve una corrida vacía (medido hasta el día 8) ni la falta de un sensor entero. Además, nadie vigila el workflow de la sombra: ni reproc-watchdog, ni nrt-monitor, ni la medición de la cadencia del cron (P3-02, P3-03, P3-09; gravedad 3).
- Hallazgo propio VF3-01: un solo record de K caído deja el job rojo 8 días seguidos, y ese rojo tapa las fallas nuevas.
- Antes del 2026-11-03 15:00 UTC conviene arreglar P3-02, P3-03, VF3-01 y P3-09. Los cuatro tocan sólo `scripts/revisar_sombra.py` y workflows, nada de pipeline/.

## 3. Veredictos

Cada veredicto lleva su gravedad y dos datos más: (a) si conviene arreglarlo antes del 2026-11-03 15:00 UTC, y (b) qué tocaría el arreglo.

### P3-01: el evaluador común da COBERTURA OK con referencia vieja, vacía o con BOM
- VEREDICTO: CONFIRMADO EN PARTE. Vieja y vacía, CONFIRMADO. BOM, REFUTADO con el formato actual: sólo rompería si `Volcan` fuera la primera columna.
- ARCHIVO:LÍNEA: `scripts/evaluador_comun.py:169` (el veredicto sólo mira tres listas, que salen vacías cuando hay 0 pasadas), `:856-857` (lo único que lo invalida además son los volcanes sin archivo) y `:898` (sale 0 con OK). `scripts/referencia_mirova_unificada.py:120` abre con `encoding="utf-8"`, sin `-sig`.
- SCRIPT:SALIDA: `scripts_v/p01_ref_vieja_vacia_bom.py` → `p01_salida.txt`. Ventana sintética del 2026-11-05 al 07, sensor VIIRS 750, y un hueco real: el brazo no tiene la pasada de las 06:10 que el control sí tiene.
  - Control positivo (la referencia lista esa pasada como protegida de 5 MW): exit 2, `INVALIDO POR INSTRUMENTO`, 1 protegida sin record.
  - Referencia vacía, sólo el encabezado: exit 0, `COBERTURA OK`, `pasadas_mirova` 0, ningún aviso.
  - Referencia vieja (snapshot de cc3887290; la última fecha es 2026-10-26 12:40 en el consolidado y 2026-10-29 13:00 en el OCR): exit 0, `COBERTURA OK`, 0 pasadas.
  - BOM con la alerta en el hueco: exit 2, INVALIDO, o sea que lo detecta. Sobre la referencia real, `leer_pasadas` da 42.907 filas con BOM y 42.907 sin BOM. Si reordeno las columnas para que `Volcan` vaya primera, quedan 0 de 2.000.
  - Un camino más (lo fundo aquí): en mi primer intento usé VIIRS 375 con filas `Sensor=VIIRS`, que la normalización lleva a VIIRS 750 (A48). Dio 0 pasadas y `COBERTURA OK`. La causa de fondo es una sola: el evaluador no exige ningún mínimo de pasadas de MIROVA.
- QUÉ PASA: si la referencia no cubre la ventana, el instrumento no tiene contra qué medir y lo declara sano. «Sin pasadas» se lee como «sin huecos».
- DASHBOARD: invisible. Lo tuerce el veredicto del A/B o de la sombra: «0 protegidas perdidas» sobre 0 protegidas.
- REPRODUCIR: `python -I -B scripts_v/p01_ref_vieja_vacia_bom.py <arbol> <carpeta>`
- GRAVEDAD: 4. Sería 5 si el pre-registro no exige un mínimo de pasadas, cosa que no verifiqué.
- (a) No hace falta para la corrida del 03-nov, porque el evaluador no lee la sombra ese día. Sí antes de la primera lectura del A/B. (b) Toca scripts/.

### P3-02: revisar_sombra no ve una corrida vacía desde el 2.º día
- VEREDICTO: CONFIRMADO.
- ARCHIVO:LÍNEA: `scripts/revisar_sombra.py:27` cuenta todos los records de la ventana de 8 días y `:40` falla sólo si `via == 0`. En `.github/workflows/sombra-codigo-mirova.yml:147-151` el paso corre después del commit, sobre el JSON del checkout, que ya trae los días anteriores.
- SCRIPT:SALIDA: `scripts_v/p02_p03_revisar.py` → `p02_p03_salida.txt`.
  - Control: el día 1 con el JSON vacío falla.
  - Día 2 sin nada nuevo y sin `ERROR processing`: verde.
  - Día 9, con el log diciendo «Cobertura NO COMPLETA: 30 búsquedas fallidas»: verde. Sólo busca `ERROR processing`, nunca «Cobertura INCOMPLETA».
  - Sale rojo recién cuando el último dato bueno queda fuera de la ventana: el día 12 de mi caso, o sea a los 9 días.
- QUÉ PASA: si NASA no entrega gránulos o la búsqueda falla, `run_pipeline` sale 0 y sólo imprime la cobertura. El vigía cuenta records viejos como si fueran de hoy y la sombra queda sin datos hasta 8 días con el job verde.
- DASHBOARD: invisible (la sombra no va al tablero). Deja indecidible la sombra.
- REPRODUCIR: `python -I -B scripts_v/p02_p03_revisar.py <arbol>`
- GRAVEDAD: 3.
- (a) Sí: es el único vigía diario y queda ciego desde el 04-nov. (b) Toca scripts/ (contar los records con `processed_utc` de esta corrida, o los nuevos contra el JSON previo, y leer la cobertura del log). Opcionalmente el workflow.

### P3-03: revisar_sombra no exige records por sensor ni por volcán y sensor
- VEREDICTO: CONFIRMADO.
- ARCHIVO:LÍNEA: `scripts/revisar_sombra.py:28,40` sólo suma `via` total. Un sensor puede desaparecer sin que ningún gránulo dé `ERROR processing`: en `scripts/run_pipeline.py:248-250` (y 292-294, 341-343), un L1B sin geolocalización hace `continue` con una incidencia, sin error.
- SCRIPT:SALIDA: `p02_p03_salida.txt`, caso `P3-03_solo_viirs375_sin_modis_ni_v750`: verde con 2 records de VIIRS 375 y ninguno de MODIS ni de VIIRS 750.
- QUÉ PASA: la vía MODIS (MOD-D fase 4) o la VIIRS 750 pueden quedarse sin datos semanas mientras VIIRS 375 mantiene el job verde.
- DASHBOARD: invisible.
- GRAVEDAD: 3. Exigir un sensor por día daría falsas alarmas, porque un día sin pasada de un sensor puede ser legítimo. El chequeo sensato es por ventana de 8 días.
- (a) Sí, junto con P3-02, que es el mismo archivo. (b) Toca scripts/.

### P3-04: los gránulos descartados por la vía y la cobertura del run no dejan rastro
- VEREDICTO: CONFIRMADO EN PARTE.
- ARCHIVO:LÍNEA:
  - `pipeline/process_viirs.py:773-774,781-782`, `process_viirs_mod.py:509-510,517-518` y `process_modis.py:657-658` devuelven `return None` sin imprimir nada.
  - `pipeline/mirova_v750_codigo.py:756-757` devuelve None si falta una banda en el L1B (es un defecto del dato) y `:798-808` si no hay grilla o si el gránulo no cubre el volcán (eso es legítimo). `run_pipeline.py:265/310/357` no imprime nada con `None`. Las dos causas se ven idénticas en el log.
  - En K, una banda ausente hace que `read_viirs_mod_l1b` devuelva el dict sin M13 (`process_viirs_mod.py:236-237`). SOSPECHA: eso termina en `ERROR processing`, que es más ruidoso que la vía; no lo tracé hasta el final.
  - `.github/workflows/sombra-codigo-mirova.yml:122-123` corre sin `--cobertura-json`, sin `upload-artifact` y sin guardar el `pipeline.log`.
- Parte que NO se sostiene: «sin rastro» de cobertura. `informar_cobertura` (`scripts/run_pipeline.py:441-528`) imprime al log, al `GITHUB_STEP_SUMMARY` y como anotaciones `::warning`. Rastro hay, aunque efímero (retención de logs del repo, SIN DATO) y no legible por máquina. Por eso `evaluador_comun.huecos` deja la causa de las ausencias de la sombra como «sin cobertura» (`evaluador_comun.py:854`).
- DASHBOARD: invisible.
- GRAVEDAD: 2. El evaluador ya trata como «no observado» lo que no tiene record (T2), así que no tuerce el veredicto; sólo esconde la causa.
- (a) Sí, para la parte del workflow: agregar `--cobertura-json` y subir el JSON y el log como artefacto es barato y deja la causa de cada día desde el primero. El aviso en `return None` no puede ir antes, porque toca pipeline/, que está congelado. (b) Workflow, más pipeline/ si se quiere el aviso.

### P3-05: la línea de log de VIIRS 375 es ciega con records de la vía
- VEREDICTO: CONFIRMADO.
- ARCHIVO:LÍNEA: `scripts/run_pipeline.py:321-327` imprime `vrp_mir_mw`, `vrp_tir_mw`, `t_max_i04_k` y `n_vent_pixels`. Ninguna de esas llaves existe en `pipeline/mirova_v750_codigo.py` (grep: 0), y el record de la vía trae `vrp_vent_mw: 0.0` fijo (l. 704). MODIS y V750 (l. 276-278 y 368-370) sí muestran `vrp_mw`, pero no dicen ni la vía ni si el store escribió.
- SCRIPT:SALIDA: `scripts_v/p05_linea_log.py` → `p05_salida.txt`. Con un record de la vía de 3,2 MW y otro sin nada, las líneas salen IDÉNTICAS (`VRP_MIR=None ... (Nonepx)`). El control con K da líneas distintas.
- Matiz: `store.py:302,308` escribe `vrp_mir_mw` cuando hay píxeles fuera del radio. Como `result` es el mismo objeto, en ese caso la línea podría mostrar un valor. Es un borde, y la mutación del mismo objeto no la verifiqué.
- GRAVEDAD: 1. Sólo confunde a quien lee el log; `revisar_sombra` no usa esa línea.
- (a) No. (b) Toca `scripts/run_pipeline.py`. Es el ejecutor de la sombra: cambiarlo cambia el sha del record, aunque no toque pipeline/.

### P3-06: VRP_PROFILE ambiental cambia lo que se lee como pasada diurna
- VEREDICTO: CONFIRMADO EN PARTE. El mecanismo es real, pero hoy no tiene efecto con los perfiles que importan.
- ARCHIVO:LÍNEA: `scripts/evaluador_comun.py:53` y `banco_paridad.py:60` usan `os.environ.setdefault`, así que gana el valor que ya esté en el entorno. `auto_audit_weekly.py:295-300` lee `ENABLE_DAYTIME_MODIS` (importado en la l. 46) y `flag_viirs_diurno()` del perfil activo.
- SCRIPT:SALIDA: `scripts_v/p06_perfil_diurno.py` → `p06_salida.txt`, Láscar, VIIRS 375 y 750 a las 18:00 UTC.
  - Sin VRP_PROFILE, con `mirova_equivalent`, `sombra_codigo_mirova` o `experimental`: descartada `true` en los tres sensores (igual en todos).
  - Control positivo `_s154_ab_diurno_k_on`: VIIRS diurno descartada `false`.
  - Ningún workflow que corra el evaluador fija VRP_PROFILE a nivel `env` (grep). El de la sombra lo pone en línea y sólo para un comando (l. 110).
- GRAVEDAD: 2. Para torcer algo hace falta un perfil diurno exportado en la shell.
- (a) No. (b) Toca scripts/.

### P3-07: el evaluador común no deja procedencia y --salida pisa
- VEREDICTO: CONFIRMADO EN PARTE.
- ARCHIVO:LÍNEA: el dict `res` (`evaluador_comun.py:837-848`) guarda la ventana, los sensores, `canal`, `regla_minimas` y los días excluidos. Esos parámetros sí quedan registrados. Lo que NO guarda: la ruta ni el sha de la referencia, las rutas de los lados, el sha del código ni el sha de `frontend/index.html`. Un grep de `sha|hashlib` en el evaluador da 0. El contraste es `banco_paridad.py:497-518`, que sí guarda `sha_index_html` y la procedencia. Además, `:897` hace `write_text` sobre `--salida` sin comprobar si el archivo existe.
- GRAVEDAD: 3. Un veredicto no se puede reproducir ni atar a la referencia exacta, y con P3-01 eso importa.
- (a) Antes de la primera lectura, no del 03-nov. (b) Toca scripts/.

### P3-08: el sha del record es el HEAD del disparo y el commit de la sombra no lo lleva
- VEREDICTO: CONFIRMADO EN PARTE.
- ARCHIVO:LÍNEA: `pipeline/store.py:89-94` toma `GITHUB_SHA` y `:549` lo escribe en cada record. El workflow, en `:135`, hace un commit con sólo la fecha. Los hechos son ciertos.
- Parte que no se sostiene: con `actions/checkout@v5` sin `ref` (l. 75), el código que corre es justo `GITHUB_SHA`. Eso es lo que conozco de la acción; sin red no lo verifiqué en esta sesión, así que queda como SOSPECHA de alta confianza. El sha identifica bien el código, incluido pipeline/. Para saber si pipeline/ cambió entre dos records basta `git diff sha1 sha2 -- pipeline/`. Lo que falta es comodidad (un sha del árbol de pipeline/), no información.
- Defecto real aparte, fuera de la sombra: con `origen: "local"`, `_sha_git_local` (l. 78-86) da el HEAD aunque el árbol esté sucio, y nada marca los cambios sin commitear.
- GRAVEDAD: 2.
- (a) Opcional y barato: poner `$GITHUB_SHA` en el mensaje del commit. (b) El workflow. Un sha del árbol de pipeline/ en el record tocaría `store.py`, que está congelado.

### P3-09: nadie vigila el run de la sombra
- VEREDICTO: CONFIRMADO.
- ARCHIVO:LÍNEA:
  - `.github/workflows/reproc-watchdog.yml:109-115` sólo mira las rutas `/reproc-`.
  - `nrt-monitor.yml:44` sólo mira `nrt.yml`.
  - `scripts/medir_cadencia_cron.py:37-40` espera 4 workflows, ninguno de la sombra.
  - `vigilancia-sombra.yml` vigila la otra sombra (K contra `experimental_v2`, l. 3-8 y 15).
  - `sombra-codigo-mirova.yml` no tiene ningún paso que abra un issue. Un grep de `sombra` en los otros workflows da 0.
- Camino no verificado: GitHub puede mandar un correo cuando falla un workflow programado (SIN DATO: la configuración de Nicolás). Una corrida que no llega (como la caída de eventos `schedule` del 2026-08-27, citada en `nrt-healthcheck.yml`) no genera nada.
- GRAVEDAD: 3. Además encadena con P3-02 y VF3-01: un rojo que nadie ve vale lo mismo que un verde ciego.
- (a) Sí: barato y sólo del workflow (un paso `if: failure()` que abra un issue, más la sombra en la lista de cadencia). (b) Workflow y `scripts/medir_cadencia_cron.py`.

### P3-10: cargar_lado no filtra via_codigo_mirova ni cuenta las fechas ilegibles
- VEREDICTO: CONFIRMADO.
- ARCHIVO:LÍNEA: `scripts/evaluador_comun.py:760-768`: no filtra `via_codigo_mirova`, y los `continue` de la l. 763 (bucket None) y de las l. 767-768 (fecha ilegible) no dejan conteo.
- SCRIPT:SALIDA: `scripts_v/p10_p11_p13.py` → `p10_p11_p13_salida.txt`. De 4 records, carga 2: uno de la vía y uno `via_codigo_mirova: "sin_mxd03"` (K caído). Los otros 2 (sensor None y `06:55:30`) desaparecen sin mensaje.
- Cadena: `revisar_sombra` pone rojo el job cuando hay un record de K, pero el commit ya ocurrió (workflow l. 144-146, a propósito). Ese record queda en `data/sombra_codigo_mirova/` y el evaluador lo lee como si fuera de la vía.
- Sustrato: desde run_pipeline, «sin_mxd03» no puede salir (MODIS exige geo en la l. 248). «geo_distinta» y «sin_grilla» sí pueden. Frecuencia: SIN DATO.
- GRAVEDAD: 3. Un record de K con una protegida entraría al brazo «código MIROVA».
- (a) Antes de la primera lectura. (b) Toca scripts/.

### P3-11: --ref deja el respaldo y las filas perdidas como opcionales en silencio, con nombres distintos a los del repo
- VEREDICTO: CONFIRMADO EN PARTE.
- ARCHIVO:LÍNEA: `scripts/evaluador_comun.py:818-821` (`opc` devuelve None en silencio) y `:806-807`. En el repo los nombres son `registro_vrp_consolidado_respaldo_20260408.csv` y `consolidado_filas_perdidas.csv` (`referencia_mirova_unificada.py:74,76`).
- SCRIPT:SALIDA: `p10_p11_p13_salida.txt`. Con una carpeta que usa los nombres del repo, el respaldo queda en None (no calza) y el histórico SÍ entra (el nombre coincide). Las filas medidas: sin capas 44.085, con el respaldo 44.841, con el histórico 46.588, con ambas 46.588.
- Lo que se sostiene: el nombre distinto afecta sólo al respaldo, y en cc3887290 el respaldo no aporta ninguna fila cuando el histórico está. Lo que sí pesa es que el histórico (2.503 filas, 109 de octubre de 2026) puede faltar sin aviso.
- GRAVEDAD: 2. Para la sombra (desde el 03-nov) hoy no tiene efecto; afecta a los A/B sobre ventanas de enero a octubre.
- (a) No es para el 03-nov. (b) Toca scripts/.

### P3-12: alerta_protegida y es_protegida cuentan un VRP nan como protegida
- VEREDICTO: CONFIRMADO.
- ARCHIVO:LÍNEA: `scripts/clase_mirova.py:72` y `:281` hacen `v is None or v < umbral`, y `nan < 1` es False. `referencia_mirova_unificada._float` (l. 89-93) convierte «nan» o «inf» en float.
- SCRIPT:SALIDA: `scripts_v/p12_nan.py` → `p12_salida.txt`. `alerta_protegida` da True con nan y con inf (los controles: 5,0 da True, 0,5 da False, None da False). Una pasada nan con `resumir_pasadas` también resulta protegida. Sustrato: 0 valores no finitos en 57.907 filas de los 4 CSV de cc3887290.
- GRAVEDAD: 2. Es latente: si apareciera tendría veto en un A/B, pero hoy no hay sustrato.
- (a) No. (b) Toca scripts/.

### P3-13: cargar_filas_referencia del auto-audit cae en silencio al cargador canónico
- VEREDICTO: CONFIRMADO.
- ARCHIVO:LÍNEA: `scripts/auto_audit_weekly.py:659-665` atrapa `except Exception: return None`, y `:549-552` usa entonces las alertas deduplicadas. El docstring de las l. 544-545 admite que eso diverge. `filas_ref` no aparece en ninguna salida (grep: 4 apariciones, todas internas).
- SCRIPT:SALIDA: `p10_p11_p13_salida.txt`. Con un CONS inexistente devuelve `None` y no imprime nada.
- GRAVEDAD: 2. El auto-audit no lee la sombra, así que queda fuera de su decisión.
- (a) No. (b) Toca scripts/.

### P3-14: evaluador_comun nunca llama a calidad_referencia_mirova.avisar
- VEREDICTO: CONFIRMADO.
- ARCHIVO:LÍNEA: grep de `avisar|calidad_referencia|indexar_referencia` en `evaluador_comun.py`, `clase_mirova.py` y `referencia_mirova_unificada.py`: 0 (sólo la palabra «avisar» en un comentario de la l. 826). El contraste es `banco_paridad.py:221-225`.
- SCRIPT:SALIDA: `p14_salida.txt`. Para la ventana 2026-11-03 a 12-31 da 0 avisos; para 2026 entero, 13.
- GRAVEDAD: 1 para la sombra (no tiene efecto) y 2 para A/B históricos.
- (a) No. (b) Toca scripts/.

### P3-15: la fecha mínima se aplica a las fechas pedidas, no al datetime_utc de cada record
- VEREDICTO: CONFIRMADO en el mecanismo. Que tenga sustrato es SOSPECHA, y probablemente no lo tiene.
- ARCHIVO:LÍNEA: `scripts/ventana_sombra.py:39-46`. `pipeline/fetch.py:608-637` asigna a un día D todo gránulo que lo toque con los bordes incluidos, y `datetime_utc` sale del nombre, que es la hora de inicio (`process_viirs.py:785`, `process_modis.py:661`). Un gránulo de 23:54 a 00:00 del 02-nov entraría con fecha 2026-11-02.
- `revisar_sombra.py:27` sí filtra por `datetime_utc`, así que no cuenta ese record.
- Las pasadas sobre Chile caen a unas 01:30-07:00 y 14:00-19:30 UTC. Es razonamiento orbital mío, no medido. No sé de ninguna cerca de las 00:00 UTC.
- GRAVEDAD: 1.
- (a) No. (b) Toca scripts/ (el lector puede filtrar por `datetime_utc`).

### VF3-01 (propio): un record de K caído deja el job rojo 8 días seguidos y tapa las fallas nuevas
- ARCHIVO:LÍNEA: `scripts/revisar_sombra.py:27-39`. `otros` se cuenta sobre los 8 días de la ventana, no sobre lo que escribió esta corrida.
- SCRIPT:SALIDA: `scripts_v/vf_rojo_arrastrado.py` → `vf_rojo_arrastrado_salida.txt`. Con un record `geo_distinta` del 05-nov, el job sale rojo del 05 al 12-nov aunque esas corridas estén sanas, y vuelve a verde el 13. El control, sin ese record, sale verde todos los días.
- QUÉ PASA: un rojo permanente se vuelve ruido, y una corrida vacía real dentro de esos días no se distingue. Es la cara inversa de P3-02.
- DASHBOARD: invisible.
- CONFIANZA: CONFIRMADO, por medición. Que un `geo_distinta` real ocurra es SIN DATO; si el reproceso de días siguientes lo reemplaza por un record de la vía, el rojo se corta antes (no lo verifiqué).
- GRAVEDAD: 2.
- (a) Sí, junto con P3-02, porque el arreglo es el mismo: contar lo escrito en la corrida. (b) Toca scripts/.

## 4. Secciones aparte

SEGUIMIENTOS
- `store._sha_git_local` (`pipeline/store.py:78-86`): en corridas locales el sha no marca un árbol sucio. Confianza: CONFIRMADO por lectura. Gravedad 2.
- Duplicados fundidos: el sensor que no calza con la referencia lo fundí en P3-01, porque la causa es la misma (sin mínimo de pasadas). La «Cobertura INCOMPLETA» que `revisar_sombra` no lee la fundí en P3-02.

VERIFICADO LIMPIO
- `revisar_sombra` sí detecta `ERROR processing` y los records que no son de la vía (controles en `p02_p03_salida.txt`), y sí falla el día 1 con el JSON vacío. La vara fue el escenario de falla construido a mano.
- El evaluador sí da INVALIDO con un hueco real cuando la referencia cubre la ventana (control positivo de P3-01). La vara: una pasada protegida que falta en el brazo y que el control sí tiene.
- El BOM sobre los CSV reales de MIROVA no pierde filas (42.907 contra 42.907). La vara: el encabezado real de cc3887290.
- La hora de los records es `%Y-%m-%d %H:%M` en los tres procesadores (`_parse_datetime`), así que el `except ValueError` de `cargar_lado` no tiene sustrato hoy.
- El árbol de la auditoría es idéntico a cc3887290 en los 16 archivos que toqué (sha256).

SIN DATO
- Si los pre-registros exigen un mínimo de pasadas o de protegidas: define si P3-01 es 4 o 5.
- La retención de logs de Actions del repo y las notificaciones por correo de Nicolás (P3-04, P3-09).
- La frecuencia real de `geo_distinta` o `sin_grilla` en la sombra (P3-10, VF3-01).
- El comportamiento exacto de `actions/checkout@v5` con `schedule` (P3-08): sin red.

FUERA DE ALCANCE
- Arreglar cualquier cosa, leer `data/sombra_codigo_mirova/` y correr el pipeline.

## 5. Nota posterior a los veredictos (después de abrir INFORME_F3.md, sólo para P3-01)
El auditor midió el BOM con un CSV sintético de 1 fila (`scripts_p3/p3_03_evaluador_ref.py`, caso B3a: «0 filas leídas (1 sin BOM)») y explica la pérdida porque «ninguna fila tenga `Volcan`» (INFORME_F3.md l. 31). Eso pasa sólo si `Volcan` es la primera columna. En los cuatro CSV de cc3887290 la primera columna es `timestamp`: el BOM se pega a esa columna y no cambia ninguna fila (42.907 de 42.907, `p01_salida.txt`). La diferencia es de formato de entrada, no de código. Mantengo el veredicto: la parte del BOM queda REFUTADA para el formato actual y es latente si Mirova-v1 reordena columnas.
