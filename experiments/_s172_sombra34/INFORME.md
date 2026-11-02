# Sombra de los 34 volcanes fuera del NRT, con las tres vías «código MIROVA» (S172)

Rama `claude/s172-sombra-34`, worktree `D:\vrp-trabajo\worktrees\s172-sombra34`, sobre main `14fb62030` (tag
defensivo `pre-s172-sombra-34`). Decisión de Nicolás del 2026-11-02 en el chat de la coordinadora: «si está corriendo
un código que funciona bien en 11 volcanes esperamos que sea similar para los otros 34, continúa con todo». El plan
(`docs/superpowers/plans/2026-11-02-nrt-34-volcanes.md`, rama `loop/activo`) dejaba las grillas para diciembre; esto
las adelanta. No abrí PR, no mergeé, no creé tags ni despaché nada.

## Qué es y por qué

MIROVA vigila en su NRT sólo los 11 chilenos (plan, H2), así que para los otros 34 no hay referencia. Antes de
llevarlos al tablero hay que ver cómo se comporta en ellos, con pasadas reales, el mismo detector que corre la sombra
de los 11. La sombra escribe en `data/sombra_34/`, que no lee el tablero ni el lector sellado de V375-E; no toca
producción ni los 11.

## Las piezas (un commit cada una)

| # | commit | qué |
|---|---|---|
| 1 | `8ec3ff01f` | grillas de los 34 en `pipeline/grillas_mirova.yaml` y el script que las genera |
| 2 | `1864cf62e` | perfil `pipeline/profiles/sombra_34.yaml` |
| 3 | `7e1a26936` | workflow `.github/workflows/sombra-34.yml` |
| 4 | `0d4320e2f` | aviso de vigilancia ciega: `scripts/vigilar_sombra_34.py` y `.github/workflows/vigilancia-sombra-34.yml` |
| 5 | `7de231b17` | pruebas `tests/test_sombra_34_s172.py` |
| 6 | (este) | informe y lista de vecinos dentro de la grilla |

### 1. Grillas

`experiments/_s172_sombra34/generar_grillas_34.py` (salida en `generar_grillas_34_salida.txt`):

- **La lista sale de `volcanoes.yaml`**: los activos sin grilla. Son 34 (el script se detiene si no), y coinciden con
  `volcanoes.yaml` menos la matriz de `nrt.yml` (prueba).
- **La regla**: (X0, Y0) = UTM del lat/lon del yaml, zona estándar por longitud (13 en EPSG 32718, al oeste de 72° O;
  21 en 32719), X0 e Y0 a 0,1 m, `centro_lat/lon` = el lat/lon del yaml a 5 decimales, `roi_v750: def`.
- **Por qué esta regla y no otra**: en 8 de los 11 el punto de MIROVA es el lat/lon del yaml (control impreso: dx 0,0 m,
  dy 0,9 a 1,0 m, redondeo del TIF). En Láscar, Planchón-Peteroa y Tupungatito MIROVA usa otro punto, de coordenadas
  redondas, a 233, 1.885 y 2.787 m del yaml; esos tres salieron de un TIF de MIROVA que los 34 no tienen, y no hay regla
  que los produzca (tampoco son el `mirova_center` del KML, que también difiere). Para los 34 se usa la regla de la
  mayoría; si MIROVA llegara a publicar un TIF de alguno, su punto real reemplaza a éste (A5).
- **Dos diferencias menores con los 11, a la vista**: (a) en los 8 el Y0 del archivo está 0,9 a 1,0 m al sur del UTM
  del yaml y en los 34 no (sub-métrico contra celdas de 375 m o más; no se copió el desfase porque no sé de dónde sale);
  (b) en los 11 `centro_lat/lon` es el centro en grados del TIF, a ~60 m del yaml, y en los 34 es el yaml. Ese centro
  sólo sirve para el recorte de 45 km y el corte de 5 km de MODIS y VIIRS 375: 60 m no cambian ninguno de los dos.
- **Ni un byte de las 11**: el script sólo agrega al final (se niega si alguno ya está). `diff_grilla.txt`: un solo
  bloque `@@ -40,0 +41,38 @@`, 0 líneas borradas, y los primeros 3.805 bytes del archivo nuevo (main entero) tienen el
  mismo sha256 que main (`da755f3e...`). No toqué la cabecera: las 34 llevan su propio bloque de comentario antes de
  la primera entrada nueva.

