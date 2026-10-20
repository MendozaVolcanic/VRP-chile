# Pre-registro S157 (tarea 1.29): D25, fondo por vecinos, sobre K, con Nevados de Chillán como caso

Estado: **BORRADOR v2 PARA EL SELLO DE NICOLÁS** (con el resultado del probe del L1B incorporado en §8 b, §8 c y §9). Nada de esto se despacha sin su «sí» escrito y sin el candado del §7
(evaluador con sus pruebas y verificador limpio). Escrito el 2026-10-20 por una sesión lateral del loop, antes de
correr ningún brazo, y corregido el mismo día con los 20 hallazgos del verificador con contexto limpio (veredicto
PARCIAL, `verificador/INFORME.md`; qué cambió por cada hallazgo en el §10). Los números de sustrato salen de
`sustrato_k.py` (`sustrato_k_salida.txt`, regla S91) y de los scripts del verificador (`verificador/v1` a `v4`, con su
salida al lado); los de Chillán, del PR #869 (`experiments/_s157_magnitud_chillan/`, rama `s157-magnitud-chillan`,
verificador PARCIAL) y de la tarea 1.14 (`experiments/_s151_presupuesto_magnitud/README.md` §3.2 y §3.4). El resumen
para sellar está en `RESUMEN_SELLO.md`. El probe del L1B que informa la decisión §8 b está en `probe_l1b/`.

## 1. La pregunta, y por qué ahora

**El fenómeno.** De noche, en un cono nevado, el anillo de 5 a 25 km alrededor del volcán es sobre todo valle más
tibio que la cumbre. Nuestro pipeline resta como fondo la **mediana de ese anillo**; MIROVA (Coppola 2016a, p. 8,
ec. 6, y siete textos más del grupo, D25) resta la **media de los vecinos no alertados** del píxel caliente. Cuando el
entorno inmediato del cráter está más frío que el anillo, restamos de más: la magnitud sale baja y, si el foco es
débil, el exceso queda negativo y se recorta a 0,0 MW. Cuando el entorno está más tibio, restamos de menos.

**Ojo con quién resta el anillo hoy (verificador H1).** En VIIRS 375, cinco volcanes ya NO restan el anillo: Puyehue
Cordón Caulle, Villarrica, Chaitén, Planchón Peteroa y Lastarria tienen `local_kernel_bg: true` (`volcanoes.yaml`) y,
con `ENABLE_LOCAL_KERNEL_BG` encendido en K, restan la media de **temperatura** de sus 8 vecinos no alertados
(`process_viirs.py:1471`). Ahí D25 cambia casi nada: la tarea 1.14 midió 0,99 a 1,00 en esos volcanes. En VIIRS 750 no
hay kernel (`process_viirs_mod.py` recibe el parámetro y no lo usa): los 11 restan el anillo.

