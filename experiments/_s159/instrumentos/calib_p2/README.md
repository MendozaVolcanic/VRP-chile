# Calibración de P2 (D-42) y candados de V34-03 y V29-01

Vara: `experiments/_s157_prereg_d25/ADENDA_CALIBRACION_P2.md` (sellada por Nicolás el 2026-10-22, commit `ca65069f6`),
más `NOTA_ESTRATO_203.md` (`5f986a209`, pedido del coordinador). Todo con datos sintéticos o de producción; nada del A/B.
El veredicto de D25 no se leyó.

## Qué cambió

`experiments/_s157_prereg_d25/evaluar_d25.py`:

- `regla_p2(sumas, neto)`: la regla de D-34 (GANA, PIERDE, BLOQUEA, EMPATE) sacada a una función. La usan la pasada
  observada y cada sorteo de la calibración, así que las dos aplican exactamente la misma regla.
- `calibrar_p2(c, bloques, W)`: el nulo de la adenda §2. En cada sorteo se multiplica por +1 o -1 cada bloque
  noche-volcán entero; sobre cada sorteo, `regla_p2` con la misma matriz `W` de `pesos_bloque` (10.000 remuestreos,
  semilla 157), que depende sólo de los bloques. 1.000 sorteos (`N_CALIB_P2`), semilla 161 (`SEMILLA_CALIB_P2 = SEMILLA
  + 4`). Devuelve falsos GANA, PIERDE y BLOQUEA.
- `decidir_p2_bloques`: después de los controles y del SIN SUSTRATO calcula la regla y su calibración. Si falsos GANA o
  falsos PIERDE pasan de `MAX_FALSOS_CALIB` (5 %, 50 de 1.000, cada cola por separado), devuelve INDECIDIBLE sea cual
  sea el resultado sin calibrar. BLOQUEA no se calibra. El detalle de P2 del JSON trae siempre `resultado_sin_calibrar`,
  `calibrada`, `falsos_gana`, `falsos_pierde`, `falsos_bloquea`, `n_sorteos`, `semilla_calibracion`, `tope_por_cola` y
  `nota_calibracion`.
- `global_ventana` y `combinar` no cambian: un P2 INDECIDIBLE deja la ventana INDECIDIBLE por la rama que ya existía.
- `estrato_203(...)`, llamado desde `contar`: estrato que sólo informa (`info["estrato_203"]`, VIIRS 750), con la tabla
  y los totales de la nota (recupera, enciende, no cambia, más «otros cambios» para que sumen n). No entra a `ver`.
- `imprimir`: una línea con la calibración de P2 y la tabla del estrato 203.

Pruebas nuevas: `tests/test_evaluar_d25_calib_p2_s160.py` (29) y `tests/test_evaluar_d25_punta_a_punta_s160.py` (8, el
caso de punta a punta sobre brazos hechos desde producción, como pide V29-01).

## Pruebas rojas y verdes

- Rojas (`rojo_calib_p2.py`, salida `rojo_calib_p2.txt` y `.xml`): las 37 pruebas nuevas, tal como quedan
  commiteadas (corridas después de su última edición), contra el evaluador de `5f986a209`. **24 fallan, las 24 por
  `AssertionError`**, 0 por otra excepción, 0 errores. Las 13 que pasan son candados de comportamiento que ya existía
  (intervalo exacto, tope y alcance del comparador, la exclusión de D-29 en `evaluar` y la marca de la calibración
  sellada); a esas las valida el corredor de mutaciones, no la salida roja.
- Verdes, con el árbol quieto (`status_antes.txt` y `status_despues.txt` iguales; `sha_antes.txt` y `sha_despues.txt`
  iguales para el evaluador, `probar_evaluar_d25.py` y las cinco baterías):
  `probar_evaluar_d25.py` **31 de 31 casos OK** (`probar_salida.txt`, 31 min); suite completa **2.415 passed, 29
  skipped, 1 xfailed** (`suite_salida.txt`, 6 min 26 s; antes eran 2.378 + las 37 nuevas).

## Mutaciones (`mutar_calib_p2.py`, salida `mutaciones_salida.txt` y `.json`)

Control primero: copia sin mutar, las cinco baterías del evaluador, 73 pruebas, 0 fallas. Atrapada = alguna prueba
falla por `AssertionError` y ninguna por otra excepción ni error, leído del XML de JUnit. Copias en
`experiments/_mut_<id>/`, borradas (al final no queda ninguna).