### 2. Perfil `sombra_34`

`extends: mirova_equivalent` directo, porque `extends` resuelve un solo nivel (comprobado en `pipeline/profile.py`,
`_load_profile`: la clave `extends` del padre no se resuelve). Repite los flags de la sombra de los 11: las tres vías
encendidas, los tres de MxD03 apagados, los tres sensores, los tres flags de K con su valor de producción, y
`data_subdir: sombra_34`. La prueba compara **todas** las constantes resueltas desde `pipeline.profile` contra
`sombra_codigo_mirova`: sólo difieren `PROFILE_NAME` y `DATA_SUBDIR`.

**Sin `volcano_overrides`, a propósito** (el plan los proponía con radio 25 e inner 5, decisiones D4 y D5): las vías no
usan `radius_km` ni `inner_radius_km` para detectar; interpolan a la grilla de 51 × 51 km y usan su caja fija. El
inner sólo pone la etiqueta `summit`/`far`. Sin inner en el yaml, el record de la vía sale con `distance_class: null` y
guarda `primary_cluster.centroid_dist_km`, que permite clasificar después con el inner que Nicolás decida (D5; no hay
valor de MIROVA que copiar). Lo único que usa el radio de 5 km es K cuando la vía no puede correr (MODIS sin MxD03).

### 3. Workflow `sombra-34.yml`

Calcado de `sombra-codigo-mirova.yml`: matriz de los 34 escrita a mano (amarrada a `volcanoes.yaml` menos `nrt.yml`
por prueba), `--volcano` explícito (run_pipeline lo respeta aunque no sea `mirova_monitored`), grupo propio
`sombra-34`, `max-parallel: 8`, sólo `EARTHDATA_TOKEN` con corte si viene vacío antes del pipeline (A71), `"on":` entre
comillas (A43), push con 5 reintentos `pull --rebase` (G4) y sólo de `data/sombra_34/<volcán>.json`, aserción del
perfil desde `pipeline.profile` (nombre, carpeta, vías, MxD03, sensores), revisión por job con
`scripts/revisar_sombra.py` (genérico: recibe la ruta del JSON; no lo toqué), log tachado y subido como artefacto.
Ventana: `scripts/ventana_sombra.py` sin cambios (hoy y 7 días atrás, nada antes del 2026-11-03; antes de esa fecha
cada job sale en segundos). Tiene `workflow_dispatch` (con `volcano`, `medir`, `start`, `end`) y **schedule**:
encenderlo es el merge, que decide Nicolás.

**Cadencia: `7 13 * * *` (13:07 UTC).** Del informe de capacidad (`experiments/_s172_capacidad_nrt/INFORME.md`,
`loop/activo`, §1 y §5 punto 3): 34 jobs con `max-parallel: 8` dan 74 a 81 min de pared de mediana (p95 79 a 87;
ESTIMACIÓN, los 34 nunca corrieron con las vías). El NRT de los 11 recibe despachos a las :10 de las 01 a las 12 UTC
(pared máxima observada 40 min, termina antes de las 12:50); la sombra de los 11 tiene cron a las 15:00 y la
experimental a las 14:00, y las dos llegan con horas de atraso (~17 a 20 UTC). A las 13:07 la corrida termina hacia
las 14:30 si GitHub la dispara a tiempo y no se cruza con el NRT; si llega con horas de atraso, se cruza a lo sumo con
la experimental y la sombra de los 11 (8 + 4 + 4 = 16 jobs, bajo el tope de 20 simultáneos del plan Free, que es SIN
DATO). El minuto 7 evita la punta de carga del minuto 0.

**Costo de runner**: ~34 jobs de 15 a 17 min (estimación del informe de capacidad para los 34 bajo
`mirova_equivalent`; la vía de MODIS podría subirlo 6 a 25 %), unos **550 a 600 min de runner por día**; repo
público, sin tope propio de minutos. El costo dominante es bajar gránulos (cada job baja los suyos: ~3 veces las
descargas del NRT de hoy, sin dato sobre topes de LAADS). Si pesa, la palanca es la ventana: el plan proponía 3 días
en vez de 8, lo que exige otra ventana que `ventana_sombra.py` hoy no expone por línea de comandos.

### 4. Vigilancia ciega

