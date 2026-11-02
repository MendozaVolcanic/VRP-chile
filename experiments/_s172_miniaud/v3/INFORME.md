# Informe del verificador v3 (S172, mini-auditoria del encendido de MODIS)

## Encabezado

- Hora del servidor al informar: Mon, 02 Nov 2026 01:45:09 GMT (header Date de `gh api -i repos/MendozaVolcanic/VRP-chile`; `date -u` 01:45:10 UTC).
- Commit medido: worktree D:/vrp-trabajo/worktrees/s172-miniaud-b en b4282319446cfea944aa1a4621c0fec7da8649a0 (PR B). Base: d3cd0b2ae (copia `f3/base_tree`, comprobada contra `git show d3cd0b2ae` normalizando CRLF: mismo sha256 en `profile.py` y `mirova_equivalent.yaml`). PR A (c83882fcf) = da67fa417 + dos archivos de informe (`git diff --stat da67fa417 c83882fcf`): todo el codigo de PR A esta en el arbol de PR B, y `git merge-base --is-ancestor c83882fcf HEAD` da "no", como decia el dato de git.
- Modelo: Sonnet 5.5 (claude-sonnet-5-5). Esfuerzo pedido: alto. Esfuerzo con que realmente corri: el arnes me fijo un esfuerzo de razonamiento bajo, asi que declaro bajo.
- CARPETA: D:/vrp-trabajo/temporales/s172_miniaud/v3 (instrumentos y salidas en `m1/`).
- caminos.md escrito antes de abrir ningun archivo citado: sha256 del contenido anterior a la nota final `ca5b99dec8ebc67c2c1a5dc80d029880d728c9d9b01d9271b20fe9420d0be8ce`; sha256 del archivo con la nota anexa (el que queda en disco) `f107fb7ff6d5fbd46669d1e4f8ff78144e07d609919c5429a1224bfc9db3c5b0`. Hora anotada en el: 01:36:07 UTC.
- Efecto lateral a declarar: las importaciones de mis scripts pudieron crear `__pycache__` ignorado por git en `pipeline/` y `scripts/` del worktree compartido (`git status --short` limpio; solo aparecen como ignorados). No toque ningun archivo versionado. No pude saber si el bytecode lo creo yo u otro auditor.
- Llamadas a la API de GitHub: 7 GET (`gh api`), de lectura. Ningun workflow despachado, ninguna credencial usada, ningun commit.
- NO mire: la suite completa de pruebas ni las pruebas de PR A/B (no corri pytest); `diario.html` y `mosaico.html` (solo `cambio_detector.js`); el contenido de data/ de produccion salvo una comparacion que resulto invalida (ver MA172-307); los INFORME.md y hallazgos.csv de los auditores (no los abri, como pide la tarea).

## En una pantalla

1. Los 7 items de la lista se sostienen en lo esencial: 4 CONFIRMADO (MA172-303, MA172-304, MA172-205, DATO-COORD), 3 CONFIRMADO EN PARTE (MA172-305, MA172-211/307 fundidos); ninguno REFUTADO.
2. Hallazgo nuevo de gravedad 5, bloquea PR B: nrt.yml no instala pyproj (comprobado en el log real del NRT del 2026-11-01 y en la metadata de PyPI), y la via de MODIS lo importa en cada granulo. Con el flag encendido, 11 de 11 volcanes lanzan ModuleNotFoundError y `run_pipeline.py` lo atrapa: el NRT de produccion deja de escribir MODIS en silencio, sin caida a K (VMA172-301).
3. MA172-303 es real (55 derivados, 46 de ellos con MODIS efectivo) pero de gravedad 2; MA172-304, MA172-205 y MA172-305 solo actuan despues de un revert o son de calidad de comentario; ninguno bloquea PR A ni PR B.
4. Bloquea PR A: nada de lo verificado. Bloquea PR B: VMA172-301.

## Hallazgos nuevos

