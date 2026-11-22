# Pre-registro de la zona A del laboratorio (MEJ-5): criterio sellado (S194, paso 2 del plan S190)

> **Qué es.** El criterio con que se va a juzgar la zona A del perfil `laboratorio`, escrito y commiteado **antes**
> de que exista un solo record del laboratorio (el paso 4 del plan todavía no corre). Lleva los valores que aprobó
> Nicolás el 2026-11-17 (D5 de `docs/PLAN_EXPERIMENTAL_S190.md` §8): tasa objetivo de 30 % por pasada en negativos
> limpios, CUMPLE con exceso NHI de p < 0,05 en al menos 4 de los 9 volcanes con serie NHI (sin Cordón Caulle),
> control con las fechas NHI corridas 15 días, persistencia sobre el sorteo, SIN PODER bajo 10 noches pareadas.
> No cambia ningún valor que él aprobó; lo que el crítico encontró que podría obligar a cambiarlos va como pregunta
> (§8).
>
> **Sello.** El evaluador es `experiments/_s194_lab_zona_a/evaluar.py`,
> sha256 del evaluador (fin de línea LF): `e0d19ae34188735a1bc468aae3bc887ff9f495eab985a95a68f4911f38cfd74b`.
> La prueba `tests/test_lab_zona_a_preregistro_s194.py::test_sello_hash_del_evaluador_en_el_preregistro` compara ese
> hash con el archivo: editar el evaluador sin re-sellar este documento deja el CI en rojo. Base: `origin/main` en
> `1c6ac41e1` (2026-11-22). Sin cambio de la lógica de detección ni de ningún valor publicado: no toca `pipeline/`,
> perfiles, workflows ni tablero.

## 1. Qué se pregunta, en una frase

Si el laboratorio baja la línea de detección sólo en el cráter (zona A, círculo de `inner_radius_km` alrededor del
ancla), ¿las noches en que **sólo el laboratorio** publica son noches en que el SWIR de alta resolución (NHI de
Sentinel 2 y Landsat) ve calor más a menudo que en las noches en que **nadie** publica, y lo que aparece de más se
repite en el mismo lugar más de lo que daría el azar? MIROVA no sirve de vara (A115): lo que agregamos es, por
definición, lo que MIROVA no publica.

El nulo es alto y ya está medido: S131 encontró en 4 de 5 volcanes la misma tasa de alerta NHI en noches con
detección propia que la basal (20 a 49 %). Por eso la prueba no compara contra cero sino contra las noches «ninguno
publica» del mismo volcán.

## 2. Datos y ventanas

| qué | fuente | ventana |
|---|---|---|
| records del laboratorio | `data/laboratorio_v1/<Volcan>.json` (paso 4; hoy no existe) | 2026-02-15 al último día disponible |
| records de producción | `data/mirova_equivalent/<Volcan>.json` | la misma |
| NHI | `https://raw.githubusercontent.com/MendozaVolcanic/NHI-v1/main/docs/nhi_data/<Carpeta>/nhi_timeseries.json` (campos `fecha`, `alerta`, `cloud_cover`, `sensor`); carpetas `Planchon-Peteroa` y `Nevados de Chillan` | la misma |
| referencia MIROVA (sólo calibración) | `registro_vrp_consolidado.csv` y `registro_vrp_ocr.csv` de Mirova-v1, bajados frescos (`referencia_mirova_unificada.bajar_remoto`) | **2026-03-01** al último día (A119; pregunta 2) |

Volcanes: los 9 con serie NHI (Láscar, Isluga, Tupungatito, Planchón-Peteroa, Nevados de Chillán, Llaima,
Villarrica, Copahue, Chaitén). Cordón Caulle fuera (D6). Lastarria no tiene serie NHI (404 en NHI-v1): no vota en NHI,
pero sí entra a la calibración y a la persistencia, que no necesitan NHI.

## 3. Definiciones operables

