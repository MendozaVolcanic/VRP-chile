# Verificación v2: encendido de la vía «código MIROVA» en MODIS (PR A + PR B)

## Encabezado

- Hora del servidor (GitHub `Date`): lunes 2026-11-02 01:44:52 GMT al cerrar (01:35:33 al abrir).
- Commit sobre el que medí: worktree de sólo lectura `D:/vrp-trabajo/worktrees/s172-miniaud-b`, HEAD b42823194 (PR B). Para PR A solo, `git show`/`git diff` contra c83882fcf y la base d3cd0b2ae; los tres scripts de vigilancia y la store son byte a byte los mismos en c83882fcf y b42823194 (`git rev-parse` de ambos lados, ver más abajo). `origin/main` 14fb62030 no cambia `nrt.yml` ni `requirements.txt` respecto de b42823194.
- Modelo: Sonnet 5.5 (claude-sonnet-5-5). Esfuerzo pedido: alto. Esfuerzo real: el arnés de esta sesión fijó esfuerzo bajo (10); lo declaro porque pedía «el que realmente usaste».
- CARPETA: `D:/vrp-trabajo/temporales/s172_miniaud/v2`.
- caminos.md escrito antes de abrir ningún archivo citado; sha256 final del archivo (con su pie): `7c36a835a7cdb7ac3f79b9aba8e0e6d517d33c72cf1ab66358cda14cb53af764`. El sha256 del contenido anterior al pie es `0f7a7ac5291838e0e1efd5538728b4bd976415b3e637c987d43def368781319d`.
- Llamadas a la API de GitHub usadas: 5 de 30 (todas GET): fecha del servidor (x2), lista de corridas del NRT, jobs del run 41353423746 (x2) y el log del job de Láscar de ese run.
- No abrí ningún INFORME.md ni hallazgos.csv de f1, f2, f3. Sí abrí `D:/vrp-trabajo/temporales/audit_s171_dia3/INFORME.md` (informe de otra auditoría, la de S171) sólo para ubicar el origen de la cifra «1,1 a 1,25» del ítem 209.
- Qué NO miré: la reversión limpia (`git revert` del PR B sobre el main del día; no estaba en mi lista), la suite completa de pruebas (no la corro), el lector de V375-E re-sellado, el contenido del frontend (`cambio_detector.js`) más allá de buscar la constante del ítem 207, la corrida real de MODIS con la vía (pyhdf no corre en Windows) y el costo real de la vía en el runner.

## En una pantalla

1. 201 y 301 son el mismo defecto y se CONFIRMAN: el NRT instala `earthaccess numpy h5py scipy pyyaml pyhdf` y no `pyproj` (log real del run 41353423746 del 2026-11-01, sin ninguna línea con pyproj); con el PR B cada gránulo MODIS que llegue a `remuestrear_grilla` lanza `ModuleNotFoundError`, `run_pipeline.py` lo atrapa (`ERROR processing`, salida 0) y no se escribe record: producción deja de escribir MODIS en los 11 volcanes (los 11 tienen grilla MODIS). Gravedad 5. Bloquea el PR B. Cambio mínimo: `pyproj` en la línea de `pip install` de `nrt.yml` (y de `backfill-tier-a.yml`, mismo defecto, hallazgo nuevo VMA172-201) más un guard.
2. La vigilancia de PR A SÍ lo atraparía, tarde: `avisos_via` da VIGILANCIA_CIEGA el mismo día y la auditoría semanal da DEGRADADO el lunes; el stale-gate del NRT y el healthcheck no lo ven (miran el último record de cualquier sensor, y VIIRS sigue escribiendo).
3. 202 se CONFIRMA en el código (una protegida con guardia que publica y producción SIN record da VERDE; con record que calla da REVERSION_CANDIDATA, medido con el control), gravedad 3; 203, 204, 206 y 209 se CONFIRMAN EN PARTE (gravedad 2); 207 y 208 se CONFIRMAN (gravedad 2). Ninguno de esos seis bloquea ni PR A ni PR B; 202 y 207 conviene corregirlos antes de sellar la regla.
4. Dos hallazgos nuevos (VMA172-201 backfill sin pyproj, gravedad 3; VMA172-202 sin respaldo a K ante cualquier excepción de la vía, gravedad 2) y uno de contexto (VMA172-203 los dos controles de frescura del NRT son ciegos por sensor).
5. Rango de IDs propios: VMA172-201 a VMA172-203.