Workflow aparte con su propio cron (23:27 UTC), no un paso del mismo workflow, porque así avisa también si
`sombra-34.yml` deja de dispararse (cron que no llega, workflow desactivado), que es justo el caso en que un paso
interno no corre. `scripts/vigilar_sombra_34.py` exige, para cada volcán de la matriz de `sombra-34.yml`, un record de
la vía (`via_codigo_mirova` True, `regimen.perfil` sombra_34) con `processed_utc` en las últimas 48 h; sin archivo,
ilegible, sólo K, otro perfil, viejo o matriz vacía es CIEGA y se abre (o se comenta, si ya hay uno abierto) el issue
«Sombra de los 34: vigilancia ciega». Si el script no deja veredicto, issue «la vigilancia falló». Espera hasta 48 h
después de max(2026-11-03, llegada de `sombra-34.yml` a main, pedida a la API de commits; si la API falla, sólo el
2026-11-03: en el peor caso un issue de más el primer día, nunca uno de menos). No escribe en el repo.

### 5. Pruebas

`tests/test_sombra_34_s172.py`, 52 pruebas, ~39 s, sin red (`pruebas_rojo_verde.txt`):

| bloque | qué fija | rojo visto |
|---|---|---|
| lista | matriz = `volcanoes.yaml` menos `nrt.yml`, 34, sin cruce | sin workflow |
| grilla | 3.805 bytes de main intactos (sha256); 45 y nada más; regla contra los 8 Tier A a 1,5 m; cada uno de los 34 con grilla en las tres familias, zona por longitud y el lat/lon del yaml en (X0, Y0) a 0,01 celda | grilla de main |
| vía de punta a punta | gránulo sintético con un foco en el cráter, familias rotando entre los 34 (11 o 12 volcanes por familia): la vía corre, no cae a K, foco a menos de 1 km del cráter, `distance_class` null; control: sin foco, 0 MW | grilla de main (34 rojos) |
| perfil | desde `pipeline.profile`: vías, MxD03, sensores, carpeta, sin overrides; todas las constantes iguales a la sombra de los 11 salvo nombre y carpeta | sin perfil |
| workflow | `"on"` texto, cron fuera de 01 a 12 UTC, dispatch, grupo propio, `max-parallel` 8, sólo token y corte antes del pipeline, la aserción del paso **ejecutada** (pasa con sombra_34, falla con sombra_codigo_mirova), un solo `git add` a `data/sombra_34/`, reintento, revisión | sin workflow |
| vigilancia | ESPERA, OK y CIEGA con datos armados; lee la matriz del workflow; el workflow abre issue y no pushea | sin script |

Rojo: con la grilla de main y sin perfil, workflows ni script, **51 fallan y pasa 1** (el control de la regla sobre
los 8 Tier A, que no depende del cambio). Verde: 52 de 52.

**Dos pruebas viejas se ajustaron** porque suponían que sólo 11 volcanes tienen grilla (las dos en rojo con la grilla
nueva, verdes tras el ajuste; van en el commit 1):
- `tests/test_mirova_v375_codigo_s165.py::test_caja_de_375_es_la_del_brazo_c13_en_los_volcanes_con_grilla`
  (`assert 45 == 11`): compara la caja C13 sobre los 11 con `inner_radius_km` y además fija que hay 45 con grilla.
- `tests/test_sombra_codigo_mirova_s167.py::test_cada_volcan_de_la_sombra_tiene_grilla_de_miroVA_en_cada_sensor`: su
  control «un volcán fuera de MIROVA no tiene grilla» quedaba vacío; ahora usa un nombre que no está en la grilla.

Guardas corridas (verde): `test_guard_declarado_vs_efectivo_s131.py` (G4 de pushers y G5 de `"on"`),
`test_guard_perfiles_congelados_s153.py`, `test_guard_token_vacio_cron_s160.py`,
`test_guard_expresiones_workflows_s161.py`, `test_perfiles_sin_claves_duplicadas_s126.py`,
`test_experimental_congelado_s150.py`, `test_flags_d22_d25_perfil_s142.py`, `test_guard_adopcion_k_s153.py`,
`test_guard_laboratorio_no_mas_ciego_s147.py`, `test_mxd03_sola_123.py`, `test_sombra_codigo_mirova_s167.py`
(223 de 223); `test_profile_data_isolation_s124.py`, `test_perfiles_d25_k_s157.py`, `test_perfiles_diurno_k_s154.py`,
`test_reproceso_historico_k_s154.py`, `test_cloud_mask_operacional_s126.py` (25 de 25); y los cinco archivos de las
vías (`test_mirova_v750_codigo_s162`, `test_mirova_modis_codigo_s164`, `test_mirova_v375_codigo_s165`,
`test_mirova_v750_cableado_s162`, `test_sombra_codigo_mirova_s167`): 165 verdes y los 4 rojos de arriba antes del
ajuste. No corrí la suite completa (encargo).