**Por qué ahora.** Con K la réplica ya calla donde MIROVA calla (adopción de S153, #850), y lo que falta es la
magnitud, sobre todo con el sensor oblicuo. En Chillán en erupción nuestra razón contra MIROVA cae con el cenit del
sensor: VIIRS 375 0,73 bajo 30°, 0,58 entre 30 y 50°, 0,45 sobre 50°; VIIRS 750 0,84, 0,41 y 0,16 (PR #869, §2.2).
De las palancas ya construidas, D25 es la que más mueve la magnitud hacia MIROVA (×1,28 [1,21; 1,35] en 468 pasadas
de VIIRS 375) y su efecto crece con el ángulo (×1,18 a nadir, ×1,41 en el borde; tarea 1.14, Tabla C2), pero se
midió dentro del brazo `literal` y sobre la detección anterior a K. Nunca se midió aislado ni sobre K.

**Lo que ya se sabe y acota la pregunta.** (a) PR #869 (verificado PARCIAL): en Chillán, en VIIRS 375 con cenit de 30°
o más, D25 **no puede** cerrar el déficit por construcción, porque ni restando un fondo cero se llega a MIROVA (G con
fondo cero 0,64 entre 30 y 50° y 0,68 sobre 50°); en VIIRS 750 y MODIS sí podría (0,96 a 1,48). Ese techo es de
Chillán, un foco de 330 K: en focos débiles el fondo pesa mucho más. (b) Evidencia previa en contra (verificador H16):
en VIIRS 375 el fondo del cúmulo ya se midió con criterio pre-registrado y no cerró la brecha en ningún volcán
(`docs/HYPOTHESIS_LOG.md`, H_S141_VECINO_FOCO_V2, no confirmada en S142), y el A/B de S143 (H_S143_D22_D25, D22 más D25
más segundo pase condicionado sin keep_peak) quedó en no adoptar. Las dos cosas fueron sobre la detección anterior a K
y con D25 mezclado con otras palancas: lo que este A/B agrega es D25 solo, sobre K.

**Lo que este A/B NO pregunta.** Si el resto del déficit angular es área del píxel (D17, tarea 1.36), selección de
vecinos (A99, A103) o el recorte del tablero en VIIRS 750 (tarea 1.8). D17 va después, sólo si queda dependencia con
el cenit.

## 2. Brazos, y por qué cada uno

| brazo | perfil | qué es | por qué está |
|---|---|---|---|
| K | `_s157_ab_d25_k_control` | la réplica K tal cual, sin MODIS | control: las pérdidas y la magnitud se cuentan contra lo que hoy se publica |
| K' | `_s157_ab_d25_k_gemelo` | K corrido otra vez | ruido del runner en la publicación (desempates que dependen de la CPU, S152). Para la magnitud no sirve de ruido (§5, H3) |
| D | `_s157_ab_d25_k_on` | K más `enable_vrp_bg_neighbor_mean_viirs375` y `_viirs750`, ventana hasta 7x7 | la palanca, con el valor del perfil |
| D1 (opcional, §8 b) | `_s157_ab_d25_k_on_h1` | D con sólo los 8 vecinos | la mitad abierta de la decisión de S142 (1 contra 3) |

`tests/test_perfiles_d25_k_s157.py` resuelve todas las constantes de `pipeline.profile` (A89) y comprueba: K es
producción salvo nombre, directorio y MODIS apagado; K' es K salvo nombre y directorio; D es K salvo los dos flags de
D25; D1 es D salvo la ventana. El verificador le hizo siete mutaciones (flag fuera de D, ventana 5x5 en D, D25 en el
gemelo, MODIS en el control, `vent_anchored` apagado en D, `SENSOR_MODIS` fuera de `FLAGS_BRAZO`, producción de vuelta
al Test 1) y las siete la hacen fallar por aserción (`verificador/v2_salida.txt`).

**MODIS va apagado en los cuatro brazos, y queda FUERA del A/B.** D25 no existe en `process_modis`: ningún flag lo
lee (`grep -c "NEIGHBOR\|neighbor_mean" pipeline/process_modis.py`: 0). MODIS sólo tiene el kernel local 3x3 en
temperatura, opt-in para 5 volcanes (Chillán no está). El PR #869 pedía el criterio de magnitud «en VIIRS 750 y
MODIS»; en MODIS no hay palanca que medir sin tocar `pipeline/` con su ciclo A45. Lo que sí se mide sin tocar el
código es el análogo en el probe del L1B (`probe_l1b/`, brazos `kernel3` y `d25_rad` sobre las dos pasadas MODIS de
Chillán del 18-oct), y eso informa si vale la pena escribir el flag (decisión §8 c). Apagar MODIS ahorra sólo el
proceso: el L1B de MODIS se sigue bajando (`fetch` no lee `SENSOR_MODIS`, verificador H17).

## 3. Dónde llega el flag (A118): consumidores del fondo y de la magnitud

D25 cambia el VRP de cada píxel alertado **después** de que la máscara de alertados quedó fija, así que no cambia qué
píxeles se detectan. Pero la magnitud por píxel tiene más consumidores que la suma, y cada uno puede mover lo que el
tablero publica. Leído en el código de `origin/main` 8c94c847b (sin cambio en esas líneas hasta f101d7304):

| consumidor | recibe el fondo de D25 | qué puede cambiar | cómo lo ve el evaluador |
|---|---|---|---|
| VRP por píxel del bloque contextual (`process_viirs.py:1492`, `process_viirs_mod.py:1047`) | sí | la magnitud | métrica M |
| kernel local de VIIRS 375 en 5 volcanes (`process_viirs.py:1471`) | D25 lo **reemplaza** | casi nada (1.14: 0,99 a 1,00) | M estratificada con y sin kernel |
| selección del cúmulo primario (`clustering.py:144` a `:153`, `vent_anchored`) | sí | el ranking usa sólo cúmulos con VRP mayor que cero y gana el más cercano: un cúmulo del cráter en 0,0 MW pierde contra uno lejano con VRP, y D25 puede devolverlo (**`far` pasa a `summit`**) o dejarlo en cero (al revés) | P4, contando aparte las pasadas cuyo `distance_class` cambia |
| píxel de más energía (`anomaly_pixels[0]`, `process_viirs.py:1536`, `process_viirs_mod.py:1081`) y filtro de distancia de `store.py:381` a `:435` | sí | si el píxel de más VRP cae fuera del radio y el cúmulo no rescata, el record queda con `vrp_mw = 0` y `discarded_reason` | P5 cuenta los `discarded_reason` que cambian |
| keep_peak y núcleo F5' (`store.py`, desde `anomaly_pixels`) | sí | el píxel ancla del núcleo de VIIRS 375 | M y P4 |
| modo de un píxel (`apply_single_pixel_mode`, umbral de magnitud del cúmulo) | sí | si el cúmulo se informa como suma o como su píxel mayor: un salto no lineal | M; P5 cuenta las pasadas que cambian de modo |
| tope D9 de 5 MW (camino D solo, fondo bajo 270 K) | sí, se aplica después (`process_viirs.py:1590`) | **esconde** el alza de D25 en escenas frías | P5 cuenta `d9_capped` en D contra K |
| filtros del tablero `isCirrusArtifact` y `isDiffuseFieldArtifact` | sí (leen la magnitud) | apagan una publicación que D25 sube sobre su umbral (calibrado con el fondo del anillo), o destapan una que baja | P1 y P2 vía el predicado con node (A97). La dirección «destapa» tiene 0 casos hoy en las dos ventanas (verificador H13) |
| recomputes del Test 1 (`process_viirs.py:1958`, `:1989`; `process_viirs_mod.py:1278`, `:1302`) | sí | nada: el Test 1 está apagado en K | huella: 0 `triggered_test1` |
| `vrp_vent_mw` (camino del vent) | **no** (anillo) | nada en el tablero bajo K | no se mide |
| MODIS | **no existe** | nada | fuera del A/B (§2) |

## 4. Ventanas, por tramo de calidad de la referencia (A119)

Los brazos corren el mismo código desde un tag (§6), así que la frontera de #535 (A104) no separa regímenes de código
entre brazos; lo que sí manda es la calidad de la referencia. Se reusan las ventanas de F/K, con V1 estirada hasta el
18-oct para meter la mañana de Chillán que motivó esto.

- **V1, 2026-08-29 a 2026-10-18** (51 días). Decide la tabla y el OCR. Trae a Chillán en erupción desde el 28-sep.
  Pisa el hito del OCR de Suomi NPP (hasta el 2026-10-09 la distancia y la clase de una fila sólo OCR pueden ser de
  otra pasada): esas pasadas no deciden con la lectura A en ninguna prueba, se listan; y el del 2026-10-10
  (`ALERTA_SIN_GEOMETRIA_OCR`): estrato aparte, no son alerta de la lectura A, en M sólo informan. Referencia congelada
  en `_congelado_v1/` (Mirova-v1@`35a5ea86`, 2026-10-20 10:29 UTC, con las dos capas del repo; `congelar.py`, copia sin
  cambios del de F/K; sha256 LF comprobados por el verificador). **Con gemelo.**
- **V2, 2026-04-01 a 2026-06-12** (73 días, el poder del veto, sobre todo Láscar). Decide **la tabla sola**: el
  evaluador reetiqueta de verdad sacando las filas del OCR (S150, H7). VIIRS por pasada desde abril (A119 b). Pisa el
  hito de NOAA-21 del 2026-04-09 (inocuo: `sin_info` igual en todos los brazos, como en F/K). Referencia: la
  congelada de F/K (`experiments/_s151_prereg_fk_11/_congelado_v2/`), misma ventana. Se despacha en dos mitades,
  **V2a 04-01 a 05-07** y **V2b 05-08 a 06-12**. Sin gemelo: las pérdidas que caigan acá se resuelven con la
  repetición dirigida de F/K (§5 de su pre-registro).
- **Chillán** no tiene K en disco antes del 2026-09-18 (su histórico con K se está rearmando), así que en el sustrato
  entra sólo desde esa fecha. En el A/B los brazos lo reprocesan entero, en las dos ventanas.

**Sustrato con K, medido en disco** (`sustrato_k_salida.txt`; conteos con la regla ORIGINAL de alertas mínimas, la SN
la aplica el evaluador; controles C1, C2, C3 y CK en verde; C1 es una prueba de regresión del cargador contra el 158 de
F/K, no un control positivo de V1, verificador H15):

| | V1 VIIRS 375 | V1 VIIRS 750 | V2 VIIRS 375 | V2 VIIRS 750 |
|---|---|---|---|---|
| protegidas A que K publica / las que deciden (sin las sólo OCR de Suomi NPP) | 38 / 31 | 31 / 29 | 38 / 38 | 42 / 42 |
| fracción de pérdida detectable al 80 %, con las que deciden | 5,1 % | 5,4 % | 4,1 % | 3,8 % |
| alertas bajo 1 MW / las que K publica | 279 / 259 | 38 / 21 | 385 / 362 | 75 / 49 |
| negativos limpios / los que K publica | 945 / 23 | 1.497 / 14 | 871 / 36 | 1.635 / 20 |
| **cúmulos del cráter en 0,0 MW en negativos (lo que D25 puede ENCENDER)** | **0** | **17** | **2** | **21** |
| ídem en alertas (lo que D25 puede RECUPERAR) | 4 | 11 | 6 | 23 |
| pares publicados con VRP de MIROVA, cenit ≤ 40° / > 40° | 166 / 131 | 29 / 23 | 211 / 189 | 64 / 27 |
| razón mediana con K, cenit ≤ 40° / > 40° | 0,72 / 0,52 | 0,66 / 0,35 | 0,73 / 0,56 | 0,54 / 0,51 |

**La lectura que cambia respecto de S151.** Con la detección vieja (C0), D25 en VIIRS 750 encendía 268 de 268
negativos limpios con el cráter en cero (`experiments/_s151_d25_v750_disco/README.md`), y su cierre quedó condicionado
a la detección. Con K esa población es de **17 y 21 pasadas en VIIRS 750 y de 0 y 2 en VIIRS 375**: K ya no deja
cúmulos mudos en el cráter donde MIROVA no vio nada. El riesgo de sobre-publicación de D25 sobre K es **del orden** de
ese tamaño: el conteo no ve los cúmulos del cráter en 0,0 MW detrás de un primario lejano (§3, H5), una población chica
(3 y 1 en VIIRS 375, 0 en VIIRS 750, cota inferior del verificador H13). Es un techo de exposición, no una predicción:
el script clasifica, no corre el pipeline.

**En noches cambia aún menos (A94, verificador H8, `verificador/v3_salida.txt`).** En VIIRS 750, las 11 y 23 alertas
que D25 podría recuperar caen todas en noches que K ya publica por otra pasada, y los 17 y 21 negativos que podría
encender caen en noches en que K ya publica algo: **0 noches nuevas** en las dos ventanas. En VIIRS 375, los 2
encendibles de V2 serían 2 noches nuevas. O sea que en VIIRS 750 D25 es una pregunta de magnitud, no de qué ve el
operador por noche, igual que lo que anotó D25 en S145.

**Pares de M por población** (`verificador/v1_salida.txt`): en VIIRS 375 con cenit ≤ 40°, de 166 pares en V1 son 63 de
volcanes con kernel, 16 de Chillán y 87 de otros; en V2, 103 con kernel y 108 de otros. En VIIRS 375 con cenit > 40°,
131 pares en V1 (28 de Chillán) y 189 en V2 (ninguno de Chillán). Entre 30 y 40° caen 42 pares en V1 y 57 en V2.

## 5. Métricas y reglas, por sensor, por tramo de cenit y por ventana

Todo se cuenta por pasada, contra K, **sólo en VIIRS 375 y VIIRS 750** (cobertura, determinismo, protegidas, P1, P2 y
M; MODIS no está en los brazos, H4), con la **lectura A** (D-4) y la **regla SN** de D-9 (MISSION), informando también
la regla original; si discrepan, manda la más estricta (como en F/K). «Publica» es el predicado de
`frontend/index.html` ejecutado con node (A97). Tramos de cenit del sensor: **≤ 40° y > 40°**. El 40° es el corte de
D17 (nota S141), **elegido** para que la tarea 1.36 compare con lo mismo; no coincide con las bandas de #869 (< 30°,
30 a 50°, ≥ 50°), que se informan además (H7).

| prueba | qué cuenta | regla | dónde decide |
|---|---|---|---|
| **P1 veto** | protegidas A que deciden, que K publica y D no | VETADO con una pérdida neta; ruidosa (K' también cambia) deja INDECIDIBLE; en V2, PENDIENTE DE REPETICIÓN (repetición dirigida de F/K, tope dos) | VIIRS 375 y 750, las dos ventanas |
| **P1b cruce de 1 MW** | protegidas A que K muestra con 1 MW o más y D bajo 1 MW | se listan; con una o más, decide Nicolás (regla de F/K §5) | ídem |
| **P2 suma bajo 1 MW** | alertas Muy Bajo que el brazo no publica + publicaciones en negativos limpios | GANA si la suma de D es menor que la de K menos el ruido; PIERDE si es mayor que la de K más el ruido; si no, EMPATE. Ruido = pasadas discordantes entre K y K' (en V2, la fracción medida en V1). Decide **por pasada**, como F/K; se informa también **por noche-volcán** (A94), y si discrepan se dice en la primera línea del veredicto | VIIRS 375 y 750, las dos ventanas |
| **M magnitud** | en las alertas que K y D publican y tienen VRP de MIROVA: d = abs(log10(D/MIROVA)) − abs(log10(K/MIROVA)) | mediana de d con intervalo bootstrap al 95 % **por bloques de noche-volcán** (las pasadas de una misma noche no son independientes, H9), 10.000 remuestreos, semilla fija. **MEJORA** si el intervalo queda entero bajo 0; **EMPEORA** si queda entero sobre 0; si no, **NEUTRO**; con menos de 5 pares o menos de 3 noches, **SIN SUSTRATO**. Sin umbral de ruido: el gemelo da la magnitud idéntica por construcción (1.14: «1,00 exacto»), así que su ruido es 0 y no se usa (H3) | ver abajo |
| **P4 el cúmulo se mueve** (informa, condiciona) | pasadas donde el centroide del cúmulo publicado de D se aleja más de 0,01 km del de K; aparte, las que cambian de `distance_class` | se informan con su volcán; si alguna es protegida, la auditoría espacial A61 de todas las movidas va antes de cualquier adopción | no decide |
| **P5 consumidores** (informa) | `d9_capped`, cambio de modo de un píxel, `discarded_reason` que cambia, publicaciones apagadas o destapadas por los filtros del tablero, `diag_bg_vecinos_n_sin_vecinos` | se informan | no decide |

**Dónde decide M.** Por ventana, en estos estratos:

| estrato | decide | por qué |
|---|---|---|
| VIIRS 750, cenit ≤ 40° y > 40° | en las dos direcciones | los 11 restan el anillo; #869: D25 puede cerrar (techo 0,96 a 1,48 en Chillán) |
| VIIRS 375 sin kernel, cenit ≤ 40° | en las dos direcciones | restan el anillo y el fondo pesa |
| VIIRS 375 sin kernel, cenit > 40° | **sólo hacia EMPEORA** (un EMPEORA bloquea CUMPLE; un MEJORA no cuenta), opción recomendada del §8 a | el techo de #869 vale sólo para Chillán (28 de 131 y 0 de 189 pares); en los focos débiles D25 puede pasarse (1.14: ×1,72 Isluga, ×2,37 Tupungatito) |
| VIIRS 375 con kernel (5 volcanes) | no decide; se informa | ya restan vecinos: predicción d ≈ 0 (1.14: 0,99 a 1,00), y meterlos diluye la mediana (H1) |
| Chillán, cada sensor y tramo | no decide por sí solo; se informa aparte | es el caso, no la muestra |

Además se informa M **por volcán** (A83, S126), las alertas `ALERTA_SIN_GEOMETRIA_OCR` aparte, y **los pares que salen
de M** en cada dirección (pasadas que K publica y D no, y al revés), porque una pasada que D25 lleva a 0,0 MW es el
peor alejamiento posible y no entra a M: queda en P1 o P2. Con la regla SN las alertas de VIIRS 375 de 0,05 MW o menos
son «MIROVA no vio nada» y **no entran a M** (H14).

**Nulo de M que puede fallar (A110, A116; reemplaza al nulo «K' en lugar de D», que no tenía camino para dar rojo,
H3).** Calibración de la regla sobre los datos reales: se toman los pares de cada estrato que decide, se reemplaza la
magnitud de D por la de K multiplicada por exp(±e), con e la magnitud observada de log(D/K) en ese par y el signo al
azar (efecto de tamaño real, sin dirección), y se aplica la regla M. Se repite 200 veces con semillas fijas. **La regla
está bien calibrada si da MEJORA o EMPEORA en 5 % o menos de las repeticiones** en cada estrato; si da más (por ejemplo
porque los bloques de noche no alcanzan a absorber la dependencia), M de ese estrato queda INDECIDIBLE. Control
positivo en el mismo instrumento: con el signo fijo hacia MIROVA, la regla tiene que dar MEJORA en más del 80 % de las
repeticiones en los estratos con 20 pares o más; si no, M no tiene poder ahí y se dice.

**Por qué este criterio de magnitud sale de los datos de MIROVA (A115).** No hay un umbral elegido para la magnitud: la
vara es el VRP que MIROVA publicó en cada pasada, la pregunta es si D queda **más cerca** de ese valor que K, en la
escala logarítmica (que castiga igual pasarse que quedarse corto: el probe de S151 dio razón mediana 1,19 en los
rescates de VIIRS 750, o sea que D25 también puede pasarse), y el nivel de la regla se calibra contra los mismos datos.
Lo elegido, y dicho como elegido: el corte de 40°, el 95 % del intervalo, el 5 % de la calibración y los mínimos de 5
pares y 3 noches.

**Predicciones (escritas antes de correr; no deciden).**
1. VIIRS 375 sin kernel, cenit ≤ 40°: M MEJORA (la razón sube desde ~0,72; 1.14 midió ×1,18 a nadir en `literal`).
   Evidencia en contra: H_S141_VECINO_FOCO_V2 y H_S143_D22_D25 (§1 b).
2. VIIRS 375 sin kernel, cenit > 40°: la razón sube; en Chillán queda bajo 0,6 (techo de #869); en Isluga y
   Tupungatito puede pasarse de 1.
3. VIIRS 750: M MEJORA en los dos tramos; en Chillán con cenit ≥ 50° la razón publicada queda bajo 0,5, porque el
   recorte del tablero (F_rec 0,57 en ese tramo) no depende del fondo.
4. VIIRS 375 con kernel: d ≈ 0 (mediana de abs(d) bajo 0,02).
5. P2: EMPATE en VIIRS 375 (0 y 2 cúmulos que encender); en VIIRS 750 el signo por pasada no lo predigo (17 y 21 que
   encender contra 11 y 23 que recuperar); por noche, sin cambio.
6. P1: CUMPLE. Si cae alguna, en VIIRS 750 de Lastarria o Tupungatito (en VIIRS 375 Lastarria ya resta vecinos), donde
   el entorno inmediato puede estar más tibio que el anillo.

## 6. Despacho (no despachar sin el sello)

**Antes del primer despacho**, en este orden: (a) el sello de Nicolás sobre este documento y las decisiones del §8;
(b) el candado del §7 mergeado y verificado; (c) el reproceso de Chillán y el histórico con K terminados o con cupo:
con el NRT (11 jobs) y otro reproceso vivo no queda margen en el tope de 20 jobs; nunca más de dos A/B vivos; (d) el
tag sobre `main` y su commit completo:

```bash
git tag -a s157-d25-k-codigo -m "codigo del A/B de D25 sobre K" origin/main
git push origin s157-d25-k-codigo
git rev-parse s157-d25-k-codigo^{commit}
```

**Cada despacho desde el tag**, nunca desde `main` a secas (A108; S152), y el siguiente **recién cuando el anterior
terminó**: antes de cada despacho, `gh run list --workflow reproc-s146-ab-sin-test1.yml --json status -q
'[.[]|select(.status!="completed")]|length'` tiene que dar 0 (grupo `s146-ab-sin-test1`, GitHub guarda un solo
pendiente por grupo y un tercero desplaza al que espera; H18).

```bash
ONCE='["Lascar","Lastarria","Isluga","Tupungatito","PlanchonPeteroa","NevadosDeChillan","Llaima","Villarrica","Copahue","PuyehueCordonCaulle","Chaiten"]'
gh workflow run reproc-s146-ab-sin-test1.yml --ref s157-d25-k-codigo -f preregistro_aprobado=si -f start=2026-08-29 -f end=2026-10-18 -f vols="$ONCE" -f brazos='["_s157_ab_d25_k_control","_s157_ab_d25_k_gemelo","_s157_ab_d25_k_on"]' -f control=_s157_ab_d25_k_control
gh workflow run reproc-s146-ab-sin-test1.yml --ref s157-d25-k-codigo -f preregistro_aprobado=si -f start=2026-04-01 -f end=2026-05-07 -f vols="$ONCE" -f brazos='["_s157_ab_d25_k_control","_s157_ab_d25_k_on"]' -f control=_s157_ab_d25_k_control
gh workflow run reproc-s146-ab-sin-test1.yml --ref s157-d25-k-codigo -f preregistro_aprobado=si -f start=2026-05-08 -f end=2026-06-12 -f vols="$ONCE" -f brazos='["_s157_ab_d25_k_control","_s157_ab_d25_k_on"]' -f control=_s157_ab_d25_k_control
```

Con la opción §8 b, se agrega `"_s157_ab_d25_k_on_h1"` a `brazos` en V1. Autentica sólo con `EARTHDATA_TOKEN` (A71);
`ubuntu-24.04` está fijado en el workflow.

**Costo, estimado** desde la tasa de F/K (`experiments/_s151_prereg_fk_11/duracion_runs.py --estimar`: 2,20 min por
día de ventana en un job sin Test 1 con los tres sensores, el job más lento 1,42 veces la mediana; sin procesar MODIS
debería ser algo menos, pero el L1B de MODIS se sigue bajando, H17, y no está medido): V1, 33 jobs de ~112 min (peor
~159), ~10 a 15 h de pared con 6 en paralelo; V2a y V2b, 22 jobs de ~80 min (peor ~115) cada uno, ~6 a 8 h cada uno.
En serie, **~22 a 31 h de grupo ocupado**; con D1, un tercio más en V1. El peor job (159 min) queda bajo el tope de 300
con el margen de A15 (1,3 × 159 = 207).

## 7. Controles antes de mirar ningún resultado, y el candado del evaluador

**Controles del A/B** (si uno falla, lo que depende de él queda INDECIDIBLE y no se interpreta). Todos sólo sobre VIIRS
375 y VIIRS 750 (H4):
1. **Cobertura pareja** (A108): las mismas pasadas en los brazos de cada despacho, por volcán y sensor; contar las de
   cada brazo contra el control ANTES de mirar el veredicto. Y el control contra lo que hay en disco con K (producción
   desde el 2026-09-18, histórico con K antes): si en algún volcán y sensor VIIRS al control le falta más del 5 % de
   las pasadas, cobertura corta (el 5 % es del instrumento, heredado de F/K, elegido y no medido). Chillán antes del
   2026-09-18 se compara contra producción (C0): las pasadas no dependen del detector. MODIS no se compara.
2. **Versión de producto** igual entre brazos en toda pasada protegida.
3. **Cableado** (A118): la línea `FLAGS_BRAZO` de cada job trae los dos flags de D25, su ventana y `SENSOR_MODIS`
   con el valor declarado (agregados al workflow en este PR); y la **huella en los records**: D tiene
   `diag_bg_vecinos_n_sin_vecinos` en sus records con cúmulo, K y K' en ninguno; 0 `triggered_test1` en todos; 0
   records MODIS en todos.
4. **Determinismo de la publicación**: K' contra K, misma decisión de publicar en 98 de cada 100 pasadas o más, por
   sensor VIIRS (umbral heredado de S149 a F/K, elegido).
5. **Calibración de M** (§5): falsos MEJORA o EMPEORA en 5 % o menos de 200 repeticiones, y poder del control positivo.
6. **La referencia es la congelada, entera**: sha256 LF de los CSV y de las dos capas contra el `MANIFIESTO.json`.
7. **El predicado del tablero** es el de `frontend/index.html` con node; el evaluador imprime su sha256.

**Candado, a implementar y verificar ANTES de despachar** (como el de la adenda K del diurno):
- `evaluar_d25.py`: el evaluador de F/K (`experiments/_s151_prereg_fk_11/evaluar_fk.py`, P1, P2, ruido, repetición,
  lectura A y SN) con los brazos parametrizados (K, K', D, D1) **sin tocar el archivo de F/K**, con los sensores
  restringidos a VIIRS en cobertura, determinismo y protegidas sin record, más M por estrato con bootstrap por bloques
  y su calibración, P1b, P2 por noche, P4 y P5 de este documento.
- Sus pruebas, en `probar_evaluar_d25.py`, cada una tiene que **fallar por la razón que dice** (S140): MODIS en
  producción y ausente en los brazos da cobertura OK (H4); positivo de M (magnitud de VIIRS 750 de D llevada hacia
  MIROVA a la mitad de distancia en log: MEJORA); negativo de M (dividida por 20: EMPEORA); un EMPEORA en VIIRS 375 sin
  kernel con cenit > 40° bloquea CUMPLE y un MEJORA ahí no lo gana; un cambio en VIIRS 375 con kernel no decide; una
  protegida oculta en D: VETADO; una protegida sólo OCR de Suomi NPP oculta: no veta; una protegida que cruza 1 MW: P1b
  la lista; un negativo publicado de más en D: P2 lo cuenta; mutación del corte de 40° a 50° cae por una prueba con
  nombre; la calibración detecta una regla mal calibrada (bootstrap por pasada sobre pares duplicados por noche).
- Mutaciones del evaluador contadas sólo si las atrapa una aserción, con control de caída (memoria S156).
- Verificador con contexto limpio sobre el evaluador.

## 8. Decisiones para el sello

**a) VIIRS 375 oblicuo (cenit > 40°, sin kernel).** Recomendado: **decide sólo hacia EMPEORA** (un EMPEORA bloquea
CUMPLE, un MEJORA no cuenta), porque el techo de #869 es de Chillán (28 de 131 pares en V1, 0 de 189 en V2) y en los
focos débiles D25 puede pasarse. Alternativas: (i) decide en las dos direcciones; (ii) no decide, sólo informa (la
versión 1 de este documento; el verificador mostró que dejaba pasar una sobre-corrección).

**b) La ventana de D25 (1 contra 3).** Recomendado: **sólo D con hasta 7x7** (el valor del perfil). Se agrega D1 en
V1 sólo si el probe del L1B muestra, en los cúmulos de Chillán, que al menos la mitad de los píxeles alertados usan
ventana mayor que 3x3 **y** la magnitud publicada cambia más de 5 % entre `h3` y `h1` en alguna pasada. Los dos umbrales
son elegidos. **Si el probe no tiene resultado al momento del candado, rige la opción por defecto: sólo D** (H10).
**Resultado del probe (run 39428997189): `h3` y `h1` dan magnitudes idénticas en los 10 gránulos; por esta regla, sólo
D** (`probe_l1b/README.md`, Resultado).

**c) MODIS.** Recomendado: **fuera de este A/B**, y decidir si se escribe el flag de D25 en MODIS (ciclo A45) con el
resultado del probe (`kernel3` y `d25_rad` en las dos pasadas MODIS de Chillán). Alternativa: escribir el flag antes y
meter MODIS en este A/B; retrasa todo y su sustrato es chico (12 protegidas que deciden en V1, 16 en V2). **Dato del
probe:** en Chillán el análogo de D25 sube MODIS ×1,32 y ×2,45 (razón 0,49 → 0,64 y 0,24 → 0,59), y el kernel 3x3
que ya existe da lo mismo a 0,1 %.

**d) Qué hacer con cada veredicto.**