## Veredictos por ítem

Para cada ítem: veredicto, gravedad mía, si bloquea, cambio mínimo (sin aplicar).

### MA172-201 + MA172-301 (fundidos: mismo defecto en dos frentes): CONFIRMADO, gravedad 5, BLOQUEA EL PR B

Instrumento y preguntas:
1. Si la vía estuviera rota por falta de pyproj, ¿esta medición lo vería? Sí: el log real del runner lista lo instalado, y mi script reproduce la excepción con pyproj bloqueado (control positivo: la misma llamada con pyproj funciona).
2. Si el instrumento estuviera muerto, ¿se vería distinto? Sí: el script imprime las dos ramas (con y sin pyproj) y dan resultados distintos.

Evidencia (todo de esta sesión):
- `nrt.yml` l. 140-143 (leídas): `pip install pyhdf` y `pip install earthaccess numpy h5py scipy pyyaml`. No hay otra línea que instale pyproj; `requirements.txt` sí lo lista (l. 4) pero el NRT no lo usa (el paso `Install dependencies` no hace `pip install -r`).
- Runner real, no el yml: `D:/vrp-trabajo/temporales/s172_miniaud/v2/nrt_log_lascar_41353423746.txt` (job 124988304577, run 41353423746, SHA ffccf6c9f, 2026-11-01 21:42 UTC): las dos líneas `Successfully installed` (l. 336 y 447) no incluyen pyproj; `grep pyproj` sobre el log completo no da nada. La versión de earthaccess instalada (0.17.0) no trae pyproj como dependencia (lista de `Requires` del paquete local 0.17.0 y de lo instalado en el runner).
- Cadena de llamada: `pipeline/process_modis.py` l. 637-652 (con `ENABLE_MODIS_CODIGO_MIROVA` verdadero, volcán con grilla y `geo_path` presente) llama `_MV.calcular_vrp_granulo`; esa función (l. ~814 de `mirova_v750_codigo.py`) llama `remuestrear_grilla`, que hace `from pyproj import Transformer` en l. 204 (import perezoso: el módulo se importa bien y recién falla al llamar). No hay `try/except` en la cadena. `scripts/run_pipeline.py` l. 279-280: `except Exception as e: print(f"  ERROR processing {l1b.name}: {e}")` y sigue; no hay respaldo a K ni escritura de record.
- Cobertura: `v201b_salida.txt`: los 11 Tier A tienen grilla MODIS (`grilla MODIS: True` en los 11), así que los 11 caen al camino que necesita pyproj. MxD03 sí se descarga en el NRT (`SEARCH_GEO_DONE MODIS_TERRA n_geo=2` en el log), así que no salen por `sin_mxd03`.
- Reproducción: `v201_sin_pyproj.py` → `v201_salida.txt`: `ENABLE_MODIS_CODIGO_MIROVA = True`, «CON pyproj: OK [(51, 51), (51, 51)]», «SIN pyproj: EXCEPCION ModuleNotFoundError import of pyproj halted; None in sys.modules».
- Nadie en el NRT lo ve: en `nrt.yml` no hay ningún grep de `ERROR processing` (sólo `NASA_AUTH_UNREACHABLE`); el job queda verde.
- Quién sí lo vería: `vigilancia_guardia_modis.avisos_via(True, None, [])` devuelve el aviso «la vía no está escribiendo» (`v203_204_208_salida.txt`), que convierte VERDE en VIGILANCIA_CIEGA y abre issue en el cron de las 22:45 UTC; la auditoría semanal (`audit-weekly.yml`, lunes) lo daría como DEGRADADO por protegidas sin record. Eso acota la ventana a un día en el mejor caso, no la elimina: durante ese tiempo MODIS de producción es cero y no hay respaldo automático a K.
- Por qué es la gravedad que es: el fallo es determinista (ocurre en la primera pasada que llegue después del merge), silencioso en el NRT y total sobre el sensor que justifica el PR. No le asigno 4 (como el otro frente) porque el mecanismo de detección de PR A llega rápido pero no impide el hueco, y porque revierte exactamente lo que el PR B quiere mejorar (Chillán).
- La prueba del PR B no lo cubre: `tests/test_sombra_codigo_mirova_s167.py` l. 160-170 comprueba que el workflow de la SOMBRA instala pyproj; ninguna prueba mira el `Install dependencies` de `nrt.yml` ni el de la guardia contra los flags activos (grep de `pip install` en `tests/*.py`: sólo ese archivo).