### 6. Lector sellado de V375-E

No toqué ninguno de los archivos que compara como texto: `volcanoes.yaml`, `scripts/run_pipeline.py`, ningún `.py`
de `pipeline/`, `sombra-codigo-mirova.yml` (`git diff --name-only` contra main: ninguno). Sí cambia
`pipeline/grillas_mirova.yaml`, que el lector marca si cambia fuera de `roi_v750`/`roi_modis` (plan, H9); eso lo
ajusta otro agente en `claude/s172-v375e-relector`. **No hay que mergear esta rama antes que ese ajuste.**

## Lo que hay que mirar al revisar la sombra

**Vecinos dentro de la grilla** (`vecinos_en_la_grilla.py`, salida al lado): la vía suma en `vrp_mw` todos los
píxeles alertados de la grilla, también fuera de la caja sensible con umbral más estricto (D32), así que un vecino
activo puede aparecer en el record de un volcán tranquilo. **11 de los 34** tienen otro volcán del yaml dentro de su
grilla de 51 × 51 km; los que más importan: Quetrupillán (Villarrica a 19,8 km, lago de lava), Michinmahuida (Chaitén a
17,5), Antillanca-Casablanca (Puyehue-Cordón Caulle a 20,2) y Callaqui (Copahue a 24,5); además Descabezado Grande y
Cerro Azul-Quizapú a 8,2 km entre sí, Lonquimay y Tolhuaca a 9,6, Irruputuncu y Olca-Paruma a 24,0. El centroide
(`primary_cluster.centroid_dist_km`) lo delata; sin inner, la etiqueta no. Si MIROVA excluye vecinos en sus ROI es SIN
DATO para Chile (CLAUDE.md, marca S158 R2 de A4).

## SIN VERIFICAR

- **Que la vía corra de verdad en un gránulo real de un volcán nuevo.** Sólo está probada sobre gránulos sintéticos.
  Lo natural es un despacho con `medir: true`, un volcán y una ventana pasada (como S168 hizo con Láscar), después del
  merge; no lo hice (encargo: no despachar).
- Que el fetch encuentre MxD03 para los gránulos MODIS de los 34 (en la sombra de los 11 fueron 77 de 77 por la vía);
  si no, esas pasadas caen a K con 5 km y el record lo dice.
- Duración real por job y pared de la corrida (las cifras son la estimación del informe de capacidad), carga sobre
  LAADS y Earthdata con 34 jobs más por día, y el tope de jobs simultáneos del plan de la cuenta.
- Que GitHub dispare el cron a una hora razonable: los de la experimental y la sombra de los 11 llegan con 3 a 5 h de
  atraso; si éste llega igual, cae entre las 16 y las 18 UTC, todavía fuera del NRT.
- Si el lector de VIIRS 750 también marca régimen por el cambio de la grilla (el plan, Tarea 2.4, lo deja como
  SOSPECHA); no lo revisé.
- El comportamiento de `revisar_sombra.py` en volcanes del norte (Taapaca a -18°): con menos pasadas por día podría
  dar más notas de «sin pasada»; la lógica es la misma que en Isluga, no lo medí.

## Faltas de procedimiento, dichas

- Edité una vez mi propio archivo nuevo de pruebas con un heredoc de Python (tres reemplazos) y creé
  `vecinos_en_la_grilla.py` con un heredoc, contra la regla común de no editar archivos del repo con heredocs. El
  contenido quedó verificado (pruebas en verde, script corrido); los demás cambios los hice con la herramienta de
  edición.
- Para ver el rojo restauré temporalmente la grilla de main con `git checkout HEAD -- pipeline/grillas_mirova.yaml`
  (archivo propio, sin cambios ajenos) y la regeneré con el script; el resultado es idéntico byte a byte al primero.