| resultado | qué se hace |
|---|---|
| P1 CUMPLE, P2 sin PIERDE en ningún sensor ni ventana, M MEJORA en al menos un estrato que decide **en cada ventana** (V1 y V2) y EMPEORA en ninguno (H9) | **CUMPLE**: se abre el ciclo de adopción (tag defensivo, R2 por píxel, verificador independiente, «sí» de Nicolás; A45, S33) |
| ídem pero M MEJORA en una sola ventana | decide Nicolás con la tabla por estrato y por volcán |
| M NEUTRO o SIN SUSTRATO en todos los estratos que deciden | **SIN EFECTO**: D25 es fidelidad literal (siete textos del grupo), pero no mueve la magnitud sobre K. Decide Nicolás |
| M MEJORA en un estrato y EMPEORA en otro | decide Nicolás con la tabla por estrato |
| P1 VETADO, o P2 PIERDE en algún sensor y ventana | **NO CUMPLE**: no se adopta; cada pérdida se diagnostica (cabecera de la imagen de MIROVA, A61) |
| P1b con alguna protegida bajo 1 MW | decide Nicolás con la lista |
| INDECIDIBLE o PENDIENTE | repetición dirigida (tope dos, F/K §5); un INDECIDIBLE de controles no se repite, se busca el defecto |

