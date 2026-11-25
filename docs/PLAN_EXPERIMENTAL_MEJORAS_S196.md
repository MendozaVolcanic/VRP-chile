# Plan de mejoras del perfil experimental, una por una (S196)

> **Qué es.** Un plan para cada mejora del laboratorio que no tenía plan escrito. Pedido de Nicolás del 2026-11-23:
> «debemos tener planes para el experimental»; aprobó escribir un documento de planificación con todos los huecos. No
> enciende nada ni toca `pipeline/`, perfiles ni workflows. Las decisiones que sólo puede tomar Nicolás están en el
> §14. El ítem P0 (§2b), pedido por Nicolás el mismo día, va primero.
>
> **Base.** `origin/main` en `34d87cdc7` (2026-11-23 14:22 UTC). NHI-v1 al commit `4d24515abe1e` (el mismo del
> re-sello S196 del control diurno). Todo número sale de un script de `experiments/_s196_plan_mejoras/` (cada uno con su
> salida al lado) o de un archivo citado al lado; ninguno se transcribió a mano (S91).
>
> **Cómo encaja.** El plan del laboratorio es `docs/PLAN_EXPERIMENTAL_S190.md` (pasos 0 a 6). Su primera extensión,
> MEJ-5 (zona A del cráter), ya tiene plan, dos pre-registros (`experiments/_s194_lab_zona_a/`,
> `experiments/_s196_lab_piso/`) y código apagado (#1096, #1102), y está en el paso 3. Este documento cubre las demás:
> las filas MEJ-2, MEJ-3, MEJ-4, MEJ-6, MEJ-7 y MEJ-8 de `docs/BEYOND_MIROVA_EXTENSIONS.md` §12, las candidatas del §6
> del plan por sensor (`docs/superpowers/specs/2026-10-24-programa-replica-por-sensor.md`), la vara de Lastarria y el
> retiro de la sombra C0.

## 0. Lo que cambiaron las mediciones previas (leer primero)

Cinco de las diez mejoras del encargo llegaron con una premisa que los datos de hoy ya no sostienen. Lo digo antes del
plan porque cambia el orden.

1. **MEJ-7 (el foco MODIS de Láscar) ya lo publica producción.** El caso que le dio origen, Láscar 2026-05-11 07:55
   UTC, está en el tablero: 0,21 MW, 1 píxel, a 0,26 km del cráter. En toda la ventana 2026-03-01 a 2026-11-22 la vía
   publica 6 de las 5.758 pasadas MODIS que la tabla de MIROVA lista como RUTINA y que tienen record nuestro (4 de
   Láscar). No es una mejora pendiente del laboratorio: es una sobre-publicación chica de la réplica
   (`salida_m7_modis_sobre_rutina.txt`).
2. **La máscara de agua (MEJ-8) no cambia nada de lo que se publica hoy en los 11 Tier A.** 0 de las 3.013 pasadas
   publicadas desde marzo tienen un alertado sobre agua en ninguna parte de la grilla; el mismo conteo de presencia
   encuentra 6 records no publicados con agua en los Tier A (Láscar, Villarrica y Chaitén, 2 cada uno) y 17 de 57 en
   Laguna del Maule, así que el cero no es ceguera del instrumento (`salida_m8b_agua_en_publicadas_tier_a.txt`; la
   primera versión del script sumaba una potencia por píxel que la vía no guarda y daba cero por construcción, lo cazó el
   verificador). Lo que no está medido es la potencia sobre agua. Todo su efecto visible está en los 34, sobre todo en
   Laguna del Maule.
3. **El VIIRS 750 calla las cumbres tibias por dilución, no por la caja.** De 1.668 pasadas en que el 375 publica la
   cumbre y su par 750 del mismo satélite no, el 750 no marcó ni un píxel en 1.663 (`salida_m4_par_750_de_solo375.txt`).
   En Tupungatito el 375 publica a 0,15 km del cráter, que está dentro de la caja sensible `sens` del 750.
4. **La vía no ancla la grilla al cráter.** La fila MEJ-4 decía «nosotros anclamos al cráter (A63)». Eso valía para K;
   la vía centra la grilla en el punto de MIROVA (`pipeline/grillas_mirova.yaml`) y mide la distancia desde el cráter.
   En MODIS, donde la caja deja el cráter afuera (Tupungatito, Cordón Caulle), el efecto no está medido: con focos de 0,1
   a 0,3 MW MODIS calla en todas las cajas (`salida_m4b_modis_en_noches_375.txt`, sin poder), y con el 375 sobre 1 MW
   MODIS calla las 8 noches de Cordón Caulle, pero también las 4 de Villarrica, que tiene el cráter dentro de su caja,
   mientras publica 48 de 70 en Láscar y 32 de 42 en Chillán (`salida_m4c_disparador_mej4.txt`). Es sospechoso, no
   probado; P4 sube en el orden (§6).
5. **El fondo de producción ya es determinista (MEJ-2)** y **el escalón de MEJ-3 ya está acotado.** El port copia el
   desempate de MATLAB en `fillmissing2` (`pipeline/mirova_v750_codigo.py`, 166 de 166 VRP contra MATLAB); y del escalón
   de MIROVA sobre 50° de cenit se sabe cuándo actúa (casi nunca bajo 20 MW, en casi todo sobre 500 MW;
   `experiments/_s190_d36/INFORME.md` §2), no por qué, ni si el NRT de MIROVA lo mantiene (SIN DATO). Nuestros pares de
   Chile sobre 50° (razón 0,996, n 39) son todos del tramo donde el escalón casi no actúa: no tienen poder para verlo.

Y un hallazgo de método que vale para todas: **SWIR a ±1 día no separa noches de la misma época.** En la medición de
las cumbres 375 sin 750, la tasa de alerta NHI por clase de noche se separa casi igual con las fechas NHI corridas 15
días que sin correr (total de «sólo 375»: 84 de 529 contra 84 de 496 con el control; Láscar 9 de 26 contra 7 de 24;
`salida_m3_cumbre_375_sin_750.txt`). Lo que NHI mide a esa escala es el episodio (semanas de actividad), no la noche.
Todo criterio que use NHI noche a noche tiene que llevar ese control o compararse dentro del mismo episodio.

## 1. Reglas comunes a todos los planes

- **Dónde corre.** En el perfil `laboratorio` (`pipeline/profiles/laboratorio.yaml`, `data/laboratorio_v1/`), sobre
  la vía de producción, con **una extensión a la vez** (plan S190 §2, decisión D2 (a) de Nicolás). Hoy el laboratorio
  cubre los 11 Tier A; no hay laboratorio para los 34. Nada de esto entra a `mirova_equivalent`.
- **Identidad con producción.** Con la extensión apagada, el laboratorio tiene que dar records idénticos a producción
  (patrón de `experiments/_s194_lab_zona_a/salida_humo_identidad.txt` y `experiments/_s195_lab_paso3/identidad_antes_despues.py`),
  y el guard «difiere sólo en lo declarado» (`tests/test_laboratorio_paso1_s193.py`) tiene que listar la clave nueva.
  Si una extensión necesita código nuevo en la vía, entra detrás de un flag apagado que en `mirova_equivalent` no existe
  o vale `false`, con una prueba de identidad byte a byte de `data/mirova_equivalent/` antes y después.
- **Archivos de A45.** `pipeline/process_*.py`, `pipeline/store.py`, `pipeline/profiles/mirova_equivalent.yaml` y
  `pipeline/mirova_v750_codigo.py`: tag defensivo con push y sí explícito de Nicolás antes de tocarlos.
- **La vara nunca es MIROVA** (A115): SWIR de alta resolución (NHI-v1, Sentinel 2 MSI y Landsat 8/9 OLI), episodios del
  OVDAS (plantilla `docs/PLANTILLA_EPISODIOS_OVDAS_S190.md`, decisión D4 (a)), persistencia en el lugar, o un testigo
  físico independiente (otro sensor de la misma pasada). Con NHI, siempre el control de fechas corridas (§0) y el nulo
  por volcán de S131 (`docs/s131/agentes/OTRO_SENSOR.md`): un volcán con foco crónico «confirma» cualquier cosa por azar.
- **Pre-registro sellado antes de mirar** los datos de veredicto, con su control de instrumento (A110, A116).
- **Ventana.** Desde 2026-03-01 para todo lo que se compare con la tabla de MIROVA (A119); NHI-v1 empieza el 2026-02-04.
- **No mirar las publicaciones diurnas VIIRS de V1 a V5** (2026-04-01 a 2027-02-28, salvo los huecos ya mirados) antes
  del **2027-03-07**: son los datos de veredicto del control diurno de #1097 (`experiments/_s195_viirs_dia_control/PREREGISTRO.md` §3).
  Eso no se toca.
- **Hueco común: no hay vara de magnitud.** SWIR, OVDAS y la persistencia dicen si había calor, no cuántos MW. Las
  mejoras que sólo cambian la potencia (MEJ-2, MEJ-3, la magnitud en geometría nativa) no se pueden juzgar hasta tener
  una. La única candidata documentada es el VRP desde Sentinel 2 de Massimetti et al. 2020 (paper de la lista MIROVA),
  que sirve para fuentes calientes de día; NHI-v1 guarda `swir2_total` por escena, y si se puede llevar a potencia como
  en ese paper es SIN VERIFICAR.

## 2. Orden propuesto y por qué

El encargo traía un orden. Los datos piden cambiarlo en cinco puntos: el retiro de la sombra C0 y la vara de Lastarria
suben (son baratos y destraban el laboratorio que ya está andando), MEJ-4 sube junto al lacolito (los dos son de Cordón
Caulle y su disparador ya se cumplió), MEJ-7 sale del laboratorio, y MEJ-2 y MEJ-3 se archivan con una condición de
reapertura.

| orden | id | mejora | por qué en este lugar |
|---|---|---|---|
| 0 | P0 | que una anomalía conocida no esconda un foco nuevo | requisito de Nicolás del 2026-11-23, va primero; su parte (1) no toca la detección y sale con la partición de #1092 |
| 1 | P1 | MEJ-8, agua (Laguna del Maule) | es la única con una falsa alarma visible en el tablero público (los 34, como preliminares); el primer paso es un A/B aislado de Laguna del Maule y después una decisión de geometría |
| 2 | P10 | retiro de la sombra C0 | cuesta 186 minutos-job por día (plan S190 §3) y su vigilancia da `SIN_OBJETO` desde S193; libera cupos para los pasos 4 a 6 del laboratorio |
| 3 | P9 | vara de Lastarria | sin ella Lastarria no vota en MEJ-5 (`experiments/_s194_lab_zona_a/PREREGISTRO.md`); la persistencia medida dice que hay algo fijo, pero no sirve de juez: la vara útil es OVDAS o TIR |
| 4 | P7 | MEJ-6, filtro solar diurno | ganancia real (alertas diurnas protegidas), pero el VIIRS de día está tomado por #1097 hasta el 2027-03-07: ahora sólo diseño |
| 5 | P8 | lacolito de Cordón Caulle | 254 pasadas en que el 375 publica la zona del lacolito y el 750 calla; entra al laboratorio sólo con una zona A propia |
| 6 | P4 | MEJ-4, caja MODIS en el cráter | 8 noches de Cordón Caulle con el 375 sobre 1 MW y MODIS en cero; un brazo chico con Villarrica de control lo decide |
| 7 | P3 | cumbres 375 sin 750 | población grande (1.668 pasadas) pero el 375 ya las publica en producción: lo que se gana es una serie 750 continua |
| 8 | P8b | magnitud en geometría nativa | sin vara de magnitud (§1) |
| archivada | P5 | MEJ-2, fondo determinista | producción ya es determinista; reabrir si aparece vara de magnitud |
| archivada | P6 | MEJ-3, fórmula a todo ángulo | acotada (se sabe cuándo actúa, no por qué); reabrir con un evento de 100 MW o más sobre 50° de cenit |
| sale | P2 | MEJ-7, foco MODIS de Láscar | ya lo publica producción: va a la cuenta de paridad |

El P0 (§2b) va primero por decisión de Nicolás. Las secciones que siguen van en el orden del encargo (P1 a P10),
para que cada una se pueda revisar contra él.

## 2b. P0. Que una anomalía conocida no esconda un foco nuevo en otra parte del edificio

> Requisito de Nicolás del 2026-11-23, transmitido por la coordinadora S196, que va **antes que todo lo demás**: «no
> queremos que una señal constante como el lacolito de puyehue o el crater de villarrica nos oculte posibles señales
> volcanicas que se den en otra parte del edificio y que si son incipientes quedaran ocultas tras las otras anomalaias
> ya conocidas y que pueden ser mayores [...] en replica solo se prublica la mayor anomalia [...] en experimental
> deberia permitir mas de una si es que exisitieran».

**El fenómeno.** Un volcán con una fuente térmica constante (el lacolito y la fisura de Cordón Caulle, el lago de lava de
Villarrica, el cráter de Láscar) puede abrir un foco nuevo en otro lado: una fisura en el flanco, un domo, una fumarola
que se calienta. Al principio ese foco es débil, más débil que la fuente conocida. Hay tres maneras en que hoy queda
escondido, y conviene separarlas porque se arreglan distinto:

1. **En la publicación.** La réplica publica una sola posición por pasada, la del cúmulo de la alertada más radiante
   (regla «radiante», D8'), y una sola potencia, la suma de todos los alertados (D32). Un foco nuevo y débil entra a la
   suma y desaparece en la posición del conocido. La única marca de hoy va al revés: v1.72 avisa «también hay calor en
   la cumbre» cuando la posición publicada está lejos y hay alertados en el cráter.
2. **En la detección (enmascaramiento).** El umbral del test contextual es max(mu + s·sd, piso), con mu y sd sacados de
   toda la grilla de 50 km (`pipeline/mirova_v750_codigo.py::_pasada_contextual`). La anomalía grande y su halo tibio
   agrandan sd; si mu + s·sd pasa sobre el piso, el umbral sube en todo el edificio. El segundo pase saca del fondo las
   celdas que alertaron en el primero (`excluidos = absol | ctx1`), pero no el halo tibio que no alertó.
3. **En la ventana de búsqueda.** Cada grilla tiene una región sensible (umbral bajo) y el resto conservador. En Cordón
   Caulle la región sensible de VIIRS 750 es la caja de 7 × 7 celdas en el cráter (#999); en MODIS, la caja de 5 × 5 al
   centro de la grilla, con el cráter afuera (D36 punto 7). **Corrección a la premisa del pedido:** fuera de la caja el
   foco no es invisible. La zona 0 se busca con los umbrales conservadores (docstring de `caja_roi`, verificación
   F9-106 de S193; el `.m` l. 389 a 391); lo que la deja casi ciega para un foco incipiente es el piso conservador de
   noche, 0,02 en NTI y 0,01 en ETI, contra 0,003 de la región sensible.

**Lo que ya existe.** La vía guarda los alertados de cada pasada en `anomaly_pixels` (hasta 100 por record, con
`lat`, `lon`, `bt_k`, `fila`, `col` y distancia; no guarda la potencia por píxel). #1092 (v1.73) reparte a posteriori
la potencia entre cráter, agua, flanco (10 km provisional, AR3 sin respuesta) y resto, invirtiendo Planck desde `bt_k`,
con cierre comprobado en 8.997 pasadas (`experiments/_s194_areas/INFORME.md`); y `experiments/_s194_areas/recurrencia.py`
cuenta en cuántas noches alertó cada casilla de 1 × 1 km. No hay series por área ni alerta de zona nueva publicadas.

**Medido hoy, sin reprocesar.**

- **Enmascaramiento, la firma, por volcán** (`m0_enmascaramiento.py`, `salida_m0_enmascaramiento.txt`). El umbral
  sensible del segundo pase (`u_nti2`, mediana) sube con la potencia de la escena dentro de cada volcán, pero poco en los
  que importan: Cordón Caulle de 0,0036 (sin calor) a 0,0049 (1 a 10 MW, n 41), Villarrica de 0,0037 a 0,0039 (n 13),
  Láscar de 0,0031 a 0,0035, Nevados de Chillán de 0,0038 a 0,0053 (10 a 100 MW, n 167). Las cifras agrupadas por
  familia de la misma salida no se citan: 167 de los 173 records de 10 a 100 MW son de Chillán y mezclan volcanes (A114,
  lección S126; lo vio el verificador). El umbral conservador (`u_nti1`) queda en su piso de 0,02 en casi todas las escenas (0 a 6 %), o sea, fuera de la región
  sensible lo que frena a un foco chico es el piso fijo, no la anomalía. Dos cautelas: la nubosidad y el ángulo también
  agrandan sd (las escenas sin calor ya están sobre el piso en el 68 a 72 %), así que esta cuenta muestra la firma pero
  no la separa de esas causas; y no hay escenas sobre 10 MW en Villarrica ni en Cordón Caulle en la ventana.
- **Cuántas pasadas ya traen un segundo foco** (`m0b_cumulos_multiples.py`, `salida_m0b_cumulos_multiples.txt`). Con
  un segundo cúmulo 8-conexo a 3 km o más del principal: Láscar 78 de 896 pasadas con detección, Isluga 72 de 603,
  Lastarria 56 de 421, Cordón Caulle 38 de 442, Tupungatito 29 de 434, Planchón-Peteroa 20 de 292, Villarrica 2 de 66.
  Con el principal en el cráter y el segundo fuera del radio interno: Láscar 14, Nevados de Chillán 3, Tupungatito 1,
  con un segundo cúmulo de mediana 1 píxel (2 en Tupungatito) y más frío que el principal. Esa columna no puede contar a
  Cordón Caulle (su radio interno es de 20 km); con el principal a 3 km o menos del cráter y otro cúmulo a 3 km o más de
  él **dentro** del radio interno, Cordón Caulle tiene 31 pasadas y Villarrica 0 (`m0c_segundo_foco_en_edificio.py`,
  `salida_m0c_segundo_foco_en_edificio.txt`). «Otra parte del edificio» se mide con el radio del edificio (D-H), no con
  el radio interno. Muchos serán ruido, y por eso la parte (2) necesita línea base y persistencia.

**El plan, en cuatro partes, de la más barata a la más cara.**

1. **Publicación múltiple** (sin tocar la detección ni A45). En el laboratorio, una serie de potencia por área (cráter,
   flanco, resto, agua) y otra por cúmulo, en cada pasada, armadas con la partición de #1092 sobre los records que la vía
   ya escribe. Lo exacto es el número de píxeles alertados y su BT por área y por cúmulo, y eso se publica como tal. La
   potencia por área **no es exacta**: lo que cierra es la suma por pasada, y el fondo se reparte por partes iguales
   entre los alertados («el VRP por área no está medido, está repartido», `experiments/_s194_areas/INFORME.md`), así
   que un foco de 1 píxel junto a un cráter caliente, justo el caso de Nicolás, puede quedar corrido. Va como estimación
   con su vara pendiente. Sale en la pestaña «Laboratorio» por área, con el número de cúmulos de la pasada. Para Cordón Caulle hace falta definir sus áreas (D-D: el radio interno de 20 km no sirve de «cráter»).
2. **Alerta de zona nueva.** Una casilla de 1 × 1 km que alerta en una noche y no alertó en ninguna de las N noches
   previas (línea base móvil por volcán, `recurrencia.py`), y que vuelve a alertar en las M noches siguientes, se marca
   como «zona nueva», sea cual sea el tamaño de la anomalía conocida. La persistencia (M) es lo que separa un foco de un
   píxel de ruido, y tiene mucho que hacer: sin ella, con N = 30, de marzo a noviembre salen 194 casillas «nuevas» en
   Láscar, 229 en Lastarria, 192 en Isluga, 99 en Chillán y 38 en Cordón Caulle y en Villarrica, y sólo una minoría está
   pegada a una casilla ya alertada (`m0d_tasa_zona_nueva.py`, `salida_m0d_tasa_zona_nueva.txt`). N y M se fijan con esa
   misma medición extendida a N de 30, 60 y 90 y M de 1 a 3; la tasa tiene que bajar en un orden de magnitud, hasta que
   Nicolás quiera mirar cada una. Un límite que hay que decir: la alerta sólo marca focos que el detector ya alertó; un
   foco escondido por los mecanismos 2 o 3 nunca la dispara. Por eso (2) sola no responde al pedido: necesita (3) y (4).
3. ⚠️ **S200 (2026-11-25): medido en VIIRS 750 de noche, resultado nulo en el flanco.** Con el detector de producción
   sin modificar (`b7626b03c`), 10 pasadas reales y la anomalía de Chillán (13 MW) trasplantada a 9 volcanes hasta
   403 MW, un foco a 1000 K a 5, 10 o 20 km necesita la misma potencia con la anomalía que sin ella (razón mediana
   1,000, máximo 1,25 fuera de la región sensible); pegado al cráter (2 km) hay un enmascaramiento chico (mediana 1,00 a
   1,10). El segundo pase lo desarma casi todo y la cumbre no deja halo tibio en la estadística. Lo que decide si un foco
   en el flanco se ve es la caja: alerta desde 0,34 MW en la región sensible y desde 1,4 MW fuera de ella, por el piso
   de 0,02. Controles de identidad, linealidad, escena sin calor y ruido pasaron. Límites: sólo Chillán trae una
   anomalía fuerte real; una anomalía extensa (campo de lava) es SIN DATO; MODIS y VIIRS 375 piden recortes de Actions.
   En VIIRS 750 la extensión del halo pierde su motivo medido y (4) queda como la palanca; decidirlo es de Nicolás. Detalle:
   `experiments/_s200_p0_3/INFORME.md`. Texto anterior:
   **Enmascaramiento, medido de verdad.** Un experimento con el detector de producción (`detectar_mirova`, sin
   tocarlo) que inserta un foco débil a 2, 5, 10 y 20 km de una anomalía fuerte. Lo más fuerte es insertarlo en escenas
   reales con su anomalía real (las 167 de Chillán de 10 a 100 MW, y las de Cordón Caulle), porque un halo sintético es
   un parámetro inventado del que depende el resultado. Los insumos hay que rearmarlos: las matrices chilenas de S159 no
   están en disco (en `experiments/_s159/o1/` no hay `entradas.mat`); hay 10 `recorte_*.npz` en
   `experiments/_s158_audit_r2/`, y el ejemplo de Etna del OSF queda de respaldo. Se mide el contraste mínimo con que el foco débil alerta con y sin la anomalía
   fuerte. Si el enmascaramiento existe, se prueba en el laboratorio la extensión natural: calcular mu y sd del segundo
   pase sin un halo dilatado de los alertados (3, 5 o 7 celdas, el mismo halo que el `.m` ya usa para el fondo del VRP).
   La medición en disco de arriba se completa estratificando por cenit y por escenas con la misma potencia en días
   seguidos, para separar la anomalía de la nube.
4. **Ventana de todo el edificio.** En el laboratorio, la región sensible deja de ser la caja del cráter y pasa a ser
   el edificio (un radio por volcán, AR3), con los umbrales sensibles. Ojo con el código de la zona A de MEJ-5: hoy sólo
   actúa dentro de la región sensible (`zona_a & (box == 2)` en `detectar_mirova`), así que mirar el edificio pide
   cambiar la caja, no sólo la zona A. Es la parte de mayor costo en falsas alarmas (valles tibios, salares, incendios en
   el flanco) y por eso va última y medida con los negativos limpios de MEJ-5.

**Qué sería un acierto y contra qué vara.** (1) no necesita vara. (2), (3) y (4) sí, y para el flanco **NHI casi no
sirve**: su caja mide de 1,3 a 4 km de lado medio en nueve de los diez volcanes con serie (Villarrica 1,5,
Planchón-Peteroa 1,3, Láscar 3,0; Lastarria no tiene) y sólo la de Cordón Caulle llega a 10 km (`experiments/_s195_viirs_dia_control/nhi_cajas.json`), así que
un foco en el flanco cae fuera de ella. La vara del flanco es la tabla de episodios del OVDAS (D4 (a)) y la imagen de
alta resolución mirada a ojo (Sentinel 2 MSI de 20 m en SWIR, Landsat OLI de 30 m y su banda térmica de 100 m) a pocos
días de cada «zona nueva». Acierto de (2): que las zonas nuevas persistentes caigan donde el OVDAS o la imagen muestran
algo, más que en un sorteo de casillas del mismo volcán. Acierto de (3) y (4): que el laboratorio alerte focos débiles
cerca de una anomalía grande sin subir la tasa en negativos limpios sobre lo que Nicolás fije.

**Riesgos y protección de producción.** (1) y (2) son derivados a posteriori: no tocan `pipeline/` ni lo publicado en la
vista operacional (guard 2 del plan S190 §4: el tablero operacional no lee el laboratorio). (3) en su parte sintética no
toca nada; la extensión del halo y (4) cambian la detección del laboratorio y entran detrás de un flag apagado, con
identidad byte a byte de `data/mirova_equivalent/`. El riesgo científico de (2) y (4) es una lluvia de falsas «zonas
nuevas»: por eso la persistencia y la tasa medida antes.

**Costo.** (1): una sesión (extender `particion.py` a todas las pasadas y a un JSON por volcán, y la vista). (2): una
sesión para la medición de la tasa y otra para la alerta. (3): una sesión sin Actions para el sintético; la extensión,
un brazo del laboratorio (del orden de un brazo del barrido S195, `salida_costo_barrido.txt`). (4): un brazo más, después
del veredicto de MEJ-5.

**A45.** (1), (2) y el sintético de (3): no. La extensión del halo de (3) y la caja de (4): sí
(`pipeline/mirova_v750_codigo.py`).

## 3. P1. MEJ-8: lagos y lagunas tibias que se confunden con calor volcánico

**El fenómeno.** De noche un lago está más tibio que la roca y la nieve que lo rodean: el agua guarda el calor del día
y lo suelta despacio, mientras el suelo se enfría rápido. Para un detector que busca un píxel más tibio que sus
vecinos, la orilla de un lago es exactamente eso. Coppola et al. 2016a (`documentacion/sp426_5.txt`, l. 689 a 694) lo
reconoce: detecciones falsas de menos de 5 MW en el borde de cuerpos de agua, que el operador quita mirando el mapa.

**Por qué MIROVA lo hace así y qué ganaríamos.** El código de MIROVA no tiene máscara de agua; confía en el operador.
La réplica es fiel y no se toca. Lo que ganaríamos es no mostrar como actividad de un volcán el calor de su lago.

**Dónde muerde, medido.** En los 11 Tier A, en nada de lo que se publica: 0 de 3.013 pasadas publicadas tienen un
alertado sobre agua (`salida_m8b_agua_en_publicadas_tier_a.txt`); los picos sobre agua de S193 en Láscar, Villarrica y
Chaitén están a 10 a 25 km del cráter (`experiments/_s193_lagos/resumen.txt`) y el tablero sólo publica la cumbre. En
los 34: Laguna del Maule tiene 35 de 123 pasadas con el pico sobre agua, 33 a 5 km o menos, porque el punto del volcán
cae dentro del lago (celda de 1 km entera de agua, `experiments/_s193_lagos/verificaciones.txt`); Carrán-Los Venados
21 de 120 (20 a 5 km o menos). MIROVA no publica Laguna del Maule (`experiments/_s193_lagos/INFORME.md` §4), así que ahí
no hay réplica que proteger.

**Qué sería un acierto y contra qué vara.** Que la regla saque las detecciones de lago y no saque calor real. La vara
natural sería SWIR, y **la bandera de NHI no sirve en estos dos volcanes**: alerta en 19 de 133 escenas de Laguna del
Maule (13 de 35 de Landsat, con nubosidad mediana de 39 % en las alertas) y en 33 de 58 escenas Sentinel 2 de Carrán,
con mediana de 257 píxeles calientes, todos los meses (`salida_m8_nhi_en_lagos.txt`). Ninguno de los dos tiene un foco
superficial conocido de ese tamaño, así que eso es un artefacto de NHI (reflejo, nube o algo en su caja) y no una vara.
Lo que queda: (a) mirar la escena (color verdadero y SWIR) de Sentinel 2 o Landsat más cercana a cada pasada
descartada, que es trabajo de ojo pero son pocas (33 más 20); (b) la tabla de episodios del OVDAS; (c) la temperatura:
un lago sin aporte volcánico no pasa de cierta BT de MIR (S193: pico sobre agua con mediana 278,8 K y máximo 315,5 K en
todos los volcanes; 295,7 K en Laguna del Maule), y ése es el corte de la salvaguarda.

**Datos.** Hay: la capa de agua por volcán (`frontend/agua/<Volcán>.geojson`, JRC GSW v1.4, ocurrencia de 50 % o más,
`scripts/generar_capa_agua.py`), el conteo por píxel de S193 (`experiments/_s193_lagos/medir_agua.py`) y el reparto por
áreas de #1092 (`experiments/_s194_areas/particion.py`, `config/areas_laboratorio.yaml`, sólo 10 Tier A). Falta:
congelar la capa como raster en el repo (hoy `medir_agua.py` baja los tiles de JRC), y una serie de escenas revisadas a
mano para la salvaguarda.

**Medición previa.** Hecha: `m8b_agua_en_publicadas_tier_a.py` (cero publicadas con agua en los Tier A, 6 records no
publicados con agua, control distinto de cero) y `m8_nhi_en_lagos.py` (la bandera NHI no sirve ahí). Con eso el plan
queda en tres pasos:

0. **A/B aislado de Laguna del Maule antes de decidir nada.** Reprocesar la historia de Laguna del Maule con las
   celdas de lago fuera de la `BOX`, en un `data_subdir` propio, y contar las dos caras: alertas que se pierden y
   **alertas nuevas que aparecen**. El `NaN` no sólo apaga las celdas del lago: las saca de mu y sd de toda la grilla,
   de las medias 3 × 3 de la orilla y de la regresión del ETI (`detectar_mirova`: `excl = np.isnan(box)`,
   `nti_roi[excl] = nan`), así que puede bajar el umbral y crear alertas en la orilla. El «33 de 33» de S193 contó la
   posición del píxel pico, no corrió el detector (`experiments/_s193_lagos/INFORME.md` §4).
1. **Laguna del Maule, geometría** (decisión de Nicolás, D5 de los 34), sólo con el resultado del paso 0: dejar fuera de
   la `BOX` las celdas de lago (`NaN`, el mecanismo de exclusión que el `.m` prevé en sus l. 102 y 103) o mover el
   punto. El punto lo fijó Nicolás el 2026-04-16 (`5c71e207a`) y la revisión de coordenadas de S190 lo dejó donde está
   (`experiments/_s190_coordenadas/INFORME.md`), así que moverlo sería deshacer una decisión suya sin dato nuevo.
   **Este paso no lleva salvaguarda**: ciega las celdas del lago sin excepción.
2. **Regla general, en el laboratorio de los 34** (no existe todavía): descartar un píxel alertado si la mitad o más de
   su celda es agua, sin margen de orilla (S193 midió que un margen borraría actividad real: 1.693 pasadas de cumbre «a
   la orilla», 53 de 1 MW o más en Planchón-Peteroa), con la salvaguarda de BT.

**Riesgos y protección de producción.** Un lago cratérico caliente que llene la celda o una erupción sublacustre caerían
bajo la regla; en Chile ningún lago cratérico monitoreado llena un píxel de 375 m (0 de 3.926 píxeles de cumbre de
Tupungatito, Planchón-Peteroa y Copahue, S193), pero Laguna del Maule es un sistema en reactivación, y el paso 1 dejaría
ciego justo su lago: un foco sublacustre o de orilla no se vería en la sombra de los 34, que se publica en el tablero
(perfil `sombra_34`, `.github/workflows/sombra-34.yml`). Ése es el costo que Nicolás pesa en D-A, con el A/B del paso 0
a la vista. La salvaguarda de BT es sólo del paso 2. Producción de los Tier A no cambia (medido: 0 pasadas publicadas).

**Costo.** Pasos 0 y 1: una sesión (código del `NaN` en la `BOX` detrás de una clave de `grillas_mirova.yaml`, prueba,
y el reproceso aislado de un volcán en la historia de los 34). Paso 2: crear el laboratorio de los 34, más caro (un perfil, un
workflow, guards), y sólo si el paso 1 no alcanza.

**A45.** Sí: el `NaN` en la `BOX` se lee en `pipeline/mirova_v750_codigo.py` (`caja_roi` hoy sólo arma 0, 1 y 2).

## 4. P2. MEJ-7: el foco puntual del cráter de Láscar que MIROVA calla en MODIS

> ⚠️ **S196: CERRADA por paridad** (D-E de Nicolás, 2026-11-23, §14). Lo que sigue es el razonamiento que la cerró.

**El fenómeno.** El cráter de Láscar tiene un foco pequeño y caliente casi permanente. Un píxel MODIS de 1 km lo ve como
un exceso chico sobre el fondo, al borde del umbral: unas noches cruza, otras no, según el ángulo, la geolocalización y
cómo cae el foco dentro del píxel.

**Por qué MIROVA lo hace así y qué ganaríamos.** MIROVA dejó esa pasada en RUTINA. La premisa de la fila era que el
port lo publicaba y producción no. **Hoy producción sí lo publica**: la vía MODIS (desde el 2026-11-02, historia
reprocesada) publica 2026-05-11 07:55 con 0,21 MW, 1 píxel, a 0,26 km, y también las otras dos candidatas de Láscar del
censo MOD-D (2026-06-04 01:20 y 2026-08-04 07:45). En total, 6 RUTINA de la tabla publicadas de 5.758 con record
(`salida_m7_modis_sobre_rutina.txt`). No queda nada que el laboratorio pueda agregar.

**Vara y medición.** Hecha: SWIR no lo confirma ni lo desmiente con este n (Láscar: 0 de 3 noches con escena NHI a ±1
día alertaron; las RUTINA no publicadas, 59 de 171). Ver el §0 sobre lo que NHI mide a esa escala.

**Plan.** Sacarla del laboratorio y anotarla en la cuenta de paridad MODIS como sobre-publicación (6 pasadas en casi
nueve meses), con la explicación física de arriba. No necesita experimento. Si Nicolás quiere seguirla, el lugar es la
vigilancia de paridad (`scripts/auto_audit_weekly.py`), no un perfil.

**Riesgos, costo, A45.** Ninguno; una línea en la fila de BEYOND (hecha en este PR). No toca A45.

## 5. P3. Cumbres tibias que el VIIRS 750 calla y el VIIRS 375 publica

**El fenómeno.** Un foco de unos cientos de metros llena una fracción del píxel de 375 m cuatro veces mayor que la del
de 750 m. El mismo calor, en el píxel grande, queda diluido entre roca fría y no cruza el umbral. Encima, MIROVA pasa el
gránulo a su grilla con interpolación lineal, que reparte el calor de un píxel aislado entre cuatro celdas: V750-C midió
que conserva el 92 % de la radiancia pero sólo el 54 % del exceso sobre el fondo en las cumbres (`experiments/_s162_v750c/INFORME.md`).

**Por qué MIROVA lo hace así y qué ganaríamos.** MIROVA calla esas cumbres en 750 y las publica en 375; la réplica
también (es la vía). Ganaríamos una serie VIIRS 750 que no se apague cuando el foco es chico. Importa porque la banda
M13 del 750 no se satura en eventos grandes y la I4 del 375 sí: un volcán que pasa de foco tibio a erupción cambia de
sensor útil a mitad del episodio.

**Medido.** 1.668 pasadas en 776 noches, sobre todo Isluga (365), Tupungatito (281), Lastarria (267), Cordón Caulle
(254), Planchón-Peteroa (190) y Láscar (157), con mediana de 0,09 a 0,25 MW y máximo de 3,10 MW
(`salida_m3_cumbre_375_sin_750.txt`). En 1.663 el 750 no marcó ningún píxel (`salida_m4_par_750_de_solo375.txt`): es
dilución o interpolación, no la caja.

**Qué sería un acierto y contra qué vara.** El 375 de la misma pasada sirve de referencia, pero **no es un testigo
independiente**: corre el mismo port del `.m` sobre la misma escena, a la misma hora y con la misma física de NTI, así
que un artefacto común (gradiente topográfico, orilla) pasa por los dos, y un criterio que premie al 750 por copiar al
375 lo premiaría también por copiar el artefacto. Y no hay evidencia independiente de que las 1.668 sean calor: la tasa
de alerta NHI de esas noches es 84 de 529 contra 223 de 1.201 en las noches en que ninguno publica (16 % contra 19 %;
Isluga 12 % contra 31 %; `salida_m3_cumbre_375_sin_750.txt`). Criterio en dos partes: (a) necesario, que el 750 del
laboratorio publique en una fracción alta de las pasadas en que el 375 publica la cumbre sin publicar más en negativos
limpios (mismo instrumento de la zona A); (b) suficiente, una muestra de esas pasadas cotejada con episodios del OVDAS
o con escenas de alta resolución del mismo episodio. SWIR noche a noche no sirve aquí (§0).

**Datos.** Todo en disco: `data/mirova_equivalent/`. Lo que falta es el brazo: el vecino más cercano en vez de la
interpolación lineal (V750-C: recupera 23 de 38 cumbres dentro de la caja) o la geometría nativa (P8b).

**Medición previa barata que falta.** Ninguna sobre disco: el brazo cambia el remuestreo, así que hay que reprocesar.
Lo barato es acotarlo: una tanda de un volcán (Isluga, el de más casos y sin ROI especial) en la ventana de un mes.

**Riesgos y protección de producción.** El vecino más cercano también levanta píxeles aislados ruidosos; por eso el
criterio lleva los negativos limpios. Va en el laboratorio detrás de un flag apagado.

**Costo.** Un brazo de una tanda: del orden de un brazo del barrido S195, que con 10 brazos costó 757 minutos-job
(`salida_costo_barrido.txt`). Más una sesión de pre-registro.

**A45.** Sí: el remuestreo vive en `pipeline/mirova_v750_codigo.py` (`remuestrear_grilla`).

## 6. P4. MEJ-4: grilla y caja ancladas al cráter

**El fenómeno.** El punto de referencia de MIROVA para un volcán no siempre es el cráter activo. En Tupungatito el
cráter queda a 4,9 km al noroeste del centro de la grilla (`experiments/_s162_v750b/ADOPCION_ROI_B4.md`); en Cordón
Caulle el foco de la fisura y el lacolito quedan a 7 a 8,5 km del punto (`experiments/_s182_pcc_crater/README.md`).
Con una caja de detección fija al centro de la grilla, un cráter descentrado puede caer en la región de umbral
conservador o fuera.

**Por qué MIROVA lo hace así y qué ganaríamos.** MIROVA ajusta la caja por volcán (el `.m` lo declara); cuál usa en
Tupungatito es SIN DATO (D36 punto 5). La vía usa la grilla de MIROVA, con `sens` en Tupungatito y `crater` en Cordón
Caulle para VIIRS 750 y la caja `def` en MODIS, donde el cráter queda fuera de la región sensible a 2,11 km en
Tupungatito y a 5,25 km en Cordón Caulle (D36 punto 7). Ganaríamos que cada sensor mire el cráter con el umbral
sensible.

**Medido.** En VIIRS 750 la caja no es lo que calla: el 750 de Tupungatito calla con el cráter dentro de `sens` (§5),
y el verificador S196 comprobó que 1.646 de las 1.668 posiciones «sólo 375» caen en la región sensible del 750. En
MODIS está **sin medir y es sospechoso**. Con focos de 0,1 a 0,3 MW MODIS calla en todas las cajas
(`salida_m4b_modis_en_noches_375.txt`: Isluga 0 de 219, Planchón-Peteroa 0 de 123), así que esa cuenta no tiene poder.
Con el 375 sobre 1 MW (`salida_m4c_disparador_mej4.txt`), MODIS publica en Láscar 48 de 70 noches y en Chillán 32 de
42, y calla las 8 de Cordón Caulle (9 pasadas 375 de 1,06 a 1,31 MW a 0,02 a 0,86 km del cráter, del 2026-09-18 al
2026-11-13, con todos los MODIS de esas noches en 0 píxeles). Pero también calla las 4 de Villarrica, que tiene el
cráter dentro de su caja, y el MODIS pasa horas antes o después que el VIIRS, sobre una fuente (el lacolito) extensa y
tibia. El disparador que la primera versión de este plan dejaba para el futuro ya se cumplió (lo vio el verificador).

**Qué sería un acierto y contra qué vara.** Que MODIS publique el cráter de Cordón Caulle en noches en que el 375 lo
publica sobre 1 MW, sin publicar más en negativos limpios, con Villarrica como control (cráter dentro de la caja: si el
brazo no le cambia nada a Villarrica y a Cordón Caulle sí, es la caja). La vara física del calor de esas noches sigue
siendo la del §10 (persistencia y la caja NHI de 10 km).

**Plan.** Un brazo chico del laboratorio con `roi_modis: crater` en Cordón Caulle (la caja sensible movida al cráter,
como ya hace VIIRS 750 desde #999) sobre esas 8 noches y sus negativos limpios, más Villarrica de control. Va con P8,
porque los dos son de Cordón Caulle. La posición publicada ya se mide desde el cráter (`final_hotspot_dist_km`).

**Riesgos, costo, A45.** Mover la caja en MODIS toca `pipeline/mirova_v750_codigo.py` (`grilla_del_volcan`, clave
`roi_modis`, que hoy no existe en `pipeline/grillas_mirova.yaml`): A45. Costo: unas pocas noches MODIS de dos volcanes,
mucho menos que un brazo del barrido S195.

## 7. P5. MEJ-2: fondo del VRP determinista con un solo píxel

**El fenómeno.** Con un solo píxel alertado, la potencia depende de qué temperatura de fondo se le resta, y MIROVA saca
ese fondo interpolando los vecinos sobre una triangulación. En una grilla regular hay muchas triangulaciones igual de
válidas, y la elección cambia el fondo.

**Por qué MIROVA lo hace así y qué ganaríamos.** Es `fillmissing2` de MATLAB. S159 midió que con un píxel el VRP varía
hasta 1,82 veces entre tres implementaciones del fondo (Octave y los dos ports; ninguna era MATLAB;
`experiments/_s159/o1/INFORME.md`). Desde V750-F el port copia el desempate de MATLAB y lo iguala en 166 de 166 VRP:
**producción ya es determinista**. Lo que quedaría es otra cosa: un fondo con una regla física (por ejemplo la mediana
del anillo) en vez de un desempate arbitrario.

**Vara.** No hay vara de magnitud (§1). Sin ella, un fondo «mejor» no se puede llamar mejor.

**Plan.** Archivar con condición de reapertura: cuando exista una vara de magnitud (Massimetti 2020 u otra), medir la
diferencia entre el fondo del `.m` y uno de regla fija en las pasadas de un píxel. Lo único abierto que sí es de la
réplica es la orientación de las filas (D36 punto 4: Etna -0,38 %), y eso va por paridad, no por el laboratorio.

**Medición previa, costo, A45.** Ninguna hoy (los records no guardan la grilla de fondo). Sin costo. Si se reabre, toca
`pipeline/mirova_v750_codigo.py`: A45.

## 8. P6. MEJ-3: la misma fórmula a todo ángulo

**El fenómeno.** Un píxel visto de lado (cenit alto) es más grande y más deformado; la potencia de un foco no debería
depender del ángulo si la fórmula usa el área correcta.

**Por qué MIROVA lo hace así y qué ganaríamos.** En el OSF de MIROVA, el 24 % de las filas VIIRS 750 sobre 50° no
cumple la fórmula de su propio código (siempre por debajo). S190 lo acotó: el escalón depende de la magnitud
(2 de 12.048 filas hasta 20 MW, 4.050 de 4.111 sobre 500 MW; `experiments/_s190_d36/INFORME.md` §2), lo que apunta a un
umbral o una corrección de software para eventos grandes; el informe dice cuándo actúa, no por qué, y si el NRT de
MIROVA lo mantiene es SIN DATO. En nuestros pares de Chile sobre 50° la razón es 0,996 (n 39), pero todos son del tramo
donde el escalón casi no actúa, así que esos pares no tienen poder para verlo; no hay ningún par de 100 MW o más. Hoy
no hay nada que medir en Chile.

**Plan.** Archivar con disparador: la primera pasada VIIRS 750 chilena de 100 MW o más con cenit sobre 50° se compara
con MIROVA y con la fórmula. Si MIROVA la recorta, se entiende la corrección antes de llamarla defecto (la fila ya lo
dice). Vara de magnitud: la misma falta del §1.

**Costo, A45.** Ninguno mientras no haya evento. No toca A45.

## 9. P7. MEJ-6: el día con un filtro solar propiamente tal

**El fenómeno.** De día el Sol se refleja en la roca, la nieve, el hielo y las nubes, y una parte de ese reflejo cae en
la banda de 4 micrones que se usa para el calor. Una ladera soleada o un borde de nube puede parecer un foco caliente.
El reflejo es más fuerte cuando el satélite mira justo hacia donde el Sol rebota (ángulo de reflejo especular chico) y
al mediodía de invierno en las cumbres nevadas.

**Por qué MIROVA lo hace así y qué ganaríamos.** El código de MIROVA rechaza la pasada entera si el ángulo de reflejo es
menor que 12° (`pipeline/mirova_v750_codigo.py`, l. 87 a 89 del `.m`) y sube los umbrales de día; aun así publica
artefactos solares (A76; uno de 760 MW en Láscar que se limpió a mano). Producción hoy: MODIS de día encendido por decisión del
2026-11-21 (`enable_daytime_modis: true`), VIIRS de día apagado (`enable_daytime_viirs: false`). En el A/B diurno de S190
el día recupera en VIIRS 750 13 de 18 protegidas con 0 de 2.910 negativos publicados, y en VIIRS 375 23 de 42 con 8 de
2.620; las 19 que el 375 no recupera son casi todas de Láscar y Lastarria al mediodía de junio, el patrón de reflejo
probable (`experiments/_s190_diurno/INFORME_VEREDICTO.md` §3). El filtro solar propiamente tal es otra cosa que el
control de #1097: aquél conserva una publicación diurna si tiene historia nocturna en el mismo lugar (persistencia);
éste decidiría por la física del reflejo de esa pasada, sin mirar la historia. Ganaríamos publicar de día el calor
real y no el reflejo, también donde no hay historia nocturna (un foco nuevo).

**Qué sería un acierto y contra qué vara.** SWIR es buena vara aquí, mejor que de noche: NHI es diurno, así que se parea
el mismo día y a pocas horas. Acierto: entre las publicaciones diurnas que el filtro quita, la tasa de alerta NHI del
mismo día en la caja del volcán es menor que entre las que conserva, con el control de fechas corridas del §0.

**Datos.** Hay: la geometría solar y del sensor por record (`solar_zenith_deg`, `solar_azimuth_deg`,
`sensor_zenith_deg`, `sensor_azimuth_deg`), el brazo diurno de la vía (`pipeline/profiles/_s190_ab_diurno_via_on.yaml`),
las cajas NHI de S195 (`experiments/_s195_viirs_dia_control/nhi_cajas.json`). Falta: la carpeta de datos del A/B diurno
no está en disco (hay que bajarla de su rama o reprocesar), y la regla física misma. Candidatas a leer antes de
proponer una (sin afirmar valores): las pruebas de reflejo de los productos de incendios MODIS y VIIRS (sus ATBD), y lo
que dicen de reflejo los papers MIROVA. Ninguno está hoy en `documentacion/` (búsqueda de «glint», sin resultados).

**Medición previa.** Descrita, no hecha: con los records diurnos del A/B de S190 en las ventanas de desarrollo W2 a W7
(las únicas ya miradas), calcular el ángulo de reflejo de cada publicación y ver si separa las 19 no recuperadas y los 8
negativos publicados de las 23 recuperadas. Son minutos una vez bajados los datos; no la hice porque no están en disco.

**Riesgos y protección de producción.** El riesgo de método es contaminar #1097: **nada de V1 a V5** (§1) hasta el
2027-03-07. El diseño se hace con W2 a W7 y el veredicto se mide en una ventana posterior a V5 (desde el 2027-03-01).
El riesgo físico: un filtro por ángulo quita también el calor real que coincide con el reflejo; por eso la vara es SWIR
del mismo día. En el laboratorio, detrás de un flag; producción no cambia.

**Costo.** Una sesión de lectura y diseño ahora; la medición previa, minutos con los datos; el veredicto, un reproceso
diurno del laboratorio en la ventana de 2027 (del orden de un brazo del barrido S195).

**A45.** Probable: la rama diurna de la vía está en `pipeline/mirova_v750_codigo.py`.

## 10. P8. El lacolito de Cordón Caulle (y P8b, la magnitud en geometría nativa)

**El fenómeno.** El lacolito de 2011 y 2012 sigue enfriándose y la fisura conserva calor; es una fuente extensa y tibia,
desplazada del punto de referencia del volcán (7 a 8,5 km, `experiments/_s182_pcc_crater/README.md`). Con su zona de
cráter de 20 km, Cordón Caulle no entra en la lógica de la zona A del laboratorio (D6 del plan S190).

**Por qué MIROVA lo hace así y qué ganaríamos.** MIROVA publica sólo lo que cruza su umbral ahí, con una mediana de
0,29 MW (`docs/BASELINE_LITERATURA_TIER_A_S77.md`). El 375 de producción publica la zona en 254 pasadas en que el 750
calla, a 0,30 km del cráter que usamos y a 7,60 km del centro de MIROVA, con mediana de 0,25 MW
(`salida_m3_cumbre_375_sin_750.txt`, `salida_m4_par_750_de_solo375.txt`). Ganaríamos que el laboratorio mida Cordón
Caulle con una zona A de radio propio alrededor del cráter (la opción de D6 que no se tomó).

**Qué sería un acierto y contra qué vara.** Persistencia en el lugar (§12 muestra que en Láscar, Villarrica y Lastarria
separa del sorteo) y SWIR: la caja NHI de Cordón Caulle es de 10 km de lado medio y contiene el punto
(`nhi_cajas.json`), así que cubre la zona. Con NHI, la diferencia entre «sólo 375» y «ninguno» en Cordón Caulle es chica
(5 de 52 contra 4 de 72; con el control, 2 de 48 contra 4 de 89): poco poder.

**Datos, medición previa.** Todo en disco. Medición barata que falta y es de minutos: con los records actuales, cuántas
pasadas del laboratorio cambiarían de estado si la zona A fuera un círculo de 3, 5 u 8 km alrededor del cráter (el
script de `experiments/_s195_lab_paso3/contar_zona_a_fuera_de_sensible.py` se puede apuntar a Cordón Caulle). La dejo
descrita porque el radio es una decisión de geólogo (D6) y no conviene medir antes de que Nicolás diga qué radios tienen
sentido físico.

**P8b, la magnitud en geometría nativa.** Correr el detector sobre los píxeles del barrido, sin pasarlos a la grilla de
MIROVA. S159 midió que contra MIROVA da 0,990 [0,703; 1,290] (n 163; `experiments/_s159/n/INFORME.md`), con un rango
mucho más ancho que el de la vía, y N0/N1 de V750-B nunca corrió. Sin vara de magnitud (§1) no hay cómo decir cuál es
mejor. Archivada con P5.

**Riesgos, costo, A45.** La zona A propia de Cordón Caulle es una clave del perfil `laboratorio` y un valor en la lista
de volcanes del pre-registro: no toca A45 si el código de la zona A ya acepta un radio por volcán (verificarlo al
escribir el plan del PR). Costo: una adenda al pre-registro de MEJ-5 y un brazo más en el próximo despacho.

## 11. P9. Lastarria: una vara que no sea SWIR

**El fenómeno.** El calor de Lastarria es de un campo fumarólico: gas y vapor a temperaturas de cientos de grados, no
lava. Es extenso y de baja temperatura (la literatura reunida en `docs/BASELINE_LITERATURA_TIER_A_S77.md` lo pone bajo
600 K y entre 0,5 y 5 MW). SWIR, que es la vara del resto, está hecho para lo muy caliente: un píxel de 20 m a 400 K casi
no brilla a 2,2 micrones. Y NHI-v1 no tiene Lastarria (43 carpetas, ninguna de Lastarria; `gh api` del 2026-11-23).

**Por qué importa.** Sin vara, Lastarria no vota en MEJ-5 (`experiments/_s194_lab_zona_a/PREREGISTRO.md`) y cualquier
extensión que lo toque queda sin juez.

**Medición previa (hecha, `m9_lastarria_persistencia.py`).** Persistencia: de las publicaciones nocturnas de Lastarria
con otra en las 3 noches previas, el 89 % cae a 1 km o menos de alguna (224 de 252), contra una mediana de 29 % con
posiciones sorteadas en su disco de 3 km. El instrumento da lo mismo en volcanes con foco conocido (Villarrica 94 %,
Láscar 100 %), así que puede dar distinto del sorteo. Pero la persistencia sola dice «algo fijo en el lugar», no «calor
volcánico». El control con cuatro volcanes de los 34 (Parinacota, Taapaca, Nevado de Longaví y Tinguiririca, con el
mismo radio de 3 km y el mismo predicado simple) no pudo probar persistencia porque casi no publican: 2 a 5 noches en
ocho meses, contra 166 de Lastarria (`salida_m9_lastarria_persistencia.txt`). Esa diferencia de tasa ya es una señal: un
volcán andino sin campo fumarólico activo no produce publicaciones de cumbre noche tras noche. Ojo: si esos cuatro
volcanes no tienen fumarolas es un supuesto mío que debe confirmar Nicolás, y en las pasadas «sólo 375» la posición
publicada de Lastarria queda a 2,16 km del cráter en mediana (`salida_m4_par_750_de_solo375.txt`), lo que conviene
cotejar con dónde está el campo.

**Las varas posibles, de más a menos concreta.**

1. **Persistencia más tasa contra volcanes de control** (lo medido arriba). Concreta y gratis, pero **no sirve de juez
   de MEJ-5** (lo vio el verificador): dice que en la cumbre de Lastarria hay algo fijo, y toda alerta que la zona A
   agregue junto a ese algo saldrá «persistente», sea fumarola o gradiente topográfico (A69). El sorteo uniforme no es el
   nulo de «dónde agrega píxeles un umbral más bajo». Si se usa, como condición necesaria, y con un nulo distinto: la
   persistencia de las alertas que agrega el mismo brazo en volcanes de control que elija Nicolás.
2. **Episodios del OVDAS** (D4 (a), ya aprobada; plantilla en `docs/PLANTILLA_EPISODIOS_OVDAS_S190.md`). Concreta si la
   tabla se llena.
3. **TIR de alta resolución (Landsat 8/9, banda térmica de 100 m).** Un campo fumarólico se ve en TIR como unos grados
   sobre el fondo; AVTOD (ASTER, 90 m) le midió a Lastarria 20,39 °C de máximo sobre el fondo entre 2000 y 2017
   (`docs/M2_AVTOD_INTEGRATION_S122.md`). El workspace tiene `Landsat-v1` (Landsat 8/9 por Planetary Computer, sano
   según `MAPA_WORKSPACE.md`); no verifiqué que cubra Lastarria ni que guarde la banda térmica. Es un supuesto hasta
   mirarlo.
4. **Pedir a NHI-v1 que agregue Lastarria.** Barato (otro repo de Nicolás), pero por lo del primer párrafo probablemente
   no vea el campo. Sólo sirve si se confirma que NHI ve fumarolas de esa temperatura.

**Riesgos y protección de producción.** Ninguno: es medición sobre disco y, si se adopta, una vara en un pre-registro.
**Costo:** la vara 1, una adenda al pre-registro de MEJ-5 (una sesión corta); la 3, una sesión de exploración en el repo
de Landsat-v1. **A45:** no.

## 12. P10. Retiro de la sombra C0 (D1-b del plan S190)

> ⚠️ **S196: paso (1) HECHO** (D-B de Nicolás, 2026-11-23, §14), con dos ajustes al inventario de abajo. (i) El control
> de `tests/test_laboratorio_paso1_s193.py` no se caía al apagar el diario, porque `nrt.yml` conserva la opción manual
> `--profile experimental`; igual se rehízo para no apoyarse en un perfil retirado: ahora mira `--profile
> mirova_equivalent` en `nrt.yml` y tres líneas sintéticas que corren el laboratorio. (ii) `vigilancia_guardia_modis.py`
> y `vigilancia_guardia_viirs.py` no se desacoplaron: `scripts/vigilancia_sombra.py` se conserva entero (sólo se apagó su
> workflow), así que el import sigue sano; el desacople queda para cuando se borre el script, junto con los datos (A38).
> La opción manual `profile=experimental` de `nrt.yml` se deja: no commitea `data/experimental_v2/`. Suite completa: dos
> pruebas dependían del workflow retirado y se reescribieron con marca A113:
> `tests/test_vigilancia_sombra_s156.py::test_el_workflow_escucha_al_workflow_de_la_sombra` (exigía el disparo) y
> `tests/test_vigilancia_guardia_modis_s172.py::test_no_modifica_la_vigilancia_de_k` (exigía el archivo idéntico; ahora
> compara el nombre y los jobs, que no cambiaron).

**El fenómeno (aquí, del sistema).** La sombra C0 (`experimental`, `data/experimental_v2/`) guarda lo que veía producción
el 2026-10-09 con el detector anterior, para disparar la reversión de K si producción callaba algo que C0 veía. Desde
el 2026-11-11 ningún sensor corre K, y desde S193 su vigilancia da `SIN_OBJETO` cuando no hay sensores en K
(`scripts/vigilancia_sombra.py`). Ya no protege ninguna adopción.

**Qué ganaríamos.** 186 minutos-job por día (plan S190 §3, medido la semana del 2026-11-10) y cupos de runner en la hora
del día en que el laboratorio necesitará correr (pasos 4 a 6). Y una pestaña «Laboratorio» que hoy muestra el detector
viejo (`frontend/experimental/index.html` lee `data/experimental_v2/`) quedaría libre para mostrar el laboratorio nuevo.

**Qué sería un acierto.** Que todo siga verde sin la sombra: suite completa, tablero operacional igual, Pages igual, y
ninguna vigilancia que dependa de ella en silencio. No hay vara científica: es mantención.

**Qué hay que tocar** (inventario de sólo lectura de esta sesión). Workflows: `experimental-diario.yml`,
`vigilancia-sombra.yml`, y decidir la opción manual `profile=experimental` de `nrt.yml`. Scripts:
`scripts/vigilancia_sombra.py`, que importan `scripts/vigilancia_guardia_modis.py` y `scripts/vigilancia_guardia_viirs.py` (`vs = vg.vs`; no se puede borrar sin cambiar los dos, y las guardias son la única alarma mientras la reversión está suspendida),
`scripts/banco_paridad.py` y `scripts/verify_reproc.py`. Frontend: `frontend/experimental/index.html` y su enlace en
`frontend/index.html`. Pruebas: unas quince la nombran o leen sus workflows (entre ellas
`tests/test_vigilancia_sombra_s156.py`, `tests/test_vigilancia_sombra_sin_k_s180.py`, `tests/test_experimental_congelado_s150.py`),
y **`tests/test_laboratorio_paso1_s193.py` tiene un control que exige que algún workflow corra `--profile experimental`**:
se cae al apagar el diario y hay que reescribirlo para que apunte al laboratorio. Otras quince parametrizan el perfil
`experimental` en guards de la vía; esas siguen valiendo mientras el perfil exista.

**Medición previa.** No hace falta más: el costo está medido y la falta de objeto la declara el propio script. Lo único
que conviene antes es correr la suite con los dos workflows retirados en una rama, para ver la lista real de rojos.

**Riesgos y protección de producción.** No toca la detección. El riesgo es apagar un vigilante que alguien espera: por
eso Nicolás eligió D1 (a), «retirarla después, en su propio PR». El plan: (1) un PR que apaga los dos workflows y deja
el perfil y los datos congelados (sin borrar `data/experimental_v2/`, A38), arregla el control de
`test_laboratorio_paso1_s193.py` y desacopla `vigilancia_guardia_modis.py` y `vigilancia_guardia_viirs.py`; (2) cuando el laboratorio tenga cron, la
pestaña pasa a leerlo. Borrar los datos viejos queda para el final, con tag (A38).

**Costo.** Una sesión. **A45:** no (ni perfiles de producción ni `pipeline/`).

## 13. Tabla de orden y dependencias

| orden | id | primer paso | depende de | A45 | costo del primer paso |
|---|---|---|---|---|---|
| 0 | P0 (1) series por área y cúmulo | extender `experiments/_s194_areas/particion.py` a todas las pasadas y a la pestaña Laboratorio | áreas de Cordón Caulle (D-D) y radio del edificio (D-H) | no | una sesión |
| 0 | P0 (2) zona nueva | medir la tasa de «zonas nuevas» por volcán y mes con N de 30, 60 y 90 y M de 1 a 3 | (1) | no | una sesión |
| 0 | P0 (3) enmascaramiento (⚠️ S200: hecho en VIIRS 750, nulo en el flanco, `experiments/_s200_p0_3/`) | sintético con `detectar_mirova` y estratificación de `m0` por cenit | nada | no (la extensión del halo, sí) | una sesión sin Actions |
| 0 | P0 (4) edificio entero | brazo del laboratorio con la región sensible del edificio | (3), veredicto de MEJ-5 y D-H | sí | un brazo |
| 1 | P1 MEJ-8 | A/B aislado de Laguna del Maule con el lago fuera de la `BOX` (alertas perdidas y nuevas); después D-A | sí de Nicolás a A45 | sí | una sesión |
| 2 | P10 C0 | PR que apaga los dos workflows y arregla el control del paso 1 | sí de Nicolás a D1-b (D-B) | no | una sesión |
| 3 | P9 Lastarria | pedir la tabla de episodios del OVDAS de Lastarria y explorar el TIR de Landsat-v1; la persistencia, sólo como condición necesaria | D-C | no | una sesión corta |
| 4 | P7 MEJ-6 | lectura (ATBD de incendios, papers MIROVA) y medición del ángulo de reflejo en W2 a W7 | bajar los datos del A/B diurno; nada de V1 a V5 antes del 2027-03-07 | probable | una sesión |
| 5 | P8 lacolito | conteo de la zona A de Cordón Caulle a 3, 5 y 8 km; adenda | radios de D6 (D-D) y que MEJ-5 dé veredicto | por verificar | una sesión |
| 7 | P3 cumbres 750 | pre-registro del brazo vecino más cercano en un volcán | que el laboratorio tenga cupo (P10) | sí | sesión más un brazo (757 minutos-job el barrido S195 de 10 brazos) |
| 6 | P4 MEJ-4 | brazo chico con `roi_modis: crater` en Cordón Caulle sobre sus 8 noches, Villarrica de control | sí de Nicolás a A45; va con P8 | sí | unas pocas noches MODIS de dos volcanes |
| 8 | P8b nativa | ninguno | vara de magnitud | sí si se reabre | ninguno |
| arch. | P5 MEJ-2 | ninguno | vara de magnitud | sí si se reabre | ninguno |
| arch. | P6 MEJ-3 | ninguno | un evento de 100 MW o más sobre 50° de cenit | no | ninguno |
| sale | P2 MEJ-7 | nota en la fila (hecha) | nada | no | ninguno |

Lo que está corriendo y no se toca: MEJ-5 (paso 3 del plan S190, pre-registros S194 y S196) y el control diurno de #1097
(veredicto no antes del 2027-03-07). P3 y P8 dependen además de que el laboratorio exista con datos (paso 4 del plan
S190), y ninguna extensión nueva corre al mismo tiempo que MEJ-5 en el mismo perfil (una a la vez, §1).

## 14. Decisiones que le tocan a Nicolás

**Decididas el 2026-11-23.** Nicolás respondió a la tabla de abajo, textual: «lo que recomiendas pero armas un visor
donde yo pueda elegir el radio con un mapa e ir moviendolo» (transmitido por la coordinadora S196). Queda así:

| # | decisión | qué se hizo o qué sigue |
|---|---|---|
| D-B | **(a)**: retirar ya la sombra C0, en un PR propio | Hecho en el PR del retiro (rama `claude/s196-retiro-c0-cfffa8`): `experimental-diario.yml` y `vigilancia-sombra.yml` sin cron ni `workflow_run`, `data/experimental_v2/` congelada con su README, aviso «SERIE CONGELADA» en la pestaña Laboratorio, control de G6 del paso 1 rehecho y `tests/test_retiro_sombra_c0_s196.py`. El paso (2) de P10 (la pestaña lee el laboratorio) espera a que el laboratorio tenga cron |
| D-E | **(a)**: MEJ-7 se cierra como paridad | Fila de MEJ-7 en `docs/BEYOND_MIROVA_EXTENSIONS.md` §12 marcada cerrada, y nota en la cuenta de paridad de MODIS (`docs/CAMINO_INDEPENDENCIA_MIROVA.md`, E3). No hay experimento |
| D-H | **(a), con visor**: un radio del edificio por volcán, que elige Nicolás moviéndolo sobre un mapa | El visor lo arma la sesión `s196-visor-radios`. Hasta que Nicolás guarde los radios, los pasos del P0 que dependen de D-H (series por área, zona nueva, edificio entero) no parten |
| D-I | **(a)**: la alerta de zona nueva se muestra sólo en la pestaña Laboratorio, con el aviso de que es experimental | El tablero operacional sigue igual a MIROVA hasta tener la tasa de zonas nuevas y su acierto contra OVDAS |

La coordinadora transmitió estas cuatro. D-A, D-C, D-D, D-F y D-G no se registran aquí como decididas: siguen abiertas
con la recomendación de la tabla de abajo hasta que alguien transmita la respuesta de Nicolás sobre cada una.

| # | pregunta | opciones | recomendación |
|---|---|---|---|
| D-H | Radio del edificio por volcán (AR3 de #1092, sin respuesta): ¿cuánto mide el «flanco» de cada uno? | (a) un radio por volcán que tú das, desde la geología; (b) 10 km en todos, como hoy | **(a)**: el P0 entero (series por área, zona nueva y ventana del edificio) depende de dónde termina el edificio, y eso es de geólogo |
| D-I | P0: ¿dónde se muestra la alerta de zona nueva? | (a) sólo en la pestaña Laboratorio, con el aviso de que es experimental; (b) también como aviso en el tablero operacional | **(a)** hasta tener su tasa y su acierto contra OVDAS; el operacional sigue igual a MIROVA |
| D-A | Laguna del Maule: ¿qué hacemos con el punto que cae en el lago? | (a) dejar el punto y sacar de la `BOX` las celdas de lago (`NaN`) en la sombra de los 34; (b) lo mismo, pero sólo en un laboratorio de los 34; (c) mover el punto a otro foco con fuente citada; (d) nada | **Primero el A/B aislado del paso 0** (sí a A45 para el código del `NaN` detrás de una clave), y con sus dos cuentas a la vista, **(a)** si las alertas nuevas en la orilla son pocas: MIROVA no publica Laguna del Maule, así que no hay réplica que romper, y no deshace el punto que fijaste el 2026-04-16. Ojo: (a) no lleva salvaguarda y deja ciego el lago en la serie pública de un sistema en reactivación |
| D-B | ¿Retiramos ya la sombra C0 (D1-b)? | (a) sí, en un PR propio que apaga los dos workflows y deja los datos congelados; (b) esperar a que el laboratorio tenga cron | **(a)**: ya no vigila nada (`SIN_OBJETO`), cuesta 186 minutos-job por día y ocupa cupos que el laboratorio va a necesitar |
| D-C | Lastarria: ¿qué vara? | (a) la tabla de episodios del OVDAS de Lastarria; (b) explorar el TIR de Landsat 8/9 (Landsat-v1); (c) persistencia contra volcanes de control | **(a), con (b) en paralelo**. La persistencia (c) sólo como condición necesaria: dice que hay algo fijo en la cumbre, y toda alerta que agregue la zona A junto a ese algo saldrá «persistente», sea fumarola o gradiente topográfico (A69). Si se usa, su nulo es la persistencia de las alertas que agrega el mismo brazo en volcanes de control que elijas tú, no un sorteo uniforme |
| D-D | Cordón Caulle en el laboratorio: ¿con qué zona A? | (a) círculo alrededor del cráter de 3, 5 u 8 km; (b) seguir fuera (D6) | **(a), que elijas el radio** según dónde está hoy el calor del lacolito y la fisura; se mide con una adenda y sin tocar el pre-registro sellado |
| D-E | MEJ-7: ¿la cerramos como paridad? | (a) sí, nota en la fila y en la cuenta de paridad MODIS; (b) seguirla como experimento | **(a)**: producción ya la publica (6 de 5.758 RUTINA) |
| D-F | MEJ-2, MEJ-3 y la magnitud nativa: ¿archivo con disparador? | (a) sí; (b) buscar ya una vara de magnitud (Massimetti 2020 con Sentinel 2) | **(a)**, y (b) como tarea de investigación aparte, porque es la que destraba a las tres |
| D-G | MEJ-6: ¿diseño ahora y veredicto en 2027? | (a) sí, con W2 a W7 y ventana de veredicto desde 2027-03-01; (b) esperar el veredicto de #1097 para empezar | **(a)**: el diseño no toca los datos de #1097, y su veredicto llegaría poco después |

## 15. Lo que este plan no resuelve

- No leí los ATBD de incendios MODIS y VIIRS: la regla física del filtro solar (P6) queda para su sesión.
- No verifiqué que `Landsat-v1` cubra Lastarria ni que guarde la banda térmica (P9, vara 3).
- La medición de P8 (zona A de Cordón Caulle) queda descrita, no hecha, a la espera de los radios.
- La medición previa de P6 (ángulo de reflejo) necesita los datos del A/B diurno, que no están en disco.
- El conteo de MEJ-8 en los Tier A (`m8b`) usa el centro del píxel dentro del polígono de agua, no la fracción de la
  celda como S193: es más grueso. Para los 34 manda S193.
- Que los cuatro volcanes de control de P9 no tengan fumarolas activas es un supuesto; lo confirma Nicolás.