Bloquea: PR B (el que enciende el flag). PR A no lo bloquea (con el flag apagado la vía no corre; la guardia es K y el comentario de `guardia-k-modis.yml` l. 90 dice, con razón, que no necesita pyproj).

Cambio mínimo: agregar `pyproj` a la línea `pip install earthaccess numpy h5py scipy pyyaml` de `nrt.yml` l. 143 (puede ir en PR A, inerte con el flag apagado; si va en PR B, revertir el PR B lo quita también y no hace daño) y un guard que falle si algún flag `enable_*_codigo_mirova` está en true en `mirova_equivalent` y un workflow que corre ese perfil no instala pyproj (ver VMA172-201 para los otros workflows).

### MA172-202: CONFIRMADO, gravedad 3, no bloquea ninguno; corregir antes de sellar la regla

- `scripts/vigilancia_guardia_modis.py`, función `disparadores`: `calla(p)` exige `p["guardia_pub"] is True and p["prod_pub"] is False`. En `vigilancia_sombra.pasadas_de_alerta` (docstring leído) `prod_pub` es «True o False si hay record a ±120 s, None si no miró». Una protegida con producción SIN record queda fuera de `candidatas`, `reversion` y `fuera_de_plazo`; el veredicto sólo mira `muy_bajo`, `sobrepublicacion`, `nulo.distintas` y `borde_del_encendido`. El contador de «pasadas que la guardia registra y producción no» (`borde_171_01`) está documentado como «sin disparar» y el workflow lo imprime sólo si ya se abrió un issue por otra causa.
- Medido con `v202_prod_sin_record.py` → `v202_salida.txt`, llamando a `disparadores` real con una protegida nocturna de Chillán de 2,18 MW, guardia que publica: A (control positivo, producción con record que calla) → REVERSION_CANDIDATA; B (producción sin record) → VERDE; C (ninguna pasada) → VERDE. Pregunta 1: sí lo vería, el control A cambia de veredicto. Pregunta 2: con instrumento muerto A y B darían igual; no es el caso.
- Por qué importa: la regla (borrador, §1) llama «peor caso» a «una señal débil o de borde de barrido que K publica y la vía no» y a la vía que «descarta en silencio los gránulos que no cubren el volcán» (hallazgo 171-01); ese descarte devuelve `None` desde `calcular_vrp_granulo` y no deja record, o sea `prod_pub` None. El diseño lo reconoce aparte («la regla no da cota y A115 prohíbe inventarla»), pero una cota por semana para una clase y cero para las protegidas son cosas distintas.
- Atenuante medido por lectura: `scripts/auto_audit_weekly.py` l. 1007-1016 y 1195 agrega «alerta protegida sin record nuestro» a `cobertura_avisos`, lo que vuelve el veredicto de la auditoría semanal DEGRADADO (l. 1213) y `audit-weekly.yml` abre issue; es semanal, no el mismo día. Ocurrencia real: SIN DATO (la guardia todavía no tiene datos; no se puede contar cuántas protegidas de borde hay).
- Cambio mínimo: en `disparadores`, tratar «protegida posterior al encendido, guardia publica, producción sin record pasadas N horas» como INVESTIGAR (no como reversión pre-autorizada). N no se inventa (A115): lo fija Nicolás, junto a las cotas. Alternativa si no se quiere tocar el código: dejar escrito en la regla que esa clase sólo la ve la auditoría semanal.

### MA172-203: CONFIRMADO EN PARTE, gravedad 2, no bloquea