**28 de 28 atrapadas por aserción**, 0 con otra excepción:

| grupo | n | cuáles |
|---|---|---|
| V34-03 | 7 de 7 | semilla y remuestreos del intervalo de P2, nivel 95 %, borde `lo >= 0`, tope de d′ al 10 %, INDECIDIBLE por d′ sin MEJORA de d, marca «NO VALE PARA DECIDIR» en el estado |
| V29-01 | 5 de 5 | crudos sin filtrar, tabla sin filtrar, cobertura sin filtrar, fecha en hora de Chile, cabecera de V1 callada |
| D-42 | 13 de 13 | semilla (constante y en la llamada), sorteos (999 y 200), tope al 10 %, tope estricto, una cola sola (cada una), colas sumadas, sorteo por pasada, fallo que no deja INDECIDIBLE, INDECIDIBLE sólo para GANA, calibración sin sustrato |
| estrato 203 | 3 de 3 | el estrato decide P2, recupera y enciende cambiados, sin exigir cumbre |

## Falsos y poder con sintéticos (adenda §5)

`cobertura_p2_calibrada.py` (escenarios de V34-01, 500 conjuntos, semillas 0 a 499, función real). Intervalos de
Wilson al 95 % en la salida.

| escenario (nulo) | falsos GANA | falsos PIERDE | INDECIDIBLE | sin calibrar GANA+PIERDE |
|---|---|---|---|---|
| A iid, 12 × 3 | 2,0 % | 5,4 % [3,7; 7,7] | 5,0 % | 8,0 % |
| B signo por noche, 12 × 4 | 1,2 % | 2,6 % | 0 % | 3,8 % |
| B2 signo por noche, 6 × 6 | 1,2 % | 3,4 % | 0 % | 4,6 % |
| B3 iid, noches desiguales | 1,8 % | 2,0 % | 32,4 % | 8,6 % |
| B4 iid, 3 noches | 0 % | 0 % | 27,6 % | 8,6 % |
| B5 signo por noche, 3 × 2 | 0 % | 0 % | 100 % | 25,0 % |
| B6 signo por noche, 4 × 2 | 0 % | 0 % | 100 % | 16,2 % |
| B7 signo por noche, 5 × 2 | 2,6 % | 6,0 % [4,2; 8,4] | 0 % | 8,6 % |
| B8 signo por noche, 8 × 2 | 1,8 % | 6,6 % [4,7; 9,1] | 2,6 % | 8,4 % |

Tres celdas quedan sobre 5 % en una cola (A, B7, B8, siempre PIERDE). No es la regla: es la muestra. En B7 el falso
PIERDE sólo ocurre con las cinco noches positivas, y el generador con las semillas 0 a 499 da 30 conjuntos así contra
15,6 esperados (13 del lado negativo; `contar_generador.py`). Para sacar el error de muestreo, `exacto_p2.py` recorre
todas las combinaciones de signos de los nulos que se pueden enumerar, con la función real:

| nulo (exacto) | combinaciones | falsos GANA | falsos PIERDE | INDECIDIBLE | sin calibrar, por cola |
|---|---|---|---|---|---|
| B2 | 64 | 1,56 % | 1,56 % | 0 % | 1,56 % |
| B4 | 32 | 0 % | 0 % | 25,0 % | 3,12 % |
| B5 | 8 | 0 % | 0 % | 100 % | 12,5 % |
| B6 | 16 | 0 % | 0 % | 100 % | 6,25 % |
| B7 | 32 | 3,12 % | 3,12 % | 0 % | 3,12 % |
| B8 | 256 | 3,52 % | 3,52 % | 2,34 % | 3,52 % |
| B9 iid, 5 × 2 | 1.024 | 0,10 % | 0,10 % | 46,9 % | 4,98 % |

**Todos quedan en 5 % o menos por cola.** A y B (12 noches) no se pueden enumerar; por simetría del nulo su tasa por
cola es el promedio de las dos colas medidas: A 3,7 %, B 1,9 %. SOSPECHA razonable, no medida exacta.

Poder (500 conjuntos):