**3.1 Pasada, noche, publica.** Una pasada es un record nocturno (se descartan las diurnas con
`banco_paridad.es_pasada_diurna_descartada`, la misma regla del banco y del auto-audit). La **noche** de una pasada es
su fecha UTC (convención del banco: las pasadas nocturnas de Chile caen después de las 00 UTC). **Publica** es el
predicado del tablero **ejecutado con node** sobre `frontend/index.html` (`banco_paridad.correr_node`: cumbre, válida,
no artefacto y valor mostrado > 0); nunca un port. Como exige cumbre, «publica» ya es «publica en la zona A». Una
**escena inválida** (`diag_codigo_mirova.motivo_vacio`, la vía no pudo medir) no publica y no cuenta como pasada
observada.

**3.2 Clases de noche.** Para cada volcán y noche se parean las pasadas del laboratorio y de producción por sensor a
±120 s (`clase_mirova.VENTANA_S`). La noche tiene **cobertura igual** si toda pasada de un perfil tiene par en el
otro y la escena es inválida en los dos o en ninguno. Con cobertura igual y al menos una pasada válida, la noche es
**S** (sólo laboratorio publica), **N** (ninguno), **A** (ambos) o **P** (sólo producción), mirando si alguna pasada
válida publica en cada perfil. Una noche con cobertura desigual o sin pasadas válidas no tiene clase.

**3.3 Negativo limpio** (sólo calibración, §5): el del banco de paridad (`banco_paridad.etiquetar`, `neg_limpio`):
fila RUTINA del consolidado con VRP 0 a ±120 s de la pasada, sin ALERTA ni FALSO_POSITIVO de MIROVA esa noche y
sensor, regla de mínimas SN (D-9), escenas inválidas excluidas.

**3.4 Pareo de una escena NHI con una noche.** NHI no trae hora, sólo fecha, y es diurno (~14 a 15 UTC en Chile).
La escena del día D se parea con la noche D (la que termina unas horas antes de la escena); si D no tiene clase, con
D+1; si tampoco, con D-1 (tolerancia ±1 día). La primera noche con clase **consume** la escena aunque sea A o P: la
escena no salta a la noche vecina porque la suya tuvo otra clase. Varias escenas en la misma noche forman una sola
unidad: alerta si alguna alerta, nubosidad la menor (la vista más limpia). Entran a la prueba sólo las unidades S y N.
Una escena con `alerta` nula no entra.