- Parte confirmada: `scripts/vigilancia_sombra.py` l. 61 `MAX_DIAS_SOMBRA_SIN_DATOS = 3` y l. 379 `if dias > MAX_DIAS_SOMBRA_SIN_DATOS`. Medido con `v203_204_208_201via.py` (`v203_204_208_salida.txt`): una guardia con último dato hace 1 o 3 días da 0 avisos, hace 4 días 11 avisos (uno por volcán), y sin ningún record 11 avisos (control positivo). Y mientras la guardia calla, `guardia_pub` es None y no puede haber `REVERSION_CANDIDATA`: la vigilancia da VERDE. El rojo de `guardia-k-modis.yml` (paso «Revisar que salió K de MODIS») no abre issue; `vigilancia-guardia-modis.yml` corre por `workflow_run` completed (cualquier conclusión) pero no mira el rojo, sólo la frescura.
- Parte que no se sostiene: «deja la vigilancia en VERDE aunque haya una protegida que producción calla» sugiere una pérdida. La guardia corre a diario con una ventana de 8 días hacia atrás (`guardia-k-modis.yml`: `INI=$(date -u -d "7 days ago" ...)`), así que si revive dentro de ese plazo recupera las pasadas y la protegida se evalúa después. El costo es un retraso (hasta unos 4 días) en un disparador que la regla quiere «el mismo día», no una pérdida. La tolerancia de 3 días es heredada de la sombra de K (que corre una vez al día), no una decisión de este PR.
- Cambio mínimo: parámetro de tolerancia propio de la guardia (1 día; corre a diario) en `avisos_guardia`, y/o un paso `if: failure()` que abra «Guardia K de MODIS: la guardia falló» (hoy el único issue por falla es el del script de vigilancia).

### MA172-204: CONFIRMADO EN PARTE, gravedad 2, no bloquea

- Parte confirmada (mecanismo): `scripts/vigilancia_sombra.py` l. 395-406 mide la frescura de la referencia sobre TODAS las filas (`fechas = [... for f in filas ...]`), sin separar sensor. `v203_204_208_salida.txt`: con una referencia que sólo tiene VIIRS fresco → `[]` (sin aviso); control positivo con la referencia vieja → aviso. Como la vigilancia de MODIS sólo mira alertas MODIS, una referencia sin filas MODIS da cero pasadas y VERDE.
- Parte que no se sostiene como riesgo actual: `v204_huecos_modis.py` → `v204_salida.txt`, sobre `data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv` (sha256 ab1a208c... coincide con el del prompt; 2026-01-10 a 2026-10-26, 290 días con filas): desde el 2026-03-01 hay **0 días** con filas VIIRS y sin filas MODIS (mes a mes 0; racha máxima de días sin MODIS: 0). Consistente con A119 (MODIS completo y plano). El control positivo del script (quitar MODIS de los últimos 5 días) sí detecta 5. Es decir: el instrumento puede ver el hueco y en 8 meses no hay ninguno. Ventana y denominador: 245 días de marzo a octubre, canal CONS solamente (el canal OCR no aporta filas MODIS).
- Cambio mínimo: `avisos_referencia(filas, hoy, sensor="MODIS")` filtrando por sensor en la vigilancia de MODIS.

### MA172-206: CONFIRMADO EN PARTE (mecanismo CONFIRMADO; la magnitud de «~4,5 días» es SOSPECHA), gravedad 2, no bloquea

- `pipeline/store.py` l. 677-684 (leídas): si ya existe un record con la misma clave (datetime_utc, sensor), el nuevo hereda `first_processed_utc` del existente; l. 695-700: el reemplazo sin `overwrite` sólo ocurre si el existente es `nrt` y el nuevo `standard` (upgrade). `scripts/vigilancia_guardia_modis.py` `encendido_desde_datos` toma el mínimo de `first_processed_utc` entre los records con `via_codigo_mirova: true`.
- Medido con `v206_encendido_upgrade.py` → `v206_salida.txt` usando `store.append_record` real con `DATA_DIR` redirigido a mi carpeta: un record K (NRT) de una pasada anterior, luego el record de la vía NRT (no reemplaza), luego el de la vía estándar (upgrade): el record final es de la vía, tiene `first_processed_utc` 01:44:28 (el instante en que se escribió K) y `processed_utc` 01:44:34, y `encendido_desde_datos` devuelve 01:44:28, anterior a la primera escritura de la vía. Control: una pasada nueva posterior al «merge» da el instante de su propia escritura. Pregunta 1: sí lo vería. Pregunta 2: el control muestra que el valor cambia con los datos.
- Qué NO medí: cuánto adelanta en producción real. El «hasta ~4,5 días» depende de cuánto tarda NASA en publicar el estándar; `store.py` l. 692-693 dice «typically 3-5 days», de ahí la cota; no tengo un dato del NRT real (SIN DATO).
- Efecto: sólo corre hacia atrás el inicio de la cuenta de los 120 días y de las 29 protegidas y mueve a «posterior» pasadas de unos pocos días antes del merge cuyos records ya son de la vía; no cambia ningún disparo para pasadas con K en producción (producción=guardia=K en ellas).
- Cambio mínimo: usar `processed_utc` (que describe ESTA versión del record, según el comentario de `store.py` l. 669-676) en lugar de `first_processed_utc` en `encendido_desde_datos` (`vigilancia_guardia_modis.py`, l. 98), o exigir además que `datetime_utc` de la pasada sea posterior a su `first_processed_utc` de K.

