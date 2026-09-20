# A/B S146: sin el Test 1 integrado en el ROI. Listo para despachar, NO despachado

El criterio vive en [`PREREGISTRO.md`](PREREGISTRO.md) y sus umbrales congelados en
[`parametros.json`](parametros.json). Los dos se commitean **antes** del primer despacho: un
sello sin historia de git no prueba el orden (V-16). **Nada de esto corrió todavía contra NASA.**

## Qué hay acá

| archivo | qué es |
|---|---|
| `PREREGISTRO.md` | el criterio completo: brazos, ventana, métricas, umbrales, controles, regla de decisión, lo que el A/B no decide, y las tres decisiones que esperan a Nicolás |
| `parametros.json` | los umbrales, congelados. Cambiar uno después de ver un resultado invalida el A/B |
| `evaluar.py` | el evaluador. Reusa el cargador y el etiquetado de `scripts/banco_paridad.py` y el predicado de publicación **ejecutado con node** desde `frontend/index.html` |
| `poder_recall.py` | mide el nulo de cada vara de recall **antes** de fijar el umbral. Su salida decide cuál vara puede decidir |
| `sintetico.py` | prueba el evaluador contra cuatro brazos con veredicto conocido de antemano |
| `contar_pasadas.py` | cobertura pareja entre brazos. Lo corre el workflow y falla si un brazo tiene menos pasadas que el control |
| `diff_perfiles.py` | vuelca los 143 atributos de `pipeline.profile` de cada brazo y prueba que difieren de producción sólo en lo declarado |
| `*_salida.txt`, `*.json` | las salidas crudas de lo que sí se corrió en local |

Los perfiles están en `pipeline/profiles/_s146_ab_{control,sin_test1,sin_prioridad_debil}.yaml` y
el workflow en `.github/workflows/reproc-s146-ab-sin-test1.yml`.

## El comando exacto para despachar

Primero commitear el pre-registro y los parámetros, y mergear a `main` (un `workflow_dispatch`
sólo es invocable desde la rama por defecto). Después:

```bash
gh workflow run reproc-s146-ab-sin-test1.yml --ref main \
  -f preregistro_aprobado=si \
  -f start=2026-09-01 \
  -f end=2026-09-20 \
  -f vols='["Lascar","Lastarria","Isluga","Tupungatito","PlanchonPeteroa","NevadosDeChillan","Llaima","Villarrica","Copahue","PuyehueCordonCaulle","Chaiten"]' \
  -f brazos='["_s146_ab_control","_s146_ab_sin_test1","_s146_ab_sin_prioridad_debil"]'
```

Sin `preregistro_aprobado=si` el workflow no corre ningún job: es un candado, no un aviso.

Para repetir un volcán que quedó con pasadas de menos por un corte de NASA (A64 y A108), el mismo
comando con la lista corta, por ejemplo `-f vols='["Llaima"]' -f brazos='["_s146_ab_sin_test1"]'`,
y volver a contar antes de evaluar.

Para evaluar, una vez que estén las salidas (en la rama `s146-ab/<run_id>` o en el artefacto
`s146ab-todo`):

```bash
python experiments/_s146_ab_sin_test1/evaluar.py \
  --control <dir>/_s146_ab_control \
  --brazo   <dir>/_s146_ab_sin_test1 \
  --brazo   <dir>/_s146_ab_sin_prioridad_debil \
  --cons experiments/_s145_paridad/_dl_referencia/registro_vrp_consolidado.csv \
  --ocr  experiments/_s145_paridad/_dl_referencia/registro_vrp_ocr.csv \
  --control-cargador \
  --out experiments/_s146_ab_sin_test1/resultado.json
```

## Duración estimada, y en qué me baso

**De 1,5 a 3 horas por job, y de 9 a 18 horas de reloj la corrida completa.** Son 33 jobs (11
volcanes por 3 brazos) con `max-parallel` 6, o sea unas 6 tandas.

La base son dos mediciones del propio proyecto, ninguna exactamente igual a esta corrida:

- S135 midió **de 72 a 153 minutos por job** de 45 días con un solo sensor (VIIRS 375), citado en
  `.github/workflows/reproc-s143-ab-d22d25.yml`. Acá son menos días (20) y más sensores (3).
- El cron NRT procesa **un día de los tres sensores para un volcán** dentro de su timeout de 50
  minutos, y típicamente en bastante menos. Veinte días de eso, con el grueso del tiempo en la
  descarga, dan del orden de 1,5 a 3 horas.

`timeout-minutes` es 330 para el job y 300 para el paso del reproceso: más de 1,3 veces lo
esperado (A15) y muy por debajo del tope duro de 6 horas de GitHub. **SOSPECHA declarada**: no
tengo una medición de un reproceso de 20 días con los tres sensores; si la primera tanda se acerca
al timeout, hay que partir la ventana en dos tramos antes de seguir.

