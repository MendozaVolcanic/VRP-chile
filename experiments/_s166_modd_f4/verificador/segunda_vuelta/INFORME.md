# Segunda vuelta del verificador: pre-registro S166 MOD-D fase 4 (arreglos de VF4-01 a VF4-12)

- Árbol medido: `ff03538dd` (HEAD de la rama `claude/focused-pascal-db1501`); `git diff HEAD` de los cuatro archivos de código y del pre-registro vacío. sha256 de `evaluar_f4.py` `7b5bf045…`, de `probar_evaluar_f4.py` `dbb219ce…`.
- Hora: 2026-10-28 08:54 (hora local del equipo; el servidor no lo pedí, no hay red).
- Qué corrí: batería completa (`bateria_mia.txt`: 53 de 53 OK, código 0); 5 escenarios contra el evaluador vacío (5 de 5 fallan por aserción; el vacío completo del autor, 53 de 53, lo leí en su salida, no lo re-corrí entero); 14 escenarios propios (`escenarios_2v.py`, `escenarios_2v_b.py`, salidas `escenarios_2v_salida.txt`, `escenarios_2v_b_salida.txt`); 12 mutaciones propias (`mutar_2v.py`, `mutar_2v_salida.txt`), con el medidor del autor sin modificar.
- Qué NO hice: no re-corrí las mutaciones M55 a M66 del autor (la máquina estaba saturada y el autor tiene su propia corrida en curso; verifiqué por lectura que cada una apunta a un escenario que asevera la regla). No leí `resultado_censo.json` (no está en esta rama). Sin red: nada de HEAD contra LAADS.

## Tabla de estados