**3.5 Estadístico.** Por volcán: exceso = (alertas NHI / unidades) en S menos lo mismo en N. Prueba de permutación de
una cola (exceso positivo), **dentro del volcán y dentro de cada estrato de nubosidad de la escena** (≤20 %, 20 a
50 %, >50 %; `cloud_cover` en %; sin dato va al estrato más nublado): se barajan las etiquetas S/N dentro de cada
estrato. 10.000 permutaciones, semilla 194, p = (1 + #{T* ≥ T}) / (1 + 10.000). La estratificación es la respuesta a
la debilidad 2; sigue siendo una permutación dentro del volcán, como aprobó D5.

**3.6 Voto de cada volcán.** **SIN PODER** si tiene menos de 10 unidades S **o** menos de 10 unidades N (D5 dice
«menos de 10 escenas pareadas»; se exige en los dos grupos porque una tasa basal con menos de 10 noches no es una
vara). Con poder: **exceso** si el exceso es positivo y p < 0,05; si no, **sin exceso**.

**3.7 Control con las fechas corridas.** Se repite 3.4 a 3.6 con todas las fechas NHI corridas **+15 días** y, por
separado, **-15 días**. El control es **nulo** si en cada uno de los dos desplazamientos a lo más **1** volcán da
exceso. Bajo el nulo, la probabilidad de que 2 o más de 9 den p < 0,05 por azar es a lo más 0,0712 por
desplazamiento (`salida_poder.txt`).

**3.8 Persistencia.** Una **detección extra** es una pasada válida que el laboratorio publica y producción no, en una
noche con cobertura igual, en los 10 volcanes de la zona A. Es **persistente** si está a ≤1 km (haversine, posición
`final_hotspot_lat/lon`) de alguna pasada publicada del laboratorio de las **3 noches previas** del mismo volcán. Se
compara la fracción persistente observada con la de 2.000 sorteos en que la posición de cada extra se reemplaza por
un punto uniforme (por área) en el disco de la zona A de su volcán (ancla `pipeline.geo_utils.get_detection_anchor`,
radio `inner_radius_km`), dejando reales las detecciones previas. **Supera** si p = (1 + #{f* ≥ f}) / 2.001 < 0,05 y
hay al menos 10 extras. Se informa además, **sin voto**, un sorteo temporal (la posición de cada extra se reemplaza
por la de una detección publicada del laboratorio del mismo volcán en una noche a más de 6 días; debilidad 5).

**3.9 Instrumento.** Si en algún volcán más del 5 % de las noches tiene cobertura desigual entre perfiles, el
veredicto es INVALIDO: un hueco de un lado fabrica noches S o N (lección de `scripts/evaluador_comun.py`, T1).

## 4. Veredicto y qué hace cada resultado

Se evalúa en este orden (`evaluar.veredicto`):

1. **INVALIDO POR INSTRUMENTO** si falla 3.9 o si el control de 3.7 no es nulo. Qué se hace: se arregla el
   instrumento (cobertura, carga) y se vuelve a correr el mismo criterio. Si lo que falla es el control, **no** se
   reformula el criterio sin un pre-registro nuevo, porque un control que salta con datos reales puede ser
   estacionalidad o un episodio de semanas (debilidad 4) y eso se decide antes de mirar otra vez.
2. **SIN PODER** si menos de 4 volcanes tienen poder (con menos de 4 votantes no se puede llegar a 4). Qué se hace:
   se espera más datos y se re-evalúa **con este mismo criterio** a lo más dos veces más, la primera no antes del
   2027-02-21 (tres meses más de NHI); cada corrida se informa, ninguna se descarta.
3. **CUMPLE** si al menos 4 volcanes dan exceso y la persistencia supera al sorteo. Qué se hace: paso 6 del plan
   (cron por tandas, vista de tres estados en la pestaña Laboratorio, fila de la ficha SDA), con el merge de Nicolás.
4. **SIN PODER** si al menos 4 dan exceso pero hay menos de 10 extras para la persistencia (no puede ocurrir con 4
   volcanes de 10 noches S cada uno, pero la regla queda escrita).
5. **NO CUMPLE** en cualquier otro caso. Qué se hace: la zona A no llega a cron; se anota en
   `docs/BEYOND_MIROVA_EXTENSIONS.md` §12 (MEJ-5) con los números y el exceso mínimo detectable de cada volcán, porque
   NO CUMPLE con poco poder no es «no hay señal» (debilidad 3). No se re-corre con otro umbral, otra ventana u otro
   estrato sin un pre-registro nuevo que diga que es el segundo intento.

Bajo el nulo (ningún volcán con señal), la probabilidad de que 4 o más de 9 den p < 0,05 por azar es a lo más
0,00064 (`salida_poder.txt`): el criterio es conservador a propósito.

## 5. Paso 3: barrido y regla para elegir el valor de la zona A

El parámetro es el multiplicador de sigma del criterio contextual nocturno en la zona A (`laboratorio_zona_a.valor`;
nota del paso 1). Menor valor, más alertas; el guard S147 vigila que no pase del s2 nocturno de producción (5).

- **Brazos:** s = 5,0 (producción: control), 4,5, 4,0, 3,5, 3,0, 2,5, 2,0, 1,5 y 1,0. Cada brazo es el perfil
  `laboratorio` con la zona encendida y ese valor, en su propia carpeta, sobre la ventana de calibración.
- **Medida:** con `evaluar.py calibrar`, por brazo y por sensor, la tasa de publicación por pasada sobre negativos
  limpios (3.3) de los 10 volcanes de la zona A; también la tasa por noche de volcán (tres sensores juntos), que se
  informa y no decide mientras `UNIDAD_TASA = "pasada"` (pregunta 1).
- **Controles:** el brazo 5,0 tiene que dar exactamente las cuentas de producción (si no, la implementación cambia
  algo más que el multiplicador: geometría, fondo o ancla, S147 §5; INVALIDO). La tasa no puede bajar al bajar s
  (INVALIDO). Cada sensor necesita al menos 30 negativos limpios por brazo (si no, SIN PODER).
- **Regla:** el valor es el **menor s** de la grilla cuya tasa por pasada no supera 30 % en **ninguno** de los tres
  sensores (la comparación es entera, 10·publicadas ≤ 3·negativos, así que 30 % exacto cumple). Si producción ya
  supera 30 % en algún sensor: SIN VALOR, a Nicolás. Si cumple hasta el piso (1,0), se elige 1,0 y el estado lo dice
  («el piso de la grilla»), para que nadie lea el piso como una calibración. Si ya 4,5 supera: SIN EXTENSION.

## 6. Lo que se puede medir hoy, sin el laboratorio

`experiments/_s194_lab_zona_a/medir_base.py` (salida `salida_medir_base.txt` y `.json`) mide sobre producción y NHI,
sin mirar al laboratorio, y `evaluar.py poder` (salida `salida_poder.txt`) da el exceso mínimo detectable:

- Producción en negativos limpios (2026-03-01 a 2026-11-21, 10 volcanes de la zona A): 0,57 % de las pasadas y
  3,15 % de las noches de volcán publican; la noche negativa tiene una mediana de 6 pasadas negativas limpias (q1 4,
  q3 8). Por sensor, la mediana es 2 en MODIS y 3 en cada VIIRS.
- NHI desde 2026-02-15: de 74 escenas (Chaitén) a 132 (Tupungatito) por volcán; tasa basal de alerta de 0,068
  (Tupungatito) a 0,351 (Llaima).
- Las unidades S y N salen sólo de noches en que producción no publica. Escenas pareadas con esas noches hoy: Isluga
  16, Láscar 23, Chaitén 46, Tupungatito 53, Planchón-Peteroa 56, Villarrica 76, Nevados de Chillán 79, Llaima 94,
  Copahue 123.
- Humo de identidad (`salida_humo_identidad.txt`): el evaluador corrido con laboratorio = producción sobre los datos
  reales da 0 noches S y 0 noches P, 0 noches con cobertura desigual, todos los volcanes SIN PODER y 0 extras, que es
  lo que tiene que dar.

## 7. El crítico despiadado: cinco debilidades y qué hice con cada una

**Debilidad 1. Una tasa de 30 % por pasada probablemente satura la noche y deja la prueba SIN PODER.** Evidencia
(`salida_medir_base.txt`): la noche negativa limpia tiene una mediana de 6 pasadas negativas entre los tres sensores,
y en producción la tasa por noche (3,15 %) ya es 5,5 veces la tasa por pasada (0,57 %). Si las pasadas de una noche
fueran independientes, 30 % por pasada daría 88 % de las noches (SOSPECHA: no son independientes, una fuente real se
repite en las pasadas de la misma noche, así que la cifra real queda entre 30 y 88 %). La prueba NHI necesita al
menos 10 noches N, y las noches S y N salen sólo de las noches en que producción no publica (Isluga 16, Láscar 23):
con la noche saturada, N se queda sin noches. **Qué hice:** no cambié el 30 % ni su unidad. Dejé implementada y
probada, pero apagada, la unidad «noche» (`UNIDAD_TASA`; la tasa por noche de volcán con los tres sensores juntos),
el barrido informa las dos, y lo llevo como **pregunta 1**. Elegir la unidad después del barrido y antes de medir NHI
no mira el resultado: el barrido no toca NHI.

**Debilidad 2. Las nubes pueden fabricar el exceso.** Mecanismo (SOSPECHA, sin medir): una noche nublada apaga
nuestra detección (la noche cae en N) y, si la nubosidad persiste a la tarde, apaga también la alerta NHI; las
noches N quedarían con menos alertas NHI por el tiempo, no por el volcán, y aparecería un exceso en S sin señal. El
control de 15 días no lo atrapa (el tiempo no se correlaciona a 15 días). Evidencia de que hay de dónde: `cloud_cover`
va de 0 a 81 % en las nueve series, y en Copahue 44 de 128 escenas están sobre 50 % (`salida_medir_base.txt`).
**Qué hice:** la permutación se estratifica por nubosidad de la escena dentro del volcán (3.5). La prueba
`test_permutacion_estratificada_neutraliza_la_nube` construye ese confusor: sin estratos da p < 0,01, con estratos
p > 0,2. Queda abierto (SOSPECHA): no verifiqué en el código de NHI-v1 si `cloud_cover` es del recuadro del volcán o
de toda la escena; si es de la escena, la estratificación corrige sólo en parte. Las escenas parecen cortadas en
~80 % (el máximo de cada serie está entre 30 y 81 %), lo que sugiere un filtro de NHI-v1, tampoco verificado.

**Debilidad 3. El poder es bajo: NO CUMPLE no va a querer decir «no hay señal».** Evidencia (`salida_poder.txt`):
con 10 noches S, 80 N y una basal de 0,35 (Láscar, Llaima, Villarrica están entre 0,29 y 0,35), hacen falta 7
alertas de 10 en S para p < 0,05; con basal 0,07 hacen falta 4 de 10. Isluga no puede votar con los datos de hoy (16
noches sin publicación de producción no alcanzan 10 + 10), y Láscar sólo si S queda entre 10 y 13. En la práctica
votan a lo más 8 volcanes y hacen falta 4. **Qué hice:** no cambié el 4 de 9 ni el 10 (son de Nicolás). El
evaluador informa por volcán n_S, n_N, alertas y p, y la regla de NO CUMPLE (§4) exige publicar el exceso mínimo
detectable de cada volcán junto al veredicto. Además, SIN PODER tiene re-evaluaciones acotadas (§4) para que esperar
datos no se convierta en repetir hasta que salga.

**Debilidad 4. El control de 15 días puede saltar por razones buenas o por azar.** Por azar: con 9 volcanes, 2 o más
con p < 0,05 ocurre a lo más 7,1 % de las veces por desplazamiento (`salida_poder.txt`), y hay dos desplazamientos.
Por razones buenas (SOSPECHA): un episodio de actividad que dura semanas (Villarrica y Llaima tienen basales NHI de
0,29 y 0,35) sigue presente 15 días después, y el control corrido lo ve: un efecto real se leería como «el
instrumento mide estacionalidad». **Qué hice:** el umbral del control (a lo más 1 volcán por desplazamiento) se fijó
para que la falsa alarma por azar quede bajo 7,1 % por desplazamiento; corrí el control en los dos sentidos (+15 y
-15) para que un ciclo no se esconda en uno; y su falla da INVALIDO, no NO CUMPLE, con el resultado por volcán de
cada desplazamiento en la salida. La prueba `test_senal_estacional_hace_saltar_el_control` muestra que una estación
de 60 días produce exceso en 4 o más volcanes y el control lo atrapa. Cómo distinguir episodio de estacionalidad queda
para un pre-registro nuevo si llega a pasar.

**Debilidad 5. El sorteo uniforme en la zona A es un nulo débil para la persistencia.** Evidencia: (a) un píxel tibio
fijo (un lago, un campo fumarólico, el borde de un glaciar, el gradiente topográfico de A69) «persiste» igual que una
fuente volcánica: en la prueba `test_persistencia_fija_supera_y_azar_no`, una posición fija hace persistentes más de la
mitad de las extras y supera al sorteo; (b) la ROI de detección de la vía no es el círculo de la zona A: en MODIS
es la caja de 5 × 5 celdas al centro (CLAUDE.md, «Reglas geométricas»), unos 2,5 km a cada lado, y el sorteo reparte
puntos hasta 5 km o más, donde la vía nunca podría detectar; eso infla el contraste a favor de lo observado.
**Qué hice:** mantuve la persistencia aprobada (sorteo uniforme) porque es la de D5, y agregué, **sin voto**, el
sorteo temporal (3.8), que respeta por construcción la ROI real y la cuantización de la grilla porque usa posiciones
que el propio laboratorio publicó. Ni uno ni otro separan un artefacto fijo de una fuente fija: eso lo hace NHI, que
es donde descansa el veredicto. Va como **pregunta 3**.

## 8. Preguntas para Nicolás (no cambian nada hasta que responda)

1. **¿La tasa objetivo de 30 % se mide por pasada (lo aprobado) o por noche de volcán?** Por la debilidad 1, con 30 %
   por pasada lo más probable es SIN PODER. Recomiendo **por noche** (la unidad del operador, A94). Si dice que sí, se
   cambia `UNIDAD_TASA` a `"noche"` y se re-sella (hash nuevo) antes de medir NHI.
2. **¿La calibración arranca el 2026-03-01 (A119: la tabla de MIROVA es sana desde marzo) en vez del 2026-02-15?**
   La medición contra NHI queda en 2026-02-15, como se aprobó; sólo la calibración, que depende de la tabla, se
   corre desde marzo. Recomiendo **sí** (es lo sellado); si prefiere 2026-02-15, se re-sella.
3. **¿El sorteo temporal de la persistencia debe votar en vez del uniforme?** Por la debilidad 5. Recomiendo **sí**.
   Hoy vota el uniforme (lo aprobado) y el temporal sólo se informa.

## 9. Cómo se probó el instrumento antes de tener datos

- `tests/test_lab_zona_a_preregistro_s194.py` (en CI): con datos sintéticos de verdad conocida el evaluador da CUMPLE,
  NO CUMPLE (sin señal; señal sin persistencia; 3 de 9), SIN PODER (8 noches S) e INVALIDO (cobertura desigual;
  señal estacional que el control atrapa); el control cae a nulo cuando la señal es de la noche misma; la
  estratificación neutraliza el confusor de nubes; la regla del barrido se prueba en sus bordes (30 % exacto, un
  sensor sobre la tasa, no monótona, piso, producción sobre la tasa, brazo faltante, control del brazo 5,0); la
  tabla de poder; y tres pruebas de sello (valores, hash del evaluador, la grilla parte del s2 leído del código).
- `experiments/_s194_lab_zona_a/mutar.py` (salida `resultado_mutaciones.json`): 22 mutaciones del criterio sobre
  copias del evaluador, corridas sin las pruebas de sello. Cuenta como atrapada sólo si alguna prueba falla por
  aserción y ninguna da error (una mutación que hace caer la prueba no está atrapada, lección S152). El control sin
  mutar pasa entero.
- Humo de identidad sobre los datos reales (§6).

## 10. Archivos

| archivo | qué es |
|---|---|
| `experiments/_s194_lab_zona_a/PREREGISTRO.md` | este documento |
| `experiments/_s194_lab_zona_a/evaluar.py` | evaluador sellado (`evaluar`, `calibrar`, `poder`) |
| `experiments/_s194_lab_zona_a/medir_base.py` | línea base de §6 (producción y NHI, sin laboratorio) |
| `experiments/_s194_lab_zona_a/mutar.py` | control de mutaciones |
| `experiments/_s194_lab_zona_a/salida_*.txt`, `resultado_mutaciones.json` | salidas de los tres scripts y del humo |
| `tests/test_lab_zona_a_preregistro_s194.py` | pruebas del evaluador |