## 9. Lo que este A/B no puede decir

- **MODIS** (§2). Ni la inconsistencia de longitud de onda de MODIS con K (banda 22 para la temperatura, banda 21 para
  volver a radiancia; hallazgo lateral de #869, ×1,05 a 1,06).
- **D17**: si después de D25 la razón sigue cayendo con el cenit, D17 queda como hipótesis (tarea 1.36), con el
  contraste por zona de agregación que propuso #869.
- **Selección**: D25 no agrega píxeles. En Chillán el probe del L1B midió que los vecinos del cúmulo son cumbre nevada
  más fría que el anillo y que, aunque MIROVA los sumara todos, aportarían 0,06 a 0,70 MW contra 2 a 17 MW que faltan:
  ahí la selección no es la palanca.
- **El poder del veto fuera de Láscar y Chillán**: como en F/K, en los otros volcanes hay 3 protegidas o menos por
  sensor y ventana (`sustrato_k_salida.txt`, tablas por volcán).
- **El día**: los brazos son nocturnos; el A/B diurno sobre K es otra tarea (1.32).

## 10. Qué cambió de la versión 1 a la 2 (verificador con contexto limpio, `verificador/INFORME.md`)

| hallazgo | gravedad | cambio |
|---|---|---|
| H1 kernel local en 5 volcanes de VIIRS 375 | 2 | §1, §3 y §5: M estratificada con y sin kernel; decide sin kernel; predicciones 4 y 6 |
| H2 VIIRS 375 oblicuo excluido con un argumento de Chillán | 2 | §5 y §8 a: decide sólo hacia EMPEORA (recomendado), con los conteos por volcán |
| H3 ruido de M y nulo que no pueden fallar | 2 | §5: ruido de M = 0 declarado; nulo reemplazado por la calibración con signo al azar y su control positivo |
| H4 MODIS apagado contra un evaluador con tres sensores | 2 | §5 y §7: todo sólo VIIRS; prueba del candado con MODIS en producción |
| H5 selección del cúmulo mal descrita | 3 | §3: el filtro de VRP > 0 cambia `far` por `summit`; P4 cuenta los cambios de etiqueta |
| H6 veto con protegidas que no deciden | 3 | `sustrato_k.py` gana la columna `pAdec`; §4 usa 31 y 29 |
| H7 el 40° no es de #869 | 3 | §1 y §5: 40° declarado como el corte de D17, elegido; bandas de #869 informadas |
| H8 P2 por pasada contra noche | 3 | §4 y §5: P2 decide por pasada (como F/K) y se informa por noche; v3 del verificador citado |
| H9 CUMPLE con un estrato cualquiera; bootstrap por pasada | 3 | §5 y §8 d: bootstrap por bloques de noche-volcán; MEJORA en cada ventana |
| H10 §8 b sin salida si el probe no corre | 3 | §8 b: opción por defecto y umbrales declarados como elegidos |
| H11 el probe atribuye al primer pase | 4 | `probe_l1b/probe_chillan.py` captura el segundo pase (columnas `sp_`); `prueba_probe.py` lo compara con `second_pass_adjacent`: 60 píxeles nuevos, 0 discrepancias, y la mutación que reconstruye con `min` en lugar de `max` da 1.867 |
| H12 píxel de más energía y filtro de distancia | 4 | §3: fila nueva; P5 cuenta `discarded_reason` |
| H13 rescatable no ve primarios lejanos | 4 | §4: «como mucho» pasa a «del orden de», con la cota del verificador |
| H14 SN, sin geometría y pares que salen de M | 4 | §5: las tres cosas fijadas |
| H15 C1 es regresión, no positivo de V1 | 4 | §4: dicho así |
| H16 evidencia previa en contra | 4 | §1 b y predicción 1 |
| H17 costo de MODIS | 5 | §2 y §6 |
| H18 frase de despacho contradictoria | 5 | §6: «cuando el anterior terminó» |
| H19 conteos con la regla original | 5 | §4 y salida del sustrato rotulados |
| H20 detalles del resumen | 5 | `RESUMEN_SELLO.md` |

El verificador dejó **VERIFICADO LIMPIO**: las cifras del §4 (re-corrida idéntica), las de #869 y 1.14, las líneas del
§3, que ningún flag de D25 llega a MODIS, los perfiles y sus siete mutaciones, el cambio del workflow, la referencia
congelada, las ventanas contra A119, y que el probe reproduce el primer pase real (384 vecinos, 0 discrepancias) con
controles que pueden fallar y un brazo MODIS `d25_rad` que es un análogo honesto de D25.
