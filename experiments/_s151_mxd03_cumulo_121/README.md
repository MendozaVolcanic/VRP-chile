# Probe S151, tarea 1.21: MxD03 junto con la etiqueta MODIS desde el cúmulo, con un brazo de ruido

**Estado: versión 2, escrita y probada con datos sintéticos, NO corrida.** Este README fija la
población, los brazos, el estimador, los estados y el criterio antes de la primera corrida. Lo sella
Nicolás después de que un verificador con contexto limpio lo revise (regla 1.6 del loop). La decisión
de producción sigue siendo suya (A45): nada de esto toca `pipeline/process_*.py`, `pipeline/store.py`
ni `pipeline/profiles/mirova_equivalent.yaml`.

La versión 1 (#840, head `f3fb8d7a`) la revisó un verificador con contexto limpio y la dio por «sellable
con arreglos» (informe fuera del repo: `C:\Users\nmend\AppData\Local\Temp\claude\verif_121\VERIFICADOR.md`,
scripts en `scripts\`). La versión 2 aplica sus dos bloqueantes y los no bloqueantes:

1. **La rama del Test 1 no estaba modelada** (sección «La rama del Test 1»): la predicción pasa a ser
   cota en esa fuente, el espía guarda los argumentos, la prueba del replay se informa por grupo, hay un
   caso sintético TEST1 y una nota para la decisión A45.
2. **FRÁGIL era global**: ahora es por pasada, con su control negativo.
3. No bloqueantes: poder declarado en unidades del operador con escenarios de verdad negativa; las
   protegidas ganadas y la deriva de C puestas delante; la anisotropía del nulo escrita en Límites (no
   corregida, ver ahí por qué); el conteo del estrato «sin» corregido; despacho de un job suelto para
   cronometrar antes de los 12.

## Por qué

La 1.17 (run 38894508138) comparó la posición de producción (`_interp_geo`) contra la oficial (MxD03)
en 470 gránulos y dio, por la letra de su pre-registro, **PIERDE PROTEGIDA**: dos alertas de MIROVA de
1,36 y 1,34 MW (Láscar Terra, 2026-04-20 y 2026-04-30 01:30) se dejan de publicar con MxD03, y MxD03
gana 9. El verificador del resultado
(`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s151_mxd03_etiquetas_verif\resultado\VERIFICADOR_RESULTADO.md`,
rama `loop/activo`) encontró que esas dos pérdidas **no son de posición**.

Lo que pasa en el volcán y en el píxel: el satélite ve el mismo calor en el cráter con las dos
geolocalizaciones, y con MxD03 el cúmulo queda incluso más cerca del cráter (0,72 a 0,23 km y 0,86 a
0,48 km). Lo que cambia es qué punto de la escena se elige como «hotspot final». El Test 1 integra un
disco de 3 km con píxeles de 1 km; correr la grilla unos cientos de metros cambia qué píxeles entran al
disco y cuáles al fondo, el Test 1 deja de disparar (inferido, no medido en la 1.17), y gana el píxel
más caliente de la escena, que en Láscar es el borde del Salar de Atacama a 19 y 21 km. En MODIS la
etiqueta `summit`/`far` sale de ese hotspot y no del cúmulo, porque
`ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER = False`. El Salar queda dentro de la cerca de 25 km, así que
el rescate F47 de `store.py` no actúa, la etiqueta queda `far` y el tablero no publica. Es la asimetría
A46/A81: el mismo calor, otra etiqueta.

El verificador encontró además que al modelo de corrimiento le faltaba un eje, y que el «control» C'
sólo prueba que el parche no fabrica diferencias, no cuánto cambia la etiqueta si uno mueve las
posiciones al azar. Esta tarea mide lo que la 1.17 no podía: si MxD03 es adoptable **cuando la
etiqueta sale del cúmulo**, separando el efecto de la etiqueta del de la posición y comparando cada uno
contra un corrimiento al azar del mismo tamaño.

## El flag que cambia el brazo MC (A89, A118)

Antes de diseñar el brazo se trazó cómo lee el código el flag, porque el nombre en la definición no es
el del uso:

- `pipeline/profile.py:648` lo define desde el YAML (`enable_modis_distance_class_from_cluster`).
- `pipeline/process_modis.py:173` lo **importa por valor** (`from pipeline.profile import ...`). Por eso
  cambiarlo en `pipeline.profile` no llega a nada: el test
  `test_parchear_pipeline_profile_no_llega_y_parchear_el_modulo_si` lo mide (etiqueta `far` contra
  `summit` en la misma escena).
- Sus **dos únicos consumidores** son las dos llamadas a `derivar_distance_class`
  (`process_modis.py:1328`, la que corre hoy, y `:1495`, dentro de la rama del ancla honesta, apagada con
  `ENABLE_HONEST_ANCHOR_MODIS = False`). Las dos leen el nombre global del módulo en el momento de la
  llamada, así que el brazo cambia `process_modis.ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER` y llega a
  las dos.
- `grep -rn -i distance_class_from_cluster` sobre `pipeline/*.py`, `scripts/*.py` y `frontend/*.html`
  da sólo `pipeline/process_modis.py` y `pipeline/profile.py`. **`store.py` no lee el flag.** Después de
  la etiqueta aplica tres reglas que no dependen de él:
  - el rescate F47, `store.py:393`: sólo si `hotspot_dist_km` supera `radius_km` (25 km en los Tier A)
    y el cúmulo tiene energía dentro de esa cerca; fuerza `summit`;
  - la regla D del vent, `:479`: si `vrp_vent_mw > 0`, fuerza `summit`;
  - el guard A46, `:514`: un `summit` cuyo cúmulo con energía está fuera del inner pasa a `far`.

  Con el flag encendido y cúmulo presente, la etiqueta final queda `summit` sólo si el cúmulo está
  dentro del inner (o, sin energía en el cúmulo, si el vent-path vio algo).

Tres defensas fijan esto:

1. **El espía.** Cada brazo envuelve `derivar_distance_class` y guarda el `desde_cluster` que vio en
   cada llamada. El evaluador da INVALIDO si un brazo con etiqueta del cúmulo vio `False`, si uno de
   producción vio `True`, o si algún brazo nunca llamó a la función.
2. **El guard de consumidores.** `test_ningun_otro_modulo_lee_el_flag` y
   `test_los_consumidores_del_flag_son_las_dos_llamadas_a_derivar` fallan si aparece otro consumidor.
3. **La mutación.** `test_si_el_brazo_mc_no_cambia_el_flag_la_prueba_falla` corre la prueba sintética
   con el brazo MC en etiqueta de producción y exige que falle.

## La rama del Test 1: el flag llega, pero con otra entrada (verificador, bloqueante 1)

El flag llega a sus dos consumidores, pero lo que **consume** no es siempre el cúmulo que se publica.
`derivar_distance_class` (`process_modis.py:1328`) recibe el `primary_cluster` del camino de erupción.
Si la fuente final es `test1` (`:1381`), ese cúmulo se **reemplaza** después por el del Test 1
(`:1425` y `:1440`), que es el que se guarda y el que el tablero publica.

En el volcán: el Test 1 ve calor en el cráter, el camino de erupción sólo encontró el Salar dentro de la
cerca, y con el flag encendido la etiqueta sale del Salar. El caso sintético TEST1 lo reproduce con el
pipeline real (disco de 5 píxeles a +1,0 K en el cráter, Salar de 330 K a 15 km): C publica con la
etiqueta `summit`; CC queda `far` y no publica, etiquetado con un cúmulo a 14,98 km mientras el guardado
está a 0,375 km (`probar_probe_cumulo.py`, caso TEST1). El replay, que sólo ve el cúmulo guardado, dice
que CC publica (`test_el_replay_no_ve_la_rama_del_test1`).

En la población hay **126 records con fuente `test1`**: 4 protegidas, 1 alerta bajo 1 MW, 113
negativos limpios y 8 sin información (`fuente_test1|*` en `prediccion_cumulo.json`). Las 4 protegidas
son de Láscar Terra, C las publica, y **dos son las pérdidas de la 1.17** (`MOD021KM.A2026110.0130` y
`MOD021KM.A2026120.0130`). Las 4 están en la muestra.

Qué cambia en el probe por esto:

- **El espía guarda los cuatro argumentos y el resultado** de cada llamada (`derivar` en el JSON), y
  `cumulo_etiqueta` compara el cúmulo con que se etiquetó contra el guardado. El evaluador cuenta por
  brazo los gránulos etiquetados con otro cúmulo (`etiqueta_con_otro_cumulo`).
- **La prueba del replay se informa por grupo** (protegidas, fuente `test1`, resto). Su credibilidad se
  decide sólo con el resto: en la fuente `test1` el replay no puede acertar por construcción.
- `tipos_de_cambio` atribuye el cúmulo con el guardado; en esos gránulos no es el que etiquetó, y se
  cruza con `etiqueta_con_otro_cumulo`.

**Para la decisión de producción (A45), salga lo que salga:** encender el flag tal como está crea una
asimetría A46 dentro del propio flag. En los records del Test 1 la etiqueta sale de un cúmulo (el de
erupción, que puede ser el Salar) y la magnitud que se publica sale de otro (el del Test 1). Si Nicolás
quisiera adoptar la etiqueta del cúmulo, primero habría que decidir de cuál cúmulo.

## Qué se mide

Por cada gránulo, el pipeline de producción (`calculate_vrp` + `store.append_record` en un directorio
temporal + el predicado del tablero ejecutado con node, A97) corre sobre el **mismo L1B** en seis
brazos. Reutiliza `procesar_brazo`, `publica`, `desplazamiento_crater` y la E/S de
`experiments/_s151_mxd03_etiquetas/probe_etiquetas.py`, con los argumentos de `scripts/run_pipeline.py`
que la 1.17 ya fija por AST.

| brazo | posición | etiqueta | qué aísla |
|---|---|---|---|
| **C** | `_interp_geo` | hotspot final (producción) | producción |
| **CC** | `_interp_geo` | cúmulo | la etiqueta sola |
| **M** | MxD03 | hotspot final | la posición sola (repite el M de la 1.17) |
| **MC** | MxD03 | cúmulo | **el arreglo que se evalúa** |
| **R** | `_interp_geo` trasladada | hotspot final | nulo de M |
| **RC** | la misma traslación que R | cúmulo | nulo de MC |
| **C'** | `_interp_geo` por el parche de M | hotspot final | prueba del parche (2 gránulos por job) |

**CC entra** porque sin él no se puede separar «la etiqueta del cúmulo arregla las dos pérdidas» de
«MxD03 las arregla», y porque es el arreglo más barato si la posición resultara no importar.

**El ruido.** R traslada en bloque toda la grilla de `_interp_geo` una distancia **igual al
corrimiento medido en el cráter de ese mismo gránulo** (`_interp_geo` menos MxD03), hacia un rumbo al
azar. El rumbo sale de `sha1("s151-tarea-1.21-ruido" + clave)`, así que es determinista y parejo (un
test lo comprueba con 4.000 claves). Es una traslación y no ruido píxel a píxel porque el defecto real
es un campo suave (unos cientos de metros de variación dentro del ROI de 25 km): mover cada píxel por
separado barajaría la geometría, que es otra cosa. Contesta «¿cuánto cambia la etiqueta si uno mueve las
posiciones lo mismo que MxD03, pero sin información?». El probe guarda el tamaño pedido y el aplicado,
y el evaluador da INVALIDO si difieren en más de 10 m.

Por gránulo y brazo se guarda además lo que el verificador de la 1.17 pidió para cerrar su punto 1:
`triggered_test1`, `test1_k_observed`, `hotspot_dist_km` (después de `store`), `discarded_reason`,
`vrp_vent_mw`, `diag_a46_relabel`, la fuente del hotspot final y los píxeles del cúmulo.

## Población y muestra

**La misma de la 1.17, sin tocar:** `experiments/_s151_mxd03_etiquetas/poblacion.json` (sha256 con
fin de línea LF `89a526cc...`, fijado por `test_la_muestra_es_la_de_la_117_sin_tocar`), 5.395 gránulos
MODIS de los 11 Tier A entre el 2026-03-01 y el 2026-10-12, 471 en la muestra, 12 jobs, las 88 pasadas
con alerta de MIROVA en censo (46 protegidas, lectura A). Así los brazos C y M de la 1.21 se pueden
comparar con los de la 1.17 gránulo por gránulo.

`predecir_etiqueta_cumulo.py` comprueba que la población se reproduce exacta con los records del
commit `bca47c6ad` (el de #835) y la referencia en los commits de Mirova-v1 que guarda
`poblacion.json`: en los 11 volcanes, las mismas N por estrato, 0 gránulos de la muestra con otra
etiqueta de MIROVA y 0 con otra publicación guardada (`predecir_etiqueta_cumulo_salida.txt`).

**Por qué no se re-estratifica.** Los estratos de la 1.17 se armaron con la distancia del hotspot final
al límite. Con la etiqueta del cúmulo lo que decide es la distancia del cúmulo, y con el modelo nuevo en
su peor caso **3.811 de 5.395 records** (70,6 %) tienen el cúmulo a menos de la banda del límite
(`cumulo_cerca_del_limite` en `prediccion_cumulo.json`). Una estratificación nueva no concentraría nada:
casi todo «puede moverse». Por eso el balance suma **todos** los estratos, y los estratos quedan sólo
como diseño muestral (cada celda volcán × estrato es un muestreo uniforme de sus gránulos).

**Gránulos que no existen en el archivo.** `comprobar_archivo.py` consultó CMR (público, sin
credenciales) por el L1B y el MxD03 Standard 6.1 de los 471 gránulos antes de correr, y dejó la lista
en `archivo_cmr.json`. Un gránulo de esa lista no cuenta como pedido. Cualquier otro que falte es
INCOMPLETO. El que la 1.17 no pudo bajar (Tupungatito `MOD021KM.A2026275.0225`, estrato A, negativo
limpio) no existe en CMR: el archivo salta del gránulo de las 02:05 al de las 02:45 de ese día.

## El modelo de corrimiento con los dos ejes

`_interp_geo` estira la grilla de 5 km con un `zoom` que alinea esquina con esquina, cuando los nodos
del L1B están en el frame 5k + 2 y en la línea 5k + 2 (#828). El corrimiento tiene así dos componentes
perpendiculares:

- **a lo ancho del barrido**, el de #828: el frame *s* recibe la posición del frame 0,99778·*s* + 2;
- **a lo largo de la traza**, el que faltaba: la línea *y* recibe la de la línea 0,998029·*y* + 2, o sea
  2 − 0,001971·*y* líneas (+2 al inicio del gránulo, 0 al medio, −2 al final). Una línea mide 1 km en
  nadir y R/H km a un ángulo con distancia oblicua R.

`modelo_corrimiento.py::corrimiento_predicho_traza` suma las dos en hipotenusa. Contra lo medido en la
1.17, con la línea del cráter que ese probe guardó (`validar_modelo_117.py`, salida en
`validar_modelo_117_salida.txt`):

| cenit | n | medido (mediana) | modelo de #828 | modelo nuevo | residuo mediano | r |
|---|---|---|---|---|---|---|
| 0 a 20° | 93 | 1,171 km | 0,421 | **1,275** | 0,043 | 0,981 |
| 20 a 35° | 85 | 1,450 | 0,482 | 1,702 | 0,093 | 0,939 |
| 35 a 50° | 68 | 2,314 | 2,088 | 2,664 | 0,356 | 0,907 |
| más de 50° | 224 | 4,554 | 4,683 | 5,182 | 0,894 | 0,926 |

El modelo nuevo predice el 1,1 a 1,3 km medido en cenit bajo, y los gránulos que exceden la banda
(predicho + 1 km) bajan de **87 a 4** de 470. A cenit alto sobreestima un poco, que es el lado seguro.
En la 1.21 el modelo **no decide qué entra al balance** (entra todo); se usa para la anotación de banda
y para el conteo de arriba. Un record guardado no trae la línea del cráter, así que para él se usa el
peor caso de la traza (2 líneas).

## Predicción pre-registrada (no decide)

Como el flag sólo cambia la etiqueta, el brazo CC se puede predecir **sin L1B** sobre la población
entera: `predecir_etiqueta_cumulo.py::replay_cumulo` aplica la regla de arriba a cada record guardado y
pasa los dos por el predicado del tablero con node (`prediccion_cumulo.json`). Es un modelo de la
cadena, no la cadena: el probe lo compara contra el CC medido (prueba del replay).

| grupo de la población | n | publica C (guardado) | publica CC (replay) | 0→1 | 1→0 |
|---|---|---|---|---|---|
| alertas protegidas | 46 | 9 | 46 (cota) | 37 | 0 (cota) |
| alertas bajo 1 MW | 42 | 2 | 40 | 38 | 0 |
| negativos limpios | 5.047 | 587 | **4.454** | 3.867 | 0 |
| de ellos, fuente `test1` (protegidas + bajo 1 MW + negativos) | 4 + 1 + 113 | 4 + 1 + 106 | sin predicción | | |

**En la fuente `test1` el replay da una cota, no una predicción.** Por la rama de arriba, CC puede
apagar ahí lo que C publica: de las 46 protegidas, CC publicaría **entre 42 y 46**, y las pérdidas van
**de 0 a 4**, así que CC y la principal **pueden salir PIERDE PROTEGIDA**. Pasa si, en la geometría de
C, el camino de erupción no tenía un cúmulo en el cráter; desde los records no se sabe. En los negativos
limpios, la misma rama puede apagar hasta 106. Δ predicho de CC contra C: **+3.829** errores contra
MIROVA, con la rama del Test 1 tomada a favor (una cota superior de lo que CC publica). Leído como geólogo: casi todas las escenas
MODIS de los 11 volcanes tienen un cúmulo pequeño con energía sobre el edificio (a 1 km el foco débil y
el gradiente topográfico se parecen, A69, A82). Sacar la etiqueta del cúmulo recupera las 46 alertas
protegidas (como cota), pero también publica 9 de cada 10 noches en que MIROVA miró y no vio nada. Es la cara
far→summit de A81 a escala de MODIS, y concuerda con lo que midió S150 en Nevados de Chillán (el brazo E
publicaba 22 de 28 negativos limpios en reposo). **Si el probe confirma esto, MC sale EMPEORA y el
arreglo no es adoptable en la réplica tal como está**, por el balance; y puede caer además por la
compuerta si la rama del Test 1 apaga alguna de las 4 protegidas de esa fuente.

Lo que el probe agrega sobre la predicción: (1) la regla 1 exacta con el código de hoy y el L1B, en los
cuatro brazos; (2) el efecto de la posición sobre las protegidas, contra su nulo; (3) la validación del
replay, que es la que permite usar la predicción para estudiar variantes (por ejemplo, un piso de
magnitud en el cúmulo) sin bajar L1B.

## Estimador

Para cada comparación X contra Y (lista abajo):

- **Regla 1, censo exacto.** De las 46 protegidas: cuántas publica Y, cuántas X, cuántas pasan de 1 a 0
  (perdidas) y de 0 a 1 (ganadas). Por volcán, satélite, cenit y tramo A119 en `cortes`.
- **Regla 2, balance.** Δ = (perdidas − ganadas en las alertas bajo 1 MW, censo exacto) + (publicaciones
  que X agrega menos las que quita en los negativos limpios, expandido por celda). Δ < 0 quiere decir
  que X se parece más a MIROVA. Cada celda (volcán × estrato de la 1.17) se estima con lo medido más
  (N − n) por la media medida. Su varianza es la de un valor en {−1, 0, +1} con las frecuencias de −1 y
  +1 suavizadas con medio conteo, para que una celda de 4 gránulos sin cambios no declare varianza cero.
  Las celdas medidas enteras entran exactas. Intervalo normal al 95 %. Los 12 negativos limpios del
  estrato «sin» (records sin distancias, fuera de los estratos desde la 1.17) no entran.
- **Por qué este intervalo y no otro: se midió su cobertura** (A110). `cobertura_estimador.py` toma diez
  escenarios donde el valor de cada gránulo de la población es conocido, repite 300 veces el muestreo
  con el mismo n por celda de la muestra real y cuenta cuántas veces el intervalo contiene el total
  verdadero y cuántas decide el signo (`cobertura_estimador_salida.txt`). Con verdad negativa, «decide
  el signo» es la probabilidad de MEJORA; con positiva, la de EMPEORA.

| escenario | total verdadero | cobertura | ancho mediano | decide el signo |
|---|---|---|---|---|
| replay (efecto de la etiqueta) | +3.867 | 0,997 | 1.077 | 1,000 |
| nulo | 0 | 1,000 | 789 | 1,000 |
| raro (2 % de 0→1 y 2 % de 1→0 al azar) | +28 | 1,000 | 836 | 0,000 |
| A_solo (30 % de 0→1 sólo en el estrato A) | +155 | 1,000 | 791 | 0,000 |
| mezcla (replay más 5 % de 1→0) | +3.431 | 0,993 | 1.165 | 1,000 |
| apaga 50 % de las publicaciones de C en negativos limpios | −290 | 1,000 | 833 | 0,050 |
| apaga 70 % | −410 | 1,000 | 843 | 0,463 |
| apaga 90 % | −540 | 1,000 | 850 | 0,917 |
| enciende 5 % de los negativos limpios que C no publica | +223 | 1,000 | 838 | 0,020 |
| enciende 10 % | +414 | 1,000 | 881 | 0,393 |

  La cobertura casi siempre de 1,000 contra un nominal de 95 % quiere decir que el intervalo es
  **conservador**: el ancho bajo el nulo (±394,4) lo fija el medio conteo de suavizado en las 32 celdas
  de 2 a 6 gránulos, no los datos.

  Una posterior de Dirichlet de Jeffreys por celda, la primera versión, **cubrió 0 de 300 veces** el
  efecto grande: con 2 a 6 gránulos en 32 de las 37 celdas que se expanden, el medio conteo arrastra la
  media hacia un tercio y el sesgo se suma en el mismo sentido en todas ellas. Por eso se descartó. El
  intervalo de Wilson sumado por celda de la 1.17 cubre siempre, pero es tan ancho (4.484 bajo el nulo)
  que **no decide el signo ni del efecto grande** (0,003); se informa al lado.
- **Control del estimador con respuesta conocida.** Con los valores del replay en los 471 gránulos de la
  muestra, el intervalo es [+3.199,6; +4.273,3] y contiene el +3.867 del censo
  (`test_control_del_estimador_con_respuesta_conocida`).
- **Poder, dicho antes de correr y en unidades del operador.** C publica 587 negativos limpios en la
  población, que son sus falsas alarmas MODIS del tramo. **MEJORA exige que el brazo apague unas 7 de
  cada 10 de esas falsas alarmas** sin perder alertas (con 7 de 10 sale MEJORA la mitad de las veces;
  con 9 de 10, 9 de cada 10 veces). Del otro lado, EMPEORA necesita unas 400 publicaciones de más
  (encender el 10 % de lo que C calla da EMPEORA 4 de cada 10 veces). Con una etiqueta que sólo agrega
  publicaciones, **en la principal MEJORA, y con ella «adoptable», es inalcanzable en la práctica**: lo
  que este probe puede entregar es EMPEORA, PIERDE PROTEGIDA o INDETERMINADO. La regla 1 es censo y no
  tiene este límite.
- **Lo que Δ no cuenta, por la letra de `docs/MISSION.md`.** Las protegidas **ganadas** (37 predichas en
  CC, como cota) no entran en Δ: la regla 1 sólo prohíbe perder, y la regla 2 es para alertas bajo 1 MW.
  Si Nicolás quiere que una protegida recuperada compense publicaciones de más, es una decisión suya y no
  está en este criterio. Y C es el código de hoy, no lo publicado: el evaluador informa aparte, en
  `deriva_protegidas`, las protegidas donde C no coincide con lo guardado.

## Comparaciones

| nombre | X contra Y | qué contesta |
|---|---|---|
| **principal** | MC contra C | el arreglo completo contra producción |
| etiqueta | CC contra C | la etiqueta sola |
| posicion_produccion | M contra C | la posición sola (repite la 1.17) |
| posicion_cumulo | MC contra CC | la posición con la etiqueta del cúmulo ya puesta |
| nulo_de_principal | RC contra C | lo mismo que la principal con un corrimiento al azar |
| nulo_de_posicion_produccion | R contra C | nulo de M contra C |
| nulo_de_posicion_cumulo | RC contra CC | nulo de MC contra CC |
| M_contra_ruido | M contra R | ¿MxD03 acerca más a MIROVA que un corrimiento al azar del mismo tamaño? |
| MC_contra_ruido | MC contra RC | lo mismo con la etiqueta del cúmulo |

## Estados y criterio (fijados antes de correr)

**Veredicto global**, en este orden:

1. **INVALIDO**: algún C' difiere de su C; un brazo vio el flag al revés o ningún brazo llamó a
   `derivar_distance_class`; o el ruido aplicado difiere del pedido en más de 10 m.
2. **INCOMPLETO**: los artefactos traen más de un commit o alguno no lo trae; falta la salida de un job
   pedido; **falta cualquier gránulo pedido** (los de
   `archivo_cmr.json` no son pedidos); los brazos no tienen la misma cantidad de gránulos medidos; o un
   job no corrió ningún C'. Se repite el job sobre el mismo código (A108). El evaluador cuenta los
   gránulos y los records por brazo **antes** de dar cualquier veredicto (`conteo_por_brazo`).
3. Si no, el veredicto de la **principal**.

**Veredicto de cada comparación**, en este orden:

1. **PIERDE PROTEGIDA**: al menos una protegida pasa de 1 a 0. Es la regla 1: no aceptable en la
   réplica.
2. **SIN CAMBIO OBSERVADO**: ningún gránulo cambia ni publicación ni etiqueta.
3. **MEJORA**: la cota superior de Δ queda bajo 0.
4. **EMPEORA**: la cota inferior de Δ queda sobre 0.
5. **INDETERMINADO**: en cualquier otro caso.

**Adoptable en la réplica** quiere decir una sola cosa: la principal sale MEJORA. SIN CAMBIO OBSERVADO e
INDETERMINADO no son adoptables. El cero de Δ no es un umbral elegido: es el punto en que X e Y cometen
los mismos errores contra MIROVA (A115, regla 4 de `docs/MISSION.md`).

Anotaciones que no cambian el veredicto:

- **FRÁGIL** (en principal, posicion_produccion y posicion_cumulo): su nulo pierde **la misma pasada**
  protegida (intersección de `perdidas_detalle`, listada en `fragil_pasadas`). Que el nulo pierda otra
  protegida no la vuelve frágil; esas quedan en `perdidas_que_el_nulo_no_pierde`. La pérdida sigue
  contando (la regla 1 mira lo que ve el operador), pero no es atribuible a MxD03: la publicación de esa
  pasada también se rompe con un sorteo de un corrimiento al azar del mismo tamaño en km (ver la
  anisotropía en Límites).
- **modelo_corto**: más de 10 % de los gránulos con el corrimiento medido sobre el predicho con su línea
  más 1 km.
- **prueba del replay**: acuerdo entre la publicación CC medida y la del replay, por grupo
  (protegidas, fuente `test1`, resto). Si el resto queda bajo 90 %, la predicción de arriba no se usa
  para estudiar variantes. El grupo `test1` se informa para medir el tamaño de la rama, no para juzgar al
  replay.
- **etiqueta con otro cúmulo**: gránulos donde el brazo se etiquetó con un cúmulo distinto del publicado.
- **deriva**: C contra lo guardado en `data/` (sólo etiqueta y publicación, como en la 1.17). El efecto
  se mide brazo contra brazo con el mismo código, así que la deriva no decide.
- **tipos de cambio** (la partición del verificador de la 1.17): cambia la fuente del hotspot final, el
  mismo píxel reubicado o otro píxel; y para el cúmulo: el mismo reubicado, otro, o aparece y
  desaparece.

Lo que cada resultado le diría a Nicolás:

| principal | lectura |
|---|---|
| MEJORA | MxD03 + etiqueta del cúmulo pasa las dos reglas: candidato a A45 |
| EMPEORA (lo predicho) | la etiqueta del cúmulo publica de más; el arreglo no entra así, y la pregunta pasa a ser qué filtro sobre el cúmulo (fuera de esta tarea) |
| PIERDE PROTEGIDA | la compuerta cae aun con la etiqueta del cúmulo; mirar `perdidas_detalle`, FRÁGIL y si son de la fuente `test1` (la etiqueta salió del cúmulo de erupción, no del publicado) |

En cualquiera de los casos vale la nota de la sección «La rama del Test 1»: con el flag encendido la
etiqueta de los records del Test 1 sale de un cúmulo distinto del que se publica.
| INDETERMINADO | el efecto es menor que lo que esta muestra puede resolver (unos 400 errores) |

## Prueba del instrumento

`probar_probe_cumulo.py` pasa escenas de 81 × 81 píxeles de 1 km por el pipeline real en los seis
brazos y C'. El workflow la corre antes de cada job y `tests/test_mxd03_cumulo_121.py` también.

| caso | escena | qué debe salir | qué sale |
|---|---|---|---|
| ETIQUETA | píxel de 285 K a 4 km del cráter (fuera del disco de 3 km del Test 1) y de 330 K a 15 km (dentro de la cerca de 25 km); sin corrimiento | C, M, R `far` / 0; CC, MC, RC `summit` / 1; espía `False` en C, M, R y `True` en CC, MC, RC | **así**: el mecanismo de las dos pérdidas de la 1.17 |
| TEST1 | disco de 5 píxeles a +1,0 K en el cráter (dispara el Test 1) y Salar de 330 K a 15 km | C, M, R `summit` / 1; CC, MC, RC `far` / 0; el espía de CC registra el cúmulo del Salar (~15 km) contra el guardado en el cráter | **así**: la rama que el replay no ve |
| POSICIÓN | foco de 335 K a 6 km al norte (inner 5), `_interp_geo` corrida 2 km al sur | C y CC publican, M y MC no; ruido de 2,000 km | **así** |
| AUSENTE | geolocalizaciones iguales | brazos de una misma etiqueta iguales; ruido 0 | **así** |
| RELLENO | como AUSENTE, MxD03 en NaN en una esquina | igual | **así** |

Además, `test_el_ruido_puede_cambiar_la_publicacion` es el control positivo del brazo R: con 2 km hacia
el norte el foco pasa de 4 a 6 km y se apaga; hacia el sur no. Cada estado del evaluador tiene un test
que lo produce y un control que no (A116), incluidos MEJORA y EMPEORA con la población real.

## Tiempo y cómo correrlo

- **Tiempo por job.** La 1.17 tardó 3,8 a 7,8 min por job (7,9 a 10,4 s por gránulo) con dos brazos. Con seis
  brazos se estima **10 a 25 min por job**. El script deja de bajar gránulos a los 70 min (los marca
  `sin_tiempo`) y el job tiene `timeout-minutes: 95` (70 × 1,3 = 91, más la instalación, A15). Con
  `max-parallel: 4`, los 12 jobs toman 3 rondas: **30 min a 1,5 h de reloj**. SIN VERIFICAR hasta
  correr: ningún brazo extra se cronometró sobre un L1B real.
- **Disco del runner.** Igual que la 1.17: cada par pesa 100 a 150 MB y se borra apenas se usa.

Primero **un job suelto para cronometrar** (uno de los más cargados: 48 gránulos del censo de Láscar), y
sólo si termina bajo los 70 min, los otros 11. **Los dos despachos tienen que correr sobre el mismo
commit**: se fija un tag sobre el commit de `main` después del merge y los dos se despachan desde ese
tag, que se anota en la bitácora del loop junto con los dos run id.

```
git tag s151-1.21-probe <commit de main tras el merge> && git push origin s151-1.21-probe
gh workflow run probe-s151-mxd03-cumulo-121.yml --ref s151-1.21-probe -f preregistro_aprobado=si -f jobs='["Lascar-2"]'
gh workflow run probe-s151-mxd03-cumulo-121.yml --ref s151-1.21-probe -f preregistro_aprobado=si \
  -f jobs='["Lascar-1","Lastarria","Isluga","Tupungatito","PlanchonPeteroa","NevadosDeChillan","Llaima","Villarrica","Copahue","PuyehueCordonCaulle","Chaiten"]'
```

Cada JSON de job guarda `commit` (`GITHUB_SHA`) y `ref` (`GITHUB_REF`), y el evaluador da **INCOMPLETO**
si los artefactos traen más de un commit o alguno no lo trae (`commits` en el resumen): un veredicto que
mezcle dos pipelines no se da (A108). El tag sólo hace que eso no pase; el evaluador es el que lo
comprueba.

El evaluador de cada despacho saldrá INCOMPLETO porque sólo ve sus propios jobs; el veredicto se saca en
local con los 12 artefactos juntos (`python evaluar_cumulo.py <carpeta>`).

Sólo con el criterio sellado y el PR mergeado: `workflow_dispatch` no corre desde una rama. Para
repetir jobs sueltos, `-f jobs='["Lascar-2"]'` y evaluar en local con todos los artefactos juntos:
`python evaluar_cumulo.py <carpeta>`.

- **Autenticación:** sólo `EARTHDATA_TOKEN` (el bloque de `nrt.yml`); el job `plan` y cada job del probe
  fallan al instante si viene vacío (A71).
- **Concurrencia:** grupo propio `probe-s151-mxd03-cumulo-121`, que no desplaza a `s146-ab-sin-test1`
  ni a `s151-ab-diurno`; `max-parallel: 4` para no cargar LAADS.
- **Salida:** no hace push. Un artefacto por job (`s151-mxd03-cumulo-<job>`) y el resumen
  (`s151-mxd03-cumulo-121-resumen`).

## Archivos

| archivo | qué es |
|---|---|
| `probe_cumulo.py` | el probe (seis brazos, espía del flag, ruido) |
| `evaluar_cumulo.py` | el criterio de arriba |
| `probar_probe_cumulo.py` | la prueba sintética |
| `modelo_corrimiento.py` | el modelo con los dos ejes |
| `validar_modelo_117.py`, `validar_modelo_117_salida.txt` | el modelo contra la 1.17 |
| `predecir_etiqueta_cumulo.py`, `prediccion_cumulo.json`, `predecir_etiqueta_cumulo_salida.txt` | la predicción y la reproducción de la población |
| `cobertura_estimador.py`, `cobertura_estimador_salida.txt` | la cobertura medida del intervalo |
| `comprobar_archivo.py`, `archivo_cmr.json`, `comprobar_archivo_salida.txt` | los gránulos que no existen en CMR |

## Límites conocidos

- El replay es un modelo de la cadena de etiquetas, no la cadena; su acuerdo se mide en la corrida.
- C corre el código de hoy, no el que produjo cada record (la 1.17 midió que los píxeles anómalos
  difieren en 248 de 470). El efecto se mide brazo contra brazo con el mismo código.
- **El nulo es anisótropo sobre 50° de cenit, y no se corrigió.** R reproduce el tamaño del corrimiento
  en km, pero lo que mueve la etiqueta es el corrimiento en píxeles, y el píxel MODIS es más ancho a lo
  ancho del barrido. El verificador midió sobre los 470 gránulos de la 1.17 (su `anisotropia.py`): bajo
  35° el rumbo al azar y el real valen lo mismo en píxeles (razón 1,00 y 0,97); sobre 50° (224 gránulos)
  el real va 91 % por el eje del barrido y el rumbo al azar es **24 % más grande en píxeles** (mediana
  1,24). El nulo perturba ahí más que MxD03, así que **sesga FRÁGIL y `M_contra_ruido` a favor de
  MxD03** en la mitad de cenit alto de la muestra. Las dos pérdidas de la 1.17 son de cenit bajo (15,6° y
  17,4°), donde el nulo sí es comparable. No se corrigió porque sortear el rumbo en píxeles exige la
  dirección del barrido en el cráter de cada gránulo real, que la prueba sintética no puede ejercitar
  (sus escenas no traen ángulos): un arreglo que sólo corre sobre el L1B quedaría sin control antes del
  sello. Al leer el resultado, FRÁGIL y `M_contra_ruido` se leen por separado bajo y sobre 50°
  (`cortes`, bin de cenit).
- Que el Test 1 deje de disparar por la posición en las dos pérdidas de la 1.17 sigue SIN VERIFICAR
  hasta esta corrida (ahora se guarda `triggered_test1` por brazo).
- Que MIROVA use MxD03 sigue SIN VERIFICAR (SP426.5 p. 3 habla de «pixel(s) geolocation» sin nombrar el
  producto).