### VMA172-301
- TÍTULO: PR B enciende la via de MODIS en produccion, pero nrt.yml (y backfill-tier-a.yml, reproc-chunked.yml) no instalan pyproj: cada granulo MODIS de los 11 volcanes falla en silencio.
- ARCHIVO:LÍNEA: `.github/workflows/nrt.yml:140-143` (`pip install earthaccess numpy h5py scipy pyyaml`, sin pyproj); `.github/workflows/backfill-tier-a.yml:73`; `pipeline/mirova_v750_codigo.py:204,227,237,245,306` (`from pyproj import Transformer` dentro de `remuestrear_grilla`, `celda_de`, `posicion_de`, `latlon_de`); `scripts/run_pipeline.py:279-280` (`except Exception as e: print(f"  ERROR processing ...")`). SCRIPT:SALIDA `m1/nrt_sin_pyproj.py` : `m1/nrt_sin_pyproj.out`.
- QUÉ PASA: la via de MODIS pasa cada granulo a la grilla UTM de MIROVA con pyproj, y el runner del NRT es un Python limpio al que solo se le instalan `earthaccess numpy h5py scipy pyyaml pyhdf`. Con `enable_modis_codigo_mirova: true` en `mirova_equivalent` (PR B), cada granulo MODIS de un volcan con grilla entra a `_MV.calcular_vrp_granulo` (`pipeline/process_modis.py:637-657`), que llama `remuestrear_grilla` sin `try/except`; la excepcion sube a `run_pipeline.py`, que imprime "ERROR processing" y sigue. No hay caida a K: el record simplemente no se escribe. La sombra ya lo sabe (`sombra-codigo-mirova.yml:90`: "el NRT no lo instala") y por eso instala pyproj y tiene un paso de revision; el NRT no tiene ese paso.
- CÓMO SE VE EN EL DASHBOARD: la serie de MODIS de los 11 Tier A deja de recibir puntos nuevos desde el primer NRT tras el merge (VIIRS sigue). Con el workflow en verde. El respaldo es `avisos_via` de la vigilancia de la guardia ("el flag ... esta encendido y no hay ningun record MODIS de la via"), que da VIGILANCIA_CIEGA en la corrida diaria siguiente: deteccion tardia de horas, no inmediata. Y como la guardia (K) si escribe, guardia contra produccion no dispara la reversion (produccion queda en `prod_pub` None, que `calla()` excluye).
- CÓMO REPRODUCIRLO: `python D:/vrp-trabajo/temporales/s172_miniaud/v3/m1/nrt_sin_pyproj.py` (granulo sintetico alrededor de cada volcan con `radius_km` 25; `calcular_vrp_granulo` real). Salida: `[normal]` 11/11 RECORD; `[bloquear]` (pyproj ausente) 11/11 EXCEPCION ModuleNotFoundError. Control: el modo normal prueba que el instrumento distingue. Sobre el entorno real: el log del NRT del 2026-11-01 21:43-21:44 UTC (copia en `f3/m6_nrt_job_log.txt` l. 451, solo leida) lista lo instalado y no incluye pyproj; `m1/pypi_requires.out` muestra que ni earthaccess 0.17.0, h5py 3.16.0, scipy 1.17.1, pyhdf 0.11.7, numpy ni pyyaml requieren pyproj (control positivo: geopandas 1.0.1 si). Una tercera comprobacion es la lectura de `nrt.yml` l. 140-143 en PR B.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 5. Corta la produccion MODIS del NRT sin error visible. Puede que otro auditor de f3 lo haya reportado como MA172-301 o 302 (no estan en mi lista); lo reporto igual como medido por mi.
- Bloquea PR B (no PR A). Cambio minimo, sin aplicarlo: agregar `pyproj` a los `pip install` de `nrt.yml` (l. 143) y de los otros workflows que corren `--profile mirova_equivalent` o un perfil libre (`backfill-tier-a.yml`, `reproc-chunked.yml`), y de preferencia un paso de revision como el de la sombra.

### VMA172-302 (= DATO-COORD, ver su veredicto)
- TÍTULO: el cargador resuelve un solo nivel de `extends`.
- ARCHIVO:LÍNEA: `pipeline/profile.py:49-66`. SCRIPT:SALIDA `m1/synth/prueba.py` : `m1/synth/salida.txt`.
- QUÉ PASA: ver veredicto DATO-COORD. CONFIANZA: CONFIRMADO. GRAVEDAD: 1. No cambia ningun censo.

## Veredictos por afirmacion

Cada uno tambien en `veredictos.csv`.