### MA172-207: CONFIRMADO, gravedad 2, no bloquea (corregir antes de sellar la regla)

- `git show loop/activo:experiments/_s171_modd_adopcion/REGLA_REVERSION_MODD_BORRADOR.md` l. 93: «Cuenta desde el encendido (`CAMBIO_DETECTOR_MODIS_UTC`, la hora del merge al segundo)». `git grep CAMBIO_DETECTOR_MODIS` en c83882fcf (PR A) no da ninguna coincidencia y el grep sobre el worktree del PR B tampoco; la única constante de la familia es `CAMBIO_DETECTOR_UTC` de K (`frontend/cambio_detector.js` l. 29, vale 2026-10-18T09:57:30Z). La regla cuenta 1 aparición del nombre inexistente (`grep -c`).
- El código usa otra frontera por diseño: `vigilancia_guardia_modis.py` (docstring l. 33-36) y la decisión de diseño 3 («el encendido sale de los datos») la derivan del primer record de la vía. Además hay una tercera definición en el tablero y el audit («primera pasada MODIS de la vía con una de K antes»: `frontend/cambio_detector.js` l. 135-140 y `frontera_via_modis` en `auto_audit_weekly.py`). O sea: tres fronteras distintas (regla: hora del merge; vigilancia: primer `first_processed_utc`, ver 206; tablero/audit: primera observación de la vía); sólo la primera no existe.
- Cambio mínimo: reescribir la l. 93 del borrador para decir la frontera de los datos (y cuál de las dos) antes de sellarlo, ya que Nicolás pre-autoriza la reversión con ese texto.

### MA172-208: CONFIRMADO, gravedad 2, no bloquea

- `scripts/vigilancia_guardia_modis.py` `disparadores` (bloque «Nulo»): `pares`/`distintas` se calculan sobre la ventana de 14 días anterior al encendido (o a hoy); el veredicto depende sólo de `distintas`, no de `pares`. `v203_204_208_salida.txt`: sin guardia → `nulo: 0 pares, 0 distintas -> veredicto VERDE`. No hay aviso en `evaluar` para pares = 0 (`avisos` sólo agrega frescura, perfiles y vía).
- El control A110 («medir su nulo») queda entonces sin poder si el PR B entra antes de que la guardia acumule pares: el texto del PR B dice «dejar correr la guardia unos días para medir su nulo» (`PR_B_CUERPO.md` l. 89), pero eso es un paso humano, no un control. `tests/test_vigilancia_guardia_modis_s172.py` l. 160 incluso fija `["nulo"]["pares"] == 0` sin exigir aviso.
- Cambio mínimo: en `evaluar`, aviso «el nulo de la guardia no tiene pares» si `nulo["pares"] == 0` (o menos de un mínimo que fije Nicolás), que ya pasa a VIGILANCIA_CIEGA vía `avisos`.

### MA172-209: CONFIRMADO EN PARTE, gravedad 1 a 2, no bloquea

