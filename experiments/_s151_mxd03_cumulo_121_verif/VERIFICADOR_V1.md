# Verificador con contexto limpio: pre-registro de la tarea 1.21 (PR #840, head f3fb8d7a)

Worktree revisado: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\agent-aa3ef748ab319056b\`
(sin cambios: `git status --short` vacío al terminar). Mis scripts: `C:\Users\nmend\AppData\Local\Temp\claude\verif_121\scripts\`.

## Veredicto: SELLABLE CON ARREGLOS

El instrumento mide el pipeline real (los seis brazos corren `calculate_vrp` + `store.append_record` +
el predicado con node), así que el veredicto global que dé será sobre el código de hoy. Lo que falla
es la lectura que el README le prepara a Nicolás: el modelo de la cadena (y con él la predicción
«46 de 46», el «0 pasan de 1 a 0» y la «prueba del replay») no cubre la rama del Test 1, que es
justamente la de las dos pérdidas de la 1.17. Y FRÁGIL no calcula lo que el README dice.

## Lo que corrí

- `python -m pytest tests/test_mxd03_cumulo_121.py`: **39 passed** en 3,6 s (node presente, sin skips).
- sha256 de `experiments/_s151_mxd03_etiquetas/poblacion.json` con LF: `89a526cc...c9e8`, igual en el
  worktree y en `origin/main`. La muestra es la de la 1.17.
- `cobertura_estimador.py` re-corrido (300 reps, salida redirigida al temporal): reproduce exacto las
  cinco filas del método principal.
- `scripts/poder.py`, `fuentes.py`, `muestra_t1.py`, `test1_rama.py`, `test1_rama2.py`,
  `anisotropia.py` (este último sobre los artefactos del run 38894508138 ya bajados en
  `C:\Users\nmend\AppData\Local\Temp\claude\mxd03_117\art\`).

## Afirmación 1: `replay_cumulo` modela la cadena

**En la rama `eruption`, `cluster_rescue` y `vent` sí.** Leí `store.py:378-520`: el rescate F47
(exige `hotspot_dist > MAX` y cúmulo con energía dentro de la cerca), la regla D (`vrp_vent > 0`) y el
guard A46 (`summit` con `pc.vrp > 0` y `pc.centroid > inner` pasa a `far`) dan exactamente las cuatro
ramas de `predecir_etiqueta_cumulo.py:50-65`. Y el orden de magnitud es plausible contra A82: el
replay publica 4.454 de 5.047 negativos limpios (88,3 %) y A82 midió cúmulo con magnitud dentro del
inner en 89,1 % de 4.800 negativos limpios MODIS; S150 en Chillán, 22 de 28.

**En la rama del Test 1, no.** `derivar_distance_class` se llama en `process_modis.py:1328` con el
`primary_cluster` del camino de erupción. Después, dentro de `if final_hotspot_source == "test1" ...`
(`:1381`), ese `primary_cluster` se **reemplaza** por el cúmulo del Test 1 (`:1425` y `:1440`). El
record guarda el segundo; con el flag encendido la etiqueta sale del primero. `replay_cumulo` lee el
guardado. Medido con el pipeline real sobre una escena sintética (`test1_rama2.py`: disco de 1 px
+1,0 K en el cráter y Salar de 330 K a 15 km, inner 5, cerca 25):

| flag | fuente | pc que vio `derivar` | etiqueta | pc guardado | dc final | publica |
|---|---|---|---|---|---|---|
| False | test1 | 14,983 km | summit | 0,375 km | summit | 1 |
| True | test1 | 14,983 km | **far** | 0,375 km | **far** | **0** |

El replay sobre el record de producción da `summit` / 1 (pc guardado a 0,375 km). O sea que con la
etiqueta del cúmulo **existe un camino de 1 a 0 que el replay no ve**: Test 1 dispara en el cráter, el
camino de erupción sólo encontró el Salar dentro de la cerca, y el flag etiqueta con el Salar.

Tamaño en la población (`fuentes.py`): **126 records con fuente `test1`**, de ellos **4 protegidas**,
113 negativos limpios (106 publicados por C), 1 alerta bajo 1 MW. Las 4 protegidas son de Láscar Terra
y tienen el hotspot de erupción en el Salar a 19,07 / 21,34 / 21,52 / 24,5 km (sin rescate F47), y
**dos de ellas son las pérdidas de la 1.17** (`MOD021KM.A2026110.0130` y `MOD021KM.A2026120.0130`).
Las 4 están en la muestra; en total la muestra tiene 18 gránulos con fuente `test1`.

Consecuencias:
- «CC recupera 46 de 46» y «1 a 0 = 0» son una **cota**, no una predicción: CC y la `etiqueta` pueden
  salir PIERDE PROTEGIDA por este camino. Si en la geometría de C el camino de erupción tenía un cúmulo
  en el cráter (como el de 0,23 y 0,48 km que la 1.17 vio con MxD03), no pasa; no se sabe desde los
  records.
- La **prueba del replay** (acuerdo global ≥ 90 %, `evaluar_cumulo.py:276-282`) no puede detectar esta
  falla: toca a lo sumo 18 de 471 gránulos (3,8 %). Es un instrumento que no puede dar el otro
  resultado (A116).
- `tipos_de_cambio` atribuye el cúmulo con el pc guardado, que en esos 18 no es el que etiquetó.
- **Para la decisión de producción (A45)**: encender el flag crea una asimetría A46 nueva dentro del
  propio flag (etiqueta desde un cúmulo, magnitud publicada desde otro). Nicolás tiene que saberlo
  antes de decidir, salga lo que salga.

## Afirmación 2: cobertura y poder del estimador

La cobertura medida se reproduce. Pero:
- Cobertura **1,000 en cuatro de cinco escenarios** con nominal 95 % quiere decir que el intervalo es
  conservador: el piso de varianza lo pone el medio conteo de suavizado en 32 celdas de 2 a 6
  gránulos, no los datos. Por eso ±394 bajo el nulo.
- **No hay ningún escenario con verdad negativa** en `cobertura_estimador.py`; MEJORA sólo se prueba con
  el caso extremo de apagar el 100 % (`test_mejora_alcanzable_con_la_poblacion_real`). Medí el poder
  (`poder.py`, 300 reps, n real por celda):

| efecto en negativos limpios | verdad aprox. | P(MEJORA) | P(EMPEORA) |
|---|---|---|---|
| apaga 50 % de las 587 publicaciones de C | −293 | 0,033 | 0 |
| apaga 70 % | −410 | 0,473 | 0 |
| apaga 90 % | −528 | 0,877 | 0 |
| enciende 5 % de los no publicados | +222 | 0 | 0,023 |
| enciende 10 % | +444 | 0 | 0,517 |

  MEJORA y EMPEORA son alcanzables, pero MEJORA exige que MC apague unas 7 de cada 10 falsas alarmas
  de producción. Con una etiqueta que agrega publicaciones, en la principal es inalcanzable en la
  práctica, y «adoptable» también. El README dice «unos 400 errores»; debería decirlo en estas unidades.

## Afirmación 3: la traslación rígida como nulo

El tamaño en km es el del cráter, pero lo que mueve la etiqueta es el corrimiento **en píxeles**, y el
píxel MODIS es anisótropo. Sobre los 470 gránulos de la 1.17 (`anisotropia.py`): bajo 35° el real y
el rumbo al azar valen lo mismo en píxeles (razón 1,00 y 0,97); sobre 50° (224 gránulos) el real va
91 % por el eje del barrido, donde el píxel es más ancho, y el rumbo al azar es **24 % más grande en
píxeles** (mediana de la razón 1,24). El nulo perturba más que MxD03 en la mitad de la muestra, así que
sesga FRÁGIL y `M_contra_ruido` a favor de MxD03. Las dos pérdidas de la 1.17 son de cenit bajo (15,6°
y 17,4°), donde el nulo sí es comparable. La frase del README «reproduce su tamaño en el cráter, que es
lo que mueve la etiqueta» no está medida.

## Afirmación 4: contra C o contra MIROVA

Contra C es la letra de `docs/MISSION.md` regla 1 («ningún cambio que pierda una alerta protegida»):
producción ya publica sólo 9 de 46 protegidas, así que contra MIROVA en absoluto C ya fallaría. El
balance relativo equivale a restar los errores de cada brazo contra MIROVA. Dos cosas que el README
debe poner delante de Nicolás: (a) las protegidas **ganadas** (37 predichas) no entran en Δ por la letra
de MISSION, y es una decisión suya si eso es lo que quiere; (b) C es el código de hoy, no lo publicado,
así que la deriva sobre las protegidas se debería informar aparte.

Estados: todos tienen test que los produce. Inalcanzables o casi: MEJORA de la principal (arriba), y la
«prueba del replay» en su lado «no creíble» frente a la falla de la rama Test 1.

## Afirmación 5: el flag llega a sus consumidores

Verificado con `grep -rn -i "distance_class_from\|from_cluster"` sobre todo el repo (salvo `data/`):
en código de producción sólo `pipeline/profile.py:648` (definición) y `pipeline/process_modis.py:173`
(import por valor), `:1330` y `:1497` (los dos argumentos de `derivar_distance_class`). Lo demás son
workflows que imprimen `pipeline.profile` y scripts de experimentos. `store.py` no lo lee. El parche en
el módulo llega a las dos llamadas. Lo que no llega bien es la **entrada** que el flag consume (el pc
previo al reemplazo del Test 1, afirmación 1): es la forma A118 de este flag.

## Afirmación 6: muestra, workflow, tiempo

Muestra: igual (sha256 arriba). Workflow `probe-s151-mxd03-cumulo-121.yml`: candado en el job `plan`
(l. 39-43) del que dependen los demás; sólo `secrets.EARTHDATA_TOKEN`, con falla inmediata si viene
vacío en `plan` y en cada job; `"on":` entre comillas (l. 14); grupo propio
`probe-s151-mxd03-cumulo-121`, distinto de `s146-ab-sin-test1` (`reproc-s146-ab-sin-test1.yml:61`) y de
`s151-ab-diurno` (`reproc-s151-ab-diurno.yml:71`), con `cancel-in-progress: false`; sin push;
`timeout-minutes: 95` contra presupuesto 70 (1,36×). La duración sigue SIN CRONOMETRAR; el corte de
70 min marca `sin_tiempo` y eso da INCOMPLETO, no un veredicto falso.

## Arreglos bloqueantes

1. **Rama del Test 1** (`process_modis.py:1328` contra `:1425`/`:1440`):
   a. README y cabecera de `predecir_etiqueta_cumulo.py`: corregir la regla de la cadena para fuente
      `test1` y declarar que «46 de 46» y «0 de 1 a 0» son cota superior, con los 126 records (4
      protegidas, 2 de ellas las pérdidas de la 1.17).
   b. El espía de `probe_cumulo.py:73-75` debe guardar los cuatro argumentos y el resultado de
      `derivar_distance_class`, para que el evaluador sepa con qué cúmulo se etiquetó.
   c. La prueba del replay se informa por grupo (protegidas, fuente `test1`, resto), no sólo global.
   d. Un caso sintético TEST1 en `probar_probe_cumulo.py` (el de `test1_rama2.py`: +1,0 K en el
      cráter, Salar a 15 km) que fije C 1 / CC 0.
   e. En «lo que cada resultado le diría a Nicolás»: el flag, tal como está, etiqueta los records del
      Test 1 con un cúmulo que no es el publicado.
2. **FRÁGIL** (`evaluar_cumulo.py:262-263`) es global: basta que el nulo pierda **cualquier** protegida,
   no la misma pasada, mientras el README la lee como «la publicación de esa pasada se rompe». Calcular
   por pasada (intersección de `perdidas_detalle`) y cambiar «cualquier corrimiento» por «un sorteo de
   un corrimiento al azar». Agregar el control negativo (nulo pierde otra pasada: no FRÁGIL).

## No bloqueantes

- Nulo anisótropo: sortear el rumbo en coordenadas de píxel (o el mismo eje con signo al azar), o al
  menos escribir el sesgo medido (1,24× sobre 50°) en Límites.
- Agregar escenarios con verdad negativa a `cobertura_estimador.py` y escribir el umbral de MEJORA en
  unidades del operador (unas 7 de cada 10 falsas alarmas de C).
- Decir que la cobertura 1,000 es conservadora y que el ±394 lo fija el suavizado.
- Protegidas ganadas fuera de Δ y deriva de C sobre protegidas: ponerlas en la tabla de lectura.
- `evaluar_cumulo.py:143` dice «14 granulos»; son 12 negativos limpios (18 records) en el estrato «sin».
- Cronometrar con un job suelto (`-f jobs='["Lascar-2"]'`) antes de los otros 11.
