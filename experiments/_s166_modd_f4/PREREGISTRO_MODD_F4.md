# Pre-registro S166 MOD-D fase 4: la vía «código MIROVA» de MODIS contra K, con los tres brazos de posición

Estado: **BORRADOR para el sello de Nicolás.** Escrito el 2026-10-28 por la sesión hija de MODIS de la fase 4 (reporta
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
    UTC (`cmr_cola.py`, `cmr_cola_salida.txt`, por versión, de 00 a 12 UTC en la caja de Chile): CMR sirve la versión
    6.1 estándar, que es la que pide `pipeline/fetch.py` primero, del 17 al 26 de octubre, con tantos MxD03 como L1B en
    cada día y plataforma (3 a 7 gránulos). Entran **si al armar la población** CMR sirve, para cada volcán y pasada
    nocturna de esos días, el L1B y su MxD03; un día que no cumpla se excluye entero en todos los brazos y se declara en
    la primera línea del resultado (como D-29).
  - CMR sirve además una Collection 7 de LAADS (versión `7`) en paralelo. Ni K ni V la piden (`fetch.py` pide 6.1 y cae
    a 6.1NRT): los dos brazos leen el mismo archivo y la colección no los separa. Que MIROVA haya pasado a la 7 es SIN
    DATO.
- **Cortes informados, que no separan brazos** (A104): los dos brazos se recalculan con un mismo código en todas las
  fechas, así que ninguna frontera de producción cae entre ellos. Se informan por tramo C y E; #535 (2026-08-28
  23:00 UTC) y la adopción de K (2026-10-18 09:57 UTC) sólo importan al control K = producción (§8.1), que compara
  contra lo que producción escribió en cada fecha.
- **A119**: MODIS desde marzo, sin reparos de cobertura de la tabla. Enero y febrero no entran.

## 5. La vara: lo que publica MIROVA

- **Referencia congelada** posterior al cierre de D-39 (el consolidado ganó 2.648 filas el 2026-10-27, 18 protegidas
  recuperadas en 60 días): consolidado de Mirova-v1 en el commit `cb91eb506c37cff0b83164dd602d8a5340277637`
  (2026-10-27 21:21:07 UTC) y OCR en `cfc57c4d8bc57c5ccd5219ff3a91749dae167b97` (2026-10-27 13:06:30 UTC), las mismas
  copias que usó S165 (`experiments/_s165_regla_posicion/referencia_salida.txt`). Su sha256 queda en el manifiesto del
  candado antes del despacho.
- **Etiquetas** con `poblacion_mxd03.py` sobre esa referencia, sin otro cambio: `protegida` (lectura A, alerta de 1 MW
  o más, pareo ±120 s), `bajo1`, `neg_limpio` (MIROVA miró y todas sus filas son RUTINA), `far_ref` (MIROVA publicó la
  fuente como `FALSO_POSITIVO` y ninguna ALERTA) y `sin_info`. La regla SN es de VIIRS 375 y no cambia nada en MODIS.
- **Por qué se re-etiqueta C** y no se usan las etiquetas selladas del censo: la tabla sellada es anterior a D-39 y le
  faltaban filas, entre ellas protegidas de Láscar. Las pasadas de C cuya etiqueta cambia contra la del censo se
  listan (informa).
- **Canal**: cada alerta lleva `solo_ocr` si es alerta sólo por una fila del OCR. Una pérdida de una protegida sólo OCR
  no veta: va a DECIDE NICOLÁS (§7), porque el OCR es la parte menos creíble de la referencia. P2 se informa también sin
  las pasadas sólo OCR.

## 6. Pruebas

Todo por pasada MODIS, «publica» y magnitud mostrada = el predicado de `frontend/index.html` ejecutado con node
(`banco_paridad.correr_node`, A97) sobre el record que dejó `store.append_record`. Las piezas estadísticas se importan
sin copiar de `experiments/_s157_prereg_d25/evaluar_d25.py`, blob `1dbabf65` (el mismo que usó el censo MOD-D):
`prueba_signos_p2` y `regla_signos_p2` (D-45), `pesos_bloque`, `regla_m` y `comparar_con_ganancia` (D-28). Bloque =
noche-volcán.