### MA172-303: CONFIRMADO (gravedad verificador 2)
- Instrumento: `m1/censo.py` carga `pipeline/profile.py` real de cada arbol en un subproceso `python -I` con `VRP_PROFILE=<perfil>` (regla A89, no el YAML). Pregunta 1: si el cargador no propagara el flag el censo lo veria (mirova_equivalent cambia). Pregunta 2: control positivo mirova_equivalent 0 a 1; errores de carga explicitos por fila (0). Denominador: 101 perfiles en PR B, 100 en la base; ventana: estado de los arboles a las 01:3x UTC del 2026-11-02.
- Resultado (`m1/censo.out`): 60 perfiles con `extends`, todos hacia mirova_equivalent; 56 pasan de False a True = mirova_equivalent + 55 derivados con la clave sin escribir. De los 55, 46 tienen `SENSOR_MODIS` efectivo True; 10 lo tienen False (A/B de VIIRS: el flag cambia pero MODIS no corre en ellos). Cuatro derivados siguen en False: experimental, experimental_ndc_focus, _s146_ab_control, guardia_k_modis. `sombra_codigo_mirova` ya era True en la base.
- Workflows (`m1/workflows_perfiles.out`, 52 workflows vivos): 8 nombran a 20 de los 55 (probe-s157-busqueda-ventana, reproc-s120-eq16-villarrica, reproc-s124-villarrica-op-ab, reproc-s135-ab-d1d2, reproc-s143-ab-d22d25, reproc-s146-ab-sin-test1, reproc-s151-ab-caja, reproc-s151-ab-diurno); ninguno instala pyproj; los otros 35 solo se despachan por `reproc-chunked.yml` o a mano, y `reproc-chunked.yml` tampoco instala pyproj. "No instalan pyproj" CONFIRMADO. El grep es por nombre de perfil como palabra; un workflow que construya el nombre dinamicamente no se veria (limite).
- Efecto: despachar uno de esos A/B ahora produce el mismo fallo silencioso de VMA172-301 en vez del K que el A/B supone. Son perfiles de experimento; no tocan produccion.
- Bloquea: PR A no. PR B no por si solo (el bloqueo es VMA172-301), pero se resuelve en la misma edicion. Cambio minimo: pyproj en los pip install de los workflows de despacho genericos y de los 8 A/B, o fijar `enable_modis_codigo_mirova: false` en los derivados que aun se despachan.

### MA172-304: CONFIRMADO (gravedad verificador 2)
- Instrumento: `m1/audit_revert.py` y `m1/audit_revert2.py` llaman las funciones reales de `scripts/auto_audit_weekly.py` (arbol de PR B): `frontera_via_modis`, `nuestros_por_noche`, `evaluar_detector`, `evaluacion_vigente`, `flags_de_evaluacion`. Escena sintetica Lascar/MODIS_TERRA: K 1-4 nov (solo en la segunda), via 5-9, K 10-14, MIROVA alerta las 10 noches. Pregunta 1: un audit que tratara bien la reversion evaluaria las 10 noches. Pregunta 2: el control sin via nunca (escenario C/E) da 10 (o 5) noches vistas, 0 fuera, de modo que el instrumento puede dar bien.
- Resultado (`m1/audit_revert.out`): revertido: `fuera_de_detector={'K en noche VIA_MODIS': 5}`, recall del detector K n_noches 0 (None), VIA_MODIS n_noches 5 con noches_sin_datos 5, flags []. (`m1/audit_revert2.out`): ventana solo K con la via aun en el historico: noches vistas 0, recall None en los dos detectores, flags []. Control: sin via, `fuera={}` y recall 100 % sobre las 5 o 10 noches.
- Matiz que rebaja la letra del titulo: no es silencio absoluto. El conteo se publica en `fuera_de_detector` (l. 1254) y el docstring de `_detector` (l. 443-447) anticipa el caso; pero los unicos avisos de `avisos_detector` (l. 1138-1146) son los de "K en noche C0", y ningun flag recoge "K en noche VIA_MODIS". Tras una reversion, el recall y la magnitud de MODIS dejan de evaluarse sin que el veredicto lo diga, y la frontera de la via queda en la primera fecha de la via para siempre (`frontera_via_modis`, l. 471, mira todo el historico cargado).
- Bloquea: ninguno; solo actua tras un revert. Cambio minimo: agregar un aviso a `avisos_detector` cuando `fuera_de_detector.get("K en noche VIA_MODIS")` sea > 0, y un paso en la regla de reversion para dar fecha de fin a la via.