| id | estado | evidencia |
|---|---|---|
| VF4-01 | **CERRADO** | `evaluar_f4.py` `regla_posicion` l. 437-438 (elegible exige `p1_vs_V` no VETADO) y l. 694-695 (`protegidas_que_otra_posicion_publica`), `veredicto` l. 659. Mi T1a (el S1 del primer verificador): V-pico ya no se elige, `PROPONER` sobre V, `P1 V-pico vs V: VETADO`. T1d (S2): V sigue, veredicto `DECIDE NICOLÁS`, protegida listada. T1b (pérdida sólo OCR): elegible pero `DECIDE`. Residuo menor: N-07. |
| VF4-02 | **CERRADO EN PARTE** | La circularidad cae: `control_identidad` l. 455-473 ya no lee `con_grilla` de la identidad, exige `n_pob == 5321`; E11, E41 y M13, M49 lo vigilan. Pero se puede esquivar por otra puerta (N-01, T2a/T2c) y el `==` no está fijado a la medición (X05 viva). |
| VF4-03 | **CERRADO EN PARTE** | Las dos claves nombradas dan rojo (l. 604-606 y 628, E42, M50, M51, M67). Misma familia sigue abierta: N-05 (T3a, T3b'). |
| VF4-04 | **CERRADO EN PARTE** | De las 12 mutaciones vivas del primer verificador, 11 tienen escenario y mutación (A01..A12 → M55..M66, E43-E49; mapeo leído, no re-corrido). Queda A13 (Chillán exige ambas magnitudes mayores que 0): mi X03 sale VIVA. Y la salida guardada del medidor no sostiene la cifra (N-02). |
| VF4-05 | **CERRADO** | `_lab` l. 204-207; `contribuciones`, `pares_m`, `chillan`, `curva_*`, `razon_protegidas` usan `f["lab"]`; sólo `p1` y `control_cobertura` usan la unión, como declara §5. E35 y M35. |
| VF4-06 | **CERRADO EN PARTE** | Protocolo escrito (§7) e implementado (`rojo_solo_en_e` l. 614-621, `evaluar` l. 704-718; E50, M52-M54; X15 y X16 atrapadas). Es a prueba de fallos (la segunda pasada re-evalúa C y, si queda rojo, INDECIDIBLE). Huecos en N-03, N-04 y N-06 (frontera 16/17 sin vigilar: X01 y X02 vivas). |
| VF4-07 | **CERRADO** (texto) | §4 define «sirve» como HEAD 200 de L1B y MxD03 de cada pasada. Que el HEAD responda 200 con las credenciales del runner: SIN DATO. Colisión con el protocolo E: N-04. |
| VF4-08 | **CERRADO** | `mutar_evaluar_f4.py` l. 130 (ROTA si el código es 1 y no hay escenario fallido) y `probar_evaluar_f4.py` l. 771-774. Mis controles: `CONTROL_ROTA` (SyntaxError) y `CONTROL_SYSEXIT` (`sys.exit(1)` al importar) salen ambos ROTA. Residuo: N-02. |
| VF4-09 | **CERRADO** | E51 corre `main` con archivos, compara con la llamada en memoria y prueba la población sin lista; `Uso` (l. 26) incluye `--poblacion`; M67. |
| VF4-10 | **CERRADO EN PARTE** | §6 restituye `soporte_independiente` al leer. La función del tag (`evaluar_paquete.py` l. 351) exige `nuestros` y `alertas_mirova`, que no están en el contrato del §11: N-08. |
| VF4-11 | **CERRADO** | 23 protegidas: `LOOP_OBJETIVOS.md` (origin/loop/activo l. 941) «2.648 filas y 23 protegidas». «2 a 7 gránulos»: `cmr_cola_salida.txt` (mínimo 2 en `MYD021KM 6.1` del 26-oct, máximo 7). Curva de K del §10: coincide con la que cita el primer verificador del censo; no pude re-leer `resultado_censo.json` (SIN DATO propio). |
| VF4-12 | **CERRADO** | §6 bis l. 184-186 declara el desempate como preferencia a priori, con la objeción de S165. |

## Hallazgos nuevos, por gravedad

### N-01 (gravedad 3). La identidad se puede esquivar con un motivo sellado: una pasada con grilla del censo que el runner marca «volcán fuera del gránulo» o «escena inválida» sale de `con_grilla` y de los denominadores sin que nada se ponga rojo
- ARCHIVO:LÍNEA: `evaluar_f4.py` l. 462 (`con_grilla` se arma sobre `_ev(filas)`, que ya sacó los motivos sellados) y l. 469; `evaluable` l. 164-165.
- QUÉ PASA: las 5.321 pasadas con grilla del censo son, por construcción, pasadas donde el port sí cubrió el volcán. Si la vía del runner dice que no lo cubre, eso es un desacuerdo de identidad, pero la pasada desaparece de la lista que se exige y `n_pob` (que cuenta filas con `grilla_censo`, incluidas las sacadas) sigue en 5.321. `fuera_del_denominador` se informa pero no se juzga.
- CÓMO SE VE / REPRODUCIR: `python escenarios_2v.py T2a`: 10 de 70 pasadas con grilla marcadas `volcan_fuera_del_granulo` (y sin entrada en la identidad): `identidad OK n_pob 70 n_con_grilla 60 faltan 0`, veredicto `PROPONER ADOPCIÓN`; igual con `escena_invalida` (T2a'). `python escenarios_2v_b.py`: 69 de 70 marcadas → identidad OK con 1 pasada medida (el veredicto sólo cae por SIN SUSTRATO de mi mundo chico, no por la identidad).
- CONFIANZA: CONFIRMADO. Un fallo sistemático de lectura (geolocalización de MxD03, por ejemplo) se leería como «el volcán no está en el gránulo».
- Arreglo mínimo: contar en `con_grilla` toda fila con `grilla_censo` cuyo motivo sea sellado, y exigir que esas pasadas se declaren como `otro_granulo` (con el tope de 1 %) o como identidad distinta.

### N-02 (gravedad 3). La evidencia que cita el §13 no corresponde a los archivos, y el medidor imprime sus controles sin hacerlos cumplir
- ARCHIVO:LÍNEA: `PREREGISTRO_MODD_F4.md` l. 362-371 (40 escenarios, 46 mutaciones, hashes `ec6d062b…`, `3e483dd7…`, `4d883aec…`, `ef346a6a…`); `mutar_evaluar_f4_salida.txt`; `mutar_evaluar_f4.py` l. 150-162.
- QUÉ PASA: (a) hoy hay 53 escenarios y 67 mutaciones, y los hashes de `evaluar_f4.py` (`7b5bf045…`) y `probar_evaluar_f4.py` (`dbb219ce…`) no son los del §13; la tabla de 13 bis ya cita E51 y M67, o sea que el §13 quedó sin actualizar. (b) La salida guardada de las mutaciones (a las 08:54 todavía la de las 04:16) trae su propio control en rojo: `IDENTIDAD ATRAPADA (debe ser VIVA)`, porque E30 fallaba incluso sin mutación; fue anterior a la edición de E30. Eso hace espuria la fila `M25_sin_pasada_nuestra_ignorada`, cuyo único escenario fallido es E30 (lo comprobé leyendo las 67 filas: es la única). Y la línea final dice igual «67 de 67 atrapadas». (c) `main` del medidor no sale con código distinto de cero ni invalida la cifra cuando un control no sale como debe.
- CÓMO REPRODUCIR: `python` sobre `mutar_evaluar_f4_salida.txt` (filas cuyas fallas son sólo E30 → `M25`); leer l. 150-162 de `mutar_evaluar_f4.py` (no hay `sys.exit` ni condición sobre `ident`).
- CONFIANZA: CONFIRMADO. El autor tenía una corrida nueva en curso (proceso `mutar_evaluar_f4.py --paralelo 5`); SIN DATO lo que escriba. Mientras no termine con IDENTIDAD VIVA y el §13 se actualice, no hay respaldo escrito de la cifra.
- Arreglo: que el medidor termine con código 1 y la leyenda «NO VALE» si algún control no sale como debe; actualizar el §13 con la corrida nueva y sus hashes.

### N-03 (gravedad 2). El protocolo del tramo E trata una vía que no corrió como si fuera un 404
- ARCHIVO:LÍNEA: `evaluar_f4.py` l. 168-169 (`falla_via_*`), l. 593-594 y 614-621; §7 «Protocolo de fallo».
- QUÉ PASA: `sin_mxd03`, `geo_distinta` o `sin_grilla` en toda la cola son rojo de cobertura «sólo en E» y E se excluye; el veredicto sale de C. Pero esos tres motivos dicen algo de la vía con datos nuevos, que es la distribución que verá producción; el argumento del §7 («un 404 no dice nada de la vía») sólo cubre fallas de descarga.
- CÓMO REPRODUCIR: `python escenarios_2v.py T4a`: 8 pasadas de E con `v_marca = geo_distinta` → `PROPONER ADOPCIÓN`, `e_excluido: true` (queda declarado en la línea del veredicto de `main`, pero el veredicto no cambia).
- Relacionado, menor (T4c, T4d): un rojo de `k_produccion` sólo en E con cobertura OK da INDECIDIBLE; el mismo rojo más una falla de descarga en E da PROPONER, porque la exclusión lo borra.
- Arreglo: que el protocolo distinga falla de descarga (excluye E) de vía que no corrió (E excluido pero el veredicto máximo es DECIDE NICOLÁS), o que lo diga expresamente.

### N-04 (gravedad 2). Excluir un día de E por el HEAD (§4) choca con la regla de cobertura contra MIROVA (§8.6) y con el protocolo E
- QUÉ PASA: un día que se excluye de la población deja pasadas de MIROVA «sin pasada nuestra» ese día; eso es rojo de cobertura sólo en E y saca E entero. Si en cambio el constructor de `sin_pasada_nuestra` ignora los días excluidos, una alerta de MIROVA (quizá protegida) desaparece sin declararse. El documento no dice cuál de las dos.
- CÓMO REPRODUCIR: `python escenarios_2v.py T4e` (una pasada de MIROVA el 19-oct sin pareja → `e_excluido: true`).
- Arreglo: una línea en §4 o §8.6: los días excluidos por HEAD entran a `sin_pasada_nuestra` con marca `dia_excluido` y no ponen rojo, pero se listan; o, al revés, ponen rojo.

### N-05 (gravedad 2). Misma familia de VF4-03: dos entradas más que dan OK por ausencia o por `None`
- `k_difiere_de_guardado: None` en todas las filas → `k_produccion OK` (`python escenarios_2v.py T3a`; l. 628 sólo pide que la clave exista). `pub_runner` ausente: en filas donde K no publica el default `or 0` coincide con el predicado, no se compara (T3b': OK; T3b con todas las filas sin la clave sí da rojo, porque algunas publican). Gravedad baja por separado; el patrón es el de A89.
- Arreglo: exigir `is True/False` en `k_difiere_de_guardado` y la clave `pub_runner` en toda fila `ok`.

### N-06 (gravedad 2). Reglas del documento que mis mutaciones dejan vivas (batería entera, 53 escenarios, contra una copia con UNA línea cambiada)
| mutación | regla | resultado |
|---|---|---|
| X01 `INICIO_E` 17 → 18 oct | frontera C/E del §4 y §7 | VIVA |
| X02 `>=` → `>` en `_es_e` | ídem (la pasada del 17 00:00) | VIVA |
| X03 Chillán sin exigir magnitudes mayores que 0 | cambio declarado en la tabla de §6 (la A13 del primer verificador) | VIVA |
| X04 elegibilidad contra V exige «SIN PERDIDA» | una pérdida sólo OCR contra V no quita elegibilidad | VIVA |
| X05 `n_pob >= 5321` | total exacto de la identidad | VIVA |
| X06 tope de otro gránulo exclusivo | «si superan el 1 %» | VIVA |
| X08 «otra posición» sólo con protegidas de la tabla | §6 bis, 3.ª viñeta | VIVA |
| X14 protegida sellada de K sólo de la tabla | §8.6 | VIVA |
| X15, X16 | filtro de E en `sin_pasada_nuestra`; declarar `e_excluido` | ATRAPADAS (E50; E30 y E50) |
| CONTROL_ROTA, CONTROL_SYSEXIT | VF4-08 | ROTA, ROTA (como debe) |
- Reproducir: `python mutar_2v.py` (≈ 1 h con la máquina cargada; salida en `mutar_2v_salida.txt`). Cada fila vive con 53 de 53 OK.
- X01 y X02 son las que más pesan: el 2026-10-17 es el corte entre «un rojo que toca C lo hace todo INDECIDIBLE» y «E se excluye». Verifiqué que `poblacion.json` de C termina el 2026-10-16 08:15 (ninguna pasada de C con fecha ≥ 17-oct), así que la regla por fecha es coherente; falta sólo que un escenario la fije.

### N-07 (gravedad 1). Texto y código no calzan en dos frases
- §6 bis dice «protegida **de la tabla**» para la viñeta de «otra posición»; el código (l. 694-695) también lista las sólo OCR (T1c: `DECIDE NICOLÁS`). Es el lado seguro, pero está sin vigilar (X08).
- La fila P1 de la tabla de §6 dice «el brazo no es elegible y el veredicto es NO ADOPTAR»; con §6 bis puede ser PROPONER si otro brazo es elegible (E24). `veredicto` l. 650-651 («P1 VETADO») es código inalcanzable.

### N-08 (gravedad 1). `soporte_independiente` necesita entradas que el contrato del §11 no trae
- La función sellada pide `nuestros` (detecciones de otros sensores) y `alertas_mirova`; el §6 dice «al leer» sin decir de dónde salen. No cambia ningún veredicto.

## Lo que verifiqué limpio

- Batería actual: 53 de 53 OK (`bateria_mia.txt`). Contra el vacío (5 escenarios míos, más lectura de la salida del autor, 53 de 53 por aserción, 0 caen).
- `soporte_independiente` existe en el tag `s162-modd-tag`; «23 protegidas», «2 a 7 gránulos» y el §10 son consistentes con sus fuentes.
- El protocolo de E es a prueba de fallos: un error de `rojo_solo_en_e` sólo puede producir INDECIDIBLE, porque la segunda pasada re-evalúa C (M54 y X15 lo muestran).
- Frontera de fecha: T4b (falla 16-oct 23:59 → INDECIDIBLE) y T4b' (falla 17-oct 00:00 → E excluido).
- Chillán con magnitud 0 no cae: T5 da SIN SUSTRATO con 4 pares (el guard de l. 341 funciona; lo que falta es que un escenario lo fije, X03).

## SIN DATO

- Que el HEAD a LAADS responda 200 con las credenciales del runner (§4).
- Salida nueva de las mutaciones del autor (en curso); mis propias M55 a M66.
- `resultado_censo.json` (curva de K del §10) en esta rama.
- Todo lo que dependa del arnés, la población y la identidad reales (no existen aún, §11).