| prueba | qué cuenta | regla |
|---|---|---|
| **P1 veto** | protegidas que K publica y el brazo no | una que no sea sólo OCR: el brazo no es elegible (§6 bis) y el veredicto es NO ADOPTAR; sólo OCR: DECIDE NICOLÁS |
| **P1 lista** | protegidas que ni K ni el brazo publican | se listan, no deciden |
| **P1b** | protegidas que los dos publican, con K ≥ 1 MW y el brazo < 1 MW | una o más: DECIDE NICOLÁS. La contraria (K < 1, brazo ≥ 1) se lista |
| **P2** (sellada en MOD-D) | E = alertas bajo 1 MW sin publicar + publicaciones en negativos limpios; +1 si el error es sólo del brazo, −1 si es sólo de K | `regla_signos_p2`: GANA, PIERDE, BLOQUEA, EMPATE, SIN SUSTRATO (4 bloques o menos) |
| **P2'** (nueva) | E + E_lejana: publicaciones del brazo en pasadas `far_ref` | la misma prueba sobre E + E_lejana |
| **M** | alertas (protegida o bajo 1 MW) que K y el brazo publican: d = abs(log10(B/MIROVA)) − abs(log10(K/MIROVA)) | `regla_m`: sólo EMPEORA decide (DECIDE NICOLÁS); d′ contra la ganancia pareja informa |
| **Razón** | mediana de brazo/MIROVA en todas las protegidas que el brazo publica, publique K o no | informa, con la marca de si cae en [0,9; 1,1] (§12, decisión 4) |
| **Curvas de cenit** | razón brazo/MIROVA y K/MIROVA por tramo de 10°; y en cada noche-volcán con dos alertas separadas por 10° o más, razón más oblicua sobre menos oblicua del brazo y de MIROVA | informan: se busca reproducir la curva de MIROVA, no aplanarla |

P2 y P2' se calculan sobre C ∪ E y se informan también por tramo.

**Qué cambia respecto de las reglas selladas de MOD-D** (todo lo demás se conserva tal cual):

| pieza | sellado de MOD-D | aquí | por qué |
|---|---|---|---|
| brazo que decide | PM (el port) | V con la posición del §6 bis | la vía del pipeline es lo que se encendería |
| vara | etiquetas de la referencia del censo | las de la referencia posterior a D-39 (§5) | a la del censo le faltaban filas |
| P1 | toda pérdida veta | una pérdida sólo OCR va a DECIDE NICOLÁS | el OCR es la parte menos creíble (§12, decisión 5) |
| P2 | sólo E | P2 y P2', decide la peor de las dos (§7) | decisión de Nicolás del 2026-10-27 (§12, decisión 3) |
| fila 2 del veredicto | «PM pierde una protegida» | «ninguna posición elegible, o P1 VETADO» | la regla de posición va antes |
| denominador | lo saca el port (`port_estado`) | lo saca la vía (`motivo` del arnés) | es la vía la que cubre o no al volcán |
| Chillán | pares con las dos magnitudes | además, ambas mayores que 0 | el sellado haría log10(0) con un record publicado con magnitud 0 (no debería ocurrir; se declara) |
| veredicto | CANDIDATO a la fase 3 | PROPONER ADOPCIÓN | es la fase 4 |
| costura, borde del gránulo, S-1, soporte de la adenda 1 | informan | no se calculan | ya se informaron en el censo y no cambian con la vía, que tiene la misma máscara |

### 6 bis. Regla de posición (se aplica antes del §7)

- **Elegible**: brazo de posición cuyo P1 contra K no está VETADO.
- **Gana**: un elegible distinto de V cuyo **P2' contra V** da GANA. Si ganan los dos, el de menor E + E_lejana (sus
  errores en P2' contra K); a igual valor, V-pico (la distancia de MIROVA calza mejor con el pico, S165).
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
| 1 | algún control del §8 en rojo | **INDECIDIBLE** (si es la identidad: se arregla la vía y se repite la identidad; no se lee el resto) |
| 2 | ninguna posición elegible, o P1 VETADO | **NO ADOPTAR** |
| 3 | P2 o P2' contra K da PIERDE | **NO ADOPTAR** |
| 4 | P2 o P2' da SIN SUSTRATO | **INDECIDIBLE** |
| 5 | P2 o P2' da BLOQUEA, o P1 sólo OCR, o P1b con alguna, o M da EMPEORA, o una protegida que K publica salió del denominador por un motivo sellado | **DECIDE NICOLÁS**, con la lista |
| 6 | P2 y P2' dan GANA o EMPATE | **PROPONER ADOPCIÓN** (a Nicolás, A45) |