El token de Earthdata vence el **2026-10-03**: la corrida tiene que terminar antes.

---

# Lo que se probó en local, con la salida cruda pegada

## 1. Los perfiles difieren de producción sólo en lo declarado

`python experiments/_s146_ab_sin_test1/diff_perfiles.py`

```
perfil base mirova_equivalent: 143 atributos

[OK] mirova_equivalent
  atributos: 143 | faltan: - | sobran: - | data_subdir: mirova_equivalent (aislado: True)
  diferencias contra mirova_equivalent (sin contar identidad): ninguna
  declaradas: - | inesperadas: - | declaradas sin aplicar: -

[OK] _s146_ab_control
  atributos: 143 | faltan: - | sobran: - | data_subdir: _s146_ab_control (aislado: True)
  diferencias contra mirova_equivalent (sin contar identidad): ninguna
  declaradas: - | inesperadas: - | declaradas sin aplicar: -

[OK] _s146_ab_sin_test1
  atributos: 143 | faltan: - | sobran: - | data_subdir: _s146_ab_sin_test1 (aislado: True)
  diferencias contra mirova_equivalent (sin contar identidad): {"ENABLE_TEST1_PATH": [true, false]}
  declaradas: ['ENABLE_TEST1_PATH'] | inesperadas: - | declaradas sin aplicar: -

[OK] _s146_ab_sin_prioridad_debil
  atributos: 143 | faltan: - | sobran: - | data_subdir: _s146_ab_sin_prioridad_debil (aislado: True)
  diferencias contra mirova_equivalent (sin contar identidad): {"ENABLE_TEST1_PRIORITY_WEAK_CLUSTER": [true, false]}
  declaradas: ['ENABLE_TEST1_PRIORITY_WEAK_CLUSTER'] | inesperadas: - | declaradas sin aplicar: -

control: mirova_equivalent comparado consigo mismo da 0 diferencias (tiene que ser 0)
VEREDICTO: todos los brazos difieren solo en lo declarado
```

La comparación es contra el perfil de producción cargado por `pipeline.profile` con
`VRP_PROFILE=<perfil>`, no contra el YAML: un flag puede estar escrito en un lado y leerse de
otro (A89). Los 143 atributos son todos los públicos en mayúsculas del módulo. `PROFILE_NAME` y
`DATA_SUBDIR` quedan fuera de la comparación por ser identidad, y en su lugar se comprueba aparte
que cada brazo escriba en su propio directorio.

## 2. El poder de cada vara de recall, medido sobre producción antes de fijar umbrales

`python experiments/_s146_ab_sin_test1/poder_recall.py --cons ... --ocr ...`

```
ventana 2026-09-01 a 2026-09-20 | records 2360 | etiquetas {'neg_limpio': 1434, 'sin_info': 732, 'far_ref': 32, 'pos': 162}
tasa base de publicacion: {"MODIS": {"n_pasadas": 457, "n_publica": 53, "tasa": 0.116}, "VIIRS375": {"n_pasadas": 954, "n_publica": 833, "tasa": 0.8732}, "VIIRS750": {"n_pasadas": 949, "n_publica": 207, "tasa": 0.2181}}
noches de volcan en que publicamos algo: 218 de 219

vara                        observado   nulo med             nulo min a max    alcanza obs poder
noche_volcan                    78/78         78                    77 a 78          0.985 NO DISCRIMINA
noche_sensor                    89/90         86                    82 a 89           0.05 DEBIL
noche_sensor_MODIS                1/1          0                      0 a 1          0.315 DEBIL
noche_sensor_VIIRS375           75/75         75                    74 a 75          0.985 NO DISCRIMINA
noche_sensor_VIIRS750           13/14         11                     7 a 14          0.135 DEBIL
pasada_pos                    157/162        139                  128 a 147            0.0 DISCRIMINA
pasada_pos_MODIS                  1/1          0                      0 a 1           0.17 DEBIL
pasada_pos_VIIRS375           143/143        132                  124 a 137            0.0 DISCRIMINA
pasada_pos_VIIRS750             13/18          8                     2 a 12            0.0 DISCRIMINA
```

Confirma I-01 y lo precisa: la noche de volcán no discrimina (el azar la alcanza en el 98,5 % de
los 200 barajados dentro de cada volcán y sensor), y la noche del sensor en VIIRS 375 tampoco.
La **pasada** sí, en los dos sensores VIIRS, y con margen. Por eso la vara que decide el A/B es
la pasada, no la noche.