- Origen de la cifra (leído, otra auditoría: `D:/vrp-trabajo/temporales/audit_s171_dia3/INFORME.md`, sección 171-03): sombra `medir` en Láscar, 8 días, 13,3 min de paso (run 40945613044), contra NRT de Láscar con K de 10,7 y 11,9 min (otras corridas), de donde sale «1,1 a 1,25». La sombra corre las TRES vías (MODIS, VIIRS 375, VIIRS 750), NRT corre K, son corridas de días distintos y de un solo volcán. No aísla el costo de MODIS. Parte «dentro del ruido de K»: la dispersión entre dos corridas de K de Láscar es de 11 % (10,7 a 11,9) y la de hoy da 11,1 min (`v209_nrt_jobs_41353423746.json`), así que el extremo bajo del rango (1,12) no se distingue del ruido; el alto (1,24) sí queda por encima.
- Holgura medida hoy (run 41353423746, paso `Run VRP pipeline` del perfil mirova_equivalent, 11 jobs): máximo 20,0 min (PuyehueCordonCaulle), mínimo 11,1 min (Láscar); `timeout-minutes: 50` en `nrt.yml` l. 179. Un factor de 1,25 sobre el máximo da 25 min. El único dato cercano al tope es el histórico de 56 min de Villarrica del 2026-09-02 citado en el comentario de `nrt.yml`/`guardia-k-modis.yml` (no lo re-medí).
- Costo mínimo propio de la parte de la vía que agrega cómputo (`remuestrear_grilla`, 2 bandas, ~6.300 puntos): 0,85 s por gránulo en este computador (`v209_costo_via_local.py` → `v209_costo_via_local_salida.txt`), cota inferior (no incluye leer MxD03 ni `procesar_grilla`; MODIS real no corre en Windows). Con unas decenas de gránulos por job el aumento es del orden de un minuto, no de 10 a 25 %.
- Lo que no puedo decir: el costo real de MODIS con la vía en el runner (SIN DATO). «VR172-04 confirmado»: no sé qué es VR172-04 (no abrí informes de los frentes); lo dicho aquí es independiente.
- Cambio mínimo: reescribir el pre-mortem (c) de la regla para decir que 1,1 a 1,25 es una medición de la sombra con tres vías en Láscar y que la holgura del NRT hoy es de 2,5 veces (20 de 50 min), y vigilar el paso `Run VRP pipeline` tras el encendido.

## Hallazgos nuevos (VMA172-201 en adelante)

### VMA172-201
- TÍTULO: `backfill-tier-a.yml` corre el perfil de producción sin instalar pyproj: tras el PR B un backfill de Tier A no escribe MODIS
- ARCHIVO:LÍNEA: `.github/workflows/backfill-tier-a.yml:73,90`
- QUÉ PASA: lo mismo que MA172-201, en otro workflow que corre `--profile mirova_equivalent` (l. 90) y sólo instala `pyhdf earthaccess numpy h5py scipy pyyaml` (l. 73). Un backfill de huecos de MODIS escribiría VIIRS y ningún MODIS, sin error.
- CÓMO SE VE EN EL DASHBOARD: invisible (el hueco de MODIS que se quería llenar sigue ahí).
- CÓMO REPRODUCIRLO: `grep -n "pyproj\|profile" .github/workflows/backfill-tier-a.yml` en el worktree del PR B; el mecanismo es el de `v201_sin_pyproj.py`.
- CONFIANZA: CONFIRMADO por lectura (mismo mecanismo ya reproducido; no despaché el workflow).
- GRAVEDAD: 3 (acción manual, acotada; pero se usa justo para reparar huecos).

### VMA172-202
- TÍTULO: cualquier excepción de la vía de MODIS mata el gránulo sin respaldo a K, aunque el comentario diga que cuando la vía «no puede correr» sigue K
- ARCHIVO:LÍNEA: `pipeline/process_modis.py:637-652`; `scripts/run_pipeline.py:279-280`; `pipeline/mirova_v750_codigo.py:204` (`griddata`)
- QUÉ PASA: el bloque de la vía sólo cae a K por las marcas `sin_grilla`, `sin_mxd03` y `geo_distinta`; una excepción (pyproj ausente, MIR casi todo NaN, `griddata` sin puntos suficientes) sale por el `except Exception` de `run_pipeline`, que imprime `ERROR processing` y no escribe nada.
- CÓMO SE VE EN EL DASHBOARD: invisible (falta la pasada; en el log, una línea `ERROR processing`).
- CÓMO REPRODUCIRLO: `python -I D:/vrp-trabajo/temporales/s172_miniaud/v2/v210_excepcion_sin_fallback.py`: control (gránulo normal) → record; MIR todo NaN → `ValueError No points given`; MIR con 2 píxeles válidos → `QhullError`. Salida en `v210_salida.txt`.
- CONFIANZA: CONFIRMADO (script). Que esos casos ocurran en datos reales: SIN DATO.
- GRAVEDAD: 2. Es una decisión de diseño a tomar (caer a K ocultaría el fallo de pyproj, que hoy sale por «la vía no está escribiendo»), no un error evidente.