El criterio de victoria de `docs/MISSION.md` (sección «Criterio de victoria de la réplica») queda así: ninguna
protegida de 1 MW o más se pierde (filas 2 y 5), y bajo 1 MW una alerta perdida y una publicación de más pesan igual
(cada una vale 1 en E, filas 3 a 6).

## 8. Controles (antes de leer el veredicto)

1. **K = producción**: en cada pasada el K del arnés se compara con el record de `data/mirova_equivalent/`; una
   diferencia se re-corre en el `codigo_sha` del record guardado (`recorrer_en_sha.py` de MOD-B) y, si no se
   reproduce, el control queda en rojo. El predicado del evaluador da la misma publicación de K que el del runner.
2. **Identidad de punta a punta** (la pieza nueva): en cada pasada de C evaluable con grilla guardada por el censo
   (5.321), V del runner contra V-grilla: **misma máscara** (las mismas celdas alertadas), **mismo VRP a 0,001 MW** y
   **misma `distance_class`**. Una sola pasada distinta con el mismo gránulo deja el control en rojo. Las pasadas con
   otro gránulo (`otro_granulo`) se cuentan y se listan; si superan el 1 % de las 5.321, el control queda en rojo
   (la identidad no se habría medido). Se informa además, por pasada, la máxima diferencia de radiancia entre la
   grilla del runner y la del censo.
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
   rojo (programa §8.1). En las protegidas que salen por un motivo sellado, «K publica» se recalcula con el predicado
   del evaluador sobre el record de K; si no coincide con el runner, es falla del instrumento (como VCR-06 del
   sellado); si K la publica, se lista y lleva el veredicto a DECIDE NICOLÁS (§7, fila 5).
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
  V/MIROVA de 0,93 a 1,10 por tramo, contra 0,63 a 0,21 de K.
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
1. **Población** `poblacion_f4.json`: C re-etiquetada y E armada, con `tramo`, `solo_ocr`, la lista de cambios de
   etiqueta contra el censo y `sin_pasada_nuestra`.
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
| `pub_runner` | `{"K": 0 o 1}` del predicado corrido en el runner |
| `k_difiere_de_guardado`, `k_reproducida_en_su_sha` | control K = producción (§8.1) |
| de la población: `lab`, `vrp_mirova`, `solo_ocr`, `tramo` (`C` o `E`) | la vara |

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

## 13. Instrumento entregado: batería y mutaciones

Corrida del 2026-10-28 con el árbol quieto (sha256 de `evaluar_f4.py`, `probar_evaluar_f4.py`, `evaluar_vacio.py` y
`mutar_evaluar_f4.py` iguales antes y después; `ec6d062b…`, `3e483dd7…`, `4d883aec…`, `ef346a6a…`):

| qué | resultado | salida |
|---|---|---|
| batería (40 escenarios: 38 con predicado sintético, 2 con node sobre el tablero real) | 40 de 40 OK | `probar_evaluar_f4_salida.txt` |
| la misma batería contra el evaluador vacío | 40 de 40 fallan **por aserción**, 0 caen | `probar_evaluar_f4_contra_vacio_salida.txt` |
| mutaciones (una regla del documento por mutación, batería entera contra cada copia) | **46 de 46 atrapadas por aserción**, 0 vivas, 0 caen, 0 no aplican | `mutar_evaluar_f4_salida.txt` |
| control de identidad (sin mutación) | VIVA, como debe | ídem |
| control de caída (excepción al entrar a `evaluar`) | CAE, como debe (no se cuenta como atrapada) | ídem |

Qué NO prueba la batería: que el arnés escriba bien el contrato (eso es del candado), ni el predicado real del tablero
fuera de N01 y N02 (el sintético publica si el record es cumbre con VRP mayor que 0; los filtros de cirro, campo difuso
y el tope de 50.000 MW del tablero sólo se ejercen con node). Una mutación del placebo a ganancia 1,0 no se incluyó:
el control compara contra la misma constante y no podría verla (es un placebo inútil, no uno roto).

## 14. Lo que este pre-registro NO decide

- El encendido: lo decide Nicolás con el resultado en la mano (A45).
- La vara: lectura A, corte de 1 MW y pareo ±120 s quedan como están.
- MxD03 sola (#920), el diurno MODIS, el bow tie (MOD-E) y la caja por volcán.
- La regla de posición de VIIRS 750 y VIIRS 375: cada sensor la mide en su propio A/B.