Un matiz propio contra el auditor del frente I, que dijo que sólo VIIRS 750 por pasada
discrimina: **VIIRS 375 por pasada también discrimina**, 143 de 143 contra un nulo cuyo máximo en
200 barajados fue 137.

## 3. El evaluador, contra una salida sintética con casos conocidos

`python experiments/_s146_ab_sin_test1/sintetico.py`

Cuatro brazos construidos a mano sobre volcanes y fechas reales, con su referencia de MIROVA
sintética, y el veredicto correcto sabido de antemano:

- **bueno**: baja mucho la publicación en negativos limpios y no pierde nada, tiene que dar ADOPTAR;
- **malo**: baja igual, pero pierde una noche que MIROVA publicó con 3,0 MW, tiene que dar NO ADOPTAR;
- **muerto**: copia byte a byte del control, no cambia nada, tiene que dar NO ADOPTAR (si diera
  ADOPTAR, el evaluador estaría roto, y ese es el modo de falla que más caro sale, A110);
- **inventa**: publica en pasadas donde el control no tiene ningún píxel anómalo, tiene que dar
  INDECIDIBLE.

```
ventana 2026-09-01 a 2026-09-20 | referencia nocturna 234 filas | sha index.html 24fba8a157
control positivo del control: cumple=True | {"n_pasadas_comparadas": 234, "fraccion_publicacion_identica": 1.0, "diferencias_por_campo": {}}
control del cargador contra banco_paridad: identico=True

==============================================================================
COMPROBACION: veredicto esperado contra veredicto obtenido
  bueno    esperado ADOPTAR      obtenido ADOPTAR       OK   criterios que fallan: -
  malo     esperado NO ADOPTAR   obtenido NO ADOPTAR    OK   criterios que fallan: ['C1_recall_pasada', 'C2_noches_dentro_de_lo_previsto']
  muerto   esperado NO ADOPTAR   obtenido NO ADOPTAR    OK   criterios que fallan: ['C3_publicacion_negativos']
  inventa  esperado INDECIDIBLE  obtenido INDECIDIBLE   OK   criterios que fallan: ['C5_nulo_estructural']
  'malo' falla por recall (1 pasada perdida de 0,5 MW o mas) y 'muerto' por publicacion (0 pasadas perdidas): motivos distintos -> True
  control del cargador contra banco_paridad identico: True
  control positivo del control cumple: True
VEREDICTO DE LA PRUEBA: PASA
```

La salida completa, con las tablas por brazo, está en
[`sintetico_salida.txt`](sintetico_salida.txt). Lo que la prueba comprueba, y que es más que "los
cuatro dieron lo esperado": que los cuatro veredictos sean **distintos entre sí** y que `malo` y
`muerto` fallen **por criterios distintos**. Si el evaluador respondiera lo mismo a todo, no
estaría leyendo los datos.

**Lo que esta prueba NO cubre**, para que nadie la lea como garantía: no prueba que el pipeline
haga lo que el perfil dice (eso lo prueba el punto 1 y lo vuelve a comprobar el workflow en cada
job), no prueba que los umbrales sean los correctos (eso es una decisión, y está argumentada en
el pre-registro), y no prueba nada sobre gránulos reales, nubes ni geometría: los records
sintéticos son mucho más limpios que los de verdad.

## 4. El guard del repo

```
python -m pytest tests/test_guard_declarado_vs_efectivo_s131.py -q
18 passed in 10.13s
```

En la primera corrida **falló**, y vale la pena dejarlo escrito. Su control G4 exige que todo
workflow que contenga `git push` tenga o el grupo de concurrencia `push-main` o su propio bucle de
reintento. Este workflow **no pushea a `main`**, pushea a una rama nueva por corrida, pero el
guard detecta el texto y no distingue una cosa de la otra. Se resolvió agregando el reintento, que
corresponde por su propia razón: si el push se cae por red se pierde la única copia durable,
porque el artefacto caduca. No se tocó el test.

También se corrieron los otros guards que leen perfiles o workflows
(`test_perfiles_sin_claves_duplicadas_s126`, `test_guard_claves_fantasma_s127`,
`test_guard_timeout_vs_ventana_s129`, `test_cadencia_cron_s133`, `test_gr2_profile_invariants`,
`test_guard_afirmaciones_de_alcance_s127`): **146 pasados, 3 saltados**. La suite completa no se
corrió.

## 5. Y el YAML del workflow

```
python -c "import yaml; d=yaml.safe_load(open('.github/workflows/reproc-s146-ab-sin-test1.yml')); print(list(d)[1]=='on')"
True
```

La clave `on` se lee como el string `"on"` y no como el booleano `True`: es el Norway Problem de
YAML 1.1 (A43), que en este repo ya costó trece horas de HTTP 422.