### VMA172-203
- TÍTULO: el stale-gate del NRT y el healthcheck miran el último record de cualquier sensor: una caída sólo de MODIS no los dispara
- ARCHIVO:LÍNEA: `.github/workflows/nrt.yml` (paso «Assert Tier A records fresh (A57)», `last = records[-1]...`); `.github/workflows/nrt-healthcheck.yml:73`
- QUÉ PASA: ambos toman `records[-1]["datetime_utc"]` de cada volcán; con VIIRS escribiendo, MODIS puede estar muerto semanas sin que ninguno avise. Es el motivo por el que MA172-201 depende por completo de la vigilancia nueva de PR A.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: leer las dos citas; ninguna filtra por sensor.
- CONFIANZA: CONFIRMADO (lectura). Contexto, no un defecto del PR.
- GRAVEDAD: 2.

## SEGUIMIENTOS (fuera de mi eje)

- `tests/test_vigilancia_guardia_modis_s172.py` l. 160 fija `nulo.pares == 0` en el caso sin guardia sin exigir aviso (relacionado con MA172-208). Confianza: CONFIRMADO. Gravedad 1.
- El comentario de `pipeline/process_modis.py` (cabecera FICHA, PR B) dice que la vía «cae a K» cuando no puede correr y que el record lo dice; esa promesa sólo cubre las tres marcas, no excepciones (ver VMA172-202). Gravedad 1.
- `backfill-tier-a.yml` y `reproc-chunked.yml` corren o pueden correr `mirova_equivalent`; sólo revisé el primero (el segundo recibe el perfil por parámetro y rehúsa el perfil de producción en l. 90 del script embebido). Confianza: SOSPECHA para otros reprocesos manuales.

## VERIFICADO LIMPIO

- El PR B no toca `nrt.yml` ni `requirements.txt` y `origin/main` 14fb62030 tampoco: `git diff --stat da67fa417 b42823194` lista 21 archivos, ninguno de esos dos (comando corrido). La vara era el diff entre refs, no un doc.
- `git rev-parse b42823194:<archivo>` y `c83882fcf:<archivo>` coinciden para `scripts/vigilancia_guardia_modis.py`, `scripts/vigilancia_sombra.py`, `.github/workflows/vigilancia-guardia-modis.yml` y `pipeline/store.py`: lo que verifiqué del PR A en el worktree del PR B es lo mismo que en la punta del PR A.
- El comentario «los 11 Tier A tienen grilla MODIS» (relevante para la extensión del fallo): comprobado con `volcan_por_coordenadas` + `grilla_del_volcan` (`v201b_salida.txt`).
- La holgura de tiempo del NRT: 11,1 a 20,0 min de 50 por job en el run 41353423746 (2026-11-01), contra el tope de `nrt.yml` l. 179.

## SIN DATO

- Cuánto tarda de verdad la vía MODIS en el runner: nada se despachó; sólo cota inferior local de la interpolación.
- Cuántas protegidas de borde de barrido (producción sin record) habrá: la guardia aún no tiene datos.
- La magnitud real del adelanto de la frontera del ítem 206 en producción (depende de la latencia del estándar de NASA).
- Qué es VR172-04 (mencionado en el ítem 209).

## FUERA DE ALCANCE

- Reversión limpia del PR B, suite completa, re-sellado del lector de V375-E, contenido científico de la vía (D34, MOD-D).

## Archivos de esta verificación (todos en CARPETA)

`caminos.md`, `INFORME.md`, `hallazgos.csv`, `veredictos.csv`, `v201_sin_pyproj.py`/`v201_salida.txt`, `v201b_grillas.py`/`v201b_salida.txt`, `v202_prod_sin_record.py`/`v202_salida.txt`, `v203_204_208_201via.py`/`v203_204_208_salida.txt`, `v204_huecos_modis.py`/`v204_salida.txt`, `v206_encendido_upgrade.py`/`v206_salida.txt`, `v209_costo_via_local.py`/`v209_costo_via_local_salida.txt`, `v209_nrt_jobs_41353423746.json`, `v210_excepcion_sin_fallback.py`/`v210_salida.txt`, `nrt_log_lascar_41353423746.txt` (log del runner, 100 KB; el token no aparece en él, pero es log de GitHub Actions, no lo publiques sin revisarlo).
