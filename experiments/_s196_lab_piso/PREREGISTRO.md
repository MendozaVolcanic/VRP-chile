# Pre-registro de la palanca del piso en la zona A del laboratorio (MEJ-5): criterio sellado (S196)

> **Qué es.** El criterio con que se va a elegir y juzgar el **piso** del umbral contextual nocturno en la zona A del
> perfil `laboratorio`, escrito y commiteado **antes** de que exista un solo record con esa palanca. Lo pidió Nicolás
> el 2026-11-23 (decisión transmitida por la coordinadora S196: «pausar el barrido y pre-registrar la palanca del
> piso»), después de que el barrido del factor s (S195, run 45114681532) se aplanara.
>
> **Relación con el pre-registro S194** (`experiments/_s194_lab_zona_a/PREREGISTRO.md`). Éste **reemplaza su §5** (la
> regla para elegir el valor de la zona A) y **usa sin cambios sus §3 y §4** (la vara: pareo NHI, permutación
> estratificada, control de 15 días, SIN PODER bajo 10, persistencia temporal, orden del veredicto y qué hace cada
> resultado). La vara no se copia: el evaluador de aquí la importa del evaluador S194 y una prueba de sello exige que
> ese archivo siga siendo el sellado. **No es un segundo intento**: con el laboratorio no se ha corrido ningún
> veredicto NHI; del barrido de s sólo se contaron publicaciones nuevas (tres volcanes, marzo), que es calibración y
> no mira NHI. Si algún día se juzgaran contra NHI las dos palancas, la segunda se declara segundo intento.
>
> ⚠️ **Re-sello S200 (2026-11-25), antes de mirar ningún resultado del barrido.** Nicolás decidió re-sellar
> («Sí, re-sella», 2026-11-25) los cuatro defectos de gravedad 3 que la auditoría externa (Codex, ronda 4, frente D)
> encontró y un verificador Claude de contexto limpio reprodujo; qué cambió y por qué, en el §5b. La vara (S194) no
> cambia. Sello vigente (S200c, fin de la ventana sellado en 2026-11-23 por el acta de cierre de la ronda 4, aprobada
> por Nicolás el 2026-11-25; §5b al final):
> sha256 del evaluador (fin de línea LF): `d17a68a2c0a12493a2efafbb839d3018ab4091a5570b52ef18937f024027acbc`.
> Sello S200b (#1130), conservado: `0b403901dedbf566ac0e190cf12d0861b26c24224bc773b1a70e73d42d61dd89`.
> Sello del re-sello S200 (#1129), conservado: `5493f1a714f709c381bae7722c7cbb09c816288f38857b720f77443d287a8286`.
> Sello anterior (S196), conservado: el evaluador tenía
> sha256 (fin de línea LF) `16d0360ebea5549000bbea432050102cf9e87a231a9cba23dbd1222ff4a42217`.
>
> **Sello.** El evaluador es `experiments/_s196_lab_piso/evaluar.py`;
> sha256 del evaluador S194 que importa (fin de línea LF): `072400b76afd536ba161a0e488182873eb83045cdc68c9faf21f8c7e5293f903`
> (el mismo que declara el pre-registro S194 tras su re-sello del 2026-11-23). Las pruebas
> `tests/test_lab_piso_preregistro_s196.py::test_sello_hash_del_evaluador_en_el_preregistro` y
> `::test_sello_hash_del_evaluador_s194_del_que_importa_la_vara` comparan los dos hashes con los archivos: editar
> cualquiera de los dos evaluadores sin re-sellar este documento deja el CI en rojo. Base: `origin/main` en
> `89cf56755` (2026-11-23). No toca `pipeline/`, perfiles, workflows ni tablero; la palanca necesita código nuevo en
> el detector, que queda escrito como paso siguiente (§9) y espera el sí de Nicolás (A45).

## 1. El fenómeno, antes que el código

El detector de MIROVA compara cada celda con sus vecinas en dos contrastes, NTI y ETI (el NTI menos lo que la
superficie fría «debería» dar), y exige que los dos superen un umbral. En la región sensible del cráter, de noche,
ese umbral es **max(mu + 5·sd, 0,003)**: el mayor entre un término estadístico (la media más cinco desviaciones del
contraste de toda la escena) y un **piso fijo** de 0,003 que no depende de la escena.

Los dos frenos actúan en escenas distintas. En una escena revuelta (nubes rotas, bordes de nieve, relieve) la sd es
grande y manda el término estadístico. En una escena **quieta** (noche fría, despejada, fondo parejo) la sd es chica,
el término estadístico cae bajo 0,003 y manda el piso. Ésa es justo la escena en que un foco chico en el cráter se
vería mejor, y el piso lo deja fuera aunque contraste 0,002 contra un fondo que no varía más que 0,0004.

Lo medido (§2) dice que **los dos frenos se tapan entre sí**: bajar sólo el piso (con s = 5) mueve poco porque en
cuanto el piso baja de 0,0015 manda el término estadístico; bajar sólo s (con el piso de hoy) mueve poco porque manda
el piso (el barrido S195). Y el piso que más frena es el de **ETI**, no el de NTI. Por eso esta palanca baja el piso
con s fijo en un valor intermedio (§3), y un CUMPLE sería **de la pareja (s_A, piso)**, no del piso solo.

## 2. Lo que se midió antes de fijar la grilla (sin reprocesar)

`experiments/_s196_lab_piso/medir_cruces.py` (salida `salida_medir_cruces.txt`) lee los records ya publicados de
producción (`data/mirova_equivalent`, vía, pasadas nocturnas válidas desde 2026-03-01, los 10 volcanes de la zona A,
última pasada 2026-11-23 07:40). Cada record guarda, por pase, mu y sd de NTI y ETI y la **celda decisiva** del 7 × 7
del cráter (la que más cerca estuvo de alertar, con sus contrastes). Para esa celda, si está en la zona A y no alertó,
el script calcula si alertaría con max(mu + s·sd, p) en NTI y ETI a la vez.

Es una **estimación de signo incierto**, no un conteo ni una cota. Subestima: el record guarda una sola celda, y otra
celda de la zona A podría cruzar (en VIIRS 375, 120 de 169 celdas de la zona A quedan fuera del 7 × 7; en
Tupungatito VIIRS 750, 155 de 204). Sobrestima: una celda que alerta no siempre publica, porque si su VRP sale
negativo el record queda con `vrp_mw` 0. La primera versión de este documento la llamaba «cota inferior»; el
verificador lo desmintió con la rama del barrido S195: Chillán MODIS_TERRA 2026-03-07 02:15 alerta en el brazo s = 1
(`n_p1` 1) con `primary_cluster.vrp_mw` -0,498 MW y `vrp_mw` 0, y el 2026-03-13 01:15 publica por otra celda
(fila 26, columna 27) que no era la decisiva.

**Control del instrumento** (§7 de la salida, A116): aplicado al barrido de s ya corrido (p = 0,003, s de 4,5 a 1,0,
Láscar, Chillán y Villarrica en marzo), predice las publicaciones nuevas reales: 0, 1, 2, 4, 4 y 4 de 0, 1, 2, 4, 4 y
4 para s de 4,5 a 2,0; en s = 1,5 acierta 4 de 4 con una predicha de más, y en s = 1,0 acierta 4 de 5 con una de más
y una de menos (los dos casos de arriba). Puede dar distinto de cero y acierta donde se puede comprobar. No está
validado con un brazo de piso, porque no existe ninguno.

Lo medido, con las cifras de la salida:

- **Qué piso manda con s = 5** (§2). Mediana de mu + 5·sd en NTI: 0,00398 (MODIS), 0,00394 (VIIRS 750), 0,00341
  (VIIRS 375), sobre 0,003; en ETI: 0,00212, 0,00190 y 0,00249, bajo 0,003. El piso de ETI manda en 4.332 de 5.538
  pasadas MODIS, 9.274 de 10.389 VIIRS 750 y 7.728 de 10.395 VIIRS 375; con p = 0,001 todavía manda en 321, 76 y 0,
  y con p = 0,0005 en ninguna.
- **Los frenos se tapan** (§3). Pasadas con alerta nueva en la zona A: sólo el piso (s = 5, p = 0,002), 327; sólo s
  (s = 3, piso de hoy), 217; los dos (s = 3, p = 0,002), 1.394. Con s = 5 la palanca del piso se separa entre 0,003
  y 0,0015 (0, 123, 205, 272, 327, 353 y 361) y se aplana después (362 en 0,00125, 0,001, 0,0005 y 0).
- **Bajar un solo piso no alcanza** (§4). Con s = 3 y p = 0,002: sólo NTI, 240; sólo ETI, 910; los dos, 1.394.
- **Tasa por noche negativa limpia** (§8; la unidad que vota, `tasas_barrido` del S194), en los siete pisos de la
  grilla (0,003 a 0,0015) y con piso 0:

  | s | 0,003 | 0,00275 | 0,0025 | 0,00225 | 0,002 | 0,00175 | 0,0015 | piso 0 |
  |---|---|---|---|---|---|---|---|---|
  | 5 | 0,0826 | 0,0962 | 0,1040 | 0,1112 | 0,1183 | 0,1222 | 0,1235 | 0,1242 |
  | 3 | 0,1151 | 0,1560 | 0,1795 | 0,2165 | 0,2536 | 0,3004 | 0,3355 | 0,3771 |
  | 2 | 0,1196 | 0,1684 | 0,2016 | 0,2588 | 0,3336 | 0,4421 | 0,5611 | 0,7939 |
  | 1 | 0,1209 | 0,1710 | 0,2048 | 0,2646 | 0,3485 | 0,4772 | 0,6216 | 0,9928 |

  Con s = 5 el 30 % no se alcanza nunca. Con s = 3 se cruza entre 0,002 y 0,00175, y aun sin piso la tasa se queda
  en 0,377: el término de 3 sigmas sigue frenando. Con s = 1 sin piso publica el 99 % de las noches: el umbral es,
  en la práctica, el piso fijo (s = 0 y s = 1 dan 258 contra 258 pasadas con el piso de hoy, §3).
- **Poder previsto** (§9; cuenta unidades S y N con el pareo sellado del S194, **sin leer ninguna alerta NHI**), en el
  brazo que elegiría la regla con la estimación:
  - s = 5: ningún volcán llega a 10 unidades S en ningún piso (máximo 8, Planchón-Peteroa y Chillán): SIN PODER.
  - s = 3, p = 0,002: votan 4 (Tupungatito 16/37, Planchón-Peteroa 25/31, Chillán 19/56, Chaitén 17/29); quedan
    fuera Láscar 4/19, Isluga 4/12, Llaima 3/91, Villarrica 6/70 y Copahue 5/118. CUMPLE exigiría exceso en los 4.
  - s = 2, p = 0,00225: votan 4 (Tupungatito 18/35, Planchón-Peteroa 20/36, Chillán 14/61, Chaitén 17/29).
  - s = 1, p = 0,00225: votan 5 (Tupungatito 18/35, Planchón-Peteroa 20/36, Chillán 15/60, Copahue 10/113 justo en
    el borde, Chaitén 17/29).

  Como la estimación es de signo incierto, estos conteos dicen el orden de magnitud, no quién vota.

**Hallazgo de paso sobre la línea base del S194.** Su `salida_medir_base.txt` informa 3,15 % de noches que publican
(81 de 2.568), pero cuenta como noche toda noche con alguna pasada negativa limpia. La unidad que vota en su
calibración (noche con alguna pasada negativa limpia y ninguna `pos` ni `far_ref`, publica si alguna pasada de la
noche publica) da para producción 127 de 1.538 noches, 0,0826. No cambia ningún criterio sellado; cambia una cifra
informada. Queda como seguimiento del S194.

## 3. La palanca

En las celdas de la zona A (región sensible BOX == 2 a no más de `inner_radius_km` del cráter, la de
`mascara_zona_a`), sólo de noche y en los dos pases contextuales, el umbral de NTI y el de ETI pasan a ser
**max(mu + s_A·sd, p_A)**, con los mismos mu y sd de toda la escena que usa producción. Fuera de la zona A el umbral
no cambia, pero el resultado sí puede cambiar por arrastre: una alerta nueva del primer pase sale del fondo del
segundo (`pob[excluidos] = nan` en `_pasada_contextual`), y eso mueve mu, sd y el fondo local de sus vecinas en toda
la escena. De día, en producción y en Cordón Caulle no cambia nada.

- **s_A = 3,0, fijo en todos los brazos de piso** (pregunta 1 a Nicolás, §11). Por qué 3: es el mayor s medido con
  el que la palanca del piso alcanza el 30 % dentro de la grilla (con s = 5 no lo alcanza y se prevé SIN PODER), y
  el menor que conserva el freno estadístico (sin piso, 0,377 de las noches, contra 0,794 con s = 2 y 0,993 con
  s = 1). s = 4 y 3,5 no se midieron. 3,0 es además un brazo de la grilla sellada del S194, así que el camino entero
  es monótono en «ver más»: de producción (5; 0,003) a (3; 0,003) por el tramo de s y de ahí a pisos menores.
- **Un solo p_A para NTI y ETI.** El .m usa el mismo 0,003 en los dos (n2 = e2), y bajar uno solo no alcanza (§2).
- **El mismo p_A en los tres sensores**, como producción, que usa 0,003 en MODIS, VIIRS 375 y VIIRS 750 (D36: MODIS y
  VIIRS 375 quedan en el valor de 750, sin medir por separado). Las tasas por sensor se informan, sin decidir.
- **Grilla:** p_A = 0,003, 0,00275, 0,0025, 0,00225, 0,002, 0,00175 y 0,0015. Con s = 3 cada paso separa al menos
  2,3 puntos de tasa por noche y 36 noches (§2), y el 30 % cae dentro con brazos a los dos lados. No baja de 0,0015:
  con s = 3 la tasa ahí ya es 0,3355 y bajo ella se aplana; y un piso 0 deja sin freno a una escena cuyo término
  estadístico no es finito (con la regla del .m el umbral sería el piso). La misma grilla sirve si Nicolás elige otro
  s_A: con s = 1 o 2 el 30 % cae entre 0,00225 y 0,002; con s = 5 no cae.
- **Guard S147:** p_A <= 0,003 y s_A <= 5, así que el umbral de la zona A nunca supera al de producción y el
  laboratorio nunca ve menos en el cráter.

## 4. Datos y ventanas

Los del S194 §2, sin cambios: records del laboratorio y de producción desde 2026-02-15, NHI de NHI-v1 `main`
(`docs/nhi_data/<Carpeta>/nhi_timeseries.json`), referencia de MIROVA bajada fresca y sólo para calibrar, desde
2026-03-01. Los 9 volcanes con serie NHI votan; Lastarria entra a calibración y persistencia; Cordón Caulle fuera.

## 5. Regla para elegir el piso (`evaluar.py calibrar`, `elegir_piso`)

- **Brazos.** `sin-zona` (el perfil `laboratorio` con la zona apagada), `control` (la zona encendida con s = 5 y piso
  0,003) y un brazo por cada p_A de la grilla con s = s_A, todos en la misma corrida y con el mismo código.
- **Medida.** La del S194 §5: `tasas_barrido` del evaluador S194, tasa de publicación por noche negativa limpia de
  volcán, tres sensores juntos (rige; respuesta 1 de Nicolás del 2026-11-22), con la tasa por pasada y por sensor
  informada sin decidir; ventana de calibración desde 2026-03-01.
- **Control de identidad, record a record** (en todos los records de los brazos, sin ventana). El brazo `control`
  tiene que ser idéntico al `sin-zona`: las mismas pasadas (volcán, sensor, hora) y, en cada una, el mismo `vrp_mw`,
  `distance_class`, `final_hotspot_lat`, `_lon` y `_dist_km`, `primary_cluster.vrp_mw`, `centroid_dist_km` y
  `n_pixels`, `n_abs`, `n_p1`, `n_p2` y `motivo_vacio`, y el bloque `s1` entero (mu, sd y umbrales de cada pase y la
  celda decisiva). Además sus cuentas tienen que ser exactamente las de producción (`data/mirova_equivalent`), como en
  el S194. Si s_A fuera 5, el brazo p_A = 0,003 es ese mismo brazo y tiene que cumplir lo mismo. Si falla: INVALIDO,
  porque la implementación cambia algo más que el umbral (geometría, fondo o ancla, S147 §5).
- **Control donde la zona no actúa.** En cada brazo de piso, los records de día (`dayflag` 1), los que no pasan por la
  vía y los de Cordón Caulle (si el brazo los trae) tienen que ser idénticos a los del `sin-zona`, con la misma firma.
  Es lo único que vigila una fuga del piso fuera de la zona, porque en el brazo `control` el piso vale lo mismo dentro
  y fuera. Si falla: INVALIDO.
- **Otros controles.** La tasa no puede bajar a lo largo del camino `control`, 0,003, 0,00275, ... 0,0015 (INVALIDO).
  Al menos 30 noches negativas limpias en cada brazo (si no, SIN PODER). Falta un brazo: INVALIDO.
- **Regla.** Si `control` ya supera 30 %: SIN VALOR, a Nicolás. Si el brazo (s_A; 0,003) ya supera 30 %: SIN VALOR DE
  PISO: el valor está en el tramo de s entre 5 y s_A, que este barrido no corre; se lleva a Nicolás con la
  recomendación de correr los brazos 4,5, 4,0 y 3,5 con la regla sellada del S194 §5. Si no, el valor es (s_A, el
  **menor p_A** de la grilla cuya tasa por noche no supera 30 %), con la comparación entera 10·publicadas <=
  3·negativas (30 % exacto cumple). Si se queda en 0,003, el estado lo dice («el piso de hoy: sólo actúa el s de la
  zona A»); si llega a 0,0015, también («el piso de la grilla»), para que nadie lea un extremo como una calibración.

## 5b. Re-sello S200 (2026-11-25): cuatro controles corregidos antes de evaluar

**Cuándo y por qué.** La ronda 4 de la auditoría externa con Codex (frente D) y un verificador Claude de contexto limpio
que la reprodujo con el `calibrar` y el `tasas_barrido` reales encontraron que, tal como estaba sellado, el evaluador
podía elegir un piso sin poder sostenerlo o salir inválido por construcción
(`experiments/_s196_lab_piso/PROPUESTA_RESELLO_S199.md`, #1123). Nicolás decidió re-sellar el 2026-11-25. **Nadie ha
corrido `calibrar` sobre el barrido**: abril, mayo y junio están cerrados y contados por brazo con
`contar_brazos_piso.py` (records por volcán, cuántos publican y cuántos publican que el control no), sin etiquetar
negativos limpios contra MIROVA, sin tasa por noche y sin elección. Esos conteos se vieron (los dejó la cadena del
barrido); por eso este re-sello no toca la regla, la grilla ni la tasa objetivo: sólo arregla controles cuyo defecto
es mecánico y no depende de ningún número del barrido. Lo que no cambia: los brazos, la grilla, s_A, la medida,
la tasa objetivo, la unidad, la regla de elección (`elegir_piso`, intacta) y la vara del S194.

**Qué cambia** (todo en `calibrar`; pruebas en `tests/test_lab_piso_resello_s200.py`, que fallan con el evaluador
sellado en S196):

- **R4FD-V201, producción contada como la guarda el laboratorio.** Desde el 2026-11-15 12:30 UTC producción guarda las
  pasadas MODIS de día y el almacén del laboratorio las rechaza, así que el control «el brazo `control` da las cuentas
  de producción» salía INVALIDO con cualquier ventana que llegue hasta hoy (con fin 2026-11-20, un control perfecto
  daba en MODIS 5.117 negativos contra 5.217). Ahora producción se cuenta sin los records que el almacén del
  laboratorio habría rechazado: la misma función `pipeline/store.py::_reject_daytime` con el flag del perfil
  `laboratorio` y las coordenadas de `volcanoes.yaml`. El control sigue completo y la ventana no se corta; una
  diferencia de noche sigue invalidando. La salida dice cuántos records se quitaron por volcán.
- **R4FD-101, todos los brazos con las mismas pasadas.** Si un brazo pierde pasadas que otro tiene (un trozo que muere a
  mitad de la lista, un brazo que cae un día), su tasa cambia y la elección también (caso medido: 17 noches perdidas en
  0,00175 cambiaban 0,002 por 0,00175 con estado ELEGIDO). Ahora todos los brazos tienen que cubrir exactamente las
  mismas pasadas (volcán, sensor, hora) dentro de la ventana de calibración, con el `sin-zona` de referencia. Si no:
  INVALIDO, con cuántas faltan y sobran por brazo.
- **R4FD-102, la identidad donde la zona no actúa necesita poder.** Ese control se apoyaba casi entero en Cordón Caulle
  y sin ese volcán comparaba cero records y aun así decía idéntico. Ahora, con menos de 30 records comparados en algún
  brazo (el mismo umbral de poder de este §5), SIN PODER.
- **R4FD-105, el mismo código en todos los brazos.** En cada pasada todos los brazos tienen que traer el mismo
  `regimen.codigo_sha`; si no, INVALIDO. Entre tandas el código puede cambiar (cada mes se despacha aparte) y se
  declara en la salida cada código con el tramo de fechas que cubre.
- **R4FD-106 (gravedad 2), una sola bajada de la referencia.** La referencia de MIROVA se baja una vez para todos los
  brazos y producción, y la salida guarda el sha256 de los dos CSV.

**Orden de los controles.** Primero los que invalidan (cobertura, código, identidad del `control`, fuga donde la zona
no actúa, cuentas de producción) y después el de poder; con todos en verde rige la regla del §5 sin cambios.

**No entra en este re-sello** (gravedad 2, quedan declarados): R4FD-104 y R4FD-V202 (la recolección y `reproc_brazos.py`
no dejan escrito qué brazo cayó y en qué día; con R4FD-101 un brazo caído ya invalida, aunque el informe no diga por
qué cayó), R4FD-108 (cero unidades NHI lanzan excepción en vez de SIN PODER; está en el evaluador S194, que es la vara y
no se toca aquí) y R4FD-111 (la calibración exige el JSON de Cordón Caulle; hoy todos los brazos lo traen).

**S200b (2026-11-25, misma decisión, todavía antes de evaluar).** Un verificador Claude de contexto limpio revisó #1129
con su propio instrumento (28 escenarios con el `tasas_barrido` real del S194;
`D:\vrp-trabajo\temporales\s200\verif_1129\VEREDICTO.md`, fuera del repo) y confirmó los cinco arreglos. Dejó efectos
no buscados; se corrigen tres, ninguno de los cuales cambiaba un ELEGIDO:

- **SIN PODER ya no tapa un INVALIDO.** Si `elegir_piso` dice INVALIDO (por ejemplo, tasa no monótona: el instrumento
  está roto), ese estado manda aunque falte poder donde la zona no actúa.
- **El poder cuenta sólo records de la ventana de calibración** donde la zona no actúa (la identidad sigue mirando
  todos). Antes, 40 records de enero daban poder a una ventana que empieza en marzo.
- **Costo.** La regla de día y las coordenadas se cargan una vez por corrida y no en cada record (el verificador midió
  unos 82 minutos sobre producción entera).

Quedan declarados: R4FD-102 depende en la práctica de Cordón Caulle (en junio, Láscar no trae ningún record de día ni
fuera de la vía), así que excluir ese volcán, como permite R4FD-111, deja al barrido sin poder para elegir; un brazo
sin `regimen` en todos sus records pasa el control de código (hoy todos los records reales lo traen); un brazo
relanzado con el mismo código y otro gránulo (NRT contra estándar) no se detecta, porque el defecto original no lo
pedía; y se guarda el sha256 de los CSV de MIROVA, no el commit remoto del que vinieron.

**S200c (2026-11-25): el fin de la ventana, sellado (R4FD-107).** La auditoría mostró que, con las mismas carpetas, el
fin de la ventana decidía el piso (fin 2026-05-31: 0,0025; 07-31: 0,00225; 11-20: 0,002), y el evaluador aceptaba
cualquiera (por defecto, el día en que se corriera). Quien evalúa podía elegir el fin mirando el resultado. El acta de
cierre de la ronda 4 (`docs/ACTA_CIERRE_AUDITORIA_CODEX_RONDA4_2026-11-25.md`), aprobada por Nicolás el 2026-11-25, fija
el fin en **2026-11-23**, el último día de la última tanda despachada del barrido, antes de mirar ningún resultado. Con
otro fin `calibrar` sale INVALIDO sin cargar ni contar nada, y la línea de comandos usa el sellado por defecto. La
salida guarda además el sha256 de cada archivo leído de cada brazo, para que la muestra evaluada quede identificada.
El inicio de la ventana (2026-03-01) no cambia.

## 6. La vara, sin cambios

El veredicto es el del S194 §3 y §4, con la misma función (`evaluar.veredicto` es `E.veredicto` del S194): clases de
noche S, N, A y P con el predicado del tablero ejecutado con node; pareo de escenas NHI con la noche D, D+1, D-1;
permutación de una cola estratificada por nubosidad, 10.000 permutaciones, semilla 194; SIN PODER con menos de 10
unidades S o N; control con las fechas NHI corridas +15 y -15 días, nulo con a lo más 1 volcán en exceso por
desplazamiento; persistencia por sorteo temporal; INVALIDO con más de 5 % de noches con cobertura desigual; CUMPLE con
exceso en al menos 4 de 9 volcanes y persistencia que supera el sorteo; re-evaluaciones de SIN PODER a lo más dos, la
primera no antes del 2027-02-21. Lo que hace cada resultado es lo del S194 §4. `evaluar.py evaluar` y `poder` llaman
al evaluador S194 tal cual.

## 7. Lo que cambia respecto del S194, y por qué

| qué | S194 | aquí | por qué |
|---|---|---|---|
| parámetro | s de la zona A | p_A, con s_A = 3 fijo | el barrido de s se aplanó porque manda el piso; el piso solo tampoco alcanza (§1, §2) |
| grilla | s = 5 a 1 | p_A = 0,003 a 0,0015 | se separa con s = 3 y contiene el 30 % (§2, §3) |
| control | brazo s = 5 con las cuentas de producción | brazo (5; 0,003) idéntico record a record al brazo sin zona, más las cuentas de producción, más identidad donde la zona no actúa | con s_A = 3 el primer brazo de piso no es producción; la identidad por record es más fina que por cuentas; el piso puede filtrarse fuera de la zona |
| monotonía | a lo largo de s | a lo largo de control, pisos | el camino sigue siendo uno solo |
| estado nuevo | | SIN VALOR DE PISO | si (3; 0,003) ya supera la tasa, el valor está en el tramo de s |
| tasa, unidad, ventanas, mínimos, vara | | sin cambios | lo aprobado por Nicolás (D5 y respuestas del 2026-11-22) |

## 8. El verificador con contexto limpio: cinco debilidades y qué hice con cada una

Un subagente sin el contexto de esta sesión leyó el pre-registro, el evaluador, las pruebas, la medición y el código
del detector, y comprobó las cifras contra la salida (todas coincidían). Encontró cinco debilidades.

**Debilidad 1. La «cota inferior» no era cota.** Lo mostró con la rama del barrido S195 (los dos casos de Chillán del
§2). **Qué hice:** lo comprobé en la misma rama, cambié el texto a «estimación de signo incierto» aquí y en el
script, expliqué los dos mecanismos y dejé dicho que el poder previsto da un orden de magnitud, no quién vota.

**Debilidad 2. Con s_A = 1 la palanca deja de ser «del piso».** Con s = 1, 1.021 de los 1.293 cruces en p = 0,00225
existen sólo porque s bajó de 5 a 1, y s = 0 casi no se distingue de s = 1: el umbral de la zona sería el piso fijo
en toda escena, también en las revueltas que el término estadístico protege. **Qué hice:** medí s = 3 y s = 2 y cambié
el sello a s_A = 3 (§3), que conserva un test de 3 sigmas (sin piso, 0,377 de las noches) y todavía alcanza el 30 %.
Dejé escrito en el §1 que un CUMPLE sería de la pareja, y la pregunta 1 lleva las tres opciones con sus números.

**Debilidad 3. El control de identidad no podía atrapar una fuga del piso.** En (5; 0,003) el piso de la zona vale lo
mismo que el de producción, así que un piso que se aplicara de día o fuera de la zona no se vería; y la frase «fuera
de la zona A nada cambia» era falsa por el arrastre del pase 1 al pase 2. **Qué hice:** agregué el control «donde la
zona no actúa» (§5, `zona_no_actua` y `identidad_donde_no_actua` en `calibrar`), corregí la frase del §3 y agregué
al §9 las pruebas de código «no actúa de día» y «nunca fuera de la zona en el pase 1» para el piso.

**Debilidad 4. `calibrar` no tenía ninguna prueba.** Una mutación que apagaba el control de identidad dentro de
`calibrar` dejaba pasar todo. **Qué hice:** cinco pruebas de `calibrar` entero con carpetas sintéticas y
`tasas_barrido` reemplazado (sano; control distinto sólo en un umbral del bloque `s1`; brazo de piso que cambia un
record de día; brazo de piso que cambia la noche, que es lo esperado; cuentas distintas de producción) y cuatro
mutaciones nuevas en `mutar.py` (sin identidad, sin el control donde no actúa, sin cuentas, `zona_no_actua` con la
noche en vez del día).

**Debilidad 5. SIN VALOR DE PISO remitía a una regla que este documento reemplaza y a brazos que no se corren.**
**Qué hice:** el estado ahora dice que el valor está en el tramo de s entre 5 y s_A, que este barrido no corre, y se
lleva a Nicolás con la recomendación concreta (brazos 4,5, 4,0 y 3,5 con la regla del S194 §5).

**Menores.** La firma no incluía mu, sd ni umbrales de cada pase: ahora incluye el bloque `s1` entero (y una mutación
lo vigila). La identidad se revisaba sólo desde 2026-03-01: ahora se exige en todos los records de los brazos.

## 9. Código que falta (paso siguiente; necesita tag y el sí de Nicolás, A45)

Nada de esto se toca en este PR. Para correr el barrido hace falta:

1. `pipeline/mirova_v750_codigo.py::_pasada_contextual` y `detectar_mirova`: un parámetro `piso_a` además de `s_a`.
   En la zona A, `u_ntiA = max(mu + s_a·sd, piso_a)` (o `piso_a` si el término no es finito) y lo mismo en ETI con
   `piso_a`. Guard: error si `piso_a > n2` o `piso_a > e2` o `piso_a <= 0`, como hoy con `s_a > s2`. Con `s_a == s2`
   y `piso_a == n2 == e2` los umbrales son los mismos floats que producción, así que el resultado es idéntico bit a bit.
2. `pipeline/profile.py` y `pipeline/profiles/laboratorio.yaml`: la clave `laboratorio_zona_a.piso` (por defecto,
   el piso de producción) junto a `valor`; `calcular_vrp_granulo` la pasa al detector.
3. `diag_s1`: guardar `u_ntiA` y `u_etiA` en el record (hoy el diagnóstico los calcula pero no los persiste), para
   que una medición posterior vea el umbral que de verdad se usó.
4. Pruebas: identidad bit a bit con (5; 0,003); guard; monotonía en un caso sintético; el piso no actúa de día y nunca
   fuera de la zona en el pase 1 (los análogos de `test_p4_la_zona_no_actua_de_dia` y
   `test_p6_monotono_al_bajar_s_y_nunca_fuera_de_la_zona` de `tests/test_laboratorio_paso3_s195.py`); el guard S147 extendido al piso; el perfil
   `mirova_equivalent` nunca enciende la zona (G4 de `tests/test_laboratorio_paso1_s193.py`).
5. El workflow del barrido de S195 con los brazos de §5 (sin-zona, control, siete pisos).

## 10. Cómo se probó el instrumento antes de tener datos

- `tests/test_lab_piso_preregistro_s196.py` (en CI): la regla en sus bordes (30 % exacto; SIN VALOR; SIN VALOR DE
  PISO; piso de hoy y piso de la grilla rotulados; no monótona, también con el control; brazo o control faltante; 29
  y 30 negativos; rige la noche; s_A = 5 da SIN EXTENSION y exige el primer piso igual a producción); el control de
  cuentas; la identidad record a record (una diferencia en cualquiera de los campos, una pasada faltante y el vacío
  la rompen); `calibrar` entero con carpetas sintéticas (cinco casos); la vara es la función del S194 y su archivo es
  el sellado; `evaluar` y `poder` delegan; y cuatro pruebas de sello (valores, hash propio, hash del S194, piso y s
  leídos de `detectar_mirova`).
- `experiments/_s196_lab_piso/mutar.py` (salida `resultado_mutaciones.json`): 25 mutaciones del criterio sobre
  copias del evaluador, corridas sin las pruebas de sello; cuenta como atrapada sólo la que hace fallar una prueba
  por aserción sin errores. Control sano: pasa entero. Control de caída: una mutación que rompe la carga del módulo
  sale NO atrapada (con error), así que el contador no cuenta caídas como aciertos (lección S152).
- La validación de `medir_cruces.py` contra el barrido de s (§2).

## 11. Preguntas para Nicolás

1. **¿s_A = 3 (recomendado), 1 o 5?** Con 3 se conserva un test de 3 sigmas y la regla, con la estimación, elegiría
   p = 0,002 con 4 volcanes que votan (CUMPLE exigiría exceso en los 4). Con 1 votarían 5, pero el umbral de la zona
   pasa a ser casi un piso fijo en toda escena. Con 5 la palanca es «el piso solo» y el brazo del piso de hoy es
   producción, pero no vota ningún volcán (SIN PODER casi seguro). Si eliges 1 o 5, se cambia `S_A` y se re-sella
   antes de correr nada; la grilla no cambia.
2. **¿Autorizas el cambio de código del §9 con tag defensivo?** Toca `pipeline/mirova_v750_codigo.py` (A45).
3. **¿El barrido corre entero (10 volcanes, desde 2026-03-01) o por tandas como el de s?** Son nueve brazos.

Respuestas (2026-11-23, ~12:30 UTC), dadas por Nicolás en la sesión coordinadora S196 y transmitidas a esta sesión
por la coordinadora (no las leí de primera mano). Textual de las opciones que eligió: (1) «s = 3 (Recomendado)»; (2)
«Sí, A45 (Recomendado)»; (3) «Por tandas (Recomendado)». La 1 confirma lo sellado: `S_A = 3.0` no cambia, así que el
evaluador y su sha256 quedan iguales y no hay re-sello. La 2 autoriza el cambio de código del §9 con tag defensivo,
en un PR aparte. La 3 fija que el barrido se despacha por tandas, como el de s.

## 12. Archivos

| archivo | qué es |
|---|---|
| `experiments/_s196_lab_piso/PREREGISTRO.md` | este documento |
| `experiments/_s196_lab_piso/evaluar.py` | evaluador sellado (`calibrar`; `evaluar` y `poder` del S194) |
| `experiments/_s196_lab_piso/medir_cruces.py` | medición del §2, sólo lectura |
| `experiments/_s196_lab_piso/salida_medir_cruces.txt` | su salida (referencia de MIROVA y su sha en la §8 de la salida; NHI-v1 en `4d24515abe1e`) |
| `experiments/_s196_lab_piso/mutar.py`, `resultado_mutaciones.json` | control de mutaciones y su salida |
| `tests/test_lab_piso_preregistro_s196.py` | pruebas del evaluador |
