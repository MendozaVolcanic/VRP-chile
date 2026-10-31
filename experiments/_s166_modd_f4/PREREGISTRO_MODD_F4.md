# Pre-registro S166 MOD-D fase 4: la vía «código MIROVA» de MODIS contra K, con los tres brazos de posición

Estado: **SELLADO** (2026-10-29, S168; tag `s168-modd-f4-sellado`). Condición de Nicolás cumplida: mutaciones atrapadas
por aserción (82 de 82, ninguna con escenarios que caen; M70 declarada en el §13 ter), control de caída CAE, §13 al
día y el tercer verificador limpio (`experiments/_s168/modd_f4_verificador/INFORME.md`, Sonnet) sin hallazgos de
gravedad 3. Lo que quedó de gravedad 1 y 2, en el §13 ter. El sello cubre las reglas y el evaluador; el candado del
§11 sigue pendiente y nada se despacha sin él. Texto original del estado:
BORRADOR para el sello de Nicolás. Escrito el 2026-10-28 por la sesión hija de MODIS de la fase 4 (reporta
a la coordinadora S166), antes de correr ningún brazo y sin mirar ningún resultado nuevo. Nada se despacha antes del
sello, del candado del §11 con su verificador limpio, del tag y del sí de Nicolás; nada se enciende en producción sin
el reproceso verificado y otro sí (A45). Rutas relativas a la raíz del repo,
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\`.

Programa: `docs/superpowers/specs/2026-10-24-programa-replica-por-sensor.md` §5 (MOD-D) y §7 (fase 4 y regla de
posición), en la rama `loop/activo`. Antecedentes que este documento hereda sin reabrir:
- El pre-registro sellado del censo MOD-D (`experiments/_s162_modis_paquete/PREREGISTRO.md`, tag `s162-modd-tag`,
  sello D-48 del 2026-10-24), sus reglas P1, P1b, P2, M y la prueba de Chillán.
- El resultado del censo (rama `claude/s162-modis-2-0dd578`, `experiments/_s162_modis_paquete/censo/`, verificado):
  DECIDE NICOLÁS, y la decisión de Nicolás del 2026-10-26: «Apruebo MOD-D como CANDIDATO: lleva la vía a pipeline/
  con la regla de MATLAB, flag apagado, tag defensivo antes del primer edit.»
- La vía en `main`, apagada (#919, `d94f25191`): `ENABLE_MODIS_CODIGO_MIROVA` en `pipeline/profile.py`, el bloque de
  `pipeline/process_modis.py` y `FAMILIAS["MODIS"]` de `pipeline/mirova_v750_codigo.py`.
- La decisión de Nicolás del 2026-10-27 (programa §7): «Sí: no fijes la regla todavía; mídela como brazo (radiante,
  cercano y pico) en los A/B de cada sensor contra lo que publica MIROVA».
- La medición de S165 de la regla de posición (`experiments/_s165_regla_posicion/INFORME.md` y `verificador/`, en
  `loop/activo`).
- Como modelo de un A/B de fase 4 con los tres brazos: `experiments/_s162_v750a/PREREGISTRO_V750A.md` (rama
  `claude/s162-viirs750-2-918174`, borrador sin sellar).

## 1. Qué se mide y por qué, como geólogo

De noche el cráter de Láscar o de Chillán es una fracción mínima de un píxel MODIS de 1 km, y más mínima todavía
cuando el satélite lo mira de lado (a 58° de cenit el píxel mide más de 2 × 5 km). MIROVA lo detecta interpolando el
gránulo a una grilla fija de 1 km alrededor del volcán, comparando cada celda con su entorno por NTI y ETI, midiendo
el fondo por interpolación debajo de un halo y sumando la radiancia de todas las celdas alertadas. El censo MOD-D
midió que hacer eso mismo (el código de MIROVA llevado a MODIS) se equivoca menos que K contra MIROVA (8 errores
contra 49 bajo 1 MW y en noches sin actividad) y lleva la magnitud de Láscar de la mitad de MIROVA a la de MIROVA.

Lo que el censo midió fue un **port** en un arnés de experimento, corrido sobre grillas que el propio arnés armó. La
fase 3 metió esa lógica en `pipeline/` y probó que da lo mismo **sobre esas grillas** (5.321 de 5.321 pasadas), pero
no pudo probar el camino de punta a punta, porque pyhdf no corre en Windows y el censo no guardó los gránulos (#919,
«Lo que NO cubre»). Este A/B mide tres cosas que todavía nadie midió:

1. **Que la vía del pipeline, leyendo el HDF y el MxD03 con las funciones de producción, ve lo mismo que el censo.**
   Si la lectura o el remuestreo difieren, la vía no es la que Nicolás aprobó (equivalencia, §8.2).
2. **Que la vía, tal como quedaría en producción (el record que deja `store.append_record` y el predicado del
   tablero), publica lo que MIROVA publica y calla donde calla mejor que K**, sin perder una alerta protegida, sobre
   el censo y sobre los diez días que vinieron después (§4).
3. **Desde dónde se mide la distancia al cráter.** La vía decide si un record es «cumbre» por la distancia del
   centroide del cúmulo más radiante. Eso importa en una sola escena: un píxel débil junto al cráter y una fuente más
   radiante lejos. Con «radiante» el record queda lejano y el tablero calla; con «cercano» queda en la cumbre y el
   tablero publica la suma, que viene mayormente de la fuente lejana; con «pico» manda el píxel más radiante solo. La
   vara es lo que hizo MIROVA en esas escenas, incluidas las pasadas en que publicó la fuente lejana como
   `FALSO_POSITIVO` (§6 bis).

**Lo que decide**: si se propone a Nicolás encender la vía en `mirova_equivalent` (con la posición que gane), si se
dice que no, o si la decisión es suya con la lista en la mano. **No adopta nada** (A45).

### Honestidad sobre lo que ya se sabe

Este A/B es **confirmatorio**: el censo ya midió casi todo con el port, y la vía reproduce al port en las grillas del
censo. Lo que puede salir distinto es el camino desde el HDF, la cola de octubre y la posición. Las predicciones del
§10 se escriben para que el resultado pueda contradecirlas.

## 2. Brazos

| brazo | qué es | papel |
|---|---|---|
| **K** | `process_modis.calculate_vrp` en el commit del tag del candado, perfil `mirova_equivalent` sin tocar (todos los flags como en producción, apagados), seguido de `store.append_record` sobre un directorio temporal | control |
| **V** | la misma llamada con `process_modis.ENABLE_MODIS_CODIGO_MIROVA = True` en memoria y nada más (los tres flags del MxD03 de #920 siguen apagados: la vía lee su propio MxD03). Posición «radiante»: centroide del cúmulo 8-conexo de la alertada más radiante, que es lo que hace hoy `procesar_grilla` | la palanca |
| **V-cercano** | el record de V con la distancia del alertado más cercano al cráter | brazo de posición |
| **V-pico** | el record de V con la distancia del alertado de mayor radiancia MIR | brazo de posición |
| **placebo** | el record de K con toda magnitud por 1,2 | control de cableado de M (D-28) |
| **V-grilla** | fuera de línea: `procesar_grilla` de la misma vía sobre la grilla 51 × 51 que guardó el censo MOD-D para esa pasada | sólo identidad (§8.2) |

**Los tres brazos de posición comparten detección, VRP y píxeles.** Sólo cambia la distancia al cráter, y con ella
`distance_class`, `primary_cluster.centroid_dist_km` y `final_hotspot_dist_km` (`variante_posicion` del evaluador, la
misma regla de `comun.variante` de S165). Las tres distancias se miden **desde el cráter** con la posición
fraccionaria que usa la vía (`posicion_de(grilla, get_detection_anchor)`), con la misma frontera inclusiva
(`summit` si la distancia es menor o igual que `inner_radius_km`). La celda de referencia de MIROVA (D15) no se usa
como origen: S165 ya cotejó las dos y la vía mide desde el cráter. Cada variante pasa por `store.append_record` en el
runner, como en producción.

## 3. Por qué no hay más brazos

El censo ya informó PM-geo5 (MxD03 dentro del paquete: sin él se pierden 3 protegidas), PM-sens (la caja) y K33 (D33):
no se repiten. D28 (bow tie) sigue fuera hasta localizar el método de MIROVA (MOD-E). La caja y el corte de cobertura
de 5 km son los de `FAMILIAS["MODIS"]` en `main`.

## 4. Población y ventanas

- **Tramo C (censo)**: las 5.465 pasadas MODIS nocturnas de `experiments/_s162_mxd03/poblacion.json` (en `main`), en
  sus 1.232 gránulos, del 2026-03-01 al 2026-10-16. El arnés pide **por nombre** el mismo L1B y el mismo MxD03 que usó
  el censo (campos `l1b` y `geo` de cada fila); si LAADS ya no los sirve, baja el vigente y la pasada queda marcada
  `otro_granulo` (cuenta para la identidad, §8.2).
- **Tramo E (cola)**: las pasadas MODIS nocturnas de los 11 Tier A del 2026-10-17 00:00 al 2026-10-26 23:59 UTC,
  armadas con la misma regla que C (`experiments/_s162_mxd03/poblacion_mxd03.py` con la ventana como único cambio).
  Por qué esa cola: incluye la tercera pérdida MODIS de Chillán del #915 (2026-10-25 07:20, 58° de cenit), que quedó
  fuera del censo. Por qué termina el 26: la referencia congelada es del 2026-10-27 21:21 UTC y las pasadas del 27
  pueden no estar todavía en la tabla.
  - Los días 17 a 20 de octubre son los que D-29 sacó porque CMR no servía MOD021KM. Medido hoy, 2026-10-28 04:00
    UTC (`cmr_cola.py`, `cmr_cola_salida.txt`, por versión, de 00 a 12 UTC en la caja de Chile): CMR lista la versión
    6.1 estándar, que es la que pide `pipeline/fetch.py` primero, del 17 al 26 de octubre, con tantos MxD03 como L1B en
    cada día y plataforma (2 a 7 gránulos). El listado no basta: CMR puede listar entradas que dan 404 al bajarlas
    (commit `798400dec`, el 12-oct de S159) y el verificador vio cambiar una fila del listado en una hora (VF4-07). Por
    eso **«sirve» quiere decir que, al armar la población, una petición HEAD a la URL de descarga del L1B y a la de su
    MxD03 responde 200 para cada volcán y pasada nocturna del día**. Un día que no cumpla se excluye entero en todos
    los brazos y se declara en la primera línea del resultado (como D-29). Esta comprobación se hace y se guarda antes
    del sello de la lista de días, junto con la población. Las pasadas de MIROVA de un día excluido **no** se sacan de
    `sin_pasada_nuestra`: quedan sin pareja, la cobertura queda en rojo sólo en E y el protocolo del §7 saca E entero
    (N-04 de la segunda vuelta). Es la lectura conservadora: una alerta de MIROVA, quizá protegida, no desaparece sin
    declararse, y el costo es perder la cola de diez días.
  - CMR sirve además una Collection 7 de LAADS (versión `7`) en paralelo. Ni K ni V la piden (`fetch.py` pide 6.1 y cae
    a 6.1NRT): los dos brazos leen el mismo archivo y la colección no los separa. Que MIROVA haya pasado a la 7 es SIN
    DATO.
- **Cortes informados, que no separan brazos** (A104): los dos brazos se recalculan con un mismo código en todas las
  fechas, así que ninguna frontera de producción cae entre ellos. Se informan por tramo C y E; #535 (2026-08-28
  23:00 UTC) y la adopción de K (2026-10-18 09:57 UTC) sólo importan al control K = producción (§8.1), que compara
  contra lo que producción escribió en cada fecha.
- **A119**: MODIS desde marzo, sin reparos de cobertura de la tabla. Enero y febrero no entran.

## 5. La vara: lo que publica MIROVA

- **Referencia congelada** posterior al cierre de D-39 (el consolidado ganó 2.648 filas el 2026-10-27, 23 protegidas
  de todos los sensores; `tasks/LOOP_OBJETIVOS.md` de `loop/activo`, entrada del 2026-10-27 12:46 UTC): consolidado de Mirova-v1 en el commit `cb91eb506c37cff0b83164dd602d8a5340277637`
  (2026-10-27 21:21:07 UTC) y OCR en `cfc57c4d8bc57c5ccd5219ff3a91749dae167b97` (2026-10-27 13:06:30 UTC), las mismas
  copias que usó S165 (`experiments/_s165_regla_posicion/referencia_salida.txt`). Su sha256 queda en el manifiesto del
  candado antes del despacho.
- **Etiquetas** con `poblacion_mxd03.py` sobre esa referencia, sin otro cambio: `protegida` (lectura A, alerta de 1 MW
  o más, pareo ±120 s), `bajo1`, `neg_limpio` (MIROVA miró y todas sus filas son RUTINA), `far_ref` (MIROVA publicó la
  fuente como `FALSO_POSITIVO` y ninguna ALERTA) y `sin_info`. La regla SN es de VIIRS 375 y no cambia nada en MODIS.
- **Por qué se re-etiqueta C** y no se usan las etiquetas selladas del censo: la tabla sellada es anterior a D-39 y le
  faltaban filas, entre ellas protegidas de Láscar. Las pasadas de C cuya etiqueta cambia contra la del censo se
  listan (informa).
- **Canal (A119)**: cada pasada lleva dos etiquetas: `lab`, con la tabla sola, que **decide** todo (P1, P1b, P2, P2',
  M, Chillán y curvas); y `lab_union`, con tabla más OCR, que **informa** (P2 con la unión, en `p2_union`). Única
  excepción: una protegida de la unión que no es protegida de la tabla («sólo OCR») y que el brazo pierde no veta,
  pero lleva el veredicto a DECIDE NICOLÁS (§7), porque perder una alerta de 1 MW o más no se deja pasar en silencio
  aunque venga del canal menos creíble. Así lo pedía ya el texto del sello de MOD-D («tabla sola decide»), aunque su
  evaluador usaba la unión (VF4-05).

## 6. Pruebas

Todo por pasada MODIS, «publica» y magnitud mostrada = el predicado de `frontend/index.html` ejecutado con node
(`banco_paridad.correr_node`, A97) sobre el record que dejó `store.append_record`. Las piezas estadísticas se importan
sin copiar de `experiments/_s157_prereg_d25/evaluar_d25.py`, blob `1dbabf65` (el mismo que usó el censo MOD-D):
`prueba_signos_p2` y `regla_signos_p2` (D-45), `pesos_bloque`, `regla_m` y `comparar_con_ganancia` (D-28). Bloque =
noche-volcán.

| prueba | qué cuenta | regla |
|---|---|---|
| **P1 veto** | protegidas que K publica y el brazo no (protegida de la tabla; las de la unión que no lo son de la tabla, aparte) | una de la tabla: el brazo no es elegible (§6 bis), y si ninguna posición queda elegible el veredicto es NO ADOPTAR; sólo OCR: DECIDE NICOLÁS |
| **P1 lista** | protegidas que ni K ni el brazo publican | se listan, no deciden |
| **P1b** | protegidas que los dos publican, con K ≥ 1 MW y el brazo < 1 MW | una o más: DECIDE NICOLÁS. La contraria (K < 1, brazo ≥ 1) se lista |
| **P2** (sellada en MOD-D) | E = alertas bajo 1 MW sin publicar + publicaciones en negativos limpios; +1 si el error es sólo del brazo, −1 si es sólo de K | `regla_signos_p2`: GANA, PIERDE, BLOQUEA, EMPATE, SIN SUSTRATO (4 bloques o menos) |
| **P2'** (nueva) | E + E_lejana: publicaciones del brazo en pasadas `far_ref` | la misma prueba sobre E + E_lejana |
| **M** | alertas (protegida o bajo 1 MW) que K y el brazo publican: d = abs(log10(B/MIROVA)) − abs(log10(K/MIROVA)) | `regla_m`: sólo EMPEORA decide (DECIDE NICOLÁS); d′ contra la ganancia pareja informa |
| **Razón** | mediana de brazo/MIROVA en todas las protegidas que el brazo publica, publique K o no | informa, con la marca de si cae en [0,9; 1,1] (§12, decisión 4) |
| **Curvas de cenit** | razón brazo/MIROVA y K/MIROVA por tramo de 10°; y en cada noche-volcán con dos alertas separadas por 10° o más, razón más oblicua sobre menos oblicua del brazo y de MIROVA | informan: se busca reproducir la curva de MIROVA, no aplanarla |

P2 y P2' se calculan sobre C ∪ E y se informan también por tramo, y P2 también con las etiquetas de la unión
(`p2_union`, informa).

**Soporte independiente (informa; adenda 1 del sello, VF4-10)**: al leer el resultado, a cada publicación de V en un
negativo limpio de C ∪ E se le aplica la función sellada `soporte_independiente` de `evaluar_paquete.py` (tag
`s162-modd-tag`): si otro sensor la ve la misma noche en otro gránulo, a 6 h o menos, es candidata al perfil
experimental. No cambia P2, que sigue contando toda publicación en un negativo limpio como costo para la réplica.

**Qué cambia respecto de las reglas selladas de MOD-D** (todo lo demás se conserva tal cual):

| pieza | sellado de MOD-D | aquí | por qué |
|---|---|---|---|
| brazo que decide | PM (el port) | V con la posición del §6 bis | la vía del pipeline es lo que se encendería |
| vara | etiquetas de la referencia del censo | las de la referencia posterior a D-39 (§5) | a la del censo le faltaban filas |
| canal | el texto decía «tabla sola decide», pero el evaluador usaba la unión con el OCR | decide la tabla sola, como decía el texto; la unión informa | A119 (VF4-05) |
| P1 | toda pérdida veta | una pérdida sólo OCR va a DECIDE NICOLÁS | el OCR es la parte menos creíble (§12, decisión 5) |
| P2 | sólo E | P2 y P2', decide la peor de las dos (§7) | decisión de Nicolás del 2026-10-27 (§12, decisión 3) |
| fila 2 del veredicto | «PM pierde una protegida» | «ninguna posición elegible, o P1 VETADO» | la regla de posición va antes |
| denominador | lo saca el port (`port_estado`) | lo saca la vía (`motivo` del arnés) | es la vía la que cubre o no al volcán |
| Chillán | pares con las dos magnitudes | además, ambas mayores que 0 | el sellado haría log10(0) con un record publicado con magnitud 0 (no debería ocurrir; se declara) |
| veredicto | CANDIDATO a la fase 3 | PROPONER ADOPCIÓN | es la fase 4 |
| costura, borde del gránulo, S-1 | informan | no se calculan | se informaron en el censo y la vía tiene la misma máscara; en E no se informan (VF4-10, aceptado: no deciden) |
| soporte de la adenda 1 | informa | informa, al leer (arriba) | el tramo E trae publicaciones nuevas (VF4-10) |

### 6 bis. Regla de posición (se aplica antes del §7)

- **Elegible**: brazo de posición cuyo P1 contra K no está VETADO y, si es V-cercano o V-pico, que tampoco pierde una
  protegida de la tabla que V publica (P1 contra V). Por qué (VF4-01): sin esto, una posición podía cambiar una alerta
  de 1 MW o más que V publica por seis publicaciones bajo 1 MW, y el criterio de victoria no admite ese canje. Una
  pérdida sólo del OCR contra V no quita la elegibilidad: lleva a DECIDE NICOLÁS por la viñeta siguiente.
- **Gana**: un elegible distinto de V cuyo **P2' contra V** da GANA. Si ganan los dos, el de menor E + E_lejana (sus
  errores en P2' contra K); a igual valor, V-pico. Esa preferencia es **a priori**, no un resultado: la frase del
  programa («la distancia de MIROVA calza mejor con el píxel pico») sale de la comparación del píxel pico contra el
  alertado más cercano, y el propio informe de S165 dice que con todo en el cráter la distancia de MIROVA sigue al
  cúmulo radiante (VF4-12). En MODIS el caso es improbable (1 de 5.321 pasadas cambia con «cercano»).
- **Protegidas que otra posición publica**: si alguna protegida, de la tabla o sólo del OCR, la publica otra regla de
  posición y la elegida no, no se cambia en silencio: el veredicto va a DECIDE NICOLÁS con la lista (§7, fila 5;
  VF4-01; N-07 de la segunda vuelta: el OCR entra aquí porque es el lado seguro).
- **Si ninguno gana**: V (radiante), si es elegible. Es lo que hace hoy la vía y lo que midió el censo; a igual
  desempeño no se cambia sin evidencia.
- **Si V no es elegible**: el elegible no peor que V en P2' (GANA, EMPATE, o SIN SUSTRATO con neto 0 o a favor); si
  son dos, el de menor E + E_lejana y a igual valor V-pico. Si ninguno: NINGUNA POSICIÓN ELEGIBLE y el veredicto es
  NO ADOPTAR.
- **Multiplicidad**: dos contrastes contra V, cada uno al 5 % de una cola, sin corregir; la probabilidad de que alguno
  gane sólo por azar es mayor que 5 %, y se declara.
- **Descriptivas, no deciden**: las pasadas que cambian de publicación contra V, por nombre y etiqueta; en las
  `far_ref`, cuántas tienen algún alertado (un cero de E_lejana sin alertados no dice nada).

## 7. Veredicto (primera fila que se cumpla), sobre el brazo elegido en el §6 bis

| orden | condición | etiqueta |
|---|---|---|
| 1 | algún control del §8 en rojo (después del protocolo del tramo E, abajo) | **INDECIDIBLE** |
| 2 | ninguna posición elegible, o P1 VETADO (con la regla del §6 bis la segunda no puede darse; queda como defensa) | **NO ADOPTAR** |
| 3 | P2 o P2' contra K da PIERDE | **NO ADOPTAR** |
| 4 | P2 o P2' da SIN SUSTRATO | **INDECIDIBLE** |
| 5 | P2 o P2' da BLOQUEA, o P1 sólo OCR, o P1b con alguna, o M da EMPEORA, o una protegida que K publica salió del denominador por un motivo sellado, o una protegida que otra posición publica y la elegida no | **DECIDE NICOLÁS**, con la lista |
| 6 | P2 y P2' dan GANA o EMPATE | **PROPONER ADOPCIÓN** (a Nicolás, A45) |

**Protocolo de fallo, escrito antes de ver los datos (VF4-06):**
- **Rojo de cobertura sólo en el tramo E** (toda pasada faltante, repetida, sobrante, con falla del arnés o de MIROVA
  sin pasada nuestra es del 2026-10-17 en adelante): E se excluye entero en todos los brazos, se evalúa C solo y el
  resultado lo declara en su primera línea (`e_excluido`). Por qué: E es una cola de diez días que el censo nunca
  corrió; un 404 ahí no dice nada de la vía, y perder las 14 h de C por eso sería caro. Un rojo que toca C deja todo
  INDECIDIBLE. La frontera es la fecha: el 2026-10-16 23:59 es de C y el 2026-10-17 00:00 ya es de E.
- **Vía que no corrió en E** (N-03 de la segunda vuelta): si entre lo que saca E hay pasadas con `sin_mxd03`,
  `geo_distinta` o `sin_grilla`, E se excluye igual, pero el veredicto no pasa de **DECIDE NICOLÁS** y la lista va en
  `e_via_no_corrio`. Eso no es una descarga: es la vía ante datos nuevos, que es lo que verá en producción.
- El protocolo lo dispara sólo la cobertura. Un rojo de otro control que cae sólo en E deja todo INDECIDIBLE, salvo
  que la cobertura ya haya sacado E: entonces los controles se recalculan sobre C. Es la lectura conservadora y se
  declara.
- **Identidad en rojo**: no se lee el resto. Se busca la causa en la vía con la pasada distinta en la mano. Si hace
  falta tocar `pipeline/`, eso es un PR propio con tag defensivo y el sí de Nicolás (A45), y después se repite la
  corrida de V entera desde un tag nuevo (no sólo las pasadas distintas), porque la vía arreglada puede cambiar
  cualquier pasada.
- **Cualquier otro control en rojo**: se busca el defecto del instrumento y se repite la lectura; no se repite la
  corrida a ciegas.

El criterio de victoria de `docs/MISSION.md` (sección «Criterio de victoria de la réplica») queda así: ninguna
protegida de 1 MW o más se pierde (filas 2 y 5), y bajo 1 MW una alerta perdida y una publicación de más pesan igual
(cada una vale 1 en E, filas 3 a 6).

## 8. Controles (antes de leer el veredicto)

1. **K = producción**: en cada pasada el K del arnés se compara con el record de `data/mirova_equivalent/`; una
   diferencia se re-corre en el `codigo_sha` del record guardado (`recorrer_en_sha.py` de MOD-B) y, si no se
   reproduce, el control queda en rojo. El predicado del evaluador da la misma publicación de K que el del runner. Una
   fila sin el campo `k_difiere_de_guardado` deja el control en rojo: no se comparó (VF4-03). El campo tiene que ser
   True o False (un `None` no es «no difiere»), y toda fila evaluable trae `pub_runner` con la clave `K`; sin ella, rojo,
   porque un 0 por defecto coincidiría con el predicado en toda pasada donde K no publica (N-05 de la segunda vuelta).
2. **Identidad de punta a punta** (la pieza nueva): en cada pasada de C evaluable con grilla guardada por el censo
   (5.321), V del runner contra V-grilla. **El conjunto que se exige sale de la población** (campo `grilla_censo`), no
   del archivo de identidad, y la población tiene que traer exactamente 5.321 pasadas con grilla del censo; si el
   archivo de identidad omite una, falta (VF4-02). En cada una: **misma máscara** (las mismas celdas alertadas), **mismo VRP a 0,001 MW** y
   **misma `distance_class`**. Una sola pasada distinta con el mismo gránulo deja el control en rojo. Las pasadas con
   otro gránulo (`otro_granulo`) se cuentan y se listan; si superan el 1 % de las 5.321, el control queda en rojo
   (la identidad no se habría medido; el 1 % exacto pasa). Una pasada con grilla del censo que el runner saca por un
   motivo sellado («volcán fuera del gránulo», «escena inválida») es un desacuerdo, porque el censo sí cubrió el volcán:
   cuenta como otro gránulo si el archivo de identidad lo declara así (y entra al tope de 1 %), y si no, deja el control
   en rojo. Sin esto, una lectura rota de MxD03 se leería como «el volcán no está» y la pasada desaparecería de la
   identidad (N-01 de la segunda vuelta). Se informa además, por pasada, la máxima diferencia de radiancia entre la
   grilla del runner y la del censo.
   **Adenda a N-01 (S170, SELLADA el 2026-10-31 con autorización de Nicolás, tag `s170-modd-f4-candado-n01`, `a7bd7562e`;
   marca S171; texto original: «BORRADOR pendiente del sello de Nicolás»;
   `experiments/_s168/modd_f4_candado/adenda_n01/ADENDA_N01_BORRADOR.md`).** Una pasada con grilla del censo que el runner
   saca como «escena inválida» cuenta como acuerdo de la identidad, y no entra al tope de 1 %, si a la vez: (1) la vía
   sobre la grilla del censo (la de `grillas_censo_sha256.txt`) llega al mismo motivo (`motivo_censo`); (2) es el mismo
   gránulo; (3) la grilla del runner es igual a la del censo a la precisión float32; y (4) tienen la misma máscara, el
   mismo VRP a 0,001 MW y la misma clase. Si falta cualquiera, rige N-01. «Volcán fuera del gránulo» sigue siempre con
   N-01. Caso simétrico: una pasada con grilla del censo que el runner evalúa (sin motivo) y cuya grilla del censo da
   «escena inválida» es un desacuerdo y deja la identidad en rojo. Por qué: el censo guardó la grilla de 45 pasadas que
   su propio port declaró escena inválida; la premisa de N-01 («una pasada con grilla del censo es una pasada que el
   censo cubrió») no vale para ellas.
3. **Records de V**: toda pasada evaluable trae los tres records (V, V-cercano, V-pico), salvo que el arnés declare
   que `store.append_record` lo descartó.
4. **Placebo**: K × 1,2 da d′ = 0 en todo par y ganancia 1,2 exacta.
5. **Contador** (fuera de línea): toda publicación de V con magnitud 0 deja de publicar; 50 negativos que V no
   publica (semilla 166), con un cúmulo de cumbre de 0,3 MW a 0,5 km inyectado, pasan a publicar y P2 cuenta 50
   errores más.
6. **Cobertura** (A108): cada pasada de la población con una fila, sin repetidas ni sobrantes. Sólo «volcán fuera del
   gránulo» (la vía no cubre el volcán: menos de 100 píxeles a 45 km o el más cercano al centro a más de 5 km) y
   «escena inválida» (motivo del `.m`) salen del denominador de todos los brazos. Una vía que no corrió (record sin
   `via_codigo_mirova` True: `sin_mxd03`, `geo_distinta`, `sin_grilla`) o una falla del arnés deja el control en rojo.
   Toda pasada MODIS de la referencia (alerta o bajo 1 MW) sin pasada de la población a ±120 s deja el control en
   rojo (programa §8.1); la población trae esa lista siempre (vacía si no hay ninguna), y si no la trae el control
   queda en rojo, porque no se midió (VF4-03). En las protegidas (de la tabla o sólo del OCR) que salen por un motivo
   sellado, «K publica» se recalcula con el predicado del evaluador sobre el record de K; si no coincide con el runner,
   o si el runner no dejó su publicación de K, es falla del instrumento (como VCR-06 del sellado); si K la publica, se
   lista y lleva el veredicto a DECIDE NICOLÁS (§7, fila 5).
7. **Referencia y re-etiquetado**: sha256 de las dos copias congeladas; el re-etiquetado corrido dos veces da lo mismo;
   y con la referencia sellada del censo reproduce las etiquetas selladas del censo (prueba de que el etiquetador es
   el mismo instrumento).
8. **Candado**: manifiesto de hashes, todos los jobs en el commit del tag, sha256 de `frontend/index.html` igual al del
   tag, blob de `evaluar_d25.py` igual a `1dbabf65`.
9. **Posición**: (a) la distancia radiante que calcula el arnés reproduce el `centroid_dist_km` y la clase del record
   de V en cada pasada con alertados; (b) las variantes conservan los píxeles de V, y el VRP cuando quedan en la misma
   clase; (c) el predicado cambia con `distance_class` (un record de cumbre a 1 km publica; el mismo a 9 km no).

## 9. Chillán, estratificado por cenit

1. **Prueba propia sellada de MOD-D §5**, con V (o el brazo elegido) en el lugar del PM, sobre las alertas de Chillán
   de C ∪ E: recuperadas (K no publica, el brazo sí), pares con prueba de signos de una cola, RESUELTO POR EL PAQUETE /
   ES DEL SENSOR / SIN SUSTRATO / SIN RESOLVER con las mismas condiciones y el mismo corte de 30°. Acompaña al
   veredicto, no entra en él.
2. **Por tramo de 10° de cenit** (informa): protegidas de Chillán, cuántas publica K y cuántas el brazo, y la mediana de
   K/MIROVA y brazo/MIROVA en cada tramo. La pérdida del 2026-10-25 07:20 (58°) se lista por nombre.

## 10. Predicciones (para poder fallar)

Del censo verificado y de S165, con la referencia sellada del censo (con la de hoy pueden cambiar etiquetas):
- **Identidad**: 5.321 de 5.321 iguales (la vía reproduce al port en las grillas del censo; la lectura de producción y
  la del probe del censo son la misma expresión). Si falla, el riesgo más probable es la fusión de B22 y B21 donde B22
  satura y el DN inválido (SOSPECHA).
- **V contra K en C**: P1 0 pérdidas; P1b 0 (el único del censo, Láscar 2026-04-25 07:35, era del desempate del port;
  con la regla de MATLAB la vía da 1,1124 MW); P2 GANA con S_K ≈ 49 y S_V ≈ 8 en unos 50 bloques; M MEJORA; curva de
  V/MIROVA por tramo de 10° de 0,93; 0,97; 1,04; 1,10; 1,06 y 1,09, contra 0,63; 0,70; 0,45; 0,31; 0,22 y 0,21 de K
  (`resultado_censo.json`, `curva_cenit` del PM y `curva_cenit_K`).
- **Chillán**: recupera las del 09-29, 10-12 y 10-15; la del 10-25 es SIN DATO (fuera del censo). El censo dio SIN
  RESOLVER (6 de 7 pares, p = 8/128); con la cola puede cambiar.
- **Posición**: S165 encontró en el censo una sola pasada que cambia con «cercano» (Láscar 2026-03-30 07:25, `far_ref`:
  «cercano» publicaría 11,7 MW como cumbre donde MIROVA ubicó la fuente a 26,87 km). Predigo que ningún brazo gana
  (P2' contra V con 1 bloque es SIN SUSTRATO) y queda V. «Pico» no se midió desde el cráter en MODIS: SIN DATO.
- **Veredicto**: PROPONER ADOPCIÓN con V.

## 11. Lo que falta antes del despacho (el candado; no es despachable sin esto)

Hecho en esta entrega:
- **Evaluador** `evaluar_f4.py` con las reglas de §6 a §9, y su **batería** `probar_evaluar_f4.py` (resultado en
  `probar_evaluar_f4_salida.txt`), roja contra un evaluador vacío por aserción
  (`probar_evaluar_f4_contra_vacio_salida.txt`), y **mutaciones** con identidad y control de caída
  (`mutar_evaluar_f4.py`, `mutar_evaluar_f4_salida.txt`). Cifras en el §13.

Falta (después del sello, en este orden):
1. **Población** `poblacion_f4.json`: C re-etiquetada y E armada (con la comprobación HEAD de los días de E, §4), con
   `lab`, `lab_union`, `tramo`, `grilla_censo`, la lista de cambios de etiqueta contra el censo y `sin_pasada_nuestra`
   (siempre presente).
2. **Arnés** `probe_f4.py` (sobre el molde de `probe_paquete.py` de MOD-D): por pasada, K y V desde el tag; un envoltorio
   de sólo lectura sobre `procesar_grilla` (A75) que captura grilla, radiancia, celdas alertadas y posición del cráter
   para calcular las tres distancias con `_cumulo_del_mas_radiante` de la vía; las variantes por `store.append_record`;
   la grilla de cada pasada en npz; `k_difiere_de_guardado` y la re-corrida en su sha; la publicación del runner.
   Filas con el contrato que lee `evaluar_f4.cargar` (`f4_parte*.jsonl`).
3. **Identidad** `identidad_f4.py`: V-grilla sobre las grillas del censo (`D:\vrp-trabajo\temporales\s162_modd\censo\`,
   265 MB, 5.321 `grilla_NNNN.npz`) contra el record y la grilla del runner.
4. **Externos** del candado (referencia, re-etiquetado, manifiesto, procedencia, predicado).
5. **Workflow** de sólo lectura con `"on":`, `EARTHDATA_TOKEN` y nada más (A71), sobre el molde del de MOD-D.
6. **Humo** de unas 25 pasadas (incluidas Láscar 2026-04-25 07:35 y Chillán 2026-10-25 07:20) y ensayo en seco.
7. **Tag** del candado y **verificador limpio** del candado; recién ahí el pedido de despacho a la coordinadora.

**Contrato de entrada del evaluador** (lo que el arnés escribe por pasada en `f4_parte*.jsonl`, `tipo: "record"`; la
población agrega lo suyo por `(vol, dt)`):

| campo | qué es |
|---|---|
| `vol`, `dt` (`AAAA-MM-DD HH:MM` UTC), `noche`, `sensor`, `z` (cenit del sensor en el cráter) | identidad de la pasada |
| `estado` | `ok` o el error del arnés |
| `motivo` | `None`, `volcan_fuera_del_granulo`, `escena_invalida` u otro (otro es falla) |
| `v_marca` | `via_codigo_mirova` del record de V: `True` si la vía corrió; `sin_mxd03`, `geo_distinta` o `sin_grilla` si siguió K |
| `inner` | `inner_radius_km` del volcán |
| `k_slim`, `v_slim`, `vcerc_slim`, `vpico_slim` | los records que dejó `store.append_record` (campos de `banco_paridad.CAMPOS_JS`) |
| `store_descarto` | `{"V": bool, "V-cercano": bool, "V-pico": bool}` si `store` no escribió ese record |
| `dist` | `{"radiante", "cercano", "pico"}` en km sin redondear, desde el cráter |
| `pub_runner` | `{"K": 0 o 1}` del predicado corrido en el runner (obligatorio en toda fila evaluable y en toda protegida que sale por un motivo sellado) |
| `k_difiere_de_guardado` (True o False), `k_reproducida_en_su_sha` | control K = producción (§8.1) |
| de la población: `lab` (tabla sola), `lab_union` (tabla más OCR, si difiere), `vrp_mirova`, `tramo` (`C` o `E`), `grilla_censo` | la vara y el conjunto de la identidad |
| de la población, aparte de las pasadas: `sin_pasada_nuestra` (lista de `[vol, dt, lab]`, siempre presente) | cobertura contra la referencia |

El soporte independiente del §6 (informa) necesita además, al leer, las detecciones de los otros sensores de la misma
noche y las alertas de MIROVA (los argumentos `nuestros` y `alertas_mirova` de la función sellada). No las escribe el
arnés: se arman al leer, de `data/mirova_equivalent/` en el commit del tag y de la referencia congelada (N-08 de la
segunda vuelta). No cambian ningún veredicto.

**Costo** (estimado; se mide en el humo): el censo midió 9,1 s por pasada con descarga, cinco variantes del port y K;
aquí son K, V y tres pasos por el almacén. Cota alta: 5.700 pasadas × 9 s ≈ 14 h de runner, en tres tandas de 8 jobs
como el censo, despachadas de a una por la coordinadora desde el tag.

## 12. Decisiones para el sello (con recomendación)

1. **Corrida completa de C ∪ E en el runner** (recomendado) o sólo la vía sobre las grillas del censo en local más el
   runner en E y una muestra. **Completa**: la identidad desde el HDF es justo lo que la fase 3 no pudo medir, y una
   muestra puede saltarse los caminos raros (B21 donde B22 satura: 0 de 149 pasadas en S159).
2. **Etiquetas de la referencia posterior a D-39** (recomendado), con las del censo listadas al lado.
3. **P2' decide junto con P2** (recomendado): es la vara que pidió Nicolás para la posición, y medir V contra K sin
   ella dejaría fuera las pasadas en que MIROVA ubicó el calor lejos.
4. **La razón brazo/MIROVA en [0,9; 1,1] informa y no decide** (recomendado). V750-A la hace decidir; aquí M ya decide
   contra K con su comparador calibrado, y la banda sería un umbral que no salió de la referencia (A115).
5. **Una protegida perdida sólo por el OCR va a DECIDE NICOLÁS y no veta** (recomendado; la tabla es lo más creíble,
   memoria S159).
6. **Sombra prospectiva** (fija aquí su tamaño y su fecha, como pide el §7 del pre-registro sellado): la vía en un
   perfil de sombra con su propio `data_subdir` (A47), desde el 2026-11-03 o desde el sí de Nicolás si es posterior,
   28 noches; se lee el día 29 con P1 (veto) y P2' (no PIERDE si hay 5 bloques o más; con 4 o menos sólo veta).
   Crear ese perfil y sumarlo al NRT toca `pipeline/profiles/` y un workflow: **necesita su sí aparte** (A45).
7. **Protocolo del tramo E** (§7): un rojo de cobertura que está sólo en la cola del 17 al 26 de octubre la saca entera
   y se lee el censo solo (recomendado: la cola no tiene línea base y un 404 ahí no dice nada de la vía). La
   alternativa es dejar todo INDECIDIBLE y repetir la corrida.
8. **Una posición no puede perder una protegida que V publica, y una protegida que otra posición publica lleva a
   DECIDE NICOLÁS** (§6 bis, recomendado: es el criterio de victoria aplicado entre brazos de posición; vale también
   para V750-A y V375-E, que hoy no lo tienen escrito).

## 13. Instrumento entregado: batería y mutaciones

**Procedencia del runner (S170, SELLADA el 2026-10-31 con autorización de Nicolás, tag `s170-modd-f4-lectura`,
`e27dc2e49`; marca S171; texto original: «BORRADOR, rama `claude/s170-modd-f4-procedencia`, sin sello ni tag»).** Por qué: la
adenda a N-01 se selló después de correr t1 a t3. Los jobs corrieron en `s170-modd-f4-candado` (d65fd231d) y la lectura
se hizo con el evaluador de `s170-modd-f4-candado-n01` (a7bd7562e). El control de procedencia (§8.8) exige un solo
commit, un solo tag y un solo evaluador, y quedó en rojo aunque el runner hizo lo mismo en los dos commits. El §7 manda
arreglar el instrumento y repetir la lectura, no la corrida; Nicolás lo autorizó el 2026-10-31 (vía la coordinadora
S170). La regla (`procedencia_runner.py`, mecánica, sin mirar resultados del A/B): la lectura acepta las cabeceras en el
tag del runner sólo si (1) el commit de la lectura desciende del del runner; (2) ningún archivo que el job del runner
ejecuta o lee para producir records cambia entre los dos (el arnés, la población, el workflow, `pipeline/`, `scripts/`,
el tablero, `data/mirova_equivalent/`, las herramientas de re-corrida, `evaluar_d25.py` y sus dos dependencias, las
cuatro carpetas `_s151` que `probe_mxd03_ab` carga por ruta y `volcanoes.yaml`; una guarda rastrea con un gancho de
auditoría lo que `probe_f4.py` abre al importarse y falla si algo queda fuera de la lista); (3) en
`evaluar_f4.py`, que el arnés importa, no cambia nada de lo que el arnés alcanza (las definiciones que nombra, su
cierre y las sentencias de nivel de módulo, salvo un bloque `__main__` sin `else`); y (4) todas las cabeceras traen el commit y el
nombre del tag del runner, el `evaluar_f4.py` del runner y el `probe_f4.py` de la lectura. Cualquier otra combinación
sigue contra el tag de la lectura. La batería y el resto del evaluador sólo habilitan el job y se comprueban aparte (control
`manifiesto`). Pruebas: `probar_procedencia_runner.py`, 5 de 5 partes (repositorio sintético: verde sólo si cambia algo
que el arnés no alcanza; rojo si cambia cualquiera de las 18 entradas de la lista del runner, una definición alcanzable,
una sentencia de módulo o el `else` de un bloque `__main__`, o si
la lectura no desciende; cabeceras: rojo si la regla no da ok, si una trae otro commit, otro sha de `probe_f4`, otro
evaluador u otro nombre de tag, o si mezclan los dos tags; caso real d65fd231d contra a7bd7562e compatible; la guarda de
carga no encuentra nada fuera de la lista). Límites declarados (verificador de la procedencia, gravedad 1): el análisis
por AST no ve llamadas dinámicas (`globals()["x"]()`, `getattr`) ni distingue definiciones duplicadas (vale la última).
Mutaciones de las líneas nuevas (`mutar_procedencia_runner.py`): 32 de 32 atrapadas por aserción (una por cada entrada
de la lista del runner, más las de la regla, la guarda y la aceptación), sin caídas, con
identidad VIVA, caída CAE y rota ROTA, y el árbol quieto (`experiments/_s168/modd_f4_candado/procedencia_runner/`).
Sobre los artefactos de t1 a t3, sólo el control (sin releer): con `--tag-runner s170-modd-f4-candado` queda OK, sin él
sigue en rojo con 99.

**Corrida de la adenda a N-01 (S170, SELLADA el 2026-10-31 en el tag `s170-modd-f4-candado-n01`, `a7bd7562e`; marca
S171; texto original: «BORRADOR, rama `claude/s170-modd-f4-adenda-n01`, sin sello ni tag»).** La regla del
§8.2 entra en `evaluar_f4.control_identidad` (función `_acuerdo_escena_invalida` y el caso simétrico) e
`identidad_f4.comparar` (campo `motivo_censo`). Batería: 71 escenarios (E65 a E69 nuevos), 71 de 71 OK; contra el vacío,
71 de 71 por aserción y 0 caen. Mutaciones: M87 a M95 nuevas, y M12 con el texto nuevo (misma mutación). Cómo se llega
a la cifra, con sus dos salidas:
- `experiments/_s166_modd_f4/mutar_evaluar_f4_salida.txt` es la corrida completa (2026-10-31 05:00 a 12:54 UTC, 94
  mutaciones, batería de 69, un proceso, árbol quieto; copia y sha256 en `experiments/_s168/modd_f4_candado/adenda_n01/corrida1/`):
  93 de 94 por aserción, con M92 viva porque ningún escenario tenía «fuera del gránulo» con todo el acuerdo.
- Se agregaron E68 (para M92) y E69 con M95 («otro gránulo no es acuerdo», verificador de la adenda implementada), y se
  repitieron, con la batería de 71, las 18 mutaciones cuyo código ejecuta el control de identidad (M11, M12, M13, M49,
  M72, M73, M76, M77, M83 y M87 a M95) y los cuatro controles (14:17 a 15:41 UTC, un proceso, árbol quieto):
  `experiments/_s166_modd_f4/mutar_evaluar_f4_salida_adenda_identidad.txt` (copia y sha256 en `adenda_n01/corrida3/`;
  la corrida 2, de 17 con E68, queda en `adenda_n01/corrida2/`). Dio 18 de 18 por aserción, sin caídas, y los cuatro
  controles como deben.
- Las otras 77 mutaciones no ejecutan el código que prueban E68 y E69, así que su clase es la de la corrida completa.
  Total: **95 de 95 atrapadas por aserción**.

Identidades regeneradas con el `identidad_f4` nuevo, con `motivo_censo`:
`experiments/_s168/modd_f4_candado/identidades/identidad_t1.json`, `_t2` y `_t3`, con sus salidas (1.746, 1.789 y
1.786 iguales). Sobre las tres tandas, sin leer el veredicto, la identidad pasa de
rojo a OK: 24, 11 y 10 escenas inválidas por acuerdo y 0 casos simétricos.

**Corrida vigente (candado, S168, 2026-10-30 00:15 a 11:35 UTC)**, después de cerrar VS-01 a VS-08 del tercer
verificador en la batería y el medidor, sin tocar `evaluar_f4.py`. Un proceso (`--paralelo 1`), temporales en
`D:\vrp-trabajo\temporales\s168_mut`, árbol quieto (sha256 de los cinco archivos del instrumento iguales antes y
después: `experiments/_s168/modd_f4_candado/mutaciones_sha256_antes.txt` y `_despues.txt`):

| qué | resultado | salida |
|---|---|---|
| batería (66 escenarios: E62, E63 y E64 nuevos) | 66 de 66 OK | `probar_evaluar_f4_salida.txt` |
| la misma batería contra el evaluador vacío | 66 de 66 fallan por aserción, 0 caen | `probar_evaluar_f4_contra_vacio_salida.txt` |
| mutaciones (82 más M83 a M86) | **86 de 86 atrapadas por aserción, ninguna con escenarios que caen**; 0 vivas, 0 caen, 0 atrapadas con caídas, 0 rotas, 0 no aplican | `mutar_evaluar_f4_salida.txt` |
| controles | identidad VIVA; caída con `RuntimeError` CAE (61 caen); caída con `ValueError` CAE (61 caen); rota ROTA | ídem |
| prueba del medidor (clasificación y salida «NO VALE» con código 1) | 5 de 5 OK | `probar_mutar_f4_salida.txt` |

Desde esta corrida, ATRAPADA exige que ningún escenario caiga (VS-01). Con el `except` de E53 acotado al mensaje de
`math.log10(0)` (VS-02), M70 sigue atrapada por E53 y el control con `ValueError` sale CAE.

**Qué sha es el del evaluador sellado (VF2-01 de la auditoría S169).** Los sha256 de abajo se midieron sobre la copia
de trabajo de Windows, que git escribe con fin de línea CRLF. El evaluador sellado es el mismo archivo: su blob en git
(LF, lo que lee el runner Linux) mide `8a1edc14…` y su copia CRLF mide `c01e0824…`. Entre `314cec809` y el tag del
sello no hay diferencias en `evaluar_f4.py` (`git diff 314cec809 s168-modd-f4-sellado -- experiments/_s166_modd_f4/evaluar_f4.py` sale
vacío), y los cierres de VS-01 a VS-08 no lo tocaron. El manifiesto del candado registra los sha de los blobs (LF).

Corrida anterior, del sello (se conserva por historia). Corrida del 2026-10-29 con el árbol quieto, `--paralelo 2` y los temporales en `D:\vrp-trabajo\temporales\` (sha256
de `evaluar_f4.py`, `probar_evaluar_f4.py`, `evaluar_vacio.py` y `mutar_evaluar_f4.py` iguales antes y después;
`c01e0824…`, `395f276e…`, `98d8d65b…`, `180aa8a8…`):

| qué | resultado | salida |
|---|---|---|
| batería (63 escenarios: 61 con predicado sintético, 2 con node sobre el tablero real) | 63 de 63 OK | `probar_evaluar_f4_salida.txt` |
| la misma batería contra el evaluador vacío | 63 de 63 fallan **por aserción**, 0 caen | `probar_evaluar_f4_contra_vacio_salida.txt` |
| mutaciones (una regla del documento por mutación, batería entera contra cada copia) | **82 de 82 atrapadas por aserción**, 0 vivas, 0 caen, 0 rotas, 0 no aplican | `mutar_evaluar_f4_salida.txt` |
| control de identidad (sin mutación) | VIVA, como debe | ídem |
| control de caída (excepción al entrar a `evaluar`) | CAE, como debe (58 escenarios caen, ninguno se cuenta como atrapado) | ídem |
| control de mutación rota (`PLACEBO = = 1.2`, error de sintaxis) | ROTA, como debe | ídem |

El medidor sale con código 1 y escribe «NO VALE» si alguno de los tres controles no sale como debe (N-02); en esta
corrida salió con código 0.

Dos cambios del instrumento respecto de `ff03538dd`, hechos para que la cifra mida lo que dice medir y no para que
cuadre:

- **E53 (magnitud 0 en Chillán)** atrapaba cualquier excepción del evaluador y la convertía en falla por aserción. Por
  eso el control de caída salía ATRAPADA en vez de CAE: una caída real del evaluador se habría contado como mutación
  atrapada. Ahora E53 atrapa sólo `ValueError` y `ZeroDivisionError`, que es lo que lanza el logaritmo de 0; cualquier
  otra excepción cae. La mutación que E53 vigila (M70) sigue atrapada, porque `log10(0)` lanza `ValueError`.
- **M82 (pasada sellada sin publicación de K en el runner)** no era una mutación válida. La versión vieja cambiaba la
  condición por `if False:`, y la pasada caía en la rama siguiente (`elif pub != int(f["pub_runner"]["K"])`), que
  lanzaba `KeyError` por la clave ausente: salía CAE, y una mutación que cae no mide nada. La nueva reemplaza el
  `fallas.append(...)` por `pass`, o sea que el evaluador acepta en silencio la pasada sin publicación de K, que es el
  defecto que la regla prohíbe. La atrapa E58 por aserción, sin caída.

Qué NO prueba la batería: que el arnés escriba bien el contrato (eso es del candado), ni el predicado real del tablero
fuera de N01 y N02 (el sintético publica si el record es cumbre con VRP mayor que 0; los filtros de cirro, campo difuso
y el tope de 50.000 MW del tablero sólo se ejercen con node). Una mutación del placebo a ganancia 1,0 no se incluyó:
el control compara contra la misma constante y no podría verla (es un placebo inútil, no uno roto).

## 13 bis. Verificador limpio y qué se hizo con cada hallazgo

Primera vuelta: Sonnet, esfuerzo alto, contexto limpio, sobre `e1f6b197b` (informe en `verificador/INFORME.md`, con
sus caminos escritos antes de leer en `verificador/CAMINOS_previos.md` y sus scripts). Veredicto: «se puede sellar CON
CAMBIOS CHICOS»; nada que diera vuelta el veredicto con datos plausibles, cuatro huecos de instrumento de gravedad 3.

| hallazgo | gravedad | qué se hizo | dónde queda fijado |
|---|---|---|---|
| VF4-01, la regla de posición ignora las protegidas | 3 | una posición que pierde una protegida que V publica no es elegible; una protegida que otra posición publica y la elegida no lleva a DECIDE NICOLÁS | §6 bis, §7 fila 5; E39, E40; M47, M48 |
| VF4-02, identidad circular | 3 | el conjunto exigido sale de la población (`grilla_censo`) y tiene que sumar 5.321; `main` no acepta otro total | §8.2; E11, E41, E51; M13, M49 |
| VF4-03, controles que pasan si falta una clave | 3 | lista `sin_pasada_nuestra` ausente y campo `k_difiere_de_guardado` ausente dan rojo | §8.1, §8.6; E42, E51; M50, M51, M67 |
| VF4-04, 12 reglas vivas a la batería | 3 | un escenario por cada una (estado del arnés, motivo desconocido, sobrante, 50 inyectados, K = 1,0 exacto, bordes de la banda y p de Chillán, «no peor», Chillán con el brazo elegido, clase y VRP de la posición) y su mutación | E43 a E49; M55 a M66 |
| VF4-05, A119 no aplicada | 2 | decide la tabla sola (`lab`); la unión (`lab_union`) informa; una protegida sólo OCR perdida va a DECIDE NICOLÁS | §5 «Canal», tabla de cambios; E04, E35; M35 |
| VF4-06, sin protocolo de fallo | 2 | escrito: rojo sólo en E saca E entero; identidad roja no toca `pipeline/` sin A45 y repite V entero | §7; E50; M52 a M54 |
| VF4-07, «CMR sirve» por listado | 2 | «sirve» = HEAD 200 de L1B y MxD03 de cada pasada, comprobado al armar la población | §4 |
| VF4-08, el medidor contaba un error de sintaxis como atrapada | 2 | ROTA si no carga o si falla sin aserción; control nuevo CONTROL_ROTA, que tiene que salir ROTA | `mutar_evaluar_f4.py`, `probar_evaluar_f4.py` (código 3) |
| VF4-09, `main` y `cargar` sin prueba | 2 | E51 corre `main` con archivos y lo compara con la llamada en memoria; `Uso` corregido | E51; M67 |
| VF4-10, adendas informativas descartadas | 1 a 2 | soporte independiente de la adenda 1 vuelve, al leer; costura, borde y S-1 se aceptan fuera (no deciden) | §6 |
| VF4-11, tres cifras | 1 | 23 protegidas (no 18), 2 a 7 gránulos (no 3 a 7), curva de K completa | §4, §5, §10 |
| VF4-12, desempate a favor del pico | 1 | se mantiene, declarado como preferencia a priori | §6 bis |

Lo que el verificador dejó SIN DATO (el arnés, la población, la identidad, el humo, los 404 de los días de E, si K del
tramo E coincide con `data/` entre NRT y estándar) es justo lo que construye el candado del §11.

Segunda vuelta: Sonnet, contexto limpio, sobre `ff03538dd` (informe en `verificador/segunda_vuelta/INFORME.md`, con
14 escenarios y 12 mutaciones propios). Dio por cerrados VF4-01, 05, 07, 08, 09, 11 y 12, y por cerrados en parte
VF4-02, 03, 04, 06 y 10, con ocho hallazgos nuevos. Su veredicto: «se puede sellar tras corregir N-01 y N-02, y
escribir en el documento N-03 y N-04».

| hallazgo | gravedad | qué se hizo | dónde queda fijado |
|---|---|---|---|
| N-01, la identidad se esquiva con un motivo sellado | 3 | una pasada con grilla del censo que sale por un motivo sellado cuenta como otro gránulo si la identidad lo declara (y entra al tope), y si no, rojo | §8.2; E59; M76, M77 |
| N-02, §13 viejo y el medidor no hace cumplir sus controles | 3 | el medidor escribe «NO VALE» y sale con código 1 si un control no sale como debe; §13 rehecho con la corrida nueva | `mutar_evaluar_f4.py`; §13 |
| N-03, vía que no corrió en E tratada como un 404 | 2 | E se excluye igual, pero el veredicto no pasa de DECIDE NICOLÁS; la lista va en `e_via_no_corrio` | §7; E61; M80, M81 |
| N-04, día excluido por HEAD contra la cobertura | 2 | sus pasadas de MIROVA quedan en `sin_pasada_nuestra` y E sale entero (lectura conservadora) | §4 |
| N-05, `None` y `pub_runner` ausente daban OK | 2 | `k_difiere_de_guardado` tiene que ser True o False; `pub_runner` con `K` obligatorio, también en las protegidas selladas | §8.1, §8.6, §11; E58, E60; M78, M79, M82 |
| N-06, ocho reglas vivas a la batería (X01 a X14) | 2 | un escenario por cada una: frontera del 16 al 17-oct, magnitud 0 en Chillán, elegibilidad con pérdida sólo OCR, grilla de más, tope de 1 % inclusivo, OCR en «otra posición» y en la sellada de K | §7, §6 bis, §8.2; E52 a E58; M68 a M75 |
| N-07, dos frases que no calzaban con el código | 1 | «otra posición» incluye el OCR (lado seguro, ahora escrito); la fila P1 de §6 y la fila 2 de §7 dicen cuándo se llega a NO ADOPTAR | §6, §6 bis, §7 |
| N-08, el soporte independiente pide entradas que el contrato no trae | 1 | se arman al leer, de `data/` en el commit del tag y de la referencia congelada | §11 |

## 13 ter. Tercer verificador (para el sello) y lo que queda declarado

Sonnet, contexto limpio, sobre `314cec809` (`experiments/_s168/modd_f4_verificador/INFORME.md`, con sus scripts y
salidas). Reprodujo la batería (63 de 63) y la batería contra el vacío (63 de 63 por aserción, 0 caen) con salidas
idénticas a las commiteadas, confirmó los cuatro sha256 del §13, corrió `--solo M70,M82` con los tres controles como
deben (identidad VIVA, caída CAE con 58, rota ROTA) y encontró que los arreglos de VF4-01 a VF4-04 y N-01 existen en el
código con su escenario y su mutación. M82 la atrapa E58 por aserción pura. Sin hallazgos de gravedad 3. El instrumento
no se tocó para el sello: los sha256 del §13 siguen valiendo.

| hallazgo | gravedad | qué queda |
|---|---|---|
| VS-01, el medidor cuenta ATRAPADA aunque otros escenarios caigan | 2 | declarado; en la corrida commiteada ninguna de las 82 tiene caídas (`caen: -` en todas), así que la cifra no cambia. A cerrar en el candado: ATRAPADA sólo con `caen` vacío y un segundo control de caída con `ValueError` |
| VS-02, M70 se atrapa porque E53 convierte en aserción la caída por `log10(0)` | 2 | declarado: **81 de 82 por aserción pura y 1 (M70) por una aserción explícita sobre la caída**. El defecto que M70 introduce es justo esa caída y no tiene otra señal observable; el `except` sólo acepta `ValueError` y `ZeroDivisionError`. A acotar en el candado al mensaje `math domain error` |
| VS-03, el brazo `no_pasan` del control del contador y la salida NO VALE del medidor no tienen prueba | 2 | a cerrar en el candado con un escenario que espere INDECIDIBLE y una prueba del código 1 |
| VS-04, `N_GRILLAS_CENSO = 5321` sin aserción propia | 1 | una constante mal escrita da INDECIDIBLE (ruidoso); aserción en el candado |
| VS-05, `control_posicion` acepta cero pasadas con alertados | 1 | en la corrida real n es grande; escenario en el candado |
| VS-06, los empates de Chillán quedan fuera de los pares | 1 | lectura sellada: lo que hace el código, `db == dk` no es par (§9). Chillán acompaña y no decide |
| VS-07, dos mutaciones propias del verificador vivas, casi equivalentes | 1 | ninguna |
| VS-08, `--traza` rechazado por argparse | 1 | opción de depuración; se arregla en el candado |

Lo que se cierra en el candado toca la batería y el medidor, no las reglas de `evaluar_f4.py`. Si algún arreglo
obligara a cambiar una regla del evaluador, eso pide un sello nuevo.

**Al día con el candado (S168).** Nicolás aceptó VS-02 tal como está arriba (M70 atrapada por la aserción explícita de
E53). Cerrados en la batería y el medidor, con la corrida vigente del §13: VS-01 (clase ATRAPADA_CON_CAIDAS, que no
cuenta, y control de caída con `ValueError`), VS-02 (`except` acotado a `math domain error`), VS-03 (E62 y
`probar_mutar_f4.py`), VS-04 (aserción en E41), VS-05 (E63), VS-06 (E64; la lectura sellada no cambia) y VS-08
(`--traza`). M83 a M86 vigilan VS-03 a VS-06. VS-07 queda como estaba.

Auditoría de patrones de S169 sobre el candado (`experiments/_s169/audit_patrones/f2/`, en `loop/activo`, con su
verificador limpio). Se arreglaron en el candado, sin tocar `pipeline/` ni las reglas del evaluador: VC169-01 y P2-05
(el sha de la población se registra sobre el blob en git, con prueba), P2-01 (el arnés resetea el circuit-breaker de
descarga antes de cada intento y corta la parte, en rojo, tras 3 gránulos seguidos sin bajar), P2-02, P2-03 con VF2-02,
P2-07 y P2-08 (detalle en el informe del candado). Quedan declarados, sin cambiar ningún veredicto con datos plausibles:

| hallazgo | gravedad | qué queda |
|---|---|---|
| P2-04, la identidad compara una clase recalculada en local | 1 a 2 | el humo dice si la clase del record del runner coincide con la recalculada |
| P2-06, la publicación de V, V-cercano y V-pico del runner no se compara con la del evaluador | 2 | sólo la de K se compara (§8.1); se informa |
| P2-09, `VRP_PROFILE` y `F4_RAIZ` cambian la lectura sin dejar rastro | 1 a 2 | la corrida se lee con los valores por defecto y lo declara |
| P2-10, «sin record guardado en data/» se lee como «K no difiere» | 1 a 2 | se cuenta en el humo (hoy 0 de 5.709 pasadas, según el verificador) |
| P2-11, un MxD03 ilegible se lee como «volcán fuera del gránulo» | 1 a 2 | da error, no «fuera»; el humo mide cuántos MxD03 traen relleno |
| P2-12, P2 con 21 bloques o más depende del generador de numpy | 1 | la versión queda registrada en el resultado (P2-02) |

## 14. Lo que este pre-registro NO decide

- El encendido: lo decide Nicolás con el resultado en la mano (A45).
- La vara: lectura A, corte de 1 MW y pareo ±120 s quedan como están.
- MxD03 sola (#920), el diurno MODIS, el bow tie (MOD-E) y la caja por volcán.
- La regla de posición de VIIRS 750 y VIIRS 375: cada sensor la mide en su propio A/B.