| efecto | calibrada | sin calibrar |
|---|---|---|
| C grande a favor, 12 × 3 | GANA 98,8 % | 99,2 % |
| C2 grande en contra, 12 × 3 | PIERDE 99,8 % | 99,8 % |
| D moderado, 20 × 2 | GANA 68,0 % | 68,4 % |
| E por noche, 10 × 4 | GANA 33,0 % | 33,0 % |
| F grande con 4 noches × 3 | **GANA 0 %, INDECIDIBLE 100 %** | GANA 75,4 % |
| F2 total con 5 noches × 2 | GANA 100 % | 100 % |

**Con 4 noches discordantes o menos, P2 calibrada no puede decidir, aunque el efecto sea grande.** Es estructural: con
B noches, que todas caigan del mismo lado bajo el nulo tiene probabilidad 2^(−B) por cola, que pasa del 5 % con B ≤ 4,
y en esa configuración la regla decide, así que la calibración siempre falla. Con 5 noches o más, el poder vuelve.

## Control del placebo del 1 % (pedido del coordinador, no es regla sellada)

`placebo_1pct.py` (brazos desde producción con `sustrato_k.unir_k`; D = K con el 1 % de las publicaciones de K
apagadas al azar, magnitud a 0,0 MW; evaluador entero) y `resumir_placebo.py` → `resumen_placebo_1pct.txt`. 20 semillas
por ventana, 0 caídas; en cada semilla las publicaciones apagadas llegan a la tabla (3 de 3 en V1, 10 de 10 en V2).

- Ventana tipo V1 (2026-09-18 a 10-18, 7 volcanes, K publica 320 pasadas, se apagan 3): P2 da **SIN SUSTRATO en 20 de
  20** semillas, en los dos sensores y las dos reglas, calibrada y sin calibrar.
- Ventana tipo V2 (2026-04-01 a 06-12, 6 volcanes, K publica 971, se apagan 10): VIIRS 375 SN, BLOQUEA 4 y SIN SUSTRATO
  16; VIIRS 375 original, calibrada PIERDE 2, BLOQUEA 1, INDECIDIBLE 1, SIN SUSTRATO 16 (sin calibrar, PIERDE 3);
  VIIRS 750, SIN SUSTRATO 20 de 20.
- **GANA calibrada: 0 de 20 en las dos ventanas** (Wilson [0 %, 16 %]); sin calibrar también 0. El criterio (no más
  del 5 % de las semillas) se cumple. Límites: con 20 semillas el intervalo llega a 16 %, y con K el placebo casi no
  tiene sustrato. Su neto va **en contra** de D (mediana +1 a +3 en VIIRS 375), al revés que en la auditoría V1a, que lo
  midió sobre C0, con más sobrepublicación. SOSPECHA: con K, apagar al azar quita más alertas que negativos limpios.

## Preguntas para Nicolás (no inventé regla)

1. **P2 INDECIDIBLE en un sensor y PIERDE calibrado en el otro.** La adenda §2.5 dice «Como hoy con un M INDECIDIBLE,
   la ventana queda INDECIDIBLE (`global_ventana`), salvo un VETADO de P1». Hoy un PIERDE se mira antes que un
   INDECIDIBLE (H2, ADENDA_CALIBRACION.md §4), así que este caso da NO CUMPLE (suma). Lo dejé así, sin tocar
   `global_ventana`, y lo fija `test_lectura_pendiente_...`. Si la frase «salvo un VETADO» quiere decir que sólo el veto
   manda antes, hay que cambiarlo antes del tag.
2. **Con 4 noches discordantes o menos, P2 no decide nunca** (ver poder). ¿Se acepta así?
3. Lecturas que apliqué: «se informa siempre» = los campos están siempre; si la calibración no corre (controles caídos
   o sin sustrato), los falsos van en `None` con una nota. En el estrato 203, «ausente» = `pc.vrp_mw` ausente con
   `distance_class` summit, y «recupera» cuenta toda alerta, también la protegida.

## Lo que no hice

- No leí el veredicto de D25 ni corrí el evaluador sobre datos del A/B. No toqué `pipeline/`, `data/`, `frontend/` ni
  las adendas. No creé tags, ramas ni PRs.
- No medí exacto A ni B (12 noches); la tasa por cola de esos dos es la medida por muestreo o el promedio simétrico.
- No volví a correr la curva de poder del comparador de M (ADENDA_PLACEBO.md §5.2); no cambia con esta adenda.
- No hubo verificador con contexto limpio: lo pide la adenda antes del tag de lectura.