### MA172-305: CONFIRMADO EN PARTE (gravedad verificador 1)
- Instrumento: `gh api repos/.../actions/workflows/<wf>/runs?event=schedule`, `run.created_at` contra la hora nominal del yml (`m1/cron/*.tsv`, `m1/cron/retraso.out`, `m1/cron/retraso_fuera_de_hora.out`). Pregunta 1: si los cron llegaran a tiempo el retraso seria de minutos (control: sync-mirova-csv `:12`, mediana 28 min y maximo 59 con n=30, y nrt.yml, mediana 0,93 h modulo 2 h, n=30, no son 0). Pregunta 2: n declarado en cada linea.
- Resultados con ventana y n: sombra 15:00 nominal, n=3 (2026-10-30 a 11-01), 4,16 a 4,87 h; experimental-diario 14:00, n=23 (10-10 a 11-01), 2,80 a 7,95 h; nrt-healthcheck 12:00, n=30 (10-03 a 11-01), 2,58 a 8,54 h; vigilancia-sombra 23:40, n=13 (10-20 a 11-01), 1,90 a 3,23 h.
- Lo confirmado: la separacion que el comentario HORA de `guardia-k-modis.yml` (l. 15-18) describe no existe, y los cron diarios llegan horas tarde. Lo que ajusto: los 4 a 5,7 h son de cron en punto; el unico comparable de hora no redonda (vigilancia-sombra, :40) da 2 a 3 h, de modo que la guardia arrancaria hacia las 19:40-21:00 UTC, aun dentro de la ventana de la sombra (que arranca ~19:00-20:00 con hasta 100 min). La guardia nunca corrio: es extrapolacion de otros workflows, y la sombra tiene n=3.
- Por que gravedad 1: la guardia tiene grupo de concurrencia propio, `max-parallel: 4` como la sombra y push con reintentos; la vigilancia corre por `workflow_run` (`vigilancia-guardia-modis.yml` l. 13-17), asi que el aviso del mismo dia no depende del cron de 22:45 (solo respaldo). Lo que se arriesga es contencion por LANCE y minutos de runner.
- Bloquea: ninguno. Cambio minimo: corregir el comentario HORA para no prometer separacion.

### MA172-205: CONFIRMADO (gravedad verificador 2)
- Instrumento: `m1/marca_revert.js`, `node`, con `primeraViaModis` y `textoAvisoModis` reales de `frontend/cambio_detector.js`. Pregunta 1: si la marca reaccionara a la reversion, la fecha o el texto cambiarian entre A (sin revertir) y B (revertido). Pregunta 2: control C (solo K) da null; A da fecha.
- Resultado (`m1/marca_revert.out`): A y B devuelven la misma fecha `2026-11-05T03:10:00.000Z`; el texto de B sigue con "Desde el 5 nov 2026 la serie de MODIS viene de la via ..." (presente), sin mencion de vuelta a K. `CambioDetector` no expone ninguna fecha de fin de la via. La regla de reversion (borrador, `git show loop/activo:experiments/_s171_modd_adopcion/REGLA_REVERSION_MODD_BORRADOR.md`, copia en `m1/regla_reversion.md`) solo trata el alta de la marca (l. 128-129), no la baja.
- Efecto: tras revertir, el escalon de vuelta de la magnitud de MODIS (el caso Chillan que la marca existe para explicar) queda sin marca y el aviso afirma lo contrario. Gravedad 2: es una anotacion de lectura de tendencia, no un dato ni una alerta.
- Bloquea: ninguno. Cambio minimo: una segunda constante (fin de la via) o detectar en `primeraViaModis` un K posterior a la via para escribir "hasta el X".

### MA172-211 y MA172-307: FUNDIDOS; CONFIRMADO EN PARTE (gravedad verificador 1)
- Son el mismo defecto: ambos en `scripts/vigilancia_guardia_modis.py`, l. 236-246 contenidas en 232-247 (la parte del workflow l. 117-118 solo fija la ventana de 8 dias, igual al NRT).
- Instrumento: `m1/nulo_sintetico.py` llama `vg.disparadores` real con 200 pares guardia/produccion pre-encendido. Pregunta 1: un nulo con tolerancia no dispararia con 1 par distinto. Pregunta 2: el caso 0 distintos da VERDE y el caso 1 distinto da INVESTIGAR (el instrumento puede dar los dos). Resultado (`m1/nulo_sintetico.out`): 0 distintos: VERDE, nulo.pares 112, distintas 0; 1 distinto: INVESTIGAR, distintas 1. Denominador: 112 pares dentro de los 14 dias (`DIAS_NULO`) previos al encendido.
- CONFIRMADO: el nulo no tiene tolerancia (las otras dos reglas tienen cota 2 y 3, l. 68-69) y el script no lee `product_version` (el campo existe: `pipeline/store.py:696-697`, auto-upgrade nrt a standard). CONFIRMADO tambien: la consecuencia es solo un issue "Guardia K de MODIS: investigar", deduplicado por prefijo, no una reversion.
- SIN DATO: que la diferencia de version de producto (NRT en uno, estandar en otro) produzca de verdad un par distinto. Mi intento (`m1/nulo_version.py`: data/experimental contra data/mirova_equivalent, MODIS, ventana comun 2026-04-17 a 04-24, 5553 pares) no sirve como nulo: los dos conjuntos son de estados de codigo distintos (199 pares con publicacion distinta y 0 con version distinta) y usa un proxy de "publica" (`primary_cluster.vrp_mw > 0`), no el predicado del tablero. No lo cuento como evidencia en ningun sentido.
- Bloquea: ninguno. Cambio minimo: darle al nulo una cota como a las otras dos, o excluir los pares con `product_version` distinto (para lo segundo hay que cargar el campo en `cargar_nuestros`).

### DATO-COORD: CONFIRMADO (gravedad verificador 1)
- `pipeline/profile.py:49-66` (PR B): `parent_cfg = yaml.safe_load(fp)` del padre, sin repetir la resolucion del `extends` del padre. Prueba (`m1/synth/`, copia del cargador, no toca el repo): `zz_nivel1` extends mirova_equivalent, `zz_nivel2` extends zz_nivel1. Salida `m1/synth/salida.txt`: mirova_equivalent VIA=True; zz_nivel1 VIA=False ANOMALY=99.0 (hereda); zz_nivel2 `ERROR KeyError 'tir_threshold_k'` (falla ruidosa, no herencia silenciosa).
- Censo (`m1/censo.out`): 60 perfiles con `extends`; destinos: solo `mirova_equivalent`. No hay ningun perfil de dos niveles, asi que el censo de MA172-303 no cambia. Bloquea: ninguno. Cambio minimo: ninguno requerido.

## SEGUIMIENTOS (fuera de mi eje)

- `nrt.yml` linea 236 corre `--profile experimental` en el mismo job que produccion; `experimental` queda fijado en `false` por PR B, asi que no hereda VMA172-301, pero conviene comprobar que ese paso siga siendo K. Confianza SOSPECHA.
- Ningun workflow de produccion (`nrt.yml`) tiene el paso de revision que si tienen sombra y guardia (`revisar_sombra.py`, `revisar_guardia_modis.py`) para detectar "run_pipeline atrapo toda excepcion y salio 0". Es la causa de que VMA172-301 sea silencioso. CONFIRMADO por lectura (comentario de `sombra-codigo-mirova.yml` l. 149-151); no medi un NRT sin ese paso.

## VERIFICADO LIMPIO

- Herencia: `pipeline.profile` real, control positivo en la base (mirova_equivalent False en base, True en PR B); 0 errores de carga en 101 perfiles. `guardia_k_modis` queda en False en PR B (`m1/censo.out`), tal como su `data_subdir` y su assert del workflow (l. 111 de `guardia-k-modis.yml`). Vara: `pipeline.profile`, no el YAML.
- El log real del NRT del 2026-11-01 coincide con la lectura de `nrt.yml`: dos fuentes independientes sobre el entorno de ejecucion.

## SIN DATO

- Si NRT contra estandar produce de verdad pares distintos en el nulo de la guardia (MA172-307): no hay corrida de la guardia (nunca corrio) ni un nulo valido en data/.
- Comportamiento real de la guardia en GitHub Actions (hora de arranque, solape): nunca corrio; solo hay extrapolacion.
- Si existe un workflow que construya nombres de perfil dinamicamente y escape al grep de `m1/workflows_perfiles.py`.

## FUERA DE ALCANCE

- Correr las pruebas de PR A/B o la suite completa (la hizo el auditor del frente 2).
- Mejorar el instrumento de otros o corregir citas viejas.
